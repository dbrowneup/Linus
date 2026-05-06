# Biological Foundation Models Synthesis

## What this document is

A synthesis of eight Group A papers — pretrained foundation models over DNA, RNA, proteins, bacterial genomes, and
metagenomic reads — read through one question: _which of these become Linus skills, in what order, at what cost, and
what does the constellation imply about Linus's biological tool registry?_ The eight one-pagers live in
[`docs/paper-notes/`](../paper-notes/), listed at the bottom. The audience is the same as the
[memory](memory-synthesis.md) and [skills](skills-and-practices-synthesis.md) syntheses: input to the next round of
edits to [paper-landscape.md](../landscapes/paper-landscape.md), [total-landscape.md](../landscapes/total-landscape.md),
and the Phase 6/7 spec backlog.

The headline claim: **Group A is the first Wave 1 batch where Linus's value proposition is unambiguously domain-specific
rather than infrastructural.** Six of eight models release weights under permissive or near-permissive licences; five of
eight are operationally deployable on M1 Max with caveats; and the smallest (REMME/REBEAN at 1.66 M, METL at 2.5–50 M)
are small enough that Linus can plausibly retrain or fine-tune from scratch rather than only consume released
checkpoints. Group A also forces the first sharp tool-registry decision: one biological generalist (LucaOne) or a
constellation of specialists? The papers argue both sides credibly, and the recommendation below splits the difference,
but the open question is sharp enough to bring back to Dan as a deliberate decision.

---

## The papers at a glance

[**Evo 2**](../paper-notes/s41586-026-10176-5.md) (Arc Institute, _Nature_ 2026) — 7B / 40B StripedHyena 2 hybrid
trained on 9.3 T DNA bp across all domains of life with a **1 M-token context at single-bp resolution**, fully open
weights / code / OpenGenome2 / SAEs. [**LucaOne**](../paper-notes/s42256-025-01044-4.md) (Alibaba DAMO, _Nat Mach
Intell_ 2025) — 1.8 B encoder pretrained jointly on DNA + RNA + protein with a unified 39-token vocabulary;
central-dogma capability emerges from joint training; CC-BY-4.0. [**AlphaGenome**](../paper-notes/s41586-025-10014-0.md)
(DeepMind, _Nature_ 2026) — single-pass U-Net + transformer ingesting **1 Mb of DNA** to predict 5,930 functional
genomic tracks at single-bp resolution across eleven modalities; weights and code open, hosted SDK non-commercial-only.
[**RiNALMo**](../paper-notes/s41467-025-60872-5.md) (Penić et al., _Nat Commun_ 2025) — 650 M-parameter encoder-only RNA
LM with the modern recipe (RoPE, SwiGLU, FlashAttention-2); **first learned RNA model to convincingly generalize across
held-out RNA families**. [**Bacformer**](../paper-notes/2025.07.20.665723v2.md) (Wiatrak et al., bioRxiv 2025) —
12-layer transformer treating a bacterial genome as an **ordered sequence of proteins** (each protein embedded with
frozen ESM-2); predicts operons, essentiality, KEGG function, 139 phenotypic traits; Apache 2.0.
[**ProteinReasoner**](../paper-notes/2025.07.21.665832v2.md) (Liu et al., BioMap, bioRxiv 2025) — multi-modal PLM that
inserts the **MSA-derived evolutionary profile as an explicit predicted intermediate modality** between sequence and
structure; beats ESM3-Open and DPLM-2 at 150 M / 650 M; **checkpoints not announced**.
[**METL**](../paper-notes/s41592-025-02776-2.md) (Gelman et al., _Nature Methods_ 2025) — small (2.5–50 M-param) protein
LM pretrained on **Rosetta biophysical simulations** rather than natural sequences; designs functional GFP variants from
only 64 wet-lab points. [**REMME / REBEAN**](../paper-notes/gkaf836.md) (Prabakaran & Bromberg, _NAR_ 2025) — **1.66
M-parameter** BERT-style DNA LM over 60–300 bp metagenomic reads (REMME) plus a fine-tuned EC-class annotation head
(REBEAN); reference-free, assembly-free annotation that beats homology tools on extreme environments.

