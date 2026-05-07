---
title: "Ternary Bonsai 8B: Ternary (1.58-bit) language models at 8B, 4B, and 1.7B scale"
source: PrismML whitepaper (Bonsai-demo repository)
authors: PrismML (Prism ML Engineering team)
affiliation: PrismML
date: 2026-04-16
pdf: ../../context/papers/bonsai-ternary-8b-whitepaper.pdf
tags:
  [
    ternary,
    1.58-bit,
    mlx,
    apple-silicon,
    prismml,
    low-bit-llm,
    bonsai,
    qwen3,
    quantization,
    post-training-quantization,
    on-device,
  ]
---

# Ternary Bonsai 8B: Ternary (1.58-bit) language models at 8B, 4B, and 1.7B scale

## TL;DR

PrismML's follow-up to 1-bit Bonsai. Same recipe, same Qwen3 base, but the weight alphabet expands from binary {-1, +1}
to ternary {-1, 0, +1} with a shared FP16 scale per group of 128 weights — structurally the BitNet b1.58 representation,
applied as a post-training-style quantization to off-the-shelf Qwen3-8B/4B/1.7B and shipped as MLX checkpoints under
Apache 2.0. Ternary Bonsai 8B lands at **75.5 average benchmark score in 1.75 GB**, recovering 95% of the 79.3-point
FP16 Qwen3-8B baseline at 9.36x smaller footprint, and adding 5.0 points over 1-bit Bonsai 8B at the cost of 0.6 GB.
Throughput numbers (83 tok/s decode, 5.2x speedup over FP16 on M4 Pro; 27 tok/s on iPhone 17 Pro Max) come from the
**2-bit MLX kernel deployment path** because MLX has no native ternary kernel yet — on-disk is 1.75 GB but in-memory is
2.16 GiB, and the speed numbers are what 2-bit kernels get you, not what true 1.58-bit would. For Linus this is the
first credibly capable 8B-class checkpoint that runs natively on Apple Silicon at sub-2-GB and ships in MLX format
today, and the strongest candidate for the Phase 1c BitNet-class Worker baseline on M1 Max.

## The problem (in plain language)

1-bit Bonsai showed Qwen3 can be squeezed into binary weights with surprisingly modest loss — but the loss was still
material (79.3 → 70.5 at 8B, ~9 points). Binary weights are denser than necessary in one specific sense: every weight is
forced to take a side, even when the right answer is "this connection doesn't matter." The standard fix — and the BitNet
b1.58 contribution — is ternary {-1, 0, +1}. The zero state improves expressivity and acts as a structured-sparsity
signal. Information content is log2(3) ≈ 1.585 bits/weight; with an FP16 scale per 128-element group, effective rate is
1.71 bits/weight and idealized compression vs FP16 is 9.4x. The empirical question PrismML answers is how much quality
the zero state buys at what footprint cost, across three scales.

## What they propose

Architecturally, Ternary Bonsai is identical to 1-bit Bonsai with one substitution. Base models are unchanged — dense
decoder-only Qwen3 with GQA (32 query / 8 KV heads), SwiGLU MLPs, RoPE, RMSNorm, 65,536-token context. Embeddings,
attention projections, MLP projections, and LM head are quantized; norms and scale metadata stay in FP16.

Weight format is ternary g128: each weight in {-1, 0, +1}, with one shared FP16 scale per group of 128 weights along the
matrix axis. Dequantized weight is w_i = s_g · t_i. This is structurally the BitNet b1.58 scheme, applied as a
quantization of pre-trained Qwen3 rather than a from-scratch BitNet pretraining run. The whitepaper does not describe
the quantization recipe in detail; it cites the 1-bit Bonsai paper for the framework, with the strong implication of
calibration-based PTQ plus light recovery training, not multi-trillion-token pretraining.

Three checkpoints are released: 8B (8.19B params, 36 blocks, 1.75 GB ternary), 4B (0.86 GB), 1.7B (0.37 GB). All ship as
MLX weights with Python and Swift bindings. License is Apache 2.0 including weights — friendly for everything Linus
needs.

The crucial deployment caveat (§2.2-2.3): **MLX has no efficient native ternary kernel**, so the deployed model uses
MLX's 2-bit kernel path. Footprint and throughput numbers reflect that, not theoretical 1.58-bit. This is the gap a
community contribution (or pmetal) could close.

