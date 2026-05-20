"""Hermetic coverage backfill for ``src/linus/server.py``.

Targets the uncovered branches not already exercised by
``test_anthropic_compat.py``, ``test_streaming.py``, ``test_sessions.py``,
and ``test_healthz.py``:

- Helper-function direct coverage:
  ``_list_local_models`` (dict/object shape normalization),
  ``_resolve_model`` (locally-pulled vs preference fallback vs 503),
  ``_build_options`` (all sampling fields populated),
  ``_merge_tool_specs`` (request-supplied tools, registry precedence),
  ``_extract_tool_calls`` (dict-shape, object-shape, ``None``, empty,
  missing-name skip),
  ``_format_tool_result`` (None / str / dict / non-JSON-serializable),
  ``_message_to_ollama`` (empty-content branch, tool_calls
  serialization, tool_call_id, name),
  ``_anthropic_input_to_transcript`` (dict-block branch, mixed content),
  ``_ollama_finish_to_anthropic_stop_reason`` (all branches).

- Tool-call loop error paths:
  Ollama ``ResponseError`` → 502,
  unknown tool name → "not registered" error to model,
  ``ToolError`` from registry → structured error to model,
  max-iteration cap → ``finish_reason="length"``/``"tool_calls"``,
  object-shape Ollama response.

- Streaming generator edge cases:
  object-shape chunks, max-iteration cap → ``"tool_calls"``,
  empty content fallthrough, session-wrapped streaming append,
  malformed mid-stream payload (JSON decode error swallowed).

- Endpoint edge cases:
  ``GET /`` root tour,
  ``POST /v1/chat/completions`` empty messages → 400,
  session-wrapped streaming → session messages persisted.

- Entrypoint smoke:
  ``main()`` calls ``uvicorn.run`` with env-driven host/port (patched).
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock

import ollama
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from linus import server as server_module
from linus.memory.sessions import reset_default_store
from linus.server import (
    AnthropicInputMessage,
    AnthropicMessageRequest,
    AnthropicTextBlock,
    ChatCompletionRequest,
    ChatMessage,
    ToolCall,
    ToolCallFunction,
    ToolDefinition,
    ToolFunctionSpec,
    _anthropic_input_to_transcript,
    _build_options,
    _extract_tool_calls,
    _format_tool_result,
    _list_local_models,
    _merge_tool_specs,
    _message_to_ollama,
    _ollama_finish_to_anthropic_stop_reason,
    _resolve_model,
    _run_chat_loop,
    _stored_to_chat_message,
    _stream_chat_completion,
    _stream_with_session_append,
    app,
)
from linus.tools import default_registry
from linus.tools.registry import ToolError

# ──────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# ──────────────────────────────────────────────────────────────────────────
# _list_local_models — both dict-shape and object-shape responses
# ──────────────────────────────────────────────────────────────────────────


def test_list_local_models_dict_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    """Older ollama clients return ``{"models": [{"model": "..."}]}``."""

    def fake_list():
        return {"models": [{"model": "qwen3:8b"}, {"model": "qwen2.5:14b"}]}

    monkeypatch.setattr(server_module.ollama, "list", fake_list)
    names = _list_local_models()
    assert names == ["qwen3:8b", "qwen2.5:14b"]


def test_list_local_models_dict_shape_falls_back_to_name_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """The dict-shape branch must accept ``name`` as a key fallback for ``model``."""

    def fake_list():
        return {"models": [{"name": "alt-model:1"}, {"model": "explicit:2"}]}

    monkeypatch.setattr(server_module.ollama, "list", fake_list)
    assert _list_local_models() == ["alt-model:1", "explicit:2"]


def test_list_local_models_object_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    """Newer ollama clients return typed objects with a ``models`` attr."""

    class FakeEntry:
        def __init__(self, model: str) -> None:
            self.model = model

    class FakeResp:
        def __init__(self) -> None:
            self.models = [FakeEntry("qwen3:8b"), FakeEntry("qwen2.5:14b")]

    monkeypatch.setattr(server_module.ollama, "list", lambda: FakeResp())
    assert _list_local_models() == ["qwen3:8b", "qwen2.5:14b"]


def test_list_local_models_object_shape_name_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Object-shape branch falls back to ``.name`` when ``.model`` is absent."""

    class FakeNameOnly:
        def __init__(self, name: str) -> None:
            self.name = name

        # Define model attribute as None so getattr returns None
        model = None

    class FakeResp:
        def __init__(self) -> None:
            self.models = [FakeNameOnly("only-name-attr")]

    monkeypatch.setattr(server_module.ollama, "list", lambda: FakeResp())
    assert _list_local_models() == ["only-name-attr"]


def test_list_local_models_skips_entries_without_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """Entries without a name (neither ``model`` nor ``name``) are skipped silently."""

    def fake_list():
        return {"models": [{"model": "good"}, {"junk": "no-name"}]}

    monkeypatch.setattr(server_module.ollama, "list", fake_list)
    assert _list_local_models() == ["good"]


# ──────────────────────────────────────────────────────────────────────────
# _resolve_model — happy path + fallback + 503
# ──────────────────────────────────────────────────────────────────────────


