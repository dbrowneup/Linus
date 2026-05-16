# symphony (`openai/symphony`)

## 1. Purpose and scope

symphony is OpenAI's published-2026 **engineering-preview harness** for coding-agent work that reframes the
human/agent relationship from "supervise the agent while it codes" to "manage the work the agent does." It is a
long-running daemon that polls an issue tracker (Linear in v1; the spec is tracker-agnostic), pulls in candidate
tickets, opens an isolated per-issue workspace, runs a coding agent (Codex via app-server mode in the reference
implementation) against the ticket inside that workspace under a repo-owned `WORKFLOW.md` policy file, and produces
**proof of work** as the human-facing artifact — CI status, PR review feedback, complexity analysis, walkthrough
videos. The repo ships two things: a **language-agnostic `SPEC.md`** that is the canonical interface definition (RFC
2119 normative language, full domain model, lifecycle, error taxonomy), and an **Elixir reference implementation**
under `elixir/` that operationalizes the spec end-to-end (~3,400 LOC Elixir + tests + a sample `WORKFLOW.md`). The repo
explicitly invites consumers to "build Symphony in a programming language of your choice" against the SPEC.md rather
than vendor the Elixir reference, which positions symphony as a protocol-with-reference rather than a
software-product-with-API. The author tagline frames this as the successor step to "harness engineering" (the OpenAI
discipline of designing the agent harness, not just the model prompt) and the README is unusually direct: "Symphony is
a low-key engineering preview for testing in trusted environments." For Linus, this is a **notable industry signal**
that OpenAI is publishing harness-engineering framing as durable public artifact, and the SPEC.md is the cleanest
modern reference for how a polling-issue-tracker-plus-isolated-workspace harness should be structured. It is not a
substrate to vendor — it is a coding harness (DEC-0017 harness plurality) whose right relationship to Linus is
"another harness Linus's orchestration backend could plausibly consume against, if a Linus user wanted Linux-style
issue-driven autonomous work."

## 2. Architecture summary

The deliverable has two artifacts. **`SPEC.md`** is a 30k-token, language-agnostic, RFC-2119-conformant specification
of the symphony service. **`elixir/`** is the working reference implementation: an Elixir/OTP mix project (`mix.exs`),
a sample `WORKFLOW.md`, a `Makefile`, mise-based toolchain pinning (`mise.toml`), a `config/` directory of OTP releases
configuration, a `lib/` directory of the actual service, a `priv/` directory for runtime data, and a `test/`
directory. The licensing is Apache-2.0 with a NOTICE file. The README's two-option framing — "Tell your favorite
coding agent to build Symphony in a programming language of your choice" or "use our experimental reference
implementation" — establishes that the spec is the contract; the Elixir impl is just one materialization of that
contract.

The **SPEC.md architecture** decomposes symphony into six layers (per SPEC §3.2). The **Policy layer** lives in the
target repo's `WORKFLOW.md` file: YAML front matter (the typed config — tracker kind, polling interval, workspace
root, hooks, concurrency limits, agent command, approval policy, sandbox policy) followed by a Markdown prompt body
that is rendered with `{{ issue.identifier }}`, `{{ attempt }}`, and similar Jinja-style placeholders. The **Config
layer** parses the front matter into typed runtime settings (poll interval, active/terminal issue states, agent
executable/args/timeouts, workspace hooks) and applies environment-variable indirection plus defaults. The
**Coordination layer** is the orchestrator: a polling loop on a fixed cadence, in-memory authoritative state, retry
queue, reconciliation against the issue tracker, bounded concurrency (default `max_concurrent_agents: 10`,
`max_turns: 20` per the sample WORKFLOW.md). The **Execution layer** is the workspace manager plus the agent runner:
filesystem lifecycle (one directory per issue identifier, sanitized to `[A-Za-z0-9._-]` characters with everything
else replaced by `_`), `after_create` and `before_remove` hooks that the workflow author writes in shell, and the
coding-agent subprocess running over the Codex app-server protocol. The **Integration layer** is the issue-tracker
client (Linear adapter in v1; the spec is structured so a GitHub Issues / Jira / Plane adapter is a swap). The
**Observability layer** is structured-logs-required plus an OPTIONAL status surface (TUI, dashboard, both).

