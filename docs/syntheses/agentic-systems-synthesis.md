# Agentic Systems Synthesis

## What this document is

_Refreshed 2026-05-09 with Trading-R1 (Tauric / UCLA same-lab progression from TradingAgents) and a cross-link to
Kimi-K2's open-source SOTA agentic-benchmark numbers (primary architectural fold in
[native-low-bit-apple-silicon](native-low-bit-apple-silicon-synthesis.md))._

A rewrite of the prior Group D synthesis, expanded from seven to ten paper-notes. This rewrite absorbs three new papers
— the two same-named-but-different _QuantAgent_ papers ([HKUST/IDEA, 2024](../paper-notes/2402.03755v1.md) and
[Stony Brook et al., 2025](../paper-notes/2509.09995v3.md)) and [WikiAutoGen](../paper-notes/2503.19065v1.md)
(KAUST, 2025) — and surfaces them as fresh evidence on threads that were present-but-quiet in the prior synthesis
(structured inter-agent communication, critic- stronger-than-writer, regret-bounded self-improvement). Tone matches the
[memory synthesis](memory-synthesis.md): prose-heavy, woven across papers, written to feed the next round of edits to
the landscape and questions documents.

The headline claim sharpens with the expansion: the agentic-systems literature has converged on a small set of
architectural primitives — role specialization, structured shared state, multi-level validation, per-tool documentation,
hybrid local/hosted-model routing, ReAct + reflection as the default loop, and a critic tier distinct from a writer tier
— and Linus's Phase 2/3 design is implicitly committing to most of them. The ten-paper version also promotes two threads
the seven-paper version under-weighted: structured inter-agent communication as a load-bearing primitive in its own
right, and the question of whether agentic-system theory (regret bounds, MDP formalism) deserves more weight in Linus's
design alongside the formal results that already anchor the memory pillar. The sober line under transferability stays:
most impressive results in this group lean on hosted frontier models in ways that don't transfer cleanly to a
local-first substrate — though [BioGuider](../paper-notes/2026.02.09.704801v1.md)'s finding that GPT-OSS edged out
Claude Sonnet and GPT-4o on its task remains the most encouraging local-first signal in the group.

---

## The papers at a glance

- [**Kosmos**](../paper-notes/2511.02824v2.md): 12-hour autonomous research agent organised around a structured "world
  model" that lets ~200 parallel rollouts cohere across 20 cycles into expert-rated multi-month-equivalent scientific
  output.
- [**Boiko/Gomes**](../paper-notes/2304.05332v1.md): the foundational 2023 Planner-plus-tools chemistry agent that ran
  Suzuki/Sonogashira couplings on a real Opentrons OT-2, plus the first serious dual-use safety analysis of a
  physical-actuator LLM system.
- [**BioGuider**](../paper-notes/2026.02.09.704801v1.md): four-module multi-agent platform that grades and corrects
  bioinformatics software documentation; benchmarked via controlled error injection; GPT-OSS edged out Claude Sonnet and
  GPT-4o.
- [**Sketch2Simulation**](../paper-notes/2603.24629v1.md): three-layer multi-agent pipeline (parsing → synthesis →
  validation) converting process flow diagrams into executable Aspen HYSYS simulations through the COM API; cloud
  multimodal + local Qwen-Coder for code.
- [**TradingAgents**](../paper-notes/2412.20138v7.md): seven-role "trading firm" template (analysts, bull/bear debate,
  trader, risk panel, fund manager) with a hybrid structured-document-plus- bracketed-dialogue communication protocol.
- [**Fundamentals of LLM Agents**](../paper-notes/2510.09244v1.md): survey decomposing every LLM agent into perception,
  reasoning, memory, and execution subsystems.
- [**Practical Guide for Evaluating LLMs**](../paper-notes/2506.13023v1.md): Google practitioners' three-pillar
  framework — Datasets (the 5 D's), Metrics (balanced scorecard, perplexity is a trap), Methodology (non-determinism,
  hallucination probes, non-response measurement).
- [**QuantAgent (HKUST/IDEA)**](../paper-notes/2402.03755v1.md): two-loop self-improving agent — writer/judge inner loop
  grounded in a KB, outer loop running results against the real environment and folding feedback back — with a
  Bayesian-regret bound showing total regret sublinear in KT under linear-MDP assumptions.
- [**QuantAgent (Stony Brook et al.)**](../paper-notes/2509.09995v3.md): four-specialist + one-integrator LangGraph
  framework for HFT directional prediction; majority-with-confirmation as the integrator commit rule; honest about
  per-cycle latency exceeding the 1-minute opportunity window.
- [**WikiAutoGen**](../paper-notes/2503.19065v1.md): KAUST's multimodal extension of the Storm/Co-Storm
  Wikipedia-article pipeline, with a four-viewpoint (supervisor / writer / reader / editor) self-reflection module and a
  critic LM materially stronger than the writer LMs.

The [Fundamentals survey](../paper-notes/2510.09244v1.md) sits at the centre as the taxonomy.
[Boiko/Gomes](../paper-notes/2304.05332v1.md) is the historical anchor. [Kosmos](../paper-notes/2511.02824v2.md) is the
present-day upper-bound demonstration. The five domain-specific multi-agent papers — BioGuider, Sketch2Simulation,
TradingAgents, the two QuantAgents, and WikiAutoGen — are different points in the same design space.
[Practical Guide](../paper-notes/2506.13023v1.md) is the cross-cutting discipline. The HKUST QuantAgent supplies the
only theoretical contribution (a regret bound); the Stony Brook QuantAgent ([g10-finance](repo-clusters/g10-finance.md))
supplies the leanest worked example of structured-prompt multi-agent dispatch — TradingAgents and Stony Brook QuantAgent
bracket the orchestration design space at DEC-0050: one is the maximal debate-style roster, the other the minimal
four-role linear pipeline. WikiAutoGen sharpens the critic-stronger-than-writer thread.

---

## Cross-cutting threads

### Thread 1: role specialization at the right granularity

The strongest, most cross-corroborated finding is that **named, scoped agent roles outperform pooled generalists**, and
the right unit of design is the role tuple — a
`(name, goal, constraints, allowed_tools, model_selection, context_schema, position_in_workflow)` object — not a
free-floating prompt string. The expanded paper set firms this up considerably.

