# beever-atlas (`Beever-AI/beever-atlas`)

_Refreshed 2026-05-18 against upstream HEAD 63be2e0; 219 commits / 619 files reviewed._

## 1. Purpose and scope

Beever Atlas is an "LLM-first wiki knowledge base" whose unique source of truth is **team chat** — Slack, Discord,
Microsoft Teams, and Mattermost — rather than papers, PDFs, URLs, or files on disk. It pulls a workspace's channel
history through a TypeScript bot service, runs a six-stage Google-ADK ingestion pipeline that distils raw messages into
atomic facts, entities, and relationships, persists them into a dual semantic-plus-graph memory (Weaviate + Neo4j +
MongoDB + Redis), and continuously rebuilds a per-channel auto-maintained wiki on top. Two consumer surfaces hang off
that memory: a React dashboard with a streaming QA agent and a `fastmcp`-served MCP endpoint exposing 16 tools to
Claude Code / Cursor. The 0.1.2 release (2026-04-30) hardened the MCP surface (auth middleware, principal-keyed rate
limits, Redis-backed sliding-window counters for multi-worker deploys, `/api/admin/mcp-metrics`), tightened security
(retired legacy unauth `/mcp` mount, CodeQL hardening sweep, SSRF hardening, HMAC-signed loader tokens, dependency CVE
patches), and unified ADK-tool + MCP-tool implementations under a shared `capabilities/` layer. The Unreleased work
toward 0.2.0 is the provider-agnostic LLM configuration system (`agent-llm-provider-pluggable`) — a unified
Endpoint+Assignment data model with 19 endpoint presets, 4 apply presets (`gemini-balanced`, `openai-quality`,
`claude-quality-gemini-fast`, **`fully-local`**), AES-256-GCM-encrypted credentials, LiteLLM single-funnel routing, and
per-Endpoint circuit breakers. The README explicitly quotes Karpathy's "LLMs read wikis, not chat logs" framing, which
keeps Beever a Group 2 (LLM-Wiki) sibling, but the chat-as-source axis still differentiates it from every other engine
in the cluster.

## 2. Architecture summary