## Key results

**Headline (8B-scale, six-benchmark average — MMLU-Redux / MuSR / GSM8K / HumanEval+ / IFEval / BFCLv3):**

| Model             | Size     | Avg  | Notes                         |
| ----------------- | -------- | ---- | ----------------------------- |
| Qwen3 8B (FP16)   | 16.38 GB | 79.3 | full-precision baseline       |
| Ternary Bonsai 8B | 1.75 GB  | 75.5 | -3.8 points, 9.36x smaller    |
| 1-bit Bonsai 8B   | 1.15 GB  | 70.5 | -8.8 vs FP16, -5.0 vs ternary |
| Llama 3.1 8B      | 16.06 GB | 67.1 | reference                     |
| GLM 4 9B          | 18.80 GB | 65.7 | reference                     |

Ternary Bonsai 8B beats every conventional 7-9B model in the comparison table except Qwen3-8B itself. The 5-point gain
over 1-bit Bonsai 8B for an extra 0.6 GB is the central empirical claim of the paper.

**Throughput on Apple Silicon (M4 Pro 48 GB, MLX Python, 2-bit deployment path):**

- 8B: 83 tok/s decode, 434 tok/s prefill, 5.2x vs FP16
- 4B: 133 tok/s decode, 728 tok/s prefill, 4.8x vs FP16
- 1.7B: 235 tok/s decode, 1585 tok/s prefill, 3.8x vs FP16

**iPhone 17 Pro Max (MLX Swift):** 8B at 27 tok/s decode, 1.9x over a 4-bit baseline.

**Energy (M4 Pro):** 0.105 mWh/token for 8B vs 0.415 mWh/token FP16 — 4x reduction. On iPhone, the ternary 8B (running
through 2-bit kernels) is actually 1.9x _more_ expensive per token than the 1-bit Bonsai 8B — the paper attributes this
to the 2-bit kernel deployment path, and explicitly notes native ternary kernels would close the gap.

**Intelligence density** (their −log(P_e)/GB metric): Ternary Bonsai dominates the 1.2B-9B band of conventional models
by a wide margin at every scale; vs 1-bit Bonsai, ternary trades some density for materially higher absolute scores. The
1.7B ternary checkpoint at 0.37 GB and 58.5 avg is striking — comparable to Qwen3 1.7B at 9x the footprint.

## Ternary vs binary: explicit trade-off

The whole paper is an empirical sweep on this single design knob. Everything else (base model, group size, quantized
layers, recipe) is held constant:

- **Memory:** +0.13 bits/weight vs binary; practically, 1.75 GB vs 1.15 GB at 8B (+0.60 GB, +52%).
- **Quality:** ternary gains 5.0 average points at 8B (75.5 vs 70.5), 7.4 at 4B (70.7 vs 62.7), 7.9 at 1.7B (58.5 vs
  49.6). The smaller the model, the more the zero state helps — consistent with smaller models being less able to afford
  bits on connections that should be off.
- **Throughput:** roughly comparable; both currently route through MLX 2-bit kernels.
- **Sparsity:** the paper does not report what fraction of ternary weights end up at zero. The obvious follow-up — if
  it's 30-50% (as in BitNet b1.58), a kernel that exploits actual zeros (rather than encoding them as 2-bit values) is a
  serious throughput opportunity.

At the 8B scale Linus most likely deploys, ternary at 1.75 GB beats binary at 1.15 GB by enough margin (95% vs 89% of
FP16) that ternary is the right default. Binary remains the choice when 0.6 GB matters — phone, KV-cache-heavy contexts,
or many concurrent Workers in unified memory.

## Relationship to BitNet b1.58

Ternary Bonsai is structurally the BitNet b1.58 weight scheme (per
[The Era of 1-bit LLMs (2402.17764v1)](2402.17764v1.md)) applied to Qwen3 as post-training quantization, not a
from-scratch BitNet pretraining. References [6] and [7] explicitly cite b1.58 and the original BitNet — lineage
acknowledged.

Functionally this answers a question Microsoft's BitNet team has not answered publicly: there is no released BitNet
b1.58 8B. The largest released BitNet model is 2B4T (see [BitNet b1.58 2B4T (2504.12285v2)](2504.12285v2.md)). Ternary
Bonsai 8B fills that gap — in practice, the first openly released and benchmarked **native-ternary 8B checkpoint**
available for download. Whether it counts as "BitNet b1.58 8B" is a labeling question; mechanically, in inference, it
is.

