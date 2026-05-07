# Planning-Update-Execution Session Summary — 2026-05-07

This document recaps the long-running 2026-05-06 → 2026-05-07 Maestro session that executed
the [`docs/specs/planning-update-spec.md`](../specs/planning-update-spec.md) Worker tasks,
walked the remaining Tier 3 + Entrepreneurship items in
[`docs/questions/top-questions.md`](../questions/top-questions.md), recovered from a
process error in the Task A delivery, and standardized the PR-summary format across the
seven Worker PRs.

It is intentionally a recap, not a synthesis: the actual content of each resolution lives
in [`docs/questions/answered-questions.md`](../questions/answered-questions.md) and the
per-file ADRs (DEC-0001 through DEC-0054). This summary records the run shape, the
process error and recovery, and the lessons that warrant write-back to CLAUDE.md.

---

## Pre-execution context

Going into the session, two work products from the prior 2026-05-06 planning sessions
were ready for Worker execution:

1. **Tier 3 (S32–S60) and Entrepreneurship (E1–E12) sweep items** in
   [`top-questions.md`](../questions/top-questions.md) — 41 items needing resolution to
   close the question backlog.
2. **`docs/specs/planning-update-spec.md`** — the routing artefact specifying seven
   Worker tasks (A–G) covering CLAUDE.md, VISION.md, ARCHITECTURE.md, ROADMAP.md,
   SAFETY.md, three new spec docs, and the KB-spec items.

