# Linus — Glossary

Terms, component names, and Linus-specific vocabulary. Update as new terms enter use.

## Project-specific

**Linus.** The project and the product. Named after Linus Pauling and Linus Torvalds.
See VISION.md for the full naming rationale. Also the name of the eventual fine-tuned
model (e.g., "Linus-Qwen-7B-v1" as a LoRA-adapted Qwen base).

**Maestro.** Dan + hosted Claude (via this chat, Claude Code, Claude.ai). Responsible
for architecture, planning, spec writing, hard debugging, taste-level decisions.

**Worker.** A local model (currently Qwen2.5-Coder-7B or Mistral-7B via Ollama). Executes
well-specified tasks handed down from the Maestro. Workers are fungible and scalable;
Maestros are not.

**Orchestra / orchestration layer.** The Linus backend itself. Composer + Conductor +
Section leaders + Musicians + Score. See VISION.md for the full extended metaphor.

**Score.** The written guidance everyone follows: CLAUDE.md, VISION.md, ARCHITECTURE.md,
ROADMAP.md, DECISIONS.md, session-level specs. The canonical reference.

**The Algorithm check.** A behavioral convention: before adding any component, ask
"can we delete this requirement instead?" Before reaching for a library, ask "does
something we already have serve this purpose?" From Elon Musk's five-step algorithm as
documented in Jon McNeill's *The Algorithm*.

**Dan task suite.** Private benchmark at `benchmarks/dan_tasks/`. 5–10 tasks pulled from
Dan's real scientific and software workflows, used as the primary measure of Linus's
actual usefulness. Re-run at every phase boundary.

**Known Library Quirks.** Section at the bottom of CLAUDE.md where resolved constants,
config values, and library gotchas are logged the moment they're discovered. Prevents
re-deriving the same fixes.

**KnowledgeBase** (capital K, capital B). Dan's separate repo containing paper extraction,
embeddings, clustering, knowledge graph, and Streamlit viewer. Integrated into Linus as
a git submodule at `modules/KnowledgeBase/`. Previously known as `papers_analysis`.

## Harness vs. orchestration

**Harness.** A coding workflow tied to a UX surface — Cline in VS Code, Claude Code in
the terminal, openclaw as a macOS app. Takes a single user query, runs one conversation
with one model, loops with built-in tools until the task is done. Harnesses are
UX-specific.

**Orchestration layer.** The Linus backend. Accepts requests from multiple front-ends,
routes to the appropriate model, exposes persistent domain-specific tools, maintains
durable state, enforces cross-cutting policies, coordinates multi-agent workflows.
Has no UI — front-ends are its UIs.

**Front-end.** Any client that talks to Linus's OpenAI-compatible endpoint: VS Code
(Claude Code, Cline, native Ollama chat), LM Studio, openclaw, a future native Linus
app. Interchangeable.

## Inference and training

**Ollama.** Local model server with Metal acceleration on Apple Silicon. Dan's current
primary worker-model server. Installed via Homebrew (NOT conda — the conda build is
CPU-only). Runs on port 11434. Serves `mistral:7b-instruct` and `qwen2.5-coder:7b`.

**pmetal.** Rust-based Apple Silicon ML platform (Epistates). Covers LoRA/QLoRA/DoRA
training, preference optimization (DPO/SimPO/ORPO/KTO), knowledge distillation
(including TAID), native ANE pipeline, custom Metal kernels, 13-format GGUF
quantization, OpenAI-compatible serving. Evaluated in Phase 1 as potential primary
serving + training backbone.

**mlx-lm.** MLX-native Python library for LLM inference and training. Fallback /
alternative to pmetal. Simpler, better-understood.

**mlx-flash.** MLX weight-streaming library (Matt Wong). Stream model weights from SSD
for larger-than-RAM models. Used in Phase 6d for inference-only evaluation of large
fine-tuned models.

**flash-moe.** Dan Woods' Metal/Objective-C MoE streaming inference engine for Qwen 3.5
397B on Apple Silicon. Not integrated into Linus directly — studied as methodology and
inspiration. Demonstrated the agentic-development pattern Linus aims to emulate.

**BitNet.** Microsoft's 1-bit LLM inference framework. Reference for 1-bit inference
on CPU and GPU.

**Bonsai.** PrismML's end-to-end 1-bit 8B MLX-native model. Potential worker candidate
for memory-constrained deployments.

**LoRA / QLoRA / DoRA.** Low-rank adapter-based fine-tuning methods. LoRA trains small
rank-k matrices added to frozen base weights. QLoRA quantizes the base to 4-bit. DoRA
separates magnitude and direction updates. All tractable on M1 Max 32GB for 7–14B
models.

**Continued pretraining.** LoRA applied to next-token prediction on raw domain text
(e.g., genomics papers). Distinct from instruction-tuning LoRA.

**Instruction-tuning LoRA.** LoRA trained on Q&A pairs or instruction/response pairs
to align model behavior toward task execution.

**DPO / ORPO / SimPO / KTO.** Preference optimization methods. Align model outputs to
human preferences via pairs of (chosen, rejected) outputs.

