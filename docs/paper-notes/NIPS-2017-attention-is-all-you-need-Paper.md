---
title: "Attention Is All You Need"
source: NIPS 2017
authors:
  Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, Illia
  Polosukhin
affiliation: Google Brain, Google Research, University of Toronto
date: 2017-06
pdf: ../../context/papers/NIPS-2017-attention-is-all-you-need-Paper.pdf
tags:
  [transformer, attention, foundational, seq2seq, machine-translation, multi-head, positional-encoding, architecture]
---

# Attention Is All You Need

## TL;DR

The paper that defined the substrate. Vaswani et al. propose the Transformer: an encoder-decoder sequence model with no
recurrence and no convolution, only stacked self-attention and position-wise feed-forward layers. The mechanism is
**scaled dot-product attention** computed as `softmax(QK^T / sqrt(d_k))V`, run in **multi-head** parallel projections,
with **sinusoidal positional encodings** added to embeddings to inject order. Trained on WMT 2014, the big model reaches
**28.4 BLEU on EN-DE** and **41.0 BLEU on EN-FR** in 3.5 days on 8 P100 GPUs — beating the prior state of the art
(including ensembles) at a fraction of the training cost. The architecture's two operationally critical properties are
O(1) sequential operations per layer (vs. O(n) for RNNs, enabling massive training parallelism) and O(1) maximum path
length between any two positions (vs. O(n) for RNNs, easing long-range dependency learning). Every modern LLM Linus will
ever run is a direct descendant of this design.

## The problem (in plain language)

In 2017, the dominant sequence-to-sequence models — for translation, summarization, language modeling — were RNNs (LSTM,
GRU) and convolutional encoders (ByteNet, ConvS2S), often augmented with attention as a side mechanism connecting
encoder to decoder. RNNs have a fundamental constraint: hidden state at position t depends on hidden state at position
t-1, so computation cannot be parallelized within a training example. As sequences get longer, this becomes the
bottleneck — memory limits batch size, and within-example sequentiality limits hardware utilization. Convolutional
approaches sidestep the sequentiality but pay for it with deeper stacks needed to relate distant positions (path length
grows with distance). Both architectures struggle with long-range dependencies precisely because the gradient signal
traverses a long, lossy path between distant tokens.

The paper's question: can you build a sequence model out of attention alone — no recurrence, no convolution — and get
competitive (or better) translation quality at lower training cost? Their answer is yes, and the architecture they offer
turns out to generalize far beyond translation.

## What they propose

The full Transformer is an encoder stack of N=6 identical layers and a decoder stack of N=6 identical layers, both
operating on d_model=512 vectors. Each encoder layer is `LayerNorm(x + Sublayer(x))` applied twice — once for multi-head
self-attention, once for a position-wise FFN with d_ff=2048 and ReLU between two linear maps. Each decoder layer adds a
third sub-layer: multi-head **cross-attention** where queries come from the decoder and keys/values come from the
encoder output. Decoder self-attention is **causally masked** (-inf on illegal positions inside the softmax) to preserve
auto-regressive generation.

The attention primitive is scaled dot-product: `Attention(Q,K,V) = softmax(QK^T / sqrt(d_k)) V`. The √d_k scaling
matters because for large d_k, raw dot products grow with variance d_k, pushing the softmax into low-gradient regions;
the scaling keeps the softmax in a usable regime. They chose dot-product over additive attention because it maps
directly onto highly optimized matmul kernels — a hardware-aware choice that ages extremely well.

**Multi-head attention** runs h=8 attention computations in parallel, each on linearly projected Q, K, V of dimension
d_k = d_v = d_model/h = 64, then concatenates and projects back. Total compute is roughly the same as a single
full-dimensional head, but each head can specialize on a different subspace / relation type, and the appendix shows
heads picking up syntactic and coreference patterns.

**Positional encoding** is sinusoidal: a deterministic function of position and dimension, with wavelengths in geometric
progression from 2π to 10000·2π. Because for any fixed offset k, PE(pos+k) is a linear function of PE(pos), the model
can in principle learn to attend by relative position. They tried learned positional embeddings and got nearly identical
results (Table 3 row E); they kept sinusoids for the chance of length extrapolation.

The training recipe: Adam (β1=0.9, β2=0.98, ε=1e-9) with the now-canonical "warmup then inverse-square-root" schedule
(warmup_steps=4000), residual dropout 0.1, label smoothing 0.1, byte-pair-encoded vocabulary (~37k EN-DE, 32k WPM
EN-FR), batches of ~25k source / 25k target tokens, base model 100k steps in 12 hours, big model 300k steps in 3.5 days.

