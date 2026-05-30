# wrg-skills

> Claude Code skills authored alongside the WinstonRedGuard
> monorepo. Five self-contained skills loaded on-demand from `~/.claude/skills/` —
> the headline one (`mcp-audit`) ships with a validated framework, an external
> disclosure SOP, and a public track record of five real-world audits.

[![lint](https://github.com/WRG-11/wrg-skills/actions/workflows/lint.yml/badge.svg)](https://github.com/WRG-11/wrg-skills/actions/workflows/lint.yml)
&nbsp;&nbsp;**5 external MCP audits** · **3 ecosystems** (TS / FastMCP-Py / low-level Py) · **0 GHSA filed** (by design — see disclosure SOP)

## Install

```bash
npx skills install github.com/WRG-11/wrg-skills
claude
/skills
```

This installs every skill under `~/.claude/skills/<skill-name>/`. Each skill loads
on-demand when its trigger phrases match — no global hooks, no startup cost.

## Quick links

| Where | What |
|---|---|
| [`skills/mcp-audit/`](skills/mcp-audit/) | The audit skill itself — procedure, rubric, examples-in-the-wild. |
| [`skills/mcp-audit/SEVERITY.md`](skills/mcp-audit/SEVERITY.md) | 33-row default-severity matrix mapping every finding type to a bucket. |
| [`docs/disclosure-sop.md`](docs/disclosure-sop.md) | When to file GHSA vs coordinated vs public for an external audit. |
| [`docs/case-studies/`](docs/case-studies/) | Five real-world audits. Frontmatter + finding matrix + upstream PR links. |
| [`docs/case-studies/_TEMPLATE.md`](docs/case-studies/_TEMPLATE.md) | Template for landing your own external-audit case-study. |
| [`docs/retrospectives/`](docs/retrospectives/) | Lessons learned across audit waves. |

---

## Real-world validation — `mcp-audit` skill

Five external audits shipped 2026-04-26 against `modelcontextprotocol/servers`, the
official MCP reference monorepo. Each produced a public case-study, an internal WRG
evidence record, and (where applicable) an upstream fix PR.

### Case studies

| # | Target | Date | Severity (C/H/M/L/I) | Status | Case-study |
|---|---|---|---|---|---|
| 1 | `@modelcontextprotocol/server-filesystem@0.6.3` | 2026-04-26 | 0 / 0 / 0 / 6 / 2 | public, upstream PRs open | [`filesystem-mcp-2026-04-26.md`](docs/case-studies/filesystem-mcp-2026-04-26.md) |
| 2 | `mcp-server-fetch@0.6.3` | 2026-04-26 | 0 / 0 / **1** / 1 / 2 | public, upstream PR open | [`fetch-mcp-2026-04-26.md`](docs/case-studies/fetch-mcp-2026-04-26.md) |
| 3 | `mcp-server-git@0.6.2` | 2026-04-26 | 0 / 0 / 0 / 2 / 1 | public, upstream PR open | [`git-mcp-2026-04-26.md`](docs/case-studies/git-mcp-2026-04-26.md) |
| 4 | `mcp-server-time@0.6.2` (lite-scan) | 2026-04-26 | 0 / 0 / 0 / 1 / 0 | public | [`time-mcp-2026-04-26.md`](docs/case-studies/time-mcp-2026-04-26.md) |
| 5 | `@modelcontextprotocol/server-memory@0.6.3` | 2026-04-26 | 0 / 0 / 0 / 2 / 1 | public, upstream PR open | [`memory-mcp-2026-04-26.md`](docs/case-studies/memory-mcp-2026-04-26.md) |

Aggregate: **0 Critical, 0 High, 1 Medium, 12 Low, 6 Info** across 5 surfaces and
~50 tools. No GHSA filed because nothing warranted one.

### 3-ecosystem triangulation

The skill was originally written against **FastMCP Python** (`@mcp.tool()`). To
validate the framework's portability, the wave covered three different MCP server
patterns. Each surface uses a different canonical return shape — the skill adapted
without force-fitting `{ok, ...}`:

| Ecosystem | Server pattern | Canonical return shape | Audited surfaces |
|---|---|---|---|
| **TypeScript** (FastMCP-style SDK) | `server.registerTool(name, config, handler)` | `{content: [{type, text}], structuredContent: {...}}` | filesystem, memory |
| **Python FastMCP** | `@mcp.tool()` decorator | `{ok: bool, ...}` envelope | fetch |
| **Python low-level python-sdk** | `@server.list_tools()` returning `list[Tool]` + `@server.call_tool()` dispatch | `[TextContent(type="text", text=...)]` | git, time |

Each ecosystem required a small inventory adaptation; the **5-axis scoring rubric
(discoverability, return-shape, naming, error-handling, test coverage) applied
unchanged** to all three. The TypeScript adaptation is codified in [`SKILL.md`](skills/mcp-audit/SKILL.md);
the low-level Python adaptation is documented in §6 of the git case-study as a
candidate SKILL.md addition.

### Disclosure SOP gate validated

The SOP exists to keep the audit honest under disclosure pressure. Wave 2 stress-tested
it with a real false-positive escalation:

- **Initial finding** in the fetch audit: a recent commit appeared to have *silently
  removed* IP-blocking code added in an earlier commit — read on the surface as a
  **High security regression**, normally a private GHSA candidate.
- **SOP §6.6 verification gate**: pickaxe (`git log -S`), branch-membership check,
  and commit-magnitude sanity-check before any disclosure filing.
- **Result**: the original commit was on an unmerged feature branch (never reached
  main); the "removing" commit was an unrelated null-values fix that touched
  different lines. The "silently removed" attribution was wrong.
- **Outcome**: **OVERRIDE: de-escalated** from High to Medium per `SEVERITY.md`
  conventions. No GHSA filed. Public coordinated PR opened instead.

This is the kind of mistake an audit tool *will* surface eventually. The SOP caught
it pre-disclosure. The full incident write-up is in the fetch case-study and
formalised as §6.6 of the disclosure SOP.

### Honest framing

- **No findings were padded** to inflate audit value. The time audit reported
  **0 security findings** because the surface (datetime computation) genuinely has
  no applicable attack surface — six of nine SEC-class checks were marked N/A and
  documented as such.
- **No findings were de-emphasised** to flatter maintainers. The memory audit's
  F-002 (non-atomic file write) was a real architectural observation; it's
  documented with reproduction steps and an explicit `OVERRIDE: de-escalated`
  rationale (publicly observable pattern → public-PR route, not GHSA theatre).
- **Discoverability scores span the honest range** — 3.00/5 (git) to 4.50/5
  (filesystem). Surface quality varies; the rubric reports it.

---

## How to use the `mcp-audit` skill

### Audit your own MCP server

Read [`skills/mcp-audit/SKILL.md`](skills/mcp-audit/SKILL.md). Quickstart:

> *"Audit my MCP server"* — Claude grep-inventories your `@mcp.tool()` (or
> `server.registerTool` / `@server.list_tools`) decorators, scores every tool
> on five axes, surfaces decay candidates, and produces a single-file Markdown
> report with a "this-week pick" of ≤1hr fixes.

The audit is **read-only** — it produces the report; you ship the fixes. Output
lands at `docs/decisions/MCP_TOOL_AUDIT_<YYYY-MM-DD>.md` or `docs/audit/<...>.md`,
following whichever convention your repo already uses.

### Audit someone else's MCP server

When the maintainer is a third party, the disclosure SOP kicks in.

1. Read [`skills/mcp-audit/SKILL.md`](skills/mcp-audit/SKILL.md) (procedure).
2. Read [`skills/mcp-audit/SEVERITY.md`](skills/mcp-audit/SEVERITY.md) (default
   severity per finding type).
3. Read [`docs/disclosure-sop.md`](docs/disclosure-sop.md) (Critical/High → private
   GHSA; Medium → coordinated 90-day; Low/Info → public PR/issue, batched).
4. Copy [`docs/case-studies/_TEMPLATE.md`](docs/case-studies/_TEMPLATE.md) into
   `docs/case-studies/<target-slug>-<YYYY-MM-DD>.md` and fill it in as you go.
5. Apply pickaxe discipline (§6.6) before raising any "silently removed",
   "regression", or "novel" claim.

The five existing case-studies are a working reference for what the final document
should look like.

### Lite-scan variant (≤10 tools)

For small surfaces (single-tool servers, datetime utilities, anything where the
discoverability/naming/return-shape axes would be noise), the skill supports a
**lite scan** that drops the three axes that can't usefully fire at low N and
keeps SEC + TEST. **Validated against `mcp-server-time@0.6.2`** (2 tools, 221 LOC,
pure datetime computation) — the lite scan correctly identified zero security
findings and one test-coverage finding without manufacturing noise from the
skipped axes. See [`time-mcp-2026-04-26.md`](docs/case-studies/time-mcp-2026-04-26.md)
for the calibration evidence.

---

## Other skills

The `mcp-audit` skill is the headline, but four other skills ship alongside it.
None of these are involved in the external-audit workflow; they exist because they
proved useful in day-to-day WRG work.

| Skill | Triggers | What it does |
|---|---|---|
| [`monorepo-audit`](skills/monorepo-audit/) | "audit my monorepo", "schema drift", "fail_under check", "orphan modules" | Three static checks across a Python monorepo: SQLite schema drift, coverage-floor drift, orphan modules. Markdown + JSON report, exit code 0/1. Read-only. |
| [`memory-check`](skills/memory-check/) | `/memory-check`, "what have I been correcting", "scan for friction patterns" | Pause-and-audit pass over the current conversation — surfaces correction patterns, repeated friction, real-time mismatches as candidate `feedback` memory entries with per-entry user approval. |
| [`wrg-devguard-paste-lint`](skills/wrg-devguard-paste-lint/) | "is this prompt safe?", "any secrets in this?", "lint this prompt" | Runs [`wrg-devguard`](https://pypi.org/project/wrg-devguard/) policy lint or secret scan against a pasted snippet. Returns structured findings (rule_id, severity, position). Useful for prompt-injection detection and credential leak review. |
| [`instinct`](skills/instinct/) — *mirror* | "remember this pattern", "log this fix", "what have we seen before", "/instinct" | Self-learning memory for AI coding agents (tool sequences, preferences, recurring fixes). Auto-promotes mature patterns into suggestions. **Mirrored from [WRG-11/instinct](https://github.com/WRG-11/instinct) v1.4.0**; runs on top of the [`instinct-mcp`](https://pypi.org/project/instinct-mcp/) PyPI server. |

### Mirror drift detection

Some skills here (currently `instinct`) are **mirrored** from another repo as a
discovery surface — the canonical copy lives upstream. To prevent silent drift:

```bash
python tools/check_mirror_drift.py             # check mode (CI runs this advisory)
python tools/check_mirror_drift.py --update    # re-record baselines after a manual sync
```

The script fetches each mirrored skill's upstream raw URL, computes a sha256, and
compares to the recorded `upstream_content_sha256` in `skills.json`. CI runs the
check as advisory (continue-on-error) so drift surfaces in the lint summary
without blocking PRs.

---

## Authoring conventions

Each skill follows the standard Claude Code skill format:

```
skills/<skill-name>/
├── SKILL.md                          # frontmatter + body (required)
├── scripts/                          # optional, executable helpers
│   └── ...
└── references/                       # optional, supporting docs
    └── ...
```

`SKILL.md` frontmatter:

```yaml
---
name: <skill-name>             # snake-case identifier
description: <when to invoke>  # the trigger description Claude reads
---
```

The `description` is the most important field — it's what Claude reads to decide
whether the skill applies. Be specific: list trigger phrases, scope conditions,
and explicit non-triggers.

---

## Contributing

**For a new skill**: open an issue first to discuss scope. PRs welcome but the
bar is *"Markdown-clean, deterministic, no surprise side effects."* CI must pass;
`SKILL.md` frontmatter validation rules live in `.github/workflows/scripts/check_frontmatter.py`.

**For a new external-audit case-study**: the bar is intentionally low — if you
ran `mcp-audit` against a third-party MCP server and want to land your write-up
here, the workflow is:

1. Copy [`docs/case-studies/_TEMPLATE.md`](docs/case-studies/_TEMPLATE.md) into
   `docs/case-studies/<target-slug>-<YYYY-MM-DD>.md`.
2. Fill in frontmatter (`target_repo`, `target_commit`, `severity_summary`,
   `disclosure_status`).
3. Apply pickaxe discipline before any "silently removed" / "regression" / "novel"
   claim — see [`disclosure-sop.md`](docs/disclosure-sop.md) §6.6.
4. Add a row to `skills/mcp-audit/README.md` "Real-world case studies" table.
5. Open a PR. The five existing case-studies are working references.

The template + SOP + SEVERITY rubric are designed to make every case-study read
the same way regardless of who authored it. Diversity of targets, uniformity of
shape.

---

## Why these skills

These are skills that surfaced naturally during day-to-day work on the WRG
monorepo (4-agent orchestration, multi-app Python project, AI safety tooling).
They graduated from `~/.claude/skills/` into a published repo when the patterns
stopped being personal and started being reusable.

Adjacent ecosystem: [browserbase/skills](https://github.com/browserbase/skills)
(browser automation), [google/skills](https://github.com/google/skills)
(cloud-product domain experts), [anthropic-skills](https://github.com/anthropics/anthropic-skills)
(canonical first-party set).

---

## License

[MIT](LICENSE) — same as WRG core.
