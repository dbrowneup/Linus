# infranodus-skills (`infranodus/skills`)

## 1. Purpose and scope

`infranodus-skills` is a collection of fifteen Anthropic-format Skills (`SKILL.md` + frontmatter `name`/`description`,
plus optional `references/`) authored by the InfraNodus team. The skills package the "cognitive variability" framework —
the four-state circulation between BIASED, FOCUSED, DIVERSIFIED, and DISPERSED knowledge-graph topologies that
InfraNodus measures via modularity and betweenness centrality — into prompt-only behaviors that any LLM client
supporting the Skills standard (Claude Web, Claude Code, Cursor, OpenClaw) can load. Several skills are pure
prompt-engineering and run standalone; others reach back to the hosted **InfraNodus MCP server** (`mcp.infranodus.com`,
authed via `INFRANODUS_API_KEY` Bearer token) for actual graph analysis, content-gap detection, GraphRAG retrieval, and
SEO/SERP import. For Linus this sits at the intersection of Group 5 (KG/network tooling, relevant to Phase 2 KB graph
DEC-0026/27 and Phase 3 hybrid retrieval) and Phase 7 Skills graduation.

## 2. Content overview

Fifteen skill folders ship in the repo: **cognitive-variability**, **critical-perspective**, **writing-assistant**,
**ontology-creator**, **seo-analysis**, **viral-videos** (YouTube optimizer), **shopping**, **rhetorical-analyst**,
**shifting-perspective**, **perspective-reversal**, **embodied-navigation**, **vipassana-meditation** (Vipassana for
LLMs), **llm-wiki** (Karpathy's LLM Wiki proposal as a guided scaffold), **actionize** (plan + Telegram-cron reminders),
and **infranodus-cli** (the catch-all reference for all InfraNodus MCP tools, intended to be pasted into clients without
native MCP support). Each is a single `SKILL.md` between ~120 and ~870 lines, frontmatter-prefixed in the standard
Skills format. The largest two — `cognitive-variability` (826 lines) and `llm-wiki` (867 lines) — are substantial
prompt-engineering documents; the smallest like `critical-perspective` (122 lines) are concise behavioral shims. The
`infranodus-cli` skill includes a `references/tool-examples.md` and frontmatter declaring `requires.bins: ["mcporter"]`
and `primaryEnv: INFRANODUS_API_KEY` — making the SaaS dependency explicit and machine-readable for OpenClaw's
installer. A GitHub Action auto-builds `.zip`/`.skill` bundles on tag push for one-click upload to Claude Web/Desktop.

## 3. What's reusable in Linus

Two things are directly useful. First, the **format itself**: the repo is a clean, real-world reference for the
Anthropic Skills standard (frontmatter + SKILL.md + optional `references/`), and Phase 7's "Skills & Autonomy
Graduation" needs exactly this shape for Linus's domain skills (genomics pipelines, paper triage, KB operations). The
`infranodus-cli` skill in particular is a useful prior-art example of how to encode external-tool dependencies in
frontmatter so a harness can self-install prerequisites — relevant for any Linus skill that wraps a CLI binary or MCP
server. Second, two of the standalone (no-MCP) skills are immediately useful as Worker-side cognitive primitives:
`critical-perspective` and `cognitive-variability`'s framework documentation can be loaded into a Worker's system prompt
during Maestro/Worker review loops to stress-test plans for blind spots and stuck-state detection — they are pure prompt
content with no runtime dependencies.

## 4. What's inspiration only

Compared to the parent **`infranodus`** repo (Group 5 sibling, the actual text-network-analysis engine: Node.js + force
graph + Neo4j + the modularity/betweenness math), this repo is a thin behavioral wrapper — it tells an LLM how to talk
about graph-shaped reasoning but does none of the graph computation itself. Compared to the other Skills-format
collection in the repo set (`OmegaWiki`, 24 skills oriented around wiki-style knowledge curation), `infranodus-skills`
trades breadth of generic utility for depth in a single conceptual framework: every skill — even `shopping` and
`viral-videos` — is animated by the same four-state cognitive-variability/structural-gap vocabulary. That uniformity is
the differentiator and also the limit; the framework is interesting but speculative, and the embodied-navigation /
vipassana-for-LLMs / cognitive-variability triad is closer to philosophy-of-mind essays than to deployable engineering
behavior. Worth reading once for the gap-as-creativity insight; not worth shipping wholesale into a scientific
assistant.

## 5. What's incompatible or out of scope

The MCP-dependent skills — `seo-analysis`, `shifting-perspective`, `embodied-navigation`, `actionize`, `infranodus-cli`,
plus the optional MCP paths inside `cognitive-variability`, `viral-videos`, and `perspective-reversal` — all require
either an `INFRANODUS_API_KEY` against the hosted SaaS (`mcp.infranodus.com`) or running `mcporter` against it. There is
no self-hostable InfraNodus MCP backend in this repo; the analysis lives on InfraNodus's servers. That is a hard
collision with Linus's "no paid APIs required for operation" north star and with Phase 4 data sovereignty. The free tier
handles "the first few iterations," which is fine for evaluation but not for production. The SEO/YouTube/shopping skills
are also commercially-flavored and orthogonal to Dan's scientific workload. The Telegram-cron reminders in `actionize`
are a specific external dependency unlikely to fit Linus's loop.

## 6. Recommendation: **Study**

Vendor nothing. Treat this repo as a reference implementation of the Anthropic Skills standard while Phase 7 design work
happens, and as a useful comparison point against `OmegaWiki`'s 24 skills when picking a house style for Linus skills.
Optionally, copy the two pure-prompt skills (`critical-perspective`, `cognitive-variability`) into `~/.claude/skills/`
for personal use during Maestro work — they're harmless prompt content and the variability framework is genuinely
interesting. Do not adopt the InfraNodus-MCP-dependent skills inside Linus until and unless an InfraNodus-equivalent (or
InfraNodus-compatible) graph backend can be self-hosted on Apple Silicon — which is a non-trivial build, not a checkbox.
Revisit during Phase 7 if a local text-network-analysis component lands as part of the Phase 2 KB graph work
(DEC-0026/27).

## 7. Questions for Dan

- **Skills format as the Phase 7 contract.** Both this repo and `OmegaWiki` use the Anthropic SKILL.md format with
  frontmatter `name`/`description`/optional `allowed-tools`. Should Linus commit to that exact format for its Phase 7
  domain skills, or define a Linus-specific superset (e.g., adding hardware/budget hints, mandatory smoke-test stubs)?
- **Cognitive-variability framework — useful or noise?** The four-state model (biased/focused/diversified/dispersed)
  maps interestingly onto Maestro/Worker review loops: a Worker stuck in BIASED could be nudged toward DIVERSIFIED by
  loading `critical-perspective`. Worth a Phase 1e experiment, or filed under "interesting but not load-bearing"?
- **Self-hostable text-network analysis.** If we want the MCP-dependent skills to work standalone, we'd need to
  reimplement InfraNodus's modularity/centrality/gap-detection over our own KB graph (Phase 2 DEC-0026/27 surface).
  That's a meaningful build. Worth scoping into Phase 3, or accept that this repo stays study-only?
- **OmegaWiki comparison.** I could not find an `OmegaWiki.md` repo note in `docs/repo-notes/` (only the twelve listed
  there) — was it intended to be authored separately, or is the comparison expected to live here in absentia? If the
  former, the head-to-head should probably be revisited once both notes exist.
- **`llm-wiki` skill vs Karpathy's autoresearch.** The `llm-wiki` skill operationalizes Karpathy's LLM Wiki proposal as
  a setup workflow, which is a near-cousin of the autoresearch loop already cloned in `repos/autoresearch/`. Is there
  appetite to consolidate these into a single Linus "build a wiki from your sources" skill backed by KnowledgeBase, or
  do they stay separate study artifacts?
