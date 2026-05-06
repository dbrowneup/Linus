---
title: "The Crystallization of Transformer Architectures (2017–2025)"
source: blog post / research survey
author: JY Tan
date: 2025
url: https://jytan.net/blog/2025/transformer-architectures/
file: ../../context/notes/jytan_2025_crystallization_of_transformer_architectures.md
tags: [architecture, convergence, RoPE, RMSNorm, SwiGLU, dataset, 2025-synthesis]
---

# The Crystallization of Transformer Architectures

## TL;DR

Tan documents 53 transformer models from June 2017 to December 2025, showing rapid exploration (2017–2022) followed by striking architectural convergence (2023–2025) on a de facto standard bundle: pre-norm RMSNorm, RoPE, SwiGLU MLPs, and KV-sharing (MQA/GQA). The dataset is Linus's primary artifact for Phase 1 recon: quantifies what "convergence" means empirically, identifies outliers (MoE routing, long-context attention), and separates robust design from path dependence.

## Key claims and insights

- **Four eras of transformer architecture**:
  - **Era I (2017–2019)**: Foundations. Post-norm, learned absolute positions, ReLU, standard MLP.
  - **Era II (2020–2022)**: Scale-up. RMSNorm, parallel attention+FFN, RoPE adoption, SwiGLU.
  - **Era III (2023–2024)**: Crystallization. LLaMA recipe (Feb 2023) standardized the stack; 41/53 models adopt RMSNorm (77%), 37/53 use RoPE (70%), 38/53 use SwiGLU (72%).
  - **Era IV (2024–2025)**: MoE divergence. Dense convergence holds; MoE design (expert count, load balancing, shared experts) remains unsettled.

- **Convergence is both signal and constraint**: The LLaMA recipe works because it is stable, efficient on current GPUs/TPUs, and pairs with fused kernels (FlashAttention, fused RMSNorm). But convergence also reflects path dependence: influential open checkpoints (LLaMA, Mistral) and kernel availability create network effects. Different hardware might favor different choices.

- **Hardware co-evolution is real**: Tensor core tile sizes (16×16 A100, 8×8 H100), memory bandwidth bottlenecks, and fused-kernel availability drove adoption of MQA/GQA (reduce KV-cache), RoPE (compose cleanly with FlashAttention), and 128-dim heads (multiples of tile size). Architectural choices are not hardware-agnostic.

- **MoE remains unsettled**: Unlike dense models, 11/53 models are MoE, and all emerged 2024–2025. Expert count (8 to 384), active experts (2–8), shared experts (0–2), and routing mechanisms vary widely. No convergence signal yet; design depends on training budget and inference-cost targets.

- **QK-normalization is the new stability lever**: Appeared 2024–2025 (Gemma 3, OLMo 2, Qwen 3, Kimi K2) as models scaled >60 layers or >30B params. Controls norm drift and prevents attention logit blow-ups without quality regression.

## What's reusable in Linus

**For Phase 1 recon and Phase 6 baseline decisions:**

- **The dataset itself is a first-class artifact**: Use the 53-model table (page 362–417 of the article) as a decision-making tool. Before fine-tuning Linus's base model, pick a comparable model from the dataset and inherit its architecture. Qwen2.5-Coder (12B, Table entry) uses RMSNorm+RoPE+SwiGLU+GQA+no-bias; that's a safe starting point.

- **Pre-norm RMSNorm is non-negotiable**: No reason to deviate on 2025 Apple Silicon. Adopt it as the baseline for any Phase 6 layer stack.

- **RoPE extrapolation strategy is essential, not optional**: When fine-tuning on context lengths beyond the base model's training length, apply NTK-aware or YaRN frequency adjustment (Tan references both). Periodicity in high-frequency dimensions is documented; ignoring it risks degradation on long-context tasks.

- **SwiGLU with 8/3 expansion is the Pareto frontier for MLPs**: Parameter-matched GeLU underperforms SwiGLU empirically (Shazeer 2020, cited throughout). Unless Linus has a specific reason to deviate (e.g., custom Metal kernels), adopt SwiGLU.

- **GQA is the safe choice for inference efficiency**: MQA (single KV head) is more aggressive but degrades quality more. Tan's table shows GQA in 23/53 models; it's the practical middle ground for KV-cache reduction when context length is a bottleneck.

- **Stability mechanisms scale with depth and parameters**: If Linus fine-tunes a 14B base to >60 effective layers (e.g., via mixture techniques), add QK-normalization. It's cheap (one RMSNorm call) and appears robustly beneficial in the empirical record.

## What's NOT applicable or dated

- **Hardware assumptions**: Tan's analysis is GPU/TPU-centric. Metal/MLX kernels may not support all fused operations optimally. Measure throughput and memory usage on M1 Max before committing to, e.g., parallel attention+FFN (only 5/53 models use it; likely because kernels don't optimize it widely).

- **Vocabulary size trends** (32K→128K→256K): Tan documents the expansion as models scale, but for Linus's LoRA work, vocabulary size is inherited from the base model and shouldn't be changed. Skip this section.

- **MoE as a Phase 6 target**: Tan notes MoE is unsettled design space. All 11 MoE models in the dataset are from 2024–2025 and trained at scale (100B+ params). LoRA training on single M1 Max makes expert design moot. Defer to Phase 7.

## Cross-references

- **Raschka's Big LLM Architecture Comparison**: Extends Tan's dataset analysis to current frontier systems (DeepSeek V3, Llama 4, GLM-5) released after Tan's article cutoff. Tan is the historical record; Raschka is the applied practitioner's reading of that record.

- **Bandaru's Transformer Design Guide Part 2**: Provides mathematical intuition for each component Tan documents (normalization, position embeddings, activation functions, attention). Read this alongside Tan's table for understanding the "why" behind each choice.

- **Vaswani et al. (2017)**: The original transformer that serves as Tan's historical anchor.

- **Shazeer (2020) "GLU Variants Improve Transformer"**: Primary source for SwiGLU advantage cited throughout.

- **Su et al. (2024) "RoFormer"**: RoPE introduction paper, cited for its mathematical elegance and relative-position encoding.

- **DeepSeek V3 auxiliary-loss-free routing** (Section 3.3): Tan's clearest explanation of the routing innovation that enables 256-expert models without training pathology.
