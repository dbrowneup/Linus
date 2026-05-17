# Top Questions

The current working agenda — a focused, prioritized subset of the open questions in
[open-questions.md](open-questions.md). Items here are organized into tiers by how much each answer changes the next
concrete action, not by how interesting they are. Walk Tier 1 first; Tier 2 follows naturally; Tier 3 is a reservoir to
dip into when context suggests one of those threads matters now.

Resolved items have moved to [answered-questions.md](answered-questions.md), keeping this document focused on what still
needs to be decided. The full per-source archive is in [open-questions.md](open-questions.md). Questions that recurred
across multiple notes have been merged here; "worth a synthesis note?" invitations have been collapsed into
documentation-cadence entries.

---

## Landscape remapping note (2026-05-05)

A landscape remapping pass on 2026-05-05 closed all unmapped repo-cluster anchors and added a 14th thematic synthesis
(entrepreneurship). The relevant cross-cuts that touch the existing sweep items below:

- **S11 / S12** (LAB-Bench MCQ + BixBench harness; FutureHouse evaluation philosophy ADR) — _primary anchor moved_ from
  function-annotation-discovery to [`infra-foundations-synthesis.md`](../syntheses/infra-foundations-synthesis.md).
  Domain treatment retained in the function-annotation-discovery synthesis as load-bearing for the skill argument; the
  Tier-1-equivalent benchmark-adoption action lives on the infra-foundations row of the synthesis matrix.
- **S22 / S23** (EPISTEMIC-STANDARDS.md; Maestro-class evaluation tier) — llms-in-science synthesis now anchors on
  g8-sci-agents (paper-qa primarily). Recommendation flow unchanged; substrate evidence sharpened.
- **S26** (hyalo + keppi as Phase 3 KB tooling) — primary cluster anchor (g5-graph-tools) is now infra-foundations
  rather than freestanding.
- **S28** (Wh-per-task as benchmark column vs ledger) — infra-foundations remapping reinforces the benchmark/methodology
  framing.

The 12 entrepreneurship-derived items from the new synthesis live in their own section at the end of this document, all
marked deferred-but-tracked per the synthesis posture.

---

## Round 1 sweep status — RESOLVED (2026-05-06)

The 2026-05-04 sweep promoted ~60 candidate questions from the post-fan-out syntheses into S1–S60 plus E1–E12. All of
those items are now resolved:

