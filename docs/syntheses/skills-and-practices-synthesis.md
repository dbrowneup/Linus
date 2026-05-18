# Skills, Practices, and Opportunities Synthesis

_Synthesized from five X/Twitter practitioner threads, May 2026._

---

## 1. Overview

These five threads come from working practitioners sharing operational knowledge about Claude/AI workflows — not
researchers, not hype merchants. Their provenance matters: they are X/Twitter threads (URLs archived in context),
written by people with hands-on experience running hundreds of sessions or scanning thousands of repos. None of them are
academic. All of them are opinionated from direct use.

The threads cover four distinct but related domains. The "17 Best Practices for Claude Cowork" thread documents
system-engineering patterns from 400+ sessions with Claude's Cowork product — the key insight being that Cowork rewards
setup investment, not prompting skill. The "Stop Staring at the Files" thread is a philosophical piece about the
claw-code project that argues the real skill in an AI-accelerated world is architectural clarity and task decomposition,
not code generation. The "17 Claude Skills → $312/Day" thread is practitioner-focused entrepreneurial content about
specific AI-assisted service offerings and digital products that produce real revenue. The "Top 50 Claude Skills &
GitHub Repos" thread is a curated catalog of skills, MCP servers, and open-source repos across categories — the most
useful reference artifact of the five. The "Cline description" is a concise technical spec for Cline as a
local-model-backed VS Code coding agent.

Taken together, these threads reinforce a single thesis from multiple angles: the bottleneck has shifted from
intelligence to clarity. Agents can execute; humans must still decide what to build, decompose it correctly, and design
the coordination system. This maps directly onto Linus's Maestro/Worker model.

---

## 2. Top 10 Claude/AI Collaboration Practices for Linus

