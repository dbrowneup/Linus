# swarmvault (`swarmclawai/swarmvault`)

## 1. Purpose and scope

SwarmVault is the most heavily productized member of the Karpathy-LLM-Wiki cohort: an MIT-licensed pnpm monorepo
published as `@swarmvaultai/cli` (Node `>=24`), backed by a marketing site at `swarmvault.ai`, a downloadable desktop
app, an Obsidian plugin, multilingual READMEs (English / Simplified Chinese / Japanese, parity-checked by
`scripts/check-readme-parity.mjs`), and a paid-looking website that nonetheless ships the whole engine open. It
implements the standard three-layer Karpathy pattern (`raw/` immutable sources, `wiki/` LLM-maintained markdown,
`swarmvault.schema.md` co-evolved schema) and then layers on a typed knowledge graph with provenance tracking,
contradiction detection, hybrid SQLite-FTS + semantic-embedding retrieval, tree-sitter code analysis, ~30 input formats
(PDF, Office, EPUB, audio via local Whisper, video via `ffmpeg`/`yt-dlp`, YouTube transcripts, code), an MCP server, a
doctor/workbench self-diagnostic, and an "agent context pack" + "agent task ledger" pair of features that treat the wiki
as both input and durable output for coding agents like Claude Code, Codex, Cursor, Copilot, Gemini CLI, Trae, Kiro,
Hermes, Antigravity, VS Code Copilot Chat, and OpenClaw.

## 2. Architecture summary

Four pnpm workspace packages: `@swarmvaultai/cli` (thin Commander entry, the bin published to npm),
`@swarmvaultai/ engine` (the bulk — ~60 source modules under `packages/engine/src/`: `graph-*.ts`, `retrieval.ts`,
`embeddings.ts`, `code-tree-sitter.ts`, `mcp.ts`, `context-packs.ts`, `memory.ts`, `doctor.ts`, `providers/`,
`web-search/`, `hooks/`), `@swarmvaultai/viewer` (interactive graph viewer / workbench, served via
`swarmvault graph serve`), and an `obsidian-plugin`. State lives on disk under `state/` (graph.json, retrieval indices,
embeddings, sessions, approvals) plus the user-facing `wiki/` markdown tree. Providers are a pluggable abstraction with
`heuristic` (fully offline default), Ollama (recommended local pairing — `gemma4`, `nomic-embed-text`), local Whisper,
OpenAI, Anthropic, Gemini, OpenRouter, Groq, Together, xAI, Cerebras, openai-compatible, and custom; tasks
(`compileProvider`, `queryProvider`, `embeddingProvider`, `audioProvider`) route independently. Releases are gated by
`scripts/release-preflight.mjs`, `check-published-manifests.mjs`, `check-readme-parity.mjs`, and per-provider
`live-smoke.mjs` lanes (heuristic, neo4j, ollama, openai, anthropic). Biome handles lint/format; lefthook runs git
hooks. Every compile emits a "share kit" (markdown, SVG card, HTML preview, JSON metadata) for posting graphs.

## 3. What's reusable in Linus

The Phase 2 KnowledgeBase pillar gets a different shape from swarmvault than it would from `llmwiki`. Where llmwiki is a
clean five-MCP-tool reference you can lift patterns from, swarmvault is a near-complete product whose interesting
architectural ideas are the **context pack** and **task ledger** workflows:
`swarmvault context build "<goal>" --target <path|node|page> --budget 8000` writes a cited, token-bounded handoff under
`wiki/context/` for a coding agent, and `swarmvault task start|update|finish|resume` records a durable task history
(goal, decisions, touched paths, linked packs, outcomes, follow-ups) as git-friendly JSON + markdown, then folds task
nodes back into the knowledge graph. That maps directly onto the Maestro/Worker handoff problem in
`docs/maestro-worker-protocol.md` — the spec-in-`experiments/<task>.md` flow could borrow the bounded-context-pack
pattern wholesale. The contradiction-detection-on-compile (`lint --conflicts`, `extracted` / `inferred` / `ambiguous`
edge tags) is the right answer to the "won't hallucinations compound?" worry that any Phase 2 KB will face. The
provider-routing abstraction (per-task provider selection, with a one-shot `swarmvault provider setup --local-whisper`
registration flow) is a sane template for Linus's eventual model router.

Versus the obvious sibling: `llmwiki-cli` is a four-file Commander CLI with two runtime dependencies (`commander`,
`js-yaml`) and no graph, no embeddings, no providers, no MCP — it punts everything to the calling agent. SwarmVault is
the opposite extreme: typed graph, hybrid retrieval, MCP server, 12 packaged agent integrations, share kit, the works.
They are in the same group only by template. For Linus the relevant comparison is "do we want llmwiki-cli's minimalism
(the agent does the thinking, the tool just edits files) or swarmvault's productized graph + retrieval (the tool
maintains an opinionated structure the agent reads from)?" — Phase 2 KB v1 should pick a side.

