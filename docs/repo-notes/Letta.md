# Letta (`letta-ai/letta`)

## 1. Purpose and scope

Letta is the productized descendant of MemGPT — the same UC Berkeley research line (Packer, Wooders, et al.) carried
forward into a venture-backed open-source company that ships a self-hostable agent server, a Python/TypeScript SDK, a
hosted control plane at `app.letta.com`, and an Apache-2.0 codebase covering the whole surface. Where the paired
paper-note ([`Letta-2310.08560.md`](../paper-notes/Letta-2310.08560.md)) covers the 2023 conceptual architecture
(virtual context management, hierarchical memory tiers, function-call memory API, self-directed control flow with
interrupts), this repo covers the 2024–2026 product evolution: explicit named **memory blocks** (`human`, `persona`,
arbitrary user-defined labels) instead of an opaque "working context" region, a **multi-agent server** with five manager
types (round-robin, supervisor, dynamic, sleeptime, voice-sleeptime), an **Agent File** (`.af`) serialization format
that exports an entire agent — memory blocks, message history, tool definitions, MCP server configs, group membership —
as a single portable artifact, a **git-backed memory repository** (added recently, optional per agent) that versions
block contents through real `git` operations, and a **first-class MCP integration** that lets any external fastmcp
server contribute tools to a Letta agent at runtime. The codebase is substantial (~536 Python files, ~138k LoC under
`letta/`), targets Python 3.11–3.13, depends on FastAPI + SQLAlchemy + Alembic + fastmcp + LlamaIndex, and ships a
`compose.yaml` that boots a three-service stack (`letta_server`, `letta_db` on `pgvector`, `letta_nginx`). For Linus,
this is the strongest single reference implementation for the Phase 2 Layer C substrate (DEC-0028, DEC-0029) and for the
Phase 3 multi-agent spawner (DEC-0050, DEC-0052) — it is also the closest existing example of how to ship the whole
memory pillar plus a multi-agent runtime as a single coherent product. It is not, however, a substrate Linus should
adopt: the storage commitments diverge from DEC-0029, and the scope is wider than what the Linus orchestration layer
needs to own.

## 2. Architecture summary

The deliverable is a Python package (`letta` on PyPI, version `0.16.7` at the time of cloning, named project in
`pyproject.toml` listing the project authors as "Letta Team") that exposes both a programmatic API and an HTTP server.
The directory layout under `letta/` is the most informative tour of the architecture: `agents/` (agent loop
implementations: `letta_agent.py`, `letta_agent_v2.py`, `letta_agent_v3.py`, plus voice and ephemeral variants —
multiple generations co-exist as the loop has evolved), `groups/` (the five multi-agent manager strategies as separate
modules: `round_robin_multi_agent.py`, `supervisor_multi_agent.py`, `dynamic_multi_agent.py`, plus four sleeptime
variants reflecting the fast-iteration cadence), `schemas/` (Pydantic models for `block.py`, `memory.py`,
`memory_repo.py`, `agent_file.py`, `group.py`, `mcp_server.py`, `message.py`, etc. — the canonical serialization
contract), `services/` (the manager classes that mediate between Pydantic schemas and SQLAlchemy ORM:
`block_manager.py`, `block_manager_git.py`, `agent_manager.py`, `mcp_manager.py`, `memory_repo/`, etc.), `server/` (a
FastAPI app under `rest_api/routers/v1/` with ~30 router modules including `agents.py`, `blocks.py`, `groups.py`,
`messages.py`, `mcp_servers.py`, `passages.py` for archival memory, `git_http.py` for memory-repo git smart HTTP), and
`functions/` (the agent-callable tool surface, with `function_sets/base.py` covering memory-edit tools, `multi_agent.py`
covering inter-agent communication, plus `files.py`, `voice.py`, `builtin.py`).

The memory model is the load-bearing piece. Memory in Letta decomposes into **three named tiers** that map onto MemGPT's
2023 architecture but with explicit, schema-validated abstractions:

- **Core memory** (the in-prompt working context). Implemented as a list of `Block` objects (`letta/schemas/block.py`,
  `BaseBlock`/`Block`/`FileBlock`), each with a `label` (e.g. `human`, `persona`), a `value` (the text content), a
  `limit` (default 100k chars per block via `CORE_MEMORY_BLOCK_CHAR_LIMIT`; 20k for `human`/`persona` per
  `CORE_MEMORY_HUMAN_CHAR_LIMIT` / `CORE_MEMORY_PERSONA_CHAR_LIMIT`), a `read_only` flag, an optional `description`
  (which the agent sees in the rendered prompt), and `metadata`. The `Memory` Pydantic model (`schemas/memory.py`)
  composes blocks plus optional `file_blocks` plus an `agent_type` for prompt-rendering variations and a `git_enabled`
  flag that switches in the git-memory rendering path. Agents edit core memory by calling tools — the
  `BASE_MEMORY_TOOLS` catalog in `letta/constants.py` includes `core_memory_append`, `core_memory_replace`,
  `memory_apply_patch`, plus the newer `BASE_MEMORY_TOOLS_V2` and `BASE_MEMORY_TOOLS_V3` adding `memory_replace`,
  `memory_insert`, `memory_rethink`, `memory_finish_edits`. The tool surface is small and explicit; the entire
  memory-edit verb set is ~10 tools.
- **Recall memory** (the durable conversation log). Backed by the `MessageManager` service over the `messages` SQL
  table; the agent recalls past messages via the `conversation_search` tool; the queue-manager-equivalent logic lives in
  the agent loop (`agents/letta_agent_v3.py`).
- **Archival memory** (the unbounded write-once-search-many store). Backed by the `passages` table plus an embedding
  index; the agent inserts and queries via tools; storage is `pgvector` in production (Postgres + the `pgvector`
  extension is a hard requirement of the default `compose.yaml`) or `sqlite-vec` via the `[sqlite]` optional dependency
  group (`aiosqlite>=0.21.0`, `sqlite-vec>=0.1.7a2`). The `[postgres]` optional install group is the production-blessed
  path.

The recently added **memory_repo** subsystem (`schemas/memory_repo.py`, `services/memory_repo/`,
`services/block_manager_git.py`, `server/rest_api/routers/v1/git_http.py`) is a per-agent git-backed memory repository
that stores block content as files on disk and versions edits as real git commits. The `MemoryCommit` Pydantic schema
captures `sha` / `parent_sha` / `message` / `author_type` (`agent` / `user` / `system`) / `author_id` / `timestamp` /
`files_changed` / `additions` / `deletions` — i.e., the full git provenance trail per memory edit. Clients can talk to
the repo via git smart HTTP (`git_http.py` router) for `git clone` / `git push` / `git pull` against an agent's memory.
This is the memory-as-version-control pattern, made first-class. The optional `git_enabled` flag on the `Memory` schema
is the toggle between the standard prompt rendering (block-by-block XML) and a git-aware rendering that prefixes block
labels with `system/`.

The **Agent File** format (`.af`, schema in `schemas/agent_file.py`) serializes an entire agent — the `AgentState`, all
blocks, the message history, the attached MCP servers, the tool registry, source documents, group membership — as a
single JSON-shaped artifact for portability. The `ImportResult` class handles re-keying on import, returning a
`id_mappings` dict so cross-references in the imported artifact are rewritten to fit the destination database. This is
the Letta-equivalent of an agent's portable savefile.

The **multi-agent server** is built around the `Group` schema (`schemas/group.py`) and the `ManagerType` enum
(`round_robin`, `supervisor`, `dynamic`, `sleeptime`, `voice_sleeptime`). Each manager type has a corresponding module
under `letta/groups/` implementing its dispatch policy. Inter-agent communication uses three tools registered through
`functions/function_sets/multi_agent.py`: `send_message_to_agent_and_wait_for_reply` (synchronous request/response),
`send_message_to_agents_matching_tags` (broadcast by tag predicate), and `send_message_to_agent_async`
(fire-and-forget). The supervisor and dynamic managers are the closest to a Linus Phase 3 spawner pattern; the sleeptime
managers (four versions reflect ongoing iteration) implement a "background reflection while the user is idle" pattern
reminiscent of generative-agents-style consolidation.

