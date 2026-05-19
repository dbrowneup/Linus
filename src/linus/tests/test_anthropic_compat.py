"""Tests for the Anthropic-compatible ``/v1/messages`` endpoint.

Validates the contract per DEC-0056: the endpoint speaks the Anthropic
Messages API shape so the official ``anthropic`` Python SDK can target
Linus via ``base_url=http://localhost:8000``.

Ollama is patched throughout; the suite is hermetic — no local Ollama
required to run.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from linus.server import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _ok_ollama_response(text: str = "Hello back!", prompt_tokens: int = 10, completion_tokens: int = 5) -> dict:
    """Build an Ollama-shaped chat response dict matching ``ollama.chat`` 0.x."""
    return {
        "message": {"role": "assistant", "content": text},
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": prompt_tokens,
        "eval_count": completion_tokens,
    }


@pytest.fixture()
def patched_chat():
    """Patch ``ollama.chat`` and ``_resolve_model`` for hermetic tests."""
    with patch("linus.server.ollama.chat", return_value=_ok_ollama_response()) as mock_chat, patch(
        "linus.server._resolve_model", return_value="qwen3:8b"
    ) as mock_resolve:
        yield mock_chat, mock_resolve


# ── Happy path ────────────────────────────────────────────────────────────


def test_messages_happy_path(client: TestClient, patched_chat) -> None:
    """Basic Anthropic-shaped request returns Anthropic-shaped response."""
    resp = client.post(
        "/v1/messages",
        json={
            "model": "claude-3-5-sonnet",
            "max_tokens": 100,
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["type"] == "message"
    assert body["role"] == "assistant"
    assert body["id"].startswith("msg_")
    assert body["model"] == "qwen3:8b"
    assert body["stop_reason"] == "end_turn"
    assert body["stop_sequence"] is None

    # content is a list of typed text blocks (Anthropic shape).
    assert isinstance(body["content"], list)
    assert len(body["content"]) == 1
    assert body["content"][0]["type"] == "text"
    assert body["content"][0]["text"] == "Hello back!"

    assert body["usage"]["input_tokens"] == 10
    assert body["usage"]["output_tokens"] == 5


def test_messages_with_system_prompt(client: TestClient, patched_chat) -> None:
    """The ``system`` top-level field should be prepended as a role=system message."""
    mock_chat, _ = patched_chat
    resp = client.post(
        "/v1/messages",
        json={
            "model": "claude-3-5-sonnet",
            "max_tokens": 100,
            "system": "You are a helpful assistant.",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    assert resp.status_code == 200, resp.text

    # Verify the system prompt landed in the Ollama messages list.
    call_kwargs = mock_chat.call_args.kwargs
    ollama_messages = call_kwargs["messages"]
    assert ollama_messages[0]["role"] == "system"
    assert ollama_messages[0]["content"] == "You are a helpful assistant."
    assert ollama_messages[1]["role"] == "user"


def test_messages_multi_turn(client: TestClient, patched_chat) -> None:
    """Multiple turns in the input messages are forwarded verbatim."""
    mock_chat, _ = patched_chat
    resp = client.post(
        "/v1/messages",
        json={
            "model": "claude-3-5-sonnet",
            "max_tokens": 100,
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
                {"role": "user", "content": "How are you?"},
            ],
        },
    )
    assert resp.status_code == 200, resp.text

    ollama_messages = mock_chat.call_args.kwargs["messages"]
    # Expect all three forwarded (no system in this request).
    assert len(ollama_messages) == 3
    assert ollama_messages[0]["role"] == "user"
    assert ollama_messages[1]["role"] == "assistant"
    assert ollama_messages[2]["role"] == "user"


def test_messages_content_block_list(client: TestClient, patched_chat) -> None:
    """Anthropic's multi-block content shape (list of text blocks) is flattened."""
    mock_chat, _ = patched_chat
    resp = client.post(
        "/v1/messages",
        json={
            "model": "claude-3-5-sonnet",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "First part."},
                        {"type": "text", "text": "Second part."},
                    ],
                }
            ],
        },
    )
    assert resp.status_code == 200, resp.text
    ollama_messages = mock_chat.call_args.kwargs["messages"]
    assert "First part." in ollama_messages[0]["content"]
    assert "Second part." in ollama_messages[0]["content"]


def test_messages_non_text_blocks_dropped(client: TestClient, patched_chat) -> None:
    """v1 silently drops non-text blocks (image, tool_use, etc.) — feature deferred."""
    mock_chat, _ = patched_chat
    resp = client.post(
        "/v1/messages",
        json={
            "model": "claude-3-5-sonnet",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image."},
                        {"type": "image", "source": {"type": "base64", "data": "...", "media_type": "image/png"}},
                    ],
                }
            ],
        },
    )
    assert resp.status_code == 200, resp.text
    ollama_messages = mock_chat.call_args.kwargs["messages"]
    assert ollama_messages[0]["content"] == "Describe this image."


