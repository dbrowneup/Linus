---
title: "1-bit Bonsai 8B: End-to-end 1-bit language model deployment across Apple, GPU, and mobile runtimes"
source: PrismML whitepaper (Bonsai family release)
authors: PrismML (corporate authorship; underlying compression method credited to Caltech intellectual property)
affiliation: PrismML
date: 2026-03-31
pdf: ../../context/papers/bonsai-1-bit-8b-whitepaper.pdf
tags:
  [
    1-bit,
    mlx,
    apple-silicon,
    prismml,
    low-bit-llm,
    bonsai,
    native-low-bit,
    qwen3,
    llama-cpp,
    metal,
    on-device-inference,
    intelligence-density,
  ]
---

# 1-bit Bonsai 8B: End-to-end 1-bit language model deployment across Apple, GPU, and mobile runtimes

## TL;DR

PrismML releases a family of true end-to-end 1-bit weight LLMs (1.7B, 4B, 8B) built by compressing Qwen3 backbones into
a custom group-wise 1-bit format (`Q1_0_g128` in GGUF, the equivalent 1-bit g128 in MLX). The 8B model lands at **1.15
GB on disk** (vs 16.38 GB FP16, a 14.2× reduction), retains a benchmark average of 70.5 across knowledge / reasoning /
math / coding / IF / tool-calling — within striking distance of full-precision Qwen3-8B (79.3) and ahead of Llama-3.1-8B
(67.1), Hermes-3-8B (65.4), and DeepSeek-R1-Qwen-7B (55.0) — and ships with custom kernels for **MLX (Python and Swift),
Metal via llama.cpp, and CUDA via llama.cpp**. On an M4 Pro 48 GB it generates at 131 tok/s via MLX (Python) vs ~16
tok/s for the FP16 baseline, an ~8× generation speedup; on iPhone 17 Pro Max it runs at 44 tok/s. Crucially, 1-bit
precision is applied **end-to-end** — embeddings, attention projections, MLP projections, and the LM head — with no FP16
escape hatches. For Linus, this is arguably the single most operationally relevant paper in the corpus for Phase 1c: an
8B-class native-low-bit Worker that already has shipping MLX kernels.

## The problem (in plain language)

Inference dominates the real-world economics of LLMs. On edge hardware (laptops, phones) the binding constraint at small
batch sizes is not arithmetic throughput but **memory bandwidth** — the cost of streaming the full weight tensor across
the bus for every generated token. If you can shrink the weights, generation gets faster more or less for free, and
energy per token drops with it.

The appeal of 1-bit weights is decades old, but the regime below ~4-bit has been historically brittle. Models stay
fluent while quietly losing reliability on multi-step reasoning, tool use, and edge cases — exactly the behaviors that
make a Worker useful in an orchestration layer. Worse, most prior near-1-bit approaches required custom calibration
sets, auxiliary metadata, or bespoke runtimes that did not integrate with mainstream stacks (`llama.cpp`, MLX). That
friction has kept 1-bit out of practical deployment. PrismML positions Bonsai as the first 1-bit LLM family that is both
**principled** (Caltech IP for the compression math) and **operationally deployable** (custom kernels for the runtimes
people actually use).

## What they propose

The architecture is unchanged from Qwen3-8B: dense decoder-only transformer, GQA (32 query / 8 KV heads), SwiGLU MLPs,
RoPE, RMSNorm, 36 blocks, 65,536-token context. The novelty is entirely in the compression and the deployment stack.

**The format — `Q1_0_g128`.** Each weight is stored as one sign bit. A single FP16 scale is shared across each group of
128 weights. Effective weight is `w_i = s_g · (2·b_i − 1)` with `b_i ∈ {0,1}`. Effective storage cost is
`1 + 16/128 = 1.125 bits/weight`, giving an idealized 14.2× compression vs FP16 before alignment overhead. The format is
applied **uniformly** across embeddings, attention projections, MLP projections, and the LM head — there is no
high-precision residual path. Norms and scale metadata stay in higher precision, but those tensors are negligible
against weight bandwidth during decoding.

**MLX caveat.** MLX's quantization API requires both a scale and a bias per group, so PrismML re-encodes their
scale-only format as `s_mlx = 2·s_g`, `b_mlx = −s_g`. This burns one extra FP16 per group, pushing MLX storage to **1.25
bits/weight** vs GGUF's 1.125. They explicitly call this out as an MLX limitation; if MLX adds scale-only quant support,
MLX builds will match GGUF. Worth flagging because it directly affects which runtime to prefer on Apple silicon.

