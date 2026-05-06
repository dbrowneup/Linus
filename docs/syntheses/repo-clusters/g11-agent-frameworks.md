# Group 11 Synthesis — Agent Frameworks, Skills, and Evaluation

**Date:** 2026-05-05 **Author:** Claude Sonnet 4.6 **Trigger:** 2026-05-05 new-repo roll-up; eight repos added from
skills-and-practices survey.

---

## What this document is

Group 11 is the cluster that closes the Phase 1 Recon loop and opens the Phase 2a specification. The eight repos span
three distinct but interlocking concerns: how to build a Worker agent (pydantic-ai, dspy, superpowers, gptme, huginn),
what skills Workers need to operate effectively (Agent-Skills-for-Context-Engineering), and how to know whether Workers
are working at all (promptfoo, lmnr). No prior cluster group addresses all three questions together. G7 (harnesses)
covers orchestration runtime; G6 (MCP tools) covers the tool substrate; G4 (memory) covers persistence. G11 is the
behavioral and empirical layer that sits above all of them.

The cluster produces two Integrate verdicts with immediate actionability — pydantic-ai as the orchestration primitive
and promptfoo as the evaluation harness — plus six Study verdicts that each contribute a concrete pattern or decision
input. The Study group is unusually coherent: dspy informs Phase 6 fine-tuning; superpowers and gptme inform Phase 2a
Worker behavior design; Agent-Skills-for-Context-Engineering provides the theoretical grounding for context routing;
huginn provides an orchestration anti-pattern catalogue; lmnr provides the Phase 5 observability target. None of these
eight repos are dead ends.

This document does not re-review individual repos — the per-file notes in `docs/repo-notes/` cover that ground. What it
does is name what this cluster collectively establishes, extract the reusable engineering patterns, connect G11 to the
broader Linus corpus, and make the phase-tagged implications explicit so they can be acted on without re-reading eight
notes.

---

## The unifying thesis

These eight repos collectively answer three questions that the existing cluster groups leave open, and the answers are
connected.

The first question is what the right base abstraction is for a Linus Worker agent. The candidate field is pydantic-ai,
dspy, gptme, and superpowers — four frameworks with very different philosophies. Pydantic-ai is type-safe and
provider-agnostic, with FastAPI ergonomics applied to LLM calls; it gives you an Agent class, RunContext dependency
injection, a validated `@tool` decorator, and Pydantic-validated outputs. DSPy is a compiler, not a runtime — it treats
prompts as learned parameters and optimizes them automatically, which is a different layer of abstraction (more relevant
for Phase 6 than Phase 2a). Superpowers is a behavioral methodology: it enforces spec-first, test-first discipline
before any implementation, but it operates on top of an existing agent runtime rather than replacing it. Gptme is a
mature CLI-first autonomous agent with a tool registry, plugin system, and lessons architecture. The answer the cluster
produces is not "pick one and ignore the rest" but a stack: pydantic-ai as the runtime base (type safety, provider
abstraction, tool registration), superpowers's behavioral patterns as the discipline layer on top (spec-first,
RED-GREEN-REFACTOR, subagent review gates), and gptme's plugin/lessons architecture as the extensibility model for
domain skills. These three fit together because they operate at different levels of the same stack.

The second question is what skills Workers need, and how they are taught. Agent-Skills-for-Context-Engineering provides
the curriculum: 14 platform-agnostic skills covering context degradation, memory system architecture, tool design
orthogonality, and evaluation methodology. The through-line is that context quality — not model size — is the primary
determinant of Worker effectiveness at a fixed compute budget. A Worker with good context routing, appropriate session
summarization, and well-designed tools outperforms a larger Worker running on poorly curated context. This has an
immediate design implication: Linus's orchestration layer needs to be a context router first and a model dispatcher
second. The skills curriculum is the intellectual foundation for designing that router.

