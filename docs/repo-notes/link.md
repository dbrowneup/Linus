# link (`gowtham0992/link`)

## 1. Purpose and scope

Link is a single-file, stdlib-only Python implementation of Karpathy's "LLM Wiki" pattern: drop sources into `raw/`,
have an LLM agent compile them into structured Wikipedia-style markdown pages under `wiki/`, and let the wiki compound
over time. It ships three artifacts in one repo — `link.py` (CLI for `demo`, `doctor`, `rebuild-backlinks`), `serve.py`
(local HTTP API + Wikipedia-style web viewer with a force-directed graph at `/graph`), and a separately-published PyPI
package `link-mcp` (registered on the official MCP Registry as `io.github.gowtham0992/link`) that exposes the wiki to
agents over MCP. Everything is local-first, MIT-licensed, no telemetry, no external API calls, no vector store, no
embedding model — pure Python stdlib plus the `mcp` SDK on the server side. For Linus this is the most "shippable today"
of the eleven sibling LLM-wiki engines and the closest fit to a Phase 2 KnowledgeBase companion.

## 2. Architecture summary

The wiki is just markdown files in a directory tree: `wiki/sources/`, `wiki/concepts/`, `wiki/entities/`,
`wiki/comparisons/`, `wiki/explorations/`, plus `index.md` (master catalog), `log.md` (append-only audit trail), and
`_backlinks.json` (auto-generated reverse + forward link index). The schema lives in `LINK.md` at repo root — a single
prose document instructing the LLM how to write pages with YAML frontmatter, confidence tags
(`[confidence: high/medium/low]`), wikilink cross-references, and a `maturity: seed | growing | mature | established`
lifecycle field per page. Search is an in-memory inverted token index built lazily on first request and invalidated by
mtime; ranking is hand-tuned (title 20pts, alias 8pts, tag 5pts, fulltext 2pts) — no embeddings, no ANN. The MCP server
in `mcp_package/link_mcp/server.py` is ~500 lines using `FastMCP` and exposes six tools — `search_wiki`, `get_context`
(the headline "topic + full graph neighborhood in one call"), `get_pages`, `get_backlinks`, `get_graph`,
`rebuild_backlinks`. `serve.py` re-exposes the same surface as a `127.0.0.1`-bound HTTP API. Integrations under
`integrations/` are bash installers that wire Link into Claude Code, Cursor, Codex, Copilot, VS Code, Kiro, and
Antigravity by dropping the `LINK.md` schema into the agent's session context and registering `link-mcp` in the relevant
MCP config — the explicit insight being that the agent itself is the maintenance loop.

## 3. What's reusable in Linus

The whole thing is small enough to read in an afternoon and dependency-light enough to vendor or run unmodified. The
most directly reusable artifact is the `LINK.md` schema — a battle-tested prompt for "you are the wiki maintainer" with
explicit page templates, confidence-tag conventions, and a maturity lifecycle. Linus's Phase 2 KnowledgeBase has the
same shape (papers as immutable sources, derived structured notes), and Link's `wiki/sources/` + `wiki/concepts/` split
maps cleanly onto KnowledgeBase's paper-vs-synthesis distinction. The `_backlinks.json` graph + `get_context` "page plus
neighborhood in one call" idiom is precisely the agent-optimized retrieval API the security synthesis gestures at when
it argues for claim-typing and content-hashed cross-references — Link doesn't content-hash, but the backlink format
would extend cleanly. The `doctor` command (orphans, dead links, stale `source_count` metadata, missing TLDRs, isolated
graph nodes, and a secrets-in-filenames/contents scan) is a lint pattern Linus's KnowledgeBase should copy verbatim.
Unlike `wikiloom` (git-as-substrate) or hypothetical sibling engines that bet on SQLite, Qdrant, or a custom binary
format, `link` keeps everything as plain markdown in a directory — meaning Obsidian opens the wiki as a vault for free
and Linus's KnowledgeBase corpus could in principle share the substrate without conversion.

## 4. What's inspiration only

