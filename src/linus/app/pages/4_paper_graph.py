"""Linus Streamlit paper-graph page — task B.4 of the MVP build.

Embeds the KnowledgeBase pipeline's pre-rendered interactive graph
viewers — Sigma.js (2D) and 3d-force-graph (3D) — as Streamlit HTML
components.

The KB pipeline (``modules/KnowledgeBase/papers_analysis/graph.py`` →
``visualize.py``) produces two self-contained HTML files:

- ``data/outputs/graph/graph_sigma.html`` — 2D WebGL, pre-positioned
  from UMAP-2D, click-to-pin with neighbor highlight, legend filter
- ``data/outputs/graph/graph_3d.html`` — 3D WebGL via Three.js,
  rotatable camera, same hover/pin UX as 2D

Both HTML files vendor their JS dependencies inline (Sigma.js +
graphology, 3d-force-graph bundling Three.js) so they render
self-contained inside a Streamlit ``components.v1.html`` iframe with
no extra network fetches.

File contents are read on demand and cached keyed on the file's mtime
— the cache invalidates automatically when KB regenerates the HTML.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from linus.app.config import KB_OUTPUTS_DIR

st.set_page_config(page_title="Paper Graph — Linus", page_icon="🜨", layout="wide")
st.title("🕸️ Paper Graph")
st.caption("Interactive similarity graph from the KnowledgeBase Phase 5 pipeline.")


_GRAPH_DIR = KB_OUTPUTS_DIR / "graph"
_SIGMA_PATH = _GRAPH_DIR / "graph_sigma.html"
_FORCE3D_PATH = _GRAPH_DIR / "graph_3d.html"


@st.cache_data(show_spinner=False)
def _load_html(path_str: str, mtime: float) -> str:
    """Return the HTML file contents, cached keyed on (path, mtime).

    The mtime arg makes the cache invalidate automatically when KB
    regenerates the HTML (e.g. after ``python -m papers_analysis.graph
    --html-only``). The cache key is the pair, not just the path.
    """
    return Path(path_str).read_text(encoding="utf-8")


# ── view selector ────────────────────────────────────────────────────────


view = st.radio(
    "View",
    options=["2D (Sigma.js)", "3D (force-directed)"],
    horizontal=True,
    label_visibility="collapsed",
)

if view == "2D (Sigma.js)":
    selected_path: Path = _SIGMA_PATH
    description = (
        "Pre-positioned from UMAP-2D, no physics simulation. "
        "Hover for paper info, click to pin + highlight neighbors, "
        "click legend entries to filter by broad topic."
    )
else:
    selected_path = _FORCE3D_PATH
    description = (
        "Pre-positioned from UMAP-3D — Three.js camera (rotate / zoom), "
        "no force simulation. Same hover/pin/legend interactions as 2D."
    )

st.caption(description)

if not selected_path.exists():
    st.warning(
        f"Graph HTML not found at `{selected_path}`.\n\n"
        "Generate it by running the KB Phase 5 pipeline:\n"
        "```\n"
        "cd modules/KnowledgeBase\n"
        "python -m papers_analysis.graph --recompute\n"
        "```\n"
        "Then refresh this page (or re-render with `--html-only` if the "
        "underlying GraphML is already built)."
    )
    st.stop()

html_text = _load_html(str(selected_path), selected_path.stat().st_mtime)
st.components.v1.html(html_text, height=900, scrolling=False)

# ── footer ────────────────────────────────────────────────────────────────

st.divider()
st.caption(
    f"Source: `{selected_path}` "
    f"({selected_path.stat().st_size // 1024} KB, "
    f"last modified epoch {int(selected_path.stat().st_mtime)}). "
    "Hover the graph for paper titles, click a node to pin + reveal abstract, "
    "click a legend entry to filter by broad topic. ESC or background-click clears the pin."
)
