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

``LINUS_PAPERQA_DIR`` / ``LINUS_PAPERS_DIR``
    Directory containing PDFs indexed by the Paper Q&A page
    (:mod:`linus.knowledge.paperqa`). ``LINUS_PAPERQA_DIR`` wins when both
    are set; ``LINUS_PAPERS_DIR`` is also honored for parity with
    :mod:`linus.tools.arxiv_ingest`. Default: ``~/.linus/papers``. The
    directory is **auto-created** by :func:`resolve_paperqa_dir` on first
    access with a README dropped inside so the user knows what belongs
    there — see bug 4 of the 2026-05-22 reveal-prep list (the dir not
    existing on a fresh machine used to surface as a hard
    ``PaperQAConfigError``).

``LINUS_SERVER_URL``
    Base URL for the Linus orchestration server (FastAPI app at
    ``src/linus/server.py``). Default: ``http://localhost:8000``.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


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


# ── Paper Q&A papers directory ───────────────────────────────────────────

#: Filename of the README dropped into a freshly-created papers directory.
PAPERQA_README_NAME: str = "README.md"

#: Body of the README that :func:`resolve_paperqa_dir` writes when the
#: papers directory is created from scratch. Kept short and operational —
#: the README's job is to tell a human stumbling into the directory what
#: belongs there and how it gets used.
PAPERQA_README_BODY: str = """# Linus Paper Q&A — drop PDFs here

Files in this directory are indexed by the Linus Paper Q&A page. Drop PDFs here
(one paper per file) and they'll be picked up on next index refresh.

This directory was auto-created by Linus on first access. To use a different
location, set the ``LINUS_PAPERQA_DIR`` environment variable to the path you
want before launching the Linus Streamlit UI or orchestration server.
"""


def paperqa_dir_path() -> Path:
    """Resolve the configured Paper Q&A papers directory **without touching the filesystem**.

    Resolution order (matches :func:`linus.knowledge.paperqa._papers_dir`):

    1. ``LINUS_PAPERQA_DIR`` environment variable, if set.
    2. ``LINUS_PAPERS_DIR`` environment variable, if set (shared with
       :mod:`linus.tools.arxiv_ingest`).
    3. Default ``~/.linus/papers``.

    This is the pure-resolution form — it does NOT create the directory or
    write the README. Use :func:`resolve_paperqa_dir` for the auto-create
    side effect.
    """
    raw = os.environ.get("LINUS_PAPERQA_DIR") or os.environ.get("LINUS_PAPERS_DIR")
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".linus" / "papers"


def resolve_paperqa_dir(*, create: bool = True) -> Path:
    """Resolve the Paper Q&A papers directory, auto-creating it on first access.

    When ``create=True`` (the default) and the resolved path does not
    exist as a directory, the directory is created (``mkdir -p`` shape)
    and a ``README.md`` is written inside with :data:`PAPERQA_README_BODY`
    so a human discovering the directory later knows what belongs there.
    This is the durable fix for the "papers dir missing → hard
    ``PaperQAConfigError``" bug surfaced in the 2026-05-22 reveal-prep
    bug list (bug 4): instead of failing, Linus now greets a fresh
    machine with an empty papers directory and a gentle "drop PDFs here"
    UX hint.

    If the resolved path exists but is a non-directory (e.g., somebody
    pointed ``LINUS_PAPERQA_DIR`` at a regular file), the path is
    returned unchanged — the caller (paper-qa wrapper, UI page) can
    decide whether to treat that as a config error. This function does
    not raise.

    Pass ``create=False`` to short-circuit the side effect (useful for
    diagnostic surfaces that want to display the resolved path without
    materializing the directory).
    """
    papers_dir = paperqa_dir_path()
    if not create:
        return papers_dir

    try:
        if papers_dir.exists():
            # Existing directory (or file at that path) — don't touch.
            return papers_dir
        papers_dir.mkdir(parents=True, exist_ok=True)
        readme_path = papers_dir / PAPERQA_README_NAME
        if not readme_path.exists():
            readme_path.write_text(PAPERQA_README_BODY, encoding="utf-8")
        logger.info(
            "Auto-created Linus Paper Q&A papers directory at %s "
            "(populate with PDFs to enable the paper-qa tool).",
            papers_dir,
        )
    except OSError as exc:
        # Filesystem error (permission denied, read-only filesystem,
        # disk full). Log and return the resolved path unchanged so the
        # caller can decide how to surface the failure. Tests at the
        # auto-create boundary can monkeypatch ``Path.mkdir`` to exercise
        # this path.
        logger.warning(
            "Failed to auto-create Linus Paper Q&A papers directory at %s: %s",
            papers_dir,
            exc,
        )

    return papers_dir


#: Cached resolved papers directory, materialized on import. The
#: directory + README are created at import time so any front-end that
#: imports ``linus.app.config`` (Streamlit UI, server-side tool registry)
#: gets the same auto-created shape without having to call the function
#: explicitly. The constant is the single source of truth for downstream
#: pages and the paper-qa wrapper.
PAPERQA_DIR: Path = resolve_paperqa_dir()


def config_summary() -> dict[str, str]:
    """Return the resolved config as a dict for display in the landing page."""
    return {
        "LINUS_KB_OUTPUTS_DIR": str(KB_OUTPUTS_DIR),
        "LINUS_KB_METADATA_DB": str(KB_METADATA_DB),
        "LINUS_KB_EMBEDDINGS_DIR": str(KB_EMBEDDINGS_DIR),
        "LINUS_PAPERQA_DIR": str(PAPERQA_DIR),
        "LINUS_SERVER_URL": SERVER_URL,
    }
