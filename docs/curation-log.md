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
