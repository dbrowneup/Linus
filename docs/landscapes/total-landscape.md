# Total Landscape

## What this document is

The master integration map across the four kinds of input Linus has accumulated:

- **118 paper notes** in [`docs/paper-notes/`](../paper-notes/) — flat lookup in
  [`docs/paper-notes/INDEX.md`](../paper-notes/INDEX.md).
- **117 repo notes** in [`docs/repo-notes/`](../repo-notes/) — flat lookup in
  [`docs/repo-notes/INDEX.md`](../repo-notes/INDEX.md).
- **15 thematic syntheses** in [`docs/syntheses/`](../syntheses/) — security, llm-wiki, skills-and-practices, memory,
  humans-teams-performance, generative-biology, infra-foundations, native-low-bit-apple-silicon, llms-in-science,
  function-annotation-discovery, agentic-systems, safety-alignment-privacy, biological-foundation-models,
  entrepreneurship (added 2026-05-05), llm-hardware-design (added 2026-05-09).
- **12 repo-cluster syntheses** in [`docs/syntheses/repo-clusters/`](../syntheses/repo-clusters/) — `g1`–`g12`; `g11`
  (agent frameworks, skills, and evaluation) added 2026-05-05; `g12` (llm-hardware-design, anchored on the QiMeng
  family) added 2026-05-09.

This document does not enumerate the underlying notes (the indexes do that) and does not retell the syntheses (those
documents do that themselves). It crosses _the syntheses_ — pointing out where independent threads converge, where they
remain in tension, and where the gaps between them are the work Linus actually has to do. It is the companion to
[`top-questions.md`](../questions/top-questions.md): this file is the map; the question file is the working agenda.

The previous landscape architecture had four documents (`paper-landscape`, `repo-landscape`, `synthesis-landscape`,
`total-landscape`) each crossing a different slice. After the post-fan-out integration pass that ratio inverted — the
syntheses became the primary unit of analysis and the older landscapes were duplicating content. The current
architecture is:

- **Indexes** for navigation (papers, repo-notes).
- **`synthesis-landscape.md`** for cross-synthesis structure (where 27 syntheses agree, disagree, and what's the
  meta-shape across them).
- **`total-landscape.md`** (this file) for the master integration — synthesis × architecture × roadmap × open questions,
  in one place.
- **`paper-landscape.md`** and **`repo-landscape.md`** are deprecated stubs that point to the indexes and syntheses;
  they're kept to preserve link integrity.

Read this once before working through Tier 1; refer back as decisions land.

_Refreshed 2026-05-08 after the synthesis-refinement pass (Sonnet 4.6 fan-out across all 25 syntheses): paper- and
repo-note cleanup deltas flowed up; DEC-0044 through DEC-0054 status propagated across the matrix; the R3 question batch
was harvested from the agent reports and lives in [`top-questions.md`](../questions/top-questions.md). Refreshed
2026-05-09 to add the 15th thematic synthesis `llm-hardware-design` and the 12th cluster `g12-llm-hardware-design`
(QiMeng family + Sketch2Simulation cross-thread reference). Refreshed 2026-05-10 after PR 30 fold-ins: 4 paper-notes
(Trading-R1, Geometry-Preserving NA, Lipman Flow Matching, Letta/MemGPT) and 8 repo-notes (Letta, rig, autogen,
langgraph, x402, goose, debate-or-vote, MiroFish-Offline) added; counts brought to 118/117/27 (15+12)._

---

## How the syntheses align

The 27 syntheses (15 thematic + 12 repo-cluster) cover overlapping but distinguishable territory. The matrix below
crosses each thematic synthesis against the architectural layers it informs and the closest cluster synthesis it shares
territory with. Cells with `—` are deliberate: not every theme touches every layer.

The 2026-05-05 remapping closed all unmapped repo-cluster anchors (g5, g8, g10) and added a 14th synthesis
(entrepreneurship) anchored on g10-finance. BixBench and LAB-Bench moved from agentic-systems to infra-foundations as
benchmark anchors, with a one-line cross-link kept in agentic-systems for their agent-loop aspect. A new g11 cluster
(agent frameworks, skills, and evaluation) was added 2026-05-05 as the primary anchor for skills-and-practices, covering
pydantic-ai, dspy, superpowers, Agent-Skills-for-Context-Engineering, gptme, huginn, lmnr, and promptfoo. The matrix now
allows many-to-many mapping: each thematic synthesis has a primary cluster anchor plus secondary clusters that sharpen
specific claims. The cross-edges expose load-bearing hubs (g4, g7, g8, g9) that touch multiple syntheses.

