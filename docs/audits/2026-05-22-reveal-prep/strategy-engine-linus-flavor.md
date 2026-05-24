# Strategy engine — Linus-flavored retrospective + forward (refreshed 2026-05-23)

**Date:** 2026-05-23 (refresh of 2026-05-22 original).
**Author:** Maestro (Claude Code), for Dan, as input to his Archimedes strategy-engine ownership
work — not a replacement for it. Cross-checked against the live `repos/archimedes/` (~340 commits
since 2026-05-12) and against Dan's own source-verified bidirectional comparison at
[`docs/research/linus-archimedes-comparison.md`](../../../repos/archimedes/docs/research/linus-archimedes-comparison.md)
and the port-back companion
[`docs/research/archimedes-to-linus-portbacks.md`](../../../repos/archimedes/docs/research/archimedes-to-linus-portbacks.md)
in the Archimedes repo (authoritative bidirectional source).

> **Refresh shape (per Dan, 2026-05-23).** The original 2026-05-22 memo was a forward-looking
> proposal sandbox-blocked from reading the live repo. Many of its ideas have since shipped in
> Archimedes — often in different shapes than proposed. This refresh does three things in
> sequence: (1) a one-page snapshot of how the strategy engine actually shipped; (2) retrospective
> on the 5 original proposals against shipped reality with delta lessons; (3) 3 NEW forward
> proposals informed by current state, spine-plus-v2, the 2026-05-23 launch-execution-plan, and
> the Xia 2026 protocol-audit framing the team has folded in.

## How the strategy engine actually shipped (one page)

The strategy engine is a five-stage data flow with clearly separated services in
`backend/archimedes/services/`. End-to-end:

1. **Corpus** (`arxiv_corpus.py` CLI + the 3-layer manifest/DB/artifact substrate in
   `docs/corpus-architecture.md`) — 10,000 q-fin papers, metadata + abstracts in the DB; full
   text PDFs / SPECTER2 embeddings / KG / clusters are scaffolded but not yet served (Phase 3c
   skeleton; Issue #96 unblocked).
2. **Fusion** (`strategy_fusion.py`, ~650 lines, feature-flagged, DB-first) — user-steered
   `FusionBrief` (asset classes, risk profile, direction, paper budget) drives **deterministic
   pre-LLM candidate selection** via synonym-mapped substring filter + direction-keyword scored
   ranking + recency tiebreak. Hard floor of 2 papers (fewer = decline-honest). Objective is
   *novelty of the cross-paper combination* (McLean-Pontiff 2016 — post-publication alpha decays
   ~58%; the durable edge is in combinations the literature hasn't published yet). Anti-
   hallucination is enforced post-parse: any `arxiv_id` not in the candidate set is dropped.
   Phase 9 UI surface on `/generate` landed `5efe7c6` (2026-05-22) — fusion is no longer dead
   code in the product path.
3. **Architect** (`strategy_architect.py`) — selects + weights pre-curated library strategies
   (today: 5 hand-curated files + a buy-hold baseline). Feeds the construction-trace + on-chain
   reasoning-trace flow.
4. **Guardrail** (`strategy_guardrail.py`) — enforces constraints (USYC floor, max DD, asset
   universe, weight caps); emits a `GuardrailResult` carrying `strategy_weights`, `usyc_weight`,
   `dropped`, `adjustments`.
5. **Portfolio agent + rigor + trace** — `portfolio_agent.py` (~850 lines, LLM-driven) takes the
   weighting and picks individual instruments (global universe across US stocks, indices, FX,
   futures, crypto, bonds by maturity), anchors each pick to a paper-grounded strategy id, emits
   a tool-call trace. `selection_bias_routes.py` runs the four-control rigor battery (DSR / PBO
   / walk-forward OOS / look-ahead audit). `construction_trace.py` builds a `ReasoningTrace`,
   content-hashes via keccak256, hands off to `ITracePublisher.publish()` which anchors on the
   deployed `ReasoningTraceRegistry` on Arc. Two Tier-1 strategies pass the rigor gate against
   22 years of real SPY data today.

Per spine-plus-v2's locked decisions, the multi-strategy mechanic is "agent runs N candidates
internally, surfaces single best, rejects browsable" — externalized critique applied at the
user-facing boundary, not at the dispatch boundary. Vault semantics are locked as "time-bound
execution container holding 1 strategy + capital + window," with 1:1 strategy↔vault cardinality.

## Retrospective on the 2026-05-22 proposals

Each of the original five Linus-flavored design ideas, scored against shipped reality. Lesson
each proposal yields — useful both for Archimedes's next architecture decisions and for Linus's
import discipline.

### 1. A grounding gate for strategy claims

**Proposed (2026-05-22).** Port `RigorResult` / `RigorFailure` dataclasses verbatim from
Linus's `rigor.py` (DEC-0059). Implement exactly one check (`unattested_oos`) against a stub
OOS registry. Asymmetric severity (errors hard-block, warnings annotate). Smallest first
step: prove the gate-runs / severity-classifies / UI-renders substrate end-to-end.

**Shipped.** Real quant math, far beyond stub. The selection-bias gate exposes four controls
at `/api/selection-bias/gate`:

- **Deflated Sharpe Ratio** — Bailey & López de Prado 2014, equation 8 with the *raw* (Pearson)
  kurtosis convention (γ₄=3 for normal; explicit because passing Fisher excess would bias the
  denominator by `(3/4)·ŜR²`). Per-bar Sharpe, Euler-Mascheroni-corrected expected best-of-N
  under the iid normal null.
- **PBO via CSCV** — Bailey-Borwein-López-Prado-Zhu 2014 Combinatorially-Symmetric-Cross-
  Validation framework. Recently upgraded (Issue #138) to compute real PBO against a parameter-
  variant grid for fusion outputs.
- **Walk-forward OOS Sharpe** — explicit train/test split (default 0.70), `out_of_sample_sharpe`
  surfaced separately from in-sample.
- **AST static look-ahead audit** — `look_ahead_audit_passed: bool` from a static analyzer over
  the strategy code.

Gate semantics are **hard, not soft**: `passes_all = (DSR_p > threshold) ∧ (PBO < threshold) ∧
(OOS Sharpe stable) ∧ (look-ahead passed)` is the CANDIDATE → VALIDATED promotion criterion. Two
Tier-1 strategies pass today against 22 years of real SPY data (Faber 2007 SMA-200, Moreira-Muir
2017 vol-managed). Per Dan's own comparison, this is "the strongest single piece in either repo."

**Delta + lesson.** The smallest-first-step framing was *too cautious* for a team with Önder's
math + statistics expertise. The proposal correctly identified the gate shape but undersized the
team's capacity to ship real corrections in a hackathon week. **The lesson generalizes**: when a
proposal hands a substrate to a Worker, the "smallest first step" framing assumes the Worker
is *Linus's hosted-LLM-budget-constrained Worker*; a domain expert with the right priors will
land the substrate AND the first real check in one pass. Calibrate "smallest first step" to
the executor, not to the substrate.

**Forward (Linus-side).** Per Dan's `archimedes-to-linus-portbacks.md`: Linus's curation is the
*soft* DEC-0019 scorecard — fine for prose syntheses, *wrong for any Worker output that makes a
stakeable prediction or claim*. The Archimedes pattern (DSR/PBO/walk-forward generalize to "is
this measured effect real or multiple-testing noise?") is the single most reusable hard-
engineering asset in Archimedes for Linus to import. Target on Linus's side: extend
`src/linus/knowledge/rigor.py` with a quantitative-gate companion module (e.g.,
`rigor_quantitative.py`) for benchmark deltas, biology screen p-values, any predictive Worker
output. This is the Linus-import case Dan's own port-back doc already specifies.

### 2. Provenance-traced strategy reasoning

**Proposed (2026-05-22).** Define `StrategyStep(kind, payload, source, timestamp)` as the only
type the engine emits. Type-by-construction forecloses the "we'll add provenance later" failure
mode. Source field discipline: `market_data:<feed>@<asof>`, `prior_strategy:<run-id>`,
`assumption:<registry-id>`, `worker:<model>@<scratchpad-hash>`. Smallest first step: every
downstream component accepts and returns lists of `StrategyStep`.

**Shipped.** Substantially bigger than proposed. Schema lives in
[`docs/specs/strategy-passport-spec.md`](../../../repos/archimedes/docs/specs/strategy-passport-spec.md)
and is wired through five tables: extensions to `strategies` (paper identity + methodology hash
+ extraction LLM + curator wallet + on-chain registration tx), extensions to `backtest_results`
(paper-claimed metrics surfaced as deltas, backtest engine + code hash, walk-forward split, OOS
Sharpe, look-ahead audit), a new `reasoning_traces` table (decision type, trigger, market context,
reasoning text, action, expected outcome, strategies invoked, content hash, off-chain storage
pointer, on-chain anchor tx), `tool_call_provenance` (per-tool inputs + outputs hashed
separately), and `paper_corpus`. The `construction_trace.build_construction_trace()` function is
**pure and stops at the hash** — the hard seam between Dan's lane (assemble + hash) and Chuan's
lane (publish to chain) is enforced by module boundary. The keccak256 content_hash is anchored
on Arc via the deployed `ReasoningTraceRegistry`.

**Delta + lesson.** Type-by-construction discipline is present, but in a more powerful form than
the proposal envisioned: the on-chain anchor IS the type-by-construction enforcement. A trace
that can't recompute its hash fails *verification*, not just *type-checking* — and the failure
is third-party-detectable, not just compile-time. **The proposal had the right instinct (forcing
provenance into the type)** but under-imagined the enforcement layer. **The lesson**: when
external verifiability is available (chain, Merkle-anchor, timestamped notary), shifting
provenance enforcement from runtime types to externally-verifiable hashes is a strict upgrade.
Type-checking catches programmer mistakes; externally-verifiable hashes catch *anyone* who tries
to tamper post-hoc — including future you.

**Forward (Linus-side).** Per Dan's port-back doc: Linus has the better *internal* provenance
discipline (claim-typing `[!source]`/`[!analysis]`, SHA-256 content hashing, audit JSONL) but no
external verifiability. The Marelli accountability pillar wants externally-verifiable attribution
— Archimedes' pattern is the concrete mechanism. Target: `src/linus/memory/anchor.py` — a
Merkle-root notarization adapter (no chain required) that makes the audit/episodic record
externally tamper-evident. This is also a v0.6.0 seed (Q2 signed-audit-slice / R5-06) already
tracked in `docs/questions/top-questions.md`.

### 3. Multi-Worker generation with structured critique

**Proposed (2026-05-22).** Generate K parallel candidate strategies under varied priors
(feature emphasis, risk-aversion, lookback window). A separate critique Worker scores each
against a fixed rubric (rigor-gate pass, OOS attestation, assumption set explicit, conflict
with prior staked positions). Smallest first step: K=2, two Workers + one critique.

**Shipped (differently).** The pattern that landed is **sequential**, not parallel:
`strategy_architect → strategy_guardrail → construction_trace → rigor gate`. The architect
proposes weights against the curated library; the guardrail enforces constraints; the rigor
gate is the externalized "critique" — but it runs on the OUTPUT, not on parallel candidates.

A *closer* shape to the proposal landed in two places:

1. The `portfolio_agent.py` LLM-driven layer: K=1 (single LLM call picks individual instruments,
   anchored to library strategies). Plus a `_RESPONSE_CACHE` with 5-min TTL so repeat requests
   don't re-hit the LLM.
2. The spine-plus-v2 locked decision: "agent runs N candidates internally, surfaces single best,
   rejects browsable." This is the K=N proposal applied at the user-facing boundary (the user
   sees winner + rejects-with-reasoning), not at the dispatch boundary.

**Delta + lesson.** The K parallel Workers pattern is the right shape for *compute-constrained*
Workers (Linus's 32 GB M1 Max + local Ollama). It is the *wrong* shape for *budget-constrained*
hosted-LLM Workers (Archimedes' Anthropic-via-GLM). The hosted-LLM economics make K=1 plus a
strong externalized gate (rigor!) the better fit. **The lesson generalizes**: the cost surface
of the Worker determines whether K-parallel-fanout is the right pattern. Map it deliberately,
not by analogy from the host-of-origin's economics.

**Forward (cross-project).** Spine-plus-v2's "agent runs N internally, surfaces best, shows
rejects" is the K=N applied at the human-facing boundary — a strict upgrade over both Linus's
internal divergence-check (which never surfaces to the user) and the original memo's K=2 (which
hides nothing but loses the comparative-evidence UI). Linus's `agents/spawner.py` could adopt
the "show rejects with reasoning" pattern when surfacing parallel agent outputs to humans;
it currently returns a winner without explaining what was considered.

### 4. Network-policy declaration for data-fetching actions

**Proposed (2026-05-22).** Adopt DEC-0061 verbatim — per-tool `network_policy` literal type
(`offline` / `online_optional` / `online_required`), captured in audit log's `network_egress[]`,
surfaced in `/healthz`. Smallest first step: one `online_optional` data-fetcher with local-cache
fallback.

**Not shipped in Archimedes.** No `network_policy` field on tools; no `network_egress[]` on
traces; no per-tool reachability surfaced in `/health`. **But a closely-shaped pattern did
ship at a different boundary**: the `LLMBackend` Protocol + `CannedBackend` deterministic
fallback + `/health` reporting `llm_backend: live|canned`. Honest degradation at the LLM-
backend level; honest *served-model capture* (the actual `response.model` rather than the
requested model) per Dan's own comparison.

**Delta + lesson.** Archimedes adopted the *spirit* (degrade loudly, never silently fall back)
but not the *granularity* (per-tool declaration). For Archimedes' current egress catalogue
(market-data fetchers, Circle SDK, USYC oracle, Anthropic/GLM, arXiv) the LLM-level signal was
"good enough" for hackathon scope, and per-tool declaration would have been overhead the team
didn't pay for. **The lesson**: granularity should match the consumer. Linus's per-tool
discipline serves a multi-Worker auditing surface; Archimedes' per-backend discipline serves
a deployed-product operator surface. Both are correct for their use case.

**Forward (bidirectional).**

- *Linus → Archimedes*: as Archimedes' egress catalogue grows post-reveal (more data vendors,
  exchanges, news feeds for the strategy library), the per-tool framework gets cheaper to
  retrofit early than late. The reference shape is `src/linus/tools/registry.py` +
  `network_policy` kwarg + the `entity_ncbi.lookup` instance (PR #113).
- *Archimedes → Linus*: lift the `LLMBackend Protocol + CannedBackend deterministic fallback +
  served-model-honesty` pattern back. Linus has `src/linus/server.py` routing OpenAI + Anthropic
  compat but lacks the clean canned-fallback + served-model-versus-requested-model honesty layer.
  This is a small, high-signal port.

### 5. Loud-degradation health surface

**Proposed (2026-05-22).** Adopt DEC-0060's `/healthz` extension: `effective_state ∈ {live,
degraded, down}` + `degradations[]` list of `{component, expected, actual, severity,
remediation}`. The `remediation` field is **actionable** — a specific command/env-var, not "check
your config." Smallest first step: one `_compute_degradations()` function with two detection
modes.

**Shipped (differently).** Archimedes' `/health` is richer in *content* but flatter in
*structure*. It reports: `llm_backend: live|canned`, `corpus_db_count`, `paper_count`,
`artifact_built_at`, contract addresses on Arc, oracle status. Closer to a status dump than to
DEC-0060's structured degradations list with per-component severity + actionable remediation.

**Delta + lesson.** Both shapes are valid for different consumers. Linus's structured
`degradations[]` is built for UI surfacing + alerting + LLM-readable reasoning ("the system told
me VECTOR_BACKEND is down, here's the fix"). Archimedes' status-dump is built for *operator
inspection* — the human runner SSH'd into EC2 wants every key fact in one place, not nested
inside a list with a severity enum. **The lesson**: the shape of the degradation signal should
follow its consumer. Picking the wrong shape (LLM-readable when humans consume it; flat-dump
when LLMs consume it) is a strictly-worse failure than picking either correctly.

**Forward.** When Archimedes adds programmatic consumers of `/health` (alerting, agent runner
self-recovery, judge-facing rubric scrapers), the structured `degradations[]` shape will start
to pay for itself. The right time to add it is when the second programmatic consumer ships.
Until then, the operator-facing dump is the right call.

## New forward proposals (informed by current state)

Three Linus-flavored ideas that the 2026-05-22 memo couldn't have proposed because they emerge
specifically from where Archimedes is *now* — informed by spine-plus-v2, by the 2026-05-23
launch-execution-plan's 5-layer-memory-pillar framing, by Xia et al. 2026's protocol-audit
framing, and by Dan's own comparison doc's "compounding-substrate" insight (its central
strategic critique of Archimedes).

### A. Memory-as-substrate for the compounding strategy library

**The problem (from Dan's own comparison).** Archimedes' real moat — on-chain provenance — is
being applied to a *non-compounding* asset. The strategy library is 5 hand-curated files; each
user request starts from zero; nothing compounds. The architect's reasoning isn't stored as
recallable, citation-typed knowledge; the fusion module's hypotheses aren't accreted into a
self-curating substrate; the rigor gate's *rejections* aren't stored as "considered but rejected"
evidence the way the spine-plus-v2 user-stories doc envisions. The North Star promises a
"compounding strategy library" — the implementation doesn't deliver it yet.

**The Linus pattern that fits.** The five-layer memory pillar (DEC-0028), specifically Layer C
(cross-session episodic — SQLite + content hashes + git, DEC-0029). Layer C is the substrate
that makes the strategy library *grow and self-curate*. Every architect proposal, every fusion
hypothesis, every rigor-gate verdict, every regime-shift decision becomes a claim-typed,
content-hashed, audited record that *future* requests retrieve and build on. The launch-
execution-plan already explicitly references this lineage ("5-layer pillar — Linus lineage +
Xia refinement").

**Smallest first step.** `backend/archimedes/services/strategy_memory.py` — SQLite-backed
episodic store of strategy proposals + verdicts. Schema lifts DEC-0029's
`(session_id, turn_id, parent_turn_id, segment, content_hash, content, trust_level, tags)`
shape but renames to Archimedes vocabulary (`generation_id, proposal_id, parent_proposal_id,
verdict_segment, content_hash, content, trust_level=rigor_pass|rigor_fail|user_rejected,
tags`). Pair with the existing on-chain `ReasoningTraceRegistry` so the Layer-C SHA chain ↔
ReasoningTrace hash relationship is explicit (the chain is the externalization of Layer C).

**What it changes about the pitch.** Reframes the moat from *"this 4-strategy library is
verified"* (a static claim) to *"our verified-knowledge substrate compounds and every increment
is provenance-anchored"* (a generative claim defensible in a way a static list isn't). This is
the structure-first-then-productize sequencing the entrepreneurship-synthesis derives from the
g10-finance prior art.

### B. Wire paper-qa as the retrieval/synthesis engine behind a RAG gateway

**The problem (from Dan's own comparison).** Fusion's candidate selection is keyword/synonym/
direction-keyword scoring — no embeddings, no rerank, no RRF, no contextual-summary loop. The
fusion module's own docstring admits "a SPECTER2 ranker is a clean post-hackathon swap behind
this same seam." Today's "research-grounded" claim is grounded in *abstracts + keyword filters*,
not paper bodies + embeddings.

**The Linus pattern that fits.** paper-qa (DEC-0044) is integrated in Linus as
`src/linus/knowledge/paperqa.py` and exposes four MCP tools (search, gather_evidence, answer,
reset). The rigor gate auto-runs inside `paperqa.answer` (DEC-0059 amendment). Apache 2.0,
st-embeddings (no API key required), single-tool integration. This is the substrate Archimedes'
fusion engine wants.

**Smallest first step.** `backend/archimedes/services/paper_rag.py` — wraps `paper-qa.Docs`
against the 10k-paper corpus. Wire into `strategy_fusion._select_candidates()` as an *additional*
ranker behind the existing keyword filter (defense-in-depth — keyword + semantic — beats either
alone). Per the existing fusion-spec seam, this is a behind-the-seam swap.

**Two-step second move.** Once paper-qa is wired, make `paper-rag` *also* callable as a tool by
the `portfolio_agent` LLM. Then the agent can iteratively look up specific papers during
portfolio construction ("this pick needs more evidence — what does the literature say about
volatility-managed equities in late-cycle?") rather than getting one static corpus injection at
prompt-build time.

### C. Cross-project bridge realized — Linus as a sibling-callable substrate

**The problem.** The original bridge spec (`docs/specs/linus-archimedes-bridge.md`, 2026-05-19)
proposed Archimedes lifting Linus's `papers.ingest_arxiv`, `KnowledgeRetriever`, and
`spawn_agents` tools. Reality: Archimedes built its own (`arxiv_corpus.py`, `strategy_provider`,
no spawner) because the Linus tools weren't sufficiently HTTP-callable or integrated at the time.
The bridge spec is now stale.

**The Linus-side opening.** Linus now serves both `/v1/chat/completions` (OpenAI) and
`/v1/messages` (Anthropic) plus `POST /v1/tools/{name}/invoke` (direct tool invocation, PR #98).
Linus's tool registry exposes paper-qa, KB tools, and the entity grounding chain as MCP-style
callable surfaces. Linus runs on configurable port (PR #127, `LINUS_SERVER_URL` env var).
Archimedes can now treat Linus as a sibling HTTP-callable substrate — without lifting code.

**Smallest first step.** A `linus-archimedes-bridge-v2` adapter: Archimedes' `paper_rag.py`
defaults to local paper-qa computation but can be configured (via `ARCHIMEDES_PAPERQA_BACKEND =
linus | local`) to delegate to Linus's `POST /v1/tools/paperqa.answer/invoke`. Same shape; one
flag flips the substrate. Side benefit: Linus's KB-derived entity grounding becomes available to
Archimedes' fusion engine for free.

**What it changes about the architecture.** Recasts Linus's role from "personal substrate that
shares patterns with Archimedes" to "sibling service Archimedes can outsource paper-intelligence
to when configured." Doesn't require Archimedes to depend on Linus; doesn't require Linus to be
deployed alongside; just makes the integration possible when the operator wants it. This is the
g6-mcp-tools / harness-vs-orchestration thesis applied to the cross-project boundary: the
orchestration layer (Linus) accrues value; the harnesses (Archimedes' Streamlit-equivalent
React UI, the strategy engine) can call into it without coupling.

## Open questions for Dan (refreshed)

1. **Compounding-substrate ambition for v0.5.0 reveal vs v0.5.1.** Proposal A (Layer C memory
   for the strategy library) is the highest-leverage architectural move per your own comparison
   doc, but it's a non-trivial new module — `strategy_memory.py` with schema design, write paths
   from architect/fusion/rigor/regime, ORM, tests, plus the conceptual reframing of "library as
   directory" to "library as substrate." Is this an in-scope post-reveal item (v0.6.0 / Spine+
   v3) or does even the *framing* (in the README, in the demo) belong in the reveal narrative —
   "we ship the substrate today, compounding lands next"?

2. **Where on the spectrum sits the rigor gate as Linus-importable artifact.** Per the port-back
   doc the case for porting to Linus is clear, but the *form* on the Linus side has at least two
   shapes: (a) a sibling-to-rigor.py module (`rigor_quantitative.py`) for any quantitative
   Worker output, or (b) a new tool exposed through the MCP registry so any client (including
   Archimedes via Proposal C) can invoke DSR/PBO/walk-forward against an arbitrary returns
   series. Tool-exposure is harder but more reusable. Which gets prioritized?

3. **The Xia 2026 protocol-audit fold-in (Outcome Embargo / Time-Aware Retrieval / Hierarchy
   of Truth / Source Tracking / V_check contract) in the 2026-05-23 launch-execution-plan.** I
   read the section headers but not the details. Are any of these named protocols *Linus-side*
   import candidates, or are they Archimedes-specific because they assume backtest-grade
   temporal discipline? The "Outcome Embargo" pattern sounds especially generalizable — separate
   the moment a prediction is *made* from the moment its outcome is *observed* — but it might
   already be in Linus's design vocabulary under different names (it's adjacent to the commit-
   reveal-trace spec Dan referenced for v1.5).

4. **The 5 hand-curated strategies as the library floor — bridge to LLM-extracted strategies.**
   Today the served library is 5 files; arxiv extraction is demo-only via
   `IStrategyProvider.extract_from_paper()` with no HTTP route. The roadmap presumably goes
   through (a) reach 10-20 hand-curated, then (b) LLM-extracted candidates pass through the
   rigor gate before admission. At what corpus-coverage point does (b) become the primary
   admission path rather than the demo path? And: does the curator wallet signature stay
   load-bearing (each LLM-extracted candidate still needs Dan's wallet) or relax to algorithmic
   admission once the rigor gate is calibrated enough to be trustworthy alone?

5. **Provenance-anchor reciprocity.** Per Proposal C, the cleanest bridge is "Archimedes can
   call Linus's paper-qa via tool-invoke." But the *deepest* cross-project pattern would be
   reciprocal: Linus calls Archimedes' rigor gate as an external service when any Linus tool
   produces a quantitative prediction. That requires Archimedes' rigor gate to be a callable
   tool with stable inputs (returns series + selection-set size + paper claims) — possible but
   non-trivial. Worth specifying as a Phase 7 cross-tool primitive, or premature?

6. **What's deliberately out of scope here.** Same standing question as the original memo: if a
   Linus-flavored idea is wrong for Archimedes — domain mismatch, team-structure mismatch,
   performance-budget mismatch — which one, and why? Across both the retrospective and the new
   proposals, where the patterns I describe are the wrong import for Archimedes, the most
   valuable signal back is which one you'd cut and what you'd put in its place.
