"""In-memory tool registry plus the :func:`tool` decorator.

The registry is a dict-of-callables keyed by tool name. Each entry carries:

* the callable itself,
* a JSON-Schema-shaped parameter spec derived from the function's type hints,
* a short description (the docstring's summary line).

The OpenAI tool-calling shape is what flows over the wire — a tool advertisement
looks like::

    {
      "type": "function",
      "function": {
        "name": "linus.knowledge.search_papers",
        "description": "Search the KnowledgeBase paper corpus.",
        "parameters": {
          "type": "object",
          "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
          "required": ["query"]
        }
      }
    }

The Phase 2a server (``src/linus/server.py``) consumes :meth:`ToolRegistry.openai_specs`
to build the ``tools=[...]`` list it forwards to Ollama, and consults
:meth:`ToolRegistry.call_tool` when the model returns a ``tool_calls`` response.

Design notes
------------
- **Hand-rolled JSON-Schema, not pydantic.** Pydantic would be over-spec for v0:
  we have a small set of allowed argument types and want the schema generation to
  stay legible. If the registry grows to support nested models we should switch to
  pydantic's ``model_json_schema()``; until then a tight stdlib path is clearer.
- **Defaults make a parameter optional.** Anything without a default is ``required``;
  anything with a default is not. This matches the OpenAI/JSON-Schema convention.
- **Unknown annotations degrade to string.** A ``Path`` or custom dataclass hint
  becomes ``{"type": "string"}`` rather than raising — the model still gets *some*
  signal, and the underlying Python function can validate or convert.
- **Tool execution is synchronous.** Async tool calls land in a later item once the
  router gets real (Phase 2h+). Today's tools are KB reads; they're already fast
  and sync.
"""

from __future__ import annotations

import inspect
import json
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints

#: Closed vocabulary of network-egress postures a tool may declare at registration
#: time. Per DEC-0061 (network-policy framework):
#:
#: - ``"offline"`` — the tool never touches the network. The default for every
#:   tool unless explicitly elevated. KB reads, Ollama-routed inference, every
#:   pre-2026-05-20 tool falls here.
#: - ``"online_optional"`` — the tool prefers the network when available and
#:   degrades cleanly to a local fallback (cache / alternative offline backend
#:   / graceful ``None``) when not. Hermetic tests exercise the offline branch;
#:   integration tests exercise both. First instance: ``entity_ncbi.py``
#:   (follow-up PR).
#: - ``"online_required"`` — the tool refuses to execute when offline. Reserved
#:   for tools whose offline result would be materially misleading. None ship
#:   in this PR; the slot exists so the framework is complete from day one.
NetworkPolicy = Literal["offline", "online_optional", "online_required"]

#: The three valid values of :data:`NetworkPolicy`, exposed as a frozenset for
#: cheap membership checks in validators. Kept in sync with the Literal above.
_ALLOWED_NETWORK_POLICIES: frozenset[str] = frozenset({"offline", "online_optional", "online_required"})


class ToolError(RuntimeError):
    """Raised when a registered tool fails to execute.

    Wraps the underlying exception so the server can return a structured error
    to the model (as a ``role=tool`` message) without leaking a full traceback
    over the wire.
    """


