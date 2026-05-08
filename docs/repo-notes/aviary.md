# aviary (`Future-House/aviary`)

## 1. Purpose and scope

Aviary (PyPI `fhaviary`, paper `arXiv:2412.21154`, December 2024) is FutureHouse's **gymnasium-style framework for
defining language-agent environments**, with a deliberately Gym/Gymnasium-shaped API: `obs, tools = await env.reset()`
and `obs, reward, done, truncated = await env.step(action)`. It is the _environment_ half of FutureHouse's training
stack — its sister library LDP supplies the _language decision process_ (agent / policy / learning) half. Aviary itself
ships five reference environments — GSM8K (math), HotPotQA (multi-hop QA), LAB-Bench (biology QA, including LitQA2 and
FigQA), LFRQA (long-form retrieval QA), and a Jupyter notebook environment — plus a paper-mentioned protein-stability
environment. For Linus this is squarely Phase 6 (fine-tuning / RL on Dan's tasks) and Phase 7 (skills graduation):
aviary is the cleanest small-API substrate for turning Dan's actual biochemistry workflows into trainable /
benchmarkable environments without inheriting a heavy RL framework.

## 2. Architecture summary

A uv workspace with a tight core in `src/aviary/` (~2.5k LOC) and per-environment packages under
`packages/{gsm8k,hotpotqa,labbench,lfrqa,notebook}/`. The core is just five abstractions, all in `aviary.core`:
`Environment[TEnvState]` (ABC, `reset` + `step`, owns a `list[Tool]` and `state`), `Message` / `ToolRequestMessage` /
`ToolResponseMessage` (OpenAI chat-message-shaped, role-tagged with a special `tool` role and PIL/base64 image support),
`Tool` (built from a Python function via `Tool.from_function` — name, args, and types come from the signature;
description comes from the docstring, FastAPI-style `\f` truncation supported), `TaskDataset[TEnvironment]`
(registry-keyed factories that yield environments per task, with `iter_batches` for training loops), and `Frame`
(serializable per-step snapshot for visualization / debugging). Two extra layers: a `fenv` decorator API
(`functional.py`) for defining environments by decorating a `start()` function plus `@env.tool()` functions; and a
remote-environment story via `EnvironmentClient` / `TaskDatasetServer` that lets a heavy environment (e.g. PaperQA + a
real notebook sandbox) run on a server, with the agent process talking to it over HTTP. The notebook environment
optionally executes inside a Docker sandbox (`NB_ENVIRONMENT_USE_DOCKER=true`) — the only place aviary itself touches
containers. Tools execute concurrently by default with a reader/writer lock for non-thread-safe tools. There is no
policy, no optimizer, no rollout loop in aviary; LDP supplies all of that.

## 3. What's reusable in Linus

The `Tool.from_function` ergonomics are excellent and map almost exactly onto what Linus needs for its Phase 2a tool
registry: a Python function with a Google-style docstring becomes an OpenAI-shaped tool with no schema duplication.
Compared with **paper-qa**, which is a _consumer_ of aviary (`GradablePaperQAEnvironment` in
`packages/labbench/src/aviary/envs/labbench/env.py` wraps a paper-qa `Settings` into a step/reward loop), and **ldp**,
which is the agent-side runtime that drives aviary's environments via `RolloutManager`, aviary alone is by far the
smallest dependency — pure Python, only pydantic + httpx + docstring*parser. Phase 6 use: wrap Dan's existing genomics /
biochemistry tasks (KnowledgeBase queries, sequence checks, paper grading) as `Environment` subclasses, register a
`TaskDataset`, and the same code is reachable by both an LDP rollout (for RL fine-tuning of a local Qwen / Mistral /
Linus worker) and a plain LiteLLM agent (for benchmarking). The `LAB-Bench` package is also directly relevant as a
\_baseline benchmark* for Dan's domain — a standardized biology-QA harness that hosted Claude has presumably been
measured on, giving a Maestro/Worker delta to chase. The `EnvironmentClient` + `TaskDatasetServer` split is a useful
prior-art pattern for Linus's own orchestration layer if a tool ever grows too heavy to live in the agent process.

## 4. What's inspiration only

The functional `fenv` API is cute but the class-based `Environment` subclass is what every shipped environment in the
repo actually uses; Linus should mirror the class-based pattern. Aviary's `Renderer`, `dataset_server`, and `cli`
(`aviary tools <env>` browser) are useful only for demos/debugging. Within the FutureHouse stack the division of labour
is clean: **aviary** = env + tool + message + dataset; **ldp** = agent, policy, rollout, training; **paper-qa** = a
heavy retrieval-QA environment plugged into aviary via the `labbench` package; **LAB-Bench** = the dataset and grading
rubric. Differentiator within the siblings: aviary is the _only_ one of the FutureHouse trio that is small,
self-contained, and interesting on its own — `paper-qa` only matters with a corpus, `ldp` only matters once you're
committed to RL training, but aviary's Tool/Environment abstractions are valuable to Linus even if RL never happens.

## 5. What's incompatible or out of scope

Nothing CUDA-bound or Apple-Silicon-hostile — aviary is pure-Python orchestration. The only friction points are
dependency weight when you opt in to environments (`labbench` pulls in PaperQA which pulls in a vector store; `notebook`
wants Docker, which on macOS runs in a VM with no Metal/ANE passthrough — fine because the notebook environment is the
agent's _target_, not Linus's inference backend), and the assumption that "training" means LDP. If Linus wants to train
with pmetal's GRPO implementation instead of LDP, aviary still works as the env spec but the rollout loop has to be
rewritten — aviary returns `(obs, reward, done, truncated)` tuples, which any RL trainer can consume, so this is a glue
task, not an incompatibility. Python 3.11+ requirement is satisfied by the `linus` conda env (3.12).

## 6. Recommendation: **Study (with a Phase 6 path to Integrate)**

Note that aviary is already an indirect runtime dependency via paper-qa (DEC-0044, accepted 2026-05-06): `paper-qa`
imports `fhaviary` as a hard dep, so when Linus adopts paper-qa as the Phase 2c KnowledgeBase retrieval engine, aviary
ships in the linus env as a transitive install whether or not Linus uses its `Environment` abstractions directly.

Phase 1: read the paper, run the GSM8K and Counter tutorial notebooks against an Ollama-hosted worker via LiteLLM to
verify the API ergonomics on Apple Silicon. Phase 6: when the RL/fine-tuning question becomes concrete, decide whether
aviary + LDP is the rollout substrate or whether pmetal's GRPO trainer wants its own env wrapper. If Dan's domain
benchmarks (`benchmarks/dan_tasks/`) end up expressed as aviary `Environment`s, the same code becomes a benchmark today
and an RL training target tomorrow — this is the strongest argument to commit early. Do not vendor; install `fhaviary`
from PyPI and wrap.

## 7. Questions for Dan

1. **Benchmark substrate.** Should `benchmarks/dan_tasks/` be implemented as aviary `Environment`s from day one (so
   Phase 6 RL is a config flip, not a rewrite), or kept as a lighter custom-eval-runner format and ported only if/when
   RL becomes real?
2. **LDP vs pmetal-trainer for RL.** Both can drive aviary environments in principle, but LDP is Python-native and
   assumes LiteLLM-style endpoints, while pmetal owns the model weights and offers GRPO/DAPO directly. Is the Phase 6
   plan "aviary envs + LDP rollouts + pmetal as the served model," or "aviary envs + a pmetal-native rollout shim"?
   They're different glue problems.
3. **LAB-Bench as a Maestro/Worker delta target.** LAB-Bench is published, with hosted-frontier scores presumably
   available. Worth running a local Qwen-Coder-32B vs. hosted-Claude head-to-head on LitQA2 / FigQA to size the gap
   before committing to fine-tuning? _Partially resolved (see
   [answered-questions.md](../questions/answered-questions.md)): LAB-Bench MCQ-with-refusal adopted as the Worker
   quality ceiling reference benchmark (S11); head-to-head run and fine-tuning gate remain open pending Phase 1c data._
4. **Notebook environment as Linus's notebook tool.** The `aviary.notebook` package is a working Docker-sandboxed
   Jupyter executor. Adopt it as Linus's first sandboxed-code-execution skill in Phase 7, or roll a simpler
   `nbclient`-based local executor and accept lower isolation?
5. **Tool definition surface.** `Tool.from_function` (signature + docstring → schema) is much cleaner than the
   Cline-style "variant prompts per model family" approach. Standardize on it for Linus's tool registry, or treat it as
   one of several adapters into a Linus-native `Tool` type?
