## DEC-0005 — Maestro/Worker protocol starts OpenAI-compatible, may migrate to MCP

**Date:** 2026-04-22 **Status:** accepted (Phase 3 MCP-revisit portion superseded by DEC-0018; protocol-surface portion
amended by DEC-0056)

**Context.** Communication protocol between Maestro (hosted Claude) and Workers (local models). Options: MCP,
OpenAI-compatible HTTP, or a direct SDK approach.

**Decision.** Start with **OpenAI-compatible HTTP** as the protocol for Maestro/Worker and front-end/backend. It's what
Ollama, pmetal, and LM Studio all speak; it's what Cline and openclaw already support; it's what KnowledgeBase's
Haystack integration already uses. **Revisit MCP for adoption in Phase 3** once tool-use patterns settle and the benefit
of MCP's structured context model becomes clearer.

**Consequence.** Low initial friction. Clear migration path. MCP-specific features (cross-server context sharing,
structured resources) are deferred but not precluded.

**Amendment 2026-05-16 — protocol surface extended (DEC-0056).** The OpenAI-only commitment is amended by
[`DEC-0056`](0056-orchestration-speaks-openai-and-anthropic-compat.md): Phase 2a's orchestration layer exposes **both**
an OpenAI-compatible surface (this ADR's original commitment) **and** an Anthropic Messages-compatible surface. Three
independent confirming signals — Letta (`repo-notes/Letta.md`), Kimi-K2 (`paper-notes/Kimi-K2-2507.20534.md`), and Goose
(`repo-notes/goose.md`) — established a dual-protocol norm in the open-source agent ecosystem during the 2026-05-10 PR
30 fold-in pass. The OpenAI surface remains the substrate; the Anthropic surface is a sibling endpoint family sharing
the underlying routing, sandbox, and audit-log machinery. See DEC-0056 for the full rationale and the per-protocol
translation contract.
