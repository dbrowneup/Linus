## DEC-0054 — Activation hooks: API stub Phase 1, feasibility spike Phase 2

**Date:** 2026-05-06 **Status:** accepted

**Context.** The safety-alignment-privacy synthesis recommends an activation-hooks API as a Phase 1 stub and Phase 2
feasibility spike. Access to intermediate layer activations enables steering, monitoring, anomaly detection, and future
interpretability tooling — all of which are architectural properties that are expensive to retrofit once the inference
layer hardens. The Phase 2 spike determines whether mlx-lm actually exposes the access needed; the Phase 1 stub
defines the surface so callers can be written before the implementation exists. Closes **S17**.

**Decision.** Add an `ActivationHooks` stub class to `src/linus/` in Phase 1. The stub is a no-op implementation of
the target API surface — all methods succeed but return `None`:

```python
class ActivationHooks:
    def register_hook(self, layer_id: str, fn: Callable) -> str: ...
    # → hook_id; fn receives (activation_tensor, layer_id) at forward time
    def get_activation(self, layer_id: str) -> Any | None: ...
    # → most-recently-captured activation at layer_id, or None if hook not active
    def clear_hooks(self) -> None: ...
    # → deregisters all hooks and frees any captured tensors
    def list_registered(self) -> list[str]: ...
    # → layer_ids with active hooks
```

The stub is imported in `src/linus/__init__.py` and available as `linus.activation_hooks`. Phase 1: all methods return
`None` / empty values with zero runtime overhead.

**Phase 2 feasibility spike.** Run Llama-3.1-8B-4bit or Qwen3-7B via mlx-lm. Attempt to extract residual stream
activations at one named intermediate layer (e.g., `transformer.h.16.output`) using mlx-lm's internal API or
post-training hooks. Evaluate: (1) does mlx-lm expose a hook registration point? (2) what is the per-token overhead?
(3) can activations be captured without breaking streaming? Document findings in `experiments/activation-hooks-spike/`.

**Decision rule from spike.** If mlx-lm exposes hooks with <5ms per-token overhead: implement `ActivationHooks` for
real in Phase 2; schedule Phase 6 steering experiment ADR. If mlx-lm does not expose hooks without forking: file a
minimal patch to mlx-lm upstream; defer implementation to Phase 6 and note the dependency; stub remains in Phase 2. If
overhead is prohibitive: stub remains; log as a known limitation; revisit when pmetal's kernel architecture exposes a
native hook surface.

**Consequence.** Activation-hooks callers can be authored in Phase 2–4 against the stub API regardless of whether the
underlying implementation exists. The stub prevents the "we'll add this later" drift pattern where interpretability
tooling gets indefinitely deferred. Phase 6+ steering experiments (FKC-style, DEC-0033 fingerprint registry) have a
defined hook surface to target.
