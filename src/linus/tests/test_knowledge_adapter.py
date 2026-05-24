"""Tests for :mod:`linus.knowledge.adapter` — the read-only KnowledgeBase gateway.

The adapter is the single integration surface between Linus and the upstream
KnowledgeBase ``metadata.db`` SQLite store. Three hard invariants must hold:

1. **Read-only.** The connection is opened with ``mode=ro`` — even an attempted
   ``INSERT`` raises rather than mutates upstream state.
2. **Graceful absence.** A missing DB raises :class:`KnowledgeBaseUnavailableError`
   with a clear remediation pointer.
3. **Stable surface.** ``Paper.from_row`` tolerates schema additions and
   missing optional columns; ``search_papers`` falls back when ``NULLS LAST``
   is unsupported by an older SQLite build.

The suite is fully hermetic — every test creates an ephemeral SQLite DB inside
``tmp_path``. No network, no submodule, no external dependencies.
"""

from __future__ import annotations

import sqlite3
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from linus.knowledge.adapter import (
    DEFAULT_METADATA_DB,
    KnowledgeBaseAdapter,
    KnowledgeBaseUnavailableError,
    Paper,
)

# Columns the adapter projects in SELECT — must match ``_PAPER_COLUMNS`` in the
# module. Kept duplicated here so a schema drift in either place produces a
# loud test failure rather than silent under-projection.
_FULL_COLUMNS = (
    "sha256",
    "filename",
    "is_supplement",
    "is_book",
    "size_mb",
    "page_count",
    "total_words",
    "title",
    "authors",
    "year",
    "journal",
    "abstract",
    "doi",
    "pmid",
    "pmcid",
    "url",
    "volume",
    "pagination",
    "issn",
    "papers_id",
    "metadata_source",
    "crossref_score",
)


# ── DB-building helpers ────────────────────────────────────────────────────


def _build_papers_db(
    db_path: Path,
    rows: list[dict] | None = None,
    *,
    columns: tuple[str, ...] = _FULL_COLUMNS,
) -> None:
    """Create a SQLite DB at ``db_path`` with a ``papers`` table.

    ``columns`` lets a test omit columns to exercise the ``from_row``
    tolerant-fallback path; ``rows`` is a list of dicts whose keys must be a
    subset of ``columns``.
    """
    conn = sqlite3.connect(db_path)
    col_defs = []
    for col in columns:
        if col == "sha256":
            col_defs.append(f"{col} TEXT PRIMARY KEY")
        elif col in {"is_supplement", "is_book", "page_count", "total_words", "year"}:
            col_defs.append(f"{col} INTEGER")
        elif col in {"size_mb", "crossref_score"}:
            col_defs.append(f"{col} REAL")
        else:
            col_defs.append(f"{col} TEXT")
    conn.execute(f"CREATE TABLE papers ({', '.join(col_defs)})")

    if rows:
        placeholders = ", ".join("?" for _ in columns)
        col_list = ", ".join(columns)
        for row in rows:
            values = [row.get(col) for col in columns]
            conn.execute(
                f"INSERT INTO papers ({col_list}) VALUES ({placeholders})",
                values,
            )

    conn.commit()
    conn.close()


