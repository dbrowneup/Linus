# Linus — Glossary

Terms, component names, and Linus-specific vocabulary. Update as new terms enter use.

## Project-specific

**Linus.** The project and the product. Named after Linus Pauling and Linus Torvalds. See VISION.md for the full naming
rationale. Also the name of the eventual fine-tuned model (e.g., "Linus-Qwen-7B-v1" as a LoRA-adapted Qwen base).

**Maestro.** Dan + hosted Claude (via this chat, Claude Code, Claude.ai). Responsible for architecture, planning, spec
writing, hard debugging, taste-level decisions.

**Worker.** A local model (currently Qwen3 — best available for 32 GB M1 Max hardware, served via Ollama). Executes
well-specified tasks handed down from the Maestro. Workers are fungible and scalable; Maestros are not.

**Orchestra / orchestration layer.** The Linus backend itself. Composer + Conductor + Section leaders + Musicians +
Score. See VISION.md for the full extended metaphor.

**Score.** The written guidance everyone follows: CLAUDE.md, VISION.md, ARCHITECTURE.md, ROADMAP.md, DECISIONS.md (and
the per-file ADRs in `docs/adr/`), session-level specs. The canonical reference.

**The Algorithm check.** A behavioral convention: before adding any component, ask "can we delete this requirement
instead?" Before reaching for a library, ask "does something we already have serve this purpose?" From Elon Musk's
five-step algorithm as documented in Jon McNeill's _The Algorithm_.

**Dan task suite.** Private benchmark at `benchmarks/dan_tasks/`. 5–10 tasks pulled from Dan's real scientific and
software workflows, used as the primary measure of Linus's actual usefulness. Re-run at every phase boundary.

**Known Library Quirks.** Section at the bottom of CLAUDE.md where resolved constants, config values, and library
gotchas are logged the moment they're discovered. Prevents re-deriving the same fixes.

**KnowledgeBase** (capital K, capital B). Dan's separate repo containing paper extraction, embeddings, clustering,
knowledge graph, and Streamlit viewer. Integrated into Linus as a git submodule at `modules/KnowledgeBase/`. Previously
known as `papers_analysis`.

## Harness vs. orchestration

**Harness.** A coding workflow tied to a UX surface — Cline in VS Code, Claude Code in the terminal, openclaw as a macOS
app. Takes a single user query, runs one conversation with one model, loops with built-in tools until the task is done.
Harnesses are UX-specific.

**Orchestration layer.** The Linus backend. Accepts requests from multiple front-ends, routes to the appropriate model,
exposes persistent domain-specific tools, maintains durable state, enforces cross-cutting policies, coordinates
multi-agent workflows. Has no UI — front-ends are its UIs.

**Front-end.** Any client that talks to Linus's OpenAI-compatible endpoint: VS Code (Claude Code, Cline, native Ollama
chat), LM Studio, openclaw, a future native Linus app. Interchangeable.

## Inference and training

**Ollama.** Local model server with Metal acceleration on Apple Silicon. Dan's current primary worker-model server.
Installed via Homebrew (NOT conda — the conda build is CPU-only). Runs on port 11434. Serves Qwen3 and other models;
specific model selection tracks the best available model for 32 GB M1 Max hardware.

**pmetal.** Rust-based Apple Silicon ML platform (Epistates). Covers LoRA/QLoRA/DoRA training, preference optimization
(DPO/SimPO/ORPO/KTO), knowledge distillation (including TAID), native ANE pipeline, custom Metal kernels, 13-format GGUF
quantization, OpenAI-compatible serving. Evaluated in Phase 1 as potential primary serving + training backbone.

**mlx-lm.** MLX-native Python library for LLM inference and training. Fallback / alternative to pmetal. Simpler,
better-understood.

**mlx-flash.** MLX weight-streaming library (Matt Wong). Stream model weights from SSD for larger-than-RAM models. Used
in Phase 6d for inference-only evaluation of large fine-tuned models.

**flash-moe.** Dan Woods' Metal/Objective-C MoE streaming inference engine for Qwen 3.5 397B on Apple Silicon. Not
integrated into Linus directly — studied as methodology and inspiration. Demonstrated the agentic-development pattern
Linus aims to emulate.

