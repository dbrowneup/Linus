# agentic-wiki-builder (`anomalyco/agentic-wiki-builder`)

## 1. Purpose and scope

A thin Python wrapper around the OpenCode CLI agent that ingests one source file at a time and grows a flat directory of
interlinked markdown files (`/wiki/*.md`) — a personal wiki — instead of a vector store or triple-based knowledge graph.
The author's stated motivation is dissatisfaction with both pure-embedding RAG and the contrived
subject/predicate/object shape of mainstream KG tools: nuanced, conditional, temporal relationships are exactly what
LLMs handle well, so why force them into triples? The novel design choice is **provenance-via-git**: every ingest run
gets its own UUID-named branch, the agents write on that branch, and `git blame wiki/foo.md` answers "what raw input
caused this paragraph?" without any inline citations or anchor tracking. This makes the project a Karpathy "LLM Wiki"
sibling to AgenticResearchWiki, llm-research-wiki, llm-wikidata, atomic-knowledge, beever-atlas, and
obsidian-llm-wiki-local — but uniquely centered on the workflow scaffolding rather than vault tooling, ontology, or a
research methodology.

## 2. Architecture summary

Roughly 140 lines of glue across `main.py` and `src/`. `main.py` orchestrates a session: mint a UUID, copy the input
file to `sessions/{uuid}/raw/`, create a `session-{uuid}` git branch, and call three agents in sequence via
`subprocess.run(["opencode", "run", prompt])`. The Writer (`src/agents/writer.py`) is told to read the raw, write
markdown into the shared flat `/wiki/`, drop helper scripts into `/helpers/` (with `uv` for env management), and log
what it did to `sessions/{uuid}/docs/`. The Editor (`src/agents/editor.py`) reviews. The Linker (`src/agents/linker.py`)
is the most code-heavy step: a DuckDB query (community `markdown` extension) over `wiki/*.md` extracts inter-file
`[…](./foo.md)` links into an edge table, NetworkX finds connected components, and for each pair of disconnected
clusters one Linker invocation is asked whether a real link belongs there. Finally, `src/version_control.py` stages
`wiki/` and `helpers/`, commits with the agent-written `summary.txt`, merges back to `main` with `--no-ff`, and deletes
the branch. There is no inference engine, no embedding store, no retrieval layer — all model work is OpenCode's. Two
source files, `wiki_agent.py` (~370 lines) and `commit_processor.py`, look like earlier drafts not wired into `main.py`.

## 3. What's reusable in Linus

The branch-per-session pattern lines up almost exactly with Linus's `agent/<task-id>/<slug>` convention in BRANCHING.md.
agentic-wiki-builder is in fact a working precedent for treating a Worker-driven knowledge-edit run as a first-class git
branch with merge-on-success / discard-on-failure semantics — this is a useful demonstration that the Maestro/Worker
protocol can lean on git as the audit log rather than building a separate one. The three-agent loop (Writer → Editor →
Linker) is a small, concrete shape for the Phase 3 parallel-agents work: bounded roles, each with a narrowly scoped
prompt and shared filesystem state. The Linker's DuckDB-+-NetworkX-over-`read_markdown_sections` trick is genuinely
clever and directly portable to KnowledgeBase Phase 2 — it gives a near-zero-infrastructure way to expose graph
structure over a markdown corpus without standing up Neo4j or Memgraph. Compared to the sibling
`obsidian-llm-wiki-local` (which leans on the Obsidian vault format) and `llm-wikidata` (which targets the Wikidata
schema), agentic-wiki-builder's filesystem-only model is the lightest and the most compatible with Linus's existing
repo-of-markdown habits.

## 4. What's inspiration only

The "use git blame as the citation system" idea is intellectually appealing but degrades as soon as agents rewrite or
reflow text — `git blame` follows lines, not provenance. For Linus's Phase 2 KB, where Dan wants to trace a claim back
to a specific paper, this approach is weaker than a structured citation map. The opinion that "LLMs hallucinate
citations, so don't ask them to" is real but the right answer is probably tool-enforced citations, not no citations.
Compared to siblings like `AgenticResearchWiki` (presumably more research-loop oriented) and `atomic-knowledge`
(presumably ontology-flavored), this repo deliberately punts on schema and lets the model decide what an article is.
That freedom is a design statement, not a feature Linus should copy wholesale.

## 5. What's incompatible or out of scope

The hard dependency on the OpenCode CLI binary means this is not directly a code library — to reuse the orchestration
you'd shell out to `opencode run`, which sits outside Linus's planned stack (Ollama / pmetal / mlx-lm). There is no
abstraction layer around the agent invocation; `call_agent` is six lines of `subprocess.run`. The single-input-file
ingest model also doesn't match Linus's KnowledgeBase scale (thousands of papers) — running this loop once per paper
serially through OpenCode would be impractically slow on M1 Max. The Linker's all-pairs-of-components prompt explosion
is O(n^2) in cluster count and would also need bounding before scaling.

## 6. Recommendation: **Study**

Lift two ideas, don't vendor the code. First, formalize "Worker session = git branch, merge-on-success" in the
Maestro/Worker protocol doc — this repo is the existence proof. Second, use the DuckDB `read_markdown_sections` +
NetworkX pattern as the prototype for KnowledgeBase Phase 2 link-graph queries; it's small enough to port in an
afternoon and worth a smoke test against a sample of `context/papers/`. Beyond those, the codebase is too thin and too
tightly bound to OpenCode to be a starting skeleton.

## 7. Questions for Dan

- **Provenance model.** Is `git blame` provenance enough for KnowledgeBase, or does Phase 2 need explicit
  paper-id-to-claim back-references because PDFs get rewritten and reflowed across ingest runs?
- **Branch-per-session as protocol.** The README's session pattern is essentially `agent/<uuid>/wiki-update`. Want to
  enshrine "every Worker-driven KB edit happens on its own branch and merges with `--no-ff`" in
  `docs/maestro-worker-protocol.md` as a hard rule, or keep it as one option among several?
- **DuckDB+NetworkX as KB graph layer.** Is this the kind of prototype you want for Phase 2 link analysis, or are you
  already committed to a heavier graph store (DuckPGQ, Memgraph, Neo4j)?
- **OpenCode in the harness picture.** Cline, claw-code-local, openclaw, Claude Code — and now, in principle, OpenCode.
  Is OpenCode worth its own evaluation slot, or has the harness shortlist already closed?
- **Differentiator confidence.** I'm calling branch-per-session and the DuckDB linker the differentiators vs the other
  six LLM-Wiki siblings, but I haven't read those repos yet. Worth flagging whether any sibling already does the same so
  the comparison holds up.
