# LLM-Hardware-Design Synthesis — Idea to Reality

_Authored 2026-05-09 on `agent/tier4-5-synthesis-foldins`. Anchor cluster:
[g12-llm-hardware-design](repo-clusters/g12-llm-hardware-design.md). Promoted from
[`docs/specs/qimeng-category-promotion.md`](../specs/qimeng-category-promotion.md). Fifteen paper-notes (the QiMeng
family) plus four cluster repos plus Sketch2Simulation as cross-thread exemplar._

## What this document is

This synthesis covers fifteen paper-notes in the QiMeng family — the most coherent line of work in the Linus reference
corpus on **using LLMs to design real artifacts that downstream non-LLM actors then realize as physical or computational
reality** — together with four cluster repos (CodeV, QiMeng-MuPa, QiMeng-SALV, QiMeng-cpu-v1), the parallel-authored
cluster synthesis at [`g12-llm-hardware-design.md`](repo-clusters/g12-llm-hardware-design.md), and one cross-thread
exemplar — Sketch2Simulation's process-engineering flowsheet generator — that lives outside the QiMeng family but shares
the spine. The thematic spine is **idea → reality**. Dan stated it directly in the seed spec for the category:

> [QiMeng] also relate[s] more to Sketch2Simulation than anything else. That paper and repo is also focused on using
> LLMs to design real physical things. That's the idea I love and want to capture. The ability for Linus to design
> physical things in a practical, highly useful way. I'd love to be able to have Linus produce schematics and designs
> for me, which could be accepted by a manufacturer or engineer or builder or some such, resulting in a real physical
> thing being built. Idea to reality. That's the dream. Having these skills informed by the corpus of knowledge I've
> accumulated should amplify my ability to design and build tangible things, with help from Linus. —
> `qimeng-category-promotion.md` §"Dan's stated framing"

That framing is the load-bearing reason this synthesis exists. The narrower technical category — "LLMs that produce
hardware-description-language code" — is a subset of the broader vision: LLMs producing artifacts that a real downstream
actor accepts and realizes. QiMeng is the cluster's purest exemplar at the hardware-and-kernel end of that continuum.
Sketch2Simulation is the exemplar at the process-engineering end. The corpus's generative-biology and
function-annotation-discovery threads are arguably the biology end, though that connection has not yet been drawn out
explicitly in either of those syntheses. Linus's eventual Phase 7+ skill class — schematics, designs, build instructions
that contractors or fabricators or engineers accept — is the destination this synthesis points at, with the QiMeng
family as the most directly transferable methodology corpus the Linus collection contains.

The papers cluster around the same group: the Yunji Chen / Qi Guo lab at the State Key Lab of Processors, Institute of
Computing Technology, Chinese Academy of Sciences, plus a few coauthors at Cambricon Technologies, ICT, and the
University of Chinese Academy of Sciences. The fifteen-paper / four-repo footprint is coherent enough to be a single
research program rather than a coincidence of topical overlap, and that internal coherence is what makes the
synthesis-level claims durable: the same planner/coder discipline, the same verification-as-oracle pattern, the same
learning-the-domain-from-real-artifacts data philosophy recurs paper after paper, applied to progressively larger
artifact classes. This synthesis traces what is durable across that recurrence and identifies which patterns Linus
should adopt now versus watch versus build toward.

The fifteen paper-notes covered, in approximately the order the synthesis treats them:

- **Foundational microarchitecture work.**
  [Push the Limits — automated CPU design with AI (2306.12456v2)](../paper-notes/2306.12456v2.md) — the existence proof
  that AI can design a working RISC-V CPU from I/O examples;
  [Automated Superscalar Processor Design (0549)](../paper-notes/0549.md) — the State-BSD extension to superscalar
  territory; [QiMeng: Fully Automated HW+SW Design (2506.05007v1)](../paper-notes/2506.05007v1.md) — the integrating
  overview paper.
- **Kernel and tensor-operator codegen.** [QiMeng-GEMM (13337-ZhouQ)](../paper-notes/13337-ZhouQ.md) — meta-prompts +
  beam-search auto-tuning; [QiMeng-TensorOp (2505.06302v1)](../paper-notes/2505.06302v1.md) — tensor operators at the
  hardware-primitive level; [QiMeng-Kernel (2511.20100v1)](../paper-notes/2511.20100v1.md) — Macro-Thinking Micro-Coding
  with planner/coder split; [QiMeng-Attention (2506.12355v1)](../paper-notes/2506.12355v1.md) — DSL-mediated attention
  kernels; [QiMeng-MuPa (2506.11153v2)](../paper-notes/2506.11153v2.md) — sequential-to-parallel translation via mutual
  supervision.
- **Hardware-description language codegen.** [CodeV (2407.10424v5)](../paper-notes/2407.10424v5.md) — multi-level
  summarization for Verilog SFT; [QiMeng-CodeV-R1 (2505.24183v5)](../paper-notes/2505.24183v5.md) — RLVR follow-up with
  automated testbench; [QiMeng-CRUX (2511.20099v4)](../paper-notes/2511.20099v4.md) — CRUX intermediate representation;
  [QiMeng-SALV (2510.19296v4)](../paper-notes/2510.19296v4.md) — signal-aware DPO at sub-module granularity.
- **Compiler and OS adjacencies.** [VEGA (3696443.3708931)](../paper-notes/3696443.3708931.md) — automatic LLVM back-end
  generation; [QiMeng-Xpiler (osdi25-dong)](../paper-notes/osdi25-dong.md) — neural-symbolic tensor-program
  transcompilation; [AutoOS (9546*AutoOS_Make_Your_OS_More*)](../paper-notes/9546_AutoOS_Make_Your_OS_More_.md) —
  LLM-driven Linux kernel configuration tuning.

Plus the four cluster repos — [CodeV](../repo-notes/CodeV.md), [QiMeng-MuPa](../repo-notes/QiMeng-MuPa.md),
[QiMeng-SALV](../repo-notes/QiMeng-SALV.md), [QiMeng-cpu-v1](../repo-notes/QiMeng-cpu-v1.md) — and the cross-thread
exemplar [Sketch2Simulation paper](../paper-notes/2603.24629v1.md) + [repo-note](../repo-notes/Sketch2Simulation.md).

---

## The discipline that recurs

Across the fifteen papers a single discipline keeps reappearing in different guises. The shape: a **planner** step emits
a structured intermediate representation; a **coder** step emits target-language artifacts informed by that
intermediate; a **verifier** — compiler, simulator, hardware testbench, AST analyzer, or boot-and-benchmark loop —
provides a correctness signal that can drive either online search (beam search, MCTS) or offline training (SFT, DPO,
RLVR). The intermediate representation is load-bearing in a specific way: it is the surface area where domain expertise
is deposited so that the LLM does not have to reproduce that expertise from scratch on every call. The verifier is
load-bearing in a different specific way: it is the boundary where probabilistic LLM output meets the deterministic
non-LLM downstream actor, and it is also the only place where the system can hear what reality has to say about the
artifact's correctness.

