---
target_repo: modelcontextprotocol/servers
target_commit: 4503e2d
target_package: '@modelcontextprotocol/server-memory@0.6.3'
audit_date: 2026-04-26
auditor: yakuphanycl (Claude Code)
skill_version: skills/mcp-audit @ 3ee91e4
severity_rubric: skills/mcp-audit/SEVERITY.md @ 3ee91e4
mcp_servers_audited:
  - src/memory/index.ts
severity_summary:
  critical: 0
  high: 0
  medium: 0
  low: 2
  info: 1
disclosure_status: public
---

# `modelcontextprotocol/servers` MCP audit — memory server (2026-04-26)

> Audited the `@modelcontextprotocol/server-memory` MCP surface (9 tools
> registered via `server.registerTool` against a file-backed JSONL
> knowledge graph). First audit on a **stateful** surface — prior three
> audits (filesystem TS, fetch FastMCP, git low-level Python) were all
> pure-functional. The state interaction surfaced one new finding class.
>
> No Critical / High / Medium findings. Two **Low** (one MCP-layer test
> gap shared with the git audit; one **non-atomic file write** that can
> torn-read or lose data on crash) and one **Info** (in-code Tool()
> descriptions are one-liners lacking when-to-use + return-shape).
>
> F-002 + F-003 batched into upstream
> [`modelcontextprotocol/servers#4049`](https://github.com/modelcontextprotocol/servers/pull/4049);
> F-001 deferred. F-002 fix is partial (atomic write addresses
> crash-mid-write and torn reads; an in-process mutex for the
> loadGraph→mutate→saveGraph race is flagged as a follow-up).

---

## 1. Scope

**In scope**
- Server: `src/memory/index.ts` — 9 tools registered via
  `server.registerTool(name, config, handler)` against a single
  `KnowledgeGraphManager` instance backed by a JSONL file at
  `MEMORY_FILE_PATH` (env override) or `./memory.jsonl` (default).
- Commit audited: [`4503e2d`](https://github.com/modelcontextprotocol/servers/commit/4503e2d)
  (`upstream/main` at audit date).
- Package: `@modelcontextprotocol/server-memory@0.6.3`.
- Adjacent surfaces examined: `src/memory/README.md`,
  `src/memory/__tests__/knowledge-graph.test.ts`,
  `src/memory/__tests__/file-path.test.ts`,
  `src/memory/package.json`.

**Out of scope**
- Performance benchmarks
- Static security scans (no secrets / network surface)
- Other servers in the monorepo: `src/filesystem` (audited separately
  as [`filesystem-mcp-2026-04-26.md`](filesystem-mcp-2026-04-26.md)),
  `src/git` (audited separately as
  [`git-mcp-2026-04-26.md`](git-mcp-2026-04-26.md)), `src/time`
  (audited in parallel by another auditor)

**Constraints**
- Read-only audit. No code executed against any live MCP client.
- No mutation tools invoked. No real memory file touched.
- All findings derived from source inspection, grep, docstring review,
  and reading the test fixtures.

---

## 2. Methodology

The audit applies the [`mcp-audit` skill](../../skills/mcp-audit/SKILL.md):
five axes scored per tool (discoverability, return-shape, naming, error
handling, test coverage), plus decay-candidate detection across four
signals.

Severity bucketing uses the default rubric in
[`skills/mcp-audit/SEVERITY.md`](../../skills/mcp-audit/SEVERITY.md).

Disclosure handling follows [`docs/disclosure-sop.md`](../disclosure-sop.md).

**Methodology adaptation — stateful axis**: this is the first audit
applied to a server with persistent state. The five canonical axes were
extended with a sixth pass on state-handling discipline:

| Sub-axis | What was checked |
|---|---|
| Concurrency | Are two parallel tool calls safe against each other (file lock, atomic write, version check)? |
| Persistence | Does state survive process restart? Is that exercised by tests? |
| Cleanup | Tool-side teardown vs fixture-side? |
| State leakage | Can one tool's state-mutation surprise another? |

This sixth pass surfaced **F-002** (non-atomic file write) — a finding
that none of the prior three pure-functional audits could have produced.
Recommended SEVERITY.md additions are documented in §6 as
candidate `STATE-*` rows.

**Honest-scoring discipline**: discoverability average came out at
3.22/5 — slightly above git's 3.00/5, well below filesystem's 4.50/5.
Descriptions are informative WHAT-statements but lack when-to-use +
return-shape; not padded, not deflated.

---

## 3. Findings

### 3.0 Findings matrix

| finding_id | section | severity | status | upstream_link |
|---|---|---|---|---|
| F-001 | `TEST-001` (surface-wide) — no MCP-layer dispatch test for the 9 `server.registerTool` handlers | Low | deferred (next-session backlog) | — |
| F-002 | proposed `STATE-001` (mapped from `SHAPE-004` analogy) — `saveGraph()` truncate-and-writes the live file with no atomic rename and no concurrency control | Low (override de-escalated from default Medium; rationale below) | reported (partial fix) | [`modelcontextprotocol/servers#4049`](https://github.com/modelcontextprotocol/servers/pull/4049) |
| F-003 | `DISC-002` + `DISC-004` (surface-wide) — 9/9 in-code Tool() descriptions are one-liners lacking when-to-use + return-shape doc | Info | reported | [`modelcontextprotocol/servers#4049`](https://github.com/modelcontextprotocol/servers/pull/4049) |

### 3.1 Critical
None.

### 3.2 High
None. Notable absences:
- No hardcoded credentials, no `eval`/`exec`, no `subprocess`.
- No HTTP / network surface (stdio-only MCP transport).
- Path handling: `MEMORY_FILE_PATH` is operator-controlled (env var),
  not tool-arg-controlled — no path-traversal vector reachable from a
  tool call.
- File writes are scoped to the configured `MEMORY_FILE_PATH`; no
  arbitrary write surface.

### 3.3 Medium
None.

### 3.4 Low

#### F-001 — No MCP-layer dispatch test (surface-wide)
- **Where**: `src/memory/__tests__/knowledge-graph.test.ts` — every test
  imports `KnowledgeGraphManager` directly and calls its methods. None
  round-trip through the `server.registerTool` handler dispatch.
- **What**: 9/9 tools have store-layer tests via the manager class
  (excellent coverage, including persistence + cascade-delete + JSONL
  round-trip + type-field strip on load). 0/9 are exercised through the
  actual MCP wrapper — the handlers in `index.ts:262-470` that call
  `JSON.stringify` on the result and return `{content, structuredContent}`.
- **Why this bucket**: SEVERITY row [`TEST-001`](../../skills/mcp-audit/SEVERITY.md)
  (no MCP-layer test for non-mutation tool), applied surface-wide.
  Default Low — failure would be observable to the caller; not a
  blast-radius issue.
- **Suggested fix**: add a small integration test using
  `@modelcontextprotocol/sdk/client` + `StdioClientTransport` (the same
  pattern used in `src/filesystem/__tests__/structured-content.test.ts`)
  that round-trips a representative tool from each family
  (create / delete / read / search / open). Estimate ~1-2 hr including
  fixture boilerplate.
- **Disclosure**: deferred. Real Low coverage debt; needs separate PR
  scope. Recommend the maintainer file a follow-up issue or treat this
  case-study as the public record.

#### F-002 — Non-atomic file write (state-handling axis)
- **Where**: `src/memory/index.ts:101-117` — `KnowledgeGraphManager.saveGraph`.
- **What**: `await fs.writeFile(this.memoryFilePath, lines.join("\n"))`
  truncates and writes the live file in a single non-atomic call. There
  is no concurrency control elsewhere in the class. Two failure modes:
  1. **Crash mid-write**: a process killed between truncate and
     buffer-flush leaves the live file empty or partial. Next read hits
     the `loadGraph` ENOENT branch (line 94-96) which silently returns
     `{entities: [], relations: []}` — data loss is **silent**.
  2. **Concurrent reader**: a tool call beginning `loadGraph` while
     another is mid-`saveGraph` can observe a torn JSONL file (lines
     that don't `JSON.parse`).
- **Why this bucket**: closest existing SEVERITY row is
  [`SHAPE-004`](../../skills/mcp-audit/SEVERITY.md) (silent failure
  obscures the problem). Default for SHAPE-004 is **Medium**.
  **OVERRIDE: de-escalated to Low.** Rationale: the failure mode is
  publicly visible in source (not a private discovery); the typical
  deployment pattern (one server process per Claude session, default
  per-package-install file path) makes data loss in practice rare; the
  fix shape is well-known (atomic rename + advisory lock); routing
  through coordinated 90-day disclosure for an architectural
  observation that any source reader can see would be theatre. Public
  PR with the fix is the appropriate route.
- **Reproduction (audit-only, no live exploitation)**:
  1. `await manager.createEntities([{name: "X", ...}])` — kicks off
     `fs.writeFile`.
  2. SIGKILL the process before the buffer flushes.
  3. Restart server. `loadGraph()` returns empty. The "X" entity is
     gone with no error indication to the caller.
- **Suggested fix (this PR)**: write to
  `<memoryFilePath>.tmp.<pid>.<ts>` then `fs.rename` into place. Atomic
  on POSIX, same-volume best-effort on Windows. Strict improvement —
  the live file is now always either the pre-existing valid snapshot
  or the new valid snapshot, never torn. Two new tests assert (a) the
  live file always parses as valid JSONL after a save and (b) no
  `<file>.tmp.*` stragglers remain.
- **Suggested fix (follow-up, NOT in this PR)**: in-process write
  mutex to prevent the broader `loadGraph→mutate→saveGraph` race.
  Two parallel tool calls can each read the same pre-state and one's
  mutation can overwrite the other's. The atomic-write fix doesn't
  address this — it makes the *file* always consistent but doesn't
  serialise the *operations*. Recommend `async-mutex`-style serialiser
  or a chained `Promise` pattern. Flagged as next-session.
- **Disclosure**: included in [`#4049`](https://github.com/modelcontextprotocol/servers/pull/4049)
  (atomic-write portion). Mutex follow-up flagged in PR body.

### 3.5 Info

#### F-003 — In-code Tool() descriptions lack when-to-use + return-shape (surface-wide)
- **Where**: `src/memory/index.ts:262-470` — all 9 `server.registerTool`
  entries.
- **What**: descriptions are short WHAT-statements ("Create multiple
  new entities in the knowledge graph"). Per the discoverability
  rubric, they have 1 of 3 axes (WHAT) and lack the other two
  (when-to-use, return-shape doc). Per-tool score: 7×3/5, 2×4/5
  (`create_relations` mentions active voice, `delete_entities`
  mentions cascade). **Average: 3.22/5**.

  README has structured Input/Returns blocks, but agents reading the
  MCP tool surface only see the in-code description. Argument-level
  Zod `.describe()` calls help slightly (not counted in the 1-5
  rubric, which scores the top-level description).
- **Why this bucket**: SEVERITY rows [`DISC-002`](../../skills/mcp-audit/SEVERITY.md)
  (missing when-to-use) + [`DISC-004`](../../skills/mcp-audit/SEVERITY.md)
  (missing return-shape doc), applied as one surface-wide finding
  (single-PR fix). Default Info.
- **Suggested fix**: rewrite each description to a consistent shape:
  WHAT (preserved) + when-to-use clause + return-shape hint +
  silent-skip behaviour. The "silent skip on duplicate / non-existent /
  unknown" semantics (currently inferable only from tests) become
  discoverable from the tool surface itself.
- **Disclosure**: included in [`#4049`](https://github.com/modelcontextprotocol/servers/pull/4049).

---

## 4. Disclosure timeline

| date | actor | event |
|---|---|---|
| 2026-04-26 | auditor | Audit completed against commit `4503e2d` |
| 2026-04-26 | auditor | Severity scan: 0 Critical / 0 High / 0 Medium → no GHSA needed |
| 2026-04-26 | auditor | F-002 severity reviewed: default Medium per SHAPE-004 analogy → **OVERRIDE de-escalated to Low** (publicly observable architectural pattern, public-PR route appropriate) |
| 2026-04-26 | auditor | Pickaxe check for prior upstream art: `gh search issues/prs` for "memory race condition", "memory atomic write", "memory.jsonl lock" — zero results. F-002 is novel. |
| 2026-04-26 | auditor | Upstream batched fix PR opened: [`#4049`](https://github.com/modelcontextprotocol/servers/pull/4049) |
| 2026-04-26 | auditor | Public case-study published (this document) |

---

## 5. Upstream response

**Acknowledgement**: pending. PR opened 2026-04-26; awaiting maintainer review.

**Patches landed**: none yet (PR open).

**Patches declined / wontfix**: none.

**Outstanding**
- F-002 (atomic write portion) + F-003 → in
  [`#4049`](https://github.com/modelcontextprotocol/servers/pull/4049),
  pending review.
- F-001 → not yet reported as separate issue; recommend the maintainer
  treat this case-study as the public record and file a follow-up.
- F-002 follow-up (in-process mutex) → not yet reported as separate
  issue; flagged in PR body and in this case-study's §6.

---

## 6. Reusable patterns

Patterns observed that should feed back into the audit infrastructure:

- **Pattern**: stateful axis as a sixth pass alongside the canonical five
  - **Observed in**: F-002 (would not have surfaced from the canonical
    five axes alone — `SHAPE-004` was the closest existing row but
    didn't quite fit because there's no exception being swallowed; the
    issue is the absence of atomicity).
  - **Generalises because**: stateful MCP servers are common
    (memory-style stores, session caches, KV servers, sequence
    counters). The pure-functional axes don't catch concurrency
    discipline issues.
  - **Proposed action**: add a "stateful surface adaptation" subsection
    to [`SKILL.md`](../../skills/mcp-audit/SKILL.md) (parallel to the
    TS-adaptation subsection from `wrg-skills#8`). Subsection content:
    *"For servers that persist state, additionally audit: (a) atomic
    write — does a successful save leave the canonical store always
    valid? (b) concurrency — are two parallel tool calls safe against
    each other? (c) persistence — does state survive restart, and
    is that tested? (d) state leakage — can one tool's mutation
    surprise another?"*
  - **Tracked as**: candidate SKILL.md update; not in scope for this
    audit per briefing constraint.

- **Pattern**: candidate new `STATE-*` rows for SEVERITY.md
  - **Observed in**: F-002 mapping difficulty.
  - **Generalises because**: F-002 maps loosely to `SHAPE-004` but the
    fit is imperfect. A dedicated row would make future audits cleaner.
  - **Proposed action**: add to [`SEVERITY.md`](../../skills/mcp-audit/SEVERITY.md)
    in a follow-up PR:
    - `STATE-001`: non-atomic write to canonical store (live file
      observable mid-write). Default Low.
    - `STATE-002`: missing in-process serialiser for
      load→mutate→save sequences (lost-write race across parallel
      tool calls). Default Medium (data loss is silent and harder to
      detect than torn reads).
    - `STATE-003`: state survives restart but persistence not tested.
      Default Info.
    - `STATE-004`: state leakage — one tool's mutation observable
      from another tool's response in unexpected way. Default Medium
      (information disclosure or correctness violation depending on
      context).
  - **Tracked as**: candidate SEVERITY.md update; not in scope for
    this audit per briefing constraint.

- **Pattern**: per-ecosystem canonical return shape, fourth
  confirmation
  - **Observed in**: §3 reasoning (no SHAPE finding even though the
    per-tool `structuredContent` shape varies — `{entities}`,
    `{relations}`, `{results}`, `{success, message}`).
  - **Generalises because**: each tool's `structuredContent` matches
    its declared `outputSchema` (verified 9/9). The variation is
    legitimate per-tool typing, not inconsistency. Fourth surface to
    confirm the per-ecosystem-canonical-shape discipline (after TS
    filesystem with `{content, structuredContent}`, Python instinct
    with `{ok}`, Python git with `[TextContent]`).
  - **Proposed action**: confirmed pattern, no action.
  - **Tracked as**: confirmed.

- **Pattern**: pickaxe discipline applied to "novel" findings
  - **Observed in**: before claiming F-002 was novel, ran
    `gh search issues --repo modelcontextprotocol/servers "memory race
    condition"`, `"memory atomic write"`, `"memory.jsonl lock"`,
    `"memory concurrent"` — all returned zero results.
  - **Generalises because**: the wave-2 lesson (false-positive
    "silently removed" attribution) suggests every "this is new"
    claim should be verified against the upstream tracker, not just
    against current source. Did this here.
  - **Proposed action**: case-study format already accommodates this
    via the disclosure timeline ("Pickaxe check..."). Worth
    formalising in SKILL.md as a discovery-prerequisite step before
    raising any STATE-class or novel finding.
  - **Tracked as**: confirmed pattern, candidate SKILL.md addition.

---

## Appendix A — tool inventory

Total tools: **9** (single module: `src/memory/index.ts`).

Storage backend: file-backed JSONL at `MEMORY_FILE_PATH` (env override) or
`./memory.jsonl` (default, co-located with package install). Backward-compat:
auto-migrates `memory.json` → `memory.jsonl` on first startup if old file
exists.

| # | Tool | Line | Args | outputSchema | structuredContent shape | MCP test | Disc. |
|---|------|------|------|---|---|---|-------|
| 1 | `create_entities` | 262 | `(entities: Entity[])` | `{entities: Entity[]}` | `{entities: result}` | none | **3** |
| 2 | `create_relations` | 284 | `(relations: Relation[])` | `{relations: Relation[]}` | `{relations: result}` | none | **4** |
| 3 | `add_observations` | 306 | `(observations: {entityName, contents}[])` | `{results: {entityName, addedObservations}[]}` | `{results: result}` | none | **3** |
| 4 | `delete_entities` | 334 | `(entityNames: string[])` | `{success: bool, message: str}` | `{success: true, message}` | none | **4** |
| 5 | `delete_observations` | 357 | `(deletions: {entityName, observations}[])` | `{success: bool, message: str}` | `{success: true, message}` | none | **3** |
| 6 | `delete_relations` | 383 | `(relations: Relation[])` | `{success: bool, message: str}` | `{success: true, message}` | none | **3** |
| 7 | `read_graph` | 406 | `()` | `{entities, relations}` | `{...graph}` | none | **3** |
| 8 | `search_nodes` | 427 | `(query: string)` | `{entities, relations}` | `{...graph}` | none | **3** |
| 9 | `open_nodes` | 450 | `(names: string[])` | `{entities, relations}` | `{...graph}` | none | **3** |

`outputSchema` matches `structuredContent` 9/9 — no `as unknown as
CallToolResult` casts (no `SHAPE-005`). Best-in-class internal type
consistency.

## Appendix B — methodology drift

- **Inventory adaptation**: TypeScript / FastMCP-style `server.registerTool`,
  same shape as filesystem audit (`wrg-skills#8` TS-adaptation subsection
  applied). No new adaptation needed for inventory.
- **Stateful axis**: this is the new methodology dimension surfaced
  here; documented in §6 as a candidate SKILL.md addition (not applied
  to SKILL.md in this audit per scope constraint).
- **Severity override**: F-002 default Medium → Low de-escalation
  documented inline with explicit rationale per SEVERITY.md "Override
  conventions". This is the first case-study to use the override
  mechanism.
- **No CHANGELOG file**: provenance traced via `git log -- src/memory/`
  (recent activity #3206 license update, #3065 SDK update; older
  #3015 modern SDK migration). No tools are decay candidates.
