# docs/questions/

Open-question lifecycle for Linus's planning work. Questions enter through `open-questions.md` (verbose archive),
graduate to `top-questions.md` (prioritized working set) when they become next-action-blocking, and exit to
`answered-questions.md` (resolved archive with ADR/PR pointers) once decided.

## Files

- [`top-questions.md`](top-questions.md) — the prioritized working set, tiered by how much each answer changes the
  next concrete action. Items numbered by sweep round: `R2-NN`, `R3-NN`, `R4-NN`, `R5-NN` (and the earlier `S-NN`,
  `M-NN`, `E-NN` ids from the 2026-05-04 round).
- [`open-questions.md`](open-questions.md) — the full unresolved backlog, organized as a verbose per-source archive
  (one section per repo-note / paper-note / synthesis where each question originated).
- [`answered-questions.md`](answered-questions.md) — the archive of resolved questions with their resolution evidence
  (ADR, PR, spec section, or session-log context). Cross-referenced from ADRs in [`../adr/`](../adr/).

## Lifecycle process

See [`../specs/question-lifecycle.md`](../specs/question-lifecycle.md) for the formal process: promotion criteria,
tier definitions, and resolution propagation rules. Round-by-round sweeps surface candidate questions from the corpus;
each round's promotions are noted in `top-questions.md` with their sweep-round prefix.

## Item shape

Each question is a single bullet with: bold ID + topic, a 1-2 sentence framing, references to the source synthesis or
repo-note, and (if applicable) a `_Partially resolved (DEC-NNNN): nuance._` or `_Framing refresh (YYYY-MM-DD): nuance._`
annotation when shipped reality has changed the question without closing it.
