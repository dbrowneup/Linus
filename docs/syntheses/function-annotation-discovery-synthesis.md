# Function Annotation, Reasoning & Discovery Synthesis

> **Cross-cutting note (added 2026-05-05).** As of the 2026-05-05 landscape remapping, **LAB-Bench and BixBench are
> primarily anchored from [`infra-foundations-synthesis.md`](infra-foundations-synthesis.md)** as Phase 1 Worker-
> selection benchmarks. The deeper methodological treatment (coverage/accuracy/precision triple, MCQ→open-answer
> collapse, FutureHouse evaluation philosophy) remains in this document because it is load-bearing for the
> function-annotation skill argument; cross-reference both files when planning benchmark adoption. The Tier-1-equivalent
> action ("LAB-Bench MCQ + BixBench as Phase 1 baseline") now lives on the infra-foundations row of the synthesis
> matrix.

## What this document is

A synthesis of eight Group C papers — three method papers (Horizyn-1, ProtHGT, DIAMOND DeepClust), two
reasoning-augmented FM systems (BioReason, BioReason-Pro), one cell-state FM (PertFormer), and two FutureHouse benchmark
suites (LAB-Bench, BixBench) — read through one question: _what does Linus actually do for Dan in the function-
annotation, reasoning, and biological-discovery layer, in what order, and how does it know it is getting better?_ The
eight paper-notes live in [`docs/paper-notes/`](../paper-notes/) and are listed under [Inputs](#inputs). Audience and
tone match the [memory](memory-synthesis.md), [biological foundation models](biological-foundation-models-synthesis.md),
and [agentic systems](agentic-systems-synthesis.md) syntheses.

The headline claim is that **Group C is the first Wave 1 batch where Linus has access to both the methods and the rulers
at the same time.** Six of the papers are concrete tools or substrate (Horizyn-1, ProtHGT, DIAMOND DeepClust, BioReason,
BioReason-Pro, PertFormer). The other two — LAB-Bench and BixBench — are FutureHouse benchmarks that reframe the rest,
because they let Linus ask "how good is this Worker, on the kind of work Dan actually does, against the frontier?"
before committing engineering effort. The Phase 1 question is therefore benchmarking, not selection, and the Phase 7
skill question is benchmark-informed rather than spec-driven.

---

## The papers at a glance

[**Horizyn-1**](../paper-notes/rocks-et-al-2026-dual-encoder-contrastive-learning-accelerates-enzyme-discovery.md)
(Dayhoff Labs, _PNAS_ 2026) — CLIP-style **dual-encoder contrastive model** mapping ECFP6+DRFP reaction fingerprints
into the same space as ProtT5 protein embeddings; recovers a known catalyst within the top 100 for **76.7%** of held-out
reactions; experimentally validated through deorphaning, promiscuity prediction, and noncanonical-amino-acid discovery;
fine-tuning on **10 reactions** lifted ene-reductase median top-100 from 38% to 71%.
[**DIAMOND DeepClust**](../paper-notes/s41592-026-03030-z.md) (Buchfink et al., _Nat Methods_ 2026) — cascaded
ultra-fast protein clusterer that clustered **19 billion** deduplicated sequences in 18 days on 27 nodes, producing
**335M cluster representatives** (5.5× the diversity of AlphaFold2's BFD); substituting DeepClust for BFD raised mean
AF2 pLDDT on 473 difficult low-MSA targets from 52.9 to 62.6. [**ProtHGT**](../paper-notes/2025.04.19.649272v1.md)
(Ulusoy & Doğan, bioRxiv 2025) — **Heterogeneous Graph Transformer** over the CROssBAR KG (542k nodes / 3.79M edges
across 9 entity types, 17 relations); type-specific node embeddings bootstrapped from modality-appropriate pretrained
encoders (ProtT5, anc2vec, dom2vec, RXNFP, doc2vec, TransE, node2vec, SELFormer); SOTA on the DeepHGAT time-based GO
benchmark and ships **KG-path explanations** for every prediction. [**BioReason**](../paper-notes/2505.23579v2.md)
(Fallahpour et al., NeurIPS 2025) — first deep architectural fusion of a DNA foundation model (Evo2-1B / Nucleotide
Transformer 500M) with an LLM (Qwen3-1.7B/ 4B), trained with **SFT then Dr. GRPO** to produce explicit `<think>` traces
over genomic sequences; KEGG disease-pathway accuracy climbs **86–90% (single-modality) → 98.28%** with
Evo2+Qwen3-4B+GRPO; ten-step mechanistic reasoning chains a domain expert can audit.
[**BioReason-Pro**](../paper-notes/2026.03.19.712954v1.md) (Fallahpour et al., bioRxiv 2026) — protein-domain successor
to BioReason; ESM3 embeddings + a typed-prediction companion (**GO-GPT**, an autoregressive transformer over GO terms) +
a Qwen3-4B reasoning LLM trained with SFT+GSPO; **27 human protein experts prefer-or-tie the SFT model's annotations
against UniProt for 79% of 162 proteins**; per-residue attention validated against cryo-EM contact residues.
[**PertFormer**](../paper-notes/2024.12.19.629561v2.md) (Yang et al., bioRxiv 2025) — 3B-parameter multimodal cell-state
foundation model trained on paired bulk epigenetics + scMultiome (1.5B paired samples across 1M cells); operates at the
_gene_ unit (300 kb regulatory window per training sample); enables **zero-shot in-silico perturbation** by editing
chromatin tracks; THAP2 (TNBC) and ZIK1 (OV) computational predictions confirmed by siRNA wet-lab validation.
[**LAB-Bench**](../paper-notes/2407.10362v3.md) (Laurent et al., FutureHouse, 2024) — 2,457-question MCQ benchmark
across eight practical-biology categories (literature recall, supplemental lookup, figure / table interpretation,
database navigation, protocol troubleshooting, sequence reasoning, cloning scenarios) with explicit "insufficient
information" option enabling separate **coverage / accuracy / precision** metrics; humans win nearly across the board;
the **MCQ→open-answer collapse** on Cloning Scenarios (~0.20 open-answer accuracy) is the methodological warning.
[**BixBench**](../paper-notes/2503.00096v3.md) (Mitchener et al., FutureHouse, 2025) — 61-capsule / 205-question agent
benchmark for **bioinformatics analysis** built on FutureHouse's Aviary gymnasium with a deliberately spartan three-tool
Jupyter scaffold (`edit_cell`, `list_workdir`, `submit_answer`); Claude 3.5 Sonnet hits **~21% open-answer accuracy**
and barely beats random in MCQ-with-refusal mode; notebook access provides **no net gain over a pure-recall baseline**
in the MCQ regime.

---

## The constellation: methods, reasoning, infrastructure, benchmarks

The eight papers organise into four archetypes mapping onto distinct Linus needs.

The **method/discovery archetype** holds three papers attacking the same broad target — given evidence about a protein
or a reaction, return a structured prediction — through three irreducibly different bets.
[Horizyn-1](../paper-notes/rocks-et-al-2026-dual-encoder-contrastive-learning-accelerates-enzyme-discovery.md) treats it
as **cross-modal retrieval**: project both sides of the reaction-enzyme pair into a shared CLIP-style space and rank by
cosine similarity, with ECFP6+DRFP on the chemistry side and frozen ProtT5 on the protein side.
[ProtHGT](../paper-notes/2025.04.19.649272v1.md) treats it as **link prediction over a typed knowledge graph**:
bootstrap each node type with a modality-appropriate encoder, run a Heterogeneous Graph Transformer with per-edge-type
attention, score (protein, GO-term) pairs through an MLP, and surface a 4–5 step KG-path explanation.
[DIAMOND DeepClust](../paper-notes/s41592-026-03030-z.md) is the infrastructural underpinning: not a model, but the
cluster substrate that makes 335M canonical protein entities a real thing sitting on disk, ready to be the node anchors
for ProtHGT-style graphs or the screening universe for Horizyn-1-style retrieval. The three methods disagree about
substrate — chemistry-aware vector vs typed graph vs homology-clustered set — and that disagreement is where Linus's
first Phase 7 decision sits.

The **reasoning archetype** holds two papers from the same Toronto/Arc group:
[BioReason](../paper-notes/2505.23579v2.md) and [BioReason-Pro](../paper-notes/2026.03.19.712954v1.md). Both apply one
recipe — frozen domain encoder + linear projection + LoRA-tuned LLM + SFT-then-RL — to add **explicit chain-of-thought**
to a biological FM. BioReason proves the recipe on DNA reasoning over KEGG pathways (86→98%); BioReason-Pro generalises
to protein function prediction with ESM3 and adds the **GO-GPT typed-prediction companion** as an evidence channel
before the free-text reasoning stage. Together they argue that reasoning over a biological FM is a tractable engineering
pattern, not a research project, and that the right primitive is **typed predictions feeding free-text reasoning**, not
either alone.

The **cross-modality archetype** is held by [PertFormer](../paper-notes/2024.12.19.629561v2.md) alone. Where the other
six papers operate at the molecule level, PertFormer operates at the **cell-state** level — each training sample is one
gene's 300 kb regulatory window in one cell — using two-stage attention (Elementary for local multiomic encoding,
Regulatory for long-range integration) to enable zero-shot in-silico perturbation. The only Group C paper whose entity
is a cell and whose output is an expression program. The modality outlier that would justify breaking out a "cell-level
FMs" group label if more accumulate.

The **benchmark archetype** is the new addition that reframes everything else.
[LAB-Bench](../paper-notes/2407.10362v3.md) measures **base-model practical-biology capability** without tools — eight
categories spanning what a biology research assistant actually does, with a coverage/accuracy/precision triple that
respects refusals. [BixBench](../paper-notes/2503.00096v3.md) measures **agentic bioinformatics analysis** with tools —
three-tool Jupyter scaffold, 61 capsules built by PhD bioinformaticians, open-answer grading by judge LLM. They are the
two halves of the same question: how good is the base model, and how good is the base model wearing the orchestration
layer? Both are public on Hugging Face, both ship eval harnesses, both have established frontier upper bounds against
which a local M1-Max-resident Worker can be measured.

---

## Cross-cutting threads

### Frontier models still fail at scientific work — and Linus's Workers are smaller still

The hardest finding to absorb is the BixBench number: Claude 3.5 Sonnet, with bioinformatics analysis tools, on
questions designed to be answerable from the analysis it performs, hits **21% open-answer accuracy**. In
MCQ-with-refusal mode both Claude 3.5 Sonnet and GPT-4o score near random because they refuse rather than commit. With
refusal removed, MCQ rises but **does not exceed the no-notebook recall baseline** — the analyses add no net signal.
Majority voting across five rollouts does not help. LAB-Bench tells the consistent story: humans win across nearly every
category, and the Cloning Scenario MCQ→open-answer collapse drops Claude 3.5 Sonnet and GPT-4o to **0.20 accuracy**,
with the two correct answers both traceable to guessing the most common enzyme (BsaI) and antibiotic (Carbenicillin).
The models are eliminating distractors and recalling priors, not reasoning about cloning workflows.

The implication for Linus is sober. Local Workers — Qwen2.5-Coder-7B, Llama-3-8B, eventually a fine-tuned Linus-7B — are
smaller and weaker than the models that produced these numbers. The realistic Phase 1 / 2 expectation is that a local
Worker scores meaningfully below 21% on BixBench and below frontier on every LAB-Bench category. That is fine, because
Linus's premise is not "beat Claude on its own ground" but "do useful private work that Claude cannot do at all." But it
does mean: (a) **Linus skills should be narrow tools wired into Workers, not generalist Workers prompted to reason in
free text**; (b) **the orchestration layer's value proposition is fan-out, audit trail, local data, and specialist
tool-routing**, not raw Worker IQ; (c) **Maestro/Worker discipline is non-negotiable** — Dan and hosted Claude do the
hard reasoning, Workers run the scoped tools.

These numbers also warn against premature reasoning-model optimism. BixBench's authors excluded o1 and DeepSeek R1
because they "struggled with the long contexts and structured tool-use outputs the agentic loop required." If the
long-trajectory + structured-tool-use combination defeats current reasoning models, swapping the Worker for QwQ will not
fix Linus's bioinformatics agent. The fix is in the harness, the tool design, and the trajectory shape, not the model
alone.

### Three paradigms for "explain why this answer"

Group C contains three architecturally distinct ways to make a biological prediction interpretable. BioReason and
BioReason-Pro make it a **free-text generation** problem: the model writes `<think>` blocks before committing, with SFT
on GPT-5-generated traces shaping the form and RL on a composite correctness + conciseness + format reward refining it.
The PFN1→profilin→actin→axonal-transport→ALS chain in BioReason and the eEFSec→SBP2 walkthrough in BioReason-Pro are the
model showing its work the way a domain expert would. Strength: human-auditability. Weakness: the chain is only as
grounded as the SFT teacher and reward make it — BioReason-Pro's strain-sensitive predictions on synthetic Acr proteins
show what happens when the reasoning is pulled toward organism priors over weak intrinsic evidence.

ProtHGT makes interpretability a **graph-path traversal** problem: every prediction is accompanied by a 4-step or 5-step
KG path through typed nodes (protein → pathway → shared-domain → disease-protein → GO term) annotated with edge
probabilities. Strength: mechanical traceability — the path is a data structure, not prose. Weakness: the schema is
fixed at construction time, so novel relations or entities outside CROssBAR are invisible to the explanation.

Horizyn-1 makes interpretability a **retrieval** problem: the answer _is_ a ranked list with cosine scores, calibrated
against training positives/negatives into low / moderate / high tiers. Strength: the cleanest possible audit. Weakness:
no mechanism — "this enzyme; 100 candidates; this confidence," not "this enzyme because the α-amine attacks the keto
carbonyl."

The Linus lesson is that interpretability is a design parameter, not a binary, and the right shape depends on the
consumer. KG paths suit a system that audits and re-queries; free-text chains suit a human reader writing a methods
section; ranked lists suit a wet-lab planner choosing five candidates to clone. Group C says all three patterns work and
ship with public weights. The recommended Linus default is **typed structured prediction wrapping free-text rationale,
both surfaces queryable in the audit log** — exactly the GO-GPT + Qwen3 shape BioReason-Pro pioneered.

### KG-grounded vs FM-only function prediction

The three protein-function-adjacent papers stake very different bets on _structured biological knowledge_. ProtHGT's
predictive power lives in the KG itself — ablations drop MF MCC from 0.697 to 0.509 when EC-number nodes are removed;
the graph **is** the model in a strong sense and the HGT is just the relational refiner. BioReason-Pro's power lives in
multiple complementary channels (ESM3, GO-GPT, GO-graph encoder, InterPro, STRING, organism prior) integrated by a
reasoning LLM; structured biology is one input among several. Horizyn-1's power lives almost entirely in **PLM and
chemistry embeddings**, with no symbolic biology in the loop — the ablation lesson was "input representations matter far
more than encoder architecture."

Linus's Phase 3 KnowledgeBase needs to handle all three modes: predictions flowing into the KG (BioReason-Pro atlas
style), the KG flowing into predictions (ProtHGT style), and decoupled embedding retrieval (Horizyn-1 style). The
**`model_prediction` edge class** the biological-FM synthesis recommended — producing-model, version, confidence,
content-hash — becomes the single mechanism that makes all three coexist. ProtHGT predictions written in with KG-path
provenance; BioReason-Pro predictions with CoT trace + GO-GPT confidence; Horizyn-1 retrievals with cosine-tier +
embedding version. The content hash is what marks stale edges when the upstream model is redeployed.

