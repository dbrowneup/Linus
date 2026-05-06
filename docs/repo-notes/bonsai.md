# Bonsai-demo (`PrismML-Eng/Bonsai-demo`)

## 1. Purpose and scope

Bonsai is a family of 1-bit and 1.58-bit (ternary) quantized language models trained by PrismML, available in 8B, 4B,
and 1.7B parameter sizes. The demo repository provides turnkey setup scripts and integration guides for running Bonsai
on macOS (Metal), Linux (CUDA/Vulkan/ROCm), and CPU. For Linus on M1 Max, Bonsai is the canonical alternative to
native-precision models: 8-10x smaller on disk, native MLX support, sub-millisecond latency, and acceptable accuracy
for many tasks where a 7-8B 1-bit model suffices. This is the reference implementation of "small, quantized, in-RAM"
inference — complementary to mlx-flash's "large, native-precision, streamed" path.

## 2. Architecture summary

Bonsai uses PrismML's quantization scheme: weights are stored as Q1_0 (1-bit) or Q2_0 (ternary) in either GGUF (llama.cpp)
or MLX native formats. The demo repo provides setup scripts (bash/PowerShell) that download pre-built binaries (llama.cpp
or MLX), fetch the appropriate model from Hugging Face, and expose a chat interface. MLX backend uses Metal-accelerated
inference via native Q1_0/Q2_0 kernels (some in-progress upstream PRs; PrismML-Eng fork carries the full suite). Model
sizes range 1.7B to 8B; the whitepaper claims the 8B variant matches Llama-2-13B in accuracy on multiple benchmarks
despite being 85% smaller. KV cache is standard FP16; no hybrid offloading (unlike mlx-flash).

## 3. What's reusable in Linus

Direct integration path: `pip install` MLX-format Bonsai weights. Bonsai-8B-mlx-1bit weighs ~1.2 GB (vs.
Qwen2.5-7B ~15 GB native), fits in RAM with room to spare, and supports the full Linus inference API (generate, chat).
For Phase 1 baselines, running Dan's task suite on Bonsai-8B gives a concrete "small model, fully quantized" benchmark
to compare against Bonsai-4B (even smaller) and Qwen/Mistral (larger, native precision). The MLX quantization kernels
are a case study in framework-native optimization: writing custom Metal kernels for specific quantization schemes is
reusable methodology for Phase 6 fine-tuning + inference specialization.

## 4. What's inspiration only

The whitepaper methodology (how PrismML trained ternary weights, the calibration procedure, accuracy preservation at
1-bit) is research-level inspiration for future phases if Linus ever pursues proprietary quantization. The llama.cpp
integration is a reference for how established inference engines adopt new quantization formats (via PRs to upstream
repos). The GGUF format choice is portable but adds a dependency; MLX format is lighter for single-platform deployment.

## 5. What's incompatible or out of scope

Bonsai is inference-only; no training path and no fine-tuning path. Phase 6 Linus fine-tuning targets full-precision
models (via pmetal, mlx-lm) or post-hoc quantization, not quantization-aware training. The Q1_0 MLX PR is still
pending upstream — Linus might have to vendor PrismML-Eng's mlx fork or wait for upstream merge. Bonsai's accuracy
claims are strong for general chat but are untested on Dan's domain (genomics, bioinformatics) — Phase 1 benchmarking
must validate this.

## 6. Recommendation: **Integrate (Phase 1 baseline, Phase 5+ deployment)**

Bonsai-8B is the immediate Phase 1 "small model" baseline: smoke-test on Dan's task suite to establish accuracy floor
vs. Qwen/Mistral. If it passes (>80% of Qwen-7B-native accuracy on genomics Q&A), Bonsai becomes a standard offering in
Phase 5+ Linus deployments for latency-critical tasks and memory-constrained scenarios. The 1.58-bit ternary variant is
worth monitoring but lower priority until Phase 6.

## 7. Questions for Dan

- **Accuracy on genomics/bioinformatics tasks.** Whitepaper benchmarks are general (MMLU, MT-Bench). What's the minimum
  acceptable accuracy delta vs. Qwen-7B native on your own benchmark suite (papers, code questions)?
- **MLX Q1_0 PR status.** Is it safe to assume the upstream merge happens by Phase 1, or should Linus patch in
  PrismML-Eng's fork now as a hedge?
- **Bonsai vs. Bonsai-Ternary trade-off.** Is 1-bit-in-RAM (Bonsai, ~1.2 GB) enough, or is 1.58-bit ternary (slightly
  less compression, potentially higher accuracy) worth the extra model variants to test?

---

_Repo-note written 2026-05-05._