| Thematic synthesis                           | Architectural layers it informs                                                                                                                                                                      | Primary cluster anchor                                                                | Secondary clusters                                                                                                                                                                                                                                          | Tier-1-equivalent action                                                                                                                                                                                                                          |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **memory**                                   | Orchestration (router, session store, audit log); KB                                                                                                                                                 | g4-memory                                                                             | g2-wiki-engines, g3-wiki-patterns, g5-graph-tools                                                                                                                                                                                                           | Phase 2 first-class memory pillar; v0 episodic store; `cot_budget` + `memory_mode` router primitives. **Resolved in M1–M17 (DEC-0028…0043).**                                                                                                     |
| **security**                                 | Orchestration (sandbox, endpoint, deps); KB ingest                                                                                                                                                   | g6-mcp-tools (indirectly, via fastmcp)                                                | g7-harnesses, g5-graph-tools, g1-apple-silicon, g4-memory, g2-wiki-engines                                                                                                                                                                                  | pip-audit + hash lock file + remove pre-emptive deps + incident protocol. **Resolved in 2026-05-03 Tier 0.** Security touches every core component Linus is building.                                                                             |
| **llm-wiki**                                 | KB substrate; orchestration (write-back, hot cache)                                                                                                                                                  | g2-wiki-engines, g3-wiki-patterns                                                     | g8-sci-agents (paper-qa adopt+extend), g4-memory (substrate shape)                                                                                                                                                                                          | Compile-not-retrieve; schema-as-product; claim typing + content hashing + write-back as Phase 2 KB deliverables.                                                                                                                                  |
| **skills-and-practices**                     | Maestro/Worker discipline                                                                                                                                                                            | g11-agent-frameworks (pydantic-ai, dspy, superpowers, gptme, huginn, lmnr, promptfoo) | g7-harnesses (Task Master AI, claude-squad), g9-bioinformatics (bioSkills), g8-sci-agents (scientific-agent-skills, paper-qa), g10-finance (transferable patterns)                                                                                          | Hot-cache convention; Worker-spec uncertainty protocol; promptfoo baseline + pydantic-ai smoke test as Phase 2a open. (Entrepreneurship content extracted to its own synthesis 2026-05-05; g10 also cross-linked from there.)                     |
| **agentic-systems**                          | Phase 3 spawner; multi-agent protocol                                                                                                                                                                | g7-harnesses (workgraph as runtime)                                                   | g6-mcp-tools (fastmcp), g4-memory (investigation memory + agentmemory primitives), g5-graph-tools (KB tool primitives), g8-sci-agents (multi-role evidence base)                                                                                            | Role + typed `AgentReport` + investigation-memory layer ADR before spawner ships. (BixBench/LAB-Bench moved to infra-foundations 2026-05-05; cross-link retained for agent-loop aspect.)                                                          |
| **infra-foundations**                        | Foundational reference; benchmarks (energy ledger, agent harnesses); KB tooling                                                                                                                      | g5-graph-tools                                                                        | g7-harnesses (workgraph + autoresearch-mlx as methodology substrate), g1-apple-silicon (autoresearch-mlx, Wh-per-task), g2-wiki-engines (foundational substrate prior art), g3-wiki-patterns (build-pattern prior art for benchmark + KB-tooling workflows) | Wh-per-task as benchmark or ledger column; "world model" terminology hygiene before Phase 3; LAB-Bench MCQ + BixBench as Phase 1 baseline (moved here 2026-05-05); hyalo + keppi as Phase 3 KB tooling layer.                                     |
| **native-low-bit-apple-silicon**             | Inference + training (Phase 1b/1c/6)                                                                                                                                                                 | g1-apple-silicon                                                                      | g6-mcp-tools (pmetal-mcp as inference-layer MCP surface)                                                                                                                                                                                                    | Phase 1c unified four-way Worker-selection methodology (Bonsai 8B + ternary + 2B4T + FP16).                                                                                                                                                       |
| **llms-in-science**                          | VISION-level posture; benchmarks (Maestro tier); scientific-agent prior art                                                                                                                          | g8-sci-agents                                                                         | g9-bioinformatics (Bacformer, BioReason, DeepSeMS), g2-wiki-engines (reproducibility floor), g3-wiki-patterns (epistemic-standards operationalization)                                                                                                      | Maestro-class evaluation tier in `benchmarks/dan_tasks/`; VISION.md citation of Binz framework; paper-qa as Phase 2 KB substrate default integration target (g8 anchor).                                                                          |
| **function-annotation-discovery**            | Phase 7 skills (biology); KB (model-prediction edges)                                                                                                                                                | g9-bio                                                                                | g8-sci-agents (paper-qa as literature-intelligence engine)                                                                                                                                                                                                  | Pick first protein-function skill (ProtHGT vs Horizyn-1 vs BioReason-Pro). Benchmark anchors (LAB-Bench, BixBench) live in infra-foundations as of 2026-05-05; cross-reference for skill evaluation.                                              |
| **generative-biology**                       | Phase 7 skills (biology); SAFETY (whole-genome tier); tool registry (`external_api_tool`)                                                                                                            | g9-bio                                                                                | g6-mcp-tools (`external_api_tool` as MCP-shape decision)                                                                                                                                                                                                    | SAFETY.md tier-control as Phase 1 deliverable; `external_api_tool` registry class + ADR.                                                                                                                                                          |
| **biological-foundation-models**             | Phase 7 (LucaOne anchor); KB (model_prediction edges); tool registry                                                                                                                                 | g9-bio                                                                                | g4-memory (`model_prediction` edge as memory-layer schema commitment), g5-graph-tools (LucaOne-as-KG-anchor depends on g5 substrate)                                                                                                                        | KB `model_prediction` edge class with provenance before Group A skills write back.                                                                                                                                                                |
| **safety-alignment-privacy**                 | SAFETY; orchestration (activation hooks); benchmarks (values eval)                                                                                                                                   | — _(intentionally unmapped)_                                                          | —                                                                                                                                                                                                                                                           | Activation-hooks API stub Phase 1, feasibility spike Phase 2 against mlx-lm.                                                                                                                                                                      |
| **humans-teams-performance**                 | VISION-level (multidisciplinary preservation); Maestro/Worker timescales                                                                                                                             | — _(intentionally unmapped)_                                                          | —                                                                                                                                                                                                                                                           | Decide on `goal_orientation` field in Worker spec template; preserve-multidisciplinary as VISION/CLAUDE/ROADMAP entry.                                                                                                                            |
| **entrepreneurship** _(added 2026-05-05)_    | VISION-level (commercial surface); Phase 2 entrepreneurial-surface document; Phase 7 skills (biology pillar productization); orchestration (Maestro/Worker context-management transferable patterns) | g10-finance                                                                           | g9-bioinformatics (bioSkills + scientific-agent-skills as productizable surface), g8-sci-agents (paper-qa as literature-intelligence engine), g7-harnesses (claude-squad + harness primitives for multi-user/multi-agent story)                             | First-class entrepreneurial-surface document (extracted from skills-and-practices); Tier 1/2/3 questions on commercial sequencing, biotech-team literature-intelligence productization, and transferable quant-agent context-management patterns. |
| **llm-hardware-design** _(added 2026-05-09)_ | Phase 6/7/8 idea→reality skill class; orchestration (planner/coder/verifier Roles extending DEC-0050); inference (MLX kernel codegen via QiMeng patterns)                                            | g12-llm-hardware-design                                                               | g1-apple-silicon (kernel codegen + MLX hint-repo + auto-tune as Phase 6d candidate substrate), g8-sci-agents (Sketch2Simulation as cross-thread process-engineering exemplar), agentic-systems (planner/coder/verifier extends Role specialization)         | 11 ADR seeds named (`_Seed: DEC-NNNN_`); MTMC pipeline as Linus orchestration substrate; RLVR-with-automated-oracle as canonical Worker self-improvement; QiMeng-SALV as cleanest tractable Apple-Silicon reproduction target.                    |

