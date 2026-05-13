# Architectural Principles for a Defensible Agent Marketplace

> **Audience:** Agent Market hackathon team
> **Purpose:** Set the design philosophy for the platform's core primitives. This doc is
> intentionally tactical-but-principled — it tells you what to build and why, without locking
> in specific schemas (those live in `agent-passport-spec.md`).

## The frame: marketplaces that don't ship verifiable history don't survive

Every agent marketplace today (see `competitor-landscape.md`) makes a reputation claim of some
kind. The differences are in **what backs the claim**. Three categories:

1. **Self-reported metadata** — listing ratings, descriptions, developer-supplied performance
   stats. ([Swarms.world](https://swarms.world/) sits closest to this.) Cheapest to ship,
   weakest defensibility. Easy to game.
2. **Token-price proxies** — the agent's tokenized share price is the reputation signal.
   ([Virtuals Protocol](https://www.virtuals.io/) is the canonical example.) Markets reflect
   beliefs about future performance, not what the agent actually did, and they're vulnerable to
   speculative bubbles disconnected from work output.
3. **Verifiable history** — a machine-readable record of each completed job, with the agent's
   reasoning trace and tool-call provenance preserved and auditable.
   ([Theoriq's Proof of Collaboration/Contribution](https://www.theoriq.ai/) is the closest
   shipped example, scoped to DeFi.) Hardest to ship, but most defensible — because anyone can
   read what the agent did.

**Agent Market's reputation system must be in category 3.** This is the load-bearing
architectural commitment that everything else flows from.

## Why category 3 is non-negotiable

Three independent arguments converge on the same conclusion:

1. **The competitive landscape forecloses category 1 and 2.**
   See `competitor-landscape.md`. Self-reported metadata is shipped by competitors with more
   resources and longer head starts. Token-price proxies have been tried for five years and
   haven't broken out for hire-shaped flows. Without verifiable history, our pitch reduces to
   "we're a worse Swarms or a less-funded Virtuals" — that's a losing pitch.

2. **The Canteen prompts implicitly require it.** Three of the four RFB ideas in the hackathon
   invitation depend on verifiable reasoning history:
   - "Trading-R1: Reasoning traces as the product" is explicit about hashing the trace and
     pinning it ([Wang et al. 2025](https://arxiv.org/abs/2509.11420))
   - "Slash-bonded copy-trading" requires a verifiable on-chain rank
   - "Translation as a source of alpha" assumes attributable structured outputs
   The hackathon sponsors are looking for verifiable-history architectures.

3. **Past performance does not persist out-of-sample.** This is the canonical failure mode of
   leaderboard-based reputation: top performers on Hyperliquid's leaderboard, on Polymarket, on
   any small-sample-size signal, decay back to mean. A "best-performing agents charge more"
   mechanic — without verifiable history — is structurally a leaderboard, and inherits the
   regression problem. Verifiable history bypasses the prediction problem entirely: the
   reputation is **what happened**, not **what we predict will happen**.

## The four primitives that make verifiable history work

These are the architectural commitments. Schema details are in `agent-passport-spec.md`; this
section is the **what and why**.

### Primitive 1: the reasoning trace

For every completed job, capture the agent's reasoning output — not just the final answer, but
the chain of intermediate reasoning that produced it. The trace is what makes the agent's
output auditable.

- **Stored off-chain** for cost reasons (reasoning traces are usually 1–100 KB, sometimes more).
- **Content-hashed** so its integrity is provable. The hash is a 32-byte digest (e.g., SHA-256
  or Keccak-256) that anyone holding the raw trace can recompute to verify it hasn't been
  tampered with.
- **Optionally anchored on-chain** — the hash, plus a pointer to the off-chain storage (an
  IPFS CID, an Arweave transaction ID, or just a URL), can be written to an Arc storage contract
  per job. This makes the trace publicly auditable without paying for on-chain storage of the
  trace itself.

The trace is the **what the agent did** part of the passport.

### Primitive 2: tool-call provenance

For every tool the agent invoked during a job, capture what tool was called, the input
parameters (hashed if sensitive), and the output the tool returned. This is what makes the
agent's tool surface auditable.

- **Why this matters separately from the trace:** a reasoning trace can claim "I checked
  Bloomberg for the latest BRK.B price," but without tool-call provenance, that's just a
  claim. Provenance proves the agent had Bloomberg as an available tool and that the tool
  responded as the agent reports.
- **Tied to MCP.** If the agent's tool surface is governed by an MCP server with a known
  manifest, the tools available to the agent are themselves a verifiable property. This is one
  of the strongest arguments for real MCP over "MCP-style" — without the protocol, the tool
  surface is just whatever the developer claims.

The provenance log is the **what the agent had access to** part of the passport.

### Primitive 3: the job-level binding

The reasoning trace and tool-call provenance are tied to a specific `job_id` — the discrete
unit of work the user paid for. This binding is what makes the marketplace structurally
honest:

- Each hire is a separate auditable record.
- Bad jobs don't get hidden; they live in the passport alongside good ones.
- Future buyers can read any prior job's full trace before hiring the same agent.

This is **not** an aggregate-rating system. Aggregate ratings smooth over failures. The passport
preserves them.

### Primitive 4: developer-attributable identity

Every agent listing is tied to a specific developer identity (wallet address + optional
human-readable handle). This is the **who built it** part of the passport.

- **Why an aggregate rating across an agent's jobs isn't enough**: we also need to roll up to
  the developer's overall record. A developer with three good agents and one rugged agent
  carries a different reputation than a developer with one consistently good agent.
- **On-chain attribution.** The developer's address is the recipient of the USDC payouts via
  the escrow contract; the same address is the listed-by field for the agent. Anyone can
  audit the developer's full portfolio.

## The three layers, named explicitly

Borrowing a framing from prediction-market architecture
([Canteen's _Unbundling the Prediction Market Stack_](https://canteenapp.com/blog) describes a
similar decomposition):

- **Agent layer** — the LLM-driven thing that does the work. Producible from any framework
  (Eliza, Swarms, AutoGen, custom). Framework-agnostic by design.
- **Identity layer** — the verifiable trace + tool-call provenance + developer attribution.
  This is what Agent Market actually owns and operates.
- **Venue layer** — the marketplace surface where users browse, compare, and hire. Where pitch
  and UX live.

Most competitors fold these together (the agent's framework is part of the platform, the
identity is the token, the venue is the developer's deployment). **Agent Market should keep
the three layers explicitly decoupled** because that's the architectural choice that makes
"framework-agnostic + MCP-native + verifiable passport" believable as a pitch.

## Design constraints these primitives imply

Once you commit to the four primitives, several design choices become forced:

1. **You commit to real MCP.** "MCP-style" adapters can't produce auditable tool-call
   provenance against a known manifest. See `mcp-integration-decision-memo.md` for the full
   argument.

2. **You commit to an on-chain anchoring path.** The passport's defensibility depends on the
   hash being verifiable independent of platform trust. If we lose the platform's database, the
   passport survives because anyone holding the off-chain trace can verify it against the
   on-chain hash. This requires a tiny Arc storage contract — much smaller than the escrow
   contract.

3. **You commit to content-hashing as the integrity primitive.** Not signatures, not platform
   attestations. The trace is what it is; any change to it changes the hash; anyone with the
   trace can verify it themselves.

4. **You commit to "verifiable history, not predictive performance" as the reputation thesis.**
   Don't ship a numeric score that claims to predict future performance. Ship the queryable
   history.

## What this doesn't commit you to

A short list of architectural choices that are NOT forced by these primitives — they remain
open, and the team can pick later:

- **Encryption of traces.** Optional. Some agents (especially in trading) may produce traces
  the developer doesn't want public. Hash-the-encrypted-trace + share-decryption-key-with-buyer
  is a v2 pattern.
- **Slashing or dispute resolution.** Don't ship in v1. The passport without slashing is
  already a defensible reputation system; slashing adds complexity without proving the wedge.
- **Token economics.** The pitch argues we don't need them. Don't introduce a token to capture
  marketplace upside; the take-rate on USDC settlement is the revenue model.
- **Particular UI patterns for the passport.** The data model dictates what's possible; how
  the team renders it (timeline view, table, drill-into-job) is a separate decision in week 2.

## How to evaluate whether a proposed feature respects these principles

When the team is deciding whether to add a feature, run it through this filter:

1. **Does it make any prior job's record less auditable?** If yes, push back hard.
2. **Does it tie reputation to predicted performance rather than actual history?** If yes,
   replace with a history-based equivalent.
3. **Does it lock us into a single framework or runtime?** If yes, push back — the
   framework-agnostic claim is part of the pitch.
4. **Does it require platform-custodied funds?** If yes, redesign. Funds flow through escrow,
   never through the platform.

A feature that fails any of these is a feature that erodes the architectural moat. Sometimes
it's worth the erosion (e.g., a v2 fiat on-ramp may require custodial intermediaries — but
that's a known v2 conversation). For v1, hold the line.

---

_The core claim of this doc: the verifiable agent passport is not a nice-to-have. It is the
single architectural commitment that makes Agent Market's pitch survive contact with the
existing market. Everything else flows from this._
