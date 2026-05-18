# everything-claude-code (`affaan-m/everything-claude-code`)

## 1. Purpose and scope

Everything Claude Code (ECC; affaan-m/everything-claude-code; MIT; the README advertises 182K+ stars, 28K+ forks, 170+
contributors, "Anthropic Hackathon Winner") bills itself as **"the performance optimization system for AI agent
harnesses"** — a single repository of agents, skills, hooks, rules, MCP configurations, and slash-command shims that
installs into Claude Code (primary), Codex, Cursor, OpenCode, Gemini, Zed, and GitHub Copilot through harness-specific
adapters. The repo's stated position (`docs/architecture/cross-harness.md`) is that **ECC is the reusable workflow
layer; harnesses are execution surfaces**, with skills as the most-portable unit and per-harness adapters limited to
loading, event-shape adaptation, and command mapping. The v2.0.0-rc.1 catalog (per `AGENTS.md` and the v1.10.0 changelog
sync) is **60 agents, 232 skills, 75 slash commands, comprehensive hook system, 14 MCP server configs**, plus a
`legacy-command-shims/` compatibility surface that ECC is actively trying to demote in favor of skills-first
contribution.

The repo carries a substantial commercial wrapper alongside the OSS core. **ECC Pro** ($19/seat/mo) is a hosted GitHub
App (`marketplace/ecc-tools`) running PR audits on private repos. **AgentShield** (`npm:ecc-agentshield`) is a CLI +
GitHub App that scans `.claude/` configs for prompt-injection patterns, hardcoded secrets, permissive allowlists, and
risky MCP servers — a 1282-test, 102-rule analyzer per the v1.6.0 changelog. **Hermes** is a private operator shell the
maintainer runs; ECC's stated architecture explicitly carves out a public/private boundary ("Hermes Boundary" — do not
ship `~/.hermes` exports, OAuth tokens, raw operator memory; do ship sanitized skills the operator distilled). **ECC 2.0
alpha** is in-tree at `ecc2/` as a Rust control-plane (`ecc-tui`) using ratatui + tokio + rusqlite + git2 — alpha, not
GA, exposing `dashboard`, `start`, `sessions`, `status`, `stop`, `resume`, `daemon` subcommands. For Linus, ECC is the
**deepest single reference** for what a mature Claude-Code-shaped skill + hook + agent + MCP ecosystem looks like under
one roof, and simultaneously a worked case study of how a solo OSS maintainer wraps that ecosystem in a sponsorship +
GitHub App + Pro tier without the OSS surface drifting.

## 2. Architecture summary

ECC's top-level layout factors cleanly along its taxonomy. **`agents/`** ships 60 subagent definitions as Markdown with
YAML frontmatter (`name`, `description`, `tools`, `model`) plus a system-prompt body; the canonical example
`code-reviewer.md` declares `tools: ["Read", "Grep", "Glob", "Bash"]` and `model: sonnet`, then carries a
hundreds-of-lines reviewer system prompt covering review process, confidence-based filtering, a pre-report gate, and
language-specific category guidance. Agent files are the most directly liftable artifact in the repo — each is a
self-contained role definition that any harness with a "subagent" notion can adapt by mapping frontmatter to its own
agent-config shape.

**`skills/`** is the canonical workflow surface and the most portable cross-harness unit (per
`docs/architecture/cross-harness.md`). Each skill lives at `skills/<name>/SKILL.md` with frontmatter `name` /
`description` / `origin` and a body structured around "When to Activate," "How It Works," and worked examples. The 232
skills span coding standards (`coding-standards`, `tdd-workflow`, `python-patterns`, `rust-patterns`), agent operations
(`agent-harness-construction`, `agentic-engineering`, `autonomous-agent-harness`, `continuous-learning`,
`continuous-learning-v2`), security (`security-scan`, `security-review`, `security-bounty-hunter`), language patterns
(per-language `*-patterns` / `*-testing` / `*-security` triples for 12+ ecosystems), domain operations
(`customer-billing-ops`, `google-workspace-ops`, `production-scheduling`), and meta-skills (`skill-create`,
`skill-stocktake`, `skill-health`, `skill-scout`, `skill-comply`). A skill like `agent-harness-construction/SKILL.md` is
deliberately small (~75 lines): it defines an "agent output quality is constrained by action space / observation /
recovery / context-budget quality" model and lists granularity rules, observation shape, error-recovery contract,
context-budgeting rules, and anti-patterns — encyclopedia-style guidance the agent loads on demand rather than carrying
in its system prompt. The cross-harness doc names a portable SKILL.md as having YAML frontmatter, a "when to use"
section, required-tools declaration without embedded secrets, repo-relative or generic examples, and labeled
harness-specific sections — i.e. SKILL.md is treated as a typed, validated artifact, not free-form Markdown.

