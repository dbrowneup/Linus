# paper-qa (`Future-House/paper-qa`)

## 1. Purpose and scope

PaperQA2 is FutureHouse's high-accuracy agentic RAG package built specifically for scientific literature — PDFs, Office
files, HTML, and source code — distributed under Apache 2.0 as the `paper-qa` PyPI package. Its 2024 paper
(`arXiv:2409.13740`) reports superhuman performance on question answering, multi-paper summarization, and contradiction
detection over LitQA2 and the WikiCrow Wikipedia-article-writing benchmark, and the December 2025 release moved to
CalVer (`v2025.12.17`) to stop conflating "PaperQA the system" with "v5 the tag." For Linus this is the most
mission-aligned repo in the entire collection: it is essentially a working, evaluated, single-user version of the Phase
2c "KnowledgeBase v1 wired in as a tool" goal, and a credible foundation for the entrepreneurial-surface
"scientific-literature-intelligence-for-biotech-teams" opportunity called out in CLAUDE.md.

## 2. Architecture summary

The pipeline lives in `src/paperqa/` as a small framework-agnostic core (Pydantic models in `types.py`, the `Docs` state
object in `docs.py`, readers in `readers.py`, the contextual-summary loop in `core.py`, settings in `settings.py`) with
an agent layer in `src/paperqa/agents/` that wraps the core into LLM-callable tools. The four tools defined in
`agents/tools.py` are `PaperSearch` (LLM-generated keyword queries against a tantivy full-text index plus Crossref /
Semantic Scholar / Unpaywall / OpenAlex metadata fetch), `GatherEvidence` (top-_k_ vector retrieval followed by
per-chunk LLM scoring and contextual summarization — the "RCS" step that drives the accuracy claim), `GenerateAnswer`
(final synthesis with grounded in-text citations like `Qian2011Neural pages 1-2`), and `Complete`/`Reset` for control
flow. Default agent is `ToolSelector`, with a hard-coded `"fake"` agent for cheap deterministic search→gather→answer
runs. Embeddings default to OpenAI `text-embedding-3-small` with a NumPy in-memory vector store; Qdrant, sparse-keyword,
hybrid, and `sentence-transformers` (prefix `st-`) are all first-class. Multimodal (images, tables, math) is on by
default and includes optional read-time `enrichment_llm` synthetic captioning that shifts text-chunk embeddings without
polluting the cited source. LLM I/O is routed entirely through `fhlmi` / LiteLLM, so any OpenAI-compatible provider —
including Ollama at `http://localhost:11434` — drops in via config. Bundled settings (`high_quality`, `fast`,
`wikicrow`, `contracrow`, `tier1_limits`) live in `src/paperqa/configs/`. PDF reading is split into separate workspace
packages: `paper-qa-pypdf` (default), `paper-qa-pymupdf`, `paper-qa-docling` (model-based layout), and
`paper-qa-nemotron` (Nvidia layout model).

## 3. What's reusable in Linus

A great deal, and at multiple integration depths. The shallowest path is to install `paper-qa[local,qdrant]` into the
linus env and expose it as a single Linus tool — `paperqa.ask(question, paper_directory=...)` — backed by a preindexed
`context/papers/` tree, point its `llm` / `summary_llm` / `embedding` at Ollama plus a sentence-transformer embedding
(Apple-Silicon-friendly, no API key), and call it from the Phase 2c orchestration layer. Within the FutureHouse stack,
`paper-qa` is the user-facing product and standalone — it depends on `fhlmi` and optionally on `ldp` (the agent runtime,
gated behind the `[ldp]` extra) and `fhaviary` (the gym/env interface, hard dep) but does **not** require running
aviary's full env loop or training an ldp policy; the bundled `ToolSelector` agent is enough on its own. So we can
integrate paper-qa today without committing to ldp or aviary — and revisit those siblings only if Phase 6 fine-tunes a
domain-specific agent policy. A deeper integration in Phase 3 swaps Linus's KnowledgeBase ingest for paper-qa's tantivy
index and metadata pipeline, keeping KnowledgeBase as the corpus-of-record and using paper-qa's `Docs` as the runtime
retrieval/synthesis engine. The `parsing.enrichment_llm` machinery is a credible template for the multimodal
figure/table handling Dan's papers will eventually need.

