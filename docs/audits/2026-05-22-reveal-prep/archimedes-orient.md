# Archimedes orient — refreshed 2026-05-23

> **Refresh note (2026-05-23).** Original (2026-05-22) was sandbox-blocked from reading
> `repos/archimedes/` and was grounded on in-tree priors from 2026-05-12 → 2026-05-14 plus
> the v1 bridge spec. This refresh is sourced from the live repo (~340 commits since 2026-05-12,
> Day 11 of the hackathon arc) plus Dan's own source-verified
> [`docs/research/linus-archimedes-comparison.md`](../../../repos/archimedes/docs/research/linus-archimedes-comparison.md)
> in the Archimedes repo. The bidirectional comparison is authoritative there; this Linus-side
> orient stays Linus-perspective and complements rather than mirrors it.

## What Archimedes is (one paragraph, refreshed)

Archimedes is an autonomous portfolio agent that turns peer-reviewed quantitative-finance research
into investable, backtested, rigor-gated strategies, executed into non-custodial vaults on the Arc
testnet with USDC settlement and every decision step hashed + anchored on-chain. A user describes
intent in plain English; Archimedes fuses that brief with the current live market regime and a
~10,000-paper q-fin research library; produces a candidate strategy spec; gates it through four
selection-bias controls (Deflated Sharpe Ratio, Probability of Backtest Overfitting via CSCV,
walk-forward out-of-sample Sharpe, look-ahead audit); deploys it into a non-custodial vault; and
surfaces every reasoning step on-chain via the deployed `ReasoningTraceRegistry`. The README's
explicit self-framing is now **"Linus for quantitative finance"** — the research-grounded
substrate (corpus + rigor + provenance) is the product, specialized to one domain, made
externally verifiable, shipped to live testnet.

## What's actually deployed (Day 11 reality, sourced from the live repo)

The product surface that exists today, on the EC2 host at `13.40.112.220` and on the Arc public
testnet (Chain ID `5042002`, where "USDC *is* gas"):

- **10 Solidity contracts on Arc testnet**: `AMMPool`, `AMMRouter`, `AssetRegistry`,
  `PriceOracle`, `ReasoningTraceRegistry`, `SyntheticFactory`, `SyntheticToken`, `SyntheticVault`,
  `Vault`, `VaultFactory`. ABIs cached in `contracts/abis/` for backend + UI consumption.
- **6-service docker-compose stack** running on EC2: FastAPI backend, PostgreSQL 16, Redis 7,
  nginx, Circle-signed oracle runner, agent runner. CI/CD via GitHub Actions; every merge to
  `main` triggers build + deploy (build-on-deploy as the canonical workflow).
- **A 3-input fusion engine** (`POST /api/strategies/generate`, landed via PR #95 + Phase 9 UI
  surface in `5efe7c6`): user brief × live market regime × 10,000-paper q-fin corpus → grounded
  strategy spec, with per-call paper citations carried into the prompt.
- **A four-control selection-bias rigor gate**, wired at `/api/selection-bias/gate` and exercised
  as the CANDIDATE → VALIDATED admission filter. Real math (not stub): Bailey & López de Prado
  2014 DSR with raw-kurtosis correction, Bailey-Borwein-López-Zhu 2014 CSCV PBO, walk-forward
  OOS Sharpe with explicit train/test split, AST-based static look-ahead audit. **2 Tier-1
  strategies pass today** against 22 years of real SPY data (Faber 2007 SMA-200, Moreira-Muir
  2017 vol-managed).
- **An LLM-driven portfolio agent** (`backend/archimedes/services/portfolio_agent.py`, 850 lines)
  that picks *individual instruments* — not just ETFs — across a global universe (US stocks,
  global indices, FX including USD/TRY, futures, crypto, bonds by maturity), anchors each
  position to one of the paper-grounded library strategies, and emits a tool-call trace.
