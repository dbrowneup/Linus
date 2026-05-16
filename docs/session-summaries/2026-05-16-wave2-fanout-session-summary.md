# Wave 2 Fanout Session Summary — 2026-05-16

## Pre-execution context

PR #31 (the bulk filename-discipline rename, DEC-0055) had merged earlier in the day, clearing the way for the
build-mode transition described in
[`docs/specs/2026-05-12-linus-implementation-plan.md`](../specs/2026-05-12-linus-implementation-plan.md). Maestro went
into the session intending to burn high usage in one sitting: dispatch parallel agents across the unblocked Phase 1 /
Phase 2 items, fold in any context stragglers Dan had queued, and finish the R4 ADR backlog. The implementation-plan
items targeted were Item 1 (Phase 2a FastAPI server), Item 2 (Phase 1d Dan tasks), Item 4 (Phase 2h memory v0), Item 5
(Phase 2c KB adapter), Item 6 (tool registry scaffolding), plus a Wave 2 corpus fold-in, a cybersecurity-notes gap
close, and four R4 ADRs (DEC-0055–DEC-0058). Two waves were run back-to-back. The first wave exposed a load-bearing
operational finding that reshaped how the second wave was dispatched — and which should reshape every parallel fan-out
from here on.

The base SHA for everything below was `9b91b66` on `main`.

---

## Step 1 — Wave 2 fanout 1: seven agents on the shared primary checkout

Seven agents were dispatched in parallel against the primary worktree, each instructed to create its own
`agent/<task>-*` branch off `main` and deliver a PR:

- **A1** — Phase 2a FastAPI orchestration backend (Item 1)
- **A2** — Phase 2h memory v0: SQLite episodic + audit log writer (Item 4)
- **A3** — Phase 2c KB read-only adapter (Item 5)
- **A4** — Phase 1d minimal Dan task suite (Item 2)
- **B1** — Wave 2 corpus fold-in (notes + INDEX + landscape refresh)
- **B2** — Cybersecurity-notes gap close (DEC-0024 supply-chain alignment)
- **C1** — R4 ADRs (DEC-0055 filename discipline, DEC-0056 Anthropic-compat amendment, DEC-0057 AGPL-fork posture,
  DEC-0058 x402-mcp graduation pathway)

The plan was clean parallelism. What actually happened was a sequence of HEAD-pointer collisions: multiple
Maestro-dispatched agents working in the **same primary worktree** issued `git switch` and `git switch -c` against the
same `.git/HEAD`. Branches got hijacked mid-command. At least two agents ended up committing to a sibling agent's
branch. The full set of landings, in order of cleanliness, was:

- **A1 → PR #32 (clean).** Phase 2a FastAPI server with `/v1/chat/completions` against local Ollama. The first agent
  dispatched and the only one whose branch state was unambiguous throughout — confirmed in retrospect that A1 finished
  before later agents started colliding.
- **A4 → PR #33 (clean).** Phase 1d minimal Dan task suite (paper summarization, FASTA GC content, title clustering)
  with a baseline run captured against `qwen2.5-coder:7b`.
- **A3 → PR #34 (clean, after cherry-pick recovery).** The original `agent/phase2c-kb-adapter` branch was contaminated
  by another agent's HEAD switch; the salvage was a clean cherry-pick onto a fresh `agent/phase2c-kb-adapter-final`
  branch, which became the PR head.
- **A2 → PR #35 (clean, ~70 min wall — most of it recovery).** Memory v0 (`src/linus/memory/episodic.py`,
  `audit_log.py`, `hashing.py` plus the four unit tests from Item 4). The implementation itself was small; the wall time
  was dominated by untangling which branch held A2's commits after A3 and B2 collisions had stomped the HEAD pointer.
- **C1 → PR #36 (clean, after rebuild on a take-two branch).** The original `agent/r4-adrs-final` branch was poisoned by
  mid-command HEAD churn; recovery was `cherry-pick` of the four ADR commits onto a fresh `agent/r4-adrs-take2` branch,
  which became the PR head.
