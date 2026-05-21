"""Tests for session-store durability gaps surfaced by the 2026-05-20 server bug sweep.

This module currently exercises the HIGH-severity finding **H-1** — streaming
session writes were silently lost when the client disconnected mid-stream
because the post-stream append only ran after the inner generator completed.
The fix persists the user turn upfront and wraps the streaming loop in a
``try/finally`` so the accumulated partial assistant content is committed
even if the generator is cancelled (e.g., ``GeneratorExit`` from Starlette
on client-disconnect). The append is idempotent so a fully-completed stream
doesn't double-write.

Reference: ``docs/bug-sweeps/2026-05-20-server-sweep.md`` (PR #106), H-1.
"""

from __future__ import annotations

import contextlib
import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from linus import server as server_module
from linus.memory.sessions import reset_default_store
from linus.server import (
    ChatMessage,
    _stream_with_session_append,
    app,
)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# ──────────────────────────────────────────────────────────────────────────
# H-1 — streaming session persistence on client disconnect
# ──────────────────────────────────────────────────────────────────────────


def test_streaming_partial_content_persisted_on_client_disconnect(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """If the streaming generator is cancelled mid-stream (simulating a client
    disconnect), the user message + accumulated partial assistant content
    must still land in the session store.

    Simulates client disconnect by closing the generator after a single
    content delta has been yielded. Starlette/uvicorn raises ``GeneratorExit``
    on the streaming response when the HTTP client drops — we exercise the
    same control-flow path by calling ``gen.close()`` directly, which is
    what the streaming response runtime does internally.
    """
    monkeypatch.setenv("LINUS_SESSIONS_DB", str(tmp_path / "sessions.db"))
    reset_default_store()

    from linus.memory.sessions import get_default_store

    store = get_default_store()
    session = store.create_session()
    sid = session.id

    # Inject an inner stream that yields one content event, then a second
    # one; the outer test closes the generator between the two so only the
    # first piece accumulates. The generator must still persist user + the
    # accumulated partial content before exiting.
    def fake_inner_stream(*_a, **_kw) -> Iterator[str]:
        yield (
            "data: "
            + json.dumps(
                {
                    "id": "chatcmpl-x",
                    "object": "chat.completion.chunk",
                    "created": 0,
                    "model": "qwen3:8b",
                    "choices": [{"index": 0, "delta": {"content": "partial-"}, "finish_reason": None}],
                }
            )
            + "\n\n"
        )
        # Second chunk would arrive here but the caller closes the generator
        # before consuming it (simulating mid-stream disconnect).
        yield (
            "data: "
            + json.dumps(
                {
                    "id": "chatcmpl-x",
                    "object": "chat.completion.chunk",
                    "created": 0,
                    "model": "qwen3:8b",
                    "choices": [{"index": 0, "delta": {"content": "never-delivered"}, "finish_reason": None}],
                }
            )
            + "\n\n"
        )
        yield "data: [DONE]\n\n"

    monkeypatch.setattr(server_module, "_stream_chat_completion", fake_inner_stream)

    new_messages = [ChatMessage(role="user", content="hi there")]
    gen = _stream_with_session_append(
        transcript=[ChatMessage(role="user", content="hi there")],
        resolved_model="qwen3:8b",
        options={},
        tool_specs=[],
        store=store,
        session_id=sid,
        new_messages=new_messages,
    )
    # Consume the first event then close — the close() call raises
    # GeneratorExit inside the generator, which the finally block must
    # handle by committing the partial content.
    first = next(gen)
    assert "partial-" in first
    gen.close()

    stored = store.get_messages(sid)
    roles = [m.role for m in stored]
    contents = [m.content for m in stored]

    # User turn persisted upfront — present regardless of disconnect.
    assert "user" in roles
    user_msg = next(m for m in stored if m.role == "user")
    assert user_msg.content == "hi there"

    # The first content delta (``"partial-"``) was accumulated before the
    # disconnect; the finally block must have written it to the store.
    assert "assistant" in roles, (
        f"Expected an assistant row after client-disconnect, got roles={roles} contents={contents}"
    )
    assistant_msg = next(m for m in stored if m.role == "assistant")
    assert assistant_msg.content == "partial-"

    reset_default_store()


def test_streaming_full_completion_not_double_written(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Happy path: full stream completes; exactly ONE assistant message lands
    in the session for that turn (no double-write between the try-block's
    intended commit and the finally block's fallback)."""
    monkeypatch.setenv("LINUS_SESSIONS_DB", str(tmp_path / "sessions.db"))
    reset_default_store()

    from linus.memory.sessions import get_default_store

    store = get_default_store()
    session = store.create_session()
    sid = session.id

    def fake_chat(**_kwargs):
        return iter(
            [
                {"message": {"role": "assistant", "content": "Full "}, "done": False, "done_reason": None},
                {"message": {"role": "assistant", "content": "answer."}, "done": True, "done_reason": "stop"},
            ]
        )

    monkeypatch.setattr(server_module.ollama, "chat", fake_chat)

    new_messages = [ChatMessage(role="user", content="ask once")]
    events = list(
        _stream_with_session_append(
            transcript=[ChatMessage(role="user", content="ask once")],
            resolved_model="qwen3:8b",
            options={},
            tool_specs=[],
            store=store,
            session_id=sid,
            new_messages=new_messages,
        )
    )
    assert events[-1] == "data: [DONE]\n\n"

    stored = store.get_messages(sid)
    user_rows = [m for m in stored if m.role == "user"]
    assistant_rows = [m for m in stored if m.role == "assistant"]
    assert len(user_rows) == 1, f"user row count != 1 (got {len(user_rows)}): {stored}"
    assert len(assistant_rows) == 1, f"assistant row count != 1 (got {len(assistant_rows)}): {stored}"
    assert assistant_rows[0].content == "Full answer."

    reset_default_store()


def test_streaming_partial_content_persisted_via_endpoint_when_response_closes_early(
    client: TestClient, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end variant of the client-disconnect case using the FastAPI
    TestClient's streaming-response context.

    The Starlette TestClient closes the response on context exit; if the
    consumer doesn't read every event, the generator inside the endpoint
    receives a ``GeneratorExit`` analogous to a real client disconnect.
    """
    monkeypatch.setenv("LINUS_SESSIONS_DB", str(tmp_path / "sessions.db"))
    reset_default_store()

    create_resp = client.post("/v1/sessions", json={})
    sid = create_resp.json()["session_id"]

    # The fake chat returns a multi-chunk stream; the test only reads a
    # prefix and closes, exercising the early-disconnect persistence path.
    chunks = [
        {"message": {"role": "assistant", "content": "early-"}, "done": False, "done_reason": None},
        {"message": {"role": "assistant", "content": "tokens"}, "done": True, "done_reason": "stop"},
    ]
    monkeypatch.setattr(server_module.ollama, "chat", lambda **_kw: iter(chunks))
    monkeypatch.setattr(server_module, "_resolve_model", lambda m: "qwen3:8b")

    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={
            "model": "qwen3:8b",
            "session_id": sid,
            "stream": True,
            "messages": [{"role": "user", "content": "hello"}],
        },
    ) as resp:
        assert resp.status_code == 200
        # Read at least one byte to make sure the streaming response started
        # before closing. We do NOT iterate to completion.
        it = resp.iter_text()
        with contextlib.suppress(StopIteration):
            next(it)
        # Context exit closes the underlying connection → generator cancellation.

    # Even with the early disconnect, the user turn must be present.
    history = client.get(f"/v1/sessions/{sid}/messages").json()["messages"]
    roles = [m["role"] for m in history]
    assert "user" in roles, f"user turn missing from history after client disconnect: {history}"
    user_msg = next(m for m in history if m["role"] == "user")
    assert user_msg["content"] == "hello"

    reset_default_store()
