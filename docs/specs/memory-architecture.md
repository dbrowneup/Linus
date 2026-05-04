# Memory Architecture (Phase 2 spec)

**Status:** v0 — drafted 2026-05-03 as part of the memory-pillar planning roll-up, alongside
[DEC-0028](../adr/0028-memory-architecture-phase2-pillar.md) through
[DEC-0043](../adr/0043-memory-mode-finetuning-targets-phase6.md). The spec is the implementation contract for the Phase
2 memory pillar; it will be amended as Phase 1c+ measurements land and as the Phase 6+ substrate experiments resolve.

## What this spec is

The architectural contract for **memory in Linus**: what it is, how it is layered, how Workers and the orchestration
layer talk to it, what substrates each layer commits to in Phase 2, and where the substrate choice is deliberately left
open for later. The spec is the prerequisite for Phase 2a orchestration backend implementation (per DEC-0028); other
Phase 2 work proceeds in parallel.

The argument for promoting memory to a Phase 2 first-class deliverable lives in
[the memory synthesis](../syntheses/memory-synthesis.md). This spec assumes that argument and translates it into
implementation contracts.

## Foundations: two requirements, four sub-requirements

Garrison's universality theorem (2412.17794) names two requirements jointly necessary and sufficient for Turing-complete
computation:

1. **Recursive state maintenance** — the system can read its current state, apply an update, and durably keep the new
   state for the next step.
2. **Reliable history access** — the system can:
   - **Reference** any prior state.
   - **Distinguish** different states unambiguously.
   - **Maintain temporal order** between states.
   - **Guarantee integrity** of stored states.

Memory architecture in Linus is the orchestration-layer machinery that satisfies these requirements end-to-end across
whatever Worker model is dispatched. Single-pass transformers satisfy neither (TC0 ceiling per Merrill & Sabharwal); the
orchestration layer's job is to externalise what the model cannot internalise.

## The four memory layers

Memory in Linus decomposes into four layers, named for what they hold and how durable that holding is. The same
`linus.memory.*` API shape serves all four; substrate choice is hidden behind the API so Workers cannot tell which layer
answered. Layers compose in retrieval — a single dispatch's prefix may pull from any combination, mediated by the
`memory_mode` router primitive (DEC-0031).

### Layer A — Intra-step latent state

**What it holds.** The continuous reasoning carry inside a single Worker forward pass — the transformer's hidden state
at step `t` becoming part of the conditioning at step `t+1`. Today, in practice, this is whatever the underlying model
architecture's hidden state happens to be: opaque, discarded between turns, never named in our planning until now.

**Substrate (Phase 2).** Whatever the dispatched Worker's architecture provides natively. No Linus-side substrate
decision required at v0; the layer is named so the architecture conversation is legible, not so it is actively
manipulated. The KV-cache continuity requirement from DEC-0036 is the sole Phase 2 commitment that touches Layer A — it
ensures the within-call hidden state survives between turns of the same session.

**Substrate (Phase 6+ candidates).** Coconut-style latent recurrence (DEC-0042) and minGRU-style minimal recurrence
(DEC-0038) both modify what gets carried at this layer. The Phase 1 spikes for those substrates will inform whether
Linus actively manages Layer A in Phase 6+ or leaves it transparent.

**Read/write API.** None at v0. Layer A is implicit in the underlying inference call; the orchestration layer treats it
as an architectural property of the Worker, not a directly addressable resource.

### Layer B — Within-session scratchpad memory

**What it holds.** Reasoning traces, intermediate tool calls and outputs, and within-task continuity inside a single
session. Per DEC-0030, scratchpad is a first-class durable artifact — the o1 anti-pattern (silently truncating reasoning
between turns) is forbidden as a Worker protocol non-conformance condition.

