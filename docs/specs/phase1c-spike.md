# Phase 1c Worker-Selection Spike Spec

**Date:** 2026-05-06 **Status:** proposed **Owner:** Dan **Phase:** 1c (after Phase 1b pmetal verdict)

**Related ADRs:** DEC-0006 (pmetal Phase 1 eval), DEC-0013 (BitNet 2B4T spike), DEC-0034 (worker-size vs CoT
length), DEC-0049 (pmetal vs PrismML deferred to Phase 1b)

---

## Goal

Determine the joint cost / quality / latency Pareto position of four Worker configurations on a 20-task sample of
`benchmarks/dan_tasks/`. The result is a Pareto chart that informs Phase 2a Worker-selection policy: which
configuration(s) to default to, under what task-class conditions to switch, and whether any configuration is
dominated and can be retired.

---

## Four configurations

| Config | Model | Backend | Quantization | Notes |
| --- | --- | --- | --- | --- |
| **C1 — Bonsai 8B 1-bit** | PrismML Bonsai 8B | Bonsai `llama-server` or Ollama | 1-bit | 1.75 GB weight footprint |
| **C2 — PrismML ternary 8B** | PrismML ternary 8B (if GGUF export available) | Bonsai / llama.cpp | ternary (1.58-bit) | Contingent on GGUF convert working at time of spike |
| **C3 — BitNet 2B4T** | `HF1BitLLM/Llama3-8B-1.58-100B-tokens` via bitnet.cpp | bitnet.cpp, CPU-only | 1-bit ternary | DEC-0013 spike candidate; no GPU path |
| **C4 — FP16 baseline** | `Qwen2.5-7B-Instruct` or `Qwen2.5-14B-Instruct` | Ollama | FP16 / Q8 | Quality ceiling reference |

If C2 is not available at spike time (GGUF export fails or PrismML ternary weights are not published), run C1, C3, C4
and document C2 as deferred with the blocker noted.

---

## Measurements per configuration

For each of the 20 tasks, record:

1. **tok/s** — tokens per second (output tokens only, measured wall-clock from first to last token)
2. **time-to-first-token (ms)** — latency from request to first output token
3. **answer quality score (1–5)** — Dan's subjective score per task after blind review (scores assigned after all
   four configs complete the task, presented without config labels)
4. **Wh/prompt** — energy cost per prompt, estimated from `powermetrics --samplers cpu_power,gpu_power` at 1 Hz during
   each run, integrated over prompt duration

Recorded in `benchmarks/results/phase1c-<YYYY-MM-DD>.json` as a JSONL file with one record per (config, task) pair.

---

## 20-task sample

Pull from `benchmarks/dan_tasks/` — the 20-task smoke-test tier. If fewer than 20 tasks exist at spike time,
include all available and note the count. Task categories should span: genomics Q&A, metagenomics analysis plan,
Python code generation (bioinformatics), paper summarization (biochem). If any category is underrepresented, draft
one synthetic task for that category and mark it as synthetic in the JSONL.

---

## Smoke-test gate

Before the full 20-task run, run **one task per configuration** (the same task for all four). Verify:
- Each config produces a non-empty, coherent response.
- tok/s is in a plausible range (>1 tok/s for any config).
- Energy measurements are non-zero.

If any config fails the smoke gate, diagnose and fix before proceeding. Do not run the full suite against a broken
config.

---

## Success criteria

The spike is done when:
1. All four configs (or three, with C2 documented as deferred) have run all 20 tasks.
2. JSONL results file is committed to `benchmarks/results/`.
3. A Pareto chart (quality vs Wh/prompt; quality vs tok/s) is produced and committed alongside the results.
4. A `docs/adr/` amendment to DEC-0049 is written: "Phase 1b found pmetal covers / does not cover Bonsai 8B" (if
   Phase 1b verdict is available by this time).

---

## LAB-Bench canary note (from S2 resolution)

LAB-Bench JSONL benchmark files must **never** be placed in `context/papers/` or any directory the KB ingest pipeline
touches. LAB-Bench data goes in `benchmarks/` only. Any benchmark task derived from LAB-Bench questions must be
authored fresh (do not copy LAB-Bench questions verbatim) to avoid canary contamination of future LAB-Bench benchmark
runs.

---

## Spec owner

Dan reviews the Pareto output and decides Phase 2a Worker defaults. Claude Code (or a Linus Worker when the Phase 1e
loop is running) executes the measurement harness.