def test_resolve_model_returns_requested_when_locally_available(monkeypatch: pytest.MonkeyPatch) -> None:
    """If the requested model is locally pulled, it's returned verbatim."""
    monkeypatch.setattr(server_module, "_list_local_models", lambda: ["qwen3:8b", "other:1"])
    assert _resolve_model("qwen3:8b") == "qwen3:8b"


def test_resolve_model_falls_back_to_preference(monkeypatch: pytest.MonkeyPatch) -> None:
    """When the requested model is missing, fall back to first preference present."""
    # Only qwen2.5-coder:7b is available — the last preference.
    monkeypatch.setattr(server_module, "_list_local_models", lambda: ["qwen2.5-coder:7b"])
    resolved = _resolve_model("never-pulled-model:nope")
    assert resolved == "qwen2.5-coder:7b"


def test_resolve_model_raises_503_when_no_preference_available(monkeypatch: pytest.MonkeyPatch) -> None:
    """No preference present → HTTP 503 with structured detail."""
    monkeypatch.setattr(server_module, "_list_local_models", lambda: ["random:1", "junk:2"])
    with pytest.raises(HTTPException) as excinfo:
        _resolve_model("anything")
    assert excinfo.value.status_code == 503
    detail = excinfo.value.detail
    assert isinstance(detail, dict)
    assert "available_models" in detail
    assert detail["available_models"] == ["random:1", "junk:2"]
    assert "hint" in detail


# ──────────────────────────────────────────────────────────────────────────
# _build_options — all three sampling fields covered
# ──────────────────────────────────────────────────────────────────────────


def test_build_options_includes_all_three_fields() -> None:
    req = ChatCompletionRequest(
        model="qwen3:8b",
        messages=[ChatMessage(role="user", content="hi")],
        temperature=0.7,
        top_p=0.9,
        max_tokens=128,
    )
    opts = _build_options(req)
    assert opts == {"temperature": 0.7, "top_p": 0.9, "num_predict": 128}


def test_build_options_empty_when_no_sampling_fields() -> None:
    req = ChatCompletionRequest(
        model="qwen3:8b",
        messages=[ChatMessage(role="user", content="hi")],
    )
    assert _build_options(req) == {}


# ──────────────────────────────────────────────────────────────────────────
# _merge_tool_specs — request-tools + registry precedence
# ──────────────────────────────────────────────────────────────────────────


def test_merge_tool_specs_includes_request_supplied_tools() -> None:
    """Request-supplied tools that don't collide with the registry are forwarded."""
    request_tool = ToolDefinition(
        type="function",
        function=ToolFunctionSpec(
            name="zzz_client_only_tool",
            description="A tool only the client knows about",
            parameters={"type": "object", "properties": {}},
        ),
    )
    specs = _merge_tool_specs(default_registry, [request_tool])
    names = [s["function"]["name"] for s in specs]
    # Both registry tools AND client tool present.
    assert "zzz_client_only_tool" in names
    # Registry tools also present (we keep the default_registry populated).
    registry_names = default_registry.names()
    for n in registry_names:
        assert n in names


def test_merge_tool_specs_registry_wins_on_collision() -> None:
    """When a client tool shares a name with the registry, registry's spec wins."""
    if not default_registry.names():
        pytest.skip("No registered tools to collide with")
    collision_name = default_registry.names()[0]
    fake = ToolDefinition(
        type="function",
        function=ToolFunctionSpec(
            name=collision_name,
            description="CLIENT-OVERRIDE-DESCRIPTION",
            parameters={"type": "object", "properties": {}},
        ),
    )
    specs = _merge_tool_specs(default_registry, [fake])
    spec = next(s for s in specs if s["function"]["name"] == collision_name)
    # Description must come from the registry, not the client's spec.
    assert spec["function"].get("description") != "CLIENT-OVERRIDE-DESCRIPTION"


def test_merge_tool_specs_sorted_by_name() -> None:
    """Output is name-sorted (deterministic ordering for prompt stability)."""
    specs = _merge_tool_specs(default_registry, None)
    names = [s["function"]["name"] for s in specs]
    assert names == sorted(names)


def test_merge_tool_specs_with_no_request_tools_and_empty_registry() -> None:
    """Empty registry + no request tools → empty list."""
    from linus.tools.registry import ToolRegistry

    empty = ToolRegistry()
    assert _merge_tool_specs(empty, None) == []


# ──────────────────────────────────────────────────────────────────────────
# _extract_tool_calls — every shape branch
# ──────────────────────────────────────────────────────────────────────────


def test_extract_tool_calls_returns_empty_when_message_obj_is_none() -> None:
    assert _extract_tool_calls(None) == []


def test_extract_tool_calls_returns_empty_when_no_tool_calls_field() -> None:
    """Dict message with no tool_calls / empty tool_calls returns []."""
    assert _extract_tool_calls({"content": "hi"}) == []
    assert _extract_tool_calls({"content": "hi", "tool_calls": []}) == []