Several observations fall out of this view:

**Memory and KB are the densest convergence points.** The memory synthesis maps onto the orchestration layer's
session/router primitives, the KB substrate (Layer D), and the g4-memory cluster's substrate evidence (openaugi as
closest existing match to DEC-0029 v0; agentmemory as parallel-write coordination prior art). The llm-wiki synthesis
touches almost the same surface from a different angle (compile-not-retrieve, claim typing, write-back as operational
discipline). The agentic-systems synthesis adds a fifth layer (investigation memory) that the four-layer pillar doesn't
yet name. These three theses point at one substrate; building it well in Phase 2 satisfies all three.

**Biology is overdetermined now.** Three thematic syntheses (function-annotation-discovery,
biological-foundation-models, generative-biology) plus the g9-bio cluster overlap heavily. The integrate-verdict trio
(paper-qa, bioSkills, scientific-agent-skills) plus the Phase 7 entrepreneurial stack (paper-qa + bioSkills +
Bacformer + LAB-Bench + KnowledgeBase) gives the biology pillar enough mass that it deserves an explicit Phase 7
sub-roadmap rather than scattered skill commitments.

**Safety has two complementary syntheses.** `security-synthesis.md` (supply chain + dep + endpoint) and
`safety-alignment-privacy-synthesis.md` (activation observability + values + dual-use uplift + privacy) are
non-overlapping. Together they cover the full safety surface; SAFETY.md needs additions from both sides.

**Agentic-systems and skills-and-practices are converging.** The skills synthesis treats orchestration mostly as a
build-vs-adopt question (Task Master AI, claude-squad); the agentic-systems synthesis goes deeper into the type system
(Role, AgentReport, validation gates, critic tier). Phase 3 spawner design is where they meet — and the g7-harnesses
cluster's workgraph finding is the most directly liftable runtime.

