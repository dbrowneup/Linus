"""Tests for the extended ``/healthz`` endpoint (Q3 loud-degradation).

Validates the ``effective_state`` + ``degradations`` payload introduced
in ``feature/q3-loud-degradation-2026-05-19``. The cross-pollination
context is Archimedes' ``/health`` — Linus's prior ``/healthz`` only
reported reachable-vs-down, so silent-fallback and missing-prerequisite
failures hid until tool invocation.

All four degradation modes are exercised in isolation plus composed,
plus the backwards-compat envelope (pre-existing keys / semantics
preserved) plus the actionable-``remediation`` contract. Ollama and the
filesystem are monkeypatched throughout; the suite is hermetic.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from linus import server as server_module
from linus.server import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def healthy_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Build a fully-healthy environment for /healthz.

    - Ollama reachable and reports the first preferred model is pulled.
    - Papers directory exists and contains at least one PDF.
    - KB artifact paths all resolve to existing files.

    Returns the papers directory (the tmp_path subtree) so individual
    tests can mutate it (e.g. delete the PDFs to trigger one degradation).
    """
    # Point paper-qa at a real directory with a PDF.
    papers_dir = tmp_path / "papers"
    papers_dir.mkdir()
    (papers_dir / "smoke.pdf").write_bytes(b"%PDF-1.4 smoke")
    monkeypatch.setenv("LINUS_PAPERQA_DIR", str(papers_dir))
    monkeypatch.delenv("LINUS_PAPERS_DIR", raising=False)

    # Build a populated KB outputs directory the artifact list points at.
    kb_root = tmp_path / "kb"
    outputs = kb_root / "outputs"
    (outputs / "graph").mkdir(parents=True)
    (outputs / "knowledge_graph").mkdir(parents=True)
    (outputs / "hierarchy.json").write_text("{}")
    (outputs / "labels_broad.json").write_text("{}")
    (outputs / "graph" / "graph_sigma.html").write_text("<html/>")
    (outputs / "knowledge_graph" / "kg_graph.graphml").write_text("<graphml/>")
    (kb_root / "metadata.db").write_bytes(b"sqlite stub")
    embeddings = kb_root / "embeddings"
    embeddings.mkdir()
    (embeddings / "specter2.npy").write_bytes(b"npy stub")

    # Stub the artifact path resolver to point at our tmp tree without
    # needing to monkey with linus.app.config's module-level Path
    # constants (which read env vars at import time).
    artifacts = [
        ("hierarchy.json", outputs / "hierarchy.json"),
        ("labels_broad.json", outputs / "labels_broad.json"),
        ("graph_sigma.html", outputs / "graph" / "graph_sigma.html"),
        ("kg_graph.graphml", outputs / "knowledge_graph" / "kg_graph.graphml"),
        ("metadata.db", kb_root / "metadata.db"),
        ("specter2.npy", embeddings / "specter2.npy"),
    ]
    monkeypatch.setattr(server_module, "_kb_artifact_paths", lambda: artifacts)

    # Default to a list-models stub that returns the first preferred
    # model. Individual tests override this.
    first_pref = server_module._MODEL_PREFERENCES[0]
    monkeypatch.setattr(server_module, "_list_local_models", lambda: [first_pref])

    return papers_dir


# ── Happy path ────────────────────────────────────────────────────────────


def test_healthz_happy_path_is_live(client: TestClient, healthy_env: Path) -> None:
    """Everything up: effective_state=live, degradations=[]."""
    resp = client.get("/healthz")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["effective_state"] == "live"
    assert body["degradations"] == []


def test_healthz_backwards_compat_keys_preserved(client: TestClient, healthy_env: Path) -> None:
    """All pre-existing /healthz keys must still be present with the same semantics."""
    resp = client.get("/healthz")
    body = resp.json()

    # Pre-existing keys.
    assert body["status"] == "ok"
    assert body["ollama_reachable"] is True
    assert isinstance(body["models"], list)
    assert server_module._MODEL_PREFERENCES[0] in body["models"]
    assert body["default_model_preference"] == list(server_module._MODEL_PREFERENCES)
    assert isinstance(body["tools"], list)

    # New keys (additive only).
    assert "effective_state" in body
    assert "degradations" in body


# ── worker_model degradation ─────────────────────────────────────────────


def _first_distinct_fallback() -> str:
    """Return the first preference distinct from ``_MODEL_PREFERENCES[0]``.

    Necessary because the preference tuple intentionally repeats the
    LINUS_DEFAULT_MODEL value at index 0 AND index 1 (see ``server.py``);
    picking ``prefs[1]`` blindly leaves the first preference satisfied.
    """
    prefs = server_module._MODEL_PREFERENCES
    first = prefs[0]
    for p in prefs[1:]:
        if p != first:
            return p
    raise AssertionError("No distinct fallback in _MODEL_PREFERENCES")


