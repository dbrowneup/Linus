# Group 7 Synthesis — Agent Harnesses, Orchestration, Model Routing

**Date:** 2026-05-04 (updated 2026-05-08) **Author:** Claude Sonnet 4.6 (Worker, commissioned by Dan Browne)
**Trigger:** G7 fan-out synthesis pass; ten new repo notes (claude-squad, claude-task-master, codebuff, workgraph,
openrouter-skills, python-sdk, origin, gravityfile, semanticworkbench) added alongside four existing harness notes
(cline, claw-code, claw-code-local, openclaw). Amended 2026-05-05: semanticworkbench expanded with full Key findings
subsection. Refined 2026-05-08: origin benchmark data + macOS Tahoe caveat added; worktree failure modes cross-linked to
CLAUDE.md engineering convention; R2-12 linkage surfaced in Open questions.

---

## What this document is

Group 7 is the most directly consequential cluster in the current fan-out for Linus's near-term decisions. Where Groups
1–6 inform substrate, knowledge architecture, and memory — questions with answers spread across Phase 2 through Phase 6
— Group 7 informs a decision that is overdue: what does the Phase 1f orchestration evaluation actually conclude, and how
does that conclusion shape the Phase 2 MVP? Every repo in this cluster has been read through that lens.

This document is not a re-review of each repo. The per-file notes cover that ground. What it does is name the
cross-cutting finding that DEC-0002 now has real data behind it, identify the specific patterns worth lifting, and make
the phase-tagged implications explicit.

---

## The unifying thesis

DEC-0002 resolved to keep custom orchestration rather than delegate it to an existing framework. Group 7 does not
reverse that. What it does is sharpen the case considerably: the most valuable repos in this cluster are not
replacements for Linus's orchestration layer but sources of individually liftable patterns that would otherwise take
months to arrive at by first principles. The cluster collectively argues for picking patterns rather than platforms —
lift the JSONL DAG schema, the git-worktree isolation primitive, the three-role model split, the ProviderPreferences
vocabulary, the assistant-as-HTTP-service protocol shape — and build the thin Linus-native connective tissue that holds
them together.

The Phase 1f evaluation question was framed as a competition: custom Linus prototype versus claude-squad plus
claude-task-master versus pmetal-MCP-as-orchestrator. Group 7 dissolves that framing. Claude-squad and
claude-task-master are not competing for the same slot; they occupy different layers (runtime isolation versus task
decomposition) and the most honest Phase 1f verdict is that they are complementary. Neither is a framework Linus should
vendor; both are sources of specific patterns Linus should implement natively in Python. That conclusion, grounded in
the repo notes, is the concrete data point DEC-0002 needed.

---

## Key findings

### workgraph is the sleeper find of G7

workgraph (`erikg/workgraph`) is the most liftable orchestration runtime in the entire repo collection so far, and it
almost does not look like one. The Rust binary `wg` is a full product — TUI, Matrix/Telegram channels, Chromium, a
keyring, an agency layer — but beneath the product surface is a four-component design that is genuinely clean: a
`.workgraph/graph.jsonl` append-only JSONL DAG file, a `handler_for_model.rs` dispatch function that maps a model spec
like `nex:qwen3-coder` or `openrouter:anthropic/claude-opus-4-7` onto a handler (CLI, in-process OAI-compat, or
external), a heartbeat-plus-PID supervisor, and a lightweight `## Validation` convention pairing each task with success
criteria that a cheap model can score.

The JSONL graph store deserves specific attention. It is human-readable, git-diffable, append-only, naturally
audit-logged, and requires zero ceremony to initialize — `wg init` produces a directory with one config file and one
graph file. This is the right weight for a personal orchestration system, and it is directly composable with Linus's
existing BRANCHING.md workflow: every task node in the graph maps to an `agent/<task-id>` branch, and the graph file
commits alongside the task's working output. The session store that ARCHITECTURE.md calls for but has not specified
should look like this.

The one notable macOS gap — `collect_process_descendants` walks `/proc` and silently degrades to an empty vec on macOS —
is a footnote, not a blocker. A `kqueue`-based or `pgrep -P`-based equivalent is a straightforward Phase 1f experiment,
not an architectural problem. The JSONL schema and the dispatch pattern port to Python without the Rust crate.

### claude-squad and claude-task-master are complementary, not competing

