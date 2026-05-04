## DEC-0011 — Lightweight branching now (Phase 0–2), graduated gitflow at Phase 3+

**Date:** 2026-04-24 **Status:** accepted

**Context.** Linus needs a git branching model that enables safe, auditable, parallel agentic development. The classical
Driessen gitflow model (`master`, `develop`, `feature/*`, `release/*`, `hotfix/*`) is powerful for managing versioned
releases, but Linus is pre-v1.0 with no production releases or explicit versioning yet. Adopting the full model now
would add ceremony without immediate value.

**Decision.** Use a lightweight branching model through Phase 2:

- `main` is the single long-lived integration branch (always code-reviewed)
- Feature branches (`feature/*`), agent branches (`agent/<task-id>/<slug>`), and fix branches (`fix/*`) branch from and
  PR back to `main`
- Experiments (`experiment/*`, `spike/*`) are ephemeral and not merged
- All changes to `main` require PR review by Dan before merge
- No `develop`, `release/*`, or `hotfix/*` branches yet

At Phase 3 (when Linus has versioned releases and needs release-branch discipline), graduate to full Driessen gitflow:
introduce `develop` as the integration point, branch features from `develop`, create `release/*` and `hotfix/*` for
release management, and tag releases on `main`.

**Consequence.** Lower overhead now (no unused ceremony), while preserving a clear migration path to gitflow when
releases matter. The spec-driven Maestro/Worker protocol naturally works with this model: Workers always branch and open
PRs, Maestro reviews and merges. The lightweight model keeps parallel task execution simple without a separate
integration branch. The branching model is fully documented in BRANCHING.md, the Maestro/Worker protocol in
docs/maestro-worker-protocol.md, and branch safety rules integrated into SAFETY.md and CLAUDE.md's tool use policy.
