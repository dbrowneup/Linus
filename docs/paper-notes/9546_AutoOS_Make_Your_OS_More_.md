---
title: "AutoOS: Make Your OS More Powerful by Exploiting Large Language Models"
source: ICML 2024 (Proceedings of the 41st International Conference on Machine Learning, PMLR 235)
authors:
  Huilai Chen, Yuanbo Wen, Limin Cheng, Shouxu Kuang, Yumeng Liu, Weijia Li, Ling Li, Rui Zhang, Xinkai Song, Wei Li,
  Qi Guo, Yunji Chen
affiliation:
  State Key Lab of Processors, Institute of Computing Technology, CAS; University of Chinese Academy of Sciences;
  Intelligent Software Research Center, Institute of Software, CAS
date: 2024-07
pdf: ../../context/papers/9546_AutoOS_Make_Your_OS_More_.pdf
tags:
  [
    llm-code-generation,
    os-kernel-tuning,
    linux-kconfig,
    aiot,
    embedded,
    state-machine,
    self-explanation,
    dynamic-tree-search,
    qimeng,
    llm-hardware-design,
  ]
---

# AutoOS: Make Your OS More Powerful by Exploiting Large Language Models

## TL;DR

Proposes AutoOS, a framework that drives an off-the-shelf LLM (GPT-3.5-Turbo) through Linux's `kconfig` decision tree
to customize and optimize OS kernel configurations automatically for AIoT and general-purpose scenarios. Frames the
problem as optimization on a dynamic tree (15,000+ Boolean / enum / numeric options with interdependencies, branch
insertion/removal as upstream choices unlock subtrees), then runs an observe-prune-propose-act-correct state machine
that traverses the tree level-by-level, keeping each prompt within the LLM's context budget. A two-round
self-explanation mechanism boosts decision consistency from 28.6% to 93.4% and effectively zeroes the
boot-failure-causing options before the correcting stage. Reaches 1.08x-1.26x performance over vendor defaults across
PolyOS / Fedora / Ubuntu (UnixBench) and 37/54 better sub-metrics on LMbench, in roughly one day per OS rather than
expert-weeks. Same ICT/CAS Yunji Chen / Qi Guo group as the rest of the QiMeng family.

## The problem (in plain language)

Modern Linux distributions ship with a kernel configuration ("`.config`") that selects among 15,000+ options:
schedulers, memory-allocator variants, debug instrumentation, file-system support, driver inclusion, preemption
model, tick rate, and so on. Vendors pick a generic default that's safe but rarely optimal, especially for
constrained hardware like AIoT boards (small RAM, specialized workloads, embedded peripherals). A specialist who knows
both the kernel internals and the target hardware can hand-tune `.config` and squeeze meaningful performance — often
weeks of an expert's time per board.

