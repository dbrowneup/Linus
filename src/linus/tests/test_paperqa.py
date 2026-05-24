"""Hermetic tests for :mod:`linus.knowledge.paperqa`.

The suite runs without paper-qa being importable and without Ollama
running. Every paper-qa-internal call site is patched at the boundary
where the wrapper crosses into the third-party library:

- The ``paperqa.Docs``, ``paperqa.Settings``, and ``paperqa.PQASession``
  symbols are stubbed via :mod:`unittest.mock` so the lazy
  :meth:`LinusPaperQA._ensure_loaded` import succeeds against fake
  objects rather than the real paper-qa.
- Async coroutines are stubbed with ``AsyncMock``; the
  :func:`linus.knowledge.paperqa._run_async` bridge resolves them
  normally.

The four ``paperqa.*`` registered tools, the citation→provenance
mapping, the reset behavior, and the error paths are all exercised here.
This is the primary safety net for the LX-1 deliverable since the
real round-trip is gated by Ollama + a paper corpus and lives in
``tests/test_paperqa_integration.py``.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from linus.knowledge.paperqa import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_MODEL,
    DEFAULT_OLLAMA_HOST,
    LinusPaperQA,
    PaperQAConfigError,
    PaperQAUnavailableError,
    _parse_first_page,
    build_ollama_llm_config,
    citation_to_provenance,
    get_singleton,
    reset_singleton,
)
from linus.tools.registry import default_registry

# ── fake paper-qa surface ─────────────────────────────────────────────────


def _install_fake_paperqa(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    """Insert a stub ``paperqa`` module into :mod:`sys.modules`.

    The stub exposes the four names :meth:`LinusPaperQA._ensure_loaded`
    imports — ``Docs``, ``Settings``, ``PQASession`` — plus the ``Text``
    and ``Doc`` types used by some fixtures. Returns the module so
    individual tests can override attributes (e.g., to inject specific
    ``aget_evidence`` return values).
    """
    fake = types.ModuleType("paperqa")

    class FakeDocs:
        def __init__(self) -> None:
            self.cleared = False
            # ``aget_evidence`` / ``aquery`` are AsyncMock so they can be
            # awaited; each test sets the return value to a fake session.
            self.aget_evidence = AsyncMock()
            self.aquery = AsyncMock()

        def clear_docs(self) -> None:
            self.cleared = True

    class FakeSettings:
        def __init__(self, **kwargs: object) -> None:
            self.kwargs = kwargs
            # Mirror paper-qa's nested ``agent.index`` so the wrapper's
            # ``settings.agent.index.paper_directory = ...`` assignment lands.
            self.agent = types.SimpleNamespace(index=types.SimpleNamespace(paper_directory=None))

    class FakePQASession:
        def __init__(self, question: str = "") -> None:
            self.question = question
            self.answer = ""
            self.formatted_answer = ""
            self.contexts: list[object] = []

    fake.Docs = FakeDocs
    fake.Settings = FakeSettings
    fake.PQASession = FakePQASession
    monkeypatch.setitem(sys.modules, "paperqa", fake)
    return fake


def _make_context(
    *,
    paper_id: str = "doc-abc",
    docname: str = "Smith2024",
    chunk_name: str = "Smith2024 pages 3-4",
    text: str = "Raw chunk text body",
    summary: str = "Contextual summary of the chunk",
    score: int = 7,
) -> MagicMock:
    """Build a Mock that quacks like a paper-qa :class:`Context`.

    Exposes ``.text.doc.dockey``, ``.text.doc.docname``, ``.text.name``,
    ``.text.text``, ``.context``, and ``.score`` — the same attributes
    :func:`citation_to_provenance` walks.
    """
    doc = MagicMock()
    doc.dockey = paper_id
    doc.docname = docname

    text_obj = MagicMock()
    text_obj.doc = doc
    text_obj.name = chunk_name
    text_obj.text = text

    ctx = MagicMock()
    ctx.text = text_obj
    ctx.context = summary
    ctx.score = score
    return ctx


@pytest.fixture(autouse=True)
def _clear_singleton() -> None:
    """Ensure each test starts with a fresh module-level singleton."""
    reset_singleton()


# ── tool registration ─────────────────────────────────────────────────────


def test_four_paperqa_tools_register_on_default_registry() -> None:
    """All four LX-1 tools must be visible on the default registry after import."""
    # Importing the package eagerly registers the tools; re-import the
    # tools package to be safe in test-isolation scenarios.
    import linus.tools  # noqa: F401

    names = default_registry.names()
    assert "paperqa.search" in names
    assert "paperqa.gather_evidence" in names
    assert "paperqa.answer" in names
    assert "paperqa.reset" in names


def test_paperqa_search_schema_advertises_query_and_k() -> None:
    """``paperqa.search`` advertises a string ``query`` and integer ``k`` with default."""
    spec = default_registry.get("paperqa.search")
    assert spec is not None
    params = spec.parameters
    assert params["type"] == "object"
    assert params["properties"]["query"] == {"type": "string"}
    assert params["properties"]["k"]["type"] == "integer"
    assert params["properties"]["k"]["default"] == 10
    assert params["required"] == ["query"]


def test_paperqa_answer_schema_advertises_query_and_max_sources() -> None:
    """``paperqa.answer`` requires ``query`` and offers an integer ``max_sources``."""
    spec = default_registry.get("paperqa.answer")
    assert spec is not None
    params = spec.parameters
    assert params["properties"]["query"] == {"type": "string"}
    assert params["properties"]["max_sources"]["type"] == "integer"
    assert params["properties"]["max_sources"]["default"] == 10
    assert params["required"] == ["query"]


def test_paperqa_reset_schema_has_no_required_args() -> None:
    """``paperqa.reset`` takes no arguments — empty ``required`` (or absent)."""
    spec = default_registry.get("paperqa.reset")
    assert spec is not None
    # The schema either omits ``required`` (no required keys) or has an
    # empty list. Either is fine for an arg-less tool.
    assert spec.parameters.get("required", []) == []


def test_paperqa_gather_evidence_schema_advertises_candidate_list() -> None:
    """``paperqa.gather_evidence`` accepts an optional ``candidate_paper_ids`` list."""
    spec = default_registry.get("paperqa.gather_evidence")
    assert spec is not None
    params = spec.parameters
    assert params["properties"]["query"] == {"type": "string"}
    # ``list[str] | None`` unwraps to ``list[str]`` via Optional-unwrap.
    assert params["properties"]["candidate_paper_ids"]["type"] == "array"


# ── argument validation ──────────────────────────────────────────────────


@pytest.mark.parametrize("bad_k", [0, -1, -10])
def test_search_rejects_non_positive_k(bad_k: int) -> None:
    """``k < 1`` raises :class:`ValueError` before paper-qa is loaded."""
    facade = LinusPaperQA()
    import asyncio

    with pytest.raises(ValueError, match="k must be >= 1"):
        asyncio.run(facade.search(query="anything", k=bad_k))


@pytest.mark.parametrize("bad_max", [0, -1, -100])
def test_answer_rejects_non_positive_max_sources(bad_max: int) -> None:
    """``max_sources < 1`` raises :class:`ValueError` before paper-qa is loaded."""
    facade = LinusPaperQA()
    import asyncio

    with pytest.raises(ValueError, match="max_sources must be >= 1"):
        asyncio.run(facade.answer(query="anything", max_sources=bad_max))


# ── citation → provenance mapping ────────────────────────────────────────


def test_citation_to_provenance_maps_full_context() -> None:
    """A fully-populated Context maps to all four provenance keys."""
    ctx = _make_context(
        paper_id="abc123",
        chunk_name="Smith2024 pages 3-4",
        text="raw text",
        summary="conditioned summary",
        score=8,
    )
    out = citation_to_provenance(ctx)
    assert out == {
        "paper_id": "abc123",
        "page": 3,
        "excerpt": "conditioned summary",
        "score": 8.0,
    }


def test_citation_to_provenance_falls_back_to_docname_when_no_dockey() -> None:
    """When dockey is missing, the docname is used as paper_id."""
    ctx = _make_context()
    ctx.text.doc.dockey = None
    out = citation_to_provenance(ctx)
    assert out["paper_id"] == "Smith2024"


def test_citation_to_provenance_excerpt_falls_back_to_raw_text() -> None:
    """When the contextual summary is empty, the raw chunk text is used as excerpt."""
    ctx = _make_context(text="raw chunk", summary="")
    out = citation_to_provenance(ctx)
    assert out["excerpt"] == "raw chunk"


def test_citation_to_provenance_handles_unset_score() -> None:
    """paper-qa's -1 'unset' sentinel normalizes to 0.0."""
    ctx = _make_context(score=-1)
    out = citation_to_provenance(ctx)
    assert out["score"] == 0.0