### Benchmark methodology: coverage/accuracy/precision and the open-answer test

LAB-Bench and BixBench make sharp methodological arguments that should propagate into how Linus benchmarks itself.
LAB-Bench's contribution is the **coverage / accuracy / precision triple** enabled by an explicit "insufficient
information" option. Tool-dependent categories appropriately score zero accuracy for tool-less models that decline, but
their precision can still be high — telling you the model knows when it doesn't know. Lumping refusals with wrong
answers obscures the calibration property local Workers need if SAFETY.md is to mean anything.

BixBench's contribution is the **MCQ→open-answer collapse**: the same questions scored as MCQ give wildly higher numbers
than scored on the open-ended answer the agent produced. The Cloning Scenario collapse to 0.20 open-answer is direct
empirical evidence that **MCQ benchmarks systematically overestimate reasoning capability**. The finding is structurally
identical to the [tokens-per-second paper](../paper-notes/2502.16721v1.md)'s argument about tok/s and to the
[Practical Guide for Evaluating LLMs](../paper-notes/2506.13023v1.md)'s perplexity-is-a-trap thread. Three independent
papers converging on **measure the operational thing, not the surrogate** is strong signal for Linus benchmarking
philosophy.

The right Linus convention: every `benchmarks/dan_tasks/` task ships with **(a) an open-answer scoring path as the
headline**, (b) an optional MCQ path for frontier comparison with the gap reported as a calibration metric, (c) explicit
coverage/accuracy/precision separation when refusals are meaningful. LAB-Bench's **80% public / 20% private split with
canary string** is the right contamination-mitigation pattern; adopt it day one. These small conventions belong in a
benchmarking ADR.

