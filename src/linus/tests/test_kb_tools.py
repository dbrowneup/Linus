"""Tests for :mod:`linus.tools.kb_tools` — KB tool wrappers on the default registry.

The kb_tools module is the seam between the in-process Linus tool registry and
the read-only KnowledgeBase adapter: it exposes two tool callables
(``linus.knowledge.search_papers`` and ``linus.knowledge.get_paper``) that the
FastAPI server forwards to Ollama as OpenAI-format tool advertisements, then
invokes by name when the model emits a ``tool_calls`` response. Under-testing
this seam leaves the tool-dispatch path fragile — the dispatcher would happily
forward a malformed Paper dict to the model if ``_paper_to_dict`` ever drifted,
and the lazy ``_get_adapter`` singleton has stateful behavior that's easy to
break with a careless refactor.

The suite is fully hermetic: every test substitutes a fake adapter via
monkeypatch on ``kb_tools._adapter`` (or via ``_get_adapter``) so no SQLite
file, no submodule, no network, and no real ``metadata.db`` is required. The
tests target every documented branch in the 88-line module, covering the four
missing-line ranges (38-40, 50, 70-72, 83-87) plus the surrounding tool
registration and dispatch invariants.
"""

from __future__ import annotations

from typing import Any

import pytest

from linus.knowledge import Paper
from linus.tools import kb_tools
from linus.tools.kb_tools import (
    _get_adapter,
    _paper_to_dict,
    get_paper,
    search_papers,
)
from linus.tools.registry import default_registry

# ── helpers ────────────────────────────────────────────────────────────────


def _make_paper(
    sha256: str = "a" * 64,
    title: str | None = "Genome assembly of Botryococcus braunii",
    authors: str | None = "Browne, D. R.; Jenkins, J.; Schmutz, J.",
    year: int | None = 2017,
    journal: str | None = "Genome Biology and Evolution",
    doi: str | None = "10.1093/gbe/evx139",
    abstract: str | None = "The colonial green alga Botryococcus braunii ...",
    url: str | None = "https://academic.oup.com/gbe/article/9/7/1894/3098565",
) -> Paper:
    """Build a Paper fixture with sensible defaults Dan-recognizable.

    Keeps the test data anchored in his actual corpus (Botryococcus braunii)
    so a failing test message reads like a real-world miss, not a synthetic
    string nobody recognizes."""
    return Paper(
        sha256=sha256,
        title=title,
        authors=authors,
        year=year,
        journal=journal,
        doi=doi,
        abstract=abstract,
        url=url,
    )


class _FakeAdapter:
    """Stand-in for :class:`KnowledgeBaseAdapter` with recorded call args.

    Tests configure ``search_return`` and ``get_return`` (or set a callable on
    those attributes to raise) and inspect ``calls`` afterward to assert that
    the kb_tools layer forwards arguments unchanged."""

    def __init__(
        self,
        search_return: list[Paper] | Exception | None = None,
        get_return: Paper | None | Exception = None,
    ) -> None:
        self.search_return = search_return if search_return is not None else []
        self.get_return = get_return
        self.calls: list[tuple[str, tuple, dict]] = []

    def search_papers(self, query: str, limit: int = 10) -> list[Paper]:
        self.calls.append(("search_papers", (query,), {"limit": limit}))
        if isinstance(self.search_return, Exception):
            raise self.search_return
        return self.search_return

    def get_paper(self, sha256: str) -> Paper | None:
        self.calls.append(("get_paper", (sha256,), {}))
        if isinstance(self.get_return, Exception):
            raise self.get_return
        return self.get_return


@pytest.fixture(autouse=True)
def _reset_adapter_singleton() -> Any:
    """Restore ``kb_tools._adapter`` to None around every test.

    The module-level singleton is the dependency-injection seam tests use
    (`monkeypatch.setattr(kb_tools, "_adapter", fake)`); if a prior test
    leaves a fake in place, subsequent tests see stale state. autouse
    fixture avoids that cross-test contamination."""
    original = kb_tools._adapter
    yield
    kb_tools._adapter = original


# ── _get_adapter: lazy-singleton lifecycle (lines 38-40) ───────────────────


