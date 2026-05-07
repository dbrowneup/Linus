---
title: "Deciphering enzymatic potential in metagenomic reads through DNA language models"
source: Nucleic Acids Research, 2025, 53, gkaf836 / DOI 10.1093/nar/gkaf836
authors: R. Prabakaran, Yana Bromberg
affiliation: Department of Biology and Department of Computer Science, Emory University, Atlanta, GA
date: 2025-08
pdf: ../../context/papers/gkaf836.pdf
tags:
  [
    dna-language-model,
    metagenomics,
    enzyme-annotation,
    ec-classification,
    foundation-model,
    reference-free,
    prokaryotic-genomics,
    microbiome,
    bert-encoder,
    fine-tuning,
    dan-domain,
  ]
---

# Deciphering enzymatic potential in metagenomic reads through DNA language models

## TL;DR

The Bromberg lab presents two compact DNA language models for metagenomics: **REMME**, a 1.66M-parameter BERT-style
encoder pretrained on 53.6M short reads (60–300 bp) from 1496 marine prokaryotic genomes via masked-token prediction
plus auxiliary coding-fraction and reading-frame heads; and **REBEAN**, REMME fine-tuned on 19M mi-faser-annotated
metagenomic reads to assign each read to one of seven first-level EC classes or non-enzyme. The pitch is a
**reference-free, assembly-free** alternative to the BLAST/HMMER/DIAMOND pipelines that dominate metagenomic functional
annotation today. REBEAN reports ~80.6% test accuracy and 0.969 macro-AUC on mi-faser labels, ~88% accuracy and 0.79
average AUROC on a UniProt experimentally-validated holdout (read-level), rising to 0.89 AUROC at the gene level via
score aggregation. Without being trained for it, the model concentrates high-confidence predictions on reads overlapping
catalytic and binding residues. Models and code are public on Bitbucket (`bromberglab/rebeanpkg`) plus a hosted web
service. For Dan, this paper sits squarely in his domain and is one of the most directly Linus-actionable papers in the
Group A foundation-model wave.

## The problem (in plain language)

Most bacteria and archaea on Earth have never been cultured. We learn about them by sequencing bulk DNA from
environmental samples — soil, seawater, gut, hydrothermal vent — getting hundreds of millions of short reads, and trying
to figure out what genes are there and what they do. The dominant workflow: (1) assemble reads into contigs, (2) call
genes, (3) translate to protein, (4) BLAST/DIAMOND/HMMER against curated references (UniRef90, KEGG, eggNOG, Pfam) to
assign function. Each step throws away signal. Assembly fails on rare organisms with low coverage. Reference matching by
definition cannot find anything that doesn't already look like a known thing. The downstream catalogues (KEGG,
eggNOG-mapper, HUMAnN3, mi-faser, Carnelian) all inherit this homology-bound horizon.

The authors' framing is that microbial "dark matter" stays dark precisely because every annotation tool defines function
via similarity to something already annotated. They want to move directly from a 60–300 bp read to an enzyme class
label, with no assembly, no translation, and no alignment — using a learned representation of read context instead. The
paper is also a counter-pitch to the de novo design line of dLM work (Evo, ProGen): annotating the existing rich
diversity of natural sequences should come before generating synthetic ones.

## What they propose

**REMME (Read EMbedder for Metagenomic Exploration).** Encoder-only transformer, six layers, eight attention heads,
128-dim token and position embeddings, GELU + 0.10 dropout, **1,662,177 trainable parameters**. Tokens are overlapping
nucleotide triplets with stride one. Pretraining data is 53.6M representative reads (after 80% MMseqs identity
clustering) drawn from 1496 marine prokaryotic MGnify assemblies, split 59/25/16 train/val/test. The training objective
is multi-task: (i) BERT-style masked-token prediction on triplets (15% masking, 80/10 split), (ii) regression head
predicting the fraction of coding nucleotides in the read, (iii) four-way classification head predicting reading frame
(frames 1/2/3 or non-transcribed). Sum of three losses, backpropagated jointly, 53 epochs. The auxiliary heads exist
explicitly to push the model past surface nucleotide statistics into biological context.

