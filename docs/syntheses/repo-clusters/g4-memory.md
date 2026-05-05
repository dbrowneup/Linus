# Group 4 Synthesis — Agent Persistent Memory

**Date:** 2026-05-04 **Repos surveyed:** agentmemory, anamnesis, omega-memory, engram, remember, prompt-vault, openaugi,
memex **Verdicts:** 7 × Study, 1 × Ignore (prompt-vault)

---

## What this document is

A cross-cutting synthesis of eight repositories surveyed as part of the Phase 1 recon run, collectively constituting the
"agent persistent memory" cluster. These repos are working reference implementations of what the memory architecture
spec calls Layer C — cross-session episodic memory, the substrate that satisfies Garrison's reliable-history-access
requirement across sessions, projects, and restarts. The theoretical case for this layer lives in
[`docs/syntheses/memory-synthesis.md`](../memory-synthesis.md); the implementation contract lives in
[`docs/specs/memory-architecture.md`](../../specs/memory-architecture.md) (DEC-0028 through DEC-0043). This document is
the empirical layer beneath both: what have practitioners actually shipped, what design decisions did they make, and
which of those decisions Linus can lift, steal, or avoid.

---

## The unifying thesis

Every repo in this cluster starts from the same observation: the default assistant — whether Claude Code, Cursor, Cline,
or any Ollama-backed agent — is amnesiac. It reconstitutes its working context from scratch at every session start,
spending tokens on re-explanation that a durable history would have made unnecessary. The repos differ in how
aggressively they treat that amnesia as an architectural problem versus a workflow problem. At one end, `openaugi` and
`agentmemory` build full retrieval substrates with vector indexes, FTS5, typed schemas, and hook taxonomies that
subscribe to every lifecycle event Claude Code exposes. At the other end, `remember` and `engram` are closer to
structured notebooks that a cooperative agent maintains by convention. `memex` sits in a philosophically distinct
position: it treats the rules-as-prompt, not the schema-as-constraint, as the load-bearing mechanism — and tests that
bet by running the same constitution on Claude, Codex, and Gemini simultaneously.

For Linus, the cluster collectively answers a question the memory-architecture spec leaves open: what should the
DEC-0029 v0 SQLite schema actually look like, in column-level detail? One repo — `openaugi` — provides a
close-to-deployable answer.

---

## Substrate landscape

The cluster spans the full range of storage choices, from single SQLite files to Postgres-with-pgvector to plain
markdown on a filesystem.

`openaugi` is the most instructive case. It commits to exactly one SQLite file, no external services, two SQL tables
(`blocks` and `links`), a single FTS5 virtual table, and one sqlite-vec `vec0` table. Block IDs are deterministic
`hash(source_path + content_hash)` — content-addressed by construction. WAL mode lets the MCP server read while the file
watcher writes. The schema is small enough to reproduce from memory and general enough to absorb Layer B scratchpad
records, Layer C episodic records, and compiled navigational metadata without migration.

`omega-memory` takes the same SQLite + sqlite-vec + FTS5 foundation but builds a much heavier product on top: 25 MCP
tools, six hook scripts, a daemon mode, an optional HTTP transport, and a Pro-gated tier with coordination, routing, and
entity-linking modules. The open-core boundary is visible in the codebase itself.

`agentmemory` uses SQLite for its KV state (via `iii-engine`, a Rust WebSocket daemon) but routes all operations through
that daemon rather than opening the SQLite file directly. The iii-engine dependency is the blocker for Linus; the
patterns agentmemory implements on top of it — hook taxonomy, RRF triple-stream retrieval, lease/signal/checkpoint
primitives — are directly portable to a Python orchestration layer that talks to a plain SQLite file.

`anamnesis` sits at the opposite end from openaugi: Postgres with pgvector and pg_trgm, FastAPI, Docker Compose, and a
full Python SDK. The Docker Compose stack is the disqualifier for Linus's macOS-on-Apple-Silicon constraint (CLAUDE.md:
"Docker runs in a VM on macOS and does NOT pass through Metal or ANE; Docker is for stateless services only"). Anamnesis
uses Postgres specifically for its stateful vector extension; that is exactly the case CLAUDE.md's constraint targets.