## 4. What's inspiration only

Compared to the LLM-Wiki-engine group (G2 — wikicrow, qmd, vectorless), paper-qa fills an adjacent but distinct slot:
those produce long-form _articles_ from a corpus, paper-qa produces _grounded answers with verifiable citations_ from a
corpus. The wikicrow bundled setting gestures at long-form generation but the engine is QA-shaped, not article-shaped —
Linus would still want one of the wiki engines for the "draft a review" workflow. Compared to the agentic-memory tools
(G4), paper-qa stores nothing across sessions beyond its tantivy index and pickled `Docs`; there is no episodic memory,
no semantic graph beyond citation metadata, no learning. Within FutureHouse, paper-qa is explicitly the "no agent
training required" path — `aviary` and `ldp` are the training stack, `paper-qa` is the deployable system, which is
exactly the right separation for Linus to consume only what it needs in Phase 2 and defer the rest to Phase 6/7. The
45-tool richness of pmetal-mcp is not the model here; paper-qa's discipline is the opposite — four tools, well-scored.

## 5. What's incompatible or out of scope

Paper-qa README is explicit that 7B local models perform poorly because the agent must follow many nested instructions;
recommended local path is "relatively large models" via llamafile or Ollama, which on a 32 GB M1 Max puts us at
Qwen2.5-14B-Instruct or maybe Mistral-Small-22B as the floor, and that is also the floor for credible `gather_evidence`
re-ranking. Default `high_quality` setting uses `evidence_k = 15` and `gpt-4o-2024-11-20` for three roles (answer,
summary, agent) — calling that with three concurrent local 14B Ollama runs on 32 GB is probably infeasible without
quantization and `max_concurrent_requests = 1`. Reproduction of the published superhuman numbers also requires
Crossref + Semantic Scholar API keys and the closed FutureHouse paper-fetching pipeline; we will get "good local biochem
QA," not "the paper's headline number." Doc parsing for the `[office]` extra pulls in `unstructured` which is large;
defer until needed. License is Apache 2.0 across the workspace, no surprises.

## 6. Recommendation: **Integrate**

Adopt paper-qa as the Phase 2c KnowledgeBase retrieval-and-synthesis engine (resolved as **DEC-0044**, accepted
2026-05-06; closes question S1). The integration plan: smoke-test
`pip install paper-qa[local]`, point it at a 10-paper sample from `context/papers/`, configure
`embedding="st-multi-qa-MiniLM-L6-cos-v1"` and `llm="ollama/qwen2.5:14b"` via LiteLLM config, run a `pqa ask` against a
known biochem question, log tok/s and answer quality. If acceptable, expose it as a Linus tool in Phase 2c and add it to
the Phase 1e Maestro/Worker loop as the "look it up in Dan's papers" capability. Revisit aviary/ldp only if Phase 6
wants to fine-tune a domain-specific tool-selection policy.

## 7. Questions for Dan

- **Citation accuracy as a metric.** The "superhuman" claim is largely about citation precision/recall vs human experts
  on LitQA2. Is that worth replicating as a Linus benchmark in `benchmarks/dan_tasks/` against your own biochem PDFs, or
  is "Dan's subjective satisfaction on real questions" the better signal?
- **Multimodal enrichment cost.** `parsing.multimodal=True` adds an LLM call per figure/table at index time. For your
  ~thousand-paper corpus that's a substantial one-time hit. Run it (and pay the time/tokens once for permanently better
  figure retrieval), defer to a later phase, or run it selectively on starred papers?
