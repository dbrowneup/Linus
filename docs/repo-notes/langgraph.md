# langgraph (`langchain-ai/langgraph`)

## 1. Purpose and scope

LangGraph is LangChain Inc.'s low-level orchestration framework for stateful, multi-actor LLM applications, marketed
under the tagline "Low-level orchestration framework for building stateful agents." Where LangChain proper is the
provider/integration layer (model clients, tool wrappers, retriever components) and LangSmith is the hosted
observability/evals platform, LangGraph is the runtime that sits between them: a **typed graph DAG with channel-based
state**, a **Pregel-inspired bulk-synchronous execution loop**, **first-class checkpointing** for durable execution and
human-in-the-loop interrupts, and a Python-native API where graph nodes are plain functions or runnables and edges are
either deterministic (`add_edge`) or conditional (`add_conditional_edges`). The framework is MIT-licensed
(`libs/langgraph/LICENSE`, LangChain Inc. 2024), Python ≥3.10, and currently at v1.2.0a7 in
`libs/langgraph/pyproject.toml` with several million weekly PyPI downloads — it has industry traction at the scale of
companies like Klarna, Replit, and Elastic per the README.

For Linus, LangGraph is the **architectural alternative to workgraph** for the Phase 2a session-store decision and the
**architectural cousin of pydantic-ai** for the Phase 2a Worker abstraction. Workgraph ([`workgraph.md`](workgraph.md))
is the recommended Phase 2a session-store shape per
[CLAUDE.md §Workgraph JSONL as the Phase 2a session-store shape](../../CLAUDE.md) — its `.workgraph/graph.jsonl`
append-only DAG plus `handler_for_model.rs` dispatch is the lightest-weight orchestration runtime in the cloned-repo
collection. LangGraph is the same architectural idea — a typed dependency graph executed by a runtime that handles
state, persistence, and resumption — built at a fundamentally different weight class: a Python framework with deep
LangChain ecosystem coupling (`langchain-core>=1.4.0a2` is a hard dependency in `libs/langgraph/pyproject.toml`), a
4,300-LoC Pregel runtime (`libs/langgraph/langgraph/pregel/main.py`), three checkpointer backends (in-memory, SQLite,
Postgres), and an SDK split into Python and JavaScript distributions. The trade-off captures the central Phase 2a
session-store decision concretely: workgraph is **cheaper, less coupled, more human-readable**; LangGraph is **richer,
more powerful, more opinionated about what an agent runtime ought to look like**. This repo-note exists to make that
trade-off legible and to flag specific LangGraph patterns (checkpoint/resume, channel-based state aggregation, the
`Send` map-reduce primitive, the `interrupt()` pause/resume semantics) worth lifting at scale even though the framework
itself is not the recommended Phase 2a substrate.

## 2. Architecture summary

The repository is a Python+TypeScript monorepo under `libs/`. The substantive Python packages are **`langgraph`** (the
core framework, ~10k+ LoC across `graph/`, `pregel/`, `channels/`, `pregel/_loop.py` at 1,867 LoC and `pregel/main.py`
at 4,314 LoC), **`langgraph-checkpoint`** (the base checkpointer interfaces, `BaseCheckpointSaver` + `Checkpoint` +
`CheckpointTuple` + `CheckpointMetadata`, plus an in-memory reference saver under `checkpoint/memory/__init__.py` at 704
LoC), **`langgraph-checkpoint-sqlite`** (645 LoC SQLite saver including its async sibling),
**`langgraph-checkpoint-postgres`** (595 LoC Postgres saver, the production-blessed path), the
**`langgraph-checkpoint-conformance`** test suite for verifying third-party checkpointers, **`langgraph-prebuilt`** (the
`create_react_agent` helper, the `ToolNode` tool-call dispatcher, the `tools_condition` edge predicate),
**`langgraph-cli`** (deployment and local-dev CLI), and **`langgraph-sdk-py`** (HTTP client for the LangGraph Server
hosted runtime). The **`sdk-js`** package is a parallel JavaScript SDK against the same server protocol; the JS runtime
equivalent ships separately at `langchain-ai/langgraphjs`. For Linus per DEC-0027 the JS surface is reference-only —
Python is the orchestration core.

The **load-bearing abstraction is `StateGraph`**, a builder class (`libs/langgraph/langgraph/graph/state.py`, 1,833
LoC). A user defines a typed state schema (a `TypedDict`, `@dataclass`, or Pydantic `BaseModel`) where each field is
optionally `Annotated[type, reducer]` — the reducer function `(Value, Update) -> Value` controls how parallel updates to
the same key are merged (LangGraph ships `add_messages` for conversation logs and `operator.add` for list concatenation
as the canonical reducers). The graph is then constructed by registering nodes (`add_node`) and edges (`add_edge`,
`add_conditional_edges`, `set_entry_point`, `set_finish_point`); a node is any callable with signature
`State -> Partial<State>` and an edge is either an unconditional successor or a callable that inspects the state and
returns the next node name(s). Calling `compile()` validates the graph (every source resolves to a real node, START is
reachable, etc.) and returns a `CompiledStateGraph` that subclasses `Pregel` and implements the LangChain `Runnable`
interface (so `.invoke()` / `.ainvoke()` / `.stream()` / `.astream()` are all available). The compile step also accepts
a `checkpointer` (the durability substrate), a `store` (long-term cross-thread memory), an optional `cache`, and
`interrupt_before` / `interrupt_after` lists that pause execution at named nodes for human review.

