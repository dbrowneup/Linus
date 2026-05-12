# Agent Marketplace — Competitor Landscape

> **Date:** 2026-05-11 (Day 1 of the Agora hackathon)
> **Audience:** Agent Market hackathon team (Shimon, Marten, Daniel R, Dan, Chuan, +1)
> **Purpose:** Map the existing agent-marketplace landscape so we (a) don't pitch as if greenfield,
> (b) find a defensible wedge, and (c) anticipate the comparisons judges will make.
>
> **Confidence note:** This brief synthesizes public information as of the author's knowledge
> through early 2026. The crypto / AI-agent space moves fast and product details (token mechanics,
> chain choices, feature sets) can shift week-to-week. Before any of this lands in a public pitch
> deck, **verify the specifics for each named competitor** via their docs or recent posts — this
> doc is a starting map, not a final reference.

## TL;DR (pitch-ready positioning)

> The agent marketplace category is real, well-funded, and lacks a clear winner. Most existing
> players bundle agent listing with **speculative token economics** — users buy an agent's token
> for upside exposure or stake a protocol token to operate agents. None of them have made
> hire-an-agent-for-one-job-and-pay-stablecoin the dominant flow. **Agent Market's wedge is
> pay-per-operation pricing in USDC on Arc, with a verifiable agent passport that bases reputation
> on what each agent actually did, not on what its token price implies.** Pay-per-op + stablecoin +
> verifiable history is the combination none of the named competitors currently lead with.

**One-sentence form** for the pitch deck:

> "While Olas, Virtuals, Bittensor, and ai16z have built agent ecosystems around speculative
> tokens, Agent Market is the first marketplace where you simply hire an agent, pay USDC per
> operation, and see a verifiable record of what it did."

## How to read this brief

For each competitor we cover:

- **What they are** — one paragraph
- **Mechanism** — how an agent gets listed, hired, and paid
- **Monetization** — where the revenue / value capture sits
- **What they're missing** — relative to Agent Market's target wedge

Then a cross-cutting matrix and a positioning recommendation.

---

## Competitor 1 — Olas / Autonolas

**What they are.** A DAO-governed protocol for "autonomous services" — code that runs continuously
on behalf of an owner (e.g., a prediction-market trading agent, an autonomous DAO contributor).
Their consumer product is **Pearl**, a desktop app where users stake the OLAS token to run hosted
services on their own machines.

**Mechanism.** A developer publishes a service spec (a Docker image plus a manifest) to the
protocol registry. Users stake OLAS tokens to activate a service; once activated, the service runs
24/7 on node operators' machines and the user earns rewards in OLAS for keeping it active. Services
are not "hired per operation" — they are continuously-running entities.

**Monetization.** Native OLAS token emissions reward service operators. Protocol revenue
(currently) is implicit in token economics rather than a direct fee.

**What they're missing.** Pay-per-operation pricing — the model is staking-based, not job-based.
Stablecoin-native settlement — value capture is entirely in the protocol's native token. The
"continuously running service" framing is also a heavier user commitment than "hire this agent to
do one thing for me."

**Reading for our positioning.** Olas owns the "autonomous service" vertical. We're explicitly
NOT competing for that user — we want the user who has a discrete job and wants it done once.
Different audience, different unit of consumption.

---

## Competitor 2 — Virtuals Protocol

**What they are.** A protocol on Base (and other EVM chains) that tokenizes individual AI agents.
Each agent gets its own ERC-20 token; holders effectively own a share of the agent's future
revenue. Best-known agents on Virtuals include AIXBT, Luna, and a long tail of consumer agents.
Through 2024–2025 this protocol had significant attention and a large market cap concentrated in
its flagship agent tokens.

**Mechanism.** A developer launches a new agent and a bonding curve mints the agent's token. Users
who believe in the agent buy the token; the agent then "earns" revenue (often advertising or
content-creation revenue) which flows back to token holders via a share-of-revenue mechanism. Users
don't hire the agent for jobs — they own it.

**Monetization.** Protocol fees on bonding-curve transactions, token-launch fees, and a share of
agent revenue captured by the protocol.

