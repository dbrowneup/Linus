# swarms (`kyegomez/swarms`)

## 1. Purpose and scope

Swarms (kyegomez/swarms; Python; Apache-2.0; ~10k+ stars at clone time) bills itself as "The Enterprise-Grade
Production-Ready Multi-Agent Orchestration Framework" — a Python framework providing a comprehensive suite of
pre-built multi-agent architectures (sequential, concurrent, hierarchical, group-chat, council, debate, majority-voting,
mixture-of-agents, planner-worker, round-robin, heavy-swarm, auto-swarm-builder) wrapped around a single `Agent`
primitive that composes an LLM + tools + memory. The framework targets backward compatibility with leading agent
frameworks and interoperability with protocols including MCP, x402, skills, and broader OpenAI-compatible stacks.

The repo carries an installed CLAUDE.md teaching guide (~1500 lines) that is unusually thorough for an open-source
agent framework — it documents the full constructor parameter surface for `Agent`, all 17 `swarm_type` values for
`SwarmRouter`, memory and persistence semantics (`persistent_memory`, `context_compression`, `Conversation.compact()`),
tool integration (Python functions, Pydantic schemas, MCP), streaming patterns (sync stdout, async, callback), and a
"choosing the right structure" decision table mapping situations to swarm types. Multiple structure classes
(`SequentialWorkflow`, `ConcurrentWorkflow`, `AgentRearrange`, `GraphWorkflow`, `MixtureOfAgents`, `HierarchicalSwarm`,
`GroupChat`, `MajorityVoting`, `CouncilAsAJudge`, `DebateWithJudge`, `HeavySwarm`, `RoundRobinSwarm`,
`PlannerWorkerSwarm`, `AutoSwarmBuilder`) all derive from the same base `Agent` primitive.

The framework runs on LiteLLM as the underlying LLM client, supporting OpenAI, Anthropic, Groq, Google, and
Ollama-compatible endpoints. MCP integration is first-class (`mcp_url` / `mcp_urls` parameters on `Agent`).

## 2. Architecture summary

**Core primitive: `Agent`** (`swarms/structs/agent.py`). A single class that wraps:

- LLM (via LiteLLM, configured via `model_name` string)
- Tools (Python functions with docstrings, auto-converted to OpenAI function schemas)
- Memory (`MEMORY.md` file at `{workspace}/agents/{agent_name}/MEMORY.md`, with `persistent_memory=True` default;
  `context_compression=True` auto-summarizes at 90% of `context_length`)
- Loop control (`max_loops=1` default, or `"auto"` for plan→execute→reflect autonomous loop)
- Streaming (sync stdout via `streaming_on`, async via `arun_stream`, callback via `streaming_callback`)
- Audit (`autosave` snapshots state to disk after each run)

**Compositional layer.** All multi-agent structures wrap one or more `Agent` instances:

- **`SwarmRouter`** is the highest-level abstraction — pass a list of agents and `swarm_type`, it handles the rest.
  Supports 17 swarm types including `"auto"` that auto-selects.
- **`AgentRearrange`** uses a Flow-DSL — `A -> B -> C, D` means A then B then (C parallel D) — with `H` for
  human-in-the-loop steps. Lightweight scriptable composition.
- **`GraphWorkflow`** is full DAG execution with topological sort, per-node callbacks, and token streaming. Supports
  fan-out/fan-in patterns.
- **`MixtureOfAgents`** is workers + aggregator with multi-layer iteration.
- **`HierarchicalSwarm`** has a director agent that breaks tasks into subtasks and delegates to workers.
- **`GroupChat`** is round-table with speaker-selection functions (`round_robin_speaker`, `expertise_based`,
  `random_speaker`, `priority_speaker`).
- **`AutoSwarmBuilder`** auto-creates agents, assigns roles, runs the appropriate swarm.

**Memory and persistence semantics.** The `persistent_memory=True` default reads `MEMORY.md` as a system preamble on
startup and appends to it on each response. `context_compression=True` triggers a `ContextCompressor` that summarizes
and rewrites `MEMORY.md` when token usage crosses 90% of `context_length`. The `Conversation.compact()` manual call
collapses history to a single summary with a timestamped archive of the full log preserved.

**Tool integration.** Python functions with docstrings are auto-converted to OpenAI function schemas. Pydantic models
also supported. MCP tools loaded via `mcp_url` (single SSE endpoint) or `mcp_urls` (list).

