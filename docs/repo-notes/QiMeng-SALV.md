# QiMeng-SALV (`QiMeng-IPRC/QiMeng-SALV`)

## 1. Purpose and scope

QiMeng-SALV is the official training-pipeline release for "QiMeng-SALV: Signal-Aware Learning for Verilog Code
Generation" ([paper-note `2510.19296v4.md`](../paper-notes/2510.19296v4.md), NeurIPS 2025). The repo packages the
two-stage training recipe — SFT followed by Signal-aware DPO (SA-DPO) — that fine-tunes Qwen2.5-Coder-7B-Instruct
into a Verilog code generator matching DeepSeek-V3 (671B) on RTLLM v1.1 with 7B parameters. The headline contribution
that makes this repo non-trivial is the **selective-loss customization** of LLaMA-Factory: instead of computing DPO
loss over all tokens of preferred/dispreferred samples, the loss is computed only over the token spans corresponding
to specific output signals identified via Yosys AST parsing. The repo distributes (a) data-prep scripts that go from
the cleaned 135k CodeV seed corpus to ~350k preference pairs annotated with signal-level token spans, (b) a forked
LLaMA-Factory submodule that consumes the annotated pairs and applies the selective DPO loss, and (c) inference glue
for the released SALV-Qwen2.5-Coder-7B model on HuggingFace.

Relevance to Linus: the repo is a working open-source reference for **substructure-aware preference optimization** —
the closest published precedent for fine-tuning a Worker to produce structured outputs where each substructure has its
own correctness oracle. The recipe generalizes beyond Verilog (function-aware DPO for Python, field-aware DPO for
typed-structured-prediction outputs per CLAUDE.md S25), and the repo is the artifact that demonstrates the loss
customization is feasible against a public, widely-used training framework.

## 2. Architecture summary

Three top-level subdirectories implement the pipeline. **`Utils/`** contains the shared infrastructure: `rollout.py`
(98 LoC) drives vLLM inference to sample k candidate Verilog modules per prompt; `sim.py` (147 LoC) wraps iverilog
simulation under Ray for per-candidate functional verification against random stimuli derived from the reference
module; `utils.py` (22 LoC) provides JSONL/JSON helpers. **`SFT/`** runs the rejection-sampling SFT data prep (k=5
candidates per prompt, keep correctly-passing ones for SFT corpus augmentation), then trains via LLaMA-Factory's
upstream SFT objective. **`SA-DPO/`** is the heart of the repo:

- `gen_spec_seed_data.py` (38 LoC) — converts CodeV's code-completion descriptions into specification-to-RTL
  descriptions for richer DPO prompts.
- `gen_AST.py` (141 LoC) — runs Yosys on each rolled-out module to produce its AST text; multiprocessed via Ray.
- `parser.py` (606 LoC) — the largest single file; defines `ASTNode` and `ASTTree` classes that parse Yosys AST output
  into structured trees, build per-module signal-dependency graphs, and perform backward traversal from each output
  signal's leaf node to extract the AST subtree's covered code lines (the `S^c` segment from the paper). This is the
  technically intricate piece — it's an AST→code-segment mapper that survives Verilog's `always`-block / `case` /
  conditional-assignment patterns.
- `gen_sa_dpo_training_data.py` (167 LoC) — assembles the final preference pairs. For each (preferred, dispreferred,
  contrast-signal) triple, it tokenizes the responses and emits records in the format
  `"verilog code <select_token> code segment token ids"` — the trailing token-id list is the mask that the customized
  LLaMA-Factory loss restricts the DPO computation to.
- `train_sa_dpo.yaml` / `merge_lora.yaml` — LLaMA-Factory configs running LoRA-based DPO at lr=5e-6 for ~7000 steps,
  followed by LoRA merge.

