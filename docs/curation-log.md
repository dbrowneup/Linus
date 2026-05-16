# Curation Log

Memory of what was added, removed, or archived from `repos/`, `context/`, and `docs/`, when, and why. See
[curation-protocol.md](protocols/curation-protocol.md) for the policy.

Entries are append-only and ordered by date. New entries are added at the bottom of the **Entries** section.

## Format

For removals/archives:

```
## YYYY-MM-DD — <action>: <path>

**Action:** archived | removed
**Rationale:** <why>
**Last-commit SHA:** <SHA pointer to commit before action>
**Source review:** <which quarterly review or planning session triggered the action>
```

For batch additions (initial clones, themed clone batches):

```
## YYYY-MM-DD — added: <count> <theme> repos to <path>

**Action:** added
**Rationale:** <why; pointer to source synthesis or planning session>
**Source review:** <planning session or trigger>
```

## Entries

### 2026-05-04 — added: 67 community repos to `repos/`

**Action:** added **Rationale:** Section 7.1 of `docs/specs/planning-update-spec.md` enumerated an initial dozen
community repos identified via the LLM Wiki and skills syntheses as Phase 2–3 reference material. Dan executed the clone
manually and substantially expanded the list to 67 repos covering ten cross-cutting themes: Apple Silicon inference
(`autoresearch-mlx`); LLM Wiki engine implementations (`link`, `llmwiki`, `llmbase`, `llmwiki-cli`, `wikidesk`,
`wikiloom`, `wikimind`, `OmegaWiki`, `swarmvault`, `synthadoc`, `TheKnowledge`); LLM Wiki agent-driven build patterns
(`agentic-wiki-builder`, `AgenticResearchWiki`, `llm-research-wiki`, `llm-wikidata`, `atomic-knowledge`, `beever-atlas`,
`obsidian-llm-wiki-local`); agent persistent memory (`agentmemory`, `anamnesis`, `omega-memory`, `engram`, `remember`,
`prompt-vault`, `openaugi`, `memex`); knowledge-graph and network-analysis tooling (`infranodus`, `infranodus-skills`,
`py3plex`, `keppi`, `hyalo`, `prism`); MCP servers and code/document context tools (`fastmcp`, `ontomics`, `codesight`,
`qmd`, `vectorless`, `WeKnora`); agent harnesses and orchestration (`claude-squad`, `claude-task-master`, `codebuff`,
`workgraph`, `openrouter-skills`, `python-sdk`, `origin`, `gravityfile`); scientific reasoning agents — primarily the
FutureHouse stack (`paper-qa`, `aviary`, `ldp`, `robin`, `ether0`, `BixBench`, `LAB-Bench`, `finch`,
`scientific-agent-skills`, `ibmdotcom-tutorials`); bioinformatics and domain-specific science models (`Bacformer`,
`BioReason`, `bioSkills`, `deepsems`); finance and quant agents (`dexter`, `OpenBB`, `QuantAgent`, `TradingAgents`,
`nixtla`). Repo-note generation proceeds group-by-group on `feature/repo-notes-g<N>-<theme>` branches; each repo-note
carries its own one-paragraph rationale per the curation protocol. **Source review:** planning session 2026-05-04.

### 2026-05-04 (late) — added: 2 agent-platform repos to `repos/`

**Action:** added **Rationale:** Added during Phase 1 recon after the main 67-repo batch; captured as distinct late
additions. `claude-prism` (PrismML 1-bit 8B MLX model, companion to `Bonsai-demo`) and `semanticworkbench` (Microsoft
multi-agent orchestration research platform) were cloned for study as part of the ongoing harness and orchestration
survey feeding `docs/syntheses/repo-clusters/g7-harnesses.md`. **Source review:** planning session 2026-05-04.

### 2026-05-05 — added: 18 repos to `repos/` (skills-and-practices + model-hardware research)

**Action:** added **Rationale:** Two waves cloned in the same session.

**Wave 1 — skills-and-practices focus (14 repos):** `superpowers` (agentic workspace with memory/tools/RAG),
`Agent-Skills-for-Context-Engineering` (structured agent-skill patterns for context engineering),
`vanna` (text-to-SQL natural-language interface), `codebase-memory-mcp` (MCP server exposing persistent codebase
memory), `pydantic-ai` (type-safe agent framework built on Pydantic), `dspy` (Stanford declarative LLM programming
framework), `lmnr` (LLM monitoring, observability, and evaluation platform), `rendergit` (render git repos as visual
maps), `gptme` (terminal-first personal AI assistant), `markdownify-mcp` (MCP server converting web pages to Markdown),
`dlt` (Python data-load tool for building data pipelines), `promptfoo` (LLM eval and red-teaming CLI),
`ExtractThinker` (structured document-extraction framework with OCR support), `huginn` (self-hosted event-driven
automation platform). These repos directly anchor or extend the skills-and-practices synthesis and the new
entrepreneurship synthesis via the E-series question sweep. **Source review:** planning session 2026-05-05.

**Wave 2 — model-hardware research (4 repos):** `Sketch2Simulation` (vision-to-simulation pipeline, touch-interface
prototyping reference), `k-dense-byok` (knowledge-dense BYOK retrieval architecture),
`OptimusKG` (knowledge-graph-grounded LLM optimization), `QiMeng-cpu-v1` (CPU-optimized LLM inference reference,
Apple Silicon portability study). These feed the native-low-bit-apple-silicon synthesis and the hardware-sovereignty
thread in the entrepreneurship synthesis. **Source review:** planning session 2026-05-05.