def test_extract_tool_calls_dict_shape() -> None:
    msg = {
        "tool_calls": [
            {
                "id": "call-explicit-id",
                "function": {"name": "do_thing", "arguments": {"k": "v"}},
            },
            {
                # No id → must be auto-generated.
                "function": {"name": "other_thing", "arguments": ""},
            },
        ]
    }
    calls = _extract_tool_calls(msg)
    assert len(calls) == 2
    assert calls[0].id == "call-explicit-id"
    assert calls[0].function.name == "do_thing"
    assert calls[1].id.startswith("call_")
    assert calls[1].function.name == "other_thing"


def test_extract_tool_calls_object_shape() -> None:
    """Object-shape: entries have ``.function.name`` / ``.function.arguments`` / ``.id``."""

    class FakeFunc:
        def __init__(self, name: str, arguments: Any) -> None:
            self.name = name
            self.arguments = arguments

    class FakeCall:
        def __init__(self, name: str, arguments: Any, call_id: str | None = None) -> None:
            self.function = FakeFunc(name, arguments)
            self.id = call_id

    class FakeMsg:
        def __init__(self, calls: list) -> None:
            self.tool_calls = calls

    msg = FakeMsg([FakeCall("obj_tool", {"a": 1}, "obj-id-1"), FakeCall("obj_tool2", {})])
    calls = _extract_tool_calls(msg)
    assert len(calls) == 2
    assert calls[0].id == "obj-id-1"
    assert calls[0].function.name == "obj_tool"
    assert calls[1].function.name == "obj_tool2"
    assert calls[1].id.startswith("call_")


def test_extract_tool_calls_skips_entries_without_name() -> None:
    """An entry whose function has no name is silently dropped."""
    msg = {
        "tool_calls": [
            {"function": {"name": "", "arguments": {}}},  # empty name
            {"function": {"arguments": {}}},  # missing name key
            {"function": {"name": "real", "arguments": {}}},
        ]
    }
    calls = _extract_tool_calls(msg)
    assert len(calls) == 1
    assert calls[0].function.name == "real"


def test_extract_tool_calls_handles_missing_function_in_object_shape() -> None:
    """Object-shape entry with no ``.function`` attribute is skipped."""

    class NoFunction:
        function = None
        id = None

    class FakeMsg:
        def __init__(self) -> None:
            self.tool_calls = [NoFunction()]

    assert _extract_tool_calls(FakeMsg()) == []


# ──────────────────────────────────────────────────────────────────────────
# _format_tool_result — every type branch
# ──────────────────────────────────────────────────────────────────────────


def test_format_tool_result_none() -> None:
    assert _format_tool_result(None) == "null"


def test_format_tool_result_string_passthrough() -> None:
    assert _format_tool_result("hello") == "hello"


def test_format_tool_result_dict_serializes_to_json() -> None:
    out = _format_tool_result({"a": 1, "b": [2, 3]})
    assert json.loads(out) == {"a": 1, "b": [2, 3]}


def test_format_tool_result_uses_default_str_for_unknown_types() -> None:
    """``default=str`` lets ``json.dumps`` accept non-serializable values."""
    from pathlib import Path

    out = _format_tool_result({"path": Path("/tmp/x")})
    decoded = json.loads(out)
    assert decoded == {"path": "/tmp/x"}


def test_format_tool_result_falls_back_to_str_on_typeerror() -> None:
    """Objects that defeat ``json.dumps`` even with ``default=str`` fall back to ``str(obj)``."""

    class Weird:
        def __str__(self) -> str:
            return "weird-obj-str"

    class Container:
        # Make json.dumps choke regardless of default=str by raising
        # inside the default callback path is hard. Instead, give
        # json.dumps something that ``default=str`` cannot serialize
        # because it raises during ``str()``.
        def __init__(self, inner: object) -> None:
            self.inner = inner

    # Trigger by passing the bare object (default=str converts it).
    # To genuinely hit the except branch, force json.dumps to raise.
    # Patch json.dumps inside the module to simulate.
    import linus.server as srv

    real_dumps = srv.json.dumps

    def _angry_dumps(obj, **kw):
        raise TypeError("synthetic")

    srv.json.dumps = _angry_dumps  # type: ignore[assignment]
    try:
        out = _format_tool_result(Weird())
    finally:
        srv.json.dumps = real_dumps  # type: ignore[assignment]
    assert out == "weird-obj-str"


# ──────────────────────────────────────────────────────────────────────────
# _message_to_ollama — content branches + tool_calls serialization
# ──────────────────────────────────────────────────────────────────────────


def test_message_to_ollama_emits_empty_content_for_system_role() -> None:
    """Non-assistant messages with content=None get an empty string body."""
    msg = ChatMessage(role="system", content=None)
    out = _message_to_ollama(msg)
    assert out == {"role": "system", "content": ""}


def test_message_to_ollama_emits_empty_content_for_user_role() -> None:
    msg = ChatMessage(role="user", content=None)
    out = _message_to_ollama(msg)
    assert out["content"] == ""


def test_message_to_ollama_emits_empty_content_for_tool_role() -> None:
    msg = ChatMessage(role="tool", content=None, tool_call_id="call_xyz")
    out = _message_to_ollama(msg)
    assert out["content"] == ""
    assert out["tool_call_id"] == "call_xyz"


