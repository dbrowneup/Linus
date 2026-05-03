## DEC-0012 — pmetal is the primary Phase 1b inference backend candidate

**Date:** 2026-05-03
**Status:** accepted (gate verdict pending Phase 1b LoRA + serve + comparative benchmark)

**Context.** Phase 1b pmetal evaluation in progress. Build from source successful;
smoke tests pass; initial impressions strongly positive. The evaluation must still
complete: LoRA trial, serve trial, comparative benchmark vs. Ollama, and the verdict
ADR. Sub-decisions about build flags, concurrency target, and dependency risk needed
answers regardless of the verdict.

**Decision.** pmetal is the lead candidate for Phase 2a serving and Phase 6 training
backbone. For Phase 1b: build with `--features serve,mlx,trainer` (defer
`ane,distill,data` to their phases). Concurrency target for the verdict is
single-request tok/s + RSS; 5-concurrent is a Phase 2a concern. Dependency risk
mitigation: pin a commit, document the Ollama+mlx-lm-ft fallback in the forthcoming
Phase 1b verdict ADR (id assigned at authoring time), and revisit quarterly.

**Consequence.** Phase 1b scope is well-defined and execution-ready. Resolves the
benchmark plurality question and the build-flags question; the LoRA + serve +
benchmark trio remain as the executable verdict. The fallback path is fully
public-API and well-understood.
