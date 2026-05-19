"""Knowledge-graph rendering helpers for the Streamlit KG page.

Bridges the KnowledgeBase Phase 6 GraphML output
(``kg_graph.graphml`` — REBEL triples + SciSpacy NER edges over Paper
+ Entity nodes) to a pyvis interactive HTML render that's embedded
inside a Streamlit ``components.v1.html`` iframe.

Split out from ``5_knowledge_graph.py`` so the load + filter + render
logic is independently testable and reusable from elsewhere (e.g. a
future tool-call surface that emits a graph view inline).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import networkx as nx
from pyvis.network import Network


@dataclass(frozen=True)
class KGStats:
    """Headline counts for the KG, displayed above the filter row."""

    total_nodes: int
    total_edges: int
    paper_nodes: int
    entity_nodes: int
    entity_categories: list[str]


def load_kg(graphml_path: Path) -> nx.MultiDiGraph:
    """Load a KG GraphML file as a NetworkX :class:`MultiDiGraph`.

    The KB Phase 6 pipeline produces a :class:`MultiDiGraph` with two
    node types (``Paper``, ``Entity``) and two edge types (``rebel``
    typed Wikidata relations, ``mentions`` from NER). NetworkX's
    ``read_graphml`` returns a generic ``Graph`` / ``DiGraph`` /
    ``MultiDiGraph`` depending on what was serialized — we coerce to
    MultiDiGraph downstream so the render code can assume one type.
    """
    g = nx.read_graphml(graphml_path)
    if not isinstance(g, nx.MultiDiGraph):
        if g.is_directed():
            converted: nx.MultiDiGraph = nx.MultiDiGraph(g)
        else:
            converted = nx.MultiDiGraph(g.to_directed())
        return converted
    return g


def compute_stats(g: nx.MultiDiGraph) -> KGStats:
    """Summarize node + edge counts and the available entity categories."""
    paper_nodes = 0
    entity_nodes = 0
    categories: set[str] = set()
    for _, data in g.nodes(data=True):
        node_type = data.get("type") or data.get("node_type") or ""
        if str(node_type).lower() == "paper":
            paper_nodes += 1
        elif str(node_type).lower() == "entity":
            entity_nodes += 1
        category = data.get("entity_type") or data.get("category")
        if category:
            categories.add(str(category))
    return KGStats(
        total_nodes=g.number_of_nodes(),
        total_edges=g.number_of_edges(),
        paper_nodes=paper_nodes,
        entity_nodes=entity_nodes,
        entity_categories=sorted(categories),
    )


def filter_subgraph(
    g: nx.MultiDiGraph,
    *,
    keep_paper: bool = True,
    keep_entity: bool = True,
    allowed_categories: Iterable[str] | None = None,
    min_degree: int = 0,
) -> nx.MultiDiGraph:
    """Return a node-induced subgraph after applying filter rules.

    - ``keep_paper`` / ``keep_entity``: include nodes of that type
    - ``allowed_categories``: if set, entity nodes must have one of these
      categories (paper nodes ignore this filter)
    - ``min_degree``: drop nodes whose total degree (in + out across
      multi-edges) is below this threshold
    """
    allowed = set(allowed_categories) if allowed_categories is not None else None

    keep_nodes: list[str] = []
    for node, data in g.nodes(data=True):
        node_type = str(data.get("type") or data.get("node_type") or "").lower()
        if node_type == "paper" and not keep_paper:
            continue
        if node_type == "entity":
            if not keep_entity:
                continue
            if allowed is not None:
                category = str(data.get("entity_type") or data.get("category") or "")
                if category not in allowed:
                    continue
        keep_nodes.append(node)

    sub = g.subgraph(keep_nodes).copy()

    if min_degree > 0:
        # Iterate to a fixed point: dropping a low-degree node lowers its
        # neighbors' degrees too, which may push them below the threshold.
        # Bound iterations defensively (V iterations is the absolute max).
        max_iters = max(1, sub.number_of_nodes())
        prev_size = -1
        for _ in range(max_iters):
            if sub.number_of_nodes() == prev_size:
                break
            prev_size = sub.number_of_nodes()
            keep = [n for n, deg in sub.degree() if deg >= min_degree]
            sub = sub.subgraph(keep).copy()

    return sub


def render_pyvis_html(
    g: nx.MultiDiGraph,
    *,
    height_px: int = 800,
    paper_color: str = "#4DA8DA",
    entity_color: str = "#F5A623",
) -> str:
    """Render a :class:`MultiDiGraph` as pyvis HTML string.

    Returns the complete HTML document (including vendored JS) suitable
    for ``streamlit.components.v1.html(value, height=...)``. Color codes
    Paper vs Entity nodes for quick visual separation.
    """
    net = Network(
        height=f"{height_px}px",
        width="100%",
        directed=True,
        notebook=False,
        cdn_resources="in_line",  # vendor vis.js inline so it works in Streamlit iframe
    )
    # Disable the physics-stabilization toolbar after initial layout settles.
    net.set_options(
        """
        {
          "physics": {
            "enabled": true,
            "stabilization": {"iterations": 100, "fit": true},
            "barnesHut": {"gravitationalConstant": -8000, "springLength": 120}
          },
          "interaction": {"hover": true, "tooltipDelay": 100}
        }
        """
    )

    for node, data in g.nodes(data=True):
        node_type = str(data.get("type") or data.get("node_type") or "").lower()
        if node_type == "paper":
            title_text = str(data.get("title") or data.get("label") or node)
            tooltip = f"<b>Paper</b><br>{title_text}"
            net.add_node(str(node), label=title_text[:30], color=paper_color, title=tooltip, shape="dot")
        else:
            label = str(data.get("label") or data.get("name") or node)
            category = str(data.get("entity_type") or data.get("category") or "")
            tooltip = f"<b>Entity</b> ({category})<br>{label}" if category else f"<b>Entity</b><br>{label}"
            net.add_node(str(node), label=label[:40], color=entity_color, title=tooltip, shape="dot")

    for u, v, edata in g.edges(data=True):
        relation = str(edata.get("relation") or edata.get("type") or "")
        edge_kind = str(edata.get("edge_type") or "").lower()
        # ``mentions`` edges (NER) get dashed lines; ``rebel`` edges stay solid.
        dashes = edge_kind == "mentions"
        net.add_edge(str(u), str(v), title=relation or None, label=relation if relation else "", dashes=dashes)

    # generate_html returns a complete standalone HTML document.
    return net.generate_html(notebook=False)
