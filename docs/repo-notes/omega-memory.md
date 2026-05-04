# omega-memory (`omega-memory/omega`)

## 1. Purpose and scope

OMEGA is a local-first, cross-model persistent-memory layer for AI coding agents, exposed primarily as an MCP server and
secondarily as a Python library. It targets exactly the gap Linus's memory-architecture spec calls Layer C
(cross-session episodic, DEC-0029): the agent forgets between sessions, re-explanations cost 10–30 minutes per restart,
and the existing "fixes" either lock you to one provider (Anthropic Memory Tool, OpenAI Memory) or push your codebase
context to someone else's server (Mem0, Zep). OMEGA's pitch is one SQLite database under `~/.omega/omega.db`, on-device
ONNX embeddings (`bge-small-en-v1.5`, 384-dim), and a single MCP server registered into whichever client config the user
runs (`omega setup --client claude-desktop|cursor|claw-code|windsurf|cline|codex`). Apache-2.0, on PyPI as
`omega-memory==1.4.9`, with a self-reported 1123 passing tests (the `tests/` tree contains 68 test files, and the README
mentions 2198+ when slow tests are included). It is one of the eight repos named in the skills synthesis Phase 1
retrieval/memory reference list.

## 2. Architecture summary

The shape is "single SQLite store + thin handler modules + MCP transport." The substrate lives under
`src/omega/sqlite_store/` (`_base.py`, `_store.py`, `_query.py`, `_search.py`, `_maintenance.py`, ~5.8k lines total)
behind a `manager.py` singleton; `bridge.py` is the public Python API (~36 functions, all delegating to the singleton).
Search is a pipeline: vector similarity via `sqlite-vec` (cosine on 384-dim embeddings), FTS5 full-text, type-weighted
scoring (decisions and lessons get 2× boost; constraints/reminders 3×), contextual re-ranking by tag/project/content,
deduplication. Memories carry a typed `event_type` (decision, lesson_learned, error_pattern, constraint, checkpoint,
session_summary, skill_template, …) with per-type Jaccard dedup thresholds in `bridge.py:DEDUP_THRESHOLDS`. Edges
auto-relate memories above similarity 0.45 to their top-3 neighbours, giving a graph traversable via `omega_traverse`.
The MCP server (`src/omega/server/mcp_server.py`) ships 25 core tools and runs in two transports: stdio (one process per
client session, default) or HTTP daemon on port 8377 (one process shared across sessions, set via `OMEGA_TRANSPORT=http`
or `omega serve --daemon`). A second tier of optional modules (coordination, router, profile, knowledge, entity, oracle)
loads only if `omega_platform.license.is_pro()` returns true — the open-core boundary. Hooks in `hooks/` integrate with
Claude Code's `~/.claude/settings.json` (SessionStart welcome briefing, UserPromptSubmit auto-capture, PostToolUse
surface-relevant-memories) and dispatch through `fast_hook.py` over a Unix socket to the daemon for sub-millisecond
fail-open semantics. A `~/.cache/omega/models/bge-small-en-v1.5-onnx/` ONNX model load takes RSS from ~31 MB to ~337 MB
on first query.

## 3. What's reusable in Linus

Five things, in priority order. **First**, the schema: a typed event-type taxonomy with per-type weights and per-type
dedup thresholds is a refinement Linus's DEC-0029 record shape
(`session_id, turn_id, parent_turn_id, role, segment, content_hash, content, trust_level, tags`) does not yet have, and
OMEGA's `_TYPE_WEIGHTS` and `DEDUP_THRESHOLDS` tables are directly cribbable as starting values. **Second**, the search
pipeline: vector + FTS5 + type-weight + rerank + dedup, all inside one SQLite file via `sqlite-vec`, validates that
Linus's v0 substrate choice (SQLite + content hashes) can carry semantic recall without a separate vector DB until Phase
4+. **Third**, the auto-relate-to-top-3 edge construction is a cheap implementation of the graph traversal Garrison's
"reference any prior state" sub-requirement implies. **Fourth**, the MCP transport split (stdio per-session vs HTTP
daemon shared) is the right design pattern for Linus's eventual orchestration backend serving multiple front-ends.
**Fifth**, `omega setup --client <name>` is a working reference for Phase 5b's "point any harness at Linus"
config-injection story.

## 4. What's inspiration only

