# Native Low-Bit Apple Silicon Inference Synthesis

## What this document is

A synthesis of eleven paper-notes that together describe the most internally
coherent operational thread in the Linus corpus: the path from "can a 1-bit
LLM exist" through "here is an 8B native-ternary checkpoint runnable on
M1 Max today, and here is the streaming machinery that makes anything
larger tractable." Three sub-threads — the BitNet research line out of
Microsoft Research (seven papers), the Bonsai productized line out of
PrismML (two whitepapers), and the larger-than-RAM streaming work (two
papers from Apple and Anthropic + Daniel Woods) — are unified by a
single question: *how do you run capable LLMs efficiently on Apple
Silicon under 32 GB of unified memory?*

The thread predates the eight-group triage that organized the rest of
the corpus; it absorbed the existing BitNet thread in the
[paper-landscape](../landscapes/paper-landscape.md) and the
larger-than-RAM streaming pair, and the two new Bonsai whitepapers shift
its center of gravity. This synthesis formalizes the previously implicit
"Group I" so the Phase 1c benchmark spike, the Phase 2 Worker selection,
the Phase 6 fine-tuning roadmap, and the Phase 6d streaming-or-not
scoping decision all work from the same picture.

The headline claim is short. **In roughly two years the field went from
"1-bit LLMs are possible in principle" (BitNet, late 2023) to "the first
MLX-native, Apache-licensed, downloadable native-ternary 8B checkpoint
runs on consumer Apple Silicon" (Bonsai Ternary 8B, April 2026).** That
trajectory closes the gap between the BitNet research line and Linus's
Phase 1c spike: the spike was originally scoped around BitNet b1.58 2B4T,
and Bonsai's 8B release fundamentally changes what "the most capable
native-low-bit Worker we can run on M1 Max" means. The Phase 6d stretch
target — opportunistic ternary >8B integration if the community released
one — has been delivered ahead of schedule. The two streaming papers
remain the path for whatever does not fit, but Bonsai 8B at 1.15–1.75 GB
of weight footprint makes that "whatever" a much smaller residual than
it was a year ago.

---

## The papers at a glance

**The BitNet research line — Microsoft Research, 2023–2025:**

- [BitNet (2310.11453, 2023-10)](../paper-notes/2310.11453v1.md) — the
  founding paper. BitLinear, the first 1-bit Transformer trained from
  scratch with `{−1, +1}` weights and 8-bit activations. Power-law
  scaling holds, beats post-training quantization at 6.7B.
- [BitNet b1.58 (2402.17764, 2024-02)](../paper-notes/2402.17764v1.md) —
  adds the zero state. Ternary `{−1, 0, +1}` weights match FP16 LLaMA
  perplexity and downstream task accuracy at 3B and above. The variant
  the field means when it says "BitNet" today.
- [BitNet a4.8 (2411.04965, 2024-11)](../paper-notes/2411.04965v1.md) —
  first push to 4-bit activations via hybrid quantization plus
  sparsification. Mostly superseded by BitNet v2.
- [BitNet v2 (2504.18415, 2025-04)](../paper-notes/2504.18415v2.md) —
  4-bit activations done elegantly via Hadamard transforms. Current best
  W1.58A4 design; enables 4-bit KV cache.
- [BitNet b1.58 2B4T (2504.12285, 2025-04)](../paper-notes/2504.12285v2.md)
  — the released open-weights checkpoint. 2B parameters, 4T training
  tokens, instruction-tuned via SFT+DPO. 0.4 GB non-embedding memory,
  29 ms TPOT on CPU, average 54.19 across 17 benchmarks.
- [bitnet.cpp (2502.11880, 2025-02)](../paper-notes/2502.11880v1.md) —
  the CPU inference runtime that makes BitNet b1.58 2B4T fast on Apple
  Silicon. 2.15× → 4.91× over FP16 on M2 Ultra; the only paper in the
  thread with directly published Apple Silicon throughput.
- [BitNet Distillation (2510.13998, 2025-10)](../paper-notes/2510.13998v1.md)
  — three-stage pipeline (SubLN insertion + 10B-token continued
  pre-training + multi-loss distillation) that converts any FP16 model
  into a 1.58-bit BitNet for a specific downstream task. ~0.25% the
  cost of from-scratch BitNet training.

**The Bonsai productized line — PrismML, 2026:**

- [Bonsai 1-bit 8B (2026-03-31)](../paper-notes/bonsai-1-bit-8b-whitepaper.md)
  — Qwen3-8B compressed to a custom group-wise 1-bit format
  (`Q1_0_g128`). 1.15 GB on disk, 70.5 average across six benchmarks,
  131 tok/s on M4 Pro via MLX. Apache 2.0; ships with MLX, Metal, and
  CUDA kernels.
