# goose (`block/goose`)

## 1. Purpose and scope

goose is a **production Rust+MCP coding agent** — a desktop app, CLI, and embeddable agent server originally shipped by
Block (Square / Cash App / Tidal) under `block/goose` and now governed by the Agentic AI Foundation (AAIF) at the Linux
Foundation, with the live source repo at `aaif-goose/goose`. Apache-2.0, written in Rust, packaged as a Cargo workspace
of seven crates (`goose`, `goose-cli`, `goose-server`, `goose-mcp`, `goose-sdk`, `goose-acp-macros`, `goose-test` /
`goose-test-support`) plus an Electron/TypeScript desktop UI under `ui/`. The goose binary boots in three modes —
`goose agent` runs the OpenAPI server (codename **goosed**) that the desktop UI talks to, `goose mcp <server>` runs
goose's own MCP servers (`autovisualiser`, `computercontroller`, `memory`, `tutorial`) over stdio, and `goose-cli` is a
terminal-native chat REPL — all sharing the same `goose` core crate. Provider catalogue is broad (~40 modules in
`crates/goose/src/providers/` covering Anthropic, OpenAI, Google, Ollama, OpenRouter, Azure, Bedrock, Databricks,
Snowflake, Vertex, Groq, xAI, Mistral, plus ACP-bridged Claude / Codex / Cursor / Gemini-CLI / Copilot / Amp / Pi);
extensions plug in over MCP (stdio, streamable HTTP, plus a deprecated SSE shim and platform-extensions running
in-process). For Linus, goose is the **single most relevant Rust+MCP harness reference in the cloned-repo collection** —
the closest existing match to what `claw-code-local` and any future Phase 5+ Linus-native Rust harness will look like as
shipped products. It is a harness, not an orchestration backend (DEC-0017, DEC-0020); the right relationship is "Linus
exposes MCP, goose consumes it like any other MCP-aware Rust client."

## 2. Architecture summary

goose is a Cargo workspace pinned to Rust 1.91.1 with edition 2021 (`rust-toolchain.toml`, `Cargo.toml`). The seven
crates split as follows. **`goose`** is the core crate — ~41 top-level modules under `crates/goose/src/` covering the
agent loop (`agents/`), provider abstraction (`providers/`), MCP client (`agents/mcp_client.rs`), recipe DSL
(`recipe/`), Anthropic Agent Client Protocol bridge (`acp/`), security inspectors (`security/`), permission system
(`permission/`), context management (`context_mgmt/`), session storage (`session/`), conversation rendering
(`conversation/`), provider-side ACP shims (`providers/{claude,codex,gemini,copilot,amp,cursor,pi}_acp.rs`), and a
feature-gated local-inference path (`providers/local_inference/` using `llama-cpp-2` + `candle` + `tokenizers`).
**`goose-cli`** is the terminal entry point with subcommands under `commands/` (`configure`, `doctor`, `gateway`,
`info`, `plugin`, `project`, `recipe`, `schedule`, `session`, `term`, `update`). **`goose-server`** is the HTTP server
("goosed") that exposes ~25 axum routers under `routes/` — `agent.rs`, `recipe.rs`, `reply.rs`, `session.rs`,
`schedule.rs`, `mcp_app_proxy.rs`, `mcp_ui_proxy.rs`, `local_inference.rs`, `dictation.rs`, `setup.rs`, `tunnel.rs`,
`telemetry.rs`, etc. — and ships an OpenAPI spec generator (`openapi.rs`, regenerated via `just generate-openapi`).
**`goose-mcp`** packages goose's bundled MCP servers (`autovisualiser`, `computercontroller`, `memory`, `tutorial`,
`peekaboo` macOS-only) over the rmcp `transport-io` (stdio) shape. **`goose-sdk`** is currently a one-file stub exposing
`custom_requests` types shared between the agent and the ACP layer. **`goose-acp-macros`** ships proc macros for the
Anthropic Agent Client Protocol. **`goose-test` + `goose-test-support`** carry shared test infrastructure including a
recorded-MCP-tests harness (`just record-mcp-tests`).

The **MCP transport surface** is the Rust-side reference any Phase 5+ Linus harness should match. goose uses the
**rmcp** crate (Rust MCP SDK, the Rust analogue of fastmcp) — declared at workspace level as
`rmcp = { version = "1.5.0", features = ["schemars", "auth"] }` and feature-gated per-crate (`client` +
`transport-child-process` + four streamable-HTTP transports in `goose`; `server` + `client` + `transport-io` + `macros`
in `goose-mcp`). `crates/goose/src/agents/mcp_client.rs` defines the `McpClientTrait` (`list_tools`, `call_tool`,
`list_resources`, `read_resource`, `list_prompts`, `get_prompt`, `subscribe`, `unsubscribe`, `set_logging_level`,
`complete`) plus a `GooseMcpHostInfo` struct describing host capabilities including the `io.modelcontextprotocol/ui`
extension capability that toggles in MCP-UI rendering. Five **extension-config types** live in
`crates/goose/src/agents/extension.rs`: `Stdio { cmd, args, envs, env_keys, timeout, available_tools }` (child process
over stdio, the canonical pattern); `StreamableHttp { uri, envs, headers, timeout, socket, available_tools }` (MCP
Streamable HTTP, with optional Unix-domain-socket transport via the `socket` field — `@name` for Linux abstract
sockets); `Builtin` (one of goose's own MCP servers spawned in-process); `Platform` (in-process extension with direct
agent access — `orchestrator`, `apps`, `chatrecall`, `code_execution`, `developer`, `summarize`, `summon`, `todo`,
`tom`, `analyze`); `Frontend` (tools delegated to a UI-side handler); `InlinePython` (uvx-executed Python snippets
declared inline). The `Sse` variant is retained for backward-compatibility with old config files only and is documented
as no longer functional. The **Envs** wrapper enforces a 31-entry blocklist of dynamic-linker and process-injection
environment variables (`PATH`, `LD_PRELOAD`, `DYLD_INSERT_LIBRARIES`, `PYTHONPATH`, `NODE_OPTIONS`, `RUBYOPT`, `GOROOT`,
`APPINIT_DLLS`, etc.) so an extension config cannot escalate via env override. The **Streamable HTTP** transport is the
only network-attached extension shape goose ships actively; the legacy SSE transport is dead code preserved for config
parsing.

