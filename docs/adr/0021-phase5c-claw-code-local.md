## DEC-0021 — Phase 5c formally adopts claw-code-local; 500-line custom Python agent fallback removed

**Date:** 2026-05-03
**Status:** accepted (amends DEC-0007 and ROADMAP Phase 5c)

**Context.** ROADMAP Phase 5c hedged with a "small custom terminal agent (~500 lines
of Python)" as a fallback. claw-code-local already adds an Ollama backend to claw-code
and is currently cloned at `repos/claw-code-local/`. Tier 1 #5 role designations
explicitly assigned claw-code-local as the primary terminal local-model Worker
harness. The fallback is speculative engineering.

**Decision.** Phase 5c formally = "adopt claw-code-local." The custom Python agent
fallback is removed from the roadmap. Phase 5c work scope: configure + integrate.
If claw-code-local proves insufficient at Phase 5, that triggers a fresh decision
at the time, not pre-emptive engineering now.

**Consequence.** Phase 5c is bounded and inexpensive. The Algorithm applied: delete
the speculative requirement.
