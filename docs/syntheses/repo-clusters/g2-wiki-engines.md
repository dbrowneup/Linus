# Group 2 Synthesis — LLM Wiki Engine Implementations

_Date: 2026-05-08 (updated). Sources: eleven repo notes under `docs/repo-notes/` for link, llmwiki, llmbase,
llmwiki-cli, wikidesk, wikiloom, wikimind, OmegaWiki, swarmvault, synthadoc, and TheKnowledge. Read against
`docs/syntheses/llm-wiki-synthesis.md` (the conceptual framework this extends) and Crossing 3 of
`docs/landscapes/total-landscape.md` (the KB substrate decision this feeds)._

---

## What this document is

The existing `llm-wiki-synthesis.md` established the conceptual framework: compile-don't-retrieve, three-layer
architecture, content hashing for staleness, the schema as flywheel, write-back as discipline, hybrid retrieval past the
200-node wall. That framework was built from the Karpathy gist, the Rohit v2 gist, and community practitioners. This
document extends it with what eleven independent code authors actually shipped. The question this synthesis answers is
not "what is the LLM Wiki pattern?" but "of the 18 wiki-engine repos now surveyed across Groups 2 and 3, which specific
artifacts are worth lifting into Linus — and when?"

---

## The unifying thesis — why all 11 landed at Study

Every repo in Group 2 arrived at Study rather than Integrate, and this is not a per-repo judgment about individual
quality. It is a structural finding. Linus's KnowledgeBase has a shape none of them targets.

The eleven siblings were all built around a common personal-vault premise: one user, one directory of notes or papers,
one LLM maintaining a wiki over that directory, one agent reading the wiki back. That shape is coherent and several
repos ship it with real sophistication. But Linus's KB is governed by three decisions that collectively put it outside
any sibling's drop-in range. DEC-0026/27 commits to a dual-substrate RDF plus property graph (rdflib + networkx,
Oxigraph evaluated later), rather than the flat markdown graph every sibling uses. DEC-0028 elevates memory architecture
to a Phase 2 first-class pillar, subsequently expanded to Layers A through E (DEC-0052 added Layer D — investigation
memory — and renumbered KB to Layer E), which means the KB is not the entire memory system — it is Layer E of a
five-layer stack, and its read API must eventually present uniformly alongside the scratchpad, episodic, and
investigation-memory layers. And the overall system targets scientific papers with claim-level epistemic typing
(`[!source]`, `[!analysis]`, `[!unverified]`, `[!gap]`) and content-hash provenance at the chunk level, which is
stricter than anything any sibling enforces as a first-class invariant.

The gap is not capability — some siblings are impressively complete. The gap is shape. A personal-vault wiki engine that
works for markdown notes works poorly as the semantic memory pillar of a Maestro/Worker orchestration backend with
typed-claim enforcement, parallel-agent write coordination, and a unified retrieval API across memory layers. That is
why all 11 are Study and none are Integrate: they are rich in prior art but wrong in shape.

---

## Pattern convergence — what every implementation shares

Reading across all eleven repos, six patterns appear in every implementation regardless of implementation language,
storage substrate, or deployment target. They represent the points where the community has effectively converged.

The three-layer split — immutable raw sources, LLM-authored wiki markdown, schema document — is universal. Every engine,
from link's 2800-line stdlib Python to swarmvault's four-package pnpm monorepo, treats the schema file (`LINK.md`,
`AGENTS.md`, `swarmvault.schema.md`, `WIKI.md`, `SKILL.md` per skill, `SCHEMA.md`) as the core product, not
configuration. The agents read the schema first; the schema defines entity types, write conventions, and lint rules;
everything else is substrate.

Wikilink cross-references as the primary graph representation are shared across all eleven, with `[[concept]]` syntax
and some form of backlink index (`_backlinks.json`, the `document_references` edge table, `edges.jsonl`,
`backlinks.json`). The format may seem like a markdown aesthetic choice, but it is actually load-bearing: it makes the
graph readable by both agents and humans without a separate graph database, and it is what makes Obsidian immediately
useful as a viewer over any of these wikis.

