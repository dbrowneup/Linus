# Paper Notes

One-page summaries of every PDF in [`context/papers/`](../context/papers/), each
written as a translation layer between dense technical material and Linus' practical
needs. The notes themselves live in [`paper-notes/`](paper-notes/), and filenames mirror
the PDF basenames so `<paper>.md` corresponds to `<paper>.pdf`.

Each note follows the same shape: TL;DR, plain-language problem statement, what the
paper proposes, key results, what's reusable in Linus, what's NOT applicable
(the hype-filter section), connections to other notes/repos/phases, and open
questions for Dan.

The notes are grouped below by theme rather than by date, since the practical
question is usually "what do I read to think about X" and not "what's newest."

---

## BitNet — Native low-bit LLMs

The most internally-coherent thread in this folder. Six papers from Microsoft
Research (and one community-built inference runtime) tracing the path from
"can a 1-bit LLM exist" (2023) to "here's a 2B open checkpoint that runs at
0.4 GB on Apple Silicon" (2025). Read in order if approaching this thread cold;
otherwise [BitNet b1.58 2B4T](paper-notes/2504.12285v2.md) and [bitnet.cpp](paper-notes/2502.11880v1.md)
are the two highest-leverage entry points for Linus.

- [BitNet (original, 2023-10)](paper-notes/2310.11453v1.md) — BitLinear, the first 1-bit
  Transformer trained from scratch. Founding paper.
- [BitNet b1.58 (2024-02)](paper-notes/2402.17764v1.md) — Adds the zero state to make
  ternary `{-1, 0, +1}` weights. The variant everyone means when they say
  "BitNet" today.
- [BitNet a4.8 (2024-11)](paper-notes/2411.04965v1.md) — First push to 4-bit activations
  via hybrid quantization + sparsification. Mostly superseded by BitNet v2.
- [BitNet v2 (2025-04)](paper-notes/2504.18415v2.md) — 4-bit activations done elegantly via
  Hadamard transforms. The current best W1.58A4 design.
- [BitNet b1.58 2B4T (2025-04)](paper-notes/2504.12285v2.md) — *The released open-weights
  checkpoint.* 2B params, 4T training tokens, instruction-tuned via SFT+DPO.
  Highest-priority paper in the folder for immediate Linus action.
- [bitnet.cpp (2025-02)](paper-notes/2502.11880v1.md) — The CPU inference runtime that makes
  BitNet b1.58 2B4T fast on Apple Silicon. Tested up to M2 Ultra; the only paper
  in this folder with direct Apple-Silicon throughput numbers.
- [BitNet Distillation (2025-10)](paper-notes/2510.13998v1.md) — How to convert *any*
  pre-trained FP16 model (Qwen3, Gemma) into a 1.58-bit BitNet for a specific
  downstream task using only ~10B tokens. Plausibly Phase 6's recipe.

## Larger-than-RAM inference on Apple Silicon

The two papers most directly tied to Linus' hardware constraints (32 GB unified
memory, 1 TB SSD, M1 Max). Both are about *streaming* model weights from flash
on demand rather than loading everything into DRAM. Together they map the full
range from "small models on big-RAM machines" through "70B-class models on
consumer Macs" to "397B-class MoE models on a 48 GB MacBook."

- [LLM in a Flash (Apple, 2023-12)](paper-notes/2312.11514v3.md) — The conceptual foundation:
  flash-streaming via activation-sparsity prediction, sliding-window cache, and
  bundled column/row reads. Tested on M1 Max, MeasureBook directly relevant.
- [Flash-MoE (Anthropic + Daniel Woods, 2026-03)](paper-notes/flash_moe.md) — The extreme
  demonstration: 397B-parameter MoE running at 5.7 tok/s on a 48 GB M3 Max via
  custom Metal/Obj-C inference engine. Notable: primary author is Claude Opus
  4.6 itself.

## Benchmarking & inference evaluation

A single paper but one with direct operational implications. Evaluation methodology often gets
treated as a solved problem; this paper argues it is not, specifically for the metrics used
to select local models.

- [Speed and LLMs: Not All Is About Tokens per Second (Conde et al., 2025-02)](paper-notes/2502.16721v1.md) —
  Five open-weights ~7B models run on 660 questions across three task designs spanning the verbosity
  spectrum (minimal output, fixed-length, open-ended explanation). **Task-completion-time rankings
  frequently invert tok/s rankings**: LLaMA-3-8B is among the slowest in tok/s but fastest to finish
  short tasks; Gemma-7B is fastest for open explanation despite mediocre tok/s. The core message:
  tok/s conflates tokenizer efficiency, verbosity, and generation speed into a single number that
  can mislead Worker model selection. The paper's three-task schema (minimal / fixed-length / open-ended,
  measured by wall-clock time) is a ready-made template for `benchmarks/dan_tasks/`.

