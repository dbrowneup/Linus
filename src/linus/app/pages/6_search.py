"""Linus Streamlit search page — task B.6 of the MVP build.

Thin UI over the :class:`linus.knowledge.KnowledgeRetriever` gateway
(task A.4). Same contract the Archimedes Tier-1 retrieval engine
consumes; the page is a working demo of that contract for Dan.

Method choices:

- **Keyword** — wired in A.4 (LIKE-search backend). Works today.
- **Semantic** — interface present, raises NotImplementedError with
  install pointer (SPECTER2 model + sentence-transformers).
- **Hybrid** — runs both; unimplemented methods auto-skipped.
"""

from __future__ import annotations

import streamlit as st

from linus.app.search import SearchResult, run_search
from linus.knowledge import KnowledgeBaseAdapter, KnowledgeBaseUnavailableError

st.set_page_config(page_title="Search — Linus", page_icon="🜨", layout="wide")
st.title("🔎 Search")
st.caption("Keyword + semantic search over the KnowledgeBase corpus, via the RAG gateway.")


# ── shared adapter (cached) ───────────────────────────────────────────────


@st.cache_resource(show_spinner=False)
def _get_adapter() -> KnowledgeBaseAdapter:
    return KnowledgeBaseAdapter()


# ── controls ──────────────────────────────────────────────────────────────


col_q, col_method, col_k = st.columns([3, 1, 1])

with col_q:
    query = st.text_input(
        "Query",
        value="",
        placeholder="e.g. long-read sequencing, volatility-managed portfolios, BRCA1 expression",
        label_visibility="collapsed",
    )

with col_method:
    method = st.selectbox(
        "Method",
        options=["keyword", "semantic", "hybrid"],
        index=0,
        help=(
            "keyword: SQL LIKE over title+abstract (always available). "
            "semantic: SPECTER2 cosine (requires sentence-transformers). "
            "hybrid: run both and fuse — unimplemented methods skip silently."
        ),
    )

with col_k:
    top_k = st.slider("Top K", min_value=5, max_value=50, value=20, step=5)


# ── execute ───────────────────────────────────────────────────────────────


if not query.strip():
    st.info("Enter a query above to search the corpus.")
    st.stop()

try:
    adapter = _get_adapter()
except KnowledgeBaseUnavailableError as exc:
    st.error(str(exc))
    st.stop()

try:
    rows, skipped = run_search(query.strip(), method=method, top_k=top_k, adapter=adapter)
except NotImplementedError as exc:
    st.warning(f"**{method.title()} retrieval not yet wired in this Linus build.**\n\n{exc}")
    st.stop()

if skipped:
    st.info("Methods skipped (interface present, implementation pending): " + ", ".join(skipped))

st.markdown(f"**{len(rows)} result(s)** for `{query}` via `{method}`.")


# ── render ────────────────────────────────────────────────────────────────


def _row_to_display(row: SearchResult) -> dict:
    """Render-friendly dict for st.dataframe."""
    return {
        "score": round(row.score, 4),
        "year": row.year,
        "title": row.title or "—",
        "authors": (row.authors or "").split(";")[0].strip() + ("…" if row.authors and ";" in row.authors else ""),
        "provenance": row.provenance,
        "sha256": row.sha256[:12] + "…",
    }


if rows:
    st.dataframe(
        [_row_to_display(r) for r in rows],
        column_config={
            "score": st.column_config.NumberColumn("Score", format="%.4f", width="small"),
            "year": st.column_config.NumberColumn("Year", width="small"),
            "title": st.column_config.TextColumn("Title", width="large"),
            "authors": st.column_config.TextColumn("First author", width="medium"),
            "provenance": st.column_config.TextColumn("Source", width="small"),
            "sha256": st.column_config.TextColumn("SHA256", width="small"),
        },
        hide_index=True,
        use_container_width=True,
    )

    st.divider()
    st.subheader("Abstracts")
    for r in rows[:10]:
        with st.expander(f"{r.title or '—'} ({r.year or 'n.d.'})"):
            st.markdown(f"**Authors:** {r.authors or 'unknown'}")
            st.markdown(f"**SHA256:** `{r.sha256}`")
            st.markdown(f"**Score:** {r.score:.4f}  ·  **Source:** {r.provenance}")
            st.markdown("---")
            st.markdown(r.abstract or "_No abstract available._")
else:
    st.info("No results. Try a different query or method.")
