# rig (`0xplaygrounds/rig`)

## 1. Purpose and scope

rig is the canonical Rust-side **unified-LLM-client library** — a Cargo workspace from Playgrounds Analytics Inc.,
MIT-licensed, ~7.2k★, currently at version 0.36.0, that abstracts 25 model providers and 15+ vector stores behind one
typed trait surface. Where Python's LiteLLM occupies the "one API for many providers" niche on the Python side, rig
occupies the corresponding niche in Rust: a `ProviderClient` + `CompletionClient` + `EmbeddingsClient` trait stack,
provider-specific `Client` structs that implement those traits, an `AgentBuilder` typestate pattern that composes
preamble + context + tools + temperature + memory + tool-server-handle into a usable `Agent`, and a workspace of
optional companion crates (`rig-mongodb`, `rig-qdrant`, `rig-neo4j`, `rig-sqlite`, `rig-lancedb`, `rig-bedrock`,
`rig-fastembed`, `rig-memory`, …) gated behind feature flags on the root `rig` facade. The library is **production-ready
for Rust applications that wrap LLM calls** — vendored by St Jude (genomics chatbot in `proteinpaint`), VT Code (a Rust
terminal coding agent), Coral Protocol's Rust SDK, Neon's `app.build` rebuild, Listen (portfolio-management agents),
Nethermind, and others per the README ECOSYSTEM list — but it is **not** a multi-agent orchestration framework, **not**
a memory pillar, and **not** a coding harness. It is the layer of abstraction that sits underneath those things on the
Rust side: "talk to any LLM provider with one API."

For Linus this is exclusively a **Phase 5+ reference target**, relevant once Rust components proliferate (pmetal,
claw-code-local, any Linus-native Rust services). Linus's core orchestration layer is Python (DEC-0027 multi-language
stance: choose the language that fits the component); rig has no place in the Phase 2a Python orchestration backend.
What rig contributes is the trait-shape vocabulary for any future Linus-side Rust adapter that needs to talk to multiple
providers, plus a confirming signal about which providers and which capability tiers (completion / embedding /
transcription / image / audio / structured output) belong in a unified-client trait stack.

## 2. Architecture summary

rig is a Cargo 2024-edition workspace with a `rig` root facade that re-exports `rig-core` plus 18 optional companion
crates behind feature flags. The lib at `crates/rig-core/` (~74,800 LoC of Rust under `src/`) is the substantive
product; the root crate is just feature-gated re-exports. The workspace excludes an `archived/` directory, uses LTO +
`opt-level = "s"` for release profile, and enforces a strict clippy lint set in `Cargo.toml` (`unwrap_used`,
`expect_used`, `indexing_slicing`, `panic`, `panic_in_result_fn`, `todo`, `unimplemented`, `unreachable`, `dbg_macro`,
`await_holding_*` all `deny` or `forbid`). The lint discipline is itself a worthwhile Rust-conventions reference for any
Linus Rust component.

The **provider trait stack** under `crates/rig-core/src/client/` factors capabilities cleanly. `ProviderClient`
(`mod.rs`) is the base contract: every provider client implements `from_env()` and `from_val(input)` constructors with a
typed `Error`. Above that, capability traits compose in: `CompletionClient` (a provider can do chat completion),
`EmbeddingsClient` (the provider can embed), `TranscriptionClient`, `ImageGenerationClient`, `AudioGenerationClient`,
`ModelListingClient`, and `VerifyClient`. Each capability trait carries an associated model type — e.g.
`CompletionClient::CompletionModel: CompletionModel<Client = Self>` — and a
`completion_model(&self, model: impl Into<String>) -> Self::CompletionModel` factory plus an
`agent(&self, model) -> AgentBuilder<Self::CompletionModel>` convenience that hands you a typestate-pattern builder. A
provider that doesn't support embedding simply doesn't implement `EmbeddingsClient`; the type system enforces capability
presence at compile time. The generic `Client<Ext, H>` struct under the same module wraps the HTTP backend
(`reqwest::Client` by default, but generic `H` allows swap-in of alternative `HttpClientExt` implementations) and a
provider-specific `Ext` extension for URL construction, auth headers, and request customization — a single shared client
shape across all providers.

