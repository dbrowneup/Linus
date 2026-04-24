# Linus — Decisions Log (ADR)

An append-only log of significant architectural, product, and process decisions. Each
entry has an id, date, context, decision, and consequence. Inspired by the ADR pattern
(see https://adr.github.io/). When this file exceeds ~20 entries, graduate to per-file
ADRs in `docs/adr/NNNN-title.md`.

## Format

```
## DEC-NNNN — <short title>

**Date:** YYYY-MM-DD
**Status:** proposed | accepted | deprecated | superseded by DEC-MMMM

**Context.** Why is this decision being made? What's the forcing function?

**Decision.** What are we doing? Be specific.

**Consequence.** What does this enable? What does it foreclose? What's the reversal cost?
```

---

## DEC-0001 — Project name and namesake

**Date:** 2026-04-22
**Status:** accepted

**Context.** The project needed a name that reflects its character — local, open,
principled, cross-domain, long-horizon — and that would sit well as a daily companion.

**Decision.** The project is named **Linus** after both Linus Pauling (biochemist,
humanitarian, Oregonian, basement-lab hacker turned two-time Nobel laureate) and Linus
Torvalds (engineer, open-source advocate, Oregonian). The logo will be a carbon atom,
reflecting Pauling's foundational work on carbon chemistry, the role of carbon in
biochemistry (Dan's field), and the hardware/wetware bridge at the heart of the project.

**Consequence.** The name carries real weight — Pauling and Torvalds embody principles
(independence, craft, long horizons, open access) that shape Linus's design. The
project is personal; the name will not be genericized for broader use.

---

## DEC-0002 — Orchestration backend as the core product

**Date:** 2026-04-22
**Status:** accepted

**Context.** Several candidate architectures presented themselves: fork a harness
(Cline, claw-code, openclaw) and extend it; use harnesses directly with some glue; or
build a harness-agnostic orchestration backend that multiple front-ends point at.

**Decision.** Linus is a **harness-agnostic orchestration backend** exposing an
OpenAI-compatible endpoint. Front-ends (Cline, openclaw, VS Code chat, future native
app) are interchangeable UIs; the backend accrues Linus-specific value (tools, skills,
sandbox policy, RAG, eventually fine-tuned models).

**Consequence.** Requires building a Python backend at `src/linus/` — more work than
forking a harness. But Linus's work accrues centrally and survives harness swaps.
Swapping from Cline to openclaw to a native app doesn't require rebuilding
KnowledgeBase integration, sandbox policy, or fine-tuned models.

---

## DEC-0003 — KnowledgeBase stays separate, integrated via submodule

**Date:** 2026-04-22
**Status:** accepted

**Context.** Dan's papers_analysis project (now KnowledgeBase) overlaps heavily with
Linus's knowledge layer. Options were: (a) fully subsume KnowledgeBase into Linus, (b)
keep it separate and consume as a submodule, (c) keep it separate and consume as a
published package.

**Decision.** KnowledgeBase is tracked as a **git submodule at `modules/KnowledgeBase/`**.
Linus imports it via an adapter at `src/linus/knowledge/`. KnowledgeBase continues as an
independent project; Linus pins a SHA and updates it deliberately.

**Consequence.** KnowledgeBase can be developed and released independently. Linus
doesn't fork it. Updating the submodule is an explicit commit. Changes to
KnowledgeBase functionality happen in the KB repo, with its own review, not via Linus
edits.

---

## DEC-0004 — Package/env management via mambaforge conda

**Date:** 2026-04-22
**Status:** accepted

**Context.** Dan's existing environment uses mambaforge (conda-forge) + conda. KB also
uses conda. Options were: keep conda, switch to uv+venv, or use both.

**Decision.** Linus uses a **conda environment named `linus`**, managed via
mambaforge. Rust and uv are installed inside the conda env for tool flexibility
(pmetal build, autoresearch-mlx, etc.). Node/npm can also be installed into the env if
needed. The brew-installed `mlx`, `mlx-c`, and `ollama` are NOT reinstalled via conda —
the brew versions have native Apple Silicon optimization.

**Consequence.** Consistent with KnowledgeBase's conventions, so patterns transfer
cleanly. Environment is reproducible via `environment.yml`. Does NOT preclude
experimenting with uv-managed venvs for specific subprojects later.

---

## DEC-0005 — Maestro/Worker protocol starts OpenAI-compatible, may migrate to MCP

**Date:** 2026-04-22
**Status:** accepted

**Context.** Communication protocol between Maestro (hosted Claude) and Workers (local
models). Options: MCP, OpenAI-compatible HTTP, or a direct SDK approach.

**Decision.** Start with **OpenAI-compatible HTTP** as the protocol for Maestro/Worker
and front-end/backend. It's what Ollama, pmetal, and LM Studio all speak; it's what
Cline and openclaw already support; it's what KnowledgeBase's Haystack integration
already uses. **Revisit MCP for adoption in Phase 3** once tool-use patterns settle and
the benefit of MCP's structured context model becomes clearer.

**Consequence.** Low initial friction. Clear migration path. MCP-specific features
(cross-server context sharing, structured resources) are deferred but not precluded.

---

## DEC-0006 — pmetal evaluated as primary serving + training backend in Phase 1

**Date:** 2026-04-22
**Status:** proposed — decision gate in Phase 1

**Context.** pmetal is a comprehensive Apple Silicon ML platform (Rust, native Metal
kernels, ANE pipeline, LoRA training, distillation, OpenAI-compatible serving). It
potentially collapses "serving layer" and "training backbone" into one component.
Alternative: use Ollama for serving, mlx-lm for training.

**Decision.** **Evaluate pmetal seriously in Phase 1** (deliverable 1b) with comparative
benchmarks against Ollama on matched models. Gate decision in
`docs/adr/0001-inference-backend.md` determines whether pmetal is adopted as primary
serving backend, training backbone, both, or neither.

**Consequence.** Commits Phase 1 time to a real evaluation instead of hand-waving.
Outcome may be "adopt pmetal fully" (big architectural win) or "Ollama for serving, mlx-
lm for training" (safer) or a hybrid. The evaluation itself is valuable regardless.

---

## DEC-0007 — Claude Code remains the terminal Maestro; claw-code is reference-only

**Date:** 2026-04-22
**Status:** accepted (amended 2026-04-23 to note claw-code-local fork)

**Context.** Dan wanted a terminal-based agent harness usable with local models.
claw-code is an open-source Rust harness with similar interface but requires an
Anthropic API key and does not natively support Ollama.

**Decision.** **Claude Code (hosted) is the terminal Maestro** for the foreseeable
future. claw-code is kept as a reference clone in `repos/claw-code/` — study its
architecture and philosophy, but do not adopt it as a runtime component. A local-model
terminal agent is a Phase 5+ deliverable, built as either a thin wrapper on Linus's
backend (~500 LOC) or by adopting Cline's CLI mode if it fits.

**Consequence.** Avoids the sunk cost of patching claw-code to support local models.
Keeps near-term focus on Linus's orchestration layer. Terminal-local-agent need gets
addressed when it becomes concrete.

**Amendment 2026-04-23 — claw-code-local fork.** A community fork
([github.com/codetwentyfive/claw-code-local](https://github.com/codetwentyfive/claw-code-local))
already adds an Ollama backend to claw-code, which is exactly the gap that made upstream
claw-code reference-only. It's now cloned at `repos/claw-code-local/`. Treat upstream
**claw-code as inspiration** (architecture and philosophy) and **claw-code-local as a
practical lead** for the Phase 5+ terminal-local-agent deliverable — possibly directly
adoptable, possibly a starting point we extend. pmetal integration would still be net-new
work on top of either. The decision above does not change yet: Claude Code remains the
terminal Maestro and we are not adopting a local CLI harness as a runtime component
today. Re-evaluate when Phase 5 work begins.

---

## DEC-0008 — openclaw as front-end in Phase 5; native Linus app in Phase 8+

**Date:** 2026-04-22
**Status:** accepted

**Context.** openclaw is a polished multi-channel front-end (macOS app, voice wake,
Canvas, iOS/Android nodes) but with a large monorepo (32k+ commits) and its own
opinionated agent architecture that overlaps with Linus's orchestration layer.

**Decision.** In **Phase 5, use openclaw unmodified as a front-end**, configured to
point at Linus's OpenAI-compatible endpoint as its model provider. Accept the
duplication between openclaw's internals and Linus's; we're using it as a UI, not as a
framework to extend. In **Phase 8+, build a native Linus app** (SwiftUI or Tauri) with
fewer features but fully branded and fully under Dan's control.

**Consequence.** Short-term: chat, voice, Canvas, mobile nodes in Phase 5 without
building them. Medium-term: divergence between openclaw's features and Linus's when
their architectures conflict. Long-term: a purpose-built Linus app replaces openclaw
for Dan's primary workflows while openclaw may persist for niche capabilities.

---

## DEC-0009 — LM Studio used for model discovery, not primary runtime

**Date:** 2026-04-22
**Status:** accepted

**Context.** Dan has LM Studio installed with local models. LM Studio provides model
discovery/download UI, casual chat, and a local OpenAI-compatible server.

**Decision.** **LM Studio is a model discovery and exploration tool**, not the primary
Linus runtime. Ollama (and pmetal, if Phase 1 adopts it) serves Linus's production
path because they are scriptable and integrate into pipelines. LM Studio is used
ad-hoc for exploring new models and casual chats with models not yet wired into
Linus.

**Consequence.** Two model stores coexist (LM Studio's and Ollama's) with some
duplication. This is acceptable given their different roles. No need to unify them.

---

## DEC-0010 — Engineering conventions inherited from KnowledgeBase insights report

**Date:** 2026-04-22
**Status:** accepted

**Context.** The Claude Insights Report on KnowledgeBase surfaced actionable patterns:
smoke-test gates, Known Library Quirks section, checkpoint discipline, hooks for
lint-on-edit, parallel Task agents, custom skills. All address real failure modes.

**Decision.** **Adopt all six patterns as first-class conventions in Linus:**

- Smoke-test gates: no full-corpus runs without a sample-pass first
- Known Library Quirks section in CLAUDE.md, updated same-session when quirks are
  resolved
- Checkpoint summaries every 3–4 multi-file edits
- `.claude/settings.json` with PostToolUse hooks: `ruff format --line-length 120`,
  `ruff check --select I --fix`, `ruff check` on Python file edits
- Parallel agent fan-out as the default for work that decomposes naturally
- Custom skills at `src/linus/skills/<name>/SKILL.md` following the Anthropic
  SKILL.md convention, beginning in Phase 7

Additionally: **The Algorithm check** as a first-class convention — before adding any
component, ask "can we delete this requirement instead?" before reaching for a library,
ask "does something we already have serve this purpose?"

**Consequence.** Stronger defaults, fewer late-surfacing failures, lower Maestro token
spend, natural alignment with The Algorithm's "delete before adding" principle.

---

*New decisions append below this line with monotonically increasing DEC-NNNN ids.*
