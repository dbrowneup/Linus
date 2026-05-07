# atomic-knowledge (`Nimo1987/atomic-knowledge`)

## 1. Purpose and scope

Atomic Knowledge bills itself as a "platform-neutral protocol for building agent-maintained work memory in markdown." It
is the most explicitly **protocol-first** of the seven LLM-Wiki sibling repos: the deliverable is a portable kit
(schemas, an `AGENT.md` operating protocol, an `init-kb.sh` bootstrap, and a small Python runtime) rather than an
end-to-end engine. The user-facing entry point stays an ordinary chat with whatever agent the user already runs; Atomic
Knowledge contributes a maintained markdown layer that survives session resets and a strict retrieval order the agent is
expected to follow. Versioned at `v0.2.0`, MIT licensed, inspired directly by Karpathy's LLM Wiki gist plus a Vannevar
Bush nod.

## 2. Content overview

The repository ships a knowledge model in `schemas/` covering seven page types — `concept`, `entity`, `project`,
`procedure`, `insight`, `candidate`, and `lint-report`. The `knowledge-base-template/` and `example-kb/` directories
materialize the layout the agent is expected to maintain: `raw/sources/` (immutable captures), `wiki/active.md`,
`wiki/recent.md`, `wiki/index.md`, `wiki/log.md`, then the formal page directories, with `meta/candidates/` as a
provisional buffer and `meta/lint-status.json` for freshness tracking. The protocol itself lives in the 19 KB `AGENT.md`
at the repo root, rendered with a real path during bootstrap and dropped into whichever instruction surface the host
agent supports. Bash scripts (`scripts/init-kb.sh`, `scripts/check-kb.sh`) handle initialization and read-only health
checks. An optional Python `runtime/service.py` exposes four bounded actions — `init_kb`, `check_kb`, `get_context`,
`validate_kb` — and an `adapters/mcp/` package wraps them as MCP tools so tool-calling agents can invoke them without
learning a CLI. Acceptance scenarios for "is the host agent actually following the protocol" live in `evals/` as four
numbered markdown scripts. Documentation in `docs/` is unusually thick for a repo this size: separate files for
`RUNTIME_BOUNDARY`, `CHAT_NATIVE_JOURNEYS`, `CANDIDATE_LIFECYCLE`, `LINT_WORKFLOW`, `KNOWLEDGE_CONSULTATION`, and
`MCP_TOOL_CONTRACTS`, each defining one slice of the autonomy and maintenance contract.

## 3. What's reusable in Linus

The frontmatter schemas — particularly `procedure.md` and `insight.md` with their `search_anchors` and `key_entities`
retrieval-hint fields — are directly liftable as a starting shape for the Phase 2 KnowledgeBase v1 page types. Compared
to the sibling **llm-research-wiki** (Paulo's schema-driven take, also Karpathy-direct), Atomic Knowledge factors
`procedure` out as a first-class type rather than folding it under method/concept. For Dan's wet-lab/biochem corpus this
is a real win: protocols and SOPs are categorically different from definitions, and a top-level `wiki/procedures/`
directory with explicit `Triggers`, `Steps`, and `Guardrails` sections matches how protocols actually get reused. The
retrieval order baked into `AGENT.md`
(`active -> recent -> index -> project -> procedure -> insight -> concept/entity -> candidate`) is a ready-to-adopt
routing policy for Linus's KB tools. The `get_context` runtime path in `runtime/service.py` is also worth borrowing
wholesale: it walks the entry files, then enumerates each formal area and emits per-file `search_anchors`/`key_entities`
hint payloads — a clean, embedding-free way to give a small worker model a structured "what to read first" answer
without forcing a vector store.

## 4. What's inspiration only

Compared to **AgenticResearchWiki** (also agent-native) and **agentic-wiki-builder** (workflow scaffolding with a DuckDB
linker and branch-per-session), Atomic Knowledge takes the opposite stance on tooling: deliberately _no_ database, _no_
vector index, _no_ background workers — the agent does maintenance during normal sessions by reading timestamps and
writing files back. That austerity is the inspiration, not the implementation. Linus's KB already has a Qdrant pillar
and a knowledge graph; it is not going to throw those away to be platform-neutral. The MCP adapter and the
`BOOTSTRAP_PROMPT.md` "paste this into any agent" pattern are also inspiration-only — Linus owns its own front-ends and
tool registry, so the cross-platform portability that justifies a paste-prompt bootstrap does not apply. The
candidate-lifecycle state machine (`open -> promoted | merged | dropped`, with a 7-day review and 14-day stale
threshold) is a documented prior-art reference for the Phase 3 "human-in-the-loop curation" question rather than
something to copy verbatim.

## 5. What's incompatible or out of scope

The autonomy boundary is conservative by design: the agent suggests writes, asks before deletes, and treats maintenance
as a writeback workflow. Linus's roadmap eventually wants more autonomy than that for trusted operations, so the
protocol's defaults will need loosening if adopted directly. The protocol also assumes a single human-curated KB with a
chat agent doing one ingest at a time; Linus's Phase 3 multi-agent fan-out (parallel workers writing back
simultaneously) breaks the implicit single-writer model — there is no merge or conflict strategy in `LINT_WORKFLOW.md`
because none was needed. Finally, the runtime is intentionally a "mechanical execution layer" that "does not interpret
user intent" — useful for cross-platform safety but the wrong stance for Linus's own orchestration layer, which _is_
allowed to interpret intent for Dan.