The **provider catalogue** under `crates/rig-core/src/providers/` is 25 modules: `anthropic` · `azure` · `chatgpt` ·
`cohere` · `copilot` · `deepseek` · `galadriel` · `gemini` · `groq` · `huggingface` · `hyperbolic` · `llamafile` ·
`minimax` · `mira` · `mistral` · `moonshot` · **`ollama`** · `openai` · `openrouter` · `perplexity` · `together` ·
`voyageai` · `xai` · `xiaomimimo` · `zai`. Plus `bedrock`, `fastembed`, `gemini-grpc`, and `vertexai` as separate
companion crates. The Ollama provider (`crates/rig-core/src/providers/ollama.rs`, ~1,777 LoC) is **first-class native**:
`OLLAMA_API_BASE_URL = "http://localhost:11434"` is the default, the `OllamaApiKey(Option<String>)` shape supports both
unauthenticated (the canonical Ollama deployment) and Bearer-authenticated (proxied/secured Ollama) modes, the
`OllamaExt` provider type implements `Capabilities` for `CompletionClient` + `EmbeddingsClient` + `ModelListingClient` +
`VerifyClient`, and the rustdoc example walks through `client.agent("qwen2.5:14b")` and
`client.embedding_model("all-minilm", 384)` end-to-end. The `examples/rag_ollama.rs` and
`examples/vector_search_ollama.rs` binaries are runnable demonstrations. The Ollama provider is treated as a peer to
OpenAI / Anthropic / Cohere — not a second-class citizen.

The **agent layer** under `crates/rig-core/src/agent/` (~653 LoC of `builder.rs` plus `mod.rs`, `completion.rs`,
`prompt_request/`, `tool.rs`) provides the typestate `AgentBuilder<M, P, ToolState>` pattern. The builder threads three
type parameters: the completion model `M`, the prompt-hook type `P`, and a tool-config typestate (`NoToolConfig` →
either `WithBuilderTools` or `WithToolServerHandle`, mutually exclusive at compile time). Configurable knobs include
`name`, `description`, `preamble` (the system prompt), `static_context` (always-included documents),
`additional_params`, `max_tokens`, `dynamic_context` (RAG sources via `VectorStoreIndexDyn`), `temperature`,
`tool_choice`, `default_max_turns`, `output_schema` (a `schemars::Schema` for structured output), `memory` (a
`ConversationMemory` backend), and `default_conversation_id`. The compiled `Agent` then implements the `Prompt`, `Chat`,
`TypedPrompt`, and `Completion` traits from `crates/rig-core/src/completion/`. The `CompletionRequest` type is rig's
canonical request shape; provider modules translate it into their native HTTP body and convert the response back to
`CompletionResponse`.

