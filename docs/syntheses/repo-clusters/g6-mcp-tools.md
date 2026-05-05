# Group 6 Synthesis — MCP Servers & Code/Document Context Tools

**Date:** 2026-05-04 **Author:** Claude Sonnet 4.6 (Worker, commissioned by Dan Browne) **Trigger:** G6 fan-out
synthesis pass; six repos evaluated: fastmcp, ontomics, codesight, qmd, vectorless, WeKnora.

---

## What this document is

Group 6 is the highest-density Integrate cluster of the fan-out: three of six repos earn Integrate verdicts (fastmcp,
ontomics, codesight), and all three connect directly to named Phase deliverables. The other three (qmd, vectorless,
WeKnora) are Study verdicts, but each contributes something concrete — qmd's fusion math, vectorless's shell-command
tool surface, WeKnora's anti-pattern catalogue.

This document does not re-review individual repos. The per-file notes in `docs/repo-notes/` cover that ground. What it
does is name what this cluster collectively establishes, extract the reusable engineering patterns, connect G6 to the
broader Linus corpus, and make the phase-tagged implications explicit so they can be acted on without re-reading six
notes.

---

## The unifying thesis

MCP as Linus's tool substrate is no longer an open architectural question. It is resolved, from evidence, and this
synthesis is the right place to canonicalize that resolution.

The evidence did not arrive as a single decisive argument. It arrived incrementally, from multiple directions. pmetal
ships `pmetal-mcp` with 45 tools for Claude Desktop. openclaw wraps its gateway as an MCP endpoint. py3plex ships
`py3plex-mcp` for graph queries. agentmemory exposes 51 tools over MCP. claw-code-local bridges Ollama behind an MCP
surface. fastmcp is the framework underneath most of these, and it is purpose-built for exactly this pattern. Five
independent repos across multiple groups independently answered "how do I expose capabilities to an AI agent?" with the
same answer. Phase 3 MCP adoption is overdetermined. The only decisions that remain are operational: which tools, what
permissions, which transport (stdio for local-only, streamable-http when two harnesses need simultaneous access), and
how to compose multiple servers into one endpoint a front-end sees. All of these are engineering decisions, not
architectural ones, and fastmcp provides the machinery for each.

The practical implication is that DEC-0029's "KB tool registry" question is answered: build it as a FastMCP server with
`@mcp.tool`-decorated functions calling into KnowledgeBase, not as a bespoke in-house protocol layer. Do not design a
Linus-native tool protocol. Do not wait for Phase 3 to make the call. The call is already made by the weight of
evidence.

---

## Key findings

**fastmcp (Integrate) — closes Phase 1f, underwrites Phase 2 tool registry.** The Phase 1f deliverable names fastmcp
evaluation explicitly. The verdict is simple: adopt. fastmcp is the decorator-plus-introspection framework that turns a
typed Python function into a schema-validated, documentation-complete MCP tool in one line. `@mcp.tool` on a typed
function produces a JSON schema automatically from type hints and a docstring; `@mcp.resource("kb://paper/{id}")`
registers a URI-template resource; four transports (stdio, http, sse, streamable-http) are a single `run()` argument;
OAuth, JWT, and OIDC live in `server/auth/`; a real middleware pipeline covers caching, rate limiting, response
limiting, timing, logging, authorization, and tool injection. `FastMCP.as_proxy()` wraps any MCP server — in-memory,
stdio, or HTTP — and re-exposes its surface, which is how Linus would eventually compose pmetal-mcp's 45 tools under its
own endpoint with Linus middleware applied. Apache 2.0. Python ≥3.10 (linus env is 3.12). The Phase 1f smoke test is:
`pip install fastmcp`, write a 30-line server that wraps one KnowledgeBase query as an `@mcp.tool`, point Cline at it
over stdio, confirm a round-trip, write the verdict as an ADR. If that round-trip has surprises, surface them. Otherwise
commit.