def test_message_to_ollama_omits_content_for_assistant_tool_call_turn() -> None:
    """Assistant turns with content=None and tool_calls present omit content entirely."""
    msg = ChatMessage(
        role="assistant",
        content=None,
        tool_calls=[ToolCall(id="c1", function=ToolCallFunction(name="t", arguments="{}"))],
    )
    out = _message_to_ollama(msg)
    # content is NOT present (the empty-content branch only fires for system/user/tool).
    assert "content" not in out
    assert "tool_calls" in out
    assert out["tool_calls"][0]["function"]["name"] == "t"


def test_message_to_ollama_includes_name_field() -> None:
    msg = ChatMessage(role="tool", content="result", name="search_papers", tool_call_id="c1")
    out = _message_to_ollama(msg)
    assert out["name"] == "search_papers"
    assert out["tool_call_id"] == "c1"


def test_message_to_ollama_serializes_tool_calls() -> None:
    msg = ChatMessage(
        role="assistant",
        content="thinking...",
        tool_calls=[
            ToolCall(id="cA", function=ToolCallFunction(name="alpha", arguments={"a": 1})),
            ToolCall(id="cB", function=ToolCallFunction(name="beta", arguments="raw-str")),
        ],
    )
    out = _message_to_ollama(msg)
    assert out["content"] == "thinking..."
    assert len(out["tool_calls"]) == 2
    assert out["tool_calls"][0] == {
        "id": "cA",
        "type": "function",
        "function": {"name": "alpha", "arguments": {"a": 1}},
    }
    assert out["tool_calls"][1]["function"]["arguments"] == "raw-str"


# ──────────────────────────────────────────────────────────────────────────
# _stored_to_chat_message smoke
# ──────────────────────────────────────────────────────────────────────────


def test_stored_to_chat_message_roundtrip() -> None:
    from linus.memory.sessions import StoredMessage

    stored = StoredMessage(session_id="sid", idx=0, role="user", content="hello", created_at=42)
    msg = _stored_to_chat_message(stored)
    assert msg.role == "user"
    assert msg.content == "hello"


# ──────────────────────────────────────────────────────────────────────────
# _anthropic_input_to_transcript — dict-block path
# ──────────────────────────────────────────────────────────────────────────


def test_anthropic_input_to_transcript_dict_block_branch() -> None:
    """A raw ``{"type": "text", ...}`` dict that bypasses pydantic coercion is accepted.

    Pydantic typically upcasts ``{"type": "text", "text": ...}`` to AnthropicTextBlock
    during request validation, so the dict-block branch in
    ``_anthropic_input_to_transcript`` is only reachable when a raw dict slips through
    (e.g. construct the input message via ``model_construct`` to skip validation).
    Construct one synthetically here so the branch is exercised.
    """
    # Bypass pydantic validation so the dict stays as a dict, not an AnthropicTextBlock.
    raw_message = AnthropicInputMessage.model_construct(
        role="user",
        content=[
            {"type": "text", "text": "Part A."},
            {"type": "text", "text": "Part B."},
        ],
    )
    req = AnthropicMessageRequest.model_construct(
        model="claude",
        max_tokens=100,
        messages=[raw_message],
        stream=False,
        system=None,
    )
    transcript = _anthropic_input_to_transcript(req)
    assert transcript[0].role == "user"
    assert "Part A." in transcript[0].content
    assert "Part B." in transcript[0].content


def test_anthropic_input_to_transcript_mixed_typed_and_dict_blocks() -> None:
    """Mixing AnthropicTextBlock objects with raw dicts must still flatten."""
    req = AnthropicMessageRequest(
        model="claude",
        max_tokens=100,
        messages=[
            AnthropicInputMessage(
                role="user",
                content=[
                    AnthropicTextBlock(type="text", text="typed-block"),
                    {"type": "text", "text": "dict-block"},
                    {"type": "image", "source": "ignored"},  # non-text dropped
                ],
            )
        ],
    )
    transcript = _anthropic_input_to_transcript(req)
    assert "typed-block" in transcript[0].content
    assert "dict-block" in transcript[0].content
    assert "ignored" not in transcript[0].content


def test_anthropic_input_to_transcript_string_content() -> None:
    """The string-content branch sets ``text = content`` directly."""
    req = AnthropicMessageRequest(
        model="claude",
        max_tokens=100,
        messages=[AnthropicInputMessage(role="user", content="plain string")],
    )
    transcript = _anthropic_input_to_transcript(req)
    assert transcript[0].content == "plain string"


def test_anthropic_input_to_transcript_system_prepended() -> None:
    req = AnthropicMessageRequest(
        model="claude",
        max_tokens=100,
        system="be terse",
        messages=[AnthropicInputMessage(role="user", content="hi")],
    )
    transcript = _anthropic_input_to_transcript(req)
    assert transcript[0].role == "system"
    assert transcript[0].content == "be terse"
    assert transcript[1].role == "user"


# ──────────────────────────────────────────────────────────────────────────
# _ollama_finish_to_anthropic_stop_reason — every branch
# ──────────────────────────────────────────────────────────────────────────


def test_ollama_finish_to_anthropic_stop_reason_none_is_end_turn() -> None:
    assert _ollama_finish_to_anthropic_stop_reason(None) == "end_turn"