**BitNet.** Microsoft's 1-bit LLM inference framework. Reference for 1-bit inference on CPU and GPU.

**Bonsai.** PrismML's end-to-end 1-bit 8B MLX-native model. Potential worker candidate for memory-constrained
deployments.

**LoRA / QLoRA / DoRA.** Low-rank adapter-based fine-tuning methods. LoRA trains small rank-k matrices added to frozen
base weights. QLoRA quantizes the base to 4-bit. DoRA separates magnitude and direction updates. All tractable on M1 Max
32GB for 7–14B models.

**Continued pretraining.** LoRA applied to next-token prediction on raw domain text (e.g., genomics papers). Distinct
from instruction-tuning LoRA.

**Instruction-tuning LoRA.** LoRA trained on Q&A pairs or instruction/response pairs to align model behavior toward task
execution.

**DPO / ORPO / SimPO / KTO.** Preference optimization methods. Align model outputs to human preferences via pairs of
(chosen, rejected) outputs.

**SPECTER2.** Scientific paper embedding model (AllenAI). 768-dim dense embeddings, title+abstract input. Used by
KnowledgeBase for semantic similarity.

**TF-IDF.** Term frequency-inverse document frequency. Sparse vocabulary-based representation. Used by KnowledgeBase
alongside SPECTER2 in hybrid similarity.

**HDBSCAN.** Hierarchical density-based clustering. Used by KnowledgeBase for paper topic clusters.

**BERTopic.** Topic modeling library using transformer embeddings. Used for topic labeling in KnowledgeBase.

**REBEL.** Relation extraction model (Babelscape). Extracts typed (head, relation, tail) triples from text. Used by
KnowledgeBase for the knowledge graph.

**SciSpacy.** Scientific NER (named entity recognition) library. `en_core_sci_lg` model used by KnowledgeBase.

## Agents and workflows

**Agent.** An LLM loop that makes tool calls, observes results, and continues until done. A harness runs an agent for a
user query. Linus can spawn multiple agents in parallel.

**Maestro/Worker loop.** The core Linus development pattern. Maestro writes a spec, Worker implements against the spec,
Maestro reviews. See `docs/protocols/maestro-worker-protocol.md`.

**Parallel agent spawn.** `linus.agent.spawn(spec, subtasks)` tool (Phase 3+). Fans out a single parent task into N
worker agents operating in parallel with shared results store.

