# beever-atlas (`Beever-AI/beever-atlas`)

## 1. Purpose and scope

Beever Atlas is an "LLM-first wiki knowledge base" whose unique source of truth is **team chat** — Slack, Discord,
Microsoft Teams, and Mattermost — rather than papers, PDFs, URLs, or files on disk. It pulls a workspace's channel
history through a TypeScript bot service, runs a six-stage Google-ADK ingestion pipeline that distils raw messages into
atomic facts, entities, and relationships, persists them into a dual semantic-plus-graph memory (Weaviate + Neo4j

- MongoDB + Redis), and continuously rebuilds a per-channel auto-maintained wiki on top. Two consumer surfaces hang off
  that memory: a React dashboard with a streaming QA agent and a `fastmcp`-served MCP endpoint exposing 16 tools to
  Claude Code / Cursor. The README is explicit that the design quotes Karpathy's "LLMs read wikis, not chat logs"
  observation — making this a Group 3 sibling of agentic-wiki-builder, AgenticResearchWiki, llm-research-wiki,
  llm-wikidata, atomic-knowledge, and obsidian-llm-wiki-local — but the chat-as-source axis sets it apart from every
  other repo in that group, which all assume a document/file/URL ingest pattern. It is also the only repo in the group
  that ships as a multi-service Docker Compose product (backend + bot + web + four datastores) targeted at small teams.

## 2. Architecture summary

Three services, four datastores. The Python backend (`src/beever_atlas/`) is a FastAPI app built on **Google ADK**
(`google-adk>=1.28.1`) with `litellm` as the model router and Gemini as the default LLM; embeddings come from Jina v4
(2048-dim). The chat-source layer is a `BaseAdapter` abstraction in `src/beever_atlas/adapters/base.py` that normalises
every platform message into a `NormalizedMessage` dataclass (content, author, platform, channel_id, message_id,
thread_id, attachments, reactions). Concrete adapters live alongside (`bridge.py`, `file_adapter.py`, `mock.py`);
platform-specific protocol work — websocket subscriptions, OAuth, rate-limit handling, Slack mrkdwn, Block Kit
formatting — is pushed out to a separate Node/TypeScript bot service in `bot/src/` with files like `bridge.ts`,
`slack-mrkdwn.ts`, `chat-manager.ts`, `webhook-buffer.ts`, plus SSRF tests for Slack and Mattermost. The Python adapter
then talks to the bot over an HTTP bridge with `BRIDGE_API_KEY` shared-secret auth. The ingestion pipeline
(`agents/ingestion/pipeline.py`) is an ADK `SequentialAgent` with explicit `ParallelAgent` fan-outs: stage 1
preprocesses, stage 2 fans out fact extraction and entity extraction in parallel, stage 3 fans out embedding and
cross-batch contradiction validation in parallel, stage 4 persists into Weaviate (3-tier: channel / topic / atomic fact)
and Neo4j (entity graph). The wiki layer (`src/beever_atlas/wiki/`) is a `gather → compile → cache` pipeline guarded by
a module-level per-channel `asyncio.Lock` so only one regeneration runs per channel at a time regardless of target
language; the QA layer (`agents/query/qa_agent.py`) streams answers over SSE and a smart router picks semantic vs graph
retrieval per question. An `agents/mcp_registry.py` and `fastmcp` server expose a curated 16-tool surface for external
code agents.

## 3. What's reusable in Linus

For Dan's single-user PDF/paper-corpus workflow, the directly portable parts are architectural rather than connector
code. The wiki-first-RAG thesis itself — distil the corpus into a structured per-source wiki at ingestion, then retrieve
against the wiki rather than raw chunks — is the same Karpathy idea agentic-wiki-builder embodies, but beever-atlas
demonstrates it at production scale with a real graph store and a real query router on the back. The
`gather → compile → cache` shape with per-resource async locks (`wiki/builder.py`) is a clean pattern Linus's
KnowledgeBase wiki layer can copy outright. The 6-stage ADK pipeline shows a concrete way to express "preprocess →
(extract facts ‖ extract entities) → (embed ‖ validate) → persist" as a typed pipeline, including the ParallelAgent
placement — Linus's Phase 3 parallel-agents design can lift this skeleton directly. The dual semantic

- graph memory with a smart router is the strongest answer in the Group 3 cohort to the "vector RAG can't do relational
  questions" problem; KnowledgeBase v2 likely wants this shape. The `fastmcp` 16-tool MCP surface is a good reference
  for the eventual Linus MCP server.

The chat-as-source axis is what differentiates beever-atlas from every Group 3 sibling: agentic-wiki-builder ingests
single source files, llm-research-wiki and AgenticResearchWiki ingest research outputs, llm-wikidata targets the
Wikidata schema, atomic-knowledge focuses on ontology, obsidian-llm-wiki-local lives inside an Obsidian vault. None of
those translate to Dan's papers/PDFs corpus directly, and neither does beever-atlas's chat ingest — but the
`BaseAdapter` + `NormalizedMessage` shape is itself a reusable template if Linus ever wants a single PDF / paper / note
/ clipboard adapter API in front of KnowledgeBase.

