# 2026-05-21 — KnowledgeBase hardcoded-paths fix (KB portability)

**Status:** proposed, 2026-05-21.
**Owner:** Maestro drafts; Dan reviews; Workers execute KB-side + Linus-side PRs.
**Target:** v0.6.0 (post-2026-05-25 reveal). For v0.5.0 reveal, the existing hardcoded
paths work as long as Dan runs the pipeline with his current setup; portability fix is
post-reveal cleanup.

---

## Motivation

The 2026-05-21 Streamlit-broken investigation surfaced that `modules/KnowledgeBase/`'s
pipeline modules have hardcoded path constants at module load time. Specifically:

| File | Constant | Path | Issue |
|---|---|---|---|
| `extract.py:42` | `LIBRARY_DIR` | `/Users/dbrowne/Documents/Papers Library` | hardcoded absolute — Dan-only |
| `metadata.py:23` | `PAPERS_DB` | `~/Library/Application Support/Papers/<UUID>.db` | hardcoded UUID — Dan's Papers app install only |
| `metadata.py:24` | `LIBRARY_DIR` | `~/Documents/Papers Library` | uses `Path.home()` — portable to any user with same dir convention |
| `summarize.py:60` | `_PAPERS_LIB` | `~/Documents/Papers Library` | same as above |
| `extract.py:43`, `cluster.py:85-87`, `graph.py:73-76`, `metadata.py:25-26`, `stats.py:37-38`, `summarize.py:59-61`, `vectorize.py:54-56`, `knowledge_graph.py:49` | various | `Path(__file__).parent.parent / "data" / ...` | module-relative — portable within the submodule but inflexible |

Two problems:

1. **`extract.py:42`'s absolute path is Dan-only.** Anyone forking the public release after
   the 2026-05-25 reveal cannot run the pipeline without editing this line. Friction for
   adoption, friction for CI.
2. **Inconsistency.** `extract.py:42` and `metadata.py:24` both define `LIBRARY_DIR` but
   with different definitions (absolute vs `Path.home()`-based). Bug surface.
3. **No env-var override mechanism.** Even where paths use `Path.home()`, users who store
   their PDFs elsewhere have to fork-edit. The Linus side already uses env vars
   (`LINUS_KB_OUTPUTS_DIR`, `LINUS_PAPERQA_DIR`); KB should mirror this pattern.

## Proposed fix — KB-side PR (`dbrowneup/KnowledgeBase`, `master` branch)

**Pattern:** every path constant moves from module-load constant to env-var-with-default
resolution. Defaults preserve current behavior; users override via env var.

### 1. Unified `papers_analysis/paths.py` module (new)

Single source of truth for all KB paths. Eliminates the `extract.py` vs `metadata.py`
`LIBRARY_DIR` inconsistency.

```python
"""KB path constants resolved from env vars with sane defaults.

Override any path by exporting the corresponding env var:

  KB_LIBRARY_DIR        -> input PDFs (default: ~/Documents/Papers Library)
  KB_PAPERS_DB          -> Papers app SQLite (default: macOS Papers app location)
  KB_DATA_DIR           -> KB's own data root (default: <repo>/data)
  KB_CACHE_DIR          -> per-PDF text/metadata cache (default: $KB_DATA_DIR/cache)
  KB_EMBEDDINGS_DIR     -> embedding artifacts (default: $KB_DATA_DIR/embeddings)
  KB_METADATA_DB        -> unified metadata DB (default: $KB_DATA_DIR/metadata.db)
  KB_OUTPUTS_DIR        -> pipeline outputs root (default: $KB_DATA_DIR/outputs)
  KB_CLUSTERS_DIR       -> clustering outputs (default: $KB_OUTPUTS_DIR/clusters)
  KB_GRAPH_DIR          -> paper graph outputs (default: $KB_OUTPUTS_DIR/graph)
  KB_KG_DIR             -> knowledge graph outputs (default: $KB_OUTPUTS_DIR/knowledge_graph)
"""
import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent  # modules/KnowledgeBase/

def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    return Path(raw).expanduser().resolve() if raw else default

LIBRARY_DIR = _env_path("KB_LIBRARY_DIR", Path.home() / "Documents" / "Papers Library")
PAPERS_DB = _env_path(
    "KB_PAPERS_DB",
    Path.home() / "Library" / "Application Support" / "Papers"
    / "f3292010-4d17-4707-a0b7-d909523af6c1.db",
)
DATA_DIR = _env_path("KB_DATA_DIR", _REPO_ROOT / "data")
CACHE_DIR = _env_path("KB_CACHE_DIR", DATA_DIR / "cache")
EMBEDDINGS_DIR = _env_path("KB_EMBEDDINGS_DIR", DATA_DIR / "embeddings")
METADATA_DB = _env_path("KB_METADATA_DB", DATA_DIR / "metadata.db")
OUTPUTS_DIR = _env_path("KB_OUTPUTS_DIR", DATA_DIR / "outputs")
CLUSTERS_DIR = _env_path("KB_CLUSTERS_DIR", OUTPUTS_DIR / "clusters")
GRAPH_DIR = _env_path("KB_GRAPH_DIR", OUTPUTS_DIR / "graph")
KG_DIR = _env_path("KB_KG_DIR", OUTPUTS_DIR / "knowledge_graph")
```

### 2. Update every pipeline module to import from `paths.py`

`extract.py`, `metadata.py`, `vectorize.py`, `cluster.py`, `graph.py`,
`stats.py`, `summarize.py`, `knowledge_graph.py`, `visualize.py` — each loses its local
path constants and imports from `papers_analysis.paths` instead.

### 3. README addendum

New section in KB README documenting the env var overrides + a worked example for
non-Dan users:

```
## Custom paths

By default the pipeline reads PDFs from ~/Documents/Papers Library and writes outputs
under <repo>/data/. To point at your own corpus:

  export KB_LIBRARY_DIR=/path/to/my/pdfs
  export KB_DATA_DIR=/path/to/my/kb-outputs
  python -m papers_analysis.extract

See papers_analysis/paths.py for the full list.
```

### 4. Tests

Hermetic test verifying env vars correctly override defaults. No new pipeline tests
(the pipeline isn't hermetic — needs real PDFs).

## Linus-side coordination — no code change required

The Linus side already uses env vars (`LINUS_KB_OUTPUTS_DIR`) and resolves them in
`src/linus/app/config.py`. After the KB-side PR ships and KB's submodule pin bumps,
the Linus config can optionally cross-set `LINUS_KB_OUTPUTS_DIR` from `KB_OUTPUTS_DIR`
if both are unset — but this is symmetric polish, not load-bearing.

## Ship plan

1. KB-side PR against `dbrowneup/KnowledgeBase` master: introduce `paths.py`, update
   pipeline modules, README. One PR, one agent dispatch (or Maestro-direct), reviewable.
2. Linus-side submodule pin bump (single small PR, mirrors SUB-1 pattern from
   `docs/specs/2026-05-19-kb-hackathon-prep.md`).
3. Verification: `python -m papers_analysis.extract` runs against both default location
   AND a `KB_LIBRARY_DIR=/tmp/test-corpus` override.

## Why post-reveal, not v0.5.0

Pre-reveal time is better spent on:
- Running the existing pipeline against Dan's actual corpus so the demo pages work.
- Fixing the remaining bug-sweep highs (8 of them).
- Final polish (assets, demo dry-run).

The KB portability fix is a clean, contained improvement that any open-source contributor
post-reveal can pick up — including someone who's not Dan. Making KB's first PR a
non-Dan-friendly portability fix would be a great way to welcome external contributors
to the project.