def test_citation_to_provenance_handles_no_page_in_chunk_name() -> None:
    """A chunk name without a page-range substring yields ``page=None``."""
    ctx = _make_context(chunk_name="Smith2024 chunk 1")
    out = citation_to_provenance(ctx)
    assert out["page"] is None


def test_citation_to_provenance_handles_missing_text_object() -> None:
    """A context with no ``.text`` falls through to defaults."""
    ctx = MagicMock()
    ctx.text = None
    ctx.context = "just a summary"
    ctx.score = 5
    out = citation_to_provenance(ctx)
    assert out["paper_id"] is None
    assert out["page"] is None
    assert out["excerpt"] == "just a summary"
    assert out["score"] == 5.0


def test_citation_to_provenance_handles_non_numeric_score() -> None:
    """A score that won't parse as float defaults to 0.0."""
    ctx = _make_context()
    ctx.score = "not-a-number"
    out = citation_to_provenance(ctx)
    assert out["score"] == 0.0


@pytest.mark.parametrize(
    "name,expected",
    [
        ("Smith2024 pages 3-4", 3),
        ("Smith2024 page 7", 7),
        ("Smith2024 p. 42", 42),
        ("Smith2024 chunk 1", None),
        ("no page reference here", None),
        ("", None),
    ],
)
def test_parse_first_page_handles_variants(name: str, expected: int | None) -> None:
    """``_parse_first_page`` recognizes 'page', 'pages', and 'p.' forms."""
    assert _parse_first_page(name) == expected