---

## The constellation: specialist vs generalist FMs

Group A is best read as a constellation along one dominant axis — **generalist breadth versus specialist depth** — with
a secondary axis of **operational reach** on M1 Max.

At the _generalist_ extreme sits **LucaOne**, the only model spanning DNA, RNA, and protein in a single shared embedding
space. The unified 39-token vocabulary plus a token-type embedding is the operationalisation of the central-dogma claim,
and the few-shot DNA-protein matching result (LucaOne 0.84 vs DNABert2+ESM2 0.73 ([s42256-025-01044-4](../paper-notes/s42256-025-01044-4.md))) is the cleanest evidence in the corpus
that joint training learns what neither half can learn alone. A step inward sits **Evo 2**, generalist _within_ DNA: 9.3
T base pairs across all three domains of life, zero-shot variant scoring, generative as well as discriminative, 1
M-token context.

At the _specialist_ extreme sit the rest. **RiNALMo** bets that ncRNA-only pretraining with diversity-clustered batching
produces stronger inter-family generalisation than any cross-modal prior. **AlphaGenome** bets that supervised
multimodal heads on functional genomic tracks dominate unsupervised likelihood scoring on regulatory variants — the
+25.5% sweep over Borzoi on eQTL sign prediction is the evidence. **METL** bets that _simulation_ data is the right
pretraining substrate where natural sequences are silent on the off-distribution mutations engineers actually want.
**ProteinReasoner** bets that protein-CoT (the MSA profile as an explicit predicted intermediate) delivers the same
expressivity gain as text CoT. **Bacformer** bets that the right unit for bacteria is the genome as an ordered protein
sequence. **REMME/REBEAN** bets that you should annotate raw sequencing reads directly with a tiny model that beats
homology baselines exactly where homology breaks down.

The empirical evidence is mixed in a clarifying way. LucaOne's discussion explicitly concedes that small specialised
models occasionally outperform large pretrained ones. RiNALMo beats SpliceBERT (pretrained exclusively on pre-mRNA) on
splicing despite seeing no mRNA at all ([s41467-025-60872-5](../paper-notes/s41467-025-60872-5.md)). AlphaGenome beats Evo 2 on the regulatory variant subdomain where Evo 2's own
paper acknowledges trailing ChromBPNet. Bacformer beats fine-tuned Evo on bacterial gene essentiality. **Neither pure
strategy survives contact with the evidence.** A LucaOne-only registry would underperform on regulatory variants,
scarce-data protein engineering, bacterial genome analysis, and metagenomic annotation. A pure specialist registry would
be operationally heavy and would lose LucaOne's cross-modal embedding geometry — the natural anchor for a multi-modality
biological knowledge graph.

The right Phase 7 design is layered: **LucaOne (or an open small embedding model) as the cross-modal default and KG
anchor; specialists invoked when the task is in their named domain.** The router needs to know which specialists apply
to which task shapes; the specialists need to know they are not the default.

---

## Cross-cutting threads

### Open weights vs hosted-or-restricted release

The release posture across the eight papers is more uniform than the broader LLM landscape, and broadly favourable to
Linus. **Five releases are unambiguously open and locally deployable**: Evo 2 (weights, code, OpenGenome2, SAE
checkpoints), LucaOne (CC-BY-4.0), RiNALMo (Zenodo weights, public fine-tuning scripts), Bacformer (Apache 2.0 on
HuggingFace), and REMME/REBEAN (Bitbucket, CC-BY-NC, plus a hosted free web service). **METL is also fully open** —
code, weights, HuggingFace Spaces demo, Colab notebooks, the Rosetta data-generation pipeline.

