## DEC-0018 — Adopt MCP as the extensibility substrate

**Date:** 2026-05-03
**Status:** accepted (supersedes "revisit MCP for adoption in Phase 3" portion of DEC-0005)

**Context.** cline, openclaw, and pmetal all speak MCP. DEC-0005 deferred MCP
adoption to a Phase 3 revisit. Two new factors changed the calculation: (a) pmetal
ships a 45-tool MCP server already, (b) the harness-plurality role designations
(DEC-0017) make MCP-as-tool-registry economically dominant — register tools once,
they show up in all harnesses without per-harness glue.

**Decision.** Adopt MCP as Linus's tool-registration substrate. Phase 2 tool registry
is built MCP-shape from the start (so Phase 3 is exposure, not refactor). Linus
exposes a Linus-native MCP server AND consumes external MCP servers via a client
adapter. **pmetal's 45-tool MCP server is the first external integration target.**
Evaluate `fastmcp` (`jlowin/fastmcp`) for the server-side construction.

**Consequence.** OpenAI-compatible HTTP remains the chat-completions surface
(per DEC-0005). MCP is layered on top for tool registration and external tool
consumption. Phase 2 tool registry implementation choice (custom, fastmcp, or other)
is its own sub-decision.
