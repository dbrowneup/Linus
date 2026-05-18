# Group 10 Synthesis — Finance / Quant Agents

**Date:** 2026-05-08 **Repos surveyed:** dexter, OpenBB, QuantAgent, TradingAgents, nixtla **Verdicts:** 0 × Integrate,
5 × Study

---

## What this document is

A cross-cutting synthesis of five repositories in the finance and quantitative-agent cluster, surveyed as part of the
Phase 1 recon run. The group is off-mission relative to Linus's scientific computing core, but the
entrepreneurial-context framing in `docs/landscapes/total-landscape.md` and `docs/landscapes/synthesis-landscape.md`
explicitly identifies financial knowledge as adjacent capability Dan wants Linus to develop. The synthesis is not
"ignore everything financial" — it is "extract the transferable patterns while staying honest about what the domain
actually requires."

The headline justification for including this group: even the repos with the shallowest direct relevance surfaced
concrete orchestration and context-management patterns that map directly onto Linus's Maestro/Worker architecture and
memory pillar. The patterns are the primary output; the financial-domain skill is secondary and phase-deferred.

---

## The unifying thesis

All five repos are, at different levels of abstraction, answers to the same problem: how do you coordinate multiple
specialist agents or data sources toward a decision that requires synthesizing heterogeneous inputs across time? That
framing strips the finance veneer off and reveals direct structural overlap with what Linus needs for scientific
workflows — literature triage, multi-omics synthesis, hypothesis evaluation, experimental QC. The most important
contributions from this group are not financial. They are: a two-tier context-compaction strategy (dexter), a
dynamic-tool-activation pattern for large MCP surfaces (OpenBB), an adversarial debate with a two-tier LLM split
(TradingAgents), and a time-series forecasting ecosystem with genuine cross-domain applicability (nixtla).

QuantAgent earns a Study verdict for its minimal linear-pipeline architecture — a four-role assembly line (measurer →
recognizer → contextualizer → decider) expressed in ~30 lines of LangGraph orchestration glue — which brackets the
design space at the opposite end from TradingAgents' debate-style roster. The vision-LLM-on-rendered-chart trick is a
domain-agnostic idea that survives the financial-domain filter.

---

## Key findings

### OpenBB — the entrepreneurial-surface anchor

OpenBB is the only Group 10 repo with direct entrepreneurial-surface utility today. As the Open Data Platform, it
provides ~35 data provider integrations under a single schema: equities, macro (FRED, ECB, OECD, IMF, BLS), SEC filings,
options, fixed income, crypto, and more, all normalized into ~181 standard Pydantic data models so that
`obb.equity.price.historical("AAPL", provider="yfinance")` and `...provider="fmp"` return the same type. That one-schema
approach is exactly the Worker-attached capability Dan asked Linus to develop for the entrepreneurial surface.

The `openbb-mcp` server adds the AI-integration story: a dynamic per-session tool-activation model where an agent
discovers available categories first, then activates only the tools it needs. This keeps the tool-budget cost bounded
for small local models — a problem that would otherwise be severe when the underlying catalog has hundreds of endpoints.
This is the most novel piece from the group relative to Linus's current tool-registry design, and it belongs in the
Phase 2 / Phase 3 architecture discussion independent of whether OpenBB itself is adopted.

The AGPLv3 license is fine for Phases 2–7 under strictly personal use on Dan's MacBook. Phase 8 (multi-user, mobile, Mac
Studio peer) forces a decision: either a clean process boundary (OpenBB runs as a separate `openbb-api` daemon and Linus
calls it over HTTP — the "mere aggregation" boundary that avoids the combined-work problem) or replacement with
permissively-licensed alternatives. The right move is an ADR before Phase 8, not an upfront license war.

The free-tier data floor — yfinance, SEC EDGAR, FRED (with a free key), federal_reserve, ECB, OECD, IMF, BLS — is broad
enough that a Phase 7 financial-data skill can be built without any paid API key subscriptions. That lowers the barrier
to a first experiment substantially.

### dexter — context-compaction prior art

