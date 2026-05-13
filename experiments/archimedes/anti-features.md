# Anti-Features — What Archimedes Is NOT Building

> **Audience:** Archimedes hackathon team
> **Purpose:** Make scope discipline explicit. For every plausible-but-distracting feature
> someone proposes mid-week-2, this doc says NO with a reason. Use it as the back-pressure
> document.
> **Date:** 2026-05-12 (Day 2). Revisit weekly.

## Why this doc exists

Hackathon scope creep is the canonical cause of weak demos. Mid-week-2, someone always
proposes "wouldn't it be cool if we also..." Each proposal sounds reasonable in isolation;
each consumes time the team doesn't have; the cumulative effect is a demo that does many
things shallowly instead of one thing well.

This doc lists the specific things Archimedes is **not** building in v1, with the
rationale. When someone proposes one, the conversation is short: "we decided not to build
this; here's why." Disagreement is fine and the list can change, but **change requires
deleting an existing line and replacing it, not silently adding scope.**

## Anti-feature list

### NOT building: a native Archimedes token

**Why not:** Our pitch's defensibility rests on "pure USDC, no token to learn." The day we
launch a token is the day we collapse into one of the competitors we differentiate
against. Take-rate on USDC settlement + USYC yield-share is the revenue model.

### NOT building: perpetual futures or any leveraged trading

**Why not:** Per [`rfb-alignment.md`](rfb-alignment.md), we skip RFB 01 deliberately. The
v1 portfolio is spot + RWA + USYC. Leverage adds liquidation failure modes, regulatory
exposure, and demo fragility we can't manage in 12 days.

### NOT building: third-party strategy onboarding for v1

**Why not:** Curated v1 library per [`mvp-scope-memo.md`](mvp-scope-memo.md). Third-party
onboarding requires moderation, abuse prevention, methodology review at scale, and an
onboarding flow — none of which advance the v1 demo. The arxiv ingest pipeline runs as a
demo segment on 2–3 papers; it does not productize for v1.

**v2 conversation, not v1.**

### NOT building: a full slashing / dispute resolution mechanic

**Why not:** Slashing requires oracle integration (where does ground truth come from?),
governance for edge cases, and dispute primitives. The strategy passport with verifiable
history + USYC floor + regime-aware deleveraging is sufficient defense for v1. Adding
slashing adds smart-contract surface, attack surface, and pitch complexity without
unblocking the wedge.

### NOT building: tax-loss harvesting

**Why not:** Mentioned in RFB 04 and in Chuan's [`design.md` § 4.3.1](design.md), but
classified as v1.5. Tax-loss harvesting requires accounting infrastructure (cost basis
tracking, wash-sale rules, jurisdiction-specific tax codes) that's a real product on its
own.

**v1.5 if Week 2 has capacity; otherwise v2.**

### NOT building: a fiat on-ramp

**Why not:** Users bring USDC. Adding a fiat on-ramp means signing partnerships (Stripe,
MoonPay, etc.), KYC, and operating a regulated flow. None of which is a hackathon project.

**v2 conversation.**

### NOT building: KYC / AML for users

**Why not:** v1 is permissionless. KYC is a regulatory burden we can't satisfy in two
weeks and that conflicts with the "wallet-native" target user. If the product graduates
beyond the hackathon, KYC becomes a conversation about whether we serve regulated
jurisdictions or remain non-custodial.

### NOT building: multi-currency support beyond USDC

**Why not:** USDC only. Even EURC is deferred unless explicit team decision. Adding it
doesn't unlock the wedge and dilutes the pitch.

**Reconsider for v1.5 if a target user explicitly needs it.**

### NOT building: cross-chain bridges to non-Arc destinations

**Why not:** Arc-native settlement. RWA tokens come from source chains via CCTP/Gateway
to Arc; we don't ship a "send your portfolio to Ethereum mainnet" feature. Bridges add
attack surface and narrative confusion.

### NOT building: a custom agent framework or runtime

**Why not:** Off the shelf. Claude API for LLM, fastmcp (or similar) for tool layer if
MCP-style is needed, Python for orchestration. We don't write our own "Archimedes
framework"; we wire together best-of-class components.

### NOT building: a portfolio simulator / paper-trading mode

**Why not:** v1 ships testnet (real on-chain transactions, but no real value at risk). A
separate "paper trading" mode is unnecessary — testnet IS paper trading with the
benefit of demonstrating real on-chain primitives.

### NOT building: mobile-first UX / a mobile app

