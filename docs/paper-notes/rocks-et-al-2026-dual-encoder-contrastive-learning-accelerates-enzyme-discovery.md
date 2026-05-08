---
title: "Dual-encoder contrastive learning accelerates enzyme discovery"
source: PNAS 2026, Vol. 123, No. 12, e2520070123 (DOI: 10.1073/pnas.2520070123)
authors: Jason W. Rocks, Dat P. Truong, Dmitrij Rappoport, Samuel Maddrell-Mander, Daniel A. Martin-Alarcon, Toni M. Lee, Steven Crossan, Joshua E. Goldford
affiliation: Dayhoff Labs, Inc., Cambridge, MA
date: 2026-03
pdf: ../../context/papers/rocks-et-al-2026-dual-encoder-contrastive-learning-accelerates-enzyme-discovery.pdf
code: https://github.com/dayhofflabs/horizyn
data: https://doi.org/10.5281/zenodo.17957034
tags: [enzyme-discovery, contrastive-learning, dual-encoder, clip, protein-language-model, prott5, ecfp6, drfp, biocatalysis, retrieval, group-c, dans-domain, phase-7-skill, fine-tuning]
---

# Dual-encoder contrastive learning accelerates enzyme discovery

## TL;DR

Horizyn-1 is a CLIP-style **dual-encoder contrastive model** that learns a shared embedding space between **biochemical
reactions** (encoded as ECFP6 + DRFP fingerprints) and **enzyme protein sequences** (encoded with the 3B-parameter
ProtT5 PLM). Trained on ~9M reaction-enzyme pairs spanning 31K reactions and 7M clustered protein sequences, it answers
"which enzyme catalyzes this reaction?" by ranking proteins via cosine similarity in the shared space. It recovers a
known catalyst within the **top 100 for 76.7%** of held-out test reactions, beating an EC-number baseline (27.5%) and
CLIPZyme. The contribution that separates this from prior work is **prospective wet-lab validation** across three
regimes: deorphaning a nylon-degradation reaction in _Arthrobacter sp. KI72_, predicting promiscuous activities in
uncharacterized _T. aquaticus_ proteins (including a dCMP kinase with only 28% identity to its nearest training
homolog), and discovering enzymes for non-natural lysine-driven transamination reactions used in pharmaceutical
noncanonical amino acid synthesis. Fine-tuning on as few as **10 reactions** from a held-out class (ene-reductases)
lifts the median top-100 hit rate from 38% to 71%. Code and the development dataset are released by Dayhoff Labs.

## The problem (in plain language)

Enzyme engineering campaigns almost always start with the same bottleneck: you have a reaction you want to run (a
transamination, a reduction, a phosphorylation of an unusual substrate) and you need a wild-type enzyme with at least
minimal native activity as a seed for directed evolution. The candidate universe is the full annotated proteome
(UniProt + TrEMBL ≈ tens of millions of sequences), and the available filters are weak. Sequence-similarity search
(BLAST, MMseqs2, HMMER, Foldseek) needs you to already have a known enzyme of the same EC class. EC-prediction tools
(CLEAN, DeepEC) tell you the category, not whether the enzyme catalyzes _your_ reaction. Reaction-conditioned tools
(BridgIT, CLIPZyme, ReactZyme) exist but are either non-ML or only retrospectively benchmarked on small datasets — never
validated experimentally at scale.

The asymmetry: the chemist knows the reaction as a SMILES string, the protein universe is fully sequenced and embedded
in PLMs like ESM-2 and ProtT5, yet no general-purpose retrieval system existed that took a reaction query and ranked
tens of millions of candidates by predicted activity. This paper builds and validates that system.

## What they propose

Horizyn-1 is structurally a CLIP model with chemistry on one side and protein sequence on the other. Both inputs are
precomputed external representations passed through small MLP projection heads into a shared embedding space. Reactions
use ECFP6 (Morgan fingerprints of reactants and products) plus DRFP (differential fingerprints capturing bond changes),
giving a 1024-bit representation. Proteins use static ProtT5 embeddings of the full sequence. Training uses **in-batch
negative sampling** with an MLNCE loss, fixed β = 10, batch size 16,384, AdamW, on a single NVIDIA T4 — the development
model trains in 1.5 hours, the full inference model in two days.

