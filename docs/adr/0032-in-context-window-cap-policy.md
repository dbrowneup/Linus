## DEC-0032 — In-context window cap policy (16K Phase 2 floor; episodic store as overflow)

**Date:** 2026-05-03 **Status:** accepted

**Context.** The Llama 3 paper ([2407.21783](../paper-notes/2407.21783v3.md)) demonstrates 128K context windows are
operationally available (98.1 multi-needle score), and is also the cleanest evidence that the bet is a quadratic-cost
simulation of memory inside attention — what Garrison's framework critiques as the wrong architectural axis. Linus has
the unusual freedom (relative to a hosted single-model assistant) to actually have a separate episodic store, and the
only way that freedom delivers value is if the orchestration layer prefers the store over the long context as a matter
of policy rather than as an after-the-fact optimization. Mughal's
[_Why Claude Gets Dumber_](../../context/notes/Why-Claude-Gets-Dumber-the-Longer-Your-Session-Run.txt)
sharpens this with operational evidence: lost-in-the-middle attention degradation makes attention degrade _inside_ the
window even when the window is large, so the cap is justified by both the formal-complexity argument and the
operational-degradation argument.

**Decision.** **Phase 2 default in-context cap is 16K tokens per Worker call**, with per-`memory_mode` (DEC-0031) budget
allocation across task spec / KB context / scratchpad / episodic prefix / system + format. The cap sits comfortably
inside every credible Worker's native window (Qwen2.5-Coder-7B 32K, Mistral-7B-Instruct-v0.3 32K, Llama-3.1-8B-Instruct
128K, BitNet b1.58 2B4T 4K), so the cap is a _policy_ constraint rather than a per-model limit.

**Per-`memory_mode` cap allocation v0:**

- `stateless` — task spec ≤ 8K, KB context ≤ 6K, system + format ≤ 2K. No episodic prefix.
- `session_stateful` — task spec ≤ 4K, KB context ≤ 4K, session scratchpad/answer prefix ≤ 6K (most recent first,
  CRISPR-style temporal weighting), system + format ≤ 2K.
- `project_stateful` — task spec ≤ 4K, KB context ≤ 3K, episodic prefix ≤ 7K (project-tagged + temporally weighted),
  system + format ≤ 2K.

The allocations are _defaults_, configurable per-call by the caller and overridable per-skill in Phase 7. Numbers are
deliberately round so empirical Phase 1c+ measurement can refine them without architecture churn.

**Overflow contract — episodic store is the substrate, not larger context.** When the budget for any layer is exceeded:

1. The over-cap content stays in the episodic store at full fidelity (DEC-0030's retention default).
2. The router applies a **summarization-or-retrieval** decision. KB context: smaller retrieval set + a summary of the
   dropped chunks. Session prefix: summarize older turns into a single summary turn record (itself a first-class
   addressable record per DEC-0030) and load the summary in place of the dropped detail. Episodic prefix: retrieve fewer
   but more relevant records via CRISPR-style ranking.
3. The caller is told (via dispatch metadata) what was summarized vs. dropped, so a follow-up `recall` can rehydrate the
   missing detail explicitly. Workers do not silently lose information; the routing layer is the keeper of what was
   elided.

**Cap-bypass mechanism.** A caller can request a higher cap up to the underlying model's native window via explicit
annotation (`context_cap_override: <N>` in the dispatch spec) recorded in the audit log. The bypass is intentionally
noisy in the audit so the "stuff everything in context" pattern is detectable when it happens. There is no automatic
bypass.

**Direction over time.** The 16K Phase 2 cap is a **floor we move with confidence** as Linus matures and as Worker
context windows themselves grow with Apple-Silicon-tractable models, _not_ a permanent ceiling. Larger context windows
are genuinely useful — they let a Worker see more of a complex task at once and reduce orchestration round-trips. The
cap moves up empirically. The episodic store, the overflow contract, and the explicit-bypass mechanism stay regardless,
because attention degrades inside the window even when the window is large (Mughal's lost-in-the-middle finding) and
because the formal-complexity argument for separate state-bearing infrastructure (Garrison's Theorem 1) is
substrate-independent.

**Telemetry.** Every dispatch records `context_used_tokens`, `context_capped: bool`,
`context_overflow_action: drop|summarize|retrieve`, and per-layer breakdown in the audit log.

**128K is a Phase 8 capability, not a Phase 2 default.** Llama 3.1 8B's 128K window is reserved for explicit-bypass
tasks where the no-summary requirement is justifiable (e.g. single-shot whole-paper extraction where summarization would
corrupt the answer). Even there, the router prefers chunked dispatch + episodic-store reassembly over single-shot 128K,
with the bypass as the escape hatch.

**Out of scope for Phase 2.** Multi-call coordination of context across parallel Workers (Phase 3 fan-out) inherits the
same cap per Worker; cross-Worker context sharing via the episodic store is the substrate, not a larger shared context
window. The summarization function used at overflow points is initially deterministic (most recent N + truncated older);
a learned summarizer is Phase 6+.

**Consequence.** Linus actively benefits from the episodic store rather than letting attention pretend to be one. The
lazy "stuff everything in context" pattern becomes detectable in audit. Cap moves up empirically as Phase 1c+ telemetry
accumulates. Reversal cost low for the cap number; medium for the overflow contract (downstream consumers will assume
the behavior).