### The FutureHouse lineage as one continuous research program

LAB-Bench, BixBench, and Kosmos are one project read three ways. LAB-Bench (2024) defined what practical biology
capability looks like as a measurable thing. BixBench (2025) lifted the measurement into open-answer agent evaluation
with a real Jupyter sandbox. [Kosmos (2511.02824v2)](../paper-notes/2511.02824v2.md), in the
[agentic-systems synthesis](agentic-systems-synthesis.md), is what FutureHouse built once they had a way to measure
progress: a 12-hour autonomous research agent with structured world model and ~200 parallel rollouts. The arc is
**measurement → harness → system**, with Aviary as the connective tissue.

For Linus this lineage is a roadmap. Phase 1 should run LAB-Bench. Phase 2 / 3 should adopt or vendor Aviary and add
Linus capsules to BixBench. Phase 7 / 8 should examine Kosmos as architectural inspiration for the Maestro fan-out +
structured shared state pattern once underlying Workers are good enough. This is one of the few external research
programs whose direction overlaps Linus's strongly enough that **active tracking** is warranted — the next FutureHouse
paper is more likely to be directly load-bearing than the next paper from any other single group.

### Modality coverage and the gaps to track

Group C spans protein, DNA, cell-state, and computational-biology workflow. Two modality gaps are visible.
**RNA-specific reasoning** is absent — RiNALMo from [Group A](biological-foundation-models-synthesis.md) covers RNA
representation, but no Group C paper adds reasoning or function annotation over RNA. A BioReason-style shell over
RiNALMo for ncRNA function, or a Pathway-GPT typed-prediction companion over RNA-binding-protein networks, would be the
symmetric extensions. **Tissue-level FMs** are also missing — PertFormer is cell-level, nothing operates at organoid /
tumour-microenvironment / spatial- architecture scale. Spatial transcriptomics FMs are the obvious next entry. Both are
gaps to _watch for_, not fill speculatively; flagging them on the synthesis backlog improves the chance the next reading
list closes them deliberately.

