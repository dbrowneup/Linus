# Group 5 Synthesis — Knowledge-Graph & Network-Analysis Tooling

## What this document is

A cross-cutting synthesis of the seven repos in Group 5: **hyalo** (Integrate), **keppi** (Study), **py3plex** (Study),
**infranodus** (Study), **infranodus-skills** (Study), **OptimusKG** (Study), and **dlt** (Study/Integrate). These repos
arrived in the same fan-out because they all touch graph-structured knowledge management, network analysis,
knowledge-graph construction, ETL infrastructure, or the tooling layer that sits between a markdown vault and an LLM
agent. The initial five repos address graph analysis and vault interaction; OptimusKG and dlt expand the group to
include production knowledge-graph pipelines and data-ingestion tooling, both critical for Phase 3–4 KnowledgeBase
scaling. The repo notes live in `docs/repo-notes/{hyalo,keppi,py3plex,infranodus,infranodus-skills,OptimusKG,dlt}.md`.

One repo that appeared in an early draft of this group — prism — was removed before synthesis began: it was cloned in
error while searching for a differently-named project (claude-prism, now in Group 8). Its verdict was Ignore and it has
no bearing on the findings here.

---

## The unifying thesis

The core graph-and-vault repos (hyalo, keppi, py3plex, infranodus, infranodus-skills) collectively argue that the
markdown vault — a folder of interlinked notes with structured frontmatter — is not primarily a text corpus. It is a
graph, and graph structure should be a first-class retrieval primitive, not an afterthought layered on top of similarity
search. Each repo in Group 5 attacks a different face of this problem: infranodus shows what network science can reveal
about a text corpus (cognitive variability, structural gaps), py3plex provides the programmatic multilayer substrate and
DSL for querying and analyzing that structure, keppi turns wikilinks into a traversable graph and builds the retrieval
layer on top of it, and hyalo provides the safe, schema-validated editing surface that keeps the graph's edges
trustworthy in the face of concurrent agent and human edits. Infranodus- skills closes the loop by showing what
LLM-facing prompt patterns look like when the graph analysis has already been done.

None of these repos is complete in isolation. Hyalo edits the vault safely but performs no analysis. Keppi traverses and
retrieves but does not edit. Py3plex analyzes multilayer structure but has no vault-specific parser. Infranodus computes
cognitive-variability metrics but is AGPL, Node.js, and requires Neo4j. The interesting finding is that they compose: an
agent can use hyalo as its writing surface, keppi as its traversal and retrieval layer, py3plex (eventually) as its
uncertainty-quantified analysis layer, and infranodus-skills as a vocabulary for talking about what the graph reveals —
without taking on any AGPL code and without running a graph database.

---

## Key findings

**Hyalo earns its Integrate verdict on three grounds.** It is a single static Rust binary with no runtime dependencies
and no Python env to manage alongside the linus conda env; it ships as `brew install hyalo`. Its `hyalo mv` command
performs what no Claude Code built-in and no other tool in this group can: a planned, dry-runnable, transactional link
rewrite across an entire vault that captures source mtime before planning to detect concurrent edits. And
`hyalo init --claude` drops two skills (`hyalo`, `hyalo-tidy`) plus a vault-scoped rule into `.claude/` that redirects
Claude Code away from raw `Read`/`Edit`/`Grep` operations toward hyalo commands — meaning Maestro sessions operating
inside KnowledgeBase immediately benefit without any further configuration. Most directly for Linus: hyalo's
typed-schema system (per-`type` required fields, enum values, filename templates, date/list/number coercion) is exactly
what the `linus kb lint` placeholder sketched in early planning documents needed. It displaces that placeholder entirely
with a working, tested implementation rather than requiring Linus to write one.

**Keppi is the strongest Phase 3 retrieval reference in this group.** Its `blast_radius.py` implements bounded BFS with
multiplicative relevance-decay and typed-edge weights in roughly 100 lines of pure NetworkX; its `context_pack.py`
chains keyword search into BFS expansion and then greedily fills a token budget by degree-centrality re-rank. Together
these two functions answer the question the LLM wiki synthesis identified as the hardest retrieval design question: how
do you translate "topic + token budget" into a concrete reading set without asking the LLM to filter in-context? Keppi
answers it deterministically, using the graph. The `context_pack(topic, token_budget) → reading set` signature is
exactly what a Linus Worker needs to call before beginning a task. Keppi's MCP server also demonstrates a specific piece
of prompt engineering worth lifting: the `instructions` string in `keppi/mcp/server.py` tells the LLM client a preferred
tool-call order (`get_embed_status → semantic_search → keyword_search → blast_radius fallback`), encoding the retrieval
strategy in the tool definition rather than in the system prompt. That pattern should carry into Linus's own KB tool
definitions.