[TradingAgents](../paper-notes/2412.20138v7.md) makes the argument most explicitly: each of seven agents is defined by a
goal sentence, a fixed tool inventory, an explicit constraint set, and a position in the workflow graph. Sentiment
analysts get web search and Reddit/X APIs; technical analysts get code execution and indicator libraries; bull/bear
researchers get only the analysts' reports — tools are scoped to roles, not pooled globally.
[BioGuider](../paper-notes/2026.02.09.704801v1.md) makes the same move at smaller scale across seven agents (planning,
execution, categorize, testing, assessment, reporting, correction). [Sketch2Simulation](../paper-notes/2603.24629v1.md)
names descriptor, validator, extractor, normalizer, basis, instantiation, configuration, and execution agents — and its
ablation study is the strongest piece of evidence in the group that **modular decomposition is doing real work, not
cosmetic**: collapsing the four coding agents into one (condition C3) substantially degrades connection consistency on
the harder cases, with the degradation growing non-linearly in task complexity. The Stony Brook
[QuantAgent](../paper-notes/2509.09995v3.md) is the leanest instantiation in the corpus — four specialists (Indicator,
Pattern, Trend, Risk) each with a narrow domain, a specific tool, and a structured output schema, plus a fifth
integrator (DecisionAgent) that acts only when "the majority align and are reinforced by confirmations."
[WikiAutoGen](../paper-notes/2503.19065v1.md) adds the supervisor / writer / reader / editor specialization at the
_critic_ layer rather than the _production_ layer, showing the role-tuple discipline applies to both halves of a
build-and-review pipeline.

[Kosmos](../paper-notes/2511.02824v2.md) is the partial dissent and the discipline against over-decomposition. Its
deliberate choice was exactly two roles (data-analysis worker, literature-search worker), avoiding the zoo of
micro-agents the application papers suggest. The lesson is that the right granularity matters and over-decomposition
into a dozen tiny roles can bury the real work under coordination overhead. The
[Fundamentals survey](../paper-notes/2510.09244v1.md) enumerates a canonical eight-role taxonomy (Planning, Reflection,
Error Handling, Memory Management, Action, Coding, Constraint, Security) but does not defend a specific decomposition;
it lists them.

For Linus this maps onto the agent spawner directly, and the expanded paper set makes the recommendation more confident,
not less. **Role is a first-class type in the Phase 3 spawner per DEC-0050**, not a convention. The Stony Brook
QuantAgent's four-specialists-plus- integrator topology with a majority-with-confirmation commit rule is the cleanest
minimal template the corpus offers; the Kosmos data point bounds it from below at two roles when focus matters more than
fan-out; WikiAutoGen's four-viewpoint critic block is the corresponding template for the review side. Three to seven
named roles per non-trivial workflow is the practical sweet spot.

### Thread 2: structured inter-agent communication, promoted to first-class

In the prior synthesis this lived inside the structured-shared-state thread. The expanded paper set argues it deserves
its own thread. The two QuantAgents and WikiAutoGen all use **structured inter-agent messages** — typed schemas,
role-keyed report formats, bracketed dialogue — as the substrate that lets multi-agent systems compose without the
telephone effect.

[TradingAgents](../paper-notes/2412.20138v7.md) names the failure mode explicitly: prior multi-agent frameworks pass
unstructured natural- language histories between agents, producing a "telephone effect" where context grows, details
drift, and earlier decisions get lost. Its hybrid protocol — structured documents with fixed schemas between teams,
free-form dialogue (bounded by N rounds and distilled by a facilitator) within debate teams — is the canonical
statement. The Stony Brook [QuantAgent](../paper-notes/2509.09995v3.md) goes further, eliminating free-form dialogue
entirely: every agent emits a typed structured output, the integrator reasons over the structured aggregate, and the
majority-with-confirmation rule is itself a structured commit predicate. The HKUST
[QuantAgent](../paper-notes/2402.03755v1.md) persists the (score, critique) pair as the structured carrier between
writer/judge turns. [WikiAutoGen](../paper-notes/2503.19065v1.md) implements its four-viewpoint self-reflection as DSPy
`Signature`-typed calls — each viewpoint has a rubric, returns a structured critique, and the writer consumes the union.
[Sketch2Simulation](../paper-notes/2603.24629v1.md)'s JSON-schema-enforced IR transitions are the most rigid version:
every inter-agent boundary is a typed JSON contract.

**The shape of the inter-agent message matters as much as the shape of the agent.** Free-form natural language between
agents is a default that works at small scale and silently degrades at larger scale; typed, role-keyed structured
messages are what the corpus's most mature systems converged on. For Linus this argues that the agent spawner should
ship a canonical `AgentReport` schema (header + structured fields + free-text rationale + tool-trace) that all Workers
are required to emit, with free-form text confined to a clearly named field. The Stony Brook QuantAgent's
majority-with-confirmation predicate is a generally useful integrator primitive — cheap, auditable, exactly the
consistency check an orchestration layer should impose before committing to an action.

The same Tauric Research / UCLA group that authored TradingAgents has since published
[Trading-R1, Xiao et al. 2025](../../context/papers/2509.11420v1.pdf), and the trajectory is itself instructive for the
typed-output thread. Where TradingAgents distributes the work across seven roles with bull/bear debate as the central
quality lever, Trading-R1 collapses that orchestration into a single model fine-tuned via supervised reverse-CoT
distillation followed by a three-stage easy-to-hard reinforcement-learning curriculum on Tauric-TR1-DB — a 100k-sample
corpus spanning 18 months, 14 equities, and five heterogeneous data sources (technical, fundamental, news, insider
sentiment, macro). The contribution that matters here is not the trading numbers but the **output shape**: Trading-R1
emits structured, evidence-based investment theses with a five-tier rating (Strong Buy / Buy / Hold / Sell / Strong
Sell) carrying volatility-adjusted reward labels, a free-text rationale grounded in the surfaced evidence, and an audit
trail of which data sources were consulted. That is the BioReason-Pro typed-structured-prediction shape (CLAUDE.md
§Typed structured prediction for biology skills, S25, 2026-05-06) reached from a different starting point — the
convention generalizes well beyond biology, and finance is the second domain in the Linus corpus to converge on it
independently. The pair also draws a methodological line for Linus: a multi-agent debate template (TradingAgents) is the
right shape when you need to surface and audit reasoning across many roles in one shot; an RL-trained single model
emitting the same typed structured output (Trading-R1) is the right shape once the structured rubric stabilizes and the
orchestration cost dominates. Phase 7 skills should default to the multi-agent shape; mature, high-cycle skills become
candidates for Trading-R1-style single-model RL distillation in Phase 6+.