**Substrate (Phase 2).** SQLite + content hashes + git-as-persistence, shared with Layer C — the same DEC-0029 episodic
store carries both within-session scratchpad and cross-session episodic records, with `session_id` tagging the boundary.
Each turn produces a two-segment record per DEC-0030: `segment="scratchpad"` (the reasoning trace) and
`segment="answer"` (the final response). Tool outputs are a third segment, `segment="tool_output"`. All three are
addressable, hashed, and linked by parent-pointer.

**Read/write API.**

```
linus.memory.scratchpad.write(session_id, turn_id, parent_turn_id,
                              segment, content, trust_level, tags)
linus.memory.scratchpad.recall(session_id) → recent turns of current session
linus.memory.scratchpad.recall_turn(session_id, turn_id) → exact turn
linus.memory.scratchpad.recall_segment(session_id, turn_id, segment)
                       → scratchpad / answer / tool_output of that turn
```

Implemented as a thin facade over the DEC-0029 episodic substrate (Layer C); the `scratchpad` API exists so Workers and
the orchestration layer can think about within-session state without coupling to the episodic substrate's full surface.

### Layer C — Cross-session episodic memory

**What it holds.** The assistant's own durable history of prior tasks, decisions, tool outputs, and reasoning traces,
organised across sessions and tagged by project. This is the layer Linus's prior planning lacked entirely; the Garrison
framework argues it is upstream of every concrete use case rather than downstream of one.

**Substrate (Phase 2).** Per DEC-0029: SQLite (single-file embedded DB at `~/.linus/episodic.db`) + SHA-256 content
hashes per record + git as persistence layer underneath. Record shape:

```
(session_id, turn_id, parent_turn_id, timestamp, role, segment,
 content_hash, content, trust_level, tags)
```

The shape absorbs scratchpad records (Layer B), tool outputs, and roll-up summaries (DEC-0039) without schema migration.
CRISPR-style temporal weighting (recent ranked higher in retrieval, ancient retrievable on demand) is a retrieval-side
concern over this substrate, not a separate substrate.

**Substrate (Phase 6+ candidate).** Per DEC-0029 + DEC-0037: TTT-style parametric consolidation (Akyürek-style per-task
LoRA fitted on session transcripts), gated on the Phase 1c TTT viability spike. If the spike passes the
under-5-minutes-per-task wall-clock decision rule, TTT graduates to a Phase 6 substrate experiment for episodic-memory
consolidation; otherwise the v0 SQLite+git substrate stands alone.

**Substrate (Phase 8 architectural option).** Hybrid graduation pattern (text → LoRA after sufficient repeated access),
gated on the Phase 6 spike result.

**Read/write API.**

```
linus.memory.episodic.record_turn(...)           — single-turn write
linus.memory.episodic.record_consolidation(...)  — multi-turn roll-up
                                                   (Phase 6+ if TTT graduates)

linus.memory.episodic.recall(query, project_tag, limit, mode)
   → ranked records matching query, scoped to project, temporally weighted
linus.memory.episodic.recall_recent(session_id?, project_tag?, n)
   → most recent n records (session- or project-scoped)
linus.memory.episodic.recall_by_tag(tag, project_tag)
linus.memory.episodic.recall_by_content(content_hash | substring)
linus.memory.episodic.recall_full(parent_id)
   → rehydrate all leaves under a parent (per DEC-0039 hybrid schema)

linus.memory.episodic.prune_archived(...)        — admin
```

Substrate variation (SQLite-only v0; future hybrid) is hidden behind this API; Workers cannot tell which mechanism
answered.

### Layer D — Semantic / knowledge memory

**What it holds.** Durable shared factual knowledge — Dan's papers, notes, corpora, ontologies. Already substantially
served by KnowledgeBase ([modules/KnowledgeBase/](../../modules/KnowledgeBase/)). The Garrison framing argues
KnowledgeBase is part of the memory pillar, not a separate "RAG feature."

