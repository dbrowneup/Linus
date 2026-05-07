# hyalo (`ractive/hyalo`)

## 1. Purpose and scope

Hyalo is a Rust CLI for operating on a folder of markdown files with YAML frontmatter — Obsidian vaults, Zettelkastens,
docs sites — at scale, from a terminal or an LLM agent. It treats the vault as structured data (properties, tags,
`[[wikilinks]]`, markdown links, task checkboxes) rather than as text, and exposes that structure through `hyalo find`,
`hyalo set` / `remove` / `append`, `hyalo mv`, `hyalo links` (auto-link, fix), `hyalo lint` / `types`, `hyalo task`,
`hyalo summary` / `properties` / `tags`. The README explicitly cites Karpathy's "LLM-maintained wiki" tweet as the
motivating pattern: rather than asking the model the same questions repeatedly, an agent accumulates a persistent,
structured knowledgebase and uses hyalo as the safe, schema-aware editing surface. Built by ractive; AI-assisted under
human supervision (see the repo's `AI_NOTICE`); MIT-licensed; v0.14.0 as cloned. For Linus, this is candidate tooling
for the Phase 2 KnowledgeBase note layer (Dan's `context/notes/` → vault), the Phase 3 hybrid retrieval graph (every
`[[wikilink]]` and frontmatter relation is an edge), and the Crossing-3 "agent maintains its own wiki" loop.

## 2. Architecture summary

A small Rust workspace: `hyalo-core` (library — scanner, BM25 index, frontmatter parse, filter DSL, link graph, link
rewrite, auto-link, schema/types, snapshot index) and `hyalo-cli` (clap-based commands under `commands/`, dispatch,
output pipeline, `--jq` post-filter via `jaq`). Edition 2024; clippy `pedantic` enforced; release builds use
`codegen-units=1`, LTO, `panic=abort`, `strip`. Scanning uses `ignore` (gitignore-aware) and `rayon` for parallel file
walking; full-text search is BM25 with stemming via `rust-stemmers` and boolean operators (`AND`, `OR`, `-term`,
quotes); the property-filter DSL in `filter::parse` accepts `key=v`, `key!=v`, `key>v`/`>=`/`<`/`<=`, bare `key`
(exists), `!key` (absent), and regex `key~=/pattern/i` (with a Perl-style `=~` alias). `hyalo mv` does not just rename:
`link_rewrite::plan_mv` produces a `RewritePlan` of `Replacement`s across every file in the vault — wikilinks (including
aliases and section anchors), markdown links, and configured frontmatter properties (`[links] frontmatter_properties`) —
captures the source mtime _before_ planning to detect concurrent edits, and supports `--dry-run` to preview the full
diff before committing. `hyalo links auto` does the inverse: scans body text for unlinked mentions of known page titles
(filenames, frontmatter `title`, `aliases`) and converts them to wikilinks, skipping code blocks, existing links,
headings, and comment fences. A snapshot index (`.hyalo-index`, msgpack-serialized via `rmp-serde`) makes repeated
queries (CI, agent loops) effectively free; mutations patch the index in place. JSON is the default output format and is
the design point for agent consumption; `--format text` is the human/LLM-prose mode and the one `hyalo init --claude`
configures.

## 3. What's reusable in Linus

Most of it, as an external binary on the agent's PATH rather than a library Linus links. The Phase 2 KB design already
calls for a markdown-vault layer for Dan's notes; hyalo gives it a fast, structured, schema-validated frontend without
writing a line of Linus code. The schema/types system (per-`type` required fields, enum values, date/list/number types,
filename templates like `iterations/iteration-{n}-{slug}.md`) is precisely the shape Linus wants for note classes
(paper, thread, decision, experiment) and replaces the "design our own lint" placeholder in the `linus kb lint` sketch
lifted from Karpathy's `llm-research-wiki`. The `hyalo init --claude` integration installs two skills (`hyalo`,
`hyalo-tidy`) and a vault-scoped rule that teaches Claude Code to prefer hyalo commands over raw
`Read`/`Edit`/`Grep`/`Glob` — directly applicable when Maestro Claude works inside Dan's KnowledgeBase. For Phase 3
hybrid retrieval, hyalo's link graph (computed from wikilinks _and_ configured frontmatter properties) is a usable seed
for the KB graph layer without bringing in a heavier graph framework like `py3plex`. The snapshot index pattern is the
right answer for the agent-loop case where the same vault is queried hundreds of times in a session.

