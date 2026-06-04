# Native Low-Bit Apple Silicon Inference Synthesis

## What this document is

A synthesis of twelve paper-notes that together describe the most internally coherent operational thread in the Linus
corpus: the path from "can a 1-bit LLM exist" through "here is an 8B native-ternary checkpoint runnable on M1 Max today,
here is the streaming machinery that makes anything larger tractable, and here is a frontier-class trillion-parameter
MoE that lives at the intersection of both." Four sub-threads — the BitNet research line out of Microsoft Research
(seven papers), the Bonsai productized line out of PrismML (two whitepapers plus a public announcement), the
larger-than-RAM streaming work (two papers from Apple and Anthropic + Daniel Woods), and the new Kimi-K2 frontier-MoE
candidate (Moonshot AI, 2025-07) — are unified by a single question: _how do you run capable LLMs efficiently on Apple
Silicon under 32 GB of unified memory?_

The thread predates the eight-group triage that organized the rest of the corpus; it absorbed the existing BitNet thread
in the [paper-landscape](../landscapes/paper-landscape.md) and the larger-than-RAM streaming pair, the two Bonsai
whitepapers shifted its center of gravity in spring 2026, and the Kimi-K2 fold-in (added 2026-05-09) raises the ceiling
of what the synthesis can plausibly target. This document formalizes the previously implicit "Group I" so the Phase 1c
benchmark spike, the Phase 2 Worker selection, the Phase 6 fine-tuning roadmap and possible base-model swap, the Phase
6d streaming-or-not scoping decision, and the Phase 8 Linus-flavored frontier-MoE research direction all work from the
same picture.

The headline claim has grown a third clause. **In roughly two years the field went from "1-bit LLMs are possible in
principle" (BitNet, late 2023) to "the first MLX-native, Apache-licensed, downloadable native-ternary 8B checkpoint runs
on consumer Apple Silicon" (Bonsai Ternary 8B, April 2026), and in mid-2025 a frontier-class 1T-parameter MoE
(Kimi-K2-Instruct) was released under a Modified MIT license whose architecture is sized such that an int4 or
ternary/1-bit Linus-flavored variant is plausibly streamable on M1 Max + a 600 GB external SSD.** That third clause is
load-bearing: BitNet/Bonsai built the 1-bit substrate; flash-streaming made >32 GB MoE feasible on consumer Apple
Silicon; **Kimi-K2 is the candidate model that could combine both for Linus**. The Phase 6d stretch target —
opportunistic ternary >8B integration if the community released one — has been delivered ahead of schedule by Bonsai.
The Phase 6/8 ceiling — a frontier-class agentic base model that Linus can plausibly fine-tune and serve under its own
inference layer — has a concrete candidate for the first time. Two ADR seeds named in this synthesis (`DEC-NNNN`
base-model-swap for the Phase 6 Qwen3 → Kimi-K2 base swap, `DEC-NNNN` low-bit-kimi-variant for the Phase 8
Linus-flavored 1-bit Kimi-K2 variant — soft seeds, not reservations; the previously-cited DEC-0055/0056 are now taken by
other landed ADRs) are open commitments, not speculation.

---

## The papers at a glance

**The BitNet research line — Microsoft Research, 2023–2025:**

- [BitNet (2310.11453, 2023-10)](../paper-notes/2310.11453v1.md) — the founding paper. BitLinear, the first 1-bit
  Transformer trained from scratch with `{−1, +1}` weights and 8-bit activations. Power-law scaling holds, beats
  post-training quantization at 6.7B.
- [BitNet b1.58 (2402.17764, 2024-02)](../paper-notes/2402.17764v1.md) — adds the zero state. Ternary `{−1, 0, +1}`
  weights match FP16 LLaMA perplexity and downstream task accuracy at 3B and above. The variant the field means when it
  says "BitNet" today.
- [BitNet a4.8 (2411.04965, 2024-11)](../paper-notes/2411.04965v1.md) — first push to 4-bit activations via hybrid
  quantization plus sparsification. Mostly superseded by BitNet v2.
- [BitNet v2 (2504.18415, 2025-04)](../paper-notes/2504.18415v2.md) — 4-bit activations done elegantly via Hadamard
  transforms. Current best W1.58A4 design; enables 4-bit KV cache.
- [BitNet b1.58 2B4T (2504.12285, 2025-04)](../paper-notes/2504.12285v2.md) — the released open-weights checkpoint. 2B
  parameters, 4T training tokens, instruction-tuned via SFT+DPO. 0.4 GB non-embedding memory, 29 ms TPOT on CPU, average
  54.19 across 17 benchmarks.
- [bitnet.cpp (2502.11880, 2025-02)](../paper-notes/2502.11880v1.md) — the CPU inference runtime that makes BitNet b1.58
  2B4T fast on Apple Silicon. 2.15× → 4.91× over FP16 on M2 Ultra; the only paper in the thread with directly published
  Apple Silicon throughput.
- [BitNet Distillation (2510.13998, 2025-10)](../paper-notes/2510.13998v1.md) — three-stage pipeline (SubLN insertion +
  10B-token continued pre-training + multi-loss distillation) that converts any FP16 model into a 1.58-bit BitNet for a
  specific downstream task. ~0.25% the cost of from-scratch BitNet training.

**The Bonsai productized line — PrismML, 2026:**

- [Bonsai 1-bit 8B (2026-03-31)](../paper-notes/bonsai-1-bit-8b-whitepaper.md) — Qwen3-8B compressed to a custom
  group-wise 1-bit format (`Q1_0_g128`). 1.15 GB on disk, 70.5 average across six benchmarks, 131 tok/s on M4 Pro via
  MLX. Apache 2.0; ships with MLX, Metal, and CUDA kernels.