The **provider abstraction** at `crates/goose/src/providers/base.rs` is a `Provider` async trait with associated
`get_name`, `get_model_config`, `get_usage`, `complete` (returning a `MessageStream` of `ChatMessage` events), plus
provider-metadata helpers and a `ProviderDef` registration struct. Each of the ~40 provider modules implements the trait
and registers itself via `provider_registry.rs`. The **OpenAI-compatible shim** at `providers/openai_compatible.rs` is
the generic adapter — every OpenAI-API-compatible endpoint (Linus's eventual `/v1/chat/completions` endpoint included,
per DEC-0005) is reachable via the `OpenAiCompatibleProvider` constructor that takes
`(name, ApiClient, ModelConfig, completions_prefix)` and reuses the shared `ImageFormat::OpenAi` request shape from
`formats/openai.rs`. The **Ollama provider** (`providers/ollama.rs`) is first-class native: defaults to
`localhost:11434`, default model `qwen3`, known-models list includes `qwen3-vl`, `qwen3-coder:30b`,
`qwen3-coder:480b-cloud`, with Ollama-specific retry config (10 retries with 1.5x backoff up to 15s, anticipating the
30-120s model-load window during which Ollama returns 500s). The **local-inference path** (gated behind the
`local-inference` Cargo feature, on by default) loads GGUF weights via `llama-cpp-2` and integrates HuggingFace
tokenizers and `candle` for tensor ops; supports Metal on macOS, optional CUDA via `--features cuda` and Vulkan via
`--features vulkan`. Tool-calling for local models has two paths in `local_inference/`: `inference_native_tools.rs` for
models that support native tool-calling (Llama 3.1+, Qwen2.5+) and `inference_emulated_tools.rs` for models that don't,
with a tool-description prompt template and post-hoc parsing in `tool_parsing.rs`.

The **agent loop** at `crates/goose/src/agents/agent.rs` orchestrates the conversation, tool execution, retry handling,
permission gating, security inspectors, large-response handling, and context-window compaction. The `Agent` struct holds
an `ExtensionManager` (the registry of attached MCP extensions and their tool surfaces), a `PermissionManager` (approval
state per tool), an `AdversaryInspector` + `EgressInspector` chain (defense-in-depth security scanners that inspect tool
calls and outputs against pattern-based threat libraries in `security/patterns.rs` and `security/scanner.rs`), an
`ActionRequiredManager` (handles MCP elicitation / sampling / human-in-the-loop pauses), and a `Container` (process / FS
/ extension state holder). The **subagent** machinery (`agents/subagent_handler.rs`, `agents/subagent_execution_tool/`,
`agents/subagent_task_config.rs`) lets a parent agent spawn child agents to execute subtasks against scoped recipes —
this is goose's analogue of a Worker fan-out pattern, scoped per-task with its own conversation, tool surface, and
notification channel. The `run_subagent_task` entry takes a `SubagentRunParams` carrying `AgentConfig`, `Recipe`,
`TaskConfig`, `return_last_only`, `session_id`, optional `cancellation_token`, optional `on_message` callback, and
optional `notification_tx` for streaming server notifications back up.

The **Recipe DSL** at `crates/goose/src/recipe/` is goose's most distinctive shipped abstraction. A `Recipe` struct
carries `version` (semver), `title`, `description`, optional `instructions` (system-prompt-shaped guidance), optional
`prompt` (the opening user turn), optional `extensions: Vec<ExtensionConfig>`, optional `settings` (`goose_provider`,
`goose_model`, `temperature`, `max_turns`), optional `activities` (UI hints), `author`, `parameters` (typed parameter
slots with `key`, `input_type`, `requirement`, `description`, `default`), optional `response` (JSON-schema constrained
output), optional `sub_recipes` (compositional task graph), and optional `retry` config. Recipes are YAML or JSON
(`recipe/read_recipe_file_content.rs`, `recipe/local_recipes.rs`, `recipe/template_recipe.rs`,
`recipe/validate_recipe.rs`, `recipe/build_recipe/`); they support templating via parameter substitution and can be
deep-linked (`recipe_deeplink.rs`). The `recipe-scanner/` directory at the workspace root ships a Docker-packaged "Goose
Recipe Security Scanner v2.1" that runs an autonomous security analysis of a recipe before execution — checking for
embedded URL fetches, malicious shell snippets, unicode-tag obfuscation, and shell-redirect attacks against environment
variables. The recipe shape is essentially "a portable, reviewable agent task spec" — comparable to Letta's Agent File
but task-scoped rather than full agent-state, and oriented around human authoring rather than agent serialization.