The **runtime is `Pregel`** (`libs/langgraph/langgraph/pregel/main.py`), a Python implementation of the bulk-synchronous
Pregel model that LangGraph credits to Google Research's 2010 Pregel paper plus Apache Beam (per the README
acknowledgements section). Execution proceeds in **supersteps**: at each step the loop identifies which nodes are ready
to run (their input channels have new values they have not yet seen — `versions_seen` in `CheckpointMetadata` tracks
this), executes them concurrently (sync via thread pool, async via asyncio), collects their writes, applies the channel
reducers to merge updates, then advances to the next superstep. The loop continues until no more nodes are ready or an
interrupt fires. The `_loop.py` (1,867 LoC) and `_runner.py` (940 LoC) modules implement the actual scheduler. The
advantage of the Pregel model is **deterministic concurrency** — within a superstep, parallel nodes cannot see each
other's writes, eliminating an entire class of race conditions that ad-hoc event-driven runtimes inherit.

**Channels** (`libs/langgraph/langgraph/channels/`) are the typed conduits that hold state between supersteps. The
channel taxonomy includes `LastValue` (default; the value is whatever the most recent writer set),
`BinaryOperatorAggregate` (combines updates with a user-supplied binary op — used for the `operator.add` reducer),
`EphemeralValue` (held for one superstep then cleared — used for graph inputs at START), `Topic` (a typed pub/sub
queue), `NamedBarrierValue` (waits for all named writers before releasing — used for `add_edge([a,b,c], d)` join
semantics), `LastValueAfterFinish` and `NamedBarrierValueAfterFinish` (post-execution variants), and `DeltaChannel`
(beta — emits change deltas rather than full values, with snapshot frequency tunable via
`LANGGRAPH_DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT`). Each channel is a small subclass of `BaseChannel` with `update` (merge
an incoming write), `checkpoint` (serialize for persistence), `from_checkpoint` (restore), and `get` (read current
value) methods. The channel abstraction is what makes the typed-reducer story tractable — the framework handles the
merge automatically given a small, declarative annotation on the state field.

The **checkpoint substrate** is a Pydantic-typed snapshot of the entire channel state at every superstep boundary. A
`Checkpoint` (TypedDict in `libs/checkpoint/langgraph/checkpoint/base/__init__.py`) carries `v` (format version,
currently `1`), `id` (monotonic UUID6 — sortable as time-ordered), `ts` (ISO 8601 timestamp), `channel_values`
(deserialized snapshot of every channel), `channel_versions` (per-channel monotonic version strings), `versions_seen`
(per-node-per-channel version map — drives the "what's ready" check), and `updated_channels`. The `CheckpointMetadata`
(TypedDict, `total=False`) captures `source` (`input` / `loop` / `update` / `fork`), `step`, `parents` (mapping
namespace→checkpoint_id, supporting subgraphs), `run_id`, plus the delta-channel snapshot counters. The
**`BaseCheckpointSaver` interface** is intentionally minimal: `get_tuple(config) -> CheckpointTuple | None` (load by
`thread_id` + optional `checkpoint_id`), `list(config, ...) -> Iterator[CheckpointTuple]` (history walk),
`put(config, checkpoint, metadata, new_versions) -> RunnableConfig` (write a new snapshot), `put_writes(...)` (record
pending intra-superstep writes for crash recovery), plus async siblings `aget_tuple` / `alist` / `aput` / `aput_writes`.
Three reference savers ship in the monorepo: `MemorySaver` (in-process, useful for tests), `SqliteSaver` (single-file
sqlite, "lightweight, synchronous use cases" per its docstring; `AsyncSqliteSaver` is the aiosqlite-backed sibling), and
`PostgresSaver` (production-grade with shallow-write and JSONB encoding variants).

The **`thread_id` / `checkpoint_ns` / `checkpoint_id` triple** is the addressing scheme. Every invocation of a compiled
graph carries a `RunnableConfig` whose `configurable.thread_id` identifies the conversation/session; `checkpoint_ns` is
the subgraph namespace (empty for the top-level graph); `checkpoint_id` is the per-superstep snapshot ID. This is the
same shape Letta's `agent_id` + memory_block addressing uses, but generalized to arbitrary state schemas rather than
memory-tier-specific blocks. A subgraph's checkpoints are scoped under its parent's namespace, so checkpoint walk-back
works hierarchically.

The **interrupt / resume model** is built on top of checkpointing (`libs/langgraph/langgraph/types.py:801` for
`interrupt()`, plus `Command` for resume). A node can call `interrupt(value)` to surface a value to the client and pause
execution; the value persists in the checkpoint as a pending write; a client resumes by invoking the graph again with
`Command(resume=<value>)` — execution restarts from the **start of the interrupted node** and replays any side-effects
up to the matching `interrupt()` call (so node implementations must be idempotent or guarded). Multiple `interrupt()`
calls in a single node are tracked positionally, with resume values matched in order. This is the canonical
human-in-the-loop primitive in the framework, and it is also how `interrupt_before` / `interrupt_after` (the breakpoint
mechanism passed to `compile()`) is implemented under the hood.

