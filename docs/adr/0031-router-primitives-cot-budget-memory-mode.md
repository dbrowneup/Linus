## DEC-0031 — Router primitives: per-call CoT budget and per-call memory mode

**Date:** 2026-05-03
**Status:** accepted

**Context.** The Merrill & Sabharwal complexity-class regimes
([2310.07923](../paper-notes/2310.07923v5.md): logarithmic / linear /
polynomial scratchpad steps map to L / regular-language-class / P upper
bounds) and the Feng et al. constructive results
([2305.15408](../paper-notes/2305.15408v5.md): chain-of-thought raises
effective depth proportional to generation length) make the per-call
reasoning-token budget a *formal* handle on what kind of problem the Worker
is being asked to solve. Uniform budgeting either underspends on
algorithmic tasks (collapsing them back toward TC0) or overspends on
lookup tasks (burning tokens for no expressivity gain). Separately,
DEC-0029's substrate decision is dispatch-time-meaningless without a
mechanism that says *which* memory layers should be loaded as prefix for a
given call — without that mechanism, every Worker call either pays the full
episodic-prefix cost or gets none, and the o1 anti-pattern (DEC-0030)
reappears as a loading-side decision rather than a retention-side one.

**Decision.** Two new first-class router primitives in Phase 2:

**Primitive 1 — `cot_budget`.** Three named regimes with v0 token caps
grounded in the Merrill & Sabharwal complexity classes:

- `logarithmic` — default 256 reasoning tokens, truncate-on-cap,
  retention-best-effort. Right for lookup-shaped tasks (extraction,
  classification, single-fact retrieval).
- `linear` — default 4096 reasoning tokens, full retention required. Right
  for inherently sequential algorithmic tasks (math, dependency
  resolution, multi-step planning, code reasoning over more than one
  file). Phase 2 default for any task the router cannot classify
  confidently — the formal results say erring high on this knob is the
  right asymmetry.
- `polynomial` — default 16384 reasoning tokens, full retention required,
  explicit confirmation gate before dispatch (this regime is expensive).
  Phase 2 has no automatic dispatch into this regime; explicit caller
  request only.

The cap numbers are *defaults*, not invariants. The DEC-0033 per-Worker
CoT-gap fingerprint feeds per-Worker calibration: the router consults the
model registry for per-Worker overrides.

**Primitive 2 — `memory_mode`.** Three values determining which memory
layers are loaded as prefix before dispatch:

- `stateless` — no episodic prefix, no scratchpad continuity expected. The
  Worker sees only the current task spec + KB context relevant to it
  (Layer D only, retrieved fresh).
- `session_stateful` — current session's scratchpad and answer history
  (Layers B + D) loaded as prefix. The Worker can reference its own prior
  turns within this task. Default for multi-turn coding work, iterative
  analysis, conversational interactions.
- `project_stateful` — current session + relevant prior-session episodic
  records (Layers B + C + D), retrieved by project tag and CRISPR-style
  temporal weighting (recent ranked higher, ancient retrievable on
  demand).

Population priority: (1) explicit caller specification, (2) skill
definition's declared memory mode (Phase 7+), (3) Phase 2 v0 heuristic
based on session continuity (fresh session with no prior project tag →
`stateless` or `session_stateful`; session resuming an existing project
tag → `project_stateful`).

**Composition.** The two primitives compose with existing Worker-selection
axes (model size, capability tags including `scratchpad_durability` from
DEC-0030, task-completion-time profile from the Speed paper). The dispatch
decision is a function over `(task_spec, cot_budget, memory_mode,
available_workers)`. The router refuses impossible combinations
(`project_stateful` with a `non_conformant` Worker per DEC-0030 is a
non-conformance error).

**Telemetry.** Both primitives recorded per dispatch in the audit log so
Phase 1c+ benchmarks can correlate budget/mode with outcome quality,
completion time, and cost.

**Phase 2 scope.** Primitives are router *signals* — dispatch logic reads
them, audit log records them, episodic-store retrieval respects
`memory_mode`. *Automatic classification* of incoming tasks into regimes
is Phase 3+ work; explicit caller annotation is the v0 fallback.

**Consequence.** Cheap to add now; expensive to retrofit later. Every
downstream consumer (logging, benchmarking, skill registry, eventual task
classifier) assumes the primitives exist. Phase 2 callers must annotate
explicitly until Phase 3 ships an auto-classifier; this is acceptable
friction in exchange for the architecture being right from the start.
Reversal cost is high — the dispatch struct, audit-log shape, and
episodic-store retrieval contract all hinge on these signals.
