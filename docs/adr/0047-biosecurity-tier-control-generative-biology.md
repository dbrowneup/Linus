## DEC-0047 — SAFETY.md three-tier biosecurity policy for generative whole-genome design

**Date:** 2026-05-06 **Status:** accepted

**Context.** The generative-biology synthesis (`docs/syntheses/generative-biology-synthesis.md`) identifies three tiers
of biological artifact generation with meaningfully different risk profiles: residue-level, gene-level, and
whole-genome. The synthesis recommends writing the tier-control policy now, before Phase 7 creates pressure to retrofit
it under time pressure. Cheap to specify now; expensive to debate under delivery pressure. Closes **S5**.

**Decision.** SAFETY.md gains a three-tier biosecurity section:

- **Tier A — Residue-level** (protein sequences, short RNA oligos, enzyme variant scoring, protein–protein docking
  outputs). Standard sandbox policy applies. No pre-authorization required per invocation. Tools in this tier:
  BioReason-Pro residue predictions, ESM3 sequence generation, RiNALMo structure prediction, Horizyn-1 enzyme
  discovery outputs.

- **Tier B — Gene-level** (synthetic gene design, regulatory element synthesis, BGC-to-SMILES routes, operon design,
  codon-optimization of novel sequences). Requires explicit Dan sign-off per invocation, logged in the audit trail.
  Tool is not agentic-executable without sign-off; Workers surface the proposed sequence and wait for approval before
  any downstream action. Tools in this tier: DeepSeMS BGC→SMILES, Bacformer gene-level generation calls.

- **Tier C — Whole-genome** (whole-genome design, large-scale genome synthesis routes, insertion of multiple
  functional regions). Requires explicit Dan sign-off plus out-of-band review (e.g., re-reading the proposed output and
  confirming in a separate session). Not agentic-executable; must be Maestro-reviewed and manually approved per
  invocation. Tools in this tier: AlphaGenome (whole-genome variant effects), Evo 2 (whole-genome generative calls).
  Evo 2 nucleotide generation above 100 kb is Tier C by default.

The three tiers are named in tool registry entries (the `biosecurity_tier` field, `null` for non-biology tools). The
audit log records the tier for every invocation that touches Tier B or C.

**Consequence.** Phase 7 biology skills launch with biosecurity tiers pre-defined rather than retrofitted. The tier
assignment is in the tool registry (static, reviewable by Dan), not in runtime logic. Future tool additions default to
Tier A unless explicitly upgraded; the conservative default limits blast radius from new tools being mis-classified.
