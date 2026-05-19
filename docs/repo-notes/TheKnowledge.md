# TheKnowledge (`badwally/TheKnowledge`)

_Refreshed 2026-05-18 against upstream HEAD 4227ad0; 117 commits / 2169 files reviewed (M37-M45 substrate growth)._

## 1. Purpose and scope

TheKnowledge is a personal canonical knowledge base implementing Karpathy's LLM Wiki gist (`442a6bf...`) as a
citation-graph-enforced markdown vault under `~/code/knowledge/`, with a deliberate three-layer split: the wiki itself
is canonical (markdown + YAML frontmatter under `wiki/` and `raw/`), NotebookLM is the heavy-synthesis service called
_through_ a gateway (briefings, audio overviews, slide decks) and every NotebookLM artifact is filed back to the vault
with bidirectional links, and Obsidian is the visualization engine on top. A Python `wiki` CLI (entrypoint
`gateway.cli:main`), an MCP server (`gateway/mcp_server.py`), and — new since the prior note — a `wiki serve` FastAPI +
React/Vite/TS web UI at `localhost:7474` expose every gateway operation. The validator hard-rejects any wiki claim
missing a `[[sources/<id>]]` citation; drafts (`--draft`) downgrade the rule to a lint warning until `wiki finalize`
runs, and drafts older than 7 days are flagged. Of the eleven siblings in the LLM-Wiki engine cohort, this is the most
opinionated about provenance (mechanical citation enforcement) and by far the broadest about source ingest — PDF, Word,
Excel, PowerPoint, CSV, image (Claude vision), voice memo, audiobook, URL, YouTube, arXiv, PubMed, Apple Notes, with
Notion/Slack/Gmail pollers queued.

## 2. Architecture summary

A single Python 3.11+ package (`knowledge-gateway`, `src/gateway/`) sitting between the human/agent and the on-disk
vault. The gateway is the only sanctioned writer: direct edits to `wiki/` or `raw/` are caught by the validator and
git-diff review, and a pre-commit hook blocks raw `nlm` invocations from sneaking into committed content. Sources land
in `raw/<type>/<id>.md` as canonical markdown plus optional binary sidecars; the LLM-authored layer lives in
`wiki/{entities,concepts,sources,synthesis,mocs,proposals,artifacts}/`. Converters live one-per-type under
`gateway/converters/` (arxiv, pubmed, youtube, web, pdf, docx, xlsx, pptx, csv, image, voice, audiobook) — six steps to
add a new one, documented in `CLAUDE.md`. Pollers under `gateway/pollers/` (`apple_notes.py` ships; Notion/Slack/Gmail
queued) cover API-only sources via a parallel contract. NotebookLM access is mediated by `gateway/nlm_client.py` with
real/mock implementations and a `wiki nlm-sync` bulk uploader. Image ingest uses `gateway/vlm.py`'s `ClaudeCLIVLMClient`;
voice/audiobook uses `mlx-whisper` + `pyannote.audio` 3.x diarization. Three substrates landed after the prior note that
materially change the architectural surface: (1) **`gateway/research/`** — a multi-adapter research orchestrator (`wiki
research`) with per-adapter query planning, a Semantic Scholar adapter with citation-graph traversal, persistent
per-session plan storage, and an `AuthorshipReport` plumbed end-to-end (created/updated/contradictions tallies); (2)
**`gateway/lint/`** — 13 lint scopes including `citation_chains`, `citation_density`, `contradictions`,
`filter_calibration`, `missing_pages`, `orphans`, `schema_drift`, `stale_claims`, `stale_drafts`, `untagged_sources`,
and `inbox_pending` / `nlm_pending`, all walkable via `wiki lint --scope <check>`; (3) **`gateway/web/` + `web/` (Vite +
React 18 + TS)** — a FastAPI scaffold (M40) with async/sync ops endpoints, in-memory `TaskStore` for long-running
operations, and SPA routes covering Dashboard, every per-source operation, Research (sessions + plan editor + 3s log-
polled progress), Review (drafts/contradictions/orphans/filter-band tabs with inline finalize/abandon and severity
badges), and per-domain Artifacts pages with confirmation modals on every LLM-calling op. `wiki bootstrap-domain` (M39)
enables top-down green-field policy authorship; `wiki discover-domains` / `promote-domain` / `demote-domain` /
`reject-proposal` cover the bottom-up proposal lifecycle. Authorship-level contradictions are now persisted to
`.knowledge/contradictions/log.jsonl`. Operational integrations: `scripts/install_watcher.sh` installs a launchd agent
that auto-ingests `raw/inbox/`; `scripts/install_mcp.sh` registers `wiki_*` tools in `~/.claude/mcp_servers.json`.

