## DEC-0022 — Parallel Worker KB write coordination: serialized writes + write-time contradiction surfacing

**Date:** 2026-05-03 **Status:** accepted

**Context.** The write-back rule (every Worker task ends with KB update proposals) is unambiguous for a single Worker.
Phase 3 multi-agent fan-out introduces concurrent proposals on the same KB pages. Last-write-wins silently loses
concurrent updates; fully-automated reconciliation is premature complexity.

**Decision.** **Serialized writes through a coordinator + write-time contradiction surfacing.** Workers don't write
directly; they emit JSON-shaped diff proposals. A single coordinator process applies proposals in order. Conflicts on
the same entity/page/triple flag for human (Dan/Maestro) review before merge. Git-branch-per- ingest is the persistence
layer underneath: each Worker's proposals land on `agent/<task-id>/<slug>` branches, the writer process resolves merges
on `develop` (per DEC-0011 gitflow graduation at Phase 3). Contradiction detection at write time, not read time.
**[KB-spec]** item: spec target `docs/specs/kb/parallel-worker-write-coordination.md`.

**Consequence.** Concurrent fan-out has well-defined semantics. No silent data loss. Conflicts are surfaced for human
judgment, not auto-resolved.
