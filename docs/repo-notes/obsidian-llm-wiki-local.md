# obsidian-llm-wiki-local (`kytmanov/obsidian-llm-wiki-local`)

## 1. Purpose and scope

`obsidian-llm-wiki-local` (PyPI: `obsidian-llm-wiki`, CLI: `olw`) is a working, polished implementation of Karpathy's
"LLM Wiki" pattern that turns an Obsidian vault into a self-improving wiki: drop a markdown file into `raw/`, the
pipeline ingests it with a fast model, compiles per-concept articles with a heavy model into `wiki/.drafts/`, and
publishes them to `wiki/` after human review. It targets local LLMs first — Ollama is the default and the README's "100%
locally" claim is the lead — and falls back to any OpenAI-compatible endpoint (LM Studio, vLLM, llama.cpp, Groq,
Together, Azure, …) only when the user explicitly switches. It is the only Group 3 sibling that ships as a
pip-installable tool with version 0.8.0, a CHANGELOG, CI badges, smoke-test scripts, and a setup wizard. For Linus, it
is the closest thing to "what a finished, opinionated personal-knowledge product built on a local Ollama Worker actually
looks like" — relevant to Phase 1 (Ollama-Worker baselines) and Phase 2 (KnowledgeBase v1 ingestion ergonomics).

## 2. Architecture summary

Pure Python 3.11+, ~10 KLOC, no langchain. The dependency list is intentionally small: `click`, `rich`, `pydantic`,
`pyyaml`, `httpx`, `watchdog`, `python-frontmatter`. Two LLM clients live behind a `LLMClientProtocol`:
`ollama_client.py` is a thin httpx wrapper on Ollama's `/api/tags`, `/api/generate`, `/api/embeddings`;
`openai_compat_client.py` covers everything else; `client_factory.build_client()` picks one based on
`config.effective_provider.name == "ollama"`. The pipeline lives in `pipeline/` with `ingest.py` (fast model extracts
concepts and writes a source-summary page), `compile.py` (heavy model writes one article per concept into
`wiki/.drafts/`), `review.py` (interactive approve/reject with diffs), `query.py` (index-routed Q&A without embeddings),
`lint.py`, `maintain.py`, and an `orchestrator.py` that chains them for `olw run`. State is a SQLite DB at
`.olw/state.db` tracking note lifecycle (new → ingested → compiled → published/failed), concept aliases, article hashes,
knowledge-item candidates, and rejections. JSON reliability is handled by `structured_output.py`'s 3-tier fallback:
native `format=json` → regex extraction → retry-with-error-feedback — the exact pattern Linus needs for sub-14B Workers.
Atomic writes (temp + rename), SHA-256 body hashes for hand-edit detection, an advisory `pipeline.lock`, a `watchdog`
debounced file watcher, and `[olw]`-prefixed git commits with `olw undo` via `git revert` round it out.

The reject-and-explain loop is the architectural feature the brief asked about. In `pipeline/compile.py` around line
870, the compiler calls `db.get_rejections(name, limit=3)`, dedupes the feedback strings, and injects them into the
prompt under the literal header `PREVIOUS REJECTIONS — address these issues in this version:`. On the human side
(`olw reject FILE --feedback "…"`), the rejection record stores both the feedback string and the rejected body, so
`compute_rejection_diff` in `pipeline/review.py` can show the user how the next draft has moved relative to the version
they rejected. After `StateDB._REJECTION_CAP` (5) rejections without an approval, the concept is auto-blocked from
future compiles until `olw unblock "Name"` re-enables it. This is a complete, persistent, human-in-the-loop critique
loop on top of a local model — no DPO, no training, just prompt injection and SQLite, and it works on a 4B model.

## 3. What's reusable in Linus

The structured-output retry ladder in `structured_output.py` is the single most directly useful piece. Linus's Phase 1
Ollama Worker will face exactly the same failure mode (Qwen2.5 / gemma occasionally wrap a flat schema in
`{"properties": {...}}`) and `obsidian-llm-wiki-local` has already solved it for production use, with three escalating
tiers and tests. Lifting that module wholesale into `src/linus/inference/` is a defensible Phase 1 move. The
provider-abstraction shape (`LLMClientProtocol` + `client_factory.build_client(config)`) is also a clean reference for
Linus's own router: a single `effective_provider` resolved from per-vault config + global config + env vars, with the
Ollama path special-cased. Compared to the hosted-API-first siblings (`AgenticResearchWiki`, `agentic-wiki-builder`),
this repo's "local first, cloud is the special case" inversion matches Linus's "no paid APIs required for operation"
north star exactly. The reject-and-explain loop is also worth study as a prototype of how a Linus Skill could capture
human critique without retraining — store the critique text, inject on next invocation, cap retries.

