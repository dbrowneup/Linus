# QiMeng-cpu-v1 (`QiMeng-OSINT/QiMeng-cpu-v1`)

## 1. Purpose and scope

QiMeng-cpu-v1 is the source code for "Automated CPU Design by Learning from Input-Output Examples," a 2024 IJCAI paper that learns CPU logic from black-box I/O behavioral specifications without formal Verilog code. The BSD (Binary Speculative Diagram) learner generates 18,260 single-output Boolean functions as a RISC-V CPU design, which was taped out as Enlightenment-1, the world's first AI-designed CPU. Relevance to Linus: the Boolean-function learning from I/O examples mirrors automated circuit design from behavioral specs and showcases how to scale automated synthesis from small logic circuits to industrial CPUs — patterns applicable to Linus Phase 6+ fine-tuning and automated optimization.

## 2. Architecture summary

C++ implementation of BSD (Binary Speculative Diagram) algorithm with Python visualization tools. The core algorithm uses a graph-based Boolean function approximation that gradually expands from coarse to fine-grained structures, driven by "Boolean Distance" metric to measure structural similarity between functions. The CPU design is partitioned into 10 clusters; each cluster trains 1,826 single-output BSDs independently (18,260 total outputs). Sequential execution is ~3,500 CPU-hours; parallel execution on 68-server HPC cluster with Slurm achieves 5-hour wall-clock time. Test harnesses include Linux kernel boot, SPEC CINT 2000, Dhrystone, and self-designing demonstrations (the chip learns its own design). Results output as Verilog gate-level netlists, convertible to GTECH via Synopsys Design Compiler.

## 3. What's reusable in Linus

The I/O-example-driven learning paradigm (no human-written specs, just test cases) is philosophically aligned with Linus's goal of learning from Dan's behavior (usage patterns, preferred tools, task decompositions). The Boolean Distance metric for measuring structural similarity between functions suggests how to measure distance between learned vs. target behaviors in fine-tuning. The hierarchical partitioning strategy (10 clusters of 1,826 tasks) is a reusable pattern for parallelizing large synthesis problems. The pipeline from I/O spec → behavioral synthesis → Verilog → tapeout is an existence proof that autonomous synthesis works at scale.

## 4. What's inspiration only

The BSD algorithm itself is specialized to Boolean function synthesis and not directly transferable to LLM fine-tuning or Linus's inference tasks. However, the broader lesson — "learning from I/O examples scales to industrial complexity (18k outputs, successful CPU)" — is reassuring for Linus Phase 6's hypothesis that learning from Dan's task-execution logs can produce meaningful fine-tuning signals. The self-designing demonstration (the CPU designs its own improvements) is a clever idea for Linus Phase 7 (Skills & Autonomy Graduation), though implementation is domain-specific.

## 5. What's incompatible or out of scope

Linux-only (tested on CentOS); requires GCC 9.3.0+, Python 3.6.8+. Synopsys Design Compiler is optional but needed for GTECH conversion and verification. Slurm is needed for distributed execution; single-machine execution of the full CPU is tractable but slow (3,500 hours). The algorithm is deterministic and resource-constrained, not designed for GPU/Metal acceleration. Not relevant to Linus's inference or RAG tasks directly; more relevant as a case study in automated design methodology.

## 6. Recommendation: **Watch (Phase 6+)**

Not for direct adoption, but important conceptually for Phase 6 (Fine-Tuning) and Phase 7 (Skills & Autonomy). If Dan decides to pursue automated fine-tuning or learned synthesis of Linus components (e.g., learning a custom tokenizer from I/O examples), the BSD learner's methodology and the CPU design case study become highly relevant. For now, archive this and revisit once Phase 6 planning begins.

## 7. Questions for Dan

- **I/O-driven fine-tuning for Linus.** The BSD learner trains from I/O test cases with no human code. Could Linus Phase 6 adopt a similar approach: gather (task_input, task_output) pairs from Dan's usage logs, then fine-tune a small model to replicate that behavior? Is this realistic given the scale of behavioral variation?
- **Boolean Distance as a loss metric.** BSD uses Boolean Distance to measure function similarity. Could a similar distance metric be defined for Linus behaviors (e.g., tool selection similarity, reasoning steps)? Worth prototyping at Phase 6?
- **Parallelization strategy.** The 10-cluster partitioning of 18,260 tasks enabled 68-server cluster execution in 5 hours. If Linus Phase 6 involves sweeping many hyperparameter combinations or fine-tuning multiple model sizes in parallel, is a similar task-partitioning strategy applicable?
- **Self-designing capability.** The CPU's self-improvement loop (design → test → feedback → refinement) is intriguing. Could Linus Phase 7 implement analogous self-improvement (Linus learns from Dan's corrections and continuously refines its skills)? Prototype scope and feasibility?
