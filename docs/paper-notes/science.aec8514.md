---
title: "TranscriptFormer: A generative cell atlas across 1.5 billion years of evolution"
source: Science (2026), DOI 10.1126/science.aec8514
authors:
  James D. Pearce, Sara E. Simmonds, Gita Mahmoudabadi, Lakshmi Krishnan, Giovanni Palla, Ana-Maria Istrate, Alexander
  Tarashansky, Benjamin Nelson, Omar Valenzuela, Donghui Li, Stephen R. Quake, Theofanis Karaletsos
affiliation:
  Chan Zuckerberg Biohub (Redwood City); Stanford Bioengineering; Stanford Applied Physics; Chan Zuckerberg Initiative
date: 2026-05-07
pdf: ../../context/papers/science.aec8514.pdf
tags:
  [
    biological-foundation-model,
    single-cell-transcriptomics,
    generative-model,
    cell-atlas,
    cross-species,
    zero-shot-cell-typing,
    autoregressive,
    esm-2-embeddings,
    czi,
    cellxgene,
    group-A,
  ]
---

# TranscriptFormer: A generative cell atlas across 1.5 billion years of evolution

## TL;DR

TranscriptFormer is a family of three generative autoregressive transformer foundation models — **TF-Metazoa** (112M
cells, 12 species, 444M trainable params), **TF-Exemplar** (110M cells, human + 4 model organisms), and **TF-Sapiens**
(57M human-only cells) — trained on single-cell RNA-seq data spanning 1.53 billion years of evolution. Cells are
represented as ordered "cell sentences" of (gene, count) pairs; gene tokens are initialized from frozen ESM-2 protein
embeddings, which is what makes the models species-agnostic. The model factorizes P(genes, counts) autoregressively with
a count-aware multi-head self-attention bias and a zero-truncated Poisson count head paired with a categorical gene
head. Trained for ~3.5T tokens on a CZI GPU cluster, the models achieve state-of-the-art zero-shot cell-type
classification across species (TF-Metazoa F1 > 0.65 even on stony coral, ~685 Mya from human, where UCE collapses to F1
≤ 0.5), zero-shot disease-state classification (SARS-CoV-2 infection, glioblastoma, 95-drug Tahoe-100M perturbations),
and emergent biological structure in the embedding space (developmental trajectories, phylogenetic distance correlation
r = −0.705 in TF-Metazoa CGE space, cross-kingdom yeast → vertebrate-progenitor mapping). The generative interface
enables "virtual instrument" prompting — TF-Sapiens recovers known transcription-factor → target-gene relationships
across all 112 known human TFs from STRING via point-wise mutual information without any supervised training on those
edges. For Linus this is the cross-species transcriptomic specialist Worker, sibling to LucaOne and ProtiCelli, and the
first model in the corpus that operates natively at the **cell** level rather than the sequence level. MIT-licensed
code; weights on Zenodo (DOI 10.5281/zenodo.18381225).

## The problem (in plain language)

Single-cell RNA sequencing has industrialized cellular phenotyping — millions of cells per study, hundreds of millions
deposited in CZ CELLxGENE — but comparing cells across species is still hand-built. Conventional cross-species
single-cell analysis requires choosing a set of one-to-one orthologous genes shared between the species in question,
which works for closely related vertebrates but evaporates as soon as the comparison crosses metazoan phyla. Comparing a
sponge cell to a mouse cell or a fungal cell to a vertebrate progenitor requires either heroic ortholog mapping or just
giving up on the cross-species axis entirely. The recently published wave of single-cell foundation models — Geneformer,
scGPT, scMulan, scFoundation, GeneCompass, sCPRINT, UCE — mostly stayed in human or human+mouse, and most are not
generative; they produce embeddings but cannot serve as "virtual instruments" that simulate cellular responses or sample
probabilistic gene relationships.

The deeper problem is that **the cell, not the genome, is the unit of biological function** — and the cell is exactly
the unit at which previous foundation models in the Linus corpus do not operate. LucaOne speaks DNA / RNA / protein
_sequence_; Evo 2 speaks _genome_; Bacformer speaks _bacterial genome as ordered protein sequence_; ProteinReasoner
speaks _protein_. None of them speaks the language of "gene-expression program of one cell." A foundation model that
operates at cell granularity, generalizes across species without ortholog tables, and exposes a generative prompting
interface for in-silico experiments is a qualitatively different kind of tool — and it's exactly what comparative
cellular biology has been missing.

