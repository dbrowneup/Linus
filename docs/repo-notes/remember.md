# remember (`remember-md/remember`)

## 1. Purpose and scope

Remember.md is a "second brain" plugin for **OpenClaw and Claude Code** by Gabi Fratica (codez.ro), distributed as the
npm package `@remember-md/remember` and as a Claude-Code plugin via the `remember-md` marketplace. It positions itself
explicitly against the flat key-value memory built into Claude Code, Cursor, and OpenClaw: instead of opaque notes
locked inside one tool, it materialises a structured Obsidian-compatible vault under `~/remember/` that any AI tool can
read and write. The vault is organised by entity type — `People/`, `Projects/`, `Notes/`, `Tasks/`, `Journal/`,
`Areas/`, `Resources/`, `Inbox/`, `Templates/`, `Archive/` — and the plugin's job is to (a) inject a `Persona.md` into
every session start, (b) capture "remember this: ..." utterances into the right file using a routing rulebook, and (c)
retroactively process months of past Claude Code `~/.claude/projects/*.jsonl` transcripts and OpenClaw
`~/.openclaw/workspace/memory/*.md` files into the same brain. For Linus, this is the first repo in the eight-way memory
survey that is shaped like a human-curated Obsidian vault rather than a pure agent retrieval store, and the first that
is dual-targeted at OpenClaw — the Phase 5 front-end of record.

## 2. Architecture summary

A small Node package: `index.js` (~135 lines) is the OpenClaw plugin entry point that registers a `session_start` hook
injecting a truncated `Persona.md` (last 20 evidence lines) and two MCP-style tools (`remember_brain_dump_context`,
`remember_brain_index`). Claude Code integration is parallel and separate: a `.claude-plugin/plugin.json` declares the
plugin, `hooks/hooks.json` wires `SessionStart` and `UserPromptSubmit` to `scripts/session_start.js` and
`scripts/user_prompt.js`, and four `skills/<name>/SKILL.md` files (`init`, `process`, `remember`, `status`) implement
the slash commands. The same scripts back both surfaces. `scripts/extract.js` is the heart of the retroactive-processing
path: it walks Claude Code's `.jsonl` transcripts and OpenClaw's `.md` memory files, dedupes via a per-source
processed-set in `~/.local/state/remember/`, strips noise prefixes (`<system->`, `<command-name>`, `<local-command->`),
and emits markdown fit for the LLM to extract entities from. The "entity schema" is _not_ a code-level type system — it
is a **markdown convention enforced by the rulebook in `REMEMBER.md`**: People files carry `role`, `relationship`,
`last_contact` frontmatter and `## Who` / `## Notes to Remember` / `## Interactions` sections; Decisions live at
`Projects/<project>/decisions/YYYY-MM-DD-<topic>.md` with `tags: [decision]`; Meetings carry `attendees`; Tasks split
into a global `Tasks/tasks.md` (`## Focus` max 10, `## Next Up` max 15) and per-project `tasks.md` backlogs; everything
cross-links via `[[wikilinks]]` so Obsidian's backlinks panel does the reverse-link work for free. The storage substrate
is plain markdown files; persistence is the user's git repo or filesystem, and there is no SQLite or vector index.

## 3. What's reusable in Linus

The **Persona.md pattern** — a single small file injected into every session that captures evolving user preferences,
naming conventions, and code style — is directly reusable as Layer E (long-term semantic memory in the
memory-architecture spec; renamed from Layer D per DEC-0052, when investigation memory took the Layer D slot). It is the
simplest, most legible implementation of "the model learns how I work" that any of the eight memory repos in this survey
offers, and it would slot into Linus's `linus.memory.persona.read()` contract with very little adaptation. The
**REMEMBER.md cascading rulebook** (global rules, per-project overrides, named sections that either append-to or
`Override:`-replace defaults) is a clean precedent for how Linus's tool registry might let users customise routing
without forking plugin code. The **session-start hook + brain-index tool** shape (`remember_brain_index` returns a
compact tree of all entities for the agent to ground against) is exactly the kind of pre-prompt context-injection
Linus's orchestration layer needs in Phase 2a, and the implementation is ~200 lines of Node — a useful reference for
sizing.

## 4. What's inspiration only

