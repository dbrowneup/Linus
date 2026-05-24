"""Linus Streamlit knowledge-graph page — task B.5 of the MVP build.

Browses the KnowledgeBase Phase 6 knowledge graph via two static Sigma.js
HTML views pre-rendered by ``papers_analysis.knowledge_graph`` (instant,
WebGL-fast), and a Python-side drill-down panel that renders the REBEL
typed-relation neighborhood of a seed paper or entity via pyvis (small
subgraphs only — typically <100 nodes).

Page anatomy:

1. **Headline stats** — counts pulled from ``kg_meta.json`` (no GraphML
   load needed for the header).
2. **View selector** — "Papers + top entities" / "REBEL typed relations"
   / "Drill-down explorer".
3. **Body** — iframe-embed the chosen static HTML, or render an interactive
   neighborhood subgraph for drill-down.

Replaces the previous pyvis-on-full-graph approach which hung on the
130k-node corpus. Pyvis is retained for drill-down only, where it shines.
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from linus.app.config import KB_OUTPUTS_DIR

st.set_page_config(page_title="Knowledge Graph — Linus", page_icon="🜨", layout="wide")
st.title("🧠 Knowledge Graph")
st.caption("Browse the REBEL + NER knowledge graph from KB Phase 6.")


_KG_DIR = KB_OUTPUTS_DIR / "knowledge_graph"
_META_PATH = _KG_DIR / "kg_meta.json"
_HTML_PAPERS_ENTITIES = _KG_DIR / "kg_papers_entities.html"
_HTML_REBEL_TYPED = _KG_DIR / "kg_rebel_typed.html"
_REBEL_JSONL = _KG_DIR / "rebel_triples.jsonl"


# ── Outputs presence check ────────────────────────────────────────────


if not _META_PATH.exists():
    st.warning(
        f"Knowledge-graph metadata not found at `{_META_PATH}`.\n\n"
        "Run the KB Phase 6 pipeline to produce it:\n"
        "```\n"
        "cd modules/KnowledgeBase\n"
        "python -m papers_analysis.knowledge_graph\n"
        "```\n"
        "Note: the REBEL model auto-downloads ~1.5 GB on first run."
    )
    st.stop()


with _META_PATH.open() as fh:
    meta = json.load(fh)


# ── Headline stats ────────────────────────────────────────────────────


node_types = meta.get("node_types", {}) or {}
edge_types = meta.get("edge_types", {}) or {}

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total nodes", f"{meta.get('n_nodes', 0):,}")
c2.metric("Total edges", f"{meta.get('n_edges', 0):,}")
c3.metric("Papers", f"{node_types.get('Paper', 0):,}")
c4.metric("Entities", f"{node_types.get('Entity', 0):,}")
st.caption(
    f"REBEL typed relations: **{edge_types.get('rebel', 0):,}** edges &middot; "
    f"NER mentions: **{edge_types.get('mentions', 0):,}** edges"
)


# ── View selector ─────────────────────────────────────────────────────


_VIEW_LABELS = {
    "papers_entities": "Papers + top entities",
    "rebel_typed": "REBEL typed relations",
    "drill_down": "Drill-down explorer",
}

view_key = st.radio(
    "View",
    list(_VIEW_LABELS.keys()),
    format_func=lambda k: _VIEW_LABELS[k],
    horizontal=True,
)


def _render_static_html(path: Path, view_label: str) -> None:
    """Embed a pre-rendered Sigma.js HTML file in an iframe."""
    if not path.exists():
        st.warning(
            f"`{path.name}` not found at `{path.parent}`. Re-render with:\n"
            "```\npython -m papers_analysis.knowledge_graph --export-html-only\n```"
        )
        return
    # mtime in caption gives reviewers a way to confirm the file was regenerated
    # after a recent pipeline run.
    mtime = path.stat().st_mtime
    size_mb = path.stat().st_size / (1024 * 1024)
    st.caption(f"_{view_label}: {size_mb:.1f} MB, rendered {_fmt_mtime(mtime)}_")
    st.components.v1.html(path.read_text(), height=820, scrolling=False)


def _fmt_mtime(mtime: float) -> str:
    """Render a file's mtime as ISO-like UTC timestamp."""
    import datetime

    return datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")


# ── Drill-down helpers ────────────────────────────────────────────────


@st.cache_data(show_spinner="Loading REBEL triples…")
def _load_rebel_triples(path_str: str, mtime: float) -> list[dict]:
    """Cached loader for the REBEL JSONL checkpoint (mtime invalidates cache)."""
    triples: list[dict] = []
    with Path(path_str).open() as fh:
        for line in fh:
            triples.append(json.loads(line))
    return triples