### Substrate dependencies on Group A

Several Group C papers consume Group A FMs as substrate, which means a Group A release propagates directly into a Group
C skill upgrade. BioReason consumes Evo 2 and Nucleotide Transformer as `f_DNA`; the frozen-encoder design makes a
future BioReason variant on AlphaGenome's 1 Mb context (addressing the 2 kb truncation) a Linus-original direction the
paper does not pursue. BioReason-Pro consumes ESM3; substituting LucaOne or ProteinReasoner is testable. ProtHGT
explicitly ablates ProtT5 vs TAPE vs ESM-2 and is agnostic to which PLM provides node features. Horizyn-1 uses ProtT5
frozen and the ablations showed that end-to-end ESM-2 fine-tuning did _not_ help, but swapping in a stronger frozen
backbone is exactly the upgrade path predicted by "backbones matter more than encoder architecture."

**A Group A model upgrade is a Group C skill upgrade**, and because all three patterns hold the encoder frozen,
substitution cost is re-running embedding precomputation, not retraining. Linus's tool registry should carry the encoder
choice as a versioned parameter so swaps can be recorded, A/B-tested, and reverted. This is the Phase 6/7 manifestation
of the KnowledgeBase content-hash discipline — model versioning as provenance for predictions, parallel to claim-typing
as provenance for KG content.

