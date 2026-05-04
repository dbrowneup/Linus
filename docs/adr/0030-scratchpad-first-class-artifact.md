## DEC-0030 — Scratchpad as a first-class durable artifact; o1 anti-pattern forbidden

**Date:** 2026-05-03 **Status:** accepted

**Context.** Three of the eleven Garrison-thread paper notes
([Merrill & Sabharwal 2310.07923](../paper-notes/2310.07923v5.md),
[Feng et al. 2305.15408](../paper-notes/2305.15408v5.md), and [Sparks 2303.12712](../paper-notes/2303.12712v5.md)) make
the same formal point from different angles: intermediate decoding tokens are not output decoration, they are the
substrate that lifts a single Worker call out of the TC0 complexity ceiling. Truncating them collapses expressivity
formally, not just inconveniently. OpenAI's documented behavior that o1 "discards reasoning tokens from its context
after each response" is a textbook case of giving up the very property that makes universal computation reachable. Linus
has the architectural freedom hosted services do not — the orchestration layer can capture and persist what the model
emits — and that freedom should be exercised by default, not by configuration.

**Decision.** **Scratchpad is a first-class durable addressable artifact in Phase 2; the o1 anti-pattern is a
non-conformance condition in the Worker protocol.**

- **Default scratchpad retention.** Every Worker invocation that emits intermediate reasoning has its reasoning tokens
  retained as a first-class record in the episodic store (DEC-0029), addressed by
  `(session_id, turn_id, segment="scratchpad")` and SHA-256-hashed for integrity. The DEC-0029 record shape absorbs
  scratchpad records natively — no separate substrate.
- **Two-segment record per turn** (Kojima two-stage pattern: reasoning extraction → answer extraction). Each Worker turn
  produces _two_ addressable records linked by parent-pointer: `segment="scratchpad"` (the reasoning trace) and
  `segment="answer"` (the final response). Tool outputs are a third segment, `segment="tool_output"`, also addressable.
  The orchestration layer always has the option to retrieve either segment in isolation — Workers cannot blur the
  boundary.
- **Worker protocol non-conformance condition.** The Worker protocol spec at `docs/protocols/maestro-worker-protocol.md`
  (and inherited by every Worker integration) explicitly forbids: silently truncating reasoning between turns,
  concatenating scratchpad into answer such that the boundary is unrecoverable, or routing reasoning through a channel
  the orchestration layer cannot durably capture. **Phase 2 will not ship with a non-conforming Worker as a default
  backend.**
- **`scratchpad_durability` capability tag in the model registry**, with values `native` (model emits reasoning we can
  capture in full), `partial` (we can capture but the model truncates internally between turns — flag as risk), and
  `non_conformant` (reasoning is structurally unavailable; e.g. o1 with hidden reasoning tokens). The router refuses to
  dispatch `session_stateful` or `project_stateful` tasks (DEC-0031 memory-mode primitive) to `non_conformant` Workers;
  `stateless` tasks are still permitted.
- **Episodic-store retention policy v0.** Scratchpad records retained at full fidelity for the lifetime of the session.
  Cross-session retention defaults to "retain unless explicitly archived." The Phase 6 TTT consolidation spike
  (DEC-0037) is the natural point at which to revisit whether long-tail scratchpad should be summarized or compressed.
- **Audit log integration.** The audit log (`~/.linus/audit.jsonl`, append-only) records the _event_ of each scratchpad
  write with hash and turn id, so the integrity guarantee survives even if the SQLite store is corrupted or rebuilt. The
  full content stays in the episodic store; the audit log carries the cryptographic chain.

**Consequence.** Linus Workers have an addressable, durable scratchpad by default; the formal-complexity expressivity
argument from the Garrison thread is realised structurally rather than left as a hope. The o1-class hosted models are
flagged in the registry but not banned; their strengths (single-shot capability) remain accessible for `stateless`
tasks. Reversal cost is high — every downstream consumer (logging, benchmarking, episodic-store consumers, the eventual
learned summarizer per DEC-0039) assumes the two-segment shape exists.
