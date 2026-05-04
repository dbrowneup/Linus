## DEC-0034 — Worker-size vs. CoT-length empirical comparison (Phase 1c)

**Date:** 2026-05-03 **Status:** accepted

**Context.** The complexity-theoretic results in [Feng et al. (2305.15408)](../paper-notes/2305.15408v5.md) and
[Merrill & Sabharwal (2310.07923)](../paper-notes/2310.07923v5.md) predict that on inherently sequential tasks a smaller
Worker with a generous CoT budget can outperform a larger Worker forced to be terse — because effective depth scales
with generation length under chain-of-thought, while parameter count alone is bounded by the TC0 ceiling on a single
forward pass. This is a falsifiable claim, and its truth-value substantially shapes Worker selection heuristics and the
Phase 6a/6b lane decision (DEC-0014).

**Decision.** **Phase 1c empirical comparison**, run after the DEC-0033 CoT-gap fingerprints land so the configurations
can be calibrated per-Worker. Hold task fixed; vary `(worker_size, cot_budget)` across at least four configurations:

- Small Worker (Qwen2.5-Coder-1.5B or Llama-3.2-3B) × `linear` budget (4096 reasoning tokens, full retention).
- Small Worker × `polynomial` budget (16384 reasoning tokens, full retention).
- Large Worker (Qwen2.5-Coder-14B or comparable) × `logarithmic` budget (256 reasoning tokens, truncate-on-cap).
- Large Worker × `linear` budget.

Measure on a sequential-task subset of `benchmarks/dan_tasks/` (math, dependency resolution, multi-step planning) using
**wall-clock task- completion-time as primary metric** per the [Speed paper](../paper-notes/2502.16721v1.md), with
secondary metrics tok/s, RSS, TTFT, output-quality score.

Results land in `benchmarks/results/cot_length_vs_size_<YYYY-MM-DD>.json`. The result feeds: (a) the Phase 6a/6b lane
decision in DEC-0014 (if small-with-CoT wins, the case for a small fine-tuned native-1-bit Worker strengthens), and (b)
the router's per-task-class dispatch heuristics in DEC-0031 (default `cot_budget` per task class informed by which
configuration wins where).

**Consequence.** A core architectural claim from the memory-pillar synthesis becomes empirical rather than asserted. If
small-with-CoT wins as predicted, Phase 6 lane bias shifts toward smaller models; if not, the existing larger-Worker
preference is validated. Either outcome is informative. Reversal cost low — the experiment is a benchmark run, not an
architecture commitment.
