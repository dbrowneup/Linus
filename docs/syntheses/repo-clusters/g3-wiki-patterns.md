# Group 3 Synthesis — LLM Wiki Agent-Driven Build Patterns

_Date: 2026-05-04 (updated 2026-05-08). Inputs: seven repo notes (agentic-wiki-builder, AgenticResearchWiki,
llm-research-wiki, llm-wikidata, atomic-knowledge, beever-atlas, obsidian-llm-wiki-local) read alongside the
llm-wiki-synthesis, security-synthesis, skills-and-practices-synthesis, memory-synthesis, and the Crossing 3 / Crossing
4 sections of total-landscape.md._

---

## What this document is

This synthesis covers the seven "workflow and schema" repos that responded to Karpathy's April 2026 LLM Wiki gist — not
by shipping runtimes, but by publishing agent protocols, ingest pipelines, page schemas, and vault conventions. The G2
cluster (engines) and G3 cluster (build patterns) together constitute 18 LLM Wiki repos, all Study-only. The G2
synthesis explains at length why none of those engines are Integrate-recommended; G3 should not re-derive that finding.
G3's distinct contribution is the workflow and schema layer: the patterns that shape what an agent does with a local
model, rather than which model it runs or how fast it runs.

---

## The unifying thesis

All seven repos are answering the same design question: what conventions does an agent need in order to turn raw
documents into a knowledge base that compounds rather than accumulates? Their answers vary in ambition and
implementation — from a 475-line `CLAUDE.md` to a 30-KLOC multi-service product — but the structural shape that recurs
across all seven is the same. There is a raw layer that the agent reads but does not modify. There is a compiled layer
(wiki pages, entities, insight records) that the agent writes and maintains. There is a schema layer (CLAUDE.md,
AGENT.md, AGENTS.md, frontmatter templates) that governs how the agent behaves at both layers. The schema layer is the
real product in every case; the specific file formats and tooling are secondary.

That thesis connects directly to what the llm-wiki-synthesis calls "the schema is the flywheel" and what Crossing 3 in
total-landscape.md identifies as the load-bearing Phase 2 KB design requirement: without typed entities, a contradiction
policy, and epistemic discipline built in from the beginning, a KB is a junk drawer that grows faster than it can be
used. G3 provides seven concrete existence proofs — varying from minimal to elaborate — of what that schema layer looks
like in practice.

---

## Pattern convergence — workflow shapes that recur

Several structural choices appear in multiple repos without coordination, which makes them stronger evidence.

The **immutable raw layer** appears in every repo that has an ingest path at all. llm-research-wiki calls its folder
`raw/` and says the agent reads but never modifies it. obsidian-llm-wiki-local enforces the same with SHA-256 hashing
and atomic rename writes that would fail if they touched `raw/`. atomic-knowledge puts its captures under `raw/sources/`
and distinguishes them architecturally from every other tier. This pattern has no design cost and substantial epistemic
benefit: it means the compiled wiki can always be regenerated from the same inputs, and claims can be traced back to
sources whose content is guaranteed unchanged.

The **three-tier read routing** — a hot-cache index first, then synthesis pages, then individual concept pages — appears
in llm-research-wiki's cluster→synthesis→`related:` cascade and in atomic-knowledge's explicit entry-page-first routing
order (`active → recent → index → project → procedure → insight → concept/entity → candidate`). Both repos solved the
same scaling problem independently: at 100+ pages the index outgrows the context window, so the agent needs a hierarchy
that lets it locate relevant material without reading everything. The llm-wiki-synthesis named this the "100-200 node
wall"; G3 offers two concrete implementations.

The **write-back loop** — the discipline that every agent task produces knowledge updates, not just a primary result —
shows up explicitly in AgenticResearchWiki's `project-doc-update` skill, in llm-research-wiki's INGEST workflow ("log
everything"), and in obsidian-llm-wiki-local's SQLite state machine that tracks each note from `new` through
`published`. Without this loop, knowledge evaporates into chat history; the llm-wiki-synthesis identified it as the
single most impactful operational discipline from the practitioner community.

The **quality gate at ingest** — inspect or discuss a source before writing anything to the wiki — appears in
llm-research-wiki's "discuss takeaways with the user before writing" beat, in llm-wikidata's entity-recall-then-resolve
loop that checks for duplicates before creating new entities, and in obsidian-llm-wiki-local's two-model pipeline (a
fast model extracts concepts, a heavy model compiles articles, human review gates publication). G3 shows that this gate
is composable: it can be a human conversation step, an embedding-similarity check, or a model-size stratification — and
Linus can combine all three in its KB ingest tool.

