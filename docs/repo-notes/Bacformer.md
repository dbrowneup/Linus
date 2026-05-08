# Bacformer (`macwiatrak/Bacformer`)

## 1. Purpose and scope

Bacformer is a prokaryotic foundation model that treats a whole bacterial genome as an ordered sequence of proteins
along chromosomes and plasmids and learns contextualised protein embeddings conditioned on the rest of the genome. It
was pretrained on ~1.3M bacterial genomes (MAGs) and ~3B proteins, with checkpoints finetuned on ~40k complete genomes.
The Wiatrak et al. 2025 biorxiv preprint frames it as a model of "the functional syntax of bacterial evolution." For
Linus this is the first in-domain biology foundation model in the repo collection that maps directly onto Dan's genomics
expertise — a candidate Phase 7 domain skill, and a credible technical substrate for the "scientific literature
intelligence for biotech teams" entrepreneurial surface flagged in the skills synthesis.

## 2. Architecture summary

Two model families, both Transformer encoders that consume per-protein average pLM embeddings rather than raw amino-acid
sequences. **Bacformer base (26M params)**: 6 layers, 480-dim hidden, 8 heads, custom rotary self-attention
(`bacformer/modeling/modeling_base.py`); takes mean-pooled embeddings from `esm2_t12_35M_UR50D` as the per-protein
"token." **Bacformer Large (300M params, released 2025-01-20)**: ESM-C 300M geometry — 30 layers, 960-dim hidden, 15
heads — with RoPE, SwiGLU, and gradient checkpointing (`bacformer/modeling/modeling_large.py`); uses
`Synthyra/ESMplusplus_small` (ESM++) embeddings as input. Both models cap at 6000 proteins per genome
(`max_position_embeddings=6000`); a ~50k protein-cluster vocabulary supports the masked-genome-modeling head and a
contrastive auxiliary loss (`alpha_contrastive_loss=0.5`). A small set of special tokens
(`PAD/MASK/CLS/SEP/PROT_EMB/END`) plus a `contig_embedding` lets one model handle multi-replicon genomes (chromosome +
plasmids). Pretraining objectives include masked-genome (15% protein masking), causal/autoregressive next-protein
prediction, and a protein-family-token variant that generates sequences of Pfam-like family IDs rather than embeddings.
Eight HuggingFace checkpoints span MAG vs complete-genome and masked vs causal vs essential-genes-finetuned. Tooling: HF
Transformers (`>=4.38.2`), PyTorch (`>=2.5.1`), bf16 inference, optional `faesm[flash-attn]` for fast ESM. A sibling
repo `BacBench` provides the standardised downstream evaluation suite. Apache-2.0.

## 3. What's reusable in Linus

The ESM-C-shaped 300M `bacformer-large-masked-complete-genomes` checkpoint plus its zero-shot operon-prediction and
strain-clustering tutorials are immediately useful as a Phase 7 domain skill: "given a `.gbff`, return contextual
protein embeddings, predicted operons, and nearest-genome hits." The pipeline factors cleanly — `bacformer.pp`
(`preprocess_genome_assembly`, `embed_dataset_col`, `protein_seqs_to_bacformer_inputs`) handles GenBank → ORF →
ESM-embedding → Bacformer-input, which is exactly the kind of opaque-but-deterministic preprocessing a Linus tool can
wrap behind a single call. The protein-embedding-as-token pattern — pLM embed once, then a second-stage transformer
treats the genome as a sequence of those embeddings — is a transferable idea for any "sequence of objects" modality
Linus might host later (e.g. chunks of papers as embeddings into a longer-context model). Compared to **BioReason**,
which (per its README) couples a DNA LLM with reasoning to produce text rationales, Bacformer is purely
representational: no LLM, no chain-of-thought, just a frozen-or-finetunable encoder over genomes. Compared to nucleotide
DNA-LLMs in the broader landscape (DNABERT-2, Nucleotide Transformer, Evo / Evo2, Caduceus), Bacformer skips the
nucleotide layer entirely and operates above ORFs — much shorter effective sequences, much more biological structure
baked into the input, but useless for non-coding analysis or strain typing below the protein level.

## 4. What's inspiration only

The pretraining harness (`run_pretraining.py`, `trainer.py`, `data_reader.py`) targets multi-GPU CUDA clusters with
~1.3M genome shards; Linus will not retrain Bacformer. The protein-family-token causal model
(`bacformer-causal-protein-family-modeling-complete-genomes`) is a fascinating idea — generative "synthetic genomes" at
the family level — but is strictly a research curiosity, not an MVP feature. The `BacBench` evaluation harness in the
sibling repo is worth borrowing methodologically when Linus eventually defines its own bio benchmarks, but is not
infrastructure Linus consumes.

