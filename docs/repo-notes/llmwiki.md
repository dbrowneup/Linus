# llmwiki (`lucasastorian/llmwiki`)

## 1. Purpose and scope

llmwiki is one of the more polished open-source implementations of Karpathy's "LLM Wiki" gist: rather than re-deriving
knowledge from raw documents on every query via RAG, an agent (here, Claude over MCP) incrementally builds and maintains
a persistent markdown wiki under a `wiki/` subfolder of the user's research directory. The pitch is explicit on the
README: "research folders accumulate useful material faster than I can keep summaries, links, and citations current by
hand. LLM Wiki offloads that editing work to Claude so I can focus on source selection and analysis instead." It ships
as a full local-first product — Python FastAPI backend, Next.js web reader, stdio MCP server, a thin `llmwiki` Python
CLI for `init`/`serve`/`mcp`/`mcp-config`/`reindex`, and a Docker-Compose-deployable hosted multi-tenant variant
(Postgres + Supabase auth + S3) that backs the author's `llmwiki.app` SaaS. Apache-2.0.

## 2. Architecture summary

Three processes, one filesystem, one SQLite. The user's research folder is the source of truth: source documents stay
where they are, the tool adds only `.llmwiki/index.db` (FTS5 search index plus extracted page artifacts) and `wiki/`
(markdown pages Claude writes). Document ingest runs locally via `pdf-oxide` (Rust-based PDF text extraction;
`opendataloader-pdf==2.3.0` in `api/requirements.txt`), `webmd` for HTML, `openpyxl` for spreadsheets, optional
LibreOffice for Office formats, and an optional `MISTRAL_API_KEY` path for higher-quality OCR. The MCP surface
(`mcp/local_server.py` + `mcp/tools/`) exposes five tools to Claude: `guide` (a long, opinionated prompt that prescribes
the wiki's hub/concepts/entities/log layout — see `mcp/tools/guide.py`), `search` (FTS5 list + full-text), `read` (PDFs
with page ranges, glob batch reads), `write` (create/`str_replace`/append, with YAML frontmatter parsing and SVG/CSV
asset support — `mcp/tools/write.py`), and `delete`. Internal cross-references are first-class:
`api/services/ references.py` parses `[^N]: filename.pdf, p.3` citations and `[text](path.md)` wiki links into a
`document_references` edge table, so the wiki maintains a citation graph alongside the prose. A `watchfiles`-based
watcher picks up out-of-band edits. The hosted variant swaps SQLite for Postgres (with PGroonga ranked search) and local
disk for S3 via a `VaultFS` abstraction (`mcp/vaultfs/{sqlite,postgres}.py`).

## 3. What's reusable in Linus

The Phase 2 KnowledgeBase pillar in ARCHITECTURE.md is the obvious target. llmwiki's "filesystem is truth, SQLite is
derived index, agent maintains a markdown wiki layer" model is a strong reference implementation for KB v1: it shows
that a useful agent-maintained corpus can be built without vector search at all (FTS5 with porter stemming carries the
local mode), and that the right MCP surface is small — five tools, not fifty. The `write.py` `str_replace` semantics and
the citation-parser in `references.py` are directly liftable patterns for Linus's own KB tools when MCP gets adopted in
Phase 3. The `guide` tool is the most interesting prior art: a long opinionated system prompt delivered as an MCP tool
return value, defining the wiki ontology (`overview.md` hub, `concepts/`, `entities/`, append-only `log.md`) so that
every Claude session re-anchors on the same structure. That pattern — schema-as-tool-output rather than schema-as-prompt
— is worth borrowing for Linus's claim-typing layer in the security synthesis. Unlike `wikiloom` (git-as-substrate) or
`OmegaWiki` (heavier content-hash-keyed object stores per the group framing), llmwiki's substrate is the plainest thing
possible: a markdown folder plus a rebuildable SQLite cache. That makes it the cheapest of the eleven engines to splice
into Phase 2 KB without committing to a particular versioning model — the content-hashing/claim-typing story from the
security synthesis can be added on top of llmwiki's `documents` table without fighting an existing object store.

## 4. What's inspiration only

