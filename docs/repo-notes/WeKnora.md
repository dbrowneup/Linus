# WeKnora (`Tencent/WeKnora`)

_Refreshed 2026-05-18 against upstream HEAD 1cb522e6; 383 commits / 827 files reviewed (v0.5.0 / v0.5.1 / v0.5.2 — v0.5.2 released 2026-05-13)._

## 1. Purpose and scope

WeKnora is Tencent's open-source enterprise RAG framework — the engine behind the WeChat Dialog Open Platform
(`chatbot.weixin.qq.com`) — packaged for self-hosting. It targets organizations that want to turn document corpora
(Feishu, Notion, Yuque, PDFs, Office, audio via ASR) into queryable, agent-reasonable knowledge with full audit and
multi-tenant access control. Three modes share one pipeline: RAG quick Q&A, a ReAct agent that orchestrates retrieval +
MCP tools + web search, and a "Wiki Mode" (new since the prior note in v0.5.0) that auto-distills source documents into
interlinked markdown pages with a knowledge graph viewer — directly parallel in shape to TheKnowledge's design space.
Trendshift-listed, MIT-licensed, **v0.5.2** at refresh time, ~20 named contributors and Tencent backing. For Linus,
this is the only enterprise-shaped, large-org-backed RAG system in the cloned set — useful as an architectural
reference for what "serious" looks like, not as code Linus would embed.

## 2. Architecture summary

A Go monolith (`go 1.26`, Gin HTTP, GORM/Postgres) with a Python gRPC sidecar (`docreader/` — PDF/Word/Excel/PPT/HTML
parsing, OCR, chunking, adaptive 3-tier splitter strategies as of v0.5.2) and a Vue/TS frontend (`frontend/`). Deployment
is Docker Compose only for local use, Helm chart for Kubernetes. The default `docker-compose.yml` brings up frontend
(NGINX on :80), the Go `app` (Gin on :8080), `docreader` (gRPC on :50051), Postgres (with `pgvector`), Redis (asynq
queue + rate limit), Langfuse (now the canonical observability path; Jaeger references were retired in v0.5.1), and a
`sandbox` image for Agent Skills. Profiles add Neo4j (GraphRAG), MinIO (object storage). Vector store is **pluggable**:
pgvector default, plus Elasticsearch, Milvus, Weaviate, Qdrant, Tencent VectorDB, and Apache Doris 4.1 (the last two
added in v0.5.2) — all wired through `internal/searchutil` and selectable per knowledge base from the UI. Retrieval is
hybrid by default (BM25 sparse via `gojieba` Chinese tokenization + dense vectors) with per-tenant RRF tuning (`RRFK` /
`RRFVectorWeight` / `RRFKeywordWeight`), optional GraphRAG over Neo4j, parent-child chunking, and now an **adaptive
3-tier chunking** pipeline that profiles each document before splitting and routes to heading-aware (Markdown), heuristic
(form-feeds, multilingual chapter markers DE/EN/ZH, all-caps titles), or recursive fallback — with a `POST
/api/v1/chunker/preview` endpoint for live debugging. LLM integration is provider-agnostic: 14+ backends including
OpenAI, Azure, **Anthropic (Claude — added v0.5.2)**, DeepSeek, Qwen, Zhipu, Hunyuan, Gemini, MiniMax, NVIDIA,
OpenRouter, Ollama, and Moonshot/Kimi. Reranker is a separate service. Agent Skills run in a sandboxed Docker container.
IM channels (WeCom, Feishu, Slack, Telegram, DingTalk, Mattermost, WeChat) live in `internal/im/`. Web search now spans
SearXNG (self-hosted federated metasearch, v0.5.2). v0.5.2 also adds: a **per-knowledge-base indexing-strategy toggle**
explicitly surfaced in the KB editor (Vector / Keyword / Wiki / Knowledge Graph individually opt-in); human-in-the-loop
MCP approval gates with a `ToolApprovalCard` and per-user approval state persistence; a `weknora` Go CLI v0.2 with
`gh`-style noun-verb commands (`api`, `auth`, `chat`, `context`, `doc`, `doctor`, `kb`, `link`, `search`, `version`), a
stable `{ok,data,error,_meta,dry_run,risk}` JSON envelope, agent-affordance flags (`--dry-run` + exit-code 10 for
destructive writes, auto-detected `CLAUDECODE` / `CURSOR_AGENT` env triggers `AI agents:` guidance) and project-level
binding via `.weknora/project.yaml`; a Global Command Palette ⌘K; multi-tenant workspace switching with RBAC; and cloud-
image packaging scripts (`scripts/cloud-image/`) for reproducible self-hosted images.

