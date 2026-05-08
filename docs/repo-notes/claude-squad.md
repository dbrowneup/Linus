# claude-squad (`smtg-ai/claude-squad`)

## 1. Purpose and scope

Claude Squad — installed as the binary `cs` — is a terminal app that runs and supervises **multiple coding-agent CLIs in
parallel**, each in its own isolated git workspace. Out of the box it manages instances of `claude`, `codex`, `gemini`,
and `aider` (any program is permissible via `-p`, e.g. `cs -p "aider --model ollama_chat/gemma3:1b"`). The operator
picks an instance from a TUI list, sees a live preview of that agent's terminal and a diff of its working copy, and can
let the agent run unattended in "auto-accept / yolo" mode (`-y`) while moving on to the next task. It is named in the
Linus planning spec as a **Phase 1f orchestration evaluation deliverable** alongside Task Master AI: the question it
answers is "do we need to build custom multi-Worker spawning, or does an existing parallel-terminal-agent manager
already cover Linus's near-term needs?"

## 2. Architecture summary

A single Go module (`go 1.23`, AGPL-3.0) compiled to one static binary. Two external runtime prerequisites: **tmux**
(for per-instance terminal isolation) and **gh** (for the "commit-and-push to a PR" hotkey). The TUI is built with
Charmbracelet's Bubble Tea / Bubbles / Lipgloss stack; git plumbing uses both `go-git/go-git/v5` and shell-out to the
system `git` CLI, with the comment that the CLI is "much faster than `go-git PlainOpen`" for hot-path checks.

Two state holders define the model. A `session.Instance` (`session/instance.go`, ~613 lines) owns one agent: title,
program command, status (`Running`/`Ready`/`Loading`/`Paused`), prompt, AutoYes flag, plus a `*tmux.TmuxSession` and a
`*git.GitWorktree`. A `git.GitWorktree` (`session/git/worktree.go` plus `worktree_ops.go`) owns workspace isolation: on
`Setup()` it shells out `git worktree add -b <prefix><session> <worktreePath> <HEAD-SHA>` into
`~/.claude-squad/worktrees/<sanitized-branch>_<nanoseconds>`. The base SHA is captured per session so diffs are stable.
`Cleanup()` runs `git worktree remove -f` plus `git branch -D` (skipping the branch delete when the session attached to
a pre-existing branch); `CleanupWorktrees()` walks the worktrees dir and prunes everything for `cs reset`.

AutoYes is implemented as a **detached daemon process** (`daemon/daemon.go`). When `cs` is launched with `-y` and
AutoYes sessions exist, the main process forks itself with a hidden `--daemon` flag, writes the child PID to
`~/.claude-squad/daemon.pid`, and exits the launcher. The daemon polls every `DaemonPollInterval` ms, and for each
non-paused, started instance it calls `instance.HasUpdated()` — when the agent's tmux pane has a new prompt waiting, it
calls `instance.TapEnter()` to send a keystroke and `UpdateDiffStats()` to refresh the TUI's diff badge. The next `cs`
launch kills the daemon by PID before opening the TUI. Hotkeys: `n`/`N` create, `D` kill, `↵`/`o` attach, `s`
commit-and-push branch, `c` checkout-and-pause, `r` resume, `tab` swap preview/diff. Config lives at
`~/.claude-squad/config.json` and supports named **profiles** (e.g. one profile per agent CLI) selected via `←`/`→`
arrows in the new-session overlay.

## 3. What's reusable in Linus

Two primitives, conceptually. The **git-worktree-per-task** isolation pattern is a near-perfect match for the
BRANCHING.md "agent branches" model — each Worker gets a worktree in `~/.linus/worktrees/`, a branch named
`<prefix><task-id>`, and a captured base SHA, so a Worker can run destructive edits without touching Dan's cwd or other
Workers' files. The whole flow (resolve repo root, create worktree dir, `worktree add -b … <HEAD>`, capture SHA, cleanup
with branch-delete suppression for pre-existing branches) is ~220 lines of straightforward Go in
`session/git/worktree_ops.go` and reads as a portable spec — Linus could re-implement it in Rust (pmetal-orchestrator)
or Python without vendoring.

The **AutoYes daemon pattern** — a polling supervisor that watches each agent's tmux pane for "waiting on input" and
taps Enter — is the autonomy-tier-2 SAFETY.md hook: a Linus daemon could similarly arbitrate Worker confirmations
against the sandbox policy rather than blanket-yes-ing.

Comparison to Phase 1f's other named candidate, **claude-task-master**: claude-squad is concerned with _runtime
isolation and supervision_ of long-running agent CLIs, not _task decomposition_. Task Master decomposes a goal into a
DAG of subtasks; claude-squad gives each subtask a private worktree and tmux pane. They are complementary, not rivals,
and the honest Phase 1f answer may be "use both, then decide whether Linus's orchestration layer should subsume their
union."

