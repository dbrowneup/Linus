# deepsems (`lab-of-biochemai/DeepSeMS`)

## 1. Purpose and scope

DeepSeMS — "Deep Secondary Metabolite Sequencing", _not_ "deep semantics" — is a transformer that predicts the chemical
structure (SMILES) of natural products produced by a biosynthetic gene cluster (BGC), given the BGC as a sequence of
Pfam protein-domain identifiers. Inputs come from antiSMASH (GenBank) or DeepBGC (FASTA); outputs are top-ranked SMILES
with a model-confidence score and a 10-fold consensus count. Published in _Nature Computational Science_ (Xu, Yang, Zhu
et al., 2026, doi 10.1038/s43588-026-00983-1) with the headline that on cryptic BGCs DeepSeMS hits 41.1% structure
recovery vs. PRISM 4's 8.9% and antiSMASH 7's 0.0%. The repo ships training script, prediction script, the trained
10-model ensemble (checkpoints downloaded from Figshare, not in git), the Pfam+SMILES vocabularies, and a Docker image
for inference. Strictly NVIDIA in its as-shipped form: the conda env pins `torch==2.1.0` plus the full `nvidia-cu12-*`
stack and the README's preferred hardware is "CUDA 12.0, RTX 4090, 24 GB VRAM".

## 2. Architecture summary

A vanilla seq2seq transformer — `nn.Transformer` from PyTorch, six encoder layers, six decoder layers, eight heads,
`d_model=512`, dropout 0.1 (`models/Transformer.py`, ~80 LOC). Source vocabulary is Pfam domain IDs (a fixed list in
`vocabs/bgc_features_vocab.csv`, ~20k entries); target vocabulary is a SMILES character/token vocabulary
(`vocabs/smiles-vocab.pt`). Training data are BGC→SMILES pairs from MIBiG-style curated databases; SMILES enumeration is
used for augmentation (default 100× amplification, two modes: structural-feature-aligned vs. randomized;
`data_processing.py`). Training loop in `train.py` is straightforward AdamW with early stopping at patience 10,
batch_size 32, 500 epochs/fold, ten independent folds producing `checkpoint0.ckpt … checkpoint9.ckpt`. Inference
(`predict.py`) runs all 10 checkpoints, ranks output SMILES by predicted score and cross-fold consensus count.
Architecturally this is the same recipe as molecular machine-translation models from 2018-2020 (e.g. Schwaller's
Molecular Transformer for reaction prediction) — what's new is the input modality (Pfam-tokenized BGCs, not reactant
SMILES) and the curated BGC→product training set, not the network. Reported training cost is 5–6 days on a single 4090.

## 3. What's reusable in Linus

For Linus's "scientific literature intelligence" Phase-1+ direction, DeepSeMS is more interesting as a _capability
wrapper_ than as code. The natural KnowledgeBase-tied tool is `predict_bgc_product(genbank_or_fasta)` — drop in a BGC,
get back ranked SMILES plus RDKit-computed molecular properties (`calculate_molecular_properties.py` already does
LogP/MW/QED/SAscore via RDKit's SA*Score Contrib). That's a high-value worker tool for any genomics-adjacent prompt and
maps cleanly onto Phase 3's tool-registry surface. The 10-checkpoint ensemble (~hundreds of MB once downloaded from
Figshare) plus a thin Python wrapper is all that's needed. Compared to G9 siblings: **Bacformer** is a microbial-genome
foundation model (broad embeddings, many downstream tasks); **BioReason** is a reasoning model over biological
literature; DeepSeMS is the narrowest and most \_executable* — one input modality, one output modality, one number that
matters (structure recovery rate). It is also notably narrower than ether0 (G8): ether0 reasons over arbitrary
chemistry; DeepSeMS does one specialized translation. For a Linus tool that has to actually return useful results behind
a wrapper, narrow-and-validated beats broad-and-vibing.

## 4. What's inspiration only