## 3. What's reusable in Linus

Still almost nothing in code form, but the pattern catalogue grew. The **provider abstraction** for 14+ LLM backends
behind one interface — now including Anthropic alongside OpenAI/Ollama — is exactly the shape Linus's inference layer
wants if it grows beyond Ollama+pmetal, and directly supports the DEC-0005 / Phase-2a Anthropic-compat revisit. The
**per-knowledge-base indexing-strategy toggle** (turn Vector / Keyword / Wiki / Knowledge Graph on or off independently
per KB) is now an explicit, UI-surfaced first-class feature in v0.5.0+, and directly answers the prior note's R2-38 open
question: yes, designing this from day one is tractable and the WeKnora pattern is the credible reference. The
**adaptive 3-tier chunking** pipeline (document profiling → heading-aware / heuristic / recursive routing, with a live
preview endpoint) is concrete prior art for the same problem KnowledgeBase will face. The **docreader gRPC sidecar
split** — keeping all Python parsing dependencies (poppler, OCR, format-specific libraries) behind a single gRPC
boundary — is a packaging pattern worth borrowing if Linus's KB ingestion outgrows in-process Python. New since the
prior note: the **`weknora` Go CLI** is a strong reference for what a well-shaped agent-aware CLI looks like — `gh`-style
noun-verb surface, stable JSON envelope, `--dry-run` and exit-code 10 for confirmation-required writes, CLAUDECODE-env
auto-guidance, and `cli/AGENTS.md` as a documented contract. If Linus ships a `linus` CLI, this is the shape to copy.
The **human-in-the-loop MCP approval gate** with persistent approval state per user is also relevant prior art for
Linus's sandbox / tier-3 autonomy questions.

## 4. What's inspiration only

Compared to the Group 6 lightweights, WeKnora is the _opposite_ end of the spectrum. Where `vectorless` proposes that
retrieval can be skipped entirely for small corpora and `qmd`/`codesight` are single-purpose Python tools, WeKnora is a
multi-tenant SaaS-grade platform with IM bots, a Chrome extension, a WeChat Mini Program, and a ClawHub skill. It is
also a meaningful contrast to **`paper-qa`** (Group 8, FutureHouse): paper-qa is a focused scientific-PDF RAG library
designed to be embedded in Python research workflows, with thoughtful citation handling and no infrastructure
assumptions; WeKnora is an infrastructure product that happens to do RAG. For Dan's single-user M1 Max scientific
workflow, paper-qa's shape is the right reference and WeKnora's is not — but WeKnora's _catalogue_ of integrated vector
stores, LLM providers, and IM channels is a useful menu of "what enterprise RAG considers table stakes in 2026."
Langfuse is now the canonical observability path (replacing Jaeger in v0.5.1+); when Linus's agent loops get complex
enough to need ReAct tracing, Langfuse runs locally via Docker and is a credible answer (though see Section 5).
WeKnora's Wiki Mode (v0.5.0) and TheKnowledge's vault both bet on "auto-distill sources into interlinked markdown +
graph" — useful triangulation that this is a viable pattern, even if Linus doesn't adopt either.

## 5. What's incompatible or out of scope

