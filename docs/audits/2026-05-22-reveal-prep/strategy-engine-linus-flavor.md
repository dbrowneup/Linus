# Strategy engine — a Linus-flavored design lens

**Date:** 2026-05-22 **Author:** Maestro (Claude Code), for Dan **Audience:** Dan, as input to his own Archimedes
strategy-engine ownership work — not a replacement for it.

> Note on sourcing: `repos/archimedes/` reads were blocked at the permission layer in this session, so this memo grounds
> on what DEC-0059 / DEC-0060 / DEC-0061 already encode about the 2026-05-19 Archimedes cross-pollination (Deflated
> Sharpe Ratio, CSCV, walk-forward OOS, /health degradation, "stakeable" outputs) plus Linus's own architecture. If Dan
> wants the memo refreshed against the actual Archimedes repo, lifting the read-permission and re-running takes minutes.

## Reading of the problem

A "strategy engine" converts a goal, context, and candidate action space into a recommended plan whose recommendation
is _stakeable_ in the DEC-0059 sense: the team will act on it, allocate capital or attention against it, and pay a
real cost if it's wrong. From the Archimedes signals already encoded in Linus's ADRs (quant-style rigor checks,
walk-forward OOS, a health endpoint distinguishing canned vs. live), the strategy engine operates where the bar is
"produce a defensible recommendation under scrutiny," not "complete the user's sentence." Accountability surface
matters more than prose surface.

The Linus lens is direct: a strategy engine is a Worker that emits a stakeable artifact, and Linus has spent the last
quarter answering exactly "how do we make stakeable Worker artifacts trustworthy without giving up speed or
local-first character?" Same shape, different domain. The memo below proposes five concrete patterns lifted from that
work, each scoped to a smallest first step.

## Linus-flavored design ideas

### 1. A grounding gate for strategy claims (rigor.py for strategies)

**What it borrows from Linus.** `src/linus/knowledge/rigor.py` (DEC-0059) gates synthesis output: citations must
resolve, entities must lookup, cross-run divergence drops calibrated confidence. The gate is a pure function with a
stable signature; new checks compose via `check_all` rather than refactoring the orchestrator. Severity is asymmetric —
citations hard-error, entities warn — because that asymmetry reflects the asymmetric cost of each fabrication mode.

**What's new for strategy.** A strategy claim isn't grounded by a `paper_id`; it's grounded by an evidence backbone:
prior runs of the same setup, the data window the recommendation rests on, assumptions made explicit ("transaction
cost ≤ X bps," "regime = trend"). A `check_strategy_grounding(claim, evidence, prior_runs)` exposes: (a) every cited
evidence handle resolves in the data store, (b) every assumption appears in a known-vocabulary registry, (c) the
recommendation has at least one walk-forward OOS attestation. Failures classify Linus-style: `error` for missing data
or unattested OOS; `warning` for unrecognized assumptions or single-run histories.

**Tradeoffs.** Adds latency and creates a refusal path the UI has to handle. Worth it for the same reason Linus took
the hit — a refused recommendation is much cheaper than a staked-and-wrong one. Asymmetric-severity discipline keeps
it from becoming a tarpit; most failures only annotate.

**Smallest first step.** Port the `RigorResult` / `RigorFailure` dataclasses verbatim. Implement exactly one check
(`unattested_oos`) against a stub OOS registry. The end-to-end shape (gate-runs, severity-classifies, UI-renders)
exercises in an afternoon and proves the substrate before any second check ships.

### 2. Provenance-traced strategy reasoning (every step retains its source)

**What it borrows from Linus.** paper-qa's `citation_to_provenance` shape (`{"paper_id", "page", "excerpt", "score"}`)
makes every synthesis step traceable to a PDF passage. The KB entity backend (DEC-0059 amendment) goes further: each
resolved entity carries a `source` field like `"kb:<sha256-prefix-of-graphml>"` so the lookup chain traces back to the
exact KG version. Provenance isn't a UI feature; it's a data-structure invariant.

**What's new for strategy.** Each step in a strategy's reasoning chain (signal extraction → feature transform →
hypothesis → backtest → recommendation) gets a `source` field with the same discipline: `"market_data:<feed>@<asof>"`,
`"prior_strategy:<run-id>"`, `"assumption:<registry-id>"`, `"worker:<model>@<scratchpad-hash>"`. The provenance string
is the cheap audit primitive — if a recommendation later proves wrong, it makes the post-mortem mechanical instead of
forensic.

**Tradeoffs.** Discipline tax on every step that emits an artifact. The Linus pattern is to make the wrapping types
carry it by construction so it can't be omitted by accident — a step without provenance fails type-checking, not
just runtime checks.

**Smallest first step.** Define `StrategyStep(kind, payload, source, timestamp)` as the only type the engine emits.
Every downstream component (backtester, scorer, recommender) accepts and returns lists of these. Type-by-construction
forecloses the "we'll add provenance later" failure mode that bit DEC-0019's input surface.

### 3. Multi-Worker strategy generation with structured critique (Maestro/Worker for strategies)

**What it borrows from Linus.** Maestro/Worker discipline plus DEC-0059's confidence-divergence check: spawn N Worker
runs of the same query, compare via Jaccard over rationale tokens and cited evidence, fold divergence into calibrated
confidence. Divergence is information, not failure. Spec-first dispatch keeps Workers cheap and Maestro attention
expensive.

**What's new for strategy.** Generate K candidate strategies in parallel under varied priors (feature emphasis,
risk-aversion, lookback window). A critique Worker — separate dispatch — scores each against a fixed rubric (rigor-gate
pass, OOS attestation present, assumption set explicit, conflict with prior staked positions). The Maestro layer
picks the winner and surfaces critiqued losers as "alternatives considered." This generalizes The Algorithm's "delete
every possible step" to strategy candidates: the discarded ones are the evidence the chosen one earned its keep.