## Training stability — multi-stream residuals

Single paper, but a substantial one. Aimed at people who design model
architectures, not at people who just use them.

- [JPmHC (JP Morgan, 2026-02)](paper-notes/2602.18308v2.md) — How to constrain the
  residual-stream mixer in Hyper-Connections to the orthogonal group via the
  Cayley transform, preventing the spectral-collapse failure mode of the prior
  doubly-stochastic approach. Validated on ARC-AGI with a 7M-parameter Tiny
  Recursive Model.

## Pre-training data curation

- [FineWeb (Hugging Face, 2024-06)](paper-notes/2406.17557v2.md) — The 15T-token open
  Common Crawl dataset (and its 1.3T educational subset, FineWeb-Edu) plus the
  open-source `datatrove` curation library. Used by BitNet b1.58 2B4T as a
  pretraining source. Methodologically interesting beyond just the data.

## KnowledgeBase ingestion — keyphrase extraction

Two complementary papers on automatically extracting keyphrases from documents during KB ingestion.
Read together: the first provides a fast, structural, unsupervised baseline; the second enriches it
with knowledge-graph semantics. Both directly address the Phase 2 KB indexing problem.

- [RaKUn 2.0 (Škrlj, Koloski & Pollak, 2022-08)](paper-notes/2208.07262v1.md) — Graph-based
  unsupervised keyphrase extractor at the Pareto frontier of retrieval quality and speed. **Up to
  two orders of magnitude faster than YAKE and MultiPartiteRank** across 15 benchmark datasets,
  with statistically indistinguishable F1@15. Processes **14 million biomedical documents in ~40
  seconds** on 12-core/32GB hardware (directly comparable to M1 Max). CPU-only, pure Python
  (`pip install rakun2`), no GPU or fine-tuning required. The Phase 2 KB ingestion tool for fast,
  large-scale keyphrase tagging and KG node-candidate generation.

- [KGRank (Shi, Zheng, Yu et al., 2017-11)](paper-notes/s41019-017-0055-z.md) — Replaces the
  standard word co-occurrence graph with a semantically enriched graph derived from DBpedia,
  linking noun-phrase keyterms to knowledge-graph entities and ranking via Personalized PageRank.
  **Best F-measure ~0.33 at K=10 on DUC2001**, outperforming all seven baselines. The key insight:
  two terms semantically related but textually far apart get a connecting edge through KG paths —
  a failure mode of TextRank and RaKUn 2.0 that KGRank sidesteps. Phase 3 KB ingestion reference
  for domain-ontology-enriched indexing (substituting GO, MeSH, ChEBI for DBpedia).

## Knowledge graphs & KnowledgeBase foundations

The two papers here are the theoretical and methodological backbone for
building [modules/KnowledgeBase/](../modules/KnowledgeBase/) — one giving the
*structural* substrate (a graph of entities and relations) and the other giving
the *vector* substrate (semantic embeddings over the nodes). They are best
read together.

- [Knowledge Graphs (Hogan et al., 2020-03 / 2021-09)](paper-notes/2003.02320v6.md) —
  The 100+ page tutorial-survey by a 17-author consortium that emerged from the
  2018 Dagstuhl seminar and crystallized the field. Walks through every layer of
  the KG stack: data models (RDF, property graphs), querying (SPARQL, Cypher),
  schemata (semantic, validating, emergent), identity, context, deductive
  knowledge (ontologies, rules, OWL, DLs), inductive knowledge (analytics,
  embeddings, GNNs, rule mining), creation, quality, refinement, and
  publication. Authored in part by Aidan Hogan at Universidad de Chile. **The
  single most KB-relevant paper in this folder** — almost every KB design
  decision Dan needs to make has a section in this paper.

## Embeddings & retrieval (KnowledgeBase-aligned)

- [Extracting Sentence Embeddings from Pretrained Transformer Models
  (Stankevičius & Lukoševičius, 2024-08)](paper-notes/2408.08073v2.md) — A 75-page
  systematic ablation of how to get good fixed-length embeddings out of
  pretrained transformers without fine-tuning. Token aggregation (idf
  weighting, first+last layer averaging, bias removal) and post-processing
  (quantile-uniform normalization, whitening, ABTT) collectively raise
  STS Spearman correlation from 62.3 → 71.6. Most striking: random embeddings
  + the same techniques nearly match BERT, proving most of the gain is in
  the shaping, not the contextualization. The KB-vector-layer companion to
  the Hogan KG survey — directly informs embedding choices for
  [modules/KnowledgeBase/](../modules/KnowledgeBase/), and its evaluation
  methodology is a template for Linus' benchmark suite.

