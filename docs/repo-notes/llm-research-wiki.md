# llm-research-wiki (`MetamusicX/llm-research-wiki`)

## 1. Purpose and scope

A personal academic-research knowledge base built as plain markdown and operated entirely through Claude Code. It is
Paulo de Assis's adaptation of Karpathy's April 2026 "LLM Wiki" pattern to the workflow of a humanities scholar: sources
go in `raw/` and are never modified; an agent reads them, extracts claims and quotes, and writes or updates interlinked
pages under `wiki/`. The artifact of interest is not a runtime — there is no server, no database, no embeddings — but
the **schema in `CLAUDE.md`** that turns Claude Code into a domain-specialist research librarian. The README claims a
first ingest produced 38 wiki pages in a single pass, which is the kind of throughput Linus's Phase 2 KnowledgeBase work
needs to match for Dan's paper backlog.

## 2. Content overview

The repo is a folder skeleton plus three governing files. `CLAUDE.md` (475 lines) defines the agent's identity
("dedicated research intelligence system, not a general assistant"), folder conventions for `raw/` and `wiki/`, six page
templates with mandatory YAML frontmatter, three workflows, cross-referencing rules, and a domain-context block listing
Paulo's key thinkers and concepts. The six page types are **source-note, concept, author, debate, synthesis, project**
(with **method** and **theme** as lighter siblings sharing the base frontmatter). The three workflows are **INGEST**
(read source → discuss takeaways before writing → create source-note → scan whole wiki for impact, updating every
concept/ author/debate page touched, stub anything missing → log everything), **QUERY** (read `index.md` → identify
cluster → read synthesis if it exists → follow `related:` frontmatter field, never re-read raw), and **LINT** (audit for
duplicates, stale pages, contradictions, orphans, overgrown pages, weak content, thin source support — present
prioritized list, never auto-fix). The most distinctive structural move is the **three-layer navigation cascade** for
keeping query cost roughly constant as the wiki grows past 100 pages: concept clusters in `index.md` → synthesis pages
per cluster → `related:` field of 3–5 nearest neighbors on every concept and author page. `wiki/`, `raw/`, `outputs/`,
and `conversations/` are empty skeletons with subfolders pre-created; `index.md` ships as a template with placeholder
clusters; `log.md` is empty. The wiki is meant to be cloned and seeded from the user's own first ingest.

## 3. What's reusable in Linus