Three services, four datastores. The Python backend (`src/beever_atlas/`) is a FastAPI app built on **Google ADK**
(`google-adk>=1.28.1`) with `litellm` as the model router and Gemini as the default LLM; embeddings come from Jina v4
(2048-dim) by default but are now provider-pluggable (Jina / OpenAI / Cohere / Voyage / Gemini / Mistral / Ollama) via
LiteLLM through PR #154 and the Endpoint+Assignment model. The chat-source layer is the `BaseAdapter` abstraction in
`src/beever_atlas/adapters/base.py` normalising every platform message into a `NormalizedMessage` dataclass; concrete
adapters live alongside (`bridge.py`, `file_adapter.py`, `mock.py`), with platform-specific protocol work pushed out to
a separate Node/TypeScript bot service in `bot/src/` and HTTP-bridge shared-secret auth. The ingestion pipeline
(`agents/ingestion/pipeline.py`) is an ADK `SequentialAgent` with `ParallelAgent` fan-outs: preprocess → (extract facts
‖ extract entities) → (embed ‖ contradiction validation) → persist (Weaviate 3-tier + Neo4j entity graph). The wiki
layer (`src/beever_atlas/wiki/`) is `gather → compile → cache` with per-channel `asyncio.Lock`; the 2026-05 graph
overhaul (PR #168) typed entities, added a classifier and co-mention edges, and updated the React UI. The QA layer
streams answers over SSE with a smart router picking semantic vs graph per question. The MCP `/mcp` mount is now the
single bearer-auth-required endpoint, with the legacy unauth mount removed and CodeQL alerts #1–#60 hardened —
least-privilege workflow permissions, static-dictionary error messages at HTTP sinks, exact-host URL substring
matching, per-platform host allowlists, strict UUID validation, double-HTML-entity-decoding fix, SSRF host allowlists
on bridge file fetches. New ops scaffolding includes a Makefile, GitHub Actions CI (backend ruff/pytest, web/bot
lint/test/build), CodeQL on push/PR/weekly cron, NebulaGraph as a second graph backend (`GRAPH_BACKEND` env var, Neo4j
default), Apache-2.0 license + NOTICE, comprehensive runbooks (`docs/runbooks/ai-setup.md`,
`docs/runbooks/atlas-yaml.md`, `docs/runbooks/litellm-cutover.md`), and an `atlas` installer with three install modes
(interactive Step-2 picker, `BEEVER_ENDPOINTS` env JSON, declarative `atlas.yaml` via `atlas apply`).

## 3. What's reusable in Linus

The wiki-first-RAG thesis (distil the corpus into a per-source wiki at ingestion, retrieve against the wiki rather than
raw chunks) and the dual semantic+graph memory with a smart router remain the headline architectural patterns to lift —
unchanged from the prior note. New for the 2026-05-18 refresh:

- **`fully-local` LLM apply preset.** The Endpoint+Assignment model explicitly ships a `fully-local` preset alongside
  Gemini/OpenAI/Claude presets, and LiteLLM is the single funnel for every completion. This is direct precedent for
  Linus's "no paid APIs required for operation" north star — the same ADK-based ingestion can run against an Ollama or
  pmetal endpoint via LiteLLM, with provider switching declarative through `atlas.yaml`. Worth studying for how
  multi-agent ADK systems can be made model-pluggable without rewriting agent code.
- **Capability-layer extraction.** The 0.1.2 work that moved ADK tools and MCP tools into a shared
  `src/beever_atlas/capabilities/` layer is the pattern Linus's tool registry should adopt — write the capability once,
  expose it through whatever surface a given Worker needs. Directly parallel to the planned Linus tool-registry shape.
- **MCP auth + rate-limit hardening.** Per-tool channel-access checks, bearer auth, principal-keyed rate limits with
  Redis-backed sliding-window counters across worker processes, principal ACL fallback, HMAC-signed loader tokens, the
  `/api/admin/mcp-metrics` operator view. Linus's eventual MCP server needs all of this; Beever's `/mcp` mount is a
  good reference implementation.
- **Long-running job pattern over MCP.** Documented in `docs/mcp-server.md` along with error codes and rate-limit
  shapes. Worth lifting verbatim.
- **CodeQL + supply-chain hardening as a release gate.** The hardening sweep (#1–#60) is concrete and worth replicating
  on Linus's own Python/TypeScript surfaces once the orchestration layer is real.

The 6-stage ADK SequentialAgent + ParallelAgent ingestion skeleton, the `gather → compile → cache` wiki builder with
per-resource async locks, and the `BaseAdapter` + `NormalizedMessage` source-abstraction shape remain directly liftable
patterns from the prior note.

## 4. What's inspiration only

The four-datastore footprint (Weaviate + Neo4j + MongoDB + Redis), the React dashboard, the bot service, docker-compose
orchestration, OAuth/encryption infrastructure for stored platform credentials, the rate-limit and SSRF-protection
plumbing across web/bot/backend, and the per-agent MCP auth — none of this is appropriate for Linus's single-user local
context. The Endpoint+Assignment data model is sophisticated (UUIDs, AES-256-GCM-encrypted creds, RPM budgets, curated
model lists, AWS-IAM/Google-SA auth types, declarative `atlas.yaml`) but more ceremony than Dan's single-machine setup
needs. The 16-tool MCP surface is comprehensive but channel-scoped; Linus's eventual MCP server should be paper- and
note-scoped instead, so the tool list is a structural reference rather than a portable contract. The atlas installer
with interactive Step-2 LLM picker is well-built but solves a multi-provider, multi-key, hosted-deployment configuration
problem Linus has explicitly chosen to avoid (DEC-0027: local-first, no paid APIs required). NebulaGraph as a second
graph backend is interesting but neither Neo4j nor NebulaGraph is on Linus's substrate roadmap (rdflib + property graph
per DEC-0015).

## 5. What's incompatible or out of scope

Unchanged from the prior note: chat platforms aren't a Linus ingest target. Slack/Discord/Teams/Mattermost connectors,
the bot service, OAuth flows, Block Kit formatters, and the encrypted credential vault are zero-utility for Dan's
workflow and represent the bulk of the codebase. Google ADK remains a heavy dependency and a programming model
distinct from Linus's planned orchestration layer; the new LiteLLM funnel and `fully-local` preset make it _possible_
to point ADK at a Linus endpoint, but the agent-prompts are still tuned for Gemini-class models and the dependency
weight argues against adoption. Weaviate and Neo4j are still Docker-resident JVM/Go services; Linus keeps its data
plane in Qdrant + SQLite + filesystem per DEC-0015. The Apache 2.0 license is permissive but the chat-platform nature
of the codebase means there are very few files where lifting code wholesale makes sense — patterns are the value, not
source. The Docker Compose multi-service shape (backend + bot + web + 4 datastores) is a team-appliance product, not a
personal-AI product.

## 6. Recommendation: **Study**

Verdict unchanged. Read for the wiki-first-RAG architecture, the ADK SequentialAgent + ParallelAgent shape, the
`gather → compile → cache` wiki builder with async per-resource locks, the dual semantic+graph memory + smart router,
the capability-layer extraction pattern, and the MCP auth/rate-limit hardening. Lift those patterns into Linus's
Phase 2/3 KB and MCP-server designs. The 0.1.2 + Unreleased work materially strengthens the "Study" recommendation —
LiteLLM-funnel + `fully-local` preset + Endpoint+Assignment is precedent for how a multi-agent ADK system stays
provider-pluggable, and the MCP hardening is directly applicable to Linus's eventual MCP server. Do not adopt the
codebase, the dependency stack (ADK, Weaviate, Neo4j, Gemini default, Jina default), or the chat connectors. Still
earns its G2-cluster wiki-engine spot — the chat-as-source differentiator is intact, and the wiki-first-RAG thesis is
now backed by a production-grade hardening pass.

## 7. Questions for Dan

1. **Wiki-first-RAG for KnowledgeBase v2.** Beever's thesis is that retrieval should hit a continuously-distilled per-
   source wiki, not raw chunks. KnowledgeBase v1 is chunk-based RAG. Is "distil each paper into a structured wiki page
   at ingest, then retrieve against that" an explicit Phase 3 design move, or out of scope?
2. **Dual semantic + graph memory.** Beever runs Weaviate + Neo4j with a smart router that picks per question. The
   current Linus plan is Qdrant-only. Is a graph store (Neo4j, Memgraph, or even a SQLite-on-disk triple table) on the
   roadmap for relational queries over the paper corpus?

   _Partially resolved (DEC-0015, see [answered-questions.md](../questions/answered-questions.md)): Dual approach
   adopted (RDF via rdflib/SPARQL + property graph); both are Phase 3 KB substrates; Weaviate/Neo4j not adopted._

3. **MCP tool surface.** Beever ships 16 tools through `fastmcp`. Is the Phase 2/3 plan for Linus's MCP surface
   similarly scoped (discovery, retrieval, graph traversal, long-running ops), or narrower for v1?

   _Partially resolved (DEC-0045, DEC-0046, see [answered-questions.md](../questions/answered-questions.md)): fastmcp
   adopted as MCP framework; deployment field in registry schema; v1 tool count and scope TBD at Phase 2a._

4. **Adapter abstraction for non-paper sources.** Beever's `BaseAdapter` + `NormalizedMessage` cleanly separates "where
   the bytes come from" from "what the pipeline does with them." Even ignoring chat, Dan has papers, threads, notes, and
   pics. Is there value in defining a similar `BaseSource` abstraction in KnowledgeBase before more source types
   accumulate, or is that premature?

5. **LiteLLM as the single completion funnel.** Beever's Unreleased work routes every completion through LiteLLM with a
   `fully-local` preset that targets Ollama. Worth adopting LiteLLM as Linus's own provider-routing layer (so a single
   `linus.yaml` declarative config switches between pmetal / Ollama / future hosted models), or is that more
   indirection than a personal-AI orchestration backend warrants?

6. **Capability-layer pattern for the Linus tool registry.** Beever's `src/beever_atlas/capabilities/` shares a single
   implementation across ADK tools and MCP tools. Worth designing Linus's tool registry around the same shape —
   write-once, expose-everywhere — from Phase 2a, or wait for the MCP surface to land first?
