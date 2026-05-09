# Synthesis Refinement Spec

**Date:** 2026-05-08 **Status:** in execution **Owner:** Maestro (Dan + Claude Code)

**Related:** [`docs/syntheses/`](../syntheses/) (14 thematic + 11 cluster); recent paper- and repo-note cleanup arc
(2026-05-07 → 2026-05-08); [`docs/questions/top-questions.md`](../questions/top-questions.md) Round 2 backlog;
[`docs/landscapes/synthesis-landscape.md`](../landscapes/synthesis-landscape.md);
[`docs/landscapes/total-landscape.md`](../landscapes/total-landscape.md).

---

## Goal

Refine all 25 syntheses (14 thematic in [`docs/syntheses/`](../syntheses/) + 11 cluster in
[`docs/syntheses/repo-clusters/`](../syntheses/repo-clusters/)) so they reflect the improvements made to the underlying
paper-notes and repo-notes during the recent cleanup arc. Each synthesis is updated in place by a Sonnet 4.6 sub-agent
that reads the synthesis, its cited notes, and the two landscape docs, then performs targeted refinement — not a
wholesale rewrite. Each agent also surfaces candidate questions for a Round 3 (R3) promotion to `top-questions.md`,
flags stale content for Maestro disposition, and proposes cross-reference updates that Maestro applies during a
consolidation pass.

The output of this effort is a single PR `agent/synthesis-refinement` containing per-file refinements, an updated
`top-questions.md` reflecting R3 promotions, and refreshed landscape docs that absorb the cross-cutting changes.

---

## Deliverables

1. **25 refined synthesis files** — in-place edits, ≤30% of any single section's content modified (see Edit Budget
   below). Files: 14 in `docs/syntheses/*-synthesis.md` + 11 in `docs/syntheses/repo-clusters/g*.md`.
2. **R3 promotion candidates** — each agent surfaces 0–5 candidate questions in their summary report. Maestro
   harvests across the 25 reports and promotes a Tier 1/2/3 batch into `top-questions.md` (R3-NN numbering, mirroring
   R2-NN convention).
3. **Cross-reference updates** — agents propose, Maestro applies. Includes any link drift between syntheses and
   updates to both landscape docs to absorb new convergences or tensions.
4. **Updated `top-questions.md` and landscape docs** — Maestro consolidation deliverable.

---

## Per-agent task contract

Each agent receives one synthesis as their target. The agent:

1. **Reads** in this order:
   - Their target synthesis (full file).
   - The synthesis's `## Inputs` / `## Cross-references` / source-list section to identify cited paper-notes and
     repo-notes.
   - Each cited note (full file).
   - [`docs/landscapes/synthesis-landscape.md`](../landscapes/synthesis-landscape.md) and
     [`docs/landscapes/total-landscape.md`](../landscapes/total-landscape.md) for cross-cutting context.
   - [`docs/questions/top-questions.md`](../questions/top-questions.md) for the current R2-NN working set (so the
     agent does not propose duplicates).
   - [`docs/questions/answered-questions.md`](../questions/answered-questions.md) to recognise which questions have
     been resolved (so the agent does not raise resolved questions as "candidates").
   - The relevant per-cluster ADRs (DEC-NNNN range) — agent identifies via grep over `docs/adr/` for the synthesis's
     subject keywords.
2. **Optionally consults** the relevant `INDEX.md` (`docs/paper-notes/INDEX.md` or `docs/repo-notes/INDEX.md`) to
   identify notes that match the synthesis's subject area but are not yet cited — these are candidates for
   weave-in if material to the synthesis's claims.
3. **Refines** the target synthesis in place. Refinement modes (in priority order):
   - **Weave in**: integrate new information, sharpened claims, or fresh perspective from cleaned-up notes.
   - **Trim**: remove stale content (resolved-and-noted items, superseded framings, duplicate prose) per Edit Budget.
   - **Sharpen**: clarify language where the recent note cleanup makes a previously-fuzzy claim crisper.
   - **Add cross-links**: where a related synthesis now bears more directly on the agent's topic (propose only;
     Maestro applies).
