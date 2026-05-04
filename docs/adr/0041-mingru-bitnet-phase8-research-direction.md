## DEC-0041 — minGRU + BitNet cross-product as Phase 8 long-horizon research direction

**Date:** 2026-05-03 **Status:** accepted

**Context.** The Garrison-thread corpus collectively points at a substrate the existing BitNet line and the minGRU paper
jointly enable but neither has built: **recurrent + 1-bit + Apple-Silicon-friendly** — minGRU-style parallel-scan
recurrence with BitLinear ternary gates. Recurrent (no quadratic attention), 1-bit (no FP16 multiplies),
Apple-Silicon-friendly (parallel scan on the GPU + adder arrays on the ANE). The Related Work section of
[Feng et al. (2410.01201)](../paper-notes/2410.01201v3.md) cites Zhu et al. 2024b ("scalable matmul-free language
modeling") which already combines HGRN-style recurrence with ternary quantization, so the cross-product is being
explored upstream. For Linus, this is the most extreme hardware-friendly substrate the corpus collectively points at —
and also the most experimental.

**Decision.** **Confirmed as a Phase 8 long-horizon research direction; gated on the DEC-0038 minGRU spike result.**

- No Phase 6/7 work is gated on it.
- Promotion from "research direction" to "planned deliverable" requires both DEC-0038 graduation (minGRU passes the MLX
  viability bar of within ~2× of paper's T4 numbers and matched perplexity) **and** DEC-0037 graduation (TTT or some
  other parametric-memory substrate validates Apple-Silicon training viability for ternary architectures), at which
  point Phase 8 gets a concrete sub-deliverable spec.
- Until then, named in [`docs/landscapes/total-landscape.md`](../landscapes/total-landscape.md) Crossing 1 / Crossing 5
  / gaps section as the long-horizon synthesis of those crossings, and that is enough.

**Consequence.** A genuinely interesting research direction stays named without consuming Phase 6/7 budget on
speculation. Phase 8 has a concrete target conditional on Phase 1 spike outcomes, so the planning artifacts remain
coherent. Reversal cost negligible — this is a research pointer, not an implementation commitment.
