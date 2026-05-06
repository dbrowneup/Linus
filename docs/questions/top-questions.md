# Top Questions

The current working agenda — a focused, prioritized subset of the open questions in
[open-questions.md](open-questions.md). Items here are organized into tiers by how much each answer changes the next
concrete action, not by how interesting they are. Walk Tier 1 first; Tier 2 follows naturally; Tier 3 is a reservoir to
dip into when context suggests one of those threads matters now.

Resolved items have moved to [answered-questions.md](answered-questions.md), keeping this document focused on what
still needs to be decided. The full per-source archive is in [open-questions.md](open-questions.md). Questions that
recurred across multiple notes have been merged here; "worth a synthesis note?" invitations have been collapsed into
documentation-cadence entries.

---

## Landscape remapping note (2026-05-05)

A landscape remapping pass on 2026-05-05 closed all unmapped repo-cluster anchors and added a 14th thematic
synthesis (entrepreneurship). The relevant cross-cuts that touch the existing sweep items below:

- **S11 / S12** (LAB-Bench MCQ + BixBench harness; FutureHouse evaluation philosophy ADR) — _primary anchor moved_
  from function-annotation-discovery to [`infra-foundations-synthesis.md`](../syntheses/infra-foundations-synthesis.md).
  Domain treatment retained in the function-annotation-discovery synthesis as load-bearing for the skill argument;
  the Tier-1-equivalent benchmark-adoption action lives on the infra-foundations row of the synthesis matrix.
- **S22 / S23** (EPISTEMIC-STANDARDS.md; Maestro-class evaluation tier) — llms-in-science synthesis now anchors on
  g8-sci-agents (paper-qa primarily). Recommendation flow unchanged; substrate evidence sharpened.
- **S26** (hyalo + keppi as Phase 3 KB tooling) — primary cluster anchor (g5-graph-tools) is now infra-foundations
  rather than freestanding.
- **S28** (Wh-per-task as benchmark column vs ledger) — infra-foundations remapping reinforces the
  benchmark/methodology framing.

The 12 entrepreneurship-derived items from the new synthesis live in their own section
([Entrepreneurship sweep promotions (added 2026-05-05)](#entrepreneurship-sweep-promotions-added-2026-05-05)) at
the end of this document, all marked deferred-but-tracked per the synthesis posture.

---

## Sweep promotions (added 2026-05-04)

A second-wave promotion pass landed on 2026-05-04, after the Section 7 fan-out closed and after nine thematic syntheses
were written in `docs/syntheses/` (humans-teams-performance, generative-biology, infra-foundations,
native-low-bit-apple-silicon, llms-in-science, function-annotation-discovery, agentic-systems, safety-alignment-privacy,
biological-foundation-models). Roughly 60 candidate questions surfaced; the items below are the ones that change next
concrete action and should be carried into the next planning session. The complete archive lives in
[open-questions.md](open-questions.md) under each source-synthesis section and in the Group 1–10 cluster sections.

These items are _unresolved_ as of 2026-05-04 and form the next planning session's working set.

### Tier 1 (sweep) — block Phase 1 / Phase 2 architecture

_S1–S10 resolved 2026-05-06. See [answered-questions.md](answered-questions.md#sweep-tier-1--s1s10-resolved-2026-05-06) and ADRs DEC-0044–DEC-0051. Tier 1 (sweep) is now empty; Tier 2 becomes the working set._

### Tier 2 (sweep) — shape Phase 2–6 architecture

_S11–S31 resolved 2026-05-06. See [answered-questions.md](answered-questions.md#sweep-tier-2--s11s31-resolved-2026-05-06) and ADRs DEC-0052–0054. Tier 2 (sweep) is now empty; Tier 3 becomes the working set._

### New Tier 2 item (added 2026-05-06)

- **Q-Maestro. Linus-as-Maestro quality threshold and Phase target.** Dan confirmed 2026-05-06 the long-term goal is
  for Linus to operate fully offline as Maestro — directing Workers, synthesizing research-quality outputs, without
  hosted Claude in the loop. VISION.md updated (Phase 8b north star). Open sub-questions: (a) What is the precise
  Maestro-class eval threshold that triggers Phase 8b planning (current proposal: within 10 pp of hosted Claude on
  the Maestro-class suite)? (b) Does this change any Phase 2–7 architectural constraints, or is it purely a quality
  target? (c) How does the Maestro-class eval suite (S23 resolution) serve double duty as both a Worker-selection
  instrument and a Linus-Maestro readiness indicator? _(VISION.md; ROADMAP.md Phase 8b; S23.)_

### Tier 3 (sweep) — documentation, conventions, longer-horizon scope

_S32–S60 and E1–E12 resolved 2026-05-06. See
[answered-questions.md](answered-questions.md#sweep-tier-3--entrepreneurship-resolved-2026-05-06). Tier 3 (sweep) and
all Entrepreneurship items are now empty; the full question backlog has been cleared._

---

## How to use this document

This document holds only _open_ questions — items that still need a decision. Tier 1 entries change next concrete
action; walk those first. Tier 2 follows as natural shape-of-the-architecture work. Tier 3 is a reservoir to dip into
when context suggests a thread matters now (e.g., Phase 4 starts → revisit Tier 3 entries on Phase 4 scope).

Each Tier 1 answer typically resolves 2–3 downstream questions automatically, so progress compounds. As decisions are
made, propagate the resolution into:

1. **[answered-questions.md](answered-questions.md)** — move the question text and pair it inline with the resolution,
   ADR pointer, and rationale.
2. **[total-landscape.md](../landscapes/total-landscape.md)** — the cross-cutting map; update affected sections.
3. **ROADMAP.md** — phase-level changes flow here.
4. **[`docs/adr/`](../adr/)** — one per-file ADR per Tier 1 decision (Tier 2/3 may share ADRs by topic).
5. **The relevant per-note `Open questions for Dan`** sections in `docs/repo-notes/` and `docs/paper-notes/` — flag the
   item as resolved with a pointer back to the ADR.

[total-landscape.md](../landscapes/total-landscape.md) integrates repos, papers, and the practitioner syntheses into a
single cross-cutting view. [open-questions.md](open-questions.md) is the verbose source archive.
[answered-questions.md](answered-questions.md) is the resolved-question archive. This file (`top-questions.md`) is the
prioritized working set distilled from those.