**REBEAN (Read Embedding-Based Enzyme ANnotator).** REMME's six encoder layers plus a three-dense-layer classifier head
producing eight logits (seven EC classes + non-enzyme). Fine-tuned for 188 epochs with AdamW + cosine restarts on 19M
reads from 19,316 metagenomic samples spanning soil, marine, freshwater, sediment, phyllosphere, and anthropogenic
environments. Labels come from **mi-faser** (the lab's prior alignment-based annotator, ~90% precision at 4th-level EC,
~50% recall). Class balance is enforced by downsampling non-enzyme reads to ~2.4M. Training is restricted to the first
106 nucleotides per read (mean − 1 SD) to remove length bias. An ablation training the classifier from random
initialization rather than REMME weights tops out at 30% accuracy after 200 epochs versus REBEAN's 80.6% — pretraining
is doing the work.

**Evaluation framework.** Five purpose-built datasets: SPEnzset1/2 from SwissProt experimentally-validated enzymes,
SPset for enzyme-vs-non-enzyme, Orthoset1/2 from OrthoDB orthologous pairs, MarineMGset from 3820 marine MAGs, and
ExtremeMGset (8M reads from hydrothermal vents, hypersaline lakes, salt crystallizer ponds — environments where
references are weakest). The ExtremeMGset compares REBEAN head-to-head with HUMAnN3, mi-faser, Carnelian, LookingGlass,
and a DIAMOND/UniRef90 baseline.

## Key results

- **Pretraining diagnostics.** REMME hits >98.5% masked-token accuracy across train/val/test. Coding-fraction prediction
  correlates with ground truth at Pearson r = 0.73 (MSE 0.04). Reading-frame classification reaches 48.6% accuracy /
  0.789 AUC (random = 25%); coding vs. non-coding reads are separated at 88.5% accuracy.
- **REBEAN on mi-faser-labeled holdout.** 80.6% test accuracy, 0.969 macro-AUC, 80.1% recall / 83.6% precision on
  read-level seven-class EC prediction. Random baseline is 12.5%.
- **REBEAN on experimentally-validated holdout (SPEnzset1, 4295 prokaryotic enzymes, 525,775 synthetic 200 bp reads).**
  Read-level: 88.1% accuracy, 33.4% recall, 71.5% precision, average AUROC 0.79 (range 0.73–0.90 across classes) at
  threshold 0.5. At 90% precision, average recall drops to 23%. Gene-level (averaging scores across reads of one gene):
  AUROC 0.89 (range 0.86–0.97), 48% recall at 90% precision. Performance scales with sequencing depth — recall at 90%
  precision rises from ~30% to ~65% as reads-per-kb goes from 1 to 50.
- **Catalytic-site enrichment (emergent).** High-confidence REBEAN reads are 50% more likely to overlap annotated
  catalytic/binding residues than other reads — and translations of high-scoring reads are spatially closer in 3D to
  functional sites in both crystal and AlphaFold2 structures. The model was never trained on functional-site
  annotations.
- **Ortholog detection.** Average read-embedding cosine similarity discriminates orthologous from non-orthologous gene
  pairs at 0.84 AUROC (genus-level: 0.88; phylum: 0.81), substantially beating MMseqs sequence identity (~0.32 AUROC).
  Embedding similarity is largely independent of sequence identity (|r| < 0.07), confirming the embeddings carry
  information beyond k-mer similarity.
