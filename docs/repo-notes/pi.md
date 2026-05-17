# pi (`earendil-works/pi`)

## 1. Purpose and scope

pi is the **Pi Agent Harness Mono Repo** — a TypeScript/Node monorepo of five npm-published packages plus docs and
examples, MIT-licensed, single-maintainer-led by Mario Zechner (`badlogic`), domain at `pi.dev` (graciously donated by
`exe.dev`). The product surface is `@earendil-works/pi-coding-agent` — a "minimal terminal coding harness" that ships
with deliberately conservative defaults (four built-in tools: `read`, `write`, `edit`, `bash`) and extends through
TypeScript Extensions, Agent Skills, prompt templates, themes, and pi-packages bundled via npm or git. The unifying
slogan repeated through the README is "adapt pi to your workflows, not the other way around" — and the philosophy
section is unusually explicit about what pi **deliberately does not ship**: no MCP, no sub-agents, no plan mode, no
permission popups, no built-in to-dos, no background bash. Everything beyond the minimal core is opt-in via an
extension or a third-party pi-package, with the explicit posture that bloat is the failure mode worth avoiding even
at the cost of feature parity with claw-code / Claude Code / Cline. The repo is a recent and actively-maintained
entrant (npm-published with a CHANGELOG-driven release cadence under `npm run release:patch` / `release:minor`,
lockstep versioning across all packages, and a contributor-gate workflow that auto-closes PRs/issues from new
contributors pending maintainer review).

The five packages split as follows. **`@earendil-works/pi-ai`** is the unified multi-provider LLM API — the lower
foundation. It speaks 35+ providers (OpenAI, Azure OpenAI, Anthropic, Google, Vertex, Mistral, Groq, Cerebras,
Cloudflare AI Gateway, xAI, OpenRouter, Vercel AI Gateway, DeepSeek, Bedrock, Fireworks, Together AI, OpenCode Zen,
Kimi For Coding, Xiaomi MiMo, MiniMax, plus any OpenAI-compatible endpoint including Ollama, vLLM, LM Studio, and
LiteLLM proxies) through a uniform streaming/completion interface with TypeBox-typed tool schemas. Built-in API
implementations cover six shapes — `openai-completions`, `openai-responses`, `openai-codex-responses`,
`azure-openai-responses`, `anthropic-messages`, `google-generative-ai`, `google-vertex`, `mistral-conversations`,
`bedrock-converse-stream` — and the provider-compatibility surface is rich enough to capture per-provider quirks via
the `compat` field on a `Model` (e.g., `thinkingFormat: "deepseek" | "openrouter" | "qwen" | "qwen-chat-template"`,
`cacheControlFormat: "anthropic"`, `maxTokensField: "max_completion_tokens" | "max_tokens"`,
`requiresReasoningContentOnAssistantMessages` for DeepSeek-shaped reasoning replay). Cross-provider handoffs work by
transforming thinking blocks to `<thinking>`-tagged text when message context crosses provider boundaries, so a
conversation can start with Claude and continue with GPT-5 or Gemini without context loss. **`@earendil-works/pi-agent-core`**
is the stateful-agent layer built on top of `pi-ai` — an `Agent` class with `prompt()` / `continue()` /
`steer()` / `followUp()` methods, an event-emitting stream (`agent_start`, `turn_start`, `message_start/update/end`,
`tool_execution_start/update/end`, `turn_end`, `agent_end`), a `beforeToolCall` / `afterToolCall` hook pair for
permission gating and post-processing, configurable parallel-or-sequential tool execution, dynamic OAuth token
refresh via `getApiKey`, and an explicit `terminate: true` tool-result hint that signals "skip the automatic follow-up
LLM call when every tool in the batch is terminating." **`@earendil-works/pi-coding-agent`** is the CLI binary `pi`
that wraps `pi-agent-core` for terminal usage — interactive TUI, four modes (interactive / `--print` / `--mode json`
JSONL events / `--mode rpc` LF-delimited JSON-RPC for process integration), session storage as JSONL files with a
**tree-of-branches** structure (each entry has `id` and `parentId`, enabling `/tree` / `/fork` / `/clone` in-place
branching without new files), and configurable compaction triggered automatically on context overflow or proactively
near the limit. **`@earendil-works/pi-tui`** is a terminal UI library with differential rendering — pi's own answer
to ratatui / blessed / ink, used inside the coding-agent. **`@earendil-works/pi-web-ui`** is a set of web components
for browser-based AI chat interfaces, presumably the substrate for downstream embedders.

The relevant integration signal: openclaw is named in `packages/coding-agent/README.md` as a real-world consumer of
the SDK ("See [openclaw/openclaw](https://github.com/openclaw/openclaw) for a real-world SDK integration"). pi is
also reachable from goose's ACP shim layer as one of seven provider-side ACP-compatible upstream harnesses
(`crates/goose/src/providers/pi_acp.rs` per the [goose repo-note](goose.md) §2), making pi the **only TypeScript-side
coding-agent harness in the cloned-repo collection that goose reaches as a peer**.

## 2. Architecture summary

The monorepo is npm-workspace-managed with five packages under `packages/` plus dev tooling (`pi-share-hf`,
`pi-test.sh`, contributor-gate GitHub workflows). The npm-published surface is lockstep-versioned: every release bumps
all five packages to the same version, with semver semantics deliberately deviating from the standard ("patch" =
fixes + features, "minor" = breaking changes, no major releases) — a single-maintainer simplification.

