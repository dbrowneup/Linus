# CodeV (`IPRC-DIP/CodeV`)

## 1. Purpose and scope

CodeV is the shared code release for two QiMeng-family papers on LLM-driven Verilog generation: **CodeV** —
[Empowering LLMs with HDL Generation through Multi-Level Summarization (2407.10424v5)](../paper-notes/2407.10424v5.md) —
and **QiMeng-CodeV-R1** —
[Reasoning-Enhanced Verilog Generation (2505.24183v5)](../paper-notes/2505.24183v5.md) — from the State Key Lab of
Processors at Institute of Computing Technology, CAS (Yang Zhao, Di Huang, Qi Guo, Yunji Chen group). The repo bundles
the GPT-3.5-based instruction-generation pipeline (the multi-level-summarization data-synthesis machinery from CodeV),
training scripts derived from Magicoder for SFT on Qwen2.5-Coder / DeepSeek-Coder / CodeLlama / CodeQwen base models,
and a vLLM-backed inference + evaluation harness for VerilogEval and RTLLM benchmarks. It is the canonical artifact for
the language-design thread in the LLM-hardware-design family — kernel-design (QiMeng-GEMM, QiMeng-Kernel, QiMeng-MuPa)
and microarchitecture-design (QiMeng-cpu-v1) live in sibling repos.

Distribution: MIT-licensed, with model checkpoints on HuggingFace under `yang-z/CodeV-*` (DS / CL / CQ / QC + four
CodeV-All variants) and a CodeV-R1 follow-on (`yang-z/CodeV-R1-7B`, `yang-z/CodeV-R1-7B-Distill`) plus the dataset
`yang-z/CodeV-All`. README is explicit that "this repo is under development" — meaning the public release is the
methods + scripts + checkpoints, not a polished framework.

## 2. Architecture summary

Three top-level subdirectories under `src/`:

- **`src/Instruction_generation/`** — the data-synthesis pipeline from CodeV. Two scripts:
  - `gpt.py` calls the OpenAI API in a 100-thread semaphore-bounded loop, reading a prompt template from disk
    (placeholders for `{our_code}`), substituting the Verilog snippet, and capturing the GPT-3.5 (or compatible) response
    as the multi-level summary. Threading is hand-rolled around `requests` / `openai` Python SDKs with file-locked
    output.
  - `changeDatasetFormat.py` is a small JSONL → fine-tune-ready format converter with a fixed seed for reproducibility.
- **`src/train/`** — `train.sh` is a thin wrapper around the Magicoder training entry point (`python -m magicoder.train`
  via `accelerate launch`). Hardcoded values for `MODEL_KEY`, `OUTPUT_DIR`, `DATAFILE_PATHS` are blank in the published
  copy; user must fill in. Configuration: bf16, flash-attention 2, max sequence length 2048, 3 training epochs, batch
  size 1 with gradient accumulation 64, adafactor optimizer, learning rate 5e-5 linear warm-up over 15 steps. This is
  the SFT recipe that produces the CodeV-Verilog and CodeV-All checkpoints; CodeV-R1's distillation stage uses an
  analogous SFT run on the chain-of-thought-augmented dataset.
- **`src/test/`** — vLLM-based inference + evaluation. `inference.py` loads a vLLM `LLM` with `gpu_memory_utilization=0.9`,
  optional tensor parallelism via `num_gpus`, `enforce_eager=True` (vLLM eager mode for stability — explicitly flagged as
  "vllm is not a stable library, watch its updates"). `run_cl.py` drives a sweep across a JSONL test set with
  `temperature=0.2` SamplingParams. `config.json` is the per-run hyperparameter record. The harness depends on the
  `verilog-eval` package (NVIDIA Labs, pinned via editable git install) for VerilogEval simulation + scoring; RTLLM
  testing is a separate dependency the README points to (`hkust-zhiyao/rtllm`).