---

## Differentiators — where the cluster diverges

The repos split primarily along two axes: how much schema they impose, and where they put their complexity budget.

llm-research-wiki and atomic-knowledge are the most schema-heavy. llm-research-wiki's six named page types with
mandatory YAML frontmatter and three formalized workflows (INGEST, QUERY, LINT) is the most complete schema in the
group. atomic-knowledge adds a seventh type (`procedure`) and formalizes the retrieval order, candidate lifecycle, and
lint workflow in separate prose documents. These two repos are complementary rather than competing.

agentic-wiki-builder and AgenticResearchWiki sit at the other end: minimal schema, maximum workflow automation.
agentic-wiki-builder commits its complexity budget to the git-branch-per-session provenance model and the
DuckDB+NetworkX linker; its wiki pages have no mandated structure. AgenticResearchWiki commits its budget to two
ready-to-install Claude Code Skills and a `CLAUDE.md` navigation discipline. Both treat schema as something the human
discovers incrementally rather than something imposed up front.

beever-atlas is the production-scale outlier. Its `gather → compile → cache` pipeline with per-channel async locks, dual
semantic+graph memory, and 16 MCP tools is architecturally the most mature. But the chat-as-source axis makes almost
none of its code portable to Dan's paper-corpus workflow, and its four-datastore footprint (Weaviate + Neo4j + MongoDB +
Redis) is incompatible with Linus's minimal-infrastructure philosophy.

obsidian-llm-wiki-local and llm-wikidata occupy a different plane entirely: they are the only repos in the group that
ship production-quality Python tooling rather than schema templates. obsidian-llm-wiki-local is a pip-installable
10-KLOC package with SQLite state, atomic writes, SHA-256 hashing, and a human-in-the-loop rejection loop.
llm-wikidata's contribution is narrower — a 50-line entity-deduplication pattern built on ChromaDB — but it addresses a
problem that none of the schema-first repos mention: what happens when two articles generate entities that refer to the
same concept under different names.

---

## Patterns and modules worth lifting

Ranked by portability and phase-urgency.

**First priority — Phase 1 hardening (lift immediately):** obsidian-llm-wiki-local's `structured_output.py` 3-tier
JSON-extraction fallback. The three tiers are: native `format=json` parameter → regex extraction from the raw response →
retry with the parse error fed back to the model as an explicit correction prompt. The repo has already solved, in MIT-
licensed ~300 lines with tests, exactly the failure mode Linus's Phase 1 Ollama Worker will hit on the first day it asks
Qwen2.5 for a structured schema. The module has no exotic dependencies (`httpx`, `pydantic`, `click`, `rich`) and the
retry-with-error-feedback pattern is applicable beyond JSON — any structured output format a Worker might produce.
Vendor it under `src/linus/inference/structured.py` with attribution and a reference to `obsidian-llm-wiki-local` in the
file header.

**Second priority — Phase 2 KB schema (port the schema, not the repo):** llm-research-wiki's six-page-type schema —
source-note, concept, author, debate, synthesis, project — is the clearest worked example of typed page structure for a
research corpus. For Dan's biochemistry and genomics domain, the translation is direct: source-note stays (one per paper
or preprint), concept becomes pathway/protein/gene/method, author stays, debate becomes contested mechanism or
contradictory result, synthesis stays, project becomes an active research or writing thread. From atomic-knowledge, add
`procedure` as a seventh type — wet-lab protocols and SOPs are categorically different from definitions and deserve
first-class status with their own `Triggers`, `Steps`, and `Guardrails` sections. Combine these into the KnowledgeBase
v1 schema specification. Do not vendor either repo; read their `CLAUDE.md` and `schemas/` once and extract the page type
definitions.

