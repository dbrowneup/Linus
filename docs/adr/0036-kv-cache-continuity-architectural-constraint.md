## DEC-0036 — KV-cache continuity as an architectural constraint

**Date:** 2026-05-03 **Status:** accepted

**Context.** The constructive complexity-theoretic results
([Merrill & Sabharwal 2310.07923](../paper-notes/2310.07923v5.md),
[Feng et al. 2305.15408](../paper-notes/2305.15408v5.md)) hinge on the transformer reading its own previously emitted
tokens with the _same_ KV cache state across decoding steps and across turns. Backends that silently invalidate KV cache
between turns leak the very expressivity those tokens were supposed to buy — the model technically has access to the
prior text but pays a fresh prefill cost and re-derives state from scratch, which collapses the recursion-via-feedback
property that lifts the system out of TC0. DEC-0030's first-class scratchpad and DEC-0031's
`session_stateful`/`project_stateful` memory modes both presuppose this continuity.

**Decision.** **KV-cache continuity is a hard requirement for any Worker backend Linus dispatches `session_stateful` or
`project_stateful` calls to.** Backends evaluated against this requirement at adoption time:

- **Ollama** — supports KV cache reuse via `keep_alive`; passes pending configuration verification.
- **pmetal** — supports KV cache continuity per its serve documentation; passes pending Phase 1b verdict (DEC-0012).
- **mlx-lm** — supports continuity; passes.
- **bitnet.cpp** — CPU-only; KV cache behavior to be verified during the Phase 1c BitNet 2B4T spike (DEC-0013). Any
  failure here is a Worker- protocol non-conformance per DEC-0030 and triggers a `scratchpad_ durability=non_conformant`
  registry tag.

The router refuses `session_stateful`/`project_stateful` dispatch to a backend that fails this requirement; `stateless`
calls are still permitted. The `keep_alive` (or backend equivalent) is configured at Worker-pool startup, not per-call,
so the cost of holding state is amortised across session-stateful calls.

**Consequence.** Worker backend evaluation gains a clear pass/fail criterion that protects the formal-complexity
expressivity argument from being silently undermined by an inference server's caching default. Some backend choices are
foreclosed (any future consideration of an attention-only API that returns logits without retaining KV cache would fail
this requirement and would not be eligible for stateful dispatch). Reversal cost medium — the registry tag is one field,
but downstream dispatch logic depends on it.