**Two thematic syntheses are intentionally repo-unmapped.** safety-alignment-privacy and humans-teams-performance remain
theory-and-practice threads with no corresponding code cluster — and that's a property of the topic, not a gap. They
feed VISION/SAFETY/benchmark-design, not a tool integration. The 2026-05-05 remapping pulled infra-foundations (now
anchored on g5-graph-tools + LAB-Bench/BixBench as benchmark anchors) and llms-in-science (now anchored on
g8-sci-agents) out of the unmapped column, and added the entrepreneurship synthesis anchored on g10-finance, leaving
zero unmapped repo-cluster groups. The 2026-05-09 fold-in added llm-hardware-design anchored on g12 (QiMeng family),
keeping the 1:1+ mapping intact at 15 thematic / 12 cluster.

---

## The crossings

The following are the substantive cross-synthesis bets — places where multiple syntheses agree on what's load-bearing
for Linus's near-term architecture. Each crossing is one of the central decisions Linus has resolved or will resolve
over the next several phases.

### Crossing 1 — The BitNet → Apple Silicon → ANE bridge

The native-low-bit-apple-silicon synthesis canonicalizes the path: six BitNet papers + three Bonsai-related papers

- pmetal kernels + bitnet.cpp's Apple M2 Ultra throughput numbers. The g1-apple-silicon cluster confirms operational
  feasibility (autoresearch-mlx as the runnable methodology substrate). Three rungs are climbable: CPU + bitnet.cpp
  (operational today), GPU + pmetal kernels (Phase 1b verdict), ANE + pmetal/Maderix patterns (Phase 2 conditional
  follow-up).

**Status (2026-05-04):** Phase 1c climbs rungs 1 and 2 under a unified four-way Worker-selection methodology. Rung 3
defers to Phase 2 conditional on favorable pmetal verdict. **New sub-question (S8):** pmetal Rust kernels vs. MLX-native
PrismML fork — ADR before the inference layer hardens.

### Crossing 2 — The streaming axis: dense (mlx-flash) vs. sparse (flash-moe) vs. composite (1-bit + streamed)

Original framing: LLM in a Flash → mlx-flash (dense, framework-integrated) → flash-moe (sparse, bespoke) → composite
(1-bit + streamed). The native-low-bit synthesis sharpens this: Bonsai 8B fits in 1.75 GB, which trivializes the "dense
fine-tuned 8B exceeds RAM" framing of Phase 6d. The g1 synthesis confirms the OS-page-cache discipline
(application-level caches over mmap'd files _hurt_ throughput on macOS unified memory).

**Status (2026-05-04):** mlx-flash narrowed to "fine-tuned models that genuinely exceed RAM" (Linus-branded 30B+ or
opportunistic ternary 30B+ from PrismML). flash-moe stays methodology-only reference. Phase 8 BitNet × Flash-MoE × JPmHC
stays long-horizon. **New question (S20):** rewrite Phase 6d framing to reflect the narrower target.

### Crossing 3 — KnowledgeBase as graph + vector layered substrate, now with paper-qa as substrate candidate

The Hogan KG survey + Stankevičius embeddings + Curse-of-Dimensionality form the theoretical spine; the llm-wiki
synthesis adds operational depth (claim typing, content hashing, write-back, hot cache); the g8 cluster surfaces
**paper-qa as the first paper-corpus-shaped tool to earn an Integrate verdict**. The biological-foundation-models
synthesis adds the `model_prediction` edge class requirement before Group A Wave 1 skills start writing back to KB.

**Status (2026-05-04):** Dual RDF + property graph (DEC-0015) substrate stands. **New Tier 1 question (S1):** paper-qa
as Phase 2 KB substrate default integration target — reframes Phase 2 as "adopt + extend" rather than "build from
scratch." **New Tier 1 question (S6):** `model_prediction` edge class with provenance before Group A writes back. **New
Tier 1 obligation (S2):** LAB-Bench canary blocklist before any KB ingestion runs.

### Crossing 4 — Structure as the operational bottleneck

The earlier total-landscape's Crossing 4 (the practitioner finding that the bottleneck has shifted from capability to
structure) now has formal teeth from the memory pillar's complexity-theoretic floor. The infra-foundations synthesis
adds the methodology dimension (capability-first measurement, Wh-per-task accounting). The llms-in-science synthesis
adds the epistemic dimension (claim categories, EPISTEMIC-STANDARDS.md candidate). The agentic-systems synthesis adds
the multi-agent dimension (Role types, typed messages, validation gates).

