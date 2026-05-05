# Group 9 Synthesis — Bioinformatics & Domain-Specific Science Models

**Date:** 2026-05-04 **Author:** Claude Sonnet 4.6 (Worker, commissioned by Dan Browne) **Trigger:** G9 fan-out
synthesis pass; four new repos evaluated: Bacformer, BioReason, bioSkills, deepsems.

---

## What this document is

Group 9 is the most directly mission-aligned cluster in the entire fan-out run. The other groups abstract outward —
inference substrate, memory architecture, knowledge-graph patterns, agent orchestration — but G9 lands squarely in Dan's
PhD specialization: bacterial genomics, variant biology, secondary metabolite chemistry, and the computational biology
tooling that sits around all of them. That direct alignment has a strategic implication: these four repos are not just
infrastructure candidates; they are evidence for what Linus can credibly offer that generic AI tooling cannot.

The verdicts are: **one Integrate** (bioSkills — the inaugural Phase 7 skills payload), **three Study**. Bacformer
carries a "path to Integrate at Phase 7" hedge because Apple Silicon viability is plausible but unverified. BioReason
and deepsems are Study because one is CUDA-locked at training time and the other is a narrow wrapper target whose value
is conditional on a paper-reproducibility check. But the synthesis across all four is richer than four independent
verdicts: the group collectively outlines a working stack that could serve both Dan's own research and a paying biotech
client.

---

## The unifying thesis

Dan has something unusual: a PhD biochemist with 13 years of scientific Python, hands-on genomics pipelines, and a local
AI orchestration backend in active development. The G9 repos represent the domain half of that equation — specialized
biological FMs, evaluated benchmarks, and validated tools that most LLM-infrastructure projects would never even examine
because their authors do not have the domain literacy to evaluate them. The unifying claim this group supports is that
the combination of Linus's infrastructure (orchestration layer, KnowledgeBase, Worker pipeline) with G9's domain content
is not just a personal productivity stack. It is the concrete substrate for a biotech intelligence product that a
boutique company or research lab would pay for today, without waiting for Phase 6 or Phase 7 to land.

The entrepreneurial surface that the skills-and-practices synthesis named as "scientific literature intelligence for
biotech teams" can now be described with specific components: bioSkills for domain-correct code and tool patterns (G9),
scientific-agent-skills for lab-workflow scaffolding (G8), paper-qa for literature retrieval (G8), LAB-Bench for
measuring whether the stack actually works on research tasks (G8), and KnowledgeBase as the indexed corpus that
everything retrieves from. G9 contributes the largest and most validated piece of that stack, and it contributes it
today rather than at some future phase. That is a meaningful finding.

---

## Key findings

**bioSkills is a clean Integrate and the strongest verdict in G9 by a margin.** The 438 SKILL.md files across 63
bioinformatics categories constitute an order of magnitude more coverage than any other Skills-format repo in the run:
OmegaWiki has 24, infranodus-skills has 15, openrouter-skills has 8, AgenticResearchWiki has 2, scientific-agent-skills
from G8 has 135. bioSkills at 438 is also the only Skills repo in the entire collection that ships a third-party
published evaluation — the Bio-Task Bench PDF in `resources/bioskills_eval_20260328.pdf` — with concrete benchmark
numbers (Codex GPT 5.4-Mini: +0.049 absolute improvement, baseline 0.935 to 0.984 with skills loaded). The coverage map
aligns directly with Dan's work: single-cell RNA-seq, ATAC-seq, variant calling, differential expression, pathway
analysis, population genetics, GWAS, structural biology via ESMFold and Chai-1, CRISPR screens. No other repo in G9 or
its sibling groups delivers this kind of domain-validated, immediately deployable capability. The install is a single
shell script against any Claude Code project. This can be done today, independent of Linus development, as a free tools
upgrade.

**Bacformer is the only Apple-Silicon-realistic broad bacterial FM in the entire run.** The protein-embedding-as-token
pattern — ESM2 or ESM++ embeds each ORF, then a second-stage Transformer treats the genome as a sequence of those
embeddings — compresses a multi-megabase bacterial genome to at most 6000 tokens, making context lengths tractable even
for large genomes. The 300M Large checkpoint (ESM-C geometry, 30 layers, 960 hidden, 15 heads) requires roughly 600 MB
of weights plus activation memory for a full-genome inference pass, well within 32 GB unified memory on M1 Max. The base
install is plain `torch>=2.5.1` plus `transformers` — no flash-attn required for inference, though the optional
`faesm[flash-attn]` path will fall back gracefully to vanilla HF on Metal. The recommendation in the repo note is a
Phase 1 evaluation spike: stand up Bacformer Large in a dedicated conda env, run the operon-prediction and
strain-clustering tutorials end-to-end on MPS, capture wall-clock and memory in `benchmarks/results/`, and let that
number determine whether this becomes a Phase 7 skill or stays study material. No other bio FM in the collection offers
a comparable path to practical M1 Max deployment.