The **MCP integration** lives at `crates/rig-core/src/tool/rmcp.rs` (~534 LoC) behind the `rmcp` feature flag — using
the `rmcp` crate (Rust MCP SDK, the Rust analogue to Python's `fastmcp`). `McpTool` wraps an `rmcp::model::Tool` and
implements rig's `ToolDyn` trait, bridging MCP tool definitions into rig's `ToolSet`. `McpClientHandler` is the auto-
updating variant: it subscribes to `notifications/tools/list_changed` and re-fetches the tool list, mutating a shared
`ToolServerHandle` so an `Agent` already running against the handle picks up new tools without rebuilding.
`examples/rmcp.rs` is a runnable end-to-end demonstration with a hand-rolled `ToolRouter`-based MCP server (a Counter
tool exposing `sum`) talking to a rig OpenAI agent over `streamable-http`. MCP is **not** a built-in default — you opt
in via `cargo add rig --features rmcp` — but the path is fully wired and live-tested in the example.

The **memory layer** under `crates/rig-core/src/memory.rs` is intentionally minimal: a `ConversationMemory` async trait
plus an `InMemoryConversationMemory` reference implementation and a `with_filter` closure hook for callers to layer in
truncation policy. History-shaping (sliding window, token budget) lives in the `rig-memory` companion crate
(`crates/rig-memory/`, version 0.1.0, much smaller — single `lib.rs`). This is a deliberately thin contract: rig does
not commit to a memory architecture, only to a "conversation history can be loaded and saved per id" interface. Compare
with Letta's full memory pillar (named blocks, archival memory, git-versioned memory_repo, three-tier model) — rig
deliberately stays out of that scope, leaving it to the application or to specialized companion crates.

The **vector-store layer** under `crates/rig-core/src/vector_store/` defines the `VectorStoreIndex` and
`VectorStoreIndexDyn` traits plus `InMemoryVectorStore` and `LSH` reference implementations. The 15+ companion crates
(`rig-mongodb`, `rig-qdrant`, `rig-neo4j`, `rig-sqlite`, `rig-lancedb`, `rig-helixdb`, `rig-milvus`, `rig-postgres`,
`rig-s3vectors`, `rig-scylladb`, `rig-surrealdb`, `rig-vectorize`) each implement `VectorStoreIndex` against their
backing store. The `rig-fastembed` companion crate is a notable outlier: it provides ONNX-runtime local embedding (via
the `fastembed` Rust crate) — relevant for any Linus Phase 7+ component that wants Rust-side local embedding without
reaching for an external service.

Other notable surfaces: `crates/rig-core/src/pipeline/` (an Airflow/Dagster-inspired DAG pipeline API for composing LLM
ops with non-LLM ops via an `Op` trait and a `parallel!` macro — distinct from the `Agent` abstraction);
`crates/rig-core/src/extractor/` (typed structured extraction via `schemars::JsonSchema` constraints, the rig analogue
to pydantic-ai's `extractor` pattern); `crates/rig-core/src/streaming/` (streaming completion responses);
`crates/rig-core/src/telemetry/` (OpenTelemetry GenAI Semantic Convention compatibility, claimed in the README under
"Full GenAI Semantic Convention compatibility"); `crates/rig-core/src/tools/think.rs` (a built-in `think` tool — a
classic agentic-loop pattern); `crates/rig-core/src/integrations/cli_chatbot.rs` and `discord_bot.rs` (two integrations
shipped in-tree); plus `loaders/` for document ingestion (PDF behind `pdf` feature via `lopdf`, EPUB behind `epub`).
WASM compatibility is a stated feature of the core library.

The `examples/` directory at the workspace root (~50 binary examples — `agent.rs`, `agent_orchestrator.rs`,
`agent_parallelization.rs`, `agent_routing.rs`, `multi_agent.rs`, `multi_turn_agent.rs`, `agent_with_memory.rs`,
`agent_with_tools.rs`, `rag.rs`, `rag_ollama.rs`, `rag_dynamic_tools.rs`, `complex_agentic_loop_claude.rs`,
`reasoning_loop.rs`, `gemini_deep_research.rs`, `pdf_agent.rs`, `rmcp.rs`, `discord_bot.rs`, `vector_search.rs`,
`vector_search_ollama.rs`, `vector_search_cohere.rs`, …) is the canonical entry point for understanding the library by
reading code rather than docs. Provider-backed live integration tests live under `tests/providers/` and are run via
`cargo test -p rig --test openai -- --ignored --test-threads=1` to avoid rate limiting.

## 3. What's reusable in Linus

rig's contribution to Linus is structural rather than substantive — Linus does not vendor rig, but its trait shapes and
design choices are useful design references for Phase 5+ Rust components.

**Phase 5+ — `ProviderClient` + capability-trait stack as the design template for any Linus-side Rust adapter (DEC-0027
multi-language stance).** Linus's eventual Rust components (pmetal-as-library callers, claw-code-local front-end work,
any Linus-native Rust service that needs to talk to LLM providers) need a way to talk to local models (Ollama,
MLX-Flash, pmetal serve) without hard-coding provider specifics. rig's trait stack is the cleanest existing Rust example
of how to factor this: `ProviderClient` for construction, `CompletionClient` / `EmbeddingsClient` /
`TranscriptionClient` etc. as opt-in capability traits, an associated `CompletionModel` type per provider, and a generic
`Client<Ext, H>` shared shape. A Linus Rust adapter that needs to reach Linus's own OpenAI-compatible orchestration
backend — call it `linus_client::Client` — should mirror this shape: implement the same capability trait set so that
downstream consumers can swap between rig's existing providers and a Linus-shaped provider without learning a new
vocabulary. The trait shape is worth lifting; the provider catalogue itself is not content Linus needs to vendor.

**Phase 5+ — Ollama provider as a confirming signal that Phase 5c claw-code-local can use rig as its provider
abstraction.** rig's first-class Ollama support — `OLLAMA_API_BASE_URL = "http://localhost:11434"` as default, the
`OllamaApiKey` shape that handles both unauthenticated (canonical Ollama) and Bearer-authenticated (proxied Ollama)
modes, runnable `examples/rag_ollama.rs` and `examples/vector_search_ollama.rs` — confirms that an Ollama-backed Rust
agent is a worked solved problem. Phase 5c work on `claw-code-local` ([`claw-code-local.md`](claw-code-local.md))
already adopts this exact pattern (env-var-driven provider routing pointing at Ollama on 11434); rig is the upstream
reference for what the "real" version of that abstraction looks like in Rust. If a Phase 5+ Linus Rust component needs
to talk to Linus's OpenAI-compatible orchestration backend (which itself proxies to Ollama / MLX-Flash / pmetal),
implementing a `linus` rig-provider — even out-of-tree — is straightforward: define a `LinusExt` provider, set
`base_url` to the Linus orchestration endpoint, reuse the `OpenAI` provider's request/response shapes (since DEC-0005
commits Linus to OpenAI-compatible HTTP), and the `Capabilities` impl block falls out cleanly.

