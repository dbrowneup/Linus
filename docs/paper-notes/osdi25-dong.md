---
title: "QiMeng-Xpiler: Transcompiling Tensor Programs for Deep Learning Systems with a Neural-Symbolic Approach"
source: OSDI 2025 (USENIX Symposium on Operating Systems Design and Implementation)
authors:
  Shouyang Dong, Yuanbo Wen, Jun Bi, Di Huang, Jiaming Guo, Jianxing Xu, Ruibai Xu, Xinkai Song, Yifan Hao, Ling Li,
  Xuehai Zhou, Tianshi Chen, Qi Guo, Yunji Chen
affiliation:
  University of Science and Technology of China; Cambricon Technologies; SKL of Processors, Institute of Computing
  Technology, CAS; Institute of Software, CAS; University of Chinese Academy of Sciences
date: 2025-07
pdf: ../../context/papers/osdi25-dong.pdf
tags:
  [
    llm-code-generation,
    transcompilation,
    neural-symbolic,
    tensor-programs,
    cuda,
    hip,
    bang-c,
    vnni,
    smt-solver,
    mcts,
    auto-tuning,
    qimeng,
    llm-hardware-design,
  ]
---

# QiMeng-Xpiler: Transcompiling Tensor Programs for Deep Learning Systems with a Neural-Symbolic Approach

## TL;DR

Proposes QiMeng-Xpiler, a neural-symbolic transcompiler that automatically translates tensor programs across
heterogeneous deep-learning systems (Intel DL Boost VNNI, NVIDIA CUDA, AMD HIP, Cambricon BANG C) at 95% average
accuracy. The key insight: an LLM (GPT-4) generates a high-level program sketch via a chain of meta-prompted
transformation passes; an SMT solver (Z3) repairs low-level details (loop bounds, indexing, tensor-intrinsic parameters)
at limited scale; and a hierarchical auto-tuner (brute-force intra-pass + MCTS inter-pass) finds optimal pass parameters
and sequences. Translated programs reach 0.78× of vendor-tuned libraries (cuDNN/cuBLAS/CNNL/oneDNN) and improve
programming productivity by up to 96× on MLU and 34× on GPU vs. a senior coder writing manually. 11 transformation
passes across three classes (sequentialization/parallelization, memory conversion, (de)tensorization) cover the full
programming-model gap between SIMT and SIMD/VLIW DLS.

## The problem (in plain language)

Deep-learning data centers run a zoo of accelerators — NVIDIA GPUs with CUDA, AMD MI with HIP, Cambricon MLU with BANG
C, Intel CPUs with VNNI, plus TPUs and IPUs. Each has its own programming model: SIMT vs SIMD vs VLIW, different memory
hierarchies (registers / shared / global; NRAM / WRAM / DRAM), different tensor intrinsics (`wmma::mma_sync`,
`__bang_mlp`, `__builtin_amdgcn_mfma_f32_16x16x4f32`, `_mm512_dpbusd_epi32`). Engineers end up writing the same tensor
program N times. The dream is "Write Once, Run Anywhere" via source-to-source transcompilation, and three families of
approaches have tried: (1) **rule-based** tools like HIPIFY (CUDA→HIP) and PPCG (C→CUDA) — work for trivial cases but
require expert-defined AST transformations and handle only specific language pairs; (2) **symbolic synthesis** like
Tenspiler and MetaLift — provide correctness guarantees via SMT but do not scale beyond DSL-sized programs and cannot
express parallel semantics; (3) **data-driven LLMs** like TransCoder, GPT-4, and OpenAI o1 — fluent but only ~30%
accurate on tensor-program transcompilation because LLMs hallucinate low-level details (wrong loop bounds, wrong tensor
lengths, wrong memory placement).

