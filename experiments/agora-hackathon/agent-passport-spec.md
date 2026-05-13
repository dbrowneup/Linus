# Agent Passport — Implementation Spec

> **Audience:** Backend engineers (Shimon, Daniel R) + smart contract owner (Chuan)
> **Status:** Draft v1 — intended as the implementable spec for the v1 demo
> **Prerequisite reading:** [`architectural-principles.md`](architectural-principles.md)
> for the philosophy, [`custody-and-settlement.md`](custody-and-settlement.md) for the
> on-chain anchor contract.

## Goal

Produce a verifiable, queryable record of every agent's prior jobs that future buyers can
audit before hiring. The passport's defensibility comes from:

1. **Content-hashed reasoning traces** stored off-chain, anchored on Arc.
2. **Tool-call provenance** capturing what the agent had access to and used.
3. **Job-level binding** — every record ties to a discrete unit of paid work.
4. **Developer attribution** linking each agent to its publisher.

Schema details, API surface, and the integration with the job flow follow.

## Schema additions

These are new tables. The existing `Agent` / `Job` / `ToolCall` / `Payment` models stay
mostly as-is, with minor additions noted.

### New table: `reasoning_traces`

```sql
CREATE TABLE reasoning_traces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id          UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    content_hash    BYTEA NOT NULL,            -- 32 bytes (Keccak-256 of the trace text)
    storage_pointer TEXT NOT NULL,             -- URL, IPFS CID, or Arweave tx id
    storage_type    VARCHAR(16) NOT NULL,      -- 'url' | 'ipfs' | 'arweave'
    byte_length     INTEGER NOT NULL,          -- size of the raw trace
    encoding        VARCHAR(16) DEFAULT 'utf-8', -- 'utf-8' | 'gzip' | 'br'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    on_chain_anchor_tx TEXT,                   -- Arc tx hash for the passport-anchor call, NULL if not yet anchored
    on_chain_anchor_at TIMESTAMPTZ,
    UNIQUE (job_id)                            -- one trace per job
);

CREATE INDEX idx_reasoning_traces_content_hash ON reasoning_traces(content_hash);
CREATE INDEX idx_reasoning_traces_job_id ON reasoning_traces(job_id);
```

**Why these fields:**