**autoresearch methodology.** Karpathy's pattern for agentic research loops: give an agent a metric, a goal, and a fixed
time budget; it iterates; keep-or-revert by git. Used in Phase 5 inference experiments and Phase 6 hyperparameter
search. Distinct from the `autoresearch-mlx` repo (which is the MLX port of Karpathy's original).

**Skill.** A Linus-native prompt template or workflow, following Anthropic's SKILL.md convention. Stored at
`src/linus/skills/<n>/SKILL.md`. Invoked via `linus.skill.invoke`. Phase 7 introduces domain skills.

**Flash-moe pattern.** The agentic development pattern demonstrated by Dan Woods' flash-moe project: give Opus a metric
and a "never stop until you hit this number" goal; let it iterate; collaborate at plateau points. 24 hours, ~90
experiments, 42% discarded, winning insight un-deducible from first principles. Used in Linus for Phase 5+ research.

**shared_context.** Linus's preferred term for what some papers call a "world model" at the orchestration layer: the
structured representation of task state passed between Maestro and Workers. Disambiguates from external usage: PAN/WHAM
use "world model" to mean a predictive simulation of the environment (`task_state`); Kosmos uses it to mean a grounded
perceptual representation (`belief_state`). Linus uses `shared_context` on its orchestration surface to avoid the
ambiguity.

**Planner / coder / verifier discipline.** A 3-role decomposition recurring across QiMeng / agentic-systems work where
one model decomposes (planner), another implements (coder), and a third checks (verifier). Cited in g12 and the
agentic-systems synthesis as the canonical pattern for self-correcting agent loops.

**MTMC (Macro-Thinking Micro-Coding).** QiMeng pattern separating high-level architectural reasoning ("macro thinking")
from low-level token-by-token implementation ("micro coding") into distinct model passes — a cousin of the
planner/coder/verifier split.

**Idea→reality spine.** Naming convention for LLM-driven hardware/biology design pipelines that synthesize artifacts
which downstream actors then realize physically (silicon, sequenced DNA, fabricated parts). The g12 cluster is the first
time this spine is named explicitly in Linus docs; biology-side analogues sit in the generative-biology synthesis.

**Agent/Identity/Venue decomposition.** Canteen-derived layered framing for multi-jurisdiction skill deployment. Agent
holds capability; Identity holds the legal/credentialed wrapper; Venue holds the jurisdiction-specific deployment
surface. Used in the entrepreneurship synthesis to articulate why a single agent skill needs three orthogonal layers to
ship commercially.

**Venue layer.** The Canteen-derived deployment / monetization / jurisdiction surface above the Linus orchestration
layer. Phase 5+ extension; not a current implementation target.

**Translation-as-moat.** Canteen entrepreneurship angle: the moat is in translating between agent capability and the
jurisdiction-specific Venue surface, not in the underlying model or skill. Phase 5+ commercial-surface candidate.

**Reproducibility bundle.** Sealed-bundle convention for primary-source distribution (papers + code + data + configs +
weights) so a Worker can re-run an experiment with no external lookup. Seeded ADR DEC-NNNN-reproducibility-bundle —
sourced from Kimi-K2 + ProtiCelli pairings.

**SKILL.md conformance linter.** Auto-checker for SKILL.md frontmatter and structure across Linus skill directories.
Seeded ADR DEC-NNNN-skill-md-conformance-linter — sourced from Kimi-K2 + claude-code-guide.

**Weight-streaming.** The mlx-flash / Kimi-K2 inference target where MoE active weights are paged from SSD to unified
memory on demand, allowing models that exceed RAM to serve at acceptable latency. Phase 6d target.

**x402-mcp.** Pending commercial-surface protocol pairing Coinbase's x402 (HTTP-402-based pay-per-call) with MCP for
metered agent endpoints. Seeded ADR DEC-NNNN-agent-monetization-via-x402-mcp.

## Domain and biology archetypes

These named patterns have appeared in at least one surveyed repo or paper and are canonical enough to reference by name
in synthesis notes and ADRs. New names are added after the second independent observation of the same pattern.

**Dual-encoder cross-modal retrieval.** An architecture pairing two specialized encoders (e.g., text + protein sequence)
trained with a shared embedding space so that queries in one modality retrieve results in the other. Primary Linus
example: Horizyn-1 (chemical/genomic cross-modal search).

**Generative wet-lab loop.** The biology design archetype: generate candidate sequences or molecules → score with a
discriminative model → filter by predicted fitness → validate in a wet-lab assay → iterate. Primary examples: Evo 2
(whole-genome generation), phage engineering pipelines. Contrast with pure in-silico prediction pipelines that skip
experimental feedback.

## Data and storage

**metadata.db.** KnowledgeBase's SQLite file with one row per paper: sha256, title, authors, year, journal, DOI,
abstract, source. Read-only from Linus.

**SHA256.** The join key between KnowledgeBase's metadata.db and PDF files on disk.

**ZIM.** File format used by Kiwix for offline content archives (Wikipedia, Khan Academy, etc.). Phase 4 deploys ZIMs
under Linus.

**PMTiles.** File format from ProtoMaps for offline vector tiles. Stores OSM data in a single file. Phase 4.

**Audit log.** Append-only JSONL at `~/.linus/audit.jsonl`. Every tool call, model call, and policy decision. Source of
truth for autonomy tier graduation decisions.

## Benchmarks

**MBPP.** "Mostly Basic Python Programming." 500-problem benchmark for code generation. Public.

**HumanEval.** OpenAI's 164-problem code completion benchmark. Public.

**MMLU.** Massive Multitask Language Understanding. 57-subject multiple-choice benchmark. Public.

**GPQA.** Graduate-level Google-proof Q&A. Dense physics/chemistry/biology MC benchmark. Public.

**SWE-bench.** Real-world software engineering benchmark. Requires fixing real GitHub issues. Heavy to run; deferred.

**OSWorld.** Agent benchmark in a virtualized desktop. Heavy; deferred until Linus has an agent worth testing.

**Dan task suite.** See project-specific section above. Primary measure of real usefulness.

## Abbreviations

- **ADR** — Architecture Decision Record. Each Linus decision lives at `docs/adr/NNNN-<slug>.md` with stable id
  `DEC-NNNN`; DECISIONS.md is the index.
- **ANE** — Apple Neural Engine. The dedicated neural accelerator on Apple Silicon.
- **API** — Application Programming Interface.
- **CLI** — Command Line Interface.
- **GGUF** — GPT-Generated Unified Format. Binary model format used by llama.cpp and Ollama. 13 quantization variants in
  pmetal.
- **GPU** — Graphics Processing Unit. On Apple Silicon, integrated.
- **KG** — Knowledge Graph.
- **KV cache** — Key-Value cache in transformer attention. Memory-heavy at long contexts.
- **LLM** — Large Language Model.
- **MCP** — Model Context Protocol (Anthropic). A standard for tool/resource exposure to LLMs.
- **MLX** — Apple's array framework for ML on Apple Silicon. Unified memory, NumPy-like.
- **MoE** — Mixture of Experts.
- **MPS** — Metal Performance Shaders. Apple's GPU compute framework.
- **NER** — Named Entity Recognition.
- **RAG** — Retrieval-Augmented Generation.
- **SSE** — Server-Sent Events. Used for streaming LLM responses.

## External projects referenced

- **KnowledgeBase** — Dan's separate repo; now a Linus submodule.
- **autoresearch** — Karpathy's agentic research loop.
- **autoresearch-mlx** — Apple Silicon port of autoresearch (trevin-creator).
- **openclaw** — Local-first gateway with multi-channel chat, voice, Canvas.
- **claw-code** — Rust CLI agent harness (inspiration only; upstream is hard-wired to the Anthropic API and has no
  local-model path).
- **claw-code-local** — Community fork by codetwentyfive
  ([github.com/codetwentyfive/claw-code-local](https://github.com/codetwentyfive/claw-code-local)) that adds Ollama
  backend support. Closer to a practical CLI harness for Linus, since it already speaks to a local server. pmetal
  integration is still TBD.
- **cline** — VS Code agentic coding extension.
- **project-nomad** — Offline knowledge server (inspiration for Phase 4).
- **flash-moe** — MoE streaming inference (Dan Woods, methodology reference).
- **mlx-flash** — MLX weight streaming (Matt Wong).
- **pmetal** — Rust ML platform for Apple Silicon (Epistates).
- **BitNet** — Microsoft 1-bit LLM inference framework.
- **Bonsai** — PrismML 1-bit 8B model.
- **ANE (Maderix)** — ANE reverse-engineering reference.
- **Kimi-K2** — Moonshot's 1T-parameter / 32B-active MoE; canonical fold-in for the Phase 6d weight-streaming lane. See
  `repo-notes/Kimi-K2.md` and the paired `paper-notes/Kimi-K2-2507.20534.md`.
- **DreamZero** — RL-derived hardware design / synthesis system (g12 cluster).
- **EgoScale** — first-person video data scaling (g12 cluster reference).
- **ClawBio** — biology-domain Claude-based agent stack reference (paired-repo from PR #29).
- **Canteen** — entrepreneurship-blog source for Agent/Identity/Venue decomposition, translation-as-moat, x402-mcp seed.
- **Agora** — agent-marketplace reference (Phase 5+ commercial-surface adjacency).
- **qimeng / QiMeng family** — CodeV, MuPa, SALV, cpu-v1 — LLM-driven hardware design family in g12 cluster.
- **Letta** — episodic-memory agent framework (formerly MemGPT); Bin A integration target.
- **autogen** — Microsoft's multi-agent orchestration framework, now in maintenance mode (see Microsoft Agent Framework,
  `microsoft/agent-framework`, for the active line).
- **langgraph** — state-machine harness for stateful agent loops; Bin A reference.
- **rig** — Rust agent framework; Bin A reference.
- **goose** — Block's terminal coding agent; Bin B reference.
- **debate-or-vote** — multi-agent debate-vs-vote evaluation harness; Bin B reference.
- **MiroFish-Offline** — offline-first agent runner (AGPL); Bin B reference.
- **x402** — Coinbase HTTP-402-based pay-per-call protocol; commercial-surface candidate.
