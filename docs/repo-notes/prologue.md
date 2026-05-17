# prologue (`aegntic/prologue`)

## 1. Purpose and scope

Prologue (aegntic/prologue; TypeScript + Bun + JAX-Python bridge; MIT; backed by aegntic.ai, the R&D division of
ae.ltd) is **a durable AI agent memory library** that gives agents a memory system "that survives context window
resets, session restarts, and process crashes." Framed not as a vector database wrapper but as a **purpose-built
memory architecture** with three integrated products:

- **MemoryMatrix** — core memory store. File-based persistence with optional Graphiti knowledge graph. **Compression
  ladders** (working → project → overview → core) and **visibility boundaries** (private → inspectable → shared →
  canonical) with atomic writes.
- **Orchestrator** — task orchestration. Spawns agent CLIs, monitors execution, runs post-session analysis (git diff →
  insight extraction → automatic memory storage). Built-in recovery manager with graduated escalation.
- **FPEF v2.0** — First Principles Execution Framework. 4-phase gate enforcement (Find → Prove → Evidence → Fix).
  Post-hoc output validation. Anti-dishonesty safeguards. Catastrophic failure recovery protocol.

The library exposes an **MCP server** with 5 tools for Claude Code integration (entry point `bin/prologue-mcp`).
TypeScript strict mode; Zod schemas in `src/types/` for all runtime validation; all errors extend `PrologueError`. A
Python bridge (`python/`) provides Graphiti integration and embeddings, managed by `uv`, spawned via `Bun.spawn()` with
a JSON protocol; the library falls back to file-only mode if Python is unavailable.

The repo CLAUDE.md is unusually detailed about **swarm execution rules** (max 5 files per phase, mandatory verification
between phases, sub-agent swarming grouped by semantic boundary, max 3 edits to a file without re-read, context-decay
re-read rules after 10+ messages, rollback planning with starting-commit-hash) and about **critical rules** (NO
CO-AUTHORED-BY in commits; Step 0 cleanup before structural refactors; spec fidelity — "if it is not in PROJECT-SPEC.md,
it does not exist"). These rules are recognizably similar in spirit to Linus's own discipline (CLAUDE.md, the Algorithm,
agent fan-out conventions).

## 2. Architecture summary

**Memory compression ladder (the load-bearing model):**

```
  WORKING        PROJECT         OVERVIEW          CORE
  (scratchpad)   (dossier)       (atlas)           (biography)
     │               │               │                │
     │   confidence   │  confidence    │  confidence   │
     │    ≥ 0.5       │    ≥ 0.7       │    ≥ 0.9       │
     ▼               ▼               ▼                ▼
  Raw notes    Focused task    Cross-project    Durable truths
  & ephemera   context        awareness
```

Memories move up through four compression levels as confidence grows. A memory is born at WORKING (raw scratch
notes); promoted to PROJECT (focused task context) when confidence ≥ 0.5; promoted to OVERVIEW (cross-project
awareness) when confidence ≥ 0.7; promoted to CORE (durable biographical truth) when confidence ≥ 0.9. This is a
**multi-tier memory consolidation pattern** with explicit numerical thresholds — closer to a learning-style consolidation
than to a flat key-value store.

**Visibility boundaries (orthogonal axis):**

- `private` → only the owning agent can read/write.
- `inspectable` → other agents can see envelopes (metadata) but not body content.
- `shared` → other agents can read content.
- `canonical` → durable, broadly accessible.

These compose with compression levels: a memory at PROJECT compression + `inspectable` visibility surfaces its
envelope to other agents without exposing the body.

**Atomic writes** — file-system atomic write semantics for durability under crashes.

**Three integrated products:**

- **MemoryMatrix** — the memory store itself. File-based core, optional Graphiti knowledge graph for relational
  queries.
- **Orchestrator** — task orchestration around the memory. Spawns agent CLIs, monitors execution, runs post-session
  analysis. Recovery manager with graduated escalation.