**What they're missing.** A simple hire-this-agent-for-one-job flow. The Virtuals model is
investment-shaped, not consumption-shaped. Users who want to USE an agent (rather than HOLD its
token) get a strictly worse UX. USDC-stable pricing is also absent — agents are priced in their own
volatile tokens.

**Reading for our positioning.** Virtuals is the loudest comp and the one judges are most likely
to bring up. The fair contrast: **Virtuals lets you bet on an agent; Agent Market lets you hire
one.** Different fundamental relationship to the agent. Their unit economics depend on speculation;
ours depend on the agent actually doing useful work that users will pay for.

---

## Competitor 3 — Bittensor

**What they are.** A decentralized AI / agent network organized into "subnets" — each subnet is
its own specialized service (image generation, text generation, prediction markets, etc.). Validators
and miners on each subnet are rewarded in the network's native TAO token based on the quality of
work they produce.

**Mechanism.** Operators run miners on a subnet, producing model outputs in response to queries.
Validators score the miners and TAO emissions flow accordingly. Subnet owners design the
incentive function for their subnet. End-user-facing applications consume subnets through API
adapters.

**Monetization.** Token emissions (TAO) to validators, miners, and subnet owners. Subnet owners can
charge inference fees in TAO.

**What they're missing.** Consumer-facing marketplace UX — Bittensor's audience is researchers,
miners, and operators, not "I need this job done today" users. Stablecoin pricing is absent.
End-to-end "I hire an agent and see results" is not the design center.

**Reading for our positioning.** Bittensor is upstream infrastructure (decentralized AI inference)
where Agent Market is downstream consumer surface (hire an agent for a job). The right comparison
is "Bittensor is to AI inference what AWS is to compute; Agent Market is to AI agents what Fiverr
is to freelancers." We could in principle use Bittensor subnets as backing infrastructure for some
Agent Market agents in v2.

---

## Competitor 4 — Fetch.ai / ASI Alliance

**What they are.** One of the original "autonomous economic agent" protocols. As of late 2024,
Fetch.ai merged into the **ASI (Artificial Superintelligence) alliance** with SingularityNET and
Ocean Protocol, consolidating three older agent / AI tokens. Their consumer-facing agent
marketplace (DeltaV) has had mixed traction historically.

**Mechanism.** Agents register on the network with a service description; users (or other agents)
discover agents via a search/dispatch layer; transactions settle in the alliance's native FET (now
ASI) token.

**Monetization.** Native-token fees on agent transactions; broader protocol economics tied to the
ASI merger.

**What they're missing.** Recent consumer traction is uncertain post-merger. Stablecoin pricing
is absent. The agent-to-agent framing is more developer-facing than user-facing.

**Reading for our positioning.** Fetch.ai is the closest historical analog to what Agent Market is
trying to do (agent registry + discovery + settlement), but their model has been native-token-only
and the consumer hire-flow has not been the dominant use case. The merger creates strategic
uncertainty. We don't need to be unkind about it — just observe that the "FET-priced agent
transactions" pattern hasn't broken out to mainstream users in five years, and there's likely a
reason (volatility, complexity, lack of consumer UX).

---

## Competitor 5 — ai16z / ElizaOS

**What they are.** **Eliza** is an open-source agent framework (TypeScript, very large GitHub
star count, broad community) maintained by the ai16z DAO. The framework lets developers build and
deploy autonomous agents with personalities, memory, and tool use. The **ai16z** token is the DAO's
governance / treasury token. There is no canonical "marketplace" product yet, though many ecosystem
projects layer marketplace-like features on top of Eliza.

**Mechanism.** Developers build agents using the Eliza framework and deploy them where they like
(X/Twitter, Discord, custom UIs). The ai16z DAO holds a treasury that invests in agent projects
built on Eliza, and the token represents exposure to that portfolio.

**Monetization.** Token-based; treasury-investment-shaped rather than fee-on-transaction.

**What they're missing.** A first-party marketplace product. Eliza is **framework**, not
**marketplace**. Stablecoin per-op pricing is absent.