**Status (2026-05-04):** 10-bits/s framing adopted as Phase 2 design principle; balanced bullets + prose; citations and
traceability first-class; planning write-back cadence as a CLAUDE.md engineering convention. **New questions:** S22
(`docs/EPISTEMIC-STANDARDS.md`); S23 (Maestro-class evaluation tier); S57 (`docs/maestro-protocol.md`).

### Crossing 5 — Memory as the load-bearing pillar (resolved 2026-05-03; substrate evidence sharpened by g4)

The Garrison thread + Mughal practitioner article established memory as a Phase 2 first-class pillar in 16 ADRs
(DEC-0028…0043); the g4-memory cluster surfaced **openaugi as the closest existing match to the DEC-0029 v0 substrate**
(two-table SQLite + sqlite-vec + FTS5 with deterministic content-hash IDs) and **agentmemory's lease/signal/checkpoint
primitives as concrete prior art for parallel-Worker write coordination**. The agentic-systems synthesis adds a
previously-unnamed fifth layer (investigation memory: task-scoped, multi-agent, single-investigation lifetime — the
Kosmos world model, Sketch2Simulation IR, HKUST QuantAgent context buffer shape).

**Status (2026-05-04):** M1–M17 resolved. **New Tier 2 question (S13):** fifth memory layer for "investigation memory" —
touches `memory-architecture.md`, resolve before Phase 3.

### Crossing 6 — Biology as a pillar, not a scattered set of skills (new, 2026-05-04)

This crossing did not exist in the prior total-landscape because the biology corpus was a few papers in a thematic
thread, not its own pillar. The post-fan-out work added 14 paper notes (Group A foundation models + Group B generators +
Group C function annotation + a dual-encoder enzyme-discovery paper) and the g9-bio cluster surfaced the integrate trio
(Bacformer + bioSkills + paper-qa from g8). The function-annotation-discovery and biological-foundation-models and
generative-biology syntheses converge on a coherent Phase 7 biology pillar with a real entrepreneurial surface
(literature intelligence for biotech teams).

**Status (2026-05-04):** Phase 7 biology pillar emerging; entrepreneurial-surface deliverable can be filled against
concrete components. **New Tier 1 questions:** S4 (`external_api_tool` registry class), S5 (SAFETY.md whole-genome
tier-control). **New Tier 2 questions:** S18 (LucaOne as KG anchor), S19 (Evo 2 vs AlphaGenome), S29 (AlphaGenome
NC-license entrepreneurial implications), S30 (bioSkills + scientific-agent-skills inaugural Phase 7 bundle), S31
(generalist × specialist FM combinations sequencing).

### Crossing 7 — Agentic-systems theory as first-class architectural input (new, 2026-05-04)

The agentic-systems synthesis is the first thematic thread with formal theoretical content beyond the memory pillar
(HKUST QuantAgent regret bound; design intuition that KB coverage growth dominates suboptimality). The g7-harnesses
cluster surfaced workgraph as the most directly liftable orchestration runtime (CLAUDE.md adopts its JSONL DAG +
dispatch as the recommended Phase 2a session-store shape). Together they push Phase 3 spawner design from "deferred
decision" to "ADR-shaped" with concrete primitives.

**Status (2026-05-04):** **New Tier 1 questions:** S9 (Role as first-class type), S10 (typed inter-agent message format
ADR). **New Tier 2 questions:** S14 (hosted-model fallback policy reframed as critic-tier-and-budget), S15 (validation
gate primitive in spawner vs sandbox). **New Tier 3:** S55 (adversarial debate as Worker primitive), S56 (agentic-system
theory in Phase 3 spawner ADR).

### Crossing 8 — Idea → reality as a load-bearing skill class (new, 2026-05-09)

The QiMeng family fan-out (CodeV, QiMeng-MuPa, QiMeng-SALV, QiMeng-cpu-v1) plus Sketch2Simulation surfaced a new spine:
LLMs producing artifacts (Verilog, CUDA kernels, hardware schematics, build instructions) that downstream non-LLM actors
(compiler, fab, manufacturer, contractor, builder) accept and realize as physical or computational artifacts. Anchored
on the new `llm-hardware-design-synthesis.md` (15 paper-notes) plus the g12 cluster. Sketch2Simulation is a cross-thread
reference exemplar (a g8-sci-agents member, not g12), supplying the multi-agent error-recovery loop.

**Status (2026-05-09):** **11 ADR seeds named inline** (`_Seed: DEC-NNNN_`) covering MTMC pipeline as Linus
orchestration substrate, RLVR-with-automated-oracle as canonical Worker self-improvement, idea→reality as a load-bearing
Phase 7 skill class, two-tier verification (in-loop fast oracles + out-of-loop ground-truth), and biotech-tangible Phase
8 target (design real physical things from natural language). QiMeng-SALV identified as the cleanest tractable
Apple-Silicon reproduction target. Phase 6/7/8 evidence-gathering is the immediate need.