- **FPEF v2.0 (First Principles Execution Framework)** — 4-phase gate enforcement: Find → Prove → Evidence → Fix. Each
  phase has gates that must be passed before advancing. Post-hoc output validation. Anti-dishonesty safeguards (the
  framework detects when an agent's stated output diverges from its actual evidence).

**MCP server (5 tools)** — entry point `bin/prologue-mcp`. Exposes the memory operations to Claude Code via MCP.

**Python bridge** — optional. Graphiti integration + embeddings via JAX. Managed by `uv` per Linus DEC-0024 disposable-
uv-env conventions. Spawned via `Bun.spawn()` with a JSON protocol. Falls back to file-only mode if Python unavailable.

**Source-material references:** the repo's CLAUDE.md notes design references in adjacent codebases — clawREFORM-
ecosystem README, Auto-Claude (coder agent, recovery service, memory_manager), cldcde projects FPEF spec. These are
not vendored but are explicitly cited as substrate.

## 3. What's reusable in Linus

**The four-tier compression ladder (WORKING → PROJECT → OVERVIEW → CORE) with confidence thresholds.** This is the
most architecturally interesting pattern. Linus's DEC-0028 memory pillar has five layers (A through E) but the
compression-ladder pattern is **orthogonal to the layer model**. It addresses **within-layer consolidation**: how
content within Layer B (within-session scratchpad) gets promoted to Layer C (cross-session episodic) and then to Layer
D/E. Prologue's pattern — confidence thresholds gate promotion — is a clean operational primitive. The Linus
memory-architecture spec ([`docs/specs/memory-architecture.md`](../specs/memory-architecture.md)) should consider
adopting confidence-gated promotion as the within-layer consolidation pattern.

**Visibility boundaries (private / inspectable / shared / canonical).** This is the closest existing precedent for
**Linus's Layer D investigation memory** (DEC-0052), which requires multi-agent shared state with controlled access.
Prologue's four-tier visibility model maps cleanly onto Linus's investigation-memory access model: agents within an
investigation can be `private` (their own scratchpad), `inspectable` (other agents see the envelope), `shared` (other
agents see the body), or `canonical` (all agents see, durable). The Linus DEC-0052 implementation should adopt this
vocabulary or something close to it.

**Atomic writes for memory persistence.** Prologue's atomic-write commitment is a portable durability primitive. For
Linus's Layer C SQLite-based persistence (per DEC-0029), atomic writes are already standard; for Layer B scratchpad
file persistence (per DEC-0030), atomic writes should be explicit.

**FPEF v2.0 4-phase gate enforcement (Find → Prove → Evidence → Fix).** The pattern — every agent task must pass
through four explicit phases, each with gates — is closely parallel to Linus's `[Plan]` → `[Act]` workflow plus the
smoke-test gate convention (CLAUDE.md, DEC-0027). For Linus's Phase 3 multi-agent spawner (DEC-0050), adopting an FPEF-
style 4-phase gate model is a portable discipline. The "anti-dishonesty safeguards" (detecting when an agent's stated
output diverges from its actual evidence) is the same intent as the BioReason-Pro typed-structured-prediction discipline
(S25) — make claims verifiable.

**Recovery manager with graduated escalation.** Prologue's recovery manager is portable for any Linus Worker that might
fail — graduated escalation (warn → retry → roll back → halt) is a robust failure model. The Linus Phase 3 spawner
spec should include a recovery primitive.

**MCP server with 5 memory tools as a Phase 3 surface.** Prologue exposes 5 MCP tools for memory operations. For
Linus's Layer C / Layer D memory access via MCP (per DEC-0045 fastmcp default), the Prologue surface is a usable
reference for which operations should be exposed. The Linus tool registry (per DEC-0046) should consider whether the
Prologue surface is the right scope (probably need at least: store, retrieve_by_tag, retrieve_by_content_hash, promote,
inspect) or whether a richer surface is needed.

**Swarm-execution-rules discipline.** The repo's CLAUDE.md swarm-execution rules (max 5 files per phase, mandatory
verification, sub-agent swarming grouped by semantic boundary, max 3 edits without re-read, context-decay re-read after
10+ messages, rollback planning) are recognizably similar to Linus's worktree fan-out discipline (CLAUDE.md "Worktree
fan-out discipline"). Two independent codebases converging on similar discipline rules is a strong signal. Worth a
brief cross-reference in CLAUDE.md.

**Bun + TypeScript strict mode + Zod for runtime validation.** Prologue's stack discipline is sharp: TypeScript strict
mode, no `any` in public API, Zod schemas in `src/types/`, all errors extend `PrologueError`. For any future
TypeScript-based Linus component (per DEC-0027 multi-language stance), this stack discipline is a portable convention.

**Python bridge via Bun.spawn + JSON protocol.** The cross-language bridge pattern — Bun spawns a Python subprocess
managed by `uv`, communicates via JSON over stdin/stdout — is a portable pattern for any future Linus component that
needs to bridge TypeScript and Python. The Linus orchestration core is Python; potential Phase 5+ frontend components
in TypeScript would benefit from this bridge pattern.

## 4. What's inspiration only

**TypeScript + Bun stack is not the Linus core.** Linus commits to Python as the orchestration core. The Prologue
library is too large (multiple subdirectories, MCP server, Python bridge, JAX/Graphiti integration) to vendor. The
patterns are portable; the implementation is not.

**Graphiti as the optional knowledge-graph layer.** Graphiti is a specific knowledge-graph product. Linus's KB
substrate (per DEC-0015 dual-graph) is not committed to Graphiti. The optional-graph pattern is portable; the specific
Graphiti dependency is not.

**JAX-based embeddings via Python bridge.** Linus's embedding stack is more naturally MLX (per DEC-0027 Apple Silicon
native). The JAX-via-Python-bridge pattern is portable but the specific JAX dependency conflicts with the MLX choice.

