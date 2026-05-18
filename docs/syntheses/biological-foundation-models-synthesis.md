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
and the few-shot DNA-protein matching result (LucaOne 0.84 vs DNABert2+ESM2 0.73
([s42256-025-01044-4](../paper-notes/s42256-025-01044-4.md))) is the cleanest evidence in the corpus that joint training
learns what neither half can learn alone. A step inward sits **Evo 2**, generalist _within_ DNA: 9.3 T base pairs across
all three domains of life, zero-shot variant scoring, generative as well as discriminative, 1 M-token context.

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
splicing despite seeing no mRNA at all ([s41467-025-60872-5](../paper-notes/s41467-025-60872-5.md)). AlphaGenome beats
Evo 2 on the regulatory variant subdomain where Evo 2's own paper acknowledges trailing ChromBPNet. Bacformer beats
fine-tuned Evo on bacterial gene essentiality. **Neither pure strategy survives contact with the evidence.** A
LucaOne-only registry would underperform on regulatory variants, scarce-data protein engineering, bacterial genome
analysis, and metagenomic annotation. A pure specialist registry would be operationally heavy and would lose LucaOne's
cross-modal embedding geometry — the natural anchor for a multi-modality biological knowledge graph.

The right Phase 7 design is layered: **LucaOne (or an open small embedding model) as the cross-modal default and KG
anchor; specialists invoked when the task is in their named domain.** The router needs to know which specialists apply
to which task shapes; the specialists need to know they are not the default.

---

## Extending the constellation: cell-level FMs as a fresh modality axis

Two recent additions to the corpus pull the specialist roster off its original sequence-and-genome axis and onto a
qualitatively different one: the **cell** as a foundation-model unit of representation. Group A as originally
constituted operates exclusively at the sequence level — DNA, RNA, protein residues, ordered protein syntaxes — and the
finest biological grain any of the eight models touches is the single base or the single amino acid. Neither ProtiCelli
([2026.03.31.715748v1](../paper-notes/2026.03.31.715748v1.md)) nor TranscriptFormer
([science.aec8514](../paper-notes/science.aec8514.md)) fits cleanly anywhere on that axis, because the cell is the unit
both models speak. They extend the specialists-as-Workers framing on a fresh modality axis rather than refining existing
axes.

**ProtiCelli is the imaging arm of that extension.** A 458 M-parameter Diffusion Transformer Large trained under EDM on
**1.23 M single-cell crops from the Human Protein Atlas**, generating 512×512 single-cell immunofluorescence images for
**12,800 human proteins** across **39 cell lines** from only three landmark stains (microtubule, nucleus, ER). The
headline downstream artifact, **Proteome2Cell**, is a 30.7 M-image synthetic atlas of 2,400 "virtual cells" (200 per
line × 12 lines) integrated into HPA v26 — proteome-scale spatial proteomics by generation rather than by experiment.
Operationally ProtiCelli sits alongside Bacformer (whole-bacterial-genome representations) and Evo 2 (DNA) as a
specialist behind a typed Linus Worker; functionally it does something none of the eight Group A models can — predict
where a protein is in a cell, conditioned on cellular landmarks, given a closed-vocabulary prompt. The closed
12,800-protein vocabulary is the load-bearing operational limitation: ProtiCelli silently falls back to a default
embedding for any out-of-vocabulary protein, which makes it strong on the human proteome and structurally inapplicable
to the metagenomic novel proteins Dan's LanzaTech work routinely turns up. Vesicular compartments (peroxisomes,
endosomes, lysosomes) remain hard for all three benchmarked imaging models — a model-class limitation rooted in weak
spatial correlation with the three landmark channels, not a tunable defect. **There is no existing BFM sibling on the
imaging axis** in this synthesis; ProtiCelli's arrival opens that axis and the paper-note's "no Linus sibling yet" flag
is what makes this fold-in materially expand the corpus rather than refine an existing thread.