The **core domain model** (SPEC §4.1) is named-and-typed in eight entities: `Issue` (normalized tracker record:
`id`, `identifier`, `title`, `description`, `priority`, `state`, `branch_name`, `url`, `labels`, `blocked_by`,
timestamps); `WorkflowDefinition` (parsed `WORKFLOW.md`: `config` map and `prompt_template` string); `Service Config`
(typed runtime view); `Workspace` (path + workspace_key + created_now boolean); `RunAttempt` (one execution: issue
ID, identifier, attempt number, workspace path, started_at, status, error); `LiveSession` (agent-subprocess state:
`session_id = <thread_id>-<turn_id>`, last event, token counts both observed-by-agent and reported-back, turn_count);
`RetryEntry` (issue ID + identifier + attempt + due-at monotonic timestamp + timer handle + error); `OrchestratorState`
(authoritative in-memory state: `running` map, `claimed` set, `retry_attempts` map, `completed` set, `codex_totals`,
`codex_rate_limits`). The naming discipline is precise: `Issue ID` is the tracker-internal key used for lookups;
`Issue Identifier` is the human-readable ticket key (`ABC-123`); `Workspace Key` is the sanitized identifier used as
directory name; `Session ID` is the composed `<thread_id>-<turn_id>` from agent telemetry. This explicit ID vocabulary
is the cleanest worked example in the harness-cluster of how to keep tracker-side, filesystem-side, and agent-side
identifiers straight.

The **`WORKFLOW.md` contract** (SPEC §5) is the load-bearing innovation. It is a single in-repo file that owns both
the workflow policy (the prompt body the agent sees) and the runtime configuration (the YAML front matter). The
front-matter schema is precisely specified: `tracker` (kind + active_states + terminal_states + project_slug),
`polling` (interval_ms), `workspace` (root + hooks.after_create + hooks.before_remove), `agent` (max_concurrent_agents
+ max_turns), and `codex` (command + approval_policy + thread_sandbox + turn_sandbox_policy). The prompt body uses
Liquid-style templating; the sample workflow renders against `{{ issue.identifier }}` and a `{% if attempt %}` block
for retry context. The discipline rule from the spec: workflow policy lives in-repo so teams version the agent prompt
and runtime settings alongside the code; no external config service, no operator-side state that the orchestrator
trusts.

The **orchestrator's poll/dispatch lifecycle** (SPEC §6) is the heart of the spec. On each poll tick, the orchestrator
fetches candidate issues in active states, applies eligibility filters (issue must not be blocked, not already
running, not claimed), sorts by priority + age, dispatches up to `max_concurrent_agents` slots, and tracks each
dispatched issue in the `claimed` set. While an agent is running, the orchestrator subscribes to agent events,
updates `LiveSession` state, and reconciles against tracker state (if the issue moves to a terminal state mid-run, the
orchestrator stops the agent; if the issue moves out of active states, the agent is released without retry). On
failure, the orchestrator schedules a `RetryEntry` with exponential backoff. On success, the issue is added to
`completed` for bookkeeping and the workspace is preserved across runs (deterministic per-issue workspace path, so
the same issue resuming on a different daemon instance lands in the same directory). Workspace cleanup happens for
issues whose state moves to a terminal state.

The **agent-runtime contract** is via the **Codex app-server mode** in the reference implementation: a `codex
... app-server` subprocess that exposes a control channel for the orchestrator to send turn-start instructions and a
stream of events back to the orchestrator (turn started, message produced, tool used, token usage updated, rate-limit
status, turn ended). The orchestrator does not parse the model's output directly; it just consumes the structured
event stream. The sample WORKFLOW.md `codex` block specifies `approval_policy: never` (the agent acts without
operator confirmation), `thread_sandbox: workspace-write` (the agent can write inside the workspace directory but not
outside), and `turn_sandbox_policy: workspaceWrite` (per-turn confirmation of the workspace-write boundary). These are
the four trust-and-safety knobs the workflow author tunes per-deployment; the spec is explicit that "trust and safety
posture" is implementation-defined and must be documented per deployment.

