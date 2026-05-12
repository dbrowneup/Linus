# autogen (`microsoft/autogen`)

## 1. Purpose and scope

AutoGen is Microsoft Research's multi-agent framework — the original incubator for the "group chat as a coordination
primitive" pattern that has since spread to LangGraph, Swarm, CrewAI, and Letta. The repo as cloned is the **AutoGen
v0.4 line** (the current stable version is 0.7.5 across the three core packages), which is a major architectural rewrite
of the original v0.2 codebase: where v0.2 was a single `pyautogen` package built around the `ConversableAgent` +
`GroupChat` + `GroupChatManager` triad, v0.4 splits the framework into three Python packages (`autogen-core`,
`autogen-agentchat`, `autogen-ext`) with an event-driven actor runtime underneath, plus a parallel .NET implementation
in `dotnet/`, an `autogen-studio` no-code GUI, and the `agbench` benchmarking harness. The repo also contains the
reference implementation of **Magentic-One** — Microsoft Research's generalist multi-agent system that wraps the AutoGen
group-chat primitives with a ledger-based orchestrator, file/web/code surfaces, and a documented research result in the
[Magentic-One blog post](https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks).
The `pyautogen` legacy package still ships in the same repo for backward compatibility but is not the surface this note
reviews.

The README banner above the install instructions is the most load-bearing fact about the repo: **AutoGen is in
maintenance mode**. Microsoft has redirected new development to
[Microsoft Agent Framework](https://github.com/microsoft/agent-framework) (MAF), the explicit "enterprise-ready
successor", and contributions to AutoGen are limited to bug fixes, security patches, and documentation. The framework
remains usable and the patterns remain durable references — but Linus should treat AutoGen as a **frozen reference
implementation** of the group-chat coordination idiom rather than a live dependency to track. Per CLAUDE.md's reactive
multi-language stance (DEC-0027) and the bounded orchestration scope (DEC-0020), this note's recommendation is **Study**
— read AutoGen for the group-chat patterns and the Magentic-One ledger architecture, then implement the relevant subset
against Linus's pydantic-ai + fastmcp substrate (DEC-0044, DEC-0045, the g11 cluster's pydantic-ai Integrate verdict).

## 2. Architecture summary

The Python deliverable is a four-package monorepo under `python/packages/`. The substantive packages are `autogen-core`
(the foundational interfaces and event-driven runtime, version 0.7.5, MIT-licensed), `autogen-agentchat` (the
higher-level agent-and-team API closest to the v0.2 surface, depends on `autogen-core==0.7.5`), and `autogen-ext`
(LLM-client implementations, code executors, MCP tooling, runtime backends, named first-/third-party agents like
WebSurfer / FileSurfer / Magentic-One). The other packages — `magentic-one-cli` (the CLI that wraps the Magentic-One
team), `autogen-studio` (FastAPI + React no-code GUI), `agbench` (benchmarking harness), `autogen-magentic-one`
(legacy/transition shim), `autogen-test-utils`, `component-schema-gen`, and the legacy `pyautogen` — are downstream
consumers of the core three. The `dotnet/` directory is a parallel .NET implementation (Microsoft.AutoGen.Contracts /
Core / Core.Grpc / RuntimeGateway.Grpc) that talks to the Python runtime over gRPC for cross-language deployment; it
ships separately on NuGet and is out of scope for Linus per DEC-0027 (Python is the core orchestration language; .NET is
not on the roadmap).

The **`autogen-core` runtime** is built around an event-driven actor pattern. The public surface
(`autogen_core/__init__.py`) exposes `Agent`, `BaseAgent`, `RoutedAgent`, `ClosureAgent`, `AgentId`, `AgentType`,
`AgentRuntime`, `MessageContext`, `TopicId`, `Subscription` (`TypeSubscription`, `TypePrefixSubscription`,
`DefaultSubscription`, `default_subscription`, `type_subscription`), `Component`, `ComponentModel`, `CancellationToken`,
and the `@event` / `@rpc` / `@message_handler` decorators that mark agent methods as message handlers. The runtime is
the **`SingleThreadedAgentRuntime`** (`_single_threaded_agent_runtime.py`, ~830 LoC) for in-process operation, and the
**`GrpcWorkerAgentRuntime`** under `autogen-ext/runtimes/grpc/` for distributed operation across multiple processes or
hosts. Agents publish messages to `TopicId`s and subscribe via type-based or prefix-based subscriptions — a
publish/subscribe shape rather than direct point-to-point calls. This is a deliberately different runtime model from
Letta's (which is request/response RPC over a FastAPI server with `Group`s as schedulers) and from pydantic-ai's (which
is a single Agent class with synchronous tool dispatch). The pub/sub primitive scales naturally to the
distributed-runtime case because subscriptions are independent of physical agent location.

The **`Component` / `ComponentModel` declarative-configuration pattern** is the load-bearing engineering choice for
serialization. Every framework primitive — agents, teams, tool workbenches, model clients, termination conditions —
implements `Component[ConfigType]` where `ConfigType` is a Pydantic model. This makes the entire agent topology
declaratively serializable: a `MagenticOneGroupChatConfig` captures `participants: List[ComponentModel]`,
`model_client: ComponentModel`, `termination_condition: ComponentModel | None`, plus the configuration fields. The shape
is consistent enough that the AutoGen Studio GUI builds workflows by composing `ComponentModel`s in the browser and
round-tripping them as JSON. For Linus this is a useful design discipline reference — every agent and team can be
serialized, versioned, and reloaded — though the implementation requires Pydantic-2 + a strict Component contract that
has to be opted into pervasively.