**TranscriptFormer is the transcriptomic arm.** A family of three generative autoregressive transformers — TF-Sapiens
(57 M human cells), TF-Exemplar (110 M cells across human + four model organisms), and the headline TF-Metazoa (**112 M
cells across 12 species spanning 1.53 Bya of evolution**) — that represent each cell as an ordered "cell sentence" of
(gene, count) pairs and initialize gene tokens from frozen ESM-2 protein embeddings. The ESM-2 initialization is what
makes the family species-agnostic: homologous genes across species sit nearby in input space without any ortholog
dictionary, which is exactly the constraint conventional cross-species single-cell analysis bumps against. Cross-species
cell-typing on previously-unseen species (mouse lemur, sea lamprey, stony coral) holds at macro F1 > 0.65 even at the
685 Mya stony-coral distance from human, where the prior SOTA single-cell foundation model UCE collapses. Phylogenetic
structure emerges in the contextualized-gene-embedding space (Spearman r = −0.705 with evolutionary distance, vs r =
−0.059 for the ESM2-CE attribution baseline) without any phylogenetic supervision. The closest sibling already present
in this synthesis is [LucaOne](../paper-notes/s42256-025-01044-4.md): both unify a previously-balkanized representation
by initializing the token space from a model trained at the next level of biological abstraction (LucaOne unifies
modalities at the sequence level, TranscriptFormer unifies species at the cell level), and both produce emergent
structure (LucaOne's central-dogma capability, TranscriptFormer's macroevolutionary phylogeny) from joint pretraining
that no single-axis baseline recovers. The architectural patterns differ — LucaOne is an encoder with token-type
embeddings disambiguating shared alphabets; TranscriptFormer is a decoder-style autoregressive model with ESM-2
gene-embedding initialization disambiguating species-specific gene IDs — but the recipe rhymes.

Both models tie directly to the two integration hooks the BFM thread has already committed to. **DEC-0046**
(`external_api_tool` registry deployment field) tags both as candidates for a hybrid posture: TranscriptFormer is
local-only (frozen weights, no network call after the checkpoint download, with `--device mps` advertised at the CLI
level — the first Group A bio FM with explicit Apple-Silicon support documented at the deployment layer rather than left
as an empirical question), while ProtiCelli is the realistic hybrid case (local for one-off predictions, remote/batch
for Proteome2Cell-scale 30.7 M-image synthesis given DiT-L's activation footprint at 50-step EDM sampling). **DEC-0048**
(`model_prediction` first-class KB edge class) is the load-bearing schema commitment for both: each ProtiCelli
prediction maps to a `model_prediction` edge with protein-id and cell-line-id endpoints, checkpoint hash and landmark
stains as provenance, predicted localization plus confidence as the edge payload, default `[!unverified]` claim-type tag
from DEC-0023; each TranscriptFormer query produces TF → target-gene PMI edges and cross-species cell-type-homology
cosine-similarity edges that fit the same schema. The concrete worked example for the DEC-0046 contract is
**ProtiCelli's `agent_tools.py`**: a JSON-Schema MCP surface (`PROTICELLI_TOOLS` exposing `validate_inputs`,
`predict_from_files`, `search_proteins`, `list_cell_lines`) with explicit Anthropic and OpenAI adapter one-liners
shipped in the README. It is unusually MCP-friendly for a biology-paper release — most bio releases stop at a CLI or a
notebook — and the Linus tool wrapping should follow the in-house fastmcp + middleware pattern from
[g6-mcp-tools](repo-clusters/g6-mcp-tools.md) per [DEC-0045](../adr/0045-fastmcp-mcp-framework-default.md), using
`agent_tools.py` as the schema reference rather than vendoring the helper directly. Proteome2Cell at 30.7 M predicted
images would also be the largest single bulk import the `model_prediction` schema has yet seen — a real stress-test in a
way the smaller-scale Evo 2 or Bacformer outputs would not provide.

The framing implication is sharper than a sibling-pair fold-in. **The cell is becoming a foundation-model unit of
representation in its own right**, alongside genome / sequence / protein, and Linus's Phase 7 biology skill class needs
a cell-level Worker family — not just sequence-level Workers. ProtiCelli and TranscriptFormer are the two ends of a
multi-modal cell-state pair: same biological subject (a single human cell), two complementary measurement modalities
(microscopy image vs RNA expression vector). A future composite Worker could call them together — predict an image with
ProtiCelli, predict transcriptomic state with TranscriptFormer, cross-reference for consistency — which is the kind of
specialist composition Phase 3's parallel-agent infrastructure exists to enable.