@dataclass(frozen=True)
class ToolSpec:
    """Metadata for a single registered tool.

    The ``parameters`` field follows the JSON-Schema-for-function-calling shape
    that OpenAI's tool-calling protocol expects: an object schema with
    ``properties`` and ``required`` lists. The ``func`` is the raw Python
    callable; calling code should prefer :meth:`ToolRegistry.call_tool` rather
    than touching ``func`` directly so coercion and error handling stay
    consistent.

    The ``network_policy`` field declares whether the tool may use the network
    per DEC-0061. Defaults to ``"offline"`` so every pre-existing registration
    keeps its semantics with zero change. The value is one of the three
    :data:`NetworkPolicy` literals; the registry validates the value at
    registration time so an invalid string cannot land in a ToolSpec.
    """

    name: str
    description: str
    parameters: dict[str, Any]
    func: Callable[..., Any]
    network_policy: NetworkPolicy = "offline"

    def to_openai(self) -> dict[str, Any]:
        """Return the OpenAI-format ``{"type": "function", "function": {...}}`` entry.

        This is what gets forwarded to Ollama (or any OpenAI-compatible
        worker) inside the request's ``tools`` array.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


# --- type-hint → JSON-Schema mapping ----------------------------------------


_SIMPLE_TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}


def _annotation_to_schema(annotation: Any) -> dict[str, Any]:
    """Best-effort translation of a single Python annotation into JSON-Schema.

    Recognized shapes:

    * Simple primitives (``str``, ``int``, ``float``, ``bool``).
    * Optional / ``T | None`` — the schema for ``T`` is returned (``None`` is
      modeled by absence + ``required`` semantics, not by a schema branch).
    * ``list[X]`` — ``{"type": "array", "items": <schema(X)>}``.
    * ``dict[str, X]`` — ``{"type": "object", "additionalProperties": <schema(X)>}``.
    * ``Any`` or unrecognized — degrades to ``{"type": "string"}`` so the model
      still has a hint to follow.
    """
    if annotation is inspect.Parameter.empty:
        return {"type": "string"}

    # Handle Optional[X] / X | None by unwrapping the None branch.
    origin = get_origin(annotation)
    if origin is Union or _is_union_type(annotation):
        non_none = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(non_none) == 1:
            return _annotation_to_schema(non_none[0])
        # Multi-type union: fall back to string so we don't lie about the schema.
        return {"type": "string"}

    if annotation in _SIMPLE_TYPE_MAP:
        return {"type": _SIMPLE_TYPE_MAP[annotation]}

    if origin in (list, tuple):
        args = get_args(annotation)
        item_schema = _annotation_to_schema(args[0]) if args else {"type": "string"}
        return {"type": "array", "items": item_schema}

    if origin is dict:
        args = get_args(annotation)
        value_schema = _annotation_to_schema(args[1]) if len(args) == 2 else {"type": "string"}
        return {"type": "object", "additionalProperties": value_schema}

    # Catch-all — string is the most permissive JSON-Schema type.
    return {"type": "string"}


def _is_union_type(annotation: Any) -> bool:
    """Detect PEP 604 ``X | Y`` unions in addition to ``typing.Union[X, Y]``."""
    # ``int | None`` produces a ``types.UnionType`` whose origin is not ``Union``.
    import types

    return isinstance(annotation, types.UnionType)


def _build_parameters_schema(func: Callable[..., Any]) -> dict[str, Any]:
    """Derive a JSON-Schema-shaped ``parameters`` dict from a callable.

    Walks ``inspect.signature(func).parameters``; each parameter contributes a
    ``properties`` entry keyed by its name. Parameters without a default land
    in ``required``. ``self`` / ``cls`` are skipped (the registry only stores
    free functions, but be tolerant).

    Type hints are resolved via :func:`typing.get_type_hints` so this works
    correctly under ``from __future__ import annotations`` (PEP 563), where
    ``inspect.signature`` would otherwise hand back string forms like ``"int"``
    that don't compare ``is int``.
    """
    sig = inspect.signature(func)

    # Resolve string-form annotations to real types. ``include_extras=False``
    # because we don't model ``Annotated[...]`` metadata at the schema layer.
    try:
        hints = get_type_hints(func, include_extras=False)
    except Exception:
        # ``get_type_hints`` can fail on forward-refs that don't resolve in the
        # function's namespace (rare). Fall back to the raw annotations so we
        # still produce a schema, even if everything degrades to "string".
        hints = {}

    properties: dict[str, Any] = {}
    required: list[str] = []

    for name, param in sig.parameters.items():
        if name in ("self", "cls"):
            continue
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            # *args / **kwargs are not modeled in JSON-Schema; skip.
            continue

        annotation = hints.get(name, param.annotation)
        schema = _annotation_to_schema(annotation)
        if param.default is not inspect.Parameter.empty and param.default is not None:
            schema["default"] = param.default
        properties[name] = schema

        if param.default is inspect.Parameter.empty:
            required.append(name)

    out: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        out["required"] = required
    return out


def _summary_line(func: Callable[..., Any]) -> str:
    """Return the docstring summary line (first non-empty line), or a fallback."""
    doc = inspect.getdoc(func) or ""
    for line in doc.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return f"Tool {func.__name__}"


# --- registry ---------------------------------------------------------------


@dataclass
class ToolRegistry:
    """A small dict-of-tools.

    Use :meth:`register` to add a tool directly, or the :func:`tool` decorator
    for declarative registration. :meth:`call_tool` looks a tool up by name and
    invokes it with a JSON-shaped argument mapping (the format the model
    returns inside ``tool_calls``).

    The registry is intentionally NOT thread-locked — Phase 2a is single-process
    and tools are registered at import time, not dynamically. If we move to
    dynamic registration we'll add a lock.
    """

    _tools: dict[str, ToolSpec] = field(default_factory=dict)

    # --- registration --------------------------------------------------------

    def register(
        self,
        func: Callable[..., Any],
        *,
        name: str | None = None,
        description: str | None = None,
        parameters: dict[str, Any] | None = None,
        replace: bool = False,
        network_policy: NetworkPolicy = "offline",
    ) -> ToolSpec:
        """Register ``func`` under ``name`` (defaults to fully-qualified ``module.func``).

        Parameters
        ----------
        func:
            The Python callable to register.
        name:
            Override the tool name. Defaults to ``"<module>.<qualname>"``,
            which produces ``"linus.knowledge.search_papers"`` for the KB
            helpers — the dotted-namespace form the OpenAI tool-calling spec
            and our own audit log both prefer.
        description:
            Override the description. Defaults to the docstring summary line.
        parameters:
            Override the JSON-Schema parameters dict. Defaults to the auto-
            derived schema from type hints.
        replace:
            If True, silently overwrite an existing tool with the same name.
            Default False raises a :class:`ValueError` on collision — this is
            usually what you want because silent re-registration is a footgun.
        network_policy:
            Per DEC-0061. One of ``"offline"`` (default; never touches the
            network), ``"online_optional"`` (uses the network when available,
            falls back to a local backend / cache / graceful None when not),
            or ``"online_required"`` (refuses to execute when offline).
            Validated at registration time; an invalid value raises
            :class:`ValueError` so typos cannot ship silently. Surfaced via
            :attr:`ToolSpec.network_policy` for the audit log and
            :func:`~linus.server._compute_degradations` to consult.
        """
        if network_policy not in _ALLOWED_NETWORK_POLICIES:
            raise ValueError(
                f"network_policy must be one of {sorted(_ALLOWED_NETWORK_POLICIES)}, got {network_policy!r}"
            )

        if name is None:
            module = func.__module__.split(".")[0]
            # Use ``__qualname__`` so nested helpers register with a sensible
            # name; fall back to ``__name__`` for plain functions.
            short = getattr(func, "__qualname__", None) or func.__name__
            name = f"{module}.{short}".replace(".<locals>.", ".")

        if name in self._tools and not replace:
            raise ValueError(f"Tool {name!r} is already registered. Pass replace=True to override.")

        spec = ToolSpec(
            name=name,
            description=description or _summary_line(func),
            parameters=parameters or _build_parameters_schema(func),
            func=func,
            network_policy=network_policy,
        )
        self._tools[name] = spec
        return spec

    def unregister(self, name: str) -> None:
        """Remove a tool by name. No-op if the tool isn't present."""
        self._tools.pop(name, None)

    def clear(self) -> None:
        """Remove every registered tool. Mainly useful in tests."""
        self._tools.clear()

    # --- lookup --------------------------------------------------------------

    def get(self, name: str) -> ToolSpec | None:
        """Return the :class:`ToolSpec` for ``name`` or ``None`` if absent."""
        return self._tools.get(name)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __iter__(self) -> Iterator[ToolSpec]:
        return iter(self._tools.values())

    def __len__(self) -> int:
        return len(self._tools)

    def names(self) -> list[str]:
        """Return the sorted list of registered tool names."""
        return sorted(self._tools)

    def openai_specs(self) -> list[dict[str, Any]]:
        """Return all registered tools in OpenAI ``tools`` array format.

        Sort order is stable (by tool name) so the model sees a deterministic
        advertisement.
        """
        return [self._tools[name].to_openai() for name in sorted(self._tools)]

    # --- execution -----------------------------------------------------------

    def call_tool(self, name: str, arguments: dict[str, Any] | str | None) -> Any:
        """Invoke a registered tool with model-supplied arguments.

        The OpenAI tool-calling format gives ``arguments`` as a JSON string; some
        servers (Ollama included) deserialize it to a dict before handing it back.
        We accept either form here. ``None`` / empty string is treated as an
        empty argument dict.

        Raises :class:`KeyError` if the tool isn't registered, and
        :class:`ToolError` if execution fails or the JSON arguments don't parse.
        """
        spec = self._tools.get(name)
        if spec is None:
            raise KeyError(f"No tool registered under {name!r}")

        if arguments is None or arguments == "":
            kwargs: dict[str, Any] = {}
        elif isinstance(arguments, str):
            try:
                kwargs = json.loads(arguments)
            except json.JSONDecodeError as exc:
                raise ToolError(f"Tool {name!r} arguments were not valid JSON: {exc}") from exc
            if not isinstance(kwargs, dict):
                raise ToolError(f"Tool {name!r} arguments must decode to an object, got {type(kwargs).__name__}")
        elif isinstance(arguments, dict):
            kwargs = dict(arguments)
        else:
            raise ToolError(f"Tool {name!r} arguments must be dict or JSON string, got {type(arguments).__name__}")

        try:
            return spec.func(**kwargs)
        except TypeError as exc:
            # Most often: model emitted an unexpected kwarg or omitted a required one.
            raise ToolError(f"Tool {name!r} rejected arguments {list(kwargs)}: {exc}") from exc
        except Exception as exc:  # Tool-internal failure (e.g. KB unavailable)
            raise ToolError(f"Tool {name!r} raised {type(exc).__name__}: {exc}") from exc