Both repos address the Phase 1f question but from different angles, and reading them side by side makes the distinction
concrete. claude-squad (`smtg-ai/claude-squad`) is concerned with runtime isolation and supervision: one tmux session
per agent, one git worktree per agent (created by shelling
`git worktree add -b <prefix><session> <worktreePath> <HEAD-SHA>`), and a `--daemon` polling supervisor that watches
each agent's pane for a waiting prompt and sends Enter. It has no opinion about what the agent is doing or how tasks are
structured. claude-task-master (`eyaltoledano/claude-task-master`) is concerned with decomposition and tracking: it
takes a PRD, runs `task-master parse-prd` to emit a typed task graph in `.taskmaster/tasks/tasks.json`, and exposes 36
MCP tools (tiered at 7/15/36 tools for ~5k/10k/21k context tokens) for iterating on that graph from Cursor, VS Code, or
Claude Code. It has no opinion about where tasks run or how workers are isolated.

The right Phase 1f reading is: claude-task-master's schema and three-role model split (main decomposer, research model
for fresh context, fallback) are worth porting as a Linus skill; claude-squad's git-worktree-per-task primitive is worth
porting as the canonical Worker workspace; workgraph's JSONL DAG and dispatch function are worth porting as the runtime.
None of these are vendored; all are re-implemented in ~200-500 lines of Python each. Together they cover most of what a
custom orchestration prototype would eventually build anyway, in less time and with more prior-art validation.

### codebuff is the most direct external prior art for Maestro/Worker discipline

codebuff (`CodebuffAI/codebuff`) is the only shipped product in G7 that decomposes a coding request across a
role-specialized internal fleet rather than routing it to a single model. Buffy (the orchestrator in
`agents/base2/base2.ts`) manages a `spawnableAgents` array — file-picker, code-searcher, planner, editor, reviewer,
basher, thinker, context-pruner — each with its own model, prompt, tool allow-list, and output contract. Sub-agents are
`SecretAgentDefinition` objects: `id`, `model`, `inputSchema`, `toolNames`, `spawnableAgents`, `systemPrompt`,
`instructionsPrompt`, `stepPrompt`, `handleSteps` generator, `outputMode`. The `handleSteps` generator pattern —
yielding tool calls and receiving `STEP` resumption tokens — is a clean formalism for deterministic orchestration glue
around stochastic LLM steps that is cleaner than Cline's monolithic loop. The `context-pruner` agent, spawned inline
every turn, is a worked example of "a Worker dedicated to context hygiene" that Linus's Phase 3 will want once
multi-session tasks accumulate scratchpad at scale.

The 61% versus 53% headline against Claude Code needs replication before citing; the eval harness is Codebuff-authored,
the judge is three Gemini 2.5 Pro instances running a Codebuff-written rubric. What the number does communicate clearly
is that role specialization is measurably worth engineering. The specific agents worth studying as Linus design
references are `file-picker.ts`, `editor.ts`, `code-reviewer.ts`, and the context-pruner — those four roughly map to the
Worker roles Linus's Phase 3 orchestrator will need. Codebuff itself cannot be run locally because Freebuff routes to
cloud models with telemetry, defeating Linus's purpose.

### origin is the most Linus-aligned harness in G7, AGPL-blocked at the desktop layer

origin (`7xuanlu/origin`) is not a harness in the usual sense — it is a local memory daemon that gives any MCP-speaking
client shared, durable cross-session memory. What makes it Linus-aligned is not the category but the hardware and
substrate choices: Apple Silicon only (M1+, no Linux, no Windows), Rust workspace, libSQL with 768-dimensional
BGE-Base-EN-v1.5-Q embeddings, DiskANN indexing, FTS5 virtual table via triggers, RRF fusion combining vector and
keyword search, and an LLM rescoring pass using Qwen3-4B-Instruct-2507 on Metal via llama-cpp-2. That is almost exactly
the substrate the Linus memory-architecture spec has been converging on from first principles. The daemon exposes an
HTTP API on `127.0.0.1:7878` and a launchd plist for persistent background operation — the right operational shape for a
personal system. The v0.2.1 benchmarks tighten the case further: 96% fewer tokens per query (168 vs. 4,505 baseline),
Recall@5 of 88.0% on LongMemEval-oracle, and 67.3% on LoCoMo10 — strong enough that the Integrate-as-service path is
worth scheduling in Phase 2b rather than continuing to study. Two operational caveats: (a) macOS Tahoe 26.x requires
`CXXFLAGS="-std=c++17"` at compile time, and `ggml_metal_init` can fail on Tahoe even when native Metal works; the
daemon auto-degrades to a no-LLM mode in that case, so a `sw_vers` check + `cargo build` smoke test should be the first
step of the R2-39 evaluation. (b) origin's `Arc<dyn EventEmitter>` trait — passing a capability boundary into the
business-logic core rather than leaking a UI or storage handle — is precisely the discipline ARCHITECTURE.md wants
between Linus's orchestration layer and front-ends; worth surfacing as an explicit Phase 2a engineering pattern.

