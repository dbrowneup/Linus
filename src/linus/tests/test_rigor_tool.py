"""Tests for the ``rigor.check`` tool registration + invocation route.

The rigor grounding gate (DEC-0059) ships with two surfaces wired into
the Linus orchestration backend by the same PR:

1. An auto-gate on :func:`linus.knowledge.paperqa.LinusPaperQA.answer`
   that augments every answer payload with a ``rigor`` field
   (covered in :mod:`test_paperqa`).
2. A registered tool ``rigor.check`` callable via the existing
   ``POST /v1/tools/{tool_name}/invoke`` route (covered here).

These tests verify the tool surface: the registration is present on the
default registry with the documented schema, and the route returns the
documented envelope for both success and validation-error cases. The
backend resolution inside the tool is monkey-patched to a hermetic
fake so the suite stays free of the KB submodule + paper-qa
installation.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from linus.server import app
from linus.tools import default_registry


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# ── registration shape ────────────────────────────────────────────────────


def test_rigor_check_is_registered_on_default_registry() -> None:
    """``rigor.check`` is present on the module-level :data:`default_registry`."""
    # Importing :mod:`linus.tools` (done at module level via the server
    # import) runs the registration decorator. We assert the name is
    # there rather than reaching into the underlying callable so the
    # test is decoupled from the helper's signature.
    assert "rigor.check" in default_registry.names()


def test_rigor_check_schema_advertises_claim_argument() -> None:
    """The advertised schema requires ``claim`` and offers two boolean toggles."""
    spec = default_registry.get("rigor.check")
    assert spec is not None
    params = spec.parameters
    assert params["type"] == "object"
    # ``claim`` is a dict; the registry maps that to a JSON-Schema object.
    assert params["properties"]["claim"]["type"] == "object"
    # The two boolean toggles default-True, so they're NOT in ``required``.
    assert "use_kb_paper_lookup" in params["properties"]
    assert params["properties"]["use_kb_paper_lookup"]["type"] == "boolean"
    assert params["properties"]["use_kb_paper_lookup"].get("default") is True
    assert "use_entity_lookup" in params["properties"]
    assert params["properties"]["use_entity_lookup"]["type"] == "boolean"
    # Only ``claim`` is required.
    assert params.get("required") == ["claim"]


def test_rigor_check_description_documents_purpose() -> None:
    """The advertised description carries the grounding-gate framing."""
    spec = default_registry.get("rigor.check")
    assert spec is not None
    assert "grounding gate" in spec.description.lower()


# ── happy path via the invoke route ───────────────────────────────────────


class _FakeKBPaper:
    """Minimal paper row used by the rigor citation check."""

    def __init__(self, page_count: int) -> None:
        self.page_count = page_count


class _FakeKBAdapter:
    """Stand-in for :class:`KnowledgeBaseAdapter` used in hermetic tests."""

    def __init__(self, papers: dict[str, int]) -> None:
        self._papers = papers

    def get_paper(self, paper_id: str) -> _FakeKBPaper | None:
        if paper_id not in self._papers:
            return None
        return _FakeKBPaper(page_count=self._papers[paper_id])


def _patch_rigor_backends(monkeypatch: pytest.MonkeyPatch, paper_map: dict[str, int]) -> None:
    """Wire :func:`_resolve_paper_backend` to a fake KB for the duration of the test."""
    from linus.knowledge.paperqa import _adapter_to_paper_lookup

    def _fake_paper_backend() -> Any:
        return _adapter_to_paper_lookup(_FakeKBAdapter(paper_map))

    monkeypatch.setattr(
        "linus.knowledge.paperqa._resolve_paper_backend",
        _fake_paper_backend,
    )


def test_invoke_rigor_check_happy_path(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """A valid claim returns 200 with the documented :func:`result_to_dict` shape."""
    _patch_rigor_backends(monkeypatch, paper_map={"sha_a": 10})

    claim = {
        "rationale": "X causes Y per Smith2024.",
        "citations": [
            {"paper_id": "sha_a", "page": 3, "excerpt": "...", "score": 0.9},
        ],
        "entities": [],
        "confidence": 0.8,
    }

    resp = client.post(
        "/v1/tools/rigor.check/invoke",
        json={"arguments": {"claim": claim}},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["tool"] == "rigor.check"

    result = body["result"]
    assert isinstance(result["passed"], bool)
    assert result["passed"] is True
    assert isinstance(result["failures"], list)
    assert result["error_count"] == 0


def test_invoke_rigor_check_surfaces_unresolved_citation(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """A claim citing a paper not in the KB surfaces ``unresolved_citation``."""
    _patch_rigor_backends(monkeypatch, paper_map={})

    claim = {
        "rationale": "X causes Y per Ghost2024.",
        "citations": [
            {"paper_id": "sha_missing", "page": 1, "excerpt": "..."},
        ],
        "entities": [],
    }
    resp = client.post(
        "/v1/tools/rigor.check/invoke",
        json={"arguments": {"claim": claim}},
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()["result"]
    assert result["passed"] is False
    kinds = {f["kind"] for f in result["failures"]}
    assert "unresolved_citation" in kinds


# ── validation error path ────────────────────────────────────────────────


def test_invoke_rigor_check_missing_claim_returns_422(client: TestClient) -> None:
    """Calling the route without the required ``claim`` arg returns 422."""
    resp = client.post(
        "/v1/tools/rigor.check/invoke",
        json={"arguments": {}},
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert "missing required arguments" in detail
    assert "claim" in detail


def test_invoke_rigor_check_disable_paper_lookup_passes_with_warning(
    client: TestClient,
) -> None:
    """``use_kb_paper_lookup=False`` skips citation grounding cleanly.

    With both backends disabled the gate has nothing to validate and
    surfaces ``backend_unavailable`` warnings — the answer still passes.
    This exercises the optional-kwarg path through the JSON envelope.
    """
    claim = {
        "rationale": "trivial",
        "citations": [],
        "entities": [],
    }
    resp = client.post(
        "/v1/tools/rigor.check/invoke",
        json={
            "arguments": {
                "claim": claim,
                "use_kb_paper_lookup": False,
                "use_entity_lookup": False,
            }
        },
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()["result"]
    assert result["passed"] is True
    kinds = {f["kind"] for f in result["failures"]}
    # Both backends absent → two ``backend_unavailable`` warnings.
    assert "backend_unavailable" in kinds