## What they propose

TranscriptFormer is a **generative autoregressive joint model over genes and their expression counts**. Three
architectural choices matter for Linus:

- **Cell sentences with ESM-2-embedded gene tokens.** A cell is represented as an ordered sequence of (gene, count)
  pairs. Each gene token is initialized from a frozen ESM-2 protein-language-model embedding of the longest protein
  product of that gene, which gives the model a species-agnostic gene-identity space — homologs across species occupy
  nearby points in input space, even when they have unrelated Ensembl IDs and no shared ortholog dictionary. An assay
  token encoding the sequencing technology is concatenated to flag technical context. Twelve transformer encoder blocks
  process the sentence with **expression-aware multi-head self-attention** that adds a function of raw counts as a
  per-pair attention bias, ensuring that highly expressed genes attend more strongly. Two decoder heads sit on top: a
  **gene head** producing a categorical distribution over the next gene in the sentence, and a **count head** producing
  a zero-truncated Poisson distribution over the count for the gene just predicted. The composite loss is cross-entropy
  on the gene head plus negative log-likelihood on the count head. Causal masking lets the model condition each
  prediction on all previously selected genes.

- **Three model variants spanning the breadth-vs-specialization axis at fixed architecture.** All three use the same
  12-block backbone with ~302M active parameters at inference, differing only in vocabulary size and training data.
  **TF-Metazoa** (vocabulary 247,388) trains on six vertebrates (human, mouse, rabbit, chicken, frog, zebrafish), four
  invertebrates (sea urchin, C. elegans, fruit fly, freshwater sponge), yeast, and Plasmodium falciparum — 112M cells
  across 1.53 Bya of evolution. **TF-Exemplar** (vocabulary 110,290) trains on human + four model organisms (mouse,
  zebrafish, fruit fly, C. elegans), 110M cells. **TF-Sapiens** (vocabulary 23,829) trains on 57M human cells only.
  Holding architecture and active parameters fixed makes the models a clean ablation of training-data breadth.

- **ESM2-CE baseline as architectural attribution.** The authors construct a deliberate baseline — ESM2-CE — that uses
  identical input representations (ESM-2 gene embeddings, count-aware features) but computes fixed-length cell
  embeddings by averaging ESM-2-derived protein embeddings, omitting the generative modeling component. The performance
  gap between TF-Metazoa and ESM2-CE is the contribution of generative cell-level pretraining, separated from the
  contribution of the species-agnostic input representation.