- [Interpreting the Curse of Dimensionality (Peng, Gui & Wu, 2024-01 / 2025-03)](paper-notes/2401.00422v3.md) —
  A short, surgical theoretical paper that proves *why* high-dimensional
  embeddings degrade: distance concentration (Minkowski, Chebyshev, and cosine
  distances all converge to a single value as dimension grows) and manifold
  effect (when `d ≫ n`, the bottom `d−n` PCA eigenvalues are exactly zero, so
  the data is forced onto a low-dim manifold). Empirically validated on Iris,
  Dermatology, Satimage, Control, Mfeat — all reach 90% variance with <10
  PCs. The theoretical foundation that explains *why* the Stankevičius
  embedding-shaping techniques are so effective, and *why* PCA-reducing
  oversized embeddings before indexing is almost always a free win.

## High-dimensional geometry / visualization (Dan's biology overlap)

- [Orthogonal projections of hypercubes (Horiike & Fujishiro, Phys Rev E
  2025)](paper-notes/Horiike-Orthogonal projections of hypercubes-2025-Physical Review E copy.md)
  — A pure-physics paper. Uses PCA as a principled, reproducible orthogonal
  projection method for visualizing high-dimensional binary state spaces (Ising
  spin systems, gene regulatory networks, evolutionary fitness landscapes).
  Connection to Linus is indirect; included here because Dan flagged it as a
  "hypercube" paper of interest.

## Cognitive throughput & information theory

Two papers that debate the information throughput of the human brain. They form a natural
pair — read the Zheng & Meister paper first, then the Sauerbrei & Pruszynski rebuttal. The
debate is scientifically interesting to Dan as a researcher, and the core framing (a narrow
conscious channel bottlenecked at ~10 bits/s above a massively parallel substrate) maps
cleanly onto the Maestro/Worker architecture. Neither paper contains code or algorithms.

- [The Unbearable Slowness of Being (Zheng & Meister, Caltech, Neuron 2025-01)](paper-notes/PIIS0896627324008080.md) —
  A Perspective applying information theory to a century of behavioral data. Human cognition —
  typing, reading, Tetris, competitive gaming, memory sports — operates at a consistent
  **~10 bits/s** regardless of modality, while peripheral senses ingest **~10⁹ bits/s**. The
  "Sifting Number" Si = 10⁸ is called the largest unexplained constant in brain science. The
  proposed outer/inner brain two-mode model maps onto Linus's Maestro (conscious synthesis) vs.
  Worker (parallel execution) split, and the ~5 GB lifetime information acquisition estimate has
  implications for KB scope and completeness goals.

- [The Brain Works at More than 10 bits/s (Sauerbrei & Pruszynski, Nat Neurosci 2025-07)](paper-notes/nihms-2096004.md) —
  A direct rebuttal arguing the 10 bits/s figure is a *lower bound* on whole-brain throughput, not
  an upper bound. Unconscious sensorimotor processing (the cerebellum alone contains half of all
  brain neurons) operates far above 10 bits/s; the Zheng-Meister measurement captures only the
  conscious cognitive output channel. The inner/outer brain partition is anatomically incoherent.
  For Linus: this deepens the Maestro/Worker analogy — Workers handle the high-bandwidth
  sensorimotor-equivalent substrate; Maestro handles the narrow conscious synthesis channel.

---

## Reading orders by Linus phase