## 4. What's inspiration only

The dogfooding loop documented in the repo's `CLAUDE.md` — every project iteration is a markdown file in
`hyalo-knowledgebase/iterations/iteration-NN-slug.md` with required `title/type/date/status/branch/tags` frontmatter,
status lifecycle `planned → in-progress → completed → superseded`, branch naming `iter-N/slug` — is a ready-made
template for how Linus could run its own `experiments/` and `docs/adr/` directories under hyalo governance. Adopting
that structure verbatim would be over-fitting to one developer's workflow, but the convention that "an iteration = a
branch = a PR = one frontmatter-validated markdown file" is worth lifting. The Claude Code skill artifacts (`hyalo`,
`/hyalo-tidy`) are also a good model for what a Linus skill bundle should look like: auto-trigger by path scope,
idempotent install via `init`, clean removal via `deinit`.

## 5. What's incompatible or out of scope

The **named sibling** in this group is `keppi`, the other vault CLI. Two structural differences that matter for Linus's
choice: (1) hyalo is **Rust**, distributed as a single static binary via Homebrew/Scoop/winget/cargo with no runtime —
keppi is **Python** under `uv`/`pyproject.toml`, which means env management, slower cold starts, and a second
interpreter to keep alive next to the linus conda env; (2) hyalo's `mv` rewrites links across the entire vault as a
planned, dry-runnable transaction with concurrent-edit detection, and its `links auto` does the title-to-wikilink
direction — Dan should confirm which of those keppi actually does before picking. Hyalo is not a graph-analysis tool:
the link graph it computes is for `mv` rewrites, broken-link detection, and orphan reporting, not for centrality or
community detection (that's `py3plex`/`infranodus` territory). It is also not a content generator — it edits frontmatter
and links, not prose; body-content edits fall back to `Edit`/`Read` per the project's own CLAUDE.md. And it's a CLI:
there is no library API for embedding hyalo in-process from Python or Rust inside Linus; integration is shell-out, which
is fine for an agent tool but limits use as a core library.

## 6. Recommendation: **Integrate**

Install via Homebrew on M1, point `.hyalo.toml` at `context/notes/` (or a Phase-2 vault subfolder) with a Linus schema
(`paper`, `thread`, `decision`, `experiment`, `iteration`), run `hyalo init --claude` to drop the skills and
vault-scoped rule into `.claude/`, and use `hyalo` as the canonical edit/search interface for Linus's note layer. Worth
a short side-by-side with `keppi` (one hour, same five operations on the same sample vault) before declaring hyalo the
winner, but the Rust-binary distribution and the planned-rewrite `mv` are strong defaults. Defer any deeper integration
(calling hyalo from inside Linus orchestration code) until Phase 3, when the KB graph layer needs a producer.

## 7. Questions for Dan

- **Vault location.** Does Linus's note vault live at `context/notes/` (gitignored, personal), as a new top-level
  `vault/` (tracked but Dan-owned), or inside `modules/KnowledgeBase/` next to the paper corpus? Hyalo's `.hyalo.toml`
  has to point somewhere and the schema lives next to it.
- **hyalo vs keppi bake-off.** Want a 30-minute Phase-1 spike that runs the same five operations (find by tag, bulk set
  status, rename + link rewrite, lint with schema, summary) on a sample vault under both tools and writes the verdict as
  an ADR in `docs/adr/`?

  _Resolved (DEC-0026, see [answered-questions.md](../questions/answered-questions.md)): Both hyalo and keppi adopted
  as Phase 3 KB tooling layer (S26)._

- **Schema design.** The pmetal-style `[schema.types.iteration]` block is appealing for Linus's `experiments/` and
  `docs/adr/` directories. Adopt the iteration-file convention (`iter-NN-slug.md`,
  `planned → in-progress → completed → superseded`) for our work, or keep our looser status quo?
- **Claude Code integration scope.** `hyalo init --claude` writes a vault-scoped rule that overrides Maestro's default
  Read/Edit behavior. Comfortable with that landing in `.claude/` for `context/notes/**`, or do you want the override
  scoped tighter?
- **Phase 3 graph producer.** When the KB graph layer comes online, do we use hyalo's `link_graph` output as the seed
  (cheap, already computed) and add `py3plex`/`infranodus` analysis on top, or keep the graph layer hyalo-independent so
  the vault tooling stays swappable?