The Phase 2 KnowledgeBase v1 is the integration target. The six-template schema maps almost directly onto what Dan needs
for the paper corpus once the page-types are translated from humanities to biochemistry: **source-note** stays (one per
paper/preprint), **concept** becomes pathway/protein/gene/disease, **author** stays (PI / first-author / collaborator
graph), **debate** becomes contested mechanism or contradictory result, **synthesis** stays (the "keep cost constant
past 100 pages" move generalizes cleanly), **project** becomes Dan's active research/writing threads. The
cluster→synthesis→`related:` cascade is the most valuable single idea — it is a concrete, embedding-free solution to the
"100+ docs and the index becomes the bottleneck" problem that any markdown-first KB hits, and it costs nothing to adopt.
The INGEST workflow's "discuss takeaways with the user _before_ writing anything" beat is a quality gate worth importing
into Linus's KB ingest tool. The LINT workflow has no parallel in any other repo in this group and gives Linus a
ready-made KB-health surface for Phase 3.

Compared to **AgenticResearchWiki** (the closest-named sibling), this is a fundamentally different workflow:
AgenticResearchWiki targets AI/ML _training-ops_ projects with `Data/Training/Eval` overviews and emphasizes
**write-back after job completion** as the central feature; llm-research-wiki targets _reading and synthesizing
literature_ with no execution loop at all. AgenticResearchWiki's Overview-rooted entry pattern is closer to a project
README; llm-research-wiki's six fixed page-types with mandatory frontmatter is closer to a typed graph.

## 4. What's inspiration only

Compared to **atomic-knowledge** (the other Karpathy-direct sibling in this group), llm-research-wiki is the more
opinionated and less portable design. atomic-knowledge ships a platform-neutral protocol with a runtime `get_context`
path and a formalized `procedures/` layer for workflows; llm-research-wiki has no runtime and no procedure type — the
workflows live as instructions inside `CLAUDE.md` and are executed by whatever agent reads it. For Linus, the right move
is to take the **schema** from llm-research-wiki and the **runtime/protocol thinking** from atomic-knowledge, not to
vendor either wholesale. The domain-context block at the bottom of `CLAUDE.md` (Paulo's thinkers and concepts) is also
inspiration only — Dan needs a parallel block for biochemistry/genomics, and the form of that block (named thinkers,
named concepts, named debates) is the lift.

## 5. What's incompatible or out of scope

The schema assumes a single human user driving a single agent at a time — there is no concurrency model, no merge
strategy for parallel ingests, and no notion of audit beyond `log.md` as an append-only text file. Linus Phase 3 wants
parallel agent fan-out, which means either serializing KB writes through a single owner or layering a real concurrency
story on top. The wiki-link convention (relative markdown paths like `[Transduction](../concepts/transduction.md)`) is
fine for human reading inside an editor but is a fragile substrate for programmatic queries; Linus will likely want the
same files plus an indexed view (SQLite, Qdrant, or both) and treat markdown as the source of truth with the index as a
derived cache. The "do not auto-fix" rule of LINT is the right default for a humanities scholar with strong opinions
about every page; for a biochemistry corpus where most fixes are mechanical (dedup of an arXiv vs. published version,
normalizing author names), Linus probably wants a `--apply` mode behind a confirmation prompt.

## 6. Recommendation: **Study (port the schema and cascade into Phase 2 KnowledgeBase)**

Do not vendor the repo. Read `CLAUDE.md` once, lift the six-page-type schema and the cluster→synthesis→`related:`
cascade into the KnowledgeBase v1 design doc, and translate the page-type vocabulary from humanities to genomics/
biochemistry. The LINT workflow is worth porting roughly verbatim as a `linus kb lint` command in Phase 3. The INGEST
"discuss before writing" beat goes into the Linus KB ingest tool's UX. Past those three lifts, llm-research-wiki has
done its job for Linus.

## 7. Questions for Dan

- **Page-type translation.** The six humanities page-types map to biochemistry roughly as paper / pathway-or-protein /
  author / contested-mechanism / synthesis / project. Is that the right mapping, or do you want a separate page-type for
  **method/protocol** (which Paulo treats as a lighter sibling of concept, but in wet-lab work is arguably the central
  artifact)?
- **Cascade vs. embeddings.** The cluster→synthesis→`related:` cascade is an embedding-free way to keep query cost
  bounded. KnowledgeBase already has a Qdrant vector store. Run both in parallel with the cascade as the navigation
  surface and embeddings as fallback for unknown terms, or pick one?
- **LINT autonomy.** Paulo's schema says "never auto-fix." For a 1000+ paper corpus, mechanical fixes (arXiv-vs-
  published dedup, author-name normalization, DOI canonicalization) are the bulk of the work. Want a `--apply` mode
  behind a confirmation, or strictly report-only like the original?
- **Domain-context block.** Paulo's `CLAUDE.md` ends with a named list of his thinkers, concepts, and debates that the
  agent uses for cross-referencing. Do you want to author the equivalent for your research areas now, or have Linus
  extract it from the first 20–30 ingested papers and propose it back?
- **Differentiator confidence.** I can distinguish llm-research-wiki from AgenticResearchWiki and atomic-knowledge on
  workflow framing (reading vs. training-ops vs. platform-neutral protocol). Is that distinction the one you'd draw, or
  do you read the three siblings differently after seeing them in practice?