### Thread 3: structured shared state as the antidote to multi-step drift

This is the prior synthesis's "structured shared state" thread, now narrowed to the _intra-investigation_ layer (state
shared across many rollouts on a single task) and complemented by Thread 2 on inter-agent messages.

[Kosmos](../paper-notes/2511.02824v2.md)'s world model is the largest instance: a structured shared state that lets ~200
parallel rollouts coordinate, enabling 8× more iterations than the prior state of the art without coherence collapse.
The HKUST [QuantAgent](../paper-notes/2402.03755v1.md) has a smaller analogue — the writer/judge shared context buffer
per task, plus the _KB itself_ as longer-lived shared state across tasks. Its outer loop takes real-environment feedback
and folds it back into the KB: **KB-grows-from-real-feedback as a design pattern**, distinct from KB-as-static-corpus.
[Sketch2Simulation](../paper-notes/2603.24629v1.md) implements the same pattern at the pipeline level: a typed
JSON-graph IR is the contract between parsing and synthesis.

This connects directly to Linus's [memory synthesis](memory-synthesis.md). The Kosmos-style task-scoped working state
that sits between scratchpad (ephemeral) and episodic (durable) is now named and decided: **Layer D — Investigation
memory** (DEC-0052), with a single-investigation lifetime, a multi-agent read/write contract, and SQLite substrate keyed
by `investigation_id`. The five-layer pillar (A–E; Layer E is the new name for semantic knowledge) supersedes the
earlier four-layer design, with investigation memory exactly filling the gap this paper set identified. The HKUST
QuantAgent's outer-loop KB-update pattern adds a second observation: episodic memory keyed by _(problem, attempt,
real-world-outcome, review)_ tuples is a domain-portable shape, and the spawner should let a Role declare its episodic
schema as part of the role definition.

### Thread 4: validation as a per-stage spawner primitive, not an end-of-pipeline check

[Sketch2Simulation](../paper-notes/2603.24629v1.md) elevates this to its strongest architectural claim. JSON-schema
enforcement on every IR transition, a rule-based normalizer that is itself validator-and- rewriter, an execution agent
whose "deterministic Python runner + LLM-fix-loop on failure" pattern (B4) is directly portable to any Linus Worker
producing an executable artifact. The C2 ablation (remove normalizer) introduces hallucinated structural elements; C4
(no RAG) causes complete execution failure on Merox.

[BioGuider](../paper-notes/2026.02.09.704801v1.md) embeds validation through a separate testing agent that runs
candidate artifacts in a controlled environment. [Boiko/Gomes](../paper-notes/2304.05332v1.md) identified the same
pattern as the most important emergent behaviour: **tool error messages must be routed back to the Planner verbatim**.
[TradingAgents](../paper-notes/2412.20138v7.md)' risky/neutral/safe risk-management debate plus fund-manager approval is
the same pattern at the _decision_ level. [WikiAutoGen](../paper-notes/2503.19065v1.md)'s four-viewpoint self-reflection
is the _content-quality_ version: the draft is validated against four orthogonal rubrics before commit. The HKUST
[QuantAgent](../paper-notes/2402.03755v1.md)'s two-loop structure is yet another shape — fast cheap inner-loop judge for
bulk filtering, slow expensive outer-loop reviewer for ground-truth checking — mapping onto Maestro/Worker discipline
directly.

The application papers make the architectural commitment: validation is per-stage, not per-pipeline. Per-stage
validation hooks in the orchestration spawner (not the sandbox layer) with an execute → detect → fix pattern — the
fixer-agent as a separate Worker — have been adopted as the Phase 3 spawner design per S15. This is also where the
[Practical Guide](../paper-notes/2506.13023v1.md)'s component-level evaluation argument lands — the orchestration
layer's intermediate components need their own metrics rather than only an end-to-end pass/fail.

### Thread 5: the critic tier — model-level Maestro/Worker inside a single workflow

This thread was touched on in the prior synthesis (TradingAgents' heterogeneous backbone selection) but the expanded set
sharpens it. [WikiAutoGen](../paper-notes/2503.19065v1.md) is the clearest single statement: writer LMs are GPT-4o-mini,
the critic LM is GPT-o3-mini, deliberately chosen for stronger reasoning. The HKUST
[QuantAgent](../paper-notes/2402.03755v1.md) formalizes the same asymmetry across loops rather than roles: cheap
inner-loop judge, expensive outer-loop reviewer; as outer iterations accumulate the reviewer's signal trains the KB so
the cheap judge converges on it. [TradingAgents](../paper-notes/2412.20138v7.md) matches expensive deep-thinking models
to high-stakes roles and cheap fast models to retrieval/formatting. [Boiko/Gomes](../paper-notes/2304.05332v1.md) used
GPT-4 as Planner and GPT-3.5 for web search — the earliest version.

For Linus this is the model-level analogue of Maestro/Worker discipline applied **inside** a single workflow. Local
Workers (Qwen2.5-Coder, Mistral-7B, future fine-tuned Linus) are the writer/inner-judge/specialist tier; hosted Claude
or a deterministic external check (compiler, test suite, KnowledgeBase fact lookup) is the critic/outer-reviewer tier.
The Role tuple should carry a `model_tier` field so the dispatcher knows whether a role is a writer, judge, or reviewer.
This sharpens the hosted-model-fallback question into something operational: not "do we ever call hosted Claude?" but
"which Roles are tagged as critic-tier, and what is the budget policy for them?"

The underlying methodological substrate for the Maestro/Worker discipline — and for the broader engineering-discipline
threads in this synthesis (parallel-by-default, push-well-specified-tasks-to-Workers, trust-the-OS-page-cache) — is
[Sutton 2019, _The Bitter Lesson_](../paper-notes/sutton_bitter_lesson.md). Sutton's argument that general methods that
leverage computation are ultimately the most effective is the underlying methodology for both the Algorithm (CLAUDE.md;
Musk via McNeill) and the Maestro/Worker discipline: Maestro attention is the scarce, expensive resource (analogous to
human-knowledge engineering); Worker compute is the abundant, cheap resource (analogous to search and learning at
scale). The discipline of preferring Worker dispatch where possible is the bitter-lesson discipline applied to Dan's
time. The Phase 3 multi-agent spawner (DEC-0050) and the parallel-by-default convention (CLAUDE.md) are the operational
realization.

### Thread 6: tool binding via per-tool documentation, not just function signatures

[Boiko/Gomes](../paper-notes/2304.05332v1.md) introduced the docs-searcher pattern: index hardware documentation with
embeddings, retrieve sections by vector search, compose a code snippet through a second LLM pass that retains function
signatures. Load-bearing for the Suzuki run because the heater-shaker module post-dated training cutoff.
[Sketch2Simulation](../paper-notes/2603.24629v1.md) institutionalises the same pattern: per-unit-type instruction files
encode COM-API conventions for each object class. The Stony Brook [QuantAgent](../paper-notes/2509.09995v3.md)'s
PatternAgent uses the same idea at smaller scale — an **in-prompt library of named patterns with concise descriptions**
matched against a rendered chart, essentially few-shot retrieval against a curated catalogue.

**Tool registration in Linus should ship a per-tool documentation artifact, not only a typed signature.** The signature
is what the schema-validator checks; the documentation is what the Worker reads to actually use the tool. This thread
also lands on a narrower KnowledgeBase pattern. Boiko's docs search, Sketch2Simulation's component-name RAG, and the
Stony Brook QuantAgent's pattern catalogue are all _vocabulary-grounding_ uses of retrieval — narrower than "answer
questions about my corpus." Linus's KnowledgeBase will have many such cases (gene names, paper IDs, chemical names, tool
argument canonicalisation); the Phase 2/3 retrieval design should treat vocabulary-grounding as a distinct query class
with its own quality target.

