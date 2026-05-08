# rendergit (`karpathy/rendergit`)

## 1. Purpose and scope

rendergit is a Python CLI tool by Andrej Karpathy that flattens any GitHub repository into a single static HTML page
with syntax highlighting, markdown rendering, sidebar navigation, and search-friendly full-text indexing. It ships two
views: a human-friendly (pretty colors, file tree, Ctrl+F) and an LLM-friendly view (raw CXML text, ready to paste into
Claude/ChatGPT for code analysis). For Linus, it's a lightweight utility for repo analysis and contextual AI interaction
— useful for reviewing external codebases before integrating them into Linus (e.g., studying MLX backend code, Ollama
integration patterns).

## 2. Architecture summary

rendergit is a ~200-line Python script with no dependencies beyond Pygments. It clones a repo to a temp directory,
walks the file tree (skipping binaries and large files), applies Pygments syntax highlighting to source files, renders
Markdown docs, builds a directory tree, generates a sidebar with file links and sizes, and outputs a single self-contained
HTML file. Two CSS themes and JavaScript toggle between human and LLM views. The LLM view dumps all code as plain text
wrapped in CXML tags (`<cxml></cxml>`) for easy copy/paste into Claude.

## 3. What's reusable in Linus

The single-HTML-page-export pattern is useful for distributing Linus codebases to remote Claude (Maestro) for analysis.
The LLM view (CXML formatting + full-codebase dump) could become a Linus tool for "analyze this repo" workflows:
invoke rendergit on a Linus component, feed it to hosted Claude for architectural review, iterate. The dual human/LLM
view UI is a model for Linus frontends that need to support both human browsing and AI-as-a-reader.

## 4. What's inspiration only

The Pygments syntax highlighting and Markdown rendering are standard; no novel patterns. The single-file HTML export
is elegant but of limited architectural value (useful as a UX detail, not a core component). Karpathy's speed-coding
ethic ("vibe coded... I don't intend to maintain or support it") is thematically aligned with Linus's Algorithm/blitzscaling
but doesn't translate to design decisions.

## 5. What's incompatible or out of scope

rendergit is read-only code exploration; Linus requires read-write tool interaction (editing files, running tests,
executing workfows). The single-file export is valuable only for static analysis and review; it's not a substitute for
a proper repo browsing UI or IDE integration. The CXML format is Claude-specific; Linus may eventually need support for
other AI models that use different context formats (e.g. `<document>` for smaller APIs).

## 6. Recommendation: **Watch (Phase 5+ as a repo-analysis tool)**

Integrate rendergit in Phase 5+ if Linus needs to analyze external repos or package Linus's own codebase for remote
Claude review. For Phase 1-4, skip it; direct GitHub/git access and Claude Code's file reading are sufficient. If
adopted, wrap it in a Linus tool that invokes rendergit and pipes the output to Claude, with results cached locally.

## 7. Questions for Dan

- **Repo analysis workflow.** When analyzing a new external repo before integration (like today's 4 repos), what's your
  current workflow? Would an automated rendergit + Claude Code analysis pipeline save you time vs. manual README skimming?
- **CXML vs. other formats.** Is CXML the right serialization for code-to-Claude, or should Linus invent its own
  (e.g., structured JSON with file paths, language, and code blocks)?
- **Privacy of repo exports.** Rendering a repo to static HTML (even locally) creates a shareable artifact. Should Linus
  tools have a guardrail against exporting proprietary code, or is that the user's responsibility?

---

_Repo-note written 2026-05-05._