- **Extreme-environment benchmark vs. existing tools.** On 8M reads from hydrothermal/hypersaline/salt-crystallizer
  samples, REBEAN agrees strongly with mi-faser (Cohen's κ = 0.945) and DIAMOND (κ = 0.880), and shares the largest
  fraction of jointly annotated reads with each baseline — while annotating substantially more reads than
  alignment-based tools alone. The headline practical claim is _increased recall on novel reads at retained precision_.
- **Novel-enzyme mining.** Applied to 124M synthetic reads from 3820 marine MAGs, REBEAN flagged 12.86M reads as
  enzymatic at >0.9 confidence and 3.02M as oxidoreductases. After restricting to genes with no prior MGnify annotation
  and clustering at 30% identity, 39,617 putatively novel proteins were identified; ESMFold structures for 32,030 of
  them showed 2–3.7× enrichment for SwissProt oxidoreductase Pfams (hypergeometric p < 1E−32). 4901 oxidoreductases
  passed the 90% precision gene-level threshold.
- **Availability.** Models, weights, and supplementary scripts at `https://bitbucket.org/bromberglab/rebeanpkg`;
  Figshare DOIs `10.6084/m9.figshare.29366837.v1` and `10.6084/m9.figshare.29286734.v1`; hosted free web service at
  `https://services.bromberglab.org/rebean/`. Open Access (CC-BY-NC).

## What's reusable in Linus

**Direct, Phase 7 (Skills & Autonomy).** REBEAN is a strong candidate for the first **domain-specific Linus Worker**
outside coding/general Q&A. The model is tiny (1.66M parameters — runs trivially on CPU let alone Metal), the workflow
(FASTQ → per-read EC labels → aggregate to gene → cross-reference with KEGG/Pfam) is well-defined, and Dan's
metagenomics background means he can both spec the tool and judge its outputs. A "metagenomic enzyme annotation" skill
exposed as an OpenAI-compatible tool call would let any front-end (Claude Code, openclaw, future native UI) trigger
reference-free annotation of a sample directly from the chat. This is the first concrete instance of a Linus tool that
is plausibly _better_ than what a hosted general-purpose Claude can do, because Claude can't run REBEAN on a 100 GB
FASTQ.

**Direct, Phase 6 (Fine-Tuning).** REMME's pretraining recipe is a near-perfect fit for Apple Silicon: 1.66M params is
two orders of magnitude under any LoRA-on-7B budget. Reproducing or extending REMME on M1 Max via MLX is a tractable
end-to-end pretraining exercise for the project — possibly the only foundation model in the Group A wave (Evo 2 at 7B+,
AlphaGenome, LucaOne, Bacformer all much larger) where Dan can plausibly do **full pretraining** locally rather than
only LoRA. The auxiliary multi-task heads (coding fraction, reading frame) generalize to any pretraining-from-scratch
reproducibility study.

**Direct, Phase 3 (Knowledge & Parallel Agents).** REBEAN annotations are first-class **KnowledgeBase node candidates**:
each read → EC class → gene → MAG → metagenome sample → environment forms a natural multi-edge graph that maps cleanly
onto the KG schema KnowledgeBase is being built around. Dan's existing paper corpus already contains the literature
scaffolding for the EC/Pfam/KEGG ontologies; pairing those ontology nodes with REBEAN-derived empirical instances from
Dan's own (or public) sequencing data is a concrete Phase 3 deliverable that exercises both the KG and parallel-agent
execution (each MAG annotation is embarrassingly parallel).

**Direct, Phase 2 (MVP).** The DIAMOND/HMMER comparison framing in the paper is the right template for Linus' first
**side-by-side benchmark** of a learned vs. classical bioinformatics tool. A `benchmarks/dan_tasks/metagenomics/` task
that runs REBEAN, mi-faser, and DIAMOND on a held-out sample and reports Cohen's κ, recall at fixed precision, and
wall-clock time per million reads would be a directly informative Phase 2 milestone — and the paper's ExtremeMGset is
reproducible because the SRA accession lists are in supplementary tables.

**Indirect, methodology.** The masked-token + auxiliary-task pretraining recipe (sequence reconstruction +
structural-property regression + classification head) generalizes beyond DNA. Any future Linus-specific encoder over
Dan's domain corpora (chemical SMILES, mass-spec, scientific text fragments) could borrow the same template.

## What's NOT applicable

**Resolution ceiling.** REBEAN classifies only the **seven first-level EC classes**, not the 4-level EC hierarchy
practitioners actually want (e.g., 1.14.13.1, "salicylate 1-monooxygenase"). For most bench-biology and
pathway-reconstruction use cases, "this read is an oxidoreductase" without a substrate guess is a starting point, not an
answer. Linus should treat REBEAN as a **filter/pre-screen** handing candidates off to a downstream specific-EC tool,
not as a final answer.

**Read length and platform.** Training is restricted to the first 106 nucleotides per read; the sweet spot is short-read
Illumina (60–300 bp). Long-read platforms (Nanopore, PacBio HiFi at 10–25 kbp) need a different architecture or
sliding-window inference.

**Marine prokaryotes only in REMME pretraining.** Pretraining used 1496 marine prokaryotic genomes. Applicability to
fungal, viral, or plant-host-associated metagenomes is unvalidated; eukaryotic intron structure and viral genomic
compaction are out of distribution. Don't assume out-of-the-box performance on a soil fungal or phage-heavy gut sample
without re-validation.

**Weight format unspecified.** The paper says models and scripts are on Bitbucket but doesn't specify framework (PyTorch
/ TF / ONNX / MLX). MLX-compatibility almost certainly requires a port — trivial at 1.66M params, but still a port.