The architectural insight is that **input representations matter far more than encoder architecture**. Fingerprint-based
reaction encoding beat both transformer (rxnfp) and graph-neural-network (Chemprop) alternatives — likely because the
reaction dataset (~31K reactions) is too small and diverse for a deep model trained from scratch, while ProtT5's
billion-protein pretraining gives the protein side a strong starting representation. End-to-end fine-tuning of
ESM-2-650M and adding 3D structural information both failed to improve performance enough to justify the compute. The
takeaway: **dual-encoder contrastive models scale primarily through better pretrained backbones on each modality, not
through joint end-to-end training**.

The training data combines Rhea, EnzymeMap (BRENDA-derived), UniProt, and TrEMBL into ~31K reactions and ~34M pairs,
then clusters proteins at 80% identity with MMseqs2 down to ~7M sequences and ~9M pairs. A three-tier confidence
heuristic (low <0.10, moderate 0.10–0.72, high ≥0.72) is calibrated on the score distributions of training positives vs.
negatives and used to prioritize wet-lab screening.

## Key results

The retrieval benchmark (Fig. 1D) shows Horizyn-1 with ECFP6/DRFP + ProtT5 at **76.7% top-100, 53.1% top-10, 31.8%
top-1** on a held-out test set of 1,012 reactions. The EC-class-3 baseline gets 27.5% top-100. Combining the model with
partial EC knowledge adds 5–10%. Performance scales **logarithmically** with training reactions; extrapolating, a 10x
reaction-diversity increase could approach 100% top-100.

The wet-lab validation is what makes the paper convincing. For the orphan **6-aminohexanoate aminotransferase** reaction
in nylon-degrading _Arthrobacter sp. KI72_, Horizyn-1's top-2 hits both showed measurable activity; _E. coli_ GabT (also
flagged) turned out to have higher activity than either Arthrobacter homolog — a previously unreported promiscuity. For
uncharacterized _T. aquaticus_ proteins with no training homologs, the model correctly predicted
(R)-2-hydroxyglutarate–pyruvate transhydrogenase activity in A0A0N0U829 and dCMP kinase activity in A0A0N0BLM2 (28%
identity to its nearest training homolog). BLAST, MMseqs2, Foldseek, CLEAN, and CLIPZyme all failed to find the dCMP
kinase activity.

The most striking result is the discovery of **lysine-driven transaminases** for synthesizing noncanonical amino acids
(phenylglycine, 2-thienylglycine, 2-furylglycine) — non-natural reactions with no direct training analog. Horizyn-1 was
queried over ~7M proteins for six reaction variants (α- vs. ε-amine donation × three keto-acid acceptors); a panel of
six enzymes was selected, four expressed, one (TA2 / P09053) showed strong activity on all three substrates. An
isotope-labeling study with 15Nε-lysine then **confirmed Horizyn-1's mechanistic prediction** that TA2 transaminates
predominantly from the α-amine — the model's α-vs-ε score difference was the only computational signal pointing there.

The fine-tuning result (Fig. 4) is the practical headline. Ene-reductases (EREDs) were held out as a novel class with
poor baseline performance (median top-100 = 38%). Fine-tuning on **just 10 ERED reactions** lifted the median to 71%. A
_single_ novel ERED reaction sometimes pushed it to 84%, and the gain size correlated (r = 0.54) with how distant that
single reaction was from training data — pointing to a clean active-learning loop where the model itself nominates the
most informative next experiment.

## What's reusable in Linus

**Architectural pattern, cross-cutting:** The dual-encoder contrastive (CLIP-style) pattern for cross-modal scientific
retrieval is the most reusable piece. Any "find me a [protein / molecule / sequence / structure] for this [reaction /
function / target / phenotype]" question fits this template: pick a strong pretrained backbone per modality, freeze it,
train a small projection head per side with in-batch negatives, store embeddings in a vector index. The pattern
transfers to drug-target retrieval, substrate-binding-site retrieval, variant-effect retrieval,
reaction-pathway-vs-genome retrieval. This belongs in `docs/syntheses/` as a named Linus architectural pattern —
**"dual-encoder cross-modal retrieval for scientific discovery"** — with Horizyn-1 as the worked example. The discipline
the paper teaches: invest in the per-modality backbones, keep the joint training cheap (frozen embeddings + MLP heads +
in-batch negatives), and resist end-to-end joint training until the simple version provably fails.

