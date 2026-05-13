# Current Repo — Red Team Observations

> **Audience:** Agent Market hackathon team
> **Purpose:** Surface the specific gaps, hedges, and architectural smells in the current
> hackathon repo state (as of the
> [README at commit-snapshot 2026-05-11](https://github.com/ShimonNavon/hackathon)), in a
> consolidated doc the team can discuss and respond to. Each item is a real concern, ranked
> by priority.
> **Mode:** intentionally adversarial. The intent is to surface every concrete problem so we
> can decide which to fix and which to accept. Healthy red-teaming makes the project stronger.

## Priority 1 — load-bearing architecture gaps

### 1.1 The agent passport is hand-wavy

**The current state.** The README describes the agent passport as "basic identity, rating,
action history, and price per operation." The planned domain models (`Agent`, `Job`,
`ToolCall`, `Payment`) do not include any `ReasoningTrace` or `AuditLog` entity. Today's
passport is whatever the agent self-reports plus the platform's own log of which tools were
invoked.

**The problem.** Without verifiable reasoning trace + tool-call provenance tied to job_id,
the passport is structurally just a fancier version of self-reported metadata. We compete
with Swarms on this axis and lose, because Swarms is a shipped marketplace with the same
quality of reputation primitive and four years' head start.

**What's needed.** See [`agent-passport-spec.md`](agent-passport-spec.md) for the
table-level spec. Minimum addition: two new tables (`ReasoningTrace`,
`ToolCallProvenance`), content-hashing on entry, and an on-chain anchor for each completed
job.

**Estimated lift.** 1–2 days for backend (one person). Could be done in parallel with
the platform UI work.

### 1.2 "MCP-style" is hedging

**The current state.** The README literally says "MCP-style tool adapters for market data,
news, and wallet lookup."

**The problem.** "MCP-style" is not MCP. It's "whatever adapter pattern the developer
wrote." Real MCP gives Agent Market three properties it cannot get otherwise:

- **Verifiable tool surface.** We can attest "this agent had access to these tools, no
  others" — because MCP's manifest is queryable.
- **Ecosystem compatibility.** Agents built with Anthropic Claude, OpenAI Agents SDK,
  Eliza, Swarms, AutoGen — all of them can speak MCP. "MCP-style" is platform-specific.
- **Pitch story.** "We use the protocol the AI industry is converging on" is a much
  cleaner pitch than "we have our own adapter standard."

**What's needed.** Commit to [`fastmcp`](https://github.com/jlowin/fastmcp) (or equivalent
Python MCP framework) for v1. Scope: one demo agent + 2-3 MCP servers (block explorer,
defillama, news). See [`mcp-integration-decision-memo.md`](mcp-integration-decision-memo.md).

**Estimated lift.** 2-3 days for one person to wire up fastmcp + three MCP servers.

### 1.3 Reputation primitives are missing from the model

**The current state.** Planned models are `Agent`, `Job`, `ToolCall`, `Payment`. There is no
`Review`, `Rating`, `Score`, `Trial`, `Bond`, or `Slashing` entity.

**The problem.** Reputation isn't a feature you add at the end; it's a property of how the
data is shaped from the start. If the schema doesn't carry the structure needed for the
reputation system, it gets bolted on later as ad hoc tables — and that's where data
inconsistencies live.

**The recommendation.** Per
[`reputation-and-vertical-selection.md`](reputation-and-vertical-selection.md), reputation is
queryable history, not aggregate score. We don't need a `Rating` table. We need the passport
tables (covered in 1.1) to be designed well. The "rating" surface is a UI-layer rollup, not
a stored primitive.

**Estimated lift.** Folded into 1.1.

### 1.4 The mocked-USDC-by-demo-day risk

**The current state.** The README says "payments may begin as mocked USDC records. The
architecture is designed so real Arc settlement can be added after the core product flow
works."

