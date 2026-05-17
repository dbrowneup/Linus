# Pod 1 Meeting Brief — 2026-05-14

> **For:** Dan, ~4 hours before tonight's Pod 1 jam session
> **Format:** 8 builders, peer-to-peer, no facilitator. Each shares for ~10 min, rest is open jam.
> **Goal of this brief:** show up sharp, give a tight 10-minute sharing slot, and find
> the highest-value cross-pollination — specifically with Bob Sheehan (Lighthouse Macro)
> whose pitch overlaps Archimedes' core primitive.

---

## The Lighthouse Macro / Bob Sheehan situation

### What he's building

**Lighthouse Macro** is an institutional macro research shop — Bob is the founder, ex
BofA Private Bank PM, CFA + CMT. Their existing product:

- **3 engines:** Macro Dynamics, Monetary Mechanics, Market Technicals
- **12 diagnostic pillars** across the three engines
- **~2,500 daily-refreshed series** feeding the pillars
- **Explicit invalidation criteria** at every step ("we can be wrong, on the record")

Their hackathon build, in Bob's words: *"reasoning-trace-as-product on Arc, in the
spirit of Trading-R1."* The thesis he's already articulated cleanly:

> *"The framework is the product. The output sits downstream. Every macro shop has a
> number. What's rare is connecting the inputs to the number with math that's auditable
> and individually wrong-able at every step. That trace is what Trading-R1 says is
> actually worth pricing. Hash it, pin to Arc, build the market on which reasoning
> patterns hold up out of sample."*

He is **explicitly open on the primitive shape**: "IPFS or Irys pinning for the trace,
hash on Arc as the anchor, then what the actual market looks like on top. Open to input
from anyone further down the reasoning-trace or prediction-market verticals."

### Why this matters for Archimedes

Bob has independently arrived at the **same architectural primitive Archimedes is
building.** Two builders in the same pod converging on "auditable reasoning trace,
hashed, anchored on Arc" is not a coincidence — it's a signal that the primitive is
real, and that we should be talking to him for at least three reasons:

1. **External validation of the thesis.** When Bob — institutional credentials,
   independent vector, different vertical — converges on the same primitive, that's
   evidence the wedge is right. Useful for the deck Q&A ("are you sure this matters?").
2. **Possible reasoning-trace-as-substrate alignment.** Archimedes' `ReasoningTraceRegistry`
   is generic — it anchors *any* canonical-JSON-hashed reasoning trace, not just
   portfolio decisions. Macro views are a structurally identical payload: claim →
   inputs → invalidation criteria → hash. If we agreed on a passport schema, LHM macro
   views could be Tier-2 contributions to the same registry.
3. **Cross-pollination on the open question Bob has.** He explicitly asked: "IPFS or
   Irys pinning for the trace?" The Archimedes commit-reveal spec (`commit-reveal-trace-spec.md`)
   has already worked through this corner. We can share what we've decided and why; he
   may have institutional-grade thinking on the prediction-market layer we haven't
   touched.

### What he's *not*

A competitor. Different vertical (macro views, not portfolio construction), different
audience (institutional investors / policymakers, not retail USDC holders), different
business model (research subscriptions vs. take-rate on USDC settlement). The overlap
is in the underlying primitive, not the product.

---

## What to share in the 10-minute slot

Order the slot from concrete-to-abstract so the open-jam question lands hot.

### 1. The team + the build (90 sec)

> *"Archimedes is a 5-person team across 5 timezones. We're building an autonomous
> portfolio agent that grounds investment strategies in peer-reviewed quant research,
> settled in USDC on Arc. As of today, Day 4, we have a live deploy at 18.171.230.205,
> 10 contracts on Arc testnet, multi-wallet UX, and three paper-grounded strategies
> seeded in our backtest engine."*

Punch-line: shipped fast, shipped real, not vapor.

### 2. The wedge (2 min)

> *"Three things make Archimedes different from the 96 other AI-portfolio submissions
> at the last Arc HackMoney:*
>
> 1. *Every strategy carries a passport — paper citation, methodology hash, our
>    re-implementation's Sharpe vs. the paper's claimed Sharpe with the delta surfaced
>    honestly.*
> 2. *Every Tier-1 strategy passes a selection-bias gate at admission — Deflated Sharpe,
>    Probability of Backtest Overfitting, walk-forward out-of-sample, look-ahead audit.*
> 3. *Every agent decision produces a reasoning trace that gets hashed and anchored on
>    Arc — via our deployed ReasoningTraceRegistry contract. The v1.5 commit-reveal
>    upgrade in spec promotes 'trace existed at T' to 'trace existed before the trade.'*
>
> *The wedge isn't 'AI does portfolios.' The wedge is 'every claim the agent makes is
> wrong-able on the record.'"*

### 3. The bridge to Bob (90 sec)

