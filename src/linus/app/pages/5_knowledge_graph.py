"""Linus Streamlit knowledge-graph page — task B.5 of the MVP build.

Browses the KnowledgeBase Phase 6 knowledge graph (REBEL typed
triples + SciSpacy NER entity mentions) interactively. Loads the
:file:`kg_graph.graphml` from the configured ``KB_OUTPUTS_DIR``,
exposes filters in the sidebar, renders the filtered subgraph via
:mod:`pyvis` embedded as inline HTML.

Page anatomy:

1. **Headline stats** — total nodes / edges, Paper vs Entity counts,
   number of distinct entity categories.
2. **Sidebar filters** — node-type checkboxes, entity-category
   multi-select, minimum-degree slider. Defaults bias toward a
   responsive initial render on large graphs.
3. **Render** — :func:`linus.app.kg_render.render_pyvis_html` produces
   a self-contained HTML doc; embedded via ``st.components.v1.html``.

Performance guard: when the source graph has > 2000 nodes, the
min-degree slider defaults to 2 so the first render is responsive.
Users can drop it back to 0 to see the full graph at the cost of
render time.
"""

from __future__ import annotations

import streamlit as st

from linus.app.config import KB_OUTPUTS_DIR
from linus.app.kg_render import compute_stats, filter_subgraph, load_kg, render_pyvis_html

st.set_page_config(page_title="Knowledge Graph — Linus", page_icon="🜨", layout="wide")
st.title("🧠 Knowledge Graph")
st.caption("Browse the REBEL + NER knowledge graph from KB Phase 6.")


_GRAPHML_PATH = KB_OUTPUTS_DIR / "knowledge_graph" / "kg_graph.graphml"

if not _GRAPHML_PATH.exists():
    st.warning(
        f"Knowledge-graph file not found at `{_GRAPHML_PATH}`.\n\n"
        "Run the KB Phase 6 pipeline to produce it:\n"
        "```\n"
        "cd modules/KnowledgeBase\n"
        "python -m papers_analysis.knowledge_graph\n"
        "```\n"
        "Note: the REBEL model auto-downloads ~1.5 GB on first run."
    )
    st.stop()


@st.cache_data(show_spinner="Loading knowledge graph…")
def _load_cached(path_str: str, mtime: float):
    """Load the GraphML once per file mtime. Returns (graph, stats)."""
    g = load_kg(_GRAPHML_PATH)
    stats = compute_stats(g)
    return g, stats


graph, stats = _load_cached(str(_GRAPHML_PATH), _GRAPHML_PATH.stat().st_mtime)


# ── headline stats ────────────────────────────────────────────────────────


c1, c2, c3, c4 = st.columns(4)
c1.metric("Total nodes", f"{stats.total_nodes:,}")
c2.metric("Total edges", f"{stats.total_edges:,}")
c3.metric("Papers", f"{stats.paper_nodes:,}")
c4.metric("Entities", f"{stats.entity_nodes:,}")


# ── sidebar filters ───────────────────────────────────────────────────────


with st.sidebar:
    st.header("Filters")

    keep_paper = st.checkbox("Include Paper nodes", value=True)
    keep_entity = st.checkbox("Include Entity nodes", value=True)

    if stats.entity_categories:
        selected_categories = st.multiselect(
            "Entity categories",
            options=stats.entity_categories,
            default=stats.entity_categories,
            help="Filter Entity nodes by their SciSpacy NER category.",
        )
    else:
        selected_categories = None
        st.caption("No entity categories detected in graph metadata.")

    # Auto-default min-degree above 0 for large graphs to keep first render snappy.
    big_graph = stats.total_nodes > 2000
    default_min_degree = 2 if big_graph else 0
    min_degree = st.slider(
        "Min node degree",
        min_value=0,
        max_value=50,
        value=default_min_degree,
        help="Drop nodes with fewer connections than this. Higher = sparser, faster render.",
    )

    if big_graph and min_degree == 0:
        st.warning(f"Full-graph render of {stats.total_nodes:,} nodes may be slow.")

    st.divider()
    st.caption(f"Source: `{_GRAPHML_PATH.name}`")


# ── filter + render ───────────────────────────────────────────────────────


sub = filter_subgraph(
    graph,
    keep_paper=keep_paper,
    keep_entity=keep_entity,
    allowed_categories=selected_categories,
    min_degree=min_degree,
)

st.markdown(
    f"**Rendering {sub.number_of_nodes():,} nodes / {sub.number_of_edges():,} edges** "
    f"after filtering (from {stats.total_nodes:,} / {stats.total_edges:,})."
)

if sub.number_of_nodes() == 0:
    st.info("Filter combination produced an empty graph. Loosen one of the constraints above.")
    st.stop()


@st.cache_data(show_spinner="Rendering pyvis HTML…", max_entries=4)
def _render_cached(
    n_nodes: int,
    n_edges: int,
    keep_p: bool,
    keep_e: bool,
    cats_tuple: tuple[str, ...] | None,
    min_d: int,
    mtime: float,
) -> str:
    """Cache key includes filter args so pyvis HTML regenerates only on filter change."""
    return render_pyvis_html(sub, height_px=800)


html_doc = _render_cached(
    sub.number_of_nodes(),
    sub.number_of_edges(),
    keep_paper,
    keep_entity,
    tuple(selected_categories) if selected_categories else None,
    min_degree,
    _GRAPHML_PATH.stat().st_mtime,
)
st.components.v1.html(html_doc, height=820, scrolling=False)