`engram` and `remember` sit entirely on flat files — markdown wikis and Obsidian vaults, respectively. No vector index,
no content hashes, no concurrency primitives. They are better understood as disciplined notebook conventions than as
retrieval substrates.

`memex` is a governed markdown directory backed only by git. Rich constitution, a 205-line bash lint script, a 1.9k-line
Python CLI, and a cross-vendor enforcer pattern — but no vector retrieval at all. The git-only persistence is
deliberately minimal; the spec rejects it as insufficient for Layer C recall at scale, while recognizing that git is
correct as the persistence layer beneath the SQLite episodic store (DEC-0029 already commits to this).

`prompt-vault` has no storage layer and no runtime, and is discussed further under the miscategorization note below.

---

## Key findings

**openaugi is the closest existing match to DEC-0029's v0 substrate.** Its two-table schema (`blocks`, `links`) with
sqlite-vec + FTS5 in WAL mode satisfies all four of Garrison's sub-requirements directly. Addressability is handled by
`blocks.id` derived from `hash(source_path + content_hash)`; disambiguation by the combination of `content_hash` and
`source`; temporal order by `block_time` and `ingested_at`; integrity by the content-hash itself plus the SQLite WAL
journal. The `kind` discriminator on `blocks` already has the vocabulary range (`context_block:document`, `data_block`,
`context_block:tag`, `context_block:cluster`) that DEC-0030's three-segment record (`scratchpad`, `answer`,
`tool_output`) would extend with three more values. The schema is alpha, but it is small and clean enough to lift almost
verbatim. The retrieval path — `get_context` doing 3× over-fetch with cosine-grouped dedup and MMR re-ranking, then
link-expansion — is the right shape for the Phase 3 retrieval combinator. The remaining gap is that openaugi's ingest
pipeline is Obsidian-vault-shaped: it knows about `[[wikilinks]]`, heading-based splits, and the `OpenAugi/` vault
subfolder. Linus's episodic store holds turn-tagged session records, not vault notes. The schema generalizes; the
pipeline does not. Lifting the schema means adopting the table design and the ID convention, then writing a Linus-native
writer that produces `segment="scratchpad"` records instead of `kind="data_block"` vault chunks.

**agentmemory's lease/signal/checkpoint primitives address Phase 3 parallel-Writer write coordination.** The
`memory_lease` MCP tool is exactly the exclusive-action primitive that the memory-synthesis's Phase 3 section identified
as an urgent question when parallel Workers begin writing to the same episodic store simultaneously. The hook taxonomy —
13 lifecycle hooks from SessionStart through TaskCompleted — is a fully worked answer to which Claude Code lifecycle
events a Layer C implementation should subscribe to and what each one writes. The four-tier consolidation logic (Working
→ Episodic → Semantic → Procedural) is implementable in Python against a plain SQLite file without adopting iii-engine.
The RRF triple-stream search in `src/state/hybrid-search.ts` is small, well-factored, and directly portable.

**remember's `scripts/extract.js` transcript walker is a ready reference for backfilling Layer C from existing session
history.** Dan has months of Claude Code transcripts in `~/.claude/projects/*.jsonl`. The memory-architecture spec notes
that a session-handoff record should be the Linus-native analogue of Mughal's volatile `.claude/session-handoff.md`.
`extract.js` shows how to walk those transcripts, strip noise prefixes, and deduplicate by processed-set — the mechanics
of retroactive episodic store population. This is a Phase 2b deliverable that the spec does not yet name explicitly, and
`extract.js` is the reference implementation.

**engram's lint taxonomy is directly portable to an episodic-store integrity verb.** Engram's `lint_wiki` operation asks
an LLM to classify the corpus against six issue types: `contradiction`, `stale`, `missing_xref`, `stub`, `orphan`,
`duplicate`. The memory-architecture spec's DEC-0039 describes roll-up consolidation but does not specify a
maintenance-pass that checks the store's integrity against itself. Engram's six-type taxonomy maps cleanly onto a
periodic Layer C audit — find contradictory episodic records, stale summaries whose constituent turns have since been
superseded, orphan records unreachable by any parent-pointer chain. This belongs in Phase 3 as a named operation on the
episodic substrate, not in DEC-0039 (which is a write-time schema concern, not an after-the-fact audit).

