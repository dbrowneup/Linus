# BioReason (`bowang-lab/BioReason`)

## 1. Purpose and scope

BioReason is the reference implementation of "Incentivizing Multimodal Biological Reasoning within a DNA-LLM Model"
(arXiv 2505.23579, Fallahpour et al., Vector Institute / UHN / Toronto). Its claim is the first deep integration of a
DNA foundation model with a general-purpose LLM such that the LLM does not just classify a sequence but reasons
multi-step over genomic input — e.g., on a 290-datapoint KEGG-derived benchmark it lifts disease-pathway-prediction
accuracy from 86% (NT-500M alone) and 90% (Qwen3-4B alone) to 98.28% with the Evo2-1B + Qwen3-4B + GRPO stack, and
delivers a roughly 15% average gain on ClinVar variant-effect prediction over either modality alone. A follow-up
(BioReason-Pro, bioRxiv 2026.03.19.712954) swaps the DNA encoder for ESM3 protein embeddings and adds GO-GPT + RL to
generate protein-function annotations preferred over UniProt 79% of the time, but that work lives in a separate repo.
For Linus this is the closest existing match to Dan's PhD substrate (genomics + computational biology) and is the most
defensible Phase 3+ "Linus does what hosted Claude can't" story.

## 2. Architecture summary

The core class is `bioreason.models.dna_llm.DNALLMModel` (407 lines). Two encoders run side-by-side: a DNA model —
either `InstaDeepAI/nucleotide-transformer-v2-500m-multi-species` loaded as `AutoModelForMaskedLM`, or Arc Institute's
`Evo2` (1B base, with a configurable hidden layer like `blocks.20.mlp.l3` tapped for embeddings) — and a text LLM, in
practice `Qwen/Qwen3-1.7B` or `Qwen/Qwen3-4B`, loaded as `AutoModelForCausalLM`. Three special tokens (`<|dna_start|>`,
`<|dna_pad|>`, `<|dna_end|>`) are added to the LLM tokenizer; at forward time the DNA encoder produces last-hidden-state
embeddings, a single learned `nn.Linear(dna_hidden_size, text_hidden_size)` projection (`self.dna_projection`) maps them
into the LLM's embedding space, and the projected DNA-token embeddings are spliced into the text-embedding sequence at
the `<|dna_pad|>` positions. There is no cross-attention bridge — it is the simplest possible "embed and prepend" fusion
of the BLIP-2/LLaVA family, which makes the architectural delta refreshingly minimal. Training is supervised LoRA
fine-tuning of the LLM (and optionally the DNA encoder) via PEFT + DeepSpeed Stage 2, followed by GRPO reinforcement
learning (`bioreason/trainer/grpo_trainer.py`, `train_grpo.py`) for the reasoning-trace step. Datasets are KEGG
disease-pathway questions and ClinVar coding / non-SNV variants curated as Jupyter notebooks under `data/`. The shell
recipes (`sh_train_dna_qwen.sh`) target SLURM with `--gpus=1 --mem=128gb`, ~12-hour walltime per config; inference uses
vLLM (`dna_vllm.py`, `eval_kegg_dna_vllm.py`).

## 3. What's reusable in Linus

The architectural pattern is what's reusable, not the code. The "tokenizer-extension + linear projection from a
specialist encoder into a general LLM" recipe is exactly what Linus would need for a future Phase 6 fine-tune that lets
a Worker (Qwen2.5-Coder, or a Linus-trained successor) accept FASTA / VCF / GenBank as first-class context rather than
as a string. The `<|dna_start|>` / `<|dna_pad|>` / `<|dna_end|>` token contract is portable; the DLProcessor pattern of
wrapping HF tokenizers to handle a second modality is portable; the choice to use NucleotideTransformer-500M (small,
HF-native, easy to port to MLX) over Evo2 (1B, custom CUDA kernels) is the right call for the 32 GB UMA budget. KEGG
disease-pathway and ClinVar VEP datasets and the curation notebooks are directly reusable as Phase 1 benchmark tasks for
"Dan-relevant evaluation" — they are exactly the kind of question Linus should be measured on, regardless of whether the
BioReason model itself is ever the one answering.

## 4. What's inspiration only

Compared to **Bacformer** (the other bio-FM in this group), BioReason is a different beast. Bacformer is
sequence-to-embedding for bacterial genomes — encoder only, useful as a featurizer for downstream tasks. BioReason is
sequence-plus-question-to-reasoning-trace, which is the strictly harder modality and the one closer to Dan's actual
workflow (interpreting a variant, walking a pathway, hypothesizing mechanism). Compared to **ether0** (G8 chemistry
reasoning model), the kinship is closer: both fuse a domain encoder with an LLM and use RL (GRPO here, also ether0) to
incentivize multi-step traces, but ether0 operates over molecular graphs / SMILES whereas BioReason operates over DNA
nucleotides — the same recipe in two adjacent sciences. The most interesting inspiration is the GRPO-for-reasoning-trace
loop: it's a concrete, working example of using RL not just for preference alignment but for _eliciting_ domain
reasoning that supervised fine-tuning alone underdelivers (98.28% vs 95.86% on KEGG with the same backbone). That maps
directly onto Phase 6 / Phase 7 if Linus ever pursues a "reasoning-trained Linus" rather than a generic instruct
fine-tune.

