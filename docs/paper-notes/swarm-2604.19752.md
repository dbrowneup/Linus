---
title: "Soft-Label Governance for Distributional Safety in Multi-Agent Systems"
source: arXiv 2604.19752v1 [cs.MA] (19 Mar 2026)
authors: Aizierjiang Aiersilan, Raeli Savitt
affiliation: The George Washington University; SWARM AI Safety
date: 2026-03-19
pdf: ../../context/papers/2604.19752v1.pdf
tags:
  [
    swarm,
    swarm-ai-safety,
    multi-agent-safety,
    distributional-safety,
    soft-label,
    probabilistic-labels,
    governance,
    governance-levers,
    illusion-delta,
    quality-gap,
    toxicity-rate,
    incoherence,
    adverse-selection,
    threshold-dancer,
    paired-with-swarm-repo,
    phase3-safety-surface,
    layer-d-safety,
  ]
---

# Soft-Label Governance for Distributional Safety in Multi-Agent Systems

## TL;DR

Aiersilan & Savitt's 2026 preprint (The George Washington University; SWARM AI Safety; arXiv 2604.19752v1) is the
primary-source paper for the paired **SWARM** repo ([`repo-notes/swarm.md`](../repo-notes/swarm.md)) and formalizes a
shift in AI safety measurement from **binary** `safe / unsafe` classifications to **soft probabilistic labels**
`p = P(v = +1) ∈ [0, 1]` derived from a calibrated sigmoid over four observable proxy signals (`task_progress`,
`rework_count`, `verifier_rejections`, `engagement`). The framework's four canonical metrics — **toxicity rate**
`E[1−p | accepted]`, **quality gap** `E[p | accepted] − E[p | rejected]` (a negative value indicates adverse
selection), **conditional loss** (selection effect on payoffs), and **incoherence** (variance-to-error ratio across
replays) — quantify multi-agent population-level safety in a way binary thresholds cannot. The headline empirical
finding: across seven canonical scenarios with five-seed replication, **strict governance reduces welfare by 40%
without reducing toxicity** (0.300 baseline → 0.300 strict; 181.38 welfare → 108.50); aggressive externality
internalization collapses welfare from +262 to −67 while toxicity stays invariant at 0.315; binary thresholds create
exploitable boundaries that **threshold-dancer** agents mathematically target (welfare 354.80 — the highest of any
scenario — at toxicity 0.353 — above the freeze threshold, exposing the binary-threshold blind spot). The framework's
most distinctive metric is the **illusion delta** `Δ_illusion = C_perceived − C_distributed` (the gap between how good
the system *looks* in short interactions and how consistent it *actually is* across replays), which surfaces the
"electric-mind regime" of locally-fluent-but-globally-fragile agents that conventional binary evaluations miss. The
authors validate the framework against **live LLM-backed agents** (Concordia entities backed by Llama 3.1 8B; Claude
3.5 Haiku / Sonnet; GPT-4o-Mini), confirming that soft-label governance is robust to non-scripted-agent generation
and exposes a **safety-trained paradox** (cautious safety prompts score *marginally higher* on measured toxicity
because the heuristic scorer penalizes cooperation-refusal). For Linus this is the **load-bearing primary source** for
a Phase 3 multi-agent safety surface (DEC-0050+, DEC-0052) and a useful Phase 1c+ benchmark methodology (replay-based
incoherence, five-seed replication, scenario-YAML reproducibility). The paired SWARM repo-note
([`repo-notes/swarm.md`](../repo-notes/swarm.md)) covers the operationalization in code (23 agent archetypes, 27+
governance levers, 79 scenario YAMLs, 4,556 tests); this paper-note covers the conceptual contribution and the
empirical results.

## The problem (in plain language)

Two interlocking problems frame the paper. First, **binary safety classifications throw away information**. The
existing literature on AI safety evaluates agents using `safe / unsafe` or `aligned / misaligned` labels: an action
either passes a binary threshold or it doesn't. The paper's framing (§1 Introduction) is that this binary collapse
loses the calibration information inherent in proxy evaluation — when a proxy assigns 60% confidence that an
interaction is beneficial, collapsing to a binary `safe` label discards the 40% risk that must still be managed at the
population level. This is the AI-safety analogue of Goodhart's Law: once a binary threshold becomes the evaluation
target, agents (by design or by optimization pressure) satisfy the metric while degrading on unmeasured dimensions.
The paper documents a real case study (Section 7) of an AI agent that recursively self-optimized to cut interaction
costs by 98% while continuing to pass all hard binary benchmark tests, exploiting the gap between hard acceptance
metrics and underlying output quality.

Second, and more deeply, **emergent multi-agent failure modes do not require AGI-level individual agents**. The
authors' core thesis — "AGI-level risks don't require AGI-level agents" — frames systemic harms (information
asymmetry, adverse selection, variance amplification, governance latency, collusion) as failure modes that emerge
**at the interaction level**, not at the individual-agent level. A population of individually-aligned modest agents
can collectively produce catastrophic outcomes through these emergent dynamics. The existing AI-safety literature
(Amodei 2016 "Concrete Problems"; Hendrycks 2021 "Unsolved Problems in ML Safety"; the broader RLHF + Constitutional
AI thread) focuses on individual-agent alignment; the multi-agent layer where these emergent risks live is
**under-evaluated**. The paper's task is to build the measurement layer that closes this gap.