**Phase 5+ — typestate `AgentBuilder` pattern as a Rust-side analogue to pydantic-ai's `Agent` class.** When Phase 5+
Linus needs a Rust-side agent abstraction, rig's typestate pattern (`NoToolConfig` → `WithBuilderTools` |
`WithToolServerHandle`, mutually exclusive at compile time) is the design reference for how to do it idiomatically. The
pattern enforces "tools come from the builder OR from a pre-existing handle, but not both" at compile time — the exact
kind of invariant that's awkward to express in Python and natural in Rust. The set of fields rig threads (`preamble`,
`static_context`, `dynamic_context`, `temperature`, `tool_choice`, `default_max_turns`, `output_schema`, `memory`,
`default_conversation_id`) is also a useful reference for what a Linus Phase 5+ Rust agent abstraction should expose.
The `output_schema: Option<schemars::Schema>` field for structured output is the Rust counterpart to the typed
structured prediction convention CLAUDE.md commits to (the BioReason-Pro shape: typed result wrapping free-text
rationale). rig already does this idiomatically; Linus Rust components should match.

**Phase 5+ — `rmcp` integration as a confirming signal that the MCP substrate (DEC-0018, DEC-0045) extends to Rust
agents.** DEC-0045 commits Linus's Python orchestration layer to fastmcp; DEC-0018 establishes MCP as the
tool-extensibility substrate. rig's `rmcp`-feature integration is the Rust counterpart — same protocol, different SDK
(the `rmcp` crate is the Rust MCP SDK) — and confirms that any Rust component Linus eventually ships will naturally
compose with the Linus MCP tool registry. The `McpClientHandler` auto-update pattern (subscribe to
`notifications/tools/list_changed`, mutate a shared `ToolServerHandle`) is also a worked reference for how a long-
running Linus MCP host should keep tool sets fresh without rebuilding the agent. The `examples/rmcp.rs` end-to-end demo
is the cleanest "rig agent calling MCP server over `streamable-http`" worked example available — directly applicable
when Phase 5+ Linus Rust adapters need to consume Linus MCP-served tools.

**Phase 5+ — strict workspace clippy lint set as a Linus Rust-conventions reference.** rig's `Cargo.toml` lint block
(`unwrap_used`, `expect_used`, `indexing_slicing`, `panic`, `panic_in_result_fn`, `todo`, `unimplemented`,
`unreachable`, `dbg_macro`, `await_holding_lock`, `await_holding_refcell_ref` all `deny` or `forbid`) is a worthwhile
template for any Linus-internal Rust crate. The `Cargo.toml` enforcement is non-trivial — it makes "no panics in
production code" a build-time guarantee, not a code-review hope — and matches Linus's general posture (audit-logged
behavior, no silent failures).

