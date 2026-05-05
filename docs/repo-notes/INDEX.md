# Repo Notes Index

Flat lookup table from each per-repo note in [`docs/repo-notes/`](../repo-notes/) to the cluster synthesis it sits
under (`g1`–`g10`, post-fan-out) and the thematic syntheses that cite it.

This is a navigation aid, not analysis. The cluster synthesis is where the within-cluster patterns and integrate/study/
ignore verdicts live; thematic syntheses cite individual repos as worked examples or counter-examples. The per-repo
note is where the verdict is justified, the architecture is described, and the open questions for Dan land.

The pre-fan-out core (12 repos: pmetal, mlx-flash, flash-moe, ANE, Bonsai-demo, BitNet, claw-code-local, claw-code,
cline, openclaw, autoresearch, project-nomad) does not have a `g`-cluster — those repos predate the Section 7 fan-out
and were already integrated into the original `repo-landscape.md` and the relevant thematic syntheses directly.

`project-nomad` is uncovered by either substrate. It lives at the per-repo-note + landscape level only — by design,
since it is a component catalog reference rather than a code integration target.

## How to read the table

- **Repo note**: link to the file in `repo-notes/`.
- **Cluster**: the `g1`–`g10` cluster synthesis for post-fan-out repos; `—` for the pre-fan-out core.
- **Thematic syntheses**: comma-separated, links to `docs/syntheses/<name>-synthesis.md`.

---

