# Agentic Systems Synthesis

## What this document is

A rewrite of the prior Group D synthesis, expanded from seven to thirteen paper-notes. This rewrite absorbs four new
papers — the two same-named-but-different _QuantAgent_ papers ([HKUST/IDEA, 2024](../paper-notes/2402.03755v1.md) and
[Stony Brook et al., 2025](../paper-notes/2509.09995v3.md)) and [WikiAutoGen](../paper-notes/2503.19065v1.md)
(KAUST, 2025) — and surfaces them as fresh evidence on threads that were present-but-quiet in the prior synthesis
(structured inter-agent communication, critic- stronger-than-writer, regret-bounded self-improvement). Tone matches the
[memory synthesis](memory-synthesis.md): prose-heavy, woven across papers, written to feed the next round of edits to
the landscape and questions documents.

The headline claim sharpens with the expansion: the agentic-systems literature has converged on a small set of
architectural primitives — role specialization, structured shared state, multi-level validation, per-tool documentation,
hybrid local/hosted-model routing, ReAct + reflection as the default loop, and a critic tier distinct from a writer tier
— and Linus's Phase 2/3 design is implicitly committing to most of them. The thirteen-paper version also promotes two
threads the seven-paper version under-weighted: structured inter-agent communication as a load-bearing primitive in its
own right, and the question of whether agentic-system theory (regret bounds, MDP formalism) deserves more weight in
Linus's design alongside the formal results that already anchor the memory pillar. The sober line under transferability
stays: most impressive results in this group lean on hosted frontier models in ways that don't transfer cleanly to a
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
only theoretical contribution (a regret bound); the Stony Brook QuantAgent supplies the leanest worked example of
structured-prompt multi-agent dispatch; WikiAutoGen sharpens the critic-stronger-than-writer thread.

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
not less. **The Phase 3 spawner should treat Role as a first-class type**, not as a convention. The Stony Brook
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

This connects directly to Linus's [memory synthesis](memory-synthesis.md). The four-layer pillar still has no explicit
slot for the Kosmos-style task-scoped working state that sits between scratchpad (ephemeral) and episodic (durable). The
expanded paper set strengthens the prior recommendation: a fifth layer worth naming explicitly — _investigation memory_
— with a single- investigation lifetime and a multi-agent read/write contract. The HKUST QuantAgent's outer-loop
KB-update pattern adds a second observation: episodic memory keyed by _(problem, attempt, real-world- outcome, review)_
tuples is a domain-portable shape, and the spawner should let a Role declare its episodic schema as part of the role
definition.

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

The application papers make the architectural commitment: validation is per-stage, not per-pipeline. **The agent spawner
should expose validation hooks per stage** (`pre_dispatch`, `post_synthesis`, `post_execution`) and require at least an
execution-validator, even if no-op for non-executable tasks. This is also where the
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

**Phase 2 — orchestration layer commitments.** The agent spawner's contract should treat **Role as a first-class type**
— a tuple of
`(name, goal, constraints, allowed_tools, model_tier, context_schema, position_in_workflow, episodic_schema)`. The role
tuple's `model_tier` field is the hook for the critic-stronger-than-writer pattern; `episodic_schema` is the hook for
KB-grows-from-real-feedback. The tool registry should ship per-tool documentation artifacts alongside typed signatures.
The audit log should record enough per-call detail that the Practical Guide's non-determinism estimation can be applied
retroactively. The default Worker reasoning loop should be ReAct + Reflexion. The canonical inter-agent message format
should be a typed `AgentReport` schema with free-form text confined to a named rationale field.

**Phase 3 — parallel agents.** The spawner's `≤N parallel rollouts per cycle` shape should target the Kosmos pattern,
with the Stony Brook QuantAgent's majority-with-confirmation rule as the cheap default integrator. The shared-state
artifact (investigation memory) deserves its own ADR before implementation. Natural starting specialization: two
general-purpose Workers (code/analysis, knowledge-retrieval) coordinated through the shared state. Multi-level
validation hooks (`pre_dispatch`, `post_synthesis`, `post_execution`) should be exposed by the spawner and required
(no-op acceptable). The execution-fix-loop pattern (Sketch2Simulation B4) is the required default for any Worker
producing an executable artifact. The HKUST QuantAgent's two-loop self-improvement structure is a Phase 3 candidate
template for any skill where ground-truth feedback is programmatic.

**Sandbox and SAFETY.md.** Boiko/Gomes' dual-use safety study argues for **screening at prompt ingress, not action
egress**, and for an explicit "physical-world tool" class in the registry from Phase 2 (empty until Phase 7). The Stony
Brook QuantAgent's RiskAgent ("fixed safety floor + LLM-tunable parameter inside a hard range") is the cleanest
formulation of bounded-envelope autonomy in the corpus and worth lifting as a SAFETY.md formalism: every tool registered
as `(fixed_safety_bounds, model_tunable_params_within_bounds)`.

**Phase 7 — skills and autonomy graduation.** BioGuider remains the cleanest reference design for a Linus _skill_. The
first non-trivial skill could plausibly be a documentation-review skill modeled on BioGuider, run against the Linus repo
itself as the smoke test. The longer-term Phase 7 target remains a "Linus Kosmos-mode" deliverable.

