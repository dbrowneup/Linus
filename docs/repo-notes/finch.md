# finch (`Future-House/data-analysis-crow`)

## 1. Purpose and scope

Finch — the FutureHouse "data-analysis-crow," packaged on PyPI as `fhda` — is a **Jupyter Notebook agent** for
scientific data analysis, bioinformatics-tilted. The agent takes a dataset path and a natural-language query, then
iteratively builds up a single `notebook.ipynb` by appending or editing code cells, executing them, observing output,
and deciding the next cell. It is the exact agent that produced the trajectories scored by **BixBench**, FutureHouse's
bioinformatics benchmark — so finch is the _tool_ and BixBench is the _yardstick_. For Linus, this is the most directly
relevant exemplar of "scientific Worker" execution on disk: Phase 7's domain-tool layer plausibly starts by adapting
finch's notebook-as-substrate pattern to Linus's KnowledgeBase and a local worker model.

## 2. Architecture summary

A small Python package (`src/fhda/`, ~12 modules) on top of the FutureHouse **Aviary** framework — finch's
`NBEnvironment` subclasses `aviary.core.Environment` and exposes three tools to the agent: `edit_cell(contents, idx)`,
`list_workdir()`, `submit_answer(answer)`. That's the entire surface area. There is no custom kernel; finch uses stock
`jupyter_client.AsyncKernelManager` for local execution and stock `jupyter nbconvert --execute --inplace --allow-errors`
inside an `aiodocker`-managed container for sandboxed execution. The clever piece is the _agent loop convention_: every
successful `edit_cell` call **automatically reruns the entire notebook from the top**, then `get_env_state_msg()` hands
the agent back a Markdown rendering of the whole notebook (cells + outputs + base64 images via `view_notebook`). The
model's "state" is literally the rendered notebook, and its actions are cell mutations — no separate scratchpad, no
tool-result message threading. `DataAnalysisEnv` (in `data_analysis_env.py`) wraps `NBEnvironment` with task
scaffolding: a problem string, an `EvalAnswerMode.LLM` grader, CoT prompt augmentation
(`prompts.CHAIN_OF_THOUGHT_AGNOSTIC`, `GENERAL_NOTEBOOK_GUIDELINES`), and a GCS-backed trajectory store.

The Docker image (`Dockerfile.pinned`, published as `futurehouse/bixbench:aviary-notebook-env`) is the other half of the
value: a miniconda3 base layered with R 4.3.3 + IRkernel + a tidyverse/Bioconductor stack (DESeq2, clusterProfiler,
EnhancedVolcano, GenomicRanges, ggpubr, pheatmap), a Python kernel with anndata, scanpy, biopython, gseapy, pydeseq2,
scikit-learn, umap-learn, mygene, plus CLI tools (BLAST, FastQC, MAFFT, IQ-TREE, SPAdes, trim-galore, ClipKIT, PhyKIT,
MetaEuk). It also installs `udocker` so the agent can recursively run other bioinformatics containers without needing
host Docker. Switching between local-kernel and container execution is a single `USE_DOCKER` env-var flip in
`config.py`. Model dispatch is via litellm; `tortoise.py` orchestrates multi-step FutureHouse-hosted pipelines (`Step`
objects with `n_replicate_tasks` for fan-out and consensus). Heavyweight deps are `ldp==0.26.0` and
`fhaviary[server]==0.19.0` — finch only makes sense atop the rest of the FutureHouse stack.

## 3. What's reusable in Linus

The notebook-as-substrate pattern is the prize, and it's small enough to lift cleanly. `NBEnvironment` is ~400 lines and
the action-observation loop is "model edits a cell; runtime reruns the whole notebook; model receives Markdown of
cells + outputs." That transposes directly onto a Phase 7 Linus scientific Worker: hand a Qwen2.5-Coder instance the
same three tools, point it at a KnowledgeBase artifact directory, and let it iterate. The rerun-everything-on-each-edit
rule is a deliberate simplification — the notebook stays causally consistent, and the model never reasons about kernel
state divergence. Worth inheriting as a constraint in Linus worker prompts.