- [Bonsai Ternary 8B (2026-04-16)](../paper-notes/bonsai-ternary-8b-whitepaper.md)
  — same recipe, ternary `{−1, 0, +1}` instead of binary. 1.75 GB on
  disk, 75.5 average (95% of FP16 Qwen3-8B's 79.3), 83 tok/s decode on
  M4 Pro. The first openly released native-ternary 8B checkpoint;
  structurally the BitNet b1.58 weight scheme applied as PTQ to Qwen3.

**The larger-than-RAM streaming line:**

- [LLM in a Flash (2312.11514, 2023-12)](../paper-notes/2312.11514v3.md)
  — Apple's foundation paper. Stream weights from flash via
  activation-sparsity prediction, sliding-window cache, and bundled
  column/row reads. Tested on M1 Max specifically. 2× available DRAM,
  4× CPU and 20× NVIDIA-GPU speedup over naïve flash loading.
- [Flash-MoE (2026-03)](../paper-notes/flash_moe.md) — Anthropic +
  Daniel Woods. 397B-parameter MoE running at 5.74 tok/s sustained on a
  48 GB M3 Max via custom Metal/Objective-C inference engine. Notable:
  primary author is Claude Opus 4.6 itself, working under Daniel Woods'
  direction over a 24-hour collaborative session — the paper is itself
  a Maestro/Worker artifact.

---

## The trajectory: research → engineering → productization

The eleven papers, read in chronological order, trace a single arc from
existence proof to deployable artifact in roughly two years.

In late **2023** the question was whether 1-bit LLMs could exist at all
at production scale. The original BitNet paper showed they could:
training from scratch with binary `{−1, +1}` weights and 8-bit activations
inside a custom `BitLinear` layer obeyed the same power-law scaling as
FP16 baselines, just shifted by a small constant. The paper was a
demonstration, not a deployment. The smallest model was 125M; the
biggest was 30B; the published throughput was estimated 7-nm matmul
energy, not measured silicon performance. Apple Silicon was not in the
picture. In parallel and unrelated, Apple's "LLM in a Flash" paper
opened the streaming axis: Mac hardware ratios — small DRAM, big fast
flash, sequential reads cheap, random reads expensive — could be
exploited by predictors of which neurons would activate, allowing
larger-than-RAM models to run on consumer hardware. Two early shoots
from two different roots.

**2024** added the engineering substance to BitNet. The b1.58 paper
introduced the zero state, taking the alphabet from `{−1, +1}` to
`{−1, 0, +1}` — 1.585 bits of information per weight rather than 1, but
with an explicit "drop this connection" signal that turned out to be
what unlocked perplexity parity with FP16 LLaMA at 3B and above. A4.8
pushed activations down to 4 bits via a hybrid scheme combining quantization
with sparsification. None of these papers shipped a checkpoint; they
shipped *recipes for training a checkpoint*. To turn the line into a
deployable artifact someone had to actually train and release one.

**Early 2025** delivered the productization engineering. bitnet.cpp
landed in February, giving the BitNet weight format a CPU inference
runtime tuned specifically for ternary mpGEMM via lookup tables and
mirror consolidation, and — critically for Linus — published M2 Ultra
throughput numbers showing 2.15× to 4.91× over FP16. April brought
BitNet v2 (Hadamard transforms cleaning up the 4-bit-activation path
that a4.8 had pioneered) and, in the same month, the released checkpoint
the field had been waiting two years for: BitNet b1.58 2B4T, 2B parameters
trained on 4T tokens, instruction-tuned via SFT+DPO, packaged as both
bf16 master weights for further training and GGUF for bitnet.cpp.
**0.4 GB non-embedding memory, 29 ms time-per-output-token on CPU.**
For the first time the BitNet thesis was something a researcher could
download.

October 2025 added the recipe for converting other models. BitNet
Distillation showed that with three carefully chosen stages — SubLN
insertion, ~10B tokens of continued pretraining, and multi-loss
distillation from an FP16 teacher — any pretrained Qwen3, Qwen2.5, or
Gemma backbone could be converted to 1.58-bit while preserving FP16
accuracy on classification and summarization. The training cost was
roughly 0.25% of from-scratch BitNet training. Crucially, naïve fine-
tuning *does not work* and gets worse with scale — you cannot just swap
`nn.Linear` for `BitLinear` and continue training. The three-stage
pipeline is load-bearing, and the SubLN insertion is the proximate
cause of the stability that allows distillation to succeed at all.

**Spring 2026** delivered the productized line. PrismML released the
1-bit Bonsai family (1.7B / 4B / 8B) in March, then the ternary
variant in April. Both apply Caltech-IP compression to Qwen3 backbones
at group size 128 with a single FP16 scale per group, and both ship
custom kernels for MLX (Python and Swift), Metal via llama.cpp, and
CUDA via llama.cpp. The 1-bit 8B lands at 1.15 GB on disk, 70.5 average
on a six-benchmark suite covering knowledge / reasoning / math / coding
/ instruction-following / tool-calling, 131 tok/s on M4 Pro via MLX. The
ternary 8B lands at 1.75 GB, 75.5 average — within four points of the
79.3 FP16 Qwen3-8B baseline at 9.36× smaller footprint. The trajectory
that started with the BitNet existence proof in 2023 has produced, in
spring 2026, an MLX-native Apache-licensed 8B-class native-low-bit LLM
that Linus can download today, run on M1 Max, and benchmark against
both the FP16 baselines and the from-scratch BitNet 2B4T checkpoint.

The arc is *research → engineering → productization → MLX-native
deployment*. It took roughly twenty-eight months. The Phase 1c spike,
scoped a year ago around BitNet 2B4T as the one publicly available
artifact, now has a much richer comparison table.

---

## Sub-thread A: The BitNet research line

The BitNet papers are best read as a single sustained engineering
program out of Microsoft Research with a clear technical protagonist
across all seven papers. Each builds on the prior; each closes a
specific gap; together they constitute the most coherent low-bit-LLM
research line in the literature.

The original [BitNet paper](../paper-notes/2310.11453v1.md) introduced
**BitLinear**, the drop-in `nn.Linear` replacement that does almost all
the work of the entire program. Weights are binarized to `{−1, +1}` via
the sign function with a centralization step; activations are quantized
to 8-bit absmax (per-tensor at training, per-token at inference); a
**SubLN** sub-layer LayerNorm goes before activation quantization to
preserve output variance, without which gradients destabilize at scale;
and the matmul output is rescaled by `β` (mean weight magnitude) and
`γ` (max activation magnitude) to dequantize back to a usable range.
The training tricks are load-bearing in the same way: a straight-through
estimator for the non-differentiable sign and clip functions; FP16
latent weights kept alongside the binarized ones, with updates
accumulated in latents and binarization on the forward pass; a
deliberately large learning rate to escape the regime where small
updates fail to flip signs. The contribution is not just the
architecture but the *training recipe* that makes the architecture
trainable.

[BitNet b1.58](../paper-notes/2402.17764v1.md) is the most consequential
paper in the line. The change is small in description — extend the
alphabet from `{−1, +1}` to `{−1, 0, +1}`, costing log₂(3) ≈ 1.585 bits
per weight instead of 1 — and large in effect. The zero state is an
explicit feature filter: it lets the model *drop a connection entirely*
rather than forcing every weight to take a side. The result is FP16
LLaMA perplexity parity at 3B and above, with the gap to FP16 widening
in BitNet's favor as scale grows. The paper introduces an "inference-
optimal" scaling law (loss vs inference energy, not FLOPs) on which
BitNet wins decisively, and proposes the weight-equivalences (13B
BitNet ≈ 3B FP16, 70B BitNet ≈ 13B FP16) that justify the program at
production scale.

The next two papers attack the activation quantization problem.
[BitNet a4.8](../paper-notes/2411.04965v1.md) tries hybrid quantization
plus sparsification: 4-bit absmean for the well-behaved activations
(QKV inputs, FFN up/gate) and top-K sparsification plus 8-bit
quantization for the outlier-heavy ones (attention output projection
`Wo`, FFN down `Wdown`). It works but leaves an inelegant collection
of moving parts. [BitNet v2](../paper-notes/2504.18415v2.md) replaces
the sparsification with **online Hadamard transformation** in the two
outlier-prone layers — H-BitLinear takes the input vector, smears its
energy uniformly across all dimensions via a fast O(n log n) Hadamard
transform, then quantizes the now-Gaussian-shaped vector to 4-bit. The
backward pass exploits Hadamard orthogonality. Removing the Hadamard
causes training to diverge; it is a stability requirement, not an
optimization. v2 also enables 4-bit KV cache with negligible accuracy
loss — directly relevant for long-context inference, where KV cache is
the binding memory pressure.

[BitNet b1.58 2B4T](../paper-notes/2504.12285v2.md) is the released
checkpoint that operationalizes the research program. Architecture
inherits everything: BitLinear, SubLN, squared-ReLU GLU (driving the
sparsity that a4.8 exploited), RoPE, no biases, LLaMA-3 tokenizer for
ecosystem compatibility. Training has three phases: 4T tokens of
pretraining with two-stage learning rate and weight decay schedules
(DCLM web crawls + FineWeb-EDU + synthetic math); SFT on WildChat /
LMSYS-Chat / WizardLM Evol-Instruct / SlimOrca with summed (not
averaged) per-token loss and a larger LR than typical FP fine-tuning;
DPO with UltraFeedback + MagPie. The result lands at 0.4 GB non-
embedding memory, 29 ms time-per-output-token on CPU, 54.19 average
across 17 benchmarks. It loses by ~1 point to Qwen2.5-1.5B (55.23) on
average quality but dominates that comparison decisively on the
memory × quality frontier — half the memory, faster inference, ~10×
lower estimated energy per token. Against post-training-quantized
INT4 versions of Qwen2.5 it wins on both axes (55.01 vs 52.15 average,
0.4 GB vs 0.7 GB).

[bitnet.cpp](../paper-notes/2502.11880v1.md) is the CPU inference
runtime that makes 2B4T fast on real hardware. The technical
contribution is two new mpGEMM kernel families, both written from
scratch because off-the-shelf inference engines either pad ternary
weights to 2-bit (wasting compression and producing slow misaligned
access) or use per-block activation quantization that doesn't match
BitNet's per-tensor INT8 training scheme (so inference output diverges
from training output). The TL family uses element-wise lookup tables
with sign/magnitude consolidation to fit three weights into 5 bits;
I2_S strictly mirrors b1.58's training quantization scheme for
bit-exact inference. **Apple M2 Ultra**: 2.15× to 4.91× speedup over
FP16 across model sizes from 700M to 70B. This is the only paper in
the thread with directly published Apple Silicon numbers, and the
runtime is what would actually serve a BitNet 2B4T checkpoint to a
Linus Worker today.

