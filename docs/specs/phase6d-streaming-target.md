# Phase 6d Streaming Inference Target Spec

**Date:** 2026-05-06 **Status:** proposed **Owner:** Dan **Phase:** 6d (after Phase 6a fine-tune is complete)

**Related ADRs:** DEC-0010 (mlx-flash adoption), DEC-0014 (flash-streaming framing narrowed to 30B+ post-Bonsai)

---

## Goal

Define the concrete model target and throughput success criterion for the Phase 6d flash-streaming inference
experiment, so that when Phase 6 begins there is no ambiguity about what "success" means. Phase 6d uses mlx-flash
(Matt Wong's weight-streaming library) to stream a 30B+ fine-tuned model from SSD, achieving sustained throughput
comparable to smaller native-speed models.

---

## Why 30B+ and not smaller

Bonsai 8B has a ~1.75 GB weight footprint and fits comfortably in unified memory at native or low-bit precision. BitNet
2B4T is smaller still. Neither needs streaming. mlx-flash is appropriate only when the model genuinely exceeds the 32 GB
unified memory budget. The original Phase 6d framing ("dense fine-tuned 8B exceeds RAM") is obsolete post-Bonsai;
DEC-0014 narrowed the target to 30B+ accordingly.

---

## Target model candidates

| Candidate | Size | Notes |
| --- | --- | --- |
| Linus-branded Qwen3-32B LoRA | ~65 GB FP16; ~18 GB Q4 | Post-Phase-6a fine-tune on Dan's KB corpus. If Q4-quantized it may fit in RAM; stream the FP16 or Q8 version from SSD to test the streaming path |
| Opportunistic ternary 30B+ | TBD | PrismML or community releases by Phase 6. Weight footprint likely < FP16 but still streaming-relevant at 30B+ |

Primary target: **Linus-branded Qwen3-32B LoRA** streamed from SSD at FP16 or Q8 precision. If ternary 30B+ weights
are available by Phase 6, run them in parallel as C2.

---

## Success criteria

| Metric | Target | Notes |
| --- | --- | --- |
| tok/s sustained | ≥ 15 tok/s | On M1 Max, streaming from internal or external SSD |
| Time to first token (TTFT) | ≤ 3 s | Acceptable for single-user interactive use |
| RSS peak | ≤ 28 GB | Leaves 4 GB headroom in unified memory |
| Dan task suite (20-task sample) | ≥ C4 baseline | Does the larger streamed model close the quality gap vs. Qwen3-8B native-speed? |

If tok/s < 15 but quality uplift on Dan tasks is measurable, record the tradeoff and surface to Maestro for a
keep-or-discard decision. A streaming model that is slower but substantially better may still be worth deploying for
overnight batch tasks.

---

## Methodology

Apply the autoresearch methodology (set a metric, set a goal, iterate until hit, keep-or-revert by git):

1. Establish the Phase 1c FP16 baseline for Qwen3-32B on Dan task suite (20 tasks) — this is the quality ceiling.
2. Run mlx-flash with default SSD-streaming configuration. Record tok/s, TTFT, RSS, quality.
3. Iterate on chunk size, prefetch policy, and quantization until the 15 tok/s target is hit or a natural plateau is
   reached.
4. At plateau, surface to Maestro with the measured Pareto position (tok/s vs. quality vs. RAM).

---

## Relationship to flash-moe

Flash-moe (Dan Woods, Metal/Obj-C) is a methodology reference — not vendored and not the implementation. The key
empirical lesson from flash-moe applies directly: the 9.8 GB Metal LRU cache wrapping mmap'd weight shards _hurt_
throughput by 38%; deleting it and trusting the macOS unified page cache produced the speedup. Do not replicate that
mistake. mlx-flash should be run without additional application-level caching layers over the mmap'd SSD weights.

---

## What is NOT in scope

- Bonsai 8B, BitNet 2B4T, or any model < 20B — these fit in RAM and should use native-speed inference.
- Streaming-based training (optimizer states on SSD) — this is open research territory; deferred past Phase 8.
- Multi-device streaming — Phase 8b hardware expansion.

---

## Related

- ROADMAP.md Phase 6d
- DEC-0010 (mlx-flash adoption decision)
- DEC-0014 (streaming target narrowing)
- `docs/syntheses/repo-clusters/g1-apple-silicon.md` — flash-moe empirical findings