The **proof-of-work surface** (named in the README's framing, partially formalized in SPEC §8 Observability) is what
the agent emits and the human consumes: CI status (from the tracker integration, populated by the agent committing
and pushing branches that have CI hooked up upstream), PR review feedback (from human and bot reviewers on the PR the
agent opens), complexity analysis (static-analysis output the workflow prompt instructs the agent to produce),
walkthrough videos (the agent records or generates them per the workflow prompt). The orchestrator does not produce
proof-of-work directly; it just runs the agent in an environment where these artifacts can be produced and surfaces
the agent's structured events.

The **Elixir reference implementation** is a relatively small Mix project (one main app under `lib/`) that
materializes the spec on top of Elixir/OTP's process-supervision and concurrency primitives. The `Makefile` shows the
top-level workflow (`make`, `make test`, deployments via OTP releases); `mise.toml` pins the Elixir/Erlang versions
and the `mix.exs` declares dependencies. The implementation choice is interesting: Elixir/OTP is excellent for
long-running supervised concurrency (a polling daemon spawning workspace-per-issue agent processes maps cleanly onto
the actor model), and the choice to publish in Elixir is itself a small statement about what kind of language fits
this problem shape. The `lib/symphony/` modules cover the issue-tracker client, workflow loader, orchestrator,
workspace manager, agent runner, and status surface — the same six SPEC §3.1 components. The repo's `priv/`,
`config/`, and `test/` directories carry runtime config, OTP releases configuration, and a relatively small test
suite. Other implementations would mostly differ in the concurrency primitives (Python asyncio + watchdogs, Go
goroutines + a supervisor, Rust tokio + a state-machine actor) and in the issue-tracker adapter; the orchestrator
state machine and the workspace lifecycle are well-specified enough that ports are tractable.

## 3. What's reusable in Linus

symphony's contribution to Linus is **design-reference and protocol-shape**, not substrate or code. The Linus
orchestration backend is single-user and Maestro/Worker-shaped, not multi-developer-team-and-issue-tracker-shaped;
adopting symphony as the Linus orchestration layer would invert the scope (DEC-0020 orchestration scope is bounded).
But several specific patterns from SPEC.md transfer cleanly to Linus's existing commitments.

**Phase 2a — `WORKFLOW.md`-style policy-in-repo as the Linus task-spec home (DEC-0050, DEC-0051).** symphony's
load-bearing innovation is keeping the workflow policy in the target repo as a single file with typed YAML front matter
plus a templated prompt body. The Phase 3 Linus spawner spec ([`phase3-spawner.md`](../specs/phase3-spawner.md))
currently leaves the task-spec format open; per the [goose repo-note](goose.md) §3 Open Question 3 the leading
candidate is a hybrid of goose's Recipe shape (typed parameters + JSON-schema response + sub_recipes) and Letta's
Agent File shape (full agent serialization). symphony adds a **third reference**: a single in-repo file with typed YAML
front matter for runtime configuration and a Liquid-templated prompt body for the agent-facing instructions. The
Linus-applicable lesson: **the task-spec lives in the repo being operated on, not in the orchestration backend**, so
the team versions the policy alongside the code. For Linus single-user, "the team" is Dan and "the repo" is the
project Linus is acting against; this maps cleanly onto a per-project `LINUS.md` file (or per-task spec under
`linus/tasks/`) that the Linus orchestration layer reads at task dispatch time. The Phase 3 spawner-spec ADR should
name symphony's WORKFLOW.md alongside goose Recipe and Letta Agent File as the three reference task-spec shapes; the
Linus-native shape is a hybrid that the spec should explicitly motivate against all three.

**Phase 2a — explicit ID-vocabulary discipline (issue ID / issue identifier / workspace key / session ID).** SPEC §4.2
formalizes a discipline rule that the rest of the harness cluster does not articulate this cleanly: tracker-internal
IDs are for map lookups, human-readable identifiers are for logs and workspace naming, sanitized identifiers are for
filesystem directory names, and composed session IDs are for agent-subprocess telemetry. Linus's Phase 2a session-store
(per the workgraph JSONL convention in CLAUDE.md) and audit log will need the same discipline: a Worker-call ID for
internal joins, a Task identifier for human logs, a workspace key for any per-task sandbox directory, a Session ID for
the audit-log row. Cribbing symphony's vocabulary into the Phase 2a session-store spec is a small, concrete
discipline lift that prevents the ID-confusion bugs that arise when these collapse to a single string. Worth one
paragraph in the Phase 2a session-store spec.

**Phase 2a — workspace as a first-class concept with deterministic-path and per-issue isolation (DEC-0022,
SAFETY.md).** symphony's workspace manager creates one directory per issue, derives the directory name
deterministically from the sanitized issue identifier, preserves the workspace across runs (resuming on a different
daemon instance lands in the same directory), and runs `after_create` / `before_remove` hooks at lifecycle events.
CLAUDE.md already commits to the worktree-fan-out discipline for parallel agent work; symphony adds the **per-task
isolation** discipline as a complementary pattern for Phase 2a sequential Worker dispatch — every long-running task
gets its own workspace directory under `~/.linus/workspaces/<task-key>/`, the path is deterministic so a Worker
resuming after interruption lands in the same place, and the orchestration layer runs setup/teardown hooks at
workspace creation and termination. This is the Linus analogue of symphony's per-issue workspace and is the right
shape for Phase 2a "Worker dispatch with isolation" without needing the full worktree-fan-out machinery.

**Phase 2a — observability discipline: structured logs required, status surface optional (DEC-0026, SAFETY.md).**
SPEC §8 makes the discipline rule explicit: structured logs MUST be emitted, a human-facing status surface (TUI,
dashboard) is OPTIONAL. The Linus equivalent already commits to the audit-log JSONL at `~/.linus/audit.jsonl` per
ARCHITECTURE.md; symphony's framing is the right discipline for the Phase 5+ status-surface question (openclaw or
similar): structured logs are the substrate, the status surface renders the substrate. The discipline keeps the
orchestration layer narrow (it produces logs; the rendering is downstream); this fits DEC-0020's bounded-orchestration-
scope commitment cleanly.