Dexter (`virattt/dexter`) is an autonomous equity-research agent shaped after Claude Code, and its most reusable piece
has nothing to do with finance. `src/agent/compact.ts` and `src/agent/microcompact.ts` implement a two-tier compaction
strategy: a lightweight `microcompact` pass runs every turn to trim low-value noise, while a full LLM-summarization pass
in `compact.ts` fires when token usage crosses an auto-compact threshold. The compaction prompt explicitly preserves
"all numerical data," forbids tool calls during compaction, and carries a structured summary of what was dropped. This
is direct prior art for the context-management primitives the memory pillar commits to in the DEC-0028 area —
specifically the Mughal-style sprint-and-compact loop that retains ~80–85% session quality across long runs versus
~40–60% in unmanaged sessions. The compaction prompt template from `compact.ts` is worth lifting into the Linus
context-manager spec as a tested starting point rather than designing from scratch.

Dexter also demonstrates the SKILL.md extensibility pattern: YAML-frontmatter markdown skill definitions exposed to the
LLM via system-prompt metadata and invoked through a single `skill` tool. The format is identical to Anthropic's own
Skill convention, which suggests the format is converging toward a de facto standard. Linus's Phase 7 skill catalog uses
it — committed as the Phase 7 standard in ROADMAP.md per E6 resolution (2026-05-06).

### TradingAgents — two-tier LLM split and the decision-log pattern

TradingAgents (`TauricResearch/TradingAgents`) is the group's richest multi-agent reference. It implements a four-stage
pipeline — parallel Analyst Team (four specialists), bull/bear Researcher debate, Trader proposal, Risk Management
debate — coordinated by a LangGraph `StateGraph` with typed `AgentState` objects at each transition. The architecture
mirrors what Linus's Phase 3 multi-agent fan-out needs, expressed in a published and maintained codebase with Ollama
support already wired in as a backend.

Two patterns are worth extracting explicitly. The `deep_think_llm` / `quick_think_llm` split in `default_config.py` is
the clearest concrete implementation in the surveyed collection of the general principle that analyst-tier Workers and
manager-tier Workers should run different model tiers. Analysts are parallelized on a cheaper, faster model; managers
arbitrating their outputs run a stronger model. Linus should formalize this as a config convention and a Maestro/Worker
boundary marker in ARCHITECTURE.md before Phase 3.

The decision-log mechanism — a markdown file at `~/.tradingagents/memory/trading_memory.md` that records each run's
decision along with realized return and alpha-vs-benchmark, fed back into the Portfolio Manager's prompt on the next run
for the same asset — is a working template for Linus's eventual self-correction loop. The feed-prior-results-into-next-
run-prompt pattern is clean, simple, and does not require the episodic-store substrate to be operational. Phase 7's
self-correction loop could adopt this pattern directly, with the KnowledgeBase as the backing store instead of a flat
markdown file.

### nixtla — the most cross-domain finding in the group

The `nixtla` repo itself is the Python SDK for TimeGPT, a closed-weight hosted paid API that violates Linus's no-paid-
APIs north star. Set it aside. The value is the surrounding Nixtlaverse ecosystem: `statsforecast` (AutoARIMA, ETS,
Theta, MSTL — pure Python/Numba, runs cleanly on Apple Silicon today), `mlforecast` (LightGBM/XGBoost over lag
features), `neuralforecast` (NHITS, NBEATSx, PatchTST, TimesNet — PyTorch with MPS support), `hierarchicalforecast`
(reconciliation across aggregate/disaggregate levels), and `utilsforecast` (shared validation and preprocessing). All
five sister libraries are open-source, local-first, and usable on M1 Max without GPU or special build steps.

The relevance to Dan's scientific work is direct and not hypothetical. Omics-trajectory data — bulk RNA-seq time
courses, single-cell pseudotime trajectories, flow cytometry kinetics, ChIP-seq signal dynamics — is time-series data.
So is environmental monitoring data: sensor streams, water-quality measurements, atmospheric concentrations. The
Nixtlaverse forecasting methods (particularly NHITS and PatchTST from `neuralforecast`) are competitive with TimeGPT on
many public benchmarks and are exactly what a Phase 7 Linus forecasting skill should expose behind a unified
`forecast(df, h, level)` interface. `hierarchicalforecast` is especially interesting for omics work because enforcing
consistency between pathway-level and gene-level forecasts is structurally identical to its intended use case.