4. **Writes a summary report** (returned as the agent's final message) with the structure below.
5. **Does not commit, branch, or push.** Maestro handles all git operations during consolidation.

### Edit Budget

The default budget per agent is **≤30% of any single section's content modified** (added, removed, or rewritten).
Section boundaries are H2/H3 headers. The budget is per-section, not per-file — an agent can refine many sections,
each within budget.

If the agent judges that a section needs >30% modification (e.g., a section was written before a major resolution and
now reads as obsolete framing), the agent **stops short of the larger edit**, leaves the section as-is, and reports
the proposed larger change in the summary report under "Escalations". Maestro decides whether to apply the larger
refinement during the consolidation pass.

The Algorithm applies: prefer trimming over rewriting, prefer sharpening over expanding. If a paragraph can be
deleted without weakening the synthesis's argument, that is the right move.

### Cross-reference rule

Agents may **propose** cross-reference updates (between syntheses, into landscape docs, into ADRs) but **must not
edit** anything outside their target synthesis. Cross-references are consolidated by Maestro after all agents return,
to avoid races on shared files.

### Structural conventions to preserve

- Section ordering and header levels are preserved unless an Escalation is raised.
- Per the CLAUDE.md doc-type conventions, agents do not introduce new top-level structural sections or rename
  existing ones without surfacing the change as an Escalation.
- Existing resolved-question stubs (e.g., `_Resolved (DEC-NNNN, see ...): summary._`) are preserved as-is unless the
  underlying resolution has itself been superseded.
- Date markers (`Date:` lines, `(updated YYYY-MM-DD)` annotations) are updated to `2026-05-08` when the agent makes
  substantive changes to a section that carries one.

---

## Summary report structure

Each agent returns a single message structured as follows:

```markdown
# Synthesis Refinement Report — <synthesis-name>

## Diff summary
<3–5 sentence narrative of what changed and why. Lead with the largest material change.>

## Refinements applied (per section)
- **<section title>**: <one-line change description>. Edit budget: ~<N>% of section.
- ...

## Stale content flagged (no edit applied)
- **<section title>**: <description of stale content + rationale for not removing>. Recommend Maestro: <action>.
- ...

## Candidate questions for R3 promotion
1. **<short title>** (proposed Tier 1/2/3). <2–4 sentence description naming the question, why it matters, and
   what concrete next action would change based on the answer.> Source: <synthesis name>; cluster anchor: <gNN>.
2. ...

## Proposed cross-reference updates (Maestro applies)
- <synthesis A> → <synthesis B>: <reason>. Suggested edit: <one-line>.
- Landscape (`synthesis-landscape.md` | `total-landscape.md`): <suggested update>.
- ...

## Escalations (>30% section edit recommended)
- **<section title>**: <description of larger change considered + rationale>. Action withheld; Maestro decision needed.
- ...

## Edit budget status
- Sections refined: N
- Sections within budget: N
- Sections at budget (no escalation): N
- Sections escalated: N
```

If a category is empty, write "None." rather than omitting the heading.

---

## Canary phase

Before the full 23-agent fan-out, Maestro dispatches **2 canary agents** on:

1. `memory-synthesis.md` (thematic, dense, multiple cross-edges into M-series ADRs).
2. `repo-clusters/g4-memory.md` (cluster, tightly coupled to the thematic above, lets Maestro spot consistency
   between agents working on related material).

Maestro inspects both reports and the resulting diffs for:

- Edit budget compliance (no silent budget violations).
- Report structure adherence (all sections present, even if "None.").
- Quality of candidate-question proposals (specificity, actionability, non-duplication of R2-NN).
- Quality of refinements (additive, not corrosive).

If both canaries pass, the full fan-out proceeds. If quality is insufficient, Maestro adjusts the spec or escalates
to Opus for the remaining 23 agents.

---

## Full fan-out

After canary acceptance, Maestro dispatches **23 agents in parallel** — one per remaining synthesis. All agents run
in foreground (Maestro waits on the full set before consolidation; running in background loses the deterministic
checkpoint).

Targets:

**Thematic syntheses (12 remaining; memory excluded as canary):**

- security, llm-wiki, skills-and-practices, humans-teams-performance, infra-foundations,
  native-low-bit-apple-silicon, llms-in-science, function-annotation-discovery, generative-biology,
  biological-foundation-models, agentic-systems, safety-alignment-privacy, entrepreneurship.

**Cluster syntheses (10 remaining; g4-memory excluded as canary):**

- g1-apple-silicon, g2-wiki-engines, g3-wiki-patterns, g5-graph-tools, g6-mcp-tools, g7-harnesses, g8-sci-agents,
  g9-bio, g10-finance, g11-agent-frameworks.

Each agent dispatch carries: the target synthesis path, the spec reference, the model directive (Sonnet 4.6), and
the report structure template above.

---

## Maestro consolidation pass

After all 25 agents return:

1. **Diff review** — Maestro reads every refined synthesis as a diff against `main`, applies any deferred Escalations
   that pass review, reverts any refinement that introduces noise. Final review pass on each synthesis is non-optional;
   these are load-bearing documents.
2. **Cross-reference application** — Maestro applies the proposed cross-reference updates that survive review,
   including changes to `synthesis-landscape.md` and `total-landscape.md`.
3. **R3 promotion** — Maestro harvests candidate questions from the 25 reports, deduplicates against R2-NN,
   evaluates Tier assignment, and writes an R3-NN section to `top-questions.md`.
4. **Landscape refresh** — both landscape docs are updated to reflect any new convergences, tensions, or hub-edge
   changes surfaced by the refinements.
5. **PR open** — single PR `agent/synthesis-refinement` against `main`, following the PR summary template in
   CLAUDE.md.
6. **Session summary** — `docs/session-summaries/2026-05-08-synthesis-refinement-session-summary.md` written per the
   doc-type convention, including estimated wall time vs actual.

---

## Question lifecycle systematization (deferred capture)

Dan raised the broader meta-question during the planning conversation: how to systematize the surface →
triage → promote → answer → resolve → record cycle so it stops being manual mental management. The pattern this
session uses (R3 promotion harvested from a coordinated synthesis pass) is the closest the project has come to a
repeatable pipeline; it suggests a Linus-internal "question registry" subsystem worth designing.

This is captured here as a marker only. A separate `docs/specs/question-lifecycle.md` stub will be added in this
session's commit batch as a placeholder for later design — it should not divert this session's primary focus, which
is synthesis refinement.

---

## Verification

Before the PR is opened:

- All 25 syntheses show non-empty diff against `main` (or are explicitly justified as "no refinement needed" in
  Maestro's review notes).
- `git log main..HEAD --stat` shows the expected files (25 syntheses + `top-questions.md` + both landscape docs +
  this spec + `question-lifecycle.md` stub + session summary). No unexpected files.
- `git log HEAD..main --stat` is empty.
- L1/L2 discipline (CLAUDE.md state-verification + cherry-pick-to-preserve) applied.
- Edit budget compliance spot-checked against agent reports (any escalations Maestro applied are noted in PR body).

---

## Status

- 2026-05-08: spec written.
- 2026-05-08: canary phase pending.
- 2026-05-08: full fan-out pending.
- 2026-05-08: consolidation pending.