## 4. What's inspiration only

Versus the existing G7 notes: **cline** is a single-agent VS Code extension with rich in-editor UX; **claw-code** is a
single-agent Rust CLI tied to Anthropic's API; **claw-code-local** adds Ollama backend but stays single-agent;
**openclaw** is a local-first chat/voice gateway, not a fan-out supervisor. Claude Squad is the only one of the five
that **treats "many agents at once" as the first-class object**. That parallel-by-default mental model is what Linus's
Phase 3 ("Knowledge & Parallel Agents") needs to internalize — the differentiators are (a) one process per agent in its
own tmux session, (b) one git worktree per agent enforcing physical-disk isolation, (c) a tiny detached daemon for
hands-free continuation. Everything else — the Bubble Tea UI, the Cobra CLI, the profile system — is polish around those
three ideas.

## 5. What's incompatible or out of scope

Claude Squad is **TUI-only** — it does not expose an HTTP/JSON API or library entry point. To embed its logic Linus
would re-implement, not import. It hard-depends on **tmux** (no Windows-native path; the Windows tmux file is a stub),
which is fine on Dan's M1 Max but means Linus's orchestration layer either inherits the tmux dependency or replaces that
primitive with its own PTY supervisor (`creack/pty` is already in claude-squad's go.mod, so a tmux-less rewrite is
plausible). It is also **Anthropic/OpenAI/Google CLI-shaped** — it spawns whatever binary you name and screen-scrapes
its tmux pane for "ready for input." That works for hosted-agent CLIs and Aider; it does **not** trivially work for
Linus's intended local-Worker pattern of "post a JSON spec to an OpenAI-compat endpoint, get a JSON response." A Linus
Worker isn't a long-lived REPL; it's a request-response inference call. The two patterns can coexist (Linus runs both
"chat-style spawned CLIs" and "stateless API Workers") but claude-squad only models the former.

## 6. Recommendation: **Study**

Install `cs` on the M1 Max (`brew install claude-squad && ln -s …/claude-squad …/cs`), spend an afternoon during Phase
1f running 3–4 parallel sessions (one Claude Code, one `cs -p "ollama run qwen2.5-coder:14b"`, one Aider against a local
model) on real Linus tasks, and write the verdict as the next-free `DEC-NNNN` ADR with slug `orchestration-evaluation`.
Do not vendor the Go code; do **lift the worktree+SHA+cleanup design** verbatim into the Linus orchestration spec as the
canonical "Worker workspace" primitive. The auto-accept daemon is a useful template for the autonomy-tier-2 supervisor
but should be re-implemented inside Linus where it can consult SAFETY.md policy rather than blanket-yes.

## 7. Questions for Dan

1. **Phase 1f verdict shape.** The spec frames this as Task-Master vs claude-squad vs custom vs pmetal-MCP. After
   reading both, my read is they solve different layers (decomposition vs runtime isolation). Want the Phase 1f ADR to
   recommend using both as off-the-shelf today, with Linus's custom layer scoped to "the glue between them," or hold the
   line that Linus owns orchestration end-to-end and they remain study-only?
2. **Worktree-per-Worker as the canonical primitive.** Adopting `~/.linus/worktrees/<branch>_<nanoseconds>` matches
   BRANCHING.md cleanly but means every Worker run touches disk and consumes inodes. For short-lived stateless Workers
   (a one-shot test-generation call) this is overkill. Two-tier model — durable worktrees for `agent/<task-id>`
   branches, in-memory `git diff`-only for one-shots — or always-worktree for uniformity?
3. **tmux dependency.** Claude-squad assumes tmux. If Linus inherits this, openclaw / native-app front-ends inherit it
   too. Acceptable now (Dan uses tmux daily) or a smell to design out via `creack/pty` directly?
4. **AutoYes meets SAFETY.md.** Claude-squad's `-y` is "press Enter on every prompt." Linus's autonomy graduation
   expects `-y` to mean "press Enter on prompts that match the current tier's allowlist, deny otherwise." Should the
   Phase 1f ADR explicitly call out that any adopted runner must hand off prompt-arbitration to Linus's policy engine?
5. **Screen-scraping vs structured I/O.** Claude-squad detects "agent waiting" by reading the tmux pane. Local Workers
   speaking OpenAI-compat give Linus structured turn boundaries for free. Do we want the orchestration layer to support
   both modalities (spawned-CLI + API-Worker), or commit to API-Worker as the only Linus-native pattern and treat
   CLI-spawning as a third-party concern?