# ── error paths ──────────────────────────────────────────────────────────


def test_search_raises_paperqa_unavailable_when_not_installed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """If paper-qa cannot be imported, calls surface :class:`PaperQAUnavailableError`."""
    # Force the lazy import to fail. Remove any cached 'paperqa' entry first.
    monkeypatch.setitem(sys.modules, "paperqa", None)
    facade = LinusPaperQA(papers_dir=tmp_path)
    import asyncio

    with pytest.raises(PaperQAUnavailableError, match="paper-qa is not installed"):
        asyncio.run(facade.search(query="x", k=3))


def test_ensure_loaded_raises_config_error_when_papers_dir_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A missing papers directory raises :class:`PaperQAConfigError`."""
    _install_fake_paperqa(monkeypatch)
    missing = tmp_path / "does-not-exist"
    facade = LinusPaperQA(papers_dir=missing)
    import asyncio

    with pytest.raises(PaperQAConfigError, match="does not exist"):
        asyncio.run(facade.search(query="x", k=3))


# ── happy-path: search / gather / answer / reset against fake paperqa ────


def test_search_returns_provenance_dicts(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """End-to-end search call returns provenance dicts from fake session contexts."""
    fake = _install_fake_paperqa(monkeypatch)
    fake_session = fake.PQASession(question="q")
    fake_session.contexts = [
        _make_context(paper_id="p1", chunk_name="A pages 1-2", score=9),
        _make_context(paper_id="p2", chunk_name="B pages 3", score=7),
    ]

    facade = LinusPaperQA(papers_dir=tmp_path)
    import asyncio

    # Stub aget_evidence on the (lazily-created) Docs instance once loaded.
    async def _run() -> list[dict]:
        # Trigger lazy load.
        facade._ensure_loaded()
        facade._docs.aget_evidence = AsyncMock(return_value=fake_session)
        return await facade.search(query="anything", k=10)

    out = asyncio.run(_run())
    assert len(out) == 2
    assert out[0]["paper_id"] == "p1"
    assert out[0]["page"] == 1
    assert out[1]["paper_id"] == "p2"
    assert out[1]["page"] == 3


def test_search_truncates_to_k(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``search(k=2)`` returns at most 2 contexts even when more are available."""
    fake = _install_fake_paperqa(monkeypatch)
    fake_session = fake.PQASession(question="q")
    fake_session.contexts = [_make_context(paper_id=f"p{i}", chunk_name=f"X pages {i}") for i in range(5)]

    facade = LinusPaperQA(papers_dir=tmp_path)
    import asyncio

    async def _run() -> list[dict]:
        facade._ensure_loaded()
        facade._docs.aget_evidence = AsyncMock(return_value=fake_session)
        return await facade.search(query="q", k=2)

    assert len(asyncio.run(_run())) == 2


