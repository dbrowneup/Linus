## DEC-0016 — [KB-spec] split convention for KB-impacting specs

**Date:** 2026-05-03 **Status:** accepted

**Context.** During the planning session of 2026-05-03, multiple Tier 1, Tier 2, and Tier 3 questions surfaced that
primarily impact KnowledgeBase rather than Linus (KB data model, ingest quality gate, embedding ablation, keyphrase
pipeline, parallel-worker write coordination, KB architecture spec). KnowledgeBase is a separate repo (per DEC-0003);
cross-repo planning needs a clean handoff convention.

**Decision.** Spec-parts that primarily impact KnowledgeBase are tagged **[KB-spec]** and split into a sub-document
under `docs/specs/kb/` for delivery in the KnowledgeBase repo (executed by Claude, or eventually by Linus, in
partnership with Dan). Linus's planning-update-spec carries the cross-cutting parts; [KB-spec] parts are the parallel
sub-document.

**Consequence.** Cross-repo work has a clear handoff. KB repo work doesn't pollute Linus's planning artifacts and vice
versa. Maestro can route specs to the right working tree.