The third question is how you know whether a Worker configuration is actually working. Promptfoo provides the answer for
evaluation: YAML-defined test suites, Ollama provider integration, semantic similarity and custom graders, and JSON
output that feeds regression detection. Lmnr provides the answer for observability: OpenTelemetry spans over every LLM
call, tool execution, and decision point, with a SQL-queryable backend and signal detection for anomalies. The key
insight from having both in the same cluster is that evaluation (promptfoo) and observability (lmnr) answer different
questions and should not be conflated. Promptfoo measures whether a given Worker configuration produces correct outputs
on known tasks — it is a correctness instrument. Lmnr measures what the system actually does during live operation — it
is a diagnostic instrument. Both are needed; they are used at different times and for different failure modes.

---

## Key findings

**pydantic-ai (Integrate, Phase 2a) — the orchestration primitive.** Pydantic AI is the base layer for Linus's
orchestration backend. The Agent class abstracts provider differences (Ollama, MLX-Flash, Anthropic) behind a typed
interface; RunContext carries per-call state (KnowledgeBase session, genomics context, sandbox policy) without global
mutation; the `@tool` decorator produces schema-validated, documentation-complete tool definitions from Python type
hints and docstrings, mirroring FastMCP's `@mcp.tool` pattern at the agent level. The four-package monorepo structure
is itself a design reference: `pydantic-ai-slim` (core, minimal dependencies), `pydantic-graph` (DAG for complex agent
loops), `pydantic-evals` (systematic evaluation), and `clai` (CLI interface). Phase 2a does not need `pydantic-graph` or
`pydantic-evals`; it needs `pydantic-ai-slim` plus the MLX-Flash and Ollama Model subclasses.

The MCP integration in pydantic-ai is natively compatible with the G6-committed FastMCP substrate: a pydantic-ai Agent
can call tools registered on a FastMCP server without any adapter layer. This means the Phase 2a tool registry (FastMCP
on `streamable-http`, as recommended in the G6 synthesis) and the Phase 2a Worker agent (pydantic-ai) compose without
friction. The Capabilities pattern — composable bundles of {tools, instructions, model tweaks} — is a cleaner
alternative to a flat tool registry for Linus's domain-specific skills (bioinformatics, genomics, code generation);
each domain gets a Capability that loads its tools only when the task context requires them.

The concrete Phase 2a task: wrap MLX-Flash and Ollama workers as pydantic-ai Model subclasses, port KnowledgeBase's
query functions to `@agent.tool`, instantiate an Agent with Linus's tool registry, and run 10 representative Dan tasks
against it. This gives a complete reference implementation of the orchestration layer testable against the Dan task
suite before any further Phase 2 infrastructure is built. Adopting pydantic-ai reduces Linus orchestration code by
approximately 70% compared to a bespoke Agent wrapper — the Agent class, model dispatch, tool registration, and type
validation are all handled. The tradeoff is a new external dependency in the core inference path; that dependency is
well-maintained (Pydantic team), MIT-licensed, and Python 3.10+ compatible with the linus conda env.

**dspy (Study, Phase 1 → 6) — the prompt optimizer.** DSPy is not a runtime for Phase 2a; it is essential reading for
Phase 6. The framework treats LM calls as learnable modules with typed input/output Signatures (declarative specs for
what the LM should do), composed via Primitives (ChainOfThought, Retrieve, MultiChain), and optimized end-to-end by
Teleprompters (BootstrapFewShot, MIPRO, BayesianSignatureOptimizer). The key conceptual shift: DSPy treats prompts as
learned parameters rather than hand-written strings, and optimizes them against a metric over a training set.

For Phase 6 (LoRA fine-tuning), DSPy offers a concrete experiment: take a slice of Dan's task suite, define DSPy
Signatures for the core operations (paper retrieval → summary, metagenomics question → analysis plan), run
BootstrapFewShot to synthesize in-context demonstrations, then use those demonstrations to train LoRA adapters on
Qwen2.5-Coder:14b. Measure whether DSPy-optimized prompts outperform hand-crafted prompts on the held-out Dan task
suite. This is the "prompt as data, not as code" philosophy applied at the fine-tuning level. For Phase 1, the immediate
value is Signatures as a clean tool-contract spec format: instead of manually writing docstrings, declare input fields
and their descriptions, output fields, and constraints — a habit worth establishing before Phase 6 requires it.

