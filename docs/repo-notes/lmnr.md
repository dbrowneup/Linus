# lmnr (`lmnr-ai/lmnr`)

## 1. Purpose and scope

Laminar (lmnr) is an open-source observability platform purpose-built for AI agents — a Rust/Next.js/Python stack that
captures OpenTelemetry traces, provides dashboards and SQL analytics for span data, evaluates agent behavior, and
monitors for anomalies via learned signal detectors. It solves the "black box LLM pipeline" problem: every agent step
(LLM call, tool execution, decision point) is traced, queryable, and visualizable, enabling fast root cause analysis,
cost tracking, and quality monitoring. For Linus, Laminar is a reference implementation of operational observability
for local agents — not a required integration but a study case for understanding how to instrument and monitor
Linus-based agents in production workflows.

## 2. Architecture summary

Laminar is a multi-service monorepo: (1) **app-server** (Rust, Actix-web HTTP + Tonic gRPC, 50+ modules) — ingests
OTel spans into PostgreSQL + ClickHouse, serves REST API and realtime SSE, handles signal detection + alerts; (2)
**frontend** (Next.js/TypeScript, Zustand stores, Drizzle ORM) — interactive trace viewer, SQL query editor, dashboard
builder, signal management UI; (3) **query-engine** (Python gRPC service) — translates SQL queries to ClickHouse
analytics queries. The backend ingests spans via gRPC exporter (high-throughput), optionally persists to S3, pipes
through RabbitMQ (async processing, optional in-memory fallback), and executes signal filters on trace aggregates
(span names, error counts, custom attributes). Signals are rules (e.g., "alert if any span contains 'error'") that
trigger alerts routed via email, Slack, PagerDuty.

## 3. What's reusable in Linus

The OTel ingestion pipeline (gRPC exporter, batch span processing, attribute extraction) is directly applicable to
Linus agents — instrument each Worker model execution, tool call, and KnowledgeBase query with OTel spans, then ship to
a local Laminar instance (via Docker Compose). The frontend's span-view message parser (reconstructing LLM conversation
from OTel `gen_ai.*` attributes) is a reference for rendering structured LLM traces. The signal/alert system (rules
engine for detecting anomalies and routing notifications) is a pattern Linus can adapt for monitoring fine-tuned model
drift or KnowledgeBase query quality. The SQL query interface for accessing all trace data is useful for ad-hoc
debugging and performance analysis of Linus agents.

## 4. What's inspiration only

Laminar's clustering service (learning-based anomaly detection for trace grouping) is elegant but requires tuning and
training data — useful only after Linus has been running agents long enough to collect baseline traces. The dashboard
builder is polished but Linus doesn't need it for Phase 2a MVP (static dashboards for performance + cost monitoring
suffice). The Signals/Alerts feature gate (requires Google Generative AI or Bedrock credentials) adds cognitive load
that Linus doesn't need to replicate immediately.

## 5. What's incompatible or out of scope

Laminar is a full-stack observability SaaS-shaped platform (managed hosted version available; self-hosted via Docker).
It's not compatible with Linus's all-local Apple Silicon constraint: the app-server is Linux-only (depends on
inotify, `/proc`-based process trees for tree-kill). A self-hosted Laminar stack requires PostgreSQL, ClickHouse,
RabbitMQ/Redis (or in-memory fallbacks), and headless Docker — feasible but operationally heavy for a local MacBook
tool. Linus can adopt OTel instrumentation without adopting the full Laminar stack; only the SDK (1 line of code) and
exporter are required.

## 6. Recommendation: **Study (Phase 5+)**

Laminar is not essential for Phase 2a (MVP orchestration doesn't require observability) but is critical reading for
Phase 5+ when Linus moves to production-grade agent workflows. The immediate practical value: (1) design Linus agent
instrumentation to emit OTel spans from day one (spec-compliant, forward-compatible), (2) evaluate Docker-compose
self-hosted Laminar on an x86 Linux VM as an optional observability backend for Dan's workflows that need comprehensive
tracing. A concrete Phase 5 experiment: instrument a Linus agent running a genomics analysis task with OTel tracing,
ingest into self-hosted Laminar, and measure span-to-alert latency and dashboard query performance on 100k+ spans.

## 7. Questions for Dan

- **OTel on local MacBook agents.** Laminar's app-server is Linux-only, but OTel SDKs are cross-platform. Should Linus
  emit OTel traces locally (for potential future remote Laminar) or build a lightweight local trace store (SQLite) that
  talks to the Linus orchestration layer directly?
- **Operational burden of self-hosted Laminar.** For Dan's personal workflows, is a full Laminar stack (Postgres +
  ClickHouse + RabbitMQ) justified, or is lightweight JSON-based request/response logging sufficient for Phase 2-4?
- **Signal detection for fine-tuned model quality.** Once Linus has fine-tuned models (Phase 6), should it auto-detect
  quality drift with Laminar's clustering, or rely on manual evaluation against the Dan task suite? _Partially resolved (DEC-0040, see [answered-questions.md](../questions/answered-questions.md)): Faithfulness audit of stored reasoning traces deferred to Phase 3 with a trigger condition; quality evaluation in Phase 6 relies on the Dan task suite first; automated drift detection is a Phase 3+ question._