The **Anthropic Agent Client Protocol (ACP) bridge** at `crates/goose/src/acp/` is goose's interop layer with
Anthropic's emerging client protocol (the protocol Claude Code, Cursor, Codex, and Zed converge on). The module provides
server-side ACP support (so goose can present its agent surface as an ACP server consumable by ACP-aware clients) and
provider-side ACP shims (`providers/{claude,codex,gemini,copilot,amp,cursor,pi}_acp.rs`) so goose can **consume external
ACP-shaped agents as if they were LLM providers** — this is how goose bridges to existing Claude Code subscription auth,
Codex CLI, Gemini CLI, GitHub Copilot, Amp, and Pi. The `goose-acp-macros` crate provides proc macros that generate the
protocol's request/response plumbing. Combined with the OpenAI-compatible shim, this gives goose three protocol shapes
simultaneously: native HTTP per provider, OpenAI-compatible HTTP via `OpenAiCompatibleProvider`, and ACP via the
`*_acp.rs` providers — a multi-protocol stance worth noting against DEC-0005's OpenAI-only commitment.

The **goose-server (goosed)** binary at `crates/goose-server/src/main.rs` is the OpenAPI-spec'd HTTP backend. Three
subcommands: `Agent` (the full chat server with axum routers under `routes/`), `Mcp` (runs one of the bundled MCP
servers in stdio mode — `autovisualiser`, `computercontroller`, `memory`, `tutorial`), and `ValidateExtensions`
(static-checks a bundled-extensions JSON file). The `Cli` parser is via `clap` derive macros; the boot path emits
`GOOSED_BOOT:` markers for the desktop UI's spawn-and-wait protocol and installs a custom panic hook. Routes include
`/agent/*` (agent lifecycle), `/recipe/*` (recipe execution and validation), `/session/*` (session events and state),
`/schedule/*` (cron-style recipe scheduling), `/mcp_app_proxy/*` and `/mcp_ui_proxy/*` (MCP-UI rendering proxies),
`/local_inference/*` (gated behind the `local-inference` feature), `/dictation/*` (audio transcription), `/setup/*`
(first-run wizard), `/tunnel/*` (cloudflared/ngrok tunnel for desktop-UI access from elsewhere on the LAN),
`/telemetry/*` (PostHog opt-in event sink). Each route is `utoipa`-annotated so `just generate-openapi` produces the
desktop UI's TypeScript clients via the OpenAPI spec.

Outside the workspace, the repo carries a few Linus-relevant ancillary directories. **`recipe-scanner/`** is the
Docker-packaged security analysis pipeline for user-submitted recipes (`scan-recipe.sh`, `base_recipe.yaml`,
`Dockerfile`, `decode-training-data.py`) — runs an autonomous goose agent inside a sandboxed container that downloads
referenced resources, scans for malware/rootkit/backdoor indicators, and emits a 0-100 risk score in a structured JSON
envelope. **`oidc-proxy/`** is a Cloudflare Worker (TypeScript via wrangler) that authenticates GitHub Actions OIDC
tokens to upstream APIs — a CI-side substrate for letting GitHub workflows call goose-protected endpoints without
storing long-lived secrets. **`services/ask-ai-bot/`** is a TypeScript Discord/Slack-bot ancillary running on Bun.
**`evals/`**, **`workflow_recipes/`**, and **`examples/`** carry runnable demos. The **`ui/`** Electron+React desktop
app (94 MB after `--depth=1` clone) consumes the goosed OpenAPI; the **`documentation/`** directory (506 MB,
Docusaurus-rendered) is the goose-docs.ai content. `bin/activate-hermit` provides a hermetic dev-tools shell via the
Hermit toolchain manager so contributors don't need cargo/just/pnpm globally installed. Notable license note: every
upstream dependency is permissively licensed; the workspace uses `cargo-deny` (`deny.toml`) to enforce license
allowlists at CI time.

## 3. What's reusable in Linus

goose's contribution to Linus is structural and design-reference rather than substantive — Linus does not vendor goose,
but its trait shapes, transport surface, and engineering choices are the canonical Rust+MCP harness reference for any
Phase 5+ Linus-native Rust component or any external Rust harness consuming Linus's orchestration backend.

**Phase 2a — OpenAI-compatible HTTP boundary as a drop-in target for goose's `OpenAiCompatibleProvider` (DEC-0005).**
Once Linus's `/v1/chat/completions` endpoint is up in Phase 2a, goose can point at it via the existing
`OpenAiCompatibleProvider` constructor in `providers/openai_compatible.rs` with no goose-side code changes — configure
`OPENAI_BASE_URL=http://localhost:<linus-port>/v1` plus an `OPENAI_API_KEY=anything` and goose treats Linus as a peer to
OpenAI, Azure, xAI, Together, OpenRouter, etc. This validates DEC-0005's bet that OpenAI-compatible HTTP is the right
protocol surface for harness portability — goose joins Cline, openclaw, claw-code-local, Letta-as-client, and
rig-via-`OpenAIExt` as confirmed Phase 2 clients.

