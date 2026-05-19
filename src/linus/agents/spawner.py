"""Minimal agent spawner — N parallel scoped Worker calls, merged.

The spawner dispatches a batch of :class:`AgentTask` records to local
Ollama Workers concurrently, bounded by a configurable concurrency
limit, and returns the results in the same order as the input tasks.

Design notes
------------

- **Concurrency model.** ``asyncio.gather`` over
  ``asyncio.to_thread``-wrapped synchronous Ollama calls. The Ollama
  Python client's sync API is what
  :mod:`linus.server` already uses; wrapping it in a thread per task
  lets multiple Ollama calls overlap on the wire without requiring
  the async client (which has version-skew issues across the
  ``ollama`` package's 0.x releases). A :class:`asyncio.Semaphore`
  bounds true parallelism to the configured ``concurrency`` value.

- **Failure isolation.** Per-task exceptions are caught and surfaced
  as :attr:`AgentResult.error`; they are *not* raised. The spawner
  always returns a complete result list — a downstream consumer
  (e.g., the Archimedes strategy-fusion engine) decides per-task
  whether to admit, retry, or drop.

- **Model resolution.** Reuses :func:`linus.server._resolve_model` so
  the spawner honors the same fallback chain as the chat-completion
  endpoint. If a future refactor extracts model resolution into its
  own module, this import moves with it.

- **Scope.** This is the v1 / MVP shape. Out of scope:
  KV-cache continuity across tasks, mid-task tool calls, streaming
  per-task output, and dependency graphs between tasks. The Phase 3
  agent-spawner ADR (DEC-0050) discusses the longer-term shape; this
  module is the bare primitive that lets Archimedes prototype against.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

import ollama

from linus.server import _resolve_model


@dataclass(frozen=True)
class AgentTask:
    """One scoped Worker invocation.

    :param name: Caller-supplied identifier; copied into :attr:`AgentResult.task_name`
        so the caller can correlate results without relying on list order.
    :param system: System prompt for this task.
    :param user: User prompt for this task.
    :param model: Optional Ollama model name. When ``None``, the default
        from :data:`linus.server._MODEL_PREFERENCES` is used.
    :param max_tokens: Optional cap on generated tokens (mapped to Ollama's
        ``num_predict`` option). ``None`` means use the model's default.
    """

    name: str
    system: str
    user: str
    model: str | None = None
    max_tokens: int | None = None


@dataclass(frozen=True)
class AgentResult:
    """Outcome of one :class:`AgentTask` invocation.

    On success, :attr:`error` is ``None`` and :attr:`content` carries the
    assistant message. On failure, :attr:`error` carries a short
    ``"<ExceptionType>: <message>"`` string and :attr:`content` is empty.
    :attr:`latency_ms` is always populated (wall time of the attempt,
    success or failure).
    """

    task_name: str
    content: str
    model_used: str
    latency_ms: int
    error: str | None = None


async def spawn_agents(
    tasks: list[AgentTask],
    concurrency: int = 4,
) -> list[AgentResult]:
    """Dispatch all ``tasks`` in parallel, bounded by ``concurrency``.

    Returns results in the same order as the input tasks. Per-task
    failures are surfaced via :attr:`AgentResult.error`, not raised —
    the function always returns a list with one entry per input task.

    :param tasks: Tasks to dispatch. Empty list returns empty list.
    :param concurrency: Maximum concurrent Ollama calls. Default 4
        matches the MacBook M1 Max's practical headroom for 8B-class
        models without thrashing unified memory.
    """
    if not tasks:
        return []

    semaphore = asyncio.Semaphore(max(1, concurrency))

    async def _run(task: AgentTask) -> AgentResult:
        async with semaphore:
            return await asyncio.to_thread(_run_sync, task)

    return list(await asyncio.gather(*(_run(t) for t in tasks)))


def _run_sync(task: AgentTask) -> AgentResult:
    """Synchronous per-task body; called from a thread by :func:`spawn_agents`."""
    started = time.perf_counter()
    requested_model = task.model or "qwen3:8b"

    try:
        resolved = _resolve_model(requested_model)
    except Exception as exc:  # noqa: BLE001 — capture model-resolution failures uniformly
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return AgentResult(
            task_name=task.name,
            content="",
            model_used=requested_model,
            latency_ms=elapsed_ms,
            error=f"{type(exc).__name__}: {exc}",
        )

    messages = [
        {"role": "system", "content": task.system},
        {"role": "user", "content": task.user},
    ]
    chat_kwargs: dict = {"model": resolved, "messages": messages}
    if task.max_tokens is not None:
        chat_kwargs["options"] = {"num_predict": task.max_tokens}

    try:
        response = ollama.chat(**chat_kwargs)
    except Exception as exc:  # noqa: BLE001 — surface any Ollama failure as AgentResult.error
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return AgentResult(
            task_name=task.name,
            content="",
            model_used=resolved,
            latency_ms=elapsed_ms,
            error=f"{type(exc).__name__}: {exc}",
        )

    content = ""
    message = response.get("message") if isinstance(response, dict) else None
    if isinstance(message, dict):
        content = message.get("content", "") or ""
    elif message is not None and hasattr(message, "content"):
        # Newer ollama client returns a typed object.
        content = getattr(message, "content", "") or ""

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return AgentResult(
        task_name=task.name,
        content=content,
        model_used=resolved,
        latency_ms=elapsed_ms,
        error=None,
    )
