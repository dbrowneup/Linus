# jan (`janhq/jan`)

## 1. Purpose and scope

(Owner-name caveat: the upstream `repos/jan/.git/config` resolves to `https://github.com/janhq/jan` — the org formerly
known as Menlo Research; the fan-out spec's "menloresearch/jan" pointer is now an alias. The canonical owner used
throughout this note is `janhq`.)

Jan is an open-source desktop app — Apache 2.0, the README's tagline is "Open-source ChatGPT replacement" — that
downloads, runs, and chats with local LLMs (Llama, Gemma, Qwen, GPT-oss, etc.) and optionally relays to hosted
providers (OpenAI, Anthropic, Mistral, Groq, MiniMax). It exposes an **OpenAI-compatible HTTP API on `localhost:1337`**
so other tools can use it as a local inference backend, supports **MCP** as the agentic tool surface, and ships an
extension SDK so the model backends (llama.cpp, MLX), retrieval/RAG, and conversational logic are all swappable
plugins. For Linus, Jan occupies the same niche as `openclaw` — a polished local-LLM front-end at the Phase 5
"interface refinement" layer — except that it ships its own inference and is positioned as a complete app, not a
gateway. Per DEC-0008 / DEC-0021, openclaw + claw-code-local already own that lane in Linus's plan; Jan is therefore a
competitor to evaluate, not a target to integrate.

## 2. Architecture summary

A Tauri 2 desktop app (Rust 1.77+ backend, Vite/React TypeScript front-end), Yarn workspaces with two top-level
packages — `core/` (the `@janhq/core` SDK; types and runtime contracts) and `web-app/` (the React UI) — plus
`extensions/` (six bundled JS extensions: assistant, conversational, download, llamacpp, mlx, rag, vector-db) and
`src-tauri/` (the Rust shell) and a Swift `mlx-server/` standalone OpenAI-compatible inference binary built with
`xcodebuild` for the macOS bundle. The Tauri side is organized in `src-tauri/src/core/` into named modules that map
1:1 onto the public surface: `server/` (the local OpenAI-compat HTTP proxy, ~3 K LOC, built on `hyper` 0.14 — the
`proxy.rs` file is large precisely because it transforms Anthropic `/messages` ↔ OpenAI `/chat/completions` and
normalizes tool-schema variants between strict and loose providers), `mcp/` (the MCP client, built on `rmcp` 0.8.5,
with config-driven server lifecycle, lockfile, restart backoff, and a non-trivial tool-call timeout policy in
`constants.rs` / `models.rs`), `extensions/`, `threads/`, `filesystem/`, `downloads/`, `system/`, `updater/`. The Rust
backend re-exports several capabilities as Tauri plugins under `src-tauri/plugins/` (`tauri-plugin-llamacpp`,
`tauri-plugin-mlx`, `tauri-plugin-hardware`, `tauri-plugin-rag`, `tauri-plugin-vector-db`); the JS extensions in
`extensions/llamacpp-extension`, `extensions/mlx-extension`, etc. are the high-level wrappers that call those plugins.
The `mlx` Cargo feature is desktop-only (Apple Silicon); the mobile build (`tauri ios`/`tauri android`) excludes it.
There is also a `jan-cli` binary defined in `src-tauri/Cargo.toml` for headless usage. License is Apache 2.0 in the
README and MIT in `Cargo.toml` (an inconsistency worth noting if Linus ever vendors anything from the repo).

## 3. What's reusable in Linus