These are drawn from the "17 Best Practices" and "Stop Staring at the Files" threads, filtered for applicability to the
Maestro/Worker workflow in Linus specifically. The Cowork practices were designed for a SaaS product (Claude's Cowork),
but the underlying system-engineering patterns translate cleanly to a local orchestration backend.

**Practice 1: Build a manifest file for every working context, not just CLAUDE.md.** The Cowork thread documents a
specific failure mode: Claude reads every file in a folder, including outdated drafts, and produces contradictory
output. The fix is a tiered manifest — canonical truth at the top, domain files in the middle, archival material flagged
to ignore. Linus already has CLAUDE.md as a session anchor, but this practice argues for extending the pattern. Every
persistent project context that Workers operate in should have a `_MANIFEST.md` that tells the Worker which files are
authoritative, which are domain-scoped, and which to skip. This is low-cost to implement in Phase 1 and high-impact for
any multi-session task.

**Practice 2: Encode standards in files, not in prompts.** The Cowork thread's central message is that prompt
engineering is the wrong investment. System engineering — building context files, global instructions, and skill
definitions — is the right one. For Linus, this means the orchestration layer should maintain persistent context files
for Dan's voice, working style, and project-specific standards. Workers should load these automatically at session
start, not receive them re-explained in each prompt. This is exactly the behavior CLAUDE.md is modeling at the Maestro
level; it needs to propagate to the Worker level.

**Practice 3: Define end state, constraints, and uncertainty protocol in every task spec.** The Cowork thread formulates
this as three questions every task prompt should answer: what does "done" look like, what are the constraints, and what
should Claude do when uncertain? This is directly applicable to Linus's Maestro/Worker spec format. Worker task specs
written in `experiments/` or `docs/specs/` should include an explicit uncertainty protocol — "if the data source is
missing, flag it rather than guessing; if a classification is ambiguous, put it in /needs-review rather than
committing." This prevents the most expensive failure mode: long autonomous runs that confidently produce wrong output.

**Practice 4: Always request a plan before execution.** The Cowork thread calls this the single change that prevents 90%
of disasters. The cost is 30 seconds; the benefit is catching misinterpretations before they produce 20 minutes of wrong
work. Linus should enforce this at the Worker spec level — every spec should include a "plan step" requirement, where
the Worker produces a brief execution plan and waits for confirmation before acting. This is already implied in Linus's
`[Plan] → [Act]` workflow but should be formalized in the Maestro/Worker protocol document.

**Practice 5: Scope context to the minimum the task actually needs.** Larger context windows do not produce better
output; they produce noisier output. The Cowork thread is explicit: subagents should receive only the context needed for
their specific subtask. This maps directly to Linus's parallel agent design. When Workers are fanned out for parallel
execution, each Worker should receive a scoped context package — not the full KnowledgeBase, not all project files, but
the minimum set required for that task. This is a design constraint for Phase 2's agent spawner.

**Practice 6: Batch related work into single sessions.** Every agent session has startup cost: file loading, context
initialization, model warm-up. The Cowork thread argues for batching related tasks into single runs. For Linus, this
means the task scheduler in Phase 2 should group related work items and pass them to a single Worker session rather than
spawning separate sessions for each subtask. Five related analysis tasks should be one Worker invocation, not five.

**Practice 7: Use subagents deliberately for independent parallel subtasks.** The Cowork thread documents that parallel
subagents reduce multi-step research tasks from 40 minutes to 10. The trigger condition is independence: subtasks that
don't depend on each other's outputs can run simultaneously. For Linus, this is the core value proposition of Phase 3's
parallel agent fan-out. The Worker spec should explicitly identify which subtasks are independent, so the agent spawner
can parallelize them. "Analyze these four vendors simultaneously" is a different instruction than "analyze these four
vendors sequentially."

**Practice 8: The bottleneck is architectural clarity, not execution speed.** This is the central insight of the "Stop
Staring at the Files" thread. The claw-code demonstration ported an entire codebase in an hour, but the human's
contribution was ten sentences of direction — not code. As agents become faster, the value of knowing what to build, how
to decompose it, and how to coordinate the pieces increases. For Dan's work with Linus, this means Maestro time should
be spent almost entirely on architecture, decomposition, and spec quality — not on implementation. Every hour spent
clarifying a spec before handing it to Workers is worth more than three hours of Maestro-level implementation.

**Practice 9: Externalize everything to version-controlled files.** The Cowork thread frames this as the solution to the
no-memory-between-sessions problem: preferences, project plans, SOPs, and decisions all live in files, not in AI memory.
Linus's architecture already reflects this (CLAUDE.md, DECISIONS.md, ARCHITECTURE.md), but it needs to extend to
Worker-level operation. Workflow definitions, recurring task specs, and evaluation rubrics should live as versioned
markdown files in `docs/specs/` or `experiments/`, so they are portable, refinable, and auditable.

**Practice 10: Taste and conviction are the non-commoditized inputs.** The "Stop Staring at the Files" thread argues
that as AI capability commoditizes code generation, the scarce input becomes the founder's specific point of view about
how something should work. This is directly applicable to Linus as a project: the value Dan is building is not a better
inference wrapper, but a personal AI system shaped by his specific scientific expertise, workflow preferences, and
judgment about what's worth building. The differentiation of any tool Dan builds on top of Linus will come from his
domain knowledge, not from the underlying models.

**Practitioner cross-check: Anthropic-internal Claude Code usage.** The same ten practices recur — under different
labels — in [How Anthropic teams use Claude Code (v2)](../../context/notes/How-Anthropic-teams-use-Claude-Code_v2.pdf),
which collects workflow exemplars from ten Anthropic-internal teams (data infrastructure, product development, security
engineering, inference, data science, API knowledge, growth marketing, product design, RL engineering, legal). The
convergence is informative because these are first-party users who built the harness, and their advice overlaps almost
completely with the X/Twitter practitioner threads above: detailed CLAUDE.md files are the single strongest predictor of
good Claude Code performance (data infrastructure team), self-sufficient verify-loops where Claude runs
builds/tests/lints automatically and catches its own mistakes are the way to extend autonomous runtime without
supervision (Claude Code team), custom slash commands carry an outsized share of repeated workflow value (security
engineering authored 50% of the entire monorepo's slash-command surface area), and the "treat the session like a slot
machine — save state, let it run 30 minutes, accept or reset rather than wrestle with context" pattern from the data
science team is a cleaner statement of Practice 4's plan-before-execution discipline pushed to its operational limit.
Three additional patterns from the Anthropic playbook are not yet in the practitioner-thread set above but are worth
folding into Linus's Maestro/Worker discipline: parallel Claude Code instances per repository as the
cross-day-context-preservation primitive (data infrastructure team — each instance maintains full context across days,
an alternative to the multi-worktree pattern from claude-squad / Section 4); end-of-session documentation updates as a
closing-cadence ritual where the agent summarizes completed work and proposes CLAUDE.md refinements based on actual
usage (data infrastructure team — directly compatible with Linus's session-summary discipline); and auto-accept mode
plus checkpoint-and-revert-by-git as the "let it run" enabling pair (Claude Code team — Practice 4's plan-then-act,
restated as a workflow pattern rather than a discipline rule). Open question for Dan, mirrored as Q6 below: should the
Phase 2a Worker spec format mandate a "verify loop" field (build / test / lint commands the Worker runs as its own
success signal before reporting done), elevating the Anthropic Claude Code team's self-sufficient-loops tip to a Linus
convention rather than a recommendation?

---

## 3. Skills Worth Incorporating into Linus

From the "17 Claude Skills" and "Top 50 Claude Skills" threads, these are the capabilities worth building or
prioritizing, mapped to Linus's current state.

**1. Deep research with auto-continuation (claude-deep-research-skill).** An 8-phase research workflow that continues
across context limits. Linus does not have this yet; autoresearch and autoresearch-mlx are in `repos/` as reference
material but not integrated. This belongs in Phase 1's recon work and Phase 3's KnowledgeBase integration. Dan's
scientific background makes this uniquely valuable — deep research over his paper corpus is a core use case.

**2. PDF processing with table extraction and form filling.** The Anthropic official skill at
`github.com/anthropics/skills/tree/main/skills/pdf` covers read, extract, merge, and split. Linus has poppler installed
for PDF reading, but no structured skill wrapping it. This is Phase 1 / Phase 2 work and directly enables KnowledgeBase
ingestion pipelines.

**3. Systematic debugging with root-cause-first methodology.** The "Superpowers" skill set (obra/superpowers, 96k stars)
includes a 4-phase systematic debugging approach. Linus does not have a formalized debugging skill. Given that Workers
will be writing and running code, a structured debugging skill baked into the Worker context would reduce the
back-and-forth when automated runs fail. Phase 2 item.

**4. Market objection mining from unstructured text.** From the "$312/Day" thread: collect Reddit, Twitter, and review
data; feed it to Claude in chunks; extract recurring objections only. This is a high-value research pattern for any
product or consulting work Dan undertakes. It requires a data collection step (scraping or manual input) and a
structured extraction prompt. Phase 1 — this can be prototyped with existing tools immediately.

**5. Vendor comparison and decision frameworks.** The "$312/Day" thread lists vendor comparison reports and decision
frameworks as reliable revenue generators. More importantly for Linus, these are internal tools Dan will need
repeatedly: comparing inference backends, evaluating new repos, choosing between training approaches. A decision
framework skill that produces structured pros/cons tables and risk notes is Phase 1 work with immediate utility.

**6. Context optimization with KV-cache awareness.** The `muratcankoylan/agent-skills-for-context-engineering` skill
(13.9k stars) covers token cost reduction and KV-cache tricks. For Linus running on 32GB unified memory with local
models, context efficiency directly affects throughput. This skill's patterns should inform how Linus's orchestration
layer manages context across Worker sessions. Phase 2 item.

**7. Meeting summary and action extraction.** A lightweight but immediately useful capability: turn meeting notes or
conversation transcripts into "who does what by when" summaries. Dan's scientific and startup background involves many
discussions that need follow-up tracking. This is something a local Worker can do reliably today with minimal
infrastructure. Phase 1, buildable as a simple experiment.

**8. Content repurposing across platform formats.** From the "$312/Day" thread: one long-form piece → Twitter threads,
LinkedIn posts, email summaries, each adapted to platform psychology. For Dan's entrepreneurial goals, being able to
convert research findings or technical writeups into multiple distribution formats is a force multiplier. Phase 2, after
the orchestration layer can route tasks to appropriate Workers.

**9. Natural language to SQL (Vanna AI pattern).** For querying Dan's genomics and scientific datasets without writing
SQL by hand. Vanna AI (`vanna-ai/vanna`) implements this pattern. Linus does not have this; it is most relevant for
Phase 3 when the KnowledgeBase includes structured datasets alongside document vectors. Worth evaluating Vanna's MLX
compatibility.

**10. Codebase-to-knowledge-graph (Codebase Memory MCP pattern).** `DeusData/codebase-memory-mcp` is a static C binary
(zero dependencies, macOS arm64 native) that indexes repositories into a knowledge graph via tree-sitter AST analysis
across 155 languages, exposing 14 MCP tools for structural search, call tracing, dead code detection, and Cypher-like
queries. Now studied in full (see `docs/repo-notes/codebase-memory-mcp.md`). _Verdict:_ **Integrate (Phase 2a spike)** —
the integration path is simple (call the binary from Python Worker tasks via subprocess). Smoke-test on Linus's own
`src/linus/` codebase first; if queries are useful, wire into KnowledgeBase as an optional indexing layer. Phase 2a
spike, Phase 3 for deeper integration.

**11. Autonomous research loop (autoresearch pattern).** Karpathy's autoresearch repo is already in `repos/` and
`autoresearch-mlx` is there as the Apple Silicon port. _Verdict for the MLX fork:_ **Integrate** (see
`docs/repo-notes/autoresearch-mlx.md`). The MLX fork runs natively on M1 Max today via `uv sync`. Concrete plan: in
Phase 1 finish, run the upstream loop verbatim for one overnight session as a smoke test (confirm the 6–7 min/experiment
cycle on Dan's chip). In Phase 6d, fork under `experiments/autoloop/` and swap the pretraining payload for a LoRA
fine-tune harness; keep `program.md` and the keep-or-revert-by-git discipline. The `program.md` pattern is itself the
closest working example of a Linus-style `SKILL.md` in the cloned repo collection. The wiring into Linus's orchestration
layer as a schedulable Worker task belongs in Phase 3, but the smoke run should not wait.

**12. SOP generation from conversation history.** From the "$312/Day" thread: turn Slack threads or messy notes into
step-by-step SOPs and decision trees. For Linus, this is how the project's own operational knowledge gets formalized. A
skill that takes a conversation about a resolved problem and produces a clean SOP entry would accelerate Linus's
self-documentation. Phase 2.

**13. Skill creator (meta-skill).** Anthropic's official Skill Creator skill
(`anthropics/skills/tree/main/skills/skill-creator`) takes a workflow description and produces a `SKILL.md` in five
minutes. For Linus, this is how the Worker skill library grows without Dan having to write skill definitions by hand.
Phase 2, after the skill framework is in place.

---

## 4. GitHub Repos Worth Evaluating

These are repos from the "Top 50" thread not already present in `repos/` that deserve evaluation for Linus. Repos
already in Linus (`autoresearch`, `autoresearch-mlx`, `cline`, `openclaw`, `claw-code`, `claw-code-local`) are excluded.

**fastmcp** (`jlowin/fastmcp`) — Build MCP servers in minimal Python. Directly relevant for Phase 2 when Linus needs to
expose its tools and KnowledgeBase via MCP. The low-friction approach fits the "delete requirements" principle. _Verdict
settled (DEC-0045):_ **Integrate**. FastMCP is the committed MCP framework; Linus builds FastMCP servers whose
`@mcp.tool`-decorated functions call into Linus's KB and orchestration code. Do not build a parallel in-house MCP layer.
Phase 2.

**Task Master AI** (`eyaltoledano/claude-task-master`) — PRD → structured tasks with dependencies → Claude executes
sequentially. Now studied in full (see `docs/repo-notes/claude-task-master.md`). _Verdict:_ **Study** — adopt the
pattern (task-spec JSON shape, three-role model split, complexity-then-expand, update-subtask breadcrumb), not the
product. MIT-with-Commons-Clause license and Node.js monolith footprint rule out vendoring. Phase 1 evaluation, Phase 2
design input.

**claude-squad** (`smtg-ai/claude-squad`) — Terminal app supervising multiple coding-agent CLIs in parallel, each in an
isolated git worktree. Now studied in full (see `docs/repo-notes/claude-squad.md`). _Verdict:_ **Study** — the
git-worktree-per-task isolation pattern and AutoYes daemon are the reusable primitives; do not vendor the Go binary.
Critically: claude-squad and Task Master AI are _complementary, not competing_ (Task Master decomposes; claude-squad
gives each task a private worktree). The Phase 1f answer is "use both patterns, neither product, build the glue."
Phase 1.

**pydantic-ai** (`pydantic/pydantic-ai`) — Type-safe agent framework. Now studied in full (see
`docs/repo-notes/pydantic-ai.md`). _Verdict:_ **Integrate (Phase 2a)** — the Agent class, RunContext dependency
injection, and validated `@tool` decorator are the orchestration primitive for Linus Workers. Reduces orchestration code
by ~70% versus a bespoke wrapper; tradeoff is a new core-path dependency. Tier 1 open question: R2-01. Phase 2a.

**DSPy** (`stanfordnlp/dspy`) — Program (not prompt) foundation models. Now studied in full (see
`docs/repo-notes/dspy.md`). _Verdict:_ **Study (Phase 1 → 6)** — not a runtime for Phase 2a; essential reading for
Phase 6. DSPy Signatures are a clean tool-contract habit to establish now; the BootstrapFewShot experiment (DSPy-
optimized prompts → LoRA training demonstrations for Qwen2.5-Coder) is the Phase 6 entry point. Phase 1 for awareness,
Phase 6 for application.

**lmnr** (`lmnr-ai/lmnr`) — Full-stack AI observability platform. Now studied in full (see `docs/repo-notes/lmnr.md`).
_Verdict:_ **Study (Phase 5+)** — the app-server is Linux-only, blocking native M1 Max deployment. Immediate Phase 2a
implication: OTel instrumentation from day one (one SDK import, standard `gen_ai.*` attributes, lightweight SQLite span
store) so no retroactive changes are needed when Laminar is deployed at Phase 5. Phase 5.

**rendergit** (`karpathy/rendergit`) — Git repo → single static HTML file for LLMs. Now studied in full (see
`docs/repo-notes/rendergit.md`). _Verdict:_ **Watch (Phase 5+)** — Claude Code's file reading is sufficient for Phase
1–4; useful for repo-to-hosted-Claude architectural reviews at Phase 5+. Phase 5+.

**gptme** (`gptme/gptme`) — Terminal-first AI agent CLI with a layered Python architecture: core chat loop, stateless
tools, plugin system, skills (YAML bundles), and lessons (pattern-activated contextual guidance). Now studied in full
(see `docs/repo-notes/gptme.md`). _Verdict:_ **Study (Phase 2a, 7)** — the lessons system (inject domain knowledge when
task language matches keywords) is the concrete answer to encoding Dan's bioinformatics expertise into Worker context
without re-injecting it in every prompt. The hook system is the enforcement point for SAFETY.md sandbox policy. Phase 2a
study, Phase 7 adaptation.

**markdownify-mcp** (`zcaceres/markdownify-mcp`) — PDFs, images, audio → Markdown. Relevant for KnowledgeBase ingestion:
converting heterogeneous documents (papers, slides, book excerpts) to a consistent Markdown format before chunking and
embedding. Phase 2 / Phase 3.

**dlt** (`dlt-hub/dlt`) — LLM-native data pipelines from 5,000+ sources. For Phase 4's data sovereignty goals, pulling
structured datasets into Linus's local storage. Dan's genomics background means he will want to ingest databases (NCBI,
UniProt, etc.) offline. Phase 4.

**promptfoo** (`promptfoo/promptfoo`) — Automated security testing for AI models. Linus's sandbox policy (SAFETY.md)
requires testing that Workers don't escape constraints. promptfoo provides automated red-teaming. Phase 2, as part of
the safety infrastructure.

**ExtractThinker** (`enoch3712/ExtractThinker`) — ORM for document intelligence. Structured extraction from documents —
tables, figures, metadata — with an ORM-like API. Relevant for scientific paper processing in the KnowledgeBase.
Phase 3.

**Huginn** (`huginn/huginn`) — Self-hosted event-driven automation platform. Despite its presentation as a monitoring
tool, its primary value for Linus is as an _orchestration reference_. Now studied in full (see
`docs/repo-notes/huginn.md`). _Verdict:_ **Study (before Phase 2a orchestration design)** — the Agent/Event DAG pattern
(stateful Agents consuming and emitting structured Events along a directed graph in a scheduler loop) directly informs
Phase 2a dispatch design. Read the agent-wiring code before finalizing the session-store mechanism; the pattern
transfers, not the Ruby implementation. Phase 2 reference.

---

## 4a. Cluster anchor: g11 agent frameworks (added 2026-05-05, updated 2026-05-08)

The 2026-05-05 landscape remapping made **[g11 agent frameworks](repo-clusters/g11-agent-frameworks.md)** the primary
cluster anchor for this synthesis. g11 covers pydantic-ai, dspy, superpowers, Agent-Skills-for-Context-Engineering,
gptme, huginn, lmnr, and promptfoo — the agent framework, skills definition, and evaluation infrastructure that
operationalize the practices and skills listed above. Adopting g11 as the anchoring cluster reframes the
skills-and-practices question from "what should Linus do" to "here is what the community has already built; which
patterns apply to Linus's Maestro/Worker model."

Three findings from the g11 synthesis have immediate design weight. First, g11 identifies a three-layer Worker stack:
pydantic-ai as the runtime base (type safety, provider abstraction, tool registration), superpowers's behavioral
patterns as the discipline layer (spec-first, RED-GREEN-REFACTOR, two-stage review), and gptme's plugin/lessons
architecture as the extensibility model for domain skills. These fit together because they operate at different levels
of the same stack rather than competing. Second, the progressive-disclosure skill architecture (YAML frontmatter index
loaded at startup, markdown body content activated lazily on keyword match) appears independently in superpowers, gptme,
and Agent-Skills-for-Context-Engineering — triple convergence is strong evidence the pattern is correct; Linus should
adopt it as the standard format for domain skills in a `src/linus/skills/` directory. Third, g11 distinguishes
evaluation (promptfoo — measures correctness on known tasks) from observability (lmnr — measures what the system
actually does during live operation); both are needed and they are not substitutes for each other.

**Worked example of the community harness-pattern catalogue: claude-code-guide.** The
[claude-code-guide](../repo-notes/claude-code-guide.md) repo (zebbern/claude-code-guide) is the most concrete external
exemplar of how a community organizes Claude Code patterns at scale, and it occupies a useful niche in the g11 anchor
that none of pydantic-ai, dspy, superpowers, or gptme cover: it is a markdown-only crowd-curated catalogue rather than a
runtime, and its scale (106 sub-agent personas, 29 SKILL modules, three CLAUDE.md guideline collections, ~3,700-line
README mirroring upstream Anthropic releases) makes it a rich quarry for shape-mining without inviting a vendoring
decision. The repo-note flags two structural lifts directly relevant to Linus. First, the agent-persona file shape (YAML
frontmatter with `name` / `description` / allowed `tools`, then a "When invoked" procedure list and explicit checklists
like "Cyclomatic complexity < 10 maintained") is directly applicable to the Phase 3 spawner contract (DEC-0050) and the
typed AgentReport output (DEC-0051): Linus's own Role definitions can adopt the same frontmatter shape and procedure
structure, then evolve the output side toward the typed message contract. Second, the orchestration-flavored personas —
`agent-organizer.md`, `context-manager.md`, `multi-agent-coordinator.md`, `workflow-orchestrator.md`,
`task-distributor.md` — are the closest external precedent for the Maestro/Worker dispatch surface itself; they are
worth a focused pass when the spawner moves from stub to implementation. The MUST/SHOULD/SHOULD-NOT rule grammar from
the `guides/` collection (zebbern's and Sabrina's CLAUDE.md exemplars, modeled on aviation-checklist discipline) is a
more machine-checkable shape than Linus's current prose-paragraph conventions, and selectively lifting it for the most
checkable rules (line-length, commit format, smoke-test gating, hook bypass flow) would tighten enforceability without
forcing the rest of CLAUDE.md to abandon the prose-first voice mandated by §Writing style for docs. Two cautions: the
106-persona breadth is aspirational rather than a target — Linus needs five to ten Worker shapes, not a stadium — and
the `skills/` tree is dominated by red-team / pentest workflows that are explicitly out of scope for Phase 1–7 work.
_Verdict: **Study**_ — mine for shapes, do not vendor; the persona library and rule-grammar selectively, the README's
harness-surface coverage as a double-check against Linus's own CLAUDE.md and protocol docs.

---

## 4b. ClawBio as a worked example of the skills-as-shippable-bundle archetype (added 2026-05-10)

The [ClawBio](../repo-notes/ClawBio.md) repo (ClawBio/ClawBio) extends the g11 framing in a direction the
agent-framework cluster does not: it is a working precedent for **what the ship-side of a Linus skill looks like** once
the bench has been written. Three patterns from ClawBio land directly on the skills-and-practices argument and are worth
treating as design inputs rather than reference material.

The first is **the Claude Code plugin marketplace as a Phase 5+ distribution channel**. ClawBio installs as
`/plugin marketplace add ClawBio/ClawBio` followed by `/plugin install clawbio`, after which all 63 skills are
agent-routable inside Claude Code without any deeper integration work. This is the same surface Linus would use to ship
its own skill bundles to any Claude Code user — Dan first, a wider audience later if any of Linus's skills graduate to a
commercial-surface offering. Section 6 already establishes Claude Code as the Maestro harness via
[DEC-0007](../adr/0007-claude-code-terminal-maestro.md); the plugin marketplace is the paired distribution channel for
skill bundles that should be addressable from Claude Code without bundling them into the Linus orchestration runtime.
Importantly, the plugin path does not displace Linus's own internal SKILL.md format or the in-house tool registry — it
is an _output_ format the orchestration layer can render to alongside MCP and direct in-process invocation. Worth
surfacing as a Phase 5/7 distribution-channel option in the spec backlog.

The second is **the reproducibility bundle as a candidate output convention for any Linus skill that produces a
publishable artefact**. Every ClawBio analysis emits `commands.sh` + `environment.yml` + `checksums.sha256` alongside
the markdown report, not as an afterthought but as part of the standard skill-output contract. The argument for adoption
generalizes well beyond biology: any Linus skill whose output might end up in a paper, a slide, or a downstream pipeline
should ship a bundle so a reviewer can reproduce the result in one command without contacting Dan. The cost is small —
three files written alongside the report — and the value compounds with every skill that adopts it. _Seed: DEC-NNNN
reproducibility-bundle-output-convention_ — companion to [DEC-0023](../adr/0023-output-interface-citations-llm-wiki.md)
(output interface citations + LLM Wiki) and [DEC-0027](../adr/0027-linus-practice-stance-batch.md) (public APIs +
measurement discipline). Phase 7 finalization is the natural commit point.

The third is **the SKILL.md conformance linter as a worked example of the "schema is the product" framing that runs
through this synthesis**. ClawBio's `scripts/lint_skills.py` enforces a 17-check checklist on every skill PR: YAML
frontmatter completeness, required sections, ≥3 trigger keywords, ≥3 gotchas, a safety disclaimer reference, the
agent-boundary clause, demo data presence, test directory presence, and a 500-line ceiling on SKILL.md size. The point
is not the specific checks (Linus's own would differ — agent-boundary clauses do not generalize cleanly to non-bio
skills) but the existence of an _enforced_ schema, machine-checkable at PR time. The progressive- disclosure skill
format Section 4a flagged as triple-converged across superpowers, gptme, and Agent-Skills-for-Context-Engineering
becomes a stronger pattern when paired with a linter that prevents drift; a SKILL.md-shaped bundle that no one validates
is markdown, not a contract. _Seed: DEC-NNNN skill-md-conformance-linter_ — Linus's own skill template, regardless of
which lineage it descends from (Anthropic's, ClawBio's, bioSkills's, or a synthesis), should ship with an equivalent
linter from day one of Phase 7 prep.

ClawBio also extends Section 4a's claude-code-guide observation about persona library-as-quarry: ClawBio's
templates/SKILL-TEMPLATE.md plus the conformance linter together are the **engineering shape** for what a Linus skill
template should look like, while the breadth-of-content question (which skills, in which domain order) remains
separately answerable from bioSkills, Anthropic's official skills repo, or whatever lineage Linus chooses to inaugurate
Phase 7 with. The two-axis split — engineering shape from one upstream, content from another — is the operational form
of the "delete every requirement" discipline applied to skill-library inheritance. _Verdict: **Study (with a high prior
on later Adapt-as-skill-library-pattern)**_ from [`ClawBio.md`](../repo-notes/ClawBio.md).

### Output-token-budget compression as a first-class skill (added 2026-05-16, caveman fold-in)

[`caveman`](../repo-notes/caveman.md) (Julius Brussee, MIT) adds a new sub-thread to the skills column: a Claude Code
skill plus 30+-harness install matrix that constrains agent output to telegraphic fragments while preserving technical
content, with a measured **~65–75% output-token reduction at 100% technical accuracy** validated through a disciplined
three-arm eval harness (skill vs. plain `Answer concisely.` vs. baseline; the honest delta is skill vs. terse, not skill
vs. verbose). The pattern is directly applicable to DEC-0032's in-context-window-cap policy — caveman is the output-side
complement to the input-side cap. The Phase 2a Worker spec should absorb an explicit `output_style` field (`verbose` /
`default` / `terse` / `caveman`) alongside the existing `memory_mode` and `cot_budget` (DEC-0031), with the dispatcher
injecting the corresponding system-prompt rider and the audit log recording the choice. The load-bearing discipline rule
is caveman's **auto-clarity carve-out** (drop to normal prose for security warnings, irreversible-action confirmations,
multi-step sequences with ambiguity risk, user-confused states) — the design pattern for "compress aggressively, bypass
under documented conditions" that DEC-0032's cap-bypass-audit-log rule already commits to on the input side. A secondary
opportunity is `caveman-compress`-style memory-file compaction: a derived `CLAUDE.compact.md` variant that Linus's
dispatcher selects when the calling Worker's `output_style` is `terse`, yielding measurable per-invocation input-token
reduction across every Worker call. The
[March 2026 brevity-improves-accuracy paper (arXiv 2604.00025)](https://arxiv.org/abs/2604.00025) cited in the caveman
README is a Phase 1 corpus add candidate alongside the Lost-in-the-Middle and Toolformer adds flagged in the
[Letta-MemGPT paper-note](../paper-notes/Letta-2310.08560.md) §Open Question 7; if the brevity-improves-accuracy
correlation holds on Dan's task suite, `output_style: terse` is not just a cost optimization but a quality one.

---

## 5. Entrepreneurial Opportunities

> **Extracted 2026-05-05.** The seven entrepreneurial opportunities originally listed here have been promoted to a
> first-class [`entrepreneurship-synthesis.md`](entrepreneurship-synthesis.md), where they sit alongside the g10-finance
> transferable-context-management patterns and the Phase 7 biology pillar's commercial surface. This section is retained
> as a pointer; new entrepreneurship content should land in the new synthesis.

The seven opportunities (Scientific literature intelligence service for biotech teams; Automated genomics pipeline
auditing and SOP generation; Domain-specific decision frameworks for funding and grant applications; Environmental data
intelligence for compliance and monitoring teams; AI-accelerated scientific manuscript preparation; Notion template
systems for scientific project management; Local AI infrastructure consulting for research institutions) remain
Dan-profile-relevant; their full treatment lives in the entrepreneurship synthesis. The Tier-1-equivalent action and
Tier 1/2/3 questions for the commercial surface are now owned by that synthesis.

---

## 6. Cline as a Linus Harness

Cline is already in `repos/cline/` as a reference clone. The description thread clarifies its practical value as a Linus
front-end.

Cline is an autonomous coding agent VS Code extension that differs from Claude Code in one critical dimension: it
natively supports local inference backends. Claude Code talks to Anthropic's API; Cline can be configured to talk to
Ollama or LM Studio running on the same machine. For Linus's Maestro/Worker architecture, this means Cline can act as a
Worker-facing IDE harness while Claude Code remains the Maestro-facing interface. Dan writes specs in Claude Code;
Workers execute them in Cline sessions backed by Qwen2.5-Coder 32B (which fits comfortably in 32GB unified memory and is
the recommended model for that RAM tier).

The capabilities Cline adds beyond Claude Code are: autonomous file creation, terminal command execution, and error
debugging — all without leaving VS Code, and all without sending code to any external API when backed by a local model.
The data privacy angle matters for Dan's work with scientific data: bioinformatics pipelines, genomic sequences, and
pre-publication results never leave the machine.

The integration story for Linus is: configure Cline's API provider to Ollama (already running on port 11434 via
Homebrew), select Qwen2.5-Coder 32B, enable compact prompts for local hardware performance. The Cline sidebar becomes
the local-model coding interface, accepting task specs from the Maestro layer and executing them autonomously. The
"compact prompts" setting in Cline is specifically documented to improve performance on local hardware — this is
relevant for M1 Max throughput.

Cline does not replace Claude Code in the Maestro role. It fills the Worker role within VS Code specifically — it is the
harness for code-writing Workers the way Ollama's HTTP API is the harness for text/analysis Workers. Phase 1 is the
right time to validate this integration: pick one well-specified coding task from the `experiments/` queue, configure
Cline against Ollama, and measure whether the output quality justifies the local-only constraint. One architectural
implication from the full Cline note (see `docs/repo-notes/cline.md`): Cline's prompt variants architecture (`xs`,
`hermes`, `glm` tuned for small or local models) is prior art evidence that tool-use prompt templates need to be
per-model-family to work reliably on anything smaller than frontier. Linus's Phase 7 skills design should plan for
variant templates per Worker model class (Qwen, Mistral, future Linus fine-tunes) from the start, not as a retrofit.

---

## 7. Open Questions for Dan

**Question 1: What is Linus's first monetizable capability, and when?** _(Moved to
[`entrepreneurship-synthesis.md`](entrepreneurship-synthesis.md) on 2026-05-05; retained here as a cross-reference for
the build-vs-monetize tension that touches Maestro/Worker discipline.)_

**Question 2: Does Linus need a custom orchestration layer, or will Task Master AI + Cline cover Phase 2?** _Partially
resolved (DEC-0002; see [answered-questions.md](../../questions/answered-questions.md)):_ custom orchestration stands,
but with Algorithm-checked primitives. Task Master AI and claude-squad are not competing orchestration replacements —
they occupy different layers (decomposition vs. runtime isolation) and the Phase 1f deliverable captures "adopt both
patterns, neither product, build the glue." The open sub-question is whether pydantic-ai as the Phase 2a Worker base
abstraction (Tier 1 R2-01) satisfies the KnowledgeBase integration and sandbox policy requirements without requiring a
fully bespoke router, or whether the custom layer must go deeper.

**Question 3: How does Dan want to handle the transition from Maestro-only to Maestro+Worker in practice?** The "Stop
Staring at the Files" thread describes a developer who typed ten sentences and walked away, with agents doing the rest.
That requires trusting the coordination system, which requires the system to have earned that trust through verified
smaller loops. What is Linus's smallest-possible closed loop — a Worker receiving a spec, executing it, and returning a
verifiable result — that Dan could run this week? Getting that loop working, even trivially, is more valuable than any
further planning.

**Question 4: What is the right fine-tuning target in Phase 6?** _Partially resolved (DEC-0043; see
[answered-questions.md](../../questions/answered-questions.md)):_ memory-mode-specific fine-tuning targets for Phase 6
are now planned — one fine-tune per memory mode (`stateless`, `session_stateful`, `project_stateful`) rather than a
single monolithic domain target. The original tension (genomics corpus vs. personal writing style vs. scientific Python)
is absorbed into this framing: the `project_stateful` mode target naturally covers KnowledgeBase-aware genomics
reasoning; the `stateless` mode target covers fast coding assistance. The DSPy BootstrapFewShot experiment (g11) adds a
third axis — DSPy-optimized in-context demonstrations can serve as training data for LoRA adapters, bridging the "which
domain" question via measurement rather than upfront choice. _(Entrepreneurial-calculus implications live in
[`entrepreneurship-synthesis.md`](entrepreneurship-synthesis.md).)_

**Question 5: Is the "Stop Staring at the Files" architectural clarity claim actually load-bearing for Dan's specific
situation?** The thread argues that task decomposition and architectural clarity are the scarce inputs as agents
improve. This is compelling, but Dan's situation has a specific wrinkle: his domain expertise (biochemistry, genomics,
environmental science) is itself scarce, independent of any architectural skill. The question is whether the
highest-leverage use of Maestro time is decomposing tasks for Workers, or whether it is applying domain expertise to
problems that Workers cannot touch — scientific interpretation, hypothesis generation, experimental design. These are
not the same. The answer shapes how Linus's Maestro/Worker boundary should be drawn.

