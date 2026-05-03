## DEC-0023 — Output interface: balanced bullets+prose, citations first-class, opt-in verbose; Linus reframed as personal LLM Wiki at scale

**Date:** 2026-05-03
**Status:** accepted

**Context.** The cognitive throughput papers (Zheng-Meister + Sauerbrei-Pruszynski)
quantify human conscious review at ~10 bits/s. Parallel Worker fan-out generates
zero throughput gain unless Maestro outputs are compressed before review. But
auditability matters — citations and traceability must be first-class for a
scientific KB. And bullet dumps without prose are themselves cognitively impoverished.

**Decision.** Adopt the 10-bits/s framing as a Phase 2 chat-UI design principle.
Synthesized Maestro outputs use **balanced bullets + prose** — bullets for
enumerable items, prose for reasoning, context, narrative. **Citations and
traceability are first-class, not optional**: every synthesized claim links back
to source Worker outputs, KB entities, or paper-notes. Worker outputs preserved
for Maestro inspection (drill-down UI affordance). **Opt-in `/verbose`** for
unsynthesized full-Worker output viewing. Multi-Worker fan-out outputs always
pass through a Maestro-side synthesis step before reaching Dan, with citation
links preserved. **Linus reframed as a personal LLM Wiki at scale** — citations,
traceability, and write-back discipline are core to the vision, not optional.

**Consequence.** UI design constraint baked into Phase 2 scope. Worker outputs are
artifacts; synthesized summaries are the review interface; both coexist. VISION.md
gets a paragraph on the LLM Wiki framing tying to Maestro/Worker discipline.
