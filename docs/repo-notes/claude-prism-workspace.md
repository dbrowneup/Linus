# Claude-Prism (`delibae/claude-prism`)

## 1. Purpose and scope

Claude-Prism is an offline-first scientific writing workspace — a Tauri 2 (Rust) desktop app for LaTeX editing with
integrated AI assistance via Claude API, embedded Python environment (uv + venv), offline Tectonic LaTeX compilation,
100+ domain-specific scientific skills (bioinformatics, cheminformatics, ML, proteomics, materials science), Git-based
version history, and Zotero bibliography integration. For Linus, Claude-Prism is a reference for how to build a
sophisticated local-first AI application on macOS (Apple Silicon native) that operates mostly offline but leverages
Claude API when AI services are needed. The scientific-skills library is particularly relevant to Dan's genomics work.

## 2. Architecture summary

Claude-Prism is a monolithic Tauri v2 app: Rust backend handles file I/O, subprocess management (uv, tectonic, git),
and LaTeX compilation; React + TypeScript + Fluent UI v9 frontend provides the editor, chat interface, and history
panels. Claude API integration is stateless (no local model server needed). LaTeX compilation is fully offline via
embedded Tectonic (TeX packages downloaded once, cached locally). Python environment management uses uv for fast venv
setup and pip operations. Git history is stored in a local `.claudeprism/history.git/` repository with automatic
snapshots on save. The "Capture & Ask" mode (press Cmd+X) overlays a selection tool on top of PDFs, captures regions,
and pre-fills the chat composer with the image.

## 3. What's reusable in Linus

The scientific-skills library (K-Dense-AI repo, 100+ domain prompts for bioinformatics, genomics, data analysis, etc.)
is directly portable to Linus as a skills expansion mechanism in Phase 3+. The Tauri + Rust architecture is a reference
for building a native macOS app if Linus eventually wants a native UI (Phase 8). The uv integration pattern (one-click
venv setup) is a model for how Linus could manage per-task Python environments. The Git-based history pattern (append-only
snapshots with labels + diffs) is similar to the workgraph JSONL session-store idea from CLAUDE.md's MCP section.

## 4. What's inspiration only

Claude-Prism's full LaTeX + PDF + editor stack is out of scope for Linus (which is not a writing tool). The Zotero
integration and citation management are discipline-specific to academic writing. The Tauri architecture is relevant
only if Linus pursues Phase 8's native app; for Phase 1–7, the OpenAI-compatible API endpoint is sufficient. The
ChatGPT/GPT-5.2 integration points serve as a reference but are not actionable for local-model-first Linus.

## 5. What's incompatible or out of scope

Claude-Prism requires Claude API keys (unlike Linus's local-first model strategy). The entire LaTeX/PDF compilation
infrastructure is not applicable to Linus (which is not a document authoring tool). Tauri 2 is Windows/Mac/Linux native
but adds a Rust+TypeScript duet that would complicate Linus's Python-native design. The scientific skills are valuable
but require constant curation and updates in lockstep with Claude's capabilities.

## 6. Recommendation: **Study (Phase 3+ skills expansion, Phase 8 UI reference)**

Before Phase 3 integrates the first domain-specific skills module, audit Claude-Prism's K-Dense skills library for
patterns and reusable prompts relevant to Dan's bioinformatics work. As a UI reference, Claude-Prism's chat + editor +
file-browser layout is elegant and worth studying if Phase 8 pursues a native Linus app. Don't integrate the Tauri
codebase; just use it as a design reference and skills inventory.

## 7. Questions for Dan

- **Scientific skills library adoption.** K-Dense's 100+ skills span bioinformatics, cheminformatics, materials science.
  How many are immediately applicable to your genomics/metagenomics work, vs. needing domain customization?
- **Skills versioning and decay.** As Claude updates, domain-specific skills (which embed implicit knowledge of Claude's
  capabilities) may age. Should Linus skills be versioned per Claude model, or should they be aggressively test-driven?
- **Phase 8 UI design.** If Linus eventually gets a native app, is Claude-Prism's sidebar + editor + right-panel layout
  the model you'd want, or do you prefer a different flow (e.g., chat on left, code on right, like VS Code)?

---

_Repo-note written 2026-05-05._