### Thread 7: hosted-frontier-model dependency is still the elephant in the room

[Kosmos](../paper-notes/2511.02824v2.md)'s throughput numbers are economical only at frontier-model capability.
[TradingAgents](../paper-notes/2412.20138v7.md) is OpenAI-only by design.
[Sketch2Simulation](../paper-notes/2603.24629v1.md) is hybrid: cloud Gemini for multimodal, local Qwen-Coder for code.
The HKUST [QuantAgent](../paper-notes/2402.03755v1.md) runs gpt-4-0125-preview throughout; the Stony Brook
[QuantAgent](../paper-notes/2509.09995v3.md) declines to name its backbone (itself a tell).
[WikiAutoGen](../paper-notes/2503.19065v1.md) is GPT-4o + GPT-4o-mini + GPT-o3-mini.
[Boiko/Gomes](../paper-notes/2304.05332v1.md) ran on GPT-4 + GPT-3.5. **The lone counter is
[BioGuider](../paper-notes/2026.02.09.704801v1.md)**, where GPT-OSS edged out Claude Sonnet, GPT-4o, and Qwen3 — the
most encouraging local-first data point in the group.

The architectural patterns transfer; the _quality_ at which they work on local 7-14B Workers is an open empirical
question. The honest read is twofold. First, **the Maestro/Worker discipline Linus already commits to is structurally
the right answer** — hosted Claude as Planner for high-stakes synthesis, local Workers for bulk execution. Second, **the
gap between demonstrated hosted-model agent capability and validated local-model agent capability is large enough that
adopting any architecture wholesale on faith is a mistake.** Each adopted primitive needs its own local-Worker
evaluation in `benchmarks/dan_tasks/` before being baked into the orchestration layer. The Sketch2Simulation hybrid
remains the most pragmatic template: route by modality and sensitivity.

The picture has shifted measurably in 2025, and [Kimi-K2](../paper-notes/Kimi-K2-2507.20534.md) is the load-bearing data
point. The primary architectural fold for Kimi-K2 lives in
[`native-low-bit-apple-silicon-synthesis.md`](native-low-bit-apple-silicon-synthesis.md) (1T-total / 32B-active MoE
topology, MuonClip-trained, weight-streaming target for Phase 6d, 1-bit / ternary candidate for Phase 8); the cross-link
belongs here because the agentic-benchmark numbers Kimi-K2 posts are the strongest single piece of evidence to date that
the hosted-vs-open-source agent-capability gap is closing fast. The instruct checkpoint scores 70.6 on τ²-Bench retail,
65.8 on τ²-Bench telecom, 76.5 on ACEBench, and 65.8% on SWE-bench Verified single-attempt agentic — the SWE-bench
number lands within striking distance of Claude Opus 4's 72.5% in the same single-attempt regime. These are open-source
SOTA on every agentic axis, achieved through a synthetic agentic-data pipeline (3,000+ real MCP tools

- rubric-paired tasks + RL with verifiable rewards) rather than through hosted-model post-training. For Linus the
  implication is concrete: the Phase 6 base-swap argument (Qwen3 → Kimi K2 LoRA seed, DEC-0055 seed) is no longer just a
  weight-streaming feasibility question — it is also a "do we want our local Worker to inherit Kimi K2's tool-use prior
  before LoRA?" question, and the answer is increasingly yes pending the streaming-feasibility measurements queued in
  Phase 6d. The architectural primitives this synthesis canonicalizes (typed AgentReport, role-as-first-class, per-stage
  validation hooks, critic tier) compose with that base swap rather than being orthogonal to it; what changes is the
  zero-shot floor a local Worker brings to the orchestration.

### Thread 8: theory shows up — the Bayesian-regret bound and what to make of it

The HKUST [QuantAgent](../paper-notes/2402.03755v1.md) is the only paper in the group with a substantive theoretical
contribution. It formalizes the inner loop as an MDP where state = context buffer, action = writer's answer or KB query,
reward = judge score. Two assumptions: (4.1) the LLM performs implicit Bayesian inference over the environment parameter
during in-context inference (Xie et al. 2021), and (4.4) the optimal policy on the simulated KB-environment can be
obtained via pessimistic value iteration (Jin et al. 2021). Lemma 4.3 gives inner-loop regret sublinear in T; Lemma 4.5
bounds outer-loop suboptimality by KB coverage uncertainty; Theorem 4.6 stitches them: total regret R(TK) sublinear in
KT.

Read against the [memory synthesis](memory-synthesis.md), this is a complementary kind of formal result at a different
stack level. The memory synthesis carries TC0 ceiling and chain-of-thought-as- polynomial-recursion results that
constrain the _substrate_. The QuantAgent regret bound constrains the _workflow_: a writer/judge/ reviewer loop with KB
grounding converges to optimality at sublinear regret in KT. Both are statements about _what is possible at all_, before
any tuning. The memory synthesis treats its formal results as first-class architectural inputs.

