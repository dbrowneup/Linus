# swarm (`swarm-ai-safety/swarm`)

## 1. Purpose and scope

swarm is the **System-Wide Assessment of Risk in Multi-agent systems** framework: a Python research codebase plus a
published technical paper that together formalize "AGI-level risks don't require AGI-level agents" as a research
program. The paired paper-note ([`swarm-2604.19752.md`](../paper-notes/swarm-2604.19752.md)) covers the conceptual
contribution — replacing binary `safe / unsafe` agent classifications with **soft probabilistic labels**
`p = P(v = +1) ∈ [0, 1]` derived from a calibrated sigmoid over observable proxy signals, then computing **expected
toxicity** `E[1−p | accepted]` and **quality gap** `E[p | accepted] − E[p | rejected]` over the population of
interactions to surface emergent failure modes that no single agent produces in isolation. This repo covers the
**operationalization**: a Python 3.10+ MIT-licensed PyPI-distributed package (`swarm-safety` on PyPI) shipping ~23
agent archetypes (honest, opportunistic, deceptive, adversarial, adaptive-adversarial, cautious / cautious-
reciprocator, threshold-dancer, LDT, RLM, council, SkillRL, plus a full LLM-backed agent across 9 providers), 27+
configurable governance levers (transaction taxes, circuit breakers, reputation decay, random audits, staking,
collusion detection, dynamic friction, sybil detection, council governance, incoherence breaker, etc.), 79 YAML
scenario definitions, 39 runnable examples, 4,556 tests across 133 files, an append-only JSONL event-logger for
deterministic replay, eight framework bridges (Concordia, OpenClaw, GasTown, LiveSWE, Prime Intellect, Ralph, Claude
Code, Worktree), and a live HuggingFace Spaces interactive sandbox. The repo's tagline — "Other frameworks ask: 'Do
the agents behave well?' SWARM asks: 'Does the system still behave when humans stop noticing the cracks?'" — captures
the **illusion delta** metric (`Δ_illusion = C_perceived − C_distributed`) that is the framework's most distinctive
contribution. For Linus, this is the strongest existing reference for what a **multi-agent safety surface** looks like
in code, which is genuinely Phase 3 territory once the spawner ships, and a useful conceptual reference for the
Phase 3+ governance / sandbox / audit-log discipline already commits to via SAFETY.md and DEC-0047. The right
relationship is **Study** the patterns (soft-label metrics, governance-lever taxonomy, replay-based incoherence
detection, scenario YAMLs as a reproducible benchmark shape), surface the implications as Phase 3 spawner-spec
considerations, do not vendor as substrate.

## 2. Architecture summary

The repo is a substantial Python package: 23 agent types in `swarm/agents/` (~29 modules), 35 core modules in
`swarm/core/` (orchestrator, payoff engine, proxy computer, domain handlers), 27 governance lever modules in
`swarm/governance/`, 17 metrics modules in `swarm/metrics/`, plus subsystems for environments (`swarm/env/`,
16 modules), the consumer-seller marketplace (`swarm/csm/`, 10 modules), council governance (`swarm/council/`, 6
modules), skill learning (`swarm/skills/`, 6 modules), bridges to external frameworks (`swarm/bridges/`, 95 files
across 8 integrations), research-pipeline scaffolding (`swarm/research/`, 12 modules), red-teaming (`swarm/redteam/`),
boundaries (`swarm/boundaries/`, external-world flow tracking), analysis (`swarm/analysis/`, sweeps + plots +
dashboard), a FastAPI server (`swarm/api/`), forecasters for adaptive governance (`swarm/forecaster/`), a replay
runner (`swarm/replay/`), a YAML scenario loader (`swarm/scenarios/`), and a logging substrate
(`swarm/logging/event_log.py`). The README claims 4,556 tests across 133 files — a substantial test surface for a
research repo, suggesting the experimental claims are reproducible at scale. Authorship is academic (Aiersilan at
The George Washington University; Savitt at SWARM AI Safety, New York); the paper is currently a 2026 preprint
"Under review."

The **soft-label pipeline** is the load-bearing architectural element. Per the paired paper-note's §4 Method:
observable signals (`task_progress`, `rework_count`, `verifier_rejections`, `engagement`) flow into a `ProxyComputer`
(`swarm/core/proxy.py`) that aggregates them with default weights `w = (0.4, 0.2, 0.2, 0.2)` summing to 1 into a raw
proxy score `v_hat ∈ [-1, +1]`, then applies a calibrated sigmoid `p = 1 / (1 + e^(-k·v_hat))` with default `k = 2.0`
to produce a soft label `p = P(v = +1)`. The `SoftPayoffEngine` (`swarm/core/payoff.py`) computes expected surplus
`S = p·s⁺ - (1-p)·s⁻` and expected harm externality `E = (1-p)·h`, then applies per-agent payoffs:
`π_a = θ·S - τ - c_a - ρ_a·E + w_rep·r_a` for the initiator and the symmetric form for the counterparty. The
`SoftMetrics` module (`swarm/metrics/soft_metrics.py`) computes the four canonical metrics: **toxicity rate**
`E[1−p | accepted]`, **quality gap** `E[p | accepted] - E[p | rejected]` (a negative value indicates adverse
selection — the system preferentially accepts low-quality interactions), **conditional loss** (selection effect on
payoffs), and **incoherence** (variance-to-error ratio across replays).