**Aegntic.ai backing.** Prologue is backed by a commercial company. The development pace and feature scope may exceed
what Linus can absorb or track. Watch for stable releases rather than tracking active development.

## 5. What's incompatible or out of scope

**Five MCP tools for memory operations vs. the agentmemory 51-tool MCP surface.** Per the existing
[`agentmemory.md`](agentmemory.md) repo-note, the agentmemory MCP surface is much richer (51 tools, including
relational graph operations). Prologue's 5-tool surface is the **minimal** alternative. The Linus tool registry per
DEC-0046 needs to decide between these surface scopes; the discussion is open per the agentmemory note's open
questions.

**Per-agent CLI spawning model.** Prologue's Orchestrator spawns agent CLIs as subprocesses with file-based
communication. Linus's Phase 3 spawner per DEC-0050 commits to a typed inter-agent message contract (`AgentReport` per
DEC-0051), which is structurally different from agent-CLI subprocess spawning. The Prologue pattern is suggestive
but doesn't directly compose with Linus's typed-message contract.

**The "anti-dishonesty safeguards" framing is anthropomorphic.** Prologue's FPEF anti-dishonesty framing treats the
agent as a potential bad actor that must be policed. Linus's discipline (DEC-0030 scratchpad-first-class-artifact;
DEC-0033 cot-gap fingerprint) is more measurement-oriented — the agent's reasoning is observable, not assumed dishonest.
The framing differs.

**Confidence thresholds (0.5, 0.7, 0.9) for promotion are domain-dependent.** Prologue's specific thresholds work for
its target domain (general agent memory); for Linus's Layer C consolidation, the right thresholds depend on the
task class and content type. Lifting the threshold values directly without calibration would be premature.

**Source-material-references to adjacent codebases.** The repo's CLAUDE.md references multiple adjacent codebases
(clawREFORM, Auto-Claude, cldcde) that aren't included. These are aegntic-internal references that don't help Linus.

## 6. Recommendation: **Study**

Prologue is a **memory-architecture pattern reference** for Linus's Phase 2 memory pillar (DEC-0028) and Phase 3
multi-agent investigation memory (DEC-0052). The compression ladder with confidence thresholds, the visibility-boundary
model, the FPEF 4-phase gate discipline, the recovery-manager pattern, the swarm-execution-rules discipline, and the
Bun-spawn-Python-via-JSON-protocol cross-language bridge are all worth lifting as design vocabulary.

The implementation is too TypeScript-native and too tied to the aegntic-internal substrate (clawREFORM, Auto-Claude,
cldcde, Graphiti, JAX) to vendor. The patterns are portable; the codebase is not.

The closest Linus-internal reference: agentmemory (per [`agentmemory.md`](agentmemory.md)) covers the same memory-
substrate space with a richer MCP surface (51 tools vs. 5). The two are complementary — agentmemory for the
comprehensive MCP-surface scope, Prologue for the compression-ladder + visibility-boundary + FPEF discipline. Both are
Study-level cross-references for the Linus memory pillar.

## 7. Questions for Dan

1. **Adopt the compression-ladder pattern (WORKING → PROJECT → OVERVIEW → CORE) for within-layer consolidation?** The
   pattern is orthogonal to the Linus Layer A-E model and addresses within-layer promotion. Worth a memory-architecture
   spec update?

2. **Adopt the four-tier visibility model (private / inspectable / shared / canonical) for Layer D investigation
   memory?** DEC-0052 commits to multi-agent shared state but doesn't yet specify the access-control vocabulary. The
   Prologue model is directly portable.

3. **FPEF-style 4-phase gate discipline for Phase 3 Worker dispatch.** The pattern (Find → Prove → Evidence → Fix with
   explicit gates) is a portable discipline for Worker dispatch. Worth a Phase 3 spawner spec inclusion?

4. **Recovery-manager primitive for Phase 3.** Graduated escalation (warn → retry → roll back → halt) is a robust
   failure model. Worth scoping in the Phase 3 spawner spec?

5. **Confidence-threshold calibration.** The Prologue thresholds (0.5, 0.7, 0.9) for promotion to PROJECT / OVERVIEW /
   CORE are domain-defaults. For Linus's Layer C consolidation, what are the right thresholds? This is an empirical
   question for Phase 2+ implementation.

6. **Bun-spawn-Python-via-JSON-protocol cross-language bridge as a Phase 5+ template.** For any Phase 5+ TypeScript-based
   Linus component, this bridge pattern is portable. Worth flagging in DEC-0027's multi-language stance as the
   reference cross-language-bridge pattern?

7. **Read the FPEF spec directly if available.** The Prologue CLAUDE.md references "FPEF v2.0 spec:
   `../cldcde/projects/fpef/FPEF-FIRST-PRINCIPLES-EXECUTION-FRAMEWORK.md`" — adjacent-codebase only. Worth attempting
   to locate the FPEF spec publicly?
