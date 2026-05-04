## DEC-0020 — Linus orchestration scope: sandbox + KB + MCP registry + audit; not task-decomposition primitives

**Date:** 2026-05-03 **Status:** accepted (refines DEC-0002)

**Context.** The skills synthesis correctly Algorithm-checks the custom orchestration question (Tier 2 #13). Reaffirming
DEC-0002's harness-agnostic backend commitment is sound — but the scope of "what Linus's orchestration layer actually
implements" needs explicit narrowing to avoid re-implementing primitives that off-the-shelf tools (Task Master AI,
claude-squad, autoresearch) already do well.

**Decision.** Linus's custom orchestration layer scope = sandbox enforcement + KB integration + MCP-shape tool
registry + audit log. It does **NOT** re-implement task decomposition primitives. Task Master AI's PRD→tasks pattern,
claude-squad's parallel-terminal pattern, and autoresearch's keep-or-revert loop are adopted as **skills** inside
Linus's skill registry, not re-built from scratch. Validated via **new Phase 1f deliverable**: comparative evaluation of
Task Master AI + claude-squad vs. custom Linus prototype vs. pmetal-MCP-as-orchestrator on a real Phase 2 task spec
(e.g., "ingest 5 papers from `context/papers/` through KB pipeline, produce summaries, surface in chat UI").

**Consequence.** Custom layer earns its keep on Linus-specific concerns; ecosystem tools handle the generic. Phase 1f
delivers empirical evidence rather than assumption. DEC-0002 holds; this DEC adds bounding scope.
