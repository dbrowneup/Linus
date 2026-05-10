# ProtiCelli (`CellProfiling/proticelli`)

## 1. Purpose and scope

ProtiCelli is the official release implementation accompanying the Stanford / CMU / KTH / CZ Biohub bioRxiv preprint
[2026.03.31.715748v1](../paper-notes/2026.03.31.715748v1.md): a deep generative model that synthesizes single-cell
immunofluorescence (IF) microscopy images for **12,800 human proteins** across 39 cell lines, conditioned on three
landmark stains (microtubules, nucleus, ER). The repo packages a ~458M-parameter Diffusion Transformer Large (DiT-L)
trained under the EDM (Elucidating Diffusion Models) framework with a Stable Diffusion 3.5 VAE for latent-space
encoding, plus a complete preprocessing pipeline, a fine-tuning loop, downloadable checkpoints, and — unusually for a
biology-paper release — a clean LLM-agent tool registry (`agent_tools.py`) with explicit Anthropic / OpenAI adapters in
the README. For Linus this is the **imaging-microscopy specialist** in a Phase 7 specialists-as-Workers panel: Bacformer
at the whole-bacterial-genome level, Evo 2 at the DNA level, ProtiCelli at the spatial-proteomics imaging level. The
repo is small, opinionated, MIT-licensed, and ships an interface that already looks like a Linus tool.

## 2. Architecture summary

The package is `proticelli/` with five subpackages: `models/` (the DiT architecture and a basic transformer-block
implementation), `schedulers/` (the EDM noise scheduler), `data/` (preprocessing transformers plus pickled protein and
cell-line vocabularies — `antibody_map.pkl`, `cell_line_map.pkl`), `config/` (an `EDMConfig` dataclass and a default
training argparse config with EDM constants), and `utils/` (checkpoint helpers, download logic, EDM math, logging).
Three top-level modules anchor the public surface: `model.py` (862 lines — the `Model` class with `predict()`, `fit()`,
`save()`, `validate_inputs()`, `download_checkpoints()`, plus the `PredictionResult` helper), `_sampling.py` (the EDM
denoising loop, 50 steps default), and `_training.py` (the fine-tuning loop with classifier-free guidance via
`label_dropout_prob=0.2`, cosine LR schedule, optional EMA, mixed-precision support). The DiT-L backbone has 28
transformer blocks, 16 attention heads at head dimension 72 (D=1152), processes 32×32 patches in a 64×64 latent space
(patch size 2×2), and conditions on (protein-id, cell-line-id, timestep) via six adaptive-normalization parameters per
block (shift, scale, gate for both attention and FFN paths). Inputs are 4-channel 512×512 TIFFs at the HPA pixel size of
**0.1067 µm/px**: channel 0 microtubules, channel 1 protein, channel 2 nucleus, channel 3 ER (channel 1 is filled with
zeros at inference). The preprocessing pipeline is three composable transformers: `ChannelAssembler` (build a 4-channel
stack from per-channel files or arrays, with a `has_protein` flag for inference vs training), `ImageNormalizer` (clip at
the MT-channel 99.95th percentile, divide all channels by that, rescale to [-1, 1], with per-channel fallback for
low-MT-intensity edge cases), and `ResolutionResampler` (bilinear rescale to 0.1067 µm/px, no-op within 1e-3 µm/px
tolerance). Training defaults: AdamW (β₁=0.95, β₂=0.999, weight decay 1e-6), lr 1e-4, batch size 16, cosine LR with 500
warmup steps, label dropout 0.2, EMA optional. The device default is `"cuda"` then `"cpu"` — no MPS-specific handling,
but no CUDA-only ops either; the question of MPS viability reduces to whether PyTorch's MPS backend handles the DiT +
EDM + SD 3.5 VAE composition. The `agent_tools.py` module exports `PROTICELLI_TOOLS` (a list of four JSON-Schema tool
definitions — `validate_inputs`, `predict_from_files`, `search_proteins`, `list_cell_lines`) plus a `run_tool`
dispatcher; the README shows the one-line conversion to Anthropic's `input_schema` shape and OpenAI's
`{"type": "function", "function": ...}` shape. Dependencies are `torch>=2.0`, `diffusers>=0.25.0`, `accelerate`,
`transformers`, `tifffile`, `numpy`, `pandas`, `scipy`, `Pillow`, `torchvision`, `timm`. Optional `[train]` extra adds
tensorboard + wandb. Checkpoints (DiT `unet/` for inference, `unet_ema/` for fine-tuning, plus the SD 3.5 VAE) are
downloaded from the Stanford ELL vault via `Model.download_checkpoints()` on first use. Top-level `quickstart.ipynb`
walks through the prediction pathway end-to-end. License: MIT.

## 3. What's reusable in Linus

