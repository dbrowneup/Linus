## DEC-0045 — fastmcp as the default MCP framework for in-house Linus servers

**Date:** 2026-05-06 **Status:** accepted

**Context.** DEC-0018 adopted MCP as the extensibility substrate. Six repos in the cloned collection ship MCP servers
(pmetal-mcp, openclaw, py3plex_mcp, agentmemory's 51-tool MCP, keppi, fastmcp as the underlying framework). The G6
synthesis (`docs/syntheses/repo-clusters/g6-mcp-tools.md`) canonicalizes the verdict: in-house Linus MCP servers build
on fastmcp's decorator API and middleware pipeline, not parallel to it. CLAUDE.md already records this as resolved at
Phase 2a planning time. This ADR closes the framework-default sub-question and the Phase 1f fastmcp evaluation
deliverable. Closes **S3**.

**Decision.** fastmcp is the default MCP framework for all in-house Linus MCP servers. In-house servers use
fastmcp's `@mcp.tool()` decorator API and its middleware pipeline. External servers consumed as MCP clients
(pmetal-mcp, keppi, ontomics, codesight) are adopted as-is without re-implementation. The Phase 2a tool registry is
MCP-shaped from the start, with fastmcp as the authoring primitive. Paper-qa's wrapper (DEC-0044) is the first
in-house server to build on fastmcp.

**Consequence.** All Phase 2a tool-registry work is MCP-shaped from day one. The six external repos that already ship
MCP servers are drop-in compatible. In-house server authoring is a single `@mcp.tool()` decorator plus a middleware
registration, matching the pattern established in the G6 synthesis as the highest-leverage starting point.
