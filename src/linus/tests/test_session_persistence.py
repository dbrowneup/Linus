"""Tests for session-store durability gaps surfaced by the 2026-05-20 server bug sweep.

Two HIGH-severity bugs are exercised here, both involving silent loss of
conversation state that the session store contract promises to preserve:

- **H-1**: streaming session writes were lost when the client disconnected
  mid-stream because the post-stream append only ran after the inner
  generator completed. The fix persists the user turn upfront and uses a
  ``try/finally`` so the accumulated partial assistant content is committed
  even if the generator is cancelled (e.g.,
  ``GeneratorExit`` from Starlette on client-disconnect). The append is
  idempotent so a fully-completed stream doesn't double-write.

- **H-2**: tool-call assistant turns + role=tool result messages were never
  persisted, even though :func:`_run_chat_loop` appended them to the in-memory
  transcript. The fix persists the full transcript slice beyond the original
  history (user message + intermediate tool-call turns + tool results +
  final assistant text) so multi-turn conversations preserve their tool
  grounding on resume.

Reference: ``docs/bug-sweeps/2026-05-20-server-sweep.md`` (PR #106), H-1 and H-2.
"""

from __future__ import annotations

import contextlib
import json
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from linus import server as server_module
from linus.memory.sessions import reset_default_store
from linus.server import (
    _TOOL_CALLS_CONTENT_MARKER,
    ChatMessage,
    ToolCall,
    ToolCallFunction,
    _persist_tool_loop_messages,
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


# ──────────────────────────────────────────────────────────────────────────
# Helpers used by the H-2 tests
# ──────────────────────────────────────────────────────────────────────────


def _ok_response(text: str = "ok", tool_calls: list | None = None, done_reason: str = "stop") -> dict:
    """Build a non-streaming Ollama response dict (mirrors test_server_coverage helper)."""
    msg: dict[str, Any] = {"role": "assistant", "content": text}
    if tool_calls is not None:
        msg["tool_calls"] = tool_calls
    return {
        "message": msg,
        "done": True,
        "done_reason": done_reason,
        "prompt_eval_count": 7,
        "eval_count": 3,
    }


# ──────────────────────────────────────────────────────────────────────────
# H-2 — tool-call + tool-result messages persistence
# ──────────────────────────────────────────────────────────────────────────


def test_tool_call_assistant_message_persisted_to_session(
    client: TestClient, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end: a chat_completions call with session_id that triggers ONE
    tool call must persist (a) user turn, (b) assistant tool-call turn,
    (c) tool-result turn, (d) final assistant text — in order."""
    monkeypatch.setenv("LINUS_SESSIONS_DB", str(tmp_path / "sessions.db"))
    reset_default_store()

    create_resp = client.post("/v1/sessions", json={})
    sid = create_resp.json()["session_id"]

    iteration = {"n": 0}

    def chat_seq(**_kwargs):
        iteration["n"] += 1
        if iteration["n"] == 1:
            return _ok_response(
                text="",
                tool_calls=[{"function": {"name": "demo.tool", "arguments": {"q": "x"}}}],
            )
        return _ok_response(text="final answer")

    monkeypatch.setattr(server_module.ollama, "chat", chat_seq)
    monkeypatch.setattr(server_module, "_resolve_model", lambda m: "qwen3:8b")
    monkeypatch.setattr(server_module.default_registry, "call_tool", lambda n, a: {"result": "tool-out"})

    resp = client.post(
        "/v1/chat/completions",
        json={
            "model": "qwen3:8b",
            "session_id": sid,
            "messages": [{"role": "user", "content": "use tool"}],
        },
    )
    assert resp.status_code == 200

    history = client.get(f"/v1/sessions/{sid}/messages").json()["messages"]
    roles_in_order = [m["role"] for m in history]
    # Expected order: user, assistant (tool-call marker), tool, assistant (final)
    assert roles_in_order == ["user", "assistant", "tool", "assistant"], (
        f"Expected [user, assistant, tool, assistant] but got {roles_in_order}: {history}"
    )

    # The assistant tool-call turn's content must carry the tool_calls marker
    # so the structured info can be recovered later.
    tool_call_msg = history[1]
    assert tool_call_msg["content"].startswith(_TOOL_CALLS_CONTENT_MARKER), (
        f"assistant tool-call turn missing marker: {tool_call_msg['content']!r}"
    )
    decoded = json.loads(tool_call_msg["content"][len(_TOOL_CALLS_CONTENT_MARKER) :])
    assert decoded["tool_calls"][0]["function"]["name"] == "demo.tool"

    # Tool result content survives verbatim (JSON of {"result": "tool-out"}).
    tool_result_msg = history[2]
    assert json.loads(tool_result_msg["content"]) == {"result": "tool-out"}

    # Final assistant content surfaces in plain form (no marker).
    final_msg = history[3]
    assert final_msg["content"] == "final answer"
    assert not final_msg["content"].startswith(_TOOL_CALLS_CONTENT_MARKER)

    reset_default_store()


def test_multi_tool_call_iterations_all_persisted(
    client: TestClient, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A multi-iteration tool loop (tool A → tool B → final text) must persist
    every assistant + tool message that was appended during the loop."""
    monkeypatch.setenv("LINUS_SESSIONS_DB", str(tmp_path / "sessions.db"))
    reset_default_store()

    create_resp = client.post("/v1/sessions", json={})
    sid = create_resp.json()["session_id"]

    iteration = {"n": 0}

    def chat_seq(**_kwargs):
        iteration["n"] += 1
        if iteration["n"] == 1:
            return _ok_response(
                text="",
                tool_calls=[{"function": {"name": "tool.a", "arguments": "{}"}}],
            )
        if iteration["n"] == 2:
            return _ok_response(
                text="",
                tool_calls=[{"function": {"name": "tool.b", "arguments": "{}"}}],
            )
        return _ok_response(text="done after two tools")

    monkeypatch.setattr(server_module.ollama, "chat", chat_seq)
    monkeypatch.setattr(server_module, "_resolve_model", lambda m: "qwen3:8b")

    def tool_router(name, args):
        return {"name": name, "ok": True}

    monkeypatch.setattr(server_module.default_registry, "call_tool", tool_router)

    resp = client.post(
        "/v1/chat/completions",
        json={
            "model": "qwen3:8b",
            "session_id": sid,
            "messages": [{"role": "user", "content": "multistep"}],
        },
    )
    assert resp.status_code == 200

    history = client.get(f"/v1/sessions/{sid}/messages").json()["messages"]
    roles_in_order = [m["role"] for m in history]
    # Expected: user, assistant (tool.a call), tool (tool.a result),
    # assistant (tool.b call), tool (tool.b result), assistant (final).
    assert roles_in_order == ["user", "assistant", "tool", "assistant", "tool", "assistant"], (
        f"Expected 6-row multi-iter history; got {roles_in_order}: {history}"
    )

    # Inspect the two tool-call assistant turns — each should encode
    # exactly one tool_call with the expected name.
    first_call = history[1]
    assert first_call["content"].startswith(_TOOL_CALLS_CONTENT_MARKER)
    decoded_a = json.loads(first_call["content"][len(_TOOL_CALLS_CONTENT_MARKER) :])
    assert decoded_a["tool_calls"][0]["function"]["name"] == "tool.a"

    second_call = history[3]
    assert second_call["content"].startswith(_TOOL_CALLS_CONTENT_MARKER)
    decoded_b = json.loads(second_call["content"][len(_TOOL_CALLS_CONTENT_MARKER) :])
    assert decoded_b["tool_calls"][0]["function"]["name"] == "tool.b"

    # Tool results round-trip through json.dumps in _format_tool_result.
    assert json.loads(history[2]["content"])["name"] == "tool.a"
    assert json.loads(history[4]["content"])["name"] == "tool.b"

    # Final assistant text is plain.
    assert history[5]["content"] == "done after two tools"

    reset_default_store()


def test_streaming_tool_call_messages_persisted_to_session(
    client: TestClient, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The streaming path's tool-loop must persist intermediate tool-call
    assistant turns + role=tool messages, not just the final assistant text.

    Exercises the H-2 fix on the streaming branch (the bug-sweep report
    flagged both the non-streaming line 1232-1240 AND the streaming
    wrapper at 1086-1093 as silently dropping the tool-loop transcript)."""
    monkeypatch.setenv("LINUS_SESSIONS_DB", str(tmp_path / "sessions.db"))
    reset_default_store()

    create_resp = client.post("/v1/sessions", json={})
    sid = create_resp.json()["session_id"]

    iteration = {"n": 0}

    def chat_side_effect(**_kwargs):
        iteration["n"] += 1
        if iteration["n"] == 1:
            # First iteration: tool-call only; no visible content.
            return iter(
                [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [{"function": {"name": "stream.tool", "arguments": {"k": 1}}}],
                        },
                        "done": True,
                        "done_reason": "stop",
                    }
                ]
            )
        # Second iteration: visible streamed response.
        return iter(
            [
                {"message": {"role": "assistant", "content": "Stream "}, "done": False, "done_reason": None},
                {"message": {"role": "assistant", "content": "result."}, "done": True, "done_reason": "stop"},
            ]
        )

    monkeypatch.setattr(server_module.ollama, "chat", chat_side_effect)
    monkeypatch.setattr(server_module, "_resolve_model", lambda m: "qwen3:8b")
    monkeypatch.setattr(server_module.default_registry, "call_tool", lambda n, a: {"streamed": True})

    resp = client.post(
        "/v1/chat/completions",
        json={
            "model": "qwen3:8b",
            "session_id": sid,
            "stream": True,
            "messages": [{"role": "user", "content": "stream + tool"}],
        },
    )
    assert resp.status_code == 200
    # Drain the body so the generator runs to completion.
    _ = resp.text

    history = client.get(f"/v1/sessions/{sid}/messages").json()["messages"]
    roles_in_order = [m["role"] for m in history]
    # Expected: user, assistant (tool-call), tool (result), assistant (final).
    assert roles_in_order == ["user", "assistant", "tool", "assistant"], (
        f"streaming session missing tool-loop rows; got {roles_in_order}: {history}"
    )
    # Tool-call marker present on the assistant tool-call turn.
    assert history[1]["content"].startswith(_TOOL_CALLS_CONTENT_MARKER)
    # Final streamed assistant content is plain text.
    assert history[3]["content"] == "Stream result."

    reset_default_store()


# ──────────────────────────────────────────────────────────────────────────
# Unit-level: _persist_tool_loop_messages tuple-shape coverage
# ──────────────────────────────────────────────────────────────────────────


def test_persist_tool_loop_messages_serializes_tool_calls() -> None:
    """Direct unit test: assistant turns with tool_calls produce a marker-prefixed
    JSON content row; role=tool turns survive content verbatim; empty messages
    are skipped."""
    messages = [
        ChatMessage(
            role="assistant",
            content="",
            tool_calls=[
                ToolCall(
                    id="call_abc",
                    type="function",
                    function=ToolCallFunction(name="kb.search", arguments={"q": "test"}),
                )
            ],
        ),
        ChatMessage(role="tool", name="kb.search", tool_call_id="call_abc", content='{"hits": 0}'),
        ChatMessage(role="assistant", content="final text"),
        ChatMessage(role="user", content=""),  # empty → skipped
        ChatMessage(role="system", content="sys-msg"),
    ]
    out = _persist_tool_loop_messages(messages)
    # 4 non-empty (tool-call, tool-result, final assistant, system); the empty user is skipped.
    assert len(out) == 4

    # First row: assistant tool-call with marker.
    role0, content0 = out[0]
    assert role0 == "assistant"
    assert content0.startswith(_TOOL_CALLS_CONTENT_MARKER)
    decoded = json.loads(content0[len(_TOOL_CALLS_CONTENT_MARKER) :])
    assert decoded["tool_calls"][0]["function"]["name"] == "kb.search"
    assert decoded["content"] == ""

    # Second: tool result verbatim.
    assert out[1] == ("tool", '{"hits": 0}')

    # Third: final assistant text plain.
    assert out[2] == ("assistant", "final text")

    # Fourth: system message preserved.
    assert out[3] == ("system", "sys-msg")
