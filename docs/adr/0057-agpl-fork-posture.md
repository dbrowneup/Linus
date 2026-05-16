## DEC-0057 — AGPL-fork posture: clean-room study, no code lifts without project-level license commitment

**Date:** 2026-05-16 **Status:** accepted

**Context.** The 2026-05-10 PR 30 fold-in pass surfaced AGPL-3.0 as the load-bearing license constraint on two
otherwise-attractive reference repos: **MiroFish-Offline** (`repo-notes/MiroFish-Offline.md` §1, §5; the most complete
worked example in the cloned-repo collection of a local-first knowledge-graph + retrieval + agent-tool stack —
Neo4j + Ollama + hybrid vector/BM25 search) and **origin** (the Rust harness whose desktop layer is AGPL, with the
core Rust crates partly Apache via subcrate split). Both repos are flagged in R4-02 because their architectural lift
candidates compound across Phase 2 (knowledge-graph + memory substrate), Phase 3 (KB tooling), and Phase 5+ (harness
integration). R2-34 (`g5-graph-tools.md`) had previously tracked the same posture question at convention-worth-codifying
priority; PR 30's adds upgraded urgency from "eventually" to "before any Phase 3 KB-tooling lift starts."

AGPL-3.0 is GNU's strong-copyleft license with the network-use provision: derivative works of AGPL software, when made
available over a network, must themselves be released under AGPL-3.0 (with full source). Two specific consequences
matter here. First, **Linus has not committed to any license** — the project-purpose section of CLAUDE.md frames Linus
as "private, local, modular AI assistant," and there is no public license statement yet and no ADR commits Linus to any
specific license. Lifting AGPL code into Linus would force a license commitment Linus has not made. Second, the
"derivative work" boundary under AGPL is interpreted broadly enough that even pattern-level lifts — reading the AGPL
source and then writing "similar but not identical" code — sit in a gray zone where copyright analysis matters. The
safe posture is to treat AGPL reference repos as study material whose architecture can be **described and discussed**
but whose code cannot be **read-and-then-written-from**.

The forcing function is concrete and dated: MiroFish-Offline is the architectural prior art Phase 2 KnowledgeBase v1
wants to reference, and origin is a candidate Phase 2b memory sidecar (R2-39). Without an explicit policy in place,
the easy path is to lean on the prior art's source layout when designing Linus's parallels — which is exactly the
clean-room-violation pattern a careful copyright posture forecloses. Closes **R4-02**; supersedes the
R2-34-convention-worth-codifying framing in `g5-graph-tools.md`.

**Decision.** Linus adopts a **clean-room separation** posture for AGPL-licensed reference code. The policy has three
tiers, each with an explicit gate:

1. **Quarantined — read for description only.** AGPL repos in `repos/` are read-only reference clones (per existing
   convention). Per-repo notes (`docs/repo-notes/<name>.md`) document the architecture, named patterns, and design
   decisions at the **descriptive** level: "MiroFish-Offline uses a Neo4j graph with a hybrid
   `vector_search ∪ bm25_search` retrieval pipeline followed by NER extraction via local-LLM JSON-mode prompting."
   The repo-note is allowed to name the pattern, name the libraries used, and describe the topology. The repo-note is
   **not** allowed to transcribe source code, reproduce module layouts as Linus implementation targets, or describe
   internal algorithms at function-by-function granularity.

2. **Reviewed — design-from-upstream-specs only.** When the architectural pattern documented in a Quarantined repo-note
   is the basis for a Linus implementation, the Linus implementation is designed and written from **upstream specs**
   (Neo4j docs, the hybrid-search literature, vendor API documentation, the public protocol specs) — not from re-reading
   the AGPL source. The author of the Linus implementation must be able to point to the upstream references that drove
   each design choice. The Quarantined repo-note may be cited as evidence that the topology is buildable and as a
   comparison case for "what does a production-deployed system in this space look like?"; the AGPL source itself is
   not the implementation reference.

