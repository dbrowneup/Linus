# Reference Landscape: Repos in Context

## What This Document Is

Twelve repos sit in `repos/`. Each has a one-page note in `docs/repo-notes/` covering purpose, architecture, what's
reusable, and a recommendation. This document zooms out: it shows how the twelve form a system, which ones are in
tension with each other, and where each enters the Linus roadmap. Read the individual notes for depth; read this for
orientation.

---

## The Four Layers

The repos cluster naturally into four layers that map onto Linus's architecture:

**Inference** — how Linus runs models locally on Apple Silicon

- `pmetal` — full-stack Rust platform: serving, training, ANE, OpenAI-compatible endpoint
- `mlx-flash` — SSD weight streaming for models larger than RAM, MLX-native, zero quality loss
- `flash-moe` — methodology reference: 400B MoE on 48 GB Apple Silicon in 24 hours
- `ANE` — existence proof + engineering patterns: backprop on the Apple Neural Engine
- `Bonsai-demo` — pretrained 1-bit and 1.58-bit models on MLX, ready to benchmark
- `BitNet` — Microsoft ternary inference; CPU-focused, study reference for kernels and distillation

**Harnesses** — how Dan interfaces with Linus

- `claw-code-local` — Rust CLI fork that adds local-model support; the practical terminal harness
- `claw-code` — upstream Rust CLI (Anthropic-locked), design reference only
- `cline` — VS Code agentic coding extension; OpenAI-compat, MCP-first, ships today
- `openclaw` — polished personal AI platform: voice, canvas, menu bar, multi-channel

**Methodology** — how to iterate and improve

- `autoresearch` — Karpathy's overnight experiment loop; MLX fork already in `repos/`
- `flash-moe` — also the keep-or-revert experiment-log discipline, canonical form

**Data Sovereignty** — what Linus can know offline

- `project-nomad` — component catalog: Kiwix, Kolibri, ProtoMaps, Qdrant, CyberChef; not code to adopt

---

## Inference: The Pivotal Decision

pmetal is the most consequential repo in the collection by a wide margin. It spans the entire inference-and-training
stack — custom Metal kernels, ANE integration, LoRA/QLoRA training, 12+ preference-optimization methods (DPO, SimPO,
ORPO, GRPO…), an OpenAI-compatible serving binary, a Python bridge via PyO3, and a 45-tool MCP server — all in a single
Rust platform. If Phase 1b's evaluation returns a favorable verdict, pmetal becomes the Phase 2a serving backend and the
Phase 6 training backbone, and most of the hard infrastructure questions are answered by adopting it rather than
building them.

The inference candidates sit on a spectrum from "framework-integrated, zero-code" to "bespoke, maximum-control." At the
framework-integrated end, mlx-flash wraps any MLX model in a streaming proxy, reads weights from SSD on demand, and
claims bit-perfect parity (`0.0000000000` loss delta) through a predictive I/O scheduler — a `pip install` plus three
function calls gets a 30B model running on 16 GB. At the bespoke end, flash-moe is 7k lines of C and Objective-C with
hand-tuned Metal shaders, built in 24 hours and 90 experiments, running a 400B MoE at 4.4 tok/s on 48 GB. Linus does not
adopt flash-moe's code; it adopts its methodology. pmetal sits between the two philosophies: Rust + Metal kernels,
hard-won optimizations, but packaged as an installable platform rather than a one-off engine.

Bonsai-demo and BitNet represent the 1-bit/ternary inference path, attacking the same thesis from different angles:
models with weights in `{-1, 0, +1}` run at far larger parameter counts for the same memory budget. Bonsai-demo's
pretrained 1-bit 8B and 1.58-bit 8B are drop-in candidates for Phase 1c's benchmark sweep, running against Qwen/Mistral
baselines to answer the quality-cost question empirically. BitNet's `bitnet.cpp` is CPU-focused with no Metal path,
making it a study reference rather than an integration target; the serious Apple Silicon 1-bit work lives in Bonsai's
MLX path and in pmetal's custom kernels.