DSPy and pydantic-ai are not competitors. A pydantic-ai Agent can call dspy.ChainOfThought modules internally; the
Agent handles the session loop and tool dispatch while DSPy handles the per-module prompt optimization. This composition
is untested but architecturally sound and worth prototyping in a Phase 6 experiment before committing.

**superpowers (Study, Phase 2a) — the behavioral discipline layer.** Superpowers is a skill-based plugin methodology
for coding agents that enforces structured workflows: brainstorming → design → planning → implementation → review. Each
workflow step is a markdown skill file with YAML metadata that auto-triggers when the task context matches defined
keywords. The critical pattern is the progressive disclosure architecture: agents load only skill names at startup, and
full skill content activates lazily when the task triggers it. This keeps the context budget controlled even when the
skill library is large.

The subagent-driven-development workflow is directly portable to Linus Phase 2a: a Worker handed a task spec should
automatically invoke check-plan, implement-task, review-against-plan, and report-completion — what Superpowers calls the
"dispatch and verify" loop. The RED-GREEN-REFACTOR discipline (delete code written before tests; enforce TDD strictly)
is a 1-to-1 behavioral skill Linus can embed in Worker task specs without adopting the full plugin system. The
finishing workflow (merge/PR decision, worktree cleanup) maps cleanly onto Linus branch discipline as defined in
BRANCHING.md. The skill template format (YAML frontmatter with name, description, triggers; markdown body with
instructions and examples) is worth adopting as the standard format for Linus domain skills in `docs/specs/`.

The two-stage review pattern — spec compliance first, then code quality — is the most actionable behavioral import for
Linus Phase 2a. Workers should not self-certify completion against a single criterion. Stage 1 asks "did the output
match the spec?" Stage 2 asks "is the output high quality?". These are different questions and frequently diverge on
underspecified tasks.

**Agent-Skills-for-Context-Engineering (Study, Phase 1→2 bridge) — the context-routing curriculum.** This curriculum
of 14 platform-agnostic skills provides the theoretical foundation for Linus's context routing decisions. Three skills
are immediately applicable to Phase 2a design. The context-degradation skill documents the lost-in-middle phenomenon
and the attention U-curve: in long contexts, information in the middle of the window receives systematically less
attention than information at the beginning or end. The mitigation — summarization, windowing, reranking — informs how
Linus's orchestration layer should compress long session history before handing it to a Worker. The memory-systems skill
frames Linus's KnowledgeBase as a long-term memory system and characterizes how Workers should query it (graph
traversal, not keyword search, for multi-hop questions). The tool-design skill argues for orthogonality: each tool
should do one thing, minimize tokens in its description, and compose with other tools rather than internally branching.

The evaluation skill is the bridge to G11's benchmarking half of the cluster: it teaches how to measure agent success
empirically, including context-efficiency metrics (tokens used, tool calls made per task) alongside accuracy. The Dan
task suite in `benchmarks/` should track both. The trigger-keyword pattern from the repo — skills detect activation by
matching task language to keyword lists in YAML frontmatter — is worth extracting as a reference for Linus's own skill
activation system in Phase 2a.

**gptme (Study, Phase 2a, 7) — the mature autonomous agent reference.** Gptme is the closest reference implementation
in the entire cloned-repo collection to what a Linus Worker Agent looks like in production. Three years of development
have produced a layered architecture that Linus Phase 2a should study before finalizing its own design: a core chat
loop (prompt → LLM call + tool selection → execute → feedback), stateless tool functions returning structured output,
a plugin system loading custom tools from configuration directories, a skills system (lightweight YAML bundles injected
when mentioned), a lessons system (contextual guidance activated by keyword patterns), and a persistent autonomous agent
template with git-tracked workspace and task queue.

The lessons system is the most underrated pattern in the repo. Instead of re-injecting domain knowledge in every
prompt, gptme maintains a library of lessons that activate contextually. For Dan's domain (metagenomics, long-read
sequencing, _Botryococcus braunii_ lipid metabolism), this means: when a Worker's task mentions PacBio HiFi or
metagenomics, the relevant bioinformatics best-practice lesson injects automatically. The lessons reduce per-prompt
token cost while increasing relevance. Phase 7 (Skills & Autonomy Graduation) is the right phase to adapt this system;
Phase 2a should design the tool registry with lessons in mind, so that adding domain lessons later doesn't require
refactoring the core loop.