The **MCP integration** is mature. `mcp[cli]>=1.9.4` and `fastmcp>=2.12.5` are direct dependencies. The
`services/mcp_manager.py` and `services/mcp_server_manager.py` services orchestrate connection lifecycle to external MCP
servers (stdio, SSE, and streamable-HTTP transports are all supported per `MCPServerType` enum and the matching
`SSEServerConfig` / `StdioServerConfig` / `StreamableHTTPServerConfig` types). OAuth flows for MCP servers are handled
end-to-end (`MCPOAuth` ORM, `services/mcp/server_side_oauth.py`). The `/mcp-servers/` REST surface lets clients
register, update, list, and execute tools against external MCP servers per agent. The MCP-tool count exposed by Letta
itself for inter-agent and memory operations is on the order of ~12 — middle ground between mem0's minimal ~5 and
agentmemory's comprehensive 51 (see [agentmemory's competitor table](agentmemory.md) for the explicit accounting).

The **storage substrate** is Postgres-first by design. `compose.yaml` mounts `ankane/pgvector:v0.5.1` as the database,
and `init.sql` provisions the schema. The 167 Alembic migration files under `alembic/versions/` reflect the schema's
production maturity. The `[sqlite]` optional group works for local development (the `letta/server/db.py` registry
detects which backend is configured and routes accordingly), but the canonical deployment posture is "Postgres with
`pgvector`". The agent loop uses async SQLAlchemy throughout (`sqlalchemy[asyncio]>=2.0.41`).

The **API surface** ships both an OpenAI-compatible `/v1/chat/completions` endpoint and an Anthropic-compatible
`/v1/anthropic/...` endpoint (`server/rest_api/routers/v1/anthropic.py`). The native Letta API is the agent-stateful
path; the chat-completions endpoints are the stateless compatibility shims. Letta is fully model-agnostic: the
`letta/llm_api/` module wraps OpenAI, Anthropic, Google Gemini, Groq, Mistral, Azure, vLLM, OpenLLM, and Ollama (via
`OLLAMA_BASE_URL` env var). The README recommends Opus 4.5 / GPT-5.2; the CLI tool **Letta Code** is a separate
TypeScript package (`@letta-ai/letta-code`) that acts as a coding harness on top of the Letta agent server, not part of
this repo.

## 3. What's reusable in Linus

Architectural patterns map onto multiple Linus phases. The relevant DECs and specs are referenced inline; the canonical
home for the conceptual lineage is the paired paper-note ([`Letta-2310.08560.md`](../paper-notes/Letta-2310.08560.md)).

**Phase 2 — memory blocks as a reference design for the in-context working set (DEC-0028, DEC-0030, DEC-0032).** Letta's
`Block` schema (`label`, `value`, `limit`, `read_only`, `description`, `metadata`) is the productized realization of
MemGPT's "working context" region with explicit shape. Where MemGPT had a single opaque text region edited via
`working_context.append` / `working_context.replace`, Letta partitions the working set into named, typed blocks with
per-block character limits (default 100k; lower for `human`/`persona`), per-block read-only flags, and a `description`
field that tells the agent what the block is _for_. This is the more explicit version of what the DEC-0030 scratchpad
spec already commits to (named segments: `scratchpad`, `answer`, `tool_output`); Letta's contribution is the
**per-block-limit + per-block-readonly + agent-visible description** triple, which is worth lifting into the Phase 2
scratchpad schema. A Linus segment record with a `segment_label`, a `char_limit`, a `read_only` flag, and an
agent-visible `description` is a cleaner contract than a flat `segment` enum.