---

## Specialists-as-Workers at the skill-class layer: ClawBio as working precedent

The constellation argument above is framed at the **model-class layer** — LucaOne as cross-modal default, specialists
invoked when the task is in their named domain. The [ClawBio](../repo-notes/ClawBio.md) repo (ClawBio/ClawBio) is the
closest existing implementation of the same dispatch logic at the **skill-class layer**: a curated 63-skill
bioinformatics library where each skill is a deterministic, versioned specialist, and a `bio-orchestrator` skill routes
free-text queries to the right downstream skill based on file type and keywords. The dispatch surface is exactly the one
this synthesis recommends — generalist orchestrator over named specialists — except the specialists are deterministic
Python tools rather than learned FMs, and the routing signal is filename + keyword rather than model-class. ClawBio
extends the existing g9-bio cluster prior art alongside Bacformer, BioReason, bioSkills, and deepsems, and is the
depth-vs-breadth complement to bioSkills: ~438 broad-but-shallow Anthropic-format skills versus 63 deeply engineered
skills with tests, demo data, a reproducibility bundle, and a benchmark scorer where ground truth exists (e.g. the
v0.5.0 AD ground-truth gene set with 168/182 benchmark tests passing across 10 audited skills).

Two ClawBio patterns are load-bearing for the integration hooks this synthesis has already committed to. First, the
**Galaxy Bridge skill** wraps `BioBlend` to expose the full usegalaxy.org tool catalog (8,000+ external bioinformatics
tools) through a single Python skill — a working precedent for the
[DEC-0046](../adr/0046-external-api-tool-registry-deployment-field.md) `external_api_tool` deployment field. The pattern
(one Linus tool → many external tools, with the registry tagging it as external-API-deployed and the audit log capturing
every invocation) is no longer aspirational; it is shipping today behind a `/plugin install clawbio` command. Second,
ClawBio's **cross-platform chaining examples** (Galaxy VEP → ClawBio PharmGx; Galaxy Kraken2 → ClawBio metagenomics) are
a working precedent for the model-prediction-edge data flow described in
[DEC-0048](../adr/0048-kb-model-prediction-edge-class.md): a variant scored by one tool flowing as typed provenance into
the next tool's input is exactly the `model_prediction` edge shape, and the chaining contract ClawBio enforces
(per-skill `--input` / `--output` / `--demo` plus a per-skill `allowed_extra_flags` allowlist filtered before subprocess
invocation) is a candidate prior-art template for the agent-spawner's tool dispatch contract.

The framing implication for Phase 7 is that **the right Linus dispatch surface is one agent spawner that dispatches to
both kinds of Worker — deterministic skill _and_ specialist FM — through a uniform interface**. ClawBio's
`bio-orchestrator` plus per-skill subprocess pattern works for tools that are deterministic and fast; this synthesis's
recommended layered design (LucaOne anchor + specialist FMs) works for tools that are stochastic and inference-heavy.
The two are not competing — they are the two ends of the same dispatch contract, and the spawner needs to know which
dispatch path is active for a given task. Whether Linus extracts ClawBio's specific implementation, re-implements over
BioBlend directly with Linus's tool-registry conventions, or simply lifts the engineering shape (per-skill tests +
reproducibility bundle + catalog generator + conformance linter) into a Linus-native skill bundle is a Phase 7 planning
question — but the pattern itself is no longer a hypothesis. It is the closest existing precedent for what a Phase 7
inaugural bio-skills bundle should look like in working form, and the depth-vs-breadth complement to bioSkills makes the
choice between them an "or both, fork the engineering shape from one and the breadth-of-content from the other" question
rather than an "or" question.

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
17 M clusters, sample one per cluster per minibatch ([s41467-025-60872-5](../paper-notes/s41467-025-60872-5.md))) is
"data curation as architecture." A few lines of data-loader code that produced the inter-family generalisation gain.
This is a candidate Linus engineering convention to adopt the moment any Linus-trained model has a sequence corpus large
enough to benefit.

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
(fine-tune on 64 wet-lab variants, synthesise 20, get 16 functional
([s41592-025-02776-2](../paper-notes/s41592-025-02776-2.md))) and the "29 simulated points ≈ 1 experimental point"
trade-off heuristic ([s41592-025-02776-2](../paper-notes/s41592-025-02776-2.md)). The pattern generalises beyond
proteins — **simulation-pretrained, observation-fine-tuned** applies to any Linus domain with scarce real data plus a
slower-but-correct simulator (enzyme kinetics, RNA folding, docking, spectroscopy). Worth lifting to a named
architectural pattern in `docs/syntheses/` once a second clean instance lands.

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