**The hyalo + keppi combination closes most of Phase 3's KB tooling gap without writing new code.** Hyalo handles the
write side: schema-validated authoring, transactional rename-and-relink, broken-link detection, bulk frontmatter
operations. Keppi handles the read side: graph-aware retrieval, context packing, community detection for gap analysis.
The two tools are complementary by design — keppi's own documentation explicitly disclaims the authoring role ("Keppi
doesn't compile external sources into a wiki"), which is hyalo's territory. What Linus would need to contribute is an
adapter that feeds hyalo's link graph output into keppi's graph builder with KB-appropriate edge weights (`cites`,
`co_author`, `shared_topic`, `shared_doi` in place of Keppi's Zettelkasten weights) — a few hundred lines of Python, not
a new system.

**Py3plex is a serious library that Phase 3 should read and Phase 4+ should consider promoting.** Its DSL v2
(`Q.nodes().where(...).compute('pagerank').uq(method='perturbation', ci=0.95).execute(network)`) is the clearest
published example of what a typed, chainable graph-query surface with first-class uncertainty quantification looks like.
Its engineering hygiene — CrossHair formal verification, icontract design-by-contract, Hypothesis property tests, a
fuzzing CI lane — is rare in academic graph libraries and sets a standard Linus's own orchestration invariants should
aspire to. Specifically, the `@require`/`@ensure`/`@invariant` contract decorators from `multinet.py` degrade to no-ops
when icontract is absent, which is the right pattern for Linus sandbox boundary code: assertions that document intent,
enforce it when the toolchain is present, and skip silently when it is not. The `py3plex_mcp` server also marks py3plex
as the fourth project in this repo set to ship an MCP server alongside its analytical tools — reinforcing the
cross-group finding that MCP is becoming the default tool-surface substrate for AI-adjacent projects, a finding that
should push toward an ADR.

**Infranodus's contribution is conceptual, not code.** The cognitive-variability framework — mapping Louvain modularity
and betweenness centrality onto a four-state model of biased, focused, diversified, and dispersed knowledge — is a
genuine addition to the analytical vocabulary Linus can apply to KnowledgeBase. The `Statement`-as-hyperedge data model
(a statement is a node linked to every concept it co-mentions, rather than just a binary edge between pairs) is also
worth lifting into the property-graph half of DEC-0015 (dual RDF + property-graph substrates): it preserves provenance
("this claim appeared in this context, attributed to this source") in the graph topology itself rather than as sidecar
metadata. Neither of these requires touching the AGPL code. The WWW'19 paper is the right source; `lib/entry.js` is
worth reading for the text-to-graph pipeline; `lib/db/neo4j.js` is worth reading for the Cypher patterns that compute
communities and gaps. Nothing should be vendored. The Python port (`DiscourseDiversity` on GitLab, MIT-licensed) is a
more tractable starting point for any re-implementation, subject to checking that it does not derive from AGPL-protected
logic.

**Infranodus-skills clarifies the Linus Skills format and surfaces a SaaS dependency problem.** Roughly one-third of the
fifteen skills in the repo call the hosted `mcp.infranodus.com` MCP server via an `INFRANODUS_API_KEY` — a direct
collision with Linus's "no paid APIs required for operation" principle. The remaining skills that are pure prompt
content (`critical-perspective`, the framework documentation inside `cognitive-variability`) are immediately useful as
cognitive primitives for Maestro review loops: the four-state variability vocabulary gives a concrete vocabulary for
diagnosing stuck or biased reasoning. The repo's GitHub Action that auto-builds `.zip`/`.skill` bundles on tag push is
also a useful template for how Linus should package its Phase 7 domain skills for distribution.

**OptimusKG demonstrates the production medallion architecture that KnowledgeBase v1 should emulate.** OptimusKG
integrates 65 biomedical data sources into a unified knowledge graph (190k nodes, 21.8M edges) following a medallion
pattern: landing layer (raw data), bronze layer (extraction and standardization per-source into Parquet), silver layer
(entity consolidation and relationship edges), and gold layer (final export via BioCypher). The catalog-first design
pattern — all datasets defined in YAML with schema, checksum, and origin metadata — provides the governance and
reproducibility layer that Linus will need as KnowledgeBase scales beyond paper corpus alone. The hook system (pre-
execution, validation, error recovery) and custom runners (FixedParallelRunner, DryRunner) for parallelism and
validation are directly applicable patterns. Most critically: OptimusKG's Polars-based transformation layer (not Pandas)
and validation story (checksums, schema validation, human-in-the-loop QA via PaperQA3) show what data integrity and
reproducibility look like at production scale. Linus does not need to match OptimusKG's 65-source integration; the Phase
3 scope is closer to 10–15 sources. But the architectural pattern — landing → bronze → silver → gold, with
catalog-driven governance — is the blueprint for KnowledgeBase v1's design.

**dlt is the authoritative ETL backbone for KnowledgeBase corpus feeding and ingestion.** dlt is a production-grade
Python library that abstracts the "extract, normalize, load" cycle: extract from REST APIs, SQL databases, cloud
storage, or 5000+ verified sources; infer and normalize schemas from messy, nested data; and load into any destination
(DuckDB, Snowflake, etc.). What makes dlt strategic for Linus is not the verified sources (Dan's data sources are
domain-specific), but three core capabilities: schema contracts (Pydantic models that enforce required fields and types,
catching corruptions early), incremental loading with checkpoint-based state tracking (enabling monthly corpus updates
without re-processing everything), and a pure-Python library model that runs anywhere without lock-in. These three
features directly address the "corpus health monitoring" and "reliable incremental ingestion" problems that
KnowledgeBase v1 will face. The contract system parallels the validation layer Linus will build; the state-tracking
pattern enables periodic corpus refresh (new papers, updated genome annotations) without waste. dlt is also tuned for
Linus's stack: typed with mypy and ruff, uses `uv` for fast dependency resolution, and includes a rich CLI for schema
inspection. The Phase 2a entry point is straightforward: a simple spike that prototypes a pipeline loading 10 papers
from a local directory into DuckDB, validates schema contracts, and measures init cost and runtime on M1 Max. If that
spike proves promising, dlt becomes the Phase 2b authoritative ETL layer for all KnowledgeBase ingestion.

---

## Patterns and modules worth lifting

**Hyalo's schema type system.** The `.hyalo.toml` `[schema.types.*]` block defines per-type required fields, value
enumerations, date and number coercion, and filename templates. For Linus the immediately useful type definitions are
`paper` (required: `title`, `doi`, `status`, `claim_types`), `decision` (mirrors the `docs/adr/` format), `experiment`
(mirrors `experiments/`), and `iteration` (for the `iter-NN-slug` ADR-convention hyalo's own CLAUDE.md documents). This
is not aspirational scaffolding — it is a working, tested schema enforcer that runs in milliseconds on a cold vault.

**Hyalo's `mv` transaction model.** `link_rewrite::plan_mv` produces a `RewritePlan` that covers wikilinks (including
aliases and section anchors), markdown links, and configured frontmatter properties, then captures the source mtime
before planning to detect concurrent edits. The `--dry-run` flag previews the full diff before commit. This is the
correct transactional model for any operation that touches links in a graph-structured vault; it is also what makes
hyalo safe to call from an agent loop where the human may be editing simultaneously.

**Keppi's `blast_radius.py` traversal pattern.** A deque-based BFS with multiplicative relevance-decay (`threshold=0.3`
default), typed-edge weights (`wikilink=1.0`, `embed=1.5`, `related_to=2.0`), and best-relevance-wins on revisit. The
core function is about 80 lines. For KnowledgeBase the weights should be re-calibrated to paper-corpus edges: citation
edges carry stronger signal than co-authorship, and shared-DOI edges are stronger than shared-topic tags. But the
structure — bounded BFS with decay, directional flag for backlink expansion, `__broken__` sentinel for dangling
references — ports directly.

