# claude-prism (`delibae/claude-prism`)

## 1. Purpose and scope

ClaudePrism is a **local-first scientific writing workspace** — a Tauri 2 + Rust desktop app that wraps the Claude CLI
around an offline LaTeX toolchain (Tectonic embedded), a built-in `uv`-managed Python environment, a CodeMirror 6
editor, native MuPDF PDF preview with SyncTeX, a Git-backed snapshot history (`.claudeprism/history.git/`), Zotero OAuth
for citations, and one-click installation of the K-Dense-AI **claude-scientific-skills** corpus. It is positioned
explicitly as a Claude-native answer to OpenAI's hosted Prism — same writing-workspace shape, but with files compiled
and stored on disk and AI inference delegated to Anthropic's API rather than uploaded to a vendor's storage. MIT
licensed, started from `assistant-ui/open-prism`. README is shipped in English, Korean, Japanese, and Simplified
Chinese, and the project advertises macOS Apple-Silicon, macOS Intel, Windows, and Linux AppImage builds. For Linus this
is the first repo in the collection that targets the **paper-drafting end of the scientific workflow** — not RAG over
papers (paper-qa), not benchmark agents (BixBench, LAB-Bench), not the multi-agent research loop (robin/aviary), but the
act of writing the manuscript itself.

## 2. Architecture summary

A pnpm + Turbo monorepo (`pnpm-workspace.yaml`: `apps/*`, `packages/*`) where the only shipping app today is
`apps/desktop/` — a Tauri 2 shell with React 19 + Vite + TypeScript on the webview side and a small Rust backend in
`apps/desktop/src-tauri/src/` totaling nine modules: `claude.rs` (spawns and supervises the Claude CLI as a child
process via `tokio::process::Command`, streams stdout/stderr over Tauri events), `latex.rs` (Tectonic compilation — note
the `tectonic = "0.15"` crate and Cargo.toml's harfbuzz/icu/freetype build instructions), `history.rs` (vendored libgit2
via `git2`), `skills.rs` (downloads
`https://github.com/K-Dense-AI/claude-scientific-skills/archive/refs/heads/main.tar.gz` and unpacks into
`~/.claude/skills/scientific-skills/` or per-project), `slash_commands.rs`, `uv.rs` (fetches and manages an `uv`-created
project venv), `zotero.rs`, plus `lib.rs` and `main.rs`. The Rust crate denies `unwrap_used` and `expect_used` via
clippy lints. Auto-update is wired through `tauri-plugin-updater`. The Anthropic dependency is indirect: ClaudePrism
shells out to the locally-installed `claude` CLI rather than calling the Anthropic SDK from Rust, which means it
inherits whatever auth, model selection, and tool surface the CLI ships with. Notably **there is no local-LLM backend**
anywhere in the tree.

## 3. What's reusable in Linus

The most directly transferable piece is the **Tectonic + uv + Git-snapshots desktop pattern** for scientific writing. If
Linus's Phase 8 native-app conversation eventually picks up paper drafting as a first-class surface, this is prebuilt
prior art for "embed a LaTeX engine, embed a Python env manager, snapshot every save into a hidden Git repo, hand the
assistant an editor with diff/accept-reject UX." The `skills.rs` install routine is a 200-line reference for how to
bootstrap `~/.claude/skills/` from a GitHub tarball — directly relevant to Phase 7's skills-graduation work and useful
even before Linus has its own skill format. The Claude-CLI-as-subprocess pattern in `claude.rs` is also instructive for
how openclaw or a future Linus front-end might shell out to a local agent process and stream events back to a webview.

The critical sibling comparison: **claude-prism and `scientific-agent-skills` (also G8) consume the exact same skill
corpus** — `K-Dense-AI/claude-scientific-skills`. ClaudePrism downloads main.tar.gz at install time; scientific-agent-
skills _is_ that corpus (or its 135-skill cousin). Where they differ is the harness wrapped around the skills:
scientific-agent-skills pairs with K-Dense's BYOK desktop chat app for general scientific Q&A; claude-prism wraps the
same skills inside a LaTeX-first writing workspace with Tectonic, MuPDF, and Zotero. So claude-prism's actual
contribution over its sibling is **the writing surface**, not the skills. Compared to `paper-qa` (G8) it sits at the
opposite end of the workflow — paper-qa retrieves and summarizes the literature you read; claude-prism helps you write
the paper that cites it. Compared to `OmegaWiki` (G2, 24 Anthropic-authored Skills covering the research lifecycle
including paper drafting), the comparison is closer in intent but OmegaWiki is a Skills bundle whereas claude-prism is a
full GUI; OmegaWiki's paper-drafting skill could plausibly be installed _into_ claude-prism alongside the K-Dense
corpus.