The Next.js web reader is not Linus territory — Linus has Streamlit for Phase 2 and openclaw later. The hosted
multi-tenant stack (Supabase auth, S3 storage, PGroonga, Sentry, logfire, Railway deploy configs in every service's
`railway.toml`) is a SaaS productization layer that has nothing to offer a single-user local assistant; the
`MODE=hosted` branches in `api/main.py` and `mcp/hosted.py` should be read past, not ported. Compared to siblings like
`llmwiki-cli` or `wikidesk` (which the group framing suggests are leaner CLI/desktop variants), llmwiki carries the
weight of being also a SaaS — the local mode is real and works, but the codebase is shaped by the multi-tenant case.

## 5. What's incompatible or out of scope

The local mode hard-depends on Python 3.11+ and Node 20+ for the web reader; the web reader is the default UX surface
and `llmwiki serve` starts both. For Linus, the Next.js half is dead weight — running `llmwiki mcp <folder>` directly
against a workspace bypasses it, but then you lose the rendered reader the screenshots advertise. PDF table extraction
is acknowledged-rough (`pdf-oxide` does prose well, tables come through as messy text); for Dan's biochem/genomics
papers with figure captions and data tables this matters and points back to the `MISTRAL_API_KEY` path or to
KnowledgeBase's existing `pypdf`-based pipeline. There is no Apple-Silicon-specific work here — no MLX, no Metal, no
ANE. The "one workspace = one MCP server" constraint is intentional in llmwiki's design but cuts against Linus's likely
desire for a single KB endpoint that spans all of `context/papers`, `context/notes`, `context/threads`, and
`context/books`; it would mean four MCP entries in `.claude/settings.json`, not one.

## 6. Recommendation: **Study**

llmwiki is the cleanest reference implementation in the Karpathy-wiki cohort for the specific patterns Linus needs in
Phase 2 KB: filesystem-as-truth, SQLite FTS5 as the bare-minimum search layer, a five-tool MCP surface, and a citation
graph derived from markdown. Read `mcp/tools/{guide,write,search}.py`, `api/services/references.py`, and the local-mode
half of `mcp/local_server.py` — that's perhaps 1500 lines and most of the design. Do not vendor or fork. When KB v1 is
specced, lift the patterns (especially the `guide`-tool-as-ontology approach and the citation edge table) and implement
them inside Linus's own tool registry against KnowledgeBase's existing storage. Re-evaluate against `wikiloom` /
`wikimind` / `TheKnowledge` once those notes land — if one of them brings claim-typing or content-hashing out of the
box, that may displace llmwiki as the reference.

## 7. Questions for Dan

- **Karpathy-wiki vs. KnowledgeBase RAG.** llmwiki's whole bet is "agent-maintained markdown wiki beats RAG-on-raw-PDFs
  for compounding research knowledge." KnowledgeBase today is a RAG/graph system. Is the Phase 2 KB v1 model a RAG-only
  baseline, an llmwiki-style compiled-wiki layer, or both side by side with the wiki citing back into the RAG?
- **MCP surface size.** llmwiki gives Claude five tools (`guide`, `search`, `read`, `write`, `delete`) and that appears
  to be enough for a maintained wiki. pmetal-mcp ships 45. Is the Phase 3 target for Linus closer to five-per-domain or
  to a flat 30-50 catalog?
- **Workspace cardinality.** llmwiki enforces one workspace per MCP server entry. For Linus, do you want one KB MCP
  endpoint covering all of `context/`, or one per subcorpus (papers, notes, threads, books) so that scope is explicit to
  the agent?
- **Claim-typing interop.** The security synthesis recommends content-hashing and typed claims for KB entries. llmwiki's
  `documents` table has a free-form `tags JSON` column and no claim type. Should a Linus port add a `claim_type` column
  and SHA-256 of canonicalized content from day one, or is that a Phase 3 concern?
- **Differentiator confidence.** I read llmwiki's code but only the group framing for the other ten siblings. Before
  committing to "Study" rather than something stronger, would you want the same depth of read on `wikiloom`,
  `TheKnowledge`, and `OmegaWiki` first to confirm llmwiki really is the cleanest reference and not just the first one
  read?