The **`Send` primitive** (`libs/langgraph/langgraph/types.py:654`) is the map-reduce / dynamic-fan-out shape. A
conditional edge can return a list of `Send(node_name, payload)` objects; the runtime then schedules `node_name` once
per Send with the per-Send payload as input, executes them concurrently within the next superstep, and aggregates their
outputs through the channel reducers. The Send payload can have a state schema different from the parent graph — useful
for "spawn N specialists, each with their own private context, then aggregate their results" patterns. This is the
LangGraph equivalent of a dynamic `add_node` in a graph that did not know its own shape at build time. **For Phase 3
spawner planning**, `Send` is the closest single API in the cloned-repo collection to what DEC-0050 / DEC-0051 are
reaching for.

The **`Command` primitive** generalizes Send: a node can return a
`Command(update=<state-update>, goto=<node>, graph=<None|PARENT>, resume=<value>)` to combine a state update, a
navigation hint, and an optional resume into one step. `Command.PARENT` lets a subgraph's node update its parent's state
directly — a hierarchical-agent primitive. This unifies edge logic and state mutation in a single typed return value.

The **`prebuilt` package** (`libs/prebuilt/langgraph/prebuilt/`) ships higher-level helpers: `create_react_agent` (an
out-of-the-box ReAct loop in `chat_agent_executor.py` — though the v1.0+ release deprecated it in favor of
`langchain.agents.create_agent`, with a deprecation warning), `ToolNode` (executes tool calls emitted by an LLM-bound
message), `tools_condition` (a conditional-edge predicate that routes to `ToolNode` if the last message contains tool
calls), `ValidationNode` (Pydantic-schema-validates tool arguments before dispatch), and `ToolCallTransformer`. The
dependency edges in the monorepo make this clear: `prebuilt` imports from `langgraph` + `checkpoint`, `langgraph`
imports from `checkpoint` + `prebuilt` (cyclic by design), and the `langgraph-cli` package depends on `sdk-py`. **MCP is
not first-class in `prebuilt`** — `tests/test_react_agent.py` shows MCP tools as a server-type literal
(`{"type": "mcp", "server_url": ...}`) but the actual MCP client adapter lives in the external `langchain-mcp-adapters`
PyPI package, not in the langgraph monorepo. This is a meaningful contrast with AutoGen ([`autogen.md`](autogen.md)),
where the `McpWorkbench` is shipped in `autogen-ext` as a native first-class abstraction.

Examples ship under `examples/` covering `multi_agent/` (`hierarchical_agent_teams.ipynb`,
`multi-agent-collaboration.ipynb`), `human_in_the_loop/`, `rag/`, `code_assistant/`, `customer-support/`,
`plan-and-execute/`, `lats/` (Language Agent Tree Search), `llm-compiler/`, `reflection/`, `reflexion/`, `rewoo/`,
`self-discover/`, `usaco/`, and `web-navigation/`. There is no canonical multi-agent supervisor primitive in `langgraph`
core — the supervisor pattern is built externally as a separate `langgraph-supervisor` PyPI package, and the swarm
pattern as `langgraph-swarm`; both layer on top of `StateGraph` rather than being shipped in the core repo. This is a
deliberate split: LangGraph core stays minimal, productized supervisor / swarm patterns live in extension packages.

## 3. What's reusable in Linus

LangGraph contributes architectural references for **durable execution**, **channel-based state aggregation**, and
**typed graph topology** — patterns Linus's Phase 2a + Phase 3 work will need at scale. The framework itself is not
vendored.

**Phase 2a — checkpoint/resume model as the reference for durable Worker execution (DEC-0028, DEC-0030).** The
`Checkpoint` + `BaseCheckpointSaver` + `thread_id` / `checkpoint_ns` / `checkpoint_id` triple is the most worked-out
durable-execution substrate in the cloned-repo collection. Where workgraph's `.workgraph/graph.jsonl` treats the entire
DAG as the unit of persistence (one append per task transition), LangGraph treats every **superstep** as a snapshot —
finer-grained, schema-validated, and crash-recoverable mid-run. For Phase 2a's single-machine personal-assistant scope,
workgraph's coarse-grained JSONL is the right starting point per CLAUDE.md's engineering convention. For Phase 3+, when
fan-out parallelism makes mid-run crashes more expensive and human-in-the-loop interrupts become a first-class need, the
LangGraph checkpoint shape is the right reference — particularly the `versions_seen` per-channel-per-node tracking,
which is exactly what a deterministic "what's ready to retry" check needs after a partial failure. The Phase 3 spawner
spec ([`phase3-spawner.md`](../specs/phase3-spawner.md)) does not yet name a checkpoint substrate; LangGraph's is the
working reference, with `SqliteSaver` (`libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/__init__.py`, 645 LoC) as the
directly-readable implementation that maps naturally onto the Linus Layer C SQLite + content-hash + git commitment
(DEC-0029). The shape worth lifting: `(thread_id, checkpoint_ns, checkpoint_id)` as the addressing triple,
monotonic-UUID6 IDs as the sortable ordering primitive, `metadata.source` as the four-valued classifier (`input` /
`loop` / `update` / `fork`) for what kind of checkpoint this is. Linus's audit log already wants these fields; LangGraph
names them.