[BitNet Distillation](../paper-notes/2510.13998v1.md) closes the loop
by giving the line a *recipe for converting other models*. Rather than
train BitNet from scratch (which costs millions of dollars and trillions
of tokens, and is closed to anyone outside frontier labs), BitDistill
takes any pretrained FP16 LLM, inserts SubLN at two specific places per
transformer block, runs ~10B tokens of continued pretraining to close
the scaling gap, then performs distillation-based fine-tuning with both
logit KL divergence (temperature 5) and single-layer attention relation-
matrix distillation MiniLM-style. The result preserves nearly all of the
FP16 source model's accuracy on classification and summarization while
delivering 10× memory reduction and 2.65× CPU inference speedup. The
naïve "swap `nn.Linear` for `BitLinear` and continue training" approach
loses 13–15 accuracy points and gets *worse* with scale — the SubLN
insertion plus continued pretraining are what make the optimization
stable. Cost is roughly 0.25% of from-scratch BitNet training. For
Linus Phase 6, this is plausibly the single most actionable paper in
the line: it converts "we can use BitNet someday once Microsoft
releases an MLX checkpoint at the size we need" into "we can convert
any HuggingFace model into a Linus-runnable Worker tomorrow."

---

## Sub-thread B: The Bonsai productized line

The two Bonsai whitepapers represent a different production path from
the BitNet line, and the distinction is structurally important to be
honest about: **Bonsai is post-training quantization on a Qwen3-8B
backbone, not from-scratch BitNet pretraining.** Both papers say so
explicitly. The compression method is described as "proprietary Caltech
intellectual property"; no recipe is published. What PrismML ships is a
deployable artifact, not a reproducible training pipeline.