**Phase 5+ — goose's MCP transport and extension-config taxonomy as the Rust+MCP shape reference for any Linus-native
Rust harness (DEC-0018, DEC-0045).** The five extension-config variants (`Stdio`, `StreamableHttp`, `Builtin`,
`Platform`, `Frontend` — plus the no-op `Sse` retained for parsing compat — and the `InlinePython` uvx escape hatch) are
a worked taxonomy of how a Rust agent host factors its plugin surface across child-process / network / in-process /
UI-delegated / inline-script extension shapes. The **Streamable HTTP variant with optional Unix-domain socket
transport** (`socket: Option<String>` with `@name` Linux abstract socket support) is non-obvious prior art worth
lifting: when a Linus Phase 5+ harness needs to talk to a Linus-side MCP server colocated on the same machine,
UDS-shaped transport is faster than localhost TCP and can carry Unix peer credentials for authentication. The
`McpClientTrait` shape (`list_tools`, `call_tool`, `list_resources`, `read_resource`, `list_prompts`, `get_prompt`,
`subscribe`, `unsubscribe`, `set_logging_level`, `complete`) is the canonical full-surface client trait — Linus's own
Phase 3 in-house MCP host (DEC-0045: fastmcp is the Python-side default; rmcp is the Rust-side counterpart) should match
this verb set.

**Phase 5+ — `Envs` blocklist as a Linus extension-config security baseline.** goose's 31-entry environment-variable
blocklist (`PATH`, `LD_PRELOAD`, `DYLD_INSERT_LIBRARIES`, `LD_LIBRARY_PATH`, `LD_AUDIT`, `PYTHONPATH`, `PYTHONHOME`,
`NODE_OPTIONS`, `RUBYOPT`, `GEM_HOME`, `CLASSPATH`, `GOROOT`, `APPINIT_DLLS`, `ComSpec`, `TEMP`, `TMP`, `LOCALAPPDATA`,
`USERPROFILE`, `HOMEDRIVE`, `HOMEPATH`, etc.) in `Envs::DISALLOWED_KEYS` is a defense-in-depth list any Linus
extension-config schema should match. The pattern — every environment variable an extension config can set is validated
against this list at `Envs::new` time, with a `validate()` method that errors if a forbidden key reappears later — is
directly portable to a Linus Pydantic validator on the equivalent Linus extension-config schema. Cost: copy the list
once, update it when a new dynamic-linker-hijack variable lands in someone's CVE feed.

**Phase 5+ — Recipe DSL as a reference for the Linus task-spec / agent-card format (DEC-0050, DEC-0051).** Goose's
Recipe shape (typed parameter slots with `key` / `input_type` / `requirement` / `description` / `default`, optional
`response.json_schema` for structured output, `sub_recipes` for compositional task graphs, `settings` for provider /
model / temperature / max-turns binding, `extensions` for MCP-server attachment) is an existing reference for what a
Linus Phase 3 agent-spawner task spec or a Linus skill manifest should cover. Where Letta's Agent File is the "savefile"
reference (DEC-0050 agent serialization) and the workgraph JSONL DAG is the "session-store" reference (Phase 2a session
store), goose's Recipe is the **task-spec** reference: a portable, reviewable, parameter-templated task description that
an agent (or a fan-out of subagents) executes. The `sub_recipes` field in particular maps onto the Phase 3 Worker
fan-out pattern (DEC-0050 `Role` as a first-class type; DEC-0051 `AgentReport` as the typed inter-agent message): a
parent recipe declares its sub_recipes, the spawner schedules them as Worker invocations, and each sub_recipe's typed
`parameters` + `response.json_schema` form the AgentReport contract. The Recipe Security Scanner (`recipe-scanner/`) is
also a Phase 7+ reference for the "machine-screen-an-agent-task-before-execution" pattern — relevant when Linus
eventually accepts user-submitted skill manifests or recipes.

**Phase 5c — goose as a directly-reachable harness for testing the Linus orchestration backend in Rust-native form.**
Once Phase 2a Linus is up and Phase 5c lands `claw-code-local` as the primary terminal harness (DEC-0021), goose becomes
the **second** Rust+MCP harness that can drive Linus through its OpenAI-compatible endpoint. The two harnesses exercise
different surface area: claw-code-local is Claude-Code-style REPL with Anthropic-shaped chat templates and slash-command
UX; goose is a recipe-driven, multi-agent, security-scanned, multi-provider harness with an Electron desktop UI. Having
both available means Phase 5+ regressions are caught from two independent client codebases — useful empirical coverage.
The `goose-mcp` crate shipping its own MCP servers also means a Linus-side MCP server can be tested from goose with one
config-file edit; goose's bundled servers (`developer`, `memory`, `computercontroller`, `autovisualiser`) are useful
comparison points for what a Linus equivalent should expose.

**Phase 5+ — Anthropic ACP support as a third confirming signal for revisiting DEC-0005's OpenAI-only commitment.** Per
the [Letta repo-note](Letta.md) §3 and the [Kimi-K2 repo-note](Kimi-K2.md) §3, Anthropic-compatible HTTP endpoints are
shipping alongside OpenAI-compatible endpoints in modern open-source agent products. goose's full ACP integration — both
server-side (goose presents an ACP surface) and client-side (goose consumes Claude Code, Cursor, Codex, Gemini, Copilot,
Amp, Pi as ACP-shaped providers) — adds a **third** confirming signal that the protocol landscape is moving plural
rather than single. DEC-0005 commits Linus to OpenAI-compatible-only at v0; the third signal sharpens the case for a
Phase 5+ ADR on Anthropic-compatible (or full ACP) HTTP as a Linus capability. The natural shape: Linus exposes
OpenAI-compatible HTTP as the v0 contract per DEC-0005, and Phase 5+ adds ACP as a second endpoint shape so any
ACP-aware Rust harness (goose included) can talk to Linus natively without going through the OpenAI shim.

