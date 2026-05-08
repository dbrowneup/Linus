# markdownify-mcp (`glama-ai/markdownify-mcp`)

## 1. Purpose and scope

Markdownify is an MCP (Model Context Protocol) server that converts diverse file types (PDFs, images, audio,
DOCX/XLSX/PPTX) and web content (YouTube, Bing search, general pages) into Markdown. It wraps `markitdown[all]`
(Microsoft's document-to-Markdown converter) and exposes 10 tools as an MCP server via a TypeScript/Bun stack. For
Linus, this is a direct fit for the Knowledge Ingestion tier: documents and web content → Markdown → KB indexing.

## 2. Architecture summary

Markdownify runs as an MCP server (Bun-based TypeScript) that spawns `markitdown` CLI subprocesses for actual
conversion. The server exports tools that handle PDFs (via `markitdown[pdf]`), images with OCR/metadata, audio
transcription, office documents, and web content (including YouTube transcript retrieval via `yt-dlp`). Path sandbox is
enforced via `MD_ALLOWED_PATHS` environment variable (colon-separated directory list on POSIX, semicolon on Windows).
The preinstall script creates a `.venv` with `markitdown[all]` extras. Supports both standalone (Bun) and Docker
deployment with configurable path restrictions.

## 3. What's reusable in Linus

This server is a direct plug-into Linus's MCP layer — once Linus has the MCP orchestration backend (Phase 2a), adding
markdownify-mcp as a tool is a two-line config add (declare the server in MCP config, mount it as a tool in the
registry). The path sandbox pattern (`MD_ALLOWED_PATHS`) is a clean template for Linus's own sandbox policy. For
KnowledgeBase v1 ingestion, markdownify handles the "convert arbitrary documents to ingestion-ready Markdown" problem.
Audio transcription (via `markitdown[all]`'s built-in Whisper support) is valuable for Dan's growing corpus of voice
notes or recorded talks.

## 4. What's inspiration only

The choice to wrap `markitdown` CLI (rather than using its Python library directly) trades some latency for simplicity —
Linus will eventually want the Python library bundled into its inference loop (especially for document-heavy prompts).
The Docker image slim build (with only `markitdown[pdf]`) is a useful pattern for cloud-native later phases, but not
immediately actionable. Bing search integration is low-value for Linus (Internet-connected Linus is out of scope).

## 5. What's incompatible or out of scope

Markdownify does not touch data quality or schema enforcement — converted Markdown is raw, not validated against KB
structure. For larger files (100+ MB PDFs), Bun subprocess overhead and `markitdown`'s memory usage may become visible
on M1 Max; measure before assuming it scales to Dan's full paper corpus. MCP over stdio (the default Bun transport) is
fine for development but requires careful env-var setup in VS Code and other harnesses; later Linus phases may prefer
HTTP-based MCP transports for clarity.

## 6. Recommendation: **Integrate (Phase 2a)**

Markdownify-mcp is a natural first MCP tool to add to the orchestration backend. Once Phase 2a has MCP server
discovery + tool registry, mark this as a dependency and run a smoke test: load 5 sample PDFs from context/, convert
them, validate the Markdown is well-formed and ingestion-ready. If tools include YouTube (common for Dan's future
workflows), test one transcript. This establishes the MCP-as-tool-substrate pattern.

## 7. Questions for Dan

1. **Markitdown CLI overhead vs. Python library.** Should Linus import `markitdown` as a Python package (tighter
   integration, no subprocess) or keep the Bun/CLI pattern (cleaner separation, easier to upgrade markitdown)? The CLI
   approach has uncertain memory overhead at scale.
2. **Audio transcription priority.** Is voice-note ingestion (via Whisper) a Linus feature for Phase 2a, or does it wait
   until KnowledgeBase v2 workflow is mature?
3. **Bing search tool.** Keep it in Linus MCP config or delete it from the tool registry to minimize API surface?
4. **Markdown validation post-conversion.** Should the KB ingestion tier validate Markdown structure and warn on
   malformed output, or assume markitdown output is always clean? _Partially resolved (DEC-0019, see
   [answered-questions.md](../questions/answered-questions.md)): KB ingest quality gate is a quality surface not a hard
   gate; validation warnings are consistent with that posture; specific Markdown structural checks remain to be
   specified._
