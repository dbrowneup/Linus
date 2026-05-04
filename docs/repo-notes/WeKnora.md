## WeKnora (`Tencent/WeKnora`)

## 1. Purpose and scope

WeKnora is Tencent's open-source enterprise RAG framework — the engine behind the WeChat Dialog Open Platform
(`chatbot.weixin.qq.com`) — packaged for self-hosting. It targets organizations that want to turn document corpora
(Feishu, Notion, Yuque, PDFs, Office, audio via ASR) into queryable, agent-reasonable knowledge with full audit and
multi-tenant access control. Three modes share one pipeline: RAG quick Q&A, a ReAct agent that orchestrates retrieval +
MCP tools + web search, and a "Wiki Mode" that auto-distills source documents into interlinked markdown pages with a
knowledge graph viewer. Trendshift-listed, MIT-licensed, v0.5.1 at clone time, ~20 named contributors and Tencent
backing. For Linus, this is the only enterprise-shaped, large-org-backed RAG system in the cloned set — useful as an
architectural reference for what "serious" looks like, not as code Linus would embed.

## 2. Architecture summary

A Go monolith (`go 1.24.11`, Gin HTTP, GORM/Postgres) with a Python gRPC sidecar (`docreader/` — PDF/Word/Excel/PPT/HTML
parsing, OCR, chunking, splitter strategies including parent-child) and a Vue/TS frontend (`frontend/`). Deployment is
Docker Compose only for local use, Helm chart for Kubernetes. The default `docker-compose.yml` brings up frontend (NGINX
on :80), the Go `app` (Gin on :8080), `docreader` (gRPC on :50051), Postgres (with `pgvector`), Redis (asynq queue +
rate limit), Jaeger (OTel traces), and a `sandbox` image for Agent Skills. Profiles add Neo4j (GraphRAG), MinIO (object
storage), Langfuse (LLM observability). Vector store is **pluggable**: pgvector default, plus Elasticsearch, Milvus,
Weaviate, Qdrant — all wired through `internal/searchutil` and selectable per knowledge base from the UI. Retrieval is
hybrid by default (BM25 sparse via `gojieba` Chinese tokenization + dense vectors), with optional GraphRAG over Neo4j
and parent-child chunking. LLM integration is provider-agnostic: 14+ backends including OpenAI, Azure, DeepSeek, Qwen,
Zhipu, Hunyuan (Tencent's own), Gemini, MiniMax, NVIDIA, OpenRouter, and Ollama — all behind a unified provider
interface using `sashabaranov/go-openai` plus per-vendor adapters. Reranker is a separate service
(`rerank_server_demo.py` ships a reference). Agent Skills run in a sandboxed Docker container
(`WEKNORA_SANDBOX_MODE=docker`, spawned per invocation). IM channels (WeCom, Feishu, Slack, Telegram, DingTalk,
Mattermost, WeChat) live in `internal/im/`.

## 3. What's reusable in Linus

Almost nothing in code form, but several patterns translate. The **provider abstraction** for 14 LLM backends behind one
interface is exactly the shape Linus's inference layer wants if it grows beyond Ollama+pmetal — worth reading
`internal/models/` before designing Linus's provider registry. The **per-knowledge-base indexing strategy toggle** (turn
vector / BM25 / GraphRAG / Wiki on or off independently) is a UX pattern Linus's KnowledgeBase v1 should consider rather
than locking in one retrieval mode globally. The **parent-child chunking** strategy (introduced in v0.3.3) is concrete
prior art for the same problem the KnowledgeBase submodule will face. And the **docreader gRPC sidecar split** — keeping
all Python parsing dependencies (poppler, OCR, format-specific libraries) behind a single gRPC boundary so the core
service stays slim and language-clean — is a packaging pattern worth borrowing if Linus's KB ingestion outgrows
in-process Python.

## 4. What's inspiration only