The blocker is license topology. The Tauri desktop app and root frontend are AGPL-3.0-only; the three server crates
(`origin-types`, `origin-core`, `origin-server`) are Apache-2.0, a split the maintainer made explicitly to let
downstream tools integrate as out-of-process services without AGPL contamination. That split defines the safe
integration path: Linus can run `origin-server` as a sidecar and call its HTTP API from `src/linus/` without touching
AGPL code. Whether that is the right call depends on how closely the Phase 2 memory-architecture spec converges on
Origin's design. The Worker's note hedged "Study with a high prior on later Integrate-as-service" — that framing remains
correct after reading the memory-synthesis and the architecture spec at commit `d77e026`. If the spec lands on libSQL +
BGE + RRF, the answer is probably "run `origin-server`"; if it diverges, the codebase remains the best single reference
for how those components fit together on Apple Silicon.

### python-sdk's ProviderPreferences is the most mature router vocabulary in G7

The OpenRouter Python SDK (`OpenRouterTeam/python-sdk`) is not a Linus dependency — it talks exclusively to a paid
hosted endpoint — but `components/providerpreferences.py` is the most mature prior-art reference for what a router in
front of N model providers needs to expose. The `ProviderPreferences` Pydantic model names: `order` (preferred provider
sequence), `allow_fallbacks` (bool), `only` / `ignore` (allow and deny lists), `sort` (one of
`price | throughput | latency | exacto`), `require_parameters` (only providers supporting all requested params),
`preferred_max_latency` and `preferred_min_throughput` with p50/p99 percentile cutoffs, and `quantizations` (filter by
quant level). This vocabulary is the product of years of running a production routing service across dozens of providers
and watching what operators actually need to express. When Linus's Phase 2a router starts fronting Ollama, pmetal serve,
mlx-lm, and eventually fine-tuned Linus variants, it will need to answer most of the same questions. Lifting the field
names where local-backend semantics match (`order`, `allow_fallbacks`, `sort`, `require_parameters`, `only`, `ignore`)
gives Linus a router interface that is already legible to any tool speaking OpenRouter, without taking on the SDK as a
dependency.

### openrouter-skills: the open-responses protocol spec is the one keeper

Of the eight openrouter-skills skills, seven require `OPENROUTER_API_KEY` and are unusable in an offline Linus
deployment. The exception is `open-responses/SKILL.md`, which documents the Open Responses protocol spec (POST
`/v1/responses`, polymorphic items, response/item state machines, SSE event catalog, agentic loop with
`previous_response_id`, four extension mechanisms) — provider-agnostic, not OpenRouter-specific. This is the protocol
Linus's Phase 2a backend is implicitly targeting when ARCHITECTURE.md says "OpenAI-compatible endpoint." Linus should
decide explicitly whether the Phase 2a target is the legacy OpenAI Chat Completions shape (what Ollama serves today),
the newer OpenAI Responses shape (stateful), or the Open Responses spec. The three are not interchangeable, and the
choice locks in client compatibility with Cline, openclaw, and claw-code-local. The open-responses spec document should
be linked from ARCHITECTURE.md or forked into `docs/specs/serving-protocol.md` before Phase 2a begins.

### semanticworkbench: the protocol shape is worth studying, the implementation is not

Semantic Workbench (`microsoft/semanticworkbench`) is the most structurally ambitious platform in G7 — a full FastAPI
backend, React/Fluent-UI frontend, and an open-ended assistant-plug-in model based on HTTP discovery and a typed Python
SDK (`AssistantApp` with decorator event handlers). The protocol shape — workbench owns conversations, assistants are
external HTTP services discovered via a typed registration call, events flow over a typed model — is the cleanest
articulation in G7 of "one host, many heterogeneous workers" and is directly relevant to how Linus's Phase 2 tool
registry and agent spawner should be structured. If Workers register via HTTP rather than being invoked as in-process
calls, openclaw and Cline can plug into the same registration surface alongside local model backends, which is the right
architecture for Phase 5+ cross-harness compatibility.