**Phase 5+ — pipeline `Op` trait + `parallel!` macro as a reference for non-LLM-step composition.** rig's `pipeline`
module (Airflow/Dagster-inspired DAG composition where each node is an `Op` and the `parallel!` macro fans out
concurrently) is a useful Rust-side reference for how to compose LLM and non-LLM steps in a typed pipeline. This is
conceptually adjacent to the workgraph JSONL DAG pattern CLAUDE.md recommends as the Phase 2a session-store shape (G7
synthesis); the workgraph crate is the canonical reference for the orchestration layer, but `rig::pipeline` is the
canonical reference for the Rust-side "compose a multi-step LLM workflow" idiom. Different scopes (workgraph = durable
orchestration runtime with append-only DAG; rig::pipeline = in-process typed pipeline composition) but overlapping
vocabulary worth knowing.

## 4. What's inspiration only

The **15+ vector-store companion crates** (`rig-mongodb`, `rig-qdrant`, `rig-neo4j`, `rig-sqlite`, `rig-lancedb`,
`rig-helixdb`, `rig-milvus`, `rig-postgres`, `rig-s3vectors`, `rig-scylladb`, `rig-surrealdb`, `rig-vectorize`) are
inspiration-only for Linus. The KnowledgeBase substrate (Python-side, with paper-qa as the retrieval engine per
DEC-0044) handles Linus's RAG needs; rig's vector-store crates are useful as references for "what a clean
`VectorStoreIndex` trait abstraction looks like in Rust" but the substance — Mongo, Neo4j, Qdrant integrations — is not
content Linus consumes. The cleanest reference is `rig-sqlite` since DEC-0029 commits Linus to SQLite as the Layer C
substrate; if a Phase 7+ Linus Rust component ever needs SQLite-backed vector search from Rust, `rig-sqlite` is the
existing shape to study.

The **provider catalogue's hosted-API focus** (Anthropic, OpenAI, Cohere, Mistral, Gemini, …) is inspiration only for
Linus's local-first stance. The 25-provider list is a useful confirming signal that "unified provider abstraction" is a
real engineering need that has been solved 25 times in Rust, but Linus's Phase 1–5 working set is much narrower (local
Ollama, eventual MLX-Flash and pmetal serve). The breadth of rig's catalogue is an existence proof, not a shopping list.

The **`rig-onchain-kit` companion crate** (Solana / EVM integrations for crypto agents) is fully out of scope for Linus.
It's a useful data point about the kinds of vertical applications rig's user base builds (crypto/DeFi agents appear
frequently in the README ECOSYSTEM list — Coral Protocol, Listen, ilert, Dria) but contributes nothing to Linus's
roadmap.

The **WASM compatibility** of `rig-core` is a useful design discipline reference (the `wasm_compat::WasmCompatSend` /
`WasmCompatSync` markers, the `WasmBoxedFuture` type alias, the `cfg(target_family = "wasm")` gates on memory-error
boxing) but Linus does not target WASM in Phases 1–8. If Phase 8+ ever runs Linus components in a browser context, the
patterns are worth revisiting.

The **TypeScript-ergonomic README posture** ("Here be dragons! As we plan to ship a torrent of features in the following
months, future updates **will** contain **breaking changes**") is the speed-and-evidence-instinct posture CLAUDE.md
endorses — useful as a discipline reference for how to communicate breaking-change tolerance in a young library, not
content to lift. rig is at version 0.36.0 and SemVer-pre-1.0; the explicit breaking-change warning is the right shape
for that maturity level.

## 5. What's incompatible or out of scope

**rig is not a Python library. Linus's core orchestration layer is Python (DEC-0027 multi-language stance: Python is the
core orchestration language; Rust is acceptable for components that fit).** Phase 2a's pydantic-ai-based orchestration
backend cannot consume rig directly — there is no Python binding, and there should not be one. rig is an option only
when the consumer is itself Rust: pmetal-as-library, claw-code-local, or any future Linus-native Rust service. This is a
hard scope incompatibility with the Phase 2a orchestration backend, not a soft one. The Python analogue Linus uses is
pydantic-ai ([`pydantic-ai.md`](pydantic-ai.md)); rig's value is exclusively Rust-side.

