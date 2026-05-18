# LLM Wiki Synthesis: Karpathy, Rohit v2, and Community Insights

_Synthesized from: Karpathy LLM Wiki Gist, Rohit LLM Wiki v2 Gist, Karpathy LLM Wiki Repos list, Autoresearching Apple's
LLM in a Flash, [COMMUNITY_INSIGHTS.md](../../context/notes/COMMUNITY_INSIGHTS.md),
[KB_DESIGN_PATTERNS.md](../../context/notes/KB_DESIGN_PATTERNS.md)._ _Date: 2026-05-01_

---

## 1. Overview

In April 2026, Andrej Karpathy published a gist describing what he called an "LLM Wiki" — a pattern for using language
models to build and maintain persistent, interlinked personal knowledge bases rather than re-deriving answers from raw
documents on every query. The gist attracted roughly 485 substantive comments from practitioners who had built real
systems on their own hardware, and Rohit Garg (author of the [`agentmemory`](../repo-notes/agentmemory.md) project)
published a follow-on gist extending the pattern with lessons from production use.

The community response is high-signal but not uniformly reliable. The most credible contributors cited specific metrics,
described failure modes, or had clearly shipped real systems (measured context savings, weeks of production use across
multiple projects, enterprise deployments). A meaningful subset of comments are conceptual rather than empirical.
Throughout this document, claims are graded accordingly.

Why does this matter for Linus? The KnowledgeBase submodule is already building on a graph-plus-vector substrate —
exactly the architecture this community is converging on from first principles. What the wiki ecosystem adds is a body
of hard-won operational wisdom about what breaks at scale, what the right quality controls are, and how to keep a
knowledge base from rotting into a junk drawer over months of use. That wisdom is directly applicable to the
KnowledgeBase design and to the session architecture Linus needs for its orchestration layer.

---

## 2. Core Concepts

**The compile-don't-retrieve distinction.** The central claim is that RAG is a retrieval system and a wiki is a
compilation system. RAG finds relevant chunks and re-derives answers on every query. A compiled wiki has already done
the synthesis — cross-references are prebuilt, contradictions already flagged, summaries already written. Queries run
against the compiled artifact, not the raw corpus. The distinction matters practically: at moderate corpus sizes (50-500
papers), the quality difference between retrieving and reasoning versus querying a well-maintained compiled wiki is
substantial.

**Three-layer architecture.** Raw sources (immutable, LLM reads but never writes), the wiki (LLM-owned markdown files,
freely written and revised), and the schema (the CLAUDE.md or AGENTS.md that governs wiki behavior). The schema is not a
setup document — it is the core product. It encodes entity types, relation types, contradiction policy, quality
thresholds, and operational conventions. Without a schema the LLM is a generic chatbot. With one it is a disciplined
knowledge worker.