**Phase 3 — channel-based state aggregation as the reference for parallel-Worker write coordination (DEC-0022).**
Linus's parallel-Worker write coordination
([`docs/adr/0022-parallel-worker-write-coordination.md`](../adr/0022-parallel-worker-write-coordination.md)) is
precisely the problem channels solve: when N Workers fan out and write back, what gets merged and how? LangGraph's
answer — annotate each state field with a `(value, reducer)` pair, let the runtime apply the reducer at superstep
boundaries — is cleaner than ad-hoc merge logic and cleaner than workgraph's "last-write-wins on the JSONL append." The
specific channels worth lifting as design references are `LastValue` (default, the most-recent-writer wins — maps onto
the Linus AgentReport `result` field), `BinaryOperatorAggregate` (commutative+associative merge — maps onto evidence
accumulation, list concatenation, score aggregation), `Topic` (typed pub/sub queue — relevant if Phase 3 ever adopts
message-passing between Workers), and `NamedBarrierValue` (wait for all named writers before release — the natural
primitive for "wait for all 3 critic Workers before computing the verdict"). The LangGraph implementation is small —
`libs/langgraph/langgraph/channels/base.py` is the 60-LoC abstract base; each concrete channel (`last_value.py`,
`binop.py`, `named_barrier_value.py`) is similar size. A Phase 3 Linus reimplementation in ~200 LoC of Python under
`src/linus/orchestration/channels.py` is achievable; the conceptual pattern is the contribution.

**Phase 3 — `Send` primitive as the reference for dynamic Worker fan-out (DEC-0050, DEC-0051).** LangGraph's `Send`
class (`libs/langgraph/langgraph/types.py:654`) is the directly-applicable shape for `linus.agent.spawn(spec, roles)`
per the Phase 3 spawner spec. A Send is `(node_name, payload, optional timeout)`; a list of Sends scheduled in one
superstep dispatches N parallel Worker invocations with per-Worker payloads, and the channel reducers handle result
aggregation. The Linus Phase 3 spawner can model role-dispatch as `Send(role.role_id, AgentReport_input)` and the
validation-gate aggregator as a barrier channel that waits for all critic Workers to return. The Send API is more
general than this — payloads can have a different schema than the parent graph state, supporting the "each specialist
gets a private context" pattern that DEC-0052 (investigation memory) needs. This pattern is more expressive than
workgraph's static DAG (where node count is known at task-graph-write-time, not runtime), and is the right reference for
the Phase 3 dynamic-spawn shape.

**Phase 3+ — `interrupt()` / `Command(resume=...)` as the canonical human-in-the-loop primitive (SAFETY.md).** The
LangGraph `interrupt(value)` → checkpoint-and-pause → `Command(resume=value)` → restart-from-node-start pattern is the
cleanest worked-out human-in-the-loop substrate in any framework Linus has surveyed. Letta's interrupt model (per the
Letta paper-note) is more memory-architecture-flavored; AutoGen has nothing comparable in core. For SAFETY.md's
autonomy-tier graduation — where higher-tier operations should pause for Dan's confirmation — the LangGraph shape is the
natural reference: a node calls `interrupt(<requested-action-description>)`, the orchestration layer surfaces it via the
harness (Claude Code, openclaw, future native UI), Dan responds, the graph resumes. Worth lifting at Phase 3+ when
sandbox graduation begins; for Phase 2a, the simpler "block on prompt" flow Claude Code already uses is sufficient. The
implementation gotcha worth noting: nodes must be idempotent on resume because LangGraph re-executes from the start of
the interrupted node, replaying any side-effects up to the matching `interrupt()` call. This is the same idempotency
discipline workgraph's heart-beat / re-spawn loop requires.

**Phase 5+ — typed graph topology as a reference for visual orchestration (DEC-0008 openclaw).** The `StateGraph`
builder API plus `compile()` produces a graph that is itself introspectable (`compiled.get_graph().draw_mermaid()`),
serializable, and visualizable in LangSmith Studio. For Phase 5+ when openclaw is in scope as the native visual
front-end, LangGraph's "graph as data" discipline is the directly applicable reference: nodes carry name + spec +
retry/timeout/cache policy, edges carry source + target + optional condition, the whole topology is one Pydantic-shaped
artifact. Linus does not need a visual builder in Phase 2 — Maestro/Worker work fine in text — but the discipline of
"every orchestration primitive is serializable to JSON for replay, debugging, and visualization" is worth committing to
early. AutoGen's Component/ComponentModel pattern ([`autogen.md`](autogen.md) §3) and Letta's `.af` Agent File format
([`Letta.md`](Letta.md) §3) are the parallel references; LangGraph's StateGraph is the third. All three converge.

**Phase 2a — `langgraph-checkpoint-conformance` as a test-suite template for Linus's session-store substrate.**
LangGraph ships a separate package, `langgraph-checkpoint-conformance`, that any third-party checkpointer implementation
can run to verify protocol conformance. The pattern — define an interface, ship a conformance test suite alongside it —
is one Linus's Phase 2a session-store work should adopt: define `LinusSessionStore` (or whatever the workgraph-shape
Phase 2a port is named), ship `linus-session-store-conformance` tests, run those tests against any concrete
implementation (JSONL-on-disk, SQLite, future Postgres). This is engineering hygiene that pays dividends when the
substrate evolves; LangGraph models it well.

**Phase 6+ — Pregel bulk-synchronous execution as a reference for deterministic agent concurrency.** LangGraph's core
insight — that **deterministic supersteps eliminate races between parallel nodes** — is the right discipline for any
future Linus Worker pool that runs N agents in parallel. Within a superstep, node A cannot see node B's writes; all
writes are merged at the boundary; this makes a parallel run deterministically replayable from the checkpoint.
workgraph's `.workgraph/graph.jsonl` does not enforce this discipline (the JSONL append order is the ground truth, races
are possible if two agents claim the same task within the heartbeat window); AutoGen's `SingleThreadedAgentRuntime`
enforces it via single-threaded sequential dispatch (no actual parallelism); only LangGraph's Pregel runtime gives you
both real concurrency and replay determinism in one package. For Phase 2a the simpler shapes are sufficient; for Phase
6+ when parallel-Worker quality starts to matter, the Pregel discipline is the reference.

