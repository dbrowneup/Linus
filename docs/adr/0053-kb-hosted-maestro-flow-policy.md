## DEC-0053 — KB → hosted-Maestro flow policy: hosted-ok / hosted-forbidden binary

**Date:** 2026-05-06 **Status:** accepted

**Context.** The safety-alignment-privacy synthesis and S16 identify a gap: KB content flows to Workers, but some
Workers (critic-tier, hosted-Maestro fallback) may be backed by hosted Claude. No policy currently governs which KB
content may be included in a prefix sent to a hosted model. Dan confirmed 2026-05-06: hosted-ok / hosted-forbidden
binary is the right shape; no middle category; LanzaTech proprietary data and financial data are never KB candidates.
Closes **S16**.

**Decision.** KB content is tagged at ingest time with one of two flow categories:

- **`hosted-ok`**: published papers, public reference databases (NCBI, UniProt, PDB), public ontologies (GO, HPO),
  public genomics corpora. These may appear in prefixes sent to hosted-Maestro Workers (hosted Claude in the
  critic-tier or hosted-Maestro fallback role).
- **`hosted-forbidden`**: Dan's personal notes (`context/notes/`), draft writing, financial records, LanzaTech
  proprietary data, private correspondence, and any content not already in the public domain. These are never included
  in prefixes sent to hosted models. The orchestrator enforces this at query time: `hosted-forbidden` items are stripped
  from any prefix assembly targeting a hosted-Maestro Worker, regardless of retrieval ranking.

**Implementation.** The KB ingest pipeline (Phase 3) adds a `flow_category` field to every ingested record, defaulting
to `hosted-forbidden`. Records must be explicitly tagged `hosted-ok` at ingest time; the conservative default limits
blast radius from mis-classified content. The `flow_category` field is immutable after ingest; reclassification
requires a manual migration with audit-log entry. No override mechanism exists at query time.

**No opt-in friction at query time.** The category boundary is set at ingest, not at query time. The orchestrator
applies the filter automatically; Workers and callers cannot request `hosted-forbidden` content for a hosted-model
prefix.

**Consequence.** Dan's private knowledge (notes, drafts, financial data, company-confidential data) is architecturally
excluded from hosted-model exposure. The binary is enforced at the substrate level (ingest tagging + query-time strip),
not by convention or caller discipline. Phase 2 note: the flow policy is architectural at Phase 2; KB write-back is
Phase 3, so the full ingest pipeline is a Phase 3 implementation target.
