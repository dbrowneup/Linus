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
