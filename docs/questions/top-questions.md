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

- **S32–S35. Naming/archetype:** "PLM + heterogeneous KG + graph transformer" archetype (name after second
  out-of-corpus replication; ProtHGT lead); "dual-encoder cross-modal retrieval" archetype (name now; Horizyn-1 lead);
  "generate→score→filter→wet-lab" generative-biology archetype (paired with Evo 2 paper note); "world model"
  terminology disambiguation (PAN/WHAM/Kosmos/memory-pillar all use it differently — pick `task_state`,
  `shared_context`, or `belief_state` for orchestration-layer surface). _(function-annotation-discovery,
  generative-biology, infra-foundations.)_
- **S36–S40. Doc additions:** VISION.md cite Binz et al. four-perspectives explicitly;
  `docs/maestro-worker-protocol.md` Philosophy section naming the Schulz/Marelli/Botvinick-Gershman blend;
  `goal_orientation` field in Worker spec template (hard requirement vs optional annotation); preserve
  multidisciplinary-time-allocation as VISION/CLAUDE/ROADMAP entry; "modern Transformer reference" paper added to
  corpus to bridge 2017→2025 (RoPE, RMSNorm, SwiGLU, GQA, pre-norm conventions). _(llms-in-science,
  humans-teams-performance, infra-foundations.)_
