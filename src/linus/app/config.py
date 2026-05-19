"""Environment-driven configuration for the Linus Streamlit UI.

All KB-artifact paths and the Linus server URL are read from environment
variables with sensible defaults. Pages should import these constants
rather than hard-coding paths.

Environment variables
---------------------

``LINUS_KB_OUTPUTS_DIR``
    Root directory containing KnowledgeBase pipeline outputs
    (``hierarchy.json``, ``labels_*.json``, ``topics_*.json``,
    ``umap_*.npy``, ``graph/``, ``knowledge_graph/``, corpus stat PNGs).
    Default: ``modules/KnowledgeBase/data/outputs/`` relative to the
    repository root.

``LINUS_KB_METADATA_DB``
    Path to the unified per-paper metadata SQLite database.
    Default: ``modules/KnowledgeBase/data/metadata.db``.

``LINUS_KB_EMBEDDINGS_DIR``
    Directory containing ``specter2.npy`` and ``tfidf_matrix.npz`` for
    the search page. Default: ``modules/KnowledgeBase/data/embeddings/``.

``LINUS_SERVER_URL``
    Base URL for the Linus orchestration server (FastAPI app at
    ``src/linus/server.py``). Default: ``http://localhost:8000``.
"""

from __future__ import annotations

import os
from pathlib import Path


def _repo_root() -> Path:
    """Resolve the Linus repository root from this file's location.

    ``src/linus/app/config.py`` → ``parents[3]`` is the repo root.
    """
    return Path(__file__).resolve().parents[3]


def _path_from_env(var: str, default_rel: str) -> Path:
    """Read a path from the environment, falling back to a repo-relative default."""
    raw = os.environ.get(var)
    if raw:
        return Path(raw).expanduser().resolve()
    return _repo_root() / default_rel


KB_OUTPUTS_DIR: Path = _path_from_env("LINUS_KB_OUTPUTS_DIR", "modules/KnowledgeBase/data/outputs")
KB_METADATA_DB: Path = _path_from_env("LINUS_KB_METADATA_DB", "modules/KnowledgeBase/data/metadata.db")
KB_EMBEDDINGS_DIR: Path = _path_from_env("LINUS_KB_EMBEDDINGS_DIR", "modules/KnowledgeBase/data/embeddings")
SERVER_URL: str = os.environ.get("LINUS_SERVER_URL", "http://localhost:8000")


def config_summary() -> dict[str, str]:
    """Return the resolved config as a dict for display in the landing page."""
    return {
        "LINUS_KB_OUTPUTS_DIR": str(KB_OUTPUTS_DIR),
        "LINUS_KB_METADATA_DB": str(KB_METADATA_DB),
        "LINUS_KB_EMBEDDINGS_DIR": str(KB_EMBEDDINGS_DIR),
        "LINUS_SERVER_URL": SERVER_URL,
    }