# --- module-level default registry ------------------------------------------


default_registry = ToolRegistry()
"""Shared :class:`ToolRegistry` used by ``@tool`` (when no explicit registry is
passed) and by the FastAPI server. Importing :mod:`linus.tools` populates this
with the KB-backed tools defined in :mod:`linus.tools.kb_tools`."""


def tool(
    func: Callable[..., Any] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    parameters: dict[str, Any] | None = None,
    registry: ToolRegistry | None = None,
    network_policy: NetworkPolicy = "offline",
) -> Callable[..., Any]:
    """Register a function as a tool. Usable bare or with arguments.

    ::

        @tool
        def search_papers(query: str, limit: int = 5) -> list[dict]:
            \"\"\"Search the KnowledgeBase corpus.\"\"\"
            ...

        @tool(name="linus.kb.search_papers")
        def search(query: str) -> list[dict]:
            ...

        @tool(name="entity.ncbi", network_policy="online_optional")
        def lookup_entity(symbol: str) -> dict | None:
            \"\"\"Resolve a gene symbol against NCBI when reachable; stub otherwise.\"\"\"
            ...

    The decorator returns the original function unchanged — registration is a
    side effect — so callers can still invoke the function directly.

    Parameters
    ----------
    name, description, parameters:
        Overrides forwarded to :meth:`ToolRegistry.register`.
    registry:
        Target registry. Defaults to the module-level :data:`default_registry`.
    network_policy:
        Per DEC-0061. Default ``"offline"``; see :meth:`ToolRegistry.register`.
        Invalid values raise :class:`ValueError` at decoration time.
    """
    target = registry if registry is not None else default_registry

    def _decorate(f: Callable[..., Any]) -> Callable[..., Any]:
        target.register(
            f,
            name=name,
            description=description,
            parameters=parameters,
            network_policy=network_policy,
        )
        return f

    # Support bare ``@tool`` (without parentheses) as well as ``@tool(...)``.
    if func is not None and callable(func):
        return _decorate(func)
    return _decorate