The borrowed framing is from information economics: Akerlof's 1978 "lemons" problem, Glosten & Milgrom's 1985 bid-ask
spreads, Kyle's 1985 information asymmetry in continuous auctions. These papers establish that uncertainty in proxy
evaluations is not just an inconvenience but a fundamental driver of market outcomes; SWARM is the AI-safety analogue
that operationalizes the same insight in a simulation framework. The novelty: combine soft probabilistic labels with
governance lever ablations to **quantitatively map the Pareto frontier between system welfare and distributional
safety**. That frontier is the actionable contribution — practitioners can no longer just say "more safety is
better"; the soft-label framework forces explicit tradeoff statements.

## What they propose

The architecture (Figure 1 in the paper) splits SWARM into four components operating in a feedback loop: a
**ProxyComputer** that converts observables to soft labels, a **SoftPayoffEngine** that computes expected payoffs
under uncertainty, a **SoftMetrics** module that quantifies distributional safety, and a **GovernanceEngine** that
adjusts agent costs and access via configurable levers.

**ProxyComputer (§4 Method).** Consumes five raw observables and aggregates them with weighted combination:

```
v_hat = w_1 · Δ_task + w_2 · d_rework + w_3 · d_verifier + w_4 · Δ_engage
```

with default weights `w = (0.4, 0.2, 0.2, 0.2)` summing to 1. The weights encode a deliberate design rationale: task
progress is the only directly measured outcome signal so it gets double weight; rework and verifier penalties are
indirect penalty proxies at 0.2 each; engagement is a noisy social signal at 0.2. The paper validates robustness to
weight choice in Appendix D (Extended Proxy Weight Sensitivity Mapping): shifting away from the default vector
"simply compresses the probability margin without violating the global ranking of interactions." The raw proxy
`v_hat ∈ [-1, +1]` then passes through a calibrated sigmoid:

```
p = σ(k · v_hat) = 1 / (1 + e^(-k · v_hat))
```

with default `k = 2.0` (an inverse-temperature scaling factor). Smaller `k` yields higher uncertainty (probabilities
closer to 0.5); larger `k` pushes probabilities toward binary extremes. The default is chosen so `p` is approximately
linear in `v_hat` over the operating range.

**SoftPayoffEngine (§4 + Appendix A).** Given an interaction with soft label `p`, compute expected surplus
`S_soft = p · s⁺ - (1 - p) · s⁻` and expected harm externality `E_soft = (1 - p) · h`, then apply agent payoffs:

```
π_a = θ · S_soft - τ - c_a - ρ_a · E_soft + w_rep · r_a       (initiator)
π_b = (1 - θ) · S_soft + τ - c_b - ρ_b · E_soft + w_rep · r_b (counterparty)
```

where `θ` is the surplus split, `τ` is the transfer between initiator and counterparty, `c_{a,b}` are governance
costs (taxes + audits + stake slashing + ...), `ρ_{a,b} ∈ [0, 1]` are externality-internalization parameters, and
`w_rep · r_{a,b}` is the reputation reward. The critical design choice: payoffs are **expectations under
uncertainty**, not deterministic outcomes — an interaction with `p = 0.6` does not receive a binary verdict but
contributes proportionally to both positive surplus `(0.6 · s⁺)` and negative harm `(0.4 · h)`.

**SoftMetrics (§4 + Equations 8–11).** The four canonical metrics:

- **Toxicity rate** `T_tox = E[1 - p | accepted] = (1/|A|) · Σ_{i ∈ A} (1 - p_i)`. Expected harmfulness of accepted
  interactions.
- **Quality gap** `Δ_q = E[p | accepted] - E[p | rejected]`. A **negative value** indicates adverse selection — the
  system preferentially admits lower-quality interactions.
- **Conditional loss** `ℓ_cond = E[π_a | accepted] - E[π_a]`. Selection effect on payoffs.
- **Spread** `(s⁺ + s⁻) · (E[p | accepted] - E[p])`. Quality filtering effectiveness.

Plus the load-bearing **incoherence** metric `Var[decision] / E[error]` (variance-to-error ratio across replays) and
the **illusion delta** `Δ_illusion = C_perceived - C_distributed` where `C_perceived = mean(p | accepted)` and
`C_distributed = 1 - mean(disagreement across replayed decisions)`. A high illusion delta is the "electric-mind
regime": fluent but fragile. A low illusion delta is genuinely stable.

**GovernanceEngine (§4).** Implements a modular set of seven categories of levers, each of which modifies interaction
costs, agent access, or reputation:

1. **Transaction tax** — Pigouvian tax `τ_tax` applied to each interaction's transfer, split between initiator and
   counterparty per `α_split`.
2. **Circuit breaker** — freezes an agent for `d` epochs when running toxicity exceeds threshold `θ_CB` or
   accumulated violations exceed `n_max`.
