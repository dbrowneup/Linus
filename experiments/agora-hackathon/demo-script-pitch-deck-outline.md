# Demo Script & Pitch Deck Outline

> **Audience:** Agent Market hackathon team (especially the eventual demo presenter and
> deck owner)
> **Status:** Working outline — to be tightened in week 2 once the build has converged.
> **Pitch length assumption:** 3-minute pitch + live demo + Q&A. Adjust if Canteen tells us
> otherwise.

## The headline message

> **"Most agent marketplaces let you bet on agents. Agent Market lets you hire them — and
> shows you exactly what they did."**

That's the one-line. Everything else in the deck supports it.

## The "wow moment" the demo must hit

A user, in front of judges, hires an agent on Agent Market. The agent runs. Judges watch:

1. The user picks an agent from the catalog.
2. The user clicks "Hire" and enters a research prompt.
3. The user's USDC moves into an Arc-native escrow contract live on testnet (judges can
   click the tx hash and see it on the explorer).
4. The agent runs, calling MCP tools (a small UI element shows tool calls happening in
   real time).
5. The agent delivers its result.
6. Settlement happens — USDC flows to the developer and the platform fee address in one
   transaction.
7. **The "Audit Passport" button appears.** User clicks it. The reasoning trace appears
   alongside the tool calls; a "Verify trace hash" button recomputes the hash in the
   browser and shows a green checkmark — proving the trace matches the on-chain anchor.

**Step 7 is the differentiator.** Without it, we're showing the same demo every other team
shows. With it, judges see verifiable history operating live.

## Pitch deck — 8-slide structure

### Slide 1: title + tagline

**Title:** Agent Market

**Tagline:** *Hire AI agents per operation. Pay USDC on Arc. Audit a verifiable passport
of everything they did.*

**Background:** team photo or single illustrative image. Date and Arc/Circle Hackathon
attribution.

### Slide 2: the problem (30 seconds, one slide)

The agent economy is real but the marketplaces today force users into one of two roles:

- **Speculator.** Buy the agent's token (Virtuals, MyShell). Hope it goes up.
- **Operator.** Stake the protocol's token to run the agent yourself (Olas, Bittensor).

**There's no good way to just hire an agent, pay for the work, and know what you got.**

Visual: three-column comparison — Speculator | Operator | (empty third column where "Buyer"
should be).

### Slide 3: what we built (60 seconds, the meat)

Agent Market — a curated marketplace where:

- **Users hire agents** for one operation at a time. No tokens to learn. Pay USDC.
- **Developers list agents** built with any framework (Eliza, Swarms, AutoGen, custom).
  MCP-native.
- **Every job produces a verifiable passport** — reasoning trace + tool calls + on-chain
  anchor on Arc.
- **Reputation is verifiable history.** Browse any agent's prior jobs; click any one; read
  the trace.

Visual: the architecture diagram from `HACKATHON-CLAUDE.md`, with the passport flow
highlighted.

### Slide 4: live demo (90 seconds)

This slide is just "DEMO" in large text. The demo runs from the deployed instance at
`hackathon.navontech.dev`. Hit the wow moment described above.

### Slide 5: competitive landscape (30 seconds)

The competitive slide from `competitor-landscape.md`:

```
TODAY'S AGENT MARKETPLACES                   AGENT MARKET'S WEDGE
─────────────────────────────                ────────────────────
Swarms — open listings, $swarms token        Curated. Vet agents before listing.
Virtuals — buy the agent's ERC-20            Hire-shaped, not own-shaped.
Olas Pearl — stake OLAS to run agents        Pay USDC per job. No token to learn.
MyShell — buy $SHELL, per-agent tokens       Pure stablecoin pricing.
Theoriq — verifiable DeFi attestations       Consumer-facing verifiable passport.
Circle Agent Stack — wallets + a2a market    We're the experience layer Circle won't build.

→ Speculation, tokens, developer-first         → Consumption, USDC, user-first
```

Acknowledging Circle directly is a power move — judges from Circle will respect it.

### Slide 6: why now (30 seconds)

Three signals that say "this market is real, today":