**Why not:** Web-first. Mobile is a different engineering problem and doesn't unlock
new judging value.

### NOT building: social features (follow users, share portfolios, comments)

**Why not:** Different product. Strategy-leaderboard (per design.md § 9) gives us
discovery; we don't need social commentary on top.

**v2 conversation.**

### NOT building: a chat-bot / conversational portfolio agent

**Why not:** v1 is form-driven onboarding (pick risk profile) + dashboard for live state.
A conversational interface is a different product and shifts the agent's failure modes
from "did it construct the right portfolio?" to "did it understand the user?" — a
harder evaluation problem.

**v2 conversation.**

### NOT building: agent-to-agent (a2a) commerce

**Why not:** Circle's Agent Marketplace targets a2a. We target a user managing their own
portfolio. Trying to do both blurs the pitch. Could be a v2 surface — "Archimedes agents
can be hired by other agents to manage sub-portfolios."

### NOT building: encrypted reasoning traces

**Why not:** v1 traces are public. The hash anchors public content. v2 can add the
encryption pattern (encrypt-trace, share-key-with-buyer) for use cases where strategy
secrecy matters.

### NOT building: model fine-tuning on our own data

**Why not:** Claude API + careful prompting handles strategy extraction and reasoning
trace generation in v1. Fine-tuning is a v2+ conversation.

### NOT building: an Arc smart contract upgrade pattern

**Why not:** Per [`docs/specs/strategy-passport-spec.md`](specs/strategy-passport-spec.md)
and following Chuan's [`design.md` § 5.2](design.md), contracts are immutable in v1. If a
bug surfaces, we deploy a new contract and migrate. Upgrade patterns add their own bug
surface (the proxy / delegatecall failure mode is non-trivial); we hold the line on
immutability for v1.

### NOT building: real-time portfolio chat with the agent

**Why not:** Reasoning traces are async — the agent decides, hashes, publishes. A
real-time chat interface where the user can interrupt or coach the agent is a different
product (and a harder one — agency vs. interruptibility tradeoffs).

### NOT building: a portfolio NFT or position-tokenization layer

**Why not:** Don't tokenize the user's *position*. Tokenize the *underlying assets* (RWA
tokens) per Chuan's [`design.md` § 5.3](design.md). Adding a layer where the user's
portfolio itself is a tradeable token is a v2+ conversation and adds complexity without
clear v1 benefit.

### NOT building: gamified / "rewards" mechanics

**Why not:** No streaks, no points, no XP for using the platform. v1 is professional;
rewards are a different product class. (Plus, gamification mixed with money management is
ethically dicey territory.)

### NOT building: real-time price feeds via custom oracle infrastructure

**Why not:** Use Chainlink, Pyth, or RedStone for price feeds. Don't roll our own oracle
network. Off-the-shelf where reliable.

## What we ARE building (for explicit contrast)

To make this doc complete: the v1 scope is the inverse of the above. Specifically:

- Portfolio agent that constructs personalized portfolios from a curated library of
  paper-grounded strategies
- Live regime detection + autonomous rebalancing + strategy rotation
- Strategy passport: paper provenance + reasoning trace + tool-call provenance
- On-chain anchoring of reasoning traces via ReasoningTraceRegistry on Arc
- Non-custodial vault: ArchimedesVault holds user USDC, agent has rebalance authority only
- USYC floor per risk profile for risk-off yield
- RWA token acquisition via CCTP/Gateway
- Strategy leaderboard for discovery
- Curated v1 library: 5–10 paper-grounded strategies
- Arxiv ingest pipeline demo on 2–3 papers (not relied on for live demo)
- Web frontend (Next.js) for onboarding + dashboard + reasoning-trace viewer
- Pitch deck + live demo + Q&A prep

That's it. That's the v1. Everything else is v2.

## How to use this doc

When someone in the team proposes a feature mid-week-2:

1. Check this doc. If it's listed as anti-feature, the conversation is short.
2. If it's a NEW feature not listed, ask: "what current scope item does this displace?"
   Hackathons are zero-sum on time; if you add X, you must subtract Y.
3. If the team agrees the proposed feature is more important than something currently in
   scope, edit this doc and the in-scope list to reflect the change. Date the change.

## Open questions

- Should we be explicit that **no native token, ever** is the long-term commitment, or
  is "no v1 token" only a v1 scope decision? Default: **v1 commitment, v2+ revisitable.**
- Should the arxiv pipeline graduate from demo to product in v2? **Yes, that's the
  natural v2 — productize the ingest pipeline as a developer-facing API.**
