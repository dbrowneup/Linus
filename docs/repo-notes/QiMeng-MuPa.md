# QiMeng-MuPa (`kcxain/QiMeng-MuPa`)

## 1. Purpose and scope

QiMeng-MuPa is the official implementation of the NeurIPS 2025 paper of the same name (arXiv:2506.11153v2 — see the
paired paper-note [`2506.11153v2.md`](../paper-notes/2506.11153v2.md)). It is a Mutual-Supervised Learning framework for
sequential-to-parallel code translation: a Translator LLM converts C ↔ CUDA, and a Tester LLM generates unit tests for
both languages, in a closed-loop iteration of **Co-verify** (execute both source and target on real CPU/GPU and discard
any triplet whose outputs disagree) and **Co-evolve** (fine-tune both models on the verified triplets via
back-translation). The repo bootstraps from BabelTower's monolingual C and CUDA corpora; after four iterations the loop
converges to 10,563 verified (C, CUDA, 5 unit tests) triplets and a fine-tuned Qwen2.5-Coder-7B Translator that closes
the Pass@1 gap to GPT-4.1 / DeepSeek-R1 from ~30 percentage points to ~2.

The release is **partial as of 2026-05** — README-flagged: "we will release the end-to-end training and evaluation code
in the near future." Shipped artifacts cover the Co-verify pipeline (compile + execute + filter), inference scaffolding
on top of vLLM, the BabelTower-derived monolingual training data, and the eval harness for Pass@k. The Co-evolve
fine-tuning step is not vendored in-repo; the README points at LLaMA-Factory as an external dependency that the user
clones separately and registers the filtered SFT dataset against. The released checkpoints (Qwen3-0.6B-translator and a
QiMeng-MuPa collection) are on Hugging Face under `kcxain/qimeng-mupa`.

The Linus-relevant scope is twofold. First, the Co-verify substrate is a generic two-agent quorum-by-execution pattern
that generalizes well beyond C↔CUDA (Phase 2/3 orchestration primitive candidate). Second, the C↔CUDA target is the
NVIDIA-specific instance of a more general sequential→parallel translation problem; the same framework applied to
sequential-C / Python ↔ MLX or Metal Shading Language is a first-class candidate Phase 7/8 idea-to-reality skill for
Linus on Apple Silicon.

## 2. Architecture summary

Python 3.12 codebase, uv-managed (`uv.lock` provided for reproducibility), built on top of vLLM 0.7.3+ for batched LLM
inference and LLaMA-Factory 0.9.2 for fine-tuning (cloned externally). Top-level layout:

- **`models/base.py`** — single inference abstraction over a Translator or Tester model, with a `PromptType` enum
  selecting the role.
- **`trans/`** — translation-side scaffolding. `vllm_predict.py` runs C-to-CUDA or CUDA-to-C inference in batch on the
  monolingual BabelTower corpus; `vllm_predict_ut.py` handles unit-test generation via the Tester role; `train.py` and
  `backtrans.py` wrap LLaMA-Factory for the back-translation loss; `dataset.py` and `evaluation/` handle data and
  metric plumbing; `LLaMA-Factory/` is a placeholder for the user's checkout.
- **`unit_test/`** — the Co-verify substrate. `compiler.py` defines a `LocalCompiler` (and a `DOCKER` enum branch) that
  compiles C with gcc and CUDA with nvcc, executes the binaries, and returns a typed `CompilingResult`
  (SUCCESS / RUNTIME_ERROR / COMPILE_ERROR / TIMEOUT / MEMORY_ERROR / UNKNOWN_ERROR). `validator.py` orchestrates the
  cross-execution: for each (source, target, unit-tests) candidate triplet, it compiles+runs both versions, normalizes
  the outputs, and accepts the triplet only if they agree on every test. `generator.py` and `prompts.py` carry the
  CUDA-Kernel-Wrapper and Function-Call-Wrapper prompt templates (the hand-engineered scaffolds that paper over the
  C++ ↔ CUDA calling-convention difference). `eval_passk.py` and `eval_cov.py` implement the Pass@k and coverage
  metrics. Multiprocessing (`Pool`) parallelizes the per-triplet compile-execute work.
- **`scripts/build_sft.sh`** — the Co-verify driver. Runs `trans.vllm_predict` for both directions (C-to-CUDA and
  CUDA-to-C), then `unit_test.validator` to filter and emit the SFT data file.
- **`scripts/eval_pass_k.sh`** — runs `unit_test.eval_passk` over a target model for the Pass@k benchmark on the
  BabelTower 233-pair test set.