**`packages/ai/` — the LLM-API foundation.** ~30 modules under `src/`. `types.ts` defines the core types: `Api`
(union of API identifiers), `Model<TApi>` (typed per-API model metadata), `Context` (`systemPrompt`, `messages`,
`tools`), `AssistantMessage`, content blocks (`text`, `thinking`, `toolCall`, `image`), `Tool` (TypeBox-shaped),
`StreamOptions` plus per-API option types (`AnthropicOptions`, `OpenAIResponsesOptions`, `BedrockOptions`, etc.). The
core verbs are `stream()` / `complete()` (raw, fully-typed per provider) and `streamSimple()` / `completeSimple()`
(provider-agnostic with a unified `reasoning: "minimal" | "low" | "medium" | "high" | "xhigh"` shorthand). Provider
modules live under `src/providers/`; each exports a `stream<Provider>()` returning an `AssistantMessageEventStream`,
message/tool conversion functions, and a faux-provider option for tests (`registerFauxProvider()` ships in-tree as
the canonical mock substrate). The **OpenAI-compat surface** at `src/providers/openai-completions.ts` is the
broadest of the package's compatibility shapes: an auto-detection table maps base URLs to per-provider `compat`
flags (Cerebras, xAI, Chutes, DeepSeek, Together AI, zAI, OpenCode, Cloudflare Workers AI, OpenRouter), and the
`OpenAICompletionsCompat` interface enumerates 17 flags covering store-field support, developer-role-vs-system,
reasoning-effort, usage-in-streaming, strict-mode tool defs, max-tokens-field name, tool-result naming/sequencing,
thinking-as-text conversion, reasoning-content replay for DeepSeek, six different thinking-format wire shapes,
Anthropic-style cache-control on prompts, OpenRouter routing preferences, and Vercel AI Gateway routing. The
**`@earendil-works/pi-ai/oauth` entry point** (a separate package subpath export) handles the three OAuth-only
providers — Anthropic (Claude Pro/Max subscription via `loginAnthropic`), OpenAI Codex (ChatGPT Plus/Pro subscription
via `loginOpenAICodex` for GPT-5.x Codex models), and GitHub Copilot (Copilot subscription via `loginGitHubCopilot`)
— with stored-credential-managed token refresh via `getOAuthApiKey()`. The `pi-ai login` CLI is the convenience
wrapper. Image-generation is a separate API surface (`getImageModel`, `generateImages()`) currently routed only through
OpenRouter.

**`packages/agent/` — the stateful-agent layer.** ~12 modules. `Agent` class lives in `src/agent.ts`; the low-level
loop functions `agentLoop()` and `agentLoopContinue()` are exposed under `src/loop.ts`. The agent's message model is
`AgentMessage` — a flexible superset of the LLM's `Message` shape that supports custom message types via TypeScript
declaration merging (the `CustomAgentMessages` interface) so UI-only message types (notifications, system events)
can flow through the agent state without contaminating LLM context. The `convertToLlm` callback bridges the two:
agent state holds the rich `AgentMessage[]`, the LLM sees a filtered/transformed `Message[]`. The `transformContext`
callback runs before `convertToLlm` for pruning, compaction, or external-context injection. **Tool execution
modes** are configurable both globally (`toolExecution: "parallel" | "sequential"` in agent config) and per-tool
(`executionMode` on `AgentTool`); parallel mode preflights tool calls sequentially but executes them concurrently,
emits `tool_execution_end` in completion order, and persists toolResult messages in assistant source order — the
mixed-batch sequential-override rule states that if any tool in a batch is `sequential`, the entire batch executes
serially. The `beforeToolCall` hook runs after argument validation and can block execution by returning
`{ block: true, reason: string }`; `afterToolCall` runs after execution and before the final tool-end events and
can override the result details or set `terminate: true` to hint loop termination. The **steering / follow-up
queue** machinery is the agent's answer to "interrupt the agent mid-tool-call without aborting":
`agent.steer(message)` queues a message delivered after the current assistant turn finishes its tool calls;
`agent.followUp(message)` queues a message delivered only after the agent fully settles. Both have `"one-at-a-time"`
(default, waits for response) or `"all"` (delivers all queued at once) modes.