The **`autogen-agentchat` agent layer** under `python/packages/autogen-agentchat/src/autogen_agentchat/agents/` provides
six built-in chat agents totaling ~3.6k LoC: **`AssistantAgent`** (1,703 LoC, the workhorse — wraps a
`ChatCompletionClient`, registers tools and a `Workbench` for MCP, supports streaming, parallel tool calls,
`max_tool_iterations` for the inner reasoning-and-tool-use loop, structured output via Pydantic models, and
`Memory`-backed long-term context); **`UserProxyAgent`** (the human-in-the-loop primitive, async-input function
hookable); **`CodeExecutorAgent`** (893 LoC — wraps a `CodeExecutor` to run code blocks emitted by other agents);
**`SocietyOfMindAgent`** (302 LoC — wraps an inner team as a single agent for hierarchical composition);
**`MessageFilterAgent`** (203 LoC — filters which messages an inner agent sees); and **`BaseChatAgent`** (the abstract
base). The `AssistantAgent` is the canonical reference for a tool-using LLM-backed agent and includes the modern
features Linus will need: `model_client_stream` for streaming token output, `reflect_on_tool_use` for the post-tool
reflection step, `tool_call_summary_format` for structuring tool-call records into the conversation, and a declarative
`AssistantAgentConfig` that captures the full state.

The **group-chat / team layer** under `autogen-agentchat/teams/_group_chat/` (~3.8k LoC across the cluster) is the
canonical reference this repo-note is reviewing. There are five group-chat managers, each in a separate module:

- **`RoundRobinGroupChatManager`** (`_round_robin_group_chat.py`, 328 LoC). Cycles through participants in a fixed
  order; the simplest scheduling primitive. The `select_speaker` method increments
  `_next_speaker_index = (current_speaker_index + 1) % len(self._participant_names)`. State is a
  `RoundRobinManagerState` Pydantic model with `message_thread`, `current_turn`, `next_speaker_index` — directly
  serializable and resumable.
- **`SelectorGroupChatManager`** (`_selector_group_chat.py`, 730 LoC). Uses an LLM to choose the next speaker at each
  turn from the participant list. The `selector_prompt` (a string template with `{participants}` / `{history}`
  placeholders) is sent to the model; an optional `selector_func: Callable` shortcuts the LLM call when a deterministic
  choice is available; an optional `candidate_func: Callable` narrows the candidate set before the LLM selects from it;
  `allow_repeated_speaker: bool` controls whether the same agent can speak twice in a row; `max_selector_attempts`
  bounds retries on parse failure. State is `SelectorManagerState`. This is the LLM-driven orchestration primitive —
  every speaker selection costs one model call, which is the O(N) per-step cost the g7 synthesis flags as the
  scalability lever for debate-or-vote heuristics.
- **`SwarmGroupChatManager`** (`_swarm_group_chat.py`, 321 LoC). Speaker selection is driven entirely by
  `HandoffMessage`s — when an agent emits a `HandoffMessage(target=<agent_name>)`, control transfers to that named
  agent. No central decision-maker; coordination lives in the handoff messages themselves. Closest to OpenAI's Swarm
  pattern. State is `SwarmManagerState` with `_current_speaker` tracked.
- **`MagenticOneOrchestrator`** (`_magentic_one/_magentic_one_orchestrator.py`, 536 LoC). The most elaborate
  orchestrator in the repo and the productized form of Microsoft Research's Magentic-One paper. The orchestrator
  maintains a **task ledger** (initial facts + plan derived from the user request) and a **progress ledger** (re-built
  every step from a JSON-structured prompt with five fields: `is_request_satisfied`, `is_in_loop`,
  `is_progress_being_made`, `next_speaker`, `instruction_or_question`, each as `{reason: str, answer: str|bool}`).
  Stalls are tracked (`_n_stalls`) — after `max_stalls` stalls the orchestrator re-plans by re-running the
  facts-and-plan prompts. The orchestrator is implemented as a `BaseGroupChatManager` subclass, so it composes cleanly
  with the rest of the group-chat machinery. The five orchestrator prompts (`ORCHESTRATOR_TASK_LEDGER_FACTS_PROMPT`,
  `ORCHESTRATOR_TASK_LEDGER_PLAN_PROMPT`, `ORCHESTRATOR_TASK_LEDGER_FULL_PROMPT`, `ORCHESTRATOR_PROGRESS_LEDGER_PROMPT`,
  `ORCHESTRATOR_TASK_LEDGER_FACTS_UPDATE_PROMPT`, `ORCHESTRATOR_TASK_LEDGER_PLAN_UPDATE_PROMPT`,
  `ORCHESTRATOR_FINAL_ANSWER_PROMPT`) are all in `_magentic_one/_prompts.py` and are the closest existing reference for
  "what does a productized supervisor agent prompt look like."
- **`GraphFlow`** (`_graph/_digraph_group_chat.py`, 878 LoC, plus `_graph_builder.py`, 209 LoC). An experimental DAG
  execution model where nodes are agents and edges are conditional message-content predicates. The fluent
  `DiGraphBuilder` API (`add_node` / `add_edge` / `add_conditional_edges` / `set_entry_point`) supports sequential
  chains, parallel fan-outs, conditional branching, and cyclic loops with safe exits. This is functionally similar to
  LangGraph's StateGraph — the AutoGen team apparently arrived at the same DAG-of-agents abstraction independently.
  Marked experimental; API is documented as expected to change.