---

## Implications for Linus skills (Phase 7)

The benchmarks force a different sequencing than the biological-FM synthesis arrived at. There the recommendation was
methods-first (REBEAN → RiNALMo + Bacformer → AlphaGenome + Evo 2 hybrid) keyed on operational viability. Here the right
Phase 7 sequence starts **before any new skill is built**: with benchmarking the existing Worker substrate against
LAB-Bench and BixBench so the next decisions are made against numbers, not intuition.

**Phase 7 prerequisite (Phase 1 work): LAB-Bench + BixBench baseline.** Pull both Hugging Face datasets, run hosted
Claude plus the current Ollama Workers through a representative subset (LAB-Bench's SeqQA + ProtocolQA + LitQA2; 5–10
BixBench capsules through the Aviary three-tool scaffold). Headline numbers into `benchmarks/dan_tasks/`. **The
empirical floor every subsequent skill candidate is measured against.**

**Skill 1: `linus.bio.enzyme_match` (Horizyn-1)** — high-value first skill, squarely Dan's domain, simple wrapper.
Reaction SMILES in, ranked enzyme list with confidence tiers out. The 14 GB embedding store fits comfortably on M1 Max.
The fine-tuning lever (10 reactions → median 71% top-100) makes Horizyn-1 a Phase 6 exemplar as well. Pairs naturally
with REBEAN from [Group A](biological-foundation-models-synthesis.md) into a complete biocatalysis pipeline (REBEAN
finds candidates from metagenomic reads, Horizyn-1 matches to target reactions, METL engineers the chosen enzyme).

**Skill 2: `linus.bio.protein_function_predict` — pick between ProtHGT and BioReason-Pro on benchmark.** The sharpest
selection question in Group C. ProtHGT is faster, KG-native, returns ranked GO terms with mechanical 4-step paths,
integrates with a planned protein-substrate KG layer, but is fixed at the CROssBAR schema and inference cost on M1 Max
is unmeasured. BioReason-Pro is slower (three sequential models), narrative-native, scores 8.03/10 from LLM judge and
79% expert tie-or-exceed UniProt, but the recipe is heavy and predictions are organism-prior-sensitive on novel
sequences. The benchmark-informed decision uses LAB-Bench SeqQA plus a Dan-authored protein-function eval before
commitment. Either way, the **240K-protein BioReason-Pro pre-computed atlas is a free Phase 3 KB ingestion target**
regardless of the eventual on-demand skill choice.

**Skill 3: `linus.bio.dna_pathway_reason` (BioReason).** Natural sibling once BioReason-Pro is operationally validated;
both share the SFT+GRPO recipe. The KEGG benchmark is reusable; the 2 kb DNA truncation is the operational limit to
surface up front.

**Substrate, not skill: DIAMOND DeepClust.** The cleanest action is Phase 4 mirror plus Phase 3 KG ingestion. The 335M
cluster representatives become the canonical protein-entity layer; the member-to-representative TSV gives the homology
relation as a derived edge; Pfam clans provide a categorical type system. Lab-scale DIAMOND v.2 +
DeepClust-on-a-Dan-corpus is plausibly a Phase 7 `linus.bio.cluster_proteins` skill on its own; biosphere-scale is not.