**`hooks/`** is a JSON manifest at `hooks/hooks.json` declaring matchers and commands for Claude Code's `PreToolUse` /
`PostToolUse` / `PreCompact` / `SessionStart` / `Stop` / `PostToolUseFailure` / `SessionEnd` lifecycle points. The hook
entries themselves are heavily-engineered Node bootstrap one-liners that resolve `CLAUDE_PLUGIN_ROOT` across plugin /
marketplace / cache install paths and then delegate to `scripts/hooks/<hook-name>.js` via a `run-with-flags.js` wrapper
that gates execution on `ECC_HOOK_PROFILE` (`minimal` / `standard` / `strict`) and `ECC_DISABLED_HOOKS`. The hook
taxonomy is the genuinely interesting surface: pre-bash dispatcher (quality / tmux / push / GateGuard checks), pre-write
doc-file-warning, pre-edit-write suggest-compact, pre-observe continuous-learning capture, pre-governance-capture (gated
on `ECC_GOVERNANCE_CAPTURE=1`), pre-config-protection (blocks edits to linter / formatter configs to prevent
agent-weakens-rules failure mode), pre-mcp-health-check, pre-edit-write gateguard-fact- force (blocks first edit per
file until investigation), post-quality-gate, post-edit design-quality-check (warns on generic-template UI drift),
post-edit accumulator (batches files for Stop-time formatting), post-edit console-warn, post-governance-capture,
post-session-activity-tracker, post-observe (continuous-learning result capture), post-ecc-metrics-bridge,
post-ecc-context-monitor (warns on context exhaustion / high cost / scope creep / tool loops), post-tool-failure
mcp-health-check, stop format+typecheck, stop check-console-log, stop session-end, stop evaluate-session (extract
patterns), stop cost-tracker, stop desktop-notify, session-end marker. The PreCompact + SessionStart pair implements
memory persistence across compactions; the Stop hook chain implements continuous learning by extracting reusable skill
candidates from each session. The hook profile system (`minimal` / `standard` / `strict`) is the runtime-cost lever:
users dial how much enforcement they want without editing the manifest.

**`mcp-configs/mcp-servers.json`** is a 14+ entry reference catalog of MCP server configurations — Jira, GitHub,
Firecrawl, Supabase, memory, omega-memory, longhand (session-history MCP backed by SQLite + ChromaDB), sequential-
thinking, Vercel, Railway, Cloudflare (4 separate MCP endpoints — docs, workers-builds, workers-bindings,
observability), ClickHouse, Exa web-search, Context7 (live docs), filesystem, Playwright, fal-ai, Browserbase,
browser-use, devfleet (multi-agent orchestration via parallel worktrees), token-optimizer, evalview (regression
testing), and more. Each entry declares command + args + env or HTTP URL, with `_comments` capturing the "keep under 10
MCPs enabled to preserve context window" guidance and `ECC_DISABLED_MCPS` for runtime disabling.

**`rules/`** ships always-follow guidelines structured as `common/` plus per-language directories (TypeScript, Python,
Go, Java, Kotlin, Rust, C++, C#, Swift, Perl, PHP) with each language pack carrying coding-style, patterns, testing, and
security files. The README is explicit that **Claude Code plugins cannot distribute `rules` automatically** — users copy
`rules/common` plus the language packs they want under `~/.claude/rules/ecc/` manually. This is the
plugin-distribution-limit footnote that shapes ECC's "pick one install path" guidance.

**`commands/`** has 75 slash commands (one Markdown file per command with frontmatter `description:`) covering core
workflow (`/plan`, `/tdd`, `/code-review`, `/build-fix`, `/verify`, `/quality-gate`), testing (`/e2e`, `/test-coverage`,
language-specific `/go-test`, `/rust-test`, `/kotlin-test`, `/cpp-test`), code review (`/python-review`, `/go-review`,
`/rust-review` etc.), planning (`/multi-plan`, `/multi-workflow`, `/orchestrate`, `/devfleet`), session management
(`/save-session`, `/resume-session`, `/sessions`, `/checkpoint`, `/aside`, `/context-budget`), learning (`/learn`,
`/learn-eval`, `/evolve`, `/promote`, `/skill-create`, `/skill-health`, `/rules-distill`), loops (`/loop-start`,
`/loop-status`, `/claw` — NanoClaw v2 persistent REPL with model routing), and project / infrastructure
(`/harness-audit`, `/model-route`). The repo's stated direction (per `AGENTS.md` "Workflow Surface Policy" and
`commands/` README) is **skills-first**: `commands/` is "a legacy slash-entry compatibility surface" kept for
cross-harness parity and migration, with new contributions landing in `skills/` first. `legacy-command-shims/` is the
parallel surface for shim-only entries.