def test_ollama_finish_to_anthropic_stop_reason_stop_is_end_turn() -> None:
    assert _ollama_finish_to_anthropic_stop_reason("stop") == "end_turn"


def test_ollama_finish_to_anthropic_stop_reason_length_is_max_tokens() -> None:
    assert _ollama_finish_to_anthropic_stop_reason("length") == "max_tokens"


def test_ollama_finish_to_anthropic_stop_reason_unknown_is_end_turn() -> None:
    """Anything else maps to ``end_turn`` defensively."""
    assert _ollama_finish_to_anthropic_stop_reason("weird") == "end_turn"


# ──────────────────────────────────────────────────────────────────────────
# _run_chat_loop — error paths
# ──────────────────────────────────────────────────────────────────────────


def _ok_response(text: str = "ok", tool_calls: list | None = None, done_reason: str = "stop") -> dict:
    msg: dict = {"role": "assistant", "content": text}
    if tool_calls is not None:
        msg["tool_calls"] = tool_calls
    return {
        "message": msg,
        "done": True,
        "done_reason": done_reason,
        "prompt_eval_count": 7,
        "eval_count": 3,
    }


def test_run_chat_loop_ollama_response_error_becomes_502(monkeypatch: pytest.MonkeyPatch) -> None:
    """An ``ollama.ResponseError`` is converted to HTTP 502."""

    def boom(**_kwargs):
        raise ollama.ResponseError("model not found")

    monkeypatch.setattr(server_module.ollama, "chat", boom)
    transcript = [ChatMessage(role="user", content="hi")]
    with pytest.raises(HTTPException) as excinfo:
        _run_chat_loop(transcript, "qwen3:8b", {}, [])
    assert excinfo.value.status_code == 502
    assert "Ollama returned an error" in str(excinfo.value.detail)


