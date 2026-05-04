---
title: "Toward universal steering and monitoring of AI models"
source: Science 391 (6787), 19 February 2026, DOI 10.1126/science.aea6792
authors: Daniel Beaglehole, Adityanarayanan Radhakrishnan, Enric Boix-Adserà, Mikhail Belkin
affiliation: UC San Diego (CSE & Halıcıoğlu Data Science Institute); MIT; Broad Institute of MIT and Harvard; Wharton School, University of Pennsylvania
date: 2026-02
pdf: ../../context/papers/science.aea6792.pdf
tags: [interpretability, steering, monitoring, activations, safety, alignment, rfm, probing, hallucination, toxicity, group-f]
---

# Toward universal steering and monitoring of AI models

## TL;DR
The authors present a **supervised** method (Recursive Feature Machines, RFM) for extracting per-block "concept vectors" from the internal activations of a frozen LLM, VLM, or reasoning model using as few as 500 labeled prompts and under a minute of A100 time per concept. Adding a scaled concept vector `ε·v` to a single transformer block's activations during the forward pass **steers** generation toward (or away from) that concept; training a small classifier on projections of activations onto those vectors gives a **monitor** that detects whether the concept is active. They demonstrate steering across 512 concepts on three Llama generations (8B–90B, including 4-bit quantized Llama-3.2-vision-90b and Llama-3.3-70b), show concept vectors transfer across languages (English-trained "conspiracy theorist" works in Chinese) and compose linearly (multi-concept steering), exploit steering to expose safety vulnerabilities (anti-refusal, dangerous-materials instructions) AND to improve performance (Python→C++ translation on HackerRank), and show that **RFM-based probes beat GPT-4o judges and a fine-tuned ToxicChat-T5-Large** at hallucination/toxicity monitoring across six benchmarks. Framed explicitly as an alternative to sparse-autoencoder unsupervised approaches: cheaper, supervised, immediately operational.

## The problem (in plain language)
A modern LLM contains an enormous amount of knowledge encoded in its activations, but we have almost no instruments for *reading* those activations at inference time. Two consequences follow. When a model behaves badly — hallucinates a citation, refuses an innocent request, gets jailbroken — we cannot tell from outside whether the relevant concept (deception, harmfulness, refusal) was active during generation; we can only judge the output, which the model has been optimized to make plausible. And when we want to *change* a behavior — terser, less likely to fabricate, willing to translate to C++ — the standard lever is fine-tuning (LoRA, RLHF), which is expensive and produces a different model.

