## DEC-0058 — `@x402/mcp` graduation pathway: Watch → Spike → Integrate, with concrete triggers

**Date:** 2026-05-16 **Status:** accepted (defines graduation triggers)

**Context.** The Canteen-blog landscape note (`context/notes/canteen_blog_landscape_2026-05.md` §"x402 v2 Release") and
the `entrepreneurship-synthesis.md` §E13 entry both flagged `@x402/mcp` — the MCP-transport extension of Coinbase's
x402 HTTP-402 payment protocol — as a tracked-but-deferred integration point, with a seeded ADR slot
(`DEC-NNNN agent-monetization-via-x402-mcp`). The Canteen post (dated 2025-12-01) described `@x402/mcp` as
roadmap-only.

The 2026-05-10 PR 30 fold-in surfaced the factual update (`repo-notes/x402.md` §1, §3): **`@x402/mcp` is now shipped at
v2.10.0** across TypeScript (`@x402/mcp`), Python (`x402[mcp]`), and Go (`x402-foundation/x402/go/mcp`), with a complete
server-side `createPaymentWrapper` API, a client-side `createX402MCPClient` factory, hook surfaces for
`onBeforeExecution` / `onAfterExecution` / `onAfterSettlement` (server) and `onPaymentRequired` / `onBeforePayment` /
`onAfterPayment` (client), and a documented MCP-SDK workaround for embedding 402 payment-required errors in
`McpError`-converted tool results. The Canteen framing of "signaled but not yet shipped" is half-true: the integration
point is **shipped**, but its stability and production usage are still early — the SDK workaround is a freshness
signal, and there is no visible production deployment yet.

The current verdict on x402 is **Watch** (`repo-notes/x402.md` §6). The R4-03 entry asks: when does that verdict
graduate, to what, and on what trigger? Without explicit graduation triggers in the ADR layer, the Watch verdict
risks indefinite drift — either staying Watch when the field has moved (Phase 5+ planning arrives, the standard
matures, and Linus is still relying on a stale read), or jumping straight to Integrate without a Spike step
(committing to a payment substrate before measuring the cost). Closes **R4-03**; complements DEC-0046 (external_api
deployment field) and DEC-0045 (fastmcp default framework).

The decision is **not** "Linus will adopt x402." That commitment depends on Phase 5+ commercial-surface scope that
Linus has not yet decided to take. The decision is the **graduation rubric** that converts the current Watch verdict
into a Spike or an Integrate when the conditions are met — the rubric that keeps Watch from drifting into permanent
deferral or permanent dismissal.

**Decision.** `@x402/mcp` carries a three-step graduation pathway with explicit triggers and explicit outputs at each
step.

### Step 1 — Watch → Spike (a one-week experimental integration)

The Spike step kicks off when **any one** of the following triggers fires:

1. **A Phase 5+ commercial-surface decision lands** that names paid tool calls as in-scope. This is the most
   forcing trigger and is the path the entrepreneurship synthesis §E13 anticipated. Concretely: a Phase 5 (interface
   refinement) or Phase 7 (skills + autonomy) planning session produces an ADR or ROADMAP commit naming "Linus exposes
   a paid surface" as in-scope. The Spike is then the prior-art validation step before the implementation ADR.
2. **A Canteen-class hackathon or partnership opportunity** explicitly names x402 in its requirements. The Canteen
   outreach note (`context/notes/canteen_outreach_2026-05.md`) frames the Canteen-blog landscape as a possible
   commitment vehicle; if Canteen or a similar partnership names x402 as the payment substrate, the Spike validates
   `@x402/mcp` against Linus's MCP stack before partnership commitment.
3. **`@x402/mcp` reaches v3.x stable** with the MCP-SDK-limitation workaround resolved upstream **and** at least one
   independent visible production deployment. This is the maturity-based trigger that fires without any Linus-side
   commercial-surface forcing function — when the standard is mature enough to commit to in the abstract, Linus's
   Spike measures the cost of doing so concretely.

The Spike is **time-boxed at one week** of Worker-driven implementation effort, with the following deliverable
contract (mirroring the `repo-notes/x402.md` §7-Q8 tentative answer):

- Pick **one** Linus skill that could plausibly be paid — preferably one already tagged `external_api` per DEC-0046,
  so the Spike exercises the same registry-field surface a real paid skill would use.
- Wrap the skill with `@x402/mcp` server-side `createPaymentWrapper`. Use the FastMCP integration substrate per
  DEC-0045 — do not add a parallel MCP framework. The Spike specifically tests whether `@x402/mcp` composes cleanly
  with FastMCP middleware.
- Spin up a **test facilitator** (either the public `x402.org/facilitator` against a testnet, or a local mock
  facilitator). Run the full handshake from a Python `x402[mcp]` client.
- **Measure**: (a) latency overhead of the payment handshake vs. an unwrapped tool call; (b) the surface-area cost of
  the FastMCP/x402-MCP adapter layer (LoC, dependency count, transitive supply-chain risk per DEC-0024); (c) whether
  the SDK-limitation workaround manifests in any user-visible way; (d) the integration's compatibility with Linus's
  audit-log discipline (audit fields for `payment_required`, `payment_received`, `settled` events).