---

## The architectural layers Linus actually has to build

Independent of theme, these are the distinct engineering layers that fall out of the combined landscape. Each has its
own decision shape and dependency structure.

### Layer A — Orchestration layer (Linus proper)

The product, in `src/linus/`. OpenAI-compatible endpoint, session store, audit log, tool registry, agent spawner,
sandbox. Speaks to inference backends below it (pmetal-serve / Ollama / bitnet.cpp / mlx-flash) and to harnesses above
it (cline / claw-code-local / openclaw / Claude Code / claude-squad).

**Updated Phase 2 scope (2026-05-04, with 2026-05-10 fold-ins):**

- **MCP framework** — fastmcp adopted as default; Phase 2a tool registry built MCP-shape from the start (CLAUDE.md
  update + S3 + DEC-0026 status).
- **Session store and audit log** — workgraph-style JSONL DAG + dispatch as recommended shape (CLAUDE.md update + g7
  synthesis).
- **Memory primitives** — `cot_budget` and `memory_mode` as router primitives; episodic substrate API
  (`linus.memory.episodic.*`); scratchpad as first-class durable artifact (DEC-0030/0031/0032).
- **Tool registry** — `external_api_tool` class for non-locally-deployable tools (S4, ADR pending).
- **Activation observability** — API stub in Phase 1, feasibility spike in Phase 2 against mlx-lm/Llama-3.1-8B-4bit
  (S17).
- **PR 30 reference-stack signals (2026-05-10):** Letta (Study, MemGPT-derivative; Anthropic-compat HTTP signal), rig
  (Study, Rust + first-class Ollama provider; Phase 5+ candidate provider abstraction), autogen (Study, but in
  maintenance mode — MAF is the live successor), langgraph (Study, graph-based orchestration; reinforces workgraph JSONL
  DAG choice), goose (Study, Rust + MCP harness entrant), debate-or-vote (Study + Phase 3 spike candidate; round-0 vote
  outperforms multi-round debate finding), MiroFish-Offline (Watch; AGPL-3.0 blocks code lift), x402 (Watch;
  commercial-payments substrate, `@x402/mcp` shipped).

### Layer B — Inference / training layer

Worker models and the kernels that run them. pmetal is the top candidate by breadth; bitnet.cpp is a CPU-only fallback;
mlx-flash is the >RAM dense path; Bonsai's `llama-server` is an interim 1-bit serving path. The autoresearch loop drives
optimization of this layer.

**Updated Phase 1c shape (2026-05-04, with 2026-05-09 fold-ins):**

- Phase 1b pmetal verdict still gates inference-backend lock-in.
- Phase 1c unified four-way methodology (Bonsai 8B 1-bit + ternary + BitNet 2B4T + FP16 baseline) under one harness
  (S7).
- pmetal Rust kernels vs. MLX-native PrismML fork ADR before the inference layer hardens (S8).
- BitDistill spike timing decision (Phase 6a vs 6b vs deferred) (S21).
- **Phase 6/8 weight-streaming candidate (2026-05-09):** Kimi-K2 (1T total / 32B active) tagged as a candidate model for
  `mlx-flash` weight-streaming when fine-tuning exceeds the 32 GB unified-memory ceiling; see
  [`docs/specs/phase6d-streaming-target.md`](../specs/phase6d-streaming-target.md) and `repo-notes/Kimi-K2.md`.
- **DreamZero / EgoScale (2026-05-09):** referenced only in synthesis context for downstream skill discovery; not Phase
  1c scope.

### Layer C — KnowledgeBase / data layer