Pretraining data: 112M cells from CZ CELLxGENE Discover plus organism-specific atlases for non-human-non-mouse species
(RabbitGastrulation2022, Malaria Cell Atlas, Alzheimer's Fly Cell Atlas, etc.). Compute: large-scale distributed CZI GPU
cluster, mixed precision, ~3.5T training tokens with linear warm-up + cosine decay. Sampling rates upweight low-resource
species to balance representation.

Inference produces two output families: **cell embeddings** (mean-pooled across the cell sentence) for linear-probe
classification, and **contextualized gene embeddings (CGEs)** — per-gene representations conditioned on the rest of the
cell sentence — for gene-level analyses. The CLI exposes both via `transcriptformer inference --emb-type {cell,cge}`.
The generative interface is not exposed via a single flag in v0.6.1; the "virtual instrument" prompts in §"Using
TranscriptFormer as a virtual instrument" are custom analyses run on top of the model's autoregressive likelihoods.

## Key results

**Out-of-distribution cell-typing across 685 Mya of evolution (the headline result).** On unseen species (mouse lemur,
tropical clawed frog, sea lamprey, stony coral) TF-Metazoa and TF-Exemplar maintain macro F1 > 0.65 even at the 685-Mya
stony-coral distance from human — where the prior SOTA single-cell foundation model UCE collapses to F1 ≤ 0.5 (Fig. 2B).
On the more clinically meaningful chicken-to-mammal cell-type transfer (310 Mya divergence), TF-Exemplar reaches
species-average F1 0.448 versus UCE 0.251, and TF-Exemplar improves on the ESM2-CE baseline by 91% — direct evidence
that the generative pretraining, not the ESM-2 input representation alone, is doing the work.

**State-of-the-art zero-shot cell-typing on Tabula Sapiens 2.0.** TF-Exemplar achieves macro F1 0.910 on the held-out
post-training-cutoff Tabula Sapiens 2.0 component, edging TF-Metazoa (0.907) and TF-Sapiens (0.906); UCE ties at 0.906
and ADIO.Cell at 0.708 trails substantially. In the harder 65th-95th-percentile tail (myeloid leukocytes, T-cells,
innate lymphoid cells), TranscriptFormer variants and UCE separate from the rest. Multispecies pretraining does not
dilute human performance — TF-Exemplar slightly outperforms TF-Sapiens on cross-species transfer tasks while TF-Sapiens
retains its narrow advantage on human-disease-modeling tasks.

**Zero-shot disease-state classification, no fine-tuning.** Three datasets, all held out from training. SARS-CoV-2
infected vs uninfected lung cells: TF-Sapiens macro F1 0.859, TF-Exemplar 0.856, TF-Metazoa 0.854, all significantly
outperforming scGPT (0.798) and Geneformer (0.797) (Fig. 3D). Glioblastoma tumor vs normal: TranscriptFormer variants
and scVI achieve F1 0.88-0.91, substantially outperforming UCE. Tahoe-100M drug perturbation (95 compounds): TF-Sapiens
mean AUC 0.879 over UCE 0.779, scGPT 0.774, scVI 0.709 — and the per-compound spread (0.727 to 0.998) reveals that some
compounds (TAK-901, Bortezomib, PH-797804) leave essentially deterministic transcriptional fingerprints that any
reasonable model recovers, while others are at the edge of detectability.

**Cross-species perturbation transfer.** LPS treatment of bone-marrow-derived mononuclear phagocytes from mouse, rat,
rabbit, and pig — TF-Metazoa species-averaged F1 0.925 versus UCE 0.740, ESM2-CE 0.580. The inflammatory-response
perturbation state transfers across species without any species-specific fine-tuning, which is the exact regime
cross-species transcriptomic foundation models are supposed to serve.

**Emergent phylogenetic structure in CGE space.** TF-Metazoa contextualized gene embeddings, averaged across cells of
comparable type, encode phylogenetic distance: Spearman r = −0.705 (p = 0.004) between embedding cosine similarity and
Mya of evolutionary distance across vertebrates. ESM2-CE shows no correlation (r = −0.059, p = 0.801). The model was
only trained on _one_ chicken dataset yet learns the chicken-to-mammal transcriptional distance from data — strong
evidence that joint cross-species pretraining is reconstructing macroevolutionary structure that no single species' data
could reveal.

**Cross-kingdom emergent mapping.** Yeast cell states grown under ten environmental conditions map most similarly to
embryonic progenitor cell states across five animal species. The biological interpretation — yeast as a
transcriptionally progenitor-like cell — is speculative across a >1 Bya gap, but the model's willingness to land that
mapping reproducibly across animal hosts is itself notable. Sponge choanocytes map to primary sensory neurons in
roundworm and frog, supporting evolutionary models proposing choanocyte-derived sensory cell origins (Fig. 4F).

**Generative TF → target-gene recovery.** Using point-wise mutual information from TF-Sapiens autoregressive
log-probabilities on Tabula Sapiens 2.0 cell-type contexts, the model recovers known canonical TF → target relationships
from STRING v12.0: E2F8 (87 hits vs 2.0 expected), FOXM1 (105 vs 4.1), MYBL2 (54 vs 1.3), SPIB (9 vs 0.1), UHRF1 (59 vs
1.4) — all well above permutation-test baselines. The model recapitulates the empirical TF → cell-type heatmap from
Tabula Sapiens 2.0 _without ever seeing the TS-2.0 evaluation set during training_ and without any supervised training
on TF → target-gene edges. This is the "virtual instrument" claim made operational.

**Compute realism.** Three model variants × ~3.5T tokens × 12-layer 302M-active-param architecture is a substantial
CZI-GPU-cluster training run, well beyond M1 Max retraining range. But the released models are designed for inference at
modest hardware scales: README documents A100 40GB recommended, with explicit fallback to 16GB GPUs at batch size 1-4,
and the inference CLI exposes a `--device {auto,cpu,cuda,mps}` flag — the codebase claims MPS support out of the box.

## What's reusable in Linus

**Direct, Phase 7 (Skills & Autonomy Graduation):** TranscriptFormer is the **cross-species transcriptomic specialist
Worker** in Linus's biological tool registry. The relevant tool surface is well-defined:
`linus.bio.embed_cells(adata) -> embeddings`,
`linus.bio.classify_cell_types(adata, reference_atlas) -> cell-type labels`,
`linus.bio.predict_disease_state(adata, condition) -> binary probability`,
`linus.bio.virtual_tf_targets(cell_type, tf_name) -> ranked gene list with PMI scores`. The released CLI already
provides the first three; the fourth requires custom code over the autoregressive log-probabilities but the methodology
is fully described. Tag deployment per **DEC-0046** (`external_api_tool` registry deployment field): the tool is
**local-only** — frozen weights, no network call required after the checkpoint download — but the cell embeddings and
CGE outputs themselves are first-class candidates for publication into a `model_prediction` edge class per **DEC-0048**,
which is exactly the cellular-state edge type that no current Linus KB substrate carries.

**Direct, Phase 7 specialist registry — sibling to LucaOne, ProtiCelli.** The "specialists-as-Workers" framing in
`biological-foundation-models-synthesis.md` extends here. LucaOne is the generalist sequence encoder (DNA / RNA /
protein); ProtiCelli is the generative cellular-imaging specialist; TranscriptFormer is the generative
cellular-transcriptomics specialist. Each operates at a different biological granularity, and a single Worker call
cannot substitute for the others. The router decision documented in the BFM synthesis — generalist as default +
specialist on named domain — extends to TranscriptFormer as the named specialist for cell-type / disease-state /
cross-species cellular-transcriptomic queries. TF-Metazoa is the default variant for cross-species work; TF-Sapiens is
the variant for human-disease-modeling specifically; TF-Exemplar is the model-organism transfer variant.

**Direct, Phase 3 (Knowledge & Parallel Agents) — KnowledgeBase model-prediction edges.** Per **DEC-0048**
(`model_prediction` is a first-class KB edge class), TranscriptFormer outputs are an unambiguous fit. Two productive
edge types: (a) **TF → target-gene** edges from PMI analysis on TF-Sapiens, scored with the model's PMI value and an
explicit `model_prediction` provenance tag, queryable alongside experimentally-grounded STRING / KEGG edges; (b)
**cell-type → cell-type** cross-species homology edges from the developmental-cell-atlas mapping work — sponge
choanocyte ↔ frog Rohon-Beard neuron, yeast → vertebrate progenitor — represented as similarity edges with the model's
cosine-similarity score. Both edge types must be explicitly tagged as model-derived under DEC-0048's discipline; the
biosecurity tier per DEC-0047 stays at Tier A for read-only embedding / classification use, but generative TF-target
prompting that touches sensitive perturbation targets warrants a Tier-B review when those targets become operationally
available.

**Direct, Phase 1-2 recon — Apple Silicon viability spike.** The README explicitly documents `--device mps` as a
supported flag. The 302M-active-parameter inference footprint (FP16) is comfortable on M1 Max unified memory: ~600MB
weights + activations for typical cell sentence lengths, well within the 32GB budget even running concurrent with other
Linus models. Concrete spike: stand up TranscriptFormer in a disposable `uv venv` per **DEC-0024** (the dependencies are
heavy — torch 2.5.1 pinned, scanpy, anndata, hydra-core, cellxgene-census 1.17 — not appropriate for the linus conda
env), download `tf_sapiens` plus the `homo_sapiens_gene` embedding pack (~2-4GB), run inference on a small held-out
h5ad, capture wall-clock and memory in `benchmarks/results/`. If MPS works at practical speed on a Tabula-Sapiens-sized
input (10-100k cells in single-digit minutes), TranscriptFormer becomes a Phase 7 skill candidate; if MPS underperforms
or has correctness issues, demote to a CPU-fallback skill or remote-API option per DEC-0046. The flag-level support is
the first such advertisement among the Group A bio FMs.

**Indirect, architectural pattern — gene-token initialization from frozen pLM embeddings.** The TranscriptFormer + UCE
pattern (gene tokens initialized from ESM-2 embeddings rather than learned ID-table lookups) generalizes. For any future
Linus-trained model where token identities have an external semantic representation (genes ↔ proteins; chemical
structures ↔ SMILES embeddings; functions ↔ docstrings), initializing the token table from a frozen embedding model
produces species-agnostic / domain-agnostic transfer for free, without requiring paired supervision. This is the same
lesson as Bacformer's protein-embeddings-as-tokens trick, generalized one level: when the unit of representation has
external semantic structure, exploit it.

**Indirect, evaluation methodology — held-out-by-construction post-training-cutoff data.** Tabula Sapiens 2.0, used as
the human-cell-typing evaluation, postdates the training-data cutoff for all benchmark models — TranscriptFormer
included. Combined with the cross-species OOD evaluation (mouse lemur, tropical clawed frog, sea lamprey, stony coral
never seen in training) this is the cleanest published example of a biological-foundation-model evaluation that
genuinely tests generalization rather than hidden training-set leakage. For `benchmarks/dan_tasks/`, the discipline rule
is: any biology benchmark Linus authors should explicitly document its temporal relationship to the training corpus of
the models being benchmarked, and prefer post-cutoff evaluation sets when available.

## What's NOT applicable / hype filter

The training compute (a CZI GPU cluster with mixed precision and distributed data parallelism running ~3.5T tokens ×
three model variants) is not reproducible on Apple Silicon. Linus uses TranscriptFormer as an inference-only or
LoRA-fine-tunable backbone, not a from-scratch retrain target. Phase 6 LoRA on the 302M-active-parameter inference path
is plausibly tractable on M1 Max but is well outside Phase 1-2 scope and the paper does not characterize how the model
responds to small fine-tunes.

The "1.53 billion years of evolution" framing is rhetorically powerful but biologically uneven — the training set spans
yeast (a fungus, ~1 Bya from animals) and Plasmodium (a protist, even more divergent) through vertebrate cells, but the
bulk of the data (>50%) is human and ~12% mouse. Performance at the extreme phylogenetic distances (yeast →
vertebrate-progenitor cross-kingdom mapping) is enabled by a few percent of the training data. Don't read claims at the
long-distance edge as having the same evidential weight as the within-vertebrate cross-species transfer claims, which
are well-supported. The phylogenetic-distance correlation result (Spearman r = −0.705) is computed within vertebrates,
not cross-kingdom.

The "virtual instrument" framing is real but limited in scope. The TF → target-gene PMI analysis is a well-defined
statistical operation on the model's joint distribution; calling it a "virtual instrument" suggests a more general
capability than the paper actually demonstrates. The model can score TF → gene cellular-context-conditioned associations
and recover known relationships, but it does not simulate full perturbation responses (CRISPR knockouts, drug treatments
at arbitrary doses) in a way that would substitute for wet-lab experiments. It is _hypothesis-generation_, not
_experiment replacement_, and the paper is mostly careful to say so.

The model has no built-in batch-effect handling — the discussion explicitly flags donor effects as stronger than batch
effects in the Tabula Sapiens 2.0 CGE analysis, and the authors cannot fully rule out batch contamination. For Dan's
bioinformatics work where batch effects are first-class concerns (any meta-analysis of disparate scRNA-seq cohorts),
TranscriptFormer outputs need to be checked against batch-correction baselines, not consumed as if they were
batch-neutral.

The model is **transcriptomic only** — no ATAC-seq, no spatial transcriptomics, no protein abundance, no multimodal
Patch-seq integration. The paper flags multimodal extension as future work. For any Linus task that requires non-RNA
cellular features, TranscriptFormer is at most one input among several, not the primary tool.

The 247K-vocabulary TF-Metazoa carries non-trivial storage cost for a model that only has 302M active parameters at
inference: 444M trainable + 633M non-trainable (frozen pretrained ESM-2 embeddings). Quantization-friendliness on M1 Max
is unmeasured; the frozen embeddings dominate the parameter count and FP16 quantization should be straightforward, but
no quantization characterization is provided.

## Connections

**Sibling generative cellular biology FM — ProtiCelli.** ProtiCelli (paper-note
[`2026.03.31.715748v1.md`](2026.03.31.715748v1.md), repo-note
[`../repo-notes/ProtiCelli.md`](../repo-notes/ProtiCelli.md)) is the generative cellular-imaging foundation model
authored in the same fan-out as TranscriptFormer. The two share a deep operational pattern: a generative foundation
model that operates at the **cell** level rather than the sequence level, exposes a "virtual instrument" prompting
interface, and is designed for in-silico hypothesis generation rather than supervised end-task replacement. They differ
in modality (transcriptomics vs imaging) and evolutionary scope (TranscriptFormer's 1.53 Bya cross-species range has no
obvious counterpart in cellular imaging), but the framing is shared. Reading them together sharpens the point that **the
cell is becoming a foundation-model unit of representation in its own right**, alongside genome / sequence / protein,
and that Linus's Phase 7 biology skill class needs a cell-level Worker family, not just sequence-level Workers.

**Cross-thread cousin — LucaOne.** LucaOne (paper-note [`s42256-025-01044-4.md`](s42256-025-01044-4.md)) is the closest
sibling in the Linus corpus — both are biological foundation models with a strong cross-axis pretraining claim (LucaOne
unifies modalities; TranscriptFormer unifies species). LucaOne demonstrates emergent central-dogma capability from joint
DNA + protein training; TranscriptFormer demonstrates emergent phylogenetic structure from joint cross-species cellular
training. The architectural patterns are different — LucaOne is an encoder with token-type embeddings disambiguating
shared alphabets, TranscriptFormer is a decoder-style autoregressive model with ESM-2 gene-embedding initialization
disambiguating species-specific gene IDs — but the recipe rhymes: **unify a previously-balkanized representation by
initializing the token space from a model trained at the next level of biological abstraction.** The Phase 7 question of
generalist-vs-specialist that LucaOne raises in the BFM synthesis applies here too: TranscriptFormer is itself a
generalist within cellular transcriptomics, and a bench scientist working primarily on human disease might be better
served by TF-Sapiens specifically rather than TF-Metazoa.

**Long-context complement — Evo 2.** Evo 2 (paper-note [`s41586-026-10176-5.md`](s41586-026-10176-5.md)) operates at
single-base genomic granularity with 1M-token context; TranscriptFormer operates at cell-sentence granularity (typically
a few thousand expressed genes). Together they cover two orthogonal scales of biological FM — one that reads chromosomes
and one that reads cells. A natural Phase 7+ composite is "Evo 2 predicts variant effects → TranscriptFormer predicts
cell-type-specific expression consequences," a pipeline that no single Group A model addresses.

**Architectural cousin — biophysics-conditioned PLM.** The biophysics-conditioned PLM (paper-note
[`2025.07.20.665723v2.md`](2025.07.20.665723v2.md)) demonstrates that contextualizing a protein language model with
physical conditions (temperature, pH) produces a context-aware representation; TranscriptFormer's contextualized gene
embeddings (CGEs) — gene representations conditioned on the rest of the cell sentence — are the cellular analogue. Both
validate the broader pattern that **frozen embeddings are insufficient where context matters**, and both expose
context-aware embeddings as a primary output alongside cell / protein-level embeddings.

**Generative-biology synthesis cross-link.** TranscriptFormer's "virtual instrument" framing is generative biology done
at the cellular regulation level rather than the sequence level. Where ProteinReasoner (paper-note
[`2025.07.21.665832v2.md`](2025.07.21.665832v2.md)) and Evo 2 generate sequences, TranscriptFormer generates
probabilistic cellular states. The [generative-biology-synthesis](../syntheses/generative-biology-synthesis.md) lineage
is consistent across all three: a generative likelihood over a biological substrate is more useful than a discriminative
classifier on the same substrate, even when the discriminative task is what gets evaluated.

**Synthesis target.** Primary fold-in:
[`biological-foundation-models-synthesis.md`](../syntheses/biological-foundation-models-synthesis.md) — TranscriptFormer
extends the specialists-as-Workers framing to a **cross-species cell-level transcriptomic specialist**, an axis that
LucaOne does not have (LucaOne unifies modalities at the sequence level, not species at the cell level). The synthesis's
generalist-vs-specialist constellation gains a third dimension: TranscriptFormer is itself a generalist within
transcriptomics, parameterized by training-data breadth, and the architectural-fixed three-variant family (Sapiens /
Exemplar / Metazoa) sharpens the framing — broader pretraining trades off slightly with within-species depth when the
application is human-disease-only.

## Open questions for Dan

1. **MPS device support — does the `--device mps` flag actually deliver?** The README advertises MPS, the codebase has
   the flag, but no published benchmark numbers exist for TranscriptFormer on M1 Max. The first concrete Phase 1 spike
   is "stand up TF-Sapiens in a disposable uv venv, run inference on a 10k-cell h5ad with `--device mps`, compare
   wall-clock and embedding-quality against `--device cpu`, capture in `benchmarks/results/`." If MPS works,
   TranscriptFormer is the first Group A bio FM with native Apple-Silicon support documented at the CLI level, which has
   registry implications.

2. **Variant default — TF-Metazoa, TF-Exemplar, or TF-Sapiens as the Linus default?** The paper demonstrates that
   TF-Exemplar slightly outperforms TF-Metazoa on cross-species transfer tasks while TF-Sapiens retains a narrow
   advantage on human-disease tasks. For Dan's task distribution (LanzaTech metagenomics is mostly bacterial, but the
   cellular-foundation-model use cases are likely to involve _Botryococcus_-adjacent algal cells, fungal hosts, and
   yeast as a reference) — does TF-Metazoa win because it's the only variant that includes yeast and Plasmodium, or is
   the real biological-distance to algae too large for any of the three to be useful? The 1.53Bya training scope does
   not include any green algae or land plants, which is a structural gap.