def test_run_chat_loop_handles_object_shape_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ollama may return a typed object instead of a dict; the loop must handle both."""

    class FakeMsg:
        content = "from-object"
        tool_calls = None

    class FakeResult:
        def __init__(self) -> None:
            self.message = FakeMsg()
            self.done = True
            self.done_reason = "stop"
            self.prompt_eval_count = 4
            self.eval_count = 2

    monkeypatch.setattr(server_module.ollama, "chat", lambda **_kw: FakeResult())
    transcript = [ChatMessage(role="user", content="hi")]
    final, finish_reason, pt, ct = _run_chat_loop(transcript, "qwen3:8b", {}, [])
    assert final.content == "from-object"
    assert finish_reason == "stop"
    assert pt == 4
    assert ct == 2


def test_run_chat_loop_unknown_tool_surfaces_error_to_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """When the model calls a non-registered tool, the loop responds with an error payload."""
    iteration = {"n": 0}

    def chat_seq(**_kwargs):
        iteration["n"] += 1
        if iteration["n"] == 1:
            return _ok_response(
                text="",
                tool_calls=[{"function": {"name": "nonexistent.tool", "arguments": "{}"}}],
            )
        return _ok_response(text="acknowledged")

    monkeypatch.setattr(server_module.ollama, "chat", chat_seq)
    transcript = [ChatMessage(role="user", content="please call it")]
    _run_chat_loop(transcript, "qwen3:8b", {}, [])
    # The transcript now contains an assistant turn (with tool_calls) and a
    # role=tool turn carrying the structured "not registered" error.
    tool_messages = [m for m in transcript if m.role == "tool"]
    assert len(tool_messages) == 1
    payload = json.loads(tool_messages[0].content)
    assert "not registered" in payload["error"]


def test_run_chat_loop_tool_error_surfaces_to_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """When the registry raises ToolError, the loop wraps it as a role=tool message."""
    iteration = {"n": 0}

    def chat_seq(**_kwargs):
        iteration["n"] += 1
        if iteration["n"] == 1:
            return _ok_response(
                text="",
                tool_calls=[{"function": {"name": "buggy.tool", "arguments": "{}"}}],
            )
        return _ok_response(text="done")

    def raise_tool_error(name, args):
        raise ToolError(f"synthetic failure for {name}")

    monkeypatch.setattr(server_module.ollama, "chat", chat_seq)
    monkeypatch.setattr(server_module.default_registry, "call_tool", raise_tool_error)

    transcript = [ChatMessage(role="user", content="trigger error")]
    _run_chat_loop(transcript, "qwen3:8b", {}, [])
    tool_messages = [m for m in transcript if m.role == "tool"]
    assert len(tool_messages) == 1
    payload = json.loads(tool_messages[0].content)
    assert "synthetic failure" in payload["error"]


def test_run_chat_loop_max_iterations_returns_length(monkeypatch: pytest.MonkeyPatch) -> None:
    """If the model keeps emitting tool_calls forever, the loop caps and returns finish=length."""

    def always_tool_calls(**_kwargs):
        return _ok_response(
            text="",
            tool_calls=[{"function": {"name": "anything", "arguments": "{}"}}],
        )

    def quiet_call(name, args):
        return {"result": "ok"}

    monkeypatch.setattr(server_module.ollama, "chat", always_tool_calls)
    monkeypatch.setattr(server_module.default_registry, "call_tool", quiet_call)

    transcript = [ChatMessage(role="user", content="loop forever")]
    final, finish_reason, _pt, _ct = _run_chat_loop(transcript, "qwen3:8b", {}, [])
    assert finish_reason == "length"
    # final_message preserves the tool_calls (the loop ran out of room).
    assert final.tool_calls is not None and len(final.tool_calls) > 0


def test_chat_completions_max_iterations_remaps_length_to_tool_calls(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The OpenAI-compat endpoint rewrites finish_reason from ``length`` to ``tool_calls``
    when the final message still carries tool_calls."""

    def always_tool_calls(**_kwargs):
        return _ok_response(
            text="",
            tool_calls=[{"function": {"name": "anything", "arguments": "{}"}}],
        )

    monkeypatch.setattr(server_module.ollama, "chat", always_tool_calls)
    monkeypatch.setattr(server_module, "_resolve_model", lambda m: "qwen3:8b")
    monkeypatch.setattr(server_module.default_registry, "call_tool", lambda n, a: {"ok": True})

    resp = client.post(
        "/v1/chat/completions",
        json={"model": "qwen3:8b", "messages": [{"role": "user", "content": "loop"}]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["choices"][0]["finish_reason"] == "tool_calls"


# ──────────────────────────────────────────────────────────────────────────
# Streaming generator — object-shape + max-iterations + JSON-decode swallow
# ──────────────────────────────────────────────────────────────────────────


def test_stream_chat_completion_object_shape_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    """The streaming path must handle object-shape chunks as well as dicts."""

    class FakeMsg:
        def __init__(self, content: str) -> None:
            self.content = content
            self.tool_calls = None

    class FakeChunk:
        def __init__(self, content: str, done: bool, done_reason: str | None) -> None:
            self.message = FakeMsg(content)
            self.done = done
            self.done_reason = done_reason

    def fake_chat(**_kwargs):
        return iter(
            [
                FakeChunk("Hello", False, None),
                FakeChunk(" world", True, "stop"),
            ]
        )

    monkeypatch.setattr(server_module.ollama, "chat", fake_chat)

    events = list(_stream_chat_completion([ChatMessage(role="user", content="hi")], "qwen3:8b", {}, []))
    # Find content delta events.
    content_pieces: list[str] = []
    for ev in events:
        if ev.startswith("data: ") and ev.strip() != "data: [DONE]":
            payload = json.loads(ev[len("data: ") :])
            delta = payload.get("choices", [{}])[0].get("delta", {})
            if "content" in delta:
                content_pieces.append(delta["content"])
    assert "".join(content_pieces) == "Hello world"
    assert events[-1] == "data: [DONE]\n\n"


def test_stream_chat_completion_max_iterations_emits_tool_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """If the streaming model keeps emitting tool_calls forever, the loop caps and
    emits finish_reason=tool_calls."""

    def always_tool_calls(**_kwargs):
        return iter(
            [
                {
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [{"function": {"name": "anytool", "arguments": {}}}],
                    },
                    "done": True,
                    "done_reason": "stop",
                }
            ]
        )

    monkeypatch.setattr(server_module.ollama, "chat", always_tool_calls)
    monkeypatch.setattr(server_module.default_registry, "call_tool", lambda n, a: {"ok": True})

    events = list(_stream_chat_completion([ChatMessage(role="user", content="hi")], "qwen3:8b", {}, []))

    # Find the terminator chunk with finish_reason.
    finish_reasons: list[str] = []
    for ev in events:
        if ev.startswith("data: ") and ev.strip() != "data: [DONE]":
            payload = json.loads(ev[len("data: ") :])
            fr = payload.get("choices", [{}])[0].get("finish_reason")
            if fr is not None:
                finish_reasons.append(fr)

    assert "tool_calls" in finish_reasons
    assert events[-1] == "data: [DONE]\n\n"


def test_stream_chat_completion_tool_error_payload_to_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """The streaming path also handles unknown tools / ToolError by appending a structured
    error payload (server-internal — not visible as a delta)."""
    iteration = {"n": 0}

    def chat_side_effect(**_kwargs):
        iteration["n"] += 1
        if iteration["n"] == 1:
            return iter(
                [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [{"function": {"name": "nope.unknown", "arguments": "{}"}}],
                        },
                        "done": True,
                        "done_reason": "stop",
                    }
                ]
            )
        return iter(
            [
                {
                    "message": {"role": "assistant", "content": "fine."},
                    "done": True,
                    "done_reason": "stop",
                }
            ]
        )

    monkeypatch.setattr(server_module.ollama, "chat", chat_side_effect)

    transcript = [ChatMessage(role="user", content="ask")]
    # Pump generator.
    events = list(_stream_chat_completion(transcript, "qwen3:8b", {}, []))

    # The transcript should now include a role=tool message with the structured error.
    tool_messages = [m for m in transcript if m.role == "tool"]
    assert len(tool_messages) == 1
    err_payload = json.loads(tool_messages[0].content)
    assert "not registered" in err_payload["error"]
    # Stream still terminates properly.
    assert events[-1] == "data: [DONE]\n\n"