**Question 6: Should the Phase 2a Worker spec format mandate a "verify loop" field, elevating the Anthropic Claude Code
team's self-sufficient-loops tip to a Linus convention?** The
[Anthropic-internal Claude Code playbook](../../context/notes/How-Anthropic-teams-use-Claude-Code_v2.pdf) treats the
verify loop (build / test / lint commands the agent runs as its own success signal) as the primary mechanism for
extending autonomous runtime without supervision. This is a stronger statement than Practice 4's plan-before-execution
discipline: it shifts the human attention point from up-front spec review to post-hoc result review, which only works if
the agent can self-detect failure. Adopting it as a Linus convention would mean every Worker spec carries an explicit
verify-loop block, and the orchestration layer refuses to mark a task done if the verify loop has not been exercised.
The open question is whether this fits Linus's task mix — coding tasks have a natural verify loop (build / test / lint),
but analysis / research / synthesis tasks (which dominate Dan's current usage) do not, and forcing a verify-loop field
on every spec might be ceremony without value for the latter class. Possible compromise: mandate the field for
code-producing Workers, make it optional with a structured rationale for analysis Workers, and record the mode in the
audit log alongside `memory_mode` and `cot_budget` (DEC-0031).

**Question 7: Of the 106 agent personas in [claude-code-guide](../repo-notes/claude-code-guide.md), which 5–10 map
cleanly onto Phase 3 Worker roles Linus actually needs?** The orchestration cluster (`agent-organizer.md`,
`context-manager.md`, `multi-agent-coordinator.md`, `workflow-orchestrator.md`, `task-distributor.md`) is the most
directly relevant external precedent for the Phase 3 spawner Role catalogue (DEC-0050) and is the right starting quarry.
Should `docs/specs/phase3-spawner.md` seed its initial Role catalogue from those five, plus a small set of
domain-specific roles drawn from Dan's actual workflow (a `bioinformatics-engineer` analogue, a `paper-reviewer`
analogue, etc.), or should the catalogue be derived bottom-up from observed Worker invocations rather than top-down from
an external persona library? A subordinate question is whether the MUST/SHOULD/SHOULD-NOT rule grammar from the guide's
`guides/` collection deserves an ADR seed for selective lifting into Linus's own conventions on the most checkable rules
— line-length, commit format, smoke-test gating, hook bypass flow — without disturbing the prose-first voice that
CLAUDE.md §Writing style for docs mandates elsewhere.