- [Bonsai Ternary 8B (2026-04-16)](../paper-notes/bonsai-ternary-8b-whitepaper.md) — same recipe, ternary `{−1, 0, +1}`
  instead of binary. 1.75 GB on disk, 75.5 average (95% of FP16 Qwen3-8B's 79.3), 83 tok/s decode on M4 Pro. The first
  openly released native-ternary 8B checkpoint; structurally the BitNet b1.58 weight scheme applied as PTQ to Qwen3.
- _Companion announcement_ — `context/notes/Announcing 1-bit Bonsai.txt` (PrismML's 2026-03-31 launch piece) frames the
  release as the founding artifact of an "intelligence density" research program out of Caltech, defined as
  `D = -log(P_e)/N` where `P_e = 1 − score/100` and `N` is GB of weight footprint. The announcement positions Bonsai as
  "the first commercially viable 1-bit LLMs," foregrounding the Pareto-frontier shift from the FP16 8B-class cluster to
  the 1.15 GB regime — a positioning that matters for Linus's framing of low-bit not as a research curio but as a
  deployment substrate.

**The larger-than-RAM streaming line:**

- [LLM in a Flash (2312.11514, 2023-12)](../paper-notes/2312.11514v3.md) — Apple's foundation paper. Stream weights from
  flash via activation-sparsity prediction, sliding-window cache, and bundled column/row reads. Tested on M1 Max
  specifically. 2× available DRAM, 4× CPU and 20× NVIDIA-GPU speedup over naïve flash loading.
- [Flash-MoE (2026-03)](../paper-notes/flash_moe.md) — Anthropic + Daniel Woods. 397B-parameter MoE running at 5.74
  tok/s sustained on a 48 GB M3 Max via custom Metal/Objective-C inference engine. Notable: primary author is Claude
  Opus 4.6 itself, working under Daniel Woods' direction over a 24-hour collaborative session — the paper is itself a
  Maestro/Worker artifact.

**The Kimi-K2 frontier-MoE candidate:**

- [Kimi-K2 (2507.20534, 2025-07)](../paper-notes/Kimi-K2-2507.20534.md) — Moonshot AI's open-weights frontier model. A
  **1.04-trillion-parameter MoE** with **32B activated parameters per token**, 384 experts (8 active + 1 shared), MLA
  attention, 128K context, pre-trained on 15.5T tokens with **zero loss spikes** thanks to the new MuonClip optimizer.
  Block-fp8 weights under a Modified MIT license. Open-source SOTA on every agentic benchmark axis (65.8 SWE-bench
  Verified single-attempt, 71.6 multi-attempt; 66.1 τ²-Bench; 76.5 ACEBench). For this synthesis it is simultaneously
  the largest weight-streaming target ever credibly proposed for a Linus phase, a Phase 6 LoRA-base candidate that could
  replace Qwen3, and the substrate for a Phase 8 1-bit Linus-flavored variant — three independent strategic vectors plus
  MuonClip as a fourth optimizer-level vector. Sub-thread D below covers the architectural and operational details.

---

## The trajectory: research → engineering → productization

The eleven papers, read in chronological order, trace a single arc from existence proof to deployable artifact in
roughly two years.

In late **2023** the question was whether 1-bit LLMs could exist at all at production scale. The original BitNet paper
showed they could: training from scratch with binary `{−1, +1}` weights and 8-bit activations inside a custom
`BitLinear` layer obeyed the same power-law scaling as FP16 baselines, just shifted by a small constant. The paper was a
demonstration, not a deployment. The smallest model was 125M; the biggest was 30B; the published throughput was
estimated 7-nm matmul energy, not measured silicon performance. Apple Silicon was not in the picture. In parallel and
unrelated, Apple's "LLM in a Flash" paper opened the streaming axis: Mac hardware ratios — small DRAM, big fast flash,
sequential reads cheap, random reads expensive — could be exploited by predictors of which neurons would activate,
allowing larger-than-RAM models to run on consumer hardware. Two early shoots from two different roots.

**2024** added the engineering substance to BitNet. The b1.58 paper introduced the zero state, taking the alphabet from
`{−1, +1}` to `{−1, 0, +1}` — 1.585 bits of information per weight rather than 1, but with an explicit "drop this
connection" signal that turned out to be what unlocked perplexity parity with FP16 LLaMA at 3B and above. A4.8 pushed
activations down to 4 bits via a hybrid scheme combining quantization with sparsification. None of these papers shipped
a checkpoint; they shipped _recipes for training a checkpoint_. To turn the line into a deployable artifact someone had
to actually train and release one.

**Early 2025** delivered the productization engineering. bitnet.cpp landed in February, giving the BitNet weight format
a CPU inference runtime tuned specifically for ternary mpGEMM via lookup tables and mirror consolidation, and —
critically for Linus — published M2 Ultra throughput numbers showing 2.15× to 4.91× over FP16 on CPU (NEON SIMD, no
Metal or ANE path; up to 6.25× on x86). April brought BitNet v2 (Hadamard transforms cleaning up the 4-bit-activation
path that a4.8 had pioneered) and, in the same month, the released checkpoint the field had been waiting two years for:
BitNet b1.58 2B4T, 2B parameters trained on 4T tokens, instruction-tuned via SFT+DPO, packaged as both bf16 master
weights for further training and GGUF for bitnet.cpp. **0.4 GB non-embedding memory, 29 ms time-per-output-token on
CPU.** For the first time the BitNet thesis was something a researcher could download.

October 2025 added the recipe for converting other models. BitNet Distillation showed that with three carefully chosen
stages — SubLN insertion, ~10B tokens of continued pretraining, and multi-loss distillation from an FP16 teacher — any
pretrained Qwen3, Qwen2.5, or Gemma backbone could be converted to 1.58-bit while preserving FP16 accuracy on
classification and summarization. The training cost was roughly 0.25% of from-scratch BitNet training. Crucially, naïve
fine- tuning _does not work_ and gets worse with scale — you cannot just swap `nn.Linear` for `BitLinear` and continue
training. The three-stage pipeline is load-bearing, and the SubLN insertion is the proximate cause of the stability that
allows distillation to succeed at all.

**Spring 2026** delivered the productized line. PrismML released the 1-bit Bonsai family (1.7B / 4B / 8B) in March, then
the ternary variant in April. Both apply Caltech-IP compression to Qwen3 backbones at group size 128 with a single FP16
scale per group, and both ship custom kernels for MLX (Python and Swift), Metal via llama.cpp, and CUDA via llama.cpp.
The 1-bit 8B lands at 1.15 GB on disk, 70.5 average on a six-benchmark suite covering knowledge / reasoning / math /
coding / instruction-following / tool-calling, 131 tok/s on M4 Pro via MLX. The ternary 8B lands at 1.75 GB, 75.5
average — within four points of the 79.3 FP16 Qwen3-8B baseline at 9.36× smaller footprint. The trajectory that started
with the BitNet existence proof in 2023 has produced, in spring 2026, an MLX-native Apache-licensed 8B-class
native-low-bit LLM that Linus can download today, run on M1 Max, and benchmark against both the FP16 baselines and the
from-scratch BitNet 2B4T checkpoint.

The arc is _research → engineering → productization → MLX-native deployment_. It took roughly twenty-eight months. The
Phase 1c spike, scoped a year ago around BitNet 2B4T as the one publicly available artifact, now has a much richer
comparison table.

A fourth point on this arc, sitting orthogonal to the BitNet/Bonsai line but directly relevant to where the synthesis is
heading, was already on the table when Bonsai released. **Kimi-K2-Instruct** (Moonshot AI, July 2025) shipped a
1.04T-parameter MoE under a Modified MIT license with block-fp8 weights and open-source SOTA agentic benchmarks. It is
not low-bit in the BitNet sense and not Apple-Silicon-targeted in any sense, but its architecture (8 active experts of
~44 MB each at FP8, ~350 MB/token streamed shard set, ~15–25 GB of always-resident attention/embed/norm/dense/shared-
expert layer) is sized such that it sits **just past the M1 Max FP8 ceiling, plausibly inside at int4, and comfortably
inside at 1-bit/ternary**. That sizing is what turns Kimi-K2 from "a frontier model Dan can read about" into "a frontier
model whose 1-bit Linus-flavored variant is a credible Phase 8 research target on Dan's hardware." Sub-thread D below
unpacks the math.

---

## Sub-thread A: The BitNet research line

The BitNet papers are best read as a single sustained engineering program out of Microsoft Research with a clear
technical protagonist across all seven papers. Each builds on the prior; each closes a specific gap; together they
constitute the most coherent low-bit-LLM research line in the literature.

The original [BitNet paper](../paper-notes/2310.11453v1.md) introduced **BitLinear**, the drop-in `nn.Linear`
replacement that does almost all the work of the entire program. Weights are binarized to `{−1, +1}` via the sign
function with a centralization step; activations are quantized to 8-bit absmax (per-tensor at training, per-token at
inference); a **SubLN** sub-layer LayerNorm goes before activation quantization to preserve output variance, without
which gradients destabilize at scale; and the matmul output is rescaled by `β` (mean weight magnitude) and `γ` (max
activation magnitude) to dequantize back to a usable range. The training tricks are load-bearing in the same way: a
straight-through estimator for the non-differentiable sign and clip functions; FP16 latent weights kept alongside the
binarized ones, with updates accumulated in latents and binarization on the forward pass; a deliberately large learning
rate to escape the regime where small updates fail to flip signs. The contribution is not just the architecture but the
_training recipe_ that makes the architecture trainable.

[BitNet b1.58](../paper-notes/2402.17764v1.md) is the most consequential paper in the line. The change is small in
description — extend the alphabet from `{−1, +1}` to `{−1, 0, +1}`, costing log₂(3) ≈ 1.585 bits per weight instead of 1
— and large in effect. The zero state is an explicit feature filter: it lets the model _drop a connection entirely_
rather than forcing every weight to take a side. The result is FP16 LLaMA perplexity parity at 3B and above, with the
gap to FP16 widening in BitNet's favor as scale grows. The paper introduces an "inference- optimal" scaling law (loss vs
inference energy, not FLOPs) on which BitNet wins decisively, and proposes the weight-equivalences (13B BitNet ≈ 3B
FP16, 70B BitNet ≈ 13B FP16) that justify the program at production scale.

The next two papers attack the activation quantization problem. [BitNet a4.8](../paper-notes/2411.04965v1.md) tries
hybrid quantization plus sparsification: 4-bit absmean for the well-behaved activations (QKV inputs, FFN up/gate) and
top-K sparsification plus 8-bit quantization for the outlier-heavy ones (attention output projection `Wo`, FFN down
`Wdown`). It works but leaves an inelegant collection of moving parts. [BitNet v2](../paper-notes/2504.18415v2.md)
replaces the sparsification with **online Hadamard transformation** in the two outlier-prone layers — H-BitLinear takes
the input vector, smears its energy uniformly across all dimensions via a fast O(n log n) Hadamard transform, then
quantizes the now-Gaussian-shaped vector to 4-bit. The backward pass exploits Hadamard orthogonality. Removing the
Hadamard causes training to diverge; it is a stability requirement, not an optimization. v2 also enables 4-bit KV cache
with negligible accuracy loss — directly relevant for long-context inference, where KV cache is the binding memory
pressure.

[BitNet b1.58 2B4T](../paper-notes/2504.12285v2.md) is the released checkpoint that operationalizes the research
program. Architecture inherits everything: BitLinear, SubLN, squared-ReLU GLU (driving the sparsity that a4.8
exploited), RoPE, no biases, LLaMA-3 tokenizer for ecosystem compatibility. Training has three phases: 4T tokens of
pretraining with two-stage learning rate and weight decay schedules (DCLM web crawls + FineWeb-EDU + synthetic math);
SFT on WildChat / LMSYS-Chat / WizardLM Evol-Instruct / SlimOrca with summed (not averaged) per-token loss and a larger
LR than typical FP fine-tuning; DPO with UltraFeedback + MagPie. The result lands at 0.4 GB non- embedding memory, 29 ms
time-per-output-token on CPU, 54.19 average across 17 benchmarks. It loses by ~1 point to Qwen2.5-1.5B (55.23) on
average quality but dominates that comparison decisively on the memory × quality frontier — half the memory, faster
inference, ~10× lower estimated energy per token. Against post-training-quantized INT4 versions of Qwen2.5 it wins on
both axes (55.01 vs 52.15 average, 0.4 GB vs 0.7 GB).

[bitnet.cpp](../paper-notes/2502.11880v1.md) is the CPU inference runtime that makes 2B4T fast on real hardware. The
technical contribution is two new mpGEMM kernel families, both written from scratch because off-the-shelf inference
engines either pad ternary weights to 2-bit (wasting compression and producing slow misaligned access) or use per-block
activation quantization that doesn't match BitNet's per-tensor INT8 training scheme (so inference output diverges from
training output). The TL family uses element-wise lookup tables with sign/magnitude consolidation to fit three weights
into 5 bits; I2_S strictly mirrors b1.58's training quantization scheme for bit-exact inference. **Apple M2 Ultra**:
2.15× to 4.91× speedup over FP16 across model sizes from 700M to 70B (up to 6.25× on x86 laptop CPUs). Critically,
bitnet.cpp targets CPU SIMD only — NEON on ARM, AVX2 on x86 — with no Metal or ANE path; the Apple Silicon GPU and
Neural Engine are left on the table. This is the only paper in the thread with directly published Apple Silicon numbers,
and the runtime is what would actually serve a BitNet 2B4T checkpoint to a Linus Worker today, though its CPU-only
nature means it is increasingly a baseline rather than the primary serving path as MLX-native alternatives (Bonsai)
mature.

[BitNet Distillation](../paper-notes/2510.13998v1.md) closes the loop by giving the line a _recipe for converting other
models_. Rather than train BitNet from scratch (which costs millions of dollars and trillions of tokens, and is closed
to anyone outside frontier labs), BitDistill takes any pretrained FP16 LLM, inserts SubLN at two specific places per
transformer block, runs ~10B tokens of continued pretraining to close the scaling gap, then performs distillation-based
fine-tuning with both logit KL divergence (temperature 5) and single-layer attention relation- matrix distillation
MiniLM-style. The result preserves nearly all of the FP16 source model's accuracy on classification and summarization
while delivering 10× memory reduction and 2.65× CPU inference speedup. The naïve "swap `nn.Linear` for `BitLinear` and
continue training" approach loses 13–15 accuracy points and gets _worse_ with scale — the SubLN insertion plus continued
pretraining are what make the optimization stable. Cost is roughly 0.25% of from-scratch BitNet training. For Linus
Phase 6, this is plausibly the single most actionable paper in the line: it converts "we can use BitNet someday once
Microsoft releases an MLX checkpoint at the size we need" into "we can convert any HuggingFace model into a
Linus-runnable Worker tomorrow."

---

## Sub-thread B: The Bonsai productized line

The two Bonsai whitepapers represent a different production path from the BitNet line, and the distinction is
structurally important to be honest about: **Bonsai is post-training quantization on a Qwen3-8B backbone, not
from-scratch BitNet pretraining.** Both papers say so explicitly. The compression method is described as "proprietary
Caltech intellectual property"; no recipe is published. What PrismML ships is a deployable artifact, not a reproducible
training pipeline.

That distinction matters for how Bonsai relates to the BitNet line. The 1-bit Bonsai 8B uses a custom group-wise 1-bit
format (`Q1_0_g128`): each weight is one sign bit, with a single FP16 scale per group of 128 weights along the matrix
axis, giving 1.125 effective bits per weight in GGUF (1.25 in MLX, where a quirk of MLX's quantization API requires a
bias term per group). This is structurally **closer to the original BitNet's `{−1, +1}` regime** than to b1.58's
ternary, but with the practical wrinkle that Bonsai is applied as PTQ on Qwen3 rather than trained from scratch.
Quality-wise the result is striking: 70.5 average across the six-benchmark suite (MMLU-Redux, MuSR, GSM8K, HumanEval+,
IFEval, BFCLv3) for the 8B, vs Qwen3-8B at 79.3 in FP16 — about nine points of quality lost to the squeeze. That places
Bonsai 1-bit 8B above Llama-3.1-8B (67.1), Hermes-3-8B (65.4), and DeepSeek-R1-Qwen-7B (55.0) on the same suite, all in
1.15 GB instead of 16+ GB.

The ternary Bonsai 8B is the more directly Linus-relevant artifact. The weight format is structurally **identical to
BitNet b1.58** — weights in `{−1, 0, +1}` with an FP16 scale per group of 128 along the matrix axis — applied as PTQ to
Qwen3 instead of trained from scratch. PrismML acknowledges the lineage explicitly, citing both b1.58 and the original
BitNet. The result is 1.75 GB on disk and 75.5 average on the six-benchmark suite, recovering 95% of the FP16 Qwen3-8B
baseline at 9.36× smaller footprint. Five points of quality buys 0.6 GB of footprint relative to 1-bit Bonsai. The
smaller the model, the more the zero state buys: ternary gains 5.0 average points over binary at 8B, 7.4 at 4B, 7.9 at
1.7B. This is consistent with the obvious intuition — smaller models are less able to afford bits on connections that
should be off, so the explicit "this connection doesn't matter" signal helps more. At the 8B scale Linus most likely
deploys, ternary's 95% recovery beats 1-bit's 89% by a margin large enough that ternary is the right default for
general-purpose Worker tasks. 1-bit remains the choice when 0.6 GB matters — phone targets, KV-cache-heavy long-context
inference, or many concurrent Workers fighting for unified memory.

Two operational caveats deserve attention. The first is that the Bonsai throughput numbers are reported on **M4 Pro 48
GB**, not M1 Max 32 GB. Bandwidth differs (M4 Pro ~273 GB/s, M1 Max ~400 GB/s), and the 1-bit kernel is bandwidth-bound,
so M1 Max may actually be faster than the published numbers suggest — but Linus cannot know without measuring. The
second is more structural and the most operationally significant fact in either Bonsai paper: **MLX has no efficient
native ternary kernel**. Bonsai Ternary 8B's 5.2× speedup over FP16 on M4 Pro is achieved by routing through MLX's
existing 2-bit kernel path. The on-disk size is 1.75 GB, but the in-memory size is 2.16 GiB because the deployment uses
2-bit storage. Throughput numbers are what 2-bit kernels get you, not what true 1.58-bit storage and arithmetic could
deliver. This is the single most tractable Linus contribution opportunity in the corpus, and it surfaces on its own
below.

The Bonsai release accomplishes two things the BitNet line had not. First, it scales: there is no released BitNet b1.58
8B. The largest released BitNet checkpoint is 2B4T. Bonsai Ternary 8B fills exactly that gap and is in practice **the
first openly released and benchmarked native-ternary 8B checkpoint available for download**. Whether it "counts as"
BitNet b1.58 8B is a labeling question; mechanically, in inference, it is. Second, it ships MLX kernels. bitnet.cpp is
CPU-only on Apple Silicon (NEON SIMD on ARM, no Metal, no ANE). Bonsai ships custom kernels for MLX in both Python and
Swift, and for Metal via a PrismML fork of llama.cpp. For the first time, Apple Silicon GPU acceleration of a low-bit
LLM ships in a downloadable package.

The PrismML announcement (`context/notes/Announcing 1-bit Bonsai.txt`, 2026-03-31) frames the release with a piece of
quantitative rhetoric worth absorbing into the Linus framing of low-bit. Rather than report raw benchmark averages
alone, PrismML defines an **intelligence density** metric `D = −log(P_e)/N` where `P_e = 1 − score/100` and `N` is
weight footprint in GB. The metric assigns greater value to improvements near high accuracy (where further gains are
typically harder) than to equal-sized improvements at lower performance levels. By that measure 1-bit Bonsai 8B scores
1.06/GB, where the closest comparable model in its parameter class (Qwen3-8B itself) scores 0.10/GB — "not just ahead on
this measure; it is in a different regime." The metric is self-serving but the underlying claim survives reasonable
alternative definitions, and the framing is useful: when Linus selects Workers, **quality at fixed footprint** is a
better single-axis summary than benchmark score alone, especially in a 32 GB unified-memory regime where every spare GB
earns interest in concurrent-Worker capacity.

![1-bit Bonsai 8B intelligence density vs other 8B-class models — PrismML announcement, Fig I](../../context/pics/PrismML_Intelligence_Density_Measurement.png)

![1-bit Bonsai 8B raw benchmark scores vs 8B-class models at radically smaller footprint — PrismML announcement, Fig II](../../context/pics/PrismML_Benchmark_Performance.png)

![1-bit Bonsai family Pareto frontier shift — performance vs size across 20 leading instruct models, PrismML announcement, Fig IV](../../context/pics/Bonsai-Performance-vs-Size.png)

![1-bit Bonsai 8B energy consumption (mWh/tok) across hardware platforms — PrismML announcement, Fig III](../../context/pics/Bonsai-Energy-Use.png)

---

## Sub-thread C: The larger-than-RAM streaming line

The two streaming papers attack a different problem from low-bit quantization: not "how do you make weights smaller,"
but "how do you run a model whose weights don't fit at all." The two are substitute solutions to the same underlying
constraint — limited unified memory on consumer Apple Silicon — and Bonsai's existence shifts the balance between them
in a specific way that matters for Phase 6d planning.

[LLM in a Flash](../paper-notes/2312.11514v3.md) is the conceptual foundation, and the only paper in the corpus
published _by Apple_ that directly addresses Linus's hardware. The premise is the Mac hardware ratio: M1 Max has perhaps
10 GB of effectively available DRAM for inference but ~100 GB of fast flash, and ~6 GiB/s sequential SSD reads versus
much slower random access. Standard inference treats this hardware as if it were a server with infinite DRAM. Apple's
recipe is to do the opposite: store weights on flash, predict via a small per-layer low-rank predictor (~4 GPU-hours per
layer to train) which FFN neurons will activate for the current token, and load only those into DRAM. Bundle columns of
the up-projection with rows of the down-projection so they arrive in one read. Maintain a sliding-window cache of
recently active neurons so each new token only loads the _delta_. The result is that a 7B Llama-2 runs on a device with
4 GB free DRAM, with 4× CPU and 20× NVIDIA-GPU speedup over naïve flash loading, and zero-shot accuracy preserved. The
paper is the design doc for [`repos/mlx-flash`](../../repos/mlx-flash/), which operationalizes this for dense MLX
models.

[Flash-MoE](../paper-notes/flash_moe.md) is the extreme demonstration of the same philosophy. A 397-billion-parameter
Qwen3.5 MoE running at 5.74 tok/s sustained on a 48 GB M3 Max via custom Metal/Objective-C streaming.

![Flash-MoE 397B benchmark scatter — quality vs footprint frontier with the streamed Flash-MoE 397B point](../../context/pics/HDtyosvbcAAHMwd.png)
The technique stack is dense: 2-bit re-quantization of the 4-bit experts (RMSE 0.001–0.003, exploiting the fact that
within a group of 64 4-bit values only 16 distinct floats exist anyway); a three-command-buffer Metal pipeline with the
third buffer's expert fetch dispatched in parallel via `pread()` from the CPU while CMD2 executes on the GPU;
hand-written kernels for tiled threadgroup matrix-vector multiply with inline dequantization; a counterintuitive finding
that _removing_ a 9.8 GB application-level expert cache gave +38% throughput because it was competing for DRAM with the
macOS page cache. The paper is its own existence proof of the Maestro/Worker model Linus aspires to, written by Claude
Opus 4.6 as primary author under Daniel Woods' direction over a 24-hour collaborative session. The techniques are too
bespoke to vendor, but the methodology — and three specific lessons (trust the OS page cache, the deferred-CMD3
pipeline, custom Metal beats MLX by 12× on this workload) — generalize beyond MoE.

The relevance of these two papers to Linus has been **changed by Bonsai's release** in a specific and significant way.
Before Bonsai, the only credible path to running an 8B-class capable model on M1 Max under serious memory pressure was
either FP16 with most other workloads killed, or 4-bit quantization (8 GB resident), or flash streaming. With Bonsai 8B
at 1.15–1.75 GB resident, **mlx-flash is unnecessary at the 8B class** — the entire Worker fits trivially in unified
memory with plenty of room for KV cache, KnowledgeBase indices, and orchestration. Streaming re-emerges only at 30B+ for
native quality, or at 70B+ if and when PrismML scales the Bonsai recipe upward. This is a major Phase 6d scoping result:
the original stretch target was "ternary 8B if community releases" — Bonsai delivers exactly that. The streaming roadmap
shifts from "we may need this for any reasonably capable Worker" to "we need this only for the rare model that genuinely
exceeds RAM in the regime that matters." Kimi-K2, covered next, is exactly that rare model.

---

## Sub-thread D: The Kimi-K2 frontier-MoE candidate

The fourth sub-thread is a single paper-note ([Kimi-K2 (2507.20534)](../paper-notes/Kimi-K2-2507.20534.md)) that arrived
in the corpus late but reframes the synthesis's upper bound. Moonshot AI's open-weights release in July 2025 is a
1.04-trillion-parameter MoE with 32B activated parameters per token, 384 experts (8 active + 1 shared), MLA attention,
128K context, pre-trained on 15.5T tokens with — and this is the load-bearing claim of the paper — **zero loss spikes
anywhere** in the training trace. The optimizer that delivered that stability is **MuonClip**: Muon plus a per-head
QK-Clip post-update that, after each Muon step, rescales the query and key projection weights of any attention head
whose maximum pre-softmax logit exceeds threshold τ=100. The mechanism is roughly ten lines of Python on top of an
existing Muon implementation, and it is the kind of optimizer-level intervention that becomes a discipline default if it
generalizes.

Kimi-K2 does not, on first inspection, belong in a synthesis about running LLMs efficiently under 32 GB of unified
memory. The released block-fp8 distribution is ~1.04 TB on disk; resident memory under naïve loading is multi-hundred-
GB; the training infrastructure (256 H800 GPUs with NVLink and 8×400 Gbps RoCE) is a different planet from a MacBook
Pro. But on second inspection — once the synthesis's pre-existing tools (BitNet/Bonsai quantization to 1-bit/ternary,
flash-MoE expert streaming) are brought to bear — the architecture is sized in a way that puts a Linus-flavored variant
inside the M1 Max + 600 GB external SSD envelope. The footprint math from the paper-note is the load-bearing surface.