The distinction that matters for Dan: a from-scratch BitNet 8B would in principle be cleaner — weights trained to live
in {-1, 0, +1} from step zero. Ternary Bonsai is Qwen3 **squeezed into** {-1, 0, +1} after the fact, and the 5% gap vs
FP16 Qwen3 is the price of that squeeze. From-scratch BitNet 8B might recover some of it (BitDistill,
[2510.13998v1](2510.13998v1.md), is the contemporary distillation attempt). For now, Ternary Bonsai 8B is what you can
download today and run in MLX today.

## What's reusable in Linus

**Phase 1c (BitNet spike) — primary recommendation:** Ternary Bonsai 8B should be the headline checkpoint for the spike,
alongside (not instead of) BitNet b1.58 2B4T. The spike question is "can a low-bit model be a credible Worker on M1
Max?" — and 8B at 1.75 GB / 2.16 GiB resident is the most ambitious credible answer. Comparing 2B4T (true native
ternary, smaller) vs Ternary Bonsai 8B (PTQ ternary, larger) on Dan's task suite is the right A/B. Also benchmark
Ternary Bonsai 4B as the middle-ground option that fits alongside KV cache, embeddings, and a second concurrent Worker.

**Phase 1c — measure the deployment-path tax:** the 5.2x speedup is via 2-bit kernels. Report tok/s, watts, footprint
for the as-shipped path, and flag the gap to a hypothetical native 1.58-bit kernel. This connects to the pmetal
evaluation: "implement a real ternary kernel" is a tractable pmetal contribution that would benefit Bonsai users
immediately.

**Phase 2 (MVP) — interim 1-bit serving lane:** CLAUDE.md and total-landscape.md flag Bonsai as the interim 1-bit
serving lane while pmetal matures. Ternary Bonsai 8B is more useful as a Worker than 1-bit Bonsai 8B — the 5-point gain
matters for code/tool-calling, where 1-bit's 65.7 IFEval / 65.7 BFCLv3 are mediocre and ternary's 81.8 / 73.9 are
competitive. Default to ternary; offer 1-bit as opt-in for footprint-critical paths.

**Phase 6 (Fine-Tuning):** Bonsai's recipe — Qwen3 base + group-128 ternary + FP16 scales — is a candidate target format
for the first Linus-branded checkpoint. Natural sequence: LoRA on Qwen3-8B for Dan's biochem/genomics/Python corpus →
distill into the Bonsai ternary format.

**Phase 6d (streaming target):** the ROADMAP's "ternary 8B" stretch goal is now concrete. Ternary Bonsai 8B at 1.75 GB
fits trivially in unified memory with no streaming — but the same recipe at 70B (if PrismML scales it) is exactly the
larger-than-RAM regime that [LLM in a Flash (2312.11514v3)](2312.11514v3.md) and [flash-moe](flash_moe.md) target. Worth
tracking PrismML's release cadence.

**Phase 8 (BitNet × Flash-MoE × JPmHC speculation):** a 1.75-GB strong 8B accelerates the speculative timeline
meaningfully. Eight Ternary Bonsai 8B Workers in parallel consume ~14 GB of weights, leaving ~18 GB for KV caches and
orchestration — a fan-out that wasn't credible at FP16 even with 4-bit quantization.

**Eval methodology:** PrismML uses a six-benchmark average (MMLU-Redux, MuSR, GSM8K, HumanEval+, IFEval, BFCLv3) plus
four extras under EvalScope with vLLM on H100. `benchmarks/dan_tasks/` should mirror the six-benchmark set when
comparing to Bonsai claims, and pair tok/s with the wall-clock task-completion methodology from
[Speed and Conversational LLMs (2502.16721v1)](2502.16721v1.md).

## What's NOT applicable

Throughput and energy numbers are from M4 Pro 48 GB, not M1 Max 32 GB. Relative speedup vs FP16 (5.2x decode) likely
transfers reasonably — both are unified-memory Apple Silicon — but absolute throughput on M1 Max will be lower (smaller
GPU, lower bandwidth) and energy-per-token won't transfer. Linus must run its own measurements.

