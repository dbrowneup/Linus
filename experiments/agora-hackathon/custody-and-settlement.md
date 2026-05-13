# Custody and Settlement Architecture

> **Audience:** Agent Market hackathon team (and especially Chuan Bai, who likely owns the
> smart contract implementation)
> **Purpose:** Make the custody decision explicit and irreversible before any smart contract
> is written, because custody choice is the single most consequential architectural decision
> in the project — both for security and for the regulatory profile of the demo.

## The non-negotiable: platform never custodies user funds

**Agent Market's smart contract architecture must keep user funds outside the platform's
control at all times.** This is the rule that gets us out of all the failure modes that look
like "centralized intermediary holds USDC, has a bad day, users lose money." It also keeps us
out of regulatory categories we are not equipped to handle (money transmitter, custodian,
trust company).

If the team is ever tempted to violate this rule for UX reasons, the answer is no. There is
always a non-custodial pattern that achieves the same UX, and it is always worth the extra
engineering hour.

## The three custody patterns to choose from

Any pay-per-operation flow needs to handle three actors: the user (paying USDC), the agent
developer (receiving USDC), and the platform (taking a fee). The question is: **who holds the
USDC between when the user pays and when the developer receives it?**

### Pattern A — Per-job escrow contract (recommended)

The user prepays USDC into an Arc-native escrow contract scoped to a specific `job_id`. The
contract holds the USDC until the agent completes the job, at which point a settlement function
releases USDC to the developer's address and the platform fee address simultaneously. If the
job fails or is disputed (v2), the contract returns USDC to the user.

**Pros:**

