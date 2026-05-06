## DEC-0052 — Investigation memory: Layer D (five-layer memory pillar)

**Date:** 2026-05-06 **Status:** accepted

**Context.** The four-layer memory pillar (Layer A: intra-step latent; Layer B: within-session scratchpad; Layer C:
cross-session episodic; Layer D: semantic knowledge) identified in DEC-0028 and specified in
`docs/specs/memory-architecture.md` lacks a layer for task-scoped, multi-agent, single-investigation-lifetime memory.
Three systems in the corpus occupy this gap: Kosmos's world model (shared state maintained across a full research
investigation), Sketch2Simulation's intermediate representation (IR passed between pipeline stages within one
orchestration run), and HKUST QuantAgent's context buffer (strategy + reasoning log shared between planner and executor
across one trading cycle). Dan confirmed 2026-05-06 that investigation memory is a genuinely distinct layer, not a
sub-type of episodic memory. Closes **S13**.

**Decision.** Add **Layer D — Investigation memory** to the memory pillar between cross-session episodic (Layer C) and
semantic knowledge (formerly Layer D, now Layer E). Rename the semantic-knowledge layer to Layer E throughout all
specifications and code. The total pillar becomes five layers (A–E).

Layer D definition:

- **Lifetime.** Created when a multi-agent investigation spawns; archived to Layer C (episodic store, tagged
  `investigation_id`) when the investigation closes. GC policy: investigations older than 30 days without activity are
  automatically archived.
- **Access pattern.** All agents participating in a given investigation share a single investigation context. Individual
  agents write their outputs into the shared context; any agent can read the full context at any point in the
  investigation. This is distinct from Layer B (per-session scratchpad, not shared across agents) and Layer C (archived,
  not live during execution).
- **Substrate (Phase 3).** SQLite table in `~/.linus/investigations.db` with `investigation_id` as the primary
  partition key, `agent_id`, `role_id` (from DEC-0050), `entry_type`, `content_hash`, and `content` fields. Shares the
  same hash-and-parent-pointer discipline as Layer C.
- **Read/write API.**

```
linus.memory.investigation.create(investigation_id, task_id, participating_roles)
linus.memory.investigation.write(investigation_id, agent_id, entry_type, content)
    → content_hash
linus.memory.investigation.read(investigation_id, query?, limit?)
    → list of entries, temporally ordered
linus.memory.investigation.close(investigation_id)
    → archives to Layer C as a single episodic record with summary + all leaf hashes
```

**Consequence.** The memory-architecture.md spec is updated to five layers (A–E). Layer E is the new name for semantic
knowledge throughout all code and documentation. Investigation memory is Phase 3 substrate implementation; Phase 2
exposes only the API shape. The cross-cutting contracts table gains a Layer D column. The `memory_mode` router primitive
(DEC-0031) is unchanged at Phase 2; a new `investigation_stateful` mode that includes Layer D in prefix loading is
deferred to Phase 3 design.