- `content_hash` is the integrity primitive. SHA-256 or Keccak-256 — pick one and stick to
  it. Keccak-256 is the EVM-native choice (matches Solidity's `keccak256`); SHA-256 is the
  more general choice. Recommend Keccak-256 since we're anchoring on Arc.
- `storage_pointer` + `storage_type` decouple storage choice from the spec. v1 can use a
  platform-hosted URL (S3, Cloudflare R2); v2 can move to IPFS / Arweave for full
  decentralization. Same schema works.
- `byte_length` + `encoding` let buyers decide whether to fetch — if a trace is 5 MB, they
  may not bother.
- `on_chain_anchor_tx` is NULL until the anchor contract is called; this allows the demo
  to log a trace immediately and anchor asynchronously (or on a settled-jobs-only basis).
- `UNIQUE (job_id)` enforces one trace per job — no rewriting history.

### New table: `tool_call_provenance`

This is the structural extension of the existing `ToolCall` table. Either extend the
existing `tool_calls` table OR create a new `tool_call_provenance` table; my recommendation
is to extend the existing one to avoid two-source-of-truth headaches.

If extending `tool_calls`:

```sql
ALTER TABLE tool_calls ADD COLUMN input_hash BYTEA;          -- 32 bytes
ALTER TABLE tool_calls ADD COLUMN output_hash BYTEA;         -- 32 bytes
ALTER TABLE tool_calls ADD COLUMN mcp_server_id VARCHAR(64); -- which MCP server provided this tool
ALTER TABLE tool_calls ADD COLUMN tool_manifest_hash BYTEA;  -- hash of the MCP manifest at call time
```

**Why these fields:**

- `input_hash` + `output_hash` let the passport assert "the agent called this tool with this
  input and got this output" without exposing potentially sensitive raw input/output to
  public storage. Raw values can still be stored in a private table if needed for the
  platform's own debugging.
- `mcp_server_id` ties the tool call to a specific MCP server, enabling later verification
  against that server's manifest.
- `tool_manifest_hash` captures what the agent's tool surface looked like at job time. This
  is what makes "the agent had access to these tools and no others" attestable.

### Minor changes to existing tables

**`agents`** — add columns:

```sql
ALTER TABLE agents ADD COLUMN developer_wallet VARCHAR(64) NOT NULL;
ALTER TABLE agents ADD COLUMN agent_framework VARCHAR(32);  -- 'eliza' | 'autogen' | 'swarms' | 'custom' | 'mcp-native'
ALTER TABLE agents ADD COLUMN mcp_manifest_url TEXT;        -- URL to the MCP manifest
```

**`jobs`** — add columns:

```sql
ALTER TABLE jobs ADD COLUMN escrow_contract VARCHAR(64);    -- Arc address of the job's escrow
ALTER TABLE jobs ADD COLUMN passport_anchored BOOLEAN DEFAULT FALSE;
ALTER TABLE jobs ADD COLUMN passport_anchor_tx TEXT;        -- Arc tx hash for the anchor
```

## API surface

The passport adds these endpoints to the planned API (which currently has `/api/health`,
`/api/agents`, `/api/jobs`, `/api/payments`):

```
GET    /api/jobs/{job_id}/passport
       → returns the passport record for a specific job, including:
         - trace metadata (hash, storage pointer, byte length)
         - all tool calls and their input/output hashes
         - on-chain anchor tx hash if anchored
         - developer wallet, agent framework

GET    /api/agents/{agent_id}/passport
       → returns the agent's full job history, paginated:
         - list of completed jobs with passport metadata
         - aggregate stats (job count, avg cost, time range)
         - link to each job's full passport

GET    /api/jobs/{job_id}/trace
       → fetches the actual reasoning trace from storage
         - first hits the storage_pointer to get the raw trace
         - returns it with a header indicating the computed hash matches the stored hash
         - returns 422 if the hash doesn't match (storage corruption)

POST   /api/jobs/{job_id}/anchor    (internal, called by platform after settlement)
       → calls the passport-anchor contract on Arc
         - inputs: job_id, content_hash, storage_pointer
         - emits an event; updates the jobs.passport_anchored flag
```

## Integration with the job flow

This is how the passport gets populated as a job runs. Each step is a clearly-defined hand-off
point.

1. **User hires agent** → `POST /api/jobs` creates a `jobs` row with status `pending`. User
   deposits USDC into the escrow contract.
2. **Agent runs** → the platform's job runner invokes the agent with the user's request.
   The agent uses MCP tools; each tool call gets logged to `tool_calls` with `input_hash`
   and `output_hash`.
3. **Agent completes** → the agent returns its result and reasoning trace.
4. **Platform writes the trace** → the platform:
   - Stores the raw trace in the configured backend (S3 / IPFS / etc.); gets back a
     `storage_pointer`.
   - Computes `content_hash = keccak256(trace_bytes)`.
   - Writes the `reasoning_traces` row (without `on_chain_anchor_tx`).
   - Updates the `jobs` row to status `completed`.
5. **Platform settles** → the platform's signer calls `settle(jobId)` on the escrow
   contract. USDC flows to the developer and the platform fee address.
6. **Platform anchors** → the platform's signer calls
   `anchor(jobId, contentHash, storagePointer)` on the passport-anchor contract. Captures
   the Arc tx hash; updates `reasoning_traces.on_chain_anchor_tx` and
   `jobs.passport_anchor_tx`.

Steps 5 and 6 can be batched into a single transaction sequence to save on Arc gas (which is
already cheap, but parsimony is free).

## Content-hashing details

Keccak-256 over the canonical-encoding of the reasoning trace. "Canonical" means:

- Trace is a UTF-8 string.
- No trailing whitespace, no platform-specific line endings (use `\n`, not `\r\n`).
- If the trace is JSON, serialize with sorted keys, no extra spaces (`json.dumps(obj,
  sort_keys=True, separators=(',', ':'))`).

The byte-level encoding rule is important because different serializations produce different
hashes. Document the canonicalization clearly so anyone can recompute the hash from the
storage and check it.

## On-chain anchor contract

This is the small Arc-native contract that captures the hash. Pseudocode (the actual
Arc-native equivalent of Solidity will look similar):

```solidity
pragma solidity ^0.8.20;

contract PassportAnchor {
    address public platform;

    event JobAnchored(
        uint256 indexed jobId,
        bytes32 traceHash,
        string  storagePointer,
        uint256 timestamp
    );

    constructor() {
        platform = msg.sender;
    }

    function anchor(
        uint256 jobId,
        bytes32 traceHash,
        string calldata storagePointer
    ) external {
        require(msg.sender == platform, "only platform");
        emit JobAnchored(jobId, traceHash, storagePointer, block.timestamp);
    }
}
```

That's it. ~20 lines. The contract emits an event; we don't store the data on-chain
because it's wasteful — the event is enough for indexers to pick up, and the off-chain
storage holds the actual trace.

**Why not store the hash + pointer in contract state?** Because emitting an event is cheaper
gas-wise, and we don't need to query historical anchor records on-chain (we query them from
the indexed event logs, or from our own database). State-storage is a v2 conversation if
we want trustless query-from-contract.