**Phase 5+ — local-inference path as a confirming signal for the multi-tier provider story.** goose's `local-inference`
Cargo feature (on by default) loads GGUF models via `llama-cpp-2` plus `candle` for tensor ops, supports Metal on macOS,
optional CUDA via `--features cuda`, and ships native + emulated tool-calling paths in `local_inference/`. This is the
Rust-side analogue of what Linus's Phase 1b inference bake-off (pmetal vs mlx-lm vs Ollama) is evaluating; the practical
takeaway is that **two-tier tool-calling** (native for Llama 3.1+ / Qwen2.5+, emulated for older / smaller models) is
the realistic shape for a tool-using local-model path. Linus's Phase 2a Worker registry should distinguish models by
their tool-calling tier, matching goose's internal split.

**Phase 5+ — clippy-deny posture for Linus Rust components.** goose's workspace lint posture — `string_slice = "warn"`,
`uninlined_format_args = "allow"`, plus the per-crate dependencies on `tracing`, `anyhow`, `thiserror`, `tokio`, and a
single `Apache-2.0` license across the workspace — is a reasonable baseline for any Linus-internal Rust crate. Pair it
with rig's stricter lint set (per the [rig repo-note](rig.md) §3) when codifying a Linus Rust conventions section in
CLAUDE.md.

## 4. What's inspiration only

The **Electron+React desktop UI** under `ui/desktop/` is goose's primary user surface — not relevant to Linus, which
already commits to openclaw as the Phase 5 front-end ([openclaw.md](openclaw.md)). The desktop UI's interaction with
goosed via OpenAPI-generated TypeScript clients is a useful pattern for any Phase 8+ Linus-native desktop story but not
content to lift.

The **40-provider catalogue** is more breadth than Linus needs. The provider modules useful to Linus are
`openai_compatible.rs` (for talking to Linus's own endpoint), `ollama.rs` (for direct Ollama bypass during Phase 1
inference work), and conceptually the local_inference path (for the Phase 1b pmetal / mlx-lm comparison). Anthropic,
Bedrock, Databricks, Snowflake, Vertex, Google, Azure, Cohere, Mistral, Groq, xAI, etc. are all hosted-LLM providers
Linus does not target as primary substrates. The catalogue's existence is a confirming signal that "unified provider
abstraction" is a real engineering need; the modules themselves are inspiration only.

The **OIDC proxy** (`oidc-proxy/` Cloudflare Worker) is Block / AAIF infrastructure for letting GitHub Actions workflows
authenticate to upstream APIs without long-lived secrets. Linus has no comparable CI-against-hosted-API need; the
substrate (Cloudflare Workers + wrangler) is also outside Linus's stack. The pattern (OIDC token validation + API key
injection at a proxy) is worth knowing about for any future Linus-CI-against-Linus-endpoint scenario but not content to
adopt.

The **tunnel surface** (`crates/goose-server/src/tunnel.rs`, `routes/tunnel.rs`) supports cloudflared / ngrok tunnels so
the desktop UI can reach goosed from another machine on the LAN. Linus's Phase 5+ openclaw deployment will plausibly
need a similar story (LAN-reachable Linus endpoint for an iPad / phone client), but the tunnel implementation depends on
third-party tunnel binaries that Linus does not need to ship.

The **PostHog opt-in telemetry** (`crates/goose/src/posthog.rs`, gated behind the `telemetry` feature) plus the OTel
instrumentation (`telemetry/` and `otel/` modules, gated behind `otel`) reflect goose's product-ops posture. Linus's
audit log will need observability eventually, but goose's stack — PostHog for product analytics, OTel for distributed
tracing — is heavier than the local-first single-user posture warrants. Useful as a reference for what an audit-log
schema should cover (per-call request/response, latency, model, provider, tool calls); not content to adopt.

The **`bin/activate-hermit` hermetic dev-shell** is goose's solution to "contributors shouldn't need cargo/just/pnpm
globally installed." Linus uses conda + uv (DEC-0024) for Python; the equivalent question for Rust is open. The Hermit
pattern is a reasonable answer if Linus ever fans out a Rust component that wants reproducible toolchain pinning; for
now, `rust-toolchain.toml` in any Linus Rust crate is sufficient.

The **multi-version agent loop discipline** (the absence of a `letta_agent_v2.py` / `_v3.py`-style fanout in the goose
codebase, in contrast to Letta) suggests goose has been more aggressive about replacing the agent loop in-place rather
than versioning it. The lesson: per-feature feature-flagging (`code-mode`, `local-inference`, `aws-providers`,
`telemetry`, `otel`, `rustls-tls`, `native-tls`) is goose's primary backward-compatibility surface, not loop versioning.
For Linus's eventual agent loop, this is the cleaner pattern when it works; fall back to Letta-style versioning only
when a feature flag can't carve the change cleanly.

## 5. What's incompatible or out of scope

**goose is a coding-agent harness, not an orchestration backend (DEC-0017 harness plurality, DEC-0020 orchestration
scope is bounded).** The fundamental relationship is asymmetric: goose **consumes** model providers and MCP extensions;
Linus **is** the model provider (via its OpenAI-compatible endpoint) and the MCP extension host (via its in-house MCP
servers per DEC-0045). Goose is downstream of Linus, not parallel to it. Adopting goose as a Linus orchestration
substrate would invert this relationship and contradict DEC-0020 explicitly. The right relationship is "Linus is goose's
provider; goose is one of several harnesses Linus exposes against."

