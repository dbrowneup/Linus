"""Server-level tool-call roundtrip with Ollama mocked.

The Ollama daemon is mocked at the ``ollama.chat`` and ``ollama.list`` boundaries
so this test runs deterministically regardless of which models are pulled
locally. The mock plays a two-turn script:

    turn 1 → model returns a ``tool_calls`` request for a synthetic tool.
    turn 2 → model returns the synthesized plain-content answer.

The server is expected to:

1. Detect the tool call.
2. Route it through the (test-local) :class:`ToolRegistry` via a monkeypatched
   ``default_registry``.
3. Append the ``role=tool`` response to the transcript and re-invoke Ollama.
4. Return the model's plain content with ``finish_reason="stop"``.

The test uses a fake registry rather than the real KB-backed registry so it
runs without requiring ``modules/KnowledgeBase/data/metadata.db`` to be built.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from linus import server
from linus.tools.registry import ToolRegistry


class FakeChatResponse(dict):
    """Mimics Ollama's dict-shaped chat response.

    Using a plain dict is sufficient because :func:`linus.server.chat_completions`
    handles both the typed-object and dict shapes. Going via dict here keeps the
    test free of dependence on private ``ollama._types.Message`` internals.
    """


@pytest.fixture
def test_registry(monkeypatch: pytest.MonkeyPatch) -> ToolRegistry:
    """Swap the server's default_registry for a fresh one containing a stub tool."""
    reg = ToolRegistry()

    def search_papers(query: str, limit: int = 3) -> list[dict]:
        """Stub: return a deterministic two-item paper list."""
        return [
            {
                "sha256": "a" * 64,
                "title": f"Paper about {query} (#1)",
                "authors": "A. Alpha; B. Beta",
                "year": 2024,
            },
            {
                "sha256": "b" * 64,
                "title": f"Paper about {query} (#2)",
                "authors": "C. Gamma",
                "year": 2023,
            },
        ][:limit]

    reg.register(search_papers, name="linus.knowledge.search_papers")

    # The server holds a module-level reference to default_registry; patch
    # that name so the chat-completions endpoint sees the test registry. The
    # `_merge_tool_specs` helper takes a registry parameter, so we patch
    # `server.default_registry` to flow through cleanly.
    monkeypatch.setattr(server, "default_registry", reg)
    return reg


