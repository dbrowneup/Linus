"""Tests for :mod:`linus.tools.registry` — the model-facing tool dispatch surface.

The registry is how Linus exposes callable functions to the model: a tool is
*registered* (decorator or explicit ``ToolRegistry.register``), *advertised*
as an OpenAI-format JSON-Schema entry, and *dispatched* by name with a
JSON-shaped argument mapping. Every one of those paths must be exercised so
regressions in the schema generation or the dispatch error surface get caught
hermetically rather than only at integration time when a real model emits a
weird ``tool_calls`` shape.

The suite is fully hermetic — pure in-process Python, no Ollama, no network,
no filesystem touch beyond what pytest provides.
"""

from __future__ import annotations

from typing import Any, Optional, Union

import pytest

from linus.tools.registry import (
    _ALLOWED_NETWORK_POLICIES,
    ToolError,
    ToolRegistry,
    ToolSpec,
    _annotation_to_schema,
    _build_parameters_schema,
    _summary_line,
    default_registry,
    tool,
)

# ── _annotation_to_schema: every documented branch ─────────────────────────


def test_annotation_empty_degrades_to_string() -> None:
    """``inspect.Parameter.empty`` (no annotation) becomes ``{"type": "string"}``
    so the model still gets a usable hint (line 121)."""
    import inspect

    assert _annotation_to_schema(inspect.Parameter.empty) == {"type": "string"}


def test_annotation_simple_primitives() -> None:
    """Simple primitives map directly via ``_SIMPLE_TYPE_MAP``."""
    assert _annotation_to_schema(str) == {"type": "string"}
    assert _annotation_to_schema(int) == {"type": "integer"}
    assert _annotation_to_schema(float) == {"type": "number"}
    assert _annotation_to_schema(bool) == {"type": "boolean"}


def test_annotation_typing_optional_unwraps_to_inner() -> None:
    """``Optional[int]`` (i.e. ``Union[int, None]``) unwraps to the schema for
    ``int`` — ``None`` is modeled by the ``required`` semantics, not as a
    schema branch (lines 126-128)."""
    assert _annotation_to_schema(Optional[int]) == {"type": "integer"}


def test_annotation_pep604_optional_unwraps_to_inner() -> None:
    """PEP 604 ``int | None`` unwraps the same way as ``typing.Optional[int]``.
    Exercises the ``_is_union_type`` branch (lines 126-128 via PEP 604)."""
    assert _annotation_to_schema(int | None) == {"type": "integer"}


def test_annotation_multi_type_union_falls_back_to_string() -> None:
    """A union with more than one non-None member can't be safely modeled as
    a single JSON-Schema branch, so we fall back to string rather than lie
    (line 130 — both ``typing.Union`` and PEP 604 ``|`` cover this)."""
    assert _annotation_to_schema(Union[int, str]) == {"type": "string"}
    assert _annotation_to_schema(int | str) == {"type": "string"}


def test_annotation_list_of_primitive() -> None:
    """``list[X]`` becomes an array schema with the inner type's schema as
    ``items`` (lines 135-138)."""
    assert _annotation_to_schema(list[int]) == {
        "type": "array",
        "items": {"type": "integer"},
    }


def test_annotation_bare_list_defaults_items_to_string() -> None:
    """``list`` without a parameter has no get_args() entries; items
    degrades to string (lines 135-137 fallback branch)."""
    # ``list`` as an annotation has origin ``list`` and no args.
    assert _annotation_to_schema(list) == {"type": "string"}
    # parameterized but exercise the tuple branch too
    assert _annotation_to_schema(tuple[str, ...]) == {
        "type": "array",
        "items": {"type": "string"},
    }


def test_annotation_dict_of_string_to_int() -> None:
    """``dict[str, int]`` becomes an object schema whose
    ``additionalProperties`` matches the value type (lines 140-143)."""
    assert _annotation_to_schema(dict[str, int]) == {
        "type": "object",
        "additionalProperties": {"type": "integer"},
    }


def test_annotation_bare_dict_defaults_values_to_string() -> None:
    """``dict`` without parameters (no get_args output) falls back to string
    values (lines 140-142 fallback branch)."""
    assert _annotation_to_schema(dict) == {"type": "string"}


