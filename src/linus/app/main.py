"""Linus Streamlit UI — landing page (task B.0 of the MVP build).

Launch with ``streamlit run src/linus/app/main.py``.

Shows project status, the resolved environment configuration, and a live
health check of the Linus orchestration server. Individual pages
(chat, corpus stats, cluster explorer, paper graph, knowledge graph,
search) auto-appear in the sidebar as they ship.
"""

from __future__ import annotations

import httpx
import streamlit as st

from linus.app.config import (
    KB_EMBEDDINGS_DIR,
    KB_METADATA_DB,
    KB_OUTPUTS_DIR,
    SERVER_URL,
    config_summary,
)

st.set_page_config(
    page_title="Linus",
    page_icon="🜨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🜨 Linus")
st.caption("A personal AI orchestration backend for Apple Silicon.")

# ── Server health check ─────────────────────────────────────────────────────
st.header("Server status")

health_col, url_col = st.columns([1, 3])


def _check_server(url: str, timeout: float = 2.0) -> tuple[bool, str, dict | None]:
    """Return ``(ok, detail, body)`` from a GET on the server's ``/healthz`` probe.

    Hitting ``/healthz`` rather than ``/`` matters: the FastAPI app doesn't
    define a root route, so a GET on ``/`` returns 404 and the page would
    incorrectly report "Unreachable" while the server is actually fine.
    The ``/healthz`` endpoint additionally tells us whether Ollama is
    reachable from the server's perspective, plus the new degradation
    payload introduced in feature/q3-loud-degradation.
    """
    probe = url.rstrip("/") + "/healthz"
    try:
        response = httpx.get(probe, timeout=timeout)
        if response.status_code == 200:
            body = response.json()
            ollama_ok = body.get("ollama_reachable", False)
            n_models = len(body.get("models", []) or [])
            detail_msg = f"HTTP 200 from {probe} — Ollama {'reachable' if ollama_ok else 'NOT reachable'}, {n_models} model(s) pulled"
            return True, detail_msg, body
        return False, f"HTTP {response.status_code} from {probe}", None
    except httpx.ConnectError:
        return False, f"Connection refused at {probe} — is the server running?", None
    except httpx.TimeoutException:
        return False, f"Timeout after {timeout}s at {probe}", None
    except Exception as exc:  # noqa: BLE001 — surface any failure mode to the UI
        return False, f"{type(exc).__name__}: {exc}", None


ok, detail, health_body = _check_server(SERVER_URL)
with health_col:
    if ok:
        st.success("Reachable")
    else:
        st.error("Unreachable")
with url_col:
    st.code(detail, language="text")

if not ok:
    st.info(
        "To start the server, in a separate terminal run:\n"
        "```\n"
        "conda activate linus\n"
        "uvicorn linus.server:app --reload\n"
        "```"
    )

# ── Effective state (degradations) ──────────────────────────────────────────
# Live-vs-degraded was previously invisible. /healthz now ships an
# ``effective_state`` + ``degradations`` payload describing each silent
# fall-through (missing Worker model, empty papers dir, missing KB
# artifacts, empty Ollama installation). Show it inline so the
# Reachable/Unreachable binary doesn't swallow operationally-significant
# problems.
if ok and health_body is not None:
    st.header("Effective state")
    effective_state = health_body.get("effective_state", "unknown")
    degradations = health_body.get("degradations", []) or []

    if effective_state == "live":
        st.success(f"State: **live** — all checks passing ({len(degradations)} degradations)")
    elif effective_state == "degraded":
        st.warning(f"State: **degraded** — {len(degradations)} warning(s); core function intact")
    elif effective_state == "down":
        st.error(f"State: **down** — {len(degradations)} blocking issue(s); core function impaired")
    else:
        st.info(f"State: **{effective_state}**")

    if degradations:
        st.table(
            [
                {
                    "Component": d.get("component", ""),
                    "Expected": d.get("expected", ""),
                    "Actual": d.get("actual", ""),
                    "Severity": d.get("severity", ""),
                    "Remediation": d.get("remediation", ""),
                }
                for d in degradations
            ]
        )
    else:
        st.caption("No degradations reported.")

# ── KB artifact availability ────────────────────────────────────────────────
st.header("KnowledgeBase artifacts")

artifact_rows: list[tuple[str, str, bool]] = [
    (
        "Cluster hierarchy",
        str(KB_OUTPUTS_DIR / "clusters" / "hierarchy.json"),
        (KB_OUTPUTS_DIR / "clusters" / "hierarchy.json").exists(),
    ),
    (
        "Broad cluster labels",
        str(KB_OUTPUTS_DIR / "clusters" / "labels_broad.json"),
        (KB_OUTPUTS_DIR / "clusters" / "labels_broad.json").exists(),
    ),
    (
        "Paper graph (2D)",
        str(KB_OUTPUTS_DIR / "graph" / "graph_sigma.html"),
        (KB_OUTPUTS_DIR / "graph" / "graph_sigma.html").exists(),
    ),
    (
        "Knowledge graph",
        str(KB_OUTPUTS_DIR / "knowledge_graph" / "kg_graph.graphml"),
        (KB_OUTPUTS_DIR / "knowledge_graph" / "kg_graph.graphml").exists(),
    ),
    ("Metadata DB", str(KB_METADATA_DB), KB_METADATA_DB.exists()),
    ("SPECTER2 embeddings", str(KB_EMBEDDINGS_DIR / "specter2.npy"), (KB_EMBEDDINGS_DIR / "specter2.npy").exists()),
]

for name, path, exists in artifact_rows:
    icon = "✅" if exists else "⚠️"
    st.markdown(f"{icon} **{name}** — `{path}`")

if not all(exists for _, _, exists in artifact_rows):
    st.info(
        "Missing artifacts are expected if the KB pipeline hasn't been run against the configured "
        "`LINUS_KB_OUTPUTS_DIR`. Re-point the env var at a populated outputs directory to enable the "
        "Corpus Stats / Cluster Explorer / Paper Graph / Knowledge Graph / Search pages."
    )

# ── Environment configuration ───────────────────────────────────────────────
st.header("Environment configuration")
st.caption("All values overridable via environment variables — see `src/linus/app/config.py`.")
st.table([{"variable": k, "value": v} for k, v in config_summary().items()])

# ── Next steps pointer ──────────────────────────────────────────────────────
st.header("Pages")
st.markdown(
    "Pages appear in the sidebar as their files land in `src/linus/app/pages/`. "
    "Per the MVP build spec (`docs/specs/2026-05-19-mvp-build.md`), the planned set is:\n\n"
    "1. **Chat** — streaming chat over the Linus server (task B.1)\n"
    "2. **Corpus Stats** — KB-generated overview PNGs (task B.2)\n"
    "3. **Cluster Explorer** — broad → mid → fine drill-down (task B.3)\n"
    "4. **Paper Graph** — Sigma.js + 3d-force-graph embed (task B.4)\n"
    "5. **Knowledge Graph** — REBEL/NER viewer (task B.5)\n"
    "6. **Search** — keyword + semantic over the corpus (task B.6)"
)
