# mlx-flash (`matt-k-wong/mlx-flash`)

## 1. Purpose and scope

mlx-flash is the MLX-ecosystem answer to Apple Research's "LLM in a Flash" paper (`2312.11514`): a Python package that
streams model weights from SSD so MLX can run models larger than the machine's RAM, while preserving the model's native
precision — no additional quantization, no requantization tricks. The canonical example on the tin is a 30B Nemotron
(17.8 GB on disk) running on a 16 GB MacBook Air with bit-perfect parity and a faster load than the same model running
normally on adequate hardware. Claimed support scales to 70B on 32 GB and 400B+ with enough disk. For Linus this is the
MLX-native counterpart to flash-moe: same problem (bigger-than-RAM inference on Apple Silicon), different philosophy
(framework integration + zero quality loss vs. hand-built engine + ruthless optimization).

## 2. Architecture summary

mlx-flash wraps existing MLX model layers in a `StreamingProxy` rather than reimplementing the transformer loop — so
RoPE scaling, residual streams, causal masks, and any other architectural nuance come from the original model code
unchanged. The proxies intercept each layer's execution to force synchronous `mx.eval()` and fire a **Predictive I/O
Scheduler**: an MPC-Lite control loop that establishes a clean compute baseline on the first ("Cold Start") token, then
predicts the bandwidth demand of layer N+1 while the GPU works on layer N. A token-bucket actuator paces SSD reads via
micro-sleeps to keep GPU degradation under 5%. Weights are mmap'd lazily from safetensors (`mmap(lazy=True)`) and pulled
by `os.pread` under predictive control. A `TiledLinear` op uses FP32 accumulation to match standard MLX Metal behavior
exactly (loss delta claimed at `0.0000000000`). The KV cache is hybrid: the most recent 128 tokens stay in FP16 in
memory; older context is offloaded to properly-scaled 8-bit quantized disk storage, with a passkey-retrieval test
showing 100% accuracy on context hidden 1,000+ tokens deep. The roadmap (still unfinished) targets an async DAG
scheduler (v0.4.0) and MoE lookahead routing for Mixtral/DeepSeek (v0.5.0).

## 3. What's reusable in Linus

This is the most directly-integrable "big model" pathway in the repo collection. mlx-flash is a `pip install` away,
wraps any MLX model, and doesn't require any custom kernel work. Linus Phase 5+ calls this out explicitly as the
flash-streaming inference backend; getting a smoke-test working end-to-end is likely a one-hour exercise. The
bit-perfect-parity story matters for Dan's work specifically: any genomics-or-chemistry Q&A benchmark comparing
Linus-with-streaming to Linus-native-precision shouldn't have confounds from quantization artifacts. The hybrid KV cache
(FP16-recent + 8-bit-older) is a reusable design pattern for any long-context feature Linus eventually wants,
independent of whether the weights themselves are streamed.

## 4. What's inspiration only

The MPC-Lite bandwidth controller is the cleanest productized version of the flash-moe-style SSD pacing. Its existence,
and that it achieves <5% GPU degradation, reframes "streaming hurts inference speed" — true naively, not true if the
scheduler is good. Useful mental model for any Linus engineering decision involving SSD/GPU contention.

## 5. What's incompatible or out of scope

mlx-flash is inference-only; no training path, no fine-tuning path. For Phase 6, Linus has to look elsewhere (pmetal,
mlx-lm-ft). The "bigger than RAM" claim is real but comes with tradeoffs the README glosses: on Dan's slower SSD (M1 Max
vs. flash-moe's M3 Max Apple Fabric), the MPC-Lite scheduler will have less bandwidth to work with, so the acceptable
weight-residence budget may be larger in practice than the 16 GB Air demo suggests. This is a measure-it-yourself case.

## 6. Recommendation: **Integrate (in Phase 5+)**

A clear fit for Phase 5+'s "inference engine for larger fine-tuned models" slot. Concrete experiment: once Phase 6
produces a LoRA'd Qwen2.5-7B (or larger), run it via mlx-flash with a 4 GB weight budget on the 32 GB M1 Max and measure
tok/s, parity vs. native, and Dan-task- suite accuracy. If it holds up, mlx-flash becomes the way Linus runs anything
that doesn't fit in RAM at native precision. Pairs naturally with Bonsai-demo: one path is "big model, native precision,
streamed" (mlx-flash); the other is "small model, 1-bit, in-RAM" (Bonsai). Dan task suite can decide which wins for
which task class.

## 7. Questions for Dan

- **mlx-flash vs. flash-moe philosophically.** Same problem, different tradeoff: mlx-flash is framework-integrated +
  zero quality loss + predictive scheduling; flash-moe is bespoke + aggressively quantized
  - manual pipeline. Which style should Linus prefer when forced to choose?
- **The native-precision claim on M1 Max.** Nemotron-30B on a 16 GB Air at bit-perfect parity is the README headline;
  the unstated question is _tok/s_. Worth a small benchmark to see what native- precision streaming costs on your
  hardware before committing to it as a serving path.
- **Streaming + 1-bit as a composite path.** Running a 1.58-bit 30B (hypothetical Ternary-Bonsai-30B) with mlx-flash
  streaming is combinatorially more memory-efficient than either alone. Is this a Phase 6d experiment target, or does it
  wait until PrismML trains a large ternary Bonsai? _Partially resolved (S20, see [answered-questions.md](../questions/answered-questions.md)): Phase 6d framing positions mlx-flash for ≥32 GB models; Bonsai 8B at 1.75 GB does not need streaming; ternary-30B combination deferred until PrismML produces a large ternary model._
- **Hybrid KV cache as a Linus feature.** The 128-token FP16 + older- 8-bit disk-offloaded KV cache pattern is useful
  even without weight streaming. Should it be part of Phase 2a's minimum feature set, or deferred until a concrete
  long-context use case surfaces?