Beyond the libraries, the time-series-as-foundation-model framing carries a Phase 6 research implication. TimesFM
(Google, ~200M parameters, open-weight) and Chronos (Amazon, T5-based, 20M–700M, open-weight) are the open successors to
TimeGPT's approach. They run on PyTorch with MPS, and their parameter counts make LoRA fine-tuning on 32 GB unified
memory tractable. A Chronos or TimesFM fine-tuned on Dan's omics-trajectory or environmental-monitoring series is
plausibly the closest analog to the biological foundation models (Bacformer, BioReason from Group 9) for the
temporal-data side of his domain. This is a Phase 6 candidate worth flagging alongside the text-model fine-tuning lane.

### QuantAgent — the minimal linear-pipeline counterpart

QuantAgent (`Y-Research-SBU/QuantAgent`) is a four-node LangGraph pipeline (Indicator → Pattern → Trend → Decision) in
which the Pattern and Trend agents render chart images and pass them to a vision LLM for interpretation. Its Study
verdict rests on the orchestration architecture, not the financial domain: a four-role linear pipeline (measurer →
recognizer → contextualizer → decider) coordinated by a single `StateGraph` over a shared state dict is ~30 lines of
orchestration glue — the cleanest minimal multi-agent template in the corpus. Compared to TradingAgents' debate-style
multi-team roster, QuantAgent and TradingAgents together bracket the orchestration design space at its minimal and
maximal ends. Both are visible reference points when the agent-spawner spec (DEC-0050) is fleshed out.

The vision-LLM-on-rendered-chart trick survives the financial-domain filter. When numbers are awkward to summarize in
tokens — sparse genomics coverage tracks, variant call density plots, long-range epigenomic signal — rendering a plot
and asking a multimodal model to interpret it bypasses the token-representation problem. The catch is that Linus's local
vision-model story is immature; the pattern becomes viable when a strong local Qwen2.5-VL or equivalent is running
reliably on M1 Max. File it as a Phase 3+ idea contingent on local vision capability.

The "high-frequency trading" labeling in QuantAgent's paper title is also a useful cautionary example. The actual system
makes one decision per multi-second hosted-LLM round-trip — structurally incapable of HFT latency. The framing is
aspirational marketing applied to a research prototype. Linus should apply the same honesty test to its own positioning:
Worker latency is bounded by inference time, and any capability claim in ARCHITECTURE.md or project-facing documentation
should reflect actual measured performance, not aspirational framing.

---

## Patterns and modules worth lifting

This is the key section. None of the code from this group is vendored into Linus, but six patterns transfer directly to
non-financial domains.

**Two-tier context compaction (dexter).** `microcompact.ts` + `compact.ts` in `src/agent/` implement a tested
preserve-numbers / summarize-prose compaction loop with an explicit threshold trigger. This pattern is now a resolved
Phase 2 design constraint (E5, accepted 2026-05-06): lift the compaction prompt template verbatim as the starting point
for the Linus context manager. The two-tier structure — lightweight every-turn pass plus full LLM-summarization at
threshold — is the right shape regardless of domain. This maps directly onto the DEC-0028 memory pillar and the Mughal
sprint-and-compact pattern.

**Dynamic per-session MCP tool activation (OpenBB).** The `openbb-mcp` discovery model — a small initial tool surface,
browse categories, activate on demand — is a concrete answer to the context-window-bloat problem that any large MCP tool
catalog creates. Linus's Phase 2 / Phase 3 tool registry should adopt this pattern: a discovery layer exposes category
metadata, not full tool schemas, until the agent explicitly activates a category. The implementation in OpenBB's
`openbb_platform/extensions/mcp_server/` is a working reference.

**Deep/quick LLM tier split (TradingAgents).** `default_config.py` exposes `deep_think_llm` and `quick_think_llm` as
first-class config knobs. Analysts (parallel, cheap, fast) run on the quick tier; managers (synthesizing, arbitrating)
run on the deep tier. This is a Maestro/Worker boundary marker that should be a named config convention in Linus's
ARCHITECTURE.md before Phase 3 — not just an implementation detail but a typed concept in the orchestration layer.

**Decision-log-feeds-next-run-prompt (TradingAgents).** The `trading_memory.md` append-and-inject loop is the simplest
possible implementation of a self-correction mechanism: record the outcome, compute the realized error, inject prior
lessons into the next invocation's manager prompt. Linus's Phase 7 self-correction loop can start with this exact
pattern, backed by a KnowledgeBase entry instead of a flat markdown file, and evolve from there.

