"""Tests for SSE streaming on ``/v1/chat/completions`` (task A.1).

Validates the OpenAI streaming contract:

- ``Content-Type: text/event-stream`` when ``stream=true``
- First chunk carries ``delta.role = "assistant"``
- Subsequent chunks carry ``delta.content`` (token-or-tokens at a time)
- Terminal chunk carries ``finish_reason`` and an empty delta
- Stream ends with ``data: [DONE]\\n\\n``
- Non-streaming path (``stream=false`` or absent) preserves JSON response

Ollama is patched throughout; the suite is hermetic.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from linus.server import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# ── helpers ───────────────────────────────────────────────────────────────


def _stream_chunks(texts: list[str], done_reason: str = "stop") -> list[dict]:
    """Build an Ollama-shaped streaming response sequence.

    Each text becomes one chunk with ``done=False``; the last chunk has
    ``done=True`` and ``done_reason``.
    """
    chunks: list[dict] = []
    for i, text in enumerate(texts):
        chunks.append(
            {
                "message": {"role": "assistant", "content": text},
                "done": i == len(texts) - 1,
                "done_reason": done_reason if i == len(texts) - 1 else None,
            }
        )
    return chunks


def _parse_sse_stream(body: str) -> list[Any]:
    """Parse an SSE stream into a list of payloads.

    Returns a list whose items are either JSON dicts or the string
    ``"[DONE]"`` for the terminator. Non-``data:`` lines are skipped.
    """
    out: list[Any] = []
    for raw_line in body.splitlines():
        if not raw_line.startswith("data: "):
            continue
        payload = raw_line[len("data: ") :]
        if payload == "[DONE]":
            out.append("[DONE]")
        else:
            out.append(json.loads(payload))
    return out


# ── streaming happy path ──────────────────────────────────────────────────


def test_streaming_returns_event_stream_content_type(client: TestClient) -> None:
    """``stream=true`` should return ``Content-Type: text/event-stream``."""
    chunks = _stream_chunks(["Hello", " world"])
    with (
        patch("linus.server.ollama.chat", return_value=iter(chunks)),
        patch("linus.server._resolve_model", return_value="qwen3:8b"),
    ):
        resp = client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen3:8b",
                "messages": [{"role": "user", "content": "hi"}],
                "stream": True,
            },
        )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")


def test_streaming_first_chunk_has_role(client: TestClient) -> None:
    """OpenAI convention: first chunk's delta carries role=assistant."""
    chunks = _stream_chunks(["hi"])
    with (
        patch("linus.server.ollama.chat", return_value=iter(chunks)),
        patch("linus.server._resolve_model", return_value="qwen3:8b"),
    ):
        resp = client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen3:8b",
                "messages": [{"role": "user", "content": "hi"}],
                "stream": True,
            },
        )

    events = _parse_sse_stream(resp.text)
    assert len(events) >= 2  # role chunk + final + [DONE]
    first = events[0]
    assert first["object"] == "chat.completion.chunk"
    assert first["choices"][0]["delta"] == {"role": "assistant"}


def test_streaming_content_chunks_concatenate_to_full_response(client: TestClient) -> None:
    """Joining all content deltas should reconstruct the model's full response."""
    parts = ["Hello", " ", "world", "!"]
    chunks = _stream_chunks(parts)
    with (
        patch("linus.server.ollama.chat", return_value=iter(chunks)),
        patch("linus.server._resolve_model", return_value="qwen3:8b"),
    ):
        resp = client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen3:8b",
                "messages": [{"role": "user", "content": "hi"}],
                "stream": True,
            },
        )

    events = _parse_sse_stream(resp.text)
    content_pieces = [
        ev["choices"][0]["delta"]["content"]
        for ev in events
        if isinstance(ev, dict) and "content" in ev["choices"][0].get("delta", {})
    ]
    assert "".join(content_pieces) == "Hello world!"


def test_streaming_terminator_chunk_has_finish_reason(client: TestClient) -> None:
    """The chunk immediately before ``[DONE]`` carries finish_reason."""
    chunks = _stream_chunks(["hi"], done_reason="stop")
    with (
        patch("linus.server.ollama.chat", return_value=iter(chunks)),
        patch("linus.server._resolve_model", return_value="qwen3:8b"),
    ):
        resp = client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen3:8b",
                "messages": [{"role": "user", "content": "hi"}],
                "stream": True,
            },
        )

    events = _parse_sse_stream(resp.text)
    assert events[-1] == "[DONE]"
    terminator_chunk = events[-2]
    assert terminator_chunk["choices"][0]["finish_reason"] == "stop"
    assert terminator_chunk["choices"][0]["delta"] == {}


def test_streaming_done_sentinel_emitted(client: TestClient) -> None:
    """The stream must end with the ``data: [DONE]`` sentinel."""
    chunks = _stream_chunks(["hi"])
    with (
        patch("linus.server.ollama.chat", return_value=iter(chunks)),
        patch("linus.server._resolve_model", return_value="qwen3:8b"),
    ):
        resp = client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen3:8b",
                "messages": [{"role": "user", "content": "hi"}],
                "stream": True,
            },
        )

    events = _parse_sse_stream(resp.text)
    assert events[-1] == "[DONE]"


