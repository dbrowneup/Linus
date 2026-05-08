# TheKnowledge (`badwally/TheKnowledge`)

## 1. Purpose and scope

TheKnowledge is a personal canonical knowledge base implementing Karpathy's LLM Wiki gist (`442a6bf...`) as a
citation-graph-enforced markdown vault under `~/code/knowledge/`, with a deliberate three-layer split: the wiki itself
is canonical (markdown + YAML frontmatter under `wiki/` and `raw/`), NotebookLM is the heavy-synthesis service called
_through_ a gateway (briefings, audio overviews, slide decks) and every NotebookLM artifact is filed back to the vault
with bidirectional links, and Obsidian is the visualization engine on top. A Python `wiki` CLI (entrypoint
`gateway.cli:main`) plus an MCP server (`gateway/mcp_server.py`) expose every gateway operation. The validator hard-
rejects any wiki claim missing a `[[sources/<id>]]` citation. Of the eleven siblings in the LLM-Wiki engine cohort, this
is the most opinionated about provenance (mechanical citation enforcement) and by far the broadest about source ingest —
PDF, Word, Excel, PowerPoint, CSV, image (Claude vision), voice memo, audiobook, URL, YouTube, arXiv, PubMed, Apple
Notes, with Notion/Slack/Gmail pollers queued.

## 2. Architecture summary

A single Python 3.11+ package (`knowledge-gateway`, `src/gateway/`) sitting between the human/agent and the on-disk
vault. The gateway is the only sanctioned writer: direct edits to `wiki/` or `raw/` are caught by the validator and
git-diff review, and a pre-commit hook blocks raw `nlm` invocations from sneaking into committed content. Sources land
in `raw/<type>/<id>.md` as canonical markdown plus optional binary sidecars; the LLM-authored layer lives in
`wiki/{entities,concepts,sources,synthesis,mocs,artifacts}/`. Converters live one-per-type under `gateway/converters/`
(arxiv, pubmed, youtube, web, pdf, docx, xlsx, pptx, csv, image, voice, audiobook) — six steps to add a new one,
documented in `CLAUDE.md`. Pollers under `gateway/pollers/` (`apple_notes.py` ships) cover API-only sources via a
parallel contract. NotebookLM access is mediated by `gateway/nlm_client.py`: an `NlmClient` Protocol with a real
`NlmCLIClient` that shells out to the third-party `nlm` CLI (`notebook create`, `add url|text`,
`slides|audio|report create`, `download`) and a mock for tests; the gateway wraps every artifact creation with
frontmatter that links back to the source notebook URL. Image ingest goes through `gateway/vlm.py`'s
`ClaudeCLIVLMClient` (shells out to `claude -p`) producing structured Overview / Visible-text / Key-elements /
Domain-content sections. Voice/audiobook transcription uses `mlx-whisper` plus `pyannote.audio` 3.x speaker diarization
on Apple Silicon (optional `[whisper]` extra; pinned with care — `huggingface_hub<1.0`, `torchaudio<2.5` — for known
compat traps). Operational integrations: `scripts/install_watcher.sh` installs a launchd agent that auto-ingests
`raw/inbox/`; `scripts/install_mcp.sh` registers `wiki_*` tools in `~/.claude/mcp_servers.json` so any other Claude Code
project can cite into the vault. Lookup-before- create is enforced by slug-similarity checks; an example bank and
`wiki finetune` distill domain filter policies as the corpus grows.

## 3. What's reusable in Linus

The Phase 2 KnowledgeBase pillar gets the most leverage. Three patterns transfer almost unchanged. First, the
gateway-as-only-writer discipline: every mutation goes through one Python entrypoint that runs frontmatter validation,
slug-collision checks, citation-graph enforcement, and event logging to `log.md` — exactly the surface Linus's KB needs
in Phase 2a so that Cline, Claude Code, openclaw, and the future native UI all see the same invariants. Second, the
converter and poller plug-in contracts (six-step add for converters, `Poller` subclass for API-only sources) are a clean
drop-in for Linus's planned multi-source ingest of `context/papers`, `context/notes`, `context/threads`, and
`context/books`. Third, the `NlmClient` Protocol is a textbook example of how to wrap a flaky third-party CLI behind a
typed seam with a mock for tests — directly applicable to anywhere Linus shells out (Ollama, pmetal, future Linus
fine-tunes). The MCP server in `gateway/mcp_server.py` is a small, focused surface (one tool per gateway op) — closer in
spirit to llmwiki's five-tool `guide/search/read/write/delete` than to pmetal-mcp's 45.

