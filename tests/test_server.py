"""Smoke test for the Phase 2a FastAPI orchestration backend.

Per CLAUDE.md and the implementation-plan spec, this is the happy-path smoke
test the success criteria call out. The intent is to fail LOUDLY (not skip)
if Ollama is unreachable or no preferred model is pulled — those are real
environment problems that should surface immediately rather than being
silently swallowed.

Run with::

    conda activate linus && pytest tests/test_server.py -v
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from linus import server
from linus.server import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_healthz_reports_ollama_and_models(client: TestClient) -> None:
    """/healthz should report that Ollama is reachable and list at least one model."""
    resp = client.get("/healthz")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "ok"
    assert body["ollama_reachable"] is True, (
        "Ollama is not reachable. Start it with `brew services start ollama` "
        "(see CLAUDE.md Known Library Quirks for port-conflict recovery)."
    )
    assert isinstance(body["models"], list)
    assert body["models"], (
        "No Ollama models are pulled locally. Pull at least one of "
        f"{server._MODEL_PREFERENCES!r} before running the smoke test "
        "(e.g. `ollama pull qwen3:8b`)."
    )


def test_root_endpoint_returns_identity_and_endpoint_map(client: TestClient) -> None:
    """GET / should return project identity + a tour of the available endpoints.

    Regression guard for the 2026-05-19 routing bug: the Streamlit UI's
    landing page reported "Unreachable" because it was hitting GET / which
    returned 404. The UI fix targets /healthz; this endpoint exists for
    anyone curl-hitting the base URL.
    """
    resp = client.get("/")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "Linus"
    assert "endpoints" in body
    # Sanity-check a few key endpoints are advertised:
    endpoints = body["endpoints"]
    assert endpoints["health"] == "GET /healthz"
    assert "openai_chat_completions" in endpoints
    assert "anthropic_messages" in endpoints


def test_chat_completions_happy_path(client: TestClient) -> None:
    """POST /v1/chat/completions returns a ChatCompletion-shaped response.

    Asks the model a tiny prompt to keep latency low. Asserts on the response
    *shape* rather than content — model outputs are non-deterministic but the
    schema is fixed.

    ``max_tokens`` is set generously (256) because qwen3:8b runs in "thinking
    mode" by default, which silently consumes tokens on internal reasoning
    before emitting visible content. A tight 16-token budget gets spent on
    thinking and ``content`` lands empty with ``finish_reason="length"`` —
    not the integration failure this test exists to surface.
    """
    payload = {
        "model": "qwen3:8b",  # may fall back to qwen2.5-coder:7b on this box
        "messages": [
            {"role": "user", "content": "Reply with exactly the word: ack"},
        ],
        "max_tokens": 256,
    }
    resp = client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert body["object"] == "chat.completion"
    assert body["id"].startswith("chatcmpl-")
    assert isinstance(body["created"], int)
    assert isinstance(body["model"], str) and body["model"]

    assert len(body["choices"]) == 1
    choice = body["choices"][0]
    assert choice["index"] == 0
    assert choice["message"]["role"] == "assistant"
    assert isinstance(choice["message"]["content"], str)
    # The model produced *some* text. Empty content is a real failure mode.
    assert choice["message"]["content"].strip(), f"Assistant returned empty content; full response: {body!r}"

    usage = body["usage"]
    assert {"prompt_tokens", "completion_tokens", "total_tokens"} <= usage.keys()
    assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]


def test_empty_messages_rejected(client: TestClient) -> None:
    """An empty messages list is a client error (400), not a 500."""
    payload = {"model": "qwen3:8b", "messages": []}
    resp = client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 400, resp.text
    assert "messages" in resp.json()["detail"].lower()


@pytest.mark.integration
def test_tool_invoke_happy_path_against_real_registry(client: TestClient) -> None:
    """POST /v1/tools/{name}/invoke routes through the real default_registry.

    Integration-marked because it depends on the module-level
    :data:`linus.tools.default_registry` having at least one
    invocable tool registered — the production registry currently
    advertises the KB tools (``linus.knowledge.search_papers``,
    ``linus.knowledge.search_chunks``, etc.) and the four
    ``paperqa.*`` tools wired in via PR #89.

    We pick a tool we know is registered and has all-optional args:
    ``paperqa.reset`` takes zero arguments and either returns a status
    dict (paper-qa installed) or a structured 500 (paper-qa missing).
    Either outcome demonstrates that the route reached the registry
    and the registry produced an answer — what this test is here to
    verify.
    """
    available = server.default_registry.names()
    assert available, "no tools registered in default_registry — registry import broken?"

    # Prefer paperqa.reset (no required args, fast). Fall back to any
    # zero-required-arg tool if the paper-qa wiring isn't loaded.
    target = None
    for name in ["paperqa.reset", *available]:
        spec = server.default_registry.get(name)
        if spec is not None and not spec.parameters.get("required"):
            target = name
            break
    assert target is not None, f"no zero-required-arg tool found in default_registry — available: {available}"

    resp = client.post(f"/v1/tools/{target}/invoke", json={"arguments": {}})
    # Acceptable outcomes:
    # - 200: tool ran and returned a JSON result.
    # - 500: tool ran, raised, surfaced as documented structured error
    #   (e.g. PaperQAUnavailableError if paper-qa isn't pip-installed).
    assert resp.status_code in (200, 500), resp.text
    body = resp.json()
    if resp.status_code == 200:
        assert body["tool"] == target
        assert "result" in body
        assert isinstance(body["duration_ms"], (int, float))
    else:
        assert body["detail"].startswith("tool raised: ")
