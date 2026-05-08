# QuantAgent (`Y-Research-SBU/QuantAgent`)

## 1. Purpose and scope

QuantAgent is the reference implementation for the arXiv paper "QuantAgent: Price-Driven Multi-Agent LLMs for
High-Frequency Trading" (Xiong, Zhang, Feng, Sun, You — Stony Brook / CMU / UBC / Yale / Fudan, Sept 2025). It is a
LangGraph-orchestrated four-agent pipeline that ingests a recent OHLCV K-line window (the web interface fetches the last
~30 candlesticks via yfinance), runs three specialist analyst agents in series, and emits a final LONG/SHORT execution
directive plus risk-reward ratio from a Decision Agent. The "high-frequency" framing in the title is aspirational
positioning — the actual loop calls hosted vision LLMs (GPT-4o, Claude Haiku 4.5, Qwen3-VL, MiniMax M2.7) that take
seconds per turn, so the system is HFT-themed rather than HFT-latency. Scope for Linus: this is research code from the
"agentic LLMs for trading" subfield, useful as a worked example of multi-agent decomposition and chart-image reasoning,
not as a production trading stack.

## 2. Architecture summary

A small Python package (~16 top-level modules, no `pyproject.toml` — `requirements.txt` only). `trading_graph.py`
constructs a `TradingGraph` that owns two `BaseChatModel`s (an `agent_llm` and a `graph_llm`, configurable per-provider)
and a `TechnicalTools` toolkit. `graph_setup.py` wires a linear LangGraph `StateGraph` over `IndicatorAgentState`:
`START → Indicator Agent → Pattern Agent → Trend Agent → Decision Maker → END`. There is no branching, no parallelism,
no loop — it is a four-node assembly line. Each analyst is a closure built by `create_<role>_agent(llm, toolkit)` that
binds the LLM to a role-specific tool subset and runs a one-shot prompt-then-tool-call cycle.

The decomposition: **Indicator Agent** binds five TA-Lib wrappers (`compute_macd`, `compute_rsi`, `compute_roc`,
`compute_stoch`, `compute_willr`) and emits a momentum/oscillator narrative. **Pattern Agent** calls
`generate_kline_image`, sends the rendered chart back to a vision LLM, and returns a plain-language pattern label
(head-and-shoulders, double bottom, etc.). **Trend Agent** calls `generate_trend_image` to overlay fitted upper/lower
trend channels, then asks the vision LLM to describe channel slope and consolidation. **Decision Agent** takes the three
text reports plus `time_frame` and `stock_name` and produces a JSON
`{forecast_horizon, decision, justification, risk_reward_ratio}` — with HOLD explicitly forbidden in the system prompt
("⚠️ HOLD is prohibited due to HFT constraints"). A Flask + Yahoo Finance front-end (`web_interface.py`) provides asset
selection, timeframe choice (1m–1d), API-key management, and chart rendering. Vision-LLM input is mandatory because two
of four agents reason over generated chart images rather than raw numbers.

## 3. What's reusable in Linus

The most transferable artifact is the **decomposition pattern itself**: a domain-expert quartet (measurer, recognizer,
contextualizer, decider) coordinated by a sequential graph with a single shared state object. That shape generalizes
cleanly to Dan's actual scientific workflows — for a genomics example, Indicator → "compute QC metrics on a FASTQ",
Pattern → "render IGV-style coverage track and identify variant signatures", Trend → "compare to reference cohort",
Decision → "flag for review or pass". This is the same Maestro/Worker structure ARCHITECTURE.md envisions, expressed in
LangGraph rather than home-grown orchestration. If Linus eventually adopts LangGraph as the orchestration substrate
(currently undecided), `graph_setup.py` is a 30-line template worth copying. The vision-LLM-on-rendered-chart trick is
also reusable: when numbers are awkward to summarize in tokens, render a plot and ask a multimodal model. Compare
against `TradingAgents` (the other multi-agent trading sibling in this group), which uses a much larger debate-style
roster (analysts, researchers, trader, risk team) and explicit inter-agent argumentation; QuantAgent is the **minimalist
linear-pipeline** counterpart, and the comparison is instructive — TradingAgents shows how to scale deliberation;
QuantAgent shows how thin a useful pipeline can be.

