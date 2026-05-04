## DEC-0026 — Planning write-back cadence: Maestro/Dan + Claude planning sessions refine core files at session close

**Date:** 2026-05-03 **Status:** accepted

**Context.** The LLM Wiki synthesis's write-back rule ("every substantive task produces two outputs: the deliverable and
KB updates") was framed for Worker tasks. Practitioner experience during the planning session of 2026-05-03 surfaced
that this discipline applies equally to Maestro/Dan + Claude planning sessions — without explicit write-back, planning
insights evaporate into chat history.

**Decision.** Adopt **planning write-back cadence** as a CLAUDE.md Engineering Convention. At the close of every
multi-question planning session, allocate time for core-file write-back: refining CLAUDE.md, VISION.md, ROADMAP.md,
ARCHITECTURE.md, SAFETY.md, DECISIONS.md, and the relevant landscape/spec docs. The planning-update-spec.md is the
natural artifact for this routing.

**Consequence.** Planning insights compound into the knowledge base rather than evaporating. Session boundaries become
natural write-back checkpoints. Future planning sessions inherit a refined substrate.
