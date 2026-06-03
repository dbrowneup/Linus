# paper-qa evaluation → a Linus-native RAG substrate

**Date:** 2026-06-02 **Status:** evaluation + design sketch for Dan's review **Owner:** Maestro
**Context:** DEC-0044 adopted paper-qa as the Phase-2c citation-grounded QA engine. Live testing
this session showed that integration is the wrong call: paper-qa **timed out at 10 minutes on
12 papers** (`curl` exit 28). Dan's direction (2026-06-02): _"study it, copy the best ideas —
especially full-text embedding for passage-level traceability — and build our own faster
substrate on our terms. Push the frontier instead of sitting on it."_ This doc is that study.

## What paper-qa actually does (anatomy + cost model)

Read against the installed source (`paper-qa 2026.3.18`).

**Ingest (`Docs.aadd`, once per process — not persisted):** parse PDF → chunk the **full text**
(`readers.py`, default **5000 chars / chunk with overlap**, char- or token-based) → embed every
chunk with the configured embedder (Linus wired `ollama/mxbai-embed-large`). The `Docs` object
lives in memory only; nothing is written to disk, so **every new process re-parses and
re-embeds the entire corpus**.

**Query (`Docs.aquery`):**

1. Embed the query, retrieve top **`evidence_k` (default 10)** chunks by cosine (MMR).
2. **Evidence "map" step (`core._map_fxn_summary`): one LLM call _per retrieved chunk_** —
   produces a relevance-scored (~100-word) contextual summary. With defaults that is **10 LLM
   calls**. (`evidence_skip_summary=False` by default; setting it `True` skips this entire step.)
3. Filter by `evidence_relevance_score_cutoff` (≥1), keep top **`answer_max_sources` (default 5)**.
4. **One** final LLM call synthesizes the answer with inline grounded citations.

**Per-query cost with defaults: ~11 LLM calls + a full-corpus embedding pass.** On local
qwen3:8b (~15–20 s/call) that is minutes of LLM time alone — the timeout is structural, not a
tuning miss.

## What's genuinely good (adopt the _ideas_, on our terms)

- **Full-text chunking is the right call** and the thing KB doesn't give us. KB's SPECTER2
  embeddings are **title+abstract only** (KB CLAUDE.md: _"Do NOT feed full text"_), so they
  support paper-level retrieval but not passage-level traceability. Detailed, checkable answers
  need the body text chunked and embedded. This is the frontier Dan named.
- **Passage-level provenance.** `Context → Text → Doc(dockey, pages, formatted_citation)` plus a
  per-chunk relevance score maps cleanly onto Linus's DEC-0023 provenance
  (`{paper_id, page, excerpt, score}`) and the "follow the trail to the source" goal.
- **Optional per-chunk relevance scoring + summarization** is a real precision lever — it filters
  off-topic chunks and condenses — but it's the expensive step. paper-qa already exposes the
  on/off switch (`evidence_skip_summary`); the design lesson is to make this a **mode**, not an
  always-on default.
- **Local-model-hardened JSON parsing** (`core.llm_parse_json`: strips `<think>` tags, repairs
  fraction scores and broken JSON) — worth lifting wholesale for any structured local-LLM output.
- **Citation stripping** (`strip_citations`) so the source's own bibliography doesn't collide with
  Linus's grounded citations.

## What's wrong for us (build differently)

1. **No persistence.** Re-embedding full text every process is the dominant cost and makes
   corpus-scale impossible. → **A persistent full-text chunk-embedding store** (embed once, reuse
   forever) is the single highest-leverage change.
2. **`evidence_k` LLM calls per query.** The per-chunk "map" summarization is the latency killer
   on local hardware. → Default to **retrieve-then-synthesize (1 LLM call)**; offer the per-chunk
   rerank/summary as an opt-in **rigorous mode**.
3. **A second, independent embedder.** paper-qa ignores everything KB already built. → One Linus
   embedding substrate; reuse KB's abstract-SPECTER2 for coarse paper-level retrieval where it
   helps.

## A Linus-native RAG sketch (for discussion)

- **Persistent chunk store.** Chunk PDFs (≈Dan-tunable size/overlap) once; embed once; store
  vectors + provenance (`sha256`, page, char-span, text) in SQLite (`sqlite-vec`) or numpy+ANN.
  Built incrementally (embed-on-first-access, cached forever) or batch over the corpus.
- **Retrieval.** Fast path: cosine top-k passages over the chunk store. Optional two-stage:
  KB abstract-SPECTER2 narrows to candidate papers → full-text passages within them (reuses KB,
  scales, sharper).
- **Synthesis.** **Fast mode (default):** top-k passages → one grounded-citation LLM call, run
  through `rigor.py` (DEC-0059). **Rigorous mode (opt-in):** paper-qa-style per-chunk
  relevance-scored summaries before synthesis, for high-stakes manuscript work.