Append-only audit logging appears in every production-shaped implementation — `log.md` in link, llmwiki, and
TheKnowledge; `audit.db` SQLite with source SHA-256 in synthadoc; `chunk_cache.py` JSONL event logs in llmbase; git
history as the audit log in wikiloom. The substrate varies but the invariant — every mutation is logged immutably — is
constant.

A lint or doctor command for graph hygiene appears across the group. Link's `doctor` command is the most developed:
orphan detection, dead-link checking, stale `source_count` metadata, isolated graph nodes, secrets-in-filenames scan.
WikiMind has a linter subpackage. OmegaWiki has `/check` for bidirectional-link enforcement. Synthadoc runs periodic
lint passes. This pattern is independently rediscovered and worth adopting verbatim.

Write-back as a first-class discipline appears everywhere, though the enforcement mechanism varies — TheKnowledge's hard
citation validator rejects any write without a resolved `[[sources/]]` link; wikiloom's two-layer human-edit protection
uses commit prefixes plus auto-region markers; synthadoc's audit trail creates accountability after the fact. The
pattern the conceptual framework recommended is not aspirational; it is already the consensus.

Provider abstraction over the LLM call is present in every multi-repo implementation: wikiloom's litellm routing,
llmbase's OpenAI-compatible endpoint (which accepts Ollama), wikimind's five-provider router, synthadoc's `providers/`
with Ollama as the local path, swarmvault's pluggable task-provider separation. Every serious implementation separates
"which model" from "what to do with the model's output," because swapping backends is the first thing a real user does.

---

## Differentiators — where the cluster diverges

Within that convergence, the cluster diverges along three meaningful axes.

**Storage substrate.** Link, llmwiki, llmwiki-cli, llmbase, wikiloom, OmegaWiki, and TheKnowledge are all
markdown-on-filesystem, with derived caches in SQLite. Wikidesk and swarmvault add a typed knowledge graph
(`graph.json`, Neo4j-optional in swarmvault) alongside the markdown. Wikimind goes furthest with SQLModel tables,
optional Postgres, and ARQ-backed async compilation. The spread from "flat markdown" to "full RDBMS with background job
queue" spans the group, and every point on the spectrum has a real implementation.

**Provenance depth.** This is where the group diverges most meaningfully for Linus's purposes. Wikiloom implements the
deepest provenance: `chunk_id = sha256(source_hash + chunk_index)[:12]`, stored in every page's `sources` frontmatter
array, so any claim traces deterministically to the exact text the LLM saw. TheKnowledge enforces citation at write time
— the validator rejects any page without a resolved `[[sources/<id>]]` link. Link tracks `[confidence: high/medium/low]`
in prose but has no hash-stable chunk addressing. Llmbase has per-source metadata but no per-claim typing. OmegaWiki
adds a `confidence` field to typed graph edges. Synthadoc's audit DB records source SHA-256 at ingest but not per-claim.
The provenance spectrum runs from wikiloom's chunk-level hash addresses to link's prose-only confidence tags, and no
sibling has implemented all three of: chunk-level hashing, claim-type typing, and citation-enforcement at write time
simultaneously.

**Scope of the lifecycle.** OmegaWiki extends the wiki straight through to LaTeX paper submission and reviewer rebuttal.
Synthadoc treats the wiki as a long-running operational service with a durable job queue, cost gates, OTel traces, and
cron-style scheduling. Swarmvault adds context packs and a task ledger as first-class artifacts. Link, llmwiki-cli, and
wikiloom stop at the wiki itself. The spectrum from "markdown maintenance tool" to "research lifecycle platform" spans
all eleven repos, and Linus's relevant horizon is somewhere between synthadoc's operational posture and link's elegant
minimalism.

---

## Patterns and modules worth lifting

This is the section that matters for Linus's roadmap. Each lift candidate is named with its source, the specific files
or patterns to read, and the phase where it becomes actionable.

