# Bonsai-demo (`PrismML-Eng/Bonsai-demo`)

## 1. Purpose and scope

Bonsai-demo is PrismML's runner repository for two families of small,
natively-trained low-bit LLMs: **Bonsai** (true 1-bit weights) and
**Ternary-Bonsai** (1.58-bit ternary weights, packed in a `Q2_0` 2-bit format
for hardware friendliness). Each family ships in 1.7B, 4B, and 8B sizes,
with both GGUF (for llama.cpp) and MLX builds. The repo itself is mostly
setup scripts plus two whitepapers; the real artifacts are the pretrained
model weights on Hugging Face and the upstream `llama.cpp` PRs that merged
the 1-bit `Q1_0` format into mainline across CPU, Metal, CUDA, and Vulkan
backends. For Linus this is the canonical 1-bit-on-Apple-Silicon pathway.

## 2. Architecture summary

Pretrained weights are distributed in two formats: GGUF for llama.cpp, and
native MLX `1bit` / `2bit` packings. On Apple Silicon the setup script
clones PrismML's `llama.cpp` fork, builds with Metal, and also clones their
MLX fork and does `uv sync --extra mlx`. The 1-bit path uses the
newly-merged upstream `Q1_0` Metal kernel; the 1.58-bit path uses a `Q2_0`
(2-bit) packing where each ternary weight gets 2 bits, which wastes some
representational space (1.58 vs 2) but maps cleanly onto existing 2-bit
Metal / CUDA paths and unlocks fast kernels without writing new hardware-
level code. The MLX path uses stock MLX's existing 2-bit support for
ternary, no fork required. A `llama-server` chat UI at port 8080 and an
Open WebUI adapter at port 9090 are provided for quick interaction. Context
sizes are tuned by `--fit`; the 8B model supports 65k tokens with ~10.5 GB
memory.

## 3. What's reusable in Linus

A great deal, and directly. The pretrained model weights themselves are the
first thing to grab — `prism-ml/Bonsai-8B-mlx-1bit` and
`prism-ml/Ternary-Bonsai-8B-mlx-2bit` are drop-in candidates for Linus's
Phase 1c benchmark sweep, running against Dan task suite alongside the
Qwen/Mistral baselines. The PrismML MLX fork's 1-bit kernels are a
reference implementation worth reading when Linus eventually wants its own
custom Metal low-bit kernels — Bonsai ran these to upstream, so the PRs
themselves are the documentation. The `llama-server` OpenAI-compatible
serving binary (from PrismML's fork) is a zero-code path to getting 1-bit
models behind an HTTP endpoint while Linus's own router is still being
built in Phase 2a.

## 4. What's inspiration only

The Bonsai team's upstreaming strategy — ship pretrained models plus
working backend kernels across *all* hardware targets in one release — is
the template for how an Apple Silicon 1-bit ecosystem becomes real rather
than staying a research curio. The whitepapers (included in the repo)
likely contain training-recipe details worth pulling into Linus's Phase 6
planning, even if Linus ends up using distillation (BitDistill,
`2510.13998`) rather than training from scratch.

## 5. What's incompatible or out of scope

Nothing substantive is incompatible. The setup script installs `uv` and a
`.venv` per-repo, which collides lightly with the Linus `conda activate
linus` convention — fine for running Bonsai outside Linus's env, but
bringing the Bonsai runtime into Linus's env would need minor packaging
care. The 1-bit `Q1_0` format uses group size 128 vs upstream `TQ1_0`'s
group size 256, so the formats are *not* interchangeable; any Linus code
that loads Bonsai weights must use PrismML's kernel, not stock llama.cpp's
TQ paths.

## 6. Recommendation: **Integrate (experimentally)**

Pull Bonsai-8B-mlx-1bit and Ternary-Bonsai-8B-mlx-2bit via the setup
script. Add them to Phase 1c's benchmark sweep alongside
`qwen2.5-coder:7b`, `mistral:7b-instruct`, and BitNet b1.58 2B4T. Use the
bundled `llama-server` as a stand-in OpenAI-compatible endpoint in the
Phase 1e Maestro/Worker loop — it's the cheapest way to get a 1-bit local
model behind HTTP before `pmetal serve` is evaluated. If Ternary-Bonsai-8B
lands near Qwen-7B quality on Dan task suite while fitting in ~2.5 GB, it
meaningfully reframes what "local worker model" means on 32 GB.

## 7. Questions for Dan

- **Bonsai-8B and Ternary-Bonsai-8B in the Phase 1c baseline sweep?** This
  is the cheapest test of the 1-bit quality-cost frontier on your
  hardware. Happy to write a smoke-test spec for it.
- **PrismML's `llama-server` as the interim OpenAI-compatible endpoint for
  the Phase 1e Maestro/Worker loop?** It ships today and routes to the
  Metal backend, buying time before `pmetal serve` is evaluated. The
  alternative is staying on Ollama and accepting that Ollama does not yet
  have `Q1_0` Metal kernels.
- **Native-1-bit vs. distilled-to-1-bit (BitDistill) as Linus's fine-tuning
  path.** Bonsai trained from scratch with 1-bit / ternary weights.
  BitDistill takes an FP16 model and distills down. Different risks. Do
  you want to run both experiments in parallel at Phase 6, or pick a
  lane?
- **PrismML's llama.cpp and MLX forks as upstream-tracking dependencies.**
  They've committed to upstreaming; do we track their forks as study
  references and adopt the upstreamed kernels once merged, or pin a
  specific fork commit as a Linus dependency?
