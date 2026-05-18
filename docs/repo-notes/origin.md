# origin (`7xuanlu/origin`)

_Refreshed 2026-05-18 against upstream HEAD 43d905d; 157 commits / 512 files reviewed._

## 1. Purpose and scope

Origin is not a coding agent or a harness — it is a **personal agent memory layer**: a local daemon that sits behind
Claude Code, Cursor, Codex, Claude Desktop, Windsurf, Gemini CLI, ChatGPT web, or any other MCP-speaking client and
gives them a shared, durable memory of decisions, preferences, project facts, gotchas, and lessons. As of v0.6.x
(May 2026) the canonical install path is the Claude Code plugin (`/plugin marketplace add 7xuanlu/origin`,
`/plugin install origin@7xuanlu`), with a locked verb set of skills — `/init`, `/brief`, `/capture`, `/recall`,
`/distill`, `/review`, `/forget`, `/handoff` — that exercise the daemon through MCP. The daemon does the housekeeping in
the background — deduplication, cross-linking, page distillation, supersession tracking, contradiction detection,
provenance retention — and exposes recall via MCP through the `origin-mcp` npm package (or as an in-repo Rust binary).
For Linus's stack it slots squarely into the **Knowledge pillar** and the **Memory pillar** (DEC-0028), alongside
KnowledgeBase, not the orchestration or harness pillars. Apple Silicon is a hard platform requirement (M1+, no Intel, no
Linux, no Windows). Published numbers: 168 tokens per query vs 4,505 for full replay, 19% better relevance than basic
vector search; Recall@5 88.0% on LongMemEval-oracle (500 Q) and 67.3% on LoCoMo10. Eval harness at
`crates/origin-core/src/eval/`.

## 2. Architecture summary

A **five-crate** Rust workspace (up from four in the prior note; the Tauri desktop app and its AGPL surface have moved
out of this repo entirely to the separate `7xuanlu/origin-app` repository). The in-repo crates are now: `origin-server`
(Axum HTTP API on `127.0.0.1:7878`); `origin-core` (all business logic — libSQL store, FastEmbed embeddings, llama-cpp-2
inference via Metal, hybrid search, knowledge graph, refinery, eval); `origin-types` (deliberately lightweight
serde-only boundary crate); `origin` / `origin-cli` (a Rust user-facing CLI binary added in #54 that talks HTTP to the
daemon — `setup`, `install`, `status`, `search`, `recall`, `store`, `list`, `agents`, `model`, `key`, `doctor`); and
`origin-mcp` (merged in from a separate repo in v0.5.0 via `git subtree`, published to npm as `npx -y origin-mcp` and to
crates.io as a binary). **All five workspace crates are Apache-2.0 via workspace inheritance.** The Tauri desktop app
(`origin-app`) is AGPL-3.0-only but lives in its own repo and is no longer a concern for code-level reuse from this
monorepo.

