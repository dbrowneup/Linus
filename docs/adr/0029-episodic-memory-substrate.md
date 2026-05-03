## DEC-0029 — Cross-session episodic memory substrate (Layer C)

**Date:** 2026-05-03
**Status:** accepted

**Context.** The memory synthesis identifies cross-session episodic memory
(Layer C in the four-layer decomposition) as the load-bearing layer Linus's
prior planning lacked entirely. Three substrate candidates emerge from the
Garrison-thread corpus: conservative structured-text-and-hashes
(SQLite + git), ambitious parametric-via-LoRA-consolidation (Akyürek-style
test-time training applied to session transcripts, per the
[TTT paper note](../paper-notes/2411.07279v2.md)), or hybrid where knowledge
graduates from text into LoRA after sufficient repeated access. The
corpus does not converge on a winner. The Phase 2 spec must commit to a
substrate without precluding later evolution.

**Decision.** **Conservative v0 in Phase 2; TTT spike in Phase 6 informed by
a Phase 1 viability measurement; hybrid kept as an explicit Phase 8
architectural option, not committed.** Concretely: Phase 2 Layer C v0 is
**SQLite** (single-file embedded DB at `~/.linus/episodic.db`) +
**SHA-256 content hashes per record** + **git as persistence substrate
underneath** (linus repo and KnowledgeBase already commit-track work;
episodic-memory writes commit through the same substrate). The four
sub-requirement obligations from DEC-0028 map cleanly: rowid + content hash
for *addressability* and *disambiguation*; monotonic timestamp +
parent-pointer for *temporal order*; SHA chain + git history for
*integrity*. CRISPR-style temporal weighting (recent ranked higher in
retrieval, ancient retrievable on demand) is a retrieval-side concern over
this substrate, not a separate substrate.

Episodic record shape v0: `(session_id, turn_id, parent_turn_id,
timestamp, role, content_hash, content, trust_level, tags)`. The shape
mirrors the chat transcript but with explicit addressability and integrity,
and is wide enough to absorb scratchpad records (DEC-0030) and tool-output
records without schema migration.

Linus exposes the layer via the **`linus.memory.episodic.*` tool family**:
reads (`recall`, `recall_recent`, `recall_by_tag`, `recall_by_content`),
writes (`record_turn`, `record_consolidation`), and admin
(`prune_archived`). Substrate variation (SQLite-only v0; hybrid v2 if it
lands) stays hidden behind this API so Workers cannot tell which layer
answered.

Phase 1 prerequisite: the **TTT viability smoke test** (DEC-0037) must run
before any Phase 6 lane decision. Phase 6 spike target: an Akyürek-style
per-project LoRA consolidation experiment using the v0 SQLite store as
input, output measured cost-per-consolidation on M1 Max + retrieval-quality
delta vs. SQLite-only baseline. Phase 8 architectural option (not
commitment): the hybrid "graduate from text into LoRA after repeated
access" pattern, gated on the Phase 6 spike result.

**Consequence.** A known-good substrate ships in Phase 2 with no
research-grade dependencies. Operational from day one. The Akyürek result
stays reachable as an upgrade path without Phase 2 budget pressure. The
uniform `linus.memory.episodic.*` API absorbs whatever substrate evolution
follows. Reversal cost low for v0 (SQLite is boring); medium for the
parametric upgrade path (the Phase 6 spike could fail, and Linus stays on
v0 indefinitely — that is acceptable).
