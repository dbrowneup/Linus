# Fresh landscape + top-questions reconstruction (no-peek)

**Experiment date:** 2026-05-16
**Branch:** `experiment/fresh-landscape-reconstruction`
**Base SHA:** `9b91b66` (main)
**Author:** Claude Opus 4.7 worker, commissioned by Dan via Maestro spec.

## What this experiment is

A **blank-slate reconstruction** of Linus's four landscape-and-top-questions
documents using only the 27 synthesis documents (15 thematic + 12 cluster) as
input. The objective is to test whether the corpus's existing landscape
structure has come to constrain what the syntheses surface — i.e., whether
re-deriving the landscape from the syntheses arrives at the same shape (a
convergence signal) or at a different one (a divergence signal Dan can use as
calibration).

## Forbidden-list constraint

During composition the following files were **not read**:

- `docs/landscapes/total-landscape.md`
- `docs/landscapes/synthesis-landscape.md`
- `docs/landscapes/paper-landscape.md`
- `docs/landscapes/repo-landscape.md`
- `docs/questions/top-questions.md`
- `docs/questions/open-questions.md`
- `docs/questions/answered-questions.md`

The constraint was honored throughout the composition of
`fresh-total-landscape.md`, `fresh-synthesis-landscape.md`, and
`fresh-top-questions.md`. The forbidden files were consulted only at the very
end, during the final paragraph of `composition-notes.md`, to produce the
convergence-vs-divergence reflection.

## What this produced

- `fresh-total-landscape.md` — cross-corpus rollup, organized by maturity-tier
  (validated → in-flight → speculative).
- `fresh-synthesis-landscape.md` — synthesis-doc rollup, organized by load-bearing
  function (substrate / behavioral / domain / measurement / commercial).
- `fresh-top-questions.md` — working agenda of ~20 open questions, tiered by
  impact-on-next-action.
- `composition-notes.md` — meta-commentary written after the three documents
  above were complete, including the post-hoc convergence/divergence reflection.

## How to read it

If you are the grader (Dan), the cleanest comparison is to diff the structure
of `fresh-total-landscape.md` against `docs/landscapes/total-landscape.md` and
of `fresh-top-questions.md` against `docs/questions/top-questions.md`.

If you are a future Maestro or Worker session: this experiment is a
point-in-time document, not load-bearing. It records what one Worker session
arrived at when handed the syntheses alone. The canonical landscape and
top-questions documents remain in `docs/landscapes/` and `docs/questions/`.

## When it ran

Composed in a single session on 2026-05-16. Total wall time including read
pass: roughly 2.5 hours.
