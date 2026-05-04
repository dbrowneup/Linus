## DEC-0013 — BitNet 2B4T spike adopted as the first concrete Phase 1c experiment

**Date:** 2026-05-03 **Status:** accepted

**Context.** Multiple paper notes (BitNet 2B4T, bitnet.cpp, BitNet Distillation) plus the cross-cutting paper-landscape
question identified a single-experiment spike that simultaneously answers the BitNet quality-cost question, the
bitnet.cpp Apple-Silicon throughput question, and the 1-bit Worker viability question. Phase 1c needed a first concrete
experiment.

**Decision.** Pull `bitnet-b1.58-2B-4T-gguf`, build bitnet.cpp on M1 Max, benchmark against Ollama-served Qwen2.5 and
Llama-3.2 in `benchmarks/dan_tasks/` using task-completion-time methodology (three-task schema: minimal / fixed-length /
open-ended). Spike output also seeds the Phase 1c benchmark sweep design.

**Consequence.** A single ~half-day-of-work experiment threads three Tier 1 / Tier 3 questions together. Result informs
the Phase 6 fine-tuning lane decision.