## 4. What's inspiration only

The **full LangChain ecosystem dependency** — `langchain-core>=1.4.0a2,<2` is a hard `pyproject.toml` dependency, and
adopting LangGraph means adopting the full LangChain `Runnable` / `LCEL` (LangChain Expression Language) /
`BaseChatModel` / `BaseTool` typing surface — is the largest single reason LangGraph is **inspiration only** for Linus.
CLAUDE.md commits to pydantic-ai as the orchestration primitive (g11 cluster Integrate verdict); pydantic-ai is the
explicit anti-LangChain alternative, designed to give type safety and provider abstraction without the LangChain
framework surface. Layering LangGraph on top of pydantic-ai is contradictory — they are competing orchestration layers.
The LangGraph patterns worth lifting (checkpointing, channels, Send, interrupt) are implementable in ~500-1000 LoC of
Python against pydantic-ai's existing primitives without inheriting LangChain.

**LangSmith / LangGraph Cloud / LangGraph Studio** are LangChain Inc.'s commercial layer — observability + hosted
deployment + visual debugging — and the README explicitly markets the framework as a substrate for them. For Linus per
DEC-0017 (harness plurality) and DEC-0020 (bounded orchestration scope), the orchestration backend is local; a LangSmith
adoption would route every LLM call to LangChain Inc.'s hosted observability, which is contrary to Linus's privacy
posture. The g11 cluster Integrate verdict for observability is **lmnr** (OpenTelemetry-based, SQL-queryable,
self-hosted) — Linus does not need LangSmith, and the LangSmith-shaped patterns are not worth porting.

**The supervisor and swarm extension packages** (`langgraph-supervisor`, `langgraph-swarm`) — referenced in the
multi_agent examples but shipped as separate PyPI packages — are the LangGraph community's productized multi-agent
patterns. They are reference material on par with AutoGen's `SelectorGroupChatManager` and `SwarmGroupChatManager`
([`autogen.md`](autogen.md) §2), but the implementations are LangGraph-specific (StateGraph + Command-based handoff) so
the lift cost is non-trivial. For Phase 3 spawner planning, AutoGen's Magentic-One ledger pattern is the more directly
liftable supervisor reference — its prompts are framework-agnostic, where LangGraph's supervisor implementation is
tightly coupled to its Command/handoff plumbing.

The **`create_react_agent` deprecation in v1.0+** (the function now emits a `LangGraphDeprecatedSinceV10` warning
pointing to `langchain.agents.create_agent`) is a useful data point about LangChain Inc.'s release cadence: the v1.0 →
v2.0 transition is reorganizing the high-level helpers between LangChain and LangGraph, with prebuilt agents moving back
into LangChain proper. The lesson for Linus is that LangGraph's high-level helpers are a moving target even when the
low-level StateGraph + Pregel substrate is stable. Lift the patterns from the low-level substrate; do not chase the
prebuilt-helper API.

The **JavaScript SDK + `langgraphjs`** parallel runtime is a useful design point about cross-language agent
orchestration — LangChain Inc. ships Python and JS as parallel first-class implementations, talking to the same
LangGraph Server protocol over HTTP. For Linus per DEC-0027 (Python core, Rust where it fits, JS only at front-end
layer) this is reference-only. The HTTP-protocol-as-cross-language-substrate choice is a useful confirming signal for
any Phase 5+ openclaw work that needs to call a Python Linus orchestration backend from a JS/TS UI.

The **`DeltaChannel` (beta)** — emit incremental change deltas rather than full snapshots, with a tunable snapshot
frequency to cap reconstruction cost — is interesting prior art for any Linus future work on **memory diff
compression**. The pattern is relevant if Layer C episodic memory ever adopts a delta-encoded log shape (rather than
full-snapshot-per-session), but the design space is complex (snapshot frequency vs. reconstruction cost trade-off, the
`LANGGRAPH_DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT` bound) and Phase 2 does not need it. Watch.

## 5. What's incompatible or out of scope

**The LangChain ecosystem coupling is the architectural mismatch with Linus.** LangGraph cannot be adopted as a runtime
dependency in the Phase 2a orchestration backend because Linus has already committed to pydantic-ai as the orchestration
primitive (g11 Integrate verdict) and pydantic-ai is the explicit alternative to LangChain. The specific
incompatibilities: (1) LangGraph's `Runnable` interface is from `langchain_core.runnables`; pydantic-ai does not
implement Runnable. (2) LangGraph's `BaseChatModel` is from `langchain_core.language_models`; pydantic-ai has its own
provider abstraction. (3) LangGraph nodes return state-update dicts or `Command` objects; pydantic-ai agents return
Pydantic-validated outputs. Bridging these surfaces is possible but the bridge layer would be ~300+ LoC of adapter code
that exists only to reconcile two competing typing systems. The cheaper path is to lift LangGraph's patterns
(checkpointing, channels, Send, interrupt) into Linus-native code on pydantic-ai + fastmcp, paying the lift cost once.

