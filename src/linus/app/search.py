"""Search-page helpers — thin wrapper over the KnowledgeRetriever contract.

The Cluster Explorer (B.3) shows the topic structure; this module
powers the Search page (B.6) by letting the user query the corpus by
keyword (and, when SPECTER2 is wired, by semantic similarity).

Routing through :class:`linus.knowledge.KnowledgeRetriever` ensures
the UI and the Archimedes-facing tool surface share one retrieval
contract — same fusion math, same provenance, same hit shape.
"""

from __future__ import annotations

from dataclasses import dataclass

from linus.knowledge import (
    KnowledgeBaseAdapter,
    KnowledgeBaseUnavailableError,
    KnowledgeRetriever,
    RetrievalHit,
    RetrievalResult,
)


@dataclass(frozen=True)
class SearchResult:
    """One row of search results, flattened for st.dataframe rendering."""

    sha256: str
    title: str | None
    year: int | None
    authors: str | None
    abstract: str | None
    score: float
    provenance: str  # comma-joined method names


def run_search(
    query: str,
    method: str,
    top_k: int = 20,
    adapter: KnowledgeBaseAdapter | None = None,
) -> tuple[list[SearchResult], list[str]]:
    """Run a search; return ``(rows, methods_skipped)``.

    ``method`` is one of ``"keyword"``, ``"semantic"``, or ``"hybrid"``.
    For ``"hybrid"``, both methods run (the gateway auto-skips
    unimplemented ones). For an explicit method, raises
    :class:`NotImplementedError` from the underlying gateway if the
    method isn't wired — the caller should surface that to the UI as a
    descriptive notice.
    """
    if adapter is None:
        adapter = KnowledgeBaseAdapter()

    retriever = KnowledgeRetriever(adapter)

    if method == "hybrid":
        result = retriever.retrieve(query, top_k=top_k)
    else:
        result = retriever.retrieve(query, top_k=top_k, methods=[method])  # type: ignore[list-item]

    return [_to_row(hit) for hit in result.hits], list(result.methods_skipped)


def _to_row(hit: RetrievalHit) -> SearchResult:
    return SearchResult(
        sha256=hit.paper.sha256,
        title=hit.paper.title,
        year=hit.paper.year,
        authors=hit.paper.authors,
        abstract=hit.paper.abstract,
        score=hit.score,
        provenance=", ".join(hit.provenance),
    )


__all__ = [
    "SearchResult",
    "KnowledgeBaseUnavailableError",
    "RetrievalResult",
    "run_search",
]
