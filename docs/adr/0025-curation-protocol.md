## DEC-0025 — Curation protocol for `repos/`, `context/`, `docs/`

**Date:** 2026-05-03 **Status:** accepted

**Context.** Linus accumulates content rapidly: cloned repos, papers, notes, synthesis docs. Without a curation
protocol, `repos/` and `context/` and `docs/` grow into junk drawers; without a removal protocol, removed content's
existence becomes opaque to future planning sessions. Healthy knowledge management requires both growth and pruning,
with memory of what was pruned and when.

**Decision.** Adopt a lightweight curation protocol covering: (a) when/why content is added (with rationale captured in
synthesis or repo notes); (b) cadence of review (quarterly); (c) explicit archive/removal pathway; (d) **memory of what
was removed and when** via `docs/curation-log.md`. The Algorithm is applied at each curation-review checkpoint. Protocol
documented in `docs/curation-protocol.md` and indexed in CLAUDE.md Engineering Conventions.

**Consequence.** Content can grow boldly because pruning is principled. Removed content remains discoverable for
reflection. Quarterly cadence makes the protocol sustainable.
