# claude-code-guide (`zebbern/claude-code-guide`)

## 1. Purpose and scope

claude-code-guide is a community-curated reference for Claude Code itself: a 3,700-line README that maps the harness's
slash commands, environment variables, hooks, plugin system, MCP wiring, sandbox modes, sub-agents, and worktree
isolation, plus three sibling collections — 106 role-specific agent personas under `agents/`, 29 security-focused SKILL
modules under `skills/`, and three CLAUDE.md guideline collections under `guides/` (zebbern's, Sabrina's, and a
multi-stack "CLAUDE.md Collection" covering Django, Rails, React, Vue, TypeScript, Python, Laravel, security, testing,
optimizers, orchestrators). The repo is a packaged crowd memory of how working practitioners configure and instruct
Claude Code; for Linus it is interesting on two axes: as a reference for what surfaces Linus's own future front-end
should expose, and as a quarry of agent-persona shapes and CLAUDE.md conventions worth lifting (or explicitly rejecting)
into Linus's skills-and-practices corpus.

## 2. Architecture summary

Three orthogonal asset trees, each markdown-only and zero-dependency. (a) `README.md` is the harness encyclopedia —
documents Claude Code features that Maestro and Dan use day-to-day (slash commands, hooks, plan/fast/sandbox modes,
MCP, worktrees) and is kept in lockstep with the upstream `CHANGELOG.md` (~140 versions tracked). (b) `agents/` ships
106 sub-agent persona files in YAML-frontmatter + role-prose shape: each defines `name`, `description`, allowed `tools`
(Read/Write/Edit/Bash/Glob/Grep), then enumerates "When invoked", checklists (e.g., code-reviewer's "Cyclomatic
complexity < 10 maintained"), and per-domain procedures. Roles span specialized verticals (blockchain-developer,
fintech-engineer, embedded-systems), platform engineers (kubernetes-specialist, terraform-engineer, devops-incident-
responder), language pros (rust-engineer, python-pro, golang-pro), and orchestration roles (agent-organizer,
context-manager, multi-agent-coordinator, workflow-orchestrator, task-distributor). (c) `skills/` follows Anthropic's
SKILL.md shape (YAML metadata + Purpose + Inputs/Prerequisites + procedure) but is heavily slanted toward red-team /
pentest workflows (sql-injection-testing, sqlmap, metasploit, AD attacks, privilege escalation, Burp Suite). (d)
`guides/` collects three rule-coded CLAUDE.md exemplars — MUST/SHOULD/SHOULD-NOT discipline modeled on aviation
checklists, with TDD cadences, function-length caps, conventional-commits requirements, and explicit quality gates
(`prettier --check` + `eslint` + `tsc --noEmit`).

## 3. What's reusable in Linus

The agent-persona file shape is directly applicable to the Phase 3 spawner (DEC-0050) and the role-as-first-class-type
contract: Linus's own `Role` definitions can adopt the same `name` + `description` + `tools` frontmatter, "When
invoked" procedure list, and explicit checklists, then evolve toward the typed AgentReport contract (DEC-0051) on the
output side. The orchestration-flavored personas (`agent-organizer.md`, `context-manager.md`, `multi-agent-
coordinator.md`, `workflow-orchestrator.md`, `task-distributor.md`) are the closest external precedent for the
Maestro/Worker dispatch surface and worth a focused pass when the spawner moves from stub to implementation. The
MUST/SHOULD/SHOULD-NOT rule grammar from `guides/CLAUDE.md by zebbern` and `guides/CLAUDE.md by Sabrina` is a more
machine-checkable shape than the prose-paragraphs convention currently used in Linus's CLAUDE.md "Engineering
conventions" section; selectively lifting it for the most checkable rules (line-length, commit format, smoke-test
gating, hook bypass flow) would tighten enforceability without losing the reasoning-friendly prose elsewhere
(CLAUDE.md §Writing style for docs explicitly favors prose over bullet dumps for human-read docs, so this stays
selective). The README's documentation of Claude Code surfaces (hooks, plan mode, MCP, worktrees, sub-agents)
double-checks Linus's own coverage of these primitives — particularly the worktree section, which complements the
2026-05-08 worktree fan-out discipline write-up. A handful of skill files (e.g., `red-team-tools`, `network-101`)
are tangentially relevant if Linus ever needs internal-security-review workflows; treat as inspiration only for now.

