# Linus — Architecture

## The central distinction: harness vs. orchestration

A recurring source of confusion when working across multiple agentic tools is the blur
between "harness" and "orchestration layer." They look similar from the outside — both
involve LLMs, tool use, and loops — but they sit at different positions in the stack and
accrue value differently. Linus is designed around keeping them cleanly separate.

A **harness** is a coding workflow tied to a UX surface. Cline lives in VS Code. Claude
Code lives in a terminal. Claw-code lives in a terminal too, with an eventual ACP/Zed mode.
Each of these takes a single user query, runs one conversation with one model, and inside
that conversation loops the model against built-in tools (read file, write file, run shell,
etc.) until the task is deemed complete. Harness logic is things like "render a diff
inline," "ask for approval before running this command," "remember the last 20 messages in
this editor session." Harnesses are front-end-specific by nature. Swapping harnesses means
a different UX; swapping them should not mean losing your knowledge base, tools, policies,
or fine-tuned model.

An **orchestration layer** is a product backend. It accepts requests from multiple front-
ends (harnesses, chat UIs, automations), decides which model should handle each request,
exposes a persistent set of domain-specific tools, maintains durable state (sessions,
memory, audit logs), enforces policies that need to apply regardless of front-end, and can
coordinate multiple model calls into a single workflow (e.g., fan out to parallel agents,
merge results). It has no UI of its own — front-ends are its UIs. The orchestration layer
is where Dan-specific intelligence accrues over time.

The cleanest analogy: harnesses are terminal emulators. The orchestration layer is the
shell. One shell, many terminals. Swap the terminal, keep your shell. Swap the harness,
keep Linus.

### Where the overlap actually is

Three places, and it's worth being explicit:

- **Tool execution.** Harnesses ship file ops, shell execution, and similar by default.
  Linus exposes tools that are Linus-specific: knowledge base search, multi-agent spawn,
  skill invocation, cluster context retrieval. The rule: if the tool is UX-local (edit
  this file in this editor), the harness owns it. If the tool is product-level (search
  Dan's papers, call a skill, spawn agents, enforce sandbox), Linus owns it. Sandboxed
  shell is owned by Linus because sandbox policy must apply across all harnesses.

- **Agent loops.** Harnesses run loops within a single user conversation. Linus runs loops
  internal to a single request (multi-tool calls, parallel agents). They don't conflict
  because they operate at different scopes.

- **System prompts.** Both layers contribute. The harness adds "you are a coding assistant
  in this repo." Linus adds "you have access to these Linus-native tools, and here is
  relevant Dan context." They stack.

### Why this architecture earns its keep

When you use openclaw in Phase 5, you don't rebuild knowledge integration. When you build
a native Linus app in Phase 8, you don't rebuild it. When you switch Cline out for the
native VS Code Ollama chat, you don't rebuild it. Your work accrues in the backend, not
in the harness. The orchestration layer isn't extra work — it's the work, done once, so
the harness layer can stay thin and swappable.

## Layered view

```
  ┌─────────────────────── FRONT-ENDS ─────────────────────────┐
  │  VS Code (Claude Code, Ollama chat, optionally Cline)      │
  │  LM Studio (model discovery, casual chat)                  │
  │  openclaw (Phase 5+: chat, voice, Canvas, mobile nodes)    │
  │  native Linus app (Phase 8+)                               │
  └───────────────────────────┬────────────────────────────────┘
                              │  OpenAI-compatible HTTP
                              ▼
  ┌──────────── LINUS ORCHESTRATION LAYER (src/linus/) ────────┐
  │                                                            │
  │  Router       Tool registry     Agent spawner              │
  │  Sandbox      Session store     Audit log                  │
  │  Skills       Memory            RAG gateway                │
  │                                                            │
  └────┬──────────────────┬──────────────────┬─────────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
  ┌─────────┐       ┌────────────┐      ┌──────────┐
  │INFERENCE│       │ KNOWLEDGE  │      │ TRAINING │
  │         │       │            │      │          │
  │Ollama   │       │KnowledgeBase│     │pmetal    │
  │pmetal   │       │(submodule) │      │ (LoRA,   │
  │ serve   │       │            │      │  QLoRA,  │
  │mlx-lm   │       │SPECTER2    │      │  DPO,    │
  │mlx-flash│       │Metadata DB │      │  distill)│
  │(larger- │       │Knowledge   │      │          │
  │ than-RAM│       │ Graph      │      │mlx-lm    │
  │ later)  │       │Qdrant?     │      │  ft (alt)│
  └─────────┘       └────────────┘      └──────────┘
```

## Components

### Front-ends

- **Claude Code (terminal)**. Primary hosted-Maestro interface. Used for planning,
  architecture, multi-file coordination, and tasks that benefit from frontier-model
  reasoning. Does NOT route through Linus — Claude Code talks directly to hosted Claude.
- **VS Code** with the extensions that make sense: Git Graph, Claude Code extension,
  Ollama chat integration, optionally Cline. Individual extensions can point at either
  hosted Claude or Linus's local endpoint.
- **LM Studio**. Used primarily for browsing and downloading open-source models (convenient
  UI, MLX/GGUF filters, memory-fit estimation) and for casual one-off chats with models
  that aren't wired into the Linus flow yet. Not the primary runtime.
- **openclaw** (Phase 5+). Polished multi-channel front-end: macOS menu bar app, voice
  wake, live Canvas, iOS/Android nodes. Configured to point at Linus's OpenAI-compatible
  endpoint. Accept duplication between openclaw's internals and Linus's; we use it as a
  UI, not as a framework to extend.
- **Native Linus app** (Phase 8+). SwiftUI or Tauri, directly talking to Linus backend.
  Fewer features than openclaw, fully branded, fully ours.

### The Linus orchestration layer (src/linus/)

This is the product. A Python package, built iteratively starting in Phase 2.

**Router.** Receives OpenAI-compatible requests. Selects the appropriate worker model
based on request metadata and task class. Routes to the chosen inference engine.

**Tool registry.** Catalog of Linus-native tools, grouped by domain:
- `linus.knowledge.*` — papers search, paper get, cluster context, KG query, SPECTER2
  nearest neighbors (wraps KnowledgeBase)
- `linus.fs.*` — sandboxed read/write within the Linus tree
- `linus.shell.*` — sandboxed command execution
- `linus.agent.*` — parallel agent spawn, agent status, agent result merge
- `linus.skill.*` — invoke a named skill (see Skills below)
- `linus.data.*` — data package management (Phase 4: Kiwix, maps, etc.)

Tools are discoverable by models via the standard OpenAI tool-use schema.

**Agent spawner.** Implements the multi-agent pattern: given a parent spec and a list of
subtasks, spawn N Worker processes in parallel, each with a scoped prompt, scoped tool
allowlist, and shared results store (SQLite). Returns aggregated results to the parent.
First implementation probably uses `asyncio` + Ollama's async client; LangGraph
evaluated as an alternative once needs are clearer (Phase 3+).

**Sandbox.** Enforces the allowlist/blocklist from SAFETY.md on every tool call. Writes
every call to the audit log. Rejects forbidden operations. Confirmation-required ops are
returned to the front-end for user approval before execution.

**Session store.** SQLite, one table initially. Columns: session_id, timestamp, user_msg,
assistant_msg, tool_calls (JSON), tool_results (JSON). Used for continuity across
front-end reconnections.

**Audit log.** Append-only JSONL at `~/.linus/audit.jsonl`. Every tool call, every model
call, every policy decision. Useful for safety review, usage analysis, and autonomy
graduation criteria.

**Skills.** Linus-specific prompt templates and workflows, following the `SKILL.md`
convention established by Anthropic. Stored under `src/linus/skills/<skill_name>/SKILL.md`.
Invoked via the `linus.skill.invoke` tool. Phase 7 is when domain skills bloom.

**Memory.** Deferred. Start with session history in the session store. A proper memory
layer (long-term facts about Dan, preferences, past-conversation retrieval) is a Phase 3+
addition. Don't over-engineer before the need is concrete.

**RAG gateway.** Thin adapter layer between Linus's tool registry and KnowledgeBase's
existing retrieval infrastructure. Adds caching, query logging, and the ability to fuse
multiple retrieval sources (SPECTER2 + TF-IDF + KG) into a single context object.

### Inference backends

- **Ollama.** First-stop Worker model server. Homebrew install, Metal acceleration.
  Current models: `mistral:7b-instruct`, `qwen2.5-coder:7b`. Suitable for Phase 1 and 2.
- **pmetal serve** (Phase 1 evaluation, Phase 2+ if adopted). Apple Silicon native, written
  in Rust, with custom Metal kernels, native ANE pipeline, and OpenAI-compatible serving.
  Offers capabilities beyond Ollama/mlx-lm: fused kernels, ANE integration, LoRA-adapter-
  aware serving, FP8 runtime quantization. Serious candidate for primary serving backend.
- **mlx-lm.** Reference/fallback MLX-based LLM runtime. Used for anything pmetal doesn't
  yet support and for direct MLX access in experiments. Also the alt path for LoRA
  fine-tuning if pmetal's LoRA doesn't pan out.
- **mlx-flash** (Phase 5+). Weight streaming from SSD for larger-than-RAM models. Used
  for inference-only evaluation of large fine-tuned models. Inspired by Dan Woods'
  flash-moe and Apple's LLM in a Flash paper.
- **BitNet / Bonsai** (Phase 5+). 1-bit model inference for specific memory-constrained
  deployments. Evaluated for the Linus-on-phone future and for the "bigger-model-smaller-
  memory" direction.

### Knowledge subsystem

**KnowledgeBase** (`modules/KnowledgeBase/`) is a git submodule pinned to a specific
commit of Dan's separate KnowledgeBase repo. It is the source of truth for Dan's paper
library, metadata, embeddings, clusters, and knowledge graph. Linus imports from it; Linus
does not modify it directly. Changes to KnowledgeBase happen in that repo and are brought
into Linus via `git submodule update`.

The integration is via `src/linus/knowledge/` which provides a thin adapter exposing
KnowledgeBase's functionality as Linus tools. Specifically:

- Ingest metadata.db at Linus startup
- Load SPECTER2 embeddings lazily
- Wrap the similarity graph and knowledge graph as queryable resources
- Expose all the above via the tool registry under `linus.knowledge.*`

**Qdrant** (optional, Phase 3+): if KnowledgeBase's current numpy-based similarity search
hits scalability limits, add Qdrant in Docker as the vector DB. Not needed for the MVP.

### Training subsystem (Phase 6+)

**pmetal** handles LoRA, QLoRA, DoRA, knowledge distillation, and preference optimization
(DPO/SimPO/ORPO/KTO) natively on Apple Silicon. If Phase 1 evaluation confirms performance
and stability, pmetal becomes the training backbone.

**mlx-lm ft** is the alternative path: well-understood, MLX-native, simpler.

**autoresearch methodology** (not the repo, the pattern): for optimizable processes,
frame the optimization as a metric + budget + keep-or-revert loop. Let a Worker iterate
overnight. Review results in the morning. Used during Phase 5 inference experiments and
Phase 6 fine-tuning hyperparameter search.

### Data sovereignty layer (Phase 4+)

- **Kiwix** serving offline Wikipedia (English initially, Simple English as a smaller
  option, Khan Academy content as a separate ZIM)
- **ProtoMaps PMTiles** serving OpenStreetMap data offline. PMTiles is the format; OSM is
  the data.
- **Data package registry** at `~/.linus/data_packages.json` tracking installed datasets,
  versions, update availability
- **Update check tool** polling upstream sources; user approves any downloads

Docker is acceptable for these services (stateless, no Metal needs).

## Boundary rules

- The orchestration layer **never** depends on any specific harness.
- Harnesses **never** depend on each other.
- KnowledgeBase is consumed via a defined adapter; Linus does not reach into
  KnowledgeBase internals.
- Inference engines are interchangeable behind the router. Swapping Ollama for pmetal
  should not require changes to the tool registry or chat UI.
- Tools are pure functions of their arguments (plus allowed side effects on the sandbox).
  No hidden global state.
- Every mutation is auditable. Every file write goes through `linus.fs.write`. Every
  shell command goes through `linus.shell.run_sandboxed`.

## Interface contracts

### OpenAI-compatible endpoint

`POST /v1/chat/completions` with the OpenAI ChatCompletions schema, including `tools`
and `tool_choice`. Supports streaming via SSE. Supports tool-call extensions for
Linus-native tools alongside standard ones.

### Tool schema

All Linus tools declare their schema in JSON-Schema draft 2020-12. Tools are registered
via decorator:

```python
@linus.tool("linus.knowledge.search_papers")
def search_papers(query: str, limit: int = 10) -> list[dict]:
    """Semantic search over Dan's paper library using SPECTER2."""
    ...
```

### Session persistence

Sessions are identified by UUID. A new session is created on first request without a
`X-Linus-Session` header. Sessions auto-expire after 30 days of inactivity (configurable).
Front-ends can resume sessions by passing the header.

### Sandbox contract

Every Linus tool that touches the filesystem or shell MUST:

1. Validate arguments against allowlist/blocklist from SAFETY.md
2. Write an audit log entry before executing
3. Return a `LinusToolResult` with status (`ok`, `denied`, `error`) and details
4. Never raise uncaught exceptions to the model; convert to status=error

## Implementation phasing

Phase 2 delivers a minimal but real version of this architecture:

- Router: single-engine (Ollama), no intelligent dispatch yet
- Tool registry: 3–5 tools (knowledge search, file read/write, sandboxed shell)
- Agent spawner: NOT in Phase 2 — deferred to Phase 3
- Sandbox: policy enforced, allowlist/blocklist live
- Session store: SQLite, simple
- Audit log: JSONL, append-only
- Skills: NOT in Phase 2 — deferred to Phase 7 when we know what skills matter
- Memory: NOT in Phase 2 — session history only
- RAG gateway: KnowledgeBase v1 (search + metadata)

Phase 3 extends: parallel agents, deeper KnowledgeBase integration, first skills.

Phase 5 extends: openclaw as a front-end; VS Code integration polished.

Phase 6 extends: training backend (pmetal or mlx-lm-ft), first fine-tuned adapters.

## Open architectural questions (revisit as they become concrete)

- **Protocol for parallel agent coordination.** Shared SQLite vs. Python multiprocessing
  queues vs. Redis vs. LangGraph state store. Decide in Phase 3 based on concrete
  workload.
- **Long-term memory design.** Embedding-based similarity over past conversations?
  Entity-linked facts? Deferred until a concrete use case surfaces.
- **MCP (Model Context Protocol) adoption.** Potentially useful for letting Linus consume
  MCP servers (e.g., `mcporter` as openclaw does). Evaluate in Phase 3 once we see how
  tool-use patterns settle.
- **Voice input routing.** When openclaw voice wake is integrated, does the voice stream
  go through Linus, or does openclaw transcribe and send text? Probably text, but
  validate when we get there.
- **Mobile companion architecture.** openclaw has iOS/Android node support via WebSocket.
  The question of whether Dan's phone talks to Linus directly or via an openclaw relay is
  deferred to Phase 9.

These remain open on purpose. The Algorithm says delete requirements that aren't forced;
these are forced when we hit them, not before.