The full public API is the obvious target — `Model`, `ChannelAssembler`, `ImageNormalizer`, `ResolutionResampler`, the
`PROTICELLI_TOOLS` registry — wrapped behind a `linus.skills.proticelli` Phase 7 tool. The shape maps cleanly onto the
[typed-structured-prediction convention](../../CLAUDE.md): the wrapping returns a `SubcellularLocalizationPrediction`
record with the generated image, predicted-organelle distribution (computable from the released SubCell embeddings the
paper uses), confidence, evidence (prompt landmarks + model checkpoint hash + cell-line conditioning), and a free-text
rationale field. The `agent_tools.py` JSON-Schema definitions are directly usable as the schema spec for a fastmcp-based
Linus MCP server (per [DEC-0045](../adr/0045-fastmcp-mcp-framework-default.md)) — Linus shouldn't vendor
`agent_tools.py` wholesale (the PROTICELLI_TOOLS schemas don't account for Linus's session/audit context) but they're a
strong reference. The `model.fit()` API is fully exposed and clean — fine-tuning on a small custom dataset (e.g. Dan's
own microscopy data, a bespoke cell line, a perturbation series) is a single function call with cosine LR,
classifier-free guidance, and EMA built in; this is the **lab-in-the-loop** pattern the paper demonstrates with the
FUCCI cell-cycle fine-tune, and it's plausibly tractable on M1 Max in mixed precision (Phase 6 demo candidate). The
`validate_inputs()` pre-flight pathway is exactly the right shape for Linus's input-validation Worker pattern — it
returns errors, warnings, and resolved (possibly auto-corrected) names without loading any weights, which means Linus
can validate user input cheaply before paying the inference cost. Per DEC-0048 each ProtiCelli prediction maps to a
`model_prediction` edge in the KnowledgeBase: protein-id node and cell-line-id node as endpoints; model identifier,
checkpoint hash, and landmark stains as provenance; predicted localization plus confidence as the edge payload; default
`[!unverified]` claim-type tag from DEC-0023. Per DEC-0046 the registry entry's deployment field decides local-Worker vs
external-HTTP/MCP execution — likely a hybrid: local for one-off predictions, remote or batch for Proteome2Cell-scale
synthesis. The released **Proteome2Cell** dataset (30.7M synthetic images, 12 cell lines × 200 cells × 12,800 proteins,
integrated into HPA v26 in September 2026) is a Phase 4 Data Sovereignty mirror candidate, even if Linus never re-runs
ProtiCelli inference locally.

## 4. What's inspiration only

The `_training.py` distributed training loop assumes multi-GPU CUDA and uses HuggingFace `accelerate` — usable as a
reference for how to wire EDM + DiT-L training cleanly, but not infrastructure Linus consumes. The `_sampling.py` EDM
50-step denoising loop is reference reading for any future Linus-native MLX port of a diffusion model — the
preconditioning math (cskip / cout / cin), the σ schedule, and the loop structure are all worth porting cleanly rather
than reinventing. The protein-vocabulary pickle format (`antibody_map.pkl`) is a valid micro-pattern for
closed-vocabulary embeddings in any Linus tool that needs to map biological identifiers to learnable parameters, though
for production Linus would prefer a versioned JSON or YAML vocabulary file with explicit provenance.

## 5. What's incompatible or out of scope

The single most important constraint: **MPS viability is unverified.** The repo defaults to `"cuda"` then `"cpu"`, and
PyTorch's MPS backend has historically had gaps for diffusion-transformer + VAE compositions (silent fallback to CPU on
unsupported ops, occasional numerical differences, no flash-attention equivalent). The DiT-L weights at FP32 are ~1.8 GB
plus ~250 MB for the SD 3.5 VAE — well within 32 GB unified memory at fp16, but the EDM 50-step sampling loop's
activation footprint at 16×64×64 latent batch is the operational unknown. A focused spike (load checkpoints in fp16, run
a single prediction, log wall-clock + memory) is the right Phase 1c-style gate. If MPS works at single-
digit-second-per-image latency, ProtiCelli becomes a local Phase 7 Worker; if "minutes per image but it works", a hybrid
local + remote pattern; if MPS is broken or memory-bound, ProtiCelli is `external_api_tool`-deployed (Stanford ELL
vault, HPA web interface, or a cloud endpoint) per DEC-0046. **Protein vocabulary is closed at 12,800 entries** — the
model encodes proteins through learnable embeddings, not through an ESM-style protein language model, so it cannot
generalize to proteins outside the training vocabulary. For Dan's LanzaTech metagenomics workflow this is the
load-bearing operational limitation: novel proteins from environmental sequencing fall back to a default unconditioned
embedding (silent, no warning) and predictions are unreliable. The authors flag ESM-conditioned embeddings as future
work; until then ProtiCelli is closed-world on the human proteome. **Cell-line vocabulary is closed at 39 entries** —
fallback to a default unconditioned embedding is more graceful (the model is trained with 50% cell-line dropout, so it
knows how to handle "no cell line"), but novel cell lines will not get cell-line- specific localization patterns.
**Vesicular compartments (peroxisomes, endosomes, lysosomes) are intrinsically hard** — all three benchmarked models
fail similarly because the vesicle locations correlate weakly with the three landmark channels. This is a model-class
limitation, not fixable by tuning. **Health-bias** — trained on standard cell lines under normal conditions; CM4AI
drug-perturbation transfer works but more extreme states (CRISPR knockouts, infection, disease tissue) are
out-of-distribution. **No license complications** for use, redistribution, or fine-tune publishing — MIT is the most
permissive open-source license. **Repo maturity** — `version = "0.1.0"`, single PyPI release, single primary maintainer
(Huangqingbo "Paul" Sun, sunh@stanford.edu); expect API churn through the next several releases.