## Frontend / UI implications

The passport's value as a marketing wedge is mostly realized in the UI. For v1:

- **Agent profile page** — surfaces the agent's job count, recent jobs with one-line
  descriptions, "Audit this agent's history" CTA.
- **Job detail page** — shows the reasoning trace (fetched from storage), the tool calls
  used, the on-chain anchor tx (linked to Arc explorer).
- **"Verify trace" button** — fetches the raw trace and recomputes the hash in the
  browser; shows green checkmark if it matches the anchored hash. This is the **demo's wow
  moment** for the passport — judges can see the verifiability is real, not claimed.

Without the "verify trace" UI element, the passport is invisible to humans and the
differentiation collapses. **The frontend owner needs to prioritize this.**

## Edge cases and what to NOT do

- **Trace is too large.** Cap at 1 MB for v1. If an agent produces more, store the first
  1 MB and the last 1 MB, with a flag indicating truncation. Hash the truncated version.
- **Trace contains secrets the developer doesn't want public.** Out of scope for v1. v2
  pattern: encrypt the trace, share the decryption key with the buyer. The hash is over
  the encrypted bytes, which is sufficient for integrity.
- **Agent failed mid-job.** Still log the partial trace + tool calls. The passport should
  capture failures honestly; that's the point.
- **Don't add aggregate ratings.** No `rating_score` field on `agents`. The reputation
  surface is the queryable history.
- **Don't anchor before settlement.** A passport for an unsettled job is incomplete; the
  anchor goes after settlement so the passport is final.
- **Don't allow trace edits.** `reasoning_traces` has a `UNIQUE (job_id)` constraint; if a
  bug requires rewriting a trace, that's a v2 conversation (probably never — the
  immutability is the point).

## Estimated lift

- **Backend schema + endpoints** — 1-2 days (one engineer).
- **MCP tool-call provenance wiring** — 1 day (one engineer, partially in parallel with
  MCP integration work).
- **PassportAnchor contract + Arc testnet deployment** — 0.5 days (Chuan, parallel).
- **Frontend "verify trace" UI** — 1 day (frontend owner).
- **Storage backend** (S3 or R2 for v1) — 0.5 days (configuration, not new infrastructure).

**Total:** ~3-4 person-days, well-parallelizable across the team.

## Acceptance criteria for v1

- [ ] Any completed job has a `reasoning_traces` row with a content hash.
- [ ] Any completed job has tool-call provenance with input/output hashes.
- [ ] Any completed job (after settlement) is anchored to Arc via the PassportAnchor
      contract, with the tx hash queryable via the API.
- [ ] The "verify trace" UI element fetches the trace, recomputes the hash, and
      cross-references against the on-chain anchor. Pass/fail visible to the user.
- [ ] The `GET /api/agents/{agent_id}/passport` endpoint returns the full job history with
      links to each job's passport.