QiMeng-GEMM is the simplest expression. The planner emits a sequence of canonical primitives (tiling, reordering,
vectorization, layout, pipeline) drawn from a five-element taxonomy. The coder is the same frozen LLM, instantiated with
a meta-prompt template that combines the platform-agnostic primitive description with platform-specific hints retrieved
from a curated repository. The verifier is the compiler-and-benchmark pipeline — clang or nvcc compiles the output, the
benchmark harness measures GFLOPS, and a beam search prunes branches that fail to compile or fall below a performance
threshold. There is no fine-tuning, no RL, no policy network — just a structured prompt substrate plus a search
procedure plus the verifier as oracle. The result on RISC-V CPU and NVIDIA GPU exceeds hand-tuned vendor libraries on
many configurations, with development time compressed from senior-engineer-days to ten minutes. The discipline _works_,
and it works without any of the heavier machinery.

QiMeng-Kernel is QiMeng-GEMM's more sophisticated descendant for the GPU-kernel domain. The planner becomes an explicit
lightweight LLM emitting **macro thinking** actions (semantic optimization choices), the coder becomes a heavier LLM
performing **micro coding** under an RL-trained policy with rule-based reward shaping. The intermediate has bifurcated
into two: a macro-level action space (tiling, fusion, pipelining, reordering — same family as QiMeng-GEMM's primitives,
now a typed RL action space) and a micro-level code segment (the actual CUDA / Triton implementation of each step). The
verifier is the compile-execute-on-KernelBench harness. The result is 100% accuracy on KernelBench, 70% over
general-purpose LLMs, 7.3x over hand-optimized PyTorch Eager. The architecture is more complex than QiMeng-GEMM's, but
the discipline is the same: planner → intermediate → coder → verifier. The MTMC pattern is itself a candidate for a
Linus-internal architectural pattern (`_Seed: DEC-NNNN_` for "Macro-Thinking Micro-Coding pipeline as a Linus
orchestration substrate") — the macro/micro split rhymes with the Maestro/Worker discipline (CLAUDE.md §Maestro/Worker
discipline), and the typed-action / typed-code-segment shape rhymes with the agent-spawner role-as-first-class-type
design (DEC-0050) and AgentReport typing (DEC-0051).

CodeV inverts the data-synthesis direction without changing the discipline. The planner here is implicit — the recipe
relies on a structural insight about the LLM's own asymmetry: GPT-3.5 can summarize Verilog at 64.7% pass@1 but generate
it at only 33.5% pass@1, a fact the authors quantify directly. So the recipe collects 165K syntax-correct Verilog
modules from GitHub, asks GPT-3.5 to **summarize** each one at multiple abstraction levels, and uses the resulting
(description, code) pairs as SFT training data for Qwen2.5-Coder-7B. The verifier in this loop is the iverilog testbench
(functional correctness on VerilogEval / RTLLM) plus the synthesis tool (Yosys for syntax-and-elaboration sanity). The
intermediate is the multi-level summary itself, which doubles as fine-tuning data. The discipline holds: real artifacts
harvested from the real world, summarized into a structured form, paired with the original code as training data,
validated by an automated oracle. This insight — **summarization is the structurally easier task in low-resource code
domains** — is the most directly transferable component of CodeV for any Linus Phase 6 fine-tuning roadmap that targets
a domain where Dan has artifacts but limited public corpora (bioinformatics WDL pipelines, _B. braunii_ assembly
scripts, LanzaTech metagenomics SOPs).

