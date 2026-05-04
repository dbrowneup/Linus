## DEC-0043 — Memory-mode-aware fine-tuning targets in Phase 6a

**Date:** 2026-05-03 **Status:** accepted

**Context.** Phase 6a commits to FP16-LoRA on a genomics/biochem corpus regardless of the lane decision (DEC-0014). The
fine-tune is the first opportunity to make the resulting Worker _natively cooperate_ with the memory pillar substrate
(DEC-0028 through DEC-0032) rather than requiring the orchestration layer to post-process around it. The
[Kojima paper](../paper-notes/2205.11916v4.md) Table 4 shows trigger sensitivity is real (45.7%–78.7% spread across
instructive variants on the same task), making "trigger-invariance" a concrete fine-tuning target. The
[Coconut paper](../paper-notes/2412.06769v3.md) suggests structured output that surfaces branch points is likewise
trainable. None of these add compute cost; they are training-data shape decisions.

**Decision.** **Two memory-related fine-tuning targets are added to the Phase 6a deliverable as training-data shape
requirements.**

1. **Step-by-step decomposition for system-2 queries as default behavior.** The fine-tune training data biases toward
   step-by-step reasoning on system-2 queries (math, dependency resolution, multi-step planning, code reasoning over
   more than one file) without requiring the "let's think step by step" trigger. The Kojima trigger sentence is absorbed
   into the prior. Measurable as **CoT-gap shrinkage post-fine- tune** using the DEC-0033 fingerprint methodology — the
   same 50-item smoke test re-run on the fine-tuned adapter.
2. **Episodic-store-friendly output structure.** The fine-tune is trained to produce outputs that are clean for the
   DEC-0030 two-segment record shape: explicit `scratchpad` / `answer` separation via a structural marker the
   orchestration layer can parse; facts carry typed tags compatible with the LLM Wiki claim-typing convention
   (`[!source]` / `[!analysis]` / `[!unverified]` / `[!gap]`); branch- point surfacing is encouraged where applicable
   per Coconut's superposition framing.

Both are training-data shape decisions, not architecture decisions, and cost nothing in Phase 6 compute beyond curating
the training set. The result is a Linus-native Worker that natively cooperates with the memory pillar substrate,
reducing the orchestration-layer post-processing burden.

Validation: held-out perplexity on KB papers + Dan task suite (existing Phase 6a validation) + CoT-gap re-measurement +
a structural-output parse-success rate on a held-out set of system-2 prompts.

**Consequence.** Phase 6a's first fine-tuned Linus adapter ships with memory-pillar-aware behaviors built in. Subsequent
Phase 6b/6c/6d fine-tunes inherit the same training-data shape conventions. Reversal cost medium — the training-data
shape choices propagate through every subsequent fine-tune, and changing them later means re-curating the training
corpus.