ANE occupies its own niche: a weekend research hack proving that backpropagation — not just inference — can run on the
Apple Neural Engine via reverse-engineered private APIs, with no CoreML, no Metal, no GPU. The code should not be
adopted directly; it is private-API-dependent and will break on macOS updates. But it is load-bearing for the roadmap in
one important way: the existence proof means "defer ANE work to Phase 8" is no longer the conservative choice. pmetal's
ANE crate implements the same engineering patterns in a maintained context, and benchmarking "ANE prefill + GPU decode"
as a pmetal configuration becomes a Phase 1b priority rather than a nice-to-have.

---

## Harnesses: More Front-Ends Than You Need

Linus has four potential front-ends — and that is fine, for now. cline (VS Code), claw-code-local (terminal), openclaw
(chat/voice/canvas), and Claude Code (hosted Maestro, already in use) all point at an OpenAI-compatible endpoint, which
is the only interface they will see. None of them require Linus to care about their internals.

claw-code-local is the most immediately useful. Two patches on top of the clean-room Claude Code port: auto-detect the
provider from env vars, fix streaming markdown block spacing. Set `OPENAI_BASE_URL=http://localhost:11434/v1`, run
`claw --model qwen3:14b`, and you have the full Claude-Code-style terminal experience against a local model. Install it
now, point it at Ollama, and Phase 1e's Maestro/Worker loop has a terminal surface without writing a line of code. The
upstream claw-code is Anthropic-locked; it is design reference only.

cline extends this into VS Code with the full agentic coding workflow: AST analysis, regex search, file edits with diff
views, terminal execution, linter monitoring, and MCP tool creation on the fly. The architectural detail worth borrowing
from cline is not its code — Linus does not extend it — but its `xs` / `hermes` / `glm` prompt variant system, which
demonstrates empirically that tool-use prompts tuned for frontier models fail on small local models. Every harness that
speaks to a sub-7B worker needs model-family-specific templates, not a watered-down GPT-5 prompt. Linus's Phase 7 skills
design should factor the same way.

openclaw is the Phase 5 UI: voice wake, macOS menu bar, Canvas, iOS companion node. It is more ambitious than either
terminal or VS Code front-end, and it assumes a polished backend behind it. The `SKILL.md` convention it uses is the
same one Linus's Phase 7 adopts, so skills written for Linus are portable to openclaw without modification. Install and
pin in Phase 5; stay out of its channel configuration beyond macOS + WebChat unless a specific messenger integration is
needed.

---

## Methodology: Keep-or-Revert as a Practice

autoresearch and flash-moe share the same fundamental discipline: fixed budget, one editable file (or parameter set),
clear metric, keep-or-revert by git. flash-moe's experiment log is the canonical exemplar — 90 entries, 42% discarded —
and its most surprising finding is that no custom caching strategy beat the OS page cache. autoresearch packages this as
a minimal Python rig: `program.md` tells the agent what the metric is and what the budget is, `train.py` is the single
editable file, the agent iterates overnight at ~12 experiments per hour.

The MLX fork (`autoresearch-mlx`, already in `repos/`) is the pathway to running this methodology on Dan's hardware
without a Linux GPU box. The correct Phase 6d plan is to translate `program.md` to a `SKILL.md`, replace the editable
file with a `lora_config.py`, and set the metric to Dan task suite score rather than raw validation bits-per-byte. The
per-experiment budget will need to be longer (30 minutes vs. the 5-minute H100 budget), but the loop structure — edit,
train, compare, keep or revert — is unchanged.

---

## Data Sovereignty: A Component Catalog, Not a Framework

