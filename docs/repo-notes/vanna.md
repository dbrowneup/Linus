# vanna (`vanna-ai/vanna`)

## 1. Purpose and scope

Vanna 2.0 is a production SQL agent platform: natural language → SQL generation → query execution → visualization (tables, charts, summaries), all streamed to a web UI component. It enforces user-aware access control at every layer (permissions baked into tool execution, not bolted on after), provides enterprise features (audit logs, rate limiting, lifecycle hooks), and works with any LLM (Claude, Gemini, Anthropic, Ollama) and any database (PostgreSQL, SQLite, BigQuery, etc.). For Linus specifically: this is a reference implementation of how to build a domain-specific agent (here: SQL; Linus will need genomics, chemistry, bioinformatics queries) with user context flowing through system prompt → tool execution → result filtering. It's also a working example of FastAPI + MCP-style tools + streaming responses that Dan could adapt for Linus's own orchestration layer.

## 2. Architecture summary

Vanna 2.0 builds on a three-layer stack: (1) **LLM Layer** (pluggable, supports OpenAI/Anthropic/Ollama via providers), (2) **Agent Layer** (agentic loop with tool calling, user context injection), (3) **Tool Layer** (SQL execution, visualization, custom tools extending a `Tool` base class with permission checks). A `UserResolver` extracts identity from incoming requests (cookies, JWTs, custom auth); that User object flows into tool execution context automatically. Tools return `ToolResult` (success/failure + LLM-visible output), and the agent streams responses to the frontend `<vanna-chat>` web component. The runtime supports FastAPI (primary), Flask, and Ollama's native interface. Custom tools are Pydantic models with an `execute()` coroutine; lifecycle hooks (pre/post-call, quota checking) plug into the execution loop. Observability is built in (tracing, metrics, logging).

## 3. What's reusable in Linus

The `Tool` base class + registry pattern is directly portable to Linus's MCP tool system. A `RunSqlTool(sql_runner=...)` becomes `GenomicsQueryTool(knowledge_base=...)` with identical shape. The user-context-injection design (User object threaded through ToolContext) is exactly what Linus needs for audit (which Worker called what on behalf of whom) and permissions (some tools only for domain experts). The lifecycle-hooks pattern (pre-call quota check, post-call logging) is reusable as-is for Linus Phase 2a. The streaming responses to a web component pattern (backend chunks data, frontend renders incrementally) is applicable if Linus builds a native chat UI. The entire FastAPI harness is a working scaffold for "local LLM + tools + streaming responses" — a good reference for Linus's own backend.

## 4. What's inspiration only

Vanna's SQL generation tuning (few-shot examples, schema-aware prompting, answer validation) is domain-specific and won't transfer to bioinformatics tasks. The visualization layer (Plotly charts, table rendering) is frontend-specific; Linus can steal the pattern but not the code. The multi-database abstraction is useful for understanding how to support multiple query targets, but Linus will likely standardize on one backend (KnowledgeBase SQLite or a graph store).

## 5. What's incompatible or out of scope

Vanna is closed-source SaaS-ready; the GitHub repo is the open-source 2.0 engine. Licensing is MIT, but the design assumes paying customers (rate limiting, audit logs as compliance features). The web component (`<vanna-chat>`) is pre-built and proprietary; Linus would build its own or use openclaw. The LLM integrations are hardcoded (Anthropic, OpenAI, Azure, Ollama); Linus only needs Ollama + future fine-tuned models. The SQL generation accuracy story requires data lineage & schema understanding that Linus doesn't have yet.

## 6. Recommendation: **Study (Phase 2a)**

Use Vanna's tool-base-class design and user-context-injection pattern as the blueprint for Linus's MCP tool layer. Copy the lifecycle-hooks architecture for audit/logging. Run a spike in Phase 2a: build one custom tool (e.g., SemanticSearchTool over KnowledgeBase) using Vanna's pattern and measure code clarity. Don't integrate Vanna's full stack (SQL + viz); Linus's domain is different. The FastAPI scaffold is useful reference; Linus will likely build its own orchestration backend from scratch.

## 7. Questions for Dan

- **User context flow.** Vanna threads User through every tool call automatically. Should Linus Workers be aware of their caller (Dan), or is that audit/logging-only? Does audit context need to flow into the task spec or just the log?
  _Partially resolved (DEC-0050, DEC-0031, see [answered-questions.md](../questions/answered-questions.md)): Role
  carries `memory_access_tier`; `memory_mode` and `cot_budget` are audit-logged per call; per-tool caller propagation
  TBD in Phase 2a orchestration spec._
- **Tool lifecycle hooks.** Vanna has pre-call (quota) and post-call (logging) hooks. For Linus, are there pre/post-tool scenarios worth supporting, or is a flat "execute + log" model enough?
- **Streaming responses.** Vanna's web component consumes streamed JSON chunks (table, chart, text). If Linus ever needs a chat UI, should it support streaming or batch-return results? Does incremental feedback matter for Linus tasks (typically short, ~minutes)?