**AlphaGenome is the hybrid case.** Source code, weights, and variant scoring implementations are openly available at
`github.com/google-deepmind/alphagenome_research`; the hosted Python SDK and API at
`deepmind.google.com/science/alphagenome` are non-commercial- only. Strictly better than AlphaFold-3's early API-only
era — the weights are out — but the licensing footnote matters if Linus ever surfaces AlphaGenome client-facing.

**ProteinReasoner is the open question.** The paper does not announce checkpoint release, and the methods describe an
internal BioMap training stack. Until checkpoints land, ProteinReasoner is an architecture lesson, not a Linus Worker.

The implication is concrete: **six of eight are immediately candidates for a local Linus skill; one needs a deliberate
decision about the API path; one is on hold pending BioMap.** This is unusually favourable for a "private, local, no
paid APIs required" project, and worth flagging in Phase 4: the biology field has so far chosen openness more often than
the text field.

### Modern Transformer recipe convergence and data-curation patterns

The dominant recipe is uniform across the corpus. **RoPE, SwiGLU, FlashAttention-2, and pre-layer normalisation** appear
together in RiNALMo, LucaOne, and ProteinReasoner; Bacformer uses RoPE for the same context-extrapolation reason;
AlphaGenome uses the same primitives at the transformer-layer level inside its U-Net. Evo 2 is the deliberate exception
— StripedHyena 2 substitutes input-dependent convolutions for most of attention to make 1 M-token context tractable at
40B at ~3× the throughput of a tuned Transformer.

The implication is that **the same recipe Linus's text Workers will use is the recipe biology FMs are converging on.**
The MLX, llama.cpp, and HF transformers stacks Linus invests in for text inference will broadly transfer to most Group A
models out of the box. The exceptions (Evo 2's hyena operators, ProteinReasoner's three separate decoder heads, METL's
3D structure-based position embedding) need bespoke conversion. This argues for prioritising the standard-recipe models
in Phase 7 over Evo 2, where local-inference plumbing is not yet mature.

A second pattern worth naming: RiNALMo's **diversity-clustered batching** (cluster 36 M sequences at 70% identity into
17 M clusters, sample one per cluster per minibatch ([s41467-025-60872-5](../paper-notes/s41467-025-60872-5.md))) is "data curation as architecture." A few lines of data-loader code
that produced the inter-family generalisation gain. This is a candidate Linus engineering convention to adopt the moment
any Linus-trained model has a sequence corpus large enough to benefit.

### Long context vs resolution

Evo 2 (1 M-token context at single-bp) and AlphaGenome (1 Mb input window at single-bp output across 5,930 tracks) each
refuse the field's long- standing length-vs-resolution trade-off. The other six models are short-context: RiNALMo's
pretraining cap is 1024 tokens, LucaOne's is 1280, ProteinReasoner trains on single proteins, METL is per-protein,
REMME's context is 60–300 bp per read, and Bacformer's tokens are proteins (so 1024 protein-tokens covers a small
bacterial genome but at the nucleotide level it operates on frozen per-protein ESM-2 embeddings).

The operational implication for M1 Max is severe: **the long context will not be available locally regardless of model
size.** Activation memory at 1 M tokens for Evo 2 40B is incompatible with 32 GB unified memory; for Evo 2 7B at FP16
the weights alone are ~14 GB, leaving little room for non-trivial context. The realistic local envelope for Evo 2 is the
7B model at 4-bit / 8-bit with 32 k–128 k context. Long context becomes a remote-endpoint feature; the local default is
short-context. The router should know which tasks require long context (rare — a few classes of genome-scale generation)
and which do not (most variant scoring, all RNA structure prediction, most protein engineering, all metagenomic
annotation).

This is the same lesson the [memory synthesis](memory-synthesis.md) articulated for text LLMs from a different angle:
long context is useful but not a substitute for an architectural memory layer when you are memory-bound.

### Generalisation and the simulation-pretraining outlier