**memex's cross-vendor enforcer pattern is architecturally novel and directly applicable to Maestro/Worker QA.** Memex's
design principle is that the model that wrote a record should never audit it: Codex audits Claude's memory writes, with
read-only access and a dated report dropped in `docs/reports/`. For Linus, which is local-first, "different vendor"
would mean "different local model" — Mistral-7B auditing Qwen2.5-Coder writes. The security synthesis established that
trust-tier separation and output validation are first-class concerns for the orchestration layer. The cross-vendor
enforcer pattern is the concrete mechanism for applying that principle to the memory store: a separate Worker, with
lower authority, audits the episodic records that the primary Worker wrote. Whether a local-model enforcer is
adversarially strong enough to catch real inconsistencies is an open question, but the pattern is worth encoding as a
Phase 3 design constraint rather than discovering it independently.

**anamnesis's authority-weighted hierarchy is the right answer to the wrong substrate.** The explicit/agent/system/
inferred cap hierarchy (8.0/4.0/2.0/1.0 initial weights, adjustable via reweight cycles) is a disciplined answer to the
failure mode where Worker-generated noise drowns user-stated facts in retrieval. DEC-0029's schema does not currently
have a `trust_level` weight for retrieval ranking distinct from the binary `trust_level` field it does carry. Anamnesis
makes a practical argument that AI-derived records should earn retrieval prominence through repeated confirmation cycles
rather than starting at full authority. The concept transfers; the Postgres substrate does not.

**prompt-vault is miscategorized.** It is a prompt cookbook, not memory infrastructure. The repo ships no runtime, no
schema, no storage layer, and no API surface. The `claude-md-memory-workflow/` subdirectory contains a weekly GitHub
Actions cron that auto-updates a CLAUDE.md, and `obisidian-knowledge-graph/` contains shell recipes for auditing an
Obsidian vault — these are adjacent to memory concerns, not constitutive of them. The auto-ADR slash command in
`self-documenting-ai-agent/` is worth saving as a draft for a future Linus skill. Beyond that, prompt-vault should not
appear in the Layer C infrastructure discussion.

---

## Patterns and modules worth lifting

This is the section that directly serves Phase 2 implementation.

**The openaugi two-table schema as the DEC-0029 starting point.** Read `data-model.md`, then `store/sqlite.py` through
the DDL and FTS5 trigger definitions (approximately line 120). The question for Dan is whether to adopt the column names
verbatim and add `session_id`, `turn_id`, `parent_turn_id`, `segment`, and `trust_level` as new columns on `blocks`, or
to rename to `episodes` and `episode_links` to signal Linus's ownership boundary. Either is defensible; the column names
matter less than committing to the schema before Phase 2a writes its first migration. The alternative of standing up
Qdrant in Docker for the same workload is worth closing explicitly: `sqlite-vec` inside the same file satisfies Phase 2
recall requirements and removes a stateful Docker service, which is exactly the kind of requirement The Algorithm says
to delete.

**The agentmemory hook taxonomy as the Phase 2 lifecycle spec.** Port the 13 hooks (SessionStart, UserPromptSubmit,
PreToolUse, PostToolUse, PostToolUseFailure, PreCompact, SubagentStart, SubagentStop, Stop, SessionEnd, TaskCompleted,
Notification, sdk-guard) into the Phase 2 episodic-memory spec, replacing iii-engine calls with direct SQLite writes via
`linus.memory.episodic.record_turn(...)`. Each hook's write contract — what fields it populates, what `trust_level` it
assigns, what `segment` discriminator it uses — is the implementation-ready Layer C spec that DEC-0030 currently leaves
to the implementer.