The five group-chat patterns are not equally mature. Round-robin and selector are stable and well-documented. Swarm is
stable but niche. Magentic-One is the research result. GraphFlow is explicitly experimental. The `Society of Mind` agent
(`agents/_society_of_mind_agent.py`) wraps any group-chat as a single agent for hierarchical composition, producing a
Linus-relevant primitive: a Magentic-One team can be embedded as a tool-call surface inside another AssistantAgent's
tool registry — essentially a hierarchical Maestro/Worker pattern at the agent level.

The **inter-agent message types** (`autogen-agentchat/messages.py`) form a typed message taxonomy: `TextMessage` /
`MultiModalMessage` / `HandoffMessage` / `StopMessage` / `ToolCallRequestEvent` / `ToolCallExecutionEvent` /
`ToolCallSummaryMessage` / `ThoughtEvent` / `ModelClientStreamingChunkEvent` / `MemoryQueryEvent` /
`SelectSpeakerEvent`. Each is a Pydantic model serializable through the `MessageFactory`. The `HandoffMessage` is the
swarm-coordination primitive; `ToolCallRequestEvent` / `ToolCallExecutionEvent` / `ToolCallSummaryMessage` are the
canonical tool-call audit trail. This is the existing reference for what a Linus `AgentReport` (DEC-0051) plus the
surrounding inter-agent message types should look like — AutoGen has done the exhaustive enumeration so Linus does not
have to.

The **MCP integration** under `autogen-ext/tools/mcp/` (`_actor.py`, `_workbench.py`, `_session.py`, `_stdio.py`,
`_sse.py`, `_streamable_http.py`, `_host.py`) is mature and first-class. The `McpWorkbench` is a `Workbench`
implementation that wraps an external MCP server; an `AssistantAgent` can be configured with `workbench=<McpWorkbench>`
or `workbench=List[McpWorkbench]` instead of a static tool list, and the MCP server's `list_tools` / `call_tool` /
`list_resources` / `read_resource` / `list_resource_templates` / `list_prompts` / `get_prompt` capabilities surface to
the agent transparently. Optional `Sampling` / `Roots` / `Elicitation` capabilities are supported via `McpSessionHost`.
All three transports (`StdioServerParams`, `SseServerParams`, `StreamableHttpServerParams`) are supported. The README's
second example (web-browsing assistant via Playwright MCP server) is the canonical "real product uses MCP for tools"
demonstration. AutoGen's MCP integration **is** the v0.4 default story — the README demonstrates it before any other
tool pattern. This converges with DEC-0045 (fastmcp as the default Linus MCP framework) and DEC-0018 (MCP as the
tool-extensibility substrate); AutoGen is one of the six repos in the cloned collection that ship MCP-as-default per the
g6 synthesis.

The **model-client layer** under `autogen-ext/models/` covers `openai`, `anthropic`, `azure`, `cache`, `llama_cpp`,
**`ollama`** (Linus-relevant), `replay`, and `semantic_kernel`. The `OpenAIChatCompletionClient` is the canonical
reference; the `OllamaChatCompletionClient` is the local-first option. There is no MLX provider, no MLX-Flash provider,
no pmetal-serve provider — same gap rig has, with the same workaround (point an OpenAI-compatible client at Linus's
orchestration backend per DEC-0005, which itself proxies to Ollama / MLX-Flash / pmetal). The `autogen-core/models/`
interface (`ChatCompletionClient`, `ChatCompletionContext`, `LLMMessage`, `CreateResult`, `ModelFamily`) is
provider-agnostic; adding a Linus-shaped provider is a Pydantic-Component subclass plus a request/response translation
layer.

The **memory layer** under `autogen-core/memory/` (`_base_memory.py` + `_list_memory.py`) is intentionally minimal: a
`Memory` ABC plus a `ListMemory` reference implementation that holds a list of `MemoryContent`. Compare with rig's
`ConversationMemory` (also intentionally minimal) and Letta's full named-blocks + git-versioned memory_repo + paged
archival memory pillar (substantial). AutoGen sits at the rig end of the spectrum — the framework deliberately does not
commit to a memory architecture, leaving it to user code or to layered extensions. Per DEC-0028 / DEC-0029 the Linus
memory pillar is independent of any framework's memory abstraction; AutoGen's `Memory` ABC is a useful subscribe-pattern
shape but contributes nothing to the memory-architecture substance.

The **code-executor layer** under `autogen-ext/code_executors/` and `autogen-core/code_executor/` provides Docker /
local / Jupyter executors. Magentic-One wires up a Docker executor by default (with a fallback to local) — important
because the Magentic-One team's `Coder` and `ComputerTerminal` agents run arbitrary code, and the warning block in
`autogen-ext/teams/magentic_one.py` is explicit about the security implications. For Linus per SAFETY.md the relevant
adoption path is the local code-executor pattern with audit-logging — Docker executors are forbidden for ML workloads
(DEC-0027) but acceptable for stateless code execution.

The `python/samples/` directory has ~30 sample projects (`agentchat_chess_game`, `agentchat_dspy`, `agentchat_fastapi`,
`agentchat_graphrag`, `agentchat_streamlit`, `core_async_human_in_the_loop`, `core_chess_game`, `core_chainlit`, plus
many more) covering both core and agentchat surfaces. The samples are the cleanest end-to-end runnable references for
how the framework is actually used; the `agentchat_dspy` sample is particularly relevant because it demonstrates how to
compose AutoGen with DSPy (DEC seed for Phase 6 fine-tuning workflows per the g11 synthesis).

## 3. What's reusable in Linus

AutoGen's contribution to Linus is design vocabulary — the group-chat manager taxonomy, the Magentic-One ledger pattern,
the typed message taxonomy, the Component/ComponentModel serialization discipline. The framework itself is not vendored.