The most striking cross-distribution results come from the smaller and more tightly curated models. RiNALMo's
leave-one-family-out victory on ArchiveII (8 of 9 families) is the cleanest evidence that _generalist within a modality_
with diversity-clustered curation produces representations that transfer to unseen sub-distributions. Evo 2's zero-shot
variant scoring across all three domains of life is the broadest cross-domain generalisation in the corpus — and the
BRCA1 ridge-regression result (AUROC 0.95 on noncoding SNVs, beating every supervised baseline) shows the learned
representation is rich enough that a tiny supervised head recovers clinical-grade performance. **Scientific
applicability of these models is largely a function of how well they generalise off the training distribution**, because
that is where the real interpretive work happens — ClinVar variants of uncertain significance are unseen by definition,
newly discovered ncRNAs are off-distribution by definition.

METL is the genuine pretraining-substrate outlier. Every other Group A paper pretrains on natural sequences; METL is the
only paper that pretrains on **synthetic data from biophysical simulation** — millions of variants per target protein,
run through Rosetta to extract 55 biophysical attributes, with the trained encoder predicting those attributes from
sequence. The motivating argument is mechanistic: protein engineering wants to know what happens at non-natural
mutations, and natural sequences are silent on that regime by definition. The evidence is the GFP design experiment
(fine-tune on 64 wet-lab variants, synthesise 20, get 16 functional ([s41592-025-02776-2](../paper-notes/s41592-025-02776-2.md))) and the "29 simulated points ≈ 1 experimental
point" trade-off heuristic ([s41592-025-02776-2](../paper-notes/s41592-025-02776-2.md)). The pattern generalises beyond proteins — **simulation-pretrained, observation-fine-tuned**
applies to any Linus domain with scarce real data plus a slower-but-correct simulator (enzyme kinetics, RNA folding,
docking, spectroscopy). Worth lifting to a named architectural pattern in `docs/syntheses/` once a second clean instance
lands.

### M1 Max viability: what Dan can actually run, fine-tune, retrain

The eight models sort cleanly. **REMME/REBEAN (1.66 M)** is trivially local and plausibly the only model in the wave
where Dan can do **full pretraining from scratch on M1 Max** via MLX, not just LoRA. **METL (2.5–50 M)** is comfortable
for inference; fine-tuning the 20 M Global was 20–42 min on an A100, so single-digit-hour territory on M1 Max via MLX.
**Bacformer** (small transformer atop frozen ESM-2 35M) is comfortable for inference and fine-tuning; per-genome
analysis is seconds to minutes locally. **RiNALMo (650 M)** is comfortable for inference at any precision; LoRA
fine-tuning is at the upper edge but tractable; full unfrozen fine-tuning is not 32-GB-tractable. **LucaOne (1.8 B)** is
edge-of-comfort — should fit at FP16 with care, comfortably at INT8/INT4, LoRA in range, PyTorch→MLX conversion needed
but the encoder is standard. **ProteinReasoner (150 M / 650 M)** would fit comfortably; blocked on checkpoint release,
and format conversion will be non-trivial because of the three separate decoder heads. **AlphaGenome** is the central
unknown — a Phase 1 spike (clone, inspect, attempt one inference on a 1 Mb interval) is the right next step. **Evo 2**
is the genuinely hard case: 40B is firmly out of M1 Max range; 7B at 4-/8-bit with reduced context is plausible _if_
StripedHyena 2 plumbing exists in MLX or llama.cpp, which it does not yet — the **central operational unknown** for any
Evo 2 skill.

**Five of eight are local Workers without significant engineering plumbing** (REMME/REBEAN, METL,
ProteinReasoner-when-released, Bacformer, RiNALMo). **One needs MLX conversion** (LucaOne). **One needs a Phase 1
spike** (AlphaGenome). **One is genuinely operationally hard locally** (Evo 2, possibly remote-endpoint at 40B).

### KnowledgeBase implications

