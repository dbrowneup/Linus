# OmegaWiki (`skyllwt/OmegaWiki`)

## 1. Purpose and scope

OmegaWiki (stylized ΩmegaWiki) is a Karpathy-LLM-Wiki implementation from PKU's DAIR Lab that consciously stretches the
pattern from "build a knowledge wiki" into a full research-lifecycle platform: paper ingestion, knowledge graph, gap
detection, idea generation, novelty checking, experiment design and execution (local or remote GPU), claim tracking,
paper drafting, LaTeX compilation, and reviewer-rebuttal generation. The wiki is the single source of truth; every
operation reads and writes to it. The implementation is delivered as **24 Claude Code slash-command skills** plus a
fleet of deterministic Python helpers under `tools/`, an MCP server for cross-model adversarial review, and a GitHub
Actions cron that ingests new arXiv papers daily. Bilingual (EN / ZH). Within Group 2 of the LLM-Wiki cluster this is
the maximalist entry — the other ten siblings stop at "build and maintain the wiki"; OmegaWiki keeps going until the
output is a submitted paper and a rebuttal.

## 2. Architecture summary

The product surface is `wiki/` — nine entity types (`papers`, `concepts`, `topics`, `people`, `ideas`, `experiments`,
`claims`, `Summary`, `foundations`) stored as Obsidian-compatible Markdown with `[[wikilink]]` cross-references and a
strict bidirectional-link rule enforced by `/check`. Derived state lives in `wiki/graph/`: `edges.jsonl` (typed semantic
edges with confidence levels), `citations.jsonl` (bibliographic), `context_brief.md`, and `open_questions.md`, all
rebuilt via `tools/research_wiki.py` (the "wiki engine" with ~20 CLI subcommands). Skills live under
`.claude/skills/<skill>/SKILL.md` with optional `references/` subfolders that the skill itself decides when to load —
the same on-demand-context pattern Anthropic ships in its own Skills examples. Inputs flow through `raw/` (`papers/`,
`notes/`, `web/`, plus tool-managed `discovered/` and `tmp/`). The `mcp-servers/llm-review/` MCP server exposes any
OpenAI-compatible second model (DeepSeek, Qwen, OpenAI, OpenRouter…) as an adversarial reviewer that `/review`,
`/novelty`, and `/refine` call into. Runtime is Claude Code itself — README documents env-var recipes for pointing
Claude Code at MiMo / DeepSeek / Kimi / GLM Anthropic-protocol endpoints, so the project assumes (but does not require)
the Anthropic-API surface and a hosted frontier model. Python 3.9+, Node 18+, MIT license. Lean runtime deps (`PyMuPDF`,
`feedparser`, `requests`, `markdownify`, `chardet`, `deepxiv-sdk`).

## 3. What's reusable in Linus

The skill catalogue is the most directly relevant artifact for Linus's Phase 7 graduation. Each skill is a real
`SKILL.md` written to the Anthropic Skills standard — `description`, `argument-hint`, on-demand `references/`, explicit
Reads/Writes, deterministic-tool-vs-LLM split. That's the same shape Linus needs for its own research, ingestion, and
KB-query skills, and it's strictly better study material than any of the simpler siblings because the breadth forces the
authors to confront questions Linus will hit (manifest-driven multi-skill handoff via `.checkpoints/init-sources.json`;
"user-owned vs derived" parameter discipline; tex-priority fallback chains). The wiki schema itself — particularly the
claims / experiments / ideas trio with `failure_reason` as "anti-repetition memory" — is a clean answer to "what should
Linus's KnowledgeBase store beyond paper chunks?" and maps onto the Phase 2 KB pillar with very little translation.
`tools/research_wiki.py`, `tools/lint.py`, and `tools/_env.py` are small enough to read end-to-end and would be
reasonable references for a Linus-side wiki engine should Dan want one. The cross-model-review MCP server is a working
template for "Linus exposes a worker model as an MCP tool that Claude Code can call."