**Phase 3 — group-chat manager taxonomy as the canonical reference for the agent-spawner coordination strategies
(DEC-0050, DEC-0051).** AutoGen's five-pattern taxonomy (round-robin, selector, swarm, Magentic-One, GraphFlow) is the
most thoroughly worked-out menu of multi-agent coordination strategies in the cloned-repo collection. The
[`phase3-spawner.md`](../specs/phase3-spawner.md) spec commits to `Role` as a first-class type (DEC-0050) and
`AgentReport` as the typed inter-agent message (DEC-0051), but does not yet name the manager taxonomy. This repo gives
that taxonomy concrete vocabulary: **round-robin** (deterministic cycling, the simplest baseline), **selector**
(LLM-driven speaker selection at each step, the workhorse for heterogeneous role sets), **swarm/handoff** (decentralized
coordination via HandoffMessage, useful when agents have local knowledge of who to talk to next),
**supervisor/Magentic-One-orchestrator** (centralized planner with task + progress ledgers, the pattern most directly
applicable to the Linus Maestro/Worker shape), and **graph/DAG** (declarative DAG topology, the pattern that overlaps
with workgraph's session-store recommendation). The Letta repo-note ([`Letta.md`](Letta.md) §3) committed Linus Phase 3
to `supervisor` + `dynamic` as the v0 vocabulary; AutoGen's Magentic-One is the **reference implementation** of the
supervisor pattern, with seven worked prompts and a 536-LoC orchestrator the Linus implementation can crib from.

**Phase 3 — Magentic-One task-ledger + progress-ledger pattern as the canonical supervisor-orchestrator shape.** The
two-ledger pattern is the load-bearing piece. The **task ledger** is built once at task start by running two LLM calls —
one to extract facts (`ORCHESTRATOR_TASK_LEDGER_FACTS_PROMPT`, asks the model to enumerate given facts, facts to look
up, facts to derive, and educated guesses) and one to derive a plan (`ORCHESTRATOR_TASK_LEDGER_PLAN_PROMPT`). The
**progress ledger** is built at every step thereafter from `ORCHESTRATOR_PROGRESS_LEDGER_PROMPT`, which forces a
five-field JSON output (`is_request_satisfied`, `is_in_loop`, `is_progress_being_made`, `next_speaker`,
`instruction_or_question`). Stalls are tracked (`_n_stalls`); after `max_stalls` (default 3) the orchestrator re-runs
the facts-update and plan-update prompts and re-enters the outer loop. This is the productized form of "self-reflective
supervisor agent with explicit loop-detection" that the agentic-systems synthesis identifies as the canonical
multi-agent debate-vs-execution framing. The Linus Phase 3 spawner spec should adopt this pattern for the supervisor
manager: the `is_request_satisfied` / `is_in_loop` / `is_progress_being_made` triad is the natural shape of the
validation gate (S15 in the answered-questions corpus); the `next_speaker` / `instruction_or_question` pair is the
natural shape of the dispatch step. Cribbing the seven prompts directly (with attribution in the docstring) and adapting
to the Linus `Role` + `AgentReport` vocabulary is faster than re-deriving the prompts.

**Phase 3 — typed message taxonomy as a reference for the Linus inter-agent message catalog.** AutoGen's
`autogen-agentchat/messages.py` enumerates 11 distinct message types: `TextMessage`, `MultiModalMessage`,
`HandoffMessage`, `StopMessage`, `ToolCallRequestEvent`, `ToolCallExecutionEvent`, `ToolCallSummaryMessage`,
`ThoughtEvent`, `ModelClientStreamingChunkEvent`, `MemoryQueryEvent`, `SelectSpeakerEvent`. DEC-0051 commits Linus to
`AgentReport` as the typed inter-agent message but does not enumerate the surrounding types. This is the reference for
what the surrounding catalog should cover — particularly `ToolCallRequestEvent` / `ToolCallExecutionEvent` /
`ToolCallSummaryMessage` (the canonical tool-call audit trail), `ThoughtEvent` (the reasoning-token first-class artifact
per DEC-0030), `HandoffMessage` (if Linus adopts swarm-style coordination as a v1 manager), and `SelectSpeakerEvent`
(audit record of supervisor decisions). The Linus catalog does not need to mirror this exactly, but the shape is the
existing target — the reasoning-tokens-as-events pattern is directly relevant to DEC-0030's "scratchpad as durable
artifact" commitment.

**Phase 2 / 3 — Component/ComponentModel declarative-configuration discipline.** AutoGen's choice to make every
framework primitive `Component[ConfigType]` with a Pydantic config model is a useful design discipline for any Linus
orchestration primitive. The benefit: every team, agent, tool, model client, termination condition can be serialized to
JSON, versioned, reloaded, diffed, and composed visually. The cost: pervasive Pydantic-2 dependence and a strict
contract on every component. Linus's Phase 2a adoption of pydantic-ai (the g11 cluster Integrate verdict) already puts
Linus on Pydantic-2; the AutoGen Component pattern is the natural extension to the orchestration layer's other
primitives. Worth a Phase 2a note: every Linus primitive ships a Pydantic config model, and the orchestration layer
exposes a `to_component_model()` / `from_component_model()` round-trip. This is the direct analogue to Letta's **Agent
File** format (`.af` schema, [`Letta.md`](Letta.md) §3) — both products solve the same problem (declarative,
serializable, round-trippable agent topologies) with slightly different shapes.

**Phase 3 — `SocietyOfMindAgent` as a reference for hierarchical Maestro/Worker composition.** The `SocietyOfMindAgent`
wraps an inner team as a single agent with the same chat interface as any other agent. This is the directly applicable
primitive for "a Magentic-One team is itself a tool that the Linus Maestro can call" — it gives hierarchical composition
without a special abstraction layer, just normal agent-as-tool. Phase 3+ Linus spawner work that wants to build
investigation-memory-aware sub-teams (DEC-0052) can use this shape: the inner team runs with its own investigation
memory, the outer Maestro sees only the team's `AgentReport`, and the encapsulation is automatic. The 302-LoC
implementation is small enough to crib if Linus needs the pattern before adopting an agent-framework dependency.

**Phase 5+ — pub/sub agent runtime as a reference for distributed agent operation.** The `SingleThreadedAgentRuntime`
(in-process) and `GrpcWorkerAgentRuntime` (cross-process gRPC) split is the existing reference for how a Linus
distributed-Worker pool would be wired in Phase 5+ if Linus ever runs Workers across multiple processes or hosts. The
pub/sub-with-typed-subscriptions shape (`TopicId` + `TypeSubscription` / `TypePrefixSubscription` /
`DefaultSubscription`) scales naturally because subscriptions are independent of physical agent location — agent A
subscribed to topic T receives messages whether A is in the same process as the publisher or across a gRPC boundary.
Linus Phase 1–4 is single-machine, so this is reference-only — but if Phase 8+ ever distributes across the M1 Max + a
future Mac Studio, AutoGen's `GrpcWorkerAgentRuntime` is the existing template.

**Phase 2a — MCP `Workbench` shape as a reference for multi-server tool composition.** The `McpWorkbench` pattern —
where an agent is configured with `workbench=<McpWorkbench>` or `workbench=List[McpWorkbench]` and the server's full
tool / resource / prompt surface is exposed transparently — is one of two existing references (alongside Letta's
`mcp_manager` / `mcp_server_manager` split) for how the Linus Phase 2a tool registry should expose multiple MCP servers
to a single agent. The differences are: AutoGen exposes resources and prompts in addition to tools (Letta is tool-only),
AutoGen supports MCP Sampling / Roots / Elicitation via `McpSessionHost` (Letta does not), and AutoGen's `ToolOverride`
mechanism allows per-tool name remapping at the workbench level (Letta has no equivalent). For Phase 2a the
resources-and-prompts surface is likely scope-creep; the tool-only surface is the path of least resistance. But if Phase
7+ KnowledgeBase work surfaces resources / prompts as first-class MCP capabilities (per DEC-0044's paper-qa
integration), AutoGen's `McpWorkbench` is the template.

## 4. What's inspiration only

The **AutoGen Studio no-code GUI** (`autogen-studio` package, FastAPI + React) is a useful reference for what a Linus
visual orchestration builder might look like at Phase 5+, but Linus's harness-plurality model (DEC-0017) and the bounded
orchestration scope (DEC-0020) keep visual builders out of the orchestration backend's product surface. Per the README's
own warning — "AutoGen Studio is meant to help you rapidly prototype multi-agent workflows... It is **not meant to be a
production-ready app**" — Studio is itself flagged as prototype-grade, which weakens the case further. If a Linus visual
front-end ever materializes, openclaw ([`openclaw.md`](openclaw.md)) is the more relevant reference per DEC-0008.

The **`agbench` benchmarking suite** is a useful design template for a Linus benchmark harness, but Linus already has
`benchmarks/dan_tasks/` as the private benchmark suite (CLAUDE.md repo layout) and the g11 cluster commits to
`promptfoo` as the evaluation harness Integrate verdict. The agbench shape is reference-only; the substantive Linus
evaluation pipeline routes through promptfoo + dan_tasks + the lmnr observability layer.

The **TypeScript / .NET cross-language story** — the `dotnet/` directory ships a parallel .NET implementation that talks
to the Python runtime over gRPC for cross-language deployment — is an interesting design point about what "agent runtime
as a service" looks like when the runtime is intentionally polyglot. For Linus per DEC-0027 (Python core, Rust where it
fits, .NET not on the roadmap) this is reference-only. The gRPC-as-cross-language-substrate choice is a useful
confirming signal that gRPC is the natural protocol for cross-language agent runtimes — relevant if any Phase 5+ Rust
component (claw-code-local, pmetal-serve) ever needs to talk to a Python agent runtime.