**If you only have time for two papers**:
[BitNet b1.58 2B4T](paper-notes/2504.12285v2.md) (Linus' near-term Worker model) +
[bitnet.cpp](paper-notes/2502.11880v1.md) (how to run it on M1 Max).

**Phase 2 (Linus MVP, Worker selection + KB v1)**:
2B4T → bitnet.cpp → BitNet b1.58 (background on what 2B4T inherits) →
[Speed and LLMs](paper-notes/2502.16721v1.md) (benchmark methodology for Worker selection) →
[Knowledge Graphs](paper-notes/2003.02320v6.md) (KB structural design) →
[Sentence Embeddings](paper-notes/2408.08073v2.md) (KB embedding pipeline) →
[RaKUn 2.0](paper-notes/2208.07262v1.md) (fast keyphrase extraction for KB ingestion) →
[Curse of Dimensionality](paper-notes/2401.00422v3.md) (why embedding-dim choices matter).

**Phase 3 (Knowledge & Parallel Agents)**:
[Knowledge Graphs](paper-notes/2003.02320v6.md) is the spine here — every KB design
decision (data model, schema, identity, context, querying, deductive vs inductive
layer) has a section in it. [Sentence Embeddings](paper-notes/2408.08073v2.md) and
[Curse of Dimensionality](paper-notes/2401.00422v3.md) are the rate-limiting papers
for the *vector* layer over the graph — KB retrieval quality is bounded by embedding
quality, and embedding quality is bounded by how well distance concentration is
mitigated. [KGRank](paper-notes/s41019-017-0055-z.md) is the Phase 3 upgrade for
keyphrase extraction, enriching KB node labels with ontology-grounded semantics.

**Phase 6 (fine-tuning)**:
BitNet Distillation → 2B4T → BitNet original (for BitLinear / SubLN /
training-stability fundamentals) → FineWeb (for continued-pretraining corpus).

**Phase 6+ (long-context / batched inference)**:
BitNet v2 (4-bit KV cache, Hadamard outlier handling) → bitnet.cpp.

**Phase 7+ (large fine-tuned models, > 10 GB)**:
LLM in a Flash → Flash-MoE.

**Phase 8 (research directions)**:
JPmHC → Flash-MoE → all four BitNet papers, as the seed for a
"BitNet-MoE-streaming-with-Cayley-stability" synthesis.

## Cross-cutting open questions

> **All cross-cutting questions below resolved 2026-05-03.** See
> [../questions/top-questions.md](../questions/top-questions.md) Resolution Log and
> [../specs/planning-update-spec.md](../specs/planning-update-spec.md) for execution
> detail. Resolutions summarized inline below for reading-in-place.

The notes individually flag questions for Dan; a few reappear across multiple
notes and may deserve a discussion of their own:

1. **Is the *single most useful Phase 1 spike* "build bitnet.cpp on M1 Max, pull `bitnet-b1.58-2B-4T-gguf`, benchmark vs Ollama-served Qwen and Llama"?** **RESOLVED:** Yes — adopted as first concrete Phase 1c experiment using task-completion-time methodology in `benchmarks/dan_tasks/`.
2. **Should Linus commit to a BitNet-derived Worker for Phase 6, or keep the FP16-LoRA option open?** **RESOLVED:** Defer the lane decision until Phase 1c BitNet data lands. Phase 6a commits to FP16-LoRA on genomics/biochem corpus regardless. Decision gate at Phase 6a/6b boundary.
3. **Is a BitNet × Flash-MoE × JPmHC synthesis a real Phase 8 research direction, or premature speculation?** **RESOLVED:** Stays Phase 8 long-horizon research direction in landscape docs; no Phase 6/7 work gated on it. Phase 6d stretch target = opportunistic ternary >8B integration via mlx-flash if community releases.
4. **Should there be a `synthesis-bitnet-on-apple-silicon.md` companion note?** **RESOLVED:** Defer until Phase 1c BitNet results land. If the spike validates the path, the synthesis earns its writing time then.
5. **Should the KB v1 embedding pipeline use the recipe from [Stankevičius & Lukoševičius](paper-notes/2408.08073v2.md)?** **RESOLVED:** Run a unified Phase 2 ablation matrix (SPECTER2 raw / +Stankevičius post-processing / BGE-base / +post-processing / random+post-processing) × {full-dim, PCA-256/384/512}. Adopt winning recipe. Methodology folded into `docs/experimental-protocol.md` (Phase 1c). **[KB-spec]**.
6. **Should there be a `docs/specs/kb-architecture.md`?** **RESOLVED:** Yes — adopted as **[KB-spec] Phase 2 deliverable**, walking the Hogan KG survey section-by-section, reflecting the dual RDF + property graph commitment.
7. **Should KB embeddings be PCA-reduced before indexing, and should the KB observability dashboard track distance discrimination as a health metric?** **RESOLVED:** Both — folded into the Phase 2 unified embedding ablation (item 5 above) and the KB observability surface.
8. **Should `benchmarks/dan_tasks/` be structured around a three-task schema with wall-clock task-completion time as the primary metric?** **RESOLVED:** Yes — three-task schema (minimal / fixed-length / open-ended) with wall-clock as **primary** axis. Multiple metrics recorded (tok/s, RSS, TTFT, completion time, quality). Worker selection is **holistic**. Public eval baselines (MBPP/HumanEval/MMLU/GPQA) run alongside.
9. **Should RaKUn 2.0 be the Phase 2 keyphrase extraction layer for KB ingestion?** **RESOLVED:** **Integrate-and-evaluate, not adopt outright.** RaKUn 2.0 enters KB as additional tool alongside the existing TF-IDF + BERTopic + SPECTER2 + UMAP pipeline. Phase 2 evaluation (overlap with author keywords + Dan manual top-5 + τ ∈ {0.5, 1.0, 1.5} sweep) decides production layer. Possibly retain both as parallel signals. **[KB-spec]**.
10. **Should the Phase 2 Linus output interface default to high-information-density concise summaries?** **RESOLVED:** Yes — adopt 10-bits/s framing as Phase 2 design principle. **Balanced bullets + prose** (not bullet dumps). **Citations and traceability are first-class.** Worker outputs preserved for Maestro inspection. Opt-in `/verbose`. Reframes Linus as personal LLM Wiki at scale.
