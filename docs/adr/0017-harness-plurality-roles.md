## DEC-0017 — Harness plurality maintained through Phase 5 with explicit role designations

**Date:** 2026-05-03
**Status:** accepted

**Context.** Linus has four candidate front-ends (Claude Code, cline, claw-code-local,
openclaw). The "converge to one" answer is empirical and depends on Dan's actual
usage; the *intent* shapes Phase 5 budget and per-harness investment.

**Decision.** Maintain plurality through Phase 5. Explicit role designations:
Claude Code = hosted Maestro (no convergence pressure; different layer); cline =
primary VS Code Worker harness; claw-code-local = primary terminal local-model
Worker harness; openclaw = Phase 5 chat/voice/canvas/mobile UI. **No per-harness
gold-plating** beyond "configure to point at Linus's endpoint and make it work." If
one proves dominant by Phase 6, naturally let it absorb the others' use cases.

**Consequence.** Each harness gets minimum-viable integration; Linus's endpoint
(OpenAI-compatible, MCP-shape tool registry) is the surface they all consume.
Convergence is observable, not engineered.