The paper's framing of the failure modes is precise: GPT-4 zero-shot on CUDA→BANG C compiles 0% of the time. Few-shot
pushes compilation to ~50% but computation accuracy stays at ~8% — the code compiles but computes the wrong answer. Pure
SMT can't represent the problem space. The authors argue these approaches are complementary: LLMs are good at high-level
program sketches (control flow, intrinsic selection), bad at low-level details (loop bounds, indices); SMT is the
inverse. The question: can a structured chain of LLM passes plus SMT repair plus auto-tuning achieve correctness AND
performance AND scalability?

## What they propose

**QiMeng-Xpiler** is a transcompiler with two coupled components:

1. **Neural-Symbolic Program Synthesis.** Decomposes transcompilation into 11 transformation passes (Loop Recovery, Loop
   Bind, Loop Split, Loop Fuse, Loop Reorder, Loop Expansion, Loop Contraction, Cache, Pipeline, Tensorize, Detensorize)
   grouped into three categories:
   - _Sequentialization/parallelization_ — bridges SIMT/SIMD/serial parallel models by mapping built-in parallel
     variables (`threadIdx.x`, `clusterId`, `coreId`) to indexing variables, or vice versa.
   - _Memory conversion_ — bridges memory hierarchies (CUDA `__shared__` → MLU `__nram__`/`__wram__`); inserts cache
     reads, pipelines data movement.
   - _(De)tensorization_ — converts scalar code to tensor intrinsics (`__bang_mlp`, `wmma::mma_sync`) by retrieving
     candidates from the target's programming manual; inverse pass restores scalar form.

   Each pass runs a four-stage workflow: (a) **Program annotation** — an LLM marks code with semantic operation tags
   (`operation(matmul)`); a BM25 search retrieves the corresponding target-platform intrinsic from the programming
   manual; the annotated program carries `intrinsic(__bang_mlp(input[Nram, Wram], output[Nram]))`-style hints into
   transformation. (b) **Meta-prompts based transformation** — a meta-prompt template combines a platform-agnostic
   description (the operation's functionality), platform-specific examples (target-language code skeletons retrieved
   from the manual), and tuning knobs (search-space anchors). The LLM emits a transformed program with a correct sketch
   but error-prone low-level values. (c) **Bug localization** — Algorithm 2: build ASTs of source and transformed
   programs; binary-search over buffers comparing values to find the first faulty buffer; classify the error as
   IndexError (control-flow mismatch) or TensorInstructionError. (d) **SMT-based code repairing** — Algorithm 3: extract
   a code sketch and SMT query encoding loop-bound and buffer-access constraints; feed to Z3; for tensor-instruction
   errors, hand off to Tenspiler for synthesis. The repaired snippet is stitched back. The "limited scale" property —
   each pass touches a small region — is what keeps SMT tractable.

2. **Hierarchical Performance Auto-Tuning.** Two nested search loops:
   - _Intra-pass auto-tuning_ — for each pass with parameters (loop split sizes, loop reorder permutations), an LLM
     enumerates candidates via meta-prompt; brute-force search picks the best. Search-space size varies by DLS (Matmul
     512³: 150 on GPU, 10 on MLU).
   - _Inter-pass auto-tuning_ — Markov decision process over pass sequences: state = current program, action = next
     pass + parameters, reward = real execution time of the transformed program, with reward 0 for transformations
     failing unit tests. **MCTS** (Monte Carlo Tree Search) with 13-deep search and 512 simulations finds optimal
     sequences. Reward is `Rt = max(throughput(p_t,i))` over the intra-pass candidates. Failed transformations get
     pruned by the unit-test wall.

The `S = |D1| × |K1| × ... × |Dn| × |Kn|` search space (passes × tuning knobs) is huge; the hierarchical decomposition
is what makes it tractable.

## Key results

- **Compilation accuracy:** ~100% across all 12 transcompilation directions (CUDA↔BANG↔HIP↔VNNI). GPT-4 few-shot ranges
  23.8% to 97.0%; OpenAI o1 few-shot 41.7% to 98.8%. Rule-based HIPIFY: 85.7% (CUDA→HIP); PPCG: 47.6% (C→CUDA C).
