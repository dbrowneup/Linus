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

The 12 entrepreneurship-derived items from the new synthesis live in their own section at the end of this document,
all marked deferred-but-tracked per the synthesis posture.

---

## Round 1 sweep status — RESOLVED (2026-05-06)

The 2026-05-04 sweep promoted ~60 candidate questions from the post-fan-out syntheses into S1–S60 plus E1–E12.
All of those items are now resolved:

- **S1–S10 (Tier 1)**: resolved 2026-05-06 via DEC-0044 through DEC-0051. See
  [`answered-questions.md`](answered-questions.md#sweep-tier-1--s1s10-resolved-2026-05-06).
- **S11–S31 (Tier 2)**: resolved 2026-05-06 via DEC-0052 through DEC-0054 plus inline updates. See
  [`answered-questions.md`](answered-questions.md#sweep-tier-2--s11s31-resolved-2026-05-06).
- **S32–S60 + E1–E12 (Tier 3 + Entrepreneurship)**: resolved 2026-05-06 across CLAUDE.md, VISION.md, ROADMAP.md,
  GLOSSARY.md, and protocol/spec docs. See
  [`answered-questions.md`](answered-questions.md#sweep-tier-3--entrepreneurship-resolved-2026-05-06).

The 16-ADR memory-pillar batch (M1–M17) was resolved earlier (2026-05-03 via DEC-0028 through DEC-0043). Round 1 of
the sweep cleared the question backlog as it stood at 2026-05-04.

---

## Round 2 sweep promotions (added 2026-05-07)

A 2026-05-07 sweep across the 25 syntheses (12 with explicit Open-questions sections cleaned in PR #21; 13 thematic
syntheses surveyed for inline questions) promoted the items below as the new working set. Numbering uses the `R2-NN`
prefix to mark this as the second sweep round and keep the audit trail legible alongside the resolved S/M/E series.

The promoted items reflect what changes next concrete action. Items left in the syntheses as still-open but not
promoted here are tracked in their source documents and listed in the
[`docs/specs/synthesis-cleanup-spec.md`](../specs/synthesis-cleanup-spec.md) "Surfaced ambiguities" section. Most are
implementation-detail or empirical questions that resolve naturally during Phase 1c/2a execution rather than needing
a planning-session decision now.

### Tier 1 — block Phase 1 / Phase 2a architecture

These eight items each block a Phase 1 spike or a Phase 2a architectural decision. Walk them first.

- **R2-01. Pydantic-ai as a core inference-path dependency vs. lightweight bespoke wrapper.** Adopting `pydantic-ai`
  reduces Linus orchestration code by ~70% but adds an external dependency to the core path. The alternative is a
  bespoke Agent wrapper using only `pydantic` (already a dependency), keeping the dependency graph minimal.
  Phase 2a architecture decision; sets the substrate for every Worker dispatch. _(g11-agent-frameworks.)_
- **R2-02. Worker review gates: self-review against rubric, or Dan-review at task completion.** Superpowers
  enforces two-stage review (spec compliance, then code quality) before a Worker can mark a task complete. Phase 2a
  trade: self-review requires a rubric in every spec; Dan-review is simpler for Phase 2a but less scalable for
  Phase 3 multi-agent workflows. _(g11-agent-frameworks.)_
- **R2-03. Dan task suite scope and grader design (Phase 1d).** Promptfoo can run 20 (fast iteration) or 100 (more
  regression coverage) tasks against the local Ollama Worker. For Dan's domain (genomics Q&A, metagenomics analysis,
  paper summarization), semantic-similarity assertions may not capture correctness — gene names are right or wrong,
  not "similar." Phase 1d blocks on Dan authoring the tasks and choosing the grader strategy. _(g11-agent-frameworks
  + cross-cutting Phase 1d need.)_
- **R2-04. Context-routing policy in the Phase 2a orchestration layer.** Agent-Skills-for-Context-Engineering
  argues that context quality, not model size, is the primary determinant of Worker effectiveness. When does
  session history get summarized vs. passed verbatim? When does a KB query result get truncated vs. passed in full?
  Phase 2a spec needs an explicit context-routing policy or commits to deferred empirical tuning.
  _(g11-agent-frameworks.)_
- **R2-05. Open Responses vs Chat Completions for the Phase 2a serving protocol.** Ollama serves the legacy Chat
  Completions shape; the Open Responses spec adds stateful response threading and the SSE event catalog. Cline and
  openclaw speak both; claw-code-local speaks OpenAI-compat generically. Locks in client compatibility for Phase 2a;
  short spike against the Open Responses spec is recommended before commit. _(g7-harnesses.)_
- **R2-06. Stdio or streamable-http transport for the Phase 2 MCP launch.** g6 recommends streamable-http on
  localhost from day one (Cline + Claude Code want simultaneous access; spawning N stdio children is fragile).
  Counter-arguments: startup latency, process isolation, dependency simplicity. Phase 2a transport-level decision.
  _(g6-mcp-tools.)_
- **R2-07. Vault location for hyalo/keppi (Phase 2 config).** Hyalo's `.hyalo.toml` must point at a concrete path.
  Three candidates: `context/notes/` (gitignored, personal), a new top-level `vault/` (tracked, Dan-owned), or
  inside `modules/KnowledgeBase/` next to the paper corpus. Each implies different gitignore policies and KB-
  submodule interactions. Decision feeds Phase 3 KB-tooling layer. _(g5-graph-tools.)_
- **R2-08. Hyalo vs keppi 30-minute bake-off (Phase 1 spike).** Run both tools on the same sample vault for the
  five operations (find by tag, bulk set status, rename + link rewrite, lint with schema, summary). Closes the
  "confirm which operations keppi actually supports" question and produces an ADR verdict on responsibility split.
  _(g5-graph-tools.)_

### Tier 2 — shape Phase 2–6 architecture

Nineteen items that don't block a single concrete next action but compound into the architecture as Phase 2 work
proceeds.

- **R2-09. Schema lift verbatim or extended for the episodic store v0.** The openaugi `(blocks, links)` schema
  satisfies DEC-0029's requirements with almost no friction. Adopt verbatim with Linus-specific columns added, or
  rename to `(episodes, episode_links)` to signal ownership boundary from the first migration? Decision before the
  first DEC-0029 migration file. _(g4-memory.)_
- **R2-10. sqlite-vec vs Qdrant for memory v0.** Omega-memory and openaugi prove that 384-dim cosine search inside
  the same SQLite file satisfies Phase 2 recall requirements with no separate service. The Algorithm says delete
  the Qdrant service from v0 scope and add it back if sqlite-vec proves insufficient. _(g4-memory.)_
- **R2-11. Trust-level binary vs weighted continuous.** Anamnesis calibrates AI-derived records at weight 1.0
  initial, earning up to 4.0 via reweight cycles. DEC-0029's `trust_level` field carries the same concept at the
  binary level. Anamnesis-style continuous weight or binary sufficient for Phase 2? _(g4-memory.)_
- **R2-12. Phase 1f framing for claude-squad + claude-task-master.** g7 argues they are not competitors but
  planner and runner. Does the Phase 1f ADR capture "adopt both patterns, neither product," or declare one as
  primary and the other supplementary? _(g7-harnesses.)_
- **R2-13. Two-tier LLM config as a named convention.** TradingAgents' `deep_think_llm` / `quick_think_llm` split
  is a transferable pattern. Formalize in ARCHITECTURE.md as a named config pattern before Phase 3, or leave
  implicit in per-skill configuration? _(g10-finance.)_
- **R2-14. Biology RLVR verifier candidates (Phase 6 scope).** ether0's chemistry recipe generalizes if the oracle
  side does. Candidates: BLAST, ESMFold pLDDT, ClinVar, eQTL direction-of-effect — all sub-second per call,
  near-deterministic, no remote paid API. Dan's genomics experience is the filter for which biology tasks have
  cheap-enough verifiers to run in a tight RL loop. Shapes Phase 6 scope. _(g8-sci-agents.)_
- **R2-15. Phase 7 sandbox decision for the notebook-agent Worker.** Three options: emulated x86 Docker (slow for
  BLAST, IQ-TREE, SPAdes on M1 Max); arm64 bioinformatics image (real packaging work against bioconda pins);
  Linus-native sandbox via per-Worker conda env + sandbox-exec. The right starting point depends on which
  bioinformatics tools Dan actually needs in the analysis loop. _(g8-sci-agents.)_
- **R2-16. Bio-Task Bench Intermediate plateau interpretation (action item).** Both bioSkills agents land at
  0.96–0.97 on Intermediate with or without skills loaded. Three explanations are consistent with the data; the
  one Dan finds most credible changes how aggressively to invest in skills as an autonomy-graduation mechanism.
  Worth a 30-minute look at five representative Intermediate tasks. _(g9-bio.)_
- **R2-17. Bacformer vs Dan's existing operon-calling pipelines.** A 300M protein-context-aware encoder placed
  relative to Dan's 13 years of genomics tooling: replacement, ensemble member, or "interesting embedding signal
  to graft onto existing scoring"? Determines whether Bacformer is a Phase 7 skill surfacing results to Dan, or a
  Phase 7 capability feeding upstream of Dan's analyses. _(g9-bio.)_
- **R2-18. ProtHGT vs Horizyn-1 vs BioReason-Pro for the first protein-function skill.** Three architectures
  (KG-grounded reasoning; cross-modal retrieval; chain-of-thought reasoning over a frozen encoder). Phase 7 first-
  skill choice; criteria depend on Dan's typical protein-function questions and whether KG vs free-text reasoning
  fits domain workflows better. _(function-annotation-discovery.)_
- **R2-19. FutureHouse evaluation philosophy adopt wholesale.** The insufficient-info option, the human-pairwise
  + LLM-judge + structural-grounding stack, the canary-protected MCQ approach. Strong methodological prior
  art for Linus's `benchmarks/dan_tasks/biology/`. Adopt the philosophy or pick à la carte? _(function-annotation-
  discovery.)_
- **R2-20. Generalist × specialist FM combinations sequencing for Phase 7.** ROADMAP.md commits the first three
  pairs (Trias+GenNA, REBEAN+DeepSeMS, Bacformer+DeepSeMS); biology-phase7-roadmap.md captures the deferred Phase 8
  pairs. Question: which pair gets resourced first within Phase 7, and what failure mode would cause a re-sequence?
  _(generative-biology + biological-foundation-models.)_
- **R2-21. Wh per task as a benchmark column or a separate energy ledger.** The Google note's per-prompt energy
  framing argues energy belongs alongside throughput as a first-class metric. Phase 1c+ benchmark methodology
  decision. _(infra-foundations.)_
- **R2-22. Implement the write-back rule across parallel Workers.** The write-back rule (every task produces a
  deliverable + KB update proposals) is operationally clear for serial work, less so for parallel Workers writing
  to overlapping pages. DEC-0022 resolved KB-write coordination at the policy level; the question now is the
  implementation pattern (lease, optimistic-merge, branch-per-Worker). _(llm-wiki.)_
- **R2-23. Immutable atomic notes vs mutable wiki pages.** The community is split. Immutable atomic Zettelkasten
  notes are append-only, link-rich, content-hashable; mutable wiki pages compound knowledge but invite drift.
  Phase 2/3 KB substrate-level architecture choice. _(llm-wiki.)_
- **R2-24. EPISTEMIC-STANDARDS.md as Phase 2a deliverable.** Marelli operationalized at the doc level: define the
  claim categories Linus distinguishes (`[!source]`, `[!analysis]`, `[!unverified]`, `[!gap]` per DEC-0023) and the
  evidentiary standards for each. Currently deferred in `planning-update-spec.md`; needs KB schema (DEC-0048) and
  claim types (DEC-0023) live before the doc is operational. _(llms-in-science; S22 originally.)_
- **R2-25. E3 dynamic tool activation timing.** OpenBB's `openbb-mcp` per-session tool activation pattern keeps
  tool-budget cost bounded for small local Workers. Adopt as Phase 2 default, or defer to Phase 3 when the actual
  tool surface is large enough to need it? _(entrepreneurship E3.)_
- **R2-26. E10 open-source-by-default architecture audit.** With E1 codified (open-source-by-default release
  posture), the architecture inherits constraints: license-compatible deps only, contributor-friendly module
  boundaries, no proprietary internal APIs that would need stripping for release. Short audit pass when Phase 2 is
  actively underway to surface anything that silently assumed proprietary deployment.
  _(entrepreneurship E10.)_
- **R2-27. Q-Maestro: Linus-as-Maestro quality threshold and Phase target (carried forward).** Dan confirmed
  2026-05-06 the long-term goal is for Linus to operate fully offline as Maestro. VISION.md captures the Phase 8b
  north star. Open sub-questions: (a) precise Maestro-class eval threshold that triggers Phase 8b planning (current
  proposal: within 10 pp of hosted Claude); (b) does this change any Phase 2–7 architectural constraints, or is it
  purely a quality target; (c) how does the Maestro-class eval suite serve double duty as Worker-selection
  instrument and Linus-Maestro readiness indicator? _(VISION.md; ROADMAP.md Phase 8b.)_

### Tier 3 — documentation, conventions, longer-horizon scope

A reservoir for Phase 4+ planning, longer-horizon research, conventions worth codifying eventually, and action
items that depend on Dan's domain-specific reading. Dip in when context suggests an item matters now. Items grouped
by source synthesis for quick scanning.

**Memory and KB substrate (g4, llm-wiki).** R2-28 cross-vendor enforcer for memory (g4); R2-29 confidence decay
rate for claim types (llm-wiki); R2-30 FUNGI processing protocol as KB ingest step (llm-wiki); R2-31 entity
deduplication threshold (llm-wiki); R2-32 mostly-correct-is-broken handling for high-stakes content (llm-wiki).

**KB tooling (g5, g6).** R2-33 paper-corpus edge weights for blast radius (g5); R2-34 AGPL re-implementation
policy as DECISIONS.md entry (g5); R2-35 InfraNodus self-hosting as Phase 3 stretch (g5); R2-36 ontomics
benchmarking scope on KnowledgeBase corpus (g6); R2-37 vectorless bake-off model selection — hosted vs local
(g6); R2-38 WeKnora per-KB indexing toggle for Phase 2 design (g6).

**Harnesses and orchestration (g7, g11).** R2-39 origin as Phase 2b memory sidecar candidate (g7); R2-40 OTel
local storage vs Laminar deployment timing (g11).

**Bio benchmarks and tools (g8, g9).** R2-41 ProtocolQA as personal calibration test (g8 — 1-hour read);
R2-42 BioReason benchmark legitimacy (g9 — 30-min curation read); R2-43 deepsems cryptic-BGC reproducibility
(g9 — paper read).

**Finance / commercial surface (g10, entrepreneurship).** R2-44 financial-intelligence as Phase 7 priority or
"nice eventually" (g10); R2-45 AGPL stance before Phase 8 (g10); R2-46 Nixtlaverse as Phase 7 forecasting skill
(g10); R2-47 financial-execution safety boundary in SAFETY.md (g10); R2-48 first monetizable capability and when
(skills-and-practices); R2-49 Maestro-only to Maestro+Worker transition handling in practice (skills-and-
practices); R2-50 E4 adversarial debate as Worker primitive (entrepreneurship, was S55); R2-51 E5 two-tier
compaction lift (entrepreneurship); R2-52 E7 when does the entrepreneurial-gunpowder claim become testable
(entrepreneurship); R2-53 E8 Botryonyx/CaribAlgae as background-only (entrepreneurship); R2-54 E9 pricing-anchor
honesty at exploration time (entrepreneurship).

**Biology FM strategy (biological-foundation-models, function-annotation-discovery, generative-biology).**
R2-55 Generalist vs specialist Worker default for Phase 7 (biological-foundation-models); R2-56 METL pattern apply
now or wait for second instance (biological-foundation-models); R2-57 Evo 2 + Wave 3 generative-phages mini-
synthesis (biological-foundation-models); R2-58 swap BioReason-Pro encoder to LucaOne or ProteinReasoner
(function-annotation-discovery); R2-59 Linus default mode for function prediction (function-annotation-discovery);
R2-60 open-answer vs MCQ as methodology principle (function-annotation-discovery); R2-61 FKC steering as generic
Linus inference-time pattern (generative-biology).

**Activation / safety research (safety-alignment-privacy).** R2-62 supervised activation steering as cheaper
alternative to LoRA fine-tuning (Phase 6+); R2-63 activation steering on BitNet ternary weights (research
question); R2-64 dataset source for Linus's first concept vectors (Phase 6+); R2-65 mirroring/sycophancy
detection on Maestro outputs (Phase 7+).

**Foundation watching (infra-foundations).** R2-66 when does Linus need diffusion-model internals vs. treat as
black boxes (watch-the-field); R2-67 is local actually greener than hosted when boundary drawn comprehensively
(research framing); R2-68 KB index bottleneck at corpus size (empirical; revisit at 100–200 papers indexed).

**LLM Wiki research (llm-wiki).** R2-69 flash-mode inference + activation pruning interaction (open research,
revisits at Phase 6).

**Dan-personal reflection (llms-in-science).** R2-70 which of the four Binz perspectives most resonates for Dan
and is that reflected in current docs (Dan-time question; not action-blocking).

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