**BioReason is architecturally important but operationally blocked.** The paper (arXiv 2505.23579) describes a working
DNA-encoder-plus-LLM fusion that achieves 98.28% on a 290-datapoint KEGG disease-pathway benchmark versus 86–90% for
either modality alone, and a ~15% average lift on ClinVar variant-effect prediction. The architecture is elegant and
small: a learned `nn.Linear` projection maps DNA encoder embeddings (from NucleotideTransformer-500M or Evo2-1B) into
the LLM's token space at three special-token positions, with LoRA SFT followed by GRPO reinforcement learning for the
reasoning trace. No cross-attention, no custom layers, no exotic bridging — the fusion is BLIP-2 / LLaVA family applied
to genomics. But the code is CUDA-locked at the seams: `device_map='cuda'` is hard-coded in the model load, DeepSpeed
Stage 2 is required for training, vLLM is the inference backend, and the Evo2 path depends on NVIDIA Triton kernels.
Checkpoints are not yet released. This is Study for Phase 1 and potentially Phase 3, with a Phase 6 aspiration: once
MLX-native training infrastructure is established, the BioReason recipe (tokenizer extension

- linear projection + GRPO) is small enough to re-implement with NucleotideTransformer-500M and Qwen3-1.7B as the
  components that have working MLX ports. The re-implementation is more interesting than vendoring the upstream code
  would have been.

**deepsems is a narrow, validated, wrappable capability.** The DeepSeMS transformer (6+6 encoder-decoder, 512 hidden,
eight heads, ~80 LOC of model code) predicts SMILES structures for natural products from biosynthetic gene clusters
encoded as sequences of Pfam domain IDs. The headline number — 41.1% cryptic-BGC structure recovery versus PRISM 4's
8.9% and antiSMASH 7's 0.0% — is published in _Nature Computational Science_ (2026), which is a stronger provenance
signal than a preprint. The model is small (~50M parameters), PyTorch 2.1 base, no custom CUDA kernels visible in the
model code, and an MPS port is likely an afternoon of work. The value is not in the architecture — a vanilla
sequence-to-sequence transformer from 2017 — but in the curated MIBiG-derived BGC→SMILES training set and the
10-checkpoint ensemble that emerges from it. The right Linus move is a Phase 3 tool wrapper:
`predict_bgc_product(genbank_or_fasta)` that calls all 10 checkpoints, ranks SMILES by consensus count, and links output
to ChEMBL/PubChem records in KnowledgeBase. Phase 3 is gated on a reproducibility check of the headline numbers —
dataset leakage at 290 evaluation examples is a real risk — which belongs to Dan or a Worker with the paper in context.

---

## Patterns and modules worth lifting

**The protein-embedding-as-token pattern (Bacformer).** Treating a protein, a gene cluster, or any domain-typed
biological object as a single high-dimensional token in a second-stage transformer generalizes well beyond prokaryotic
genomes. The architectural recipe — embed at one resolution, then model relationships at a coarser resolution with a
separate transformer — is applicable anywhere Linus encounters a sequence of typed objects that have meaningful internal
structure. Chunks of papers embedded by a sentence encoder and then processed by a longer-context model is the direct
information-retrieval analog. This is a transferable design idea, not just a bio trick.

**Tokenizer extension via special tokens and linear projection (BioReason).** The three-token contract (`<|dna_start|>`,
`<|dna_pad|>`, `<|dna_end|>`) plus a single `nn.Linear` projection from encoder hidden size to LLM hidden size is a
minimal and portable recipe for adding a new modality to an existing instruct-tuned LLM without retraining the base. The
Linus Phase 6 bio-multimodal design should start from this pattern. The fact that it achieves near-parity with much more
elaborate fusion approaches (cross-attention bridges, full fine-tuning of both encoders) while remaining simple enough
to re-implement in a week is important evidence for the "delete before building" principle.

**GRPO for reasoning elicitation, not alignment (BioReason).** The KEGG result — LoRA SFT reaches 95.86%, GRPO lifts it
to 98.28% on the same backbone — demonstrates that reinforcement learning with verifiable rewards is a distinct training
signal from supervised imitation, even in a narrow domain. The interesting Phase 6 question is not "should Linus
fine-tune?" (yes) but "should the fine-tune include a GRPO pass on domain-specific reasoning traces?" BioReason is the
clearest evidence that this pass earns its cost in bio-specific question answering.