**Keppi's `context_pack` greedy-fill algorithm.** `build_context_pack(topic, token_budget, ...)` chains keyword search
into `blast_radius`, then re-ranks by degree centrality, then greedily fills to the token budget. This is a complete
answer to the LLM wiki synthesis's finding that "scoping should be deterministic" — the LLM receives a pre-filtered
context bundle from the graph layer rather than filtering in-context. The function signature itself
(`topic + token budget → reading set`) is the right shape for a Linus KB tool.

**Keppi's MCP server instructions string.** The `instructions` field in `keppi/mcp/server.py` encodes the preferred
retrieval strategy (`embed_status → semantic_search → keyword_search → graph traversal`) as part of the tool definition.
This means the strategy travels with the tool and does not need to be re-specified in every system prompt. Linus's KB
tool definitions should adopt this pattern: embed retrieval strategy and fallback order in the tool's `instructions`
field, not in the agent's system prompt.

**Py3plex's `@require`/`@ensure` contract pattern.** The icontract decorators in `multinet.py` are no-ops when the
library is absent, making them a zero-cost documentation mechanism in environments that do not install the verification
toolchain. For Linus's orchestration-layer sandbox boundary code — especially the tool registry and the agent spawner —
adopting `@require`/`@ensure` for pre/post-conditions gives both documentation and, when icontract is installed in a
development env, actual runtime enforcement. This is Phase 2 work and a low-risk, high-signal engineering convention to
adopt now.

