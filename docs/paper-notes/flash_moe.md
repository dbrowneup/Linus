---
title: Flash-MoE — Streaming a 397B Parameter Mixture-of-Experts Model from NVMe at 5.7 Tokens/Second on Consumer Hardware
source: tech report (not yet on arXiv as of context download)
authors: Claude Opus 4.6 (primary author), Daniel Woods (research direction & systems engineering)
affiliation: Anthropic; Independent
date: 2026-03 (file dated 2026-03-18)
pdf: ../../context/papers/flash_moe.pdf
tags: [moe, flash-streaming, apple-silicon, metal, m3-max, 397b-model, expert-sparsity, nvme]
---

# Flash-MoE: Streaming a 397B Parameter Mixture-of-Experts Model from NVMe at 5.7 Tokens/Second on Consumer Hardware

## TL;DR
The most extreme demonstration of "larger-than-RAM inference on a Mac" published to date — and the paper directly behind [repos/flash-moe/](../../repos/flash-moe/). A **397-billion-parameter MoE model (Qwen3.5-397B-A17B)** runs on an Apple M3 Max with **48 GB of unified memory at 5.74 tok/s sustained**, by streaming expert weights from a 1 TB NVMe SSD on demand. Combines (a) MoE's natural extreme sparsity (only ~2% of weights active per token), (b) aggressive 2-bit requantization of expert weights (RMSE 0.001–0.003), and (c) a custom Metal/Objective-C compute pipeline with a fused three-command-buffer GPU pipeline. **Notable**: the primary author is Claude Opus 4.6 itself, working under Daniel Woods' direction over a 24-hour collaborative session — this is itself a Maestro/Worker artifact.

## The problem (in plain language)
Mixture-of-Experts models trade *active parameters* for *total parameters*: 397B total weights, 17B active per token, 512 experts per layer of which only 4–10 fire at any moment. So while the storage cost is huge (209 GB at 4-bit, 120 GB at 2-bit), the *compute* per token is small. The mismatch between storage size (huge) and compute size (modest) is the same kind of bandwidth-vs-compute imbalance that "[LLM in a Flash](2312.11514v3.md)" exploited for dense models — but MoE's sparsity is *extreme* (2% active vs LLM-in-a-Flash's 3–10%), so the streaming opportunity is even bigger.

The catch: a 397B model needs ~600 MB of expert weights *per token* delivered fast enough to keep the GPU busy. M3 Max's NVMe does 17.5 GB/s sequential, which on paper is enough — but only if you read in big chunks, only if you don't waste bandwidth on bookkeeping, and only if CPU-GPU synchronization doesn't stall the pipeline. Most of the paper is the engineering to make that paper-thin budget actually work.

## What they propose
A complete inference engine, written from scratch in **Objective-C and Metal Shading Language** (no Python, no MLX, no PyTorch — they tried MLX first and it was too slow). Major components:

**1. Weight organization (5.5 GB resident, 120–209 GB on disk):**
- *Non-expert weights* (embeddings, attention Q/K/V/O, norms, routing gates, shared expert): mmap'd at startup, ~5.5 GB total. These are needed every token.
- *Expert weights*: 60 binary files (one per layer), with 512 experts packed sequentially. Per-expert layout precisely sized so `pread(fd[layer], buf, EXPERT_SIZE, expert_idx * EXPERT_SIZE)` is a single seek-free read.

**2. 2-bit requantization (4-bit → 2-bit for experts only):**
- Original MLX checkpoint is 4-bit affine, group size 64. They re-quantize each group's 64 values to 2-bit affine.
- Critically: the dynamic range *within a 4-bit group* is already compressed (only 16 distinct float values exist), so 2-bit (4 levels) preserves them with RMSE 0.001–0.003.
- 44.5% reduction in expert size (7.08 MB → 3.93 MB), 209 GB → 120 GB total.

**3. Metal compute pipeline (three command buffers per layer):**
- **CMD1 (Attention)**: Q/K/V projections, committed and waited.
- **CMD2 (Post-attention + routing)**: Output projection, residual, RMSNorm, routing gate, shared-expert gate/up projections. Fused.
- **CMD3 (Experts + Combine, deferred)**: Critically, while CMD2 executes, the CPU does softmax on routing logits, picks top-K, and dispatches **parallel `pread()` from SSD** into Metal shared buffers (4 pthreads via `dispatch_apply`). CMD3 is committed but *not waited* — the next layer's CMD1 is submitted immediately. The Metal GPU queue serializes correctly.

**4. Custom Metal kernels:**
- `dequant_matvec_4bit_v3` and `dequant_matvec_2bit`: tiled threadgroup matrix-vector multiply with inline dequantization, SIMD reduction, coalesced uint32 loads.
- `swiglu_fused_vec4`, `weighted_sum`, `rms_norm` — all hand-written.

**5. Counterintuitive cache discovery:**
- Their initial design had a **9.8 GB Metal LRU expert cache** in DRAM. Removing it gave **+38% throughput**. Why? The cache competed for DRAM with the *macOS page cache*, which manages the SSD-resident model file far better than any application-level cache could. *Trust the OS, not the app.*