The cross-cutting design implication: **KnowledgeBase exposes a typed `model_prediction` edge class** carrying the
producing model, version, confidence, and content hash — committed in DEC-0048. This generalises the
[LLM wiki synthesis](llm-wiki-synthesis.md)'s claim-typing pattern to model-derived claims: a predicted operon from
Bacformer is an `[!unverified]` claim (default per DEC-0048) with specific provenance, distinct from an `[!source]`
claim from a curated database. Dan may manually upgrade a prediction to `[!analysis]` or `[!source]` after review;
upgrades are audit-logged. When the model is updated, the content-hash mechanism flags the KG edges that need
revalidation. The `model_prediction` edge class must be present in the KnowledgeBase schema before any Group A Wave 1
skills start writing back (Phase 2 spec; Phase 3 implementation).

**OptimusKG** ([2604.27269v1](../paper-notes/2604.27269v1.md)) provides a mature reference for biomedical
knowledge-graph design at scale: a unified ontology across 18 sources, 190K+ nodes and 21.8M edges with explicit FAIR
principles, evidence grounding, and property-rich metadata. While OptimusKG's full integration is deferred (it covers
biomedical-only domains and requires 18+ external ontology harmonization), its medallion architecture (Landing → Bronze
→ Silver → Gold layers) and provenance-tracking schema are directly reusable patterns for Phase 3's KnowledgeBase
integration of Group A model outputs. The medallion-architecture ingest pattern is the closest external analogue to the
KB ingest quality surface per DEC-0019.

---

## Implications for Linus skills (Phase 7)

Recommended sequence: **REBEAN first, then paired RiNALMo + Bacformer, then hybrid AlphaGenome + Evo 2 variant scoring,
with LucaOne and METL added on concrete demand.**

**Skill 1: `linus.bio.metagenomics.annotate`** (REBEAN). The easiest first skill: 1.66 M parameters, well-defined
workflow (FASTQ → per-read EC → aggregate to gene), Dan's metagenomics background lets him spec and judge. Plausibly
_better_ than what hosted Claude can do, because Claude cannot run REBEAN on a 50 GB FASTQ. The right pattern-setter for
Phase 7. Effort: a focused week.

**Skill 2: `linus.bio.bacterial_genome.analyse`** (Bacformer). Natural companion to REBEAN. Operon prediction, gene
essentiality, KEGG function (188 classes), and 139-trait phenotype inference as zero-shot or fine-tuned heads. Apache
2.0 on HuggingFace; custom architecture so MLX needs custom code but the model is small. **Analytical heads only
initially**; the generative head is Tier B under the DEC-0047 biosecurity policy (explicit Dan sign-off per invocation,
audit-logged) — the authors flag the dual-use surface themselves and the three-tier policy is already in SAFETY.md.

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
release is the motivating case; Evo 2 40B is the second. _Resolved (DEC-0046, see
[answered-questions.md](../questions/answered-questions.md)): a `deployment` field (`"local" | "mcp" | "external_api"`)
is now in the registry schema; Phase 2a activates the local and MCP variants; `external_api` execution path is deferred
to Phase 7._

**Is METL's simulation-pretrained pattern worth applying to other Linus domains now, or wait for a second instance?**
Recommend waiting; this synthesis is the placeholder. The risk of premature naming is generalising from a single case.

