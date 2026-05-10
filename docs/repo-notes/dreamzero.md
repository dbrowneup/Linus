# dreamzero (`dreamzero0/dreamzero`)

## 1. Purpose and scope

The DreamZero release repo is NVIDIA GEAR Lab's open-source implementation of the **World Action Model** described in
[`docs/paper-notes/2602.15922v1.md`](../paper-notes/2602.15922v1.md): a 14B autoregressive flow-matching diffusion
transformer built on top of Wan2.1-I2V-14B-480P that jointly predicts future video frames and continuous robot actions
for closed-loop control of bimanual manipulation robots (AgiBot G1, Franka, YAM). The repo bundles three deployable
artifacts: pretrained checkpoints (DreamZero-DROID, DreamZero-AgiBot) on HuggingFace; a distributed-inference WebSocket
server (`socket_test_optimized_AR.py`) tuned for multi-GPU GB200/H100 deployment with DiT caching, NVFP4 quantization,
and TensorRT-on-Blackwell paths; and a full training codebase (Hydra + DeepSpeed ZeRO-2) capable of reproducing the
DROID checkpoint or post-training onto a new embodiment from ~30 minutes of play data. Apache 2.0. The project topped
both RoboArena and MolmoSpaces leaderboards as of 2026-02-27 — DreamZero-DROID, trained _from scratch_ on DROID alone
with no large-scale robot pretraining, is currently #1 on the open robotics policy benchmarks. For Linus this is **a
watch-the-frontier datapoint**, not a deployment target: robotics is outside the Phase 1–6 scope, and the GPU
dependencies (multi-GPU CUDA 12.9+, Blackwell or Hopper) are structurally incompatible with Apple Silicon.

## 2. Architecture summary

Python 3.11; conda env (`conda create -n dreamzero python=3.11`); PyTorch 2.8+ with CUDA 12.9+. Hard dependencies
include `flash-attn` (no Metal backend), `transformer_engine[pytorch]` (GB200 only, optional for H100), and
`tensorrt==10.13.2.6` (GB200-only fast path with `LOAD_TRT_ENGINE` env var). Repo layout: top-level
`socket_test_optimized_AR.py` is the server entrypoint; `test_client_AR.py` is the smoke test; `groot/` carries the
model code (the "groot" name is a holdover from the GR00T family the GEAR Lab also publishes); `scripts/train/` contains
training launchers (`droid_training.sh`, `droid_training_wan22.sh` for the smaller 5B backbone, plus AgiBot/YAM scripts
referenced in `docs/DATASET_TO_GEAR_AND_TRAIN.md`); `eval_utils/run_sim_eval.py` points the policy at the `sim-evals`
benchmark harness via the hosted API; `debug_image/` is sample inputs. Configuration is Hydra; training uses DeepSpeed
ZeRO Stage 2 with `bf16` and `save_lora_only=true` by default. The inference server uses PyTorch distributed
(`torch.distributed.run --standalone --nproc_per_node=2`) to parallelize classifier-free-guidance forward passes across
2+ GPUs; `--enable-dit-cache` toggles the cosine-similarity-gated velocity caching that compresses 16 diffusion steps
to 4. Training data is ingested as LeRobot v2.0 format; the preprocessed DROID-LeRobot dataset (~131GB) is released on
HuggingFace at `GEAR-Dreams/DreamZero-DROID-Data`. Three camera views (`exterior_image_1_left`, `exterior_image_2_left`,
`wrist_image_left`) are concatenated spatially into a single frame rather than added as architectural complexity.
Default training hyperparameters per the README: `per_device_train_batch_size=1`, `learning_rate=1e-5`, `num_frames=33`,
`action_horizon=24`, `image_resolution=320×176`, `bf16=true`. Inference latency post-warmup: ~0.6s on GB200, ~3s on H100
(the README figures), with the paper claiming 150ms on GB200 once Flash + NVFP4 + TensorRT are all stacked.

## 3. What's reusable in Linus

Honestly: not much, in the direct-port sense. The repo is a robotics policy server requiring multi-GPU NVIDIA datacenter
hardware. Apple Silicon viability is essentially zero for the inference path — `flash-attn` has no Metal backend, the
NVFP4 quantization stack is Blackwell-architecture-specific, and the 14B Wan2.1 backbone at fp16 is ~28GB of weights
which leaves no headroom for the activations needed during diffusion on a 32GB unified-memory M1 Max. What _is_ reusable
is structural and methodological:

- The **closed-loop KV-cache-with-ground-truth-replacement pattern** in `socket_test_optimized_AR.py` (Algorithm 2 in
  the paper) is a reference implementation of the bounded-error stateful-policy pattern that resonates with Linus's
  Layer A/B memory architecture (DEC-0028, DEC-0029, DEC-0036). Reading the inference loop end-to-end is a useful Phase
  2+ exercise even if no code transfers.
- The **decoupled noise scheduling in DreamZero-Flash** is a portable training-time idea: bias one modality's denoising
  timestep distribution toward high-noise via `Beta(α,β)` while keeping the other uniform, training the model to handle
  the train-test mismatch of few-step inference. The conceptual pattern transfers to any multi-modality diffusion
  training where one modality has stronger priors than the other. Phase 6+ stretch applicability if MLX ever becomes a
  serious diffusion-training substrate.
- The **post-training script + 30-minute-play-data adaptation recipe** is the most actionable artifact in the repo — not
  for robotics, but as documented evidence of what data-efficient adaptation looks like when the foundation model is
  doing most of the work. Useful read for any Phase 6 fine-tuning planning, especially when justifying small-data
  approaches to skeptics.
- The **LoRA failure mode is also documented** — the README and the paper both note LoRA gave suboptimal results,
  forcing full DiT updates. This is a useful counterexample to the standard "LoRA is the answer" instinct in fine-tuning
  planning.

## 4. What's inspiration only

The 38× inference-speedup stack (CFG parallelism, DiT caching, `torch.compile` + CUDA Graphs, NVFP4 quantization, cuDNN
attention backend, GPU-side scheduler, decoupled noise schedules) is the most engineering-dense part of the repo and is
worth reading as a case study in how to make a 14B iterative-denoising model real-time. Each component has an Apple
Silicon equivalent in spirit (MLX kernel fusion, mlx-flash quantization, MPS attention backends), but the code does not
port. The DiT-caching trick — gate on cosine similarity between successive flow-matching velocities, reuse cached
velocity when above threshold, drop effective steps from 16 to 4 — is the most directly portable concept; an MLX
implementation would be Phase 6+ research-direction work, possibly relevant if Linus ever explores diffusion-grade MLX
inference.

The **video-model-as-policy framing** is itself the inspiration: the empirical result that a video diffusion backbone,
adapted minimally with action heads, beats VLM-with-action-heads (the dominant paradigm) by 2× on physical
generalization is a load-bearing datapoint for the broader question of "what's the right foundation-model substrate for
action-conditioned tasks." Linus's default assumption is LLM substrates; DreamZero is a forcing function to keep the
question open.

## 5. What's incompatible or out of scope

The hardware floor is the structural barrier. The README is explicit: "Multi-GPU setup (tested on GB200, H100), Minimum
2 GPUs for distributed inference, CUDA 12.9+." None of this is achievable on Apple Silicon. The datacenter GPUs the code
targets are several orders of magnitude more compute and bandwidth than M1 Max. Even reading-only deployment of a
released checkpoint requires GPU rental; even GPU rental costs ~$10–30/hr at the GB200 tier and the warmup phase alone
takes "a few minutes" per the README.

The **dataset scale** is also out of scope: 500 hours of teleoperation, 22 environments, 22 named robot operators in the
acknowledgements is industrial data collection. The DROID dataset is 131GB preprocessed, ~1.7TB raw. Training is not
something Dan or Linus reproduces; even fine-tuning is a multi-GPU exercise.

The **product surface mismatch.** DreamZero outputs continuous robot motor commands. Linus's product surface is a
personal AI for genomics/scientific computing. There is no current Dan workflow this model serves. Dan does not have a
robot, a manipulator, or a fabrication actuator that DreamZero would drive.

The **`flash-attn` dependency** specifically is a hard wall: `flash-attn` requires NVIDIA-CUDA, has no Metal backend,
and is non-optional in DreamZero's pipeline (not just the optional `[faesm]` extra as in Bacformer). The model code path
assumes `flash-attn` is available.

`tensorrt`/`transformer_engine` are GB200-class only and unavailable on macOS regardless of GPU.