**workgraph is the lighter-weight Phase 2a substrate.** Per CLAUDE.md's engineering convention, the recommended Phase 2a
session-store is workgraph's `.workgraph/graph.jsonl` append-only DAG plus the `handler_for_model.rs` dispatch pattern
(ported to Python). The contrast with LangGraph is concrete: workgraph's session store is one JSONL file,
human-readable, git-diffable, append-only, with zero dependencies beyond the file system; LangGraph's checkpoint
substrate requires a SQLite or Postgres backend, schema migrations
(`libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/utils.py` ships the migration logic), and a 600-LoC `SqliteSaver`
implementation that handles JSON serialization, version tracking, and async operations. For a single-user personal
assistant, the workgraph weight is right; LangGraph's weight is calibrated for multi-user production deployments at
companies like Klarna and Replit. The Phase 2a Linus session store should not adopt LangGraph's checkpointer; it should
adopt workgraph's JSONL shape with the option to migrate to a LangGraph-style SQLite checkpointer at Phase 3+ if the
Worker fan-out scale demands finer-grained snapshots.

**LangGraph's MCP integration is not first-class in core.** Unlike AutoGen's `McpWorkbench`
(`autogen-ext/tools/mcp/_workbench.py`), Letta's `mcp_manager` (`letta/services/mcp_manager.py`), or pydantic-ai's
native FastMCP composition, LangGraph delegates MCP to the external `langchain-mcp-adapters` PyPI package. The
`langgraph-prebuilt` test suite (`tests/test_react_agent.py:315`) treats MCP as a server-type literal in `bind_tools`,
but the actual adapter lives outside the monorepo. For Linus per DEC-0045 (FastMCP as default MCP framework) and
DEC-0018 (MCP as the tool-extensibility substrate), this is a meaningful gap — the Linus tool registry needs MCP to be
first-class, and LangGraph would require an extra adapter package on top of its existing dependency surface.

**The Pregel runtime is heavier than Phase 2a needs.** The `pregel/main.py` (4,314 LoC) + `pregel/_loop.py` (1,867
LoC) + `pregel/_runner.py` (940 LoC) implementation is a production-grade bulk-synchronous scheduler with async/sync
execution paths, retry policies, timeout policies, cache policies, error handlers, stream transformers, and a debug
surface. For Linus's Phase 2a single-Worker use case, this is overkill — pydantic-ai's single-Agent dispatch plus a
workgraph-style JSONL session store is the right weight. Adopting LangGraph's runtime would inflate the Phase 2a
complexity budget for capabilities Linus does not need (cross-graph subgraph composition, async + sync simultaneous
execution, runtime-tuned cache policies). Defer the Pregel-shape substrate to Phase 3+ when parallel-Worker fan-out +
checkpoint-recovery + human-in-the-loop interrupts all become first-class needs simultaneously.

**Apple Silicon / MLX / pmetal model providers are absent.** LangGraph delegates model providers to LangChain proper,
which ships providers for OpenAI, Anthropic, Azure, Ollama, llama-cpp, Hugging Face, and others — but not MLX,
MLX-Flash, or pmetal-serve. This is the same gap AutoGen, Letta, and rig all have, with the same workaround: point an
OpenAI-compatible client at Linus's orchestration backend per DEC-0005, which itself proxies to Ollama / MLX-Flash /
pmetal. The framework is portable; the providers it ships with are not Apple-Silicon-aware in any deep way.

**`langgraph-checkpoint-postgres` as the production-blessed default is the wrong shape for Linus.** LangChain Inc.'s
production guidance (per the README, the LangGraph Cloud documentation, and the `compose.yaml` in the repo) is
Postgres + the `pgvector` extension as the production substrate — the same shape Letta uses ([`Letta.md`](Letta.md) §2).
For a personal-assistant single-machine deployment, this is a dependency Linus does not want to manage. SQLite
(`SqliteSaver`) is the right weight, but LangChain Inc. flags it as "lightweight, synchronous use cases (demos and small
projects)" in the docstring — i.e., not the recommended production path. For Linus the SQLite path is fine, but the
framing in LangGraph's own documentation suggests the framework is optimized for the wrong end of the deployment scale.

## 6. Recommendation: **Study**

Read LangGraph as the canonical reference for **typed graph DAG state aggregation**, **checkpoint/resume durable
execution**, the **Send map-reduce primitive**, and the **interrupt/resume human-in-the-loop substrate** — then
implement the relevant patterns against Linus's pydantic-ai + fastmcp + workgraph-shape substrate. The specific files
worth reading are:

- `libs/langgraph/langgraph/graph/state.py` (1,833 LoC, the StateGraph builder — read enough to understand `add_node`,
  `add_edge`, `add_conditional_edges`, `compile` with checkpointer and interrupt args; the rest is overload-validation
  noise).
- `libs/langgraph/langgraph/types.py` (the `Send`, `Command`, `interrupt` primitives — these are the load-bearing API
  surface).
- `libs/langgraph/langgraph/channels/base.py` + `channels/last_value.py` + `channels/binop.py` +
  `channels/named_barrier_value.py` (the channel implementations — small, readable, directly liftable).
- `libs/checkpoint/langgraph/checkpoint/base/__init__.py` (the `BaseCheckpointSaver` interface, `Checkpoint` +
  `CheckpointTuple` + `CheckpointMetadata` schemas — the working reference for any future Linus durable-execution
  substrate).
