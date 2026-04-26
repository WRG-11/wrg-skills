# External MCP audit index

This index summarises external MCP server audits performed using the
[`mcp-audit` skill](../skills/mcp-audit/SKILL.md). As of 2026-04-26,
**5 audits across 3 ecosystems** (TypeScript MCP SDK, Python low-level SDK,
Python FastMCP-style) are complete. All target the
[`modelcontextprotocol/servers`](https://github.com/modelcontextprotocol/servers)
reference monorepo.

**Aggregate result**: 0 Critical / 0 High / 0 Medium / 13 Low / 6 Info
across 38 tools and 1 prompt. No GHSA filed. 5 upstream PRs opened, all
public. The framework produces consistent, actionable findings — but the
reference servers are well-maintained, so the findings are Low/Info class
(test gaps, docstring gaps, one return-shape deviation, one non-atomic write).

---

## Per-audit summaries

### 1. `@modelcontextprotocol/server-filesystem@0.6.3`

| | |
|---|---|
| **Audit date** | 2026-04-26 |
| **Variant** | Full (5-axis) |
| **Surface** | 14 tools (TypeScript MCP SDK, `server.registerTool`) |
| **Severity** | 0/0/0/6/2 (C/H/M/L/I) |
| **What we found** | 12 of 14 tools lacked MCP-layer integration tests (F-001..F-005, batched). `read_media_file` envelope deviates from the 13 siblings (SHAPE-001). `read_file` partially decayed (deprecated but still registered). |
| **Case-study** | [`filesystem-mcp-2026-04-26.md`](case-studies/filesystem-mcp-2026-04-26.md) |
| **WRG evidence** | [WRG#307](https://github.com/yakuphanycl/WinstonRedGuard/pull/307) |
| **Upstream PRs** | [#4045](https://github.com/modelcontextprotocol/servers/pull/4045) (F-006 fix), [#4046](https://github.com/modelcontextprotocol/servers/pull/4046) (F-001..F-005 tests), [#4047](https://github.com/modelcontextprotocol/servers/pull/4047) (F-007+F-008 docs) |

### 2. `mcp-server-fetch@0.6.3`

| | |
|---|---|
| **Audit date** | 2026-04-26 |
| **Variant** | Full (5-axis) |
| **Surface** | 1 tool + 1 prompt (Python low-level `mcp.server.Server`) |
| **Severity** | 0/0/0/2/2 (C/H/M/L/I) |
| **What we found** | SSRF posture: tool fetches arbitrary URLs without IP/host allowlist — maintainer-tracked via [#2317](https://github.com/modelcontextprotocol/servers/issues/2317) since 2025-07-10, README CAUTION warns users. No MCP-layer integration test. Missing return-shape docs. No CHANGELOG. |
| **Case-study** | [`fetch-mcp-2026-04-26.md`](case-studies/fetch-mcp-2026-04-26.md) |
| **WRG evidence** | [WRG#308](https://github.com/yakuphanycl/WinstonRedGuard/pull/308) |
| **Upstream** | Comment on existing [#2317](https://github.com/modelcontextprotocol/servers/issues/2317); no new PR |

### 3. `mcp-server-git@0.6.2`

| | |
|---|---|
| **Audit date** | 2026-04-26 |
| **Variant** | Full (5-axis) |
| **Surface** | 12 tools (Python low-level `mcp.server.Server`) |
| **Severity** | 0/0/0/2/1 (C/H/M/L/I) |
| **What we found** | `git_branch` returns error string while 11 peers raise `McpError` (ERR-002). No MCP-layer dispatch test. 12/12 tool descriptions lack when-to-use + return-shape guidance. Security posture strong: active path-traversal, symlink-escape, and flag-injection defences, all with tests. |
| **Case-study** | [`git-mcp-2026-04-26.md`](case-studies/git-mcp-2026-04-26.md) |
| **WRG evidence** | [WRG#309](https://github.com/yakuphanycl/WinstonRedGuard/pull/309) |
| **Upstream PR** | [#4048](https://github.com/modelcontextprotocol/servers/pull/4048) (F-001 error fix + F-003 docs) |

### 4. `@modelcontextprotocol/server-memory@0.6.3`

| | |
|---|---|
| **Audit date** | 2026-04-26 |
| **Variant** | Full (5-axis) — first stateful-surface audit |
| **Surface** | 9 tools (TypeScript MCP SDK, `server.registerTool`, file-backed JSONL knowledge graph) |
| **Severity** | 0/0/0/2/1 (C/H/M/L/I) |
| **What we found** | Non-atomic file write: `saveGraph()` truncate-and-writes with no rename and no concurrency control — crash-mid-write loses data. No MCP-layer dispatch test. 9/9 tool descriptions are one-liners. First audit to surface a stateful finding class (proposed STATE-001). |
| **Case-study** | [`memory-mcp-2026-04-26.md`](case-studies/memory-mcp-2026-04-26.md) |
| **WRG evidence** | [WRG#311](https://github.com/yakuphanycl/WinstonRedGuard/pull/311) |
| **Upstream PR** | [#4049](https://github.com/modelcontextprotocol/servers/pull/4049) (F-002 atomic write + F-003 docs) |

### 5. `mcp-server-time@0.6.2`

| | |
|---|---|
| **Audit date** | 2026-04-26 |
| **Variant** | **Lite scan** (security + test axes only; §6.5 first validation) |
| **Surface** | 2 tools (Python low-level `mcp.server.Server`) |
| **Severity** | 0/0/0/1/0 (C/H/M/L/I) |
| **What we found** | Zero security findings — pure-computation server with no external-system interaction (6 of 9 SEC checks N/A). No MCP-layer integration test, but ~30 unit tests with excellent edge-case coverage (DST transitions, fractional offsets, date-line crossings). |
| **Case-study** | [`time-mcp-2026-04-26.md`](case-studies/time-mcp-2026-04-26.md) |
| **WRG evidence** | [WRG#310](https://github.com/yakuphanycl/WinstonRedGuard/pull/310) |
| **Upstream** | None needed |

---

## Aggregate table

| Target | Date | Tools | Variant | C | H | M | L | I | Status | Upstream | Case-study |
|---|---|---|---|---|---|---|---|---|---|---|---|
| filesystem (TS) | 2026-04-26 | 14 | full | 0 | 0 | 0 | 6 | 2 | public | [#4045](https://github.com/modelcontextprotocol/servers/pull/4045) [#4046](https://github.com/modelcontextprotocol/servers/pull/4046) [#4047](https://github.com/modelcontextprotocol/servers/pull/4047) | [filesystem](case-studies/filesystem-mcp-2026-04-26.md) |
| fetch (Py) | 2026-04-26 | 1+1p | full | 0 | 0 | 0 | 2 | 2 | public | [#2317](https://github.com/modelcontextprotocol/servers/issues/2317) comment | [fetch](case-studies/fetch-mcp-2026-04-26.md) |
| git (Py) | 2026-04-26 | 12 | full | 0 | 0 | 0 | 2 | 1 | public | [#4048](https://github.com/modelcontextprotocol/servers/pull/4048) | [git](case-studies/git-mcp-2026-04-26.md) |
| memory (TS) | 2026-04-26 | 9 | full | 0 | 0 | 0 | 2 | 1 | public | [#4049](https://github.com/modelcontextprotocol/servers/pull/4049) | [memory](case-studies/memory-mcp-2026-04-26.md) |
| time (Py) | 2026-04-26 | 2 | lite | 0 | 0 | 0 | 1 | 0 | public | — | [time](case-studies/time-mcp-2026-04-26.md) |
| **Total** | | **38+1p** | | **0** | **0** | **0** | **13** | **6** | | **5 PRs + 1 issue comment** | |

---

## Cross-cutting findings

### Common Low findings

| Pattern | Audits affected | Notes |
|---|---|---|
| TEST-001: No MCP-layer integration test | **5/5** (filesystem, fetch, git, memory, time) | Universal pattern across the reference servers. Unit tests exist in all 5, but none exercise the Client→Server→dispatch→response round-trip. Filesystem has the largest gap (12 tools untested at MCP layer); time has the narrowest (trivial dispatch over well-tested business logic). |
| ERR-002: Inconsistent error idiom | 1/5 (git) | `git_branch` returns error string while 11 peers raise `McpError`. Isolated to one tool. |
| SHAPE-001: Return-shape deviation | 1/5 (filesystem) | `read_media_file` returns `content: array` while 13 siblings return `content: string`. Architectural — matches its outputSchema but breaks sibling consistency. |
| STATE-001 (proposed): Non-atomic file write | 1/5 (memory) | `saveGraph()` truncate-and-writes a live JSONL file. Crash-mid-write loses data. Novel finding class for stateful surfaces. |

### Common Info findings

| Pattern | Audits affected | Notes |
|---|---|---|
| DISC-002/DISC-004: Docstring gaps | 3/5 (filesystem, git, memory) | In-code Tool() descriptions lack when-to-use guidance and/or return-shape documentation. Surface-wide in git (12/12) and memory (9/9). Filesystem has 2 isolated gaps. |
| DECAY-002/DECAY-003: Partial decay / no CHANGELOG | 2/5 (filesystem, fetch) | `read_file` is deprecated but still registered (filesystem). No per-package CHANGELOG (fetch, but monorepo-wide pattern). |
| SEC-004: SSRF posture (de-escalated) | 1/5 (fetch) | Documented limitation with maintainer-tracked enhancement. |

### Override convention usage

Three distinct override patterns have been applied across these audits:

| Override type | Audit | Finding | Direction | Rationale |
|---|---|---|---|---|
| Medium-as-patch (de-escalated ×4) | filesystem | F-002..F-005 (TEST-003 → Low) | Medium → Low | Mutation tools lack MCP-layer test, but unit tests cover the underlying filesystem operations |
| Maintainer-tracked-documented | fetch | F-001 (SEC-004 → Low) | High → Low | Maintainer aware via [#2317](https://github.com/modelcontextprotocol/servers/issues/2317), README CAUTION, labelled `enhancement` |
| Novel-architectural (de-escalated) | memory | F-002 (SHAPE-004 analogy → Low) | Medium → Low | Non-atomic write is a correctness issue, not a security vulnerability; single-user reference server |

### Disclosure SOP routing distribution

| Route | Count | Examples |
|---|---|---|
| Public upstream PR | 5 | #4045, #4046, #4047, #4048, #4049 |
| Comment on existing issue | 1 | [#2317](https://github.com/modelcontextprotocol/servers/issues/2317) (fetch SSRF) |
| GHSA filed | 0 | — |
| Declined / deferred | 2 findings | TEST-001 deferred in git + memory (next-session backlog) |

The GHSA gate in the disclosure SOP was tested once (fetch F-001 initially flagged as Medium) and correctly prevented a false-positive escalation after pickaxe verification downgraded the finding.

---

## 3-ecosystem triangulation

| Ecosystem | Servers audited | Canonical envelope | Example tool return | Tool count |
|---|---|---|---|---|
| TypeScript MCP SDK (`server.registerTool`) | filesystem, memory | `{content: [{type, text}], structuredContent: {content: ...}}` | `structuredContent.content` is a string (13/14) or array (1/14 `read_media_file`) | 23 |
| Python low-level SDK (`@server.call_tool()`) | fetch, git, time | `[TextContent(type="text", text=...)]` | Single `TextContent` with JSON-serialized payload or plain text | 15+1p |
| Python FastMCP (`@mcp.tool()`) | *(none in reference servers)* | — | — | 0 |

**Observations**:
- TypeScript servers use `structuredContent` (SDK 1.26+ feature) with Zod `outputSchema` validation. Python servers return raw `TextContent` with no schema enforcement.
- Return-shape consistency is higher within each ecosystem than across them. This is expected — the SDK layer imposes different idioms.
- The Python low-level SDK servers (fetch, git, time) all use the same `[TextContent(...)]` pattern. git wraps content in JSON; fetch and time do too; fetch adds a `"Contents of {url}:\n"` prefix.
- No FastMCP (`@mcp.tool()`) servers exist in the reference monorepo. The skill was originally designed for FastMCP; all 5 audits required framework adaptation. This is noted as a skill-improvement opportunity.

---

## Lessons learned

For full discussion, see [retro #10](retrospectives/first-external-audit-2026-04-26.md).

1. **Pickaxe-for-novel-findings**: the fetch audit's F-001 was initially mis-attributed
   as a "regression" based on a cross-branch `git diff`. Pickaxe verification (`git log -S`,
   `git branch --contains`) corrected the claim pre-disclosure. The git and memory audits
   applied pickaxe proactively (zero false positives in those audits). Now a mandatory step
   in the audit procedure.

2. **Lite-scan variant validated**: the time audit (2 tools, §6.5 dogfood) confirmed that
   for <10-tool servers, skipping discoverability/return-shape/naming/decay axes saves ~60%
   of analysis time with zero loss of actionable findings. All 3 skipped axes would have
   trivially passed.

3. **Override convention**: 3 distinct de-escalation patterns are now live — Medium-as-patch
   (filesystem ×4), maintainer-tracked-documented (fetch ×1), and novel-architectural
   (memory ×1). Each has a clear rationale that can be reused in future audits.

4. **Stateful-surface axis**: the memory audit surfaced a finding class (non-atomic file
   write) that does not map cleanly to any existing SEVERITY.md row. Proposed as STATE-001;
   candidate for a 6th axis in future skill revisions.

5. **Disclosure SOP gate works**: the GHSA gate caught the fetch false-positive before any
   upstream filing. Cost: one extra review cycle. Benefit: avoided filing a duplicate of an
   existing maintainer-tracked enhancement issue.

6. **TEST-001 is universal**: all 5 reference servers lack MCP-layer integration tests.
   This is the single most common finding class. It suggests the MCP ecosystem has a
   testing-culture gap at the protocol layer (unit tests are common; round-trip tests are
   not).

---

## How this index is maintained

When a new audit lands:

1. Add a per-audit summary card (§ above) with the standard fields.
2. Add a row to the aggregate table.
3. Update cross-cutting findings if the new audit introduces or reinforces a pattern.
4. Update the 3-ecosystem triangulation if a new ecosystem is audited.
5. Update the opening paragraph's count and date.

The case-study documents in `docs/case-studies/` are the source of truth for individual
findings. This index synthesises but never duplicates finding detail — always link to the
case-study for specifics.