@pytest.fixture
def populated_db(tmp_path: Path) -> Path:
    """An ephemeral KB DB seeded with three realistic-shaped papers.

    Spans the bool, NULL, and is_supplement filtering branches.
    """
    db_path = tmp_path / "metadata.db"
    rows = [
        {
            "sha256": "a" * 64,
            "filename": "long-read.pdf",
            "is_supplement": 0,
            "is_book": 0,
            "size_mb": 2.5,
            "page_count": 12,
            "total_words": 4200,
            "title": "Long-read sequencing of microbial genomes",
            "authors": "Smith, J; Doe, A",
            "year": 2024,
            "journal": "Nature",
            "abstract": "We describe a PacBio HiFi pipeline for microbial assembly.",
            "doi": "10.1000/aaa",
            "pmid": "12345",
            "pmcid": "PMC1",
            "url": "https://example.com/a",
            "volume": "11",
            "pagination": "1-10",
            "issn": "1234-5678",
            "papers_id": "p-aaa",
            "metadata_source": "crossref",
            "crossref_score": 90.0,
        },
        {
            "sha256": "b" * 64,
            "filename": "short-read.pdf",
            "is_supplement": 0,
            "is_book": 0,
            "size_mb": 1.1,
            "page_count": 8,
            "total_words": None,  # exercises NULL handling
            "title": "Short-read assembly methods compared",
            "authors": None,
            "year": 2018,
            "journal": "Bioinformatics",
            "abstract": "Methods for short-read assembly across species.",
            "doi": None,
            "pmid": None,
            "pmcid": None,
            "url": None,
            "volume": None,
            "pagination": None,
            "issn": None,
            "papers_id": None,
            "metadata_source": None,
            "crossref_score": None,
        },
        {
            "sha256": "c" * 64,
            "filename": "supp.pdf",
            "is_supplement": 1,  # excluded from search_papers
            "is_book": 0,
            "size_mb": 0.5,
            "page_count": 4,
            "total_words": 800,
            "title": "Supplementary information for long-read paper",
            "authors": "Smith, J",
            "year": 2024,
            "journal": "Nature",
            "abstract": "Supplementary PacBio data tables.",
            "doi": "10.1000/aaa-supp",
            "pmid": None,
            "pmcid": None,
            "url": None,
            "volume": None,
            "pagination": None,
            "issn": None,
            "papers_id": None,
            "metadata_source": "crossref",
            "crossref_score": None,
        },
    ]
    _build_papers_db(db_path, rows)
    return db_path


@pytest.fixture
def empty_db(tmp_path: Path) -> Path:
    """A KB DB with the papers table schema but zero rows."""
    db_path = tmp_path / "metadata.db"
    _build_papers_db(db_path, rows=[])
    return db_path


# ── Module-level constants ─────────────────────────────────────────────────


def test_default_metadata_db_resolves_to_repo_modules_path() -> None:
    """``DEFAULT_METADATA_DB`` must point at ``modules/KnowledgeBase/data/metadata.db``
    relative to the Linus repo root — the canonical upstream location."""
    assert DEFAULT_METADATA_DB.name == "metadata.db"
    parts = DEFAULT_METADATA_DB.parts
    assert "modules" in parts
    assert "KnowledgeBase" in parts
    assert "data" in parts


# ── Paper dataclass + from_row ────────────────────────────────────────────


def test_paper_defaults_only_sha_required() -> None:
    """``sha256`` is the only required field; everything else defaults to None/False."""
    paper = Paper(sha256="deadbeef")
    assert paper.sha256 == "deadbeef"
    assert paper.title is None
    assert paper.authors is None
    assert paper.is_supplement is False
    assert paper.is_book is False
    assert paper.crossref_score is None


def test_paper_is_frozen() -> None:
    """``Paper`` is frozen — attribute mutation must raise."""
    paper = Paper(sha256="x")
    with pytest.raises(FrozenInstanceError):
        paper.title = "mutated"  # type: ignore[misc]


def test_paper_from_row_happy_path(populated_db: Path) -> None:
    """``from_row`` extracts every column from a row containing all of them."""
    conn = sqlite3.connect(populated_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        f"SELECT {', '.join(_FULL_COLUMNS)} FROM papers WHERE sha256 = ?",
        ("a" * 64,),
    ).fetchone()
    conn.close()

    paper = Paper.from_row(row)
    assert paper.sha256 == "a" * 64
    assert paper.title == "Long-read sequencing of microbial genomes"
    assert paper.authors == "Smith, J; Doe, A"
    assert paper.year == 2024
    assert paper.size_mb == 2.5
    assert paper.is_supplement is False
    assert paper.is_book is False
    assert paper.crossref_score == 90.0


def test_paper_from_row_coerces_is_supplement_to_bool(populated_db: Path) -> None:
    """``is_supplement = 1`` (INTEGER upstream) must coerce to bool True."""
    conn = sqlite3.connect(populated_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        f"SELECT {', '.join(_FULL_COLUMNS)} FROM papers WHERE sha256 = ?",
        ("c" * 64,),
    ).fetchone()
    conn.close()

    paper = Paper.from_row(row)
    assert paper.is_supplement is True
    assert paper.is_book is False  # 0 → False


def test_paper_from_row_null_columns_pass_through(populated_db: Path) -> None:
    """A row whose optional fields are NULL produces a Paper with None values."""
    conn = sqlite3.connect(populated_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        f"SELECT {', '.join(_FULL_COLUMNS)} FROM papers WHERE sha256 = ?",
        ("b" * 64,),
    ).fetchone()
    conn.close()

    paper = Paper.from_row(row)
    assert paper.sha256 == "b" * 64
    assert paper.total_words is None
    assert paper.authors is None
    assert paper.doi is None
    assert paper.crossref_score is None