def test_answer_returns_full_payload(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``answer`` returns question / answer / formatted_answer / citations."""
    fake = _install_fake_paperqa(monkeypatch)
    fake_session = fake.PQASession(question="why?")
    fake_session.answer = "Because X causes Y."
    fake_session.formatted_answer = "Because X causes Y. (Smith2024)"
    fake_session.contexts = [_make_context()]

    facade = LinusPaperQA(papers_dir=tmp_path)
    import asyncio

    async def _run() -> dict:
        facade._ensure_loaded()
        facade._docs.aquery = AsyncMock(return_value=fake_session)
        return await facade.answer(query="why?", max_sources=10)

    out = asyncio.run(_run())
    assert out["question"] == "why?"
    assert out["answer"] == "Because X causes Y."
    assert out["formatted_answer"] == "Because X causes Y. (Smith2024)"
    assert len(out["citations"]) == 1
    assert out["citations"][0]["paper_id"] == "doc-abc"


def test_gather_evidence_filters_by_candidate_paper_ids(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``candidate_paper_ids`` is enforced as a soft filter on returned contexts."""
    fake = _install_fake_paperqa(monkeypatch)
    fake_session = fake.PQASession(question="q")
    fake_session.contexts = [
        _make_context(paper_id="p1"),
        _make_context(paper_id="p2"),
        _make_context(paper_id="p3"),
    ]

    facade = LinusPaperQA(papers_dir=tmp_path)
    import asyncio

    async def _run() -> list[dict]:
        facade._ensure_loaded()
        facade._docs.aget_evidence = AsyncMock(return_value=fake_session)
        return await facade.gather_evidence(query="q", candidate_paper_ids=["p1", "p3"])

    out = asyncio.run(_run())
    assert [c["paper_id"] for c in out] == ["p1", "p3"]


def test_reset_clears_docs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``reset`` calls into ``Docs.clear_docs`` once the facade is loaded."""
    _install_fake_paperqa(monkeypatch)
    facade = LinusPaperQA(papers_dir=tmp_path)
    import asyncio

    async def _run() -> dict:
        facade._ensure_loaded()
        return await facade.reset()

    out = asyncio.run(_run())
    assert out["status"] == "reset"
    assert facade._docs.cleared is True


def test_reset_on_unloaded_facade_is_a_no_op() -> None:
    """Calling reset before any load is a no-op that reports honestly."""
    facade = LinusPaperQA()  # never loaded
    import asyncio

    out = asyncio.run(facade.reset())
    assert out["status"] == "reset"
    assert "no-op" in out["detail"]


# ── singleton lifecycle ───────────────────────────────────────────────────


def test_get_singleton_returns_same_instance() -> None:
    """Repeated :func:`get_singleton` calls return the same object."""
    a = get_singleton()
    b = get_singleton()
    assert a is b
    assert isinstance(a, LinusPaperQA)


def test_reset_singleton_drops_cached_instance() -> None:
    """After :func:`reset_singleton` a fresh instance is constructed."""
    a = get_singleton()
    reset_singleton()
    b = get_singleton()
    assert a is not b


# ── ollama config builder ────────────────────────────────────────────────


def test_build_ollama_llm_config_defaults() -> None:
    """Default config points at the documented host and model."""
    cfg = build_ollama_llm_config()
    entry = cfg["model_list"][0]
    assert entry["model_name"] == f"ollama/{DEFAULT_MODEL}"
    assert entry["litellm_params"]["model"] == f"ollama/{DEFAULT_MODEL}"
    assert entry["litellm_params"]["api_base"] == DEFAULT_OLLAMA_HOST


def test_build_ollama_llm_config_honors_overrides() -> None:
    """Explicit model + host arguments override the defaults."""
    cfg = build_ollama_llm_config(model="qwen3:14b", host="http://example:11434")
    entry = cfg["model_list"][0]
    assert entry["model_name"] == "ollama/qwen3:14b"
    assert entry["litellm_params"]["api_base"] == "http://example:11434"


def test_build_ollama_llm_config_honors_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment-variable overrides propagate when no explicit args are given."""
    monkeypatch.setenv("LINUS_PAPERQA_MODEL", "qwen3:14b")
    monkeypatch.setenv("OLLAMA_HOST", "http://custom:9999")
    cfg = build_ollama_llm_config()
    entry = cfg["model_list"][0]
    assert entry["model_name"] == "ollama/qwen3:14b"
    assert entry["litellm_params"]["api_base"] == "http://custom:9999"


# ── papers-dir resolution ────────────────────────────────────────────────


def test_papers_dir_default_is_under_home() -> None:
    """With no env vars, the default papers dir is ``~/.linus/papers``."""
    from linus.knowledge.paperqa import _papers_dir

    expected = Path.home() / ".linus" / "papers"
    # Use monkey-free check: ``LINUS_PAPERQA_DIR`` / ``LINUS_PAPERS_DIR`` may
    # not be set in CI but could be locally; respect either if present.
    import os

    if not (os.environ.get("LINUS_PAPERQA_DIR") or os.environ.get("LINUS_PAPERS_DIR")):
        assert _papers_dir() == expected


def test_papers_dir_honors_linus_paperqa_dir_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``LINUS_PAPERQA_DIR`` takes precedence over the default."""
    target = tmp_path / "papers-explicit"
    monkeypatch.setenv("LINUS_PAPERQA_DIR", str(target))
    from linus.knowledge.paperqa import _papers_dir

    assert _papers_dir() == target


def test_papers_dir_falls_back_to_linus_papers_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``LINUS_PAPERS_DIR`` (the arxiv-ingest shared var) is used if PAPERQA_DIR unset."""
    target = tmp_path / "papers-shared"
    monkeypatch.delenv("LINUS_PAPERQA_DIR", raising=False)
    monkeypatch.setenv("LINUS_PAPERS_DIR", str(target))
    from linus.knowledge.paperqa import _papers_dir

    assert _papers_dir() == target


# ── 2026-05-22 reveal-prep bug 4 — papers-dir auto-create ──────────────────


def test_papers_dir_auto_creates_when_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``_papers_dir()`` materializes the configured path with a README inside.

    Regression test for the 2026-05-22 reveal-prep bug 4: a fresh
    machine without ``~/.linus/papers`` used to surface as
    :class:`PaperQAConfigError`. The fix shifts the missing-dir path
    into the resolver, which auto-creates the directory and drops a
    README so the user knows what belongs there.
    """
    target = tmp_path / "papers-fresh"
    monkeypatch.setenv("LINUS_PAPERQA_DIR", str(target))
    from linus.knowledge.paperqa import _papers_dir

    # Pre-condition: the target does not exist.
    assert not target.exists()

    resolved = _papers_dir()
    assert resolved == target
    # Post-condition: the directory is now materialized + README written.
    assert target.is_dir()
    readme = target / "README.md"
    assert readme.is_file()
    body = readme.read_text(encoding="utf-8")
    assert "Linus Paper Q&A" in body
    assert "Drop PDFs here" in body


def test_papers_dir_auto_create_is_idempotent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Calling :func:`_papers_dir` twice on a pre-existing directory does not
    rewrite the README — the user is free to edit it in place without losing
    their changes on the next page load.
    """
    target = tmp_path / "papers-stable"
    target.mkdir()
    readme = target / "README.md"
    readme.write_text("custom content — please do not overwrite\n", encoding="utf-8")

    monkeypatch.setenv("LINUS_PAPERQA_DIR", str(target))
    from linus.knowledge.paperqa import _papers_dir

    _papers_dir()
    _papers_dir()

    # The README content should be unchanged after two resolver calls
    # on an already-existing directory.
    assert readme.read_text(encoding="utf-8") == "custom content — please do not overwrite\n"


def test_ensure_loaded_no_longer_raises_when_default_dir_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When the resolver auto-creates the dir, ``_ensure_loaded`` succeeds.

    This is the end-to-end shape of the bug-4 fix: a fresh
    :class:`LinusPaperQA` whose ``papers_dir`` comes from the resolver
    against a non-existent path no longer fails at the
    ``_ensure_loaded`` boundary.
    """
    _install_fake_paperqa(monkeypatch)
    target = tmp_path / "papers-autocreated"
    monkeypatch.setenv("LINUS_PAPERQA_DIR", str(target))
    reset_singleton()

    # Building via the singleton + resolver should yield a working facade
    # whose ``_ensure_loaded`` does not raise.
    facade = get_singleton()
    facade._ensure_loaded()
    assert facade.papers_dir == target
    assert target.is_dir()


def test_ensure_loaded_still_rejects_non_directory_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A regular file at the configured path still surfaces ``PaperQAConfigError``.

    The auto-create resolver only handles the missing-dir case. If the
    user pointed ``LINUS_PAPERQA_DIR`` at a regular file (or a symlink to
    one), the wrapper still rejects it explicitly so the failure is
    legible instead of crashing inside paper-qa.
    """
    _install_fake_paperqa(monkeypatch)
    bogus = tmp_path / "not-a-directory"
    bogus.write_text("this is a file, not a dir", encoding="utf-8")

    facade = LinusPaperQA(papers_dir=bogus)
    import asyncio

    with pytest.raises(PaperQAConfigError, match="not a directory"):
        asyncio.run(facade.search(query="x", k=3))


# ── default-embedding constants ───────────────────────────────────────────


def test_default_embedding_model_is_ollama_prefixed() -> None:
    """The default embedding model is an Ollama-routed name (no hosted API)."""
    assert DEFAULT_EMBEDDING_MODEL.startswith("ollama/")


# ── tool-call surface dispatch ───────────────────────────────────────────


def test_paperqa_search_tool_dispatches_through_singleton(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Invoking the registered ``paperqa.search`` tool runs through the singleton."""
    _install_fake_paperqa(monkeypatch)
    monkeypatch.setenv("LINUS_PAPERQA_DIR", str(tmp_path))
    reset_singleton()

    # Patch the singleton's search method to a known async stub so we
    # don't need to fake out every paper-qa internal.
    sentinel = [{"paper_id": "stub", "page": 1, "excerpt": "x", "score": 1.0}]

    singleton = get_singleton()
    singleton.search = AsyncMock(return_value=sentinel)  # type: ignore[method-assign]

    result = default_registry.call_tool("paperqa.search", {"query": "anything", "k": 3})
    assert result == sentinel
    singleton.search.assert_awaited_once_with(query="anything", k=3)


def test_paperqa_answer_tool_dispatches_through_singleton(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Invoking the registered ``paperqa.answer`` tool runs through the singleton."""
    _install_fake_paperqa(monkeypatch)
    monkeypatch.setenv("LINUS_PAPERQA_DIR", str(tmp_path))
    reset_singleton()

    payload = {"question": "q", "answer": "a", "formatted_answer": "a", "citations": []}
    singleton = get_singleton()
    singleton.answer = AsyncMock(return_value=payload)  # type: ignore[method-assign]

    result = default_registry.call_tool("paperqa.answer", {"query": "q", "max_sources": 5})
    assert result == payload
    singleton.answer.assert_awaited_once_with(query="q", max_sources=5)


def test_paperqa_reset_tool_dispatches_through_singleton(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Invoking the registered ``paperqa.reset`` tool runs through the singleton."""
    _install_fake_paperqa(monkeypatch)
    monkeypatch.setenv("LINUS_PAPERQA_DIR", str(tmp_path))
    reset_singleton()

    singleton = get_singleton()
    singleton.reset = AsyncMock(return_value={"status": "reset", "detail": "ok"})  # type: ignore[method-assign]

    result = default_registry.call_tool("paperqa.reset", {})
    assert result == {"status": "reset", "detail": "ok"}
    singleton.reset.assert_awaited_once_with()


def test_paperqa_gather_evidence_tool_dispatches_through_singleton(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Invoking ``paperqa.gather_evidence`` runs through the singleton."""
    _install_fake_paperqa(monkeypatch)
    monkeypatch.setenv("LINUS_PAPERQA_DIR", str(tmp_path))
    reset_singleton()

    singleton = get_singleton()
    singleton.gather_evidence = AsyncMock(return_value=[])  # type: ignore[method-assign]

    result = default_registry.call_tool(
        "paperqa.gather_evidence",
        {"query": "q", "candidate_paper_ids": ["a", "b"]},
    )
    assert result == []
    singleton.gather_evidence.assert_awaited_once_with(query="q", candidate_paper_ids=["a", "b"])


# ── _run_async bridge ─────────────────────────────────────────────────────


def test_run_async_completes_a_simple_coroutine() -> None:
    """The sync→async bridge resolves a vanilla coroutine to its return value."""
    from linus.knowledge.paperqa import _run_async

    async def _coro() -> int:
        return 42

    assert _run_async(_coro()) == 42


def test_run_async_works_inside_running_loop() -> None:
    """When called from a running loop, the bridge runs the coroutine on a worker thread."""
    import asyncio

    from linus.knowledge.paperqa import _run_async

    async def _outer() -> int:
        async def _inner() -> int:
            return 99

        # Inside a running loop — the bridge must spin up a worker thread.
        return _run_async(_inner())

    assert asyncio.run(_outer()) == 99


# ── Settings configuration ────────────────────────────────────────────────


def test_ensure_loaded_configures_paper_directory_on_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """After load, Settings.agent.index.paper_directory points at the configured dir."""
    _install_fake_paperqa(monkeypatch)
    facade = LinusPaperQA(papers_dir=tmp_path)
    facade._ensure_loaded()
    assert facade._settings is not None
    assert facade._settings.agent.index.paper_directory == str(tmp_path)


def test_ensure_loaded_is_idempotent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Calling :meth:`_ensure_loaded` twice does not recreate ``Docs``."""
    _install_fake_paperqa(monkeypatch)
    facade = LinusPaperQA(papers_dir=tmp_path)
    facade._ensure_loaded()
    docs_first = facade._docs
    facade._ensure_loaded()
    assert facade._docs is docs_first


def test_module_constants_align_with_claude_md() -> None:
    """Sanity-check the defaults documented in CLAUDE.md.

    DEFAULT_MODEL is the empirically-validated Phase 1e/2c Worker
    (``qwen3:8b`` per CLAUDE.md). DEFAULT_OLLAMA_HOST is the documented
    brew-managed Ollama port (11434).
    """
    assert DEFAULT_MODEL == "qwen3:8b"
    assert DEFAULT_OLLAMA_HOST == "http://localhost:11434"


# ── rigor auto-gate on answer() ───────────────────────────────────────────


class _FakeKBPaper:
    """Tiny stand-in for the adapter's :class:`Paper` shape used by the rigor gate."""

    def __init__(self, page_count: int) -> None:
        self.page_count = page_count


class _FakeKBAdapter:
    """Fake ``KnowledgeBaseAdapter`` whose ``get_paper`` returns a fixed map.

    Mirrors the production adapter's surface enough for
    :class:`_AdapterPaperLookup` to wrap it. The rigor citation check
    only needs ``get_paper`` and ``get_page_count`` (via the wrapper),
    so a map of ``paper_id → page_count`` is sufficient.
    """

    def __init__(self, papers: dict[str, int]) -> None:
        self._papers = papers

    def get_paper(self, paper_id: str) -> _FakeKBPaper | None:
        if paper_id not in self._papers:
            return None
        return _FakeKBPaper(page_count=self._papers[paper_id])


def _install_rigor_backends(
    monkeypatch: pytest.MonkeyPatch,
    paper_map: dict[str, int],
) -> None:
    """Wire :func:`_resolve_paper_backend` to a fake KB; entity backend stays the stub.

    Used by the auto-gate tests below so the rigor field actually runs
    against a known-shape backend rather than failing-open. The
    ``BuiltinEntityLookup`` stub is left in place — the answer tests
    don't carry entities on the claim so the entity check fires the
    "no entities" no-op path.
    """
    from linus.knowledge.paperqa import _adapter_to_paper_lookup

    def _fake_paper_backend() -> object:
        return _adapter_to_paper_lookup(_FakeKBAdapter(paper_map))

    monkeypatch.setattr(
        "linus.knowledge.paperqa._resolve_paper_backend",
        _fake_paper_backend,
    )


def test_answer_payload_includes_rigor_field_when_backends_resolve(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The auto-gate runs and the payload carries a non-None ``rigor`` dict."""
    fake = _install_fake_paperqa(monkeypatch)
    fake_session = fake.PQASession(question="why?")
    fake_session.answer = "Because X causes Y."
    fake_session.formatted_answer = "Because X causes Y. (Smith2024)"
    # The fake context's ``paper_id`` is ``"doc-abc"`` per ``_make_context``.
    fake_session.contexts = [_make_context(paper_id="doc-abc", chunk_name="X pages 2")]

    _install_rigor_backends(monkeypatch, paper_map={"doc-abc": 10})

    facade = LinusPaperQA(papers_dir=tmp_path)
    import asyncio

    async def _run() -> dict:
        facade._ensure_loaded()
        facade._docs.aquery = AsyncMock(return_value=fake_session)
        return await facade.answer(query="why?", max_sources=10)

    out = asyncio.run(_run())
    assert "rigor" in out
    assert isinstance(out["rigor"], dict)
    # The gate ran end-to-end against the fake KB; the rigor dict
    # surfaces the documented :func:`result_to_dict` keys.
    assert "passed" in out["rigor"]
    assert "failures" in out["rigor"]
    assert "error_count" in out["rigor"]


def test_answer_rigor_passes_on_resolved_citation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A citation whose paper_id resolves and whose page is in-range passes the gate."""
    fake = _install_fake_paperqa(monkeypatch)
    fake_session = fake.PQASession(question="why?")
    fake_session.answer = "Because X causes Y."
    fake_session.formatted_answer = "Because X causes Y. (Smith2024)"
    # ``page 2`` of a 10-page paper: in range.
    fake_session.contexts = [_make_context(paper_id="doc-abc", chunk_name="X pages 2")]

    _install_rigor_backends(monkeypatch, paper_map={"doc-abc": 10})

    facade = LinusPaperQA(papers_dir=tmp_path)
    import asyncio

    async def _run() -> dict:
        facade._ensure_loaded()
        facade._docs.aquery = AsyncMock(return_value=fake_session)
        return await facade.answer(query="why?", max_sources=10)

    out = asyncio.run(_run())
    rigor = out["rigor"]
    assert rigor is not None
    assert rigor["passed"] is True
    assert rigor["error_count"] == 0


def test_answer_rigor_surfaces_unresolved_citation_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A citation whose paper_id is not in the KB → ``unresolved_citation`` error."""
    fake = _install_fake_paperqa(monkeypatch)
    fake_session = fake.PQASession(question="why?")
    fake_session.answer = "Because X causes Y."
    fake_session.formatted_answer = "Because X causes Y. (Smith2024)"
    fake_session.contexts = [
        _make_context(paper_id="doc-missing", chunk_name="X pages 2"),
    ]

    # Empty KB → the cited paper resolves to None.
    _install_rigor_backends(monkeypatch, paper_map={})

    facade = LinusPaperQA(papers_dir=tmp_path)
    import asyncio

    async def _run() -> dict:
        facade._ensure_loaded()
        facade._docs.aquery = AsyncMock(return_value=fake_session)
        return await facade.answer(query="why?", max_sources=10)

    out = asyncio.run(_run())
    rigor = out["rigor"]
    assert rigor is not None
    assert rigor["passed"] is False
    assert rigor["error_count"] >= 1
    kinds = {f.get("kind") for f in rigor["failures"]}
    assert "unresolved_citation" in kinds


def test_answer_rigor_failopens_to_none_when_gate_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """If the rigor gate raises internally, the answer succeeds with ``rigor=None``.

    The auto-gate is best-effort by contract — failures inside the gate
    must NOT propagate to the answer call. We force the gate to raise
    by monkeypatching :func:`check_grounding` to throw and verify the
    answer payload still surfaces with ``rigor=None`` rather than 5xx-ing.
    """
    fake = _install_fake_paperqa(monkeypatch)
    fake_session = fake.PQASession(question="why?")
    fake_session.answer = "Because X causes Y."
    fake_session.formatted_answer = "Because X causes Y."
    fake_session.contexts = [_make_context()]

    def _boom(*args: object, **kwargs: object) -> object:
        raise RuntimeError("rigor gate exploded")

    # Patch at the call site inside :mod:`linus.knowledge.paperqa` — the
    # auto-gate imports ``check_grounding`` lazily inside the helper so
    # the import-target is the module's own symbol resolution chain.
    monkeypatch.setattr("linus.knowledge.rigor.check_grounding", _boom)

    facade = LinusPaperQA(papers_dir=tmp_path)
    import asyncio

    async def _run() -> dict:
        facade._ensure_loaded()
        facade._docs.aquery = AsyncMock(return_value=fake_session)
        return await facade.answer(query="why?", max_sources=10)

    out = asyncio.run(_run())
    # Answer itself succeeded.
    assert out["answer"] == "Because X causes Y."
    # But the rigor field failed-open to None.
    assert out["rigor"] is None


def test_adapter_to_paper_lookup_returns_page_count_from_paper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """:func:`_adapter_to_paper_lookup` reads ``page_count`` off the adapter's Paper."""
    from linus.knowledge.paperqa import _adapter_to_paper_lookup

    lookup = _adapter_to_paper_lookup(_FakeKBAdapter({"x": 7}))
    paper = lookup.get_paper("x")
    assert paper is not None
    assert lookup.get_page_count("x") == 7
    # Unknown paper → both methods return None.
    assert lookup.get_paper("missing") is None
    assert lookup.get_page_count("missing") is None


# ── #107 H2: _AdapterPaperLookup must not double-call adapter.get_paper ────


class _CountingKBAdapter:
    """KB-adapter stand-in that counts every ``get_paper`` invocation.

    The rigor gate calls ``get_paper`` once and ``get_page_count`` once
    per citation; per the #107 H2 bug fix, the wrapper memoizes the
    first call so the second method reads from cache rather than
    re-querying SQLite. This fake makes the call count observable.
    """

    def __init__(self, papers: dict[str, int]) -> None:
        self._papers = papers
        self.call_count = 0
        self.calls_by_id: dict[str, int] = {}

    def get_paper(self, paper_id: str) -> _FakeKBPaper | None:
        self.call_count += 1
        self.calls_by_id[paper_id] = self.calls_by_id.get(paper_id, 0) + 1
        if paper_id not in self._papers:
            return None
        return _FakeKBPaper(page_count=self._papers[paper_id])


def test_adapter_paper_lookup_calls_get_paper_once_per_citation() -> None:
    """The wrapper deduplicates ``adapter.get_paper`` across the rigor gate's
    two-method call shape (``get_paper`` then ``get_page_count``) so each
    citation produces exactly ONE SQLite round-trip (#107 H2 regression test).
    """
    from linus.knowledge.paperqa import _adapter_to_paper_lookup

    adapter = _CountingKBAdapter({"doc-abc": 10})
    lookup = _adapter_to_paper_lookup(adapter)

    # Simulate the rigor gate's per-citation pattern: get_paper, then
    # get_page_count, on the same paper id.
    paper = lookup.get_paper("doc-abc")
    page_count = lookup.get_page_count("doc-abc")

    assert paper is not None
    assert page_count == 10
    # The critical assertion: the adapter saw exactly ONE call for this id.
    assert adapter.call_count == 1
    assert adapter.calls_by_id["doc-abc"] == 1


def test_adapter_paper_lookup_caches_missing_paper_ids() -> None:
    """Missing paper ids are cached as ``None`` so a follow-up ``get_page_count``
    does not re-query the adapter for the known-absent row (#107 H2 corollary).
    """
    from linus.knowledge.paperqa import _adapter_to_paper_lookup

    adapter = _CountingKBAdapter({})  # empty KB → every lookup misses
    lookup = _adapter_to_paper_lookup(adapter)

    assert lookup.get_paper("doc-missing") is None
    assert lookup.get_page_count("doc-missing") is None
    # Even though both calls returned None, only one DB hit should have
    # occurred — caching the negative result is part of the fix.
    assert adapter.call_count == 1


def test_adapter_paper_lookup_caches_per_paper_id() -> None:
    """The cache is keyed by paper_id, so distinct ids each cost one DB hit
    but each repeated id costs zero extra (#107 H2 corollary).
    """
    from linus.knowledge.paperqa import _adapter_to_paper_lookup

    adapter = _CountingKBAdapter({"a": 5, "b": 7})
    lookup = _adapter_to_paper_lookup(adapter)

    # Two citations, each calling the two-method pattern.
    lookup.get_paper("a")
    lookup.get_page_count("a")
    lookup.get_paper("b")
    lookup.get_page_count("b")
    # Plus a re-lookup of "a" — should still be 2 total DB hits.
    lookup.get_paper("a")

    assert adapter.call_count == 2
    assert adapter.calls_by_id == {"a": 1, "b": 1}