## 4. What's inspiration only

The compared-to-siblings differentiation: where `llmwiki`, `llmbase`, and `wikiloom` (Group 2 peers) implement the core
pattern of "ingest paper, maintain wiki," OmegaWiki carries that wiki straight through to LaTeX submission and reviewer
rebuttal. The downstream half — `/exp-run`, `/exp-status`, `/paper-plan`, `/paper-draft`, `/paper-compile`, `/rebuttal`,
the GitHub-Actions arXiv cron — is real code, not vapor, but it is opinionated toward ML-research workflows
(NeurIPS/ICML LaTeX, remote-GPU experiments via `ssh`/`rsync`/`screen`) that don't map onto Dan's
biochemistry-and-software workflow. So the breadth is real, not aspirational, but most of the breadth is for someone
else's job. The lifecycle framing and the failed-experiment / claim-confidence machinery are inspirational; the specific
pipe from `/exp-run` to a remote GPU box is not Linus's path.

## 5. What's incompatible or out of scope

OmegaWiki is fundamentally a **Claude-Code-hosted** application — the README's "Powered by Claude Code" badge is
literal. The runtime assumes Anthropic-protocol API access (Anthropic, or one of the routed Anthropic-compatible
endpoints from MiMo / DeepSeek / Kimi / GLM); it does not target Ollama or pmetal-serve, and there is no local-inference
path. That makes it the inverse of Linus's design intent: Linus wants the orchestration layer to front local workers,
not to be a payload on top of a hosted Maestro. Wholesale adoption would re-couple Linus to Anthropic billing, which
violates the "no paid APIs required for operation" north-star clause. The wiki engine and skill definitions are
extractable; the Claude-Code hosting model is not. The bilingual (EN/ZH) `i18n/` machinery and the WeChat community are
scope ornaments — useful signal that the project is real and maintained, but not load-bearing for Linus.

## 6. Recommendation: **Study**

Mine this aggressively as Phase 7 reference material — particularly the 24 `SKILL.md` files, the wiki schema, the
bidirectional-link enforcement rules, the cross-model-review MCP server, and the manifest-driven init handoff. Do not
vendor it; do not try to retarget it onto Ollama. When Linus reaches the point of designing its own skill catalogue,
treat OmegaWiki as the worked example of "what 24 well-scoped skills look like" and the four simpler-sibling repos as
the worked example of "what the minimum looks like." The delta between them is roughly the shape of Phase 7's planning
surface.

## 7. Questions for Dan

1. **Claim / experiment / idea entities in KnowledgeBase v1.** OmegaWiki's wiki schema treats `claims`, `experiments`,
   `ideas`, and `failure_reason` as first-class. Should Phase 2 KB adopt that vocabulary now (cheap while the schema is
   still soft) or stay paper-centric until a real research workflow forces the question?
2. **Adversarial-review MCP pattern.** The `mcp-servers/llm-review/` model — a second LLM as an MCP-exposed reviewer for
   novelty / refinement / draft critique — is the cleanest "two-model adversarial loop" template in the cluster. Worth
   building an analogous Linus MCP that exposes a worker model to Claude Code as a reviewer? Phase 3 fits.
3. **Differentiator confidence.** The "24 skills, full lifecycle" claim is real (counted: 24 skill directories under
   `.claude/skills/`, plus `shared-references/`). Sibling-by-sibling I haven't yet confirmed whether `wikiloom` or
   `TheKnowledge` reach into experiment design or paper drafting; if any of them do, OmegaWiki's "most ambitious"
   framing softens. Want me to flag that as a follow-up audit before drawing Phase 7 conclusions?
4. **Hosted-Claude dependency as a benchmark control.** Because OmegaWiki only works under Claude Code, it is also a
   natural Maestro-side benchmark target — "what does the lifecycle look like with frontier models, against which
   Linus's local-worker version is measured." Worth designating as a Phase 1b / Phase 7 reference baseline?
