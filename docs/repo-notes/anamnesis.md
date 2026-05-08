# anamnesis (`gayawellness/anamnesis`)

## 1. Purpose and scope

Anamnesis bills itself as a "4D Strategic Memory Engine" for AI agents — a server that stores not just _what_ happened
but _why_ a decision was made, _under what conditions_ it should change, and _how important_ it is relative to
everything else. It maps onto Garrison's Layer C (cross-session episodic) but takes an opinionated position on the
strategic-weighting and retrieval shape that none of the lighter siblings in this group attempt. The pitch is: a session
that opens with `reflect` against a bank gets ranked operating directives back, not a flat dump. The substrate to
deliver this is heavy: a FastAPI server (`anamnesis/api/`) backed by PostgreSQL with pgvector and pg_trgm, shipped as a
Docker Compose stack on port 8400 plus a 5433 PostgreSQL sidecar. v0.2.0, MIT, Beta. For Linus this is the most
architecturally ambitious entry in the eight-repo memory survey and the one whose substrate is most opposed to
DEC-0029's SQLite + content-hash + git commitment.

## 2. Architecture summary

A single Python package (`anamnesis/`) with a flat module layout: `api/` (FastAPI app, routes, optional bearer-token
auth), `operations/` (the five primitives — `retain`, `recall`, `reflect`, `decay_check`, `reweight`, plus `prune`),
`mcp/server.py` (MCP wrapper exposing the operations to Claude Code), `cli/` (boot prompt generators, export/import,
scoring diagnostics), `sdk/` (a thin Python client), and `embedder.py` / `llm.py` providing pluggable backends — local
sentence-transformers by default (`all-MiniLM-L6-v2`), Voyage AI optional, Anthropic for `reflect` synthesis. Storage is
six PostgreSQL tables: `memory_banks`, `memories`, `entities`, `entity_edges`, `memory_entities`, `memory_accesses`. The
"4D" in `recall` is concrete in `operations/recall.py`: four parallel async retrieval channels — semantic (pgvector
cosine over the embedding), full-text (Postgres tsvector / pg_trgm), temporal (recency + access frequency), and
relational (entity-graph traversal over LLM-extracted subject-predicate-object triples) — fused with Reciprocal Rank
Fusion (`RRF_K = 60`), then a strategic-weight boost. The "strategic" dimension is the core idea, calibrated by an
authority hierarchy: `explicit` memories cap at weight 8.0 initial / 10.0 reweighted, `system` at 2.0 / 6.0, `inferred`
(AI-derived) at 1.0 / 4.0. A reweight pass periodically recomputes weights using a temporal decay factor
(`0.5 + 0.5 * 1/(1 + days/30)`) and connectivity bonus, so frequently-recalled, well-connected memories climb while
stale ones fade. Banks carry a `mission`, ordered `directives`, tunable `weight_factors` (default 0.30 / 0.20 / 0.20 /
0.30 across the four dimensions), and a `default_decay_days`. Decay conditions are a small DSL: `after:30d`,
`when:superseded`, `when:unaccessed:60d`, `never`.

## 3. What's reusable in Linus

The conceptual layer is the genuine contribution and is reusable as design vocabulary even if the substrate isn't. The
notion of an explicit _strategic envelope_ (`reasoning`, `authority`, `confidence`, `decay_condition`, `supersedes`,
`depends_on`) wrapped around raw `content` is exactly the metadata DEC-0029's SQLite episodic record could carry — and
the `supersedes` / `depends_on` graph is a clean v0 answer to "how does Layer C version itself" that DEC-0039's
leaf+summary roll-up schema does not directly address. `reflect` as an operation distinct from `recall` —
synthesis-into-directives versus raw retrieval — is a useful split that maps to Layer C's "what should I focus on right
now?" query class. The authority cap idea (AI-derived memories must earn weight via reweight cycles before they can
outrank user-stated facts) is a disciplined answer to the well-known failure mode of Worker-generated noise polluting
episodic store; worth porting as a column on the SQLite schema regardless of substrate. The `generate-boot-prompt` CLI
(produces a ready-to-paste CLAUDE.md block instructing Claude Code to call `reflect` on session open) is a directly
applicable Linus pattern — dispatch-layer prefix loading per DEC-0032 plus a "boot brief" for the human.

## 4. What's inspiration only

