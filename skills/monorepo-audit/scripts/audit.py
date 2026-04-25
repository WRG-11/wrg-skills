"""monorepo-audit — three static checks for a Python monorepo.

No external deps beyond stdlib; tries `tomllib` (3.11+) or `tomli` as
fallback. Safe to run: read-only, no network, no mutation. Finishes in
seconds on typical repos.

Checks:
  schema_drift   — parse CREATE TABLE stmts from source, compare to
                   live SQLite DBs under likely-default locations.
                   Opt-out: no DB found → skipped with a note.
  coverage_floor — read each app's pyproject fail_under, compare to
                   recorded coverage (release_check JSON or coverage.xml).
  orphan_modules — AST import graph per app, flag .py files nobody imports.
                   Exempt: __init__.py, __main__.py, main.py, and any
                   module that backs a `[project.scripts]` entry point.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sqlite3
import sys

# Windows default cp1254 can't encode emoji markers — force utf-8
# so the skill works identically on any terminal. Safe no-op on Unix.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ──────────────────────────────────────────────────────────────────────
# Shared types
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Finding:
    check: str
    app: str
    detail: str
    severity: str = "warn"  # "warn" or "error"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CheckResult:
    name: str
    findings: list[Finding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────
# TOML loader (3.11+ stdlib or 3.10 fallback)
# ──────────────────────────────────────────────────────────────────────


def _load_toml(path: Path) -> dict[str, Any]:
    try:
        import tomllib
    except ModuleNotFoundError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ModuleNotFoundError:
            return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


# ──────────────────────────────────────────────────────────────────────
# App discovery
# ──────────────────────────────────────────────────────────────────────


def discover_apps(repo_root: Path, apps_dir: str) -> list[Path]:
    root = repo_root / apps_dir
    if not root.is_dir():
        return []
    return sorted(
        p for p in root.iterdir()
        if p.is_dir() and (p / "pyproject.toml").is_file()
    )


def _app_package_dir(app_path: Path) -> Path | None:
    """Return the package source directory: either src/<pkg> or flat <pkg>."""
    name_hint = app_path.name
    candidates = [
        app_path / "src" / name_hint,
        app_path / name_hint,
    ]
    for c in candidates:
        if c.is_dir() and (c / "__init__.py").is_file():
            return c
    # Fallback: any subdir with __init__.py under src/ or app root
    for base in (app_path / "src", app_path):
        if base.is_dir():
            for child in base.iterdir():
                if child.is_dir() and (child / "__init__.py").is_file():
                    return child
    return None


# ──────────────────────────────────────────────────────────────────────
# Check 1: schema_drift
# ──────────────────────────────────────────────────────────────────────


_CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)


def _extract_ddl(app_pkg: Path) -> list[str]:
    """Scan .py files for string literals containing CREATE TABLE."""
    ddls: list[str] = []
    for py in app_pkg.rglob("*.py"):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if _CREATE_TABLE_RE.search(node.value):
                    ddls.append(node.value)
    return ddls


def _expected_schema(ddls: list[str]) -> dict[str, set[str]]:
    """Materialize DDL in-memory and read back column sets per table."""
    if not ddls:
        return {}
    try:
        conn = sqlite3.connect(":memory:")
        for ddl in ddls:
            try:
                conn.executescript(ddl)
            except sqlite3.Error:
                continue
        tables: dict[str, set[str]] = {}
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        ).fetchall():
            tname = row[0]
            cols = {r[1] for r in conn.execute(f"PRAGMA table_info({tname})")}
            tables[tname] = cols
        conn.close()
        return tables
    except sqlite3.Error:
        return {}


def _actual_schema(db_path: Path) -> dict[str, set[str]]:
    conn = sqlite3.connect(str(db_path))
    tables: dict[str, set[str]] = {}
    try:
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall():
            tname = row[0]
            cols = {r[1] for r in conn.execute(f"PRAGMA table_info({tname})")}
            tables[tname] = cols
    finally:
        conn.close()
    return tables


def _guess_db_path(app_name: str, app_path: Path, home: Path) -> Path | None:
    """Probe common locations for an app's live SQLite DB."""
    candidates = [
        app_path / "data" / f"{app_name}.db",
        app_path / f"{app_name}.db",
        home / f".{app_name}" / f"{app_name}.db",
        home / f".{app_name}" / "data.db",
        home / ".wrg" / f"{app_name}.db",
    ]
    # Also scan home/.<app_name>/ for any .db file
    app_state = home / f".{app_name}"
    if app_state.is_dir():
        candidates.extend(app_state.glob("*.db"))
    for c in candidates:
        if c.is_file():
            return c
    return None