Three things make automating that tuning genuinely hard. The configuration space is enormous (>2^15000 if all options
were Boolean and independent, which they aren't — options interact and depend on each other in non-obvious ways).
Evaluating one configuration is expensive (compile + install + boot + benchmark = 1-2 hours per candidate). And many
options are "boot-fatal" — picking the wrong combination produces a kernel that doesn't boot, wasting the entire
evaluation cycle and giving zero learning signal. Classical approaches fail accordingly: neural-network methods need a
training dataset that doesn't exist (it would cost millions of hours of compile-evaluate to build), and Bayesian
optimization is comfortable with continuous spaces of fewer than ~20 dimensions, not with 15,000 mostly-Boolean options
with discrete dependency structure. Both classes also have no built-in concept of "this option will brick the boot
process" — they treat boot failure as a normal evaluation, paying a 1-2-hour failure cost per misstep.

A naive vanilla-LLM approach also fails. Asking GPT-4 "give me the best 15,000-option config for my board" loses on
context length (the kernel `.config` plus the kconfig source files run to ~100,000 words, dwarfing GPT-4's 32K context),
on consistency (the model contradicts itself between recommended and explained options), and on coverage (it returns
~10-20 generic options rather than the curated subset the hardware actually warrants).

The question AutoOS attacks: can a frozen LLM's expert prior knowledge be channeled through a structured search
algorithm so it interacts with the kconfig tree at a tractable per-prompt scale, prunes the boot-fatal options before
proposing, and converges on a hand-tuned-quality `.config` within roughly one day of compile-evaluate cycles?

## What they propose

**AutoOS** has three coupled mechanisms:

1. **Optimization-on-a-dynamic-tree formulation.** Linux's `make menuconfig` is already a directory-structured
   decision tree: the user navigates levels, the unmet dependencies hide subtrees, and selecting an option can both
   prune subtrees (now-unreachable options disappear) and graft new ones (newly-reachable options appear). AutoOS
   formalizes this as a tree T = (N, E) where the LLM searches a subset M of nodes that maximizes an evaluation
   function f(M) (a UnixBench score in their experiments) while avoiding the subset K of boot-fatal options. The
   tree-with-insertion/deletion shape both naturally bounds per-level prompt size and naturally encodes the
   inter-option dependency structure that defeats Bayesian methods.

2. **Five-stage state-machine traversal (observe-prune-propose-act-correct).** Each level of the tree is visited in a
   five-stage loop:
   - _Observing_ — atomic API calls (built on a modified `kconfiglib`) supply the LLM with the level's directories,
     options, semantic descriptions, and types.
   - _Pruning_ — for each subdirectory, the LLM emits P(prune | node) and a sampled prune-or-not decision; entire
     subtrees deemed irrelevant or boot-fatal are dropped before any of their options reach the proposing stage.
   - _Proposing_ — for the remaining options, the LLM picks values; the choice is randomized via the LLM's temperature
     to diversify exploration across the 24 search trials.
   - _Acting_ — the proposed option settings are applied via the atomic-API kconfig manipulator, which also reports
     newly-appeared options (subtrees grafted in) and disappeared ones (subtrees pruned by upstream choices). New
     options are queued for further proposing within the same level until the level stabilizes.
   - _Correcting_ — once the full tree has been traversed and the candidate config M is built, AutoOS compiles, boots,
     benchmarks, and on boot failure relays the failing config + error log back to the LLM for targeted debug; binary
     search is the documented fallback when the LLM-driven correction fails.

   The state machine explicitly handles the dynamic tree's growth (newly-appeared options) and shrinkage (options that
   vanish after a parent decision) as first-class transitions, which is what lets AutoOS work at the 15,000-option
   scale on a 32K-context model.

3. **Two-round self-explanation mechanism.** The authors observed that the LLM is internally inconsistent — it
   "explains" an option as performance-positive but then "does" something different (recommends disabling it). To fix
   this, the proposing stage runs a two-round self-explanation prompt: the LLM first analyzes each option's expected
   impact in isolation, then re-analyzes the impact in context, and only then commits to the recommendation. The
   ablation shows decision consistency rising from 28.6% (zero rounds) to 83.1% (one round) to 93.4% (two rounds);
   eight rounds give only 94.85%, so two is the cost-effective sweet spot. Self-explanation also brings
   boot-failure-causing options to zero in the ablation table — the consistency gain mostly manifests as eliminating
   the worst false-positive recommendations.

The overall stance is the QiMeng family's recurring pattern: don't fine-tune, don't train, **engineer the prompt
substrate plus the tree-search harness** so a frozen LLM can climb the optimization landscape using its prior
knowledge. The kconfig tree's structure is the load-bearing prior; the LLM is the fitness oracle plus the proposer.

## Key results

- **Vs. vendor defaults (UnixBench total score).** PolyOS on the SiFive HiFive Unmatched RISC-V board: 309 -> 335
  (+8.4%); Fedora on the same board: 207 -> 260 (+25.6%); Ubuntu on Intel x86-64 PC: 3,885 -> 4,238 (+9.0%). The PolyOS
  default is described as "exhaustively manually optimized" by experts, so AutoOS still beating it by 8.4% is the
  expert-level claim.
- **Vs. LLM-Vanilla.** Direct prompting (the GPT-3.5 baseline that returns 10-20 generic options) **regresses** every
  test bed — PolyOS -8.5%, Fedora -6.3%, Ubuntu +0.3%. The 33%-point gap on Fedora between LLM-Vanilla (-6.3%) and
  AutoOS (+25.6%) is the quantitative case for the structured search.
- **Sub-metric dispersion.** On Fedora's UnixBench breakdown, AutoOS lifts execl throughput +44%, process creation +43%,
  pipe switching +47%, and pipe throughput +29% — a far larger move than the headline +25.6% total. The total-score
  dilution is mostly from CPU-bound integer/float sub-tests (Dhrystone, Whetstone) where OS configuration has limited
  leverage. The picture is "AutoOS shines on the OS-bound sub-tests, where it should."
- **Generalization (LMbench).** Using the AutoOS PolyOS config tuned for UnixBench, 37/54 LMbench sub-metrics improve
  by 10-30%, 13/54 are comparable, only 4/54 regress slightly. AutoOS does not overfit the training benchmark — it
  selects an "OS-good" config that transfers to a different OS benchmark suite.
- **Boot-failure handling.** Across 24 trials per OS, average correction-phase invocations were 0.125 (PolyOS), 0.417
  (Fedora), 0.625 (Ubuntu) — most candidate configs boot on first try, validating that the pruning stage filters out
  most of the boot-fatal subtree before any compile happens.
- **Search wall time.** ~1 day per OS (the upper bound is set by the 1-2-hour compile-boot-benchmark cycle times 24
  trials), versus expert-weeks. The search-time-budget framing is honest: the bottleneck is hardware evaluation, not
  the LLM.
- **Pruning + self-explanation ablation (PolyOS).** The "plain" framework (no pruning, no self-explanation) reaches
  total score 137 with 230 modified options and 5 boot-failures over 26.7 hours of correction time. Adding pruning
  alone: score 298, 20 modified options, 2 boot-failures, 6.6 correction-hours. Adding self-explanation alone: score
  332, 74 modified options, 0 boot-failures, 0 correction-hours. Both: score 335, 17 modified options, 0
  boot-failures, 0 correction-hours. Self-explanation is a remarkably high-leverage prompt-engineering trick.

## What's reusable in Linus

AutoOS is the QiMeng family's OS-level analog of QiMeng-GEMM's kernel-level **idea -> reality** discipline. The LLM
produces an artifact (a `.config` file: a list of `CONFIG_FOO=y` / `CONFIG_FOO=n` / `CONFIG_BAR=42` lines); a
downstream non-LLM actor (the kernel build system — `make oldconfig` / `make`) accepts it and turns it into a runnable
binary at expert-tuned quality. The artifact is auditable line by line, can be diffed against the vendor default, and
can be regenerated reproducibly. This is **Phase 7 idea-to-reality skill class** material in the qimeng-category-
promotion.md sense, with extensions worth flagging for Linus.

**Phase 7 — Apple Silicon analog: LLM-tuned macOS performance settings.** macOS doesn't expose a kconfig-style
configuration tree, but it does expose a layered configuration surface: `sysctl` parameters (~4,000 readable, ~1,000
writable), `defaults` system preferences, `nvram` boot-args, kernel extensions, power-management settings, and
performance `taskpolicy` knobs. None of these is as expressive as a Linux `.config`, but the stack is non-trivial — and
it is exactly the surface a Dan-flavored Linus Worker should be able to navigate when asked "tune my MacBook for sustained
inference workloads" or "make Spotlight stop competing with my training run."
- _Artifact the LLM produces:_ a layered patch of (sysctl, defaults, nvram, taskpolicy) settings — written as a shell
  script or a structured-prediction record per the CLAUDE.md S25 convention.
- _Downstream actor that accepts it:_ macOS itself (sysctl applies live, nvram applies on next boot).
- _What must be true for Linus to replicate the discipline locally:_ a curated dependency / boot-fatal map for macOS
  (the analog of kconfig's tree structure — much smaller and more brittle), a benchmark harness (e.g., the existing
  Linus benchmark suite, a sustained-inference throughput probe), and a per-setting hint repository structured exactly
  like AutoOS's per-option semantic data. The danger is that macOS settings interact in less-documented ways than
  Linux kconfig — many `sysctl` knobs are technically writable but have no documented downstream effect, while others
  silently cause kernel panics. The pruning + self-explanation discipline is more important here than in AutoOS,
  not less.

**Phase 7 — generalization to "LLM-tuned conda env flags" / build-time tuning.** A more tractable near-term Linus skill
is tuning configuration spaces that don't risk a panic on a wrong choice but do affect performance: conda environment
flags (channel ordering, `pip install --no-build-isolation`, MKL vs. OpenBLAS, threading-library overrides), MLX
runtime environment variables (`MLX_GPU_MEMORY_LIMIT`, `MLX_LOG_LEVEL`), Ollama tuning (`OLLAMA_FLASH_ATTENTION`,
`OLLAMA_KV_CACHE_TYPE`, already in CLAUDE.md Known Library Quirks), and Python/NumPy threading knobs
(`OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS`). The state-machine pattern with self-explanation maps
cleanly: the option set is small (10s-100s, not 15,000), the evaluation is cheap (seconds-minutes per candidate, not
hours), and there are no boot-fatal failures — so pruning becomes lightweight, evaluation becomes fast, and the entire
loop fits inside a single Phase 2/3 orchestration session. This is _the_ minimum-viable port of the AutoOS pattern for
Linus, and an excellent Phase 2/3 substrate-validation target — open question 2 below.

**Phase 2/3 — observe-prune-propose-act-correct as a generic orchestration loop.** Stripped of the kconfig specifics,
AutoOS is a generic LLM-driven structured-search pattern with a built-in failure-recovery substage. The five-stage
loop is more articulated than QiMeng-GEMM's beam search because it explicitly separates the
"figure out the structure" stage (observe) from the "decide what's irrelevant" stage (prune) from the "decide what to
change" stage (propose) — and crucially, it has a first-class _correcting_ stage that closes the loop on partial
failures rather than treating them as dead branches. This is a Phase 2/3 orchestration primitive worth extracting:
it's the same shape as workgraph's DAG-dispatch (G7 synthesis) and QiMeng-GEMM's beam search (13337-ZhouQ), but with
explicit error-recovery typing — the failed-config-plus-stack-trace is fed back as a typed AgentReport (DEC-0051) and
the LLM debugs in-context. _Seed: this could be a future ADR — observe-prune-propose-act-correct as a Linus
orchestration primitive for any structured-search task with expensive evaluation and recoverable failure._

**Phase 6 — AutoOS as a synthetic-data-generation source.** The 24-trial-per-OS search produces a corpus of
(config, score, success/fail-and-why) tuples that are exactly the typed-prediction-wrapping-rationale shape from
CLAUDE.md S25. A pipeline that runs AutoOS-style search across many embedded boards / scenarios and captures the
prompts + responses + outcomes is a high-quality LoRA fine-tuning dataset for an "OS-tuning Worker" specialist. This
generalizes: any AutoOS-pattern application (kernel config, macOS sysctl, Ollama flags) generates its own training
data as it runs — a cleaner version of the QiMeng-GEMM hint-repo-as-deliverable framing.

**Self-explanation as a reusable prompt convention.** The two-round self-explanation pattern (analyze first, then
re-analyze in context, then commit to the recommendation) is general-purpose and orthogonal to the AutoOS application.
The 28.6% -> 93.4% consistency lift on a frozen GPT-3.5 is striking — and it lifts directly into Linus's
typed-structured-prediction discipline (CLAUDE.md S25). Worth surfacing as a prompt-engineering convention candidate
for any Worker call producing a structured prediction with an embedded rationale: prompt the model to commit to an
explanation, then to a decision, then to verify the decision against the explanation. _Seed: candidate Phase 2 ADR for
two-round-self-explanation as a Linus prompt convention for structured prediction._

## What's NOT applicable / hype filter

The 1.08x-1.26x headline is over **vendor defaults** for general-purpose distros (Fedora, Ubuntu) and an
"exhaustively manually optimized" PolyOS configuration. The 1.26x on Fedora reads more impressive than the others,
but Fedora's RISC-V default is much less tuned for the SiFive HiFive board than PolyOS's is — the bigger headroom is
the explanation, not necessarily the algorithm's absolute strength. The ~10% Ubuntu gain on a desktop x86-64 system is
the more honest signal of generalizable improvement; the +9% is non-trivial but doesn't suggest anything close to
"hand-tuned-quality" on a workload the vendor has had decades to optimize.

The kconfig tree structure is **load-bearing**. AutoOS works because Linux's kconfig formalizes the option dependency
graph as a navigable tree with documented semantics, exposes it through a well-specified API (kconfiglib), and ships
with a small command (`make menuconfig`) that makes the tree traversable. The paper's own Limitations section
acknowledges this: AutoOS does not directly apply to non-Linux-kernel-based OS, and the engineering cost of
abstracting "kernel configurations as a dynamic tree" for a new substrate is non-trivial. For Linus's macOS analog
(open question 1), this is the largest unknown — the macOS configuration surface is _not_ a documented dependency
tree, and constructing one is itself a substantial Phase 7 deliverable.

The 1-2-hour evaluation cycle is **expensive and hard-coded into the wall-clock budget**. The "one day per OS" wall
time is dominated by the 24 trials each costing 1-2 hours of compile + install + boot + benchmark. For Linus's
local-Worker plan on Apple Silicon, the analogous evaluation cycle is much faster on the macOS-tuning analog (live
sysctl reload, no kernel rebuild) but still substantial on actual kernel-rebuild scenarios (no Linus user is going to
rebuild a kernel locally as a routine optimization step). For most Linus-relevant configuration-tuning use cases, the
evaluation step will be either much faster (sysctl, env vars) or much slower (rebuilding LLM weights or pipelines for
"tune my LoRA hyperparameters" applications). The AutoOS wall-time-budget framing transfers, but the constants don't.

GPT-3.5-Turbo is the only LLM evaluated in the AutoOS paper. Unlike QiMeng-GEMM, AutoOS doesn't ablate over
model strength — there's no Codestral-22B equivalent that fails on the protocol. The implicit claim is that
GPT-3.5-Turbo is sufficient because the per-prompt task is simple (analyze ~10-50 options at a level), but the protocol's
multi-turn nature and the self-explanation rounds raise the same concern raised by QiMeng-GEMM's Codestral failure: a
small local Worker may not sustain the protocol. Worth measuring before committing.

The dataset of "boot-fatal options" (the K set) is implicit in the LLM's prior — there's no curated table of "these 47
options brick the boot, never propose them." This is a strength (no manual data work) and a weakness (the system's
floor on boot-failure rate is set by GPT-3.5's prior knowledge of Linux kernel internals, which is finite and version-
sensitive). For a domain like macOS where the LLM's prior is much less developed than Linux, this changes the
risk/value calculation substantially.