3. **`model_prediction` edge-class scope.** Per DEC-0048, TF → target-gene PMI edges and cell-type- homology
   cross-species edges are first-class candidates for the KB. Should Linus eagerly publish these into KB whenever a
   TranscriptFormer query runs (every cell-typing query produces O(thousand) provisional homology edges), or should
   publication be gated on explicit user request? The storage-and-noise tradeoff matters; the answer probably depends on
   whether KB queries surface model_prediction edges by default or require explicit opt-in.

4. **Generalist-vs-specialist registry decision when TranscriptFormer joins.** The BFM synthesis tentatively recommends
   LucaOne as the generalist default plus specialists on named domain. With TranscriptFormer added, the
   cellular-transcriptomic domain is named — but the routing question is whether a query like "what cell type is this
   scRNA-seq sample" goes to TranscriptFormer (the cellular specialist) or to LucaOne (the generalist that has not been
   demonstrated on cell-typing). Probably TranscriptFormer; worth confirming in the Phase 7 router design.

5. **Tier-B biosecurity surface.** Per DEC-0047 (three-tier policy), embedding extraction and cell-type classification
   are Tier A (standard sandbox). The generative TF → target-gene prompting interface — particularly when targeted at
   human-pathogen-relevant cell types — sits closer to Tier B (explicit Dan sign-off, audit-logged). Where exactly is
   the dividing line? Recovering canonical TF → target relationships from STRING is harmless; generating speculative
   TF-target predictions in cell types relevant to perturbation engineering (immune cells, neurons) is closer to
   dual-use territory. Worth scoping before exposing the virtual-instrument interface as a Linus tool.

6. **Phase 6 LoRA candidate?** TF-Metazoa's 302M active parameters are well within LoRA-on-M1-Max territory, and the
   cell-sentence input format means a Dan-corpus-specific fine-tune (e.g., on a private collection of fungal or algal
   scRNA-seq, where the original training set is thin) could genuinely improve domain performance. Worth scoping as a
   Phase 6 candidate alongside LucaOne+Dan-corpus and language-model fine-tunes, or strictly out of scope until the
   recon spike confirms inference correctness on M1 Max?

7. **Output-channel schema for the cell-level KB.** Per DEC-0048, model-prediction edges need a provenance schema that
   distinguishes evidence sources. TranscriptFormer outputs naturally fall into three classes — cell embeddings
   (continuous, dense, useful for retrieval), cell-type labels (discrete, classifier output), and TF-target PMI scores
   (continuous, statistical). Should the KB carry all three or only the discretized predictions? The continuous
   embeddings are the most information-rich and the most expensive to store; the discretized predictions are the most
   queryable.