**rig is a unified-LLM-client library, not a multi-agent framework.** Letta ([`Letta.md`](Letta.md)) is the multi-agent
reference; rig is the single-agent, multi-provider reference. The `multi_agent.rs` example in rig's `examples/`
directory is genuinely just "two rig Agents passing messages to each other in the same tokio runtime" — not the
productized multi-agent server with manager taxonomies (round-robin, supervisor, dynamic, sleeptime) that Letta ships.
Linus Phase 3's spawner spec ([`phase3-spawner.md`](../specs/phase3-spawner.md), DEC-0050, DEC-0052) draws on Letta's
manager taxonomy, not rig's example pattern — rig has nothing comparable to contribute on the multi-agent side.

**rig has no MLX-Flash / pmetal / native-Apple-Silicon-ML provider.** The 25 mainline providers are all HTTP-based,
talking to either a hosted API or a local HTTP-shaped server (Ollama, llamafile, OpenAI-compatible endpoints in
general). There is no provider that talks to MLX directly via FFI, no provider that loads a GGUF and runs it via
llama.cpp Rust bindings, no provider that calls into pmetal serve via its internal API. The path forward is
straightforward — implement a Linus-shaped provider (or an Ollama-routed indirection through Linus's OpenAI-compatible
orchestration backend) — but rig as-shipped does not solve this problem. Linus's Phase 1b inference-backend bake-off
(pmetal vs. mlx-lm vs. Ollama, [`pmetal.md`](pmetal.md)) is upstream of any rig adoption.

**rig deliberately does not commit to a memory architecture.** The `ConversationMemory` trait is intentionally minimal
(load and save history per conversation id; that's it); history-shaping policies live in the separate `rig-memory`
companion crate. Compare with Letta's full memory pillar (named blocks with per-block limits and read-only flags,
three-tier core/recall/archival model, git-versioned memory_repo). For Linus's Phase 2 memory pillar (DEC-0028, the
five-layer architecture), rig contributes nothing on the substantive side; it is correctly scoped as a unified-client
library and stays out of memory architecture. Linus's reference for the memory pillar is Letta plus the agentmemory
family, not rig.

**No Linus-side biology / KnowledgeBase / generative-biology integration in rig.** rig's vertical integrations are DeFi
(rig-onchain-kit), evaluation pipelines (`pdf_agent.rs`, `rag.rs`), and general-purpose chat — not bioinformatics or
scientific reasoning. Phase 7+ biology Workers ([`biology-phase7-roadmap.md`](../specs/biology-phase7-roadmap.md)) draw
on the Phase 7 roadmap and the BixBench / aviary / Bonsai-demo / BioReason references; rig is orthogonal to that work.
The only weak signal is the README's mention of St Jude using rig for `proteinpaint` (a genomics visualisation tool) —
confirming that rig is at least capable of being wrapped around a bioinformatics-adjacent application — but the
integration is downstream of rig, not in it.

**rig is at version 0.36.0 and warns about breaking changes between minor releases.** The README's "Here be dragons!"
banner means any Linus-side consumer needs to pin a specific version and budget churn for upgrades. Acceptable for a
Phase 5+ adoption where the integration surface is small (a few trait impls); concerning if the integration surface
grew. The recommendation here is to pin a known-good rig version when Phase 5+ work begins, not to track main.

## 6. Recommendation: **Study**

Read rig's trait stack — specifically `crates/rig-core/src/client/mod.rs` (the `ProviderClient` + `Client<Ext, H>` +
`Capabilities` + capability-traits scaffold), `crates/rig-core/src/client/completion.rs` (the `CompletionClient` trait
shape), `crates/rig-core/src/agent/builder.rs` (the typestate `AgentBuilder<M, P, ToolState>` pattern),
`crates/rig-core/src/providers/ollama.rs` (the canonical Ollama provider implementation), and
`crates/rig-core/src/tool/rmcp.rs` (the MCP-via-`rmcp` integration) — as the Rust-side reference for unified-LLM-client
abstraction. Read enough of the examples (`examples/agent.rs`, `examples/rag_ollama.rs`, `examples/rmcp.rs`,
`examples/multi_agent.rs`) to understand how the trait stack is actually used end-to-end. Treat rig as the "this is what
an idiomatic Rust LLM-client library looks like in 2026" reference; do not vendor it into Linus's Python orchestration
layer.