**The problem.** The pitch's "wow moment" is the live USDC settlement on Arc in front of
judges. If we go into demo day still mocked, we have lost the most important visual
element of the pitch. "Initially mocked" is a week-1 plan, not a week-2 plan.

**What's needed.** A hard internal deadline of **end of week 1** (Friday May 16) for real
Arc settlement to be working on testnet end-to-end. Chuan owns this per
[`custody-and-settlement.md`](custody-and-settlement.md).

**Estimated lift.** 2-3 days for Chuan once the escrow contract is written and tested.

## Priority 2 — coordination and process risks

### 2.1 License is "to be decided"

**The current state.** The README says "Private hackathon project. License to be decided."

**The problem.** Six contributors (and growing) committing to a repo with no declared license
is a real IP question. We need a license declaration:

- Before any external contributor (beyond the original four) lands a PR.
- Before any code is imported from a Linus-style external source.
- Before the demo, because judges may ask about it.

**Recommendation.** **MIT or Apache-2.0**. MIT is the simpler, more permissive choice
([template](https://choosealicense.com/licenses/mit/)). Apache-2.0 includes patent grant
language some teams prefer. Either is fine; the decision should be made this week.

**Estimated lift.** Hours. Decide, add `LICENSE` file, update `README.md`.

### 2.2 Demo vertical is undecided

**The current state.** The README's three demo agents (News Trader, Whale Watcher, Risk
Checker) are all crypto-finance-focused. The team has not formally committed to a vertical.

**The problem.** Per [`reputation-and-vertical-selection.md`](reputation-and-vertical-selection.md),
trading is the worst vertical for the demo, because reputation gaming is hardest there. The
team needs to commit by end of Day 2 / start of Day 3, because the demo agent build needs
1+ week.

**Recommendation.** **On-chain research as the lead demo vertical.** Trading lives in the
pitch deck as a "next vertical" story, not in the demo build.

**Estimated lift.** Decision is hours; the change in demo agents is days, but those days
were going to be spent anyway.

### 2.3 The bus factor on Solidity is 1 (Chuan)

**The current state.** Chuan owns the smart contract. No other team member has Solidity
experience on the resumes.

**The problem.** If Chuan becomes unavailable, the demo cannot ship. This is a real risk
for a 2-week project.

**Mitigations:**

- **Keep the contract small** (under 100 lines). See
  [`custody-and-settlement.md`](custody-and-settlement.md). A small contract is reviewable
  by a non-Solidity engineer in 30 minutes.
- **Pair-review every line.** One of Shimon, Daniel R, or Önder reads the contract with
  Chuan before deployment. Önder may also bring math-rigor review (the Kelly-Criterion /
  +EV framing he proposed for the agent decision engine generalizes to validating the
  fee-math correctness of the escrow contract).
- **Document the deploy steps** in a `docs/deploy.md` so any team member can ship a hotfix
  if Chuan is unavailable.

**Estimated lift.** Folded into the contract work.

### 2.4 Six strangers, four timezones, two day-jobs

**The current state.** The team is six people spread across UTC-5, UTC-3, UTC+1, UTC+2, and
UTC+3, with three having significant day-role commitments (Dan @ LanzaTech, Daniel R @ MV,
Chuan @ Gyld Finance CTO).

**The problem.** Coordination tax is real. Async-first will be the default; the daily sync
is the synchronization point.

**Mitigations:**

- **Lock the daily sync window.** Per HACKATHON-CLAUDE.md, 13:00 UTC = 8am Chicago / 10am
  São Paulo / 14:00 London / 15:00 Bremen / 16:00 Tel Aviv. Commit and stick to it.
- **Marten as schedule/flow owner.** He's shown coordinator instincts; let's make it
  formal.
- **Async-first writing.** Decisions get documented in commits and PRs; nothing important
  happens only in Discord ephemeral chat.
- **Weekend hour-blocks.** Dan, Daniel R, and Chuan can each block 4-hour weekend windows
  for focused work; coordinate so we have overlap.

## Priority 3 — pitch and storytelling risks

### 3.1 The "no competition" framing is factually wrong

**The current state.** Day-1 discussions referenced a quick Google check finding "no
competition." Day-2 research surfaced
[Swarms shipping a live marketplace](https://swarms.world/), Circle's first-party
[Agent Stack with marketplace component](https://decrypt.co/367490/circle-ai-agents-usdc-stablecoin-powers-222m-arc-token-sale),
[Olas Pearl with x402](https://x.com/autonolas/status/1837325890579222712),
[Theoriq with verifiable attestations](https://www.theoriq.ai/), and
[Virtuals at $578M market cap with 18,000+ agents](https://www.virtuals.io/).

**The problem.** A pitch that claims "no competition" to judges who include Circle
employees will be immediately punctured. We need to acknowledge the landscape and articulate
the wedge explicitly.

**Recommendation.** See [`competitor-landscape.md`](competitor-landscape.md). The
pitch-deck competitive slide draws the contrast cleanly: speculation vs. consumption,
tokens vs. USDC, open-listing vs. curation, opaque vs. verifiable.

### 3.2 The "wow moment" of the demo is undefined

**The current state.** No documented "this is the single thing we demonstrate live."

**The problem.** Hackathons live or die on a single moment of magic. Without committing to
one, week 2 will dissipate into polishing many partial things.

**Recommendation.** See [`demo-script-pitch-deck-outline.md`](demo-script-pitch-deck-outline.md).
The wow moment proposed: a user hires an on-chain research agent, watches the agent work,
the USDC settles on Arc live, the reasoning trace is visible, the platform fee lands in
real-time.

### 3.3 No anti-feature list yet

**The current state.** Nothing is explicitly out-of-scope. Mid-week-2, this leads to scope
creep and a worse demo.

**Recommendation.** See [`anti-features.md`](anti-features.md). Commit to NOT building a
list of plausible-but-distracting features.

## Priority 4 — minor / cosmetic

- **README has duplicate "Built for" phrasings** that could be tightened.
- **Tech stack table** lists "Cloudflare proxy" twice (architecture diagram + tech stack);
  consolidate.
- **No CONTRIBUTING.md, no CODE_OF_CONDUCT.md, no .github/PULL_REQUEST_TEMPLATE.md.** These
  are nice-to-have for an open project; don't ship in week 1, can add in week 2 if license
  is decided.
- **Backend domain models are listed informally in the README** — at some point they need
  to be in the actual SQLAlchemy models. This is hours, not days.

## Things the repo is doing well

A red team isn't a complete picture without acknowledging what's working:

- **The MVP flow is correctly identified.** "User browses → hires → backend creates job →
  agent uses tools → result saved → user pays USDC → developer earns." This is the right
  shape.
- **The architecture diagram is clean.** Cloudflare → Nginx → FastAPI + React + Postgres.
  Standard, debuggable, deployable.
- **CI/CD with Jenkins is already wired.** Many hackathon teams don't have CI; this team
  does.
- **Infrastructure is provisioned and live** (Google Cloud VM, hackathon.navontech.dev,
  Let's Encrypt, Cloudflare). Shimon shipped real infra on day 1; that's a good sign.
- **Backend, infra, and frontend skills are well-distributed** across the team. The only
  major gap (Solidity) is closed with Chuan.

## Summary — what to fix this week

In priority order:

1. **Commit to the demo vertical.** On-chain research as the lead. Decision by end of Day 2.
2. **Commit to real MCP.** Drop the "MCP-style" hedge. Use fastmcp.
3. **Ship the agent passport schema.** Two tables, content-hashed traces.
4. **Make real Arc settlement the end-of-week-1 deadline.** No mocked USDC by demo day.
5. **Lock the license.** MIT recommended.
6. **Make Marten the schedule/flow owner.** Stand up the daily sync.

Items 1–3 unlock the pitch's differentiation. Items 4–6 unblock execution. Everything else
can wait or is in-flight.