### 2026-05-05 — added: 16 papers to `context/papers/` + 4 notes-derived paper-notes (catch-up)

**Action:** added **Rationale:** Catch-up entry — sixteen papers and four notes-derived paper-notes were authored
2026-05-05 alongside the repo waves above but were not logged at the time. The papers cover four threads. (a) The
**modern transformer-architecture lineage** feeding `infra-foundations-synthesis.md`: `1910.07467` (Root Mean Square
Layer Normalization), `2002.05202` (GLU Variants), `2104.09864` (RoFormer / RoPE), `2305.13245` (GQA), and four
architecture-survey papers (`2311.12351` long-context, `2410.11381` converging architectures, `2412.03220` LLM
architectures, `2508.09834` efficient architectures). (b) The **QiMeng / LLM-hardware-design cluster** (later seeded
under `docs/specs/qimeng-category-promotion.md`): `2511.20099v4` (QiMeng-CRUX), `2511.20100v1` (QiMeng-Kernel),
`2306.12456v2` (Pushing the Limits of Machine Design), `2506.05007v1` (QiMeng: Fully Automated Hardware and Software
Design), and `0549` (Automated Superscalar Processor Design). (c) Garrison's `2412.17794v1` (Memory Makes Computation
Universal, Remember?) anchoring `memory-synthesis.md`. (d) `d41586-026-00974-2` (Nature feature on self-driving labs)
for `llms-in-science-synthesis.md` and `2604.27269v1` (OptimusKG paper) paired with the OptimusKG repo-note for
`biological-foundation-models-synthesis.md`. The four notes-derived paper-notes
(`bandaru_transformer_design_guide_pt2_modern_architecture`, `jytan_2025_crystallization_of_transformer_architectures`,
`mughal_context_window_management`, `raschka_2025_big_llm_architecture_comparison`) capture articles cited across
multiple syntheses that warranted full paper-note treatment despite their source files living in `context/notes/`
rather than `context/papers/` — a recognized paper-note variant per CLAUDE.md §Doc-type conventions.
**Source review:** notes-cleanup-fanout (PR #24) + planning-update-execution session 2026-05-07.

### 2026-05-09 — added: 12 papers + 5 repos to `context/papers/` and `repos/` (context fold-in pass)

**Action:** added **Rationale:** Three discrete sub-batches landed 2026-05-09 during the context fold-in inventory
pass (this session).

**Sub-batch 1 — QiMeng family expansion (10 papers + 3 repos).** Ten additional papers from the ICT / CAS
Yunji Chen / Qi Guo group covering Verilog generation, GEMM and FlashAttention kernel synthesis, OS kernel
configuration tuning, sequential→parallel CUDA translation, neural-symbolic transcompilation, and superscalar
processor design: `13337-ZhouQ` (QiMeng-GEMM), `2407.10424v5` (CodeV), `2505.06302v1` (QiMeng-TensorOp),
`2505.24183v5` (QiMeng-CodeV-R1), `2506.11153v2` (QiMeng-MuPa), `2506.12355v1` (QiMeng-Attention),
`2510.19296v4` (QiMeng-SALV), `3696443.3708931` (VEGA), `9546_AutoOS_Make_Your_OS_More_` (AutoOS), `osdi25-dong`
(QiMeng-Xpiler). Plus three paired repos: `repos/CodeV`, `repos/QiMeng-MuPa`, `repos/QiMeng-SALV`. The full
batch is enumerated and scoped for synthesis under `docs/specs/qimeng-category-promotion.md`; targets are
`g12-llm-hardware-design` cluster + `llm-hardware-design-synthesis.md`.

**Sub-batch 2 — generative cellular biology FM pair (2 papers + 2 repos).** Two clean paper↔repo pairs at the
cell-imaging and cross-species transcriptomic frontier: `2026.03.31.715748v1.full` (ProtiCelli — Sun et al.,
Stanford / CMU / KTH / CZ Biohub, bioRxiv 2026) paired with `repos/ProtiCelli`; and `science.aec8514`
(TranscriptFormer — Pearce et al., CZ Biohub / CZI, Science 2026) paired with `repos/transcriptformer`. Slated
for `biological-foundation-models-synthesis.md` (primary) and `generative-biology-synthesis.md` (secondary, for
ProtiCelli). Both extend the "specialists as Workers" framing in BFM with the `model_prediction` edge class
(DEC-0048) and `external_api_tool` deployment field (DEC-0046) as integration hooks.

**Sub-batch 3 — local-LLM and ecosystem repos (5).** `repos/Kimi-K2` — Moonshot's open MoE 1T-total / 32B-active
model with bundled tech report at `tech_report.pdf` (arxiv 2507.20534). Receives elevated multi-synthesis treatment
per Dan's framing as a Phase 6/8 candidate alongside or replacing Qwen3 — see open ADR seeds DEC-0055 (Phase 6 base
candidate) and DEC-0056 (Phase 8 Linus-flavored 1-bit Kimi-K2 research direction). Paper-note will use the hybrid
filename `Kimi-K2-2507.20534.md` per CLAUDE.md §Doc-type conventions paired-repo variant. Other repos: `repos/jan`
(Menlo Research's open-source local-model front-end, slated for g7-harnesses); `repos/claude-code-guide`
(Anthropic-curated workflow guide, slated for g11-agent-frameworks + skills-and-practices); `repos/cs249r_book`
(Harvard CS249R *Machine Learning Systems* textbook, slated for infra-foundations as educational reference);
`repos/awesome-ml` — multi-domain ML index, **logged here as indexed-resource only with no per-repo note authored**
per the curation discipline that index-style meta-resources are tracked in the log rather than via per-repo notes.

**Source review:** context fold-in inventory pass, 2026-05-09 (this session).

### 2026-05-10 — added: 1 paper + 8 repos to `context/papers/` and `repos/` (PR 30 cleanup pass)

**Action:** added **Rationale:** Final coverage pass after the 2026-05-09 fold-in inventory and the
post-PR-#29 sweep agents (coverage + core-doc staleness) surfaced residual gaps. Spec:
`docs/specs/2026-05-10-pr30-cleanup-spec.md`. Three discrete sub-batches.

**Sub-batch 1 — paper-note promotions for inline-cited papers (3 papers, no new PDFs).** Three papers
already in `context/papers/` were folded inline during PR #29 per Dan's option-(a) feedback but never
received per-paper-notes. Promoted now to give them durable cross-reference handles:
`docs/paper-notes/2509.11420v1.md` (Trading-R1, Tauric/UCLA/UW/Stanford 2025 — single-model RL distillation
of multi-agent trading workflow with typed-structured-prediction output, the BioReason-Pro non-biology
canonical example);
`docs/paper-notes/2602.03082v1.md` (Geometry-Preserving Neural Architectures on Manifolds with Boundary,
Elamvazhuthi/Biswal et al., LANL + Boston College 2026 — REFERENCE-category sibling of JPmHC in the
manifold-ML thread);
`docs/paper-notes/2210.02747.md` (Flow Matching for Generative Modeling, Lipman et al., Meta AI/FAIR 2022
ICLR 2023 — REFERENCE-category companion to the Holderrieth & Erives textbook
`paper-notes/2506.02070v3.md`).

**Sub-batch 2 — Letta paired-repo paper + 5 Bin A clones + 3 Bin B clones (1 paper download + 8 repos).**
`context/papers/2310.08560.pdf` downloaded from arxiv (MemGPT: Towards LLMs as Operating Systems, Packer et
al., UC Berkeley 2023 v2 Feb 2024); paired paper-note authored at
`docs/paper-notes/Letta-2310.08560.md` using the hybrid-filename convention; pairs with the new
`repos/Letta` clone and `docs/repo-notes/Letta.md`. Additional Bin A clones: `repos/rig`
(0xplaygrounds/rig — unified Rust LLM-client library across 25 providers including first-class Ollama and
MCP via `rmcp`, MIT, 7.2k★, Study); `repos/autogen` (microsoft/autogen — multi-agent group-chat framework,
**now in maintenance mode with development redirected to Microsoft Agent Framework**, MIT, Study as frozen
reference); `repos/langgraph` (langchain-ai/langgraph — stateful agent framework with typed-graph DAG +
Pregel bulk-synchronous runtime + first-class checkpointing, MIT, Study as architectural alternative to
workgraph); `repos/x402` (coinbase/x402 — HTTP-402 payment protocol for pay-per-API-call agent surfaces;
`@x402/mcp` is shipped, not roadmap-only as the Canteen note suggested; Apache 2.0, Watch). Bin B clones:
`repos/goose` (block/goose — Block's Rust+MCP coding-agent harness, multi-protocol (native HTTP /
OpenAI-compat / Anthropic ACP), Apache 2.0, Study); `repos/debate-or-vote`
(deeplearning-wisc/debate-or-vote — NeurIPS 2025 Spotlight research code, Choi/Zhu/Li UW-Madison;
demonstrates heuristic O(N) majority-vote often matches per-step-LLM O(N²) debate; MIT, Study + spike for
Phase 3 spawner coordination model); `repos/MiroFish-Offline` (nikmcfly/MiroFish-Offline — multi-agent
swarm-intelligence simulator using Ollama + Neo4j + OASIS subprocess; **AGPL-3.0** license blocks code
incorporation into Linus; Watch with AGPL caveat). Cross-cutting signal: Letta + Kimi-K2 + Goose all
ship Anthropic-compat HTTP endpoints alongside OpenAI-compat — a three-way confirmation that DEC-0005
(OpenAI-compatible-protocol) earns a revisit at Phase 2a planning time.

