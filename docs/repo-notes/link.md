# link (`gowtham0992/link`)

_Refreshed 2026-05-18 against upstream HEAD 88f07ba; 333 commits / 129 files reviewed._

## 1. Purpose and scope

Link has materially repositioned itself between the prior repo-note and 2026-05-18: it is no longer "the most shippable
LLM-wiki engine" but **local agent memory** for MCP clients, with the markdown wiki recast as the inspectable storage
layer behind that memory. The 1.1.0 release (2026-05-08) added a full memory lifecycle — `remember`, `recall`, `propose`,
`capture-session`, `accept-capture`, `redact-capture`, `archive-memory`, `restore-memory`, `forget-memory`,
`explain-memory`, `update-memory`, `memory-audit`, `memory-inbox`, `review-memory` — exposed via CLI, the `link-mcp` PyPI
package, and `serve.py`'s HTTP API. The README pitch is "give Codex, Claude, Cursor, Kiro, VS Code, Copilot, and other
MCP clients the same durable memory about you and your work," with sources, backlinks, graph context, review state, and
an audit trail. For Linus this changes the framing entirely: Link is now a candidate substrate for the memory pillar's
Layer C (cross-session episodic) and Layer E (semantic knowledge), not just a Phase 2 KB companion. Still single-file
stdlib-only Python plus the `mcp` SDK; still local-first, MIT, no telemetry, no external calls; now Homebrew-installable
via `gowtham0992/link/link` tap.

## 2. Architecture summary

Same plain-markdown-in-a-directory substrate as before — `wiki/sources/`, `wiki/concepts/`, `wiki/entities/`,
`wiki/comparisons/`, `wiki/explorations/`, `wiki/index.md`, `wiki/log.md`, `_backlinks.json` — plus a new
`wiki/memories/` tree carrying typed memory pages (`memory_type: preference | decision | project | fact | note`,
`scope: user | project | global`, `status: active | stale | archived`, `review_status: pending | reviewed | needs_update`,
`update_count`, `last_update_source`). The `LINK.md` schema document at repo root has grown to cover memory page
templates alongside source/concept/entity templates. The MCP server in `mcp_package/link_mcp/server.py` (still FastMCP)
now exposes a much larger surface — the prior 6 tools plus `query_link` (the headline budgeted answer-ready packet with
relevant memories, pages, graph neighborhood, reasons, and follow-up actions), `memory_brief`, `ingest_status`,
`remember_memory`, `recall_memory`, `update_memory`, `archive_memory`, `restore_memory`, `forget_memory`,
`explain_memory`, `memory_profile`, `memory_inbox`, `review_memory`, `memory_audit`, `propose_memories`,
`capture_session`, `accept_capture`, `redact_capture`, `delete_capture`, `capture_inbox`, `starter_prompts`,
`link_status`, `validate_wiki`, `rebuild_index`, `rebuild_backlinks`, `migrate_wiki`, `backup_wiki`. Search has been
hardened: optional in-memory SQLite FTS acceleration with token-index fallback, persistent `.link-cache/` for unchanged
large wikis, precomputed search word indexes, cache-backed graph edge construction. The local web viewer at
`serve.py` got a meaningful security pass — CSP headers, browser isolation/permissions-policy, `X-Link-Local-Action`
header required for mutations, `Origin`/`Referer` checks, rate limiting on local write APIs, bounded path parsing,
hardened `405`/`HEAD`/`TRACE`/`CONNECT` handling — plus dark/light theme, fullscreen graph mode, large-graph controls
(node search, type filtering, neighborhood depth), bounded graph summaries, `/inbox`, `/memory`, `/profile`, `/audit`,
`/captures`, `/explain-memory`, `/propose`, `/ingest`, `/prompts`. CI now enforces a tool-contract check, a
runtime-duplication guard, release hygiene checks (no outbound HTTP in tracked Python/shell), MCP stdio smoke against
the built wheel, and large-wiki performance smoke (timing thresholds for search/query/graph). Schema migration framework
(`link migrate`, MCP `migrate_wiki`) is in place for future format changes.

