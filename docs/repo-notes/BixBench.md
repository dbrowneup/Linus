# BixBench (`Future-House/BixBench`)

## 1. Purpose and scope

BixBench (arXiv 2503.00096, dataset on HuggingFace at `futurehouse/BixBench`) is a benchmark designed to evaluate
LLM-based agents on real-world bioinformatics tasks. The dataset is 205 questions derived from 60 published Jupyter
notebooks plus their accompanying data ("capsules") — each capsule is a real research artifact, zipped on HuggingFace,
containing a Data folder the agent can analyze. Tasks require the agent to explore biological datasets, write and
execute multi-step analyses in Python (or R or Bash), generate scientific hypotheses, and answer either open-ended or
multiple-choice questions about the result. The repo ships three things: agentic evaluation
(`generate_trajectories.py` + `postprocessing.py`), a zero-shot baseline (`generate_zeroshot_evals.py` +
`grade_outputs.py`) for measuring how well a model answers without ever touching the data, and the configuration to
replicate the paper's v1.5 results. For Linus this is the closest existing artifact to "a public eval for what a private
bio-Worker would actually need to do" — directly relevant to Phase 1 benchmark design (Dan-task-suite) and Phase 7
skills graduation in any genomics/biochem direction.

## 2. Architecture summary

A small Python 3.12 package built on the FutureHouse stack: `aviary` provides the `DataAnalysisEnv` and message types,
`ldp` provides the `ReActAgent`/`SimpleAgent` and the `RolloutManager`, `fhda` (data-analysis-crow, pinned to v1.5.0)
provides the actual Jupyter-notebook environment the agent acts in, `lmi`/`fhlmi` wraps litellm for any chat model, and
`fhbixbench` itself is the glue. A run is YAML-configured (`bixbench/run_configuration/*.yaml`) — agent type, model,
`max_steps` (default 20–40), batch size, capsule mode (`open` / `mcq` / `hypothesis`), refusal-option toggle,
image-avoidance toggle, eval mode, paths. `generate_trajectories.py` downloads the HF dataset, extracts capsules, spawns
a `DataAnalysisEnv` per question with a Docker-backed Jupyter kernel (`futurehouse/bixbench:aviary-notebook-env`,
`USE_DOCKER=true` default), runs an aviary or vanilla rollout, and serializes a `Trajectory` plus the produced notebook
to JSON/JSONL. `postprocessing.py` then loads the trajectories, grades them (LLM-judge for open-ended via
`OPEN_ENDED_GRADING_PROMPT` and `OPEN_ENDED_RANGE_GRADING_PROMPT`, exact-match for MCQ), runs majority-vote analysis at
configurable k (paper default 5), and produces comparison plots. The v1.5 paper reproduction runs five replicas across
GPT-4o and Claude-3.5-Sonnet, with image-on/image-off and refusal/no-refusal cells — 24–48 hours of wall time and
"significant API credits" by the README's own warning.

## 3. What's reusable in Linus

The dataset itself, treated as an external eval, is the headline value. Pointing Linus's Phase 2a OpenAI-compatible
endpoint at the `generate_zeroshot_evals.py` script via litellm's openai-compatible provider is a one-evening exercise
and gives a real, reproducible bioinformatics-knowledge score for any local model (Qwen2.5-Coder, Mistral-7B, future
fine-tuned Linus). That zero-shot path needs no Docker, no capsule downloads, and no agent loop — it tests pure
parametric knowledge of the field. The agentic path — capsule download, Docker notebook, ReAct rollout, LLM-judge — is
also runnable against Linus's endpoint, but at meaningful cost: 205 questions × replicas × max_steps tool calls. Worth
running once on the strongest local model to baseline, then again as a Phase 6 / Phase 7 graduation gate. The
YAML-configured rollout pattern (`agent_type`, `agent_kwargs`, `max_steps`, `batch_size`, `rollout_type`) is also a
clean reference for how Linus's own benchmark harness in `benchmarks/dan_tasks/` should be structured.