def test_paper_from_row_tolerates_missing_columns(tmp_path: Path) -> None:
    """The ``get()`` helper inside ``from_row`` must swallow ``IndexError`` /
    ``KeyError`` when a row was selected from a schema-mismatched query — i.e.
    the row genuinely lacks the column. This guards the adapter against upstream
    column removals and is the canonical "schema-mismatch" branch (lines 119-125).
    """
    db_path = tmp_path / "narrow.db"
    # Minimal schema: only sha256 + title; every other adapter-referenced column missing.
    _build_papers_db(
        db_path,
        rows=[{"sha256": "z" * 64, "title": "Sparse row"}],
        columns=("sha256", "title"),
    )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT sha256, title FROM papers").fetchone()
    conn.close()

    paper = Paper.from_row(row)
    assert paper.sha256 == "z" * 64
    assert paper.title == "Sparse row"
    # Every missing column collapses to its default; bool fields default False.
    assert paper.authors is None
    assert paper.year is None
    assert paper.is_supplement is False
    assert paper.is_book is False


# ── Connection lifecycle: _connect, close, __enter__/__exit__ ─────────────


def test_connect_raises_with_remediation_when_db_missing(tmp_path: Path) -> None:
    """A missing DB file raises ``KnowledgeBaseUnavailableError`` with a message
    listing the canonical remediation commands (``git submodule update`` and
    ``python -m papers_analysis.metadata``)."""
    missing = tmp_path / "does-not-exist.db"
    adapter = KnowledgeBaseAdapter(db_path=missing)
    with pytest.raises(KnowledgeBaseUnavailableError) as exc_info:
        adapter._connect()
    msg = str(exc_info.value)
    assert str(missing) in msg
    assert "git submodule update --init" in msg
    assert "papers_analysis.metadata" in msg


def test_connect_wraps_sqlite_operational_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """If ``sqlite3.connect`` raises ``OperationalError`` (e.g. permissions,
    locked file), the adapter must wrap it as :class:`KnowledgeBaseUnavailableError`
    and chain the original via ``__cause__`` (lines 206-209)."""
    db_path = tmp_path / "metadata.db"
    _build_papers_db(db_path, rows=[])

    def fake_connect(*args, **kwargs):
        raise sqlite3.OperationalError("unable to open database file")

    monkeypatch.setattr(sqlite3, "connect", fake_connect)
    adapter = KnowledgeBaseAdapter(db_path=db_path)
    with pytest.raises(KnowledgeBaseUnavailableError) as exc_info:
        adapter._connect()
    assert "Failed to open" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, sqlite3.OperationalError)


def test_connect_is_idempotent(populated_db: Path) -> None:
    """Calling ``_connect`` twice returns the same connection object (lazy cache)."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    conn1 = adapter._connect()
    conn2 = adapter._connect()
    assert conn1 is conn2
    adapter.close()


def test_connect_sets_row_factory(populated_db: Path) -> None:
    """The cached connection must have ``row_factory = sqlite3.Row`` so
    ``Paper.from_row`` can use named column access."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    conn = adapter._connect()
    assert conn.row_factory is sqlite3.Row
    adapter.close()


def test_connect_uses_readonly_uri(populated_db: Path) -> None:
    """The connection rejects writes — verifies the ``mode=ro`` URI took effect.
    Honors invariant 1 (read-only)."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    conn = adapter._connect()
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("INSERT INTO papers (sha256) VALUES ('xx')")
    adapter.close()


def test_close_releases_connection_and_is_safe_to_repeat(populated_db: Path) -> None:
    """``close`` clears the cached connection; calling it twice is a no-op."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    adapter._connect()
    assert adapter._conn is not None
    adapter.close()
    assert adapter._conn is None
    # Second close: must not raise on the None branch.
    adapter.close()
    assert adapter._conn is None