**Niche but defensible: `linus.bio.cell_perturbation_predict` (PertFormer).** Depends on whether near-term work touches
single-cell or perturbation screens. High-effort integration (CUDA port + validate

- register), low-payoff if idle. **Defer pending an explicit Dan use case** — the THAP2/ZIK1-style KB content angle can
  be exercised without the full local skill. If a project does touch this, PertFormer is the clearest cell-level FM in
  the corpus.

Tool-registry lesson: **separate skills per task shape, with substrate (DeepClust, Group A FMs) shared across them**.
Don't build a mega-skill; do share encoder and KG substrate.

---

## Implications for Linus benchmarking

Group C is the first Wave 1 batch where Linus has a **ready-made benchmark suite** for the biology-Worker layer. Adopt
before building.

**LAB-Bench's public 80% in `benchmarks/dan_tasks/biology/lab-bench/`** as a git submodule or reproducible download. Run
hosted Claude + each local Worker through SeqQA, ProtocolQA, LitQA2 in three runs, report mean ± std across the
**coverage/accuracy/precision triple**. The `[ANSWER]X[/ANSWER]` parsing convention is paper-documented. Adopt the 80/20
split + canary-string contamination pattern for Linus's private benchmarks too — bake into the benchmarking ADR now.

**BixBench's open-answer harness in `benchmarks/dan_tasks/biology/bixbench/`.** The Aviary three-tool scaffold is the
cleanest agentic-eval surface in the literature for Dan's work. Two Phase 1 spikes needed: (a) configure the scaffold to
talk to a local Ollama/mlx-served model rather than OpenAI/Anthropic; (b) substitute a local judge LLM for Claude 3.5
Sonnet and quantify evaluation noise. Half-day to a day each. The Docker-on-macOS issue is fine because Docker hosts the
_analysis sandbox_, not inference.

**Open-answer-vs-MCQ contrast as methodology principle.** Every benchmark reports an open-answer headline;
MCQ-with-refusal is secondary for frontier comparison; the gap itself is a tracked calibration metric. The most
important methodology lesson in Group C, already supported by three independent papers
([2502.16721v1](../paper-notes/2502.16721v1.md), [2506.13023v1](../paper-notes/2506.13023v1.md), BixBench).

**Capsule authoring as a recurring `dan_tasks/` pattern.** BixBench capsules (hypothesis + data + reference notebook +
result + truth-flag) are what a PhD bioinformatician produces as a byproduct of analysis. 3–5 capsules from Dan's past
genomics work serve double duty — private benchmark items frontier models cannot have memorised, plus fine- tuning data
for a Phase 6 LoRA on Qwen2.5-Coder. An afternoon per capsule.

**Frame numbers as gap-to-frontier and gap-to-human**, not absolute accuracy. A Llama-3-8B Worker scoring 8% on BixBench
is not a failure if Claude scores 21% — the question is whether tool routing, KB grounding, and Maestro/Worker fan-out
close some fraction of that gap. Phase 1 benchmarking is the ongoing measurement, not a one-shot.

---

## Implications for Linus KnowledgeBase

Three Group C papers offer distinguishable templates for the protein- substrate of the KnowledgeBase, and a fourth
offers content.

**ProtHGT's CROssBAR schema is the template for KG topology** — nine entity types, seventeen typed relations,
modality-bootstrapped node embeddings. A working production schema with SOTA function-prediction performance, not an
ad-hoc KG. Adopting CROssBAR fragments (or PrimeKG) gives interop with ProtHGT and likely with future KG-native
bioinformatics tools. The cost is committing to a specific ontology early; the cost of _not_ committing is retrofitting
once skill outputs arrive with type-mismatched provenance.

**DIAMOND DeepClust's 335M cluster representatives are the node anchors for the protein layer.** Each representative is
a canonical entity; each member is an instance linked by a "member-of" edge; the cluster graph compresses 19B-sequence
homology into a traversable structure. The granularity question — 335M (size ≥3) vs ~61M (AF2-significant size ≥30) vs
Pfam-annotated-only — is open and worth a small Phase 1 experiment before KB v1 commits.

**Horizyn-1's contrastive embeddings model the cross-modal vector layer.** Reactions and enzymes become nodes with
modality-aware vectors; cosine score is the edge weight. The same Qdrant index that powers literature retrieval powers
reaction-enzyme retrieval without architectural change. The paper's finding that shared-embedding distance correlates
with shortest-path distance (SI Fig. S17) suggests **vector geometry can substitute for graph-walk computation** on
certain bipartite subgraphs — a useful efficiency lever as the KG grows.

