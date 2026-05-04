# vectorless (`vectorlessflow/vectorless`)

## 1. Purpose and scope

Vectorless is a "Document Understanding Engine" that deliberately rejects the embedding-and-similarity-search foundation
of mainstream RAG. Its tagline — _"Knowing by reasoning, not vectors"_ — and its principles file
(`reason, don't vector / model fails, we fail / no thought, no answer`) make the philosophical commitment explicit. The
product is a 17-crate Rust workspace plus a pure-Python SDK (`pip install vectorless`) exposing a small surface:
`engine.compile(path)` to ingest a document and `engine.ask(question, doc_ids=...)` to answer with attributed evidence.
Compile is heavy and runs in Rust; ask is an LLM-driven agent loop that runs in Python and burns tokens against an
external model (litellm-routed: OpenAI, Anthropic, Ollama, anything OpenAI-compat). For Linus this is directly relevant
to Phase 1f evaluation, the Phase 2 KB tool registry (DEC-0029), and the Phase 3 hybrid-retrieval question — it is the
loudest counter-position to the BM25+vector+rerank stack that `qmd` represents, and a working implementation of the
"compile, don't retrieve" thesis from the LLM-Wiki synthesis.

## 2. Architecture summary

Two tiers separated by a clean boundary. The Rust **compile** pipeline (`crates/vectorless-compiler`) takes a document
through 15 ordered passes — frontend (`parse` → `build`), transform (`split` → `enrich`), analysis (`enhance` →
`validate`), backend (`navigation` → `concept` → `chain` → `overlap` → `route` → `reasoning` → `score` → `optimize` →
`verify`) — and produces a persisted `Document` with a navigable `Tree`, a `NavigationIndex`, a `ReasoningIndex`, a
per-node concept set, and a cross-document relationship graph (`vectorless-graph`). The output is essentially a
hierarchical, queryable representation of the document's _structure_, not a flat array of chunks with embeddings. There
are no vectors anywhere in the pipeline; `vectorless-scoring` does BM25 and keyword extraction, used only for reranking
inside the agent. The Python **ask** layer (`vectorless/ask/`) is the reasoning engine: `dispatcher.py` routes through
`QueryAnalyzer` (intent + complexity classification via the LLM), then `Orchestrator` analyzes the DocCards, picks
documents, and spawns one `Worker` per document up to 5 concurrent. Each Worker runs an LLM-in-the-loop navigation agent
on the tree using a **shell-like command vocabulary** — `ls`, `cd`, `cat`, `find`, `grep`, `head`, `wc`, `pwd`, `toc`,
`stats`, `siblings`, `ancestors`, `chain`, `summarize`, `compare`, `find_section`, `done` — defined in
`vectorless/ask/worker/commands.py` (~30 handlers). The Worker is given an initial `ls` of the root, optionally a
keyword-hint plan, then a 15-round loop of `pick command → execute → observe → repeat` until it emits `done` with
collected evidence. The Orchestrator runs up to 3 supervisor iterations with replanning if `evaluate` deems evidence
insufficient, then a `verify` pipeline (up to 2 iterations) checks the answer, and finally `rerank/synthesize` fuses
worker outputs into the final `Output(answer, evidence, confidence, trace_steps, metrics)`. Python deps: `pydantic`,
`litellm`, `instructor`, `click`. Rust extension built with maturin/PyO3.

## 3. What's reusable in Linus

The architectural idea — _treat a document tree as a filesystem and let the LLM navigate it with shell commands_ — is
the most directly transferable thing here, and it is concrete enough to lift into Linus's KB tool registry without
adopting Vectorless wholesale. Crossing 3 (KB as graph + vector store) currently presumes a vector substrate; Vectorless
suggests an additional, parallel KB tool surface where the model uses `kb_ls`, `kb_cd`, `kb_cat`, `kb_grep`,
`kb_concepts` against the KnowledgeBase's section graph. That is buildable as a Phase 2/3 MCP server on top of existing
KnowledgeBase metadata with no new dependencies. The 15-pass compile pipeline (`navigation` / `reasoning` / `chain` /
`concept` indices) is also a useful blueprint for what an "indexed-for-reasoning" KB chunk looks like — it formalizes
the engram-style "compile once, reason many times" pattern. The Python SDK is small enough (~500 lines for `engine.py`)
to be vendored and pointed at a local Ollama endpoint via litellm if Dan wants to evaluate end-to-end on the Dan-task
suite.