## 4. What's inspiration only

The native desktop GUI itself — CodeMirror 6 LaTeX bindings, MuPDF rendering, capture-and-ask region selection, the
proposed-changes diff panel — is not Linus territory. Linus is an orchestration backend with Streamlit and eventually
openclaw as its UX. The auto-update pipeline, multi-OS code-signing scaffolding, and Tauri capabilities/entitlements
plumbing are features of a shipped consumer app, not a personal AI backend. The Zotero OAuth integration is a standalone
module worth knowing exists but not worth porting until Linus needs citation tooling.

## 5. What's incompatible or out of scope

"Offline-first" needs careful unpacking against Linus's threat model. ClaudePrism's offline guarantees cover document
storage, LaTeX compilation, snapshot history, and Python execution — your manuscript and its build pipeline never leave
the disk. But **AI inference is online** and goes to Anthropic's API via the Claude CLI; the README is honest about this
("prompts and file contents that Claude reads are sent to Anthropic's API for inference"). For Linus's Phase 4
data-sovereignty objectives this is the wrong direction — Linus aims to run inference on a local Worker (Ollama, pmetal,
fine-tuned Linus). Adopting claude-prism wholesale would re-create the API dependency the project is designed to retire.
There is also no plumbing in the Rust backend for swapping the Claude CLI out for a local OpenAI-compatible endpoint;
doing so would mean either patching `claude.rs` or convincing the Claude CLI itself to target a local provider.
Apple-Silicon viability is otherwise excellent — there is a published ARM64 macOS DMG, a `build:macos` script targeting
`aarch64-apple-darwin`, and the Tauri/Rust stack is the same one pmetal uses.

## 6. Recommendation: **Study**

Install the released DMG to evaluate the writing UX hands-on — it is the closest thing in the collection to "what a
scientific-paper-drafting Worker UX could feel like." Read `skills.rs` end-to-end before designing Linus's own skill
loader in Phase 7. Do not vendor the Rust crate or the React app; do not try to retarget the Claude CLI inside it at a
local Linus endpoint as a first project (the leverage is poor versus just running the CLI against hosted Anthropic when
you actually need to draft a paper). Revisit if Phase 8 produces a native Linus desktop app, at which point
claude-prism's shell becomes a real reference architecture rather than a curiosity.

## 7. Questions for Dan

- **Paper-drafting as a Worker task.** Does the Phase 7 skills graduation include "draft a methods section from a
  notebook" or "convert a markdown draft to a journal-formatted LaTeX manuscript" as named Worker capabilities, or is
  manuscript writing always a Maestro+Dan activity? The answer changes whether claude-prism's shell is interesting at
  all.
- **K-Dense skills corpus relationship.** Two repos in this group (claude-prism and scientific-agent-skills) install the
  same K-Dense bundle. Should Linus pick the K-Dense corpus as its canonical Phase 7 scientific-skills baseline, or is
  OmegaWiki's Anthropic-authored set or some merged superset more appropriate for a PhD biochemist's workflow?
- **Tectonic embedding.** Embedding Tectonic costs a substantial Rust dependency tree (harfbuzz, icu, freetype,
  graphite2). For a Linus-side LaTeX capability, is "shell out to a system `tectonic` binary" enough, or is the
  embedded-engine pattern worth the build complexity?
- **Local LLM fit.** Suppose Phase 6 produces a Linus fine-tune capable of competent LaTeX editing on a given
  manuscript. Would patching claude-prism's `claude.rs` to talk to a local OpenAI-compatible endpoint be a reasonable
  Phase 8 spike, or is the Claude-CLI-subprocess assumption baked deep enough that a fork is impractical?
- **Differentiator confidence.** I read claude-prism as "K-Dense scientific skills wrapped in a LaTeX/PDF/Zotero writing
  GUI." If you see a sharper differentiator after using the DMG — particularly something the K-Dense
  scientific-agent-skills app doesn't already provide — please flag it; I had to stop short of running both apps
  side-by-side.
