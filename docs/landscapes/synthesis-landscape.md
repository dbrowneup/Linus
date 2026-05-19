# Synthesis Landscape

## What this document is

The cross-synthesis structural map. Linus has accumulated 27 synthesis documents — 15 thematic syntheses in
[`docs/syntheses/`](../syntheses/) and 12 repo-cluster syntheses in
[`docs/syntheses/repo-clusters/`](../syntheses/repo-clusters/). Each one is itself a cross-cut: a thematic synthesis
crosses paper-notes against an architectural or operational concern; a cluster synthesis crosses repo-notes within a
fan-out group. This document goes one level higher — it crosses the syntheses against each other.

The 2026-05-05 remapping closed all unmapped repo-cluster anchors and added a 14th thematic synthesis
(entrepreneurship). BixBench and LAB-Bench moved from agentic-systems to infra-foundations as benchmark anchors;
g5-graph-tools now anchors infra-foundations; g8-sci-agents now anchors llms-in-science; g10-finance anchors the new
entrepreneurship synthesis. A new g11 cluster (agent frameworks, skills, and evaluation — pydantic-ai, dspy,
superpowers, Agent-Skills-for-Context-Engineering, gptme, huginn, lmnr, promptfoo) was added 2026-05-05 and becomes the
primary cluster anchor for the skills-and-practices synthesis.

This is intentionally a complement to [`total-landscape.md`](total-landscape.md). The total landscape is the master
integration map (architecture × roadmap × open questions in one place); this file is the structural map across the
syntheses themselves (where they agree, tension, overlap, and what meta-shape emerges). The total landscape works
top-down (Phase 2 needs X, X is informed by syntheses A, B, C); this file works bottom-up (here are 27 syntheses, this
is what falls out when you stack them).

