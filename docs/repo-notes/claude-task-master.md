# claude-task-master (`eyaltoledano/claude-task-master`)

## 1. Purpose and scope

claude-task-master ("Taskmaster") is an opinionated **PRD-to-tasks-to-execution** workflow for AI-driven coding,
distributed as the npm package `task-master-ai` and an MCP server (`fastmcp`-based, 36+ tools). The intended motion:
write a Product Requirements Document, run `task-master parse-prd` to decompose it into a typed task graph in
`.taskmaster/tasks/tasks.json`, then iterate inside Cursor / Windsurf / VS Code / Claude Code via either the CLI or the
MCP tools (`next_task`, `expand_task`, `update_subtask`, `set_task_status`). It also exposes a separable **main /
research / fallback** model-role layer with provider plugins for Anthropic, OpenAI, Google, Perplexity, xAI, OpenRouter,
Mistral, Groq, Bedrock, Azure, Ollama, and a `claude-code` provider that piggybacks on Dan's existing Claude
subscription with no API key. For Linus this is the repo named in **Phase 1f's PRD-to-tasks evaluation**, paired with
claude-squad as the two finalists; the resolved planning position is to **adopt the PRD-to-tasks _pattern_ as a Linus
skill, not re-implement the product**, so this note exists to pin down what that pattern actually is.

## 2. Architecture summary

Node.js >= 20, TypeScript, ESM, organized as a Turbo monorepo: `packages/tm-core` (all business logic — task domain,
parsing, complexity analysis, dependency resolution, ID parsing for `1.2.3` and Jira-style `HAM-123` IDs),
`packages/tm-bridge`, `packages/tm-profiles` (per-editor rule packs: Cursor, Windsurf, Roo, VS Code, Claude Code),
`packages/ai-sdk-provider-grok-cli`, `apps/cli` (Commander-based; thin presentation), `apps/mcp` (FastMCP server; thin
presentation), `apps/extension` (planned VS Code extension). The architectural rule enforced in the upstream CLAUDE.md
is strict: **all business logic lives in `tm-core`; CLI and MCP are display-only**. State lives entirely in
`.taskmaster/`: `config.json` holds the three model roles plus globals (`defaultNumTasks: 10`, `defaultSubtasks: 5`,
`ollamaBaseURL`, `defaultTag: "master"`); `state.json` tracks the current "tag" (named workstream — branches of the task
tree, e.g. `master`, `loop`, `tm-core-phase-1`); `tasks/tasks.json` is the canonical task DB grouped by tag; individual
`task_NNN_<tag>.txt` files are derived. Task fields: `id`, `title`, `description`, `status` (`pending` / `in-progress` /
`done` / `deferred` / `cancelled` / `blocked`), `dependencies[]`, `priority`, `details`, `testStrategy`, `subtasks[]`.
The MCP server supports tiered loading via `TASK_MASTER_TOOLS=core|standard|all` (7 / 15 / 36 tools, ~5k / 10k / 21k
context tokens) — an explicit acknowledgement that 36 tools is too many to keep in a small worker's context.

## 3. What's reusable in Linus

The **task-spec schema** (id / deps / status / details / testStrategy / subtasks) is directly portable and is
essentially what a Linus "PRD-to-tasks" skill should emit; the Linus version can drop tags, the multi-provider router,
and the 36-tool MCP surface and still capture the value. The **three-role model split** — main does decomposition, a
separate `research` role queries Perplexity for fresh context, `fallback` covers main failure — is a clean idea worth
porting into Linus's worker routing (Phase 2/3): it cleanly separates "thinking model" from "browse-the-web model"
without the caller having to know which is which. The **complexity-analysis pass** (`analyze-complexity` then
`expand --all`) is the loop Karpathy's autoresearch repo also uses — score before you decompose, not after — and is the
sort of thing Linus can lift as a one-paragraph algorithm. The **`update_subtask` "log notes as you go" pattern** is a
low-cost breadcrumb mechanism that pairs well with Linus's audit-log requirement in ARCHITECTURE.md.

