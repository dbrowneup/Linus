# RFB Selection Memo

> **Audience:** Agent Market hackathon team
> **Purpose:** Evaluate the four Request-for-Builder ideas from the Canteen / Agora cold
> email against our team capability, 2-week feasibility, and judging fit. Recommend whether
> to anchor on any of them.
> **Date:** 2026-05-12 (Day 2)

## Background

The cold email from Canteen included four concrete RFB ideas. Each is internally coherent
and cites real research. **The hackathon does not require teams to pick one — they are
explicitly framed as "ideas worth exploring."** This memo asks: should Agent Market anchor
on one of them, or pursue its own thesis?

## The four RFB ideas

### RFB i — Trading-R1: Reasoning traces as the product

**Source.** Wang et al. 2025, Tauric Research.
[arxiv:2509.11420](https://arxiv.org/abs/2509.11420). Trading-R1 is a large-scale financial
reasoning model whose value is the reasoning trace itself, not the trade. The trace can be
hashed and pinned (IPFS/Arweave, hash on Arc) without eroding PnL. The proposed market
type: bets on which reasoning patterns converge to profit, using
[TradingAgents v0.2.4's structured outputs](https://arxiv.org/abs/2412.20138) as the
machine-readable substrate.

**Capability fit.** ⭐⭐ — requires a working trading agent (Chuan can advise), backtest
infrastructure (don't have), prediction-market integration (don't have).

**Feasibility in 2 weeks.** Low. The Trading-R1 model is not something we'd reproduce; the
substrate requires bringing up the TradingAgents fork, integrating with market data, and
building the betting venue. Each is a project of its own.

**Judging fit.** High — Canteen literally suggested this; it directly serves the crypto-
finance judging audience.

**Overlap with our thesis.** Strong — "reasoning trace as the product" is structurally the
same insight as our agent passport. The implementation path is just different.

**Recommendation:** **Don't anchor on RFB i directly.** Instead, **borrow the reasoning-
trace-as-product framing** for the agent passport pitch (which we're doing anyway), and
acknowledge in the deck that this is the same insight applied at a different layer.

### RFB ii — Hyperliquid Whale Index

**Concept.** An Arc-native ERC-20 that holds USDC and auto-rebalances exposure across
Hyperliquid forks (Aster, Polynomial, etc.) based on top-trader migration. Weekly rebalances
cost cents on Arc rather than dollars elsewhere. The rebalance signal is the research —
where smart money is currently trading.

**Capability fit.** ⭐⭐⭐ — Chuan's CoinShares background includes exchange connectivity;
he could in principle build this. But it requires real-time leaderboard data, oracle
integration, and an investable token.

**Feasibility in 2 weeks.** Low. A working version of this is a real product, not a demo.
Mocking it is unconvincing.

**Judging fit.** Medium — interesting, on-theme, but doesn't necessarily land as a
**marketplace** demo.

**Overlap with our thesis.** Weak. This is a single tokenized index product, not a
marketplace.

**Recommendation:** **Don't pursue.** Could be ONE agent listed on Agent Market in v2 —
"Whale Index Manager" agent that publishes rebalance signals on-chain. But it's not a
hackathon demo.

### RFB iii — Slash-bonded copy-trading

**Concept.** A USDC performance bond on Arc for a given whale that users can stake alongside.
A smart contract reads leaderboard rank via oracle; if the leader falls below a defined
threshold, the bond slashes proportionally. The empirical decay function becomes the slash
schedule directly. Arc's cheap fees mean this works at retail follower size.

**Capability fit.** ⭐⭐ — requires oracle integration, slashing-contract design, and a
leaderboard data source. Chuan could lead but it's complex for 2 weeks.

**Feasibility in 2 weeks.** Low-medium. Slashing logic is the hardest part of smart-contract
design; auditing matters; we don't have time for an audit.

**Judging fit.** High — directly addresses the leaderboard-decay problem (which we
acknowledge in
[`reputation-and-vertical-selection.md`](reputation-and-vertical-selection.md)).

**Overlap with our thesis.** Medium. The slash-bond mechanic is one **way to implement**
reputation that doesn't predict performance; our agent passport is a **different way** to
implement the same insight. The slash-bond is reputation-as-skin-in-the-game; the passport
is reputation-as-auditable-history. Both are honest answers; they're not mutually exclusive
(v2 could have both).

**Recommendation:** **Don't anchor on RFB iii.** But cite it in the pitch deck as supporting
evidence for the "leaderboard rank doesn't persist" framing — we can credit the slash-bond
idea while explaining why we chose verifiable history instead.

### RFB iv — Translation as a source of alpha

**Concept.** Forks of TradingAgents have added different locale-specific data brokers
(TradingAgents-CN with Tushare; AlpacaTradingAgent with Coindesk/DeFiLlama/Reddit). The
framework is interchangeable; the **translation layer** is the moat. The proposed market:
agents bid in USDC for the right to translate a non-English news event into a
Polymarket-shaped question, with builder fees flowing to the translator on every fill.

**Capability fit.** ⭐⭐⭐⭐ — Marten and Daniel R can both work with foreign-language
data sources; the agent layer is straightforward; the bidding mechanic is a small
smart-contract surface.

**Feasibility in 2 weeks.** Medium-high — the bidding contract is similar in shape to our
escrow; the translation agent is a clear MCP-tool-using LLM agent; Polymarket integration
is the hard part but a mock-up is acceptable for v1.

**Judging fit.** High — Canteen suggested it explicitly, says it's "the most thematically
aligned with Linus's own thesis" (the email's framing).

**Overlap with our thesis.** **Strong, and unique.** This RFB describes a marketplace
mechanic (agents bid for translation rights) that is structurally a marketplace problem.
Translation-as-alpha is not a single product; it's a category of agent listings. **A
"Translation Agent" demo on Agent Market would be a credible execution of RFB iv inside
the broader marketplace pitch.**

**Recommendation:** **Strongly consider as the demo vertical.** A "news-to-prediction-
market translation agent" on Agent Market would:

- Demo the marketplace flow end-to-end.
- Be a credible execution of one of Canteen's own RFB ideas.
- Use Dan's bilingual-corpus instincts and Marten's data-engineering chops.
- Avoid the trading-vertical regulatory issues.
- Be visually concrete: judges can see a non-English news event get translated into a
  well-formed prediction-market question, and watch the agent earn USDC.

This vertical fits cleanly with the on-chain-research lead vertical proposed in
[`reputation-and-vertical-selection.md`](reputation-and-vertical-selection.md); both are
"research-shaped, not trading-shaped" verticals. We could even build BOTH demo agents and
have them on the marketplace, with one (research) as the primary and one (translation) as
a secondary that shows extensibility.

## Decision matrix

| RFB                              | Capability fit | 2-wk feasibility | Judging fit | Overlap with our thesis | Recommendation               |
| -------------------------------- | -------------- | ---------------- | ----------- | ----------------------- | ---------------------------- |
| i. Trading-R1 reasoning traces   | ⭐⭐           | Low              | High        | Strong                  | Borrow framing; don't anchor |
| ii. Hyperliquid Whale Index      | ⭐⭐⭐         | Low              | Medium      | Weak                    | Skip                         |
| iii. Slash-bonded copy-trading   | ⭐⭐           | Low-medium       | High        | Medium                  | Cite; don't anchor           |
| **iv. Translation as alpha**     | **⭐⭐⭐⭐**   | **Medium-high** | **High**    | **Strong**              | **Consider as demo vertical**|

## The cleanest narrative for the pitch

Combining the recommendations above into a single coherent story:

> "Agent Market is a curated marketplace where users hire AI agents per operation, pay USDC
> on Arc, and audit a verifiable passport of every agent's prior work. Our lead demo agent
> is an on-chain research agent. Our second demo agent — directly building on one of
> Canteen's own RFB suggestions — is a news-to-prediction-market translation agent.
> Trading agents will live on the platform too, but we explicitly chose verticals where
> the reputation system's defensibility is strongest."

This:

- Anchors the pitch in our own thesis.
- Demonstrates we read and engaged with Canteen's RFBs.
- Shows extensibility by listing a second demo vertical.
- Inoculates against "why not trading?" by acknowledging it openly.

## What we'd need to commit to today

If the team agrees with this recommendation:

1. **Lead demo vertical: on-chain research.** Build first.
2. **Secondary demo vertical: news-to-prediction-market translation.** Build if week-1
   capacity allows; pitch-deck-only if not.
3. **Don't commit to RFBs i, ii, or iii directly.** Reference in the deck for credibility.

## Open questions

1. **Does the team want to dual-track research + translation, or single-track research?**
   The dual-track is more impressive but adds risk.
2. **Native-language fluency in a non-English market is well-covered on this team.** Önder
   (Turkish, Ankara) is a particularly strong fit — Turkish-market macro news → English
   prediction-market questions is the canonical RFB iv shape, and Turkey's macro environment
   has been producing market-relevant events at high volume. Daniel R (Portuguese, Brazil)
   covers Latin American markets; Shimon (Hebrew, Israel) covers Middle East; Chuan possibly
   Mandarin (confirm). The translation angle has multi-language depth on this team. A native
   fluency angle would make the translation demo more credible.
3. **Are we willing to mock Polymarket integration?** Or should we just demonstrate the
   "translated question" output without actual market posting? Recommendation: mock for v1;
   real integration is a v2 conversation.