def test_stream_chat_completion_streaming_tool_error_from_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Registry raising ToolError in the streaming path yields a structured tool-message."""
    iteration = {"n": 0}

    def chat_side_effect(**_kwargs):
        iteration["n"] += 1
        if iteration["n"] == 1:
            return iter(
                [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [{"function": {"name": "bad.tool", "arguments": "{}"}}],
                        },
                        "done": True,
                        "done_reason": "stop",
                    }
                ]
            )
        return iter(
            [
                {
                    "message": {"role": "assistant", "content": "got it"},
                    "done": True,
                    "done_reason": "stop",
                }
            ]
        )

    def boom(name, args):
        raise ToolError("inner-tool-blew-up")

    monkeypatch.setattr(server_module.ollama, "chat", chat_side_effect)
    monkeypatch.setattr(server_module.default_registry, "call_tool", boom)

    transcript = [ChatMessage(role="user", content="ask")]
    list(_stream_chat_completion(transcript, "qwen3:8b", {}, []))
    tool_messages = [m for m in transcript if m.role == "tool"]
    assert len(tool_messages) == 1
    payload = json.loads(tool_messages[0].content)
    assert "inner-tool-blew-up" in payload["error"]


# ──────────────────────────────────────────────────────────────────────────
# _stream_with_session_append — full coverage
# ──────────────────────────────────────────────────────────────────────────


def test_stream_with_session_append_persists_user_and_assistant_turns(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After streaming completes, user message + accumulated assistant content land in the store."""
    monkeypatch.setenv("LINUS_SESSIONS_DB", str(tmp_path / "sessions.db"))
    reset_default_store()

    from linus.memory.sessions import get_default_store

    store = get_default_store()
    session = store.create_session()
    sid = session.id

    def fake_chat(**_kwargs):
        return iter(
            [
                {"message": {"role": "assistant", "content": "Hello "}, "done": False, "done_reason": None},
                {"message": {"role": "assistant", "content": "back!"}, "done": True, "done_reason": "stop"},
            ]
        )

    monkeypatch.setattr(server_module.ollama, "chat", fake_chat)

    transcript = [ChatMessage(role="user", content="hi")]
    new_messages = [ChatMessage(role="user", content="hi")]
    events = list(
        _stream_with_session_append(
            transcript=transcript,
            resolved_model="qwen3:8b",
            options={},
            tool_specs=[],
            store=store,
            session_id=sid,
            new_messages=new_messages,
        )
    )

    # Stream terminates cleanly.
    assert events[-1] == "data: [DONE]\n\n"
    # History reflects both turns.
    stored = store.get_messages(sid)
    assert len(stored) == 2
    assert stored[0].role == "user"
    assert stored[0].content == "hi"
    assert stored[1].role == "assistant"
    assert stored[1].content == "Hello back!"

    reset_default_store()


def test_stream_with_session_append_ignores_malformed_json_payloads(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Mid-stream payloads that fail json.loads must not abort the session-append accumulator."""
    monkeypatch.setenv("LINUS_SESSIONS_DB", str(tmp_path / "sessions.db"))
    reset_default_store()

    from linus.memory.sessions import get_default_store

    store = get_default_store()
    session = store.create_session()
    sid = session.id

    # Inject a fake stream generator that yields a malformed event before
    # the real ones.
    def fake_inner_stream(*_a, **_kw) -> Iterator[str]:
        yield "data: {not-valid-json}\n\n"
        yield (
            "data: "
            + json.dumps(
                {
                    "id": "chatcmpl-x",
                    "object": "chat.completion.chunk",
                    "created": 0,
                    "model": "qwen3:8b",
                    "choices": [{"index": 0, "delta": {"content": "valid-content"}, "finish_reason": None}],
                }
            )
            + "\n\n"
        )
        yield "data: [DONE]\n\n"

    monkeypatch.setattr(server_module, "_stream_chat_completion", fake_inner_stream)

    new_messages = [ChatMessage(role="user", content="hi")]
    events = list(
        _stream_with_session_append(
            transcript=[ChatMessage(role="user", content="hi")],
            resolved_model="qwen3:8b",
            options={},
            tool_specs=[],
            store=store,
            session_id=sid,
            new_messages=new_messages,
        )
    )
    # Output ends with [DONE].
    assert events[-1] == "data: [DONE]\n\n"
    # Assistant turn accumulated despite the malformed payload.
    stored = store.get_messages(sid)
    assistant_msgs = [m for m in stored if m.role == "assistant"]
    assert len(assistant_msgs) == 1
    assert assistant_msgs[0].content == "valid-content"

    reset_default_store()


def test_stream_with_session_append_swallows_store_failure(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A store failure during the post-stream append must not raise out of the generator."""
    monkeypatch.setenv("LINUS_SESSIONS_DB", str(tmp_path / "sessions.db"))
    reset_default_store()

    from linus.memory.sessions import get_default_store

    store = get_default_store()
    session = store.create_session()
    sid = session.id

    def fake_inner_stream(*_a, **_kw) -> Iterator[str]:
        yield (
            "data: "
            + json.dumps(
                {
                    "id": "chatcmpl-x",
                    "object": "chat.completion.chunk",
                    "created": 0,
                    "model": "qwen3:8b",
                    "choices": [{"index": 0, "delta": {"content": "abc"}, "finish_reason": None}],
                }
            )
            + "\n\n"
        )
        yield "data: [DONE]\n\n"

    monkeypatch.setattr(server_module, "_stream_chat_completion", fake_inner_stream)
    monkeypatch.setattr(store, "append_messages", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("synthetic")))

    new_messages = [ChatMessage(role="user", content="hi")]
    # Should NOT raise.
    events = list(
        _stream_with_session_append(
            transcript=[ChatMessage(role="user", content="hi")],
            resolved_model="qwen3:8b",
            options={},
            tool_specs=[],
            store=store,
            session_id=sid,
            new_messages=new_messages,
        )
    )
    assert events[-1] == "data: [DONE]\n\n"

    reset_default_store()