- **S41–S44. Process/cadence:** prompt-vault placement (drop from G4 synthesis or create "miscellaneous prompt
  libraries" group); Ollama vs non-Ollama Worker mix for synthesis pass; sub-agent hook bypass process note (Worker
  writes, Maestro formats, Maestro commits); internal-error result-message recovery protocol (check filesystem state
  first when Worker results are missing). _(fan-out outstanding #1–4.)_
- **S45–S52. Spike candidates / longer-horizon:** DeepSeMS Pfam-domain encoder modernization with LucaOne or
  ProteinReasoner (Phase 6 spike); FKC steering as generic Linus inference-time pattern (record on second instance);
  activation-steering generality (Phase 6 generalization across modulations) and BitNet compatibility (`experiments/`
  spike); concept-vector dataset source (local vs hosted); mirroring/sycophancy detection on Maestro outputs (small
  audit-log extraction pipeline); METL simulation-pretrained pattern (wait for second instance); Evo 2 + generative
  phages mini-synthesis (Wave 3 prep); ProteinReasoner checkpoint release watch (BioMap GitHub, `airkingbd` HF org);
  benchmarks/low_bit/ as a dedicated suite vs folded into dan_tasks. _(generative-biology, safety-alignment-privacy,
  biological-foundation-models, native-low-bit-apple-silicon.)_
- **S53. Local vs hosted greener** comparison experiment now (one focused study) or defer to Phase 5 when the chat
  surface and energy ledger ship. _(infra-foundations.)_
- **S54. WHAM consistency/diversity/persistency triple** lifted wholesale vs derived from Linus-specific workflow
  introspection first. _(infra-foundations.)_
- **S55. Adversarial debate as a Worker primitive** — empirical question for `benchmarks/dan_tasks/`; Stony Brook
  QuantAgent is partial counter-evidence (works without debate, majority-with-confirmation as integrator).
  _(agentic-systems.)_
- **S56. Agentic-system theory as first-class architectural input.** HKUST QuantAgent regret bound is the first formal
  result; KB coverage growth as dominant lever on suboptimality is the design intuition worth promoting to a
  constraint. Brief "applicable theory" section in Phase 3 spawner ADR. _(agentic-systems.)_
- **S57. `docs/maestro-protocol.md`** — Values paper argues Maestro is not a black box and Linus depends on specific
  characterized behaviors. Cleaner than extending VISION.md because the dependencies are operational rather than
  aspirational. _(safety-alignment-privacy.)_
- **S58. Four SAFETY.md additions: single PR or staged?** Synthesis-internal answer is single PR with explicit
  per-section Dan review. _(safety-alignment-privacy.)_
- **S59. Session-rhythm metric** — worth tracking, or would degrade into theatre? Cheap to prototype on existing commit
  history; compute retrospectively before instrumenting as prospective gate. _(humans-teams-performance.)_
- **S60. "No stateful Docker on macOS" rule as explicit reference** in the eventual Phase 8 "what we don't build"
  section, with anamnesis (Postgres+pgvector), WeKnora (6–10 container stack), and finch (x86_64 miniconda) as worked
  counter-examples. _(fan-out outstanding #13.)_

---

## Entrepreneurship sweep promotions (added 2026-05-05)

These twelve items derive from the new
[entrepreneurship synthesis](../syntheses/entrepreneurship-synthesis.md). All are explicitly **deferred-but-tracked**
per the synthesis posture: Linus needs to demonstrate it is a useful intelligent tool before any commercial-surface
decision becomes load-bearing. The items are recorded so the thread is findable later, not so they are answered now.

### Tier 1 (entrepreneurship) — release-posture and framing decisions worth making early

- **E1. Open-source release posture as a default architectural commitment.** Codify "open-source-by-default if
  Linus succeeds" in VISION.md, citing the Pauling/Torvalds "for science, for society" rationale. Carve-out: if
  Linus succeeds enough that Dan wants to commercialize a derivative, that decision remains open. Architectural
  decisions that follow (license-compatible deps, contributor-friendly module boundaries, no proprietary internal
  APIs) are easier to honor as defaults than as retrofits. _(Source: entrepreneurship synthesis, E1.)_
- **E2. Reframe the Phase 2 deliverable from `docs/entrepreneurial-surface.md` to `docs/knowledge-mining-surface.md`.**
  The 2026-05-03 Tier 2 #14 resolution committed to a doc by the original name; the 2026-05-05 reframe argues the
  real entrepreneurial gunpowder is the knowledge in Dan's files, with Linus as the mining tool — productization
  is downstream. Rename to reflect this priority order. _(Source: entrepreneurship synthesis, E2.)_

### Tier 2 (entrepreneurship) — transferable g10-finance patterns worth tracking (not commercial-specific)

These are useful regardless of whether Linus ever ships a commercial offering — they sharpen the internal
architecture too. Surfaced from g10-finance because that cluster is the entrepreneurship synthesis's primary
anchor; the patterns transfer.

- **E3. Dynamic-tool-activation as Phase 2/3 orchestration primitive.** OpenBB's `openbb-mcp` per-session tool
  activation pattern keeps tool-budget cost bounded for small local Workers. Open: adopt as Phase 2 default
  tool-registry behavior, or defer to Phase 3 once the actual tool surface is large enough to need it? The
  fastmcp-based registry should adopt it; timing is the open question. _(Source: entrepreneurship synthesis, E3;
  g10-finance.)_
- **E4. Adversarial-debate as a Worker primitive — empirical question.** TradingAgents' two-tier LLM split +
  decision-log pattern (one Worker finds supporting evidence, another finds contradicting evidence, Maestro
  arbiter writes the answer with both logs) versus Stony Brook QuantAgent's no-debate
  majority-with-confirmation pattern. Cross-references **S55** to avoid duplication; this entry sharpens the
  question by naming TradingAgents specifically as the debate-positive case. _(Source: entrepreneurship
  synthesis, E4; g10-finance.)_
- **E5. Two-tier compaction for long sessions.** dexter's `microcompact` + full-compact pattern: lightweight
  per-turn pass plus full LLM-summarization pass at an auto-compact threshold; preserves all numerical data,
  forbids tool calls during compaction, carries a structured drop summary. Lift verbatim with attribution into
  the Phase 2 context-manager spec, or design from scratch? Recommendation: lift; tested prior art. _(Source:
  entrepreneurship synthesis, E5; g10-finance.)_
- **E6. SKILL.md as the Phase 7 skills bundle format.** dexter, OpenBB, bioSkills, scientific-agent-skills, and
  autoresearch all use YAML-frontmatter markdown skills with a single `skill` tool. Commit to this format as the
  Linus standard for Phase 7, or evaluate alternatives? Recommendation: commit; the format is converging toward a
  de facto standard. Cross-references **S30** on inaugural skills bundle. _(Source: entrepreneurship synthesis,
  E6.)_

### Tier 3 (entrepreneurship) — longer-horizon framing, deferred until Linus is demonstrably useful

- **E7. The "knowledge in Dan's files is the entrepreneurial gunpowder" claim — when does it become testable?**
  The whiteboard pipeline places business ideas at the end of the chain, downstream of Linus working,
  fine-tunable, and benchmarkable. Recommendation: Phase 5 at earliest (chat surface + KB + memory all working
  end-to-end on real Dan tasks). Until then, the question is premature. _(Source: entrepreneurship synthesis, E7.)_
- **E8. Botryonyx and CaribAlgae as background, not as direct opportunity hooks.** Algae as a domain is hard to
  scale quickly or profitably; Dan still loves the science but doesn't see a viable new-business path right now.
  Keep Botryonyx referenced in CLAUDE.md as the source of the speed-and-evidence instinct (no change); soften any
  synthesis text that read as "build another algae company." The algae background informs taste and
  pattern-recognition; it is not a target. _(Source: entrepreneurship synthesis, E8.)_
- **E9. Pricing-anchor honesty.** The dollar ranges in the seven opportunities (extracted from skills-and-practices
  Section 5) are anchors borrowed from adjacent SaaS/consulting markets, not Dan-validated. Revisit only when an
  opportunity is actually being explored; until then, anchors are placeholders. _(Source: entrepreneurship
  synthesis, E9.)_
- **E10. Open-source-by-default release-posture implications for the architecture.** If Linus is open-source by
  default (E1), the architecture inherits constraints: license-compatible deps only, contributor-friendly module
  boundaries, no proprietary internal APIs that would need stripping for release, public benchmarks rather than
  private moats. A short audit pass when E1 codifies (likely Phase 2) to surface anything that silently assumed
  proprietary deployment. _(Source: entrepreneurship synthesis, E10.)_
- **E11. AlphaGenome non-commercial license — relevant only conditionally.** **S29** already tracks this on the
  biology pillar's commercial readiness. From the entrepreneurship-synthesis perspective: with the 2026-05-05
  reframe (productization deferred, open-source-by-default), AlphaGenome's NC license is _not_ blocking; it is a
  constraint to revisit if and when commercial use becomes a real question. Cross-reference S29; do not duplicate.
  _(Source: entrepreneurship synthesis, E11.)_
- **E12. `docs/knowledge-mining-surface.md` first-draft scope (renamed per E2).** The document captures: Dan
  profile, the local-files-as-gunpowder reframe, the whiteboard pipeline (workspace → custom tools →
  private-Claude-equivalent → fine-tuning → eventual entrepreneurial application), the seven opportunities as
  long-tail possibilities (not action items), the g10-finance transferable patterns, and an explicit
  "deferred until Linus is demonstrably useful" stance. Phase 2 (framed as tracking, not acting) or Phase 3?
  _(Source: entrepreneurship synthesis, E12.)_

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