**Phase 2 — memory_repo as the closest existing match for DEC-0029's "git as persistence substrate underneath"
commitment.** DEC-0029 commits Linus to "SQLite + content hashes + git as persistence substrate"; the implementation
detail of how git enters the picture is left open in the spec. Letta's `memory_repo` subsystem is a working answer: each
agent's memory blocks are also files in a per-agent git repository, edits go through real `git` operations, the
`MemoryCommit` schema captures the full `sha` / `parent_sha` / author / timestamp / diff trail, and the optional
`git_enabled` rendering flag lets the agent see git-aware structure in its prompt. Linus should study this as the
canonical "memory edits as commits" reference; the `MemoryCommit` schema specifically maps onto the integrity
sub-requirement from Garrison's framework that DEC-0028 names. The divergence: Letta uses git commits as the canonical
representation of every edit, with SQLite as a derived index over the repo; Linus's DEC-0029 inverts this — SQLite is
the canonical store, git is the persistence-and-audit substrate underneath. Both shapes satisfy the integrity
sub-requirement; Letta's is heavier-weight (an entire git repo per agent) but more directly inspectable.

**Phase 2 — paged archival memory as the long-document interaction shape (DEC-0032, Phase 7 biology Workers).** Letta's
`passages` table + embedding index + tool-driven paged search is the productized form of MemGPT's archival storage. The
paged-search pattern (per the paper-note) is the recommended interaction shape for Linus's Phase 7 biology Workers
working over multi-page papers and book-length documents
([`biology-phase7-roadmap.md`](../specs/biology-phase7-roadmap.md)) — Letta is the reference implementation of that
pattern in Python with both Postgres and SQLite backends. The KnowledgeBase RAG pipeline is the substrate; Letta's
`passages` schema and the per-passage embedding index are a useful reference for how Layer E retrieval can surface the
"page through a corpus" verb to a Worker without overflowing the DEC-0032 in-context cap.

**Phase 3 — multi-agent groups as a reference for the agent-spawner manager taxonomy (DEC-0050, DEC-0052).** Letta's
five `ManagerType` strategies (round-robin, supervisor, dynamic, sleeptime, voice-sleeptime) are a worked taxonomy of
how a parent process schedules child agents. The Phase 3 spawner spec
([`phase3-spawner.md`](../specs/phase3-spawner.md)) is currently a stub committing to `Role` as a first-class type
(DEC-0050) and `AgentReport` as the typed inter-agent message (DEC-0051); Letta's manager taxonomy fills in the next
level of detail. Specifically: the **supervisor** manager (one parent fans out to N children, collects their replies,
synthesizes) is the closest existing template for the Linus Maestro/Worker pattern that DEC-0050/DEC-0051 codify; the
**dynamic** manager (the parent decides at runtime which child to dispatch to) is the analogue for the Phase 3
investigation-memory-aware spawner that DEC-0052 anticipates. The three inter-agent tools
(`send_message_to_agent_and_wait_for_reply`, `send_message_to_agents_matching_tags`, `send_message_to_agent_async`) are
the message-passing primitives a Linus spawner will need; the verb shape is directly portable.

**Phase 3 — Agent File (`.af`) format as a reference for the Linus agent serialization contract.** Linus's Phase 3 agent
spawner will need a serialization format for handing off task-scoped agent state across agents and across sessions.
Letta's Agent File format — a single JSON-shaped artifact bundling AgentState + blocks + message history + attached MCP
servers + tools + source documents + group membership, with re-keying on import via `ImportResult` — is the existing
reference for what that format should cover. The `ImportResult.id_mappings` discipline (every cross-reference gets
rewritten on import) is non-obvious but load-bearing; Linus's Phase 3 serialization should match it.

**Phase 3 — MCP server integration as a reference for the in-house Linus MCP shape (DEC-0018, DEC-0045).** Letta is a
direct user of `fastmcp` (DEC-0045: fastmcp is the default MCP framework) and supports all three transports (stdio, SSE,
streamable HTTP) plus OAuth. The `services/mcp_manager.py` + `services/mcp_server_manager.py` split (one manages
connection lifecycle, the other manages persistent server records) is a worked example of how a Linus MCP host should
factor its responsibilities. The OAuth flow handling (`MCPOAuth` ORM + `services/mcp/server_side_oauth.py`) is also the
existing reference for how a Linus MCP host should handle OAuth-protected external servers — relevant for Phase 5+ when
external API tools (DEC-0046) are tagged for production deployment.

