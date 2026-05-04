## DEC-0035 — ARC-AGI as a memory diagnostic, not a Linus capability target

**Date:** 2026-05-03 **Status:** accepted

**Context.** The [ARC Prize 2024 retrospective (2412.04604)](../paper-notes/2412.04604v2.md) documents the most
expensive empirical evidence that frontier systems are spending compute to fake memory: o3 reached 91.5% at ~$1.15M /
9.5B tokens, 172× more compute for the last 9 percentage points over the 55.5% open-source SOTA. The benchmark is most
useful to Linus as a _diagnostic frame_ — vary the memory while holding the model fixed, measure the delta — not as a
leaderboard target. Frontier-compute approaches are not Linus territory; Kaggle-track approaches are research projects,
not weekend spikes.

**Decision.** **ARC-AGI is adopted as a memory diagnostic, not a capability target.** Phase 2/3 deliverable: take 50–100
ARC-AGI public-eval tasks, run a small Linus Worker (Llama-3.2-3B class) against them twice — once with
`memory_mode=stateless`, once with `memory_mode=session_stateful` (using the v0 episodic store from DEC-0029). Measure
the delta. The experiment turns the memory thesis into a number; costs nothing in Maestro tokens; gives a concrete
measurement that survives re-running across substrate changes.

ARC-AGI-1 is good enough for diagnostic use (signal-to-noise less critical than reproducibility per the paper note);
ARC-AGI-2 is adopted as the diagnostic target when it lands and stabilises. Phase 6 considers extending to ARC-AGI-pub
track only if reproducing TTT-style results becomes a useful memory-architecture probe. The benchmark is _not_ added to
`benchmarks/dan_tasks/` (which is Worker-selection-focused) — it lives at `benchmarks/arc_agi_diagnostic/` as a
memory-architecture probe.

**Consequence.** The memory-pillar claim becomes measurable in a public-domain way. The diagnostic survives substrate
evolution: when the Phase 6 TTT spike (DEC-0037) or the minGRU spike (DEC-0038) lands, the same ARC-AGI experiment
re-runs against the new substrate and the deltas compound. Reversal cost negligible — the diagnostic is a benchmark, not
an architectural commitment.