def test_annotation_unknown_falls_back_to_string() -> None:
    """An unrecognized annotation (e.g. ``Path`` or a custom dataclass)
    degrades to ``{"type": "string"}`` rather than raising (line 146)."""
    from pathlib import Path

    assert _annotation_to_schema(Path) == {"type": "string"}

    class Custom:
        pass

    assert _annotation_to_schema(Custom) == {"type": "string"}


# ── _build_parameters_schema: structural cases ─────────────────────────────


def test_build_parameters_schema_basic_required_and_optional() -> None:
    """A function with one required + one defaulted parameter generates the
    expected ``properties`` map and minimal ``required`` list."""

    def fn(query: str, limit: int = 5) -> list[str]:
        return []

    schema = _build_parameters_schema(fn)
    assert schema["type"] == "object"
    assert schema["properties"]["query"] == {"type": "string"}
    assert schema["properties"]["limit"]["type"] == "integer"
    assert schema["properties"]["limit"]["default"] == 5
    assert schema["required"] == ["query"]


def test_build_parameters_schema_no_required_omits_required_key() -> None:
    """When every parameter has a default, the ``required`` key is omitted
    entirely (cleaner JSON-Schema output)."""

    def fn(limit: int = 5, offset: int = 0) -> None:
        return None

    schema = _build_parameters_schema(fn)
    assert "required" not in schema


def test_build_parameters_schema_skips_self_and_cls() -> None:
    """Method-style ``self`` / ``cls`` parameters are not exposed to the
    model (line 187)."""

    class C:
        def method(self, x: int) -> int:
            return x

        @classmethod
        def klass(cls, y: str) -> str:
            return y

    schema_method = _build_parameters_schema(C.method)
    assert "self" not in schema_method["properties"]
    assert "x" in schema_method["properties"]

    schema_class = _build_parameters_schema(C.klass)
    assert "cls" not in schema_class["properties"]
    assert "y" in schema_class["properties"]


def test_build_parameters_schema_skips_var_args_and_var_kwargs() -> None:
    """``*args`` / ``**kwargs`` cannot be modeled in JSON-Schema; they're
    silently dropped (line 190)."""

    def fn(x: int, *args: Any, **kwargs: Any) -> None:
        return None

    schema = _build_parameters_schema(fn)
    assert list(schema["properties"]) == ["x"]


def test_build_parameters_schema_none_default_is_not_serialized() -> None:
    """A default of literal ``None`` should mark the parameter as optional
    but NOT serialize ``"default": None`` into the schema (line 194 branch:
    ``param.default is not None``)."""

    def fn(x: int = None) -> None:  # type: ignore[assignment]
        return None

    schema = _build_parameters_schema(fn)
    # x is optional (not in required) because it has a default...
    assert "required" not in schema
    # ... but its schema entry does not carry a ``default`` key.
    assert "default" not in schema["properties"]["x"]


def test_build_parameters_schema_get_type_hints_failure_falls_back() -> None:
    """When ``typing.get_type_hints`` raises on an unresolvable forward-ref,
    the builder falls back to raw annotations rather than crashing
    (lines 176-180). Easiest reproducer: a function whose annotation cites a
    name that doesn't resolve in either local or module globals."""
    # Inject a function whose annotation references a name that won't resolve
    # via get_type_hints. We use ``exec`` so the source string sees no enclosing
    # binding of ``Mystery`` at evaluation time.
    ns: dict[str, Any] = {}
    exec(
        "def fn(x: 'Mystery') -> None:\n    return None\n",
        ns,
    )
    fn = ns["fn"]

    schema = _build_parameters_schema(fn)
    # Falls back: annotation is the string "Mystery", so _annotation_to_schema
    # is invoked on the str and degrades to {"type": "string"}.
    assert schema["properties"]["x"] == {"type": "string"}


# ── _summary_line: docstring extraction ────────────────────────────────────


def test_summary_line_returns_first_nonempty_line() -> None:
    """The first non-empty line of the docstring is the summary."""

    def fn() -> None:
        """First line summary.

        Second paragraph that should not appear.
        """

    assert _summary_line(fn) == "First line summary."


def test_summary_line_skips_leading_blank_lines() -> None:
    """Docstrings sometimes start with a blank line (``\"\"\"\\nReal text\\n\"\"\"``);
    the first *non-empty* line wins after strip()."""

    def fn() -> None:
        """
        Real content here.
        """

    assert _summary_line(fn) == "Real content here."