`requirements.txt` is the giveaway for the deployment surface: torch 2.1.2 + flash-attn 2.5.6 + vllm 0.3.3 + accelerate
0.28.0 + DeepSpeed 0.14.0 + bitsandbytes 0.43.0 + the full nvidia-cuda12 stack (cublas, cudnn, cufft, curand, cusolver,
cusparse, nccl, nvjitlink). CUDA 12.x is hard-required; cupy-cuda12x is in the deps; xformers 0.0.23.post1 is pinned.
**There is no path to running the training stack natively on Apple Silicon** — every accelerator-side dep assumes
NVIDIA. The inference path (vLLM 0.3.3) similarly assumes CUDA; running CodeV / CodeV-R1 on M1 Max requires an
alternative inference engine (Ollama, mlx-lm, llama.cpp via MLX backend) loading the HuggingFace checkpoints in a
re-quantized form (GGUF or MLX-converted).

CodeV / CodeV-R1's architectural innovations (multi-level summarization recipe, automated testbench generation,
adaptive DAPO algorithm, round-trip data synthesis) live in the **paper-notes**, not here. The repo-side artifacts are
the **methods-as-code** (instruction-generation script, SFT script) and the **evaluation harness**. Architecture
commentary on the recipes themselves is deferred to
[2407.10424v5.md](../paper-notes/2407.10424v5.md) (CodeV) and
[2505.24183v5.md](../paper-notes/2505.24183v5.md) (CodeV-R1) per the doc-type convention that paper-notes carry the
architectural claims and repo-notes carry the deployment surface.

## 3. What's reusable in Linus

**Phase 6 — frozen Worker checkpoints, hosted via Ollama / mlx-lm.** The four CodeV-Verilog and four CodeV-All
checkpoints (7B class) plus CodeV-R1-7B and CodeV-R1-7B-Distill are MIT-licensed and small enough (~4 GB int4) to host
locally on M1 Max as MCP-wrapped Verilog-generation Workers. Practical recipe: download a HuggingFace checkpoint, convert
to GGUF via `llama.cpp/convert_hf_to_gguf.py` (or to MLX format via `mlx-lm.convert`), quantize to int4, expose via
Ollama or mlx-lm. The vLLM inference path in `src/test/inference.py` is not directly portable; the alternate inference
backends are. Whether this is **useful** to Dan depends on whether Linus ever needs Verilog generation — addressed in
the paper-note Open questions; probably no, but the artifact is cheap to keep on hand.

**Phase 6 — multi-level summarization data-synthesis pipeline as a portable pattern.** The
`src/Instruction_generation/gpt.py` thread-pooled summarization loop is a 100-line Python harness that any CodeV-style
fine-tuning effort can reuse. Architecturally, it's just "for each artifact, ask a teacher LLM for a multi-level
summary, write JSONL." The CodeV recipe's transferability to Dan's domain corpora (bioinformatics scripts, KEGG SBML,
LanzaTech metagenomics SOPs) is discussed in [2407.10424v5 paper-note Open question 1](../paper-notes/2407.10424v5.md);
the repo-side artifact for that recipe is this 100-line script. Map to Phase 6 via:
[`docs/specs/qimeng-category-promotion.md`](../specs/qimeng-category-promotion.md) §"What remains to be done" task 7d.

**Phase 6 — Magicoder-flavored SFT recipe as a baseline.** The training shell script captures a documented working SFT
recipe for Verilog (and by extension Chisel, and by further extension any low-resource code domain): bf16 + flash-attn 2
+ adafactor + 3 epochs + batch 1 × grad-accum 64 + max-seq 2048 + linear-warmup-15. This is the recipe Linus's first
Phase 6 fine-tune (whatever the target domain) should baseline against. The script itself is NVIDIA-only, but the
hyperparameter set is portable to any SFT framework Linus ends up using on Apple Silicon (mlx-lm-ft, MLX LoRA, etc.).