The **23 agent types** are organized as separate modules under `swarm/agents/`, each implementing a `Policy` interface
that takes the current state and returns an action. Honest agents complete tasks diligently; opportunistic agents
maximize short-term payoff and cherry-pick tasks; deceptive agents build trust through honest behavior then exploit
trusted relationships; adversarial agents target honest agents and coordinate with allies; adaptive-adversarial
agents possess partial state observability and rehabilitate after circuit-breaker freezes; cautious and
cautious-reciprocator agents are risk-averse and play tit-for-tat; threshold-dancers are the most subtle archetype —
they explicitly program themselves to target a proxy score slightly above the freeze threshold, mathematically
scaling generation variables until `p ≈ θ_CB + ε`, exploiting binary governance boundaries without triggering them.
The LDT (Logical Decision Theory) agent uses UDT precommitment + opponent modeling; RLM (Reinforcement Learning
from Memory) learns from interaction history; council agents implement deliberative governance via the council
protocol in `swarm/council/`; SkillRL agents do reinforcement learning over an evolving skill repertoire; LLM agents
are configurable across 9 providers (Anthropic, OpenAI, Ollama, OpenRouter, Groq, Together, DeepSeek, Google,
llama.cpp).

The **27+ governance levers** in `swarm/governance/` each modify interaction costs, agent access, or reputation.
Transaction taxes apply a Pigouvian tax `τ_tax` to each interaction's transfer, split between initiator and
counterparty. Circuit breakers freeze an agent for `d` epochs when running toxicity exceeds `θ_CB` or accumulated
violations exceed `n_max`. Reputation decay applies `r ← λ·r` at each epoch boundary (preventing agents from coasting
on historical goodness). Random audits inspect with probability `p_audit` and apply penalty multiplier `m_audit` on
detection. Externality internalization `ρ_a, ρ_b ∈ [0, 1]` controls how much expected harm `E_soft` is borne by each
agent (`ρ = 0` externalizes all harm, `ρ = 1` fully internalizes). Staking requires a minimum deposit, with violations
triggering stake slashing at rate `α_slash`. Collusion detection monitors pairwise interaction frequency. Dynamic
friction is adaptive rate-limiting under stress. Sybil detection penalizes behaviorally similar clusters. Council
governance routes policy decisions through a multi-agent deliberative protocol. Incoherence breaker detects and
prevents incoherent policies. Ensemble governance composes multiple levers. The levers compose additively:
`c_a = c_a^tax + c_a^audit + c_a^stake + ...`. The full set extends with 16+ additional levers covering diversity,
transparency, decomposition, and memory governance.

The **scenario YAMLs** in `scenarios/` (79 built-in per the README) are the reproducibility substrate. Each scenario
is a YAML file declaring an agent composition (e.g., `3H+1O+1D` for 3 honest + 1 opportunistic + 1 deceptive), an
epoch count, a step count, and per-lever configuration. The paper's seven canonical scenarios (Baseline,
StrictGovernance, AdaptiveGovernance, AdversarialRedTeam, MisalignmentSweep, ThresholdDancer, CollusionDetection)
are seeded into the scenarios directory with the exact parameter values used in the paper experiments (tax rate,
CB threshold, audit probability, decay rate); the framework runs each scenario across five seeds (42, 123, 456, 789,
1024) and reports `mean ± std`. The scenario shape is portable beyond swarm: any researcher can add a YAML to
`scenarios/`, run `swarm run scenarios/<name>.yaml --seed 42 --epochs 20 --steps 15 --export-json runs/<run>.json`,
and get a deterministic JSONL event log under `runs/<timestamp>_<scenario>_seed<seed>/` for offline analysis.

The **replay-based incoherence detection** (`swarm/replay/`) is the framework's most novel measurement methodology.
The `IncoherenceMetric` computes `incoherence = Var[decision] / E[error]` across replayed decisions, surfacing whether
the agent's behavior is consistent across replays of the same input. The **illusion delta**
`Δ_illusion = C_perceived − C_distributed` then compares: `C_perceived = mean(p | accepted)` (how good the system
looks from the perceived/accepted-interaction lens) and `C_distributed = 1 − mean(disagreement across replayed
decisions)` (how consistent the system actually is across replays). A high illusion delta is the "electric-mind
regime" — locally fluent, globally fragile; a low illusion delta is genuinely stable. The framework's framing (citing
"Infinite Backrooms" in the README) is that this is the **systematic evaluation blind spot** binary safety frameworks
miss: humans over-trust systems that perform well in short-horizon interactions even when distributed evaluation
reveals substantial instability.

