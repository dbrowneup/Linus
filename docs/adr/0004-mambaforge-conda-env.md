## DEC-0004 — Package/env management via mambaforge conda

**Date:** 2026-04-22 **Status:** accepted

**Context.** Dan's existing environment uses mambaforge (conda-forge) + conda. KB also uses conda. Options were: keep
conda, switch to uv+venv, or use both.

**Decision.** Linus uses a **conda environment named `linus`**, managed via mambaforge. Rust and uv are installed inside
the conda env for tool flexibility (pmetal build, autoresearch-mlx, etc.). Node/npm can also be installed into the env
if needed. The brew-installed `mlx`, `mlx-c`, and `ollama` are NOT reinstalled via conda — the brew versions have native
Apple Silicon optimization.

**Consequence.** Consistent with KnowledgeBase's conventions, so patterns transfer cleanly. Environment is reproducible
via `environment.yml`. Does NOT preclude experimenting with uv-managed venvs for specific subprojects later.
