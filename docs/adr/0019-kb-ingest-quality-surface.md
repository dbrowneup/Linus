## DEC-0019 — KB ingest quality gate as a quality surface, not a hard gate

**Date:** 2026-05-03 **Status:** accepted

**Context.** The LLM wiki synthesis recommends an auditable YAML editorial policy at KB ingest. The naïve framing was
hard accept/reject filtering — but Dan is the primary filter (everything already on his machine has passed his download
decision). Hard gating risks losing signal already vetted by him.

**Decision.** Adopt the YAML-policy framework as a **quality surface**, not a hard gate. Phase 2 ships YAML-policy +
scoring engine + per-paper quality scorecard surfaced in chat UI / RAG context (the model sees the score and signals
when retrieving). Domain-agnostic baseline signals: peer-review status, preprint flag, data/code availability,
retraction status, RaKUn keyphrase coverage, citation/age signals. **No hard reject lane in Phase 2**; preprints flagged
(`preprint: true`), not auto-rejected. FineWeb-style known-good/known-bad statistical calibration is Phase 3 learning
exercise. **[KB-spec]** item.

**Consequence.** No content lost to over-eager gating. Quality information flows to retrieval and to Maestro for
review-time judgment. Phase 3 calibration teaches the methodology rigorously without blocking Phase 2 ingest.