**Infranodus's `Statement`-as-hyperedge data model.** Rather than binary concept-to-concept edges, infranodus stores
each statement as a node that is then linked to every concept it co-mentions via `:OF` edges. This preserves the
provenance of the relation (which statement, in which context, from which user) in the graph topology itself. For the
property-graph half of DEC-0015, this is worth adopting for episodic memory events that span multiple concepts — an
event node linked to the concepts it mentions rather than binary edges between each concept pair. It solves the
"provenance as sidecar metadata" problem that binary edges create.

---

## Cross-references

**Total-landscape Crossing 3 (KB as graph + vector substrate).** This group provides the tooling layer Crossing 3 was
missing. The dual-substrate decision (rdflib + networkx, DEC-0015) resolves which storage engines to use; hyalo and
keppi together resolve how that substrate gets populated and queried at the agent layer. Py3plex is the upgrade path
when the property graph becomes genuinely multilayer.

**G2/G3 LLM wiki synthesis.** The LLM wiki synthesis named `keppi` as a Phase 3 reference and suggested cloning it into
`repos/`. This synthesis confirms that recommendation and adds hyalo as the complementary authoring tool the LLM wiki
synthesis did not have visibility into. The compile-don't-retrieve thesis of the LLM wiki synthesis maps onto the
hyalo-as-vault-editor / keppi-as-graph-retriever split: hyalo is the compilation surface, keppi is the deterministic
scoping layer the compiled vault enables.