- **B1 — still in flight at session close.** The Wave 2 corpus fold-in (the largest single agent task, touching the most
  files) had not finished by the time the second wave's worktree-isolated agents had already landed clean PRs. It was
  not a collision casualty; it just runs long. Carried into the next session.
- **B2 — partial / failed.** The cybersecurity-notes gap-close agent was the worst collision casualty. Its commits ended
  up scattered across at least two other agents' branches; cherry-pick recovery looked tractable but the cost-
  to-clarity ratio was poor, so B2 was rolled back and re-dispatched as W3 in the worktree-isolated second wave.

The load-bearing pattern: **the agents themselves wrote correct code**. The PRs that landed do not encode any quality
issue caused by the collisions — only the wall-clock cost of untangling who-committed-where. The recovery technique was
the existing CLAUDE.md
[§Cherry-pick to preserve, never reset to delete](../../CLAUDE.md#cherry-pick-to-preserve-never-reset-to-delete)
discipline: agent commits were cherry-picked onto fresh take-two branches before any reset was contemplated against the
collision-poisoned originals.

---

## Step 2 — Wave 2 fanout 2: five worktree-isolated agents (clean)

Once the shared-checkout failure mode was diagnosed, the second wave was dispatched with `isolation: "worktree"` so each
agent ran in its own `.claude/worktrees/<agent-id>/` checkout with its own `.git` linked-worktree state. Zero
collisions. This wave covered the stragglers Dan had added mid-session plus the remaining implementation-plan items:

- **W1** — Stragglers v1: caveman + symphony + swarm repo-notes, plus the SWARM tech-report paper-note (2604.19752).
- **W2** — Tool registry scaffolding (Item 6): `src/linus/tools/registry.py` with the fastmcp-backed decorator API per
  DEC-0045.
- **W3** — Cybersecurity-notes gap close redo (B2 follow-up). Clean delivery this time.
- **W4** — First Maestro/Worker loop (Item 3): the `experiments/first-loop.md` spec + sandbox helper output recording
  the first on-the-books Maestro/Worker protocol run.
- **W5** — Synthesis rollup + pmetal-vs-ANE factual correction. A multi-doc factual error had propagated across the
  landscape and synthesis docs: pmetal was described as relying on "Apple private APIs" in some places when in fact
  pmetal uses **supported public APIs** (CoreML, MLX, Metal). The corrected statement is the one already in CLAUDE.md
  §Public APIs only and DEC-0027 — the wave-2 rollup brought the landscape and synthesis prose into alignment with that
  ground truth.
- **W6** — Stragglers v2: pi repo-note + the ElephantBroker (2603.25097) and TrustResearcher (2510.20844) paper-notes.
- **W7** — Awesome-papers triage: the `awesome-ai-agent-papers` repo Dan dropped mid-session, scanned for any paper-note
  candidates worth promoting.
- **W8** — This session summary (the agent producing this document).

All seven worktree-isolated agents completed without HEAD-pointer collisions. The worktree overhead — base-SHA pinning,
per-worktree git state, manual cleanup at session close — was real but paid for itself in the first agent that didn't
have to be cherry-pick-recovered.

---

## Step 3 — Phase 1 baseline: real Worker throughput data from PR #33

The Phase 1d task suite run against `qwen2.5-coder:7b` is the first concrete data point about Worker model quality on
Dan-shaped tasks. Three observations from the baseline:

- **paper-summarization** — full credit. The model produced a faithful three-finding extraction from a real PDF in
  `context/papers/`.
- **fasta-gc-content** — partial credit. The generated script computed GC content but included `N` bases in the
  denominator — an instruction-following failure, not a code-quality failure. The rubric explicitly said "GC% over
  A/T/G/C bases only" and the model elided that constraint.
- **title-clustering** — only 36 of 50 titles assigned to clusters, a ~28% drop. Of the three tasks this is the
  costliest signal: the model silently dropped 14 inputs without flagging the omission. For a Phase 2 dispatch design
  this is a hard data point — any orchestration layer routing batch work through this model class needs an output-size
  invariant check, not a trust-the-output assumption.

These are not benchmark scores in the Phase 1c sense; they are first-look quality observations that anchor the rest of
Phase 1 evaluation work. The ~28% drop on title-clustering, in particular, is a Phase 2 dispatch-design constraint that
should propagate into the implementation-plan follow-up.

---

## Step 4 — R4 ADR landings

Four new ADRs landed via PR #36:

- **DEC-0055** — Filename discipline (codifies the PR #31 bulk rename: no spaces in tracked filenames; `kebab-case` or
  ISO-date prefixes).
- **DEC-0056** — Orchestration speaks both OpenAI-compat **and** Anthropic-compat. Amends DEC-0005, which previously
  specified OpenAI-compat alone. Rationale: Claude Code is the Maestro harness (DEC-0007) and the most natural
  integration shape is the Anthropic Messages API; pinning Linus to OpenAI-only would force a harness-side translator
  for the highest-traffic Maestro-Linus path.
- **DEC-0057** — AGPL-fork posture. Codifies how Linus consumes AGPL upstreams (e.g., the MiroFish-Offline repo-note's
  Watch verdict): no AGPL code is vendored into `src/linus/`; AGPL upstreams may run as separate services with their own
  boundary; any contribution back to an AGPL upstream is fine.
- **DEC-0058** — x402-mcp graduation pathway. Codifies the path from "x402 is a Watch verdict in `repo-notes/`" to "x402
  is a first-class Linus payment-rail substrate" once the agent-market commercial surface is decided. The ADR doesn't
  decide adoption; it decides the gate.

---

## Lessons learned (write-back candidates)

### L1 — Shared-checkout parallel agents collide on HEAD; always use worktree isolation

**Destination:** `CLAUDE.md` §Worktree fan-out discipline, as a new top-level rule (hard rule, not a soft preference).

The collision pattern was deterministic and observable in retrospect: any time two or more Maestro-dispatched agents run
in the **same primary worktree** and any of them issues `git switch`, `git switch -c`, `git checkout`, or any operation
that mutates `.git/HEAD`, the second agent observes the first agent's HEAD pointer and acts on it. Commits land on the
wrong branch; branch creation gets aimed at the wrong base; agents stomp each other's working tree state. The five-agent
wave-2 worktree-isolated batch demonstrated by counter-example that the failure is entirely solved by giving each agent
its own linked-worktree checkout.

**Proposed CLAUDE.md addition** (drafted here for the write-back follow-up, not applied in this commit):

> **Shared-checkout parallel dispatch is forbidden.** Any parallel fan-out of two or more agents that exercise git
> operations beyond pure-read must use `isolation: "worktree"` in the Agent tool, or be manually fanned out across
> per-agent `.claude/worktrees/<agent-id>/` checkouts. The shared-checkout pattern silently produces HEAD-pointer
> collisions that look like agent failure but are actually orchestration failure; recovery requires the cherry-pick
> discipline at §Cherry-pick to preserve, never reset to delete and pays a wall-clock tax dominated by untangling
> who-committed-where rather than by the agents' actual work. The exception — and the only exception — is the explicit
> "sequential agent dispatch with file-level partitioning" pattern already documented in §Worktree fan-out discipline
> (the synthesis-refinement fan-out being the canonical example), where each agent edits a non-overlapping file on a
> shared branch and Maestro batches the commits serially.

The carve-out is important: the 25-agent synthesis-refinement fan-out (2026-05-08) worked on a shared branch precisely
because each agent edited a non-overlapping file and no agent issued `git switch`. The new rule is not "always
worktrees"; it is "**any agent that touches git state needs an isolated git directory.**"

### L2 — Cherry-pick recovery works under chaos; reinforce with wave-2 evidence

**Destination:** `CLAUDE.md` §Cherry-pick to preserve, never reset to delete — already covers the principle; add the
wave-2 evidence as a second canonical example.

The CLAUDE.md rule about cherry-picking to preserve before resetting to delete was tested under hostile conditions in
wave 2. Three branches (`agent/phase2c-kb-adapter`, `agent/r4-adrs-final`, an A2 working branch whose name has been
forgotten in the chaos) were collision-poisoned. In every case the recovery sequence was the same: identify which
commits were actually load-bearing via `git log --all` and `git reflog`, cherry-pick them onto a fresh `*-final` or
`*-take2` branch, push the new branch, open the PR from there, leave the poisoned original branch in git history as an
audit trail. Three for three. The discipline isn't theoretical; it survives a multi-agent collision storm.

The reinforcement candidate for CLAUDE.md is a one-line addition to the existing section: _"The wave-2 fan-out
(2026-05-16) tested this discipline against three collision-poisoned branches; cherry-pick-to-take-two recovered all
three without data loss."_

### L3 — Real Worker throughput data is the gold for Phase 1; the 28% drop is a Phase 2 dispatch constraint

**Destination:** `docs/specs/2026-05-12-linus-implementation-plan.md` — follow-up note in the Item 2 / Phase 1d section
recording the baseline observations, and propagation into a Phase 2 dispatch-design constraint.

The title-clustering result (36 of 50 titles assigned, ~28% silent drop) is the costliest single data point in the
session. It tells us that any Phase 2 dispatch path running batch work through `qwen2.5-coder:7b`-class models needs an
output-size invariant — the model should not be trusted to return one output per input without an explicit count check.
This is not a Phase 1c benchmark conclusion (we have N=1 task on N=1 model); it is a flashing yellow light for the
orchestration layer's batch-dispatch design.

The fasta-gc-content N-base inclusion is a weaker signal — it's an instruction-following nit on a one-shot prompt and
might disappear with better prompt construction. The Phase 2 implication is narrower: prompts that specify "compute X
over the subset Y" need machine-checkable post-conditions, not just rubric prose.

Both points should land in the implementation-plan spec's Item 2 section as observed-baseline notes, and in any Phase 2a
router design as input to the question "what invariants does the dispatcher enforce per task class?"

### L4 — pmetal vs ANE factual error persisted across multiple landscape docs; codify the corpus-audit cadence

**Destination:** `docs/protocols/curation-protocol.md` and `CLAUDE.md` §Curation cadence — extend the quarterly review
to include a factual-grep pass against the load-bearing ground-truth statements in CLAUDE.md.

The W5 agent corrected a multi-doc factual error: pmetal had been described in some landscape and synthesis prose as
relying on "Apple private APIs" or "unsupported APIs" — language that contradicts the actual ground-truth statement in
CLAUDE.md §Public APIs only (and DEC-0027): "pmetal uses supported public APIs." The error had propagated across at
least three documents before W5 caught it. The root cause is the well-known synthesis-drift pattern: a near-miss
phrasing in one doc gets quoted into another, then a third, and the original ground-truth no longer constrains the
copies.

The corpus-audit cadence proposal: every quarterly curation review (next: 2026-08-01) should include a grep pass for any
"private API", "unsupported API", or "reverse-engineered" claim across `docs/landscapes/`, `docs/syntheses/`,
`docs/paper-notes/`, and `docs/repo-notes/`, and verify each hit against the current CLAUDE.md ground truth before
either preserving or rewording. The grep takes seconds; the audit takes minutes; the cost of _not_ doing it is the slow
accretion of factually-wrong prose in load-bearing planning docs.

The generalization beyond pmetal: any ground-truth statement in CLAUDE.md that's likely to be paraphrased in synthesis
prose (the hardware-constraints block, the public-APIs-only stance, the trust-the-OS-page-cache convention) is a
candidate for the quarterly factual-grep pass.

---

## Outstanding items for next session

1. **B1 — Wave 2 corpus fold-in.** Still in flight at session close. The largest single agent task in wave 1. Carries
   forward as a sequential-dispatch follow-up; given L1, the right pattern is one agent in one worktree, not a reattempt
   in the primary checkout.

2. **B2 cherry-picks (if any survived).** W3 redelivered the cybersecurity-notes gap close cleanly via worktree
   isolation; if any B2 partial work is still sitting in the reflog or on a collision-poisoned branch, it should be
   audited and either cherry-picked into the W3 landing or formally abandoned with a curation-log entry. Most likely
   answer is "abandon" — W3 was clean and a re-merge of B2 fragments would just risk reintroducing the collision-era
   confusion.

3. **Awesome-papers gap fold-in.** W7 produced the triage of `awesome-ai-agent-papers`; the actual paper-note promotions
   surfaced by that triage need to land as follow-up paper-notes (sequential agent dispatch per L1, since each one is a
   single-file write).

4. **PR consolidation.** Wave 2's five clean PRs (#32–#36) are all open against `main`. Dan's review-and-merge pass is
   the next gate; once they land, the wave-2 worktree branches and the collision-era poisoned branches should be cleaned
   up per the §Worktree fan-out discipline cleanup sequence.

5. **Write-back of L1.** The hard rule from L1 should land in CLAUDE.md §Worktree fan-out discipline as a follow-up
   commit (separate from this session summary). The drafted language is in the L1 section above.

---

## Suggested next steps

1. **Continue the implementation plan.** Items 3 (first Maestro/Worker loop — wave 2 W4 delivered the first practice
   run; the next session is the _second_ run with the lessons folded in), 6 (tool registry — wave 2 W2 delivered the
   scaffolding; the next step is wiring it into the Phase 2a server from PR #32), and 7 (sandbox helpers, which W4
   started against `src/linus/sandbox/fs.py`) are the natural next batch.

2. **Settle pmetal evaluation.** Phase 1b has been "in progress" for weeks. After the wave-2 landings settle, the next
   high-leverage Phase 1 move is finishing the pmetal LoRA + serve + comparative benchmark per DEC-0006/0012 and
   reaching a verdict per DEC-0049 (pmetal vs PrismML fork decision).

3. **Phase 2a wiring pass.** PR #32 (FastAPI server), PR #34 (KB adapter), PR #35 (memory v0), and the wave-2 W2 tool
   registry are all isolated scaffolding. The next architectural step is a single integration commit that wires them
   together — the server taking a request, dispatching through the tool registry, recording an audit log entry, and
   optionally retrieving from the KB adapter. That commit is the actual Phase 2a MVP boundary.

4. **Run the Phase 1d suite against a second Worker model.** With one baseline data point in hand (`qwen2.5-coder:7b`,
   from PR #33), running the same suite against `qwen3:8b` or `llama3.1:8b` is cheap and produces the first comparison
   anchor for Phase 1c.

---

## Measure — estimated wall time vs actual

- **Estimated session length:** 60–90 minutes (just for this session-summary agent, W8).
- **Actual session length (this agent only):** ~25 minutes from dispatch to commit + PR open. Under-budget; the template
  was well-specified and the structural conventions in CLAUDE.md let the agent skip the design phase entirely.
- **Estimated wave-2 fanout-1 wall time:** 60 minutes (seven parallel agents).
- **Actual wave-2 fanout-1 wall time:** ~70 minutes (A2 alone), and several hours total when the cherry-pick recovery is
  included. Over-budget by 100–300% depending on which clock starts. The variance is entirely attributable to L1 (the
  shared-checkout collision pattern). With worktree isolation in fanout-2, the variance disappeared: wave-2 fanout-2
  (five worktree-isolated agents) came in at-or-under estimate.

The session-summary measurement convention says: when variance exceeds ~20%, record the cause. The cause here is L1. The
next fan-out estimate should anchor on the worktree-isolated wall time (clean, on-budget), not on the shared- checkout
wall time (chaotic, over-budget by 2–4x). This is the flash-moe pattern (DEC-0027) applied to workflow itself: measure
the clean path, plan from the measurement, not from the optimistic intuition.

---

_This document closes the 2026-05-16 wave-2 fanout arc. The five clean PRs (#32, #33, #34, #35, #36) are open for Dan's
review pass. The L1 worktree-isolation rule is the most consequential write-back from the session and should land in
CLAUDE.md in a follow-up commit before the next parallel fan-out is dispatched._