**The footprint math.** Each MoE expert in Kimi-K2 has hidden dimension 2048; one expert is roughly
`(3 × 7168 × 2048) ≈ 44M parameters → ~44 MB at FP8`. Eight active routed experts plus one shared expert plus
attention/embed/norm/dense-layer overhead gives **~350 MB of expert weights streamed per token at FP8, plus a 15–25 GB
always-resident layer for attention/embeds/norms/dense/shared-expert**. That sustained-bandwidth requirement (~350
MB/token at decode rates) is just past the M1 Max's external-SSD ceiling: the full 1.04 TB FP8 distribution does not fit
on the 600 GB external SSD as-distributed and would require staging. At **int4** the total drops to ~250 GB and the
per-token streamed shard set drops to ~175 MB — fits with headroom, plausibly inside the latency envelope. At
**ternary/1-bit** (1.58 bits/weight or 1 bit/weight) the total drops to ~130–205 GB and per-token streaming drops to
~44–88 MB — comfortably inside Phase 8 territory.

**Three strategic vectors.** Kimi-K2 is simultaneously a Phase 6 LoRA-base candidate, a Phase 6d weight-streaming
target, and a Phase 8 substrate for a 1-bit Linus-flavored MoE. These vectors operate at different time horizons and
have different success criteria, but they are not independent: the Phase 6d feasibility result determines whether the
Phase 6 base swap is even a question, and the Phase 8 1-bit variant is the only path that brings the model fully into
the unified-memory regime (the streaming path keeps it interactive but expensive). The next section unpacks the
combinable-bets thesis that ties them together.