**G6 MCP/code-context (anticipated).** Py3plex's `py3plex_mcp` server and keppi's 19-tool FastMCP server are the third
and fourth MCP servers in the cross-group count (after pmetal-MCP and Cline's MCP surface). The question "is MCP the
tool-registration substrate?" that recurs across repo notes is becoming load-bearing. Group 5 adds two more data points:
both py3plex and keppi ship MCP servers without friction, and both demonstrate that the MCP tool-definition format can
carry retrieval strategy (keppi's `instructions` field) alongside tool parameters. The ADR on "MCP as Linus tool surface
vs. native registry" should absorb this group's findings.

**Memory synthesis (Layer E — semantic/knowledge memory).** KnowledgeBase is Layer E in the five-layer memory
architecture (A: intra-step latent; B: within-session scratchpad; C: cross-session episodic; D: investigation memory; E:
semantic knowledge — per DEC-0028 through DEC-0052). This group provides the tooling that makes Layer E queryable via
graph structure rather than only via vector similarity. The `context_pack` primitive from keppi is the deterministic
scoping mechanism the memory architecture calls for: Workers receive pre-filtered context from the graph layer rather
than filtering in-context, which is both faster and more reliable. The uniform read API across memory layers (scratchpad
/ episodic / semantic) should present `context_pack`-shaped calls at the KB tool surface regardless of which layer the
context ultimately comes from.

---

## Phase-tagged implications

**Phase 2a — Linus MVP (immediate + early spike):** Install hyalo via Homebrew, point `.hyalo.toml` at `context/notes/`
with a Linus schema (`paper`, `thread`, `decision`, `experiment`, `iteration`), run `hyalo init --claude` to install the
vault-scoped rule and skills into `.claude/`. This is an afternoon of setup and it immediately improves every Maestro
session that touches KnowledgeBase notes. Read py3plex's DSL v2 design (`dsl/builder.py`, `dsl/ast.py`) before
finalizing Linus's graph-query surface in `docs/specs/kb-architecture.md` — the DSL is a stronger prior for what a
typed, chainable, uncertainty-aware query interface looks like than anything Linus would design from scratch. Port the
`@require`/`@ensure` contract pattern into `src/linus/` for sandbox boundary code (DEC-0027 implementation — Linus
practice stance on public APIs and engineering hygiene). Conduct a Phase 2a spike with dlt: prototype a simple pipeline
that loads 10 papers from a local directory into a DuckDB table, verify that schema contracts catch format mismatches,
and measure init cost and runtime on M1 Max. The goal is to validate whether dlt is the right ETL backbone for
KnowledgeBase ingestion before committing to Phase 2b integration.

**Phase 2b — Knowledge Base ingestion backbone:** If the dlt spike succeeds, integrate dlt as the authoritative ETL
layer for KnowledgeBase corpus feeding. Use dlt's schema contracts to validate paper metadata and content quality, and
checkpoint-based state tracking to enable monthly corpus updates without re-processing. Start with a simple source
(local papers directory) before expanding to API-driven sources (GitHub READMEs, structured databases). Note: DEC-0029
chose SQLite as the episodic and session store; the corpus analytics destination for dlt is a separate open question
(DuckDB and PostgreSQL are still candidates for Phase 2b bulk corpus indexing).

**Phase 3 — Knowledge & Parallel Agents (primary target):** Port keppi's `blast_radius` and `context_pack` as
Linus-native functions over the KnowledgeBase graph, replacing keppi's Zettelkasten edge weights with paper-corpus
weights (`cites`, `co_author`, `shared_topic`, `shared_doi`). Wire the resulting `context_pack(topic, token_budget)`
into the Worker invocation protocol as a standard pre-task KB query. At that point the hyalo + keppi combination covers
both the authoring side (DEC-0026/27 graph population via vault editing) and the retrieval side (deterministic graph
traversal for context scoping) without custom infrastructure beyond the weight adapter. Adopt OptimusKG's medallion
architecture (landing → bronze → silver → gold) and catalog-first governance pattern as the canonical design for
KnowledgeBase v1. Phase 3 scope is 10–15 initial sources (papers, notes, genomics databases, tool documentation), not
65, but the medallion pattern scales cleanly and provides the reproducibility and validation hooks Linus will need as
the KB grows. Evaluate whether the infranodus cognitive-variability metric (biased/focused/diversified/dispersed) is
worth implementing in Python against the KnowledgeBase graph as a quality-of-coverage signal.

**Phase 4+ — Uncertainty quantification on KB retrieval:** If the property graph has grown to include multiple node
types in earnest (paper / author / concept / claim / source) and retrieval ranking needs principled confidence
intervals, promote py3plex from Study to Integrate with a DEC-NNNN ADR. The MCP server path (`pip install py3plex[mcp]`
in a side env, expose to Claude Code, smoke test against real KB queries) is the lowest-risk entry.

**Phase 7 — Skills & Autonomy Graduation:** Use infranodus-skills' GitHub Action workflow (auto-build `.zip`/`.skill`
bundles on tag push) as the template for how Linus packages domain skills for distribution. The `infranodus-cli` skill's
`requires.bins: ["mcporter"]` frontmatter pattern (machine-readable external dependencies) is worth adopting in any
Linus skill that wraps a CLI binary. If a self-hostable text-network-analysis layer is in place by Phase 7, revisit
infranodus-skills' MCP-dependent skills as candidates to wire against that local backend.

---

## Open questions for Dan

**Vault location.** Hyalo's `.hyalo.toml` must point at a concrete path. The three candidates — `context/notes/`
(gitignored, personal), a new top-level `vault/` (tracked, Dan-owned), or inside `modules/KnowledgeBase/` next to the
paper corpus — each have different implications for what gets indexed, what is gitignored, and how KnowledgeBase's own
submodule governance interacts with hyalo's schema. The simplest starting point is `context/notes/` with a `.hyalo.toml`
that stays gitignored alongside it. _Promoted to top-questions.md as R2-07._

**Hyalo vs. keppi bake-off.** The repo notes recommend a 30-minute Phase 1 spike (find by tag, bulk set status, rename +
link rewrite, lint with schema, summary) run under both tools on the same sample vault. That spike would close the
"confirm which operations keppi actually supports" question that the infra note leaves open, and produce an ADR verdict
on how the two tools divide responsibility rather than leaving it implicit. _Promoted to top-questions.md as R2-08._

**Paper-corpus edge weights for blast radius.** Keppi's default weights (wikilink=1.0, embed=1.5, related*to=2.0) were
tuned for a Zettelkasten. KnowledgeBase's edges are paper-shaped. What is the right relative weight for a citation edge
vs. a co-authorship edge vs. a shared-topic edge? The answer should come from a smoke test on a known retrieval case
(given paper A, what should context-pack return?), not from a priori intuition. \_Tracked in top-questions.md as R2-33
(Tier 3).*

**AGPL re-implementation scope.** The cognitive-variability metric from infranodus is unencumbered as an idea (WWW'19
paper); the code is AGPL. The Python port on GitLab (`DiscourseDiversity`) is MIT-licensed but derives from the same
codebase. Confirm the policy — "re-implement from the paper, never copy, and verify MIT ports are independently clean
before borrowing" — and document it as a DECISIONS.md entry rather than leaving it implicit in the repo note. _Tracked
in top-questions.md as R2-34 (Tier 3)._

_Resolved (DEC-0018, DEC-0045, DEC-0046): MCP is Linus's tool-registration substrate from Phase 2 onwards; the registry
is built on fastmcp. Local-only MCP is the default; external MCP servers requiring paid API keys are governed by
DEC-0046's `external_api_tool` registry class with a `deployment` field._

**InfraNodus self-hosting.** If Linus reaches Phase 3 with a working text-network-analysis layer over KnowledgeBase, the
MCP-dependent skills in infranodus-skills become interesting again if that layer can expose an InfraNodus-compatible
API. Is that worth scoping as a Phase 3 stretch goal, or does it stay filed under "interesting but not load-bearing
until someone actually misses it"? _Partially resolved (DEC-0018, DEC-0045, see
[answered-questions.md](../../questions/answered-questions.md)): MCP adopted as extensibility substrate; fastmcp as the
in-house default. A local infranodus façade would follow the same pattern if Phase 3 brings a self-hostable
text-network-analysis component._