- **A strategy DSL** (`backend/archimedes/services/strategy_dsl.py` +
  `dsl_to_backtrader.py`) that compiles strategy specs to backtrader runners. Recently validated
  end-to-end: DSL-Faber matches hand-written Faber within ±0.10 Sharpe on real SPY data (Issue #139).
- **A multi-asset NAV vault** — `Vault.totalAssets()` prices all synthetic holdings via oracles;
  the rebalance path goes through `strategy_architect` → `strategy_guardrail` → on-chain action.
- **A 10,000-paper q-fin corpus** in a 3-layer substrate per `docs/corpus-architecture.md`:
  Layer 1 (manifest.jsonl committed seed, 14 MB), Layer 2 (Postgres `papers` table — the actual
  query target), Layer 3 (persistent docker volume for heavy artifacts — embeddings, KG —
  scaffolded but not yet built since Phase 3c skeleton).
- **A two-tier marketplace framing**: **Tier 1 (Archimedes Verified 🏆)** = paper-grounded +
  selection-bias-corrected + full agent autonomy. **Tier 2 (Community 👥)** = permissionless,
  opt-in agent features. Per `docs/specs/ecosystem-design-spec.md`.
- **Test coverage**: 302 backend tests + 16 analytics-engine tests green.
- **Provider-agnostic LLM backend** (`backend/archimedes/services/llm_backend.py`): the
  `LLMBackend` Protocol with `ClaudeBackend` (Anthropic SDK; also GLM via `ANTHROPIC_BASE_URL`
  override) and `CannedBackend` deterministic fallback. `/health` reports
  `llm_backend: live|canned` so silent failure is impossible.

The technology stack landed differently from the original orient's hypothesis: it's **React 19 +
Vite 8 + viem 2.48 (plain CSS)** on the frontend (NOT Next.js + TailwindCSS), **backtrader** for
backtesting (decided over vectorbt per a documented ADR — vectorbt is a v2 problem if parameter-
sweep speed becomes a constraint), and **provider-agnostic LLM** with GLM-via-z.ai as the primary
in-hackathon backend rather than Claude-only. The CLAUDE.md framing has stabilized as
build-on-deploy main-only — every merge ships to the live EC2 stack and the agentic `t2o2` system
self-iterates on CI failures directly on `main`.

## The strategy engine subsystem (Dan's lane, refreshed)

The strategy engine is the upstream of every Archimedes-verified claim — the paper-to-passport
pipeline. As shipped today it is a five-stage data flow with clearly separated services:

1. **Corpus** — `backend/archimedes/services/arxiv_corpus.py` (CLI-only ingester, recency-biased
   multi-category scraper, sha256 content-addressed PDF+text cache, idempotent) + the 3-layer
   manifest/DB/artifact substrate documented above. **Caveat per Dan's comparison doc**: the
   in-tree manifest is *metadata-and-abstract-only*; cached full-text PDFs and a SPECTER2
   embeddings index are not yet in the served path (Issue #96, unblocked but not landed).
   Today's "research-grounded" claim is grounded in **abstracts**, not paper bodies.

2. **Fusion** — `backend/archimedes/services/strategy_fusion.py` (650 lines, feature-flagged,
   DB-first reads with file fallback). User-steered by construction via a `FusionBrief`
   (`asset_classes`, `risk_appetite`, `strategic_direction`, `max_papers ∈ [2, 6]`); candidate
   selection is **deterministic and pre-LLM** — synonym-mapped substring filter + direction-
   keyword scored ranking + recency tiebreak — so the model never sees the full corpus and
   cannot silently widen the candidate set. Anti-hallucination: post-parse, any `arxiv_id` not
   in the candidate set is dropped (mirroring the architect's `strategy_id` discipline).
   Objective: **novelty** (under the McLean-Pontiff 2016 finding that post-publication alpha
   decays ~58% — the durable edge is in combinations the literature has not yet published).
   The Phase 9 fusion UI surface on `/generate` landed via `5efe7c6` (2026-05-22), promoting
   fusion from previously-dead-code (per Dan's own comparison; `strategy_fusion` was reachable
   only from `/health` until very recently) to a live user path.

3. **Architect** — `backend/archimedes/services/strategy_architect.py` (curated-library
   selector). Feeds the construction-trace + on-chain reasoning-trace data flow. Picks and
   weights *pre-curated, paper-grounded* library strategies; anti-hallucinates dropped unknown
   `strategy_id`s. The library today is 5 hand-curated files in `analytics-engine/strategies/`:
   `faber_2007_sma200_timing.py`, `moreira_muir_2017_volatility_managed.py`,
   `moskowitz_ooi_pedersen_2012_tsmom.py`, `george_hwang_2004_52w_high.py`,
   `capital_preservation_tbill.py`, plus a `pipeline_buy_hold.py` baseline.

4. **Guardrail + portfolio agent** — `strategy_guardrail.py` enforces constraints (USYC floor,
   max DD, asset universe, weight caps); `portfolio_agent.py` is the LLM-driven layer that
   takes the architect's weighting and picks specific instruments + emits a tool-call trace
   (`AgentToolCall` records: tool name, inputs, output summary). Per spine-plus-v2's locked
   decisions, the **multi-strategy mechanic** is "agent runs N candidates internally, surfaces
   single best, rejects browsable" — externalized critique applied at the user-facing boundary.

5. **Rigor gate + construction trace** — `selection_bias_routes.py` runs the four-control
   battery; `construction_trace.py` assembles a `ReasoningTrace` (decision type, trigger,
   market context, reasoning text, action taken, expected outcome, strategies invoked,
   `tool_call_provenance` per call, `content_hash` via keccak256, off-chain storage pointer,
   on-chain anchor tx). The trace publisher hands off to Chuan/Marten's `ITracePublisher.publish()`
   which anchors the hash on the deployed `ReasoningTraceRegistry`. A pending Day-3 upgrade
   (commit-reveal trace spec) strengthens "trace existed at T" to "trace existed *before* the
   trade" with proven causal ordering — wiring through is v1.5.

Dan owns this whole pipeline; Önder backs portfolio-math + risk-pricing.

## Public release posture (refreshed)

- **What's live and public**: GitHub at the canonical org (the README cites
  `github.com/hackagora/archimedes-arcadia`; the local clone's git remote shows
  `a-apin/archimedes-arcadia`, likely a personal mirror — Dan to confirm if these need
  reconciliation before reveal). EC2 deploy at `13.40.112.220`. The Agora Hackathon page
  (`luma.com/7i50p2r9`). Arc testnet is the settlement chain.
- **What's newly revealed at the 2026-05-25 Agora hackathon**: the working MVP — strategy
  engine, portfolio agent, on-chain reasoning-trace registry on Arc, the paper → strategy →
  portfolio → settlement demo, the 10,000-paper Corpus Explorer, the Tier-1-passing rigor
  verdicts. This is coordinated with Linus + KnowledgeBase's reveal as the "three repos, one
  lineage" launch wave (per `docs/launch-plan.md` + `docs/specs/launch-execution-plan-2026-05-23.md`).
- **The honest framing is the brand**: Arc has *no mainnet* — testnet-only, faucet USDC (20 USDC
  / 2h), no real funds at risk by design. Overclaiming would destroy the credibility wedge the
  whole product is built on. "AI can be wrong; the goal is to win more than you lose, not never
  lose." See `docs/launch-plan.md` § 1.
- **Canonical naming**: project name "Archimedes"; repo name `archimedes-arcadia`; team
  Discord server "Archimedes Arcadia". License is the Unlicense (full public-domain dedication).
- **Arc OSS Showcase** is the next post-reveal positioning surface
  (`ARC-OSS-SHOWCASE.md` + `ARC-OSS-FORM-DRAFT.md`); the showcase write-up frames Archimedes as
  forkable Arc-aligned primitives for the broader ecosystem, separate from the hackathon judging
  surface.

## Cross-project messaging suggestions (refreshed sentences for Linus's README)

Three sentences that hold up against the current Day-11 reality:

1. *"Archimedes ([`hackagora/archimedes-arcadia`](https://github.com/hackagora/archimedes-arcadia))
   is the entrepreneurial sibling project debuting alongside Linus at the Agora Agents Hackathon
   — a research-grounded portfolio agent settled in USDC on the Arc testnet, where every strategy
   passes a four-control selection-bias rigor gate (DSR, PBO, walk-forward OOS, look-ahead audit)
   and every reasoning step is hashed and anchored on-chain via the deployed
   `ReasoningTraceRegistry` contract."*

2. *"Where Linus is the general personal research-intelligence substrate, Archimedes is what that
   substrate looks like specialized to one domain (quantitative finance), made externally
   verifiable (on-chain anchored reasoning traces), and shipped to live testnet. The patterns
   transferred — sha256 content-addressed caching, injectable LLM-backend seams, honest
   labelled fallbacks, the Maestro/Worker discipline — and the gaps Archimedes deferred
   (paper-qa-backed semantic retrieval, the KB knowledge graph, a memory layer for the
   compounding strategy library) are exactly the next-wave bridges between the two."*

3. *"The bidirectional architecture comparison and the concrete port-back list live in the
   Archimedes repo at
   [`docs/research/linus-archimedes-comparison.md`](https://github.com/hackagora/archimedes-arcadia/blob/main/docs/research/linus-archimedes-comparison.md)
   and [`docs/research/archimedes-to-linus-portbacks.md`](https://github.com/hackagora/archimedes-arcadia/blob/main/docs/research/archimedes-to-linus-portbacks.md)
   — those are the authoritative sources for what each project would lift from the other."*

The existing reveal-context blockquote in Linus's root README is on-message and lands well after
PR #123's Archimedes URL update.

## What's still uncertain at reveal time (honest list)

- **The `hackagora` vs `a-apin` repo-URL discrepancy.** README + CLAUDE.md cite
  `github.com/hackagora/archimedes-arcadia`; the local git remote shows
  `github.com/a-apin/archimedes-arcadia`. May be a personal mirror, an org rename, or a stale
  CLAUDE.md. Worth confirming before any link goes into Linus's public README.
- **Whether the Phase 3c KB integration body lands before reveal.** Spec is in place
  (`docs/specs/kb-integration-spec.md`); skeleton scaffolded; full SPECTER2 + HDBSCAN/BERTopic
  + REBEL/SciSpacy pipeline run on the 10k corpus is the load-bearing missing piece for
  semantic retrieval. Without it the "research-grounded" claim is grounded in abstracts +
  keyword filters, not paper bodies + embeddings.
- **Whether `commit-reveal-trace` lands before reveal** to strengthen "trace existed at T" to
  "trace existed *before* the trade" with provable causal ordering.
- **Whether the team wants Linus's README to name Chuan / Önder / Marten / Daniel R. as
  collaborators** or to keep the cross-reference repo-level only. The README's Team section
  + the CLAUDE.md table already list them publicly; Linus's README mentioning them is consistent
  but should be Dan's call.
- **Whether "Archimedes Verified 🏆"** is a final brand mark or a working-title.
- **Domain + TLS** for Archimedes (per `docs/launch-plan.md` § 4) — a bare EC2 IP reads as
  "unfinished" to operator-judges; a domain + HTTPS is the single highest-ROI polish item
  before the public push. Status pending.