**Third priority — Phase 2 KB tooling (near-zero-infrastructure read tool):** atomic-knowledge's `get_context` walker in
`runtime/service.py` is roughly 70 lines. It walks the entry files, enumerates each formal area, and emits per-file
`search_anchors` and `key_entities` hint payloads — a structured "what to read first" answer that requires no vector
store. This is the right starting shape for Linus's first KB read tool, to be run before investing in Qdrant integration
for the same retrieval path. It also encodes the three-tier routing order that llm-research-wiki independently
validates. Port it as `src/linus/kb/get_context.py`, keeping the embedding-free constraint for Phase 2 and adding a
Qdrant fallback only in Phase 3.

**Fourth priority — Phase 3 lint (design pattern, not code):** llm-research-wiki's LINT workflow — audit for duplicates,
stale pages, contradictions, orphans, overgrown pages, weak content, thin source support; present a prioritized list;
never auto-fix without confirmation — is the cleanest specification in the group for a `linus kb lint` command. No other
G3 repo has anything comparable. The "never auto-fix" default is right for a research corpus where many fixes require
human judgment, but for mechanical operations (DOI canonicalization, author-name normalization, arXiv-vs-published
dedup) a `--apply` flag behind a confirmation prompt extends the design sensibly. Note that hyalo (Group 5,
Integrate-recommended) is the planned lint substrate; G3's LINT pattern should inform the lint command's UX and check
list, while hyalo provides the underlying lint engine. Do not implement this in Phase 2; add it to the Phase 3 spec.

**Fifth priority — Phase 3 link-graph (near-zero-infrastructure graph queries):** agentic-wiki-builder's Linker step — a
DuckDB query using the community `markdown` extension to extract inter-file links from `wiki/*.md` into an edge table,
then NetworkX for connected-component analysis — provides link-graph queries over a markdown corpus with no graph
database. The DuckDB markdown extension's `read_markdown_sections` function parses wikilinks directly from files on
disk. This is small enough to port in an afternoon and worth a smoke test against a 50-paper sample of `context/papers/`
before committing to a heavier graph store. It sits naturally alongside the KB read tool and can be the Phase 2 graph
layer before Memgraph or DuckPGQ is needed in Phase 3.

**Sixth priority — Phase 2 Skills (installable today):** AgenticResearchWiki ships two ready-to-install Claude Code
Skills: `import-notes/SKILL.md` (113 lines — classify and file existing notes into the correct wiki section) and
`project-doc-update/SKILL.md` (64 lines — auto-applied after any agent touch on docs, lands content in the right
directory with backlinks updated). These are installable via `cp -r skills/* ~/.claude/skills/` and would help Dan
triage the existing `context/notes/` and `context/threads/` backlog without writing any custom tooling. Worth installing
as a Phase 1 quality-of-life experiment. Separately, obsidian-llm-wiki-local's **reject-and-explain loop** is a second
lift from this priority tier: when the user runs `olw reject FILE --feedback "..."`, the rejection text is stored in
SQLite and injected into the next compile prompt under the literal header "PREVIOUS REJECTIONS — address these issues in
this version:". After five rejections without approval the concept auto-blocks until manually unblocked. This is a
complete persistent human-in-the-loop critique loop built on no DPO and no training — worth studying as a Phase 7
prototype for any Linus Skill where Worker output needs iterative human critique rather than one-shot acceptance.

**Seventh priority — Phase 2/3 entity deduplication (50-line pattern, port on demand):** llm-wikidata's
conservative/granular entity-resolution loop in `src/pipeline.py` — vector-search the existing entity set via ChromaDB,
hand the top-k candidates to the LLM, prompt it to pick "match an existing entity" or "create new" — is a real solution
to the KB duplicate-entity problem. The L2 threshold (1.2 against `all-MiniLM-L6-v2`) will need retuning for biomedical
English text; the prompt structure is portable. Port as `src/linus/kb/entity_resolver.py` when Phase 2 KB ingest starts
producing duplicate nodes. Not urgent until the first ingest reveals the actual collision rate.

**Architecture reference only — beever-atlas:** The `gather → compile → cache` wiki-builder pattern with per-resource
async locks, the ADK `SequentialAgent + ParallelAgent` ingestion pipeline shape (stage 1 preprocess → stage 2 fan-out
fact + entity extraction → stage 3 fan-out embed + contradiction validation → stage 4 persist), and the dual
semantic+graph memory with a smart query router are all worth keeping in mind as Phase 3 KB v2 design targets. The
`BaseAdapter` + `NormalizedMessage` abstraction that separates "where bytes come from" from "what the pipeline does with
them" is also a reusable template if Linus eventually wants a uniform API in front of multiple source types (papers,
notes, threads, clips). None of the connector or datastore code translates to Dan's single-user local setup; the
patterns do. (DEC-0015 adopted dual RDF + property graph rather than Weaviate + Neo4j; DEC-0045 adopted fastmcp as the
MCP framework.)