- `libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/__init__.py` (the SQLite saver — the directly-readable
  implementation to crib for a Linus Layer C migration when JSONL becomes insufficient).
- `examples/multi_agent/hierarchical_agent_teams.ipynb` and `examples/human_in_the_loop/` (worked examples of the
  `Send` + `interrupt` patterns in real multi-agent code).

Skip `pregel/main.py` on first read — it's 4,314 LoC of scheduler internals; the StateGraph + types surface gives the
conceptual story without it.

The right time to revisit LangGraph is **Phase 3 spawner planning** — when the Linus Phase 3 spawner spec
([`phase3-spawner.md`](../specs/phase3-spawner.md)) graduates from design-intent stub to implementation spec,
LangGraph's `Send` / `Command` / channel-reducer / interrupt patterns are the most directly applicable prior art for the
spawner's parallel-Worker write coordination (DEC-0022) and validation-gate (S15) primitives. At that point, the
LangGraph patterns translate into ~500-1000 LoC of Python under `src/linus/orchestration/` — specifically a `Channel`
base class plus 4 concrete channel implementations (`LastValue`, `BinaryOperatorAggregate`, `NamedBarrierValue`,
`Topic`), a `Send` + `Command` typed return value for Worker results, and a checkpoint-tuple-shaped audit log entry —
without inheriting LangChain. Cluster cell: [g11-agent-frameworks](../syntheses/repo-clusters/g11-agent-frameworks.md)
(LangGraph sits alongside pydantic-ai as the agent-framework Integrate verdict for Phase 2a, AutoGen as the multi-agent
Study verdict for Phase 3, DSPy as the prompt-optimizer Study verdict for Phase 6, and gptme/superpowers as the
discipline-layer references — LangGraph is uniquely the **durable-execution + typed-channel-aggregation** reference,
with no direct competitor in the cluster).

Do **not** vendor LangGraph. Do **not** add `langgraph` / `langgraph-checkpoint` / `langgraph-prebuilt` as dependencies
of the Phase 2a orchestration backend — pydantic-ai serves the single-agent role, workgraph-shape JSONL serves the
session-store role, and the Phase 3 spawner can crib LangGraph's patterns without inheriting LangChain. Do **not**
invest in a LangGraph-shaped checkpointer for Phase 2a — the workgraph JSONL shape is the recommended starting point per
CLAUDE.md, with an explicit option to migrate to a LangGraph-shaped SQLite checkpointer at Phase 3+ if the
parallel-Worker fan-out scale demands finer-grained snapshots. Do consider the **`langgraph-checkpoint-conformance`
test-suite pattern** as engineering hygiene worth lifting — define the Linus session-store interface and ship
conformance tests alongside it, so any future substrate (JSONL, SQLite, Postgres) can be verified without re-deriving
the contract.

The cleanest Linus relationship to LangGraph is "read the patterns, port the small surface (channels + Send +
interrupt + checkpoint metadata), implement against pydantic-ai + workgraph-shape JSONL" — pattern lift, not code lift,
and not framework adoption.

## 7. Questions for Dan

1. **workgraph JSONL vs LangGraph SQLite — when does the Phase 2a session store earn its complexity upgrade?** CLAUDE.md
   commits to workgraph-shape JSONL as the Phase 2a starting shape. LangGraph's SQLite checkpointer is the canonical
   next step up — schema-validated, version-tracked, async-capable, with `versions_seen` per-channel-per-node tracking
   that makes "what's ready to retry after a partial failure" deterministic. The open question is the migration trigger:
   does Phase 3 spawner fan-out (5-10 parallel Workers per investigation) already justify the upgrade, or does the
   complexity threshold land at Phase 5+ when human-in-the-loop interrupts and openclaw visual debugging both need
   finer-grained snapshots? Tentative answer: defer the SQLite upgrade until at least one of (a) parallel-Worker fan-out
   reaches >10 Workers per task, (b) mid-run crashes become a measured pain point in the dan_tasks suite, or (c)
   openclaw's visual replay surface needs per-superstep snapshots. Until then, JSONL plus a content-hash audit log is
   sufficient.

2. **Channel taxonomy commitment for Phase 3 spawner write coordination (DEC-0022).** LangGraph's channel taxonomy
   (`LastValue`, `BinaryOperatorAggregate`, `Topic`, `NamedBarrierValue`, plus the `LastValueAfterFinish` /
   `NamedBarrierValueAfterFinish` post-execution variants and the beta `DeltaChannel`) is the most worked-out
   typed-state-aggregation menu in the cloned-repo collection. The Phase 3 spawner spec
   ([`phase3-spawner.md`](../specs/phase3-spawner.md)) does not yet name a channel taxonomy. Should the spawner commit
   to **`LastValue` + `BinaryOperatorAggregate` + `NamedBarrierValue`** as the v0 channel set (covering the three
   natural Linus patterns: result-overwrite, evidence-accumulation, all-critics-must-vote-before-verdict), with `Topic`
   and the AfterFinish variants deferred to Phase 5+? Worth a Phase 3 spawner-spec ADR alongside DEC-0022.