**Phase 3 — retry-with-backoff plus tracker-reconciliation as the Worker-failure-handling pattern.** symphony's
orchestrator handles transient agent failure by scheduling a `RetryEntry` with exponential backoff and a
`due_at_ms` monotonic timestamp, plus reconciliation against tracker state on every poll tick (if the issue's tracker
state changes mid-run, the running agent is stopped or released). The Linus Phase 3 spawner (DEC-0050) will need an
analogous shape: Worker failure recovery via retry-with-backoff, plus reconciliation against the parent's intent (if
the Maestro cancels the task, the running Worker is terminated; if the Maestro changes its mind about the task scope,
the Worker is restarted with the new scope). symphony's state-machine spec is the cleanest published reference for
this; the Phase 3 spawner-spec ADR should crib the retry-state-machine shape.

**Phase 5+ — harness plurality reference: symphony joins goose / claw-code-local / openclaw as a Rust+/Elixir+ harness
example (DEC-0017).** Per the [goose repo-note](goose.md) §3 and the harness-cluster
[g7-harnesses synthesis](../syntheses/repo-clusters/g7-harnesses.md), Linus's Phase 5+ posture is "multiple harnesses
coexist, each has a role, Linus's orchestration backend is the common consumer downstream of them all." symphony is
a non-Rust, non-claw-shaped harness (Elixir/OTP, issue-tracker-driven, autonomous-daemon) and broadens the cluster's
coverage usefully. The cross-language proof — symphony in Elixir, goose in Rust, claw-code-local in Rust, openclaw in
TypeScript, Cline in TypeScript — confirms that "the harness language is orthogonal to the orchestration backend's
language" is the right architectural separation, which is the foundational assumption behind DEC-0017 + DEC-0020.

**Phase 5+ — issue-tracker integration as a Phase 5+ Linus capability candidate.** Linus is currently Dan-as-Maestro
driven (interactive Maestro/Worker dispatch). symphony demonstrates a **second mode**: tracker-driven autonomous
dispatch (poll Linear, pull tickets, dispatch agents, surface proof-of-work). At Phase 5+ scale (or before, if a
single-user issue tracker like Linear Personal is in scope), the symphony pattern is the canonical reference for how
to add tracker-driven autonomous dispatch to Linus without changing the Maestro/Worker semantics — tracker-driven mode
is just a different upstream caller of the same `/v1/chat/completions` and Worker-spawn endpoints. This is genuinely
Phase 5+ territory; the symphony reference is the right design anchor for the eventual ADR.

**Sample WORKFLOW.md as a worked trust-and-safety configuration reference for SAFETY.md.** The sample WORKFLOW.md in
`elixir/WORKFLOW.md` sets `approval_policy: never`, `thread_sandbox: workspace-write`, `turn_sandbox_policy:
workspaceWrite`, and `max_turns: 20`. These are four specific knobs at four specific values that operationalize
"trusted environment for autonomous coding-agent work." Linus's SAFETY.md autonomy-tier graduation will need analogous
knobs at analogous values; symphony's sample is the cleanest published reference for what a "trusted, autonomous,
sandboxed" configuration looks like in practice. Specifically: `approval_policy: never` is the Tier-3 autonomy state;
`thread_sandbox: workspace-write` is the SAFETY.md sandbox-policy directive; `max_turns: 20` is a per-task budget cap.
The SAFETY.md text should name symphony's sample as a worked reference when the autonomy-tier graduation gets a Phase
3+ rewrite.

## 4. What's inspiration only