**`scripts/`** is cross-platform Node.js utilities (CommonJS, plain `.js`, no TypeScript per the `.claude/rules/node.md`
rule pack) implementing the hook bodies, the `ecc` CLI (`scripts/ecc.js list-installed`, `doctor`, `repair`, plus
`install-plan.js` / `install-apply.js` for selective install), and the `scripts/lib/` shared helpers. **`tests/`** is 58
test files (`tests/run-all.js` plus mirrored structure under `tests/hooks/` and `tests/lib/`); the v1.8.0 changelog
claims 997 internal tests passing. **`ecc2/`** is the alpha Rust control plane — `ecc-tui` binary built on ratatui
(TUI), tokio (async), rusqlite-bundled (state store), git2 (worktree integration), clap (CLI), tracing, chrono, cron —
exposing the dashboard + session + worktree control surface that the v2.0 roadmap intends to consolidate
hook-distributed state behind. Other top-level files: `ecc_dashboard.py` (Tkinter GUI), `agent.yaml` + `manifests/` +
`plugins/` for cross-harness packaging, `schemas/` (9 JSON Schema validators), `contexts/` (per-context configurations),
`the-shortform-guide.md` + `the-longform-guide.md` + `the-security-guide.md` (the public guides the README points to).

## 3. What's reusable in Linus

**Phase 7 — SKILL.md schema as the reference for the Linus skill format (R3-03, planning-update lineage).** The Linus v2
plan's deferred skills work (and the prior R3-03 SKILL.md format-spec item) needs a typed skill artifact. ECC's SKILL.md
shape is the most-deployed-in-the-wild reference available: YAML frontmatter with `name` / `description` / `origin`,
body sections for "When to Activate" / "How It Works" / "Examples," required-tools declaration without embedded secrets,
repo-relative or generic examples, harness-specific sections explicitly labeled. The schema is small enough that the
Linus SKILL.md spec can adopt it almost verbatim (adapting `origin: ECC` to `origin: linus` and adding Linus-specific
fields like `cot_budget` / `memory_mode` per DEC-0031 if needed). Worth a Phase 7 spec lift with attribution.

**Phase 2-3 — hook taxonomy as the reference for the Linus hook surface (D3 / R3-02 hook taxonomy ADR; goose's hook
substrate is the second reference).** ECC ships the **deepest hook taxonomy** of any cloned-repo reference. The
categories (pre-bash quality / tmux / push / GateGuard checks; pre-write doc-file-warning; pre-compact suggest-compact;
config-protection blocking edits to linter configs; gateguard-fact-force blocking first-edit-per-file pending
investigation; mcp-health-check; post-edit accumulator batching for Stop-time format; stop-time format+typecheck;
stop-time evaluate-session extracting patterns; stop-time cost-tracker; post-tool-use observe for continuous learning;
context-monitor warning on exhaustion / cost / scope creep / tool loops) are a worked vocabulary the Linus hook-taxonomy
ADR can lift directly. The **`ECC_HOOK_PROFILE` minimal / standard / strict gating** plus `ECC_DISABLED_HOOKS` runtime
disable is the right control surface — users dial enforcement without editing manifests. Goose's hooks substrate (per
recent PR #57 refresh) is the second reference; ECC's is older and broader. Worth folding both into the hook-taxonomy
ADR.

