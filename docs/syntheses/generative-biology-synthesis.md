# Generative Biology Synthesis

## What this document is

A synthesis of six Group B papers — generative models that produce biological artifacts at scales from a single residue
to a complete bacteriophage genome — read through one question: _what does a private, local, M1-Max-bound assistant owe
a biochemist whose day-to-day reach extends from sequence design to enzyme engineering to mRNA optimization?_ The six
paper-notes live in [`docs/paper-notes/`](../paper-notes/) and are listed at the bottom. The audience matches the
[memory](memory-synthesis.md), [biological-foundation-models](biological-foundation-models-synthesis.md), and
[skills](skills-and-practices-synthesis.md) syntheses: input to the next round of edits to
[paper-landscape.md](../landscapes/paper-landscape.md) and [total-landscape.md](../landscapes/total-landscape.md), and
to the Phase 6/7 spec backlog and SAFETY.md.

The headline claim: **Group B is the first Wave 1 batch where the generate→score→filter→wet-lab loop becomes a
recognisable Linus orchestration archetype, and where the scale of the artefact being generated has direct dual-use
consequences for SAFETY.md.** Where [Group A](biological-foundation-models-synthesis.md) gave Linus a stable of
foundation models that _represent_ biology, Group B gives Linus a stable of models that _write_ it. Five of six release
weights; only mCSM-metal stays behind a webserver. Three are M1-Max-deployable today; one is a hybrid; two are
aspirational locally. And one — generative phages — crosses a real line that the existing dual-use literature
([2306.03809v1](../paper-notes/2306.03809v1.md)) explicitly warned about. The Phase 7 skill catalogue and SAFETY.md both
move as a result.

---

## The papers at a glance

[**mCSM-metal**](../paper-notes/1-s2.0-S0022283626000513-main.md) (Kumar, Malik & Ascher, _J. Mol. Biol._ 2026) — hybrid
neuro-symbolic predictor stitching ESMBind pLM embeddings, mCSM graph signatures, and ion-specific
coordination-chemistry rules into a per-mutation ΔP score for seven metal ions; webserver-only.

[**Trias**](../paper-notes/2025.05.13.653614v2.md) (Faizi, Sakharova & Lareau, bioRxiv 2025) — 47M-parameter BART
encoder-decoder that reverse-translates proteins into species-specific codon sequences across 640 vertebrates; trained
only on natural sequences, beats GenScript/IDT/Twist on a 30-variant GFP benchmark.

[**GenNA**](../paper-notes/2026.04.22.720063v1.md) (Shen et al., bioRxiv 2026) — 3.6B (and 0.36B) decoder-only
Qwen3-style Transformer with a 6,000-token cross-modal BPE vocabulary, prompted in plain English
(`molecule type, species, gene, function<seq>`) to generate eukaryotic nucleotide sequences.

[**DISCO**](../paper-notes/2604.05181v1.md) (Rector-Brooks et al., arXiv 2026, Caltech/Mila/Arnold lab) — joint
masked-discrete + continuous diffusion for sequence-and-structure co-design conditioned on arbitrary biomolecular
context; produced de novo carbene-transfer enzymes that exceed evolved P450 variants in TTN ([2604.05181v1](../paper-notes/2604.05181v1.md)).

[**DeepSeMS**](../paper-notes/2025.03.02.641084v1.md) (Xu et al., bioRxiv 2025) — ~100M Pfam-domain → SMILES Transformer
encoder-decoder; mined 27,139 ocean MAGs to produce 65,868 unique novel candidate metabolites including 8,783 antibiotic
candidates.

[**Generative phages**](../paper-notes/2025.09.12.675911v1.md) (King et al., Hie lab, bioRxiv 2025) — Evo 1/2 fine-tuned
on ~15K Microviridae genomes, ΦX174-templated prompting with inference-time guidance, **16 viable phages out of 302**,
several outcompeting wild-type ΦX174.

---

## The constellation: scales of generation

Group B is best read along one dominant axis — **the scale of the biological artefact being generated** — because that
axis controls nearly everything downstream: the architecture, the data requirements, the local-deployment story, the
validation cost, and the dual-use weight. Read this way the six papers form a clean ladder.

**Single residue (mCSM-metal).** A per-mutation ΔP score for whether a metal still binds. Strictly discriminative rather
than generative, but in a design pipeline scoring and proposing are inseparable, and mCSM-metal is the natural scoring
partner for residue-level proposals downstream. The architecture is the leanest in the corpus: no end-to-end training at
all, just ESMBind embeddings + RDKit and NetworkX features + per-ion exponential-decay penalty matrices. The hybrid
neuro-symbolic recipe — frozen pLM as noisy prior, symbolic rules as deterministic correction — is the most plausibly
transferable pattern in the group.