**Phase 7 skill candidate:** Reaction-to-enzyme matchmaking is squarely in Dan's wheelhouse — biocatalysis, pathway
deorphaning, promiscuity prediction in genome annotations. The model is ~3B parameters on the protein side (ProtT5
dominates inference) plus tiny MLP heads. A Phase 7 skill **enzyme-match** would take a SMILES reaction and return
ranked enzyme candidates with confidence tiers. The ~7M-sequence screening set at 1024-dim float16 is ~14 GB — fits
comfortably on the M1 Max alongside everything else.

**Phase 6 fine-tuning lever:** The ene-reductase result (10 reactions → median 71% top-100) is exactly the small-data
adaptation LoRA was designed for. The contrastive objective is well-behaved under low-rank adaptation because only
projection heads (optionally top layers of ProtT5) need updating. To specialize Horizyn-1 for a reaction class Dan cares
about — CYP450 oxidations, a glycosyltransferase family, thermophilic enzymes for industrial conditions — the data
requirement is ~10 curated pairs from BRENDA or literature; compute is a T4 for 10 epochs.

**KnowledgeBase implications:** Horizyn-1's embeddings are exactly the substrate KnowledgeBase wants for a multi-modal
scientific knowledge graph. Reactions become nodes with chemistry-aware vectors; enzymes become nodes with
function-aware vectors; the contrastive score is the edge weight. Paper-citing-enzyme and paper-discussing-reaction
edges link naturally to the literature graph. The same Qdrant index can power both literature retrieval and
reaction-enzyme retrieval. The paper's finding that shared-embedding distance correlates with shortest-path distance in
the reaction-enzyme network (SI Fig. S17) invites using Horizyn-1's space as the geometry for a biocatalysis subgraph.

**Group C anchor:** This is the leadoff Group C paper. Group C is **function annotation, reasoning, and discovery** —
DIAMOND DeepClust (clustering for annotation), ProtHGT (graph transformer for protein function), BioReason /
BioReason-Pro (reasoning over biological knowledge), Horizyn-1 (retrieval-based discovery), multimodal single-cell FM.
Horizyn-1 sits at the **retrieval/discovery** end: it proposes candidates rather than classifying or reasoning over
them. The Group C synthesis should frame these as a pipeline — clustering and classification feed retrieval; retrieval
results become evidence for reasoning; reasoning suggests next experiments.

**Compare with REMME/REBEAN ([gkaf836.md](gkaf836.md)) — Group A neighbor:** REMME/REBEAN does enzyme classification
from metagenomic reads (sequence → EC). Horizyn-1 does enzyme recommendation from a reaction (reaction → ranked
enzymes). They are **complementary halves of a discovery pipeline**: REMME expands the candidate universe via
metagenomic dark matter; Horizyn-1 navigates whatever universe exists to find activity for a target reaction. Paired as
Linus skills, they cover the workflow a biocatalysis postdoc currently does by hand over weeks.

**Compare with METL ([s41592-025-02776-2.md](s41592-025-02776-2.md)):** Both are protein engineering at opposite poles.
METL fine-tunes one model on tens of variants of one protein — local, deep, single-protein. Horizyn-1 retrieves over
millions of proteins for arbitrary reactions — global, shallow, cross-protein. They are sequential in a real campaign:
Horizyn-1 nominates the wild-type seed; METL guides directed-evolution mutagenesis on top. Both in the Linus skill
catalog enables a full local discovery → engineering loop.

## What's NOT applicable / hype filter

The wet-lab portions — cloning, BL21(DE3) expression, Ni-NTA purification, LC-MS MRM, colorimetric assays — are not
Linus's job. Linus suggests enzymes; humans run the bench. The paper makes this division crisp and Linus should keep it
crisp.

The training infrastructure assumes a CUDA T4 with 16K batch sizes and tens of millions of pairs. Re-training from
scratch on Apple Silicon is feasible (the model is small — MLPs over precomputed embeddings) but the PyTorch Lightning +
PyTorch 2.0 stack is CUDA-flavored. The right path for Linus is **inference-only reuse of released weights**; the GitHub
repo (`dayhofflabs/horizyn`) hosts the development model, and the larger inference model's release status needs
verification.

RDKit (ECFP6) and DRFP are CPU-only Python and run anywhere. No CUDA dependency on the inference path once embeddings
exist.

