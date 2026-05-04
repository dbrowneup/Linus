## DEC-0042 — Coconut as Phase 6 candidate substrate experiment, conditional on Phase 1 portability check

**Date:** 2026-05-03 **Status:** accepted

**Context.**
[Hao et al. "Training LLMs to Reason in a Continuous Latent Space" (Coconut, 2412.06769)](../paper-notes/2412.06769v3.md)
feeds the model's last hidden state back as the next input embedding rather than decoding to a discrete token. This is
the cleanest published instance of latent-space recursive state maintenance — the third axis alongside the SQLite
substrate (DEC-0029) and the TTT substrate (DEC-0037) for the memory pillar's recurrence question. A single continuous
thought can hold a _superposition_ of candidate next steps, yielding implicit breadth-first search across multiple
latent positions. For Linus this is a substrate worth evaluating, but the Meta reference implementation may or may not
be MLX-portable, and Coconut training may or may not be tractable on a 32 GB unified-memory budget.

**Decision.** **Phase 6 candidate substrate experiment, conditional on a Phase 1 MLX-portability check.**

- **Phase 1 prerequisite spike** (small, lower priority than DEC-0037 and DEC-0038): check whether the Meta reference
  implementation at `https://github.com/facebookresearch/coconut` is MLX-portable or CUDA-bound. Also evaluate whether
  **iCoT** (Deng et al., the citation Coconut builds on — language-CoT supervision with length-shortening curriculum) is
  the more practical lead for Linus's compute budget.
- **Decision rule:** if MLX port is tractable **and** iCoT-or-Coconut training cost on M1 Max is comparable to LoRA at
  the same parameter count, Coconut graduates to Phase 6 candidate substrate experiment; else filed as Phase 8 alongside
  DEC-0041.
- The decision interacts with the Phase 6a/6b lane choice from DEC-0014: if Coconut graduates and the lane decision
  favors a Linus-trained Worker substrate experiment, Coconut joins minGRU (DEC-0038) and TTT (DEC-0037) on the Phase 6
  substrate menu.

**Consequence.** Coconut stays named as a credible substrate alternative without consuming Phase 6 budget speculatively.
The Phase 1 spike is small (a build-and-run feasibility check, not a training run) and gates the Phase 6 commitment.
Reversal cost low — the spike is a feasibility check, not an architecture commitment.