Each model produces outputs that map onto KG nodes, edges, or attributes, and the right integration is
modality-specific. **LucaOne embeddings** are the cross-modal anchor: same-gene DNA and protein converge in the
embedding space without paired training, which is exactly the property a KG needs to link "the EGFR gene" and "the EGFR
protein" as the same entity in two modalities. **AlphaGenome ISM outputs** identify the specific motif a variant creates
or disrupts and link to JASPAR matrix IDs — an obvious join key for a regulatory-genomics KG (variant → motif → TF →
pathway → disease). **Bacformer phenotype attributions** are weighted gene→trait edges; the released 1.3 M-MAG
annotation cache for 32 traits is itself a candidate ingest. **REBEAN annotations** form a multi-edge graph (read → EC →
gene → MAG → sample → environment).

The cross-cutting design implication: **KnowledgeBase should expose a typed `model_prediction` edge class** carrying the
producing model, version, confidence, and content hash. This generalises the
[LLM wiki synthesis](llm-wiki-synthesis.md)'s claim-typing pattern to model-derived claims: a predicted operon from
Bacformer is an `[!analysis]` claim with specific provenance, distinct from an `[!source]` claim from a curated
database. When the model is updated, the content-hash mechanism flags the KG edges that need revalidation. Without this
discipline, model-derived KG content becomes indistinguishable from curated content within months.

**OptimusKG** ([2604.27269v1](../paper-notes/2604.27269v1.md)) provides a mature reference for biomedical knowledge-graph design at scale: a unified ontology across 18 sources, 190K+ nodes and 21.8M edges with explicit FAIR principles, evidence grounding, and property-rich metadata. While OptimusKG's full integration is deferred (it covers biomedical-only domains and requires 18+ external ontology harmonization), its medallion architecture (Landing → Bronze → Silver → Gold layers) and provenance-tracking schema are directly reusable patterns for Phase 3's KnowledgeBase integration of Group A model outputs.

---

## Implications for Linus skills (Phase 7)

Recommended sequence: **REBEAN first, then paired RiNALMo + Bacformer, then hybrid AlphaGenome + Evo 2 variant scoring,
with LucaOne and METL added on concrete demand.**

**Skill 1: `linus.bio.metagenomics.annotate`** (REBEAN). The easiest first skill: 1.66 M parameters, well-defined
workflow (FASTQ → per-read EC → aggregate to gene), Dan's metagenomics background lets him spec and judge. Plausibly
_better_ than what hosted Claude can do, because Claude cannot run REBEAN on a 50 GB FASTQ. The right pattern-setter for
Phase 7. Effort: a focused week.

**Skill 2: `linus.bio.bacterial_genome.analyse`** (Bacformer). Natural companion to REBEAN. Operon prediction, gene
essentiality, KEGG function (188 classes), and 139-trait phenotype inference as zero-shot or fine- tuned heads. Apache
2.0 on HuggingFace; custom architecture so MLX needs custom code but the model is small. **Analytical heads only
initially**; defer the generative head behind explicit per-call confirmation pending a SAFETY.md update — the authors
flag the dual-use surface themselves.

**Skill 3: `linus.bio.rna.predict_structure`** (RiNALMo). 650 M params, public Zenodo weights, modern recipe so MLX
conversion is straightforward, strongest published inter-family generalisation in the RNA-LM literature. Surface the
telomerase failure mode in the tool description.

**Skill 4: `linus.bio.dna.score_variant`** (AlphaGenome + Evo 2 hybrid). Most clinically relevant for Dan's domain.
Internal router: regulatory variants in human/mouse → AlphaGenome (more accurate, multimodal, mechanistic ISM); other
variants or non-human/non-mouse → Evo 2. Both backends need a Phase 1 spike before commitment.

**Deferred:** LucaOne (strong as the cross-modal embedding backbone for KG integration but standalone task value is less
sharp; add when KG integration is being built in Phase 3); METL (strong if Dan has a near-term protein engineering task;
otherwise speculative — worth a yes/no decision). **Blocked:** ProteinReasoner (architecture lesson pending BioMap).

The tool-registry organisation question — one molecular-biology skill versus separate DNA/RNA/protein/metagenomics
skills — should resolve toward **separate skills per modality plus task type**. The underlying models, validity domains,
output types, and failure modes genuinely differ; a single mega-skill would be operationally fragile and would obscure
per-tool caveats Dan needs visible.