**Phase 2-3 — MCP-server reference catalog mapping for Linus tool-registry seed list (DEC-0045 fastmcp default, DEC-0046
external-API deployment field).** ECC's `mcp-configs/mcp-servers.json` is a 14+ entry curated catalog with descriptions
and gating commentary (the explicit "keep under 10 MCPs enabled to preserve context window" plus `ECC_DISABLED_MCPS`
per-install override). For the Linus Phase 2/3 tool registry that DEC-0045 puts on fastmcp, the ECC catalog is the right
seed list — covering memory (omega-memory, longhand for session history), web fetch (Firecrawl, Exa, Context7 for docs),
evaluation (evalview for regression testing), and orchestration (devfleet for parallel worktree agents). The DEC-0046
external-API deployment field lines up cleanly with ECC's distinction between stdio (`npx` / `uvx` spawned) and
`type: "http"` MCP servers. Worth using the catalog as a curated checklist when seeding the Linus tool registry.

**Phase 2 — agent-file structure as the reference for Linus Worker-spawn manifests (DEC-0050 Role as first-class type,
DEC-0051 AgentReport typed inter-agent message).** ECC's 60 `agents/*.md` files factor role definitions cleanly:
frontmatter declares `name` / `description` / `tools` (a whitelist) / `model` (haiku / sonnet / opus per task), and the
body is a focused system prompt. This is the cleanest existing reference for the per-Worker manifest format the Phase 3
spawner spec (`docs/specs/phase3-spawner.md`) currently leaves open. Where Letta's Agent File ships full agent state and
Goose's Recipe ships a task-spec, ECC's agent files ship the **role definition** — the third corner of the task-spec /
agent-state / role-definition triangle. The Phase 3 spawner should adopt this shape for Linus `Role`-as-first-class-type
(DEC-0050).