**goose is a substantial product with Block / AAIF organizational coupling.** The codebase carries product-level
infrastructure — PostHog telemetry, OTel exporters, Cloudflare-Workers OIDC proxy, GitHub-Actions CI matrix, Discord
ask-ai-bot service, governance docs (`GOVERNANCE.md`, `MAINTAINERS.md`), DCO sign-off requirement (`git commit -s`),
custom-distros support (`CUSTOM_DISTROS.md`) for vendors who fork-and-rebrand — that reflect goose-the-product, not
goose-the-pattern. Linus is single-user and personal; none of this organizational machinery applies. The bare patterns
worth lifting (extension-config taxonomy, MCP transport surface, recipe DSL, OpenAI-compat shim) are extractable without
inheriting the org-shaped scaffolding, but they have to be extracted, not vendored.

**The desktop / electron / TypeScript surface is heavier than Linus's Phase 5 plan.** The `ui/` directory is 94 MB of
Electron+React+TypeScript with its own pnpm workspace, OpenAPI-generated TypeScript clients, and Tauri sub-app under
`ui/goose2/src-tauri` (excluded from the Cargo workspace). Linus's Phase 5 commits to openclaw as the front-end
([openclaw.md](openclaw.md)); duplicating the desktop work via goose's UI is out of scope. The goosed HTTP server alone
(without the desktop UI) is a reasonable comparison point for what a Linus orchestration backend's HTTP layer should
look like, but Linus's orchestration backend is Python (DEC-0027 multi-language stance: Python is the core orchestration
language) and the goosed shape transposes only as design reference, not as implementation lift.

**goose's local-inference path duplicates Linus's Phase 1b inference work, not complements it.** The
`providers/local_inference/` module loads GGUF via `llama-cpp-2` and uses `candle` for tensor ops — directly overlapping
with Linus's pmetal and mlx-lm Phase 1b candidates. The gain from goose's path (multi-OS / multi-arch via the `cuda` and
`vulkan` feature flags) is not relevant to Apple Silicon; the loss is that `llama-cpp-2` does not expose Apple's ANE the
way pmetal does (DEC-0006 / DEC-0049). Linus's Phase 1b bake-off measures pmetal vs mlx-lm vs Ollama on Apple
Silicon-specific axes; goose's local-inference is downstream of Ollama on the same axis and adds no new measurement. Out
of scope as a Phase 1 input.

**goose's recipe-scanner is over-scoped for Linus's threat model.** The Docker-packaged 0-100-risk-score security
analyzer is goose-the-product's answer to "users will share recipes online; we need to screen them." Linus is
single-user (Dan); Dan-authored skill manifests do not require autonomous-AI security scanning. The scanner pattern
(sandboxed agent inspects a task spec before execution) is a Phase 7+ reference for when Linus accepts external skill
contributions, but the v0 surface is over-scoped. Skip until Phase 7+ at the earliest.

**The Block-name backward-compatibility commitment.** `goose-mcp/src/lib.rs` keeps `top_level_domain: "Block"` /
`author: "Block"` in `APP_STRATEGY` because changing it would orphan existing user config / data directories. AAIF
inherits this technical debt. For Linus, which is greenfield, this is a reminder to **fix the directory layout naming up
front** (`~/.linus/...` per DEC-0029, not `~/.scratch/...` or `~/.daniel/...` that would later need backward-compat
aliasing).

**goose is fundamentally Apache-2.0 with permissive transitive deps; vendoring is permissively-licensed but the right
posture is still "do not vendor."** Apache-2.0 is the standard permissive license and would be Linus-compatible if
vendoring were on the table. But it isn't: Linus's posture is "study the patterns, ship the Linus implementation against
the Linus substrate." goose is too large and too organizationally-coupled to vendor cleanly; the engineering discipline
cost (tracking upstream churn, merging Block/AAIF feature work into a Linus fork) outweighs any code-reuse benefit. The
lift is at the design level only.

## 6. Recommendation: **Study**

Read goose's MCP-side and provider-side architecture as the canonical Rust+MCP harness reference. Specifically: read
`crates/goose/src/agents/mcp_client.rs` (the `McpClientTrait` full surface and the `GooseMcpHostInfo` capability struct)
and `crates/goose/src/agents/extension.rs` (the five-variant `ExtensionConfig` enum and the `Envs` blocklist) end-to-end
as the design reference for any Linus Phase 5+ Rust harness's plugin surface. Read
`crates/goose/src/providers/openai_compatible.rs` plus `crates/goose/src/providers/ollama.rs` plus
`crates/goose/src/providers/base.rs` as the Rust-side provider-trait reference, comparing against rig's typestate
`AgentBuilder` (per [rig.md](rig.md) §2) — goose is the Rust-product reference; rig is the Rust-library reference. Read
`crates/goose/src/recipe/mod.rs` and a couple of the bundled recipes under `recipe-scanner/base_recipe.yaml` and
`workflow_recipes/` for the Recipe DSL's surface and feel; this is the closest existing reference for what a Linus Phase
3 task-spec format should cover. Skim `crates/goose/src/agents/agent.rs` and
`crates/goose/src/agents/ subagent_handler.rs` for the Worker-fan-out shape goose's subagent machinery implements. Read
`crates/goose-server/src/main.rs` for the `goose agent` / `goose mcp <server>` CLI dispatch pattern as the design
reference for any future `linus agent` / `linus mcp <server>` CLI.