Storage is one libSQL DB at `~/Library/Application Support/origin/memorydb/origin_memory.db` with `F32_BLOB(768)` vector
columns (BGE-Base-EN-v1.5-Q, DiskANN-indexed), an FTS5 virtual table auto-synced via triggers, an
entity/relation/observation knowledge graph, and Reciprocal Rank Fusion combining vector + FTS. Three retrieval modes —
base (RRF only), reranked (LLM rescores after), expanded (LLM query expansion before) — each with benchmark variants.
Default on-device LLM is Qwen3-4B-Instruct-2507 on Metal via llama-cpp-2; Qwen3.5-9B optional. The daemon outlives the
app process; external clients (Claude Code via the plugin and `origin-mcp`, Cursor, curl, anything) hit the same `:7878`
socket. macOS launchd integration ships out of the box (`origin install`/`uninstall`/`status`). Significant schema and
naming changes since the prior note: Concept → **Page** (#4b91089 in v0.3.0), domain → **space** (#123 in v0.6.0,
BREAKING CHANGE; complete e2e scoping rename). The `EventEmitter` trait is unchanged and `MemoryDB` is now shared as
`Arc<MemoryDB>` at the server-state layer with a strict "clone the Arc out of the guard before any `.await`" discipline
encoded in AGENTS.md and reinforced by a fleet of PRs (#129, #131, #136). Local data also includes Markdown artifacts at
`~/.origin/pages/`, `~/.origin/sessions/`, plus a local git history users can inspect, revert, or symlink into Obsidian.

## 3. What's reusable in Linus

Origin is the most directly drop-in tool in this group for Linus, and the only one in the harness slot that is genuinely
Apple-Silicon-native rather than just "happens to run on a Mac." Two reuse paths:

**As a deployed dependency.** Run `origin-server` as Linus's per-session memory layer — Linus's orchestrator captures
decisions and gotchas through the HTTP API (`/api/memory/store`, `/api/ingest/text`), and Workers retrieve relevant
context through `/api/search` or `/api/context` before kicking off a task. The Apache-2.0 daemon + MCP shim + CLI are
now ALL Apache-2.0 inside this repo, so Linus can depend on them as out-of-process services without
license-contamination concerns at all — a strict improvement over the prior note's "AGPL-clean boundary types only"
framing. For Claude Code integration specifically, the published plugin (`/plugin marketplace add 7xuanlu/origin`) gives
Dan a one-command path to wire memory into the Maestro side without writing glue. The skill verb set (`/brief`,
`/capture`, `/recall`, `/distill`, `/review`, `/forget`, `/handoff`) is a usable contract for what Linus's own
session-scoped memory commands should look like.

**As architectural reference.** The split between `origin-core` (framework-agnostic, no tauri/no axum, unit-testable
with a `NoopEmitter`) and `origin-server` (HTTP framing only) is exactly the discipline Linus's ARCHITECTURE.md wants
between the orchestration layer and front-end harnesses — and wikimind's #677 refactor independently reached the same
shape. The `EventEmitter` trait pattern — passing `Arc<dyn EventEmitter>` into core instead of leaking a UI handle — is
worth copying for Linus's own session/audit log surface. The Arc-out-of-guard discipline (snapshot what you need from a
`RwLock` guard into a scoped block that ends before `.await`) is a load-bearing concurrency lesson Origin paid for in
PRs #129, #131, #136 — Linus can learn it cheaply. The five-crate workspace shape — types (serde-only boundary), core
(logic, framework-agnostic), server (HTTP), CLI (thin HTTP client), MCP (thin HTTP+MCP bridge) — is a clean template for
Linus's own multi-component layout. The L1–L8 local-vs-CI test responsibility table in AGENTS.md is a concrete prior art
for Linus's own test-tier discipline. The launchd plist scaffolding
(`crates/origin-server/src/resources/com.origin.server.plist`) and the `release-please` gotchas section (the
`feat:`/`fix:` pre-1.0 bump rules, the version-files-in-sync list, the squash-merge title trap) are concrete templates
if Linus ever needs to ship a daemon.

Compared to siblings: cline and the claw-codes are coding agents that _consume_ memory — none of them ship a memory
store. openclaw is a local-first chat gateway that talks to MCP servers but does not itself solve persistent
cross-session memory. Origin fills the gap none of them try to fill, and does so daemon-first (matching openclaw's
local-first ethos) rather than as an editor extension (the cline shape) or terminal CLI (claw-code shape). pmetal
overlaps slightly via `pmetal-mcp` but in the opposite direction — pmetal exposes 45 inference/training tools through
MCP; Origin exposes one capability (memory recall) deeply.

## 4. What's inspiration only

The smart-router dedup pipeline (per-window frame compare, bigram-Jaccard at 0.85, 60s AFK gating, PII redaction) is
interesting if Linus ever does ambient capture, but Phase 2/3 doesn't call for it. The LongMemEval / LoCoMo /
LoCoMo-Plus / LifeBench eval harness is a useful template for a base/reranked/expanded benchmark trio, applicable to
KnowledgeBase RAG but not directly portable. The Claude Code plugin's skill-set design (eight locked verbs, each backed
by an MCP wrapper, with `/brief` reading a handoff status file first and `/handoff` writing one) is good prior art for
how Linus could expose its own session lifecycle to Claude Code without a custom harness.

## 5. What's incompatible or out of scope

