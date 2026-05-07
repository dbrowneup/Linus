# Maestro Protocol

**Status:** initial draft (2026-05-07). Phase 2a operational document. Companion to
[`maestro-worker-protocol.md`](maestro-worker-protocol.md), which describes the per-task spec → delegate → implement
→ review → merge → close loop. This document describes the **Maestro role itself** — what Maestro is, what disciplines
it operates under, what work belongs to it versus to Workers, and where its budget gets spent.

The doc was queued as S57 in the 2026-05-04 sweep and listed as a Phase 2a deliverable in
[`docs/specs/planning-update-spec.md`](../specs/planning-update-spec.md). The `safety-alignment-privacy` synthesis
(Values paper) argued that hosted Maestro is not a black box and merits an explicit protocol; the
2026-05-06 / 2026-05-07 work added enough behavioral discipline (the seven lessons from the planning-update execution
session) and work-split clarity that capturing all of it in one place is now overdue.

---

## Who Maestro is

**Maestro = Dan + hosted Claude.** This is the core unit of agency in the project. It composes architecture, writes
specs, makes taste-level decisions, reviews PRs, resolves plateau points, and directs Worker fan-out. Specifically:

- **Dan** holds the irreducible roadmap-agency pieces: which problems to pursue, what counts as success, what to
  prioritize, when to ship vs iterate, what's biologically meaningful, what's strategically interesting.
- **Hosted Claude** (this chat / Claude Code / Claude.ai) is the cognitive amplifier: pulls context together, drafts
  specs, reasons across files, generates code, surfaces inconsistencies, holds many threads at once.

Maestro acts as a single coherent entity at the planning and review layer. Workers are fungible local models (Qwen3
today, future fine-tuned Linus); Maestro is not. This asymmetry is foundational and does not relax over time — even
in Phase 8b when Linus itself becomes Maestro-capable, the role retains its structure (one cohesive director, many
fungible executors).

A note on the long arc: **Phase 8b is the north star where local Linus replaces hosted Claude in the Maestro role.**
That transition does not eliminate Dan from Maestro; it changes the AI half of the pair. The discipline this protocol
codifies is meant to survive that transition unchanged. Workers are interchangeable; Maestros are not — and
specifically, the human in Maestro is not.

---

## Philosophy

