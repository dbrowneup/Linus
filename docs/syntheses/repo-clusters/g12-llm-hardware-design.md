# Group 12 Synthesis — LLM-Hardware-Design (QiMeng family)

**Authored 2026-05-09.** **Repos:** [`CodeV`](../../repo-notes/CodeV.md), [`QiMeng-MuPa`](../../repo-notes/QiMeng-MuPa.md),
[`QiMeng-SALV`](../../repo-notes/QiMeng-SALV.md), [`QiMeng-cpu-v1`](../../repo-notes/QiMeng-cpu-v1.md) (4 total).
**Cross-thread reference (NOT a member):** [`Sketch2Simulation`](../../repo-notes/Sketch2Simulation.md) — process-engineering
arm of the same idea-to-reality dream, lives in [g8-sci-agents](g8-sci-agents.md).
**Verdicts:** Study × 4 (with QiMeng-cpu-v1 carrying a "Watch (Phase 6+)" modifier per its repo-note; high prior on later
**Adapt** for QiMeng-SALV if Linus grows an HDL skill class).

---

## What this document is

g12 is the new repo-cluster home for the QiMeng family of LLM-driven hardware-design artifacts. Four repos sit in the
cluster — CodeV (language design: Verilog generation via multi-level summarization, with the CodeV-R1 RLVR follow-up
sharing the same release), QiMeng-MuPa (kernel translation: sequential-to-parallel C↔CUDA via Mutual-Supervised
Learning), QiMeng-SALV (signal-aware Verilog DPO: substructure-level preference optimization), and QiMeng-cpu-v1
(microarchitecture: behavioral synthesis of a tape-out-grade RISC-V CPU from I/O examples). The cluster's strategic
anchor is [`docs/specs/qimeng-category-promotion.md`](../../specs/qimeng-category-promotion.md), which records Dan's
**idea → reality** framing — LLMs producing artifacts that downstream non-LLM actors (compilers, fabs, manufacturers,
contractors) accept and realize. Sketch2Simulation in g8 is cited here as the process-engineering exemplar of the same
spine, but is not a g12 member — its substrate is multi-agent HYSYS-flowsheet generation, not hardware. The forthcoming
thematic synthesis [`llm-hardware-design-synthesis.md`](../llm-hardware-design-synthesis.md) (Task 5.2 of the parent
[context fold-in spec](../../specs/2026-05-09-context-foldin-fanout.md)) generalizes the spine across both clusters and
should be read alongside this document.

This synthesis is not a re-summary of the four repo-notes. The per-file notes carry that load. What this document does
is name what the four repos collectively point at, surface the recurring patterns of planner/coder discipline + automated
oracle + verifiable rewards that distinguish the QiMeng family from other LLM-codegen work in the corpus, position the
cluster as the corpus's most plausible self-improving substrate, and extract phase-tagged implications that follow from
treating the four repos as a unit rather than four independent decisions. Five additional QiMeng paper-notes already in
corpus ([`0549.md`](../../paper-notes/0549.md), [`2306.12456v2.md`](../../paper-notes/2306.12456v2.md),
[`2506.05007v1.md`](../../paper-notes/2506.05007v1.md), [`2511.20099v4.md`](../../paper-notes/2511.20099v4.md),
[`2511.20100v1.md`](../../paper-notes/2511.20100v1.md)) anchor the family's microarchitecture / kernel / overview
threads, plus six new paper-notes from the 2026-05-09 fold-in (QiMeng-GEMM, QiMeng-TensorOp, QiMeng-Attention, VEGA,
AutoOS, QiMeng-Xpiler) extending the reach to compiler back-ends, OS-config tuning, and tensor-program transcompilation.
The cluster's repo-side surface is intentionally narrower than its paper-side surface — the methods are released as code
selectively, the methodology is published broadly. That asymmetry shapes how the cluster earns its keep.

---

## The unifying thesis

The four repos are four bets on the same underlying claim: **LLMs are now strong enough to produce artifacts that
deterministic downstream actors will accept, provided the loss target is shaped by an automated oracle running on the
real downstream tooling**. CodeV's oracle is iverilog functional simulation against real testbenches; CodeV-R1's oracle
is a Yosys-derived rule-based testbench that the RLVR loop spins on. QiMeng-MuPa's oracle is paired CPU/GPU execution
on real silicon comparing outputs across the language gap. QiMeng-SALV's oracle is per-signal differential simulation
against a reference module via iverilog. QiMeng-cpu-v1's oracle is "did the BSD-derived Boolean logic produce the same
truth table as the I/O specification, and did the resulting netlist boot Linux on a fabricated chip." The repos disagree
on almost everything except the discipline: oracles are real, executable, and on the path the artifact would have to
take in production anyway. None of the four uses an LLM-as-judge. None uses a learned reward model. Each uses the
genuine downstream tool (compiler, simulator, fab) as the verification surface, and each shapes its training data
distribution to that oracle's signal.