The **Linear-specific tracker adapter** is symphony's v1 integration. Linus has no Linear dependency, and the Linear
API is specific (GraphQL, project slugs, state machine semantics that match Linear's product). The general pattern —
"normalize tracker payloads into a stable issue model" — is portable; the Linear-specific code is not. The right Linus
posture is to **defer** any tracker integration to Phase 5+ (Linus is single-user; Dan does not need a tracker-driven
loop at v0), and when the time comes, GitHub Issues or a local plaintext-task-file is the more likely v1 tracker than
Linear.

The **Codex app-server protocol** as the agent-runtime contract is OpenAI-specific. The Linus equivalent is the
OpenAI-compatible HTTP boundary (DEC-0005) plus the MCP host (DEC-0018, DEC-0045); the Codex-specific event stream
shape is not directly relevant. The structural lesson — "the orchestrator consumes a structured event stream from the
agent subprocess, not the model's raw output" — is portable and is already implicitly true for the Linus
`/v1/chat/completions` event stream. Document the lesson; do not lift the Codex protocol.

The **Elixir/OTP reference implementation** is well-built but not portable in detail. The actor-model concurrency
primitives map onto Python asyncio or Rust tokio with significant translation; the OTP-supervision idioms have no
direct Python analogue. The right relationship is "read the Elixir code as worked validation that the SPEC.md is
implementable end-to-end, then implement in the Linus stack against the SPEC.md directly." Per DEC-0027 multi-language
stance, Linus core orchestration is Python; the Linus-equivalent implementation would be a Python asyncio service plus
a SQLite + JSONL audit log (per DEC-0029) — a 4-6 week build that the SPEC.md specifies cleanly.

The **engineering-preview / trusted-environments framing** ("Symphony is a low-key engineering preview for testing in
trusted environments") is a soft-launch posture that suggests the API surface may change before v1. For Linus's
purposes, the SPEC.md is durable enough to cite as a design reference even if the implementation details shift; the
specific `WORKFLOW.md` schema and the orchestrator state-machine shape have inertia that survives implementation
churn. Worth noting that any production-grade Linus implementation against symphony's spec should track the spec
across versions, not pin to v1.

The **proof-of-work artifacts (CI status, PR review feedback, complexity analysis, walkthrough videos)** are framing
shorthand for "the agent produces durable, human-reviewable artifacts as the deliverable." Linus's Phase 2a Worker
output is conceptually similar (typed `AgentReport` per DEC-0051; structured tool-call results; episodic-memory
writes) but the artifact types differ — Dan's Workers do scientific analysis, code review on biology pipelines, paper
synthesis, not pull-request-against-Linear-ticket. The framing is a useful prompt for "what does proof-of-work look
like for each Linus skill" but does not transfer artifact-by-artifact.

The **`max_concurrent_agents: 10` default** is a multi-developer-team-scale default. Linus on the M1 Max 32 GB
hardware can plausibly run 2-4 concurrent local Workers at most under the current Worker-base (Qwen3), constrained
by unified memory pressure and Ollama context-switching overhead. The default is not load-bearing in either
specification — the SPEC.md treats it as implementation-defined and the workflow file lets the user override it — but
the cultural reference point (10 concurrent agents as "normal") is not the right calibration for Linus's hardware
ceiling.

## 5. What's incompatible or out of scope

**symphony is a coding-agent harness, not an orchestration backend (DEC-0017 harness plurality, DEC-0020 orchestration
scope is bounded).** Same structural relationship as goose, claw-code, claw-code-local, and Cline: symphony **consumes**
a coding-agent runtime (Codex) and a tracker integration (Linear) to produce a working agent loop; Linus **is** the
orchestration backend that the next-generation symphony-equivalent could consume. Inverting this relationship
(adopting symphony as the Linus orchestration substrate) would expand the Linus scope to include tracker integration,
issue-eligibility filtering, retry queuing, multi-developer-team concurrency, and trusted-environment policy — none of
which fit Linus's bounded scope. The right relationship: symphony is downstream of Linus, not parallel to it.

**The issue-tracker-driven autonomous-dispatch loop is conceptually different from Linus's interactive Maestro/Worker
pattern.** symphony assumes the human pushes work into a tracker and the daemon pulls work out and dispatches agents
autonomously. Linus's current pattern is Maestro (Dan + hosted Claude) dispatches tasks interactively to Workers, who
report back via the Maestro/Worker protocol. These are not the same workflow shape. At Phase 5+, Linus may add a
tracker-driven autonomous mode as a Phase 5+ capability (per §3 Phase 5+ above), but the v0 + v1 surface is
interactive-only and the symphony pattern is genuinely for a later phase.

**The Elixir choice for the reference implementation is not a fit for the Linus stack.** Linus is Python-first (DEC-0027
multi-language stance: Python is the core orchestration language; Rust, TypeScript, Bash acceptable per-component when
they fit). Elixir is a different language family, with a different concurrency model (BEAM/OTP supervision), a different
package manager (Hex), and a different toolchain (mix). The Elixir code is not portable to Linus; only the SPEC.md is
portable, and only as a design reference. The Linus implementation against the spec would be a Python asyncio service.

**The trust-and-safety posture is fundamentally permissive by default.** The sample WORKFLOW.md sets
`approval_policy: never` (no operator confirmation on agent actions), `thread_sandbox: workspace-write` (the agent
can write inside the workspace, including arbitrary git operations like push to remote branches), and `max_turns:
20` (twenty agent turns before the orchestrator forces termination). For a Linus single-user posture this is
plausible; for a multi-user / multi-tenant deployment this is too permissive. The SPEC.md is honest about this: trust
and safety posture is "implementation-defined" and must be documented per deployment. Linus's SAFETY.md autonomy-tier
graduation is the right framework for what trust-and-safety posture is appropriate at each phase; symphony's defaults
are the Tier-3 reference, not the Linus default.

**The Codex app-server protocol is OpenAI's coding-agent product surface, not a public open standard.** symphony's
agent-runtime contract is via Codex's app-server mode; the Codex CLI is a paid OpenAI product, not an open
implementation. For Linus's local-first posture (DEC-0027 public APIs only; the Worker is Qwen3 or a future fine-tuned
local base), the Codex-specific contract does not apply. The structural pattern (orchestrator consumes structured
events from the agent subprocess) ports cleanly to Ollama or MLX-LM via the OpenAI-compatible HTTP boundary; the
Codex-specific event names and shapes do not.

**The single-file `WORKFLOW.md` policy convention assumes the agent runs against the repo whose `WORKFLOW.md` it
finds.** This is the right shape when the orchestrator's job is "act on this repo's tickets" — the workflow file lives
in the target repo, the agent runs against that repo. For Linus's task taxonomy (the same Linus instance handles many
projects across many repos plus a lot of work that does not have a per-repo target — paper synthesis, KB queries,
research questions, biology skill invocations), the single-`WORKFLOW.md` shape is too narrow. A per-task spec under
`linus/tasks/<task-id>.md` plus a project-level `LINUS.md` for the cross-project policy is the right Linus shape;
symphony's contribution is the discipline rule (the policy lives in the repo, not in the orchestrator), not the
specific file layout.