That distinction matters for how Bonsai relates to the BitNet line.
The 1-bit Bonsai 8B uses a custom group-wise 1-bit format (`Q1_0_g128`):
each weight is one sign bit, with a single FP16 scale per group of 128
weights along the matrix axis, giving 1.125 effective bits per weight in
GGUF (1.25 in MLX, where a quirk of MLX's quantization API requires a
bias term per group). This is structurally **closer to the original
BitNet's `{−1, +1}` regime** than to b1.58's ternary, but with the
practical wrinkle that Bonsai is applied as PTQ on Qwen3 rather than
trained from scratch. Quality-wise the result is striking: 70.5 average
across the six-benchmark suite (MMLU-Redux, MuSR, GSM8K, HumanEval+,
IFEval, BFCLv3) for the 8B, vs Qwen3-8B at 79.3 in FP16 — about nine
points of quality lost to the squeeze. That places Bonsai 1-bit 8B
above Llama-3.1-8B (67.1), Hermes-3-8B (65.4), and DeepSeek-R1-Qwen-7B
(55.0) on the same suite, all in 1.15 GB instead of 16+ GB.

The ternary Bonsai 8B is the more directly Linus-relevant artifact.
The weight format is structurally **identical to BitNet b1.58** —
weights in `{−1, 0, +1}` with an FP16 scale per group of 128 along the
matrix axis — applied as PTQ to Qwen3 instead of trained from scratch.
PrismML acknowledges the lineage explicitly, citing both b1.58 and the
original BitNet. The result is 1.75 GB on disk and 75.5 average on the
six-benchmark suite, recovering 95% of the FP16 Qwen3-8B baseline at
9.36× smaller footprint. Five points of quality buys 0.6 GB of footprint
relative to 1-bit Bonsai. The smaller the model, the more the zero
state buys: ternary gains 5.0 average points over binary at 8B, 7.4 at
4B, 7.9 at 1.7B. This is consistent with the obvious intuition — smaller
models are less able to afford bits on connections that should be off,
so the explicit "this connection doesn't matter" signal helps more. At
the 8B scale Linus most likely deploys, ternary's 95% recovery beats
1-bit's 89% by a margin large enough that ternary is the right default
for general-purpose Worker tasks. 1-bit remains the choice when
0.6 GB matters — phone targets, KV-cache-heavy long-context inference,
or many concurrent Workers fighting for unified memory.

Two operational caveats deserve attention. The first is that the
Bonsai throughput numbers are reported on **M4 Pro 48 GB**, not M1 Max
32 GB. Bandwidth differs (M4 Pro ~273 GB/s, M1 Max ~400 GB/s), and
the 1-bit kernel is bandwidth-bound, so M1 Max may actually be faster
than the published numbers suggest — but Linus cannot know without
measuring. The second is more structural and the most operationally
significant fact in either Bonsai paper: **MLX has no efficient native
ternary kernel**. Bonsai Ternary 8B's 5.2× speedup over FP16 on M4 Pro
is achieved by routing through MLX's existing 2-bit kernel path. The
on-disk size is 1.75 GB, but the in-memory size is 2.16 GiB because
the deployment uses 2-bit storage. Throughput numbers are what 2-bit
kernels get you, not what true 1.58-bit storage and arithmetic could
deliver. This is the single most tractable Linus contribution
opportunity in the corpus, and it surfaces on its own below.

The Bonsai release accomplishes two things the BitNet line had not.
First, it scales: there is no released BitNet b1.58 8B. The largest
released BitNet checkpoint is 2B4T. Bonsai Ternary 8B fills exactly
that gap and is in practice **the first openly released and benchmarked
native-ternary 8B checkpoint available for download**. Whether it
"counts as" BitNet b1.58 8B is a labeling question; mechanically, in
inference, it is. Second, it ships MLX kernels. bitnet.cpp is CPU-only
on Apple Silicon (NEON SIMD on ARM, no Metal, no ANE). Bonsai ships
custom kernels for MLX in both Python and Swift, and for Metal via a
PrismML fork of llama.cpp. For the first time, Apple Silicon GPU
acceleration of a low-bit LLM ships in a downloadable package.

---

## Sub-thread C: The larger-than-RAM streaming line

The two streaming papers attack a different problem from low-bit
quantization: not "how do you make weights smaller," but "how do you
run a model whose weights don't fit at all." The two are substitute
solutions to the same underlying constraint — limited unified memory
on consumer Apple Silicon — and Bonsai's existence shifts the balance
between them in a specific way that matters for Phase 6d planning.

[LLM in a Flash](../paper-notes/2312.11514v3.md) is the conceptual
foundation, and the only paper in the corpus published *by Apple* that
directly addresses Linus's hardware. The premise is the Mac hardware
ratio: M1 Max has perhaps 10 GB of effectively available DRAM for
inference but ~100 GB of fast flash, and ~6 GiB/s sequential SSD reads
versus much slower random access. Standard inference treats this hardware
as if it were a server with infinite DRAM. Apple's recipe is to do the
opposite: store weights on flash, predict via a small per-layer low-rank
predictor (~4 GPU-hours per layer to train) which FFN neurons will
activate for the current token, and load only those into DRAM. Bundle
columns of the up-projection with rows of the down-projection so they
arrive in one read. Maintain a sliding-window cache of recently active
neurons so each new token only loads the *delta*. The result is that a
7B Llama-2 runs on a device with 4 GB free DRAM, with 4× CPU and 20×
NVIDIA-GPU speedup over naïve flash loading, and zero-shot accuracy
preserved. The paper is the design doc for [`repos/mlx-flash`](../../repos/mlx-flash/),
which operationalizes this for dense MLX models.