Compared to **LAB-Bench** (FutureHouse's other bio benchmark, sibling repo in this group), BixBench is end-to-end
agentic on real notebooks while LAB-Bench is multiple-choice over the literature — LAB-Bench tests recall and literature
reasoning, BixBench tests whether the agent can actually write and run analysis code on raw `.csv`/`.h5`/RNA data and
reach a defensible answer. The two are complementary; for Linus, BixBench is the more demanding and the more indicative
of real bio-Worker utility. Compared to **bioSkills's Bio-Task Bench** (G9, separate team), Bio-Task Bench evaluates
skill primitives ("does the agent invoke the right tool with the right args") via a third-party harness; BixBench
evaluates end-to-end answers against ground truth from real published notebooks. Bio-Task Bench is the cheap fast
developmental signal during skill-building; BixBench is the slower, more realistic regression check. Use both at
different cadences. Compared to **finch** (the FutureHouse agent that produced the trajectories used in the BixBench
paper), BixBench is the eval and finch is one of the systems-under-test — Linus does not need finch to run BixBench,
only an agent that can be wrapped in the `aviary`/`ldp` rollout interface (or the documented `custom_rollout` extension
point at `generate_trajectories.py:239`).

## 4. What's inspiration only

The Docker-per-question execution sandbox is good practice but does not pass through Metal/ANE on macOS (per CLAUDE.md
"Docker runs in a VM"). For Linus's own Dan-task-suite, the equivalent should be a native sandboxed Jupyter kernel — the
`use_docker: false` mode exists in BixBench's notebook config and is the right starting point. The LLM-as-judge grading
pattern is reusable but inherits all the usual bias and reproducibility caveats; Dan can read the prompts in
`prompts.py` and decide whether to trust them as-shipped or replace with stricter exact-match plus a hand-graded rubric
for the Dan-task-suite. The five-replica majority-vote methodology is methodologically sound but financially aggressive
— for local Worker eval where inference is free, run more replicas, not fewer.

## 5. What's incompatible or out of scope

The v1.5 reproduction depends on hosted GPT-4o and Claude-3.5-Sonnet API access — the published numbers are
frontier-model numbers and Linus is not trying to beat them. Comparing a local 7B Worker to those baselines on absolute
accuracy will be discouraging; the right comparison is local-model-now versus local-model-after-fine-tune, with the
frontier numbers as a ceiling. The `fhda @ git+...v1.5.0` dependency is a git pin — fine for a study clone, slightly
sticky if Linus ever vendors any of this. The Docker image is a several-hundred-MB pull. None of this is deal-breaking;
it just means BixBench is consumed as an external benchmark, not vendored.

## 6. Recommendation: **Study (and adopt the dataset as a Phase 1 / Phase 7 eval)**

Do not vendor the BixBench code into Linus. Do install `fhbixbench` into a dedicated conda env in Phase 1 once Linus's
endpoint exists, run `generate_zeroshot_evals.py` against the local endpoint for a same-evening baseline, and add the
resulting score to `benchmarks/results/`. Run the full agentic evaluation once per major Linus release as a regression
check. Use BixBench's task structure (capsule + question + Jupyter notebook + LLM-judge) as a design reference for the
private Dan-task-suite, especially for any genomics analysis tasks Dan curates from his own paper corpus.

## 7. Questions for Dan

- **Dataset overlap risk.** BixBench questions derive from 60 published notebooks. If Dan has read any of those source
  papers (likely, given the field), there is a contamination concern when Dan-curated tasks share provenance. Want to
  log which capsules Dan recognizes and treat them as "no-credit" items in the Linus scorecard?
- **Open-ended vs MCQ for Dan-task-suite.** BixBench supports both modes; the open-ended setting with LLM-judge grading
  is more realistic but noisier. For the private Dan-task-suite, do we follow BixBench and offer both, or commit to one
  mode (likely open-ended with hand-graded rubric for the held-out subset)?
- **Docker vs native kernel.** BixBench defaults to a Docker Jupyter env. On the M1 Max that loses Metal/ANE access for
  any in-notebook ML; for bio-analytics work this rarely matters (pandas/scipy/biopython), but for any benchmark task
  involving local inference inside the notebook it would. Run BixBench in `use_docker: false` mode to keep parity with
  Linus's actual deployment surface, or accept the Docker default for reproducibility?
- **LAB-Bench in parallel.** The sibling repo LAB-Bench is the literature-reasoning counterpart to BixBench's
  notebook-execution focus. Worth standing both up in Phase 1, or prioritize BixBench as the more mission-aligned and
  treat LAB-Bench as a later add?

  _Resolved (S11, see [answered-questions.md](../questions/answered-questions.md)): Both adopted for Phase 1; LAB-Bench
  is the broader knowledge-axis baseline; BixBench is the agent-harness benchmark. Dan-authored tasks weighted more
  heavily than either in Phase 1 decision-making._
- **Frontier baselines.** Should the Linus scorecard list the v1.5 paper's GPT-4o / Claude-3.5-Sonnet numbers as a
  visible ceiling on every BixBench run, or leave them out so Worker progress is judged on its own trajectory?
