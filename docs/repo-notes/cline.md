# cline (`cline/cline`)

## 1. Purpose and scope

Cline is the **VS Code agentic coding extension** — a fully featured in-editor agent harness that analyzes file
structure and ASTs, runs regex searches, reads relevant files, edits files with diff views, executes terminal commands
(with permission), monitors linter/compiler errors, and can drive a headless browser for web-development tasks. It
supports OpenRouter, Anthropic, OpenAI, Google Gemini, AWS Bedrock, Azure, GCP Vertex, Cerebras, Groq, and **any
OpenAI-compatible API including Ollama and LM Studio** out of the box. MCP (Model Context Protocol) is first-class:
Cline can create new tools on the fly by spinning up MCP servers. Apache-2.0 licensed and backed by Cline Bot Inc. For
Linus this is the incumbent "VS Code path" — the harness Dan already has installed and can point at Linus's endpoint in
Phase 2 with zero additional configuration.

## 2. Architecture summary

VS Code extension written in TypeScript. The extension and webview communicate via a gRPC-like protocol (proto files in
`proto/`), with dedicated crates for shared types, generated handlers, and clients. Model-specific prompt variants live
in `src/core/prompts/system-prompt/ variants/` — one per model family (generic, next-gen, xs, gpt-5, native-gpt-5,
gemini-3, hermes, glm, and others), with shared components under `components/` and per-variant overrides. Tools are
defined in `src/core/prompts/system-prompt/tools/` with variants per model family; a generic fallback is used when no
model-specific variant exists. Responses API providers (OpenAI Codex, native OpenAI) require native tool calling enabled
via `apiFormat: ApiFormat.OPENAI_RESPONSES`. Non-XML tool-calling protocols, browser use (via Anthropic's Computer Use),
checkpoint/restore, `@url` / `@problems` / `@file` / `@folder` context injection. Also ships a CLI under `cli/` using
React Ink for terminal UI. Extension state is managed via a `StateManager` cache with specific gotchas around
cross-window sync and webview settings round-trips.

## 3. What's reusable in Linus

Cline's direct reusability for Linus is as a **client**, not as code Linus embeds. Once Linus's `/v1/chat/completions`
endpoint is up in Phase 2a, Cline can point at it as an OpenAI-compatible provider with no code changes on the Linus
side — this is the plan already in ROADMAP Phase 5b. The _prompt variants_ architecture (`generic` / `xs` / `hermes` /
`glm` variants tuned for small or local models) is useful prior art: it shows that tool-use prompt templates need to be
per-model-family to work reliably on anything smaller than frontier, and that "small models" need specific treatment,
not a watered-down GPT-5 prompt. Linus's Phase 7 skills and tool definitions should probably factor similarly — variant
templates per worker model class (Qwen, Mistral, 1-bit/ternary Bonsai, future Linus fine-tunes).

## 4. What's inspiration only

The MCP-first tool story ("add a tool that fetches Jira tickets" → Cline spins up an MCP server) is the most aggressive
bet on MCP as the extensibility protocol of a harness. Linus can consume MCP servers directly (there's work on this
inside openclaw too), which would let Linus tools be visible to Cline automatically. The tradeoff between MCP-everywhere
and "native Linus tool registry" is worth thinking through before Phase 3.

## 5. What's incompatible or out of scope

Cline is VS-Code-bound (plus a CLI companion). For terminal-only workflows, claw-code-local is lighter and simpler.
Cline is also a large, actively-developed product with complex internal machinery — the CLAUDE.md files describe gotchas
around gRPC/proto regen, state keys, and tool registration that only matter if you're contributing to Cline itself;
Linus is not. MoCP (multi-window, cross-session state sync through the StateManager cache) is an engineering detail
Linus inherits only if it contributes to Cline. The dependency on VS Code means Phase 8 native-Linus app has to stand up
its own tool UX; Cline does not give you that for free.

## 6. Recommendation: **Integrate (as Phase 2+ client)**

Keep Cline installed. Phase 2a: once Linus's endpoint is up, add "Linus (local)" as a provider pointing at
`http://localhost:<port>/v1`, configure a worker model, and run the Phase 1e Maestro/Worker loop through Cline as one of
the front-ends. Phase 5b polishes the VS Code path. Do not vendor Cline code; do not extend Cline; treat it as a
third-party harness Linus speaks OpenAI-compat to. Revisit whether Cline, openclaw, Claude Code, or claw-code-local
becomes the dominant harness only after 1–2 phases of real use.

## 7. Questions for Dan

1. **Variant prompts for small / 1-bit models.** Cline's `xs` variant exists because tiny models need substantially
   different prompts. When Linus's Phase 6 produces a fine-tuned 1-bit model, it will likely need its own variant too.
   Plan for this in Phase 7 skills design, or defer?
2. **Browser use.** Cline's browser tool relies on Anthropic's Computer Use — a frontier-model capability. Local models
   plausibly can't drive it reliably. Is browser-based agentic work a Linus use case, or does it stay Maestro-only?