3. **Forbidden — direct code lifts.** Copying code from an AGPL repo into Linus is forbidden under this ADR until and
   unless Linus itself commits to AGPL-3.0 at the project level. That decision is currently unsettled (no ADR commits
   Linus to any license; the project-purpose framing is "private, local, modular"). A separate future ADR would be
   needed to make any AGPL commitment; until that ADR lands, AGPL code does not enter Linus's source tree, and any
   transitive AGPL dependency (an AGPL Python package, an AGPL Rust crate) is treated as a Phase-blocker that must be
   resolved before the dependent Linus component ships.

The **subcrate-split case** (origin's `goose` Apache crate vs. its AGPL desktop layer) is handled by following the
license at the **specific artefact** being considered, not the repo-level license. If Linus wants to lift a pattern
from origin's `goose` core crate (Apache), the Apache license governs and the standard supply-chain posture (DEC-0024)
applies. If Linus wants to lift from origin's desktop layer (AGPL), this ADR's quarantine/review/forbidden tiers apply.
The author of any cross-crate lift must verify the per-artefact license before the lift, not infer from the
repo-level `LICENSE` file alone.

**Pattern-level lifts** — the gray-zone case where Linus designs something "similar but not identical" to an AGPL
reference — require an explicit clean-room procedure documented per case. The minimum procedure:

- **Author A** reads the AGPL source and writes a description of the pattern in the Quarantined repo-note (already
  the default convention; no new artefact needed).
- **Author B**, who has **not read the AGPL source**, writes the Linus implementation from the Quarantined repo-note's
  description plus the upstream-spec references. Author B's commit messages and code comments may cite the upstream
  specs and the Quarantined repo-note; they may not cite the AGPL source directly.
- **Author A and Author B are different people** in the strict clean-room interpretation. In practice for Linus, where
  Author A is often Dan + Maestro and Author B is often a Worker, the clean-room separation is enforced by Worker
  spec discipline: the Worker spec includes only the architectural description and the upstream-spec links; the
  Worker does not have the AGPL repo path in its context. The Worker's output is the clean-room artefact.
- **The pattern-level lift is documented** in `docs/curation-log.md` with the AGPL source, the upstream references the
  Linus implementation draws from, the clean-room author boundary, and a sentence on why the design choice is upstream-
  spec-derived rather than AGPL-source-derived. This is the audit trail that survives a future copyright question.

A second-tier rule covers the **license-commitment escape hatch**. If at any future Phase the question "should Linus
itself be AGPL-3.0?" is settled affirmatively in a project-level license ADR, this ADR's Forbidden tier converts to
permissive direct code lifts from AGPL sources (subject to standard supply-chain discipline per DEC-0024 and the
DEC-0024 amendment for license-compatible vendoring). The escape hatch is documented here so future maintainers know
the Forbidden tier is conditional, not absolute; it depends on a project-level license decision that is currently
unsettled.

**Consequence.** Two architectural reference repos (MiroFish-Offline, origin's desktop layer) become Watch-tier-only
for code, but their architectural lessons remain available through the Quarantined-tier repo-note descriptions.
Phase 2 KB v1 design proceeds against upstream Neo4j docs and the hybrid-search literature, with MiroFish-Offline cited
as comparison case but not as implementation source. Phase 2b memory-sidecar evaluation (R2-39) of origin proceeds
against the Apache `goose` core crate; the desktop layer is descriptively studied for architectural lessons but its
code does not enter Linus.

The ADR is **deliberately strict at Phase 0–2** because the cost of being strict now is small (one fewer reference
source per design discussion) and the cost of being strict later is large (any AGPL-derived code must be tracked,
quarantined, or excised, which is an arbitrary-history-rewrite-class operation). The clean-room procedure for pattern-
level lifts is documented but should be the exception, not the default — when in doubt, design from upstream specs and
skip the AGPL reference entirely.

The **license-posture-of-Linus question** itself stays open under R2-45 ("AGPL stance before Phase 8") and is not
resolved by this ADR. DEC-0057 governs how AGPL **reference repos** are handled; the question of what license Linus
itself adopts is a separate decision that becomes urgent at Phase 8 (mobile, native app, distribution) and may resolve
to AGPL, BSD/MIT, dual-licensed, or other. This ADR is consistent with any of those outcomes — its Forbidden tier
becomes moot if Linus commits to AGPL; its Quarantined and Reviewed tiers remain useful regardless.