Cluster cell: [g7-harnesses](../syntheses/repo-clusters/g7-harnesses.md). goose belongs in the harness cluster alongside
`cline`, `claw-code`, `claw-code-local`, `openclaw`, and `claude-code-guide`. Within that cluster goose is the **shipped
Rust+MCP entrant** the cluster was previously missing — the [Canteen survey](../../context/notes/
canteen*blog_landscape_2026-05.md) calls goose "the meaningful Rust+MCP entrant currently missing" from the corpus
([Canteen, \_AI Agent Landscape*, 2026-01-06](../../context/notes/canteen_blog_landscape_2026-05.md)). g7-harnesses.md
already names goose as "the same shape claw-code-local will eventually take: a Rust-native coding agent that consumes
Linus's MCP surface as a first-class client" (line ~199). With this repo-note in place, the harness-cluster synthesis
has a primary-source target on the Rust+MCP side.

Secondary cluster cell: [g6-mcp-tools](../syntheses/repo-clusters/g6-mcp-tools.md) for the bundled-MCP-server pattern
(`goose-mcp`'s autovisualiser / computercontroller / memory / tutorial / peekaboo servers as design references for what
a Linus-bundled MCP-server crate should look like). Tertiary thematic home:
[agentic-systems-synthesis.md](../syntheses/agentic-systems-synthesis.md) for the recipe DSL's place in the
agent-task-spec landscape alongside Letta's Agent File and workgraph's JSONL DAG.

Do **not** vendor goose. Do **not** adopt it as the Linus orchestration substrate. The two specific exceptions where
adopting actual goose patterns may be reasonable:

1. **The `Envs::DISALLOWED_KEYS` blocklist.** Copy the 31-entry list verbatim into the Linus Pydantic validator on the
   Linus extension-config schema; update when a new dynamic-linker-hijack variable lands in CVE feeds. Cost is one
   paste; the security posture upside is concrete.
2. **The five-variant `ExtensionConfig` taxonomy** as a starting point for the Linus extension-config Pydantic shape,
   adapted to Python idioms. The variant set (`Stdio`, `StreamableHttp` with optional UDS socket, `Builtin`, `Platform`,
   `Frontend`, plus `InlinePython` as the inline-script escape hatch) is well-thought-out and the
   `available_tools: Vec<String>` per-variant whitelist is non-obvious but load-bearing.

Both are schema-shape lifts, not code lifts. The Linus implementation against the Linus substrate is a separate
deliverable.

## 7. Questions for Dan

1. **goose as the canonical Phase 5+ Rust-client reference for Linus MCP server testing.** When Linus exposes its own
   MCP servers (Phase 3+, per DEC-0045), should goose be the canonical "Rust-side ground-truth client" the Linus MCP
   servers are tested against — i.e., a Phase 3+ smoke-test invariant of "Linus's `linus.memory.episodic` MCP server
   responds correctly when goose connects via Streamable HTTP"? The alternative is testing only against Python
   fastmcp-based clients (Linus's own Python orchestration layer is the primary consumer). Tentative answer: yes — goose
   is permissively licensed, easy to install, and exercises the same `rmcp` Rust SDK any other Rust harness would use;
   using it as the Rust ground-truth client is much cheaper than wiring up a synthetic test harness from scratch. Worth
   committing to in the Phase 3 MCP host spec ADR.

2. **Phase 5+ openclaw vs claw-code-local vs goose — which Rust+MCP harness becomes the Linus reference?** Phase 5
   commits openclaw as the polished UI ([openclaw.md](openclaw.md)) and Phase 5c commits claw-code-local as the terminal
   harness ([claw-code-local.md](claw-code-local.md)). goose adds a third option: a recipe-driven, Apache-2.0,
   full-Rust-stack harness with built-in security scanning, multi-agent subagent machinery, and an Electron desktop UI.
   Three plausible postures: (a) defer goose entirely — Phase 5 is openclaw-and-claw-code-local only; (b) add goose as a
   third Phase 5b regression harness, used for testing Linus's OpenAI-compat boundary against an independent Rust
   client; (c) more aggressively, evaluate goose-as-front-end against openclaw at Phase 5 commit time, using actual
   usage data to pick the winner. Tentative answer: (b) — goose is too large to adopt as front-end without contradicting
   DEC-0020, but it is too useful as a regression check to skip entirely. Document "goose is the Rust+MCP regression
   harness" in the Phase 5 plan.

3. **Recipe DSL as the Phase 3 task-spec format.** Goose's Recipe shape (`title`, `description`, `instructions`,
   `prompt`, `extensions`, `settings { goose_provider, goose_model, temperature, max_turns }`, `parameters` with typed
   slots, `response.json_schema` for typed output, `sub_recipes` for compositional task graphs, `retry` config) is a
   strong existing reference for the Linus Phase 3 task-spec format the spawner spec
   ([phase3-spawner.md](../specs/phase3-spawner.md)) currently leaves open. The alternative is Letta's Agent File shape
   (richer state-bundle, oriented around full agent serialization rather than task-scoped specification). Should the
   Phase 3 spawner spec adopt goose's Recipe shape (renamed to "TaskSpec" in Linus vocabulary; the typed parameters +
   JSON-schema response are directly applicable to AgentReport per DEC-0051) or Letta's Agent File shape, or a hybrid
   (Recipe-shape for the per-task spec, Agent File-shape for the per-agent serialization)? Tentative answer: hybrid —
   Linus's Phase 3 spawner needs both (a per-task TaskSpec for what the Worker does, a per-agent AgentState for what the
   Worker carries between turns), and the two formats serve different roles. Worth a Phase 3 spawner-spec ADR alongside
   DEC-0050.