The mechanistic-interpretability tradition has tried to crack activation-reading with **sparse autoencoders** (SAEs), trained without labels to discover the features a model uses (Anthropic's Golden-Gate-Bridge work in Claude 3 Sonnet is the famous demo). The authors flag two practical problems: SAEs are not guaranteed to surface the specific concept you care about (you have to hunt through a large feature dictionary), and recent results — including a candid DeepMind interpretability post — suggest SAEs underperform supervised probing on the downstream tasks (steering, monitoring) that motivated them.

The paper's bet is that you can do this more directly. Label even a small set of prompts "concept active / inactive" and a strong supervised feature-extractor should find the linear direction in activation space that tracks the concept — and the *same* direction works both as a classifier (monitoring) and, with the right sign and magnitude, as an additive perturbation (steering).

## What they propose
The mechanism has three pieces.

**Concept vector extraction.** Curate `n` (≈400–500) prompts labeled binary {0,1} for whether the concept is present. Run them through the frozen model and capture the last-token activation `a_ℓ ∈ ℝ^k` at every transformer block `ℓ ∈ {2,…,L}`. At each block, train an RFM — a kernel-based predictor that learns features by recursively reweighting an Average Gradient Outer Product — on `(a_ℓ, y)`. The top eigenvector `v_ℓ` of the AGOP matrix at convergence is the concept vector for block `ℓ`. RFM is the load-bearing technical choice and is contrasted experimentally against PCA, difference-in-means, and logistic regression; RFM consistently wins on overall steerability (Fig. 3B and supplementary tables).

**Steering.** During the forward pass, replace `A_ℓ,r(X)` with `A_ℓ,r(X) + ε·v_ℓ` for every row `r` of the activation matrix at the chosen block(s). `ε` (the "control coefficient") is the dial: small values nudge, large values force. Multi-concept steering is just `ε₁v₁ + ε₂v₂` summed before injection. In the paper's experiments, even injection at a *single* block is sufficient to elicit a coherent behavioral shift; the first block is omitted because results were sensitive there.

**Monitoring.** Same extraction, but keep the top `p` eigenvectors per block and use the projections `⟨a_ℓ, v_{ℓ,j}⟩` as features for a downstream classifier. Two strategies: train one predictor per block and pick the best, or aggregate features across all blocks into a single vector and train one predictor. Either way, the trained probe runs as a tiny attached head during inference and predicts whether the monitored concept is active.

The whole procedure is supervised, model-agnostic in the sense that it only touches block outputs (works on LLMs, VLMs, reasoning models), and architecture-agnostic in that the same recipe was applied across Llama-3.1-70b, Llama-3.3-70b, Llama-3.2-vision-90b, Falcon, Mistral, and DeepSeek (the last for deception suppression).

## Key results
On **steerability across 512 concepts** (5 concept classes × three Llama models), RFM beat PCA, diff-in-means, and logistic regression on overall successful-steering rate. Steerability **scaled with model size and recency**: Llama-3.3-70b-4-bit was more steerable than Llama-3.1-70b-4-bit despite identical architecture, suggesting steerability is a property models acquire through better training, not just larger weights. For some concept classes (topophiles), steerability climbed from 21% to 91% across model sizes.

On **safety-vulnerability exposure**, RFM-derived "anti-refusal" vectors caused Llama-3.3-70b-4-bit and Llama-vision-3.2-90b-4-bit to produce precise instructions for dangerous materials. This is dual-use: the same instrument unlocks unsafe behavior and could be inverted to *suppress* it (DeepSeek deception suppression is shown in supplementary figures).

On **capability improvement**, steering Llama-3.3-70b-4-bit toward C++ during a Python→C++ translation task **outperformed both the model's original output and direct C++ prompting** on HackerRank (732 test cases across 50 easy/medium problems). Steering isn't just a safety lever; it can surface latent capability the prompt didn't elicit.

On **transferability and composition**, a "conspiracy theorist" vector trained on English prompts steers Chinese outputs into conspiracy responses; mixed concept vectors (conspiracy + Shakespeare) yield blended outputs. Concept representations live in a model-internal semantic space that is at least partially language-invariant — an extreme manifestation of the linear representation hypothesis.

On **monitoring**, RFM-probes trained on a Llama's activations beat **the same Llama acting as a judge** on every one of six hallucination and toxicity benchmarks (AUROC). The best probe across the three Llamas also beat **GPT-4o as judge** and beat **ToxicChat-T5-Large** (a fine-tuned classifier) on FAVABENCH. A small cheap classifier reading the model's own activations is a better detector of that model's own hallucinations than asking a stronger model to grade the output.

The cost numbers matter for Linus: under one minute on a single A100 and fewer than 500 training samples per concept — several orders of magnitude cheaper than LoRA fine-tuning.

## What's reusable in Linus

**Phase 6/7 — supervised steering as a lighter alternative to LoRA.** When Linus wants a Worker terser, less likely to refuse benign requests, or biased toward a domain (genomics terminology), the standard answer is fine-tuning. Beaglehole gives a much cheaper path: ~500 labeled prompts, per-block RFM concept vectors against a frozen Worker, applied at inference time with a tunable `ε`. No weight surgery, no retraining, reversible. A strong candidate for the first non-trivial behavior-modulation layer, sitting between prompting (free, weak) and fine-tuning (expensive, permanent).

**Phase 7 — activation monitoring as a sandbox primitive.** Linus's sandbox today is policy-level: file-system gates, network gates, command allowlists. This paper enables a qualitatively new guardrail class operating *inside* the model: a small RFM-probe attached to the local Worker's inference loop that fires when "concept = pandemic-pathogen synthesis" or "concept = deception" lights up during generation. This connects directly to the dual-use biotech concern in [paper-notes/2306.03809v1.md](2306.03809v1.md): Soice et al. raise the *design* worry that LLMs lower the barrier to dual-use bio knowledge; Beaglehole gives the *technical mechanism* by which Linus could detect when a Worker is generating in that conceptual region and intervene.

**Phase 1/2 — first-class observation surface in the architecture.** The deeper architectural lesson is that activations should be a real observation surface for the orchestration layer, not a model-internal opaque blob. When Linus runs a Worker end-to-end (pmetal-serve, mlx-lm, llama.cpp via Ollama), the inference layer is *ours* and can in principle expose hooks for reading and perturbing block outputs. Right time to put a stub `linus.observability.activations.*` API into ARCHITECTURE.md — no-op for Ollama, real hooks for mlx-lm later. Naming the surface now lets later phases plug things in without re-architecting.

**Phase 3 — supervised hallucination probes for KnowledgeBase RAG.** The monitoring result (probes beat judges including GPT-4o) is directly applicable. When a Worker produces a RAG answer over Dan's papers corpus, a small RFM-probe trained on hallucination-labeled examples could flag low-confidence responses for review or re-retrieval. Cheaper at inference than a second model judge, and closer to ground truth because it reads what the generating model actually represented internally.

**Cross-cutting — extends `docs/syntheses/security-synthesis.md`.** That synthesis covers prompt injection and supply-chain risk but treats the model as a black box. Activation-level inspection adds a third defensive axis: behavioral monitoring from inside the model.

## What's NOT applicable

**Hosted Maestro is opaque to all of this.** The technique fundamentally requires read/write access to per-block activations during the forward pass. Linus's Maestro path (Anthropic API, Claude.ai) does not expose this and never will. A meaningful architectural constraint: any workflow whose safety story depends on activation-level monitoring **must** route through a local Worker. Cuts both ways — it's an argument for keeping certain sensitive workflows local rather than reflexively dispatching to Maestro.

**A100, fp16, and 4-bit Llama only.** The paper runs on NVIDIA A100s with steered models either fp16 or 4-bit-quantized Llama family. It does not test BitNet (1.58-bit), arbitrary GGUF quantizations, or MLX-quantized variants. Steering at 4-bit works (Llama-3.3-70b-4-bit and Llama-3.2-vision-90b-4-bit are the demos), encouraging for Linus, but extreme quantizations like BitNet are open — the additive `ε·v` perturbation may interact poorly with ternary weights. Flag for empirical check.

**RFM is not standard infrastructure.** Recursive Feature Machines (Radhakrishnan et al., Science 2024) are a relatively new tool; there's no batteries-included MLX or PyTorch port to `pip install`. The Zenodo code release (zenodo.18215716) is the starting point. Adopting this means taking on a non-trivial dependency that will need wrapping for Apple Silicon.

**Concept-vector quality depends on dataset curation.** The paper uses GPT-4o to generate 400 statements per concept. A fully-local Linus would either replicate with a local model (lower quality) or accept a one-time cloud cost.

**Single-block steering is convenient but sensitivity is real.** The first block was omitted because results there were unstable. Block choice and `ε` are not theoretically prescribed — they are tuned per concept per model. "Deploying steering" is not a one-line config; each behavior gets its own calibration.

## Connections

This is the *technical mechanism* anchor for **Group F (Safety/Alignment/Privacy)**. The constellation: **dual-use biotech** ([2306.03809v1.md](2306.03809v1.md)) is the *design / policy* angle (LLMs lower barriers to dangerous knowledge); **LLM deanonymization** ([2602.16800v2.md](2602.16800v2.md)) is the *threat-model* angle (text users wrote can be re-identified); **Anthropic Values in the Wild** (next batch) is the *cultural / corpus* angle (what values emerge in deployed assistant behavior); **Beaglehole** is the *instrument* angle — it gives Linus a concrete tool with which to observe and intervene on an internal Worker. The only Group F paper that hands Linus an actual lever rather than a concern. The dual-use biotech worry in particular is *answerable* — partially, imperfectly — by an activation monitor over a local Worker.

It extends `docs/syntheses/security-synthesis.md` along an axis that synthesis doesn't cover: that synthesis is about supply chain (where models and code come from) and prompt injection (what arrives at the model). Beaglehole adds **behavioral observation from inside the model** as a third defensive surface.

Methodologically, this paper is in productive tension with the SAE / mechanistic-interpretability tradition (Anthropic Transformer Circuits work, Golden Gate Bridge, Bricken et al. on monosemanticity). The cited DeepMind post (Smith et al., 2024) — that SAEs underperform probing on downstream tasks — does real work in their argument. For Linus the lesson is to favor the simpler supervised tool now and reserve mechanistic-interpretability tooling for later phases when the question shifts from "monitor / steer this concept" to "what concepts exist at all?" Nothing else in the noted corpus covers internal-state inspection of inference; this is unique in Group F.

## Open questions for Dan

1. **Should Linus's local Worker inference layer (pmetal-serve / mlx-lm / Ollama) expose activation hooks?** The architecture decision is binary: either the inference layer is a black box (faster to ship, no observability story) or it exposes per-block hooks (more engineering, but enables steering, monitoring, and any future activation-based tooling). Worth deciding before mlx-lm integration solidifies. Recommend: stub `linus.observability.activations.*` API in ARCHITECTURE.md now, no-op for Ollama, real hooks for mlx-lm in Phase 6/7.

2. **Is real-time activation monitoring a feasible Phase 7 sandbox primitive on M1 Max, or too expensive?** The probe itself is small (a linear classifier over ~`L·p` features), but capturing per-block activations during generation has memory and latency cost. Worth a back-of-envelope estimate against Llama-3.1-8B-4bit on an M1 before committing to the design.

3. **Supervised steering as a behavior-modulation lever — Phase 6 prerequisite to LoRA?** The paper's case for supervised steering being cheaper than fine-tuning is strong. Should Linus's roadmap add an explicit "steering before fine-tuning" Phase 6 milestone — i.e., try to achieve a desired behavior with RFM steering first, escalate to LoRA only if steering is insufficient?

4. **Does this technique work on BitNet / extreme-quantized models?** The paper validates 4-bit Llama, which is reassuring, but BitNet's ternary weights and severely-quantized activations might break the linearity assumption that makes additive `ε·v` work. This is an empirical question worth flagging if BitNet (Group A) becomes a serious deployment target — possibly a small spike experiment in `experiments/`.

5. **Where does the dataset for our first concept vectors come from?** The paper's GPT-4o-generated 400-statement-per-concept pipeline assumes cloud-LLM access. For a "private, local" Linus, do we accept GPT-4o or hosted Maestro as a one-time bootstrapping cost for concept-vector training data, or do we want a fully-local pipeline using a strong Worker (with the quality hit that implies)? This affects whether the activation-monitoring story can claim full data sovereignty.

6. **First concept to actually try.** If we do this, the first concept matters for credibility. Candidates: hallucination (most general, biggest payoff for KnowledgeBase RAG), terseness (smallest scope, easiest to evaluate), or pandemic-pathogen-synthesis-adjacent content (highest-stakes safety demo, hardest to label). Recommend hallucination first — the monitoring evaluation is well-defined and the result is immediately useful in Phase 3.