**Is a focused "Evo 2 + Wave 3 generative phage" mini-synthesis worth writing?** A full paper note now exists for the
phage genome design paper ([2025.09.12.675911v1](../paper-notes/2025.09.12.675911v1.md)) — the first experimental
demonstration that a genome LM can design viable whole-genome phages using Evo 1/2 as backbone. The pipeline (pretrained
FM → family-scoped SFT → template prompt → inference-time constraint scoring → wet-lab validation) is the canonical
generative-biology archetype. The pairing (Evo 2 foundation model + phage design downstream application) would land at
"what does a private generative-biology workflow look like in Linus" and would force a sharp answer to the
local-vs-remote-Evo-2 question. **Recommend yes**, 1500–2000 words, tracked as R2-57 (Tier 3, top-questions.md).

**Faithfulness of model-derived KG content.** Group A is the first Wave 1 batch where the volume of model-derived KG
content is large enough to make claim-typing load-bearing. _Resolved (DEC-0048, see
[answered-questions.md](../questions/answered-questions.md)): the `model_prediction` edge class with producing-model +
version + confidence + content-hash provenance is committed to the KnowledgeBase schema; must be present before any
Group A Wave 1 skills start writing back._

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

The closest cross-synthesis neighbor is [function-annotation-discovery](function-annotation-discovery-synthesis.md):
BioReason-Pro (typed-profile CoT over a multi-model pipeline) and ProteinReasoner (typed-profile intermediate within a
single PLM) bracket the "make-a-biological-FM-reason" design space, and the encoder-swap experiment (R2-58) is the
concrete Phase 7 comparison between this synthesis's Group A foundation models and that synthesis's
reasoning-architecture poles.

This synthesis feeds `synthesis-landscape.md` (the headline claim as a quick-reference row) and `total-landscape.md`
(the four Phase 7 skill priorities, the Phase 4 OpenGenome2/AlphaGenome benchmark mirrors, the METL Phase 6 fine-tuning
exemplar, the REMME full pretraining target). The `paper-landscape.md` pointer is deprecated; per-paper navigation lives
in [`docs/paper-notes/INDEX.md`](../paper-notes/INDEX.md). The Wave 3 Evo 2 + generative phage mini-synthesis is tracked
as R2-57 in `top-questions.md`; the phage paper note ([2025.09.12.675911v1](../paper-notes/2025.09.12.675911v1.md)) is
already written and tagged to this synthesis.

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

Adjacent paper notes now tagged to this synthesis (not core Group A inputs but extending the specialist roster onto the
cell-level modality axis and the Wave 3 generative direction):

- [2026.03.31.715748v1](../paper-notes/2026.03.31.715748v1.md) — Sun et al., _Generative machine learning unlocks the
  first proteome-wide image of human cells_ (ProtiCelli, bioRxiv 2026) — DiT-L latent-diffusion model that synthesizes
  single-cell IF images for 12,800 human proteins from three landmark stains; ships an `agent_tools.py` JSON-Schema MCP
  surface and the 30.7 M-image Proteome2Cell dataset; the imaging arm of the cell-level FM extension.
- [science.aec8514](../paper-notes/science.aec8514.md) — Pearce et al., _TranscriptFormer: A generative cell atlas
  across 1.5 billion years of evolution_ (_Science_ 2026) — three generative autoregressive transformer variants
  (TF-Sapiens, TF-Exemplar, TF-Metazoa) trained on up to 112 M cells across 12 species; the transcriptomic arm of the
  cell-level FM extension; first Group A bio FM with `--device mps` advertised at the CLI level.
- [2025.09.12.675911v1](../paper-notes/2025.09.12.675911v1.md) — King et al., _Generative design of novel bacteriophages
  with genome language models_ (bioRxiv 2025) — first experimental demonstration that a genome LM can design viable
  whole-phage genomes; uses Evo 1/2 as backbone; see R2-57 in `top-questions.md`.

Cross-references that were load-bearing: [memory-synthesis.md](memory-synthesis.md),
[skills-and-practices-synthesis.md](skills-and-practices-synthesis.md), [llm-wiki-synthesis.md](llm-wiki-synthesis.md),
[generative-biology-synthesis.md](generative-biology-synthesis.md),
[synthesis-landscape.md](../landscapes/synthesis-landscape.md).

---