**The agentmemory lease/signal/checkpoint vocabulary for Phase 3 parallel-Worker coordination.** Do not implement these
in Phase 2 — the v0 single-writer episodic store does not need them. Do name them in the Phase 3 spec now, so the schema
can accommodate them without migration. `memory_lease` is an exclusive-write lock per record or session scope.
`memory_signal` is an async notification that a write has completed and dependents may re-read. `memory_checkpoint` is a
point-in-time snapshot of the episodic store (wrapping a git commit in DEC-0029's substrate).

**The anamnesis 4D retrieval pattern as a Phase 2 v1 target.** Anamnesis's four async channels — semantic, full-text,
temporal, relational — fused with RRF at k=60 are implementable without Postgres: sqlite-vec for semantic, FTS5 for
full-text, a recency-weighted ORDER BY for temporal, and a small in-process entity table for relational traversal.
agentmemory's `hybrid-search.ts` is the code reference for the same fusion logic. The v0 Phase 2a retrieval can be
simpler (semantic + full-text only), with temporal and relational added in Phase 2b once the schema is stable.

**The anamnesis `supersedes` / `depends_on` edge columns as the versioning primitive.** DEC-0039's hybrid leaf+summary
schema handles multi-step task roll-ups. What it does not currently address is explicit supersession: when a later
session corrects a decision made in an earlier one, the earlier record should be marked superseded rather than silently
overridden. Two foreign-key columns on the `episodes` table — `supersedes_id` and `depends_on_id` — are the minimal
expression of this, and they are cheap to add at schema definition time.

**The memex constitution as the Maestro-facing memory governance document.** The `constitution-core.md` pattern — a
portable, vendor-neutral document that tells any agentic harness how the memory store is organized, what the three
thread tiers are, and what the write discipline expects — is a model for the equivalent Linus document. The Phase 2
memory pillar implementation should produce a `docs/specs/memory-constitution.md` alongside the technical spec. This is
not a separate runtime artifact; it is the human- and Maestro-facing description of the same rules the SQLite schema
encodes. Memex has proved the pattern is portable across Claude, Codex, and Gemini.

**The remember Persona.md pattern as the Layer D user-preference record.** A single small file capturing evolving user
preferences, naming conventions, and working-style observations, injected into every session start, is the simplest
implementation of Layer D's persistent user context. `linus.memory.persona.read()` wraps a read of this file; the file
is maintained by the orchestration layer as a side effect of observations marked `trust_level=high`. The risk remember
demonstrates — every observation gets appended with no provenance, including hallucinated ones — is the exact failure
mode DEC-0030's trust-level field prevents.

**The engram lint taxonomy as the Phase 3 episodic-store audit operation.** Define a `linus.memory.episodic.audit()`
verb that sends a sliding window of recent episodic records to a local Worker with a strict-schema prompt and classifies
issues as `contradiction | stale | missing_xref | stub | orphan | duplicate`. The verb is read-only; it produces a
structured report that the Maestro reviews before any remediation writes. Engram's `parse_lint_response` Pydantic
contract is the right shape for validating the LLM's classification response before acting on it.

---

## Cross-references

The memory-synthesis document argued for Layer C promotion to a Phase 2 first-class deliverable and specified the
substrate (SQLite + content hashes + git). This document provides the empirical grounding: eight practitioners
independently converged on the same architectural need, and the one who implemented it closest to DEC-0029's spec is
`openaugi`. The memory-synthesis's Phase 3 parallel-write question has a named answer in agentmemory's
lease/signal/checkpoint primitives.

The LLM Wiki synthesis (G2/G3 clusters) surfaced many of the same repos from a different angle — agentmemory and
openaugi appear in that synthesis as retrieval and memory reference implementations. This group extends that reading by
examining the full episodic substrate, not just the retrieval shape. The G6 paper-qa cluster (if surveyed) would connect
to Layer D (KnowledgeBase), which this group treats as already specified by DEC-0015 and the KnowledgeBase submodule.

The security synthesis's trust-tier separation pattern connects directly to anamnesis's authority-weighted hierarchy and
to memex's cross-vendor enforcer. Both are answers to the same question: when Workers write to the memory store, how do
we prevent agent-generated noise from polluting user-stated facts? The security synthesis named this as an
orchestration- layer concern; the G4 repos show two concrete mechanism designs.

---

## Phase-tagged implications

**Phase 2a (episodic store v0 substrate):** Lift the openaugi two-table schema as the starting migration. Implement the
agentmemory hook taxonomy as the lifecycle write contract. Adopt sqlite-vec + FTS5 inside the same file; delete the
Qdrant requirement from v0 scope. Add `supersedes_id` and `depends_on_id` columns now — zero-cost at definition time,
expensive to add later. Write the `linus.memory.persona.read()` Layer D primitive using a Persona.md pattern from
remember.

**Phase 2b (backfill and retrieval):** Use `remember/scripts/extract.js` as the reference for a Python
`linus.memory.episodic.backfill_from_history()` tool that walks `~/.claude/projects/*.jsonl` transcripts and populates
the episodic store retroactively. Add temporal and relational channels to the retrieval path (anamnesis 4D pattern over
SQLite). Write `docs/specs/memory-constitution.md` using the memex constitution as the model.

**Phase 3 (parallel-Worker write coordination):** Promote the agentmemory lease/signal/checkpoint vocabulary to a named
DEC alongside DEC-0029. Add `linus.memory.episodic.audit()` using engram's lint taxonomy. Implement the cross-vendor
enforcer pattern: a separate low-authority Worker audits the episodic records written by the primary Worker and drops a
dated report. Tag the enforcer audit result with `trust_level=system` rather than `inferred`; it should not override
user-stated facts but should surface contradictions for Maestro review.

---

## Open questions for Dan

**Schema lift: verbatim or extended?** The openaugi `(blocks, links)` schema satisfies DEC-0029's requirements with
almost no friction. The decision is whether to adopt the column names verbatim and add Linus-specific columns, or to
rename to `(episodes, episode_links)` to signal ownership boundary from the first migration. Both are defensible; the
choice should be made before Phase 2a opens the first migration file.

**sqlite-vec vs Qdrant for v0.** Omega-memory and openaugi both prove that 384-dim cosine search inside the same SQLite
file satisfies Phase 2 recall requirements with no separate service. DEC-0029 does not pin a vector substrate. The
Algorithm says to delete the Qdrant service from v0 scope and add it back if sqlite-vec proves insufficient. Is the
Qdrant choice already locked for reasons orthogonal to substrate count (HNSW performance, multi-tenant scoping), or is
this an active deletion candidate?

**Does openaugi's schema get lifted verbatim?** This is the Phase 2 scoping question this cluster surfaces that the
memory-synthesis does not address. The two-table schema is close enough to deployable that the question is not "design
or reference?" but "lift or study?" The difference is whether the DEC-0029 migration file starts from the openaugi DDL
or from a clean-room design informed by it. Lifting saves time and inherits battle-tested column choices; clean-room
design preserves full alignment with Linus's naming conventions and avoids inheriting alpha-software debt. Given the
spec's DEC-0029 column set is already specified
(`session_id, turn_id, parent_turn_id, timestamp, role, segment, content_hash, content, trust_level, tags`), the
clean-room path diverges from openaugi primarily at the `blocks` vs `episodes` naming level. This is worth resolving
explicitly before Phase 2a implementation begins.

**Authority caps for Worker-generated memories.** Anamnesis calibrates AI-derived records at weight 1.0 (initial),
earning up to 4.0 via reweight cycles, to prevent agent noise from drowning user-stated facts in retrieval. DEC-0029's
`trust_level` field carries the same concept at the binary level. Should Linus's episodic retrieval apply an
anamnesis-style continuous weight that Worker-generated records must earn, or is the binary trust-level field sufficient
for Phase 2?

**Cross-vendor enforcer with local-only models.** Memex's enforcer depends on a genuinely different vendor catching what
the writer missed. For Linus, the closest analogue is a different local model family auditing the episodic store.
Whether that is adversarially strong enough to catch real inconsistencies is untested. Should the enforcer role escalate
to hosted Claude (Maestro) on a periodic cadence, or is a local-model enforcer the right design even if it is weaker?

---

_Inputs: `docs/repo-notes/{agentmemory,anamnesis,omega-memory,engram,remember,prompt-vault,openaugi,memex}.md`. Primary
cross-references: `docs/syntheses/memory-synthesis.md`, `docs/specs/memory-architecture.md` (DEC-0028 through DEC-0043),
`docs/syntheses/llm-wiki-synthesis.md`, `docs/landscapes/total-landscape.md` Crossing 5. Review trigger: when Phase 2a
episodic store implementation begins; when Phase 3 parallel-Worker coordination spec is drafted._
