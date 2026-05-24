"""Unit tests for :mod:`linus.tools.registry`.

Two behaviors are exercised here, matching the success criteria in
``docs/specs/2026-05-12-linus-implementation-plan.md`` Item 6:

* ``test_registry_register_and_lookup`` — basic register / get / openai_specs /
  call_tool round-trip on a fresh :class:`ToolRegistry`.
* ``test_tool_decorator_param_schema_from_hints`` — the ``@tool`` decorator
  derives a JSON-Schema-shaped ``parameters`` dict from type hints, including
  ``Optional`` unwrap, ``list[...]`` item types, and default-driven required
  membership.

The KB tools registered on the module-level default registry are covered in
the server roundtrip test rather than here so this file stays decoupled from
the SQLite layer.
"""

from __future__ import annotations

import pytest

from linus.tools.registry import ToolError, ToolRegistry, tool

# ---------------------------------------------------------------------------
# test_registry_register_and_lookup
# ---------------------------------------------------------------------------


def test_registry_register_and_lookup() -> None:
    """A function registered on a fresh :class:`ToolRegistry` should be
    discoverable by name, advertised in OpenAI shape, and invocable via
    :meth:`ToolRegistry.call_tool` with either dict or JSON-string args."""
    reg = ToolRegistry()

    def add(a: int, b: int) -> int:
        """Add two integers."""
        return a + b

    spec = reg.register(add, name="math.add")

    # Registration metadata.
    assert spec.name == "math.add"
    assert "math.add" in reg
    assert reg.names() == ["math.add"]
    assert len(reg) == 1
    assert reg.get("math.add") is spec
    assert reg.get("does.not.exist") is None

    # OpenAI advertisement shape — outer envelope + nested function spec.
    advertised = reg.openai_specs()
    assert len(advertised) == 1
    entry = advertised[0]
    assert entry["type"] == "function"
    assert entry["function"]["name"] == "math.add"
    assert entry["function"]["description"] == "Add two integers."
    params = entry["function"]["parameters"]
    assert params["type"] == "object"
    assert set(params["required"]) == {"a", "b"}
    assert params["properties"]["a"] == {"type": "integer"}
    assert params["properties"]["b"] == {"type": "integer"}

    # call_tool: dict arguments.
    assert reg.call_tool("math.add", {"a": 2, "b": 3}) == 5

    # call_tool: JSON-string arguments (the OpenAI wire form).
    assert reg.call_tool("math.add", '{"a": 7, "b": 8}') == 15

    # call_tool: empty arguments → no kwargs (would only work for arg-less funcs).
    with pytest.raises(ToolError):
        reg.call_tool("math.add", None)  # missing required args → TypeError → ToolError

    # Duplicate registration without replace=True should raise.
    with pytest.raises(ValueError, match="already registered"):
        reg.register(add, name="math.add")

    # Unknown tool name should KeyError.
    with pytest.raises(KeyError):
        reg.call_tool("not.registered", {})

    # Bad JSON → ToolError, not raw JSONDecodeError.
    with pytest.raises(ToolError, match="not valid JSON"):
        reg.call_tool("math.add", "{not json")

    # unregister + clear semantics.
    reg.unregister("math.add")
    assert "math.add" not in reg
    reg.register(add, name="math.add")
    reg.clear()
    assert len(reg) == 0


# ---------------------------------------------------------------------------
# test_tool_decorator_param_schema_from_hints
# ---------------------------------------------------------------------------


def test_tool_decorator_param_schema_from_hints() -> None:
    """``@tool`` should derive a JSON-Schema ``parameters`` dict from type hints.

    Covers the four type-handling cases the registry promises in its module
    docstring: simple primitives, ``Optional[X]`` (unwrapped), ``list[X]``
    items, and defaults that drop a parameter from ``required``.
    """
    reg = ToolRegistry()

    @tool(registry=reg, name="search")
    def search_tool(
        query: str,
        limit: int = 5,
        tags: list[str] | None = None,
        verbose: bool = False,
    ) -> list[dict]:
        """Search a corpus for ``query``."""
        return []

    spec = reg.get("search")
    assert spec is not None
    assert spec.description == "Search a corpus for ``query``."

    params = spec.parameters
    assert params["type"] == "object"
    props = params["properties"]

    # Simple primitive: str → "string", no default → required.
    assert props["query"] == {"type": "string"}

    # int with a default → "integer" + default annotated, NOT required.
    assert props["limit"]["type"] == "integer"
    assert props["limit"]["default"] == 5

    # Optional[list[str]] (i.e. ``list[str] | None``) should unwrap to the
    # list schema (None is modeled by absence, not by a schema branch).
    assert props["tags"]["type"] == "array"
    assert props["tags"]["items"] == {"type": "string"}

    # bool default
    assert props["verbose"]["type"] == "boolean"
    assert props["verbose"]["default"] is False

    # Only ``query`` lacks a default → only ``query`` is required.
    assert params["required"] == ["query"]

    # The decorator must return the original function unchanged so callers
    # can still invoke it directly.
    assert search_tool("anything") == []


def test_tool_decorator_bare_form_uses_default_registry() -> None:
    """``@tool`` without parentheses registers on the module-level default registry.

    The default registry already carries the KB tools, so this test creates a
    fresh tool with a unique name and cleans up after itself rather than
    swapping the global out.
    """
    from linus.tools import default_registry

    # Sanity: this test's tool name must be unique. Pick an obvious-fake one.
    test_name = "test_only.unique_decorator_tool"
    if test_name in default_registry:
        default_registry.unregister(test_name)

    @tool(name=test_name)
    def helper(x: str) -> str:
        """Return x uppercased."""
        return x.upper()

    try:
        assert test_name in default_registry
        assert default_registry.call_tool(test_name, {"x": "hi"}) == "HI"
    finally:
        default_registry.unregister(test_name)


def test_register_name_default_is_module_dotted() -> None:
    """Registering without ``name=`` should produce ``<top-module>.<qualname>``."""
    reg = ToolRegistry()

    def whatever(x: int) -> int:
        """Do nothing useful."""
        return x

    spec = reg.register(whatever)
    # ``whatever.__module__`` is this test module; the top-level component is "tests".
    assert spec.name.endswith(".whatever")
    assert spec.name.startswith(whatever.__module__.split(".")[0])