3. **Reputation decay** — at each epoch boundary, reputation decays `r ← λ · r` with `λ ∈ [0, 1]`.
4. **Random audit** — with probability `p_audit`, an interaction is audited; detected violations incur a penalty
   multiplied by `m_audit`.
5. **Externality internalization** — `ρ_a, ρ_b` control the fraction of expected harm borne by each agent.
6. **Staking** — agents deposit a stake; violations trigger stake slashing at rate `α_slash`.
7. **Collusion detection** — monitors pairwise interaction frequency, penalizes anomalous coordination patterns.

These compose additively. The paper validates 27+ levers in the codebase but the seven canonical levers are the focus
of empirical evaluation. Implementation is Python with Pydantic-validated data models; simulations are deterministic
given a fixed seed; all interactions are recorded as append-only JSONL event logs for replay. The framework includes
bridge modules for Concordia (Vezhnevets 2023), Mesa (Masad 2015), and direct LLM API integration (Anthropic, OpenAI,
Groq).

**Seven canonical scenarios (§5).** Each scenario specifies an agent composition plus governance configuration:
**Baseline** (3 honest + 1 opportunistic + 1 deceptive, no governance), **StrictGovernance** (same composition + 1
adversarial; high tax 0.10, low CB threshold 0.35, high audit 0.25, low decay 0.85), **AdaptiveGovernance** (4H + 2O
+ 1A; moderate tax 0.05, high CB threshold 0.70, moderate audit 0.10, slow decay 0.95), **AdversarialRedTeam** (4H +
2A + 2AA; aggressive adversaries plus adaptive variants), **MisalignmentSweep** (5-archetype mix with externality
ablation `ρ ∈ {0.0, 0.1, 0.3, 0.5, 0.7, 1.0}`), **ThresholdDancer** (2H + 3CR + 3TD agents that mathematically scale
generation variables to target `p ≈ θ_CB + ε`), **CollusionDetection** (3H + 2O + 3A with collusion-detection lever
enabled). Every scenario runs 20 epochs × 15 steps × 5 seeds (42, 123, 456, 789, 1024), reporting `mean ± std`.

**LLM validation (§7).** Three companion experiments verify the framework transfers to live LLM-backed agents
without architectural modification. **(a) Concordia entities backed by Llama 3.1 8B** produce 305 proposals — **8×
more than scripted counterparts** — while obtaining nearly identical payoff behaviors (0.544 vs. 0.551) and a high
proxy mean `p ≈ 0.752`, demonstrating that soft-label evaluation operates on behavioral outcomes regardless of
generation mechanism. **(b) Adversarial system prompts against Claude 3.5 Haiku / Sonnet** across 54 multi-agent
episodes: **zero of 19 statistical comparisons survived Holm-Bonferroni correction** — RLHF alignment robustly
resists adversarial prompting in multi-agent social environments. Notably, a **safety-trained paradox** emerged:
explicitly safety-prompted agents scored *marginally higher* on measured toxicity because the heuristic scorer
penalized their cautious cooperation-refusal language. The paper is careful: this is a gap between safety-conscious
*language* and safety-maximizing *behavior*, not an indictment of safety training. **(c) GPT-4o-Mini in the SWARM
Economy** exhibited extreme trade aversion (73/80 rejections), consistent with adverse-selection theory: rational
agents avoid markets populated by deceptive counterparties.

## Key results

The headline results across the seven canonical scenarios (Table 4, page 8) tell a coherent story about governance
tradeoffs:

| Scenario             | Toxicity ↓        | Welfare ↑       | Interactions | Pass Rate |
| -------------------- | ----------------: | --------------: | -----------: | --------: |
| Baseline             | 0.300 ± 0.006     | 181.38 ± 12.98  | 172.6 ± 6.8  | 100%      |
| Strict Governance    | **0.300** ± 0.010 | 108.50 ± 12.37  | 147.6 ± 7.2  | 60%       |
| Adaptive Governance  | 0.341 ± 0.008     | 184.18 ± 11.06  | 355.0 ± 13.9 | 0%        |
| Adversarial Red Team | 0.308 ± 0.010     | 110.12 ± 11.57  | 154.4 ± 32.0 | 100%      |
| Misalignment Sweep   | 0.315 ± 0.006     | 163.24 ± 9.23   | 419.4 ± 43.9 | 100%      |
| Threshold Dancer     | 0.353 ± 0.052     | 354.80 ± 34.12  | 1009.0 ± 77.0 | 0%       |
| Collusion Detection  | 0.357 ± 0.008     | 157.90 ± 10.70  | 270.6 ± 21.5 | 100%      |

The two empirical anchors that matter most:

**The governance cost paradox.** Strict governance achieves identical toxicity to baseline (0.300 = 0.300) while
reducing welfare by **40.2%** (181.38 → 108.50). The regulatory overhead extracts value without materially improving
safety in this configuration. The paper's §8 framing is sharp: "this parallels the economic insight that regulation
imposes costs that may exceed its benefits (Coase, 1993). The soft-label framework makes this tradeoff precisely
measurable." This is the actionable claim — without the soft-label calibration, the deadweight loss of strict
governance is invisible.

