"""Tests for :mod:`linus.app.kg_render`.

Hermetic: builds small NetworkX MultiDiGraphs by hand to exercise the
filter + stat + render helpers without needing the KB GraphML file.
"""

from __future__ import annotations

import networkx as nx
import pytest

from linus.app.kg_render import compute_stats, filter_subgraph, render_pyvis_html


@pytest.fixture()
def tiny_kg() -> nx.MultiDiGraph:
    """Small toy KG: 2 papers, 3 entities, 5 edges."""
    g: nx.MultiDiGraph = nx.MultiDiGraph()
    g.add_node("paper:1", type="Paper", title="Paper One", label="P1")
    g.add_node("paper:2", type="Paper", title="Paper Two", label="P2")
    g.add_node("ent:gene", type="Entity", label="BRCA1", entity_type="GENE_OR_GENE_PRODUCT")
    g.add_node("ent:dis", type="Entity", label="cancer", entity_type="DISEASE")
    g.add_node("ent:chem", type="Entity", label="aspirin", entity_type="CHEMICAL")

    g.add_edge("paper:1", "ent:gene", edge_type="mentions", relation="mentions")
    g.add_edge("paper:1", "ent:dis", edge_type="mentions", relation="mentions")
    g.add_edge("paper:2", "ent:gene", edge_type="mentions", relation="mentions")
    g.add_edge("ent:gene", "ent:dis", edge_type="rebel", relation="causes")
    g.add_edge("ent:chem", "ent:dis", edge_type="rebel", relation="treats")
    return g


def test_compute_stats_counts_correctly(tiny_kg: nx.MultiDiGraph) -> None:
    stats = compute_stats(tiny_kg)
    assert stats.total_nodes == 5
    assert stats.total_edges == 5
    assert stats.paper_nodes == 2
    assert stats.entity_nodes == 3
    assert set(stats.entity_categories) == {"GENE_OR_GENE_PRODUCT", "DISEASE", "CHEMICAL"}


def test_filter_drops_paper_nodes(tiny_kg: nx.MultiDiGraph) -> None:
    sub = filter_subgraph(tiny_kg, keep_paper=False, keep_entity=True)
    assert sub.number_of_nodes() == 3
    types = {data.get("type") for _, data in sub.nodes(data=True)}
    assert types == {"Entity"}


def test_filter_drops_entity_nodes(tiny_kg: nx.MultiDiGraph) -> None:
    sub = filter_subgraph(tiny_kg, keep_paper=True, keep_entity=False)
    assert sub.number_of_nodes() == 2
    types = {data.get("type") for _, data in sub.nodes(data=True)}
    assert types == {"Paper"}


def test_filter_by_entity_category(tiny_kg: nx.MultiDiGraph) -> None:
    sub = filter_subgraph(
        tiny_kg,
        keep_paper=True,
        keep_entity=True,
        allowed_categories=["GENE_OR_GENE_PRODUCT", "DISEASE"],
    )
    # papers + gene + disease = 4 nodes (chem dropped)
    assert sub.number_of_nodes() == 4
    assert "ent:chem" not in sub.nodes


def test_filter_min_degree(tiny_kg: nx.MultiDiGraph) -> None:
    # ent:chem has degree 1; ent:dis has degree 4. min_degree=3 keeps only nodes with deg>=3.
    sub = filter_subgraph(tiny_kg, min_degree=3)
    degrees = dict(sub.degree())
    assert all(d >= 3 for d in degrees.values())


def test_filter_empty_category_list_keeps_no_entities(tiny_kg: nx.MultiDiGraph) -> None:
    """Passing allowed_categories=[] should drop all entity nodes (no allowed match)."""
    sub = filter_subgraph(tiny_kg, allowed_categories=[])
    types = {data.get("type") for _, data in sub.nodes(data=True)}
    assert "Entity" not in types
    assert types == {"Paper"}


def test_render_pyvis_html_returns_valid_html(tiny_kg: nx.MultiDiGraph) -> None:
    html = render_pyvis_html(tiny_kg)
    assert isinstance(html, str)
    assert "<html" in html.lower()
    assert "</html>" in html.lower()
    # Vendored vis.js means the doc carries a vis-network reference.
    assert "vis" in html.lower()


def test_render_handles_empty_graph_gracefully() -> None:
    g: nx.MultiDiGraph = nx.MultiDiGraph()
    html = render_pyvis_html(g)
    assert isinstance(html, str)
    assert "<html" in html.lower()


def test_render_distinguishes_paper_and_entity_colors(tiny_kg: nx.MultiDiGraph) -> None:
    """Paper and entity nodes should use different colors in the rendered HTML."""
    html = render_pyvis_html(tiny_kg, paper_color="#001122", entity_color="#FF8800")
    assert "001122" in html.lower() or "#001122" in html
    assert "ff8800" in html.lower() or "#FF8800" in html
