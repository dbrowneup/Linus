## DEC-0062 — Linus-native RAG supersedes paper-qa as the corpus retrieval-and-synthesis engine; paper-qa demoted to an optional deep-dive tool

**Date:** 2026-06-03 **Status:** accepted

**Context.** DEC-0044 (2026-05-06) adopted paper-qa (FutureHouse, Apache-2.0) as the Phase-2c KnowledgeBase
retrieval-and-synthesis engine on an explicit "adopt + extend" posture: expose it as a Linus tool over a preindexed
`context/papers/` tree, and in Phase 3 "swap KnowledgeBase's retrieval layer to paper-qa's tantivy index and RCS
pipeline, keeping KnowledgeBase as corpus-of-record." That decision was made from a repo-study verdict — paper-qa earned
the only corpus-shaped Integrate in the g8-sci-agents fan-out — not from running it against Dan's corpus at scale.

Live testing during the v0.5.0 close (2026-06-02) ran paper-qa against Dan's papers for the first time and found the
adoption posture structurally unworkable on local hardware: a single corpus-scale query **timed out at 10 minutes on 12
papers** (`curl` exit 28). The cost model explains why, and it is architectural rather than a tuning miss. paper-qa holds
its `Docs` index in process memory only — **nothing is persisted, so every new process re-parses and re-embeds the
entire corpus** — and each query runs an evidence "map" step that issues **one LLM call per retrieved chunk**
(`evidence_k=10` by default) before a final synthesis call, i.e. **~11 local-LLM calls per query**. On a qwen3-class
Worker at ~15–20 s/call that is minutes of LLM time per question, before counting the full-corpus re-embed. paper-qa is
well-built for hosted-model, few-document workflows; it is the wrong shape for a persistent, corpus-scale, local-first
engine. The full anatomy and cost model are in
[`docs/specs/2026-06-02-paperqa-evaluation-and-linus-native-rag.md`](../specs/2026-06-02-paperqa-evaluation-and-linus-native-rag.md).

The supersession was initially recorded only in the question and landscape docs; this ADR captures it in the
authoritative decision layer, where DEC-0044 had remained plainly `accepted` — the gap this ADR closes.

**Decision.** Two parts.

1. **Demote paper-qa from the corpus engine to an optional "few named papers" deep-dive tool.** The in-tree
   `linus.knowledge.paperqa` wrapper (plus the v0.5.0 ingest fix) stays as a tool for deep reads over a small, explicit
   set of named papers, where its per-chunk evidence summarization is an asset and the latency is acceptable. paper-qa's
   **Integrate verdict for that narrow use stands** — DEC-0044's repo-note verdict is not reversed. What is superseded is
   DEC-0044's _corpus-scale_ "adopt + extend / swap KB's retrieval to paper-qa" posture.

2. **Build a Linus-native full-text-chunk RAG as the v0.6.0 corpus retrieval-and-synthesis engine.** The native engine
   fixes paper-qa's two structural problems: a **persistent full-text chunk-embedding store** (embed once, reuse across
   processes — the single highest-leverage change) and a **retrieve-then-synthesize default (one LLM call)**, with the
   expensive per-chunk relevance summarization available as an opt-in _rigorous mode_ rather than an always-on default.
   Dan's build calls (2026-06-03): **lift the plumbing, build the brain** — reuse paper-qa's Apache-2.0 readers/chunkers
   as libraries, replace the orchestration (persistence + retrieval + synthesis) with Linus-native code — and build the
   **full modular skeleton** up front: persistent chunk store → two-stage retrieve (KB abstract-SPECTER2 narrows to
   candidate papers → full-text passages within them) + cross-encoder rerank → fast/rigorous synthesis modes through the
   rigor gate, with each stage swappable as measurement directs.

**What we keep from paper-qa (the ideas, on our terms).** Full-text chunking — KB's SPECTER2 embeddings are
title+abstract only, supporting paper-level retrieval but not the passage-level traceability detailed answers need, so
the body text must be chunked and embedded. Passage-level provenance (`Context → Text → Doc`, mapping onto DEC-0023's
`{paper_id, page, excerpt, score}` shape). The local-model-hardened JSON parsing (`llm_parse_json`: strips `<think>`
tags, repairs fraction scores and broken JSON). The `evidence_skip_summary` switch, lifted as a fast/rigorous **mode**
rather than an always-on cost. Citation stripping, so a source's own bibliography does not collide with Linus's grounded
citations.

**Open sub-decisions (resolved at build time, tracked as R5-09).** Five design choices remain deliberately open: the
full-text embedder (full text wants a different model than abstract-SPECTER2); persistence scope (whole-corpus
pre-embed vs. grow-on-demand-and-cache); where the fast/rigorous knob sits by default; two-stage vs. single-stage
retrieval; and the build-vs-lift line per component. The grader for the RAG-vs-no-RAG ablation (R2-03) is likewise
chosen at build time, with the real questions in hand. The KB-side packaging that lets the native RAG import KB modules
directly — the Option C layered env plus the hardcoded-paths refactor (R5-01 / R5-02) — lands **before** the RAG build,
per Dan's 2026-06-03 sequencing.

**Consequence.** DEC-0044's corpus-engine posture is superseded; its status becomes
`accepted (corpus-engine posture superseded by DEC-0062; "few named papers" optional-tool use retained)`. The Phase-2→3
"RAG beats the bare-Worker baseline" gate — the North-Star evidence claim that local models can be private _and_
powerful — moves from v0.5.0 to **v0.6.0**, measured against the native engine. KnowledgeBase remains corpus-of-record;
the native RAG reads KB outputs from disk today and imports KB modules after the Option-C packaging lands. paper-qa's
runtime dependencies (`fhlmi`, `fhaviary`) stay for the optional tool but are no longer load-bearing for the corpus
path. v0.5.0 was tagged on the orchestration substrate without this engine; v0.6.0 is the corpus-RAG marquee.

**References.**

- [DEC-0044](0044-paper-qa-kb-retrieval-engine.md) — paper-qa as the Phase-2c corpus engine. Corpus-engine posture
  **superseded** by this ADR; the "few named papers" optional-tool verdict is retained.
- [DEC-0023](0023-output-interface-citations-llm-wiki.md) — output/provenance shape (`{paper_id, page, excerpt, score}`)
  the native citations map onto.
- [DEC-0029](0029-episodic-memory-substrate.md) — episodic store (Layer C); orthogonal to the corpus-RAG path and
  unaffected.
- [DEC-0059](0059-grounding-gate-output-surface.md) — grounding/rigor gate the native synthesis output runs through.
- [DEC-0061](0061-network-policy-framework.md) — network-policy framework; native-RAG embedding and retrieval are
  local-only (`offline`), no egress.
- Spec: [`docs/specs/2026-06-02-paperqa-evaluation-and-linus-native-rag.md`](../specs/2026-06-02-paperqa-evaluation-and-linus-native-rag.md)
  — full paper-qa anatomy, cost model, native-RAG design sketch, and speed-vs-rigor analysis.
- Open design decisions tracked as **R5-09** in [`docs/questions/top-questions.md`](../questions/top-questions.md).
