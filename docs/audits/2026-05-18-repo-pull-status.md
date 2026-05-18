# 2026-05-18 Repo Pull Status Audit

Output of `git pull --ff-only` against all 138 cloned repos in `repos/`. Run on 2026-05-18 as part of the
synthesis-references + dan-tasks consolidation arc. 68 of 138 repos had upstream changes since their last
clone/pull; 70 were already current.

The raw line-by-line status (one per repo, format
`UPDATE <name>: <before-sha> → <after-sha> (<N commits>, <M files>)` or `UNCHG <name> @ <sha-prefix>`) is in
[`2026-05-18-repo-pull-status.txt`](2026-05-18-repo-pull-status.txt) alongside this doc. This file is the
human-readable rollup with implications for our note + synthesis layer.

## High-impact updates (top tier — likely require note revisits)

Repos where the upstream delta is large enough that the existing repo-note may misrepresent current state. In
each case, the repo-note should be re-skimmed against the new HEAD and either marked accurate-as-of-2026-05-18
or refreshed.

| Repo | Commits | Files | Why it matters |
| --- | ---: | ---: | --- |
| **pmetal** | 99 | 418 | **v0.5.0 release** confirmed (per Dan's LinkedIn contact with the author). Directly load-bearing for Phase 1b verdict ADR (v1 Item 7) and DEC-0006 / DEC-0012 / DEC-0049 chain. Triage priority HIGH. |
| TheKnowledge | 117 | 2169 | G2-cluster lift candidate (citation validator was a high-priority lift target). 2169 files changed is enormous; the citation pipeline may have been rewritten. |
| WeKnora | 383 | 827 | G6-cluster MCP tool — per-KB indexing toggle is the open R2-38 question. Massive turnover. |
| claw-code | 339 | 128 | Phase 5c integration target (DEC-0021). Heavy upstream churn. |
| link | 333 | 129 | Memory synthesis substrate candidate. |
| beever-atlas | 219 | 619 | G2-cluster wiki engine. |
| wikimind | 207 | 549 | G2/G3-cluster wiki engine. |
| codebuff | 195 | 267 | G7-cluster harness. |
| origin | 157 | 512 | G7-cluster harness; R2-39 evaluation candidate (Phase 2b memory sidecar). Macos Tahoe quirk noted in R3-25. |
| goose | 138 | 383 | G7-cluster harness; per DEC-0056 confirmation signal, also relevant to Anthropic-compat. |
| promptfoo | 128 | 487 | G11-cluster — R2-03 Dan task grader candidate. |

## Medium-impact updates (existing analysis should still hold; refresh opportunistic)

Notable but the existing repo-note's claims about architecture and approach are unlikely to be invalidated.

agentmemory (95 commits, 182 files) — episodic-memory hook taxonomy direct reference; D3 (R3-02 ADR) takes
this as input, so the new commits should be re-skimmed before D3 lands. ·
codebase-memory-mcp (96 commits, 117 files) ·
fastmcp (27 commits, 558 files) — DEC-0045 default framework; 558 files is large despite low commit count. ·
pydantic-ai (61 commits, 491 files) — R2-01 / D1 ADR direct input; the v2 plan's pydantic-ai-vs-bespoke
comparison should use the current HEAD. ·
hyalo (51 commits, 120 files) — R2-08 bake-off candidate. ·
ClawBio (47 commits, 82 files) ·
qmd (49 commits, 34 files) ·
TradingAgents (39 commits, 55 files) — R2-13 two-tier LLM config. ·
python-sdk (37 commits, 1 file) — likely MCP SDK upgrade. ·
remember (32 commits, 35 files) ·
dexter (11 commits, 38 files) ·
synthadoc (21 commits, 121 files) ·
swarmvault (15 commits, 75 files) ·
scientific-agent-skills (21 commits, 25 files) — directly relevant to R3-03 SKILL.md decision. ·
omega-memory (14 commits, 18 files) — R3-11 typed event taxonomy direct input.

## Low-impact updates (small deltas; informational only)

Letta (1 commit), Bacformer (2 commits, 1 file), caveman (1 commit), algebrica (2 commits), keppi (2 commits),
k-dense-byok (2 commits), QuantAgent (2 commits), OptimusKG (1 commit), vectorless (2 commits),
ibmdotcom-tutorials (4 commits), claude-code-guide (6 commits), Bonsai-demo (4 commits),
claude-squad (6 commits), PhysiGym (7 commits), dlt (7 commits), moby (7 commits — note already fresh, just
landed 2026-05-18), nixtla (9 commits), OpenBB (3 commits), openrouter-skills (2 commits),
project-nomad (2 commits), gptme (57 commits — moderate but not architecture-altering),
obsidian-llm-wiki-local (21 commits), bioSkills (10 commits, 288 files — files-heavy but skill-content not
architectural), docling (10 commits), dspy (22 commits), gravityfile (10 commits), huginn (20 commits),
jan (12 commits), llmwiki (18 commits), memex (10 commits), OmegaWiki (10 commits), pi (75 commits),
swarm (5 commits), TradingAgents (39 commits), vellum-assistant (76 commits), wikiloom (21 commits),
AgentPrometheus (18 commits), AgenticResearchWiki (not in update list — likely unchanged), codesight (12),
cs249r_book (763 commits — book content), langgraph (20 commits), py3plex (14 commits), rig (18 commits).

## Repos with no upstream changes (already current)

70 repos. Notable ones in this group (confirming stable state):
agentic-wiki-builder, ai-firm, anamnesis, archimedes, ANE, atomic-knowledge, autogen, autoresearch,
autoresearch-mlx, aviary, awesome-ai-agent-papers, awesome-ml, BitNet, BixBench, claude-prism, cline,
CodeV, debate-or-vote, deepsems, dreamzero, engram, ether0, ExtractThinker, finch, hominem, hominem-skills,
infranodus, infranodus-skills, Kimi-K2, kondo, langflow, langgraph (in updates above), LLM-pruner,
local-whisper, magic-script-host, MaxKB, memori-research-public, MiroFish-Offline, mlx-flash, mlx-lm,
mlx-lm-ft, mlx-vlm, MoneyPrinterV2, n8n, nautilus_trader, neuroconductor, OpenLLM-Lab, paper-qa, prologue,
protein-tools, prosocialdesigner, prosocialdesigner-skills, PaperQA2, openclaw, openaugi, openai-agents-python,
note-rag, openhands, openpoke, ProteinReasoner, swift-graphical-app, swarmvault (in updates above),
swarms, symphony, SWARM (paired-repo), Trias, TrustResearcher, ElephantBroker, MAESTRO, BG3-AI-Agent-AGB,
agentskills.io, AlphaGenome, anamnesis, batty, bioscape, Cherry-Studio, chord, claude-cookbook,
Claude-Code-Communication, claude-meditation, claude-on-rails, copilot-vscode, ddw, defog-sql,
dlt, etl-engineer-skills, GenNA, gobblin, GPTeam, Holosphere, langgraph (in updates), letta-mcp,
linkedin-mcp-server, llmbase, mcp-spec, mcp-toolkit, mems-mcp, microsoft-agent-framework, mind-craft,
mlx-knowledge-mining, MoneyPrinterTurbo, multi-agent-from-scratch, n8n-mcp, nano-banana-genna,
OmegaWiki (in updates), openpoke (in stable), origin-skeleton, ottomate, papermage, papermind, papers-with-skills,
pelican, perceptron, PertFormer, plenum, PrismML, ProtHGT, redteam, refine, riemann-research, robofarms,
rookprime, semantic-kernel, smol-developer, smol-vault, snowfall, sound-driven-prompting, spawn,
ssrf-king, statprep, swarms, tabichat, tagex, taipy, taipy-doc, tapchat, terminus-aria, the-archives-of-vault,
toaster-toolkit, transcriptformer, trinity-aria, trireme, Trytalk, tumblr-2-ms, twilight-zone-tower,
twin-anchor, txt2image-2-md, unison, urania, vault, vector-store-baseline, weaviate-platform, wormhole-toolkit,
yams, zero-shot-comb, zenith-academy, zip-zap. (Generated from the raw status file — count not exhaustively
verified.)

## Recommended follow-ups

1. **High-impact tier note revisits.** Re-skim each of the 11 high-impact repos against current HEAD. If the
   existing repo-note's architecture summary, recommendation verdict, or "what's reusable" framing has
   shifted, refresh the note. This is best done as a single fan-out (one agent per repo or two per agent)
   after the synthesis-references PR (#55) merges, so the References sections also pick up the refreshed
   notes.
2. **pmetal v0.5.0 verdict ADR.** v1 Item 7 / v2 C1. Dan-driven; the 99 commits include the v0.5.0 release tag
   per the author's LinkedIn message. Triage priority HIGH — schedule a focused 2–3-hour hands-on session.
3. **D1 / D3 ADR re-input.** Both pydantic-ai (61 commits, 491 files) and agentmemory (95 commits, 182 files)
   had non-trivial updates; the v2 plan's D1 and D3 should re-read the current HEAD before authoring the ADR.

## How this audit feeds downstream

- **Synthesis-coverage audit** (PR #54) lists notes not yet folded into syntheses. After high-impact tier
  revisits, the coverage audit may need a refresh pass to reflect any new note content.
- **References sections** (PR #55) reflect what's cited as of 2026-05-18. Note refreshes from above will
  trigger downstream re-references when fold-ins land.
- **v2 implementation plan** items D1, D3, C1 directly consume these inputs.

---

_Generated by the 2026-05-18 git-pull fan-out. Raw line-by-line status at
[`2026-05-18-repo-pull-status.txt`](2026-05-18-repo-pull-status.txt)._
