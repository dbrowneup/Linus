# qmd (`tobi/qmd`)

## 1. Purpose and scope

QMD — "Query Markup Documents" — is an on-device search engine for Markdown corpora (notes, transcripts, docs, code)
authored by Tobi Lutke and shipped as the `@tobilu/qmd` npm package. It combines BM25 full-text search (SQLite FTS5),
vector semantic search (sqlite-vec), and LLM cross-encoder re-ranking, fused via Reciprocal Rank Fusion. All inference
runs locally through `node-llama-cpp` against three small GGUF models (an EmbeddingGemma-300M embedder, a
Qwen3-Reranker-0.6B cross-encoder, and a fine-tuned `qmd-query-expansion-1.7B` Qwen3 variant). It exposes a CLI, a
TypeScript SDK (`createStore`), and an MCP server with both stdio and HTTP transports. For Linus this is the most
directly relevant retrieval reference for Phase 1f evaluation, the Phase 2 KB tool registry (DEC-0029), and the Phase 3
hybrid-retrieval deliverable.

## 2. Architecture summary

A single TypeScript codebase, ~7k lines across `src/store.ts` (the unified search/index facade), `src/llm.ts` (all
node-llama-cpp model loading and prompt formatting), `src/db.ts` (SQLite schema), `src/ast.ts` (tree-sitter chunking),
and an `mcp/` server. Persistence is one SQLite file at `~/.cache/qmd/index.sqlite` with seven tables: `collections`,
`path_contexts`, `documents`, `documents_fts` (FTS5 BM25), `content_vectors` (chunk metadata), `vectors_vec` (sqlite-vec
ANN), and `llm_cache` for memoizing query expansions and rerank scores. Documents are chunked at ~900 tokens with 15%
overlap by a smart-boundary scorer that prefers Markdown headings, code-fence boundaries, and horizontal rules over
arbitrary cuts; for `.ts/.tsx/.js/.jsx/.py/.go/.rs` files an opt-in `--chunk-strategy auto` adds tree-sitter AST break
points (class/interface/struct/impl/trait = 100, function/method = 90, type/enum = 80, import/use = 60) merged with the
regex scores. The hybrid `query` flow expands the original query into two LLM variants, runs BM25 + vector for each of
the three queries (six ranked lists total), fuses them with RRF (k=60) plus an original-query ×2 weight and a top-rank
bonus (+0.05 for #1, +0.02 for #2–3), takes top 30 candidates, reranks via node-llama-cpp's `createRankingContext()` /
`rankAndSort()` API on Qwen3-Reranker, and finally blends RRF and reranker scores position-aware (rank 1–3: 75/25; 4–10:
60/40; 11+: 40/60). The MCP server's HTTP daemon mode keeps GGUF models resident in VRAM across requests, with
embedding/rerank contexts disposed after 5-min idle and lazily recreated.

## 3. What's reusable in Linus

QMD implements two of the three legs of the Phase 3 hybrid-retrieval target (BM25 + vector + graph traversal fused via
RRF). The fusion mathematics, the position-aware blend that prevents the reranker from destroying high-confidence exact
matches, and the original-query weighting are directly transferable to KnowledgeBase — they encode hard-won behavior
that a from-scratch RRF would have to rediscover. node-llama-cpp on Apple Silicon uses the llama.cpp Metal backend, so
the GGUF inference path is M1-Max-friendly out of the box; the three default models total ~2.0 GB of weights, well
within budget. The MCP server with both stdio and HTTP transports is a working reference for DEC-0029's "KB tool
registry over MCP" question — particularly the daemon mode's pattern of "models stay loaded; contexts are disposable."
The `createStore()` SDK shape (inline config, YAML config, or DB-only reopen) and the `--explain` flag that returns
per-document score traces (RRF rank, rerank confidence, blended score) are good templates for Linus's KB API. Smart
Markdown chunking with code-fence protection is an obvious lift for indexing Dan's notes/papers corpus.

## 4. What's inspiration only

Compared with **WeKnora** (a multi-source RAG framework) and **vectorless** (LLM-as-retriever, no embeddings at all),
qmd is deliberately the narrowest of the three: Markdown-first, single-user, single-machine, three small GGUFs. That
narrowness is the point — it ships a complete hybrid pipeline in ~7k lines of TypeScript where WeKnora needs a service
mesh. For Linus, qmd's narrowness means it is more useful as a _blueprint_ than as a dependency: the Linus KB needs to
ingest PDFs (papers), code, threads, and pictures, not just `.md`, and Linus's retrieval has to fuse the KnowledgeBase
graph as a third leg. The fine-tuned `qmd-query-expansion-1.7B` model is also inspiration — Linus could plausibly
fine-tune its own query-expansion small model on the paper corpus during Phase 6, with the qmd model as a worked example
of "small fine-tune for a specific narrow task."

## 5. What's incompatible or out of scope

The hard requirement on Node.js >=22 / Bun >=1.0 plus Homebrew SQLite means qmd lives in the JavaScript runtime, not
Linus's Python orchestration layer — it must be wrapped (CLI, MCP, or a child process around the SDK), not imported.
node-llama-cpp pulls its own Metal-compiled llama.cpp at install time, which duplicates capability already covered by
Ollama and pmetal; running three inference stacks on one machine is wasteful unless qmd's three small models stay
resident in the qmd process and serve only retrieval. The schema is Markdown-centric (single `documents` table with a
title and body), so non-Markdown sources need either pre-conversion or schema work. The `bun build --compile` warning in
CLAUDE.md ("never run it, breaks sqlite-vec") is a reminder that the sqlite-vec native binding is fragile across build
changes.

## 6. Recommendation: **Study**

The Phase 3 RRF hybrid-retrieval deliverable should crib the fusion math, position-aware blend, and rerank-on-top-30
pattern straight from `src/store.ts` rather than reinvent. Run qmd against a Markdown subset of the KnowledgeBase as a
Phase 1f baseline and compare its top-k against KnowledgeBase's current retrieval — a fast, honest data point on whether
the BM25+vector+rerank combo actually wins for Dan's corpus. Do not adopt qmd as the Linus KB backend; the Markdown-only
schema and the JS-runtime cost don't fit. Treat the MCP server as a reference for DEC-0029 sequencing and for the
"shared HTTP daemon vs per-client subprocess" tradeoff.

## 7. Questions for Dan

- **Is RRF+rerank the right Phase 3 fusion target for KnowledgeBase?** qmd's blend of RRF, original-query ×2 weight,
  top-rank bonus, and position-aware rerank merging is more elaborate than "RRF k=60." Worth porting wholesale, or start
  with vanilla RRF and earn complexity by measurement?
- **Phase 1f baseline scope.** Does running qmd against a Markdown slice of the corpus (notes/, threads/, maybe paper
  abstracts) and comparing top-k against KnowledgeBase's retriever count as a useful Phase 1f data point, or is the
  Markdown-only constraint too narrow to be informative?
- **Three inference stacks on one box.** Ollama, pmetal (pending Phase 1b), and qmd's node-llama-cpp would each load
  their own Metal context. If qmd is adopted even as a study tool, do we cap it to short-lived runs, or accept a
  resident MCP daemon as a third concurrent inference process?
- **Query-expansion fine-tune.** Tobi shipped a 1.7B Qwen3 fine-tuned for query expansion. This is a tractable Phase 6
  exercise on Dan's corpus — useful as a first LoRA target, or distract from harder scientific-domain fine-tunes?
- **Differentiator vs siblings (vectorless, WeKnora).** I called qmd "narrowest of the three." Useful framing, or would
  Dan rather see them ranked on a different axis (Apple-Silicon-native, Markdown-fit, MCP-readiness)?