The **declarative `selector_prompt` template format** (with `{participants}` / `{history}` placeholders) is a useful
reference for how to parametrize speaker-selection prompts, but Linus's prompt management — once it has any — should use
a structured Pydantic schema (the BioReason-Pro typed-structured-prediction shape per CLAUDE.md) rather than string
templating. AutoGen's choice is fine for v0 but is not the modern shape Linus should mirror.

The **`agentchat_chess_game`** and **`core_chess_game`** samples are useful as worked examples of how multi-agent
coordination scales to game-playing scenarios with strict turn semantics. Out of scope for Linus's domain (genomics,
science, code), but the turn-coordination patterns may be useful if Phase 7+ Linus ever adopts a game-style benchmark
for multi-agent reasoning.

The **`agentchat_dspy` sample** is the cleanest existing reference for AutoGen + DSPy composition — useful if Phase 6
Linus fine-tuning work (the g11 cluster's DSPy Study verdict) ever wants to compile prompts for a Linus-based agent via
DSPy. Reference-only at the sample level; the substantive integration work is Phase 6.

## 5. What's incompatible or out of scope

**AutoGen is in maintenance mode; Microsoft Agent Framework (MAF) is the live successor.** This is the most important
single fact about the repo. The README banner is unambiguous: "AutoGen will not receive new features or enhancements and
is community managed going forward. New users should start with Microsoft Agent Framework." For Linus this means three
things. First, Linus should not adopt AutoGen as a live dependency — patterns are durable, the upstream is not. Second,
Linus should not invest in building a Linus-specific AutoGen adapter (model-client, runtime extension, etc.) because the
energy is going to MAF; any adapter would target a frozen API surface. Third, the Magentic-One reference implementation,
the group-chat patterns, and the orchestrator prompts are still worth reading and cribbing — they will not change, and
they capture Microsoft Research's accumulated multi-agent engineering taste. The **Microsoft Agent Framework** repo
(`microsoft/agent-framework`) is worth a separate Watch entry in the Linus tracking — when MAF stabilizes its public
Python API, a focused repo-note covering "what changed since AutoGen v0.4" is the natural follow-up. But that is a
separate exercise; this repo-note is bounded to the AutoGen v0.4 line as cloned.

**The .NET implementation is out of scope.** The `dotnet/` directory and the four NuGet packages
(`Microsoft.AutoGen.Contracts` / `Core` / `Core.Grpc` / `RuntimeGateway.Grpc`) are not relevant to Linus's
Python-core-plus-Rust-where-it-fits posture (DEC-0027). The .NET / Python cross-language story is interesting design
material but not actionable for the Linus roadmap.

**The default model assumption is hosted GPT-4-class.** Almost every example in the README, the docstrings, and the
samples targets `gpt-4.1` or `gpt-4o` or `gpt-5.2`. The Magentic-One paper's results and the Magentic-One default
prompts (`ORCHESTRATOR_TASK_LEDGER_FACTS_PROMPT` is described as "sensible for GPT-4o class models") are calibrated for
hosted frontier models. The framework supports Ollama as a local-first option, but the prompts themselves are not tuned
for smaller models. This is a hype-filter point: when Linus adopts the Magentic-One ledger pattern with local Workers
(Qwen3 baseline, smaller fine-tuned variants), the prompts likely need work — particularly the JSON- structured progress
ledger, where parse failures (`_max_json_retries = 10` in the orchestrator) are a known failure mode that gets worse as
model function-calling reliability degrades. Linus's Phase 1c worker-selection spike
([`phase1c-spike.md`](../specs/phase1c-spike.md)) is the right place to measure this gap before committing to the ledger
pattern.

**The pub/sub event-driven runtime is heavier than Linus needs in Phase 2a.** The `SingleThreadedAgentRuntime` is a
production-grade actor runtime with topic-based subscriptions, intervention handlers, message-handler context, and
serialization registries. For Linus's Phase 2a single-user single-machine use case, this is overkill — the simpler shape
is pydantic-ai's "single Agent class with synchronous tool dispatch" plus the Phase 3 spawner spec
([`phase3-spawner.md`](../specs/phase3-spawner.md)) for fan-out coordination. Adopting AutoGen's runtime would inflate
the Phase 2a complexity budget for capabilities (cross-process distribution, topic-based subscriptions) that Linus does
not need until Phase 5+ at the earliest. The pattern is worth knowing; the implementation is worth deferring.

**The Magentic-One agent stack (WebSurfer / FileSurfer / Coder / ComputerTerminal) is a productized specific-vertical,
not a generic primitive.** The Magentic-One paper's results come from the four-agent stack (Orchestrator + WebSurfer +
FileSurfer + Coder + ComputerTerminal); the `MagenticOne` class in `autogen-ext/teams/magentic_one.py` instantiates
exactly this stack. For Linus's domain (genomics, science, code) the surfer agents are not directly applicable — the
value is in the orchestrator pattern, not the four agents it coordinates. Adapting Magentic-One for Linus means: keep
the orchestrator + ledgers, replace WebSurfer / FileSurfer / Coder / ComputerTerminal with Linus-specific roles
(researcher / critic / writer / executor per DEC-0050). The Magentic-One blog post warns explicitly about
prompt-injection attacks via webpages and recommends Docker-isolated execution; that warning generalizes — any Linus
adoption of the orchestrator pattern needs sandbox enforcement at the executor level (SAFETY.md).