---

## Cross-references

G3's workflow patterns only become load-bearing when G2's runtime layer exists beneath them. The G2 synthesis covers the
inference engines; G3 provides the ingest, schema, and lint discipline that runs above those engines. The two clusters
together constitute the full Karpathy LLM Wiki pattern as implemented across the community.

The llm-wiki-synthesis (the Karpathy gist + Rohit v2 + community practitioner thread) is the primary reference for the
claim-typing, content-hashing, and write-back-rule requirements that G3's schema work should satisfy. Where G3 repos and
the llm-wiki-synthesis agree — on immutable raw layers, three-tier routing, and the write-back loop — the design is
confirmed from independent angles.

The memory-synthesis connects to G3 through Layer D (semantic/knowledge memory): the same scratchpad-as-durable-artifact
and reliable-history-access requirements that Garrison's framework places on the episodic store apply equally to the
compiled wiki layer. G3's schema discipline is what makes Layer D trustworthy; without claim typing and content hashing,
the KB fails the integrity requirement.

The security-synthesis reinforces claim typing from an angle none of the G3 repos mention: when KB content reaches a
Worker as context, ungrounded synthesis claims are a prompt-injection surface as well as an epistemic problem. The
trust-tier tagging the security synthesis recommends for KB-sourced context (`source: knowledge_base`, low trust,
sanitized) maps directly onto the `[!source]` / `[!analysis]` / `[!unverified]` / `[!gap]` claim types that
llm-wiki-synthesis recommends and llm-research-wiki's schema partially implements.

G8 (sci-agents cluster) surfaces paper-qa as the first paper-corpus tool to earn an Integrate verdict (DEC-0044), which
reframes Phase 2 KB substrate from "build" to "adopt + extend." paper-qa's tantivy full-text + vector retrieval pipeline
is the planned Phase 2c embedding layer that G3's cascade → embedding fallback design points toward. The
cluster→synthesis→`related:` cascade from llm-research-wiki is the embedding-free Phase 2 bridge; paper-qa takes over
for unknown terms in Phase 3 when the corpus exceeds 200 nodes and the index-only routing in the cascade becomes
insufficient.

---

## Phase-tagged implications

**Phase 1 — Worker hardening:** Lift `structured_output.py` from obsidian-llm-wiki-local into
`src/linus/inference/structured.py`. Install the two AgenticResearchWiki Claude Code Skills (`import-notes`,
`project-doc-update`) as a quality-of-life experiment on `context/notes/`. Run the DuckDB+NetworkX linker pattern as a
smoke test against a 50-paper sample — this is one afternoon of work and determines whether the approach is worth
formalizing as a Phase 2 KB tool.

**Phase 2 — KB schema and read tooling:** Design the KnowledgeBase v1 page schema using the seven-type composite from
llm-research-wiki and atomic-knowledge (source-note, concept, author, debate, synthesis, project, procedure), with
mandatory YAML frontmatter per type and the `search_anchors` / `key_entities` hint fields from atomic-knowledge as
optional but encouraged. Implement the `get_context` walker from atomic-knowledge as the first KB read tool. Build the
ingest pipeline's quality gate per DEC-0019: a quality surface, not a hard reject lane — YAML-policy scoring with the
per-paper quality scorecard surfaced to Maestro at retrieval time, no `FILTERED.md` quarantine. Implement the write-back
rule as a mandatory exit step in every Worker KB invocation: every task returns a deliverable plus KB page update
proposals.