**Memory pillar refinement.** _Investigation memory_ as the fifth layer (task-scoped, multi-agent, single-investigation
lifetime). The HKUST QuantAgent's outer-loop KB-update pattern adds: episodic memory keyed by _(problem, attempt,
real-world-outcome, review)_ tuples is domain-portable; the spawner should let a Role declare its episodic schema. The
[Fundamentals survey](../paper-notes/2510.09244v1.md)'s "procedures" content type is a related gap deserving explicit
decision (fifth layer? episodic with a "generalized" flag? semantic-knowledge with a "procedural" type?) before Phase 3
fan-out.

---

## Implications for Linus evaluation

The [Practical Guide](../paper-notes/2506.13023v1.md) is essentially the design document for `benchmarks/dan_tasks/`.
(BixBench and LAB-Bench moved to [`infra-foundations-synthesis.md`](infra-foundations-synthesis.md) as benchmark
anchors as of 2026-05-05; their agent-loop aspect is referenced from there. Practical Guide remains the central
evaluation anchor for Group D.)

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
bull/bear pattern beat single-Worker reasoning at equivalent token cost on local hardware? **Per-Worker judge-fidelity
smoke test** — can a local 7B Worker play the HKUST QuantAgent's inner-loop judge with informative fidelity, or must the
judge be hosted Claude or a hardcoded checker? **Per-Worker critic-tier smoke test** — does WikiAutoGen's critic-
stronger-than-writer pattern survive when both are local (larger Qwen2.5 critiquing smaller Qwen2.5)? Each is hours of
work and informs weeks of architecture.

---

## Tensions and open questions

**1. Should Role be a first-class type in the Phase 3 agent spawner?** TradingAgents / BioGuider / Sketch2Simulation /
Stony-Brook-QuantAgent / WikiAutoGen all argue yes; Kosmos's two-role minimalism is the counter-data-point against
over-decomposition. The expanded paper set tilts strongly toward "yes." ADR before Phase 3.

**2. Should Linus name a fifth memory layer for "investigation memory"?** Kosmos world model, Sketch2Simulation IR, and
the HKUST QuantAgent context buffer all occupy a layer the four-layer pillar lacks (task-scoped, multi-agent,
single-investigation lifetime). Resolve before Phase 3.

**3. Does Linus need a "validation gate" primitive in the spawner, or is that the sandbox layer's job?**
Sketch2Simulation argues per-stage hooks make failures localizable; the HKUST QuantAgent two-loop judge/reviewer and
WikiAutoGen four-viewpoint critic block strengthen the case.

**4. Is "12-hour autonomous Linus run on a Dan-supplied dataset" the right Phase 7 north-star?** Concrete, falsifiable,
inherits Kosmos's evaluation. Honest concern: gated on hosted-model-class capability local Workers may not reach on M1
Max.

**5. What is Linus's policy on hosted-model fallback?** The critic-tier thread reframes this: not "do we ever call
hosted Claude?" but "which Roles are tagged as critic-tier and what is the budget policy?"

**6. Should adversarial debate be a Worker primitive?** Each round costs 2N+1 model calls; TradingAgents has no ablation
isolating debate. The Stony Brook QuantAgent is a partial counter — it works without debate, with
majority-with-confirmation as integrator. Empirical question for `benchmarks/dan_tasks/`.

**7. Typed inter-agent message format?** The expanded set makes this hard to defer — TradingAgents, both QuantAgents,
WikiAutoGen, BioGuider, and Sketch2Simulation all use typed structured outputs; only Kosmos hides the schema in a shared
state object. Default to typed `AgentReport` with free text confined to a named rationale field. ADR before the spawner
ships.

**8. Should agentic-system theory join memory-pillar theory as first-class architectural input?** The HKUST QuantAgent
regret bound is the first formal result in the group. Assumptions don't hold strictly, but the design intuition (KB
coverage growth as dominant lever on suboptimality) is worth promoting to a design constraint. A brief "applicable
theory" note in the Phase 3 spawner ADR.

---

## Where this synthesis fits

This synthesis reinforces the [memory synthesis](memory-synthesis.md)'s argument that structured addressable state is a
load-bearing primitive — every paper in this group depends on some version of it. It adds two refinements: a fifth
_investigation memory_ layer (task-scoped, multi-agent, single- investigation lifetime), and per-Role declared episodic
schemas keyed by _(problem, attempt, real-world-outcome, review)_ tuples from the HKUST QuantAgent's KB-feedback
pattern.

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

The thirteen paper-notes synthesised here, all in [`docs/paper-notes/`](../paper-notes/):

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

_This synthesis is the input to the next round of edits to [paper-landscape.md](../landscapes/paper-landscape.md),
[synthesis-landscape.md](../landscapes/synthesis-landscape.md), [total-landscape.md](../landscapes/total-landscape.md),
and [open-questions.md](../questions/open-questions.md). It should be revisited when the Phase 3 agent-spawner ADR
lands, when the first BioGuider-style Linus skill ships, and whenever a new agentic-systems paper enters the corpus that
materially shifts one of the eight cross-cutting threads or adds a new one._