---

_Document synthesized May 2026. Source threads archived in `context/threads/`._

---

## References

### Repo-notes

- [`agent-skills-for-context-engineering`](../repo-notes/agent-skills-for-context-engineering.md) — Muratcan Koylan's
  14-skill platform-agnostic curriculum on context engineering; cited as one of three independent appearances of the
  YAML-frontmatter progressive-disclosure skill format (Section 3 item 6 and Section 4a).
- [`autoresearch`](../repo-notes/autoresearch.md) — Andrej Karpathy's overnight LLM-directed ML-research loop with
  `program.md` as the human-edited skill sheet; cited as the canonical pattern for Phase 6d / Phase 7c experimentation
  loops.
- [`autoresearch-mlx`](../repo-notes/autoresearch-mlx.md) — Trevin Creator's MLX port of Karpathy's autoresearch loop;
  cited with an Integrate verdict for M1-Max-native execution as the entry point for the Phase 1 / Phase 6d autoresearch
  smoke run.
- [`caveman`](../repo-notes/caveman.md) — Julius Brussee's output-token compression skill plus cross-harness install
  matrix (~65–75% reduction at 100% technical accuracy); cited as the output-side complement to DEC-0032's in-context
  cap and the source of the `output_style` Worker-spec field proposal.
- [`claude-code-guide`](../repo-notes/claude-code-guide.md) — Zebbern's community-curated Claude Code reference (106
  agent personas, 29 SKILL modules, three CLAUDE.md guideline collections); cited as the most concrete external exemplar
  of community-organized Claude Code patterns and the seed quarry for the Phase 3 spawner Role catalogue.