**Tradeoffs.** K× the inference budget. On 32 GB M1 Max this caps at 3-5 qwen3:8b dispatches; in Archimedes the
ceiling is different (likely higher), which changes K but not the pattern.

**Smallest first step.** K=2: two Workers, one critique. The shape generalizes to N without code change. The 2026-05-18
wave-2 fanout's "probe permissions first with a canary" discipline applies — a K=1 dry-run before any parallel
dispatch.

### 4. Network-policy declaration for data-fetching strategy actions

**What it borrows from Linus.** DEC-0061's three-value `network_policy` (`offline` / `online_optional` /
`online_required`), per-tool declared at registration, captured in the audit log's `network_egress[]` field, surfaced
in `/healthz` reachability checks. Every external call is a trust decision reviewed at design time, not a runtime
surprise.

**What's new for strategy.** A strategy engine pulling market data, scraping a filing, hitting a pricing API, or
querying a counterparty system is structurally the same as `entity_ncbi.py` reaching NCBI Gene: an opt-in network
action that declares posture, logs host + query hash + response size, and degrades gracefully when offline. Archimedes
probably has a richer egress catalogue than Linus (data vendors, exchanges, news), which makes per-tool declaration
more important, not less. Three-layer accountability (author declares, reviewer checks, audit records) carries over
verbatim.

**Tradeoffs.** Discipline overhead at registration and audit-log plumbing. The flip side: every external dependency
is documented at design time, every call is auditable post-hoc, and an offline run produces a documented degraded
artifact instead of a silent failure.

**Smallest first step.** Define the `network_policy` literal type and audit-log field shape verbatim from DEC-0061.
Add a reachability check pointed at the engine's most-critical external host. One `online_optional` data-fetcher
with a local-cache fallback exercises the whole substrate end-to-end.

### 5. Loud-degradation health surface for the strategy engine

**What it borrows from Linus.** DEC-0060's `/healthz` extension with `effective_state ∈ {live, degraded, down}` and a
`degradations[]` list of `{component, expected, actual, severity, remediation}`. The `remediation` field is
**actionable** — a specific command or env-var, not "check your config." Additive: pre-existing keys keep their
semantics.

**What's new for strategy.** A strategy engine has more failure modes than a chat server: stale data feed, model
fall-through (preferred forecaster missing), assumption-registry drift, OOS-window expiry, risk-limit override. Each
is operationally costly when silent. A `/strategy/health` endpoint with the same shape gives downstream consumers (UI,
scheduler, risk system) a canonical alerting signal. The warning-vs-error distinction is load-bearing: a stale feed
might still produce a defensible recommendation; an expired OOS window cannot.

**Tradeoffs.** One more endpoint to maintain. Worth it the moment a stale state would cost real money or attention —
which on a strategy engine is approximately always.

**Smallest first step.** One `_compute_degradations()`-style function with two detection modes (stale data, missing
forecaster), targeting DEC-0060's 22-test hermetic coverage discipline. UI surfacing is cheap once the endpoint
exists.

## Open questions for Dan

1. **Stakeable definition.** Does the Archimedes team have an explicit stakeable-output threshold (a confidence floor,
   a rigor-pass requirement) before a strategy is actionable, or is it still informal? The grounding-gate analog only
   works if there's a clear hard-vs-soft severity classification you can defend; DEC-0059's "citations error, entities
   warn" asymmetry came from a real cost-of-failure asymmetry.

2. **Provenance vocabulary scope.** What's the smallest set of source-kinds for strategy steps — market-data feeds,
   prior strategies, assumption registry, model + scratchpad hash? Locking the vocabulary early keeps the
   `StrategyStep.source` field interpretable; letting it grow ad-hoc loses the audit affordance.

3. **K for the multi-Worker fanout.** Given the Archimedes inference budget (local vs. hosted, allowed wall-clock per
   generation), what's the natural K? Linus's 32 GB constraint puts K in 2-5; Archimedes might be wider, which drives
   whether the critique loop is one critic or a fan-in.

4. **Network egress catalogue.** Which external hosts does the engine touch, and which are `online_required` (refuse
   offline) vs. `online_optional` (degrade-cached)? An `online_required` strategy action is stronger than in Linus —
   refusing to recommend because a feed is down may be exactly right, or may itself be the worst outcome.

5. **Health-surface consumer + gate-enforcement boundary.** Who consumes `/strategy/health` (UI, risk system,
   scheduler, on-call human)? That shapes whether `effective_state` needs three values or finer-grained, and whether
   `remediation` is a command string or structured action. Relatedly: do you want the rigor gate informational at the
   answer-payload boundary (DEC-0059 amendment's choice — faster to ship, learn false-positive rate, harden later) or
   hard-enforced at the orchestration boundary from day one?

6. **What's deliberately out of scope.** If a Linus-flavored idea here is wrong for Archimedes — domain mismatch,
   team-structure mismatch, performance-budget mismatch — which one, and why? Patterns travel well because Linus and
   strategy engines share the stakeable-artifact shape, but "shape match" isn't "fit." Where Linus's pattern is the
   wrong import, the most valuable signal back is which idea you'd cut and what you'd put in its place.
