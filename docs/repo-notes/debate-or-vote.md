# debate-or-vote (`deeplearning-wisc/debate-or-vote`)

## 1. Purpose and scope

debate-or-vote is the **research-code reference implementation** for the NeurIPS 2025 Spotlight paper
[_Debate or Vote: Which Yields Better Decisions in Multi-Agent Large Language Models?_](https://arxiv.org/abs/2508.17536)
by Hyeong Kyu (Froilan) Choi, Xiaojin (Jerry) Zhu, and Yixuan (Sharon) Li (UW-Madison, Sharon Li's lab). It is a small
(~332 KB, ~14 Python files, ~700 LoC of core) MIT-licensed PyTorch + HuggingFace `transformers` codebase whose only
purpose is to run controlled head-to-head experiments comparing **multi-agent debate (MAD) — every agent re-prompted
each round with all peers' opinions — against simple majority voting** on a battery of benchmark Q&A datasets
(arithmetics, GSM8K, HellaSwag, CommonSenseQA, MMLU formal-logic, MMLU pro-medicine, HH-RLHF, CNN-DailyMail). The
headline finding of the paper — and the load-bearing reason this repo is in the Linus corpus — is that **simple voting
matches or outperforms multi-round debate across most settings**, which inverts the prevailing assumption that more
inter-agent coordination is always better. The implication for Linus's Phase 3 spawner (DEC-0050, DEC-0051) is direct:
when fanning out N Workers on a question that admits a structured answer, the cheapest-and-best-as-the-evidence-shows
coordination is to let each Worker think independently and aggregate with a heuristic (vote, median, or argmax over
typed fields), not to spend N × R additional LLM calls re-prompting each Worker with peers' responses every round.

debate-or-vote is **not** a framework, harness, or library. It is single-purpose research code: one entry point
(`src/main.py`), one inference engine (`src/model/model_utils.py::engine` — a thin wrapper around HF `model.generate()`
with batched input), one evaluator module (`src/evaluator.py` — regex-based answer extraction + majority-vote
tie-break), and per-dataset loaders under `src/data/`. It targets CUDA on Linux (`environment.yaml` pulls
`torch==2.7.1+cu128` and the full `nvidia-cu12*` stack; the prefix line points at
`/nobackup-fast/froilan/miniconda3/envs/venv`); there is no Apple Silicon support, no test suite, no recovery /
checkpointing, no MCP / OpenAI-compat layer, no CLI beyond argparse. The relevance to Linus is **the algorithmic result,
not the artifact**. Lift the heuristic-aggregation-vs-per-step-debate framing into the Phase 3 spawner spec; do not
vendor or fork the code. Per the [g7-harnesses](../syntheses/repo-clusters/g7-harnesses.md) synthesis line ~195: "the
research-code reference implementation of this pattern; it is a concrete candidate for the Phase 3 spawner Worker
fan-out coordination model."

## 2. Architecture summary

The repo is intentionally flat. Top level: `README.md`, `environment.yaml` (Python 3.10 + CUDA 12.8 conda env named
`venv` with PyTorch, `transformers==4.55.2`, `accelerate`, `peft`, `datasets`, `langchain` for some loaders,
`rouge_score` for summarization eval, `sentence-transformers`), `src/`, and `scripts/`. There is no `setup.py`,
`pyproject.toml`, test directory, GitHub Actions config, Dockerfile, or sub-package `__init__.py` discipline — it runs
as `python src/main.py <args>` from the repo root with `token` (a HuggingFace API token in a single-line file) sitting
next to `main.py`.

The **entry point** is `src/main.py`. The argparse surface declares the experiment matrix in twenty arguments split into
four groups: environment (`--seed`, `--out_dir`), data (`--data_dir`, `--data` — one of `arithmetics`, `gsm8k`,
`hellaswag`, `pro_medicine`, `formal_logic`, `csqa`, `hh_rlhf`, `cnn_daily` — `--data_size`, `--split`), agent
(`--num_agents`, `--multi_persona`), model (`--model` — one of `llama3.1-8b`, `qwen2.5-7b`, `qwen2.5-32b` per
`model/model_utils.py::model_dirs`, `--model_dir`, `--memory_for_model_activations_in_gb`), and debate
(`--debate_rounds`, `--sparse`, `--centralized`, `--solver` ∈ {`vote`, `debate`}, `--bae` for "base answer extractor",
`--cot` for chain-of-thought instruction suffix, `--alpha`, `--max_num_agents`). The `--sparse` and `--centralized`
flags are mutually exclusive topology selectors; absence of both means decentralized full-mesh.

The **debate loop** in `main()` runs `args.debate_rounds + 1` rounds (round 0 = independent initial opinions, rounds
1..R = debate revisions). Each round: (1) build per-agent messages via `get_new_message`; (2) call the shared `engine`
to batch-generate `args.num_agents` responses through one HF `model.generate()` call with
`do_sample=True, temperature=1.0, top_p=0.9, max_new_tokens=512`; (3) call the dataset-appropriate evaluator
(`evaluate_arithmetics` / `evaluate_mcq` / `evaluate_gen` for CNN-DailyMail summarization, plus `bae` variants); (4)
record per-round responses, per-agent final answers, the aggregated "debate answer", and a correctness flag against
ground truth; (5) append a JSONL record to
`out/history/<dataset>_<size>__<model>_N=<N>_R=<R>[_SPARSE|_CENTRAL][_BAE][_HETERO].jsonl`. After all questions are
processed, mean accuracy per round is appended as a TSV line to `out/logs.tsv`. The output schema is round-indexed so a
downstream notebook can plot accuracy as a function of debate-round count for any (dataset, topology, persona-set,
model) cell.

The **three coordination topologies** are implemented in
[`get_new_message`](https://github.com/deeplearning-wisc/debate-or-vote/blob/main/src/main.py) (`src/main.py` lines
72-134):

- **Decentralized full mesh** (default, `not args.centralized and not args.sparse`). Each agent's round-r prompt
  contains all N-1 peers' round-(r-1) responses verbatim, plus its own previous response, plus the original question.
  Prompt size grows linearly in N; total tokens per round grow as O(N²) (N agents × O(N) tokens of peer context each).
  This is the canonical "multi-agent debate" of the [Du et al. 2023](https://arxiv.org/abs/2305.14325) /
  [DyLAN](https://arxiv.org/abs/2310.02170) line.
- **Sparse ring** (`--sparse`). Each agent sees only its two ring-adjacent peers (`agents[(i-1) % N]` and
  `agents[(i+1) % N]`) plus its own previous response. Prompt size is constant per agent regardless of N; total tokens
  per round are O(N). This is the topology Liang et al. (and the broader sparse-MAD literature) argued for on cost
  grounds.
- **Centralized star** (`--centralized`). Agent 0 sees all N-1 peers (one hub-and-spoke read); agents 1..N-1 each see
  only agent 0's response. Total prompt tokens per round are O(N) but information flow is asymmetric: only agent 0 has
  the full picture. The aggregation step then uses **only agent 0's answer**
  (`central_agent_response = {list(agent_responses.keys())[0]: list(agent_responses.values())[0]}`) — the rest of the
  agents are effectively decoration once the central agent has digested their opinions.

The **aggregation step** ("the heuristic that the debate-or-vote paper compares debate against") lives in
`src/evaluator.py` and is the load-bearing simplicity of this repo. For arithmetic and GSM8K, `evaluate_arithmetics`
extracts each agent's final number via `re.findall(r"\{(.*?)\}", response)[-1]`, takes the last brace-delimited
substring, strips `final answer:`, parses as float, rounds to one decimal, and takes the **majority vote with random
tie-break** (`random.choice(most_common)`). For MCQ datasets, `evaluate_mcq` does the same with letter answers (`(A)`,
`(B)`, ...). For CNN-DailyMail summarization, `evaluate_gen` picks the summary with highest ROUGE-L against ground truth
— a "best-of-N" ranker rather than a vote, since summaries are not categorical. The `bae` ("base answer extractor")
variants (`base_evaluate_arithmetics`, `base_evaluate_mcq`) skip the brace-format requirement and parse the last numeric
token / last `(X)`-shaped match in the response — fallback parsing for models that don't reliably follow the
brace-format instruction.

The critical design choice is that the **vote is computed every round, regardless of whether the experiment is "vote" or
"debate"**. The aggregated `debate_answer` from the round-0 vote is recorded as the round-0 result; the round-r vote is
the round-r result. So "vote" in the paper's framing corresponds to **round 0 only** (no debate rounds, just N
independent agents and a vote), while "debate" corresponds to **round R** with all R rounds of inter-agent re-prompting
before the final vote. The paper's experimental design is therefore "compare round-0 accuracy (pure vote) against
round-R accuracy (debate + vote) on the same N agents" — and the headline result is that round 0 is competitive or
better in most cells.

The **`--multi_persona` heterogeneous-agent mode** (the `heterogeneous.sh` script) replaces the uniform "You are an AI
assistant" system prompt with a per-agent role drawn from a 14-persona library (Mathematician, Economist, Psychologist,
Lawyer, Doctor, Programmer, Historian, plus four code-writing personas — Python Assistant, Algorithm Developer, Computer
Scientist, Coding Artist, Software Architect — directly cited as borrowed from
[DyLAN](https://arxiv.org/pdf/2310.02170)). The persona set is filtered per dataset: {Assistant, Mathematician, Lawyer,
Economist, Programmer} for arithmetics/GSM8K; {Assistant, Mathematician, Programmer, Psychologist, Doctor} for
pro-medicine. The agent-name format is `<dataset>_<size>__<model>__<persona>__Agent<i>`, so the JSONL output is
downstream-greppable per persona.

The **inference engine** in `src/model/model_utils.py::engine` is a one-call wrapper: tokenize the batch of prompts,
move to GPU, call
`model.generate(do_sample=True, temperature=1.0, top_p=0.9, max_new_tokens=512, return_dict_in_generate=True, output_scores=True, num_return_sequences=1, return_legacy_cache=True)`,
decode generated tokens (skipping the input prefix). One non-obvious detail in the comment at line 15:
`# we find that NOT using chat template is better in MAD` — when prompts are plain user-content strings (not full
chat-templated `[{role: user, content: ...}]` envelopes), MAD performance is empirically better. This is a calibration
finding of the paper: chat templates leak instruction-following biases that homogenize agent responses, which is the
wrong direction for a system whose inputs depend on **diversity of opinions**.

The **model wrappers** under `src/model/llama.py` and `src/model/qwen.py` (the only two loaders, both small) wire up HF
`AutoModelForCausalLM` + `AutoTokenizer` with the model's stock chat template (used only when `multi_persona` needs a
system prompt — see `engine`'s `if type(messages[0]) == list:` branch). LoRA loading via `peft` is supported
(`peft_path` argument on `get_agents`) but unused in the shipped scripts.

The **eight per-dataset shell scripts** under `scripts/` are the experimental matrix. Each runs three commands — default
(full mesh), `--sparse`, `--centralized` — to produce the topology-comparison cells the paper reports.
`heterogeneous.sh` adds `--multi_persona` to all three. There is no orchestration framework around the scripts; they are
bare `python src/main.py ...` invocations meant to be submitted to a SLURM cluster (the `nobackup-fast` prefix in
`environment.yaml` is the giveaway).

## 3. What's reusable in Linus

debate-or-vote's contribution to Linus is **algorithmic**, not code. The lift is the framing
"heuristic-aggregation-vs-per-step-LLM-coordination" and the empirical evidence that the heuristic side wins more often
than the prevailing literature claimed. The destination is the [Phase 3 spawner spec](../specs/phase3-spawner.md) under
DEC-0050 (Role as a first-class type) and DEC-0051 (AgentReport as the typed inter-agent message).

**Phase 3 — heuristic aggregation as the v0 Worker fan-out coordination primitive.** When the Phase 3 spawner fans out N
Workers on a question with a structured answer, the v0 coordination should be **vote-shaped** rather than debate-shaped:
each Worker produces an `AgentReport` independently, and the spawner aggregates with a per-field-type heuristic
(majority for categorical, median for ordinal, argmax-over-confidence for ranked, ROUGE-L best-of-N for free-text per
debate-or-vote's `evaluate_gen`). The debate-shaped alternative — re-prompting each Worker with all peers' reports
across multiple rounds — should be available as an opt-in mode but **not the default**, given debate-or-vote's evidence
that debate is at parity-or-worse in most cells while costing N × R extra LLM calls. This commits the Phase 3 spawner to
**heuristic O(N) coordination as the default** and **per-step-LLM O(N²) debate as an opt-in escape hatch** — the
inversion of the AutoGen-style group-chat default (per [autogen.md](autogen.md) §3, where the centralized Magentic-One
orchestrator runs per-step-LLM coordination through the task-and-progress ledgers).

**Phase 3 — `solver` argument as the Worker-fan-out dispatch knob.** debate-or-vote's `--solver` argument (`'vote'` vs
`'debate'`) is the cleanest existing reference for the dispatch shape Linus's spawner needs: a single flag on the
fan-out call that picks between the cheap heuristic aggregator and the expensive multi-round debate. Lift the shape (a
single string-valued flag with two choices) and the semantics (vote = aggregate round-0 reports with heuristic; debate =
run R rounds of peer-re-prompting before aggregation). The Linus equivalent should default to `vote` per the previous
bullet. Combined with DEC-0031's `cot_budget` and `memory_mode` dispatch knobs, this gives the spawner a small,
orthogonal control surface: `cot_budget` controls how much each individual Worker thinks, `memory_mode` controls what
each Worker remembers, and `solver` (or a less-loaded name like `coordination` or `aggregation`) controls how Workers'
outputs are combined.

**Phase 3 — the three topology variants as a design-space sketch, not a v0 implementation target.** debate-or-vote's
three topologies (decentralized full mesh, sparse ring, centralized star) are the cleanest worked taxonomy of "how much
coordination structure does a fan-out need" in the cloned-repo collection. For Linus's v0 spawner, the practical choice
is **decentralized full-mesh OFF / sparse OFF / centralized = vote**: do not implement any peer-broadcast structure at
v0; ship the vote-shaped heuristic aggregator and add topology variants only if Phase 3 measurement on
`benchmarks/dan_tasks/` shows a quality gap that can be closed with debate. The sparse-ring topology is the obvious "v1
if needed" — O(N) prompt size, partial peer awareness — but committing to it before measurement contradicts the DEC-0027
/ Algorithm framing (delete every requirement, then add it back if it returns).

**Phase 3 — JSONL audit-log shape with per-round records.** debate-or-vote's `out/history/<run-name>.jsonl` shape — one
JSONL line per question, each carrying a round-indexed dict of
`{round_id: {responses, final_answers, final_answer_iscorr, debate_answer, debate_answer_iscorr, answer}}` — is a
directly-usable shape for Linus's Phase 3 fan-out audit log. It carries the right axes (per-round, per-agent,
per-question) for plotting accuracy-vs-rounds curves (the workhorse plot in the paper) and for diagnosing where
individual Workers diverged from the aggregate. The shape is consistent with the
[g7-harnesses synthesis](../syntheses/repo-clusters/g7-harnesses.md) recommendation to adopt the workgraph JSONL
append-only DAG as the Phase 2a session-store / audit-log format — debate-or-vote's per-round JSONL is a per-fan-out
specialization of the same shape. Match the Linus equivalent's schema to this when drafting the Phase 3 spawner
audit-log spec.

**Phase 1+ — empirical-comparison harness as a calibration target for `benchmarks/dan_tasks/`.** debate-or-vote's
experimental matrix (8 datasets × {model: Llama-3.1-8B, Qwen2.5-7B, Qwen2.5-32B} × {N: 3, 5, 7} × {topology: full /
sparse / central} × {persona-set: uniform / heterogeneous} × {round-count: 0..5}) is a precision exercise in controlled
multi-agent ablation. The protocol is directly portable to Linus's `benchmarks/dan_tasks/`: when measuring whether
Worker fan-out beats single-Worker on a given task, follow debate-or-vote's structure — fix all axes except the one
under test, run for multiple seed values, plot accuracy as a function of the swept axis. The pattern is also explicit in
the [agentic-systems-synthesis](../syntheses/agentic-systems-synthesis.md) line ~379 as a "per-Worker debate-quality
smoke test" — debate-or-vote provides the existing scaffold to copy, scaled down to single-machine M1-Max-tractable
token counts.

**Phase 3 — DyLAN-derived persona library as starter material for Linus's heterogeneous-agent mode.** The 14-persona
list in `model/model_utils.py::get_agents` (Mathematician, Economist, Psychologist, Lawyer, Doctor, Programmer,
Historian, Python Assistant, Algorithm Developer, Computer Scientist, Coding Artist, Software Architect, plus the "None"
/ "Assistant" defaults) and the per-dataset filter (5 personas for arithmetics, 5 for pro-medicine) are a practical
reference for how a Linus heterogeneous-Worker mode would seed system prompts. The list is small and directly reusable
as a starter set when Phase 3 needs a heterogeneous-Worker capability; the per-dataset filtering pattern (only the
relevant personas for the task at hand) is a useful discipline to inherit.

**Recommendation verdict's "spike" component — a Linus-side reproduction on M1 Max.** The most concrete way to land the
algorithmic finding in Linus is to **reproduce the headline experiment on M1 Max with a Linus Worker fan-out**: pick one
dataset (GSM8K is the natural choice — small, well-known, scoring is unambiguous), pick one model (Qwen2.5-7B-Instruct
via Ollama, since it appears in debate-or-vote's matrix and is a plausible Linus Worker), run N=3 and N=5 with R=0
(vote-only) and R=3 (debate), and confirm the per-token accuracy curves cross the way the paper predicts. The
deliverable is a `experiments/debate-or-vote-spike/` directory with a Python script that calls Ollama N times per round,
the per-question JSONL output in the same shape, and a one-page summary in `docs/specs/phase3-spawner.md` updating the
spawner-spec coordination defaults. **Estimated effort: one Worker session, ~4 hours wall time given Qwen2.5-7B at ~50
tok/s and ~100 questions × 5 rounds × 5 agents.** The spike output is what closes the algorithmic loop with empirical
evidence on Linus hardware before the spawner spec commits.

## 4. What's inspiration only

The **per-dataset shell scripts** under `scripts/` are tied to a SLURM-cluster file layout (`/nobackup-fast/froilan/`
prefix, separate `--data_dir` and `--model_dir` arguments expected to point at cluster-mounted paths). Useful as a
reading reference for the full experimental matrix the paper sweeps, but not directly runnable on Linus infrastructure
without rewriting the data and model paths. The scripts are also bare command lines with no parallelism wrapper — each
script line is a separate `python src/main.py` invocation. A Linus-side reproduction would replace the shell scripts
with `experiments/debate-or-vote-spike/run.py`.

The **CUDA-only inference path** in `src/model/model_utils.py::engine`. The HF `model.generate()` call with the
`return_legacy_cache=True` argument is a transformers-API quirk relevant to PyTorch + CUDA generation; on Apple Silicon,
the Linus equivalent should call Ollama (via the `/api/chat` endpoint) or mlx-lm rather than HF
`transformers.generate()` directly, both for hardware-targeting reasons and because Ollama's per-request batching and
KV-cache management is more robust than what a research-code wrapper provides. The inference loop is inspiration for
shape (one `engine` call per round, batched across N agents) but not for substance (the implementation does not target
Apple Silicon).

The **regex-based answer extraction** in `evaluator.py`'s `re.findall(r"\{(.*?)\}", response)[-1]` is fragile: it fails
silently on responses that don't follow the brace format, falling back to `""` and contaminating the vote. The paper's
results acknowledge this — the `--bae` (base answer extractor) flag is the explicit fallback for models that ignore the
brace-format instruction. For Linus's Phase 3 spawner, the cleaner shape is **typed structured prediction with explicit
JSON schema** per the CLAUDE.md "Typed structured prediction for biology skills" convention (S25): instead of
regex-extracting a free-text response, the Worker emits a typed object
(`{answer: "...", confidence: 0.87, rationale: "..."}`) and the aggregator votes / medians / ranks over the typed
`answer` field directly. The regex extraction is inspiration for the algorithm (majority vote with random tie-break) but
not for the implementation.

The **`engine`'s no-chat-template comment** (`# we find that NOT using chat template is better in MAD`) is a useful
calibration finding to remember — chat templates can homogenize responses and degrade the diversity the heuristic
aggregator depends on — but it is a research-code observation, not a Linus implementation guide. The Linus equivalent
should test both shapes empirically rather than committing to "no chat template" by precedent. The
[answered-questions](../questions/answered-questions.md) entry S55 ("Adversarial debate as Worker primitive") is the
relevant ADR-tracker context: the resolution defers debate-as-primitive to empirical testing, and debate-or-vote's
finding sharpens the prior.

The **HuggingFace token in a flat file** (`with open('token','r') as f: token = f.read()` — `main.py` lines 333-335) is
research-code shortcutting. Linus uses `~/.config/linus/credentials` or environment variables per the CLAUDE.md
allowlist; do not lift the flat-file token pattern. Inspiration only for "the experiment scripts need an API token"; the
implementation pattern is a security smell.

## 5. What's incompatible or out of scope

**debate-or-vote is research code with no production-readiness budget.** No tests, no CI, no error recovery, no logging
discipline beyond `print()` statements, no checkpointing for crash-resume, no rate-limiting / retry on the HF generate
path, no input validation. This is the norm for a paper-companion repo and is not a criticism — it's research code,
which is what the recommendation verdict (Study + spike) reflects. But it explicitly disqualifies debate-or-vote as a
Linus dependency or a Linus-vendorable code base. The lift is the algorithmic result, not the artifact.

**The CUDA-only environment.** `environment.yaml` declares `torch==2.7.1+cu128` plus the full `nvidia-cu12*` stack
(`nvidia-cublas-cu12`, `nvidia-cuda-cupti-cu12`, `nvidia-cudnn-cu12`, `nvidia-cufft-cu12`, `nvidia-cusparselt-cu12`,
`nvidia-nccl-cu12`, `triton`, `triton-kernels`, etc.). The repo does not run on Apple Silicon without re-targeting the
inference path to Ollama or mlx-lm. The Linus reproduction (per §3) must call Ollama, not the HF path.

**The benchmark-Q&A evaluation surface is mismatched with Linus's primary task.** debate-or-vote evaluates on arithmetic
/ multiple-choice-Q&A / summarization benchmarks where ground truth is a single short string and accuracy is exact-match
(or ROUGE-L). Linus's Phase 3 spawner is for **software engineering and scientific work** — fan-out of Workers debugging
a Python pipeline, exploring a corpus, or running a metagenomic analysis. The output shape is a code change, a JSON
document, a research note, or a multi-step plan. The aggregation heuristic for that shape is **not**
majority-vote-on-a-string; it's something closer to "best by test pass rate" or "best by typed-evidence match" or "merge
by typed-field quorum." The algorithmic finding (heuristic aggregation often beats per-step-LLM debate) generalizes; the
specific aggregator (`evaluate_arithmetics` / `evaluate_mcq`) does not. The Phase 3 spawner spec needs to design
Linus-specific heuristics for Linus's task shapes; debate-or-vote's evaluators are a starting point only for the
categorical / numerical sub-cases.

**The CNN-DailyMail "ROUGE-L best-of-N" aggregator is wrong-by-construction for Linus's open-ended outputs.**
debate-or-vote's `evaluate_gen` ranks N summaries against ground truth via ROUGE-L and picks the highest scorer. This
requires ground truth to exist at evaluation time — fine for a benchmark, useless for a Linus task where the whole point
is that no ground truth exists yet. For Linus's open-ended tasks, the analogous aggregator is **LLM-as-judge with
typed-output rubric** (per the BioReason-Pro shape from CLAUDE.md "Typed structured prediction for biology skills"), not
ROUGE-L. Mark this as out of scope for Linus reproduction; the open-ended task requires its own aggregator design.

**Centralized topology with vote-on-agent-0-only is wrong for Linus.** `args.centralized` mode aggregates from agent 0's
response alone, ignoring agents 1..N-1's outputs after they've informed agent 0's revision. This is fine for the paper's
design (it's part of the topology comparison) but is a worse Linus default than decentralized + vote: it discards N-1
Worker outputs at aggregation time. If Linus implements a "centralized supervisor" pattern (per
[autogen.md](autogen.md)'s Magentic-One reference), the supervisor's job is to **plan and dispatch** the Workers, not to
be the only voice in the final answer. Use the centralized topology for **planning** (one agent writes the plan, N
agents execute the steps) and the decentralized + vote shape for **answering** (N agents answer independently, vote /
median / argmax over their typed reports). debate-or-vote's centralized topology blends the two awkwardly; the Linus
equivalent should keep them separate.

**The persona library is benchmark-tuned, not Linus-task-tuned.** The 14-persona list (Mathematician, Economist, Lawyer,
Doctor, Programmer, etc.) is calibrated for the benchmark mix (where "Doctor" persona helps on pro-medicine,
"Mathematician" on arithmetics, "Lawyer" on hh_rlhf-style ethics questions). Linus's relevant personas — for
software-engineering, scientific-computing, bioinformatics, metagenomics — are different (Senior Scientist, Pipeline
Engineer, Genomics Specialist, Reviewer, Architect, Test Author). Lift the **pattern** (a small per-task-filtered
persona library with system prompts under 300 characters each); rewrite the **content** for Linus's task surface.

**No license issue, but the result-reproducibility cost is non-trivial.** The MIT license is permissive and clean. But
reproducing the paper's full experimental matrix (8 datasets × 3 models × 3 topologies × 2 persona sets × 6 round counts
× multiple seeds) on cluster-grade hardware is order-of-magnitude beyond what a single M1 Max can do in any reasonable
wall time. The Linus reproduction (per §3 last bullet) must scope down aggressively: one dataset, one model, two
topologies, one persona set, two round counts, three seeds. That is enough to confirm the headline finding on Linus
hardware; it is not a reproduction of the paper's matrix.

## 6. Recommendation: **Study + spike**

Read `src/main.py` (the debate loop, the three topologies in `get_new_message`, the round-indexed JSONL output shape)
and `src/evaluator.py` (the `evaluate_*` aggregators — majority vote with random tie-break for categorical / numerical,
ROUGE-L best-of-N for free-text) end-to-end as the algorithmic reference for the Phase 3 spawner's coordination
primitive. Skim `src/model/model_utils.py` (the personas list, the `engine`'s no-chat-template-in-MAD calibration
finding, the model-loading dispatch). The primary cluster cell is
[g7-harnesses](../syntheses/repo-clusters/g7-harnesses.md), which already names debate-or-vote at line ~195 as "the
research-code reference implementation of this pattern; it is a concrete candidate for the Phase 3 spawner Worker
fan-out coordination model." Secondary thematic homes are
[humans-teams-performance-synthesis](../syntheses/humans-teams-performance-synthesis.md) (the debate-vs-vote thread on
multi-agent decision quality) and [agentic-systems-synthesis](../syntheses/agentic-systems-synthesis.md) (the
multi-agent coordination findings, including the explicit deferral of debate-as-Worker-primitive in
[answered-questions](../questions/answered-questions.md) S55 / E4 — debate-or-vote's evidence is the reason that
deferral is now a sharper "default to vote" rather than a vague "decide later").

The **spike** component beyond plain "Study" is the small Linus-side reproduction described in §3 last bullet:
`experiments/debate-or-vote-spike/` reproducing one cell of the paper's matrix on M1 Max via Ollama (Qwen2.5-7B, GSM8K,
N=3 and N=5, R=0 and R=3, three seeds, ~100 questions). The deliverable is a one-page summary in
[`docs/specs/phase3-spawner.md`](../specs/phase3-spawner.md) updating the spawner-spec coordination defaults with
Linus-hardware empirical evidence. The spike is what closes the algorithmic loop with measurement on Linus's actual
substrate before the Phase 3 spawner spec commits to a coordination default. **Do not vendor the code, do not adopt the
inference path, do not lift the regex evaluators.** Lift the algorithmic finding and the per-round JSONL audit-log
shape; ship Linus-native implementations of everything else.

The contrast case is [autogen.md](autogen.md) §3 (AutoGen / Magentic-One). AutoGen runs **per-step-LLM coordination**
through the Magentic-One orchestrator's task and progress ledgers — every step is an LLM call in the inner coordination
loop, with stall-detection and replan re-prompting on failure. debate-or-vote runs **heuristic coordination** with the
LLM removed from the inner loop entirely: the only LLM calls per round are the N agent generations themselves;
aggregation is pure regex + Counter + random.choice. The two repos bracket the design space for Linus: AutoGen's
Magentic-One is the maximal-coordination shape (every coordination decision is an LLM call); debate-or-vote is the
minimal-coordination shape (every coordination decision is a heuristic). The Phase 3 spawner should default to
debate-or-vote's shape for fan-out aggregation and fall back to AutoGen-shaped per-step-LLM coordination only when
measurement on `benchmarks/dan_tasks/` shows the heuristic is failing on a specific task class. AutoGen's
`MagenticOneOrchestrator` (`autogen-agentchat/.../_magentic_one_orchestrator.py`, 536 LoC, per [autogen.md](autogen.md))
is also the natural intermediate to study — its **task ledger** (per-task fact and plan inventory) and **progress
ledger** (per-step LLM-judged progress assessment) are per-step-LLM mechanisms that debate-or-vote explicitly avoids;
the design space "no ledger / progress ledger / full coordination ledger" is the spectrum the Phase 3 spawner spec
should sketch.

## 7. Questions for Dan

1. **Should Linus download the arxiv paper (2508.17536) as a paired paper-note alongside this repo-note?** This would
   mirror the [Letta / MemGPT](Letta.md) and [Kimi-K2](Kimi-K2.md) patterns where a paper-note and a repo-note are both
   in the corpus when the artifact is "this is the paper's reference implementation." The paper itself — the empirical
   matrix, the formal argument for why heuristic aggregation is theoretically sound, the related-work discussion of
   DyLAN / Du-et-al MAD — is the load-bearing content; the repo is the artifact. A paper-pair note following the
   paper-notes paired-repo variant convention (CLAUDE.md §Doc-type conventions: filename `<RepoName>-<arxiv-id>.md`,
   here `debate-or-vote-2508.17536.md`, with `pdf:` frontmatter pointing into `repos/debate-or-vote/` — though there is
   no PDF in the repo currently, only the arxiv link) would deepen the Linus corpus on the algorithmic finding.
   Tentative answer: yes — download the PDF into `context/papers/` and author the paired paper-note in a follow-up Tier
   5+ task, since the algorithmic content (the proof sketch, the ablation matrix, the DyLAN comparison) is what the
   Phase 3 spawner spec actually needs to cite, not the research-code artifact.

2. **Should the Phase 3 spawner spec commit to "vote is the default coordination, debate is opt-in" right now, or wait
   for the M1-Max spike to confirm the finding on Linus hardware?** Two postures: (a) commit now — debate-or-vote's
   evidence (NeurIPS 2025 Spotlight, multi-dataset, multi-model, multi-topology) is strong enough to default to vote
   without re-deriving on Linus hardware; (b) defer the default until the spike measurement is in. Tentative answer: (a)
   — the paper's evidence is sufficient to commit to the default, and the spike is for sharpening Linus-specific
   calibration (e.g., does the no-chat-template finding hold on Ollama-served Qwen2.5-7B?) rather than confirming the
   headline finding from scratch. Worth explicit ADR text in the Phase 3 spawner spec under DEC-0050.

3. **Does Linus's `solver` / `coordination` knob belong in the dispatch layer (caller-side, per-fan-out) or the spawner
   config (Worker-side, declared-once)?** debate-or-vote's `--solver vote|debate` is a CLI-level experiment-control
   knob; for Linus, the question is whether the equivalent knob is set per-fan-out by the Maestro-issuing-the-fan-out
   (caller-side flexibility, lower-overhead runtime change) or set in the spawner's Worker config (declared once per
   Worker pool, easier to reason about). Tentative answer: caller-side per-fan-out, to match `cot_budget` and
   `memory_mode` (DEC-0031) which are already dispatch-time-explicit. The aggregation strategy is properly an attribute
   of "this fan-out," not of "this Worker pool." Worth resolution in the Phase 3 spawner spec.

4. **How does the typed `AgentReport` (DEC-0051) shape interact with the heuristic-aggregator design?** Per
   debate-or-vote's `evaluate_*` shape, the aggregator is **per-task-type** (numerical for arithmetics, categorical for
   MCQ, ROUGE-L for free-text). For Linus, the cleanest shape is to declare the aggregator at the `AgentReport` schema
   layer: each typed `AgentReport` schema declares its own
   `aggregation: vote | median | argmax_confidence | best_by_typed_evidence | judge_with_rubric` field, and the spawner
   reads that field at fan-out aggregation time. Tentative answer: yes — bake the aggregation strategy into the typed
   `AgentReport` schema, not into the spawner config or the dispatch call. This keeps the spawner uniform across task
   types (the spawner just looks up the report's aggregator) and makes new task types self-describing. Worth a Phase 3
   spawner spec ADR alongside DEC-0051.

5. **Should debate-or-vote's three topology variants (full mesh / sparse ring / centralized star) be sketched in the
   Phase 3 spawner spec as design-space documentation, or omitted entirely?** Two postures: (a) sketch all three in the
   spec as "future variants we know exist" — useful documentation for when measurement says pure-vote is insufficient;
   (b) omit topology variants entirely from v0 spec, and add a section only when measurement demands them. Tentative
   answer: sketch them briefly in a "Design space (future variants)" subsection of the Phase 3 spawner spec, with
   debate-or-vote as the canonical reference. The cost is a paragraph; the upside is that future Phase 3 spec revisions
   don't need to re-discover the design space.

6. **The DyLAN-derived persona library (14 personas) — is this where Linus's heterogeneous-Worker mode persona set
   should start, or should Linus author its own from scratch?** The library is benchmark-tuned (Mathematician helps
   arithmetics, Doctor helps pro-medicine, etc.) and Linus's task surface is different (software engineering, scientific
   computing, bioinformatics, metagenomics, LLM infrastructure). Tentative answer: author from scratch — Linus's
   personas (Senior Scientist, Pipeline Engineer, Genomics Specialist, Reviewer, Architect, Test Author, plus
   Dan-specific roles like "LanzaTech metagenomics workflow expert") are different enough that lifting the DyLAN library
   is more confusing than helpful. The pattern (small per-task-filtered library with sub-300-char system prompts) is
   what to lift; the content is Linus-specific.

7. **Is debate-or-vote's calibration finding "no chat template is better in MAD" a phenomenon to test on Linus's
   Ollama-served Qwen2.5 / Llama-3.1 path, or a research-code-specific observation?** The comment at `model_utils.py`
   line 15 (`# we find that NOT using chat template is better in MAD`) is a non-obvious instruction-following /
   response-diversity finding worth re-testing on Linus's actual inference path: when N=5 Workers all answer the same
   question via Ollama (which always applies the model's chat template at the `/api/chat` endpoint), do the responses
   cluster too tightly to benefit from voting? If yes, Linus may need to expose a `raw_completion` path (Ollama's
   `/api/generate` endpoint) for fan-out scenarios specifically. Tentative answer: include this as a measurement axis in
   the M1-Max reproduction spike — run the same N=5 GSM8K experiment with `/api/chat` (templated) and `/api/generate`
   (raw) prompts and compare round-0 vote accuracy. If the gap is real on Linus hardware, document it as a Phase 3
   inference-path dispatch consideration.

8. **Should the Linus reproduction spike (per §3 last bullet) be a Worker-delegated task or a Maestro task?** The work
   is well-specified (one dataset, one model, two topologies, two round counts), small in code surface (~200 LoC of
   orchestration around Ollama), and produces a typed JSONL result that maps to a spec-update. Tentative answer:
   Worker-delegated, with the spec at `docs/specs/debate-or-vote-spike.md` describing the experimental matrix, the
   Ollama integration, the JSONL output shape, the success criteria (Linus reproduces the paper's headline finding on
   the GSM8K cell within 5 percentage points). The Worker produces the spike output and the spec update; Maestro reviews
   and merges. Schedule for after Phase 1c Worker selection lands so the chosen Worker model can do the job.