CodeV-R1 takes the next step. The SFT model from CodeV becomes the starting point for a five-stage RLVR pipeline: crawl
→ summarize → distill (CodeV-R1-7B-Distill, the chain-of-thought SFT) → equivalence-check → adaptive-DAPO RL
(CodeV-R1-7B). The verifier is a rule-based testbench generator that uses Yosys for circuit-structure analysis to
extract I/O ports, clock signals, and reset signals, then runs M=100 random stimuli of N=1000 cycles against both the
generated and reference modules with per-signal equivalence checks. The testbench itself is the contribution that
matters: 96.1% fewer false negatives than LLM-generated testbenches, 62.5% more injected errors detected. Without that
oracle the RLVR loop has no signal; with it, a 7B specialist beats 671B DeepSeek-R1 on RTLLM by 8.1 percentage points.
**The oracle is the bottleneck, not the training algorithm** — that is the load-bearing CodeV-R1 lesson, and it
generalizes to every domain Linus might pursue with RLVR (`_Seed: DEC-NNNN_` for "automated-oracle-first as a Linus
fine-tuning convention", a generalization of CLAUDE.md §Smoke-test gates to fine-tuning data).

A fourth instance — for a fourth domain class — is QiMeng-Xpiler. The artifact here is a translated tensor program (CUDA
→ BANG C, CUDA → HIP, etc.), the downstream actor is the platform-specific compile-and-run pipeline, and the discipline
is wrapped around an explicit neural-symbolic split. Eleven transformation passes — sequentialization / parallelization,
memory conversion, (de)tensorization — are each instantiated by the LLM via meta-prompt and then **repaired** by an SMT
solver (Z3) for low-level details (loop bounds, indexing, tensor-intrinsic parameters). The hierarchical auto-tuner —
brute-force intra-pass plus MCTS inter-pass — finds optimal pass parameters and sequences. The verifier is unit-test
execution; failed transformations get pruned by the unit-test wall and earn reward zero in the MCTS reward function. The
neural-symbolic split is more architecturally explicit than in QiMeng-GEMM or QiMeng-Kernel, and it earns its complexity
precisely because tensor-program transcompilation has more low-level detail than GEMM-codegen does — too much for the
LLM to get right one-shot. **The point is not the specific architecture; the point is that the discipline is the same**:
planner emits structured intermediate, coder emits artifact, verifier provides ground truth, search procedure prunes
failed branches.

The recurrence is informative. **The artifact class varies — kernel source, Verilog modules, tensor programs, CPU
microarchitectures, OS configs, compiler back-ends — but the architectural skeleton is constant**. That constancy is
what the Linus orchestration layer should aim to expose as a first-class abstraction: a planner / coder / verifier
contract with the artifact and the intermediate as typed data, the verifier as a swappable oracle, and the search
procedure (beam, MCTS, RL policy) as the strategy that ties them together. The cluster synthesis at
[g12-llm-hardware-design](repo-clusters/g12-llm-hardware-design.md) treats this discipline at the within-family level;
this thematic synthesis treats it as the load-bearing pattern Linus should generalize across domains.

---

## The verification surface

The discipline only works if the verifier is real. Without a high-quality oracle the planner / coder pipeline becomes a
generator-without-grader and the artifact quality degrades to whatever a vanilla LLM-prompt would have produced. The
QiMeng papers are clearer on this point than most ML literature: every paper in the cluster spends substantial
engineering effort on the verifier — and the verifier _is_ the contribution at least as often as the LLM technique is.
Each domain has a different verification surface, and Linus's Phase 6+ ability to apply this discipline to a new domain
turns on whether a verification surface for that domain exists or can be built.

The QiMeng family's verification surfaces, by domain:

- **GEMM and tensor-operator codegen** (QiMeng-GEMM, QiMeng-TensorOp, QiMeng-Attention) — compile-and-benchmark, with
  the compiler (`clang`, `nvcc`, `clang-mlu`, the platform's assembler) as the gatekeeper for correctness and the
  benchmark harness measuring GFLOPS / TFLOPS as the performance oracle. Functional correctness is verified by
  comparison against a reference implementation under random inputs.
- **GPU-kernel codegen** (QiMeng-Kernel) — KernelBench, TritonBench, plus PyTorch Eager as the reference implementation.
  Same compile-and-execute discipline as GEMM, with the additional layer of a kernel-launching harness that measures
  end-to-end performance under realistic workload shapes.
- **Verilog / HDL** (CodeV, CodeV-R1, QiMeng-CRUX, QiMeng-SALV) — Yosys for structural analysis (I/O port extraction,
  bit widths, clock and reset polarity) plus iverilog for simulation, with random-stimulus testbenches running against a
  reference module. The CodeV-R1 testbench generator is the family's most engineered verification surface: a three-phase
  pipeline (circuit-structure analysis → simulation → verification) with dual-stage validation for sequential reset
  signals and exhaustive testing of non-conflicting reset combinations.
- **CPU microarchitecture** (Push the Limits, 0549) — formal verification via property-checking (the QiMeng-cpu-v1 BSD
  pipeline achieves 100% verification pass-rate) plus full-system tests like Linux kernel boot, SPEC CINT 2000,
  Dhrystone, and self-hosting. The verification surface is thicker here because the artifact is a CPU; but the
  discipline still holds — the planner-and-coder produces a Verilog gate-level netlist, the verifier confirms it works,
  and the downstream actor (Synopsys Design Compiler, then a fab — Enlightenment-1 was actually fabbed) accepts the
  artifact.
- **OS configuration** (AutoOS) — boot-and-benchmark on real hardware, with UnixBench and LMbench as the throughput
  oracles. The verification surface here is the most expensive in the cluster (1–2 hours per candidate config because
  compile + boot + bench is genuinely slow), and AutoOS's pre-pruning of boot-fatal options via the LLM's
  observe-prune-propose-act loop is what makes the verification budget tractable.
- **Compiler back-ends** (VEGA) — the LLVM regression suite (16,000+ test cases) plus per-statement confidence scoring
  on the generated code. The verification surface for compiler back-ends is unusually thick — back-end generation can be
  wrong in ways that pass all unit tests but produce miscompiled code at scale — and VEGA's 71.5% / 73.2% / 62.2% pass@1
  across RISC-V / RI5CY / xCORE is bounded by exactly that thickness.
- **Tensor-program transcompilation** (QiMeng-Xpiler) — unit-test execution under the target's runtime (CUDA, HIP, BANG
  C, VNNI), with the SMT solver (Z3) providing a complementary verifier for the low-level transformations the LLM cannot
  get right one-shot.

For Linus on Apple Silicon, the implication is concrete and somewhat sobering. **What verification surfaces are
available locally for which output classes?** Most of the QiMeng-family verifiers are open-source and lift trivially:
iverilog, Yosys, clang, MCTS-with-unit-tests, SMT-via-Z3 — all run on macOS without modification. **The QiMeng-GEMM and
CodeV-R1 testbench harnesses port to Apple Silicon directly**, and an Apple-Silicon kernel-codegen harness is a Phase 6d
/ Phase 7 deliverable rather than a research blocker. This is the load-bearing finding for Phase 6/7 viability: the
Linus operator does not need to build new verification infrastructure to start applying the discipline. The
infrastructure exists; what's missing is the meta-prompt + hint repository for Apple Silicon's specific kernel-class
targets (Metal threadgroup tiles, MLX kernel patterns, ANE-supported primitives).

The non-trivial verification surfaces — production EDA toolchains (Synopsys Design Compiler, Cadence Genus), full-system
hardware simulation, the LLVM regression suite at full scale — are either prohibitively expensive (closed-source EDA
costs five-figure licenses) or simply slow (LLVM regression tests on a single M1 Max take hours per back-end variant).
Linus's realistic envelope is the open-source segment of the toolchain: synthesis to gate-level via Yosys, simulation
via iverilog, transcompilation via Z3-plus-MCTS. This is fine for prototyping and education and weekend curiosity; it
does not close the full RTL → tape-out loop. The "idea → reality" pipeline as currently realized has a closed-source
segment Linus cannot fully internalize — a structural ceiling the synthesis should be honest about.

The Sketch2Simulation cross-thread surfaces a different version of the same constraint: HYSYS itself — the verifier — is
a $20K+/seat Windows-only commercial product Linus will never directly call. The pattern (multi-stage agent
decomposition with an executable-artifact verifier) ports cleanly; the specific verifier does not. Whatever
process-engineering verifier Linus eventually ends up with — perhaps an open-source DWSIM or COFE flowsheet simulator,
perhaps a custom Python-based pseudo-verifier for limited cases — is itself a Phase 7 deliverable, distinct from but
analogous to the Apple-Silicon kernel-codegen harness.

The deeper design rule that emerges: **Linus skill development should start with the verifier**. Before any meta-prompt
authoring, before any fine-tuning, before any RLVR setup, the Phase 7 skill author should answer: what is the
verification surface for this artifact class? If the answer is "we don't have one and would need to build it," that
build-cost is the actual unit of effort being amortized — not the meta-prompt, not the fine-tune, not the search
procedure. CodeV-R1's testbench-generator is its dominant contribution; QiMeng-Xpiler's neural-symbolic pass library is
half SMT-solver tooling; AutoOS's boot-fatal pruning is what makes the boot-and-benchmark verifier tractable in the
first place. The ML technique is interchangeable; the verifier is bespoke per domain.

---

## Self-improvement loops

The cluster's most strategically interesting papers are the ones where the LLM not only produces an artifact but is
**improved by the verification result**. Three architectural patterns recur, with progressive sophistication.

**Pattern 1: Online search with verifier-driven pruning** (QiMeng-GEMM, QiMeng-TensorOp, QiMeng-Xpiler). The LLM is
frozen; the search procedure (beam search, MCTS) explores the artifact space; verifier-failed branches get pruned and
verifier-passed branches advance. There is no model weight update; the "improvement" is per-query, in the search trace,
and it disappears when the query ends. This is the Phase 2/3 candidate Linus should adopt first — it's the cheapest to
build, the search graph is durable as a scratchpad-class artifact (DEC-0030), and prune trails are episodic-memory
candidates (DEC-0029, Layer C). The pattern works across the full cluster spectrum: kernels (QiMeng-GEMM with beam
search), tensor operators (QiMeng-TensorOp with MCTS), tensor-program transcompilation (QiMeng-Xpiler with hierarchical
intra-pass / inter-pass MCTS), and OS configuration (AutoOS with the observe-prune-propose-act-correct state machine).
The auto-tuning beam-search-over-LLM-emitted-code shape is a generic agent-driven program-search primitive
(`_Seed: DEC-NNNN_` for "verifier-pruned tree search as a Linus orchestration primitive"), structurally close to
workgraph's DAG-based dispatch (G7 synthesis,
[`docs/syntheses/repo-clusters/g7-harnesses.md`](repo-clusters/g7-harnesses.md)) extended with a fitness function and
pruning step.

