## DEC-0056 — Orchestration speaks OpenAI- and Anthropic-compatible HTTP

**Date:** 2026-05-16 **Status:** accepted (amends DEC-0005)

**Context.** DEC-0005 committed Linus to OpenAI-compatible HTTP as the v0 wire protocol for the Maestro/Worker and
front-end/backend surface. That commitment was made when the open-source agent ecosystem was effectively single-protocol
on the wire and Ollama, pmetal, LM Studio, Cline, and openclaw all spoke OpenAI-compat. The landscape has since shifted.
Three independent confirming signals — surfaced by the 2026-05-10 PR 30 fold-in pass — now point at a dual-protocol
norm:

1. **Letta** (`repo-notes/Letta.md` §3, §7-Q8) ships both an OpenAI-compatible `/v1/chat/completions` endpoint and an
   Anthropic-compatible `/v1/anthropic/...` endpoint (`server/rest_api/routers/v1/anthropic.py`). The native Letta API
   is the stateful agent path; the chat-completions endpoints are the stateless compatibility shims.
2. **Kimi-K2** (`paper-notes/Kimi-K2-2507.20534.md` §Key results, §What's reusable) deploys an Anthropic-compatible API
   at `platform.moonshot.ai` alongside an OpenAI-compatible surface, with the documented temperature-mapping quirk
   (`real_temperature = request_temperature × 0.6`) flagged as a cautionary semantic-translation tax.
3. **Goose** (`repo-notes/goose.md` §1, §3) ships full Anthropic Agent Client Protocol (ACP) support — both server-side
   (goose presents an ACP surface to ACP-aware clients) and client-side via provider-side shims
   (`providers/{claude,codex,gemini,copilot,amp,cursor,pi}_acp.rs`).

Three independent products converging on dual OpenAI/Anthropic endpoints — within roughly six months — is enough
signal to revisit DEC-0005's single-protocol commitment. The forcing function is harness portability: any client that
already speaks Anthropic-shape (Claude Code, Cursor, Codex, Zed, Amp, and an expanding ACP cohort) can plug into Linus
without a translation shim if Linus exposes the second endpoint shape. The cost of adding it is small (one extra HTTP
endpoint plus a shared dispatch underneath); the cost of not adding it is each future Anthropic-shape client either
needs a per-client adapter or cannot use Linus at all. Closes **R4-01**.

**Decision.** Phase 2a's orchestration HTTP layer exposes **both** an OpenAI-compatible surface (`/v1/chat/completions`
plus the OpenAI Responses spec endpoints as DEC-0005 and R2-05 require) and an Anthropic-compatible surface (the
`/v1/messages` shape used by Anthropic's Messages API and the ACP-style `/v1/anthropic/...` mounting Letta uses). The
two endpoint families share the underlying routing, Worker dispatch, sandbox, audit-log, and memory-mode (DEC-0031)
machinery — they differ only in the request/response envelope shape and the streaming-event catalog. Anthropic-shape
streaming uses the Anthropic SSE event vocabulary (`message_start`, `content_block_delta`, `message_delta`,
`message_stop`); OpenAI-shape streaming uses the OpenAI SSE event vocabulary. A thin per-protocol adapter layer maps
each shape onto a single internal `LinusRequest` / `LinusResponse` pair before dispatch.

The decision is **not** "speak ACP." Goose's full ACP integration (server-side ACP surface plus client-side ACP-shim
providers) is a larger surface area than Linus needs at Phase 2a; ACP carries client-protocol concerns (session
management, tool-call routing, slash-command UX) that overlap with Linus's own agent-spawner and tool-registry
surfaces. The Phase 2a delivery is the narrower Anthropic-Messages-compatible HTTP surface — enough to let any client
written against the Anthropic Messages API hit Linus without translation. ACP-as-Linus-capability stays a deferred
question; if Phase 5+ work surfaces a concrete ACP client that needs full integration, an ADR amendment covers the
graduation.

The Kimi-K2 temperature-mapping quirk is logged as a cautionary tale: the Anthropic-compatible surface is **not** a
transparent passthrough of OpenAI-shape requests. Specific semantic translations the Phase 2a implementation must
get right include (a) the `system` field placement (Anthropic uses a top-level `system` string; OpenAI puts it as the
first message with `role: "system"`), (b) the message-content shape (Anthropic uses content blocks with explicit
`type`; OpenAI uses a single string or content-array union), (c) tool-call format (Anthropic `tool_use` /
`tool_result` content blocks vs. OpenAI `tool_calls` / `tool_call_id`), and (d) the streaming-event catalog. The
Phase 2a spec should call out each translation explicitly with a small unit test demonstrating round-trip parity for
the common cases.

**Consequence.** Linus is harness-portable across both major endpoint shapes from Phase 2a onward. Any client written
against the Anthropic Messages API (or the chat-completions-shim half of Letta-style stacks) can use Linus without
translation; any client written against OpenAI Responses / Chat Completions continues to work. Phase 5+ openclaw,
claw-code-local, and any future native Linus front-end inherit both wire-protocol paths for free. The implementation
cost is bounded — one shared `LinusRequest` / `LinusResponse` core plus two thin adapter layers, fewer than ~500 LoC
of orchestration Python on top of the OpenAI-shape work that DEC-0005 and R2-05 already commit to. The reversal cost
is small: if the Anthropic surface goes unused after a measurement window, the endpoints can be deprecated and
removed; the OpenAI surface remains as DEC-0005's commitment.

The decision **does not** commit Linus to any particular Anthropic-shape extension beyond the Messages API surface.
Anthropic's extended-thinking endpoints, the `claude-3-7-sonnet-extended-thinking` feature flag, and any future
Anthropic-specific capability surface (tool-result content-type variants, citations, etc.) are out of Phase 2a scope;
they can be added per-feature as Linus needs them. The minimum target is "any Anthropic Messages API client can hit
Linus and get a usable response back" — that is the harness-portability claim.

**Amendment 2026-05-16 — supersedes the DEC-0005 single-protocol commitment.** DEC-0005's status line is updated to
note that the OpenAI-only portion is amended by DEC-0056 (the MCP-revisit portion remained superseded by DEC-0018).
DEC-0005's underlying decision — OpenAI-compatible HTTP as the v0 substrate — is preserved; DEC-0056 only extends the
endpoint surface to include the Anthropic-shape sibling.