- [`claude-squad`](../repo-notes/claude-squad.md) — smtg-ai's terminal supervisor running multiple coding-agent CLIs in
  parallel under tmux + git worktrees; cited as a Study verdict and one of the two Phase 1f orchestration evaluation
  finalists alongside Task Master AI.
- [`claude-task-master`](../repo-notes/claude-task-master.md) — Eyal Toledano's PRD-to-tasks-to-execution workflow
  (npm + fastmcp); cited as a Study verdict for adopting the pattern (task-spec JSON, three-role model split,
  complexity-then-expand, update-subtask breadcrumb) without vendoring the product.
- [`cline`](../repo-notes/cline.md) — VS Code agentic coding extension supporting Ollama + LM Studio backends; cited as
  the Worker-facing IDE harness for code-writing Workers while Claude Code remains the Maestro front-end.
- [`ClawBio`](../repo-notes/ClawBio.md) — ClawBio's 63 bioinformatics-native AI agent skills built on OpenClaw; cited as
  a worked example of the skills-as-shippable-bundle archetype, the SKILL.md conformance linter pattern, and the
  reproducibility-bundle output convention.
- [`codebase-memory-mcp`](../repo-notes/codebase-memory-mcp.md) — DeusData's static-C-binary code intelligence engine
  indexing repos into a tree-sitter knowledge graph with 14 MCP tools; cited with an Integrate verdict as a Phase 2a
  spike candidate for KnowledgeBase code-indexing.
