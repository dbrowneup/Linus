# autoresearch (`karpathy/autoresearch`)

## 1. Purpose and scope

autoresearch is Andrej Karpathy's small, deliberately-constrained rig
for autonomous LLM research: give an AI agent a single training file
(`train.py`) and a 5-minute wall-clock time budget per experiment,
then let it iterate overnight — modify code, retrain, check whether
validation bits-per-byte improved, keep or discard, repeat. The
training code is a stripped-down single-GPU port of nanochat. The
*interesting* file isn't `train.py` (which the agent edits) but
`program.md` (which the *human* edits) — a Markdown "skill" describing
how the agent should operate. At ~12 experiments per hour and ~100 per
overnight run, this is a concrete, minimal demonstration of agentic ML
research. For Linus this is the canonical pattern to steal for Phase
6d (flash-streaming eval) and Phase 7c (inference experimentation),
and a sibling of the flash-moe methodology.

## 2. Architecture summary

Three files that matter, plus a `pyproject.toml`. `prepare.py` handles
data prep (downloads training data, trains a BPE tokenizer) and
runtime utilities (dataloader, evaluation) and is never modified.
`train.py` is the single agent-editable file: full GPT model (Muon +
AdamW optimizer), training loop, all hyperparameters exposed at the
top. `program.md` is the agent's instruction sheet — a compact "skill"
telling it what the metric is (val_bpb, lower is better, vocab-size-
independent for fair architectural comparisons), what the budget is
(5 minutes wall clock), how to iterate (edit `train.py`, run, check,
keep-or-revert). Platform support is explicit: requires a single
NVIDIA GPU (tested on H100), Python 3.10+, `uv`. The author lists
four notable forks for other platforms (MacOS, MLX, Windows RTX, AMD);
the MLX fork (`trevin-creator/autoresearch-mlx`) is the Apple Silicon
relevant one and is already cloned into `repos/autoresearch-mlx/`.

## 3. What's reusable in Linus

The *pattern* is the reusable artifact, and it is extremely reusable:
one small editable file + one metric + one time budget + keep-or-revert
by git + a Markdown "skill" describing the loop. This maps directly
onto the flash-moe experiment log (90 experiments, 42% discarded) and
is the template for Phase 6d's overnight fine-tuning sweeps and Phase
7c's tokens/sec-target optimizer. The `program.md` pattern also lines
up perfectly with Linus's Phase 7 `SKILL.md` plans — autoresearch is
essentially a minimal working example of "Linus skill as autonomous
loop." The MLX fork (autoresearch-mlx) is the pathway to running this
same methodology on Dan's hardware without waiting for a Linux + NVIDIA
box.

## 4. What's inspiration only

The narrative framing ("one day, frontier AI research used to be done
by meat computers…") is a reminder that Linus's trajectory isn't just
about building a useful local assistant — it's about building an
infrastructure where experimentation is cheap enough that Dan can
treat research as a background process. That's the Phase 7c north star.

## 5. What's incompatible or out of scope

Upstream requires an NVIDIA GPU. The Apple Silicon path is via
`autoresearch-mlx`, the fork already sitting in `repos/`. Even so, a
5-minute budget on H100 is not the same as a 5-minute budget on M1
Max: training-loop convergence rates at that time scale will be much
worse, so the "hyperparameters worth searching" and "plausible val_bpb
improvements per 5 minutes" look quite different. Several README
recommendations (switch to TinyStories, lower `DEPTH`, lower
`MAX_SEQ_LEN` to 256, drop `TOTAL_BATCH_SIZE` to 2^14) address exactly
this. For Linus's real workflows the budget should probably be longer
(30 min – 2 hr) and the targets should be Dan-task-suite scores
rather than raw val_bpb.

## 6. Recommendation: **Study upstream, integrate the MLX fork
experimentally**

Do not use the upstream repo directly — the CUDA dependency and
5-minute/H100 budget don't match Linus's reality. Do use
`autoresearch-mlx` (already cloned) as the Phase 6d and Phase 7c
prototype. Concretely: in Phase 6, adopt the `program.md` + single-
edit-file + fixed-budget + keep-or-revert loop as the template for
overnight LoRA sweeps (agent edits a single `lora_config.py`, runs
training, compares to baseline on Dan task suite, keeps or reverts
via git). In Phase 7c, adopt the same loop for inference
experimentation with tok/s-target.

## 7. Questions for Dan

- **First real use of autoresearch methodology.** Phase 6d or Phase
  1b's pmetal evaluation? The pmetal LoRA trial is a natural first
  loop: Maestro (me, or you + me) writes the `program.md`, Worker
  iterates overnight, we wake up to a benchmark table. Low risk,
  exercises the whole Maestro/Worker protocol on real work.
- **Metric for Linus's loops.** Karpathy uses val_bpb for its
  architecture-fairness. Linus's analogue is Dan task suite score,
  which is higher-variance and slower-per-evaluation. Are we willing
  to lengthen the per-experiment budget (30 min+) to get the
  higher-signal metric, or keep short loops on proxy metrics?
- **`program.md` as SKILL.md.** autoresearch's `program.md` is
  essentially a lightweight skill. Promoting it to the Anthropic
  `SKILL.md` convention makes it portable between Claude Code and
  Linus. Worth doing in Phase 7, or premature?
- **Read the Karpathy tweets linked in the README.** Short. Likely
  contain framing worth surfacing in VISION.md if you want Linus to
  inherit some of the "research org as code" posture explicitly.
