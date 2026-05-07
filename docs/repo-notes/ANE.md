# ANE (`Maderix/ANE-training`)

## 1. Purpose and scope

A weekend research hack (the author's word) that proves something Apple does not want proven: backpropagation — full
transformer training, forward and backward passes — can run directly on the Apple Neural Engine using reverse-engineered
private APIs (`_ANEClient`, `_ANECompiler`, `_ANEInMemoryModelDescriptor`), with no CoreML, no Metal, no GPU. The repo
trains a 109M-parameter Stories110M model at 91 ms/step and a Qwen3-0.6B (596M) at 412 ms/step on an M4, entirely on the
ANE's ~15.8 TFLOPS FP16 compute plus some CPU-side gradient accumulation via Accelerate. INT8 W8A8 shows 1.88×
throughput over FP16 at 35.1 peak TOPS.

## 2. Architecture summary

MIL (Model Intermediate Language) programs are constructed at runtime as text, handed to the private in-memory compiler,
and executed on the ANE via IOSurface shared-memory tensors. The dynamic pipeline packs both activations and weights
into a single spatial input dimension, sliced inside the MIL kernel, so weights can change without recompilation (the
ANE compiler leaks resources and has a hard ~119 compile limit, worked around via `exec()` restart). Forward and
backward dx passes run on the ANE; dW gradients are computed CPU-side with `cblas_sgemm` and overlapped via a GCD
dispatch queue. Six kernels per layer for plain MHA models, ten for GQA. Key tricks: forward taps expose Q/K/V/attention
scores as extra outputs so the backward pass doesn't recompute them; SDPA causal masking is decomposed into ANE Q@K^T →
CPU mask+softmax → ANE scores@V because ANE hardware ignores `attn_mask`; global loss scaling of `256 × NLAYERS`
prevents FP16 gradient underflow; a GPU→ANE zero-copy IOSurface pipeline is demonstrated (GPU prefill, ANE decode).

## 3. What's reusable in Linus

Not the code — this is Objective-C plus private APIs, and the author is explicit that it's not a maintained library. But
three contributions are gold. First, the _existence proof_: ANE training is possible, and the blocker has always been
software. Any Linus decision about "defer ANE-anything to Phase 8" should now default the other way. Second, the
_benchmark numbers_: 91 ms/step for 109M parameters, 412 ms/step for 596M, 1.88× for INT8 over FP16 — these are real
data points on an M4 that Linus's Phase 1b pmetal evaluation should try to match or contextualize on M1 Max. Third, the
_engineering pattern catalog_: forward-tap reuse for backward, IOSurface zero-copy layouts, `exec()` restart for the
compile-leak workaround, CPU-side dW overlap. These patterns show up in pmetal's ANE crate too, and the ANE repo is the
clearer small-scale reference.

## 4. What's inspiration only

The three Maderix substack articles cited in the README ("Reverse Engineering," "Benchmarks," "Training") are the
substantive write-up. They should be in Dan's read queue — they're the best narrative explanation of what the ANE
actually is and why CoreML's inference-only posture is a software choice, not a hardware constraint.

## 5. What's incompatible or out of scope

Everything about the maintenance story. The author does not intend to grow this into a framework: PRs are slow, features
are forks-welcome, the APIs are Apple-private and can break on any macOS update. Running anything from this repo in
Linus production would be a recipe for future breakage. macOS 15+ and tested only on M4 — the M1 Max may behave
differently, though the ANE generations are close enough that most kernels should port.

## 6. Recommendation: **Study (seriously, at paragraph depth)**

Read the code once; read the substack articles carefully; then look at pmetal's `pmetal-metal` and `pmetal-ane` crates
with the ANE-repo patterns in mind. Do not depend on this repo. But treat the existence proof as load-bearing for
Linus's roadmap: ANE-aware training and inference are real on consumer Apple Silicon today, and the question is which
_production-quality_ backend to adopt for Linus (pmetal is the obvious candidate) rather than whether the capability
exists.

## 7. Questions for Dan

- _Resolved (see [answered-questions.md](../questions/answered-questions.md)): ANE deferred to Phase 2 as conditional follow-up benchmark, gated on favorable pmetal Phase 1b verdict; T2.9._

- **Read-or-defer on the Maderix substack series.** The three articles are arguably the best documentation of the ANE
  that exists. Worth reading now, or defer to whenever an ANE decision is actually forced?

- _Resolved (DEC-0027, see [answered-questions.md](../questions/answered-questions.md)): Linus stays on public APIs (CoreML, MLX, Metal); pmetal carries any private-API risk; ANE reverse-engineering repo is reference only._

- _Resolved (DEC-0027, see [answered-questions.md](../questions/answered-questions.md)): Linus strictly on public Apple APIs; private-API usage stays in pmetal, not vendored into Linus._
