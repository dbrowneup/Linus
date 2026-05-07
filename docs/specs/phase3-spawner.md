# Phase 3 Agent Spawner — Design Intent

**Date:** 2026-05-06 **Status:** design intent stub **Owner:** Dan **Phase:** 3 (full spec written at Phase 3 planning
time)

**Related ADRs:** DEC-0050 (Role type), DEC-0051 (AgentReport), DEC-0052 (investigation memory); answered-questions
S9, S10, S13, S14, S15, S56

---

> **Scope note.** This is a design intent stub, not an implementation spec. Its purpose is to record the key
> architectural decisions so they are findable and don't have to be re-derived at Phase 3 planning time. The full
> implementation spec is a Maestro task to be written when Phase 3 begins.

---

## Goal and scope

The Phase 3 spawner enables `linus.agent.spawn(spec, roles)` — it fans a parent task into N Workers with typed
communication and shared state. Full task-decomposition primitives (PRD→tasks, parallel terminal patterns) are adopted
as skills in the skill registry rather than re-implemented here (DEC-0020). The spawner handles lifecycle, dispatch,
and result aggregation; it does not embed task-decomposition logic.

## Role type (DEC-0050)

A `Role` is a dataclass with `role_id`, `capability_set`, `memory_access_tier`, and `critic_eligible`. It is
serializable as JSON or YAML and stored in the Worker registry. Example roles: `researcher` (broad KB access, not
critic-eligible), `critic` (narrow output access, critic-eligible), `writer` (synthesis only, no raw retrieval). Role
definitions are configured per-investigation, not globally.

## AgentReport (DEC-0051)

The typed inter-agent message format. Fields: `task_id`, `role_id`, `status` (`complete` / `partial` / `blocked` /
`error`), `result`, `rationale` (only free-text field), `evidence`, `timestamp`. `status: "partial"` is explicitly
valid — a Worker that completes 80% of a task usefully before hitting a blocker should not be silenced.

## Validation-gate primitive (S15)

The spawner's validation gate is a quality surface (did the Worker produce output that is good enough?), distinct from
sandbox enforcement (the Worker tried to do something it cannot do). The fixer-agent pattern handles quality failures:
execute → detect quality shortfall → spawn a fix Worker → resubmit. Sandbox failures surface immediately to Maestro
and do not enter the fixer loop.

## Critic-tier policy (S14)

Workers with `critic_eligible: true` trigger a call to the current Maestro-tier model (hosted Claude now; Linus-Maestro
at Phase 8b). Critic calls are expensive and should be used only at plateau points — when the spawner's own quality
gate cannot resolve a disagreement or when the task requires judgment beyond Worker capability.

## Investigation memory (DEC-0052)

The spawner creates a Layer D investigation memory store at fan-out and closes it on completion, archiving the
investigation record to Layer C (cross-session episodic). This means parallel Workers share a scoped investigation
context without polluting the permanent episodic store.

## Key open question for Phase 3 planning

**Dynamic tool activation (S56 / E3):** whether per-session tool activation is necessary at the actual tool-budget
scale of Phase 3. KB-coverage growth is the dominant lever on spawner suboptimality (HKUST QuantAgent formal result) —
expanding retrieval coverage beats refining model quality at constant KB coverage. Evaluate tool activation only after
KB coverage has been expanded and the ceiling is clearly measured.

## Status

Design intent only. Full implementation spec to be written by Maestro at Phase 3 planning time.