def test_close_before_connect_is_noop(populated_db: Path) -> None:
    """Closing an adapter that never opened still works."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    assert adapter._conn is None
    adapter.close()  # no-op — covers the early-return branch
    assert adapter._conn is None


def test_context_manager_opens_eagerly_and_closes_on_exit(populated_db: Path) -> None:
    """``with KnowledgeBaseAdapter() as kb:`` opens eagerly so connection
    errors surface inside the ``with`` block, and closes on exit."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    with adapter as kb:
        assert kb is adapter
        assert adapter._conn is not None
    assert adapter._conn is None


def test_context_manager_surfaces_connection_error(tmp_path: Path) -> None:
    """``__enter__`` must trigger ``_connect`` so a missing DB raises inside
    the ``with`` statement (not later when a query is made)."""
    missing = tmp_path / "absent.db"
    with pytest.raises(KnowledgeBaseUnavailableError), KnowledgeBaseAdapter(db_path=missing):
        pass


def test_context_manager_closes_on_exception(populated_db: Path) -> None:
    """Exit closes the connection even when the body raises."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    with pytest.raises(RuntimeError, match="forced"), adapter:
        assert adapter._conn is not None
        raise RuntimeError("forced")
    assert adapter._conn is None


# ── search_papers ──────────────────────────────────────────────────────────


def test_search_papers_happy_path_single_token(populated_db: Path) -> None:
    """Single-token query finds rows where the token appears in title or
    abstract (case-insensitive); supplements are excluded."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    hits = adapter.search_papers("PacBio", limit=10)
    adapter.close()

    # paper 'a' has PacBio in abstract; paper 'c' is a supplement (excluded).
    shas = {p.sha256 for p in hits}
    assert "a" * 64 in shas
    assert "c" * 64 not in shas


def test_search_papers_ands_multiple_tokens(populated_db: Path) -> None:
    """Multi-token query ANDs each token across title-or-abstract."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    # 'short' appears in paper b title; 'methods' also in paper b title.
    hits = adapter.search_papers("short methods", limit=10)
    adapter.close()
    shas = {p.sha256 for p in hits}
    assert "b" * 64 in shas
    # Paper a doesn't contain "short" → must not appear.
    assert "a" * 64 not in shas


def test_search_papers_orders_by_year_desc(populated_db: Path) -> None:
    """Hits are returned year-DESC so recent work surfaces first."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    hits = adapter.search_papers("assembly", limit=10)
    adapter.close()
    # Papers a (2024, abstract has "assembly") and b (2018, title has "assembly").
    years = [p.year for p in hits if p.year is not None]
    assert years == sorted(years, reverse=True)


def test_search_papers_excludes_supplements(populated_db: Path) -> None:
    """``is_supplement = 1`` rows must never appear."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    # 'supplementary' token would match paper c's title, but supplement filter blocks it.
    hits = adapter.search_papers("supplementary", limit=10)
    adapter.close()
    assert hits == []


def test_search_papers_empty_query_returns_empty(populated_db: Path) -> None:
    """Empty or whitespace-only query returns ``[]`` rather than the whole corpus."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    assert adapter.search_papers("", limit=5) == []
    assert adapter.search_papers("   ", limit=5) == []
    adapter.close()


def test_search_papers_no_matches_returns_empty(populated_db: Path) -> None:
    """A query with no hits returns an empty list."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    hits = adapter.search_papers("nonexistent-term-zzz", limit=5)
    adapter.close()
    assert hits == []


def test_search_papers_respects_limit(populated_db: Path) -> None:
    """``limit`` caps the returned row count."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    # Token 'assembly' matches at least papers a and b.
    hits = adapter.search_papers("assembly", limit=1)
    adapter.close()
    assert len(hits) <= 1


@pytest.mark.parametrize("bad_limit", [0, -1, -100])
def test_search_papers_rejects_non_positive_limit(populated_db: Path, bad_limit: int) -> None:
    """``limit <= 0`` must raise ``ValueError`` (line 260)."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    with pytest.raises(ValueError, match="limit must be positive"):
        adapter.search_papers("anything", limit=bad_limit)
    adapter.close()


def test_search_papers_lazy_loads_connection(populated_db: Path) -> None:
    """``search_papers`` opens the connection on first call if not already open."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    assert adapter._conn is None
    adapter.search_papers("PacBio", limit=1)
    assert adapter._conn is not None
    adapter.close()


