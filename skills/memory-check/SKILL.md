---
name: memory-check
description: Pause and scan the current conversation for friction patterns that auto-memory might have missed — places where the user corrected the same kind of output repeatedly, fixes that keep coming back, or stylistic mismatches between what was produced and what was wanted. Use this skill when the user invokes `/memory-check`, types phrases like "memory check", "check for patterns", "what have I been correcting", "scan friction", "look for repeated fixes", "what should I remember from this session", or asks Claude to explicitly step back and audit what should be captured. Also use after a long working session before wrapping up, or when the same correction has happened ~3+ times and feels worth capturing into durable memory. Output is a structured report with three sections (correction patterns, repeated friction, real-time mismatches) plus draft memory entries the user can approve per-entry — this skill surfaces candidates, the user decides what to commit. Recall-discipline tool, not a memory writer.
---

# memory-check

Pauses normal flow and runs three explicit recall triggers on the recent
conversation to catch patterns that passive auto-memory might have missed.
Surfaces them as a structured report with draft memory entries the user can
approve, edit, or reject — never writes memory unilaterally.

## When to invoke

- User types `/memory-check`
- User explicitly asks Claude to look for patterns, friction, or repeated corrections
- After a long working session, before wrapping up
- When the same kind of correction has happened ~3+ times in the conversation and Claude wants to confirm before saving

## The three triggers

Adapted from AI Maker's *Ultimate Guide to Claude's Project Memory*, but
**explicit and on-demand** instead of always-on. The point is the deliberate
pause, not the prompts themselves.

### 1. Pattern detection mid-work

Look back at the entire conversation. Are there patterns in how the user has
corrected outputs? List specific corrections, count occurrences, group by
type. Do not just list individual fixes — group them.

### 2. Friction identification

Has the user been correcting the same *kind* of thing repeatedly? Identify
friction kinds (e.g. "I keep adding emojis when the user wants none", "I keep
explaining what code does when the user only wants the why"), not individual
mistakes.

### 3. Real-time naming

For any pattern surfaced in #1 or #2, name it as a rule a future Claude could
follow: *"I keep doing X when the user actually wants Y."* This is the form
that goes into a `feedback` memory entry's body.

## Output format

Always produce this structure, even if some sections are empty:

```
### Correction patterns
- <pattern> — N occurrences this session
  Examples: "<short quote 1>", "<short quote 2>"
- <pattern> — N occurrences
  …

### Repeated friction
- <friction kind> — what I keep doing wrong, what the user actually wants

### Real-time mismatches
- "I write X but the user wants Y" — phrased as a rule

### Draft memory entries
- (feedback) <name>: <one-line rule>
  **Why:** <reason from conversation>
  **How to apply:** <when/where this rule kicks in>
- (user) <name>: <fact about the user that informed a correction>
- (project) <name>: <project-specific fact, if surfaced>
```

If a section has nothing, write `(none this session)` rather than omitting it
— absence is informative.

## After surfacing — per-entry approval

For each draft memory entry, offer three actions:

- **Save** — Claude writes the entry to `~/.claude/projects/<slug>/memory/`
  using the standard format (frontmatter `name` + `description` + `type`, then
  body), and adds a one-line pointer to `MEMORY.md`.
- **Edit** — user revises the body or scope before save.
- **Skip** — discard. Pattern may resurface later if it keeps happening; the
  skill will catch it again.

Do **not** write any memory without explicit per-entry user approval. The
skill produces candidates; the user decides what is durable.

## Caps and discipline

- **Cap output at top 5 patterns.** If more surface, list the top 5 and mention
  the overflow count without enumerating.
- **Quote sparingly.** Two short example quotes per pattern is plenty — the
  user can scroll if they want full context.
- **Group by pattern, not by chronology.** Avoid replaying the conversation;
  this is a synthesis tool.
- **Always report something.** If nothing surfaces, output `Scanned <N> turns,
  no clear friction pattern this session.` Empty output is a result.

## What this is not

- Not a replacement for auto-memory — auto-memory still observes passively;
  this is a deliberate audit on top.
- Not a regex/heuristic scan — uses Claude's direct recall of the conversation.
- Not chronological — groups by pattern.
- Not silent — always reports, even if nothing was found.
- Not a memory writer — only a candidate surfacer with per-entry approval.