def test_summary_line_no_docstring_uses_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """When ``inspect.getdoc`` returns an empty string, the fallback is
    ``"Tool <funcname>"`` (line 214)."""

    def fn() -> None:
        return None

    # fn has no docstring → getdoc returns None → "" → fallback
    assert _summary_line(fn) == "Tool fn"


# ── ToolSpec dataclass behavior ────────────────────────────────────────────


def test_toolspec_to_openai_returns_function_envelope() -> None:
    """A ToolSpec serializes to the OpenAI ``{"type": "function", ...}``
    envelope with name / description / parameters in the inner dict."""

    def fn(q: str) -> str:
        return q

    spec = ToolSpec(
        name="t.echo",
        description="Echo a query.",
        parameters={"type": "object", "properties": {"q": {"type": "string"}}},
        func=fn,
    )
    envelope = spec.to_openai()
    assert envelope["type"] == "function"
    assert envelope["function"]["name"] == "t.echo"
    assert envelope["function"]["description"] == "Echo a query."
    assert envelope["function"]["parameters"]["properties"]["q"]["type"] == "string"


def test_toolspec_is_frozen_dataclass() -> None:
    """``ToolSpec`` is frozen so callers can't mutate registry entries
    in place — important for the "tools are registered at import time"
    no-locks design."""

    def fn() -> None:
        return None

    spec = ToolSpec(name="t.x", description="d", parameters={}, func=fn)
    with pytest.raises(Exception):  # FrozenInstanceError, but be tolerant
        spec.name = "t.y"  # type: ignore[misc]


# ── ToolRegistry: registration ─────────────────────────────────────────────


def test_register_with_explicit_name_stores_spec() -> None:
    """The basic ``register`` path: explicit name + auto-derived schema."""
    reg = ToolRegistry()

    def fn(query: str) -> str:
        """Search."""
        return query

    spec = reg.register(fn, name="mytool.search")
    assert isinstance(spec, ToolSpec)
    assert spec.name == "mytool.search"
    assert spec.description == "Search."
    assert "query" in spec.parameters["properties"]
    assert "mytool.search" in reg


def test_register_derives_name_from_module_and_qualname() -> None:
    """Without an explicit ``name``, the registry derives
    ``"<top-module>.<qualname>"`` (lines 269-273). For functions defined at
    module top-level, this is ``"<package>.<funcname>"``."""
    reg = ToolRegistry()

    def fn(x: int) -> int:
        """A tool."""
        return x

    spec = reg.register(fn)
    # ``fn`` lives in this test module. ``__module__.split(".")[0]`` is the
    # top-level package; for ``src.linus.tests.test_registry`` that's "src",
    # or for direct ``linus.tests.test_registry`` it's "linus". Either way,
    # the derived name ends with ".fn" because qualname is "fn" (no .<locals>
    # because we're at module scope per pytest's collection model... actually
    # pytest collects functions defined inside test functions as nested, so
    # qualname will contain ".<locals>.fn", which the implementation strips).
    assert spec.name.endswith(".fn")
    # ".<locals>." must be stripped per the contract.
    assert ".<locals>." not in spec.name


def test_register_strips_locals_qualifier_from_nested_funcs() -> None:
    """Functions defined inside another function have qualname like
    ``outer.<locals>.inner``. The registry strips ``.<locals>.`` so the tool
    name reads cleanly (line 273)."""
    reg = ToolRegistry()

    def make_fn():
        def inner(x: int) -> int:
            """Inner doc."""
            return x

        return inner

    spec = reg.register(make_fn())
    assert ".<locals>." not in spec.name
    # The name should contain "make_fn.inner" after the strip.
    assert "make_fn.inner" in spec.name


def test_register_duplicate_raises_value_error_by_default() -> None:
    """Re-registering an existing name without ``replace=True`` raises
    ``ValueError`` (line 276) — silent re-registration is a footgun."""
    reg = ToolRegistry()

    def fn() -> None:
        return None

    reg.register(fn, name="t.x")
    with pytest.raises(ValueError, match="already registered"):
        reg.register(fn, name="t.x")


def test_register_duplicate_with_replace_overrides() -> None:
    """``replace=True`` silently overwrites the existing tool — the override
    path that the duplicate-check guards."""
    reg = ToolRegistry()

    def fn_a() -> str:
        return "a"

    def fn_b() -> str:
        return "b"

    reg.register(fn_a, name="t.x")
    reg.register(fn_b, name="t.x", replace=True)
    assert reg.get("t.x").func is fn_b