## 4. What's inspiration only

The financial domain itself is off-mission for Linus's scientific-computing core, so the **TA-Lib indicator toolkit, the
Yahoo Finance integration, the chart-pattern catalog, and the trade-decision prompt** are inspiration at most — study
how the prompts encode domain heuristics ("ignore early-stage patterns unless breakout-confirmed", "default to dominant
trendline slope when reports disagree"), not the contents. The "HFT" framing is marketing; the system makes one decision
per multi-second LLM round-trip and could not survive a real HFT execution loop. Compared to **dexter** (the other
agentic financial-research repo in this group), QuantAgent is execution-flavored and chart-vision-heavy where dexter is
more research-and-retrieval — different niches, both off-core for Linus.

## 5. What's incompatible or out of scope

Hosted vision LLMs are mandatory by design — every chart-rendering agent posts an image back to GPT-4o / Claude /
Qwen-VL / MiniMax. Linus's local vision-capable inference story (Phase 2+) is immature; running QuantAgent end-to-end
against a local Qwen2.5-VL or similar is plausible but unvalidated. TA-Lib has the usual native-build gotchas on Apple
Silicon (`conda install -c conda-forge ta-lib` works; pip wheels often don't). The **single LangGraph StateGraph with a
global `IndicatorAgentState` dict** is fine at four nodes but would not scale to dozens of agents without rework.
Real-money trading is explicitly out of scope and explicitly dangerous — the README's disclaimer is correct, and any
Linus exposure to this code must stay in research/backtest mode; the line between "analyzes a chart" and "places an
order" is a single API-key swap.

## 6. Recommendation: **Ignore** (for the scientific-computing core; Study if Dan wants the financial-knowledge adjacency)

QuantAgent is a clean, small, readable example of LangGraph multi-agent decomposition, but the domain is off-mission and
the architectural lessons are subsumed by **TradingAgents** (richer decomposition) for the multi-agent pattern and by
**OpenBB** (broader data substrate) for the financial-knowledge adjacency. If Phase 7 ever produces a "financial
analysis" skill for Linus, revisit this repo for prompt design and the chart-vision pattern. Otherwise leave it as
reference clone — no code to vendor, no submodule to add.

## 7. Questions for Dan

- **Multi-agent decomposition pattern transferability.** The four-role linear pipeline (measurer → recognizer →
  contextualizer → decider) is generic. Worth prototyping a non-financial Linus skill on this template — say, a
  paper-triage skill (extract → classify → contextualize-against-KB → recommend) — to see whether LangGraph adds value
  versus a hand-rolled sequence in Phase 2's orchestration layer?
- **LangGraph as orchestration substrate.** QuantAgent, TradingAgents, and several other agentic repos in the collection
  use LangGraph. ARCHITECTURE.md leaves the orchestration runtime open. Want to do a Phase 2a spike that evaluates
  LangGraph vs. a custom Linus orchestrator on one or two skills, with a written verdict ADR?
- **Vision-LLM-on-rendered-chart pattern for science.** QuantAgent demonstrates "render → ask multimodal model" as a way
  to summarize numerical data. For genomics (coverage tracks, variant call plots, phylogeny figures) this could be
  useful with a local Qwen2.5-VL. Worth a Phase 1 experiment, or wait until local vision models are stronger?
- **Differentiation from TradingAgents.** QuantAgent and TradingAgents are sibling repos solving overlapping problems
  with very different architectures (linear-4-agent vision pipeline vs. debate-style multi-team roster). Is the
  financial-knowledge adjacency Dan wants better served by one over the other, or do we treat both as study material and
  revisit only if a concrete Phase 7 skill needs them?
- **Real-money safety boundary.** SAFETY.md doesn't currently address financial-execution autonomy. If Linus ever grows
  a financial skill, do we want an explicit SAFETY.md tier that forbids execution endpoints (broker APIs, wallet
  signing) regardless of harness? Worth pre-committing now, before the temptation appears.