Horizyn-1 cannot predict kinetic parameters (kcat, Km) or quantitative mutant activity — a real limit for engineering.
It ranks by _catalytic plausibility_, not activity magnitude. The discussion is honest about this and points downstream
to METL-style mutational models. It also doesn't distinguish catalytic domains from full sequences, and struggles with
chemistry involving protein-based metabolites (ferredoxins) or oligonucleotides. Any Linus wrapper should surface these
caveats in its docstring.

## Connections

The paper is a direct sibling of [REMME/REBEAN (gkaf836.md)](gkaf836.md) — REMME mines metagenomes for enzymes;
Horizyn-1 matches enzymes to reactions. Two independently designed halves of the same pipeline.

The reaction-fingerprint side connects to any Linus cheminformatics work: RDKit is a likely KnowledgeBase dependency
anyway, and ECFP6/DRFP machinery can serve molecule-similarity queries elsewhere.

The architectural pattern is the one CLIP popularized for image-text and that has since been replicated for image-audio
(CLAP), video-text (VideoCLIP), code-natural-language (CodeBERT-family), and protein-text (ProtST). Horizyn-1 applies it
to **reaction-protein**. Documenting this in `docs/syntheses/` makes the skeleton easier to recognize across future
Group C and beyond.

The fine-tuning result (10 examples → large gain) sits in the broader theme of **few-shot adaptation of pretrained
backbones** running through METL, LoRA, and in-context learning. The mechanism differs (full fine-tuning of projection
heads, not adapter weights), but the lesson — frozen large pretrained encoders make small-data adaptation tractable — is
the same.

Operationally, the choice of **frozen ProtT5 + small MLP heads** over end-to-end ESM-2 fine-tuning echoes the
[tokens-per-second paper (2502.16721v1.md)](2502.16721v1.md) in spirit: the expensive option is not always the better
option. Measure first.

## Open questions for Dan

1. **Code and weights status:** The GitHub repo (`https://github.com/dayhofflabs/horizyn`) hosts the _development model_
   code; Zenodo hosts the _development dataset_. The larger 9M-pair inference model — the one validated experimentally —
   is the one Linus would actually want. Is it released? In what format? PyTorch checkpoints can be loaded under Apple
   Silicon via PyTorch-MPS, but a clean MLX port would be cheaper at inference time. Worth checking before committing to
   a Phase 7 skill spec.

2. **Comparison with tools you actually use:** How does Horizyn-1 compare in your hands to existing tools — DLKcat
   (kinetic prediction), ECnet/CLEAN (EC classification), or Foldseek (structural similarity)? The paper compares
   against CLIPZyme, BLAST, MMseqs2, and Foldseek and wins, but a domain practitioner's view on whether the predicted
   enzymes are _actually useful starting points for engineering_ is worth more than the benchmark numbers.

3. **Phase 7 skill scoping:** Is `enzyme-match` (reaction → ranked enzymes) niche enough that it should wait until Phase
   7, or general enough — given biocatalysis is a recurring theme in your work — that a thin wrapper around the released
   weights belongs in Phase 3 alongside KnowledgeBase v1? The 14 GB embedding store fits the M1 Max comfortably.

4. **Reaction-fingerprint dependency surface:** Horizyn-1 relies on RDKit (ECFP6) and DRFP for reaction encoding. If
   Linus already needs RDKit for KnowledgeBase chemistry parsing, this is free. If not, it's a moderate dependency to
   add. Worth confirming the chemistry-tooling decision once, ahead of any skill that touches molecular representations.

5. **Pair with REMME/REBEAN and METL?** The natural Linus packaging is a three-skill biocatalysis trio: REMME/REBEAN
   (find candidate enzymes from sequence data), Horizyn-1 (match candidates to target reactions), METL (engineer the
   chosen enzyme via small-data prediction). Should this trio be planned as a unit for Phase 7, or are they three
   independent skills that happen to compose well?

6. **Active-learning loop:** The paper points to a "lab-in-the-loop" active learning strategy in the discussion — the
   model nominates the next reaction to characterize based on embedding-space distance, the wet-lab returns data, the
   model fine-tunes. Is there a Linus-shaped role here as the orchestration layer between a query, the model's
   recommendations, an experimental protocol generator, and a results database? It's speculative, but it's the kind of
   long-running scientific workflow where an orchestration backend earns its keep.