The repo is also **young** — 2026-02-19 paper, 2026-02-20 first code release, 2026-02-27 leaderboard claims. Active
development, fast-moving API, expected churn. Not stable enough to pin-and-forget.

## 6. Recommendation: **Watch**

DreamZero is impressive, currently SOTA on the public robotics-policy leaderboards, and an important paradigm datapoint
for the corpus — but it is not reusable in Linus in any Phase 1–6 capacity. Robotics is outside the current scope, and
the GPU dependency surface (multi-GPU CUDA 12.9+, Blackwell-specific NVFP4 path, `flash-attn` non-optional) makes even
inference deployment infeasible on Apple Silicon. The right disposition is **Watch**: track GEAR Lab releases, note when
smaller (~5B) checkpoints with relaxed dependencies appear, and reconsider if Linus's Phase 7+ scope ever opens an
embodied-actor or lab-instrument-automation lane. The companion paper-note
[`../paper-notes/2602.15922v1.md`](../paper-notes/2602.15922v1.md) captures the reusable framings (memory architecture
rhyme, inference-optimization vocabulary, video-model-as-substrate question, idea-to-reality cross-thread); engagement
with this repo should be limited to reading the inference loop in `socket_test_optimized_AR.py` for the
ground-truth-replacement pattern and skimming the training launcher in `scripts/train/` for the data-efficient
post-training recipe. Do not pull dependencies; do not attempt to run on M1 Max. Re-evaluate at the next quarterly
curation review (DEC-0025) if the repo or the GEAR Lab roadmap shifts.

## 7. Questions for Dan

1. **Embodied-actor scope.** DreamZero is the cleanest current evidence that video-backbone-as-policy is the right
   architecture for physical-action generalization. Does Linus's Phase 7+ scope have any room for an "embodied actor /
   lab-instrument automation" destination, or is robotics far enough out that even the destination marker is
   over-claiming? Reading: roadmap says Phase 8 is "Beyond MacBook" — robotics is a candidate for that destination but
   no commitment exists.
2. **GPU-rental engagement, yes/no.** The released checkpoints can be exercised on rented GB200 / H100 instances at
   ~$10–30/hr. Is there value in a one-shot weekend exercise — rent a GB200 for an evening, run the WebSocket server
   against the public sim-evals harness, document the deploy story end-to-end — purely as fluency-building for Phase 7+
   planning? Counterargument: it costs real money and does nothing for Phase 1–6 deliverables.
3. **DiT caching as MLX research direction.** The cosine-similarity-gated velocity caching trick is conceptually
   portable to any iterative-denoising MLX model. Worth scoping as a Phase 6+ MLX research direction — "implement and
   benchmark DiT caching in MLX on a small video diffusion model" — or strictly out of scope until MLX has more
   diffusion tooling? My read: it's a 1-2 week experiment that would generate transferable MLX know-how; not a
   commitment but a candidate.
4. **The inference loop as memory-architecture reference.** The `socket_test_optimized_AR.py` inference loop is a
   reference implementation of the bounded-error stateful policy pattern. Worth a deliberate read-and-write-up exercise
   (1-2 hours) to map the KV-cache-with-ground-truth-replacement pattern onto Linus's Layer A/B memory architecture, or
   is the rhyme too speculative to merit the effort?
5. **Frontier-on-incompatible-hardware tracking discipline.** DreamZero is the second example in the corpus (after
   WHAM-1.6B, which _is_ tractable on M1 Max) of a SOTA result that lives on hardware Linus does not have. Worth a
   recurring discipline — a short index of "frontier results that don't fit on Apple Silicon" — so Dan has a calibrated
   picture of what Linus is and is not relinquishing? Could live as a section in
   [`../landscapes/total-landscape.md`](../landscapes/total-landscape.md) or as a new doc.
6. **NVIDIA GEAR Lab as a coherent thread.** DreamZero plus the parallel-authored EgoScale (`2602.16710v1.md`, same lab,
   same paper drop date) plus prior GR00T work suggest the GEAR Lab is producing a coherent embodied-AI thread worth
   tracking. Is there value in the corpus carrying a small "NVIDIA GEAR Lab" landmarks doc — analogous to the QiMeng
   family treatment in llm-hardware-design — or is the relevance low enough that two paper-notes plus this repo-note
   suffice?
