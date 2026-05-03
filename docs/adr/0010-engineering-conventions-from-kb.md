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