**BioReason-Pro's pre-computed 240K-protein atlas is content, not schema.** Includes structured CoT alongside GO terms —
the _why_ not just the _what_. Materially higher-quality than UniProt's bare term lists. High ingest priority.

The cross-cutting implication matches the [biological-FM synthesis](biological-foundation-models-synthesis.md): the KG
needs an explicit `model_prediction` edge class with producing-model + version

- confidence + content-hash, distinguishing model-derived claims from curated. Group C makes this load-bearing rather
  than aspirational — BioReason-Pro's atlas alone would otherwise pollute the KG with hundreds of thousands of
  unattributed predictions within months. The [LLM wiki synthesis](llm-wiki-synthesis.md)'s `[!analysis]` vs `[!source]`
  distinction is the natural prior-art.

---

## Tensions and open questions

**ProtHGT vs Horizyn-1 vs BioReason-Pro for the first protein-function skill — on what criteria?** Three architectures,
three output shapes, three operational profiles. Pick on benchmark against a Dan-authored protein-function eval, but the
deeper question is which axis matters: latency, narrative quality, GO-Fmax, low-similarity robustness, ease of local
deployment, agreement with experimental controls. BioReason-Pro's own four-tier evaluation (automated Fmax, LLM-judge,
human pairwise, structural grounding) is a credible picking template; a scaled-down version belongs in
`benchmarks/dan_tasks/biology/`.

**Should LAB-Bench MCQ + BixBench agent harness be the Phase 1 baseline for Worker selection?** Case for yes: most
rigorous public benchmarks in Dan's domain, established frontier upper bounds, days of work instead of weeks. Case for
caution: a benchmark is an opinion about what matters, and adopting LAB-Bench's MCQ-with-refusal smuggles in the
FutureHouse opinion. Recommended: **adopt now, supplement with Dan- authored capsules over Phase 1–3, reserve the right
to weight categories differently than the source papers**. Benchmarking ADR resolves the convention.

**Is the FutureHouse evaluation philosophy worth adopting wholesale?** The insufficient-info option, the
open-answer-vs-MCQ contrast, the 80/20 public/private split, the LLM-judge for open-answer grading, the pure-recall
calibration baseline — these are coherent choices that hang together. Yes, with one caveat: the LLM-judge dependency on
hosted Claude is not aligned with Linus's local-first posture, and Phase 4 should target a local judge or accept a
hybrid where hosted Claude is benchmarking-only. Deserves an explicit ADR.

**Should the BioReason-Pro encoder be swapped to LucaOne or ProteinReasoner?** Frozen-encoder design makes the swap
mechanically cheap. Hypothesis: a cross-modal pretrained encoder (LucaOne) or an explicitly reasoning encoder
(ProteinReasoner) gives different — possibly better — cellular-component or organism-specific behaviour than ESM3. Phase
6 / 7 spike worth naming: rerun the BioReason-Pro harness with each substituted, report deltas. Pending ProteinReasoner
checkpoint release.

**"PLM + heterogeneous KG + graph transformer" as a named Linus archetype?** At least three corpus papers (ProtHGT,
DeepHGAT, PSPGO) are variants. Recommendation: **name after a second independent replication outside this corpus**, with
ProtHGT as the lead worked example.

**"Dual-encoder cross-modal retrieval" as a named Linus archetype?** The pattern is well-established externally (CLIP,
CLAP, VideoCLIP, CodeBERT, ProtST), and Horizyn-1 is the first scientific-discovery instantiation in the corpus. **Name
it now** with Horizyn-1 as lead worked example — external priors are strong enough that the pattern is not speculative.

**Should Linus pick a default mode for function prediction?** Linus needs all three (ProtHGT KG-grounded, BioReason-Pro
FM-with-typed- companion, Horizyn-1 pure FM), but the default for new skills should be what the orchestration layer
audits most cleanly. Recommended default: **typed structured prediction wrapping free-text rationale** (the
BioReason-Pro shape) — both human-readable and machine-queryable, and generalises beyond biology.

---

## Where this synthesis fits

Group C sits between [Group A (biological foundation models)](biological-foundation-models-synthesis.md) as the
**substrate provider** and [Group D (agentic systems)](agentic-systems-synthesis.md) as the **orchestration consumer**.
Group A FMs are the encoders inside Group C systems (BioReason consumes Evo 2, BioReason-Pro consumes ESM3, Horizyn-1
consumes ProtT5, ProtHGT ablates ProtT5/TAPE/ESM-2). Group D architectures wrap Group C skills into workflows — Linus's
Phase 7 / 8 design is implicitly committing to running Group C skills inside Group D-style agent loops with KG-grounded
memory.