**Phase 2 — multi-harness pattern as confirming signal for DEC-0017 (harness plurality) and DEC-0005/DEC-0056 (OpenAI +
Anthropic dual surfaces).** ECC explicitly targets Claude Code, Codex, Cursor, OpenCode, Gemini, Zed, and GitHub Copilot
as execution surfaces, with skills as the portable unit and per-harness adapters limited to loading + event-shape +
command-name mapping. The architectural stance ("If a change requires editing three harness copies of the same workflow,
the shared source is in the wrong place. Put the workflow back in `skills/`, then adapt only loading, event shape, or
command routing at the harness edge") is **exactly** the Linus DEC-0017 plus DEC-0020 stance applied to the harness
layer. Confirming evidence that "harnesses are pluggable surfaces; the durable workflow lives below them" is the right
architectural bet. Worth referencing as a multi-vendor data point in the harness-plurality synthesis.

**Phase 2 — memory persistence + continuous-learning hook pair as the reference for Layer C session-store integration
(DEC-0028 memory pillar, DEC-0029 episodic SQLite + content hashes + git, DEC-0030 scratchpad first-class).** ECC's
`SessionStart` hook loads prior context, `PreCompact` saves state before compaction, `Stop` hooks evaluate the session
for extractable patterns and persist activity to a SQLite state store. The `continuous-learning-v2` skill plus
`/learn-eval` + `/evolve` + `/promote` + `/instinct-status` commands implement an instinct-based learning loop with
confidence scoring and import/export. This is a worked precedent for the Linus v2 N5 session-store work plus Layer C
episodic-memory surface — the architecture is the same shape (hooks at lifecycle points, SQLite store, content hashes),
the rough taxonomy is the same (per-session activity → extracted patterns → confidence-scored skills → promotion to
global). The implementation is too Node-and-Claude-Code-specific to vendor; the architecture is reusable.

**Phase 7+ — AgentShield as the reference for Linus config-security scanning (DEC-0024 supply-chain posture, SAFETY.md
sandbox tiers).** AgentShield (`ecc-agentshield`, 1282 tests, 102 rules per v1.6.0 changelog) is a CLI + GitHub App that
scans `.claude/` configs for hardcoded secrets, prompt-injection patterns, overly permissive allowlists, dangerous
bypass flags, risky MCP servers, command injection via interpolation in hook scripts, data exfiltration patterns, and
silent error suppression. The check matrix (CLAUDE.md / settings.json / mcp.json / hooks/ / agents/) maps cleanly onto
Linus's equivalent surfaces. For Phase 7+ when Linus accepts external skill manifests (per DEC-0046 / DEC-0047), an
AgentShield-equivalent scanner is the right defense-in-depth layer. Goose's recipe-scanner is the parallel reference;
AgentShield is the **config-time** scanner (analyzes the static `.claude/` tree), goose's recipe-scanner is the
**execution-time** scanner (analyzes a specific recipe before running it). Linus needs both eventually; AgentShield is
the cheaper first build.

**Cross-cutting — `commands/` legacy / `skills/` canonical demotion as a design lesson.** ECC explicitly demoting
`commands/` from canonical to legacy-compat surface ("Workflow Surface Policy" in `AGENTS.md`) is a worked example of
how a mature workflow repo handles surface drift. The lesson: when two surfaces overlap (Linus's eventual MCP-tool
surface vs. slash-command surface vs. skill surface), pick one canonical and explicitly demote the others to "kept for
compatibility, contribute new work to canonical." Worth applying when Linus's own surface count grows.

## 4. What's inspiration only

**The ecc.tools commercial layer + GitHub App + Pro tier.** ECC Pro ($19/seat/mo private-repo PR audits via the
`marketplace/ecc-tools` GitHub App with 150 installs), the GitHub Sponsors funnel, and the public Hermes operator story
are entrepreneurially instructive but not directly applicable to Linus's single-user, Apple-Silicon-native, locally-
served, no-paid-APIs-required posture. The relevant lesson is **how a solo OSS maintainer wraps an OSS core in a
sponsorship + GitHub App + Pro tier without the OSS surface drifting** — the Hermes Boundary doc is a clean policy for
"what stays public, what stays private." Relevant to E1 / E10 / E12 entrepreneurship items and the eventual Phase 8
commercial-surface thesis as a worked case study, not as code to lift.

**ECC 2.0 alpha Rust control-plane (`ecc2/`).** The ratatui + tokio + rusqlite + git2 + clap stack is a reasonable
Rust-side choice for an interactive control plane, and the `ecc-tui` subcommand surface (`dashboard`, `start`,
`sessions`, `status`, `stop`, `resume`, `daemon`) lines up with the kinds of operations a Linus orchestration front-end
eventually needs. But the alpha is explicitly not GA, Linus already commits to openclaw as the Phase 5 front-end (per
`docs/repo-notes/openclaw.md` and DEC-0008), and the rusqlite + git2 stack carries assumptions about single-process
control that don't match Linus's parallel-agent model (DEC-0050). Useful as a Rust-side reference for the kinds of
subcommands a future Linus CLI might expose; not content to vendor.

**232 skills is more breadth than Linus needs at Phase 1.** The Linus skill set will be domain-driven (bioinformatics

- scientific computing + LanzaTech-style metagenomics workflows + Phase 6+ fine-tuning workflows) rather than
  language-coverage-driven (TypeScript / Python / Go / Java / Kotlin / Rust / C++ / Swift / Perl). Most of ECC's skills
  won't apply directly to Dan's work. The **format** is reusable; the **content** is largely orthogonal.

**60 agents is more than Linus needs at Phase 2/3.** Most of ECC's agents are per-language reviewers / build-resolvers
that won't apply to Linus's bio + agentic systems focus. A handful are directly relevant (`planner`, `architect`,
`tdd-guide`, `code-reviewer`, `security-reviewer`, `harness-optimizer`, `loop-operator`, `mle-reviewer`) — the rest are
inspiration only.

**Heavy framing language ("Anthropic Hackathon Winner," "182K+ stars," "production-ready" + "battle-tested" repeated
throughout).** The marketing posture is the kind of framing the
[`docs/syntheses/agentic-systems-synthesis.md`](../syntheses/agentic-systems-synthesis.md) Maestro-as-empirical-object
thread flags as over-claiming. Linus documentation should not adopt this framing.

## 5. What's incompatible or out of scope

**Node.js + Claude-Code-specific hook bootstrap.** ECC's hooks are heavily-engineered Node bootstrap one-liners that
resolve `CLAUDE_PLUGIN_ROOT` across plugin / marketplace / cache install paths, then delegate to
`scripts/hooks/<hook>.js` via the `run-with-flags.js` wrapper. The architecture assumes a Node 18+ runtime, Claude
Code's specific hook lifecycle (`PreToolUse` / `PostToolUse` / `PreCompact` / `SessionStart` / `Stop` /
`PostToolUseFailure` / `SessionEnd`), and the plugin-install resolution rules. Linus's orchestration layer is Python
(DEC-0027 multi-language stance: Python is the core orchestration language) and Linus doesn't ship as a Claude Code
plugin — the bootstrap is not transportable. The hook **taxonomy** lifts cleanly; the **implementation** doesn't.

