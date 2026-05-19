## DEC-0059 — Grounding gate at the OUTPUT surface: hard admission for stakeable Worker outputs

**Date:** 2026-05-19 **Status:** accepted

**Context.** Linus is increasingly asked to produce stakeable artifacts — manuscript-ready paragraphs, citation-rich
synthesis answers, structured biology predictions — where a fabricated citation or hallucinated entity is materially
worse than a refused answer. Workers can and do fabricate: a 7–14B local model under a tight CoT budget will sometimes
emit a plausible-looking paper_id that doesn't exist in the KB, or name a gene that isn't a real symbol. The 2026-05-19
Archimedes cross-pollination conversation surfaced this problem directly: in the quant world, every backtested strategy
gets a Deflated Sharpe Ratio audit before being staked; Linus has no equivalent for staked synthesis output.

DEC-0019 (KB ingest quality surface) addressed quality at the **INPUT** surface and intentionally chose NOT to gate —
Dan is the primary filter; everything already on his machine has passed his download decision; hard gating would lose
signal he's already vetted. That decision is correct at the input surface; it does not generalize to the output surface.
Workers are not Dan. A fabricated citation appearing in an answer was never on Dan's machine; the input gate cannot have
caught it. Different surface, different policy.

**Decision.** Add a **hard admission gate at the OUTPUT surface**: `src/linus/knowledge/rigor.py`, exposing
`check_grounding(claim, papers, entities, prior_runs) -> RigorResult`. The gate runs three baseline checks on every
stakeable Worker output before it reaches the user or lands in a manuscript draft.

1. **Citation grounding.** Every cited `paper_id` must resolve in the KB metadata DB. Cited `page` (when provided) must
   be within the paper's `page_count`. Failures are `error`-severity — the gate refuses the answer.

2. **Entity grounding.** Every named biological entity (gene, protein, ontology term) must resolve in a reference store.
   v0.5.0 ships a stub `BuiltinEntityLookup` seeded with a small set of well-known entities (BRCA1, TP53, EGFR, …) so
   the end-to-end shape is exercisable without external lookups or network. **Unresolved entities are
   `warning`-severity, not `error`** — the stub backend explicitly says "flag, don't block." Real backends (NCBI Gene,
   UniProt, GO ontology) ship post-reveal and may re-promote this to error.

3. **Confidence calibration.** When the audit log (per DEC-0030 / DEC-0031) records multiple Worker runs of the same
   query, compare them via a Jaccard average over rationale token bags and cited paper sets. Substantial divergence
   produces a `confidence_divergence` warning and reduces the calibrated confidence proportionally. Empty / single-run
   prior histories produce no warning and a `calibration=None`. Divergence is information, never a hard error.

The gate composition surface is `check_grounding` for the v0.5.0 baseline and `check_all(claim, checks=[...])` for
arbitrary post-reveal additions. The result type `RigorResult(passed, failures, confidence_calibration, extras)` carries
the verdict, the detailed failure list (with `kind`, `detail`, `severity`, and `target`), the calibrated confidence
where estimable, and per-check telemetry.

**Stub-entity-backend-with-warning-not-error semantics.** Why warning rather than error for unresolved entities, when
the citation surface uses error? Two reasons. First, the v0.5.0 entity backend is a hand-seeded stub by necessity — we
cannot block stakeable output on a backend that knows ten entities when the real catalog is millions. Second, entity
fabrication is harder to commit than citation fabrication: a Worker that says "EGFR signaling" is much more likely to be
talking about the real EGFR than a Worker that says "paper-id sha_xyz123" is referring to a real paper. The asymmetric
severity reflects the asymmetric risk. Once real entity backends ship, the warning may be promoted to error in a
follow-up ADR.

**Extension points (post-reveal, NOT v0.5.0 scope).** The 2026-05-19 Archimedes conversation surfaced two adjacent
surfaces where the same gate shape applies. The module is structured so each is an **additive plug-in**, not a refactor:

- **Time-series-aware checks on scientific longitudinal data.** Many biological/chemical measurements are time-series
  (growth curves, sequencing campaigns, treatment trajectories). A look-ahead audit — verifying that every cited source
  predates the claim's `asof_date` — is the same shape as the baseline checks. Function:
  `check_temporal_grounding(claim, asof_date) -> RigorResult`.

- **Archimedes-style quantitative rigor on entrepreneurial-surface outputs.** When Linus produces a strategy claim on
  the entrepreneurial surface (yield model, market sizing, pricing curve), the same Deflated Sharpe Ratio,
  Combinatorially-Symmetric Cross-Validation, and walk-forward out-of-sample checks apply. Function:
  `check_quantitative_overfitting(strategy_claim) -> RigorResult`.

Each extension is a separate pure function with the same return shape, composed via `check_all`. Adding one is the size
of a new function plus a new test — not a refactor of the orchestrator. The baseline `check_grounding` signature stays
stable across post-reveal additions.

**Consequence.** Workers can no longer silently fabricate citations or out-of-range pages in stakeable output — the gate
refuses such claims at the orchestration boundary. Hallucinated entities surface as visible warnings to the user and
Maestro, without blocking the conversation. Cross-run divergence becomes a calibrated, audit-loggable signal rather than
an invisible footgun.

The v0.5.0 ship is intentionally narrow: three checks, one stub backend, one ADR. Promotion of the entity check to
error-severity, real NCBI/UniProt/GO backends, and the post-reveal time-series + quant-overfitting checks are deferred
work — they extend the surface without modifying it. The DEC-0019 input-surface scorecard remains unchanged and
complementary: ingest scores material; rigor.py scores synthesis.

**References.**

- [DEC-0019](0019-kb-ingest-quality-surface.md) — KB ingest quality surface (the INPUT-surface counterpart).
- [DEC-0023](0023-output-interface-citations-llm-wiki.md) — Citation + claim-categories interface (the shape rigor
  consumes).
- [DEC-0030](0030-scratchpad-first-class-artifact.md) — Scratchpad as first-class durable artifact (the audit log
  prior-runs come from).
- [DEC-0031](0031-router-primitives-cot-budget-memory-mode.md) — Router primitives recording memory_mode and cot_budget
  per Worker call (the audit log carrier).
- CLAUDE.md §"Typed structured prediction for biology skills" (S25, the BioReason-Pro shape).
- Source: `src/linus/knowledge/rigor.py`; tests at `src/linus/tests/test_rigor.py`.