**SPECTER2.** Scientific paper embedding model (AllenAI). 768-dim dense embeddings,
title+abstract input. Used by KnowledgeBase for semantic similarity.

**TF-IDF.** Term frequency-inverse document frequency. Sparse vocabulary-based
representation. Used by KnowledgeBase alongside SPECTER2 in hybrid similarity.

**HDBSCAN.** Hierarchical density-based clustering. Used by KnowledgeBase for paper
topic clusters.

**BERTopic.** Topic modeling library using transformer embeddings. Used for topic
labeling in KnowledgeBase.

**REBEL.** Relation extraction model (Babelscape). Extracts typed (head, relation, tail)
triples from text. Used by KnowledgeBase for the knowledge graph.

**SciSpacy.** Scientific NER (named entity recognition) library. `en_core_sci_lg` model
used by KnowledgeBase.

## Agents and workflows

**Agent.** An LLM loop that makes tool calls, observes results, and continues until
done. A harness runs an agent for a user query. Linus can spawn multiple agents in
parallel.

**Maestro/Worker loop.** The core Linus development pattern. Maestro writes a spec,
Worker implements against the spec, Maestro reviews. See
`docs/maestro-worker-protocol.md`.

**Parallel agent spawn.** `linus.agent.spawn(spec, subtasks)` tool (Phase 3+). Fans out
a single parent task into N worker agents operating in parallel with shared results
store.

**autoresearch methodology.** Karpathy's pattern for agentic research loops: give an
agent a metric, a goal, and a fixed time budget; it iterates; keep-or-revert by git.
Used in Phase 5 inference experiments and Phase 6 hyperparameter search. Distinct from
the `autoresearch-mlx` repo (which is the MLX port of Karpathy's original).

**Skill.** A Linus-native prompt template or workflow, following Anthropic's SKILL.md
convention. Stored at `src/linus/skills/<n>/SKILL.md`. Invoked via
`linus.skill.invoke`. Phase 7 introduces domain skills.

**Flash-moe pattern.** The agentic development pattern demonstrated by Dan Woods'
flash-moe project: give Opus a metric and a "never stop until you hit this number" goal;
let it iterate; collaborate at plateau points. 24 hours, ~90 experiments, 42% discarded,
winning insight un-deducible from first principles. Used in Linus for Phase 5+ research.

## Data and storage

**metadata.db.** KnowledgeBase's SQLite file with one row per paper: sha256, title,
authors, year, journal, DOI, abstract, source. Read-only from Linus.

**SHA256.** The join key between KnowledgeBase's metadata.db and PDF files on disk.

**ZIM.** File format used by Kiwix for offline content archives (Wikipedia, Khan
Academy, etc.). Phase 4 deploys ZIMs under Linus.

**PMTiles.** File format from ProtoMaps for offline vector tiles. Stores OSM data in a
single file. Phase 4.

**Audit log.** Append-only JSONL at `~/.linus/audit.jsonl`. Every tool call, model call,
and policy decision. Source of truth for autonomy tier graduation decisions.

## Benchmarks

**MBPP.** "Mostly Basic Python Programming." 500-problem benchmark for code generation.
Public.

**HumanEval.** OpenAI's 164-problem code completion benchmark. Public.

**MMLU.** Massive Multitask Language Understanding. 57-subject multiple-choice benchmark.
Public.

**GPQA.** Graduate-level Google-proof Q&A. Dense physics/chemistry/biology MC benchmark.
Public.

**SWE-bench.** Real-world software engineering benchmark. Requires fixing real GitHub
issues. Heavy to run; deferred.

**OSWorld.** Agent benchmark in a virtualized desktop. Heavy; deferred until Linus has
an agent worth testing.

**Dan task suite.** See project-specific section above. Primary measure of real
usefulness.

## Abbreviations

- **ADR** — Architecture Decision Record. The format used in DECISIONS.md.
- **ANE** — Apple Neural Engine. The dedicated neural accelerator on Apple Silicon.
- **API** — Application Programming Interface.
- **CLI** — Command Line Interface.
- **GGUF** — GPT-Generated Unified Format. Binary model format used by llama.cpp and
  Ollama. 13 quantization variants in pmetal.
- **GPU** — Graphics Processing Unit. On Apple Silicon, integrated.
- **KG** — Knowledge Graph.
- **KV cache** — Key-Value cache in transformer attention. Memory-heavy at long contexts.
- **LLM** — Large Language Model.
- **MCP** — Model Context Protocol (Anthropic). A standard for tool/resource exposure to
  LLMs.
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
- **claw-code** — Rust CLI agent harness (reference).
- **cline** — VS Code agentic coding extension.
- **project-nomad** — Offline knowledge server (inspiration for Phase 4).
- **flash-moe** — MoE streaming inference (Dan Woods, methodology reference).
- **mlx-flash** — MLX weight streaming (Matt Wong).
- **pmetal** — Rust ML platform for Apple Silicon (Epistates).
- **BitNet** — Microsoft 1-bit LLM inference framework.
- **Bonsai** — PrismML 1-bit 8B model.
- **ANE (Maderix)** — ANE reverse-engineering reference.