**ontomics (Integrate) — Maestro's semantic window into `src/linus/`.** ontomics is a Rust binary (npm-distributed,
`npm install -g @ontomics/ontomics`) that builds a precomputed semantic ontology of a codebase from tree-sitter ASTs:
TF-IDF concept extraction, naming-convention detection, abbreviation resolution, behavioral function-body clusters via
Candle embeddings (BGE-small 384-dim for concepts, CodeRankEmbed 768-dim for function bodies), PageRank entity scoring,
and approximately 20 MCP tools over a SQLite index at `<repo>/.ontomics/index.db`. The README's headline claim — "~20×
fewer tokens" against Claude Sonnet on external ML repos — is a single precomputed query against a resident index, not
on-the-fly parsing. The startup is deliberately deferred: the MCP server is ready immediately on a graph built without
embeddings; embedding work completes in a background thread. `ontology_diff` against a git ref is a cheap semantic-delta
summary useful for branch reviews. The Apple Silicon story is clean: Candle ships a `metal` feature flag.

The critical positioning decision: ontomics is a codebase-shape tool, not a paper-corpus tool. It answers "what does
`transform` mean in this codebase?" and "which functions compute the same thing under different names?". It is not a
KnowledgeBase component. It is a Maestro navigation tool for `src/linus/` — the layer that lets Claude Code and Cline
understand Linus's own growing codebase without burning 20 read operations per question. Register it in the Phase 2 MCP
surface via `claude mcp add -s user ontomics -- ontomics` and an `.mcp.json` at the repo root.

**codesight (Integrate) — structural complement to ontomics's semantic layer.** codesight is an `npx`-runnable
TypeScript CLI with zero runtime dependencies — no `dependencies` field in `package.json` — that compiles a structural
context map (routes, ORM models, import graph, component tree, blast-radius, env) and exposes it as 13 MCP tools over a
hand-rolled JSON-RPC 2.0 stdio server. It runs in approximately 200ms. AST parsing is opportunistic: TypeScript projects
get genuine TS compiler API analysis; Python gets an inline stdlib-`ast` extractor that handles FastAPI, Flask, Django,
and SQLAlchemy; Go uses a similar shell-out pattern. Framework coverage is intentionally wide and shallow — 33
web-framework detectors, 13 ORM detectors, 14 languages — while ontomics is narrow and deep.

The ontomics/codesight pairing is the practical answer to "what does a Worker know about the repo it's editing?" before
it starts. ontomics answers the semantic question (domain vocabulary, naming conventions, behavioral clusters);
codesight answers the structural question (where are the routes, what does this import graph look like, what is the
blast radius of changing this module). Together they replace 40–70K tokens of ad-hoc file reading with two targeted MCP
tool calls. They are not competing; register both.

**qmd (Study) — most liftable retrieval artifact for Phase 3.** qmd is a local hybrid search engine for Markdown
corpora: BM25 via SQLite FTS5, vector search via sqlite-vec, and cross-encoder reranking via Qwen3-Reranker-0.6B, all
running through node-llama-cpp on the Metal backend. Its most directly transferable artifact is the fusion math in
`src/store.ts`. The query flow: expand the original query into two LLM variants (total three query forms), run BM25 plus
vector for each (six ranked lists), fuse with RRF at k=60 plus an original-query ×2 weight and a top-rank bonus (+0.05
for rank 1, +0.02 for ranks 2–3), take the top 30 candidates, rerank with the cross-encoder, then blend position-aware
(rank 1–3: 75% RRF / 25% reranker; rank 4–10: 60/40; rank 11+: 40/60). This blend prevents the reranker from destroying
high-confidence exact-match results — a failure mode that naive "reranker wins" pipelines hit. The Phase 3
hybrid-retrieval deliverable should crib this math directly from `src/store.ts` rather than derive it from first
principles. qmd as a backend for KnowledgeBase is not the recommendation; it is Markdown-centric and lives in the
JavaScript runtime. But the math is the artifact worth carrying.