## 3. What's reusable in Linus

Link is now the strongest candidate substrate Dan's reference stack has for the Phase 2 memory pillar. The most
directly portable pieces:

- **Memory schema with lifecycle.** `wiki/memories/` with typed memory pages (preference/decision/project/fact/note) +
  scope (user/project/global) + status (active/stale/archived) + review_status (pending/reviewed/needs_update) +
  `update_count` + `last_update_source` is exactly the shape the memory-architecture spec needs for Layer C episodic
  storage. Adopt the page schema near-verbatim.
- **`query_link` agent-facing packet.** Returns memory + ranked pages + graph neighborhood + reasons + budget report +
  follow-up actions in one call with explicit token/character counts. This is the budgeted-retrieval API shape DEC-0032
  (16K in-context cap) wants — agent-side calls into Linus's KB/memory should return packets with budget headroom and
  next-action hints, not raw chunks.
- **Memory review/audit/inbox/explain pattern.** `memory-inbox` for pending review, `memory-audit` for health/risk
  factors, `explain-memory` for provenance and recall readiness. Linus's memory architecture needs a parallel surface —
  Workers should be able to ask "what memories are pending review?" and "why does this memory exist?"
- **Conflict + duplicate detection on memory writes.** Strong duplicates refused unless explicitly allowed, contradictory
  active memories surfaced before saving, review gate on proposals. Directly portable to Linus's episodic-memory
  insert path.
- **`capture-session` + `propose-memories` + `accept-capture` workflow.** Save long session notes locally as raw
  captures, surface proposal-only memory candidates, require explicit accept, support redact/delete with confirmation,
  block ingest of secret-bearing content. Linus's session-end flow (Layer B scratchpad → Layer C episodic promotion)
  needs exactly this gate.
- **`doctor`, `validate_wiki`, release-hygiene checks.** The lint-and-ingest-gate pattern (frontmatter, type/directory
  alignment, required sections, dead links, stale backlinks, unreadable pages, secret content) is a Worker-side
  validation discipline Linus's KB and memory layers should copy.
- **MCP tool contract enforcement in CI.** Tool-contract guard + runtime-duplication guard prevent CLI/HTTP/MCP drift.
  Pattern worth lifting into Linus's eventual MCP server.

Plain-markdown-in-a-directory substrate still means Obsidian opens the wiki as a vault for free, and the schema is
human-readable. Bounded payloads (page lists, backlinks, graph summaries) are explicitly designed for agent context
budgets rather than browser display — directly aligned with Linus's Worker-call shape.

## 4. What's inspiration only

The web viewer at `serve.py` is more polished than before (CSP, dark mode, fullscreen graph, memory dashboard,
audit/inbox/explain pages) and now ships a GitHub Pages product site under `docs/`, but Linus still has Streamlit /
openclaw on the front-end track and shouldn't run a second web UI. The Homebrew tap (`gowtham0992/homebrew-link`) is a
nice operational detail but not a Linus integration vector. The per-agent install scripts (codex / claude-code / cursor
/ kiro / copilot / vscode / antigravity each get their own `integrations/<agent>/install.sh`) remain a clever
configure-someone-else's-config pattern, but Linus owns the harness-facing endpoint itself and won't register as a
third-party MCP tool in other agents' configs. The starter-prompt machinery (`link prompts`, MCP `starter_prompts`,
`/prompts`) is a nice onboarding shape — likely Linus's eventual `linus doctor` / `linus prompts` equivalent should
expose similar guidance, but the actual prompts are Link-specific.

## 5. What's incompatible or out of scope

