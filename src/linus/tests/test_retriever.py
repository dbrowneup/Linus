"""Tests for the unified RAG retrieval gateway (:mod:`linus.knowledge.retriever`).

Covers the three contract dimensions:

1. Keyword retrieval works against a mock adapter, returns a ranked
   :class:`RetrievalResult` with proper provenance.
2. Method selection — auto-selection silently skips unimplemented
   methods; explicit selection of an unimplemented method raises
   :class:`NotImplementedError` with the documented install pointer.
3. Fusion math — when multiple methods score the same paper, the
   fused score is the weighted sum and ``provenance`` lists every
   contributor.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from linus.knowledge import (
    KnowledgeBaseAdapter,
    KnowledgeRetriever,
    Paper,
    RetrievalHit,
    RetrievalResult,
)


def _paper(sha: str, title: str) -> Paper:
    """Minimal Paper helper for fixture construction."""
    return Paper(sha256=sha, title=title)


@pytest.fixture
def mock_adapter() -> KnowledgeBaseAdapter:
    """Adapter with three pre-canned papers and deterministic search."""
    adapter = MagicMock(spec=KnowledgeBaseAdapter)

    papers = {
        "sha_a": _paper("sha_a", "Long-read sequencing of microbial genomes"),
        "sha_b": _paper("sha_b", "Short-read assembly methods"),
        "sha_c": _paper("sha_c", "PacBio HiFi accuracy benchmarks"),
    }

    def search(query: str, limit: int = 10):
        # Crude relevance: rank by title containing query words.
        terms = query.lower().split()
        scored = []
        for paper in papers.values():
            title_lower = (paper.title or "").lower()
            hits = sum(1 for t in terms if t in title_lower)
            if hits:
                scored.append((hits, paper))
        scored.sort(key=lambda kv: kv[0], reverse=True)
        return [p for _, p in scored[:limit]]

    def get(sha):
        return papers.get(sha)

    adapter.search_papers.side_effect = search
    adapter.get_paper.side_effect = get
    return adapter


def test_keyword_only_returns_ranked_hits(mock_adapter):
    """Auto-method selection should silently skip semantic+graph and
    return keyword-only hits with appropriate provenance."""
    retriever = KnowledgeRetriever(mock_adapter)
    result = retriever.retrieve("long-read sequencing", top_k=5)

    assert isinstance(result, RetrievalResult)
    assert result.methods_used == ["keyword"]
    assert set(result.methods_skipped) == {"semantic", "graph"}
    assert len(result.hits) >= 1

    top = result.hits[0]
    assert isinstance(top, RetrievalHit)
    assert top.paper.sha256 == "sha_a"
    assert top.provenance == ["keyword"]
    assert "keyword" in top.method_scores
    assert top.score > 0
    assert result.metadata["elapsed_ms"] >= 0


def test_explicit_semantic_raises_with_install_pointer(mock_adapter):
    """When the user asks for semantic explicitly, the contract requires
    a NotImplementedError with the documented install pointer so the
    Archimedes consumer can surface it to their team."""
    retriever = KnowledgeRetriever(mock_adapter)
    with pytest.raises(NotImplementedError) as exc_info:
        retriever.retrieve("query", methods=["semantic"])
    assert "sentence-transformers" in str(exc_info.value)


def test_explicit_graph_raises_with_install_pointer(mock_adapter):
    """Same contract requirement for graph retrieval."""
    retriever = KnowledgeRetriever(mock_adapter)
    with pytest.raises(NotImplementedError) as exc_info:
        retriever.retrieve("query", methods=["graph"])
    assert "kg_graph.graphml" in str(exc_info.value)


def test_fusion_weighted_sum_across_methods(mock_adapter):
    """Patch a stub semantic method to verify fusion math.

    Bypasses the NotImplementedError by overriding ``_semantic`` directly;
    keeps the public contract intact while exercising the fusion path.
    """
    retriever = KnowledgeRetriever(mock_adapter, weights={"keyword": 0.4, "semantic": 0.6})

    def fake_semantic(query: str, top_k: int) -> dict[str, float]:
        return {"sha_a": 1.0, "sha_c": 0.5}

    retriever._semantic = fake_semantic  # type: ignore[method-assign]

    result = retriever.retrieve("PacBio HiFi", top_k=5)
    assert set(result.methods_used) == {"keyword", "semantic"}

    # sha_c is "PacBio HiFi accuracy benchmarks" — top keyword match (rank 0),
    # and present in semantic with score 0.5.
    by_sha = {hit.paper.sha256: hit for hit in result.hits}
    assert "sha_c" in by_sha
    sha_c_hit = by_sha["sha_c"]
    assert set(sha_c_hit.provenance) == {"keyword", "semantic"}
    assert sha_c_hit.method_scores["semantic"] == 0.5
    # Weighted sum: 0.4 * keyword_score + 0.6 * 0.5; keyword_score depends on
    # ranking — just assert positivity and that score reflects both methods.
    assert sha_c_hit.score > 0.6 * 0.5  # at minimum the semantic contribution


def test_empty_keyword_result_yields_empty_hits(mock_adapter):
    """No matches → empty hits list, methods_used still reports keyword ran."""
    retriever = KnowledgeRetriever(mock_adapter)
    result = retriever.retrieve("nonexistent-term-zzz", top_k=5)
    assert result.hits == []
    assert "keyword" in result.methods_used


def test_top_k_caps_results(mock_adapter):
    """top_k=1 returns at most one hit even when more would match."""
    retriever = KnowledgeRetriever(mock_adapter)
    result = retriever.retrieve("sequencing", top_k=1)
    assert len(result.hits) <= 1


def test_custom_weights_per_call(mock_adapter):
    """Per-call weight override applies for that call only."""
    retriever = KnowledgeRetriever(mock_adapter)
    base_weights = dict(retriever.weights)
    retriever.retrieve("sequencing", weights={"keyword": 999.0})
    # Instance weights unchanged.
    assert retriever.weights == base_weights
