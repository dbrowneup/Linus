# docs/audits/

Dated audit batches. Each batch addresses a specific question against the corpus at a point in time, surfaces
findings, and recommends remediation. Audits are preserved for the durable record even after their suggestions are
applied — the audit is the receipt for the resulting change.

## Convention

Per CLAUDE.md doc-type conventions, an audit is `<batch-name>/<source>-audit.md` with sections:

- `## Summary`
- `## Findings` (H3 sub-categories by severity/class)
- `## Remediation recommendations (priority order)`
- `## Confidence assessment`

Some reveal-prep audits diverge from this shape when the author's structure better serves the actionable communication
inside a tight window; those are flagged in their batch README.

## Batches

- [`citation-traceability-2026-05-05/`](citation-traceability-2026-05-05/) — the canonical-shape audit. Validates
  citation chains across paper-notes ↔ syntheses ↔ landscapes.
- [`2026-05-22-reveal-prep/`](2026-05-22-reveal-prep/) — four reports produced ahead of the v0.5.0 public reveal:
  ROADMAP audit, doc-consistency audit, question audit, Archimedes orient.
- `2026-05-18-core-doc-alignment.md` — top-level alignment audit between core docs (CLAUDE.md / VISION.md / ROADMAP.md /
  ARCHITECTURE.md / SAFETY.md / DECISIONS.md / GLOSSARY.md).
- `2026-05-18-repo-pull-status.md` (+ `.txt`) — repo-pull verification (which submodules + cloned repos drifted since
  the prior pull).