**The `autogen-magentic-one` legacy package is a transition shim.** The current Magentic-One implementation lives in
`autogen-ext/teams/magentic_one.py` plus `autogen-agentchat/teams/_group_chat/_magentic_one/`; the standalone
`autogen-magentic-one` package is a backward-compatibility shim from the v0.2 → v0.4 transition. Read the v0.4
implementation, not the legacy package.

**Function-calling reliability inherited from the Magentic-One ledger pattern.** The progress ledger's JSON-output shape
is the load-bearing dependency. The orchestrator retries up to `_max_json_retries = 10` times on parse failure; if all
10 fail, the orchestrator throws. For Linus's local Workers — Qwen3 baseline, smaller fine-tuned variants — the
function-calling reliability bar that the Magentic-One pattern requires is not necessarily met. This is the same
constraint the Letta repo-note ([`Letta.md`](Letta.md) §5) flags as inherited from MemGPT; AutoGen inherits it from the
same source (ChatCompletionClient tool-call mechanics). The Phase 1c worker-selection spike is the right place to
measure whether local Workers clear the bar.

## 6. Recommendation: **Study**

Read AutoGen as the canonical reference for **group-chat coordination patterns** and **the Magentic-One supervisor
ledger pattern**, then implement the relevant subset against Linus's pydantic-ai + fastmcp substrate. The specific files
worth reading are `autogen-agentchat/teams/_group_chat/_round_robin_group_chat.py` (the simplest scheduling primitive),
`autogen-agentchat/teams/_group_chat/_selector_group_chat.py` (the LLM-driven scheduler — read enough to understand the
`selector_prompt` template, the `allow_repeated_speaker` flag, and the `selector_func` / `candidate_func` escape
hatches), `autogen-agentchat/teams/_group_chat/_magentic_one/_magentic_one_orchestrator.py` and
`_magentic_one/_prompts.py` together (the supervisor pattern + the seven canonical prompts — the most directly
applicable file in the entire repo), `autogen-agentchat/agents/_assistant_agent.py` (the canonical tool-using agent with
streaming, parallel tool calls, structured output, MCP workbench), `autogen-ext/tools/mcp/_workbench.py` (the MCP
workbench shape for multi-server tool composition), and `autogen-agentchat/messages.py` (the typed message taxonomy).
Skim the `_swarm_group_chat.py` (handoff-driven coordination) and `_graph/_digraph_group_chat.py` (DAG-driven
coordination) for completeness; both are reference material for less-canonical patterns Linus may revisit in Phase 5+.
Read enough samples (`agentchat_dspy`, `core_async_human_in_the_loop`, `agentchat_fastapi`) to see the framework used
end-to-end.