_This synthesis feeds [synthesis-landscape.md](../landscapes/synthesis-landscape.md) and
[total-landscape.md](../landscapes/total-landscape.md) and the Phase 6/7 spec backlog. The `paper-landscape.md` pointer
is deprecated; paper-level navigation lives in [`docs/paper-notes/INDEX.md`](../paper-notes/INDEX.md). Revisit when:
ProteinReasoner checkpoints appear on BioMap GitHub / `airkingbd` HF (passive watch per S52); the AlphaGenome and Evo 2
7B local-deployability spikes land; the ProtiCelli and TranscriptFormer M1-Max MPS spikes land; the Wave 3 Evo 2 +
generative phage mini-synthesis (R2-57) is written; any new Group A paper enters `context/papers/`. Updated 2026-05-10
(ClawBio specialist-skill-as-Worker fold-in)._

---

## References

### Repo-notes

- [`Bacformer`](../repo-notes/Bacformer.md) — protein-embedding-as-token bacterial genome FM; Apache 2.0,
  Apple-Silicon-realistic.
- [`BioReason`](../repo-notes/BioReason.md) — DNA-encoder + LLM fusion with GRPO reasoning traces over KEGG pathways.
- [`bioSkills`](../repo-notes/bioSkills.md) — 438-skill bioinformatics SKILL.md catalogue for Claude Code.
- [`ClawBio`](../repo-notes/ClawBio.md) — 63 deeply engineered clinical/consumer genomics skills with reproducibility
  bundles.
- [`deepsems`](../repo-notes/deepsems.md) — BGC→SMILES transformer for cryptic biosynthetic-gene-cluster metabolite
  prediction.
- [`fastmcp`](../repo-notes/fastmcp.md) — decorator-based MCP server framework; Linus's default MCP substrate
  (DEC-0045).
- [`OptimusKG`](../repo-notes/OptimusKG.md) — biomedical knowledge graph with medallion-architecture FAIR ingest
  pipeline.
- [`ProtiCelli`](../repo-notes/ProtiCelli.md) — DiT-L diffusion FM synthesizing proteome-wide single-cell
  immunofluorescence images.
- [`transcriptformer`](../repo-notes/transcriptformer.md) — generative cell-atlas autoregressive transformer family with
  `--device mps` support.

### Paper-notes

- [`2025.07.20.665723v2`](../paper-notes/2025.07.20.665723v2.md) — Bacformer contextualised protein language model over
  bacterial genomes.
- [`2025.07.21.665832v2`](../paper-notes/2025.07.21.665832v2.md) — ProteinReasoner multi-modal PLM with MSA-profile
  chain-of-thought.
- [`2025.09.12.675911v1`](../paper-notes/2025.09.12.675911v1.md) — Generative design of viable bacteriophages with
  Evo-family genome LMs.
- [`2026.03.31.715748v1`](../paper-notes/2026.03.31.715748v1.md) — ProtiCelli proteome-wide generative imaging
  foundation model.
- [`2604.27269v1`](../paper-notes/2604.27269v1.md) — OptimusKG unified biomedical knowledge graph with provenance and
  FAIR principles.
- [`gkaf836`](../paper-notes/gkaf836.md) — REMME/REBEAN tiny DNA-LM for reference-free metagenomic enzyme annotation.
- [`s41467-025-60872-5`](../paper-notes/s41467-025-60872-5.md) — RiNALMo 650M RNA language model with cross-family
  generalisation.
- [`s41586-025-10014-0`](../paper-notes/s41586-025-10014-0.md) — AlphaGenome single-bp regulatory variant effect
  prediction across 5,930 tracks.
- [`s41586-026-10176-5`](../paper-notes/s41586-026-10176-5.md) — Evo 2 StripedHyena DNA FM with 1M-token context across
  all domains of life.
- [`s41592-025-02776-2`](../paper-notes/s41592-025-02776-2.md) — METL biophysics-based protein LM pretrained on Rosetta
  simulations.
- [`s42256-025-01044-4`](../paper-notes/s42256-025-01044-4.md) — LucaOne unified DNA+RNA+protein encoder with
  central-dogma emergence.
- [`science.aec8514`](../paper-notes/science.aec8514.md) — TranscriptFormer generative cell atlas across 1.5 billion
  years of evolution.
