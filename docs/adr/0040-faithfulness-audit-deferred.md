## DEC-0040 — Faithfulness audit of stored reasoning traces deferred (out of Phase 2 scope)

**Date:** 2026-05-03
**Status:** accepted

**Context.** Reasoning traces stored as durable artifacts (DEC-0030,
DEC-0039) and surfaced to Dan are implicitly endorsed by the system. The
[Kojima paper note's](../paper-notes/2205.11916v4.md) error analysis flags
that traces sometimes generate unnecessary steps after reaching the correct
answer, then corrupt the answer; sometimes they just rephrase the question.
A faithfulness-audit component (does the reasoning chain actually compute
what it claims to?) is technically possible but adds non-trivial complexity
and may not be needed at v0 scale.

**Decision.** **Faithfulness audit is out of scope for Phase 2; deferred to
Phase 3 with an explicit trigger condition.** Phase 2 stores reasoning
traces as the formal-complexity argument requires (DEC-0030) and surfaces
them to Dan as durable artifacts, but does not audit them for
self-consistency at write time or read time.

**Trigger condition for Phase 3 audit work:** a measurable failure mode
appears in practice — Worker reasoning trace claims X but the answer
reflects Y, or a downstream Worker uses a stored trace as input and
inherits its error. At that point, a faithfulness-audit component goes
into the Phase 3 backlog with concrete failure cases as design input.

The Algorithm check applies: build the audit when there is a real failure
to detect, not before. The audit-log telemetry from DEC-0030, DEC-0031, and
DEC-0032 supplies the data that surfaces the trigger condition.

**Consequence.** Phase 2 ships without an audit layer; the door stays open
for Phase 3+ to add one when failure modes surface in practice. Reversal
cost low — the audit can be added later without changing the underlying
schema, since traces are already addressable and hashed. If failure modes
never surface (because Worker output is faithful enough at the granularity
Dan cares about), the cost saved is real.
