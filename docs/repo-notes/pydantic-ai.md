# pydantic-ai (`pydantic/pydantic-ai`)

## 1. Purpose and scope

Pydantic AI is a production-grade Python agent framework from the Pydantic team that brings FastAPI's ergonomic design
philosophy to LLM application development. It offers type-safe agent building, model-agnostic provider support (OpenAI,
Anthropic, Ollama, Mistral, Google, etc.), structured output via Pydantic validation, dependency injection, tool
registry, and tight integration with Pydantic Logfire for observability. For Linus, it's a reusable orchestration
primitive: the Agent class abstracts away provider differences and handles message flow, tool calling, and fallback
strategies that could power local Worker agents or serve as a reference for Linus's own orchestration layer.

## 2. Architecture summary

Pydantic AI is a workspace-structured monorepo with four main packages: `pydantic-ai-slim` (the core Agent framework,
model providers, and tools; minimal dependencies), `pydantic-graph` (type-hint-based DAG for complex agent loops),
`pydantic-evals` (systematic evaluation of agents and stochastic functions), and `clai` (a CLI chat interface + optional
web UI). The Agent is the primary abstraction: it wraps a `Model` provider, accepts typed dependency injection via
`RunContext`, exposes a `@tool` decorator for registering LLM-callable functions with Pydantic-validated arguments,
supports dynamic instructions, and manages multi-turn conversations. Capabilities (web search, thinking, MCP) are
composable extras that bundle tools + instructions + model tweaks. The system achieves full type safety through
extensive use of `TypeVar`, `Protocol`, and Pydantic schemas; docstrings are parsed and passed to the LLM as tool
descriptions.

## 3. What's reusable in Linus

The Agent class and its design patterns are directly liftable: RunContext dependency injection, the @tool decorator
pattern, Pydantic validation on tool arguments/outputs, and the provider-agnostic Model abstraction. Linus can adopt
these patterns wholesale for its Worker orchestration — each local model execution becomes a Model subclass, tools are
registered via @agent.tool, and RunContext carries domain-specific state (KnowledgeBase session, genomics context,
etc.). The MCP integration (native in pydantic-ai) is immediately applicable to Phase 2a's tool substrate. The
Capabilities pattern (composable feature bundles) is a cleaner alternative to flat tool registries for Linus's plugin
architecture.

## 4. What's inspiration only

The evals framework (DSL for systematic testing of LLM behavior, metric aggregation, result tracking) is architecturally
sound but Linus doesn't need an evals subsystem yet — Dan's task suite and benchmark suite serve that role. The graph
library (type-hint-based DAG for complex agent loops with branching/loops) is useful for representing multi-step Agent
workflows but not required for Phase 2a MVP.

## 5. What's incompatible or out of scope

Pydantic AI's Model providers all target remote APIs (OpenAI, Anthropic, Google, Azure Bedrock, etc.) or lightweight
local models via Ollama. There is no first-class support for MLX-native inference, LoRA-served weights, or streaming
from disk — those remain Linus's domain. The framework is aggresstic about where the Model runs; hooking in MLX-Flash or
pmetal inference is a straightforward Model subclass implementation.

## 6. Recommendation: **Integrate (Phase 2a)**

Pydantic AI should be the base layer of Linus's orchestration backend. The Agent class, Model abstraction, tool
decorator, dependency injection pattern, and type-safety philosophy align perfectly with Linus's design. A concrete
Phase 2a task: wrap MLX-Flash and Ollama models as Pydantic AI Model subclasses, port Dan's KnowledgeBase tools to the
@tool pattern, and instantiate an Agent configured with Linus's tool registry. This gives a complete reference
implementation of the orchestration layer that can be tested against the Dan task suite.

## 7. Questions for Dan

1. **Pydantic AI vs. building from scratch.** Adopting pydantic-ai wholesale reduces Linus orchestration code by ~70%
   (Agent, model dispatch, tool registration, type validation all handled). The tradeoff is a new external dependency in
   the core inference path. Is that acceptable, or should Linus implement its own lightweight Agent wrapper using only
   pydantic?
2. **The graph library for multi-step tasks.** Some of Dan's domain tasks (e.g., "analyze a paper, then run a
   computational workflow") map naturally to DAGs. Is pydantic-graph's type-hint syntax worth adopting, or keep agent
   control flow as imperative loops? _Partially resolved (see
   [answered-questions.md](../questions/answered-questions.md)): Workgraph JSONL append-only DAG is the recommended
   Phase 2a session-store and audit-log format; pydantic-graph as a control-flow layer is not committed but not
   excluded._
3. **Capabilities for Linus plugins.** Pydantic AI capabilities bundle {tools, instructions, model tweaks}. Should Linus
   adopt this pattern, or is it over-engineered for Linus's tool + instruction model? _Partially resolved (DEC-0046,
   DEC-0050, see [answered-questions.md](../questions/answered-questions.md)): Tool registry has a deployment field
   (local/mcp/external_api); Role bundles capability_set + memory_access_tier — similar to Capabilities pattern but
   Linus-native._