The customized **`LLaMA-Factory/`** is a vendored submodule (not the upstream); it parses the
`<select_token>`-annotated responses and computes DPO loss only on the selected token spans (per the paper's Eq. 2).
The customization is the load-bearing engineering work of the repo; without it, the data-prep pipeline produces
records that upstream LLaMA-Factory would silently ignore the masking on. Inference at deployment time uses the
merged model with vanilla `transformers` `AutoModelForCausalLM` — no special inference machinery required.

External dependencies: `vllm==0.8.3` and `deepspeed==0.16.9` (pinned in `requirements.txt`), `iverilog` and `yosys`
(install via apt on Linux, brew on macOS), Python 3.11, conda env named `SALV`. The released model
(`TabCanNotTab/SALV-Qwen2.5-Coder-7B-Instruct`) is bf16 7B; the dataset (`TabCanNotTab/SALV-dataset`) is published as
a HuggingFace dataset of preference pairs.

## 3. What's reusable in Linus

The **selective-DPO-loss customization** is the highest-leverage reusable artifact in the repo. Linus's Phase 6
fine-tuning lane needs a substrate that supports per-substructure-token-mask losses for any task with a
substructure-level oracle (per-function pytest for code, per-field validator for typed-structured-prediction outputs,
per-section validator for multi-section reports). The repo's LLaMA-Factory fork is the working open-source reference
for that substrate. The customization is conceptually simple — extend the DPO loss to multiply log-probabilities by a
token-span mask before summing — but the integration cost is non-trivial; having a working reference saves an
implementation cycle. A Linus port could either (a) vendor a similar fork into Linus's training tree, (b) port the
selective-loss patch to MLX-LM-FT (the Apple-Silicon-native fine-tuning toolchain), or (c) implement a generic
"selective-objective wrapper" abstraction that takes any objective fn + token mask and returns a masked variant.
Option (c) is the cleanest; the SALV repo's fork is the empirical existence proof that (c) is plausible.

The **AST→code-segment mapper in `parser.py`** is reusable as a methodology reference for any task that needs to map
from a parsed-AST node back to source-text spans. The Verilog-specific class structure (the `ASTTree` walk over
Yosys's particular AST format) is not directly portable, but the pattern — parse to AST, build dependency graph,
backward-traverse from output node, retain covered source-text lines — is. For Linus, the closest analogous use is
extracting per-function token spans from Python ASTs for function-aware DPO; the `parser.py` patterns transfer in
shape if not in code.

The **iverilog-based differential-simulation harness** (`Utils/sim.py`) is a clean, fast (0.65 ms/sample with
parallelism) implementation of property-based testing applied to LLM-emitted code: generate N random input stimuli
from the reference's interface, simulate both candidate and reference, compare outputs per-signal. The pattern
generalizes to Python (run candidate fn vs. reference fn on random inputs, compare per-output-field), Rust (same
shape with cargo-fuzz-style stimuli generation), and any executable artifact. Reusable as a pattern; the Verilog-
specific iverilog wrapping is reference-only.

The **rejection-sampling SFT data augmentation** (`SFT/gen_sft_training_data.py`) is a small but tidy 48-LoC
implementation of "sample k candidates per prompt, keep the correct ones, fold them into SFT corpus." This is a
generic SFT data-augmentation recipe that Linus's Phase 6 training-recipe library could carry as a first-class
function with task-specific oracle plugins.

The **Yosys-AST + iverilog choice for the EDA tooling** is a deliberate engineering decision worth carrying forward
if Linus ever needs HDL-aware tooling: both are open-source, both are widely available, both run on macOS via Homebrew
without major friction. The SALV repo demonstrates that an HDL training pipeline can be built on these tools without
proprietary EDA dependencies.

The **HuggingFace artifacts** (model + dataset) make this the most reproducible recipe in the QiMeng cluster. A Linus
Phase 6 reproduction is well-scoped: ~7000 LoRA steps on a 7B bf16 base with a 350k-pair dataset is comfortably within
M1 Max's 32 GB unified memory budget.

## 4. What's inspiration only

The **two-stage SFT → SA-DPO pipeline as a whole** is inspiration-level, not direct-port-level: SALV trains
specifically against a Verilog corpus with reference modules paired to each prompt; Linus's general-purpose Worker
fine-tuning may not have access to that pairing. The shape — SFT first, then preference optimization with selective
loss — is the takeaway, not the specific data flow.

The **partial-correct-sample filtering ablation** (mixing partials hurts without filtering, helps with) is a
methodological inspiration for Phase 6 dataset curation conventions but doesn't directly port without per-domain
substructure oracles. For Verilog the oracle is iverilog simulation; for general code it's pytest; for typed-
structured-prediction outputs it's per-field validators. The repo demonstrates the recipe; instantiating it for a new
domain requires the oracle infrastructure.

The **inference example in README.md** (transformers + Verilog code-block extraction) is straightforward and not
particularly novel — useful only as a confirmation that the released model loads cleanly. Linus's Phase 6 fine-tunes
will use Ollama / MLX-LM for inference; the transformers loader is reference-only.

The **CodeV seed data lineage** is significant for context (SALV is a sibling of CodeV-R1, both trained on the same
135k cleaned dataset) but is not part of the SALV repo proper — the dataset is hosted separately. For full
reproducibility a Linus port needs the CodeV repo as a sibling reference (see [`CodeV.md`](CodeV.md), pending; the
paper-notes `2407.10424v5.md` and `2505.24183v5.md` cover the lineage).

## 5. What's incompatible or out of scope

**Linux-first training environment.** The training scripts assume `apt install iverilog yosys`, deepspeed-style
distributed training, and the bash-shell entry points (`get_sft_training_data.sh`, `get_sa_dpo_training_data.sh`).
macOS works — both iverilog and yosys are in Homebrew, deepspeed runs on PyTorch+MPS but with limited validation —
but the published bash scripts would need light adaptation. The throughput numbers in the paper (60-core parallelism
for 0.65 ms/sample simulation) are not directly transferable to M1 Max's 10 CPU cores; expect ~6× wall-clock per
epoch's worth of stimuli generation. The training itself is LoRA on a 7B base, comfortable within 32 GB unified
memory but unmeasured on Apple Silicon.

**vLLM for rollout.** The candidate-sampling stage uses vLLM 0.8.3, which has Apple-Silicon support but is not the
primary deployment target for Apple-Silicon workloads. For a Linus Phase 6 reproduction, the rollout step would
likely be re-implemented against MLX-LM or Ollama; the vLLM-specific code in `Utils/rollout.py` is reference-only on
Apple Silicon. This is a tractable port (the rollout interface is a simple "given prompt, return k candidates"
contract) but is yet-another implementation step.

**LLaMA-Factory fork as a foreign substrate.** Linus's preferred Phase 6 fine-tuning toolchain is MLX-LM-FT (Apple-
Silicon-native LoRA/full fine-tuning) plus the broader MLX ecosystem. The SALV LLaMA-Factory fork is PyTorch-based,
optimized for CUDA/Linux, and is the largest single piece of vendored code in the repo. Adopting it directly into
Linus would mean carrying a non-MLX training substrate, which conflicts with the **public-APIs-only** principle
(DEC-0027) — LLaMA-Factory is a public framework but it's not the Apple-Silicon-native one. The selective-loss patch
is small and self-contained; porting it to MLX-LM-FT is the cleaner move.

**Reference-module pairing requirement.** SALV's reward signal requires a reference module paired with each prompt
for differential simulation. Pure RLHF (preferences without references) and pure RLVR-with-pytest-oracle don't fit
this shape. For Linus's Worker self-improvement loop on tasks where pytest is the only oracle, SALV's recipe needs
adaptation — either generate "reference" implementations from a strong teacher LLM (Claude Sonnet, GPT-4) before
training, or relax the differential-simulation step to "pass the test suite" granularity (which loses the per-signal
fineness).

**Verilog-specific AST parsing.** The 606-LoC `parser.py` is tightly coupled to Yosys's AST output format and
Verilog's specific signal-dependency idioms (always blocks, case statements, conditional assignments). The patterns
transfer; the code does not. For Python function-aware DPO, the AST→token-span mapper would need to be re-implemented
against Python's `ast` module; for typed-structured-prediction-aware DPO, against the JSON parser.

**SystemVerilog assertions, generate blocks, parameterized modules** — the AST parser focuses on combinational and
basic always-block Verilog; complex generate/parameterize patterns may not parse cleanly. Out of scope for this
release.

**Out-of-distribution Verilog idioms** — analog mixed-signal, asynchronous-design, formal-verification idioms — are
unaddressed by both the training corpus (CodeV) and the AST parsing.

## 6. Recommendation: **Study**

SALV is a high-quality methodology reference and a tractable Phase 6/7 reproduction target, but it is not a
direct-integrate candidate for Linus. Three reasons:

First, the substrate is PyTorch + LLaMA-Factory + CUDA-leaning, not MLX-native. Adopting SALV directly would mean
carrying a non-Apple-Silicon-native training stack into Linus — at odds with the **public-APIs-only / Apple-Silicon-
native** principle (DEC-0027). The right move is to lift the **methodology** (selective-loss DPO; substructure-aware
preference pairs; partial-correct-sample filtering) into Linus's MLX-LM-FT-based Phase 6 lane, not to vendor the
LLaMA-Factory fork.

Second, SALV's reward derivation is **reference-paired differential simulation**, not the pytest-oracle / verifiable-
rewards shape that Linus's Worker self-improvement loop most naturally consumes. The recipe is adaptable to
pytest-oracle tasks (function-aware DPO with pytest-pass-as-correctness), but the adaptation is non-trivial and
should be designed against Linus's actual Worker-task distribution rather than back-ported from Verilog.

Third, the cluster home for SALV (g12-llm-hardware-design, pending — see
[`../specs/qimeng-category-promotion.md`](../specs/qimeng-category-promotion.md)) is methodology-only for Linus.
Verilog generation is not a Linus skill class; the value is in what SALV teaches about preference optimization for
structured outputs, which generalizes far beyond Verilog. A "Study + adopt methodology in Phase 6/7" verdict matches
the cluster's role.

Concretely: Phase 6 / Phase 7 should carry forward the **signal-aware-DPO recipe** (substructure oracle + token-span
mask + selective DPO loss) and **partial-correct-sample filtering convention**, implemented against MLX-LM-FT for
Apple-Silicon-native training. The SALV repo is the open-source reference for what the recipe looks like end-to-end;
the LLaMA-Factory fork is the existence proof that the loss customization is feasible on a public framework. Both are
study-grade, neither is integrate-grade.

A modifier: high prior on later **Adapt** if Linus needs Verilog or HDL skills as a Phase 7+ skill class for any
hardware-coupled experiment (Linus-flavored Apple-Silicon accelerator design, FPGA prototyping, etc.). At that point
the released model + dataset + training recipe become a tractable Phase 6 reproduction target with bounded scope; the
recipe is well-documented enough to follow end-to-end.

## 7. Questions for Dan

1. Is the QiMeng-family **signal-aware-DPO recipe** worth adopting as Linus's Phase 6 default for substructure-aware
   fine-tuning, with a Linus-internal MLX-LM-FT implementation? The methodology generalizes (function-aware DPO for
   Python, field-aware DPO for typed-structured-prediction outputs per CLAUDE.md S25); SALV is the open-source
   existence proof that it works at 7B scale and matches 671B-scale baselines on the trained domain. Worth seeding
   as `_Seed: DEC-NNNN_` in the cluster's promotion spec.

2. Should Linus's Phase 6 training-recipe library carry **selective-objective** as a first-class abstraction —
   `(token_mask, objective_fn) -> masked_objective_fn` — so SFT, DPO, GRPO, PPO all consume the same mask source?
   SALV demonstrates this for DPO; the same masking pattern applies wherever per-token-span correctness can be
   derived. The abstraction would be a Linus-internal convention that downstream training recipes (function-aware,
   field-aware, signal-aware, section-aware) all instantiate.

3. Is **SALV-on-Apple-Silicon** worth pursuing as Linus's first end-to-end RL fine-tune reproduction in Phase 6/7?
   The bounded scope (7B base, 350k pairs, ~7000 LoRA steps, public model + dataset, well-documented recipe) makes
   it a tractable methodology-validation target. The byproduct — a working substructure-aware-DPO implementation in
   MLX-LM-FT — is reusable far beyond Verilog. The cost is the iverilog/yosys macOS build and the LLaMA-Factory→
   MLX-LM-FT loss port. _Seed: DEC-NNNN (SALV-on-Apple-Silicon Phase 6/7 reproduction target)._

4. Should "**always filter heterogeneous-quality data at the substructure level when an oracle exists**" become a
   CLAUDE.md convention for the Phase 6 fine-tuning lane? SALV's ablation table is a striking single demonstration
   of this — partial-correct mixing _hurts_ without filtering, _helps_ with filtering. The cost is the substructure-
   oracle plumbing; the benefit is reliably positive ROI from partials that would otherwise need to be discarded.
   For domains where substructure oracles are easy (Verilog signals, Python functions, typed-prediction fields), this
   seems like a no-brainer convention; for free-form prose, it doesn't apply. Worth codifying explicitly.

5. SALV requires a **paired reference implementation** for each prompt (for differential simulation). For Linus's
   Worker self-improvement loop where the only oracle is `pytest` pass/fail (no paired reference), does SALV's
   recipe degrade gracefully — i.e., can the contrast-signal construction be replaced by per-test-case-pass/fail
   spans? Or does the recipe fundamentally require the reference pairing for fine-grained signal extraction? Worth
   modeling before committing to SALV-style as the Phase 7 self-improvement substrate; the alternative is module-
   level (function-level) RLVR per CodeV-R1, which has the per-task pass/fail granularity but loses the signal-level
   refinement.

6. The `parser.py` AST→code-segment mapper is the most complex single piece of the repo. For a Python function-aware-
   DPO port, would it be cleaner to (a) re-implement against Python's `ast` module, or (b) skip the AST step entirely
   and use simpler regex-based function-boundary extraction (Python's `def`/`class` boundaries are far more
   syntactically clean than Verilog's always-block boundaries)? The simpler path likely suffices for Python; the
   AST-based path is the fallback if the simple one breaks on edge cases (decorators, nested functions, async).