- [Circle launched Agent Stack May 11, 2026](https://decrypt.co/367490/circle-ai-agents-usdc-stablecoin-powers-222m-arc-token-sale)
  — $222M Arc presale, BlackRock among investors.
- [Olas Pearl is doing 700K transactions/month, 30% MoM growth.](https://www.theblock.co/post/338713/olas-raises-13-8-million-to-launch-pearl-an-app-store-for-autonomous-ai-agents-in-crypto)
- [Virtuals Protocol has 18,000+ agents and $470M Agentic GDP.](https://coinmarketcap.com/cmc-ai/virtual-protocol/latest-updates/)

The category is happening. The unanswered question is: **who builds the experience layer
for users, not speculators or operators?** Agent Market.

### Slide 7: what we ship next (30 seconds)

After the hackathon:

- Onboard third-party agent developers.
- Expand demo verticals: trading (with Chuan's CoinShares expertise),
  prediction-market translation (Canteen RFB iv), compliance verification.
- Open-source the passport schema as a standard others can adopt.
- v2: slashing for the agents that consistently produce bad jobs, dispute resolution.

Visual: a vertical-list "now / 30 days / 90 days" roadmap.

### Slide 8: team + ask (30 seconds)

Team photos and one-line credentials. Ask depends on what we want from judges — be honest:

- "We're not asking for funding today. We're asking for: (a) listing partnerships with
  agent developers, (b) feedback on the passport schema, (c) introductions to teams building
  agents who want a marketplace surface."

The "asking for nothing" ask is often the strongest — judges respect a team that's just
shipping.

## Q&A preparation — anticipated judge questions

**Q: How is this different from Swarms?**

A: Swarms is a developer-and-crypto-native marketplace; everything is mediated by their
`$swarms` token. Agent Market is for users who would never buy a token but want to hire
an agent. Pure USDC. Curated quality. Verifiable passport.

**Q: How is this different from Circle's Agent Marketplace?**

A: Circle is infrastructure; Agent Market is experience. Circle provides wallets,
nanopayments, and a permissionless protocol for agent-to-agent commerce. We provide a
curated, opinionated marketplace where users can trust the listings. We consume Circle's
infrastructure — we don't compete with it.

**Q: Why aren't your demo agents trading agents? Trading is where the money is.**

A: Trading is where the most regulatory exposure is, where reputation gaming is hardest,
and where every other hackathon team is going. We chose research because the wedge — the
verifiable passport — is most clearly defensible there. Trading agents will live on the
platform; they're just not in the lead demo because their reputation system is structurally
harder to defend in two weeks.

**Q: What's your moat against Circle eventually building a curated marketplace themselves?**

A: Circle is structurally neutral infrastructure. Curation requires opinions. We bet they
won't ship strong curation themselves because it conflicts with their permissionless ethos.
If they do, the moat is execution speed and community trust — places where a focused team
outcompetes a big company.

**Q: Why USDC and not your own token?**

A: Tokens add friction and speculation; USDC removes both. We're optimizing for users who
want a job done, not for tokenholders. The platform's revenue comes from take-rate on USDC
settlement.

**Q: How does the passport prevent bad agents from gaming the system?**

A: It doesn't aggregate. There's no number to game. The passport is queryable history; if
an agent has 100 great jobs and 5 terrible ones, future buyers see all 105. They decide.
Bad agents can't hide failures; good agents can't fake successes.

**Q: What's your business model?**

A: Take-rate on USDC settlement. 5% in v1, governance-changeable later. We don't earn from
token speculation; we earn when agents do real work users pay for.

**Q: How do you onboard non-crypto users? Do they need a wallet?**

A: v1 requires a wallet (we're crypto-native by hackathon definition). v2 can layer on
fiat on-ramps or smart-account abstractions for users who don't want to manage keys. The
escrow contract architecture is compatible with either path.

**Q: What happens if a job fails?**

A: The escrow contract has a refund path. The platform's signer can call `refund(jobId)`
to return the user's USDC if the job didn't complete. v2: dispute resolution for
partial-completion cases.

**Q: How big is the addressable market?**

A: Total agent-economy value capture is in the early innings. Virtuals' Agentic GDP at
$470M is one data point. Olas's 700K tx/month is another. The agent economy is real and
growing 30%+ MoM in the closest comp; we don't need to forecast precisely to know it's
material.

## The pitch's posture

A few notes on how to deliver:

- **Don't apologize.** The team is solid and the build is real. No "we're just a hackathon
  team" framing.
- **Don't oversell.** Show what we built; don't claim what we didn't.
- **Acknowledge competitors by name.** Demonstrates we understand the landscape.
- **Don't say "no competition."** This was wrong on Day 1; correcting it openly in the
  pitch is part of credibility.
- **Use the team's credentials sparingly but precisely.** Chuan at CoinShares + Gyld
  Finance is a real anchor; Dan's scientist background + LanzaTech is a real anchor;
  Marten's HPC/ML academic chops add depth. Don't oversell; one or two sentences each.

## Logistics for the demo day

- **Run the demo on a dedicated wallet** that has no real-value assets, only testnet USDC.
- **Have a backup video recording** of the demo flow, in case live infrastructure has a
  bad moment. Don't lean on it; it's an insurance policy.
- **Test the live demo at the same time of day** as the actual judging — network latency
  and infrastructure load matter.
- **The Q&A is where the deck's preparation pays off.** Rehearse the anticipated
  questions out loud, ideally with the team.

## Owner: who drives this?

Recommend:

- **Pitch deck owner:** one person — likely Marten (coordinator) or Dan (Product Owner
  background). Owns slide content; integrates input from team.
- **Demo runner:** Shimon (he built the infra; he knows the system). Plays
  the user role in the live demo.
- **Q&A primary:** rotating across topical experts:
  - **Dan** for architecture, agent passport, and vision.
  - **Chuan** for custody, on-chain, Arc, and RWA-context framing (his ex-CoinShares +
    Gyld Finance + RWA tokenization credibility lets him handle the "what about
    institutional/regulated rails" line of questioning crisply).
  - **Önder** for math/statistics questions (Kelly Criterion, +EV decision-making, the
    statistical-rigor backing the reputation primitives — he's an ASA Statistical Insight
    World Champion, so this is a clean credibility marker).
  - The **demo runner** (Shimon) for live system questions.

Lock these roles by end of week 1 so week 2 is rehearsal, not negotiation.
