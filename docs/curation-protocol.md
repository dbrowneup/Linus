# Curation Protocol

Lightweight protocol for managing growth and pruning of `repos/`, `context/`, and
`docs/`. Adopted in DEC-0025. Memory of removals is captured in
[curation-log.md](curation-log.md).

## Principles

1. **Growth is encouraged.** Cloning a reference repo, adding a paper, drafting a
   synthesis note are all low-cost actions. The default is `add`.
2. **Pruning is principled.** At quarterly review checkpoints, apply The Algorithm:
   does this content still earn its keep? If not, archive or remove.
3. **Memory of pruning is preserved.** Every removal is logged in curation-log.md
   with rationale, timestamp, and (where applicable) a SHA pointer to the last
   commit that included the content.

## When to add

- A repo that informs an active phase or open question.
- A paper that resolves or sharpens an open question.
- A synthesis note that consolidates ≥3 separate threads of reasoning.
- A spec that names a deliverable.

Add with a one-paragraph rationale captured in the originating note (synthesis,
repo-note, paper-note).

## When to archive vs. remove

- **Archive** (move to `docs/archive/<area>/<name>.md`): historical reference value
  but no current relevance; might inform future work; should remain searchable.
- **Remove** (delete via `git rm`): superseded, factually wrong, or cleanly
  redundant with newer material. Always logged.

Archived content stays in git history regardless; the archive path is for current-
state navigation cleanliness.

## Quarterly review checklist

At the start of each quarter:

1. **`repos/`:** for each cloned repo, ask: does any active phase still reference
   it? Is its purpose now superseded by another resource? Pre-emptive: don't
   remove repos cited in active synthesis notes.
2. **`context/`:** review `papers/`, `notes/`, `pics/` for items unread/unused over
   the last quarter. Archive (not delete) low-engagement items.
3. **`docs/`:** review `repo-notes/`, `paper-notes/`, `syntheses/`, `landscapes/`
   for stale claims. Update inline rather than removing if the document still
   serves; remove only if cleanly superseded.
4. **Log every removal/archive in `curation-log.md`** with: date, path, action,
   rationale, last-commit-SHA pointer.
5. **Apply The Algorithm to surface speculative additions** that haven't earned
   their keep yet.

## Cadence

- Quarterly full review (March, June, September, December).
- Ad hoc removal of clearly-superseded items at any time, but logged the same way.
