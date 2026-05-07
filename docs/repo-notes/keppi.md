# keppi (`jgoldfed/keppi`)

## 1. Purpose and scope

Keppi — "Knowledge Engine for Precise Pattern Intelligence" — is a Python 3.10+ CLI that turns an Obsidian-style
markdown vault into a weighted directed graph and exposes a dozen graph-traversal commands on top of it. The product
framing is explicit: similarity search finds textually related content, but answering "if I take this job in another
city, which of my notes does that touch?" is a structural query that requires walking edges, not embedding cosines.
Keppi parses every wikilink, embed, `related_to:` frontmatter field, tag overlap, and folder co-residence into a
NetworkX graph stored in SQLite, then runs BFS-with-relevance-decay, Louvain community detection, betweenness/degree
centrality, and (optionally) `sqlite-vec` KNN over Ollama or OpenAI embeddings. MIT-licensed, on PyPI as `keppi`, with a
19-tool MCP server and two shipped agent skills (`wiki-search`, `vault-research`). For Linus this is a Phase 2 KB-graph
reference and a Phase 3 hybrid-retrieval reference — a worked example of "graph traversal as a first-class retrieval
primitive sitting between the wiki layer and the LLM."

## 2. Architecture summary

A flat Python package: `keppi/parser/` (markdown + frontmatter + config), `keppi/graph/` (`builder.py` constructs the
NetworkX `DiGraph` and writes it to SQLite via `storage.py`; `incremental.py` updates on file watch), `keppi/analysis/`
(the seven analysis primitives — `blast_radius`, `centrality`, `communities`, `context_pack`, `drift`, `gaps`,
`suggestions`), `keppi/search/` (`keyword.py`, `semantic.py`, and `providers.py` for Ollama/OpenAI embedding clients),
`keppi/mcp/server.py` (FastMCP server exposing 19 tools), and `keppi/cli/` (Typer + Rich). The graph model uses fixed
edge weights — `wikilink=1.0`, `embed=1.5`, `related_to=2.0`, `tag_overlap=0–0.5×Jaccard`, `folder_proximity=0.3` — so
"relevance" is just the multiplicative product of edge weights along a BFS path; results below a `threshold` (default
0.3) get pruned. `compute_blast_radius` is the canonical traversal: a deque-based BFS with
`direction in {"out","in","both"}` (so backlink-only expansion is a flag, not a separate algorithm), best-relevance-wins
on revisit, and `__broken__` sentinel-prefixed nodes for dangling wikilinks. `build_context_pack` chains
`keyword_search → blast_radius → degree-centrality re-rank → greedy fill to a token budget`, which is the closest thing
in this repo collection to a complete "graph-aware retrieval" pipeline. Embeddings are chunked at 1600 chars with 200
overlap, stored alongside the graph in the same SQLite file via `sqlite-vec` — no separate vector store, no service to
run at query time. The MCP server's `instructions` string explicitly tells the LLM client to call
`get_embed_status() → semantic_search(wiki_only=True) → fall back to keyword_search`, which is a small but real piece of
prompt engineering for agent-side retrieval planning.

## 3. What's reusable in Linus

The graph model and the traversal primitives port almost directly. Linus's KnowledgeBase already produces a node/edge
layer; what it lacks is the query layer Keppi calls "blast radius" — bounded BFS with multiplicative relevance decay and
typed-edge weights — and the `context_pack` greedy-fill algorithm that turns "topic + token budget" into a concrete
reading set. Both are ~100-line NetworkX functions with no Apple-Silicon dependencies; they belong in the Phase 3 hybrid
retrieval layer alongside vector KNN, with similarity-search providing seed nodes and graph traversal providing
neighborhood expansion. The MCP server is a useful template for how the Phase 2a tool registry might expose KB tools —
note in particular the model-instructions string that tells the agent the preferred call order. The `sqlite-vec` +
NetworkX + SQLite single-file pattern is also worth borrowing for any KB-on-a-laptop persistence layer where running
Qdrant feels like overkill.

Compared to the named siblings in this group: `hyalo` is the other Obsidian-vault CLI in Group 5, but its emphasis (per
its own framing) is daily-note synthesis and LLM-mediated authoring; Keppi explicitly disclaims that role ("Keppi
doesn't compile external sources into a wiki") and stays inside graph traversal. Compared to `agentic-wiki-builder` in
Group 3 (DuckDB + NetworkX link graph), Keppi treats the wiki as input rather than output — agentic-wiki-builder
constructs the wiki, Keppi assumes it exists and makes it queryable. This split is useful for Linus:
agentic-wiki-builder is a candidate for the Phase 3 wiki-construction loop, Keppi is a candidate for the Phase 3
wiki-traversal loop, and they compose rather than compete.

## 4. What's inspiration only

The "blast radius" framing and the specific edge-weight scheme (`related_to` 2× `wikilink` 2× `tag_overlap`) reflect one
person's intuitions about their own vault. Linus's KB is paper-corpus-shaped, not Zettelkasten-shaped, so the weights
will need re-tuning — citation edges, co-author edges, and shared-DOI edges have no analog in Keppi. Drift detection
("stale notes connected to recently-updated ones"), the `gaps` Louvain-community-pair heuristic, and the frontmatter
`related_to` field are vault-author-workflow features rather than retrieval features; useful as ideas, not code to lift.
The two shipped MCP skills (`wiki-search`, `vault-research`) are specifically tuned to the author's own vault layout
(`3-Resources/wiki/`) and would need rewriting for any other corpus.

## 5. What's incompatible or out of scope

Nothing about Keppi is hostile to Apple Silicon — it's pure-Python NetworkX with optional Ollama embeddings — but it is
single-vault, single-process, and expects markdown files on disk. The SQLite-with-`sqlite-vec` storage is fine for
hundreds of thousands of edges but is not a graph database; queries beyond 2–3 hops on a dense graph degrade quickly,
which the author hints at by capping default depth at 2. Keppi is a tool, not a library — the public API is the CLI and
the MCP server, and the internal modules import each other freely (`context_pack` reaches into `blast_radius` and
`keyword_search` directly). Linus integrating Keppi as a library would mean tolerating that internal coupling or
extracting just the algorithm functions.

## 6. Recommendation: **Study**

Read `keppi/analysis/blast_radius.py`, `keppi/analysis/context_pack.py`, and `keppi/mcp/server.py` as primary references
when designing Linus's Phase 3 hybrid retrieval. Port the BFS-with-relevance-decay pattern and the greedy
token-budget-fill pattern as Linus-native functions over the KnowledgeBase graph; do not vendor the package. Re-evaluate
when Phase 3 starts whether the MCP-server-as-tool-surface pattern (with the embedded retrieval-strategy instructions
string) is the right shape for Linus's KB tools, or whether a native Linus tool registry is preferable.

## 7. Questions for Dan

- **KB graph schema parity.** Keppi's edge types are vault-author-shaped (`wikilink`, `embed`, `related_to`,
  `tag_overlap`, `folder_proximity`). The KnowledgeBase corpus is paper-shaped (`cites`, `cited_by`, `co_author`,
  `shared_topic`, `shared_doi`). Should we define the Phase 2 KB edge schema explicitly before borrowing Keppi's
  weighting scheme, or pick weights empirically once the graph is built?
- **Hybrid retrieval order.** Keppi's MCP server hard-codes `semantic_search → keyword_search → graph traversal`. For
  paper retrieval the natural order may invert (citation-graph expansion from a known paper, then semantic re-rank). Do
  we want a single canonical retrieval recipe in Phase 3, or pluggable strategies per task type?