The right time to revisit rig is **Phase 5+**, when Rust components Linus consumes (pmetal serve, claw-code-local) or
ships (any Linus-native Rust adapter) start to need a unified-provider abstraction. At that point the question is not
"should Linus depend on rig?" but "should the Linus Rust adapter implement rig's `ProviderClient` capability-trait stack
so it composes with the existing rig ecosystem?" — a question worth a Phase 5+ ADR alongside the orchestration- backend
Phase 2a work. The current default position is "yes, mirror the trait shape so Linus-served local-first endpoints look
like a normal rig provider to Rust consumers." Cluster cell:
[g11-agent-frameworks](../syntheses/repo-clusters/g11-agent-frameworks.md) (rig sits next to pydantic-ai as the
Rust-side multi-provider abstraction; pydantic-ai is the Python-side Integrate verdict for Phase 2a, rig is the
Rust-side Study verdict for Phase 5+).

Do **not** vendor rig. Do **not** wrap it from Python via PyO3. Do **not** add it to the Phase 2a orchestration backend.
The cleanest Linus relationship to rig is "Linus's OpenAI-compatible HTTP endpoint (DEC-0005) is consumable by any rig
provider that points its `base_url` at the Linus endpoint" — i.e., interoperability through the existing OpenAI
compatibility layer, not through a direct rig dependency. If a Phase 5+ Linus component needs Rust-side provider
abstraction, the natural shape is an out-of-tree mini-crate (`linus-rig-provider` or similar) that implements the rig
trait stack against the Linus orchestration endpoint, distributed separately from the Linus core repo.

## 7. Questions for Dan

1. **Mirror rig's `ProviderClient` capability-trait shape in any Linus-side Rust adapter?** When Phase 5+ Linus Rust
   components need to talk to LLM providers, the cleanest design is to mirror rig's `ProviderClient` +
   `CompletionClient` + `EmbeddingsClient` + `TranscriptionClient` + … capability-trait stack so that downstream Rust
   consumers can swap between rig's existing providers and a Linus-shaped provider without learning new vocabulary. The
   alternative is to roll a Linus-native trait shape and accept the friction. Tentative answer: mirror rig's trait
   shape; the cost is small and the interoperability win is real. Worth a Phase 5+ ADR alongside the
   orchestration-backend Phase 2a work.

2. **Implement a Linus rig-provider so any rig agent can talk to Linus's orchestration backend out-of-the-box?** rig's
   `OllamaExt` provider is ~20 lines of trait impls plus a request/response translation layer over the shared
   `Client<Ext, H>` shape. Implementing a `LinusExt` provider for Linus's OpenAI-compatible endpoint (per DEC-0005) is
   similarly small — most of the work is reusing the `OpenAIExt` request/response shapes with a different `base_url`.
   Should this live in-tree under `src/linus/rust/` (the Linus repo grows a Rust crate), out-of-tree as a separate
   `linus-rig-provider` crate (cleaner separation, harder to keep in sync), or wait until a concrete Phase 5+ consumer
   materializes? Tentative answer: defer until Phase 5+ when there's a concrete consumer; the OpenAI-compatible endpoint
   already provides interoperability through `OpenAIExt` with `base_url` override, which is the path of least resistance
   for the interim.

