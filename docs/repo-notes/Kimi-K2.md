# Kimi-K2 (`moonshotai/Kimi-K2`)

## 1. Purpose and scope

Kimi-K2 is Moonshot AI's release vehicle for the **Kimi K2 model family** — a 1.04T-parameter / 32B-active
Mixture-of-Experts open-weights large language model with state-of-the-art agentic capabilities, distributed under a
**Modified MIT license**. The repo itself is deliberately thin: it contains the tech report
([`tech_report.pdf`](../../repos/Kimi-K2/tech_report.pdf), 5.1 MB, also on arXiv as
[2507.20534](https://arxiv.org/abs/2507.20534)), the README that summarizes the model card and benchmark tables,
deployment guidance documents under `docs/`, the figures used in the paper and README, and a `LICENSE` file. There is
**no code** for training, inference, or fine-tuning in this repo — Moonshot's intent is that downstream consumers deploy
via established external inference engines and read the tech report for architectural detail. All architectural and
training-process content lives in the paired paper-note
([`Kimi-K2-2507.20534.md`](../paper-notes/Kimi-K2-2507.20534.md)); this note treats the repo as a **distribution +
deployment artifact** only.

## 2. Architecture summary

The deliverable is a pair of HuggingFace-hosted checkpoint families:
[`moonshotai/Kimi-K2-Base`](https://huggingface.co/moonshotai/Kimi-K2-Base) (the foundation model intended for
fine-tuning) and [`moonshotai/Kimi-K2-Instruct`](https://huggingface.co/moonshotai/Kimi-K2-Instruct) (the post-trained
reflex-grade chat/agent model). Both ship in **block-fp8** format — the active distribution shape — which represents
weights as FP8 values inside small blocks with shared FP32 scales, rather than uniform FP8 across the model. Block-fp8
was chosen to balance disk size against numerical stability for inference; total checkpoint footprint is on the order of
**~1 TB on disk** for the 1.04T-parameter model.

Recommended inference engines (per README §4): **vLLM, SGLang, KTransformers, TensorRT-LLM**. All four are
production-grade, GPU-native (CUDA), and require multi-GPU clusters at FP8 — none currently runs natively on Apple
Silicon. There is no MLX path; there is no llama.cpp path; there is no native Metal kernel. Anyone running Kimi K2 on
Apple Silicon today is either (a) re-quantizing aggressively and using llama.cpp once it lands MLA-MoE support, or (b)
building a flash-MoE-style expert-streaming engine from scratch. The Linus path goes through the flash-MoE / pmetal /
mlx-flash route, not through any of the four officially supported engines.

The repo also documents two **API surfaces** at `platform.moonshot.ai`: an OpenAI-compatible HTTP endpoint and an
**Anthropic-compatible** endpoint. The Anthropic-compatible API has a documented behavioral quirk:
**`real_temperature = request_temperature × 0.6`**. That is, a request with `temperature: 1.0` is internally served at
temperature 0.6 — the API does the translation silently. The recommended `temperature = 0.6` setting in the README's
chat examples is therefore the OpenAI-compatible value; through the Anthropic-compatible API the same behavior would
require `temperature ≈ 1.0` from the caller.

The deployment-guide documents under `docs/` (`deploy_guidance.md` and `tool_call_guidance.md` per README links) walk
through vLLM and SGLang launch commands and tool-call message-format specifics. They are external-engine configuration
recipes, not architectural content.

## 3. What's reusable in Linus

Architectural and training claims (the MuonClip optimizer, the 1T-MoE-with-MLA topology, the synthetic agentic-data
pipeline, the joint RL framework, the sparsity-48 scaling law, the MuonClip τ = 100 zero-loss-spike result) **all defer
to the paired paper-note**, [`Kimi-K2-2507.20534.md`](../paper-notes/Kimi-K2-2507.20534.md). This repo-note focuses
exclusively on what the **artifact** provides:

**Block-fp8 as a distribution-shape signal.** The choice of block-fp8 (rather than uniform FP8 or BF16) is itself
informative: block-quantized formats with FP32 scales are now table-stakes for trillion-parameter open-weights
distribution. Linus's eventual Phase 6/8 quantization work — whether via re-quantization of an existing FP8 checkpoint
or via training a 1-bit Linus-flavored variant from scratch (DEC-0056 seed in the paper-note) — should default to
block-quantized scales rather than uniform.

**License posture.** The Modified MIT license is more permissive than Llama 3 Community License (which has explicit
700M-MAU and competitive-use exclusions) and closer to Apache 2.0 than to either. The modifications are attribution and
threshold-based: distributors with >100M monthly active users _or_ >$20M USD in monthly revenue must add a "Powered by
Kimi K2" attribution. At Linus's scale these clauses are inert. They become relevant only at hypothetical distribution
scenarios well beyond the current Linus roadmap.

**Inference-engine selection signal.** The four officially supported engines (vLLM, SGLang, KTransformers, TensorRT-LLM)
are all CUDA-native and confirm the open-weights frontier-model deployment story is currently GPU-cluster-shaped. Apple
Silicon support arrives, when it does, through community llama.cpp / MLX ports rather than Moonshot's official channel.
Linus's path is therefore consistent with the pmetal / mlx-flash / flash-moe lane already established in
[`docs/syntheses/repo-clusters/g1-apple-silicon.md`](../syntheses/repo-clusters/g1-apple-silicon.md).

**Anthropic-compatible API surface as a Linus front-end pattern.** Kimi K2's deployment ships an Anthropic-compatible
HTTP surface alongside an OpenAI-compatible one. This is an emerging pattern across open-weights distributions and is a
confirming signal for revisiting Linus's DEC-0005 commitment to OpenAI-compatible-only at some future phase. The
temperature-mapping quirk (`real_temperature = request_temperature × 0.6`) is a useful concrete cautionary tale:
Anthropic compatibility is not a transparent passthrough; it is a semantic translation that downstream callers must be
aware of. If Linus ever adopts an Anthropic-compatible surface, this kind of quirk needs to be either eliminated or
audit-logged.

## 4. What's inspiration only

The repo's **figure assets** under `figures/` (the benchmark bar charts, the architecture diagram, the data-synthesis
pipeline figure) are well-designed reference exhibits for any future Linus deliverable that needs to communicate
"open-weights frontier model" to a non-specialist audience. They are not vendored.

The **deployment guides** for vLLM and SGLang are useful as templates for what a Linus-equivalent deployment guide
should look like once Phase 5/6 has a model-running path documented end-to-end. Format reference, not content reuse.

The **README structure** (Model Introduction → Model Summary table → Evaluation Results → Deployment → Model Usage →
License → Citation) is a clean template for any Linus-released model card or evaluation report.

## 5. What's incompatible or out of scope

The four supported inference engines (vLLM, SGLang, KTransformers, TensorRT-LLM) are CUDA-native and not portable to
Apple Silicon as-is. There is no current path from this repo to a working Linus inference loop without significant
re-quantization and engine-substitution work; that work is the Phase 6d / Phase 8 research program, not a
ready-to-integrate artifact.

The block-fp8 weight format is not directly consumable by Apple-Silicon-native tooling (MLX, llama.cpp, the BitNet
runtime, pmetal). Conversion to MLX or to a flash-MoE-style on-disk layout is a separate engineering task that the repo
does not assist with; it provides the source weights and nothing more.

The Modified MIT license's attribution clause is straightforward to comply with at Linus's current scale, but the
**training-data constitution** of the model is not disclosed in the released artifacts. For any downstream commercial or
distribution scenario, the absence of a documented training-data lineage is a separate concern that neither the license
nor the README addresses; the safety-and-alignment posture of running Kimi K2 in production is not derivable from this
repo alone.

There is **no fine-tuning code** in the repo. LoRA, QLoRA, or full fine-tuning of either Kimi-K2-Base or
Kimi-K2-Instruct requires the user to bring their own training stack (Transformers + PEFT, or MLX-LM + LoRA, or
similar). The paper-note's Phase 6 LoRA-base-candidate framing assumes an external fine-tuning pipeline; this repo does
not provide one.

## 6. Recommendation: **Study (with a high prior on later Integrate-as-base-model at Phase 6/8 contingent on weight-streaming evidence)**

Read the paired paper-note end-to-end before any Phase 6 base-model decision. Treat this repo as the
**distribution-and-license artifact** rather than as a code dependency. The integration path runs through the flash-MoE
/ pmetal / mlx-flash lane — re-quantize the block-fp8 checkpoint to int4 or ternary, build an expert-streaming inference
engine on Apple Silicon, measure per-token latency on Dan's M1 Max + 600 GB external SSD, and decide on the basis of
measured agentic-benchmark deltas after LoRA on Dan's domain corpus. The DEC-0055 (Phase 6 LoRA base candidate) and
DEC-0056 (Phase 8 1-bit Linus-flavored variant) seeds in the paper-note set the decision framework; this repo provides
the source artifacts to act on those decisions when the time comes.

Do **not** vendor this repo. Do **not** copy the figures or the deployment guides into the Linus tree. Do read the
`LICENSE` file and surface any actionable obligations into [SAFETY.md](../../SAFETY.md) or
[DECISIONS.md](../../DECISIONS.md) before any non-experimental downstream use.

## 7. Questions for Dan

1. **Modified MIT license review prior to Phase 6 commitment.** The license carries attribution and revenue-threshold
   clauses (>100M MAU or >$20M monthly revenue triggers a "Powered by Kimi K2" attribution requirement) that are inert
   at Linus's current scale but activate at any future commercialization scenario. Should we read the `LICENSE` file
   end-to-end now and add a small entry to [DECISIONS.md](../../DECISIONS.md) (or [SAFETY.md](../../SAFETY.md))
   documenting which clauses apply at which Linus-scale thresholds, before any LoRA spike runs against the Kimi-K2-Base
   checkpoint?

2. **Anthropic-compatible API surface as a future-Phase Linus capability.** DEC-0005 commits Linus to OpenAI-compatible
   HTTP. The fact that Moonshot ships both surfaces suggests that future-Phase Linus front-ends may benefit from
   Anthropic compatibility too — particularly if Cline / claw-code / openclaw consolidate on Anthropic protocol over
   time. Worth a separate ADR ("Anthropic-compatible HTTP as a Phase 5+ Linus capability, alongside OpenAI-compatible")
   that absorbs the temperature-mapping quirk as a worked example of why protocol compatibility is semantic rather than
   syntactic?

3. **Block-fp8 → int4/ternary requantization spike scope.** The Phase 6d weight-streaming feasibility question
   (paper-note open question 1) reduces to: can the block-fp8 distribution be re-quantized to int4 or ternary while
   preserving SWE-bench Verified / τ²-Bench performance, and how much engineering does that take? Is this a bounded
   spike Linus runs in Phase 1c/1b alongside the pmetal vs. PrismML decision (DEC-0049), or does it wait for Phase 6
   proper? The earlier we get the requantization curve, the earlier the Phase 6/8 base-model decision can commit.

4. **Distribution-size logistics on the 600 GB external SSD.** The block-fp8 distribution is ~1 TB and does not fit on
   the 600 GB external SSD as-distributed. Streaming download + on-the-fly requantization to int4 is feasible but adds
   engineering surface. Alternatively, do we plan for a 2 TB external SSD upgrade as part of the Phase 6d hardware
   budget, or do we commit to running Kimi K2 only after a successful int4/ternary requantization?