The five-stage state machine and the two-round self-explanation are presented as a unified design but are clearly
separable. The ablation shows self-explanation is the bigger contributor on PolyOS (75% of the boot-failure reduction
and most of the score gain), with pruning being more about runtime efficiency. For a Linus port, applying the
self-explanation pattern is much higher-leverage than reproducing the full state machine.

## Connections

This is the OS-level analog of [QiMeng-GEMM (13337-ZhouQ.md)](13337-ZhouQ.md)'s kernel-level
**idea -> reality** discipline: in QiMeng-GEMM the LLM produces matmul source code accepted by `clang`/`nvcc`; in
AutoOS the LLM produces a `.config` accepted by the kernel build system. Both treat the problem as structured search
over an LLM-emitted artifact with a downstream non-LLM actor as oracle, both rely on a hand-curated semantic
substrate (hint repository in QiMeng-GEMM, kconfig API + per-option semantics in AutoOS), and both decline to
fine-tune in favor of prompt + search. AutoOS extends the QiMeng-GEMM pattern with an explicit failure-recovery stage
(the correcting loop) — a worthwhile generalization.

The strongest in-family neighbor is [QiMeng-Kernel (2511.20100v1.md)](2511.20100v1.md), where the macro/micro
planner-coder split with RL-trained policy formalizes what AutoOS's state machine does informally. AutoOS's
proposing stage is structurally the same role as QiMeng-Kernel's macro planner; AutoOS's acting + correcting stages
are the same role as QiMeng-Kernel's micro coder + verification loop. AutoOS predates QiMeng-Kernel and uses
prompt-engineering rather than RL, which makes it the cleaner reference for Phase 2/3 substrate validation.