def test_chat_completions_streaming_with_session_id_persists_after_stream(
    client: TestClient, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end: POST /v1/chat/completions with stream=true + session_id appends turns."""
    monkeypatch.setenv("LINUS_SESSIONS_DB", str(tmp_path / "sessions.db"))
    reset_default_store()

    # Create the session first.
    create_resp = client.post("/v1/sessions", json={})
    sid = create_resp.json()["session_id"]

    chunks = [
        {"message": {"role": "assistant", "content": "Hi "}, "done": False, "done_reason": None},
        {"message": {"role": "assistant", "content": "there!"}, "done": True, "done_reason": "stop"},
    ]
    monkeypatch.setattr(server_module.ollama, "chat", lambda **_kw: iter(chunks))
    monkeypatch.setattr(server_module, "_resolve_model", lambda m: "qwen3:8b")

    resp = client.post(
        "/v1/chat/completions",
        json={
            "model": "qwen3:8b",
            "session_id": sid,
            "stream": True,
            "messages": [{"role": "user", "content": "hi"}],
        },
    )
    assert resp.status_code == 200

    history = client.get(f"/v1/sessions/{sid}/messages").json()["messages"]
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hi there!"

    reset_default_store()


# ──────────────────────────────────────────────────────────────────────────
# Endpoint surface — root + empty-messages 400
# ──────────────────────────────────────────────────────────────────────────


def test_root_endpoint_returns_tour(client: TestClient) -> None:
    """GET / returns the friendly identity + endpoint tour."""
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Linus"
    assert "endpoints" in body
    assert "openai_chat_completions" in body["endpoints"]
    assert "anthropic_messages" in body["endpoints"]
    assert body["docs"] == "/docs"


def test_chat_completions_empty_messages_400(client: TestClient) -> None:
    """Empty messages list → HTTP 400 (non-stream path)."""
    resp = client.post(
        "/v1/chat/completions",
        json={"model": "qwen3:8b", "messages": []},
    )
    assert resp.status_code == 400
    assert "non-empty" in resp.json()["detail"]


def test_chat_completions_no_tool_calls_passthrough(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Plain assistant response with no tool calls → finish_reason from done_reason."""
    monkeypatch.setattr(server_module.ollama, "chat", lambda **_kw: _ok_response("hello", done_reason="stop"))
    monkeypatch.setattr(server_module, "_resolve_model", lambda m: "qwen3:8b")

    resp = client.post(
        "/v1/chat/completions",
        json={"model": "qwen3:8b", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["choices"][0]["finish_reason"] == "stop"
    assert body["choices"][0]["message"]["content"] == "hello"
    assert body["usage"]["total_tokens"] == 10  # prompt(7) + completion(3)


# ──────────────────────────────────────────────────────────────────────────
# main() entry point — uvicorn.run is patched so we don't actually serve
# ──────────────────────────────────────────────────────────────────────────


def test_main_invokes_uvicorn_with_env_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """``main()`` reads LINUS_HOST / LINUS_PORT / LINUS_RELOAD and forwards to uvicorn."""
    monkeypatch.delenv("LINUS_HOST", raising=False)
    monkeypatch.delenv("LINUS_PORT", raising=False)
    monkeypatch.delenv("LINUS_RELOAD", raising=False)

    fake_uvicorn = MagicMock()
    fake_module = MagicMock()
    fake_module.run = fake_uvicorn

    monkeypatch.setitem(__import__("sys").modules, "uvicorn", fake_module)
    server_module.main()
    fake_uvicorn.assert_called_once_with("linus.server:app", host="127.0.0.1", port=8000, reload=False)


def test_main_honors_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    """LINUS_HOST/LINUS_PORT/LINUS_RELOAD override the defaults."""
    monkeypatch.setenv("LINUS_HOST", "0.0.0.0")
    monkeypatch.setenv("LINUS_PORT", "9999")
    monkeypatch.setenv("LINUS_RELOAD", "1")

    fake_uvicorn = MagicMock()
    fake_module = MagicMock()
    fake_module.run = fake_uvicorn

    monkeypatch.setitem(__import__("sys").modules, "uvicorn", fake_module)
    server_module.main()
    fake_uvicorn.assert_called_once_with("linus.server:app", host="0.0.0.0", port=9999, reload=True)