**Async support.** `arun()` for non-streaming, `arun_stream()` for token-level async iteration. `asyncio.run()`
compatible.

## 3. What's reusable in Linus

**Pattern catalog for the Linus Phase 3 multi-agent spawner (DEC-0050).** Swarms ships a remarkable breadth of
multi-agent architectures — sequential, concurrent, hierarchical, group-chat, council, debate, majority-voting,
mixture-of-agents, planner-worker, round-robin, heavy-swarm, auto-swarm-builder. Each comes with its own decision
rubric ("when to use this structure"). For Linus's Phase 3 spawner spec
([`docs/specs/phase3-spawner.md`](../specs/phase3-spawner.md)), Swarms is the **most comprehensive pattern catalog** in
the cloned-repo collection. The Linus implementation does not need to vendor Swarms (the architectural choices differ —
workgraph JSONL session-store, fastmcp tool substrate, OpenAI-compat HTTP), but Swarms's pattern catalog is a useful
**design-vocabulary cross-reference**. The Phase 3 spawner spec should reference Swarms's pattern names where they map
cleanly onto Linus's choices.

**`AgentRearrange` Flow DSL as a pattern for Linus orchestration language.** The Flow DSL (`A -> B -> C, D` with `H`
for human-in-the-loop) is a clean, scriptable way to specify multi-agent execution graphs. Linus's Phase 3 spawner
could adopt the same DSL shape for orchestration scripts. The grammar is small (one operator each for sequential and
parallel; `H` for human-in-the-loop; arbitrary agent-name identifiers) and the parser is trivial.

**Memory tiering precedent.** The `persistent_memory` + `context_compression` + `Conversation.compact()` pattern is a
direct precedent for Linus's Layer B (within-session scratchpad) and Layer C (cross-session episodic) split per
DEC-0028. Swarms's pattern uses `MEMORY.md` as a single per-agent file with auto-rewriting on compression. Linus's
DEC-0029 commits to SQLite + content hashes + git; Swarms's pattern is the simpler precedent. The Swarms compression
heuristic (90% of `context_length`) is a usable default for Linus's DEC-0032 16K cap policy.

**Speaker-selection functions for the Phase 3 spawner.** Swarms's `GroupChat` ships four speaker-selection strategies
(`round_robin`, `expertise_based`, `random`, `priority`). For multi-agent investigation memory (Layer D, DEC-0052),
selection strategies matter — the Linus Phase 3 spawner could lift these directly. The implementations are small (each
is a one-function strategy).

**Tool-auto-schema-from-docstring pattern.** The `swarms.tools.pydantic_to_json.base_model_to_openai_function` pattern
plus auto-schema-from-Python-function-docstring is a clean implementation pattern. Linus's tool registry (per DEC-0046)
could adopt the same auto-schema approach for Python tools, reducing tool-registration boilerplate.

**Backward-compatibility-as-feature mindset.** Swarms advertises "backward compatibility with leading agent frameworks
and interoperability with protocols such as MCP, x402, skills." The mindset — never make agent-framework migration
painful — is the right one for an open-source orchestration framework that wants community adoption. The DEC-0005
OpenAI-compat ADR is the Linus-side equivalent commitment.

## 4. What's inspiration only

**Apache-2.0 license, but the codebase is large (61 files in `structs/`).** Linus's choice to keep the orchestration
layer small and Python-centric argues against vendoring Swarms wholesale. The pattern catalog is reusable as design
vocabulary; the implementation is too large to absorb. The Linus Phase 3 spawner should be implemented from scratch
following workgraph JSONL session-store + fastmcp tool patterns, with Swarms as design-vocabulary cross-reference.

**The `"auto"` swarm_type is opaque.** `AutoSwarmBuilder` and `SwarmRouter(swarm_type="auto")` are advertised as
auto-selecting the right structure, but the heuristics for "right structure" are not documented in detail. For Linus's
audit-log-first orchestration discipline (per DEC-0030 scratchpad-first-class-artifact), auto-selection without
auditable rationale is the wrong default. The Linus Phase 3 spawner should require explicit swarm-type selection with
audit-logged rationale, not auto-selection.