Other QiMeng-family connections: [QiMeng (2506.05007v1.md)](2506.05007v1.md) — the integrating overview that places
AutoOS in the family taxonomy; [QiMeng-CRUX (2511.20099v4.md)](2511.20099v4.md) — Verilog code-gen sibling, same
prompt-engineering-as-substrate discipline applied to HDL; [Push the Limits — CPU design via AI (2306.12456v2.md)](2306.12456v2.md)
— earlier CAS-group work establishing the "LLMs design real hardware" thread at the CPU level;
[Cheng et al. superscalar processor design (0549.md)](0549.md) — the closely-related processor-architecture exemplar.
The repo-side anchor for the family is [QiMeng-cpu-v1 (repo-note)](../repo-notes/QiMeng-cpu-v1.md).

The cross-paradigm sibling outside QiMeng (same idea -> reality spine, different domain) is
[Sketch2Simulation (2603.24629v1.md)](2603.24629v1.md) — process-engineering flowsheets via multi-agent LLMs accepted
by Aspen HYSYS. AutoOS is OS configuration; Sketch2Simulation is chemical-process configuration; QiMeng-GEMM is
kernel code. Three artifact types, three downstream actors, one design discipline.

The cluster home is the in-flight [`docs/specs/qimeng-category-promotion.md`](../specs/qimeng-category-promotion.md)
(B14 / g12-llm-hardware-design synthesis to be authored in Tier 5 of `docs/specs/2026-05-09-context-foldin-fanout.md`),
where AutoOS anchors the **OS-configuration** branch of the idea -> reality spine. AutoOS is also a candidate touch
point for the [skills-and-practices synthesis](../syntheses/skills-and-practices-synthesis.md) (the
two-round self-explanation as a Linus prompt convention) and the
[infra-foundations synthesis](../syntheses/infra-foundations-synthesis.md) (configuration-space search as an
orchestration primitive).

