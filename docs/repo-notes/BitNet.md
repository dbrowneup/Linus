# BitNet (`microsoft/BitNet`, a.k.a. `bitnet.cpp`)

## 1. Purpose and scope

`bitnet.cpp` is Microsoft's official inference framework for 1.58-bit ternary LLMs — models whose weights take only the
values `{-1, 0, +1}`. Forked from `llama.cpp`, it provides optimized CPU kernels (ARM and x86), a W2A8 CUDA kernel for
GPU inference, and declares NPU support as coming. The claim that matters most for Linus isn't edge inference on phones;
it's that `bitnet.cpp` already runs a 100B ternary LLM on an Apple M2 Ultra at ~7 tok/s (`2502.11880`, Fig. 1). That is
the puck. A 32 GB M1 Max should, in principle, hold a 1.58-bit model several times the parameter count of what FP16
permits, and the BitNet scaling-law work (`2310.11453`, Fig. 1) argues the loss gap to FP16 narrows as size grows. 1-bit
on Apple Silicon is a plausible route to substantially larger and smarter local models, not just a phone trick.

## 2. Architecture summary

The repo layers on top of `llama.cpp`, adding two things. The CPU kernels (`src/ggml-bitnet-lut.cpp`,
`src/ggml-bitnet-mad.cpp`) implement ternary GEMM via a Lookup Table method inherited from Microsoft's T-MAC project:
instead of multiplying, precompute all possible dot products of a fixed activation tile against the three ternary values
and read results out of a table. Three variants — `I2_S`, `TL1`, `TL2` — are selected at model-prep time by
`setup_env.py` for the target CPU/model combination. The `gpu/` directory contains a CUDA W2A8 kernel (2-bit weights ×
8-bit activations) with a weight permutation packing sixteen ternary values into a 32-bit int, using NVIDIA's `dp4a`
instruction for the inner dot product. Supported official models include BitNet-b1.58-2B-4T, a 3B variant, a
Llama3-8B-1.58 retrain, and the Falcon3 and Falcon-E families. The accompanying BitNet v2 (`2504.18415`) and BitNet
Distillation (`2510.13998`) papers — not yet in this repo's inference path — add a Hadamard-transform trick for
activation outliers and a practical pipeline for converting off-the-shelf full-precision LLMs into 1.58-bit.

## 3. What's reusable in Linus

Three things. First, the GGUFs themselves: BitNet b1.58 2B4T is already a one-line `ollama pull` test for the 1-bit
output-quality question on Dan's machine. Second, the LUT / weight-permutation kernel patterns are a template for the
Metal and ANE kernels Linus eventually wants — anything packing low-bit weights into a wider word will look structurally
similar. Third, the BitDistill pipeline (SubLN module + multi-head attention distillation + continual-pretraining
warmup) gives a concrete recipe for taking, say, a Qwen2.5-7B and producing a 1.58-bit task-specialized Linus variant at
claimed 10× memory savings and 2.65× CPU speed, which if it reproduces makes a fine-tuned 1-bit Linus adapter a
near-term proposition rather than a Phase 8 bet.

## 4. What's inspiration only

The repo's benchmark methodology — matched model/quantization configurations reporting tok/s, RSS, and energy — is worth
mirroring in Phase 1c. The larger thesis that 1-bit models "call for new hardware" aligns with pmetal's fused-kernel
ambitions and with Apple's ANE, both of which already prefer low-bit integer arithmetic; Linus is positioned to benefit
from that alignment without building it.

## 5. What's incompatible or out of scope

The `gpu/` CUDA build is dead on M-series hardware — no Metal port exists here, and `dp4a` has no drop-in Apple
equivalent. The CPU path compiles for ARM and would run on the M1 Max's CPU cores, but a CPU-only build wastes the GPU
and ANE that Linus's architecture is designed around, and Ollama's Metal-hybrid path is already faster for most models.
Adopting `bitnet.cpp` as Linus's runtime would be a step sideways at best; the serious Apple Silicon 1-bit work belongs
in MLX (Bonsai-demo) or in a custom Metal kernel (pmetal territory).

## 6. Recommendation: **Study, plus a cheap experiment**

Keep `repos/BitNet/` as reference. Do _not_ build `bitnet.cpp` into Linus. Do two things instead. (a) Pull BitNet b1.58
2B4T and Llama3-8B-1.58 via Ollama, add them to the Phase 1c benchmark sweep alongside `qwen2.5-coder:7b` and
`mistral:7b-instruct`; the question "how much quality does 1.58-bit actually cost on Dan task suite?" is answerable in a
day and informs every downstream decision. (b) Bookmark the BitNet Distillation paper as the Phase 6 dark-horse
candidate — if `pmetal`'s LoRA pipeline turns out viable, BitDistill becomes a serious alternative or complement to LoRA
for producing a Linus-branded model.

## 7. Questions for Dan

- **How aggressively do we want to chase 1.58-bit on Apple Silicon as a first-class path?** Bitnet.cpp's ~7 tok/s at
  100B on M2 Ultra implies a ~40–50B ternary model could be feasible on the M1 Max. Is that compelling enough to put an
  "MLX/Metal ternary runtime" experiment earlier in the roadmap (Phase 2–3 experimental branch) rather than waiting for
  Phase 6+?
- **BitNet Distillation as a fine-tuning path.** Would you accept a 1.58-bit distilled Qwen2.5 variant as the Phase 6
  deliverable if it beats a FP16-LoRA'd counterpart on Dan task suite, given it sacrifices some smoothness in exchange
  for much larger effective capacity?
- **Ternary base models vs. converted models.** Native ternary training (BitNet b1.58 2B4T) vs. post-hoc distillation
  (BitDistill) vs. post-hoc quantization (run FP16 Qwen at 2-bit via bitnet.cpp-style kernels) — three different
  philosophies. Any strong prior?
- **Hardware bet.** The BitNet papers repeatedly call for "new hardware designed for 1-bit LLMs." The ANE is closer to
  that than Metal is. Is investing in ANE kernel development (via pmetal or directly) worth Linus dev time in Phase 2–3,
  or does it stay a Phase 7+ project?
