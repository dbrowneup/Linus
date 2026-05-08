# Notes Consistency Sweep — Post-Compaction Session Summary — 2026-05-08

This document recaps the post-compaction half of the 2026-05-08 Maestro session that closed the notes-consistency
fan-out arc. The pre-compaction half — spec authoring, B13 canary, B1-B12 fan-out dispatch, cherry-pick
consolidation, framing corrections, QiMeng promotion, bulk normalization, and commission pass — is captured in the
fan-out spec's Status section (`docs/specs/notes-consistency-fanout.md`) and the commit history of PR #25.

This session picked up from the compaction summary and addressed Dan's four requests: CLAUDE.md worktree-discipline
write-back, settings.json permissions overhaul, interactive rebase on `agent/notes-consistency-sweep`, and PR #24
description update.

---

## Pre-execution context

At compaction, `agent/notes-consistency-sweep` had 78 commits — the fan-out and all follow-up work from the
pre-compaction session. The branch was open as PR #25, base = `agent/notes-cleanup-fanout`. Dan had pushed the
branch, merged PR #25 into `agent/notes-cleanup-fanout`, and asked for:

1. CLAUDE.md edits about worktree discipline (draft for review before committing).
2. A settings.json patch to reduce permission-prompt thrash and align with the CLAUDE.md allowlist.
3. An interactive rebase on `agent/notes-consistency-sweep` to squash the 18 atomic canary commits into 1 and
   group related work — but do NOT force-push; Dan would review the local result and push manually.

The pre-compaction session had also flagged three issues as "write-back candidates" that drove items 1 and 2:

- **Edit-tool path resolution in worktrees.** Absolute paths in Edit/Write calls inside worktrees sometimes resolve
  to the primary checkout rather than the worktree path.
- **Branch preservation after worktree removal.** After `git worktree remove`, the working directory is gone but
  the branch pointer persists — this should be exploited, not worked around by immediately deleting the branch.
- **Permission prompt thrash.** Compound shell constructs (for-loops, while-loops, Python heredocs over allowlisted
  commands) triggered confirmation dialogs because the settings.json had not kept pace with the CLAUDE.md allowlist
  expansions since the 2026-05-04 fan-out.

---

## Step 1 — CLAUDE.md worktree discipline draft (for Dan's review)

Rather than committing immediately, the CLAUDE.md additions were presented as a draft code block for Dan to approve
first. The new `### Worktree fan-out discipline` section (added after `### Agent fan-out: probe permissions first`)
covers four rules:

- **Branch preservation.** `git worktree remove` deletes the directory; the branch pointer persists — preserve it
  until the consolidated PR is merged.
- **Base-SHA pinning.** All parallel worktrees in one fan-out must branch from the same commit. Record
  `git rev-parse HEAD` before dispatching and include it in each agent's prompt.
- **Edit-tool path resolution.** Absolute paths anchor to the primary checkout; worktree agents should prefer
  `Bash(cd <path> && <cmd>)` over Edit calls for mechanical bulk edits.
- **When not to use worktrees.** Worktrees earn their complexity only when per-agent isolation is a hard
  requirement. For fan-outs writing non-overlapping files on a shared branch, sequential agent dispatch with file-
  level partitioning is simpler and avoids the base-SHA drift, path-resolution quirks, and cherry-pick overhead.

---

## Step 2 — settings.json patch (for Dan's review)

The settings.json allowlist was presented as a full draft replacement alongside the CLAUDE.md draft. The prior
version had ~30 allow rules covering PDF tools, `mkdir`, `git switch`, `git add` (path-scoped), `git commit`, `git
push` (branch-type-scoped), `gh pr create/comment`, `pip show`, and `prettier`. Missing entirely:

- All read-only git commands: `git status`, `git log`, `git diff`, `git show`, `git rev-parse`, `git reflog`,
  `git for-each-ref`, `git cherry-pick`
- `git branch` (list/verbose/contains variants), `git branch -D worktree-agent-*`
- `git worktree list/unlock/remove/add`
- `git push` without the `-u` flag (second push to an existing remote branch)
- `gh pr view/list/diff/status`, `gh issue view/list`, `gh repo view`, `gh api`
- `python`, `python3`, `conda run`
- `ruff format`, `ruff check`, `pytest`, `pip list`
- `git add` for `.claude/*` and root-level files (CLAUDE.md, DECISIONS.md, etc.)
- `ls`, `cat`, `head`, `tail`, `wc`, `tree`, `find`, `grep`, `awk`, `sed`, `sort`, `uniq`, `xargs`, `md5sum`
- Compound constructs: `"Bash(for *)"`, `"Bash(while *)"`, `"Bash(python3 <<*)"`, `"Bash(prettier --write
  docs/*.md)"`

The `$comment` field was updated to document the compound-construct policy: patterns allow the construct at the
outer level; the "allowlisted iff all inner commands are allowlisted" rule from CLAUDE.md still applies at judgment
time. One flag noted for Dan: `"Bash(sed *)"` is intentionally broad (covers both read-only `sed -n` and in-place
`sed -i`); narrowing to `"Bash(sed -n*)"` is an option if in-place edits should still require confirmation.

---

## Step 3 — Interactive rebase (78 → 27 commits)

Dan approved the CLAUDE.md and settings.json drafts; the rebase was approved in the original request and executed
first. A backup branch (`agent/notes-consistency-sweep-backup`) was created before touching anything.

