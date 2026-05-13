# Strategy Passport — Implementation Spec

> **Audience:** Backend engineers + smart contract owner (Chuan)
> **Status:** Draft v1 — builds on Chuan's `ReasoningTrace` shape in
> [`../design.md` § 4.4](../design.md), formalizes the per-strategy passport schema, and
> threads the paper-claim binding through to on-chain anchoring.
> **Prerequisite reading:** [`../architectural-principles.md`](../architectural-principles.md)
> for the philosophy.

## Goal

Make every strategy and every agent decision **independently auditable** — by future users,
by reviewers, by the agent itself when replaying historical decisions. The defensibility of
the platform rests on this primitive.

The strategy passport extends Chuan's existing `Strategy` dataclass (design.md § 4.1) and
`ReasoningTrace` dataclass (design.md § 4.4) with the additional structure needed to make
the verifiability claim concrete.

## Schema

Three tables, plus one extension to Chuan's existing `strategies` table.

### Table extension: `strategies` (additions to Chuan's existing schema)

```sql
-- New columns on the existing strategies table per design.md § 4.1
ALTER TABLE strategies ADD COLUMN paper_arxiv_id        VARCHAR(64);
ALTER TABLE strategies ADD COLUMN paper_title           TEXT;
ALTER TABLE strategies ADD COLUMN paper_authors         TEXT[];
ALTER TABLE strategies ADD COLUMN paper_venue           VARCHAR(128);   -- journal, conference, "arxiv only"
ALTER TABLE strategies ADD COLUMN paper_year            INTEGER;
ALTER TABLE strategies ADD COLUMN paper_doi             VARCHAR(128);
ALTER TABLE strategies ADD COLUMN paper_citation_count  INTEGER;        -- snapshot at curation time
ALTER TABLE strategies ADD COLUMN methodology_hash      BYTEA NOT NULL; -- 32 bytes, content hash of extracted methodology
ALTER TABLE strategies ADD COLUMN methodology_text      TEXT NOT NULL;  -- the actual extracted methodology
ALTER TABLE strategies ADD COLUMN extraction_llm        VARCHAR(64);    -- which model extracted it (claude-3.5-sonnet, etc.)
ALTER TABLE strategies ADD COLUMN extraction_prompt_hash BYTEA;         -- hash of the prompt used (reproducibility)
ALTER TABLE strategies ADD COLUMN curator_wallet        VARCHAR(64);    -- wallet of human who validated (v1: Dan)
ALTER TABLE strategies ADD COLUMN curator_validation_at TIMESTAMPTZ;
ALTER TABLE strategies ADD COLUMN on_chain_registration_tx VARCHAR(128); -- StrategyRegistry contract tx
```

### Table extension: `backtest_results` (additions to Chuan's existing schema)

```sql
-- New columns on the existing backtest_results table per design.md § 4.2
ALTER TABLE backtest_results ADD COLUMN paper_claimed_sharpe    NUMERIC(8,4);
ALTER TABLE backtest_results ADD COLUMN paper_claimed_cagr      NUMERIC(8,4);
ALTER TABLE backtest_results ADD COLUMN paper_claimed_max_dd    NUMERIC(8,4);
ALTER TABLE backtest_results ADD COLUMN backtest_engine         VARCHAR(32); -- 'backtrader' | 'vectorbt' | 'custom-numpy'
ALTER TABLE backtest_results ADD COLUMN backtest_code_hash      BYTEA;       -- hash of the executable backtest code
ALTER TABLE backtest_results ADD COLUMN transaction_cost_bps    INTEGER DEFAULT 10;
ALTER TABLE backtest_results ADD COLUMN walk_forward_split      NUMERIC(4,2) DEFAULT 0.70; -- train fraction
ALTER TABLE backtest_results ADD COLUMN out_of_sample_sharpe    NUMERIC(8,4); -- separately from in-sample
ALTER TABLE backtest_results ADD COLUMN look_ahead_audit_passed BOOLEAN DEFAULT FALSE;
```

### New table: `reasoning_traces` (extends Chuan's dataclass)