**HeavySwarm framing is aggressive marketing.** The `HeavySwarm` framing ("Intensive multi-loop analysis. Best for
research-grade analysis. Derive a novel approach to solving the alignment problem in AI.") is the kind of framing the
[`docs/syntheses/agentic-systems-synthesis.md`](../syntheses/agentic-systems-synthesis.md) Maestro-as-empirical-object
thread flags as **over-claiming**. Linus's documentation should not adopt this framing.

## 5. What's incompatible or out of scope

**LiteLLM-only LLM client.** Swarms is built on LiteLLM exclusively. Linus's Phase 1c worker-selection spike
([`docs/specs/phase1c-spike.md`](../specs/phase1c-spike.md)) probably wants Ollama-direct (the brew-managed Ollama
serve is a Linus convention per CLAUDE.md), not LiteLLM-wrapped Ollama. Vendoring Swarms would introduce a LiteLLM
dependency that conflicts with the existing Ollama-direct pattern.

**No native MCP server implementation.** Swarms's `mcp_url` parameter consumes MCP-server tools but does not implement
an MCP server itself. The Linus orchestration layer needs **both** sides — consuming external MCP tools (Swarms's
pattern is sufficient) and exposing Linus's internal tools via MCP (fastmcp is the Linus default per DEC-0045). Swarms
contributes to the consumer side only.

**Persistent memory model is per-agent, not cross-agent.** Swarms's `MEMORY.md` is keyed on `agent_name`, with no
default mechanism for memory sharing across agents in a swarm. The Linus Layer D investigation-memory model (DEC-0052)
is multi-agent shared state by design. Swarms's pattern doesn't compose.

**No first-class session-store / audit-log format.** Swarms's `autosave` saves agent state but doesn't define a
session-store format like workgraph JSONL. The Linus orchestration layer commits to workgraph JSONL as the Phase 2a
session-store shape (per CLAUDE.md "Workgraph JSONL as the Phase 2a session-store shape"). Swarms doesn't contribute
here.

**License-compatible but not architecturally aligned.** Apache-2.0 allows incorporation, but the LiteLLM dependency,
the 61-file `structs/` directory, the auto-selection heuristics, and the single-file-per-agent memory model all argue
against direct adoption.

## 6. Recommendation: **Study**

Swarms is a **design-vocabulary cross-reference** for the Phase 3 multi-agent spawner (DEC-0050) and for the broader
Linus orchestration layer. The 17-swarm-type catalog, the speaker-selection functions, the Flow DSL, and the
tool-auto-schema-from-docstring pattern are all worth lifting as design vocabulary. The implementation is too large
and too architecturally distant (LiteLLM-only, no native MCP server, per-agent memory) to vendor.

The contrast with the workgraph-as-session-store recommendation (per [`workgraph.md`](workgraph.md)) is instructive:
workgraph contributes the **infrastructure** (JSONL append-only DAG, handler dispatch, tree-kill pattern); Swarms
contributes the **design vocabulary** (swarm types, speaker selection, Flow DSL). Both are Study-level repos, both
inform the Phase 3 spawner spec, but neither is vendored.

## 7. Questions for Dan

1. **Adopt the 17-swarm-type catalog as Phase 3 spawner design vocabulary?** The Phase 3 spawner spec is currently
   thin. Lifting Swarms's pattern names (with attribution) as the design vocabulary would give the spec a quickly
   readable reference table without requiring re-derivation. Worth a spec update?

2. **AgentRearrange Flow DSL adoption?** The DSL is small enough to vendor (~50 LOC for the parser). For Phase 3
   spawner orchestration scripts (where Dan or a Maestro Worker specifies an execution graph), the DSL is more readable
   than a JSON or YAML config. Worth a Phase 3 spec decision?

3. **Speaker-selection functions for Layer D investigation memory.** Swarms's four speaker-selection strategies are
   each ~10-20 LOC. For multi-agent investigation memory (DEC-0052), the strategies are directly portable. Worth a
   Phase 3 spec inclusion?

4. **Tool-auto-schema-from-docstring as a Linus tool-registry convention.** Currently the Linus tool registry per
   DEC-0046 doesn't specify how Python tools are auto-converted to MCP schemas. Adopting the Swarms pattern (function
   docstring → OpenAI function schema) is a low-cost convention that reduces registration boilerplate. Worth a
   convention update?

5. **`context_compression` heuristic — 90% of context_length as the default trigger.** Linus's DEC-0032 commits to a
   16K in-context cap with audit-logged bypass. The Swarms 90%-of-context-length trigger is a usable v0 default for
   when overflow-to-Layer-C routing fires. Worth surfacing as a DEC-0032 implementation detail?
