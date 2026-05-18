# pmetal (`Epistates/pmetal`)

_Refreshed 2026-05-18 against upstream HEAD 0891716; 99 commits / 418 files reviewed (v0.5.0 release on 2026-05-07)._

## 1. Purpose and scope

pmetal — "Powdered Metal" — is an Apple-Silicon-native ML platform written in Rust, spanning the entire stack from
custom Metal GPU kernels and ANE integration up through LoRA/QLoRA/DoRA training, 12+ preference-optimization methods
(DPO, SimPO, ORPO, KTO, GRPO, DAPO…), knowledge distillation with TAID, 14 model-merging strategies, diffusion training,
a GGUF quantizer, an OpenAI- _and_ Anthropic-compatible serving binary (behind a feature flag), a Python extension via
PyO3, a full TUI, and a Tauri+Svelte desktop GUI. As of v0.5.0 (2026-05-07) it adds a `pmetal-distributed` crate for
Thunderbolt-fabric multi-Mac clusters, full-parameter pretraining, and a JobSpec/JobEvent orchestration substrate that
keeps CLI / TUI / GUI / MCP in lockstep. It is, by a wide margin, the most ambitious project in the repo collection and
maps almost 1:1 onto Linus's Inference + Training pillars in ARCHITECTURE.md. For Phase 1b's "inference-backend bake-
off" this is the challenger; for Phase 6 it is the prospective training backbone.

## 2. Architecture summary

A Rust workspace of ~21 specialized crates: `pmetal-metal` (custom Metal kernels: FlashAttention, fused GDN, fused LoRA,
fused SwiGLU, fused RMSNorm, fused RoPE, fused cross-entropy), `pmetal-bridge` (the zero-allocation MLX C++ bridge that
**replaced mlx-rs entirely in v0.5.0** — every crate now goes through this), `pmetal-mlx` (MLX compat layer on top of
bridge), `pmetal-models` (18+ LLM architectures plus `forward_hidden` for 17 of them), `pmetal-lora` (LoRA/QLoRA with
dynamic architecture detection and adapters for Granite/Llama4/DeepSeek/NemotronH/Cohere/Phi/Gemma4/GPT-OSS/Qwen3-MoE/
Qwen3-Next added in v0.5.0), `pmetal-trainer` (all the PO losses + a shared `PairedPreferenceTrainer<L>` trait),
`pmetal-distill` (online, offline, progressive, cross-vocabulary, TAID — plus v0.5.0 SOTA additions: ULD, GKD, MiniLLM,
Skewed JSD), `pmetal-merge` (Fisher, RegMean, MoE expert permutation alignment via Hungarian solver, dtype-aware save),
`pmetal-serve` (OpenAI- + Anthropic-compatible HTTP with continuous batching, paged-KV admission, shared prefix cache,
embeddings endpoint), `pmetal-mcp` (MCP server now at **51 tools**, up from 45), and the new `pmetal-distributed`
(Thunderbolt fabric, ring all-reduce, tensor/expert/context/ZeRO/pipeline parallelism) and `pmetal-vocoder` crates. ANE
integration uses a dynamic weight pipeline. A **production-ready** TurboQuant KV cache (no longer experimental) achieves
4-6× compression with near-zero quality loss via random rotation + Lloyd-Max quantization + QJL residual correction;
v0.5.0 added outlier-aware mixed-precision, Hamming skip-list dispatch, and Variant F drop-QJL paths, wired through
`pmetal serve --kv-turboquant`. A Metal 4 / MPP kernel backend (15 MPP-optimized shaders) auto-selects on M5+ via
`KernelDispatch` while preserving Metal 3 paths for M1-M4. Hardware auto-detection tunes kernels per chip family
(Apple7/8/9/10) and tier. Signed binaries on GitHub; crate on crates.io. MSRV is 1.89.

## 3. What's reusable in Linus

If pmetal's Phase 1b evaluation is favorable, essentially everything. The serving layer (`pmetal serve`) slots into
Phase 2a as the OpenAI- compatible endpoint and **now also speaks Anthropic-compat** (streaming `/v1/messages` with
`message_start` → `content_block_start` → `content_block_delta*` → `content_block_stop` → `message_delta` →
`message_stop` events plus a non-streaming path) — directly relevant to the DEC-0005 / Phase-2a Anthropic-compat
revisit. Continuous batching with shared prefix cache makes multi-concurrent-request serving viable on 32 GB.
`/v1/embeddings` across 17 architectures gives Linus's KB retrieval a native embedding path without spinning up a
separate service. The training layer (`pmetal train`, `pmetal pretrain`, `pmetal distill`, `pmetal grpo`, `pmetal
rlkd`, `pmetal embed-train`) slots into Phase 6 as the fine-tuning backbone — with the v0.5.0 LoRA/QLoRA expansion the
adapter coverage now spans every text architecture Linus is likely to fine-tune. `pmetal-mcp` ships **51 tools** for
Claude Desktop and any MCP-capable harness. The `JobSpec` / `JobEvent` orchestration substrate (16 canonical spec
types, streaming `progress` / `metric` / `log` / `artefact` / `complete` / `failed` events) is a clean prior art for
Linus's own Phase 2a orchestration audit log. The `easy` Rust/Python APIs let Linus call pmetal as a library rather
than shelling out. TurboQuant's 4-6× KV cache compression is now a stable production option for long-context memory
pressure on 32 GB. The new `pmetal-distributed` crate is forward reference material for Phase 8 multi-Mac work — not
needed for the single-M1-Max baseline but interesting if Dan adds a Mac Studio later.

