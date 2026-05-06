## DEC-0048 — KnowledgeBase model_prediction edge class with provenance [KB-spec]

**Date:** 2026-05-06 **Status:** accepted

**Context.** Biological foundation model skills (Bacformer, LucaOne, BioReason-Pro, ESM3, etc.) will write
model-derived predictions back to the KnowledgeBase in Phase 7. Without a typed distinction between model-derived
assertions and source-derived claims, the KB becomes a credibility-indeterminate store: human-verified literature
claims and model-generated predictions are structurally identical and indistinguishable post-hoc. The claim-typing rule
(DEC-0023: `[!source]` / `[!analysis]` / `[!unverified]` / `[!gap]`) handles text-layer differentiation but does not
capture the provenance chain needed to know which model, at which version, produced a given prediction. Closes **S6**.

**Decision.** Add a `model_prediction` edge class to the KnowledgeBase schema (defined in DEC-0015). Required fields:

- `producing_model` (string: model identifier + version, e.g., `"bacformer-v1.2"`)
- `confidence` (float 0.0–1.0, model-reported; `null` if the model does not report calibrated confidence)
- `content_hash` (SHA-256 of the input context passed to the model to generate this prediction — enables staleness
  detection if source data is later updated)
- `timestamp` (ISO-8601 datetime of prediction)

All `model_prediction` edges inherit the `[!unverified]` claim-type tag from DEC-0023 by default. Dan may upgrade an
individual prediction to `[!analysis]` or `[!source]` after manual review; upgrades are logged. Stale predictions
(content_hash no longer matches current source content) surface as `[!gap]` candidates in the KB lint pass (hyalo,
DEC-0026 integration). The `model_prediction` edge class must be present in the KnowledgeBase schema **before** any
Group A Wave 1 skills start writing back.

**Consequence.** Model-derived KB content is auditable, diffable, and staleness-detectable. The schema commitment is
Phase 2 (spec only); write-back implementation is Phase 3. KnowledgeBase integrity is preserved as the biology pillar
scales.