**Phase 5+ — Anthropic-compatible HTTP surface as a confirming signal for revisiting DEC-0005.** Letta ships both an
OpenAI-compatible `/v1/chat/completions` and an Anthropic-compatible endpoint at `/v1/anthropic/...`. Together with
Kimi-K2's similar dual-surface choice (see [`Kimi-K2.md`](Kimi-K2.md) §3), this is a second confirming signal that
Anthropic-compatible HTTP is becoming a co-equal endpoint shape across modern open-source agent products. DEC-0005
commits Linus to OpenAI-compatible-only at v0; a future ADR ("Anthropic-compatible HTTP as a Phase 5+ Linus capability")
is the natural place to absorb the pattern.

**Phase 7+ — sleeptime managers as a reference for background consolidation (DEC-0029 + DEC-0048).** Letta's four
sleeptime manager variants (`sleeptime_multi_agent.py`, `sleeptime_multi_agent_v2/3/4.py`) implement the
"background-reflection-while-the-user-is-idle" pattern. The version-fanout suggests this is an active area of iteration
inside Letta itself, but the architectural shape — a separate manager class that runs consolidation between user turns —
is directly applicable to the Phase 7+ Linus consolidation pipeline that synthesizes episodic records into KnowledgeBase
entries (DEC-0048 model-prediction edges; the Layer C → Layer E graduation hinted at in the memory-architecture spec).

## 4. What's inspiration only

The **multi-tenancy and authentication machinery** in Letta — `OrganizationManager`, per-organization API key scoping,
the `routers/v1/users.py` and `routers/v1/organizations.py` REST surfaces, the JWT and API-key middleware — is built for
Letta the SaaS product. Linus is single-user (Dan); none of this applies. The user/organization Pydantic models are
useful only as a reference for how to scope queries by actor in SQLAlchemy filtered selects.

The **OpenTelemetry / Sentry / Datadog / ClickHouse instrumentation surface** under `letta/otel/`, `letta/monitoring/`,
and the `clickhouse_otel_traces.py` / `llm_trace_writer.py` services is the production-observability stack Letta-the-
service operates with. Linus's audit log will need observability eventually, but the canonical Linus posture is
single-user and local-first; adopting the full OTel exporter chain would be premature. The `LLMTrace` schema (per-call
request/response capture) is a useful reference for what a Linus per-Worker-call audit record should contain, though.

The **`compose.yaml` three-service stack** (Postgres + Letta server + nginx) is a deployment template for self-hosting
Letta at scale; the deployment-guide-as-content reference is useful for what a Linus equivalent should look like at
Phase 5+, but the substance — Postgres-with-pgvector, nginx as TLS terminator — is not directly reusable on the Linus
single-machine target.

The **`@letta-ai/letta-code` CLI tool** (separate repo, npm-installable as `@letta-ai/letta-code`) is Letta's
coding-harness front-end. Per CLAUDE.md's harness-vs-orchestration distinction (DEC-0020) and the harness-plurality note
(DEC-0017), Linus is the orchestration backend; coding harnesses (Cline, claw-code, Claude Code) are separate
front-ends. Letta Code is a useful comparison point for how a memory-aware coding harness can be built but is not part
of the Linus product surface.

The **agent-loop versioning** (`letta_agent.py`, `letta_agent_v2.py`, `letta_agent_v3.py` co-existing) and the
**sleeptime manager fanout** (v1 through v4) are a worked example of how an iteratively-evolving agent runtime maintains
backward compatibility — useful as a discipline reference for when Linus's own agent loop accumulates versioned variants
in Phase 4+, but not content to lift.

## 5. What's incompatible or out of scope

**The Postgres + pgvector default substrate diverges from DEC-0029.** Letta's production substrate is Postgres with the
`pgvector` extension, not SQLite + content hashes + git. The `[sqlite]` optional install group is supported, but the
canonical deployment is Postgres-first: the `compose.yaml` mounts `ankane/pgvector:v0.5.1` as the default database, the
167 Alembic migration files reflect the Postgres schema's production maturity, and the `[postgres]` optional install
group includes both `pgvector>=0.2.3` and three Postgres driver libraries. DEC-0029 explicitly chooses SQLite for the v0
substrate and chooses git as the persistence substrate underneath; Letta inverts the priority (Postgres canonical,
SQLite optional, git as a per-agent overlay). Adopting Letta as a substrate would require either accepting the Postgres
dependency or operating against the unsupported SQLite path; either choice contradicts DEC-0029.