**Version-compatibility block plus introspect-on-failure (bioSkills).** Every bioSkills SKILL.md carries a
`## Version Compatibility` header pinning specific library versions and instructing the agent to handle `ImportError`
and `AttributeError` gracefully rather than retry blindly. This is the correct pattern for any environment where the
Bioconda toolchain and the conda env may differ from the environment the skill was authored in. When Linus builds its
own non-bio skills, this convention should be the template: pin versions, specify failure behavior, assume the
environment is heterogeneous.

**Domain-vocabulary tokenization (deepsems).** Representing a BGC as a sequence of Pfam domain IDs — a vocabulary of
~20k biological vocabulary tokens — and training a sequence-to-sequence model on that representation is a concrete
instance of the broader principle: when domain structure is well-defined, use it as the tokenization. The Pfam domain
vocabulary is to BGC analysis what SMILES tokens are to molecular generation. Linus's Phase 7 domain skills are likely
to encounter similar situations — sequences of GO terms, sequences of KEGG ortholog IDs, sequences of regulatory
elements — and the deepsems pattern shows this is tractable with a vanilla architecture if the vocabulary is right.

---

## Cross-references

**G8 (paper-qa, LAB-Bench, scientific-agent-skills, ether0).** bioSkills (G9) and scientific-agent-skills (G8) are
complementary, not competing. scientific-agent-skills has 135 skills covering general lab-science agent patterns;
bioSkills has 438 covering bioinformatics specifics. Together they produce approximately 573 skills as the inaugural
Phase 7 catalogue. The synthesis for G8 should be read alongside this document for the full picture of what Linus's
Phase 7 skills layer looks like on day one. LAB-Bench (G8) is the natural evaluation harness for measuring whether that
combined catalogue actually improves Worker performance on research tasks Dan cares about.

**Skills-and-practices synthesis (entrepreneurial surface).** The scientific-literature-intelligence opportunity named
in that synthesis as "Phase 1-ready" now has a concrete component specification: paper-qa (G8) for retrieval, bioSkills
(G9) for code-pattern priming, scientific-agent-skills (G8) for workflow scaffolding, KnowledgeBase for the indexed
corpus, and LAB-Bench (G8) as the internal quality bar. G9 is the domain anchor that makes this stack credible to a
biotech client in a way that a generic AI tool is not.

**BioReason and ether0 (G8 chemistry reasoning).** Both repos fuse a domain-specific encoder with a general LLM using a
linear projection and train the resulting model with GRPO to produce multi-step reasoning traces. ether0 does this for
molecular graphs and SMILES; BioReason does it for DNA sequences. They are the same architectural recipe in adjacent
sciences, which is a useful convergence signal. When Linus considers a Phase 6 bio-multimodal training run, these two
repos together define the template.

**Memory synthesis (scratchpad retention and episodic store).** The BioReason GRPO loop produces explicit reasoning
traces as training targets. If Linus ever trains on its own session transcripts, those traces — grounded in genomics
reasoning steps — are exactly the "durably recorded intermediate artifacts" the memory synthesis argues should be
first-class citizens. The two syntheses reinforce each other: the memory layer is what makes it possible to accumulate
bio-domain reasoning traces across sessions; BioReason is what those traces should look like.

---

## Phase-tagged implications

**Phase 1 (now).** Install bioSkills immediately via `./install-claude.sh --project <kb-or-research-repo>` against
KnowledgeBase or any active sequencing analysis project. This costs nothing, requires no Linus infrastructure, and
upgrades Claude Code's behavior on Dan's real bio tasks today. Concurrently: run the Bacformer Large MPS evaluation
spike — dedicated conda env, operon-prediction and strain-clustering tutorials end-to-end, wall-clock and memory
captured in `benchmarks/results/`. That measurement is the decision gate for Bacformer's Phase 7 candidacy. Read the
deepsems paper (_Nat. Comp. Sci._ 2026) for the cryptic-BGC evaluation design; a 290-example test set warrants scrutiny
before building a tool around the headline number.

**Phase 6 (fine-tuning).** BioReason is the template for Linus's Phase 6 bio-multimodal training run. The specific
configuration worth targeting is NucleotideTransformer-500M (HF-native, MPS-compatible) as the DNA encoder, Qwen3-1.7B
(existing MLX port) as the LLM, a linear projection layer, and LoRA SFT on KEGG disease-pathway and ClinVar VEP datasets
from the BioReason curation notebooks, followed by a GRPO pass. This is a re-implementation from the paper, not a port
of the CUDA code, and it is tractable on M1 Max at the 1.7B scale. The GRPO component should be treated as a Phase 6
experiment rather than a guaranteed deliverable — the SFT baseline should be measured first to determine whether the
reinforcement step earns its engineering cost.

**Phase 7 (skills and autonomy graduation).** Two actions:

First, add bioSkills as the inaugural domain skills bundle using selective `--categories` install keyed to project type.
The categories with the clearest immediate return for Dan's genomics work are `single-cell`, `variant-calling`,
`differential-expression`, `pathway-analysis`, and `clinical-databases`. Re-run the Bio-Task Bench against the Phase 2a
Worker model (Qwen2.5-Coder-32B or Mistral-7B) to test whether the local-model amplification hypothesis holds — the
biggest benchmark gain (+0.049) was on the weaker Codex 5.4-Mini, and if small local models get similar gains, the case
for bundling skills with every Linus instance strengthens considerably.

Second, if the Phase 1 Bacformer MPS evaluation succeeds, add `predict_from_genbank(path)` as a Phase 7 domain skill
that wraps the Bacformer Large checkpoint behind a single call returning contextual protein embeddings, predicted
operons, and nearest-genome hits. The `bacformer.pp` preprocessing pipeline (GenBank → ORF → ESM++ embedding → Bacformer
input) is already factored for this use.

**Phase 3 (knowledge and parallel agents).** If the deepsems paper-reproducibility check passes, implement the BGC tool
wrapper in Phase 3 alongside the tool-registry build-out: `predict_bgc_product(genbank_or_fasta)` calling all 10
ensemble checkpoints, ranking SMILES by consensus count and confidence score, and linking outputs to ChEMBL/PubChem if
those databases land in KnowledgeBase by Phase 4.

**Entrepreneurial surface (Phase 1-ready through Phase 3).** The biotech intelligence stack enabled by G9 plus G8 is not
a long-horizon aspiration. A working demonstration today is: Dan loads bioSkills against a client's question (a
competitor's BGC cluster, a variant-effect query, a pathway deconvolution problem), invokes Claude Code primed with the
relevant skills, and returns a structured analysis. The differentiation over a generic AI service is Dan's domain
literacy and the bioSkills catalogue. This is Phase 1-ready without any Linus infrastructure. Phase 3 extends it with
KnowledgeBase retrieval and Worker pipeline automation. Phase 7 adds Bacformer embeddings as a first-class analytical
signal alongside text retrieval.

---

## Open questions for Dan

**Bio-Task Bench Intermediate plateau.** Both agents land at 0.96–0.97 on Intermediate with or without skills loaded.
Three explanations are consistent with the data: the rubric is too coarse to detect skill-level gains at the top end;
the Intermediate tasks genuinely require multi-step biological judgment that in-context skill priming cannot provide; or
skills help on the wrong axis at Intermediate difficulty (API recall instead of reasoning). Which explanation you find
most credible changes how aggressively Linus should invest in the skills layer as an autonomy-graduation mechanism
versus investing in the reasoning-trace training path (BioReason GRPO template). Worth a 30-minute look at five
representative Intermediate tasks before deciding.

**Bacformer versus your existing operon callers.** You have 13 years of genomics pipelines. Where does a 300M
protein-context-aware encoder land relative to whatever you currently use for operon calling, MAG QC, or strain
clustering — replacement, ensemble member, or "interesting embedding signal to graft onto existing scoring"? The answer
determines whether Bacformer is a Phase 7 skill that surfaces results to Dan directly or a Phase 7 capability that feeds
upstream of Dan's own analyses.

**BioReason benchmark legitimacy.** The KEGG disease-pathway set covers 290 datapoints curated from KEGG relation
annotations. Is that benchmark actually meaningful to a working biochemist — does 98% accuracy imply genuine multi-step
pathway reasoning, or has the task been reduced to a pattern-matching exercise where memorization of KEGG annotation
structure dominates? A 30-minute read of the curation notebook in `data/` would resolve this before adopting the dataset
as a Linus evaluation target.

**deepsems cryptic-BGC reproducibility.** The 41.1% versus 8.9% headline is large enough to be either field-changing or
a test-set construction artifact. Do you want to read the _Nat. Comp. Sci._ paper critically yourself, or route that
review to a Worker with the paper in context and a structured rubric for checking train/test overlap?

**Pairing with scientific-agent-skills.** bioSkills (438) plus scientific-agent-skills from G8 (135) produces roughly
573 skills as the Phase 7 inaugural catalogue, with bioSkills handling the bioinformatics specifics and
scientific-agent-skills handling the broader lab-science agent patterns. Does that pairing feel right from your vantage
point, or are there overlapping skills categories between the two repos that would create confusion for a Worker
receiving both in context?

---

_Cross-references: G8 synthesis (paper-qa, LAB-Bench, scientific-agent-skills, ether0); skills-and-practices synthesis
(entrepreneurial surface, section 5); memory synthesis (scratchpad retention, episodic store); ROADMAP.md Phase 7
(Skills & Autonomy Graduation). Revisit when the Bacformer MPS benchmark lands in `benchmarks/results/`, when BioReason
checkpoints are released, and when the Phase 6 MLX training infrastructure is established._