project-nomad's value to Linus is its curated list: Kiwix for offline Wikipedia and ebook ZIMs, Kolibri for structured
Khan Academy courseware, ProtoMaps for offline maps, Qdrant for vector search, CyberChef for data tooling, and Ollama +
Qdrant for local AI with RAG. NOMAD itself is Debian-first, Docker-orchestrated, and NVIDIA-GPU-recommended — none of
those fit Linus. But four of its named components enter Linus's Phase 4 roadmap, and NOMAD's curation decisions (which
Wikipedia ZIM subsets to install, which PMTiles region files to default to) are worth consulting when Phase 4 begins.
NOMAD is proof the pattern works; Linus extracts the components and discards the orchestration layer.

Kolibri is worth calling out separately. It is the right tool for structured educational content — Khan Academy's
curriculum is organized as a learning tree, not as an encyclopedia, and Kolibri's native app (cross-platform,
macOS-compatible, no Docker needed) presents it that way. Kiwix is for reference lookup; Kolibri is for worked
explanations, exercises, and domain walkthroughs. For a research assistant supporting scientific and computational work,
the distinction matters: when Linus needs to explain a statistical method or walk through a genomics algorithm,
Kolibri's Khan Academy tree has structured pedagogy where a Kiwix article is a definition. Phase 4 should install both
and expose them through separate tools.

NOMAD's posture — "Knowledge That Never Goes Offline," zero telemetry, no authentication by default, the network
boundary as the trust boundary — is the right stance for Linus and should be articulated explicitly in VISION.md if it
isn't already. The Phase 4 data sovereignty layer is not a feature bolted onto a cloud-dependent system; it is a design
constraint. Linus must be able to operate completely offline, with all data under Dan's physical control, in any
condition including the field.

---

## How the Repos Relate to Each Other

Several repos are in explicit tension or direct dialogue:

**mlx-flash and flash-moe** are complementary, not competing. flash-moe is the methodology reference and the existence
proof that SSD-streaming at production scale works; mlx-flash is the integrable implementation for Linus. When Linus
needs >RAM models, mlx-flash is the tool; flash-moe's paper is the mental model for why SSD-paced inference works at
all, and why trusting the OS page cache beats custom caching logic.

**Bonsai-demo and BitNet** address the same 1-bit quality question from different engineering philosophies. Bonsai is
MLX-native and Apple-Silicon-first, shipping pretrained models with working Metal kernels merged upstream. BitNet's
`bitnet.cpp` is CPU/CUDA-first with no Metal path; its value to Linus is the BitDistill paper (`2510.13998`), which
describes a practical distillation recipe from FP16 to 1.58-bit applicable to any Linus fine-tuned model at Phase 6.

**claw-code and claw-code-local** are upstream and fork. The upstream is design reference; the fork is the thing to
actually install. Track claw-code's roadmap (ACP/Zed ambitions, MCP refinement) as signal for features the fork may
eventually pull in; adopt the fork's commit-pinned build for real use.

**pmetal subsumes ANE** in practice. ANE showed the engineering patterns are feasible and that Apple's inference-only
CoreML posture is a software choice, not a hardware constraint. pmetal ships those same patterns as a maintained
platform. If pmetal's Phase 1b evaluation passes, the ANE repo becomes background study material rather than a gap Linus
needs to fill independently.

**autoresearch, flash-moe, and the Dan task suite** form the experimentation framework. flash-moe defined the
experiment-log discipline; autoresearch packaged it as a repeatable loop; the Dan task suite provides the Linus-specific
evaluation metric. Together they are Phase 7c's overnight inference-optimization loop.

**openclaw, cline, and claw-code-local** are three front-ends that all point at the same Linus endpoint. They serve
different contexts — terminal work, VS Code work, and chat / voice / canvas respectively. The convergence question
(whether all three remain or one proves dominant) is a Phase 5 empirical question, not a Phase 1 design decision.

---

## Phase-by-Phase: Where Each Repo Enters

**Phase 1 — Recon & Baselines**