**Docker-hosted Postgres is forbidden by the Linus hardware constraint.** CLAUDE.md's hardware constraints state "Docker
is for stateless services only" because the macOS VM does not pass through Metal or ANE. Postgres-in-Docker is
acceptable under that rule (Postgres is stateless from the GPU/ANE perspective; only the SQL-level state matters), but
it is heavier than DEC-0029's single-file SQLite at `~/.linus/episodic.db` and adds operational surface (the Postgres
container needs to be running for Linus memory to function). This is a difference in posture, not a hard incompatibility
— but it is exactly the kind of dependency DEC-0029's "single SQLite file" choice was designed to avoid.

**The OpenAI-/Anthropic-default LLM client coupling is a soft incompatibility with the local-first stance.** Letta's
agent loop is fully model-agnostic and supports Ollama via `OLLAMA_BASE_URL`, but the README leads with "we recommend
Opus 4.5 and GPT-5.2 for best performance" and the example code targets `model: "openai/gpt-5.2"`. The default-tooling
posture is hosted-model-first; the Ollama path works but is not the recommended deployment. For Linus's local-first
stance (DEC-0027 public APIs only, the Worker-orchestration pattern in CLAUDE.md), this is a posture mismatch — Letta is
built for hosted Claude / OpenAI as the agent's underlying model, with local models as an option; Linus is built for
local Workers as the default with hosted Claude as the Maestro upstream.

**The scope is broader than the Linus orchestration layer should own.** Letta is a self-hostable agent server +
multi-tenant SaaS + CLI coding harness + Python SDK + TypeScript SDK — a full product surface. Linus's orchestration
layer per ARCHITECTURE.md is intentionally narrower: a router + MCP tool registry + agent spawner + sandbox + session
store + audit log, with harnesses staying separate (DEC-0020 orchestration scope is bounded). Adopting Letta as the
Linus orchestration substrate would inflate the scope to match Letta's; that contradicts DEC-0020 explicitly.

**Function-calling reliability is a soft constraint inherited from MemGPT.** Per the paired paper-note's hype-filter
section, MemGPT's quality is bottlenecked by the underlying model's function-calling reliability — GPT-4 excellent,
GPT-3.5 brittle, even GPT-4 Turbo worse than GPT-4 on the nested-KV task. Letta inherits this bottleneck: the entire
memory-edit + multi-agent message-passing surface is tool-calls, and the surface only works as well as the underlying
Worker's function-calling does. Linus's planned local Workers (Qwen3, future fine-tuned bases) need to clear a
function-calling reliability bar before the Letta-style full pattern delivers comparable lift. The Phase 1c
worker-selection spike ([`phase1c-spike.md`](../specs/phase1c-spike.md)) is the right place to measure this.

**Letta Code (the CLI) targets coding-tasks, not the Linus Maestro/Worker workflow.** Letta Code is a coding harness
that competes with Claude Code, Cursor, Cline. It is conceptually orthogonal to Linus's Maestro/Worker discipline. Even
if Linus were to adopt Letta-the-server as its backend, Letta Code would be a separate front-end choice that does not
fit Linus's harness-plurality model (DEC-0017).

## 6. Recommendation: **Study**

Letta is the strongest single reference implementation for Linus's Phase 2 memory pillar (DEC-0028) and the closest
existing example of a productized multi-agent runtime (DEC-0050, DEC-0052). Read the relevant source modules deeply —
specifically `letta/schemas/{block,memory,memory_repo,agent_file,group}.py`,
`letta/services/{block_manager,block_manager_git,memory_repo,mcp_manager,mcp_server_manager}.py`, and the multi-agent
`manager` modules under `letta/groups/`. The `MemoryCommit` schema, the `Block` field set (`label` / `value` / `limit` /
`read_only` / `description` / `metadata`), the `ManagerType` taxonomy (`round_robin` / `supervisor` / `dynamic` /
`sleeptime` / `voice_sleeptime`), the three inter-agent tool verbs (`send_message_to_agent_and_wait_for_reply` /
`send_message_to_agents_matching_tags` / `send_message_to_agent_async`), the Agent File serialization shape with
`id_mappings` re-keying — all are directly applicable as design references for the corresponding Linus surfaces. Cluster
cell: [g4-memory](../syntheses/repo-clusters/g4-memory.md) (Letta belongs in the cross-session-episodic cluster
alongside agentmemory, anamnesis, openaugi, and engram).