**`packages/coding-agent/` — the CLI binary.** This is the user-facing surface. The README's table-of-contents
enumerates: Quick Start, Providers & Models (the same 35+ providers as `pi-ai`, accessed via API key, subscription
OAuth, or custom `~/.pi/agent/models.json`), Interactive Mode (TUI with @-file references, tab path completion,
Ctrl+V image paste, `!command` / `!!command` bash escape, command palette via `/`), Sessions (JSONL with tree
branching), Settings (global at `~/.pi/agent/settings.json`, per-project at `.pi/settings.json`), Context Files
(`AGENTS.md` or `CLAUDE.md` loaded from `~/.pi/agent/`, parent directories walked from `cwd`, and the current
directory — concatenated), and Customization (Prompt Templates, Skills following the
[Agent Skills standard](https://agentskills.io), Extensions, Themes, Pi Packages). The session-tree feature is
load-bearing for pi's pitch: every session is a single JSONL file with `id` / `parentId` pointers, so the user can
`/tree`-navigate to any prior message, `/fork` from that point into a new session, or `/clone` the current active
branch into a new file — preserving full history while allowing exploratory branching without disk-space
multiplication. Compaction is **lossy** but the full pre-compacted history remains in the JSONL file accessible via
`/tree`. Auto-compaction triggers either on context-overflow recovery (the agent attempts a turn, gets a
context-too-long error, compacts, retries) or proactively near the limit. The four built-in tools (`read`, `bash`,
`edit`, `write`) plus three filesystem helpers (`grep`, `find`, `ls`) are intentionally the minimum set; everything
else — sub-agents, plan mode, permission popups, background bash, todos — is **explicitly delegated to extensions or
third-party packages**. Per the philosophy section: "[these features] confuse models" / "use a TODO.md file, or build
your own with extensions" / "use tmux" / "build it with extensions, or install a package."

**Pi Packages and extension surface.** `pi install <source>` accepts seven source URIs: `npm:<pkg>`,
`npm:<pkg>@version`, `git:<host>/<owner>/<repo>`, `git:<host>/<owner>/<repo>@tag-or-commit`, `git:git@...`,
`https://<host>/...`, `ssh://...`. Packages install to `~/.pi/agent/git/` (git) or global npm by default, or to
`.pi/git/` / `.pi/npm/` with the `-l` (local) flag. Git packages install runtime deps with `npm install --omit=dev`.
The `pi config` subcommand toggles individual extensions, skills, prompts, and themes within an installed package.
A pi-package is a `package.json` with a `"pi"` key declaring directories for extensions, skills, prompts, and
themes; without the manifest, auto-discovery scans the conventional directories. The explicit security disclosure
in the README — "Pi packages run with full system access. Extensions execute arbitrary code, and skills can instruct
the model to perform any action including running executables. Review source code before installing third-party
packages." — is the honest framing of the trust model and is closer to "you are responsible for the supply chain"
than to "we will sandbox third-party code."

**Extensions are TypeScript modules.** The `ExtensionAPI` exposes `pi.registerTool({ name, ... })`,
`pi.registerCommand("name", { ... })`, `pi.on("tool_call", handler)`, `pi.registerProvider(...)`, plus hooks for
custom editors, status lines, headers/footers, overlays, MCP server integration, custom compaction, permission
gates, path protection, SSH and sandbox execution, git checkpointing, and arbitrary other UI customizations. The
default export can be `async` so extension factories that need one-time initialization (e.g., fetching remote
model lists before calling `pi.registerProvider()`) block startup until they settle. Skills follow the Agent Skills
standard (`SKILL.md` Markdown files in `~/.pi/agent/skills/<name>/` or `~/.agents/skills/<name>/` or `.pi/skills/`
or `.agents/skills/`) and are invoked via `/skill:name` or loaded automatically by the model.

**Operational surface.** The `pi --mode rpc` sub-CLI exposes the agent over LF-delimited JSONL on stdin/stdout for
non-Node consumers; the SDK pattern at `createAgentSession(...)` and `createAgentSessionRuntime(...)` is the
in-process integration shape openclaw uses. The CLI accepts ten resource flags (`-e/--extension`, `--no-extensions`,
`--skill`, `--no-skills`, `--prompt-template`, `--no-prompt-templates`, `--theme`, `--no-themes`,
`--no-context-files`, plus combinatorial usage like `--no-extensions -e ./my-ext.ts` to load exactly one), three
tool flags (`--tools list`, `--no-builtin-tools` and `--no-tools`), and standard session flags
(`-c/--continue`, `-r/--resume`, `--session`, `--fork`, `--no-session`). The `--offline` / `PI_OFFLINE=1` flag
disables all startup network operations (update check at `https://pi.dev/api/latest-version`, install/update
telemetry at `https://pi.dev/api/report-install`, package update checks); both update checks and telemetry are
also individually opt-out-able via `PI_SKIP_VERSION_CHECK=1` and `PI_TELEMETRY=0` / `enableInstallTelemetry: false`.

**The `AGENTS.md` development rules** are an unusually transparent maintainer policy: no emojis in any artifact;
files read fully before wide-ranging changes; no `any` types unless required; no inline imports; no single-line
helper functions with one call site; never reset/checkout/clean/stash because multiple agents may share the worktree
(the parallel-agents discipline is documented as `**CRITICAL** Git Rules for Parallel Agents **CRITICAL**`); use
specific file paths in `git add`, never `-A` / `.`; never commit with `--no-verify`. The repo also documents
testing pi interactively via `tmux new-session -d -s pi-test -x 80 -y 24` then sending keys with `tmux send-keys`
— a pattern Linus's harness regression suite could lift directly for any future Phase 5+ TUI testing.

## 3. What's reusable in Linus

pi's contribution to Linus is **structural and design-reference**, not substantive — Linus does not vendor pi (it
is TypeScript-on-Node, Linus's orchestration core is Python per DEC-0027). But the harness shape, the explicit
"what we deliberately don't ship" philosophy, the session-tree feature, the `pi-ai` provider abstraction's `compat`
field richness, and the `pi-agent-core` event model are individually liftable as Phase 2+ design references where
Linus's harness consumers (openclaw, claw-code-local, future entrants) need protocol alignment.

**Phase 2a — OpenAI-compatible HTTP boundary as the substrate for pi's `openai-completions` provider (DEC-0005).**
Once Linus's `/v1/chat/completions` endpoint is up in Phase 2a, pi can point at it via `pi-ai`'s OpenAI-compat
shim by registering a custom `Model<'openai-completions'>` with `baseUrl: "http://localhost:<linus-port>/v1"` —
no pi-side code changes required. The `compat` field's 17 flags (per `OpenAICompletionsCompat` in
`packages/ai/src/types.ts`) are a worked enumeration of what an OpenAI-compatible server may or may not support, and
Linus's Phase 2a endpoint can use this as a checklist for what behaviors to advertise: store-field support
(`supportsStore`), developer-role vs system-message routing (`supportsDeveloperRole`), reasoning-effort field name
and shape (`supportsReasoningEffort`, `thinkingFormat`), max-tokens field name (`maxTokensField`), strict-mode in
tool defs (`supportsStrictMode`), session-affinity headers, tool-result `name` requirement, tool-result-followed-by-
assistant requirement, thinking-as-text conversion, reasoning-content replay on assistant messages. This is the
**most thorough cross-provider compatibility surface in the cloned-repo collection** and is more comprehensive than
goose's per-provider modules (which encode the differences but don't expose them as a uniform contract). When Linus
ships its Phase 2a server, the README should document which `compat` flags Linus's endpoint advertises so pi (and
any other `openai-compat`-flag-aware client) can configure correctly.

