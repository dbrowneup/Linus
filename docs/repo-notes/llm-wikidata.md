# llm-wikidata (`QipengGuo/llm-wikidata`)

## 1. Purpose and scope

`llm-wikidata` is a small (~875 LOC across `src/`, `main.py`, `visualize.py`, `db_manager.py`) Python pipeline that
consumes a JSONL of articles, asks an OpenAI-compatible LLM to summarise each one and emit 5–10 keyword entities, then
links each keyword against a persistent ChromaDB collection of previously seen entities to suppress duplicates. It
positions itself as a Karpathy-LLM-Wiki riff, but in practice it is narrower and more pointed than its sibling
markdown-wiki projects: rather than emitting per-entity wiki pages or a curated repo tree, it produces a flat
`pipeline_results.jsonl` of `(article_id, summary, linked_entities)` tuples plus a vis.js HTML graph rendered by
`visualize.py`. The interesting payload, for Linus's purposes, is the entity-deduplication mechanism inside
`src/pipeline.py`, not the "knowledge graph" output.

## 2. Architecture summary

Four files do the real work. `src/models.py` defines four pydantic models — `Article`, `ExtractionResult` (summary +
keywords), `Entity` (uuid, name, optional description, source article), and a `ResolutionResult` carrying a
"conservative" and an optional "granular" entity name. `src/llm_service.py` wraps the OpenAI SDK (with a deterministic
`MockLLMService` twin for offline runs) and exposes two methods: `extract_summary_and_keywords` and `resolve_entities`.
`src/vector_store.py` is a ~70-line ChromaDB wrapper that adds entities by name and returns top-k neighbours under an L2
distance threshold (default 1.2, top-k 3, default embedder `sentence-transformers/all-MiniLM-L6-v2`). `src/pipeline.py`
is the orchestrator: for each extracted keyword it asks ChromaDB for nearest entities; if none clear the threshold the
keyword becomes a brand-new entity ("Branch A, conservative"); otherwise the LLM is shown the candidates and asked to
return either the canonical `conservative_entity` (one of the candidates, normally) plus optionally a more specific
`granular_entity` ("Branch B"). The resolved entities get written back to ChromaDB, so subsequent articles see them as
candidates. The actual "knowledge graph" is a one-line in-process dict —
`self.knowledge_graph[article_id] = [entity_ids]` — never persisted; `visualize.py` reconstructs a bipartite
article↔entity graph by re-reading `pipeline_results.jsonl`.

## 3. What's reusable in Linus

The genuinely useful idea here is the **entity-recall loop as a duplicate suppressor for LLM-generated KGs**, which is a
real problem any Phase 2/3 KnowledgeBase write-back path will hit. The pattern — vector-search the existing entity set,
hand the LLM the top-k candidates, and prompt it to pick "match an existing entity" vs "create a new one" — is small
(~50 lines), framework-light, and slots cleanly above whatever entity store Linus settles on. The **conservative +
granular dual emission** is also worth borrowing: it sidesteps the most common LLM-KG failure mode (over-specific,
near-duplicate entities like "Llama 4" vs "Meta Llama 4 model") by forcing the model to commit to a broad anchor first
and only optionally specialise. Compared to its sibling `obsidian-llm-wiki-local` (which writes one markdown file per
concept and lets Obsidian's wikilinks be the index), `llm-wikidata` is the only Group 3 repo that treats entity identity
as a first-class problem solved with embeddings rather than filename collisions or hand-curation. That mechanism could
plausibly live as a small `linus.kb.entity_resolver` module independent of whatever graph layer DEC-0026/27 lands on.

## 4. What's inspiration only

Almost everything else. The "knowledge graph" is a Python dict, the visualiser is a vis.js HTML dump, the schema is two
fields wide (name + description), there are no relations between entities (the graph is article→entity bipartite, not
entity→entity), and there's no provenance beyond `source_article_id`. Compared to siblings like `AgenticResearchWiki` or
`llm-research-wiki` which at least produce navigable per-page artefacts, the output here is a JSONL and an HTML —
nothing a human would browse. The example dataset is 100 Chinese-language tech-blog articles from "机器之心"; the
prompts are bilingual but the entity-resolution heuristics may not survive the transition to English biomedical text
without retuning the L2 distance threshold and the resolution prompt.

## 5. What's incompatible or out of scope

The architectural direction is the **opposite** of Linus's KB roadmap. DEC-0015 commits to dual RDF + property graph
with markdown-style claim write-back as the human-readable surface; `llm-wikidata` commits to neither — there is no
triple store, no property graph, no claim structure, no schema beyond `name`/`description`. ChromaDB as the sole entity
registry would not satisfy Linus's need for typed relations, provenance chains, or SPARQL-ish querying. The repo also
has no notion of **agents** in the orchestration sense: the "agent-driven" framing in the group context is generous —
`pipeline.py` is a deterministic for-loop with two LLM calls per article, not a planning or tool-using loop. Adopting
the repo wholesale would mean ripping out the parts Linus has already designed around; adopting the entity-resolution
helper in isolation is the practical path.

## 6. Recommendation: **Study**

Read `src/pipeline.py` and `src/vector_store.py` once, lift the conservative/granular resolution prompt and the
recall-then-resolve loop as a reference implementation when Phase 2 KnowledgeBase ingestion needs an entity
deduplicator, and otherwise leave it alone. Do not vendor; do not depend on; do not let the "LLM Wiki" framing pull the
KB design toward a flat name-only entity store. The 50-line dedup pattern is the whole takeaway.

## 7. Questions for Dan

- **Entity resolution as a Phase 2 KB tool.** Worth carving out a `linus.kb.entity_resolver` module that wraps the
  recall-then-resolve pattern (vector top-k + LLM pick-or-create with conservative/granular emission), independent of
  whatever store DEC-0015 lands on? It's small enough to write from scratch in an afternoon.
- **Distance threshold tuning.** This repo uses L2 ≤ 1.2 against `all-MiniLM-L6-v2` on Chinese tech-blog text. For Dan's
  biomedical corpus that threshold and embedder are both wrong. Is there appetite for a Phase 1/2 micro-bench that picks
  an embedder + threshold against a labelled set of "should-merge / should-not-merge" entity pairs from the paper
  corpus?
- **Conservative/granular split vs single canonical entity.** The dual-emission idea trades one entity for up to two; in
  an RDF setting you'd model the granular as a sub-class or `skos:narrower` of the conservative. Is that the intended
  downstream shape, or do you want a single canonical entity per keyword with the granular treated as a label/alias?
- **Differentiator confidence.** The README sells this as a knowledge-graph project, but the actual KG is a one-line
  dict and the visualisation is bipartite. The genuine differentiator vs the markdown-wiki siblings is the ChromaDB
  entity-recall step, full stop. Agreed, or do you see another piece worth lifting?