[Flash-MoE](../paper-notes/flash_moe.md) is the extreme demonstration
of the same philosophy. A 397-billion-parameter Qwen3.5 MoE running at
5.74 tok/s sustained on a 48 GB M3 Max via custom Metal/Objective-C
streaming. The technique stack is dense: 2-bit re-quantization of the
4-bit experts (RMSE 0.001–0.003, exploiting the fact that within a
group of 64 4-bit values only 16 distinct floats exist anyway); a
three-command-buffer Metal pipeline with the third buffer's expert
fetch dispatched in parallel via `pread()` from the CPU while CMD2
executes on the GPU; hand-written kernels for tiled threadgroup
matrix-vector multiply with inline dequantization; a counterintuitive
finding that *removing* a 9.8 GB application-level expert cache gave
+38% throughput because it was competing for DRAM with the macOS page
cache. The paper is its own existence proof of the Maestro/Worker model
Linus aspires to, written by Claude Opus 4.6 as primary author under
Daniel Woods' direction over a 24-hour collaborative session. The
techniques are too bespoke to vendor, but the methodology — and three
specific lessons (trust the OS page cache, the deferred-CMD3 pipeline,
custom Metal beats MLX by 12× on this workload) — generalize beyond MoE.

The relevance of these two papers to Linus has been **changed by
Bonsai's release** in a specific and significant way. Before Bonsai, the
only credible path to running an 8B-class capable model on M1 Max under
serious memory pressure was either FP16 with most other workloads
killed, or 4-bit quantization (8 GB resident), or flash streaming. With
Bonsai 8B at 1.15–1.75 GB resident, **mlx-flash is unnecessary at the
8B class** — the entire Worker fits trivially in unified memory with
plenty of room for KV cache, KnowledgeBase indices, and orchestration.
Streaming re-emerges only at 30B+ for native quality, or at 70B+ if and
when PrismML scales the Bonsai recipe upward. This is a major Phase 6d
scoping result: the original stretch target was "ternary 8B if community
releases" — Bonsai delivers exactly that. The streaming roadmap shifts
from "we may need this for any reasonably capable Worker" to "we need
this only for the rare model that genuinely exceeds RAM in the regime
that matters."

---

## Cross-cutting threads

**Quantization and streaming as substitute solutions.** The two answers
to "limited unified memory" sit on the same axis. Make the weights
smaller, or stream them in. Each axis has structural costs and benefits:
quantization sacrifices some quality and requires the model to be trained
or distilled to live in low precision; streaming sacrifices throughput
to flash bandwidth and requires per-architecture predictor training. For
the regime where both apply (8B-class capable models on M1 Max), Bonsai
has shifted the balance decisively in favor of quantization. mlx-flash
still wins for fine-tuned dense FP16 models that exceed RAM, and
flash-MoE methodology still wins for genuinely huge MoE models. But the
*default* Phase 2 Worker is now plausibly a low-bit Bonsai variant
running entirely in unified memory, with streaming reserved for the
rarer cases where the model genuinely exceeds RAM.

**MLX as the convergence point.** The three sub-threads come together on
MLX in a way that was not visible a year ago. bitnet.cpp is CPU-only on
Apple Silicon (NEON SIMD); it does not touch Metal or the ANE. Flash-MoE
explicitly *avoided* MLX because it was too slow for the 397B
streaming workload. But Bonsai ships custom MLX kernels in both Python
and Swift, and the underlying MLX framework is becoming the lingua
franca for Apple Silicon LLM inference even when the kernels themselves
are bespoke. This convergence has implications for the Linus inference
layer: an MLX-based serving path is now the natural shape, with bespoke
kernels (PrismML's, eventually pmetal's, possibly Linus's own ternary
kernel) plugged in where they earn their complexity. The CPU-only
bitnet.cpp path remains a valid baseline but is increasingly the
fallback rather than the primary.

**From-scratch pretraining vs PTQ vs distillation.** The corpus now
contains three production paths to a low-bit deployable LLM, with very
different cost and quality profiles. From-scratch BitNet pretraining is
the cleanest in principle — weights trained to live in `{−1, 0, +1}`
from step zero — but costs trillions of tokens and is closed to anyone
outside frontier labs. BitNet Distillation gives a recipe that any lab
with a few thousand GPU-hours can run, taking any pretrained Qwen3 /
Qwen2.5 / Gemma backbone to 1.58-bit at ~0.25% of from-scratch cost.
PrismML's Bonsai is PTQ, taking pretrained Qwen3 to 1-bit or ternary
without (publicly disclosed) continued pretraining; the recipe is
closed but the artifacts are downloadable. Linus's Phase 6 fine-tuning
plan can mix these: LoRA on FP16 Qwen3-8B for Dan's biochem/genomics/
Python corpus, then either BitDistill or Bonsai-style ternarization to
produce the deployable Worker. The right path depends on whether
PrismML opens the Bonsai recipe and whether BitDistill on a small
fine-tuned Worker turns out tractable on M1 Max — both empirical
questions deferrable past Phase 1c.