**Phase 5+ — pi as the canonical TypeScript-side coding-agent harness reference for openclaw integration.** Per the
explicit cross-reference in `packages/coding-agent/README.md` ("See `openclaw/openclaw` for a real-world SDK
integration"), pi is **already** the substrate openclaw consumes. Linus's Phase 5 commits openclaw as the polished
front-end ([openclaw repo-note](openclaw.md)); the chain is pi (npm package) → openclaw (Phase 5+ Linus front-end)
→ Linus (Phase 2+ orchestration backend). The `pi-coding-agent` SDK pattern at `createAgentSession(...)` is the
in-process integration shape — `AuthStorage.create()`, `ModelRegistry.create(authStorage)`,
`createAgentSession({sessionManager, authStorage, modelRegistry})`, then `session.prompt(...)`. For Phase 5+,
when openclaw needs to plug into Linus's orchestration backend, the relevant question becomes "does openclaw
continue to consume pi's SDK in-process, or does it consume Linus's orchestration backend via HTTP?" Likely both —
pi handles the TUI / session-tree / extension surface inside openclaw; Linus's HTTP endpoint handles the
provider-routing / Worker-spawning / MCP-tool surface. The Phase 5+ ADR on openclaw integration should reference
pi's SDK shape as the substrate openclaw already depends on, and Linus's `/v1/chat/completions` endpoint as the
target pi's `openai-completions` provider then talks to. The architectural cleanliness: pi handles UX, openclaw
handles bundling/distribution, Linus handles orchestration.

**Phase 2a — session-tree JSONL as a richer prior-art reference for the session-store format.** Workgraph's
`.workgraph/graph.jsonl` append-only DAG is the recommended Phase 2a session-store shape per CLAUDE.md and the
[g7-harnesses synthesis](../syntheses/repo-clusters/g7-harnesses.md). Pi's session format is a **complementary**
reference: also JSONL, also append-only, also `id`-keyed entries — but pi additionally tracks `parentId` to enable
the **tree-of-branches** UX (in-place branching with `/tree` / `/fork` / `/clone`). For Linus's Phase 2a session
store, this is a directly relevant capability question: does Linus need the workgraph-style linear-DAG shape (one
session = one node-chain), or the pi-style tree shape (one session = a branching tree where any prior point can
spawn a new active branch)? The tree shape is the richer pattern; it costs only the `parentId` field plus the
navigation tooling. For Linus's Maestro+Worker discipline where exploratory branches are common (Worker writes a
draft, Maestro re-runs from an earlier point with revised guidance), the pi shape is plausibly the better fit. The
Phase 2a session-store ADR should evaluate both formats and decide which to commit to — neither is much harder to
implement than the other; the choice locks in what `/tree`-like UX Linus can offer downstream.

**Phase 3 — the `terminate: true` tool-result hint as a clean Worker-termination protocol primitive (DEC-0051).**
Pi's tool-result interface supports a `terminate: true` flag returned from either `execute()` or `afterToolCall` —
a hint that the agent should stop after the current tool batch, taking effect only when **every** finalized tool
result in the batch is terminating. The runtime semantic is "the assistant message that called these tools is
final; do not call the LLM again for a follow-up turn." This is a clean substrate for the AgentReport pattern in
DEC-0051: when a Worker finishes its task, its terminal tool call (e.g., `linus.agent.report_final(report)`) sets
`terminate: true` and the spawner does not re-invoke the Worker. The shape is more disciplined than openai's stop
reasons (which are model-side, not tool-side) and more granular than goose's recipe-level `max_turns` cap (which
applies to the whole task). For Linus's Phase 3 spawner, adopt the per-tool-result termination hint as the canonical
signal that a Worker is done, with a uniform `terminate: true` field on tool results echoed in the AgentReport
serialization.