3. **Adopt rig's clippy lint set as the Linus Rust-conventions baseline?** rig's `Cargo.toml` workspace lints
   (`unwrap_used`, `expect_used`, `indexing_slicing`, `panic`, `panic_in_result_fn`, `todo`, `unimplemented`,
   `unreachable`, `dbg_macro`, `await_holding_lock`, `await_holding_refcell_ref` all `deny` or `forbid`) are a
   strict-but-reasonable baseline for production Rust code. Should Linus adopt this lint set as a convention for any
   Linus-internal Rust crate (mirroring how the linus-conda env's ruff config commits to line-length 120 and
   import-sort)? Tentative answer: yes, codify in a "Rust conventions" subsection of CLAUDE.md or a new
   `docs/conventions/rust.md`, alongside the existing Python ruff convention. The dependency is zero (clippy ships with
   rustup); the discipline upside is real.

4. **rig::pipeline vs. workgraph for Rust-side multi-step composition?** CLAUDE.md recommends workgraph's
   `.workgraph/graph.jsonl` append-only DAG plus `handler_for_model.rs` dispatch as the Phase 2a session-store and
   audit-log shape (G7 synthesis recommendation; the Rust crate doesn't need to be vendored, the JSONL shape and
   dispatch pattern can be ported to Python). rig::pipeline is a different DAG abstraction at a different scope
   (in-process typed pipeline composition vs. durable orchestration runtime). Are these complementary (workgraph for the
   durable orchestration layer, rig::pipeline for in-process Rust-side composition once Rust components land in Phase
   5+) or competing references that should pick a winner? Tentative answer: complementary — they solve different
   problems — but the Phase 5+ ADR that adopts rig's trait shape should also name rig::pipeline as the in-process
   composition reference for Rust-side multi-step work, distinct from workgraph's durable-DAG role.

5. **MCP via `rmcp` confirms the substrate generalizes — should Linus track `rmcp` as the Rust counterpart to fastmcp?**
   DEC-0045 commits Linus's Python layer to fastmcp; rig's `rmcp` integration uses the `rmcp` crate (Rust MCP SDK),
   confirming that the MCP substrate (DEC-0018) is genuinely cross-language. Should the Linus conventions name `rmcp` as
   the Rust-side MCP framework default, parallel to fastmcp's Python-side default (DEC-0045)? Tentative answer: yes,
   document `rmcp` as the Rust-side default in the same ADR that adopts rig's trait shape — the cost is documenting a
   single sentence; the alternative is leaving the convention implicit and risking later inconsistency. Lower stakes
   than DEC-0045 since the consumer surface is smaller.

6. **rig as a multi-language Rust fan-out reference — does the rig ecosystem (25 providers, 15 vector-store companion
   crates, 7.2k★) suggest a stronger Rust posture for Linus than DEC-0027 currently endorses?** DEC-0027's
   multi-language stance is reactive ("Rust is acceptable when components fit"); rig's existence and adoption
   demonstrates that there is a substantial Rust ecosystem for LLM application infrastructure that Linus could consume
   in Phase 5+. Should the Phase 5+ planning include a "Linus Rust component inventory" exercise (what's already in Rust
   — pmetal, claw-code, claw-code-local — and what could fan out — Linus-rig-provider, Linus-rmcp- server, possibly a
   Rust-side Worker pool) ahead of any actual Rust work? Tentative answer: light-touch — note the inventory in the Phase
   5 planning spec; do not commit to a Rust-fan-out roadmap until a concrete Phase 5+ consumer drives it. Avoid the
   "Rust everywhere" trap; remain reactive per DEC-0027.

7. **rig's `extractor` (typed structured extraction) as a Rust-side analogue to the BioReason-Pro typed-structured-
   prediction convention.** CLAUDE.md commits to "typed structured prediction wrapping free-text rationale" for any
   biology skill or domain skill producing a predictive output (BioReason-Pro shape, S25). rig's `extractor` module uses
   `schemars::JsonSchema` to constrain LLM output to a typed Rust struct — the Rust-side counterpart to pydantic's
   typed-output shape. Phase 7+ biology Workers may eventually have a Rust-side adapter (if pmetal serve ever exposes a
   Rust-only fast-path); should the typed-structured-prediction convention explicitly name rig's `extractor` (alongside
   pydantic-ai's typed outputs) as the canonical Rust-side reference? Tentative answer: yes, when the biology-skills
   convention graduates to a dedicated `docs/skills/notes/` guide, name both the Python pydantic shape and the Rust
   schemars shape; until then, defer.