The thesis emerging from holding the four together is that **the oracle is the unit of effort being amortized, not the
training algorithm**. CodeV-R1's headline contribution by impact is the rule-based testbench generator (96.1% false-
negative reduction over LLM-generated testbenches, 62.5% more injected errors detected); the adaptive-DAPO speedup is
secondary. SALV's headline is the AST-to-token-span signal extractor that lets DPO reward only the correct sub-spans;
the loss customization itself is conceptually simple. MuPa's headline is the Co-verify execution-comparison harness;
the back-translation Co-evolve loop is conventional fine-tuning on top. QiMeng-cpu-v1's headline is "I/O examples scale
to industrial complexity at 18,260 outputs producing a tape-out-ready chip"; the BSD algorithm itself is specialized
graph search. Across the four, the LLM is the cheap surface; the oracle is the load-bearing engineering work. This
reframing matters for Linus: building a verifiable oracle for a Dan-task class is the prerequisite that gates every
downstream fine-tuning ambition, and the oracle's quality bounds the upside of any subsequent RL.

For Linus this means the cluster is the corpus's most direct blueprint for **self-improving Workers**. The hosted
Maestro can stay the architect; a local Worker can improve itself on Dan-task classes where Linus has built a reliable
oracle (pytest-passing Python, ruff-clean Python, paper-qa-faithful answers, smoke-test-passing pipelines) using the
QiMeng family's discipline. The cluster does not show that this scales beyond 7B-class specialists on narrow domains —
the published headline results are all in that envelope — but it is the cleanest existing demonstration that the
discipline works at all, on domains with a Linus-comparable shape (data-scarce, structurally decomposable, with hard
correctness requirements). The thematic synthesis carries the cross-domain generalization argument; this cluster
synthesis carries the within-cluster pattern catalog.

---

## Within-cluster patterns

Five patterns recur across the four repos and constitute the cluster's reusable engineering vocabulary. Each is
introduced once with its strongest cluster exemplar, then surfaced briefly where the other repos instantiate it.

**Multi-level summarization data synthesis (CodeV).** The CodeV recipe — collect real-world artifacts, ask a strong
teacher LLM to summarize each at multiple abstraction levels (fine-grained implementation description + high-level
functional spec), pair (summary, real artifact) as training data, fine-tune on the pair set — exploits the empirical
asymmetry that LLMs are better at describing existing code than at generating new code in low-resource domains. CodeV's
Table I shows GPT-3.5 hitting 64.7% pass@1 when asked to summarize Verilog and only 33.5% when asked to generate it;
the recipe's leverage is direct. The recipe is structurally domain-agnostic and generalizes to any low-resource code
domain Dan might care about — bioinformatics WDL pipelines, KEGG SBML metabolic models, MaxQuant proteomics configs,
LanzaTech metagenomics SOPs, _Botryococcus_-flavored assembly scripts — provided Dan has a clean real-artifact corpus
to bootstrap from. Linus convention candidate: when Phase 6 fine-tuning targets a new domain, the data-synthesis loop
defaults to multi-level summarization rather than direct generation. SALV's training corpus descends from this same
135k cleaned-CodeV seed; the multi-level-summarization data synthesis is the family's foundational data-curation step.
Maps to Phase 6 ADR seed candidate per [`qimeng-category-promotion.md`](../../specs/qimeng-category-promotion.md)
§"What remains to be done" task 7.

**RLVR loop with rule-based testbench (CodeV-R1, paired with CodeV in `repos/CodeV`).** RLVR's structural blocker for
hardware-description code is the verification oracle: LLM-generated testbenches fail to handle reset signals, clock
polarities, and sequential state machines, and module-level testing is too coarse for fine-grained reward. CodeV-R1's
answer is a five-stage pipeline (code-to-NL via DeepSeek-V3, NL-to-code via DeepSeek-R1 with chain-of-thought, SFT on
the filtered triples, equivalence checking via the rule-based testbench, RLVR with adaptive DAPO on the filtered ~3.1K
corpus) that achieves a 7B-parameter model surpassing 671B DeepSeek-R1 on RTLLM v1.1 by 8.1 percentage points at a
total cost of ~2,656 A100-GPU-hours. The RLVR template generalizes far beyond Verilog: any task with an automated
verifiable oracle and a low-resource data corpus is a candidate. For Linus the four-component pattern (automated
oracle + round-trip data synthesis + distill-then-RL + adaptive DAPO) is the load-bearing self-improvement candidate
ADR seed. Adaptive DAPO is independently a generic RLVR speedup (~1.25× wall-clock at no architectural cost), worth
adopting wherever a dynamic-sampling RL algorithm is in use. SALV's signal-aware DPO is the substructure-level
refinement of the same preference-optimization-for-Verilog thread: CodeV-R1's rewards stop at "the whole module
passes simulation"; SALV pushes one structural level deeper with per-signal correctness extracted via Yosys AST.