Compared to the Group 6 lightweights, WeKnora is the _opposite_ end of the spectrum. Where `vectorless` proposes that
retrieval can be skipped entirely for small corpora and `qmd`/`codesight` are single-purpose Python tools, WeKnora is a
multi-tenant SaaS-grade platform with IM bots, a Chrome extension, a WeChat Mini Program, and a ClawHub skill. It is
also a meaningful contrast to **`paper-qa`** (Group 8, FutureHouse): paper-qa is a focused scientific-PDF RAG library
designed to be embedded in Python research workflows, with thoughtful citation handling and no infrastructure
assumptions; WeKnora is an infrastructure product that happens to do RAG. For Dan's single-user M1 Max scientific
workflow, paper-qa's shape is the right reference and WeKnora's is not — but WeKnora's _catalogue_ of integrated vector
stores, LLM providers, and IM channels is a useful menu of "what enterprise RAG considers table stakes in 2026."
Langfuse integration in particular is worth noting: when Linus's agent loops get complex enough to need ReAct tracing,
Langfuse is a credible answer (and runs locally via Docker — though see Section 5).

## 5. What's incompatible or out of scope

This is a **stateful Docker-Compose stack**, full stop. The minimal default brings up six containers; `--profile full`
brings up ten or more. On Dan's M1 Max, Docker runs in a Linux VM with no Metal/ANE passthrough — every embedding,
inference, or rerank call routed through a containerized Ollama would lose the unified-memory advantage that makes the
M1 Max attractive in the first place. The compose file works around this with
`OLLAMA_BASE_URL=http://host.docker.internal:11434` (reaching out to a host Ollama) but that's a bandage on the deeper
mismatch: this stack assumes a dedicated server with GPU passthrough or cloud GPUs, not a laptop. Postgres, Redis,
Jaeger, optional Neo4j, optional MinIO, optional Langfuse are persistent services that idle even when nothing is being
asked of them — directly at odds with Linus's "native inference, Docker only for stateless services" rule in CLAUDE.md.
The multi-tenancy, IM bots, JWT auth, AES-256-GCM encrypted credentials, OIDC login, and SSRF whitelist are all weight
Linus does not need for a single-user system. The codebase is also primarily Chinese-documented (the English README is
generated; `docs/开发指南.md` and the four README translations indicate the canonical audience), which raises the cost
of contributing back upstream.

## 6. Recommendation: **Study**

Read `internal/models/` for the provider-abstraction shape, skim `internal/searchutil/` for the hybrid + per-KB index
toggle pattern, and look at `docreader/` as a model for the parser-as-sidecar split. Do not deploy it. Do not vendor any
of it. Revisit only if Linus ever grows toward multi-user / shared-knowledge-base territory, which is not on the
roadmap.

## 7. Questions for Dan

- **Provider abstraction now or later.** WeKnora's strongest reusable idea is the unified LLM provider interface — same
  shape regardless of OpenAI vs Ollama vs Hunyuan. Does Linus want to design that abstraction in Phase 2a (when there
  are only Ollama and pmetal candidates), or wait until a third backend forces it?
- **Per-KB indexing strategy toggle.** Should KnowledgeBase v1 commit to one retrieval mode (e.g., dense-only) for
  simplicity, or design from day one for hybrid + GraphRAG with per-corpus toggles like WeKnora does?
- **Parser-as-sidecar.** The `docreader` Python gRPC sidecar pattern keeps the Go core clean of every PDF/OCR
  dependency. Worth considering for KnowledgeBase ingestion if the dependency surface grows, or premature for a Python
  monolith?
- **Langfuse for agent tracing.** When Linus gets to multi-step ReAct loops in Phase 3, do you want LLM-native
  observability (Langfuse, Phoenix, Helicone) in scope, or is OpenTelemetry + structured logs sufficient?
- **Differentiation gap.** Is there any meaningful overlap between WeKnora's Wiki Mode (auto-distill documents into
  interlinked markdown + knowledge graph) and the KnowledgeBase submodule's own roadmap, or are these solving different
  problems for different users?