**Codon-level constrained generation (Trias).** The artefact is a coding sequence, generated under the hard constraint
of a fixed amino acid sequence and the soft conditioning of a species tag. Trias is also the smallest model in the
corpus by parameter count (47M) and the cheapest to run locally. The constraint structure is what keeps it small:
choosing among synonymous codons given context is a much narrower problem than open-ended generation, and 47M parameters
of BART trained on 10M vertebrate CDSs converge on a model whose perplexity correlates ρ = -0.76 with measured GFP
fluorescence on a held-out benchmark _without ever seeing expression data during training_. This is the corpus's
strongest argument that natural-sequence pretraining alone learns expression-relevant context.

**Mid-scale text-conditional generation (GenNA).** Full nucleotide sequences (tRNAs, rRNAs, histone CDSs) generated from
a short English prompt rather than from an amino-acid template. Hundreds to a few thousand bases; 3.6B (or 0.36B)
parameters; 416B characters across 2,221 eukaryotic species with structural XML tags interleaved into the token stream.
GenNA is the corpus's clearest demonstration that natural-language conditioning on biology is now a settled capability:
in-silico mutation scanning produces a clean stratification (synonymous < missense < nonsense < frameshift) without
variant-effect supervision; species-conditioned generation reproduces species-specific GC and codon distributions;
generated tRNAs pass tRNAscan-SE including spontaneous wobble behaviour. Validation is entirely _in silico_.

**Single-protein joint sequence+structure design (DISCO).** A step sideways into protein space and up in architectural
ambition. DISCO generates a protein's amino-acid sequence and its 3D backbone in a single denoising trajectory,
conditioned on whatever biomolecular context the user provides. The architecture is the heaviest in the corpus
(Pairformer + AlphaFold-3-class infrastructure trained on the unfiltered PDB); the validation is also the strongest,
because DISCO-designed carbene transferases not only worked but _exceeded evolved P450 variants_ on TTN. The Frances
Arnold attribution is not incidental — DISCO is the de novo enzyme paper that finally clears the bar her
directed-evolution program set.

**BGC → small-molecule (DeepSeMS).** Input is a biosynthetic gene cluster represented as ~250 Pfam-domain tokens, output
is a SMILES string. The artefact is a small molecule; the model is ~100M parameters of vanilla Transformer
encoder-decoder; the training set is the painfully small MIBiG (3,029 paired examples) blown up to 55,903 by
scaffold-aligned SMILES enumeration. Once trained, DeepSeMS scales effortlessly: applied to 27,139 ocean MAGs it
produces 65,868 unique novel candidate metabolites. The generation→curation pipeline runs at metagenomic scale; wet-lab
validation does not.

**Whole-organism genome (generative phages).** The top of the ladder. The artefact is a complete ~5 kb phage genome with
eleven densely-overlapping ORFs and a viability surface that decades of rational engineering have struggled to navigate.
The substrate is Evo 1 (7B/131K) and Evo 2 (7B/8K) fine-tuned on ~15K Microviridae genomes; the recipe is a six-stage
pipeline (host → template family → SFT → conserved-prefix prompt → tiered inference-time scoring → wet-lab); the
validation is the strongest in the corpus because **16 of 302 designs produced viable phages ([King et al., 2025](../paper-notes/2025.09.12.675911v1.md))**, several outcompeting
ΦX174 itself, and a cocktail broke through LPS-mediated resistance that ΦX174 alone never could. This is also the paper
that crosses the line into dual-use territory.

The ladder is not just descriptive. Every cross-cutting thread — local deployability, validation cost, dual-use weight,
foundation model dependence, KG schema choice — shifts monotonically along the scale axis. Bigger artefacts cost more to
generate, more to validate, more to deploy locally, and more to gatekeep.

---

## Cross-cutting threads

### Open weights vs webserver-only release

**Five of six release weights** under permissive terms: Trias (HuggingFace), GenNA (HuggingFace + GitHub), DISCO (GitHub
with checkpoints), DeepSeMS (GitHub plus a hosted webserver in China), and the generative-phage Evo variants
(HuggingFace + Zenodo training data). **mCSM-metal is the lone webserver-only release** — the only access is the
biosig.lab.uq.edu.au Flask server with a JSON API and 7-day job retention.

This split is operationally cleaner than the corresponding text-LLM landscape, but mCSM-metal is the motivating case for
an `external_api_tool` registry class — a class the Group A synthesis already flagged as needed for AlphaGenome's hybrid
release. Group B makes the case sharper: webserver-only is one of two stable release modes, and Linus needs a
first-class abstraction for it. The contrast within Group B is also instructive: generative phages release everything
precisely because the recipe is general and limiting access is illusory once the substrate FM is itself open. mCSM-metal
restricts release for what reads as resource-protection rather than safety reasons.

### M1 Max viability per scale