Compared to the ten siblings in this group: where `llmwiki` (lucasastorian) bets on filesystem-as-truth + SQLite FTS5 +
a Next.js reader, and `wikidesk` / `link` / `llmwiki-cli` lean toward leaner CLI/desktop variants, **TheKnowledge is the
only sibling whose architecture explicitly outsources whole-corpus synthesis to a third-party heavy service (NotebookLM)
while keeping the local vault canonical** — `nlm-briefing`, `nlm-audio`, `nlm-slides`, `nlm-revise`. The multi-format
ingest scope (13 source types, including Office formats, images via vision, audiobooks with diarization, and Apple Notes
via JXA) is also broader than any sibling I've seen, and the citation validator is the strictest of the cohort —
`--draft` is the only escape hatch and drafts older than 7 days get flagged.

## 4. What's inspiration only

The NotebookLM integration itself is inspiration, not a port. NotebookLM is a hosted Google service — Linus's whole
point is private/offline operation, so wiring `wiki nlm-*` directly into Linus would violate the north star.
Architecturally interesting (synthesis-as-a-service behind a gateway, artifacts file back to canonical storage), and the
_pattern_ is reusable for routing heavy synthesis to an MLX worker or hosted Claude under user control, but the specific
NotebookLM coupling stays study material. The `wiki finetune` example-bank distillation is a nice prior art for Phase 7
skills graduation but isn't wired to anything Linus has yet. The Obsidian-as-visualizer choice is a deliberate non-goal
for Linus (Streamlit in Phase 2, openclaw later, native UI in Phase 8); the wikilink format is worth preserving for
cross-tool legibility, but Linus does not need to ship an Obsidian vault.

## 5. What's incompatible or out of scope

Hard dependence on the `nlm` CLI (third-party `notebooklm-mcp-cli`) and on the user's NotebookLM account makes the
NotebookLM half non-portable to a fully-local Linus. The Claude-vision image converter shells out to the `claude` CLI
and consumes hosted Claude tokens — fine for Dan's Maestro budget but not "no paid APIs required" Worker work. The
`wiki batch-ingest` migrator is shaped specifically for the author's prior Obsidian research-notebook layout
(`~/code/research-notebook/data/obsidian*/`) and would need rework for Dan's `context/` tree. Vector / BM25 search is
explicitly deferred until ~10k pages — KnowledgeBase already has a richer retrieval stack, so Linus's KB layer should
not regress to markdown-only search. Single-user vault assumptions throughout (`.knowledge/` runtime state, file-lock
file, watcher PID) are fine for Dan but bake in single-machine semantics that don't generalize to the Phase 8 "beyond
MacBook" world.

## 6. Recommendation: **Study**

Read `gateway/cli.py`, `gateway/validator.py`, `gateway/nlm_client.py`, `gateway/converters/{image,voice,audiobook}.py`,
`gateway/pollers/apple_notes.py`, and the top of `WIKI.md` — perhaps 2000 lines total and most of the design. Lift the
gateway-as-only-writer discipline, the converter/poller plug-in contract, and the typed-client-with-mock seam into
Linus's Phase 2 KB. Do not vendor or fork; the NotebookLM coupling and the Obsidian assumption make a direct adoption
the wrong shape for Linus. After the Phase 2 KB v1 spec lands, revisit whether TheKnowledge's strict-citation validator
should be ported as a hard invariant on Linus-authored synthesis pages — it's the most defensible answer to
hallucination drift I've seen in this cohort.

## 7. Questions for Dan

1. **NotebookLM-shaped slot in Linus.** TheKnowledge treats NotebookLM as "the heavy-synthesis service behind the
   gateway." Linus has a directly analogous slot: a heavy-synthesis worker that's not the chat-loop model. Should that
   slot in Phase 3 be a larger MLX model running locally, hosted Claude under explicit user invocation, or both behind a
   `synthesis-backend` ADR?
2. **Citation-as-hard-invariant.** TheKnowledge's validator rejects any claim lacking `[[sources/<id>]]`. Worth porting
   as a Phase 2 KB invariant on Linus-authored synthesis pages, or kept as a lint warning so Workers can produce
   exploratory drafts cheaply?
3. **Converter scope for Phase 2.** TheKnowledge ships 13 source-type converters. Dan's `context/` today is mostly PDFs
   and notes — is the right Phase 2 scope just `pdf` + `note` + `web`, with audiobook/voice/image deferred to Phase 4
   data sovereignty, or does the breadth matter from day one?
4. **Gateway pattern vs. KnowledgeBase APIs.** KnowledgeBase already exposes Python APIs. Should Linus's KB tools call
   KnowledgeBase directly, or wrap KnowledgeBase behind a TheKnowledge-style gateway so MCP, validator, and audit log
   are uniform across all writers?
5. **Differentiator confidence.** I read TheKnowledge's code in depth and only the group framing for nine of the ten
   siblings (plus `llmwiki` from the prior note). The "NotebookLM behind a gateway" angle reads as genuinely unique in
   the cohort, but it's worth confirming once `OmegaWiki`, `wikiloom`, `wikimind`, and the others have notes — none of
   them sound like they share that bet, but I haven't verified.