3. **`Send` as the canonical Phase 3 fan-out primitive.** LangGraph's `Send(node_name, payload, optional timeout)` is
   the directly-applicable shape for `linus.agent.spawn(spec, roles)`. The pattern is more expressive than workgraph's
   static DAG (where node count is known at graph-write-time) and lighter-weight than AutoGen's `RoutedAgent` +
   topic-based subscription model. Should the Phase 3 spawner adopt `Send`-shaped invocation (typed payload, optional
   per-Worker timeout, deterministic concurrent dispatch) as its v0 fan-out API, or commit to a Linus-native shape that
   integrates more tightly with the `Role` + `AgentReport` vocabulary (DEC-0050, DEC-0051)? Tentative answer: adopt the
   Send shape verbatim but rename to `Spawn(role_id, payload, timeout)` and make `payload` typed as `AgentInput` (a
   Pydantic model that wraps the role's input schema). The API is identical; the type-naming aligns with the Linus
   vocabulary.

4. **Interrupt/resume substrate for Phase 3+ human-in-the-loop sandbox graduation (SAFETY.md).** LangGraph's
   `interrupt(value)` → checkpoint-and-pause → `Command(resume=value)` → restart-from-node-start pattern is the cleanest
   worked-out human-in-the-loop primitive. SAFETY.md's autonomy-tier graduation will eventually need a substrate where
   higher-tier operations pause for Dan's confirmation. Should Phase 3+ adopt the LangGraph pattern verbatim (call site
   `interrupt()`, idempotent re-execution on resume, checkpoint-backed durability), or build a simpler "block on prompt"
   flow first and earn the LangGraph pattern when it's needed? Tentative answer: simpler first (a synchronous "pause and
   ask" flow with no checkpoint backing) until either (a) parallel Workers all need to pause simultaneously and waiting
   becomes a coordination problem, or (b) long-running tasks make the no-checkpoint flow lose work on Maestro
   context-window resets. Then graduate to the LangGraph shape.

5. **Conformance-test-suite discipline for the Linus session-store substrate.** LangGraph ships a separate
   `langgraph-checkpoint-conformance` package that any third-party checkpointer can run to verify protocol conformance —
   engineering hygiene that pays dividends when the substrate evolves. Should Phase 2a's session-store work include a
   `linus-session-store-conformance` test suite as a peer artifact, so future substrate migrations (JSONL → SQLite →
   Postgres) can be verified mechanically? Tentative answer: yes, codify this as a Phase 2a deliverable — define the
   session-store interface in a Pydantic protocol, ship conformance tests alongside it, run them against the JSONL
   implementation. The ~200 LoC of test-suite code amortizes over any future substrate change.

6. **MCP integration delta — LangGraph relies on `langchain-mcp-adapters`, AutoGen ships `McpWorkbench` natively,
   pydantic-ai composes with FastMCP directly. Does this affect the Phase 2a substrate decision?** The three frameworks
   treat MCP very differently. pydantic-ai's native FastMCP composition (g11 Integrate verdict + DEC-0045) is the
   cleanest path; AutoGen's `McpWorkbench` is the most feature-rich (resources + prompts + sampling + roots +
   elicitation, per [`autogen.md`](autogen.md) §2); LangGraph delegates entirely to an external adapter. For Linus per
   DEC-0045 the answer is settled — pydantic-ai + FastMCP — but the LangGraph approach is a useful negative data point:
   a framework that intentionally delegates MCP to an external package makes adoption costlier than one that ships it
   natively. Worth confirming Phase 2a's MCP integration is built directly on FastMCP without a LangChain bridge layer,
   even when LangGraph patterns are lifted elsewhere.

7. **Pregel bulk-synchronous discipline as a Phase 6+ replay-determinism substrate.** LangGraph's core insight — that
   supersteps eliminate races between parallel nodes, making parallel runs deterministically replayable from the
   checkpoint — is the right discipline for any future Linus Worker pool that runs N agents in parallel and needs
   replay-from-checkpoint to work reliably. workgraph's JSONL append doesn't enforce this; AutoGen's
   `SingleThreadedAgentRuntime` enforces it via single-threaded sequential dispatch. For Phase 6+ when fine-tuned Worker
   quality starts to be benchmarked at scale (BootstrapFewShot-style with DSPy, the Phase 6 fine-tuning path), replay
   determinism on the dan_tasks suite is the natural validation substrate. Should the Phase 6 benchmark harness commit
   to bulk-synchronous discipline (every parallel-Worker test run is replayable bit-for-bit from a checkpoint) as a
   quality bar, or accept eventual-consistency-style flakiness as the trade-off for runtime simplicity? Tentative
   answer: yes, commit to determinism — the Pregel discipline is the right ground truth for evaluation, even if the
   Phase 2a runtime doesn't fully implement it. Worth naming explicitly when Phase 6 spec work begins.

8. **DeltaChannel as a Phase 7+ memory-diff-compression reference.** LangGraph's beta `DeltaChannel` — emit incremental
   change deltas rather than full snapshots, with tunable snapshot frequency
   (`LANGGRAPH_DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT`, default 5000) and explicit snapshot triggers — is interesting prior
   art for any future Linus Layer C work that wants to compress episodic-memory storage. The pattern: between full
   snapshots, store only deltas; cap the reconstruction cost by forcing periodic snapshots; tune the snapshot-frequency
   trade-off per channel. For Phase 2 the Layer C SQLite + content-hashes commitment (DEC-0029) is sufficient; for Phase
   7+ if episodic memory grows to GB-scale and storage starts to matter, DeltaChannel is the reference. Reference-only
   at this stage; flag in [`docs/specs/memory-architecture.md`](../specs/memory-architecture.md) as a Phase 7+
   optimization candidate.