**Recall/precision asymmetry.** At read level, REBEAN trades a lot of recall for precision (33.4% recall at threshold
0.5 on validated enzymes). It's conservative and aggregates well at the gene level, but anyone expecting Pfam-HMMER
per-read sensitivity will be disappointed.

**No generation, no design.** Purely discriminative — none of the de novo design pipeline Evo 2 or ProGen offers is on
the table.

## Connections

**Within the Group A foundation-model wave.** REMME/REBEAN is the **smallest and most narrowly-scoped** model in the
wave — 1.66M parameters, encoder-only, single-domain (prokaryotic short reads), single downstream task (EC
classification). **Evo 2** (7B+, autoregressive, full genomes, generation-capable) is the maximalist counter-pitch the
authors explicitly push back against; REBEAN is _deployable now_, Evo 2 is _study-and-watch_. **AlphaGenome**
(regulatory variant prediction) is a sibling discriminative DNA model on a different downstream task — together they
sketch a layered annotation stack. **LucaOne** (joint DNA/RNA/protein) and **Bacformer** (bacterial genome PLM) are
larger multimodal/whole-genome competitors; REBEAN's narrow design is its strength on a 32 GB MacBook. **RiNALMo**,
**ProteinReasoner**, and **METL** round out the omics sweep — REBEAN is the only Group A model operating directly on raw
sequencing reads.

**Within Linus architecture.** REBEAN connects to the **memory pillar** through KG-friendly output (read → EC → gene →
genome → environment), to the **inference layer** as a sub-100 MB model running alongside Ollama Workers without
competing for memory, and to the **orchestration layer** as the first tool whose value comes from doing something Claude
cannot do (run on a 50 GB FASTQ locally, in private). The paper's framing — most metagenomic methods are
reference-bound, the field needs a paradigm shift — echoes the "delete the requirement" stance in CLAUDE.md's Algorithm.
Reference databases are a requirement REBEAN deletes.

## Open questions for Dan

1. **Is the Bitbucket release directly usable, or does it need an MLX port?** Action item: clone
   `bromberglab/rebeanpkg`, check framework + license + checkpoint format. At 1.66M parameters a PyTorch → MLX port is
   hours of work, not weeks. Worth queuing as an experiment when bandwidth allows.
2. **How does REBEAN compare to your current go-to tools?** You almost certainly use some combination of eggNOG-mapper,
   KEGG-via-BLAST/HMMER, possibly mi-faser itself given Bromberg lab is upstream of much of this. A side-by-side on a
   sample you already have ground truth for would settle whether REBEAN earns Linus inclusion or just gets noted.
3. **Can REMME-from-scratch be the Linus pretraining proof-of-concept?** It's small enough that _full_ pretraining on M1
   Max with MLX is genuinely feasible — not LoRA, not adapter, real pretraining. That would be a Phase 6 milestone
   unlike any other in the wave (Evo 2 / Bacformer / LucaOne are not retrainable on a laptop; REMME is). Worth a spike?
4. **EC depth roadmap.** First-level EC is interesting but practitioners want 4-level. Is there appetite for Linus to
   host a fine-tuned per-class downstream classifier (REMME → "if predicted EC 1, run a finer EC 1.x.y.z model") — and
   would that be Worker work or Maestro-spec work?
5. **KnowledgeBase schema implications.** If REBEAN annotations become KG nodes, do read-level annotations live as
   ephemeral evidence linked to gene/genome nodes, or as first-class entities? The volume difference is 4–5 orders of
   magnitude (genes ~10⁴–10⁵ per sample, reads ~10⁸–10⁹). Worth a brief schema-design conversation before any production
   run.
6. **Privacy angle.** Some metagenomes (human gut, clinical) are sensitive. A reference-free, locally-run annotator
   avoids the data-residency problems of uploading to KEGG/MG-RAST/MGnify web services. Is that a use case you'd
   actually want — or is your work primarily on public/environmental samples where this isn't a concern?