- User funds are never held by the platform.
- Settlement is atomic — developer payout and platform fee land in the same transaction.
- Auditable: anyone can see the contract's balance, deposits, and withdrawals on Arc.
- Smart contract surface is small (one escrow contract + a fee-recipient parameter).
- Matches the [x402 mental model](https://www.x402.org/) for HTTP-payment-flows; we can
  potentially use x402 primitives if `@x402/mcp` ships in time.

**Cons:**

- Requires a smart contract on Arc, which means Chuan (or whoever owns contracts) needs to
  ship it, test it on Arc testnet, and deploy.
- A new escrow contract per job is gas-expensive at scale; for v1 demo this doesn't matter,
  but at production we'd want a factory pattern (one master contract, many jobs).

**Risk surface:** the escrow contract itself. If it has a bug, funds can be locked or
extracted. Mitigation: keep the contract small (under 100 lines), do not add features beyond
the minimum, test against Arc testnet, have a second team member read the contract before
deployment.

### Pattern B — Session keys / smart-account spend limits (ERC-4337)

The user's smart-account wallet (an ERC-4337 implementation) is configured with session keys
that grant the platform's agent a bounded spending allowance scoped to a particular job. The
agent draws down from the user's wallet directly as it works.

**Pros:**

- Even more user-friendly in theory: the user "pre-authorizes," the agent acts, no escrow
  contract is needed.
- Aligns with where the smart-account world is heading.

**Cons:**

- Significantly more complex to implement. Smart accounts on Arc require a working bundler,
  paymaster, and session-key implementation. Arc is on testnet; tooling may not be mature.
- Harder to demonstrate to a hackathon judge in 60 seconds. "Look at this on-chain escrow"
  is a clearer narrative than "look at this session-key authorization."
- Doesn't solve a problem we have. The escrow pattern already keeps funds non-custodial; we
  don't gain anything substantive by going to session keys for v1.

**Risk surface:** the full ERC-4337 stack plus our session-key implementation. Larger attack
surface than the escrow contract.

### Pattern C — Platform custodies user funds (rejected)

The user pays USDC to a platform-controlled wallet. The platform later pays the developer
out of its own wallet, less the fee.

**Pros:**

- Simplest UX-wise. "Buy credits, spend credits" model.

**Cons:**

- **Regulatory exposure.** Holding user funds in custody is regulated activity in most
  jurisdictions. Depending on volume, we could be a money transmitter, a payment processor,
  or worse. Not where we want to be for a hackathon demo, let alone a real product.
- **Trust failure mode.** A platform that holds funds becomes a trust target. One mistake,
  one bad actor, one drained wallet, and the platform is over.
- **Forecloses the "no token to learn" wedge.** Centralized custody undermines the
  "permissionless, verifiable, USDC-native" pitch.

**This pattern is rejected.** Do not consider it in the demo or in the v1 architecture. It
is not allowed in this project.

## The recommendation: Pattern A for v1

Ship the per-job escrow contract. The minimum viable surface:

- **A single contract type** — `JobEscrow.sol` (or whatever the Arc-native Solidity-equivalent
  is named).
- **Three functions:**
  - `deposit(jobId, amount)` — user calls this to fund the job. Takes USDC, holds it.
  - `settle(jobId)` — callable by the platform's signer after job completion. Releases the
    USDC to the developer's address (minus the fee) and the fee to the platform's fee address.
  - `refund(jobId)` — callable by the platform's signer (or anyone after a timeout) if the
    job fails. Returns USDC to the user.
- **Two parameters:**
  - `feeBps` — the platform's take rate in basis points. Initialize at 500 (5%); make
    governance-changeable later.
  - `feeRecipient` — the platform's fee-collection address.
- **Per-job state:**
  - `jobId`, `user`, `developer`, `amount`, `status` (open / settled / refunded).

**Total complexity:** small. ~50–80 lines of Solidity, exclusive of imports.

**Estimated build time:** 1–2 days for Chuan to write, test, and deploy to Arc testnet.

## The platform's "settler" role: how it works without custody

Here's the subtlety that makes Pattern A work without the platform being a custodian:

The platform's signer can call `settle()` and `refund()`, but it cannot drain the contract.
The contract has no `withdraw()` or `emergencyExit()` or similar function. The only ways USDC
leaves the contract are:

- The `settle()` path, which is forced to send to the developer and the fee address in the
  configured proportions.
- The `refund()` path, which is forced to send back to the user.

The platform's signer is a **trigger**, not a **custodian**. It has the right to decide
"this job is done, run the settlement logic" — but the settlement logic is on-chain and the
platform cannot alter where the funds go. This is a critical distinction for the regulatory
profile and for the pitch's defensibility.

## Auxiliary contracts

In addition to the escrow contract, there is one other tiny contract worth shipping for v1:

### The passport-anchor contract

A separate contract that lets the platform anchor a content hash + storage pointer per job.
This is the on-chain part of the `agent-passport-spec.md` design. Functions:

- `anchor(jobId, traceHash, storagePointer)` — callable by the platform's signer after job
  completion. Emits an event with the hash and pointer; optionally stores them in contract
  state.

Total complexity: ~20 lines. Trivial. This is what gives the agent passport its
"verifiable independent of platform" property.

## What to NOT add to the contracts in v1

Resist all of these:

- **Slashing for bad agent performance.** Requires a dispute mechanism, which requires a
  governance layer or oracle. Out of scope for v1.
- **Time-locks beyond a simple "if not settled in 30 days, refundable."** Don't build
  vesting, multi-stage releases, etc. Not needed.
- **Multi-currency support.** USDC only.
- **Cross-chain bridges.** Arc only.
- **Tokenized escrow positions.** Don't mint NFTs or tokens representing in-progress jobs.
- **Governance / DAO mechanics.** Single-admin-key for fee parameters in v1; revisit in v2.
- **Subscription pricing.** Per-operation only.

Every one of these is plausibly nice. Every one of them adds attack surface, audit cost, and
demo complexity. Hold the line at the minimum surface.

## Testing discipline

Because we are not getting a formal audit before the demo, we need to substitute discipline:

1. **Test on Arc testnet first.** Every flow that touches money runs on testnet before any
   demo dependency exists on it.
2. **Two team members read every contract.** Chuan writes; one of Shimon, Daniel R, or the
   6th member reads. Find bugs in pairs, not solo.
3. **Forge / Hardhat test suite.** At minimum: happy-path deposit-settle, happy-path
   deposit-refund, invariant tests (no path drains the contract, fees always sum correctly).
4. **No upgrade pattern in v1.** Don't use OpenZeppelin's upgradeable contracts. Deploy
   immutable. If we find a bug, we deploy a new one and migrate. (Upgrade patterns add their
   own bug surface.)

## What the team's USDC operational hygiene looks like

Separate from the contracts, the team's day-to-day operations need to follow basic hygiene:

- **Dedicated dev wallets for testing.** Never connect a wallet that holds real value.
- **`.env` files gitignored.** No private keys in the repo, ever. Use environment variables
  or, better, hardware wallets / Anvil dev accounts on testnet.
- **The platform's signer key is NOT in the GitHub repo.** It lives in a secrets manager
  (initially, just on Chuan's machine in a `.env` file; in v2, in a secret manager service).
- **The platform's fee-recipient address is on a hardware wallet** or, for the demo, on a
  cold wallet none of us have used elsewhere.
- **Don't paste any keys, even testnet ones, into Discord or any AI chat.**

These are not glamorous, but the worst-case outcome for the demo is "we shipped, then someone
got compromised, and Circle's people noticed."

## What happens if Chuan is the bus factor of 1

Chuan owns the smart contract. If he gets sick, takes a job emergency, or otherwise becomes
unavailable mid-week, the team needs to continue. Mitigations:

- **Keep the contract small enough that a non-Chuan team member can read it in 30 minutes.**
  This is the strongest mitigation. The contract should be ~80 lines.
- **Document the deploy steps** in `docs/deploy.md` so any team member can ship a hotfix.
- **Don't make Chuan the only person with the deploy key.** Pair him with at least one other
  team member who has the secrets and can execute a redeploy if needed.

## Summary

- Custody pattern: **Per-job escrow contract on Arc** (Pattern A).
- Reject: platform custody (Pattern C). Defer: smart accounts (Pattern B) to v2.
- Minimum surface: one escrow contract + one passport-anchor contract. ~100 lines total.
- Don't add slashing, governance, or upgradeability in v1.
- Test on Arc testnet; pair-review every line of Solidity.
- Demo target: live USDC settlement on Arc, in front of judges, with the audit trail visible.