def test_search_papers_falls_back_when_nulls_last_unsupported(populated_db: Path) -> None:
    """On a pre-3.30 SQLite that doesn't support ``NULLS LAST``, the first
    SQL raises ``OperationalError`` and the adapter retries with the simpler
    ``ORDER BY year DESC, title`` form (lines 290-300).

    Substitutes the cached SQLite connection with a thin proxy whose first
    ``execute`` raising ``OperationalError`` triggers the fallback path. We
    can't ``monkeypatch.setattr`` ``sqlite3.Connection.execute`` directly
    (it's read-only), so we wrap.
    """

    class _FlakyConn:
        """Proxy that raises ``OperationalError`` once on ``NULLS LAST`` SQL."""

        def __init__(self, real: sqlite3.Connection) -> None:
            self._real = real
            self.call_count = 0

        def execute(self, sql, params=()):
            self.call_count += 1
            if "NULLS LAST" in sql and self.call_count == 1:
                raise sqlite3.OperationalError("near 'NULLS': syntax error")
            return self._real.execute(sql, params)

        def close(self):
            return self._real.close()

    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    real_conn = adapter._connect()
    flaky = _FlakyConn(real_conn)
    adapter._conn = flaky  # type: ignore[assignment]

    hits = adapter.search_papers("assembly", limit=5)
    adapter.close()

    assert flaky.call_count == 2  # primary attempt + fallback
    assert len(hits) >= 1


def test_search_papers_returns_paper_dataclass_instances(populated_db: Path) -> None:
    """Each row is wrapped in a :class:`Paper` instance."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    hits = adapter.search_papers("PacBio", limit=5)
    adapter.close()
    assert all(isinstance(p, Paper) for p in hits)


# ── get_paper ──────────────────────────────────────────────────────────────


def test_get_paper_happy_path(populated_db: Path) -> None:
    """Existing SHA returns the matching :class:`Paper`."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    paper = adapter.get_paper("a" * 64)
    adapter.close()
    assert paper is not None
    assert paper.sha256 == "a" * 64
    assert paper.title == "Long-read sequencing of microbial genomes"


def test_get_paper_missing_returns_none(populated_db: Path) -> None:
    """Non-existent SHA returns None (NOT an exception)."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    assert adapter.get_paper("f" * 64) is None
    adapter.close()


def test_get_paper_empty_sha_returns_none(populated_db: Path) -> None:
    """Empty / falsy SHA short-circuits to None without hitting the DB
    (line 322-323)."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    assert adapter.get_paper("") is None
    # The empty-sha guard runs BEFORE _connect, so _conn stays None.
    assert adapter._conn is None
    adapter.close()


def test_get_paper_case_insensitive_lookup(populated_db: Path) -> None:
    """SHA input is lowercased before lookup, so uppercase still matches."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    paper = adapter.get_paper("A" * 64)  # uppercase
    adapter.close()
    assert paper is not None
    assert paper.sha256 == "a" * 64


def test_get_paper_lazy_loads_connection(populated_db: Path) -> None:
    """``get_paper`` opens the connection on first non-empty call."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    assert adapter._conn is None
    adapter.get_paper("a" * 64)
    assert adapter._conn is not None
    adapter.close()


# ── count_papers ───────────────────────────────────────────────────────────


def test_count_papers_happy_path(populated_db: Path) -> None:
    """``count_papers`` returns the total row count including supplements."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    assert adapter.count_papers() == 3
    adapter.close()


def test_count_papers_empty_db(empty_db: Path) -> None:
    """A zero-row DB reports a count of 0."""
    adapter = KnowledgeBaseAdapter(db_path=empty_db)
    assert adapter.count_papers() == 0
    adapter.close()


def test_count_papers_returns_int(populated_db: Path) -> None:
    """The returned count is an ``int`` (not e.g. a numpy scalar)."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    result = adapter.count_papers()
    adapter.close()
    assert isinstance(result, int)


def test_count_papers_raises_when_db_missing(tmp_path: Path) -> None:
    """``count_papers`` surfaces ``KnowledgeBaseUnavailableError`` via the
    lazy-connect path when the DB is absent."""
    adapter = KnowledgeBaseAdapter(db_path=tmp_path / "absent.db")
    with pytest.raises(KnowledgeBaseUnavailableError):
        adapter.count_papers()


# ── Read-only invariant integration ────────────────────────────────────────