**`max_turns: 20` is a hard turn budget that does not compose with `cot_budget` or `memory_mode` (DEC-0031).**
symphony's per-task turn budget is a fixed integer cap; Linus's per-Worker call already has more sophisticated budget
primitives via the `cot_budget` field (logarithmic / linear / polynomial per DEC-0031) and the `memory_mode` field
(stateless / session_stateful / project_stateful). The simple turn-count cap is a useful coarse safety belt but does
not subsume the Linus dispatch struct's richer shape; Linus should keep DEC-0031's primitives and use the turn-count
cap only as a hard upper bound (e.g. `max_turns_hard_cap: 100` independent of `cot_budget`).

## 6. Recommendation: **Watch + Study**

Read `SPEC.md` end-to-end as the cleanest published reference for a polling-tracker-plus-isolated-workspace harness
spec, paying particular attention to §4 (Core Domain Model — the eight entities and the ID-normalization rules), §5
(Workflow Specification — the `WORKFLOW.md` schema and the templating contract), §6 (Orchestration Lifecycle — the
poll/dispatch/reconcile state machine and the retry shape), and §8 (Observability — the structured-logs-MUST plus
status-surface-OPTIONAL discipline rule). Skim `elixir/lib/symphony/` to validate the spec is end-to-end implementable
without surprises; the Elixir code is small and well-organized. Skim `elixir/WORKFLOW.md` as a worked configuration
reference for a trusted-environment autonomous deployment.

**Watch** because symphony is OpenAI's industry signal that "harness engineering" is a durable discipline worth
publishing public specifications for, and the spec will likely evolve over the next 12-18 months. The cross-vendor
implication — Anthropic published claw-code and the harness-engineering blog post that symphony's README references;
OpenAI now published symphony with `https://openai.com/index/harness-engineering/` in the README — is that the harness
is the layer of public-spec convergence between the two leading model vendors. For Linus, this is the same kind of
signal the [Letta repo-note](Letta.md) §3 (Anthropic-compatible HTTP shipping alongside OpenAI-compatible) and the
[goose repo-note](goose.md) §3 (full ACP server + client support) carry: the protocol landscape is moving plural, and
Phase 5+ Linus should plan accordingly.

**Study** the specific patterns above (§3 What's reusable in Linus): the `WORKFLOW.md`-style policy-in-repo idea as a
reference for the Phase 3 task-spec format alongside goose Recipe and Letta Agent File; the explicit ID-vocabulary
discipline for the Phase 2a session-store; the workspace-as-first-class-concept lesson for Phase 2a Worker isolation;
the structured-logs-required-status-surface-optional discipline for the observability surface; the retry-with-backoff
plus tracker-reconciliation pattern for Phase 3 Worker-failure handling. These are five small, concrete pattern lifts
that improve Linus's existing commitments without expanding scope.

Do **not** vendor symphony. Do **not** adopt it as the Linus orchestration backend. The architectural fit is wrong
(symphony is a harness, Linus is the backend; per DEC-0020 the orchestration scope is bounded) and the language fit is
wrong (Elixir/OTP vs. Python asyncio). The implementation-language differences mean even a "thin port" would be a
significant rewrite. The right relationship: read the spec, lift the patterns, ship the Linus implementation.

Cluster cell: [g7-harnesses](../syntheses/repo-clusters/g7-harnesses.md). symphony belongs in the harness cluster
alongside goose, claw-code-local, openclaw, Cline, claw-code, codebuff, semanticworkbench, and claude-task-master.
Within that cluster, symphony is the **issue-tracker-driven autonomous-dispatch entrant** — the same shape as
codebuff's planner/runner split (per the [g7-harnesses synthesis](../syntheses/repo-clusters/g7-harnesses.md)
discussion of claude-squad and claude-task-master as planner/runner finalists) but with the planner externalized
to an issue tracker rather than another agent. Cross-cluster: symphony's `WORKFLOW.md` policy-in-repo idea is also
relevant to the [agentic-systems-synthesis.md](../syntheses/agentic-systems-synthesis.md) discussion of agent task
specs (alongside goose Recipe and Letta Agent File per the comparative thread there).

Primary thematic home: [`../syntheses/agentic-systems-synthesis.md`](../syntheses/agentic-systems-synthesis.md), as
the cleanest modern published reference for an autonomous agent dispatch loop. Secondary thematic home:
[`g7-harnesses.md`](../syntheses/repo-clusters/g7-harnesses.md) for the harness-plurality framing.

## 7. Connections

