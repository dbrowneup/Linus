## DEC-0037 — Apple-Silicon viability spike for test-time training (TTT)

**Date:** 2026-05-03 **Status:** accepted

**Context.** [Akyürek et al. (2411.07279)](../paper-notes/2411.07279v2.md) show that fitting a per-task LoRA adapter on
synthetic leave-one-out demonstrations lifts an 8B Llama from 45% to 53% on ARC, with ensembling reaching 61.9% (average
human performance). For Linus, TTT is the most plausible candidate for _episodic-memory consolidation_: a session
transcript becomes a transient LoRA adapter, stored as a per-project memory module, loaded back when the project
resumes. DEC-0029 keeps this option open as a Phase 6 spike but gates the decision on a Phase 1 viability measurement.
The viability question is whether per-task LoRA training on mlx-lm + Llama-3.2-1B is cheap enough on M1 Max to be
operationally useful.

**Decision.** **Phase 1c spike**, sequenced after the BitNet 2B4T benchmark (DEC-0013) and before the Phase 6 lane
decision (DEC-0014). Reproduction shape:

- 10 ARC validation tasks.
- Llama-3.2-1B as base model (smallest credible target).
- mlx-lm LoRA pipeline.
- Leave-one-out synthetic data generation per Akyürek recipe (with geometric augmentations: flips, rotations, color
  permutations).

Primary measurement: per-task compute cost on M1 Max (wall-clock + RSS + thermal). Secondary measurement: accuracy lift
over the base 1B model on the 10 tasks.

**Decision rule:** if per-task TTT cost is **under ~5 minutes wall-clock** with adapter saving correctly, TTT graduates
to a Phase 6 candidate substrate for episodic-memory consolidation per DEC-0029; otherwise TTT is **deferred to Phase 8
as a research direction** and Phase 2's SQLite + git substrate stands alone for the lifetime of Phase 6+. The decision
rule is the load-bearing artifact of this experiment.

Results land in `experiments/ttt-mlx-arc-spike/results.md` with raw benchmark output in
`benchmarks/results/ttt_viability_<YYYY-MM-DD>.json`.

**Consequence.** The Phase 6 substrate menu is informed by measurement rather than speculation. If the spike succeeds,
Phase 6 gains a concrete substrate experiment for episodic-memory consolidation; if it fails, the v0 SQLite + git
substrate from DEC-0029 is confirmed as the long-term answer and Phase 8 becomes the home for any future TTT
experimentation. Either outcome closes a planning question with empirical input. Reversal cost low — the spike is a
contained experiment.