**Reading for our positioning.** Eliza is potentially a **partner** more than a **competitor** —
many agents listed on Agent Market could be built using Eliza. We don't compete with the framework
layer; we compete with whoever ships a great marketplace built ON frameworks like Eliza. The pitch
position: "Eliza, AutoGen, LangGraph — pick your framework. Agent Market is where you bring the
agent and start earning."

---

## Competitor 6 — Theoriq

**What they are.** A protocol for "modular agent collectives" — composable agents that can be
combined into multi-agent workflows, with cryptographic attestations of reasoning steps. Theoriq
has emphasized **verifiable agent collectives** as their core thesis.

**Mechanism.** Agents register with a typed interface, can be composed into workflows, and produce
attested outputs that can be verified against the protocol's specification.

**Monetization.** Native-token economy.

**What they're missing.** Consumer-facing simplicity — the framing of "modular collectives" is
developer-attractive but user-confusing. Stablecoin pricing is absent.

**Reading for our positioning.** Theoriq is the closest competitor on the **verifiable reasoning**
axis — they emphasize attested outputs in a similar spirit to what we're doing with the agent
passport. The difference: their attestation lives in their own protocol's typed-interface
abstraction; ours lives in content-hashed reasoning traces anchored to standard infrastructure.
Worth tracking. If they ship something we don't, we should know quickly.

---

## Competitor 7 — MyShell

**What they are.** A consumer-facing AI agent app store, primarily Asian-market-focused. Each
agent has a native token; users buy/hold the token for usage rights and a share of agent revenue.
Strong on voice agents, chat agents, and entertainment use cases.

**Mechanism.** Developers publish agents; users buy `$SHELL` token or per-agent tokens for usage.
The model is closer to "freemium app store" than to pay-per-op.

**Monetization.** Native token economy, app-store fees.

**What they're missing.** Financial / utility verticals (their lane is entertainment + consumer
AI). Stablecoin pricing. B2B-style hire-for-a-job flow.

**Reading for our positioning.** Different vertical, different audience. Less directly comparable
to Agent Market. Useful to acknowledge in the deck only if a judge brings them up.

---

## Honorable mentions (not deep-dived)

- **AutoGen / LangGraph / CrewAI** — multi-agent **frameworks**, not marketplaces. Like Eliza,
  these are upstream of what Agent Market lists, not competitive with it.
- **HuggingFace Spaces** — model hosting platform, not agent marketplace, but increasingly hosts
  agent demos. Different category; worth noting for completeness.
- **Anthropic / OpenAI agent products** — first-party hosted agents from foundation-model providers.
  Different value proposition: their agents are bound to their models; ours are model-agnostic and
  use MCP to plug into any tool surface.
- **Polymarket / Hyperliquid leaderboards** — referenced by Canteen as inspiration for the slash-
  bond / copy-trading RFB ideas. These are venues for SPECIFIC kinds of agent activity, not
  marketplaces. If a copy-trading vertical were ever Agent Market's lead, these would become
  reference points; for now they're context.

---

## Cross-cutting positioning matrix

| Competitor    | Pricing model         | Settlement asset    | Reputation primitive    | Primary audience           |
| ------------- | --------------------- | ------------------- | ----------------------- | -------------------------- |
| Olas          | Staking-based         | OLAS token          | Stake-weighted          | Operators, prediction nerds|
| Virtuals      | Token ownership       | Agent's ERC-20      | Token price (proxy)     | Crypto speculators         |
| Bittensor     | Validator emission    | TAO                 | Validator scoring       | Researchers, operators     |
| Fetch / ASI   | Per-transaction       | FET / ASI           | Self-reported           | Developers (mostly)        |
| ai16z / Eliza | Token treasury        | ai16z token         | (Framework, not market) | Builders                   |
| Theoriq       | Per-transaction       | Native token        | Cryptographic attestation| Developers                |
| MyShell       | Token-gated           | $SHELL + agent tokens| Usage-weighted         | Consumer (entertainment)   |
| **Agent Market** | **Pay-per-operation** | **USDC on Arc**  | **Verifiable history (passport)** | **People with a job to do** |

