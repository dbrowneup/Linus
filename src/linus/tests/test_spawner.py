"""Tests for the minimal agent spawner (:mod:`linus.agents.spawner`).

The Ollama client is patched throughout so the suite is hermetic — no
local Ollama install required to run.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import patch

import pytest

from linus.agents import AgentResult, AgentTask, spawn_agents


def _ok_chat_response(text: str = "ok") -> dict:
    """Build an Ollama-shaped chat response dict."""
    return {"message": {"role": "assistant", "content": text}}


def test_empty_task_list_returns_empty() -> None:
    """Edge case: no tasks → no results, no failures."""
    results = asyncio.run(spawn_agents([]))
    assert results == []


def test_all_tasks_succeed() -> None:
    """Three trivial tasks all return successful AgentResults in input order."""
    tasks = [
        AgentTask(name="say-hello", system="", user="say hello"),
        AgentTask(name="count-3", system="", user="count to 3"),
        AgentTask(name="describe-cat", system="", user="describe a cat"),
    ]

    with (
        patch("linus.agents.spawner.ollama.chat") as mock_chat,
        patch("linus.agents.spawner._resolve_model", return_value="qwen3:8b"),
    ):
        mock_chat.side_effect = [
            _ok_chat_response("hello"),
            _ok_chat_response("one, two, three"),
            _ok_chat_response("a small furry creature"),
        ]
        results = asyncio.run(spawn_agents(tasks))

    assert len(results) == 3
    assert all(isinstance(r, AgentResult) for r in results)
    assert all(r.error is None for r in results)
    # Order preserved.
    assert [r.task_name for r in results] == ["say-hello", "count-3", "describe-cat"]
    assert results[0].content == "hello"
    assert results[1].content == "one, two, three"
    assert results[2].content == "a small furry creature"
    assert all(r.model_used == "qwen3:8b" for r in results)
    assert all(r.latency_ms >= 0 for r in results)


def test_per_task_failure_isolated_to_that_task() -> None:
    """One task raising should NOT crash the batch — its result carries the error."""
    tasks = [
        AgentTask(name="ok-1", system="", user="hi"),
        AgentTask(name="boom", system="", user="trigger failure"),
        AgentTask(name="ok-2", system="", user="hi again"),
    ]

    def side_effect(**kwargs):
        # Use the messages content to discriminate which task this is.
        user_msg = next(
            (m["content"] for m in kwargs.get("messages", []) if m["role"] == "user"),
            "",
        )
        if "failure" in user_msg:
            raise RuntimeError("simulated ollama crash")
        return _ok_chat_response("ok")

    with (
        patch("linus.agents.spawner.ollama.chat", side_effect=side_effect),
        patch("linus.agents.spawner._resolve_model", return_value="qwen3:8b"),
    ):
        results = asyncio.run(spawn_agents(tasks))

    assert len(results) == 3
    by_name = {r.task_name: r for r in results}
    assert by_name["ok-1"].error is None
    assert by_name["ok-2"].error is None
    assert by_name["boom"].error is not None
    assert "RuntimeError" in by_name["boom"].error
    assert "simulated ollama crash" in by_name["boom"].error
    assert by_name["boom"].content == ""


def test_model_resolution_failure_isolated() -> None:
    """A model_resolve failure surfaces as the task's error, not raised."""
    tasks = [AgentTask(name="bad-model", system="", user="hi", model="nonexistent:99b")]

    with patch(
        "linus.agents.spawner._resolve_model",
        side_effect=RuntimeError("no such model"),
    ):
        results = asyncio.run(spawn_agents(tasks))

    assert len(results) == 1
    assert results[0].error is not None
    assert "no such model" in results[0].error
    # model_used falls back to the requested model when resolution fails.
    assert results[0].model_used == "nonexistent:99b"


def test_concurrency_actually_parallelizes() -> None:
    """Three tasks at 100 ms each, concurrency=3 → total < 250 ms.

    If concurrency weren't working, total would be ~300 ms (serial).
    Allowing slack for scheduler overhead.
    """
    tasks = [AgentTask(name=f"t{i}", system="", user="hi") for i in range(3)]

    def slow_chat(**kwargs):
        time.sleep(0.1)
        return _ok_chat_response("ok")

    with (
        patch("linus.agents.spawner.ollama.chat", side_effect=slow_chat),
        patch("linus.agents.spawner._resolve_model", return_value="qwen3:8b"),
    ):
        start = time.perf_counter()
        results = asyncio.run(spawn_agents(tasks, concurrency=3))
        elapsed = time.perf_counter() - start

    assert len(results) == 3
    assert all(r.error is None for r in results)
    # Concurrency=3, three 100ms tasks → ~100ms (one wave) + overhead.
    # Serial would be ~300ms. Threshold of 250ms gives generous overhead headroom
    # while still proving parallelism.
    assert elapsed < 0.25, f"Expected parallel execution under 250ms, got {elapsed:.3f}s"