The previous version of this document covered four syntheses (security, llm-wiki, skills-and-practices, memory). That
ratio has expanded ~6× since the post-fan-out integration pass. Read this once before working through Tier 1 in
`top-questions.md`; refer back as decisions land. (Updated 2026-05-05 to reflect g11 + 5 thematic additions; refreshed
2026-05-08 after the synthesis-refinement pass that flowed paper- and repo-note cleanup deltas into the syntheses,
propagated DEC-0044 through DEC-0054 status across the rows, and harvested the R3 question batch. Updated 2026-05-09 to
add the 15th thematic synthesis `llm-hardware-design` and the 12th cluster `g12-llm-hardware-design` after the QiMeng /
idea→reality fan-out per `docs/specs/qimeng-category-promotion.md`. Refreshed 2026-05-10 to add ClawBio as the 5th
member of the g9-bio cluster — depth-vs-breadth complement to bioSkills and the closest existing precedent for the Phase
7 inaugural bio-skills bundle in working form. Refreshed 2026-05-10 (Tier 10 audit, PR 30) to fold 4 paper-notes
(Trading-R1, Geometry-Preserving NA, Lipman Flow Matching, Letta/MemGPT) and 8 repo-notes (Letta, rig, autogen,
langgraph, x402, goose, debate-or-vote, MiroFish-Offline) into the relevant cluster rows; correct the maestro-protocol
path mismatch in §"What's missing". Refreshed 2026-05-16 (Wave 2 landings) — memory-synthesis Layer C v0 substrate
(SQLite + content-hashing + audit log) now implemented per DEC-0029 via PR #35; agentic-systems-synthesis sees the first
Worker-throughput evidence point from the Phase 1d Dan task suite v0 baseline (PR #33); the DEC-0005 single-protocol
commitment is amended by DEC-0056 (Anthropic-compat HTTP) and the AGPL/x402-mcp gaps are closed by DEC-0057/0058 via PR
#36. ADR ceiling moves to DEC-0058.)

---

## The 27 syntheses

### Thematic syntheses (15)

| Synthesis                                                                                   | One-line characterization                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`security`](../syntheses/security-synthesis.md)                                            | Supply chain + dependency surface + endpoint security + prompt-injection threat model. Triggered by litellm.                                                                                                                                                                                                                                                                                                                                                    |
| [`llm-wiki`](../syntheses/llm-wiki-synthesis.md)                                            | LLM Wiki pattern: compile-not-retrieve, schema-as-product, claim typing, content hashing, write-back, hot cache.                                                                                                                                                                                                                                                                                                                                                |
| [`skills-and-practices`](../syntheses/skills-and-practices-synthesis.md)                    | Practitioner collaboration patterns + Claude skills filtered for Dan's profile. Primary cluster anchor remapped to g11 (agent frameworks) 2026-05-05. (Entrepreneurship content extracted to its own synthesis 2026-05-05.)                                                                                                                                                                                                                                     |
| [`memory`](../syntheses/memory-synthesis.md)                                                | Garrison thread + Mughal practitioner article: memory as Phase 2 first-class pillar, five-layer architecture (A–E) per DEC-0028–DEC-0043 + DEC-0052. Layer C v0 substrate (SQLite + SHA-256 content-hashing + JSONL audit log; DispatchEvent validates router primitives at construction per DEC-0031) landed 2026-05-16 via PR #35; 35 unit tests pass.                                                                                                        |
| [`humans-teams-performance`](../syntheses/humans-teams-performance-synthesis.md)            | Güllich on multidisciplinary expertise + Harvey on team rhythm; Maestro/Worker analogy at three timescales. VISION.md design practice adopted (S39, 2026-05-06).                                                                                                                                                                                                                                                                                                |
| [`infra-foundations`](../syntheses/infra-foundations-synthesis.md)                          | Foundational references (attention paper, flow matching, PAN, Google AI energy, WHAM) + benchmarks (LAB-Bench, BixBench moved here 2026-05-05) + KG/network tooling (g5 anchor) — methodology + watch-the-field.                                                                                                                                                                                                                                                |
| [`native-low-bit-apple-silicon`](../syntheses/native-low-bit-apple-silicon-synthesis.md)    | BitNet + Bonsai + bitnet.cpp + flash-streaming on Apple Silicon — research → engineering → productization arc.                                                                                                                                                                                                                                                                                                                                                  |
| [`llms-in-science`](../syntheses/llms-in-science-synthesis.md)                              | Binz et al. four-perspectives framework + Knuth optimistic anchor + scientific-agent prior art (g8 anchor 2026-05-05); Linus's posture in that frame. paper-qa adopted as Phase 2c retrieval engine (DEC-0044).                                                                                                                                                                                                                                                 |
| [`function-annotation-discovery`](../syntheses/function-annotation-discovery-synthesis.md)  | Methods (ProtHGT, Horizyn-1, BioReason-Pro, DeepClust) + reasoning. Benchmarks (LAB-Bench, BixBench) moved to infra-foundations 2026-05-05; cross-reference for skill evaluation.                                                                                                                                                                                                                                                                               |
| [`generative-biology`](../syntheses/generative-biology-synthesis.md)                        | Generative biological artifacts at scales from residue → genome; SAFETY tier-control (DEC-0047, three-tier policy live in SAFETY.md) + external_api_tool registry class (DEC-0046).                                                                                                                                                                                                                                                                             |
| [`biological-foundation-models`](../syntheses/biological-foundation-models-synthesis.md)    | Pretrained FMs over DNA/RNA/protein/bacterial genome; LucaOne as KG anchor + specialists as Workers. KB `model_prediction` edge class committed (DEC-0048); `external_api` deployment field committed (DEC-0046).                                                                                                                                                                                                                                               |
| [`safety-alignment-privacy`](../syntheses/safety-alignment-privacy-synthesis.md)            | Activation observability + values + dual-use uplift + privacy through local execution. DEC-0047 (biosecurity tier), DEC-0053 (KB → hosted-Maestro flow), DEC-0054 (activation hooks API stub) all landed; SAFETY.md additions PR #16 merged.                                                                                                                                                                                                                    |
| [`agentic-systems`](../syntheses/agentic-systems-synthesis.md)                              | Multi-agent role specialization + typed messages + validation gates + critic tier; first formal theory result (regret bound). Role (DEC-0050), AgentReport (DEC-0051), and investigation memory Layer D (DEC-0052) all resolved 2026-05-06. (BixBench/LAB-Bench's agent-loop aspect cross-linked to infra-foundations as of 2026-05-05.)                                                                                                                        |
| [`entrepreneurship`](../syntheses/entrepreneurship-synthesis.md) _(added 2026-05-05)_       | Commercial surface for Linus + biotech-team literature-intelligence productization + transferable Maestro/Worker context-management patterns from quant-agent prior art (g10 anchor). E1 (open-source-by-default) and E2 (entrepreneurial-surface doc) resolved 2026-05-06; E3–E10 promoted to R2-25..R2-26, R2-50..R2-54.                                                                                                                                      |
| [`llm-hardware-design`](../syntheses/llm-hardware-design-synthesis.md) _(added 2026-05-09)_ | Idea → reality spine: LLMs producing artifacts (kernels, hardware schematics, build instructions) that downstream non-LLM actors (compiler, fab, manufacturer) accept and realize. Anchored on the QiMeng family (15 paper-notes + g12 cluster) with Sketch2Simulation as cross-thread process-engineering exemplar. 11 ADR seeds named (MTMC, idea→reality skill class, RLVR/Worker self-improvement, two-tier verification, biotech-tangible Phase 8 target). |

### Repo-cluster syntheses (12)

| Synthesis                                                                                               | One-line characterization                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`g1-apple-silicon`](../syntheses/repo-clusters/g1-apple-silicon.md)                                    | 8 repos; autoresearch-mlx as the runnable methodology substrate; trust the OS page cache. QiMeng-cpu-v1 promoted out of g1 into a forthcoming LLM-hardware-design category (see `docs/specs/qimeng-category-promotion.md`).                                                                                                                                                                                                                                                                                                                                                                        |
| [`g2-wiki-engines`](../syntheses/repo-clusters/g2-wiki-engines.md)                                      | 11 LLM Wiki implementations; high pattern convergence, no drop-in winner; wikiloom + llmbase + wikidesk + OmegaWiki most liftable.                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| [`g3-wiki-patterns`](../syntheses/repo-clusters/g3-wiki-patterns.md)                                    | 7 agent-driven wiki build patterns; obsidian-llm-wiki-local 3-tier JSON fallback for Ollama; llm-research-wiki LINT workflow.                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| [`g4-memory`](../syntheses/repo-clusters/g4-memory.md)                                                  | 9 agent-memory systems; openaugi as closest match to DEC-0029 v0; agentmemory primitives for parallel-write coordination. k-dense-byok added as Study. PR 30 (2026-05-10): Letta (MemGPT-derivative agent platform; Anthropic-compat HTTP signal — Study) and MiroFish-Offline (local fork of MiroFish; AGPL-3.0 caveat — Watch) cross-reference here for memory-substrate evidence pending synthesis refresh.                                                                                                                                                                                     |
| [`g5-graph-tools`](../syntheses/repo-clusters/g5-graph-tools.md)                                        | 7 KG/network-analysis + ETL tools; hyalo (Integrate) + keppi close Phase 3 KB tooling gap; OptimusKG + dlt added as Study.                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| [`g6-mcp-tools`](../syntheses/repo-clusters/g6-mcp-tools.md)                                            | 11 repos; fastmcp as default (DEC-0045); expanded to document-context platform (markdownify-mcp, codebase-memory-mcp, vanna, ExtractThinker, rendergit added). MCP commitment closed via DEC-0018/0045/0046; transport selection (stdio vs streamable-http) live as R2-06. PR 30 (2026-05-10): x402 (Watch — `@x402/mcp` shipped across TS/Python/Go, upgrading the Canteen-blog mention from roadmap-only to live; commercial-payments substrate for future MCP servers).                                                                                                                         |
| [`g7-harnesses`](../syntheses/repo-clusters/g7-harnesses.md)                                            | 10 agent harnesses; workgraph JSONL DAG + dispatch as recommended Phase 2a session-store shape. semanticworkbench added as HTTP-registered protocol reference. PR 30 (2026-05-10): rig (Rust + first-class Ollama provider — Study; Phase 5+ candidate provider abstraction), autogen (Study, but in maintenance mode — MAF is the live successor; cautionary signal), langgraph (Study — graph orchestration; reinforces workgraph JSONL DAG), goose (Rust + MCP harness entrant — Study), debate-or-vote (Study + Phase 3 spike candidate; round-0 vote outperforms multi-round debate finding). |
| [`g8-sci-agents`](../syntheses/repo-clusters/g8-sci-agents.md)                                          | 12 scientific reasoning agents; paper-qa as first paper-corpus Integrate, substrate decision resolved (DEC-0044, paper-qa as Phase 2c retrieval engine; aviary ships transitively); LAB-Bench canary blocklist obligation. Sketch2Simulation error-recovery loop added.                                                                                                                                                                                                                                                                                                                            |
| [`g9-bio`](../syntheses/repo-clusters/g9-bio.md)                                                        | 5 bioinformatics tools / models (ClawBio added 2026-05-10 as depth-vs-breadth complement to bioSkills); bioSkills as Phase 7 inaugural skills bundle (~438 bio skills); ClawBio as worked precedent for the per-skill engineering shape (tests + reproducibility bundle + conformance linter + plugin-marketplace distribution).                                                                                                                                                                                                                                                                   |
| [`g10-finance`](../syntheses/repo-clusters/g10-finance.md)                                              | 5 finance/quant agents (5 × Study; QuantAgent reclassified from Ignore to Study 2026-05-08, contributing the minimal four-role linear-pipeline pattern alongside TradingAgents' maximal debate-style roster); transferable Maestro/Worker context-management patterns. Anchors the entrepreneurship thematic synthesis (2026-05-05).                                                                                                                                                                                                                                                               |
| [`g11-agent-frameworks`](../syntheses/repo-clusters/g11-agent-frameworks.md) _(added 2026-05-05)_       | 8 agent framework, skills, and evaluation repos; pydantic-ai (Integrate) + promptfoo (Integrate) as immediate actionables; dspy, superpowers, gptme, huginn, Agent-Skills, lmnr as Study. Primary anchor for skills-and-practices synthesis. pydantic-ai Capabilities pattern resolved to Linus-native shape (DEC-0046 deployment field + DEC-0050 Role `capability_set`) 2026-05-06.                                                                                                                                                                                                              |
| [`g12-llm-hardware-design`](../syntheses/repo-clusters/g12-llm-hardware-design.md) _(added 2026-05-09)_ | 4 QiMeng-family repos (CodeV, QiMeng-MuPa, QiMeng-SALV, QiMeng-cpu-v1) covering LLM-driven Verilog/CUDA/processor design via planner/coder discipline + RLVR/signal-aware DPO/MuSL feedback loops. Sketch2Simulation cited as cross-thread reference exemplar (g8 member, not g12). Primary anchor for the new `llm-hardware-design` thematic synthesis.                                                                                                                                                                                                                                           |

---

## Cluster hubs and synthesis cross-edges (updated 2026-05-05)

The 2026-05-05 remapping moved the matrix from one-cluster-per-synthesis to many-to-many and added g11 as the 11th
cluster (primary anchor for skills-and-practices). Each thematic synthesis keeps a primary cluster anchor (the cluster
whose Tier-1-equivalent action is most load-bearing), but secondary edges expose where the same cluster informs multiple
syntheses. Four clusters become _hubs_ — clusters that anchor or substantively inform four or more thematic syntheses.
The hubs are the leverage points: investing in the underlying repos (or in the patterns the cluster surfaces) compounds
across multiple syntheses simultaneously.

| Hub cluster       | Thematic syntheses it touches                                                                                                                                                | Why it's a hub                                                                                                                                                                                                                                                                                    |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **g4-memory**     | memory _(primary)_, agentic-systems, llm-wiki, biological-foundation-models, security                                                                                        | The memory pillar is genuinely cross-cutting — investigation memory, claim-typed write-back, model_prediction provenance, and trust-tier tagging all share the same substrate.                                                                                                                    |
| **g7-harnesses**  | agentic-systems _(primary)_, infra-foundations, security, entrepreneurship                                                                                                   | Harnesses are where every operational pattern actually runs; workgraph-style JSONL DAG + dispatch is the recommended Phase 2a session-store shape. (skills-and-practices primary anchor moved to g11 2026-05-05; g7 remains a secondary edge.)                                                    |
| **g8-sci-agents** | llms-in-science _(primary)_, agentic-systems, skills-and-practices, llm-wiki, function-annotation-discovery, entrepreneurship                                                | paper-qa alone earns the breadth — it's the first paper-corpus tool to earn Integrate, the literature-intelligence engine for Phase 7, and the substrate-reframe ("adopt + extend") for Phase 2 KB.                                                                                               |
| **g9-bio**        | function-annotation-discovery _(primary)_, biological-foundation-models _(primary)_, generative-biology _(primary)_, skills-and-practices, llms-in-science, entrepreneurship | The biology pillar is overdetermined; bioSkills (~438 skills), Bacformer (Apple-Silicon-realistic broad-bio FM), ClawBio (added 2026-05-10 — depth-and-engineering complement to bioSkills's breadth), and the integrate trio drive the Phase 7 sub-roadmap and the inaugural commercial surface. |

Two clusters are anchors-only (anchor one or two syntheses but don't function as hubs): **g1-apple-silicon**
(native-low-bit primary; infra-foundations, security secondary), **g10-finance** (entrepreneurship primary;
skills-and-practices secondary). Both are doing focused work rather than cross-cutting work. **g11-agent-frameworks**
(added 2026-05-05) is currently an anchor for skills-and-practices primary plus secondary edges into agentic-systems and
infra-foundations — anchors-only status at launch but the pydantic-ai + promptfoo + dspy pattern library could expand
its reach as Phase 2a hardens. **g12-llm-hardware-design** (added 2026-05-09) is anchor-only for the new
`llm-hardware-design` thematic synthesis at launch; whether it expands into a hub depends on how broadly the
planner/coder/verifier discipline ports to other domains (Apple-Silicon kernel codegen, biology skill design,
schematics-from-natural-language) — the thematic synthesis flags this as Phase 6/7/8 evidence-gathering.

The remaining clusters — **g2-wiki-engines**, **g3-wiki-patterns**, **g5-graph-tools**, **g6-mcp-tools** — are
mid-degree: each touches three to five thematic syntheses, mostly as secondary edges that sharpen substrate or tooling
decisions. g5-graph-tools in particular went from unmapped at the start of 2026-05-05 to anchor of infra-foundations
plus secondary edges into memory, agentic-systems, biological-foundation-models, and security — Phase 3 KB tooling is
concentrated here. g3-wiki-patterns touches memory, llms-in-science, and infra-foundations, making it a connective edge
between substrate prior art and benchmark/KB-tooling workflows.

The synthesis-side mirror image: **safety-alignment-privacy** and **humans-teams-performance** are intentionally
repo-unmapped, and that's a property of the topic. Both feed VISION/SAFETY/benchmark-design rather than tool
integration.

---

## The unifying thesis (expanded)

Across all 27 syntheses, from completely different starting points, the same underlying claim recurs: **the bottleneck
has shifted from capability to structure.** The earlier four-synthesis version of this document already named four
angles on this; the expanded set adds four more.

- **The skills synthesis** calls it _architectural clarity_: agents can execute at speed, but only a human who has
  decomposed the task correctly, encoded the standards in files, and specified the uncertainty protocol gets useful
  output.
- **The LLM wiki synthesis** calls it _the schema is the product_: without a CLAUDE.md-equivalent governing entity
  types, contradiction policy, and epistemic standards, an LLM wiki is a junk drawer that grows faster.
- **The security synthesis** calls it _design decisions baked into the orchestration layer_: tiered trust, input
  provenance tagging, dependency minimization cannot be retrofitted.
- **The memory synthesis** calls it _structure as the precondition for capability_: single-pass transformers are
  provably stuck in TC0; the only escape is recursive state maintenance plus reliable history access, both architectural
  properties.

Three more angles entered with the post-fan-out work:

- **The agentic-systems synthesis** calls it _role specialization at the right granularity_: multi-agent systems
  collapse without explicit Role types and typed `AgentReport` messages; structured shared state is the antidote to
  multi-step drift.
- **The function-annotation-discovery synthesis** calls it _typed structured prediction wrapping free-text rationale_:
  the right default mode for any new skill in a domain where claims need to be auditable.
- **The humans-teams-performance synthesis** calls it _preserve room for multidisciplinary work_: Güllich's evidence on
  generative expertise generalizes to the AI collaboration setting — narrow specialization is the wrong shape for
  Maestro tasks even when it looks more efficient locally.
- **The entrepreneurship synthesis** (added 2026-05-05) calls it _commercial surface only crystallizes when the
  underlying schemas, citation discipline, and Maestro/Worker context-management patterns are right_: the g10-finance
  quant-agent prior art shows that the same context-budget and dispatch primitives Linus needs internally are also what
  make the literature-intelligence offering credible to a biotech buyer. Productization is downstream of structure, not
  upstream of it.

Mughal's practitioner data adds the operational shape of the same claim from yet another angle (disciplined context
management buys back ~25–45 percentage points of session quality across long sessions versus unmanaged context).

The compound implication for Linus is unchanged from the original 2026-05-03 framing, just stronger: **the most
important Phase 2 work is not standing up services; it is getting the schemas, specs, standards, and memory architecture
right.** Every correction filed back into CLAUDE.md, every ADR, every spec is worth more than ten implementation
shortcuts.

---

## How the syntheses overlap

Many of the syntheses cover orthogonal territory; some have substantial overlap that's worth naming explicitly.

### KnowledgeBase has three syntheses pointing at it

- **llm-wiki** supplies the operational discipline (claim typing, content hashing, write-back, quality gate as surface).
- **memory** supplies the architectural framing (KB as Layer E of the five-layer pillar per DEC-0052; uniform read API
  across layers).
- **biological-foundation-models** supplies a near-term obligation (`model_prediction` edge class with provenance before
  Group A skills start writing back).

The g2 + g3 wiki clusters add concrete prior art (wikiloom's chunk-id formula, llm-research-wiki's typed page schema,
atomic-knowledge's get_context walker, obsidian-llm-wiki-local's 3-tier JSON fallback). The g8 cluster adds **paper-qa
as the first paper-corpus-shaped tool to earn Integrate**, which reframes Phase 2 KB substrate from "build" to "adopt +
extend." The g5 cluster adds **hyalo + keppi as the Phase 3 KB tooling layer** (lint + transactional link rewrites +
bounded-BFS-with-decay context_pack retrieval). Together: the KB layer has the most diverse multi-synthesis input of any
architectural component.

### Memory has two syntheses + one cluster pointing at it

- **memory** is the canonical thesis (Garrison + Mughal; M1–M17 resolved 2026-05-03).
- **agentic-systems** adds a fifth layer (investigation memory: task-scoped, multi-agent, single-investigation lifetime
  — Kosmos world model, Sketch2Simulation IR, HKUST QuantAgent context buffer).
- **g4-memory** cluster surfaces openaugi as closest existing match to DEC-0029 v0 substrate; agentmemory's
  lease/signal/checkpoint primitives as concrete prior art for parallel-Worker write coordination.

The investigation-memory layer is the most consequential addition — it forces a question on whether
`memory-architecture.md` should grow a Layer E or whether existing layers can absorb the new use case.

PR 30 (2026-05-10) added the **MemGPT paper** (`paper-notes/Letta-2310.08560.md`, paired with `repo-notes/Letta.md`) as
a paired-repo entry. MemGPT is the LLM-as-OS framing — a hierarchical memory-paging architecture (main context window as
RAM; archival store as disk) that predates the five-layer pillar but covers similar ground for the Layer C ↔ Layer B
boundary. Folding the substantive findings into `memory-synthesis.md` is a deferred refresh; pre-refresh, the paper and
Letta repo-note carry the detail.

### Safety has two syntheses pointing at it

- **security** covers the supply-chain / dep / endpoint / prompt-injection axes (resolved 2026-05-03 Tier 0).
- **safety-alignment-privacy** covers the activation-observability / values / dual-use / privacy axes.

These are non-overlapping in topic but converge on one operational implication: SAFETY.md needs additions from both
sides, and the four-axis safety-alignment-privacy synthesis recommends a single PR with explicit per-section Dan review
for the four additions it identifies.

### Biology has three syntheses + one cluster pointing at it

- **function-annotation-discovery** for methods + benchmarks.
- **generative-biology** for SAFETY tier-control + external_api_tool registry.
- **biological-foundation-models** for Phase 7 substrate strategy (LucaOne as KG anchor; specialists as Workers).
- **g9-bio** cluster surfaces Bacformer (Apple-Silicon-realistic broad bio FM) + bioSkills (Phase 7 inaugural ~438
  skills) + DeepSeMS (BGC → SMILES generative skill) + BioReason (CUDA-locked architecture reference) + ClawBio (added
  2026-05-10 — depth-vs-breadth complement to bioSkills; the closest existing worked example of a Phase 7 inaugural
  bio-skills bundle in working form, with per-skill tests + reproducibility bundle + conformance linter + Claude Code
  plugin-marketplace distribution as directly liftable engineering patterns).

The biology pillar is overdetermined: three thematic syntheses + a cluster + the integrate-verdict trio (paper-qa,
bioSkills, scientific-agent-skills) + the M1-Max-realistic broad-bio FM (Bacformer) + the worked-example bio-skills
engineering precedent (ClawBio) make Phase 7 biology its own sub-roadmap rather than a scattered set of skills.

### Infra-foundations now anchors benchmarks + KG tooling (updated 2026-05-05)

- **infra-foundations** synthesis was previously theory-and-practice-only with no repo-cluster anchor. The 2026-05-05
  remapping added two anchors:
  - **g5-graph-tools** cluster (hyalo, keppi, py3plex, others) supplies the Phase 3 KB tooling layer (lint +
    transactional link rewrites + bounded-BFS-with-decay context_pack retrieval).
  - **LAB-Bench (FutureHouse)** and **BixBench** moved from agentic-systems to infra-foundations as Phase 1
    Worker-selection benchmarks. Their agent-loop aspect is cross-linked from agentic-systems but the benchmark
    obligation (canary blocklist, Phase 1 baseline adoption with caveats, FutureHouse evaluation philosophy ADR) lives
    here.

This consolidates the benchmark and KB-tooling threads in one synthesis rather than scattered between agentic-systems
and function-annotation-discovery.

### llms-in-science now anchors scientific-agent prior art (updated 2026-05-05)

- **llms-in-science** synthesis was previously theory-and-practice-only with no repo-cluster anchor.
- **g8-sci-agents** cluster supplies the scientific-agent prior art (paper-qa as first paper-corpus Integrate;
  research-agent harnesses for literature work; LAB-Bench canary blocklist obligation). paper-qa specifically reframes
  Phase 2 KB substrate from "build" to "adopt + extend."

The llms-in-science thread is now substrate-grounded rather than purely posture-shaping.

### Inference / training has one synthesis + one cluster

- **native-low-bit-apple-silicon** covers the full BitNet + Bonsai + bitnet.cpp + flash-streaming arc.
- **g1-apple-silicon** is mostly autoresearch-mlx as runnable methodology substrate + the trust-the-OS-page-cache
  finding.

Plus the original repo-landscape's pre-fan-out cluster (pmetal, mlx-flash, flash-moe, ANE, Bonsai-demo, BitNet) which is
woven into the synthesis rather than carrying a separate cluster doc. The convergence here is operational more than
architectural: the same conclusions ("trust the OS page cache," "1-bit and ternary are the efficient frontier on M1
Max," "pmetal is the inference-backend lead pending Phase 1b verdict") show up under both substrates.

### Entrepreneurship now has its own synthesis + one cluster (added 2026-05-05)

- **entrepreneurship** synthesis pulls Dan-profile-relevant commercial surface out of skills-and-practices into a
  first-class thread, anchored on g10-finance and pairing with the biology pillar's literature-intelligence stack.
- **g10-finance** cluster (TradingAgents, both QuantAgents, etc.) supplies transferable Maestro/Worker
  context-management patterns and a worked-example domain (quant) where structured agent loops have already shipped to a
  paying audience. The patterns generalize — the domain does not.

The entrepreneurship synthesis is intentionally cross-cutting: it reads Phase 7 biology output (paper-qa + bioSkills +
Bacformer + LAB-Bench + KnowledgeBase) as the inaugural commercial surface, and reads g10's harnesses as the
context-management pattern library.

### LLM-hardware-design has its own synthesis + one cluster (added 2026-05-09)

- **llm-hardware-design** synthesis frames the **idea → reality** spine — LLMs producing artifacts (kernels, hardware
  schematics, build instructions) that downstream non-LLM actors (compiler, fab, manufacturer, contractor, builder)
  accept and realize as physical or computational artifacts. Anchored on 15 QiMeng-family paper-notes plus the g12
  cluster, with Sketch2Simulation as cross-thread process-engineering exemplar (a g8-sci-agents member, not a g12
  member). 11 ADR seeds are flagged inline (`_Seed: DEC-NNNN_`), most importantly: MTMC pipeline as Linus orchestration
  substrate, RLVR-with-automated-oracle as canonical Worker self-improvement architecture, and idea→reality as a
  load-bearing Phase 7 skill class.
- **g12-llm-hardware-design** cluster surfaces the planner/coder/verifier discipline across 4 QiMeng repos (CodeV,
  QiMeng-MuPa, QiMeng-SALV, QiMeng-cpu-v1), with QiMeng-SALV identified as the cleanest tractable Apple-Silicon
  reproduction target (signal-aware DPO + AST-based reward shaping); MuPa-on-MLX as Phase 7/8 highest-leverage
  application; cpu-v1's behavioral-synthesis methodology as the ongoing reference.

The thread reaches into native-low-bit-apple-silicon (the QiMeng kernel-codegen patterns inform Apple-Silicon MLX kernel
generation; QiMeng-GEMM-style hint-repo + auto-tune is a candidate Phase 6d substrate) and agentic-systems
(Sketch2Simulation's multi-agent error-recovery loop is the closest sibling pattern; planner/coder/verifier Roles extend
the existing Role specialization argument). Phase 6/7/8 evidence-gathering is the immediate need; Phase 8's "design real
physical things from natural language" target is the strategic destination per Dan's stated framing in
[`qimeng-category-promotion.md`](../specs/qimeng-category-promotion.md).

### Orchestration has three syntheses + two clusters (updated 2026-05-05)

- **agentic-systems** for multi-agent typing (Role, AgentReport, validation gates, critic tier, regret bound).
- **skills-and-practices** for build-vs-adopt orchestration primitives (Task Master AI, claude-squad, fastmcp).
- **security** for dep philosophy (delete langchain/langgraph; orchestration logic is the work, not extra).
- **g7-harnesses** cluster surfaces workgraph as the most directly liftable orchestration runtime (JSONL DAG + dispatch
  as recommended Phase 2a session-store shape).
- **g11-agent-frameworks** cluster (added 2026-05-05) adds the behavioral layer: pydantic-ai as the Worker base
  abstraction, superpowers + gptme as behavioral-discipline patterns, promptfoo as the evaluation harness, dspy as the
  Phase 6 fine-tuning primitive. g11 answers _how Workers are built and validated_, where g7 answers _how Workers are
  orchestrated at runtime_.

These converge on a single architectural implication: **build the custom orchestration layer (DEC-0002 stands), but
adopt patterns/primitives from off-the-shelf tools rather than re-implement them.** Phase 1f deliverable is the explicit
Algorithm-check.

**everything-claude-code (added 2026-05-18) cross-cuts skills-and-practices + g7-harnesses + agentic-systems +
g6-mcp-tools.** affaan-m's 182K-star multi-harness performance system anchors a fourth cross-edge in the orchestration
cluster — the closest existing reference to the full Claude-Code-shaped ecosystem (skills + hooks + agent files + MCP
configs + runtime gating). Primary thematic home: skills-and-practices; secondary: g7-harnesses (multi-harness pattern
as strong confirming signal for DEC-0017 harness plurality).

---

## Where the syntheses tension

Most cross-synthesis tension is now soft (different angles on the same problem) rather than hard (incompatible
recommendations). Three tensions are worth naming explicitly:

**1. Custom orchestration vs. off-the-shelf, sharpened.** skills-and-practices says "delete before building";
agentic-systems says "Role + typed AgentReport + investigation memory must be first-class." Resolution adopted
2026-05-03: keep DEC-0002 (custom orchestration) but Algorithm-check primitives via the new Phase 1f deliverable; adopt
the PRD→tasks pattern as a skill, not a re-implementation. The agentic-systems synthesis sharpens this with ADR-shaped
sub-questions (Role as first-class type, typed inter-agent message format) that need to land before the spawner ships.

**2. Local-first as design constraint vs. hosted-Maestro as load-bearing.** safety-alignment-privacy ("local execution
as the privacy mechanism") and llms-in-science (Schulz et al.: open-source as reproducibility floor) push hard toward
local. memory and skills-and-practices treat hosted Claude as the Maestro indefinitely. The reframing (critic-tier as a
router primitive, not a binary local/hosted question — which Roles are tagged critic-tier and what is the budget
policy?) absorbs the tension. **New Tier 2 question (S14):** make this explicit.

**3. Specialist vs. generalist FMs in biology.** function-annotation-discovery and biological-foundation-models disagree
on whether LucaOne (generalist) or task-specific specialists (RiNALMo, ESM3) should be the Phase 7 default. The hybrid
recommendation (LucaOne as KG anchor; specialists as task workers) is a hedge; the empirical sub-question is whether
benchmarking LucaOne head-to-head against the specialists reveals a clear winner. **New Tier 2 question (S18):** resolve
via head-to-head in `benchmarks/dan_tasks/biology/`.

---

## Cross-cutting implications

### KnowledgeBase pattern requirements (consolidated from llm-wiki + memory + biological-foundation-models)

The Phase 2 KB schema must encode, before the first Worker writes back:

- **Claim typing** (`[!source]` / `[!analysis]` / `[!unverified]` / `[!gap]` from llm-wiki).
- **Content hashing for staleness** (SHA-256 of source files at compile time, also a security mechanism).
- **Write-back rule** as structural Worker spec requirement (every task returns deliverable + KB update proposals).
- **`model_prediction` edge class** with producing-model + version + confidence + content-hash provenance for
  model-derived KG content (biological-foundation-models requirement).
- **LAB-Bench canary blocklist** at ingestion time (g8 cluster requirement).
- **Quality gate as quality surface, not hard gate** — Dan is the primary filter (resolved Tier 1 #6, 2026-05-03).

### Maestro/Worker discipline (consolidated from skills + memory + agentic-systems)

- **Task specs** must answer goal/constraints/uncertainty before dispatch.
- **Context scope** is a design constraint, not a preference — Workers receive the minimum context for their subtask.
- **Parallel fan-out** investments are in spec quality and decomposition, not in spawning machinery.
- **Batched sessions** address startup-cost overhead.
- **Scratchpad as first-class durable artifact** — DEC-0030 forbids the o1 anti-pattern.
- **`cot_budget` and `memory_mode`** as router primitives — DEC-0031.
- **In-context cap policy** (16K Phase 2 floor; episodic-store overflow) — DEC-0032.
- **Role + typed AgentReport** before the multi-agent spawner ships — resolved via DEC-0050 (Role) and DEC-0051
  (AgentReport); Phase 3 implementation per `docs/specs/phase3-spawner.md` design-intent stub.
- **Investigation memory** as a fifth named layer in the memory architecture — resolved 2026-05-06 via DEC-0052; Layer D
  in the five-layer pillar (A–E).

### Safety posture (consolidated from security + safety-alignment-privacy)

- **Dependency surface minimization** — delete langchain/langgraph (resolved Tier 0, 2026-05-03).
- **Hash-pinned lock files + monthly pip-audit** — production env hardening (resolved Tier 0).
- **Trust-tier tagging on every context-window item** — Phase 2 architectural commitment.
- **Incident response protocol** — drafted in SAFETY.md (Supply Chain Incident Response section); resolved Tier 0,
  2026-05-03.
- **Activation-hooks API stub Phase 1, feasibility spike Phase 2** — resolved via DEC-0054 (API stub Phase 1,
  feasibility spike Phase 2 against mlx-lm; Phase 6 steering ADR if spike passes).
- **KB → hosted-Maestro flow policy** — resolved via DEC-0053; `hosted-ok` / `hosted-forbidden` binary tag at ingest
  time, conservative default `hosted-forbidden`. Enforcement in SAFETY.md.
- **SAFETY.md tier-control for generative whole-genome design** — resolved via DEC-0047; three-tier biosecurity policy
  (residue / gene / whole-genome) with sign-off + out-of-band review at the top tier. Codified in SAFETY.md.
- **Four SAFETY.md additions as a single PR with per-section Dan review** — completed 2026-05-07 as PR #16 (Task E in
  `docs/specs/planning-update-spec.md`).

### Phase 7 skills + entrepreneurial surface (consolidated from biology trio + entrepreneurship + g8/g9/g10)

- **Inaugural Phase 7 skills bundle:** bioSkills (~438 bio skills) + scientific-agent-skills (~135 broad science skills)
  = ~573 total (S30).
- **Literature intelligence stack:** paper-qa + bioSkills + Bacformer + LAB-Bench + KnowledgeBase as the concrete
  components for `docs/entrepreneurial-surface.md` — now owned by the entrepreneurship synthesis (added 2026-05-05).
- **Generalist × specialist FM combinations sequencing:** Trias+GenNA, REBEAN+DeepSeMS, Bacformer+DeepSeMS first three
  Phase 7-tractable; mCSM-metal+DISCO and AlphaGenome+GenNA Phase 8 (S31).
- **Transferable Maestro/Worker context-management patterns** from g10-finance quant-agent prior art applied to the
  biotech literature-intelligence offering (entrepreneurship synthesis).

---

## What's missing

The 2026-05-04 / 2026-05-05 / 2026-05-06 sweeps closed most of the gaps the prior version of this section listed. After
PR #22 + the 2026-05-10 PR 30 audit + the 2026-05-16 Wave 2 implementation landings, the only remaining open writing
item is:

- **`docs/EPISTEMIC-STANDARDS.md`** defining claim categories Linus distinguishes (Marelli operationalized; generalizes
  the LLM-wiki KB categories — S22). Phase 2a deliverable; needs KB schema (DEC-0048) and claim types (DEC-0023) live
  before the standards doc is operational.

Closed during the resolution arc:

- **`docs/protocols/maestro-protocol.md`** (S57): drafted 2026-05-07 (~18KB) via PR #22 at
  [`docs/protocols/maestro-protocol.md`](../protocols/maestro-protocol.md). The original §"What's missing" entry pointed
  at the pre-move path `docs/maestro-protocol.md`; the 2026-05-10 audit corrects the path and reclassifies this from
  open to closed. Phase 2a operationalization scheduling is the residual work.
- **Modern-Transformer-reference paper** (S38): closed 2026-05-06 as Tier 3 documentation deferral; absorbed into the
  infra-foundations synthesis's Transformer reference section rather than authored as a separate paper.
- **Phase 3 spawner ADR + spec** (S9, S10, S13): closed 2026-05-06 / 2026-05-07. Role + AgentReport + investigation
  memory all have ADRs (DEC-0050, DEC-0051, DEC-0052). Design-intent stub exists at `docs/specs/phase3-spawner.md`; full
  implementation spec is a Phase 3 Maestro task per Dan's direction.
- **Phase 7 biology sub-roadmap**: closed 2026-05-07 as `docs/specs/biology-phase7-roadmap.md` (Task F.3 in the
  planning-update spec).
- **Phase 2a orchestration HTTP backend bootstrap**: closed 2026-05-16 via PR #32 — `src/linus/server.py` ships an
  OpenAI-compatible `/v1/chat/completions` endpoint backed by Ollama. The Anthropic-compat surface per DEC-0056 (PR #36)
  is the immediate follow-on.
- **Phase 2c KnowledgeBase read-only adapter**: closed 2026-05-16 via PR #34 — `src/linus/knowledge/adapter.py` opens
  the upstream metadata.db via `file:?mode=ro`; first DEC-0044 paper-qa integration is the next step.
- **Phase 2h memory v0 substrate**: closed 2026-05-16 via PR #35 — SQLite episodic store + audit log + content-hashing
  for the Layer C substrate per DEC-0029; Worker-dispatch integration is the next open item.
- **Phase 1d Dan task suite v0**: closed 2026-05-16 via PR #33 — first baseline run against `qwen2.5-coder:7b`
  collected; three-task suite operational; qwen3:8b rerun pending.
- **Anthropic-compat HTTP ADR (DEC-0056)**: closed 2026-05-16 via PR #36 — amends DEC-0005 to commit Phase 2a
  orchestration HTTP to dual OpenAI- and Anthropic-compatible surfaces.
- **AGPL-fork posture ADR (DEC-0057)**: closed 2026-05-16 via PR #36 — clean-room study, no code lifts without
  project-level license commitment. Resolves the MiroFish-Offline-driven open gap and R2-34.
- **x402-mcp graduation pathway ADR (DEC-0058)**: closed 2026-05-16 via PR #36 — Watch → Spike → Integrate progression
  with concrete triggers; Watch today.
- **DEC-0055 filename discipline ADR**: closed 2026-05-16 via PR #31 — codifies the ASCII-safe `context/` filename
  convention applied during the bulk rename of 23 files; 16 markdown files updated to reference the new paths.

---

_This document should be revisited when any new synthesis lands, when a Phase boundary closes, or when a Tier 1 question
resolves in a way that materially changes the cross-synthesis picture._
