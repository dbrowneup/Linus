---
title: "Why Claude Gets Dumber the Longer Your Session Runs (and the Exact Fix)"
source: blog post / operations guide
author: Ayesha Mughal
date: 2026-03
url: https://medium.com/... (archived from Medium)
file: ../../context/notes/mughal_context_window_management.md
tags: [context-window, memory, operations, session-management, degradation]
---

# Context Window Management for Long Sessions

## TL;DR

Mughal documents the operational failure mode that emerges when hosted-Claude harnesses (Claude Code, etc.) run long sessions without active context management. Session quality degrades to ~40–60% of fresh baseline after several hours, driven by lost-in-the-middle attention, real effective token budget collapse (~147K of 200K), and lack of orchestrated compaction. The mitigation (30-minute sprint + targeted compaction loops achieving ~85% quality retention) applies directly to Linus's Worker session design and memory pillar (M1–M5 resolutions).

## Key claims and insights

- **Lost-in-the-middle effect degrades guidance**: Attention weights concentrate at prompt start and end; session instructions and foundational context (CLAUDE.md, early decisions) sink into weakly-attended middle zones. Repeating corrections makes it worse, not better, because each correction pushes the original guidance deeper into the weak zone.

- **Effective budget collapse before nominal capacity**: 200K context window carries ~7K system prompt, ~8K tool definitions, ~2–8K per MCP server schema. With several servers loaded, usable working budget drops to ~147K. Observable quality degradation begins around 64–75% fill, not 90%.

- **Concrete operational mitigations**:
  - `/context` command: diagnostic visibility into current fill, per-category breakdown (system, conversation, files, tools), remaining headroom. Check at session start; treat 60% fill as action threshold.
  - Three distinct operations: full clear (cheap, loses state); targeted compact (lossy on specifics, retains decisions); rewind (surgical, to specific checkpoint).
  - **Session-handoff file** (`.claude/session-handoff.md`): volatile, gitignored, written at session end and read at session start. Contains modified files, decisions and rationale, current state, exact next step, gotchas. Cleanest mechanism for cross-session reliable history.
  - **MCP-schema budget discipline**: disable MCP servers not needed for current task. Load only what this task needs; schema overhead recovers tens of thousands of tokens.
  - **PreCompact hook**: fires immediately before any compaction (manual or automatic) and writes critical context to handoff file before lossy compression. Safety net against auto-compaction's silent state loss.
  - **30-minute sprint + targeted compaction loop**: bound each session-of-work to single objective, compact before token use crosses degradation threshold, restart fresh. Empirical: ~85% performance retention across 4-hour sessions with eight compactions vs. 40–60% in marathon session.

- **Per-action token cost modeling**: full file reads ~3K tokens, targeted greps ~200, vague prompts ~30K. Specificity is a 40× efficiency multiplier; adopt token cost as routing heuristic.

## What's reusable in Linus

**For memory pillar (M1–M5) and Worker session design:**

- **Mughal operationalizes Garrison's architectural thesis**: Where Garrison argues from complexity theory that episodic stores are non-negotiable, Mughal supplies the empirical "what happens when you don't" in a familiar setting and the "how much you recover" with disciplined management. Both perspectives reinforce: aiming for ever-larger context windows while also routing through an episodic store is the right bet.

- **Session-handoff file is the hosted-Claude analogue of Linus's Phase 2 episodic store**: Same role, different substrate. Handoff is addressable artifact, written at session boundaries, read at start; in Linus, episodic store (SQLite + content hashes + git) carries the same continuity role. The operational pattern transfers directly.

- **PreCompact hook pattern**: Model this in Linus's Worker protocol. Capture and persist the durable substrate (memory-mode choice, current state, decisions) before any lossy compression event, not after. Forbidding the "o1 anti-pattern" (all reasoning in latent space, no intermediate artifacts) is the generalization.

- **MCP-schema budget discipline → cot_budget + memory_mode router**: Both are about budgeting context as a resource per-call, not loading everything by default. Mughal's evidence sharpens the trade-off: smaller per-call budgets (with episodic overflow) outperform larger budgets (with lazy compaction) at quality.

- **30-minute sprint loop is operationally what Linus enables**: Each Worker session should be short enough to stay below degradation threshold. Episodic store carries continuity across sessions rather than a single long prompt. M4 `project_stateful` memory mode + episodic store + in-context cap policy (M5) collectively implement this.

## What's NOT applicable or dated

- **Mechanism names are Claude Code–specific**: `/context`, `/clear`, `/compact`, `/rewind`, `PreCompact` hook don't transfer. The **roles** (diagnostic, clear, compact, rewind, pre-compaction safety) do. Linus needs the same primitives with its own naming.

- **200K context window and ~147K degradation threshold are hosted-Claude specific**: Linus's local Workers have smaller windows (Qwen2.5-Coder 32K, Llama-3.1-8B 128K). Degradation thresholds are an empirical question per Worker. The principle (degradation begins well below nominal) generalizes; the numbers don't.

- **30-minute sprint cadence is pair-programming–specific**: Calibrated to a particular hosted-Claude workflow. Linus's Maestro/Worker dispatch is shorter-lived (seconds to minutes per call, not hours). The sprint pattern translates onto **session-level** continuity (Maestro/Dan envelope), not individual Worker calls.

## Cross-references

- **Garrison memory thread** (synthesis in `memory-synthesis.md`): The architectural counterpart arguing that recursive state and reliable history access are non-negotiable. Mughal is the operational proof.

- **LLM Wiki synthesis** on hot-cache pattern and write-back rule: Mughal's session-handoff file is essentially a hot-cache designed for session boundaries.

- **Skills and practices synthesis** on Worker spec discipline: targeted prompts (specific files + line ranges) match Mughal's advice on context efficiency through specificity.

- **CLAUDE.md lost-in-the-middle discussion**: Relates to why CLAUDE.md and early context are critical (they sink to weak-attention zones) and why the episodic store + per-call memory-mode router is essential.