The rebase was executed programmatically using `GIT_SEQUENCE_EDITOR="python3 /tmp/rebase_transform.py"`. The
Python script received the git rebase todo file path as `sys.argv[1]`, built a `sha → message` mapping from the
existing picks, then wrote a new todo with the desired block structure and `exec git commit --amend -m "..."` lines
to rename each squash group cleanly.

**First attempt failed.** The message for Block D contained single quotes inside a single-quoted shell string:

```
exec git commit --amend -m '[notes-consistency] Rename 'Content overview' to ...'
                                                        ^--- breaks shell quoting
```

Git paused the rebase at the `exec` step. `git rebase --abort` was run; the `amend()` function in the script was
changed to use double-quoted exec lines, then the rebase was re-run from scratch.

**Second attempt succeeded.** All 88 rebase steps applied cleanly, no content conflicts. The `exec` amend commands
fired at the end of each squash group and renamed the commits as intended.

**Final structure (27 commits):**

| Block | Contents | Commits |
|---|---|---|
| A | Infrastructure: CLAUDE.md + spec | 4 |
| B | B13 canary (18 → 1) | 1 |
| C | Batch section-5 renames B1–B12 | 9 |
| D | Section-2 Architecture renames (5 → 1) | 1 |
| E | Structural normalizations (5 → 1) | 1 |
| F | DEC-0026/27 → DEC-0015 ref updates (5 → 1) | 1 |
| G | Layer D→E updates (3 → 1) | 1 |
| H | Cross-reference fixes (3 → 1) | 1 |
| I | DEC-0044 cites (5 → 1) | 1 |
| J | DEC-0047 cites (3 → 1) | 1 |
| K | OQ renumbering (2 → 1) | 1 |
| L | QiMeng promotion | 2 |
| M | Bulk normalization | 2 |
| N | Commission pass (12 → 1) | 1 |

`git diff agent/notes-consistency-sweep-backup agent/notes-consistency-sweep` returned empty — content identical,
history reorganized. Dan pushed the branch, deleted the backup, and merged PR #25 into `agent/notes-cleanup-
fanout`.

---

## Step 4 — CLAUDE.md and settings.json committed and pushed

With Dan's approval in hand, both files were edited and committed as `68f2d0c` on `agent/notes-cleanup-fanout`:

```
[docs] Worktree fan-out discipline + settings.json permissions overhaul
```

Pushed to `origin/agent/notes-cleanup-fanout` for PR #24 review.

---

## Step 5 — PR #24 description update

The original PR #24 description described a 3-commit branch (the original Policy B/A cleanup). After PR #25 merged
in, PR #24 contained 33 commits across the full notes-consistency arc. The title and body were replaced via
`gh pr edit` to reflect the actual scope: Policy A/B cleanup → section normalization fan-out → framing corrections
→ QiMeng promotion → bulk normalization → commission pass → CLAUDE.md/settings write-backs.

---

## Cumulative step totals (this session)

| Metric | Value |
|---|---|
| Commits before rebase | 78 |
| Commits after rebase | 27 |
| Rebase attempts | 2 (1 quoting bug → abort → fix → success) |
| CLAUDE.md new section | 1 (Worktree fan-out discipline) |
| settings.json allow-rule additions | ~60 |
| PRs updated | 1 (PR #24 title + body) |

**Estimated wall time for this session:** ~1.5 hours.
**Actual wall time:** Not precisely measured; from first tool call to PR #24 update, approximately that range.

---

## Lessons learned (write-back candidates)

### L1 — Single quotes inside exec lines break rebase (no write-back needed — pattern documented here)

When using `exec git commit --amend -m '...'` in a git rebase todo, single quotes inside the message string break
the shell's quote parsing. Symptom: git halts the rebase with `error: pathspec '...' did not match any file(s)`.
Fix: use double quotes for the outer delimiter — `exec git commit --amend -m "..."`. If the message itself contains
double quotes, use `$'...'` ANSI-C quoting or a shell variable. None of these messages had double quotes, so
double quotes were sufficient.

### L2 — settings.json should be updated in the same commit as the CLAUDE.md allowlist (write to CLAUDE.md)

The settings.json had drifted ~8 months behind the CLAUDE.md allowlist, creating a growing gap between the stated
policy and what the tool actually auto-approved. The accumulated gap caused the permission-prompt thrash that Dan
complained about. Discipline: when any "Allowlist (auto-execute OK)" entry is added to CLAUDE.md, update
`settings.json` in the same commit. This is analogous to keeping tests and implementation in sync.

### L3 — Programmatic rebase with GIT_SEQUENCE_EDITOR (new technique for the toolbox)

`GIT_SEQUENCE_EDITOR="python3 <script>"` allows a git rebase todo file to be rewritten by a script rather than
manually. The script receives the todo file path as `argv[1]`, can parse all existing pick lines into a
`sha → message` dict, write an entirely new ordering with `pick` / `fixup` / `exec` directives, and git applies
the result. This is the right tool for any fan-out that produces > ~20 commits in non-ideal order.

---

## Outstanding items for next session

1. **PR #24 review and merge.** The branch and description are current; Dan reviews and merges when satisfied.
2. **QiMeng synthesis.** Deferred until Dan uploads ~4 repos and ~8 additional papers. Seed spec at
   `docs/specs/qimeng-category-promotion.md`.
3. **Phase 1c spike.** The notes-consistency arc is complete; `docs/specs/phase1c-spike.md` is the next
   forward-progress deliverable.

---

## Suggested next steps

1. **Merge PR #24** once reviewed.
2. **Upload QiMeng items**, then commission the synthesis using the seed spec as the brief.
3. **Begin Phase 1c spike** — the pmetal evaluation spec is written; execution is the deliverable.