**wikiloom's chunk-id derivation** (`chunk_store.py`: `chunk_id = sha256(source_hash + chunk_index)[:12]`) is the
highest-priority lift for Phase 2. The conceptual framework called for content hashing; wikiloom is the closest existing
prior art that has shipped and debugged this specific formula. The truncation to 12 hex characters is documented with
its collision-probability math (negligible below ~10M chunks per source, which Linus will not reach in Phase 2). For
Linus's KB schema design, adopt this derivation as the canonical convention — or consciously choose full-length hashes
for zero-collision peace of mind and document why. Either way, read `wikiloom/chunk_store.py` before the Phase 2 KB
schema spec is finalized. The tiered-confidence linker (95/85/70 cutoffs, producing auto/flagged/pending/discarded
outputs with a `pending.json` queue for human review) is the companion pattern for entity resolution and is worth
adopting or at least using as the numeric baseline for Linus's own tuning.

**llmbase's operations registry** (`llmwiki/operations.py`, 628 lines:
`Operation(name, description, handler, params, writes, category)` + `register()` + `dispatch()` with write-lock
escalation) is the most directly liftable structural pattern in the group for Phase 2. The problem it solves — one tool
definition drives CLI, HTTP, and MCP without drift — is exactly the problem Linus's Phase 2a tool registry faces. The
`_needs_write_lock` escalation hook for operations like `kb_ask` that can promote to write is a useful detail most
implementations miss. Read `llmwiki/operations.py` and `llmwiki/pipeline/` before designing the Linus tool registry. Do
not vendor llmbase itself (the OpenAI-only client and trilingual Buddhist-canon deployments are the wrong shape), but
the registry pattern is nearly drop-in.

**wikidesk's runner-trait abstraction** (`server/src/runner/mod.rs`: one trait, three implementations — `generic`,
`stream-json`, `acp`; bounded by a 2-permit semaphore and a 128-slot mpsc queue) is the right template for Phase 3
parallel-Worker write coordination. Wikidesk is the only sibling that has thought about multi-agent deployment topology
— N agents on N machines sharing one wiki server, with lifecycle-hook sync keeping local mirrors current. The `research`
MCP tool (submit a question, get a `task_id`, poll `get_result`) is the Maestro/Worker pattern implemented at MCP-tool
granularity. Read `server/src/runner/mod.rs`, `queue.rs`, and the sync protocol in `shared/src/lib.rs` before designing
Phase 3 agent fan-out and queued tool semantics. The whole server is ~2.4k lines of Rust, readable in an afternoon.

**OmegaWiki's `.claude/skills/` layout** is the cleanest worked example of the Anthropic Skills standard among all repos
surveyed. Each skill is a real `SKILL.md` with `description`, `argument-hint`, on-demand `references/`, explicit
Reads/Writes, and a clean deterministic-tool-vs-LLM split. The claims/experiments/ideas wiki schema — with
`failure_reason` as "anti-repetition memory" to prevent re-running failed experiment paths — maps onto Phase 2 KB almost
without translation. OmegaWiki's 24 skills spanning the full research lifecycle are the correct prior art for Phase 7
skills graduation: the delta between OmegaWiki's 24 skills and link's minimal tool surface is roughly the shape of the
Phase 7 planning problem. Read all 24 `SKILL.md` files and the wiki schema before Phase 7 begins.

**TheKnowledge's NlmClient Protocol pattern** (`gateway/nlm_client.py`: an `NlmClient` Protocol with a real
`NlmCLIClient` that shells out to the third-party `nlm` CLI, and a mock for tests) is a textbook typed-seam for wrapping
any flaky third-party CLI. The gateway-as-only-writer discipline — every mutation through one entrypoint, running
frontmatter validation + slug-collision checks + citation-graph enforcement + event logging — is the most defensible
write architecture in the cluster for preventing hallucination drift. The citation validator that hard-rejects any page
missing a `[[sources/<id>]]` link is the strictest answer to the epistemic-integrity problem identified in the
conceptual framework, and the only implementation that enforces it mechanically at write time rather than by convention.
Read `gateway/validator.py`, `gateway/nlm_client.py`, and `gateway/converters/` before speccing the Phase 2 KB write
interface.

**llmwiki's `guide` MCP tool** (`mcp/tools/guide.py`) is the cleanest example of schema-as-tool-output — a long,
opinionated prompt defining the wiki's ontology delivered as an MCP tool return value rather than embedded in the system
prompt. Every Claude session calling `guide` re-anchors on the same structure without the schema consuming system-prompt
budget. The pattern scales better than encoding the schema in CLAUDE.md for large ontologies, and it is directly
applicable to Linus's KB query surface once MCP is adopted in Phase 3.