4. **Anthropic ACP support as a Phase 5+ Linus capability — third confirming signal.** Per Letta ([Letta.md](Letta.md)
   §3), Kimi-K2 ([Kimi-K2.md](Kimi-K2.md) §3), and now goose (full ACP server-side + provider-side support), three
   independent products ship Anthropic-compatible HTTP endpoints alongside OpenAI-compatible ones. DEC-0005 commits
   Linus to OpenAI-compatible-only at v0. Three confirming signals from independent products is enough evidence to
   commit to a Phase 5+ ADR — should Phase 5+ planning include an "Anthropic-compatible / ACP HTTP as a Linus
   capability" ADR alongside the orchestration-backend Phase 2a work? Tentative answer: yes — promote this from "open
   question" to "scheduled Phase 5+ ADR." The cost of supporting ACP alongside OpenAI-compat is a second router shape;
   the upside is that any ACP-aware Rust harness (goose, plus future entrants) can talk to Linus natively without going
   through the OpenAI shim. Schedule the ADR for Phase 5+ planning.

5. **`Envs` blocklist adoption — copy directly, or fold into a broader Linus security-posture spec?** Goose's 31-entry
   environment-variable blocklist is the most concrete dynamic-linker-hijack defense in the cloned-repo collection.
   Direct adoption is one paste into the Linus extension-config validator; the alternative is a broader Linus
   security-posture spec covering env blocklists, sandbox tiers (per SAFETY.md autonomy graduation), permission gating,
   and security-inspector chains (goose's `AdversaryInspector` + `EgressInspector` chain is also relevant here).
   Tentative answer: direct adoption now, broader spec in Phase 7+ when the Linus skills surface widens enough to
   justify the heavier framework. The blocklist is a one-paste improvement; the broader spec is a Phase 7+ deliverable.

6. **goose-mcp bundled-server crate as a reference for a Linus equivalent.** The `goose-mcp` crate ships four bundled
   MCP servers (`autovisualiser`, `computercontroller`, `memory`, `tutorial`, plus `peekaboo` macOS-only) over the
   `transport-io` (stdio) shape, with a `mcp_server_runner` that the goose-server CLI's `mcp` subcommand dispatches to.
   Should Linus ship a comparable in-house MCP-server bundle (per DEC-0045: fastmcp-built MCP servers under
   `src/linus/skills/mcp/`), and if so, what's the v0 server set? Tentative answer: yes — Linus's Phase 3 MCP host spec
   should commit to a v0 server set covering at minimum (a) `linus.memory.episodic` (Layer C surface per DEC-0029,
   MCP-mediated read/write/search), (b) `linus.knowledge.kb` (KnowledgeBase retrieval surface per DEC-0044's paper-qa
   integration), (c) `linus.agent.spawner` (the Phase 3 spawner exposed as an MCP tool surface per DEC-0050). Cluster
   cell [g6-mcp-tools.md](../syntheses/repo-clusters/g6-mcp-tools.md) is the natural home for the comparison; goose-mcp
   belongs in the canon there alongside agentmemory's 51-tool MCP and Letta's ~12-tool MCP (per [Letta.md](Letta.md) §3
   Open Question 2).

7. **Subagent execution as a Phase 3 fan-out reference.** Goose's `subagent_handler.rs` + `subagent_execution_tool/`
   - `subagent_task_config.rs` machinery implements task-scoped child-agent dispatch with per-subagent conversation,
     tool surface, cancellation tokens, and notification-channel streaming back to the parent. This is the closest
     existing Rust reference for the Phase 3 spawner pattern (DEC-0050 Role + DEC-0051 AgentReport). Should the Phase 3
     spawner spec name goose's subagent shape as the design reference alongside Letta's manager-taxonomy shape
     (round-robin / supervisor / dynamic / sleeptime / voice-sleeptime per [Letta.md](Letta.md) §3)? Tentative answer:
     yes — Letta's reference is for the manager-taxonomy vocabulary (which scheduling strategy the parent uses); goose's
     reference is for the per-subagent execution shape (how a single child is invoked with what state). Both are useful,
     neither is exclusive. Worth a Phase 3 spawner-spec ADR.

8. **Recipe Security Scanner as a Phase 7+ skill-manifest screening reference.** Goose's `recipe-scanner/` Docker
   container runs an autonomous goose agent inside a sandbox to score user-submitted recipes 0-100 on security risk
   before execution. Phase 7+ Linus may eventually accept external skill manifests (per DEC-0046 external-API tool
   registry deployment field, DEC-0047 biosecurity tier control); the recipe-scanner pattern is a worked Phase 7+
   reference for "machine-screen-an-external-task-spec-before-execution." Should the Phase 7+ skill-screening design
   spec name goose's recipe-scanner as a design reference? Tentative answer: yes when the spec is drafted, but defer the
   spec itself to Phase 7+ — Linus is single-user, Dan-authored-skills-only at v0; external skill acceptance is
   genuinely Phase 7+ territory. Document the reference now, write the spec when it becomes load-bearing.
