# Reputation and Vertical Selection

> **Audience:** Agent Market hackathon team
> **Purpose:** Make two decisions explicit: (1) the reputation system's design philosophy, and
> (2) the demo vertical. Both decisions are interlocked because the trading vertical concentrates
> the reputation-gaming risk and the vertical we choose shapes how the passport is built.

## Part 1 — Reputation gaming, and why "verifiable history" is the only honest answer

### The leaderboard problem

The simplest reputation system is a leaderboard: "the agent with the highest historical
performance ranks first." This is the model Hyperliquid uses for trader leaderboards; it's the
model Polymarket effectively uses for top forecasters; it's the implicit model behind
Virtuals' token-price-as-reputation pattern.

It does not survive contact with empirical reality. **Past performance on a leaderboard does
not persist out of sample.** This is well-documented in the financial literature
([Sharpe, 1966](https://www.jstor.org/stable/2351741);
[Carhart, 1997](https://www.jstor.org/stable/2329556)) and is the explicit motivation behind
the [Canteen RFB iii — slash-bonded copy-trading](https://canteenapp.com/blog) prompt, which
asks builders to encode the empirical decay function as a slash schedule.

Why doesn't it persist?

- **Survivorship bias.** Leaderboards display survivors. Bad-luck losers are invisible.
- **Small-sample artifacts.** A trader with 20 good trades and 0 bad trades may have skill, may
  have luck, or may be in a market regime that suits their strategy temporarily. The data
  doesn't distinguish.
- **Regime change.** A strategy that was great in one market environment fails when the
  environment shifts. Past results are partial information about future results.
- **Gaming.** As soon as a leaderboard has value, people game it — sybils, churn-and-burn
  accounts, coordinated voting rings, fake trades for self-confirmation.

Building a reputation system on a leaderboard mechanic and claiming "the best-performing
agents charge more" is structurally vulnerable to all of these failure modes.

### The verifiable-history alternative

Instead of asking "which agent will be best in the future?" — a prediction problem nobody can
solve well — ask "what has this agent actually done?" That's a recall problem, which is
trivially solvable: store the data, make it queryable.

Concretely, instead of an aggregate rating, the passport surfaces:

- **What jobs the agent has completed.** With timestamps, costs, and outputs.
- **The reasoning trace for each job.** Auditable by anyone who wants to inspect.
- **The tools the agent used.** Verifiable against an MCP manifest.
- **The user's feedback on the job.** Captured but not aggregated into a single number.

Future buyers can read the history and make their own assessment of whether the agent suits
their job. The platform is not predicting performance; it's providing the data buyers need to
predict for themselves.

This is the architecture the [`architectural-principles.md`](architectural-principles.md)
document specifies in detail. The reputation system is the user-facing presentation of those
primitives.

### What we say about reputation in the pitch

Three short claims, all defensible:

1. "Reputation in Agent Market is built from verifiable history, not from token prices or
   self-reported metrics."
2. "Buyers can audit any prior job before hiring an agent, including the reasoning trace and
   tools used."
3. "We don't claim the past predicts the future. We claim the past is auditable."

Each of these is concrete, falsifiable, and survives skeptical questioning.

### What we DO NOT say in the pitch

- "Our reputation system predicts future agent performance better than competitors." (Cannot
  be defended; nobody's system does this well.)
- "Bad agents get slashed automatically." (We don't ship slashing in v1.)
- "The best agents always rise to the top." (No empirical basis; in fact the opposite is the
  baseline expectation.)
- "We use AI to detect bad agents." (Hand-wavy; we don't ship this.)

## Part 2 — Demo vertical selection

### Why this decision matters now

The demo vertical determines:

1. **Which judges resonate.** Crypto-finance judges vs. AI/automation judges have different
   sensibilities.
2. **What tools the demo agents need.** A trading agent needs market data feeds; a research
   agent needs document search; a translation agent needs LLM APIs. Different MCP surfaces.
3. **How regulatory-shaped the conversation gets.** Trading agents draw regulatory attention;
   non-trading agents don't.
4. **How credible the reputation system is.** Trading reputations decay; research reputations
   are more durable.
5. **Whether Dan's domain credibility (scientist) or Chuan's domain credibility (quant
   trading) anchors the pitch.**

### The case against trading as the lead demo

The Day-1 evaluation already established this; it bears repeating because it's tempting to
default to trading given Chuan's background and the hackathon's crypto-finance audience.

- **Regulatory exposure.** A "trading agent" that recommends or executes trades in front of
  judges from Circle is making a public statement about a regulated activity. Even on testnet,
  the framing matters.
- **Custody complexity scales.** Trading agents need access to user funds in a way research
  agents don't. The escrow model handles this, but the demo's narrative gets harder.
- **Reputation credibility on small samples is the hardest case.** As discussed above, trading
  performance is the canonical example of leaderboard-rank decay. The pitch becomes
  "our agent did 5 simulated trades successfully" — which doesn't impress anyone who has spent
  any time in markets.
- **The category is overcrowded at this hackathon.** The Canteen RFBs are all crypto-finance.
  Olas Pearl's traction is mostly prediction-market trading. Every hackathon team is
  defaulting to trading. **Being the trading team in a room of trading teams is the wrong
  positioning move.**

### Better vertical candidates

In rough order of "easy to ship a good demo in two weeks":

1. **On-chain research / whale watching.** "Hire an agent to research a wallet, a token, a
   protocol — get back a structured report with primary-source citations." Reuses MCP tools
   for chain data ([Etherscan](https://etherscan.io/),
   [DeFiLlama](https://defillama.com/), [Dune](https://dune.com/), block explorers).
   Reputation gaming is hard because the output is auditable text, not a numerical
   performance claim.

2. **News-to-prediction-market translation.** This is the Canteen RFB iv prompt explicitly —
   "agents bid in USDC for the right to translate a non-English news event into a Polymarket-
   shaped question, with builder fees flowing back to the translator on every fill." This has
   the appealing property that the agent's output (a well-formed prediction-market question)
   is concrete and judgeable on the spot.

3. **Document / content summarization with citations.** "Hire an agent to summarize a 200-page
   document with citations to specific passages." Demos well because the output is concrete;
   reputation system works because the citations either back the claims or they don't.

4. **Compliance / signal verification.** "Hire an agent to verify whether a specific on-chain
   action looks like a sanctioned-address interaction." Niche but credible.

5. **Code review / vulnerability analysis (on-chain).** "Hire an agent to read this contract
   and flag the likely vulnerabilities." Plays well in a crypto audience; reputation system
   works because the agent's analysis can be cross-checked against known CVEs.

### The recommendation

**Use on-chain research as the lead demo vertical.** Specifically: "hire an agent to research
a wallet (or token, or protocol) and produce a structured intelligence report with primary-
source citations."

Why this specifically:

- **Reuses existing MCP tools.** Etherscan, DeFiLlama, Dune, block-explorer APIs all have
  available adapters and we can build the rest as MCP servers in days.
- **The agent's output is concrete and auditable in real-time.** The judge can click a
  citation and verify it.
- **Reputation system is credible.** Past research reports are durable artifacts.
- **No regulatory exposure.** Research is journalism; it's not a regulated activity.
- **Custody is simple.** User pays for a research job; agent delivers a report; settlement
  triggers.
- **Differentiates from every other team.** Every other hackathon team will demo trading;
  we'll demo research.

### Trading lives in the pitch deck, not the demo

We can still talk about trading, just not as the live demo.

- **Pitch deck slide 4 or 5: "What else lives on Agent Market?"** Show that the platform is
  vertical-agnostic; trading agents can be listed alongside research, translation, code-review,
  compliance. Use Chuan's quant credibility to make this slide credible.
- **In judging Q&A: "Why didn't you demo trading?"** Answer: "Because trading reputation is a
  prediction problem and our wedge is verifiable history. The trading vertical will work on
  Agent Market the day someone builds a trading agent with a passport you can audit. Until
  then, we showed you the verticals where the architecture is most clearly defensible."

### Vertical-selection summary

| Vertical                       | Demo build cost | Judging fit | Regulatory   | Reputation credibility |
| ------------------------------ | --------------- | ----------- | ------------ | ---------------------- |
| Trading                        | Medium          | High        | High risk    | Low (decay)            |
| **On-chain research (rec.)**   | **Low**         | **High**    | **Low**      | **High**               |
| Prediction-market translation  | Medium          | High        | Medium       | Medium                 |
| Document summarization         | Low             | Medium      | Low          | High                   |
| Compliance / signal verification | Medium          | Medium      | Low          | High                   |
| Code review                    | Medium          | Medium      | Low          | High                   |

On-chain research is the dominant choice on this matrix. The rest are good backup options.

## Bringing it together

The reputation system and the vertical choice are entangled. Trading concentrates the
reputation-gaming problem; non-trading verticals make verifiable history easier to ship and
easier to defend.

**Recommendation:**

1. Build the reputation system on **verifiable history**, not aggregate ratings or token
   prices. Implementation per [`architectural-principles.md`](architectural-principles.md)
   and [`agent-passport-spec.md`](agent-passport-spec.md).
2. Choose **on-chain research** as the demo vertical. Trading lives in the pitch deck as a
   showcase of platform extensibility, not in the demo build.
3. Use Dan's scientific credibility and Chuan's quant credibility as **pitch-deck assets**,
   not as demo-vertical anchors.
