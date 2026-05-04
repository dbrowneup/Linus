# synthadoc (`paulmchen/synthadoc`)

## 1. Purpose and scope

Synthadoc is the "production-shaped" entry in the Karpathy LLM-wiki cohort — a Python 3.11+ FastAPI engine
(`synthadoc serve` on port 7070) that ingests raw sources (PDF, DOCX, PPTX, XLSX, MD, URL, image, YouTube transcript)
and **compiles** them into a persistent Markdown wiki under a chosen wiki root, with `[[wikilink]]` cross-references,
contradiction detection, orphan-page tracking, an `audit.db` SQLite ledger of every ingest with token cost, a Tavily-
backed web-search ingest path, an Obsidian companion plugin (TypeScript, in `obsidian-plugin/`), a hot-loaded
`BaseSkill` plug-in system for new file formats, hooks fired on `on_ingest_complete` / `on_lint_complete`, and an
OpenTelemetry exporter. AGPL-3.0 (engine) with Apache-2.0 carve-outs for the skill and provider base classes so user
extensions are unencumbered. Versioned (`v0.3.0`, `Community Edition`), CI-tested, and badged like a commercial product.
Where `link` is a single-file vendor candidate and `llmwiki` is the cleanest reference, synthadoc is the one most ready
to be aimed at "small team / enterprise" use — multiple wikis on different ports, scheduled cron-style ingest, and
per-wiki `AGENTS.md` for LLM behaviour.

## 2. Architecture summary

A single Python package laid out by concern: `synthadoc/cli/` (Typer entrypoint `synthadoc.cli.main:app`),
`synthadoc/agents/` (one file per role — `ingest_agent.py`, `query_agent.py`, `lint_agent.py`, `scaffold_agent.py`,
`search_decompose_agent.py`, `skill_agent.py`), `synthadoc/core/` (`orchestrator.py`, `queue.py`, `scheduler.py`,
`cache.py`, `cost_guard.py`, `hooks.py`, `logging_config.py`), `synthadoc/skills/` (one folder per format: `pdf`,
`docx`, `pptx`, `xlsx`, `markdown`, `url`, `image`, `youtube`, `web_search`, registered through `registry.py` against a
`base.py` `BaseSkill`), `synthadoc/providers/` (`anthropic.py`, `openai.py`, `ollama.py`, `coding_tool.py` for Claude
Code / Opencode subscription reuse, plus `pricing.py` for token-cost accounting across seven providers), and
`synthadoc/storage/` plus `synthadoc/observability/`. Each wiki root carries its own `.synthadoc/` directory holding
`config.toml`, `audit.db` (append-only SQLite — source SHA-256, token counts, cost events), `logs/synthadoc.log` (JSON-
lines, rotated by size), `logs/traces.jsonl` (OTel default exporter), and `server.pid`. Ingest is a queued, resumable
job (`core/queue.py`) with retry/backoff and per-wiki cost soft-warn / hard-gate. Search is BM25 (`rank_bm25`) by
default with optional `fastembed` (`BAAI/bge-small-en-v1.5`) re-ranking gated behind `[search] vector = true`. Query and
web-search both use **decomposition agents** (`search_decompose_agent.py`) that split a compound input into parallel
sub-tasks merged before synthesis. Three-layer caching (embedding, LLM response, provider prompt cache) keyed by source
hash; cache invalidates automatically on content change or `CACHE_VERSION` bump in `core/cache.py`. The Obsidian plugin
in `obsidian-plugin/` (esbuild + Vitest) talks to the same HTTP API the CLI uses.

## 3. What's reusable in Linus

Several patterns map cleanly onto Phase 2 (KnowledgeBase v1) and Phase 3 (parallel agents). The **per-wiki `.synthadoc/`
directory layout** — config, audit DB, JSON-lines log, OTel traces, PID file — is a tidy template for how a Linus KB
workspace could be self-contained on disk. The **`audit.db` schema** (source hash, tokens in/out, USD cost, event type,
job id) is exactly the audit trail SAFETY.md asks for; a Linus port could lift it whole. The **`BaseSkill` registry with
hot-load from `<wiki-root>/skills/` and `~/.synthadoc/skills/`** plus the file-extension / intent-prefix dispatch is a
serious candidate for how Linus's Phase 7 skills graduation actually loads skills without restart, and is more
sophisticated than `link`'s static dispatch or `llmbase`'s in-process `register()`. The **decomposition agent pattern**
— split a query into focused sub-queries, fan out, merge, deduplicate, fall back if the LLM call fails — is the cleanest
articulation of Phase 3's "agent fan-out" in any sibling I've seen. Crucially, synthadoc already ships a `coding_tool`
provider (`providers/coding_tool.py`) that reuses Claude Code or Opencode as the LLM backend without an API key —
directly relevant to Maestro/Worker discipline and worth studying as a model for how Linus might shell out to a coding
harness when one is available.

