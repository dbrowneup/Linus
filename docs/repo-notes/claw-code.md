# claw-code (`ultraworkers/claw-code`)

> Compare with [claw-code-local.md](./claw-code-local.md). The two are sibling entries: upstream vs. practical local
> fork.

## 1. Purpose and scope

claw-code is a Rust CLI agent harness — a from-scratch reimplementation of Claude Code's terminal experience:
interactive REPL, session persistence, tool use (file read/write/edit, grep, glob, bash, git), slash commands, markdown
rendering. It is a **clean-room port**, not a copy of Anthropic's source, and the upstream branch is hardcoded to
require an `ANTHROPIC_API_KEY` — it does not support local models out of the box despite having a multi-provider
abstraction internally. Treat it as the _canonical design_ of what a polished local CLI agent should look like, and
claw-code-local as the _practical_ entry point for Linus.

## 2. Architecture summary

Rust workspace under `rust/` containing the `claw` binary and its crate dependencies. The `api` crate exposes a
`ProviderClient` abstraction with OpenAI-compat and xAI support already implemented, but the CLI wires it to
`AnthropicClient` specifically and always requires Anthropic credentials. An `install.sh`, `Containerfile`, and
`ROADMAP.md` suggest intent to eventually support ACP/Zed (Agentic Context Protocol, as used by the Zed editor) —
`claw acp serve` is a discoverability alias with no real backend yet. Sibling tooling (`USAGE.md`, `PARITY.md`,
`PHILOSOPHY.md`, `PRD.json`) documents the project carefully; it clearly has professional intent. Container-first
workflow is a supported install path.

## 3. What's reusable in Linus

Indirectly, a lot: the whole notion of "claw-style CLI agent harness pointed at Linus's OpenAI-compatible endpoint" is
how Phase 5c (the terminal-agent surface) gets solved cheaply. Directly, nothing — upstream requires Anthropic API keys,
which is the one thing Linus does not want its local CLI to depend on. However, the _structure_ of the Rust workspace
(how sessions persist, how tool calls are dispatched, how slash commands are defined) is a useful reference for Linus's
own tool-registry and session-store design in Phase 2a, even if Linus implements those in Python.

## 4. What's inspiration only

The `PHILOSOPHY.md` and `PARITY.md` documents are worth reading for how a Claude-Code-parity project frames its scope
and design choices. The UltraWorkers ecosystem (`clawhip`, `oh-my-claudecode`, `oh-my-codex`) suggests an emerging
"companion tooling" culture around agent harnesses; Linus may want to assemble a similar small-tools toolbelt once the
orchestration layer is real.

## 5. What's incompatible or out of scope

The Anthropic-API lock-in is the deal-breaker. The `cargo install claw-code` trap noted in the README (the crates.io
name points to a deprecated stub) suggests active confusion in the upstream world — anything Linus depends on here
should be a git-pinned build from the `ultraworkers` repo, not a crates.io install. ACP/Zed support is aspirational;
don't plan around it.

## 6. Recommendation: **Study (and defer to claw-code-local)**

Read once for vocabulary and design patterns. Do not build. Do not adopt. For any real integration, go to the fork
(claw-code-local, which is the better practical lead) and keep upstream as a reference for what a "production-looking"
Rust agent harness can be.

## 7. Questions for Dan

- **Is "Linus has its own CLI harness" a Phase 5 goal, or OK to stay on Claude Code + claw-code-local forever?** ROADMAP
  5c mentions a ~500-line custom terminal agent as a fallback. The fork handles the local-model case today, so this may
  be a dead requirement.
- **ACP/Zed as a Linus surface.** claw-code's ACP ambitions overlap with any future Linus-in-Zed idea. Not a
  2026-current path, but worth flagging if you care about the Zed ecosystem.
- **Rust as a Linus language.** claw-code, claw-code-local, and pmetal are all Rust. If Linus stays Python-first for
  orchestration but has Rust-based components (pmetal bindings, future CLI), is that fine, or do you want a stated "one
  orchestration language" policy?
- **Read `PHILOSOPHY.md` now or defer?** It's short; likely contains framing worth lifting into Linus's own docs if
  relevant. I can pull excerpts into VISION.md if useful.