def test_get_adapter_lazily_constructs_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    """First call to ``_get_adapter`` constructs a new
    :class:`KnowledgeBaseAdapter` and caches it on the module global.
    Exercises line 38-40 (the ``if _adapter is None: _adapter = ...`` branch).

    We monkeypatch the adapter class so no real DB file is required — the
    constructor is replaced with a tracker that returns a sentinel."""
    constructed: list[Any] = []

    class _Tracker:
        def __init__(self) -> None:
            constructed.append(self)

    monkeypatch.setattr(kb_tools, "KnowledgeBaseAdapter", _Tracker)
    monkeypatch.setattr(kb_tools, "_adapter", None)

    result = _get_adapter()
    assert isinstance(result, _Tracker)
    assert len(constructed) == 1
    # The module-level singleton is now populated, so a second call must NOT
    # re-construct.
    assert kb_tools._adapter is result


def test_get_adapter_returns_cached_singleton_on_second_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Second + subsequent calls return the cached instance without
    re-constructing. The lazy-singleton contract: one adapter per process,
    not one per tool call."""
    construct_count = 0

    class _Tracker:
        def __init__(self) -> None:
            nonlocal construct_count
            construct_count += 1

    monkeypatch.setattr(kb_tools, "KnowledgeBaseAdapter", _Tracker)
    monkeypatch.setattr(kb_tools, "_adapter", None)

    first = _get_adapter()
    second = _get_adapter()
    third = _get_adapter()
    assert first is second is third
    assert construct_count == 1


def test_get_adapter_uses_module_level_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests can inject a fixture adapter by setting ``kb_tools._adapter``
    directly; ``_get_adapter`` returns it untouched (no re-construction).
    This is the documented monkeypatch site for downstream test files."""
    fake = _FakeAdapter()
    monkeypatch.setattr(kb_tools, "_adapter", fake)
    assert _get_adapter() is fake