**Mutual-Supervised Learning / Co-verify + Co-evolve (QiMeng-MuPa).** The MuPa shape is two coupled abilities — a
Translator that converts sequential→parallel code in both directions, and a Tester that generates unit tests for both
languages — bootstrapped from monolingual corpora through alternating Co-verify (run both source and target on real
CPU/GPU and discard triplets whose outputs disagree) and Co-evolve (fine-tune both models on the verified triplets via
back-translation) steps. After four iterations the loop converges to 10,563 verified (C, CUDA, 5 unit tests) triplets
and a fine-tuned Qwen2.5-Coder-7B Translator that closes the Pass@1 gap to GPT-4.1 / DeepSeek-R1 from ~30 percentage
points to ~2. The Co-verify step is structurally a generic two-agent quorum-by-execution pattern: Worker-A emits
artifact, Worker-B emits validator/test, the orchestrator runs both on the real downstream tooling and accepts the
joint output only on cross-validation. Stripped of C↔CUDA specifics, this is a Phase 2/3 orchestration primitive
candidate alongside the workgraph DAG-dispatch pattern from [g7-harnesses](g7-harnesses.md) and the role-typed
agent-spawner pattern (DEC-0050, DEC-0051). The MLX/Metal port is the cluster's cleanest Apple-Silicon Phase 7/8
target: a MuPa-on-MLX adaptation would replace the LocalCompiler's CUDA branch with a Metal compiler invocation, swap
the BabelTower CUDA monolingual corpus for a curated MLX/Metal-kernel corpus, and use the same Translator/Tester
inference scaffold with mlx-lm batched inference standing in for vLLM. The infrastructure pattern lifts directly; the
hand-engineered CUDA Kernel Wrapper template is the non-trivial domain-knowledge asset that needs an MLX-flavored
analog before any loop can run, comparable in shape to QiMeng-GEMM's hint repository.

**Substructure-aware preference optimization (QiMeng-SALV).** SALV's load-bearing engineering work is the AST-to-token-
span mapper (the 606-line `parser.py` that turns a Yosys AST output into structured signal-dependency trees and
backward-traverses from each output signal's leaf to extract the AST subtree's covered code lines), paired with a
LLaMA-Factory fork that customizes DPO loss to compute token probabilities only over the contrast signals' code
segments. The empirical payoff is striking: training only on whole-module-correct samples is _better_ than training
only on partial-correct samples without filtering (mixing partial-correct without filtering hurts the model); but with
SALV's signal-level filtering, both partial-only and mixed-data settings beat complete-only, and the full mix beats any
subset (62.6% vs 57.4% pass@1 on RTLLM v1.1). The recipe generalizes far beyond Verilog: any domain where outputs are
structurally decomposable, per-substructure correctness oracles exist, and SFT quality is heterogeneous. Function-aware
DPO for Python (per-function pytest oracle, function-body token spans), field-aware DPO for typed-structured-prediction
outputs (per-field validators per CLAUDE.md S25), and section-aware DPO for multi-section reports are direct analogs.
Linus convention candidates: (a) **selective-objective** as a first-class abstraction in the Phase 6 training-recipe
library (`(token_mask, objective_fn) → masked_objective_fn`, applicable to SFT/DPO/GRPO/PPO uniformly); (b) **always
filter heterogeneous-quality data at the substructure level when an oracle exists** as a Phase 6 fine-tuning convention
worth codifying in CLAUDE.md.

