## DEC-0006 — pmetal evaluated as primary serving + training backend in Phase 1

**Date:** 2026-04-22
**Status:** proposed — decision gate in Phase 1

**Context.** pmetal is a comprehensive Apple Silicon ML platform (Rust, native Metal
kernels, ANE pipeline, LoRA training, distillation, OpenAI-compatible serving). It
potentially collapses "serving layer" and "training backbone" into one component.
Alternative: use Ollama for serving, mlx-lm for training.

**Decision.** **Evaluate pmetal seriously in Phase 1** (deliverable 1b) with comparative
benchmarks against Ollama on matched models. The Phase 1b verdict ADR (a forthcoming
ADR — id will be assigned at authoring time) will determine whether pmetal is adopted as
primary serving backend, training backbone, both, or neither.

**Consequence.** Commits Phase 1 time to a real evaluation instead of hand-waving.
Outcome may be "adopt pmetal fully" (big architectural win) or "Ollama for serving, mlx-
lm for training" (safer) or a hybrid. The evaluation itself is valuable regardless.
