# origin (`7xuanlu/origin`)

## 1. Purpose and scope

Origin is not a coding agent or a harness — it is a **personal agent memory layer**: a local daemon that sits behind
Claude Code, Cursor, Codex, Claude Desktop, Windsurf, Gemini CLI, ChatGPT web, or any other MCP-speaking client and
gives them a shared, durable memory of decisions, preferences, project facts, gotchas, and lessons. The daemon does the
housekeeping in the background — deduplication, cross-linking, concept compilation, provenance retention — and exposes
recall via MCP through a small npm package (`origin-mcp`). An optional Tauri desktop app provides a menu-bar process,
search/inspect/edit UI, and "Remote Access" via a Cloudflare tunnel for web clients (Claude.ai, ChatGPT). It groups with
the harness notes only by accident of the curation taxonomy; in Linus's stack it slots squarely into the **Knowledge
pillar**, alongside KnowledgeBase, not the orchestration or harness pillars.

Apple Silicon is a hard platform requirement (M1+, no Intel, no Linux, no Windows). Published numbers: 96% fewer tokens
per query than full chat replay (168 vs 4,505) at 19% better relevance than basic vector search; Recall@5 88.0% on
LongMemEval-oracle (500 Q) and 67.3% on LoCoMo10. Eval harness at `crates/origin-core/src/eval/`.

## 2. Architecture summary

A four-crate Rust workspace plus a React/Tauri 2 frontend, daemon-first. `origin-server` runs an Axum HTTP API on
`127.0.0.1:7878`; `origin-core` owns all business logic (libSQL store, FastEmbed embeddings, llama-cpp-2 inference via
Metal, hybrid search, knowledge graph, refinery); `origin-types` is a deliberately lightweight serde-only boundary crate
so the MIT-licensed `origin-mcp` (separate repo) can depend on it without AGPL contamination; `app/` is the thin Tauri
desktop client (HTTP proxies and macOS sensors). Storage is one libSQL DB at
`~/Library/Application Support/origin/memorydb/origin_memory.db` with `F32_BLOB(768)` vector columns
(BGE-Base-EN-v1.5-Q, DiskANN-indexed), an FTS5 virtual table auto-synced via triggers, an entity/relation/observation
knowledge graph, and Reciprocal Rank Fusion combining vector + FTS. Three retrieval modes — base (RRF only), reranked
(LLM rescores after), expanded (LLM query expansion before) — each with benchmark variants. Default on-device LLM is
Qwen3-4B-Instruct-2507 on Metal via llama-cpp-2; Qwen3.5-9B optional. The daemon outlives the app process; external
clients (Claude Code via `origin-mcp`, curl, anything) hit the same `:7878` socket. macOS launchd integration ships out
of the box (`origin install`/`uninstall`/`status`). Three-license split: `origin-types`/`origin-core`/`origin-server`
are Apache-2.0, the Tauri app and root frontend are AGPL-3.0-only, `origin-mcp` is MIT.

## 3. What's reusable in Linus

Origin is the most directly drop-in tool in this group for Linus, and the only one in the harness slot that is genuinely
Apple-Silicon-native rather than just "happens to run on a Mac." Two reuse paths:

**As a deployed dependency.** Run `origin-server` as Linus's per-session memory layer — Linus's orchestrator captures
decisions and gotchas through the HTTP API (`/api/memory/store`, `/api/ingest/text`), and Workers retrieve relevant
context through `/api/search` or `/api/context` before kicking off a task. Because the Apache-2.0 daemon and the MIT MCP
shim are AGPL-clean, Linus can depend on them as out-of-process services without license contamination of `src/linus/`.

**As architectural reference.** The split between `origin-core` (framework-agnostic, no tauri/no axum, unit-testable
with a `NoopEmitter`) and `origin-server` (HTTP framing only) is exactly the discipline Linus's ARCHITECTURE.md wants
between the orchestration layer and front-end harnesses. The `EventEmitter` trait pattern — passing
`Arc<dyn EventEmitter>` into core instead of leaking a UI handle — is worth copying for Linus's own session/audit log
surface. The `bump-patch-for-minor-pre-major` release-please gotcha and the launchd plist scaffolding
(`crates/origin-server/src/resources/com.origin.server.plist`) are concrete templates if Linus ever needs to ship a
daemon.

Compared to siblings: cline and the claw-codes are coding agents that _consume_ memory — none of them ship a memory
store. openclaw is a local-first chat gateway that talks to MCP servers but does not itself solve persistent
cross-session memory. Origin fills the gap none of them try to fill, and does so daemon-first (matching openclaw's
local-first ethos) rather than as an editor extension (the cline shape) or terminal CLI (claw-code shape). pmetal
overlaps slightly via `pmetal-mcp` but in the opposite direction — pmetal exposes 45 inference/training tools through
MCP; Origin exposes one capability (memory recall) deeply.