**Phase 1c spike implications.** The Phase 1c spike was originally
scoped around BitNet 2B4T as the one available native-low-bit checkpoint
worth benchmarking on M1 Max. Bonsai's release expands the scope
materially. The spike should now benchmark, with one unified harness
following the task-completion-time methodology from
[Speed and LLMs (2502.16721)](../paper-notes/2502.16721v1.md), at minimum:
**BitNet b1.58 2B4T** (true native ternary, smallest, the original
Microsoft release), **Bonsai Ternary 8B** (PTQ ternary, largest, MLX-
native, Apache-licensed), **Bonsai 1-bit 8B** (PTQ binary, smallest
8B-class footprint), and **Bonsai Ternary 4B** (the middle-of-fairway
candidate that fits alongside two concurrent Workers in 32 GB). The
methodology must report tok/s on tg128 and pp512, wall-clock task-
completion time on `dan_tasks/`, peak RSS, energy per token where
measurable, and quality on at least the six-benchmark Bonsai suite
(MMLU-Redux, MuSR, GSM8K, HumanEval+, IFEval, BFCLv3). The spike's
result is the basis for the Phase 2 Worker selection, so the
methodology has to be holistic — not tok/s alone, not benchmark score
alone, but the joint Pareto position across cost / quality / latency.