**Kernels.** The format requires custom inference support on every backend, since neither llama.cpp nor MLX natively
understands `Q1_0_g128`. PrismML maintains forks of (a) `llama.cpp` with custom CUDA and Metal kernels
(`PrismML-Eng/llama.cpp`), (b) Apple's `mlx` framework (`PrismML-Eng/mlx`), and (c) Apple's `mlx-swift` framework for
iOS (`PrismML-Eng/mlx-swift`). Sign bits are decoded inline inside the matmul kernel rather than materializing FP16
weights — the bandwidth advantage actually reaches the silicon.

**Training.** The whitepaper is thin here. The compression is described as "proprietary Caltech intellectual property";
no recipe is published. The base is explicitly Qwen3-8B, so this is **post-training compression of a pretrained
backbone**, not from-scratch 1-bit pretraining (the BitNet b1.58 path). Bonsai gives you a deployable 1-bit Worker
today; it does not give you a recipe for training one yourself.

## Key results

**Storage (Table 2).** FP16 safetensors: 16.38 GB. GGUF Q1_0_g128: 1.15 GB (14.2×). MLX 1-bit g128: 1.28 GB (12.8×).

**Throughput (Table 3, the headline numbers for Linus).** On **M4 Pro 48 GB**, MLX (Python) generates at 131 tok/s for
the 1-bit model vs 16 tok/s for the FP16 baseline (~8× on this generation). llama.cpp Metal on the same M4 Pro hits 85
tok/s vs 16 tok/s baseline (5.4×). On iPhone 17 Pro Max, MLX Swift delivers 44 tok/s — and the FP16 baseline simply does
not fit, so the comparison is against a 4-bit version (3.2×). On RTX 4090 with CUDA, 368 tok/s vs 59 tok/s (6.2×).
Prompt processing (PP512) gains are much smaller (~1.0–1.1× per Appendix A), as expected — prompt processing is
compute-bound, not bandwidth-bound.

**Energy (Table 4).** On Mac M4 Pro via MLX: 0.074 mWh/token vs 0.415 mWh/token FP16, a **5.6× reduction**. Metal path:
5.1×. RTX 4090: 4.1×. iPhone: ~2.1× over the 4-bit baseline. Notably, instantaneous power draw is _not_ always lower for
1-bit — inline dequantization shifts execution toward a more compute-intensive regime — but tokens come out fast enough
that energy per token still drops by 4–6×.

**Quality (Tables 5 and 7).** Six-skill average (MMLU-Redux, MuSR, GSM8K, HumanEval+, IFEval, BFCLv3) for 1-bit Bonsai
8B is **70.5**, vs Qwen3-8B at 79.3 (FP16 ceiling), Olmo-3-7B at 70.9, Llama-3.1-8B at 67.1, GLM-4-9B at 65.7,
DeepSeek-R1-Qwen-7B at 55.0. Per-benchmark: MMLU-Redux 65.7, MuSR 50.0, GSM8K 88.0, HumanEval+ 73.8, IFEval 79.8, BFCLv3
65.7. About 9 average points lost to its FP16 ancestor while shrinking 14×; competitive with most other full-precision
8B instruct models.

**Intelligence density (Table 6).** PrismML defines `D = -log(P_e)/N` where `P_e = 1 - score/100` and N is GB, by
analogy to error exponents in coding theory. Bonsai 1.7B / 4B / 8B occupy the top three slots in their 22-model
comparison by a wide margin. The metric is self-serving but the underlying claim survives reasonable alternative
definitions.

**Evaluation discipline (Appendix B).** Identical infrastructure (vLLM 0.15.1 on H100, EvalScope 1.4.2), greedy
decoding, deterministic execution (`VLLM_BATCH_INVARIANT=1`, `FLASH_ATTN`), no per-model prompt engineering, code
benchmarks in `python:3.11-slim` Docker sandboxes, rule-based scoring with Gemini 2.5 Flash Lite as recall fallback only
on extraction failure. Unusually careful for a corporate whitepaper.

## What's reusable in Linus

**Direct, Phase 1c (the BitNet spike, immediately).** Phase 1c is scoped to benchmark BitNet b1.58 2B4T on M1 Max as the
first native-low-bit Worker spike. Bonsai 1-bit 8B **changes the spike**: it adds an 8B-class model with shipping MLX
kernels and Apache-licensed weights. The spike should benchmark both side-by-side on M1 Max — same prompt set, same
task-completion methodology from `2502.16721v1.md` — reporting (a) tok/s on tg128 and pp512, (b) wall-clock
task-completion time on dan_tasks, (c) memory footprint and peak RSS, (d) energy per token where measurable, (e) quality
on a subset of PrismML's benchmarks (at minimum MMLU-Redux, HumanEval+, BFCLv3) to sanity-check the published 70.5
average locally.