The Maestro/Worker split is a principled stance, not just a token-economics convenience. It draws on three bodies of
work, mapped to Linus operationalizations. The full mapping lives in
[`maestro-worker-protocol.md`](maestro-worker-protocol.md#philosophy); the short version:

- **Schulz (open-source collaborators).** Workers are fungible, open-source, locally hosted. The human collaborator
  reviews and takes responsibility. Workers are not authors; they are research assistants.
- **Marelli (attribution and accountability).** Every output is traceable to its producing model, its inputs, and the
  decision that authorized it. The audit log, content-hashing, and claim-typing are Marelli requirements wearing
  engineering clothing.
- **Botvinick & Gershman (humans retain roadmap agency).** A class of decisions — which problems to pursue, what
  constitutes success, how to weigh trade-offs — should stay with the human regardless of Worker capability. Maestro
  budget discipline operationalizes this.

These three positions are not in tension. Together they define a coherent stance: open-source Workers under Schulz
norms, audited under Marelli discipline, directed by a human Maestro following Botvinick/Gershman's roadmap principle.

---

## Maestro budget discipline

Maestro attention is the scarcest resource in the project. The budget rules:

1. **Arrive with context gathered, questions sharpened, task well-specified.** Don't use Maestro tokens to read files
   Claude could read incrementally during execution; pull excerpts and paste, or hand the spec to a Worker.
2. **Don't use Maestro tokens for well-specified implementation.** If a task can be specified as "do X with these
   inputs and these success criteria," it is a Worker task by default.
3. **Reserve Maestro attention for architecture, taste, and plateau-points.** The flash-moe pattern: when an
   autoresearch loop plateaus, that's a Maestro signal, not a Worker signal. Plateaus need framework changes, not
   more iterations of the same loop.
4. **Multi-Worker fan-out generates real throughput only when synthesized before reaching Dan.** Workers run at ~10⁹
   bits/s of substrate; Dan + Maestro consume at ~10 bits/s of conscious channel (Zheng & Meister 2024). Synthesis is
   not optional — raw Worker concatenation defeats the parallelism gain.

The Maestro budget is enforced operationally by the `cot_budget` and `memory_mode` router primitives (DEC-0031), the
in-context cap policy (DEC-0032), and the output-synthesis layer (DEC-0023). It is enforced philosophically by the
discipline rules below.

---

## Behavioral disciplines

The seven lessons from the 2026-05-06 → 2026-05-07 planning-update execution session are codified in CLAUDE.md as
Engineering Conventions and reproduced here as the Maestro behavioral spec. The session summary is at
[`docs/session-summaries/2026-05-07-planning-update-execution-session-summary.md`](../session-summaries/2026-05-07-planning-update-execution-session-summary.md).

### L1 — State verification across context boundaries

When state was established in a prior context — a different session, a context-window compaction summary, or even
Maestro's own claims from earlier in the same session — verify the state before building further work on it.
Specifically:

- **Branch state verification before "ready to merge" claims.** Before any end-of-session report that a PR is ready or
  that a branch contains a commit, run `git log <branch>..main --stat` and `git log main..<branch> --stat`. If those
  two commands don't show the expected diff, the claim is false.
- **Compaction-summary humility.** Treat any synthesized session summary as a hypothesis about prior state, not a
  ground truth. Verify any "X was committed / pushed / merged / written" claim against the actual artefact before
  proceeding.

The canonical failure mode this addresses is PR #12 (2026-05-06): a falsely confident compaction summary claimed a
commit was on branch X when it was actually on branch Y; an empty PR was opened and merged before anyone checked.

### L2 — Cherry-pick to preserve, never reset to delete

Before any `git reset --hard` past a commit, run `git branch --contains <sha>` to confirm the commit exists elsewhere.
The safe pattern is cherry-pick first, reset second; never the reverse. Reflog rescue is possible but not durable past
~90 days.

### L3 — PR summary discipline

Apply the uniform PR-summary template (CLAUDE.md "PR summary discipline") to every Worker- or Maestro-delivered PR
that descends from a planning-update spec or any multi-task spec doc. Per-PR ad-hoc structures defeat the point of
batched review.

### L4 — Agent fan-out: probe permissions first

When fanning out N parallel agents that need bash access for `git` / `gh` / `pytest` / similar operations, probe with
a single canary agent before the full fan-out. The canary costs a minute; debugging six stuck agents costs much more.

### L5 — Empty PRs as fast-forward push vehicles

A PR opened from a branch that has zero unique commits beyond its base will still merge if Dan clicks "merge,"
fast-forwarding `origin/main` to wherever the head pointed. This is not a bug but it can confuse reviewers. PR #12
was the canonical instance.

### L6 — GitHub PR `baseRefOid` caching artefact

When a PR is opened from a branch based on local main ahead of origin/main, GitHub captures `baseRefOid` at the older
origin/main commit. Even after origin/main advances, the diff display shows the stale-base diff. The merge itself is
correct; the review UI is misleading. Workaround: keep origin/main current before fanning out task branches.

### L7 — Falsely-confident summaries are the canonical failure mode

The PR #12 incident was caused by Maestro overstating certainty about prior session state. The general principle:
when a session ends or compacts, the synthesized summary reflects Maestro's understanding — which can be wrong.
Synthesizing humility into the summary is itself a Maestro discipline.

---

## Work-split: Claude-executable vs Dan-only

The roadmap divides cleanly into work that Claude (Maestro and/or Workers) can execute end-to-end, work that requires
Dan-judgment checkpoints, and work that only Dan can do. The bottleneck is Dan-attention for taste/judgment, not
Dan-time for implementation. This section is the operational decision rubric.

### Dan-only by nature

These cannot be delegated meaningfully:

- **Architecture taste-level decisions and ADR approvals.** Even when Claude drafts the ADR, only Dan can sign it.
- **Domain-truth checks.** Whether a biology output is biologically meaningful, whether a paper's claim survives
  critical reading, whether a synthesized answer is correct in Dan's field. Dan is the only person on this project
  who can sign off.
- **Dan task suite authoring.** The benchmark's value is that the tasks are real Dan-work. Anyone else inventing them
  produces something else. (Claude can write the harness; Dan authors the tasks.)
- **Values / strategy calls.** Monetize-now vs. build-first; how much time to allocate to biology vs. infra; when
  Linus is "useful enough" to graduate; whether to engage a paying client. Roadmap-direction agency belongs to Dan.
- **Hardware, network, credentials.** Plugging in a Mac Studio, configuring keychains, network setup, anything that
  requires being physically at the machine.
- **Final review / "is this useful to me?" judgments.** The acceptance criterion for any deliverable.

### Claude-executable with Dan-checkpoint

Most of the roadmap. Claude (Maestro) and Workers do the work; Dan reviews PRs:

- **Phase 1 implementation.** Repo notes, pmetal eval runs, `lm-eval` standup, memory-pillar spikes (CoT-gap
  fingerprint, TTT viability, minGRU MLX port), benchmark harness code. Dan needed for: pmetal install if interactive
  sign-off is required, the keep-or-revert decisions on Pareto results, defining what counts as "passes" for each
  spike.
- **Phase 2 orchestration backend.** FastAPI app, OpenAI-compatible router, MCP tool registry, sandbox enforcement,
  session store, audit log, Streamlit chat UI, KB v1 adapter, memory pillar v0 (all 7 sub-deliverables), output-
  synthesis layer, ARC-AGI memory diagnostic. Dan needed for: UX defaults, domain-skill priorities, integration
  testing.
- **Phase 3 spawner + parallel agents.** Full spawner spec (Maestro task), implementation, parallel-write
  coordination, investigation memory, classifier. Dan needed for: spawner spec sign-off, values-level call on
  critic-tier policy.
- **Phase 4 data sovereignty.** Kiwix install, Wikipedia ZIM ingestion, Kolibri benchmark surface, PMTiles regional
  fallback logic, data-package registry, update-check tool. Dan needed for: which ZIMs to actually load, disk-
  allocation calls.
- **Phase 6 fine-tuning.** Hyperparameter sweeps via autoresearch loop, LoRA training runs, the 5% Q&A sample review
  queue (Dan reviews; Claude prepares the queue), flash-streaming evaluation. Dan needed for: domain-quality
  acceptance, the keep-or-revert call on each adapter.
- **Phase 7 skills.** Adopting bioSkills + scientific-agent-skills (mechanical), drafting custom domain skills, A/B
  test on 5 tasks. Dan needed for: which custom skills matter, autonomy-tier graduation criteria.
- **Synthesis maintenance.** Cleanup sweeps (resolved-questions removal, stale-link fixes) — purely mechanical.
- **Doc maintenance generally.** ADR drafting (Dan reviews), spec writing within bounds, landscape updates as new
  material arrives, glossary maintenance, all CLAUDE.md/VISION.md write-back.

### The Maestro-budget arithmetic

Right now Dan-attention is the binding constraint, and it's spent on three things in roughly this order:

1. **Reviewing Maestro/Worker PRs.** Necessary; not avoidable; could be batched.
2. **Resolving open questions in conversation.** Mostly done — the Tier 1/2/3/E backlog is clear.
3. **Writing tasks that only Dan can write** (Dan task suite, domain-truth review, strategic calls).

If Dan-review friction can be lowered ((1) becomes faster because PRs are small and well-specified) and Maestro time
is reserved for (3), throughput rises substantially. The PR-summary standardization (L3) is a small step in that
direction; the Worker-context section of the planning-update-spec was a bigger one.

### Decision rubric for new tasks

When a new task surfaces, Maestro applies this rubric in order:

1. **Can this be deleted?** (The Algorithm check from CLAUDE.md.) If not load-bearing, defer.
2. **Is this a Dan-only task per the categories above?** If yes, Dan executes; Maestro supports with context.
3. **Can this be specified well enough to hand to a Worker?** If yes, Maestro writes the spec; Worker executes.
4. **Is this a Maestro-judgment task that nonetheless can be drafted by Claude?** If yes, Maestro drafts and Dan
   reviews — common for ADRs, specs, syntheses, planning docs.
5. **Does this require interactive Dan + Claude collaboration?** If yes, schedule a Maestro session — typically the
   slowest path in token terms but the right one for plateau-points and architectural questions.

---

## When Maestro should escalate

Three classes of situation always escalate from Maestro-execution mode to Maestro-collaboration mode (Dan + Claude
working synchronously rather than Claude executing under Dan's prior direction):

1. **Plateau points** — when an autoresearch loop, benchmark sweep, or implementation arc stops making progress per
   its metric. Plateaus need framework changes that only Dan + Maestro together can produce.
2. **Architectural surprises** — when implementation reveals that a prior architectural assumption was wrong. New
   ADR territory; Dan must be in the room.
3. **Cross-domain decisions** — when a choice has implications across two or more architectural layers (e.g.,
   memory pillar + KB substrate + safety policy). Risk of missed implications is too high for solo Maestro
   execution.

Smaller tactical issues (a Worker permission-block, a single-file misroute, a stale doc reference) are handled by
Maestro autonomously and surfaced in PR descriptions or session summaries.

---

## Audit and accountability

Per the Marelli operationalization, every Maestro-directed action leaves a trail:

- **Per session**: a session summary in [`docs/session-summaries/`](../session-summaries/) recapping what was done,
  what's outstanding, and what was learned. The
  [planning-update-execution session summary](../session-summaries/2026-05-07-planning-update-execution-session-summary.md)
  is the current canonical example of the format.
- **Per decision**: an ADR in [`docs/adr/`](../adr/) with stable `DEC-NNNN` id. Indexed in
  [DECISIONS.md](../../DECISIONS.md).
- **Per Worker dispatch (Phase 2+)**: an audit-log entry at `~/.linus/audit.jsonl` per DEC-0030/0031/0032, recording
  `cot_budget`, `memory_mode`, scratchpad and answer hashes.
- **Per planning arc**: a planning-update-spec in `docs/specs/` (rewritten per session) routing edits to the right
  files and acting as the merge-log when complete (see
  [`planning-update-spec.md`](../specs/planning-update-spec.md) for the canonical example, marked COMPLETE
  2026-05-07).

The audit chain is what makes Schulz/Marelli/Botvinick-Gershman more than philosophy — it is the engineering surface
that converts "the human reviews" into "the human can verify in N minutes that the work actually happened the way
the work product claims."

---

## What this protocol is not

- **Not the Worker protocol.** That is [`maestro-worker-protocol.md`](maestro-worker-protocol.md). This document
  describes Maestro-as-a-role; that document describes the per-task delegation loop.
- **Not a static contract.** Behavioral disciplines are appended as new failure modes are observed (the L1–L7
  block above is the current set as of 2026-05-07; expect L8+ additions over time).
- **Not a replacement for ADRs.** Specific decisions live in `docs/adr/`. This document captures the meta-discipline
  under which those decisions get made.
- **Not Phase-frozen.** The work-split and discipline rules will evolve as Linus matures and especially as the
  Phase 8b transition (Linus-as-Maestro) becomes real. The current shape is the starting shape, not the final shape.

---

## Related reading

- [`docs/protocols/maestro-worker-protocol.md`](maestro-worker-protocol.md) — per-task delegation loop.
- [`docs/protocols/curation-protocol.md`](curation-protocol.md) — curation discipline for `repos/`, `context/`,
  `docs/`.
- [`CLAUDE.md`](../../CLAUDE.md) Engineering Conventions — operational discipline rules, including L1–L7 above.
- [`SAFETY.md`](../../SAFETY.md) — autonomy tiers, sandbox policy, supply-chain incident response.
- [`VISION.md`](../../VISION.md) Maestro/Worker discipline section — the orchestra metaphor and the cognitive-
  throughput anchor.
- [`docs/specs/planning-update-spec.md`](../specs/planning-update-spec.md) — execution log for the
  planning arc that produced this protocol's behavioral discipline section.
- [`docs/syntheses/llms-in-science-synthesis.md`](../syntheses/llms-in-science-synthesis.md) — the Schulz / Marelli /
  Botvinick-Gershman / Bender four-perspectives framework that anchors the Philosophy section.

---

_This is an initial draft. Amendments via the planning-write-back-cadence convention (DEC-0026) — the next planning
session that touches Maestro discipline updates this file in the same PR as its other write-back artefacts._