**Local Nixtlaverse as a time-series Worker (nixtla).** `statsforecast`, `mlforecast`, and `neuralforecast` install
cleanly on Apple Silicon today with no special steps. Wrapping them behind a uniform `forecast(df, h, level)` interface
gives Linus a Phase 7 time-series Worker tool that spans finance, omics-trajectory, and environmental-monitoring data
without any API keys or cloud dependencies. The interface design from the `NixtlaClient` API —
`client.forecast(df, h=24, level=[80, 90])` — is the right ergonomic target regardless of which backend is called.

**Minimal linear multi-agent pipeline (QuantAgent).** A four-role assembly line (measurer → recognizer → contextualizer
→ decider) coordinated by a single LangGraph `StateGraph` over a shared state dict, ~30 lines of orchestration glue plus
role-specific tool bindings. This is the clearest minimal multi-agent template in the corpus and brackets the design
space at the opposite end from TradingAgents' debate-style roster. Together, QuantAgent (minimal) and TradingAgents
(maximal) give the Phase 3 agent-spawner spec (DEC-0050) the min/max orchestration envelope it needs. Transfer the
decomposition shape to Linus scientific workflows: measurer → "compute QC metrics", recognizer → "identify variant
signatures", contextualizer → "compare to reference cohort", decider → "flag for review or pass."

---

## Cross-references

**Entrepreneurship synthesis (primary thematic anchor).** G10 is the primary cluster anchor for
`docs/syntheses/entrepreneurship-synthesis.md` (added 2026-05-05). The entrepreneurship synthesis reads G10's harnesses
as the context-management pattern library that makes the literature-intelligence offering credible: dexter's two-tier
compaction, OpenBB's dynamic-tool-activation, and TradingAgents' adversarial-debate shape are the same primitives Linus
needs internally, surfaced in a domain where structured agent loops have already shipped to a paying audience. The
transferable patterns are the primary contribution; the financial domain is secondary.

**G6 MCP.** OpenBB's dynamic per-session tool-activation pattern is the most directly applicable finding from G10 to the
MCP tool-registry design questions that G6 raises. The two groups together provide both the motivating problem (large
catalogs bloat context) and a working solution (per-session activation with a discovery layer). Dynamic tool activation
timing is tracked as R2-25 in `top-questions.md`.

**G7 multi-agent.** TradingAgents' role-decomposition-with-debate pattern and the `deep_think_llm`/`quick_think_llm`
split are the practical complements to whatever orchestration framework G7 evaluates. The bull/bear debate shape
(analyst fan-out → adversarial researchers → synthesis manager → risk debate) is a template that generalizes to
literature triage, multi-omics hypothesis evaluation, and experimental-design review. QuantAgent's minimal four-node
linear pipeline brackets the opposite end of the design space — together they give DEC-0050's agent-spawner spec the
min/max envelope it needs.

**Memory synthesis (DEC-0028 area).** Dexter's two-tier compaction strategy is now a confirmed Phase 2 design constraint
(E5, resolved 2026-05-06): lift the compaction prompt template into the orchestration-layer context-manager spec.
TradingAgents' decision-log pattern is the simplest viable starting point for Layer C cross-session episodic memory
before the full SQLite episodic store is operational.

**Entrepreneurial surface (skills synthesis).** OpenBB is the most direct connection between G10 and the entrepreneurial
opportunities documented in `docs/syntheses/entrepreneurship-synthesis.md`. The financial-data infrastructure it
provides enables literature-intelligence and related commercial surface capabilities indirectly by making
financial-context enrichment a zero-additional-infra addition to those services.

---

## Phase-tagged implications

**Phase 2 — Linus MVP.** Lift dexter's compaction prompt template into the orchestration-layer context-manager spec —
the two-tier compaction pattern (dexter's `microcompact` + `compact`) is now a resolved Phase 2 design constraint (E5,
accepted 2026-05-06): the Linus context-manager spec inherits the preserve-numbers / summarize-prose compaction loop
with explicit threshold trigger. Adopt the `deep_think_llm`/`quick_think_llm` config convention in ARCHITECTURE.md —
still open as R2-13 in `top-questions.md`.

**Phase 3 — Knowledge & Parallel Agents.** Stand OpenBB up in a throwaway `uv` env (`experiments/openbb/`) and validate:
pull AAPL historicals via yfinance, pull FRED 10Y yields, compute correlation, summarize the result. If MCP per-session
activation works as documented with a 7B model, design the Phase 3 tool registry with the dynamic-activation pattern.
Evaluate whether the decision-log-feeds-next-run-prompt mechanism from TradingAgents can be wired into the KnowledgeBase
as a lightweight self-correction primitive ahead of the full Phase 7 skill.

