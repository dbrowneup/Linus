"""Linus Streamlit chat page — task B.1 of the MVP build.

Streaming chat UI backed by the Linus FastAPI server. Persists
``session_id`` in the URL query string so a browser refresh keeps the
conversation; loads stored history on every page load via
``GET /v1/sessions/{id}/messages``; streams responses via SSE from
``POST /v1/chat/completions`` with ``stream=true``.

Behavioral contract (depends on PRs A.1, A.3 being merged):

- **First visit / no ?session=XXX in URL**: page POSTs to
  ``/v1/sessions`` to mint a new session, then rewrites the URL with
  ``?session=<uuid>``. A subsequent refresh enters via the
  "existing session" path and the conversation persists.
- **Existing session (URL has ?session=XXX)**: page GETs the stored
  message history and renders it as alternating user/assistant
  bubbles before accepting new input.
- **New user message**: page emits a streaming POST against the
  chat endpoint with the new user message AND ``session_id``; the
  server prepends stored history server-side and persists the new
  turn pair after the response completes. The UI uses
  ``st.write_stream`` to render incoming tokens live in the
  assistant bubble.

The Linus server is assumed reachable at ``SERVER_URL`` (default
``http://localhost:8000``, override via ``LINUS_SERVER_URL``). If the
server isn't reachable the page surfaces an error rather than hanging.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

import httpx
import streamlit as st

from linus.app.config import SERVER_URL

st.set_page_config(page_title="Chat — Linus", page_icon="🜨", layout="wide")
st.title("🜨 Chat")
st.caption("Streaming chat over the Linus orchestration server.")


# ── server interaction helpers ────────────────────────────────────────────


@st.cache_data(ttl=10)
def _fetch_available_models() -> list[str]:
    """Return the list of locally-available Ollama model names.

    Cached for 10 seconds — model availability rarely changes mid-session
    and uncached this would hit /healthz on every Streamlit rerun.
    """
    try:
        resp = httpx.get(f"{SERVER_URL}/healthz", timeout=3.0)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        return list(models) if isinstance(models, list) else []
    except (httpx.RequestError, httpx.HTTPStatusError, ValueError):
        return []


def _ensure_session_id() -> str | None:
    """Read session_id from URL or mint a new one. Returns None on server failure."""
    existing = st.query_params.get("session")
    if existing:
        return existing
    # Mint a new session via the server so it's present in the store.
    try:
        resp = httpx.post(f"{SERVER_URL}/v1/sessions", json={}, timeout=5.0)
        resp.raise_for_status()
        sid = resp.json()["session_id"]
    except (httpx.RequestError, httpx.HTTPStatusError, KeyError, ValueError) as exc:
        st.error(f"Failed to create session: {exc}")
        return None
    st.query_params["session"] = sid
    return sid


def _fetch_history(session_id: str) -> list[dict[str, str]]:
    """Pull the stored conversation history. Empty list on any failure."""
    try:
        resp = httpx.get(f"{SERVER_URL}/v1/sessions/{session_id}/messages", timeout=5.0)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        messages = resp.json().get("messages", [])
        return [
            {"role": m["role"], "content": m["content"]}
            for m in messages
            if m.get("role") in ("user", "assistant") and m.get("content")
        ]
    except (httpx.RequestError, httpx.HTTPStatusError, ValueError):
        return []


def _stream_chat(session_id: str, model: str, user_prompt: str) -> Iterator[str]:
    """Yield content deltas from a streaming chat completion.

    Parses Server-Sent Events from ``/v1/chat/completions`` with
    ``stream=true``. Each SSE event is ``data: {json}\\n\\n``; we extract
    the ``choices[0].delta.content`` field per chunk and yield it. The
    terminator ``data: [DONE]`` ends iteration.
    """
    payload = {
        "model": model,
        "session_id": session_id,
        "stream": True,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    try:
        with httpx.stream(
            "POST",
            f"{SERVER_URL}/v1/chat/completions",
            json=payload,
            timeout=httpx.Timeout(300.0, connect=5.0),
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data = line[len("data: ") :].strip()
                if data == "[DONE]":
                    return
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if "error" in chunk:
                    yield f"\n\n_[stream error: {chunk['error'].get('message', 'unknown')}]_"
                    return
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta_content = choices[0].get("delta", {}).get("content")
                if delta_content:
                    yield delta_content
    except httpx.RequestError as exc:
        yield f"\n\n_[connection error: {exc}]_"
    except httpx.HTTPStatusError as exc:
        yield f"\n\n_[server error {exc.response.status_code}: {exc.response.text}]_"


# ── sidebar ───────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Settings")

    available_models = _fetch_available_models()
    if available_models:
        default_idx = available_models.index("qwen3:8b") if "qwen3:8b" in available_models else 0
        model = st.selectbox("Model", available_models, index=default_idx)
    else:
        st.warning("Server unreachable or no models pulled.")
        model = st.text_input("Model (manual)", value="qwen3:8b")

    st.divider()
    st.caption(f"Server: `{SERVER_URL}`")

    session_id = _ensure_session_id()
    if session_id:
        st.caption(f"Session: `{session_id[:8]}…`")
        if st.button("Clear conversation", use_container_width=True):
            # Drop the query param + clear local cache; the server-side session
            # row stays for audit but the UI starts fresh on next interaction.
            st.query_params.clear()
            st.session_state.pop("messages_cached_for", None)
            st.session_state.pop("messages", None)
            st.rerun()
    else:
        st.error("No session available — chat is disabled.")


# ── message history bootstrap ─────────────────────────────────────────────

if session_id is None:
    st.stop()  # Sidebar already showed the error; halt before render loop.

# Cache the loaded history per-session so we don't hit /messages on every rerun.
if st.session_state.get("messages_cached_for") != session_id:
    st.session_state.messages = _fetch_history(session_id)
    st.session_state.messages_cached_for = session_id


# ── render conversation ───────────────────────────────────────────────────

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ── handle new input ──────────────────────────────────────────────────────

prompt = st.chat_input("Ask Linus…")
if prompt:
    # 1. Render the user message immediately for responsiveness.
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Stream the assistant response into a fresh bubble.
    with st.chat_message("assistant"):
        full_text = st.write_stream(_stream_chat(session_id, model, prompt))

    # 3. Record the full assistant reply in our local cache. The server has
    #    already persisted it via the session_id mechanism, so the next page
    #    refresh will reload it from /messages — this local append just keeps
    #    the UI consistent within the current rerun cycle.
    if isinstance(full_text, str):
        st.session_state.messages.append({"role": "assistant", "content": full_text})