The hook system (pre/post tool execution callbacks) is the enforcement point for Linus's SAFETY.md sandbox policy.
Rather than embedding sandbox logic in every tool function, register sandbox-check hooks at the agent level; every tool
call passes through them unconditionally. This is the same architectural pattern as FastMCP's middleware pipeline —
cross-cutting concerns (authorization, rate limiting, audit logging) belong in the middleware/hook layer, not in
individual tool implementations.

**huginn (Study, before Phase 2a orchestration design) — the agent/event DAG reference.** Huginn is a Ruby/Rails
self-hosted automation platform whose core abstraction — stateful Agents consuming and emitting structured Events along
a directed graph in a scheduler loop — is directly applicable to Linus's orchestration design even though none of the
implementation code transfers. The Agent/Event DAG pattern establishes what "multi-agent workflow composition" looks
like as a first-class system concept, as opposed to an ad-hoc chain of function calls.

The gem-extensibility model (third-party tools installable without forking the core) is the organizational pattern
Linus will need as the skill library grows beyond a single developer's attention. The Huginn acceptance test suite
(complex stateful workflow tests via headless browser) demonstrates how to test multi-step agent pipelines end-to-end —
a testing pattern Linus lacks entirely for Phase 2a. Huginn's reliance on a full database (MySQL/PostgreSQL) is heavier
than Linus needs, confirming the G7 recommendation for workgraph's JSONL append-only DAG as the Linus session-store
shape. Read the Huginn agent-wiring code before finalizing Phase 2a's orchestration dispatch mechanism; then document
the Python-equivalent design in ARCHITECTURE.md.

**lmnr (Study, Phase 5+) — the observability target architecture.** Laminar is a full-stack AI observability platform
(Rust Actix-web backend, Next.js frontend, PostgreSQL + ClickHouse + RabbitMQ) that ingests OpenTelemetry spans, serves
a trace viewer with SQL query interface, and detects anomalies via learned signal filters. It is the right Phase 5+
observability target for Linus agents, with one critical caveat: the app-server is Linux-only (inotify, `/proc`-based
process trees), so it cannot run natively on Dan's M1 Max. Self-hosted deployment requires Docker and is feasible as a
stateless service on a future Mac Studio or x86 Linux VM.

The immediate Phase 2a design implication — independent of when Laminar is deployed — is OTel instrumentation from day
one. The OTel SDK is one import and one initialization call; it adds no operational burden in Phase 2a. If Linus agents
emit OTel spans from the beginning, instrumenting for Laminar at Phase 5 requires no retroactive code changes. The OTel
`gen_ai.*` attribute namespace (model name, input tokens, output tokens, tool name, span kind) is the schema to follow.
Emit it everywhere: LLM calls, tool executions, KnowledgeBase queries, and orchestration decision points. The span data
is also useful locally — a lightweight SQLite span store in `src/linus/telemetry/` gives Linus basic trace visibility
without the full Laminar stack, covering the Phase 2–4 observability gap before Laminar is operationally justified.

**promptfoo (Integrate, Phase 1 close) — the evaluation harness.** Promptfoo is the benchmarking layer for Linus's Dan
task suite. It is a production-grade Node.js CLI that runs YAML-defined test suites against any LLM provider (including
local Ollama), computes per-test metrics (accuracy, latency, token cost), supports semantic similarity and custom grader
assertions, and outputs structured JSON results. The Node.js runtime adds a second language dependency alongside
Python, but promptfoo runs as a standalone CLI rather than inside Linus's Python package — the boundary is clean, the
integration is a shell call or subprocess invocation. There is nothing to build; it is ready to use now.