**The MLX kernel gap as a Linus contribution opportunity.** Bonsai
Ternary 8B's most consequential operational caveat is also the most
tractable contribution opportunity in the entire corpus for Linus.
**MLX has no native ternary kernel.** Bonsai's deployed throughput
reflects the MLX 2-bit kernel path, with the on-disk 1.75 GB inflating
to 2.16 GiB resident. A native MLX ternary kernel would close that gap,
and the connection to [`repos/pmetal`](../../repos/pmetal/) — Epistates'
maintained Rust ML platform for Apple Silicon, which already ships
fused low-bit kernels in production — is direct. The contribution is
well-scoped (a single kernel, a known weight format, a known consumer
in PrismML's MLX fork), tractable for Linus's skill profile (Rust +
Metal + careful numerical work, which Dan is actively learning), and
benefits the entire MLX-on-Apple-Silicon community immediately. It
sits naturally as a Phase 1d or Phase 6d work item, after Phase 1c
benchmarking has quantified what the gap costs.

**Flash-MoE's curiosity.** The primary author of the flash-MoE paper is
Claude Opus 4.6 itself, working under Daniel Woods' direction over a
24-hour collaborative session. This is exactly the operating model
[CLAUDE.md](../../CLAUDE.md) describes for Linus — the Maestro/Worker
discipline applied to a research-engineering artifact. The paper is
worth studying not just for its technical content but as an existence
proof of what disciplined Maestro/Worker collaboration can produce when
the Worker has the right tools and the Maestro has set the spec
correctly. For the Phase 8 BitNet × Flash-MoE × JPmHC speculative
research direction, this is also a sociotechnical existence proof:
ambitious cross-paper synthesis is something a Linus-class assistant
plausibly can do.

**The Phase 6d stretch target now met.** The original Phase 6d roadmap
language ([`docs/landscapes/total-landscape.md` Crossing 2 resolution](../landscapes/total-landscape.md))
set "ternary 8B integration if community releases" as an opportunistic
stretch target. Bonsai delivers exactly that, ahead of schedule and
with MLX-native deployment kernels included. This calls for an explicit
Phase 6d reframe: the formal target remains "mlx-flash streams any
fine-tuned model that exceeds RAM," but the stretch target has shifted
from "wait for someone to release a ternary 8B" to "evaluate Bonsai
Ternary 8B as the Phase 2 default Worker, with mlx-flash as the path
for whatever genuinely exceeds RAM (Bonsai Ternary 30B+ if PrismML
ever publishes it, or any Linus-fine-tuned model that grows past
~16 GB resident)."

---

## Implications for Linus

The eleven papers translate into a small set of concrete commitments
ranging from Phase 1c (immediate) through Phase 8 (long-horizon
research direction).

**Phase 1c — spike scope expansion.** The BitNet spike originally
scoped around BitNet 2B4T should expand to a four-way comparison:
BitNet 2B4T (baseline, true native ternary, smallest), Bonsai Ternary
8B (the new flagship, MLX-native), Bonsai 1-bit 8B (the footprint-
critical alternative), and Bonsai Ternary 4B (the middle-ground
candidate that fits alongside two concurrent Workers). Run all four
under one unified harness in `benchmarks/dan_tasks/` using the task-
completion-time methodology from
[Speed and LLMs](../paper-notes/2502.16721v1.md) and the evaluation
discipline from [Bonsai's Appendix B](../paper-notes/bonsai-1-bit-8b-whitepaper.md)
(locked dataset revisions, deterministic attention, identical
generation parameters, no per-model prompt tuning, sandboxed code
execution, rule-based scoring with LLM fallback only on extraction
failure). Report joint cost / quality / latency Pareto position; do
not pick a winner on a single metric. The spike's output becomes the
Phase 2 Worker-selection basis.

**Phase 2 — Worker selection and orchestration fan-out.** Bonsai 8B
is a strong candidate for the default Linus Worker. The crucial
architectural consequence is footprint: at 1.15 GB (1-bit) or 1.75 GB
(ternary) on disk, with 2.16 GiB resident in the MLX 2-bit deployment
path, **multiple parallel Bonsai Workers fit comfortably in 32 GB
unified memory**. Four concurrent ternary 8B Workers consume ~9 GB of
weights, leaving ~23 GB for KV caches, KnowledgeBase / Qdrant indices,
orchestration, and the IDE. This strengthens the orchestration-layer
fan-out story enough that **parallel agent fan-out becomes a Phase 2
concern rather than a Phase 3 one**. The ROADMAP can credibly target
"N parallel Workers in unified memory" in the MVP phase.

**Phase 5 — Interface refinement.** The Bonsai footprint also
strengthens the multi-Worker UX story: the orchestration layer can
keep specialized Workers warm (a code Worker via Qwen2.5-Coder-7B, a
general Worker via Bonsai Ternary 8B, a small Worker for fast
classification via BitNet 2B4T at 0.4 GB) without the swap-in / swap-
out friction that an FP16 Worker selection would impose. Worker
specialization becomes operationally cheap.

**Phase 6 — fine-tuning.** Three production paths to a Linus-branded
low-bit Worker now exist, ranked by tractability and risk:
*FP16-LoRA on Dan's domain corpus*, the safe baseline already committed
in the existing planning, leaves a deployable artifact even if the
low-bit paths fail. *BitDistill on a small fine-tuned Worker*, using
the three-stage SubLN-insertion-plus-continued-pretraining-plus-
distillation pipeline, is the published recipe for converting any
HuggingFace FP16 model to 1.58-bit; cost is dominated by the ~10B-token
continued pretraining step, which on M1 Max needs a benchmark spike to
verify is hours/days/weeks. *Bonsai-style PTQ* on a domain-fine-tuned
Qwen3-8B is appealing because the Bonsai artifacts validate the format,
but the recipe is closed; either PrismML opens it or the community
reverse-engineers it. The pragmatic Phase 6 sequence is FP16-LoRA first
(unconditional), then BitDistill on the small fine-tuned Worker as the
first low-bit pass (when the spike confirms tractability), then watch
PrismML for either an opened recipe or a Bonsai-LoRA workflow.

**Phase 6d — streaming as residual.** Reframe Phase 6d explicitly:
mlx-flash is the path for any *future* fine-tuned model that genuinely
exceeds RAM. Bonsai's existence makes the 8B-class regime not need
streaming at all. The streaming roadmap shifts from "we may need this
for any capable Worker" to "we need this only for the rare large fine-
tuned Worker that genuinely exceeds RAM, or for opportunistic ternary
30B+ if PrismML ever scales the Bonsai recipe upward." Flash-MoE stays
methodology-only reference (no Linus dependency on its bespoke Metal
codebase, but the OS-page-cache lesson and the deferred-CMD3 pipeline
pattern inform the Linus inference layer when it eventually has its
own kernel work).

**Phase 8 — the speculative cross-product.** A "Bonsai-MoE-streamed-
with-Cayley-stability" research direction now has materially more
plausibility than it did a year ago. Eight Ternary Bonsai 8B Workers
in parallel consume ~14 GB of weights — a fan-out that wasn't credible
at FP16 even with 4-bit quantization. Combining JPmHC's Cayley-
stabilized hyper-connections with BitNet ternary weights and Flash-MoE
streaming would push the single-machine inference frontier further;
nothing in the ROADMAP is gated on this, but it remains the most
ambitious natural cross-product the corpus collectively points at.

**MLX ternary kernel as a Linus contribution.** The most tractable,
well-scoped, immediately community-beneficial contribution opportunity
in the entire Linus corpus is a native MLX ternary kernel that exploits
the actual zeros in the Bonsai Ternary weight format rather than
encoding them as 2-bit values. The contribution is bounded (one kernel,
known format, known consumer in PrismML's MLX fork), aligned with the
[`repos/pmetal`](../../repos/pmetal/) Rust+Metal kernel work that Linus
already tracks, and benefits every Apple Silicon BitNet user on day one.
Worth scoping as a Phase 1d (immediately after the Phase 1c spike
quantifies the deployment-path tax) or Phase 6d (alongside the
streaming-or-not scoping decision) work item.

---

## Tensions and open questions

The Phase 1c spike, the Phase 2 Worker selection, and the Phase 6
fine-tuning roadmap all need decisions that this synthesis can sharpen
but not finally resolve. The corpus surfaces seven sharp questions:

**1. Should Phase 1c benchmark Bonsai 8B and BitNet 2B4T together
under a unified Worker-selection methodology?** The synthesis says
yes — the natural shape is a four-way comparison with one unified
harness, scoring on the joint cost / quality / latency Pareto position
rather than any single metric. The open question is methodology
authority: should the methodology spec live in
[`docs/specs/phase1c-spike.md`](../specs/) (proposed) or in
[`docs/experimental-protocol.md`](../experimental-protocol.md)
(existing)? Either is defensible; the second is more durable.

**2. Should the MLX ternary kernel gap be a Linus contribution?** This
is the single best-scoped contribution opportunity in the corpus. The
question is whether to scope it as Phase 1d (immediately, while the
spike's measurement of the deployment-path tax is fresh) or Phase 6d
(deferred until streaming-or-not scoping, when the broader low-bit
inference story has more empirical grounding). The Phase 1d framing is
more aggressive but produces a Linus contribution earlier; the Phase 6d
framing is safer but risks the gap being closed by someone else first.

**3. Bonsai 1-bit vs ternary: what is the right Worker default?** At
8B, ternary's 95% quality recovery vs binary's 89% is a substantial
gap, and the 0.6 GB extra footprint (1.75 GB vs 1.15 GB) is small
relative to 32 GB. The synthesis predicts ternary as the right default
for general-purpose Worker tasks, with binary as opt-in for footprint-
critical paths (phone, KV-cache-heavy long contexts, many concurrent
Workers). Phase 1c benchmark data will resolve this empirically; the
question is what quality margin or task-specific weakness in 1-bit
would trigger the switch.

**4. Should pmetal's low-bit Rust kernels be evaluated as an
alternative to MLX-native Bonsai serving?** pmetal already ships fused
low-bit kernels in production. The Bonsai release vendors a PrismML
fork of MLX with its own custom kernels. Long-term the question is
whether Linus pins to the PrismML fork (a real maintenance liability),
contributes upstream MLX support for scale-only quant formats (which
would let MLX match GGUF's 1.125 bits/weight), or waits for pmetal to
subsume both. This deserves its own ADR before the inference layer
hardens.

**5. For Phase 6, is BitDistill on a small fine-tuned Worker more
tractable than waiting for or reverse-engineering Bonsai PTQ?** The
BitDistill recipe is published and the cost dominated by ~10B tokens
of continued pretraining; on M1 Max this could be hours, days, or
weeks depending on how functional MLX's BitNet training path is. The
Bonsai recipe is closed but the artifacts are downloadable. A small
benchmark spike to measure the BitDistill continued-pretraining cost on
M1 Max would scope this; the question is when to run it (Phase 6a vs
Phase 6b vs deferred until PrismML's posture clarifies).

**6. Is "Native Low-Bit Apple Silicon" worth its own dedicated
benchmark suite distinct from `benchmarks/dan_tasks/`?** The Bonsai
papers use a six-benchmark suite (MMLU-Redux, MuSR, GSM8K, HumanEval+,
IFEval, BFCLv3) as the standard low-bit-LLM comparison set. Mirroring
that suite in a `benchmarks/low_bit/` subdirectory would let Linus
reproduce published numbers and track the low-bit landscape over time
as new releases land. The alternative is folding the same benchmarks
into `benchmarks/dan_tasks/` as one of several scoring axes. The
synthesis weakly prefers the dedicated suite, on the grounds that low-
bit is a sufficiently distinct frontier to warrant its own observability
surface, but reasonable people can disagree.

**7. Is mlx-flash deprecated for Phase 6d's *original* purpose?** The
original Phase 6d framing scoped streaming as the path for any fine-
tuned Worker that exceeded RAM. Bonsai's compactness makes the 8B
class fit trivially. The honest answer is that mlx-flash is not
deprecated — it is *narrowed in scope* — and the Phase 6d formal
target should be rewritten to reflect that. Fine-tuned models that
genuinely exceed RAM (Linus-branded 30B+ or any opportunistic ternary
30B+ from PrismML) remain the proper streaming targets. The Bonsai
existence proof has shifted Phase 6d's center of gravity, not removed
its motivation.

---

## Where this synthesis fits

This synthesis is the third in the Linus corpus to cross multiple
sub-threads and explicit landscape Crossings. The
[memory synthesis](memory-synthesis.md) argued that memory is the
load-bearing architectural pillar that all other pillars rest on; the
[security synthesis](security-synthesis.md) and
[LLM Wiki synthesis](llm-wiki-synthesis.md) similarly span multiple
papers and Crossings. This one argues that **native low-bit inference
on Apple Silicon is the load-bearing operational pillar** — the substrate
that makes every other Linus capability tractable on Dan's hardware
rather than aspirational.

The connections to the rest of the corpus are direct. The memory pillar
treats 1-bit / ternary substrate as one axis of the "structure compounds"
thesis ([memory synthesis Layer A](memory-synthesis.md)) — a Linus
Worker substrate hosted on a recurrent / minGRU / SSM architecture with
BitLinear gates is the most extreme hardware-friendly substrate the
combined corpus points at, and the Phase 8 speculative direction in the
memory synthesis points at the same cross-product as the BitNet × Flash-
MoE × JPmHC speculation here. The agentic systems thread benefits
directly: cheaper Workers enable more parallel agentic fan-out, and the
Bonsai footprint puts that fan-out in Phase 2 rather than Phase 3. The
biological foundation models thread (Group A) interacts in a more
speculative way: foundation models could plausibly be ternary-distilled
via BitDistill, though no domain-specific BitDistill recipe has been
published and the foundation-model context lengths typical of biology
work may be where 4-bit KV cache from BitNet v2 matters most.

The local repository anchors are concrete.
[`repos/Bonsai-demo`](../../repos/Bonsai-demo/) is the local clone of
PrismML's release with both 1-bit and ternary checkpoints; it is the
deployment surface for the Phase 1c spike.
[`repos/BitNet`](../../repos/BitNet/) is Microsoft's reference
implementation, including bitnet.cpp and (per the BitDistill paper's
claims) the BitDistill training code; it is the comparison baseline and
the BitDistill source. [`repos/mlx-flash`](../../repos/mlx-flash/) is
the streaming reference Linus would integrate against if a fine-tuned
Worker exceeds RAM. [`repos/pmetal`](../../repos/pmetal/) is the
long-term native runtime where a Linus-contributed MLX ternary kernel
would land. [`repos/ANE`](../../repos/ANE/) is the methodology reference
for any future ANE-side work; per the Crossing 1 resolution, Linus's
own code stays on public APIs, with pmetal as the supported ANE path.

The landscape doc connections close the loop. This synthesis formalizes
the union of [Crossing 1 (BitNet → Apple Silicon → ANE)](../landscapes/total-landscape.md#crossing-1-the-bitnet--apple-silicon--ane-bridge)
and [Crossing 2 (the streaming axis)](../landscapes/total-landscape.md#crossing-2-the-streaming-axis-dense-mlx-flash-vs-sparse-flash-moe-vs-composite-1-bit-streamed),
and adds the Bonsai productized line as a third axis that bridges them.
The next round of edits to
[`docs/landscapes/paper-landscape.md`](../landscapes/paper-landscape.md)
should promote the existing "BitNet" and "Larger-than-RAM inference"
sections into a unified "Native Low-Bit Apple Silicon Inference" group
pointing at this synthesis. The
[`docs/landscapes/synthesis-landscape.md`](../landscapes/synthesis-landscape.md)
and [`docs/questions/open-questions.md`](../questions/open-questions.md)
should pick up the seven open questions above.

---

*This synthesis should be revisited when the Phase 1c spike results
land (it will turn the four-way comparison into concrete Worker-selection
data), when PrismML opens or refuses to open the Bonsai compression
recipe (the Phase 6 fine-tuning path depends on this), when an MLX
native ternary kernel lands either from PrismML or from a Linus
contribution (it removes the deployment-path tax that limits the
Bonsai numbers reported here), and whenever a new ternary or 1-bit
checkpoint at 8B+ scale lands in the open ecosystem.*