**Direct, Phase 1c (`repos/Bonsai-demo`).** Added as an interim 1-bit serving option while pmetal is evaluated. The
whitepaper promotes it from curiosity to deployment surface for a model that — if benchmarks reproduce — could be the
**default Linus Worker** for general tasks. Worth confirming whether the demo uses the PrismML MLX fork or pulls
binaries; that determines whether Linus must vendor a second MLX install alongside whatever pmetal eventually requires.

**Direct, Phase 2 (MVP).** A 1.15 GB Worker at 131 tok/s on M4 Pro (presumably comparable on M1 Max — similar bandwidth
class) means Linus can plausibly run **multiple parallel Workers** in 32 GB without crowding out KnowledgeBase / Qdrant
/ IDE. Even at 4 GB peak per instance, four parallel Bonsai-8B Workers fit in 16 GB. The orchestration layer's parallel
fan-out story gets dramatically more credible with a Worker this small.

**Direct, Phase 6 (Fine-tuning) — with caveat.** No published compression recipe means Bonsai is **not** a path to a
Dan-specific 1-bit Linus model from a domain corpus; that path remains BitNet b1.58 (`2402.17764v1.md`) from-scratch or
BitDistill (`2510.13998v1.md`) for FP16→ternary distillation. What Bonsai enables is **using** a strong 1-bit Worker as
a distillation target or as a baseline any Linus-trained model must beat. If a Bonsai LoRA recipe ever lands, an
8B-class native-low-bit fine-tunable Worker on M1 Max becomes a workflow Dan otherwise couldn't have.

**Direct, Phase 6d (streaming / mlx-flash).** With Bonsai 8B at 1.15 GB resident, `mlx-flash`-style streaming is
unnecessary at the 8B class — the whole model fits comfortably. Streaming re-emerges only at 30B+ or for serving
multiple distinct 8B+ models without swapping. Useful Phase 6d scoping result.

**Indirect, evaluation methodology.** Appendix B is a template for how Linus should run benchmark sweeps: locked dataset
revisions, deterministic attention, identical generation parameters across models, no per-model prompt tuning, sandbox
code execution, rule-based scoring with LLM fallback only on extraction failure. `benchmarks/dan_tasks/` should adopt
this from the start.

## What's NOT applicable

Headline throughput numbers are reported on **M4 Pro, not M1 Max**. Bandwidth differs (M4 Pro ~273 GB/s vs M1 Max ~400
GB/s); the 1-bit kernel is bandwidth-bound, so M1 Max may actually be faster — but published numbers do not transfer
directly. Must measure.

The compression recipe is closed. No published path from "FP16 model X" to "1-bit Bonsai-format X"; only released
Qwen3-derived checkpoints. Linus cannot use Bonsai to compress, e.g., a domain-fine-tuned Qwen3-8B variant.

The MLX runtime requires the **PrismML fork**, not stock MLX — a maintenance liability. If pmetal becomes the inference
layer, integrating PrismML's Metal kernels is non-trivial.

The benchmark comparison excludes the BitNet family entirely. PrismML compares against full-precision 6–9B models only.
A direct Bonsai-1-bit vs BitNet-ternary head-to-head is on us.

The "intelligence density" metric is novel and unvalidated outside this paper. Useful framing, cite cautiously.

The roadmap promises future Bonsai variants at other bit widths and non-transformer backbones with no dates. Treat as
forward-looking.

## Connections

This paper sits at the center of the Linus **native-low-bit / efficient-inference** thread:

- **BitNet originals.** [BitNet (2310.11453v1)](2310.11453v1.md) and [BitNet b1.58 (2402.17764v1)](2402.17764v1.md) are
  the from-scratch ternary alternative. Complementary, not competitive: BitNet teaches you to _train_ low-bit; Bonsai
  gives you a deployable low-bit Qwen3-8B today.
- **BitNet release timeline.** [a4.8 (2411.04965v1)](2411.04965v1.md), [v2 (2504.18415v2)](2504.18415v2.md), and
  [b1.58 2B4T (2504.12285v2)](2504.12285v2.md) are Phase 1c spike targets. Bonsai joins as the 8B sibling.
- **bitnet.cpp ([2502.11880v1](2502.11880v1.md)).** PrismML's `llama.cpp`-Metal/CUDA kernel work is the architectural
  twin; Bonsai extends to GPU and Metal explicitly.