Two things stay inspirational rather than adopted. First, `serve.py`'s web viewer with the force-directed `/graph` is a
nicely-built local Wikipedia clone, but Linus has Streamlit for Phase 2 chat UI and openclaw later — a second web UI
isn't worth maintaining. Second, the integration installer pattern (one bash script per agent harness, each writing into
the agent's config) is clever but redundant for Linus, which intends to own the harness-facing endpoint itself rather
than registering as a third-party tool in someone else's config. The ranked-by-token-overlap search is an honest
baseline but Linus's Phase 3 hybrid retrieval will want BM25 + dense embeddings + graph re-ranking; Link's search is a
fine starting point but not the destination. Compared to `link-mcp`, the sibling MCP-shipping engines in this group
differentiate mostly on storage substrate and agent-integration story — `link`'s choice of "PyPI-installable MCP server
pointing at a directory of markdown" is the most operationally simple of the bunch and the easiest to swap out later if
a sibling proves to have a better retrieval story.

## 5. What's incompatible or out of scope

Link assumes a single human curator and a single agent maintainer; there is no concept of multi-agent concurrent writes,
no locking on `wiki/index.md` or `_backlinks.json`, and the `log.md` audit trail is append-only-by-convention rather
than enforced. Phase 3 multi-agent fan-out would either need to serialize wiki writes through Linus's orchestration
layer or pick a different substrate. There is no notion of content-hashing or claim-level provenance beyond
`[confidence: high/medium/low]` strings and `*Source: [[source-page]]*` links in prose — the security synthesis's
claim-typing and hash-stable identifiers would be a layer Linus adds on top, not something Link provides. The MCP server
requires the `mcp` SDK, Python 3.10+, and works against a local directory only; no remote wiki, no authentication on
`serve.py` (binds `127.0.0.1` and the README warns explicitly against exposing it). Single-maintainer project, four
commits of history visible in the clone, beta status — operational risk if Linus depends on it deeply.

## 6. Recommendation: **Study**

Read `LINK.md`, `mcp_package/link_mcp/server.py` end-to-end, and the `doctor` implementation in `link.py` before
designing the Phase 2 KnowledgeBase write/maintenance interface. Adopt the page-template + confidence-tag + maturity
conventions wholesale unless there's a reason not to. Adopt the `get_context` "page plus graph neighborhood in one call"
API shape for KnowledgeBase's agent-facing retrieval. Do not vendor the code; the value is in the conventions and the
API shape, not in 2,800 lines of Python that Linus will want to rewrite to share the orchestration layer's session
store, audit log, and sandbox policy. Revisit after the Group 2 sweep: if a sibling engine offers a better retrieval
story (BM25, embeddings, claim-typing) with comparable simplicity, prefer that one. If not, `link` is the reference.

## 7. Questions for Dan

- **Substrate choice for KnowledgeBase write layer.** Link bets on plain markdown in a directory, no DB. KnowledgeBase
  today uses SQLite for metadata and a vector store for embeddings. Should Phase 2's wiki-style synthesis layer sit on
  top of KnowledgeBase's existing storage, or should it adopt Link's directory-of-markdown substrate (with KB continuing
  to handle papers and embeddings)?
- **Confidence tags vs. claim-typing.** The security synthesis argues for typed claims with content-hashed identifiers;
  Link uses inline `[confidence: high/medium/low]` strings in prose. Are those compatible — confidence as a field on a
  typed claim — or does adopting claim-typing mean abandoning Link's prose-friendly tagging?
- **Wiki maintenance as a Worker job.** The Link model is "agent ingests, agent compiles, agent maintains." On Linus
  that's a Worker loop running on Qwen2.5-Coder or a future fine-tuned Linus. Is wiki maintenance a good first
  long-running Worker task to design around in Phase 3, or does it belong later?
- **Sibling sweep verdict.** Of the eleven Group-2 engines, only the rest of the sweep will tell us whether Link's
  stdlib-only / markdown-only minimalism is the right baseline or whether a sibling with embeddings + BM25 + graph
  re-ranking is closer to what Phase 3 needs. Hold the integration decision until the full Group 2 read is in?