Group B (generation side) is sequential complement: Group C predicts what exists or could exist functionally, Group B
generates new candidates. The KnowledgeBase synthesis connection (via [llm-wiki-synthesis](llm-wiki-synthesis.md)) is
that Group C is the first batch where model-derived KG content is large enough — BioReason-Pro's 240K-protein atlas
alone — to make claim-typing operationally load-bearing. The [memory synthesis](memory-synthesis.md) connection is that
BioReason and BioReason-Pro are domain confirmations of the CoT-escapes-TC0 thesis — the 86→98% KEGG jump and the 79%
UniProt expert tie-or-exceed are biology-domain instantiations of the theoretical capability gap.

This synthesis should produce: a Group C cluster entry in [paper-landscape.md](../landscapes/paper-landscape.md); a
headline- claim row in [synthesis-landscape.md](../landscapes/synthesis-landscape.md); the LAB-Bench + BixBench Phase 1
benchmarking commitment, the Horizyn-1 first-skill recommendation, the ProtHGT-vs-BioReason-Pro benchmark-informed
selection, the DIAMOND DeepClust Phase 4 mirror, and the BioReason-Pro atlas Phase 3 KB ingestion in
[total-landscape.md](../landscapes/total-landscape.md). Open questions go into `top-questions.md`. The two
named-archetype proposals (dual-encoder cross-modal retrieval; PLM + heterogeneous KG + graph transformer) become short
standalone syntheses once a second clean external instance lands.

---

## Inputs

The eight Group C paper notes (all in [`docs/paper-notes/`](../paper-notes/)):

- [rocks-et-al-2026-dual-encoder-contrastive-learning-accelerates-enzyme-discovery](../paper-notes/rocks-et-al-2026-dual-encoder-contrastive-learning-accelerates-enzyme-discovery.md)
  — Rocks et al., _Dual-encoder contrastive learning accelerates enzyme discovery_ (Horizyn-1, _PNAS_ 2026).
- [s41592-026-03030-z](../paper-notes/s41592-026-03030-z.md) — Buchfink et al., _Clustering the protein universe of life
  using DIAMOND DeepClust_ (_Nature Methods_ 2026).
- [2025.04.19.649272v1](../paper-notes/2025.04.19.649272v1.md) — Ulusoy & Doğan, _ProtHGT: Heterogeneous Graph
  Transformers for Automated Protein Function Prediction_ (bioRxiv 2025).
- [2505.23579v2](../paper-notes/2505.23579v2.md) — Fallahpour et al., _BioReason: Incentivizing Multimodal Biological
  Reasoning within a DNA-LLM Model_ (NeurIPS 2025).
- [2026.03.19.712954v1](../paper-notes/2026.03.19.712954v1.md) — Fallahpour et al., _BioReason-Pro: Advancing Protein
  Function Prediction with Multimodal Biological Reasoning_ (bioRxiv 2026).
- [2024.12.19.629561v2](../paper-notes/2024.12.19.629561v2.md) — Yang et al., _Multimodal foundation model predicts
  zero-shot functional perturbations and cell fate dynamics_ (PertFormer, bioRxiv 2025).
- [2407.10362v3](../paper-notes/2407.10362v3.md) — Laurent et al., _LAB-Bench: Measuring Capabilities of Language Models
  for Biology Research_ (FutureHouse, 2024).
- [2503.00096v3](../paper-notes/2503.00096v3.md) — Mitchener et al., _BixBench: a Comprehensive Benchmark for LLM-based
  Agents in Computational Biology_ (FutureHouse, 2025).

Cross-references that were load-bearing: [memory-synthesis.md](memory-synthesis.md),
[biological-foundation-models-synthesis.md](biological-foundation-models-synthesis.md),
[agentic-systems-synthesis.md](agentic-systems-synthesis.md), [llm-wiki-synthesis.md](llm-wiki-synthesis.md),
[skills-and-practices-synthesis.md](skills-and-practices-synthesis.md),
[synthesis-landscape.md](../landscapes/synthesis-landscape.md), the tokens-per-second paper
[2502.16721v1](../paper-notes/2502.16721v1.md), the practical-eval guide [2506.13023v1](../paper-notes/2506.13023v1.md),
and Kosmos [2511.02824v2](../paper-notes/2511.02824v2.md).

---

_This synthesis is the input to the next round of edits to [paper-landscape.md](../landscapes/paper-landscape.md),
[synthesis-landscape.md](../landscapes/synthesis-landscape.md), [total-landscape.md](../landscapes/total-landscape.md),
and the Phase 1 benchmarking + Phase 6 / 7 spec backlog. It should be revisited when the LAB-Bench and BixBench
local-deployment spikes land, when the ProtHGT vs BioReason-Pro benchmark-informed comparison runs, when ProteinReasoner
checkpoints appear and the encoder-swap experiment is possible, when an RNA-reasoning paper or tissue-level FM appears
in `context/papers/`, and when the next FutureHouse paper extends the LAB-Bench → BixBench → Kosmos arc._