**Phase 3 — Hybrid retrieval and lint:** Implement `linus kb lint` using llm-research-wiki's LINT workflow specification
as the check list and hyalo (G5, Integrate-recommended) as the underlying lint engine. Add `--apply` for mechanical
fixes. Extend the `get_context` walker with paper-qa's retrieval pipeline (DEC-0044) as the hybrid-search fallback for
queries outside the cascade. Add the entity-resolution loop from llm-wikidata when KB ingestion starts producing
duplicate nodes. Promote the DuckDB+NetworkX link graph to a formal KB tool if the Phase 1 smoke test validates it. The
write-back rule implementation for parallel Workers is tracked as R2-22 in `top-questions.md`; DEC-0022 resolved the
policy (branch-per-Worker coordination), but the concrete implementation pattern (lease, optimistic-merge, or
branch-per-Worker flush) is the open Phase 2/3 engineering question.

---

## Open questions for Dan

The six-page-type schema from llm-research-wiki is the clearest starting point for KB v1, but the `procedure` type from
atomic-knowledge may or may not belong in Phase 2 alongside the others — does Dan's paper corpus already have enough
protocol-centric content (wet-lab methods sections, bioinformatics pipeline descriptions) to justify a `procedure` type
from day one, or does that wait until the SOP-generation use case in Phase 2 actually produces procedure pages?

The LINT workflow's "never auto-fix" default is right for humanistic scholarship; for a biochemistry corpus, DOI
canonicalization and arXiv-vs-published deduplication are mechanical operations that should not require a human decision
for every instance. What is the right autonomy level for the `linus kb lint --apply` mode — confirmation per fix,
confirmation per fix-type, or auto-apply with a dry-run diff shown afterward?

The `structured_output.py` lift from obsidian-llm-wiki-local is the clearest Phase 1 action item and the one with the
most immediate payoff. The question is whether to vendor it directly (MIT-licensed, ~300 lines, attribution in the file
header) or rewrite from scratch with the same three-tier logic. Vendoring is faster and keeps the test coverage;
rewriting removes the Obsidian-vault framing from the variable names and removes any future surprise from upstream
changes. Which does Dan prefer as the default practice for short MIT-licensed utilities? (Tracked as Tier 3 in
`top-questions.md`.)

---

_Cross-references: llm-wiki-synthesis.md (canonical practitioner patterns); memory-synthesis.md (Layer D KB integrity
requirements); security-synthesis.md (trust-tier tagging for KB content); g8-sci-agents.md (paper-qa as Phase 2c KB
retrieval engine, DEC-0044). Update this document when the Phase 2 KB schema spec lands or when Phase 3 lint design
begins._

---

## References

### Repo-notes

- [`agentic-wiki-builder`](../../repo-notes/agentic-wiki-builder.md) — Git-branch-per-session provenance plus a
  DuckDB+NetworkX Linker that extracts inter-file wikilinks into an edge table for connected-component analysis.
- [`AgenticResearchWiki`](../../repo-notes/AgenticResearchWiki.md) — Two ready-to-install Claude Code Skills
  (`import-notes`, `project-doc-update`) plus a `CLAUDE.md` navigation discipline.
- [`atomic-knowledge`](../../repo-notes/atomic-knowledge.md) — Seven-page-type schema with the `procedure` type; the
  `get_context` walker (~70 lines) provides near-zero-infrastructure KB read tooling.
- [`beever-atlas`](../../repo-notes/beever-atlas.md) — Production-scale outlier: `gather → compile → cache` pipeline,
  ADK `SequentialAgent + ParallelAgent` shape, dual semantic+graph memory.
- [`hyalo`](../../repo-notes/hyalo.md) — G5 Integrate-recommended lint engine; planned substrate beneath the
  `linus kb lint` command.
- [`llm-research-wiki`](../../repo-notes/llm-research-wiki.md) — Six-page-type schema (source-note, concept, author,
  debate, synthesis, project) with three formalized workflows (INGEST, QUERY, LINT).
- [`llm-wikidata`](../../repo-notes/llm-wikidata.md) — Entity-deduplication pattern (~50 lines, ChromaDB-backed
  conservative/granular resolver) addressing the concept-drift problem.
- [`obsidian-llm-wiki-local`](../../repo-notes/obsidian-llm-wiki-local.md) — Pip-installable 10-KLOC package with SQLite
  state, atomic writes, SHA-256 hashing, and the `structured_output.py` 3-tier JSON fallback worth lifting immediately.
- [`paper-qa`](../../repo-notes/paper-qa.md) — G8 Integrate verdict (DEC-0044) reframing Phase 2 KB substrate from
  "build" to "adopt + extend"; tantivy full-text + vector retrieval pipeline.