- **Citations.** passage + paper + page + score, click-through to the source PDF — the
  traceability spine Dan wants.

## Open decisions (the sharp questions live in the PR/chat)

1. Embedder for full-text chunks (mxbai-embed-large? a SPECTER2 variant? a general/long-context
   model?) — full text wants a different model than abstract-SPECTER2.
2. Persistence scope: pre-embed the whole corpus's full text (≈GB-scale store, long one-time
   build) vs. grow-on-demand-and-cache.
3. Default mode given Dan wants _both_ fast and precise — where does the fast/rigorous knob sit?
4. Two-stage (KB abstract → full-text passages) vs. single-stage full-text index.
5. v0.5.0 scope: tag now on the orchestration substrate with native RAG as v0.6.0, or hold the
   tag for the native RAG?
6. Build-from-scratch vs. lift paper-qa's Apache-2.0 readers/chunkers as libraries while
   replacing the orchestration (persistence + drop the per-chunk LLM map).

## Disposition of the current paper-qa integration

Keep the in-tree `linus.knowledge.paperqa` wrapper + this session's ingest fix as an **optional
"deep-dive over a few named papers" tool** (it works for small, explicit sets), but **demote it
from the corpus marquee.** Supersede DEC-0044 with a new ADR adopting the Linus-native substrate
once the direction is chosen.

## Speed vs. rigor is not a strict frontier (deeper analysis, per Dan's prompt)

Dan's instinct — that fast and precise needn't be mutually exclusive — is correct. paper-qa's
latency doesn't come from "rigor"; it comes from **one expensive way of buying precision**: an
LLM call per retrieved chunk (`evidence_k` summaries). That conflates rigor with a single
implementation. Precision in RAG actually comes from several independent levers, and most are far
cheaper than per-chunk LLM summarization:

- **Retrieval quality — the dominant lever, and cheap.** The answer is only as good as the top-k
  passages. Wins: coherent chunking (semantic/structural, not arbitrary 5000-char cuts); a strong
  embedder; **hybrid dense + lexical retrieval fused via RRF** (KB already has TF-IDF + SPECTER2 —
  the qmd RRF pattern is liftable); optional one-shot query expansion / HyDE. Get the top-k
  _right_ and the expensive per-chunk filtering becomes largely redundant.
- **Cross-encoder reranking — most of paper-qa's per-chunk benefit at ~1000× less cost.** A small
  cross-encoder reorders the top-k by query–passage relevance in **milliseconds**, no per-chunk
  LLM call. This captures the relevance-scoring half of paper-qa's evidence step almost for free.
- **Citation verification as a cheap post-hoc gate, not an upfront map.** Dan's rigor = _the claim
  traces to a verifiable passage_. Achieved by feeding the synthesis LLM the actual passages with
  stable ids, requiring inline citations, then **verifying each cited claim against its passage** —
  which Linus already has in `rigor.py` (DEC-0059). That's one structured check (or a cheap
  entailment model), not N LLM summaries.

What the per-chunk LLM summary genuinely adds is (a) relevance scoring — a cross-encoder does this
cheaper — and (b) compressing each chunk to its question-relevant core, which matters only when
chunks are long/noisy and context is tight. Both shrink with better chunking and larger context
windows. So: paper-qa sits at an _expensive corner_, not on an unavoidable speed/rigor frontier.

**Design consequence for the v0.6.0 Linus-native RAG.** Don't frame it as a binary "fast mode vs
rigorous mode." Make the **default both fast and well-grounded**:

```
persistent full-text chunk store
  → hybrid retrieve top-N (dense + BM25, fused via RRF)
  → cross-encoder rerank to top-k
  → one grounded-citation synthesis call
  → rigor.py verifies every cited claim against its cited passage
```

and reserve an **optional max-rigor top-up** (paper-qa-style per-chunk LLM extraction, or a second
verification pass) for genuinely high-stakes claims (manuscript submission). The knob isn't "speed
vs rigor"; it's "how much _marginal_ precision to pay on top of an already fast-and-grounded
baseline." Most queries never need the top-up.

This reframes the open decisions above:

- The two model choices that matter are the **full-text chunk embedder** and a **small local
  cross-encoder reranker** — both swappable behind a clean interface (the modular boundary Dan
  asked for, so we can rebuild a component if it's a bottleneck).
- **Persistence scope** (whole-corpus pre-embed vs grow-on-demand-and-cache) becomes a pure
  cost/coverage call, now decoupled from the speed/rigor question.
- The deferred **RAG-vs-no-RAG measurement** should evaluate this default pipeline and **ablate the
  levers** (retrieval-only → +rerank → +LLM-topup) — turning Dan's "are they exclusive?" question
  into an empirical speed/precision curve rather than an assumption.