The implementation cannot be adopted: Azure/MSAL identity (`@azure/msal-browser`, `azure-identity`,
`azure-keyvault-secrets`) is woven into both the frontend and the backend, and the Codespaces dev-container flow makes
native M1 Max bring-up a manual reconstruction project. The MIT license is clean but the Azure coupling is a
disqualifier for a local-first system. The actionable output is to read `libraries/python/semantic-workbench-api-model`
and `workbench-service/semantic_workbench_service/controller/` before drafting the Phase 2a orchestration API, and to
decide whether Linus's Worker registration should look structurally similar — HTTP discovery plus typed event bus —
rather than reinventing a different protocol.

### Dumb components, smart interaction patterns (Canteen Theme B) and Goose as the Rust+MCP harness entrant

An external practitioner survey of the multi-agent landscape converges on the same engineering taste this cluster
arrives at empirically. As Canteen frames it: _"Dumb components with smart interaction patterns outperform smart
components with dumb interaction patterns."_ and _"Heuristic belief updates avoid per-step LLM calls; this is the
central scalability lever for multi-agent debate." — Canteen, Multi-Agent Landscape, 2026-03-27_
([Canteen, _Multi-Agent Landscape_, 2026-03-27](../../../context/notes/canteen_blog_landscape_2026-05.md)). The first
claim is The Algorithm restated for orchestration: do not invest in making each agent smarter when investing in the
interaction protocol gives larger returns. This validates the existing Linus Worker fan-out preference (DEC-0050: role
as a first-class type in the agent spawner; DEC-0051: AgentReport as the typed inter-agent message), and it sharpens
the case for the codebuff-style role specialization noted above — codebuff's measurable gain over Claude Code comes
from interaction structure (planner → file-picker → editor → reviewer → context-pruner), not from any individual agent
being more capable than its peers. The second claim — heuristic belief updates as the scalability lever — is concrete
engineering: when a debate framework needs every agent to update its position based on what other agents said, doing
that with per-step LLM calls scales as O(N²) per round; doing it with a heuristic update rule (weighted polling, vote
shift, confidence decay) scales as O(N) per round and removes the LLM from the inner coordination loop entirely.
**`debate-or-vote` (`deeplearning-wisc/debate-or-vote`)** is the research-code reference implementation of this
pattern; it is a concrete candidate for the Phase 3 spawner Worker fan-out coordination model and is on the Tier 2
repo-add list (Study + spike) per the Canteen landscape note.

**Goose** (`block/goose`) is the meaningful Rust+MCP harness entrant currently absent from the per-repo notes. The
harness-plurality landscape covered above includes `claw-code`, `cline`, `claude-code-guide`, and `openclaw`; Goose
extends the set with the explicit Rust+native-MCP combination that the Canteen survey calls out. The relevance is the
same shape claw-code-local will eventually take: a Rust-native coding agent that consumes Linus's MCP surface as a
first-class client. Adding the repo-note (Tier 2, Study) is a small task with a concrete payoff: it gives Linus a
direct prior-art reference for how the Rust client side of the MCP boundary is wired in a shipped product.

The claw-code project posted a labelled architectural diagram for its orchestration layer that captures the harness
shape this cluster is converging on — Architect / Executor / Reviewer triad driven by an integrated harness layer
(`oh-my-codex` + `clawhip` + `oh-my-openagent`) over a development loop of analysis → planning → coding/tools →
review → verification, with text-based developer input as the primary control surface:

![claw-code key orchestration concept — Architect/Executor/Reviewer triad over a development loop, text-based agent
orchestration via `$team` and `$ralph` modes (instructkr/claw-code, 2025)](../../../context/pics/HE2psIVbcAA6VLz.jpg)

The diagram is useful as a reference picture of the pattern: a harness layer sitting between the developer's text
commands and an explicit role triad, with the development loop visible as a closed cycle rather than a one-shot
generation. Linus's Phase 2a orchestration layer should expose enough surface that an external harness like this
one (or claw-code-local, or Goose) can plug roles into Linus's MCP tool registry rather than re-implementing the
review and verification stages internally.