The state-machine traversal connects to [G7 harnesses synthesis](../syntheses/repo-clusters/g7-harnesses.md)
(workgraph DAG-dispatch + handler-for-model patterns) and to the agent-spawner role-as-first-class-type design
(DEC-0050 / DEC-0051): observe / prune / propose / act / correct map naturally onto five typed agent roles with
typed AgentReport handoffs. The two-round self-explanation rhymes with the
typed-structured-prediction-wrapping-rationale convention from CLAUDE.md S25.

## Open questions for Dan

1. **macOS configuration-surface mapping — is this even tractable?** AutoOS lives on Linux because kconfig is a
   well-documented dependency tree exposed via a navigable API. macOS has no equivalent. Is constructing a
   macOS-configuration dynamic tree (sysctl + defaults + nvram + power-management + taskpolicy + Spotlight + kernel
   extensions, with cross-dependencies and boot-fatal-option mapping) a Phase 7 deliverable Dan wants to invest in,
   or is the analog skill better targeted at a much narrower surface (just MLX runtime env vars, just Ollama tuning)
   where the dependency structure is simple? The macOS-tree-construction question is the largest practical blocker
   to porting AutoOS-as-a-skill to Linus.

2. **LLM-tuned conda env flags / runtime env vars — Phase 2/3 substrate-validation target?** The smallest meaningful
   port of the AutoOS pattern is tuning a configuration surface that's ~50 options, evaluates in seconds, and never
   bricks anything: conda env channels + pip flags + threading-library env vars + MLX/Ollama performance knobs. This
   is much more tractable than the macOS-sysctl analog (open question 1) but it's also where Dan's actual day-to-day
   pain probably lives — "Linus, profile and tune my conda env for `pip install jax` to use the right BLAS." Worth
   building first to validate the observe-prune-propose-act-correct pattern, then maybe extending to bigger surfaces.

