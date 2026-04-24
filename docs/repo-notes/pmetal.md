# pmetal (`Epistates/pmetal`)

## 1. Purpose and scope

pmetal — "Powdered Metal" — is an Apple-Silicon-native ML platform
written in Rust, spanning the entire stack from custom Metal GPU
kernels and ANE integration up through LoRA/QLoRA/DoRA training, 12+
preference-optimization methods (DPO, SimPO, ORPO, KTO, GRPO, DAPO…),
knowledge distillation with TAID, 14 model-merging strategies,
diffusion training, a GGUF quantizer, an OpenAI-compatible serving
binary (behind a feature flag), a Python extension via PyO3, a full
TUI, and a Tauri+Svelte desktop GUI. It is, by a wide margin, the most
ambitious project in the repo collection and maps almost 1:1 onto
Linus's Inference + Training pillars in ARCHITECTURE.md. For Phase
1b's "inference-backend bake-off" this is the challenger; for Phase 6
it is the prospective training backbone.

## 2. Architecture summary

A Rust workspace of ~20 specialized crates: `pmetal-metal` (custom
Metal kernels: FlashAttention, fused GDN, fused LoRA, fused SwiGLU,
fused RMSNorm, fused RoPE, fused cross-entropy), `pmetal-mlx` (MLX
integration via a zero-allocation C++ bridge), `pmetal-models` (18+
LLM architectures including Llama 4 Scout/Maverick, Qwen3 MoE, Qwen3.5
Next, DeepSeek V3, Mixtral, Granite-Hybrid, NemotronH, Jamba, Flux
diffusion), `pmetal-lora` (LoRA/QLoRA with dynamic architecture
detection), `pmetal-trainer` (all the PO losses), `pmetal-distill`
(online, offline, progressive, cross-vocabulary, TAID),
`pmetal-serve` (OpenAI-compatible HTTP), and `pmetal-mcp` (MCP server
with 45 tools for Claude Desktop). ANE integration uses a dynamic
weight pipeline — 9 MIL kernels compiled once at startup, weights
packed alongside activations in IOSurface spatial dimension — the
same engineering pattern documented in the `ANE` repo, hardened into a
production codebase. A TurboQuant KV cache achieves 4-6× compression
with near-zero quality loss via random rotation + Lloyd-Max
quantization and QJL residual correction, data-oblivious (no
calibration). Hardware auto-detection tunes kernels per chip family
(Apple7/8/9/10) and tier (Base/Pro/Max/Ultra), including M5's NAX
accelerator. Signed binaries on GitHub; crate on crates.io.

## 3. What's reusable in Linus

If pmetal's Phase 1b evaluation is favorable, essentially everything.
Serving layer (`pmetal serve`) slots into Phase 2a as the OpenAI-
compatible endpoint. Training layer (`pmetal train`, `pmetal distill`,
`pmetal grpo`) slots into Phase 6 as the fine-tuning backbone.
`pmetal-mcp` gives Linus a 45-tool MCP server if MCP is adopted in
Phase 3. The `easy` Rust/Python APIs mean Linus can call pmetal as a
library rather than shelling out, preserving orchestration cleanliness.
The ANE pipeline addresses the "who actually ships production ANE
code?" question — the ANE repo is a proof; pmetal is the product.
TurboQuant's 4-6× KV cache compression addresses long-context memory
pressure on 32 GB directly.

## 4. What's inspiration only

The sheer breadth — 20 crates, 12 training methods, 14 merge
strategies, GUI + TUI + CLI + SDK + Python bindings — is a model for
what "one person's ambitious local ML platform" can look like given
several years of sustained effort. Linus does not need to grow that
wide; it needs to consume pmetal *as a library* for Phases 2a, 6, and
7, and remain the orchestration layer on top. The GUI in particular
is not Linus territory — Linus has Streamlit and eventually openclaw.

## 5. What's incompatible or out of scope

Rust build times and binary size. A release build of the full feature
set is substantial and slow on 32 GB while other things are running;
the `--features easy` or `--features serve` subsets are the practical
entry points. Some architectures listed in `pmetal-models` (Llama 4,
Qwen3 MoE, DeepSeek, Pixtral, Whisper, CLIP, T5) are implemented but
not wired into the `DynamicModel` dispatcher, so inference through the
CLI/SDK is limited to the ~18 dispatched families — this is almost
certainly fine for Linus's needs but worth noting before promising
"pmetal supports anything." LoRA training only covers Llama, Qwen 2/3
/3.5, Gemma, Mistral, Phi-3 — Llama 4 and MoE architectures are
inference-only for training purposes.

## 6. Recommendation: **Integrate (pending Phase 1b verdict)**

pmetal is the single most consequential repo in the collection for
Linus. Phase 1b's evaluation plan is correctly scoped: build it,
smoke-test `pmetal tui` and `pmetal info`, try a toy LoRA, stand up
`pmetal serve`, benchmark against `ollama serve`, write the verdict to
`docs/adr/0001-inference-backend.md`. If tok/s, TTFT, RSS, and
5-concurrent throughput are at parity or better and no stability
deal-breakers surface, adopt pmetal as the Phase 2a serving backend
and commit to it as the Phase 6 training backbone. If it wobbles,
fall back to Ollama + mlx-lm-ft and revisit pmetal at a later release.

## 7. Questions for Dan

- **Scope of Phase 1b.** The roadmap calls for a 5-concurrent
  throughput test; is that the right concurrency target, or would
  single-request tok/s + memory-footprint be enough to make the
  adopt/defer call?
- **Feature-flag strategy.** Default pmetal build includes ANE + MLX
  + serve + Trainer + data + distill — about 15 active features on
  the critical path. Do we build the full default for Phase 1b and
  let compile times hurt, or strip to `--features serve` for the
  first pass and layer training in when Phase 6 approaches?
- **pmetal-mcp as Linus's tool registry path.** pmetal already ships
  45 tools via MCP. Is that a serious candidate for the Phase 2a
  tool registry (Linus wraps pmetal-mcp + adds KnowledgeBase tools),
  or should Linus own tool definitions entirely and pmetal-mcp is
  study material?
- **Dependency risk.** pmetal is one developer's project. It's
  impressive and signed, but single-maintainer risk is real. If
  adopted deeply, what's the fallback plan — pin a commit and accept
  no updates, or maintain readiness to migrate to mlx-lm + Ollama if
  pmetal goes stale?
- **Manifold-Constrained Hyper-Connections (`pmetal-mhc`).** This
  maps directly onto the JPmHC paper (`2602.18308`) in the context
  folder. Are you interested in running mhc as a Phase 6 training
  experiment, or does it stay a curiosity?