- **Computation accuracy (functional correctness):** 86.9% to 100% across directions. The hardest case is CUDA→BANG
  (SIMT→SIMD across an unfamiliar ISA): GPT-4 zero-shot 0%, OpenAI o1 zero-shot 0%, OpenAI o1 few-shot 48.2%,
  **QiMeng-Xpiler 91.7%**. SMT-repair contribution: ablation removes SMT and computation accuracy drops from 91.7% →
  54.2% on CUDA→BANG.
- **Execution performance:** 0.78× of vendor-tuned libraries on average (cuDNN/cuBLAS, CNNL, rocBLAS, oneDNN).
  Performance gap explained by hand-tuned vendors using assembly, deep pipelining, aggressive unrolling not reachable by
  the pass set.
- **FlashAttention-1/2 case study:** 0.61–0.81× of native FA1/FA2 implementations across direction pairs. Limited by
  inability to match intricate shared-memory tiling.
- **Productivity:** Deformable Attention (~200 LoC) — manual senior coder takes ~6 days for CUDA→BANG; QiMeng-Xpiler
  - senior debug takes 5 hours (28.8× speedup). Junior coder: ~30 days manual vs 7.5 hours w/ tool (96.0×). For C→CUDA:
    11.4× senior, 34.3× junior.
- **Compilation time:** 1.2 to 7.8 hours per operator (avg 3.7 hours) on CUDA→BANG. Time dominated by autotuning for
  matmul-class operators; SMT only triggers when LLM transformation fails unit test.
- **Failure cases:** complex control flow (nested loops + conditionals in Deformable Attention defeats both LLM and
  SMT); difficult-to-understand custom intrinsics (LLM can't annotate semantics it doesn't recognize).

## What's reusable in Linus

QiMeng-Xpiler is the QiMeng family's clearest demonstration of the **idea → reality** spine for cross-platform kernel
transcompilation: the LLM produces a high-level program sketch, the SMT solver (a downstream non-LLM actor) repairs the
sketch, the compiler (clang/nvcc/CNGCC) accepts the result and produces an executable that runs on real silicon. The
paper is also the most directly relevant QiMeng paper to Linus's Apple Silicon substrate-flexibility question — could
the same neural-symbolic approach transcompile CUDA/TensorRT kernels (or BANG C, or HIP) into Metal/MLX kernels? —
because Metal is structurally a fifth DLS in the paper's taxonomy: SIMT-like programming model (threadgroups), explicit
memory hierarchy (threadgroup memory, device memory, ANE), specialized intrinsics (`simdgroup_matrix`, MPSGraph, ANE
primitives). The 11-pass framework is platform-agnostic by construction; the adaptation cost is described as "one-time"
with single-line prompt extensions.

