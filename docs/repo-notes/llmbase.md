# llmbase (`Hosuke/llmbase`)

## 1. Purpose and scope

llmbase (PyPI package `llmwiki`, by Hosuke / Huang Geyang) is a Python implementation of Karpathy's "LLM Wiki" pattern:
raw material lands in `raw/`, an LLM compiles it into structured, interlinked markdown articles in `wiki/concepts/`, and
a `lint heal` loop continuously merges duplicates, fills broken links, and regenerates taxonomy. The tagline is "a
personal knowledge base that an LLM compiles, not just stores," which is nearly identical to `llmwiki`'s framing. The
shipped product is a Flask web UI + agent HTTP API + MCP server + Click CLI, all four backed by a single operations
registry; the live deployments (華藏閣, 斯文) are autonomous trilingual Buddhist / classical-Chinese knowledge bases
that learn continuously from CBETA, ctext, and Wikisource. For Linus this is a candidate reference architecture for the
Phase 2 KnowledgeBase pillar — not as code to vendor, but as a worked example of "wiki-as-memory" with an unusually
clean three-surface contract.

## 2. Architecture summary

A single Python package (`llmwiki/`, ~35 modules, MIT) plus a Vite/React frontend in `frontend/`. The pipeline is
literally `raw/ → compile → wiki/concepts/ → query/lint → wiki/`, with `叠加进化` (incremental merge) as the core
invariant: concepts are updated in place, never overwritten. Articles are trilingual markdown (EN / 中文 / 日本語),
wiki-linked via `[[target]]` and resolved through `llmwiki/resolve.py` against an `aliases.json` map (with
simplified/traditional conversion via opencc). Search is **TF-IDF over markdown** with no vector store and no embeddings
— `kb_search` scores compiled concepts; `kb_search_raw` runs the same scorer against original `raw/` for verbatim
fallback. Taxonomy is LLM-generated per-domain and persisted to `wiki/_meta/taxonomy.json`. The `llmwiki/operations.py`
registry (628 lines) is the single source of truth for every KB op as
`Operation(name, description, handler, params, writes, category)`; CLI (`cli.py`), HTTP (`agent_api.py`, `web.py`), and
MCP (`mcp_server.py`) all dispatch through `operations.dispatch()`, which acquires `worker.job_lock` for writes. A
pipeline subsystem (`llmwiki/pipeline/`, `chunk_cache.py`) provides content-hash-validated stage caching with
append-only JSONL event logs and SIGKILL-safe stale-lock recovery — runs that quota out mid-batch resume from the cache.
An autonomous worker thread (started from `wsgi.py` in production, not `llmbase web`) ingests, compiles, and heals on
hour-scale intervals. Customization is "library not framework": override module-level constants at import time and
register lifecycle hooks (`ingested`, `compiled`, `taxonomy_generated`, …) — both live deployments run pure `llmwiki`
with no fork.

## 3. What's reusable in Linus

The **operations registry pattern** (`Operation` dataclass + `register()` + `dispatch()` with a write-lock and a
`_needs_write_lock` escalation hook for ops like `kb_ask` with `promote=True`) is the cleanest "one definition, three
surfaces" implementation in the eleven-repo group and worth lifting almost verbatim into Linus's Phase 2a tool registry
— it solves the same problem the orchestration layer faces (CLI + OpenAI-compat HTTP + MCP all exposing the same tools
without drift). The `kb_search` / `kb_search_raw` two-layer recall idea — TF-IDF over a compiled concept layer with
verbatim fallback to the raw source layer — maps directly onto Phase 3's hybrid retrieval design and is a useful
counterweight to the "embed everything" default; the KnowledgeBase submodule already does Qdrant, but a TF-IDF concept
layer over markdown is cheap, debuggable, and works offline (Phase 4 data sovereignty). The `chunk_cache.py` +
`pipeline/run_stage` primitive (content-hash keyed, JSONL event log as source of truth, partial-exit semantics for LLM
quota cut-offs) is genuinely good and should inform any long-running KB-build pipeline Linus runs against the papers
corpus.

