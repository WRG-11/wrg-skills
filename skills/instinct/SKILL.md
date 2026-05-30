---
name: instinct
description: Self-learning pattern memory for AI coding agents. Record tool sequences, user preferences, and recurring fixes; let mature patterns auto-promote into rules that guide future sessions. Use when the user says "remember this pattern", "log this fix", "what have we seen before in this repo", "consolidate session memory", "tidy up memory", "what patterns have you learned", "show me instinct stats", or invokes "/instinct". Also trigger proactively when you notice you are repeating a fix, applying the same sequence a third time, or when the user corrects the same behavior twice. Do NOT use for per-session-only scratch notes (use regular memory), clipboard/paste operations, chat history search (that's conversation context), or when the user asks about Mem0 or claude-mem (those are different products). What makes instinct different: frequency-driven confidence (not LLM judgment), maturity tiers (raw/mature/rule/universal), automatic chain detection from timing, cross-project promotion, and multi-platform export.
---

> **Mirrored skill** — canonical source: [WRG-11/instinct@v1.4.1+](https://github.com/WRG-11/instinct/blob/master/.claude/skills/instinct/SKILL.md). This copy in `wrg-skills` exists for cross-discovery; for upstream changes, watch the [`instinct`](https://github.com/WRG-11/instinct) repo. Last sync: 2026-04-25 (post-merge of upstream PR #24).

# instinct skill

`instinct` is a self-learning memory layer for AI coding agents. It
observes patterns from your sessions, tracks confidence through repeated
reinforcement, auto-promotes recurring patterns into suggestions and
rules, and surfaces them in future sessions — without the user repeating
themselves.

Runs on top of the `instinct-mcp` server. No network calls, local
SQLite store.

## When to use

Trigger this skill when:

- User says **"remember this pattern"**, **"log this fix"**, **"save this preference"**
- User asks **"what have we seen before?"**, **"what patterns do you know?"**, **"any learned rules for this repo?"**
- User says **"consolidate memory"**, **"tidy up patterns"**, **"end-of-session summary"**
- User corrects the same behavior twice — record the correction as `pref:` or `fix:`
- You notice you are applying the same fix or sequence for the third time
- User explicitly invokes **`/instinct`**

**Do NOT trigger** when:

- User wants per-session scratch notes — use regular conversation memory
- User asks about **Mem0**, **claude-mem**, or other memory products — those are separate tools
- User wants clipboard or paste operations
- User wants chat history search — that's conversation context, not pattern memory

## Workflow

Typical flow across a session:

1. **Session start** — check for learned patterns:
   ```
   instinct__suggest project="<repo-name>"
   ```
   Apply patterns with confidence >= 10 (rules) automatically.
   Mention patterns with confidence 5-9 (mature) as soft suggestions.

2. **During work** — record observations as you spot them:
   ```
   instinct__observe pattern="fix:missing-await-in-handler" project="<repo-name>" explain="async handlers need await on db calls"
   ```
   Each re-observation increments confidence. A pattern observed 5+ times
   auto-promotes to "mature" (suggested); 10+ becomes a "rule" (auto-applied).

3. **Session end** — consolidate and summarize:
   ```
   instinct__session_summary project="<repo-name>"
   ```
   This runs consolidation (promotion + chain detection + FTS rebuild)
   and returns a digest of what was learned.

## Pattern naming convention

Always prefix pattern names with their type:

| Prefix | Shape | Example |
|---|---|---|
| `seq:` | tool/action sequence | `seq:lint->format->test` |
| `pref:` | user preference | `pref:commit-style=conventional` |
| `fix:` | recurring fix | `fix:missing-import-on-save` |
| `combo:` | things used together | `combo:pytest+ruff` |

## Tool quick reference

The server exposes 22 tools. These 8 cover day-to-day use:

| Tool | What it does |
|------|-------------|
| `observe` | Record one pattern observation; increments confidence (1=new, 5=mature, 10=rule) |
| `suggest` | Retrieve mature+ patterns (confidence >= 5) sorted by confidence; compact by default |
| `consolidate` | Promote patterns that crossed thresholds, detect chains, rebuild FTS index |
| `session_summary` | End-of-session snapshot: recent activity + top suggestions + stats + auto-consolidate |
| `search_instincts` | FTS5 keyword search across pattern keys, metadata, and explain text |
| `get_instinct` | Exact-key lookup for one pattern's full record |
| `stats` | Store health: totals, level distribution, category breakdown |
| `gc` | Housekeeping: decay stale patterns, merge duplicates, clean orphans, rebuild FTS |

Additional tools for specific workflows:

| Tool | What it does |
|------|-------------|
| `list_instincts` | Browse all patterns including low-confidence seedlings; supports filters |
| `alias_pattern` | Merge duplicate patterns by redirecting one key to another |
| `find_duplicates` | Detect near-identical pattern keys for merge candidates |
| `detect_chains` | Auto-create `seq:A->B` patterns from observation timing proximity |
| `effectiveness` | Measure confirmation rate of suggested patterns over a time window |
| `trending` | Rank patterns by recent observation velocity |
| `history` | Show one pattern's confidence timeline with timestamps |
| `import_patterns` | Bulk-insert many patterns in one call |
| `import_claude_md` | Parse and ingest patterns from a CLAUDE.md file |
| `export_rules` | Export rule-level patterns as structured JSON |
| `export_claude_md` | Render rules as Markdown for CLAUDE.md |
| `export_skill` | Package rules as a SKILL.md file |
| `export_platform` | Render rules for .cursorrules / .windsurfrules / AGENTS.md |
| `inject_claude_md` | Idempotently write rules into a CLAUDE.md file (marker-bounded block) |

## Do

- Prefix every pattern (`seq:`, `pref:`, `fix:`, `combo:`). Unprefixed
  patterns are harder to search and auto-promote.
- Include an `explain` string — it surfaces in suggestions and exports.
- Trust high-confidence rules — they survived repeated validation.
- Alias synonyms to keep the graph clean
  (`instinct__alias_pattern old="seq:a -> b" target="seq:a->b"`).
- Run `consolidate` or `session_summary` at end of session so promotions
  land before the next session reads them.

## Do not

- Do not observe personal or sensitive info. The store is local but the
  export paths (`export_claude_md`, `export_platform`) round-trip to disk.
- Do not record one-off fixes. If it will not happen again, let it fade.
- Do not manually inflate confidence by re-observing the same pattern in
  a tight loop — consolidate does that legitimately.
- Do not fight low-confidence suggestions. Apply them once, then let the
  feedback loop strengthen or demote them.

## What this skill is NOT

- **Not a clipboard or paste tool** — it doesn't store or retrieve arbitrary text
- **Not a chat memory replacement** — conversation context and session notes are separate concerns
- **Not Mem0 / claude-mem** — those are different products with different architectures
- **Not LLM-judgment-based** — instinct uses frequency and recency, not model evaluation, to rank patterns
- **Not a real-time guard** — it's a learning layer, not a runtime blocker

## Install

```bash
pip install instinct-mcp
claude mcp add instinct -- instinct serve
```

Or in any MCP-compatible client's config:

```json
{
  "mcpServers": {
    "instinct": {
      "command": "instinct",
      "args": ["serve"]
    }
  }
}
```

---

**Sync note for `wrg-skills` maintainers**: this is a mirror, not a fork. To
pick up upstream improvements, re-copy from
`WRG-11/instinct/.claude/skills/instinct/SKILL.md` and bump the "Last
sync" date in the provenance line above. Drift detection should eventually
land as a CI step that hashes the upstream file and compares; until then,
manual sync on a quarterly cadence (or when upstream releases new minor /
ships a meaningful skill polish) is the convention.