---

## References

### Repo-notes

- [`claude-prism`](../../repo-notes/claude-prism.md) — Named here to disambiguate from the early-draft `prism` that was
  cloned in error; claude-prism now lives in Group 8.
- [`cline`](../../repo-notes/cline.md) — Referenced for its MCP surface as part of the cross-group MCP-as-tool-substrate
  count.
- [`dlt`](../../repo-notes/dlt.md) — Authoritative ETL backbone candidate for KnowledgeBase corpus feeding: schema
  contracts, incremental loading with state tracking, pure-Python library model.
- [`hyalo`](../../repo-notes/hyalo.md) — Integrate-verdict static Rust binary; `hyalo mv` provides transactional link
  rewrites with concurrent-edit detection and a typed-schema system that displaces the `linus kb lint` placeholder.
- [`infranodus`](../../repo-notes/infranodus.md) — Cognitive-variability framework (Louvain modularity + betweenness
  centrality → biased/focused/diversified/dispersed); contribution is conceptual, code is AGPL.
- [`infranodus-skills`](../../repo-notes/infranodus-skills.md) — Fifteen skills clarifying the Linus Skills format;
  one-third depend on hosted `mcp.infranodus.com`, the rest are pure prompt content.
- [`keppi`](../../repo-notes/keppi.md) — Phase 3 retrieval reference: `blast_radius.py` bounded BFS with decay and
  `context_pack.py` greedy-fill to token budget; MCP `instructions` field encodes retrieval strategy.
- [`OptimusKG`](../../repo-notes/OptimusKG.md) — Production medallion architecture (landing → bronze → silver → gold)
  for biomedical knowledge graphs; catalog-first governance pattern for KnowledgeBase v1.
- [`paper-qa`](../../repo-notes/paper-qa.md) — Referenced via OptimusKG's PaperQA3 human-in-the-loop QA validation
  pattern.
- [`pmetal`](../../repo-notes/pmetal.md) — Referenced for its pmetal-MCP server as part of the cross-group
  MCP-as-tool-substrate count.
- [`py3plex`](../../repo-notes/py3plex.md) — Serious multilayer-graph library with DSL v2 query surface, first-class
  uncertainty quantification, and rigorous engineering hygiene (CrossHair, icontract, Hypothesis).
