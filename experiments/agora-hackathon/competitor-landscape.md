# Agent Marketplace — Competitor Landscape

> **Updated:** 2026-05-12 (Day 2 of the Agora hackathon)
> **Audience:** Agent Market hackathon team
> **Purpose:** Map the existing landscape with verifiable sources, identify the genuine wedges,
> and surface a critical new competitive finding: **Circle has launched its own first-party agent
> marketplace stack**, which materially changes positioning.
>
> **Every claim below carries a primary-source link.** Where I describe product features or market
> numbers, the link goes to either the company's own documentation, a press release, or a
> reputable third-party source (CoinMarketCap, Messari, The Block). When in doubt, follow the link.

## The headline finding nobody on the team has surfaced yet

**Circle launched [Agent Stack](https://decrypt.co/367490/circle-ai-agents-usdc-stablecoin-powers-222m-arc-token-sale) on
May 11, 2026 — the same week this hackathon began.** Agent Stack is a
[suite of Circle-native developer tools](https://www.stocktitan.net/news/CRCL/circle-launches-ai-infrastructure-to-power-the-agentic-3j0lw9rke3ev.html)
that includes:

- **Agent Wallets** — programmable wallets purpose-built for autonomous agents
- **Agent Marketplace** — a Circle-operated marketplace where agents can browse and pay for
  services from other agents
- **Nanopayments** — micropayments down to $0.000001 per transaction via Circle Gateway
- **Circle CLI** — developer tooling for the agent stack

Circle's marketplace component is the same problem space the hackathon is asking teams to build
in. Circle [raised $222M in an Arc token presale](https://decrypt.co/367490/circle-ai-agents-usdc-stablecoin-powers-222m-arc-token-sale)
at a $3B fully-diluted valuation alongside the launch, with BlackRock among the named investors.
The sponsor of this hackathon is building a first-party version of the product they have asked
hackathon teams to ship.

**This is not a death knell. It is a positioning constraint.** Agent Market needs to be either
(a) a thin polished surface that consumes Circle's primitives and adds clear opinionated UX value,
(b) a vertical or experience that Circle's generalist marketplace won't go deep on, or (c) a
direct test of whether a community-curated marketplace can outcompete an infrastructure-provider-
operated one. Pick deliberately. Pitching as if Circle's marketplace doesn't exist will not work
with these judges.

---

## TL;DR (pitch-ready positioning, revised)

> The "USDC-pay-per-operation AI agent marketplace" thesis is no longer differentiating on its
> own — Circle ships it as infrastructure, [Swarms](https://swarms.world/) ships it as marketplace,
> [Olas Pearl](https://olas.network/) ships it with [x402](https://www.x402.org/) integration.
> What's still genuinely missing in the field: **a curated, verifiable, UX-first agent marketplace
> where reputation is grounded in machine-readable history rather than token economics**. That's
> the wedge Agent Market can credibly claim if we ship the agent passport with content-hashed
> reasoning traces. Without that primitive, we're a thin reskin of products that already exist.

**One-sentence pitch (Day 2 revision):**

> "Circle gave agents wallets and Swarms gave them a token-based marketplace. Agent Market gives
> users a curated, verifiable place to hire agents with a passport you can audit — and pay USDC
> per operation without buying anyone's token."

---

## How to read this brief

Each competitor section includes:

- **What they are** — one paragraph
- **Mechanism** — how an agent gets listed, hired, and paid
- **Monetization** — value capture
- **2026 traction signals** — recent numbers with primary-source links
- **What they're missing** — relative to Agent Market's target wedge

A cross-cutting matrix and positioning recommendation follow.

---

## Competitor 1 — Swarms (kyegomez) — the most direct competitor

**What they are.** [Swarms](https://github.com/kyegomez/swarms) is an enterprise-grade
multi-agent orchestration framework with a live marketplace at
[swarms.world](https://swarms.world/). The
[Swarms Marketplace](https://medium.com/@kyeg/the-swarm-marketplace-ai-agents-for-hire-1015d3c92d87)
explicitly markets itself as "AI Agents for Hire." Founded and maintained by Kye Gomez; the
GitHub repo has [~6.7K stars and 911 forks](https://github.com/kyegomez/swarms).

**Mechanism.** Developers build agents with the Swarms framework (or list standalone prompts and
tools), publish to swarms.world, and earn when other users hire/buy them. The marketplace supports
"prompts, agents, and tools" as listable item categories. As of
[June 2025](https://medium.com/@kyeg/swarms-marketplace-payments-are-live-monetize-your-agents-prompts-and-tools-a50b93a7720a),
marketplace payments are live.

**Monetization.** Dual: the native `$swarms` token serves as the primary marketplace currency
(buying, selling, subscriptions, auctions), AND
[x402 integration](https://medium.com/@kyeg/how-to-monetize-your-agents-with-swarms-and-x402-a-simple-step-by-step-tutorial-e56bacc2daf2)
lets developers monetize per-API-call in stablecoins. Swarms supports MCP natively.

**2026 traction.** ~6.7K GitHub stars; live marketplace with payments; active Medium presence
documenting feature launches. The platform spans framework, marketplace, and payment layer in
a single ecosystem.

**What they're missing relative to Agent Market.**

- **UX simplicity for non-crypto users.** Swarms is developer-and-crypto-native; the marketplace
  layer is wrapped in the `$swarms` token economy.
- **Curation.** Swarms.world is open-listing; anyone can publish. Quality varies enormously, and
  the marketplace doesn't gate on demonstrated quality.
- **Verifiable per-job history.** Reputation appears to be based on listing metadata and ratings
  rather than per-job content-hashed traces.
- **A non-token settlement path.** Although x402 is supported, the primary marketplace economy
  is `$swarms`-token-mediated, which doesn't appeal to users who want to just pay $10 and get a
  job done.

**Honest read for our positioning.** Swarms is the most threatening direct comp. They have
shipped what we're proposing. Our wedge against them is **curation + pure-stablecoin pricing +
verifiable passport** — opinionated quality, simpler UX, no token to learn. If our demo is just
"a marketplace where you pay USDC for agent work," they will be the comparison every judge makes,
and we will lose on shipped-product maturity.

---

## Competitor 2 — Circle Agent Stack (the sponsor)

**What they are.** [Circle Agent Stack](https://www.stocktitan.net/news/CRCL/circle-launches-ai-infrastructure-to-power-the-agentic-3j0lw9rke3ev.html)
is Circle's first-party suite of agent-economy primitives, launched May 11, 2026. Components:
**Circle CLI**, **Agent Wallets**, **Agent Marketplace**, and **Nanopayments powered by
[Circle Gateway](https://www.arc.network/)**. Sits on top of
[Arc](https://www.arc.network/), Circle's stablecoin-native L1 (public testnet, no mainnet date
announced yet).

**Mechanism.** Developers register agents through Circle CLI; agents get programmable wallets;
the marketplace component lets agents discover and pay each other. Nanopayments allow transfers
down to $0.000001 — true micropayments for high-frequency agent operations.

**Monetization.** Circle's platform economics — USDC issuance fees, Arc settlement fees, Gateway
infrastructure fees. The
[$222M ARC token presale at $3B FDV](https://decrypt.co/367490/circle-ai-agents-usdc-stablecoin-powers-222m-arc-token-sale)
indicates how seriously Circle takes the agent-economy thesis.

**2026 traction.** Launched same week as the hackathon. Reported partnerships including Kyriba
for [enterprise treasury USDC capabilities](https://www.circle.com/pressroom/kyriba-and-circle-bring-usdc-capabilities-to-enterprise-treasury-unlocking-a-path-toward-more-intelligent-treasury-decisioning).
$77B USDC in circulation as of Q1 2026 (28% YoY growth) per
[Circle's earnings call](https://www.tickerreport.com/banking-finance/13436902/circle-internet-group-q1-earnings-call-highlights.html).

**What they're missing.** Circle's marketplace is infrastructure-first; it appears to target
agent-to-agent commerce (machine-to-machine), not the human-hires-an-agent-for-a-job consumer
UX. The actual product surface for end-user discovery, comparison, and trust is open. Circle is
also unlikely to make opinionated curation decisions — they're a neutral infrastructure provider.

**Honest read for our positioning.** Circle is **infrastructure**; Agent Market should be
**experience**. We consume their Wallets, Nanopayments, and Gateway. We compete with their
Marketplace component on UX, curation, and human-facing trust signals — places where Circle's
neutral-infrastructure posture limits them. The framing in the pitch: "Circle gave agents
wallets; we give users a marketplace they can trust."

---

## Competitor 3 — Olas (Autonolas) Pearl

**What they are.** [Olas](https://olas.network/) operates Pearl, an "AI Agent App Store" for
consumer-runnable autonomous services. Originally launched as a staking-based protocol, Pearl
has evolved significantly — most importantly,
[Pearl v1 integrated x402](https://x.com/autonolas/status/1837325890579222712), enabling agents
to pay for off-chain services in stablecoins.

**Mechanism.** Developers publish services to the Olas registry as Docker-image manifests; users
download Pearl ([Mac + Windows](https://olas.network/blog/the-3-step-guide-to-start-running-agents-with-pearl))
and stake OLAS to run agents on their own machine, earning rewards as the agent meets its
work targets. With x402 integration, those agents can now pay external service APIs in USDC
on a per-call basis.

**Monetization.** OLAS token emissions to operators; protocol fees implicit in tokenomics; x402
enables per-call API monetization for service providers (a separate revenue layer outside the
OLAS economy).

**2026 traction.** [$13.8M raised in Feb 2025](https://www.theblock.co/post/338713/olas-raises-13-8-million-to-launch-pearl-an-app-store-for-autonomous-ai-agents-in-crypto)
to launch Pearl. **700,000+ transactions/month, growing ~30% MoM**; 3.5M total transactions
across 9 chains, with 2M of those being agent-to-agent. Olas agents power 75%+ of Safe
transactions on Gnosis on some days, driven heavily by prediction-market trading.

**What they're missing.**

- **Consumer simplicity.** Pearl still requires users to stake the OLAS token to run agents.
  Hiring an agent for a single job, paying USDC, and walking away is not the design center.
- **Curation.** Pearl's app-store framing implies broad-listing rather than curated quality.

**Honest read for our positioning.** Olas is operationally further ahead than the Day-1 brief
gave them credit for. The 700K tx/month + 30% MoM growth + x402 integration means they are
**not just "staking-based" anymore**. They are a legitimate adjacent competitor for any vertical
that benefits from "always-on" autonomous service framing. We're different because **we're
hire-for-a-job, they're stake-and-run-the-service** — but the difference is narrower than
described in the Day-1 draft and judges may treat them as a near-comp.

---

## Competitor 4 — Virtuals Protocol

**What they are.** [Virtuals Protocol](https://www.virtuals.io/) is an AI agent launchpad
where each agent is represented by an ERC-20 token paired with VIRTUAL in locked liquidity pools.
Built initially on Base; expanded to [Ethereum, Solana, and Ronin](https://www.coingecko.com/en/coins/virtual-protocol).

**Mechanism.** A developer launches an agent and an associated bonding-curve-priced ERC-20
token mints. Holders earn share of agent revenue. Users don't "hire" agents — they own them.

**Monetization.** Protocol fees on bonding-curve transactions and token-launch events.

**2026 traction.** **18,000+ agents listed**;
[$470M+ aGDP (Agentic GDP)](https://coinmarketcap.com/cmc-ai/virtual-protocol/latest-updates/);
$578M market cap as of recent CMC snapshot (down from a ~$5B peak in early 2025). In
[February 2026 launched Virtuals Revenue Network](https://www.prnewswire.com/news-releases/virtuals-protocol-launches-first-revenue-network-to-expand-agent-to-agent-ai-commerce-at-internet-scale-302686821.html)
for agent-to-agent commerce.

**What they're missing.** Per-operation hire flow in stablecoins. Their model is investment-
shaped: buy the token, hold for upside. Discrete-job hiring with USDC is absent.

**Honest read for our positioning.** Virtuals is the loudest competitor by mindshare. Many
judges and crypto-native commentators will frame "agent marketplace" through Virtuals' lens. We
need a sharp one-liner: **"Virtuals lets you bet on an agent; Agent Market lets you hire one."**
Different fundamental relationship to the agent. Our unit economics depend on the agent doing
useful work; theirs depend on speculation that someone will want exposure to the agent's future.

---

## Competitor 5 — Theoriq

**What they are.** [Theoriq](https://www.theoriq.ai/) is a decentralized protocol coordinating
"AI agent collectives" for DeFi-native automation (liquidity provision, yield optimization,
treasury management). Their distinguishing feature is **on-chain attestation of agent reasoning**
via "Proof of Collaboration" and "Proof of Contribution" — verifiable encrypted certificates
attesting to what agents did.

**Mechanism.** Agents register with typed interfaces, can be composed into Collectives, and
produce attested outputs. The
[OpenLedger partnership announced Jan 2026](https://www.prnewswire.com/news-releases/openledger-partners-with-theoriq-to-bring-verifiable-ai-agents-into-live-defi-markets-302664498.html)
brings these attestations onchain for live DeFi markets.

**Monetization.** Native THQ token.

**What they're missing.** Consumer simplicity (their "modular agent collectives" framing is
developer-attractive but user-confusing). Stablecoin per-op pricing. Pure-hire flow.

**Honest read for our positioning.** **Theoriq is the closest competitor on the verifiable-trace
axis** — they have shipped what we are proposing to build (the agent passport). The difference:
their attestations live inside their protocol's typed-interface abstraction with the THQ token;
ours would live in content-hashed reasoning traces anchored to standard infrastructure and paid
in USDC. **If they ship a consumer-facing surface before we do, the verifiable-trace differentiation
disappears.** Worth tracking.

---

## Competitor 6 — Fetch.ai / ASI Alliance

**What they are.** Fetch.ai is one of the originals; merged with SingularityNET and Ocean into
the ASI (Artificial Superintelligence) alliance in late 2024. Historical product
DeltaV has been in transition since the merger.

**Mechanism.** Agent registration, discovery via search/dispatch, transactions in native FET (now
ASI) token.

**2026 traction.** Strategic uncertainty post-merger. Consumer-marketplace traction has been
modest historically.

**What they're missing.** Stablecoin pricing. Consumer-facing hire flow. Recent breakout
traction.

**Honest read for our positioning.** Fetch's five-year history is instructive: **the
"agent-priced-in-native-token" pattern has not broken out to mainstream users in half a decade**.
That observation supports our "USDC instead of native token" wedge. We can cite Fetch as evidence
that the token-pricing-marketplace approach has a ceiling for consumer adoption.

---

## Competitor 7 — ai16z / ElizaOS

**What they are.** [Eliza](https://github.com/elizaOS/eliza) is a popular open-source agent
framework (TypeScript) maintained by the ai16z DAO. The `ai16z` token is the DAO governance and
treasury token; **there is no canonical first-party marketplace product yet**, though ecosystem
projects build marketplace-like features on top.

**Mechanism.** Build agents with Eliza framework; deploy where you want (X, Discord, custom).
The DAO invests in agent projects; the token represents portfolio exposure.

**Monetization.** Token + DAO treasury, not transactional.

**What they're missing.** A first-party marketplace. Stablecoin per-op pricing.

**Honest read for our positioning.** **Eliza is potentially a partner, not a competitor.** Agents
listed on Agent Market could be built using Eliza. Our wedge isn't against the framework layer;
it's against the marketplace layer. Pitch position: "AutoGen, LangGraph, Eliza, Swarms — pick
your framework. Agent Market is where you bring the agent and start earning USDC."

---

## Competitor 8 — Bittensor

**What they are.** [Bittensor](https://bittensor.com/) is a decentralized AI network organized
into "subnets," each producing specialized AI outputs (image gen, text gen, prediction markets,
etc.). Miners and validators earn TAO based on output quality.

**Mechanism.** Operators run miners; validators score them; TAO emits to performers. Subnet
owners design incentive functions.

**Monetization.** TAO emissions, subnet inference fees.

**What they're missing.** Consumer-facing marketplace. Stablecoin pricing.

**Honest read for our positioning.** Bittensor is **upstream infrastructure**, not a competitor.
Some Agent Market agents in v2 could plausibly be backed by Bittensor subnets. The right framing:
"Bittensor is to AI inference what AWS is to compute; Agent Market is to AI agents what Fiverr
is to freelancers." Adjacent layer, not the same layer.

---

## Competitor 9 — MyShell

**What they are.** [MyShell](https://myshell.ai/) is a consumer-facing AI agent app store
primarily focused on entertainment, voice, and chat use cases. Token-gated access; each agent
can have its own token.

**Mechanism.** Developers publish; users buy `$SHELL` or per-agent tokens for usage rights and
revenue share.

**Monetization.** Token economy + app-store fees.

**What they're missing.** Financial/utility verticals (their lane is entertainment). Stablecoin
pricing. B2B hire-for-a-job flow.

**Honest read for our positioning.** Different vertical, different audience. Useful only as a
comparison if a judge brings them up; not a direct comp.

---

## Honorable mentions (frameworks and adjacent, not marketplaces)

- **[AutoGen](https://github.com/microsoft/autogen)** — Microsoft's multi-agent framework; now
  largely in maintenance mode with active development moved to
  [Microsoft Agent Framework](https://github.com/microsoft/agent-framework). Framework layer.
- **[LangGraph](https://github.com/langchain-ai/langgraph)** — LangChain's agent-orchestration
  framework. Framework layer.
- **[CrewAI](https://github.com/joaomdmoura/crewAI)** — popular multi-agent framework. Framework
  layer.
- **[Letta (formerly MemGPT)](https://github.com/letta-ai/letta)** — long-running agent runtime
  with persistent memory. Infrastructure layer.
- **Anthropic Claude / OpenAI agent products** — first-party hosted agents from foundation-model
  providers. Bound to their models, not framework-agnostic. Different category.

These are not marketplaces; they're the upstream framework and runtime layer. **If our pitch
positions us as framework-agnostic + MCP-native, we should mention them by name to demonstrate
we understand the landscape.**

## Non-competitors that share a name (avoid confusion)

- **[Unanimous AI Swarm](https://unanimous.ai/swarm/)** — a human-collaboration platform that
  uses "swarm intelligence" to facilitate group decisions. **Not** an agent marketplace; the
  name overlap with Kye Gomez's Swarms is coincidental.
- **[swarm-ai.org / ResearchSwarmAI](https://www.swarm-ai.org/)** — open-source academic AI
  safety research framework studying emergent risks in multi-agent systems. Reference
  implementation of [Soft-Label Governance for Distributional Safety in Multi-Agent Systems
  (Aiersilan & Savitt, 2026)](https://arxiv.org/abs/2604.19752). MIT-licensed safety research,
  **not** a commercial marketplace. Useful as a reference if we want to talk credibly about
  multi-agent safety risks in the deck.

---

## Cross-cutting positioning matrix

| Competitor          | Pricing model                       | Settlement asset     | Reputation primitive                    | Primary audience          |
| ------------------- | ----------------------------------- | -------------------- | --------------------------------------- | ------------------------- |
| Swarms              | Pay-per-use (x402) + token-mediated | `$swarms` + USDC     | Open listings, ratings                  | Crypto + AI developers    |
| Circle Agent Stack  | Per-operation (nanopayments)        | USDC                 | (No first-party reputation primitive)   | Agent developers (a2a)    |
| Olas Pearl          | Staking-based; x402 for service pay | OLAS + USDC (x402)   | Stake-weighted                          | Operators, prediction nerds |
| Virtuals            | Token ownership                     | VIRTUAL + agent ERC-20 | Token price (proxy)                   | Crypto speculators        |
| Theoriq             | Per-transaction                     | THQ                  | Proof of Collaboration + Contribution   | DeFi developers           |
| Fetch / ASI         | Per-transaction                     | FET / ASI            | Self-reported                           | Developers (legacy)       |
| ai16z / Eliza       | Token treasury                      | ai16z token          | (Framework, not market)                 | Builders                  |
| Bittensor           | Validator emission                  | TAO                  | Validator scoring                       | Researchers, operators    |
| MyShell             | Token-gated                         | $SHELL + per-agent   | Usage-weighted                          | Consumer (entertainment)  |
| **Agent Market (proposed)** | **Pay-per-operation**       | **USDC on Arc**      | **Verifiable history (agent passport)** | **People with a job to do** |

The bottom row is the differentiation story. The wedge that survives the new findings:
**curated marketplace + pure-USDC pricing (no token to learn) + verifiable on-chain-anchored
reasoning trace**. Each of the three is genuinely missing in at least one major competitor; the
combination is missing in all of them.

---

## Where Agent Market wedges (revised, post-research)

1. **Curated, not open-listing.** Swarms.world is open and quality varies; Virtuals and Olas are
   technically open with token-gated quality signals. Agent Market positions as **opinionated
   curation** — we vet agents before listing for the v1 demo, and only let through ones that
   have demonstrated quality. This is the simplest differentiation to ship in two weeks because
   we control the curation policy ourselves.

2. **Pure USDC pricing, no token to learn.** Swarms uses `$swarms`; Virtuals uses VIRTUAL +
   per-agent tokens; Olas uses OLAS to run agents; MyShell uses `$SHELL`. Every meaningful
   marketplace except possibly Circle's first-party one ties value capture to a native token.
   The simple consumer pitch: **"You don't need to buy any token. Just USDC."** This wedge
   depends on us not launching a token of our own.

3. **Verifiable reasoning trace as agent passport.** Theoriq has shipped attestations but inside
   their THQ-token DeFi-focused stack. Swarms ratings are self-reported metadata. Virtuals
   reputation is token-price proxy. **A content-hashed reasoning trace, anchored to Arc storage,
   tied to each completed job, queryable by future buyers** is genuinely missing in the field
   among consumer-facing products. If we ship this primitive in the demo, it's the most
   defensible piece of the pitch.

4. **UX simplicity for non-crypto users.** Every competitor above except Circle assumes the user
   is crypto-native. Agent Market positions for a user who would never buy `$swarms` or VIRTUAL —
   they have a job, they want it done, they pay USDC. This is also the wedge against Circle's
   first-party marketplace: Circle is infrastructure-shaped, not experience-shaped.

---

## Risks the landscape implies

- **Circle's Agent Marketplace is the existential question.** If Circle's marketplace
  component ships strong consumer UX in the next 60–90 days, we are competing with the
  infrastructure provider on their own rails. Pitch positioning needs to acknowledge this
  directly — being asleep on it would read as un-serious to these judges.
- **Swarms has shipped what we propose.** They're crypto-native and developer-focused, but
  saying "no one has done this" is now factually wrong. The honest framing: "Swarms shipped a
  developer-and-crypto-native version. Agent Market is the version for users who don't want
  to buy `$swarms` first."
- **Theoriq is the closest on verifiable trace.** If they expose a consumer-facing surface
  before we do, the verifiable-passport differentiation evaporates. The defense is to ship the
  passport visibly in our demo (a "see the trace" UI element, not just a backend table).
- **x402 is rapidly maturing.** v2 [shipped Dec 2025](https://docs.cdp.coinbase.com/x402/welcome)
  with reusable sessions and multi-chain. [Amazon Bedrock](https://news.bitcoin.com/coinbase-gives-amazon-bedrock-agents-wallet-tools-with-usdc-settlement/)
  integrated it May 7, 2026. Olas Pearl integrated it for off-chain payments. **We should plan
  to use x402 directly rather than build our own payment primitive.** Building our own when x402
  exists is the kind of NIH that's pitch-fatal.
- **"USDC pay-per-op" is no longer differentiating on its own.** Multiple players ship it. Our
  pitch cannot rest on it; it needs the curation + passport + UX-simplicity stack on top.

---

## Open data points still worth confirming

- Whether Circle Agent Stack's Marketplace component has a public alpha or just a roadmap
  positioning slide.
- Whether `@x402/mcp` has shipped a stable spec (mentioned as a roadmap item; recent
  [Cryptorefills launch](https://www.wingerdaily.com/2026/05/11/cryptorefills-launches-x402-payments-for-ai-agents-publishes-agentic-commerce-reference/)
  may indicate further-along status). The
  [Coinbase x402 + MCP integration](https://docs.cdp.coinbase.com/x402/welcome) is live in
  Agentcore Gateway.
- Recent Crypto-AI hackathon winners that overlap our thesis.
- Whether Theoriq's verifiable-trace UX is end-user-facing or developer-tool-facing.

A focused 1-2 hour validation pass before pitch day is warranted.

---

## Recommended pitch-deck competitive-landscape slide

```
TODAY'S AGENT MARKETPLACES                       AGENT MARKET'S WEDGE
─────────────────────────────                    ────────────────────
Swarms — buy $swarms, browse open listings       Curated. We vet agents before listing.
Virtuals — buy the agent's ERC-20 for exposure   Hire-shaped, not own-shaped.
Olas Pearl — stake OLAS to run autonomous svcs   Pay USDC per job. No tokens to learn.
MyShell — buy $SHELL, agent-specific tokens      Pure stablecoin pricing.
Theoriq — verifiable DeFi agent attestations     Consumer-facing verifiable passport.
Circle Agent Stack — agent wallets + a2a market  We're the experience layer Circle won't build.
Fetch / ASI — native token, modest traction      Five years of FET-priced marketplaces have
                                                 not broken out. We pick stablecoin from day 1.

→ Speculation, tokens, developer-first             → Consumption, USDC, user-first
```

The slide tells the truth: the category is real, the competition is serious, and we have a
narrow but defensible wedge that depends on shipping a specific architectural primitive (the
verifiable passport) plus an opinionated curation policy plus genuine consumer UX.

---

## Bottom line for the team

The Day-1 draft framed this as a wide-open category with no clear winner. **Day-2 research
revises that materially.** The category has at least one direct comp shipping (Swarms), at
least one infrastructure-provider-as-competitor with massive resources (Circle), at least one
attestation-shipping comp (Theoriq), and a $222M Arc presale that signals serious money
flowing into the agent-economy thesis.

This is not a reason to back off — it's confirmation the thesis is right. But the pitch needs
to be **honest about the landscape and sharp about the wedge**. Three honest claims we can
defend:

1. Curated quality, not open listings
2. Pure-USDC pricing, no token to learn
3. Verifiable on-chain-anchored agent passport

Ship those three and the pitch is credible. Skip any of them and we're a thin reskin of a
shipped product.

---

_Maintainer note: this brief is live as of 2026-05-12 (Day 2). Re-validate before pitch day —
the agent-economy landscape is moving in weeks, not months._
