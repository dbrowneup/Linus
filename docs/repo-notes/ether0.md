# ether0 (`Future-House/ether0`)

## 1. Purpose and scope

ether0 is FutureHouse's open release of a 24B-parameter scientific reasoning model for chemistry plus the infrastructure
to evaluate it: a benchmark dataset (`futurehouse/ether0-benchmark` on HF), the verifiable reward functions used to
train and grade it, and a small remote-rewards FastAPI server for the rewards that need a real chemistry oracle. The
model itself is post-trained from `mistralai/Mistral-Small-24B-Instruct-2501` via the loop described in arXiv
2506.17238: SFT on long-CoT traces, RL with verifiable rewards (RLVR) on focused task groups to produce per-task
"specialists," rejection sampling on specialist traces, then SFT + RLVR on the base again to fold specialists back into
one generalist. Crucially this repo does _not_ ship the training code — it ships the rewards, prompts, data models, and
dataset utilities. The training itself was done with NeMo-RL or HF TRL; ether0 contributes the verification layer that
makes RLVR work for a domain like chemistry. For Linus this is the most concretely useful artifact in the FutureHouse
stack from a Phase 6 perspective: a worked, published recipe for converting a 24B base into a domain reasoner using
rule + simulator rewards.

## 2. Architecture summary

Two installable packages in a `uv` workspace. `ether0` (the main package, ~1500 LOC of Python plus two `.bloom` filters)
is RDKit-heavy: every reward function operates on parsed SMILES, with `is_reasonable_molecule` gating outputs through
valence sanitization, counter-ion checks, ring-system checks via a pre-built bloom filter (`rings.bloom`), and a
REOS-style fingerprint check (`fingerprints.bloom`) plus a hard-coded `BAD_SMARTS_PATTERNS` list (peroxides, hydrazines,
polynitros, long carbon chains). The eleven reward functions in `EVAL_FUNCTIONS` cover the chemistry task matrix:
`valid_mol_eval` (SMILES completion), `product_eval` (forward synthesis exact match or Tanimoto), `rxn_eval` and
`str_eval` (IUPAC naming with Unicode-normalized comparison), `formula_eval` (molecular-formula match plus Tanimoto
threshold of 0.7), `functional_group_eval` (formula plus exmol functional-group set inclusion), `oracle_solubility_eval`
(constraint-satisfying molecule design with scaffold/group/Tanimoto constraints, graded against a ±0.5 log-S window),
`oracle_rxn_eval` (forward reaction with regex sanity check, purchasable-reactant verification, and ground-truth product
match), and `caption_eval`. Rewards are mostly binary 0/1 with optional `soft` mode for partial credit — the
verifiable-rewards regime in its strict form. The `ether0.remotes` package wraps the oracles that can't be a pure
function: a Molecular Transformer (USPTO 480k checkpoint, OpenNMT, ~400 MB PyTorch), `KDESol` for solubility, and
`molbloom` for purchasability. It exposes them behind a bearer-token FastAPI service (`ether0-serve`) that the
in-process rewards call via `httpx` clients (`fetch_forward_rxn`, `fetch_solubility`, `fetch_purchasable`). Rich
`RewardReason` enum tags every failure mode (`INVALID_MOL`, `FAILED_RING_CHECK`, `PRODUCT_IS_REACTANT`,
`NOT_PURCHASABLE`, …) into per-example metadata so RL training can stratify failures.

## 3. What's reusable in Linus

The reward-function library and the `RewardFunctionInfo` data model are directly importable today for any chemistry
agent in the KnowledgeBase or future Linus skills work — `pip install git+https://github.com/Future-House/ether0.git`
and you have RDKit-backed verifiers for SMILES validity, formula match, functional-group containment, Tanimoto
similarity, and forward-reaction sanity, complete with a reason taxonomy. The `is_reasonable_molecule` chain
(REOS-bloom + ring-bloom + bad-SMARTS + counter-ion split) is a small and battle-tested filter that any
chemistry-adjacent generation tool should reuse instead of reinventing. More importantly, the **pattern** is the
artifact: a clear separation between (a) a frozen verifier that emits binary or near-binary rewards and (b) a base model
that gets RLVR'd against it, with rejection sampling between specialist and generalist passes. That recipe transfers
cleanly to biology — variant effect prediction (verifier: ClinVar pathogenicity match), protein-language tasks
(verifier: ESMFold pLDDT or structural alignment score), gene-regulatory reasoning (verifier: tissue-specific expression
direction). The Phase 6 fine-tuning roadmap can cite ether0 as an existence proof that 24B + RLVR with domain-specific
verifiers beats much larger general models on focused scientific tasks. Compared to **`aviary` and `ldp`** in the
FutureHouse training stack (which provide the agent environment and the gradient-based RL loop respectively), ether0 is
what fills in for the reward signal — `aviary` and `ldp` are domain-agnostic and would happily host an ether0-style
training run; ether0 is the chemistry-shaped piece that plugs in.