## Key results

**Translation.** Big Transformer hits 28.4 BLEU on WMT14 EN-DE (newstest2014), beating previous best (including
ensembles) by >2 BLEU. On EN-FR, 41.0 BLEU — new single-model SOTA at <1/4 the training FLOPs of the prior best. Base
Transformer alone (12 hours, 8×P100) beats every previously published single model and ensemble. Training cost in FLOPs
is roughly 2.3e19 (big EN-DE) vs. 1.2e21 for GNMT+RL Ensemble — close to two orders of magnitude cheaper for better
quality.

**Complexity comparison (Table 1).** Self-attention: O(n²·d) per layer, O(1) sequential ops, O(1) max path length. RNN:
O(n·d²) per layer, O(n) sequential, O(n) path. Convolution (kernel k): O(k·n·d²) per layer, O(1) sequential, O(log_k(n))
path. The decisive numbers are the sequential-ops and path-length columns; the O(n²·d) per-layer cost is the price paid
(and is exactly the cost that the entire long-context literature since 2019 has tried to attack).

**Ablations (Table 3).** Single-head attention loses 0.9 BLEU vs. h=8; too many heads (h=32) also degrades. Reducing d_k
hurts quality, suggesting compatibility scoring is non-trivial. Bigger d_model and d_ff help. Dropout is essential to
avoid overfitting. Sinusoidal vs. learned positional embeddings ≈ tie.

**Generalization.** Brief WSJ English constituency parsing experiment shows the Transformer generalizes outside
translation with no architectural changes — early evidence that this was a general-purpose sequence model, not a
translation trick.

## What's reusable in Linus

This is the substrate of literally everything Linus does. Every Worker model — Qwen2.5-Coder, Mistral-7B, Llama 3.x,
BitNet variants, the eventual fine-tuned Linus — is a decoder-only Transformer (the encoder half got dropped after
BERT/GPT diverged, but the core attention + FFN + residual + layer-norm block is unchanged in structure). Knowing this
paper cold is a prerequisite for reading anything else in the corpus.

Concrete load-bearing implications for Linus design:

- **Quantization (BitNet thread).** The BitNet papers ([2310.11453v1](2310.11453v1.md), [2402.17764v1](2402.17764v1.md),
  [2504.18415v2](2504.18415v2.md), [2504.12285v1](2504.12285v1.md)) replace the FP linear projections inside attention
  and FFN with 1-bit / 1.58-bit weights. The architecture they replace is exactly this one. Understanding which tensors
  are quantized (the WiQ/WiK/WiV/WO and FFN W1/W2 matrices) requires Section 3 of this paper as the reference.
- **Memory-pillar complexity (Garrison thread).** The TC0 / hard-attention / soft-attention expressivity bounds in
  [2305.15408v5](2305.15408v5.md), [2310.07923v5](2310.07923v5.md), and the rest of the Garrison thread are bounds on
  _this exact architecture_. The "intra-step latent memory" tier in Linus's memory pillar is constrained by what this
  architecture can compute in a single forward pass. The chain-of-thought escape hatch is precisely the move from one
  forward pass to many — a workaround for the depth/path limits established by the design Vaswani et al. introduced.
- **Larger-than-RAM streaming (mlx-flash, flash-MoE, LLM in a Flash).** The streaming work in `repos/mlx-flash/` and
  `repos/flash-moe/` is engineering on top of this layer structure: they stream the per-layer weight tensors (the same
  WQ/WK/WV/WO/FFN matrices) from SSD into Metal memory layer-by-layer. The N=6 (here) → N=32+ (modern) layer stack is
  what makes streaming a viable approach: each layer's weights are an independent unit you can swap.
- **KV cache and inference economics.** Auto-regressive generation reuses K and V from past tokens — the KV cache that
  dominates inference memory at long context is a direct consequence of the attention formulation here. Every M1 Max
  memory budget calculation Linus will ever do (32 GB unified, n² attention scratch, KV cache growth) traces back to
  Section 3.2.1.
- **Multi-head as a parallelism unit.** Multi-head attention is embarrassingly parallel across heads. On Metal/MLX this
  is a natural granularity for kernel work. Worth remembering when reasoning about throughput on Apple Silicon vs. CUDA
  assumptions.

Phase relevance: foundational reference, not phase-gated. Cite from Phases 1, 2, 6, 7. Re-read sections 3.2 and 4 before
any quantization, fine-tuning, or KV-cache work.

## What's NOT applicable