### gravityfile: Ignore, save the scanner gotcha

gravityfile (`epistates/gravityfile`) is a Rust TUI disk-usage explorer with no LLM dependency and no relevance to
orchestration or model routing. It sits in G7 as the designated outlier slot. The one useful technical detail: the
`jwalk::WalkDirGeneric` scanner caps at 4 threads on macOS via a `#[cfg(target_os = "macos")]` branch because APFS
contention degrades throughput past that point. If Linus's Phase 3 KnowledgeBase indexer walks the `context/papers/`
directory with parallel workers, that cap should be respected. Otherwise the file closes here.

---

## Patterns and modules worth lifting

This is the section with actionable engineering content. Every item below can be implemented in Python under
`src/linus/orchestration/` or `src/linus/skills/` without vendoring any external code.

**The JSONL task-graph store.** Derived from workgraph's `.workgraph/graph.jsonl` schema. One record per event: `id`,
`title`, `status`, `blocked_by`, `assigned`, `exec`, `created_at`, `started_at`, `completed_at`, `log[]`. Append-only,
human-readable, git-diffable. Propose this as the concrete format for Linus's session store and audit log — write a
`docs/specs/orchestration-store.md` ADR that copies the schema into Linus terms before Phase 2a begins.

**The git-worktree-per-Worker isolation primitive.** Derived from claude-squad's `session/git/worktree_ops.go`. The full
flow — resolve repo root, create `~/.linus/worktrees/<branch>_<nanoseconds>`, shell
`git worktree add -b agent/<task-id> <path> <HEAD-SHA>`, capture the base SHA for stable diffs, cleanup with
branch-delete suppression for pre-existing branches — is ~220 lines that port directly to Python subprocess calls. Adopt
this as the canonical Worker workspace primitive. Two-tier model makes sense: durable worktrees for `agent/<task-id>`
branches, in-memory `git diff` only for one-shot stateless Workers. **Failure modes** now captured as a CLAUDE.md
engineering convention ("Worktree fan-out discipline"): three non-obvious pitfalls are base-SHA drift (all parallel
worktrees must branch from the same commit), Edit-tool path resolution (Edit/Write calls with absolute paths sometimes
resolve to the primary checkout rather than the worktree path — prefer `Bash(cd <worktree-path> && …)` inside an agent),
and branch-delete-before-merge loss (retain agent branches until the consolidated PR is confirmed merged; do NOT
`git branch -D` immediately after `git worktree remove`). When not to use worktrees: if Workers are writing
non-overlapping files on a shared branch, sequential agent dispatch with file-level partitioning is simpler and avoids
the worktree overhead entirely.

**The three-role model split.** Derived from claude-task-master's provider-plugin architecture. Main model does
decomposition; a research model queries an external or specialized source for fresh context; fallback covers main model
failure. Linus's version plausibly needs a fourth role — a cheap triage model (Mistral-7B or Qwen2.5-7B) for scoring and
classification tasks — but the three-role skeleton is the right starting point and should be encoded in the Phase 2
router's model-registry schema rather than implied by convention.

**The task-spec schema.** Derived from claude-task-master's `.taskmaster/tasks/tasks.json` shape. Fields: `id`, `title`,
`description`, `status`, `dependencies[]`, `priority`, `details`, `testStrategy`, `subtasks[]`. Linus's PRD-to-tasks
skill should emit this exact shape into `experiments/<task-id>.json` or the JSONL store above, callably from Maestro or
from a Worker. The schema is small enough to implement in an afternoon.

**The handler-for-model dispatch function.** Derived from workgraph's `src/dispatch/handler_for_model.rs`. One function,
one argument (model spec string like `ollama:qwen2.5-coder:14b` or `pmetal:serve` or `mlx-lm:<path>`), returns a typed
handler. Today Ollama, tomorrow pmetal serve and mlx-lm and fine-tuned Linus — all behind the same dispatch axis. This
is simpler to implement in Python than to discover by accident.

**The ProviderPreferences vocabulary.** Derived from python-sdk's `components/providerpreferences.py`. Fields `order`,
`allow_fallbacks`, `sort`, `require_parameters`, `only`, `ignore` map cleanly onto local-backend semantics. Drop
`max_price`, `zdr`, `data_collection` (hosted-provider concerns). Write the Linus-native version as a Pydantic model in
Phase 2a alongside the router design; record it as an ADR so the vocabulary choice is explicit.