**Comfortably local for inference.** Trias (47M, BART, MPS-friendly HuggingFace stack) is the _easiest_ model in either
Group A or B to deploy on M1 Max — minutes-to-pull, runs alongside any Worker LLM in unified memory without contention.
DeepSeMS at ~100M is comfortable under PyTorch CPU or MLX with a small port. GenNA's 0.36B variant is M1-Max-friendly
under MLX int4 ("explicitly provided to facilitate efficient experimentation and development in resource-constrained
settings" — the author's framing reads as written for Linus's hardware envelope).

**Local with engineering.** GenNA's 3.6B variant lives at Mistral-7B-class memory footprint at int4, within the 32 GB
envelope when no other Worker is running. The cross-modal BPE vocabulary means existing Qwen3 LoRA tooling will not
transfer cleanly.

**Remote tool.** mCSM-metal is webserver-only by construction. For Phase 1–3, wrapping is the realistic move.

**Aspirational locally.** DISCO inference at the scales reported (~10⁴ candidates per campaign) requires substantial
GPU; the Pairformer + AlphaFold-3-class backbone alone is many gigabytes, with no MLX path. The generative-phage
pipeline depends on Evo 1 or Evo 2, neither of which has a tractable MLX port; Evo 1's 131K context is well beyond M1
Max's comfortable envelope. Both are remote-Worker-tier; Phase 8 is the earliest realistic horizon for local DISCO.

The pattern is monotonic in artefact scale: single residue and codon-level generation are local; mid-scale
text-conditional and small-molecule generation are local with engineering; single-protein joint design and whole-genome
generation are remote. **Three of six are Linus-deployable today; one needs external API; two are aspirational pending
external GPU access.**

### Foundation-model substrate dependencies

Group B is downstream of Group A in a way that becomes explicit on synthesis reading. The generative-phage pipeline _is_
Evo 2 fine-tuned — the experimental validation Evo 2 was designed to enable, and the answer to the Group A synthesis's
"what would Evo 2 enable downstream?" question. mCSM-metal _is_ ESMBind, which is itself ESM-2 fused with ESM-IF; remove
the substrate FM and mCSM-metal has no baseline binding probability to refine. DISCO uses an ESM-style pLM as a frozen
input encoder during cross-modal recycling. GenNA descends conceptually from the entire nucleotide-FM lineage even
though it reinitialises from scratch. Even DeepSeMS, which uses one-hot Pfam IDs rather than learned embeddings, has an
obvious modernisation path that swaps Pfam IDs for LucaOne or ProteinReasoner embeddings. **Trias is the genuine
outlier** — a self-contained 47M model trained from scratch on natural CDSs, with no upstream FM dependency.

The implication for Linus's tool registry is that **Group B and Group A are not parallel skill collections — they are
vertically composed.** A registry that exposes Evo 2 as a Worker but not the generative-phage fine-tune is incoherent
(the fine-tune _is_ the useful object). Group A models are the _substrate_ layer; Group B models are the _application_
layer that consumes the substrate. The Phase 7 skill catalogue should reflect this stratification.

### Validation rigor

**Wet-lab validated:** DISCO (90 designs, four new-to-nature reactions catalysed at TTN exceeding evolved P450 variants;
error-prone PCR confirms evolvability), generative phages (302 candidates, 16 viable phages with fitness and
resistance-breaking data; Evo-Φ36 cryo-EM at 2.9 Å), and mCSM-metal (~1,400-mutation alanine-scanning blind validation
plus the SOD1/ALS recapitulation). **In-silico-only:** Trias (correlation against published expression data on a
30-variant GFP benchmark), GenNA (perplexity stratification, validator passes on generated sequences), and DeepSeMS
(Tanimoto similarity to MIBiG, no synthesis on the 65k novel metabolites).

The split correlates strongly with artefact scale. The cheapest-to- validate artefacts get wet-lab validation; the
combinatorially-large artefacts cannot. This is not a defect of the in-silico papers — the validation cost is genuinely
prohibitive — but it is a binding constraint on what Linus can claim. **Naked GenNA output is hypothesis. Naked DeepSeMS
output is hypothesis. Naked Trias output is hypothesis with an unusually strong likelihood-as-fitness-proxy correlation
backing it but only on one published benchmark.** The Linus tool wrappers should surface this as a property of the tool
— every candidate carries a `validation_tier` tag (wet-lab, held-out in silico, distribution in silico, none) that
propagates into the KnowledgeBase.

The DISCO + error-prone PCR pattern is worth singling out: DISCO-designed dCT-H11 produced ~35 improved variants under
one round of random mutagenesis ([2604.05181v1](../paper-notes/2604.05181v1.md)) with substitutions scattered across the protein, confirming the designs occupy fitness
regions accessible to evolution. This is the strongest validation pattern in the corpus — not just "it worked once" but
"it occupies a navigable fitness landscape."

### Inference-time guidance and prompting

A pattern repeated across four of six papers: control over the generative artefact comes not from supervised fine-tuning
on the target task but from inference-time conditioning. **GenNA's four-field prompt** is a free-form English channel;
**Trias's species tag** is a categorical channel that shapes 640 codon-usage regimes from one set of weights; **the
generative-phage recipe** uses a conserved 4–9 nt prefix prompt plus three tiers of inference-time scoring; **DISCO**
uses Feynman-Kac correctors ([2604.05181v1](../paper-notes/2604.05181v1.md)) to tilt sampling toward joint sequence+structure rewards and toward on-target ligand binding
while penalising off-target decoys.

This is the same thread the [memory synthesis](memory-synthesis.md) followed in the text-LLM space: the right answer to
"make the model better at X" is increasingly "spend inference-time compute through the right scoring function" rather
than "fine-tune harder." For Linus the implication is that generative-biology Workers need a richer interface than just
a prompt and a sampling temperature — a structured _conditioning surface_ that bundles the prompt, the categorical tags,
the per-step scoring functions, and the acceptance/rejection thresholds. A registry that exposes generative-biology
models as `model(prompt) → output` underspecifies the actual control surface; one that exposes
`model(conditioning_object) → ranked_candidates` is closer to the shape these papers describe.

The Feynman-Kac corrector framework from DISCO is reusable beyond its protein-design context. Wherever Linus has a
per-trajectory reward (code synthesis with test-pass rewards, SQL with execution rewards, the Trias
likelihood-against-expression setting), FKC is the right inference-time pattern. Worth a short synthesis note when a
second instance lands.

### Dual-use risk gradient

Sorting the six papers by dual-use weight produces a sharp ordering. **Generative phages** sits at the top by an order
of magnitude: the first experimental demonstration that a genome language model can design viable, complete genomes from
scratch, the recipe is fully published and reproducible, the substrate FM (Evo 2) is open, and the King et al. authors
themselves curated training data to exclude eukaryotic viruses _because they recognised the dual-use surface_. The paper
designs phages, not human pathogens; the wet-lab work was done under a biosafety regime appropriate for non-pathogenic
phages on non-pathogenic hosts. But the recipe is general. Applying it to a pathogen FM would produce generative
pathogen design.

**DISCO** sits next: de novo enzyme design is dual-use in the sense that a designer enzyme can catalyse chemistry that
would not otherwise occur, and DISCO has demonstrated the capability to design enzymes that exceed evolved variants —
Linus should not surface DISCO-mediated design of enzymes for controlled or precursor chemistry. The remaining four are
substantially lower-risk: mCSM-metal predicts mutation effects on existing structures (no novel catalytic capacity);
Trias optimises codons within a fixed protein (no novel function); DeepSeMS predicts metabolite structures from natural
BGCs (no novel biosynthesis); GenNA generates eukaryotic sequences within natural functional classes.

The connection to [2306.03809v1](../paper-notes/2306.03809v1.md) is direct. That paper's threat model was that LLMs
collapse the tacit-knowledge moat around pandemic biology by acting as patient expert tutors over the literature.
**Generative phages does the analogous collapse for whole-genome design**: it removes the generative-design moat that
decades of rational phage engineering struggled to navigate. SAFETY.md needs an explicit "generative whole-genome
design" tier that is not the same as the existing OS/filesystem autonomy tiers. Linus does not run Evo 2 locally and is
unlikely to before Phase 8, but the relevant question is not "can Linus do this" — it is "should Linus assist with
workflows that are doing this elsewhere," and the answer needs a written policy before any biology Worker arrives that
could plausibly chain into one.

### Architectural pattern repetition

Three recurring patterns plus three outliers. **Transformer encoder-decoder over biological sequences**: Trias and
DeepSeMS are the same architectural shape — vanilla 6+6-layer encoder-decoder in the 47M–100M range, trained on a small
curated paired dataset with a small target vocabulary, on single-A100-class compute. The pattern is "domain-specialised
small Transformer that beats hand-encoded baselines on the hardest cases" and it is one of the most plausible templates
for _Linus-trained_ domain models in Phase 6. **Autoregressive decoder-only Transformer over a unified vocabulary**:
GenNA stands alone in Group B; the cross-modal BPE lesson — putting nucleotides, English, and XML in one token space —
generalises to any setting where two modalities want to coexist (protein + UniProt descriptions, SMILES + IUPAC names).
**Autoregressive genome model with inference-time guidance**: the generative-phage pipeline is Evo 1/Evo 2 (StripedHyena
2 hybrid) plus a tiered scoring stack — the contribution is the _recipe_ more than any new architectural primitive.

**Outliers.** DISCO is the corpus's only diffusion-based model (masked discrete + continuous, jointly trained), the
heaviest by far. mCSM-metal is the corpus's only hybrid neuro-symbolic predictor — pLM embeddings as prior, structural
graph features as quantification, ion-specific penalty matrices as deterministic correction; no end-to-end training at
all. Each is the lone instance of its archetype here but each archetype is generally important: diffusion is the
dominant class for sequence-and- structure co-design across the field; hybrid neuro-symbolic is the dominant pattern for
narrow-task protein-engineering tools where data is scarce. Both deserve named-archetype entries in `docs/syntheses/`
once a second instance lands. The mCSM-metal note already proposed the **PLM+graph+rules archetype** by name; this
synthesis seconds it.

### The generate→score→filter→wet-lab workflow

Across DISCO, generative phages, DeepSeMS, and (implicitly) GenNA when paired with downstream validators, the same
orchestration shape recurs: a generative model produces a large pool of candidates; one or more scoring functions rank
them; deterministic filters cut to a small set; that small set is handed to wet-lab. DISCO uses ~10⁴ candidates filtered
to 90 designs. Generative phages uses thousands filtered to 302. DeepSeMS produces 65,868 candidates filtered by RDKit
substructure search to 8,783 antibiotic candidates. GenNA's generated tRNAs are filtered by tRNAscan-SE; rRNAs by
Infernal; histone CDSs by ProGen2 perplexity and translated MW × pI.

This is the same shape the [skills synthesis](skills-and-practices-synthesis.md) named for Dan's research workflow at
large. Group B is the first batch where the shape is _intrinsic to the tools themselves_, not just to Dan's wrapping
around them. The Linus orchestration layer should expose this as a **generative-biology workflow archetype**: a typed
pipeline that takes a generative Worker, a bank of scoring Workers, a filter specification, and a candidate-pool size
cap; runs the pipeline with intermediate KG persistence at each stage; surfaces the ranked output to Dan for wet-lab
decision. **Recommend `docs/syntheses/generative-biology-archetype.md`** that pairs this synthesis with the Evo 2
paper-note as the canonical worked example.

---

## Implications for Linus skills (Phase 7)

Recommended sequence: **Trias first, then DeepSeMS as a wrapped local Worker, then mCSM-metal as an external HTTP tool,
then GenNA in the 0.36B variant, with DISCO and the Evo 2 / generative-phage pipeline deferred as remote-Worker-tier
skills.**

**Skill 1: `linus.bio.protein.codon_optimize`** (Trias). The right first skill for the same reasons REBEAN was the right
first Group A skill: small (47M), open weights, modern HuggingFace BART stack, high-frequency biotech use case for Dan's
actual work. Two endpoints in one skill: `codon_optimize(protein, organism)` and `score_codon_sequence(cds, organism)`.
The scoring endpoint is just as valuable as the generation endpoint because it lets Dan rank candidate sequences from
any source using the same calibrated metric the paper validates against expression data. Caveats for the wrapper:
vertebrate-only; greedy decoding has a documented rare-codon momentum failure mode; expose decoding-strategy controls.
Effort: a focused week.

**Skill 2: `linus.bio.bgc.predict_metabolite`** (DeepSeMS). Natural companion to a future Bacformer/REBEAN metagenomic
skill. Input is a GenBank-format BGC or an antiSMASH job ID; output is a ranked list of SMILES with prediction scores.
The model runs locally; scaffold-stripped output should be flagged as constitutional-formula- only. The
substructure-based virtual screening step (RDKit filters for antibiotic functional groups) is a clean orchestration
shape worth wrapping as part of the skill: model proposes, deterministic chemistry library disposes. Effort: a focused
week plus license check before mirroring weights. The 65k-metabolite ocean catalogue should be ingested into
KnowledgeBase as a Phase 4 deliverable alongside the skill.

**Skill 3: `linus.bio.protein.metal_mutation_score`** (mCSM-metal, external HTTP tool). The first instance of the
`external_api_tool` registry class. Input is a PDB accession + mutations; output is per-ion ΔP scores plus the
compensatory-interaction subgraph. The webserver's clean async-submission / job-ID / polling API makes this an ideal
first test case: exercises auth, rate-limiting, polling, result caching (7-day job retention upstream), graceful
upstream-offline degradation, and provenance tagging without needing weights to land. Effort: a few days plus the ADR.

**Skill 4: `linus.bio.dna.text_to_sequence`** (GenNA, 0.36B variant). The natural-language → biology bridge the
orchestration layer needs. Maestro translates Dan's intent into the four-field template, dispatches to the GenNA Worker,
captures sequences, and routes to a validator chain (tRNAscan-SE, Infernal, BLASTP, optionally Evo 2 perplexity). The
Phase-1 smoke test — 50 prompts × {0.36B, 3.6B} × MLX int4, measured by validator pass rates and wall-clock — settles
which variant becomes the default Worker. Caveats: distribution sharpening at default sampling means the wrapper must
expose temperature and top-p controls when Dan wants tail diversity; the 6,000-token BPE washes out single-bp
resolution, so cis-regulatory work should route to a different tool. Effort: a focused fortnight including the MLX
conversion work.

**Deferred — DISCO and the Evo 2 / generative-phage pipeline.** Both are remote-Worker-tier. DISCO is among the cleanest
Maestro/Worker decompositions in the corpus, but the remote Worker requires GPU access Linus does not yet have. The Evo
2 fine-tunes have the same shape. Both should be specced as `external_api_tool` entries waiting for a Phase 8 Mac Studio
tier or external GPU subscription, not left out of the registry entirely.

The Phase 7 skill organisation question — modality-grouped (`linus.bio.dna.*`, `linus.bio.protein.*`,
`linus.bio.molecule.*`) or task-grouped — should resolve toward modality-grouped, for the same reason the Group A
synthesis recommended: validity domains, output types, and failure modes are modality-bound.

---

## Implications for Linus tool registry

Group B forces three concrete tool-registry decisions.

**An `external_api_tool` registry class.** Both syntheses now recommend this — Group A flagged AlphaGenome's hybrid
release; Group B adds mCSM-metal as a pure-webserver case and DISCO / Evo 2 as future remote-GPU cases. The class needs
auth, rate-limiting, async job-ID + polling support, result caching with TTL aligned to the upstream's retention policy,
graceful offline-fallback, trust-tier tagging, and provenance recording. The registry should treat these as _first-class
Workers_, not as a degraded path — orchestration patterns that work for local Workers (KG persistence, scratchpad
retention, session memory) need to work for remote ones too. **Recommend an ADR before any biology skill ships.**

**A "candidate generator + scorer + filter" pipeline pattern.** The shape is intrinsic to four of six Group B papers.
The orchestration layer should expose a typed pipeline abstraction: a generative Worker, a list of scoring Workers (each
with a weight and a per-trajectory or post-hoc tag), a filter specification, a candidate-pool size cap, and intermediate
KG persistence at each stage. **Recommend a one-page spec in `docs/specs/`** paired with the Phase 7 generative-biology
archetype synthesis.

**A `validation_tier` tag on every candidate artefact.** Group B candidates span everything from "wet-lab demonstrated
functional" to "in silico against chemistry-validity baseline." The tier needs to ride alongside the artefact through
the orchestration layer and into the KnowledgeBase, so a downstream Worker reading the KG can distinguish "DISCO
designed and the Arnold lab validated this enzyme" from "DeepSeMS proposed this metabolite and no one has ever
synthesised it." Without this discipline the KG silently homogenises evidence levels within months. **Recommend the
provenance schema include a typed `validation_tier` field** with enum values `wet_lab_validated`, `held_out_in_silico`,
`distribution_in_silico`, `none`.

---

## Implications for Linus safety (SAFETY.md)

Group B is the first Wave 1 batch where the _capability being demonstrated_ is the kind of thing that needs an explicit
SAFETY.md policy, even if Linus never runs the highest-risk tools locally. Existing SAFETY.md tiers are framed around OS
/ filesystem / shell autonomy — necessary, but not sufficient where the generated artefact itself is the safety surface.
The [2306.03809v1](../paper-notes/2306.03809v1.md) note already argued for a "biological dual-use" section before any
biology Worker arrives; Group B sharpens the case from a hypothetical to a specific, published recipe.

**The recommended SAFETY.md addendum** should name three tiers along the artefact-scale gradient.

_Tier 1 (low-risk generative-biology tools):_ Trias, DeepSeMS, mCSM-metal, GenNA within natural functional classes.
Allowed by default within Linus's autonomy envelope; provenance and validation-tier tagging required; no special gating.

_Tier 2 (designer-protein / designer-enzyme generation):_ DISCO and any future de novo protein-design tool. Allowed but
flagged: the orchestration layer should refuse to surface designer-enzyme proposals for explicit controlled / precursor
/ weaponisable chemistry classes (a deny-list maintained against published illicit precursor and chemical weapons
convention schedules), and should require Dan-explicit confirmation before dispatch when the prompt context contains
those classes.

_Tier 3 (whole-genome generative design):_ the Evo 2 / generative-phage pipeline and any successor. Forbidden as a
default capability; requires an explicit per-session opt-in plus a written research justification that lands in the
audit log; the orchestration layer enforces this _before_ any Worker is invoked, because once a Worker has produced a
viable genome design even a discarded output has been generated, logged, and potentially leaked.

The asymmetry between Dan's expertise and the threat model is unchanged from the dual-use synthesis: Dan is a PhD
biochemist with genomics specialisation, so the contract is not about denying him knowledge he already has but about
ensuring the _system's_ behaviour is caller-invariant, audit-clean, and would generalise to a future multi-user Linus or
a compromised-machine scenario. **The explicit SAFETY.md update** should reference both this synthesis and
[2306.03809v1](../paper-notes/2306.03809v1.md) directly, name the six Group B papers and the artefact-scale gradient,
and commit to the three-tier policy as a Phase 1 deliverable rather than a Phase 7 retrofit.

A second SAFETY.md hook worth adding, motivated by the generative- phage paper specifically: the _training-data curation
property_ that King et al. relied on (Evo 2's deliberate exclusion of eukaryotic viruses including pathogenic human
viruses) is a model-level safeguard that propagates into downstream tools. Linus should **prefer substrate FMs that
publicly document their hazard-curation posture**, and should record curation status as a tool registry property.

---

## Implications for Linus KnowledgeBase

Group B produces designed-artefact catalogues at a scale that makes KG ingest a first-class concern. The 65,868 ocean
metabolites from DeepSeMS (with provenance to source MAG, ocean province, depth, temperature, oxygen, scaffold/QED
annotations); the 16 viable phages plus 302 candidate genomes from generative phages (with parent prompts, model
versions, score vectors, experimental fitness data, cryo-EM maps); the 90 DISCO designs across four reactions (with
sequence-structure-target tuples, AlphaFold confidence, active-site geometry, measured TTN/yield/selectivity, and the
dCT-H11 mutational landscape) — all of this is structured KG content with unusually clean provenance.

The right KG schema for Group B content is the **designed-artefact triple** of
`(designed_artefact + design_rationale + experimental_outcome)`, where each component is a typed node with explicit
provenance. The designed-artefact node carries the sequence (or structure, or SMILES), the modality, the source model

- version, and the generation parameters. The design-rationale node carries the conditioning context, the scoring
  functions applied at inference time, and the filter thresholds. The experimental-outcome node carries the validation
  tier, the measured values where applicable, and the date / experimenter / protocol. The triple is reusable across the
  entire generative- biology landscape, not just Group B.

This is also where the [LLM Wiki synthesis](llm-wiki-synthesis.md)'s claim-typing discipline does the most work in Group
B specifically. A Trias-generated codon sequence with ρ = -0.76 likelihood correlation and no wet-lab validation is a
different kind of claim than a DISCO-designed enzyme with 4,050 TTN measured in the Arnold lab. The KG schema should
make the distinction load-bearing — different `validation_tier` enum values, different decay rates for retrieval
ranking, different display treatment when surfaced to Dan.

The 65k-metabolite ocean catalogue and the 302-candidate phage corpus are the two best **stress-test datasets** for the
KG schema itself. Phase 3 KG work should ingest at least one of them as a worked test case, and should use the ingest
exercise to firm up the schema before any Linus-internal generative-biology Worker starts writing back.

---

## Tensions and open questions

**Is "generate → score → filter → wet-lab validate" worth naming as a Linus generative-biology archetype now, or wait
for a second in-corpus instance beyond DISCO and generative phages?** The recommendation above is to write the archetype
synthesis paired with the Evo 2 paper-note as the canonical worked example. The risk of premature naming is low because
the shape is intrinsic to the field, not just to this corpus.

**Should the Evo 2 + generative-phages pairing be a focused mini- synthesis?** The Group A synthesis already flagged
this as a Wave 3 deliverable. Group B reading strengthens the recommendation — the paired synthesis would force a sharp
answer to the local-vs-remote-Evo-2 question, the SAFETY.md tier-3 policy, and the external-Worker-tier infrastructure
question.

**What is the right pattern for wrapping webserver-only tools like mCSM-metal?** An `external_api_tool` registry class
plus an ADR. The deeper open question is whether the registry should treat external tools as first-class Workers or as a
degraded path. The synthesis-level argument is _first-class_: Linus needs the orchestration patterns to work uniformly
across substrates, not bifurcate by deployment locus.

**Does generative whole-genome design warrant explicit SAFETY.md tier-control before Phase 7 even starts?** Yes — write
the three-tier policy as a Phase 1 deliverable. Writing policy now is cheap; retrofitting it under pressure is
expensive.

**Generalist Group A FMs vs specialist Group B generators — which combinations are worth implementing first?** The
combinations that reinforce most strongly: (1) **Trias + GenNA** for sequence design, with GenNA generating CDSs from
free-text prompts and Trias re-codonising them for the target host; (2) **REBEAN + DeepSeMS** for metagenomic discovery,
with REBEAN annotating EC-class enrichment and DeepSeMS predicting metabolite structures from BGCs in the same sample;
(3) **Bacformer + DeepSeMS** for bacterial genome → BGC → metabolite analysis; (4) **mCSM-metal + DISCO (Phase 8)** for
designer metalloenzyme analysis; (5) **AlphaGenome + GenNA** for text-conditional regulatory-region generation with
mechanistic variant scoring downstream. The first three are tractable in Phase 7; the last two are Phase 8.

**Should DeepSeMS's Pfam-domain-token input representation be modernised with LucaOne or ProteinReasoner embeddings
before being exposed as a Linus skill?** The DeepSeMS note flagged this as a Phase 6 experiment Dan could spec for a
Worker. The synthesis-level argument is that the experiment is genuinely informative about the Group A → Group B
substrate-vs-application stratification: modernisation either buys accuracy on cryptic BGCs (stratification empirically
real) or doesn't (specialist-from-scratch posture more durable than substrate-dependence reading suggests). **Recommend
the experiment as a Phase 6 spike** in either case.

**FKC steering as a generic Linus inference-time pattern?** The DISCO note flagged this as a synthesis-level question.
Group B reading reinforces: Feynman-Kac correctors are mathematically principled where best-of-N is heuristic, and the
pattern applies wherever a per-trajectory reward is available. Worth recording when a second instance lands.

---

## Where this synthesis fits

Group B is the second Wave 1 biological batch and the first batch where the value proposition is _generative_ rather
than representational. The [Group A synthesis](biological-foundation-models-synthesis.md) argued that Linus's value
proposition becomes unambiguously domain- specific when biological foundation models become local Workers; Group B
argues that the _next_ step is generative tools that turn Dan's intent into candidate biology, with Linus orchestrating
the generate→score→filter loop and the KnowledgeBase recording design rationale and experimental outcome as durable
artefacts.

The connection to **Group A** is direct and vertical. Group A models are the substrate; Group B models are the
application layer that consumes the substrate. The generative-phage pipeline _is_ Evo 2 fine-tuned; mCSM-metal _is_
ESMBind plus chemistry rules; DISCO uses an ESM-style pLM as a frozen input encoder; even DeepSeMS has an obvious
modernisation path. The Phase 7 skill catalogue should reflect this stratification — substrate skills and application
skills are not parallel, they are layered.

The connection to the **eventual Group C synthesis** (function / discovery — the analysis side complementary to
generation) will close the loop. Group B generates candidates; Group C will analyse them. A complete generative-biology
workflow chains Group B (design) with Group C (analyse) under Linus orchestration, with KG persistence at each stage and
validation-tier propagation throughout.

The connection to **Group F** (safety — dual-use) is the sharpest in this synthesis. The
[2306.03809v1 dual-use note](../paper-notes/2306.03809v1.md) warned in 2023 that LLMs collapse the tacit-knowledge moat
around pandemic biology; the King et al. generative-phage paper is the first in-corpus demonstration of an analogous
capability collapse for whole-genome design, with a fully published recipe and an open substrate FM. SAFETY.md needs the
three-tier policy named above, with explicit references to both papers, before any biology Worker arrives that could
plausibly chain into the higher-risk capabilities.

The connection to the **memory pillar** comes through KnowledgeBase schema. Generative-biology artefacts have unusually
rich and unusually clean provenance — every designed artefact has a parent prompt, a model version, a scoring vector,
and (where wet-lab validated) an experimental outcome. The
`(designed_artefact + design_rationale + experimental_outcome)` triple is a stress test for the KG schema and a worked
example of the `model_prediction` edge class the Group A synthesis proposed.

This synthesis should produce edits to [paper-landscape.md](../landscapes/paper-landscape.md) (a Group B cluster entry
mirroring Group A's, organised by the artefact-scale axis),
[synthesis-landscape.md](../landscapes/synthesis-landscape.md) (the headline claim plus the three-tier SAFETY.md
recommendation as a quick-reference row), and [total-landscape.md](../landscapes/total-landscape.md) (the four Phase 7
skill priorities, the `external_api_tool` ADR, the `generate→score→filter` archetype synthesis, the Phase 4 ocean-
metabolite catalogue mirror, the SAFETY.md three-tier addendum). The Wave 3 Evo 2 + generative-phage mini-synthesis goes
onto the synthesis backlog with its scope expanded to also serve as the worked example for the generative-biology
archetype.

---

## Inputs

The six Group B paper notes (all in [`docs/paper-notes/`](../paper-notes/)):

- [1-s2.0-S0022283626000513-main](../paper-notes/1-s2.0-S0022283626000513-main.md) — Kumar, Malik & Ascher, _mCSM-metal_
  (_J. Mol. Biol._ 2026).
- [2025.05.13.653614v2](../paper-notes/2025.05.13.653614v2.md) — Faizi, Sakharova & Lareau, _Trias_ (bioRxiv 2025).
- [2026.04.22.720063v1](../paper-notes/2026.04.22.720063v1.md) — Shen et al., _GenNA_ (bioRxiv 2026).
- [2604.05181v1](../paper-notes/2604.05181v1.md) — Rector-Brooks et al., _DISCO_ (arXiv 2026).
- [2025.03.02.641084v1](../paper-notes/2025.03.02.641084v1.md) — Xu et al., _DeepSeMS_ (bioRxiv 2025).
- [2025.09.12.675911v1](../paper-notes/2025.09.12.675911v1.md) — King et al., _Generative design of novel bacteriophages
  with genome language models_ (Hie lab, bioRxiv 2025).

Cross-references that were load-bearing:
[biological-foundation-models-synthesis.md](biological-foundation-models-synthesis.md) (Group A sister synthesis;
substrate-vs-application stratification), [memory-synthesis.md](memory-synthesis.md) (KG schema as semantic memory
layer; inference-time-compute thread), [skills-and-practices-synthesis.md](skills-and-practices-synthesis.md)
(hypothesis-generation + validator-bank workflow), [llm-wiki-synthesis.md](llm-wiki-synthesis.md) (claim typing for
model-derived KG content), and [paper-notes/2306.03809v1.md](../paper-notes/2306.03809v1.md) (Group F dual-use biotech;
the policy reference for the SAFETY.md three-tier addendum).

---

_This synthesis is the input to the next round of edits to [paper-landscape.md](../landscapes/paper-landscape.md),
[synthesis-landscape.md](../landscapes/synthesis-landscape.md), [total-landscape.md](../landscapes/total-landscape.md),
and the Phase 6 / 7 spec backlog plus a Phase 1 SAFETY.md addendum. It should be revisited when the Trias and DeepSeMS
Phase 7 wrappers land, when the Wave 3 Evo 2 + generative-phage mini-synthesis is written, when the `external_api_tool`
ADR is drafted, when DISCO local-deployability becomes tractable on a Mac Studio tier, and when any new Group B paper
enters `context/papers/`._