Compare to the lighter siblings in this group: `agentmemory` and `engram` lean on SQLite or single-file stores;
`prompt-vault` and `remember` go even lighter (markdown / JSON). Anamnesis sits at the opposite end of the spectrum —
Postgres + pgvector + pg_trgm + asyncpg + FastAPI + a Docker Compose orchestrator + an MCP server + a Python SDK + a
CLI. That is more moving parts than DEC-0029's "single-file embedded DB" target by roughly an order of magnitude. The 4D
parallel-retrieval-with-RRF pattern is the most interesting algorithmic idea in the eight repos and is reusable as a v1
retrieval design over Linus's SQLite substrate (FAISS or sqlite-vec for semantic, FTS5 for fulltext, a recency index for
temporal, a small in-process entity table for relational) — a 4D recall that doesn't require Postgres. The entity-graph
extraction at `retain` time depends on an LLM call (Anthropic by default); for Linus that should route through the local
Worker pool, not a hosted API.

## 5. What's incompatible or out of scope

The Docker Compose substrate is a near-disqualifier on Linus's own terms. CLAUDE.md's "Hardware Constraints" and "Tool
Use Policy" sections are explicit: Docker on macOS runs in a VM and does not pass through Metal or ANE; Docker is for
stateless services only. Anamnesis's Postgres container is _stateful_ — exactly what the constraint targets — and its
server container needs no Metal but adds a long-running VM-bound process. The README's manual-mac fallback
(`brew install postgresql@17` + `createdb` + `CREATE EXTENSION vector`) avoids the VM but replaces it with a
system-level Postgres install Linus has not committed to and that DEC-0029 explicitly chose against. The strategic
weight system is also calibrated for human-curated banks where `explicit` memories from a planner dominate; Linus's
Worker fan-out is the opposite shape (mostly `inferred`-authority writes from agents) and would need re-tuning of caps
and reweight ceilings to avoid collapsing into a near-uniform low-weight pile. The `reflect` operation requires either
an Anthropic API key or it degrades to "raw ranked memories" — the synthesis-into-directives behaviour, the headline
feature, is not a local-first capability out of the box.

## 6. Recommendation: **Study**

The substrate is wrong for Linus and porting the server wholesale would relitigate DEC-0029. But the design ideas —
explicit strategic envelope, authority-capped weights with reweight earn-up, `reflect` as a distinct synthesis
primitive, 4D parallel retrieval with RRF, the boot-prompt CLI pattern, the `supersedes` / `depends_on` graph as v0
versioning — are the strongest in this group and worth lifting into the DEC-0029 SQLite schema and the dispatch-layer
prefix loader. Read `operations/recall.py`, `operations/reflect.py`, `SCHEMA.md`, and `cli/` once; do not run the Docker
stack except to sanity-check behaviour against a small seeded bank.

## 7. Questions for Dan

1. **Strategic envelope columns on the DEC-0029 schema.** Anamnesis's `reasoning`, `authority`, `confidence`,
   `decay_condition`, `supersedes`, `depends_on` are mostly orthogonal to DEC-0030's two-segment record. Worth adding
   any of them to the `~/.linus/episodic.db` schema before Phase 2a starts writing migrations, or defer until use cases
   demand them?
2. **4D recall over SQLite.** The RRF-fused four-channel retrieval is implementable on sqlite-vec + FTS5 + a recency
   index + a small entity table without leaving SQLite. Is this a Phase 2 v1 target, a Phase 3 enhancement, or out of
   scope until a real retrieval-quality complaint surfaces?
3. **Authority caps for Worker-generated memories.** Linus's Worker fan-out will write mostly `inferred`-authority
   records. Anamnesis caps these at 1.0 (initial) / 4.0 (reweighted) to prevent agent noise drowning user-stated facts.
   Is that discipline the right default for Linus's episodic store, or does it need different calibration when the
   writes are mostly automated?
4. **`reflect` as a Linus primitive.** Anamnesis distinguishes `recall` (retrieval) from `reflect` (LLM-synthesised
   directives over mission + directives + top memories). DEC-0031's `memory_mode` router primitive is closer to
   `recall`. Worth adding a separate `reflect`-style operation for boot-time strategic briefing, or is the
   dispatch-layer prefix loader sufficient?
5. **Single sibling worth comparing in depth.** This group has eight implementations. Anamnesis sits at the heaviest
   substrate end; `agentmemory` is plausibly at the SQLite-native end most aligned with DEC-0029. Want me to flag this
   comparison explicitly in the `agentmemory` note when it's written, or do the eight notes plus a synthesis pass at the
   end?
