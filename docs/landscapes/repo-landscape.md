# Repo Landscape — DEPRECATED

> **Status: DEPRECATED 2026-05-04.** This document was retired during the post-fan-out integration pass that
> grew the cloned-repo collection from 12 to ~80 and produced the 10 cluster syntheses in
> [`docs/syntheses/repo-clusters/`](../syntheses/repo-clusters/). Its narrative content has been absorbed into
> those clusters and the relevant thematic syntheses; its navigation function moved to
> [`docs/repo-notes/INDEX.md`](../repo-notes/INDEX.md).

## Where the content went

- **Per-repo notes:** [`docs/repo-notes/`](../repo-notes/) (80 files, unchanged).
- **Navigation lookup** (repo → cluster + covering thematic syntheses):
  [`docs/repo-notes/INDEX.md`](../repo-notes/INDEX.md).
- **Cluster-level analysis** (within-cluster patterns, integrate/study/ignore verdicts, per-cluster Phase
  implications): the 10 cluster syntheses in [`docs/syntheses/repo-clusters/`](../syntheses/repo-clusters/).
- **Cross-cluster integration** (the four-layer model: inference / harnesses / methodology / data sovereignty;
  phase-by-phase entry; key tensions): [`docs/landscapes/total-landscape.md`](total-landscape.md) and
  [`docs/landscapes/synthesis-landscape.md`](synthesis-landscape.md).
- **Verdicts and decisions:** the per-cluster syntheses carry the Integrate/Study/Ignore call for each repo within
  that cluster; the [`fan-out-session-summary-2026-05-04.md`](../specs/fan-out-session-summary-2026-05-04.md) is
  the read-out for the run that produced them.

## Why it was retired

When this document was written, the four-layer model (inference / harnesses / methodology / data sovereignty) over
12 repos was readable. After the post-fan-out expansion to ~80 repos, that shape stretched into a wall and the
right place to look was no longer here — it was the cluster synthesis or the per-repo note. The original four-layer
framing has been preserved, in updated form, in `total-landscape.md`'s "Architectural layers" section; the
verdict-bearing analysis lives in the cluster syntheses.

This stub preserves link integrity for any document that still references `repo-landscape.md`.
