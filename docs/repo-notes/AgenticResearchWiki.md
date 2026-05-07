# AgenticResearchWiki (`Tencent/AgenticResearchWiki`)

## 1. Purpose and scope

AgenticResearchWiki is a **forkable Markdown wiki skeleton plus a `CLAUDE.md` / `AGENTS.md` pair** designed to give a
coding agent (Claude Code, Codex CLI, Cursor) the same project context the human researcher has. It is explicitly
positioned for AI-research / long-horizon projects where data, training and eval live in different repos and where the
agent otherwise starts every conversation from zero. The value proposition is not a server, an inference engine, or a
runtime — it is the **directory layout, the page templates, the navigation rules in `CLAUDE.md`, and the convention that
the agent writes its own results back into the wiki** so the next session inherits them. For Linus this is a
Phase-3-relevant artifact: it is one of the cleanest worked examples of "agent-native project memory via a Markdown
graph," and it sits next to the KnowledgeBase pillar and the still-open Memory Architecture spec.

## 2. Content overview

The skeleton is small and deliberate. At the root: `Overview.md` (the single entry point — project goal, current
main-line method, code/data/output paths, task navigation, "investigated, not adopted"), `CLAUDE.md` and an identical
`AGENTS.md` (28 lines each — reading order, "do NOT read by default" list, `{{...}}` placeholder semantics,
doc-update-skill invocation rule). Five module directories each ship with an `Overview` and a `Records/` subfolder:
`Storyline/` (Introduction, RelatedWork, Target — long-form narrative split out of Overview), `Data/` (DataOverview),
`Training/` (TrainingOverview + Records/), `Eval/` (EvalOverview), `ResearchNotes/` (ResearchNotesOverview, six topical
subdirs: Data/Models/Training/Eval/Benchmarks/RelatedPapers), `ExperimentalTracks/` (with `abandoned/` for
post-mortems), `Shared/` (cross-task technical notes — env, cluster). Inter-doc links use Obsidian-style `[[ ]]` syntax
and the recommended editor is Obsidian (for the graph view), but the README explicitly notes any plain-text editor works
because the agent treats `[[ ]]` as plain-text search. The `skills/` directory ships two ready-to-install Claude Code
Skills: `import-notes/SKILL.md` (113 lines — classify and file existing notes from a folder or inline paste into the
right wiki section) and `project-doc-update/SKILL.md` (64 lines — auto-applied whenever the agent touches docs, so new
content lands in the right directory with the right filename and the right backlinks). A complete Simplified Chinese
mirror lives under `zh-CN/`. Everything is MIT-licensed and intended to be forked verbatim, then rewritten in place for
a real project.

## 3. What's reusable in Linus

The skeleton itself is highly reusable as a **template for per-project subdirectories under `context/` or for
KnowledgeBase project workspaces**. The page-template / placeholder convention (`{{...}}` is an unfilled field with a
fill hint, never treated as content) is a small but excellent piece of agent-prompting craft and worth lifting verbatim
into Linus's own page templates. The "single Overview entry point + progressive disclosure + write-back loop" pattern
directly informs the still-open Memory Architecture spec — this is one of the cleanest published examples of the
journal/index/synthesis split that the recent memory synthesis docs argue Linus needs. The two bundled Skills
(`import-notes`, `project-doc-update`) are drop-in-installable into `~/.claude/skills/` today and would help Dan
classify the existing `context/notes/` and `context/threads/` material without writing custom glue. Compared to its
sibling `agentic-wiki-builder` (which reportedly automates wiki _construction_ from a corpus), AgenticResearchWiki is
the opposite move: humans start the wiki, the agent inherits it and maintains it.

## 4. What's inspiration only

The Obsidian graph view, the symlink-everything multi-repo layout (docs repo as root, training / data / eval repos
symlinked in), and the Tencent-internal-cluster framing (8-GPU launches, DeepSpeed ZeRO, A100 references in the
illustrative example) do not transfer to Linus's M1 Max single-machine reality. The pattern of `cd`-ing the agent into a
docs repo so `CLAUDE.md` auto-loads is already how Claude Code works in the Linus repo today; we don't need to copy the
layout, only the page conventions. Compared to the similarly-named `llm-research-wiki`, AgenticResearchWiki is narrower
and more opinionated: it is _a research project's wiki_, not a _wiki of LLM research_; the audience is one team running
one long-horizon project, not the open-source community indexing a field. Pick from the skeleton à la carte — Overview
template, placeholder convention, progressive-disclosure rules, the two skills — and leave the rest.

## 5. What's incompatible or out of scope

There is no code to run, no inference layer, no benchmarks, no tests. The repo is documentation and conventions. The
"skills" are Claude Code Skills (markdown SKILL.md files), not executable Linus tools, so they don't slot into the Phase
2a tool registry — they live in the harness layer alongside Claude Code itself. The Obsidian graph view and the `[[ ]]`
link syntax are not parsed by anything in Linus today; they would need a small renderer (or just acceptance that links
resolve via grep). The repo's framing assumes one wiki per project, while Linus's KnowledgeBase pillar is explicitly
cross-project. Some adaptation work is needed to decide whether each Linus phase / experiment gets its own mini-wiki or
whether the convention collapses into the existing `docs/` + `experiments/` split.

## 6. Recommendation: **Study**

Read it once, then steal the four pieces that are clearly load-bearing: (a) the `Overview.md` template structure, (b)
the `{{placeholder}}` convention with its three-rule disposal logic, (c) the "do NOT read by default" allowlist pattern
in `CLAUDE.md`, and (d) the two Skills (install into `~/.claude/skills/` and try them on `context/notes/`). Do not fork
the repo as Linus's wiki — Linus's `docs/` already plays that role and the structure is too research-team specific.
Revisit during the Memory Architecture spec finalization (the synthesis notes already cite this kind of write-back loop
as a target pattern) and during Phase 3 when KnowledgeBase project workspaces get designed.

## 7. Questions for Dan

- **Page templates for `docs/`.** Want to lift the `Overview.md` template + `{{...}}` placeholder convention into
  Linus's `docs/` page-template kit, or keep `docs/` informal and reserve this only for per-project workspaces under
  `context/`?

- **Install the two Skills.** `import-notes` and `project-doc-update` are user-level installable today
  (`cp -r skills/* ~/.claude/skills/`). Worth doing as a Phase 1 quality-of-life experiment on `context/notes/`, or
  defer until Memory Architecture lands?

- **Differentiator check vs. siblings.** I distinguished AgenticResearchWiki from `llm-research-wiki` (research-of-LLMs
  vs. research-via-LLMs) and `agentic-wiki-builder` (agent-maintained vs. agent-constructed) on README evidence alone.
  Once the other two notes land, want me to revisit and tighten the contrast?

- _Resolved (DEC-0028, DEC-0039, see [answered-questions.md](../questions/answered-questions.md)): Memory Architecture spec (layers A–E, hybrid episodic schema) is the canonical Linus write-back pattern; AgenticResearchWiki is a useful worked example reference._

- **Per-experiment wikis.** Tencent's framing is one wiki per project. Linus has many concurrent experiments under
  `experiments/`. Does each experiment get a mini-wiki, or does this convention only kick in for multi-month efforts
  (Phase 6 fine-tuning, Phase 4 data-sovereignty datasets)?