**Phase 7 — CodeV-R1's testbench-generation harness as a candidate skill.** Per CodeV-R1
[paper-note Open question 5](../paper-notes/2505.24183v5.md), the testbench-generation framework (Yosys + iverilog +
custom Python) is independently a Phase 7 candidate skill — Linus producing a testbench from a Verilog reference,
exposed via MCP to Maestro. The harness is not currently in this repo (the README points to NVIDIA's `verilog-eval` and
HKUST's `rtllm`); CodeV-R1's project page (https://iprc-dip.github.io/CodeV-R1) is where the testbench code is
released. Worth tracking as a separate repo if the testbench-as-skill direction matures.

**Phase 6 — adaptive DAPO algorithm as a generic RLVR speedup.** The CodeV-R1 paper claims a 1.25× training-cost
reduction from adaptive DAPO; the algorithmic detail is in the paper, the implementation is presumably in
`yang-z/CodeV-R1`'s training code (current public release status to be verified). Either way, the pattern is portable
to any DAPO-derivative RLVR run — relevant for any future Linus self-improvement loop. _Seed: DEC-NNNN_ candidate per
[2505.24183v5 paper-note "Phase 6 — RLVR loop as a Worker self-improvement substrate"](../paper-notes/2505.24183v5.md).

**Idea → reality discipline.** Per [`qimeng-category-promotion.md`](../specs/qimeng-category-promotion.md), CodeV +
CodeV-R1 are the QiMeng family's exemplars at the **language-design** level: artifact = Verilog source, downstream
actor = synthesis toolchain (Yosys, Synopsys DC, Cadence Genus), oracle = functional simulation (VerilogEval testbenches,
RTLLM, CodeV-R1 automated testbench). The repo is the "code form" of the discipline; the papers are the methodology
form. This anchoring matters for the Phase 7 idea-to-reality skill class generalization — Linus designing process
flowsheets, expression vectors, BOMs follows the same artifact / actor / oracle factoring.

## 4. What's inspiration only

**The instruction-generation thread-pool harness is a 100-line Python script with hand-rolled threading and
file-locking** — fine for a one-off research-grade data-synthesis run, not production-grade. For Linus's eventual
data-synthesis workflows the inspiration is the **shape** (per-artifact teacher-LLM call producing JSONL output), not
the implementation. A production version would use `asyncio` + `httpx` or a proper task queue + structured logging +
retry-with-backoff; the published code does none of that.

**The Magicoder-derived SFT recipe is documented but not novel.** The hyperparameter set works, but it's neither
heavily tuned nor accompanied by ablations within this repo (the paper has the data-size ablations). Linus's eventual
fine-tune on a different domain may want different hyperparameters; the recipe is a starting point, not a target.

**The vLLM inference harness is functional but tightly coupled to CUDA.** The `enforce_eager=True` flag and the explicit
"watch vllm updates" comment hint that the authors hit instability they didn't fully diagnose. For Linus, the
inspiration is the **shape** of the harness (load model, run JSONL test set, score against a benchmark), not the
specific vLLM dependency.

**README cites the "CodeV is under development" disclaimer.** As of the repo's current state, README is sparse, the
`config.json` has hardcoded blanks, and several script paths are placeholders (`r""` empty raw strings). Linus engineers
adapting this code should expect to fill in gaps from the papers; the repo is a methods release, not a turnkey product.

## 5. What's incompatible or out of scope

**NVIDIA CUDA 12.x is hard-required for training and for the published vLLM inference path.** Every accelerator-side
dep in `requirements.txt` assumes CUDA: torch 2.1.2 (CUDA build), flash-attn 2.5.6 (NVIDIA-specific), vllm 0.3.3 (CUDA
backend), nvidia-cuda-cublas / cudnn / cufft / curand / cusolver / cusparse / nccl / nvjitlink, cupy-cuda12x, xformers
0.0.23.post1 (CUDA), bitsandbytes 0.43.0 (CUDA), DeepSpeed 0.14.0 (CUDA primary). **None of this runs natively on
Apple Silicon.** Per CLAUDE.md §Hardware Constraints — Docker macOS doesn't pass through Metal or ANE either, so
containerized fallback is also off-limits. Linus's only viable path to using CodeV / CodeV-R1 on M1 Max is via the
**HuggingFace checkpoint** loaded in an alternate inference engine (Ollama, mlx-lm, llama.cpp + MLX); training
reproduction on Apple Silicon is not feasible.

**The training infrastructure assumes a multi-A100-80G or H100 cluster.** Per CodeV-R1 paper-note: 78 hours on 8 A100s
for SFT + 127 hours on 16 A100s for RL = ~2,656 A100-GPU-hours total for the full RLVR pipeline. CodeV's SFT-only run is
much smaller but still cluster-scale. None of this is reproducible on a single workstation.

**Synopsys / Cadence / closed-source synthesis tools are required for production back-end flow.** The repo's evaluation
harness only exercises the front-end (Verilog correctness via testbenches); the back-end (synthesis quality, timing
closure, formal verification, tape-out) is beyond the open-source toolchain. For Linus's idea-to-reality discipline at
the hardware level, this is a known closed-source segment that cannot be internalized.

**Editable git install of `verilog-eval` (NVIDIA Labs) and dependency on `hkust-zhiyao/rtllm`.** These are external
repos with their own maintenance state; integrating CodeV's evaluation pipeline into Linus requires wrapping or
vendoring those upstream dependencies. Both are open-source but not in the Linus tree.

**Repo is not vendored — `repos/CodeV` is read-only reference clone per CLAUDE.md.** Edits to `repos/*` are
forbidden; the canonical pattern (DEC-0010, CLAUDE.md §Tool Use Policy) is to study the patterns + lift selectively
into Linus's own code under `src/linus/`. CodeV checkpoints — if hosted as Workers — get pulled into Linus's
model-cache directory, not into this repo clone.

**The repo currently bundles only CodeV pipeline code, not CodeV-R1's full RLVR pipeline.** Per CodeV-R1's project page
(https://iprc-dip.github.io/CodeV-R1) and paper §1, the CodeV-R1 model + training code + dataset are released — but
the structure of the released code (whether it lives in this same `IPRC-DIP/CodeV` repo, in a sibling `CodeV-R1` repo,
or only on HuggingFace) needs verification. The 2407 paper covers what's currently in `repos/CodeV/src/`; the 2505
paper's code release surface is partially TBD pending repo refresh.

## 6. Recommendation: **Study**

CodeV is **Study** for the same reason QiMeng-cpu-v1 is **Watch** but stronger: the recipes (multi-level summarization,
Chat-FIM-Tag SFT, adaptive DAPO, round-trip data synthesis) are domain-portable and directly relevant to Linus Phase 6
fine-tuning conventions for low-resource code domains, even if Verilog itself is not a Linus skill class Dan needs.
The CodeV-R1 RLVR loop is the corpus's cleanest blueprint for a Worker self-improvement substrate (`_Seed: DEC-NNNN_`
candidate), which makes it more architecturally important than its Verilog-specific framing suggests. The published
checkpoints are MIT-licensed and small enough to host locally as frozen Workers if a Verilog use case ever materializes.
Probable verdict per the [context-foldin-fanout spec](../specs/2026-05-09-context-foldin-fanout.md) Tier 2 table.

**Cluster placement: _Pending llm-hardware-design_** per
[`qimeng-category-promotion.md`](../specs/qimeng-category-promotion.md). Once `g12-llm-hardware-design.md` lands, the
CodeV repo-note Connections + INDEX entry should refresh to point at the new cluster synthesis as the language-design
anchor of the family.

## 7. Questions for Dan

1. **Worker hosting for CodeV / CodeV-R1.** Should Linus pull a CodeV / CodeV-R1 checkpoint into the Phase 1 baseline
   set (alongside Qwen3-Coder, DeepSeek-Coder), even if a Verilog-generation skill isn't on the near-term roadmap?
   Cost: ~4-15 GB disk per checkpoint × the variants we keep, plus a one-time GGUF / MLX conversion. Benefit:
   on-demand Verilog Worker if Dan ever wants one, plus a probe model for studying RLVR-trained reasoning behavior on a
   well-defined oracle domain.

2. **Multi-level summarization sweep over Dan's KB.** Per CodeV
   [paper-note Open question 3](../paper-notes/2407.10424v5.md), the multi-level-summarization pipeline (one-time pass
   with a strong teacher LLM producing fine-grained + high-level summaries per artifact) is a candidate Phase 2/3 KB
   augmentation experiment. The repo's `gpt.py` is the reference implementation. Worth scoping as a Phase 2 KB
   experiment? Token budget for a hosted-Claude-as-teacher one-time sweep on Dan's papers + threads + notes corpus is
   the crux of the cost question.

3. **CodeV-R1 RLVR loop as Phase 6 ADR seed (`_Seed: DEC-NNNN_`).** Per CodeV-R1
   [paper-note Open question 1](../paper-notes/2505.24183v5.md), the four-component pattern (automated oracle +
   round-trip data synthesis + distill-then-RL + adaptive DAPO) is a candidate canonical Linus Worker self-improvement
   architecture. The repo would be the reference implementation for the algorithmic side; the per-domain oracle
   (pytest, ruff, paper-qa, bioinformatics-pipeline) is the Linus-side unit of effort. Worth committing the ADR seed
   number now, ahead of the synthesis lands? Or defer to the synthesis (`g12-llm-hardware-design.md`) for the durable
   architectural commitment per
   [`qimeng-category-promotion.md`](../specs/qimeng-category-promotion.md) §"What remains to be done"?

4. **CodeV-R1 testbench harness as a Phase 7 skill candidate.** Per CodeV-R1
   [paper-note Open question 5](../paper-notes/2505.24183v5.md), the Yosys + iverilog + Python testbench-generation
   framework is independently a Phase 7 candidate skill (Linus producing a Verilog testbench, exposed via MCP). The
   testbench code lives at https://iprc-dip.github.io/CodeV-R1, not in this repo's current public release. Worth
   tracking the testbench code release separately from the model release? If so, watch for a sibling repo or a
   public-release update on the project page.

5. **License audit for ML-supply-chain checkpoints.** CodeV is MIT-licensed; CodeV-R1 inherits the project's licensing.
   The base models (DeepSeek-Coder, CodeLlama, CodeQwen, Qwen2.5-Coder) carry their own (mostly permissive) licenses,
   but each has its own restrictions worth documenting before Linus commits to hosting any of them as a Worker. Per
   CodeV [paper-note Open question 4](../paper-notes/2407.10424v5.md), is there a Phase 7 ML-supply-chain license-audit
   convention worth seeding now — analogous to the biosecurity-tier-control framework (DEC-0047) but for model
   provenance?

6. **g12 cluster synthesis anchoring for the repo-side artifacts.** Per
   [`qimeng-category-promotion.md`](../specs/qimeng-category-promotion.md) §"What remains to be done" Task 5.1, the
   new cluster synthesis (`g12-llm-hardware-design.md`) should treat CodeV (this repo) as the language-design
   repo-side anchor, alongside QiMeng-MuPa / QiMeng-SALV (kernel-design) and QiMeng-cpu-v1 (microarchitecture-design).
   Should the cluster synthesis present these four repos as a single artifact-as-code thread (here is what the
   methods look like in code form), or as parallel substrates of the discipline (each repo demonstrates a different
   level of the artifact / actor / oracle factoring)? Same shape question as the paper-side framing in
   [CodeV paper-note Open question 5](../paper-notes/2407.10424v5.md) and
   [CodeV-R1 paper-note Open question 6](../paper-notes/2505.24183v5.md).
