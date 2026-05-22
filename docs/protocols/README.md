# docs/protocols/

Operating protocols — the durable forms of patterns referenced (often in shortened form) from
[`../../CLAUDE.md`](../../CLAUDE.md). These documents capture _how_ Linus's work happens, separate from _what_ the work
produces.

## Files

- [`maestro-worker-protocol.md`](maestro-worker-protocol.md) — the full Maestro (Dan + hosted Claude) ↔ Worker (local
  model) delegation contract. Spec-first dispatch, smoke gates, scratchpad discipline, memory-mode + cot-budget
  declarations.
- [`maestro-protocol.md`](maestro-protocol.md) — the Maestro-only loop: when hosted Claude operates without Worker
  dispatch, how attention is allocated, when to pause for write-back.
- [`curation-protocol.md`](curation-protocol.md) — policy for adding, pruning, and archiving material in `repos/`,
  `context/`, and `docs/`. Adopted in DEC-0025. The factual-grep audit clause (added 2026-05-16) lives here.

Each is a living document — updated when execution surfaces gaps. Session summaries in
[`../session-summaries/`](../session-summaries/) often cite the relevant protocol section that drove a decision.