def test_register_with_explicit_description_and_parameters_overrides() -> None:
    """Explicit ``description`` and ``parameters`` win over the auto-derived
    docstring summary and JSON-Schema."""
    reg = ToolRegistry()

    def fn(q: str) -> str:
        """Auto-derived summary."""
        return q

    custom_params = {
        "type": "object",
        "properties": {"q": {"type": "string"}},
        "required": ["q"],
    }
    spec = reg.register(
        fn,
        name="t.custom",
        description="Custom description.",
        parameters=custom_params,
    )
    assert spec.description == "Custom description."
    assert spec.parameters is custom_params


# ── ToolRegistry: unregister / clear / lookup / iteration ──────────────────


def test_unregister_removes_existing_tool() -> None:
    """``unregister`` removes the named tool from the registry."""
    reg = ToolRegistry()

    def fn() -> None:
        return None

    reg.register(fn, name="t.x")
    assert "t.x" in reg
    reg.unregister("t.x")
    assert "t.x" not in reg


def test_unregister_missing_name_is_noop() -> None:
    """``unregister`` of a name that isn't registered must not raise
    (line 291: ``dict.pop(name, None)``)."""
    reg = ToolRegistry()
    # Should not raise.
    reg.unregister("nonexistent.tool")
    assert len(reg) == 0


def test_clear_removes_all_tools() -> None:
    """``clear`` empties the registry (line 295)."""
    reg = ToolRegistry()

    def a() -> None:
        return None

    def b() -> None:
        return None

    reg.register(a, name="t.a")
    reg.register(b, name="t.b")
    assert len(reg) == 2

    reg.clear()
    assert len(reg) == 0
    assert reg.names() == []


def test_get_returns_spec_or_none() -> None:
    """``get`` returns the ToolSpec for known names, ``None`` for missing."""
    reg = ToolRegistry()

    def fn() -> None:
        return None

    reg.register(fn, name="t.x")
    spec = reg.get("t.x")
    assert spec is not None
    assert spec.name == "t.x"

    assert reg.get("does.not.exist") is None


def test_contains_works_for_present_and_absent_names() -> None:
    """``in`` operator delegates to ``__contains__`` (line 304)."""
    reg = ToolRegistry()

    def fn() -> None:
        return None

    reg.register(fn, name="t.x")
    assert "t.x" in reg
    assert "t.y" not in reg


def test_iter_yields_toolspecs() -> None:
    """Iterating the registry yields ``ToolSpec`` instances (line 307)."""
    reg = ToolRegistry()

    def a() -> None:
        return None

    def b() -> None:
        return None

    reg.register(a, name="t.a")
    reg.register(b, name="t.b")
    specs = list(reg)
    assert all(isinstance(s, ToolSpec) for s in specs)
    assert {s.name for s in specs} == {"t.a", "t.b"}


def test_len_returns_tool_count() -> None:
    """``len(reg)`` matches the number of registered tools (line 310)."""
    reg = ToolRegistry()
    assert len(reg) == 0

    def fn() -> None:
        return None

    reg.register(fn, name="t.x")
    assert len(reg) == 1


def test_names_returns_sorted_list() -> None:
    """``names`` returns the tools in sorted order — deterministic display."""
    reg = ToolRegistry()

    def fn() -> None:
        return None

    reg.register(fn, name="t.z")
    reg.register(fn, name="t.a", replace=False)
    reg.register(fn, name="t.m", replace=False)
    assert reg.names() == ["t.a", "t.m", "t.z"]


# ── ToolRegistry: openai_specs serialization ───────────────────────────────


def test_openai_specs_sorted_and_well_shaped() -> None:
    """``openai_specs`` returns OpenAI-format function envelopes sorted by
    tool name — deterministic order for the model."""
    reg = ToolRegistry()

    def a(q: str) -> str:
        """A doc."""
        return q

    def b(n: int) -> int:
        """B doc."""
        return n

    reg.register(a, name="t.zebra")
    reg.register(b, name="t.alpha")

    specs = reg.openai_specs()
    assert [s["function"]["name"] for s in specs] == ["t.alpha", "t.zebra"]
    assert all(s["type"] == "function" for s in specs)
    assert specs[0]["function"]["parameters"]["properties"]["n"]["type"] == "integer"
    assert specs[1]["function"]["parameters"]["properties"]["q"]["type"] == "string"


