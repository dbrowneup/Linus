"""Unified retrieval gateway over the KnowledgeBase corpus.

This module exposes :class:`KnowledgeRetriever` — a single contract for
research-grounded retrieval that fuses three orthogonal signals:

- **keyword** — TF-IDF / SQL ``LIKE`` over title and abstract (via the
  existing :class:`linus.knowledge.adapter.KnowledgeBaseAdapter`).
- **semantic** — SPECTER2 dense-embedding cosine similarity. Interface
  fully typed; implementation pending sentence-transformers + SPECTER2
  adapter install.
- **graph** — knowledge-graph traversal (REBEL triples + SciSpacy NER
  edges). Interface defined; implementation pending KG load layer.

The fused score is a weighted sum of per-method scores with
configurable weights. Provenance is preserved per hit so downstream
callers (e.g., a portfolio agent's reasoning trace) can cite which
methods contributed evidence.

This v1 ships keyword search only. Semantic and graph methods raise
:class:`NotImplementedError` with documented install pointers when
requested directly; when methods are auto-selected (``methods=None``),
unavailable methods are silently skipped and the result's
``methods_used`` field reflects what actually ran.

Why the contract matters even with a thin impl: the Archimedes project
(submodule consumer of Linus) lifts this interface verbatim as the
research-grounded engine for paper-grounded trading strategies. The
shape of :class:`RetrievalHit`, :class:`RetrievalResult`, and
:meth:`KnowledgeRetriever.retrieve` is therefore frozen behavior; bug
fixes welcome, but field renames or argument removals require an ADR.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Literal

from linus.knowledge.adapter import KnowledgeBaseAdapter, Paper

# Method-name literal used across the public surface.
RetrievalMethod = Literal["keyword", "semantic", "graph"]
_ALL_METHODS: tuple[RetrievalMethod, ...] = ("keyword", "semantic", "graph")

# Default fusion weights. Mirrors the KB similarity-graph default
# (TF-IDF weight 0.3, SPECTER2 weight 0.7) per its Phase 5 design notes.
# Graph weight starts at 0.0 because the graph method is unimplemented
# in v1 — callers can override at retrieve() time.
DEFAULT_WEIGHTS: dict[RetrievalMethod, float] = {
    "keyword": 0.3,
    "semantic": 0.7,
    "graph": 0.0,
}


@dataclass(frozen=True)
class RetrievalHit:
    """One ranked result from :meth:`KnowledgeRetriever.retrieve`.

    The :attr:`paper` field carries the full bibliographic record from
    the KnowledgeBase. :attr:`score` is the fused score across all
    contributing methods. :attr:`method_scores` maps each method name
    to its raw per-method score (post-normalization), so a caller
    inspecting a reasoning trace can see *why* a paper ranked high.
    :attr:`provenance` lists the methods whose score met the per-method
    inclusion threshold (default: > 0).
    """

    paper: Paper
    score: float
    method_scores: dict[str, float]
    provenance: list[str]


@dataclass(frozen=True)
class RetrievalResult:
    """The full response from :meth:`KnowledgeRetriever.retrieve`.

    :attr:`hits` is sorted by :attr:`RetrievalHit.score` descending.
    :attr:`methods_used` reflects what actually ran (vs. what was
    requested) — semantic/graph methods that aren't yet implemented
    appear in :attr:`methods_skipped` when methods were auto-selected,
    or raise :class:`NotImplementedError` when explicitly requested.
    :attr:`metadata` carries timing and corpus-size info for tracing.
    """

    query: str
    methods_used: list[str]
    methods_skipped: list[str]
    hits: list[RetrievalHit]
    metadata: dict[str, object] = field(default_factory=dict)


class KnowledgeRetriever:
    """Hybrid retrieval gateway over the KnowledgeBase corpus.

    Wraps an existing :class:`KnowledgeBaseAdapter` and exposes one
    :meth:`retrieve` method that dispatches to one or more retrieval
    methods, fuses scores, and returns a ranked
    :class:`RetrievalResult`.

    Example::

        from linus.knowledge import KnowledgeBaseAdapter, KnowledgeRetriever

        retriever = KnowledgeRetriever(KnowledgeBaseAdapter())
        result = retriever.retrieve("long-read sequencing", top_k=10)
        for hit in result.hits:
            print(hit.score, hit.provenance, hit.paper.title)
    """

    def __init__(
        self,
        adapter: KnowledgeBaseAdapter,
        weights: dict[RetrievalMethod, float] | None = None,
    ) -> None:
        self.adapter = adapter
        self.weights = dict(weights) if weights else dict(DEFAULT_WEIGHTS)

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        methods: list[RetrievalMethod] | None = None,
        weights: dict[RetrievalMethod, float] | None = None,
    ) -> RetrievalResult:
        """Run hybrid retrieval and return a fused ranked result.

        :param query: The natural-language query string.
        :param top_k: Maximum number of hits to return after fusion.
        :param methods: Restrict to a subset of methods (e.g.
            ``["keyword"]``). When ``None``, all available methods run
            and unavailable methods are skipped silently. When a
            method is explicitly requested but unimplemented, the call
            raises :class:`NotImplementedError`.
        :param weights: Override the fusion weights for this call. Any
            method name omitted from the dict falls back to the
            instance's default weights.
        """
        requested = list(methods) if methods else list(_ALL_METHODS)
        explicit_request = methods is not None
        effective_weights = dict(self.weights)
        if weights:
            effective_weights.update(weights)

        per_method_results: dict[str, dict[str, float]] = {}
        methods_used: list[str] = []
        methods_skipped: list[str] = []

        started = time.perf_counter()

        for method in requested:
            try:
                scored = self._dispatch_method(method, query, top_k)
            except NotImplementedError:
                if explicit_request:
                    raise
                methods_skipped.append(method)
                continue
            per_method_results[method] = scored
            methods_used.append(method)

        fused = self._fuse(per_method_results, effective_weights)
        hits = self._materialize_hits(fused, per_method_results, top_k)

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return RetrievalResult(
            query=query,
            methods_used=methods_used,
            methods_skipped=methods_skipped,
            hits=hits,
            metadata={
                "elapsed_ms": elapsed_ms,
                "weights": effective_weights,
                "top_k": top_k,
            },
        )

    # ── per-method implementations ──────────────────────────────────────────

    def _dispatch_method(
        self,
        method: RetrievalMethod,
        query: str,
        top_k: int,
    ) -> dict[str, float]:
        """Route to the per-method retrieval and return ``{sha256: score}``."""
        if method == "keyword":
            return self._keyword(query, top_k)
        if method == "semantic":
            return self._semantic(query, top_k)
        if method == "graph":
            return self._graph(query, top_k)
        raise ValueError(f"Unknown retrieval method: {method!r}")

    def _keyword(self, query: str, top_k: int) -> dict[str, float]:
        """Keyword search via the existing adapter's LIKE backend.

        Scores are rank-based: ``1.0`` for the top hit, linearly
        decaying to ``1/N`` for the N-th. Crude but stable and
        order-preserving across requests.
        """
        papers = self.adapter.search_papers(query, limit=top_k)
        n = len(papers)
        if n == 0:
            return {}
        return {paper.sha256: 1.0 - (i / n) for i, paper in enumerate(papers)}

    def _semantic(self, query: str, top_k: int) -> dict[str, float]:
        """Semantic search via SPECTER2 query-embedding cosine.

        Not yet implemented in v1. The contract is fully typed; an
        implementation lifts the SPECTER2 model-load + cosine-batch
        pattern from ``modules/KnowledgeBase/papers_analysis/vectorize.py``.
        Requires the ``sentence-transformers`` and ``allenai/specter2_base``
        + proximity-adapter dependencies.
        """
        raise NotImplementedError(
            "Semantic retrieval (SPECTER2) is not yet wired in this Linus build. "
            "To enable, install sentence-transformers and the SPECTER2 model: "
            "    pip install sentence-transformers"
            "    python -c \"from transformers import AutoModel; AutoModel.from_pretrained('allenai/specter2_base')\""
            "Then implement KnowledgeRetriever._semantic to embed the query and cosine "
            "against modules/KnowledgeBase/data/embeddings/specter2.npy "
            "(joined on specter2_sha256s.json). See "
            "modules/KnowledgeBase/papers_analysis/vectorize.py for the reference pattern."
        )

    def _graph(self, query: str, top_k: int) -> dict[str, float]:
        """Knowledge-graph retrieval (REBEL triples + SciSpacy NER edges).

        Not yet implemented in v1. The contract is fully typed; an
        implementation loads
        ``modules/KnowledgeBase/data/outputs/knowledge_graph/kg_graph.graphml``
        with NetworkX, performs entity-anchored neighborhood expansion
        from the query, and ranks papers by graph-proximity score.
        """
        raise NotImplementedError(
            "Graph retrieval (REBEL/NER knowledge graph) is not yet wired in this Linus build. "
            "To enable, ensure the KB Phase 6 pipeline has been run "
            "(python -m papers_analysis.knowledge_graph in modules/KnowledgeBase) and "
            "then implement KnowledgeRetriever._graph to load kg_graph.graphml via "
            "networkx.read_graphml, perform entity-anchored neighborhood expansion "
            "from the query, and rank papers by graph-proximity score."
        )

    # ── fusion ──────────────────────────────────────────────────────────────

    def _fuse(
        self,
        per_method: dict[str, dict[str, float]],
        weights: dict[RetrievalMethod, float],
    ) -> dict[str, float]:
        """Weighted sum across methods. Missing methods contribute 0."""
        all_shas: set[str] = set()
        for scores in per_method.values():
            all_shas.update(scores.keys())

        fused: dict[str, float] = {}
        for sha in all_shas:
            total = 0.0
            for method, scores in per_method.items():
                method_score = scores.get(sha, 0.0)
                weight = weights.get(method, 0.0)
                total += weight * method_score
            fused[sha] = total
        return fused

    def _materialize_hits(
        self,
        fused: dict[str, float],
        per_method: dict[str, dict[str, float]],
        top_k: int,
    ) -> list[RetrievalHit]:
        """Build :class:`RetrievalHit` records sorted by fused score desc."""
        ranked = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)[:top_k]

        hits: list[RetrievalHit] = []
        for sha, score in ranked:
            paper = self.adapter.get_paper(sha)
            if paper is None:
                # Shouldn't happen — every sha came from an adapter result —
                # but guard against schema drift.
                continue
            method_scores = {method: scores[sha] for method, scores in per_method.items() if sha in scores}
            provenance = [m for m, s in method_scores.items() if s > 0.0]
            hits.append(
                RetrievalHit(
                    paper=paper,
                    score=score,
                    method_scores=method_scores,
                    provenance=provenance,
                )
            )
        return hits
