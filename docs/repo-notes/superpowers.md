# superpowers (`obra/superpowers`)

## 1. Purpose and scope

Superpowers is a methodology and plugin system for AI coding agents that enforces structured workflows across multiple agent platforms (Claude Code, Cursor, Copilot CLI, GitHub Copilot, etc.). It orchestrates agents through a series of composable skills: brainstorming, design refinement, plan-writing, test-driven development, subagent dispatch, and code review. Rather than agents jumping directly to implementation, Superpowers forces the agent to spec before building, isolating design feedback loops from implementation work. For Linus, this is directly applicable as a behavioral framework for Worker agents: the methodology ensures que any Worker handed a task follows a spec-first, test-first discipline before declaring work complete.

## 2. Architecture summary

Superpowers is a skill-based plugin distributed across multiple agent harnesses. Each skill is a markdown file (under 500 lines) containing instructions + YAML metadata defining when that skill auto-triggers. There are 15+ skills: foundational (brainstorming, writing-plans, executing-plans), testing (test-driven-development, systematic-debugging), collaboration (subagent-driven-development, dispatching-parallel-agents), and finishing (requesting-code-review, finishing-a-development-branch). Skills use progressive disclosure: agent loads only names at startup; full content activates when task context matches a trigger (e.g., "let's build something" triggers brainstorming). The system enforces RED-GREEN-REFACTOR, YAGNI, DRY, and two-stage review (spec compliance first, code quality second). Zero-dependency design by principle — no third-party libs allowed in core.

## 3. What's reusable in Linus

The subagent-driven-development pattern is directly portable to Linus Phase 2a (Worker orchestration). A Worker handed a well-specified task should automatically invoke check-plan, implement-task, review-against-plan, and report-completion — exactly what Superpowers does. The RED-GREEN-REFACTOR discipline for test-driven development is a 1-to-1 skill Linus can use verbatim. The progressive-disclosure pattern (metadata-first, lazy-load full content) is architecturally sound for a large skill library; Linus can steal the triggering mechanism and YAML metadata shape. The finishing-workflow (merge/PR decision, worktree cleanup) maps cleanly onto Linus branch discipline (see BRANCHING.md).

## 4. What's inspiration only

The marketplace distribution model (per-harness plugin registration, skill auto-discovery) is specific to Claude Code's plugin system and won't transfer as-is to future Linus frontends. The multi-harness install logic (auto-detect Codex, Cursor, VS Code, etc.) is out of scope for Linus Phase 1-2 but becomes relevant if Linus someday exposes Workers across multiple frontends. The "human partner" language and specific red-flag rationalization lists are finely tuned for agent behavior shaping — reuse the pattern, not the prose.

## 5. What's incompatible or out of scope

Superpowers is agent-facing, not agent-building — it shapes behavior after an agent is already running. Linus Phase 1-2 is about building the orchestration backend; Worker behavior shaping comes at Phase 3+. The 94% PR rejection rate enforcement and contributor-gate patterns (strict AGENTS.md requirements) are org-specific and don't apply to internal Linus Workers. The platform-specific harness installation code is dead weight for a local system.

## 6. Recommendation: **Study (Phase 2a)**

Extract the skill template (metadata format, progressive disclosure, trigger mechanism) and subagent-driven-development workflow as reference designs for Phase 2a's Worker task dispatch. Don't integrate the full plugin system; cherry-pick the behavioral patterns. Run a spike: implement one Worker skill (test-driven-development) in Linus's style and measure how much of Superpowers' methodology transfers cleanly.

## 7. Questions for Dan

- **Subagent review gates.** Superpowers does two-stage review (spec compliance, then code quality) before marking work complete. Should Linus Workers do the same, or does Dan review once at the end-of-task level?
- **RED-GREEN-REFACTOR enforcement.** Superpowers deletes code written before tests and enforces TDD strictly. Is this the standard Dan wants Linus Workers to follow, or does it depend on task type (tests required vs. exploratory)?
- **Marketplace vs. embedded skills.** Superpowers distributes skills via per-harness marketplaces. Should Linus Phase 2a bundle Worker skills in the codebase (simpler for a local system), or build skill discovery and auto-update infrastructure early?
- **Design-review loops.** Superpowers gates implementation on design approval. For Linus Workers, should every task spec require Dan sign-off before implementation starts, or only for high-risk work (e.g., knowledge-graph changes)?
