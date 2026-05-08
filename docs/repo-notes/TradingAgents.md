# TradingAgents (`TauricResearch/TradingAgents`)

## 1. Purpose and scope

TradingAgents is a multi-agent LLM trading framework from Tauric Research, productized from the arXiv paper
[2412.20138](https://arxiv.org/abs/2412.20138) (Xiao, Sun, Luo, Wang, 2025). It mirrors the role decomposition of a real
trading firm — Analyst Team, Researcher Team (bull vs. bear debate), Trader, Risk Management debate, Portfolio Manager —
and runs them as nodes in a LangGraph state machine. It is an _academic-paper implementation hardened into a
community-facing tool_: v0.2.4 ships structured outputs, persistent decision memory, LangGraph checkpoint resume,
multi-provider LLM support (OpenAI, Google, Anthropic, xAI, DeepSeek, Qwen, GLM, OpenRouter, **Ollama**, Azure), Docker,
and an `i18n` README. For Linus this is off-mission for the scientific computing core, but the role-decomposition
pattern is the most directly transferable Maestro/Worker analog in the entire repo collection — it is the same idea
("specialists with specific prompts debate, then a manager decides") applied to a different domain.

## 2. Architecture summary

A Python 3.10+ package built on LangChain + LangGraph. The entry point is
`tradingagents.graph.trading_graph.TradingAgentsGraph`, which compiles a `StateGraph` whose nodes are the role agents.
`agents/analysts/` holds four parallel analysts (`market_analyst`, `social_media_analyst`, `news_analyst`,
`fundamentals_analyst`); `agents/researchers/` holds `bull_researcher` and `bear_researcher` that take all four reports
and debate for `max_debate_rounds`; `agents/managers/research_manager.py` synthesizes the debate;
`agents/trader/trader.py` proposes a transaction; `agents/risk_mgmt/` runs a second debate (`aggressive_debator`,
`conservative_debator`, `neutral_debator`) for `max_risk_discuss_rounds`; `agents/managers/portfolio_manager.py` issues
the final approve/reject. Each role is a closure (`create_bull_researcher(llm) -> bull_node`) that reads/writes a typed
`AgentState` (`InvestDebateState`, `RiskDebateState`) — clean and inspectable. Two LLM tiers are wired as
`deep_think_llm` and `quick_think_llm`, so analysts can run on a cheaper/faster model and managers on a stronger one.
Tools (yfinance, Alpha Vantage, news, insider transactions, indicators via `stockstats`) live in `dataflows/` behind a
vendor-config indirection. Persistence: a markdown decision log at `~/.tradingagents/memory/trading_memory.md` is fed
back into the Portfolio Manager prompt on subsequent runs for the same ticker (with realized return + alpha-vs-SPY
computed post-hoc); LangGraph SQLite checkpoints under `~/.tradingagents/cache/checkpoints/<TICKER>.db` enable resume
after crashes. No live brokerage integration — `backtrader` is a dep and the README explicitly disclaims this is
research-only.

## 3. What's reusable in Linus

The orchestration pattern, not the trading code. The role-decomposition-with-debate idiom — a fan-out of specialist
analysts, a structured adversarial debate (bull/bear) over their reports, a synthesis manager, then a second risk debate
before commit — is exactly the shape Linus's Phase 3 ("Knowledge & Parallel Agents") and Phase 7 ("Skills & Autonomy
Graduation") need. Substitute domain: literature triage instead of market analysis (fundamentals analyst → wet-lab
reproducibility analyst, sentiment → citation-network analyst, technical → methodology critic; bull/bear → "supports the
hypothesis" vs "alternative explanation"; risk debate → "what does this experiment cost / what could go wrong"); the
LangGraph plumbing transfers directly. The two-tier LLM split (deep / quick) is a clean and concrete pattern Linus
should copy: Worker model for analysts, larger model (or hosted Maestro) for managers. The persistent decision-log
mechanism — append outcome, recompute realized return, inject prior lessons into the next run's prompt — is a working
template for Linus's eventual KnowledgeBase-backed self-correction loop.

Compared to **QuantAgent** (other multi-agent trading; Chinese academic group), TradingAgents is the more polished
community product: English-first docs and CLI, multi-provider including Ollama out of the box, structured outputs and
checkpoint resume in v0.2.4, a published arXiv paper plus active versioned releases through 2026. Compared to **dexter**
(single-agent financial research), TradingAgents' value is precisely the multi-role debate — dexter shows what one agent
with good tools can do; TradingAgents shows what role specialization + adversarial debate + a manager buys you on top.

## 4. What's inspiration only

The financial domain itself, the `dataflows/` vendor adapters (yfinance, Alpha Vantage, stockstats), the `backtrader`
backtesting integration, and the prompts (which are explicitly written in trader-speak: "Bull Analyst", "growth
potential", "competitive advantages"). None of that maps onto Dan's scientific work. The CLI built on `typer` + `rich` +
`questionary` is nice prior art for any future Linus interactive launcher, but Linus already has Streamlit and
(eventually) openclaw, so this is study-only.

## 5. What's incompatible or out of scope

Real-money execution. The README and the project's disclaimer page are explicit: "designed for research purposes…not
intended as financial, investment, or trading advice." There is no live brokerage adapter and the Portfolio Manager
"sends the order to the simulated exchange" — no real money moves. Anyone reading this note: do not wire this up to a
brokerage account based on a backtest looking good. Beyond that, the LangChain/LangGraph dependency surface is heavier
than Linus wants in its core (LangGraph is a reasonable choice but it's a commitment), and the framework's assumption of
frontier hosted LLMs for the manager tier means the local-Ollama path is the worst-quality configuration, not the best —
direct opposite of Linus's posture.

## 6. Recommendation: **Study**

Clone-as-reference is correct. Do not vendor or depend on TradingAgents in Linus. Read `tradingagents/graph/setup.py`,
`graph/trading_graph.py`, `agents/researchers/bull_researcher.py`, and `agents/managers/portfolio_manager.py` carefully
before designing Linus's Phase 3 multi-agent fan-out — they are a working, published reference for the bull/bear
debate + manager-arbitration pattern that Linus will want in non-financial form. Revisit if Dan ever decides to give
Linus a "personal-finance research" skill in Phase 7, at which point the `dataflows/` vendor adapters and the
decision-log mechanism become directly useful and TradingAgents may graduate to "Integrate as an opt-in skill module."

## 7. Questions for Dan

1. **Two-tier LLM split as a Linus convention.** TradingAgents' `deep_think_llm` / `quick_think_llm` distinction is a
   clean pattern — analysts on a cheap fast model, managers on a strong model. Should Linus formalize this as a config
   convention (and as a Maestro/Worker boundary marker) in ARCHITECTURE.md before Phase 3?
2. **Decision-log + reflection pattern.** The `~/.tradingagents/memory/trading_memory.md` mechanism — append outcome,
   compute realized result, feed prior lessons into the next run's manager prompt — is a near-drop-in template for a
   Linus "what worked / what didn't" memory. Is that interesting enough to spec independently, or does it stay coupled
   to whatever KnowledgeBase ends up being?
3. **Personal finance as a Phase 7 skill.** The README is firm that this is research-only and not investment advice.
   Setting that aside — do you ever want Linus to do private personal-finance research (analyze a 401k, model a
   refinance, evaluate a stock) such that TradingAgents' `dataflows/` adapters become useful, or is finance permanently
   out of scope for Linus?
4. **LangGraph as Linus's orchestration substrate.** TradingAgents, like several other agent frameworks, builds on
   LangGraph. Linus has not committed to an orchestration library yet. Is LangGraph in the running for Phase 2a's
   orchestration layer, or is the plan to write a thinner Linus-native graph runner and avoid that dep?