Single-maintainer project, beta status, still no concept of multi-agent concurrent writes — `wiki/index.md` and
`_backlinks.json` are still single-writer artifacts, and the new memory lifecycle assumes one human curator + one agent
maintainer. Phase 3 parallel-Worker fan-out (DEC-0022) would need to serialize memory writes through Linus's
orchestration layer or pick a different substrate. There is still no content-hashing or claim-level provenance beyond
`[confidence: high/medium/low]` strings and `*Source: [[source-page]]*` links — the security-synthesis claim-typing
work is a layer Linus would add on top. The local web viewer is `127.0.0.1`-bound with explicit "do not expose without
adding auth" warnings; Linus's orchestration layer would replace, not extend, the HTTP surface. The atomic-write helpers
are good but the lock model is per-file not per-resource — `gather → compile → cache` parallelism (beever-atlas style)
isn't here. Python 3.10+ minimum for the MCP package.

## 6. Recommendation: **Adapt** _(was "Study")_

Verdict promoted from Study to Adapt. The 1.1.0 memory-mode pivot gives Linus's memory pillar a much closer fit than
prior assessments allowed — the schema, lifecycle, agent-facing packet shape, and review/audit/explain surfaces are all
candidates for direct adoption into the Phase 2 memory-architecture spec rather than just inspirational read-arounds.
Adapt rather than Integrate because (a) Linus's Worker memory writes must flow through orchestration-layer policy (audit
log, sandbox, cot_budget / memory_mode dispatch fields), which Link's single-writer model doesn't support out of the
box; (b) Linus's episodic store has SQLite + content hashes + git as durable substrate per DEC-0029, not pure markdown;
(c) the MCP server should be Linus's, not a third-party tool registered into Linus. Concrete next move: lift Link's
`wiki/memories/` schema, the `query_link` packet shape, and the review/inbox/audit/explain surfaces into the
memory-architecture spec; vendor the `LINK.md` schema document into a `docs/specs/memory-page-schema.md` as a starting
point; keep `link-mcp` running locally on Dan's machine while the Linus memory layer is built so the pattern stays
present in daily use. Revisit at Phase 2b consolidation.

## 7. Questions for Dan

1. **Memory schema adoption depth.** Should Linus's Layer C episodic-memory page schema be a near-verbatim port of
   Link's `wiki/memories/` YAML frontmatter (`memory_type`, `scope`, `status`, `review_status`, `update_count`,
   `last_update_source`), or do you want Linus's schema to diverge for content-hash + claim-typing reasons?
2. **`query_link` packet shape as Linus's MCP retrieval contract.** Link's bounded-budget agent-facing packet (memory +
   ranked pages + graph neighborhood + reasons + budget report + follow-up actions in one call) is a strong shape for
   Linus's eventual KB/memory MCP tools. Adopt as the canonical packet contract in Phase 2a planning, or treat as one
   candidate among others?
3. **Memory review workflow as Worker job.** Link's review-pending / inbox / audit / explain surfaces imply a periodic
   maintenance loop (an agent reviews pending memories, marks reviewed, flags conflicts). On Linus that's a Worker
   running on Qwen3 against the episodic store. Is "memory review as a long-running Worker task" a Phase 3 design
   target or later?
4. **Run `link-mcp` against Dan's local machine in the meantime?** The most concrete way to surface Link's patterns into
   Linus design decisions is to actually use it daily — `link-mcp` registered in Claude Code with a personal wiki. Worth
   doing as a Phase 1 background activity (~30 min setup), or premature?

   _Prior Q1 (KB write-layer substrate): partially superseded — DEC-0029 chose SQLite + content hashes + git for Layer
   C; Link's markdown-only substrate now informs schema, not durable storage._

   _Prior Q2 (confidence vs claim-typing): unchanged — still an open layering question, deferred to Phase 2b._

   _Prior Q3 (wiki maintenance as Worker job): folded into new Q3 above._

   _Prior Q4 (sibling-sweep verdict): closed — Group 2 sweep complete; Link's pivot to memory makes it a primary
   reference rather than one engine among eleven._