**Plugin-distribution model assumes Claude Code marketplace.** ECC installs primarily via `/plugin marketplace add` +
`/plugin install ecc@ecc` in Claude Code. The OSS installer (`install.sh --profile full` / `npx ecc-install`) is the
manual fallback. Linus doesn't have a marketplace-distribution story — it's a personal orchestration backend, not a
plugin. The selective-install architecture (`install-plan.js` / `install-apply.js` / manifest-driven targeted component
installation) is interesting prior art for "users opt into the components they want" but isn't load-bearing for Linus's
posture.

**Multi-harness adapter complexity.** ECC's adapter layer for Cursor / OpenCode / Codex / Gemini carries non-trivial
per-harness translation logic (Cursor uses `.cursor/` for rules; Codex reads `AGENTS.md` + plugin metadata + MCP config
but hook parity is instruction-driven; OpenCode has a plugin/event system with 20+ event types; Gemini is install/
instruction-oriented). Linus is single-user and currently single-harness-primary (Claude Code today, openclaw at Phase 5
per DEC-0008). The adapter pattern is interesting if Linus ever needs to support multiple harnesses; the
specific-harness shims aren't applicable now.

**232-skill catalog is too large to audit holistically.** A repo-note can speak to the format and a sample of skill
categories; auditing all 232 individually is out of scope for this synthesis pass and probably out of scope for any
single Linus session. If specific Linus phases need specific ECC skills (e.g., `agent-harness-construction`,
`continuous-learning-v2`, `agentic-engineering`, `mle-workflow`), those should be read individually at adoption time
rather than holistically up front.

**Tkinter dashboard + Python-side surfaces.** `ecc_dashboard.py` is a Tkinter desktop app for status monitoring;
`ecc consult` is a Python CLI advisor. Both run in ECC's Python tooling, not in the agentic loop. Useful as a worked
example of "the OSS repo ships its own status UI alongside the harness-side install" but Linus doesn't need a Tkinter
dashboard.

**License-compatible but heavy to vendor.** MIT allows full incorporation but the repo is 60 agents + 232 skills + 75
commands + comprehensive hooks + 14 MCP configs + Rust control plane + Python dashboard + selective installer + cross-
harness adapters + commercial wrapper + GitHub App. Vendoring wholesale is the wrong move; surgically lifting the
schemas (SKILL.md, agent file frontmatter, hook taxonomy, MCP config catalog) is the right move.

## 6. Recommendation: **Study** (with Adapt candidates for Phase 7+ skills work and the Phase 2-3 hook-taxonomy ADR)

ECC is the **single deepest reference** for a mature Claude-Code-shaped ecosystem under one roof — agents, skills,
hooks, rules, MCP configs, slash commands, cross-harness adapters, and a commercial wrapper. It's also too large and too
organizationally-shaped to vendor wholesale, and the implementation is too Node + Claude-Code + plugin-distribution
specific to lift directly into Linus's Python-orchestration + locally-served + no-paid-APIs posture. The right posture
is **Study, with surgical Adapt lifts at three points**: (1) the SKILL.md schema as Linus's Phase 7 skill-format
reference; (2) the hook taxonomy as the Phase 2-3 hook-taxonomy ADR's primary reference (alongside goose's hook
substrate as the secondary); (3) the agent-file frontmatter as the Phase 3 spawner's per-Worker manifest reference
(alongside Letta's Agent File for full agent-state serialization and Goose's Recipe for task-specs). The MCP-config
catalog is a useful curated checklist for Phase 2/3 tool-registry seeding, and the memory-persistence +
continuous-learning hook pair is a worked precedent for Linus's Layer C session-store integration. The commercial
wrapper (ECC Pro, AgentShield, GitHub App, Hermes operator story) is **not** applicable to Linus's posture but **is**
entrepreneurially instructive — the Hermes Boundary doc is a clean policy template for any future Linus public/private
boundary work.