**The AGPL license boundary has moved.** As of v0.5.0 the Tauri desktop app lives in `7xuanlu/origin-app` (still
AGPL-3.0-only); the monorepo at `repos/origin/` is now uniformly Apache-2.0. Vendoring code from this repo is no longer
license-blocked. (Code from `7xuanlu/origin-app` would still require AGPL discipline; that repo is not in
`repos/origin/` today.) First compile still takes several minutes while llama.cpp builds for Metal. **The macOS Tahoe
`CXXFLAGS="-std=c++17"` release-build workaround is no longer documented in upstream — it appears to have been resolved
in the current `llama-cpp-2 = "0.1"` dependency. The `ggml_metal_init` failure mode on Tahoe is still documented but is
now handled gracefully: the daemon auto-degrades to no-LLM (`#"Metal/ggml on macOS Tahoe 26.x"` in AGENTS.md), and the
init skill's failure path explicitly recognizes the Metal-init issue as a non-fatal degradation rather than a build
break.** This resolves R3-25's hardest sub-issue at the upstream level. Storage path defaults to
`~/Library/Application Support/origin/`, shared between dev and prod — override with `ORIGIN_DATA_DIR` and
`ORIGIN_PORT`. Single maintainer, v0.6.1, "Early preview, expect sharp edges." MCP is the documented ingress; the bare
HTTP API is canonical in AGENTS.md but could shift between releases.

## 6. Recommendation: **Study (with a high prior on later Integrate-as-service)**

_Verdict unchanged from prior note._ Origin is hardware-aligned, license-compatible at every level of this repo,
plugin-installable into Claude Code today, and solves a real Linus problem (cross-session memory) that none of the other
harnesses or KB tools currently address. The R3-25 Tahoe-compat blocker is largely resolved upstream — daemon
auto-degrades to no-LLM on `ggml_metal_init` failure, and the historic `CXXFLAGS="-std=c++17"` workaround is no longer
needed. But Linus already has KnowledgeBase as the Phase 2/3 knowledge backbone, and the Memory Architecture
specification (DEC-0028 ff., `docs/specs/memory-architecture.md`) still gates adoption. Adopting Origin now would
prejudge that spec. The right move is: read the current AGENTS.md fully (it's substantially expanded since the prior
note), mine the `EventEmitter` / Arc-out-of-guard / spaces-vs-domain / page-vs-concept lessons, borrow the
base/reranked/expanded eval-harness shape for KnowledgeBase RAG benchmarks, and revisit Origin as a candidate
implementation when the Linus memory layer is specified concretely. If the Linus memory spec converges on something
close to Origin's shape (libSQL + BGE + RRF + LLM rerank/expand), prefer running `origin-server` as a sidecar over
reimplementing — the v0.6 numbers are compelling, the codebase is the most polished single-product Rust workspace in the
collection, the license is now permissive end-to-end, and Tahoe compat is no longer a deployment hazard.

## 7. Questions for Dan

1. **AGPL hygiene.** With `repos/origin/` now uniformly Apache-2.0 (the Tauri app moved to a separate AGPL repo we don't
   clone), the boundary-types-only constraint from the prior note is moot for in-repo code. Do we still want a written
   SAFETY.md / DECISIONS.md rule for AGPL code generally (since other repos in the collection are AGPL), or close that
   question?
2. **Eval-harness pattern.** Origin's three-variant benchmark structure (base / reranked / expanded) on LongMemEval and
   LoCoMo is the most disciplined RAG eval in the collection. Worth porting the shape to `benchmarks/dan_tasks/` for
   KnowledgeBase RAG, or premature?
3. **macOS Tahoe stability (R3-25, now mostly resolved upstream).** The `CXXFLAGS="-std=c++17"` workaround is gone in
   current Origin; the `ggml_metal_init` failure mode is documented as a graceful auto-degrade rather than a build
   break. Is your dev MacBook on Tahoe, and if so, does Linus's own llama.cpp / MLX path want to adopt Origin's
   degrade-to-no-LLM pattern, or treat Metal-init failure as a hard error?
4. **Plugin-first install path.** Origin's primary distribution is now the Claude Code plugin
   (`/plugin marketplace add 7xuanlu/origin`). Worth taking a 30-minute spike to install it on Dan's MacBook and measure
   the actual behavior against the spec, before the Memory Architecture work crystallizes?
5. **Skill verb adoption.** Origin's eight locked verbs (`/brief`, `/capture`, `/recall`, `/distill`, `/review`,
   `/forget`, `/handoff`, `/init`) are a usable contract. Does Linus's eventual memory surface adopt the same verbs for
   compatibility, or stake out its own vocabulary?
