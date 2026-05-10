# transcriptformer (`czi-ai/transcriptformer`)

## 1. Purpose and scope

TranscriptFormer is the official Chan Zuckerberg Initiative reference implementation of the cross-species generative
single-cell foundation model published in Pearce et al., _Science_ 2026 (paper-note
[`../paper-notes/science.aec8514.md`](../paper-notes/science.aec8514.md)). The repository ships three trained model
variants — **TF-Sapiens** (57M human cells, ~368M trainable params), **TF-Exemplar** (110M cells across human + 4 model
organisms, ~542M trainable params), and **TF-Metazoa** (112M cells across 12 species spanning 1.53 Bya of evolution,
~444M trainable params) — plus an inference-focused Python package, a `transcriptformer` CLI, two demonstration
notebooks, and a stand-alone preprocessing pipeline for generating ESM-2 protein embeddings for new species. It is the
operational artifact that lets Linus actually run the cellular-transcriptomic specialist Worker pattern that the paper
describes; without this repo, TranscriptFormer would be a paper-only reference.

For Linus this is the second cell-level biological foundation model in the corpus (after ProtiCelli), and the first that
ships a fully open inference path with explicit MPS device support advertised at the CLI level. It is a Phase 7
specialist Worker candidate — the cross-species cell-typing / disease-state / contextualized-gene-embedding tool —
sibling to LucaOne (sequence-level generalist), Bacformer (bacterial-genome specialist), and ProtiCelli (cellular
imaging specialist).

## 2. Architecture summary

The repo is structured for inference and downstream analysis, not training: the `src/transcriptformer/` package has no
training loop. The model package (`src/transcriptformer/model/`) defines the 12-block transformer encoder (`model.py`),
expression-aware multi-head self-attention with count-bias terms (`layers.py`), causal masking (`masks.py`), the
gene-categorical + zero-truncated-Poisson count loss heads (`losses.py`), and a small `embedding_surgery.py` module that
handles swapping ESM-2 embedding tables when running inference on a species not seen during training. Inference is
orchestrated through PyTorch Lightning (`inference.py` in both `model/` and `cli/`), with a Hydra-driven configuration
substrate (`conf/inference_config.yaml`) and a `transcriptformer` CLI exposing three commands: `download` (S3-fetched
checkpoints, three model variants + 24 species' ESM-2 embedding packs), `download-data` (CellxGene Census driver pulling
H5AD shards for arbitrary species), and `inference` (run forward, emit cell embeddings or contextual gene embeddings).
The data layer (`src/transcriptformer/data/`) implements a backed-read OOM-safe DataLoader compatible with
DistributedSampler for multi-GPU work, and the `tokenizer/` package handles cell-sentence construction from H5AD inputs.
The `preprocess/` directory is a separate ESM-2 embedding-generation pipeline for adding species not in the pre-built
embedding pack — useful when a downstream user wants to run TF-Metazoa on a species whose ESM-2 embeddings are not yet
released. Pinned dependencies are heavy (torch 2.5.1 specifically, anndata 0.11.4, scanpy 1.11.2, hydra-core 1.3.2,
cellxgene-census 1.17, pytorch-lightning 2.5.1) and the README explicitly recommends installing into a dedicated
`uv venv` rather than an existing environment. License is **MIT** (Copyright 2025 Chan Zuckerberg Initiative). Active
maintenance: v0.6.1 released 2025-11-06, with a sustained release cadence (v0.4 → v0.5 → v0.6 across summer/fall 2025).
The two demonstration notebooks (`notebooks/celltype-classification-across-species.ipynb`,
`notebooks/contextual-gene-embeddings.ipynb`) are the primary onboarding documentation beyond the README and reproduce
the paper's main downstream tasks.

## 3. What's reusable in Linus