## 4. What's inspiration only

The 106-persona breadth is aspirational: Linus does not need a fintech-engineer or wordpress-master role, and shipping
a stadium of personas would be a Phase 3 anti-pattern (more YAML to maintain than discipline to apply). Treat the
collection as a menu to draw 5-10 actually-useful Worker shapes from, not as a target to match. The CHANGELOG-mirroring
practice — keeping a community README synchronized with upstream Anthropic releases — is impressive curation but is
labor that Linus does not need to replicate; harness-level changelogs already live upstream. The "CLAUDE.md Collection"
sub-stacks (Django, Rails, React, Laravel, etc.) are useful exemplars of how language/framework conventions get
encoded, but Linus's own CLAUDE.md style (long-form prose explaining reasoning) is intentionally different and should
not converge on the rule-only Sabrina/zebbern shape across the whole document.

## 5. What's incompatible or out of scope

The skills tree is dominated by offensive-security workflows (SQL injection, privilege escalation, red-team
reconnaissance) which are explicitly out of scope for Linus's Phase 1-7 work and bump up against the biosecurity-tier
spirit of DEC-0047 even though that ADR scopes biology specifically — the reasoning ("don't help generate weaponizable
artifacts") generalizes to "don't industrialize attack tooling." The agent personas assume a generic Claude Code
deployment, not Linus's local-Worker substrate; their "Query context manager" / "Coordinate with X agent" steps presume
infrastructure Linus is still building. The MIT-licensed assets are reusable verbatim but the community-curation model
(open contributions, version-tracked README) is not the right shape for Linus's internal docs, which are owned by Dan
and Maestro and follow the curation protocol (DEC-0025) rather than open contribution.

## 6. Recommendation: **Study**

Mine the agent-persona shape and the orchestration-flavored personas for Phase 3 spawner inputs; mine the MUST/SHOULD
rule grammar from the guides for selective lifts into Linus's own conventions; cross-check the README's Claude Code
surface coverage against Linus's CLAUDE.md to surface any harness primitives not yet documented in Linus
(`docs/protocols/maestro-worker-protocol.md`, `docs/specs/phase3-spawner.md` are the natural destinations). Do not
integrate the persona library wholesale and do not adopt the security-skill workflows. Cluster: g11-agent-frameworks.
Primary thematic synthesis: skills-and-practices.

## 7. Questions for Dan

1. **Persona transplant target.** Of the 106 agent personas, which 5-10 map cleanly onto Phase 3 Worker roles Linus
   actually needs? The orchestration cluster (agent-organizer, context-manager, multi-agent-coordinator, workflow-
   orchestrator, task-distributor) is the most directly relevant; should the Phase 3 spawner spec
   (`docs/specs/phase3-spawner.md`) seed its Role catalogue from those?
2. **MUST/SHOULD rule grammar.** Is the rule-coded checklist style (zebbern's BP-1 / C-2 / T-1 / G-1 / S-1 / QG-1
   tags) worth an ADR seed for Linus's own conventions — applied selectively to the most checkable rules (function
   length, commit format, smoke-test gating, hook bypass flow) — or does it conflict with the prose-first writing
   style mandated by CLAUDE.md §Writing style for docs?
3. **CLAUDE.md addition candidates.** The README documents Claude Code primitives (sandbox modes, plan mode, worktree
   isolation, hooks, sub-agent invocation) at a level of operational detail that exceeds Linus's current CLAUDE.md
   coverage of those same primitives. Should the next planning-update round commission a sweep that pulls from this
   reference into Linus's own conventions and decision log?
4. **Maestro/Dan vs community surface.** How does the community guide's day-to-day Claude Code surface (plan mode, fast
   mode, slash-command vocabulary, hook patterns) differ from the surface Maestro and Dan actually use? Is there a
   gap-analysis worth running once before Phase 5 front-end work begins, so the eventual openclaw / claw-code-local
   surface inherits the practitioner-validated subset rather than re-deriving it?