**The agent-definition contract.** Derived from codebuff's `SecretAgentDefinition` TypeScript type. Translated to
Python/Pydantic: `id`, `model`, `display_name`, `system_prompt`, `tool_names`, `spawnable_agents`, `output_mode`, and a
`handle_steps` async generator. This is the right shape for Linus's Phase 3 Worker registry — it forces per-agent model
declaration and role specialization rather than treating all Workers as interchangeable.

**The `## Validation` convention.** Derived from workgraph's agency layer. Every task spec in `experiments/<task-id>.md`
or the JSONL store carries a `## Validation` section with explicit success criteria. The orchestration layer (or a cheap
triage-model Worker) scores completed tasks against these criteria. This is the lightweight version of SAFETY.md's
autonomy-tier-graduation mechanism and should be adopted in the Maestro/Worker protocol spec now, before Phase 2a, as a
zero-cost improvement to existing practice.

**The open-responses protocol reference.** Derived from openrouter-skills' `open-responses/SKILL.md`. The state-machine
and SSE event catalog should be linked from ARCHITECTURE.md or reproduced in `docs/specs/serving-protocol.md` as the
reference for what Linus's Phase 2a `/v1/responses`-compatible endpoint is aiming at.

---

## Cross-references

**G6 fastmcp / MCP adoption.** The origin note, the cline note, and the semanticworkbench note all land on MCP as the
tool-substrate that already connects harnesses and Workers. Three of the four most relevant repos in the collection have
converged on MCP. This reinforces the DEC-0005 evaluation deferred to Phase 3+ — the data now supports making MCP-as-
tool-substrate an explicit Phase 3 ADR rather than letting it accrete by default.

**G4 memory overlap.** Origin belongs architecturally in the Knowledge/Memory cluster, not in Harnesses — it sits here
only because the curation taxonomy placed it in G7. The origin note and the memory-synthesis document should be read
together: origin is the most complete existing implementation of what the memory-synthesis proposes as Layer C (cross-
session episodic store) and Layer D (semantic/knowledge memory) combined. The memory-architecture spec at
`docs/specs/memory-architecture.md` should explicitly evaluate `origin-server` as a candidate implementation before
building from scratch.

**Entrepreneurial surface.** The skills-and-practices-synthesis flagged Opportunity 7 (local AI infrastructure
consulting for research institutions). Group 7 sharpens that opportunity: claude-squad, workgraph, and semanticworkbench
together demonstrate that the demand for multi-agent orchestration infrastructure exists and is actively being built by
multiple independent teams. The gap is not that no one is doing it — it is that no one is doing it on Apple Silicon, in
a way that is offline-first and private by design. That gap is Linus's differentiated angle.

---

## Phase-tagged implications

**Phase 1f closure (immediate).** Write the DEC-NNNN orchestration-evaluation ADR with the following verdict: (1)
claude-squad and claude-task-master address different layers — decomposition versus runtime isolation — and are
complementary; neither is a candidate for adoption as a product, both are sources of specific patterns to implement
natively. (2) workgraph's JSONL DAG plus dispatch function is the most liftable runtime primitive in the cluster;
produce a `docs/specs/orchestration-store.md` that copies the schema into Linus terms. (3) the Phase 1f evaluation
question ("do we need to build custom multi-Worker spawning?") answers itself: yes, because no existing tool covers the
Python-native, Ollama-first, SAFETY.md-policy-enforcing combination Linus requires — but "build" here means "assemble
from five liftable primitives" not "invent from scratch."

**Phase 2a MVP.** Four concrete deliverables implied by G7: (1) adopt the JSONL task-graph as the session store format
with an ADR; (2) implement the git-worktree-per-Worker isolation in `src/linus/orchestration/workspace.py`; (3) write
the `ProviderPreferences`-vocabulary router preferences schema as a Pydantic model; (4) decide the serving protocol
target (Chat Completions vs Open Responses) and document it in ARCHITECTURE.md. None of these require an internet
connection or a paid API. All can be done concurrently with Phase 2's other MVP work.

**Phase 2b memory layer.** Evaluate `origin-server` as a candidate sidecar for the cross-session episodic store before
building from scratch. The Apache-2.0 daemon is license-clean for out-of-process integration. If the memory-architecture
spec converges on libSQL + BGE + RRF, running `origin-server` at `127.0.0.1:7878` is the fastest path to a working v0.