The architecture itself (a 2017-vintage `nn.Transformer` from PyTorch, ~80 LOC of model code) is not novel and is not
something Linus needs to study. The _problem framing_ is interesting: representing a biological object (a BGC) as a
sequence of Pfam tokens — a domain-vocabulary tokenization — and translating to chemistry, is exactly the kind of
"compose two well-tokenized worlds with a transformer" pattern that Dan's domain-tool roadmap (Phase 7 skills, plus the
"scientific literature intelligence" entrepreneurial direction) will repeatedly encounter. The data-augmentation
strategy (SMILES enumeration with structural-feature alignment) is also worth knowing about for any future Linus
fine-tune that touches molecules.

## 5. What's incompatible or out of scope

The shipped artifact is CUDA-only on paper. In practice, PyTorch 2.1 has MPS support and the model is small (~50M
parameters in the standard config), so an `torch.device("mps")` swap and pruning the `nvidia-*` pip dependencies should
make inference run on Dan's M1 Max — but this is untested by upstream and HMMER + Pfam scanning add a non-GPU
preprocessing dependency (`hmmer=3.3.2` from bioconda; ~1.5 GB Pfam-A.hmm download from Figshare). Training the full
10-fold ensemble at 5–6 days/4090 is not a serious option on the M1 Max; if customization is needed, fine-tuning single
checkpoints from the published weights is the only practical path. The Docker image is Linux/CUDA-only and should be
ignored on macOS in favor of the conda route. The model is also tightly coupled to its specific Pfam vocabulary — adding
a domain that wasn't in training requires a re-tokenization plan, not a config change.

## 6. Recommendation: **Study** (with a clear path to a Phase 3 tool wrapper)

This is not infrastructure Linus integrates; it's a domain capability Linus wraps. Read the _Nat. Comp. Sci._ paper to
verify the cryptic-BGC numbers and confirm the 41% recovery claim isn't dataset-leakage flavored. If they hold up,
schedule a Phase 3 task: download checkpoints + Pfam from Figshare, port `predict.py` to MPS, smoke-test on the provided
`antiSMASH_example.gbk` and verify SMILES output matches the published web server, then wrap as a Linus tool with
KnowledgeBase-linked outputs (structure → linkable to ChEMBL/PubChem if those land in KB). Keep it Study-level until the
MPS port and reproducibility check succeed; promote to Integrate once a worker-callable tool exists.

## 7. Questions for Dan

- **Cryptic-BGC reality check.** The headline (41.1% structure recovery vs. 8.9% / 0.0% for PRISM 4 / antiSMASH 7) is
  large enough to be either field-changing or a benchmark-construction artifact. Worth a careful read of the paper's
  test-set design before promising a Linus tool — do you want to do that read, or have it queued for a Worker?
- **Scope of "molecular properties" in your work.** `calculate_molecular_properties.py` covers LogP / MW / TPSA / QED /
  SAscore via RDKit — drug-likeness flavored. Your biochemistry interest is genomic/regulatory, not drug-discovery. Is
  downstream filtering on these properties useful to you, or is the SMILES alone the deliverable?
- **MPS port effort budget.** Porting `predict.py` to `torch.device("mps")` is probably an afternoon (model is 50M
  params, no custom CUDA kernels visible). Is that worth a Phase-3 spike, or hold off until the broader KnowledgeBase +
  worker-tool plumbing is up?
- **Pfam dependency.** Running DeepSeMS requires HMMER + Pfam-A.hmm (~1.5 GB) installed and indexed. Is bundling Pfam
  inside KnowledgeBase acceptable, or should the BGC-prediction tool assume Pfam is a separately-managed KnowledgeBase
  artifact?
- **Sibling comparison priority.** Of {DeepSeMS, Bacformer, BioReason, bioSkills}, DeepSeMS is the most _packaged_
  (paper, weights, web server, Docker, ensemble). Should it be the G9 entry that gets promoted to a Phase 3 tool first
  as a forcing function for the whole "biology-domain Linus tool" pattern, or is one of the others a better leading
  example?
