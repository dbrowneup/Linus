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
