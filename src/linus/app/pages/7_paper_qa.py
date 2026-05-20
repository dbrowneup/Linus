"""Linus Streamlit paper-qa page — task LX-2 of the 2026-05-19 KB hackathon-prep spec.

Citation-grounded paper-corpus Q&A UI over the four ``paperqa.*`` tools
shipped in PR #89 (:mod:`linus.knowledge.paperqa`). The page is a thin
front-end over the Linus orchestration server's direct tool-invocation
endpoint (``POST /v1/tools/{tool_name}/invoke``), so the page never
imports paper-qa in-process and the model is never in the loop.

Page-to-server contract
-----------------------

The page calls ``POST /v1/tools/paperqa.answer/invoke`` with
``{"arguments": {"query": question, "max_sources": max_sources}}`` and
renders the structured result directly. The response shape mirrors
:func:`linus.knowledge.paperqa.LinusPaperQA.answer` — a dict with
``answer`` (markdown), ``citations`` (list of provenance dicts), and
``formatted_answer`` (paper-qa's inline-citation pretty print) — wrapped
in the standard tool-invoke envelope::

    {"tool": "paperqa.answer", "result": {...}, "duration_ms": 12345.0}

The "Reset session" button calls ``POST /v1/tools/paperqa.reset/invoke``
with empty arguments to drop paper-qa's in-process Docs collection.

This page was originally implemented (PR #92) as a chat-completions
roundtrip with a system prompt steering the model into emitting a
``<!--LINUS_CITATIONS-->`` marker block that the page then parsed.
That worked but was fragile: citation fidelity depended on the model
following the marker-block instruction. The direct tool-invocation
route removes the model from the loop entirely.

State management
----------------

Flow is single-shot per question — paper-qa manages its own session
state inside the tool, so the page does not carry chat history.
``st.session_state`` holds the last submitted question, last answer
text, last citations list, and a status banner for the reset button.
Page-load does NOT auto-fire a query.

Errors
------

Every failure mode is surfaced inline:

- HTTP / connection failures → red ``st.error`` with the exception repr.
- 5xx from the server (tool raised) → red ``st.error`` with the
  structured detail from the response body.
- 4xx (404 unknown tool, 422 bad args) → red ``st.error`` so an operator
  spotting a regression can act on it without reading the server log.
- Zero-citation answers → an explicit "No citations were returned"
  notice rather than a silent empty expander.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
import streamlit as st

from linus.app.config import SERVER_URL

st.set_page_config(page_title="Paper Q&A — Linus", page_icon="🜨", layout="wide")
st.title("📚 Paper Q&A")
st.caption(
    "Citation-grounded question answering over your local paper corpus, via "
    "paper-qa's `Docs.aquery` routed through the Linus orchestration server's "
    "direct tool-invocation endpoint."
)


# ── paper-directory resolution (matches linus.knowledge.paperqa) ──────────


def _resolve_papers_dir() -> Path:
    """Mirror :func:`linus.knowledge.paperqa._papers_dir` for display only.

    Reads ``LINUS_PAPERQA_DIR`` then ``LINUS_PAPERS_DIR``, falling back to
    ``~/.linus/papers``. This function does NOT import paper-qa or the
    Linus paper-qa module — it's pure display logic. The actual indexing
    happens server-side when the tool is invoked.
    """
    raw = os.environ.get("LINUS_PAPERQA_DIR") or os.environ.get("LINUS_PAPERS_DIR")
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".linus" / "papers"


def _count_indexable_pdfs(papers_dir: Path) -> int | None:
    """Return the count of ``*.pdf`` files in the paper directory, or ``None``.

    ``None`` signals "directory does not exist" (so the UI can render the
    "create me" hint instead of a misleading zero). The count is shallow
    (top-level only) since paper-qa's default ingestion behavior is also
    flat.
    """
    if not papers_dir.exists() or not papers_dir.is_dir():
        return None
    try:
        return sum(1 for entry in papers_dir.iterdir() if entry.suffix.lower() == ".pdf")
    except (PermissionError, OSError):
        return None


# ── server interaction ────────────────────────────────────────────────────


@st.cache_data(ttl=10)
def _fetch_available_models() -> list[str]:
    """Pull the locally-available model list from ``/healthz``.

    Cached for 10s. Identical pattern to ``1_chat.py``. Empty list on any
    failure — the sidebar falls back to a free-text input in that case.
    The model selector itself is informational on this page: paper-qa's
    tool surface does not accept a ``model`` argument, so the selection
    has no effect on the invocation (see the disabled-with-tooltip note
    in the sidebar).
    """
    try:
        resp = httpx.get(f"{SERVER_URL}/healthz", timeout=3.0)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        return list(models) if isinstance(models, list) else []
    except (httpx.RequestError, httpx.HTTPStatusError, ValueError):
        return []


def _invoke_tool(tool_name: str, arguments: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """POST one tool-invoke request and return ``(result, error_message)``.

    Exactly one of the two return-tuple slots is non-empty: on success,
    ``error`` is ``None`` and ``result`` is the structured tool return
    value (already unwrapped from the ``ToolInvokeResponse`` envelope).
    On any failure ``result`` is ``None`` and ``error`` describes what
    went wrong. Errors are returned (not raised) so the page can render
    them inline rather than crashing the Streamlit script.
    """
    payload = {"arguments": arguments}
    try:
        # Generous timeout — paper-qa over a fresh index can spend tens
        # of seconds embedding + searching + summarizing before the tool
        # returns.
        resp = httpx.post(
            f"{SERVER_URL}/v1/tools/{tool_name}/invoke",
            json=payload,
            timeout=httpx.Timeout(600.0, connect=5.0),
        )
    except httpx.RequestError as exc:
        return None, f"Connection error talking to {SERVER_URL}: {exc!r}"

    if resp.status_code >= 400:
        # Try to surface the server's structured detail (e.g. "tool
        # raised: PaperQAConfigError: ..."); fall back to raw text.
        try:
            body = resp.json()
            detail = body.get("detail", body)
        except ValueError:
            detail = resp.text[:500]
        return None, f"Server returned HTTP {resp.status_code}: {detail}"

    try:
        body = resp.json()
    except ValueError as exc:
        return None, f"Server response was not JSON: {exc!r}"

    result = body.get("result")
    if result is None:
        return None, f"Unexpected response shape — no 'result' field: {body!r}"

    return result, None


# ── session-state initialisation ──────────────────────────────────────────


# The flow is single-shot per question — paper-qa manages its own session
# state inside the tool — so the page does NOT thread questions through a
# chat-style session. The session_state entries below are pure UI scratch:
# the last rendered question/answer/citations + a status banner for reset.
st.session_state.setdefault("paperqa_question", "")
st.session_state.setdefault("paperqa_answer_md", "")
st.session_state.setdefault("paperqa_formatted_answer", "")
st.session_state.setdefault("paperqa_citations", [])
st.session_state.setdefault("paperqa_status", None)
# ``paperqa_rigor`` holds the structured result from the auto-gate on
# :func:`linus.knowledge.paperqa.LinusPaperQA.answer`. ``None`` means
# either the gate failed-open (best-effort: the answer call succeeded
# but the gate raised internally) or the server is too old to return a
# ``rigor`` field. The renderer treats both identically.
st.session_state.setdefault("paperqa_rigor", None)


# ── sidebar ───────────────────────────────────────────────────────────────


with st.sidebar:
    st.header("Settings")

    available_models = _fetch_available_models()
    # The model selector is informational here. paperqa.answer's signature
    # is ``(query, max_sources)`` — there's no ``model`` kwarg, so the
    # selection has no effect on the invocation. Render it disabled with
    # a tooltip explaining why, so the page is visually consistent with
    # other pages (chat, anthropic) without misleading the user.
    _model_disabled_help = (
        "The paper-qa tool uses the server-configured Worker model "
        "(default ``qwen3:8b``, override via ``LINUS_PAPERQA_MODEL``). "
        "Per-call model selection is not supported by the tool signature, "
        "so this selector is read-only on this page."
    )
    if available_models:
        default_idx = available_models.index("qwen3:8b") if "qwen3:8b" in available_models else 0
        st.selectbox(
            "Model (server-configured)",
            available_models,
            index=default_idx,
            disabled=True,
            help=_model_disabled_help,
        )
    else:
        st.warning("Server unreachable or no models pulled.")
        st.text_input(
            "Model (server-configured)",
            value="qwen3:8b",
            disabled=True,
            help=_model_disabled_help,
        )

    max_sources = st.slider(
        "Max citation sources",
        min_value=1,
        max_value=20,
        value=10,
        step=1,
        help=(
            "Upper bound on the number of paper-qa Context objects rolled into "
            "the answer. Passed directly to `paperqa.answer(max_sources=…)`."
        ),
    )

    st.divider()
    st.caption(f"Server: `{SERVER_URL}`")
    st.caption("Invocation: direct `paperqa.answer` tool call (model not in loop).")

    if st.button("Reset paper-qa session", use_container_width=True):
        with st.spinner("Calling `paperqa.reset`…"):
            _, err = _invoke_tool("paperqa.reset", {})
        if err:
            st.error(f"Reset failed: {err}")
        else:
            st.session_state.paperqa_question = ""
            st.session_state.paperqa_answer_md = ""
            st.session_state.paperqa_formatted_answer = ""
            st.session_state.paperqa_citations = []
            st.session_state.paperqa_rigor = None
            st.session_state.paperqa_status = "Paper-qa session reset. The next question will rebuild the index."
            st.rerun()


# ── paper-directory status line ───────────────────────────────────────────


papers_dir = _resolve_papers_dir()
pdf_count = _count_indexable_pdfs(papers_dir)

status_cols = st.columns([3, 1])
with status_cols[0]:
    if pdf_count is None:
        st.warning(
            f"Paper directory `{papers_dir}` does not exist. "
            "Create it and drop PDFs in, or set `LINUS_PAPERQA_DIR` "
            "to an existing directory."
        )
    elif pdf_count == 0:
        st.warning(f"Paper directory `{papers_dir}` is empty — no PDFs to query. Drop some PDFs in and rerun.")
    else:
        st.info(f"Paper directory: `{papers_dir}` — **{pdf_count}** PDF{'s' if pdf_count != 1 else ''} on disk.")
with status_cols[1]:
    st.caption("Tools: `paperqa.search`, `paperqa.gather_evidence`, `paperqa.answer`, `paperqa.reset`.")


# ── question input + Ask button ───────────────────────────────────────────


question = st.text_area(
    "Question",
    value=st.session_state.paperqa_question,
    placeholder=(
        "e.g. What chain length does TS1 prefer for the cyclic diterpenes "
        "in Botryococcus braunii? — anything answerable from the indexed corpus."
    ),
    height=100,
)

ask_col, _ = st.columns([1, 5])
ask_clicked = ask_col.button("Ask", type="primary", use_container_width=True)


# ── execute on Ask ────────────────────────────────────────────────────────


if ask_clicked:
    if not question.strip():
        st.warning("Type a question first.")
    else:
        st.session_state.paperqa_question = question
        st.session_state.paperqa_status = None
        with st.spinner(
            "Invoking `paperqa.answer` — embedding, retrieval, summarization. This can take 10-60 s on a cold index."
        ):
            result, err = _invoke_tool(
                "paperqa.answer",
                {"query": question.strip(), "max_sources": max_sources},
            )

        if err:
            st.session_state.paperqa_answer_md = ""
            st.session_state.paperqa_formatted_answer = ""
            st.session_state.paperqa_citations = []
            st.session_state.paperqa_rigor = None
            st.error(err)
        elif not isinstance(result, dict):
            st.session_state.paperqa_answer_md = ""
            st.session_state.paperqa_formatted_answer = ""
            st.session_state.paperqa_citations = []
            st.session_state.paperqa_rigor = None
            st.error(f"Tool returned an unexpected shape (expected dict, got {type(result).__name__}): {result!r}")
        else:
            # paperqa.answer's contract: {answer, citations, question,
            # formatted_answer, rigor}. Be tolerant — surface whatever
            # the tool returned, defaulting missing fields.
            answer_md = str(result.get("answer") or "").strip()
            formatted = str(result.get("formatted_answer") or "").strip()
            citations_raw = result.get("citations") or []
            citations = list(citations_raw) if isinstance(citations_raw, list) else []
            rigor_raw = result.get("rigor")
            # ``rigor`` may be None (gate failed-open), a dict (gate ran),
            # or absent (older server). Normalize None / non-dict to None
            # so the renderer treats them identically.
            rigor = rigor_raw if isinstance(rigor_raw, dict) else None
            st.session_state.paperqa_answer_md = answer_md
            st.session_state.paperqa_formatted_answer = formatted
            st.session_state.paperqa_citations = citations
            st.session_state.paperqa_rigor = rigor


# ── rigor-badge renderer ──────────────────────────────────────────────────


def _render_rigor_badge(rigor: dict[str, Any] | None) -> None:
    """Render the per-answer rigor-gate badge inline.

    The badge is colored by the gate's verdict:

    - **green** ``Grounded`` — ``passed=True`` and zero warnings.
    - **yellow** ``Grounded with warnings (N)`` — ``passed=True`` but
      ``warning_count>0``. Warnings include a missing backend, a stub
      entity lookup, or a confidence-divergence signal — none of which
      block the answer.
    - **red** ``Gate failed (N errors)`` — ``passed=False``. At least
      one ``error``-severity failure (unresolved citation,
      page-out-of-range). A reviewer should treat this as a hard
      regression in the answer's grounding.
    - **informational** ``Rigor check not available`` — the gate
      raised internally or the server didn't return a ``rigor`` field.
      The answer is still rendered above.

    Below the badge, an expandable "Rigor details" section lists each
    failure with its kind, severity, target, and detail message.
    ``confidence_calibration`` is surfaced as a small line when present.
    """
    if rigor is None:
        st.caption("i Rigor check not available for this answer.")
        return

    passed = bool(rigor.get("passed"))
    error_count = int(rigor.get("error_count") or 0)
    warning_count = int(rigor.get("warning_count") or 0)
    failures = rigor.get("failures") or []
    calibration = rigor.get("confidence_calibration")

    # Single-call colored badge using Streamlit's success/warning/error.
    if passed and warning_count == 0:
        st.success("Grounded — all citations and entities resolved.")
    elif passed:
        st.warning(
            f"Grounded with warnings ({warning_count}) — answer passed the gate "
            "but at least one informational signal fired."
        )
    else:
        st.error(
            f"Gate failed ({error_count} error{'s' if error_count != 1 else ''}) — "
            "the answer's grounding has at least one hard failure."
        )

    # Confidence-calibration line, when populated. Calibration is a 0..1
    # float; surface it with two-decimal precision so the demo audience
    # sees the same shape the rigor module emits.
    if calibration is not None:
        try:
            cal_f = float(calibration)
            st.caption(f"Confidence calibration: {cal_f:.2f}")
        except (TypeError, ValueError):
            pass

    # The failures list is the actionable detail. Expand it by default
    # when the gate did NOT pass so the human's eye lands on the
    # specifics; collapse it for the warnings-only case so the answer
    # surface stays uncluttered.
    if failures:
        with st.expander(
            f"Rigor details ({len(failures)})",
            expanded=not passed,
        ):
            for failure in failures:
                if not isinstance(failure, dict):
                    st.markdown(f"- {failure}")
                    continue
                kind = failure.get("kind") or "—"
                severity = failure.get("severity") or "—"
                target = failure.get("target")
                detail = failure.get("detail") or ""
                target_str = f" · target `{target}`" if target else ""
                st.markdown(f"- **{kind}** ({severity}){target_str}: {detail}")


# ── render the current answer + citations ─────────────────────────────────


if st.session_state.paperqa_status:
    st.success(st.session_state.paperqa_status)

if st.session_state.paperqa_answer_md or st.session_state.paperqa_formatted_answer:
    st.subheader("Answer")
    if st.session_state.paperqa_answer_md:
        st.markdown(st.session_state.paperqa_answer_md)
    elif st.session_state.paperqa_formatted_answer:
        # Fall back to paper-qa's pretty-printed form when the bare
        # ``answer`` field is empty — happens occasionally on degenerate
        # queries against tiny corpora.
        st.markdown(st.session_state.paperqa_formatted_answer)

    # Rigor badge sits between the answer and the citations expander,
    # so reviewers see the gate verdict in the same eye-sweep as the
    # answer text but before they drill into the per-citation list.
    _render_rigor_badge(st.session_state.paperqa_rigor)

    citations = st.session_state.paperqa_citations
    with st.expander(
        f"Citations ({len(citations)})",
        expanded=bool(citations),
    ):
        if not citations:
            st.info(
                "No citations were returned for this query. The corpus may "
                "be empty, or the question may not match any indexed content."
            )
        else:
            for idx, cit in enumerate(citations, start=1):
                if not isinstance(cit, dict):
                    # Defensive — if the tool emitted a bare string per
                    # entry instead of a dict, still render it readably.
                    st.markdown(f"**{idx}.** {cit}")
                    st.divider()
                    continue
                paper_id = cit.get("paper_id") or "—"
                page = cit.get("page")
                score = cit.get("score", 0.0)
                excerpt = cit.get("excerpt") or ""
                page_str = f"p. {page}" if page is not None else "page unknown"
                try:
                    score_str = f"{float(score):.3f}"
                except (TypeError, ValueError):
                    score_str = str(score)
                st.markdown(f"**{idx}. `{paper_id}`** · {page_str} · score `{score_str}`")
                if excerpt:
                    # Block-quote keeps long excerpts visually distinct from
                    # the answer prose above.
                    quoted = "\n".join(f"> {line}" for line in excerpt.splitlines())
                    st.markdown(quoted)
                st.divider()
elif not ask_clicked:
    # Pristine state — give the user a hint about what the page does.
    st.info(
        "Type a question above and click **Ask**. Linus will invoke the "
        "server-side `paperqa.answer` tool directly and render the "
        "citation-grounded result here."
    )