@pytest.fixture
def mock_ollama(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Mock ollama.list and ollama.chat with a scripted two-turn response.

    Returns the call-recording dict so tests can assert on what the server
    actually forwarded to Ollama (model name, tools list, transcript shape).
    """
    state: dict[str, Any] = {"chat_calls": [], "list_calls": 0}

    def fake_list() -> dict[str, Any]:
        state["list_calls"] += 1
        # Pretend the fallback model is pulled. The server's _resolve_model
        # walks _MODEL_PREFERENCES and picks the first match.
        return {"models": [{"model": "qwen2.5-coder:7b"}]}

    def fake_chat(**kwargs: Any) -> FakeChatResponse:
        state["chat_calls"].append(kwargs)
        turn = len(state["chat_calls"])
        if turn == 1:
            # First turn: model demands a tool call. No content, just tool_calls.
            return FakeChatResponse(
                message={
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "linus.knowledge.search_papers",
                                "arguments": {"query": "memory architecture", "limit": 2},
                            }
                        }
                    ],
                },
                done=True,
                done_reason="stop",
                prompt_eval_count=42,
                eval_count=7,
            )
        # Second turn: model has the tool result and synthesizes an answer.
        return FakeChatResponse(
            message={
                "role": "assistant",
                "content": (
                    "Two papers discuss memory architecture: "
                    "\"Paper about memory architecture (#1)\" (2024) and "
                    "\"Paper about memory architecture (#2)\" (2023)."
                ),
            },
            done=True,
            done_reason="stop",
            prompt_eval_count=100,
            eval_count=24,
        )

    monkeypatch.setattr("ollama.list", fake_list)
    monkeypatch.setattr("ollama.chat", fake_chat)
    return state


@pytest.fixture
def client() -> TestClient:
    return TestClient(server.app)


# ---------------------------------------------------------------------------
# test_server_tool_call_roundtrip
# ---------------------------------------------------------------------------


def test_server_tool_call_roundtrip(
    client: TestClient,
    test_registry: ToolRegistry,
    mock_ollama: dict[str, Any],
) -> None:
    """End-to-end: a model that emits tool_calls drives a tool execution and
    receives the synthesized follow-up answer in a single HTTP request."""
    payload = {
        "model": "qwen3:8b",  # will fall back to qwen2.5-coder:7b per mocked list
        "messages": [
            {"role": "user", "content": "What papers discuss memory architecture?"},
        ],
    }
    resp = client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # Outer shape.
    assert body["object"] == "chat.completion"
    assert body["id"].startswith("chatcmpl-")
    assert body["model"] == "qwen2.5-coder:7b"
    assert len(body["choices"]) == 1
    choice = body["choices"][0]
    assert choice["index"] == 0
    assert choice["finish_reason"] == "stop"

    # The final assistant message is the plain-content turn 2 answer; no
    # lingering tool_calls leak out at the boundary.
    message = choice["message"]
    assert message["role"] == "assistant"
    assert "memory architecture" in message["content"].lower()
    assert message.get("tool_calls") in (None, [])

    # Usage accumulates across both Ollama calls.
    assert body["usage"]["prompt_tokens"] == 42 + 100
    assert body["usage"]["completion_tokens"] == 7 + 24
    assert body["usage"]["total_tokens"] == body["usage"]["prompt_tokens"] + body["usage"]["completion_tokens"]

    # Two ollama.chat calls happened in the right order with the right shape.
    assert len(mock_ollama["chat_calls"]) == 2

    first_call = mock_ollama["chat_calls"][0]
    # Tools advertisement carried the test-registry tool.
    advertised_names = [t["function"]["name"] for t in first_call["tools"]]
    assert "linus.knowledge.search_papers" in advertised_names
    # First-turn transcript had the user prompt only.
    first_messages = first_call["messages"]
    assert len(first_messages) == 1
    assert first_messages[0]["role"] == "user"

    second_call = mock_ollama["chat_calls"][1]
    second_messages = second_call["messages"]
    # Second-turn transcript: user + assistant(tool_calls) + tool(response).
    assert [m["role"] for m in second_messages] == ["user", "assistant", "tool"]
    tool_msg = second_messages[2]
    assert tool_msg["name"] == "linus.knowledge.search_papers"
    assert "memory architecture" in tool_msg["content"]
    # The tool content must be the JSON-serialized list returned by the stub.
    assert tool_msg["content"].startswith("[")
    assert tool_msg["content"].endswith("]")


def test_server_routes_unknown_tool_call_as_error_to_model(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the model emits a tool_call for an unregistered tool, the server
    surfaces a structured error to the model (as the role=tool content)
    rather than 500-ing the request."""
    empty_registry = ToolRegistry()
    monkeypatch.setattr(server, "default_registry", empty_registry)

    state = {"chat_calls": 0}

    def fake_list() -> dict[str, Any]:
        return {"models": [{"model": "qwen2.5-coder:7b"}]}

    def fake_chat(**kwargs: Any) -> FakeChatResponse:
        state["chat_calls"] += 1
        if state["chat_calls"] == 1:
            return FakeChatResponse(
                message={
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {"function": {"name": "ghost.tool", "arguments": {}}}
                    ],
                },
                done=True,
                done_reason="stop",
            )
        # Inspect what the server sent us as the role=tool message.
        tool_message = next(
            (m for m in kwargs["messages"] if m["role"] == "tool"),
            None,
        )
        # Echo it back so the test can assert on the content.
        return FakeChatResponse(
            message={
                "role": "assistant",
                "content": f"OK, tool error was: {tool_message['content']}",
            },
            done=True,
            done_reason="stop",
        )

    monkeypatch.setattr("ollama.list", fake_list)
    monkeypatch.setattr("ollama.chat", fake_chat)

    resp = client.post(
        "/v1/chat/completions",
        json={
            "model": "qwen3:8b",
            "messages": [{"role": "user", "content": "Call the ghost."}],
        },
    )
    assert resp.status_code == 200, resp.text
    content = resp.json()["choices"][0]["message"]["content"]
    assert "ghost.tool" in content
    assert "not registered" in content.lower()


def test_server_request_supplied_tools_are_merged(
    client: TestClient,
    test_registry: ToolRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tools sent in the request body should be merged with the server registry
    in the advertisement Ollama receives, server-side names winning on
    collision."""
    state: dict[str, Any] = {"tools_seen": None}

    def fake_list() -> dict[str, Any]:
        return {"models": [{"model": "qwen2.5-coder:7b"}]}

    def fake_chat(**kwargs: Any) -> FakeChatResponse:
        state["tools_seen"] = kwargs.get("tools")
        return FakeChatResponse(
            message={"role": "assistant", "content": "ack"},
            done=True,
            done_reason="stop",
        )

    monkeypatch.setattr("ollama.list", fake_list)
    monkeypatch.setattr("ollama.chat", fake_chat)

    payload = {
        "model": "qwen3:8b",
        "messages": [{"role": "user", "content": "hi"}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "client.only.tool",
                    "description": "Client-only addition.",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ],
    }
    resp = client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 200, resp.text

    names = [t["function"]["name"] for t in state["tools_seen"]]
    # Both the server-registered KB stub and the client-supplied tool appear.
    assert "linus.knowledge.search_papers" in names
    assert "client.only.tool" in names
