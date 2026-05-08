# llmwiki-cli (`doum1004/llmwiki-cli`)

## 1. Purpose and scope

llmwiki-cli is a deliberately tiny CLI — `wiki` (with `llmwiki` as a fallback alias) — that lets an LLM agent (Claude
Code, Codex, etc.) build and maintain a personal markdown knowledge base on disk. The CLI is "the hands": it reads,
writes, searches, lints, and surfaces the wikilink graph; the LLM is "the brain" and decides what to write. The hard
rule, repeated in both README and `CLAUDE.md`, is that the CLI never calls any LLM API itself and has no Git, cloud, or
vector backend — it is a pure filesystem tool over markdown with YAML frontmatter, plus a tiny global registry at
`~/.config/llmwiki/`. It is one of eleven independent implementations of Karpathy's "LLM Wiki" pattern in this
collection, and within that group it occupies the "thinnest possible agent-facing CLI" slot.

## 2. Architecture summary

Single-process Bun/Node CLI in TypeScript, ~14 commands wired with `commander`. Entry point is `src/index.ts`, which
registers each command as a `makeXxxCommand()` factory and uses a `preAction` hook to resolve the active wiki and inject
a `WikiContext` carrying a `StorageProvider`. Resolution order: `--wiki` flag → cwd `.llmwiki.yaml` → walk up parent
directories → registry default. All page I/O goes through the `StorageProvider` interface in `src/lib/storage.ts`; the
only implementation is `WikiManager` in `src/lib/wiki.ts`, rooted at the wiki directory. Supporting modules:
`frontmatter.ts` (YAML detect/parse/emit), `link-parser.ts` (wikilink extraction and graph build), `index-manager.ts`
(upserts the master `wiki/index.md` on every `wiki write` under `wiki/*`), `search.ts` (term-frequency ranking, no
embeddings), `templates.ts` (scaffolds `SCHEMA.md`, `index.md`, and — as drop-in strings — a GitHub Actions workflow
plus `build-graph.js`/`build-site.js` that publish a d3-force link graph to GitHub Pages). Dependencies are just
`commander` and `js-yaml`. The write path is unusual and worth flagging: `wiki write <path>` reads a JSON object from
stdin, validates fields, writes frontmatter+body, and there is intentionally no edit/append/index command — agents must
`wiki read` → mutate → `wiki write` the full JSON.

## 3. What's reusable in Linus

The pieces worth lifting for the Phase 2 KnowledgeBase pillar are conceptual, not code. The
`StorageProvider`/`WikiManager` split is a clean abstraction the KnowledgeBase ingest path could mirror so the same
agent commands work over filesystem today and a Qdrant- or SQLite-backed store later. The "JSON-on-stdin write,
full-rewrite-only, index auto-upsert" contract is a remarkably small but agent-friendly tool surface that Linus's tool
registry can copy verbatim — five filesystem verbs plus `lint`/`links`/`backlinks`/`orphans` is genuinely enough for an
agent to maintain a graph of notes, and it dodges the "agents make tiny patch edits and corrupt frontmatter" failure
mode. Compared to its likely upstream `llmwiki` — which ships an api+converter+mcp+ web+supabase stack with
`docker-compose.yml` — llmwiki-cli is the same idea stripped to a single-file npm install, which matches Linus's
Algorithm-step-2 instinct. The d3-force visualization is implemented as self-contained scripts in `templates.ts`
(extractable via `bun scripts/generate-viz-scripts.ts`) and could be borrowed standalone for KnowledgeBase graph
inspection without adopting any of the CLI.

## 4. What's inspiration only

Multi-wiki registry, the `wiki skill` self-documenting command (the canonical SKILL_GUIDE lives in
`src/commands/skill.ts`), and the scaffolded `SCHEMA.md` that teaches the agent the conventions on first contact are
nice patterns but not things Linus needs to embed. The contrast with sibling `swarmvault` is sharp and instructive:
swarmvault is a pnpm monorepo with engine/viewer/cli packages, biome+lefthook+playwright, multiple live-smoke lanes
against Neo4j/Ollama/OpenAI/Anthropic, and a `clawhub` skill-publishing pipeline — roughly two orders of magnitude more
surface area for the same Karpathy idea. llmwiki-cli's distinctness is exactly the absence of all that: two runtime
deps, no graph DB, no provider abstraction over LLMs, no version control opinions. If Linus ever wants a "minimal viable
wiki tool to point a Worker at," this is the reference shape; if it wants a fully-engineered platform, swarmvault is.

## 5. What's incompatible or out of scope

The full-page-rewrite write contract is fine for small agent-curated wikis but will be a problem at KnowledgeBase scale
(thousands of paper summaries, large bodies, frequent small updates) — Linus would need an append/patch path before this
contract scaled. Search is term-frequency only, no embeddings, no semantic recall — fine for a few hundred pages,
useless against the Phase 2 paper corpus. Multi-wiki state lives in `~/.config/llmwiki/registry.yaml`, which collides
with Linus owning its own session/state store. The optional GitHub Pages graph viz assumes a public repo and Actions
runner, neither of which fits a private local assistant. Bun is fine in dev but the published artifact targets Node, so
there's no Apple-Silicon-specific acceleration story here — this is a plain Node CLI.

## 6. Recommendation: **Study**

Read `src/index.ts`, `src/lib/storage.ts`, `src/lib/wiki.ts`, `src/lib/index-manager.ts`, and `src/commands/write.ts`
before designing the Phase 2 KnowledgeBase tool surface. Lift the StorageProvider abstraction and the JSON-stdin write
contract conceptually; do not vendor the package or take it as a runtime dependency. Revisit only if Phase 5 surfaces a
real need for a separate "personal notes wiki" distinct from the paper-corpus KnowledgeBase, in which case
`npm install -g llmwiki-cli` is a 30-second adoption.

## 7. Questions for Dan

1. **Tool-surface minimalism for KB.** llmwiki-cli's full agent surface is ~14 commands, two of which (`read`, `write`)
   do most of the work. Is that the right ceiling for the Phase 2 KnowledgeBase tool registry, or do you expect Linus
   tools to be richer (chunked retrieval, citation, structured-query) from day one?
2. **Full-rewrite vs patch semantics.** The "always rewrite the full page from JSON" contract trades efficiency for
   agent reliability. For KnowledgeBase paper summaries this is probably fine; for synthesis notes that grow over time
   it gets expensive. Want Linus's KB write tool to follow this contract or support an append/patch variant?
3. **Personal wiki as a separate pillar.** Is there a Dan-personal-notes wiki use case that should be served by
   `llmwiki-cli` as a third-party tool alongside KnowledgeBase, or does everything funnel through the KnowledgeBase
   pillar?
4. **Karpathy-pattern convergence.** With eleven implementations of the same idea in `repos/`, do you want a single
   Maestro-authored synthesis ADR that picks one shape (this CLI, llmwiki's full stack, swarmvault's monorepo, a
   workflow-pattern from Group 3) as the Linus reference, or stay agnostic until Phase 2a forces a choice?
5. **d3-force graph viz.** The interactive graph is the most user-visible artifact in this repo. Worth extracting as a
   standalone KnowledgeBase visualization in Phase 2, or noise relative to Streamlit + future openclaw front-ends?
