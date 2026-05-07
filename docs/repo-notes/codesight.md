# codesight (`Houseofmvps/codesight`)

## 1. Purpose and scope

codesight (Kailesk Khumar) is an `npx`-installable CLI that scans a project root and emits a compiled "context map"
(`.codesight/CODESIGHT.md` plus per-domain files for routes, schema, components, libs, config, middleware, dep graph) so
an AI coding assistant can read one pre-digested file instead of spending 40-70K tokens glob/grep'ing the codebase from
scratch. Beyond the one-shot scan it ships an MCP server with 13 tools (scan, summary, routes-by-prefix,
schema-by-model, blast-radius, env, hot-files, events, coverage, refresh, plus three wiki tools), a "wiki mode" that
compiles per-subsystem articles à la Karpathy's LLM-wiki gist, and a `--mode knowledge` pass that does the same trick
over an Obsidian vault / ADR folder. Distribution is npm (claimed 4,000+ downloads); supported targets include Claude
Code, Cursor, Copilot, Codex, Windsurf, Cline, Aider — anything that reads markdown or speaks MCP. For Linus this is a
candidate to drop verbatim into the Phase 2/3 KB tool registry as the "instant codebase knowledge" primitive: install
once, point the MCP client at it, every Worker session starts with a structured map of whatever repo it is editing.

## 2. Architecture summary

A TypeScript Node project (`>=18`) with **literally zero runtime dependencies** — `package.json` has no `dependencies`
field at all, only three devDeps (`typescript`, `tsx`, `@types/node`). The "AST precision" trick is opportunistic
borrowing: when scanning a project that has TypeScript installed in its own `node_modules`, codesight `require`'s the
host project's TS compiler API to parse routes/schema/components structurally. When TS is absent, it falls back to
hand-tuned regex. For Python and Go this is taken further — `src/ast/extract-python.ts` actually shells out to the
system `python3` with an inline script that uses the stdlib `ast` module to parse FastAPI/Flask decorators, Django
`urlpatterns`, and SQLAlchemy `Column` definitions; `extract-go.ts` does the analogous trick for Gin/Echo/Fiber. The
README's "AST for TS, regex for everything else" line undersells this. Eight detectors
(`detectors/{routes, schema, components, libs, config, middleware, graph, events}.ts`) plus
contracts/blast-radius/coverage/openapi/graphql side modules run in parallel in `core.ts`, hand off to `formatter.ts`
which writes the markdown bundle. The MCP server (`src/mcp-server.ts`, 794 lines) is hand-rolled JSON-RPC 2.0 over stdio
with both framed and newline transports — no `@modelcontextprotocol/sdk` dependency. `routes.ts` alone is 1969 lines of
per-framework dispatch (33 framework detectors). Wiki articles are AST-derived, not LLM-derived: zero API calls, ~200ms
scan.

## 3. What's reusable in Linus

The whole binary is reusable as-is. Phase 2a Linus exposes an OpenAI-compatible endpoint; Phase 3 wires in a tool
registry. Adding codesight as one of the first registered tools is essentially a one-line MCP config — same shape as the
README's Claude Code snippet — and it gives every Worker process structured knowledge of whatever directory it is
operating in, without Linus having to write a single line of code-analysis logic. Compared to the closest sibling in
this group, **ontomics** (`EtienneChollet/ontomics`), the differentiators are: (a) codesight is structural and
deterministic (routes, ORM models, import graph) where ontomics is semantic and clustering-based (domain concepts,
naming conventions, behavioral similarity) — they answer different questions and are arguably complementary; (b)
codesight has no dependencies and starts in ~200ms with `npx`, where ontomics is a Rust+Python+TypeScript hybrid with a
heavier install path; (c) codesight's framework coverage is wide and shallow (33 web frameworks, 13 ORMs across 14
languages) where ontomics is narrow and deep (semantic indexing, vocabulary evolution, exportable artifacts). For
Linus's near-term need — "tell the Worker where the routes and models are in the repo it's editing" — codesight wins.
For long-term science use — "find all the functions across my pipelines that compute the same thing under different
names" — ontomics is the better fit. Both can register simultaneously in an MCP-based tool registry. The Python AST path
also means codesight handles Linus's own primarily-Python codebase reasonably well, not just the TS/JS world the README
markets toward. The wiki-mode pattern (AST-compiled persistent articles checked into git) is independently worth
stealing as a model for how Linus might surface KnowledgeBase corpus state to Workers between sessions.

