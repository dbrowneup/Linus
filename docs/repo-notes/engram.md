# engram (`emipanelliok/engram`)

## 1. Purpose and scope

Engram is a Python CLI (PyPI: `engram-wiki`, MIT, Alpha) that gives a coding agent a persistent, plain-markdown wiki it
writes and grooms itself. The pitch is "Not RAG. Not embeddings. A real wiki — built and maintained by your AI agent,"
and the README cites Karpathy's LLM Wiki gist and Vannevar Bush's Memex as direct ancestors. The surface is six verbs:
`save`, `ingest`, `query`, `lint`, `compress`, `forget`, all `--json`-friendly for agent piping. Storage is one
directory (`~/.engram` or per-project `.engram/`) holding `sources/raw/`, `wiki/*.md`, an append-only `log.md`, and
`engram.toml`. LLM providers are Claude, OpenAI, and Ollama via a thin `LLMClient` factory. Despite the name it sits on
the wiki/semantic side of the agent-memory landscape, not the episodic side — a meaningful boundary distinction for the
Linus memory pillar (DEC-0028 through DEC-0043).

## 2. Architecture summary

Three thin layers under `src/engram/`. The `wiki/` layer (`store.py`, `article.py`) owns the filesystem: each article is
a markdown file with a YAML-ish header (slug, title, tags, sources, timestamps), and `WikiStore.search()` is a literal
keyword-and-tag scorer (title 3, tag 2, body 1) — no embeddings, no vector DB, not even BM25. The `core/` layer holds
the six operations. `save_memory` reads the current `index.md` plus the top-N keyword hits, hands them to the LLM with a
system prompt instructing it to either create a new article or update an existing one, parses a strict Pydantic response
(`parse_article_response`), and writes the file. `query_wiki` is the symmetric read path: keyword-rank, take top-K, ask
the LLM to answer using only those articles. `compress_wiki` triggers when article count or total KB exceeds
configurable hot thresholds: it groups articles by primary tag, asks the LLM to merge each group, snapshots a backup
under `backups/<timestamp>/` first, and replaces the originals atomically. `lint_wiki` ships the whole corpus (truncated
at 40k chars) to the LLM with a strict-schema prompt asking for
`contradiction | stale | missing_xref | stub | orphan | duplicate` issues. The `llm/` layer is a
`complete(system, user)` interface with three concrete clients. The `sources/` layer (`url.py`, `text.py`) handles
`ingest` with SSRF guards (private-network blocks) and BeautifulSoup→markdown conversion for HTML. Path traversal is
defended at the `WikiStore._validate_slug` level with an `^[a-z0-9][a-z0-9\-] {0,79}$` regex plus a resolved-path
containment check. The whole codebase is small, ~300 LOC of core, ~700 LOC total including tests.

## 3. What's reusable in Linus

The shape that matters for Linus is **write-time synthesis**: the LLM does the work on `save`, not on every `query`.
That maps onto Layer E (semantic / KnowledgeBase) of the Garrison decomposition in
[memory-architecture.md](../specs/memory-architecture.md), not Layer C (episodic) where DEC-0029's SQLite + content
hashes substrate lives. (Note: this layer was renamed from Layer D to Layer E per DEC-0052, when investigation memory
took the Layer D slot.) As prior art for the KB-spec items, three patterns are worth lifting: (a) the strict-Pydantic
LLM-response contract in `parse_article_response`/`parse_lint_response` — Linus's own LLM-mediated tools should validate
LLM output before acting on it, full stop; (b) the `compress` design — backup before destructive merge, group-by-tag,
guard against undersized LLM responses (`len < 20` skip, `len > 200_000` truncate) — the audit-log + git-as-persistence
discipline in DEC-0029 already covers the backup story but the threshold-driven trigger and the "skip-on-bad-response"
check are reusable; (c) the `lint` health-check verb itself — Linus's episodic store has no equivalent, and the
contradiction/stale/orphan taxonomy maps cleanly onto a Layer C maintenance pass that DEC-0039's roll-up consolidation
doesn't currently address.

## 4. What's inspiration only

The headline differentiator versus group siblings is **identity confusion, intentional**. PyPI name `engram-wiki` admits
it: this is a wiki engine wearing a memory-pillar hat. Compared to `agentmemory`/`mem0`-style episodic stores (which are
session-tagged event logs with vector recall), engram has no episode concept, no `session_id`, no recency decay, no
"what happened in the last conversation" recall mode. The `log.md` is chronological but is operator-facing audit, not a
recall surface. Compared to Group 2's LLM Wiki engines (`link`, `llmwiki`), engram is structurally the same animal —
markdown corpus + LLM-curated cross-references + simple search — with a strong opinion about being agent-driven rather
than human-driven. The keyword-only `search()` is the Karpathy gist's exact prescription ("Search: Simple keyword match
on markdown"), and the README's roadmap entry "Embeddings-enhanced search — Optional, for large wikis (100+ articles)"
concedes the obvious ceiling. For Linus this means engram's design is most useful as **inspiration for the KB
write-side**, not as a model for the DEC-0029 episodic substrate. The episodic siblings in this group will have the
recall patterns Linus actually needs.

## 5. What's incompatible or out of scope

Linus's KnowledgeBase is the Layer E substrate (DEC-0042; renumbered from Layer D per DEC-0052) and already has a
NetworkX + Qdrant pipeline; engram's
flat-files-plus-keyword approach is a step backward in retrieval power, and it has no notion of the KB's paper-corpus
structure. The compress-by-tag merge is destructive at the article level — fine when the wiki is the source of truth,
not fine when the wiki is a derived view over canonical sources, which is Linus's situation. The `lint`-the-whole-corpus
operation is O(corpus) per call and bounded at 40k chars — does not scale to KnowledgeBase volume. No MCP server yet (on
roadmap). Per-project `.engram/` directories overlap awkwardly with per-project tagging in DEC-0029's episodic schema —
two storage conventions for the same project axis is exactly the kind of thing The Algorithm says to delete one of.

## 6. Recommendation: **Study**

Read `core/save.py`, `core/compress.py`, `core/lint.py`, and `core/parsing.py` before authoring the KB write-side and
the episodic-store maintenance verbs. Lift the strict-Pydantic LLM response contract and the compress-with-backup
discipline. Do not adopt engram itself: wrong layer (semantic, not episodic), wrong storage shape for KnowledgeBase,
wrong scale ceiling. The 1-2 hours spent reading it pay off as KB-spec input, not as a runtime dependency.

## 7. Questions for Dan

- **Lint as a Layer C verb.** Engram's `lint` finds contradictions, stale entries, orphans across the corpus. The
  episodic spec has consolidation (DEC-0039) but no integrity pass. Is a periodic LLM-mediated "audit your own episodic
  store for contradictions" worth a DEC slot, or premature?
- **Write-time-synthesis vs. write-time-raw.** DEC-0029 stores raw turns + content hashes (write-time-raw). Engram does
  write-time-synthesis (LLM rewrites the corpus on every save). For the KB write side specifically — does Linus want
  ingestion to do engram-style synthesis into the KB, or stay raw-ingest with retrieval-time synthesis?
- **Differentiator confidence.** Within Group 4, engram is the clearest "wiki, not memory" outlier; the others
  (agentmemory, anamnesis, omega-memory, remember, prompt-vault, openaugi, memex) are presumably more episodic-shaped.
  Worth deferring final layer-C-substrate ADR refinements until the rest of the group is noted, in case one of them has
  a recall pattern that obsoletes part of DEC-0029?