def _build_neighborhood(triples: list[dict], seed: str, hops: int):
    """Return a MultiDiGraph of the seed's k-hop REBEL neighborhood.

    Matching order: exact entity-name match (case-insensitive); else any
    triple whose sha256 starts with the seed (paper drill-down). Empty
    graph when nothing matches — caller surfaces the no-match warning.
    """
    import networkx as nx

    g = nx.MultiDiGraph()
    for t in triples:
        g.add_edge(t["head"], t["tail"], relation=t["relation"], sha256=t["sha256"])

    seed_lower = seed.lower().strip()
    seeds: set[str] = set()
    for node in g.nodes():
        if str(node).lower() == seed_lower:
            seeds.add(node)
    if not seeds:
        # Paper SHA drill-down: include both endpoints of any triple from this paper.
        for u, v, data in g.edges(data=True):
            sha = data.get("sha256", "")
            if sha.startswith(seed_lower):
                seeds.add(u)
                seeds.add(v)
    if not seeds:
        return nx.MultiDiGraph()

    visited = set(seeds)
    frontier = set(seeds)
    for _ in range(hops):
        nxt: set[str] = set()
        for node in frontier:
            nxt |= set(g.predecessors(node))
            nxt |= set(g.successors(node))
        frontier = nxt - visited
        visited |= frontier
        if not frontier:
            break

    return g.subgraph(visited).copy()


def _render_neighborhood_pyvis(g, seed_lower: str, height_px: int = 700) -> str:
    """Render an entity-only MultiDiGraph as pyvis HTML.

    Seed nodes get a brighter highlight; relation labels appear on edges.
    Small graphs only — caller filters before invoking.
    """
    from pyvis.network import Network

    net = Network(
        height=f"{height_px}px",
        width="100%",
        directed=True,
        notebook=False,
        cdn_resources="in_line",
        bgcolor="#0f172a",
        font_color="#e2e8f0",
    )
    net.set_options(
        """
        {
          "physics": {
            "enabled": true,
            "stabilization": {"iterations": 100, "fit": true},
            "barnesHut": {"gravitationalConstant": -6000, "springLength": 95}
          },
          "nodes": {
            "shape": "dot",
            "font": {"color": "#f1f5f9", "size": 13}
          },
          "edges": {
            "color": {"color": "rgba(148,163,184,0.55)"},
            "smooth": {"type": "continuous"},
            "font": {"color": "#94a3b8", "size": 10, "align": "middle"}
          }
        }
        """
    )

    for node in g.nodes():
        is_seed = str(node).lower() == seed_lower
        net.add_node(
            str(node),
            label=str(node),
            color="#fbbf24" if is_seed else "#7dd3fc",
            size=18 if is_seed else 12,
            title=f"<b>{node}</b><br>degree: {g.degree(node)}",
        )
    for u, v, data in g.edges(data=True):
        net.add_edge(
            str(u),
            str(v),
            label=str(data.get("relation", "")),
            title=str(data.get("relation", "")),
        )
    return net.generate_html(notebook=False)


# ── Body ──────────────────────────────────────────────────────────────


if view_key == "papers_entities":
    st.caption(
        f"Papers ({node_types.get('Paper', 0):,}) coloured by their broad cluster · "
        "top-200 entities (amber) at the centroid of their source papers."
    )
    _render_static_html(_HTML_PAPERS_ENTITIES, "Papers + top entities")

elif view_key == "rebel_typed":
    st.caption(
        "Entity↔entity subgraph from REBEL triples · filtered to nodes with degree ≥ 2 · coloured by Louvain community."
    )
    _render_static_html(_HTML_REBEL_TYPED, "REBEL typed relations")

else:  # drill_down
    st.caption(
        "Type a paper SHA-256 (or prefix) or an entity name. Renders the seed's "
        "k-hop REBEL neighbourhood as a small interactive graph."
    )
    if not _REBEL_JSONL.exists():
        st.warning(f"`{_REBEL_JSONL}` not found — run KB Phase 6 first.")
        st.stop()

    seed_col, hops_col = st.columns([3, 1])
    seed = seed_col.text_input(
        "Seed (entity name or paper SHA)",
        value="",
        placeholder="e.g. genome, BRCA1, or a sha256 prefix like 0007fd82",
    )
    hops = hops_col.slider("Hops", min_value=1, max_value=3, value=2)

    if not seed.strip():
        st.info("Enter a seed above to render its REBEL neighbourhood.")
        st.stop()

    triples = _load_rebel_triples(str(_REBEL_JSONL), _REBEL_JSONL.stat().st_mtime)
    with st.spinner("Building neighborhood…"):
        sub = _build_neighborhood(triples, seed, hops)

    if sub.number_of_nodes() == 0:
        st.warning(
            f"No REBEL triples match `{seed}`. "
            "Try a shorter SHA prefix or an entity that appears in `rebel_triples.jsonl`."
        )
        st.stop()

    # Safety guard: huge neighborhoods (e.g. seed=genome with hops=3) can blow up
    # browser memory in pyvis. Cap at a sensible threshold and warn.
    n_nodes = sub.number_of_nodes()
    if n_nodes > 500:
        st.warning(
            f"Neighborhood has {n_nodes:,} nodes — capping render to 500 by trimming "
            "lowest-degree boundary nodes. Reduce hops for cleaner views."
        )
        # Keep the top-500 nodes by degree (preserves the dense core around seed).
        keep = sorted(sub.nodes(), key=lambda n: sub.degree(n), reverse=True)[:500]
        sub = sub.subgraph(keep).copy()

    st.markdown(f"**Neighborhood: {sub.number_of_nodes():,} nodes, {sub.number_of_edges():,} edges** (hops={hops})")

    with st.spinner("Rendering pyvis…"):
        html = _render_neighborhood_pyvis(sub, seed.lower().strip())
    st.components.v1.html(html, height=720, scrolling=False)
