## DEC-0014 — Phase 6 fine-tuning lane decision deferred; Phase 6a commits to FP16-LoRA on genomics regardless

**Date:** 2026-05-03 **Status:** accepted

**Context.** Phase 6 has three candidate lanes: native-1-bit (Bonsai/2B4T), BitDistill (FP16 → 1.58-bit), and FP16-LoRA
fallback. Each requires different infrastructure investment. Picking the lane shapes Phase 6 entirely, but the right
lane depends on Phase 1c BitNet benchmark results and the genomics-vs-coding fine-tune target question.

**Decision.** Defer the lane decision until Phase 1c BitNet benchmark data lands and the genomics-vs-coding target is
settled. **Phase 6a commits to FP16-LoRA on a genomics/biochem corpus regardless** — safe foundational work and an
always-available baseline. Explicit decision gate at the Phase 6a/6b boundary.

**Consequence.** Phase 6a is unblocked. Lane decision is informed rather than speculative. FP16-LoRA never blocks Phase
6 deliverables.