def test_concurrency_limit_serializes_excess() -> None:
    """At concurrency=1 the same three 100ms tasks should take ~300ms (serial)."""
    tasks = [AgentTask(name=f"t{i}", system="", user="hi") for i in range(3)]

    def slow_chat(**kwargs):
        time.sleep(0.1)
        return _ok_chat_response("ok")

    with (
        patch("linus.agents.spawner.ollama.chat", side_effect=slow_chat),
        patch("linus.agents.spawner._resolve_model", return_value="qwen3:8b"),
    ):
        start = time.perf_counter()
        results = asyncio.run(spawn_agents(tasks, concurrency=1))
        elapsed = time.perf_counter() - start

    assert len(results) == 3
    # Serial: three 100ms tasks ≈ 300ms minimum.
    assert elapsed >= 0.29, f"Expected serial execution >= 290ms, got {elapsed:.3f}s"


def test_max_tokens_threaded_into_ollama_options() -> None:
    """max_tokens=50 should map to Ollama's options['num_predict'] = 50."""
    tasks = [AgentTask(name="capped", system="", user="hi", max_tokens=50)]

    with (
        patch("linus.agents.spawner.ollama.chat", return_value=_ok_chat_response("hi")) as mock_chat,
        patch("linus.agents.spawner._resolve_model", return_value="qwen3:8b"),
    ):
        asyncio.run(spawn_agents(tasks))

    call_kwargs = mock_chat.call_args.kwargs
    assert call_kwargs["options"] == {"num_predict": 50}


def test_default_model_used_when_none_specified() -> None:
    """task.model=None routes through default model resolution."""
    tasks = [AgentTask(name="default-model", system="", user="hi")]

    with (
        patch("linus.agents.spawner.ollama.chat", return_value=_ok_chat_response("ok")),
        patch("linus.agents.spawner._resolve_model", return_value="qwen3:8b") as mock_resolve,
    ):
        results = asyncio.run(spawn_agents(tasks))

    mock_resolve.assert_called_once_with("qwen3:8b")
    assert results[0].model_used == "qwen3:8b"


def test_run_sync_catches_message_extraction_failure_as_agent_result_error() -> None:
    """A response whose ``.content`` attribute raises on access must NOT escape
    ``_run_sync`` — the spawner's "always returns a complete result list"
    contract requires the failure to surface as :attr:`AgentResult.error`.

    Regression cover for PR #108 H1: the pre-fix ``_run_sync`` wrapped only the
    ``_resolve_model`` and ``ollama.chat`` call sites in try/except; an
    exception raised by the message-extraction block (e.g., a typed object
    whose ``.content`` property raises) bubbled out of the thread, through
    ``asyncio.to_thread``, and into ``asyncio.gather`` — cancelling the batch
    and discarding partial results.
    """

    class _BrokenMessage:
        # Picking a non-AttributeError exception is load-bearing: ``hasattr``
        # and ``getattr(..., default)`` both swallow ``AttributeError`` from a
        # descriptor, which would silently produce empty content instead of an
        # exception. A ``TypeError`` (or any non-AttributeError) propagates
        # out of the extraction block and exercises the new outer try/except.
        @property
        def content(self) -> str:
            raise TypeError("simulated broken .content descriptor")

    tasks = [
        AgentTask(name="ok-1", system="", user="hi"),
        AgentTask(name="broken", system="", user="trigger broken response"),
        AgentTask(name="ok-2", system="", user="hi again"),
    ]

    def side_effect(**kwargs):
        user_msg = next(
            (m["content"] for m in kwargs.get("messages", []) if m["role"] == "user"),
            "",
        )
        if "broken" in user_msg:
            return {"message": _BrokenMessage()}
        return _ok_chat_response("ok")

    with (
        patch("linus.agents.spawner.ollama.chat", side_effect=side_effect),
        patch("linus.agents.spawner._resolve_model", return_value="qwen3:8b"),
    ):
        results = asyncio.run(spawn_agents(tasks))

    # Contract: one result per input task, in input order, even though one
    # task's response shape was broken.
    assert len(results) == 3
    assert [r.task_name for r in results] == ["ok-1", "broken", "ok-2"]
    by_name = {r.task_name: r for r in results}
    # The two healthy tasks complete normally.
    assert by_name["ok-1"].error is None
    assert by_name["ok-1"].content == "ok"
    assert by_name["ok-2"].error is None
    assert by_name["ok-2"].content == "ok"
    # The broken task surfaces the failure as ``error`` instead of raising.
    assert by_name["broken"].error is not None
    assert "TypeError" in by_name["broken"].error
    assert "simulated broken .content descriptor" in by_name["broken"].error
    assert by_name["broken"].content == ""
    # Latency is still populated on the failed task (wall-time of the attempt).
    assert by_name["broken"].latency_ms >= 0


@pytest.mark.parametrize("message_field", ["dict", "object"])
def test_handles_both_dict_and_object_message_shapes(message_field: str) -> None:
    """The ollama client has evolved across 0.x; support both shapes."""
    tasks = [AgentTask(name="t", system="", user="hi")]

    class _MessageObj:
        content = "hello-object"

    if message_field == "dict":
        response: object = {"message": {"role": "assistant", "content": "hello-dict"}}
        expected = "hello-dict"
    else:
        response = {"message": _MessageObj()}
        expected = "hello-object"

    with (
        patch("linus.agents.spawner.ollama.chat", return_value=response),
        patch("linus.agents.spawner._resolve_model", return_value="qwen3:8b"),
    ):
        results = asyncio.run(spawn_agents(tasks))

    assert results[0].content == expected
    assert results[0].error is None