**Phase 6/7/8 — Metal/MLX as a fifth target DLS for QiMeng-Xpiler.** _Artifact the LLM produces:_ Metal Shading Language
(MSL) compute kernels or MLX/Metal kernels for tensor operators (GEMM, attention, softmax, layernorm). _Downstream actor
that accepts it:_ the Metal compiler toolchain + SMT-based repair (Z3) + Tenspiler-extension for Metal/ANE intrinsic
synthesis. _What must be true for Linus to replicate the discipline locally on Apple Silicon:_ (a) a curated Metal
programming-manual digest searchable by BM25 (intrinsic names, parallelism primitives, memory qualifiers) — equivalent
to the BANG C / CUDA C manuals the paper retrieves from; (b) a unit-test harness for each tensor-operator family that
runs on M1 Max within the auto-tuning loop; (c) extension of Tenspiler's code generation backend to emit MSL or MLX
kernels (the paper notes "extending Tenspiler for instructions like TensorCore, MatrixCore, or AVX-VNNI typically
requires only a few lines of code"); (d) an SMT specification of the SIMT-vs-Metal-threadgroup mapping for the Loop
Recovery / Loop Bind passes. Phase 6d's weight-streaming target spec already implies handcrafted Metal kernels;
QiMeng-Xpiler is the methodology that replaces the hand-craft with LLM + SMT + auto-tune. Maps to Phase 6d
(`docs/specs/phase6d-streaming-target.md`), to Phase 7 idea-to-reality skill class seeded in
[`qimeng-category-promotion.md`](../specs/qimeng-category-promotion.md), and to a Phase 8 research direction where Linus
inherits a Cambricon kernel zoo (or PyTorch HIP zoo) and transcompiles it on demand to Apple Silicon — significant for
substrate flexibility because the corpus of optimized CUDA/HIP kernels is orders of magnitude larger than the corpus of
optimized Metal kernels.

**Phase 2/3 — neural-symbolic dispatch as an orchestration primitive.** Stripped of the tensor-program specifics, the
four-stage pass workflow (annotate → meta-prompt-transform → bug-localize → SMT-repair) is a generic "LLM-emits-sketch /
verifier-checks / formal-method-repairs" pattern. The MCTS-over-pass-sequences inter-pass auto-tuner is a typed action
search exactly like the agent-spawner role-typed work-graph (DEC-0050, DEC-0051) — the pass type is the role, the
program state is the work-graph node, the unit-test failure is the typed-AgentReport-validation, the MCTS reward is the
AgentReport's quantitative score. The 11-pass categorization (parallelism / memory / instruction) is also a strong
typed-AgentReport schema candidate: each pass emits a structured record
`{pass_type, params, transformed_code, unit_test_pass, perf_delta, repair_invoked}` that satisfies the
typed-structured-prediction-wrapping-rationale convention (CLAUDE.md S25). The search graph is a durable
scratchpad-class artifact (DEC-0030) — the MCTS tree is exactly the kind of episodic-memory candidate that should
outlive a single transcompilation run.

**Phase 6 — meta-prompt + manual-retrieval as a fine-tuning data shape.** The paper's meta-prompt structure
(platform-agnostic description + platform-specific examples + tuning knobs) instantiated against a programming manual
via BM25 is a high-quality dataset shape for a kernel-transcompilation fine-tune. A LoRA over tuples
`{source_lang, target_lang, pass_type, source_snippet, manual_excerpt, target_snippet, smt_repair_diff}` — bootstrapped
by running QiMeng-Xpiler-style prompting against a strong teacher LLM on a known-good corpus of operator pairs — is a
plausible Phase 6 deliverable. The pattern generalizes the QiMeng-GEMM hint repository to multi-target transcompilation
rather than single-target codegen.

**Idea → reality discipline.** Per [`qimeng-category-promotion.md`](../specs/qimeng-category-promotion.md) §"Dan's
stated framing": QiMeng-Xpiler is the idea-to-reality pattern at the program-translation altitude — an LLM produces a
real artifact (a transcompiled tensor program in the target language) that a real downstream actor (the target DLS's
compiler + SMT solver as a co-pilot) accepts and converts into a runnable binary at vendor-library-quality. There is no
human-in-the-loop between the LLM and the compiled binary other than unit-test feedback and benchmark measurement; the
human cost (Table 5) is the one-time per-DLS setup of a programming manual + a few intrinsic examples. For the broader
Linus design-and-build vision, transcompilation is one altitude up from kernel codegen (QiMeng-GEMM): instead of writing
a kernel from scratch, you translate one. This is directly applicable to "Linus inherits a CUDA codebase and runs it on
Apple Silicon" workflows that Dan's bioinformatics work will encounter (metagenomics tools shipped as CUDA-only).

## What's NOT applicable / hype filter

The 95% average accuracy is across **operator-level kernels** with bounded LoC (7–214). Real-world tensor programs embed
in larger systems (training loops, inference servers, scheduler integration); the paper does not address end-to-end
transcompilation of an entire framework backend. Translating a single GEMM operator does not validate that you can
transcompile a TensorRT engine to a CoreML model, or a vLLM CUDA kernel collection to MLX.

The 0.78× vendor-library performance gap is significant for production deployment. Hand-tuned cuBLAS / CNNL beat
QiMeng-Xpiler by 22% on average and substantially more on FlashAttention-class kernels (down to 0.61×). For Linus
deploying an inference path, transcompiled kernels would need a follow-up hand-optimization pass to close the gap — or
you accept the gap as the cost of automation. The paper is honest about this: deep pipelining, hand-written assembly,
and aggressive unrolling are out of reach.

The compilation time (1.2–7.8 hours per operator on a single direction) is **offline-only**. There is no just-in-time
use case here; this is a build-step tool. For Linus's Phase 6/7 use case (one-time kernel-zoo transcompilation), this is
fine; for any "transcompile on demand at runtime" framing, this is a deal-breaker.

The MCTS auto-tuner relies on **real execution measurements** as the reward signal, which means you need the target
hardware in-loop. To transcompile CUDA → Metal you need an M1 Max in the loop. This is true for Linus by construction
(the M1 Max is the development hardware), but it precludes cross-development from a CUDA-only box.

The four DLS evaluated (Intel VNNI, NVIDIA, AMD, Cambricon) all share the **C-like syntax family**. The paper does not
test transcompilation to MLX (Python-embedded DSL) or to Triton (Python kernel-DSL). MLX in particular is at a higher
abstraction level than CUDA C, and the Loop Recovery / Loop Bind passes may not have a direct mapping. Worth a
feasibility spike before committing to a port.

The SMT solver's tractability hinges on **limited-scale per-pass** problems. Deformable Attention's nested-loop +
conditional control flow defeats it; the paper acknowledges this as a failure mode. Linus's Phase 7 use cases will hit
this wall on any non-trivial control-flow-heavy kernel (sparse attention, dynamic-shape kernels). The
limit-of-the-method is real and architectural.

GPT-4 is the only LLM evaluated. Codestral-22B was excluded; OpenAI o1 was a baseline only. The paper does not report on
whether smaller/local models (DeepSeek-Coder-V2-Lite, Qwen3-Coder-30B-A3B) can sustain the multi-turn meta-prompt
protocol. By analogy with QiMeng-GEMM's Codestral-22B failure (1.0× across all sizes), there is a non-trivial
possibility that local Apple Silicon Workers cannot sustain the QiMeng-Xpiler protocol without adaptation — especially
given the tensor-program transcompilation problem is a strict superset of the single-target codegen problem QiMeng-GEMM
addresses.

The "Tenspiler extension for new DLS" handwave — "typically requires only a few lines of code" — is glib. Tenspiler
itself is a substantial program-synthesis system; extending its code-generation backend for Metal MSL or MLX would be a
non-trivial project, not a few-line patch. The paper amortizes its setup cost across many operators; Linus would need to
amortize across whatever kernel zoo it commits to porting, and that calculus needs explicit estimation.

## Connections

QiMeng-Xpiler sits at the **program-transformation altitude** of the QiMeng family — one step up from kernel codegen
([QiMeng-GEMM (13337-ZhouQ.md)](13337-ZhouQ.md), [QiMeng-Kernel (2511.20100v1.md)](2511.20100v1.md)) and one step down
from full HW+SW design ([QiMeng full overview (2506.05007v1.md)](2506.05007v1.md)). The meta-prompt structure
(platform-agnostic + platform-specific + tuning knobs) is the **same primitive** introduced in QiMeng-GEMM but applied
to multi-pass transformation rather than single-pass codegen. The hierarchical auto-tuning (intra-pass brute-force +
inter-pass MCTS) is the **same search-as-orchestration pattern** as QiMeng-Kernel's macro-thinking/micro-coding split,
with MCTS replacing the RL-trained policy.

Within the QiMeng family the closest thematic neighbors are: [QiMeng-GEMM (13337-ZhouQ.md)](13337-ZhouQ.md) — the
earliest and simplest expression of the meta-prompt + auto-tune pattern (single-target kernel codegen);
[QiMeng-Kernel (2511.20100v1.md)](2511.20100v1.md) — the macro-thinking/micro-coding paradigm with RL replacing beam
search / MCTS; [QiMeng-CRUX (2511.20099v4.md)](2511.20099v4.md) — Verilog code generation, the same prompt-
engineering-as-substrate discipline at the HDL altitude;
[Push the Limits — CPU design via AI (2306.12456v2.md)](2306.12456v2.md) — earlier CAS-group work establishing the
LLM-designs-real-hardware thread; [Cheng et al. superscalar processor design (0549.md)](0549.md) — the closely-related
processor-architecture exemplar; and [QiMeng: Fully Automated HW+SW Design (2506.05007v1.md)](2506.05007v1.md) — the
integrating overview of the family.

The repo-side anchor for the family is [QiMeng-cpu-v1 (repo-note)](../repo-notes/QiMeng-cpu-v1.md) — behavioral
synthesis of a RISC-V CPU using related LLM-driven techniques, the only QiMeng artifact in the corpus that ships
end-to-end source code today.

The cluster home is the in-flight [`docs/specs/qimeng-category-promotion.md`](../specs/qimeng-category-promotion.md)
(B14 / g12-llm-hardware-design), where this paper specifically anchors the **transcompilation-as-idea→reality** thread:
a CUDA tensor program is the input idea, an MLU/HIP/VNNI binary is the realized artifact, the neural-symbolic synthesis
pipeline is the bridge. The cross-paradigm sibling outside QiMeng is Sketch2Simulation (HYSYS process flowsheets via
multi-agent LLMs) — different domain (process engineering vs program transformation), same idea-to-reality pattern with
structured intermediate representations and downstream non-LLM acceptors.

The four-stage neural-symbolic workflow (annotate → transform → localize → repair) is structurally a typed-action
work-graph in the sense of DEC-0050 / DEC-0051; the MCTS-over-pass-sequences inter-pass auto-tuner is a fitness-driven
extension of the workgraph DAG-dispatch pattern documented in the G7 cluster synthesis
([`docs/syntheses/repo-clusters/g7-harnesses.md`](../syntheses/repo-clusters/g7-harnesses.md)). The typed-AgentReport
schema for pass results is a typed-structured-prediction-wrapping-rationale substrate per CLAUDE.md S25. The
SMT-as-repair-co-pilot pattern is the symbolic counterpart to the LLM-Worker-as-orchestration- substrate, and the
unit-test wall as MCTS reward-zero is a direct analogue of typed-AgentReport-rejection in the agent spawner.

The paper's Tenspiler dependency connects to the broader symbolic-synthesis literature (Tenspiler, MetaLift, Z3 SMT
solver) which Linus has not yet integrated; if Phase 6+ Linus adopts QiMeng-Xpiler's pattern, Tenspiler becomes a
candidate dependency alongside MLX and Metal.

