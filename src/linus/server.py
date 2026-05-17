"""Linus orchestration backend — Phase 2a bootstrap.

Minimal FastAPI app exposing an OpenAI-compatible ``POST /v1/chat/completions``
endpoint that routes to a local Ollama instance (default: http://localhost:11434).

This is the v0 scaffold called out as Item 1 in
``docs/specs/2026-05-12-linus-implementation-plan.md`` and per DEC-0005
(OpenAI-compatible protocol for Maestro/Worker + front-end/backend). It is
deliberately tiny: no streaming, no tool registry, no router intelligence, no
sandbox, no session store, no audit log. Those land in separate items.

Design notes
------------
- Pydantic models match the public shape of the OpenAI ``ChatCompletion`` /
  ``ChatCompletionRequest`` objects closely enough that any harness already
  speaking OpenAI's HTTP (Cline, openclaw, Claude Code via Ollama plugin,
  curl-based smoke tests) can talk to this endpoint without modification.
- The ``model`` field on the request is honored if the named model is actually
  available locally. If it is not, we resolve to the first preferred fallback
  that *is* available (``qwen3:8b`` → ``qwen2.5:14b`` → ``qwen2.5-coder:7b``).
  If none of the preferences are available, we raise HTTP 503 with the
  available-model list embedded in the error body so the client can fail loud
  rather than silently swap models.
- Ollama is reached via the ``ollama`` Python client (already pinned in
  ``environment.yml`` / ``pyproject.toml``). The client honors ``OLLAMA_HOST``
  for non-default hosts; we do not override it here.
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Any

import ollama
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Preference order for v0. The first locally-available model wins when the
# request's ``model`` field does not name an installed model. The list is
# intentionally short — Phase 2a does not yet do router intelligence.
_DEFAULT_MODEL = os.environ.get("LINUS_DEFAULT_MODEL", "qwen3:8b")
_MODEL_PREFERENCES: tuple[str, ...] = (
    _DEFAULT_MODEL,
    "qwen3:8b",
    "qwen2.5:14b",
    "qwen2.5-coder:7b",
)


# --- OpenAI-compatible request/response models ------------------------------


class ChatMessage(BaseModel):
    """One message in a chat completion request or response."""

    role: str = Field(..., description="One of: 'system', 'user', 'assistant', 'tool'.")
    content: str = Field(..., description="The message text.")
    name: str | None = None


class ChatCompletionRequest(BaseModel):
    """Subset of OpenAI's ChatCompletionRequest sufficient for v0.

    Unused-but-accepted fields (``temperature``, ``top_p``, ``max_tokens``,
    ``stream``) are forwarded as Ollama ``options`` when set. ``stream`` is
    accepted but ignored — streaming lands in a follow-up item.
    """

    model: str
    messages: list[ChatMessage]
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    stream: bool = False


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str | None = None


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: ChatCompletionUsage


# --- helpers ----------------------------------------------------------------


def _list_local_models() -> list[str]:
    """Return the list of model names currently pulled into the local Ollama.

    Wraps ``ollama.list()`` and normalizes the shape across client versions:
    older builds return dicts under ``"models"``; newer ones return typed
    objects with a ``model`` attribute. Either case yields a list[str] of
    fully-qualified names (e.g. ``"qwen2.5-coder:7b"``).
    """
    try:
        resp = ollama.list()
    except Exception as exc:  # pragma: no cover - depends on local daemon
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach Ollama at the configured host: {exc!r}",
        ) from exc

    raw = resp.get("models", []) if isinstance(resp, dict) else getattr(resp, "models", [])
    names: list[str] = []
    for entry in raw:
        if isinstance(entry, dict):
            name = entry.get("model") or entry.get("name")
        else:
            name = getattr(entry, "model", None) or getattr(entry, "name", None)
        if name:
            names.append(name)
    return names


def _resolve_model(requested: str) -> str:
    """Pick the model to actually run.

    The requested name is honored if it is locally pulled. Otherwise we walk
    the preference list and return the first match. If no preference is
    locally available, we raise HTTP 503 with the available-model list — the
    point is to fail loud, not silently swap.
    """
    available = _list_local_models()
    if requested in available:
        return requested
    for candidate in _MODEL_PREFERENCES:
        if candidate in available:
            return candidate
    raise HTTPException(
        status_code=503,
        detail={
            "error": (
                f"Requested model {requested!r} is not pulled and no preferred fallback "
                f"({list(_MODEL_PREFERENCES)}) is locally available."
            ),
            "available_models": available,
            "hint": "Run e.g. `ollama pull qwen3:8b` to install a default Worker model.",
        },
    )


def _build_options(req: ChatCompletionRequest) -> dict[str, Any]:
    """Translate the OpenAI-shape sampling fields into Ollama ``options``."""
    options: dict[str, Any] = {}
    if req.temperature is not None:
        options["temperature"] = req.temperature
    if req.top_p is not None:
        options["top_p"] = req.top_p
    if req.max_tokens is not None:
        # Ollama calls this ``num_predict``.
        options["num_predict"] = req.max_tokens
    return options


# --- app --------------------------------------------------------------------


app = FastAPI(
    title="Linus orchestration backend",
    description=(
        "Phase 2a bootstrap. OpenAI-compatible /v1/chat/completions routing to "
        "a local Ollama instance. See docs/specs/2026-05-12-linus-implementation-plan.md."
    ),
    version="0.0.1.dev0",
)


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    """Lightweight liveness probe. Reports the locally-available model list."""
    try:
        models = _list_local_models()
        ollama_reachable = True
    except HTTPException:
        models = []
        ollama_reachable = False
    return {
        "status": "ok",
        "ollama_reachable": ollama_reachable,
        "models": models,
        "default_model_preference": list(_MODEL_PREFERENCES),
    }


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
def chat_completions(req: ChatCompletionRequest) -> ChatCompletionResponse:
    """OpenAI-compatible chat-completions endpoint.

    The v0 implementation:
    - Resolves the requested model against locally-available Ollama models.
    - Forwards the message list verbatim.
    - Translates ``temperature``, ``top_p``, ``max_tokens`` into Ollama
      ``options``. Other sampling fields are not yet honored.
    - Returns the response in OpenAI ChatCompletion shape.

    Streaming (``stream=true``) is accepted but ignored in v0 — the response
    is always materialized in full before returning.
    """
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages must be a non-empty list")

    resolved = _resolve_model(req.model)
    options = _build_options(req)

    try:
        result = ollama.chat(
            model=resolved,
            messages=[m.model_dump(exclude_none=True) for m in req.messages],
            stream=False,
            options=options or None,
        )
    except ollama.ResponseError as exc:
        raise HTTPException(status_code=502, detail=f"Ollama returned an error: {exc!s}") from exc
    except Exception as exc:  # pragma: no cover - network/daemon failure path
        raise HTTPException(status_code=502, detail=f"Ollama call failed: {exc!r}") from exc

    # The ollama client returns a ChatResponse object (or, on older builds, a
    # dict). Read the assistant message text out in a version-tolerant way.
    if isinstance(result, dict):
        message = result.get("message", {}) or {}
        content = message.get("content", "") if isinstance(message, dict) else ""
        prompt_tokens = int(result.get("prompt_eval_count", 0) or 0)
        completion_tokens = int(result.get("eval_count", 0) or 0)
        finish_reason = result.get("done_reason") or ("stop" if result.get("done") else None)
    else:
        message_obj = getattr(result, "message", None)
        content = getattr(message_obj, "content", "") if message_obj is not None else ""
        prompt_tokens = int(getattr(result, "prompt_eval_count", 0) or 0)
        completion_tokens = int(getattr(result, "eval_count", 0) or 0)
        finish_reason = getattr(result, "done_reason", None) or ("stop" if getattr(result, "done", False) else None)

    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        created=int(time.time()),
        model=resolved,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content=content or ""),
                finish_reason=finish_reason,
            )
        ],
        usage=ChatCompletionUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )


def main() -> None:
    """``linus serve`` entry point — start the uvicorn server.

    Reads host/port from ``LINUS_HOST`` / ``LINUS_PORT`` env vars (defaults:
    ``127.0.0.1`` / ``8000``). Reload is off by default; pass ``LINUS_RELOAD=1``
    to enable autoreload during development.
    """
    import uvicorn

    host = os.environ.get("LINUS_HOST", "127.0.0.1")
    port = int(os.environ.get("LINUS_PORT", "8000"))
    reload = os.environ.get("LINUS_RELOAD", "0") == "1"
    uvicorn.run("linus.server:app", host=host, port=port, reload=reload)


if __name__ == "__main__":  # pragma: no cover
    main()