**Behavioral synthesis from I/O examples (QiMeng-cpu-v1).** The BSD (Binary Speculative Diagram) learner synthesizes
18,260 single-output Boolean functions from black-box I/O behavioral specifications without formal Verilog code,
hierarchically partitioned into 10 clusters of 1,826 tasks each — the partitioning enables 5-hour wall-clock execution
on a 68-server HPC cluster against a sequential ~3,500-CPU-hour cost. The fabricated chip (Enlightenment-1, the world's
first AI-designed CPU) boots Linux, runs SPEC CINT 2000, and runs Dhrystone — meaningful physical-realization beyond
testbench correctness. The BSD algorithm itself is specialized to Boolean function synthesis and is not directly
transferable to LLM fine-tuning, but the **broader lesson that I/O-example-driven learning scales to industrial
complexity (18k outputs, successful tape-out)** is the cluster's strongest evidence that the idea-to-reality discipline
works at production scale, not just on benchmarks. For Linus this anchors the Phase 6 hypothesis that learning from
Dan's task-execution logs (input artifact, expected output, oracle pass/fail) can produce meaningful fine-tuning
signals; the parallelization strategy (10-cluster partitioning) is a reusable pattern for Phase 6 hyperparameter sweeps
or fine-tune fan-outs. The "self-designing" demonstration (the chip improves its own design via I/O feedback) is a
Phase 7 idea worth shelving for revisit during Skills & Autonomy Graduation.

A sixth pattern — **macro-thinking / micro-coding (MTMC) planner-coder split** — runs through the cluster's paper-side
material via [`2511.20100v1.md`](../../paper-notes/2511.20100v1.md) (QiMeng-Kernel) but is not realized in any of the
four cluster repos. MTMC decouples GPU kernel generation into a lightweight planner LLM emitting semantic optimization
actions (tiling, fusion, pipelining, reordering) and a heavier coder LLM realizing them step-by-step under RL-trained
policy with rule-based reward shaping. The planner/coder split rhymes directly with Linus's Maestro/Worker discipline
(CLAUDE.md §Maestro/Worker) and with the role-typed agent-spawner shape (DEC-0050, DEC-0051). MTMC + SALV combine
naturally into a Worker self-improvement stack: MTMC's macro outputs are the decomposition input to SALV's per-
substructure DPO, with the planner producing the structural skeleton and the coder filling spans whose correctness is
verified independently. The cluster synthesis surfaces this as a candidate Phase 6/7 architecture; the thematic
synthesis (Task 5.2) carries the cross-domain reasoning.

---

## The four repos in detail

This section narrows from cluster-level patterns to per-repo cluster-relevance. The full architecture summaries live
in the per-repo notes.

### CodeV (`IPRC-DIP/CodeV`) — language design