> *"Bob — your pitch lit me up. Your 12 diagnostic pillars across 3 engines with
> invalidation criteria at every step is structurally the same primitive we're
> building, applied to macro instead of portfolios. The framework-as-product framing is
> exactly right. We've been calling it the strategy passport on our side; you're
> calling it the reasoning trace on yours; they're the same thing.*
>
> *I'd love to compare notes on three open questions:*
>
> 1. *Storage layer — we've been leaning toward off-chain JSON with on-chain hash
>    anchors. You mentioned IPFS or Irys. What's your prior?*
> 2. *Commit-reveal binding — we have a spec for temporal binding ('trace existed
>    before the trade'). Is there a macro-views analog for 'view existed before the
>    macro event'?*
> 3. *Schema convergence — if we agreed on the passport shape, your macro views could
>    anchor on the same registry as our portfolio decisions. The primitive is
>    cross-domain. That might be more interesting than either of us shipping a parallel
>    registry."*

### 4. What we're stuck on / want input on (90 sec — open the jam)

Pick one of these depending on who's in the room:

- **Traction.** The 30% Traction rubric weight is unusual. We're trying to get
  arc-canteen telemetry firing density up. Curious how the rest of the pod is thinking
  about this — are people drawing real users in, or is it mostly Day-4 prep?
- **Reasoning-trace consumers.** Who actually *reads* the trace? In the institutional
  macro case (Bob's domain), policymakers and PMs read it. In our case, retail USDC
  holders are unlikely to read each trace — but a verification layer (auditors,
  curators, watchdog services) might. Is there a market structure for "trace auditors"
  on Arc that we haven't thought through?
- **Cross-domain primitive.** If reasoning-trace-as-product generalizes — portfolio +
  macro + prediction markets + scientific claims — does anyone in the pod see a
  registry shape that could serve all of them, or does each vertical need its own?

The third question is the strongest if Bob is engaged.

---

## What to listen for from others

- **Anyone else in Pod 1 also building reasoning-trace / verifiable-claim infrastructure.**
  Likely candidates given the cohort: prediction-market builders, scientific-claim
  attesters, anyone touching ERC-8004 (onchain agent identity).
- **Anyone with a real user base.** A team with traction is a team you can borrow demand
  from for cross-promotion. If someone is building a wallet front-end, an agent
  marketplace, or a portfolio dashboard — they might be a downstream consumer of
  Archimedes' strategy library.
- **Anyone struggling with Circle SDK integration.** Chuan has solved a lot of this
  already (Wallets, Gateway, USYC). Trading a quick consult for a future cross-promo or
  endorsement is cheap.
- **Anyone on the math side (Önder's space).** Statistics, actuarial, quant. Önder
  doesn't need help, but a peer connection in-pod is valuable for both of them.

---

## Soft moves after the meeting

- **Follow Bob on X (`@LHMacro`).** Read one or two of his "From Foundations to Fault
  Lines" pieces before the meeting if you have 20 minutes — that's the stablecoin /
  Treasury / structural fragility series he mentioned. Shows good faith.
- **Send Bob a 1-paragraph follow-up message** offering to share the commit-reveal-trace
  spec privately if he's interested. (It's public in the repo, but the offer is a soft
  signal of seriousness.)
- **Log the conversation in arc-canteen.** `arc-canteen update-traction` it as
  *"Discussed reasoning-trace registry schema convergence with Bob Sheehan (Lighthouse
  Macro, ex-BofA Private Bank, CFA+CMT) — potential Tier-2 macro-views integration into
  Archimedes' ReasoningTraceRegistry."* Traction telemetry doesn't care if the
  conversation is with a teammate or a stranger; it cares about activity volume.
- **Mention the pod meeting to the Archimedes team in `#standups` afterward.** Two
  sentences max. If Bob and Dan find common ground, it should surface to the team
  alongside everything else.

---

## Things to NOT do

- **Don't pitch hard.** Pod 1 is peer-to-peer, not a sales channel. The 10-minute slot
  is for sharing, not closing.
- **Don't promise a schema-convergence partnership in the room.** That's a real
  technical decision that needs Chuan + Önder in the loop. Express interest, propose a
  follow-up call, don't commit.
- **Don't oversell Day-4 state.** The deck is "shipping fast, with intellectual rigor as
  the wedge." Not "we've solved AI-driven portfolio management." Bob will see through
  oversell faster than most because he's already a senior practitioner.
- **Don't talk about the Galaxy Digital connection unprompted.** Your brother-in-law is
  trusted in-network for crypto sanity-checks; pod is a different relationship surface.
  If someone asks about your crypto network, fine — otherwise let it sit.

---

## TL;DR — one sentence

Tonight's pod meeting is a high-value cross-pollination opportunity with Bob Sheehan
because he's independently converging on Archimedes' core primitive (reasoning trace
anchored on Arc); show up with shipped artifacts, propose schema convergence as a
follow-up topic, and let the conversation breathe.