## 4. What's inspiration only

The 24B model itself is interesting reading on what RLVR can buy a single-domain reasoner, but at Mistral-Small-24B
scale it is at the upper edge of what fits comfortably on the M1 Max — Q4 quant lands around 14 GB, which leaves room
for context but not for serving alongside other workers. The published weights are worth pulling and benchmarking once
Phase 1 is settled; production use as a Linus worker is unlikely. The MolTrans server and `KDESol` oracle are
chemistry-only. Compared to **BioReason** (G9, DNA reasoning over Evo2 + Qwen3-4B with GRPO over MCQ accuracy), ether0
is the more mature template: BioReason is one published RL setup with one verifier, while ether0 is eleven verifiers
spanning a full task taxonomy with the simulator/oracle separation made explicit. If Linus ever attempts a Bio reasoner,
the architectural model to copy is ether0's, not BioReason's.

## 5. What's incompatible or out of scope

The `ether0-serve` remote stack pulls OpenNMT and a 400 MB MolTrans checkpoint hosted on Google Drive — workable but
fragile, and the OpenNMT line of `pyonmttok`/`OpenNMT-py` has CUDA assumptions in places that can bite on Apple Silicon.
The MolTrans inference itself runs on CPU/Metal-PyTorch fine for evaluation, just not at training-loop speeds. The
training code is _not_ in this repo — adopting the recipe means standing up NeMo-RL or TRL ourselves, neither of which
is Apple-Silicon-native (NeMo-RL is CUDA-bound; TRL works on MPS but is not optimized for it). This is the major gap:
ether0 hands you the verifier and the recipe, but the actual RLVR training run for a Linus-specific domain model is on
us, and it is the place where pmetal would have to step in (pmetal-trainer ships GRPO and DAPO, which are the relevant
losses).

## 6. Recommendation: **Study**

Pull and read the rewards module and the paper (arXiv 2506.17238). Optionally `pip install ether0` into the linus env
and run the benchmark example against a local Ollama model to confirm the `EVAL_FUNCTIONS` API works the way the README
claims — it's a one-afternoon exercise and produces a real number. Do not adopt as a runtime dependency in Phase 2;
revisit in Phase 6 when fine-tuning becomes active, at which point the ether0 recipe becomes the most detailed published
template for "post-train a mid-size open base into a domain reasoner via verifiable rewards." If a biology variant of
this is ever attempted, ether0's reward-taxonomy and reason-enum design should be copied wholesale.

## 7. Questions for Dan

1. **Biology verifier candidates.** The ether0 trick is that chemistry has cheap rule-based and simulator-based oracles
   (RDKit, MolTrans, KDESol, molbloom). Which biology subdomains do you think have analogously cheap verifiers — BLAST
   identity for sequence design, ESMFold pLDDT for protein design, tissue-eQTL direction-of-effect for variant
   reasoning? A short list would shape Phase 6 materially.
2. **Mistral-Small-24B as base.** Ether0 chose Mistral-Small-24B specifically. For a Linus bio reasoner, is 24B the
   right starting size given the 32 GB constraint, or do we deliberately go smaller (Qwen2.5-7B / Mistral-7B) to keep
   RLVR experiments cheap and trade specialist quality for cycle time?
3. **Specialist-then-generalist pattern.** The ether0 paper's RL loop runs specialists per task group, rejection-samples
   their traces, and re-SFTs into a generalist. Worth replicating verbatim for a Linus domain model, or is the
   multi-pass orchestration overhead prohibitive on M1 Max — i.e. should we collapse to single-stage RLVR?
4. **Reward-function design discipline.** Most of ether0's verifiers return strict 0/1, with `soft` Tanimoto only as a
   fallback. Do you agree with the design bet that strict binary rewards beat dense shaped rewards for RLVR, or do you
   want partial-credit shaped rewards as the default for early bio experiments where the verifier itself is noisier?
5. **Adopting `ether0.rewards` in KnowledgeBase.** Some KnowledgeBase chemistry tooling could use `valid_mol_eval` and
   `is_reasonable_molecule` as guardrails for any LLM-generated SMILES today — worth a small dependency, or keep
   KnowledgeBase free of FH-stack imports for now?