def test_openai_specs_empty_registry_returns_empty_list() -> None:
    """No tools → empty list (not None)."""
    reg = ToolRegistry()
    assert reg.openai_specs() == []


# ── ToolRegistry.call_tool: every branch in the 337-371 block ──────────────


def test_call_tool_dispatches_with_dict_arguments() -> None:
    """Happy path: dict arguments unpack via ``**kwargs`` to the function."""
    reg = ToolRegistry()

    def add(a: int, b: int) -> int:
        """Sum."""
        return a + b

    reg.register(add, name="t.add")
    assert reg.call_tool("t.add", {"a": 2, "b": 3}) == 5


def test_call_tool_dispatches_with_json_string_arguments() -> None:
    """OpenAI's tool-calling format gives ``arguments`` as a JSON string;
    ``call_tool`` deserializes it before invoking the tool."""
    reg = ToolRegistry()

    def add(a: int, b: int) -> int:
        return a + b

    reg.register(add, name="t.add")
    assert reg.call_tool("t.add", '{"a": 2, "b": 3}') == 5


def test_call_tool_treats_none_as_empty_kwargs() -> None:
    """``arguments=None`` invokes the function with no arguments — useful for
    zero-arg tools."""
    reg = ToolRegistry()

    def hello() -> str:
        return "world"

    reg.register(hello, name="t.hello")
    assert reg.call_tool("t.hello", None) == "world"


def test_call_tool_treats_empty_string_as_empty_kwargs() -> None:
    """Empty string ``arguments`` is the same as ``None`` — some Ollama
    versions emit ``""`` for zero-arg tools."""
    reg = ToolRegistry()

    def hello() -> str:
        return "world"

    reg.register(hello, name="t.hello")
    assert reg.call_tool("t.hello", "") == "world"


def test_call_tool_unknown_name_raises_keyerror() -> None:
    """An unregistered tool name raises ``KeyError`` (line 339)."""
    reg = ToolRegistry()
    with pytest.raises(KeyError, match="No tool registered"):
        reg.call_tool("nope.nothing", {})


def test_call_tool_invalid_json_string_raises_toolerror() -> None:
    """Malformed JSON in the ``arguments`` string raises ``ToolError``
    wrapping the JSONDecodeError (lines 346-349)."""
    reg = ToolRegistry()

    def fn(x: int) -> int:
        return x

    reg.register(fn, name="t.x")
    with pytest.raises(ToolError, match="not valid JSON"):
        reg.call_tool("t.x", "{not json}")


def test_call_tool_json_decoding_to_non_object_raises_toolerror() -> None:
    """If the JSON decodes to something that isn't a dict (e.g. a list),
    ``ToolError`` is raised (lines 350-354)."""
    reg = ToolRegistry()

    def fn(x: int) -> int:
        return x

    reg.register(fn, name="t.x")
    with pytest.raises(ToolError, match="must decode to an object"):
        reg.call_tool("t.x", "[1, 2, 3]")


def test_call_tool_non_dict_non_str_arguments_raises_toolerror() -> None:
    """Passing a type that's neither dict nor str (e.g. an int) raises
    ``ToolError`` with a clear message (lines 358-361)."""
    reg = ToolRegistry()

    def fn(x: int) -> int:
        return x

    reg.register(fn, name="t.x")
    with pytest.raises(ToolError, match="must be dict or JSON string"):
        reg.call_tool("t.x", 42)  # type: ignore[arg-type]


def test_call_tool_typeerror_from_func_wraps_as_toolerror() -> None:
    """If the model emits the wrong kwarg names, Python raises ``TypeError``
    on ``func(**kwargs)``; the registry wraps it as ``ToolError`` (lines
    365-369)."""
    reg = ToolRegistry()

    def fn(x: int) -> int:
        return x

    reg.register(fn, name="t.x")
    # Missing required kwarg ``x``
    with pytest.raises(ToolError, match="rejected arguments"):
        reg.call_tool("t.x", {})

    # Unknown kwarg ``y``
    with pytest.raises(ToolError, match="rejected arguments"):
        reg.call_tool("t.x", {"y": 1})


def test_call_tool_internal_exception_wraps_as_toolerror() -> None:
    """Any other exception inside the tool (e.g. KB unavailable, division by
    zero) gets wrapped in ``ToolError`` with the original exception type in
    the message (lines 370-371)."""
    reg = ToolRegistry()

    def explode(x: int) -> int:
        raise RuntimeError("KB unavailable")

    reg.register(explode, name="t.boom")
    with pytest.raises(ToolError, match="raised RuntimeError"):
        reg.call_tool("t.boom", {"x": 1})


