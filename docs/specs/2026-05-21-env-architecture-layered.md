# 2026-05-21 — Env-architecture: layered linus + KB (Option C)

**Status:** proposed, 2026-05-21.
**Owner:** Maestro drafts; Dan reviews; v0.6.0 work item.
**Decision pending — Dan approves before any KB packaging changes ship.**

---

## Motivation

The 2026-05-21 Streamlit-broken investigation surfaced a structural friction: Linus and
KnowledgeBase live in separate conda envs (`linus` and `papers` respectively), and the
two envs share no shipping discipline. KB's pipeline modules require PyMuPDF +
networkx + scispacy + transformers + a scientific-computing stack that the `linus` env
doesn't carry; conversely, `linus` ships FastAPI + Ollama-client + paper-qa that KB
doesn't need.

Today this means:

1. Running KB's pipeline requires `conda activate papers` and operating from a
   different shell context than Linus's server/UI work.
2. Any Python-level interop between Linus and KB is hand-mediated through disk
   artifacts (Linus reads KB's outputs at `modules/KnowledgeBase/data/outputs/`).
3. The KB submodule is effectively a sibling project — interesting collaboration
   pattern, but operational friction for a single-developer setup.

The three option space (per the 2026-05-21 chat) is:

| Option | Description |
|---|---|
| **A. Fully separate** | Status quo. Linus reads KB outputs from disk; never invokes KB pipeline directly. Two envs forever. |
| **B. Merged** | One `linus` env carries KB's deps too. KB's PyMuPDF (AGPL) lives inside the linus env. License boundary blurs. |
| **C. Layered** | `linus` is the base. KB ships its own `pyproject.toml` with `[project.dependencies]`; `pip install -e modules/KnowledgeBase` overlays KB's deps INTO the linus env (or any env). Single conda env, optional KB layer, license boundary remains at KB submodule edge. |

Dan's 2026-05-21 call: **Option C (layered)**, post-reveal. This spec captures the
design.

## The plan

### KB-side packaging (the load-bearing change)

KB currently has no `pyproject.toml`; its dependencies live in `environment.yml`
(conda) only. The fix:

1. Author `modules/KnowledgeBase/pyproject.toml` with:
   ```toml
   [project]
   name = "knowledgebase"
   version = "0.1.0"
   requires-python = ">=3.11"
   dependencies = [
       "pymupdf>=1.23",
       "networkx>=3.0",
       "scispacy>=0.5",
       "transformers>=4.30",
       "sentence-transformers>=2.2",
       "hdbscan>=0.8",
       "bertopic>=0.15",
       "rdflib>=7.0",
       "sqlalchemy>=2.0",
       "pandas>=2.0",
       "scipy>=1.11",
       "numpy>=1.26",
       "ollama>=0.1.7",
       # Plus whatever the actual full list is — derived from
       # KB's existing environment.yml + import audit
   ]

   [project.optional-dependencies]
   gpu = ["torch>=2.0"]
   dev = ["pytest>=7.0", "ruff>=0.3"]

   [build-system]
   requires = ["setuptools>=68", "wheel"]
   build-backend = "setuptools.build_meta"

   [tool.setuptools]
   packages = ["papers_analysis"]
   ```

2. Keep `environment.yml` (the `papers` env) intact — that's the standalone-KB path.
   Anyone using KB-only continues to `conda env create -f environment.yml`.

3. The layered path: `pip install -e modules/KnowledgeBase` inside the `linus` env
   overlays KB's deps without touching the conda env file. Both envs continue to
   work; one of them now also gives you Python-level access to KB modules.

### Linus-side coordination

1. New optional extra in `pyproject.toml`:
   ```toml
   [project.optional-dependencies]
   kb = [
       "knowledgebase @ file://./modules/KnowledgeBase",
   ]
   ```
2. Install instruction in Linus README: `pip install -e .[kb]` adds KB's deps to
   whatever env Linus is installed in.
3. CLAUDE.md amendment: document the new `linus + kb` layered install pattern as
   the recommended dev setup; `papers`-env continues to work for KB-only users.

### What stays the same

- The KB submodule is still a separate git repo at `dbrowneup/KnowledgeBase`.
- KB's `papers` conda env continues to work standalone.
- The hardcoded-paths fix per `docs/specs/2026-05-21-kb-hardcoded-paths-fix.md` is
  orthogonal and lands on the same KB-side PR (or as a sibling).
- Linus's `linus` conda env continues to work without KB (the `[kb]` extra is opt-in).

### Migration / ship plan

1. **KB-side PR #1** (against `dbrowneup/KnowledgeBase` master): introduce
   `pyproject.toml` with the full dependency list. No code change beyond packaging.
   Tested by `pip install -e .` from a fresh venv producing a working install.
2. **KB-side PR #2 / sibling** (optional, can be the same PR): the hardcoded-paths
   refactor per the separate spec.
3. **Linus-side PR**: add the `[kb]` optional extra to `pyproject.toml`; update
   Linus README setup section; bump submodule pin.
4. **Documentation**: CLAUDE.md amendment + a one-page runbook for the layered
   install.

### Tradeoffs

**Pro:**
- Single env (`linus`) can do everything if you want it to.
- License boundary preserved (PyMuPDF AGPL stays in KB's pyproject; Linus core's
  MIT remains pure when installed without `[kb]`).
- Standalone KB-only users still get a clean `papers` env path.
- Python-level interop becomes possible (e.g., Linus tools can call KB pipeline
  functions directly post-install).

**Con:**
- KB needs to maintain a pyproject.toml AND environment.yml. Risk of drift —
  mitigation: a tiny `tools/check_dep_parity.py` script that compares the two.
- The first install is heavier (KB drags in transformers, scispacy models, etc.).
- AGPL surface is technically reachable in the linus env when `[kb]` is installed
  — this is the same effective state as today (KB's outputs flow into Linus), so
  no real change in license obligation. Document explicitly anyway.

### Risk surface

- **Dependency conflicts.** Both envs share Python 3.12 but KB pins some libraries
  more tightly. Resolve by widening KB's pins where possible; pin Linus's
  conflicting deps to compatible ranges.
- **GPU stack.** KB optionally uses torch+CUDA on non-Apple hardware. The `[kb]`
  install on Apple Silicon should default to CPU+MPS torch; document the
  GPU-extra (`pip install -e .[kb,gpu]`) for non-Apple installs.
- **Build time.** First-time pip install with KB extras is heavy. Acceptable
  one-time cost for the dev story; CI can cache aggressively.

## Out of scope for this spec

- Whether to also collapse into a single repo (we keep KB as submodule).
- Whether to ship KB as a PyPI package (deferrable — `pip install -e
  modules/KnowledgeBase` from the file path is enough for v0.6.0).
- Whether to migrate KB from conda to uv-only (separate decision, not load-bearing
  for the layered architecture).

## Success criterion

After this lands:

```
conda activate linus
pip install -e .[kb]
python -c "import linus.server, papers_analysis.extract"
```

…works and prints no errors. Both stacks are importable from one env, the
license boundary stays clean, and the standalone `papers` env path is preserved.