- **`BabelTower/dataset/`** — the monolingual C and CUDA corpora (filtered for compile-pass) that bootstrap the loop.
- **`unit_total_eval_cases.jsonl`** — the test set with five GPT-4-generated unit tests per pair (the 233-pair test
  set after compile-filtering down from 364 BabelTower pairs).

The execution model assumes a Linux + CUDA + GCC + nvcc + GPU box — the paper's experiments were on
Llama3-8B-Instruct, Qwen2.5-Coder-7B, and Qwen3-0.6B, and the eval harness includes calls out to OpenAI-compatible
APIs for GPT-4 / GPT-4o / GPT-4.1 / DeepSeek baselines. Heavy use of CUDA-specific tooling (`nvidia-cuda-nvcc-cu12`),
DeepSpeed for distributed training, swanlab for telemetry, and `tree-sitter-c` for AST analysis.

The Co-verify loop's wall-clock cost is dominated by the per-triplet compile-execute step. Each iteration filters
hundreds-to-thousands of triplets (759 C / 2459 CUDA at iteration 1, growing to 2079 / 8484 at iteration 4); each
candidate must be compiled (C with `gcc`, CUDA with `nvcc`), wrapped with the appropriate boilerplate, executed, and
its outputs normalized and compared. Compile and launch latency are non-trivial — for CUDA on real hardware,
microseconds per launch but on the order of a second per `nvcc` invocation; the multiprocessing `Pool` over candidates
is what makes the loop tractable.

## 3. What's reusable in Linus

The MuPa idea→reality triplet maps cleanly: **artifact** = parallel CUDA source code (Translator) and
language-appropriate unit tests (Tester); **downstream actor** = `nvcc` / CUDA runtime + the test harness on real
hardware; **what must be true for Linus** = a real toolchain to compile and execute candidate code on the hardware
under test, plus wrappers paving over calling-convention differences, plus base LLMs capable of multi-turn structured
output for both translation and unit-test generation. The repo gives a working reference for all four pieces in a
CUDA-flavored implementation; for Linus, all four exist in a Metal/MLX-flavored implementation that hasn't been built
yet, and this repo is the closest substrate-grade reference for it.

**Phase 7/8 — the Apple-Silicon analog skill.** The most exciting Linus-specific read. CUDA is to NVIDIA as MLX (or
Metal Shading Language) is to Apple Silicon, and the data-scarcity asymmetry that justified MuPa for C↔CUDA is even
more severe for C/Python ↔ MLX. A MuPa-on-MLX adaptation would: substitute the LocalCompiler's CUDA branch with an
MLX/Metal compiler invocation; replace the CUDA Kernel Wrapper prompt template with a Metal threadgroup +
buffer-binding wrapper; swap the BabelTower CUDA monolingual corpus for a curated MLX/Metal-kernel monolingual corpus
(Phase 7 effort, comparable in shape to QiMeng-GEMM's hint repository); use the same vLLM-driven Translator/Tester
inference scaffold (with vLLM running the local Qwen3-Coder Worker on the M1 Max). The Co-evolve back-translation
fine-tune is conventional LLaMA-Factory training and would run on whatever GPU substrate Linus has access to (M1 Max
LoRA is plausible for sub-7B; full fine-tune at 7B+ is at the edge per CLAUDE.md). The infrastructure pattern (driver
scripts + per-triplet validator + filtered SFT dataset + back-translation loop) is directly liftable.

**Phase 6 — Co-verify as a triplet-store + filter pipeline.** Even without porting to Apple Silicon, the
`unit_test/validator.py` substrate is a clean reference for the kind of "execution-oracle filter" that Phase 6 fine-
tuning data quality depends on. Lifting the typed `CompilingResult` enum, the wrapper-prompt structure, and the
multiprocessing `Pool` orchestration into a Linus-internal data-curation utility is a few-hundred-LOC port and gives
the project a generic "compile + run + compare → admit triplet" filter usable for any code-translation skill (not just
sequential→parallel). Tag this as a _candidate utility module_ for Phase 2a or Phase 6 prep work, depending on when
the first code-translation skill lands.

**Phase 6 — typed-triplet record as KB-ingestion shape.** The released 10,563 verified (C, CUDA, 5-tests) triplets are
themselves a Phase 6 fine-tune candidate **outside** the Apple-Silicon-port question. The triplet shape `{source,
target, unit-tests, oracle-result, language-pair}` is an instance of the typed-structured-prediction-wrapping-rationale
convention from CLAUDE.md (S25), and a clean fit for the model-prediction-edge-class spec (DEC-0048) in the
KnowledgeBase. Surfacing these triplets as queryable KB records gives downstream Linus skills (kernel-codegen,
code-review, parallelization-suggestion) high-quality exemplars without re-running the loop.

**Phase 2/3 — Co-verify as an orchestration primitive.** Stripped of the C↔CUDA specifics, the Co-verify step is a
generic two-agent quorum-by-execution pattern: Worker-A emits artifact, Worker-B emits validator/test, the orchestrator
runs both and accepts the joint output only on cross-validation. This is a natural extension of the workgraph
DAG-dispatch substrate (G7 synthesis,
[`docs/syntheses/repo-clusters/g7-harnesses.md`](../syntheses/repo-clusters/g7-harnesses.md)) and the role-typed
agent-spawner pattern (DEC-0050, DEC-0051) — the verifier-by-execution role becomes first-class rather than ad-hoc.
This substrate use is tractable in Phase 2/3, before any of the fine-tuning use cases are reachable.

**Phase 6 — language-agnostic shared-weight finding as a base-model-architecture data point.** MuPa's empirical result
that one model trained on both directions and both languages beats per-(direction × language) specialization at the
7B–8B scale informs the Phase 6 base-model question (consistent with DEC-0043).

## 4. What's inspiration only

The CUDA Kernel Wrapper prompt template (`unit_test/prompts.py`) is hand-engineered domain knowledge — comparable in
shape to QiMeng-GEMM's hint repository. The general principle (generate language-bridge wrappers via a few-shot
prompt with one or two worked examples) ports to Metal/MLX, but the specific prompt content does not.