**Memory lifecycle: confidence decay and supersession.** [Rohit's v2](../repo-notes/agentmemory.md) adds the observation
that knowledge has a lifecycle which the original gist ignores. Every claim should carry a confidence score (source
count, recency, contradiction status). Claims that haven't been accessed or reinforced in months should deprioritize via
Ebbinghaus-style exponential decay. When new information contradicts an existing claim, the old claim should be marked
stale and linked to the new one — preserved but superseded — rather than silently overwritten. For a scientific paper
corpus, methods sections go stale faster than foundational results; this distinction should be encoded in the schema.

**Consolidation tiers.** Raw observations compress through a pipeline: working memory (recent, unprocessed) → episodic
memory (session summaries) → semantic memory (cross-session facts) → procedural memory (workflows extracted from
repeated patterns). Each tier is more compressed, more confident, and longer-lived. This is the architecture that
prevents a wiki from becoming a flat accumulation of everything ever added.

**Typed knowledge graph over flat pages.** Flat wikilinks are a starting point, not a destination. A typed knowledge
graph — with explicit entity types (method, model, dataset, author, concept, tool) and typed relation types (uses,
evaluated-by, contradicts, extends, proposed-by) — enables deterministic graph traversal for scoping queries without LLM
involvement. This is a strict improvement over keyword search or similarity retrieval for "what depends on X?" or "what
methods has this author proposed?"

**Hybrid search: BM25 + vector + graph traversal.** The index.md approach (a single catalog file the LLM reads before
answering queries) works to about 100-200 pages. Past that, the index itself overflows the context window. The mature
retrieval architecture combines BM25 keyword matching, vector similarity search, and graph traversal, fused with
reciprocal rank fusion. Each stream catches things the others miss: BM25 finds exact terms, vectors find semantic
neighbors, graph traversal finds structural connections.

**Scoping is deterministic; reasoning is probabilistic.** The sharpest architectural insight from the community: making
an LLM do set operations (relevance filtering, scope determination) in-context is slow, expensive, and silently lossy.
Relevance should be determined by the graph and index layer, deterministically. The LLM receives a pre-filtered context
bundle and does reasoning over it — which is what it's actually good at. This principle has direct implications for how
Linus should route queries to the KnowledgeBase.

**Epistemic claim typing.** Every factual claim in a wiki page should be explicitly tagged as one of four types:
`[!source]` (verbatim or close paraphrase with citation), `[!analysis]` (inference from sourced facts, with reasoning
shown), `[!unverified]` (no authoritative source), or `[!gap]` (known missing knowledge, never filled with a guess).
Without this discipline, the LLM synthesizes without citing, and humans cannot distinguish grounded claims from
plausible-sounding confabulations. This is especially important for a scientific KB where the cost of a wrong embedded
claim compounds across downstream syntheses.

**Content hashing for staleness detection.** Every compiled KB entry should record the SHA-256 hash of its source files
at compile time. When source files change, entries derived from them are automatically flagged as stale — no LLM
involvement required. This is lightweight to implement and provides deterministic provenance tracking that scales
indefinitely.

**Write-back rule.** Every substantive task produces two outputs: the deliverable (the answer, the analysis, the
synthesis) and updates to the wiki or KB pages touched by the reasoning. Without an explicit rule enforcing this,
knowledge evaporates into chat history. Practitioners who measured this independently called it the single most
impactful operational discipline.

**Quality gate at ingest.** Not everything belongs in the knowledge base. A semantic quality filter applied before
compilation — scoring sources against a domain editorial policy — prevents the KB from degrading into a flat
accumulation of whatever was added. The community consensus from production users: filtering noise at the door beats any
retrieval improvement downstream. The gate should be explicit and auditable, not implicit human judgment.

**The schema is the flywheel.** Every correction, every refined convention, every lesson from a failed ingest belongs in
CLAUDE.md. Over months, the schema accumulates operational wisdom that would otherwise be re-explained every session.
This is the compounding mechanism that makes a well-maintained wiki increasingly valuable rather than increasingly
noisy.

**Two-layer architecture.** A single monolithic wiki doesn't scale to multiple concurrent projects. The right structure
separates a central wiki (reusable cross-project knowledge: entities, concepts, methods, foundational results) from
project-specific wikis (current state, decisions, experiment logs, blockers). For Linus specifically: the paper corpus
naturally fits the central wiki; Linus project state fits the project wiki.

**Speculative linking.** When the LLM writes a page and creates a wikilink to a concept that doesn't have a page yet,
that broken link is a signal, not an error. Red links are a prioritization queue for future ingest work. The
KnowledgeBase graph should track "anticipated" nodes (mentioned but not yet extracted) as a distinct node type.

---

## 3. Most Relevant GitHub Repos

### Inference and Local-First Priority

**[obsidian-llm-wiki-local](../repo-notes/obsidian-llm-wiki-local.md)** (kytmanov/obsidian-llm-wiki-local) — 100% local
Ollama, concept extraction, rejection feedback loop, actively iterating (concept aliases, multi-language support as of
v0.5). Directly relevant because it proves the fully local pattern works without cloud APIs. Relevant to Phase 2 (Linus
MVP) when building the KnowledgeBase interaction layer.

**[NiharShrotri/llm-wiki](../repo-notes/llmwiki.md)** — Python CLI, Ollama plus Qwen3, QMD hybrid search, 3-way query
scope, write-back, contradiction detection. One of the most complete local-first implementations in the thread. Relevant
to Phase 2-3 as a reference for what a complete ingest/query/lint loop looks like in Python.

**[7xuanlu/origin](../repo-notes/origin.md)** — Tauri (Rust) desktop app, background daemon, Qwen3 on Metal, explicit
quality gate at ingest. The quality gate insight (filtering at the door beats retrieval improvements) came from this
builder. Relevant to Phase 2; the Metal backend and Rust architecture are directly applicable to Linus's hardware
targets.

**[nashsu/llm_wiki](../repo-notes/llmwiki-cli.md)** — Cross-platform Tauri (Rust), Ollama plus multi-provider, 3-column
layout with graph view. Relevant to Phase 5 (interface) and for understanding what a native desktop shell looks like on
the same Rust/Tauri stack Linus might eventually use.

### Knowledge Graph and Retrieval

**[jgoldfed/keppi](../repo-notes/keppi.md)** — Weighted directed graph built from wikilinks, tags, and frontmatter.
Blast-radius analysis (what does updating this node affect?), Louvain community detection, gap detection, 19-tool
FastMCP server. Tested on 1,471 notes and 267K edges. The blast-radius (`build_context_pack` greedy-fill to a token
budget) and gap-detection concepts are directly applicable to the paper library in KnowledgeBase. Keppi and
[hyalo](../repo-notes/hyalo.md) together constitute the Phase 3 KB tooling layer (lint + transactional link rewrites +
bounded-BFS-with-decay retrieval). Relevant to Phase 3 (KB/Parallel Agents).

**[omega-memory/omega-memory](../repo-notes/omega-memory.md)** — Local semantic search: FTS5 plus vector embeddings plus
cross-encoder reranking, all on-device. 95.4% on LongMemEval at 50ms retrieval. Solves the index.md scaling problem
without requiring a heavy vector database. Directly relevant to Phase 3 when the KnowledgeBase grows past 200 nodes and
the index-file approach breaks down.

**[vectorlessflow/vectorless](../repo-notes/vectorless.md)** — Knowledge graph traversal for document retrieval with no
vector database. Builds a knowledge link graph for contextual retrieval. Relevant to Phase 3 as an alternative retrieval
architecture for cases where vector DB overhead is undesirable.

**[QipengGuo/llm-wikidata](../repo-notes/llm-wikidata.md)** — Combines LLMs and ChromaDB to recall existing entities
before inserting new ones, preventing duplicate or hallucinated graph nodes. The entity deduplication approach (checking
for existing nodes before creating new ones) is a concrete solution to the concept-drift problem the community
identified as the hardest part of graph construction. Phase 3.

**[Tencent/WeKnora](../repo-notes/WeKnora.md)** — Auto-built wiki plus typed knowledge graph (Neo4j), wiki-grounded
retrieval, Chrome extension for ingestion. Apache 2.0. The typed graph architecture and wiki-grounded retrieval pattern
are worth studying, even if Neo4j itself is heavier than what Linus needs. Phase 3.

### Provenance and Citation Integrity

**[badwally/TheKnowledge](../repo-notes/TheKnowledge.md)** — Write-validator pattern: rejects any wiki page write that
doesn't include a resolved `[[sources/]]` link to an already-ingested file. Span anchors to exact timestamps and pages.
Bidirectional backlinks maintained automatically. This is the most rigorous citation enforcement implementation in the
thread. Relevant to Phase 2-3 for KnowledgeBase metadata curation.

**[gayawellness/anamnesis](../repo-notes/anamnesis.md)** — Purpose-built provenance layer tracking how knowledge was
compiled, why decisions were made, and what superseded what. "The wiki is the codebase; Anamnesis is the git log."
Running 13 agents in production. The multi-agent provenance architecture is directly applicable to Linus's parallel
agent work in Phase 3.

**[ap0phasi/agentic-wiki-builder](../repo-notes/agentic-wiki-builder.md)** — Git branch per ingestion. Every source is
processed on its own branch, enabling contamination tracing: if a bad source corrupts wiki claims, the branch history
lets you identify exactly what it touched and revert selectively. Phase 3 (parallel agents).

**[do-y-lee/wikiloom](../repo-notes/wikiloom.md)** — Chunk-level SHA-256 hashing with source traceability. Storing
`sha256(source_hash + chunk_index)` in page frontmatter gives a direct line from any wiki claim to the exact passage in
the raw source. Human-edit protection. Phase 2-3.

### Agent Memory and MCP

**[rohitg00/agentmemory](../repo-notes/agentmemory.md)** — BM25 plus vector plus knowledge graph, RRF fusion, 95.2% on
LongMemEval-S, 51 MCP tools (plus 107 REST endpoints). Knowledge graph extraction optional. This is the production
implementation behind the Rohit v2 gist. The 13-hook lifecycle taxonomy (`SessionStart` through `TaskCompleted`) is the
most directly liftable element for the Phase 2 episodic memory layer (DEC-0029) — a worked catalog of which Claude Code
lifecycle events Layer C needs to subscribe to. Relevant as a reference architecture for Linus's memory layer. Phase
2-3.

**[bitsofchris/openaugi](../repo-notes/openaugi.md)** — "Links are the whole thing" — treats tags and links as
first-class graph nodes. Two-table SQLite schema (`blocks`, `links`), sqlite-vec + FTS5 in one file, 17-tool MCP server,
write-back from chat conversations. Minimal dependency footprint. The two-table schema is the closest existing match to
the DEC-0029 v0 episodic substrate (same `content_hash`-keyed IDs, same WAL mode, same FTS5 + vector in a single file) —
the g4-memory synthesis identifies it as the candidate to lift almost verbatim for the Phase 2 episodic memory layer.
Relevant to Phase 2 as both KB substrate reference and simplest graph-backed memory implementation with MCP integration.

**[axoviq-ai/synthadoc](../repo-notes/synthadoc.md)** — Multi-provider including Ollama, contradiction detection,
confidence thresholds, HITL review queue, audit trail, 6 file format ingesters (PDF, DOCX, PPTX, images, URLs,
spreadsheets). The most complete batteries-included implementation that remains local-first. Relevant to Phase 2-3; the
contradiction detection and HITL queue are immediately applicable to KnowledgeBase.

**redmizt/multi-agent-wiki-toolkit** — Flat files plus bash plus Python plus git. No database, no external services.
Deterministic and reproducible. 18 architectural extensions for multi-agent production use. Relevant to Phase 3 parallel
agent work; the no-external-services constraint matches Linus's minimal dependency philosophy.

### Lightweight CLI and Tooling

**[tobi/qmd](../repo-notes/qmd.md)** — Local hybrid search engine: BM25 plus vector plus LLM reranking. Both CLI and MCP
server. All on-device. Explicitly recommended by Karpathy as the search solution for wikis that outgrow index.md. Phase
3 when search is needed.

**ilya-epifanov/llmwiki-tooling** — CLI for linting, checking and fixing links, enforcing frontmatter fields. Designed
to be driven by AI agents. Saves tokens versus freeform linting. Phase 2-3 for KnowledgeBase lint automation.

**[HawHello/AgenticResearchWiki](../repo-notes/AgenticResearchWiki.md)** — Wiki holds data paths, training configs, and
eval records. Agent enters from Overview.md and writes records back. Compounds project memory (not just knowledge).
Directly relevant to Linus's experiment tracking needs. Phase 1-2.

### Specialized

**[MetamusicX/llm-research-wiki](../repo-notes/llm-research-wiki.md)** — Academic research template with domain-specific
page types: concepts, authors, debates, syntheses. First ingest produced 38 interlinked pages from one source. A useful
template for how a scientific paper corpus should organize its entity types. Phase 2-3 for KnowledgeBase.

**[EtienneChollet/ontomics](../repo-notes/ontomics.md)** — Tree-sitter AST plus TF-IDF plus code embeddings to generate
a semantic index of a codebase's domain vocabulary (concepts, conventions, abbreviations, behavioral clusters). Exposed
as MCP tools. Deterministic, no hallucination. Relevant to Phase 2 when Linus wants to give Worker agents semantic
access to the Linus codebase itself.

---

## 4. Community Insights Most Relevant to Linus

**The hot cache pattern eliminates session re-explanation cost.** A `session/hot.md` file of roughly 500 words — current
task, recent decisions, active blockers, what must not be reverted — loaded at every session start costs less than 0.25%
of a 200K context window and eliminates 2-3K tokens of re-explanation per session. One practitioner measured 2.7x
context savings ratio (192.6 KB processed, 122.4 KB kept out of context) using a two-file startup plus BM25 search over
session transcripts for historical context. Linus should implement this immediately in the orchestration layer as a
session context injection mechanism. The existing CLAUDE.md session startup protocol is the right place to formalize it.

**Classify documents before extracting from them.** Every document type needs a different extraction template. A 50-page
empirical paper needs methodology rigor checks. A preprint needs a "not peer-reviewed" flag. A dataset needs provenance
and license fields. A review article needs coverage period. Without type classification, summaries are uniformly
shallow. For KnowledgeBase, the existing paper-focused pipeline should be expanded to at least six document types, each
with required frontmatter fields and extraction prompts. This validates and extends the current metadata design.

**Epistemic integrity is the hardest unsolved problem.** Multiple serious practitioners raised the same concern
independently: an LLM wiki can synthesize without citing, drift from sources without knowing it, and present false
certainty where disagreement exists. The concrete mitigations the community converged on — claim typing (`[!source]`,
`[!analysis]`, `[!unverified]`, `[!gap]`), content hashing for staleness detection, explicit contradiction policy in the
schema, LLM as diff-proposer rather than silent overwriter — should all be incorporated into the KnowledgeBase schema.
This is not a nice-to-have for a scientific corpus; it is the difference between a KB that earns trust over time and one
that silently corrodes it.

**Scoping should be deterministic.** This is the clearest architectural principle from the community discussions:
relevance filtering ("what's relevant to this query?") should be handled by the graph, BM25, or metadata filters — not
by asking the LLM to read a large index and decide in-context. For Linus's query routing, this means the knowledge graph
should be the primary scoping layer, and the LLM should receive a pre-filtered context bundle. This validates the
graph-plus-vector substrate KnowledgeBase is building.

**The write-back rule.** Every session, every synthesis, every useful connection found should be filed back into the
wiki or KB. Practitioners who implemented this rule explicitly reported it as the single discipline that makes the
difference between a KB that compounds and one that stays flat. For Linus, this means every Worker task invocation
should end with KB update proposals, not just the primary deliverable.

**The schema is the compounding flywheel.** One enterprise practitioner running this across 15 stakeholders for months
reported: every correction filed back into CLAUDE.md means the same mistake never happens again. Over months the schema
encodes accumulated operational wisdom. Linus already has this intuition embedded in CLAUDE.md's Known Library Quirks
section. The explicit "Learned Corrections" pattern should be formalized with a dedicated section and a lint rule that
periodically consolidates entries.

**Quality gate at ingest beats retrieval improvements.** A semantic scoring step before any source is compiled into the
KB — applied against a domain editorial policy — is more impactful than any retrieval optimization downstream. For
KnowledgeBase this should be a formal, auditable YAML policy file, not implicit human judgment. DEC-0019 resolved the
hard-gate framing as a quality surface: no hard reject lane in Phase 2; sources are scored and flagged (preprints marked
`preprint: true`, quality scorecard surfaced in retrieval context) rather than filtered out, preserving signal Dan has
already vetted. Sources do not fail the gate — they carry transparent quality metadata.

**Ingest idempotency via content hashing.** Re-ingesting the same source (unchanged) slowly distorts the wiki by
reinforcing its claims artificially. Every source should have its content hash checked against the ingest log before
compilation proceeds. This is a one-line check that prevents a class of silent distortions.

**Speculative linking: red links are features.** When the LLM creates a wikilink to a concept that doesn't have a page
yet, that broken link is a prioritization queue for future ingest work, not an error to suppress. KnowledgeBase's graph
should track anticipated nodes as a distinct type. This is a direct practical implication for the graph schema.

**Counter-arguments and the FUNGI framework.** Every concept page should have a counter-arguments section. When a corpus
is skewed (which a personal paper library always is), the knowledge base develops a skewed picture unless the schema
actively requires engagement with opposing evidence. The FUNGI framework (Frame, Unearth, Network, Grow, Interrogate)
provides a practical five-step ingest protocol for maintaining epistemic balance. For a scientific KB, the Interrogate
step is especially important: every new claim should be accompanied by an explicit search for the strongest
counter-evidence in the existing corpus.

**Dual-layer architecture prevents cross-project contamination.** A central wiki (reusable entities, concepts, methods)
plus project-specific wikis (state, decisions, experiments) is the mature structure. For Linus, the paper corpus lives
in the central wiki; Linus orchestration state lives in the project wiki. The `Actuel/Archive` pattern within project
pages (old entries compressed to archive with date, never deleted) preserves institutional memory without accumulation
noise.

**The index.md scaling wall is predictable and should be planned for.** It arrives at roughly 100-200 pages. Planning
the retrieval upgrade (BM25 plus vector search) before the wall hits, rather than after, avoids a painful migration.
KnowledgeBase should add hybrid retrieval as a Phase 3 deliverable with explicit capacity planning for when the index
file outgrows the context window.

---

## 5. KB Design Patterns

[KB_DESIGN_PATTERNS.md](../../context/notes/KB_DESIGN_PATTERNS.md) translates the community learnings into twelve
concrete, actionable patterns with CLAUDE.md rules and directory structures. The document is immediately applicable and
should be treated as a design specification for the next KnowledgeBase sprint.

The patterns that map most directly onto Linus's current KnowledgeBase architecture are:

The session hot cache (Pattern 1) and four-level progressive disclosure (Pattern 2) apply directly to the Linus
orchestration layer's session management, not just KnowledgeBase. A Linus session that injects 200 tokens of hot
context, a 1-2K token index, and then pulls specific pages on demand is far more efficient than one that reads files ad
hoc.

Document type classification (Pattern 3) validates and extends what KnowledgeBase is doing. The suggested types —
`paper_empirical`, `paper_theoretical`, `paper_review`, `preprint`, `dataset`, `technical_report` — are a reasonable
starting set for the paper corpus. Each type should have required frontmatter fields and type-specific extraction
prompts.

Claim typing (Pattern 4) and content hashing (Pattern 5) are the two patterns with the highest epistemic ROI. They
should be implemented together: every claim knows its source and every source has a hash. A lint pass that checks hash
mismatches and claim type completeness catches both stale knowledge and unsourced synthesis. Neither requires any new
infrastructure — just schema discipline.

The explicit contradiction policy (Pattern 6) is the one pattern that most directly prevents long-term KB decay. Without
it, contradictions between papers are silently resolved by whichever source was ingested last. With it, contradictions
are flagged at write time, preserved, and require human resolution before a claim is marked canonical. This is
especially important for a scientific corpus where genuine contradictions between papers are common and meaningful.

The typed entity system with explicit relation types (Pattern 11) aligns with what KnowledgeBase's graph substrate
already supports. The suggested entity types (method, model, dataset, metric, author, institution, paper, concept, tool)
and relation types (is-a, part-of, uses, evaluated-by, proposed-by, contradicts, extends, implemented-by) should be
encoded in the KnowledgeBase schema and enforced at write time. Free-form wikilinks without relation types should be a
lint error.

The two-layer architecture (Pattern 12) provides the directory structure Linus needs for the session context pattern.
The proposed structure — a central `wiki/` for reusable knowledge and a `projects/linus/` for project state — is a clean
fit for the current repo layout.

The anti-patterns section deserves equal attention: silent overwrite, treating index.md as the primary retrieval
mechanism past 200 pages, accepting "mostly correct" for high-stakes content, ingest without idempotency, and deferred
contradiction resolution are the failure modes that cause production KB systems to rot. Each has a specific mitigation
and each mitigation should appear in the KnowledgeBase CLAUDE.md schema.

---

## 6. Autoresearch and the LLM-in-a-Flash Connection

The "Autoresearching Apple's LLM in a Flash" thread is a first-person account by Dan Woods of running Qwen 3.5 397B on
an M3 Max MacBook Pro — a 209 GB MoE model producing approximately 4.4 tokens per second with production-quality output
including tool calling, using 5.5 GB resident memory, with no Python in the hot path. The paper and code are in
[`repos/flash-moe`](../repo-notes/flash-moe.md), which Linus already has cloned.

Several things in the thread connect directly to Linus's current landscape:

The methodology is exactly the autoresearch pattern Karpathy described and that
[`repos/autoresearch`](../repo-notes/autoresearch.md) and [`repos/autoresearch-mlx`](../repo-notes/autoresearch-mlx.md)
implement. Dan Woods gave Claude Opus a metric to optimize (tokens per second), a goal ("never stop until you hit this
number"), reference materials (the LLM in a Flash paper, Maderix's ANE reverse-engineering work — also in
[`repos/ANE`](../repo-notes/ANE.md)), and let it run for 24 hours and 90 experiments. 42% of experiments were discarded.
The flash-moe pattern emerged from that search. This is not inspiration; this is the exact methodology Linus is planning
to use for its own performance optimization work, and it has a concrete, documented success case.

The hardware findings are directly relevant. The M3 Max achieves 17.5 GB/s sequential SSD reads, which is 3x faster than
the M1 Max that the LLM in a Flash paper benchmarked. The M1 Max in the Linus hardware is at the low end of this
trajectory, but the architecture is the same. The theoretical throughput floor for the M1 Max stack (limited by SSD
bandwidth) is calculable from the paper's methodology.

The most counterintuitive finding — deleting the hand-engineered 9.8 GB Metal LRU expert cache made everything 38%
faster — is a lesson that generalizes well beyond flash streaming. Application-level caches that compete with the OS
buffer cache harm performance by forcing the hardware memory compressor to work continuously. The lesson is: trust the
hardware, get the software out of the way. This applies to any inference optimization work Linus undertakes on Apple
Silicon.

The MoE sparsity insight is relevant to future model selection. MoE models at inference time activate a tiny fraction of
their expert weights per token (Qwen 3.5 397B activates 10 of 512 experts; this can be pruned to 4 with no quality
degradation). That means expert weight blocks are small enough to stream from SSD effectively. Any future Linus model
selection for flash-mode inference should prioritize MoE architectures where total parameter count vastly exceeds active
parameter count.

The thread also demonstrates that the ANE work in [`repos/ANE`](../repo-notes/ANE.md) (Maderix's reverse-engineering)
was a direct input to the flash-moe optimization — the ANE architecture knowledge informed where the Metal cache was
hurting rather than helping. Linus has both `repos/ANE` and `repos/flash-moe`; these should be read as companion
materials.

---

## 7. New Open Questions for Linus

**At what corpus size does the KnowledgeBase index file become the bottleneck?** The community consensus is 100-200
pages. KnowledgeBase should instrument its current index size and establish a concrete threshold that triggers the
hybrid search upgrade. What is Linus's current node count, and what's the growth trajectory? Planning the retrieval
upgrade before the wall hits matters.

**How should Linus implement the write-back rule across parallel Workers?** The write-back rule (every task produces a
deliverable plus KB updates) is straightforward for a single agent. For Linus's parallel agent architecture in Phase 3,
multiple Workers may simultaneously propose updates to the same KB pages. DEC-0022 resolved the policy-level question:
serialized writes through a coordinator, Workers emit JSON diff proposals rather than writing directly, conflicts flag
for human review before merge. The open implementation question (tracked as R2-22) is the specific coordination
mechanism — lease, optimistic-merge, or branch-per-Worker — which resolves during Phase 3 implementation rather than
requiring an advance architectural decision now.

**What is the right confidence decay rate for different claim types in a scientific corpus?** Rohit's v2 proposes
Ebbinghaus decay — exponential with time, reset on access or confirmation. Methods sections decay faster than
foundational results. But what are the right decay constants for Dan's specific domains (genomics, computational
biology, ML inference)? This is an empirical question that requires running the system and measuring how often flagged
"stale" claims turn out to actually be stale.

**Can the FUNGI processing protocol be formalized as a KnowledgeBase ingest step?** The five-step protocol (Frame,
Unearth, Network, Grow, Interrogate) is a natural fit for paper ingestion — it forces explicit counter-argument search
before filing a claim. Is it tractable to run this protocol on every paper with a local Qwen2.5 Worker, or does the
Interrogate step require a stronger model? What would the quality difference look like?

**How does flash-mode inference interact with the multi-expert activation pruning finding?** The flash-moe work found
that pruning from K=10 to K=4 experts had no quality degradation but K=3 caused immediate collapse. Is this threshold
model-specific or architecture-general? For future Linus model selection using flash streaming, understanding the safe
pruning floor across MoE architectures matters for sizing storage and bandwidth budgets.

**Should Linus adopt immutable atomic notes (Zettelkasten) or mutable wiki pages?** The community is split on this.
Mutable wiki pages are easier to keep current but create silent overwrite risks and make provenance harder. Immutable
atomic notes with stable IDs make every claim traceable to its original write but require a separate synthesis layer.
Given that KnowledgeBase is already structured around entity pages (which are naturally mutable as papers are added), is
there a hybrid that gets the provenance benefits of immutability without the overhead?

**What is the right entity deduplication threshold for KnowledgeBase?** KevinYoung-Kw's system uses >60% entity overlap
as the threshold for updating an existing page rather than creating a new one. The community identified concept
deduplication ("attention mechanism" vs "self-attention") as the hardest part of graph construction. What threshold
works for Dan's scientific domain, and can a local model run this check reliably at ingest time?

**How should Linus handle the "mostly correct is broken" problem for high-stakes content?** For formal specifications,
reproducible protocols, and method descriptions in the KB, a mostly-correct summary is not a degraded state — it is a
broken state. Should those content types use the wiki only as a navigation/pointer layer to pre-validated source
material, with the wiki itself prohibited from being the authoritative content? What are the right domain categories for
this distinction in Dan's corpus?

**What does the entrepreneurial application surface look like for a private compiled KB?** The Karpathy pattern and the
community implementations are almost entirely personal or team-internal. The business/team use cases mentioned (internal
wiki fed by Slack, customer calls, meeting transcripts; competitive analysis; due diligence) suggest that a
well-implemented compiled KB with strong provenance controls could be a differentiated product. What would a
Linus-derived KB-as-a-service look like for a small lab or startup? What are the privacy and custody requirements that
matter?

---

## 8. Suggested Additions to Linus repos/

These are repos worth cloning into `repos/` as reference material, with justification. All are local-first or
architecture-relevant; none require CUDA.

**omega-memory/omega-memory** — The retrieval architecture (FTS5 plus vector plus cross-encoder, 95.4% accuracy at 50ms)
is the most complete local on-device retrieval implementation in the thread. Clone as `repos/omega-memory`. Phase 3
reference for the retrieval upgrade.

**jgoldfed/keppi** — The blast-radius analysis, Louvain community detection, and gap detection concepts applied to a
real KG of 1,471 notes and 267K edges. Clone as `repos/keppi`. The graph traversal techniques are directly applicable to
KnowledgeBase. Phase 3 reference.

**rohitg00/agentmemory** — The production implementation behind the Rohit v2 gist: BM25 plus vector plus KG, RRF fusion,
51 MCP tools. Clone as `repos/agentmemory`. Phase 2-3 reference for the memory/retrieval layer architecture and the
13-hook Claude Code lifecycle taxonomy.

**bitsofchris/openaugi** — The simplest complete implementation of graph-backed memory with MCP and write-back from
chat. One SQLite file. Clone as `repos/openaugi`. A useful minimal reference before implementing something more complex.

**tobi/qmd** — Local hybrid search CLI and MCP server. Karpathy explicitly recommended it. Clone as `repos/qmd`. Phase 3
when the index.md wall arrives.

**badwally/TheKnowledge** — The write-validator pattern (reject writes without valid source links) is worth studying as
a reference implementation before designing the KnowledgeBase write discipline. Clone as `repos/the-knowledge`. Phase
2-3.

**redmizt/multi-agent-wiki-toolkit** — Flat files, bash, Python, git, no external services. 18 architectural extensions
for multi-agent production. Clone as `repos/multi-agent-wiki`. Phase 3 parallel agent reference.

**HawHello/AgenticResearchWiki** — The pattern of using the wiki to store data paths, training configs, and eval records
(compounding project memory, not just knowledge) is a useful complement to what `repos/autoresearch` does for the
research loop itself. Clone as `repos/agentic-research-wiki`. Phase 1-2.

Do not clone: anything requiring PostgreSQL, Neo4j, or CUDA in the hot path; cloud-only systems; or repos that are pure
front-ends without reusable architectural content (Tauri desktop apps are useful to study in the browser but not as
reference implementations for Linus's current phase).

---

_This document should be updated when the KnowledgeBase schema is next revised or when Phase 3 parallel agent work
begins. Key references: [KB_DESIGN_PATTERNS.md](../../context/notes/KB_DESIGN_PATTERNS.md) for implementation patterns,
[repos/flash-moe](../repo-notes/flash-moe.md) for the autoresearch methodology applied to Apple Silicon inference,
[repos/autoresearch](../repo-notes/autoresearch.md) and [repos/autoresearch-mlx](../repo-notes/autoresearch-mlx.md) for
the research loop framework._

---

## References

### Repo-notes

- [`AgenticResearchWiki`](../repo-notes/AgenticResearchWiki.md) — Wiki holds data paths, training configs, and eval
  records; compounds project memory via two ready-to-install Claude Code Skills.
- [`ANE`](../repo-notes/ANE.md) — Maderix's Apple Neural Engine reverse-engineering reference; companion input to the
  flash-moe optimization work.
- [`agentic-wiki-builder`](../repo-notes/agentic-wiki-builder.md) — Git-branch-per-ingestion provenance model with
  DuckDB+NetworkX linker for contamination tracing.
- [`agentmemory`](../repo-notes/agentmemory.md) — Production reference architecture behind Rohit v2 gist; BM25 + vector
  - KG with RRF fusion, 95.2% on LongMemEval-S, 51 MCP tools, 13-hook lifecycle.
- [`anamnesis`](../repo-notes/anamnesis.md) — Purpose-built provenance layer ("the wiki is the codebase; Anamnesis is
  the git log") running 13 agents in production.
- [`autoresearch`](../repo-notes/autoresearch.md) — Research loop framework implementing Karpathy's autoresearch pattern
  (metric + goal + reference materials + extended run).
- [`autoresearch-mlx`](../repo-notes/autoresearch-mlx.md) — MLX-targeted autoresearch variant; companion to autoresearch
  for Apple Silicon optimization workflows.
- [`flash-moe`](../repo-notes/flash-moe.md) — Streaming 397B-parameter MoE on M3 Max via the autoresearch pattern;
  documented success case for Linus's planned performance methodology.
- [`hyalo`](../repo-notes/hyalo.md) — Phase 3 KB tooling complement to keppi: transactional link rewrites with
  schema-validated authoring; together they form the Phase 3 KB tooling layer.
- [`keppi`](../repo-notes/keppi.md) — Weighted directed graph from wikilinks/tags/frontmatter with blast-radius analysis
  and 19-tool FastMCP server; tested on 1,471 notes / 267K edges.
- [`llm-research-wiki`](../repo-notes/llm-research-wiki.md) — Academic-research template with domain-specific page types
  (concepts, authors, debates, syntheses).
- [`llm-wikidata`](../repo-notes/llm-wikidata.md) — Entity-deduplication pattern using LLMs plus ChromaDB to recall
  existing entities before insert.
- [`llmwiki`](../repo-notes/llmwiki.md) — NiharShrotri's Python CLI: Ollama plus Qwen3, QMD hybrid search, 3-way query
  scope, write-back, contradiction detection.
- [`llmwiki-cli`](../repo-notes/llmwiki-cli.md) — nashsu's cross-platform Tauri (Rust) shell with Ollama plus
  multi-provider and 3-column graph-view layout.
- [`obsidian-llm-wiki-local`](../repo-notes/obsidian-llm-wiki-local.md) — 100% local Ollama wiki with concept extraction
  and rejection feedback loop; proves the fully-local pattern.
- [`omega-memory`](../repo-notes/omega-memory.md) — Local semantic search (FTS5 + vector + cross-encoder rerank) hitting
  95.4% on LongMemEval at 50ms retrieval; solves the index.md scaling wall.
- [`ontomics`](../repo-notes/ontomics.md) — Tree-sitter AST plus TF-IDF plus code embeddings producing a deterministic
  semantic index of a codebase's domain vocabulary; exposed as MCP tools.
- [`openaugi`](../repo-notes/openaugi.md) — "Links are the whole thing": two-table SQLite schema (`blocks`, `links`)
  with sqlite-vec + FTS5, 17-tool MCP server, write-back from chat.
- [`origin`](../repo-notes/origin.md) — Tauri (Rust) desktop app with background daemon, Qwen3 on Metal, and explicit
  quality gate at ingest.
- [`qmd`](../repo-notes/qmd.md) — Local hybrid search engine (BM25 + vector + LLM rerank) and MCP server; explicitly
  recommended by Karpathy for wikis past the index.md wall.
- [`synthadoc`](../repo-notes/synthadoc.md) — Multi-provider including Ollama with contradiction detection, confidence
  thresholds, HITL review queue, audit trail, six file format ingesters.
- [`TheKnowledge`](../repo-notes/TheKnowledge.md) — Write-validator pattern: hard-rejects any wiki page write without a
  resolved `[[sources/]]` link; the most rigorous citation enforcement in the corpus.
- [`vectorless`](../repo-notes/vectorless.md) — Knowledge-graph traversal for document retrieval with no vector database
  via a knowledge-link graph for contextual retrieval.
- [`WeKnora`](../repo-notes/WeKnora.md) — Tencent's auto-built wiki plus typed knowledge graph (Neo4j) with
  wiki-grounded retrieval and a Chrome ingestion extension.
- [`wikiloom`](../repo-notes/wikiloom.md) — Chunk-level SHA-256 hashing with source traceability via
  `sha256(source_hash + chunk_index)` in page frontmatter.