**Phase 2+ — the steering / follow-up queue pattern as the canonical Maestro-interrupt primitive.** Pi's
`agent.steer(message)` (delivered after the current tool batch) and `agent.followUp(message)` (delivered after the
agent fully settles) are the closest existing reference for what Linus's Maestro-side "interrupt the Worker without
killing the Worker" interface should look like. The two-queue split is non-obvious: steering interrupts mid-task
(Maestro spots an error in the Worker's reasoning, wants to redirect); follow-up extends the task (Maestro adds a
side requirement after the original task is done). Pi's mode flags (`"one-at-a-time"` waits for response between
queue entries; `"all"` delivers everything at once) cover the realistic policy axes. For Linus's Phase 2+
orchestration backend, this is a directly usable Maestro-API shape: the Maestro UI exposes a "send steering
message" and a "send follow-up message" affordance to the Worker registry; the Worker's `dispatch_continuation`
primitive (per the open question in the [MemGPT paper-note](../paper-notes/Letta-2310.08560.md) §"Open questions
for Dan" Q5) maps onto pi's `steering` and `followUp` queue semantics.

**Phase 5+ — provider-routing `compat` field as a reference for Linus's Worker registry tags.** Pi-ai's `compat`
field is set per-Model (not per-Provider), which is the right granularity: even within a single provider, different
models may have different reasoning-format wire shapes, different field-name conventions, or different cache-control
support. Linus's Phase 2 Worker registry should adopt the same granularity — per-Worker capability tags rather than
per-Provider tags — and pi's enumeration (`thinkingFormat: "openai" | "openrouter" | "deepseek" | "together" |
"zai" | "qwen" | "qwen-chat-template"`, `cacheControlFormat: "anthropic"`, `maxTokensField`,
`requiresReasoningContentOnAssistantMessages`, etc.) is the prior-art reference for which capability dimensions
matter in practice. Combined with goose's stratification (`Stdio` / `StreamableHttp` / `Builtin` / `Platform` /
`Frontend` / `InlinePython` per the [goose repo-note](goose.md) §3) for extension-config taxonomy and rig's
typestate `AgentBuilder` for Rust-side type safety, pi's compat-field richness completes the picture: capability
tags at the Worker level are what enables a generic dispatcher to route the right task to the right Worker without
hard-coding per-provider quirks.

**Phase 5+ — the explicit "what we don't ship" philosophy as a Linus design discipline anchor.** Pi's most distinctive
contribution is not technical; it is the **philosophical posture**, articulated in `packages/coding-agent/README.md`
§Philosophy and the [Mario Zechner blog post](https://mariozechner.at/posts/2025-11-30-pi-coding-agent/) cited
there. The five "no" claims — no MCP, no sub-agents, no permission popups, no plan mode, no built-in to-dos, no
background bash — are each accompanied by a one-line "build it as an extension or install a package" answer,
backed by the empirical claim that "todos confuse models" and "permission popups break flow" and "MCP adds latency
when shell commands plus READMEs already work." This is The Algorithm (CLAUDE.md §Guiding Principles) restated for
harness design: **question every feature; delete every step; simplify before adding more.** For Linus's Phase 5+
harness design, the relevant takeaway is not "copy pi's no-feature list" (Linus is an orchestration backend, not a
harness) but rather "explicitly enumerate what Linus deliberately does not ship, and back each non-feature with a
one-line rationale." The current ARCHITECTURE.md is implicit about scope boundaries (DEC-0020 commits to bounded
orchestration scope); promoting that to an explicit list — "Linus does not ship its own UI; Linus does not ship a
plan-mode skill; Linus does not ship a custom MCP server beyond the v0 set per DEC-0045; Linus does not ship
permission-popup UX (delegated to the harness)" — would clarify the contract for downstream harness authors.
Worth a Phase 2a planning-update sub-section.

## 4. What's inspiration only

The **TypeScript-on-Node implementation** is not a code-lift target. Linus's orchestration core is Python (DEC-0027);
pi's package architecture (npm workspaces, lockstep versioning, TypeBox-as-schema) does not transpose. The
`@earendil-works/pi-ai` package's surface area is what's design-relevant; the implementation language is incidental.
Even if Linus eventually ships a TypeScript front-end (openclaw is TypeScript per the
[openclaw repo-note](openclaw.md)), the orchestration substrate stays Python and `pi-ai` is a reference for
**what the abstraction should cover**, not a candidate dependency for Linus's backend.

The **35-provider catalogue** is broader than Linus needs. Like goose's 40-provider catalogue (per the [goose
repo-note](goose.md) §4), pi's matrix targets a broad commercial product audience — Anthropic, OpenAI, Google,
Bedrock, Vertex, Azure, Mistral, Groq, Cerebras, xAI, OpenRouter, Vercel AI Gateway, plus eight Anthropic-compat
relabel providers (Fireworks, Kimi For Coding, Xiaomi MiMo across four regional billing plans). Linus's primary
substrates are local (pmetal, mlx-lm, Ollama; Phase 6+ fine-tuned variants) plus a small set of hosted endpoints
where Maestro/Worker delegation routes to a frontier model for hard reasoning. The 35-provider surface confirms
that "unified provider abstraction" is a real engineering need; the concrete provider modules are inspiration only,
not content to lift.

The **session-tree TUI navigation UX** (`/tree` / `/fork` / `/clone` interactive flow with Ctrl+← / Ctrl+→ / Alt+←
fold-and-jump, Shift+L bookmark labeling, Shift+T timestamp toggling) is pi's polished UX layer and is not
relevant to Linus's orchestration backend. The data shape (JSONL with `id` + `parentId`) is usefully liftable per
§3 above; the TUI is openclaw's or claw-code-local's concern, not Linus's.

The **`enableInstallTelemetry` + `pi.dev` update-check + install-ping triad** is pi's product-ops posture for a
public-distribution npm package. Linus has none of these concerns — it is single-user, single-developer, runs
locally only — and the equivalent in Linus is the absence of any such phone-home. Pi's three opt-out levers
(`PI_OFFLINE=1`, `PI_SKIP_VERSION_CHECK=1`, `PI_TELEMETRY=0`, plus `enableInstallTelemetry: false` in
settings.json) are a reasonable reference for what disclosure looks like when a tool does want telemetry — but
Linus's posture is "no telemetry by default, no opt-out needed because there's nothing to opt out from." The
pattern is inspiration only.

The **CLAUDE.md / AGENTS.md context-file convention** is interesting cross-pollination. Pi loads `AGENTS.md` or
`CLAUDE.md` at startup from `~/.pi/agent/AGENTS.md` (global), parent directories walking up from `cwd`, and the
current directory — and concatenates all matching files. This is structurally similar to Claude Code's context-file
loading. For Linus, the equivalent concern is what context files the orchestration backend exposes to Workers
(this is plausibly Linus's CLAUDE.md plus relevant ADRs per DEC-0026's planning write-back cadence), but the
loading mechanism is harness-side, not orchestration-side. Linus exposes context as a structured prefix the
dispatch layer renders; harnesses like pi may additionally load their own context files. The two systems are
complementary.

The **contributor-gate workflow** (auto-closing PRs/issues from new contributors via
`.github/workflows/issue-gate.yml` and `.github/workflows/pr-gate.yml`, with maintainer-approved `lgtm` / `lgtmi`
comments granting future submission rights) is pi's solution to open-source maintainer burden — a single-maintainer
project with a strict "I read auto-closed issues daily and reopen the ones that meet the quality bar" policy.
Linus is single-developer with no external contributors; the pattern is inspiration only and worth knowing about
if Linus ever opens to external contribution in Phase 8+, but not content to adopt today.

## 5. What's incompatible or out of scope

**pi is a coding-agent harness, not an orchestration backend (DEC-0017, DEC-0020).** Same asymmetric relationship
as goose: pi **consumes** model providers and tool extensions; Linus **is** the model provider (via DEC-0005's
OpenAI-compatible endpoint) and the MCP extension host (via DEC-0045's in-house MCP servers). Pi is downstream of
Linus, not parallel. Adopting pi as a Linus orchestration substrate would invert this and contradict DEC-0020. The
right relationship: Linus is one of pi's model providers; pi is one of several harnesses Linus exposes against.
The pi → openclaw → Linus chain (per §3 above) is the correct architectural layering.

**pi deliberately does not ship MCP** ([Mario Zechner's blog post](https://mariozechner.at/posts/2025-11-02-what-if-you-dont-need-mcp/)
cited in the README is the maintainer's full argument). Pi's posture is "MCP adds latency when shell commands plus
READMEs already work" — and the alternative pi proposes is the **CLI-tools-with-READMEs** + **Agent Skills standard**
shape (skills loaded from `SKILL.md` files that instruct the LLM how to invoke shell commands directly). For Linus,
which has committed to MCP via DEC-0018 and DEC-0045 (fastmcp as the default framework), pi's MCP-skepticism is
**inspiration only** — a data point in the harness-landscape debate, not a position Linus should adopt. Pi's
philosophical posture validates that "MCP everywhere" is not a settled position in the harness ecosystem; Linus's
counter is that the MCP-as-tool-substrate decision (DEC-0018) is locked in for orchestration-side reasons (typed
schemas, host-side capability discovery, cross-language compatibility) that pi's harness-side analysis does not
weigh equally. The two positions can coexist: Linus exposes MCP servers; pi consumers can opt to use pi extensions
that wrap Linus's MCP servers if they want them, or skip them entirely. The asymmetry is fine.

**pi deliberately does not ship sub-agents.** The README's philosophy section is explicit: "There's many ways to
do this. Spawn pi instances via tmux, or build your own with extensions, or install a package that does it your
way." For Linus, which has committed to multi-agent Worker fan-out as the Phase 3 architecture (DEC-0050 Role as
first-class type, DEC-0051 AgentReport as typed inter-agent message), pi's sub-agent-skepticism is inspiration
only — pi's tmux-shellout-or-extension-it approach is plausibly correct for a single-user terminal coding-agent,
but Linus's orchestration backend is exactly where sub-agent infrastructure belongs (per DEC-0020 bounded
orchestration scope). The Phase 3 spawner spec ([phase3-spawner.md](../specs/phase3-spawner.md)) is committed
work; pi's posture does not require revisiting it.

**The single-maintainer product-ops layer.** Pi ships GitHub workflows (`issue-gate.yml`, `pr-gate.yml`,
`approve-contributor.yml`), a `pi-share-hf` companion repo for publishing OSS coding-agent sessions to Hugging
Face, lockstep versioning across five packages, an npm-publish release pipeline, plus the `enableInstallTelemetry`
opt-out machinery for `pi.dev/api/report-install`. None of this applies to Linus, which is private and single-user.
The patterns are usefully visible (Mario Zechner's solo maintainer playbook is thoughtfully designed) but not
content to adopt.

**Agent Skills standard adoption commitment.** Pi explicitly adopts the [Agent Skills standard](https://agentskills.io)
for its skill format. Linus has not committed to the standard; the Phase 2+ Linus skill spec is implicit in
DEC-0045's fastmcp commitment plus the per-skill manifest conventions in `docs/repo-notes/agent-skills-for-context-engineering.md`.
Whether Linus should align its skill manifest to the Agent Skills standard for cross-harness portability is a
plausible open question for Phase 5+ — if openclaw consumes pi-shaped skills natively and Linus also wants to
expose Linus-bundled skills to pi/openclaw consumers, then matching the manifest format earns interop. But this is
a Phase 5+ question, not a Phase 2 commitment, and pi's adoption of the standard is a data point, not a forcing
function.

**The four-mode CLI (`interactive` / `--print` / `--mode json` / `--mode rpc`)** is pi's surface, not Linus's. Linus
ships an HTTP endpoint per DEC-0005; pi's RPC mode (LF-delimited JSONL on stdin/stdout) is a complementary
substrate for stdin/stdout-friendly consumers, but Linus's primary contract is HTTP. The patterns can coexist (a
Phase 5+ Linus-CLI shim could expose `linus --mode rpc` for stdin/stdout consumers), but that's out of scope today.

**OAuth subscription auth flows** (Claude Pro/Max via `loginAnthropic`, ChatGPT Plus/Pro via `loginOpenAICodex`,
GitHub Copilot via `loginGitHubCopilot`) are pi's answer to "let users use the subscriptions they already pay
for instead of separate API keys." Linus does not need this — Linus's primary substrates are local (no auth) plus
API-key-shaped hosted endpoints where the user manages keys directly. Pi's OAuth machinery is over-scoped for
Linus's threat model.

## 6. Recommendation: **Study**

Read pi's `packages/coding-agent/README.md` end-to-end as the canonical reference for what a deliberately-minimal
terminal coding-agent harness looks like, and the Philosophy section as a discipline anchor for Linus's own
"what we don't ship" articulation. Read `packages/ai/src/types.ts` and `packages/ai/src/providers/openai-completions.ts`
as the design reference for the per-Model `compat` field (the 17-flag `OpenAICompletionsCompat` enum is the most
comprehensive cross-provider compatibility surface in the cloned-repo collection). Read `packages/agent/README.md` and
the `Agent` class API for the event-stream shape, the `beforeToolCall` / `afterToolCall` hook surface, the
`terminate: true` tool-result hint, and the steering / follow-up queue semantics — all directly relevant to Linus's
Phase 2+ orchestration design. Skim `packages/coding-agent/AGENTS.md` for the parallel-agents git discipline; it's
a tighter version of CLAUDE.md's "Worktree fan-out discipline" engineering convention and a useful cross-check.

Cluster cell: [g7-harnesses](../syntheses/repo-clusters/g7-harnesses.md). pi belongs in the harness cluster
alongside `cline`, `claw-code`, `claw-code-local`, `openclaw`, `goose`, `claude-code-guide`, `claude-squad`,
`claude-task-master`, `codebuff`, `gravityfile`, `semanticworkbench`, and `jan`. Within that cluster pi is the
**TypeScript-side minimalist entrant** — the explicit counterpart to goose's "kitchen-sink Rust+MCP product"
posture, the philosophical opposite of cline's "everything in the harness" approach, and the substrate openclaw
already consumes via SDK integration. Secondary thematic home:
[agentic-systems-synthesis.md](../syntheses/agentic-systems-synthesis.md) for the deliberately-no-MCP /
deliberately-no-sub-agents / deliberately-no-plan-mode stance as a data point in the multi-agent landscape debate
(the contrarian counterposition to the synthesis's "role specialization at the right granularity" thread).

Do **not** vendor pi. Do **not** adopt pi's TypeScript-Node implementation in Linus's Python backend. Do **not**
inherit pi's MCP-skepticism — DEC-0018 / DEC-0045 are locked in for Linus's reasons. Three specific exceptions
where adopting pi patterns may be reasonable:

1. **The `OpenAICompletionsCompat` 17-flag enumeration** as a checklist for what Linus's Phase 2a
   `/v1/chat/completions` endpoint should document as advertised behaviors. One-paste reference; lets pi (and any
   other compat-flag-aware client) configure correctly out of the box.
2. **The session-tree JSONL shape with `parentId` pointers** as an alternative to (or evolution of) the workgraph
   linear-DAG shape for Linus's Phase 2a session store. The pi shape costs only the additional `parentId` field
   plus the navigation tooling; the UX upside is significant.
3. **The `terminate: true` per-tool-result hint** as the canonical Worker-termination signal in Linus's Phase 3
   AgentReport schema (DEC-0051). The shape is cleaner than goose's recipe-level `max_turns` and more granular
   than openai's stop-reason field.

All three are schema-shape lifts adapted to Linus idioms, not code lifts. The Linus implementation against the
Linus substrate is a separate deliverable per usual.

## 7. Questions for Dan

1. **pi as the canonical TypeScript-side Linus client reference for Phase 5+ openclaw integration.** Pi is named
   in `packages/coding-agent/README.md` as the substrate openclaw consumes ("See `openclaw/openclaw` for a
   real-world SDK integration"). When Linus's Phase 2a `/v1/chat/completions` endpoint is up, should pi be the
   canonical "TypeScript-side ground-truth client" against which the endpoint is regression-tested — i.e., a
   Phase 5b smoke-test invariant of "Linus's endpoint responds correctly when pi (running as openclaw's
   substrate) connects via `pi-ai`'s `openai-completions` provider"? The alternative is testing only via Python
   clients. Tentative answer: yes — pi is MIT-licensed, npm-installable in one command, the SDK is well-typed,
   and exercising the TypeScript-side endpoint compatibility from the same code path openclaw uses is much
   cheaper than wiring up a synthetic test harness. Worth committing to in the Phase 5b regression-suite plan
   alongside the goose Rust-side regression invariant (per the [goose repo-note](goose.md) §7 Open Question 1).

2. **Adopt pi's `OpenAICompletionsCompat` flag enumeration as the Phase 2a endpoint capability advertisement
   schema.** Pi's 17-flag enum is the most comprehensive cross-provider compatibility surface in the cloned-repo
   collection. Should Linus's Phase 2a endpoint adopt the same enum (with appropriate Linus-side semantics) as
   its capability-advertisement schema, exposed at e.g. `GET /v1/compat` or as a header on the response? The
   benefit is automatic compatibility with any `pi-ai`-aware client (pi itself, openclaw, future entrants). The
   cost is committing to a third-party schema that may evolve under pi's maintenance. Tentative answer: yes —
   adopt the schema, vendor a snapshot in `docs/specs/serving-protocol.md`, accept that future pi-ai changes may
   require Linus-side schema updates. The cross-harness interop value substantially exceeds the maintenance cost
   for a single-developer system.

3. **Phase 2a session-tree vs linear-DAG decision.** Workgraph's linear JSONL DAG is the current recommended
   Phase 2a session-store shape per CLAUDE.md and [g7-harnesses](../syntheses/repo-clusters/g7-harnesses.md);
   pi's tree-shape JSONL (with `parentId` pointers and `/tree` / `/fork` / `/clone` navigation) is the
   complementary alternative. For Linus's Maestro+Worker discipline, where exploratory branches are common
   (Maestro re-runs a Worker from an earlier point with revised guidance), the tree shape is plausibly the better
   fit. Should the Phase 2a session-store ADR commit to the tree shape from the start, or land on the linear
   shape with the tree feature deferred to Phase 3+? Tentative answer: commit to the tree shape from the start —
   the `parentId` field is one column; the navigation UX can be deferred to Phase 5+ harness work; the cost of
   migrating from linear to tree later is higher than the cost of building tree-shaped from day 1.

4. **pi's `terminate: true` tool-result hint adoption in DEC-0051 AgentReport.** Pi's per-tool-result `terminate`
   flag (set to `true` from `execute()` or `afterToolCall()`, takes effect only when every tool in the batch is
   terminating) is a clean Worker-termination signal. Should Linus's Phase 3 AgentReport (DEC-0051) adopt the
   same pattern — a terminal tool call like `linus.agent.report_final(report)` sets `terminate: true`, the
   spawner observes the signal and does not re-invoke the Worker? The alternative is a separate
   `agent.complete()` API call or a stop-reason-style signal. Tentative answer: yes — adopt the per-tool-result
   pattern, document in DEC-0051 update or a follow-on ADR. The pattern is more granular than stop-reasons and
   composes cleanly with parallel tool execution.

5. **Anthropic Agent Skills standard alignment for Phase 5+ cross-harness skill portability.** Pi adopts the
   [Agent Skills standard](https://agentskills.io) for its `SKILL.md` format. The standard is also adopted by
   `agent-skills-for-context-engineering` (cloned per the
   [agent-skills-for-context-engineering repo-note](agent-skills-for-context-engineering.md)) and by Claude
   Code's skill mechanism. Should Linus's Phase 2+ skill manifest format (currently implicit in DEC-0045 plus
   the per-skill conventions) align to the standard, so that Linus-bundled skills are consumable by pi /
   openclaw / Claude Code without per-harness adaptation? The cost is a small constraint on Linus's skill
   manifest fields (the standard prescribes some structure); the benefit is cross-harness portability for the
   Phase 7+ skill ecosystem. Tentative answer: yes when the Phase 5+ openclaw spec is drafted, defer the
   formal alignment to that ADR. A "Linus skills are Agent-Skills-standard-conformant" claim earns interop with
   the broader ecosystem and costs little.

6. **pi's philosophy section as a discipline anchor for Linus's "what we deliberately don't ship" articulation.**
   Pi's README §Philosophy is the clearest enumeration of harness non-features in the cloned-repo collection.
   Should ARCHITECTURE.md or the Phase 5+ planning ADR include a parallel section enumerating Linus's
   non-features — e.g., "Linus does not ship its own UI (delegated to openclaw / claw-code-local / pi); Linus
   does not ship plan-mode (delegated to harness skills); Linus does not ship permission-popup UX (delegated to
   the harness's `beforeToolCall` hook); Linus does not ship its own MCP server beyond DEC-0045's v0 set"? The
   value is bounded-scope clarity for downstream harness authors and for Linus's own discipline. Tentative
   answer: yes — the Phase 2a planning-update cycle (per DEC-0026) is the natural moment to draft this section
   for ARCHITECTURE.md.

7. **The `pi --mode rpc` substrate as a reference for a future `linus --mode rpc` stdin/stdout consumer
   interface.** Pi's RPC mode (LF-delimited JSONL on stdin/stdout) is the substrate for non-Node consumers that
   want to drive pi programmatically without HTTP. Linus's primary contract is HTTP (DEC-0005), but a parallel
   stdin/stdout interface would let stdin/stdout-friendly consumers (a future Linus CLI, a future
   editor-plugin sidecar, certain Unix-pipeline integrations) drive Linus without setting up an HTTP client.
   Should a Phase 5+ ADR commit to shipping a `linus serve --mode rpc` companion to the HTTP endpoint, with the
   same JSON envelope as the HTTP response shape? Tentative answer: defer to Phase 5+ — Linus's v0 contract is
   HTTP per DEC-0005; the rpc surface is a Phase 5+ convenience layer. Worth flagging in the Phase 5+ planning
   docs but not in v0 scope.

8. **pi-side openclaw consumption pattern: in-process SDK vs HTTP-only.** Pi's SDK is consumed in-process by
   openclaw via `createAgentSession(...)` — openclaw imports `@earendil-works/pi-coding-agent` and calls SDK
   methods directly. When Linus's Phase 2+ orchestration backend is up, the question becomes: does openclaw
   continue to consume pi's SDK in-process AND additionally call Linus's HTTP endpoint for orchestration-side
   features (Worker spawning, MCP tools, session store)? Or does openclaw migrate fully to Linus's HTTP endpoint
   and stop importing pi? Tentative answer: the in-process+HTTP hybrid is the right Phase 5 architecture —
   openclaw uses pi's SDK for TUI / session-tree / extension surface (the UX layer pi excels at) and Linus's
   HTTP endpoint for orchestration (the substrate Linus excels at). Worth documenting the hybrid pattern
   explicitly in the Phase 5 openclaw integration ADR so both pi and Linus understand the contract.