The non-streaming use of Kimi-K2 is **MuonClip as a Phase 6 fine-tuning convention candidate, independent of base-model
choice**. Whether MuonClip generalizes to dense models, to smaller scales, or to MLX implementations on Apple Silicon
are open questions, but the surface area is small enough that a Phase 6 spike could LoRA-fine-tune a 7B–32B Worker with
MuonClip vs. Muon vs. AdamW and settle the matter cheaply. Even a negative result (MuonClip doesn't help LoRA on a small
Worker) is a useful boundary on the technique's domain of validity. This is the kind of paper-supplied optimizer-level
finding that Linus's Phase 6 fine-tuning convention — already committed to FP16-LoRA on Qwen3-8B as the safe baseline —
should explicitly evaluate.

The agentic dimension matters even outside this synthesis's primary frame. Kimi-K2's agentic-data-synthesis pipeline (a
3,000+ MCP tool repository plus 20,000+ synthetic tools, multi-turn rollouts in a stochastic simulator, LLM-judge
filtering against task rubrics) is the closest published template to what Phase 7's biology-skills training will need.
The agentic-systems and skills-and-practices syntheses fold this in directly; here it is mentioned only because Linus's
"capable agentic Worker" requirement is the **reason** the Phase 6 base-swap question is sharp at all. If Qwen3-32B-LoRA
delivered the agentic benchmarks Linus needs, Kimi-K2 would be a curiosity. It does not — Kimi-K2 leads SWE-bench
Verified open-source by ~10 percentage points, τ²-Bench by similar margins — and that gap is what makes the swap
question worth asking.

---

## The combinable-bets thesis: Kimi-K2 × flash-MoE × BitNet/Bonsai

The most consequential strategic move surfaced by this synthesis is the realization that the four sub-threads above are
**combinable** in a specific way that targets a specific deployable artifact. The argument runs in three steps.

**Step 1: BitNet/Bonsai built the 1-bit substrate.** The trajectory from BitNet (existence proof, 2023) through Bonsai
Ternary 8B (deployable artifact, 2026) demonstrates that capable LLMs can live in 1-bit / 1.58-bit / ternary weight
formats with quality losses bounded by single-digit percentage points relative to FP16, that the conversion path can be
either from-scratch pretraining (BitNet b1.58 2B4T), distillation (BitNet Distillation), or post-training quantization
on a strong open base (Bonsai). The substrate is real, the artifacts are downloadable, and the deployment kernels exist
on Apple Silicon for the first time.

**Step 2: Flash-streaming made >32 GB MoE feasible on consumer Apple Silicon.** Flash-MoE's 397B-parameter, 5.74 tok/s
result on a 48 GB M3 Max — combining 2-bit re-quantization of experts, a three-command-buffer Metal pipeline with
deferred CMD3 expert fetch, and the "trust the OS page cache" finding — is the existence proof that the bandwidth-vs-
compute imbalance of MoE inference can be exploited on consumer hardware to run models 4× the size of unified memory.
The methodology is too bespoke to vendor wholesale, but the technique stack generalizes, and the M1 Max + 600 GB
external SSD has roughly half the streaming bandwidth of M3 Max — a degradation factor, not a categorical barrier.