Versus the rest of the FutureHouse stack: **paper-qa** is read-only literature QA, **aviary** is the underlying
tool/environment abstraction (finch _uses_ it, doesn't replace it), **ldp** is the rollout/training library, **robin**
and **ether0** are domain-specific scientific agents, **LAB-Bench** and **BixBench** are evaluation harnesses. Finch is
the only one whose deliverable is "an agent that _does_ multi-step computational analysis end-to-end and emits a
runnable artifact." Its notebook is reviewable, re-executable, and shareable in a way a chat transcript is not — which
matches how Dan actually does science.

## 4. What's inspiration only

`tortoise.py` and the `expts/` server/client pattern are bound to FutureHouse's hosted platform (`futurehouse-client`,
GCS storage, hosted job IDs like `job-futurehouse-data-analysis-crow-high`) and don't transfer to a local Linus install.
The Aviary `Environment` / `Tool` abstractions are reasonable but Linus does not need to adopt aviary as a framework
dependency to copy the notebook-loop pattern; aviary is worth reading as a reference for what a clean tool/env interface
looks like, not vendoring. The litellm-mediated provider zoo is overkill — Linus has Ollama and is heading toward pmetal
serve; one or two providers is enough.

## 5. What's incompatible or out of scope

The Docker dependency is load-bearing. CLAUDE.md flags that **Docker on macOS runs in a Linux VM with no Metal/ANE
passthrough**, and the bioinformatics image is x86_64 miniconda3 — on M1 Max it runs under Rosetta/QEMU emulation, slow
particularly for SPAdes, BLAST, IQ-TREE. The `USE_DOCKER=false` path (`AsyncKernelManager` against a local Jupyter
kernel) sidesteps emulation but loses sandbox isolation and forces Linus to host the full bioinformatics conda env,
colliding with `linus` env discipline. Choices: accept slow emulated Docker, build an arm64 variant of the image (real
work — bioconda pins predate arm64), or design a Linus-native sandbox (sandbox-exec + per-Worker conda env) and abandon
the published image. Secondary: GCP deps and `futurehouse-client` couple advanced flows to FutureHouse's hosted
platform; `EXEC_TIMEOUT = 1200.0` is laptop-punishing and needs tightening; pinned `anthropic`/`numpy`/`pandas` versions
will conflict and need loosening in any port.

## 6. Recommendation: **Study (and port the loop pattern in Phase 7)**

Do not vendor finch. Do read `notebook_env.py` and `data_analysis_env.py` carefully — they are the canonical worked
example of "agent + Jupyter + iterative refinement" and the right starting reference when Linus's Phase 7
scientific-Worker spec gets written. At that point, lift the three-tool surface (`edit_cell`, `list_workdir`,
`submit_answer`), the rerun-on-edit invariant, and the Markdown-of-notebook observation shape directly into a Linus tool
implementation. Skip aviary, ldp, tortoise, and the GCS layer; replace litellm with Linus's own router; and make a
host-vs-Docker decision upfront rather than carrying both code paths. The bioinformatics package list in
`Dockerfile.pinned` and `kernel_requirements.txt` is a useful menu for what the eventual "Linus bio Worker env" should
include even if the image itself is rebuilt.

## 7. Questions for Dan

- **Sandbox decision for Phase 7.** Three options: (a) accept emulated x86 Docker and the slowness, (b) build an arm64
  bioinformatics image (real packaging work, many bioconda pins to revisit), (c) skip Docker and isolate via a
  per-Worker conda env + sandbox-exec. Which way should the spec lean?
- **Notebook-as-artifact in KnowledgeBase.** Finch produces a `notebook.ipynb` per task as a first-class shareable
  artifact. Should Linus's KnowledgeBase store agent-produced notebooks alongside papers and notes — i.e., does "agent
  ran this analysis" become a retrievable, citable object?
- **Rerun-everything cost on local hardware.** The "rerun whole notebook on every edit" invariant is elegant but
  expensive on a laptop for analyses with 10+ minute cells. Acceptable cost for the simplicity, or do we add cell-level
  cache invalidation in the Linus port?
- **Coupling to BixBench as the eval.** Does it make sense to run BixBench against Linus's own port of the finch loop as
  the Phase 7 acceptance test, or build a Dan-specific notebook benchmark in `benchmarks/dan_tasks/` that more closely
  matches your real workflow (the genomics/RNA-seq problems you actually do)?
  _Partially resolved (S11, S12, see [answered-questions.md](../questions/answered-questions.md)): BixBench adopted as
  Phase 1 agent-harness benchmark; Dan-authored tasks weighted more heavily; both run in parallel._
- **Multi-language support.** Finch supports Python, R, and Bash via `NBLanguage`. R is a meaningful fraction of
  bioinformatics. Is keeping R kernel support in Linus a Phase 7 requirement, or is Python-only acceptable for v1?