## 4. What's inspiration only

The Roku/BrightScript/SceneGraph support is heroic and irrelevant. The HTML report dashboard is irrelevant — Linus has
Streamlit and eventually openclaw. The `--profile <tool>` config-file generators (CLAUDE.md, .cursorrules, codex.md,
AGENTS.md) are interesting prior art but Linus already has its own CLAUDE.md authored by Dan; auto-generated versions
would clobber the curated one. The benchmark-table style — every framework × stack with files/routes/models/ savings
columns — is a good model for how Linus's own benchmark suite (`benchmarks/dan_tasks/`) should report results.

## 5. What's incompatible or out of scope

Node runtime in the Linus stack: Linus is Python-first; pulling in a Node MCP server means `npm` becomes a runtime
dependency for one tool. The CLAUDE.md notes node/npm as installable inside the conda env but not currently required.
This is small but real — every additional language runtime is a maintenance surface. Single-maintainer single-vendor
risk: codesight is one person's project (Kailesk Khumar / Houseofmvps), MIT-licensed, ~9 months old, no listed sponsors.
The "4,000+ downloads" claim is monthly-ish from npm but the repo's contributor count is essentially one. The `--init`
and `--profile` flags will overwrite existing CLAUDE.md / AGENTS.md files; if used in the Linus repo they would destroy
the hand-written one — never run those flags inside the Linus tree. The wiki and knowledge modes write to `.codesight/`
which would need adding to `.gitignore` if codesight runs against the Linus repo itself, OR (per the README's intent)
committed deliberately as session-warmup context.

## 6. Recommendation: **Integrate**

Add codesight to the Phase 2/3 MCP tool registry once that registry exists. Concretely: `npm install -g codesight`
inside the linus conda env (or commit to `npx codesight` per-invocation), wire it into Linus's MCP client surface, let
Workers call `codesight_get_summary` / `codesight_get_routes` / `codesight_get_blast_radius` against whatever project
they're editing. Run it against a representative scientific Python repo (one of Dan's KnowledgeBase consumers, or the
Linus repo itself) before committing to it as a default — verify the Python AST extractor gives useful output on non-web
codebases (no FastAPI routes to find in a numerical-pipeline repo). Keep it out of the Linus root's own hooks until the
`--init` overwrite behavior is confirmed safe. Pair with ontomics rather than choose between them — they are
complementary, not competing.

## 7. Questions for Dan

- **Per-repo vs global install.** `npx codesight` resolves the package every invocation (the README warns about Codex
  hitting a 30s timeout because of this). Globally installing inside the linus conda env is faster but means a Node
  package lives in our env. Acceptable, or do we wait until there's a second reason to take that dependency?
- **Wiki artifacts in git.** codesight's value compounds when `.codesight/wiki/` is committed and consulted at session
  start (Karpathy-style). Are we willing to commit AI-context artifacts into the Linus repo, or treat them as
  per-session ephemera?
- **Codesight on non-web Python.** The detectors are tuned for web frameworks (routes, ORMs, components). On a pure
  numerical/scientific Python repo with no routes and no ORM, the output may be mostly the dependency graph and env
  vars. Is that still worth the tool slot, or should we bake a science-flavored variant later?
- **Differentiator I could not pin down.** I can distinguish codesight from ontomics confidently, but the line between
  codesight's wiki-mode and a vectorless/WeKnora retrieval pass is fuzzy when the source is markdown rather than code.
  Worth comparing those three explicitly in a follow-up note before Phase 3 retrieval design lands.