**Step 3: Kimi-K2 is the candidate model that combines both for Linus.** The 1.04T-parameter Kimi-K2 architecture sits
exactly where the two prior threads converge. It is too large for unified-memory deployment at any precision currently
practical (the FP8 distribution alone is ~1 TB), so the BitNet/Bonsai-style aggressive quantization is necessary. It is
sparse enough (8 active routed experts out of 384, ~3% activation rate per token) that the flash-streaming pattern
applies. It is licensed permissively enough (Modified MIT) that a Linus-flavored derivative is a real option. It is
agentically capable enough at FP8 that the Phase 6/8 prize is worth the engineering. **No single paper in the existing
synthesis would produce this candidate**; the candidate emerges only from the combination.

The two ADR seeds named in this synthesis make the combinable-bets thesis durable.

**DEC-0055 (Phase 6 Qwen3 → Kimi-K2 base swap).** _Seed: DEC-0055._ CLAUDE.md currently names Qwen3 as Linus's default
Worker base "for 32 GB M1 Max hardware." The decision criteria for swapping Qwen3 → Kimi-K2 ought to be: (a) **agentic
benchmark deltas** on Dan's domain corpus after LoRA training (not zero-shot) — concretely SWE-bench Verified, τ²-Bench,
Aider-Polyglot scores; (b) **memory-budget feasibility** under a flash-MoE-style streaming inference path on M1 Max with
the 600 GB external SSD; (c) **license cleanliness** (Modified MIT is more permissive than Llama 3 Community License and
competitive with Apache 2.0 once the trademark/attribution clauses are read end-to-end). Tentative threshold for
discussion: ≥10 percentage points on SWE-bench Verified after equivalent LoRA training, ≥5 percentage points on τ²-
Bench, _and_ per-token latency within 2× of Qwen3-32B-native. If Kimi-K2 hits two of three, mixed verdict; if all three,
commit to swap; if zero, commit to staying on Qwen3. The decision is gated on the Phase 6d streaming-feasibility spike,
which is a measurement task, not an argumentation task.

**DEC-0056 (Phase 8 1-bit / ternary Linus-flavored Kimi-K2 variant).** _Seed: DEC-0056._ The aspirational target. Apply
flash-MoE's expert-streaming methodology to Kimi-K2's released base checkpoint and apply BitNet's / Bonsai's ternary or
1-bit weight quantization at the same time. A 1.58-bit ternary Kimi-K2 carries roughly `1.04T × 1.58 bits ≈ 205 GB`
total; a strict 1-bit variant carries ~130 GB. The active-expert per-token streaming budget at 1-bit drops from ~350 MB
(FP8) to ~44 MB — within an order of magnitude of the M1 Max's sustained external-SSD bandwidth budget for interactive
use. Whether this artifact can be _produced_ is a research question separate from whether it can be _served_: the
established BitNet line trains from scratch (closed to anyone outside frontier labs), Bonsai's PTQ recipe is closed
intellectual property, and BitNet Distillation's three-stage SubLN-insertion + 10B-token continued pretraining + multi-
loss distillation pipeline is the closest published path. Phase 8 should scope a feasibility spike that distills
Kimi-K2-Base into a ternary variant on a small subset of layers, evaluates on SWE-bench-Verified-lite and τ²-Bench-lite,
and decides.