The specific 2017 numbers are dead. d_model=512, h=8, N=6, d_ff=2048 are toy sizes by 2025 standards (Llama-3-8B is
N=32, d_model=4096, d_ff=14336, h=32 with 8 KV heads via GQA). The base/big distinction is gone — modern models have a
continuous size ladder.

The encoder-decoder split is gone for everything Linus uses. Decoder-only (GPT lineage) won; the encoder half lives on
in BERT-style retrievers (and is relevant to the KnowledgeBase embedding stack) but not in Linus Worker models.
Sinusoidal positional encoding has been replaced by RoPE (rotary), ALiBi, or NoPE in essentially every modern model —
the linear-extrapolation property the authors hoped sinusoids would give in fact didn't hold well, and RoPE handles it
better.

LayerNorm has been largely replaced by RMSNorm (cheaper, comparable quality). Post-norm (`LayerNorm(x + Sublayer(x))`,
as in this paper) has been replaced by pre-norm (`x + Sublayer(LayerNorm(x))`) in basically every modern model because
it trains more stably at depth. ReLU FFNs have been replaced by SwiGLU / GeGLU. The vanilla learning-rate schedule with
warmup + inverse-sqrt is still used but cosine schedules are now equally common.

The WMT 2014 translation focus is irrelevant; Linus is not in the translation business. The "no quantization" assumption
is irrelevant; Linus runs everything quantized.

This is a "read once, re-read sections 3.2 and 4 occasionally, refer to as the canonical source" paper. It's not
actionable in the sense that no one is going to implement the 2017 base model; it is actionable in the sense that every
other paper in the corpus assumes you know it.

## Connections

The BitNet thread ([2310.11453v1](2310.11453v1.md), [2402.17764v1](2402.17764v1.md), [2504.18415v2](2504.18415v2.md),
[2504.12285v1](2504.12285v1.md)) modifies the linear projections inside this architecture. Read Section 3.2 of this
paper before any of those.

The memory-pillar / expressivity thread ([2305.15408v5](2305.15408v5.md), [2310.07923v5](2310.07923v5.md), and the rest
of the Garrison synthesis) is about complexity-class bounds on the architecture introduced here. The TC0 ceiling result
is a statement about what a fixed-depth Transformer (this design, scaled up) can compute in a single forward pass.

[Llama 3 (2407.21783)](2407.21783v3.md) is the modern industrialized version: same skeleton, replaced positional
encoding (RoPE), replaced norm (RMSNorm pre-norm), replaced FFN (SwiGLU), grouped-query attention (GQA) as a
memory-saving tweak to multi-head, vastly larger N and d_model, and 15T training tokens instead of WMT's ~5M sentence
pairs. It is instructive to read Llama 3 with this paper open and note exactly which knobs got turned.

[LLM in a Flash (2312.11514v3)](2312.11514v3.md) and the mlx-flash / flash-MoE engineering work depend on the
layer-by-layer block structure introduced here. The "stream a layer at a time" trick only makes sense because Vaswani et
al. designed identical, independent stacked blocks.

[Speed and Conversational LLMs (2502.16721v1)](2502.16721v1.md) is a measurement paper about throughput on this
architecture; the verbosity / tokenizer / tok-per-second analysis presupposes the auto-regressive decoder defined in
Section 3.

## Open questions for Dan

1. **Attention-as-implementation-target paper.** Linus will eventually need to run attention efficiently on Metal/ANE.
   Should the corpus include FlashAttention-1/2/3 (Tri Dao) as the canonical "how attention is actually implemented on
   accelerators" reference? The original FlashAttention paper is short and load-bearing for any throughput conversation.
2. **KV cache economics.** Given the M1 Max 32 GB constraint, the KV cache is going to dominate long-context inference
   cost for Linus. Worth a dedicated note on KV-cache memory math (per-layer K and V tensors of shape [batch,
   n_kv_heads, seq_len, d_head] in the chosen dtype) tied to specific Worker models? This is implicit in this paper but
   never spelled out.
3. **Encoder-only relevance.** The KnowledgeBase embedding stack uses encoder-only models (BERT-family). Worth treating
   the encoder half of this paper as the historical root of that stack, and adding a BERT note (1810.04805) explicitly
   to the corpus to close that loop?
4. **Bibliographic hygiene.** This is the canonical citation. Should `docs/glossary.md` or a similar file maintain a "if
   you only read five papers in the Linus corpus, read these" pointer with this one at the top? The corpus is going to
   grow; new readers (future Dan, future Worker fine-tunes trained on this repo) need the orientation.