The shared release for two QiMeng papers ([CodeV (2407.10424v5)](../../paper-notes/2407.10424v5.md) and
[CodeV-R1 (2505.24183v5)](../../paper-notes/2505.24183v5.md)) is the cluster's **language-design** anchor. The
planner/coder discipline is implicit rather than explicit — CodeV is single-stage SFT, CodeV-R1 adds a distill-then-RL
phase with explicit chain-of-thought between `<think>` tags before code in `<answer>` tags — but the verification
discipline is sharp: VerilogEval and RTLLM testbenches are real iverilog simulations, the rule-based testbench
generator in CodeV-R1 is a Yosys-derived oracle that runs at 15 instances/second on 32-way parallelization, and the
RLVR loop's reward signal is binary on (correctly-formatted, testbench-passing). Local-replication conditions on Apple
Silicon: training reproduction is **not feasible** (CUDA 12.x hard-required across torch / vLLM / flash-attn / DeepSpeed
/ accelerate); inference deployment via the published HuggingFace checkpoints (`yang-z/CodeV-*` and `yang-z/CodeV-R1-*`)
is straightforward through Ollama or mlx-lm with a one-time GGUF or MLX conversion. The 7B-class checkpoints fit
comfortably in M1 Max RAM at int4 (~4 GB each); CodeV-R1's reasoning trace requires KV-cache continuity discipline at
runtime per DEC-0036 (silent CoT truncation invalidates the model's reasoning behavior). Whether Verilog generation is
ever a Dan-skill is an open question; the artifacts are cheap to keep on hand for occasional use and as a probe model
for studying RLVR-trained reasoning behavior on a domain with a well-defined oracle.

### QiMeng-MuPa (`kcxain/QiMeng-MuPa`) — kernel translation

The cluster's **kernel-translation** anchor and Linus's most-portable Apple-Silicon analog candidate. The planner/coder
discipline is genuinely two-agent: Translator emits artifact, Tester emits unit tests, both share weights across
languages and directions, and the Co-verify execution oracle filters joint outputs. Verification is real CPU/GPU
execution on actual hardware. Local-replication conditions on Apple Silicon: the published code is **NVIDIA-CUDA-locked
end-to-end** (`pyproject.toml` declares `nvidia-cuda-nvcc-cu12` and `vllm`; `unit_test/compiler.py` runs `nvcc`
directly), so direct execution of the released code on M1 Max is not viable; the methodology lifts cleanly. The most
exciting Linus-specific read is Phase 7/8 MuPa-on-MLX: substitute the LocalCompiler's CUDA branch with an MLX/Metal
compiler invocation, replace the CUDA Kernel Wrapper prompt template with a Metal threadgroup + buffer-binding wrapper,
swap the BabelTower CUDA monolingual corpus for a curated MLX/Metal-kernel monolingual corpus (Phase 7 effort
comparable in shape to QiMeng-GEMM's hint repository), and use the same Translator/Tester inference scaffold with
mlx-lm batched inference standing in for vLLM. The released 10,563-triplet (C, CUDA, 5-tests) dataset is a Phase 6
fine-tune candidate **independent** of the Apple-Silicon-port question; ingesting it as KB records (per the
model-prediction-edge-class spec, DEC-0048) gives downstream Linus skills high-quality exemplars without re-running the
loop. The Qwen3-0.6B Translator's Pass@1 of 84.44 on C→CUDA is striking — a sub-billion-parameter parallelizer at
frontier-comparable performance is a useful datapoint for the inference-cost side of the Linus self-improvement
question, and the model is small enough to run two simultaneous instances on M1 Max for inference-time Co-verify.

### QiMeng-SALV (`QiMeng-IPRC/QiMeng-SALV`) — signal-aware DPO

The cluster's **substructure-aware preference optimization** anchor and the closest published precedent for fine-tuning
a Worker to produce structured outputs where each substructure has its own correctness oracle. The planner/coder
discipline is implicit (the SFT model emits whole modules; SALV's contribution is in the post-training stage, not in
the generation architecture); the verification discipline is intricate, with Yosys-AST-based code-segment extraction
producing the per-signal token spans that the customized LLaMA-Factory loss restricts DPO computation to. Local-
replication conditions on Apple Silicon: this is the cluster's most tractable end-to-end reproduction target. A 7B base
+ 350k preference pairs + ~7000 LoRA steps fits comfortably within M1 Max's 32 GB unified memory; the
iverilog/Yosys/macOS toolchain is a Homebrew install. The simulation throughput (0.65 ms/sample at 60-core parallelism
in the paper) drops to ~3.9 ms/sample at M1 Max's 10 cores, still negligible vs forward/backward training cost. The
main port cost is the LLaMA-Factory selective-loss customization to MLX-LM-FT (or running PyTorch + MPS, which the
upstream framework supports but at unmeasured throughput). Probable canary for a Linus-internal MTMC reproduction or
Phase 6/7 RL-fine-tune validation: SALV's bounded scope, public model + dataset, well-documented recipe make it the
cluster's strongest candidate for "first end-to-end RL fine-tune Linus reproduces on Apple Silicon." The byproduct — a
working substructure-aware-DPO implementation in MLX-LM-FT — is reusable far beyond Verilog.

### QiMeng-cpu-v1 (`QiMeng-OSINT/QiMeng-cpu-v1`) — microarchitecture

The cluster's **microarchitecture** anchor and the only repo whose downstream actor is a literal silicon fab. The
planner/coder discipline is replaced by hierarchical task partitioning (10 clusters of 1,826 tasks each); the
verification discipline is I/O-example-driven Boolean Distance comparison plus eventual physical realization (Linux
boot, SPEC CINT 2000, Dhrystone on the fabricated Enlightenment-1 chip). Local-replication conditions on Apple Silicon:
the algorithm is **deterministic and resource-constrained, not GPU/Metal-accelerated** — sequential execution is
~3,500 CPU-hours, parallel execution requires a 68-server cluster with Slurm. Single-machine M1 Max execution is
tractable but slow; full CPU synthesis is not a near-term Linus deliverable. The cluster placement is methodological
rather than artifactual: QiMeng-cpu-v1 is the family's strongest evidence that the **idea-to-reality discipline works
at industrial complexity**, with a tape-out-grade chip as the artifact. For Linus this is the cluster's most
**actively useful** repo for understanding behavioral-synthesis methodology — the partitioning strategy, the Boolean
Distance metric for measuring function similarity (a candidate distance metric for Linus behaviors at fine-tune time),
and the I/O-example-driven learning paradigm (philosophically aligned with Linus's goal of learning from Dan's
behavior logs). The repo is the cluster's anchor for the "LLMs design real hardware that gets fabricated" claim that
distinguishes the QiMeng family from any other LLM-codegen work in the corpus.

---

## Sketch2Simulation as cross-thread reference

[Sketch2Simulation](../../repo-notes/Sketch2Simulation.md) (paper [`2603.24629v1.md`](../../paper-notes/2603.24629v1.md))
is the **process-engineering arm of the same idea-to-reality dream** and is cited here as a cross-thread reference, not
as a g12 cluster member. The Sketch2Simulation pipeline converts hand-drawn process flow diagrams into executable
Aspen HYSYS Python scripts through a nine-stage multi-agent LangGraph pipeline; the artifact the LLM produces is
HYSYS-COM-API Python, the downstream actor is the Aspen HYSYS simulator, and the oracle is execution success against
proprietary template files plus per-stage validation gates. The structural shape — unstructured input → typed
intermediate representation → multi-agent code synthesis → execution validation with bounded fix-loop — rhymes
directly with the QiMeng cluster's idea-to-reality spine, but the substrate is multi-agent process-flowsheet generation
rather than single-domain hardware codegen. That substrate difference is why Sketch2Simulation lives in
[g8-sci-agents](g8-sci-agents.md) (FutureHouse stack + adjacents) rather than g12: its kin are scientific-reasoning
agents with multi-agent orchestration as the load-bearing pattern, not LLM-driven hardware-design workflows with
verifiable-rewards training as the load-bearing pattern. The cross-thread cite matters because the **forthcoming
thematic synthesis** [`llm-hardware-design-synthesis.md`](../llm-hardware-design-synthesis.md) (Task 5.2) is the
durable home for the cross-domain idea-to-reality argument; this cluster synthesis stays focused on within-cluster
patterns, with Sketch2Simulation surfaced as the bridge to the broader thematic surface. When Linus eventually grows a
Phase 7 idea-to-reality skill class — process flowsheets a contractor accepts, expression-vector designs a wet lab
accepts, BOMs a manufacturer accepts — the thematic synthesis carries the multi-domain framing; this cluster synthesis
carries the QiMeng-side technical pattern catalog.

---

## Verdicts

All four repos earn **Study** with caveats:

- **CodeV** — Study. The recipes (multi-level summarization, Chat-FIM-Tag SFT, adaptive DAPO, round-trip data
  synthesis) are domain-portable; the published checkpoints are MIT-licensed, small (~4 GB int4), and trivially hosted
  via Ollama or mlx-lm. The CodeV-R1 RLVR loop is the cluster's cleanest Worker-self-improvement-substrate candidate
  ADR seed.
- **QiMeng-MuPa** — Study. The MuSL framework is the most directly relevant substrate the QiMeng family offers for an
  Apple-Silicon kernel-codegen Linus skill, but the published code is so CUDA-tied that direct adoption is off the
  table; the right Linus stance is to treat this as the canonical reference implementation of the Co-verify / Co-evolve
  loop and lift the architectural pattern into a Linus-native MuPa-on-MLX skill in Phase 7/8.
- **QiMeng-SALV** — Study, with a high prior on later **Adapt** if Linus needs Verilog or HDL skills as a Phase 7+
  skill class for any hardware-coupled experiment. The selective-DPO-loss customization is the highest-leverage
  reusable artifact in the cluster; the recipe ports cleanly to function-aware DPO for Python and field-aware DPO for
  typed-structured-prediction outputs.
- **QiMeng-cpu-v1** — Watch (Phase 6+) per the repo-note. Not for direct adoption, but conceptually load-bearing for
  Phase 6 (the I/O-example-driven learning paradigm aligns with learning from Dan's task-execution logs) and Phase 7
  (the self-designing demonstration is intriguing for Skills & Autonomy Graduation).

**Canary for a Linus-internal MTMC reproduction.** If Phase 7 commits to a planner/coder Worker self-improvement loop
on Apple Silicon, **QiMeng-SALV is the canary**. Three reasons. First, the bounded scope (7B base, 350k pairs, ~7000
LoRA steps, public model + dataset) makes it tractable on M1 Max in a single workstation-week of training time after
the LLaMA-Factory→MLX-LM-FT loss port lands. Second, the methodology generalizes broadly (substructure-aware preference
optimization is reusable across the Phase 6 fine-tuning lane); a successful Apple-Silicon reproduction validates the
selective-objective abstraction for SFT/DPO/GRPO/PPO simultaneously. Third, the verification toolchain (iverilog +
Yosys via Homebrew) is cleanly available on macOS without proprietary EDA dependencies, sidestepping the closed-source
synthesis-toolchain problem that bounds CodeV / CodeV-R1's idea-to-reality reach. CodeV-R1 is the **second-best canary
candidate** if a more research-grade RLVR loop is wanted earlier, but its compute cost (~2,656 A100-GPU-hours total)
puts a full reproduction beyond M1 Max scope; LoRA-only RLVR on a 7B Worker with a smaller corpus is the realistic
bound. MuPa-on-MLX is the **most exciting** but **most prerequisite-heavy** target — the Metal kernel wrapper template
is the gating artifact, and the throughput question (Metal kernel launch latency vs CUDA's microsecond launch) needs
an empirical measurement before architectural commitment.

---

## Open questions

The cluster surfaces six cluster-level open questions that the per-repo notes touch but cannot resolve in isolation.
The thematic synthesis (Task 5.2) carries cross-cluster framings of the same questions; these are scoped to within-g12
decisions.

**1. Which planner/coder discipline transfers cleanest to Apple Silicon kernel codegen (MLX/Metal)?** Three candidates
in the cluster: CodeV-R1's distill-then-RL (full RLVR on a 7B base; high upside, high prerequisite-cost),
QiMeng-MuPa's Mutual-Supervised Learning (Translator + Tester pair; strong fit for the C/Python ↔ MLX target but
needs the Metal kernel wrapper authored first), and SALV's signal-aware DPO (substructure-level preference
optimization; cleanest reproduction target but requires a paired-reference dataset rather than a pytest-style oracle).
A Phase 6c spike measuring per-step throughput on each pattern against an MLX kernel target would resolve the
ordering. The MTMC pattern from QiMeng-Kernel ([`2511.20100v1.md`](../../paper-notes/2511.20100v1.md)) is the natural
combinatorial answer (planner from MTMC + per-substructure preference from SALV + execution oracle from MuPa) but
adds integration cost.

**2. Is the Worker-LLM viability for the planner step low enough to make this a Phase 6/7 reality?** CodeV-R1's
planner is implicit in the chain-of-thought; QiMeng-MuPa's planner is the Translator's structured-output behavior;
SALV's planner is absent (whole-module generation). MTMC's planner is explicit and lightweight (the QiMeng-Kernel
paper notes the planner can be a smaller LLM than the coder). For Linus's local Worker plan with Qwen3 on 32 GB
unified memory, can a 7B planner + 7B coder run side-by-side at inference time, or is the realistic deployment
"single Worker doing both roles sequentially with KV-cache discard between turns"? This affects whether the cluster's
Worker self-improvement architectures are training-time-only patterns or inference-time orchestration primitives. The
MuPa repo-note's Question 3 and the SALV repo-note's Question 3 carry the per-repo framings; the cluster-level
question is whether Linus commits to a multi-Worker concurrent inference pattern in Phase 2/3 (per the agent-spawner
spec, DEC-0050, DEC-0051) or stays sequential through Phase 6 and revisits at Phase 7.

**3. Does the Linus-internal Worker need fine-tuning on hardware-design corpora?** The cluster's checkpoints (CodeV,
CodeV-R1, SALV-Qwen2.5-Coder-7B, the MuPa Qwen3-0.6B Translator) are Verilog/CUDA specialists. For Linus's general
Worker orchestration, none of these is the right base — the realistic Linus base is Qwen3 (32-GB-friendly, broadly
capable per Phase 1) with potential Kimi-K2 weight-streaming swap per the native-low-bit synthesis. The hardware-
design checkpoints are useful as **probe models** for studying RLVR-trained reasoning behavior and as **frozen
specialist Workers** for occasional Verilog use, not as Linus's substrate. The cluster question is therefore
methodology-extraction (lift the recipes into Linus's Phase 6 fine-tuning lane) rather than direct adoption of any
hardware-design checkpoint as the Linus base.

**4. Where does the closed-source synthesis-toolchain segment leave the idea-to-reality reach?** CodeV / CodeV-R1 /
SALV stop at functional-correctness via simulation; they do not address PPA (power / performance / area) optimization,
formal verification, timing closure, or actual silicon fabrication. The idea-to-reality pipeline as currently realized
has a closed-source segment (Synopsys Design Compiler / Cadence Genus / actual fab) that Linus cannot fully
internalize. QiMeng-cpu-v1 is the cluster's only repo that closed the full RTL → tape-out loop, and it required a
68-server cluster with Slurm. For Linus's Phase 7 idea-to-reality skill class, this means the cluster's hardware-side
exemplars demonstrate the **discipline** but the production-scale realization needs proprietary tools or institutional
infrastructure outside Linus's scope. The thematic synthesis (Task 5.2) carries the cross-domain version of this
question (how does the closed-source-segment problem shape Phase 7 skill-class scoping for non-hardware idea-to-reality
domains).

**5. Is the cluster's evidence base too narrow to commit a Phase 6 ADR?** All four repos are Verilog or CUDA
specialists; the recipes generalize **claimed**ly (the per-repo paper-notes carry strong arguments, but no paper
demonstrates the recipe on a non-hardware domain). The cluster's strongest cross-domain bets are SALV's signal-aware
DPO generalizing to Python function-aware DPO and typed-structured-prediction field-aware DPO, and MuPa's MuSL pattern
generalizing to Python↔Rust translation. Both need a Linus-internal validation experiment before becoming a Phase 6
ADR convention. The smallest-scope validation: a Python↔Rust MuPa loop using `pytest` + `cargo test` as the execution
oracle (per the MuPa repo-note's Question 6) doubles as a learning aid for Dan and validates the Co-verify substrate
on a non-CUDA target without requiring the Metal kernel wrapper.

**6. Should the cluster commit to MTMC + SALV as the Worker self-improvement stack?** The MTMC pattern (planner emits
decomposition; coder fills spans; RL trains the coder) and SALV's signal-aware DPO (per-substructure preference
optimization) are complementary by construction: MTMC's macro outputs are the decomposition input to SALV's DPO. Both
are paper-side; the MTMC repo doesn't exist (QiMeng-Kernel's release status is paper-only as of 2026-05-09), and SALV
is the only cluster repo with a full RLVR-style stack released. The cluster synthesis surfaces the combination as a
Phase 6/7 architecture candidate; the per-paper-notes carry the pattern-level argument; the durable architectural
commitment lives in a future ADR seed (per
[`qimeng-category-promotion.md`](../../specs/qimeng-category-promotion.md) §"What remains to be done" task 7) rather
than this synthesis. Worth surfacing here so the thematic synthesis (Task 5.2) can pick up the cross-domain
generalization without re-derivation.

---

_Cross-references: [`llm-hardware-design-synthesis.md`](../llm-hardware-design-synthesis.md) (forthcoming thematic
synthesis, Task 5.2 of the parent spec — the durable home for the cross-domain idea-to-reality argument);
[`qimeng-category-promotion.md`](../../specs/qimeng-category-promotion.md) (the canonical strategic anchor);
[`g8-sci-agents.md`](g8-sci-agents.md) (Sketch2Simulation's cluster home and the process-engineering arm of the
idea-to-reality spine); [`g1-apple-silicon.md`](g1-apple-silicon.md) (Apple-Silicon substrate the cluster's recipes
must port onto); [`g7-harnesses.md`](g7-harnesses.md) (workgraph DAG-dispatch substrate for the Co-verify orchestration
primitive lift). Next review triggers: Phase 2/3 Co-verify orchestration-primitive adoption decision; Phase 6c
Worker-selection spike result; Phase 6/7 Linus-internal MTMC reproduction commitment. Cluster placement: 12th repo
cluster in the synthesis landscape, sibling to g1-apple-silicon (which previously footnoted QiMeng-cpu-v1 before the
2026-05-08 promotion). Member repo-notes:
[CodeV](../../repo-notes/CodeV.md) ·
[QiMeng-MuPa](../../repo-notes/QiMeng-MuPa.md) ·
[QiMeng-SALV](../../repo-notes/QiMeng-SALV.md) ·
[QiMeng-cpu-v1](../../repo-notes/QiMeng-cpu-v1.md). Cluster paper-notes (15 total once Tier 1 lands):
[QiMeng-GEMM](../../paper-notes/13337-ZhouQ.md) ·
[CodeV](../../paper-notes/2407.10424v5.md) ·
[QiMeng-TensorOp](../../paper-notes/2505.06302v1.md) ·
[QiMeng-CodeV-R1](../../paper-notes/2505.24183v5.md) ·
[QiMeng-MuPa](../../paper-notes/2506.11153v2.md) ·
[QiMeng-Attention](../../paper-notes/2506.12355v1.md) ·
[QiMeng-SALV](../../paper-notes/2510.19296v4.md) ·
[VEGA](../../paper-notes/3696443.3708931.md) ·
[AutoOS](../../paper-notes/9546_AutoOS_Make_Your_OS_More_.md) ·
[QiMeng-Xpiler](../../paper-notes/osdi25-dong.md) ·
[QiMeng-CRUX](../../paper-notes/2511.20099v4.md) ·
[QiMeng-Kernel](../../paper-notes/2511.20100v1.md) ·
[QiMeng overview](../../paper-notes/2506.05007v1.md) ·
[Push the Limits CPU](../../paper-notes/2306.12456v2.md) ·
[Cheng et al. superscalar](../../paper-notes/0549.md)._