def test_streaming_chunks_have_stable_completion_id(client: TestClient) -> None:
    """All chunks in a single stream share the same ``id``."""
    chunks = _stream_chunks(["a", "b", "c"])
    with (
        patch("linus.server.ollama.chat", return_value=iter(chunks)),
        patch("linus.server._resolve_model", return_value="qwen3:8b"),
    ):
        resp = client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen3:8b",
                "messages": [{"role": "user", "content": "hi"}],
                "stream": True,
            },
        )

    events = _parse_sse_stream(resp.text)
    chunk_events = [e for e in events if isinstance(e, dict)]
    ids = {e["id"] for e in chunk_events}
    assert len(ids) == 1
    assert next(iter(ids)).startswith("chatcmpl-")


# ── backward compatibility ────────────────────────────────────────────────


def test_non_streaming_path_returns_json_unchanged(client: TestClient) -> None:
    """``stream=false`` (or absent) preserves the existing JSON response shape."""
    non_streaming_response = {
        "message": {"role": "assistant", "content": "Hello back"},
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": 5,
        "eval_count": 3,
    }
    with (
        patch("linus.server.ollama.chat", return_value=non_streaming_response),
        patch("linus.server._resolve_model", return_value="qwen3:8b"),
    ):
        resp = client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen3:8b",
                "messages": [{"role": "user", "content": "hi"}],
                "stream": False,
            },
        )

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    body = resp.json()
    assert body["object"] == "chat.completion"
    assert body["choices"][0]["message"]["content"] == "Hello back"


def test_stream_field_absent_is_non_streaming(client: TestClient) -> None:
    """Omitting ``stream`` entirely uses the non-streaming path (default false)."""
    non_streaming_response = {
        "message": {"role": "assistant", "content": "ok"},
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": 1,
        "eval_count": 1,
    }
    with (
        patch("linus.server.ollama.chat", return_value=non_streaming_response),
        patch("linus.server._resolve_model", return_value="qwen3:8b"),
    ):
        resp = client.post(
            "/v1/chat/completions",
            json={"model": "qwen3:8b", "messages": [{"role": "user", "content": "hi"}]},
        )

    assert resp.headers["content-type"].startswith("application/json")
    assert resp.json()["object"] == "chat.completion"


# ── tool-call handling in streaming ───────────────────────────────────────


def test_streaming_tool_call_resolved_internally_then_continues(client: TestClient) -> None:
    """When the model emits tool_calls mid-stream, server resolves them and
    streams the post-tool assistant content normally (tool plumbing hidden)."""

    # First iteration: streaming response where the final chunk has tool_calls,
    # no visible content.
    tool_call_final_chunk = {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "linus.knowledge.search_papers",
                        "arguments": {"query": "test", "limit": 1},
                    }
                }
            ],
        },
        "done": True,
        "done_reason": "stop",
    }
    # Second iteration: post-tool streaming response with actual content.
    post_tool_chunks = _stream_chunks(["I found ", "one paper."])

    call_count = {"n": 0}

    def chat_side_effect(**kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return iter([tool_call_final_chunk])
        return iter(post_tool_chunks)

    fake_tool_result = [{"sha256": "abc", "title": "Test Paper", "year": 2024}]
    with (
        patch("linus.server.ollama.chat", side_effect=chat_side_effect),
        patch("linus.server._resolve_model", return_value="qwen3:8b"),
        patch.object(
            __import__("linus.tools", fromlist=["default_registry"]).default_registry,
            "call_tool",
            return_value=fake_tool_result,
        ),
    ):
        resp = client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen3:8b",
                "messages": [{"role": "user", "content": "find a paper"}],
                "stream": True,
            },
        )

    events = _parse_sse_stream(resp.text)
    content_pieces = [
        ev["choices"][0]["delta"]["content"]
        for ev in events
        if isinstance(ev, dict) and "content" in ev["choices"][0].get("delta", {})
    ]
    # Tool call's empty content should NOT appear as a visible delta.
    # Post-tool content should: "I found one paper."
    assert "".join(content_pieces) == "I found one paper."
    assert events[-1] == "[DONE]"


# ── error surfacing in streams ────────────────────────────────────────────


def test_streaming_ollama_failure_surfaces_as_inline_error(client: TestClient) -> None:
    """A mid-stream Ollama failure should emit a structured error event then [DONE]."""

    def boom(**kwargs):
        raise RuntimeError("simulated ollama crash")

    with (
        patch("linus.server.ollama.chat", side_effect=boom),
        patch("linus.server._resolve_model", return_value="qwen3:8b"),
    ):
        resp = client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen3:8b",
                "messages": [{"role": "user", "content": "hi"}],
                "stream": True,
            },
        )

    events = _parse_sse_stream(resp.text)
    # Should have: leading role chunk, error event, [DONE]
    error_events = [e for e in events if isinstance(e, dict) and "error" in e]
    assert len(error_events) == 1
    assert "simulated ollama crash" in error_events[0]["error"]["message"]
    assert events[-1] == "[DONE]"