## Open questions for Dan

1. **Metal / MLX as a fifth DLS — feasibility spike.** The paper's 11-pass framework assumes a C-family target language.
   Metal Shading Language is C-family (HLSL-derived); MLX is Python-embedded. The Loop Recovery / Loop Bind / Cache
   passes have direct Metal mappings (threadgroup, device memory, threadgroup_position_in_grid). The Tensorize pass
   needs a Metal `simdgroup_matrix` / MPSGraph / ANE-intrinsic vocabulary. What's the minimum viable Metal target — a
   single GEMM variant, an MLX flash-attention-style kernel, a quantized dequant kernel — to validate the methodology
   ports? And is MLX or pure Metal the right altitude for the v1 spike (MLX is more abstract and may not fit the pass
   model; pure Metal is more concrete and closer to CUDA C in surface form)?

2. **Local Worker LLM viability — same question as QiMeng-GEMM, harder problem.** GPT-4 is the only LLM evaluated. The
   multi-pass meta-prompt protocol with annotation + transformation + bug localization requires sustained multi-turn
   capability that smaller/local models historically struggle with. Before committing to Phase 6/7 architecture, run the
   canonical CUDA→BANG benchmark with Qwen3-Coder-30B-A3B and DeepSeek-Coder-V2- Lite as the LLM backend. If the local
   Worker can't sustain the protocol on the unit-test-pass / accuracy metric, either (a) the protocol needs adaptation
   (shorter prompts, fewer passes per turn), or (b) the methodology requires hosted Claude / GPT-4 as the LLM and Linus
   operates as the SMT-repair + auto-tune substrate around a remote LLM — which is a meaningfully different deployment
   shape.