The **bridges** under `swarm/bridges/` (95 files across 8 integrations) connect swarm to external simulation
frameworks: Concordia (Google DeepMind's generative-agent simulator), Mesa (Python agent-based modeling library),
OpenClaw (the same project Linus is paired with at Phase 5), GasTown (gas-economy simulator), LiveSWE (live
software-engineering env), Prime Intellect, Ralph, Claude Code, and Worktree. The bridges let swarm's governance and
metrics layer wrap external agent simulations: feed external agent interactions through the soft-label pipeline,
score with the same metric set, run the same governance levers. This is the operational claim that "soft-label
governance transfers across simulation backends without architectural modification" — validated empirically per the
paper with Concordia entities and Claude / GPT-4o-Mini live LLM-backed agents (paper Table 7).

The **research-pipeline scaffolding** under `swarm/research/` includes a `track_a/` directory of formal research
runs, plus quality gates, platforms, and agents specific to research workflows. The `swarm autoresearch` CLI command
runs an experimental auto-research loop that mutates governance parameters, evaluates scenarios against an objective,
and records results to `runs/autoresearch/summary.json` — a meta-optimization layer over the framework. The
`swarm/forecaster/` module ships risk forecasters for adaptive governance (governance levers that adjust thresholds
based on predicted future state).

The repo also ships a **clawxiv bridge** (`docs/bridges/clawxiv.md` + `examples/clawxiv/export_history.py`) for
publishing safety-research preprints from agent-driven workflows — a notable agent-publishing surface that pairs
with the OpenClaw ecosystem (per the README). A live HF Spaces sandbox (`rsavitt-swarm-sandbox.hf.space`) is the
interactive demo path; a Streamlit dashboard under `examples/demo/app.py` is the local equivalent. The `make ci`
target runs lint + type-checking + tests; `pip install swarm-safety` is the canonical install. The licensing is MIT
throughout, the repo's `.claude/agents/` and `.claude/commands/` directories carry a complete Claude-Code-template
setup (custom slash commands, research-role specialist agents, optional git hooks, MCP integrations via `.mcp.json`),
and the CLAUDE.md is unusually disciplined ("Extend, don't proliferate" — explicit rule against creating new slash
commands when an existing one can absorb the functionality).

## 3. What's reusable in Linus

swarm's contribution to Linus is **conceptual + design-reference + methodology**, not substrate. swarm is genuinely
multi-agent research code; Linus's Phase 2/3 surface is single-Maestro + bounded-Worker-fan-out, which is much
narrower than the population-level agent ecosystems swarm targets. But several specific patterns from the framework
and the paired paper transfer to Linus's existing commitments around safety, audit, and Phase 3 multi-agent dispatch.

**Phase 3 — soft-label safety metrics as the Phase 3 multi-agent safety surface (DEC-0050, DEC-0051, DEC-0052,
SAFETY.md).** Once the Phase 3 spawner (DEC-0050) lands and Linus has multiple Workers running in coordination
(supervisor-fan-out, dynamic-dispatch, investigation-memory shared per DEC-0052), the **multi-agent safety surface**
becomes a first-class concern. swarm's contribution is the canonical soft-label framework: every Worker invocation
carries an observable proxy score (the Linus equivalent of `task_progress` is the Worker's reported success;
`rework_count` is retry-count from the audit log; `verifier_rejections` is failed-validator-checks from the
`AgentReport`; `engagement` is per-task complexity), and the population-level metrics (toxicity rate `E[1−p |
accepted]` over the Worker invocation distribution, quality gap `E[p | accepted] − E[p | rejected]` for adverse
selection) are computable from the same audit log. The Phase 3 spawner-spec ADR should name the soft-label pipeline as
the **safety-surface design reference** alongside the existing Garrison's framework that DEC-0028 names for memory
integrity, and the Phase 3 audit-log schema (per ARCHITECTURE.md's `~/.linus/audit.jsonl`) should grow the observable
proxy fields needed for the soft-label computation. Cost: a small extension of the audit-log row shape; upside: a
quantitatively-grounded multi-agent safety measurement surface from the moment Phase 3 ships, rather than retrofitted
later.

**Phase 3 — `illusion delta` as the multi-agent loop coherence metric (DEC-0035 ARC-AGI as memory diagnostic;
DEC-0034 worker-size vs. CoT-length comparison).** The `Δ_illusion = C_perceived − C_distributed` metric is the
sharpest existing operationalization of "the agent looks good in short interactions but is unstable across replays."
For Linus Phase 3 multi-agent loops, this maps onto: `C_perceived` = mean confidence reported by the Worker on
accepted outputs; `C_distributed` = `1 − mean(disagreement across N replays with different seeds)` for the same
input. A high illusion delta on a Linus Worker indicates the Worker is fluent-but-unstable; a low illusion delta
indicates genuine stability. This is a **new measurement axis** the Phase 1c+ Worker benchmarks (DEC-0034, DEC-0035)
do not yet cover — function-calling reliability, instruction-following reliability, scratchpad-durability are about
the Worker's per-call competence, but the illusion-delta is about **distributional consistency**. Worth promoting to
the Phase 1c spike spec as an additional measurement.

**Phase 3 — governance-lever taxonomy as the Phase 3 spawner-spec safety vocabulary (SAFETY.md, DEC-0047).** swarm's
27+ governance levers are organized into a small taxonomy (cost-applied levers like transaction taxes; access-applied
levers like circuit breakers and staking; reputation-applied levers like decay and audits; detection levers like
collusion / sybil / incoherence; deliberative levers like council governance). Linus's Phase 3 spawner-spec safety
surface needs a comparable vocabulary: **cost levers** (per-Worker token budget caps per DEC-0031; per-task wallclock
caps per CLAUDE.md "Measure, don't just estimate" convention); **access levers** (autonomy tiers from SAFETY.md;
biosecurity tiers from DEC-0047); **reputation levers** (a Phase 3+ candidate — Worker registry property that decays
on observed failures); **detection levers** (the soft-label pipeline above, plus the existing audit-log inspectors);
**deliberative levers** (Phase 3+ candidate — when two Workers disagree on a task result, escalate to a third Worker
acting as a "council" arbiter per swarm's `swarm/council/` pattern). Worth a one-paragraph addition to the Phase 3
spawner-spec ADR naming the five-category vocabulary.

**Phase 3 — replay-based determinism discipline (CLAUDE.md "Measure, don't just estimate" + DEC-0029).** swarm's
scenario-YAML-plus-seed reproducibility shape (`swarm run scenarios/baseline.yaml --seed 42 --epochs 20`) is the
worked example of "experiments are reproducible from scenario YAML + seed + exported history/CSVs." Linus's Phase
1c+ benchmark suite should adopt the same shape: each benchmark is a YAML file under `benchmarks/dan_tasks/`
declaring the task spec + Worker + seed; the runner produces a deterministic JSONL event log under
`benchmarks/results/<timestamp>_<scenario>_seed<seed>/` for offline analysis. The CLAUDE.md "Faithful reporting"
convention (which swarm's CLAUDE.md also articulates) is the discipline rule that anchors this: report what actually
happened, not what was hoped for. swarm's `runs/<timestamp>_<scenario>_seed<seed>/` directory structure is directly
portable to Linus's `benchmarks/results/` layout.

**Phase 3 — scenario-driven adversarial-pressure testing as the Phase 3 Worker-coordination stress test.** swarm's
`AdversarialRedTeam` scenario (4 honest + 2 adversarial + 2 adaptive-adversarial agents, 20 epochs, 15 steps) is the
canonical multi-agent adversarial-pressure shape. The paper's empirical finding — "the adversarial red team scenario
inevitably collapses the ecosystem after initial exploitation, yielding significantly reduced cumulative welfare
(110.12 vs. 181.38)" — is the kind of result Linus's Phase 3 multi-agent spawner needs to stress-test against before
shipping to production. The Linus equivalent is "what happens when one Worker in a supervisor-fan-out becomes
adversarial / deceptive / opportunistic?" The Phase 3 stress-test spec should include this scenario class. The
**MisalignmentSweep** scenario (4 honest + 2 opportunistic + 2 adversarial + 1 deceptive + 1 cautious; runs over a
range of externality-internalization values `ρ ∈ {0.0, 0.1, 0.3, 0.5, 0.7, 1.0}`) is a worked example of how to
parameterize an ablation sweep over a key governance lever; the methodology is directly portable to Linus's Phase 3
governance-lever ablations.

**Phase 5+ — OpenClaw bridge as a confirming signal for Phase 5 interoperability.** swarm ships a Concordia bridge,
a Mesa bridge, an OpenClaw bridge, and bridges to GasTown / LiveSWE / Prime Intellect / Ralph / Claude Code /
Worktree. The OpenClaw bridge specifically aligns with Linus's Phase 5 commitment to openclaw as the front-end
([openclaw repo-note](openclaw.md)). The bridge contract — swarm wraps external agent interactions, scores them
through the soft-label pipeline, applies governance levers — is a worked example of "external agent runtime, internal
safety measurement layer." For Phase 5+ Linus, this is the right shape for any future Linus-side multi-agent safety
measurement: the orchestration layer wraps Worker interactions, the safety layer scores them, the governance layer
applies levers. The pattern is portable; the specific OpenClaw bridge code is openclaw-specific.

**Phase 5+ — research-pipeline scaffolding as a reference for the Linus formal-research workflow.** swarm's
`swarm/research/` module ships a `track_a/` directory for formal research runs, quality gates, research-role
specialist agents (defined in `.claude/agents/`), and the `swarm autoresearch` auto-research loop CLI. For Linus's
own scientific workflow (Dan's actual deployment target — metagenomics analysis, paper synthesis, hypothesis
generation), this is the closest existing reference for "what does an LLM-augmented research workflow look like in
code." Worth studying the `.claude/agents/` setup (research-role specialists), the `swarm/research/quality_gates/`
implementations (how to gate research outputs against quality criteria before they enter the durable record), and
the `swarm autoresearch` loop (how to parameter-sweep over governance levers against an objective). This is a Phase 7
biology-skills-roadmap reference per [`biology-phase7-roadmap.md`](../specs/biology-phase7-roadmap.md), not a Phase 2
input.

**Phase 7+ — `BioReason-Pro`-style typed structured prediction for safety outputs (per CLAUDE.md §Typed structured
prediction).** swarm's soft-label output `p ∈ [0, 1]` plus the structured proxy fields (`task_progress`,
`rework_count`, `verifier_rejections`, `engagement`) plus the governance-lever costs (`c_a^tax`, `c_a^audit`,
`c_a^stake`) constitute a fully typed structured-prediction shape for safety classification. This is exactly the
shape CLAUDE.md §Typed structured prediction commits to for biology skills (BioReason-Pro template); swarm
demonstrates the same shape works for safety classification. For Phase 7+ Linus skills that produce safety-relevant
predictions (any skill that touches biosecurity per DEC-0047), the swarm shape — typed numeric prediction + named
provenance fields + machine-queryable rationale — is the right output contract.

## 4. What's inspiration only

The **scale of 23 agent types** is wider than Linus needs at Phase 3. The Linus Worker taxonomy will likely have a
much smaller v0 set (a handful of roles per DEC-0050, mostly distinguished by `cot_budget` and `memory_mode` plus
domain-specific tool surfaces rather than by behavioral archetype). swarm's distinction between honest /
opportunistic / deceptive / adversarial / threshold-dancer is the result of "what kinds of bad-actor behavior should
the framework be able to measure?" — that question's Linus equivalent is "what kinds of Worker failure should the
audit log detect?" which is a much narrower question. The specific archetype catalog is inspiration only; the
**behavioral discrimination axes** (cooperative vs. opportunistic; honest vs. deceptive; consistent vs. distributional-
unstable) port over.

The **multi-agent-simulation framing** is fundamentally different from Linus's Maestro/Worker discipline. swarm
assumes a population of N agents interacting over discrete epochs, with no central authority and emergent dynamics.
Linus assumes a central Maestro (Dan + hosted Claude) dispatching to Workers, with Workers reporting back, no
free-floating peer-to-peer interactions. The two are not the same problem class. swarm's framework applies to Linus
**only at Phase 3+ when multiple Workers are coordinating under a parent Maestro** — and even then, the Worker
interactions are mediated by the Maestro, not free-floating. swarm's framework is useful only as design reference,
not as architecture.

The **economic-equilibrium framing** (Akerlof / Glosten-Milgrom / Kyle citations, "lemons" problem, adverse-selection
spread, Pigouvian taxation) is a load-bearing rhetorical framework for the swarm paper but does not map directly onto
Linus's substrate. Linus is not a market; Workers do not trade with each other. The **information-economics
intuition** that "uncertainty in proxy signals enables adverse selection" ports over to Linus's audit-log analysis;
the specific economic vocabulary (taxes, transfers, externalities) does not.

The **bridges to Concordia / Mesa / GasTown / LiveSWE / Prime Intellect / Ralph** are research-framework interop
surfaces. None of these are Linus integration targets. The OpenClaw bridge is the only one directly relevant to
Linus, and even there the bridge is for swarm-side measurement of OpenClaw agents, not for OpenClaw-side consumption
of swarm.

The **LLM-backed agent configuration across 9 providers** (Anthropic, OpenAI, Ollama, OpenRouter, Groq, Together,
DeepSeek, Google, llama.cpp) is research breadth not Linus breadth. Linus targets local Workers (Ollama / mlx-lm /
Qwen3) as the default with hosted Claude as the Maestro upstream; the 9-provider catalog is inspiration only.

The **`swarm autoresearch` auto-research loop** is meta-optimization over governance parameters. For Linus's Phase 7+
scientific-research workflow, the meta-optimization concept is interesting but the swarm-specific loop is research-
framework-specific. Useful as design reference; not content to lift.

The **CLAUDE-Code-template setup** in `.claude/agents/` and `.claude/commands/` is a worked example of a Claude-Code-
template-style research repo. Linus's own CLAUDE.md is a different style (single-user, single-Maestro, prose-first);
swarm's "Extend, don't proliferate" discipline rule is the most directly portable convention — Linus could borrow
this as a convention for the `docs/skills/` and `docs/specs/` surfaces (don't create a new spec when an existing one
can absorb the change). Worth surfacing as a CLAUDE.md convention candidate.

## 5. What's incompatible or out of scope

**swarm is a multi-agent research framework, not an orchestration backend or harness (DEC-0017, DEC-0020).** swarm
**measures** multi-agent systems via the soft-label pipeline and applies governance levers as cost / access /
reputation modifications; it does not orchestrate the agents themselves (those are external). Adopting swarm as a
Linus substrate would invert this relationship and require the orchestration layer to be a multi-agent simulator,
which contradicts DEC-0020 (bounded scope) and the Maestro/Worker discipline (CLAUDE.md). The right relationship is
"Linus orchestration layer produces audit-log events that swarm-style metrics can score; swarm-style governance
levers can be implemented as policy on top of the audit-log surface, but they are not part of the orchestration
layer's primary responsibility."

**The population-level focus is a fundamental scope mismatch with single-user Linus.** swarm's framing is "AGI-level
risks don't require AGI-level agents" — emergent failure modes appear in populations of modest agents. Linus is
single-user, with a small fanout (Maestro + 2-4 concurrent Workers maximum on the M1 Max ceiling). The
population-level dynamics swarm studies (adverse selection over an ecosystem of N agents, illusion delta over many
replayed decisions, governance-lever calibration across 200+ interactions per scenario) do not have Linus analogues
at v0 + v1 scale. The framework's value to Linus is conceptual + methodological, not direct numerical measurement.

**The 27+ governance levers are over-engineered for Linus's Phase 3 surface.** Linus's Phase 3 spawner spec needs a
small, focused safety surface — a handful of cost / access / detection levers, not 27. The over-engineered surface is
appropriate for swarm's research role (parameter sweep across many levers to map the Pareto frontier of welfare-vs-
safety) but inappropriate for Linus's production role (a few well-chosen levers operating reliably). The right Linus
posture: cherry-pick the 4-6 most directly-applicable levers (per-Worker token cap, per-task wallclock cap, autonomy
tier, biosecurity tier, retry-on-failure-with-decay) for the v0 surface; defer the broader catalog to Phase 7+ when
the skills surface widens.

**The `under-specified acceptance mechanics` limitation is also a fundamental Linus mismatch.** The paper's
limitations section (page 14 of the PDF) explicitly names: "the exact thresholding rules and systemic dynamics
governing whether an interaction is 'accepted' or computationally simulated are simplified compared to complex
real-world platform curation logic." For Linus, "accepted" means "the Worker's output landed in the audit log" — much
simpler than swarm's economic-marketplace acceptance dynamics. The simplification works **in Linus's favor** (the
acceptance model is unambiguous) but means swarm's specific accept-reject modeling does not directly transfer.

**The `static agent response` and `fixed agent taxonomy` limitations also surface mismatches.** swarm uses rule-based
agents that treat governance levers as accounting penalties rather than as strategic constraints. The paper notes
that "real-world multi-agent deployment contexts inherently involve a fluid array of unknown agent types and unseen
behaviors." For Linus's Phase 3 Workers — which are LLM-backed and can in principle adapt to governance constraints
strategically — swarm's static-agent results are a **lower bound** on what governance lever ablations would show.
swarm's empirical claim that "strict governance reduces welfare 40% without improving safety" is honest for static
agents but may not survive adaptive LLM agents that can game the levers. The Phase 3 stress test should include
LLM-backed adversarial agents (per swarm's Validation Experiments Table 7 + the AdversarialRedTeam scenario), not
just static ones.

**The CLAUDE-Code-template scaffolding in `.claude/` carries opinionated conventions that don't match Linus's
CLAUDE.md.** swarm's CLAUDE.md "Extend, don't proliferate" + "Faithful reporting" + "Core principles are append-only"
are good conventions but encoded differently from Linus's CLAUDE.md (which is prose-first and convention-by-section).
The `.claude/agents/` research-role specialists and `.claude/commands/` slash-command set are swarm-specific and
should not be lifted directly. Pattern-borrow the conventions; do not vendor the scaffolding.

## 6. Recommendation: **Study**

Read the paired paper ([`swarm-2604.19752.md`](../paper-notes/swarm-2604.19752.md)) end-to-end for the conceptual
framework, then read the following modules in source: `swarm/core/proxy.py` and `swarm/core/payoff.py` for the
soft-label pipeline implementation; `swarm/metrics/soft_metrics.py` and `swarm/metrics/incoherence.py` for the metric
implementations including illusion delta; `swarm/governance/` for the lever taxonomy (specifically `transaction_tax`,
`circuit_breaker`, `reputation_decay`, `random_audit`, `staking`, `collusion_detection`); `swarm/agents/honest.py`
through `swarm/agents/threshold_dancer.py` for the archetype implementations (the threshold-dancer is the most
instructive — it shows what binary-governance evasion looks like in code); `swarm/scenarios/` for the YAML scenario
format and one of the baseline scenarios for the structure; `swarm/replay/` for the replay machinery. Skim
`swarm/bridges/openclaw/` for the OpenClaw-specific bridge as the closest Phase 5 reference. Skim the
`examples/quickstart.ipynb` Colab notebook for the canonical 5-minute demo path.

**Study** the patterns above (§3 What's reusable in Linus): soft-label safety metrics as a Phase 3 multi-agent safety
surface; illusion delta as a Phase 3 Worker-loop coherence metric; governance-lever taxonomy as the Phase 3 spawner-
spec safety vocabulary; replay-based determinism discipline for the benchmark suite; adversarial-red-team scenario
class as a Phase 3 stress-test reference; OpenClaw bridge as the Phase 5 interoperability pattern; research-pipeline
scaffolding as a Phase 7+ scientific-workflow reference; typed structured prediction for safety outputs as a CLAUDE.md
§Typed-structured-prediction confirming signal. Each is a small pattern lift; the lessons compound over Phase 3-7.

Do **not** vendor swarm. Do **not** adopt the population-level multi-agent framing or the 27-lever governance
surface. The architectural fit is wrong (swarm measures populations of free-floating agents; Linus orchestrates
Maestro/Worker pairs) and the scope fit is wrong (swarm is research breadth; Linus is single-user production). The
Python implementation is high-quality but is not the substrate Linus needs; the Linus implementation against the
patterns swarm names is a separate deliverable.

Cluster cell: [g11-agent-frameworks](../syntheses/repo-clusters/g11-agent-frameworks.md). swarm belongs in the
agent-framework cluster as the **multi-agent safety + governance research framework** that the cluster is otherwise
missing — the cluster's existing entries (autogen, langgraph, dspy, pydantic-ai, superpowers, lmnr, etc.) are mostly
about how agents are built, not about how agent **interactions** are measured for safety. swarm fills that gap.
Cross-cluster: swarm's bridges to OpenClaw and Concordia surface a secondary connection to
[g7-harnesses](../syntheses/repo-clusters/g7-harnesses.md), but the primary home is g11.

Primary thematic home: [`../syntheses/safety-alignment-privacy-synthesis.md`](../syntheses/safety-alignment-privacy-synthesis.md).
swarm is the strongest single existing reference for the multi-agent-safety axis that the synthesis names but does not
yet have a load-bearing example for. Secondary thematic home:
[`../syntheses/agentic-systems-synthesis.md`](../syntheses/agentic-systems-synthesis.md) for the population-level
agent-interaction framing as a complement to the Maestro/Worker thread that synthesis carries.

## 7. Connections

The primary fold is into [`../syntheses/safety-alignment-privacy-synthesis.md`](../syntheses/safety-alignment-privacy-synthesis.md).
swarm is the strongest single existing reference in the cloned corpus for **multi-agent safety measurement** — the
soft-label pipeline, the four canonical metrics (toxicity rate, quality gap, conditional loss, incoherence), the
illusion-delta metric, the 27-lever governance taxonomy, and the seven canonical scenarios are all named and
implemented. The synthesis currently treats safety as a single-agent-RLHF-plus-supply-chain axis; swarm adds the
**multi-agent / population-level** axis as a fifth axis alongside mechanism, values characterization, threat-model,
and design-policy. The synthesis should fold swarm in as the canonical reference for the new axis, with the paired
paper-note as the primary-source backbone.

The secondary fold is into [`../syntheses/repo-clusters/g11-agent-frameworks.md`](../syntheses/repo-clusters/g11-agent-frameworks.md).
swarm extends the cluster with a multi-agent safety + governance research framework that the existing entries do
not cover. The cluster synthesis should fold swarm in as the "what about how agent **interactions** are measured?"
entrant alongside the existing agent-building-focused entries; the fold-in is a single paragraph naming the soft-
label pipeline + the governance-lever taxonomy + the replay-based incoherence detection + the OpenClaw bridge as the
four load-bearing contributions.

The tertiary cross-references:

- [`../syntheses/agentic-systems-synthesis.md`](../syntheses/agentic-systems-synthesis.md) — swarm's population-level
  framing complements the Kosmos / BioGuider / Sketch2Simulation thread that synthesis carries. The discriminating
  axis: those papers are about agent **competence** (can the agent do the task); swarm is about agent **safety in
  population** (does the system still behave when agents interact). Cross-link the two threads at the synthesis's
  next revision.
- [`Letta.md`](Letta.md) §3 — the manager-taxonomy reference (`round_robin`, `supervisor`, `dynamic`, `sleeptime`,
  `voice_sleeptime`) is the Phase 3 spawner-spec design reference for **how the parent dispatches children**; swarm
  is the design reference for **how the parent measures children's interaction safety**. Both are Phase 3
  spawner-spec inputs; both should be named in the Phase 3 spawner ADR.
- [`goose.md`](goose.md) §3 — goose's `subagent_handler` + `subagent_execution_tool` machinery is the per-child-
  execution shape; swarm is the per-interaction-safety-measurement shape. Same Phase 3 spawner-spec context.
- [`symphony.md`](symphony.md) §3 (the WORKFLOW.md policy-in-repo idea) — swarm's scenario YAMLs are the
  reproducibility analogue: a per-scenario YAML in the research-repo declares the experiment, runs deterministically
  from seed + scenario + version of the framework. Both reinforce the "experiments + policies live in the repo, not
  in the orchestrator" discipline.
- [`openclaw.md`](openclaw.md) — swarm ships an explicit OpenClaw bridge; the Phase 5+ Linus + openclaw integration
  could plausibly use the swarm safety-measurement layer on the agent-interaction trace from openclaw. Cross-link in
  the Phase 5 planning notes.

Phase mapping: Phase 1c+ (replay-based determinism discipline for the benchmark suite; illusion-delta as a
distributional-consistency measurement axis); Phase 3 (soft-label safety metrics as the multi-agent safety surface;
governance-lever taxonomy as the spawner-spec safety vocabulary; adversarial-red-team scenario class as the stress-
test reference); Phase 5+ (OpenClaw bridge as the interoperability pattern); Phase 7+ (research-pipeline scaffolding
as a scientific-workflow reference; typed structured prediction for safety outputs as a confirming signal for the
CLAUDE.md convention). swarm surfaces as a **pattern + methodology reference**, not a substrate — the implementation
is multi-agent research code, not orchestration code, but the patterns the implementation embodies are directly
relevant to multiple Linus phases.

## 8. Questions for Dan

1. **Soft-label safety metrics as the Phase 3 multi-agent safety surface.** Once the Phase 3 spawner (DEC-0050) lands
   and multiple Workers run in coordination, the multi-agent safety surface becomes first-class. Should the Phase 3
   spawner-spec ADR commit to the soft-label pipeline (observable proxy → calibrated sigmoid → soft label `p` →
   toxicity / quality-gap / conditional-loss / incoherence metrics) as the canonical multi-agent safety measurement
   shape, with the audit log extended to carry the proxy fields needed for the computation? Tentative answer: yes —
   the discipline is well-formalized (per the paired paper), the cost is small (a few extra audit-log fields plus a
   metrics module on top), and the upside is a quantitatively-grounded safety measurement surface available from the
   moment Phase 3 ships. Worth a DEC alongside DEC-0050.

2. **Illusion delta as a Phase 1c+ Worker-benchmark measurement axis.** swarm's `Δ_illusion = C_perceived −
   C_distributed` is the sharpest existing operationalization of "the Worker looks good in short interactions but is
   unstable across replays." Should the Phase 1c spike spec
   ([`phase1c-spike.md`](../specs/phase1c-spike.md)) add illusion-delta as a measurement axis alongside the existing
   function-calling-reliability, instruction-following-reliability, and scratchpad-durability axes? Tentative answer:
   yes — the measurement is cheap (run the Worker N times on the same input with different seeds, compute
   `1 − mean(disagreement)`), and the diagnostic value is distinct (catches distributional-inconsistency, which the
   existing per-call axes do not). Worth adding to the Phase 1c+ benchmark suite.

3. **Governance-lever taxonomy as the Phase 3 spawner-spec safety vocabulary.** swarm's 27+ levers organize into a
   small taxonomy (cost-applied, access-applied, reputation-applied, detection-applied, deliberative). Should the
   Phase 3 spawner-spec ADR commit to the five-category vocabulary as the framing for Linus's own safety surface,
   even though Linus's v0 surface ships only 4-6 levers? Tentative answer: yes — the framing is durable beyond v0,
   and it gives Phase 7+ extensions a clear taxonomy to add into. Worth one paragraph in the Phase 3 spawner-spec
   ADR.

4. **Replay-based determinism discipline for the Phase 1c+ benchmark suite (CLAUDE.md "Measure, don't just
   estimate").** swarm's scenario-YAML-plus-seed reproducibility shape is directly portable to Linus's benchmarks.
   Should the Phase 1c+ benchmark suite under `benchmarks/dan_tasks/` adopt the YAML-per-task plus
   `benchmarks/results/<timestamp>_<scenario>_seed<seed>/` directory shape, with JSONL event logs as the canonical
   replay substrate? Tentative answer: yes — the shape is well-tested (swarm's 4,556 tests are a strong
   reproducibility signal), the cost is small (one YAML file per benchmark task + a per-run results directory), and
   the benefit (deterministic replay, offline analysis, third-party reproduction) is substantial. Worth committing
   to in the Phase 1c spec.

5. **AdversarialRedTeam scenario class as a Phase 3 stress-test reference.** swarm's adversarial-red-team scenario
   class is the canonical multi-agent adversarial-pressure shape. Should the Phase 3 multi-agent spawner stress-test
   suite include an analogous scenario class — "what happens when one Worker in a supervisor-fan-out becomes
   adversarial / deceptive / opportunistic / threshold-dancing?" Tentative answer: yes — the Phase 3 stress-test
   should include adversarial-Worker scenarios as a baseline test, with swarm's seven canonical scenarios
   (Baseline, StrictGovernance, AdaptiveGovernance, AdversarialRedTeam, MisalignmentSweep, ThresholdDancer,
   CollusionDetection) as the design reference for the stress-test scenario taxonomy.

6. **Typed structured prediction for safety outputs — confirming signal for CLAUDE.md §Typed-structured-prediction.**
   swarm's `p` plus the structured proxy fields plus the governance costs is exactly the typed-structured-prediction
   shape CLAUDE.md commits to for biology skills (BioReason-Pro template). Should the CLAUDE.md convention be
   reinforced — "typed structured prediction is the right shape for any prediction with auditability requirements,
   including safety classification" — with swarm cited as the safety-side confirming signal alongside BioReason-Pro
   on the biology side? Tentative answer: yes — the convention is durable, the cross-domain confirming signal
   reinforces the discipline, and the wording can be tightened in the next CLAUDE.md update.

7. **OpenClaw bridge as the Phase 5 interoperability reference.** swarm ships an explicit OpenClaw bridge
   (`swarm/bridges/openclaw/`) that wraps OpenClaw agent interactions, scores them through the soft-label pipeline,
   and applies governance levers. For Phase 5+ Linus's openclaw integration, this is the closest existing reference
   for "external agent runtime, internal safety measurement layer." Should the Phase 5 planning notes name swarm's
   OpenClaw bridge as the design reference for the eventual Linus + openclaw safety-measurement integration?
   Tentative answer: yes — cite the bridge in the Phase 5 ADR seed when the time comes; defer implementation to
   Phase 5+ when openclaw and Phase 3 spawner are both up.

8. **AGPL / MIT licensing posture across the recent multi-agent additions (cross-reference with
   `MiroFish-Offline.md`).** swarm is MIT-licensed throughout, which is Linus-compatible (DEC-0027 multi-language
   stance is licensing-agnostic, but MiroFish-Offline's AGPL-3.0 blocked code incorporation per the curation-log
   2026-05-10 entry). swarm joins Letta (Apache-2.0), goose (Apache-2.0), and Kimi-K2 (Modified MIT) as the recent
   open-source additions with permissive licenses; the cross-cluster picture is favorable. No specific action needed
   — just confirmation that the Phase 3 multi-agent design space is well-populated with permissively-licensed
   reference implementations Linus can study without IP friction.

9. **`Extend, don't proliferate` discipline as a CLAUDE.md convention candidate.** swarm's CLAUDE.md encodes a clean
   discipline rule: "Do not create new slash commands, agents, or hooks when an existing one can absorb the
   functionality. Prefer flags over files. Same rule for agents. Same rule for hooks. When in doubt, don't create."
   This is a portable convention for Linus's `docs/specs/`, `docs/skills/`, and `.claude/agents/` surfaces — the
   same urge to proliferate exists in Linus's structure and the same constraint serves it. Should CLAUDE.md add an
   "Extend, don't proliferate" convention to the Engineering Conventions section, citing swarm as the design
   reference? Tentative answer: yes — the convention is small, durable, and inexpensive to adopt. Worth one
   paragraph addition in the next CLAUDE.md update.
