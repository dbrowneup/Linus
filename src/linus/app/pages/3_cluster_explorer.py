"""Linus Streamlit cluster-explorer page — task B.3 of the MVP build.

Three-pane drill-down browser over the KB Phase 4 broad → mid → fine
topic hierarchy. Left pane = breadcrumb path with back navigation;
middle pane = clickable topic list at the current scale; right pane =
detail view (Sankey, 3D UMAP scatter, paper list) scoped to the
selected topic.

Per the MVP spec's "locked design choice 3": three-pane layout with
breadcrumbs + tree + detail. Data layer is in
:mod:`linus.app.cluster_data` — Streamlit-agnostic + unit-tested.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import streamlit as st

from linus.app.cluster_data import (
    SCALES,
    ClusterData,
    Scale,
    TopicScale,
    load_cluster_data,
)
from linus.app.config import KB_METADATA_DB, KB_OUTPUTS_DIR

st.set_page_config(page_title="Cluster Explorer — Linus", page_icon="🜨", layout="wide")
st.title("🗂️ Cluster Explorer")
st.caption("Drill broad → mid → fine over the KnowledgeBase topic hierarchy.")


# ── data load ─────────────────────────────────────────────────────────────


@st.cache_data(show_spinner="Loading cluster data…")
def _load_cluster_data_cached(outputs_dir_str: str, mtime: float):
    """Return a fresh :class:`ClusterData` from disk; cached on hierarchy.json mtime."""
    return load_cluster_data(Path(outputs_dir_str))


def _hierarchy_mtime() -> float:
    """Use any one of the cluster files' mtime as the cache key.

    Picking ``labels_fine.json`` first because if anything else changed,
    the fine labels almost certainly did too — the KB pipeline emits
    the whole batch in one run.
    """
    for name in ("labels_fine.json", "labels_mid.json", "labels_broad.json"):
        path = KB_OUTPUTS_DIR / name
        if path.exists():
            return path.stat().st_mtime
    return 0.0


data = _load_cluster_data_cached(str(KB_OUTPUTS_DIR), _hierarchy_mtime())

if data is None:
    st.warning(
        "Cluster artifacts not found at the configured outputs directory.\n\n"
        "Run the KB Phase 4 pipeline to produce them:\n"
        "```\n"
        "cd modules/KnowledgeBase\n"
        "python -m papers_analysis.cluster\n"
        "```\n"
        f"Expected files under `{KB_OUTPUTS_DIR}/`:\n"
        "- `labels_broad.json`, `labels_mid.json`, `labels_fine.json`\n"
        "- `topics_broad.json`, `topics_mid.json`, `topics_fine.json`\n"
        "- `hierarchy.json`, `umap_3d.npy`, `umap_sha256s.json`"
    )
    st.stop()


# ── state initialization ──────────────────────────────────────────────────

if "explorer_broad_id" not in st.session_state:
    st.session_state.explorer_broad_id = None
if "explorer_mid_id" not in st.session_state:
    st.session_state.explorer_mid_id = None
if "explorer_fine_id" not in st.session_state:
    st.session_state.explorer_fine_id = None


def _current_scale() -> Scale:
    if st.session_state.explorer_fine_id is not None:
        return "fine"
    if st.session_state.explorer_mid_id is not None:
        return "mid"
    return "broad"


def _select_broad(broad_id: str) -> None:
    st.session_state.explorer_broad_id = broad_id
    st.session_state.explorer_mid_id = None
    st.session_state.explorer_fine_id = None


def _select_mid(mid_id: str) -> None:
    st.session_state.explorer_mid_id = mid_id
    st.session_state.explorer_fine_id = None


def _select_fine(fine_id: str) -> None:
    st.session_state.explorer_fine_id = fine_id


def _back() -> None:
    """Pop the deepest set id."""
    if st.session_state.explorer_fine_id is not None:
        st.session_state.explorer_fine_id = None
    elif st.session_state.explorer_mid_id is not None:
        st.session_state.explorer_mid_id = None
    elif st.session_state.explorer_broad_id is not None:
        st.session_state.explorer_broad_id = None


# ── layout: three panes ──────────────────────────────────────────────────

left, middle, right = st.columns([1, 2, 4])


# ── LEFT PANE: breadcrumb path + back nav ────────────────────────────────


def _topic_label(scale: Scale, cluster_id: str | None) -> str:
    if cluster_id is None:
        return "—"
    ts: TopicScale = data.scale(scale)
    label = ts.cluster_to_label.get(cluster_id) or f"#{cluster_id}"
    # Truncate to keep the breadcrumb readable.
    return label if len(label) <= 30 else label[:28] + "…"


with left:
    st.markdown("### Path")
    broad_id = st.session_state.explorer_broad_id
    mid_id = st.session_state.explorer_mid_id
    fine_id = st.session_state.explorer_fine_id

    # Each level shown as a small button — clicking returns to that level.
    if broad_id is None:
        st.markdown("_at broad level_")
    else:
        if st.button(f"Broad: {_topic_label('broad', broad_id)}", key="bc_broad"):
            _select_broad(broad_id)
            st.rerun()
        if mid_id is not None:
            if st.button(f"▸ Mid: {_topic_label('mid', mid_id)}", key="bc_mid"):
                _select_mid(mid_id)
                st.rerun()
        if fine_id is not None:
            if st.button(f"▸ Fine: {_topic_label('fine', fine_id)}", key="bc_fine"):
                _select_fine(fine_id)
                st.rerun()

    st.divider()
    if broad_id is not None and st.button("⬆ Back", key="back", use_container_width=True):
        _back()
        st.rerun()


# ── MIDDLE PANE: clickable topic list at the current level ──────────────


def _list_topics_at_current_level() -> tuple[Scale, list[tuple[str, str, int]]]:
    """Return (level, [(cluster_id, label, paper_count), ...]) for the middle pane.

    The level is one ABOVE the current selection — i.e. while at broad
    (nothing selected), show broad topics. After broad selected, show
    mid topics under it. After mid selected, show fine topics under it.
    Once fine is selected, the middle pane shows fine again but with
    the selection highlighted.
    """
    if st.session_state.explorer_broad_id is None:
        # Show all broad topics
        items = [
            (cid, data.broad.cluster_to_label.get(cid) or f"#{cid}", len(papers))
            for cid, papers in data.broad.cluster_to_papers.items()
        ]
        return "broad", sorted(items, key=lambda x: -x[2])
    if st.session_state.explorer_mid_id is None:
        # Show mid topics under selected broad
        bid = st.session_state.explorer_broad_id
        children = data.children_of(bid, "broad")
        items = [
            (cid, data.mid.cluster_to_label.get(cid) or f"#{cid}", len(data.mid.cluster_to_papers.get(cid, [])))
            for cid in children
        ]
        return "mid", sorted(items, key=lambda x: -x[2])
    # Show fine topics under selected mid
    mid_id_local = st.session_state.explorer_mid_id
    children = data.children_of(mid_id_local, "mid")
    items = [
        (cid, data.fine.cluster_to_label.get(cid) or f"#{cid}", len(data.fine.cluster_to_papers.get(cid, [])))
        for cid in children
    ]
    return "fine", sorted(items, key=lambda x: -x[2])


with middle:
    level, items = _list_topics_at_current_level()
    st.markdown(f"### {level.title()} topics ({len(items)})")
    if not items:
        st.info(f"No {level} topics under the current selection.")
    else:
        for cid, label, count in items[:200]:  # cap to keep render snappy on large fanout
            display = f"{label} ({count})"
            if st.button(display, key=f"topic_{level}_{cid}", use_container_width=True):
                if level == "broad":
                    _select_broad(cid)
                elif level == "mid":
                    _select_mid(cid)
                else:
                    _select_fine(cid)
                st.rerun()
        if len(items) > 200:
            st.caption(f"…and {len(items) - 200} more (showing top 200 by paper count).")


# ── RIGHT PANE: Sankey + 3D UMAP + paper list ────────────────────────────


def _selected_papers() -> tuple[list[str], Scale, str | None]:
    """Return (papers, scale_of_selection, cluster_id_of_selection)."""
    fid = st.session_state.explorer_fine_id
    mid = st.session_state.explorer_mid_id
    bid = st.session_state.explorer_broad_id
    if fid is not None:
        return data.papers_under(fid, "fine"), "fine", fid
    if mid is not None:
        return data.papers_under(mid, "mid"), "mid", mid
    if bid is not None:
        return data.papers_under(bid, "broad"), "broad", bid
    # Nothing selected — all papers across all broad clusters
    all_papers: list[str] = []
    for papers in data.broad.cluster_to_papers.values():
        all_papers.extend(papers)
    return all_papers, "broad", None


def _build_sankey(scope_broad: str | None, scope_mid: str | None) -> go.Figure:
    """Build a broad → mid → fine Sankey scoped to the current selection."""
    broad_ids = (
        [scope_broad]
        if scope_broad is not None
        else sorted(data.broad.cluster_to_papers.keys())
    )

    sources: list[int] = []
    targets: list[int] = []
    values: list[int] = []
    node_labels: list[str] = []
    node_index: dict[tuple[Scale, str], int] = {}

    def _add_node(scale: Scale, cid: str) -> int:
        key = (scale, cid)
        if key in node_index:
            return node_index[key]
        node_index[key] = len(node_labels)
        label = data.scale(scale).cluster_to_label.get(cid) or f"#{cid}"
        node_labels.append(f"{scale[0].upper()}: {label[:30]}")
        return node_index[key]

    for bid in broad_ids:
        b_idx = _add_node("broad", bid)
        mids = data.children_of(bid, "broad")
        if scope_mid is not None:
            mids = [m for m in mids if m == scope_mid]
        for mid_id_iter in mids:
            m_idx = _add_node("mid", mid_id_iter)
            count_b_to_m = len(data.mid.cluster_to_papers.get(mid_id_iter, []))
            if count_b_to_m > 0:
                sources.append(b_idx)
                targets.append(m_idx)
                values.append(count_b_to_m)
            for fine_id_iter in data.children_of(mid_id_iter, "mid"):
                f_idx = _add_node("fine", fine_id_iter)
                count_m_to_f = len(data.fine.cluster_to_papers.get(fine_id_iter, []))
                if count_m_to_f > 0:
                    sources.append(m_idx)
                    targets.append(f_idx)
                    values.append(count_m_to_f)

    if not sources:
        return go.Figure()

    fig = go.Figure(
        data=[
            go.Sankey(
                node={
                    "label": node_labels,
                    "pad": 10,
                    "thickness": 14,
                    "color": "#4DA8DA",
                },
                link={
                    "source": sources,
                    "target": targets,
                    "value": values,
                    "color": "rgba(77,168,218,0.3)",
                },
            )
        ]
    )
    fig.update_layout(height=420, margin={"l": 8, "r": 8, "t": 8, "b": 8})
    return fig


def _build_umap_scatter(
    selected_papers_set: set[str], color_by_scale: Scale
) -> go.Figure | None:
    """3D UMAP scatter — color by cluster at given scale; dim non-selected."""
    if data.umap_3d is None or not data.umap_sha256s:
        return None
    coords = data.umap_3d
    sha_list = data.umap_sha256s

    scale_obj = data.scale(color_by_scale)

    x = coords[:, 0]
    y = coords[:, 1]
    z = coords[:, 2]
    colors: list[str] = []
    opacities: list[float] = []
    hover: list[str] = []

    for sha in sha_list:
        cluster_id = scale_obj.paper_to_cluster.get(sha)
        label = scale_obj.cluster_to_label.get(cluster_id, "—") if cluster_id else "—"
        hover.append(label[:40])
        # Distinct color per cluster — hash to a hue
        if cluster_id is None:
            colors.append("#999999")
        else:
            # Simple deterministic color from cluster_id
            hue = (abs(hash(cluster_id)) % 360)
            colors.append(f"hsl({hue}, 70%, 55%)")
        opacities.append(1.0 if sha in selected_papers_set else 0.08)

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="markers",
                marker={
                    "size": 3,
                    "color": colors,
                    "opacity": opacities,
                },
                hovertext=hover,
                hoverinfo="text",
            )
        ]
    )
    fig.update_layout(
        height=420,
        margin={"l": 0, "r": 0, "t": 8, "b": 0},
        scene={"xaxis_title": "", "yaxis_title": "", "zaxis_title": ""},
    )
    return fig


@st.cache_data(show_spinner=False)
def _fetch_paper_meta(metadata_db_str: str, shas_tuple: tuple[str, ...]) -> list[dict[str, Any]]:
    """Pull (title, year, authors) for the given sha256 list from metadata.db."""
    db_path = Path(metadata_db_str)
    if not db_path.exists() or not shas_tuple:
        return []
    placeholders = ",".join("?" for _ in shas_tuple)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT sha256, title, year, authors FROM papers WHERE sha256 IN ({placeholders})",
            shas_tuple,
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


with right:
    selected_papers, sel_scale, sel_cid = _selected_papers()
    selected_papers_set = set(selected_papers)
    selection_label = "Full corpus" if sel_cid is None else _topic_label(sel_scale, sel_cid)
    st.markdown(f"### Detail: {selection_label}")
    st.caption(f"{len(selected_papers):,} papers in current selection.")

    tab_sankey, tab_umap, tab_papers = st.tabs(["Sankey", "3D UMAP", "Papers"])

    with tab_sankey:
        sankey_fig = _build_sankey(
            st.session_state.explorer_broad_id,
            st.session_state.explorer_mid_id,
        )
        if sankey_fig.data:
            st.plotly_chart(sankey_fig, use_container_width=True)
        else:
            st.info("No Sankey to render at the current selection.")

    with tab_umap:
        if data.umap_3d is None:
            st.warning(
                "UMAP-3D coordinates not found — run the KB Phase 4 pipeline to produce "
                "`umap_3d.npy` and `umap_sha256s.json`."
            )
        else:
            umap_fig = _build_umap_scatter(selected_papers_set, _current_scale())
            if umap_fig is not None:
                st.plotly_chart(umap_fig, use_container_width=True)

    with tab_papers:
        if not selected_papers:
            st.info("No papers in current selection.")
        else:
            # Cap the metadata fetch at the first 500 papers per render.
            preview = tuple(selected_papers[:500])
            rows = _fetch_paper_meta(str(KB_METADATA_DB), preview)
            if rows:
                st.dataframe(
                    rows,
                    column_config={
                        "sha256": st.column_config.TextColumn("SHA256", width="small"),
                        "title": st.column_config.TextColumn("Title", width="large"),
                        "year": st.column_config.NumberColumn("Year"),
                        "authors": st.column_config.TextColumn("Authors", width="medium"),
                    },
                    hide_index=True,
                    use_container_width=True,
                )
                if len(selected_papers) > 500:
                    st.caption(f"Showing first 500 of {len(selected_papers):,} papers.")
            else:
                st.warning(
                    f"No metadata found in `{KB_METADATA_DB}` for the selected papers. "
                    "Run the KB Phase 2 metadata pipeline if missing."
                )