Do **not** vendor Letta. Do **not** adopt it as the Linus orchestration substrate. The substrate divergence from
DEC-0029 (Postgres + pgvector canonical vs. SQLite + content hashes + git canonical) is real, and the scope divergence
from DEC-0020 (full multi-tenant SaaS server vs. bounded local orchestration layer) is also real. Both are alignment
issues, not bugs in either product — Letta is correctly designed for what it is, Linus is correctly scoped for what it
is. The right relationship is Linus borrows the design vocabulary (memory blocks, manager taxonomy, Agent File shape,
memory-as-commits) and ships its own implementation against the SQLite-and-git substrate DEC-0029 commits to.

The two specific exceptions where adopting actual Letta artifacts may be reasonable:

1. **The Agent File JSON schema** as a starting point for the Linus Phase 3 agent-serialization contract. The schema is
   well-thought-out and the `ImportResult.id_mappings` re-keying discipline is non-obvious; cribbing the shape and
   adapting to Linus's Pydantic models is faster than re-deriving it.
2. **The `MemoryCommit` Pydantic schema** as the Linus per-edit audit record under the `linus.memory.episodic.*`
   substrate. The fields (`sha` / `parent_sha` / `author_type` / `author_id` / `timestamp` / `files_changed` /
   `additions` / `deletions`) directly satisfy Garrison's integrity sub-requirement from DEC-0028 and are exactly what
   DEC-0029's audit record should contain.

Both are schema lifts, not code lifts. The Linus implementation against DEC-0029's substrate is a separate Phase 2a
deliverable.

## 7. Questions for Dan

1. **Memory-block schema lift for the Phase 2 scratchpad spec.** Letta's `Block` schema adds three fields beyond what
   DEC-0030's three-segment scratchpad currently specifies: a per-block `limit` (so an agent knows when it is
   approaching block capacity), a per-block `read_only` flag (so the agent can mark stable user preferences as
   immutable), and a per-block `description` (so the agent sees what the block is _for_ at prompt-render time). Should
   the Phase 2 scratchpad schema absorb these as named fields on the segment record, or stay with the flat `segment`
   enum until measurement shows the richer shape pays off? The richer shape is closer to DEC-0029's "addressability"
   sub-requirement; the flat shape is faster to ship.

2. **MCP surface scope for Layer C — what's the right pole on the minimal-to-comprehensive spectrum?** This question is
   open across three repo-notes now and deserves a single committed answer. agentmemory's competitor table (see
   [`agentmemory.md`](agentmemory.md) §7 Open Question 2) anchors the comparison: agentmemory exposes 51 memory tools,
   Letta exposes ~12 via inter-agent + memory-edit + archival surfaces, mem0 exposes ~5. Where should Linus's Phase 3
   memory MCP surface land? Tentative read: Letta's ~12-tool middle pole is the right shape — comprehensive enough to
   cover the read/write/search/edit/inter-agent verbs, restrained enough to be auditable. Worth committing to in a Phase
   3 spawner-spec ADR alongside DEC-0050.

3. **memory_repo as the canonical Phase 2 git-substrate pattern.** DEC-0029 commits to "git as persistence substrate
   underneath" SQLite but does not specify the implementation detail. Letta's `memory_repo` subsystem is one
   instantiation: a per-agent git repository where each block is a file, edits are commits, and the `MemoryCommit`
   schema captures provenance. Should Linus adopt this exact shape (per-agent or per-session git repo, blocks as files),
   or invert it (SQLite canonical, periodic git-commit of the SQLite file as the audit substrate)? The Letta shape is
   more inspectable but heavier; the inverse is lighter but loses the per-edit git diff. Tentative answer: the inverse,
   because SQLite-canonical is what DEC-0029 explicitly chooses; the per-edit diff trail can come from a separate
   audit-log JSON file under the same git substrate.