The concrete Phase 1-close task: define 20 representative Dan tasks in a `promptfooconfig.yaml` in
`benchmarks/dan_tasks/`, test against Ollama/qwen2.5-coder:14b, export JSON to `benchmarks/results/`, measure mean
latency and task accuracy. This baseline is the measurement against which every subsequent model swap, prompt change,
or tool addition is evaluated. The red-teaming plugins (prompt injection, jailbreak, refusal bypass) are Phase 3
material — relevant when Linus exposes tools with write capabilities and sandbox policy must be validated under
adversarial conditions.

---

## Patterns and modules worth lifting

The most immediately actionable pattern from G11 is the pydantic-ai Agent as the orchestration primitive with
FastMCP-registered tools. The connection: pydantic-ai's `@agent.tool` decorator and FastMCP's `@mcp.tool` decorator
are cognate patterns. Tools registered in the FastMCP server are callable from a pydantic-ai Agent over MCP without
duplication; tools that need to be callable directly from Python code (without MCP round-trip) are registered via
`@agent.tool`. The Phase 2a tool registry decision is: FastMCP for the external-facing MCP surface (Cline, Claude Code,
future front-ends), pydantic-ai Agent for the internal Worker runtime. Both surfaces consume the same underlying Python
functions; the decorator determines which surface registers them.

The progressive-disclosure skill architecture appears in three independent repos (superpowers, gptme, Agent-Skills).
All three converge on the same design: a YAML frontmatter index loaded at startup with skill names and trigger
keywords, plus markdown body content loaded lazily when the task context matches. This convergence is strong evidence
the pattern is correct. Linus should adopt it as the standard format for domain skills — a `skills/` directory under
`src/linus/` with one file per skill, YAML frontmatter defining triggers, markdown body containing instructions and
examples. Domain skills (metagenomics analysis, genome assembly, WDL pipeline construction) go here; they inject into
Worker context automatically when the task language matches their trigger keywords.

The hook/middleware layer for sandbox enforcement is the gptme + FastMCP convergence on cross-cutting concerns. Both
frameworks separate per-tool logic from cross-tool policy. Linus should follow this pattern: SAFETY.md policy lives in
a hook registered at the Agent level (not inside individual tools), and the FastMCP middleware pipeline enforces rate
limits and authorization at the MCP surface. Policy changes require editing one place, not every tool implementation.

The two-stage review pattern from superpowers (spec compliance, then code quality) is the Worker quality gate. Encode
it in the task spec format in `experiments/` and `docs/specs/`: every task spec should include an explicit "done
criteria" list covering both spec compliance (output matches stated requirements) and quality (output follows Linus
engineering conventions). Workers self-report against both before declaring completion.

The OTel instrumentation-from-day-one pattern from lmnr is a cheap insurance policy. One import (`opentelemetry-sdk`),
one initialization call, and standard `gen_ai.*` attributes on every LLM call and tool execution. The spans write to a
local SQLite store (lightweight custom store, not the full Laminar backend) until Phase 5 justifies Laminar. The
tracing data enables post-hoc debugging of long autonomous runs — a capability that becomes critical as Workers handle
increasingly complex tasks in Phase 3+.

---

## Cross-references

**G6 (MCP tools) → pydantic-ai + FastMCP composition.** The G6 synthesis committed FastMCP as the MCP substrate and
`streamable-http` as the Phase 2 transport. Pydantic-ai's native MCP support means a pydantic-ai Agent can call tools
registered on a FastMCP server without any adapter. The Phase 2a architecture is: FastMCP server on
`streamable-http:PORT` exposing KB tools, ontomics, and codesight; pydantic-ai Agent pointing at that endpoint via its
MCP capability. This is the two-sentence Phase 2a architecture for tool access.

**G7 (harnesses, workgraph) → huginn + pydantic-ai orchestration design.** The G7 synthesis recommended workgraph's
JSONL append-only DAG as the Phase 2a session-store shape. Huginn's agent/event DAG confirms the pattern — a
structured, inspectable graph of agent steps is the right primitive for multi-step workflows. Pydantic-ai's
`pydantic-graph` package (type-hint DAG for complex agent loops) is a Python-native alternative to porting workgraph's
Rust JSONL shape; the two are compatible design choices for the same problem. The Phase 2a decision is which to use as
the session-store format; both G7 and G11 evidence points toward JSONL for simplicity, with pydantic-graph as the
in-process control-flow primitive.