The bottom row is the clean differentiation story. Four columns, four wedges. No single competitor
matches the four-way combination.

---

## Where Agent Market wedges (the three honest claims we can make)

1. **Pay-per-operation pricing in stablecoins.** Nobody named above leads with this. The closest is
   Fetch.ai's per-transaction model, but it settles in a volatile native token, which is not the
   same product. Stablecoin per-op + Arc's cheap fast settlement is the unlock that makes
   small-dollar agent hires viable.

2. **Verifiable agent passport.** Theoriq is the only direct competitor on this axis and they
   couch it inside a protocol-specific typed-interface abstraction; we anchor it in content-hashed
   reasoning traces that any user can verify against an off-chain store. The passport-as-history
   discipline (we report what happened, not what we predict will happen) is a positioning
   commitment we can make confidently.

3. **Framework-agnostic listing.** We don't tie agents to a single framework (Eliza, AutoGen,
   LangGraph, or our own). Developers bring whatever stack they like, expose tools via MCP, and
   list. This is a defensible position **only if we commit to real MCP** (not "MCP-style"), because
   MCP is what makes the framework-agnostic promise concrete rather than marketing.

## Risks the landscape implies

- **Virtuals is the elephant in the room.** Their market cap means many judges will benchmark
  against them. Be ready with a sharp "they let you bet, we let you hire" line.
- **Verifiable-trace claims need to be backed by actual implementation.** Theoriq has been talking
  about attestation longer than we have. If the agent passport in our demo is a stub, the
  differentiation collapses. The passport schema + at least one trace-verification flow needs to
  ship by demo day.
- **"Pay-per-operation in stablecoins" sounds obvious in 2026.** Someone is likely already
  building this; we should monitor the hackathon's other submissions and recent Crypto-AI launches.
  Differentiation may need to be sharpened mid-hackathon as the landscape clarifies.
- **MCP commitment matters for the framework-agnostic claim.** Without real MCP, the framework-
  agnostic argument is weakened to "you can integrate however you like" — true of every API. With
  real MCP, the argument is "the protocol AI providers are converging on as the tool standard is
  what we natively speak." Different conversation.

---

## Open data points worth confirming before pitch day

- Virtuals' current top-agent market cap (was multi-hundred-million peak; check recent state).
- Whether Olas has shipped or signaled any per-op or stablecoin-pricing direction.
- Theoriq's current product surface and whether their attestation feature is shipped vs. specced.
- Recent Crypto-AI hackathon winners (search "Coinbase agent hackathon" / "Circle agent hackathon"
  / "x402 hackathon" for the last 6 months) — is there a winner we should know about?
- Whether `@x402/mcp` has shipped a stable spec yet (relevant for our MCP positioning and
  monetization-via-MCP story).
- Whether anyone has launched a "stablecoin pay-per-op AI agent marketplace" in the last 90 days
  that would invalidate the "nobody leads with this" claim.

A two-hour focused search before the pitch deck is final would confirm or refute each of these.

---

## Recommended pitch-deck slide (one slide, three columns)

```
HOW PEOPLE BUY AGENTS TODAY                  HOW PEOPLE SHOULD BUY AGENTS
─────────────────────────────                ────────────────────────────
Virtuals — buy the agent's token             Agent Market — hire the agent for one job
Olas — stake the protocol's token            Pay USDC. Watch it work. See what it did.
Bittensor — run a miner                      Verifiable history, not token-price proxy.
Eliza/ai16z — buy the framework's token      Framework-agnostic, MCP-native.
MyShell — buy the agent's token              No speculation required.
Fetch/ASI — pay in volatile native token

→ Speculation as the access model            → Consumption as the access model
```

The frame: most of the landscape is "buy upside exposure to agents." Our frame is "buy a job
done." That's the wedge, and it's clean to draw on a single slide.

---

_Maintainer note: this brief should be re-validated before the pitch deck is final. The crypto
landscape moves fast; a 2-week-old competitor analysis can be obsolete. Treat this as the starting
map, not the final reference._