**Substrate (Phase 2).** The dual KB substrate per DEC-0015: RDF (rdflib + optional Oxigraph) and property graph
(networkx). The [KB-spec items](../specs/kb/) handle the KB-side details; this spec specifies only the Layer D contract
from the memory-pillar perspective.

**Read/write API.** The existing KB tool families per DEC-0015:

```
linus.knowledge.sparql.*    — RDF / SPARQL queries
linus.knowledge.graph.*     — property-graph traversal
```

Memory-pillar uniformity requires that the dispatch-layer prefix-loading machinery treats Layer D retrievals the same
shape as Layer B/C retrievals — a Worker should not be able to tell whether a fact came from its own scratchpad, a prior
session, or KnowledgeBase. The `memory_mode` router primitive (DEC-0031) governs which combination is loaded as prefix;
the KB API supplies the records.

## Cross-cutting contracts

### Sub-requirement-to-mechanism mapping

| Sub-requirement | Layer A                        | Layer B                              | Layer C                                               | Layer D                                   |
| --------------- | ------------------------------ | ------------------------------------ | ----------------------------------------------------- | ----------------------------------------- |
| Addressability  | (transparent)                  | `(session_id, turn_id, segment)`     | `(session_id, turn_id, segment)` rowid + content_hash | KB entity URI / graph node id             |
| Disambiguation  | (transparent)                  | content_hash                         | content_hash + tags                                   | KB schema + identity per DEC-0015         |
| Temporal order  | KV-cache continuity (DEC-0036) | monotonic timestamp + parent-pointer | monotonic timestamp + parent-pointer                  | KB ingest timestamp + version             |
| Integrity       | (transparent)                  | SHA chain + audit log                | SHA chain + git history                               | KB content hashing per LLM Wiki synthesis |

### The router-side contract: `memory_mode` and prefix loading

DEC-0031 specifies three `memory_mode` values; this section is the implementation contract for what each loads as Worker
prefix.

`stateless`: Layer D only. KB context retrieved fresh; no scratchpad, no episodic prefix. Per-layer cap allocation per
DEC-0032: task spec ≤ 8K, KB context ≤ 6K, system + format ≤ 2K.

`session_stateful`: Layers B + D. Current session's scratchpad and answer history loaded as prefix (most recent first,
CRISPR-style temporal weighting). Default for multi-turn coding work. Per-layer cap allocation: task spec ≤ 4K, KB
context ≤ 4K, session prefix ≤ 6K, system + format ≤ 2K.

`project_stateful`: Layers B + C + D. Current session + relevant prior-session episodic records, retrieved by project
tag. Per-layer cap allocation: task spec ≤ 4K, KB context ≤ 3K, episodic prefix ≤ 7K, system + format ≤ 2K.

The dispatch layer enforces the cap per DEC-0032. Overflow routes through the episodic store via the
summarization-or-retrieval contract: dropped content stays in Layer C at full fidelity; the router applies a
deterministic summary in place of the dropped detail; the caller is told via dispatch metadata what was elided so a
follow-up `recall` can rehydrate.

### The router-side contract: `cot_budget` and reasoning retention

DEC-0031 specifies three `cot_budget` regimes; this section is the implementation contract for retention behavior.

`logarithmic` (default 256 reasoning tokens, truncate-on-cap, retention-best-effort): the scratchpad segment is recorded
in Layer B if the Worker emits one, but the contract does not require full retention. Right for lookup-shaped tasks
where the chain is short.

`linear` (default 4096 reasoning tokens, full retention required): the scratchpad segment is captured at full fidelity
in Layer B and addressable for follow-up `recall`. Phase 2 default for any task the router cannot classify confidently.

`polynomial` (default 16384 reasoning tokens, full retention required, explicit caller request): same retention contract
as linear, with an explicit confirmation gate before dispatch. No automatic dispatch into this regime in Phase 2.

The defaults are calibrated per Worker via the DEC-0033 CoT-gap fingerprint: a Worker with a small CoT-gap may need
higher caps; a Worker with a large CoT-gap may saturate earlier.

