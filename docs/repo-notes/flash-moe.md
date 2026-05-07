# flash-moe (`Daniel Woods + Claude Opus 4.6`)

## 1. Purpose and scope

flash-moe runs **Qwen3.5-397B-A17B** — a 397 _billion_ parameter Mixture-of-Experts model — on a 48 GB MacBook Pro M3
Max at ~4.4 tok/s with production-quality output, including working tool calling. The full 209 GB model (4-bit experts)
lives on NVMe SSD, and only the K=4 experts activated per token (~6.75 MB each) are read into memory per layer. The
entire thing is 7k lines of C/Objective-C plus 1.2k lines of hand-tuned Metal shaders — no Python, no PyTorch, no MLX,
no framework. It was built in 24 hours across 90+ experiments, 42% of which were discarded. For Linus this is the single
clearest demonstration of what's possible on current Apple Silicon when you throw framework overhead out.

## 2. Architecture summary

Per-layer pipeline (4.28 ms average): attention projections + delta-net on GPU (1.22 ms), o_proj + norm + routing on GPU
(0.55 ms), top-K routing on CPU (0.003 ms), parallel `pread()` of K=4 expert weights from SSD (2.41 ms — the
bottleneck), then a deferred GPU command that runs expert forward + combine + norm while the next layer's attention
projections are already being encoded. The counterintuitive result is that _no custom expert cache_ beats the OS page
cache: every attempt (Metal LRU, malloc cache, LZ4 compressed cache) lost to the kernel's built-in page-cache LRU, which
achieves ~71% hit rate naturally with zero code. The Metal kernels are hand-tuned: an FMA-optimized 4-bit dequant that
pre-computes `scale*x` and `bias*x` so dequant+multiply becomes one fused multiply-add (+12%), a fused SwiGLU, batched
attention with in-kernel RoPE, a fused combine+residual+sigmoid-gate. Accelerate BLAS (`cblas_sgemv`, `cblas_sger`)
handles the GatedDeltaNet recurrence on CPU at 64% faster than scalar code. Unified memory forces a _serial_ GPU→SSD→GPU
pipeline because any concurrent SSD DMA causes disproportionate GPU latency spikes through the shared memory controller.

## 3. What's reusable in Linus

Almost none of the code, by design — Woods ships a single-purpose engine, not a library. What Linus reuses is the
_methodology_, and the paper documenting it (already in `context/papers/flash_moe.pdf`) is the canonical reference.
Concretely: (a) the 90-experiment keep-or-revert log is the gold standard for the Phase 6d "flash-streaming evaluation"
and for Phase 7c's autoresearch-style overnight-iteration loop; (b) the "trust the OS page cache" principle generalizes
directly to any SSD-streaming path Linus might pursue; (c) the FMA dequant pattern is applicable to any low-bit GPU
kernel Linus or pmetal writes; (d) the bandwidth-measurement discipline (418 GiB/s GPU dequant saturation; 17.5 GB/s
sustained NVMe) is the template for Phase 1b's pmetal comparison and for any mlx-flash evaluation.

## 4. What's inspiration only

The flash-moe _achievement_ — a frontier-scale model on a laptop — is the north-star demo Linus should eventually be
able to reproduce. It's also the concrete argument for why a roadmap item like "run a ~400B MoE locally on Dan's
MacBook" is not science fiction; the demo exists on M3 Max, and the M1 Max 32 GB case is a smaller-scale version of the
same problem.

## 5. What's incompatible or out of scope

Hardware and scale differences. flash-moe runs on 48 GB; Dan has 32 GB. The M1 Max's SSD is slower than the M3 Max's
17.5 GB/s Apple Fabric (the paper notes "3× faster than M1 Max" explicitly), so the SSD-bound 2.41 ms/layer step will be
worse here. Qwen3.5-397B-A17B may be too large for even streaming on 32 GB; the closer M1 Max target is probably a
~100B-class MoE (GPT-OSS-120B, a Mixtral-class model) or a dense 1-bit 30B via Bonsai. Also: flash-moe is Objective-C
and Metal directly; Linus is Python + Rust (pmetal). Any reuse is at the technique level, not the code level.

## 6. Recommendation: **Study (primary reference for Phase 6d)**

Read the paper end-to-end before Phase 6d. Extract the experiment log format — 58 entries with kept/discarded + why —
and use it as the template for Linus's own Phase 6d results table. Do not try to port flash-moe to Linus. Do look at
`mlx-flash` as the MLX-native analogue that would actually integrate with Linus.

## 7. Questions for Dan

- **The 32 GB flash-moe analogue.** flash-moe ran ~400B on 48 GB. On the M1 Max 32 GB with a slower SSD, the comfortable
  ceiling is probably a ~100–150B MoE or a 30–50B dense-1-bit model. Want me to sketch a concrete Phase 6d target ("get
  MODEL X running at N tok/s on Dan's hardware") once Phase 1b closes?
- **"Trust the OS" as a Linus design principle.** The flash-moe finding that every custom cache lost to the OS page
  cache is a strong generalizable principle. Explicitly promote it to a Linus engineering convention in CLAUDE.md, or
  keep it implicit?

  _Resolved (DEC-0027, see [answered-questions.md](../questions/answered-questions.md)): Adopted as CLAUDE.md
  Engineering Convention; OS page cache trusted by default for all mmap'd/SSD-streaming workloads._
- **Autoresearch + flash-moe methodology fusion.** Phase 7c's overnight iteration loop is essentially the flash-moe
  experiment log run as a supervised AI loop against a tok/s target. Is this the first concrete use case for the Phase
  3b parallel-agent infrastructure, or does it stay a later-phase thing?
- **Objective-C / Metal-direct as an escape hatch.** If Linus ever needs flash-moe-level control — say, to beat pmetal
  on a specific workload — we'd be writing Obj-C and Metal by hand. That's a skill Dan doesn't currently have. Is
  acquiring it a Phase 7+ bet, or ruled out in favor of "whatever pmetal supports"?

  _Resolved (DEC-0027, see [answered-questions.md](../questions/answered-questions.md)): Obj-C + Metal accepted as a
  language escape hatch; Linus stays on public Apple APIs; pmetal is the primary path, not custom Obj-C._
