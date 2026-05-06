---
title: "The Big LLM Architecture Comparison: From DeepSeek V3 to GLM-5"
source: blog post / architecture comparison
author: Sebastian Raschka
date: 2025-07 (last updated 2026-04)
url: https://magazine.sebastianraschka.com/p/the-big-llm-architecture-comparison
file: ../../context/notes/raschka_2025_big_llm_architecture_comparison.md
tags: [architecture, MoE, MLA, GQA, inference, 2025-frontier]
---

# The Big LLM Architecture Comparison

## TL;DR

Raschka surveys frontier LLM architectures (DeepSeek V3/R1, Llama 4, GLM-5, etc.) across 2024-2026, identifying two pivotal shifts: Multi-Head Latent Attention (MLA) as a KV-cache compression alternative to GQA, and high-expert-count MoE (64-256 experts) as the dominant scaling axis for dense→sparse transition. The analysis matters for Linus because MLA + MoE define the inference-efficiency Pareto frontier that drives Phase 6 fine-tuning decisions on Apple Silicon's 32 GB unified memory.

## Key claims and insights

- **MLA vs GQA tradeoff**: GQA shares KV heads across query groups but degrades quality slightly; MLA compresses KV tensors into latent space, then reconstructs at inference with one extra matmul. DeepSeek V2/V3 ablations show MLA outperforms both MHA and GQA on downstream tasks while saving KV-cache memory — practical win for long-context inference under memory constraint.
- **MoE explosion in expert count**: Mixtral (8 experts), Llama 3.1-405B (still dense), DeepSeek V3 (256+1 shared), GLM-5 (128–256 routed). Routing quality and auxiliary-loss-free load balancing (DeepSeek bias-term innovation) become critical at scale.
- **Normalization convergence complete**: RMSNorm + pre-norm is universal in 2025 frontier models. No outliers; the choice is settled.
- **RoPE dominance with caveats**: All surveyed 2025 models use RoPE, but long-context scaling requires NTK-aware or YaRN frequency adjustment. Periodicity in high-frequency dimensions is a real problem; direct fixes essential.
- **Stability mechanisms now non-negotiable**: QK-normalization, logit soft-capping, and depth-scaled initialization appear in nearly every 2025 model. No longer optional.

## What's reusable in Linus

**For Phase 6 fine-tuning on 32 GB M1 Max:**

- **MLA as the target compression strategy**: If Linus fine-tunes a 7–14B base model with LoRA, consider MLA for KV-cache reduction during inference. A single forward+backward matmul per layer is cheap; the memory savings for long-context chat enable longer session windows (relevant to Mughal's context degradation problem).
- **MoE routing as a post-Phase-6 direction**: The auxiliary-loss-free bias-term approach (DeepSeek) is simpler than traditional load-balancing losses and appears empirically robust. If Linus scales to multi-expert local inference, start there rather than Shazeer's 2017 noisy-gating baseline.
- **Stability interventions for 14B→7B LoRA**: QK-normalization is cheap (one RMSNorm per KV pair, no learned params required). Logit soft-capping (tanh scaled) is a one-line addition to attention. If LoRA training on 32 GB hits instability, try these first before touching learning rate.
- **Extrapolation-safe RoPE**: When fine-tuning on new context lengths, use NTK-aware base-frequency scaling or YaRN. Raschka's citations show Qwen2 and DeepSeek V3 converged on YaRN; it's battle-tested.

## What's NOT applicable or dated

- **Full MoE training on 32 GB unified memory**: Raschka's 256-expert models assume TPU/GPU clusters with expert parallelism and ring-all-reduce. Linus's single M1 Max cannot efficiently shard experts across devices. MoE is a deferred goal (Phase 7+), not a Phase 6 target.
- **The article's normalization comparison doesn't address LayerNorm vs RMSNorm on Apple Silicon specifically**: Raschka assumes NVIDIA GPU optimization kernels. Metal/MLX may have different performance characteristics; measure before adopting.
- **Exact expert counts and active-expert ratios**: The 256 experts in GLM-5 and Kimi K2 are calibrated for 10T-token training runs with 8×8 TPU pods. Linus's local LoRA will need empirical tuning on much smaller batches.

## Cross-references

- **JY Tan's crystallization article**: Provides the 2017–2025 quantitative dataset backing up Raschka's narrative. Raschka is the applied practitioner view; Tan is the evidence-base.
- **Bandaru's Transformer Design Guide Part 2**: Covers the same architectural components (RMSNorm, RoPE, GQA, MLA, SwiGLU, MoE) with deeper math. Read Bandaru first for intuition, then Raschka for how these combine in current systems.
- **Vaswani et al. (2017) "Attention Is All You Need"**: The original transformer that Raschka uses as the historical baseline.
- **DeepSeek V3 paper (2412.19437)** and **DeepSeek V2 paper (2405.04434)**: Primary sources for MLA + auxiliary-loss-free MoE that Raschka discusses.