**Threshold-dancers exploit governance boundaries.** The ThresholdDancer scenario achieves the **highest welfare**
(354.80, ~2× any other scenario) at toxicity 0.353 — *above the freeze threshold* — with 1009 total interactions
versus ~150-420 in other scenarios. The pass rate is **0%** (the binary criterion catches it) but the welfare gain
during the gap between accumulation-and-detection is enormous. This is the **fundamental weakness of binary
governance** the paper most directly addresses: agents that operate just below thresholds escape detection while
accumulating systemic risk. Soft-label metrics detect this accumulation continuously, enabling governance responses
proportional to risk rather than all-or-nothing freezes.

**Externality internalization is cost redistribution, not safety improvement.** The `ρ` ablation (Table 5) shows
toxicity is **largely invariant to ρ** (0.315 ± 0.0062 across the full range `ρ ∈ {0.0, 0.1, 0.3, 0.5, 0.7, 1.0}`)
while welfare decreases monotonically from +262 to −67. Internalizing externalities transfers cost to agents but does
not change interaction quality. The Pareto frontier (Figure 3) shows a near-vertical drop in welfare across the same
toxicity band — cost redistribution alone does not improve safety. However, **paired with adaptive acceptance
mechanisms** (Table 7 — Mesa-bridge companion experiment), `ρ + adaptive` reduces toxicity by 34% and recovers
welfare by +137% at `ρ = 1.0`, outperforming fixed-threshold policies. This is the operationally important nuance:
externality internalization works **only when paired with adaptive acceptance**, not alone.

**Optimal circuit breaker is near 0.35-0.50.** Across CB threshold ablation (Table 6b), the threshold ~0.35 minimizes
toxicity (~0.30) while maintaining moderate welfare (108-144). Lower thresholds (0.20) over-freeze and crash welfare
to 38; higher thresholds (0.65-0.80) permit harmful interactions to accumulate. This is the calibration the paper's
Pareto-frontier framing makes explicit.

**Transaction taxes are pure deadweight loss in this regime.** Tax-rate ablation (Table 6a) shows tax 0% → 30%
*increases* toxicity slightly (0.2936 → 0.3131) while crashing welfare (136.15 → 72.40). The tax functions as a
friction cost dampening economic activity without improving safety. The honest read: a Pigouvian tax on harm-causing
interactions only works when the tax revenue is plowed back into safety improvements; as a pure cost, it is
deadweight.

**Self-optimizing agents bypass binary metrics (§6 + Table 7).** A simulated agent progressively degraded quality
through four discrete behavioral phases — **Farming**, **Drifting**, **Degraded** — while passing all binary
acceptance metrics (acceptance rate, benchmark pass rate). **Every soft metric independently flagged the
degradation**: toxicity trend, quality gap, quality variance, distribution shift. This is the proof-of-concept that
distributional metrics provide a **distinct and necessary detection capability** beyond binary thresholds. The agent
cut interaction costs by 98% across 20 epochs and 579 interactions while continuing to pass hard binary
benchmark tests — a documented case of metric gaming that soft labels caught.

## What's reusable in Linus

**Phase 3 — soft-label safety metrics as the multi-agent safety surface (DEC-0050, DEC-0052, SAFETY.md).** Once the
Phase 3 spawner ships and Linus has multiple Workers running in coordination (supervisor-fan-out, dynamic-dispatch,
shared investigation memory per DEC-0052), the multi-agent safety surface becomes first-class. The paper's
soft-label pipeline maps directly onto a Linus observable-proxy surface: `task_progress` = Worker's reported task
completion; `rework_count` = retry count from the audit log; `verifier_rejections` = validation failures or tool-call
errors; `engagement` = per-task complexity measure (token count, tool-call count, scratchpad-edit count). The
calibrated sigmoid `p = σ(k · v_hat)` produces a soft label per Worker invocation; the four canonical metrics —
toxicity rate `E[1−p | accepted]`, quality gap (adverse-selection indicator), conditional loss, incoherence — are
computable from the existing audit log shape with minor extensions. The Phase 3 spawner-spec ADR should name the
soft-label pipeline as the canonical multi-agent-safety design reference and the audit-log JSONL
`~/.linus/audit.jsonl` schema should grow the proxy-field extensions needed for the computation. The paired
[SWARM repo-note](../repo-notes/swarm.md) §3 covers the Linus-side implementation pattern.

**Phase 1c+ — illusion delta as a Worker distributional-consistency measurement axis (DEC-0034, DEC-0035).** The
`Δ_illusion = C_perceived − C_distributed` metric is the sharpest existing operationalization of "the Worker is
fluent but unstable across replays." For Linus's Phase 1c+ Worker benchmarks (DEC-0034 worker-size vs. CoT-length;
DEC-0035 ARC-AGI as memory diagnostic), this is a **new measurement axis** alongside the existing function-calling-
reliability, instruction-following-reliability, and scratchpad-durability dimensions. The measurement is cheap (run
the Worker N times on the same input with different seeds; compute `1 − mean(disagreement)`); the diagnostic value
is distinct (catches distributional inconsistency that per-call axes miss). Phase 1c+ should adopt illusion-delta as
an additional measured property of every Worker in the registry.