## 3. What's reusable in Linus

The Phase 2 KnowledgeBase pillar gets even more leverage than the prior note flagged. Four patterns transfer almost
unchanged. First, the gateway-as-only-writer discipline: every mutation goes through one Python entrypoint that runs
frontmatter validation, slug-collision checks, citation-graph enforcement, and event logging to `log.md` — exactly the
surface Linus's KB needs in Phase 2a so that Cline, Claude Code, openclaw, and the future native UI all see the same
invariants. Second, the converter and poller plug-in contracts (six-step add for converters, `Poller` subclass for
API-only sources) are a clean drop-in for Linus's planned multi-source ingest of `context/papers`, `context/notes`,
`context/threads`, and `context/books`. Third, the `NlmClient` Protocol is a textbook example of how to wrap a flaky
third-party CLI behind a typed seam with a mock for tests. Fourth — new since the prior note — the **`wiki serve`
FastAPI + React scaffold** is a credible reference shape for Linus's Phase 2 chat UI: in-memory `TaskStore` for
long-running ops, polling-based progress in the SPA, confirmation modals on every cost-sensitive (LLM) operation, and
SPA-served-by-FastAPI (no separate dev server in production). The MCP server in `gateway/mcp_server.py` remains a
small, focused surface, and the new `gateway/research/` orchestrator pattern (multi-adapter query expansion + structured
plan storage + per-session progress via `log.md` parsing) is prior art if Linus's Phase 3 agent fan-out wants similar
session-scoped observability.

Compared to the ten siblings in this group: where `llmwiki` (lucasastorian) bets on filesystem-as-truth + SQLite FTS5 +
a Next.js reader, and `wikidesk` / `link` / `llmwiki-cli` lean toward leaner CLI/desktop variants, **TheKnowledge is
still the only sibling whose architecture explicitly outsources whole-corpus synthesis to a third-party heavy service
(NotebookLM) while keeping the local vault canonical** — `nlm-briefing`, `nlm-audio`, `nlm-slides`, `nlm-revise`,
`nlm-sync`. The multi-format ingest scope (13 source types, including Office formats, images via vision, audiobooks
with diarization, and Apple Notes via JXA) is also broader than any sibling, and the citation validator remains the
strictest of the cohort. The **citation validator is still the high-priority lift candidate** the prior note flagged —
the v1 code is intact at `src/gateway/validator.py` + `src/gateway/citations.py`, refined since the prior note (M6
content-hash and immutability checks, M42 contradictions persistence) but not architecturally rewritten.

## 4. What's inspiration only

The NotebookLM integration itself is inspiration, not a port. NotebookLM is a hosted Google service — Linus's whole
point is private/offline operation, so wiring `wiki nlm-*` directly into Linus would violate the north star.
Architecturally interesting (synthesis-as-a-service behind a gateway, artifacts file back to canonical storage,
`nlm-sync` bulk-uploads raw sources by domain), and the _pattern_ is reusable for routing heavy synthesis to an MLX
worker or hosted Claude under user control, but the specific NotebookLM coupling stays study material. The `wiki
finetune` example-bank distillation is a nice prior art for Phase 7 skills graduation but isn't wired to anything Linus
has yet. The Obsidian-as-visualizer choice is a deliberate non-goal for Linus (Streamlit in Phase 2, openclaw later,
native UI in Phase 8); the wikilink format is worth preserving for cross-tool legibility, but Linus does not need to
ship an Obsidian vault. The new web UI's React/Vite/TS stack is a useful shape reference but not necessarily Linus's
choice — Phase 2's Streamlit baseline is faster to ship and reaches openclaw later anyway.

