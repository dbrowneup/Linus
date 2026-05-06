## DEC-0049 — pmetal vs. MLX-native PrismML fork: deferred to Phase 1b verdict

**Date:** 2026-05-06 **Status:** proposed — gate decision at Phase 1b

**Context.** Two inference backend paths exist for low-bit serving on M1 Max: (A) PrismML fork of MLX, vendored by
Bonsai with custom low-bit kernels (real maintenance liability — it diverges from upstream MLX); (B) pmetal, which
already ships fused low-bit kernels in production on Apple Silicon and subsumes a broader capability surface (training,
serving, kernel authoring). The native-low-bit-apple-silicon synthesis names this as the long-term lock-in question
before the inference layer hardens. A third path — (C) contributing upstream MLX scale-only quant support — is
available but requires open-source contribution lead time. Closes **S8** (deferred pending Phase 1b).

**Decision.** Default to Path C: wait for pmetal to subsume the Bonsai 8B use case, or for the Phase 1b verdict to
settle the question empirically. The Phase 1b pmetal evaluation (DEC-0006, DEC-0012) must explicitly answer: "Does
pmetal serve Bonsai 8B ternary / 1-bit at ≥ Bonsai's own serving throughput (tok/s) on M1 Max?" If yes: PrismML fork
is not incurred; pmetal is the unified inference backend. If no: new ADR (proposed sub-ADR to this one) picks between
Path A (pin PrismML fork) and Path B (contribute upstream MLX quant support), informed by the Phase 1b latency gap and
PrismML's current maintenance trajectory.

**Resolution criteria.** Phase 1b produces `docs/specs/phase1b-verdict.md` covering pmetal coverage of the Bonsai 8B
use case. That document gates this ADR's transition from `proposed` to `accepted` (Path C confirmed) or `superseded`
(new ADR for Path A or B).

**Consequence.** No inference backend lock-in before evidence. The PrismML fork maintenance liability (diverging MLX
fork, custom kernels, no upstream support) is not incurred prematurely. If pmetal coverage is confirmed at Phase 1b,
this question closes permanently.