- **BitDistill ([2510.13998v1](2510.13998v1.md)).** Distillation path that could fill the gap Bonsai's closed recipe
  leaves open.
- **LLM in a Flash ([2312.11514v3](2312.11514v3.md)) and `flash-moe`.** Motivate streaming for larger-than-RAM. Bonsai
  8B at 1.15 GB makes streaming unnecessary at 8B — useful Phase 6d scoping.
- **Speed and LLMs ([2502.16721v1](2502.16721v1.md)).** Provides task-completion-time methodology that should sit
  underneath any Bonsai vs BitNet vs FP16 comparison.
- **Sister Bonsai-ternary whitepaper** (same batch). The 1-bit-vs-ternary distinction is real: 1-bit uses {−1,+1} with
  group-wise FP16 scales; ternary uses {−1,0,+1}. Ternary's zero is a free sparsity prior; 1-bit lacks it but compresses
  harder. Which wins on Dan's hardware is an empirical question for the Phase 1c spike.

The local artifacts make this concrete: `repos/Bonsai-demo` is the deployment surface, `repos/mlx-flash` is the
streaming alternative this paper makes less urgent, and `pmetal` is the longer-term native runtime where PrismML's
kernel work would eventually need to be ported or integrated.

## Open questions for Dan

1. **Phase 1c scope expansion.** Should the BitNet spike formally expand to a "1-bit / native-low-bit shootout" — BitNet
   b1.58 2B4T, Bonsai 1-bit 1.7B / 4B / 8B, the upcoming Bonsai-ternary variant, all benchmarked on M1 Max with the
   `dan_tasks` suite and the task-completion-time methodology? That's the natural scope given what just landed; worth
   confirming before the spike spec is written.
2. **`Bonsai-demo` integration path.** Does the demo wrap PrismML's MLX fork, llama.cpp Metal, or both? The answer
   determines whether Linus needs to vendor and track a forked MLX install, or can run Bonsai through stock llama.cpp +
   Metal kernels. The maintenance cost differs significantly.
3. **Default-Worker decision criteria.** If Bonsai 1-bit 8B reproduces ~70 average benchmark and ~100+ tok/s on M1 Max
   with ~1.5 GB peak RSS, does it become the **default Linus Worker** for general tasks, displacing Qwen2.5-Coder for
   non-code work? What benchmark margin or quality threshold would trigger that switch?
4. **Quality-floor probe.** PrismML's published average is 70.5; Qwen3-8B at FP16 is 79.3. Nine points is a lot or a
   little depending on the task. Is it worth a small targeted eval — say, 30 of Dan's actual scientific-Q&A and
   code-review prompts side-by-side between Bonsai-1bit-8B and a comparable FP16 7–8B — before committing Bonsai as a
   default? That would catch a "fluent but unreliable" failure mode the standard benchmarks would miss.
5. **Compression-recipe watch.** If PrismML or the community ever publishes the Bonsai compression method, a
   domain-tuned Qwen3-8B → 1-bit Bonsai-format Linus model becomes plausible. Worth an explicit watch item, separate
   from the BitNet from-scratch path?
6. **MLX fork strategy.** Long-term, does Linus pin to PrismML's MLX fork, contribute upstream support for scale-only
   quant formats (which would let MLX match GGUF's 1.125 bits/weight), or wait for pmetal to subsume both? The fork is a
   real maintenance liability and the question deserves an ADR before the inference layer hardens.

---

**Suggested group: NEW: I — Native low-bit / efficient inference (Apple Silicon)**

Justification: this paper, the seven existing BitNet thread notes (`2310.11453v1`, `2402.17764v1`, `2411.04965v1`,
`2504.18415v2`, `2504.12285v2`, `2502.11880v1`, `2510.13998v1`), the forthcoming Bonsai-ternary whitepaper, and arguably
[LLM in a Flash (2312.11514v3)](2312.11514v3.md) form a coherent operational thread: the combined
research-and-engineering question of **how to run capable LLMs efficiently on Apple Silicon under 32 GB unified
memory**. They predate the eight numbered triage groups but together constitute the most internally-coherent thread in
the corpus and are the most directly relevant to Phase 1c, Phase 2 Worker selection, and Phase 6d streaming-or-not
scoping. Naming the group "I — Native low-bit / efficient inference (Apple Silicon)" foregrounds the hardware target
(which is what makes these papers cohere for _Linus specifically_, vs. low-bit research in general). Bonsai 1-bit 8B is
the new center of gravity for this group: it's the largest, most operationally deployable, and most MLX-native member.