The most directly reusable artifacts are the **three trained checkpoints plus their ESM-2 embedding packs**, deployed
via the CLI behind a thin Linus tool wrapper. The exposed surface is well-defined:
`transcriptformer inference --checkpoint-path ./checkpoints/tf_<variant> --data-file <h5ad> --emb-type {cell,cge}`
covers the cell-typing, disease-state-classification, and contextualized-gene-embedding use cases without writing any
new model code. The `--device mps` flag is advertised in the CLI documentation, which makes this the first Group A bio
foundation model in the Linus corpus with explicit Apple-Silicon support documented at the deployment layer rather than
left as an empirical question — Phase 1 recon need only verify the flag works correctly, not engineer the path itself.
Per **DEC-0046** (`external_api_tool` registry deployment field), the natural Linus tool tag is **local-only**: weights
download once via S3 (~2-4GB per variant, ~10GB for all three plus the all-embeddings pack), no network call required at
inference time. Per **DEC-0048** (`model_prediction` first-class KB edge class), TranscriptFormer outputs are immediate
candidates for the KB: TF → target-gene PMI scores (the "virtual instrument" prompt described in the paper) become
statistically-tagged `model_prediction` edges in a KB query layer alongside experimentally- grounded STRING / KEGG
edges; cross-species cell-type-homology cosine similarities (sponge choanocyte ↔ frog Rohon-Beard neuron, yeast →
vertebrate-progenitor) become similarity edges with explicit model provenance. The **embedding_surgery.py** logic —
running TF-Metazoa or TF-Exemplar on a species not present in the original training set by swapping in a
freshly-generated ESM-2 embedding pack — is the operationally novel piece: it means that for any species with a
sequenced proteome, Linus can (in principle) run the model end-to-end without needing the original CZI team to release
support for that species. For Dan's algal / fungal applications this matters disproportionately, since the 12-species
training set covers neither green algae nor most fungi beyond yeast.

The **gene-token-from-frozen-pLM-embedding pattern** is also a transferable architectural recipe rather than a runnable
artifact: the lesson generalizes to any future Linus-trained model where token identities have an external semantic
representation, and the `tokenizer/` substrate is small and readable enough to repurpose into other contexts
(chemical-structure tokens initialized from SMILES embeddings, function tokens initialized from docstring embeddings).

## 4. What's inspiration only

The training pipeline does not ship in this repo at all — there is no `train.py`, no PyTorch Lightning training loop, no
data-shard-creation utility for the 112M-cell pretraining corpus. The CZI authors did the pretraining on their internal
cluster and released only the inference artifacts. This is the right deployment posture for Linus (retraining was never
going to happen on M1 Max), but it means the repo is a black box for any pretraining-related question. Likewise, the
**multi-GPU DDP inference path** (`--num-gpus N`, recommended for >100k cells) is a useful existence proof that the
model parallelizes cleanly, but Linus does not have multi-GPU on a MacBook Pro and the single-GPU / MPS / CPU paths are
what Linus will actually exercise. The **CellxGene Census bulk-download driver** (`bulk_download.py`) is a polished
implementation of "fetch shards of single-cell data from a public registry by species name," which is methodologically
interesting for any future Linus skill that bulk-fetches biological data on a species-named API surface but is not
infrastructure Linus consumes. The **Hydra configuration substrate** is heavyweight relative to what a Linus tool
wrapper actually needs — most tool calls will pass three or four parameters (checkpoint path, h5ad path, output path,
embedding type) and do not benefit from a full Hydra config tree; a thin Linus wrapper should expose the small parameter
surface directly.

## 5. What's incompatible or out of scope

