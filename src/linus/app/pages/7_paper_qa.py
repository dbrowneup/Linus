"""Linus Streamlit paper-qa page — task LX-2 of the 2026-05-19 KB hackathon-prep spec.

Citation-grounded paper-corpus Q&A UI over the four ``paperqa.*`` tools
shipped in PR #89 (:mod:`linus.knowledge.paperqa`). The page is a thin
front-end over the Linus orchestration server's OpenAI-compatible
chat-completions endpoint; the server resolves any ``paperqa.answer`` /
``paperqa.search`` / ``paperqa.reset`` tool calls server-side through
:data:`linus.tools.default_registry`, so the page never imports paper-qa
in-process.

Page-to-server contract
-----------------------

The page calls ``POST /v1/chat/completions`` with a system prompt that
instructs the model to:

1. Invoke the ``paperqa.answer`` tool with the user's question and the
   configured ``max_sources``.
2. After the tool result returns, format the final reply as a Markdown
   answer followed by a fenced JSON block delimited by the marker
   ``<!--LINUS_CITATIONS-->`` carrying the raw citations list verbatim.

The page parses the JSON block out of the assistant's reply to render
the citations expander. If the marker is missing (model didn't follow
the format) we surface a soft warning and still render the natural-text
answer — never a silent empty state.

The "Reset session" button independently issues a chat request that
forces ``paperqa.reset`` so the in-process Docs collection is cleared.

State management
----------------

``st.session_state`` tracks the current question, current answer text,
current citations list, and a UI-local ``paperqa_session_id`` (chat
session id used to thread the conversation through the server's session
store, allowing the model to see its own prior turns within the page).
Page-load does NOT auto-fire a query — the user must click Ask.

Errors
------

Every failure mode is surfaced inline:

- HTTP / connection failures → red ``st.error`` with the exception repr.
- Server-side tool errors (paper-qa unavailable, no papers indexed) →
  visible warning citing the underlying message.
- Zero-citation answers → an explicit "No citations were returned"
  notice rather than a silent empty expander.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path
from typing import Any

import httpx
import streamlit as st

from linus.app.config import SERVER_URL

st.set_page_config(page_title="Paper Q&A — Linus", page_icon="🜨", layout="wide")
st.title("📚 Paper Q&A")
st.caption(
    "Citation-grounded question answering over your local paper corpus, via "
    "paper-qa's `Docs.aquery` routed through the Linus orchestration server."
)


# ── paper-directory resolution (matches linus.knowledge.paperqa) ──────────


def _resolve_papers_dir() -> Path:
    """Mirror :func:`linus.knowledge.paperqa._papers_dir` for display only.

    Reads ``LINUS_PAPERQA_DIR`` then ``LINUS_PAPERS_DIR``, falling back to
    ``~/.linus/papers``. This function does NOT import paper-qa or the
    Linus paper-qa module — it's pure display logic. The actual indexing
    happens server-side when the model invokes the tool.
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
    """
    try:
        resp = httpx.get(f"{SERVER_URL}/healthz", timeout=3.0)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        return list(models) if isinstance(models, list) else []
    except (httpx.RequestError, httpx.HTTPStatusError, ValueError):
        return []


# Marker the system prompt asks the model to wrap the citations JSON with.
# Chosen as an HTML comment so it survives Markdown rendering invisibly if
# the parser misses it. The pattern is liberal — model frequently emits
# small whitespace variations.
_CITATIONS_MARKER = "<!--LINUS_CITATIONS-->"
_CITATIONS_PATTERN = re.compile(
    r"<!--\s*LINUS_CITATIONS\s*-->\s*```(?:json)?\s*(\[.*?\]|\{.*?\})\s*```",
    re.DOTALL | re.IGNORECASE,
)


def _build_system_prompt(max_sources: int) -> str:
    """Return the system prompt steering the model into the paperqa.answer flow.

    The prompt is explicit because qwen3:8b's tool-use compliance is
    high-but-not-perfect at this scale; an unambiguous instruction with
    a worked example gives us the citations roundtrip with high fidelity.
    """
    return (
        "You are Linus, a citation-grounded research assistant. When the user "
        "asks a question about the local paper corpus, you MUST call the "
        "`paperqa.answer` tool with their question as the `query` argument "
        f"and `max_sources={max_sources}`. After the tool returns its JSON "
        "result, write your final reply in this exact two-part format:\n"
        "\n"
        "1. The natural-language answer (use the `answer` field of the tool "
        "result; render it as Markdown).\n"
        f"2. Immediately after the answer, on its own line, emit the marker "
        f"`{_CITATIONS_MARKER}` followed by a fenced ```json code block "
        "containing the `citations` list from the tool result verbatim. "
        "Example shape:\n"
        "\n"
        "```\n"
        "<paragraph answer here>\n"
        "\n"
        f"{_CITATIONS_MARKER}\n"
        "```json\n"
        '[{"paper_id": "abc", "page": 3, "excerpt": "...", "score": 0.91}]\n'
        "```\n"
        "```\n"
        "\n"
        "Do NOT add commentary after the JSON block. Do NOT reformat the "
        "citations — preserve all four fields per entry. If the tool returns "
        "no citations, emit an empty array `[]` after the marker."
    )


def _build_reset_system_prompt() -> str:
    """System prompt for the reset path — instructs the model to call paperqa.reset."""
    return (
        "You are Linus. The user has requested that the paper-qa session "
        "be cleared. Call the `paperqa.reset` tool (it takes no arguments) "
        "and then reply with a single short sentence confirming the reset."
    )


def _call_chat_completions(
    *, system_prompt: str, user_prompt: str, model: str, session_id: str
) -> tuple[str, str | None]:
    """POST one chat-completion request and return ``(content, error_message)``.

    Exactly one of the two return-tuple slots is non-empty: on success the
    error is ``None`` and ``content`` is the assistant's reply string; on
    failure ``content`` is empty and ``error_message`` describes what went
    wrong. Errors are returned (not raised) so the page can render them
    inline rather than crashing the Streamlit script.
    """
    payload: dict[str, Any] = {
        "model": model,
        "session_id": session_id,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    try:
        # Generous timeout — paper-qa over a fresh index can spend tens of
        # seconds embedding + searching + summarizing before the assistant
        # turn completes.
        resp = httpx.post(
            f"{SERVER_URL}/v1/chat/completions",
            json=payload,
            timeout=httpx.Timeout(600.0, connect=5.0),
        )
    except httpx.RequestError as exc:
        return "", f"Connection error talking to {SERVER_URL}: {exc!r}"

    if resp.status_code >= 400:
        return "", f"Server returned HTTP {resp.status_code}: {resp.text[:500]}"

    try:
        body = resp.json()
    except ValueError as exc:
        return "", f"Server response was not JSON: {exc!r}"

    try:
        content = body["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        return "", f"Unexpected response shape: {exc!r}; body={body!r}"

    return content, None


def _parse_answer_and_citations(reply: str) -> tuple[str, list[dict[str, Any]], str | None]:
    """Split the assistant reply into ``(answer_md, citations, warning)``.

    The system prompt asks for a ``<!--LINUS_CITATIONS-->`` marker followed
    by a fenced JSON code block. If we find the marker we strip everything
    from the marker onward out of the answer body and parse the JSON. If
    the marker is missing OR the JSON is malformed we still return the full
    reply as the answer and surface a non-fatal warning to the caller.
    """
    if not reply:
        return "", [], "Empty response from the server."

    match = _CITATIONS_PATTERN.search(reply)
    if match is None:
        return reply.strip(), [], (
            "Model did not emit the expected citations block — rendering the "
            "raw answer only. The underlying tool may still have returned "
            "citations server-side; rerun if a citation list is required."
        )

    answer_md = reply[: match.start()].strip()
    raw_json = match.group(1).strip()
    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        return reply.strip(), [], (
            f"Citations block found but JSON failed to parse ({exc!r}); "
            "rendering raw answer."
        )

    # Tolerate either a bare list or an envelope dict with a 'citations' key.
    citations: list[dict[str, Any]]
    if isinstance(parsed, dict):
        candidate = parsed.get("citations", [])
        citations = list(candidate) if isinstance(candidate, list) else []
    elif isinstance(parsed, list):
        citations = parsed
    else:
        return answer_md, [], (
            f"Citations block parsed as {type(parsed).__name__}, not list/dict; "
            "rendering raw answer."
        )

    return answer_md, citations, None


# ── session-state initialisation ──────────────────────────────────────────


# A page-local chat session id so the underlying server-side session_store
# threads our requests together. We mint it once per browser session via
# st.session_state — no need to round-trip /v1/sessions because the server
# auto-creates the row on first POST when the id doesn't exist yet.
if "paperqa_session_id" not in st.session_state:
    st.session_state.paperqa_session_id = f"paperqa-{uuid.uuid4().hex}"

# Hold-over containers for the current Q/A so a Streamlit rerun (sidebar
# tweak, button click) doesn't wipe the answer on the screen.
st.session_state.setdefault("paperqa_question", "")
st.session_state.setdefault("paperqa_answer_md", "")
st.session_state.setdefault("paperqa_citations", [])
st.session_state.setdefault("paperqa_warning", None)
st.session_state.setdefault("paperqa_status", None)


# ── sidebar ───────────────────────────────────────────────────────────────


with st.sidebar:
    st.header("Settings")

    available_models = _fetch_available_models()
    if available_models:
        default_idx = (
            available_models.index("qwen3:8b") if "qwen3:8b" in available_models else 0
        )
        model = st.selectbox("Model", available_models, index=default_idx)
    else:
        st.warning("Server unreachable or no models pulled.")
        model = st.text_input("Model (manual)", value="qwen3:8b")

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
    st.caption(f"Session: `{st.session_state.paperqa_session_id[:14]}…`")

    if st.button("Reset paper-qa session", use_container_width=True):
        with st.spinner("Asking the model to call paperqa.reset…"):
            _, err = _call_chat_completions(
                system_prompt=_build_reset_system_prompt(),
                user_prompt="Please clear the paper-qa session.",
                model=model,
                session_id=st.session_state.paperqa_session_id,
            )
        if err:
            st.error(f"Reset failed: {err}")
        else:
            # Also clear the page-local Q&A scratch state so the screen
            # reflects the reset visibly.
            st.session_state.paperqa_question = ""
            st.session_state.paperqa_answer_md = ""
            st.session_state.paperqa_citations = []
            st.session_state.paperqa_warning = None
            st.session_state.paperqa_status = (
                "Paper-qa session reset. The next question will rebuild the index."
            )
            # Mint a fresh underlying chat session_id so the model doesn't
            # see the prior tool-loop history of the reset turn.
            st.session_state.paperqa_session_id = f"paperqa-{uuid.uuid4().hex}"
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
        st.warning(
            f"Paper directory `{papers_dir}` is empty — no PDFs to query. "
            "Drop some PDFs in and rerun."
        )
    else:
        st.info(
            f"Paper directory: `{papers_dir}` — **{pdf_count}** PDF"
            f"{'s' if pdf_count != 1 else ''} on disk."
        )
with status_cols[1]:
    st.caption(
        "Tools: `paperqa.search`, `paperqa.gather_evidence`, "
        "`paperqa.answer`, `paperqa.reset`."
    )


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
            "Routing the question through paper-qa — embedding, retrieval, "
            "summarization. This can take 10–60 s on a cold index."
        ):
            reply, err = _call_chat_completions(
                system_prompt=_build_system_prompt(max_sources),
                user_prompt=question.strip(),
                model=model,
                session_id=st.session_state.paperqa_session_id,
            )

        if err:
            st.session_state.paperqa_answer_md = ""
            st.session_state.paperqa_citations = []
            st.session_state.paperqa_warning = None
            st.error(err)
        else:
            answer_md, citations, warning = _parse_answer_and_citations(reply)
            st.session_state.paperqa_answer_md = answer_md
            st.session_state.paperqa_citations = citations
            st.session_state.paperqa_warning = warning


# ── render the current answer + citations ─────────────────────────────────


if st.session_state.paperqa_status:
    st.success(st.session_state.paperqa_status)

if st.session_state.paperqa_answer_md:
    st.subheader("Answer")
    st.markdown(st.session_state.paperqa_answer_md)

    if st.session_state.paperqa_warning:
        st.warning(st.session_state.paperqa_warning)

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
                    # Defensive — if the model emitted a bare string per
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
                st.markdown(
                    f"**{idx}. `{paper_id}`** · {page_str} · score `{score_str}`"
                )
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
        "server-side `paperqa.answer` tool and render the model's "
        "citation-grounded reply here."
    )