**Phase 3 parallel agents.** Adopt the codebuff agent-definition contract (as a Pydantic model) as the Worker registry
schema. The four agents to implement first as Linus-native Workers are: file-picker (scopes context before any task),
editor (writes code), reviewer (scores output against `## Validation`), and context-pruner (runs inline to prevent
scratchpad accumulation). Workgraph's heartbeat-plus-PID supervisor and the `kqueue`-based macOS tree-kill equivalent
should land in this phase.

**Phase 2a protocol design.** Before committing the orchestration API shape, read `semanticworkbench`'s
`libraries/python/semantic-workbench-api-model` and `workbench-service/semantic_workbench_service/controller/` as a
reference for assistant-as-HTTP-service registration and event dispatch. The question of whether Linus's Workers are
in-process calls or HTTP-registered services should be settled explicitly as an ADR: the semanticworkbench protocol
design demonstrates that the framework-agnostic HTTP-registered pattern is viable for orchestration, and the tradeoffs
(loose coupling, external integration, debuggability) merit explicit discussion before Phase 2a hardens the decision.

**Phase 5 interface.** The semanticworkbench protocol design — Workers as HTTP-registered external services with a typed
event bus — is the right reference when Phase 5 connects openclaw, Cline, and claw-code-local to Linus's orchestration
layer. If Phase 2a commits to HTTP registration, the Phase 5 surface is a thin rendering layer over already-standardized
events. If Phase 2a commits to in-process, the Phase 5 interface needs a different abstraction for external-service
registration.

---

## Open questions for Dan

**Phase 1f framing.** The evaluation brief treats claude-squad and claude-task-master as finalists for the same slot.
After reading both notes, the verdict is that they are not competitors — they are planner and runner. Does the ADR
capture "adopt both patterns, neither product," or should it declare one pattern as primary and treat the other as
supplementary?

_Partially resolved (CLAUDE.md "Workgraph JSONL as the Phase 2a session-store shape" Engineering Convention): the
recommended Phase 2a shape is workgraph-style JSONL DAG + dispatch. ARCHITECTURE.md notes the audit log is append-only
JSONL at `~/.linus/audit.jsonl` (Phase 2). The session-store substrate (JSONL vs SQLite vs JSONL→SQLite migration gate
at Phase 3) remains an implementation choice but JSONL-first is the default per the convention. Remaining framing
question (whether to declare one pattern primary) is live as **R2-12** in
[`top-questions.md`](../../questions/top-questions.md#tier-2--shape-phase-26-architecture)._

**Open Responses versus Chat Completions.** The serving protocol choice locks in client compatibility. Ollama serves the
legacy Chat Completions shape; the Open Responses spec adds stateful response threading and the SSE event catalog. Cline
and openclaw speak both; claw-code-local speaks OpenAI-compat generically. What is the Phase 2a target, and is it worth
a short spike against the open-responses spec document before committing? This question is promoted as **R2-05** in
[`top-questions.md`](../../questions/top-questions.md#tier-1--block-phase-1--phase-2a-architecture), where it is listed
as a Tier 1 item blocking Phase 2a architecture.

**Origin as memory sidecar.** The memory-architecture spec is fresh at commit `d77e026`. Does Dan want to evaluate
`origin-server` as a Phase 2b candidate sidecar before the spec hardens, or does the spec get written first and origin
gets evaluated against the resulting requirements? The order matters because if origin is the candidate, the spec should
be written in a way that makes the evaluation legible. Now tracked as **R2-39** (Tier 3) in
[`top-questions.md`](../../questions/top-questions.md#tier-3--documentation-conventions-longer-horizon-scope), with the
additional caveat that macOS Tahoe compatibility (see origin key findings above) should be verified before scheduling
the bake-off.

_Resolved (DEC-0018, DEC-0045): MCP adoption is committed for Phase 2 onwards (not Phase 3 kickoff). fastmcp is the
default framework. DEC-0005's MCP portion is superseded by DEC-0018 per the index in DECISIONS.md._

---

_This document should be revisited at Phase 1f ADR close, at Phase 2a design kickoff (serving protocol and session store
decisions), at Phase 2b (origin-vs-build-from-scratch for the memory layer), and at Phase 3 kickoff (Worker registry
schema and parallel-agent heartbeat supervisor)._
