## DEC-0027 — Linus practice/stance batch (page cache, public APIs, multi-language, sovereignty, reproducibility, Obj-C)

**Date:** 2026-05-03 **Status:** accepted

**Context.** Several stance-level questions surfaced together (Tier 3 #16): trust the OS page cache as a convention;
Apple private-API risk appetite; Rust as a co-language policy; explicit sovereignty statement; reproducibility +
interpretability principle; Obj-C/Metal-direct work as a future skill bet. These shape Linus's posture across phases
without being phase-blocking.

**Decision.** (1) **Trust the OS page cache** adopted as CLAUDE.md Engineering Convention (anchored by the flash-moe
paper's empirical finding). (2) **Public APIs only for Linus's own code** (CoreML/MLX/Metal). pmetal uses supported APIs
(not private); the ANE reverse-engineering repo stays methodology reference only, not vendored. Linus does not
reverse-engineer Apple's private APIs. (3) **Multi-language stance**: Python is core orchestration language; comfortable
with Rust components (pmetal, claw-code/claw-code-local), JavaScript/TypeScript components (some node/npm familiarity),
and bash for stringing CLI tools. No "one orchestration language" policy. (4) **Light sovereignty refinement** in
VISION.md borrowing NOMAD's framing ("the network boundary is the trust boundary"); not over-elaborated. (5)
**Reproducibility + interpretability over fancy stochastic methods** adopted as a VISION.md design principle (anchored
by the Horiike PCA-projection paper). (6) **Obj-C/Metal-direct as Phase 7/8+ skill bet** — not ruled out, deferred.
Decision revisited only if/when concrete demand surfaces.

**Consequence.** Linus's posture is documented and stable. CLAUDE.md and VISION.md gain explicit conventions where prior
implicit ones existed. Future planning sessions can reference these stances without re-deriving them.
