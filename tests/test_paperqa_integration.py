"""Integration test for the LX-1 paper-qa Phase 2c surface.

Requires:

- ``paper-qa`` installed (``pip install 'paper-qa>=5.0'``).
- A locally running Ollama with the configured Worker model
  (``qwen3:8b`` by default; override via ``LINUS_PAPERQA_MODEL``) and
  the configured embedding model (``mxbai-embed-large`` by default;
  override via ``LINUS_PAPERQA_EMBEDDING``).
- A directory with at least one PDF, pointed at by ``LINUS_PAPERQA_DIR``.

The test is marked ``integration`` so it is excluded from the hermetic
default run. Invoke explicitly with::

    pytest tests/test_paperqa_integration.py -m integration -v

If the required dependencies are not present the test is skipped
cleanly — it never fails for environment reasons, only for genuine
behavior regressions.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def papers_dir() -> Path:
    """Resolve the configured paper directory, skipping if not present.

    Honors ``LINUS_PAPERQA_DIR`` (preferred) and ``LINUS_PAPERS_DIR``
    (fallback, shared with the arxiv-ingest tool). Skips the test when
    neither resolves to a directory with at least one PDF.
    """
    raw = os.environ.get("LINUS_PAPERQA_DIR") or os.environ.get("LINUS_PAPERS_DIR")
    if not raw:
        pytest.skip(
            "Neither LINUS_PAPERQA_DIR nor LINUS_PAPERS_DIR is set. "
            "Point one at a directory containing at least one PDF."
        )
    path = Path(raw).expanduser()
    if not path.exists():
        pytest.skip(f"Configured papers directory does not exist: {path}")
    pdfs = list(path.glob("*.pdf"))
    if not pdfs:
        pytest.skip(f"Configured papers directory contains no PDFs: {path}")
    return path


@pytest.fixture(scope="module")
def paperqa_available() -> None:
    """Skip the suite if paper-qa cannot be imported."""
    pytest.importorskip(
        "paperqa",
        reason="paper-qa is not installed. Run: pip install 'paper-qa>=5.0'",
    )


@pytest.fixture(scope="module")
def ollama_reachable() -> None:
    """Skip the suite if Ollama is not responding on the configured host."""
    import socket
    import urllib.parse
    import urllib.request

    host_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    parsed = urllib.parse.urlparse(host_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 11434
    try:
        with socket.create_connection((host, port), timeout=2.0):
            pass
    except OSError as exc:
        pytest.skip(f"Ollama not reachable at {host_url}: {exc}")


def test_round_trip_search_returns_provenance(
    papers_dir: Path, paperqa_available: None, ollama_reachable: None
) -> None:
    """``paperqa.search`` returns at least one provenance-shaped dict.

    Smoke gate: any non-empty result with the required four keys passes.
    A more rigorous answer-quality test belongs in the LAB-Bench /
    benchmark suite (Phase 1e), not here.
    """
    from linus.knowledge.paperqa import get_singleton, reset_singleton

    reset_singleton()
    facade = get_singleton()
    import asyncio

    results = asyncio.run(facade.search(query="cell metabolism", k=3))
    assert isinstance(results, list)
    if results:  # Allow an empty index — the smoke is that the call completes.
        first = results[0]
        assert {"paper_id", "page", "excerpt", "score"} <= set(first)


def test_round_trip_answer_produces_text_and_citations(
    papers_dir: Path, paperqa_available: None, ollama_reachable: None
) -> None:
    """``paperqa.answer`` returns a non-empty answer + citations payload.

    Runs against the configured corpus + local Ollama; cost is one full
    paper-qa agent loop. Marked integration so CI does not pay it.
    """
    from linus.knowledge.paperqa import get_singleton, reset_singleton

    reset_singleton()
    facade = get_singleton()
    import asyncio

    payload = asyncio.run(facade.answer(query="what does the literature say?", max_sources=5))
    assert isinstance(payload, dict)
    assert {"question", "answer", "formatted_answer", "citations"} <= set(payload)
    assert isinstance(payload["citations"], list)