The primary fold is into [`../syntheses/agentic-systems-synthesis.md`](../syntheses/agentic-systems-synthesis.md).
symphony is a notable industry signal that OpenAI is publishing harness-engineering framing as durable public
artifact, and the SPEC.md is the cleanest modern reference for a polling-tracker-plus-isolated-workspace agent
dispatch loop. The synthesis should fold symphony in alongside the existing Kosmos / Boiko-Gomes / BioGuider /
Sketch2Simulation thread as the **autonomous-dispatch + proof-of-work + repo-versioned-policy** reference; the
specific patterns (ID-vocabulary discipline, workspace-as-first-class, retry-with-tracker-reconciliation) are the
worked-design-references the Phase 3 spawner spec can crib from.

The secondary fold is into [`../syntheses/repo-clusters/g7-harnesses.md`](../syntheses/repo-clusters/g7-harnesses.md).
symphony broadens the harness cluster's coverage with a non-Rust, non-claw-shaped entrant (Elixir/OTP,
issue-tracker-driven, autonomous-daemon, language-agnostic SPEC.md as the primary artifact rather than the
implementation). Cross-vendor signal: combined with goose (Block / AAIF), claw-code (Anthropic), and now symphony
(OpenAI), the cluster's "industry endorsement" axis is fully covered — every leading vendor has now published a
harness reference, which validates the harness-cluster-as-distinct-concern framing the synthesis builds on.

The tertiary cross-references:

- [`goose.md`](goose.md) §3 (the Recipe DSL discussion) — symphony's `WORKFLOW.md` is the third reference for the
  Phase 3 task-spec format question alongside goose Recipe and Letta Agent File. The Phase 3 spawner-spec ADR should
  motivate the Linus task-spec shape against all three.
- [`Letta.md`](Letta.md) §3 (the Agent File discussion) — same three-way comparison. The discriminating axes are: how
  much state the spec carries (Letta full agent state; goose per-task scoped; symphony per-policy in-repo), how the
  spec reaches the agent (Letta via the agent server; goose via local file load; symphony via tracker-driven dispatch
  reading the in-repo `WORKFLOW.md`), and what the agent does after completing the task (Letta resumes; goose exits;
  symphony reconciles against the tracker).
- [`codebuff.md`](codebuff.md) — the existing planner/runner discussion in the harness cluster (claude-squad as
  planner, claude-task-master as runner). symphony is a related but distinct shape: the **issue tracker is the
  planner** (humans push work into Linear) and the symphony orchestrator is the runner. Cross-link the two
  discussions in g7-harnesses.md.
- [`workgraph.md`](workgraph.md) (cluster cell `g7-harnesses`) — symphony's poll-and-dispatch state machine plus the
  in-memory `OrchestratorState` shape is the closest published reference for the Phase 2a session-store + dispatch
  loop alongside workgraph's JSONL DAG (per the CLAUDE.md "Workgraph JSONL as the Phase 2a session-store shape"
  Engineering Convention). The state-machine shape from symphony plus the JSONL-DAG persistence shape from workgraph
  together form the Phase 2a session-store design reference set.

Phase mapping: Phase 2a (`WORKFLOW.md`-style policy-in-repo as a task-spec reference, ID-vocabulary discipline for the
session-store, workspace-as-first-class for Worker isolation, structured-logs-required for observability);
Phase 3 (retry-with-tracker-reconciliation pattern for Worker-failure handling, three-way task-spec comparison
alongside goose Recipe and Letta Agent File); Phase 5+ (issue-tracker-driven autonomous-dispatch as a Phase 5+ Linus
capability candidate; cross-vendor harness-plurality reference alongside goose / claw-code-local / openclaw).
symphony surfaces as a **pattern reference**, not a substrate — the implementation is Elixir/OTP and tracker-driven,
neither of which fits the Linus Phase 2/3 surface, but the SPEC.md is durable design content.

## 8. Open questions for Dan

1. **`WORKFLOW.md` as a Phase 3 task-spec reference alongside goose Recipe and Letta Agent File.** Three independent
   published references for "what does the agent task spec look like?" now exist (goose Recipe, Letta Agent File,
   symphony WORKFLOW.md). The discriminating axes are how much state is carried, how the spec reaches the agent, and
   what happens after task completion. Should the Phase 3 spawner spec ADR motivate the Linus task-spec shape against
   all three, picking a hybrid? Tentative answer: yes — the Linus shape is most naturally a hybrid (Recipe-style typed
   parameters and JSON-schema response from goose, AgentFile-style state-bundling from Letta, WORKFLOW.md-style
   policy-in-target-repo from symphony). Worth one paragraph in the Phase 3 spawner-spec ADR motivating the hybrid
   choice.

