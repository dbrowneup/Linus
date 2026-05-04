## DEC-0005 — Maestro/Worker protocol starts OpenAI-compatible, may migrate to MCP

**Date:** 2026-04-22 **Status:** accepted (Phase 3 MCP-revisit portion superseded by DEC-0018)

**Context.** Communication protocol between Maestro (hosted Claude) and Workers (local models). Options: MCP,
OpenAI-compatible HTTP, or a direct SDK approach.

**Decision.** Start with **OpenAI-compatible HTTP** as the protocol for Maestro/Worker and front-end/backend. It's what
Ollama, pmetal, and LM Studio all speak; it's what Cline and openclaw already support; it's what KnowledgeBase's
Haystack integration already uses. **Revisit MCP for adoption in Phase 3** once tool-use patterns settle and the benefit
of MCP's structured context model becomes clearer.

**Consequence.** Low initial friction. Clear migration path. MCP-specific features (cross-server context sharing,
structured resources) are deferred but not precluded.
