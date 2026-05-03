## DEC-0039 — Episodic memory schema for multi-step Worker tasks: hybrid leaf + summary

**Date:** 2026-05-03
**Status:** accepted

**Context.** A multi-step Worker task (canonical Maestro-Worker scenario:
delegate, Worker carries the task across many tool calls, returns a
synthesized result) produces N turns of intermediate state. Storing every
turn at full fidelity satisfies Garrison's reliable-history-access
requirement but produces large episodic-store payloads on `recall`.
Storing only summaries trades faithfulness for tractability and risks the
o1 anti-pattern (DEC-0030) at the multi-task aggregation level.

**Decision.** **Hybrid: full M3 two-segment record at the leaf,
deterministic structural summary at the parent, both addressable.**

- **Leaf nodes** (individual Worker turns inside a task) store the full
  DEC-0030 two-segment record (`scratchpad` / `answer` / `tool_output`)
  at native fidelity in the DEC-0029 episodic store.
- **Parent nodes** (the rolled-up "task completed" record at the end of a
  multi-turn delegation) store a summary record with parent-pointer to
  all leaves.
- **Default behavior:** `linus.memory.episodic.recall` at the parent level
  returns the summary; explicit `recall_full(parent_id)` rehydrates from
  the leaves.
- **Summary function v0:** deterministic structural roll-up — decisions
  made (extracted from scratchpad annotations), files touched (extracted
  from tool_output records), errors encountered (extracted from
  tool_output stderr), final answer (the parent's `answer` segment) — plus
  a retained pointer to each leaf. **Not a learned summarizer**; that is
  deferred to Phase 6+ once a fine-tuned candidate exists.
- **The pattern mirrors Mughal's session-handoff file scaled down to the
  task level**: cheap to do at small scale, painful to retrofit later.

The schema absorbs the existing DEC-0029 record shape natively; the
`segment` field gains values `summary` (parent-level structural roll-up)
and `pointer` (a parent's pointer set to its child leaves).

**Consequence.** `recall` at the project or session level returns
manageable payloads while `recall_full` preserves the full faithfulness
the formal-complexity argument requires. Workers operating at the project
level see summaries by default; an explicit `recall_full` is a deliberate
choice that surfaces in the audit log. Reversal cost low — adding a
learned summarizer in Phase 6+ replaces the deterministic function without
schema change.