Three concrete primitives, all _study_-grade rather than _vendor_-grade. **(1) The `mlx-server/` Swift binary** is a
genuinely interesting reference for native MLX serving on Apple Silicon: it ships an OpenAI-compatible chat-completions
endpoint with SSE streaming and tool calling, builds with stock `xcodebuild`, and runs as `./mlx-server --model
<path> --port 8080 --ctx-size 4096`. Linus's Phase 1 already plans to evaluate `pmetal serve` and `mlx-lm` as local
inference targets (DEC-0006, DEC-0012); `mlx-server` is a third public-API native option worth benchmarking against
those and adds nothing to maintain because it is upstream-maintained. Phase 1c spike candidate. **(2) The
Anthropic↔OpenAI transformation in `src-tauri/src/core/server/proxy.rs`** is a directly applicable pattern for Linus's
DEC-0005 OpenAI-compatibility layer: when (not if) Linus has to accept Anthropic-shaped traffic from clients like
Claude Code while routing to an OpenAI-shaped Worker, this proxy is the exact transformation table — body shape, tool
schema normalization, content-array vs string content, image/media block conversion. ~3 K LOC of Rust that maps onto
~500 LOC of Python equivalent in Linus's orchestration layer. Read as design reference, do not vendor (license
mismatch / monorepo coupling). Phase 2a router work. **(3) The MCP client wiring in `src-tauri/src/core/mcp/`** uses
`rmcp` 0.8.5 with a config schema (`McpServerConfig` — transport, url, command, args, envs, timeout, headers), restart
backoff with multiplier, and tool-call timeouts as constants. This matches the shape Linus needs per DEC-0018 (MCP as
extensibility substrate) and DEC-0045 (fastmcp default), and validates that production-quality Rust MCP _client_ code
is small (~7 source files). Reference, not vendor. Phase 2a/3 MCP wiring.

## 4. What's inspiration only

Jan's **plugin/extension model** — a `core/` SDK plus per-capability JS extensions (`llamacpp-extension`,
`mlx-extension`, `rag-extension`, `vector-db-extension`, `assistant-extension`, `conversational-extension`,
`download-extension`) — is a reasonable target architecture for Linus's eventual capability surface. The **Tauri shell
+ Rust backend + web-app front-end** decomposition is also exactly what a future native Linus app would look like
(Phase 8 territory per DEC-0008's hand-off path); Jan is a working reference implementation of that shape on Apple
Silicon, including the Cargo feature flags for desktop-vs-mobile splits and the `tauri.macos.conf.json` /
`Entitlements.plist` apparatus. None of this is reusable code — it is reusable _design_, and it competes with the
openclaw-flavored Phase 5 plan rather than complementing it. The Anthropic-to-OpenAI proxy logic is the cleanest part
of the codebase to read for cross-protocol design ideas even if no code is lifted.

## 5. What's incompatible or out of scope

Jan is **a complete app**, not an orchestration backend. It owns the UI, the inference servers, the model store, the
extension surface, the MCP client, the threads database, and the OpenAI-compatible proxy. Linus per DEC-0002 is
explicitly the orchestration layer beneath any front-end; integrating Jan would mean either (a) accepting Jan as the
front-end and surrendering the Linus-controlled extension surface, or (b) running Jan and Linus side-by-side with two
local OpenAI-compat servers competing for the same clients — both worse than the openclaw plan. Jan's **inference
stack is fixed** (llama.cpp + MLX via the bundled extensions); Linus's pmetal/Ollama/mlx-lm experimentation lane
(DEC-0006, DEC-0012, DEC-0049) cannot ride inside Jan without forking the llamacpp/mlx extensions, which is not worth
doing for an ecosystem Linus does not own. **License inconsistency** between README (Apache 2.0) and `Cargo.toml`
(MIT) means Linus should not vendor any code without first asking upstream which license actually governs. The
**Tauri/Yarn/Vite/Rust toolchain** is heavy (Node ≥ 20, Yarn ≥ 4.5.3, Tauri 2.7, Rust 1.77, MetalToolchain) — fine for
Jan as a product but a non-trivial dependency to track for a project that might only want to read three files.
**Auto-update + OAuth + remote-provider commands** baked into the Tauri shell expand the trust surface in directions
Linus's local-first stance does not need (DEC-0024 supply-chain posture).

## 6. Recommendation: **Watch**

Jan is the closest analogue to "what Linus might look like if it tried to be a complete user-facing app instead of an
orchestration backend with a separate UI." That is precisely the design Linus has explicitly rejected (DEC-0002,
DEC-0008). Watch the project for three specific reasons: (1) it is on Apple Silicon and ships native MLX serving, so
it is a useful baseline for Phase 1 inference benchmarks (Jan's `mlx-server` vs `pmetal` vs `mlx-lm` on the same model
+ same prompts); (2) its Anthropic↔OpenAI proxy and `rmcp`-based MCP client are the highest-quality public reference
implementations for two specific Linus tasks (DEC-0005 router shape, DEC-0018 MCP wiring); (3) if openclaw's
Phase 5 integration falls through (e.g., openclaw goes dormant or its license drifts), Jan is the obvious fallback
front-end candidate, even though that would require re-litigating DEC-0008. No code to vendor, no integration to
plan; revisit at the next quarterly curation review (2026-08-01).