**6. Linear attention for 75% of layers:**
- Qwen3.5 uses **GatedDeltaNet** (linear-attention variant) for 45 of 60 layers, with full attention only every 4th layer. Linear attention has O(1) per-step compute after warmup, which is what makes the model viable on a laptop GPU at all.

## Key results
- **5.74 tok/s sustained, 7+ tok/s peak** on M3 Max 48 GB. First demonstration of a model >4× DRAM running at interactive speeds on consumer hardware.
- **209 GB → 120 GB at 2-bit**, with 0.001–0.003 RMSE per layer.
- **5.5 GB resident DRAM** (everything except experts).
- **943 MB I/O per token** (240 expert reads × 3.93 MB) — well under the 17.5 GB/s NVMe budget.
- **12× speedup** from the optimization journey (0.47 tok/s with MLX → 5.74 tok/s with custom Metal).
- **Quality verified** across mathematical reasoning, code generation, and scientific explanation — 2-bit experts produce production-quality output indistinguishable from 4-bit.

Scale: Apple M3 Max 48 GB, 1 TB NVMe. Linus' M1 Max 32 GB is ~75% of the unified memory and roughly half the SSD bandwidth (M1 Max ~6 GB/s vs M3 Max 17.5 GB/s) — so the *exact* numbers won't transfer, but the *technique* should scale down.

## What's reusable in Linus
**Direct (this is Linus' inference moonshot):** This paper *is* [repos/flash-moe/](../../repos/flash-moe/). If we want to run a 200B-class MoE model on Linus, this is the path. The 397B → 5.74 tok/s result on M3 Max would translate to roughly 2–3 tok/s on M1 Max with a ~70B–100B MoE model (different architecture, different SSD speed), which is still *interactive* for many uses.

**Direct (architecture lessons that transcend MoE):**
- *Trust the OS page cache; don't build an LRU.* This finding alone might save weeks of engineering across Linus' inference layer.
- *Three-command-buffer fused pipeline with deferred CMD3.* This is the canonical pattern for Metal inference where CPU-side I/O and GPU compute need to overlap. Generalizable beyond MoE.
- *Custom Metal kernels beat MLX by 12×* on this workload. Sobering but useful: don't assume MLX is always the right abstraction; sometimes raw Metal is necessary.

**Indirect (BitNet × MoE):** A natural next-paper-that-doesn't-exist-yet is BitNet-ternary MoE experts. Combining JPmHC-stable hyper-connections + BitNet ternary weights + Flash-MoE streaming would be the holy grail of single-machine inference. Worth flagging as a Linus Phase 8 research direction.

**Meta-relevance (the paper itself is a Maestro/Worker artifact):** Per the abstract, Claude Opus 4.6 is the *primary author*, with Dan Woods directing the research over 24 hours of continuous collaborative sessions. This is exactly the operating model CLAUDE.md describes for Linus. Worth studying not just for the technical content but as an existence proof of what disciplined Maestro-Worker collaboration can produce.

## What's NOT applicable
- **Hardware specifics**: M3 Max NVMe at 17.5 GB/s is 3× M1 Max's 6 GiB/s. Linus' actual numbers will be substantially lower; the technique is what transfers, not the throughput.
- **48 GB unified memory** vs. M1 Max's 32 GB. With 5.5 GB resident, an M1 Max has ~24 GB free for context, KV cache, and other Workers — generous, but tighter.
- **The 397B Qwen3.5 checkpoint** specifically requires the GatedDeltaNet linear-attention architecture. Not all MoE models will work; you need linear attention for 75% of layers to make compute fit.
- **Custom Objective-C and Metal**: writing this from scratch is a major engineering investment. Better to consume [repos/flash-moe/](../../repos/flash-moe/) than to reimplement.

## Connections
- **Direct heir of**: [LLM in a Flash](2312.11514v3.md) — same flash-streaming + sparsity philosophy, scaled up via MoE's 2% activation rate and 3× faster NVMe.
- **Companion to**: [repos/flash-moe/](../../repos/flash-moe/) (the codebase) and [repos/mlx-flash/](../../repos/mlx-flash/) (MLX-based dense streaming).
- **Synergistic with the BitNet papers**: BitNet ternary experts + Flash-MoE streaming is a natural Phase 8 research direction.
- **Linus phase**: Phase 6 (large fine-tuned models), Phase 7 (skill graduation), Phase 8 (beyond MacBook — the techniques here scale up to Mac Studio / Vision Pro hardware).

## Open questions for Dan
1. **Highest-impact concrete next step**: do you want me to scope a Phase 1 spike that runs the *existing* [repos/flash-moe/](../../repos/flash-moe/) code on the M1 Max with a smaller MoE checkpoint (Mixtral-8×7B or DeepSeek-V2-Lite) to validate the technique works on our hardware? This would directly test "can Linus host 80B-class MoE models" — a Phase 6/7 question made concrete in Phase 1.
2. The paper is Claude-as-primary-author. That's an existence proof for the Maestro/Worker model that Linus is built around. Worth a `docs/maestro-worker-flash-moe-case-study.md` companion writeup analyzing the collaboration dynamics? Or is that too meta?
3. Combining BitNet experts with Flash-MoE streaming would push the memory/quality frontier further. Realistic Phase 8 direction, or premature?
