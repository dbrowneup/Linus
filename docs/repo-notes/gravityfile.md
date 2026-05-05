# gravityfile (`epistates/gravityfile`)

## 1. Purpose and scope

gravityfile (binary alias `grav`) is a Rust+Ratatui TUI disk-usage explorer and analyzer — a modern, visually-rich
replacement for `du`/`ncdu`/`dust` with multi-view navigation (Tree, Miller columns, interactive Treemap), duplicate
detection (3-phase BLAKE3: size → partial → full), file-age distribution analysis, safe trash-based deletes with an undo
stack, git status indicators, and a plugin system with Lua, Rhai, and WASM (Extism) runtimes. It is unrelated to agent
harnesses, orchestration, or model routing — it sits in Group 7 only as the "outlier slot," and the honest read is that
its core function (understanding where disk mass accumulates) has minimal direct relevance to Linus. The interesting
bits, if any, are architectural: the parallel-scanning crate and the Ratatui app structure.

## 2. Architecture summary

A small Rust workspace organized as a thin top-level binary (`src/main.rs`, ~510 lines) that wires clap subcommands
(`scan`, `duplicates`, `age`, `export`, plus a default-launches-TUI mode) to six internal crates: `gravityfile-core`
(FileNode/FileTree types, `CompactString`-based name interning, inode tracking), `gravityfile-scan` (the `JwalkScanner`
doing parallel directory traversal), `gravityfile-analyze` (`DuplicateFinder`, `AgeAnalyzer`), `gravityfile-ops`
(copy/move/trash/undo), `gravityfile-plugin` (mlua + rhai + extism hosts), and `gravityfile-tui` (the Ratatui app, with
sub-modules for `app`, `event`, `preview`, `search`, `theme`, `ui`, and shell-integration via a `--cwd-file` /
`--print-cwd` exit hook). The scanner uses `jwalk::WalkDirGeneric` with `Parallelism::RayonNewPool(4)` on macOS (a
deliberate cap — note the `#[cfg(target_os = "macos")]` branch in `scanner.rs`) and rayon's default pool elsewhere,
prunes via a precompiled `globset` ignore set inside the `process_read_dir` closure to avoid descending into pruned
trees, and broadcasts progress over a `tokio::sync::broadcast` channel so the TUI can render scan progress without
blocking. Memory footprint claim: ~120 MB per 1M nodes via `CompactString` and boxed children. Release profile is the
standard "ship a tight binary" recipe: `lto = true`, `codegen-units = 1`, `strip = true`, `panic = "abort"`.

## 3. What's reusable in Linus

Two small things, neither central. First, `gravityfile-scan` is a clean, MIT/Apache-2.0-licensed example of using
`jwalk` correctly on macOS — including the explicit 4-thread cap (which avoids APFS contention degrading throughput past
a point), the `process_read_dir` closure for early pruning, and cross-filesystem detection via `MetadataExt::dev()`. If
Linus ever needs to walk the KnowledgeBase corpus, the `context/papers/` directory, or a checkpoint tree at high speed
(e.g., "index every PDF newer than X," "find duplicate weight files across `repos/`"), this is the right shape of code
to copy as a 200-line utility rather than a dependency. Second, the Ratatui app skeleton in `gravityfile-tui`
(App/Event/UI module split, broadcast-channel-backed progress, shell-integration via cwd file on exit) is a passable
reference if Linus ever wants a native TUI front-end alongside the eventual openclaw web UI — though `pmetal` already
ships a more relevant TUI tied to LLM workflows, so gravityfile's TUI is the second-best example here.

## 4. What's inspiration only

Compared to its Group 7 siblings, gravityfile is structurally different. claude-squad and codebuff are agent harnesses;
claude-task-master and workgraph orchestrate task graphs; openrouter-skills and python-sdk are model-routing/SDK
plumbing; origin is a runtime. gravityfile shares none of those concerns — it has no LLM dependency, no tool-calling
protocol, no provider abstraction, and never touches a network. The closest "inspiration" is generic: the plugin system
(Lua + Rhai + WASM via Extism in one process) is an example of multi-runtime embedding in a Rust binary, which is a
pattern Linus might eventually want for user-defined skills, but openclaw and pmetal-mcp are more directly relevant
prior art for that. The "3-phase hash" pattern (cheap discriminator → partial → full) is also a generally useful
performance shape, but Linus has no obvious application for it today.

## 5. What's incompatible or out of scope

There is nothing to integrate. gravityfile is a standalone end-user tool, not a library Linus would link against, and
not a service Linus would call. The plugin runtimes (mlua, rhai, extism), git2 with vendored libgit2 disabled, archive
crates (zip/tar/flate2/xz2/bzip2), and the trash crate are all dependencies Linus has no use for. Pulling
`gravityfile-scan` in as a crate dependency for one helper would drag in compact_str, dashmap, jwalk, rayon, and the
internal `gravityfile-core` types — better to copy 200 lines of jwalk usage if needed.

## 6. Recommendation: **Ignore**

Install it as a personal tool if Dan likes the demo (`cargo install gravityfile` gives both `gravityfile` and `grav`),
but it does not belong in Linus's architecture. Note this in the curation log and move on. If a future Linus phase needs
a fast parallel scanner (Phase 3 KnowledgeBase indexing, perhaps), revisit `crates/gravityfile-scan/src/scanner.rs` as a
copy-paste reference for the ~50 lines of `jwalk::WalkDirGeneric` setup and the macOS thread cap.

## 7. Questions for Dan

- **Does the KnowledgeBase indexer need a fast parallel walker?** If KB ingestion is currently slow because of
  single-threaded directory traversal, the jwalk pattern in `gravityfile-scan/src/scanner.rs` is worth lifting. If KB
  walks are already fast enough or bound by PDF parsing and embedding, this is a non-issue and gravityfile becomes pure
  ignore.
- **Native TUI for Linus — yes or no?** ROADMAP Phase 5 points at openclaw as the front-end and Phase 8 at a native app.
  Is there an in-between phase where a Ratatui TUI for "talk to local Linus from any terminal without a browser" would
  be valuable? If yes, gravityfile-tui and pmetal's TUI become joint references. If no, this question closes the file.
- **Multi-runtime plugin embedding (Lua + Rhai + WASM) — relevant to Phase 7 skills?** gravityfile embeds three
  scripting runtimes in one binary. For Linus's skills/tools system, is in-process scripting on the table, or is the
  plan strictly subprocess + MCP?
- **Outlier honesty check.** The brief flagged this as Group 7's outlier and I confirm it: the only meaningful
  Linus-side angle is the scanner, and even that is a 200-line copy-paste candidate, not an integration. Should outlier
  repos like this get full notes in future curation passes, or a one-liner in the log?