## 6. Recommendation: **Study (with a high prior on later Integrate-as-tool at Phase 7)**

ProtiCelli is the cleanest packaged biology FM in the cloned-repos collection right now — small enough to read end-
to-end, well-documented (the README is unusually complete), MIT-licensed, and with a public-API surface that already
looks like a Linus tool. The high-leverage next step is a focused **Phase 1c-style spike**: a fresh `proticelli` conda
env on M1 Max, `Model.download_checkpoints()`, run the quickstart on the released `example_cell_reference_input/` data,
capture wall-clock + memory + qualitative output in a `benchmarks/results/` JSON. If MPS is workable, ProtiCelli
graduates straight to the Phase 7 imaging-FM specialist Worker. If MPS is broken, the deployment shifts to
`external_api_tool` per DEC-0046 — still useful as a Linus tool, just remote-executed. The closed-vocabulary limitations
are real but they are a feature of the **current** version; the v2 with ESM-conditioned protein embeddings (flagged by
the authors as future work) would be strictly more useful for Dan's metagenomics workflow. Watch for that release. For
the present, Phase 7 deployment with a "human-proteome-only" guardrail and a fallback to remote-endpoint inference for
proteome-scale workloads is the realistic path. The `model_prediction` edge class (DEC-0048) gets its first non-trivial
bulk-import test from Proteome2Cell once HPA v26 ships in September 2026.

## 7. Questions for Dan

1. **MPS spike timing.** The repo is small and the spike is well-scoped (load checkpoints in fp16, run one prediction,
   log timing + memory). Worth slotting into Phase 1c alongside the Bacformer MPS spike, or defer to Phase 7 prep
   specifically?

2. **Closed-vocabulary acceptance.** ProtiCelli's 12,800-protein closed vocabulary is the load-bearing operational
   limitation for any LanzaTech metagenomics use case. Is the human-proteome subset still useful enough to make
   ProtiCelli a Phase 7 deployment now (with a guardrail rejecting novel proteins), or wait for the ESM-conditioned v2
   release before committing engineering time?

3. **Lab-in-the-loop fine-tune as a Phase 6 demo.** The FUCCI cell-cycle fine-tune (~5,000 cells, 50 epochs, exposed via
   `model.fit`) is plausibly tractable on M1 Max in mixed precision — would running it end-to-end through Linus (call
   `fit`, save checkpoint, run new predictions, all logged through the audit trail) be a satisfying Phase 6 demonstrator
   that doesn't depend on LLM fine-tuning being ready?

4. **Proteome2Cell mirror in Phase 4.** Once HPA v26 ships in September 2026, mirroring a per-cell-line subset of
   Proteome2Cell (e.g., HeLa + U2OS + A-431 + HEK293) is on the order of tens of GB on disk — easily tractable on the 1
   TB external SSD. Worth the disk and the bandwidth for offline access, or rely on the HPA web interface and call it
   remotely?

5. **`agent_tools.py` as the Linus-tool schema reference.** ProtiCelli ships a JSON-Schema tool registry with Anthropic
   / OpenAI adapter examples in the README — already shaped like an MCP-server entry. Per DEC-0045 (fastmcp default),
   should the Linus wrapping use ProtiCelli's `PROTICELLI_TOOLS` schemas verbatim as the schema reference (Linus adds
   session/audit context, ProtiCelli stays the same), or rewrite the schemas in Linus's own convention?

6. **The full Phase 7 specialist panel.** ProtiCelli (imaging) + Bacformer (whole-bacterial-genome) + Evo 2 (DNA) +
   LucaOne (DNA + RNA + protein joint) + biophysics PLM (proteins) + TranscriptFormer (transcriptomics) — six
   specialists across five modalities. Five+ tools is a lot. Is that the right Phase 7 ambition, or scope down to the
   three you'd actually use day-to-day for the Phase 7 MVP?
