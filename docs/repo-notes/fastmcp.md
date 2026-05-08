# fastmcp (`PrefectHQ/fastmcp`)

## 1. Purpose and scope

FastMCP is **the** Python framework for building Model Context Protocol servers and clients — Apache-2.0, authored by
Jeremiah Lowin (`jlowin`), now maintained by Prefect. The repo's own claim, easy to verify by package counts, is that
FastMCP 1.0 was folded into the official `mcp` Python SDK in 2024 and that the standalone v2.x project ships some
version of FastMCP in roughly 70% of MCP servers across all languages. PyPI name `fastmcp`; current dependency line is
`mcp>=1.24.0,<2.0`, so FastMCP wraps and extends the bare SDK rather than replacing it. For Linus this is the named
candidate in the Phase 1f deliverable ("evaluate fastmcp before committing to MCP server construction technology") and
the most likely substrate for the Phase 2 KB tool registry under DEC-0029. Almost every other Group 6 repo (ontomics,
py3plex's MCP, agentmemory's 51-tool MCP, the openclaw and pmetal MCP servers) is built on top of it.

## 2. Architecture summary

A single Python package (`src/fastmcp/`) organized around three pillars: `server/` (the `FastMCP` class plus `auth/`,
`middleware/`, `apps/`, `proxy.py`, `transforms/`, `openapi/`), `client/` (a full async `Client` with its own `auth/`
and a transports layer), and the four MCP component types as top-level modules: `tools/`, `resources/`, `prompts/`, plus
`apps/` for FastMCP's interactive-UI extension. The public ergonomics are decorator-driven on a single `FastMCP`
instance: `@mcp.tool` introspects type hints and docstrings to produce JSON schema, validation, and documentation
automatically; `@mcp.resource("uri://path")` registers static resources; `@mcp.resource("uri://{var}")` registers a
resource template (URI variables become function parameters); `@mcp.prompt("name")` registers prompts. Tools can also be
added imperatively with `server.add_tool(callable)`. `FastMCP.as_proxy(other_server)` wraps any MCP server (in-memory,
stdio, HTTP) and re-exposes its surface — the foundation of FastMCP's mounting/composition story. Transports are
declared as `Transport = Literal["stdio", "http", "sse", "streamable-http"]` and chosen at `mcp.run()` time; HTTP rides
on `uvicorn` + `websockets` + `python-multipart`, with `streamable-http` being the modern bidirectional default. Auth is
a first-class subsystem: `server/auth/` ships JWT issuer, OAuth proxy, OIDC proxy, redirect validation, SSRF protection,
and a CIMD (client-initiated metadata discovery) handler — built on `authlib`. Middleware is a real pipeline —
`server/middleware/` includes `caching`, `rate_limiting`, `response_limiting`, `timing`, `error_handling`, `logging`,
`authorization`, `ping`, `tool_injection`, `dereference` — composable around tool/resource/prompt invocation. A `cli`
(`fastmcp = "fastmcp.cli:app"`, built on `cyclopts`) gives you `fastmcp run`, `fastmcp dev`, etc. The `openapi/` package
generates an MCP server from an OpenAPI spec. Optional extras: `apps` (Prefab UI for in-chat interactive components),
`tasks` (pydocket-backed background tasks), per-provider clients (`anthropic`, `openai`, `gemini`, `azure`), and
`code-mode` (`pydantic-monty`).

## 3. What's reusable in Linus

Effectively all of it, as a library dependency. The Phase 2 KB tool registry can be a `FastMCP` instance with one
`@mcp.tool`-decorated function per KnowledgeBase capability (semantic search, hybrid retrieval, paper fetch, Cypher
query, citation graph walk), one `@mcp.resource("kb://paper/{id}")` template per resource type, and stdio transport for
local-only Maestro/Worker calls. For Phase 3 parallel-Worker fan-out, `FastMCP.as_proxy()` lets Linus mount per-Worker
MCP servers under a single endpoint. Auth and rate-limiting middleware become relevant when openclaw is exposed beyond
localhost in Phase 5; the OpenAPI generator can wrap any HTTP service Dan already has into an MCP surface for free. **Vs
the bare `mcp` SDK:** the bare SDK gives you protocol primitives and a low-level server; FastMCP gives you the decorator
API, automatic JSON-schema generation from type hints, four transports behind one `run()` call, a real middleware
pipeline, OAuth/JWT/OIDC out of the box, in-memory and remote proxying, and an OpenAPI ingester. **Vs the in-house MCP
servers in pmetal-mcp, openclaw-mcp, py3plex_mcp, agentmemory:** those are application servers — they _use_ FastMCP (or
its peers) to expose a specific tool surface; FastMCP itself is the framework underneath. Linus should not build a fifth
in-house MCP layer; it should build a FastMCP server whose tool functions call into Linus's KB and orchestration code.

