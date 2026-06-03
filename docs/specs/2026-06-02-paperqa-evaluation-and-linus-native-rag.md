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