## 5. What's incompatible or out of scope

Hard dependence on the `nlm` CLI (third-party `notebooklm-mcp-cli`) and on the user's NotebookLM account makes the
NotebookLM half non-portable to a fully-local Linus. The Claude-vision image converter shells out to the `claude` CLI
and consumes hosted Claude tokens — fine for Dan's Maestro budget but not "no paid APIs required" Worker work. The
`wiki batch-ingest` migrator is shaped specifically for the author's prior Obsidian research-notebook layout
(`~/code/research-notebook/data/obsidian*/`) and would need rework for Dan's `context/` tree. Vector / BM25 search is
still explicitly deferred until ~10k pages — KnowledgeBase already has a richer retrieval stack, so Linus's KB layer
should not regress to markdown-only search. Single-user vault assumptions throughout (`.knowledge/` runtime state,
file-lock file, watcher PID, in-memory `TaskStore`) are fine for Dan but bake in single-machine semantics that don't
generalize to the Phase 8 "beyond MacBook" world.

## 6. Recommendation: **Study**

No verdict change. The substantial M37-M45 substrate growth (research orchestrator, lint surface, web UI, domain
proposals, contradictions detection) makes TheKnowledge an even richer reference but doesn't change the
NotebookLM-coupling / Obsidian-assumption / single-user shape that argued against direct adoption in the prior note.
Read `gateway/cli.py`, `gateway/validator.py`, `gateway/citations.py`, `gateway/nlm_client.py`,
`gateway/converters/{image,voice,audiobook}.py`, `gateway/pollers/apple_notes.py`, `gateway/research/orchestrator.py`,
and the FastAPI scaffold at `gateway/web/` plus the top of `WIKI.md` — perhaps 3000 lines total and most of the design.
Lift the gateway-as-only-writer discipline, the converter/poller plug-in contract, the typed-client-with-mock seam, and
the **strict-citation validator as a hard invariant on Linus-authored synthesis pages** — the validator code at
`src/gateway/validator.py` + `src/gateway/citations.py` is the most defensible answer to hallucination drift in this
cohort and remains the highest-priority lift target for Linus's Phase 2 KB. Do not vendor or fork; the NotebookLM
coupling and the Obsidian assumption make a direct adoption the wrong shape for Linus.

## 7. Questions for Dan

1. **NotebookLM-shaped slot in Linus.** TheKnowledge treats NotebookLM as "the heavy-synthesis service behind the
   gateway." Linus has a directly analogous slot: a heavy-synthesis worker that's not the chat-loop model. Should that
   slot in Phase 3 be a larger MLX model running locally, hosted Claude under explicit user invocation, or both behind a
   `synthesis-backend` ADR?
2. **Citation-as-hard-invariant.** TheKnowledge's validator rejects any claim lacking `[[sources/<id>]]`. Worth porting
   as a Phase 2 KB invariant on Linus-authored synthesis pages, or kept as a lint warning so Workers can produce
   exploratory drafts cheaply? The 2026-05 refresh confirms the validator code is mature, refined (M6 content-hash + M42
   contradictions log), and a clean lift target.
3. **Converter scope for Phase 2.** TheKnowledge ships 13 source-type converters. Dan's `context/` today is mostly PDFs
   and notes — is the right Phase 2 scope just `pdf` + `note` + `web`, with audiobook/voice/image deferred to Phase 4
   data sovereignty, or does the breadth matter from day one?
4. **Gateway pattern vs. KnowledgeBase APIs.** KnowledgeBase already exposes Python APIs. Should Linus's KB tools call
   KnowledgeBase directly, or wrap KnowledgeBase behind a TheKnowledge-style gateway so MCP, validator, and audit log
   are uniform across all writers?
5. **Research orchestrator pattern for Phase 3.** TheKnowledge's `gateway/research/` shows a per-adapter query planner,
   persistent session storage, Semantic Scholar citation-graph traversal, and a structured plan editor. Should Linus's
   Phase 3 agent fan-out adopt this shape (sessions + plans + per-step `log.md` progress) or stay closer to the workgraph
   JSONL substrate already recommended in the G7 synthesis?