3. **CUDA kernel zoo as a Phase 7 corpus.** Dan's bioinformatics-and-LLM workflow lives downstream of CUDA-heavy tooling
   (cuDNN, FlashAttention, TensorRT, vLLM CUDA kernels, NVIDIA bio kernels). The QiMeng-Xpiler claim is that one-time
   per-DLS setup amortizes across an unbounded operator zoo. Should Linus build a "Linus kernel zoo" as a Phase 7
   deliverable: a curated set of CUDA / HIP source kernels for operators Dan's workflow needs, with a transcompilation
   pipeline to keep MLX / Metal versions in sync? The setup cost is real (Tenspiler extension, manual-digest, unit-test
   harness); the benefit is substrate flexibility — Linus could automatically inherit any new CUDA kernel that lands in
   the open-source ecosystem.

4. **Neural-symbolic dispatch as a Phase 2/3 orchestration primitive.** The four-stage workflow (annotate → transform →
   localize → repair) is not transcompilation-specific. It is "LLM-emits-sketch / verifier-checks /
   formal-method-repairs" — a general pattern for any LLM-driven task where (a) the LLM is good at sketches, (b) a
   downstream non-LLM actor exists for verification and repair, and (c) the task can be decomposed into limited- scale
   passes. Should this be a first-class Linus orchestration primitive at Phase 2/3, alongside the role-typed work-graph
   (DEC-0050) and the agent-spawner (DEC-0051)? If yes, the v1 substrate could be the QiMeng-Xpiler port from Open
   Question 1 — same code base validates the orchestration primitive _and_ delivers the Metal transcompilation skill.

