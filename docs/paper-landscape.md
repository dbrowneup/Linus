# Paper Notes

One-page summaries of every PDF in [`context/papers/`](../../context/papers/), each
written as a translation layer between dense technical material and Linus' practical
needs. Filenames mirror the PDF basenames so `<paper>.md` corresponds to `<paper>.pdf`.

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
otherwise [BitNet b1.58 2B4T](2504.12285v2.md) and [bitnet.cpp](2502.11880v1.md)
are the two highest-leverage entry points for Linus.

- [BitNet (original, 2023-10)](2310.11453v1.md) — BitLinear, the first 1-bit
  Transformer trained from scratch. Founding paper.
- [BitNet b1.58 (2024-02)](2402.17764v1.md) — Adds the zero state to make
  ternary `{-1, 0, +1}` weights. The variant everyone means when they say
  "BitNet" today.
- [BitNet a4.8 (2024-11)](2411.04965v1.md) — First push to 4-bit activations
  via hybrid quantization + sparsification. Mostly superseded by BitNet v2.
- [BitNet v2 (2025-04)](2504.18415v2.md) — 4-bit activations done elegantly via
  Hadamard transforms. The current best W1.58A4 design.
- [BitNet b1.58 2B4T (2025-04)](2504.12285v2.md) — *The released open-weights
  checkpoint.* 2B params, 4T training tokens, instruction-tuned via SFT+DPO.
  Highest-priority paper in the folder for immediate Linus action.
- [bitnet.cpp (2025-02)](2502.11880v1.md) — The CPU inference runtime that makes
  BitNet b1.58 2B4T fast on Apple Silicon. Tested up to M2 Ultra; the only paper
  in this folder with direct Apple-Silicon throughput numbers.
- [BitNet Distillation (2025-10)](2510.13998v1.md) — How to convert *any*
  pre-trained FP16 model (Qwen3, Gemma) into a 1.58-bit BitNet for a specific
  downstream task using only ~10B tokens. Plausibly Phase 6's recipe.

## Larger-than-RAM inference on Apple Silicon

The two papers most directly tied to Linus' hardware constraints (32 GB unified
memory, 1 TB SSD, M1 Max). Both are about *streaming* model weights from flash
on demand rather than loading everything into DRAM. Together they map the full
range from "small models on big-RAM machines" through "70B-class models on
consumer Macs" to "397B-class MoE models on a 48 GB MacBook."

- [LLM in a Flash (Apple, 2023-12)](2312.11514v3.md) — The conceptual foundation:
  flash-streaming via activation-sparsity prediction, sliding-window cache, and
  bundled column/row reads. Tested on M1 Max, MeasureBook directly relevant.
- [Flash-MoE (Anthropic + Daniel Woods, 2026-03)](flash_moe.md) — The extreme
  demonstration: 397B-parameter MoE running at 5.7 tok/s on a 48 GB M3 Max via
  custom Metal/Obj-C inference engine. Notable: primary author is Claude Opus
  4.6 itself.

## Training stability — multi-stream residuals

Single paper, but a substantial one. Aimed at people who design model
architectures, not at people who just use them.

- [JPmHC (JP Morgan, 2026-02)](2602.18308v2.md) — How to constrain the
  residual-stream mixer in Hyper-Connections to the orthogonal group via the
  Cayley transform, preventing the spectral-collapse failure mode of the prior
  doubly-stochastic approach. Validated on ARC-AGI with a 7M-parameter Tiny
  Recursive Model.

## Pre-training data curation

- [FineWeb (Hugging Face, 2024-06)](2406.17557v2.md) — The 15T-token open
  Common Crawl dataset (and its 1.3T educational subset, FineWeb-Edu) plus the
  open-source `datatrove` curation library. Used by BitNet b1.58 2B4T as a
  pretraining source. Methodologically interesting beyond just the data.

## Embeddings & retrieval (KnowledgeBase-aligned)

- [Extracting Sentence Embeddings from Pretrained Transformer Models
  (Stankevičius & Lukoševičius, 2024-08)](2408.08073v2.md) — A 75-page
  systematic ablation of how to get good fixed-length embeddings out of
  pretrained transformers without fine-tuning. Token aggregation (idf
  weighting, first+last layer averaging, bias removal) and post-processing
  (quantile-uniform normalization, whitening, ABTT) collectively raise
  STS Spearman correlation from 62.3 → 71.6. Most striking: random embeddings
  + the same techniques nearly match BERT, proving most of the gain is in
  the shaping, not the contextualization. **The most KB-relevant paper in
  this folder** — directly informs embedding choices for
  [modules/KnowledgeBase/](../../modules/KnowledgeBase/), and its evaluation
  methodology is a template for Linus' benchmark suite.

## High-dimensional geometry / visualization (Dan's biology overlap)

- [Orthogonal projections of hypercubes (Horiike & Fujishiro, Phys Rev E
  2025)](Horiike-Orthogonal projections of hypercubes-2025-Physical Review E copy.md)
  — A pure-physics paper. Uses PCA as a principled, reproducible orthogonal
  projection method for visualizing high-dimensional binary state spaces (Ising
  spin systems, gene regulatory networks, evolutionary fitness landscapes).
  Connection to Linus is indirect; included here because Dan flagged it as a
  "hypercube" paper of interest.

---

## Reading orders by Linus phase

**If you only have time for two papers**:
[BitNet b1.58 2B4T](2504.12285v2.md) (Linus' near-term Worker model) +
[bitnet.cpp](2502.11880v1.md) (how to run it on M1 Max).

**Phase 2 (Linus MVP, Worker selection + KB v1)**:
2B4T → bitnet.cpp → BitNet b1.58 (background on what 2B4T inherits) →
[Sentence Embeddings](2408.08073v2.md) (KB embedding pipeline).

**Phase 3 (Knowledge & Parallel Agents)**:
[Sentence Embeddings](2408.08073v2.md) is the rate-limiting paper here — KB
retrieval quality is bounded by embedding quality.

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

The notes individually flag questions for Dan; a few reappear across multiple
notes and may deserve a discussion of their own:

1. **Is the *single most useful Phase 1 spike* "build bitnet.cpp on M1 Max,
   pull `bitnet-b1.58-2B-4T-gguf`, benchmark vs Ollama-served Qwen and Llama"?**
   Mentioned in 2B4T, bitnet.cpp, and BitNet Distillation notes.
2. **Should Linus commit to a BitNet-derived Worker for Phase 6, or keep the
   FP16-LoRA option open?** Mentioned in BitNet b1.58 and BitNet Distillation
   notes.
3. **Is a BitNet × Flash-MoE × JPmHC synthesis a real Phase 8 research
   direction, or premature speculation?** Mentioned in JPmHC and Flash-MoE notes.
4. **Should there be a `synthesis-bitnet-on-apple-silicon.md` companion note
   that pulls the four-or-five most relevant papers into one "what's the actual
   inference path" writeup?** Mentioned in BitNet v2 and 2B4T notes.
5. **Should the KB v1 embedding pipeline use the recipe from
   [Stankevičius & Lukoševičius](2408.08073v2.md)** (idf weighting + first+last
   layers + quantile-u normalization), and should that paper's ablation
   methodology be lifted into a `docs/experimental-protocol.md` Linus-house
   style guide for benchmark design? Mentioned in the embeddings note.
