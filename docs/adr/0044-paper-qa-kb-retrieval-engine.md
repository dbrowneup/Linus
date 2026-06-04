## DEC-0044 — paper-qa as Phase 2c KnowledgeBase retrieval-and-synthesis engine

**Date:** 2026-05-06 **Status:** accepted (corpus-engine posture superseded by DEC-0062; "few named papers"
optional-tool use retained)

**Context.** paper-qa (FutureHouse, Apache 2.0, `arXiv:2409.13740`) is the first paper-corpus-shaped tool to earn an
Integrate verdict in the g8-sci-agents fan-out. It ships four well-scoped tools — `PaperSearch` (tantivy full-text +
metadata fetch), `GatherEvidence` (top-k vector retrieval + LLM re-ranking via the RCS loop), `GenerateAnswer`
(citation-grounded synthesis), `Complete`/`Reset` (control flow) — and routes all LLM I/O through LiteLLM, so Ollama at
`http://localhost:11434` is a first-class provider. The Phase 2 KB substrate question has been open since DEC-0003:
build the retrieval-and-synthesis layer from scratch on top of wikiloom + openaugi, or adopt a system that already does
it well. DEC-0029 resolved the episodic store (SQLite + content-hashes + git); this ADR resolves the paper-corpus
read/query side. Closes **S1**.

**Decision.** Adopt paper-qa as the Phase 2c KnowledgeBase retrieval-and-synthesis engine. Phase 2c integration plan:
smoke-test `pip install paper-qa[local]` into the linus conda env against a 10-paper sample from `context/papers/`
(five papers — smoke gate first); configure `embedding="st-multi-qa-MiniLM-L6-cos-v1"` (sentence-transformer,
Apple-Silicon-friendly, no API key) and `llm="ollama/qwen2.5:14b"` via LiteLLM config; run `pqa ask` against a known
biochem question and log tok/s and answer quality. If acceptable, expose as a Linus tool in Phase 2c backed by a
preindexed `context/papers/` tree, and add it to the Phase 1e Maestro/Worker loop as the "look it up in Dan's papers"
capability. Phase 3: swap KnowledgeBase's retrieval layer to paper-qa's tantivy index and RCS pipeline, keeping
KnowledgeBase as corpus-of-record. This is "adopt + extend," not "build from scratch."

paper-qa covers the paper-corpus side only. DEC-0029's episodic store (Layer C) and the KB graph substrate (DEC-0015)
are orthogonal and unaffected. FutureHouse's `fhlmi` and `fhaviary` become runtime deps; `ldp` is the obvious Phase 6
candidate for fine-tuning the tool-selection policy, but paper-qa's bundled `ToolSelector` agent is sufficient through
Phase 5. FutureHouse stack commitment is intentional: paper-qa is the most mission-aligned external system in the full
cloned-repo collection.

**Caveat.** paper-qa's README warns that 7B models perform poorly (nested instruction following breaks down); Phase 2c
targets Qwen2.5-14B-Instruct as the minimum Worker floor. LAB-Bench JSONL benchmark files must stay in `benchmarks/`,
never in `context/papers/` or any directory the KB ingest pipeline touches (canary contamination risk).

**Consequence.** Phase 2c gains a citation-grounded, evaluated paper-QA tool without building one. Exit ramp preserved:
paper-qa's LiteLLM interface means swapping the execution engine is a config change, not an architectural refactor.
