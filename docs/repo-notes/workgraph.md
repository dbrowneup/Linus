# workgraph (`erikg/workgraph`)

## 1. Purpose and scope

workgraph is a Rust CLI (`wg`) that treats coordination as a typed dependency graph and a long-lived service that spawns
agents on whatever node is ready. The tagline — "works for humans, works for AI agents, works for both at once" — is
literal: a `wg agent create` registration is the same primitive whether the actor is Erik on Matrix or a Claude CLI
subprocess, both consume `wg ready` and both transition tasks through `open → in-progress → done` via the same
`wg claim` / `wg done` API. The interesting layer for Linus is `wg service start`: a daemon that watches the graph,
classifies nodes as ready, claims them on behalf of registered agents, spawns the matching CLI subprocess (`claude`,
`codex`, or in-process `nex` for OAI-compatible endpoints), heart-beats them, and re-spawns or triages dead ones. This
is DAG orchestration with a concrete agent-spawning runtime attached, not a planner that emits a task list.

## 2. Architecture summary

A single-binary Rust crate (`name = "workgraph"`, `bin = "wg"`, edition 2024) on petgraph + clap + tokio + ratatui. The
working tree's task graph lives in `.workgraph/graph.jsonl` — append-only JSONL, one record per task or edge, with
fields like `id`, `title`, `status`, `blocked_by`, `assigned`, `exec`, `created_at`, `started_at`, `completed_at`, and a
per-task `log` array. Project config is `.workgraph/config.toml`; global config is `~/.wg/config.toml`. The dispatch
core (`src/dispatch/handler_for_model.rs`) is one function that maps a model spec like `claude:opus`, `codex:gpt-5`,
`nex:qwen3-coder`, or `openrouter:anthropic/claude-opus-4-7` onto a handler — `claude` CLI, `codex` CLI, or in-process
`wg nex` speaking OAI-compat. The service layer (`src/service/`) is built around an `ExecutorRegistry`, an
`AgentRegistry` with per-PID heartbeat tracking, a `graph_watcher`, a `dispatch_boot`, and a `chat_compactor`. Spawn
commands are templated (the test config uses `claude --model {model} --print "{prompt}"`), so any model fronted by a CLI
is one config line away. Process management is serious: `collect_process_descendants` walks `/proc` to tree-kill agents
that escape via `setsid`, and the dispatcher integrates a heartbeat / dead-agent / auto-triage loop that can use a cheap
haiku model to decide whether a dead agent's work was actually finished. A second loop layered on top is the "agency":
`auto_evaluate`, `auto_assign`, `auto_triage`, `flip` — short one-shot LLM calls pinned to `claude:haiku` that score
completed tasks against a `## Validation` section in the task description, manage identity assignment, and gate
acceptance. Optional features wire in Matrix, Telegram, Email, Slack as agent contact channels. A `ratatui` TUI
(`wg tui`) gives a 9-tab inspector including a firehose of all agent stdout, and there's a PTY-embedded `wg nex` for
in-TUI inference. A skill (`wg skill install`) drops a `~/.claude/skills/wg/` definition so Claude Code auto-detects the
tool surface.

## 3. What's reusable in Linus

The graph-shaped task store and the spawn-on-ready service are the parts worth borrowing for Phase 1f's orchestration
evaluation and Phase 3's parallel-Worker spec. JSONL persistence in a `.workgraph/`-style directory is the right weight
for a personal system: human-readable, git-diffable, append-only, no SQLite ceremony — Linus's session store and audit
log could share that shape. `handler_for_model.rs`'s "one function, six handlers, derived from a model prefix" is a
clean pattern that Linus's router could lift directly: today Ollama, tomorrow `pmetal serve` and `mlx-lm`, all behind
the same dispatch axis. The heartbeat-and-tree-kill pattern matters because Linus will spawn long-lived Worker
subprocesses on M1 Max where a stale child quietly burns 24 GPU cores until the next reboot. The `## Validation`
convention plus auto-evaluate is a lightweight version of what Linus's Maestro/Worker protocol already wants: specs in
`experiments/<task>.md` carry success criteria, a worker exits, an evaluator scores. Compared with
**claude-task-master** (a separate Group 7 sibling), workgraph is the runtime where claude-task-master is the planner:
claude-task-master takes a PRD and emits a flat task list, workgraph holds an editable DAG and runs the daemon that
fires the agents. They are plausibly composable — claude-task-master generates, workgraph executes — though that
integration is not built. Compared with **claude-squad** (Group 7's other parallel-spawn approach, a tmux/git-worktree
multiplexer), workgraph reasons about _dependencies_ rather than just _isolation_: claude-squad lets you run N agents in
N worktrees side by side, workgraph decides which N can run _now_ given the edges, and routes their I/O back into the
graph.