**G4 (memory, agentmemory) → Agent-Skills-for-Context-Engineering memory-systems skill.** The G4 synthesis covered
persistence mechanisms (agentmemory's 51-tool MCP, SQLite-backed episodic memory). The memory-systems skill from G11
provides the framing for how Workers query the KnowledgeBase as long-term memory — graph traversal for multi-hop
questions, vector recall for similarity search, BM25 for exact-term scientific literature search. The two clusters
together define the Linus memory architecture: what to store (G4) and how Workers should access it (G11).

**Skills-and-practices thematic synthesis → Agent-Skills-for-Context-Engineering.** The skills-and-practices thematic
synthesis (from X/Twitter practitioner threads, `docs/syntheses/skills-and-practices-synthesis.md`) argues that
context quality is the primary bottleneck in AI-accelerated workflows. Agent-Skills-for-Context-Engineering provides
the empirical and theoretical grounding for the same claim. Together they establish a unified principle for Linus Phase
2a: the orchestration layer's primary job is context management — selecting, compressing, and routing the right
information to each Worker — not model dispatch. Model dispatch is a solved problem (pydantic-ai handles it); context
management is the open problem that Phase 2a must address.

**G8 (sci-agents) → gptme domain-skills applicability.** The G8 synthesis covered scientific agent patterns
(retrieval-augmented generation for papers, structured output for experimental results). Gptme's lessons system is the
mechanism for encoding Dan's domain knowledge (metagenomics, long-read sequencing, _B. braunii_ metabolism) into Worker
context automatically. G8 identified the science-domain gap in generic agent frameworks; gptme's lessons architecture
is the concrete answer to how that gap is bridged.

---

## Phase-tagged implications

**Phase 1 close (promptfoo baseline, dspy Signature reading).** Promptfoo is the only Phase 1 deliverable from G11.
Define 20 representative Dan tasks in `benchmarks/dan_tasks/promptfooconfig.yaml`, test against Ollama local workers,
export baseline JSON results. This closes the Phase 1 measurement gap — before Phase 2a begins, there is a quantitative
baseline for task accuracy and latency against which every subsequent change is measured. Simultaneously, read DSPy
Signatures as a habit-forming exercise: whenever writing a tool docstring, also write the equivalent DSPy Signature.
This costs nothing now and makes Phase 6 a translation exercise rather than a design exercise.

**Phase 2a (pydantic-ai as orchestration base, superpowers behavioral discipline, skill architecture).** Three
deliverables. First: wrap MLX-Flash and Ollama as pydantic-ai Model subclasses, register KnowledgeBase query functions
as `@agent.tool`, instantiate an Agent, run 10 Dan tasks, measure against the promptfoo baseline. This is the Phase 2a
orchestration smoke test. Second: extract the superpowers two-stage review pattern and subagent-driven-development
workflow into Linus's task spec format — every `docs/specs/` file gets explicit spec-compliance and quality-criteria
sections. Third: create `src/linus/skills/` directory with the progressive-disclosure format; write three domain skills
(metagenomics, genome assembly, WDL pipelines) as the initial library. Read huginn's agent-wiring code before
finalizing the orchestration dispatch mechanism; document the Python equivalent in ARCHITECTURE.md.

**Phase 2b (OTel instrumentation, gptme hook pattern).** Add OTel instrumentation to the pydantic-ai Agent: one SDK
import, one initialization, `gen_ai.*` attributes on every LLM call and tool execution. Implement a lightweight SQLite
span store in `src/linus/telemetry/` as the local trace backend. Register sandbox-policy hooks at the Agent level
(mirroring gptme's pre/post tool execution hooks); SAFETY.md policy enforces unconditionally without per-tool
duplication.

**Phase 3 (multi-agent workflows, red-teaming).** Activate huginn-style DAG dispatch for multi-step tasks using the
workgraph JSONL session-store shape from G7. Run promptfoo red-teaming plugins (prompt injection, jailbreak, refusal
bypass) against Linus's tool registry — particularly KB query tools and any tools with write access. The Agent-Skills
evaluation skill informs how to add context-efficiency metrics (tokens per task, tool calls per task) to the benchmark
suite alongside accuracy.

**Phase 5 (lmnr observability, gptme lessons).** Evaluate self-hosted Laminar on an x86 Linux target (future Mac
Studio or VM). The OTel spans emitted from Phase 2b are forward-compatible; no instrumentation changes needed. If
Laminar deployment is operationally justified, point the exporter at the Laminar gRPC endpoint. If not, the SQLite span
store from Phase 2b is sufficient through Phase 5. Separately, adapt gptme's lessons system for Linus domain
knowledge — a Phase 7 stretch target that should be designed in Phase 5 to avoid refactoring the core loop later.

**Phase 6 (dspy prompt optimization, LoRA fine-tuning).** Run the DSPy BootstrapFewShot experiment: define Signatures
for 3–5 core Linus operations, run the teleprompter against a labeled subset of Dan's task suite, collect optimized
demonstrations, use them to train LoRA adapters on Qwen2.5-Coder:14b via mlx-lm. Measure optimized-prompt accuracy
against the Phase 1 promptfoo baseline. Explore pydantic-ai + DSPy composition as a target architecture — Agent
handles session state and tool dispatch; DSPy modules handle per-operation prompt optimization internally.

---

## Open questions for Dan

**Pydantic-ai as a dependency in the core inference path.** Adopting pydantic-ai reduces Linus orchestration code by
approximately 70%. The tradeoff is a new external dependency in the core path. The alternative — a bespoke lightweight
Agent wrapper using only `pydantic` (already a dependency) — keeps the dependency graph minimal but requires
reimplementing model dispatch, tool registration, and multi-turn management. Is the dependency cost acceptable for the
implementation savings, or should Linus implement its own thin wrapper and treat pydantic-ai as a study reference only?

**Worker review gates.** Superpowers enforces two-stage review (spec compliance, then code quality) before a Worker
can mark a task complete. Should Linus Workers self-review against both criteria autonomously (requires a rubric in
every task spec), or does Dan review at task completion regardless (simpler for Phase 2a, less scalable for Phase 3
multi-agent workflows)?

**Dan task suite scope and grader design.** Promptfoo can run 20 tasks (fast iteration) or 100 tasks (more regression
coverage) against the local Ollama worker. For Dan's domain (genomics Q&A, metagenomics analysis plans, code generation,
paper summarization), semantic-similarity assertions may not capture correctness — a gene name list is right or wrong,
not "similar." Should the Phase 1 task suite use custom Python graders for domain-specific assertions from the start,
or start with built-in assertions and add custom graders when failures reveal their inadequacy?

**OTel local storage vs. Laminar.** The lmnr note recommends OTel instrumentation from day one but defers Laminar
deployment to Phase 5+. The gap between Phase 2b and Phase 5 is covered by a lightweight SQLite span store. Is that
gap acceptable, or is there value in deploying a minimal observability backend earlier — for example, a Jaeger
all-in-one container (Docker, stateless, no Metal required) as a temporary trace viewer before full Laminar is
justified?

**Context-routing policy in the orchestration layer.** Agent-Skills-for-Context-Engineering argues that context
quality, not model size, is the primary determinant of Worker effectiveness. Phase 2a's orchestration layer needs a
context-routing policy: when does session history get summarized vs. passed verbatim? When does a KB query result get
truncated vs. passed in full? These are design decisions that shape Worker performance on every task. Should the Phase
2a spec include an explicit context-routing policy, or defer that to empirical tuning once the system is running and
the promptfoo baseline reveals which tasks hit context quality failures first?

---

_This synthesis should be revisited when the Phase 1 promptfoo baseline lands (it determines the Phase 2a evaluation
target), when the pydantic-ai smoke test runs (it confirms or revises the Integrate verdict), when the Phase 2a
orchestration spec is written (huginn, superpowers, gptme, and Agent-Skills all feed into it), and when Phase 6
fine-tuning begins (DSPy Signatures and the BootstrapFewShot experiment both land there)._