The pinned dependencies are **heavy and opinionated** — `torch==2.5.1` (with the explicit warning in the README that
2.6.0+ causes pickle errors), `cellxgene-census==1.17`, `anndata==0.11.4`, `scanpy==1.11.2`, `pytorch-lightning==2.5.1`,
plus a long tail of test/build dependencies. Per **DEC-0024** (disposable uv envs for experimental packages),
TranscriptFormer **must** install into its own `uv venv`, not the linus conda env: the torch pin alone collides with
whatever Linus uses elsewhere, and the cellxgene-census bulk-download driver pulls in boto3 / pynvml that are out of
place in a general-purpose env. The README's strong "use uv" recommendation aligns with Linus's existing posture; this
is not a friction. **Apple-Silicon-specific concerns**: `pynvml` (NVIDIA-only) is a hard dependency for some monitoring
paths; the codebase falls back when CUDA is unavailable, but the dependency itself is unconditionally pulled in by
`pip`. The README documents the device flag includes `mps` as an option but the published benchmarks (in the paper, in
the README, in the CHANGELOG) all reference NVIDIA A100 40GB or 16GB-fallback CUDA hardware — no CZI-published number
exists for M1 Max latency / throughput / numerical correctness, which is the load-bearing empirical question for Phase 1
recon. The paper text explicitly notes that some PyTorch ops used in the count-aware attention may be CPU-only on MPS in
older PyTorch builds; the explicit `--disable-compile-block-mask` flag in the CLI hints that block-mask compilation has
CPU/debug fallbacks for exactly this reason. Pretraining or large-scale fine-tuning on M1 Max is **out of scope** — the
CZI training cluster footprint is well beyond Phase 6 LoRA range, though small LoRA adapters on the released checkpoints
are plausibly tractable. The `download-data` CLI command pulls multi-gigabyte shards from CellxGene Census, which is
fine but not a fit for the Linus sandbox without explicit user opt-in for the network operation. Repo activity is
moderate: 18 top-level entries, single-organization maintainer (CZI), recent v0.6.x cadence — appropriate for a Study
verdict but not yet for Integrate-as-service.

## 6. Recommendation: **Study (with a high prior on later Integrate as a Phase 7 specialist Worker)**

TranscriptFormer is the most operationally polished cross-species single-cell foundation model in the Linus repo
collection and the first to advertise MPS device support at the CLI level. It is the natural cell-level transcriptomic
specialist for the Phase 7 biology skill class — sibling to LucaOne (sequence-level generalist), Bacformer
(bacterial-genome specialist), and ProtiCelli (cellular-imaging specialist) — and an obvious source of
`model_prediction` edges (DEC-0048) for the KB once the cellular-data substrate is in place. Concrete Phase 1-2 recon
path: in a disposable `uv venv` per DEC-0024, download `tf_sapiens` plus the `homo_sapiens_gene` embedding pack
(~2-4GB), run the `celltype-classification-across-species.ipynb` notebook end-to-end with `--device mps` on a small
held-out h5ad shard from Tabula Sapiens 2.0, capture wall-clock + memory + correctness-vs-CPU in
`benchmarks/results/<date>-transcriptformer-mps.json`. If MPS produces numerically-correct outputs at practical speeds
(10k cells in single-digit minutes is the bar; 100k cells in <30 minutes is comfortable), TranscriptFormer becomes a
Phase 7 skill candidate with TF-Sapiens as the human-disease default and TF-Metazoa as the cross-species default; tag
the deployment as `external_api_tool: local-only` per DEC-0046. If MPS underperforms or has numerical-correctness
issues, demote to a CPU-fallback skill and reconsider remote-API deployment (Phase 8+ research direction, not Phase 1-2
critical path).

Biosecurity note per **DEC-0047** (three-tier policy, accepted 2026-05-06): cell-type classification, embedding
extraction, and contextualized-gene-embedding outputs stay at Tier A (standard sandbox, no special review). The
generative "virtual instrument" interface — TF → target-gene PMI prompting on TF-Sapiens — sits closer to Tier B when
prompted at cell types relevant to dual-use perturbation engineering (immune-cell TF networks for pharmaceutical or
biodefense purposes); recovering canonical STRING relationships is benign, generating speculative TF → target
predictions in pathogen-host-cell contexts warrants explicit Dan sign-off and audit-log entry. The dividing line should
be clarified before the virtual-instrument interface is exposed as an agentic-executable Linus tool; sit at
"embeddings + classification only" (Tier A) until then.