---

## Implications for Linus fine-tuning (Phase 6)

**METL is the right Phase 6 first exemplar.** Fully public, biology-relevant, 20 M-param Global fine-tuning was 20–42
min on an A100 — a low-risk MLX+LoRA stress test on a real foundation model. The
[paper-note](../paper-notes/s41592-025-02776-2.md) recommends a `experiments/metl-m1-fine-tune.md` spike; this synthesis
seconds it.

**REMME/REBEAN is the right Phase 6 _full pretraining_ candidate.** At 1.66 M params the entire recipe (53.6 M reads,
multi-task loss with auxiliary coding-fraction and reading-frame heads, 53 epochs) is plausibly reproducible end-to-end
on M1 Max via MLX. **Unique opportunity in the corpus** — every other model is too large for full local pretraining. A
successful reproduction establishes that Linus can do real pretraining of small foundation models, not just consume
released checkpoints.

**RiNALMo and LucaOne** are LoRA fine-tuning candidates at edge-of- comfort. RiNALMo on a Dan-specific RNA corpus
(riboswitches, structure- probed RNAs); LucaOne via downstream-head fine-tune on a frozen encoder (cheaper than LoRA —
the paper deploys downstream tasks this way). **Bacformer** (small transformer atop frozen ESM-2) is fine-tunable
locally. **AlphaGenome and ProteinReasoner** are not realistic fine-tuning candidates locally.

The METL pattern (**simulation-pretrained, experiment-fine-tuned**) deserves consideration as a named Linus
architectural pattern after a second concrete instance lands. The strongest default LoRA candidates assuming Dan picks a
target: **RiNALMo on a Dan RNA corpus** and **METL on a specific protein-engineering target**. Both have the property
that an afternoon of fine-tuning would produce a Worker noticeably better than the published baseline on Dan's specific
task — exactly the regime LoRA on M1 Max should target.

---

## Implications for Linus data sovereignty (Phase 4)

**OpenGenome2** (Evo 2's training corpus, 8.8 trillion nucleotides spanning GTDB bacteria/archaea, NCBI eukarya, IMG/VR
phage, with deliberate eukaryotic-virus exclusions for biosafety) is the headline candidate. Raw size is large but
tractable on an external SSD; nucleotide data compresses well. Mirroring lets Linus fine-tune supervised heads on Evo 2
embeddings (the BRCA1 ridge-regression pattern generalises to many clinically relevant genes), do RAG over reference
genomes, and inherit the biosafety property without auditing it ourselves. **Recommend mirroring** at the same priority
as Wikipedia / Kiwix.

**AlphaGenome's evaluation datasets** in `alphagenome_research` (fine-mapped GTEx eQTL, ENCODE-rE2G CRISPRi, CAGI5 MPRA,
ClinVar splicing) are landmark sets that generalise well beyond AlphaGenome itself — a credible starting variant-effect
benchmark suite for `benchmarks/dan_tasks/genomics/`, with AlphaGenome predictions as a reproducible reference baseline.
Modest storage (gigabytes). **Recommend mirroring.**

**Bacformer's 1.3 M-MAG phenotype annotation cache** is a candidate KnowledgeBase ingest rather than a raw mirror —
concrete Phase 3 KB enrichment that exercises both schema and parallel-agent execution. **RiNALMo evaluation sets**
(bpRNA, ArchiveII) are sub-terabyte and worth mirroring for any RNA-LM fine-tuning work. **METL's Rosetta pretraining
data** is generated, not downloaded; mirror the _generation pipeline_ (the Open Science Pool notebook) rather than the
data itself.

Total storage for the priority mirrors lands in the low-tens-of-terabytes range — a single external SSD dedicated to
biology, separate from Wikipedia/Kiwix. Phase 4 cannot mirror everything, and Group A is one of several domains
competing for the same budget; this synthesis argues Group A's share is well-justified given Dan's domain centrality,
but the trade-off should be made explicitly.

