---
title: "Transformer Design Guide (Part 2: Modern Architecture)"
source: blog post / technical tutorial
author: Rohit Bandaru
date: 2024
url: https://rohitbandaru.github.io/blog/Transformer-Design-Guide-Pt2/
file: ../../context/notes/bandaru_transformer_design_guide_pt2_modern_architecture.md
tags: [architecture, normalization, attention, MoE, efficiency, tutorial]
---

# Transformer Design Guide Part 2: Modern Architecture

## TL;DR

Bandaru provides the mathematical foundations and implementation details for modern transformer architecture (as of 2024): normalization choices (LayerNorm vs RMSNorm), activation functions (GeLU vs SwiGLU), position embeddings (sinusoidal to RoPE to ALiBi), efficient attention (FlashAttention, sliding-window, MQA/GQA), and MoE routing. The article is Linus's primary reference for understanding the "why" behind each component, with executable math and intuition for implementing each technique on Apple Silicon (Metal).

## Key claims and insights

- **RMSNorm vs LayerNorm**: RMSNorm removes mean-centering (shift-invariant), drops learned bias β, halves memory, reduces computation. Empirically matches LayerNorm while simplifying the operation. "More efficient than LayerNorm" becomes universal in 2024 LLMs.

- **Activation functions are empirically superior but theoretically opaque**: SwiGLU outperforms parameter-matched GeLU (Shazeer 2020), likely because gating mechanism allows input-dependent feature suppression. GLU family's expressivity advantage (gating ≈ learning second-order polynomials) may compensate for reduced width (8/3 expansion vs 4).

- **Position encodings: absolute → learned → relative → rotational**: Sinusoidal (Vaswani 2017) lacks flexibility. Learned absolute positions (GPT-1/2/3) adapt but don't extrapolate. Relative embeddings (T5, Shaw 2018) encode pairwise distances efficiently. RoPE exploits rotation matrices to encode relative position multiplicatively through Q/K transformation, achieving extrapolation benefits without learned parameters.

- **RoPE periodicity and long-context fixes**: Base frequency (10000) creates wavelength ~9763 tokens at d=768. For context >32K, periodicity degrades quality. Solutions: positional interpolation (rescale base frequency), NTK-aware scaling (adjust base differently), YaRN (scale high/low frequencies differently). Bandaru references Qwen2 and DeepSeek V3 convergence on YaRN.

- **FlashAttention is kernel-level optimization, not architecture**: Reduces memory reads/writes by ~4× via block matrix multiplication + online softmax + recomputation. Makes long sequences practical; enables RoPE extrapolation value to materialize in practice.

- **Attention variants for efficiency**:
  - Sliding-window attention: O(n) complexity, only local tokens attend. Mistral 7B uses half-context window. Combined with global attention blocks (Gemma 2, ModernBERT), maintains both local and long-range connectivity.
  - MQA: single KV head shared across all queries. ~32× KV-cache reduction. Degrades quality noticeably.
  - GQA: intermediate ground. Multiple query heads share groups of KV heads. ~4–8× reduction with minimal quality loss. Widely adopted.

- **MoE routing is an active research frontier**: Sparsely-gated (2017): noisy Gaussian gates + load-balancing loss. GShard (2020): simplifies loss, adds random sampling. Switch Transformer (2021): k=1 expert, single unified loss. DeepSeek (2024): auxiliary-loss-free bias-term routing (select via biased scores, weight via unbiased scores). Routing collapse (all tokens route to same experts) is the core problem; different solutions exist but none is universal.

- **Shared experts in modern MoE**: DeepSeek, Trinity introduce always-active experts storing general knowledge. Reduces fragmentation of common patterns across specialized experts. Improves training stability.

## What's reusable in Linus

**For Phase 6 fine-tuning baseline and Phase 7 post-training:**

- **RMSNorm implementation**: Bandaru provides the exact formula (lines 62–68) that Linus needs to adopt as default for any LoRA-fine-tuned layer stack. One learned scaling vector γ per layer; no learned β. Metal kernel exists (MLX); no custom implementation needed.

- **SwiGLU as the MLP baseline**: Use 8/3 expansion factor when parameter-matching to GeLU baseline. Bandaru explains why gating matters (input-dependent modulation) and provides the exact architecture. No theoretical justification (Shazeer: "divine benevolence"), but empirically robust across domains.

- **RoPE with YaRN for long-context fine-tuning**: When extending Linus's base model (e.g., Qwen2.5-Coder at 32K context) to longer windows for project-specific tasks, apply YaRN. Bandaru cites both Qwen2 and DeepSeek V3 convergence. Implementation: adjust base frequency by scaling different dimension frequencies by different factors (low frequencies more, high frequencies less).

- **GQA as the target attention variant**: If Linus inherits a base model with MHA, GQA conversion is straightforward (group KV heads, share within groups). Bandaru's explanation of the math (lines 563–577) makes the conversion clear. ~4–8× KV-cache savings without quality regression.

- **FlashAttention integration**: MLX already fuses attention kernels; no custom implementation needed. Understand that FlashAttention makes long-context training practical and that RoPE's extrapolation value materializes best when paired with fused kernels.

- **Sliding-window attention for very long contexts**: If Linus needs to handle >100K context tokens during fine-tuning, combine sliding-window (e.g., 4K window) for local attention with periodic global blocks. Bandaru cites Gemma 2 and ModernBERT. Metal kernel support may be limited; measure first.

## What's NOT applicable or dated

- **GPU/TPU optimization assumptions**: Bandaru's efficiency analysis assumes NVIDIA/TPU memory hierarchies (HBM, SRAM). Metal's unified memory model may have different bottlenecks. FlashAttention's 4× gains presume A100/H100 tile sizes; Apple Silicon might see different factors. Measure on M1 Max before trusting reported speedups.

- **FP8 quantization and custom kernels**: Bandaru discusses Gemma 2's logit soft-capping and other stabilization tricks but doesn't dive into quantization. Linus's LoRA fine-tuning likely runs in BF16 or FP32 (MLX supports both); quantization is a deployment-stage concern (Phase 7+).

- **MoE as a Phase 6 baseline**: Bandaru provides deep routing intuition (Sparsely-Gated, GShard, Switch, DeepSeek variants) but notes there's no convergence. For single M1 Max LoRA training, MoE is prohibitively complex. Focus on dense baseline (RMSNorm + SwiGLU + GQA + RoPE) first. Defer MoE to Phase 7 with multi-device setup.

- **Vision Transformer differences**: Bandaru notes ViT and other modalities tend to stick to more vanilla architectures. Linus is text-focused; skip these sections.

## Cross-references

- **Vaswani et al. (2017) "Attention Is All You Need"**: The original transformer and sinusoidal position encoding baseline.

- **Shazeer (2020) "GLU Variants Improve Transformer"**: Primary source for SwiGLU advantage.

- **Su et al. (2021/2024) "RoFormer"**: RoPE introduction and mathematical foundation.

- **Dao et al. (2022) "FlashAttention"**: Kernel optimization that makes modern LLMs practical.

- **Press et al. (2021) "ALiBi"**: Attention with Linear Biases as an alternative to learned or absolute position embeddings.

- **Raschka's Big LLM Architecture Comparison**: Applies Bandaru's components to current frontier systems (DeepSeek V3, Llama 4, GLM-5).

- **JY Tan's Crystallization article**: Quantifies which of Bandaru's components have converged in practice (53-model dataset).

- **Gemma 2 technical report**: Combines many of Bandaru's techniques (RMSNorm, RoPE, GQA, sliding-window + global attention, logit soft-capping, QK-normalization) into a coherent 2024 system.
