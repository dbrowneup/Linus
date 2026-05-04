## DEC-0028 — Memory architecture promoted to Phase 2 first-class pillar

**Date:** 2026-05-03 **Status:** accepted

**Context.** Erik Garrison's January 2025 essay _Memory makes computation universal, remember?_ and its companion arXiv
proof paper (2412.17794), read together with the eleven supporting papers now noted in [paper-notes/](../paper-notes/)
under the memory-pillar grouping, supply a formal complexity-theoretic argument that universality requires only two
primitives — recursive state maintenance and reliable history access — and that single-pass transformers satisfy neither
(TC0 ceiling). The empirical evidence (Kojima's emergence-at-scale CoT gap, Sparks Section 8's predictable failure
modes, ARC-AGI's 172× compute premium for the last 9 percentage points) makes the gap operationally visible. Ayesha
Mughal's March 2026 practitioner article on context-window degradation supplies the operational shape inside
hosted-Claude sessions. Existing Linus planning treated long-term memory as deferred until concrete use cases surface;
the corpus makes the case that memory is _upstream_ of every concrete Phase 2 use case (carrying a long task across many
tool calls, resuming a project across sessions, building a durable assistant view of Dan's work) rather than downstream
of one.

**Decision.** Memory architecture is **promoted from a Phase 3+ deferred concern to a Phase 2 first-class architectural
pillar** and named as the fourth named layer in `total-landscape.md`'s "three layers Linus has to build" section (now
four). The [memory synthesis](../syntheses/memory-synthesis.md) is the synthesis input;
[`docs/specs/memory-architecture.md`](memory-architecture.md) is the new Phase 2 deliverable, drafted as part of this
planning roll-up so the spec lands alongside the resolutions rather than as a downstream Worker task. The spec walks
through Layers A–D (intra-step latent / within-session scratchpad / cross-session episodic / semantic-knowledge), the
four sub-requirement obligations from Garrison's framework (addressability, disambiguation, temporal order, integrity),
the substrate choice per layer (or "deferred to Phase 6+ pending measurement" where the corpus has not converged), the
read/write API the orchestration layer exposes, and the contract between memory layers and the Maestro/Worker protocol.
The spec is a prerequisite for Phase 2a orchestration backend implementation; other Phase 2 work (chat UI 2b, KB
integration 2c) proceeds in parallel.

This ADR also folds in the **memory budget accounting** sub-decision (M12): ARCHITECTURE.md gains a "Memory Budget
Accounting" section naming memory budget as a first-class architectural quantity, with o3 at ~$1.15M for 91.5% on
ARC-AGI-1 as the cautionary upper bound (cost of brute-forcing memory reliability through compute) and
human-with-pen-and-paper as the lower bound. Linus's design target sits in the middle: tens of dollars of electricity
per day on a single M1 Max, with the architectural pressure to narrow the gap to the lower bound through substrate
(DEC-0029), discipline (DEC-0030, DEC-0031, DEC-0032), and measurement (DEC-0033, DEC-0035). The audit-log telemetry
from DEC-0030/0031/0032 supplies the data that makes implicit memory-cost choices legible.

**Consequence.** Phase 2 scope expands to include the memory-architecture spec and its v0 implementation. Phase 3
retains parallel-write coordination (DEC-0022) and hybrid retrieval but those are now informed by the spec rather than
designed without it. The o1 anti-pattern (silently truncating reasoning between turns) becomes a non-conformance
condition (DEC-0030). Substrate experiments (TTT per DEC-0029/DEC-0037, minGRU per DEC-0038, Coconut per DEC-0042) are
sequenced behind Phase 1 viability spikes and the v0 substrate, so Phase 2 ships regardless of their outcomes. Reversal
cost is high — every downstream Worker integration, router primitive, and benchmarking choice will assume the pillar
exists.
