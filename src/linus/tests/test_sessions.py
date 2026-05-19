"""Tests for the session store (task A.3) and its server integration.

Two suites in one file:

1. **Store-level tests** — directly exercise :class:`SessionStore` against
   an in-memory SQLite DB. Pure unit tests.
2. **Endpoint tests** — exercise the FastAPI server's session-aware
   chat-completions endpoint and the new ``/v1/sessions`` endpoints.
   Ollama is patched throughout for hermeticity.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from linus.memory.sessions import (
    Session,
    SessionStore,
    StoredMessage,
    in_memory_store,
    reset_default_store,
)
from linus.server import app


# ── Store-level tests ──────────────────────────────────────────────────────


def test_create_session_returns_record() -> None:
    with in_memory_store() as store:
        session = store.create_session(model="qwen3:8b", system_prompt="You are helpful")
    assert isinstance(session, Session)
    assert session.id  # non-empty UUID
    assert session.model == "qwen3:8b"
    assert session.system_prompt == "You are helpful"
    assert session.created_at > 0


def test_create_session_honors_supplied_id() -> None:
    with in_memory_store() as store:
        session = store.create_session(session_id="custom-id-123")
    assert session.id == "custom-id-123"


def test_ensure_session_idempotent() -> None:
    with in_memory_store() as store:
        s1 = store.ensure_session("sid-1", model="qwen3:8b")
        s2 = store.ensure_session("sid-1", model="qwen3:8b")
    assert s1.id == s2.id
    assert s1.created_at == s2.created_at


def test_append_message_assigns_dense_idx() -> None:
    with in_memory_store() as store:
        store.create_session(session_id="sid-1")
        m1 = store.append_message("sid-1", "user", "Hello")
        m2 = store.append_message("sid-1", "assistant", "Hi there")
        m3 = store.append_message("sid-1", "user", "How are you?")
    assert m1.idx == 0
    assert m2.idx == 1
    assert m3.idx == 2


def test_append_messages_atomic_batch() -> None:
    with in_memory_store() as store:
        store.create_session(session_id="sid-1")
        results = store.append_messages(
            "sid-1",
            [
                ("user", "First"),
                ("assistant", "Second"),
                ("user", "Third"),
            ],
        )
    assert [m.idx for m in results] == [0, 1, 2]
    assert [m.role for m in results] == ["user", "assistant", "user"]


def test_get_messages_orders_by_idx_asc() -> None:
    with in_memory_store() as store:
        store.create_session(session_id="sid-1")
        store.append_message("sid-1", "user", "first")
        store.append_message("sid-1", "assistant", "second")
        store.append_message("sid-1", "user", "third")
        messages = store.get_messages("sid-1")
    assert [m.content for m in messages] == ["first", "second", "third"]
    assert [m.idx for m in messages] == [0, 1, 2]


def test_get_session_returns_none_for_unknown_id() -> None:
    with in_memory_store() as store:
        assert store.get_session("nope") is None


def test_two_sessions_have_independent_idx() -> None:
    with in_memory_store() as store:
        store.create_session(session_id="A")
        store.create_session(session_id="B")
        store.append_message("A", "user", "from A")
        store.append_message("B", "user", "from B")
        store.append_message("A", "assistant", "to A")
        # Reads must happen inside the `with` — :memory: store closes on exit.
        assert [m.idx for m in store.get_messages("A")] == [0, 1]
        assert [m.idx for m in store.get_messages("B")] == [0]


def test_delete_session_cascades_to_messages() -> None:
    with in_memory_store() as store:
        store.create_session(session_id="doomed")
        store.append_message("doomed", "user", "hi")
        store.append_message("doomed", "assistant", "bye")
        assert store.delete_session("doomed") is True
        assert store.get_session("doomed") is None
        assert store.get_messages("doomed") == []
    # Deleting an unknown session returns False, not an error.
    with in_memory_store() as store:
        assert store.delete_session("ghost") is False


def test_list_sessions_most_recent_first() -> None:
    import time as time_module

    with in_memory_store() as store:
        store.create_session(session_id="first")
        time_module.sleep(0.01)
        store.create_session(session_id="second")
        sessions = store.list_sessions()
    # Most recent first.
    assert sessions[0].id == "second"
    assert sessions[1].id == "first"


# ── Server-integration tests ───────────────────────────────────────────────


@pytest.fixture()
def client(tmp_path, monkeypatch) -> TestClient:
    """TestClient with an isolated SessionStore pointing at a tmp DB."""
    db_path = tmp_path / "sessions.db"
    monkeypatch.setenv("LINUS_SESSIONS_DB", str(db_path))
    reset_default_store()
    yield TestClient(app)
    reset_default_store()


def _ok_ollama_response(text: str = "ok") -> dict[str, Any]:
    return {
        "message": {"role": "assistant", "content": text},
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": 5,
        "eval_count": 3,
    }


def test_post_sessions_creates_session(client: TestClient) -> None:
    resp = client.post("/v1/sessions", json={"model": "qwen3:8b"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"]
    assert body["model"] == "qwen3:8b"
    assert body["created_at"] > 0


def test_post_sessions_empty_body(client: TestClient) -> None:
    """Empty/no body should still create a session."""
    resp = client.post("/v1/sessions", json={})
    assert resp.status_code == 200
    assert resp.json()["session_id"]


def test_post_sessions_honors_client_id(client: TestClient) -> None:
    resp = client.post("/v1/sessions", json={"session_id": "client-supplied-uuid"})
    assert resp.status_code == 200
    assert resp.json()["session_id"] == "client-supplied-uuid"


def test_get_session_messages_404_for_unknown(client: TestClient) -> None:
    resp = client.get("/v1/sessions/nonexistent/messages")
    assert resp.status_code == 404


def test_get_session_messages_returns_empty_for_new_session(client: TestClient) -> None:
    create = client.post("/v1/sessions", json={}).json()
    resp = client.get(f"/v1/sessions/{create['session_id']}/messages")
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == create["session_id"]
    assert body["messages"] == []


def test_chat_completions_with_session_id_persists_history(client: TestClient) -> None:
    """After a chat completion with session_id, the new turn is stored."""
    create = client.post("/v1/sessions", json={}).json()
    sid = create["session_id"]

    with patch("linus.server.ollama.chat", return_value=_ok_ollama_response("Hello!")), patch(
        "linus.server._resolve_model", return_value="qwen3:8b"
    ):
        resp = client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen3:8b",
                "session_id": sid,
                "messages": [{"role": "user", "content": "Hi"}],
            },
        )

    assert resp.status_code == 200
    # Now history should contain user + assistant.
    history_resp = client.get(f"/v1/sessions/{sid}/messages")
    history = history_resp.json()["messages"]
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hi"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hello!"


def test_session_history_prepended_on_subsequent_request(client: TestClient) -> None:
    """Second request with same session_id should see first turn in transcript."""
    create = client.post("/v1/sessions", json={}).json()
    sid = create["session_id"]

    with patch("linus.server.ollama.chat", return_value=_ok_ollama_response("Hi back")) as mock_chat, patch(
        "linus.server._resolve_model", return_value="qwen3:8b"
    ):
        # Turn 1
        client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen3:8b",
                "session_id": sid,
                "messages": [{"role": "user", "content": "What's my name?"}],
            },
        )
        # Turn 2
        client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen3:8b",
                "session_id": sid,
                "messages": [{"role": "user", "content": "Same question?"}],
            },
        )

    # Inspect Ollama's transcript on the second call: it should contain the
    # turn-1 user message AND turn-1 assistant response AND turn-2 user message.
    second_call_messages = mock_chat.call_args_list[1].kwargs["messages"]
    roles_and_contents = [(m["role"], m.get("content", "")) for m in second_call_messages]

    assert ("user", "What's my name?") in roles_and_contents
    assert ("assistant", "Hi back") in roles_and_contents
    assert ("user", "Same question?") in roles_and_contents


def test_chat_completions_without_session_id_remains_stateless(client: TestClient) -> None:
    """Backward compat: no session_id means no history loaded or persisted."""
    with patch("linus.server.ollama.chat", return_value=_ok_ollama_response("ok")) as mock_chat, patch(
        "linus.server._resolve_model", return_value="qwen3:8b"
    ):
        resp = client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen3:8b",
                "messages": [{"role": "user", "content": "hi"}],
            },
        )

    assert resp.status_code == 200
    # The Ollama call should have received only the one user message we sent.
    messages = mock_chat.call_args.kwargs["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"


def test_session_auto_created_on_first_chat_use(client: TestClient) -> None:
    """If the client passes a session_id without first POSTing /v1/sessions,
    ensure_session creates it on demand."""
    sid = "auto-created-id"

    with patch("linus.server.ollama.chat", return_value=_ok_ollama_response("ok")), patch(
        "linus.server._resolve_model", return_value="qwen3:8b"
    ):
        resp = client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen3:8b",
                "session_id": sid,
                "messages": [{"role": "user", "content": "hi"}],
            },
        )
    assert resp.status_code == 200
    # Session should now exist with history.
    hist = client.get(f"/v1/sessions/{sid}/messages")
    assert hist.status_code == 200
    assert len(hist.json()["messages"]) == 2