Compared to its siblings: `llmbase` shares the "LLM as compiler not storage" tagline with `llmwiki` (same author
namespace — `llmwiki` is the PyPI name here), but where `llmwiki` is closer to the Karpathy gist as a small reference,
`llmbase` is the productized, multi-tenant, multi-deployment evolution with a unified operations contract, an autonomous
worker, and a self-healing lint pipeline. Versus `link`, which mirrors Karpathy's framing more directly as a minimal
pattern, `llmbase` is the maximalist take — trilingual articles, alias resolution, emergent taxonomy, eight-category
lint with LLM-confirmed dedup. It is the most "complete product" of the engine repos and the most opinionated about
no-vector-DB at personal scale.

## 4. What's inspiration only

The trilingual EN / 中文 / 日本語 article schema and the Buddhist-canon / classical-Chinese deployments are not Linus's
domain — Dan's corpus is biochem, genomics, and CS papers in English. The `xici` (导读 guided introduction) and tone
modes (文言 📜, scholar 🎓, ELI5 👶, caveman 🦴) are charming but irrelevant to a scientific-computing workflow. The
Flask + Vite frontend is similarly out of scope; Linus has Streamlit short-term and openclaw long-term. The fact that
the package name `llmwiki` collides with this group's namesake-sibling repo (and forced a v0.8.0 rename from `tools` to
`llmwiki`) is itself a useful warning if Linus ever publishes a KB package — pick a name with no neighbors.

## 5. What's incompatible or out of scope

OpenAI-only LLM client (`llmwiki/llm.py`) routed through `openai>=1.30.0`. Works with any OpenAI-compatible endpoint
including Ollama, so the boundary is soft, but there is no native MLX / pmetal path. The autonomous worker assumes a
long-lived gunicorn deployment and a ChunkCache-friendly disk; both fit Linus but require an explicit decision about
whether Linus's KB is a long-running service or a query-time process. No claim-typing or content-hashing in the
security-synthesis sense — provenance metadata is per-source, not per-claim, so the security synthesis's interop story
would need to be added on top, not consumed from llmbase.

## 6. Recommendation: **Study**

Read `llmwiki/operations.py`, `llmwiki/pipeline/`, `llmwiki/chunk_cache.py`, and `llmwiki/search.py` as reference for
Phase 2 KB design and the Phase 2a tool registry; lift the operations-registry pattern (it is the most useful single
artifact in the eleven-repo group). Do not vendor the package or build on top of `llmwiki` — the trilingual /
classical-Chinese baggage and OpenAI-only LLM client make it the wrong base for an English-scientific corpus on Apple
Silicon. Revisit if Phase 3 hybrid retrieval converges on TF-IDF over a compiled concept layer; the design is well
thought out and the live deployments are evidence it works at scale.

## 7. Questions for Dan

1. **Operations-registry adoption.** The `Operation(name, handler, params, writes, category)` + `dispatch()` pattern is
   a near-drop-in answer to Phase 2a's "one tool, three surfaces (CLI / OpenAI-compat HTTP / MCP)" problem. Adopt it as
   the Linus tool-registry shape, or design a different abstraction that better fits the Maestro/Worker delegation
   model? _Partially resolved (DEC-0018, DEC-0045, see [answered-questions.md](../questions/answered-questions.md)): MCP
   adopted as extensibility substrate; fastmcp's decorator API is the in-house Linus server pattern; the specific
   operations-registry shape for Phase 2a remains to be decided._
2. **Two-layer recall vs Qdrant.** llmbase makes a defensible no-vector-DB argument at personal scale (TF-IDF over
   compiled concepts + verbatim raw fallback). The KnowledgeBase submodule already commits to Qdrant. Is Phase 3 hybrid
   retrieval `Qdrant + BM25/TF-IDF + compiled concept layer`, or stay vector-first and treat llmbase's two-layer pattern
   as a curiosity?
3. **Compiled concept layer over papers.** llmbase's central bet is that a LLM-maintained markdown wiki over your corpus
   is more useful than raw chunks. For Dan's papers/notes/threads — do you want a compiled concept layer on top of the
   existing KnowledgeBase chunks, or is the chunk-and-retrieve baseline sufficient for Phase 2?
4. **Sibling differentiation.** `llmbase` and `llmwiki` (the namesake sibling) share an author namespace and framing. Is
   there value in studying both, or should one be designated canonical and the other ignored?
5. **Autonomous worker model.** llmbase's worker thread (CBETA every 6h, compile every 1h, health every 24h) is the
   simplest "always-on KB" pattern in the group. Is an always-on background ingest/compile/heal loop in scope for Linus,
   or does ingestion stay user-initiated through Phase 4?