**Phase 6 — Fine-Tuning.** Time-series foundation models (TimesFM, Chronos) join the fine-tuning candidate list
alongside the text-model LoRA lane. A Chronos model fine-tuned on Dan's omics-trajectory data is a concrete, tractable
experiment on 32 GB unified memory (parameter counts are 20M–700M). This is the closest analog the collection has
surfaced to the biological foundation models (Bacformer, BioReason) for the temporal side of Dan's domain.

**Phase 7 — Skills & Autonomy Graduation.** OpenBB graduates to an integrated financial-data skill, scoped initially to
the free-tier providers (yfinance, SEC, FRED, ECB, OECD). The Nixtlaverse libraries become the backend for a unified
`forecast`/`detect_anomalies` Worker tool usable across finance, omics, and environmental domains. Revisit the
vision-LLM-on-rendered-chart pattern from QuantAgent if local multimodal inference is strong enough by then.

---

## Open questions for Dan

**Financial-intelligence priority.** The total-landscape doc lists financial knowledge as desired adjacent capability.
Is this a near-term Phase 7 target — build a Linus financial-data skill against OpenBB's free providers — or a "nice
eventually" placeholder that can remain dormant while the scientific-computing core is built?

**AGPL stance before Phase 8.** OpenBB is AGPLv3. For Phases 2–7 on a personal machine with no network exposure to
others, this is fine. For any "let a collaborator use Linus" or mobile-access scenario in Phase 8, an ADR is needed:
process-boundary isolation or license replacement? Worth pre-committing to the decision criteria now rather than
discovering the constraint mid-Phase-8.

**Nixtlaverse as a Phase 7 forecasting skill.** `statsforecast`, `mlforecast`, and `neuralforecast` install cleanly
today. Is there a real corpus of omics-trajectory or environmental time-series data in `context/` that could anchor a
Phase 7 benchmark and make this concrete, or does the forecasting skill remain speculative until that data exists?

**Two-tier LLM config as a named convention.** Should `deep_think_llm`/`quick_think_llm` be formalized in
ARCHITECTURE.md as a named config pattern before Phase 3, or is the analyst/manager distinction best left implicit in
per-skill configuration?

**Financial-execution safety boundary.** SAFETY.md does not currently address financial-execution autonomy. If Linus
ever grows a financial skill — even research-only — worth adding an explicit tier that forbids broker API calls and
wallet signing regardless of what a Worker requests? Pre-committing this constraint before the capability exists is
cheaper than adding it after.

---

## References

### Repo-notes

- [`dexter`](../../repo-notes/dexter.md) — virattt's Claude-Code-shaped autonomous equity-research agent (TypeScript /
  Bun / LangChain / Ink TUI); the source of the two-tier microcompact + compact context-compaction prior art lifted into
  the Phase 2 context-manager spec (E5).
- [`nixtla`](../../repo-notes/nixtla.md) — Nixtla's TimeGPT SDK over a hosted paid API plus the fully-local Nixtlaverse
  (statsforecast, mlforecast, neuralforecast, hierarchicalforecast, utilsforecast); the most cross-domain finding in the
  group, applicable to omics-trajectory and environmental-monitoring time-series.
- [`OpenBB`](../../repo-notes/OpenBB.md) — OpenBB Finance's Open Data Platform with ~35 data-provider integrations under
  one Pydantic schema plus `openbb-mcp`; the entrepreneurial-surface anchor of the cluster and the source of the dynamic
  per-session tool-activation pattern.
- [`QuantAgent`](../../repo-notes/QuantAgent.md) — Stony Brook / CMU / UBC / Yale / Fudan four-node LangGraph pipeline
  (Indicator → Pattern → Trend → Decision) using vision-LLM-on-rendered-chart; brackets the minimal end of the
  multi-agent orchestration design space.
- [`TradingAgents`](../../repo-notes/TradingAgents.md) — Tauric Research's LangGraph multi-agent trading framework with
  Analyst Team / bull-bear Researcher debate / Trader / Risk Management debate; the source of the `deep_think_llm` /
  `quick_think_llm` two-tier LLM split and the decision-log-feeds-next-run-prompt self-correction pattern.