## 7. Questions for Dan

1. **MPS viability — the load-bearing question.** The README advertises `--device mps` but no published benchmark
   confirms numerical correctness or competitive speed on M1 Max. The first concrete Phase 1 spike is "TF-Sapiens on a
   10k-cell Tabula-Sapiens-2.0 shard, MPS vs CPU, capture in `benchmarks/results/`." Worth assigning to a Worker with a
   one-page spec, or worth deferring until the broader Phase 1 bio-FM-MPS battery is being run?

2. **Variant default for Linus.** TF-Sapiens (human-only, narrowly specialized), TF-Exemplar (human + 4 model organisms,
   generalizes well to mammals), TF-Metazoa (12-species, full cross-kingdom range). For your task distribution —
   LanzaTech metagenomics is bacterial, but the cellular-FM use case at LanzaTech or in your academic / biotech network
   is plausibly fungal-host or algal — does TF-Metazoa win because it's the only variant that includes yeast and
   Plasmodium, or is the biological distance to most LanzaTech-relevant species (especially algae) too large for any of
   the three? The 1.53 Bya training set notably **excludes** all green algae, all land plants, and all archaea, which is
   a structural gap for non-animal applied biotech work.

3. **`embedding_surgery` — does it work for arbitrary species?** The repo's embedding-surgery logic is the operationally
   novel piece: in principle, any species with a sequenced proteome can be added at inference time by generating fresh
   ESM-2 embeddings via the `preprocess/` pipeline. For _Botryococcus braunii_ or any other Dan-relevant
   non-CZI-supported species, what does the end-to-end add-a-species path actually require? Is it a Worker-spec-able
   task or does it need real biological judgment in selecting reference transcript sets per species?

4. **`model_prediction` edge-class scope.** Per DEC-0048, TF → target-gene PMI edges and cell-type-homology edges are
   first-class candidates for the KB. Should Linus eagerly publish these into KB whenever a TranscriptFormer query runs
   — every cell-typing query produces O(thousand) provisional cross-species homology edges — or should publication be
   gated on explicit user request? The signal-to-noise ratio matters; the answer probably depends on whether KB queries
   surface model-prediction edges by default.

5. **Phase 6 LoRA candidate.** TF-Metazoa's 302M active parameters at inference are within LoRA-on-M1-Max range. A
   Dan-corpus fine-tune on a private collection of fungal or algal scRNA-seq (or environmental metatranscriptomics,
   where bacterial signal mixes with eukaryotic signal) could fill the training-data gap that TF-Metazoa structurally
   has. Worth scoping as a Phase 6 candidate alongside LucaOne+Dan-corpus and language-model fine-tunes, or strictly out
   of scope until Phase 7 inference is confirmed to work on Apple Silicon?

6. **Generative virtual-instrument interface — Linus tool now or defer?** The TF → target-gene PMI prompt is
   well-defined methodologically (the paper provides the recipe) but is not exposed as a single CLI flag in v0.6.1; it
   requires custom code over the model's autoregressive log-probabilities. Wrapping it as a Linus tool is
   straightforward in principle but raises the Tier-B biosecurity question above. Is the right Phase 7 scope
   "embeddings + classification (Tier A)" only, with the virtual-instrument interface deferred to Phase 7+ once the
   biosecurity dividing line is clarified?

7. **Output-channel schema for cellular-data KB.** TranscriptFormer outputs naturally fall into three classes — cell
   embeddings (continuous, dense, retrieval-friendly), cell-type labels (discrete, classifier output), and TF-target PMI
   scores (continuous, statistical). Should the KB carry all three or only the discretized predictions? The continuous
   embeddings are the most information-rich and the most expensive to store; the discretized labels are the most
   queryable. This decision touches DEC-0048 directly and should probably be made before the first cellular-data
   ingestion lands.
