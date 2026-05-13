# Anti-Features — What We Are NOT Building

> **Audience:** Agent Market hackathon team
> **Purpose:** Make scope discipline explicit. For every plausible-but-distracting feature
> someone on the team will propose mid-week-2, this doc says NO with a reason. Use it as
> the back-pressure document.
> **Date:** 2026-05-12 (Day 2). Revisit weekly.

## Why this doc exists

Hackathon scope creep is the canonical cause of weak demos. Mid-week-2, someone always
proposes "wouldn't it be cool if we also..." Each proposal sounds reasonable in
isolation. Each consumes time the team doesn't have. The cumulative effect is a demo that
does many things shallowly instead of one thing well.

This doc lists the specific things we are NOT building, with the rationale, so that when
someone proposes them, the answer is already on file. Disagreement is fine and the list can
change, but **change requires deleting an existing line and replacing it, not silently
adding scope.**

## Anti-feature list

### NOT building: third-party agent onboarding for v1

**Why not:** Curated quality is one of the three claims our pitch rests on. Third-party
onboarding requires moderation, abuse prevention, KYC, and an onboarding flow — all of which
are real engineering work and none of which advances the demo. For v1, we curate.

**v2 conversation, not v1.**

### NOT building: a full slashing / dispute resolution mechanic

**Why not:** Slashing requires dispute primitives (who decides what counts as a "failed"
job?), oracle integration (where does the ground truth come from?), and governance for
edge cases. The passport with refund-on-failure is sufficient defense for v1. Adding
slashing adds smart-contract surface, attack surface, and pitch complexity without
unblocking the wedge.

**Per [`custody-and-settlement.md`](custody-and-settlement.md).**

### NOT building: predictive performance scores or aggregated ratings

**Why not:** Verifiable history is the wedge; aggregated scores are the failure mode we're
trying to escape. No `rating_score` on the `agents` table. No leaderboard ranking. The UI
surfaces queryable history; users assess themselves.

**Per [`reputation-and-vertical-selection.md`](reputation-and-vertical-selection.md).**

### NOT building: a native Agent Market token

**Why not:** "No token to learn" is one of the three claims our pitch rests on. The day we
launch a token is the day we collapse into one of the competitors we're differentiating
against. Take-rate on USDC settlement is the revenue model.

### NOT building: a fiat on-ramp

**Why not:** Users need to bring USDC to use the platform. Adding a fiat on-ramp (Stripe,
MoonPay, etc.) means signing up for partnerships, handling KYC, and operating a regulated
flow. None of which is a hackathon project. **v2 conversation.**

### NOT building: cross-chain bridges

**Why not:** Arc only. USDC on Arc only. Bridges add attack surface, complexity, and
narrative confusion. The pitch is "USDC on Arc"; let's not muddle it.

### NOT building: multi-currency support

**Why not:** USDC only. Even EURC (which Circle issues and Arc supports) is out of scope
for v1. Adding it doesn't unlock the wedge and dilutes the pitch.

### NOT building: a public agent SDK

**Why not:** Developers integrate by exposing an MCP server. We don't need to ship a
proprietary "Agent Market SDK" — MCP is the SDK. **v2 conversation if/when we want to
offer convenience wrappers.**

### NOT building: native trading-agent infrastructure

**Why not:** Per the [vertical-selection memo](reputation-and-vertical-selection.md),
trading is the wrong demo vertical. Building trading-agent-specific features (market data
streams, position management, risk constraints) consumes time and pulls focus.

### NOT building: chat-bot agent interfaces

**Why not:** Agents on Agent Market are hired for discrete operations, not for ongoing
conversations. Chat-bot UX is a different product. If a developer wants to list a
conversational agent on Agent Market, that's fine, but the v1 demo doesn't need a chat
UI.

### NOT building: agent-to-agent (a2a) commerce in v1

**Why not:** Circle's Agent Marketplace targets a2a. We target user-hires-agent. Trying to
do both blurs the pitch. v2 can add a2a primitives; v1 stays human-facing.

### NOT building: a mobile app

**Why not:** Web-first. Mobile is a different engineering problem and doesn't unlock new
judging value.

### NOT building: a dispute UI

**Why not:** The platform's signer can refund failed jobs. v1 doesn't need a
"dispute this job" button. v2 conversation when slashing/governance is on the table.

### NOT building: encrypted reasoning traces

**Why not:** v1 traces are public. The hash anchors public content. v2 can add the
encryption pattern (encrypt-trace, share-key-with-buyer) for sensitive use cases. v1
agents that produce sensitive reasoning can simply choose not to list on Agent Market.

### NOT building: KYC / AML for developers or users

**Why not:** v1 is permissionless on both sides. KYC is a regulatory burden we can't
satisfy in two weeks and that conflicts with the "wallet-native" target user.

### NOT building: a referral / affiliate program

**Why not:** Distracting; doesn't advance the demo.

### NOT building: complex pricing tiers

**Why not:** Per-operation USDC pricing. No subscriptions, no usage-tiered discounts, no
volume packages. v1 keeps the pricing model maximally simple to support the "no tokens to
learn" pitch.

### NOT building: a "social" layer (follow agents, share results)

**Why not:** Distracting. Different product. Don't.

### NOT building: agent-output caching / memoization

**Why not:** Each hire is a fresh job. No caching layer that returns cached results
without paying. Smart but not the demo.

### NOT building: a custom agent runtime / sandbox

**Why not:** Agents run in their developer's infrastructure (the developer's MCP server is
called by our runner). We don't host a "Docker sandbox" for arbitrary agent code in v1.

### NOT building: open API for analytics / aggregate data

**Why not:** The passport is per-job. We don't ship a "GET /api/stats" that exposes
aggregate metrics across agents. v2 conversation.

## What we ARE building (for explicit contrast)

To make this doc complete: the full v1 scope is the inverse of the above. Specifically:

- Marketplace UI with 2-3 curated demo agents (one lead vertical + optionally one secondary)
- End-to-end flow: browse → hire → backend job → MCP tools → result → USDC settlement on
  Arc → developer payout + platform fee → passport anchored
- Agent passport: reasoning trace + tool-call provenance + on-chain hash anchor
- "Verify trace" UI element (the wow moment)
- Pitch deck + live demo + Q&A prep
- License (recommend MIT)
- Daily sync + async-first workflows

That's it. That's the whole project. Everything else is v2.

## How to use this doc

When someone in the team proposes a feature mid-week-2:

1. Check this doc. If it's listed as anti-feature, the conversation is short: "we decided
   not to build this; here's why."
2. If it's a NEW feature not listed, ask: "what current scope item does this displace?"
   Hackathons are zero-sum on time; if you add X, you must subtract Y.
3. If the team agrees the proposed feature is more important than something currently in
   scope, edit this doc and the in-scope list to reflect the change. Date the change.

## Open questions

- Should we add a one-liner "the secondary demo agent is in/out" decision here? Currently
  open per [`rfb-selection-memo.md`](rfb-selection-memo.md). If the team decides
  single-track research, the translation-agent line moves to anti-features.
- Should we explicitly list "no token to launch even post-hackathon" as a forward-looking
  commitment? Or leave that for the v2 strategy conversation?
