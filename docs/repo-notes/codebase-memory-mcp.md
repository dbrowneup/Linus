# codebase-memory-mcp (`DeusData/codebase-memory-mcp`)

## 1. Purpose and scope

codebase-memory-mcp is a code intelligence engine shipped as a single static C binary (zero dependencies, cross-platform: macOS/Linux/Windows, arm64/amd64). It indexes full repositories into a knowledge graph (functions, classes, call chains, HTTP routes, infrastructure-as-code) using tree-sitter AST analysis across 155 languages, then exposes 14 MCP tools for structural search, call tracing, dead code detection, impact analysis, and Cypher-like queries. The headline claim: Linux kernel (28M LOC, 75K files) indexed in 3 minutes; any structural query answered in <1ms; 120x fewer tokens than file-by-file exploration. For Linus, this is directly applicable to both the KnowledgeBase submodule (add codebase indexing to the paper corpus) and the Worker orchestration layer (give Workers a graph-based "understand this codebase" capability, faster than LLM reasoning alone).

## 2. Architecture summary

codebase-memory-mcp compiles tree-sitter grammars for all 155 languages into a single executable (no external grammar downloads, no Ollama/Docker needed). On first run, it performs a multi-pass indexing: (1) file discovery (.gitignore aware, symlink-aware), (2) AST structure extraction, (3) definition resolution, (4) call-graph building, (5) HTTP route detection, (6) infrastructure-as-code indexing. All intermediate data lives in RAM with LZ4 compression; memory is freed after indexing. Results persist to `~/.cache/codebase-memory-mcp/` as SQLite (WAL mode, ACID-safe). The graph has ~30 node label types (Function, Class, Route, Resource, etc.) and 20+ edge types (CALLS, IMPORTS, HTTP_CALLS, DATA_FLOWS, etc.). MCP exposes 14 tools: search_graph (regex + filters), trace_call_path (BFS), detect_changes (git diff impact), query_graph (Cypher-lite), get_architecture (overview), semantic_query (nomic-embed-code vectors, int8, compiled in), plus infrastructure queries (Dockerfiles, Kubernetes). Background watcher auto-syncs after git changes. Optional graph UI (localhost:9749) for 3D visualization.

## 3. What's reusable in Linus

The tree-sitter indexing strategy is portable to Linus's KnowledgeBase: wrap the codebase-memory pipeline to index Dan's paper corpus + genomics codebases in a single unified graph. Use the semantic_query tool (nomic embeddings, no API) to enable "find papers similar to this query" without hitting Claude API. The call-graph + impact-analysis patterns are useful if Dan ever wants Workers to understand side effects of code changes (Phase 3 scenario). The Cypher-lite query language is a good fit for a Worker to express structural questions ("show me all functions that call this enzyme assay function across all papers/code"). The MCP integration is reference-grade: 14 tools cleanly separated, installed via `install` command that auto-detects 11 agents (Claude Code, Cursor, VS Code, Aider, etc.). Binary distribution model (static, no deps, verified by VirusTotal + sigstore) is a pattern Linus could copy for Workers.

## 4. What's inspiration only

The Louvain community detection (functional module clustering) is neat but overkill for Linus Phase 1-2. The HTTP route + gRPC/GraphQL detection is domain-specific to web services; not applicable to papers or bioinformatics code (different entry-point patterns). The infrastructure-as-code indexing (Dockerfiles, K8s manifests) is useful only if Linus targets containerized deployment. The LSP-style hybrid type resolution (Go, C++) produces higher-quality call graphs but requires language-specific analyzers that may not be worth the complexity for Linus's initial scope (Python + papers).

## 5. What's incompatible or out of scope

codebase-memory-mcp is C, not Python. Using it in Linus requires either (a) calling the binary via subprocess + JSON parsing (simple, works), or (b) porting the core graph store to Python (expensive). The binary is Linux/macOS-only; Windows support requires the full repo. The embedded Nomic embeddings (768d int8, 40K tokens) are efficient but may not match Linus's eventual embedding choice (Dan might fine-tune embeddings on his domain). The UI variant requires the compiled binary; can't be embedded as a library.

## 6. Recommendation: **Integrate (as Phase 2a spike)**

Start with the simplest integration: call the codebase-memory-mcp binary from Python Worker tasks via subprocess. Test on Linus's own codebase (query the graph of src/linus, understand module structure, trace task impact). If the spike succeeds (clarity gained, tokens saved), commit the binary to repos/ and wire it into the KnowledgeBase as an optional indexing tool for Users who have local codebases. Full Python port deferred to Phase 3+.

## 7. Questions for Dan

- **Binary distribution & trust.** codebase-memory-mcp ships pre-compiled binaries signed by sigstore. Should Linus adopt a similar distribution model for Workers (pre-built binaries + signature verification), or keep everything Python-in-conda for simplicity?
- **Graph unification.** If codebase-memory indexes papers + code in one store, Workers need to understand which edges are paper-citations vs. code-calls vs. semantic-similarity. Should the graph have a `source` property on each edge, or stay flat (queries would need to filter by node type)?
- **Semantic search integration.** codebase-memory uses int8 nomic embeddings (~0.5 MB). Should Linus adopt the same embedding + metric for consistency, or build a fancier embedding pipeline in Phase 3 when fine-tuning starts?
- **Incremental indexing.** codebase-memory's background watcher re-indexes on git changes. If Linus indexes the KnowledgeBase, how often should it refresh? Daily? On-demand? Or as a Phase 2a spike, skip auto-sync and require manual `index` commands?