This is a **stateful Docker-Compose stack**, full stop. The minimal default brings up six containers; `--profile full`
brings up ten or more. On Dan's M1 Max, Docker runs in a Linux VM with no Metal/ANE passthrough — every embedding,
inference, or rerank call routed through a containerized Ollama would lose the unified-memory advantage that makes the
M1 Max attractive in the first place. The compose file works around this with
`OLLAMA_BASE_URL=http://host.docker.internal:11434` but that's a bandage on the deeper mismatch: this stack assumes a
dedicated server with GPU passthrough or cloud GPUs, not a laptop. Postgres, Redis, Langfuse, optional Neo4j, optional
MinIO are persistent services that idle even when nothing is being asked of them — directly at odds with Linus's "native
inference, Docker only for stateless services" rule in CLAUDE.md. The multi-tenancy, IM bots, JWT auth, AES-256-GCM
encrypted credentials, OIDC login, SSRF whitelist, and the new (v0.5.2) tenant RBAC / workspace switching / per-user
favorites are all weight Linus does not need for a single-user system. The Anthropic provider's value to Linus comes
from the abstraction _pattern_, not the WeKnora implementation — Linus's serving stack would call Anthropic-compat
endpoints directly (e.g., pmetal's `/v1/messages`) without WeKnora's tenant-credential indirection. The codebase is
also primarily Chinese-documented (the English README is generated; `docs/开发指南.md` and the four README translations
indicate the canonical audience), which raises the cost of contributing back upstream. Go 1.26 MSRV bump in v0.5.2 is a
non-issue for "don't deploy this" but worth noting if Dan ever evaluates running it.

## 6. Recommendation: **Study**

No verdict change. The v0.5.0-v0.5.2 changes (per-KB indexing toggle, adaptive chunking, Anthropic provider, agent-aware
Go CLI, Wiki Mode, MCP approval gates) make WeKnora a richer pattern reference but reinforce rather than soften the
"don't deploy this on a laptop" verdict — the multi-tenant + RBAC + workspace + IM bot weight grew, not shrank. Read
`internal/models/` for the provider-abstraction shape (now including the Anthropic adapter), skim `internal/searchutil/`
for the hybrid + per-KB index toggle pattern, look at `docreader/` and `docs/CHUNKING.md` for the adaptive chunking
design, and read `cli/AGENTS.md` + `cli/README.md` for the agent-aware CLI pattern if Linus ever ships a `linus` CLI. Do
not deploy it. Do not vendor any of it. Revisit only if Linus ever grows toward multi-user / shared-knowledge-base
territory, which is not on the roadmap.

## 7. Questions for Dan

1. **Provider abstraction now or later.** WeKnora's strongest reusable idea is the unified LLM provider interface — same
   shape regardless of OpenAI vs Ollama vs Anthropic vs Hunyuan. Does Linus want to design that abstraction in Phase 2a
   (when there are only Ollama and pmetal candidates), or wait until a third backend forces it? Phase-2a Anthropic-compat
   support (DEC-0005 revisit) makes the abstraction question more urgent than the prior note assumed.
2. **Per-KB indexing strategy toggle.** _Partially resolved (R2-38, see WeKnora v0.5.0+):_ the WeKnora pattern is now a
   shipped, UI-surfaced, per-KB toggle covering Vector / Keyword / Wiki / Knowledge Graph independently. KnowledgeBase
   v1 should adopt this shape from day one rather than locking in a single retrieval mode globally — confirm the toggle
   set for Phase 2 KB v1 (likely just Vector + Keyword to start, with GraphRAG + Wiki deferred to later phases).
3. **Parser-as-sidecar.** The `docreader` Python gRPC sidecar pattern keeps the Go core clean of every PDF/OCR
   dependency. Worth considering for KnowledgeBase ingestion if the dependency surface grows, or premature for a Python
   monolith?
4. **Langfuse for agent tracing.** When Linus gets to multi-step ReAct loops in Phase 3, do you want LLM-native
   observability (Langfuse, Phoenix, Helicone) in scope, or is OpenTelemetry + structured logs sufficient? WeKnora's
   v0.5.1 Jaeger→Langfuse migration is a useful data point on which way the industry is trending.
5. **Agent-aware CLI shape.** WeKnora's `weknora` CLI v0.2 ships an explicit agent-affordance contract — `--dry-run`,
   exit-code 10 for confirmation-required writes, stable JSON envelope, CLAUDECODE-env-triggered guidance. If Linus
   eventually ships a `linus` CLI surface for harnesses to drive the orchestrator, is this the right reference shape, or
   does Linus's OpenAI-/Anthropic-compat HTTP API obviate the CLI surface entirely?
6. **Differentiation gap.** WeKnora's v0.5.0 Wiki Mode (auto-distill documents into interlinked markdown + knowledge
   graph) is now a direct architectural parallel to TheKnowledge and to KnowledgeBase's own roadmap. Are these solving
   the same problem in three different surfaces, or are there meaningful axes (citation strictness, NotebookLM
   integration, multi-tenancy) that separate them for Linus's purposes?
