# agentmemory (`rohitg00/agentmemory`)

## 1. Purpose and scope

agentmemory is a TypeScript/Node memory server (`@agentmemory/agentmemory` on npm, Apache-2.0, v0.9.4) that implements
the design Rohit Ghumare published as a viral GitHub gist (1050 stars / 150 forks) extending Karpathy's "LLM Wiki"
pattern. It runs as a long-lived background process speaking three protocols at once — 51 MCP tools, 107 REST endpoints
on port 3111, and a real-time WebSocket viewer on 3113 — into which any harness that speaks MCP or HTTP (Claude Code,
Cursor, Cline, OpenCode, Codex, Goose, Aider, Hermes) writes observations and from which they read context. The README
leads with concrete numbers — 95.2% R@5 on LongMemEval-S, ~$10/yr token cost — and unlike most "implementation of a
gist" projects the substance is actually here: 118 source files, ~21.8k LoC, 800+ tests, 57 functions in
`src/functions/`, 13 hook scripts, the works. For Linus this is the most directly relevant repo in the Layer-C
cross-session-episodic group; almost everything in `docs/specs/memory-architecture.md` (DEC-0028 … DEC-0043) has a
corresponding implementation here, although the storage substrate (iii-engine) is not the SQLite + git substrate Dan
committed to in DEC-0029.

## 2. Architecture summary

The unusual choice is the runtime. agentmemory is built on `iii-engine` — a separate Rust binary speaking WebSocket on
port 49134 that supplies three primitives: HTTP triggers, KV state (file-backed SQLite at `./data/state_store.db`), and
event streams. The repo therefore has no Express, no Postgres, no Redis: every function is registered with
`sdk.registerFunction("mem::name", …)` and invoked via `sdk.trigger(...)`, hooks are standalone Node scripts that POST
to the REST API, and the viewer reads off iii's WebSocket. This is mostly invisible to Linus (the SQLite still backs
everything) but it does mean adopting agentmemory as a library means adopting iii-engine as a runtime dependency. Memory
flow per the README: PostToolUse hook fires → SHA-256 dedup in a 5-minute window → privacy filter strips API keys /
`<private>` tags → raw observation stored → optional LLM compress to facts+concepts+narrative → embedding via one of six
providers (`all-MiniLM-L6-v2` local default through `@xenova/transformers`) → BM25 + vector index. Stop hook runs
session summarization, optional knowledge-graph extraction, and "slot reflection." SessionStart loads the project
profile and runs hybrid retrieval to inject ~2k tokens of context. The four-tier consolidation (Working / Episodic /
Semantic / Procedural) lives in `src/functions/consolidate.ts` and uses an XML-prompted LLM call with a 1–10 strength
score. `auto-forget.ts` implements TTL expiry, contradiction detection (cosine ≥ 0.9), and low-value eviction with full
audit trail. Triple-stream retrieval (`src/state/hybrid-search.ts`) fuses BM25 + vector + knowledge-graph traversal via
RRF (k=60) with session diversification capped at 3 results per session.

## 3. What's reusable in Linus

The single most reusable element is the **hook taxonomy**: the 13 scripts in `src/hooks/` (SessionStart,
UserPromptSubmit, PreToolUse, PostToolUse, PostToolUseFailure, PreCompact, SubagentStart/Stop, Stop, SessionEnd,
TaskCompleted, Notification, sdk-guard) are a worked example of exactly which Claude Code lifecycle events Layer C needs
to subscribe to and what each one should write. Phase 2 episodic-memory layer (DEC-0029) can borrow this mapping
verbatim. The **MCP tool surface** — `memory_recall`, `memory_save`, `memory_smart_search`, `memory_governance_delete`,
`memory_snapshot_create`, `memory_lease`, `memory_signal_send`, `memory_checkpoint`, `memory_verify` — is an unusually
complete catalog and worth using as a checklist when Linus designs its own MCP surface in Phase 3. The **hybrid-search
RRF fusion code** in `src/state/hybrid-search.ts` is small, well-factored, and directly portable to the Linus Python
stack. The **lease + signal + checkpoint primitives** address Garrison's parallel-Worker write coordination problem
(Phase 3) — `memory_lease` is exactly the exclusive-action mechanism that group consensus has been hand-waving about.
The **citation provenance** (`memory_verify`) and **git snapshots** (`memory_snapshot_create`) line up directly with
Garrison's integrity sub-requirement and DEC-0029's git-as-substrate commitment — agentmemory snapshots the iii KV
scopes; Linus would snapshot the SQLite file. Among the eight sibling repos, agentmemory and **memex** are the only two
that ship a complete real-time viewer; against **anamnesis** and **engram** it is by far the more polished and
benchmarked package, and against **mem0/Letta** (named in its own competitor table) it's the only one with no external
DB requirement.

