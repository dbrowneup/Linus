"""KnowledgeBase-backed tools registered on the default registry.

Wraps :class:`linus.knowledge.KnowledgeBaseAdapter` as two tool callables that
return plain-dict results suitable for serialization back to a model:

* ``linus.knowledge.search_papers(query, limit=5)`` — keyword search.
* ``linus.knowledge.get_paper(sha256)`` — single-paper lookup.

The adapter is constructed lazily at first invocation and reused thereafter via
a module-level singleton. This matches the "open the SQLite read connection on
first query" lifecycle the adapter itself documents and avoids hammering the DB
when no tool call is in flight.

If the KB submodule isn't initialized or ``metadata.db`` has not been built, the
tools raise :class:`KnowledgeBaseUnavailableError` from the underlying adapter.
The server's tool-dispatch loop translates that into a structured ``role=tool``
error message so the model can recover gracefully (or, more often, the demo
script surfaces the remediation hint to Dan verbatim).
"""

from __future__ import annotations

from typing import Any

from linus.knowledge import KnowledgeBaseAdapter, Paper
from linus.tools.registry import tool


# Singleton adapter — created on demand. Tests can monkeypatch this attribute to
# inject a fixture-backed adapter; the indirection through ``_get_adapter`` keeps
# the patch site stable.
_adapter: KnowledgeBaseAdapter | None = None


def _get_adapter() -> KnowledgeBaseAdapter:
    """Return the process-wide :class:`KnowledgeBaseAdapter`, creating it lazily."""
    global _adapter
    if _adapter is None:
        _adapter = KnowledgeBaseAdapter()
    return _adapter


def _paper_to_dict(paper: Paper) -> dict[str, Any]:
    """Render a :class:`Paper` as a model-friendly dict.

    Only the fields a model is likely to cite back are included; size_mb and
    other infrastructure fields are dropped to keep the tool response compact.
    The shape is stable so the model can format consistent answers across calls.
    """
    return {
        "sha256": paper.sha256,
        "title": paper.title,
        "authors": paper.authors,
        "year": paper.year,
        "journal": paper.journal,
        "doi": paper.doi,
        "abstract": paper.abstract,
        "url": paper.url,
    }


@tool(name="linus.knowledge.search_papers")
def search_papers(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Search the KnowledgeBase paper corpus by keyword.

    Returns up to ``limit`` papers matching the query in title or abstract,
    ordered most-recent-first. The query is treated as whitespace-separated
    tokens that all must appear in either title or abstract (case-insensitive).
    """
    kb = _get_adapter()
    hits = kb.search_papers(query, limit=limit)
    return [_paper_to_dict(p) for p in hits]


@tool(name="linus.knowledge.get_paper")
def get_paper(sha256: str) -> dict[str, Any] | None:
    """Fetch a single paper from the KnowledgeBase by SHA256 hash.

    Returns the paper as a dict, or ``None`` if no row matches the hash.
    The SHA256 is the primary key in the KB ``papers`` table (it hashes the PDF
    bytes).
    """
    kb = _get_adapter()
    paper = kb.get_paper(sha256)
    if paper is None:
        return None
    return _paper_to_dict(paper)