## 6. Recommendation: **Study**

Read the schemas under `schemas/` and the retrieval order in `AGENT.md` as a concrete reference when designing the Phase
2 KnowledgeBase v1 page model. Lift the `procedure` page type and the `search_anchors`/`key_entities` frontmatter idea;
lift the entry-page-first read order as a default tool-routing policy; consider porting the `get_context` walker as a
starting Linus KB tool. Do not adopt the platform-neutral framing or the MCP adapter wholesale — Linus owns its surface
— and do not adopt the conservative autonomy defaults without revisiting them against SAFETY.md's tier model. Worth a
focused half-day read with the example KB open beside the schemas.

## 7. Questions for Dan

- **Procedure as a first-class page type.** Atomic Knowledge promotes `procedure` to peer status with `concept` and
  `insight`. For your wet-lab/SOP corpus this seems obviously right, but it adds a page type that llm-research-wiki and
  AgenticResearchWiki do not have. Do you want the Phase 2 KB v1 schema to include `procedure` from day one, or start
  with concept/entity/insight and add procedure once it has corpus to back it?
- **Retrieval-hint frontmatter (`search_anchors`, `key_entities`).** These are an embedding-free way to bias a small
  worker's read set. Worth standardizing across Linus KB pages as required frontmatter, or leave them optional like the
  upstream protocol does?
- **Differentiator strength vs llm-research-wiki.** I'm calling "platform-neutral protocol stance" plus
  "procedures-as-first-class" plus "the MCP-wrapped `get_context` runtime" as the three differentiators vs the other six
  LLM-Wiki siblings. With the protocol-first framing being the loudest. Does that match what you noticed reading them,
  or is there a fourth angle (the candidate-lifecycle state machine? the `evals/` acceptance scripts?) that landed
  harder for you?
- **Single-writer assumption.** The protocol presumes one agent maintaining one KB at a time. Phase 3 wants parallel
  workers. Is the right pattern per-worker scratch KBs that get merged into a canonical KB by Maestro, or one shared KB
  with file-level locking — and either way, is that a problem worth solving in Phase 2 or deferring to Phase 3?

  _Resolved (DEC-0022, see [answered-questions.md](../questions/answered-questions.md)): Serialized writes through a
  coordinator with write-time contradiction surfacing; Phase 3 spec target._
- **Autonomy-tier alignment.** AGENT.md says "ask before deletes, archives, bulk cleanup, large restructures." SAFETY.md
  is going to want a more graduated tier model. Do we want to write the mapping (Atomic Knowledge's prompt rules →
  Linus's autonomy tiers) as an explicit ADR, or treat the AK defaults as Tier-0 and graduate from there in Phase 7?