**vectorless (Study) — shell-command navigation surface worth porting.** vectorless's philosophical claim (retrieval by
LLM-driven document navigation, zero embeddings) is aggressive and the latency cost is real — 20–80 LLM calls per query
against a non-trivial corpus, minutes per answer on a local 7B Worker. That cost rules it out as a primary retrieval
path. What survives as a reusable architectural idea is the shell-command vocabulary: `ls`, `cd`, `cat`, `grep`, `find`,
`toc`, `concepts`, `chain`, `summarize`, `compare`, `done`. This vocabulary, implemented as a thin MCP surface over
KnowledgeBase's existing section graph, gives Maestro and Workers a navigable document-tree interface that complements
vector retrieval rather than replacing it. The cost of building `kb_ls` / `kb_cd` / `kb_cat` / `kb_grep` / `kb_concepts`
over existing KnowledgeBase metadata is small; the payoff is a retrieval mode appropriate for precise, multi-hop
navigation on small document sets where the latency of 5–10 navigation calls is acceptable. A smoke test in
`experiments/vectorless-smoke/` (3–5 papers, Ollama/qwen2.5-coder:14b, same Dan-task questions as the qmd baseline)
produces the data that determines whether this pattern earns a Phase 3 tool slot.

**WeKnora (Study) — the conscious anti-pattern.** WeKnora is Tencent's enterprise RAG platform: Go monolith, Python gRPC
sidecar, Vue/TS frontend, six-container Docker Compose minimum (frontend, app, docreader, Postgres, Redis, Jaeger),
optional Neo4j, MinIO, Langfuse. On Dan's M1 Max, Docker has no Metal or ANE passthrough. Every embedding or inference
call routed through a containerized Ollama loses the unified-memory advantage that the whole Linus stack is built
around. This is directly against the CLAUDE.md rule: Docker only for stateless services; inference stays native.

WeKnora is worth studying precisely because it makes explicit what "serious enterprise RAG" considers table stakes in
2026: pluggable vector stores (pgvector, Elasticsearch, Milvus, Weaviate, Qdrant), parent-child chunking, per-KB
indexing strategy toggles, unified LLM provider abstraction across 14 backends, sandboxed Agent Skills, and IM channel
integrations. Linus does not need any of these now. The provider abstraction pattern (`internal/models/`) and the per-KB
indexing toggle are worth reading before designing Linus's own inference provider interface. Everything else is a
catalogue of Linus non-requirements. WeKnora's existence is the clearest articulation in the corpus of why Linus made
the choices it did: local-native inference, SQLite over Postgres, no multi-tenancy, Docker only for stateless
components.

---

## Patterns and modules worth lifting

The most immediately actionable pattern from this cluster is the FastMCP decorator idiom applied to KnowledgeBase. Every
KnowledgeBase capability (semantic search, hybrid retrieval, paper fetch, citation graph walk, Cypher query) becomes an
`@mcp.tool`-decorated function on a single `FastMCP` instance, with a `@mcp.resource("kb://paper/{id}")` template per
resource type. No bespoke protocol design. The shape is: import fastmcp, instantiate `mcp = FastMCP("linus-kb")`,
decorate functions, call `mcp.run(transport="streamable-http", port=PORT)`. The middleware pipeline handles rate
limiting and logging. `FastMCP.as_proxy()` handles composition when pmetal-mcp's tools need to appear under the same
endpoint.

The deferred-startup pattern from ontomics — MCP server available immediately, expensive indexing runs in a background
thread — is the right ergonomic for any Linus tool whose first-run cost is dominated by one-time computation. Wire this
into the Phase 2 KB server design: return "indexing in progress" for embedding-dependent tools until the background
thread completes; make BM25 and metadata tools available immediately.

The qmd position-aware rerank blend (`ranks 1–3: 75/25; 4–10: 60/40; 11+: 40/60`) is a concrete Phase 3 engineering
artifact. Implement it in KnowledgeBase's retrieval layer alongside the existing RRF. The original-query ×2 weight
prevents query expansion from diluting high-confidence matches on the original phrasing — particularly important for
exact-term searches in scientific literature.

The vectorless shell-command surface (`kb_ls`, `kb_cd`, `kb_cat`, `kb_grep`, `kb_concepts`) is Phase 2/3 MCP tool
material, built over KnowledgeBase's existing graph and section metadata. The vectorless architecture note makes the
case; the build is in Linus code, not adopted from vectorless itself.