- [`dlt`](../repo-notes/dlt.md) — dlthub's LLM-native data-pipeline library with 5,000+ source integrations; cited as a
  Phase 4 data-sovereignty enabler for offline ingestion of databases like NCBI and UniProt.
- [`dspy`](../repo-notes/dspy.md) — Stanford's program-not-prompt foundation-model framework with Signatures,
  Teleprompters, and BootstrapFewShot; cited with a Study verdict as the Phase 6 entry point bridging DSPy-optimized
  in-context demos to LoRA training demonstrations.
- [`extractthinker`](../repo-notes/extractthinker.md) — Enoch Tor's ORM-like Pydantic-contract document-extraction
  library; cited as Phase 3 scientific-paper-processing tooling for KnowledgeBase ingestion.
- [`fastmcp`](../repo-notes/fastmcp.md) — Prefect-maintained Python MCP framework; cited with an Integrate verdict
  (DEC-0045) as the committed Linus MCP framework on which in-house tool servers will be built.
- [`gptme`](../repo-notes/gptme.md) — gptme's terminal-first AI agent CLI with a plugin/skills/lessons architecture;
  cited with a Study verdict as the concrete answer to encoding Dan's bioinformatics expertise into Worker context via
  the lessons keyword-activation pattern.
- [`huginn`](../repo-notes/huginn.md) — Self-hosted event-driven automation platform with Agent/Event DAGs in a
  scheduler loop; cited with a Study verdict as the orchestration-reference pattern for Phase 2a dispatch design.
