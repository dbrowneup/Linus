# docs/specs/

Living implementation specs — the durable form of "here's what we agreed to build, and how." Specs are handed off to
Workers (or to Maestro for direct implementation) and updated when execution surfaces gaps. Once a spec's
implementation has shipped and stabilized, the spec may stay (as an artefact of the decision) or be retired into the
ADR layer.

## Spec families

**Implementation plans** — the largest-scope specs, often spanning multiple phases:

- `2026-05-12-linus-implementation-plan.md` and `2026-05-17-linus-implementation-plan-v2.md` — Phase 2a/2b plans;
  v2 carries the still-open follow-ups (N6-derived F-tier items, D-series design ADRs).
- `2026-05-19-kb-hackathon-prep.md` — the spec that drove the 2026-05-19 → 2026-05-21 reveal-prep arc.
- `2026-05-19-mvp-build.md` — the MVP-build spec for Phase 2a closure.

**Architectural-pillar specs:**

- [`memory-architecture.md`](memory-architecture.md) — the five-layer memory pillar implementation contract
  (DEC-0028).
- [`phase1c-spike.md`](phase1c-spike.md) — Phase 1c memory-pillar spike scope.
- [`phase3-spawner.md`](phase3-spawner.md) — the agent-spawner spec (DEC-0050 / DEC-0051).
- [`phase6d-streaming-target.md`](phase6d-streaming-target.md) — flash-streaming inference target.

**Workflow + bridge specs:**

- [`manuscript-polish-workflow.md`](manuscript-polish-workflow.md) — Dan's PhD-draft workflow that the grounding gate
  serves.
- [`linus-archimedes-bridge.md`](linus-archimedes-bridge.md) — Linus ↔ Archimedes integration contract.

**v0.6.0 seeded specs:**

- [`2026-05-21-env-architecture-layered.md`](2026-05-21-env-architecture-layered.md) — Option C env layering.
- [`2026-05-21-kb-hardcoded-paths-fix.md`](2026-05-21-kb-hardcoded-paths-fix.md) — KB portability fix.

**Fan-out + cleanup specs:**

- `notes-consistency-fanout.md`, `synthesis-cleanup-spec.md`, `synthesis-refinement-spec.md`, `2026-05-09-context-foldin-fanout.md`, `2026-05-10-pr30-cleanup-spec.md`, `2026-05-16-awesome-papers-gap-triage.md`, `2026-05-18-synthesis-coverage-audit.md` — each drove a specific multi-PR arc.

**Other:**

- [`question-lifecycle.md`](question-lifecycle.md) — the question-lifecycle process formalization (see
  [`../questions/`](../questions/)).
- [`biology-phase7-roadmap.md`](biology-phase7-roadmap.md) — Phase 7 biology-skill roadmap.
- [`qimeng-category-promotion.md`](qimeng-category-promotion.md) — promotion criteria from the qimeng synthesis.
- [`planning-update-spec.md`](planning-update-spec.md) — the canonical planning-update spec template.
- [`kb/`](kb/) — KnowledgeBase-specific specs.