def test_call_tool_chained_exception_preserves_cause() -> None:
    """The wrapped ``ToolError`` should chain via ``raise ... from exc`` so
    the original traceback is recoverable from the ``__cause__`` attribute."""
    reg = ToolRegistry()

    def explode() -> None:
        raise ValueError("inner detail")

    reg.register(explode, name="t.boom")
    try:
        reg.call_tool("t.boom", None)
    except ToolError as exc:
        assert isinstance(exc.__cause__, ValueError)
        assert "inner detail" in str(exc.__cause__)


def test_call_tool_copies_dict_arguments() -> None:
    """``kwargs = dict(arguments)`` means mutating the caller's dict after
    dispatch does not affect (or get affected by) the registry call. Tests
    the ``dict(arguments)`` copy path on line 356."""
    reg = ToolRegistry()
    captured: dict[str, Any] = {}

    def fn(x: int) -> int:
        captured["seen"] = x
        return x

    reg.register(fn, name="t.x")
    args = {"x": 7}
    reg.call_tool("t.x", args)
    args["x"] = 999  # mutate after dispatch
    assert captured["seen"] == 7


# ── @tool decorator ────────────────────────────────────────────────────────


def test_tool_decorator_bare_form_registers_to_default_registry() -> None:
    """``@tool`` without parentheses (bare form) goes through the
    ``callable(func)`` branch (line 427)."""
    # Clean slate on the module-level default_registry to avoid clashing names
    # carried in from prior tests.
    snapshot = dict(default_registry._tools)
    try:

        @tool
        def my_bare_tool(q: str) -> str:
            """Bare-form decorator tool."""
            return q

        names = default_registry.names()
        assert any(n.endswith(".my_bare_tool") for n in names)
        # The decorator returns the original function unchanged.
        assert my_bare_tool("hi") == "hi"
    finally:
        default_registry._tools.clear()
        default_registry._tools.update(snapshot)


def test_tool_decorator_parenthesized_form_with_explicit_registry() -> None:
    """``@tool(registry=reg, name="...")`` registers to the explicit registry
    rather than the module default."""
    reg = ToolRegistry()

    @tool(name="custom.echo", registry=reg)
    def echo(s: str) -> str:
        """Echo."""
        return s

    assert "custom.echo" in reg
    assert "custom.echo" not in default_registry  # didn't leak
    assert echo("hi") == "hi"


def test_tool_decorator_parenthesized_form_no_args_uses_default_registry() -> None:
    """``@tool()`` (empty parens) still routes to ``_decorate`` and registers
    to the default registry. Exercises the ``return _decorate`` branch."""
    snapshot = dict(default_registry._tools)
    try:

        @tool()
        def my_paren_tool(x: int) -> int:
            """Paren-form decorator tool."""
            return x

        assert any(n.endswith(".my_paren_tool") for n in default_registry.names())
    finally:
        default_registry._tools.clear()
        default_registry._tools.update(snapshot)


def test_tool_decorator_forwards_description_and_parameters_overrides() -> None:
    """Explicit ``description`` / ``parameters`` on the decorator flow through
    to ``register``."""
    reg = ToolRegistry()
    custom_params = {
        "type": "object",
        "properties": {"x": {"type": "integer"}},
        "required": ["x"],
    }

    @tool(
        name="t.over",
        description="Override description.",
        parameters=custom_params,
        registry=reg,
    )
    def fn(x: int) -> int:
        """Auto doc — should be overridden."""
        return x

    spec = reg.get("t.over")
    assert spec is not None
    assert spec.description == "Override description."
    assert spec.parameters is custom_params


# ── network_policy (DEC-0061) ──────────────────────────────────────────────


def test_allowed_network_policies_set_matches_literal_vocabulary() -> None:
    """The frozenset and the Literal must stay in lock-step. If the vocabulary
    grows we want the test suite to fail loudly until both halves move
    together."""
    assert {"offline", "online_optional", "online_required"} == _ALLOWED_NETWORK_POLICIES


def test_register_defaults_network_policy_to_offline() -> None:
    """Tools registered without an explicit ``network_policy`` land as
    ``"offline"`` per DEC-0061 — the migration is invisible for existing
    tools."""
    reg = ToolRegistry()

    def fn() -> None:
        return None

    spec = reg.register(fn, name="t.offline_default")
    assert spec.network_policy == "offline"