**synthadoc's decomposition agent pattern** (`agents/search_decompose_agent.py`: split a compound query into parallel
focused sub-queries, fan out, merge, deduplicate, fall back on LLM failure) is the clearest articulation of Phase 3's
agent fan-out shape among all eleven repos. Synthadoc also contributes the `BaseSkill` hot-load registry (scan a
directory, load extensions without restart, dispatch by file extension or intent prefix) as a concrete Phase 7 reference
for dynamic skill loading. Both patterns are worth reading before Phase 3 design begins. Note the AGPL-3.0 engine
license: lift the pattern, not the code.

**swarmvault's context-pack and task-ledger patterns** (`packages/engine/src/context-packs.ts`:
`swarmvault context build "<goal>" --target <path> --budget <tokens>` writing a cited, token-bounded handoff;
`packages/engine/src/memory.ts`: `task start|update|finish|resume` recording a durable task history folded back into the
knowledge graph) map directly onto the Maestro/Worker handoff problem in `docs/maestro-worker-protocol.md`. The
spec-in-`experiments/<task>.md` flow could borrow the bounded-context-pack model wholesale — the goal, target, and token
budget are exactly the fields a Worker spec needs. Read both modules before Phase 2 Worker spec format is finalized.

---

## Cross-references

The primary cross-reference is to `docs/syntheses/llm-wiki-synthesis.md`. This synthesis does not re-derive the
framework established there — it assumes it. The community patterns (content hashing, write-back rule, quality gate at
ingest, hybrid retrieval past 200 nodes, scoping deterministically before reasoning probabilistically) are the
conceptual framework; the above lift candidates are the community's concrete implementations of those patterns.

The memory-synthesis cross-reference (`docs/syntheses/memory-synthesis.md`) is also load-bearing. Layer E of the
five-layer memory architecture (semantic/knowledge memory, renumbered from Layer D via DEC-0052) is where KnowledgeBase
sits. The uniform read API requirement — Workers cannot tell whether context came from scratchpad, episodic, or
knowledge memory — is a design constraint no sibling has addressed because none is building a layered memory system.
This is the architectural gap that makes all 11 Study rather than Integrate, and it is worth naming explicitly in the
Phase 2 KB spec.

The G3 wiki patterns group adds 7 more repos to the same Study verdict (see
`docs/syntheses/repo-clusters/g3-wiki-patterns.md`), bringing the full count to 18 LLM Wiki repos, all Study. The G3
survey confirms that none of the seven G3 repos (agentic-wiki-builder, AgenticResearchWiki, llm-research-wiki,
llm-wikidata, atomic-knowledge, beever-atlas, obsidian-llm-wiki-local) achieved all three provenance properties
simultaneously — the wikiloom + TheKnowledge split for provenance depth stands across the full 18-repo cohort. The
paper-qa reframing from g8-sci-agents (KB substrate as "adopt + extend" rather than "build from scratch") is worth
surfacing here: Phase 2 KB can bootstrap on paper-qa's existing ingest pipeline and layer the chunk-id derivation and
citation enforcement described above on top rather than re-implementing the base infrastructure.

---

## Phase-tagged implications

**Phase 2 KB schema (immediate).** Before any code is written for KnowledgeBase v1, read wikiloom's `chunk_store.py` and
TheKnowledge's `validator.py`. The chunk-id derivation and the citation-enforcement validator are the two most directly
actionable patterns in the group for the Phase 2 KB schema decision. Read llmwiki's `mcp/tools/guide.py` and link's
`LINK.md` for the schema-as-tool-output and page-template conventions. Read llmbase's `operations.py` for the tool
registry shape. These five reads, perhaps 3000 lines total, cover the highest-value design decisions.

**Phase 2 Worker spec format.** Before the Maestro/Worker protocol spec is finalized, read swarmvault's
`context-packs.ts` and `memory.ts`. The bounded-context-pack format (goal + target + token budget + citations) is the
closest existing prior art for a Linus Worker handoff artifact.