### The Worker-side contract: scratchpad durability

Per DEC-0030, every Worker integration carries a `scratchpad_durability` capability tag in the model registry: `native`
(full reasoning capture possible), `partial` (capture possible but model truncates internally — flag as risk),
`non_conformant` (reasoning structurally unavailable, e.g. o1 with hidden reasoning tokens). The router refuses
`session_stateful` and `project_stateful` dispatch to `non_conformant` Workers; `stateless` calls remain permitted.

Per DEC-0036, every Worker backend used for stateful dispatch must preserve KV cache across turns within a session.
Backends are evaluated against this requirement at adoption time; failures trigger a
`scratchpad_durability=non_conformant` registry tag.

### The audit-log contract

Per DEC-0030/0031/0032, the audit log at `~/.linus/audit.jsonl` (append-only) records, per dispatch:

- The dispatch metadata:
  `(session_id, turn_id, worker_id, cot_budget, memory_mode, context_used_tokens, context_capped, context_overflow_action, per_layer_breakdown)`.
- The event of each scratchpad / answer / tool_output write with its hash and turn id.
- Any `context_cap_override` annotation (the explicit-bypass mechanism per DEC-0032 — bypass is intentionally noisy in
  audit so the "stuff everything in context" pattern is detectable).

The audit log is the data source for Phase 1c+ benchmarks correlating budget/mode with outcome quality, completion time,
and cost. It is also the integrity backstop: if the SQLite episodic store is corrupted or rebuilt, the audit log carries
the cryptographic chain that lets durability claims be verified after the fact.

## Phase 2 implementation deliverables

In execution order:

1. **Schema and storage** — `~/.linus/episodic.db` SQLite schema with the DEC-0029 record shape. Migration script.
   Hash-computation helpers.
2. **Audit log** — `~/.linus/audit.jsonl` append-only writer with the contract above.
3. **`linus.memory.episodic.*` tool family** — read and write APIs as specified above. `recall_full` and the hybrid
   leaf+summary semantics from DEC-0039.
4. **`linus.memory.scratchpad.*` thin facade** — over the episodic substrate, exposing the within-session API.
5. **Dispatch-layer prefix loader** — reads `memory_mode`, applies cap per DEC-0032, summarisation-or-retrieval on
   overflow, dispatch metadata reporting.
6. **Router primitive plumbing** — `cot_budget` and `memory_mode` as first-class fields in the dispatch struct; explicit
   caller annotation in v0.
7. **Worker registry** — `scratchpad_durability` capability tag; per-Worker `cot_budget` overrides populated by the
   DEC-0033 fingerprint measurement.
8. **CoT-gap fingerprint runner** — 50-item MultiArith-style smoke test per DEC-0033; output written to registry and
   benchmark results.
9. **ARC-AGI memory diagnostic** — 50–100 public-eval tasks, run twice (stateless vs. session_stateful) per DEC-0035;
   output is the memory-thesis-as-a-number measurement.

Items 1–7 are Phase 2 prerequisites for the orchestration backend per DEC-0028. Items 8–9 are Phase 1c benchmark
deliverables that feed Phase 2 calibration.

## What this spec deliberately leaves open

- **Layer A active management** (Coconut-style latent recurrence, minGRU-style minimal recurrence) — Phase 6+ pending
  the DEC-0038 and DEC-0042 spikes.
- **Layer C parametric consolidation** (TTT-style adapter consolidation of session transcripts) — Phase 6 spike
  conditional on the DEC-0037 Phase 1c viability test.
- **Hybrid Layer C graduation** (text → LoRA after repeated access) — Phase 8 architectural option per DEC-0029, gated
  on the Phase 6 spike.
- **Learned summarisation** — DEC-0039 keeps the v0 summary function deterministic and structural; a learned summarizer
  is Phase 6+ once a fine-tuned candidate exists.