def check_schema_drift(apps: list[Path], home: Path) -> CheckResult:
    result = CheckResult(name="schema_drift")
    for app_path in apps:
        app_name = app_path.name
        pkg = _app_package_dir(app_path)
        if pkg is None:
            continue
        ddls = _extract_ddl(pkg)
        if not ddls:
            continue  # silent — app has no SQL, nothing to check
        expected = _expected_schema(ddls)
        if not expected:
            result.notes.append(f"{app_name}: DDL found but failed to parse")
            continue
        db_path = _guess_db_path(app_name, app_path, home)
        if db_path is None:
            result.notes.append(
                f"{app_name}: skipped, no live DB found at common paths"
            )
            continue
        try:
            actual = _actual_schema(db_path)
        except sqlite3.Error as exc:
            result.findings.append(Finding(
                check="schema_drift", app=app_name,
                detail=f"live DB read failed: {exc}",
                severity="error",
            ))
            continue
        for table, expected_cols in expected.items():
            if table not in actual:
                result.findings.append(Finding(
                    check="schema_drift", app=app_name,
                    detail=f"table '{table}' in code but missing from {db_path.name}",
                ))
                continue
            actual_cols = actual[table]
            only_in_db = actual_cols - expected_cols
            only_in_ddl = expected_cols - actual_cols
            for col in sorted(only_in_db):
                result.findings.append(Finding(
                    check="schema_drift", app=app_name,
                    detail=f"table '{table}' column '{col}' in DB but not in code",
                ))
            for col in sorted(only_in_ddl):
                result.findings.append(Finding(
                    check="schema_drift", app=app_name,
                    detail=f"table '{table}' column '{col}' in code but not in DB",
                ))
        for table in sorted(set(actual) - set(expected)):
            result.notes.append(
                f"{app_name}: table '{table}' in DB but not in code "
                f"(might be legacy / external)"
            )
    return result


# ──────────────────────────────────────────────────────────────────────
# Check 2: coverage_floor
# ──────────────────────────────────────────────────────────────────────