The right time to revisit AutoGen is **Phase 3 spawner planning** — when the Linus Phase 3 spawner spec
([`phase3-spawner.md`](../specs/phase3-spawner.md)) graduates from design-intent stub to implementation spec, AutoGen's
group-chat manager taxonomy and the Magentic-One ledger prompts are the most useful prior art to crib from. Cluster
cell: [g11-agent-frameworks](../syntheses/repo-clusters/g11-agent-frameworks.md) (AutoGen sits alongside pydantic-ai,
dspy, gptme, superpowers, huginn, promptfoo, lmnr, and Agent-Skills-for-Context-Engineering as the agent-framework
reference set; AutoGen is uniquely the multi-agent supervisor reference — pydantic-ai is the Phase 2a single-agent
Integrate verdict, AutoGen is the Phase 3 multi-agent Study verdict).

Do **not** vendor AutoGen. Do **not** add `autogen-core` / `autogen-agentchat` / `autogen-ext` as dependencies of the
Phase 2a orchestration backend — pydantic-ai serves the single-agent role, and the Phase 3 spawner can crib the manager
taxonomy and the Magentic-One prompts without inheriting the runtime. Do **not** invest in tracking AutoGen's upstream —
it is in maintenance mode and the energy is at Microsoft Agent Framework. Do open a separate Watch entry for
`microsoft/agent-framework` when Phase 3 planning begins; the natural follow-up repo-note is "what changed in MAF that
the AutoGen patterns get superseded by." The cleanest Linus relationship to AutoGen is "read the v0.4 patterns, crib the
Magentic-One prompts with attribution, implement against pydantic-ai + fastmcp" — pattern lift, not code lift.

## 7. Questions for Dan

1. **Crib the Magentic-One seven-prompt orchestrator pattern as the Phase 3 supervisor manager?** AutoGen's
   `_magentic_one/_prompts.py` ships seven prompts (`ORCHESTRATOR_TASK_LEDGER_FACTS_PROMPT`,
   `ORCHESTRATOR_TASK_LEDGER_PLAN_PROMPT`, `ORCHESTRATOR_TASK_LEDGER_FULL_PROMPT`,
   `ORCHESTRATOR_PROGRESS_LEDGER_PROMPT`, `ORCHESTRATOR_TASK_LEDGER_FACTS_UPDATE_PROMPT`,
   `ORCHESTRATOR_TASK_LEDGER_PLAN_UPDATE_PROMPT`, `ORCHESTRATOR_FINAL_ANSWER_PROMPT`) plus the five-field progress
   ledger schema (`is_request_satisfied`, `is_in_loop`, `is_progress_being_made`, `next_speaker`,
   `instruction_or_question`, each as `{reason: str, answer: str|bool}`). The pattern is tuned for GPT-4-class models.
   Should the Phase 3 spawner spec adopt these prompts directly (with attribution), retune them for Qwen3 / smaller
   Workers, or re-derive a Linus-native shape? Tentative answer: crib the structure (the five-field progress ledger, the
   facts-update + plan-update stall-recovery mechanism, the `_n_stalls` / `max_stalls` shape), retune the prompts for
   local Workers as part of the Phase 1c spike, attribute Microsoft Research / Magentic-One in the prompt-file
   docstring.