## 5. What's incompatible or out of scope

Apple Silicon viability is the load-bearing question and the answer is "mostly yes, with caveats." The README's install
path is heavily CUDA-flavoured (`pip install flash-attn --no-build-isolation`, `cuda-toolkit 12.1.0`, A100 GPU in the
PAO1 example), but flash-attn is listed only under the optional `[faesm]` extra; the base install pulls plain
`torch>=2.5.1` + `transformers`, both of which run on MPS. Inference on the 300M Large model in bf16 is ~600MB of
weights plus activations for sequences up to 6000 proteins — well within 32 GB unified memory, especially if ESM++
embedding is run in batches. The 26M base model is trivial. What will not work cleanly: faESM/flash-attn (no Metal
backend), so the "fast" embedding path falls back to vanilla HF — slower, but functional. Pretraining or large-batch
finetuning on M1 Max is not viable (Phase 6 territory at best, and only with the 26M model). Several dependencies are
heavyweight and slightly ill-fitting for a Linus subprocess (`scanpy`, `igraph`, `leidenalg`, `tensorboardx`,
`accelerate`); they pull in a non-trivial conda env that's worth isolating from `linus`. The PyPI package is at
`v0.2.0`, "Development Status :: 3 - Alpha" — single-maintainer, recent release, expect API churn.

## 6. Recommendation: **Study (with a path to Integrate at Phase 7)**

Bacformer is the most directly Dan-relevant repo in the bio group and worth a real evaluation, but not in the immediate
Phase 1–2 critical path. Concrete next step: in Phase 1's recon work, stand up Bacformer Large in a dedicated
`bacformer` conda env on the M1 Max, run the strain-clustering and zero-shot-operon tutorials end-to-end on MPS without
flash-attn, and capture wall-clock + memory in a `benchmarks/results/` JSON. If the M1 Max can do useful inference at
practical speeds (PAO1-sized genome in single-digit minutes is the bar), Bacformer becomes a Phase 7 skill: a Linus tool
that takes a GenBank path or an NCBI accession and returns contextual embeddings + downstream task outputs to either Dan
or a Worker LLM. If MPS inference is unworkable, demote to study material until Linus has a remote-GPU offload story.

Biosecurity note: per **DEC-0047** (SAFETY.md three-tier policy, accepted 2026-05-06), the
`bacformer-causal-protein-family-modeling-complete-genomes` checkpoint's gene-level / family-token generation is
explicitly Tier B — explicit Dan sign-off per invocation, logged in the audit trail, not agentic-executable without
approval. Read-only embedding / clustering / zero-shot-operon use of the masked checkpoints stays Tier A (standard
sandbox).

## 7. Questions for Dan

- **Which downstream task carries the most weight for you?** The eight checkpoints cover masked vs causal vs
  essential-genes-finetuned, MAG vs complete-genome. Operon ID, essential-gene prediction, and strain clustering all
  have ready tutorials — is one of these the natural first Linus skill, or is the contextualised-embedding output itself
  the primary product (i.e., upstream of your own KnowledgeBase analyses)?
- **Bacformer vs your existing pipelines.** You have 13 years of genomics tooling. Where does a 300M protein-aware
  encoder land relative to whatever you currently use for, say, operon calling or MAG QC — replacement, ensemble member,
  or "interesting embedding signal to graft onto existing scoring"?
- **The protein-family-token causal checkpoint.** `bacformer-causal-protein-family-modeling-complete-genomes` can
  generate plausible bacterial genomes at the family level. Is that something you want to expose as a Linus capability
  (synthetic-genome scaffolds, hypothesis generation), or strictly off-piste?
- **Differentiation from BioReason and the DNA-LLM landscape.** I argued in section 3 that Bacformer occupies a distinct
  slot (above-ORF, prokaryote-only, encoder-only, no reasoning head). Does that framing match your read, or is there
  overlap I'm missing — e.g., do you see Bacformer embeddings being plugged into a BioReason-style reasoning loop as a
  Phase 7+ composite?
- **Pretraining ambitions.** Phase 6 is fine-tuning on Apple Silicon. The 26M base model with a small LoRA on a bespoke
  corpus (e.g., your own genome collection) is plausibly tractable on M1 Max. Worth scoping as a Phase 6 candidate
  alongside the language-model fine-tunes, or strictly out of scope?

  _Partially resolved (S31, see [answered-questions.md](../questions/answered-questions.md)): Bacformer+DeepSeMS is
  a Phase 7 generalist × specialist pairing target. Phase 6 fine-tuning scope for the 26M base model not yet
  explicitly decided._