- **Faithfulness audit of stored reasoning** — DEC-0040 defers to Phase 3 with an explicit trigger condition.
- **Per-task automatic classification into `cot_budget` and `memory_mode`** — Phase 2 ships with explicit caller
  annotation; automatic classification is Phase 3+ work.
- **The 16K in-context cap moves up over time** — DEC-0032 makes the cap a floor we move with confidence, not a
  permanent ceiling. The episodic store, overflow contract, and explicit-bypass mechanism stay regardless.

## Memory budget accounting (forward pointer)

ARCHITECTURE.md gains a "Memory Budget Accounting" section per DEC-0028 naming memory budget as a first-class
architectural quantity tracked per session and per task. Reference upper bound: o3 at ~$1.15M for 91.5% on ARC-AGI-1
(the cost of brute-forcing memory reliability through compute). Reference lower bound: human with pen, paper,
sandwiches. Linus's design target sits in the middle: tens of dollars of electricity per day on a single M1 Max, with
the architectural pressure to narrow the gap to the lower bound through this spec's substrate choices, the discipline
encoded in DEC-0030/0031/0032, and the measurements from DEC-0033/0035.

The audit-log telemetry from DEC-0030/0031/0032 supplies the data that makes implicit memory-cost choices ("we'll just
retry until it works", "let's pad the context budget") legible as memory-budget decisions rather than invisible cost.

## ADR cross-references

The 16 ADRs that ratify this spec:

- [DEC-0028](../adr/0028-memory-architecture-phase2-pillar.md) — Phase 2 pillar promotion + memory budget accounting
- [DEC-0029](../adr/0029-episodic-memory-substrate.md) — Layer C substrate (SQLite + content hashes + git)
- [DEC-0030](../adr/0030-scratchpad-first-class-artifact.md) — Scratchpad as first-class artifact; o1 anti-pattern
  forbidden
- [DEC-0031](../adr/0031-router-primitives-cot-budget-memory-mode.md) — `cot_budget` and `memory_mode` router primitives
- [DEC-0032](../adr/0032-in-context-window-cap-policy.md) — In-context window cap policy
- [DEC-0033](../adr/0033-cot-gap-fingerprint-registry-property.md) — Per-Worker CoT-gap fingerprint
- [DEC-0034](../adr/0034-worker-size-vs-cot-length-comparison.md) — Phase 1c worker-size-vs-CoT-length comparison
- [DEC-0035](../adr/0035-arc-agi-as-memory-diagnostic.md) — ARC-AGI as memory diagnostic
- [DEC-0036](../adr/0036-kv-cache-continuity-architectural-constraint.md) — KV-cache continuity
- [DEC-0037](../adr/0037-ttt-apple-silicon-viability-spike.md) — TTT viability spike
- [DEC-0038](../adr/0038-mingru-mlx-port-spike.md) — minGRU MLX port spike
- [DEC-0039](../adr/0039-episodic-schema-hybrid-leaf-summary.md) — Episodic schema for multi-step tasks
- [DEC-0040](../adr/0040-faithfulness-audit-deferred.md) — Faithfulness audit deferred
- [DEC-0041](../adr/0041-mingru-bitnet-phase8-research-direction.md) — minGRU + BitNet Phase 8 research direction
- [DEC-0042](../adr/0042-coconut-phase6-substrate-experiment.md) — Coconut Phase 6 substrate experiment
- [DEC-0043](../adr/0043-memory-mode-finetuning-targets-phase6.md) — Phase 6a memory-mode-aware fine-tuning targets

Synthesis input: [docs/syntheses/memory-synthesis.md](../syntheses/memory-synthesis.md). Practitioner anchor:
[Mughal context-window article](../../context/notes/Why%20Claude%20Gets%20Dumber%20the%20Longer%20Your%20Session%20Run.txt).
Theoretical anchor: [Garrison synthesis](../../context/notes/garrison_memory_makes_computation_universal.md).