Should Linus treat agentic-system theory the same way? **Yes, with calibration.** The QuantAgent assumptions almost
certainly don't hold strictly in Linus's actual workloads, so the bound is not a guarantee but a design intuition: more
KB coverage → tighter regret. That intuition promotes to a design constraint: **when designing an agentic workflow with
a real-world feedback signal, prefer architectures where each iteration produces persistent KB enrichment**. The
parallel to the CoT findings is exact — prefer architectures that retain reasoning tokens, because retained intermediate
state is the dominant lever on expressivity. The practical recommendation is a brief "applicable theory" note in any
Phase 3 ADR on the agent spawner: which architectural choices have formal support, which are heuristic.

---

## Implications for Linus architecture

The Phase 2 orchestration layer needs to commit to several things that the current architecture documents either name
implicitly or defer. Pulling these together by the existing roadmap:

**Phase 2 — orchestration layer commitments.** **Role is a first-class type** in the Phase 3 agent spawner per DEC-0050:
minimum schema `{role_id, capability_set, memory_access_tier, critic_eligible}`, serializable to YAML, enforced at
dispatch. The `critic_eligible` field is the hook for the critic-stronger-than-writer pattern; the spawner should allow
episodic schema declaration per role for KB-grows-from-real-feedback patterns. **AgentReport is the canonical
inter-agent message format** per DEC-0051: `{task_id, role_id, status, result, rationale, evidence, timestamp}`,
free-form text confined to `rationale`, appended to the workgraph JSONL session store. The tool registry should ship
per-tool documentation artifacts alongside typed signatures. The audit log should record enough per-call detail that the
Practical Guide's non-determinism estimation can be applied retroactively. The default Worker reasoning loop should be
ReAct + Reflexion.

**Phase 3 — parallel agents.** The spawner's `≤N parallel rollouts per cycle` shape should target the Kosmos pattern,
with the Stony Brook QuantAgent's majority-with-confirmation rule as the cheap default integrator. Investigation memory
(Layer D per DEC-0052) is the shared-state artifact: SQLite-backed, keyed by `investigation_id`, shared read/write
across all agents in one investigation, archived to Layer C (episodic) on close. Natural starting specialization: two
general-purpose Workers (code/analysis, knowledge-retrieval) coordinated through Layer D. Per-stage validation hooks
(`pre_dispatch`, `post_synthesis`, `post_execution`) are exposed by the spawner; the execute → detect → fix pattern
(Sketch2Simulation B4) is the required default for any Worker producing an executable artifact. The HKUST QuantAgent's
two-loop self-improvement structure is a Phase 3 candidate template for any skill where ground-truth feedback is
programmatic.

**Sandbox and SAFETY.md.** Boiko/Gomes' dual-use safety study argues for **screening at prompt ingress, not action
egress**, and for an explicit "physical-world tool" class in the registry from Phase 2 (empty until Phase 7). The Stony
Brook QuantAgent's RiskAgent ("fixed safety floor + LLM-tunable parameter inside a hard range") is the cleanest
formulation of bounded-envelope autonomy in the corpus and worth lifting as a SAFETY.md formalism: every tool registered
as `(fixed_safety_bounds, model_tunable_params_within_bounds)`.

**Phase 7 — skills and autonomy graduation.** BioGuider remains the cleanest reference design for the _shape_ of a Linus
skill: bounded multi-agent workflow, named roles, constrained corrector, structured output, SKILL.md YAML-frontmatter
format (resolved S30/E6). The Phase 7 inaugural skills bundle is bioSkills + scientific-agent-skills (~573 skills
total). BioGuider's error-injection benchmark methodology is a reusable `dan_tasks/` family for any correction or
refactoring skill. The longer-term Phase 7 target remains a "Linus Kosmos-mode" deliverable.

**Memory pillar refinement.** _Investigation memory_ is now **Layer D** in the five-layer pillar (A–E) per DEC-0052.
Layer E is the new name for semantic knowledge throughout. The HKUST QuantAgent's outer-loop KB-update pattern adds:
episodic memory keyed by _(problem, attempt, real-world-outcome, review)_ tuples is domain-portable; the spawner should
let a Role declare its episodic schema. The [Fundamentals survey](../paper-notes/2510.09244v1.md)'s "procedures" content
type remains an open gap (episodic with a "generalized" flag? Layer E with a "procedural" type?) — resolve before Phase
3 fan-out; it is not covered by DEC-0052.

---

## Implications for Linus evaluation

The [Practical Guide](../paper-notes/2506.13023v1.md) is essentially the design document for `benchmarks/dan_tasks/`.
(BixBench and LAB-Bench moved to [`infra-foundations-synthesis.md`](infra-foundations-synthesis.md) as benchmark anchors
as of 2026-05-05; their agent-loop aspect is referenced from there. Practical Guide remains the central evaluation
anchor for Group D.)

The 5 D's apply item-by-item: **Defined Scope** (tag the Linus capability targeted), **Demonstrative** (Dan would
actually send the prompt), **Diverse** (topic/difficulty/format spread, embedding clustering), **Decontaminated** (Dan's
own work, post-cutoff or never-public), **Dynamic** (versioned, quarterly refresh). The sample-size formula
`n = z²·m̂(1−m̂)/ε²` gives ~246 items for 95% confidence at ε=5%. The balanced scorecard (ROUGE-L + embedding cosine

- NLI + autorater, never averaged) maps onto Worker selection. Hosted Claude as the Phase 1-2 autorater (Maestro
  budget); a hybrid policy (local default, escalate to Claude on disagreement) deserves its own ADR.

Two CI-gate measurements deserve permanent slots from Phase 1: **fictitious-entity hallucination probes** and
**non-response measurement** — paired metrics where suppressing one inflates the other. A biochem/genomics probe set is
also a plausible small public release.