## 4. What's inspiration only

The sheer breadth — 21 crates, 12 training methods, 14 merge strategies, GUI + TUI + CLI + SDK + Python bindings, plus
a multi-Mac distributed runtime — is a model for what "one person's ambitious local ML platform" can look like given
several years of sustained effort. Linus does not need to grow that wide; it needs to consume pmetal _as a library_
for Phases 2a, 6, and 7, and remain the orchestration layer on top. The GUI in particular is not Linus territory —
Linus has Streamlit and eventually openclaw. The Tauri+Svelte desktop GUI is an interesting reference for how a
local-first ML app can look but is orthogonal to Linus's harness story. `pmetal-distributed`'s Thunderbolt fabric is
inspirational for the future Mac-Studio-plus-MacBook-Pro lab — useful to know exists, not on the Phase 2-6 path.

## 5. What's incompatible or out of scope

Rust build times and binary size. A release build of the full feature set is substantial and slow on 32 GB while other
things are running; the `--features easy` or `--features serve` subsets are the practical entry points. Some
architectures listed in `pmetal-models` (Llama 4, Qwen3 MoE, DeepSeek, Pixtral, Whisper, CLIP, T5) are implemented but
not all wired into the `DynamicModel` dispatcher — worth a `pmetal info` check before promising "pmetal supports
anything." MSRV bumped to 1.89 in v0.5.0; the linus conda env's Rust install must keep pace. The new pretraining
pipeline (`pmetal pretrain`) is a full-from-scratch training mode — out of scope for Linus's "fine-tune Dan-specific
models" Phase 6 goal, which stays in LoRA/QLoRA territory. The `pmetal-distributed` crate assumes Thunderbolt-fabric
multi-Mac topologies that Dan doesn't have today; relevant only if Phase 8 hardware materializes.

## 6. Recommendation: **Integrate (pending Phase 1b verdict)**

No verdict change. v0.5.0 strengthens the case rather than altering the architecture story: the mlx-rs → bridge
migration removes a long-standing dependency layer, continuous batching + Anthropic-compat directly serve Phase 2a
needs, and TurboQuant + JobSpec/JobEvent give Linus production-ready primitives to consume. Phase 1b's evaluation plan
remains correctly scoped: build it, smoke-test `pmetal tui` and `pmetal info`, try a toy LoRA, stand up `pmetal serve`
(now `--features serve` includes the Anthropic-compat path by default), benchmark against `ollama serve`, write the
verdict as a new ADR in `docs/adr/` (id assigned at authoring time — next free `DEC-NNNN`, slug `inference-backend`).
If tok/s, TTFT, RSS, and 5-concurrent throughput are at parity or better and no stability deal-breakers surface, adopt
pmetal as the Phase 2a serving backend and commit to it as the Phase 6 training backbone. If it wobbles, fall back to
Ollama + mlx-lm-ft and revisit pmetal at a later release.

## 7. Questions for Dan

1. **Scope of Phase 1b.** The roadmap calls for a 5-concurrent throughput test; is that the right concurrency target, or
   would single-request tok/s + memory-footprint be enough to make the adopt/defer call? v0.5.0's continuous batching
   makes 5-concurrent more meaningful to measure than it was at the previous note's writing.
2. **Feature-flag strategy.** Default pmetal build now includes ANE + MLX + serve + Trainer + data + distill + the
   distributed crate. Do we build the full default for Phase 1b and let compile times hurt, or strip to `--features
   serve` for the first pass and layer training in when Phase 6 approaches?
3. **pmetal-mcp as Linus's tool registry path.** pmetal now ships **51 tools** via MCP (up from 45). _Partially
   resolved (DEC-0045, see [answered-questions.md](../questions/answered-questions.md)): Linus owns in-house tool
   definitions via fastmcp; pmetal-mcp consumed as external server, not the registry foundation._
4. **Dependency risk.** pmetal is one developer's project. It's impressive, signed, and now on a steady 0.x release
   cadence (0.4 → 0.5 in ~6 weeks), but single-maintainer risk is real. Dan is in LinkedIn contact with the author —
   does that change the readiness-to-migrate calculus, or is the fallback (mlx-lm + Ollama) still the right insurance
   if pmetal goes stale?
5. **Anthropic-compat at Phase 2a.** v0.5.0 ships streaming `/v1/messages` alongside OpenAI-compat. The DEC-0005
   Phase-2a revisit (Linus speaks both protocols) becomes very cheap if pmetal is the serving backend — confirm whether
   you want Linus to advertise both endpoints from Phase 2a or stay OpenAI-only until a harness demands Anthropic-compat.
6. **Manifold-Constrained Hyper-Connections (`pmetal-mhc`).** This maps directly onto the JPmHC paper (`2602.18308`) in
   the context folder. Are you interested in running mhc as a Phase 6 training experiment, or does it stay a curiosity?