The vLLM-based inference scaffolding (`trans/vllm_predict.py`) is well-suited to NVIDIA + 7B-class model batched
inference. On Apple Silicon, vLLM is not the right inference path — Linus's path is Ollama + mlx-lm (and eventually
pmetal/MLX) per ARCHITECTURE.md. The structural pattern (batch-inference driver script over a monolingual corpus →
JSONL output → validator filter) ports cleanly; the specific framework dependency does not.

The repo's swanlab + LLaMA-Factory + DeepSpeed training stack is a CUDA-cluster pattern. Linus's training stack is
MLX-LM-FT and `mlx_lm` per the Phase 6 plan. The fine-tuning code in `trans/train.py` and `trans/backtrans.py` is
inspiration only.

## 5. What's incompatible or out of scope

The repo is **NVIDIA-CUDA-locked end-to-end**: `pyproject.toml` declares `nvidia-cuda-nvcc-cu12` and `vllm` as
dependencies; `unit_test/compiler.py` runs `nvcc` directly; the Co-verify execution paths assume a CUDA-capable GPU.
None of this runs on Apple Silicon, and `vllm` itself is Linux+CUDA-only. Direct execution of the released code on
Dan's M1 Max is not feasible.

The README explicitly flags incomplete code release ("we will release the end-to-end training and evaluation code in
the near future"). The Co-evolve fine-tuning side is partially externalized to a user-cloned LLaMA-Factory and a
manual SFT-dataset registration step — i.e., the published flow is "use our Co-verify pipeline to filter your SFT
data, then train your model with LLaMA-Factory yourself." Reproducing the paper's headline results from this repo
alone is not turnkey.

The Docker compile path (`CompileMethod.DOCKER`) is enumerated but per CLAUDE.md "Docker inference is forbidden" on
Apple Silicon (the macOS VM does not pass through Metal or ANE). The local-compile path is the only viable option for
any Apple-Silicon adaptation, and the local-compile path is currently CUDA-tied.

The 233-pair BabelTower test set is small enough that Pass@k confidence intervals on small differences (the
1.56-BLEU-vs-CodeRosetta lift) are wider than the headline suggests. Independent reproduction on a larger benchmark
(e.g., a HumanEval-CUDA variant if one materializes) would matter before betting Linus architecture on the absolute
metric levels.

The MuPa training loop is **two networks of similar size** (Translator + Tester). For Linus's 32 GB unified memory
budget, running both during inference (e.g., for an inference-time self-verifying translation skill) requires
careful memory planning — likely sequential rather than concurrent. Inference-time Co-verify is plausible only if the
two roles share weights or run sequentially with KV-cache discard between turns.

## 6. Recommendation: **Study**

The MuPa _framework_ is the most directly relevant substrate the QiMeng family offers for an Apple-Silicon
kernel-codegen Linus skill, but the published _code_ is so CUDA-tied that direct adoption is not on the table. The
right Linus stance is **Study**: treat this as the canonical reference implementation of the Co-verify / Co-evolve
loop, lift the architectural pattern into a Linus-native MuPa-on-MLX skill in Phase 7/8, and lift the
`unit_test/validator.py` execution-oracle-filter substrate as a Phase 2a or Phase 6 utility module on the way there.
Watch for the promised end-to-end code release; revisit the verdict if the released code becomes more
hardware-agnostic. In parallel, ingest the released 10,563-triplet dataset into the KnowledgeBase as Phase 6 fine-tune
material independent of the Apple-Silicon question.

The probable path: Phase 2/3 lift the Co-verify pattern as an orchestration primitive (verifier-by-execution role);
Phase 7 begin a Linus-native MuPa-on-MLX skill spec; Phase 8 the actual fine-tune and deployment of the Apple-Silicon
Translator/Tester pair.

## 7. Questions for Dan

1. **Apple-Silicon target — minimum viable kernel for a MuPa-on-MLX spike.** What's the smallest meaningful first
   target — a single element-wise kernel (saxpy/axpby), a small fused-attention micro-kernel, a quantized-dequant
   kernel, a softmax+norm kernel? The paper's BabelTower coverage suggests starting with element-wise and small-loop
   patterns; the hint-repo cost is lowest there. The Phase 6d weight-streaming work
   ([`docs/specs/phase6d-streaming-target.md`](../specs/phase6d-streaming-target.md)) would benefit most from an
   attention-class kernel target.

2. **Wrapper-cost estimate before any MuPa-on-MLX loop can run.** The CUDA Kernel Wrapper prompt template is non-trivial
   domain knowledge; the Metal/MLX analog needs to be authored before the Co-verify loop is meaningful. Is this a
   Maestro-authored artifact (Dan + hosted Claude write it once), or a Phase 7 hint-repo deliverable in its own right
   (a curated `hint-repos/metal-kernels/` analog)? Same question applies to the Function Call Wrapper for any C/Python
   sequential reference paired with an MLX target.

3. **vLLM-equivalent for the M1 Max Translator/Tester.** The repo uses vLLM for batched inference on NVIDIA. On Apple
   Silicon, the natural substitute is mlx-lm batched inference or Ollama with parallel completions. Is mlx-lm's
   batching mature enough to drive a Co-verify loop at the iteration size the paper uses (hundreds of triplets per
   round), or do we need to drop iteration size by 10× and accept slower convergence?

4. **Triplet KB ingestion as a separate work item.** Independent of the Apple-Silicon-port question, should the
   released 10,563 verified (C, CUDA, 5-tests) triplets be ingested into the KnowledgeBase now as typed records (per
   the model-prediction-edge-class spec, DEC-0048), making them retrievable as exemplars for kernel-codegen and
   code-review skills? This is a low-risk, near-term Phase 6 prep deliverable that does not depend on any subsequent
   adaptation work.

5. **Co-verify as a Phase 2/3 orchestration primitive vs. a Phase 6 training-time loop.** Two distinct lifts of the
   same pattern. Phase 2/3 lift = adopt verifier-by-execution as a typed-AgentReport validator (DEC-0051) for
   Translator-class Workers. Phase 6 lift = the full MuSL fine-tuning loop as a Worker-pair self-improvement substrate.
   Both are tractable; Phase 2/3 lift has less prerequisite setup (no fine-tuning, no hardware-specific
   compile-toolchain integration). Order matters — do the Phase 2/3 lift first, then the Phase 6/7 lift on top of the
   resulting substrate?

6. **Python↔Rust as a Linus-internal MuPa target.** A Python↔Rust MuPa loop using `pytest` + `cargo test` as the
   execution oracle is a much smaller-scope target than MuPa-on-MLX, runs on whatever hardware Linus has, and doubles
   as a learning aid for Dan (typed exemplars of "how this Python ends up in Rust"). Is this a reasonable Phase 6
   sub-project, scoped before the Apple-Silicon ambition? It would also exercise the Co-verify substrate-lift from
   Question 5 in a real Linus context.

7. **Sub-billion-parameter Translator viability on M1 Max.** The released Qwen3-0.6B-translator achieves Pass@1 84.44 on
   C→CUDA — a sub-billion-parameter model that's frontier-comparable on this specific task. For Linus, a sub-1B
   Translator is comfortably in M1 Max RAM with room for a similarly-sized Tester running concurrently. Worth
   investigating whether the released checkpoint is downloadable and runnable on Apple Silicon as a near-term Phase 1
   benchmark — even before any MuPa-on-MLX adaptation, "can we run their released CUDA Translator locally" is a useful
   datapoint on the inference cost side.