The most distinctive thing relative to siblings: where `link` and `llmbase` are single-process Python scripts, `llmwiki`
adds a Next.js reader, and `wikiloom` (per group framing) bets on git-as-substrate, **synthadoc is the only one that
treats the wiki as a long-running ops surface** — durable job queue with retry, cron-style scheduler
(`synthadoc schedule add ... --cron "0 2 * * *"`), per-model pricing tables and cost gates, OpenTelemetry, multi-wiki
isolation on different ports, and a hooks system intended for CI/CD integration. That ops posture is what Linus's Phase
2a serving layer needs to grow into; synthadoc is a working blueprint.

## 4. What's inspiration only

The Obsidian plugin half is not Linus territory — Linus's UX surface is Streamlit in Phase 2 and openclaw later, and Dan
does not currently use Obsidian as a primary surface. The marketing scaffolding (badges, "Community Edition" versioning,
the comparison table against NotebookLM and Notion AI) is product-page work that has nothing to teach the orchestration
layer. The Tavily web-search-to-wiki path is interesting but presupposes a paid web-search vendor; Phase 4's
data-sovereignty posture (Kiwix, ProtoMaps/OSM) prefers locally-mirrored corpora over ad-hoc web fetches, so this stays
a pattern study rather than a direct port.

## 5. What's incompatible or out of scope

AGPL-3.0 on the engine means vendoring the codebase forces the same license on Linus, which is a deliberate decision not
to be made casually — the Apache-2.0 carve-outs apply only to subclassing `BaseSkill` and `LLMProvider`, not to lifting
`core/orchestrator.py` or `core/queue.py`. There is no Apple-Silicon-specific work here — no MLX, no Metal, no ANE; the
`ollama` provider is the only local path and it inherits whatever Ollama's Metal acceleration offers. The ingest
pipeline assumes "wiki = one domain"; running synthadoc against Dan's `context/papers`, `context/notes`, and
`context/threads` would mean three separate wiki roots on three ports — workable, but cuts against the likely Linus
desire for one KB endpoint that spans all subcorpora. PDF ingest leans on `pypdf` + `pdfminer.six`, which is solid for
prose but matches KnowledgeBase's existing weakness on figure captions and data tables in biochem/genomics papers.

## 6. Recommendation: **Study**

Synthadoc is too heavy and too AGPL to vendor, but it is the most operationally mature member of the wiki cohort and the
one whose patterns map most directly onto Phase 2a (durable queue + audit + cost gate), Phase 3 (decomposition fan-
out), and Phase 7 (hot-loaded skill registry). Read `core/orchestrator.py`, `core/queue.py`, `core/cost_guard.py`,
`agents/search_decompose_agent.py`, `skills/registry.py` + `skills/base.py`, and `providers/coding_tool.py` — that is
the highest-value slice, perhaps 1500–2500 lines. Lift the audit-DB schema and the skill-registry hot-load pattern into
Linus's own (non-AGPL) implementation when the relevant phases land. Re-evaluate once `wikiloom`, `wikimind`,
`OmegaWiki`, and `TheKnowledge` notes are in — if any of them brings claim-typing or content-hashing as primary
abstractions, that may displace synthadoc as the operational reference, but synthadoc will likely remain the strongest
template for the audit/queue/scheduler/cost layer specifically.

## 7. Questions for Dan

- **AGPL boundary.** Synthadoc's engine is AGPL-3.0 with Apache-2.0 only on the `BaseSkill` and `LLMProvider` extension
  classes. Are you comfortable with "read and reimplement the patterns" being the only path, or is there a world where
  Linus tolerates an AGPL submodule for a self-hosted, never-distributed engine?
- **Multi-wiki vs. single-KB cardinality.** Synthadoc's whole UX assumes one wiki = one domain on its own port; the same
  question came up against `llmwiki`. Do you want Linus's KB to be one endpoint over all of `context/`, or one per
  subcorpus (papers / notes / threads / books) so the agent's scope is explicit?
- **Cost-guard relevance.** Synthadoc's `cost_guard.py` exists because its target users hit paid APIs. Linus's
  philosophy is local-first with no paid APIs in the steady state. Is there still a reason to port a soft-warn / hard-
  gate layer (for guarding ANE/GPU minutes, token-budget per task, or future hosted-model spillover), or is this
  inspector-only?
- **Skill hot-load model.** Synthadoc's `BaseSkill` + folder-scan + `entry_points` approach is more dynamic than
  `llmbase`'s `register()` decorator. For Phase 7, do you want Linus skills to be hot-loadable from a directory without
  a server restart, or is restart-on-skill-change acceptable and simpler?
- **Decomposition as a Phase 3 default.** Synthadoc decomposes both queries and web searches into parallel sub-tasks
  with a graceful fallback. Should Phase 3's agent fan-out adopt this as the default execution shape (decompose →
  parallel workers → merge), or is that overkill for the worker-orchestra Linus is initially aiming at?
