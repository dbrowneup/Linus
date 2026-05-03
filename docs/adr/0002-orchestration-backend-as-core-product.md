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