The **typed-vault-as-API** idea is the meaningful differentiator and the part to study, not vendor. Compared to
`openaugi` (sibling: Obsidian-as-graph-substrate, focuses on extracting graph structure from existing vaults) and
`memex` (sibling: vault-shaped but more focused on note-capture-and-search), Remember's distinguishing move is its
**opinionated entity ontology baked into the routing rules rather than the data model** — there is no schema file and no
validator; the ontology lives entirely in `REMEMBER.md` prose and the LLM is trusted to obey it. This is fundamentally a
_prompt-engineering approach to typed memory_, not a database approach. For Linus's DEC-0029 substrate (SQLite + content
hashes + git), this is the wrong commitment — Linus needs verifiable types and content hashes Workers cannot lie about.
The retroactive `/remember:process` workflow that scans months of `.jsonl` transcripts is also inspirational: Linus will
eventually want to backfill Layer C episodic memory from existing Claude Code session logs, and `scripts/extract.js` is
a working reference for how to walk those transcripts, strip noise, and dedupe.

## 5. What's incompatible or out of scope

The whole architecture is JavaScript inside the Claude Code / OpenClaw plugin envelope; Linus's memory layer is Python
in `src/linus/memory/` and the Worker dispatch path. Importing Remember as a dependency does not make sense — Linus's
orchestration layer needs to _own_ memory writes, not delegate them to a plugin running inside a front-end that may or
may not be active. The lack of content hashes, the lack of any concurrency story (two front-ends writing the same
`Tasks/tasks.md` at once is undefined behaviour), and the trust-the-LLM-to-route approach all violate DEC-0029's audit
requirements. The `Persona.md`-as-evidence-log approach is also unbounded by trust level — a hallucinated "evidence
line" gets appended just as readily as a real one, with no `trust_level` tagging analogous to DEC-0030's scratchpad
segments. The Obsidian compatibility, while attractive for Dan personally, is a UX feature, not an architectural one —
the same vault could be regenerated from Linus's SQLite store if a markdown export tool is desired.

## 6. Recommendation: **Study**

Read `index.js`, `scripts/extract.js`, and the `REMEMBER.md` rulebook before finalising the Phase 2a
`linus.memory.persona` and `linus.memory.episodic.recall_session` implementations. Borrow the Persona.md
single-file-injection pattern explicitly (note it as prior art in the relevant ADR; the relationship to Layer E
(semantic, renumbered from Layer D per DEC-0052) is the load-bearing one). Borrow the `extract.js`
Claude-Code-transcript walker as reference for the eventual backfill-from-history tool. Do **not** vendor the package,
do **not** install the plugin alongside Linus during Phase 2 (it would race Linus on memory writes), and revisit only if
Phase 5 OpenClaw integration surfaces a need for a markdown-vault export of Linus's episodic store — at which point the
routing-rulebook concept is a candidate for the export's organisational schema.

## 7. Questions for Dan

1. **Persona vs trust-level scratchpad.** Remember's `Persona.md` is unbounded — every observation gets appended as an
   "evidence line" with no provenance. DEC-0030 mandates trust levels on scratchpad segments. Should Linus's Layer E
   persona (semantic; renumbered from Layer D per DEC-0052) inherit the same trust-level tagging, or is Persona-class
   data (style preferences, naming conventions) always trust=high by definition? _Partially resolved (DEC-0030, see
   [answered-questions.md](../questions/answered-questions.md)): DEC-0030 mandates trust-level tagging on scratchpad
   segments; persona-class data trust policy TBD in Phase 2a memory spec._
2. **Markdown vault as Layer C export.** SQLite is the source of truth for episodic memory (DEC-0029), but a read-only
   markdown-vault projection would let Dan browse memory in Obsidian and let openclaw see memory without speaking SQL.
   Worth a small export-tool spike in Phase 2b, or premature?
3. **Retroactive backfill from `~/.claude/projects/*.jsonl`.** Dan has months of Claude Code transcripts already.
   Remember's `extract.js` shows the walker works. Is backfilling Linus's Layer C from this corpus a Phase 2b
   deliverable, or a Phase 3 "knowledge & parallel agents" item?
4. **OpenClaw plugin co-existence.** If Dan installs Remember.md inside OpenClaw for personal Obsidian-vault curation,
   and Linus also writes memory through its own pathway, the two are independent stores with no sync. Is that acceptable
   separation, or does this argue for Linus owning the only memory write-path and Remember-the-tool being uninstalled
   once Phase 2a ships?
5. **Differentiation gap with `openaugi` / `memex`.** Remember's distinguishing move is the routing-rulebook ontology;
   `openaugi` and `memex` solve adjacent problems (graph extraction from vaults, capture-and-search). Are any of the
   three sibling repos worth installing in parallel for a week of personal use to test the Obsidian-vault pattern in
   practice, or is the survey enough?
