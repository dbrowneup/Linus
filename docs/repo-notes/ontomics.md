# ontomics (`EtienneChollet/ontomics`)

## 1. Purpose and scope

ontomics is a Rust-built MCP server that gives any coding agent a precomputed semantic ontology of a codebase, so that
questions like "what does `transform` mean here?" or "what are the main domain concepts?" resolve in a single tool call
instead of the 19–26 grep/read/follow calls a tool-using LLM would otherwise emit. The README's headline claim is "~20×
fewer tokens" against Claude Sonnet on the voxelmorph and ScribblePrompt repos, with answer-quality parity. It supports
Python, TypeScript, JavaScript, and Rust via tree-sitter, runs entirely locally with no API keys, and is listed on the
official MCP Registry. For Linus this matters in Phase 2a (the tool registry needs at least one strong code-context tool
that any front-end can call) and Phase 3 (hybrid retrieval — ontomics is structural/semantic and pairs with the
KnowledgeBase's prose retrieval).

## 2. Architecture summary

A single Rust binary (~17 source modules under `src/`, no `mod.rs` nesting), distributed as a static binary via npm,
Homebrew, a shell installer, and `cargo install`. The pipeline orchestrated in `main.rs` runs in fixed order:
`parser.rs` walks tree-sitter ASTs in parallel via rayon to extract `RawIdentifier`, `Signature`, `ClassInfo`,
`CallSite`; `tokenizer.rs` splits identifiers into subtokens (snake/camel/ALLCAPS) and detects abbreviations;
`analyzer.rs` runs TF-IDF over subtokens to find domain-specific concepts and detect naming conventions; `embeddings.rs`
runs Candle + safetensors inference with two models — BGE-small (384-dim) for concept clustering and CodeRankEmbed
(`nomic-ai/ CodeRankEmbed`, 768-dim) for function-body behavioral similarity; `cluster.rs` does agglomerative clustering
with average linkage; `entity.rs` promotes functions/classes to `Entity` nodes with semantic roles; `logic.rs` is the L4
behavioral layer that clusters function bodies and Jaccard-overlaps with concept clusters; `centrality.rs` PageRank-
scores entities. Everything lands in `graph.rs` (`ConceptGraph`), and `tools.rs` (`OntomicsServer` implementing
`rmcp::ServerHandler`) maps ~20 MCP tools onto `ConceptGraph` query methods. Persistence is SQLite at
`<repo>/.ontomics/index.db`, auto-invalidated by a `build.rs`-computed hash of indexing source files; `notify` watches
for incremental re-indexing. Deferred startup is the trick that makes the "one tool call" claim honest:
`cargo run -- serve` returns an MCP-ready server immediately on a graph built without embeddings, and the embedding work
completes in a background thread. The 20× token reduction is a single precomputed query against this index, not
on-the-fly parsing.

## 3. What's reusable in Linus

Directly reusable as a Phase 2a tool registered in Linus's MCP layer. Install path is one line
(`npm install -g @ontomics/ontomics`) and the binary auto-detects the git repo. Once Linus exposes an MCP tool surface
(currently planned for Phase 3 but the substrate decision is being framed during Phase 2a — see the "MCP as tool
substrate" finding in the cline and pmetal notes), `ontomics` becomes one of the first concrete tools front-ends like
Cline, Claude Code, or openclaw can call against any project Dan opens. The `compact_context` and `briefing` tools are
particularly relevant to Linus's Worker-loop ergonomics: a Worker about to refactor a file can pull a tiered
concept+logic context bundle in one call rather than burn its window on 20 reads. The `ontology_diff` tool against a git
ref is a cheap way to summarize "what changed semantically since main" — useful in branch reviews and the agent-branch
PR workflow described in BRANCHING.md. The Apple-Silicon story is fine: Candle ships a `metal` feature flag (declared in
`Cargo.toml`) for the embedding inference; CPU fallback works regardless.

Compared to **codesight** (the other code-context tool in this group): based on the group context note alone, codesight
appears to be the more direct competitor; ontomics's distinguishing pitch is the ontology layer — TF-IDF concept
extraction, naming-convention detection, abbreviation resolution, behavioral-similarity clusters, ontology diff between
git refs — not just symbol indexing. If codesight turns out to be a thinner LSP-style symbol/snippet retriever, the two
are complementary rather than substitutable; if codesight also builds a semantic layer, this note's recommendation will
need revisiting after that note is written.

## 4. What's inspiration only

The dual-embedding-model split (cheap 384-dim concept embeddings + expensive 768-dim code-body embeddings, both via
Candle) is a clean pattern Linus's own KnowledgeBase tools could borrow when ranking paper passages vs. code snippets
later. The `domain_pack` export — portable YAML of abbreviations, conventions, terms, associations — is an interesting
artifact format for cross-project knowledge transfer that Linus does not need now but is worth filing for Phase 7 skills
design (a "house style" pack per Dan project type). The deferred-startup pattern (MCP available immediately, embeddings
background-fill) is exactly the right ergonomic for any Linus tool whose first-run cost is dominated by indexing.

## 5. What's incompatible or out of scope

ontomics targets four general-purpose languages — Python, TypeScript, JavaScript, Rust. Dan's scientific work hits the
Python case directly; the others are bonus. Notably absent: R, Julia, shell, Nix, the bioinformatics DSLs (Snakemake,
Nextflow, CWL), and prose/Markdown. So it is not a substitute for the KnowledgeBase's paper retrieval and it will not
help with snakemake pipeline reasoning. The "must be a git repo" check refuses home/root/temp without `--force`, which
is fine but means scratch experiments under `experiments/` need to live inside the Linus git tree to be indexable — they
already do. The CodeRankEmbed download (~hundreds of MB) plus BGE-small are downloaded once on first run and cached
locally; first-touch cost on a fresh machine is non-trivial but one-time.

## 6. Recommendation: **Integrate**

In Phase 2a, install ontomics globally (`npm install -g @ontomics/ontomics`), add it via
`claude mcp add -s user ontomics -- ontomics` for the Claude Code path, and add an `.mcp.json` at the Linus repo root
for any front-end that honors that convention. Smoke-test on the KnowledgeBase submodule and on the Linus `src/` tree
once the latter has more than a stub. If the "one tool call vs 19" claim holds for Dan's actual question patterns,
ontomics becomes the default code-context tool Linus's Worker loop reaches for. If it doesn't hold or the index drifts
noticeably under active edit, fall back to grep + LSP and revisit when codesight is written up.

## 7. Questions for Dan

- **MCP-as-substrate decision timing.** Cline, openclaw, pmetal, and ontomics all speak MCP. Adopting ontomics in Phase
  2a effectively forces Linus to stand up an MCP client/registry earlier than ROADMAP currently has it. Do we want to
  pull that decision forward to Phase 2a explicitly, or run ontomics out-of-band (registered per-front-end) until Phase
  3? _Resolved (DEC-0018, see [answered-questions.md](../questions/answered-questions.md)): MCP-as-tool-substrate is no longer an open question; MCP ADR should be written at Phase 2a planning time; ontomics can be registered per-front-end now and folded into the Phase 2a MCP registry as it stands up._
- **Benchmark on a real Dan project.** The README's 20× claim is on voxelmorph and ScribblePrompt — clean ML repos.
  Should the Phase 1 benchmark suite include an "ontomics on KnowledgeBase" test (Python, mixed domain) to confirm the
  ratio holds on something messier?
- **Behavioral clustering on bioinformatics code.** CodeRankEmbed was trained on general code; how well does it cluster
  numerical/bioinformatics function bodies (lots of array math, similar shapes, different intents)? Worth a quick
  ablation before committing.
- **Sibling comparison gap.** This note can't yet differentiate ontomics from codesight beyond the README pitch. Do you
  want me to write the codesight note next so the head-to-head decision is made on facts rather than marketing?
- **Domain-pack export as a Linus artifact.** ontomics's YAML `export_domain_pack` could be checked into Dan's projects
  as a portable convention spec. Is that a workflow you'd actually use, or is it a "neat feature, never opened" risk?