## 7. Questions for Dan

1. **DEC-0005 router prior art.** Jan's `proxy.rs` is the most complete public reference for the Anthropic↔OpenAI
   transformation Linus will need at the orchestration layer. Worth allocating a Phase 2a sub-task to read the file
   end-to-end and write a port spec for the Python equivalent — explicitly as a reading exercise, not a vendoring
   exercise — so the next-best-tool work doesn't reinvent it from scratch?

2. **`mlx-server` as a fourth Phase 1 inference candidate.** Currently Phase 1 lists pmetal (DEC-0012), Ollama,
   `mlx-lm`, and the deferred PrismML fork (DEC-0049). Jan's `mlx-server` is a fourth public-API option, runs on
   `localhost:8080` natively, and is upstream-maintained. Add to the Phase 1c spike scope, or consider it duplicative
   with `mlx-lm` and skip?

3. **MCP client implementation choice.** DEC-0045 makes `fastmcp` the default MCP framework, but `fastmcp` is
   server-side. For the client side (Linus calling out to MCP servers from its router/agent layer), `rmcp` 0.8.5 (the
   crate Jan uses) is one option; the Python `mcp` SDK is another; rolling our own is a third. Has the
   client-framework choice been made anywhere I should be reading, or is that an open Phase 2a/3 question?

4. **Phase 5 fallback.** DEC-0008 names openclaw as the Phase 5 front-end and DEC-0009 keeps LM Studio
   discovery-only. If Jan should also be on the radar as a Watch-tier fallback (in case openclaw goes sideways), is
   that worth recording explicitly — either as a paragraph in the openclaw repo-note's Connections, or as a small
   `_Seed: DEC-NNNN_` annotation here that gets promoted only if a fallback is ever needed?

5. **Licence inconsistency for vendoring.** README says Apache 2.0; `src-tauri/Cargo.toml` says MIT. Both are
   permissive and compatible with Linus's stance, but the inconsistency means any code lift would need an upstream
   issue to confirm which licence actually governs. Worth raising upstream as a one-line GitHub issue, or just note
   it in the curation log and move on?

6. **Plugin/extension architecture as a Phase 8 reference.** Jan's `core/` SDK + `extensions/` JS plugins +
   `src-tauri/plugins/` Rust plugins is the cleanest public example of a Tauri-shell-plus-pluggable-extensions
   architecture I have seen for an Apple-Silicon-first local-LLM app. If Phase 8 includes a native Linus app, is that
   the architecture pattern to anchor on, or is the openclaw Gateway+companion-nodes pattern (DEC-0008) the firmer
   reference?

7. **MLX desktop-vs-mobile feature flag.** Jan's `Cargo.toml` excludes the `mlx` feature on the mobile build, with
   the `desktop` feature aggregating `mlx + hardware + deep-link`. If Linus ever does a mobile companion (Phase 8),
   is that the right shape — feature-gate Apple-Silicon-only inference behind a `desktop` Cargo feature so the
   mobile build compiles cleanly without it — or are there better patterns to copy from elsewhere?

Cross-references for the cluster index and synthesis fold-in: cluster home is
[g7-harnesses](../syntheses/repo-clusters/g7-harnesses.md) (Jan slots in as a "complete-app" example versus the
harness-vs-orchestration distinction G7 draws); the Phase 5 lane is owned by [openclaw](openclaw.md) per
[DEC-0008](../adr/0008-openclaw-frontend-native-app.md), with [claw-code-local](claw-code-local.md) as the Phase 5c
Rust harness ([DEC-0021](../adr/0021-phase5c-claw-code-local.md)); the design points where Jan is most useful as
reference are [DEC-0005](../adr/0005-openai-compatible-protocol.md) (the Anthropic↔OpenAI transformation in
`proxy.rs`), [DEC-0018](../adr/0018-mcp-extensibility-substrate.md) (the `rmcp`-based MCP client wiring), and
[DEC-0045](../adr/0045-fastmcp-mcp-framework-default.md) (where Jan's `rmcp` is a client-side candidate distinct
from `fastmcp`'s server-side scope).