## 4. What's inspiration only

The Rust crate as a whole is too thick for Linus to vendor — 60+ dependencies, optional Matrix/Telegram/Email/Slack
backends, a full TUI, `chromiumoxide` for headless browser, `tiktoken-rs`, `keyring` — that's a complete product, not a
library. The right move is to read the small load-bearing files (the dispatch handler, the JSONL schema, the heartbeat
loop) and reimplement the slice Linus needs in Python under `src/linus/orchestration/`, or to call `wg` as a subprocess.
The agency layer (`auto_assign`, `auto_evaluate`, `auto_triage`, `flip`, `evolve`) is interesting prior art for "LLMs
grading LLMs" but bigger than Linus needs in Phase 3; revisit at Phase 7 when skills and autonomy widen.

## 5. What's incompatible or out of scope

workgraph is Linux-first in places — `collect_process_descendants` walks `/proc` and is gated on `target_os = "linux"`,
returning an empty vec on macOS, so dead-agent tree-kill silently degrades on M1. Default Anthropic-API assumption means
out-of-the-box `wg service start` will reach for `claude --print` and burn API credits, not Ollama; the `nex:` /
`openrouter:` routes work but are second-class citizens in the README. `cargo install --path .` rebuilds the full
feature surface (matrix-lite, ratatui, chromiumoxide, all of it) and is a heavier compile than Linus benefits from. The
`~/.wg/`, `~/.claude/skills/wg/`, systemd-user-unit, and `wg secret` keychain integration all assume workgraph owns the
user's coordination surface — adopting workgraph wholesale means Linus is downstream of it, which inverts the
architecture in CLAUDE.md where Linus is the orchestration layer.

## 6. Recommendation: **Study**

Build `wg`, run `wg init` + `wg service start --model claude:haiku` against a 3-task DAG with a smoke gate, and watch
the agents fire in `wg tui`. The artifact to produce is a one-page spec (`docs/specs/orchestration-store.md`) that
copies the JSONL schema, the handler-for-model pattern, and the heartbeat loop into Linus terms. Decision point at Phase
3: if Linus's parallel-Worker fan-out needs a graph store, reimplement the slice in Python rather than vendoring the
Rust crate; if it doesn't, the study still pays for itself by clarifying what Linus's session store should look like. Do
not adopt as a runtime dependency.

## 7. Questions for Dan

- **Graph vs. list as the orchestration substrate.** workgraph commits to a DAG with `--after` edges, cycles, and a
  `restart_on_failure` policy. claude-task-master commits to an ordered list emitted from a PRD. Which fits the kinds of
  work you actually delegate to Workers — bench sweeps and ablations (graph-shaped, dependencies real) or per-paper
  synthesis batches (list-shaped, embarrassingly parallel)?
- **JSONL store at the orchestration layer.** ARCHITECTURE.md mentions a session store and an audit log without picking
  a format. Adopting workgraph's `.workgraph/graph.jsonl` shape (append-only, one record per event, human-readable) for
  Linus's session store would be cheap and git-friendly. Or do you want SQLite from day one for query power?
- **Agency / auto-evaluate as Linus's verification layer.** workgraph's `## Validation` convention plus a haiku-pinned
  evaluator is a lightweight version of what SAFETY.md's autonomy tier graduation needs. Worth lifting the convention
  into Linus's Maestro/Worker protocol now, or keep verification human-in-the-loop until Phase 7?
- **The macOS gap.** Tree-kill via `/proc` doesn't exist on M1. If Linus borrows the heartbeat pattern, we need a
  `kqueue`-based or `pgrep -P`-based equivalent. Worth writing as a small Phase 1f experiment, or accept that on macOS a
  stuck Worker is a `wg kill --force` command rather than an automatic recovery?
- **Composing workgraph with claude-task-master.** A plausible Group-7 verdict is "task-master plans, workgraph
  executes" — task-master emits the DAG, workgraph runs it. Is that interesting enough to prototype in Phase 3, or
  should Linus own both halves natively in Python?
