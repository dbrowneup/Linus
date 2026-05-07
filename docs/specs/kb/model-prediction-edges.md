# KnowledgeBase model_prediction Edge Class

**Date:** 2026-05-06 **Status:** proposed **Phase:** 2 (schema spec) / 3 (write-back implementation) **Related ADR:**
DEC-0048

---

## Goal

Define the `model_prediction` edge class for the KnowledgeBase schema (DEC-0015) so that model-derived content written
by biological foundation model skills (Phase 7) is auditable, diffable, and staleness-detectable from the moment the
first skill writes back. The schema must be committed before any Group A Wave 1 skill writes to the KB.

---

## Edge class schema

A `model_prediction` edge is a sub-type of the general KnowledgeBase provenance edge. It inherits all base-edge fields
and adds the following required fields:

| Field | Type | Description |
| --- | --- | --- |
| `producing_model` | string | Model identifier and version, e.g., `"bacformer-v1.2"` or `"qwen3-14b"` |
| `confidence` | float or null | Model-reported confidence in [0.0, 1.0]; `null` if the model does not report calibrated confidence |
| `content_hash` | string | SHA-256 of the input context passed to the model to generate this prediction — enables staleness detection if source data is updated |
| `timestamp` | string | ISO-8601 datetime of prediction |
| `biosecurity_tier` | string or null | `"A"`, `"B"`, or `"C"` for biology predictions as defined in DEC-0047; `null` for non-biology predictions |

All five fields are required at write time. A `model_prediction` edge record missing any field is rejected by the KB
schema validator.

---

## Default claim tag

All `model_prediction` edges carry the `[!unverified]` claim tag from DEC-0023 by default. This tag is applied
automatically at write time and cannot be suppressed by the writing Worker. It signals to any downstream consumer —
human or automated — that the content has not been independently verified and should be treated as a hypothesis, not an
established fact.

An individual prediction may be promoted to `[!analysis]` (model-mediated inference that has been reviewed and is
considered plausible) or `[!source]` (verified against a primary source) by Dan after manual review. Promotions are
logged as separate audit events with the reviewer identity and timestamp. A model-generated prediction may never
self-promote: only a human reviewer or a designated critic-eligible Worker acting on behalf of a human review step may
change the claim tag.

Stale predictions — where the `content_hash` no longer matches the current content of the source entity — surface as
`[!gap]` candidates during the KB lint pass and are flagged for re-prediction or removal.

---

## Write-back contract

Workers write model predictions as `model_prediction` edges, never as direct assertions. A Worker that has predicted a
functional annotation for a gene does not add that annotation directly to the KB's assertion layer. Instead, it creates
a `model_prediction` edge from the prediction context to the predicted claim, populated with all five required fields.
The claim is then visible in the KB as a pending prediction awaiting review.

Maestro or a designated critic-eligible Worker (as defined in DEC-0050 and DEC-0051) is responsible for promoting a
prediction to assertion after review. The promotion step requires an explicit audit log entry. There is no implicit or
background promotion path.

This contract means the KB's assertion layer remains a curated set of human-or-critic-reviewed claims, while the
`model_prediction` layer accumulates the raw outputs of foundation model skill runs. The two layers are structurally
distinct and queryable independently.

---

## Relationship to existing edge classes

The `model_prediction` edge is a sub-type of the general provenance edge defined in DEC-0015. The base provenance edge
records source, target, relationship type, and timestamp. The `model_prediction` sub-type adds `producing_model`,
`confidence`, `content_hash`, and `biosecurity_tier` — fields that are specific to model-generated content and
meaningless for edges derived directly from literature or human curation. Existing provenance edges are unaffected.

The `model_prediction` edge class is not a replacement for the `[!source]` / `[!analysis]` / `[!unverified]` / `[!gap]`
claim-type taxonomy from DEC-0023. The claim-type taxonomy operates at the text layer and is visible to human readers
scanning KB content. The `model_prediction` edge operates at the graph layer and carries machine-queryable provenance
metadata. Both systems apply simultaneously to model-derived content: the text carries `[!unverified]`; the edge
carries the producing-model fields.

---

## Concrete example

A bioSkills function-annotation Worker runs on BRCA1 using a biology foundation model and predicts that BRCA1 is
involved in DNA repair at confidence 0.87. The write-back creates a `model_prediction` edge with the following fields:

```json
{
  "producing_model": "bacformer-v1.2",
  "confidence": 0.87,
  "content_hash": "sha256:a3f8c2...",
  "timestamp": "2026-05-06T15:04:00Z",
  "biosecurity_tier": "A"
}
```

The predicted claim — `BRCA1 → involved_in → DNA_repair` — appears in the KB as `[!unverified]`. It is visible to
subsequent Workers and to Dan, but it is not treated as an established fact by any retrieval or synthesis step that
filters on claim type. Dan or a critic-eligible Worker reviews the prediction against the primary literature; if the
review is positive, the claim is promoted to `[!source]` with an audit log entry, and the `[!unverified]` tag is
replaced. If the source content that produced the prediction is later updated, the `content_hash` mismatch surfaces the
prediction as a `[!gap]` candidate, prompting re-evaluation.

---

## Phase sequencing

The `model_prediction` schema definition is a Phase 2 deliverable (spec only). The write-back implementation — the
tooling that allows biology skill Workers to create `model_prediction` edges — is a Phase 3 deliverable, sequenced
after the KB graph substrate (DEC-0015) is live and after the spawner (Phase 3) exists to coordinate multi-Worker skill
runs. The schema must be committed to the KnowledgeBase repo before Phase 7 Group A Wave 1 skills are activated.
