"""Linus orchestration backend — Phase 2a bootstrap.

Minimal FastAPI app exposing an OpenAI-compatible ``POST /v1/chat/completions``
endpoint that routes to a local Ollama instance (default: http://localhost:11434).

This is the v0 scaffold called out as Item 1 in
``docs/specs/2026-05-12-linus-implementation-plan.md`` and per DEC-0005
(OpenAI-compatible protocol for Maestro/Worker + front-end/backend). The Item 6
slice (this revision) adds the tool-registry roundtrip: the server now accepts
``tools=[...]`` in the request body and resolves any ``tool_calls`` the model
emits against :data:`linus.tools.default_registry`, looping until the model
returns plain assistant content (or hits ``LINUS_MAX_TOOL_ITERATIONS``).

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
- Tool-call iteration is bounded by ``LINUS_MAX_TOOL_ITERATIONS`` (default 6).
  Reaching the bound finishes the response with ``finish_reason="length"`` and
  returns whatever the last assistant turn produced — better to surface the
  tool-loop spin than hang the request.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
import time
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import ollama
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from linus.memory.sessions import (
    SessionStore,
    StoredMessage,
    get_default_store,
)
from linus.tools import ToolRegistry, default_registry
from linus.tools.registry import ToolError

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

# Cap on the number of tool-call → tool-response cycles per request. A
# well-behaved model needs 1–2 cycles; the safety bound exists to surface
# pathological loops (model keeps re-calling the same tool with the same args)
# rather than burn through compute silently.
_MAX_TOOL_ITERATIONS = int(os.environ.get("LINUS_MAX_TOOL_ITERATIONS", "6"))


# --- OpenAI-compatible request/response models ------------------------------


class ToolCallFunction(BaseModel):
    """The ``function`` field inside a single tool call."""

    name: str
    # OpenAI's wire format ships ``arguments`` as a JSON string; some Ollama
    # builds emit a dict instead. Accept either — the registry's call_tool
    # tolerates both shapes.
    arguments: str | dict[str, Any] = ""


class ToolCall(BaseModel):
    """One model-emitted tool call in OpenAI shape."""

    id: str = Field(default_factory=lambda: f"call_{uuid.uuid4().hex[:24]}")
    type: str = "function"
    function: ToolCallFunction


class ChatMessage(BaseModel):
    """One message in a chat completion request or response.

    ``content`` is optional because tool-call assistant turns and tool-result
    turns may legitimately have empty content (the structured fields carry the
    payload instead).
    """

    role: str = Field(..., description="One of: 'system', 'user', 'assistant', 'tool'.")
    content: str | None = Field(default=None, description="The message text.")
    name: str | None = None
    # Present on assistant messages that requested tools.
    tool_calls: list[ToolCall] | None = None
    # Present on role=tool messages; references the matching tool_call id.
    tool_call_id: str | None = None


class ToolFunctionSpec(BaseModel):
    """OpenAI tool advertisement — the ``function`` half of a tool spec."""

    name: str
    description: str | None = None
    parameters: dict[str, Any] | None = None


class ToolDefinition(BaseModel):
    """OpenAI tool advertisement — the outer envelope."""

    type: str = "function"
    function: ToolFunctionSpec


class ChatCompletionRequest(BaseModel):
    """Subset of OpenAI's ChatCompletionRequest sufficient for v0.

    Unused-but-accepted fields (``temperature``, ``top_p``, ``max_tokens``,
    ``stream``) are forwarded as Ollama ``options`` when set. ``stream`` is
    accepted but ignored — streaming lands in a follow-up item.

    The ``tools`` field is treated as an *additive* advertisement: any tools the
    client lists are merged with the server-side :data:`linus.tools.default_registry`
    (server-side names win on collision). This lets harnesses extend the menu
    per-request without having to redeclare the KB tools every time.
    """

    model: str
    messages: list[ChatMessage]
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    stream: bool = False
    tools: list[ToolDefinition] | None = None
    # OpenAI permits ``"auto"`` / ``"none"`` / ``"required"`` / a forced-tool
    # object here; v0 accepts and forwards the string forms verbatim.
    tool_choice: str | dict[str, Any] | None = None
    # Optional session_id makes the request stateful: when present, the
    # server prepends prior stored history to ``messages`` before sending
    # to Ollama, and appends the new user turn(s) + assistant response to
    # the store after the call completes. Per task A.3 of the MVP spec.
    session_id: str | None = None


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


# --- Session-store API models (task A.3) ------------------------------------


class CreateSessionRequest(BaseModel):
    """Body of ``POST /v1/sessions``. All fields are optional."""

    model: str | None = None
    system_prompt: str | None = None
    session_id: str | None = Field(
        default=None,
        description="Client-provided session id (UUID). If omitted, the server mints one.",
    )


class CreateSessionResponse(BaseModel):
    session_id: str
    created_at: int
    model: str | None = None
    system_prompt: str | None = None


class StoredMessageOut(BaseModel):
    """One entry in ``GET /v1/sessions/{id}/messages``."""

    idx: int
    role: str
    content: str
    created_at: int


class SessionMessagesResponse(BaseModel):
    session_id: str
    messages: list[StoredMessageOut]


# --- Direct tool-invocation models (per task LX-2 follow-up) ----------------


class ToolInvokeRequest(BaseModel):
    """Body of ``POST /v1/tools/{tool_name}/invoke``.

    The tool is identified by its registered name in the path; this body
    carries only the keyword arguments the tool will be called with. Empty
    by default so tools that take no arguments (e.g. ``paperqa.reset``)
    can be invoked with ``{}``.
    """

    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Keyword arguments forwarded to the registered tool.",
    )


class ToolInvokeResponse(BaseModel):
    """Successful response from ``POST /v1/tools/{tool_name}/invoke``.

    ``result`` carries the tool's return value verbatim, serialized as
    whatever JSON-compatible Python object the tool produced (dict, list,
    str, etc.). ``duration_ms`` is the wall-clock time spent inside the
    tool, useful for UI surfaces that want to show "took 12.3 s" without
    re-timing the HTTP roundtrip themselves.
    """

    tool: str
    result: Any
    duration_ms: float


# --- Anthropic-compatible request/response models (per DEC-0056) ------------


class AnthropicTextBlock(BaseModel):
    """One ``{"type": "text", "text": ...}`` content block."""

    type: str = "text"
    text: str


class AnthropicInputMessage(BaseModel):
    """One message in an Anthropic Messages API request.

    Anthropic accepts ``content`` as either a plain string OR a list of
    typed content blocks (text, image, tool_use, tool_result, etc.). v1
    accepts both shapes for ``role`` ∈ {``user``, ``assistant``}; only
    text content is forwarded to the underlying Ollama model. Non-text
    blocks are silently dropped with a logged warning — image/tool
    handling is a v2 hop.
    """

    role: str
    content: str | list[AnthropicTextBlock | dict[str, Any]]


class AnthropicMessageRequest(BaseModel):
    """Subset of the Anthropic Messages API sufficient for v1.

    See https://docs.anthropic.com/en/api/messages for the full spec.
    Fields beyond this subset are accepted but ignored (Pydantic
    silently drops unknown fields).
    """

    model: str
    max_tokens: int
    messages: list[AnthropicInputMessage]
    system: str | None = None
    temperature: float | None = None
    top_p: float | None = None
    stream: bool = False
    # Anthropic also accepts ``stop_sequences`` and ``metadata``; we accept
    # but don't act on them in v1.
    stop_sequences: list[str] | None = None
    metadata: dict[str, Any] | None = None


class AnthropicUsage(BaseModel):
    """Anthropic-shape usage payload."""

    input_tokens: int = 0
    output_tokens: int = 0


class AnthropicMessageResponse(BaseModel):
    """Anthropic Messages API response shape.

    The Python ``anthropic`` SDK constructs its ``Message`` object from
    exactly this JSON shape, so as long as the field names and types
    match, the SDK is happy.
    """

    id: str
    type: str = "message"
    role: str = "assistant"
    content: list[AnthropicTextBlock]
    model: str
    stop_reason: str | None = "end_turn"
    stop_sequence: str | None = None
    usage: AnthropicUsage


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


def _resolve_papers_dir() -> Path:
    """Resolve the paper-qa papers directory the same way
    :func:`linus.knowledge.paperqa._papers_dir` does.

    Duplicated here (rather than imported) so degradation detection does not
    drag paper-qa import-time cost into ``/healthz``. The resolution order
    must stay in lock-step with the paperqa module:

    1. ``LINUS_PAPERQA_DIR`` env var, if set.
    2. ``LINUS_PAPERS_DIR`` env var, if set (shared with arxiv_ingest).
    3. ``~/.linus/papers/`` default.
    """
    raw = os.environ.get("LINUS_PAPERQA_DIR") or os.environ.get("LINUS_PAPERS_DIR")
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".linus" / "papers"


def _kb_artifact_paths() -> list[tuple[str, Path]]:
    """Return the canonical ``(label, path)`` list of KB artifacts.

    Mirrors the artifact table rendered by ``src/linus/app/main.py`` so
    /healthz reports the same set the Streamlit landing audits. Reading
    ``linus.app.config`` here pulls in the same env-var resolution the UI
    uses without forcing Streamlit as a server import.
    """
    from linus.app.config import KB_EMBEDDINGS_DIR, KB_METADATA_DB, KB_OUTPUTS_DIR

    return [
        ("hierarchy.json", KB_OUTPUTS_DIR / "hierarchy.json"),
        ("labels_broad.json", KB_OUTPUTS_DIR / "labels_broad.json"),
        ("graph_sigma.html", KB_OUTPUTS_DIR / "graph" / "graph_sigma.html"),
        ("kg_graph.graphml", KB_OUTPUTS_DIR / "knowledge_graph" / "kg_graph.graphml"),
        ("metadata.db", KB_METADATA_DB),
        ("specter2.npy", KB_EMBEDDINGS_DIR / "specter2.npy"),
    ]


def _compute_degradations() -> tuple[str, list[dict[str, Any]]]:
    """Inspect Linus's effective runtime state and return ``(effective_state, degradations)``.

    The orchestration server can be "reachable" yet still unable to do its
    primary job: the preferred Worker model may not be pulled, paper-qa's
    papers directory may be empty, KB outputs may be missing, or Ollama may
    be running with zero models installed. The original ``/healthz`` only
    surfaced reachable-vs-down, which let these failures hide until tool
    invocation. This function makes them loud.

    Detection covers four classes (see CLAUDE.md and the Q3 spec for
    cross-pollination context from Archimedes' ``/health``):

    - ``worker_model`` — the first preferred model is not in the locally
      pulled list. severity=warning if a fallback preference matches;
      severity=error if no preference matches at all.
    - ``papers_dir`` — the resolved papers directory does not exist OR
      contains zero PDFs. severity=error (paper-qa tools will fail at
      call time without a populated directory).
    - ``kb_outputs`` — one or more of the canonical KB artifact paths
      (hierarchy.json, labels_broad.json, graph, kg, metadata.db,
      specter2.npy) is missing. One degradation entry per missing
      artifact; severity=warning each (Streamlit pages already handle the
      missing case gracefully).
    - ``ollama_models_empty`` — Ollama is reachable but no models are
      pulled at all. severity=error.

    The returned ``effective_state`` is:

    - ``"live"`` — zero degradations.
    - ``"degraded"`` — warnings only.
    - ``"down"`` — any error-severity degradation, OR Ollama unreachable.

    Each degradation carries an actionable ``remediation`` string so the
    UI can show a concrete fix (e.g. ``ollama pull qwen3:8b``) rather
    than a vague "warning". The shape is::

        {"component": str,
         "expected": str,
         "actual": str,
         "severity": "warning" | "error",
         "remediation": str}
    """
    degradations: list[dict[str, Any]] = []
    ollama_reachable = True
    models: list[str] = []

    try:
        models = _list_local_models()
    except HTTPException:
        ollama_reachable = False

    # --- ollama_models_empty ------------------------------------------------
    # If Ollama is reachable but has zero models pulled, every Worker call
    # will fail immediately. Surface this as an error, not a warning.
    if ollama_reachable and not models:
        degradations.append(
            {
                "component": "ollama_models_empty",
                "expected": "at least one model pulled in Ollama",
                "actual": "Ollama reachable but no models installed",
                "severity": "error",
                "remediation": f"Run: ollama pull {_MODEL_PREFERENCES[0]}",
            }
        )

    # --- worker_model -------------------------------------------------------
    # The first preference is the model Linus actually wants to use. If it's
    # missing but a later preference is locally available, that's a silent
    # fall-through — degradation=warning. If NO preference is available,
    # ``_resolve_model`` would 503; surface that as a degradation=error so
    # /healthz answers the question without a chat-completions roundtrip.
    if ollama_reachable and models:
        first_preference = _MODEL_PREFERENCES[0]
        if first_preference not in models:
            available_preference = next(
                (m for m in _MODEL_PREFERENCES if m in models),
                None,
            )
            if available_preference is None:
                degradations.append(
                    {
                        "component": "worker_model",
                        "expected": f"first preference {first_preference!r} (or any of {list(_MODEL_PREFERENCES)})",
                        "actual": f"none of the preferred models are pulled; available: {models}",
                        "severity": "error",
                        "remediation": f"Run: ollama pull {first_preference}",
                    }
                )
            else:
                degradations.append(
                    {
                        "component": "worker_model",
                        "expected": f"first preference {first_preference!r}",
                        "actual": f"falling back to {available_preference!r}",
                        "severity": "warning",
                        "remediation": f"Run: ollama pull {first_preference}",
                    }
                )

    # --- papers_dir ---------------------------------------------------------
    # paper-qa tools register at import time and only fail at call time when
    # the directory is missing or empty. Surface both shapes as a single
    # error-severity degradation so the operator sees it before a tool call.
    papers_dir = _resolve_papers_dir()
    if not papers_dir.exists():
        degradations.append(
            {
                "component": "papers_dir",
                "expected": f"existing directory at {papers_dir}",
                "actual": "directory does not exist",
                "severity": "error",
                "remediation": (
                    f"Create the directory and add PDFs: mkdir -p {papers_dir} "
                    "(or set LINUS_PAPERQA_DIR to an existing directory)"
                ),
            }
        )
    else:
        try:
            pdfs = list(papers_dir.glob("*.pdf"))
        except OSError as exc:
            degradations.append(
                {
                    "component": "papers_dir",
                    "expected": f"readable directory at {papers_dir}",
                    "actual": f"cannot enumerate PDFs: {exc!s}",
                    "severity": "error",
                    "remediation": f"Check permissions on {papers_dir}",
                }
            )
        else:
            if not pdfs:
                degradations.append(
                    {
                        "component": "papers_dir",
                        "expected": f"at least one PDF in {papers_dir}",
                        "actual": "directory exists but contains zero PDFs",
                        "severity": "error",
                        "remediation": (
                            f"Add PDFs to {papers_dir} (e.g. via the paperqa.ingest tool "
                            "or by copying papers in manually)"
                        ),
                    }
                )

    # --- kb_outputs ---------------------------------------------------------
    # Per-artifact entries (warning each) so the operator can see exactly
    # which artifact is missing without cross-referencing the artifact list
    # in the Streamlit landing.
    try:
        artifacts = _kb_artifact_paths()
    except Exception:
        # Defensive: linus.app.config import or env-var-resolution failure
        # must not crash /healthz. Surface as zero kb_outputs degradations
        # rather than a 500.
        artifacts = []
    for name, path in artifacts:
        if not path.exists():
            degradations.append(
                {
                    "component": "kb_outputs",
                    "expected": f"KB artifact {name} at {path}",
                    "actual": "missing",
                    "severity": "warning",
                    "remediation": (
                        f"Run the KnowledgeBase pipeline to produce {name}, or set "
                        "LINUS_KB_OUTPUTS_DIR / LINUS_KB_METADATA_DB / "
                        "LINUS_KB_EMBEDDINGS_DIR to a populated location"
                    ),
                }
            )

    # --- effective_state classification ------------------------------------
    # "down" covers both Ollama-unreachable AND any error-severity
    # degradation; the orchestration server cannot do its primary job in
    # either case.
    if not ollama_reachable or any(d["severity"] == "error" for d in degradations):
        effective_state = "down"
    elif degradations:
        effective_state = "degraded"
    else:
        effective_state = "live"

    return effective_state, degradations


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


def _merge_tool_specs(
    registry: ToolRegistry,
    request_tools: list[ToolDefinition] | None,
) -> list[dict[str, Any]]:
    """Combine the server-side registry's tools with any request-supplied ones.

    Server-side names take precedence on collision: the registry is the
    audit-of-record for what Linus actually executes, and silently shadowing
    a registered tool with a client-supplied advertisement of the same name
    would defeat that. Client-only tools are forwarded as-is; the model gets
    to see them, but if it tries to call them the registry will raise
    :class:`KeyError` and the loop surfaces a tool-not-found error to the
    model — which is the right way to fail.
    """
    specs: dict[str, dict[str, Any]] = {}
    if request_tools:
        for td in request_tools:
            specs[td.function.name] = td.model_dump(exclude_none=True)
    for spec in registry.openai_specs():
        specs[spec["function"]["name"]] = spec
    return [specs[name] for name in sorted(specs)]


def _extract_tool_calls(message_obj: Any) -> list[ToolCall]:
    """Pull ``tool_calls`` out of an Ollama response message in either shape.

    Ollama's typed Message has ``tool_calls: list[Message.ToolCall]`` where each
    item is ``{function: {name, arguments}}``. Older / dict-shape responses use
    the same structure but as dicts. Either path produces a list of our pydantic
    :class:`ToolCall` records (which auto-generate ``id`` when the upstream
    didn't provide one — Ollama typically doesn't).
    """
    if message_obj is None:
        return []

    raw = message_obj.get("tool_calls") if isinstance(message_obj, dict) else getattr(message_obj, "tool_calls", None)
    if not raw:
        return []

    out: list[ToolCall] = []
    for entry in raw:
        if isinstance(entry, dict):
            fn = entry.get("function") or {}
            name = fn.get("name") if isinstance(fn, dict) else getattr(fn, "name", None)
            args = fn.get("arguments") if isinstance(fn, dict) else getattr(fn, "arguments", None)
            call_id = entry.get("id")
        else:
            fn = getattr(entry, "function", None)
            name = getattr(fn, "name", None) if fn is not None else None
            args = getattr(fn, "arguments", None) if fn is not None else None
            call_id = getattr(entry, "id", None)

        if not name:
            continue
        tc = ToolCall(
            id=call_id or f"call_{uuid.uuid4().hex[:24]}",
            function=ToolCallFunction(name=name, arguments=args or ""),
        )
        out.append(tc)
    return out


def _format_tool_result(result: Any) -> str:
    """Render a tool result as the string body of a ``role=tool`` message.

    Tries JSON first since most tool outputs are plain dicts / lists; falls
    back to ``str(result)`` for anything that doesn't serialize cleanly.
    """
    if result is None:
        return "null"
    if isinstance(result, str):
        return result
    try:
        return json.dumps(result, default=str)
    except (TypeError, ValueError):
        return str(result)


def _stored_to_chat_message(stored: StoredMessage) -> ChatMessage:
    """Translate a :class:`StoredMessage` into the internal :class:`ChatMessage` shape."""
    return ChatMessage(role=stored.role, content=stored.content)


def _message_to_ollama(msg: ChatMessage) -> dict[str, Any]:
    """Convert a :class:`ChatMessage` into the dict shape Ollama expects.

    Filters out ``None`` values so optional fields don't confuse older client
    versions, and renormalizes ``tool_calls`` to the ``{function: {name,
    arguments}}`` dict form Ollama accepts.
    """
    out: dict[str, Any] = {"role": msg.role}
    if msg.content is not None:
        out["content"] = msg.content
    elif msg.role in ("system", "user", "tool"):
        # Ollama can be strict about empty content on non-assistant messages;
        # always send something. Assistant tool-call turns may have empty
        # content legitimately.
        out["content"] = ""
    if msg.name:
        out["name"] = msg.name
    if msg.tool_call_id:
        out["tool_call_id"] = msg.tool_call_id
    if msg.tool_calls:
        out["tool_calls"] = [
            {
                "id": tc.id,
                "type": tc.type,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in msg.tool_calls
        ]
    return out


def _run_chat_loop(
    transcript: list[ChatMessage],
    resolved_model: str,
    options: dict[str, Any],
    tool_specs: list[dict[str, Any]],
) -> tuple[ChatMessage, str, int, int]:
    """Run the Ollama chat-with-tools loop and return the final message.

    Shared between :func:`chat_completions` (OpenAI shape) and
    :func:`messages` (Anthropic shape). Mutates ``transcript`` by
    appending assistant turns + tool-result messages as the loop
    progresses.

    Returns ``(final_message, finish_reason, prompt_tokens, completion_tokens)``.
    """
    final_message: ChatMessage | None = None
    finish_reason: str | None = None
    prompt_tokens_total = 0
    completion_tokens_total = 0

    for iteration in range(_MAX_TOOL_ITERATIONS + 1):
        try:
            result = ollama.chat(
                model=resolved_model,
                messages=[_message_to_ollama(m) for m in transcript],
                stream=False,
                options=options or None,
                tools=tool_specs or None,
            )
        except ollama.ResponseError as exc:
            raise HTTPException(status_code=502, detail=f"Ollama returned an error: {exc!s}") from exc
        except Exception as exc:  # pragma: no cover - network/daemon failure path
            raise HTTPException(status_code=502, detail=f"Ollama call failed: {exc!r}") from exc

        if isinstance(result, dict):
            message_obj = result.get("message", {}) or {}
            content = message_obj.get("content", "") if isinstance(message_obj, dict) else ""
            prompt_tokens = int(result.get("prompt_eval_count", 0) or 0)
            completion_tokens = int(result.get("eval_count", 0) or 0)
            done_reason = result.get("done_reason") or ("stop" if result.get("done") else None)
        else:
            message_obj = getattr(result, "message", None)
            content = getattr(message_obj, "content", "") if message_obj is not None else ""
            prompt_tokens = int(getattr(result, "prompt_eval_count", 0) or 0)
            completion_tokens = int(getattr(result, "eval_count", 0) or 0)
            done_reason = getattr(result, "done_reason", None) or ("stop" if getattr(result, "done", False) else None)

        prompt_tokens_total += prompt_tokens
        completion_tokens_total += completion_tokens

        tool_calls = _extract_tool_calls(message_obj)

        assistant_msg = ChatMessage(
            role="assistant",
            content=content or "",
            tool_calls=tool_calls or None,
        )

        if not tool_calls:
            final_message = assistant_msg
            finish_reason = done_reason or "stop"
            break

        transcript.append(assistant_msg)

        if iteration >= _MAX_TOOL_ITERATIONS:
            final_message = assistant_msg
            finish_reason = "length"
            break

        for tc in tool_calls:
            try:
                tool_result = default_registry.call_tool(tc.function.name, tc.function.arguments)
                payload = _format_tool_result(tool_result)
            except KeyError:
                payload = json.dumps({"error": f"Tool {tc.function.name!r} is not registered"})
            except ToolError as exc:
                payload = json.dumps({"error": str(exc)})
            except Exception as exc:  # pragma: no cover - defensive
                payload = json.dumps({"error": f"Unexpected tool error: {type(exc).__name__}: {exc}"})

            transcript.append(
                ChatMessage(
                    role="tool",
                    name=tc.function.name,
                    tool_call_id=tc.id,
                    content=payload,
                )
            )

    if final_message is None:
        final_message = ChatMessage(role="assistant", content="")
        finish_reason = "stop"

    return final_message, finish_reason or "stop", prompt_tokens_total, completion_tokens_total


def _anthropic_input_to_transcript(req: AnthropicMessageRequest) -> list[ChatMessage]:
    """Translate an Anthropic Messages request into the internal :class:`ChatMessage` list.

    The Anthropic shape has ``system`` as a separate top-level field; we
    fold it into the transcript as a leading ``role=system`` message.
    Multi-block content (list of typed content blocks) is flattened to
    the concatenation of all ``type=text`` blocks; non-text blocks are
    dropped silently in v1 (image / tool_use / tool_result handling is
    a v2 hop).
    """
    transcript: list[ChatMessage] = []
    if req.system:
        transcript.append(ChatMessage(role="system", content=req.system))

    for input_msg in req.messages:
        if isinstance(input_msg.content, str):
            text = input_msg.content
        else:
            text_parts: list[str] = []
            for block in input_msg.content:
                if isinstance(block, AnthropicTextBlock):
                    text_parts.append(block.text)
                elif isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(str(block.get("text", "")))
                # Non-text blocks dropped silently in v1.
            text = "\n".join(p for p in text_parts if p)
        transcript.append(ChatMessage(role=input_msg.role, content=text))

    return transcript


def _ollama_finish_to_anthropic_stop_reason(finish_reason: str | None) -> str:
    """Translate Ollama's ``done_reason`` into Anthropic's ``stop_reason``."""
    if finish_reason in (None, "stop"):
        return "end_turn"
    if finish_reason == "length":
        return "max_tokens"
    return "end_turn"


def _sse_format(payload: dict[str, Any]) -> str:
    """Encode a payload dict as a single Server-Sent Event in OpenAI's wire shape.

    OpenAI's streaming endpoint emits ``data: {json}\\n\\n`` for each chunk and
    a final ``data: [DONE]\\n\\n`` sentinel. This helper handles the ``{json}``
    case; the sentinel is emitted as a string literal at the end of the stream.
    """
    return f"data: {json.dumps(payload)}\n\n"


def _streaming_chunk(
    completion_id: str,
    created: int,
    model: str,
    delta: dict[str, Any],
    finish_reason: str | None = None,
) -> dict[str, Any]:
    """Build one OpenAI ``chat.completion.chunk``-shaped dict.

    Per the OpenAI streaming contract, each chunk has the same envelope as
    a non-streaming completion but with ``object="chat.completion.chunk"``
    and a single ``delta`` (partial update) instead of a full ``message``.
    The first chunk of a stream typically carries ``delta={"role": "assistant"}``;
    subsequent chunks carry ``delta={"content": "<token-or-tokens>"}``;
    the terminal chunk carries an empty delta plus ``finish_reason``.
    """
    return {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": delta,
                "finish_reason": finish_reason,
            }
        ],
    }


def _stream_chat_completion(
    transcript: list[ChatMessage],
    resolved_model: str,
    options: dict[str, Any],
    tool_specs: list[dict[str, Any]],
) -> Iterator[str]:
    """Generator yielding SSE-encoded OpenAI streaming chunks.

    Iterates Ollama's native streaming chat API. When the model emits
    ``tool_calls`` (typically arriving on the final chunk of an iteration),
    the generator executes them server-side via
    :data:`linus.tools.default_registry`, appends ``role=tool`` messages to
    the transcript, and continues streaming the next iteration. Up to
    :data:`_MAX_TOOL_ITERATIONS` cycles; the bound is shared with the
    non-streaming path.

    Tool-call content is **not** emitted as visible deltas to the client —
    the tool roundtrip is server-internal, and only the model's final
    text response surfaces token-by-token. This matches the UX users
    expect (they see the answer, not the plumbing); harnesses that want
    to inspect tool calls should hit the non-streaming endpoint.

    The terminating event is ``data: [DONE]\\n\\n`` per the OpenAI spec.
    Errors mid-stream are emitted as a final ``data: {"error": ...}`` event
    before ``[DONE]`` so the client sees a structured failure rather than
    a half-finished stream.
    """
    completion_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())

    # Emit the leading role chunk (OpenAI's convention: the first delta
    # carries role=assistant; subsequent chunks carry content deltas).
    yield _sse_format(_streaming_chunk(completion_id, created, resolved_model, delta={"role": "assistant"}))

    for iteration in range(_MAX_TOOL_ITERATIONS + 1):
        try:
            stream = ollama.chat(
                model=resolved_model,
                messages=[_message_to_ollama(m) for m in transcript],
                stream=True,
                options=options or None,
                tools=tool_specs or None,
            )
        except Exception as exc:  # noqa: BLE001 — surface any failure mid-stream
            yield _sse_format({"error": {"message": f"Ollama call failed: {exc!r}", "type": "ollama_error"}})
            yield "data: [DONE]\n\n"
            return

        accumulated_content = ""
        last_message_obj: Any = None
        last_done_reason: str | None = None

        for chunk in stream:
            if isinstance(chunk, dict):
                message_obj = chunk.get("message", {}) or {}
                done = bool(chunk.get("done", False))
                done_reason = chunk.get("done_reason")
            else:
                message_obj = getattr(chunk, "message", None) or {}
                done = bool(getattr(chunk, "done", False))
                done_reason = getattr(chunk, "done_reason", None)

            content_delta = ""
            if isinstance(message_obj, dict):
                content_delta = message_obj.get("content", "") or ""
            else:
                content_delta = getattr(message_obj, "content", "") or ""

            if content_delta:
                accumulated_content += content_delta
                yield _sse_format(
                    _streaming_chunk(completion_id, created, resolved_model, delta={"content": content_delta})
                )

            if done:
                last_message_obj = message_obj
                last_done_reason = done_reason
                break

        tool_calls = _extract_tool_calls(last_message_obj) if last_message_obj is not None else []

        if not tool_calls:
            yield _sse_format(
                _streaming_chunk(
                    completion_id,
                    created,
                    resolved_model,
                    delta={},
                    finish_reason=last_done_reason or "stop",
                )
            )
            yield "data: [DONE]\n\n"
            return

        transcript.append(ChatMessage(role="assistant", content=accumulated_content or "", tool_calls=tool_calls))

        if iteration >= _MAX_TOOL_ITERATIONS:
            yield _sse_format(
                _streaming_chunk(
                    completion_id,
                    created,
                    resolved_model,
                    delta={},
                    finish_reason="tool_calls",
                )
            )
            yield "data: [DONE]\n\n"
            return

        for tc in tool_calls:
            try:
                tool_result = default_registry.call_tool(tc.function.name, tc.function.arguments)
                payload = _format_tool_result(tool_result)
            except KeyError:
                payload = json.dumps({"error": f"Tool {tc.function.name!r} is not registered"})
            except ToolError as exc:
                payload = json.dumps({"error": str(exc)})
            except Exception as exc:  # pragma: no cover - defensive
                payload = json.dumps({"error": f"Unexpected tool error: {type(exc).__name__}: {exc}"})

            transcript.append(
                ChatMessage(
                    role="tool",
                    name=tc.function.name,
                    tool_call_id=tc.id,
                    content=payload,
                )
            )

    yield "data: [DONE]\n\n"


def _stream_with_session_append(
    transcript: list[ChatMessage],
    resolved_model: str,
    options: dict[str, Any],
    tool_specs: list[dict[str, Any]],
    store: SessionStore,
    session_id: str,
    new_messages: list[ChatMessage],
) -> Iterator[str]:
    """Wrap :func:`_stream_chat_completion` with a post-stream session append.

    Streams normally, accumulating the assistant content from each
    ``delta.content`` event. After the inner stream emits ``[DONE]``,
    appends the new user/system messages + the accumulated assistant
    response to the session store so the next request with the same
    ``session_id`` sees this turn in its history.

    Session writes are best-effort — any exception during the append
    is swallowed silently so a storage failure doesn't truncate the
    user-visible stream.
    """
    accumulated = ""
    for event in _stream_chat_completion(transcript, resolved_model, options, tool_specs):
        yield event
        # Parse content deltas as they fly by; cheap because each event is
        # already a small JSON blob the client is consuming.
        if event.startswith("data: "):
            payload = event[len("data: ") :].strip()
            if payload and payload != "[DONE]":
                try:
                    chunk = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                choices = chunk.get("choices") or []
                if choices:
                    delta_content = choices[0].get("delta", {}).get("content")
                    if delta_content:
                        accumulated += delta_content

    try:
        new_turns: list[tuple[str, str]] = []
        for m in new_messages:
            if m.role in ("user", "system") and m.content:
                new_turns.append((m.role, m.content))
        if accumulated:
            new_turns.append(("assistant", accumulated))
        if new_turns:
            store.append_messages(session_id, new_turns)
    except Exception:  # noqa: BLE001 — session-store failure must not truncate the stream
        pass


# --- app --------------------------------------------------------------------


app = FastAPI(
    title="Linus orchestration backend",
    description=(
        "Phase 2a bootstrap. OpenAI-compatible /v1/chat/completions routing to "
        "a local Ollama instance. See docs/specs/2026-05-12-linus-implementation-plan.md."
    ),
    version="0.0.2.dev0",
)


@app.get("/")
def root() -> dict[str, Any]:
    """Friendly root endpoint — orients anyone curl-hitting the base URL.

    Returns project identity + a tour of the available endpoints so the
    server isn't an opaque 404 to a curious operator. The Streamlit UI
    uses ``/healthz`` (not this) for its liveness probe; this route is
    purely human-facing.
    """
    return {
        "name": "Linus",
        "tagline": "A personal AI orchestration backend for Apple Silicon.",
        "version": app.version,
        "docs": "/docs",
        "endpoints": {
            "health": "GET /healthz",
            "openai_chat_completions": "POST /v1/chat/completions",
            "anthropic_messages": "POST /v1/messages",
            "tool_invoke": "POST /v1/tools/{tool_name}/invoke",
            "sessions_create": "POST /v1/sessions",
            "sessions_messages": "GET /v1/sessions/{session_id}/messages",
        },
    }


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    """Lightweight liveness probe with degradation reporting.

    Returns the locally-available model list and registered tool names
    (pre-existing keys; backwards-compat preserved) AND two new fields:

    - ``effective_state`` — one of ``"live"`` / ``"degraded"`` / ``"down"``,
      classifying whether Linus can do its primary job. Live-vs-degraded
      was previously invisible: a server could be "reachable" yet have no
      Worker model pulled, an empty papers directory, missing KB
      artifacts, etc. The Streamlit landing's Reachable/Unreachable
      binary swallowed all of these.
    - ``degradations`` — list of structured entries describing each
      detected problem, with an actionable ``remediation`` string the UI
      can surface inline (e.g. ``ollama pull qwen3:8b``).

    See :func:`_compute_degradations` for the full classification
    contract.
    """
    try:
        models = _list_local_models()
        ollama_reachable = True
    except HTTPException:
        models = []
        ollama_reachable = False

    effective_state, degradations = _compute_degradations()

    return {
        "status": "ok",
        "ollama_reachable": ollama_reachable,
        "models": models,
        "default_model_preference": list(_MODEL_PREFERENCES),
        "tools": default_registry.names(),
        "effective_state": effective_state,
        "degradations": degradations,
    }


@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    """OpenAI-compatible chat-completions endpoint.

    The v0+Item6 implementation:
    - Resolves the requested model against locally-available Ollama models.
    - Forwards the message list verbatim, with the merged tool advertisement
      (server registry + any request-supplied tools).
    - When the model returns ``tool_calls``, routes each through
      :data:`linus.tools.default_registry` and appends a ``role=tool`` response
      message per call. Loops until the model returns plain assistant content
      or :data:`_MAX_TOOL_ITERATIONS` is hit.
    - Translates ``temperature``, ``top_p``, ``max_tokens`` into Ollama
      ``options``. Other sampling fields are not yet honored.
    - When ``stream=true``, returns a ``text/event-stream`` SSE response
      emitting OpenAI-shape ``chat.completion.chunk`` events terminated by
      ``data: [DONE]``. Tool-call iterations are server-internal in the
      streaming path — only final assistant text surfaces token-by-token.
    """
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages must be a non-empty list")

    resolved = _resolve_model(req.model)
    options = _build_options(req)
    tool_specs = _merge_tool_specs(default_registry, req.tools)

    # Session-aware mode: if session_id is set, prepend stored history before
    # req.messages. The client only sends NEW turns; the server reconstructs
    # the full transcript so model context survives page refreshes.
    history: list[ChatMessage] = []
    store: SessionStore | None = None
    if req.session_id:
        store = get_default_store()
        store.ensure_session(req.session_id, model=resolved)
        history = [_stored_to_chat_message(m) for m in store.get_messages(req.session_id)]

    transcript: list[ChatMessage] = history + list(req.messages)

    if req.stream:
        if store is not None and req.session_id:
            # Wrap the stream generator with a post-stream session append.
            return StreamingResponse(
                _stream_with_session_append(
                    transcript, resolved, options, tool_specs, store, req.session_id, req.messages
                ),
                media_type="text/event-stream",
            )
        return StreamingResponse(
            _stream_chat_completion(transcript, resolved, options, tool_specs),
            media_type="text/event-stream",
        )

    final_message, finish_reason, prompt_tokens_total, completion_tokens_total = _run_chat_loop(
        transcript, resolved, options, tool_specs
    )

    # Session-aware mode: append the new user turns + assistant response so the
    # next request with the same session_id sees this turn in its history.
    if store is not None and req.session_id:
        new_turns: list[tuple[str, str]] = []
        for m in req.messages:
            if m.role in ("user", "system") and m.content:
                new_turns.append((m.role, m.content))
        if final_message.content:
            new_turns.append(("assistant", final_message.content))
        if new_turns:
            store.append_messages(req.session_id, new_turns)

    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        created=int(time.time()),
        model=resolved,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=final_message,
                finish_reason=(
                    "tool_calls" if final_message.tool_calls and finish_reason == "length" else finish_reason
                ),
            )
        ],
        usage=ChatCompletionUsage(
            prompt_tokens=prompt_tokens_total,
            completion_tokens=completion_tokens_total,
            total_tokens=prompt_tokens_total + completion_tokens_total,
        ),
    )


@app.post("/v1/messages", response_model=AnthropicMessageResponse)
def messages(req: AnthropicMessageRequest) -> AnthropicMessageResponse:
    """Anthropic-compatible Messages API endpoint.

    Implements DEC-0056: Linus speaks Anthropic Messages format alongside
    OpenAI chat-completions so any harness or SDK already pointed at the
    Anthropic API can target Linus via ``base_url=http://localhost:8000``
    without code changes.

    v1 ships **non-streaming only**. ``stream=true`` requests return HTTP
    501 with a structured error pointing at the follow-up task. Full
    Anthropic SSE streaming (``message_start`` / ``content_block_*`` /
    ``message_delta`` / ``message_stop`` events) lands when the OpenAI
    streaming work in task A.1 ships and the same Ollama-streaming
    plumbing can be reused.

    Internally translates the request into the existing internal
    :class:`ChatMessage` transcript, runs the shared
    :func:`_run_chat_loop`, then maps the final assistant message back
    into Anthropic shape. Tool advertisement is intentionally **not**
    exposed via this endpoint in v1 — Anthropic tool-use semantics
    differ enough from OpenAI's that they deserve their own contract;
    callers wanting tool routing should use ``/v1/chat/completions``.
    """
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages must be a non-empty list")

    if req.stream:
        raise HTTPException(
            status_code=501,
            detail={
                "error": "streaming_not_implemented",
                "message": (
                    "Anthropic-compat streaming is not yet wired in Linus v1. "
                    "The non-streaming form is available; call again with stream=false. "
                    "Streaming will land alongside task A.1 (SSE on /v1/chat/completions)."
                ),
            },
        )

    resolved = _resolve_model(req.model)

    # Translate Anthropic sampling fields into the same Ollama options
    # shape ``_build_options`` produces for /v1/chat/completions.
    options: dict[str, Any] = {}
    if req.temperature is not None:
        options["temperature"] = req.temperature
    if req.top_p is not None:
        options["top_p"] = req.top_p
    if req.max_tokens is not None:
        options["num_predict"] = req.max_tokens

    transcript = _anthropic_input_to_transcript(req)
    if not transcript or all(m.role == "system" for m in transcript):
        raise HTTPException(
            status_code=400,
            detail="messages must contain at least one non-system message",
        )

    final_message, finish_reason, prompt_tokens_total, completion_tokens_total = _run_chat_loop(
        transcript, resolved, options, []
    )

    content_text = final_message.content or ""
    return AnthropicMessageResponse(
        id=f"msg_{uuid.uuid4().hex[:24]}",
        type="message",
        role="assistant",
        content=[AnthropicTextBlock(type="text", text=content_text)],
        model=resolved,
        stop_reason=_ollama_finish_to_anthropic_stop_reason(finish_reason),
        stop_sequence=None,
        usage=AnthropicUsage(
            input_tokens=prompt_tokens_total,
            output_tokens=completion_tokens_total,
        ),
    )


@app.post("/v1/tools/{tool_name}/invoke", response_model=ToolInvokeResponse)
async def invoke_tool(tool_name: str, req: ToolInvokeRequest) -> ToolInvokeResponse:
    """Invoke a registered tool directly, bypassing the model.

    Intended for UI surfaces that want structured tool output without the
    natural-language-wrapping a chat completion would introduce. The
    Streamlit paper-qa page uses this to get citation objects back as
    JSON instead of relying on a system-prompt-steered marker-block hack.

    Behavior:

    - Looks up ``tool_name`` in :data:`linus.tools.default_registry`. If
      no tool is registered under that name, returns HTTP 404 with the
      list of available tool names in the error detail so callers can
      self-correct without a separate ``/healthz`` roundtrip.
    - Validates ``req.arguments`` against the tool's JSON-Schema-shaped
      ``parameters.required`` list. Missing required args produce HTTP
      422 with the names listed in the error detail (mirrors FastAPI's
      own validation-error shape conceptually).
    - Awaits the result if the underlying callable is an async
      coroutine; otherwise calls it synchronously in a thread so the
      event loop is not blocked. (Currently-registered ``paperqa.*``
      tools are sync wrappers that internally bridge to async; that
      shape is preserved transparently.)
    - On any uncaught exception inside the tool, returns HTTP 500 with
      ``f"tool raised: {exc_type}: {exc_msg}"`` in the detail — never a
      stack trace.
    - Times the invocation and reports the elapsed milliseconds in the
      response body.

    This endpoint is purely additive; it does not alter the behavior of
    any other route.
    """
    spec = default_registry.get(tool_name)
    if spec is None:
        raise HTTPException(
            status_code=404,
            detail=(f"tool not found: {tool_name}; available: {default_registry.names()}"),
        )

    # Validate required arguments against the tool's declared schema.
    required = list(spec.parameters.get("required", []))
    missing = [name for name in required if name not in req.arguments]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=(f"tool {tool_name!r} missing required arguments: {missing}; required={required}"),
        )

    start = time.perf_counter()
    try:
        if inspect.iscoroutinefunction(spec.func):
            result = await spec.func(**req.arguments)
        else:
            # Run sync tools in a worker thread so a long-running KB or
            # paper-qa call (which may take tens of seconds) does not
            # block FastAPI's event loop and starve concurrent requests.
            result = await asyncio.to_thread(spec.func, **req.arguments)
    except HTTPException:
        raise
    except TypeError as exc:
        # Most often: caller passed an unexpected kwarg, or the schema
        # missed an unmodeled requirement. Surface as 422 so the client
        # can correct the call shape, not as a generic 500.
        raise HTTPException(
            status_code=422,
            detail=f"tool {tool_name!r} rejected arguments: {type(exc).__name__}: {exc}",
        ) from exc
    except Exception as exc:
        # Convert any uncaught tool failure to a structured 500. We catch
        # broadly on purpose: the contract is "the tool ran or 500", not
        # "the tool ran or whichever exception the tool happened to raise".
        raise HTTPException(
            status_code=500,
            detail=f"tool raised: {type(exc).__name__}: {exc}",
        ) from exc

    duration_ms = (time.perf_counter() - start) * 1000.0

    return ToolInvokeResponse(tool=tool_name, result=result, duration_ms=duration_ms)


@app.post("/v1/sessions", response_model=CreateSessionResponse)
def create_session(req: CreateSessionRequest | None = None) -> CreateSessionResponse:
    """Create a new chat session and return its id.

    Body is optional. Callers can supply ``model`` and ``system_prompt``
    for the UI to surface; they're stored verbatim but not enforced on
    subsequent requests. Callers can also provide their own
    ``session_id`` (e.g. a browser-generated UUID) and the server will
    honor it.
    """
    body = req or CreateSessionRequest()
    store = get_default_store()
    session = store.create_session(
        model=body.model,
        system_prompt=body.system_prompt,
        session_id=body.session_id,
    )
    return CreateSessionResponse(
        session_id=session.id,
        created_at=session.created_at,
        model=session.model,
        system_prompt=session.system_prompt,
    )


@app.get("/v1/sessions/{session_id}/messages", response_model=SessionMessagesResponse)
def get_session_messages(session_id: str) -> SessionMessagesResponse:
    """Return the stored message history for a session.

    Used by the Streamlit chat page (task B.1) to render conversation
    history on page load. The session must exist; 404 otherwise.
    """
    store = get_default_store()
    if store.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown session_id: {session_id!r}")
    messages = store.get_messages(session_id)
    return SessionMessagesResponse(
        session_id=session_id,
        messages=[
            StoredMessageOut(
                idx=m.idx,
                role=m.role,
                content=m.content,
                created_at=m.created_at,
            )
            for m in messages
        ],
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