Chuan's `ReasoningTrace` dataclass becomes this table:

```sql
CREATE TABLE reasoning_traces (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id        UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    decision_type       VARCHAR(32) NOT NULL,   -- rebalance | rotation | regime_change | construction | initial
    trigger             VARCHAR(64) NOT NULL,   -- what caused this decision (drift | regime | calendar | decay | user)
    market_context      JSONB NOT NULL,         -- regime, key metrics at decision time
    reasoning_text      TEXT NOT NULL,          -- LLM-generated explanation
    action_taken        JSONB NOT NULL,         -- concrete trades executed (or planned, if dry run)
    expected_outcome    TEXT,                   -- what the agent expects to happen
    confidence          NUMERIC(4,3),           -- 0.000 - 1.000
    strategies_invoked  UUID[] NOT NULL,        -- which strategies were considered/used
    tool_calls_count    INTEGER DEFAULT 0,
    content_hash        BYTEA NOT NULL,         -- 32 bytes, keccak256 of the full trace
    storage_pointer     TEXT NOT NULL,          -- URL/IPFS/Arweave to the full trace JSON
    storage_type        VARCHAR(16) NOT NULL,   -- 'url' | 'ipfs' | 'arweave'
    byte_length         INTEGER NOT NULL,
    encoding            VARCHAR(16) DEFAULT 'utf-8',
    on_chain_anchor_tx  VARCHAR(128),           -- Arc tx hash for the registry call (NULL until anchored)
    on_chain_anchor_at  TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reasoning_traces_portfolio_id ON reasoning_traces(portfolio_id);
CREATE INDEX idx_reasoning_traces_decision_type ON reasoning_traces(decision_type);
CREATE INDEX idx_reasoning_traces_created_at ON reasoning_traces(created_at);
CREATE INDEX idx_reasoning_traces_content_hash ON reasoning_traces(content_hash);
```

### New table: `tool_call_provenance`

```sql
CREATE TABLE tool_call_provenance (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reasoning_trace_id  UUID NOT NULL REFERENCES reasoning_traces(id) ON DELETE CASCADE,
    tool_name           VARCHAR(128) NOT NULL,  -- e.g. 'market_data.vix' | 'paper_search.semantic_scholar' | 'usyc.yield'
    tool_provider       VARCHAR(64),            -- e.g. 'circle_sdk' | 'yfinance' | 'arxiv_api'
    input_payload       JSONB,                  -- the tool's inputs (may be redacted for sensitive)
    input_hash          BYTEA NOT NULL,         -- hash over canonical-encoded input
    output_payload      JSONB,                  -- the tool's outputs (may be redacted)
    output_hash         BYTEA NOT NULL,         -- hash over canonical-encoded output
    latency_ms          INTEGER,
    error_state         VARCHAR(32),            -- NULL on success; 'timeout', 'rate_limit', 'error_response'
    invoked_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tool_call_provenance_trace_id ON tool_call_provenance(reasoning_trace_id);
CREATE INDEX idx_tool_call_provenance_tool ON tool_call_provenance(tool_name);
```

### New table: `paper_corpus`

For the curated strategy library to be auditable, we need to track papers themselves
separately from the strategies derived from them.

```sql
CREATE TABLE paper_corpus (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    arxiv_id            VARCHAR(64) UNIQUE,     -- nullable for non-arxiv papers
    doi                 VARCHAR(128) UNIQUE,    -- nullable
    title               TEXT NOT NULL,
    authors             TEXT[] NOT NULL,
    venue               VARCHAR(128),
    year                INTEGER,
    categories          VARCHAR(16)[],          -- q-fin.PM, q-fin.TR, etc.
    citation_count_at_curation INTEGER,
    abstract            TEXT,
    pdf_storage_pointer TEXT,                   -- URL to our cached PDF copy
    pdf_hash            BYTEA,                  -- hash of cached PDF for integrity
    curator_wallet      VARCHAR(64),
    curator_note        TEXT,                   -- Dan's per-paper rationale
    added_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE NULLS NOT DISTINCT (arxiv_id, doi)   -- both can be NULL but the pair must be unique
);

CREATE INDEX idx_paper_corpus_arxiv_id ON paper_corpus(arxiv_id);
CREATE INDEX idx_paper_corpus_categories ON paper_corpus USING GIN(categories);
```