2. **ID-vocabulary discipline for the Phase 2a session-store.** symphony's SPEC §4.2 distinguishes four IDs (issue
   ID, issue identifier, workspace key, session ID) and uses each precisely. Should the Phase 2a session-store spec
   commit to an analogous four-ID discipline (e.g., task ID for internal joins, task identifier for human logs,
   workspace key for filesystem directory names, session ID for audit-log rows)? Tentative answer: yes — the
   discipline is cheap (one paragraph in the spec, one consistent vocabulary across the codebase) and the bug-
   prevention payoff is real (collapsed-ID bugs in long-running daemons are notoriously hard to debug).

3. **Workspace-as-first-class-concept for Phase 2a Worker isolation.** symphony creates one directory per issue,
   deterministically derived from the sanitized identifier, with `after_create` and `before_remove` hooks. The Linus
   analogue at Phase 2a is per-task workspace directories under `~/.linus/workspaces/<task-key>/`. Should the Phase 2a
   Worker-dispatch spec commit to deterministic per-task workspace paths with `after_create` / `before_remove` hooks,
   as a complementary discipline alongside the CLAUDE.md worktree-fan-out convention? Tentative answer: yes for
   long-running tasks (multi-step coding work, paper synthesis with intermediate files); not needed for
   one-shot tasks (single tool call, single response). Worth a sub-section in the Phase 2a Worker-dispatch spec.

4. **Issue-tracker integration as a Phase 5+ Linus capability candidate.** symphony's tracker-driven autonomous-dispatch
   loop is genuinely Phase 5+ territory (Linus is single-user, interactive Maestro/Worker at v0). Should the Phase 5+
   planning include an "issue-tracker-driven autonomous mode" as a candidate capability, with symphony as the design
   reference? Tentative answer: yes; defer the spec to Phase 5+, but cite symphony in the Phase 5 ADR seed as the
   design reference when the time comes. Most likely v1 tracker for Linus is GitHub Issues or a local plaintext task
   file, not Linear.

5. **`approval_policy: never` + `thread_sandbox: workspace-write` as a Tier-3 SAFETY.md reference.** symphony's
   sample WORKFLOW.md is the cleanest published worked example of a "trusted, autonomous, sandboxed" trust-and-safety
   configuration. Should SAFETY.md's autonomy-tier graduation cite symphony's sample as the Tier-3 reference
   configuration, specifically the four-knob shape (`approval_policy`, `thread_sandbox`, `turn_sandbox_policy`,
   `max_turns`)? Tentative answer: yes — the worked reference is a useful target for the SAFETY.md Tier-3 description,
   and the four-knob shape generalizes cleanly to other coding-agent runtimes Linus may eventually consume.

6. **OpenAI publishing harness-engineering as public-spec reference — a confirming signal for Linus's Maestro/Worker
   discipline.** symphony's existence and the OpenAI harness-engineering blog post the README references is direct
   industry validation of the **harness-engineering-as-discipline** framing Linus's CLAUDE.md has committed to from
   the start (Maestro/Worker discipline, spec-then-invoke-then-review, output budgets, MCP as tool substrate). For
   Dan's confidence in the architectural direction, this is the cross-vendor confirmation signal: both Anthropic
   (claw-code, the harness-engineering blog) and OpenAI (symphony, the harness-engineering blog the README links)
   converge on "the harness is a first-class engineering concern with its own design discipline." No action needed —
   just confirmation that the Phase 2/3 commitments are on the right side of the industry trajectory.

7. **Cross-vendor harness plurality confirmation — third independent signal for the Phase 5+ ADR set.** Per the
   [Letta repo-note](Letta.md) §3 and the [goose repo-note](goose.md) §3, two independent products ship
   Anthropic-compatible HTTP endpoints alongside OpenAI-compatible ones. symphony adds a **third confirming signal**:
   OpenAI is publishing harness specs that explicitly assume coding-agent-runtime plurality (Codex in the v1 spec,
   but the SPEC.md is structured to swap in a different agent runtime via the workflow's `agent` block). Three signals
   from three independent vendors (Anthropic via Letta-compatibility-references, Moonshot via Kimi-K2's Anthropic-
   compat surface, OpenAI via symphony's open agent-runtime contract) is enough evidence to commit to Phase 5+ ADRs:
   (a) Anthropic-compatible HTTP alongside OpenAI-compatible; (b) pluggable agent-runtime contract per the symphony
   shape. Worth scheduling both ADRs for Phase 5+ planning.

8. **Should Linus's CLAUDE.md cite symphony's `WORKFLOW.md` discipline as a Linus engineering convention?** The
   discipline rule "the workflow policy lives in the target repo, versioned alongside the code; the orchestrator
   trusts the repo's policy over any external config" is a small, durable convention. CLAUDE.md already has analogous
   conventions (smoke-test gates, checkpoint discipline, branching). Should "Policy lives in the target repo" join
   the list, with a one-paragraph entry citing symphony as the design reference? Tentative answer: defer to Phase 3
   when the Linus task-spec format ADR lands — at that point the convention has a concrete artifact (per-task
   spec files plus a project-level `LINUS.md`) and the CLAUDE.md entry can cite the spec rather than just the
   design pattern.