The `@require`/`@ensure` contract pattern from py3plex (via icontract) — adopted in the G5 py3plex note — pairs well
with FastMCP's typed-function idiom. Tool function signatures carry the type constraints; icontract pre/post-conditions
carry the semantic invariants. Together they give the tool registry a first-class testing story without a separate test
layer for each tool.

---

## Cross-references

**G3 (obsidian-llm-wiki-local, llm-wiki synthesis) → fastmcp + MCP transport.** The llm-wiki synthesis identified
obsidian-llm-wiki-local as the cleanest fully-local Ollama pattern and recommended Ollama hardening conventions from
that cluster. Those same conventions apply to any FastMCP tool that routes through Ollama: the Ollama flash-attention
and KV cache env vars (`OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`) are already in CLAUDE.md's Known Library
Quirks. The Phase 2 FastMCP tool server that calls `ollama.generate()` should inherit those env vars in its launch
configuration.

**G5 (hyalo, keppi, KB tooling) → ontomics + codesight positioning.** The G5 KB tooling cluster covers the
KnowledgeBase's own paper-corpus tools: ingestion, vector retrieval, graph traversal. ontomics and codesight are
explicitly not KB components — they operate on `src/linus/` and whatever repo a Worker is editing, not on the paper
corpus. The boundary matters: G5 tools serve the KnowledgeBase's knowledge layer; G6 code-context tools serve the coding
layer. Both register in the same FastMCP surface, but they answer different questions. Keppi's blast-radius analysis
(what does updating this graph node affect?) has a codesight analog in its blast-radius MCP tool over import graphs —
these are cognates worth comparing when Phase 3 hybrid-retrieval design lands.

**G1 (pmetal-mcp) → FastMCP composition.** pmetal ships 45 MCP tools. If Phase 1b's pmetal verdict is favorable,
`FastMCP.as_proxy(pmetal_server)` lets Linus re-expose those 45 tools under the Linus endpoint with Linus middleware
applied. This is the lowest-cost path to a rich tool surface in Phase 2: Linus adds KB tools on top of pmetal's
inference and training tools, and `as_proxy` handles the composition without duplicating the tool definitions.

**Total-landscape MCP finding.** The total-landscape document's "MCP as tool substrate" observation, previously framed
as a Phase 3 question, is now resolved by the weight of evidence across G1, G5, and G6. The synthesis recommendation is
to update the total-landscape's MCP section from "candidate substrate" to "committed substrate, pending policy
decisions." The policy decisions — tool allowlist, transport selection, per-tool permission tiers — belong in a new ADR
(`DEC-NNNN, slug mcp-adoption`) at Phase 2a planning time, not Phase 3.

---

## Phase-tagged implications

**Phase 1f (fastmcp evaluation, qmd baseline, vectorless smoke test).** Phase 1f already lists fastmcp evaluation as a
named deliverable. The evaluation is a 30-line smoke test, not a research project: install, write one tool, confirm a
round-trip, write the ADR. Alongside it: run qmd against a Markdown slice of the KnowledgeBase (notes, threads, paper
abstracts) and compare top-k against KnowledgeBase's current retrieval — a fast, honest data point on whether
BM25+vector+rerank wins on Dan's specific corpus. Run the vectorless smoke test on 3–5 papers to get the latency number
that determines whether the navigation pattern is Worker-viable at all on local hardware.

**Phase 2a (orchestration layer, tool registry foundation).** Build the Phase 2 KB tool registry as a FastMCP server.
The tool set at launch: semantic search, hybrid retrieval (BM25+vector), paper fetch, citation graph walk. Transport:
`streamable-http` on localhost from day one — not stdio — because Cline and Claude Code will want simultaneous access.
Register ontomics and codesight in the same MCP surface immediately. The three-tool Phase 2 MCP surface (KB tools +
ontomics + codesight) is the foundation the Phase 3 expansion builds on.