def test_healthz_worker_model_warning_when_fallback_available(
    client: TestClient, healthy_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """First preference missing, but a later preference is available → warning."""
    prefs = server_module._MODEL_PREFERENCES
    fallback = _first_distinct_fallback()
    # Offer the fallback only; ensure the first preference is absent.
    monkeypatch.setattr(server_module, "_list_local_models", lambda: [fallback])

    body = client.get("/healthz").json()

    worker_degs = [d for d in body["degradations"] if d["component"] == "worker_model"]
    assert len(worker_degs) == 1
    deg = worker_degs[0]
    assert deg["severity"] == "warning"
    assert prefs[0] in deg["expected"]
    assert fallback in deg["actual"]
    assert "ollama pull" in deg["remediation"]
    assert prefs[0] in deg["remediation"]
    # severity=warning → degraded, not down.
    assert body["effective_state"] == "degraded"


def test_healthz_worker_model_error_when_no_preference_available(
    client: TestClient, healthy_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No preferences pulled → severity=error, effective_state=down."""
    # Return one model, but not one in the preference list.
    monkeypatch.setattr(server_module, "_list_local_models", lambda: ["some-random-model:latest"])

    body = client.get("/healthz").json()

    worker_degs = [d for d in body["degradations"] if d["component"] == "worker_model"]
    assert len(worker_degs) == 1
    assert worker_degs[0]["severity"] == "error"
    assert "ollama pull" in worker_degs[0]["remediation"]
    assert body["effective_state"] == "down"


# ── ollama_models_empty degradation ───────────────────────────────────────


def test_healthz_ollama_models_empty(client: TestClient, healthy_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ollama reachable but zero models pulled → error + ollama_models_empty."""
    monkeypatch.setattr(server_module, "_list_local_models", lambda: [])

    body = client.get("/healthz").json()

    empty_degs = [d for d in body["degradations"] if d["component"] == "ollama_models_empty"]
    assert len(empty_degs) == 1
    assert empty_degs[0]["severity"] == "error"
    assert "ollama pull" in empty_degs[0]["remediation"]
    assert body["effective_state"] == "down"


# ── papers_dir degradation ───────────────────────────────────────────────


def test_healthz_papers_dir_missing(
    client: TestClient, healthy_env: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Configured papers dir does not exist → error."""
    monkeypatch.setenv("LINUS_PAPERQA_DIR", str(tmp_path / "does-not-exist"))

    body = client.get("/healthz").json()

    papers_degs = [d for d in body["degradations"] if d["component"] == "papers_dir"]
    assert len(papers_degs) == 1
    deg = papers_degs[0]
    assert deg["severity"] == "error"
    assert "does not exist" in deg["actual"]
    # Remediation must be actionable — mkdir or env-var suggestion.
    assert "mkdir" in deg["remediation"] or "LINUS_PAPERQA_DIR" in deg["remediation"]
    assert body["effective_state"] == "down"


def test_healthz_papers_dir_empty(client: TestClient, healthy_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Papers dir exists but contains zero PDFs → error."""
    # Remove the smoke PDF the fixture set up.
    for pdf in healthy_env.glob("*.pdf"):
        pdf.unlink()

    body = client.get("/healthz").json()

    papers_degs = [d for d in body["degradations"] if d["component"] == "papers_dir"]
    assert len(papers_degs) == 1
    deg = papers_degs[0]
    assert deg["severity"] == "error"
    assert "zero PDFs" in deg["actual"] or "0 PDFs" in deg["actual"] or "no PDFs" in deg["actual"].lower()
    assert deg["remediation"]
    assert body["effective_state"] == "down"


def test_healthz_papers_dir_fallback_env_var(
    client: TestClient, healthy_env: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """LINUS_PAPERS_DIR is the fallback when LINUS_PAPERQA_DIR is unset."""
    monkeypatch.delenv("LINUS_PAPERQA_DIR", raising=False)
    alt_dir = tmp_path / "alt-papers"
    alt_dir.mkdir()
    (alt_dir / "alt.pdf").write_bytes(b"%PDF stub")
    monkeypatch.setenv("LINUS_PAPERS_DIR", str(alt_dir))

    body = client.get("/healthz").json()

    # No papers_dir degradation — the fallback env var pointed at a
    # populated directory.
    assert not [d for d in body["degradations"] if d["component"] == "papers_dir"]


# ── kb_outputs degradation ───────────────────────────────────────────────


def test_healthz_kb_outputs_missing_emits_per_artifact_warnings(
    client: TestClient, healthy_env: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Missing KB artifacts → one warning per missing artifact."""
    # Re-stub artifact list to point at non-existent paths.
    fake_root = tmp_path / "no-kb"
    artifacts = [
        ("hierarchy.json", fake_root / "hierarchy.json"),
        ("labels_broad.json", fake_root / "labels_broad.json"),
        ("graph_sigma.html", fake_root / "graph" / "graph_sigma.html"),
    ]
    monkeypatch.setattr(server_module, "_kb_artifact_paths", lambda: artifacts)

    body = client.get("/healthz").json()

    kb_degs = [d for d in body["degradations"] if d["component"] == "kb_outputs"]
    assert len(kb_degs) == 3
    for d in kb_degs:
        assert d["severity"] == "warning"
        assert d["actual"] == "missing"
        assert d["remediation"]
    # All warnings, no errors → degraded.
    assert body["effective_state"] == "degraded"


def test_healthz_kb_outputs_partial_missing(
    client: TestClient, healthy_env: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Some artifacts present, some missing → one warning per missing."""
    # Two real, one fake.
    real = tmp_path / "real.json"
    real.write_text("{}")
    fake = tmp_path / "fake.json"  # not created
    artifacts = [
        ("real-a.json", real),
        ("real-b.json", real),
        ("missing.json", fake),
    ]
    monkeypatch.setattr(server_module, "_kb_artifact_paths", lambda: artifacts)

    body = client.get("/healthz").json()
    kb_degs = [d for d in body["degradations"] if d["component"] == "kb_outputs"]
    assert len(kb_degs) == 1
    assert "missing.json" in kb_degs[0]["expected"]


# ── Composition (warning + error → down) ─────────────────────────────────


def test_healthz_multiple_degradations_compose(
    client: TestClient, healthy_env: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Multiple degradations of differing severities → down."""
    # worker_model warning: fall back to a distinct preference.
    fallback = _first_distinct_fallback()
    monkeypatch.setattr(server_module, "_list_local_models", lambda: [fallback])
    # papers_dir error: missing directory.
    monkeypatch.setenv("LINUS_PAPERQA_DIR", str(tmp_path / "missing"))
    # kb_outputs warning: one missing artifact.
    monkeypatch.setattr(
        server_module,
        "_kb_artifact_paths",
        lambda: [("hierarchy.json", tmp_path / "nope.json")],
    )

    body = client.get("/healthz").json()

    components = {d["component"] for d in body["degradations"]}
    assert "worker_model" in components
    assert "papers_dir" in components
    assert "kb_outputs" in components

    # Any error → down, regardless of how many warnings sit alongside.
    assert body["effective_state"] == "down"


# ── Ollama unreachable ───────────────────────────────────────────────────


def test_healthz_ollama_unreachable_is_down(
    client: TestClient, healthy_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ollama unreachable → effective_state=down, ollama_reachable=False."""
    from fastapi import HTTPException

    def _raise(*_a, **_kw):
        raise HTTPException(status_code=503, detail="Could not reach Ollama")

    monkeypatch.setattr(server_module, "_list_local_models", _raise)

    body = client.get("/healthz").json()

    assert body["ollama_reachable"] is False
    assert body["models"] == []
    assert body["effective_state"] == "down"


# ── Remediation actionability contract ───────────────────────────────────


def test_healthz_every_degradation_has_non_empty_remediation(
    client: TestClient, healthy_env: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every emitted degradation must carry a non-empty, actionable remediation."""
    # Set up several degradations at once.
    monkeypatch.setattr(server_module, "_list_local_models", lambda: [])  # ollama_models_empty
    monkeypatch.setenv("LINUS_PAPERQA_DIR", str(tmp_path / "absent"))  # papers_dir
    monkeypatch.setattr(
        server_module,
        "_kb_artifact_paths",
        lambda: [("specter2.npy", tmp_path / "no-emb.npy")],
    )

    body = client.get("/healthz").json()

    assert body["degradations"], "expected at least one degradation"
    for d in body["degradations"]:
        assert d["remediation"], f"degradation {d['component']!r} has empty remediation"
        assert isinstance(d["remediation"], str)
        # "Actionable" heuristic: starts with a verb / contains an
        # imperative cue. The contract is informal but every emitted
        # remediation in the codebase satisfies one of these.
        lower = d["remediation"].lower()
        assert any(cue in lower for cue in ("run:", "ollama pull", "set ", "create ", "mkdir", "add ", "check ")), (
            f"degradation {d['component']!r} remediation not obviously actionable: {d['remediation']!r}"
        )


# ── Internal API: _compute_degradations directly ─────────────────────────


def test_compute_degradations_live_when_clean(healthy_env: Path) -> None:
    """``_compute_degradations`` returns (live, []) on a clean env."""
    state, degs = server_module._compute_degradations()
    assert state == "live"
    assert degs == []


def test_compute_degradations_classifies_warning_only_as_degraded(
    healthy_env: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Warning-only set classifies as 'degraded', not 'down'."""
    monkeypatch.setattr(
        server_module,
        "_kb_artifact_paths",
        lambda: [("only-missing.json", tmp_path / "absent.json")],
    )
    state, degs = server_module._compute_degradations()
    assert state == "degraded"
    assert len(degs) == 1
    assert degs[0]["severity"] == "warning"


def test_compute_degradations_error_dominates_warnings(
    healthy_env: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A single error trumps any number of warnings → down."""
    # Warning: one missing KB artifact.
    monkeypatch.setattr(
        server_module,
        "_kb_artifact_paths",
        lambda: [("missing.json", tmp_path / "absent.json")],
    )
    # Error: papers dir missing.
    monkeypatch.setenv("LINUS_PAPERQA_DIR", str(tmp_path / "no-papers"))

    state, degs = server_module._compute_degradations()
    assert state == "down"
    severities = {d["severity"] for d in degs}
    assert "warning" in severities
    assert "error" in severities


# ── Defensive branches: papers_dir glob OSError, _kb_artifact_paths import failure ──


def test_compute_degradations_papers_dir_glob_oserror(healthy_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An OSError from ``Path.glob`` surfaces as an error-severity degradation.

    Defensive branch: a permission failure on the configured papers
    directory leaves /healthz reporting a structured error with an
    actionable remediation, not crashing the endpoint.
    """
    original_glob = Path.glob

    def _raising_glob(self, pattern):
        if self == healthy_env:
            raise OSError("permission denied (synthetic)")
        return original_glob(self, pattern)

    monkeypatch.setattr(Path, "glob", _raising_glob)

    state, degs = server_module._compute_degradations()
    papers_degs = [d for d in degs if d["component"] == "papers_dir"]
    assert len(papers_degs) == 1
    deg = papers_degs[0]
    assert deg["severity"] == "error"
    assert "permission" in deg["actual"].lower() or "cannot enumerate" in deg["actual"].lower()
    assert "Check permissions" in deg["remediation"]
    assert state == "down"


# ── Helper-function direct tests (line-coverage for the resolvers) ──────


def test_resolve_papers_dir_uses_paperqa_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """LINUS_PAPERQA_DIR is honored when set."""
    monkeypatch.setenv("LINUS_PAPERQA_DIR", "/tmp/explicit-papers")
    assert server_module._resolve_papers_dir() == Path("/tmp/explicit-papers")


def test_resolve_papers_dir_falls_back_to_papers_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """LINUS_PAPERS_DIR is the fallback when LINUS_PAPERQA_DIR is unset."""
    monkeypatch.delenv("LINUS_PAPERQA_DIR", raising=False)
    monkeypatch.setenv("LINUS_PAPERS_DIR", "/tmp/shared-papers")
    assert server_module._resolve_papers_dir() == Path("/tmp/shared-papers")


def test_resolve_papers_dir_default_home_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """With no env vars set, defaults to ``~/.linus/papers/``."""
    monkeypatch.delenv("LINUS_PAPERQA_DIR", raising=False)
    monkeypatch.delenv("LINUS_PAPERS_DIR", raising=False)
    resolved = server_module._resolve_papers_dir()
    assert resolved == Path.home() / ".linus" / "papers"


def test_kb_artifact_paths_returns_canonical_six() -> None:
    """The artifact resolver returns the canonical six labels in stable order."""
    artifacts = server_module._kb_artifact_paths()
    labels = [a[0] for a in artifacts]
    assert labels == [
        "hierarchy.json",
        "labels_broad.json",
        "graph_sigma.html",
        "kg_graph.graphml",
        "metadata.db",
        "specter2.npy",
    ]
    # Each artifact carries a Path.
    for _, path in artifacts:
        assert isinstance(path, Path)


def test_compute_degradations_kb_artifact_resolver_failure_is_swallowed(
    healthy_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If ``_kb_artifact_paths`` raises (e.g. linus.app.config import error),
    /healthz must not crash — kb_outputs degradations are simply skipped."""

    def _raise(*_a, **_kw):
        raise RuntimeError("synthetic linus.app.config import failure")

    monkeypatch.setattr(server_module, "_kb_artifact_paths", _raise)

    state, degs = server_module._compute_degradations()
    # No kb_outputs entries since the resolver failed; everything else
    # still classifies normally (healthy fixture → live).
    assert not [d for d in degs if d["component"] == "kb_outputs"]
    assert state == "live"