**The strategic gravity of these two seeds is asymmetric**, and the asymmetry is the point. DEC-0055 is a Phase 6
decision that depends primarily on a Phase 6d measurement (does the streaming path produce interactive latency on Dan's
hardware) plus an empirical comparison (does Kimi-K2 LoRA beat Qwen3 LoRA on Dan's domain by enough margin). The
measurement and the comparison are bounded tasks. DEC-0056 is a Phase 8 research direction that could land anywhere
between "produces a frontier-class agentic Linus Worker that runs on a MacBook Pro" and "demonstrates a sharp boundary
on what 1-bit quantization preserves at trillion-parameter scale" — both outcomes are useful, but the upper bound is
materially more transformative than anything else the synthesis points at. The reason the seeds are surfaced together is
that Phase 6d's measurement informs both: the streaming feasibility result is the prerequisite for both the base- swap
decision and the Phase 8 substrate research direction. **Phase 6d's spike is the most important measurement in the
entire low-bit-Apple-Silicon arc**, in a way it was not before Kimi-K2 was added to the corpus.

---

## Cross-cutting threads

**Quantization and streaming as substitute solutions.** The two answers to "limited unified memory" sit on the same
axis. Make the weights smaller, or stream them in. Each axis has structural costs and benefits: quantization sacrifices
some quality and requires the model to be trained or distilled to live in low precision; streaming sacrifices throughput
to flash bandwidth and requires per-architecture predictor training. For the regime where both apply (8B-class capable
models on M1 Max), Bonsai has shifted the balance decisively in favor of quantization. mlx-flash still wins for
fine-tuned dense FP16 models that exceed RAM, and flash-MoE methodology still wins for genuinely huge MoE models. But
the _default_ Phase 2 Worker is now plausibly a low-bit Bonsai variant running entirely in unified memory, with
streaming reserved for the rarer cases where the model genuinely exceeds RAM.

**MLX as the convergence point.** The three sub-threads come together on MLX in a way that was not visible a year ago.
bitnet.cpp is CPU-only on Apple Silicon (NEON SIMD); it does not touch Metal or the ANE. Flash-MoE explicitly _avoided_
MLX because it was too slow for the 397B streaming workload. But Bonsai ships custom MLX kernels in both Python and
Swift, and the underlying MLX framework is becoming the lingua franca for Apple Silicon LLM inference even when the
kernels themselves are bespoke. This convergence has implications for the Linus inference layer: an MLX-based serving
path is now the natural shape, with bespoke kernels (PrismML's, eventually pmetal's, possibly Linus's own ternary
kernel) plugged in where they earn their complexity. The CPU-only bitnet.cpp path remains a valid baseline but is
increasingly the fallback rather than the primary.

**From-scratch pretraining vs PTQ vs distillation.** The corpus now contains three production paths to a low-bit
deployable LLM, with very different cost and quality profiles. From-scratch BitNet pretraining is the cleanest in
principle — weights trained to live in `{−1, 0, +1}` from step zero — but costs trillions of tokens and is closed to
anyone outside frontier labs. BitNet Distillation gives a recipe that any lab with a few thousand GPU-hours can run,
taking any pretrained Qwen3 / Qwen2.5 / Gemma backbone to 1.58-bit at ~0.25% of from-scratch cost. PrismML's Bonsai is
PTQ, taking pretrained Qwen3 to 1-bit or ternary without (publicly disclosed) continued pretraining; the recipe is
closed but the artifacts are downloadable. Linus's Phase 6 fine-tuning plan can mix these: LoRA on FP16 Qwen3-8B for
Dan's biochem/genomics/ Python corpus, then either BitDistill or Bonsai-style ternarization to produce the deployable
Worker. The right path depends on whether PrismML opens the Bonsai recipe and whether BitDistill on a small fine-tuned
Worker turns out tractable on M1 Max — both empirical questions deferrable past Phase 1c.

**Phase 1c spike implications.** The Phase 1c spike was originally scoped around BitNet 2B4T as the one available
native-low-bit checkpoint worth benchmarking on M1 Max. Bonsai's release expands the scope materially. The spike should
now benchmark, with one unified harness following the task-completion-time methodology from
[Speed and LLMs (2502.16721)](../paper-notes/2502.16721v1.md), at minimum: **BitNet b1.58 2B4T** (true native ternary,
smallest, the original Microsoft release), **Bonsai Ternary 8B** (PTQ ternary, largest, MLX- native, Apache-licensed),
**Bonsai 1-bit 8B** (PTQ binary, smallest 8B-class footprint), and **Bonsai Ternary 4B** (the middle-of-fairway
candidate that fits alongside two concurrent Workers in 32 GB). The methodology must report tok/s on tg128 and pp512,
wall-clock task- completion time on `dan_tasks/`, peak RSS, energy per token where measurable, and quality on at least
the six-benchmark Bonsai suite (MMLU-Redux, MuSR, GSM8K, HumanEval+, IFEval, BFCLv3). The spike's result is the basis
for the Phase 2 Worker selection, so the methodology has to be holistic — not tok/s alone, not benchmark score alone,
but the joint Pareto position across cost / quality / latency.

**The MLX kernel gap as a Linus contribution opportunity.** Bonsai Ternary 8B's most consequential operational caveat is
also the most tractable contribution opportunity in the entire corpus for Linus. **MLX has no native ternary kernel.**
Bonsai's deployed throughput reflects the MLX 2-bit kernel path, with the on-disk 1.75 GB inflating to 2.16 GiB
resident. A native MLX ternary kernel would close that gap, and the connection to [`repos/pmetal`](../../repos/pmetal/)
— Epistates' maintained Rust ML platform for Apple Silicon, which already ships fused low-bit kernels in production — is
direct. The contribution is well-scoped (a single kernel, a known weight format, a known consumer in PrismML's MLX
fork), tractable for Linus's skill profile (Rust + Metal + careful numerical work, which Dan is actively learning), and
benefits the entire MLX-on-Apple-Silicon community immediately. It sits naturally as a Phase 1d or Phase 6d work item,
after Phase 1c benchmarking has quantified what the gap costs.

**Flash-MoE's curiosity.** The primary author of the flash-MoE paper is Claude Opus 4.6 itself, working under Daniel
Woods' direction over a 24-hour collaborative session. This is exactly the operating model [CLAUDE.md](../../CLAUDE.md)
describes for Linus — the Maestro/Worker discipline applied to a research-engineering artifact. The paper is worth
studying not just for its technical content but as an existence proof of what disciplined Maestro/Worker collaboration
can produce when the Worker has the right tools and the Maestro has set the spec correctly. For the Phase 8 BitNet ×
Flash-MoE × JPmHC speculative research direction, this is also a sociotechnical existence proof: ambitious cross-paper
synthesis is something a Linus-class assistant plausibly can do.

**The Phase 6d stretch target now met.** The original Phase 6d roadmap language
([`docs/landscapes/total-landscape.md` Crossing 2 resolution](../landscapes/total-landscape.md)) set "ternary 8B
integration if community releases" as an opportunistic stretch target. Bonsai delivers exactly that, ahead of schedule
and with MLX-native deployment kernels included. This calls for an explicit Phase 6d reframe: the formal target remains
"mlx-flash streams any fine-tuned model that exceeds RAM," but the stretch target has shifted from "wait for someone to
release a ternary 8B" to "evaluate Bonsai Ternary 8B as the Phase 2 default Worker, with mlx-flash as the path for
whatever genuinely exceeds RAM (Bonsai Ternary 30B+ if PrismML ever publishes it, or any Linus-fine-tuned model that
grows past ~16 GB resident)."

---

## Implications for Linus

The eleven papers translate into a small set of concrete commitments ranging from Phase 1c (immediate) through Phase 8
(long-horizon research direction).

**Phase 1c — spike scope expansion.** The BitNet spike originally scoped around BitNet 2B4T should expand to a four-way
comparison: BitNet 2B4T (baseline, true native ternary, smallest), Bonsai Ternary 8B (the new flagship, MLX-native),
Bonsai 1-bit 8B (the footprint- critical alternative), and Bonsai Ternary 4B (the middle-ground candidate that fits
alongside two concurrent Workers). Run all four under one unified harness in `benchmarks/dan_tasks/` using the task-
completion-time methodology from [Speed and LLMs](../paper-notes/2502.16721v1.md) and the evaluation discipline from
[Bonsai's Appendix B](../paper-notes/bonsai-1-bit-8b-whitepaper.md) (locked dataset revisions, deterministic attention,
identical generation parameters, no per-model prompt tuning, sandboxed code execution, rule-based scoring with LLM
fallback only on extraction failure). Report joint cost / quality / latency Pareto position; do not pick a winner on a
single metric. The spike's output becomes the Phase 2 Worker-selection basis.

**Phase 1d — first baseline collected 2026-05-16 (PR #33).** The Dan task suite v0 produced its first run against
`qwen2.5-coder:7b` (qwen3:8b not yet pulled locally — the runner correctly failed loud and the baseline was collected
against the best locally-available model). All three tasks completed in 55.75s wall: `paper-summarization` full-credit
(10.5s; three numbered findings on MemGPT, grounded in the paper), `fasta-gc-content` partial (19.2s; stdlib-only script
with divide-by-zero guard, but counts `N` in the denominator where the rubric says exclude — a real rubric-edge
failure), and `title-clustering` partial (26.0s; five named clusters but only 36/50 input titles got assigned, ~28% drop
— a coverage-vs-throughput signal worth carrying forward into the Phase 1c four-way methodology). This is the first
empirical anchor for the Worker-selection arc and will be re-run once `qwen3:8b` is pulled.

**Phase 2 — Worker selection and orchestration fan-out.** Bonsai 8B is a strong candidate for the default Linus Worker.
The crucial architectural consequence is footprint: at 1.15 GB (1-bit) or 1.75 GB (ternary) on disk, with 2.16 GiB
resident in the MLX 2-bit deployment path, **multiple parallel Bonsai Workers fit comfortably in 32 GB unified memory**.
Four concurrent ternary 8B Workers consume ~9 GB of weights, leaving ~23 GB for KV caches, KnowledgeBase / Qdrant
indices, orchestration, and the IDE. This strengthens the orchestration-layer fan-out story enough that **parallel agent
fan-out becomes a Phase 2 concern rather than a Phase 3 one**. The ROADMAP can credibly target "N parallel Workers in
unified memory" in the MVP phase.

**Phase 5 — Interface refinement.** The Bonsai footprint also strengthens the multi-Worker UX story: the orchestration
layer can keep specialized Workers warm (a code Worker via Qwen2.5-Coder-7B, a general Worker via Bonsai Ternary 8B, a
small Worker for fast classification via BitNet 2B4T at 0.4 GB) without the swap-in / swap- out friction that an FP16
Worker selection would impose. Worker specialization becomes operationally cheap.

**Phase 6 — fine-tuning and the open base-model question.** Three production paths to a Linus-branded low-bit Worker now
exist, ranked by tractability and risk: _FP16-LoRA on Dan's domain corpus_, the safe baseline already committed in the
existing planning, leaves a deployable artifact even if the low-bit paths fail. _BitDistill on a small fine-tuned
Worker_, using the three-stage SubLN-insertion-plus-continued-pretraining-plus-distillation pipeline, is the published
recipe for converting any HuggingFace FP16 model to 1.58-bit; cost is dominated by the ~10B-token continued pretraining
step, which on M1 Max needs a benchmark spike to verify is hours/days/weeks. _Bonsai-style PTQ_ on a domain-fine-tuned
Qwen3-8B is appealing because the Bonsai artifacts validate the format, but the recipe is closed; either PrismML opens
it or the community reverse-engineers it. The pragmatic Phase 6 sequence is FP16-LoRA first (unconditional), then
BitDistill on the small fine-tuned Worker as the first low-bit pass (when the spike confirms tractability), then watch
PrismML for either an opened recipe or a Bonsai-LoRA workflow.

The new Phase 6 question Kimi-K2 raises is the **base-model swap (`DEC-NNNN` base-model-swap seed, see Sub-thread D and the combinable-
bets section above)**. CLAUDE.md currently commits to Qwen3 as Linus's default Worker base. Kimi-K2-Instruct is at
minimum a credible alternative on agentic benchmarks (open-source SOTA on every axis the paper measures) and at maximum
an architecturally distinct path that — combined with the 1-bit Linus-flavored variant of DEC-0056 — could replace the
Qwen3-Bonsai-Ternary-8B center of gravity entirely with a Kimi-K2-derived MoE Worker. The decision is gated on the Phase
6d streaming-feasibility spike. MuonClip surfaces independently as a fine-tuning convention candidate worth a small
ablation (LoRA on a 7B–32B Worker with MuonClip vs. Muon vs. AdamW) regardless of base-model choice.

**Phase 6d — streaming as residual, but with a sharply elevated upper target.** Reframe Phase 6d explicitly: mlx-flash
is the path for any _future_ fine-tuned model that genuinely exceeds RAM. Bonsai's existence makes the 8B-class regime
not need streaming at all. The streaming roadmap shifts from "we may need this for any capable Worker" to "we need this
only for the rare large model that genuinely exceeds RAM." But the rare large model now has a name: **Kimi-K2 at int4
(~250 GB total, ~175 MB/token streamed) or at ternary/1-bit (~130–205 GB total, ~44–88 MB/token streamed)**. Phase 6d's
spike, formerly a contingency for fine-tuned-Linus-Worker overrun, is now the gating measurement for both DEC-0055 and
DEC-0056 — the most consequential single measurement in the synthesis's strategic arc. The flash-MoE
methodology-only-reference status persists (no Linus dependency on its bespoke Metal codebase, but the OS-page-cache
lesson and the deferred-CMD3 pipeline pattern inform the Linus inference layer when it eventually has its own kernel
work), with Kimi-K2 as the concrete target the methodology would be applied to.

**Phase 8 — the speculative cross-product, now with a concrete substrate.** The "Bonsai-MoE-streamed-with-Cayley-
stability" research direction has had materially more plausibility than a year ago since Bonsai released; with Kimi-K2
in the corpus, it has a concrete substrate. Eight Ternary Bonsai 8B Workers in parallel consume ~14 GB of weights — a
fan-out that wasn't credible at FP16 even with 4-bit quantization. Combining [JPmHC's](../paper-notes/2602.18308v2.md)
Cayley-stabilized hyper-connections (which replace Sinkhorn-constrained doubly-stochastic matrices with orthogonal
`O(n)` mixers, eliminating spectral stalling in deep stacks) with BitNet ternary weights and Flash-MoE streaming
**applied to Kimi-K2** would push the single-machine inference frontier further than any other combination the corpus
points at. The JPmHC paper note also connects to BitNet 2B4T explicitly: both use SubLN-style normalization inserts as a
training-stability mechanism, though via different mathematical routes — and Kimi-K2 introduces a third stability
mechanism (MuonClip's QK-Clip rescale) operating at the optimizer level rather than the architecture level. The four
mechanisms (BitNet's SubLN, Bonsai's group-128 quantization recipe, JPmHC's Cayley orthogonal mixers, MuonClip's
QK-Clip) are independent stability surfaces that could in principle compose. DEC-0056 (Phase 8 1-bit Linus-flavored
Kimi-K2 variant) is the durable name for this cross-product as a research direction, distinct from the speculative
four-paper synthesis it would draw on.

**MLX ternary kernel as a Linus contribution.** The most tractable, well-scoped, immediately community-beneficial
contribution opportunity in the entire Linus corpus is a native MLX ternary kernel that exploits the actual zeros in the
Bonsai Ternary weight format rather than encoding them as 2-bit values. The contribution is bounded (one kernel, known
format, known consumer in PrismML's MLX fork), aligned with the [`repos/pmetal`](../../repos/pmetal/) Rust+Metal kernel
work that Linus already tracks, and benefits every Apple Silicon BitNet user on day one. Worth scoping as a Phase 1d
(immediately after the Phase 1c spike quantifies the deployment-path tax) or Phase 6d (alongside the streaming-or-not
scoping decision) work item.

---

## Tensions and open questions

The Phase 1c spike, the Phase 2 Worker selection, and the Phase 6 fine-tuning roadmap all need decisions that this
synthesis can sharpen but not finally resolve. The corpus surfaces seven sharp questions:

**1. Should Phase 1c benchmark Bonsai 8B and BitNet 2B4T together under a unified Worker-selection methodology?** The
synthesis says yes — the natural shape is a four-way comparison with one unified harness, scoring on the joint cost /
quality / latency Pareto position rather than any single metric. The open question is methodology authority: should the
methodology spec live exclusively in [`docs/specs/phase1c-spike.md`](../specs/phase1c-spike.md) (the per-phase spec
already committed) or in a separate `docs/specs/experimental-protocol.md` that generalizes across phases? The per-phase
spec is the more immediate deliverable; the generalized protocol can be extracted later if the pattern recurs.

**2. Should the MLX ternary kernel gap be a Linus contribution?** This is the single best-scoped contribution
opportunity in the corpus. The question is whether to scope it as Phase 1d (immediately, while the spike's measurement
of the deployment-path tax is fresh) or Phase 6d (deferred until streaming-or-not scoping, when the broader low-bit
inference story has more empirical grounding). The Phase 1d framing is more aggressive but produces a Linus contribution
earlier; the Phase 6d framing is safer but risks the gap being closed by someone else first.

**3. Bonsai 1-bit vs ternary: what is the right Worker default?** At 8B, ternary's 95% quality recovery vs binary's 89%
is a substantial gap, and the 0.6 GB extra footprint (1.75 GB vs 1.15 GB) is small relative to 32 GB. The synthesis
predicts ternary as the right default for general-purpose Worker tasks, with binary as opt-in for footprint- critical
paths (phone, KV-cache-heavy long contexts, many concurrent Workers). Phase 1c benchmark data will resolve this
empirically; the question is what quality margin or task-specific weakness in 1-bit would trigger the switch.

**4. Should pmetal's low-bit Rust kernels be evaluated as an alternative to MLX-native Bonsai serving?** pmetal already
ships fused low-bit kernels in production. The Bonsai release vendors a PrismML fork of MLX with its own custom kernels.
Long-term the question is whether Linus pins to the PrismML fork (a real maintenance liability), contributes upstream
MLX support for scale-only quant formats (which would let MLX match GGUF's 1.125 bits/weight), or waits for pmetal to
subsume both. This deserves its own ADR before the inference layer hardens.

**5. For Phase 6, is BitDistill on a small fine-tuned Worker more tractable than waiting for or reverse-engineering
Bonsai PTQ?** The BitDistill recipe is published and the cost dominated by ~10B tokens of continued pretraining; on M1
Max this could be hours, days, or weeks depending on how functional MLX's BitNet training path is. The Bonsai recipe is
closed but the artifacts are downloadable. A small benchmark spike to measure the BitDistill continued-pretraining cost
on M1 Max would scope this; the question is when to run it (Phase 6a vs Phase 6b vs deferred until PrismML's posture
clarifies).

**6. Is "Native Low-Bit Apple Silicon" worth its own dedicated benchmark suite distinct from `benchmarks/dan_tasks/`?**
The Bonsai papers use a six-benchmark suite (MMLU-Redux, MuSR, GSM8K, HumanEval+, IFEval, BFCLv3) as the standard
low-bit-LLM comparison set. Mirroring that suite in a `benchmarks/low_bit/` subdirectory would let Linus reproduce
published numbers and track the low-bit landscape over time as new releases land. The alternative is folding the same
benchmarks into `benchmarks/dan_tasks/` as one of several scoring axes. The synthesis weakly prefers the dedicated
suite, on the grounds that low- bit is a sufficiently distinct frontier to warrant its own observability surface, but
reasonable people can disagree.

**7. Is mlx-flash deprecated for Phase 6d's _original_ purpose?** The original Phase 6d framing scoped streaming as the
path for any fine- tuned Worker that exceeded RAM. Bonsai's compactness makes the 8B class fit trivially. The honest
answer is that mlx-flash is not deprecated — it is _narrowed in scope_ — and the Phase 6d formal target should be
rewritten to reflect that. Fine-tuned models that genuinely exceed RAM (Linus-branded 30B+ or any opportunistic ternary
30B+ from PrismML) remain the proper streaming targets. The Bonsai existence proof has shifted Phase 6d's center of
gravity, not removed its motivation. Kimi-K2 (questions 8–12 below) is the most consequential addition to the streaming
target list.

**8. Is weight-streaming Kimi-K2 on M1 Max + 600 GB external SSD actually feasible at interactive latency?** The
synthesis-level argument requires that the per-token streaming budget (~350 MB/token at FP8, ~175 MB at int4, ~44–88 MB
at 1-bit/ternary) lands inside the M1 Max external-SSD sustained read budget under the flash-MoE-style `pread()` access
pattern. The full Kimi-K2 FP8 distribution (~1 TB) does not fit on the 600 GB external SSD as-distributed and would
require staging; the int4 form (~250 GB) fits with headroom. The first-byte and steady-state per-token latencies are
empirical, not analytical — Phase 6d needs to measure, not estimate.

**9. What is the per-token latency floor for Kimi-K2 streaming vs. Qwen3-32B native?** If the streaming gap is ≥5×, the
streamed-Kimi-K2 Worker is not interactive even if it fits; if it's ≤2×, it's a viable Worker. The threshold matters
because hosted Claude is the comparison point — interactive should mean responses begin within 1–2 seconds and stream at
≥5 tok/s. This question gates DEC-0055.

**10. Does FP8 → int4 → ternary preservation of agentic benchmarks hold for Kimi-K2?** The published Kimi-K2 numbers are
at FP8. Whether the block-fp8 distribution requantizes cleanly to int4 with <2% benchmark degradation on SWE-bench
Verified and τ²-Bench, and whether the BitNet-Distillation-style path preserves those numbers at ternary, are empirical
questions that need a quantization spike smaller in scope than the full Phase 8 rebuild. A negative result (>5%
degradation at int4) would close DEC-0056 cleanly; a positive result keeps both seeds open.

**11. Is MuonClip reproducible on Apple Silicon, and does it generalize beyond MLA-MoE?** The MuonClip optimizer is
reproducible in MLX in principle (Muon already exists; QK-Clip is a 10-line addition), but the per-head `Smax_h`
tracking interacts with MLX's eager-by-default execution. Whether it generalizes to dense models (Kimi-K2 only validates
on MLA-MoE) and to smaller scales (the only published trace is the 1T run) is the second-order question. A Phase 6 spike
LoRA-fine-tuning a 7B–32B model with MuonClip vs. Muon vs. AdamW would settle the matter cheaply, and the result informs
Phase 6 fine-tuning conventions independent of any Kimi-K2 base-swap decision.

**12. What is the evidence threshold for the Phase 6 Qwen3 → Kimi-K2 base swap?** Tentative threshold for discussion:
≥10 percentage points on SWE-bench Verified after equivalent LoRA training on Dan's domain corpus, ≥5 percentage points
on τ²-Bench, _and_ per-token latency within 2× of Qwen3-32B-native. If Kimi-K2 hits two of three, mixed verdict; if all
three, commit to the swap; if zero, commit to staying on Qwen3. The threshold itself is an open commitment — Dan's call,
to be sharpened during the Phase 6d planning session.

---

## Where this synthesis fits

This synthesis is the third in the Linus corpus to cross multiple sub-threads and explicit landscape Crossings. The
[memory synthesis](memory-synthesis.md) argued that memory is the load-bearing architectural pillar that all other
pillars rest on; the [security synthesis](security-synthesis.md) and [LLM Wiki synthesis](llm-wiki-synthesis.md)
similarly span multiple papers and Crossings. This one argues that **native low-bit inference on Apple Silicon is the
load-bearing operational pillar** — the substrate that makes every other Linus capability tractable on Dan's hardware
rather than aspirational.

The connections to the rest of the corpus are direct. The memory pillar treats 1-bit / ternary substrate as one axis of
the "structure compounds" thesis ([memory synthesis Layer A](memory-synthesis.md)) — a Linus Worker substrate hosted on
a recurrent / minGRU / SSM architecture with BitLinear gates is the most extreme hardware-friendly substrate the
combined corpus points at, and the Phase 8 speculative direction in the memory synthesis points at the same
cross-product as the BitNet × Flash-MoE × JPmHC speculation here. The [JPmHC paper note](../paper-notes/2602.18308v2.md)
is now in the corpus and connects both to Flash-MoE (JPmHC's ordinary HC is used there; the paper explicitly names
combining JPmHC stability with Flash-MoE streaming as a natural research direction) and to BitNet 2B4T (both use
SubLN-style inserted norms as variance-preservation mechanisms). The agentic systems thread benefits directly: cheaper
Workers enable more parallel agentic fan-out, and the Bonsai footprint puts that fan-out in Phase 2 rather than Phase 3.
The biological foundation models thread (Group A) interacts in a more speculative way: foundation models could plausibly
be ternary-distilled via BitDistill, though no domain-specific BitDistill recipe has been published and the
foundation-model context lengths typical of biology work may be where 4-bit KV cache from BitNet v2 matters most.

The local repository anchors are concrete. [`repos/Bonsai-demo`](../../repos/Bonsai-demo/) is the local clone of
PrismML's release with both 1-bit and ternary checkpoints; it is the deployment surface for the Phase 1c spike.
[`repos/BitNet`](../../repos/BitNet/) is Microsoft's reference implementation, including bitnet.cpp and (per the
BitDistill paper's claims) the BitDistill training code; it is the comparison baseline and the BitDistill source.
[`repos/mlx-flash`](../../repos/mlx-flash/) is the streaming reference Linus would integrate against if a fine-tuned
Worker exceeds RAM. [`repos/pmetal`](../../repos/pmetal/) is the long-term native runtime where a Linus-contributed MLX
ternary kernel would land. [`repos/ANE`](../../repos/ANE/) is the methodology reference for any future ANE-side work;
per the Crossing 1 resolution, Linus's own code stays on public APIs, with pmetal as the supported ANE path.
[`repos/Kimi-K2`](../../repos/Kimi-K2/) is the Moonshot release artifact (block-fp8 weights, deployment scripts, and the
load-bearing `tech_report.pdf` that backs the [Kimi-K2 paper-note](../paper-notes/Kimi-K2-2507.20534.md)) — the
substrate for both DEC-0055 and DEC-0056.

The cross-synthesis links matter for Kimi-K2 specifically. The architectural and training-claim fold-in lives in
[`infra-foundations-synthesis.md`](infra-foundations-synthesis.md) (MuonClip as optimizer-stability finding; MLA-at-64-
heads scaling-law sweep; sparsity-48 result). The agentic-benchmark fold-in lives in
[`agentic-systems-synthesis.md`](agentic-systems-synthesis.md) (SOTA τ²-Bench / ACEBench scores; the 3,000-MCP-tool
synthetic-data pipeline as Phase 7 methodology import). The Anthropic-compatible-API fold-in lives in
[`skills-and-practices-synthesis.md`](skills-and-practices-synthesis.md). This synthesis's primary fold focuses
exclusively on the operational thread — quantization, streaming, and Apple-Silicon feasibility — and explicitly defers
the architectural commentary, agentic-benchmark detail, and API-pattern commentary to those sibling syntheses.

The landscape doc connections close the loop. This synthesis formalizes the union of
[Crossing 1 (BitNet → Apple Silicon → ANE)](../landscapes/total-landscape.md#crossing-1-the-bitnet--apple-silicon--ane-bridge)
and
[Crossing 2 (the streaming axis)](../landscapes/total-landscape.md#crossing-2-the-streaming-axis-dense-mlx-flash-vs-sparse-flash-moe-vs-composite-1-bit-streamed),
and adds the Bonsai productized line as a third axis that bridges them. The next round of edits to
[`docs/landscapes/paper-landscape.md`](../landscapes/paper-landscape.md) should promote the existing "BitNet" and
"Larger-than-RAM inference" sections into a unified "Native Low-Bit Apple Silicon Inference" group pointing at this
synthesis. The [`docs/landscapes/synthesis-landscape.md`](../landscapes/synthesis-landscape.md) and
[`docs/questions/open-questions.md`](../questions/open-questions.md) should pick up the seven open questions above.

## References

### Repo-notes

- [`ANE`](../repo-notes/ANE.md) — Maderix/ANE-training; reverse-engineered methodology reference for Apple Neural Engine
  training, public-API line per DEC-0027.
- [`BitNet`](../repo-notes/BitNet.md) — Microsoft's reference implementation including bitnet.cpp CPU runtime and the
  BitDistill training pipeline.
- [`Bonsai-demo`](../repo-notes/Bonsai-demo.md) — PrismML's released 1-bit and ternary 8B checkpoints with
  MLX/Metal/CUDA kernels and llama-server endpoint.
- [`Kimi-K2`](../repo-notes/Kimi-K2.md) — Moonshot AI release artifact (block-fp8 weights, deployment scripts, tech
  report); substrate for DEC-0055 and DEC-0056.
- [`mlx-flash`](../repo-notes/mlx-flash.md) — The dense >RAM streaming reference Linus would integrate against for any
  fine-tuned Worker that exceeds RAM.
- [`pmetal`](../repo-notes/pmetal.md) — Epistates' maintained Rust ML platform for Apple Silicon; long-term native
  runtime where a Linus-contributed MLX ternary kernel would land.

### Paper-notes

- [`2310.11453v1`](../paper-notes/2310.11453v1.md) — BitNet, the founding 1-bit Transformer paper introducing BitLinear
  and SubLN.
- [`2312.11514v3`](../paper-notes/2312.11514v3.md) — LLM in a Flash; Apple's foundation paper for activation-sparsity
  weight streaming, M1 Max tested.
- [`2402.17764v1`](../paper-notes/2402.17764v1.md) — BitNet b1.58; the ternary {−1,0,+1} variant achieving FP16 LLaMA
  parity at 3B and above.
- [`2411.04965v1`](../paper-notes/2411.04965v1.md) — BitNet a4.8; first push to 4-bit activations via hybrid
  quantization + sparsification.
- [`2502.11880v1`](../paper-notes/2502.11880v1.md) — bitnet.cpp; CPU inference runtime delivering 2.15–4.91× over FP16
  on Apple M2 Ultra via NEON SIMD.
- [`2502.16721v1`](../paper-notes/2502.16721v1.md) — Speed and LLMs; task-completion-time methodology for the Phase 1c
  unified benchmark harness.
- [`2504.12285v2`](../paper-notes/2504.12285v2.md) — BitNet b1.58 2B4T; the released open-weights ternary checkpoint,
  0.4 GB and 29 ms TPOT on CPU.
- [`2504.18415v2`](../paper-notes/2504.18415v2.md) — BitNet v2; W1.58A4 via online Hadamard transformation enabling
  4-bit KV cache.
- [`2510.13998v1`](../paper-notes/2510.13998v1.md) — BitNet Distillation; three-stage pipeline converting any FP16 model
  into 1.58-bit at ~0.25% of from-scratch cost.
- [`2602.18308v2`](../paper-notes/2602.18308v2.md) — JPmHC; Cayley-stabilized orthogonal Hyper-Connections, sibling
  Phase 8 cross-product substrate.
- [`bonsai-1-bit-8b-whitepaper`](../paper-notes/bonsai-1-bit-8b-whitepaper.md) — PrismML's 1-bit Bonsai 8B; Qwen3 PTQ to
  1.15 GB at 70.5 benchmark average, 131 tok/s on M4 Pro.
- [`bonsai-ternary-8b-whitepaper`](../paper-notes/bonsai-ternary-8b-whitepaper.md) — PrismML's Ternary Bonsai 8B; 1.75
  GB at 75.5 average (95% of FP16 Qwen3-8B), first openly released native-ternary 8B.
- [`flash_moe`](../paper-notes/flash_moe.md) — Anthropic + Daniel Woods 397B-MoE streaming on M3 Max via bespoke
  Metal/Objective-C; OS-page-cache lesson.
- [`Kimi-K2-2507.20534`](../paper-notes/Kimi-K2-2507.20534.md) — Moonshot AI Kimi K2 tech report; MLA+MoE topology,
  MuonClip optimizer, zero loss spikes across 15.5T tokens.

---

_This synthesis should be revisited when the Phase 1c spike results land (it will turn the four-way comparison into
concrete Worker-selection data), when PrismML opens or refuses to open the Bonsai compression recipe (the Phase 6
fine-tuning path depends on this), when an MLX native ternary kernel lands either from PrismML or from a Linus
contribution (it removes the deployment-path tax that limits the Bonsai numbers reported here), whenever a new ternary
or 1-bit checkpoint at 8B+ scale lands in the open ecosystem, when the Phase 6d streaming-feasibility spike returns a
verdict on Kimi-K2 at int4 or 1-bit (this gates DEC-0055 and DEC-0056), when Moonshot AI or any community effort
publishes a low-bit Kimi-K2 derivative, and when MuonClip's generalization to dense models or smaller scales is
empirically tested._
