# Q-Fin Paper Corpus — Seed List for v1 Strategy Library

> **Date:** 2026-05-12 (Day 2)
> **Author:** Initial seed list — to be curated and validated by Dan against the criteria
> in [`mvp-scope-memo.md`](mvp-scope-memo.md). Treat as a starting menu, not a commitment.
> **Audience:** Dan (curator), Önder (math validator), team (review)
> **Purpose:** Propose a structured, categorized seed list of ~30 peer-reviewed quant
> finance papers from which v1's 5–10 strategies can be sourced. Each entry includes
> arxiv/DOI, why it's a good candidate, and what's needed to validate it.

## Curation criteria (recap from MVP scope memo)

A paper qualifies for the v1 strategy library if and only if:

1. **Published in a peer-reviewed journal OR on arxiv with significant citations** (>50 or
   from an established author).
2. **Strategy is implementable** — well-defined entry/exit signals, available historical
   data, no proprietary feeds.
3. **Backtest period ≥ 10 years** of accessible data on liquid markets.
4. **Re-runnable to Sharpe ≥ 0.5** at conservative transaction costs (10bps round-trip).
5. **No look-ahead bias** in our re-implementation (walk-forward only).

Papers below are organized by arxiv [q-fin category](https://arxiv.org/list/q-fin/recent).
**Validation status to be filled by Dan:** ✓ = re-validated; ⚠ = re-implementation in
progress; ☐ = candidate not yet evaluated.

---

## Tier A — Foundational strategies (high confidence, well-known)

These are the canonical quant strategies. Every quant team in the world has implemented
them. They serve as **anchors of trust** in the v1 library — judges and users immediately
recognize the references.

### A1. Momentum (Jegadeesh & Titman 1993)

- **Citation:** Jegadeesh, N., & Titman, S. (1993). "Returns to buying winners and selling
  losers: Implications for stock market efficiency." *Journal of Finance*, 48(1), 65–91.
- **DOI:** [10.1111/j.1540-6261.1993.tb04702.x](https://doi.org/10.1111/j.1540-6261.1993.tb04702.x)
- **Strategy shape:** Rank assets by 3–12 month returns; long top decile, short bottom
  decile; rebalance monthly. The seminal momentum paper. **~30,000+ citations.**
- **Why include:** Most-cited momentum paper in the literature. Easy to implement; robust
  across decades and markets.
- **Validation status:** ☐ Pending Dan's re-run with 10bps costs on a US-equity universe.
- **Likely Sharpe:** ~0.5–1.0 historically; degraded post-2010 but still positive.

### A2. Time-series momentum (Moskowitz, Ooi & Pedersen 2012)

- **Citation:** Moskowitz, T. J., Ooi, Y. H., & Pedersen, L. H. (2012). "Time series
  momentum." *Journal of Financial Economics*, 104(2), 228–250.
- **Strategy shape:** Long an asset if its trailing 12-month return is positive; short if
  negative. Each asset independently. Works across asset classes (equities, bonds,
  commodities, currencies).
- **Why include:** Strong out-of-sample evidence; complements cross-sectional momentum
  (A1). Pedersen is AQR — quality of source matters.
- **Validation status:** ☐
- **Likely Sharpe:** ~1.0 in cross-asset universe.

### A3. Hierarchical Risk Parity (López de Prado 2016)

- **Citation:** López de Prado, M. (2016). "Building diversified portfolios that
  outperform out-of-sample." *Journal of Portfolio Management*, 42(4), 59–69.
- **DOI:** [10.3905/jpm.2016.42.4.059](https://doi.org/10.3905/jpm.2016.42.4.059)
- **Strategy shape:** Cluster assets by correlation; allocate hierarchically. Avoids the
  ill-conditioning of mean-variance optimization without using factor models.
- **Why include:** Modern portfolio construction. López de Prado is a serious source
  (Cornell, AQR). Methodology is mathematically rigorous and code is well-known
  (PyPortfolioOpt has it built in).
- **Validation status:** ☐
- **Likely Sharpe:** Comparable to risk parity; lower drawdown than equal-weight.

### A4. Risk Parity (Asness, Frazzini & Pedersen 2012)

- **Citation:** Asness, C. S., Frazzini, A., & Pedersen, L. H. (2012). "Leverage aversion
  and risk parity." *Financial Analysts Journal*, 68(1), 47–59.
- **Strategy shape:** Allocate risk equally across asset classes (typically equities,
  bonds, commodities); rebalance to maintain risk contributions. Foundational for the
  Bridgewater All-Weather approach.
- **Why include:** Well-understood, robustly performant, fits naturally with the
  Conservative / Moderate risk profiles.
- **Validation status:** ☐
- **Likely Sharpe:** ~0.7–1.0.

### A5. Pairs Trading (Gatev, Goetzmann, & Rouwenhorst 2006)

- **Citation:** Gatev, E., Goetzmann, W. N., & Rouwenhorst, K. G. (2006). "Pairs trading:
  Performance of a relative-value arbitrage rule." *Review of Financial Studies*, 19(3),
  797–827.
- **DOI:** [10.1093/rfs/hhj020](https://doi.org/10.1093/rfs/hhj020)
- **Strategy shape:** Find pairs of stocks with historically correlated prices; trade the
  spread when it diverges.
- **Why include:** Classic statistical arbitrage. Market-neutral. Demonstrates a
  *different* category of strategy from trend/factor.
- **Validation status:** ☐
- **Likely Sharpe:** ~0.5–1.5 in early periods; degraded but still useful for
  diversification.

---

## Tier B — Factor and asset-pricing strategies

Modern factor literature. These strategies form the bedrock of "smart beta" and
quantitative equity portfolios.

### B1. Fama-French 5-Factor Model (Fama & French 2015)

- **Citation:** Fama, E. F., & French, K. R. (2015). "A five-factor asset pricing model."
  *Journal of Financial Economics*, 116(1), 1–22.
- **DOI:** [10.1016/j.jfineco.2014.10.010](https://doi.org/10.1016/j.jfineco.2014.10.010)
- **Strategy shape:** Long-short portfolios sorted on size, book-to-market, profitability,
  investment, and market beta. The factor zoo's most cited model.
- **Why include:** Reference factor model. Even if we don't trade the factors directly,
  this informs how we interpret strategy performance.
- **Validation status:** ☐ (factor returns from Ken French's data library are public).

### B2. Carhart 4-Factor Model (Carhart 1997)

- **Citation:** Carhart, M. M. (1997). "On persistence in mutual fund performance."
  *Journal of Finance*, 52(1), 57–82.
- **Why include:** Added momentum to Fama-French 3-factor. Standard reference for any
  momentum-related strategy's risk-adjusted returns.
- **Validation status:** ☐

### B3. Quality Minus Junk (Asness, Frazzini & Pedersen 2019)

- **Citation:** Asness, C. S., Frazzini, A., & Pedersen, L. H. (2019). "Quality minus
  junk." *Review of Accounting Studies*, 24, 34–112.
- **Strategy shape:** Long high-quality stocks (profitable, growing, safe, well-managed);
  short low-quality stocks. AQR's flagship factor.
- **Why include:** Strong out-of-sample evidence; complements value and momentum;
  defensive characteristics.
- **Validation status:** ☐

### B4. Betting Against Beta (Frazzini & Pedersen 2014)

- **Citation:** Frazzini, A., & Pedersen, L. H. (2014). "Betting against beta." *Journal of
  Financial Economics*, 111(1), 1–25.
- **Strategy shape:** Long low-beta stocks (leveraged); short high-beta stocks. Exploits
  the low-volatility anomaly with leverage.
- **Why include:** Real edge from a behavioral source (institutional leverage
  constraints). Important for the Conservative profile.
- **Validation status:** ☐
- **Note:** v1 doesn't allow user-side leverage, but the long-only version is
  implementable.

### B5. Value and Momentum Everywhere (Asness, Moskowitz & Pedersen 2013)

- **Citation:** Asness, C. S., Moskowitz, T. J., & Pedersen, L. H. (2013). "Value and
  momentum everywhere." *Journal of Finance*, 68(3), 929–985.
- **Strategy shape:** Cross-asset value and momentum strategies. Documents that V/M
  factors work across equity countries, bonds, currencies, commodities.
- **Why include:** Best multi-asset cross-validation. Supports the multi-asset RWA
  framing in Chuan's design.

---

## Tier C — Machine learning factor strategies

Modern ML approaches to asset pricing. These add the AI flavor to the curated library
without departing from peer-reviewed rigor.

### C1. Empirical Asset Pricing via Machine Learning (Gu, Kelly & Xiu 2020)

- **Citation:** Gu, S., Kelly, B., & Xiu, D. (2020). "Empirical asset pricing via machine
  learning." *Review of Financial Studies*, 33(5), 2223–2273.
- **DOI:** [10.1093/rfs/hhaa009](https://doi.org/10.1093/rfs/hhaa009)
- **Strategy shape:** Use neural networks, gradient-boosted trees, and other ML methods
  on a large feature set (94 firm characteristics + 74 industry features). Long-short on
  ML-predicted returns.
- **Why include:** *The* canonical ML-meets-asset-pricing paper. >1000 citations. Shows
  ML methods substantially outperform linear factor models.
- **Validation status:** ☐ (data and code available from authors).
- **Pitch value:** This is the AI strategy in the library. Strong "see, AI does help"
  evidence for the agentic-portfolio thesis.

### C2. Deep Hedging (Buehler, Gonon, Teichmann & Wood 2019)

- **Citation:** Buehler, H., Gonon, L., Teichmann, J., & Wood, B. (2019). "Deep hedging."
  *Quantitative Finance*, 19(8), 1271–1291.
- **arxiv:** [1802.03042](https://arxiv.org/abs/1802.03042)
- **Strategy shape:** Use deep RL to learn optimal hedging policies under realistic
  market frictions (transaction costs, market impact).
- **Why include:** Shows ML applied to risk management (a key theme for the Conservative
  profile). Less directly tradeable but instructive.

### C3. Machine Learning Trading Agent Frameworks

- **TradingAgents** (Xiao et al. 2024) — [arxiv:2412.20138](https://arxiv.org/abs/2412.20138).
  Multi-agent LLM-based trading framework. Adjacent to our work but at the agent
  framework level, not the strategy level.
- **Trading-R1** (Wang et al. 2025) — [arxiv:2509.11420](https://arxiv.org/abs/2509.11420).
  Reasoning-trace-as-product. **Directly relevant to our reasoning-trace primitive.**
- **QuantAgent** ([Stony Brook 2024](https://github.com/stonybrook-edu/quantagent)) —
  Trading agent framework with vision-LLM-on-charts. Adjacent.

**Note:** These are agent frameworks, not strategies per se. They influence the agent
runtime, not the strategy library. Cited in the pitch deck for context.

---

## Tier D — Risk management and execution

Critical for the Önder math module and the live-agent risk infrastructure.

### D1. Kelly Criterion (Kelly 1956 / Thorp 1969)

- **Citation:** Kelly, J. L. (1956). "A new interpretation of information rate." *Bell
  System Technical Journal*, 35(4), 917–926. + Thorp, E. O. (1969). "Optimal gambling
  systems for favorable games." *Review of the International Statistical Institute*,
  37(3), 273–293.
- **Strategy shape:** Position sizing rule that maximizes long-run log-wealth growth.
- **Why include:** Önder's stated math foundation. Used in v1 for position-sizing within
  each risk profile.

### D2. Walk-Forward Validation Best Practices (López de Prado 2018)

- **Citation:** López de Prado, M. (2018). *Advances in Financial Machine Learning*.
  Wiley. (Book, not paper, but the canonical reference.)
- **Why include:** Reference for our backtest validation discipline. Walk-forward,
  combinatorial purged k-fold, deflated Sharpe ratio.

### D3. Deflated Sharpe Ratio (Bailey & López de Prado 2014)

- **Citation:** Bailey, D. H., & López de Prado, M. (2014). "The deflated Sharpe ratio:
  Correcting for selection bias, backtest overfitting and non-normality." *Journal of
  Portfolio Management*, 40(5), 94–107.
- **Why include:** Honest backtest accounting. The "paper-claimed-Sharpe vs
  out-of-sample-Sharpe" delta we surface in the passport is an applied form of this.

### D4. Combinatorially Symmetric Cross-Validation (Bailey, Borwein, López de Prado &
Zhu 2017)

- **Citation:** Bailey, D. H., et al. (2017). "The probability of backtest overfitting."
  *Journal of Computational Finance*, 20(4), 39–69.
- **Why include:** Backtest validation methodology. Cited in the passport spec for the
  `look_ahead_audit_passed` flag.

---

## Tier E — Regime detection

For the live agent's regime classifier (design.md § 4.3.3).

### E1. Markov Regime-Switching Models (Hamilton 1989)

- **Citation:** Hamilton, J. D. (1989). "A new approach to the economic analysis of
  nonstationary time series and the business cycle." *Econometrica*, 57(2), 357–384.
- **Why include:** Canonical regime-switching framework. Chuan's regime detection
  (risk-on / risk-off / transition / crisis) is structurally Markov.

### E2. Markov-Switching Vector Autoregression for Asset Allocation (Ang & Bekaert 2002)

- **Citation:** Ang, A., & Bekaert, G. (2002). "International asset allocation with
  regime shifts." *Review of Financial Studies*, 15(4), 1137–1187.
- **Why include:** Application of regime-switching to portfolio construction. Directly
  informs the regime → allocation mapping.

### E3. Macroeconomic Regime Detection via Composite Indicators (Various, 2010s)

- **Note:** A line of literature on combining VIX, term spread, credit spread, etc., into
  a composite regime indicator. Worth surveying for the specific feature set Chuan's
  design uses.

---

## How the seed list maps to the v1 library

Target: 5–10 strategies for the v1 library, drawn from:

| Tier | Strategies for v1 library                                         |
| ---- | ----------------------------------------------------------------- |
| A    | At least 3 of (A1 momentum, A2 time-series momentum, A3 HRP, A4 risk parity, A5 pairs) |
| B    | 1–2 factor strategies (B3 quality, B4 BAB, or B5 cross-asset V/M)  |
| C    | 1 ML-based strategy (C1 Gu-Kelly-Xiu or similar)                  |
| D    | Math primitives, not standalone strategies (used in sizing/validation) |
| E    | Regime classifier, not a tradeable strategy                       |

**Suggested v1 library composition:**

1. Cross-sectional momentum (A1)
2. Time-series momentum (A2)
3. Hierarchical Risk Parity (A3)
4. Risk Parity all-weather (A4)
5. Pairs trading on liquid US equity pairs (A5)
6. Quality factor (B3)
7. Cross-asset value-and-momentum (B5)
8. ML-predicted factor returns (C1 simplified)

That's 8 strategies. Each has a paper-grounded methodology, each has a known historical
performance envelope, each fits naturally inside one or more of the Conservative /
Moderate / Aggressive / Hyper-Risky risk profiles.

## Process notes

- **Dan does the curation pass.** ~2–4 hours of work per strategy: read the paper,
  implement the strategy as a `bt.Strategy` subclass, run the backtest, fill in the
  passport metadata, document the methodology. ~30 hours total for 8 strategies. Spread
  across week-1 evenings + weekend.
- **Önder reviews each strategy's math.** Particularly Kelly sizing inside each
  strategy's position rules. ~30 min per strategy.
- **Methodology hash:** generated deterministically from the canonical methodology text +
  the paper arxiv ID. Documented in
  [`specs/strategy-passport-spec.md`](specs/strategy-passport-spec.md).
- **For the arxiv ingest pipeline demo (Day 11):** pick 2–3 *recent* (2024–2026) arxiv
  q-fin papers we haven't pre-curated. Show the LLM extracting methodology, generating
  code, running a validation backtest, and the human curator (Dan) reviewing the result.

## What's deliberately NOT in this seed list

- Crypto-native strategies (DeFi yield farming, MEV, etc.). The v1 library is
  TradFi-grounded; crypto-side allocation is via USYC + RWA tokens.
- Strategies that require leverage > 2x (the Hyper-Risky profile allows modest leverage
  but no portfolio-margin / perpetual-futures patterns).
- Strategies from non-peer-reviewed sources (Medium, Substack, anonymous Twitter, etc.)
  even if intriguing.
- High-frequency / latency-sensitive strategies. Backtester can't realistically simulate
  these.

---

## Next steps

1. **Dan reviews and approves this seed list** (or proposes changes). Day 3.
2. **Dan starts implementation pass** with A1 (Jegadeesh-Titman momentum) as the
   reference implementation. Day 3–4.
3. **Önder reviews A1's Kelly sizing and look-ahead audit.** Day 4.
4. **Repeat for remaining strategies** through Day 7.
5. **By Day 7,** the strategy library is populated and live in the database.