# ── Stop-reason mapping ───────────────────────────────────────────────────


def test_messages_max_tokens_stop_reason(client: TestClient) -> None:
    """Ollama's ``done_reason="length"`` should map to Anthropic ``"max_tokens"``."""
    response = _ok_ollama_response()
    response["done_reason"] = "length"

    with patch("linus.server.ollama.chat", return_value=response), patch(
        "linus.server._resolve_model", return_value="qwen3:8b"
    ):
        resp = client.post(
            "/v1/messages",
            json={
                "model": "claude-3-5-sonnet",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Write a long essay"}],
            },
        )
    assert resp.status_code == 200
    assert resp.json()["stop_reason"] == "max_tokens"


# ── Streaming (deferred) ──────────────────────────────────────────────────


def test_messages_streaming_returns_501(client: TestClient, patched_chat) -> None:
    """v1 returns 501 with a structured error when stream=true."""
    resp = client.post(
        "/v1/messages",
        json={
            "model": "claude-3-5-sonnet",
            "max_tokens": 100,
            "stream": True,
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    assert resp.status_code == 501
    body = resp.json()
    assert body["detail"]["error"] == "streaming_not_implemented"
    assert "stream=false" in body["detail"]["message"]


# ── Validation errors ─────────────────────────────────────────────────────


def test_messages_empty_messages_400(client: TestClient, patched_chat) -> None:
    """Empty messages list → 400."""
    resp = client.post(
        "/v1/messages",
        json={"model": "claude-3-5-sonnet", "max_tokens": 100, "messages": []},
    )
    assert resp.status_code == 400


def test_messages_only_system_400(client: TestClient, patched_chat) -> None:
    """Translation produces only role=system; reject so we don't 502 from Ollama."""
    # An empty messages list with only system is impossible per pydantic
    # (messages is required and min-len validated). The "only-system" case
    # arises if every message is a system message in input — Anthropic doesn't
    # actually allow this, but we defend against it.
    resp = client.post(
        "/v1/messages",
        json={
            "model": "claude-3-5-sonnet",
            "max_tokens": 100,
            "system": "be helpful",
            "messages": [{"role": "system", "content": "extra system"}],
        },
    )
    assert resp.status_code == 400
    assert "non-system message" in resp.json()["detail"]


def test_messages_invalid_request_unprocessable(client: TestClient, patched_chat) -> None:
    """Missing required field → 422 from Pydantic validation."""
    resp = client.post(
        "/v1/messages",
        json={
            "model": "claude-3-5-sonnet",
            # missing max_tokens, messages
        },
    )
    assert resp.status_code == 422


# ── SDK shape compatibility ───────────────────────────────────────────────


def test_messages_response_matches_anthropic_sdk_fields(client: TestClient, patched_chat) -> None:
    """The Anthropic Python SDK constructs its Message object from these exact fields."""
    resp = client.post(
        "/v1/messages",
        json={
            "model": "claude-3-5-sonnet",
            "max_tokens": 100,
            "messages": [{"role": "user", "content": "Hi"}],
        },
    )
    assert resp.status_code == 200
    body = resp.json()

    # Required fields the SDK reads off the response:
    expected_fields = {"id", "type", "role", "content", "model", "stop_reason", "stop_sequence", "usage"}
    assert expected_fields.issubset(body.keys())
    # usage shape:
    assert {"input_tokens", "output_tokens"}.issubset(body["usage"].keys())


def test_messages_sampling_fields_forwarded_to_ollama(client: TestClient) -> None:
    """temperature, top_p, max_tokens land in Ollama's options dict."""
    with patch("linus.server.ollama.chat", return_value=_ok_ollama_response()) as mock_chat, patch(
        "linus.server._resolve_model", return_value="qwen3:8b"
    ):
        client.post(
            "/v1/messages",
            json={
                "model": "claude-3-5-sonnet",
                "max_tokens": 75,
                "temperature": 0.3,
                "top_p": 0.95,
                "messages": [{"role": "user", "content": "Hi"}],
            },
        )

    options = mock_chat.call_args.kwargs["options"]
    assert options == {"temperature": 0.3, "top_p": 0.95, "num_predict": 75}


def test_messages_doesnt_advertise_tools(client: TestClient) -> None:
    """v1 of /v1/messages intentionally doesn't expose the OpenAI tool registry."""
    with patch("linus.server.ollama.chat", return_value=_ok_ollama_response()) as mock_chat, patch(
        "linus.server._resolve_model", return_value="qwen3:8b"
    ):
        client.post(
            "/v1/messages",
            json={
                "model": "claude-3-5-sonnet",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Hi"}],
            },
        )
    # tools kwarg should be None (no tool advertisement on this endpoint in v1).
    assert mock_chat.call_args.kwargs.get("tools") is None
