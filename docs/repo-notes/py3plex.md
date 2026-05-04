# py3plex (`SkBlaz/py3plex`)

## 1. Purpose and scope

py3plex is a mature, MIT-licensed Python library for **multilayer network analysis** — graphs in which nodes and edges
carry types and live in distinct layers, with intra-layer and inter-layer (coupling) edges. It originated with the 2019
Skrlj/Kralj/Lavrac papers (Applied Network Science; Complex Networks VII) and has since grown to ~211k LOC, 9.2k tests,
170+ examples, a 106-page handbook PDF, a `py3plex` CLI, and a `py3plex-mcp` Model Context Protocol server. The badge
set on the README — Tests, Examples, Tutorial, Code Quality, Benchmarks, Documentation, Formal Verification (CrossHair +
icontract + z3), Fuzzing — is unusually serious for an academic graph library and is what makes this repo worth real
attention rather than filing as "yet another NetworkX wrapper." For Linus this lands squarely in the Phase 2 KB graph
layer (DEC-0026/27, dual RDF + property graph) and in Phase 3 hybrid retrieval where embeddings + community structure +
centrality have to compose cleanly.

## 2. Architecture summary

The package is organized into ~40 sub-packages. The data-structure spine is `py3plex.core.multinet` — a 4754-line module
exposing a `multi_layer_network` container built on top of `networkx` graphs (one per layer, plus coupling edges and
optional supra-adjacency tensor projections via `scipy.sparse`). HINMINE decomposition lives next to it (`core/HINMINE/`
for heterogeneous information network mining), with parsers, converters, an immutable variant, lazy evaluation, schema
validation, and a temporal `temporal_multinet`. Above the data layer sits `py3plex.dsl/` — a SQL-like query DSL ("DSL
v2") with an explicit AST (`Query`, `SelectStmt`, `LayerExpr`, `ComputeItem`, `UQConfig`, `CounterfactualSpec`), a
`Q.nodes()/.edges()/.communities()` builder, a planner, executors (including a semiring executor), a fastpath, and a
provenance/explain layer. `py3plex.algorithms/` covers community detection (Louvain, Leiden, Infomap via SWIG, label
propagation, SBM, spectral multilayer, AutoCommunity multi-objective Pareto selection with uncertainty quantification),
multilayer centrality, Ollivier-Ricci curvature, network classification, robustness testing, and SIR multiplex dynamics.
`py3plex.embeddings/` ships metapath2vec and NetMF; `py3plex.uncertainty/` and `py3plex.counterfactual/` expose
confidence-interval and intervention machinery that the DSL surfaces as `.uq(...)` and `.where(intervention=...)`
clauses. `py3plex.compat/` provides round-trip conversions to igraph, PyG, and DGL. The MCP server in `py3plex_mcp/`
exposes 7 tools and 3 resources covering the DSL v2 surface for AI-agent use.

## 3. What's reusable in Linus

The most directly relevant piece for Phase 2 is the **DSL v2 + executor + provenance triple**. Linus has already
committed (via the dual-substrate decision in Crossing 3) to networkx as the property-graph engine sitting beside
rdflib; py3plex's `multi_layer_network` is a `networkx.MultiDiGraph`-based container, so a Linus KnowledgeBase property
graph could in principle be wrapped as a degenerate one-layer py3plex network and gain the entire DSL-driven query/
community/centrality/uncertainty stack at the cost of one dependency. Even if Linus does not adopt the multilayer
container, the DSL design
(`Q.nodes().where(degree__gt=5).compute('pagerank').uq(method='perturbation', n_samples=100, ci=0.95).execute(network)`)
is a strong reference for what a Phase 3 hybrid-retrieval API should look like — typed, chainable, with uncertainty as a
first-class clause rather than a wrapper. The MCP server is a ready-made way to expose graph queries to Claude Code or
Cline during Phase 3 if Linus settles on MCP as its tool-registration substrate. The metapath2vec embeddings are
appropriate for a heterogeneous KB (paper / author / concept / claim layers) and would compose with the
Stankevičius-style vector layer that Crossing 3 calls for.

The serious **engineering hygiene** — CrossHair formal verification + icontract design-by-contract + z3 SMT solving +
Hypothesis property tests + a Fuzzing CI lane — is rare enough in this genre to be a differentiator on its own. The
contract decorators in `multinet.py` (`@require`, `@ensure`, `@invariant`) degrade to no-ops when icontract is missing,
which is the right pattern for Linus to copy in `src/linus/` for orchestration-layer invariants without forcing the
verification toolchain on every install.

**Differentiator vs. siblings.** Against `infranodus` (the other graph engine in this group), py3plex is a programmatic
library, not a discourse-analysis web app — it provides the algorithmic substrate where infranodus provides the
opinionated UX over a narrower analytical model (text-as-graph). Against the `agentic-wiki-builder` DuckDB+NetworkX
pattern Linus already references, py3plex is the natural upgrade path the day a single-graph property store starts
needing typed layers (papers vs. concepts vs. citations) and the day uncertainty quantification on centrality matters
for "is this concept actually a hub or just one perturbation away from being marginal?" — questions a plain `networkx`

- DuckDB stack cannot answer without a new layer of code that py3plex has already written and tested.

## 4. What's inspiration only

The visualization stack (diagonal-projection multilayer plots, hairball plots, supra-adjacency matrix plots, the
`example_images/py3plex_showcase.png` aesthetic) is paper-quality scientific visualization for human consumption, not
something Linus needs. Streamlit/openclaw chat is the Linus surface; py3plex visualizations would only matter if Dan
wanted publication-grade KB diagrams, which is not a Phase 2/3 goal. Likewise, the SWIG-bound Infomap algorithm and the
Cython build dependency are real installation friction that Linus should not adopt unless community detection becomes a
load-bearing Phase 3 retrieval primitive — and even then `python-louvain` (already a py3plex optional extra) covers the
80% case without SWIG.

## 5. What's incompatible or out of scope

py3plex is `requires-python = ">=3.8"` and pulls a substantial scientific dependency tree (numpy, scipy, networkx,
gensim, scikit-learn, matplotlib, seaborn, rdflib, bitarray, tqdm) plus heavy optionals (PyG, DGL, igraph, infomap,
plotly, pyarrow). The base install is fine; the `[optional]` meta-extra plus `[pyg]` would noticeably bloat the linus
conda env. None of this is Apple-Silicon-incompatible — it is pure-Python / scipy / NumPy — but PyG+DGL bring CUDA
expectations that do not apply on M1 Max, so those extras stay disabled. The included MCP server requires Python 3.10+,
which the linus env already satisfies (3.12). The library does not ship its own persistence layer beyond pickle and a
custom format; SQLite/DuckDB/parquet is left to the caller, which is fine because Linus is bringing its own KB store
anyway. There is no GPU acceleration of any kind — for graphs at the KB sizes Linus is plausibly building (10^4–10^6
nodes), this is not a problem; for KB sizes 10^7+ it would be.

## 6. Recommendation: **Study**

py3plex is too valuable to ignore and too heavy to integrate sight-unseen. The recommendation is to study it during
Phase 2 KB-spec work: read the DSL v2 design (`py3plex/dsl/builder.py` + `dsl/ast.py`) before specifying Linus's own
graph-query surface, port the `@require`/`@ensure` contract pattern into `src/linus/` for orchestration invariants, and
try a 50-node smoke test wrapping a tiny KB property graph as a one-layer `multi_layer_network` to feel out the API fit.
If by Phase 3 the KB has acquired multiple node/edge types in earnest (paper / author / concept / claim / source) and
uncertainty quantification on retrieval ranking has become a felt need, promote py3plex from Study to Integrate with a
DEC-NNNN ADR. The MCP server is the lowest-risk integration path — install `py3plex[mcp]` in a side env, expose it to
Claude Code, and see whether the DSL holds up under real KB queries before committing the Linus core to it.

## 7. Questions for Dan

- **Does Linus's KB actually become multilayer?** The DEC-0026/27 dual-substrate decision is RDF + property graph, not
  multilayer-property graph. If the property graph stays single-layer (one node-type universe, edges typed by relation),
  py3plex is overkill and plain networkx + a custom query helper is the right size. If layers (paper / concept / claim /
  author / source) are first-class, py3plex is the obvious substrate. Which way are you leaning before Phase 2 starts?
- **DSL design ownership.** py3plex's DSL v2 is genuinely well-designed, but importing it means Linus's graph query
  surface is shaped by an upstream library's roadmap. Do we want to fork the DSL design into a Linus-native query
  builder (lighter, KB-shaped, fewer concepts), or accept the dependency to avoid rebuilding what works?
- **Uncertainty quantification in KB retrieval.** py3plex makes confidence intervals on centrality/community a one-line
  `.uq(...)` clause. The synthesis-landscape work emphasizes epistemic standards and claim typing; UQ on graph-derived
  rankings is a natural extension. Is this a Phase 3 priority, or a Phase 4+ refinement?
- **Formal verification adoption.** CrossHair + icontract + z3 is a serious testing posture. Adopting even just
  icontract `@require`/`@ensure` for Linus's tool registry and sandbox boundary code would be cheap and high-value. Want
  to add this as a Known Library / Engineering Convention now, or wait for a concrete pain point?
- **MCP-as-tool-substrate, again.** py3plex ships an MCP server alongside pmetal's, openclaw's, and Cline's MCP support.
  The Phase 3 question — "is MCP the tool-registration substrate?" — keeps recurring. Three serious local-AI-adjacent
  projects in this repo collection have already answered yes. Time to make the call?