Cluster cell: skills-and-practices is the natural primary home (the SKILL.md + hook-taxonomy + practices fold is the
densest contribution). Secondary cell: agentic-systems for the agent-file + cross-harness pattern. Tertiary cells:
g7-harnesses for the multi-harness stance, g6-mcp-tools for the MCP-config catalog, security for the AgentShield
reference, entrepreneurship for the commercial-wrapper case study. Do **not** vendor; do **not** adopt as a Linus
substrate; do study the schemas and lift them with attribution at the three Phase 2/3/7 entry points named above.

## 7. Questions for Dan

1. **SKILL.md schema lift for the Phase 7 Linus skill format (R3-03 promotion).** ECC's SKILL.md is the most-deployed
   skill-format reference available, and the schema (YAML frontmatter with `name` / `description` / `origin` plus a body
   structured around "When to Activate" / "How It Works" / "Examples" + required-tools whitelist) is small enough to
   lift almost verbatim. Should the deferred R3-03 SKILL.md spec adopt ECC's schema as the v0 reference, adapting only
   the Linus-specific fields (`cot_budget` / `memory_mode` per DEC-0031, biosecurity tier per DEC-0047)? Tentative
   answer: yes — the schema is the most concrete reference available, and the alternative (custom-shape Linus skill
   format) doesn't earn the design tax.

2. **Hook-taxonomy ADR — promote ECC's taxonomy + goose's hooks substrate as dual references for the deferred R3-02 / D3
   hook-taxonomy ADR?** ECC's hook taxonomy is broader (PreToolUse / PostToolUse / PreCompact / SessionStart / Stop /
   PostToolUseFailure / SessionEnd with the `ECC_HOOK_PROFILE` minimal / standard / strict gating); goose's hooks
   substrate (per recent PR #57) is the Rust-side reference. Two independent references confirm the taxonomy is stable.
   Should the Phase 2-3 hook-taxonomy ADR commit to both as primary references and lift the hook profile minimal /
   standard / strict gating as the Linus runtime control surface? Tentative answer: yes — the profile gating is the
   right cost lever and the taxonomy is well-validated.

3. **Phase 3 spawner per-Worker manifest format — adopt ECC agent-file frontmatter (`name` / `description` / `tools` /
   `model`) as the v0 schema?** The Phase 3 spawner spec (`docs/specs/phase3-spawner.md`) currently leaves the
   per-Worker manifest open. ECC's agent-file frontmatter is the cleanest existing reference for role definition; Goose
   Recipe is the cleanest for task-spec; Letta Agent File is the cleanest for full agent-state. The three are
   complementary, not competing. Should the Phase 3 spawner spec adopt ECC's frontmatter (with `model` adapted to a
   Linus-side tier — `qwen3` / `qwen3-coder` / future fine-tuned) as the v0 Role manifest, with Recipe and Agent File
   reserved for later spec extensions? Tentative answer: yes — the smallest schema first, extend if needed.

4. **Phase 7+ AgentShield-equivalent config scanner — write a Linus spec now or defer until external skills land?**
   AgentShield is the worked reference for `.claude/`-config-time security scanning (1282 tests, 102 rules). Linus is
   currently single-user (Dan) so external skill manifests are a Phase 7+ concern, but a config scanner that catches
   prompt-injection patterns / hardcoded secrets / overly permissive allowlists in Linus's own configs is useful sooner.
   Should the Phase 7+ skill-screening spec name AgentShield as a primary reference (alongside goose's recipe-scanner as
   the execution-time complement) and be drafted at Phase 2-3 planning to set expectations? Tentative answer: draft the
   spec at Phase 2-3 planning, defer implementation to Phase 7+ — the design intent should be on record before the
   surface widens.

5. **Hermes Boundary policy template — adopt for the Linus public/private boundary at Phase 5+?** ECC's Hermes Boundary
   doc carves out a clean policy: ship sanitized setup docs / repo-relative demos / general operator skills / examples
   without private credentials; do not ship OAuth tokens / API keys / raw operator memory / personal workspace memory /
   private datasets / local-only automation packs. This is a Phase 8 commercial-surface relevant template — when Linus
   eventually accepts external contributions or shares Dan's skill / instinct distillations publicly, the same
   public/private discipline applies. Should the Phase 5+ planning name the Hermes Boundary doc as a policy-template
   reference for the eventual Linus public-surface guidelines? Tentative answer: yes — the policy is clean, well-
   argued, and directly applicable; lift it with attribution when Linus surfaces something external.