2. **Manager taxonomy commitment for Phase 3.** Letta's repo-note Open Question 4 asked which subset of Letta's
   five-type vocabulary (round_robin, supervisor, dynamic, sleeptime, voice_sleeptime) Phase 3 should commit to; AutoGen
   now provides a parallel taxonomy (round_robin, selector, swarm, Magentic-One/supervisor, GraphFlow/DAG). Two
   reference taxonomies converge on the same shape: round-robin is the deterministic baseline, supervisor is the
   canonical centralized pattern, plus optional decentralized (swarm) and DAG (GraphFlow) variants. Should the Phase 3
   spawner spec commit to **round-robin + supervisor** as the v0 manager set (matching the Letta repo-note's tentative
   answer of `supervisor` + `dynamic`, where AutoGen's `selector` is the Letta-equivalent of `dynamic`), with `swarm`
   and `GraphFlow` deferred to Phase 5+? Worth a Phase 3 spawner-spec ADR.

3. **Component/ComponentModel declarative-configuration discipline as a Phase 2a convention?** Every AutoGen primitive
   ships a Pydantic config model and a `to_component_model()` / `from_component_model()` round-trip. Per DEC-0026
   (planning write-back cadence) and the consistency-across-PRs PR-summary discipline, this kind of uniform
   serializability would help Linus's audit-log + session-store work as well — every spawner invocation, every tool
   call, every Worker config could be serialized to JSON for replay or inspection. Should Phase 2a commit to "every
   Linus orchestration primitive ships a Pydantic config + round-trip" as a convention, or wait for a concrete need to
   drive the discipline? Tentative answer: yes, codify in CLAUDE.md alongside the existing "typed structured prediction
   wrapping free-text rationale" convention; the cost is one Pydantic model per primitive, the upside is uniform
   serializability for the audit log + the eventual openclaw visual builder (DEC-0008).

4. **Inter-agent message taxonomy — adopt the AutoGen 11-message catalog, the Letta three-tool catalog, or a
   Linus-native subset?** DEC-0051 commits Linus to `AgentReport` as the typed inter-agent message but does not
   enumerate the surrounding types. AutoGen ships 11 (TextMessage, MultiModalMessage, HandoffMessage, StopMessage,
   ToolCallRequestEvent, ToolCallExecutionEvent, ToolCallSummaryMessage, ThoughtEvent, ModelClientStreamingChunkEvent,
   MemoryQueryEvent, SelectSpeakerEvent); Letta ships three inter-agent tool verbs
   (`send_message_to_agent_and_wait_for_reply`, `send_message_to_agents_matching_tags`, `send_message_to_agent_async`)
   plus its memory-edit and archival tools. The two products solve the inter-agent message problem at different
   abstraction layers — AutoGen is event-typed, Letta is RPC-tool-shaped. Linus needs both layers (audit-record types +
   invocation-tool verbs). Tentative answer: a Linus-native subset that adopts `AgentReport` (DEC-0051) + AutoGen's
   `ToolCallRequestEvent` / `ToolCallExecutionEvent` / `ToolCallSummaryMessage` / `ThoughtEvent` / `SelectSpeakerEvent`
   (the audit-record types) + Letta's three inter-agent verbs (the invocation tools). Worth a Phase 3 spawner-spec ADR
   alongside DEC-0051.

5. **AutoGen vs Letta vs writing from scratch — when Phase 3 spawner planning starts, what is the right basis?** This
   repo-note plus the Letta repo-note ([`Letta.md`](Letta.md)) plus rig ([`rig.md`](rig.md)) all converge on the same
   recommendation: **read the patterns, do not vendor the framework**. The Phase 3 spawner spec is small (per the
   design-intent stub, it commits to `Role`, `AgentReport`, validation gate, critic policy, investigation memory) and
   the implementation is bounded — pydantic-ai for single-agent loops, a Linus-native group-chat manager set cribbing
   AutoGen's taxonomy and Magentic-One prompts, fastmcp for the tool surface. The framework dependencies that would
   replace this work (AutoGen, Letta, LangGraph) all bring extra surface — runtimes, agent stacks, memory commitments —
   that contradict DEC-0020 (bounded orchestration scope). Tentative answer: write Phase 3 from scratch against
   pydantic-ai + fastmcp + Linus-native primitives, with the AutoGen and Letta repo-notes as the design-vocabulary
   cribsheets. Worth committing to in the Phase 3 spawner-spec ADR.

6. **Microsoft Agent Framework as the natural successor watch-target.** AutoGen is in maintenance mode; MAF
   (`microsoft/agent-framework`) is the live successor. The natural follow-up to this repo-note is a separate
   `agent-framework.md` repo-note covering "what changed in MAF that supersedes the AutoGen patterns." Should that note
   land at Phase 3 planning time (once MAF's public API stabilizes) or at the same Tier 3 fan-out tier as this one?
   Tentative answer: Phase 3 planning time — MAF is too young to commit to a Linus stance now, and the AutoGen patterns
   are stable enough to drive Phase 3 design without it. Track MAF in
   [`docs/landscapes/total-landscape.md`](../landscapes/total-landscape.md) as a Watch-tier entry until then.

7. **The Magentic-One ledger pattern as the contrast case for debate-or-vote in the Phase 3 evaluation.** The
   [`g7-harnesses.md`](../syntheses/repo-clusters/g7-harnesses.md) synthesis frames `debate-or-vote` as the
   research-code reference for heuristic belief updates that avoid per-step LLM calls (the O(N²) → O(N) scalability
   lever). The Magentic-One progress ledger is the **opposite** pattern — every step costs one LLM call, and the
   pattern's quality scales with model capability rather than with N agents. The Phase 3 evaluation should explicitly
   contrast these two coordination strategies on Dan's task suite: does the Magentic-One ledger (per-step LLM call,
   GPT-4-class quality assumed) outperform a debate-or-vote heuristic (per-step heuristic update,
   Worker-quality-bounded) on the kinds of tasks Linus actually runs? Tentative answer: yes, this is the right Phase 3
   evaluation framing — Magentic-One as the "smart-coordinator" pole, debate-or-vote as the "heuristic-coordinator"
   pole, with Worker quality (Qwen3 vs smaller fine-tuned variants) as the orthogonal variable. Worth naming explicitly
   in the Phase 3 spawner spec.

8. **Society-of-Mind pattern as a Phase 5+ hierarchical-Maestro primitive.** AutoGen's `SocietyOfMindAgent` wraps an
   inner team as a single agent with the same chat interface — the natural primitive for "a Magentic-One-style Linus
   team is itself a tool the outer Maestro can call." This is the directly applicable shape for Phase 5+
   investigation-memory-aware sub-teams (DEC-0052) and for hierarchical Maestro/Worker composition where the Maestro
   task is itself decomposed into sub-Maestros. Should Phase 5+ planning include a "hierarchical composition primitive"
   line item, with `SocietyOfMindAgent` as the reference? Tentative answer: yes, light-touch — name the reference in the
   Phase 5 planning spec; defer the implementation until a concrete consumer materializes (Phase 7+ biology Workers
   running independent investigations is the leading candidate).