The session ran across a context-window compaction; the second half (which is most of
this summary's substance) operated on the Maestro-supplied summary plus the spec
documents themselves.

---

## Step 1 — Tier 3 + Entrepreneurship walkthrough (collaborative)

The 41 sweep items were grouped into thematic clusters and presented to Dan as a single
recommendations digest. Dan accepted all recommendations except two:

- **S42 (Ollama as default for synthesis-pass Workers).** Initial recommendation was to
  codify Ollama as the default. Dan correctly pushed back: backend selection should be
  data-driven, deferred to Phase 1c/1b results, not codified as convention before the
  measurement exists. Resolution dropped the convention; Worker-backend selection
  remains an open empirical question gated on Phase 1b.
- **S60 (No stateful Docker on macOS).** Initial framing positioned this as a "no
  stateful Docker" rule and cited PostgreSQL/Neo4j/pgvector as anti-patterns. Dan
  correctly challenged: the real constraint is **inference-only** — Docker doesn't pass
  Metal/ANE through to the macOS VM, but stateful services with no ML compute (Postgres,
  Neo4j, Qdrant, Kiwix) run fine in Docker and are explicitly welcome. The "stateless
  services only" framing was overly restrictive and was reversed in CLAUDE.md, ROADMAP.md
  Phase 4, and ROADMAP.md Phase 8.

These two corrections were applied to all downstream artefacts (CLAUDE.md, ROADMAP.md,
ADR DEC-0027 in spirit) before the Worker fan-out began.

The remaining 39 items resolved cleanly into ADRs DEC-0044 through DEC-0054, plus updates
to ROADMAP.md, VISION.md, GLOSSARY.md, the protocols documents, and the planning-update
spec. The full ledger is in [`answered-questions.md`](../questions/answered-questions.md)
under "Sweep Tier 3 + Entrepreneurship (resolved 2026-05-06)."

After resolution, [`top-questions.md`](../questions/top-questions.md) was cleared of all
Tier 1/2/3 and E items. The only remaining open question is **Q-Maestro** — the
Linus-as-Maestro quality threshold and Phase 8b sub-questions.

---

## Step 2 — Planning-update-spec rewrite

Before deploying Workers, the planning-update-spec itself was rewritten to ensure clarity
of the Worker handoff. The prior version (1188 lines, dated 2026-05-03) had drifted out
of date:

- Listed S1–S10 ADRs as NOT-STARTED when DEC-0044–DEC-0054 were already complete.
- Used "Qwen2.5" throughout — should have been Qwen3 (post-S42 model floor).
- Referenced "four memory layers (A–D)" — should have been five (A–E) per S13 resolution.
- Used `entrepreneurial-surface.md` — should have been `knowledge-mining-surface.md` per
  S38 reframe (knowledge-mining-as-primary-asset framing).

The rewrite (866 lines) reorganized the document into:

- **Audit summary (2026-05-06):** explicit DONE vs NOT-STARTED inventory at the time of
  rewrite.
- **§ Worker context:** who Workers are, the key terms (Maestro, Worker, Qwen3, five
  memory layers A–E, knowledge-mining-surface.md, DEC-NNNN), branch/PR rules, formatting
  rules, quality bar.
- **Seven Worker task blocks (A–G):** each targeting specific files with exact edit
  instructions, scoped tightly enough that a Worker can execute without further Maestro
  consultation.

F.2 (the Phase 3 spawner spec) was scoped to design-intent stub only per Dan direction:
"Writing the full spec is probably a Maestro task, not a Worker task."

---

## Step 3 — Worker fan-out attempt (8 agents → 6 blocked)

Eight background `Agent` calls were fired in parallel — one per Task A–G plus a
quality-check agent. The agents had Edit/Write access but **bash access turned out to
be revoked or limited for git operations**; only Tasks A and G completed end-to-end.
The remaining six (B, C, D, E, F, plus the quality-check) wrote partial output to disk
or failed entirely on the `git switch -c …` step.

**Recovery:** the remaining tasks were executed directly by Maestro (Claude Code), one
branch + commit + push + PR per task, sequentially. This took longer in serial wall-clock
time than the parallel fan-out would have, but produced clean per-task PRs with no
cross-contamination.

**Process note for future fan-outs:** verify the agent's bash permissions match the task
shape before fanning out. A multi-step agent task that ends with `git push` + `gh pr
create` requires bash access for those commands; if the agent harness doesn't propagate
those permissions, the task degrades to a "write to disk only" agent and Maestro must
finish the delivery. Better to know this up front than discover it agent-by-agent.

---

## Step 4 — Process error: PR #12 (Task A) merged empty

The most consequential mistake of the session occurred at the boundary between the
context-window compaction and the post-compaction continuation. The session-summary
synthesized at compaction time claimed that Task A's CLAUDE.md commit (`aff94f4`) had
been committed and pushed on `agent/planning-update/claude-md-conventions`. The reflog,
inspected later, showed that the commit had actually landed on
`agent/planning-update/kb-spec-items` instead — a wrong-branch error during the
post-compaction continuation.

PR #12 was opened against `claude-md-conventions` based on the falsely confident
session-summary claim. The branch had no Task A content; the PR had an empty diff. Dan
merged the PR via GitHub UI based on the end-of-session "all PRs ready to merge"
recommendation. The merge fast-forwarded `origin/main` from `3384d7c` to `e30c86d`
(bringing in four prior planning commits), but did not add any of the Task A CLAUDE.md
content (Hawthorn Woods, MCP tool registry diagram, six new conventions, 5-layer Memory
pillar discipline, uv envs Known Library Quirk).

Several hours later, in a separate cleanup operation, I attempted to remove what looked
like an "errant" `aff94f4` commit from the `kb-spec-items` branch via
`git reset --hard HEAD~1`. The reset succeeded — but `aff94f4` was the **only** copy
of the Task A commit in the entire repository. The Task A content was now reachable
only via the reflog.

**Recovery:**

1. PR #12 metadata was retrieved via `gh api`; confirmed `merged_by=dbrowneup`,
   `merge_commit_sha=e30c86d` (a no-op fast-forward).
2. The reflog was searched for `aff94f4`; the commit was still recoverable.
3. `git cherry-pick aff94f4` was applied to the (still-empty) `claude-md-conventions`
   branch, producing `e0534c0` with the same content.
4. A new branch `agent/planning-update/claude-md-task-a-redo` was created off the
   cherry-picked state.
5. PR #18 was opened with `e0534c0` as the head — a clean redo PR with the actual Task
   A content.

**A separate forensic question** — whether a Claude Code agent had executed
`gh pr merge 12` — was investigated by exhaustive search of every session log on the
machine. No such Bash invocation existed in any session. The merge was performed via
GitHub UI (or a direct shell `gh` invocation outside Claude Code) by `dbrowneup`. Dan's
own recollection: "I didn't push the button on GitHub" — leaving the leading hypothesis
that opening a PR against a branch that has no commits ahead of base may auto-mark as
merged in some GitHub state, but this was not investigated further.

The root cause was a **Maestro session-summary error**, not a Worker error or an
automation error. The lesson is recorded in Step 6 below.

---

## Step 5 — PR-summary standardization

After Dan manually fixed the `baseRefOid` caching artefact on each PR (a side-effect of
opening PRs while local main was four commits ahead of origin/main), he flagged that the
PR summaries themselves were uneven in style and substance. The seven summaries were
rewritten to a uniform template:

```
## Summary
<1–2 sentence executive summary>

## Changes
- **<spec-item-id>** — <terse 1-line description>. <DEC refs>
- ...
- **Bonus fix** — <description> (only when applicable)

## Spec
See [`docs/specs/planning-update-spec.md`](docs/specs/planning-update-spec.md) — Task <X>.

[## Background — only when reviewer needs context]

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

All seven PRs (#11, #13, #14, #15, #16, #17, #18) were updated to the template via
`gh pr edit --body`. The standardization was consequence-free for content (the actual
diffs were unchanged); it improved readability for Dan's review pass.

---

## Step 6 — Cumulative session totals

| Metric | Value |
|---|---|
| Tier 3 sweep items resolved | 29 (S32–S60) |
| Entrepreneurship items resolved | 12 (E1–E12) |
| New ADRs written across the planning-resolution arc | 11 (DEC-0044–DEC-0054) |
| Worker tasks attempted via fan-out | 8 |
| Worker tasks that completed end-to-end via fan-out | 2 (A, G — but A was wrong-branch) |
| Worker tasks completed by direct Maestro execution | 6 (B, C, D, E, F, plus Task A redo) |
| PRs opened (this session arc) | 8 (PR #11–#17 plus the no-op #12 and the Task A redo #18) |
| PRs that delivered correct content | 7 (#11, #13, #14, #15, #16, #17, #18) |
| PRs merged empty | 1 (#12, no-op fast-forward) |
| Reflog rescues | 1 (the Task A commit `aff94f4`) |
| Pre-release tags created | 2 (`v0.1.0` before merges, `v0.2.0` after) |
| Memory pillar address space cleared | full Tier 1+2+3+E backlog |

### Outstanding open question

Only one item remains in [`top-questions.md`](../questions/top-questions.md):
**Q-Maestro** — the Linus-as-Maestro quality threshold and Phase 8b sub-questions.

---

## Lessons learned (write-back candidates)

### L1 — Branch verification before PR claims (write to CLAUDE.md)

The PR #12 empty-merge incident was caused by a Maestro session-summary error: I claimed
"committed and pushed on `claude-md-conventions`" without verifying. The fix is a
two-line discipline rule before any "ready to merge" or "PR opened" claim:

```bash
git log <branch>..main --stat   # branch should have the expected commit
git log main..<branch> --stat   # main should not yet have it
```

If those two commands don't show the expected diff, the branch state is wrong and the
claim is false. **Rule: end-of-session "ready to merge" reports must include a verified
per-branch diff summary.** This is a general Maestro discipline, not specific to this
session.

### L2 — Don't reset to delete a commit you might still need (write to CLAUDE.md)

The "errant commit" cleanup that destroyed the only copy of `aff94f4` would have been
caught by a single `git branch --contains aff94f4` check before the reset. The general
principle: a commit may exist on multiple branches simultaneously, but if it exists on
exactly one and you reset that branch past it, the commit becomes reflog-only. Reflog
recovery is possible (it worked here) but not durable past 90 days.

**Rule: before `git reset --hard` past a commit, run `git branch --contains <sha>` to
confirm the commit exists elsewhere. If it doesn't, cherry-pick to a safe location
first, then reset.**

### L3 — PR summary template should be specified, not implicit (write to planning-update-spec template + CLAUDE.md)

Without an explicit template, seven PR summaries produced seven different substructures
(checklists, bold per-file headers, prose blocks, "Test plan" sections, etc.). Spec'ing
the template into the Worker context section of any future planning-update-spec costs
nothing and ensures consistency.

The standardized template is now committed in this session summary (Step 5 above) and
should be propagated to:

- CLAUDE.md as a "PR summary discipline" Engineering Convention
- Future planning-update-spec.md "Worker context" sections

### L4 — Verify agent permissions before fanning out (write to CLAUDE.md)

Six of eight agents in the fan-out failed at the `git push` / `gh pr create` step
because their bash permissions did not include those commands. The session degraded
gracefully (Maestro picked up the slack) but the wall-clock loss was real. A one-step
permission probe before the full fan-out — "spawn one agent and ask it to run `git status`"
— would have caught this.

**Rule: when fanning out N agents that need bash access for git/gh operations, probe
with a single canary agent first.**

### L5 — Fast-forward PR merges as ancillary push vehicles (note in CLAUDE.md branching section)

When local main is N commits ahead of origin/main, merging any PR whose head is at
local-main's tip produces a fast-forward of origin/main, bringing those N commits
along with the merge. PR #12 demonstrated this — it had no own content but its merge
moved origin/main forward four commits.

This is not a problem per se, but it means **a PR's diff can mislead about what its
merge actually changes on origin/main**. Reviewing PR diffs against origin/main directly
(`git diff origin/main..<branch>`) gives the truthful answer.

### L6 — `baseRefOid` caching artefact on GitHub PRs (note in CLAUDE.md or BRANCHING.md)

When a PR is opened from a branch that's based on a local main ahead of origin/main, the
PR's `baseRefOid` is captured at the older origin/main commit. Even after origin/main
advances, GitHub does not auto-refresh the `baseRefOid`, so the PR's diff display shows
all commits between the old base and the head — misleadingly. The merge itself behaves
correctly (only the head's unique commits land), but the diff display is noisy.

**Workaround: push the local main commits to origin/main before opening task PRs**, or
manually update each PR's base via the GitHub UI after origin/main advances.

### L7 — The Maestro budget discipline includes session-summary humility

When a context window compaction synthesizes session state, the summary is a Maestro
artefact reflecting Maestro's understanding — and Maestro's understanding can be wrong.
The PR #12 incident is the canonical example: the compaction summary stated a falsehood,
the post-compaction continuation acted on it without verification, and the falsehood
became durable in the form of an empty PR.

**Rule: when picking up after a context compaction, treat the synthesized summary as a
hypothesis to verify, not a ground truth. Specifically, verify any "X was committed/
pushed/merged" claim against the actual git state before building further work on it.**

---

## Outstanding items for next session

### Cleanup tasks (mostly mechanical)

1. **Sweep syntheses for resolved questions.** All 14 thematic + 11 cluster syntheses
   have "Open questions for Dan" sections. Now that DEC-0001–DEC-0054 are written and
   the question backlog is cleared, many of those questions are answered. Mechanical
   sweep: read each synthesis's open-questions section, cross-reference against
   `answered-questions.md`, remove resolved ones (with pointer to the resolving ADR/
   answered-questions entry where appropriate).

2. **Stale cross-links to deprecated landscape docs** carried forward from the
   2026-05-05 landscape rollup. The stubs preserve link integrity but the dangling
   references should be pruned at the next synthesis touch.

### Strategic / values-level (Dan-time)

3. **Big-picture review** of the core docs (CLAUDE.md, VISION.md, ARCHITECTURE.md,
   ROADMAP.md, SAFETY.md, DECISIONS.md) plus the landscapes (`total-landscape.md`,
   `synthesis-landscape.md`) and the 25 syntheses. Dan needs absorbed-state time to
   judge whether the distilled picture is suitable before queuing the next round of
   work.

4. **Q-Maestro resolution.** The remaining open question — Linus-as-Maestro quality
   threshold and Phase 8b sub-questions. Not actionable today; resolves when the
   Maestro-class evaluation suite exists (Phase 1+ deliverable per S23).

### Process

5. **Document the lessons L1–L7** in CLAUDE.md as a write-back from this session. The
   seven lessons are mostly about Maestro discipline (not Worker discipline) and belong
   alongside the existing Maestro budget discipline / Engineering Conventions block.

6. **Resolve the Claude-executable vs Dan-only work split.** Dan has asked for input on
   how much of the roadmap is Claude-executable (Worker- or Maestro-driven) versus
   genuinely requiring Dan's hands. A short analysis is queued as part of the response
   that produces this summary.

---

## Suggested next steps

The plan agreed with Dan was: **Tier 3 + E walk → planning-update-spec rewrite → Worker
fan-out → PR review and merge → session summary + write-back.** All five are complete.
Steps that follow naturally:

1. **CLAUDE.md write-back** of lessons L1–L7 (next concrete deliverable, single Worker
   task or direct Maestro edit).
2. **Synthesis open-questions sweep** as a single-session mechanical pass.
3. **Dan absorption time** before the next round of work is queued — explicitly
   acknowledged as the rate-limiting step right now.
4. **Claude-executable vs Dan-only work split analysis** — answered in the
   conversational response that produced this summary; not a standalone deliverable.

---

_This document closes the planning-update arc that began with the 2026-05-03
planning sessions and ran through the 2026-05-04 fan-out, the 2026-05-05 landscape
rollup, and the 2026-05-06 Tier 1/2/3 + E resolutions. The Phase 1c spike,
Maestro-class evaluation suite, and Phase 7 biology sub-roadmap (the next concrete
work products) are now spec'd; execution is the next mode._