## 4. What's inspiration only

The Tauri app, the six-windows-from-one-webview architecture, the ambient/snip/quick-capture sensor pipeline, the
Cloudflare tunnel "Remote Access" feature, and the React 19 + TanStack Query + Tailwind 4 frontend are all GUI surface
area Linus does not need — Linus has Streamlit and eventually openclaw. The smart-router dedup pipeline (per-window
frame compare, bigram-Jaccard at 0.85, 60s AFK gating, PII redaction) is interesting if Linus ever does ambient capture,
but Phase 2/3 doesn't call for it. The LongMemEval/LoCoMo/LoCoMo-Plus/LifeBench eval harness is a useful template for a
base/reranked/expanded benchmark trio, applicable to KnowledgeBase RAG but not directly portable.

## 5. What's incompatible or out of scope

**The desktop app and root frontend are AGPL-3.0-only.** Vendoring any of `app/` or `src/` into Linus's own codebase
forces Linus to AGPL its entire shipped product. This is a hard blocker for code-level reuse of the GUI; the
out-of-process integration path in Section 3 is the only safe one. The Apache-2.0 split for
`origin-types`/`origin-core`/`origin-server` exists precisely so downstream tools can avoid this — respect that
boundary.

First compile takes several minutes while llama.cpp builds for Metal; macOS Tahoe 26.x release builds need
`CXXFLAGS="-std=c++17"`, and `ggml_metal_init` can fail on Tahoe even when native Metal works (daemon auto-degrades to
no-LLM). Storage path defaults to `~/Library/Application Support/origin/`, shared between dev and prod — override with
`ORIGIN_DATA_DIR` and `ORIGIN_PORT`. Single maintainer, v0.2.1, "Early preview, expect sharp edges." MCP is the
documented ingress; non-MCP clients hit the bare HTTP API which is described in CLAUDE.md but not the public README and
could shift between releases.

## 6. Recommendation: **Study (with a high prior on later Integrate-as-service)**

Origin is hardware-aligned, license-compatible at the integration boundary, and solves a real Linus problem
(cross-session memory) that none of the other harnesses or KB tools currently address. But Linus already has
KnowledgeBase as the Phase 2/3 knowledge backbone, and the Memory Architecture specification just landed in the roadmap
(commit `d77e026`). Adopting Origin now would prejudge that spec. The right move is: read CLAUDE.md fully, mine the
`EventEmitter`/Arc-out-of-guard patterns, borrow eval-harness shape for KnowledgeBase RAG benchmarks, and revisit Origin
as a candidate implementation when the Linus memory layer is specified concretely. If the Linus memory spec converges on
something close to Origin's shape (libSQL + BGE + RRF + LLM rerank/expand), prefer running `origin-server` as a sidecar
over reimplementing — the v0.2 numbers are compelling and the codebase is the most polished single-product Rust
workspace in the collection.

## 7. Questions for Dan

- **Memory layer ownership.** The Memory Architecture spec is fresh. Is the intent for Linus to _own_ the memory store
  (KnowledgeBase + bespoke schema) or to _consume_ one (Origin daemon as sidecar)? This decision flips Origin from
  "study material" to "architectural dependency." _Resolved (DEC-0028, DEC-0029, see [answered-questions.md](../questions/answered-questions.md)): Linus owns the memory store; Phase 2 substrate is SQLite + content hashes + git for Layer C; Origin stays study material until the memory spec is concretely implemented, then revisit as sidecar candidate._
- **MCP as the integration substrate.** Origin's primary surface is MCP; pmetal's `pmetal-mcp` exposes 45 tools the same
  way; cline and openclaw both speak MCP. Three of the four most relevant repos in the collection have converged on MCP.
  Want to make MCP-as-tool-substrate an explicit Phase 3 ADR rather than letting it accrete? _Resolved (DEC-0018, see [answered-questions.md](../questions/answered-questions.md)): MCP adopted as the extensibility substrate; MCP ADR to be written at Phase 2a planning time._
- **AGPL hygiene.** Origin is the second AGPL repo encountered (after a few others in earlier groups). Do we want a
  written rule in SAFETY.md or DECISIONS.md that AGPL code is allowed as an out-of-process dependency but never
  vendored, with the Apache-2.0 boundary types as the integration surface?
- **Eval-harness pattern.** Origin's three-variant benchmark structure (base / reranked / expanded) on LongMemEval and
  LoCoMo is the most disciplined RAG eval in the collection. Worth porting the shape to `benchmarks/dan_tasks/` for
  KnowledgeBase RAG, or premature?
- **macOS Tahoe stability.** Origin documents real Tahoe 26.x pain (`ggml_metal_init` failures, C++17 release-build fix,
  CoreGraphics quirks). Is your dev MacBook on Tahoe yet, and if so, has Linus's own llama.cpp/MLX path hit the same
  Metal init failure mode?