- **S1–S10 (Tier 1)**: resolved 2026-05-06 via DEC-0044 through DEC-0051. See
  [`answered-questions.md`](answered-questions.md#sweep-tier-1--s1s10-resolved-2026-05-06).
- **S11–S31 (Tier 2)**: resolved 2026-05-06 via DEC-0052 through DEC-0054 plus inline updates. See
  [`answered-questions.md`](answered-questions.md#sweep-tier-2--s11s31-resolved-2026-05-06).
- **S32–S60 + E1–E12 (Tier 3 + Entrepreneurship)**: resolved 2026-05-06 across CLAUDE.md, VISION.md, ROADMAP.md,
  GLOSSARY.md, and protocol/spec docs. See
  [`answered-questions.md`](answered-questions.md#sweep-tier-3--entrepreneurship-resolved-2026-05-06).

The 16-ADR memory-pillar batch (M1–M17) was resolved earlier (2026-05-03 via DEC-0028 through DEC-0043). Round 1 of the
sweep cleared the question backlog as it stood at 2026-05-04.

---

## Round 2 sweep promotions (added 2026-05-07)

A 2026-05-07 sweep across the 25 syntheses (12 with explicit Open-questions sections cleaned in PR #21; 13 thematic
syntheses surveyed for inline questions) promoted the items below as the new working set. Numbering uses the `R2-NN`
prefix to mark this as the second sweep round and keep the audit trail legible alongside the resolved S/M/E series.

The promoted items reflect what changes next concrete action. Items left in the syntheses as still-open but not promoted
here are tracked in their source documents and listed in the
[`docs/specs/synthesis-cleanup-spec.md`](../specs/synthesis-cleanup-spec.md) "Surfaced ambiguities" section. Most are
implementation-detail or empirical questions that resolve naturally during Phase 1c/2a execution rather than needing a
planning-session decision now.

### Tier 1 — block Phase 1 / Phase 2a architecture

These eight items each block a Phase 1 spike or a Phase 2a architectural decision. Walk them first.

- **R2-01. Pydantic-ai as a core inference-path dependency vs. lightweight bespoke wrapper.** Adopting `pydantic-ai`
  reduces Linus orchestration code by ~70% but adds an external dependency to the core path. The alternative is a
  bespoke Agent wrapper using only `pydantic` (already a dependency), keeping the dependency graph minimal. Phase 2a
  architecture decision; sets the substrate for every Worker dispatch. _(g11-agent-frameworks.)_
- **R2-02. Worker review gates: self-review against rubric, or Dan-review at task completion.** Superpowers enforces
  two-stage review (spec compliance, then code quality) before a Worker can mark a task complete. Phase 2a trade:
  self-review requires a rubric in every spec; Dan-review is simpler for Phase 2a but less scalable for Phase 3
  multi-agent workflows. _(g11-agent-frameworks.)_
- **R2-03. Dan task suite scope and grader design (Phase 1d).** Promptfoo can run 20 (fast iteration) or 100 (more
  regression coverage) tasks against the local Ollama Worker. For Dan's domain (genomics Q&A, metagenomics analysis,
  paper summarization), semantic-similarity assertions may not capture correctness — gene names are right or wrong, not
  "similar." Phase 1d blocks on Dan authoring the tasks and choosing the grader strategy. _(g11-agent-frameworks;
  cross-cutting Phase 1d need.)_
- **R2-04. Context-routing policy in the Phase 2a orchestration layer.** Agent-Skills-for-Context-Engineering argues
  that context quality, not model size, is the primary determinant of Worker effectiveness. When does session history
  get summarized vs. passed verbatim? When does a KB query result get truncated vs. passed in full? Phase 2a spec needs
  an explicit context-routing policy or commits to deferred empirical tuning. _(g11-agent-frameworks.)_
- **R2-05. Open Responses vs Chat Completions for the Phase 2a serving protocol.** Ollama serves the legacy Chat
  Completions shape; the Open Responses spec adds stateful response threading and the SSE event catalog. Cline and
  openclaw speak both; claw-code-local speaks OpenAI-compat generically. Locks in client compatibility for Phase 2a;
  short spike against the Open Responses spec is recommended before commit. _(g7-harnesses.)_
- **R2-06. Stdio or streamable-http transport for the Phase 2 MCP launch.** g6 recommends streamable-http on localhost
  from day one (Cline + Claude Code want simultaneous access; spawning N stdio children is fragile). Counter-arguments:
  startup latency, process isolation, dependency simplicity. Phase 2a transport-level decision. _(g6-mcp-tools.)_
- **R2-07. Vault location for hyalo/keppi (Phase 2 config).** Hyalo's `.hyalo.toml` must point at a concrete path. Three
  candidates: `context/notes/` (gitignored, personal), a new top-level `vault/` (tracked, Dan-owned), or inside
  `modules/KnowledgeBase/` next to the paper corpus. Each implies different gitignore policies and KB- submodule
  interactions. Decision feeds Phase 3 KB-tooling layer. _(g5-graph-tools.)_
- **R2-08. Hyalo vs keppi 30-minute bake-off (Phase 1 spike).** Run both tools on the same sample vault for the five
  operations (find by tag, bulk set status, rename + link rewrite, lint with schema, summary). Closes the "confirm which
  operations keppi actually supports" question and produces an ADR verdict on responsibility split. _(g5-graph-tools.)_

### Tier 2 — shape Phase 2–6 architecture

Nineteen items that don't block a single concrete next action but compound into the architecture as Phase 2 work
proceeds.

- **R2-09. Schema lift verbatim or extended for the episodic store v0.** The openaugi `(blocks, links)` schema satisfies
  DEC-0029's requirements with almost no friction. Adopt verbatim with Linus-specific columns added, or rename to
  `(episodes, episode_links)` to signal ownership boundary from the first migration? Decision before the first DEC-0029
  migration file. _(g4-memory.)_
- **R2-10. sqlite-vec vs Qdrant for memory v0.** Omega-memory and openaugi prove that 384-dim cosine search inside the
  same SQLite file satisfies Phase 2 recall requirements with no separate service. The Algorithm says delete the Qdrant
  service from v0 scope and add it back if sqlite-vec proves insufficient. _(g4-memory.)_
- **R2-11. Trust-level binary vs weighted continuous.** Anamnesis calibrates AI-derived records at weight 1.0 initial,
  earning up to 4.0 via reweight cycles. DEC-0029's `trust_level` field carries the same concept at the binary level.
  Anamnesis-style continuous weight or binary sufficient for Phase 2? _(g4-memory.)_
- **R2-12. Phase 1f framing for claude-squad + claude-task-master.** g7 argues they are not competitors but planner and
  runner. Does the Phase 1f ADR capture "adopt both patterns, neither product," or declare one as primary and the other
  supplementary? _(g7-harnesses.)_
- **R2-13. Two-tier LLM config as a named convention.** TradingAgents' `deep_think_llm` / `quick_think_llm` split is a
  transferable pattern. Formalize in ARCHITECTURE.md as a named config pattern before Phase 3, or leave implicit in
  per-skill configuration? _(g10-finance.)_
- **R2-14. Biology RLVR verifier candidates (Phase 6 scope).** ether0's chemistry recipe generalizes if the oracle side
  does. Candidates: BLAST, ESMFold pLDDT, ClinVar, eQTL direction-of-effect — all sub-second per call,
  near-deterministic, no remote paid API. Dan's genomics experience is the filter for which biology tasks have
  cheap-enough verifiers to run in a tight RL loop. Shapes Phase 6 scope. _(g8-sci-agents.)_
- **R2-15. Phase 7 sandbox decision for the notebook-agent Worker.** Three options: emulated x86 Docker (slow for BLAST,
  IQ-TREE, SPAdes on M1 Max); arm64 bioinformatics image (real packaging work against bioconda pins); Linus-native
  sandbox via per-Worker conda env + sandbox-exec. The right starting point depends on which bioinformatics tools Dan
  actually needs in the analysis loop. _(g8-sci-agents.)_
- **R2-16. Bio-Task Bench Intermediate plateau interpretation (action item).** Both bioSkills agents land at 0.96–0.97
  on Intermediate with or without skills loaded. Three explanations are consistent with the data; the one Dan finds most
  credible changes how aggressively to invest in skills as an autonomy-graduation mechanism. Worth a 30-minute look at
  five representative Intermediate tasks. _(g9-bio.)_
- **R2-17. Bacformer vs Dan's existing operon-calling pipelines.** A 300M protein-context-aware encoder placed relative
  to Dan's 13 years of genomics tooling: replacement, ensemble member, or "interesting embedding signal to graft onto
  existing scoring"? Determines whether Bacformer is a Phase 7 skill surfacing results to Dan, or a Phase 7 capability
  feeding upstream of Dan's analyses. _(g9-bio.)_
- **R2-18. ProtHGT vs Horizyn-1 vs BioReason-Pro for the first protein-function skill.** Three architectures
  (KG-grounded reasoning; cross-modal retrieval; chain-of-thought reasoning over a frozen encoder). Phase 7 first- skill
  choice; criteria depend on Dan's typical protein-function questions and whether KG vs free-text reasoning fits domain
  workflows better. _(function-annotation-discovery.)_
- **R2-19. FutureHouse evaluation philosophy adopt wholesale.** The insufficient-info option, the human-pairwise
  - LLM-judge + structural-grounding stack, the canary-protected MCQ approach. Strong methodological prior art for
    Linus's `benchmarks/dan_tasks/biology/`. Adopt the philosophy or pick à la carte? _(function-annotation-
    discovery.)_
- **R2-20. Generalist × specialist FM combinations sequencing for Phase 7.** ROADMAP.md commits the first three pairs
  (Trias+GenNA, REBEAN+DeepSeMS, Bacformer+DeepSeMS); biology-phase7-roadmap.md captures the deferred Phase 8 pairs.
  Question: which pair gets resourced first within Phase 7, and what failure mode would cause a re-sequence?
  _(generative-biology + biological-foundation-models.)_
- **R2-21. Wh per task as a benchmark column or a separate energy ledger.** The Google note's per-prompt energy framing
  argues energy belongs alongside throughput as a first-class metric. Phase 1c+ benchmark methodology decision.
  _(infra-foundations.)_
- **R2-22. Implement the write-back rule across parallel Workers.** The write-back rule (every task produces a
  deliverable + KB update proposals) is operationally clear for serial work, less so for parallel Workers writing to
  overlapping pages. DEC-0022 resolved KB-write coordination at the policy level; the question now is the implementation
  pattern (lease, optimistic-merge, branch-per-Worker). _(llm-wiki.)_
- **R2-23. Immutable atomic notes vs mutable wiki pages.** The community is split. Immutable atomic Zettelkasten notes
  are append-only, link-rich, content-hashable; mutable wiki pages compound knowledge but invite drift. Phase 2/3 KB
  substrate-level architecture choice. _(llm-wiki.)_
- **R2-24. EPISTEMIC-STANDARDS.md as Phase 2a deliverable.** Marelli operationalized at the doc level: define the claim
  categories Linus distinguishes (`[!source]`, `[!analysis]`, `[!unverified]`, `[!gap]` per DEC-0023) and the
  evidentiary standards for each. Currently deferred in `planning-update-spec.md`; needs KB schema (DEC-0048) and claim
  types (DEC-0023) live before the doc is operational. _(llms-in-science; S22 originally.)_
- **R2-25. E3 dynamic tool activation timing.** OpenBB's `openbb-mcp` per-session tool activation pattern keeps
  tool-budget cost bounded for small local Workers. Adopt as Phase 2 default, or defer to Phase 3 when the actual tool
  surface is large enough to need it? _(entrepreneurship E3.)_
- **R2-26. E10 open-source-by-default architecture audit.** With E1 codified (open-source-by-default release posture),
  the architecture inherits constraints: license-compatible deps only, contributor-friendly module boundaries, no
  proprietary internal APIs that would need stripping for release. Short audit pass when Phase 2 is actively underway to
  surface anything that silently assumed proprietary deployment. _(entrepreneurship E10.)_
- **R2-27. Q-Maestro: Linus-as-Maestro quality threshold and Phase target (carried forward).** Dan confirmed 2026-05-06
  the long-term goal is for Linus to operate fully offline as Maestro. VISION.md captures the Phase 8b north star. Open
  sub-questions: (a) precise Maestro-class eval threshold that triggers Phase 8b planning (current proposal: within 10
  pp of hosted Claude); (b) does this change any Phase 2–7 architectural constraints, or is it purely a quality target;
  (c) how does the Maestro-class eval suite serve double duty as Worker-selection instrument and Linus-Maestro readiness
  indicator? _(VISION.md; ROADMAP.md Phase 8b.)_

### Tier 3 — documentation, conventions, longer-horizon scope

A reservoir for Phase 4+ planning, longer-horizon research, conventions worth codifying eventually, and action items
that depend on Dan's domain-specific reading. Dip in when context suggests an item matters now. Items grouped by source
synthesis for quick scanning.

**Memory and KB substrate (g4, llm-wiki).** R2-28 cross-vendor enforcer for memory (g4); R2-29 confidence decay rate for
claim types (llm-wiki); R2-30 FUNGI processing protocol as KB ingest step (llm-wiki); R2-31 entity deduplication
threshold (llm-wiki); R2-32 mostly-correct-is-broken handling for high-stakes content (llm-wiki).

**KB tooling (g5, g6).** R2-33 paper-corpus edge weights for blast radius (g5); R2-34 AGPL re-implementation policy as
DECISIONS.md entry (g5); R2-35 InfraNodus self-hosting as Phase 3 stretch (g5); R2-36 ontomics benchmarking scope on
KnowledgeBase corpus (g6); R2-37 vectorless bake-off model selection — hosted vs local (g6); R2-38 WeKnora per-KB
indexing toggle for Phase 2 design (g6).

**Harnesses and orchestration (g7, g11).** R2-39 origin as Phase 2b memory sidecar candidate (g7); R2-40 OTel local
storage vs Laminar deployment timing (g11).

**Bio benchmarks and tools (g8, g9).** R2-41 ProtocolQA as personal calibration test (g8 — 1-hour read); R2-42 BioReason
benchmark legitimacy (g9 — 30-min curation read); R2-43 deepsems cryptic-BGC reproducibility (g9 — paper read).

**Finance / commercial surface (g10, entrepreneurship).** R2-44 financial-intelligence as Phase 7 priority or "nice
eventually" (g10); R2-45 AGPL stance before Phase 8 (g10); R2-46 Nixtlaverse as Phase 7 forecasting skill (g10); R2-47
financial-execution safety boundary in SAFETY.md (g10); R2-48 first monetizable capability and when
(skills-and-practices); R2-49 Maestro-only to Maestro+Worker transition handling in practice (skills-and- practices);
R2-50 E4 adversarial debate as Worker primitive (entrepreneurship, was S55); R2-51 E5 two-tier compaction lift
(entrepreneurship); R2-52 E7 when does the entrepreneurial-gunpowder claim become testable (entrepreneurship); R2-53 E8
Botryonyx/CaribAlgae as background-only (entrepreneurship); R2-54 E9 pricing-anchor honesty at exploration time
(entrepreneurship).

**Biology FM strategy (biological-foundation-models, function-annotation-discovery, generative-biology).** R2-55
Generalist vs specialist Worker default for Phase 7 (biological-foundation-models); R2-56 METL pattern apply now or wait
for second instance (biological-foundation-models); R2-57 Evo 2 + Wave 3 generative-phages mini- synthesis
(biological-foundation-models); R2-58 swap BioReason-Pro encoder to LucaOne or ProteinReasoner
(function-annotation-discovery); R2-59 Linus default mode for function prediction (function-annotation-discovery); R2-60
open-answer vs MCQ as methodology principle (function-annotation-discovery); R2-61 FKC steering as generic Linus
inference-time pattern (generative-biology).

**Activation / safety research (safety-alignment-privacy).** R2-62 supervised activation steering as cheaper alternative
to LoRA fine-tuning (Phase 6+); R2-63 activation steering on BitNet ternary weights (research question); R2-64 dataset
source for Linus's first concept vectors (Phase 6+); R2-65 mirroring/sycophancy detection on Maestro outputs (Phase 7+).

**Foundation watching (infra-foundations).** R2-66 when does Linus need diffusion-model internals vs. treat as black
boxes (watch-the-field); R2-67 is local actually greener than hosted when boundary drawn comprehensively (research
framing); R2-68 KB index bottleneck at corpus size (empirical; revisit at 100–200 papers indexed).

**LLM Wiki research (llm-wiki).** R2-69 flash-mode inference + activation pruning interaction (open research, revisits
at Phase 6).

**Dan-personal reflection (llms-in-science).** R2-70 which of the four Binz perspectives most resonates for Dan and is
that reflected in current docs (Dan-time question; not action-blocking).

---

## Round 3 sweep promotions (added 2026-05-08)

A 2026-05-08 synthesis-refinement pass dispatched 25 Sonnet 4.6 sub-agents (one per synthesis) to flow paper- and
repo-note cleanup deltas up into the synthesis layer. Each agent surfaced 2–4 candidate questions per synthesis; ~70
candidates total, deduped and curated to the 27 items below. Numbering uses the `R3-NN` prefix to mark this as the third
sweep round.

### Tier 1 — block Phase 1 / Phase 2a architecture

These eight items each block a Phase 1 spike, a Phase 2a deliverable, or an ADR amendment. Walk first.

- **R3-01. Has the supply chain architecture actually been executed?** DEC-0024 resolved 2026-05-03 (architecture
  decided: hash-pinned lock file + monthly pip-audit + uv envs for experimental packages), but no lock file has been
  generated and the first pip-audit pass has not run. The synthesis flags this as overdue. Concrete next action: a
  30-minute lock-file generation + pip-audit drill run before any further Phase 2 service dependencies are added.
  _(security; no cluster anchor — pre-condition for everything else.)_
- **R3-02. agentmemory hook taxonomy as the Phase 2a episodic-memory lifecycle spec.** The 13-hook taxonomy
  (`SessionStart` through `TaskCompleted`) is the most complete worked answer to "which Claude Code lifecycle events
  does Layer C subscribe to?" in the entire corpus. DEC-0029 specifies the record shape but leaves hook-to-write mapping
  to the implementer. Concrete action: port the 13 hooks into a Phase 2a episodic-memory ADR (per-hook `segment` /
  `trust_level` / `role` write contract) before implementation begins. _(g4-memory.)_
- **R3-03. Linus skill format spec — adopt SKILL.md or write a Linus-native variant.** Three independent threads
  converge on progressive-disclosure YAML frontmatter + lazy-load markdown (g11 superpowers/gptme/Agent-Skills, g9-bio
  bioSkills/scientific-agent-skills, the agentskills.io spec). Question: Phase 2a `src/linus/skills/` adopts SKILL.md
  verbatim (skills become installable in Claude Code, Cursor, etc. without reformatting), adopts a Linus-native variant,
  or writes a mapping layer. The answer changes whether the inaugural Phase 7 skills bundle (~573 from bioSkills +
  scientific-agent-skills, S30) is portable. _(g11; cross-cuts skills-and-practices, g9-bio, entrepreneurship.)_
- **R3-04. Phase 1c spike model list reconciliation between g1-apple-silicon and native-low-bit syntheses.** The two
  syntheses give slightly different model lists for the Phase 1c benchmark sweep (g1 includes `llama3-8b-1.58` via
  Ollama as a 1-bit baseline; native-low-bit's four-way comparison does not). Running the spike from two reading angles
  produces different test matrices. Reconcile in `docs/specs/phase1c-spike.md` first. _(native-low-bit-apple-silicon;
  cluster anchor: g1-apple-silicon.)_
- **R3-05. AlphaGenome local-deployability spike (overdue Phase 1).** The biological-foundation-models synthesis
  recommends a one-day spike (clone, inspect model size, attempt one local inference on a 1 Mb interval) before
  committing the variant-scoring skill. Not yet done. The answer determines whether AlphaGenome is a local Worker or
  must use the non-commercial API path (DEC-0046's `external_api` registry field already reserves the latter), with
  direct entrepreneurial implications. _(biological-foundation-models; cluster anchor: g9-bio.)_
- **R3-06. DEC-0047 amendment: DeepSeMS BGC→SMILES is Tier B for novel-BGC generation, not Tier A.** DEC-0047 classifies
  DeepSeMS as Tier A (residue-level, no pre-authorization), but the synthesis correctly puts BGC→SMILES calls under Tier
  B when generating from novel/cryptic BGCs. Tier A is appropriate as a lookup against known MIBiG; Tier B is
  appropriate for de-novo metabolite proposals. The ADR should be amended with a conditional assignment before any Phase
  7 DeepSeMS skill ships. _(generative-biology; cluster anchor: g9-bio.)_
- **R3-07. Worktree fan-out vs sequential dispatch as Phase 3 default.** The CLAUDE.md "Worktree fan-out discipline"
  convention now documents both patterns. When the Phase 3 multi-agent fan-out is designed, an explicit decision is
  needed: does `src/linus/orchestration/workspace.py` need per-task worktree management, or is sequential dispatch with
  file-level partitioning sufficient for parallel-Worker workflows? Shapes the spawner spec. _(g7-harnesses.)_
- **R3-08. Benchmarking ADR codifying the open-answer-headline + coverage/accuracy/precision-triple convention.** Three
  independent papers (BixBench, LAB-Bench, the tokens-per-second paper 2502.16721v1) converge on "measure the
  operational thing, not the surrogate." S12 partially resolved the FutureHouse evaluation philosophy, but the specific
  convention — every `benchmarks/dan_tasks/` task ships an open-answer headline, MCQ as secondary, gap reported as
  calibration metric, coverage/accuracy/precision separated — is not yet codified. Author the ADR before Phase 1d
  task-suite authoring begins. _(function-annotation-discovery; cross-cuts infra-foundations.)_

### Tier 2 — shape Phase 2–7 architecture

Nineteen items that don't block a single concrete next action but compound into the architecture as Phase 2–7 work
proceeds.

- **R3-09. Layer A governance: preferred-architecture register in the router.** Should the router carry an explicit flag
  (e.g., for `memory_mode = session_stateful`, prefer Workers with externally addressable hidden states — SSM/hybrid
  architectures) or is opacity at Layer A the correct Phase 2 contract? Determines whether DEC-0031's router primitive
  documentation needs a "preferred Layer A architecture" field before Phase 2a or whether that's deferred to Phase 6.
  _(memory; cluster anchor: g4.)_
- **R3-10. Garrison conformance check as a Worker integration gate.** Should Linus carry an internal property test
  ("Worker must preserve KV-cache across consecutive calls; must not truncate reasoning tokens; must return scratchpad
  as separately addressable records") that any Worker integration must pass to be eligible for
  `memory_mode != stateless` dispatch? Without this, each new Worker integration requires ad-hoc judgment. _(memory.)_
- **R3-11. omega-memory typed event taxonomy as episodic store seed.** OMEGA's `_TYPE_WEIGHTS` and `DEDUP_THRESHOLDS`
  enumerate ~30 event types with per-type weights (0.05 file*summary → 3.0 constraint/reminder) and per-type Jaccard
  dedup thresholds. Decision before the first DEC-0029 migration: seed with OMEGA-style typed taxonomy from day one
  (adds a `type_weight` column + lookup table) or stay schema-flat and add types empirically. *(g4-memory.)\_
- **R3-12. Model weight integrity verification status.** SHA-256 verification of model weight files before any model
  runs in Linus is in Section 6 of the security synthesis but no implementation target is recorded. Ollama and mlx-lm
  downloads have already happened. 10-minute check: are checksums available for every model in `~/.ollama/models/`?
  _(security; cluster anchor: g1-apple-silicon.)_
- **R3-13. Keppi `build_context_pack` as Phase 3 retrieval entry point.** Keppi's greedy-fill
  `keyword_search → blast_radius → degree-centrality re-rank` is the most complete graph-aware retrieval pipeline in the
  surveyed repos (~100 lines NetworkX, no Apple Silicon dependency). Phase 3 default, or does paper-corpus retrieval
  invert the order (citation-graph expansion first, semantic re-rank second)? Shapes Phase 3 KB tooling layer API.
  _(llm-wiki; cluster anchor: g5-graph-tools.)_
- **R3-14. Prompt-variant templates per Worker model class.** Cline's `xs`/`hermes`/`glm` variants provide empirical
  evidence that tool-use prompt templates must be per-model-family for reliable local-model operation. Phase 7 skills
  ADR commits to this pattern (variant templates per Qwen, Mistral, future Linus fine-tunes) or treats it as optional
  from the skills library's first version. _(skills-and-practices; cluster anchor: g11.)_
- **R3-15. MLA vs GQA for Phase 6 KV-cache on M1 Max.** Raschka's note establishes Multi-Head Latent Attention (DeepSeek
  V2/V3) as outperforming Grouped-Query Attention on downstream tasks while compressing KV-cache via low-rank latent
  rather than head-grouping. Question: does MLX or any downstream Ollama backend support MLA's reconstruction matmul
  efficiently on Apple Silicon's unified memory, and is the quality gain over GQA measurable at 7–14B scale? Determines
  Phase 6 base-model selection and whether context-window extension uses YaRN alone or MLA + YaRN. _(infra-foundations;
  cluster anchor: g1-apple-silicon.)_
- **R3-16. ProteinReasoner vs BioReason-Pro: which architectural pole for biological reasoning Workers?**
  ProteinReasoner (typed-profile intermediate within a single PLM) and BioReason-Pro (typed companion + free-text CoT
  across a multi-model pipeline) bracket the "make-a-biological-FM-reason" design space. Phase 7 protein-annotation
  skill choice depends on M1 Max inference cost, output shape (structured profile vs free-text trace), and which Linus's
  orchestration layer audits most cleanly. Concrete action: run both on five Dan-selected proteins, score with the
  BioReason-Pro four-tier eval, report deltas. _(function-annotation-discovery; cluster anchor: g9-bio.)_
- **R3-17. Hazard-curation posture as a tool-registry ADR (`hazard_curation_status`).** DEC-0047 codifies the
  biosecurity tier framework but does not require substrate FMs to document training-data hazard-curation posture as a
  registry property. The synthesis flags this as a watch-and-enforce principle without an ADR; when the first Phase 7
  biology tool is onboarded (Trias or GenNA), pressure to skip this check will appear. Cheap to codify now, expensive to
  retrofit. _(generative-biology; cluster anchor: g9-bio.)_
- **R3-18. Procedural memory layer placement.** The Fundamentals survey's "procedures" content type (AWM-style induced
  workflows) has no clean home in the five-layer pillar: it sits between Layer C (raw episodic) and Layer E (generalized
  semantic). DEC-0052 explicitly does not cover it. Decide: assign to Layer C with a `generalized: bool` flag, assign to
  Layer E with a `procedural` type tag, or name a sub-layer. Affects what Phase 3 fan-out agents are allowed to learn
  and write back between runs. _(agentic-systems; cluster anchor: g4-memory.)_
- **R3-19. Hosted-model fallback budget policy as a concrete ADR.** DEC-0050 names `critic_eligible: bool` in the Role
  schema but does not define the budget policy (which Roles, what cap on critic-tier hosted-model calls per session).
  This is the operational handle that resolves "do we ever call hosted Claude?" into something the orchestration layer
  can enforce. _(agentic-systems; cluster anchor: g7-harnesses.)_
- **R3-20. Stylometric-leakage SAFETY.md section: when does it land?** DEC-0047 (biological dual-use) and DEC-0053 (KB
  flow) landed in PR #16. The stylometric/identity-leakage tiering — per-request audit log fields (`destination`,
  `content-class`, `bytes-sent`) and a redact-before-paste CLI — is scoped Phase 2a but has no ADR, no spec entry, no
  PR. Without a delivery target it risks indefinite deferral. _(safety-alignment-privacy.)_
- **R3-21. `value_frame` as a mandatory task-spec field — design now or defer.** The Values paper argues every Linus
  task implicitly summons a value frame from the hosted Maestro; the synthesis recommends a mandatory `value_frame`
  field in the orchestration task-spec template. CLAUDE.md mentions it but no ADR or Phase 2a delivery target exists.
  Commit the schema in Phase 2a or explicitly park as Tier 3. _(safety-alignment-privacy.)_
- **R3-22. Bonsai Ternary 8B domain-task quality gap measurement (pre-Phase-1c).** The 75.5 published benchmark average
  (95% of FP16 Qwen3-8B) is on general benchmarks; Dan's genomics and metagenomics questions may show a different gap. A
  10-task informal pre-Phase-1c run gives an early signal on whether the ternary checkpoint is Worker-viable before the
  formal sweep. Determines whether Phase 1c resources go to confirmation or discovery. _(g1-apple-silicon.)_
- **R3-23. paper-qa "adopt + extend" interaction with G2 lift candidates.** g8 established paper-qa as the first
  paper-corpus Integrate (DEC-0044). G2 identified wikiloom's chunk-id derivation, TheKnowledge's citation validator,
  and llmbase's operations registry as high-priority lift candidates for Phase 2 KB. Do those lifts go on top of
  paper-qa's ingest pipeline, in parallel to it, or are they superseded by paper-qa's own provenance mechanisms? Needs
  decision before Phase 2 KB code is written. _(g2-wiki-engines; cross-cuts g8-sci-agents.)_
- **R3-24. dlt corpus-analytics store selection (DuckDB vs PostgreSQL vs SQLite).** DEC-0029 settled the
  episodic/session store on SQLite, but the Phase 2b dlt ingestion destination for bulk corpus data (paper metadata,
  full-text chunks) is unresolved. Determines whether the dlt integration is a one-line `dlt[duckdb]` install or a
  `psycopg2`-backed pipeline. _(g5-graph-tools.)_
- **R3-25. Origin macOS Tahoe compatibility verification before Phase 2b.** The repo-note documents `ggml_metal_init`
  failures and `CXXFLAGS="-std=c++17"` requirements on Tahoe 26.x. If Dan is on Tahoe at Phase 2b, the origin bake-off
  (R2-39) could fail on Tahoe-specific issues rather than architectural ones. `sw_vers` check + `cargo build` smoke test
  should be the first step of the R2-39 evaluation. _(g7-harnesses.)_
- **R3-26. DSPy + pydantic-ai composition viability (Phase 6 pre-spike).** A pydantic-ai Agent calling
  `dspy.ChainOfThought` modules internally is "architecturally sound and worth prototyping in a Phase 6 experiment
  before committing." Determines whether Phase 6 scope includes both LoRA fine-tuning and DSPy optimization tracks or
  only one. Concrete action: define one DSPy Signature for a Linus tool contract (e.g., paper-retrieval → structured
  summary) and verify it composes with `pydantic-ai Agent.run`. _(g11-agent-frameworks.)_
- **R3-27. Audit-log specification against Marelli requirements.** The synthesis names the audit log as the central
  Marelli-compliance deliverable but the only current concrete spec is a single CLAUDE.md line. Question: should the
  audit log be redesigned as a per-output record of model + prompt + retrieved context + claimed-vs-retrieved citations?
  Concrete action: open `docs/specs/audit-log-spec.md` as a Phase 2a deliverable alongside memory-architecture spec.
  _(llms-in-science.)_

### Tier 3 — reservoir

Lower-priority items surfaced by the synthesis-refinement pass. Dip in when context suggests a thread matters now.

- R3-28. Multi-needle as an episodic-store benchmark proxy (memory).
- R3-29. minGRU session-memory encoder viability >4096 tokens (memory).
- R3-30. Vendor vs rewrite for short MIT-licensed utilities — codify as CLAUDE.md/DECISIONS.md convention (g3).
- R3-31. Reject-and-explain loop as generic Phase 7 Skill primitive (g3, via obsidian-llm-wiki-local).
- R3-32. EventEmitter trait as Linus audit-log surface pattern (g7, via origin's `Arc<dyn EventEmitter>`).
- R3-33. Procedure page type — Phase 2 KB v1 or wait for SOP corpus (g3, KB schema design).
- R3-34. Self-driving-lab parallel: quarterly Nature/Science scouting cadence (llms-in-science).
- R3-35. PertFormer 1-day PyTorch+MPS smoke test as Phase 1b spike (function-annotation-discovery).
- R3-36. KB figure index as Phase 3 work item — CLIP-shortlist + multimodal-rank from WikiAutoGen (agentic-systems).
- R3-37. JPmHC Cayley-parametrization MLX layer feasibility (native-low-bit; Phase 8 research).
- R3-38. Bacformer 26M LoRA fine-tune on Dan's genome collection — Phase 6 candidate (g9-bio).

---

## Round 4 sweep promotions — RESOLVED (2026-05-16)

The 2026-05-10 PR 30 fold-in pass (4 paper-notes + 8 repo-notes) surfaced three new live threads that didn't fit
existing R2 / R3 items. Numbering used the `R4-NN` prefix. All three resolved 2026-05-16 via DEC-0056, DEC-0057, and
DEC-0058 (see [`answered-questions.md`](answered-questions.md#round-4-sweep-resolved-2026-05-16)).

- **R4-01. Anthropic-compatible HTTP surface (DEC-0005 amendment).** Resolved by
  [DEC-0056](../adr/0056-orchestration-speaks-openai-and-anthropic-compat.md): Phase 2a's orchestration layer exposes
  both an OpenAI-compatible and an Anthropic Messages-compatible surface, sharing the underlying routing, sandbox, and
  audit-log machinery. The three confirming signals (Letta + Kimi-K2 + Goose) were sufficient.
- **R4-02. AGPL-fork posture as a DECISIONS.md entry.** Resolved by [DEC-0057](../adr/0057-agpl-fork-posture.md):
  three-tier policy (Quarantined / Reviewed / Forbidden) for AGPL reference repos. Project-license-of-Linus question
  (R2-45) stays open and acts as the escape hatch for the Forbidden tier.
- **R4-03. `@x402/mcp` graduation from Watch to Spike or Integrate.** Resolved by
  [DEC-0058](../adr/0058-x402-mcp-graduation-pathway.md): three-step pathway (Watch → Spike → Integrate) with concrete
  triggers for each transition. Spike is pre-specified as a one-week deliverable; Integrate ADR scope is pre-specified;
  negative-graduation paths (Dismiss, Re-evaluate) documented so Watch cannot drift into indefinite deferral.

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