5. **MCTS-over-pass-sequences vs RL-trained policy — when to switch?** QiMeng-Xpiler uses MCTS (model-free,
   simulation-based search); QiMeng-Kernel uses an RL-trained policy on top of a similar pass set. MCTS is simpler (no
   training infra) and works offline; RL amortizes search over training but requires a reward model. For Linus's Phase 7
   use case (kernel-zoo transcompilation), is the offline MCTS approach sufficient, or does the volume of operators
   justify training a Linus-specific RL policy on the same dataset shape? This is the same question as "QiMeng-GEMM beam
   search vs QiMeng-Kernel RL policy" at the next altitude.

6. **Productivity claim's portability — 96× on MLU is from a high baseline.** The 96× junior-coder productivity
   improvement on CUDA→BANG is partly because BANG C is genuinely hard for humans (limited tooling, sparse
   documentation, unfamiliar SIMD). Apple Silicon Metal is somewhere between CUDA (well-documented) and BANG (less
   well-documented than CUDA). What's the realistic expected productivity multiplier on a CUDA→Metal port for a
   Dan-class engineer (deep CUDA fluency, learning Metal)? 5×? 20×? The answer informs whether the methodology is
   "interesting research" or "bet-the-skill-class" for Phase 7.

7. **Tenspiler dependency cost.** The paper's tensor-instruction-repair handoff to Tenspiler is one of two non-LLM
   components (the other is Z3). Extending Tenspiler for Metal/ANE is "a few lines of code" per the paper, but Tenspiler
   itself is a non-trivial Rosette/Racket dependency. Is the Linus dependency surface willing to absorb a Rosette/Racket
   dep, or should the Phase 6/7 port use an alternative (custom Z3-based synthesis, re-implement Tenspiler-like behavior
   in Python over MLX)? The DEC-0024 supply-chain posture argues for minimum-viable dependency injection here.
