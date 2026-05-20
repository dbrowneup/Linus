"""Tests for ``POST /v1/tools/{tool_name}/invoke``.

The direct tool-invocation endpoint is the structured-output side door
that lets UI surfaces (notably the Streamlit paper-qa page) get tool
results back as JSON without a chat-completion roundtrip. The endpoint
is purely additive — these tests use a monkey-patched
:data:`linus.tools.default_registry` so they don't depend on paper-qa
or any other optional dependency being installed.

Coverage targets:

- Happy path: a registered sync tool with all required args returns 200
  with the documented ``{tool, result, duration_ms}`` shape.
- Unknown tool: 404 with the available-tool list in the detail so the
  client can self-correct without a separate ``/healthz`` roundtrip.
- Missing required arg: 422 with the missing-arg names listed.
- Tool raises: 500 with ``f"tool raised: {exc_type}: {exc_msg}"`` —
  never a stack trace.
- Tool TypeError (e.g. unexpected kwarg the schema didn't catch): 422.
- Async tool: an async coroutine function is awaited correctly.
- Result-shape pass-through: nested dicts / lists serialize as JSON.

The pattern follows ``test_anthropic_compat.py`` — :class:`TestClient`
plus :func:`monkeypatch.setattr` on the module-level registry — so the
tests stay hermetic and run in well under a second.
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from linus.server import app
from linus.tools.registry import ToolRegistry


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def isolated_registry(monkeypatch: pytest.MonkeyPatch) -> ToolRegistry:
    """Replace ``linus.server.default_registry`` with a fresh empty registry.

    Tests register only the tools they need, so behavior is deterministic
    regardless of which production tools happen to be loaded into the
    module-level :data:`linus.tools.default_registry` at import time.
    """
    fresh = ToolRegistry()
    monkeypatch.setattr("linus.server.default_registry", fresh)
    return fresh


# ── Happy path ────────────────────────────────────────────────────────────


def test_invoke_sync_tool_happy_path(client: TestClient, isolated_registry: ToolRegistry) -> None:
    """A registered sync tool returns 200 with {tool, result, duration_ms}."""

    def echo(query: str, multiplier: int = 1) -> dict[str, object]:
        """Echo the query multiplied. Sync, no async bridge."""
        return {"echoed": query * multiplier, "multiplier": multiplier}

    isolated_registry.register(echo, name="testing.echo")

    resp = client.post(
        "/v1/tools/testing.echo/invoke",
        json={"arguments": {"query": "abc", "multiplier": 3}},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["tool"] == "testing.echo"
    assert body["result"] == {"echoed": "abcabcabc", "multiplier": 3}
    assert isinstance(body["duration_ms"], (int, float))
    assert body["duration_ms"] >= 0


def test_invoke_tool_returns_documented_envelope(client: TestClient, isolated_registry: ToolRegistry) -> None:
    """The response envelope has exactly the documented keys."""

    def trivial() -> str:
        """No-arg tool."""
        return "ok"

    isolated_registry.register(trivial, name="testing.trivial")

    resp = client.post("/v1/tools/testing.trivial/invoke", json={"arguments": {}})
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"tool", "result", "duration_ms"}


def test_invoke_tool_empty_arguments_default(client: TestClient, isolated_registry: ToolRegistry) -> None:
    """Body without an ``arguments`` field defaults to ``{}`` and works for no-arg tools."""

    def trivial() -> str:
        """No-arg tool."""
        return "no-args-ok"

    isolated_registry.register(trivial, name="testing.trivial")

    resp = client.post("/v1/tools/testing.trivial/invoke", json={})
    assert resp.status_code == 200, resp.text
    assert resp.json()["result"] == "no-args-ok"


# ── Unknown tool ──────────────────────────────────────────────────────────


def test_invoke_unknown_tool_returns_404(client: TestClient, isolated_registry: ToolRegistry) -> None:
    """An unregistered tool name returns 404 with the available list."""

    def visible(query: str) -> str:
        return query

    isolated_registry.register(visible, name="testing.visible")

    resp = client.post(
        "/v1/tools/testing.does-not-exist/invoke",
        json={"arguments": {}},
    )
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    assert "tool not found: testing.does-not-exist" in detail
    # The available-list must include the tool we actually registered.
    assert "testing.visible" in detail
    assert "available:" in detail


def test_invoke_unknown_tool_with_empty_registry_returns_404(
    client: TestClient, isolated_registry: ToolRegistry
) -> None:
    """With zero registered tools, the 404 still mentions an empty available list."""
    resp = client.post(
        "/v1/tools/testing.does-not-exist/invoke",
        json={"arguments": {}},
    )
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    assert "tool not found: testing.does-not-exist" in detail
    assert "available: []" in detail


# ── Missing required arg ──────────────────────────────────────────────────


def test_invoke_missing_required_arg_returns_422(client: TestClient, isolated_registry: ToolRegistry) -> None:
    """A tool whose schema declares a required arg gets a 422 when that arg is missing."""

    def needs_query(query: str, limit: int = 5) -> list[str]:
        """Search-style tool; query is required, limit has a default."""
        return [f"{query}-{limit}"]

    isolated_registry.register(needs_query, name="testing.needs_query")

    resp = client.post(
        "/v1/tools/testing.needs_query/invoke",
        json={"arguments": {"limit": 10}},  # missing 'query'
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert "missing required arguments" in detail
    assert "query" in detail


def test_invoke_missing_multiple_required_args_lists_all(client: TestClient, isolated_registry: ToolRegistry) -> None:
    """Multiple missing required args are all named in the 422 detail."""

    def two_required(a: str, b: int) -> str:
        return f"{a}-{b}"

    isolated_registry.register(two_required, name="testing.two_required")

    resp = client.post(
        "/v1/tools/testing.two_required/invoke",
        json={"arguments": {}},
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert "a" in detail and "b" in detail


def test_invoke_with_only_optional_args_succeeds(client: TestClient, isolated_registry: ToolRegistry) -> None:
    """A tool whose args are all optional accepts an empty arguments dict."""

    def all_optional(prefix: str = "P", n: int = 0) -> str:
        return f"{prefix}{n}"

    isolated_registry.register(all_optional, name="testing.all_optional")

    resp = client.post("/v1/tools/testing.all_optional/invoke", json={"arguments": {}})
    assert resp.status_code == 200
    assert resp.json()["result"] == "P0"


# ── Tool raises ───────────────────────────────────────────────────────────


def test_invoke_tool_raises_returns_500_with_structured_detail(
    client: TestClient, isolated_registry: ToolRegistry
) -> None:
    """An uncaught exception inside the tool returns 500 with type+msg, no stack."""

    def explodes(query: str) -> str:
        raise RuntimeError("synthetic boom")

    isolated_registry.register(explodes, name="testing.explodes")

    resp = client.post(
        "/v1/tools/testing.explodes/invoke",
        json={"arguments": {"query": "hi"}},
    )
    assert resp.status_code == 500
    detail = resp.json()["detail"]
    # Documented format: "tool raised: {exc_type}: {exc_msg}".
    assert detail.startswith("tool raised: RuntimeError: ")
    assert "synthetic boom" in detail
    # And critically: no Python traceback frames leaked into the body.
    assert "Traceback" not in detail
    assert 'File "' not in detail


def test_invoke_tool_raises_custom_exception_type(client: TestClient, isolated_registry: ToolRegistry) -> None:
    """The exception class name surfaces verbatim in the detail."""

    class CustomToolError(Exception):
        pass

    def raises_custom() -> None:
        raise CustomToolError("custom failure mode")

    isolated_registry.register(raises_custom, name="testing.custom_error")

    resp = client.post("/v1/tools/testing.custom_error/invoke", json={"arguments": {}})
    assert resp.status_code == 500
    assert "tool raised: CustomToolError: custom failure mode" in resp.json()["detail"]


def test_invoke_tool_type_error_returns_422(client: TestClient, isolated_registry: ToolRegistry) -> None:
    """A TypeError from the tool (e.g. unexpected kwarg) surfaces as 422, not 500.

    The schema's ``required`` check catches missing-arg cases, but Python's
    own kwarg validation is the final line — surfacing it as 422 keeps the
    client/server boundary honest: client errors are 4xx, server errors are 5xx.
    """

    def strict_kwargs(query: str) -> str:
        return query

    isolated_registry.register(strict_kwargs, name="testing.strict")

    resp = client.post(
        "/v1/tools/testing.strict/invoke",
        json={"arguments": {"query": "ok", "extra": "unexpected"}},
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert "TypeError" in detail
    assert "rejected arguments" in detail


# ── Async tool ────────────────────────────────────────────────────────────


def test_invoke_async_tool_awaits_result(client: TestClient, isolated_registry: ToolRegistry) -> None:
    """A registered async tool function is awaited and its result returned."""

    async def async_echo(query: str) -> dict[str, str]:
        """Native coroutine — the route detects this and awaits."""
        # Yield to the loop once so the await chain is exercised, not
        # just an immediately-resolving coroutine.
        await asyncio.sleep(0)
        return {"echoed": query, "via": "async"}

    isolated_registry.register(async_echo, name="testing.async_echo")

    resp = client.post(
        "/v1/tools/testing.async_echo/invoke",
        json={"arguments": {"query": "hi"}},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["tool"] == "testing.async_echo"
    assert body["result"] == {"echoed": "hi", "via": "async"}


def test_invoke_async_tool_exception_returns_500(client: TestClient, isolated_registry: ToolRegistry) -> None:
    """An async tool that raises surfaces the same 500 contract as the sync path."""

    async def async_raises() -> None:
        await asyncio.sleep(0)
        raise ValueError("async failure")

    isolated_registry.register(async_raises, name="testing.async_raises")

    resp = client.post("/v1/tools/testing.async_raises/invoke", json={"arguments": {}})
    assert resp.status_code == 500
    detail = resp.json()["detail"]
    assert "tool raised: ValueError: async failure" in detail


# ── Result shape pass-through ─────────────────────────────────────────────


def test_invoke_tool_passes_nested_result_through(client: TestClient, isolated_registry: ToolRegistry) -> None:
    """Tool results that are dicts of lists of dicts (paperqa.answer shape) round-trip cleanly."""

    def paperqa_answer_stub(query: str, max_sources: int = 10) -> dict[str, object]:
        """Mimic the paperqa.answer contract shape without importing paper-qa."""
        return {
            "question": query,
            "answer": f"Synthesized answer for {query!r}",
            "formatted_answer": "Answer with [citation]",
            "citations": [
                {
                    "paper_id": "abc123",
                    "page": 3,
                    "excerpt": "Relevant chunk.",
                    "score": 0.91,
                }
            ][:max_sources],
        }

    isolated_registry.register(paperqa_answer_stub, name="paperqa.answer")

    resp = client.post(
        "/v1/tools/paperqa.answer/invoke",
        json={"arguments": {"query": "what is X", "max_sources": 5}},
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()["result"]
    assert result["question"] == "what is X"
    assert result["answer"].startswith("Synthesized answer")
    assert len(result["citations"]) == 1
    cit = result["citations"][0]
    assert cit["paper_id"] == "abc123"
    assert cit["page"] == 3
    assert cit["score"] == 0.91


def test_invoke_tool_duration_ms_is_positive(client: TestClient, isolated_registry: ToolRegistry) -> None:
    """duration_ms is a non-negative float reflecting wall-clock spent in the tool."""

    def sleepy() -> str:
        # Spend a tiny but measurable amount of time so duration_ms > 0
        # on systems with millisecond-resolution monotonic clocks.
        import time as _time

        _time.sleep(0.005)
        return "slept"

    isolated_registry.register(sleepy, name="testing.sleepy")

    resp = client.post("/v1/tools/testing.sleepy/invoke", json={"arguments": {}})
    assert resp.status_code == 200
    duration = resp.json()["duration_ms"]
    assert duration >= 0.0
    # Generous upper bound — the test must not flake on heavily-loaded CI.
    assert duration < 5000.0


# ── Path-parameter shape ──────────────────────────────────────────────────


def test_invoke_tool_name_with_dotted_namespace(client: TestClient, isolated_registry: ToolRegistry) -> None:
    """Tool names with dots (the registry's default convention) route correctly."""

    def fn(query: str) -> str:
        return query

    isolated_registry.register(fn, name="linus.knowledge.search")

    resp = client.post(
        "/v1/tools/linus.knowledge.search/invoke",
        json={"arguments": {"query": "abc"}},
    )
    assert resp.status_code == 200
    assert resp.json()["tool"] == "linus.knowledge.search"
    assert resp.json()["result"] == "abc"