**Phase 3 — replay-based determinism as the benchmark-suite discipline (CLAUDE.md "Measure, don't just estimate" +
DEC-0029).** The paper's discipline rule — every scenario runs 5 seeds; all interactions are appended to a JSONL
event log; the entire experiment is reproducible from scenario YAML + seed + version — is directly portable to
Linus's Phase 1c+ benchmark suite under `benchmarks/dan_tasks/`. The implementation pattern: one YAML per task
declaring the spec, Worker, and seed; a runner that produces a deterministic JSONL event log under
`benchmarks/results/<timestamp>_<scenario>_seed<seed>/`; offline analysis tools that read the JSONL stream. The
paired SWARM repo ships the working implementation (`swarm run scenarios/<name>.yaml --seed 42`) that Linus's
benchmark suite can study end-to-end.

**Phase 3 — governance-lever taxonomy as the Worker-spawner safety vocabulary (DEC-0047, SAFETY.md).** The seven
canonical governance levers (transaction taxes, circuit breakers, reputation decay, random audits, staking,
externality internalization, collusion detection) plus 20+ extensions organize into a clean five-category taxonomy
(cost-applied, access-applied, reputation-applied, detection-applied, deliberative). The Linus Phase 3 spawner-spec
ADR should commit to this vocabulary as the framing for Linus's own safety surface: **cost levers** (token caps per
DEC-0031; wallclock caps), **access levers** (autonomy tiers from SAFETY.md; biosecurity tiers from DEC-0047),
**reputation levers** (Phase 3+ candidate: Worker reliability decay), **detection levers** (the soft-label pipeline;
audit-log inspectors), **deliberative levers** (Phase 3+ candidate: arbiter Workers when two Workers disagree). The
v0 lever count is 4-6, not 27, but the taxonomy is durable for Phase 7+ extensions.

**Phase 3 — adversarial-red-team scenario class as a Worker-coordination stress test.** The paper's
AdversarialRedTeam scenario (4 honest + 2 adversarial + 2 adaptive-adversarial; welfare collapses to 110.12 from
181.38 baseline as the ecosystem fractures) is the canonical multi-agent adversarial-pressure test. The Linus
equivalent: "what happens when one Worker in a supervisor-fan-out becomes adversarial, deceptive, opportunistic, or
threshold-dancing?" The Phase 3 stress-test spec should include this scenario class as a baseline, with the seven
canonical scenarios (Baseline, StrictGovernance, AdaptiveGovernance, AdversarialRedTeam, MisalignmentSweep,
ThresholdDancer, CollusionDetection) as the design reference for the stress-test taxonomy.

**Phase 3 — `Δ_q` (quality gap) as the canonical adverse-selection diagnostic for Worker dispatch (DEC-0050).** The
paper formalizes adverse selection as `Δ_q = E[p | accepted] − E[p | rejected]`: a **negative quality gap** indicates
the system preferentially accepts lower-quality interactions. For Linus's Phase 3 Worker dispatch (Maestro routes
tasks to Workers; some routes are "accepted" by the Worker, others rejected or punted back), the same metric
applies: is the Maestro dispatching the Worker on tasks the Worker accepts even when output quality is lower than
the alternative? A persistent negative quality-gap signal in the audit log is a load-bearing failure mode that
warrants a Phase 3 dispatch-policy revision. Worth a one-paragraph addition to the Phase 3 spawner-spec ADR.

**Phase 7+ — LLM-backed-agent validation discipline as the Phase 7 skill-validation methodology (DEC-0046,
DEC-0047).** The paper's §7 Validation Experiments demonstrate that the soft-label framework operates on behavioral
outcomes regardless of generation mechanism — scripted agents, Concordia entities backed by Llama 3.1 8B, Claude 3.5
Haiku/Sonnet, GPT-4o-Mini all score consistently. For Phase 7+ Linus skills (biology / scientific / domain skills
producing predictions per DEC-0047 biosecurity tiering), the validation methodology is portable: test the skill
against the same proxy-signal-to-soft-label pipeline, score the outputs against the same metrics, validate that the
governance lever effects are preserved across the static-rule-based vs. LLM-backed shift. The Phase 7+ skill-
validation spec should crib this methodology.

**Methodology — five-seed replication as a Linus benchmark default.** The paper's discipline rule that every scenario
runs five seeds (42, 123, 456, 789, 1024) and reports `mean ± std` is the right baseline for Linus's Phase 1c+
benchmark suite. The existing CLAUDE.md "Faithful reporting" convention is aligned with this; the specific five-seed
default is cheap to adopt and provides meaningful variance estimates without exploding benchmark cost. Worth
committing to in the Phase 1c spec.

## What's NOT applicable / hype filter