**Sub-batch 3 — orphan pic embeds (no clones; reference housekeeping).** Two genuinely orphan pics from
`context/pics/` were embedded into existing prose: `Git_Branching_Model.pdf` linked from
[`BRANCHING.md`](../BRANCHING.md) §Phase 3 Migration as the locally-archived Driessen 2010 reference;
`HE2psIVbcAA6VLz.jpg` (claw-code orchestration concept diagram) embedded in
`docs/syntheses/repo-clusters/g7-harnesses.md` near the Goose / claw-code-local discussion. The earlier
sweep agent's "9 orphan pics" claim was largely an artefact of grep missing URL-encoded paths
(`%20`-encoded spaces) — 7 of 9 flagged pics were already embedded; only the 2 above were genuine orphans.

**Source review:** PR 30 cleanup spec at `docs/specs/2026-05-10-pr30-cleanup-spec.md`, 2026-05-10.

### 2026-05-16 — added: 1 awesome-list repo-note + gap-triage spec (no clones, no paper-note fold-ins)

**Action:** added repo-note + spec for an existing-but-unnoted reference resource. **Rationale:** `repos/awesome-ai-agent-papers`
(VoltAgent/awesome-ai-agent-papers — MIT-licensed curated list of 370 arxiv papers published from January 2026 onward,
organized into Multi-Agent / Memory & RAG / Eval & Observability / Agent Tooling / AI Agent Security buckets) was
present in `repos/` but unannotated. Unlike `repos/awesome-ml` — logged indexed-only on 2026-05-09 because its
multi-domain breadth made per-paper ingestion uneconomic — awesome-ai-agent-papers is **agent-themed, 2026-vintage,
and topically tight to Linus's active syntheses** (memory, agentic-systems, safety-alignment-privacy, MCP). The Wave-2
triage authored a repo-note positioning it as a **Watch verdict / ingestion source** for periodic mining on
quarterly curation reviews ([`docs/repo-notes/awesome-ai-agent-papers.md`](repo-notes/awesome-ai-agent-papers.md))
plus a paired gap-triage spec ([`docs/specs/2026-05-16-awesome-papers-gap-triage.md`](specs/2026-05-16-awesome-papers-gap-triage.md))
that cross-references the 370 awesome arxiv IDs against Linus's 70 arxiv-style paper-notes, confirms zero overlap
(the awesome list is entirely 2026-Q1/Q2 arxiv, Linus's existing arxiv notes are mostly 2023–2025), and ranks the top
20 high-priority gaps for follow-up Wave-3 ingestion. **No paper PDFs downloaded and no paper-notes authored in this
sweep** — the gap-triage spec is the durable tracker; HIGH-priority candidates flow into a follow-up PR. Cluster cell:
g11-agent-frameworks. **Source review:** Wave-2 fan-out, 2026-05-16.

### 2026-05-16 — added: Wave 2 fold-in batch (6 paper-notes + 7 external repo-notes + 4 Dan-own repos noted)

**Action:** added

**Rationale:** Targeted fold-in pass for the Linus corpus covering (a) 2 uncovered papers in `context/papers/` whose
PDFs had been added but not yet write-up'd; (b) 3 biomed/policy briefs in `context/notes/`; (c) Sutton's bitter_lesson
as foundational substrate; (d) triage of 11 new repos cloned into `repos/` since the previous curation pass.

**Detail:**

**Sub-batch 1 — 2 uncovered paper-notes** (`docs/paper-notes/`):

- `2512.24695v1.md` (Behrouz et al., _Nested Learning: The Illusion of Deep Learning Architecture_, Google Research +
  Columbia, NeurIPS 2025) — Continuum Memory System + Hope architecture + Delta Gradient Descent + Multi-Scale
  Momentum Muon. Folded into [`memory-synthesis.md`](../syntheses/memory-synthesis.md) as the 2025-era theoretical
  scaffold for the multi-timescale-update story; added to the four-candidate substrate-experiment constellation
  alongside Coconut, minGRU, and TTT.
- `s41540-026-00683-6.md` (Gallup & Steel, _Generative design of synthetic gene circuits for functional and
  evolutionary properties_, Oxford, npj Systems Biology and Applications 2026) — CVAE for whole-circuit topology
  design with paired IntaRNA physics-based validator. Folded into
  [`generative-biology-synthesis.md`](../syntheses/generative-biology-synthesis.md) as the circuit-design rung between
  sequence-design and pathway-design.

**Sub-batch 2 — 3 notes-derived paper-notes from `context/notes/`** (`docs/paper-notes/`):

- `holko_wilbanks_howell_ai_ready_biodata.md` (War on the Rocks, March 2026) — AI-Ready Biodata is America's Next
  Strategic Infrastructure. Strategic-policy commentary on biodata as the binding AI-bio constraint. Primary fold:
  [`entrepreneurship-synthesis.md`](../syntheses/entrepreneurship-synthesis.md) biodata-sovereignty thread; secondary:
  [`biological-foundation-models-synthesis.md`](../syntheses/biological-foundation-models-synthesis.md).
- `love_reynolds_goldston_frye_biomanufacturing_us.md` (MIT Policy Brief, 2024) — biomanufacturing capacity as the
  production-layer constraint companion to the biodata commentary. Primary fold:
  [`entrepreneurship-synthesis.md`](../syntheses/entrepreneurship-synthesis.md) biomanufacturing-policy thread.
- `marler_gerstein_biotechnology_warfighter.md` (RAND commentary, October 2022) — foundational dual-use threat-model
  framing for biotechnology. Primary fold:
  [`safety-alignment-privacy-synthesis.md`](../syntheses/safety-alignment-privacy-synthesis.md) democratization-as-
  orthogonal-axis; secondary: [`entrepreneurship-synthesis.md`](../syntheses/entrepreneurship-synthesis.md).

The three policy pieces together form the strategic substrate for the entrepreneurship synthesis's new
biodata-sovereignty / biomanufacturing-policy thread (added 2026-05-16).

**Sub-batch 3 — bitter_lesson** (`docs/paper-notes/sutton_bitter_lesson.md`): Sutton's 2019 essay as the foundational
methodological substrate for the Algorithm (CLAUDE.md), Maestro/Worker discipline, parallel-by-default convention, and
the broader "scale-with-compute beats encoded-human-knowledge" engineering discipline (DEC-0027 substrate). Folded
into both [`agentic-systems-synthesis.md`](../syntheses/agentic-systems-synthesis.md) and
[`infra-foundations-synthesis.md`](../syntheses/infra-foundations-synthesis.md).

**Sub-batch 4 — 7 external repo-notes for new clones** (`docs/repo-notes/`):

- `swarms.md` (kyegomez/swarms — Python multi-agent orchestration framework with 17 swarm types; Apache 2.0; Study as
  design-vocabulary cross-reference for the Phase 3 multi-agent spawner per DEC-0050).
- `AgentPrometheus.md` (chuan-gyld/AgentPrometheus — Python+Docker workspace runtime built on the "system executes,
  AI consults" design rule; license unspecified — license investigation needed before any code lift; Study as
  design-rule reference for Phase 2a/2b backend).
- `vellum-assistant.md` (vellum-ai/vellum-assistant — TypeScript+Bun personal AI assistant with four-pillar
  framing (memory/identity/proactivity/security); MIT; Study as design-vocabulary cross-reference for Phase 5+
  interface refinement and the manifest-driven `SKILL.md` + `TOOLS.json` skill format).
- `MoneyPrinterV2.md` (FujiwaraChoki/MoneyPrinterV2 — Python content-marketing-automation CLI; **AGPL-3.0** strongly
  copyleft license blocks code incorporation into Linus; Watch with AGPL caveat — independent confirmation of
  Ollama-direct over LiteLLM is the most useful Linus calibration data point).
- `local-whisper.md` (t2o2/local-whisper — Swift+SPM Apple-Silicon-optimized speech-to-text menu-bar app; MIT;
  **Adapt** recommendation — the canonical Apple-Silicon-native Linus reference app for Phase 5+ frontend work).
- `algebrica.md` (antoniolupetti/algebrica — Markdown+LaTeX+SVG university mathematics knowledge base; CC BY-NC 4.0
  non-commercial-only restricts content reuse but patterns portable; Study as content-organization pattern reference
  for the Linus KB per DEC-0015 dual-graph and DEC-0048 model-prediction edges).
- `prologue.md` (aegntic/prologue — TypeScript+Bun durable AI agent memory library with compression ladder +
  visibility boundaries + FPEF v2.0 4-phase gate discipline; MIT; Study as memory-architecture pattern reference for
  DEC-0028 memory pillar and DEC-0052 Layer D investigation memory).

**Sub-batch 5 — 4 Dan-own repos (noted but no repo-note written per discipline).** The following four repos in
`repos/` are Dan's own work clones (Agora hackathon adjacent + AI-firm exploration), not external reference material;
they appear in `repos/` for development convenience and are tracked separately via `experiments/` artifacts:

- `repos/archimedes/` — Dan's Agora hackathon Archimedes project (per `experiments/archimedes/`).
- `repos/hackathon/` — Dan's Agora hackathon working repo (per `experiments/agora-hackathon/`).
- `repos/ai-firm/` — `chuan-gyld/ai-firm`, an AI-company-of-agents exploration that Dan cloned for reference; minimal
  active engagement, kept for potential Phase 3 multi-agent precedent reference.
- `repos/openclaw-workflow/` — Dan's openclaw-adjacent workflow exploration (per the openclaw repo-note thread).

Repo-notes for these four are intentionally **not** written: archimedes/hackathon/openclaw-workflow are Dan's own
work-in-progress and don't fit the external-reference repo-note shape; ai-firm is third-party but kept as a low-stakes
reference rather than a fully audited integration candidate. If `ai-firm` becomes a more substantive Phase 3+
reference, a full repo-note can be authored at that time.

**Sub-batch 6 — INDEX backfill.** [`docs/paper-notes/INDEX.md`](../paper-notes/INDEX.md) backfilled with all 6 new
paper-notes (alphabetical insertion). [`docs/repo-notes/INDEX.md`](../repo-notes/INDEX.md) backfilled with all 7 new
external repo-notes (alphabetical insertion). Dan-own repos are not in the repo-notes INDEX since they have no
repo-note.

**Source review:** Wave 2 fold-in spec / dispatch, 2026-05-16 (this session). PR opened from
`agent/wave2-foldin-corpus`; commits atomic per concern (one per new note batch + final INDEX + curation-log commit).
### 2026-05-16 (late) — added: Wave 2 stragglers v2 (1 repo-note + 2 paper-notes)

**Action:** added

**Rationale:** Second-batch fold-in (v2) covering one repo + two papers that Dan added post-W1-straggler-agent launch.
A sibling agent (W1, branch `agent/wave2-stragglers`) is folding in caveman + symphony + swarm + SWARM-paper as the v1
straggler batch; this v2 batch on `agent/wave2-stragglers-v2` covers a strictly non-overlapping set of three artifacts.

**Sub-batch — `pi` repo-note** (`docs/repo-notes/pi.md`): `earendil-works/pi`, the Pi Agent Harness Mono Repo — a
TypeScript/Node monorepo of five npm-published packages (`@earendil-works/pi-coding-agent` CLI,
`@earendil-works/pi-agent-core` stateful-agent runtime, `@earendil-works/pi-ai` unified multi-provider LLM API across
35+ providers, `@earendil-works/pi-tui` terminal-UI library, `@earendil-works/pi-web-ui` browser-chat components),
MIT-licensed, single-maintainer-led by Mario Zechner (`badlogic`), `pi.dev` domain. pi ships a deliberately-minimal
coding harness with extension-driven customization (TypeScript Extensions, Agent Skills standard, prompt templates,
themes, pi-packages bundled via npm or git), and is the substrate openclaw consumes via `createAgentSession(...)` per
`packages/coding-agent/README.md`. pi is also reachable from goose as a provider-side ACP shim
(`crates/goose/src/providers/pi_acp.rs`), making pi the only TypeScript-side coding-agent harness in the cloned corpus
that goose reaches as a peer. Slated for `g7-harnesses` (primary cluster) + `agentic-systems-synthesis.md` (secondary
thematic — the deliberately-no-MCP / no-sub-agents / no-plan-mode posture as a data point in the multi-agent landscape
debate). Verdict: **Study**. Key reusable patterns: the `OpenAICompletionsCompat` 17-flag enumeration as a Phase 2a
endpoint-capability checklist; the session-tree JSONL shape with `parentId` pointers as an alternative-or-evolution to
the workgraph linear-DAG session store; the `terminate: true` per-tool-result hint as the canonical Phase 3
Worker-termination signal (DEC-0051 extension); the steering/follow-up queue pattern as the Maestro-interrupt
primitive; pi's explicit "what we deliberately don't ship" philosophy as a Linus discipline anchor for ARCHITECTURE.md
bounded-scope articulation. No new clone needed — `repos/pi/` already exists from an earlier sweep.

**Sub-batch — ElephantBroker paper-note** (`docs/paper-notes/2603.25097v1.md`): Cristian Lupascu, PhD & Alexandru
Lupascu (Elephant Broker, Bucharest, Romania), arXiv 2603.25097v1, 2026-03-26. An open-source cognitive runtime
pairing a Neo4j knowledge graph with a Qdrant vector store via the Cognee SDK to provide durable verifiable agent
memory. Implements a complete cognitive loop with eight named mechanisms — hybrid five-source retrieval pipeline,
eleven-dimension competitive scoring engine (with (1 − 1/e) submodularity guarantee via greedy budget-constrained
selection), four-state evidence verification model (Unverified → Self-Supported → Tool-Supported → Supervisor-Verified
with confidence multipliers 0.5 / 0.7 / 0.9 / 1.0), five-stage context lifecycle (bootstrap → ingest → assemble →
compact → afterTurn), six-layer cheap-first guard pipeline (autonomy-domain → static-rule → semantic → structural →
forced-reinjection → optional LLM escalation), nine-stage consolidation engine, three-layer AI firewall, numeric
authority model with twelve actor types and multi-organization permission hierarchy. Architecturally validated through
2,200+ tests spanning unit/integration/end-to-end. Three deployment tiers (`memory-only` / `context-only` / `full`),
five profile presets (`personal-assistant` / `research` / `coding` / `managerial` / `worker`) with inheritance,
multi-gateway isolation, web management dashboard for human oversight (EU AI Act Article 14 compliance), and
OpenTelemetry + Prometheus observability across 100+ custom metrics. **The closest published direct-competitor /
cousin to Linus's Phase 2+ Layer C episodic memory substrate** (DEC-0029) — overlapping enough to be directly
load-bearing for Linus's substrate decisions, and *different enough* (graph+vector+SDK vs. SQLite+content-hash+git) at
the substrate level that the divergence points are themselves the most informative comparison surface. Primary fold:
`memory-synthesis.md` (canonical Layer C direct-competitor reference); secondary fold:
`agentic-systems-synthesis.md` (Thread 2 structured inter-agent communication — typed authority graph + multi-tier
safety scanning); tertiary fold: `safety-alignment-privacy-synthesis.md` (six-layer cheap-first guard pipeline +
three-layer AI firewall + six-tier safety scanning as the canonical multi-tier safety enforcement reference).
Paper-note depth: ~500 lines per Dan's framing of "richly relevant to Phase 2+ memory and safety pillars; treat with
substantial depth." PDF already in `context/papers/2603.25097v1.pdf` from an earlier add.

**Sub-batch — TrustResearcher paper-note** (`docs/paper-notes/2510.20844v3.md`): Jiawei Zhou, Ruicheng Zhu, Mengshi
Chen, Jianwei Wang, Kai Wang (ACEM Shanghai Jiao Tong University; UNSW), WWW Companion '26 Dubai April 13-17 2026,
arXiv v3 2026-01-25, 6 pages. A multi-agent demo system for knowledge-grounded transparent research ideation. The
architecture decomposes ideation into four coupled stages: (A) **Structured Knowledge Curation** — LLM-guided topic
decomposition into well-formed search queries dispatched via Semantic Scholar API under a fixed retrieval budget,
followed by incremental four-phase KG construction (entity extraction → mini-batch enrichment → top-K=10 degree-based
expansion → hybrid 60/40 high-degree-vs-random sampling); (B) **Diversified Idea Generation** — literature-informed
planner agent decomposing into Problem Statement / Proposed Methodology / Experimental Validation facets, then three
parallel strategies (base variants + Graph-of-Thought variants with b=3, d=5 depth-first KG traversal scored on node
quality 0.6 + edge-type diversity 0.2 + length 0.2 + cross-pollination of top-ranked ideas) generating an α=10
over-generated candidate pool with real-time string + semantic deduplication; (C) **Multi-stage Idea Selection** —
internal weighted-criteria scoring (novelty 0.30 / feasibility 0.25 / clarity 0.20 / impact 0.25) plus iterative
Jaccard-or-LLM-score merging at threshold 0.85, then external comparison against retrieved literature via BGE-M3
embeddings retaining candidates with cosine similarity below 0.7; (D) **Expert Panel Review & Synthesis** —
asynchronous reviewer agent (technical soundness + feasibility) + novelty agent (originality + distinctness) scoring
each candidate on a 5-dimension 1-5 rubric, aggregator module fusing both perspectives, ~3.5 weak-accept threshold for
high-quality classification. The system exposes intermediate reasoning states, execution logs, configurable agents,
and JSON-archived per-component outputs through a four-region web interface. Demonstrated on k-truss breaking
producing 3 candidate research ideas in ~15-30 minutes consuming 200K+ tokens using GPT-5. Live demo + source at
`github.com/valleysprings/TrustResearcher`. **Directly relevant Phase 7+ prototype** for Linus's eventual
research-ideation skill — the four-stage architecture is portable as a Phase 7+ skill template (Curation → Generation
→ Selection → Review), the Graph-of-Thought primitive is a Phase 3+ KG-grounded-reasoning primitive candidate, and
the typed 5-dimension review rubric extends the DEC-0051 AgentReport schema for research-ideation outputs.
**Critical caveat:** the case-study performance is **not** empirically validated against baselines (single
self-curated topic from the authors' own research area, no head-to-head comparison to a simpler GPT-5 baseline);
adopt the architecture, do not adopt the performance claim. Primary fold: `llms-in-science-synthesis.md` (automated
scientific ideation under the "collaborator-like" four-perspectives frame from Schulz et al.); secondary fold:
`agentic-systems-synthesis.md` (Thread 4 validation-as-per-stage-instrumentation example via the transparency-by-design
discipline + Thread 7 hosted-frontier dependency illustration); tertiary fold:
`repo-clusters/g8-sci-agents.md` (candidate clone for Phase 7+ planning reference; clone deferral noted — clone when
Phase 7+ becomes active). Paper-note depth: ~400 lines per Dan's framing.

**Source review:** Wave 2 stragglers v2 dispatch, 2026-05-16 (this session). PR opened from
`agent/wave2-stragglers-v2`; commits atomic per artifact (one for the pi repo-note, one per paper-note, one for INDEX
+ curation-log + synthesis-edits consolidation). Sibling W1 batch (`agent/wave2-stragglers`) carries caveman +
symphony + swarm + SWARM-paper; this v2 batch is strictly non-overlapping.

### 2026-05-16 — added: Wave 2 stragglers v1 (3 repo-notes + 1 paired paper-note)

**Action:** added

**Rationale:** First-batch fold-in (v1) covering three repos plus one paired paper that Dan added immediately
post-PR-30. Sibling agent W2 (branch `agent/wave2-stragglers-v2`, entry above) covers a strictly non-overlapping
second batch (pi repo-note + two paper-notes); the two batches were dispatched concurrently against the same base
SHA (`9b91b66`) on `main` so cherry-pick consolidation is clean.

**Sub-batch 1 — `caveman` repo-note** (`docs/repo-notes/caveman.md`): `JuliusBrussee/caveman`, a Claude Code skill
plus 30+-harness install matrix that constrains agent output to telegraphic fragments while preserving technical
content, with a measured **~65–75% output-token reduction at 100% technical accuracy** validated through a three-arm
eval harness (skill vs. terse-baseline vs. no-prompt — honest delta is skill vs. terse to avoid conflating with
generic conciseness) and a real-Claude-API benchmark suite (average 65% reduction across 10 prompts, range 22–87%).
MIT-licensed, single-maintainer-led by Julius Brussee. Skill (not framework or substrate) — no cluster letter applies.
Slated for `skills-and-practices-synthesis.md` (primary) and `memory-synthesis.md` (secondary — the auto-clarity rule
as the design pattern for DEC-0032's explicit cap-bypass-audit-log discipline on the output-token-budget side). Verdict:
**Study + Adapt**. Key reusable patterns: an `output_style` Worker dispatch field (`verbose` / `default` / `terse` /
`caveman`) as a sibling to `memory_mode` and `cot_budget` per DEC-0031, with the dispatcher injecting the matching
system-prompt rider and the audit log recording the choice; a `CLAUDE.compact.md` startup-budget optimization producing
~46% input-token savings on every session start while preserving code blocks / URLs / paths / commands byte-identical;
the auto-clarity bypass discipline (drop to normal prose for security warnings, irreversible actions, multi-step
sequences with ambiguity risk, user-confused states) as the design pattern for "compress aggressively, bypass under
documented conditions"; the three-arm eval discipline (skill vs. terse vs. baseline) for the Phase 1c+ benchmark suite.
Phase 1 corpus add candidate: the cited March 2026 brevity-improves-accuracy paper (arXiv 2604.00025; +26 accuracy
points on certain benchmarks under brevity constraints).

**Sub-batch 2 — `symphony` repo-note** (`docs/repo-notes/symphony.md`): `openai/symphony`, OpenAI's engineering-preview
harness reframing the human/agent relationship from "supervise the agent while it codes" to "manage the work the
agent does." A long-running daemon polls an issue tracker (Linear in v1; tracker-agnostic SPEC.md), opens isolated
per-issue workspaces, runs coding agents under a repo-owned `WORKFLOW.md` policy file, and produces proof-of-work
artifacts (CI status, PR review feedback, complexity analysis, walkthrough videos). Apache-2.0. Deliverable is unusual:
a 30k-token language-agnostic SPEC.md (RFC 2119 normative language) plus an Elixir reference implementation under
`elixir/`. Slated for `g7-harnesses` (primary cluster) + `agentic-systems-synthesis.md` (primary thematic — the
WORKFLOW.md policy-in-repo idea as the third reference task-spec shape alongside goose Recipe and Letta Agent File).
Verdict: **Watch + Study**. Key reusable patterns: the `WORKFLOW.md` policy-in-repo discipline; the explicit
ID-vocabulary discipline (issue ID for lookups, issue identifier for human logs, workspace key for filesystem,
session ID for telemetry); the workspace-as-first-class concept with deterministic per-task paths and `after_create`
/ `before_remove` hooks; the retry-with-tracker-reconciliation state machine; the structured-logs-required +
status-surface-optional observability discipline; the sample WORKFLOW.md as the SAFETY.md Tier-3 trust-and-safety
reference. Cross-vendor signal: combined with goose (Block/AAIF) and claw-code (Anthropic), symphony confirms the
harness is the layer of public-spec convergence between leading model vendors.

**Sub-batch 3 — `swarm` paired-repo treatment** (`docs/repo-notes/swarm.md` + `docs/paper-notes/swarm-2604.19752.md`):
`swarm-ai-safety/swarm`, the **System-Wide Assessment of Risk in Multi-agent systems** framework paired with the arXiv
2604.19752v1 preprint (Aiersilan & Savitt 2026, 19 Mar 2026 — "Soft-Label Governance for Distributional Safety in
Multi-Agent Systems"). Paired-repo treatment per CLAUDE.md §Paper-note paired-repo variant — paper-note uses the
hybrid filename `swarm-2604.19752.md` with `pdf:` pointing to `../../context/papers/2604.19752v1.pdf` (downloaded from
arxiv 2026-05-16; the swarm artifacts repo does not vendor the preprint). Repo is MIT-licensed Python 3.10+, PyPI
package `swarm-safety`, 23 agent archetypes, 27+ governance levers, 79 YAML scenarios, 39 examples, 4,556 tests across
133 files, 8 framework bridges (Concordia, OpenClaw, GasTown, LiveSWE, Prime Intellect, Ralph, Claude Code, Worktree),
live HF Spaces sandbox. Both notes slated for `g11-agent-frameworks` (primary cluster) +
`safety-alignment-privacy-synthesis.md` (primary thematic — multi-agent / population-level safety as a fifth axis
alongside mechanism / values-characterization / threat-model / design-policy) + `agentic-systems-synthesis.md`
(secondary thematic — population-level framing as complement to the existing competence-focused Kosmos / BioGuider /
Sketch2Simulation thread). Verdict: **Study** for both. Key reusable patterns: soft-label safety metrics
(`p = σ(k·v_hat)` from observable proxy signals → toxicity rate `E[1−p | accepted]` / quality gap
`E[p | accepted] − E[p | rejected]` / conditional loss / incoherence) as the Phase 3 multi-agent safety surface
(DEC-0050, DEC-0052); illusion delta `Δ_illusion = C_perceived − C_distributed` as a Phase 1c+ Worker
distributional-consistency benchmark axis; the five-category governance-lever taxonomy (cost / access / reputation /
detection / deliberative) as the Phase 3 spawner-spec safety vocabulary; the seven canonical scenarios as the
adversarial-pressure stress-test design reference; the `swarm/bridges/openclaw/` integration as the Phase 5+ Linus +
openclaw safety-measurement design reference; the calibration-discipline note (proxy-to-probability requires
empirical calibration against human-labeled ground truth before metric values are trustworthy) as a Phase 3 ADR
prerequisite; the **safety-trained paradox** finding (cautious safety prompts scored marginally higher on heuristic
toxicity because the scorer penalized cooperation-refusal) as a "measure what you mean" SAFETY.md cautionary tale; the
**`Extend, don't proliferate`** CLAUDE.md convention candidate from the swarm CLAUDE.md.

**Source review:** Wave 2 stragglers v1 dispatch, 2026-05-16 (this session). PR opened from `agent/wave2-stragglers`;
commits atomic per artifact (one for caveman repo-note, one for symphony repo-note, one for swarm repo-note, one for
the SWARM paper-note, one for INDEX backfill + synthesis edits + this curation-log entry). Sibling W2 batch
(`agent/wave2-stragglers-v2`) carries pi repo-note + two non-overlapping paper-notes; this v1 batch is strictly
non-overlapping per the dispatch coordination.