Compared with **claude-squad** (the other Phase 1f candidate, which is parallel-terminal/tmux fan-out of multiple Claude
Code sessions against git worktrees), Taskmaster occupies a complementary, not overlapping, slice: claude-squad
parallelizes _execution_ of independent tasks across sessions; Taskmaster handles the _decomposition and tracking_ that
should happen _before_ those sessions are spawned. The honest read of Phase 1f is "they aren't really competitors";
Linus likely wants the Taskmaster pattern as the planner and the claude-squad pattern as the runner. Compared with
**workgraph** (the other task-graph-shaped sibling in Group 7), the Taskmaster graph is hand-tracked-with-AI-help and
shallow (tasks + subtasks + sub-subtasks, dependency edges); workgraph proposes a real DAG executor — the Taskmaster
data model is good enough for Phase 2 Linus and a real DAG can be deferred until orchestration demands it.

## 4. What's inspiration only

The Cursor-first MCP install path, the npm-distribution model (`npx -y task-master-ai`), the Hamster Studio cloud
extension, the Sentry telemetry, the changeset/turbo release machinery, the per-editor profile packs (Cursor / Windsurf
/ Roo / Q Developer), and the 36-tool MCP surface are all product-distribution choices irrelevant to a single-user local
Linus. The MIT-with-Commons-Clause license also forbids "competing products," which formally rules out vendoring even if
it were tempting. The provider-plugin sprawl (~14 `@ai-sdk/*` providers as direct dependencies) is exactly the fan-out
Linus wants to _avoid_ — Linus routes through Ollama / pmetal / Claude Code, not 14 hosted APIs.

## 5. What's incompatible or out of scope

Node-monolith with a heavy dep tree (Express, Helmet, AWS SDK creds, Sentry, Supabase, JWT, fs-extra, lockfiles,
`@anthropic-ai/mcpb`) — pulling this in as a dependency would balloon the Linus footprint and cross the "single-language
Python+Rust" boundary in CLAUDE.md. The "tags as named workstreams" model is a soft-fork-of-the-task-DB abstraction that
competes with git branches and would conflict with BRANCHING.md's branch-discipline contract. The mandatory
`.taskmaster/` directory, `config.json` schema, and `tasks.json` write-locking via `proper-lockfile` are all
load-bearing for Taskmaster's product but would be foreign objects in the Linus tree.

## 6. Recommendation: **Study**

Read the schema, port the pattern, do not vendor and do not depend. Concretely: (a) write the Phase 1f comparison ADR
naming Taskmaster's task-spec JSON shape and three-role model split as the parts Linus adopts; (b) implement a thin
"PRD-to-tasks" skill in `src/linus/skills/` that emits the same JSON shape into `experiments/<task>.json`, callable from
Maestro and from a Worker; (c) close the Phase 1f deliverable by documenting that claude-squad and claude-task-master
are complementary (planner vs. runner), not finalists for the same slot.

## 7. Questions for Dan

- **Phase 1f framing.** The brief treats claude-squad and claude-task-master as competing candidates, but they target
  different stages (decompose vs. parallel-execute). Is the Phase 1f deliverable better written as "adopt both patterns,
  neither product," or do you want a single winner declared?
- **Three model roles, or more?** Taskmaster pins three: main / research / fallback. Linus's worker layer plausibly
  needs at least four — main (Qwen2.5-Coder), research (an external API or Perplexity for facts), fallback, and a
  cheap/fast triage model (Mistral-7B or Bonsai). Codify three roles or design for N from the start?
- **Task-state location.** Taskmaster centralizes everything in `.taskmaster/`. Should Linus's PRD-to-tasks skill output
  to `experiments/<task-id>/`, to a SQLite-backed session store (per ARCHITECTURE.md), or to git-tracked JSON next to
  the spec — and which of those plays best with the agent-branch workflow in BRANCHING.md?
- **MCP tool count discipline.** Taskmaster's `core` tier is 7 tools at ~5k tokens; their default of 36 already costs
  ~21k tokens. For Linus's eventual MCP surface, do we adopt a hard cap (say, 10 tools per worker session) and force
  composition, or accept higher token cost in exchange for breadth?
- **Differentiator gap.** I could not identify a meaningful technical differentiator that argues for Taskmaster _over_
  reimplementing the pattern in Linus — every reusable idea (schema, three roles, complexity-then-expand) is small
  enough to lift in a day. Is there a Taskmaster feature you specifically want that I should re-evaluate before closing
  the ADR?