The most important Phase 1 action is running the pmetal evaluation and writing the ADR. Build pmetal, smoke-test
`pmetal tui` and `pmetal serve`, run a toy LoRA, benchmark against Ollama, and commit the verdict as a new ADR in
`docs/adr/` (forthcoming, id assigned at authoring time — next free `DEC-NNNN`, slug `inference-backend`). In parallel,
pull Bonsai-8B-mlx-1bit, Ternary-Bonsai-8B-mlx-2bit, and BitNet b1.58 2B4T (via Ollama) and add them to Phase 1c's
benchmark sweep alongside `qwen2.5-coder:7b` and `mistral:7b-instruct` — this is a day's work and answers the 1-bit
quality-cost question before any fine-tuning commitment is made. Install claw-code-local now and use it for the Phase 1e
Maestro/Worker loop. Read the Maderix ANE substack articles and the flash-moe paper before Phase 1b closes; extract the
flash-moe experiment-log format as the template for Phase 6d.

**Phase 2 — Linus MVP**

If pmetal passes Phase 1b, `pmetal serve` stands up the `/v1/chat/completions` endpoint and claw-code-local re-points at
Linus instead of Ollama directly. If pmetal is deferred, Bonsai's `llama-server` is the interim OpenAI-compatible
endpoint for 1-bit models while Ollama handles the standard workers. cline gets a "Linus (local)" provider
configuration, opening the VS Code path without any code changes on the Linus side.

**Phase 4 — Data Sovereignty**

Consult project-nomad's component list when this phase begins. Kiwix for offline Wikipedia (install the native macOS
binary, not the Docker container); use NOMAD's ZIM selection curation as a starting point for which subsets to download.
Kolibri for structured Khan Academy courseware — install the native macOS app, configure for local-only access, and
expose a `linus.kolibri.search(topic)` tool alongside the Kiwix tool; these serve different needs and both belong in
Phase 4. ProtoMaps PMTiles served by a static local server. Qdrant in Docker if KnowledgeBase's numpy similarity search
hits its limits. For notes and personal knowledge, Obsidian is a better fit than NOMAD's FlatNotes — it is already the
standard in Dan's workflow and has a mature local-first model that integrates naturally with Linus tools.

**Phase 5 — Interface Refinement**

Install openclaw, pin a specific version, and point it at Linus's endpoint as the configured model provider. Keep Linus
skills under `src/linus/skills/*/SKILL.md` and symlink them into openclaw's workspace so the same skills surface in
both. Formalize claw-code-local as the terminal path, and formalize cline as the VS Code path. Evaluate empirically
which front-end handles which use cases best; converge only if one clearly wins.

**Phase 6 — Fine-Tuning**

pmetal's training stack (`pmetal train`, `pmetal distill`, `pmetal grpo`) is the primary backbone if Phase 1b passed.
The autoresearch-mlx loop is the overnight experiment harness: translate `program.md` to a Linus `SKILL.md`, set the
metric to Dan task suite score, set the editable file to `lora_config.py`. Benchmark mlx-flash as the serving path for
fine-tuned models that exceed RAM at native precision — the "big model streamed at native precision" vs. "small model
1-bit in-RAM" (Bonsai) question should be answered by this phase's experiments, not decided in advance. The BitDistill
paper is the dark-horse alternative if LoRA fine-tuning proves less effective than expected.

**Phase 7 — Skills & Autonomy**

Promote the autoresearch loop to a first-class `SKILL.md` and use it as the Phase 7c overnight inference-optimization
loop. Apply cline's prompt-variant pattern to Linus's tool definitions: per-worker-class templates for Qwen, Mistral,
1-bit Bonsai, and future Linus fine-tunes rather than a single generic tool-use prompt.

---

## Key Tensions

> **All three tensions resolved 2026-05-03.** See [../questions/top-questions.md](../questions/top-questions.md)
> Resolution Log and [../specs/planning-update-spec.md](../specs/planning-update-spec.md). Resolutions noted inline
> below.

Three questions sit at the center of decisions the repos collectively force:

**The inference backend.** pmetal is the clearly-right answer if it passes Phase 1b. If it doesn't — stability issues,
build problems on M1 Max, unacceptable latency — the fallback is Ollama + mlx-lm-ft + Bonsai's llama-server. The
evaluation plan is well-scoped; the most important thing is running it and writing the ADR rather than deciding in
advance.

**RESOLVED:** pmetal is the lead, pending Phase 1b verdict. Build flags `--features serve,mlx,trainer` for 1b.
Concurrency target single-request tok/s + RSS for verdict. Pin a commit; document Ollama+mlx-lm-ft fallback in the
forthcoming Phase 1b verdict ADR in `docs/adr/` (id assigned at authoring time); revisit quarterly. As of 2026-05-03 the
build + smoke tests pass with strong initial impressions.

**The 1-bit bet.** Bonsai, BitNet, and flash-moe together argue that 1-bit/ternary models are the efficient frontier for
local inference on constrained memory. The Phase 1c benchmark sweep will answer the quality question. The open decision
is whether 1-bit becomes a first-class experimental path in Phase 2–3 (given BitNet's 100B model at 7 tok/s on M2 Ultra)
or stays secondary until Phase 6. The answer depends partly on how much quality Bonsai-8B actually sacrifices on Dan
task suite — run the benchmark first.

**RESOLVED:** Phase 1c BitNet 2B4T spike (build bitnet.cpp on M1 Max, benchmark vs. Ollama-served Qwen2.5/Llama-3.2
using task-completion-time methodology) is adopted as the first concrete experiment. Phase 6 fine-tuning lane decision
deferred until Phase 1c data lands. Phase 6a commits to FP16-LoRA on genomics/biochem regardless.

**MCP as the extensibility substrate.** cline, openclaw, and pmetal all speak MCP. Adopting MCP as Linus's
tool-registration surface in Phase 3 means tools registered once become visible in all three harnesses without custom
glue code. That is architecturally cleaner but carries MCP's complexity and the risk of a protocol dependency. The
alternative is owning tool definitions natively in Linus's orchestration layer and building per-harness adapters. This
decision should be made explicitly at the start of Phase 3, not inherited by accident.

**RESOLVED:** **Adopt MCP** as the extensibility substrate. Phase 2 tool registry is built MCP-shape from the start (no
Phase 3 refactor — just exposure). Linus exposes a Linus-native MCP server AND consumes external MCP servers. **pmetal's
45-tool MCP server is the first external integration target.** Evaluate `fastmcp` for server-side construction. This
updates DEC-0005's "revisit MCP for adoption in Phase 3" to "adopted."

---

## Quick Reference

| Repo            | Layer                   | Recommendation                    | Enters           |
| --------------- | ----------------------- | --------------------------------- | ---------------- |
| pmetal          | Inference + Training    | Integrate pending Phase 1b        | Phase 2a         |
| Bonsai-demo     | Inference (1-bit)       | Integrate experimentally          | Phase 1c         |
| BitNet          | Inference (1-bit)       | Study + cheap experiment          | Phase 1c         |
| mlx-flash       | Inference (>RAM)        | Integrate in Phase 5+             | Phase 6          |
| flash-moe       | Inference / Methodology | Study (primary Phase 6d ref)      | Phase 6d         |
| ANE             | Inference (ANE)         | Study seriously                   | Phase 1b context |
| claw-code-local | Harness (terminal)      | Integrate now                     | Phase 1e         |
| claw-code       | Harness (terminal)      | Study, defer to fork              | —                |
| cline           | Harness (VS Code)       | Integrate as Phase 2+ client      | Phase 2a         |
| openclaw        | Harness (chat/voice)    | Integrate as Phase 5 front-end    | Phase 5          |
| autoresearch    | Methodology             | Integrate MLX fork experimentally | Phase 6d         |
| project-nomad   | Data Sovereignty        | Borrow components individually    | Phase 4          |