## 4. What's inspiration only

The decorator + introspection pattern (`@mcp.tool` on a typed function → schema, validation, docs) is the right shape
for Linus's _internal_ tool registry too, even where MCP isn't the wire protocol. The `as_proxy` / mounting story is the
cleanest answer to "how do I compose 5 MCP servers into one endpoint a harness sees" — worth copying the _idea_ if Linus
ever needs a non-MCP tool composer. The middleware list (`caching`, `rate_limiting`, `response_limiting`, `timing`,
`tool_injection`) is a useful shopping list for what an orchestration layer eventually wants regardless of protocol.

## 5. What's incompatible or out of scope

Nothing major. The dependency footprint is real — `httpx`, `uvicorn`, `websockets`, `pydantic`, `authlib`, `rich`,
`cyclopts`, `opentelemetry-api`, `watchfiles`, `griffelib`, `py-key-value-aio` — and that's before optional extras. For
a strictly minimal stdio-only KB tool server this is heavier than calling the bare `mcp` SDK directly; the trade is
worth it once a second feature (auth, middleware, a second transport, proxying, OpenAPI ingest) shows up. The Prefab UI
`apps` extra and the Prefect Horizon enterprise gateway are out of scope for a private local assistant. Python ≥3.10 is
fine (linus env is 3.12). License is Apache-2.0 — clean for both library use and any future vendoring.

## 6. Recommendation: **Integrate**

Adopt FastMCP as Linus's MCP server framework in Phase 2. The Phase 1f deliverable is short: `pip install fastmcp`,
write a 30-line server that exposes one KnowledgeBase tool over stdio, point Claude Desktop or Cline at it, confirm a
round-trip, and write the verdict as an ADR (next free `DEC-NNNN`, slug `mcp-framework`). If anything surprising
surfaces — startup latency, schema-generation edge cases on Linus's tool signatures, transport quirks under
Maestro/Worker concurrency — record it and reconsider; otherwise commit. Do not build an in-house MCP server layer.

## 7. Questions for Dan

1. **Stdio vs streamable-http for Phase 2.** Local-only Maestro/Worker calls are fine over stdio, but the moment a
   second harness wants the same KB tools (Cline + Claude Code + openclaw simultaneously), HTTP becomes simpler than
   spawning N stdio children. Default to `streamable-http` on `localhost:<port>` from day one, or start stdio and
   migrate?
2. **Tool granularity.** FastMCP encourages many small typed tools. KnowledgeBase has natural verbs (semantic_search,
   hybrid_search, get_paper, walk_citations, run_cypher) — does each become its own `@mcp.tool`, or does Linus expose
   one parameterized `kb_query` and dispatch internally? The first is more legible to harnesses; the second is closer to
   how DEC-0029 frames the registry.
3. **Auth posture.** Phase 2 is single-user localhost; auth is unneeded. Phase 5b openclaw might expose Linus on the LAN
   for Dan's iPad. Plan to enable FastMCP's JWT/OAuth subsystem then, or stay localhost-only and tunnel via SSH?
4. **Proxy/composition.** If pmetal-mcp's 45 tools are useful, `FastMCP.as_proxy(pmetal_server)` lets Linus re-expose
   them under its own endpoint with Linus middleware applied. Worth pursuing in Phase 3, or keep pmetal-mcp as a
   separate endpoint Maestro picks explicitly?
5. **Dependency weight.** FastMCP pulls ~20 runtime deps including `authlib`, `opentelemetry`, `griffelib`,
   `watchfiles`. Acceptable for the Linus env, or do we want a thinner alternative (the bare `mcp` SDK) for a
   minimal-deps profile in case of shipping a packaged Linus binary later?