- **Output**: a recommendation paired with the measurement data — either "this is viable, draft the Integrate ADR" or
  "this is premature, push the seed another two quarters." The Spike output is committed in
  `experiments/x402-mcp-spike/` per the standard spike-artefact convention.

### Step 2 — Spike → Integrate (the real ADR)

The Integrate step graduates the `DEC-NNNN agent-monetization-via-x402-mcp` seed in DECISIONS.md to a real ADR, with
the Spike measurements as evidence. The Integrate ADR commits Linus to:

- A specific MCP-payment integration substrate (`@x402/mcp` if the Spike validated it, or a documented alternative).
- A specific facilitator posture — local-mock during development, third-party facilitator for production, or self-hosted
  facilitator if the privacy posture demands it (per `repo-notes/x402.md` §5).
- A specific scope of paid tools — which DEC-0046 `external_api`-tagged tools are eligible, what the registration flow
  looks like, and how the biosecurity tier policy (DEC-0047) interacts with paid surfaces (a Tier-C generative-biology
  tool must not be paid-accessible from anonymous clients regardless of payment, etc.).
- A specific position on **fiat-vs-crypto rails** (per `repo-notes/x402.md` §7-Q3, §7-Q5). The tentative scope-bounded-
  acceptable position — Linus's core orchestration stays off-chain, but a satellite project or harness-layer integration
  may be on-chain — is the leading candidate but is decided in the Integrate ADR with then-current evidence.

The Integrate ADR also names the **deployment phase**. The default expectation is Phase 5 (interface refinement) or
Phase 7 (skills + autonomy) — earlier is unlikely; later is acceptable if the commercial-surface decision has not
landed.

### Step 3 — Maintenance and re-evaluation

Post-Integrate, `@x402/mcp` is held to the same supply-chain discipline as any other Linus dependency (DEC-0024): the
package version is hash-pinned in the Linus env's lock file; `pip-audit` runs catch known vulnerabilities; any breaking
upstream change is treated as a Phase-blocker until a compatible Linus-side patch lands. If x402 itself loses adoption
to a competing standard (per the multi-standard landscape in `repo-notes/x402.md` §5 — Pump.fun fee-recipients,
Hyperliquid HIP-3, Polymarket V2 builder codes, Stripe-for-AI, OpenAI API key billing, Anthropic metering, etc.), the
Integrate ADR is reopened for re-evaluation. The reversal cost is bounded by the rail-agnostic-protocol-level design
position (`repo-notes/x402.md` §7-Q5) — Linus's internal `PaymentRequest` / `PaymentReceipt` typed pair adapts to x402
via a thin adapter package; the adapter is swappable.

### Negative-graduation paths

Two paths lead **away** from x402 rather than toward it:

- **Dismiss to Ignore.** If the Spike measurement shows the integration is unviable on Linus's infrastructure (the
  facilitator dependency leaks transaction flow incompatibly with Linus's privacy posture per DEC-0053; the latency
  overhead is operationally prohibitive; the FastMCP/x402-MCP composition requires invasive forks), the seed graduates
  to a documented Ignore verdict with the Spike measurements as the evidence record. The dismissal is **not** "we
  decided not to commercialize"; it is "this specific substrate doesn't fit, but a different commercial-surface
  substrate may fit later."
- **Re-evaluate without committing.** If the Spike is run but the Integrate trigger has not yet fired (no concrete
  commercial-surface decision; no Canteen-class commitment), the Spike output is filed as evidence and the seed
  stays open until the trigger fires. This is the expected path if the Spike is forced by a maturity-based trigger
  (#3 above) rather than a commercial-surface trigger (#1, #2).

**Consequence.** The Watch verdict on `@x402/mcp` is now bounded — it cannot drift into indefinite deferral because the
graduation triggers are concrete and dated against ROADMAP phases. The Spike is pre-specified so Worker dispatch can
begin immediately on trigger-fire without a separate planning round. The Integrate ADR's scope is pre-specified so the
Integrate decision is a fill-in-the-blanks exercise rather than an open-ended planning conversation. The negative paths
(Dismiss, Re-evaluate) are documented so a Spike-with-negative-results does not leave Linus stuck in "we measured but
never decided."

The decision **does not** commit Linus to commercial surface at any phase. The commercial-surface decision remains the
forcing function for Trigger #1; this ADR only specifies what happens when that decision (or one of the other two
triggers) lands. Linus may stay in Watch indefinitely if no trigger fires — that is an acceptable outcome and is the
expected outcome through Phase 4. The ADR earns its keep by ensuring Phase 5+ planning does not have to relearn the
prior art from scratch when a trigger does fire.

The **MCP-SDK-limitation workaround pattern** documented in `repo-notes/x402.md` §7-Q6 — embedding structured error
data inside a tool result as JSON-serialized payload to work around MCP-SDK's `error.data`-loss conversion — is folded
into Linus's MCP convention library as a standalone pattern, independent of the x402 graduation pathway. Any future
Linus MCP tool that needs to surface structured error data through the SDK (rate-limit info, auth-failure data,
payment-required data) can use the same shape. The x402 spike validates the pattern by exercising it; the convention
library captures the pattern even if x402 itself never ships.