iPhone 17 Pro Max numbers are interesting context but not directly actionable for a desktop-class system. They do
confirm the same MLX checkpoints run on iOS — relevant for Phase 8 mobile.

Benchmarks were run on H100 via vLLM, not Apple Silicon via MLX. Standard methodology for cross-model comparability, but
no guarantee the MLX 2-bit-kernel deployment exhibits identical scores. Worth a sanity check in Phase 1c: re-run two or
three benchmarks on the released MLX checkpoint and confirm no silent degradation.

The whitepaper does not describe the quantization training recipe in reproducible detail; if Linus wants to
ternary-quantize a custom-fine-tuned Qwen3 (Phase 6), the Bonsai-demo repo and the 1-bit Bonsai paper are needed, with
substantial gap-filling.

The paper does not report sparsity statistics (what fraction of ternary weights are zero) — the most directly useful
number for sizing kernel-optimization opportunities. Worth raising with PrismML or measuring directly.

## Connections

Closest sibling: **[1-bit Bonsai 8B (bonsai-1-bit-8b-whitepaper.md)](bonsai-1-bit-8b-whitepaper.md)** — same authors,
same base model family, same release pipeline; this paper _is_ the follow-up and treats the 1-bit paper as its baseline
and reference for methodology details.

The full ternary/1-bit thread:

- **[BitNet (2310.11453v1)](2310.11453v1.md)** — the original 1-bit Transformer scheme.
- **[BitNet b1.58 (2402.17764v1)](2402.17764v1.md)** — the canonical ternary architecture; Ternary Bonsai's weight
  format is structurally identical.
- **[BitNet a4.8 (2411.04965v1)](2411.04965v1.md)** — 4-bit activations for 1-bit weights; orthogonal optimization that
  could apply to Bonsai.
- **[BitNet v2 (2504.18415v2)](2504.18415v2.md)** — newer Microsoft iteration.
- **[BitNet b1.58 2B4T (2504.12285v2)](2504.12285v2.md)** — the released BitNet checkpoint; Ternary Bonsai 8B is the
  larger scale point that the BitNet team has not yet published.
- **[bitnet.cpp (2502.11880v1)](2502.11880v1.md)** — CPU inference for BitNet; the Apple Silicon counterpart is what
  Bonsai + MLX (and eventually pmetal) provide.
- **[BitDistill (2510.13998v1)](2510.13998v1.md)** — distilling FP models into ternary; conceptually adjacent to
  whatever recipe PrismML is using.

Streaming and efficiency: **[LLM in a Flash (2312.11514v3)](2312.11514v3.md)** and **[flash-moe](flash_moe.md)** —
relevant if a future Bonsai release scales beyond the unified memory budget.

Evaluation methodology: **[Speed and Conversational LLMs (2502.16721v1)](2502.16721v1.md)** — Bonsai's tok/s claims
should be paired with task-completion-time measurement on Dan's actual workload before Worker selection.

Repo/code: `repos/Bonsai-demo/` is the local clone of the PrismML release with both 1-bit and ternary checkpoints.
`repos/mlx-flash/` is the streaming-inference reference. A future pmetal contribution implementing native ternary
kernels would close the deployment-path gap noted in §2.3.

## Open questions for Dan

1. **Sparsity probe:** worth a 30-minute experiment on the released checkpoint to measure the actual fraction of ternary
   weights that are zero. This number tells us how much a real ternary kernel would beat the 2-bit deployment path,
   which scopes the potential pmetal contribution.
2. **MLX-vs-vLLM score sanity check:** the published 75.5 average is from vLLM/H100. Spot-check IFEval and HumanEval+ on
   the MLX-deployed Apple Silicon version to confirm the deployment path does not silently degrade quality.
3. **Phase 6 target format:** is "fine-tune Qwen3-8B on Dan corpus, then ternary-quantize Bonsai-style" the canonical
   roadmap for the first Linus-branded checkpoint, or do we wait for native pmetal training paths first?
4. **Worker count budgeting:** at 2.16 GiB resident per 8B Bonsai instance, the M1 Max can comfortably hold 4-6
   concurrent Workers plus orchestration, KV caches, and Qdrant/Kiwix overhead. Does this change the orchestration-layer
   router design — is parallel agent fan-out a Phase 2 concern rather than Phase 3?