## 5. What's incompatible or out of scope

This is a CUDA codebase and it is not subtle about it: `pyproject.toml` requires `deepspeed`, `bitsandbytes`,
`trl[vllm]`, and `qwen-vl-utils`; `dna_llm.py` hard-codes `torch.device("cuda" if torch.cuda.is_available() else "cpu")`
with `device_map="cuda"` for the LLM load; the Evo2 path imports `from evo2 import Evo2` which depends on
NVIDIA-specific Triton kernels. SLURM scripts request 128 GB RAM and 1 GPU per run. Training the published configs on M1
Max is not feasible — a Qwen3-4B + Evo2-1B + LoRA + GRPO run that takes 12 hours on an A100 is not coming back inside
the heat death of the universe on 32 GB UMA, and DeepSpeed Stage 2 + vLLM both lack Metal support. Inference of the
published checkpoints (when released — `## Checkpoints` says "We will release the checkpoints soon!") might be
tractable: NT-500M is a HuggingFace BERT-like that runs fine on MLX or MPS, Qwen3-1.7B/4B has working MLX ports, and the
projection layer is a single Linear. But the wrapper code would need to be substantially rewritten to remove the
DeepSpeed / vLLM / bitsandbytes path. Bottom line: as a binary to run, this needs porting work; as a paper to
re-implement, it is small enough to be tractable.

## 6. Recommendation: **Study**

Read the paper (arXiv 2505.23579) end-to-end — it is short and Dan's domain. Skim `bioreason/models/dna_llm.py` for the
fusion pattern. Add the KEGG-derived disease-pathway prediction set and the ClinVar coding / non-SNV VEP sets to the
Phase 1 `benchmarks/dan_tasks/` shortlist as bio-domain evaluation, since they are exactly the questions Linus should be
graded on. Do not attempt to run training or even native inference on the M1 Max in Phase 1 — wait for the public
checkpoints, then in Phase 3 or 6 evaluate whether a port to MLX (NT-500M + Qwen3-1.7B is the smallest configuration and
is the realistic target) is worth the engineering. The far-better Linus play is "use the BioReason architecture as a
template for a Linus-native bio-multimodal Worker," not "vendor BioReason's CUDA stack."

The BioReason-Pro follow-up (bioRxiv 2026.03.19.712954) is the more direct Linus prior art: per CLAUDE.md §"Typed
structured prediction for biology skills" (resolved 2026-05-06, S25), every Linus biology skill that produces a
predictive output should adopt the BioReason-Pro shape — typed structured result wrapping a free-text `rationale` field.
Per **DEC-0047** (biosecurity tier policy), BioReason-Pro residue-level outputs sit in Tier A (standard sandbox); only
gene/whole-genome generation paths escalate to Tier B/C.

## 7. Questions for Dan

1. **KEGG benchmark legitimacy.** The 290-datapoint KEGG disease-pathway set is the headline result. Is that benchmark
   actually meaningful to a working biochemist — does getting 98% on it imply useful pathway reasoning, or has it been
   reduced to a multiple-choice exercise where memorization of KEGG itself dominates? Worth a 30-minute look at the
   curation notebook before adopting it as a Linus eval target.
2. **Evo2 vs NucleotideTransformer.** For Linus's Phase 1 benchmark suite, NT-500M is the M1-Max-tractable choice and
   Evo2-1B almost certainly is not. But the paper shows Evo2 wins on VEP non-SNV. Are you willing to leave the harder,
   more interesting variant-effect questions on the table to stay on a portable encoder, or is Evo2 worth the porting
   fight in Phase 6?
3. **DNA-LLM fusion vs RAG.** BioReason's pitch is that the LLM literally consumes DNA embeddings as context tokens. The
   obvious Linus alternative is a KnowledgeBase RAG over annotated genomic resources (KEGG, ClinVar, UniProt, Ensembl) +
   a generic Qwen — no fusion, no fine-tune. Do you have a prior on which path is more promising for Phase 3?
4. **GRPO for reasoning, not alignment.** The repo's `train_grpo.py` uses GRPO to elicit reasoning traces, lifting KEGG
   from 95.86% to 98.28%. That is a concrete protocol Linus could adopt in Phase 6 for a "reasoning-trained Linus"
   rather than a generic instruct fine-tune. Worth raising to a Phase 6 candidate experiment now, or premature?
5. **BioReason-Pro relevance.** The follow-up swaps DNA encoder for ESM3 protein embeddings + GO-GPT to predict protein
   function — closer to wet-lab interpretation. Should this group's "study target" be BioReason or BioReason-Pro?
