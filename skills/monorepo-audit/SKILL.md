---
name: monorepo-audit
description: Audit a Python monorepo for schema drift between SQLite code/DBs, coverage-floor drift between pyproject fail_under and recorded coverage, and orphan Python modules never imported anywhere. Use this skill whenever the user mentions governance checks, schema drift, coverage floor, orphan modules, dead code detection in a monorepo, app/package audit, "is this module used?", fail_under vs actual coverage mismatch, or any phrase like "audit my repo", "check my monorepo", or "/monorepo-audit". Also use when you see a user working in a repo with multiple `apps/<name>/` or `packages/<name>/` subprojects and they're thinking about hygiene, dead code, or consistency across apps — even if they don't specifically ask for an "audit". The output is a human-readable markdown report plus structured JSON, and the skill is fast (no network, stdlib + optional tomli fallback, walks the repo and finishes in seconds).
---

# monorepo-audit

## What this skill does

Runs three static checks across a Python monorepo and reports findings in a
single report. Works on any repo where subprojects live under `apps/<name>/`,
`packages/<name>/`, or a configurable layout. No network calls, no mutation —
pure read-and-report.

The three checks:

1. **Schema drift** — parses `CREATE TABLE` statements out of app source code,
   builds the expected column set, compares against live on-disk SQLite DBs
   under `~/.<something>/<app>.db` (or configurable). Flags extra columns on
   either side and missing tables.
2. **Coverage floor** — reads each app's `pyproject.toml`
   `[tool.coverage.report].fail_under` value, compares against recorded
   coverage (reads `artifacts/health/release_check_<app>.json` or
   `coverage.xml` when present). Flags apps whose actual coverage is below
   their declared floor.
3. **Orphan modules** — walks each app's `src/` tree (or flat layout),
   builds an AST-based import graph, flags `.py` files that no sibling
   imports. Entrypoints (`__init__.py`, `__main__.py`, `main.py`, and
   targets of `[project.scripts]`) are exempt.

## When to use

Strongly trigger on any of:
- "audit my monorepo" / "audit this repo" / "governance check"
- "schema drift" / "coverage floor" / "fail_under" / "orphan modules"
- "is this module used?" / "dead code in my repo"
- "/monorepo-audit" (explicit slash)
- User in a repo with `apps/*/pyproject.toml` asking about hygiene/cleanup

Don't trigger if:
- Single-package repo (no `apps/` or `packages/` layout) — skill expects multi-app
- User wants test coverage metrics, not the floor discipline — different tool
- User wants linting / type checking — that's ruff/mypy, not this

## How to run

From the repo root:

```bash
python <skill-path>/scripts/audit.py            # human-readable markdown
python <skill-path>/scripts/audit.py --json     # JSON report
python <skill-path>/scripts/audit.py --only coverage_floor  # single check
python <skill-path>/scripts/audit.py --apps-dir packages    # custom layout
python <skill-path>/scripts/audit.py --skip schema_drift    # opt out of a check
```

Exit code:
- `0` — no findings
- `1` — at least one finding

Flags:
- `--json` — emit JSON instead of markdown
- `--apps-dir DIR` — which directory contains the subprojects (default: `apps`; common alternatives: `packages`, `projects`)
- `--only CHECK` — run only one check (schema_drift / coverage_floor / orphan_modules)
- `--skip CHECK` — skip one check (can be passed multiple times)
- `--health-dir DIR` — where release/coverage JSONs live (default: `artifacts/health`)

## Workflow for Claude when this skill triggers

1. **Verify layout.** Confirm the repo has `apps/*/pyproject.toml` (or the
   user's configured layout). If not, tell the user — skill doesn't fit.
2. **Run the audit script.** Start with the default (all three checks, markdown).
3. **Interpret the report.**
   - Severity: `warn` (default) is informational; `error` means the check
     asserts a contract was violated.
   - Findings are per-(check, app, detail). Group them by app if the user
     wants to know "what's wrong with app X".
4. **Propose action — don't apply.** For each finding:
   - Schema drift: explain whether the code or the DB is the source of truth.
     Usually code-is-source-of-truth → DB needs migration.
   - Coverage floor: either raise the floor (if actual is higher) or improve
     tests (if actual is lower). Don't silently lower the floor.
   - Orphan modules: may be (a) genuinely dead code → delete, (b) exempt
     entrypoint the graph missed → add to exemption list, or (c) imported
     dynamically → flag for human review.
5. **Ask before mutating.** The skill is read-only by design. If the user
   wants a fix applied, generate the edit and confirm before writing.

## Conventions the skill assumes

See `references/conventions.md` for layout expectations, default paths, and
how to configure non-standard monorepos.

## Edge cases / known limits

- **Missing on-disk SQLite DB:** Skipped with a note — the app may simply
  not have been run yet. Don't flag.
- **Dynamic imports** (`importlib.import_module(name)` with a runtime name):
  orphan-modules will false-positive on these. Check for plugin registries
  or entry-point manifests before deleting flagged modules.
- **Python 3.10:** `tomllib` isn't stdlib; skill falls back to `tomli` if
  installed, otherwise skips pyproject-based checks with a note.
- **Non-Python monorepos:** Unsupported. Skill requires `pyproject.toml`
  per-app to meaningfully check coverage.

## Report format

Markdown output (default):

```markdown
# Monorepo audit — <repo-name>
_Generated <timestamp>_

## Summary
- 3 checks ran
- 7 findings (2 error, 5 warn)
- 18 apps scanned

## schema_drift
- **app_a** [warn]: table `users` on-disk has extra columns: email_verified
- **app_b** [error]: table `sessions` missing on-disk (expected by code)

## coverage_floor
- **app_c** [error]: fail_under=60, actual=42 (drift: -18)

## orphan_modules
- **app_d** [warn]: `helpers/legacy.py` — no importers found
```

JSON output (`--json`):

```json
{
  "repo_root": "/path/to/repo",
  "generated_at": "2026-04-23T19:30:00Z",
  "apps_scanned": 18,
  "checks": ["schema_drift", "coverage_floor", "orphan_modules"],
  "findings": [
    {"check": "coverage_floor", "app": "app_c",
     "detail": "fail_under=60, actual=42 (drift: -18)",
     "severity": "error"}
  ],
  "skipped": ["schema_drift:app_e (no SQLite DB on disk)"]
}
```
