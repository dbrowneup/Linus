# prism (`payneio/prism`)

## 1. Purpose and scope

Prism is Paul Payne's "next-generation content management protocol" — a Python 3.12 CLI plus library
(`pip install -e .`, `prism init my-wiki`) that turns a directory of Markdown files into a structurally validated wiki
with auto-generated cross-references and a roadmap toward graph "projections" and AI-assisted summarization. It is
positioned against Notion and Obsidian as a protocol-first, git-friendly, editor-agnostic substrate intended
specifically as backend context for an LLM assistant. Importantly for Linus, Prism is early-stage: the spec is ambitious
(Sections 6 "Projections" and "AI-Powered Summarization" in `core-specification.v1.md`), but the codebase implements
only the wiki layer so far — every test file under `tests/projection/`, `tests/summarize/`, and `tests/indices/` is zero
bytes. So Prism is best read as a design document with a working wiki engine attached, not as a finished
projection/summarization tool.

## 2. Architecture summary

A small async Python package (~900 LOC under `src/prism/`) built on `asyncclick`, `aiofiles`, and `aiopath`. The core
model is three node types — Page, Folder, Media — stored as Markdown files in a hierarchical directory tree with a
`.prism/` metadata sidecar holding `backlinks.txt`, `tags.txt`, and a `.search/` index directory. Filesystem access goes
through a `FileSystem` interface (`Disk` and `Memory` implementations) so operations are testable without touching disk.
Dynamic content is the defining mechanic: HTML-comment markers like `<!-- prism:generate:toc -->` …
`<!-- /prism:generate:toc -->` are filled in by generator classes (`generators/toc.py`, `breadcrumbs.py`, `pages.py`,
`siblings.py`) during a `prism refresh` pass, which validates structure, runs generators, and reindexes. YAML front
matter and a `<!-- prism:metadata --> ... -->` trailer carry per-page metadata. The `Prism` class (`src/prism/prism.py`)
is the entry point, with `create_page`, `get_folder`, `refresh_page`, and `refresh_folder` as the public surface.
"Projection" in the spec means three things — Sub-Prism (extract a subtree), Flatten (concat pages into one document),
and Summary (AI-walked summarization of a node's neighborhood) — none of which are implemented yet. The repo carries six
versioned spec docs (core v0/v1, api, indexing, library, sync) totaling ~1400 lines, indicating the design work has run
well ahead of implementation.

## 3. What's reusable in Linus

Almost nothing as code today, but the **protocol shape** is genuinely interesting for Linus's Phase 2 KB layer. The idea
of treating a Markdown corpus as a graph with a `.prism/` sidecar index, generators that keep TOCs and backlinks in
sync, and a refresh pass that revalidates structure on demand, lines up directly with how Linus's `context/` folder
(papers, threads, notes) could be made navigable for both Dan and worker agents without standing up a heavyweight CMS.
The "projection" concept — extract a subtree or flatten a neighborhood into a single document — is exactly what a Worker
needs when given a task: a materialized, scoped context window built from the KB graph rather than a raw file dump. If
Linus ends up needing a Markdown-side index alongside the KnowledgeBase Qdrant vector store, Prism's spec is a credible
starting template.

## 4. What's inspiration only

Compared to its Group 5 siblings, Prism is structurally different and that distinction matters. `keppi` and `hyalo` are
vault-traversal CLIs aimed at Obsidian-compatible Markdown; `infranodus` and `py3plex` are real network/knowledge-graph
engines with measures, layouts, and analytics; Prism is a wiki-as-graph CMS protocol whose graph operations are still on
paper. Calling it a Group 5 "knowledge graph" tool is generous — it's closer to a Group 2 LLM-Wiki engine (Outline,
BookStack, Wiki.js) re-imagined for agentic context-assembly. For Linus, this means Prism does not compete with
`infranodus` for graph analysis or with `py3plex` for multilayer projection; it competes with hand-rolling a Markdown
organizer on top of `context/`. Treat the spec docs as design inspiration for how a future Linus KB-write surface could
shape itself.

## 5. What's incompatible or out of scope

The implementation is too thin to depend on. Empty test files for projection, summarization, and indices mean those
features are vapor; the search index directory is created but no search backend exists; sync (per
`sync-specification.v0.md`) is unimplemented. The package metadata says `pip install prism` is "Doesn't work, yet." — so
adoption means vendoring or pinning a commit and accepting maintenance burden for a one-developer hobby project at
v0.1.0. Prism is also Markdown-only and assumes content authored as human-readable pages; Linus's KnowledgeBase deals
with PDFs, paper metadata, and structured records that do not naturally live in a wiki page format. Finally, Prism's
async-everywhere choice (`asyncclick`, `aiopath`) is fine in isolation but adds friction if Linus wants to call it as a
sync library from non-async code paths.

## 6. Recommendation: **Ignore (with the spec saved as design reference)**

Prism does not earn integration into Linus today and probably not in any near phase. The wiki engine is small enough to
reimplement if needed, the projection/summarization features Dan would actually want are unwritten, and Linus's KB story
is better served by KnowledgeBase + vector search + (eventually) a graph layer than by a Markdown CMS protocol. The
valuable artifact here is the spec set — pull a couple of ideas (subtree projection, flatten-for-context,
generator-based index maintenance) into the Phase 2 KB design notes and move on. Revisit only if Payne ships the
projection and summarize modules and a real search backend.

## 7. Questions for Dan

- **Markdown CMS for `context/`.** The folders `context/papers/`, `context/threads/`, `context/notes/` are exactly the
  shape a Prism manages. Is there appetite for a lightweight "give me a TOC and backlink map across `context/notes/`"
  tool, or is your existing editor workflow already covering that?
- **Projection-as-context-assembly.** Prism's "Flatten a subtree into one Markdown doc" is a primitive that Worker
  agents could call to build their own task context. Worth specifying as a Linus Phase 3 tool independent of Prism — yes
  or no?
- **Spec-first vs. ship-first.** Prism is a clear case of design running ahead of implementation (1400 lines of spec,
  900 lines of code, zero tests for the headline features). Useful cautionary tale to cite in DECISIONS.md when we set
  Linus's spec/ship ratio?
- **Differentiation with confidence.** I called Prism "more CMS than KG" relative to the rest of Group 5. Does that
  match your read, or do you see a graph-analysis angle here I'm missing?
- **One-dev dependency risk, again.** Same shape as the pmetal question: would you ever vendor a v0.1 one-maintainer
  protocol like Prism, or is the bar "must be at v1 with real users" before any Linus integration?
