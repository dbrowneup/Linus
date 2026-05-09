# Question Lifecycle (placeholder)

**Status:** stub captured 2026-05-08. Not yet a design spec.

## Why this exists

Through the R1 → R2 → R3 promotion arc, Dan and Maestro have been managing the question lifecycle manually: surfacing
candidate questions inside paper-notes, repo-notes, and syntheses; promoting a curated subset into
[`top-questions.md`](../questions/top-questions.md) per round; resolving with ADRs into
[`answered-questions.md`](../questions/answered-questions.md); back-flowing partial-resolution stubs into the source
notes. The mechanics work, but the cognitive load for the Maestro is high — keeping track of ~70 candidate questions
across 25 syntheses, deduping against ~70 already-promoted R2-NN items, deciding what's load-bearing enough to promote,
walking the answered-questions cross-references on each pass.

The pattern recurs as the project scales. As more notes accrue, more questions surface; as more decisions land, more
cross-references need updating. Manual management is the bottleneck.

## What a Linus-internal question registry could look like

This is not a design — it's a marker for a future design pass. The shape that suggested itself during the
synthesis-refinement consolidation:

- **Typed records.** Each question is a typed claim (`[!gap]` per the LLM Wiki synthesis claim typing) stored in the
  episodic-memory substrate (Layer C per DEC-0029) with a lifecycle field: `surfaced`, `triaged`, `promoted`,
  `partially-resolved`, `resolved`, `superseded`.
- **Surfacing.** Workers emit candidate-question records as part of their write-back contract (every task produces a
  deliverable + KB update proposals + open-questions-raised). The R3 batch above is the manual version of this output.
- **Promotion.** A periodic Maestro pass evaluates the queue, dedups, assigns Tier, writes promoted items to
  `top-questions.md`. Could be Maestro-only (high quality, slow) or assisted by a low-tier Worker that proposes a
  promotion list for Maestro confirmation.
- **Resolution.** When an ADR lands, the related question records flip to `resolved` with an ADR pointer. Stale
  partial-resolution stubs in the source notes get auto-updated, not manually swept.
- **Cross-referencing.** The registry holds the canonical link between question-id, source-note, ADR, and any
  cross-synthesis mention. Updating one updates all.

## Productization potential

The question-lifecycle pattern generalizes beyond Linus. Technical teams managing decision queues against research
corpora face the same problem (the entrepreneurship synthesis names structured-question-management as a candidate
commercial surface — productization downstream of structure, not upstream). Worth holding as a marker as the
biotech-team literature-intelligence offering crystallizes.

## Next step

Not a Phase 1 deliverable. Revisit when Phase 2 episodic-memory implementation has shipped (the substrate is the
prerequisite); when the Phase 3 spawner spec is written (Workers need to be able to emit candidate-question records as a
typed write-back); and after the R4 sweep, where the same manual process will recur and crystallize the pain points into
design requirements.

---

_Captured during the 2026-05-08 synthesis-refinement consolidation pass to avoid the idea sliding into a session note
and getting forgotten. Not designed; not scheduled. A handle for later._