**Phase 2b (Maestro src/ navigation).** Once `src/linus/` has enough code to be worth indexing, ontomics provides the
semantic map and codesight provides the structural map. The combined MCP surface — ontomics's domain concepts and naming
conventions, codesight's routes/models/import graph — replaces 40–70K tokens of ad-hoc file reading with targeted tool
calls. This is the enabler for efficient Worker task execution against Linus's own codebase. Smoke-test on the
KnowledgeBase submodule (`src/linus/` is still sparse) before claiming it as a Phase 2 deliverable; the KnowledgeBase's
Python code is a messier target than the clean ML repos ontomics benchmarks on.

**Phase 3 (hybrid retrieval, KB shell-command tools).** The qmd fusion math (RRF k=60, original-query ×2, position-aware
rerank blend) is a Phase 3 copy-and-adapt, not a rederivation. Implement it in KnowledgeBase's retrieval layer.
Simultaneously, add the vectorless-style shell-command tool surface (`kb_ls`, `kb_cd`, `kb_cat`, `kb_grep`,
`kb_concepts`) as a second retrieval mode behind the same FastMCP endpoint — useful for multi-hop navigation on small
document sets where vector recall is not the bottleneck. If the vectorless smoke test produces favorable latency
numbers, this surface gets a dedicated MCP tool slot. If not, it remains study material.

**Phase 3 (MCP policy ADR).** The MCP adoption decision needs an ADR before Phase 3 begins, not during it. The ADR
content: commit to MCP as the tool substrate; specify the initial tool allowlist; assign permission tiers per tool class
(read-only KB tools at Tier 0, write-capable tools at Tier 2); specify the transport (streamable-http on localhost);
specify the composition strategy (FastMCP.as_proxy for pmetal-mcp if Phase 1b verdict is favorable). This is three hours
of writing, not three months of evaluation.

---

## Open questions for Dan

**Stdio or streamable-http from Phase 2 launch?** The fastmcp note frames this as a question; this synthesis recommends
streamable-http on localhost from day one. The reasoning: Cline and Claude Code will want simultaneous access to the
same KB tool surface, and spawning N stdio children for N clients is more fragile than one HTTP server. Is there a
reason to start with stdio instead — startup latency, process isolation, dependency simplicity?

**Ontomics benchmarking scope.** The 20× token reduction claim is on voxelmorph and ScribblePrompt — clean ML repos.
Dan's scientific Python (numerical pipelines, bioinformatics, no web framework routes) is a messier target. Should the
Phase 1f benchmark suite include an ontomics run against the KnowledgeBase submodule to confirm the ratio holds? And
should CodeRankEmbed's clustering of bioinformatics function bodies (lots of array math, similar shapes, different
intents) get an explicit ablation before ontomics is registered as a default Worker tool?

**Which comes first: MCP ADR or Phase 3 design?** The total-landscape observation is that MCP adoption is now
overdetermined, but the ADR formalizing the commitment has not been written. Should this happen at the start of Phase 2a
planning — before any tool code is written — so that the commit is explicit and the policy decisions are made once
rather than implied by implementation choices?

**Vectorless bake-off model selection.** The vectorless smoke test needs an LLM in the loop. Against a hosted model
(Claude Haiku, gpt-4o-mini) the quality ceiling is honest but expensive; against Ollama/qwen2.5-coder:14b the ceiling is
the realistic Linus-on-MacBook constraint. The two answers could diverge significantly. Which framing is more useful for
the Phase 3 decision: "does this pattern work in principle?" (hosted) or "does this pattern work on my hardware?"
(local)?

**WeKnora's per-KB indexing toggle — relevant for KnowledgeBase v1?** WeKnora lets each knowledge base instance
independently choose its retrieval mode (dense-only, hybrid, GraphRAG, Wiki). KnowledgeBase v1 currently has no such
toggle. Should the Phase 2 KB design commit to one retrieval mode for simplicity, or build the toggle mechanism from the
start? The Algorithm says delete requirements; but adding the toggle later if multiple retrieval modes coexist is harder
than building it in.

---

_This synthesis should be revisited when the Phase 1f fastmcp, qmd, and vectorless smoke tests produce results (they
determine the Phase 2 tool surface), when the MCP adoption ADR lands (it collapses the remaining policy questions), and
when Phase 3 hybrid-retrieval design begins (the qmd fusion math and vectorless navigation pattern both land there as
concrete inputs)._