The Kosmos three-statement-type rubric (data-analysis / literature / synthesis, supported / refuted / unsure) should be
adopted even at small scale for Phase 3+ autonomous-research benchmarks. BioGuider's controlled error-injection
methodology is reusable as a `dan_tasks/` family for any correction or refactoring skill. WikiAutoGen's WikiSeek
methodology — deliberately curate a benchmark of _underexplored_ topics — is a third reusable pattern, particularly
relevant for Dan's KnowledgeBase where most real synthesis lives in exactly that regime. A `dan_tasks/niche_synthesis/`
set of 30-50 thin-source topics would let Linus measure whether its degradation curve flattens (like WikiAutoGen's) or
drops sharply as topics get more obscure.

Three pre-Phase-2 measurements deserve highest priority. **Per-Worker debate-quality smoke test** — does TradingAgents'
bull/bear pattern beat single-Worker reasoning at equivalent token cost on local hardware? Adversarial debate as a
Worker primitive is deferred until this measurement exists (resolved S55/E4). **Per-Worker judge-fidelity smoke test** —
can a local 7B Worker play the HKUST QuantAgent's inner-loop judge with informative fidelity? Qwen3 is the Phase 1 local
judge for open-answer grading; hybrid escalation pattern is deferred (S12). **Per-Worker critic-tier smoke test** — does
WikiAutoGen's critic-stronger-than-writer pattern survive when both are local (larger Qwen2.5 critiquing smaller
Qwen2.5)? Each is hours of work and informs weeks of architecture.