## 4. What's inspiration only

Most of the surface area. The desktop app, the multilingual README maintenance machinery, the
`clawhub install swarmvault` skill-distribution workflow, the share-kit (SVG card + HTML preview + bundle for posting
graphs to social), the Obsidian plugin, the 12 agent install targets — none of that is Linus territory. The marketing
site, the SaaS-shaped onboarding ("download desktop app for macOS / Windows / Linux"), and the multi-OS release pipeline
are productization a single-user local assistant does not pay for. The breadth of input formats (Slack zips, mbox, ICS,
BibTeX, AsciiDoc, Org-mode, 14 image formats including JXL/HEIC/AVIF) is impressive but largely orthogonal to Dan's
`context/papers` + `context/notes` + `context/threads` + `context/books` corpus, which KnowledgeBase already handles
through its own `pypdf`-based pipeline.

## 5. What's incompatible or out of scope

Node `>=24` is a hard floor — fine on Dan's machine but a constraint to note. The codebase is TypeScript through and
through, which means embedding it into the Python-first Linus orchestrator means subprocessing the CLI or running it as
a sidecar; there is no Python binding. There is no Apple-Silicon-specific work — no MLX, no Metal, no ANE; tree-sitter
and SQLite are CPU-bound, embeddings come from whatever provider you wire up. The default graph viewer is browser-served
(`graph serve` opens localhost), which is fine but again outside Linus's intended Streamlit / future-openclaw UX
surface. The whole product assumes the agent is the _consumer_ of the wiki (via context packs and MCP) rather than a
peer of the orchestrator — Linus wants tool registries, not turnkey agent installs.

## 6. Recommendation: **Study**

Read three modules and move on: `packages/engine/src/context-packs.ts` (token-bounded agent handoff with citations and
explicit omissions), `packages/engine/src/memory.ts` (durable task ledger with graph integration), and
`packages/engine/src/mcp.ts` (the MCP surface that exposes both). That, plus the `swarmvault.schema.md` template under
`templates/llm-wiki-schema.md`, is the design transfer Linus actually needs. Do not vendor, do not fork, do not
subprocess `swarmvault` from inside Linus — the dependency surface (Node 24, pnpm, four packages, 60 engine modules,
biome, lefthook, tsup, Playwright) is not a price worth paying when KnowledgeBase + a Linus-native context- pack tool
can deliver the same value. Re-read after the `wikiloom` / `wikimind` / `OmegaWiki` / `TheKnowledge` notes land to
confirm context-packs + task-ledger remain swarmvault's distinguishing contribution rather than a common pattern across
the cohort.

## 7. Questions for Dan

1. **Context packs as the Maestro/Worker artifact.** SwarmVault's
   `context build "<goal>" --target <path> --budget <tokens>` is essentially the spec format
   `docs/maestro-worker-protocol.md` is reaching for, but with citations and provenance baked in. Should Phase 2's spec
   format be Linus-native or a thin wrapper over a swarmvault-style bounded-context-pack tool?
2. **Task ledger vs. git history.** SwarmVault's `task start|update|finish` writes a parallel ledger under
   `state/memory/tasks/` and folds it into the knowledge graph. Linus already has git for atomic commits and branches
   for agent work (BRANCHING.md). Is a separate task ledger redundant, complementary (commits are artifacts, ledger is
   intent), or actively confusing?
3. **i18n in the cohort.** SwarmVault is the only sibling shipping Chinese and Japanese READMEs. That suggests the
   author is courting an international user base that the English-only siblings (`llmwiki`, `llmwiki-cli`, `wikidesk`)
   are not. Useful signal for "which of the eleven engines has real users," or noise?
4. **Contradiction detection as a KB feature.** SwarmVault tags every edge as `extracted` / `inferred` / `ambiguous` and
   runs `lint --conflicts`. The security synthesis recommends typed claims + content hashing for KB entries — is the
   swarmvault edge-typing taxonomy the right vocabulary to adopt for Linus, or is it too coarse for scientific claims?
5. **Differentiator confidence.** I depth-read swarmvault and only spot-checked `llmwiki-cli`'s `package.json` for the
   comparison. Before committing the Study verdict, would you want me to do the same depth on `wikiloom`, `wikimind`,
   and `TheKnowledge` to confirm context-packs + task-ledger really are unique to swarmvault and not also present in a
   leaner sibling?