---

## Tensions and open questions

**Generalist vs specialist Worker strategy — what is the right Phase 7 default?** The recommended split (LucaOne as KG
anchor, specialists as task workers) is a hedge; whether it is also the right answer is empirical. _Sub-question:_
benchmark LucaOne against RiNALMo on a Dan-relevant RNA task and against AlphaGenome on a variant scoring task before
committing the registry architecture? A short head-to-head in `benchmarks/dan_tasks/biology/` would resolve this in a
session.

**Evo 2 vs AlphaGenome for variant prediction — both, or pick one?** The hybrid recommendation depends on both being
operationally available locally, and Evo 2 faces real plumbing risk (StripedHyena 2 quantization tooling).
_Sub-question:_ is the hybrid worth the operational cost, or is the right Phase 7 commitment "AlphaGenome as variant
scoring, Evo 2 as a separate generative DNA skill," with no internal routing?

**Should the tool registry have an `external_api_tool` class for non-locally-deployable models?** AlphaGenome's hybrid
release is the motivating case; Evo 2 40B is the second. Explicit auth, rate-limiting, cost accounting, graceful offline
fallback, trust-tier tagging — recommend an ADR.

**Is METL's simulation-pretrained pattern worth applying to other Linus domains now, or wait for a second instance?**
Recommend waiting; this synthesis is the placeholder. The risk of premature naming is generalising from a single case.

**Is a focused "Evo 2 + Wave 3 generative phage" mini-synthesis worth writing?** The Evo 2 paper-note flags an explicit
downstream application (bioRxiv 2025.09.12.675911v1) using Evo 1/2 as backbone. The pairing would land at "what does a
private generative-biology workflow look like in Linus" and would force a sharp answer to the local-vs-remote-Evo-2
question. **Recommend yes**, 1500–2000 words, scheduled as Wave 3 prep.

**Faithfulness of model-derived KG content.** Group A is the first Wave 1 batch where the volume of model-derived KG
content is large enough to make claim-typing load-bearing. _Sub-question:_ does the KnowledgeBase schema need a
`model_prediction` edge class with explicit producing-model

- version + confidence + content-hash provenance before Group A skills start writing back? Recommend yes.

**ProteinReasoner checkpoint release** — worth a low-priority watch on BioMap GitHub and the `airkingbd` HuggingFace
org.

**AlphaGenome non-commercial licence — does it constrain Linus's long-term posture?** If Linus is ever offered as a
service to others (the [skills synthesis](skills-and-practices-synthesis.md) flags scientific literature intelligence as
a near-term opportunity), the API path is closed and the only legal path is the released weights run locally. The hybrid
release means this is workable _if_ the local-deployability spike lands cleanly.

---

## Where this synthesis fits

Group A is the first Wave 1 batch where the Linus value proposition is unambiguously domain-specific rather than
infrastructural. The [memory](memory-synthesis.md), [skills](skills-and-practices-synthesis.md),
[security](security-synthesis.md), and [LLM wiki](llm-wiki-synthesis.md) syntheses are all infrastructural claims about
how Linus is built. **Group A is the first batch that says clearly what Linus does for Dan that hosted Claude cannot.**
It runs a private 1.66 M-parameter model over a 50 GB FASTQ from a sensitive metagenomic sample. It scores BRCA1 VUS
with a learned representation beating every supervised baseline. It predicts operons, essentiality, and 139 phenotypic
traits on an assembled MAG Dan never wants to upload. It designs functional GFP variants from 64 wet-lab training
points, locally. These concrete capabilities motivate the entire project.