**First empirical Worker-throughput data point (2026-05-16, PR #33).** The Phase 1d Dan task suite v0 collected its
first baseline against `qwen2.5-coder:7b` (qwen3:8b not yet pulled): three tasks completed in 55.75s wall — paper-
summarization (10.5s, full-credit on the MemGPT paper), fasta-gc-content (19.2s, partial — script counts `N` in the
denominator where the rubric says exclude), and title-clustering (26.0s, partial — only 36/50 input titles got assigned
to a cluster, a ~28% drop). Three observations relevant to the agentic-systems thread: (1) a 7B local Worker handles
short-context summarization at full quality, which is the easy regime; (2) the rubric-edge failure on FASTA (counting N)
is exactly the kind of partial-credit failure a critic-tier review pass would catch — a smoke-test for the
critic-stronger-than-writer pattern; (3) the 28% drop on title-clustering is a real coverage-vs-throughput signal — some
inputs got silently dropped rather than misclassified, suggesting an output-completeness check is a useful validation
gate for any classify-N-into-K task. Each becomes a real prior for spawner-stage validation-gate design.

**First Phase 2a orchestration runtime (2026-05-16, PR #32).** `src/linus/server.py` now ships an OpenAI-compatible
FastAPI bootstrap with an Ollama backend — the Worker-dispatch surface this synthesis has been writing against now
exists in code. The Anthropic-compat surface per DEC-0056 is the immediate next deliverable; combined the two endpoint
families share the same internal `LinusRequest`/`LinusResponse` pair and the same Worker dispatch beneath, so the Phase
3 spawner work (DEC-0050 Role, DEC-0051 AgentReport, DEC-0052 investigation memory) builds on a runtime that is no
longer hypothetical.

---

## Tensions and open questions

**1. Should Role be a first-class type in the Phase 3 agent spawner?** _Resolved (DEC-0050, see
[answered-questions.md](../questions/answered-questions.md)): Yes. Role is a first-class Python type with minimum schema
`{role_id, capability_set, memory_access_tier, critic_eligible}`, serializable to YAML, enforced at spawner dispatch._

**2. Should Linus name a fifth memory layer for "investigation memory"?** _Resolved (DEC-0052, see
[answered-questions.md](../questions/answered-questions.md)): Yes. Layer D — Investigation memory — added to the
five-layer pillar (A–E). SQLite substrate, `investigation_id`-keyed, shared read/write across all participating agents,
archived to Layer C on close. Layer E is now the name for semantic knowledge._

**3. Does Linus need a "validation gate" primitive in the spawner, or is that the sandbox layer's job?** _Partially
resolved (S15): Per-stage validation hooks sit in the orchestration spawner, not the sandbox. The execute → detect → fix
pattern with a fixer-agent as a separate Worker is the Phase 3 design. Sandbox policy enforcement (DEC-0024) is
complementary but distinct._

**4. Is "12-hour autonomous Linus run on a Dan-supplied dataset" the right Phase 7 north-star?** Concrete, falsifiable,
inherits Kosmos's evaluation. Honest concern: gated on hosted-model-class capability local Workers may not reach on M1
Max.

**5. What is Linus's policy on hosted-model fallback?** The critic-tier thread reframes this: not "do we ever call
hosted Claude?" but "which Roles are tagged as critic-tier and what is the budget policy?"

**6. Should adversarial debate be a Worker primitive?** _Partially resolved (S55/E4): Deferred to empirical testing. Do
not architect a debate primitive until there is measurement data on quality lift from `benchmarks/dan_tasks/`. The
majority-with-confirmation integrator (Stony Brook QuantAgent) is the architectural default pending that data._

**7. Typed inter-agent message format?** _Resolved (DEC-0051, see
[answered-questions.md](../questions/answered-questions.md)): Typed `AgentReport` is the canonical inter-agent message
format: `{task_id, role_id, status, result, rationale, evidence, timestamp}`. Free text confined to `rationale`.
`status: "partial"` handles incomplete-but-useful Worker results. Records appended to workgraph JSONL session store._

**8. Should agentic-system theory join memory-pillar theory as first-class architectural input?** The HKUST QuantAgent
regret bound is the first formal result in the group. Assumptions don't hold strictly, but the design intuition (KB
coverage growth as dominant lever on suboptimality) is worth promoting to a design constraint. A brief "applicable
theory" note in the Phase 3 spawner ADR.

### Industry harness-engineering signals and the multi-agent safety surface (added 2026-05-16, wave-2 stragglers fold-in)

Three wave-2 additions extend the agentic-systems thread along two independent axes. On the **harness-engineering**
axis, [`symphony`](../repo-notes/symphony.md) (OpenAI, Apache-2.0) is the cleanest modern published reference for a
polling-tracker-plus-isolated-workspace agent dispatch loop: a language-agnostic SPEC.md with RFC 2119 normative
language, a full domain model (Issue / WorkflowDefinition / Workspace / RunAttempt / LiveSession / RetryEntry /
OrchestratorState), and an Elixir reference implementation. The load-bearing innovation is keeping workflow policy
in-repo as a single `WORKFLOW.md` file with typed YAML front matter plus a Liquid-templated prompt body, with the
orchestrator trusting the repo's policy over any external config; this joins
[`goose`](../repo-notes/goose.md)'s Recipe DSL and [`Letta`](../repo-notes/Letta.md)'s Agent File as the three
reference task-spec shapes the Phase 3 spawner-spec ADR should motivate against. Cross-vendor signal: combined with
goose (Block / AAIF) and claw-code (Anthropic), symphony's existence and its explicit reference to OpenAI's published
"harness engineering" framing confirms that the harness is the layer of public-spec convergence between the leading
model vendors. On the **multi-agent safety** axis, [`swarm`](../repo-notes/swarm.md) (paired with the new paper-note
[`swarm-2604.19752`](../paper-notes/swarm-2604.19752.md)) introduces the population-level / soft-label framework
explicitly missing from the existing competence-focused thread (Kosmos, BioGuider, Sketch2Simulation): every agent
interaction carries a soft probabilistic label `p = P(v = +1) ∈ [0, 1]` derived from a calibrated sigmoid over four
observable proxy signals (`task_progress`, `rework_count`, `verifier_rejections`, `engagement`), and the population-
level metrics (toxicity rate `E[1−p | accepted]`, quality gap `E[p | accepted] − E[p | rejected]`, illusion delta
`Δ_illusion = C_perceived − C_distributed`) surface emergent failure modes binary `safe/unsafe` thresholds miss. The
seven canonical scenarios with five-seed replication are the worked methodology for Phase 3 multi-agent stress-tests
once the spawner ships. The **`AdversarialRedTeam`** scenario (welfare collapses from 181 to 110 as the ecosystem
fractures) and the **`ThresholdDancer`** scenario (welfare 354.80 — highest of any scenario — at toxicity 0.353,
exposing binary-threshold blind spots agents mathematically exploit) are the canonical adversarial-pressure tests the
Phase 3 spawner-spec stress-test suite should crib. Together the three additions confirm that Phase 3+ Linus needs
both a published task-spec contract (symphony's `WORKFLOW.md` shape) and a published safety-measurement contract
(swarm's soft-label pipeline); both are Phase 3 spawner-spec ADR inputs from complementary angles.

---

## Where this synthesis fits

This synthesis reinforces the [memory synthesis](memory-synthesis.md)'s argument that structured addressable state is a
load-bearing primitive — every paper in this group depends on some version of it. The two refinements it contributed are
now resolved: Layer D (investigation memory, DEC-0052) and the per-Role episodic schema pattern keyed by _(problem,
attempt, real-world-outcome, review)_ tuples from the HKUST QuantAgent's KB-feedback pattern. The five-layer pillar
(A–E) replaces the earlier four-layer design, with Layer E now naming semantic knowledge.

It reinforces the [skills synthesis](skills-and-practices-synthesis.md)'s argument that the bottleneck has shifted from
intelligence to clarity — TradingAgents' role tuples, BioGuider's per-agent constraints, Sketch2Simulation's per-tool
instruction files, and the Stony Brook QuantAgent's in-prompt pattern library are all "encode standards in files, not in
prompts."

It adds the evaluation discipline explicitly. The [Practical Guide](../paper-notes/2506.13023v1.md) prevents
architectural primitives from being adopted on hosted-model-flavoured hand-waving. WikiAutoGen's WikiSeek methodology
adds a specifically Linus-relevant pattern: deliberately thin-source benchmarks for synthesis tasks.

It extends the synthesis-landscape's treatment of formal results. Memory-pillar theory (TC0 ceiling,
CoT-as-polynomial-recursion) was the first formal-results entry in Linus's architectural input stream. The HKUST
QuantAgent regret bound is the first agentic-system-theory entry, arguing for a parallel discipline at the workflow
layer.

It is silent on the security thread that the [security synthesis](security-synthesis.md) carries; Boiko/Gomes is the one
overlap (ingress-side prompt screening for SAFETY.md). It is silent on inference efficiency — these papers are about
coordination, not inference cost, with the only connection being the Maestro/Worker model-routing argument.

The natural next read is the Phase 3 ADR on the agent spawner: which primitives become first-class commitments, which
become opt-in patterns, which become explicit non-commitments pending benchmark data. The eight open questions above are
the input to that ADR.

---

## Inputs

The ten paper-notes synthesised here, all in [`docs/paper-notes/`](../paper-notes/):

- [2511.02824v2](../paper-notes/2511.02824v2.md) — Mitchener et al., _Kosmos: An AI Scientist for Autonomous Discovery_
  (Edison Scientific / FutureHouse, 2025).
- [2304.05332v1](../paper-notes/2304.05332v1.md) — Boiko, MacKnight & Gomes, _Emergent autonomous scientific research
  capabilities of large language models_ (Carnegie Mellon, 2023).
- [2026.02.09.704801v1](../paper-notes/2026.02.09.704801v1.md) — Ma et al., _A multi-agent platform for assessment and
  improvement of bioinformatics software documentation_ (BioGuider; Ohio State, 2026).
- [2603.24629v1](../paper-notes/2603.24629v1.md) — Bahamdan et al., _Sketch2Simulation: Automating Flowsheet Generation
  via Multi-Agent Large Language Models_ (Imperial College London / BYU, 2026).
- [2412.20138v7](../paper-notes/2412.20138v7.md) — Xiao, Sun, Luo & Wang, _TradingAgents: Multi-Agents LLM Financial
  Trading Framework_ (UCLA / MIT / Tauric Research, 2025).
- [2510.09244v1](../paper-notes/2510.09244v1.md) — de Lamo Castrillo, Gidey, Lenz & Knoll, _Fundamentals of Building
  Autonomous LLM Agents_ (UPC / TUM, 2025).
- [2506.13023v1](../paper-notes/2506.13023v1.md) — Rudd, Andrews & Tully, _A Practical Guide for Evaluating LLMs and
  LLM-Reliant Systems_ (Google, 2025).
- [2402.03755v1](../paper-notes/2402.03755v1.md) — Wang, Yuan, Ni & Guo, _QuantAgent: Seeking Holy Grail in Trading by
  Self-Improving Large Language Model_ (HKUST / IDEA Research, 2024). _Two-loop self- improving framework with
  Bayesian-regret bound; the only theoretical contribution in the group._
- [2509.09995v3](../paper-notes/2509.09995v3.md) — Xiong, Zhang, Feng, Sun & You, _QuantAgent: Price-Driven Multi-Agent
  LLMs for High- Frequency Trading_ (Stony Brook / CMU / UBC / Yale / Fudan, 2025). _Same name as 2402.03755v1 but a
  different paper, different team, different scope: four-specialist + one-integrator LangGraph framework for HFT
  directional prediction._
- [2503.19065v1](../paper-notes/2503.19065v1.md) — Yang et al., _WikiAutoGen: Towards Multi-Modal Wikipedia-Style
  Article Generation_ (KAUST / Lanzhou / Sydney / A\*STAR, 2025).

Cross-references that were load-bearing without being part of Group D:

- [memory-synthesis.md](memory-synthesis.md) — the four-layer memory pillar this synthesis proposes extending with an
  "investigation memory" fifth layer; also the source of the formal-results discipline Thread 8 extends to
  agentic-system theory.
- [skills-and-practices-synthesis.md](skills-and-practices-synthesis.md) — the encode-standards-in-files discipline this
  synthesis grounds at the agent-spawner and tool-registry level.
- [synthesis-landscape.md](../landscapes/synthesis-landscape.md) — the aggregator this synthesis will be linked from.

---

## References

### Repo-notes

- [`everything-claude-code`](../repo-notes/everything-claude-code.md) — affaan-m's 182K-star agent-harness performance
  system; agent-file frontmatter as the cleanest reference for per-Worker role definitions (third corner of the
  task-spec / agent-state / role-definition triangle alongside goose Recipe + Letta Agent File). Continuous-learning
  hooks (`/learn` → `/evolve` → `/promote` → `/instinct-status`) relevant to the agent-improvement thread.
- [`goose`](../repo-notes/goose.md) — production Rust+MCP coding agent (Block / AAIF); Recipe DSL as one of the three
  reference task-spec shapes for the Phase 3 spawner.
- [`Letta`](../repo-notes/Letta.md) — productized MemGPT descendant; Agent File task-spec shape and Anthropic-compat
  endpoint reference.
- [`swarm`](../repo-notes/swarm.md) — System-Wide Assessment of Risk in Multi-agent systems framework; population-level
  soft-label safety substrate for Phase 3 stress-tests.
- [`symphony`](../repo-notes/symphony.md) — OpenAI engineering-preview harness; `WORKFLOW.md` policy-in-repo as third
  task-spec reference and issue-tracker-driven autonomous-dispatch entrant.

### Paper-notes

- [`2026.02.09.704801v1`](../paper-notes/2026.02.09.704801v1.md) — Ma et al., _BioGuider: A multi-agent platform for
  assessment and improvement of bioinformatics software documentation_ (Ohio State, 2026).
- [`2304.05332v1`](../paper-notes/2304.05332v1.md) — Boiko, MacKnight & Gomes, _Emergent autonomous scientific research
  capabilities of large language models_ (Carnegie Mellon, 2023).
- [`2402.03755v1`](../paper-notes/2402.03755v1.md) — Wang, Yuan, Ni & Guo, _QuantAgent: Seeking Holy Grail in Trading by
  Self-Improving Large Language Model_ (HKUST / IDEA, 2024); the only Bayesian-regret-bound theoretical contribution.
- [`2412.20138v7`](../paper-notes/2412.20138v7.md) — Xiao, Sun, Luo & Wang, _TradingAgents: Multi-Agents LLM Financial
  Trading Framework_ (UCLA / MIT / Tauric Research, 2025).
- [`2503.19065v1`](../paper-notes/2503.19065v1.md) — Yang et al., _WikiAutoGen: Towards Multi-Modal Wikipedia-Style
  Article Generation_ (KAUST, 2025); four-viewpoint critic-stronger-than-writer pattern.
- [`2506.13023v1`](../paper-notes/2506.13023v1.md) — Rudd, Andrews & Tully, _A Practical Guide for Evaluating LLMs and
  LLM-Reliant Systems_ (Google, 2025).
- [`2509.09995v3`](../paper-notes/2509.09995v3.md) — Xiong et al., _QuantAgent: Price-Driven Multi-Agent LLMs for High-
  Frequency Trading_ (Stony Brook / CMU / UBC / Yale / Fudan, 2025); minimal four-specialists + integrator template.
- [`2509.11420v1`](../paper-notes/2509.11420v1.md) — Xiao et al., _Trading-R1: Financial Trading with LLM Reasoning via
  Reinforcement Learning_ (Tauric / UCLA, 2025); RL-trained single-model collapse of TradingAgents orchestration.
- [`2510.09244v1`](../paper-notes/2510.09244v1.md) — de Lamo Castrillo et al., _Fundamentals of Building Autonomous LLM
  Agents_ (UPC / TUM, 2025); the eight-role taxonomy reference.
- [`2511.02824v2`](../paper-notes/2511.02824v2.md) — Mitchener et al., _Kosmos: An AI Scientist for Autonomous
  Discovery_ (Edison Scientific / FutureHouse, 2025); 12-hour autonomous research agent upper bound.
- [`2603.24629v1`](../paper-notes/2603.24629v1.md) — Bahamdan et al., _Sketch2Simulation: Automating Flowsheet
  Generation via Multi-Agent Large Language Models_ (Imperial / BYU, 2026).
- [`Kimi-K2-2507.20534`](../paper-notes/Kimi-K2-2507.20534.md) — Kimi Team, _Kimi K2: Open Agentic Intelligence_
  (Moonshot AI, 2025); open-source SOTA on agentic benchmarks; Phase 6d weight-streaming and Phase 6 LoRA-seed
  candidate.
- [`sutton_bitter_lesson`](../paper-notes/sutton_bitter_lesson.md) — Sutton, _The Bitter Lesson_ (2019); foundational
  methodological substrate for the Maestro/Worker discipline.
- [`swarm-2604.19752`](../paper-notes/swarm-2604.19752.md) — Aiersilan & Savitt, _Soft-Label Governance for
  Distributional Safety in Multi-Agent Systems_ (2026); paired with `repo-notes/swarm.md`.

---

_This synthesis is the input to the next round of edits to [paper-landscape.md](../landscapes/paper-landscape.md),
[synthesis-landscape.md](../landscapes/synthesis-landscape.md), [total-landscape.md](../landscapes/total-landscape.md),
and [open-questions.md](../questions/open-questions.md). It should be revisited when the Phase 3 agent-spawner ADR
lands, when the first BioGuider-style Linus skill ships, and whenever a new agentic-systems paper enters the corpus that
materially shifts one of the eight cross-cutting threads or adds a new one._