## API surface

The passport adds these endpoints to Chuan's planned API:

```
GET    /api/strategies/{id}/passport
       → strategy's full passport: paper info, methodology, backtest, validation status,
         on-chain registration tx

GET    /api/strategies/{id}/paper
       → underlying paper metadata + PDF storage pointer

GET    /api/portfolios/{id}/decisions
       → paginated list of all reasoning traces for this portfolio

GET    /api/decisions/{trace_id}
       → single reasoning trace with full metadata + tool calls

GET    /api/decisions/{trace_id}/trace
       → fetches the actual full trace JSON from storage
         - hits the storage_pointer
         - returns with header indicating computed hash matches stored hash
         - returns 422 if hash mismatch (storage corruption)

GET    /api/decisions/{trace_id}/tool-calls
       → list of tool calls invoked during this decision

POST   /api/decisions/{trace_id}/anchor       (internal, called by agent after settlement)
       → calls the ReasoningTraceRegistry contract on Arc
         - inputs: trace_id, content_hash, storage_pointer, decision_type
         - emits event; updates reasoning_traces.on_chain_anchor_tx

GET    /api/paper-corpus
       → list all papers in the curated corpus, filterable by category/year/curator

GET    /api/paper-corpus/{id}/strategies
       → all strategies derived from a given paper
```

## Integration with the agent's decision flow

This is how the passport gets populated as the agent operates:

1. **User connects wallet, picks risk profile** → backend creates a `portfolios` row.
2. **Agent constructs portfolio v0:**
   - Selects strategies from the library (Chuan's design.md § 4.3.2).
   - For each strategy, looks up its passport (paper + methodology + backtest).
   - Computes weights using Kelly + correlation-aware optimization (Önder's math module).
   - Writes a `reasoning_traces` row with `decision_type='construction'`.
   - For each tool call (regime check, USYC yield lookup, etc.), writes a
     `tool_call_provenance` row.
   - Computes `content_hash = keccak256(canonical_trace_json)`.
   - Stores the full trace JSON in cloud storage; updates `storage_pointer`.
3. **Agent executes trades:**
   - Vault contract `rebalance()` called with the action_taken from the trace.
   - On-chain tx hash recorded back in `reasoning_traces.action_taken.tx_hash`.
4. **Agent anchors the trace:**
   - ReasoningTraceRegistry `publishTrace(traceId, contentHash, storagePointer)` called.
   - Tx hash recorded in `reasoning_traces.on_chain_anchor_tx`.
5. **Live agent loop (Week 2 onwards):**
   - Regime detection runs continuously.
   - On trigger (drift, regime change, decay, calendar), agent constructs a target
     portfolio.
   - Cost-benefit check (see design.md § 4.3.4).
   - If positive: execute trades, write new `reasoning_traces` row, anchor.
   - If negative: log a "rebalance skipped" trace, anchor that too (failures are
     auditable).

## Content-hashing details

`keccak256` over canonical-encoded JSON. "Canonical" means:

- UTF-8 string.
- No trailing whitespace; `\n` line endings.
- JSON serialized with sorted keys, no extra spaces:
  `json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)`.
- Numeric precision: floats serialized with 8 decimal places fixed.

Document the canonicalization in `src/lib/canonical.py` (or equivalent) so anyone can
recompute the hash from the stored content.

## Smart contract integration

Reference Chuan's `ReasoningTraceRegistry.sol` and `StrategyRegistry.sol` from
[`../design.md` § 5.2](../design.md). Concretely:

**StrategyRegistry — when registering a curated strategy:**

```solidity
function registerStrategy(
    bytes32 strategyId,            // keccak256(paper_arxiv_id || methodology_hash)
    bytes32 methodologyHash,
    bytes32 paperCorpusHash,       // links to the paper_corpus row
    bytes calldata metadata        // ABI-encoded: paper_arxiv_id, paper_title, curator_wallet
) external onlyCurator;
```

**ReasoningTraceRegistry — when anchoring a decision:**

```solidity
function publishTrace(
    bytes32 traceId,
    bytes32 contentHash,
    string  calldata storagePointer,
    uint8   decisionType,           // enum: 0=construction, 1=rebalance, 2=rotation, 3=regime, 4=skipped
    uint256 portfolioId
) external onlyAgent;
```

Events emitted; off-chain indexer picks up and links to DB rows.

## Frontend / UI implications

The passport's value is mostly realized in the UI. For v1:

- **Strategy detail page** — shows paper title, authors, arxiv link, methodology
  summary, backtest results with paper-claimed comparison, validation timestamp, on-chain
  registration tx hash.
- **Portfolio dashboard "decisions" tab** — chronological list of reasoning traces. Each
  entry shows: trigger, regime context, action summary, on-chain tx link.
- **Decision detail page** — full reasoning trace, expandable tool calls, "Verify trace
  hash" button that recomputes in-browser and shows green checkmark vs on-chain anchor.
- **Paper viewer** — embedded or linked PDF of the source paper for each strategy.

**The "Verify trace hash" UI element is the demo wow-moment for the passport.** Without
it, the verifiability is invisible to humans and the differentiation collapses.

## Edge cases and what to NOT do

- **Trace is too large.** Cap at 1 MB v1. If exceeded, store summarized trace + flag
  truncation; hash the truncated version.
- **Tool output is sensitive.** v1 stores all tool outputs publicly. v2 can encrypt
  per-trace with shared key to authorized auditors.
- **Agent decision fails mid-flight.** Still write the trace, with action_taken capturing
  the partial state. Failed decisions are auditable too.
- **Don't add aggregate ratings.** No `confidence_score` or `quality_rating` on
  `strategies` beyond the explicit backtest metrics. The reputation surface is the
  queryable history.
- **Don't anchor speculative traces.** Construction traces are anchored *after* the vault
  trades execute, not before. (A trace that didn't result in trades is still anchored,
  but the action_taken field captures the no-op.)
- **Don't allow trace edits.** `reasoning_traces` has no UPDATE on `content_hash` or
  `storage_pointer` — if a bug requires rewriting a trace, that's a v2 conversation
  (probably never).

## Estimated lift

| Component                                         | Owner        | Days  |
| ------------------------------------------------- | ------------ | ----- |
| Backend schema migration + reasoning trace writes | Daniel       | 1.5   |
| Paper corpus + curator workflow                   | Dan          | 1     |
| Tool-call provenance instrumentation              | Daniel       | 0.5   |
| Storage backend (S3 / R2)                         | Backend lead | 0.5   |
| ReasoningTraceRegistry contract                   | Chuan        | 0.5   |
| StrategyRegistry contract                         | Chuan        | 0.5   |
| "Verify trace" UI element                         | Daniel       | 1     |
| Strategy detail page (with paper)                 | Daniel       | 0.5   |

**Total: ~5–6 person-days, well-parallelizable.** Fits inside Week 1 alongside the rest of
the Week-1 milestones in [`../design.md` § 8](../design.md).

## Acceptance criteria for v1

- [ ] Each curated strategy has a populated `paper_arxiv_id` + `methodology_hash` +
      `methodology_text`.
- [ ] Each backtest result has `paper_claimed_sharpe` populated for comparison.
- [ ] Every agent decision produces a `reasoning_traces` row.
- [ ] Every tool call during a decision produces a `tool_call_provenance` row.
- [ ] Every settled decision is anchored to Arc via ReasoningTraceRegistry; tx hash
      queryable.
- [ ] The "Verify trace" UI element fetches the trace, recomputes the hash, and shows
      pass/fail vs the on-chain anchor.
- [ ] The `GET /api/portfolios/{id}/decisions` endpoint returns the full ordered decision
      history.