## 4. What's inspiration only

The iii-engine substrate is the line — Linus committed in DEC-0029 to plain SQLite + content hashes + git, and adopting
iii-engine would mean adding a Rust runtime daemon for a problem Dan has already decided to solve with boring SQLite.
The MCP server architecture (51 tools, multi-transport) is a model to imitate, not code to import. The viewer on port
3113 (single-page HTML, WebSocket stream, knowledge-graph visualization) is a useful reference for what a Phase 5 Linus
inspector might look like, but is bound to the iii streams runtime. The project-profile-injection-on-SessionStart
pattern (1–2k tokens) is the right shape for Linus but should be re-implemented against Linus's prompt-assembly path.

## 5. What's incompatible or out of scope

The iii-engine dependency is the showstopper for direct integration. iii is a young Rust binary distributed via a
shell-installer (`curl … | sh`) or Docker; it is not on Homebrew, not on crates.io, not in any Apple-Silicon-tested
binary channel Linus would otherwise touch. Adopting it would invert Linus's stack — iii becomes the orchestration
runtime and Linus becomes one of its tenants. Node 20+ is required, which is fine but adds a third runtime alongside
Python and Rust. The default LLM provider is **no-op** (no compression unless an API key or the opt-in
Claude-subscription fallback is enabled) — the headline R@5 number is in BM25-plus-vector territory, not LLM-compressed
territory, which is worth knowing before quoting it. The "Lamborghini" `DESIGN.md` in the repo root is a UI design
system for the marketing site (`agent-memory.dev`) and unrelated to the engine; do not be misled.

## 6. Recommendation: **Study**

Read it carefully and steal patterns; do not vendor it. Specifically: (a) port the hook taxonomy and per-hook write
contract into the Phase 2 episodic-memory layer; (b) use the 51-tool MCP catalog as a coverage checklist when designing
Linus's tool surface in Phase 3; (c) lift the RRF triple-stream search code from `src/state/hybrid-search.ts` to Python
in Phase 2 retrieval; (d) borrow the lease/signal/checkpoint vocabulary for parallel-Worker coordination in Phase 3. Do
not adopt iii-engine; do not run a parallel Node daemon for memory; honor DEC-0029. Revisit the "adopt the package as a
black-box MCP server" option only if Phase 2's home-grown layer proves more painful than expected, and then accept that
you are running iii-engine.

## 7. Questions for Dan

- **Hook taxonomy adoption.** The 13-hook lifecycle catalog (SessionStart through TaskCompleted) maps cleanly onto
  Garrison's four sub-requirements. Want a follow-up doc that ports this to a Linus-native list as part of the Phase 2
  episodic-memory spec, or keep that scoped to DEC-0029 work?
- **MCP surface scope.** agentmemory exposes 51 memory tools; mem0 exposes ~5; Letta exposes ~12. Where on that spectrum
  should Linus's Layer-C MCP surface land in Phase 3 — minimal-and-composable, or comprehensive-and-curated?
- **Lease / signal / checkpoint primitives.** These are real answers to Phase 3 parallel-Worker write coordination.
  Worth promoting from "implementation detail" to a named DEC alongside DEC-0029, or premature to formalize before the
  v0 substrate ships?
- **iii-engine evaluation.** It's a real piece of engineering and not crazy as a Worker-orchestration runtime in its own
  right. Worth a 30-minute look before fully closing the door, or are you firm that Linus's runtime is Python
  orchestration over SQLite and iii is out of scope full stop?
- **Headline-benchmark interpretation.** The 95.2% R@5 LongMemEval-S number is with embeddings on but LLM compression
  off (the no-op default). Should Linus replicate LongMemEval-S as part of the Phase 2 episodic-memory acceptance
  criteria, and if so against the same `all-MiniLM-L6-v2` baseline so numbers are comparable across group repos?