The synthesis connects to the **memory pillar** through the KnowledgeBase-as-semantic-memory layer (Layer D): each Group
A model produces typed KG-relevant outputs, and the right way to integrate them is via a `model_prediction` edge class
with explicit provenance and content hashes, generalising the LLM wiki synthesis's claim-typing discipline to
model-derived claims. The connection to the eventual **Group D synthesis** (agentic systems) is that Group A models are
the _tools_ Group D agents will call — a Phase 3 `variant-batch` agent fanning ClinVar variants to AlphaGenome is
exactly the parallel-agent pattern Group D will formalise. The connection to the **skills synthesis** is the sharpest:
that synthesis argued domain expertise is itself a moat for Dan, and that Linus's design should draw the Maestro/Worker
boundary so Workers handle well-specified scientific data tasks while Dan's judgment applies to hypothesis generation
and output interpretation. **Group A is the concrete realisation of that boundary.** REBEAN classifies reads; Dan judges
whether the novel-enzyme candidates are biologically plausible. AlphaGenome predicts mechanism; Dan judges whether it's
consistent with the patient phenotype. This is the moat in operation.

This synthesis should produce edits to `paper-landscape.md` (a Group A cluster entry), `synthesis-landscape.md` (the
headline claim as a quick- reference row), and `total-landscape.md` (the four Phase 7 skill priorities, the Phase 4
OpenGenome2/AlphaGenome benchmark mirrors, the METL Phase 6 fine-tuning exemplar, the REMME full pretraining target).
The Wave 3 Evo 2 + generative phage mini-synthesis goes onto the synthesis backlog; the open questions go into
`top-questions.md`.

---

## Inputs

The eight Group A paper notes (all in [`docs/paper-notes/`](../paper-notes/)):

- [s41586-026-10176-5](../paper-notes/s41586-026-10176-5.md) — Brixi et al., _Genome modelling and design across all
  domains of life with Evo 2_ (_Nature_ 2026).
- [s42256-025-01044-4](../paper-notes/s42256-025-01044-4.md) — He et al., _Generalized biological foundation model with
  unified nucleic acid and protein language_ (LucaOne, _Nature Machine Intelligence_ 2025).
- [s41586-025-10014-0](../paper-notes/s41586-025-10014-0.md) — Avsec et al., _Advancing regulatory variant effect
  prediction with AlphaGenome_ (_Nature_ 2026).
- [s41467-025-60872-5](../paper-notes/s41467-025-60872-5.md) — Penić et al., _RiNALMo: general-purpose RNA language
  models can generalize well on structure prediction tasks_ (_Nature Communications_ 2025).
- [2025.07.20.665723v2](../paper-notes/2025.07.20.665723v2.md) — Wiatrak et al., _A contextualised protein language
  model reveals the functional syntax of bacterial evolution_ (Bacformer, bioRxiv 2025).
- [2025.07.21.665832v2](../paper-notes/2025.07.21.665832v2.md) — Liu et al., _ProteinReasoner: A Multi-Modal Protein
  Language Model with Chain-of-Thought Reasoning for Efficient Protein Design_ (bioRxiv 2025).
- [s41592-025-02776-2](../paper-notes/s41592-025-02776-2.md) — Gelman et al., _Biophysics-based protein language models
  for protein engineering_ (METL, _Nature Methods_ 2025).
- [gkaf836](../paper-notes/gkaf836.md) — Prabakaran & Bromberg, _Deciphering enzymatic potential in metagenomic reads
  through DNA language models_ (REMME/REBEAN, _Nucleic Acids Research_ 2025).

Cross-references that were load-bearing: [memory-synthesis.md](memory-synthesis.md),
[skills-and-practices-synthesis.md](skills-and-practices-synthesis.md), [llm-wiki-synthesis.md](llm-wiki-synthesis.md),
[synthesis-landscape.md](../landscapes/synthesis-landscape.md).

---

_This synthesis is the input to the next round of edits to [paper-landscape.md](../landscapes/paper-landscape.md),
[synthesis-landscape.md](../landscapes/synthesis-landscape.md), [total-landscape.md](../landscapes/total-landscape.md),
and the Phase 6 / 7 spec backlog. It should be revisited when ProteinReasoner checkpoints appear, when the AlphaGenome
and Evo 2 7B local-deployability spikes land, when the Wave 3 Evo 2 + generative phage mini-synthesis is written, and
when any new Group A paper enters `context/papers/`._