3. **Two-round self-explanation as a Linus prompt convention.** The 28.6% -> 93.4% consistency lift on GPT-3.5 is a
   high-leverage prompt-engineering result. Should Linus surface this as a documented convention (alongside CLAUDE.md
   S25's typed-structured-prediction-wrapping-rationale) for any Worker call producing a structured prediction with
   stakes? It costs ~2x the prompt tokens and roughly halves the inconsistency rate; for stakes-bearing decisions the
   trade is clearly worthwhile. Open question is whether the result generalizes to local Worker models (Qwen3-Coder,
   DeepSeek-Coder-V2-Lite) or whether the lift is closed-model-specific.

4. **State-machine traversal as a Phase 2/3 orchestration primitive.** The five-stage loop (observe / prune / propose
   / act / correct) is a more articulated version of QiMeng-GEMM's beam search and the workgraph DAG-dispatch
   pattern, with explicit failure recovery. Is there a Phase 2/3 case for adopting it as a Linus orchestration
   primitive (alongside or underneath workgraph), with each stage as a typed agent role producing a typed AgentReport
   and a durable scratchpad-class artifact (DEC-0030, DEC-0050, DEC-0051)? If yes, the v1 substrate could be the conda-env-
   tuning skill from open question 2, validating the orchestration primitive on a real workload before committing the
   pattern to Phase 3 architecture.

5. **Boot-fatal-option dataset as a curated artifact.** AutoOS implicitly relies on the LLM's Linux-kernel prior to
   identify boot-fatal options. For domains where the LLM's prior is weaker (macOS, niche embedded RTOS, non-Linux
   container runtimes), curating an explicit boot-fatal-option list — and structuring it as
   typed-prediction-wrapping-rationale records per CLAUDE.md S25 — could be a Phase 7 deliverable in its own right.
   Is this worth investing in, or is the right Linus stance "stay on configuration surfaces where mistakes are
   recoverable" (open question 2's framing)?

6. **AutoOS as a synthetic-data-generation source for Phase 6 fine-tuning.** Each AutoOS run produces ~24 trials' worth
   of (config, prompt, LLM response, evaluation outcome) tuples. Aggregating across many boards / scenarios / OSes
   produces a configuration-tuning corpus that could fine-tune a specialist Worker. Is "OS / runtime configuration
   tuning" a Phase 6 specialist worth building, or is it a Phase 7 skill best handled by a general-purpose Worker
   plus the AutoOS-style harness? The answer depends on the answer to open question 1 — if macOS-as-skill turns out to
   be in scope, a specialist becomes more valuable; if Linus stays on narrow runtime-env-var surfaces, a general
   Worker is enough.

7. **Where to place AutoOS in the new g12-llm-hardware-design synthesis.** The QiMeng family has a hardware-design
   spine (kernels, accelerator microarchitecture, CPU design); AutoOS is the OS-software-side member of the same
   research family but isn't strictly hardware design. Should the cluster synthesis present AutoOS as the
   "system-software analog" branch of the idea -> reality spine, or carve out a separate tier inside the cluster for
   "configuration-space tuning" (which would also house the macOS analog if we build it)? Decision shapes the cluster
   narrative and the section structure of `g12-llm-hardware-design.md`.