4. **Multi-agent manager taxonomy — should Phase 3 commit to the Letta five-type vocabulary, or a Linus-specific
   subset?** Letta's manager types (`round_robin`, `supervisor`, `dynamic`, `sleeptime`, `voice_sleeptime`) are a useful
   baseline. The Linus Phase 3 spawner spec ([`phase3-spawner.md`](../specs/phase3-spawner.md)) commits to `Role` as a
   first-class type (DEC-0050) but does not yet name the manager taxonomy. Tentative answer: Linus Phase 3 commits to
   `supervisor` (the Maestro/Worker pattern) and `dynamic` (the investigation-memory-aware pattern from DEC-0052) as the
   v0 vocabulary; `round_robin` is implementable on top of `dynamic`; `sleeptime` defers to Phase 7+ when the
   consolidation pipeline lands; `voice_sleeptime` is out of scope. Worth a Phase 3 spawner-spec ADR.

5. **Agent File format as the Linus Phase 3 agent-serialization contract.** Letta's `.af` format covers AgentState +
   blocks + message history + attached MCP servers + tools + source documents + group membership, with `id_mappings`
   re-keying on import. Linus Phase 3 will need an equivalent for handing off task-scoped agent state across agents and
   sessions. Should Linus crib the Agent File schema directly (changing field names where DEC-0050/0051 vocabulary
   diverges) or re-derive a Linus-native shape from scratch? The first is faster and inherits a thought-through design;
   the second is cleaner but slower. Tentative answer: crib the schema, document the crib in the Phase 3 spawner spec,
   and credit Letta in the schema's docstring.

6. **`memory_apply_patch` and `memory_insert` as memory-edit verbs — patch-style vs. line-numbered.** Letta's recent
   memory-edit additions (`memory_replace`, `memory_insert`, `memory_apply_patch` in `BASE_MEMORY_TOOLS_V2/V3`) are a
   verb evolution from MemGPT's coarser `core_memory_append` / `core_memory_replace` toward finer-grained edits. The
   `memory_apply_patch` verb takes a patch string (presumably unified diff format) and applies it; `memory_insert` is
   line-number-aware. For Phase 2 scratchpad-edit verbs in `linus.memory.scratchpad.*`, should Linus adopt the
   patch-style + line-numbered shape now, or stick with the simpler `write` / `append` / `replace` until measurement
   shows the richer shape is worth the agent-side complexity? MemGPT-paper Open Question 4 already raised
   function-calling reliability as a Worker-registry property; the patch-style verbs raise the function-calling
   complexity bar further.

7. **SCoT/Letta-style memory in the Phase 3 codebuff comparison.** Codebuff's repo-note Open Question 2 names
   "SCoT/Letta-style memory" as a Phase 3 evaluation candidate against LLMLingua and summarization checkpoints (see
   [`codebuff.md`](codebuff.md) §7). With this repo-note in place, the codebuff Open Question now has a primary-source
   target on the Letta side; the Phase 3 Worker-pruner evaluation can compare the Letta memory-block + paged-archival
   pattern against codebuff's per-step inline `context-pruner` agent on Dan's task suite. Should the Phase 3 evaluation
   spec name Letta-style memory specifically (per the comparator set this repo-note now anchors), or stay with the more
   abstract "memory-aware compression" framing in codebuff §7?

8. **Anthropic-compatible HTTP as a Phase 5+ Linus capability — second confirming signal.** Both Kimi-K2's deployment
   ([`Kimi-K2.md`](Kimi-K2.md) §3) and Letta's REST API ship Anthropic-compatible endpoints alongside OpenAI-compatible
   ones. DEC-0005 commits Linus to OpenAI-compatible-only at v0. Two confirming signals from independent products is
   enough evidence to consider revisiting; should the Phase 5+ planning include an "Anthropic-compatible HTTP as a Linus
   capability" ADR alongside the orchestration-backend Phase 2a work, or wait for a third signal?
