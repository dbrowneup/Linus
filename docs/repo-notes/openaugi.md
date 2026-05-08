# openaugi (`bitsofchris/openaugi`)

## 1. Purpose and scope

OpenAugi (Chris Lovejoy / "bitsofchris", MIT, alpha v0.1.0, Python 3.12+) is a self-hostable "personal intelligence
engine" that ingests an Obsidian vault, splits notes by heading, embeds and indexes the pieces in a single SQLite file,
and exposes the result to Claude as an MCP server. The pitch — "one pip install, one SQLite file, one MCP server" — is
the cleanest one-line statement of exactly the v0 substrate Dan committed to in DEC-0029 (SQLite + content hashes; git
left to the orchestration layer). It was named in the Phase 1 skills-synthesis retrieval/memory reference list, and sits
in the Layer-C cross-session episodic memory group alongside `agentmemory`, `anamnesis`, `memex`, `engram`, `remember`,
`omega-memory`, `prompt-vault`. Within that group OpenAugi is the most rigorous distillation of "context engineering as
index design" — the codebase is small (a couple dozen modules, ~2k lines for the two most consequential files) and the
design choices are unusually well documented.

## 2. Architecture summary

Two SQL tables and one virtual table, no more.
`blocks(id, kind, content, summary, embedding, source, title, tags, block_time, occurred_at, metadata, content_hash, ingested_at)`
holds every node — documents, splits, tags, generated "context blocks" — discriminated by `kind`
(`context_block:document`, `data_block`, `context_block:tag`, `context_block:cluster`).
`links(from_id, to_id, kind, weight, metadata)` with composite PK `(from_id, to_id, kind)` holds typed edges
(`contains`, `groups`, `links_to`, `summarizes`). FTS5 (`blocks_fts`) is wired with insert/update/ delete triggers;
sqlite-vec's `vec0` virtual table holds normalized embeddings so L2 == cosine; WAL mode lets the MCP read while the file
watcher writes. Block IDs are deterministic `hash(source_path + content_hash)` — the same addressability+integrity
pattern DEC-0029 specifies. The pipeline (`pipeline/runner.py` orchestrator, `adapters/ vault.py` Obsidian splitter,
`pipeline/embed.py` step, `pipeline/cluster.py` HDBSCAN at multiple embedding dimensionalities, `pipeline/dispatch.py`
"zzz instructions → task files", `agents/task_watcher.py` task files → named tmux Claude Code sessions) is incremental
and content-hash-keyed. The MCP server (`mcp/server.py`, ~17 tools) exposes five retrieval modes — semantic (sqlite-vec
KNN), keyword (FTS5), graph (`get_related`, `traverse`), temporal (`recent`), direct (`get_block`, `get_blocks`) — plus
a `get_context` combinator that does 3× over-fetch with cosine-grouped dedup and MMR re-ranking, and write tools
(`write_document`, `write_thread`, `write_snip`, `tag_block`) that round-trip back into the vault. Embedding providers
are pluggable: local `sentence-transformers` by default, optional OpenAI or Ollama via extras.

## 3. What's reusable in Linus

The schema is the prize, and it lines up with DEC-0029 with almost no friction. Garrison's four sub-requirements all
have a clean home: addressability via `blocks.id` derived from `content_hash`, disambiguation via
`(content_hash, source)`, temporal order via `block_time` + `ingested_at`, integrity via the content-hash itself plus
the SQLite WAL journal. Phase 2 episodic memory could import this two-table layout almost verbatim, with `kind` extended
(`scratchpad`, `tool_output`, `answer` per DEC-0030, plus the `context_block:*` family for compiled summaries).
sqlite-vec + FTS5 in one file removes the need for Qdrant for v0 — a real Algorithm-step-1 deletion candidate worth
considering. The `get_context` MCP tool's overfetch-→-dedup-→-MMR-→-link-expansion pattern is small, well-isolated, and
a strong starting template for Linus's Phase 3 retrieval combinator. The hub-score SQL (logs of inbound/outbound link
counts plus entry counts, computed at query time, no stored table) is a free Phase 3 signal. Compared to **memex** —
also a vault-as-knowledge-graph sibling — OpenAugi is _machine-readable_ (typed graph in SQLite that an agent queries
through tools) where memex is _agent-readable_ (governed markdown wiki the agent reads as files under constitutional
rules); OpenAugi gives Linus a substrate, memex gives Linus a discipline, and the two compose. Compared to **remember**
— also Obsidian-compatible — OpenAugi owns the index (it computes embeddings, hubs, clusters, and exposes them via MCP)
where remember is a thin organizational schema on top of plain markdown driven by slash-commands; remember is closer to
a productivity plugin, OpenAugi is closer to the Phase 2 episodic substrate itself.