def test_get_adapter_propagates_constructor_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the underlying adapter raises during construction (e.g. SQLite
    can't open the file), ``_get_adapter`` does not swallow it — the error
    propagates up to the dispatcher which wraps it as a ``role=tool``
    error message."""

    class _Boom:
        def __init__(self) -> None:
            raise RuntimeError("metadata.db missing")

    monkeypatch.setattr(kb_tools, "KnowledgeBaseAdapter", _Boom)
    monkeypatch.setattr(kb_tools, "_adapter", None)

    with pytest.raises(RuntimeError, match=r"metadata\.db missing"):
        _get_adapter()
    # On failure the cached singleton remains None so the next call retries.
    assert kb_tools._adapter is None


# ── _paper_to_dict: dict shape contract (line 50) ──────────────────────────


def test_paper_to_dict_emits_exact_documented_keys() -> None:
    """The dict shape is a contract — the model sees these keys, so reordering
    or renaming a field breaks downstream formatting. Pin the exact key set
    so a future ``size_mb`` re-introduction (explicitly dropped per the
    docstring) trips the test."""
    paper = _make_paper()
    out = _paper_to_dict(paper)
    assert set(out.keys()) == {
        "sha256",
        "title",
        "authors",
        "year",
        "journal",
        "doi",
        "abstract",
        "url",
    }


def test_paper_to_dict_values_passthrough() -> None:
    """Each field on the Paper dataclass maps 1:1 to the dict; no
    transformation, no truncation."""
    paper = _make_paper(
        sha256="b" * 64,
        title="A title",
        authors="Author A; Author B",
        year=2024,
        journal="Cool Journal",
        doi="10.0/test",
        abstract="An abstract.",
        url="https://example.org/paper",
    )
    out = _paper_to_dict(paper)
    assert out["sha256"] == "b" * 64
    assert out["title"] == "A title"
    assert out["authors"] == "Author A; Author B"
    assert out["year"] == 2024
    assert out["journal"] == "Cool Journal"
    assert out["doi"] == "10.0/test"
    assert out["abstract"] == "An abstract."
    assert out["url"] == "https://example.org/paper"


def test_paper_to_dict_preserves_none_fields() -> None:
    """KB rows are sparsely populated — most bibliographic fields are nullable.
    The dict must preserve ``None`` rather than substituting an empty string;
    the model can then choose its own missing-data rendering."""
    paper = Paper(sha256="c" * 64)  # everything else None
    out = _paper_to_dict(paper)
    assert out["sha256"] == "c" * 64
    assert out["title"] is None
    assert out["authors"] is None
    assert out["year"] is None
    assert out["journal"] is None
    assert out["doi"] is None
    assert out["abstract"] is None
    assert out["url"] is None


def test_paper_to_dict_drops_infrastructure_fields() -> None:
    """The Paper dataclass carries fields the model doesn't need
    (filename, size_mb, page_count, ...). Confirm none of them leak."""
    paper = Paper(
        sha256="d" * 64,
        filename="paper.pdf",
        size_mb=1.23,
        page_count=20,
        total_words=10_000,
        is_supplement=False,
        is_book=False,
        pmid="12345",
        pmcid="PMC1",
        volume="9",
        pagination="100-110",
        issn="0000-0000",
        papers_id="abc",
        metadata_source="crossref",
        crossref_score=0.9,
        title="t",
    )
    out = _paper_to_dict(paper)
    forbidden = {
        "filename",
        "size_mb",
        "page_count",
        "total_words",
        "is_supplement",
        "is_book",
        "pmid",
        "pmcid",
        "volume",
        "pagination",
        "issn",
        "papers_id",
        "metadata_source",
        "crossref_score",
    }
    assert not (forbidden & set(out.keys()))


# ── search_papers: happy path + error path (lines 70-72) ───────────────────


def test_search_papers_returns_list_of_dicts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Happy path: ``search_papers(query, limit)`` calls the adapter's
    ``search_papers`` and returns each ``Paper`` mapped through
    ``_paper_to_dict``. Covers lines 70-72."""
    paper_a = _make_paper(sha256="a" * 64, title="Paper A", year=2023)
    paper_b = _make_paper(sha256="b" * 64, title="Paper B", year=2022)
    fake = _FakeAdapter(search_return=[paper_a, paper_b])
    monkeypatch.setattr(kb_tools, "_adapter", fake)

    out = search_papers("genome", limit=5)

    assert isinstance(out, list)
    assert len(out) == 2
    assert out[0]["title"] == "Paper A"
    assert out[1]["title"] == "Paper B"
    # All entries are plain dicts, not Paper instances.
    assert all(isinstance(item, dict) for item in out)


def test_search_papers_forwards_query_and_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """The adapter call receives ``query`` and ``limit`` verbatim — kb_tools
    does no pre-processing. The model owns query construction."""
    fake = _FakeAdapter(search_return=[])
    monkeypatch.setattr(kb_tools, "_adapter", fake)

    search_papers("lipid productivity", limit=12)

    assert fake.calls == [("search_papers", ("lipid productivity",), {"limit": 12})]


def test_search_papers_default_limit_is_five(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default ``limit=5`` per the function signature — small enough to keep
    a single tool response compact for the model."""
    fake = _FakeAdapter(search_return=[])
    monkeypatch.setattr(kb_tools, "_adapter", fake)

    search_papers("query")

    assert fake.calls == [("search_papers", ("query",), {"limit": 5})]


def test_search_papers_empty_results_returns_empty_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty adapter result becomes an empty list — distinct from ``None``,
    which would break the model's expected iteration."""
    fake = _FakeAdapter(search_return=[])
    monkeypatch.setattr(kb_tools, "_adapter", fake)
    assert search_papers("nomatch") == []


def test_search_papers_propagates_adapter_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the underlying adapter raises (e.g. KB unavailable), the
    exception bubbles up unchanged — the registry's ``call_tool`` wraps it
    as a ``ToolError`` and the server emits a structured ``role=tool``
    error per the module docstring's contract."""
    from linus.knowledge import KnowledgeBaseUnavailableError

    boom = KnowledgeBaseUnavailableError("metadata.db missing")
    fake = _FakeAdapter(search_return=boom)
    monkeypatch.setattr(kb_tools, "_adapter", fake)

    with pytest.raises(KnowledgeBaseUnavailableError, match=r"metadata\.db missing"):
        search_papers("query", limit=5)


# ── get_paper: happy / miss / error paths (lines 83-87) ───────────────────


def test_get_paper_hit_returns_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    """Happy path: a matching SHA256 returns the paper as a dict."""
    paper = _make_paper(sha256="e" * 64, title="Found", year=2020)
    fake = _FakeAdapter(get_return=paper)
    monkeypatch.setattr(kb_tools, "_adapter", fake)

    out = get_paper("e" * 64)

    assert isinstance(out, dict)
    assert out["sha256"] == "e" * 64
    assert out["title"] == "Found"
    assert out["year"] == 2020


def test_get_paper_miss_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """A hash with no matching row returns ``None`` (line 85-86 branch).
    This is the explicit ``if paper is None: return None`` short-circuit."""
    fake = _FakeAdapter(get_return=None)
    monkeypatch.setattr(kb_tools, "_adapter", fake)

    assert get_paper("f" * 64) is None


def test_get_paper_forwards_sha256(monkeypatch: pytest.MonkeyPatch) -> None:
    """The SHA256 is forwarded verbatim — kb_tools does no normalization
    (the adapter lowercases internally)."""
    fake = _FakeAdapter(get_return=None)
    monkeypatch.setattr(kb_tools, "_adapter", fake)

    get_paper("ABCDEF" * 10 + "1234")
    assert fake.calls == [("get_paper", ("ABCDEF" * 10 + "1234",), {})]


def test_get_paper_propagates_adapter_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An adapter exception bubbles up unchanged from ``get_paper`` so the
    dispatcher's structured-error path can surface it to the model."""
    from linus.knowledge import KnowledgeBaseUnavailableError

    boom = KnowledgeBaseUnavailableError("db gone")
    fake = _FakeAdapter(get_return=boom)
    monkeypatch.setattr(kb_tools, "_adapter", fake)

    with pytest.raises(KnowledgeBaseUnavailableError, match="db gone"):
        get_paper("a" * 64)


# ── Tool-registration invariants ───────────────────────────────────────────


def test_search_papers_registered_with_dotted_name() -> None:
    """Importing :mod:`linus.tools.kb_tools` registers
    ``linus.knowledge.search_papers`` on the default registry. The dotted
    namespace is the on-the-wire name the model sees in OpenAI tool
    advertisements."""
    assert "linus.knowledge.search_papers" in default_registry


def test_get_paper_registered_with_dotted_name() -> None:
    """Same contract for ``linus.knowledge.get_paper``."""
    assert "linus.knowledge.get_paper" in default_registry


def test_search_papers_spec_advertises_query_and_limit() -> None:
    """The auto-derived JSON-Schema for the registered tool must expose
    ``query`` (required) and ``limit`` (optional, integer with default 5)
    so the model can call it correctly."""
    spec = default_registry.get("linus.knowledge.search_papers")
    assert spec is not None
    params = spec.parameters
    assert params["type"] == "object"
    assert params["properties"]["query"] == {"type": "string"}
    assert params["properties"]["limit"]["type"] == "integer"
    assert params["properties"]["limit"]["default"] == 5
    assert params["required"] == ["query"]


def test_get_paper_spec_advertises_sha256_required() -> None:
    """``get_paper`` requires a single ``sha256`` string argument."""
    spec = default_registry.get("linus.knowledge.get_paper")
    assert spec is not None
    params = spec.parameters
    assert params["properties"]["sha256"] == {"type": "string"}
    assert params["required"] == ["sha256"]


def test_registered_search_papers_is_callable_via_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end dispatch: ``call_tool("linus.knowledge.search_papers",
    {...})`` invokes the underlying function with a real fake adapter and
    returns the dict-list. Mirrors what the FastAPI server does when the
    model emits a ``tool_calls`` entry."""
    paper = _make_paper(sha256="1" * 64, title="Dispatched", year=2025)
    fake = _FakeAdapter(search_return=[paper])
    monkeypatch.setattr(kb_tools, "_adapter", fake)

    result = default_registry.call_tool(
        "linus.knowledge.search_papers",
        {"query": "algae", "limit": 3},
    )
    assert isinstance(result, list)
    assert result[0]["title"] == "Dispatched"
    assert fake.calls == [("search_papers", ("algae",), {"limit": 3})]


def test_registered_get_paper_is_callable_via_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end dispatch for ``get_paper``."""
    paper = _make_paper(sha256="2" * 64, title="By hash", year=2025)
    fake = _FakeAdapter(get_return=paper)
    monkeypatch.setattr(kb_tools, "_adapter", fake)

    result = default_registry.call_tool(
        "linus.knowledge.get_paper",
        {"sha256": "2" * 64},
    )
    assert isinstance(result, dict)
    assert result["sha256"] == "2" * 64
    assert result["title"] == "By hash"


def test_kb_tools_advertised_in_openai_specs() -> None:
    """The OpenAI function-envelope serialization includes both KB tools so
    the FastAPI server can forward them to Ollama as the ``tools=[...]``
    array in chat-completion requests."""
    specs = default_registry.openai_specs()
    names = [s["function"]["name"] for s in specs]
    assert "linus.knowledge.search_papers" in names
    assert "linus.knowledge.get_paper" in names