## 4. What's inspiration only

The CLI surface (`olw setup`, `olw doctor`, `olw run`, `olw watch`, `olw compare`) and the vault layout
(`raw/`/`wiki/`/`wiki/.drafts/`/`wiki/sources/`/`wiki/synthesis/`/`.olw/`) are the user-product part. Linus is an
orchestration backend, not a vault tool, so the convention to copy is the data-model discipline (immutable `raw/`, all
generated state under one hidden directory, atomic writes, SHA-256 hand-edit detection) rather than the literal
directory names. The `olw compare` "vault switch advisor" — rebuild two preview vaults from the same `raw/` notes, diff
results, return one of `switch | keep_current | manual_review` — is a nice prior art for a Phase 1 inference bake-off
harness, but Linus already has `benchmarks/dan_tasks/` for this. The Obsidian-specific touches (graph filters, Dataview
tags, `[[wikilinks]]`, web-clipper integration) live downstream of whatever Linus's KnowledgeBase chooses to expose;
Phase 2 may or may not adopt them, but they are not on the critical path.

## 5. What's incompatible or out of scope

The pipeline assumes a personal-vault scale (~100 source notes — the README says the no-embeddings query layer "works
well up to ~100 source notes"). Dan's KnowledgeBase has a paper corpus that is at least an order of magnitude larger and
already invested in a real RAG/vector setup; the index-only routing in `pipeline/query.py` is not the right answer at
that scale. The CLI is the only entry point — there is no library API, no HTTP endpoint, no MCP server. Embedding this
in Linus means lifting modules into `src/linus/`, not running `olw` as a subprocess. The legacy two-step LLM planning in
`compile.py --legacy` is on its way out; ignore. The smoke test against `gemma4:e4b` takes 15+ minutes, which is fine
for the maintainer's CI but not a fast Linus loop.

## 6. Recommendation: **Study**

Read it carefully, lift `structured_output.py` and the `LLMClientProtocol` / `client_factory` pattern when Linus's Phase
1 Ollama Worker needs reliable JSON, and treat the reject-and-explain loop as the reference implementation if Linus ever
ships a "human critique improves next generation" skill. Do not embed `olw` as a tool in Linus and do not adopt its
vault layout for KnowledgeBase. The `obsidian-llm-wiki` PyPI package is the right shape for its target user (an
individual with an Obsidian vault); Linus's target is a backend with multiple front-ends and a much larger corpus. What
is genuinely transferable is the engineering taste — small dependency surface, atomic writes, SQLite state,
deterministic cleanup, retry-with-error-feedback for structured output — and that is worth a careful read before writing
the equivalent Linus modules.

## 7. Questions for Dan

- **Lift `structured_output.py` directly?** It is MIT, ~300 lines, no exotic dependencies, and solves a problem Linus
  will hit in Phase 1 the day a Qwen2.5 Worker is asked for JSON. Vendor it under `src/linus/inference/structured.py`
  with attribution, or rewrite from scratch?
- **Compared to its Group 2/3 siblings (`AgenticResearchWiki` is hosted-API-first; `agentic-wiki-builder`,
  `llm-research-wiki`, `llm-wikidata`, `atomic-knowledge`, `beever-atlas` are mostly hosted-first too), this is the only
  one that treats Ollama as the default and OpenAI-compat as the fallback.** Does that local-first commitment plus the
  reject-and-explain loop make `obsidian-llm-wiki-local` the canonical Group-3 reference for Linus, with the others as
  contrast cases?
- **Reject-and-explain as a Linus Skill primitive.** Imagine a Phase 7 Linus Skill where any Worker output can be
  rejected with a free-text critique that gets injected into the next invocation, capped at 5 attempts. Is that worth
  spec'ing now while the pattern is fresh, or premature?
- **Obsidian as a Linus front-end, ever?** The `wiki/` output is plain markdown with `[[wikilinks]]` and YAML
  frontmatter — Obsidian-readable for free. If KnowledgeBase eventually exports synthesis pages in this shape, Dan gets
  graph view and backlinks at zero cost. Phase 4 candidate, or out of scope?
- **The vault layout vs. the KnowledgeBase submodule.** `obsidian-llm-wiki-local`'s discipline (immutable `raw/`, all
  generated state under a single hidden directory, atomic writes, hand-edit detection) is the right pattern. Is
  KnowledgeBase already shaped this way, or worth a Phase 2 audit before deeper integration?