Compared to the closest sibling in the group, **agentmemory**, OMEGA is markedly heavier and more opinionated: 1+
Pro-gated commercial modules, six-process hook tree, MCP-first stance, pre-built integrations for CrewAI and LangChain,
a CLI with 14 subcommands, an Inno Setup installer for Windows, even AES-256 encrypted profile storage with macOS
Keychain. agentmemory is closer to a minimal episodic-store library; OMEGA is closer to a product. For Linus the heavier
features — coordination/file-locking, intent broadcasting, weekly digests, knowledge-base ingestion, multi-entity
corporate memory — are out of scope at v0 and likely forever. The "1123 passing tests" headline is genuinely impressive
discipline but doesn't transfer; what transfers is the schema, the search pipeline, and the dedup constants. The Pro
gating via `omega_platform.license.is_pro()` is also a soft warning sign for vendoring: the open-core line is in the
codebase, not just in the README.

## 5. What's incompatible or out of scope

OMEGA is an MCP server first; Linus's Phase 2a target is an OpenAI-compatible HTTP endpoint with its own
`linus.memory.*` API surface, not an MCP server. Adopting OMEGA wholesale would mean bolting an MCP transport into
Linus's orchestration layer ahead of when ARCHITECTURE.md plans for it. The schema is also flatter than DEC-0029 — no
explicit `parent_turn_id` chain, no `segment` discriminator for scratchpad/answer/tool_output (Layer B in the spec), no
first-class trust-level field — so Linus cannot literally adopt `omega.db` as its episodic store; it would have to
re-implement on Linus's record shape. The "skill_template" event type and `distill_trajectory` machinery hint at a
Workers-learning-from-trajectories direction that overlaps Phase 7 skills work but with different mechanics than
DEC-0042/0037 contemplate. License gating on the interesting modules (router, coordination, knowledge, entity, profile)
means anything Linus might want from those tiers requires either a license, a clean reimplementation, or remaining on
the core tier.

## 6. Recommendation: **Study**

Read `src/omega/sqlite_store/_base.py`, `_query.py`, `_search.py` and `bridge.py:DEDUP_THRESHOLDS` in full when Phase 2a
implementation of `linus.memory.episodic` begins (per DEC-0028 ordering, this is the prerequisite for the orchestration
backend). Crib the type-weight table, dedup thresholds, and the FTS5 + sqlite-vec + rerank pipeline as v0 defaults; tune
on Dan's task suite later. Do not vendor; do not depend; do not run `omega setup` against Dan's `~/.claude/` (it would
overwrite hooks Linus will be installing in the same files). Revisit if Phase 5b adopts MCP as the front-end protocol —
at that point OMEGA becomes a candidate reference for the Linus MCP server itself rather than just for Layer C
internals.

## 7. Questions for Dan

- **Type taxonomy.** OMEGA has ~30 event types with weights from 0.05 (file_summary) to 3.0 (constraint, reminder).
  DEC-0029 leaves the type/weight question open. Do we want to seed Linus's episodic store with an OMEGA-style typed
  taxonomy from day one, or stay schema-flat and let types emerge from usage?
- **sqlite-vec vs separate vector store.** OMEGA proves you can do 384-dim cosine search inside SQLite with no separate
  service. DEC-0029 doesn't pin a vector substrate. Adopt `sqlite-vec` as the v0 vector layer (matches the "one file,
  one process" aesthetic), or stand up Qdrant in Docker for the same workload?
- **MCP timing.** OMEGA is MCP-first; Linus's ARCHITECTURE.md is OpenAI-compat-first with MCP as a Phase 3+ option (per
  cline.md and pmetal.md notes). Does OMEGA's existence — and the fact that Cursor / Claw Code / Windsurf / Cline /
  Codex all already speak MCP — pull MCP earlier in the roadmap?
- **Hook collision risk.** OMEGA writes into `~/.claude/settings.json`, `~/.claude.json`, and `~/.claude/CLAUDE.md`.
  Linus will eventually want to write into the same files for its own session hooks. Should Linus's settings model
  reserve a namespaced block from the start to avoid collision with tools like OMEGA, or treat it as a Phase 5b problem?
- **Cross-model handoff in practice.** OMEGA's "cross-model" claim reduces to "every client points its MCP config at the
  same SQLite file." That is real but modest. Is that the cross-model story Linus wants too (Linus is the one server,
  every harness points at it), or is there a more ambitious handoff — say, transcript-replay across model families —
  worth specifying for Phase 5+?
