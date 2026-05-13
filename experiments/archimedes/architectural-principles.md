# Architectural Principles for a Defensible Portfolio Agent

> **Audience:** Archimedes hackathon team
> **Purpose:** Establish the design philosophy underneath the strategy passport, the on-chain
> reasoning-trace anchoring, and the non-custodial vault. This is the "why" doc; the "what"
> details live in the specs in [`specs/`](specs/) and in Chuan's
> [`design.md`](design.md).

## The frame: portfolio agents that don't ship verifiable history don't earn trust

Every portfolio agent — robo-advisor, DeFi yield aggregator, copy-trading platform, AI
trading product — makes a competence claim of some kind. The differences are in **what
backs the claim**. Three categories:

1. **Self-reported metrics.** "Our AI delivered 18% returns last year, trust us." Cheapest
   to ship; weakest defensibility. The user has no way to audit how the returns were
   generated, what risks were taken, or whether the methodology survives out-of-sample.
2. **Audited backtests.** "Here's our 10-year backtest, audited by Firm X." Better than
   self-report, but the user still can't audit a *specific* portfolio decision the agent
   made — only the aggregate historical claim.
3. **Verifiable per-decision history.** A machine-readable record of every decision the
   agent makes — what regime it detected, which strategies it selected, why it allocated
   weights as it did, what trades it executed — with each decision's reasoning trace
   hashed and anchored on-chain. This is what Trading-R1 (Wang et al. 2025,
   [arxiv:2509.11420](https://arxiv.org/abs/2509.11420)) calls "reasoning trace as the
   product."

**Archimedes' reputation system is in category 3.** This is the load-bearing architectural
commitment from which everything else flows.

## Why category 3 is non-negotiable

Three independent arguments converge:

1. **The market is crowded with category-1 and category-2 products.** Wealthfront,
   Betterment, Schwab Intelligent Portfolios, every DeFi yield aggregator, every "AI ETF"
   on Twitter — none of them surface per-decision auditable reasoning. Without that, we're a
   late entrant to a saturated category.
2. **The Agora hackathon's framing rewards it.** [Canteen's positioning](https://luma.com/7i50p2r9):
   *"AI agents are the new citizens... continuous, comparative reasoning... treat the agora
   as substrate."* The Agora's whole pitch is that markets are information-processing
   machines; reasoning traces ARE information. RFB 04's "Adaptive Portfolio Manager" lives
   most credibly when each adaptation has an auditable reasoning trail.
3. **Past performance does not persist out-of-sample.** This is the canonical failure mode
   of leaderboard-based reputation (see [`reputation-and-vertical-selection.md`](reputation-and-vertical-selection.md)
   in the prior agent-marketplace work; the same principle applies). A portfolio agent
   that claims "X% returns last year, so you can trust me" inherits the regression-to-mean
   problem of every leaderboard. **Verifiable reasoning history bypasses the prediction
   problem**: we don't claim the past predicts the future; we claim the past is auditable.

## The three primitives that make verifiable history work

These are the architectural commitments. Schema details in
[`specs/strategy-passport-spec.md`](specs/strategy-passport-spec.md); principle here.

### Primitive 1: paper-claim binding (the strategy passport)

Every strategy in the library carries a verifiable provenance trail:

- **Source paper(s):** arxiv ID, title, authors, publication venue, our methodology
  summary.
- **Methodology hash:** a content-hash of the extracted methodology — what the LLM read
  from the paper and turned into a strategy definition.
- **Backtest results:** Sharpe, Sortino, max drawdown, CAGR, equity curve, the works.
  Critically: comparison against the paper's *claimed* metrics. If the paper said Sharpe
  4.6 and our re-implementation got Sharpe 1.8, we record and surface the delta.
- **Validation gate timestamp:** when did this strategy graduate from "candidate" to
  "validated" to "live"?
- **Curator signature** (v1 — Dan's wallet): an audit trail of who vetted the strategy.

The strategy passport answers: *"Why should I trust this strategy?"* with concrete,
verifiable answers rather than self-reported metrics.

### Primitive 2: reasoning trace (the decision passport)

For every agent decision (portfolio construction, rebalance, strategy rotation, regime
change), capture:

- **The trigger** that caused the decision (drift threshold, regime change, calendar,
  strategy decay).
- **The market context** at decision time (regime classification, key metrics, correlations).
- **The reasoning** — LLM-generated explanation of why the decision was made, what
  alternatives were considered, what tradeoff was made.
- **The action taken** — concrete trades, weight changes, rebalance details.
- **The expected outcome** — what the agent predicts will happen.
- **The content hash** of the full trace.
- **The on-chain anchor tx hash** — recorded on Arc via the ReasoningTraceRegistry
  contract.

Each decision is a single record; the user's full decision history is queryable in order;
any decision can be audited end-to-end.

### Primitive 3: tool-call provenance

For every tool the agent invoked during a decision (market data fetch, paper search,
regime computation, USYC yield lookup), capture which tool was called, the inputs, and the
outputs. This is what makes the agent's *information surface* auditable.

- A reasoning trace can claim "I checked the VIX and saw it spike to 35," but without
  tool-call provenance, that's just a claim.
- Provenance proves the agent had that specific tool, queried it with that specific
  input, and got that specific output.
- Critically, this enables backtesting the *agent's behavior* on historical data — if the
  agent's tool calls are recorded, we can replay them later with different LLM prompts
  and see how decisions would have differed.

## The three layers, named explicitly

Borrowing a framing from prediction-market architecture (Canteen's _Unbundling the
Prediction Market Stack_ post):

- **Agent layer** — the LLM-driven thing that does the work (strategy selection, regime
  detection, rebalance execution). Producible from any framework; framework-agnostic by
  design.
- **Identity layer** — the strategy passport + reasoning trace + tool-call provenance.
  Verifiable, hashed, on-chain-anchored. **This is what Archimedes actually owns and
  operates.**
- **Venue layer** — Arc as the settlement substrate. Sub-second finality, USDC
  denomination, ~$0.01 fees via Paymaster.

Most portfolio products fold these together (the agent's logic is the platform's IP, the
identity is opaque, the venue is implicit). **Archimedes keeps them explicitly decoupled**
because that's the architectural choice that makes "paper-grounded provenance +
MCP-native + verifiable history" credible as a pitch.

## Design constraints these primitives imply

Once you commit to the three primitives, several design choices are forced:

1. **You commit to an on-chain anchoring path.** The verifiability depends on the hash
   being checkable independent of the platform. Chuan's
   [`design.md` § 5.2](design.md) specifies this as `ReasoningTraceRegistry.sol`. Don't
   skip it.
2. **You commit to content-hashing as the integrity primitive.** Not signatures, not
   platform attestations. The trace is what it is; any change to it changes the hash;
   anyone with the trace can verify it themselves.
3. **You commit to "verifiable history, not predictive performance" as the reputation
   thesis.** Don't ship a numeric score that claims to predict future performance. Ship
   the queryable, auditable history.
4. **You commit to non-custodial settlement.** Platform never holds user funds. ArchimedesVault
   contracts hold USDC; agent has rebalance authority only, not withdraw-to-platform
   authority.
5. **You commit to paper-grounded curation, not LLM-blind ingestion.** Strategies come
   from real published research with verifiable methodology. The arxiv pipeline can
   *propose* strategies, but a human curator (Dan in v1) validates before listing.

## What this doesn't commit you to

A short list of architectural choices that are NOT forced by these principles — they remain
open, and the team can pick later:

- **Encryption of traces.** v1 traces are public. v2 can add encrypt-trace +
  share-key-with-buyer for use cases where strategy secrecy matters.
- **Slashing for bad agent performance.** Don't ship in v1. The passport with verifiable
  history is already a defensible reputation system; slashing adds complexity without
  proving the wedge.
- **Token economics.** No native token. Take-rate on USDC settlement + USYC yield share
  is the revenue model.
- **Specific UI patterns for the reasoning trace.** The data model dictates what's
  possible; how the team renders it (timeline view, decision drilldown, trace viewer) is
  a separate decision.
- **Specific LLM provider.** Claude API for v1; multi-provider support is a v2 question.

## How to evaluate proposed features against these principles

When the team is deciding whether to add a feature, run it through this filter:

1. **Does it make any prior decision's record less auditable?** If yes, push back hard.
2. **Does it tie reputation to predicted performance rather than actual history?** If yes,
   replace with a history-based equivalent.
3. **Does it move user funds into platform custody?** If yes, redesign.
4. **Does it lock us into a single framework or LLM provider?** If yes, push back.
5. **Does it bypass the paper-claim binding?** (E.g., "let users submit untested strategies
   directly.") If yes, push back — the paper-grounded curation is part of the pitch.

A feature that fails any of these is a feature that erodes the architectural moat.
Sometimes it's worth the erosion (e.g., a v2 fiat on-ramp may require custodial
intermediaries — but that's a known v2 conversation). For v1, hold the line.

## How this differs from the prior agent-marketplace work

Some of these principles are direct ports of the architectural thinking that went into
the prior agent-marketplace project. The translation:

- **Agent passport → strategy passport.** Same primitive (verifiable identity for an
  agent's work), applied to strategies instead of generic agents.
- **Reasoning trace → reasoning trace.** Same primitive; same on-chain anchor pattern.
- **Tool-call provenance → tool-call provenance.** Same.
- **Verifiable history > predicted performance.** Same thesis.
- **Non-custodial escrow → non-custodial vault.** Same pattern; the contract surface is
  different (a vault holds aggregate user deposits + RWA tokens rather than per-job
  escrows), but the principle that the platform never custodies is identical.

What's NEW for Archimedes:

- **Paper-claim binding.** This is specific to Archimedes' strategy-engine framing — the
  agent's strategies come from published research, and the provenance trail back to the
  paper is part of the verifiable history. The agent-marketplace project didn't have an
  equivalent because agents there could be anything; Archimedes constrains itself to
  paper-grounded strategies precisely because that constraint is the defensibility moat.
- **Methodology re-validation.** We don't trust the paper's claimed metrics; we re-run the
  backtest and surface the delta. This is a quality discipline the prior work didn't need.

---

_The core claim of this doc: paper-grounded provenance + on-chain reasoning trace anchoring
+ non-custodial settlement is the architectural commitment that makes Archimedes' pitch
survive contact with a saturated robo-advisor / DeFi-yield-aggregator / AI-portfolio market.
Everything else flows from this._