`modules/KnowledgeBase/` (submodule), plus the data-sovereignty components from Phase 4. Hogan KG survey + Stankevičius
embeddings + Curse-of-Dimensionality form the theoretical substrate. The llm-wiki synthesis adds operational discipline
(claim typing, content hashing, write-back, hot cache). The g2/g3 wiki clusters surface specific implementation prior
art (wikiloom's chunk-id formula, atomic-knowledge's get_context walker, llm-research-wiki's typed page schema,
obsidian-llm-wiki-local's 3-tier JSON fallback for Ollama Workers).

**Updated Phase 2 scope (2026-05-04):**

- **paper-qa** as candidate substrate for the paper-corpus side of KB (S1).
- **`model_prediction` edge class** with producing-model + version + confidence + content-hash provenance before Group A
  Wave 1 skills start writing back (S6).
- **LAB-Bench canary blocklist** at ingestion time before any RAG or fine-tune work (S2).
- **hyalo + keppi** as Phase 3 KB tooling layer (lint + transactional link rewrites + bounded-BFS-with-decay
  context_pack retrieval) (S26).
- **Quality gate as a quality surface, not a hard gate** — Dan is the primary filter (resolved Tier 1 #6, 2026-05-03).
- **Hybrid retrieval** (BM25 + vector + graph traversal, fused via RRF) as Phase 3 deliverable; qmd's RRF logic is
  liftable.

### Layer D — Memory pillar

Per `docs/specs/memory-architecture.md`. **Five layers (A–E)** as of DEC-0052: intra-step latent (A), within-session
scratchpad (B), cross-session episodic (C, SQLite + content hashes + git), investigation memory (D, task-scoped
multi-agent SQLite), and semantic knowledge (E, KnowledgeBase). The five-layer architecture is committed in
DEC-0028–DEC-0043 plus DEC-0052; implementation is Phase 2 (B/C/E active) and Phase 3 (D).

**Substrate prior art (added 2026-05-04):**

- **openaugi** is the closest existing match to the DEC-0029 v0 substrate; design ideas may be portable.
- **agentmemory** lease/signal/checkpoint primitives are concrete prior art for parallel-Worker write coordination.

### Layer E (new, 2026-05-04) — Skills and entrepreneurial surface

Not an architectural layer in the runtime sense; the Phase 7 capability layer. The g8/g9 fan-out + the biology synthesis
trio surfaced concrete components: bioSkills (~438 bio skills) + scientific-agent-skills (~135 broad science skills) as
the inaugural Phase 7 bundle (~573 total); paper-qa as the literature intelligence engine; Bacformer as the most
M1-Max-realistic broad bio FM; LAB-Bench as the rigorous public benchmark; **ClawBio (added 2026-05-10) as the closest
existing worked example of a Phase 7 inaugural bio-skills bundle in working form** — per-skill tests + reproducibility
bundle + conformance linter + Claude Code plugin-marketplace distribution as directly liftable engineering patterns.

**Phase 2 placeholder:** `docs/entrepreneurial-surface.md` (resolved Tier 2 #14, 2026-05-03; renamed to
`docs/knowledge-mining-surface.md` per E2 resolution 2026-05-06) becomes concrete with this stack as the first worked
example.

---

## Where the gaps are (updated 2026-05-10)

The 2026-05-03 gap list closed four of seven items (custom-orchestration vs. off-the-shelf via Phase 1f deliverable; KB
ingest quality gate via reframe; written incident response protocol; commercial surface via entrepreneurial-surface
deliverable). The remaining three plus several new ones surfaced by the post-fan-out work:

**Open from prior list:**

- **A Linus episodic-memory implementation.** v0 substrate (SQLite + content-hashes + git) is specified (DEC-0029) but
  not yet implemented. Phase 2 deliverable. **OPEN.**
- **Orchestration-surface context-management primitives.** `/context`, `/clear`, `/compact`, `/rewind` analogues
  - PreCompact-hook-style "capture critical state before lossy compression" pattern. Phase 2 deliverable. **OPEN.**
- **A unified BitNet × MoE × Streaming codebase.** Phase 8 research direction; minGRU + BitLinear gates as the
  hardware-friendly recurrent + 1-bit cross-product. **OPEN.**
- **An MLX Cayley parametrization layer.** JPmHC validated on 7M TRM at 8× B200; no MLX implementation yet. Phase 6
  architecture decision; not phase-blocking. **OPEN.**
- **An ANE serving binary that is both production-quality and officially supported.** pmetal uses private APIs. No
  public-API ANE serving path currently performs comparably. **OPEN.**

**New 2026-05-04, status updates 2026-05-10:**

- **A Phase 7 biology sub-roadmap.** **CLOSED 2026-05-07** as
  [`docs/specs/biology-phase7-roadmap.md`](../specs/biology-phase7-roadmap.md).
- **A Phase 3 spawner ADR draft.** **CLOSED 2026-05-06** via DEC-0050 (Role), DEC-0051 (AgentReport), DEC-0052
  (investigation memory Layer D); design-intent stub at [`docs/specs/phase3-spawner.md`](../specs/phase3-spawner.md).
- **An MLX ternary kernel contribution path.** native-low-bit synthesis names this as the single best-scoped external
  contribution opportunity in the corpus. Phase 1d (immediate) vs Phase 6d (deferred). **OPEN.**
- **A `docs/maestro-protocol.md` for hosted-Maestro behavioral dependencies.** **CLOSED via PR #22** — drafted at
  [`docs/protocols/maestro-protocol.md`](../protocols/maestro-protocol.md) (~18KB, 2026-05-07). S57 closure is
  scheduling for Phase 2a operationalization; the doc itself exists.
- **A modern-Transformer-reference paper bridging 2017 → 2025.** **CLOSED 2026-05-06** as Tier 3 documentation deferral
  (S38); absorbed into the infra-foundations synthesis's Transformer reference section.

**New 2026-05-10 (PR 30 fold-in implications):**

- **An Anthropic-compatible HTTP surface ADR.** Three independent signals now point at this: Letta ships both OpenAI-
  and Anthropic-compatible endpoints; Kimi-K2 deploys with both; the broader open-source agent ecosystem is converging
  on dual endpoints. DEC-0005 commits Linus to OpenAI-compat-only at v0; a Phase 5+ ADR ("Anthropic- compatible HTTP as
  a Linus capability") becomes warranted if a fourth confirming signal lands. **OPEN.**
- **A `@x402/mcp` graduation ADR (Phase 7+ / Phase 8).** x402's `@x402/mcp` shipped (TypeScript + Python + Go); the
  Canteen-blog mention upgraded from "roadmap-only" to live. Watch-only today; an ADR becomes warranted when a Linus
  commercial-surface decision forces the question (per `repo-notes/x402.md` §6). **OPEN.**
- **An AGPL-fork posture entry in DECISIONS.md.** MiroFish-Offline's Watch verdict is gated explicitly on AGPL-3.0
  contamination analysis. R2-34 (g5 AGPL re-implementation policy) is the existing tracker; PR 30's MiroFish add raises
  the urgency from "convention worth codifying eventually" to "before any Phase 3 KB-tooling lift starts." **OPEN.**
- **An autogen-as-cautionary-tale documentation point.** AutoGen is in maintenance mode (Microsoft Agent Framework is
  the live successor). PR 30's AutoGen fold-in plus the Kimi-K2 / Letta / Goose fold-ins together raise the
  reference-stack-staleness concern: any reference repo can shift to maintenance mode without notice. CLAUDE.md's
  "Reference-stack maintenance signals" engineering convention (added 2026-05-10) is the codification.

---

## How the work products fit together (updated 2026-05-10)

```
docs/
├── paper-notes/INDEX.md      (navigation: 118 paper notes → thematic syntheses)
├── repo-notes/INDEX.md       (navigation: 117 repo notes → cluster + thematic syntheses)
├── paper-notes/*.md          (118 per-paper write-ups)
├── repo-notes/*.md           (117 per-repo write-ups)
│
├── syntheses/
│   ├── *-synthesis.md        (15 thematic syntheses; entrepreneurship added 2026-05-05; llm-hardware-design 2026-05-09)
│   └── repo-clusters/*.md    (12 cluster syntheses, g1–g12; all anchored to a thematic synthesis)
│
├── landscapes/
│   ├── synthesis-landscape.md  (cross-synthesis structure: where 27 agree/disagree/overlap)
│   ├── total-landscape.md      (this file: master integration; crossings; gaps)
│   ├── paper-landscape.md      (DEPRECATED stub → INDEX + syntheses)
│   └── repo-landscape.md       (DEPRECATED stub → INDEX + syntheses)
│
└── questions/
    ├── top-questions.md      (working agenda; R2-NN / R3-NN promotions; resolved S/M/E series archived)
    ├── answered-questions.md (resolution archive with DEC links + uncovered audit)
    └── open-questions.md     (full archive; per-source records)
```

Specs and ADRs live alongside:

- [`docs/specs/memory-architecture.md`](../specs/memory-architecture.md) — Phase 2 memory pillar contract.
- [`docs/specs/planning-update-spec.md`](../specs/planning-update-spec.md) — execution log for the planning arc that
  resolved S1–S60 + E1–E12 (status: complete, all seven Worker tasks merged 2026-05-07).
- [`docs/specs/qimeng-category-promotion.md`](../specs/qimeng-category-promotion.md) — promotion of the QiMeng family
  out of g1 into the new g12 cluster + llm-hardware-design thematic synthesis (2026-05-09).
- [`docs/specs/2026-05-10-pr30-cleanup-spec.md`](../specs/2026-05-10-pr30-cleanup-spec.md) — PR 30 cleanup pass spec
  covering Tier 1–7 fold-ins plus this Tier 10 audit.
- [`docs/session-summaries/2026-05-04-fan-out-session-summary.md`](../session-summaries/2026-05-04-fan-out-session-summary.md)
  — read-out from the Section 7 fan-out.
- `docs/adr/NNNN-*.md` — per-file ADRs (DEC-0001 through DEC-0054 as of 2026-05-06; no new ADRs in PR 30).

The intended workflow is: walk `top-questions.md` Tier 1 in conversation, with `total-landscape.md` open as the map,
`synthesis-landscape.md` open for cross-synthesis context, and the relevant per-synthesis or per-note file open for
depth. Update `total-landscape.md` and the relevant planning documents (ROADMAP.md, ARCHITECTURE.md, SAFETY.md,
CLAUDE.md, the specs and ADRs) as each answer lands.