**Phase 3 hybrid retrieval and parallel-agent coordination.** Wikidesk's runner-trait and sync protocol is the reference
for queued, bounded-concurrency research subtasks. Synthadoc's decomposition agent is the reference for fan-out query
execution. Both should be read before Phase 3 architecture is designed.

**Phase 7 skills graduation.** OmegaWiki's 24 SKILL.md files are the mandatory pre-read. Synthadoc's `BaseSkill`
hot-load registry is the implementation template. The delta between OmegaWiki's full lifecycle (paper through rebuttal)
and link's minimal tool surface (five MCP verbs) defines the Phase 7 planning space.

---

## Open questions for Dan

**Claim typing as a hard invariant or a lint warning?** TheKnowledge's validator hard-rejects writes missing a citation
link. Wikiloom's human-edit protection is enforced by convention plus commit prefix. The security synthesis argues claim
typing is the difference between a KB that earns trust over time and one that silently corrodes it. The question is
whether Phase 2 should adopt TheKnowledge's strict enforcement — which means Workers producing exploratory drafts need
an explicit `--draft` flag — or start with lint warnings and tighten later. Earlier is cheaper; retrofitting after
thousands of pages are indexed is not.

**Single KB endpoint or one per subcorpus?** Six siblings enforce "one workspace = one MCP server instance" (llmwiki is
explicit about this; synthadoc runs separate processes on separate ports per wiki root). Linus's `context/` spans
papers, notes, threads, and books. A single KB endpoint means one MCP entry for everything; separate endpoints mean
explicit agent scope but four entries in `.claude/settings.json`. This decision shapes the Phase 2 tool surface before
the first line of KB code is written.

**Operations registry adoption.** Llmbase's `Operation` dataclass is a near-drop-in for the "one definition, three
surfaces" tool registry Linus needs in Phase 2a. The alternative is a Linus-native abstraction designed from scratch to
better fit the Maestro/Worker delegation model (e.g., an Operation carries an autonomy tier from SAFETY.md, not just a
writes flag). Which direction: lift llmbase's proven contract, or design around Linus's specific constraints? _Partially
resolved (DEC-0018, DEC-0045, see [answered-questions.md](../../questions/answered-questions.md)): MCP adopted as
extensibility substrate; fastmcp's decorator API is the in-house Linus server pattern. The specific shape of the Phase
2a tool registry (whether to lift llmbase's `Operation` dataclass or design a Linus-native abstraction with
autonomy-tier fields) remains open — see R2-01 in top-questions.md._

**Wiki-compilation layer or RAG-only?** Every sibling builds a compiled wiki over the raw corpus and argues it is more
useful than RAG-on-raw-PDFs for compounding research knowledge. KnowledgeBase today is RAG-as-product. Is there appetite
for an LLM-maintained markdown wiki layer on top of KnowledgeBase in Phase 3, or does the corpus stay query-only with
provenance via content-hashed citations? The community's unanimous answer is "compile" but the community has not tried
it on academic biochemistry/genomics papers with table-heavy data sections.

**G3 cross-check on provenance depth.** _Resolved (2026-05-08):_ The G3 synthesis
(`docs/syntheses/repo-clusters/g3-wiki-patterns.md`) is now available and confirms no G3 repo achieved chunk-level
hashing plus claim-type typing plus citation enforcement simultaneously. The wikiloom + TheKnowledge combination remains
the primary provenance reference for the 18-repo cohort. G3's most relevant provenance contribution is
obsidian-llm-wiki-local's SHA-256 hashing with atomic-rename writes, which is chunk-level-adjacent but stops short of
per-claim typing and citation enforcement at write time.

---

_Update this document when the Phase 2 KB schema spec lands and when Phase 3 parallel-agent write coordination design
begins. G3 cross-check is now complete (2026-05-08). Primary inputs: `docs/repo-notes/` for all eleven repos;
`docs/syntheses/llm-wiki-synthesis.md`; `docs/syntheses/memory-synthesis.md`;
`docs/syntheses/repo-clusters/g3-wiki-patterns.md`; Crossing 3 of `docs/landscapes/total-landscape.md`._