def test_adapter_cannot_mutate_via_search_path(populated_db: Path) -> None:
    """The adapter exposes no public write method; even the cached SQLite
    connection (which a buggy caller could grab) rejects writes. This is the
    end-to-end honoring of invariant 1."""
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    conn = adapter._connect()
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("UPDATE papers SET title = 'tampered' WHERE sha256 = ?", ("a" * 64,))
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("DELETE FROM papers WHERE sha256 = ?", ("a" * 64,))
    adapter.close()


# ── #107 H4: resource-leak guards (__del__ + close + context-manager) ──────


def test_kb_adapter_close_releases_connection(populated_db: Path) -> None:
    """``close`` closes the cached SQLite connection so subsequent queries
    against the now-closed connection raise — proving the file handle was
    actually released (#107 H4 regression test).
    """
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    conn = adapter._connect()
    # Sanity: the freshly-opened connection works (row_factory=sqlite3.Row,
    # so column-0 access is the canonical way to read a SELECT-literal value).
    assert conn.execute("SELECT 1").fetchone()[0] == 1

    adapter.close()

    # The cached connection has been cleared, AND the underlying SQLite
    # connection object is closed (further use raises ProgrammingError).
    assert adapter._conn is None
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")


def test_kb_adapter_context_manager_closes_on_exit(populated_db: Path) -> None:
    """``with KnowledgeBaseAdapter() as kb:`` releases the connection on exit;
    the connection captured during the block is closed afterward (#107 H4).
    """
    captured_conn: sqlite3.Connection | None = None
    with KnowledgeBaseAdapter(db_path=populated_db) as adapter:
        captured_conn = adapter._conn
        assert captured_conn is not None
        # Connection works inside the block.
        assert captured_conn.execute("SELECT 1").fetchone()[0] == 1
    # After exit: adapter clears its cache, AND the captured connection is closed.
    assert adapter._conn is None
    assert captured_conn is not None
    with pytest.raises(sqlite3.ProgrammingError):
        captured_conn.execute("SELECT 1")


def test_kb_adapter_del_closes_connection(populated_db: Path) -> None:
    """The ``__del__`` finalizer closes the connection when the adapter is
    garbage-collected without ``close()`` having been called (#107 H4).

    Captures the connection out-of-band, then forces ``__del__`` by dropping
    the only reference. The captured connection must then be unusable.
    """
    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    captured_conn = adapter._connect()
    assert captured_conn.execute("SELECT 1").fetchone()[0] == 1

    # Drop the only reference to the adapter and force a collection so
    # __del__ fires deterministically rather than relying on CPython's
    # refcount-immediate behavior alone.
    import gc

    del adapter
    gc.collect()

    # The connection that the adapter held should now be closed.
    with pytest.raises(sqlite3.ProgrammingError):
        captured_conn.execute("SELECT 1")


def test_kb_adapter_del_is_safe_when_never_connected(populated_db: Path) -> None:
    """``__del__`` on an adapter whose connection was never opened must not
    raise — the ``self._conn is not None`` guard inside ``close()`` covers
    this, but exercising it via the finalizer path guards the integration
    (#107 H4 corollary).
    """
    import gc

    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    assert adapter._conn is None
    # No exceptions should be raised when the adapter is collected without
    # ever having opened a connection.
    del adapter
    gc.collect()


def test_kb_adapter_del_is_safe_when_close_already_called(populated_db: Path) -> None:
    """Calling ``close()`` then dropping the adapter must not raise from
    ``__del__`` — close already nulled ``_conn`` so the finalizer is a no-op
    (#107 H4 corollary).
    """
    import gc

    adapter = KnowledgeBaseAdapter(db_path=populated_db)
    adapter._connect()
    adapter.close()
    assert adapter._conn is None
    del adapter
    gc.collect()


def test_kb_adapter_del_swallows_close_exceptions(populated_db: Path) -> None:
    """``__del__`` must swallow any exception from ``close()`` to keep
    interpreter shutdown quiet — even if a corrupt internal state would
    otherwise raise (#107 H4 hardening).
    """
    import gc

    adapter = KnowledgeBaseAdapter(db_path=populated_db)

    # Replace the cached connection with a stub whose close() raises.
    class _ExplodingConn:
        def close(self) -> None:
            raise RuntimeError("simulated close failure")

    adapter._conn = _ExplodingConn()  # type: ignore[assignment]

    # __del__ must not propagate the exception. del + gc.collect() would
    # surface a noisy traceback if it did; the call itself is the assertion.
    del adapter
    gc.collect()