Compared to its **G6 sibling `qmd`** (BM25+dense+rerank, classical RAG done well), Vectorless makes the exact opposite
bet: zero embeddings, all retrieval is reasoning. Compared to **`engram`** and the G2/G3 LLM-Wiki engines (compile
documents into structured, model-readable artifacts up front), it is philosophically aligned but operationally different
— Vectorless compiles into a navigable tree the agent walks at query time, where engram-style systems compile into a
flat document the model reads directly. It is the most aggressive "compile-don't-retrieve" implementation in the repo
collection.

## 4. What's inspiration only

The Rust compile pipeline itself is impressive and probably overkill for Linus to import; KnowledgeBase already has its
own ingestion and would not benefit from a parallel Rust workspace. The verification + replan loops are well designed
but add latency cost on top of an already token-heavy pattern. The Docusaurus docs site, the langchain / llamaindex
adapter packages, and the CLI are product polish that Linus does not need.

## 5. What's incompatible or out of scope

The cost model is the hard constraint. A single `ask()` call runs query analysis (1 LLM call), orchestrator analysis (1
call), per-worker keyword hinting and planning (1–2 calls), then up to 15 navigation rounds per worker × up to 5
concurrent workers × up to 3 supervisor iterations + verification + rerank synthesis. That is plausibly 20–80 LLM calls
per query against a non-trivial corpus. Against a hosted frontier model that's expensive; against a local 7–14B worker
model on M1 Max that's slow — minutes per query is realistic. Vector RAG returns a top-k in tens of milliseconds with
one final synthesis call. Vectorless trades two-to-three orders of magnitude of latency and token cost for higher
reasoning quality on hard, multi-hop questions. That tradeoff has to be evaluated, not assumed. Vectorless also assumes
model competence; there are no heuristic fallbacks, by design — a small worker model that hallucinates `cd nonexistent`
will fail the whole query rather than degrade gracefully. This makes it a poor fit for the smallest local workers
(Phi-3, Mistral-7B-Q4) without prompt-variant tuning of the kind Cline has for `xs` models.

## 6. Recommendation: **Study**

Build a smoke-test harness in `experiments/vectorless-smoke/`: install from PyPI, point `litellm` at
`ollama/qwen2.5-coder:14b`, compile 3–5 papers from the context folder, run the Dan-task suite questions, log token
counts and wall-clock against the same questions answered by KnowledgeBase's existing retrieval. The result of that
bake-off informs whether Vectorless's pattern (or just its shell-command tool surface) belongs in Linus, or whether the
cost makes it a hosted-Claude-only luxury. Do not adopt the Rust crate workspace; if the philosophy wins, port the
smaller idea (navigable-tree tools as MCP) into Linus's own KB tool registry.

## 7. Questions for Dan

- **Bake-off scope.** Should the Vectorless evaluation use a hosted model (gpt-4o-mini, Claude Haiku) for an honest
  quality ceiling, a local Ollama worker for an honest Linus-on-MacBook ceiling, or both? The two answers could be very
  different and shape whether this pattern is "worker territory" at all.
- **Crossing 3 implications.** Vectorless's existence is an argument that a Linus KB built _purely_ on graph +
  shell-command tools, with no vectors, might be viable. Crossing 3 currently assumes vectors. Do we want to defend that
  assumption with a measurement, or is the hybrid path (vectors for recall, navigation for precision) already settled?
- **Tool surface as MCP.** The shell-command vocabulary (`ls`/`cd`/`cat`/`grep`/`concepts`/`chain`) is the most concrete
  reusable artifact. Is this a Phase 2 KB-tool-registry candidate, or does it wait for Phase 3 hybrid retrieval design?
- **Failure-mode tolerance.** Vectorless's "model fails, we fail" stance is the opposite of Linus's preference for
  graceful degradation in worker pipelines. If we adopt the navigation pattern, do we want to keep the strict stance or
  add KnowledgeBase-style fallbacks (BM25 backstop when the agent gives up)?
- **engram comparison.** Is there a planned engram experiment where we can run head-to-head with Vectorless on the same
  documents and same questions, so the "compile-don't-retrieve" thesis gets a real measurement instead of a vibe?