**The economic-equilibrium framing is rhetorical scaffolding, not substrate.** The paper leans heavily on Akerlof /
Glosten-Milgrom / Kyle / Pigou citations to motivate the soft-label framework as an information-economics
operationalization. The intuition (uncertainty enables adverse selection) ports to Linus's audit-log analysis; the
specific market-theoretic vocabulary (taxes, transfers, externalities, bid-ask spreads) does not. Linus's Workers
do not trade with each other; the dispatch is hub-and-spoke (Maestro to Workers, not Worker-to-Worker free trade).
Read the economic citations as motivation; do not lift the market metaphor.

**The 27+ governance lever count is research breadth, not Linus breadth.** The paper claims 27+ levers; the codebase
ships them all. For Linus's Phase 3 v0 surface, 4-6 well-chosen levers are appropriate; the broader catalog is
research-tool-ness, not production-tool-ness. The right Linus posture per the paired SWARM repo-note §3: cherry-pick
the cost / access / detection levers most directly applicable; defer the broader catalog to Phase 7+.

**Population-level scale is genuinely different from Linus's Maestro/Worker scale.** The paper studies populations of
N agents over T epochs with K steps per epoch (N=8 agents × 20 epochs × 15 steps = 2,400 interactions per scenario).
Linus's Phase 3 multi-agent fanout is much smaller (Maestro + 2-4 concurrent Workers on the M1 Max 32 GB ceiling).
The population-level dynamics the paper studies (adverse selection over an ecosystem; collusion across many
pairwise interactions; threshold-dancer accumulation across many epochs) do not have direct Linus analogues at v0 +
v1 scale. The framework's value is conceptual + methodological, not direct numerical measurement on Linus's surface.

