# prompt-vault (`AI-Engineer-Skool/prompt-vault`)

## 1. Purpose and scope

prompt-vault is a four-folder grab-bag of public prompts that accompany videos taught in the AI Engineering Skool
community. The README is two lines long and the entire repo is markdown plus a single GitHub Actions YAML — there is no
runtime, no server, no library, no MCP, no schema, no storage layer. It is a prompt library, not a memory system. The
four directories are `claude-md-memory-workflow/` (a self-updating CLAUDE.md GitHub Action),
`notion-db-to-technical-blog/` (a one-shot blog-generation prompt), `obisidian-knowledge-graph/` (an `AGENTS.md` plus
three sub-agent prompts for maintaining an Obsidian PARA vault), and `self-documenting-ai-agent/` (a
`.claude/commands/auto-document-agent.md` slash-command that asks Claude to read a branch diff and emit an ADR). Total
executable footprint: one weekly GitHub Action (`update-claude-md.yml`) that runs the `claude-md-review-prompt.md`
prompt against the repo it lives in and opens a PR with the resulting CLAUDE.md edit. Everything else is text intended
to be pasted into a chat or dropped into a `.claude/commands/` folder.

## 2. Content overview

`claude-md-memory-workflow` is the most operational artifact: a weekly cron-triggered Action that uses
`anthropics/claude-code-action@beta` with `mode: agent`, hands Claude a long structured prompt covering 12 review
dimensions (project overview, tech stack, commands, architecture, components, content schema, scripts, configs, SEO,
conventions, integrations), and lets it `Edit`/`MultiEdit` CLAUDE.md, then opens a labelled PR. The prompt is
Astro-blog-shaped (mentions `astro.config.mjs`, `src/pages/`, `src/content/`) and the README explicitly notes it must be
reworked per project. `obisidian-knowledge-graph` is the heaviest single subdirectory — `AGENTS.md` is a CLI-query
playbook of `rg`/`fd` recipes for auditing wikilink density, front-matter coverage, and PARA folder hygiene in an
Obsidian vault, plus three sub-agent prompts (`transcript_processing_agent.md` ~20 KB, `vault_connectivity_agent.md` ~9
KB, `persona_professional_seeking_ai_mastery.md` ~1 KB). `notion-db-to-technical-blog/` is a single
content-transformation prompt with strict "no code, no commands, no implementation detail" guard rails, designed to turn
Notion rows into 700-word conceptual posts that funnel viewers to YouTube. `self-documenting-ai-agent/` ships an
`adr-template.md` and a single slash-command that runs `git diff main`, decides whether the diff is architecturally
significant, and, if so, writes a new ADR using the template.

## 3. What's reusable in Linus

Almost nothing as substrate, but two prompts are usable as starting drafts. The `auto-document-agent.md` slash command
is a near-direct cousin of the workflow that produces our own per-file ADRs in `docs/adr/` — its decision rule ("skip
ADR for bug fixes, refactors, doc changes, config tweaks") is a sensible filter that we could lift verbatim into a
`/adr-from-diff` Linus skill once Phase 7's skills layer exists. The `update-claude-md.yml` Action shows the shape of a
"docs-stay-honest" cron we could copy for keeping CLAUDE.md, ROADMAP.md, and ARCHITECTURE.md from drifting against the
repo state, though the per-project specifics in the embedded prompt would need a full rewrite to match Linus's prose
conventions and the per-file ADR layout in `docs/adr/`. Neither is load-bearing; both are the kind of thing Maestro
could re-derive in a single session if needed.

## 4. What's inspiration only

Set against its Group 4 siblings — agentmemory, anamnesis, omega-memory, engram, remember, openaugi, memex —
prompt-vault is structurally a different shape. Those repos ship code (Python/TS), schemas, vector stores, MCP servers,
retrieval loops; prompt-vault ships prompts. The Obsidian playbook is the closest thing to "memory" in the repo, and it
is at best a methodology for keeping a human-curated knowledge graph well-linked, not a substrate Linus could call. The
`linus.memory.*` API laid out in `docs/specs/memory-architecture.md` (Layers A–D, SQLite + content hashes + git per
DEC-0029) has no surface area in this repo to compare against — there is nothing here that holds state across sessions
or hashes anything. Compared to a true memory implementation like (say) anamnesis or memex, prompt-vault sits in a
different category entirely: it is a prompt cookbook with a self-updating-docs gimmick, not memory infrastructure.

## 5. What's incompatible or out of scope

The Astro-shaped CLAUDE.md prompt is not transferable without rewriting; the Notion-to-blog prompt has no analogue use
case in Linus (we are not running a content funnel); the Obsidian playbook assumes a specific vault layout under
`/Users/ai-native-engineer/Documents/Vault/Vault` and a PARA/FINVA discipline that does not match this repo's structure.
None of these are blockers because none of them are dependencies — they are just text files we would not use.

## 6. Recommendation: **Ignore**

Skim once, lift the two prompt patterns above into a side note if Phase 7 wants them, and move on. Nothing here is on
the critical path for the memory pillar, and pinning the submodule would commit us to tracking a weekly-changing
prompt-cookbook for no engineering benefit. If Dan wants the auto-ADR or auto-CLAUDE.md cron, the cleanest path is to
write our own in `.github/workflows/` rather than vendor or fork this repo.

## 7. Questions for Dan

- **Auto-ADR cron.** The `auto-document-agent.md` pattern (run `git diff main` on a branch, emit an ADR if the change is
  architectural) would pair well with this repo's own DEC-NNNN discipline. Worth a small Phase 1c experiment to bolt
  onto our existing `.claude/settings.json` hooks, or premature?
- **Self-updating CLAUDE.md.** Would you want the weekly cron to keep CLAUDE.md honest against the repo, given how often
  we are amending it as the architecture decisions land? The risk is that an automated PR overwrites the careful prose
  style for a more mechanical bullet-style summary.
- **Obsidian playbook relevance.** Do you maintain (or plan to maintain) an Obsidian vault for `context/notes/` or the
  paper corpus? If yes, the `vault_connectivity_agent.md` and `transcript_processing_agent.md` prompts are concretely
  useful; if no, the entire `obisidian-knowledge-graph/` subdirectory is dead weight for Linus's purposes.