## 4. What's inspiration only

The four-datastore footprint (Weaviate + Neo4j + MongoDB + Redis), the React dashboard, the bot service, docker-compose
orchestration, OAuth/encryption infrastructure for stored platform credentials, the rate-limit and SSRF-protection
plumbing, the per-agent MCP auth and rate limits — none of this is appropriate for Linus's single- user local context.
The Gemini + Jina API dependency is a clean architectural choice for Beever's hosted scenario but the opposite of
Linus's "no paid APIs required for operation" north star; ADK with `litellm` would in principle let the same pipeline
run against an Ollama or pmetal endpoint, but verifying that is real work and the wiki/QA prompts are tuned for
Gemini-class models. Compared to sibling **agentic-wiki-builder** specifically: agentic-wiki-builder is ~140 lines of
glue around OpenCode and uses git itself as the citation log; beever-atlas is a 30+ KLOC product with explicit citations
linked back to source messages in a managed wiki cache. Dan's KnowledgeBase scale sits closer to the
agentic-wiki-builder end, but Beever's compile-and-cache discipline is what to copy as KnowledgeBase grows.

## 5. What's incompatible or out of scope

Chat platforms aren't a Linus ingest target. Slack/Discord/Teams/Mattermost connectors, the bot service, OAuth flows,
Block Kit formatters, and the encrypted credential vault are zero-utility for Dan's workflow and represent the bulk of
the codebase. Google ADK is a defensible choice but adds a heavy dependency and a programming model that doesn't align
with Linus's planned orchestration layer. Weaviate and Neo4j are both Docker-resident JVM/Go services — fine for a team
appliance, but Linus has been deliberately keeping its data plane in Qdrant + SQLite + filesystem, and neither swap is
free. The Apache 2.0 license is permissive, but the chat-platform nature of the codebase means there are very few files
where lifting code wholesale makes sense — patterns are the value here, not source.

## 6. Recommendation: **Study**

Read for the wiki-first-RAG architecture, the ADK SequentialAgent + ParallelAgent shape of the ingestion pipeline, the
`gather → compile → cache` wiki builder with async per-resource locks, and the dual semantic+graph memory + smart
router. Lift those patterns into KnowledgeBase v2 design. Do not adopt the codebase, the dependency stack (ADK,
Weaviate, Neo4j, Gemini, Jina), or the chat connectors. Revisit if Linus ever grows a "team mode" or if Dan wants
chat-history ingest from his own DMs/Discords (unlikely on the current roadmap).

## 7. Questions for Dan

- **Wiki-first-RAG for KnowledgeBase v2.** Beever's thesis is that retrieval should hit a continuously-distilled per-
  source wiki, not raw chunks. KnowledgeBase v1 is chunk-based RAG. Is "distil each paper into a structured wiki page at
  ingest, then retrieve against that" an explicit Phase 3 design move, or out of scope?
- **Dual semantic + graph memory.** Beever runs Weaviate + Neo4j with a smart router that picks per question. The
  current Linus plan is Qdrant-only. Is a graph store (Neo4j, Memgraph, or even a SQLite-on-disk triple table) on the
  roadmap for relational queries over the paper corpus?

  _Partially resolved (DEC-0015, see [answered-questions.md](../questions/answered-questions.md)): Dual approach
  adopted (RDF via rdflib/SPARQL + property graph); both are Phase 3 KB substrates; Weaviate/Neo4j not adopted._
- **Google ADK as an orchestration framework.** Beever's pipeline is expressed as ADK `SequentialAgent` /
  `ParallelAgent` rather than ad-hoc Python. Is ADK on the table for Linus's orchestration layer, or do we want to own
  the agent-graph abstraction ourselves to keep the dependency surface small?

  _Resolved (DEC-0002, DEC-0020, see [answered-questions.md](../questions/answered-questions.md)): Linus owns its
  orchestration layer; ADK not adopted; scope is sandbox + KB + MCP registry + audit._
- **MCP tool surface.** Beever ships 16 tools through `fastmcp`. Is the Phase 2/3 plan for Linus's MCP surface similarly
  scoped (discovery, retrieval, graph traversal, long-running ops), or narrower for v1?

  _Partially resolved (DEC-0045, DEC-0046, see [answered-questions.md](../questions/answered-questions.md)): fastmcp
  adopted as MCP framework; deployment field in registry schema; v1 tool count and scope TBD at Phase 2a._
- **Adapter abstraction for non-paper sources.** Beever's `BaseAdapter` + `NormalizedMessage` cleanly separates "where
  the bytes come from" from "what the pipeline does with them." Even ignoring chat, Dan has papers, threads, notes, and
  pics. Is there value in defining a similar `BaseSource` abstraction in KnowledgeBase before more source types
  accumulate, or is that premature?
