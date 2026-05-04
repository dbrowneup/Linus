## DEC-0033 — Per-Worker CoT-gap fingerprint as a registry property

**Date:** 2026-05-03 **Status:** accepted

**Context.** [Kojima et al. (2205.11916)](../paper-notes/2205.11916v4.md) show that the chain-of-thought capability gap
is _emergent at scale_: negligible below ~60B parameters in 2022 GPT-3, dramatic above. For Linus's local Worker fleet
(1B–14B class), the per-Worker CoT response varies: some models are RLHF'd on CoT-style data and step-by-step by
default, others gain little from the trigger, others lose accuracy when forced to verbose reasoning on lookup-shaped
tasks. Without a measured per-Worker fingerprint, the router either burns tokens injecting CoT triggers on Workers that
don't benefit, or suppresses the trigger on Workers whose latent capability needs it. DEC-0031's `cot_budget` primitive
needs per-Worker calibration to be useful.

**Decision.** **CoT-gap is a measured property in the model registry, not a guessed configuration.** A fixed 50-item
MultiArith-style smoke test runs on every model pulled into the registry; the registry stores
`accuracy_with_CoT - accuracy_without_CoT` per model, alongside existing tags (parameter count, native context window,
`scratchpad_durability` from DEC-0030, task-completion-time profile from the Speed paper).

The router consults the delta in two ways: (1) decides whether to inject a CoT trigger automatically (large positive
delta → inject; near-zero or negative → suppress); (2) scales the DEC-0031 `cot_budget` defaults per-Worker — a Worker
with a small CoT-gap may need higher caps to extract its latent capability; a Worker with a large CoT-gap may saturate
earlier.

The fingerprint is re-run when the model is updated. Phase 1c deliverable, run alongside the BitNet 2B4T spike already
scheduled in DEC-0013. Results land in `benchmarks/results/cot_gap_<YYYY-MM-DD>.json` and are mirrored into the Linus
model registry at `~/.linus/registry/models.json`.

**Consequence.** Worker dispatch becomes empirically calibrated rather than heuristic. The 50-item smoke test is cheap
enough (low minutes per Worker on M1 Max) to re-run on every model update. Reversal cost low — the registry field is one
column; if measurement turns out to be uninformative, the router can ignore it without architectural change.