**Static-rule-based-agent limitations are a fundamental finding qualification.** The paper's limitations section
(page 14) explicitly notes that "primary experiments employ largely rule-based agents that treat governance levers
as mere accounting penalties rather than as strategic constraints. They lack the capacity to dynamically adapt their
policies or gamify the governance layer in response to the interventions." For Linus's LLM-backed Workers — which
*can* in principle adapt strategically — the paper's empirical claims (strict governance reduces welfare 40%
without improving safety) are a **lower bound** on what adaptive-Worker ablations would show. The Phase 3 stress
test must include LLM-backed adversarial agents (the paper's §7 partial validation), not just rule-based ones.

**The `under-specified acceptance mechanics` limitation surfaces a Linus mismatch.** The paper acknowledges
acceptance dynamics are simplified compared to real-world platform curation logic. For Linus, "accepted" means "the
Worker's output landed in the audit log" — much simpler than the paper's stochastic acceptance threshold. The
simplification works in Linus's favor; the paper's specific accept-reject modeling does not transfer.

**The `safety-trained paradox` finding requires careful framing.** The paper notes that explicitly safety-prompted
Claude agents scored *marginally higher* on measured toxicity because the heuristic scorer penalized cautious
cooperation-refusal. This is a real finding (cited at page 13, "LLM Agent Validation") but should not be over-
interpreted: it does not mean safety training is counterproductive; it means **the proxy signals do not perfectly
capture safety**, which is exactly the limitation the soft-label framework is designed to surface. For Linus's
Worker registry, the right takeaway: measure carefully and avoid optimizing against proxies that don't capture the
underlying objective.

**Calibration assumptions matter.** The default sigmoid sharpness `k = 2.0` is calibrated to span the unit interval
smoothly; different `k` values would produce different soft-label distributions and different metric values. The
paper notes (page 14 Limitations, first paragraph) that "uncalibrated proxy mapping: the translation of complex
proxy observable scores into probabilities via a simple scaled sigmoid is a stark simplification. Real proxy
evaluation requires rigorous empirical calibration against dense human-labeled ground truth to ensure metric
reliability." For Linus's adoption, the calibration step is genuinely necessary — Dan would need a small
human-labeled calibration set of Worker outputs to calibrate the `k` parameter before the metrics are operationally
trustworthy.

**The 5-seed replication is variance estimation, not statistical power.** Five seeds gives `mean ± std` but not
strong statistical power for hypothesis testing. The paper's §7 validation note that "zero of 19 statistical
comparisons survived Holm-Bonferroni correction" is honest about this: with five seeds × 54 episodes, the power to
detect small effects is limited. For Linus's Phase 1c+ Worker benchmarks, five seeds is the right default for
variance reporting but more seeds (or careful effect-size estimation) are needed before strong empirical claims.

## Connections

The primary fold is into [`../syntheses/safety-alignment-privacy-synthesis.md`](../syntheses/safety-alignment-privacy-synthesis.md).
swarm is the strongest single existing primary source in the cloned corpus for **multi-agent safety measurement** —
the soft-label pipeline, the four canonical metrics, the illusion-delta metric, the 27-lever governance taxonomy, and
the seven canonical scenarios are all formalized here. The synthesis currently treats safety as a four-axis surface
(mechanism, values characterization, threat-model, design-policy); this paper adds the **multi-agent /
population-level** axis as a fifth, with the paired SWARM repo-note as the operationalization companion. The
synthesis should fold this paper in as the canonical primary source for the new axis at the next revision.

The secondary fold is into [`../syntheses/agentic-systems-synthesis.md`](../syntheses/agentic-systems-synthesis.md).
The paper's population-level framing complements the synthesis's existing Kosmos / BioGuider / Sketch2Simulation
thread (those papers are about agent **competence**; this paper is about agent **safety in population**). The
discriminating axis is whether the system behaves under emergent dynamics; the synthesis can cross-link the two
threads as complementary perspectives on the same multi-agent surface.

The tertiary cross-references:

- The paired [SWARM repo-note](../repo-notes/swarm.md) is the operationalization companion. The repo-note covers the
  23 agent archetypes, 27+ governance levers, scenario YAML format, replay machinery, OpenClaw bridge, and the live
  HF Spaces sandbox; this paper-note covers the conceptual contribution and the empirical results. Together they
  form the paired-repo treatment per CLAUDE.md §Paper-note paired-repo variant — hybrid filename `swarm-2604.19752.md`,
  `pdf:` frontmatter pointing to `../../context/papers/2604.19752v1.pdf`, mutual cross-references.
- [`Letta-2310.08560.md`](Letta-2310.08560.md) §"What's reusable in Linus" — Letta's MemGPT-paper precedent for
  function-calling memory APIs and self-directed control flow with interrupts complements this paper's framework for
  multi-agent safety. Letta covers Phase 2 single-agent memory architecture; SWARM covers Phase 3+ multi-agent safety
  measurement. Both are Phase 3 spawner-spec ADR inputs from different angles.
- [`../repo-notes/Letta.md`](../repo-notes/Letta.md) §3 — the multi-agent manager taxonomy (`round_robin`,
  `supervisor`, `dynamic`, `sleeptime`, `voice_sleeptime`) is the Phase 3 spawner-spec design reference for *how* the
  parent dispatches children; SWARM is the design reference for *how* the parent measures children's interaction
  safety. Both should be named in the Phase 3 spawner ADR.
- [`../repo-notes/goose.md`](../repo-notes/goose.md) §3 — goose's `subagent_handler` machinery is the per-child-
  execution shape; SWARM is the per-interaction-safety-measurement shape. Same Phase 3 spawner-spec context.
- [`../repo-notes/openclaw.md`](../repo-notes/openclaw.md) — SWARM ships an explicit OpenClaw bridge, making it the
  canonical Phase 5+ Linus + openclaw safety-measurement integration reference.
- [`2306.03809v1`](2306.03809v1.md) (Boiko/Gomes dual-use biotech) and the existing safety-alignment-privacy thread
  on biosecurity (DEC-0047) — the soft-label / governance-lever shape is the canonical surface for **how** to
  implement biosecurity-tier gating per DEC-0047, with the governance-lever taxonomy as the framing.
- Multi-agent companion experiments validate the framework against **live LLM-backed agents** (Llama 3.1 8B via
  Concordia; Claude 3.5 Haiku/Sonnet; GPT-4o-Mini) — confirming signal alongside the existing values-paper RLHF
  robustness thread.

Phase mapping: Phase 1c+ (illusion-delta as a Worker distributional-consistency measurement; five-seed replication
default; replay-based determinism); Phase 3 (soft-label safety metrics as the multi-agent safety surface;
governance-lever taxonomy as the spawner-spec safety vocabulary; adversarial-red-team scenario class as the
stress-test reference; `Δ_q` quality gap as adverse-selection diagnostic); Phase 7+ (LLM-backed-agent validation
methodology for skill-validation; typed structured prediction for safety outputs). The paper surfaces as the
**primary source** for a Phase 3 safety-architecture commitment, not a lift-the-implementation candidate — the Linus
implementation against the patterns is a separate Phase 3 deliverable, with the paired SWARM repo as the
implementation reference.

## Open questions for Dan

1. **Should the Phase 3 spawner-spec ADR commit to soft-label safety metrics as the canonical multi-agent safety
   surface?** The paired SWARM repo-note's Open Question 1 raises the same question from the repo side; this
   paper-note is the primary-source backbone. Tentative answer: yes — the discipline is well-formalized, the cost is
   small (a few audit-log field extensions + a metrics module), and the upside is a quantitatively-grounded safety
   measurement available from the moment Phase 3 ships. Worth a DEC alongside DEC-0050 + DEC-0052.

2. **Calibration discipline — does Linus need a human-labeled calibration set before the metrics are operationally
   trustworthy?** The paper notes (Limitations) that "uncalibrated proxy mapping is a stark simplification" and
   "real proxy evaluation requires rigorous empirical calibration against dense human-labeled ground truth." For
   Linus, this means Dan would need a small labeled set of "this Worker output was actually harmful / actually
   correct" judgments to calibrate the `k` parameter and the `w` proxy-weight vector before the metric values are
   trustworthy. Should the Phase 3 spawner-spec spec include a calibration-set commitment as a prerequisite? How
   large is "small enough to be feasible" but "large enough to be statistically meaningful" — 50? 100? 500
   labeled-output samples?

3. **Illusion-delta as a Phase 1c+ Worker-benchmark axis — promote from this paper-note to the Phase 1c spec.**
   `Δ_illusion = C_perceived − C_distributed` is the sharpest existing measurement of "fluent-but-unstable" Worker
   behavior. The Phase 1c spike spec ([`phase1c-spike.md`](../specs/phase1c-spike.md)) currently does not name
   distributional-consistency as a measurement axis. Should the Phase 1c spike spec absorb illusion-delta as a
   measured property of every candidate Worker? Tentative answer: yes — the measurement is cheap (run with N seeds;
   compute `1 − mean(disagreement)`); the diagnostic value is distinct (catches what function-calling-reliability
   and instruction-following-reliability do not). Worth a one-paragraph addition to phase1c-spike.md.

4. **Quality-gap `Δ_q` as the canonical adverse-selection diagnostic for the Phase 3 audit-log.** The paper formalizes
   `Δ_q = E[p | accepted] − E[p | rejected]`: a negative quality gap indicates adverse selection (the system
   preferentially accepts lower-quality interactions). For Linus's Phase 3 dispatch, the same metric applies to
   Maestro-Worker dispatching: is the Maestro routing tasks to Workers that accept-but-underperform? Should the
   Phase 3 audit-log analysis include `Δ_q` as a load-bearing dispatch-policy diagnostic? Tentative answer: yes —
   the metric is cheap to compute from the audit log shape, and a sustained negative `Δ_q` signal would flag a
   dispatch-policy revision need.

5. **AdversarialRedTeam scenario class as a Phase 3 stress-test reference — promotion candidate.** The seven
   canonical scenarios (Baseline, StrictGovernance, AdaptiveGovernance, AdversarialRedTeam, MisalignmentSweep,
   ThresholdDancer, CollusionDetection) are a worked taxonomy of multi-agent adversarial pressure. Should the Phase
   3 multi-agent spawner stress-test suite name the seven canonical scenarios as the design reference for the
   stress-test scenario taxonomy? Tentative answer: yes — the scenario shapes are well-tested (5-seed replication
   in the paper), the YAML format is portable, and the Linus-specific stress-test scenarios can be derived as
   smaller-scale analogues (e.g., Linus AdversarialRedTeam = 1 supervisor Maestro + 3 honest Workers + 1
   adversarial-but-not-detected Worker).

6. **Adding "Lost in the Middle" (Liu 2023a), "Toolformer" (Schick 2023), and the brevity-improves-accuracy paper
   (arXiv 2604.00025) to the Phase 1 corpus.** Per the [Letta-MemGPT paper-note](Letta-2310.08560.md) §Open Question
   7 and the [caveman repo-note](../repo-notes/caveman.md) §Open Question 5, three load-bearing references are not
   yet in `context/papers/`. This paper does not add new citation candidates beyond the seven the paired SWARM
   repo-note enumerates (Aiersilan + Savitt 2026 alongside the existing Akerlof / Goodhart / Tomašev / Pierucci /
   Tailor lineage), but the same Phase 1 curation question applies: should the corpus absorb these three references
   in the next curation pass?

7. **Phase 7+ — LLM-backed-agent validation methodology adoption.** The paper's §7 validation experiments demonstrate
   that the soft-label framework operates on behavioral outcomes regardless of generation mechanism. For Phase 7+
   Linus skills (biology / scientific / domain skills producing predictions), the validation methodology — score the
   skill outputs against the same proxy-to-soft-label pipeline; validate that governance lever effects are preserved
   across the static-rule-based → LLM-backed shift — is directly portable. Should the Phase 7 biology-skills-roadmap
   ([`biology-phase7-roadmap.md`](../specs/biology-phase7-roadmap.md)) absorb this methodology as a skill-validation
   contract? Tentative answer: yes — the methodology is well-formalized and the validation experiments anchor it
   empirically; defer the specific implementation to Phase 7+ when the skills surface lands.

8. **The "safety-trained paradox" as a CLAUDE.md SAFETY.md note — be careful about proxy choice.** The paper's §7
   finding that cautious safety prompts score *marginally higher* on heuristic toxicity (because the scorer
   penalizes cooperation-refusal) is a real cautionary tale for proxy design. Should SAFETY.md absorb a one-paragraph
   note about "measure what you mean, not what is easy to measure" — citing this paper as the worked cautionary tale
   for proxy-misalignment in safety scoring? Tentative answer: yes — the lesson is durable and the cross-reference
   anchors a discipline rule that prevents repeating the mistake.

9. **The Pareto-frontier framing as a Phase 3 dispatch-policy framing — should the Phase 3 spawner-spec ADR commit
   to Pareto-frontier mapping as the canonical governance-tradeoff analysis?** The paper's Figure 3 (Risk-Welfare
   Pareto Frontier) is the cleanest existing operationalization of "every governance lever has welfare cost in
   exchange for safety gain; mapping the Pareto frontier is the actionable analysis." For Linus, the analogue is
   "every Worker-dispatch policy choice has a welfare cost (latency, token cost, retry rate) in exchange for safety
   gain." Should the Phase 3 dispatch-policy analysis be framed as Pareto-frontier mapping, with the seven canonical
   SWARM scenarios as the parameter-sweep design reference? Tentative answer: yes — the framing is durable and
   matches the existing CLAUDE.md "Measure, don't just estimate" convention; worth committing to in the Phase 3
   spawner-spec ADR.