## 4. What's inspiration only

The HDBSCAN multi-pass clustering (`pipeline/cluster.py`) — coarse pass at dim-64 for "life areas," fine pass within
each area for recurring ideas, cross-domain pass for non-obvious connections — is interesting but Phase 4+ at the
earliest; v0 doesn't need clusters to be useful. The `zzz: <instruction>` dispatch pattern (write a marker in any note,
the watcher launches a Claude Code agent in a named tmux session) is a clever Obsidian-native UX but it's a workflow
choice, not a memory primitive — Linus's Maestro/Worker dispatch path is independent. The Cloudflare-Tunnel remote-
access doc and the auth/JWT module are out of scope for a local-only Linus.

## 5. What's incompatible or out of scope

OpenAugi is Obsidian-vault-shaped. Splitter heuristics, `[[wikilink]]` extraction, `OpenAugi/` subfolder conventions,
the round-trip writers all assume markdown notes in a vault. Linus's episodic memory holds turn-tagged scratchpad +
answer + tool_output records, which are not Obsidian notes; the schema generalizes, the ingest pipeline does not. Status
is alpha v0.1.0 — vendoring as a library means absorbing alpha churn; Linus should **lift the schema and tool shapes**,
not depend on the package. The codebase reaches for an `openai` API key for embeddings/LLM as the documented-default
upgrade path; Linus's Phase 2 commitment is local-first via Ollama, so OpenAugi's optional `[ollama]` extra is the
relevant entry point and the `[openai]` defaults should not be read as "what good looks like." Finally, no `git`
integration: DEC-0029's git-as-persistence layer is Linus's job, not OpenAugi's.

## 6. Recommendation: **Study**

Read `data-model.md`, `store/sqlite.py` (especially the DDL, FTS triggers, and indexes through line 120), and the
`get_context` implementation in `mcp/server.py`. Lift the two-table schema as the starting point for the DEC-0029 v0
SQLite substrate; lift the deterministic `hash(source + content_hash)` ID convention; lift `get_context`'s overfetch+
dedup+MMR+link-expansion shape into Linus's Phase 3 retrieval combinator. Do not vendor; do not depend; do not import
the Obsidian ingest pipeline. Revisit OpenAugi's `pipeline/cluster.py` in Phase 4 when navigability over months of
episodic records starts mattering.

## 7. Questions for Dan

1. **Schema lift, verbatim or extended?** OpenAugi's `(blocks, links)` schema covers DEC-0029's addressability/
   disambiguation/temporal/integrity needs cleanly. Adopt the column set verbatim and add `session_id`, `turn_id`,
   `parent_turn_id`, `segment`, `trust_level` as new columns on `blocks`, or rename to `episodes` + `episode_links` to
   make the ownership boundary obvious from schema names alone? _Partially resolved (DEC-0029, see
   [answered-questions.md](../questions/answered-questions.md)): SQLite + content hashes + git confirmed as v0 episodic
   substrate; detailed schema columns deferred to Phase 2 memory-architecture.md spec._
2. **sqlite-vec instead of Qdrant for v0.** OpenAugi runs FTS5 + sqlite-vec inside the same file as the source-of-truth
   table, which deletes a service from the architecture. Worth re-opening the v0 Qdrant decision in light of this, or is
   the Qdrant choice already locked for reasons orthogonal to substrate-count (e.g., HNSW perf, multi-tenant scoping)?
   _Partially resolved (DEC-0029, see [answered-questions.md](../questions/answered-questions.md)): DEC-0029 commits to
   SQLite for the episodic layer (Layer C); Qdrant remains the KB vector store; the two stores serve different layers
   and are not directly competing._
3. **OpenAugi vs memex split.** OpenAugi gives a typed graph an agent queries through tools; memex gives a governed
   markdown wiki an agent reads as files. These are complementary, not competitive — OpenAugi as Layer C substrate,
   memex as the cross-session "constitution" layer over project artifacts. Want this articulated as an ADR before Phase
   2a, or leave it implicit until both prove out?
4. **Context-block kind in the schema.** OpenAugi makes "compiled navigational metadata" a first-class block kind
   (`context_block:cluster`, hub summaries, concept pages). Linus's spec doesn't yet name an equivalent — should the
   Phase 2 schema reserve a `kind="context_block:*"` family up front, or is that premature before Phase 3 retrieval
   patterns crystallize?
5. **`get_context` as Linus's default retrieval verb.** OpenAugi collapses semantic+keyword+dedup+MMR+link-expansion
   into one tool with sensible defaults. Adopt that as the Linus Phase 3 retrieval entry point, or expose the five modes
   individually and let the Worker compose?