**Pattern 2: Offline distillation from a strong teacher** (CodeV, CodeV-R1-Distill stage). The student LLM is fine-tuned
on (description, code) or (description, chain-of-thought, code) triples generated by a teacher LLM running against
real-world artifacts. The verifier in this loop is the equivalence-checker that filters teacher-generated triples to
those whose regenerated code is functionally equivalent to the original. The improvement is durable — model weights
update — but the cost is bounded: ~78 GPU-hours for the SFT stage in CodeV-R1's case, well below the cost of training
from scratch. The Phase 6 candidate is to apply this pattern to Dan's domain corpora: collect real artifacts (Dan's
career-accumulated _B. braunii_ assembly scripts, LanzaTech metagenomics WDL pipelines, PacBio internal SOPs, biology
protocol notebooks), ask hosted Claude as the teacher to summarize them at multiple abstraction levels, pair (summary,
artifact) tuples as fine-tuning data, and SFT a Worker. The structural insight that **summarization is structurally
easier than generation in low-resource domains** is the durable contribution. The Maestro budget discipline (CLAUDE.md
§Maestro budget discipline) is the right cost frame: pay teacher tokens once for high-value supervised data, not
repeatedly for runtime inference (`_Seed: DEC-NNNN_` for "multi-level summarization data synthesis as a Linus Phase 6
fine-tuning convention").

**Pattern 3: Reinforcement learning with verifiable rewards** (CodeV-R1's RL stage, QiMeng-Kernel's RL-trained
micro-coder, QiMeng-SALV's signal-aware DPO). The student LLM is fine-tuned via RL — DAPO, GRPO, DPO, or signal-aware
DPO — using the verifier as the reward signal. The improvement is durable; the cost is substantial (CodeV-R1's RL stage
was 127 hours on 16 A100s, ~2,032 GPU-hours, on top of the 624-hour SFT stage). The structural insight is twofold: (a)
the oracle is the bottleneck (CodeV-R1's testbench is the dominant contribution, the RLVR loop is the consumer); (b) the
**granularity of the reward signal matters as much as the algorithm**. QiMeng-SALV's signal-aware DPO is the most
striking case in the cluster — by extracting per-signal code segments via AST analysis and computing the DPO loss only
over those segments rather than the whole module, SALV converts partially-correct modules into useful preference pairs
and produces a denser learning signal. A 7B Qwen2.5-Coder fine-tuned with this recipe matches DeepSeek-V3 (671B) on
RTLLM v1.1. The lesson is the same as CodeV-R1's: dense oracles beat sparse ones; signal-level rewards beat module-level
rewards; oracle granularity is a first-class design knob.

For Linus, the pattern-3 question is durable: **does the RLVR-with-automated-oracle pattern translate to a Worker
self-improvement loop on Dan's domain?** The candidate ADR seed (`_Seed: DEC-NNNN_` for "RLVR-with-automated-oracle as
the canonical Linus Worker self-improvement architecture") rests on identifying a Linus-relevant verifiable-oracle
domain. Candidates: pytest-passing Python (easy oracle, broad relevance); ruff-clean Python (easy oracle, narrow
improvement); paper-qa-faithful answers (DEC-0044) (harder oracle, high relevance to Dan's KB workflow); bioinformatics
pipeline correctness — Nextflow / WDL passing small synthetic inputs (high effort to build the oracle, high relevance to
Dan's actual work). The apparent winner on relevance × oracle-buildability is the bioinformatics pipeline-correctness
oracle, but it requires Dan to author small synthetic test inputs for canonical pipeline classes (a Phase 7 oracle-build
investment) before any RLVR can run. CodeV-R1's lesson is that this build investment is the dominant cost; the model
training is the consumer.

Two further compute-side considerations. The total ~2,656 A100-GPU-hours cited in CodeV-R1 is well above what a single
M1 Max can deliver in any reasonable wall time, and adaptive DAPO is a Verilog-specific instantiation of a more general
algorithmic family (PPO, GRPO, DAPO, OREO). For Phase 6 Apple Silicon viability, the realistic Linus path is LoRA-only
RLVR on a 7B Worker with a much smaller corpus, possibly with cloud A100 bursts for occasional full RL runs and on-Mac
LoRA-RLVR for incremental sharpening between bursts. The Phase 6c spike scoping should establish per-step cost on M1 Max
(adaptive-DAPO inner loop on a 7B LoRA-only adapter, a small Linus-relevant corpus) before committing to the
architecture. This is the kind of "measure first" discipline (CLAUDE.md §Measure, don't just estimate) where the
empirical anchor matters more than the architectural enthusiasm.

---

## Sketch2Simulation as cross-thread exemplar

[Sketch2Simulation](../paper-notes/2603.24629v1.md) sits outside the QiMeng family but shares the spine. The artifact is
not a hardware kernel or a Verilog module; it is a process flow diagram converted into an executable Aspen HYSYS
simulation script via the simulator's COM API. The downstream actor is the HYSYS simulator itself (a deterministic,
non-LLM industrial software package that accepts the script and runs it as a real chemical-process simulation). The
discipline maps cleanly: a three-layer pipeline orchestrated as a LangGraph state machine, with parsing and
interpretation in Layer 1, simulation model synthesis in Layer 2, multi-level validation woven through both. The
verifier in this loop is the COM API itself — when the synthesized Python script fails at runtime, the trace is captured
and an LLM patches the script under bounded retries. The discipline holds: planner / coder / verifier, with the verifier
doing real work and the failure-localized fix loop providing the resilience.

The structural contrast with the QiMeng family is informative. QiMeng papers operate in domains where the artifact's
**semantic correctness** is verifiable cheaply (compile-and-bench, simulate, equivalence-check) — the verifier is fast
and the search budget can be large. Sketch2Simulation operates in a domain where the artifact's **executability** is
verifiable cheaply (does the COM script run, does HYSYS converge) but the artifact's **semantic correctness** (does the
process flowsheet actually match the original sketch's intent) requires a second-order check from a domain expert. The
paper does not solve this — they evaluate on F1 of unit / stream / connection / material consistency, which is a
mechanical correctness check, not a design-quality check. **For Phase 7 idea-to-reality skills the Linus orchestration
layer needs to support both verifier classes**: cheap-and-deterministic for the executability check, and expensive-and-
expert for the semantic-correctness check. The QiMeng-family verifiers handle the first; Linus's KnowledgeBase
(DEC-0044, paper-qa) plus Maestro review handle the second. The two-tier verification structure is itself a design seed
(`_Seed: DEC-NNNN_` for "two-tier verification — cheap executability check plus expensive semantic check — as a Phase 7
idea-to-reality skill substrate").

The other architectural insight Sketch2Simulation surfaces — **multi-level validation as a first-class orchestration
primitive** — is the kind of pattern that should fold directly into the Phase 3 agent-spawner design. The ablation study
(C1 removes the descriptor, C2 removes the normalizer, C3 merges the four coding agents into one, C4 disables RAG) shows
that **architectural sensitivity grows with task complexity**: the simple case tolerates degradation, the complex one
doesn't. Each layer earns its keep, and the value of decomposition rises non-linearly with task complexity. For Linus,
this is the empirical case for the agent-spawner exposing validation hooks per stage rather than just an end-of-pipeline
pass/fail. It is also the empirical case for the "execution validation with bounded LLM-fix retry" pattern as a Phase 3
substrate primitive.

The hybrid cloud/local deployment (Gemini 3 Flash for multimodal vision, Qwen 2.5 / 3 Coder local via Ollama for code
synthesis) is an operationally important point that the QiMeng family largely sidesteps. **For Linus's "private local
assistant" stance, the cloud-multimodal layer is exactly the failure mode Phase 4 (Data Sovereignty) needs to design
against**, and the longer-term answer involves either better local multimodal models (a Phase 5+ research direction) or
an opt-in cloud-tier budget that the user explicitly authorizes per task. The Sketch2Simulation paper is honest that
their "multimodal interpretation runs on Gemini 3 Flash because open-weight multimodals underperformed on this task";
Linus's framing should match the honesty while pointing toward a private-by-default trajectory.

---

## Implications for Linus

The fifteen papers, four repos, and one cross-thread exemplar sort cleanly into Linus's phased plan. The mapping below
is the synthesis's strategic claim — what to adopt now versus build toward versus watch.

**Phase 2/3 — orchestration substrate.** The planner / coder / verifier discipline is the load-bearing pattern Linus
should expose as a first-class abstraction in the agent-spawner. The verifier-pruned tree search (beam, MCTS) is a
generic orchestration primitive, generalizing workgraph's DAG-dispatch with a fitness function. The two-tier
verification model from Sketch2Simulation (cheap-executability + expensive-semantic) is the right shape for any Phase 3
skill that produces an executable artifact. Multi-level validation as a per-stage hook in the agent-spawner — informed
by the Sketch2Simulation ablation result that decomposition value rises non-linearly with task complexity — is the right
default. ADR seeds: `_Seed: DEC-NNNN_` for "verifier-pruned tree search as a Linus orchestration primitive" and
`_Seed: DEC-NNNN_` for "Macro-Thinking Micro-Coding pipeline as a Linus orchestration substrate" (the latter generalizes
the QiMeng-Kernel pattern to cross-domain Linus skills, with the macro/micro split typed via DEC-0050 / DEC-0051).

**Phase 6 — Worker fine-tuning conventions.** Three patterns translate to Phase 6 fine-tuning. First, **multi-level
summarization data synthesis** (CodeV) — a low-resource-domain fine-tuning recipe that uses summarization (the
structurally easier task for an LLM) to generate (description, artifact) pairs, applicable to Dan's career corpus.
Second, **automated-oracle-first** (CodeV-R1) — before fine-tuning a Worker on a Dan-task class, build the verification
oracle for that task class first, generalizing CLAUDE.md §Smoke-test gates to the fine-tuning data layer. Third, **RLVR
with adaptive DAPO** as the Worker self-improvement substrate, with an honest caveat that the absolute compute cost is
not free — the realistic Linus path is LoRA-only RLVR on a 7B Worker with a small corpus, plus possibly cloud A100
bursts for occasional full runs. ADR seeds: `_Seed: DEC-NNNN_` for "multi-level summarization data synthesis as a Linus
Phase 6 fine-tuning convention", `_Seed: DEC-NNNN_` for "automated-oracle-first as a Linus fine-tuning convention", and
`_Seed: DEC-NNNN_` for "RLVR-with-automated-oracle as the canonical Linus Worker self-improvement architecture". The
QiMeng-SALV signal-aware DPO finding — that oracle granularity matters as much as the algorithm — is a fourth seed
(`_Seed: DEC-NNNN_` for "fine-grained-reward DPO as the default Linus preference-optimization variant" when sub-artifact
decomposition is feasible).

**Phase 6d — Apple Silicon kernel-codegen.** The minimum-viable Linus port of the QiMeng-GEMM paradigm is a Phase 6d
candidate: hand-curated hint repository for Apple Silicon's unified memory model + Metal threadgroup / thread structure

- ANE primitives where applicable; compile-and-benchmark harness on M1 Max; frozen Worker LLM (Qwen3-Coder, DeepSeek-
  Coder-V2, or hosted Claude during development) playing the prompt-driven coder; auto-tuning beam search per
  QiMeng-GEMM. Smallest meaningful target: a single GEMM variant in MLX or a Metal SGEMM kernel or a flash-attention
  micro-kernel. The Phase 6d streaming-target spec (`docs/specs/phase6d-streaming-target.md`) already implies
  handcrafted Metal kernels somewhere downstream; this is the place where the QiMeng-GEMM discipline lands first. ADR
  seed: `_Seed: DEC-NNNN_` for "QiMeng-GEMM-style hint-repo + auto-tune as the Linus Apple Silicon kernel-codegen
  substrate".

**Phase 7 — idea-to-reality skill class.** The thematic synthesis's headline strategic claim. **Idea-to-reality is a
first-class Phase 7 skill class for Linus**, with QiMeng's hardware/kernel exemplars and Sketch2Simulation's
process-engineering exemplar as the methodology corpus. The skill class is defined by the discipline (planner / coder /
verifier with downstream actor accepting the artifact) and parameterized by domain (kernel, hardware-description
language, process flowsheet, schematic, BOM, build instructions). For Dan specifically, the highest-leverage instances
are the ones where his domain expertise compounds: bioinformatics pipeline generation (Nextflow / WDL); _B. braunii_-
flavored metabolic modeling; metagenomics SOP authoring informed by his LanzaTech career. Less directly relevant but not
zero: HDL skill via CodeV (Linus produces Verilog, accepted by Yosys + Synopsys for hobbyist FPGA / ASIC work);
hand-OS-config tuning via AutoOS (Linus tunes a Linux config for Dan's Linux dev box); multi-platform tensor-program
transcompilation via QiMeng-Xpiler (Linus translates a CUDA kernel to MLX or Metal). The Phase 7 ADR seed is the biggest
commitment in this synthesis: `_Seed: DEC-NNNN_` for "idea-to-reality skill class — Linus skills produce artifacts that
downstream non-LLM actors accept and realize". The Phase 7 ADR should also commit to the Phase 7-specific
skill-development discipline that this synthesis surfaces: **start with the verifier**.

**Phase 8 — longer-horizon ambitions.** The aspirational target — Linus designing physical things that contractors,
fabricators, builders, and engineers accept — sits at Phase 8. The QiMeng-cpu-v1 result is the existence proof that the
loop closes at industrial complexity (an AI-designed RISC-V CPU was actually fabbed as Enlightenment-1). What sits
between Linus and that ambition is (a) Apple Silicon viability for the planner/coder loop on the relevant domain, (b)
verification-surface availability or build-cost for the relevant domain, (c) Dan's domain-expertise depth in the target
— which is highest in biology / biotech / chemistry / bioinformatics, where his career corpus and PhD-level training
compound. The strongest candidate Phase 8 instance is **schematics + designs for tangible biotech things** (bioreactor
designs, fermentation vessel layouts, custom electroporation cuvette geometries, bench-scale biotech instrumentation
BOMs), where the downstream actor is a contract-manufacturing partner or a 3D-printing service or a
benchtop-instrumentation supplier and the verifier is a CAD validation tool plus Dan's expert review. This is far beyond
what any single paper in the cluster proves — but the QiMeng family's existence-proof at the CPU end gives the
trajectory empirical support, and Sketch2Simulation's existence-proof at the process-engineering end shows the pattern
generalizes outside hardware. ADR seed: `_Seed: DEC-NNNN_` for "Phase 8 idea-to-reality target — biotech tangible
things, with Dan's domain expertise as the load-bearing context".

**Cross-cutting — typed structured prediction.** The recurring meta-prompt + hint-repository structure across the
cluster (QiMeng-GEMM, QiMeng-TensorOp, QiMeng-Xpiler, QiMeng-Attention) is itself a typed-structured-prediction
substrate in the sense of CLAUDE.md §S25 (typed structured prediction wrapping rationale, originally surfaced for
biology skills). The shape `{primitive: "tiling", platform: "metal", hint: "...", code: "...", rationale: "..."}`
generalizes the biology shape
`{gene: "BRCA1", predicted_function: "DNA repair", confidence: 0.87, evidence: ["pmid:12345"], rationale: "..."}` to
hardware design specs. Same shape, different domain. The convention extension is worth committing to as part of the
Phase 6 / Phase 7 ADR landing — the typed-prediction-with-rationale shape applies across biology, kernel codegen, and
HDL generation, and it should be the default skill-output shape (`_Seed: DEC-NNNN_` for "typed structured prediction
extended to hardware-design specs").

---

## Tensions and open questions

Several questions remain unresolved at the synthesis level and warrant further discussion.

**The Worker-LLM viability question for the planner step.** The QiMeng-family results are predominantly produced with
strong closed or large-open models — GPT-4o, Claude 3.5 Sonnet, DeepSeek-V3 (236B / 671B), DeepSeek-R1. The smaller-
model results are uneven: Codestral-22B fails the QiMeng-GEMM multi-turn meta-prompt protocol on GPU; CodeV-R1's
distillation only converts the coder, leaving the planner role implicit; QiMeng-Kernel uses a "lightweight LLM" for
macro thinking but does not specify the size. **For Linus's local-only Worker plan with Qwen3 (or Kimi-K2 if the Phase 6
base swap from [`docs/syntheses/native-low-bit-apple-silicon-synthesis.md`](native-low-bit-apple-silicon-synthesis.md)
lands), is the planner step viable on a 7B–32B local model, or does it require a strong teacher (hosted Claude, frozen
during development) to produce the planning trace?** The candidate compromise: planner runs on hosted Claude during
Phase 6 spike development, then is fine-tuned into a local Worker via CodeV-style multi-level summarization once the
meta-prompt + hint repository is stable. This compromise echoes the Maestro budget discipline (hosted Claude as
expensive teacher, local Worker as runtime consumer) and sidesteps the small-Worker-can't-follow-protocol risk. But it
remains an open question worth scoping before any Phase 6 commitment.

**The domain-expertise-required question for usefulness.** The sharpest tension is between Dan's domain depth and the
QiMeng family's domain. **Dan is a biochemist, not a chip designer**; the realistic Linus user is Dan-the-biochemist
plus Dan-the-bioinformatician plus Dan-the-software-engineer. The QiMeng family's domain is exactly the domain Dan does
not specialize in. So the question becomes: **does the LLM-hardware-design pattern transfer to LLM-bioinformatics-design
or LLM-biotech-design or LLM-chemistry-design?** The methodology corpus suggests yes — the discipline (planner / coder /
verifier with downstream actor) is domain-agnostic — but the methodology is silent on what the verifier looks like in
biology / biotech / chemistry. Some candidate verifiers exist (NCBI BLAST for sequence-correctness, AlphaFold-type
folding scores for protein-design, simple in-vitro-assay-correctness predictions, electroporation efficiency scoring),
but none have the cheap-and-deterministic property the QiMeng family enjoys. **A Phase 7 scoping spike — pick one
biology subdomain, identify the cheapest verifier, build a minimum-viable QiMeng-GEMM-style port — is the right first
step**. The answer to "can Dan's biology domain support the discipline" is the gating decision for whether Linus's Phase
7 idea-to-reality skill class lands as a biology-first capability or stays at the kernel-codegen / HDL generation end of
the cluster. The cross-thread to generative-biology and function-annotation-discovery syntheses is open: are there
parallel idea→reality dreams in those threads, and what verifiers do they imply?

**The closed-source verifier ceiling.** A structural ceiling the synthesis should be honest about: the production
end-to-end pipelines for the QiMeng family's strongest results (Synopsys Design Compiler / Cadence Genus for ASIC tape-
out, Aspen HYSYS for chemical-process simulation, Intel MKL / NVIDIA cuBLAS as performance-comparison oracles) are
closed-source and Apple-Silicon-incompatible. **Linus's realistic envelope stops at the open-source segment of the
toolchain**: Yosys + iverilog for HDL, clang / nvcc / mlx for kernels, open-source process simulators where they exist
(DWSIM, COFE — neither evaluated against the cluster's papers), open-source bioinformatics pipelines for Dan's domain.
This ceiling matters for any Phase 7 / Phase 8 commitment that imagines Linus producing artifacts a downstream
manufacturer or fab "actually accepts" — there will be a Linus-produced artifact handoff to a closed-source toolchain
the user (Dan or another operator) runs separately, and Linus does not internalize that segment. This is acceptable; it
should just be explicit in the Phase 7 ADR.

**The compute-cost question for self-improvement.** CodeV-R1's RLVR loop landed in ~2,656 A100-GPU-hours, well above
what an M1 Max can deliver in any reasonable wall time. For Phase 6 / Phase 7 self-improvement to be a Linus capability
rather than a research curiosity, **either the compute cost has to come down (LoRA-only RLVR on small corpora, smaller
inner-loop model, adaptive DAPO speedups) or Linus has to embrace occasional cloud bursts for full RL runs**. The
cloud-burst pattern conflicts with Linus's "private local assistant" framing slightly — the compromise is that the RL
training run is a one-time supervised data generation step, not a runtime requirement, and the resulting fine-tuned LoRA
adapter runs locally afterward. This is the same pattern the Maestro budget discipline already endorses for
hosted-Claude-as-teacher; extending it to occasional cloud-A100-as-trainer is a small additional commitment. The Phase
6c spike (LoRA-RLVR feasibility on M1 Max with adaptive DAPO inner loop) is the gating measurement; the empirical anchor
matters more than the architectural enthusiasm here.

**The "is QiMeng a single research program or many" question.** Across the fifteen papers the same author group recurs:
Yunji Chen, Qi Guo, the State Key Lab of Processors at ICT-CAS plus collaborators. The internal coherence of the family
is striking — the same MTMC-or-equivalent planner/coder discipline, the same verification-as-oracle pattern, the same
data-from-real-artifacts philosophy. **Is this group running a single coherent research agenda toward end-to-end
LLM-driven hardware design (with QiMeng-cpu-v1 / Enlightenment-1 as the existence proof and the rest as methodology
pillars), or is it a productive group whose papers happen to share a discipline?** The answer matters for Linus's
tracking strategy: if it's a single agenda, the corpus has a continuation worth watching closely (a future
QiMeng-Kernel-R1 applying CodeV-R1's RLVR template to GPU-kernel codegen, or a future QiMeng-Photonic for photonic-IC
design); if it's a productive group, individual papers age independently. The honest read: probably the former, with the
QiMeng-X\* naming convention and the internal cross-citations as evidence. Worth an explicit Phase 6+ "watch this group"
commitment in the Linus convention list.

**The biosecurity-tier question for biology extensions.** If the Phase 7 idea-to-reality skill class extends from
hardware/kernel codegen into biology/biotech, the biosecurity-tier-control framework (DEC-0047) becomes load-bearing in
a way it is not for kernel codegen. Schematics for fermentation vessels are bench-tier work; sequence designs that
enable gain-of-function research in pathogens are not. The Phase 7 ADR for the idea-to-reality skill class should
explicitly incorporate the biosecurity-tier framework into the skill's output gating — not as an afterthought, but as a
first-class constraint on the skill's deployment surface. The QiMeng family's hardware-design domain does not exercise
this constraint; the moment Linus extends to biology, it does. This is an open question for the Phase 7 ADR
specifically.

---

## Where this synthesis fits

**Anchor cluster.** [g12-llm-hardware-design](repo-clusters/g12-llm-hardware-design.md) — the parallel-authored cluster
synthesis covering the four QiMeng repos (CodeV, QiMeng-MuPa, QiMeng-SALV, QiMeng-cpu-v1) with Sketch2Simulation as
cross-thread reference exemplar. The cluster synthesis treats the discipline at the within-family level (planner/coder
patterns, verification-surface comparisons, repo-level integration verdicts); this thematic synthesis treats it as the
load-bearing pattern Linus should generalize across domains.

**Robotics as a third physical-realization arm of the idea→reality spine.** The two arms this synthesis treats as
primary — QiMeng's LLM→hardware-description-language→fabricated-chip path and Sketch2Simulation's
LLM→flowsheet→process-engineer path — share a spine with a third arm that lives outside this synthesis's primary scope:
robotics, where a video-or-VLM-derived action policy emits motor commands that a robot's physical hardware realizes as
task completion. The 2026-02-19 NVIDIA GEAR Lab paper drop — [DreamZero](../paper-notes/2602.15922v1.md) (a 14B
autoregressive flow-matching DiT that doubles VLA zero-shot generalization on bimanual manipulation) and
[EgoScale](../paper-notes/2602.16710v1.md) (a flow-matching VLA trained on 20,854 hours of egocentric human video, with
a clean log-linear data-scale-vs-loss law) — are the watch-the-field exemplars. Both inherit from the
[WHAM](../paper-notes/s41586-025-08600-3.md) world-action-model lineage anchored in
[infra-foundations](infra-foundations-synthesis.md), and both are Phase 7/8 watch-only for Linus rather than directly
liftable: the GB200/H100 hardware floor (NVFP4 quantization Blackwell-specific, `flash-attn` with no Metal backend, 14B
at fp16 leaving no activation headroom on M1 Max) closes the door on near-term deployment, and Dan does not currently
operate any robotic embodiment. The reason the cross-thread is worth naming anyway is structural: the idea→reality
discipline this synthesis canonicalizes — planner emits structured intermediate, coder emits artifact, verifier provides
oracle, downstream non-LLM actor realizes the artifact as physical reality — is the same shape regardless of whether the
downstream actor is a fab tool, a process simulator, or a robot. If Linus's Phase 7+ scope ever opens an embodied-actor
or lab-instrument-automation lane (a 3D printer, a microscope stage, a manipulator, benchtop biotech instrumentation),
the world-action-model paradigm is currently the strongest empirical evidence for the right architecture to get there,
and the planner/coder/verifier discipline this synthesis develops is what would carry over.

**Cross-thread links.**

- [native-low-bit-apple-silicon-synthesis](native-low-bit-apple-silicon-synthesis.md) — the Apple Silicon kernel-codegen
  relevance is direct: any Phase 6d Linus-internal MTMC-style pipeline targeting Metal / MLX kernels is the same
  hardware-bound discipline, and the Kimi-K2 / Bonsai / flash-MoE work shape the Phase 6d streaming target this
  synthesis points at.
- [infra-foundations-synthesis](infra-foundations-synthesis.md) — the WHAM / DreamZero / EgoScale world-action-models
  sub-thread is the robotics arm of the idea→reality spine this synthesis canonicalizes; cross-thread is watch-only
  while the GB200/H100 hardware floor holds, but the discipline (planner / coder / verifier with downstream
  physical-actor) is shared.
- [agentic-systems-synthesis](agentic-systems-synthesis.md) — the Sketch2Simulation cross-thread fold-in. The
  multi-agent decomposition and execution-fix-loop patterns are first surfaced there; this synthesis extends them to the
  idea-to-reality lens.
- [generative-biology-synthesis](generative-biology-synthesis.md) — open question on whether parallel idea-to-reality
  dreams exist in biology. The cross-thread is currently a hypothesis; no biological QiMeng-equivalent has been authored
  yet.
- [function-annotation-discovery-synthesis](function-annotation-discovery-synthesis.md) — adjacent to the biology
  cross-thread, where typed structured prediction with rationale (CLAUDE.md S25) already lives.
- [skills-and-practices-synthesis](skills-and-practices-synthesis.md) — the Phase 7 idea-to-reality skill class is a
  Linus-specific skill instantiation that this synthesis nominates; the skills-and-practices synthesis is the natural
  destination for the durable skill-class commitment when the Phase 7 ADR lands.

**Spec home.** [`docs/specs/qimeng-category-promotion.md`](../specs/qimeng-category-promotion.md) — the canonical
statement of the idea-to-reality spine and Dan's strategic intent. This synthesis quotes the framing directly; the spec
is the load-bearing source for the category's strategic rationale and the placeholder for the Phase 7 / Phase 8 ADRs the
synthesis seeds.

**ADR seeds named in this synthesis** (numbers TBD — placeholders signal where commitments could land):

- `_Seed: DEC-NNNN_` — Macro-Thinking Micro-Coding pipeline as a Linus-internal orchestration substrate (Phase 2/3).
- `_Seed: DEC-NNNN_` — Verifier-pruned tree search as a Linus orchestration primitive (Phase 2/3).
- `_Seed: DEC-NNNN_` — Two-tier verification (cheap-executability + expensive-semantic) as a Phase 7 idea-to-reality
  skill substrate.
- `_Seed: DEC-NNNN_` — Multi-level summarization data synthesis as a Phase 6 fine-tuning convention.
- `_Seed: DEC-NNNN_` — Automated-oracle-first as a Phase 6 fine-tuning convention.
- `_Seed: DEC-NNNN_` — RLVR-with-automated-oracle as the canonical Linus Worker self-improvement architecture.
- `_Seed: DEC-NNNN_` — Fine-grained-reward DPO (signal-aware DPO from QiMeng-SALV) as the default Linus
  preference-optimization variant when sub-artifact decomposition is feasible.
- `_Seed: DEC-NNNN_` — QiMeng-GEMM-style hint-repo + auto-tune as the Linus Apple Silicon kernel-codegen substrate
  (Phase 6d).
- `_Seed: DEC-NNNN_` — Idea-to-reality skill class — Linus skills produce artifacts that downstream non-LLM actors
  accept and realize (Phase 7).
- `_Seed: DEC-NNNN_` — Phase 8 idea-to-reality target — biotech tangible things, with Dan's domain expertise as the
  load-bearing context.
- `_Seed: DEC-NNNN_` — Typed structured prediction extended to hardware-design specs (Phase 6 / 7 cross-cutting).

The seed count is large, and that is itself a signal: the QiMeng family is dense with durable architectural commitments
the Linus phased plan should make explicit. Not all eleven seeds will land as ADRs in a single Phase 6 / 7 planning arc;
the priority order is roughly the sequence the Linus phased plan reaches — Phase 2/3 orchestration substrates first,
Phase 6 fine-tuning conventions next, Phase 6d Apple-Silicon kernel-codegen after that, Phase 7 idea-to-reality skill
class as the load-bearing strategic commitment, Phase 8 biotech-tangible-things target as the aspirational horizon. The
Phase 7 ADR is the biggest commitment, and the one this synthesis exists to argue for.

The strategic argument in one paragraph: **The QiMeng family demonstrates, across fifteen papers and four repos, that
LLMs can produce real artifacts — kernels, hardware-description-language modules, CPU microarchitectures, OS configs,
compiler back-ends, tensor-program transcompilations — that real downstream actors (compilers, simulators, fabs, kernel
boot loaders) accept and realize at industrial quality, when the pipeline embeds the planner / coder / verifier
discipline that recurs across the family.** The Sketch2Simulation cross-thread shows the same discipline ports outside
hardware. The strategic implication for Linus is that **idea-to-reality is a real, build-able Phase 7 skill class — not
a speculative aspiration but a methodology corpus with a clear adoption path**, gated only on the per-domain
verification-surface availability (which is open-source and tractable for Apple Silicon kernel codegen, HDL generation,
and tensor-program transcompilation; closed-source-bounded for production EDA / process simulation; build-cost-bounded
for biology / biotech / chemistry). Dan's career corpus and domain depth point at biology / biotech as the
highest-leverage Phase 7 / 8 target, and the verification-surface investment in that domain is the dominant unit of
effort to amortize. **The discipline is real; the corpus is dense; Phase 7 should commit.**

---

## References

### Repo-notes

- [`Bonsai-demo`](../repo-notes/Bonsai-demo.md) — Referenced alongside Kimi-K2 and flash-moe as shaping the Phase 6d
  Apple Silicon streaming target this synthesis points at.
- [`CodeV`](../repo-notes/CodeV.md) — Verilog-generation LLM trained via multi-level summarization SFT on harvested
  GitHub modules; g12 cluster anchor for HDL codegen.
- [`flash-moe`](../repo-notes/flash-moe.md) — Apple Silicon streaming MoE inference reference informing the Phase 6d
  kernel-codegen target.
- [`Kimi-K2`](../repo-notes/Kimi-K2.md) — Candidate Phase 6 base-model swap from the native-low-bit-apple-silicon
  synthesis; cited as a possible local-Worker planner substrate.
- [`paper-qa`](../repo-notes/paper-qa.md) — KB retrieval-and-synthesis engine (DEC-0044) named as a candidate
  Linus-relevant verifiable-oracle domain (paper-qa-faithful answers) and as the expensive-semantic verifier in the
  two-tier verification structure.
- [`QiMeng-MuPa`](../repo-notes/QiMeng-MuPa.md) — Mutual-supervised learning for sequential-to-parallel tensor-program
  translation; g12 cluster repo.
- [`QiMeng-SALV`](../repo-notes/QiMeng-SALV.md) — Signal-aware DPO at sub-module granularity for Verilog generation; g12
  cluster repo demonstrating fine-grained reward granularity.
- [`QiMeng-cpu-v1`](../repo-notes/QiMeng-cpu-v1.md) — Reference implementation of the automated CPU design pipeline
  (Enlightenment-1 RISC-V chip); g12 existence proof at industrial complexity.
- [`Sketch2Simulation`](../repo-notes/Sketch2Simulation.md) — Multi-agent LangGraph pipeline converting process-flow
  sketches into executable Aspen HYSYS simulations; cross-thread idea→reality exemplar outside QiMeng.
- [`workgraph`](../repo-notes/workgraph.md) — G7 harness reference whose DAG-based dispatch the verifier-pruned tree
  search primitive generalizes with a fitness function and pruning step.

### Paper-notes

- [`0549`](../paper-notes/0549.md) — Automated Superscalar Processor Design by Learning Data Dependencies; State-BSD
  extension of the QiMeng automated-CPU line into superscalar territory.
- [`13337-ZhouQ`](../paper-notes/13337-ZhouQ.md) — QiMeng-GEMM: meta-prompts plus beam-search auto-tuning for
  high-performance GEMM kernel generation.
- [`2306.12456v2`](../paper-notes/2306.12456v2.md) — Pushing the Limits of Machine Design: existence proof that AI can
  design a working RISC-V CPU from I/O examples.
- [`2407.10424v5`](../paper-notes/2407.10424v5.md) — CodeV paper: multi-level summarization SFT for Verilog generation;
  the structural-asymmetry insight (summarize easier than generate).
- [`2505.06302v1`](../paper-notes/2505.06302v1.md) — QiMeng-TensorOp: automatically generating high-performance tensor
  operators at the hardware-primitive level.
- [`2505.24183v5`](../paper-notes/2505.24183v5.md) — QiMeng-CodeV-R1: RLVR follow-up to CodeV with automated testbench
  generator as the dominant contribution.
- [`2506.05007v1`](../paper-notes/2506.05007v1.md) — QiMeng: Fully Automated Hardware and Software Design for Processor
  Chips; integrating overview paper for the family.
- [`2506.11153v2`](../paper-notes/2506.11153v2.md) — QiMeng-MuPa paper: mutual-supervised learning for
  sequential-to-parallel translation.
- [`2506.12355v1`](../paper-notes/2506.12355v1.md) — QiMeng-Attention: DSL-mediated attention kernel generation via SOTA
  attention operator.
- [`2510.19296v4`](../paper-notes/2510.19296v4.md) — QiMeng-SALV paper: signal-aware DPO for sub-module reward
  granularity in Verilog.
- [`2511.20099v4`](../paper-notes/2511.20099v4.md) — QiMeng-CRUX: narrowing the gap between natural language and Verilog
  via a CRUX intermediate representation.
- [`2511.20100v1`](../paper-notes/2511.20100v1.md) — QiMeng-Kernel: Macro-Thinking Micro-Coding paradigm for LLM-based
  GPU-kernel generation.
- [`2602.15922v1`](../paper-notes/2602.15922v1.md) — DreamZero: 14B autoregressive flow-matching DiT doubling VLA
  zero-shot generalization on bimanual manipulation (robotics arm of idea→reality).
- [`2602.16710v1`](../paper-notes/2602.16710v1.md) — EgoScale: flow-matching VLA trained on 20,854 hours of egocentric
  human video; clean data-scale-vs-loss law.
- [`2603.24629v1`](../paper-notes/2603.24629v1.md) — Sketch2Simulation paper: automating flowsheet generation via
  multi-agent decomposition with COM-API verifier.
- [`3696443.3708931`](../paper-notes/3696443.3708931.md) — VEGA: automatic LLVM back-end generation using a pre-trained
  language model with per-statement confidence scoring.
- [`9546_AutoOS_Make_Your_OS_More_`](../paper-notes/9546_AutoOS_Make_Your_OS_More_.md) — AutoOS: LLM-driven Linux kernel
  configuration tuning via observe-prune-propose-act loop.
- [`osdi25-dong`](../paper-notes/osdi25-dong.md) — QiMeng-Xpiler: transcompiling tensor programs across deep learning
  systems via neural-symbolic passes plus Z3.
- [`s41586-025-08600-3`](../paper-notes/s41586-025-08600-3.md) — WHAM: World and Human Action Models towards gameplay
  ideation; foundational lineage for the DreamZero/EgoScale robotics arm.