@pytest.mark.parametrize("policy", ["offline", "online_optional", "online_required"])
def test_register_accepts_each_allowed_network_policy(policy: str) -> None:
    """All three DEC-0061 network-policy values construct cleanly via
    ``ToolRegistry.register``."""
    reg = ToolRegistry()

    def fn() -> None:
        return None

    spec = reg.register(fn, name=f"t.{policy}", network_policy=policy)  # type: ignore[arg-type]
    assert spec.network_policy == policy


def test_register_rejects_invalid_network_policy() -> None:
    """A network_policy outside the DEC-0061 vocabulary raises ValueError —
    typos cannot ship silently."""
    reg = ToolRegistry()

    def fn() -> None:
        return None

    with pytest.raises(ValueError, match="network_policy must be one of"):
        reg.register(fn, name="t.bad", network_policy="online")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="network_policy must be one of"):
        reg.register(fn, name="t.bad2", network_policy="optional")  # type: ignore[arg-type]


def test_register_invalid_network_policy_does_not_partially_register() -> None:
    """Validation runs BEFORE the duplicate-name check and BEFORE the registry
    dict insert — a rejected registration must not pollute the registry."""
    reg = ToolRegistry()

    def fn() -> None:
        return None

    with pytest.raises(ValueError):
        reg.register(fn, name="t.partial", network_policy="bogus")  # type: ignore[arg-type]
    assert "t.partial" not in reg
    assert len(reg) == 0


def test_toolspec_network_policy_default_is_offline() -> None:
    """ToolSpec constructed directly (bypassing register) also defaults to
    offline — important for any test or code that builds a spec by hand."""

    def fn() -> None:
        return None

    spec = ToolSpec(name="t.x", description="d", parameters={}, func=fn)
    assert spec.network_policy == "offline"


def test_toolspec_network_policy_is_frozen() -> None:
    """ToolSpec is a frozen dataclass; mutating network_policy in place must
    raise. Keeps the audit-of-record property: a tool's declared policy is
    fixed at registration."""

    def fn() -> None:
        return None

    spec = ToolSpec(
        name="t.x",
        description="d",
        parameters={},
        func=fn,
        network_policy="online_optional",
    )
    assert spec.network_policy == "online_optional"
    with pytest.raises(Exception):  # FrozenInstanceError
        spec.network_policy = "offline"  # type: ignore[misc]


def test_tool_decorator_accepts_network_policy() -> None:
    """The ``@tool`` decorator forwards network_policy to register, producing
    a ToolSpec whose policy matches the kwarg."""
    reg = ToolRegistry()

    @tool(name="t.ncbi", registry=reg, network_policy="online_optional")
    def lookup(symbol: str) -> str:
        """Lookup."""
        return symbol

    spec = reg.get("t.ncbi")
    assert spec is not None
    assert spec.network_policy == "online_optional"


def test_tool_decorator_defaults_network_policy_to_offline() -> None:
    """The decorator's default network_policy is "offline" — every existing
    @tool registration keeps its semantics unchanged."""
    reg = ToolRegistry()

    @tool(name="t.local", registry=reg)
    def local(q: str) -> str:
        """Local."""
        return q

    spec = reg.get("t.local")
    assert spec is not None
    assert spec.network_policy == "offline"


def test_tool_decorator_rejects_invalid_network_policy() -> None:
    """An invalid network_policy on the decorator raises ValueError at the
    moment the decorator runs (i.e. at import time of the module that
    defines the tool) — bad declarations fail loud before the registry is
    consulted."""
    reg = ToolRegistry()

    with pytest.raises(ValueError, match="network_policy must be one of"):

        @tool(name="t.bad", registry=reg, network_policy="weekly")  # type: ignore[arg-type]
        def bad() -> None:
            return None


# ── ToolError surface ──────────────────────────────────────────────────────


def test_toolerror_is_runtimeerror_subclass() -> None:
    """``ToolError`` subclasses RuntimeError so server code can catch the
    broader exception class if it wants — the structured-error wrapper is
    additive, not blocking."""
    assert issubclass(ToolError, RuntimeError)
    err = ToolError("kaboom")
    assert isinstance(err, RuntimeError)
    assert str(err) == "kaboom"