def _floor_from_pyproject(pyproject: Path) -> int | None:
    data = _load_toml(pyproject)
    tool = data.get("tool", {})
    cov = tool.get("coverage", {})
    report = cov.get("report", {})
    val = report.get("fail_under")
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _coverage_from_health_json(path: Path) -> int | None:
    """Look for a 'coverage' or 'total' percent in a release-check JSON."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    for key in ("coverage", "total_coverage", "pct"):
        if key in data and isinstance(data[key], (int, float)):
            return int(data[key])
    # Nested structure (common): apps[0].coverage
    apps = data.get("apps")
    if isinstance(apps, list) and apps:
        first = apps[0]
        if isinstance(first, dict):
            for key in ("coverage", "pct"):
                if key in first and isinstance(first[key], (int, float)):
                    return int(first[key])
    return None


def _coverage_from_coverage_xml(xml_path: Path) -> int | None:
    """Very loose parse of coverage.py XML for line-rate."""
    try:
        text = xml_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(r'line-rate="([0-9.]+)"', text)
    if m:
        try:
            return int(round(float(m.group(1)) * 100))
        except ValueError:
            return None
    return None


def check_coverage_floor(apps: list[Path], health_dir: Path) -> CheckResult:
    result = CheckResult(name="coverage_floor")
    for app_path in apps:
        app_name = app_path.name
        pyproj = app_path / "pyproject.toml"
        if not pyproj.is_file():
            continue
        floor = _floor_from_pyproject(pyproj)
        if floor is None:
            result.notes.append(f"{app_name}: no fail_under declared")
            continue

        actual: int | None = None
        health_json = health_dir / f"release_check_{app_name}.json"
        if health_json.is_file():
            actual = _coverage_from_health_json(health_json)
        if actual is None:
            cov_xml = app_path / "coverage.xml"
            if cov_xml.is_file():
                actual = _coverage_from_coverage_xml(cov_xml)

        if actual is None:
            result.notes.append(
                f"{app_name}: fail_under={floor}, no coverage record found"
            )
            continue
        drift = actual - floor
        if drift < 0:
            result.findings.append(Finding(
                check="coverage_floor", app=app_name,
                detail=f"fail_under={floor}, actual={actual} (drift: {drift:+d})",
                severity="error",
            ))
        elif drift >= 10:
            # Not a finding — an advisory note: floor could be raised
            result.notes.append(
                f"{app_name}: fail_under={floor}, actual={actual} "
                f"(floor could be raised)"
            )
    return result


# ──────────────────────────────────────────────────────────────────────
# Check 3: orphan_modules
# ──────────────────────────────────────────────────────────────────────


_EXEMPT_FILENAMES = {"__init__.py", "__main__.py", "main.py"}


def _script_targets(pyproject: Path) -> set[str]:
    """Dotted module paths that back `[project.scripts]` entries."""
    data = _load_toml(pyproject)
    scripts = data.get("project", {}).get("scripts", {}) or {}
    targets: set[str] = set()
    for _name, spec in scripts.items():
        if isinstance(spec, str) and ":" in spec:
            mod = spec.split(":", 1)[0]
            targets.add(mod)
            # also exempt any parent packages
            parts = mod.split(".")
            for i in range(1, len(parts)):
                targets.add(".".join(parts[:i]))
    return targets


def _imports_from_file(py: Path) -> set[str]:
    """Extract all import targets from a file.

    Handles three patterns that orphan detection needs to see:
      import pkg.mod              → "pkg", "pkg.mod"
      from pkg import mod         → "pkg", "pkg.mod"  (mod might be a submodule)
      from . import mod           → "mod"              (bare, match via suffix)
      from .submod import X       → "submod", "submod.X"
    """
    try:
        tree = ast.parse(py.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.add(n.name)
                # Also add parent packages: pkg.sub.leaf → pkg, pkg.sub
                parts = n.name.split(".")
                for i in range(1, len(parts)):
                    imports.add(".".join(parts[:i]))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
                # Each imported name might be a submodule of the parent
                for n in node.names:
                    if n.name != "*":
                        imports.add(f"{node.module}.{n.name}")
            # Relative imports (from . import foo / from .sub import X):
            # record bare name; suffix match on full dotted module will catch it.
            for n in node.names:
                if n.name != "*":
                    imports.add(n.name)
    return imports


def check_orphan_modules(apps: list[Path]) -> CheckResult:
    result = CheckResult(name="orphan_modules")
    for app_path in apps:
        app_name = app_path.name
        pkg = _app_package_dir(app_path)
        if pkg is None:
            continue
        py_files = list(pkg.rglob("*.py"))
        if not py_files:
            continue
        script_mods = _script_targets(app_path / "pyproject.toml")

        # Build module name for each file
        file_to_mod: dict[Path, str] = {}
        mod_to_file: dict[str, Path] = {}
        for py in py_files:
            rel = py.relative_to(pkg.parent)
            parts = rel.with_suffix("").parts
            mod = ".".join(parts)
            file_to_mod[py] = mod
            mod_to_file[mod] = py

        # Collect all imports from every file
        all_imports: set[str] = set()
        for py in py_files:
            all_imports |= _imports_from_file(py)

        # For each file, is there any importer?
        for py, mod in file_to_mod.items():
            if py.name in _EXEMPT_FILENAMES:
                continue
            if mod in script_mods:
                continue  # exempt: registered as CLI entry
            # Considered imported if some import name equals mod or starts with mod + "."
            referenced = any(
                imp == mod or imp.startswith(mod + ".") or
                mod.endswith("." + imp) or mod == imp
                for imp in all_imports
            )
            if not referenced:
                rel_display = py.relative_to(app_path)
                result.findings.append(Finding(
                    check="orphan_modules", app=app_name,
                    detail=f"{rel_display} — no importers found",
                ))
    return result


# ──────────────────────────────────────────────────────────────────────
# Report assembly
# ──────────────────────────────────────────────────────────────────────


ALL_CHECKS = ("schema_drift", "coverage_floor", "orphan_modules")


def run_audit(
    repo_root: Path,
    apps_dir: str,
    health_dir: Path,
    only: str | None,
    skip: set[str],
) -> dict[str, Any]:
    selected = [c for c in ALL_CHECKS if (only is None or c == only) and c not in skip]
    apps = discover_apps(repo_root, apps_dir)
    home = Path.home()
    results: list[CheckResult] = []

    for check in selected:
        if check == "schema_drift":
            results.append(check_schema_drift(apps, home))
        elif check == "coverage_floor":
            results.append(check_coverage_floor(apps, health_dir))
        elif check == "orphan_modules":
            results.append(check_orphan_modules(apps))

    all_findings: list[Finding] = []
    all_notes: list[str] = []
    for r in results:
        all_findings.extend(r.findings)
        all_notes.extend(f"{r.name}: {n}" for n in r.notes)

    return {
        "repo_root": str(repo_root),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "apps_scanned": len(apps),
        "checks": [r.name for r in results],
        "findings": [f.to_dict() for f in all_findings],
        "notes": all_notes,
    }


def render_markdown(report: dict[str, Any]) -> str:
    repo_name = Path(report["repo_root"]).name or report["repo_root"]
    findings = report["findings"]
    error_count = sum(1 for f in findings if f["severity"] == "error")
    warn_count = sum(1 for f in findings if f["severity"] == "warn")

    lines = [
        f"# Monorepo audit — {repo_name}",
        f"_Generated {report['generated_at']}_",
        "",
        "## Summary",
        f"- {len(report['checks'])} checks ran: {', '.join(report['checks'])}",
        f"- {len(findings)} findings ({error_count} error, {warn_count} warn)",
        f"- {report['apps_scanned']} apps scanned",
        "",
    ]

    if not findings:
        lines.append("✅ No findings. Repo is clean.")
    else:
        # Group findings by check
        by_check: dict[str, list[dict]] = {}
        for f in findings:
            by_check.setdefault(f["check"], []).append(f)
        for check_name in report["checks"]:
            items = by_check.get(check_name, [])
            lines.append(f"## {check_name}")
            if not items:
                lines.append("_No findings._")
            else:
                for f in items:
                    sev = f["severity"]
                    marker = "🔴" if sev == "error" else "⚠️"
                    lines.append(f"- {marker} **{f['app']}** [{sev}]: {f['detail']}")
            lines.append("")

    notes = report.get("notes", [])
    if notes:
        lines.append("## Notes (skipped / advisory)")
        for n in notes:
            lines.append(f"- {n}")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="monorepo-audit",
        description="Schema-drift / coverage-floor / orphan-module audit for a Python monorepo.",
    )
    p.add_argument("--repo-root", type=Path, default=Path.cwd(),
                   help="Repo root (default: CWD).")
    p.add_argument("--apps-dir", default="apps",
                   help="Subproject directory name (default: apps).")
    p.add_argument("--health-dir", type=Path, default=None,
                   help="Where release_check JSONs live (default: <repo>/artifacts/health).")
    p.add_argument("--json", action="store_true",
                   help="Emit JSON instead of markdown.")
    p.add_argument("--only", choices=ALL_CHECKS, default=None,
                   help="Run only one check.")
    p.add_argument("--skip", action="append", choices=ALL_CHECKS, default=[],
                   help="Skip a check (repeatable).")
    args = p.parse_args(argv)

    repo_root = args.repo_root.resolve()
    health_dir = args.health_dir or (repo_root / "artifacts" / "health")

    report = run_audit(
        repo_root=repo_root,
        apps_dir=args.apps_dir,
        health_dir=health_dir,
        only=args.only,
        skip=set(args.skip),
    )

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(report))

    return 1 if report["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