- [`lmnr`](../repo-notes/lmnr.md) — Laminar's full-stack AI observability platform (Rust/Next.js/Python +
  OpenTelemetry); cited with a Study (Phase 5+) verdict and a Phase 2a instrumentation recommendation (OTel from day
  one).
- [`markdownify-mcp`](../repo-notes/markdownify-mcp.md) — Glama AI's MCP server wrapping Microsoft `markitdown` to
  convert PDFs, images, audio, and Office documents to Markdown; cited as Phase 2 / Phase 3 KnowledgeBase ingestion
  tooling.
- [`promptfoo`](../repo-notes/promptfoo.md) — Promptfoo's open-source LLM eval + red-teaming CLI/library; cited as the
  Phase 2 SAFETY.md sandbox-escape-testing infrastructure.
- [`pydantic-ai`](../repo-notes/pydantic-ai.md) — The Pydantic team's type-safe agent framework with `Agent`,
  `RunContext`, and `@tool` primitives; cited with an Integrate (Phase 2a) verdict as the orchestration base abstraction
  for Linus Workers.
- [`rendergit`](../repo-notes/rendergit.md) — Karpathy's static-HTML repo flattener for LLM context paste; cited with a
  Watch verdict for Phase 5+ repo-to-hosted-Claude architectural reviews.
- [`superpowers`](../repo-notes/superpowers.md) — obra/superpowers methodology and plugin system enforcing spec-first /
  TDD / subagent-driven workflows; cited as the discipline layer of the three-layer g11 Worker stack (pydantic-ai +
  superpowers + gptme).
- [`vanna`](../repo-notes/vanna.md) — Vanna 2.0's natural-language-to-SQL agent platform with user-aware permissioning;
  cited as the prior-art pattern for Phase 3 structured-dataset query skills over Dan's genomics data.

### Paper-notes

- [`Letta-2310.08560`](../paper-notes/Letta-2310.08560.md) — MemGPT paper (Packer, Wooders et al.); cited via the
  caveman fold-in's pointer to the Letta paper-note's Open Question 7 on brevity-improves-accuracy and Toolformer corpus
  additions.