| Repo note | Cluster | Thematic syntheses |
| --- | --- | --- |
| [`agentic-wiki-builder`](../repo-notes/agentic-wiki-builder.md) | [g3-wiki-patterns](../syntheses/repo-clusters/g3-wiki-patterns.md) |  |
| [`AgenticResearchWiki`](../repo-notes/AgenticResearchWiki.md) | [g3-wiki-patterns](../syntheses/repo-clusters/g3-wiki-patterns.md) |  |
| [`agentmemory`](../repo-notes/agentmemory.md) | [g4-memory](../syntheses/repo-clusters/g4-memory.md) | [llm-wiki](../syntheses/llm-wiki-synthesis.md) |
| [`anamnesis`](../repo-notes/anamnesis.md) | [g4-memory](../syntheses/repo-clusters/g4-memory.md) |  |
| [`ANE`](../repo-notes/ANE.md) | — | [llm-wiki](../syntheses/llm-wiki-synthesis.md), [native-low-bit-apple-silicon](../syntheses/native-low-bit-apple-silicon-synthesis.md) |
| [`atomic-knowledge`](../repo-notes/atomic-knowledge.md) | [g3-wiki-patterns](../syntheses/repo-clusters/g3-wiki-patterns.md) |  |
| [`autoresearch-mlx`](../repo-notes/autoresearch-mlx.md) | [g1-apple-silicon](../syntheses/repo-clusters/g1-apple-silicon.md) | [llm-wiki](../syntheses/llm-wiki-synthesis.md), [skills-and-practices](../syntheses/skills-and-practices-synthesis.md) |
| [`autoresearch`](../repo-notes/autoresearch.md) | — | [llm-wiki](../syntheses/llm-wiki-synthesis.md), [skills-and-practices](../syntheses/skills-and-practices-synthesis.md) |
| [`aviary`](../repo-notes/aviary.md) | [g8-sci-agents](../syntheses/repo-clusters/g8-sci-agents.md) |  |
| [`Bacformer`](../repo-notes/Bacformer.md) | [g9-bio](../syntheses/repo-clusters/g9-bio.md) |  |
| [`beever-atlas`](../repo-notes/beever-atlas.md) | [g3-wiki-patterns](../syntheses/repo-clusters/g3-wiki-patterns.md) |  |
| [`BioReason`](../repo-notes/BioReason.md) | [g9-bio](../syntheses/repo-clusters/g9-bio.md) | [function-annotation-discovery](../syntheses/function-annotation-discovery-synthesis.md) |
| [`bioSkills`](../repo-notes/bioSkills.md) | [g9-bio](../syntheses/repo-clusters/g9-bio.md) |  |
| [`BitNet`](../repo-notes/BitNet.md) | — | [native-low-bit-apple-silicon](../syntheses/native-low-bit-apple-silicon-synthesis.md) |
| [`BixBench`](../repo-notes/BixBench.md) | [g8-sci-agents](../syntheses/repo-clusters/g8-sci-agents.md) | [function-annotation-discovery](../syntheses/function-annotation-discovery-synthesis.md) |
| [`Bonsai-demo`](../repo-notes/Bonsai-demo.md) | — | [native-low-bit-apple-silicon](../syntheses/native-low-bit-apple-silicon-synthesis.md) |
| [`claude-prism`](../repo-notes/claude-prism.md) | [g8-sci-agents](../syntheses/repo-clusters/g8-sci-agents.md) |  |
| [`claude-squad`](../repo-notes/claude-squad.md) | [g7-harnesses](../syntheses/repo-clusters/g7-harnesses.md) |  |
| [`claude-task-master`](../repo-notes/claude-task-master.md) | [g7-harnesses](../syntheses/repo-clusters/g7-harnesses.md) |  |
| [`claw-code-local`](../repo-notes/claw-code-local.md) | — | [skills-and-practices](../syntheses/skills-and-practices-synthesis.md) |
| [`claw-code`](../repo-notes/claw-code.md) | — | [skills-and-practices](../syntheses/skills-and-practices-synthesis.md) |
| [`cline`](../repo-notes/cline.md) | — | [skills-and-practices](../syntheses/skills-and-practices-synthesis.md) |
| [`codebuff`](../repo-notes/codebuff.md) | [g7-harnesses](../syntheses/repo-clusters/g7-harnesses.md) |  |
| [`codesight`](../repo-notes/codesight.md) | [g6-mcp-tools](../syntheses/repo-clusters/g6-mcp-tools.md) |  |
| [`deepsems`](../repo-notes/deepsems.md) | [g9-bio](../syntheses/repo-clusters/g9-bio.md) |  |
| [`dexter`](../repo-notes/dexter.md) | [g10-finance](../syntheses/repo-clusters/g10-finance.md) |  |
| [`engram`](../repo-notes/engram.md) | [g4-memory](../syntheses/repo-clusters/g4-memory.md) |  |
| [`ether0`](../repo-notes/ether0.md) | [g8-sci-agents](../syntheses/repo-clusters/g8-sci-agents.md) |  |
| [`fastmcp`](../repo-notes/fastmcp.md) | [g6-mcp-tools](../syntheses/repo-clusters/g6-mcp-tools.md) |  |
| [`finch`](../repo-notes/finch.md) | [g8-sci-agents](../syntheses/repo-clusters/g8-sci-agents.md) |  |
| [`flash-moe`](../repo-notes/flash-moe.md) | — | [infra-foundations](../syntheses/infra-foundations-synthesis.md), [llm-wiki](../syntheses/llm-wiki-synthesis.md) |
| [`gravityfile`](../repo-notes/gravityfile.md) | [g7-harnesses](../syntheses/repo-clusters/g7-harnesses.md) |  |
| [`hyalo`](../repo-notes/hyalo.md) | [g5-graph-tools](../syntheses/repo-clusters/g5-graph-tools.md) |  |
| [`ibmdotcom-tutorials`](../repo-notes/ibmdotcom-tutorials.md) | [g8-sci-agents](../syntheses/repo-clusters/g8-sci-agents.md) |  |
| [`infranodus-skills`](../repo-notes/infranodus-skills.md) | [g5-graph-tools](../syntheses/repo-clusters/g5-graph-tools.md) |  |
| [`infranodus`](../repo-notes/infranodus.md) | [g5-graph-tools](../syntheses/repo-clusters/g5-graph-tools.md) |  |
| [`keppi`](../repo-notes/keppi.md) | [g5-graph-tools](../syntheses/repo-clusters/g5-graph-tools.md) | [llm-wiki](../syntheses/llm-wiki-synthesis.md) |
| [`LAB-Bench`](../repo-notes/LAB-Bench.md) | [g8-sci-agents](../syntheses/repo-clusters/g8-sci-agents.md) | [function-annotation-discovery](../syntheses/function-annotation-discovery-synthesis.md) |
| [`ldp`](../repo-notes/ldp.md) | [g8-sci-agents](../syntheses/repo-clusters/g8-sci-agents.md) |  |
| [`link`](../repo-notes/link.md) | [g2-wiki-engines](../syntheses/repo-clusters/g2-wiki-engines.md) |  |
| [`llm-research-wiki`](../repo-notes/llm-research-wiki.md) | [g3-wiki-patterns](../syntheses/repo-clusters/g3-wiki-patterns.md) |  |
| [`llm-wikidata`](../repo-notes/llm-wikidata.md) | [g3-wiki-patterns](../syntheses/repo-clusters/g3-wiki-patterns.md) |  |
| [`llmbase`](../repo-notes/llmbase.md) | [g2-wiki-engines](../syntheses/repo-clusters/g2-wiki-engines.md) |  |
| [`llmwiki-cli`](../repo-notes/llmwiki-cli.md) | [g2-wiki-engines](../syntheses/repo-clusters/g2-wiki-engines.md) |  |
| [`llmwiki`](../repo-notes/llmwiki.md) | [g2-wiki-engines](../syntheses/repo-clusters/g2-wiki-engines.md) |  |
| [`memex`](../repo-notes/memex.md) | [g4-memory](../syntheses/repo-clusters/g4-memory.md) |  |
| [`mlx-flash`](../repo-notes/mlx-flash.md) | — | [infra-foundations](../syntheses/infra-foundations-synthesis.md), [native-low-bit-apple-silicon](../syntheses/native-low-bit-apple-silicon-synthesis.md) |
| [`nixtla`](../repo-notes/nixtla.md) | [g10-finance](../syntheses/repo-clusters/g10-finance.md) |  |
| [`obsidian-llm-wiki-local`](../repo-notes/obsidian-llm-wiki-local.md) | [g3-wiki-patterns](../syntheses/repo-clusters/g3-wiki-patterns.md) |  |
| [`omega-memory`](../repo-notes/omega-memory.md) | [g4-memory](../syntheses/repo-clusters/g4-memory.md) | [llm-wiki](../syntheses/llm-wiki-synthesis.md) |
| [`OmegaWiki`](../repo-notes/OmegaWiki.md) | [g2-wiki-engines](../syntheses/repo-clusters/g2-wiki-engines.md) |  |
| [`ontomics`](../repo-notes/ontomics.md) | [g6-mcp-tools](../syntheses/repo-clusters/g6-mcp-tools.md) |  |
| [`openaugi`](../repo-notes/openaugi.md) | [g4-memory](../syntheses/repo-clusters/g4-memory.md) | [llm-wiki](../syntheses/llm-wiki-synthesis.md) |
| [`OpenBB`](../repo-notes/OpenBB.md) | [g10-finance](../syntheses/repo-clusters/g10-finance.md) |  |
| [`openclaw`](../repo-notes/openclaw.md) | — | [skills-and-practices](../syntheses/skills-and-practices-synthesis.md) |
| [`openrouter-skills`](../repo-notes/openrouter-skills.md) | [g7-harnesses](../syntheses/repo-clusters/g7-harnesses.md) |  |
| [`origin`](../repo-notes/origin.md) | [g7-harnesses](../syntheses/repo-clusters/g7-harnesses.md) |  |
| [`paper-qa`](../repo-notes/paper-qa.md) | [g8-sci-agents](../syntheses/repo-clusters/g8-sci-agents.md) |  |
| [`pmetal`](../repo-notes/pmetal.md) | — | [native-low-bit-apple-silicon](../syntheses/native-low-bit-apple-silicon-synthesis.md) |
| [`project-nomad`](../repo-notes/project-nomad.md) | — |  |
| [`prompt-vault`](../repo-notes/prompt-vault.md) | [g4-memory](../syntheses/repo-clusters/g4-memory.md) |  |
| [`py3plex`](../repo-notes/py3plex.md) | [g5-graph-tools](../syntheses/repo-clusters/g5-graph-tools.md) |  |
| [`python-sdk`](../repo-notes/python-sdk.md) | [g7-harnesses](../syntheses/repo-clusters/g7-harnesses.md) |  |
| [`qmd`](../repo-notes/qmd.md) | [g6-mcp-tools](../syntheses/repo-clusters/g6-mcp-tools.md) | [llm-wiki](../syntheses/llm-wiki-synthesis.md) |
| [`QuantAgent`](../repo-notes/QuantAgent.md) | [g10-finance](../syntheses/repo-clusters/g10-finance.md) | [agentic-systems](../syntheses/agentic-systems-synthesis.md) |
| [`remember`](../repo-notes/remember.md) | [g4-memory](../syntheses/repo-clusters/g4-memory.md) |  |
| [`robin`](../repo-notes/robin.md) | [g8-sci-agents](../syntheses/repo-clusters/g8-sci-agents.md) |  |
| [`scientific-agent-skills`](../repo-notes/scientific-agent-skills.md) | [g8-sci-agents](../syntheses/repo-clusters/g8-sci-agents.md) |  |
| [`semanticworkbench`](../repo-notes/semanticworkbench.md) | [g7-harnesses](../syntheses/repo-clusters/g7-harnesses.md) |  |
| [`swarmvault`](../repo-notes/swarmvault.md) | [g2-wiki-engines](../syntheses/repo-clusters/g2-wiki-engines.md) |  |
| [`synthadoc`](../repo-notes/synthadoc.md) | [g2-wiki-engines](../syntheses/repo-clusters/g2-wiki-engines.md) |  |
| [`TheKnowledge`](../repo-notes/TheKnowledge.md) | [g2-wiki-engines](../syntheses/repo-clusters/g2-wiki-engines.md) |  |
| [`TradingAgents`](../repo-notes/TradingAgents.md) | [g10-finance](../syntheses/repo-clusters/g10-finance.md) | [agentic-systems](../syntheses/agentic-systems-synthesis.md) |
| [`vectorless`](../repo-notes/vectorless.md) | [g6-mcp-tools](../syntheses/repo-clusters/g6-mcp-tools.md) |  |
| [`WeKnora`](../repo-notes/WeKnora.md) | [g6-mcp-tools](../syntheses/repo-clusters/g6-mcp-tools.md) |  |
| [`wikidesk`](../repo-notes/wikidesk.md) | [g2-wiki-engines](../syntheses/repo-clusters/g2-wiki-engines.md) |  |
| [`wikiloom`](../repo-notes/wikiloom.md) | [g2-wiki-engines](../syntheses/repo-clusters/g2-wiki-engines.md) |  |
| [`wikimind`](../repo-notes/wikimind.md) | [g2-wiki-engines](../syntheses/repo-clusters/g2-wiki-engines.md) |  |
| [`workgraph`](../repo-notes/workgraph.md) | [g7-harnesses](../syntheses/repo-clusters/g7-harnesses.md) |  |
