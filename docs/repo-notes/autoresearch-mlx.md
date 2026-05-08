# autoresearch-mlx (`trevin-creator/autoresearch-mlx`)

## 1. Purpose and scope

autoresearch-mlx is a clean Apple Silicon port of Karpathy's autoresearch loop, with PyTorch + CUDA swapped out for MLX
end-to-end. The protocol is unchanged: one mutable `train.py`, one metric (`val_bpb`), a fixed 5-minute training budget,
keep-or-revert by git, `program.md` as the agent's skill sheet. Where the upstream `autoresearch.md` note had to
recommend "study the pattern, then find a way to run it on Dan's hardware," this port collapses that gap — it runs
natively on M1 Max today via `uv sync && uv run prepare.py && uv run train.py`. For Group 1 (Apple Silicon Inference &
Training) it is the _executable_ sibling of upstream autoresearch and the most immediately useful research-loop
substrate Linus has.

## 2. Architecture summary

Same minimal three-file shape as upstream. `prepare.py` (read-only: data, BPE tokenizer via `rustbpe`, dataloader,
`evaluate_bpb`, `MAX_SEQ_LEN`, `TIME_BUDGET`); `train.py` (agent-editable: a GPT with GQA, sliding-window attention
pattern `"SSSL"`, RoPE, value embeddings, AdamW, 5-minute training loop); `program.md` (the skill — branch-per-run on
`autoresearch/<tag>`, log to `results.tsv`, never `git add -A` because it's monorepo-aware). Dependencies are
deliberately tiny: `mlx>=0.30`, `numpy`, `pyarrow`, `regex`, `requests`, `rustbpe`, `tiktoken` — no torch, no
transformers, no accelerate. The public `results.tsv` walks from a `2.667` AdamW baseline down to `1.807902` in four
commits with one discard; the README's longer-run table reports `1.294526` on M4 Max and a meaningfully different winner
stack (Muon, sharper attention, smaller MLP) on a Mac Mini — exactly the hardware-conditional finding the upstream loop
can't surface from a single H100. Per-experiment wall time on Apple Silicon is ~6–7 minutes (5 min training plus
compile/ eval overhead); MFU reporting is a placeholder because there's no clean Apple Silicon FLOPs reference. The eval
token budget is also intentionally reduced for faster iteration, with the `evaluate_bpb` interface preserved.

## 3. What's reusable in Linus

This is the executable form of the pattern that was "inspiration only" in the upstream note. The rig drops into Phase 6d
as the overnight LoRA sweep substrate with little adaptation — swap `train.py`'s pretraining loop for a LoRA fine-tune
harness against the Phase 6 base model, swap `val_bpb` for a Dan-task-suite proxy or held-out PPL on Dan's corpus, keep
`program.md` and the keep-or-revert discipline almost verbatim. The branch-per-run convention (`autoresearch/<tag>`)
maps cleanly onto Linus's `agent/<task-id>/<slug>` branches in BRANCHING.md and is a worked example of how a Worker
should manage its branch during a long autonomous run. `program.md` itself is the closest thing in the cloned repo
collection to a working Anthropic- style `SKILL.md`, and its monorepo-safety paragraph ("never `git add -A`") is the
paranoid-by-default operational guardrail Phase 7 skills should inherit. The tiny pure-MLX dependency surface also makes
this a useful sanity check for "is MLX actually fast enough on M1 Max?" independent of pmetal's Phase 1b verdict.

## 4. What's inspiration only

The published pretraining recipe (depth-4 GPT, AdamW, `window_pattern="SSSL"`, value embeddings) is interesting as a
reference architecture but isn't a thing Linus needs to consume — Linus isn't going to pretrain its own GPTs from
scratch. The Mac Mini vs M4 Max divergence in the README is the more important takeaway: it confirms that
hardware-tier-conditional optimizer/architecture choices are real on Apple Silicon, which justifies running Phase 6's
autoloops on Dan's actual M1 Max rather than transferring recipes from anyone else's results table.

## 5. What's incompatible or out of scope

The training task (next-token pretraining with `val_bpb`) is wrong for Linus's real goals — Linus cares about
Dan-task-suite scores and KnowledgeBase QA, not bpb on a generic web shard. The _loop_ is directly reusable, the
_payload_ needs replacing before Phase 6d benefits. Second, `program.md`'s "NEVER STOP" posture goes beyond what
SAFETY.md currently allows — it assumes an agent running unattended overnight, committing without supervision; autonomy
tier graduation has to catch up before that's appropriate even on a sandboxed branch. Third, the public `train.py` is
AdamW-only; the README admits the longer working port explored a Muon variant that isn't exposed here, so reproducing
the `1.294526` M4 Max number from public code alone is unlikely.

## 6. Recommendation: **Integrate**

Of the cloned reference repos, this has the highest ratio of "directly runnable on Dan's hardware today" to "new code
Linus must write to benefit." Concrete plan: in Phase 1 finish, run the upstream loop verbatim for one overnight session
on M1 Max as a smoke test — confirm `uv sync` + `prepare.py` + `train.py` actually work, reproduce a couple of rows of
`results.tsv`, get a local feel for the 6–7 min/experiment cycle on Dan's chip. Then in Phase 6d, fork the rig under
`experiments/autoloop/` and replace the pretraining payload with a LoRA fine-tune harness against the Phase 6 base
model, keeping `program.md`, the branch convention, and the keep-or-revert-by-git discipline. Phase 7c reuses the same
shell with a tok/s target instead of a loss target. The upstream autoresearch repo stays study-only; this fork is what
actually runs.

## 7. Questions for Dan

1. **Smoke run timing.** Run the verbatim 5-minute loop now alongside Phase 1b's pmetal evaluation so we have a
   hardware-local baseline on this M1 Max before Phase 6d needs it, or wait until 6d formally opens?
2. **Payload swap for Phase 6d.** Is the first real Linus autoloop a LoRA sweep with held-out PPL on Dan's corpus, or go
   straight to a Dan-task-suite scorer despite the higher per-experiment cost?
3. **Autonomy tier for "NEVER STOP".** `program.md` assumes an agent running unsupervised overnight on its own branch,
   committing freely. SAFETY.md doesn't authorize that today. Is overnight-autonomous- on-an-agent-branch the right
   first graduation step in Phase 7?
4. **Muon variant.** The README hints the working (non-public) port used Muon to reach `1.294526` on M4 Max. Worth
   porting Muon into our fork as the first agent-driven experiment, or stay AdamW-only?
