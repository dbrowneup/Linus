# Changelog

All notable changes to Linus are recorded here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); each version is a git tag on `main`.

## [0.5.0] — 2026-06-02

First public-substrate release: a working local AI orchestration backend on Apple Silicon. The
corpus-scale citation-grounded RAG marquee is intentionally deferred to v0.6.0 (see Notes).

### Added

- Anthropic-compatible `POST /v1/messages` alongside OpenAI `POST /v1/chat/completions`
  (DEC-0056), both with SSE streaming and a multi-iteration tool-call loop.
- Server-side session persistence (SQLite WAL) with session endpoints.
- fastmcp-based tool registry; KB read-only tools (`search_papers`, `get_paper`),
  `papers.ingest_arxiv`, and a direct `POST /v1/tools/{name}/invoke` route.
- Five-layer memory pillar v0 (DEC-0028): episodic SQLite store, append-only JSONL audit log,
  content hashing.
- Path-validating sandbox (`SandboxFS`) enforcing the SAFETY.md Tier 0/1 contract (TOCTOU +
  symlink-escape hardened).
- Grounding/rigor gate (`knowledge/rigor.py`, DEC-0059) with KB- and NCBI-derived entity backends.
- Loud degradation: `/healthz` reports `effective_state` + `degradations[]` with actionable
  remediation (DEC-0060).
- Network-policy framework: per-tool `network_policy`, audit-log `network_egress[]`, `/healthz`
  reachability for `online_*` tools (DEC-0061); first instance `entity_ncbi.lookup`.
- Streamlit personal UI: landing + 7 pages (chat, corpus stats, cluster explorer, paper graph,
  knowledge graph, search, paper-qa) over KnowledgeBase outputs.
- paper-qa integration, now scoped as an optional "few named papers" deep-dive tool.

### Fixed (2026-06-02 substrate hardening)

- `/healthz` `kb_outputs` check resolves cluster artifacts under `outputs/clusters/` (PR #138).
- Cluster Explorer renders KB topic names instead of raw dicts (PR #139).
- paper-qa now ingests its papers directory before querying (was an empty-`Docs` no-op).
- Core navigational docs trued up to reality (ROADMAP status board, ARCHITECTURE, CLAUDE.md;
  PR #137).

### Notes

- **Corpus-scale RAG is a v0.6.0 deliverable, by design.** Live testing showed paper-qa is
  structurally too slow as a corpus engine (~11 LLM calls/query + re-embedding full text every
  process). The v0.6.0 marquee is a Linus-native persistent full-text-chunk RAG substrate — see
  [`docs/specs/2026-06-02-paperqa-evaluation-and-linus-native-rag.md`](docs/specs/2026-06-02-paperqa-evaluation-and-linus-native-rag.md).
- Test suites at tag time: hermetic **704** (~6s), integration **77** (~11s).

## [0.4.0] — 2026-05-19

Phase 2a MVP: FastAPI orchestration backend with OpenAI-compatible chat completions, Ollama
worker engine, tool registry + KB read-only adapter, memory v0, sandbox, and the initial
Streamlit UI. First non-prerelease tag.

## [0.3.0] · [0.2.0] · [0.1.0] — 2026-04 → 2026-05

Foundation and recon phases: repo scaffolding and environment, the core documentation set
(VISION / ARCHITECTURE / ROADMAP / SAFETY / DECISIONS / GLOSSARY), the repo-note and paper-note
corpus, the thematic + cluster syntheses, and the ADR series (DEC-0001 onward). See `git log` and
`DECISIONS.md` for detail.

[0.5.0]: https://github.com/dbrowneup/Linus/releases/tag/v0.5.0
[0.4.0]: https://github.com/dbrowneup/Linus/releases/tag/v0.4.0
