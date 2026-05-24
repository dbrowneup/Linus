"""Read-only adapter over the KnowledgeBase ``metadata.db`` SQLite store.

The KnowledgeBase project (``modules/KnowledgeBase/``) is the corpus-of-record for
Dan's paper library: 16k+ rows in ``data/metadata.db`` keyed by SHA256 hash of each
PDF, with columns covering bibliographic metadata (title, authors, year, journal,
abstract, DOI, etc.) plus per-file features (page count, total words, is_supplement,
is_book). The schema is defined in ``modules/KnowledgeBase/papers_analysis/metadata.py``.

This adapter wraps that database from the Linus side with three hard invariants:

1. **Read-only.** SQLite is opened via the ``file:...?mode=ro`` URI form; the
   connection cannot issue writes even if a bug attempted one. This honors the
   ROADMAP 2c constraint that Linus "does NOT mutate KnowledgeBase state."
2. **Graceful absence.** If the submodule is not initialized or ``metadata.db`` has
   not been built yet (it is a ~40 MB local artifact, gitignored upstream), the
   adapter raises :class:`KnowledgeBaseUnavailableError` with a clear pointer to
   the remediation command (``git submodule update --init`` and/or
   ``python -m papers_analysis.metadata`` inside the KB checkout).
3. **No upstream dependencies.** The KB submodule ships heavy ML deps (SPECTER2,
   BERTopic, sentence-transformers). The adapter pulls in nothing from
   ``papers_analysis``; it is pure stdlib ``sqlite3``.

The v0 search uses ``LIKE %query%`` against title and abstract. This is intentionally
simple — SPECTER2 embedding search lands in a separate Phase 2c item, and the dual
substrate (SPARQL + property graph) lands in Phase 2f. See
``docs/specs/2026-05-12-linus-implementation-plan.md`` Item 5 for the bootstrap scope.
"""

from __future__ import annotations

import contextlib
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

# Default location of the KB metadata DB relative to the Linus repo root. The repo root
# is two levels up from this file: ``src/linus/knowledge/adapter.py`` → ``Linus/``.
_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_METADATA_DB = _REPO_ROOT / "modules" / "KnowledgeBase" / "data" / "metadata.db"

# Columns selected from the ``papers`` table. Kept explicit (not ``SELECT *``) so the
# adapter is robust to upstream column additions (e.g. ``doi_pdf``, ``doi_conflict``
# added by the ``--enrich`` pass) and so the :class:`Paper` dataclass stays stable.
_PAPER_COLUMNS = (
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


class KnowledgeBaseUnavailableError(RuntimeError):
    """Raised when the KnowledgeBase metadata DB cannot be opened.

    Most common cause: the ``modules/KnowledgeBase`` submodule is not initialized, or
    ``metadata.db`` has not been built yet inside it. The exception message includes
    the remediation steps so callers can surface them to the user verbatim.
    """


@dataclass(frozen=True)
class Paper:
    """A single row from the KnowledgeBase ``papers`` table.

    All bibliographic fields are nullable upstream (only ``sha256`` is guaranteed),
    so every field except ``sha256`` is ``Optional``. ``authors`` is stored as a
    ``"; "``-joined string upstream; callers that need a list should split on
    ``"; "`` themselves to preserve fidelity with the source data.
    """

    sha256: str
    filename: str | None = None
    is_supplement: bool = False
    is_book: bool = False
    size_mb: float | None = None
    page_count: int | None = None
    total_words: int | None = None
    title: str | None = None
    authors: str | None = None
    year: int | None = None
    journal: str | None = None
    abstract: str | None = None
    doi: str | None = None
    pmid: str | None = None
    pmcid: str | None = None
    url: str | None = None
    volume: str | None = None
    pagination: str | None = None
    issn: str | None = None
    papers_id: str | None = None
    metadata_source: str | None = None
    crossref_score: float | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Paper:
        """Build a :class:`Paper` from a ``sqlite3.Row``.

        ``is_supplement`` / ``is_book`` are stored as ``INTEGER`` (0/1) upstream;
        coerce to ``bool`` here so Python callers get the natural type.
        """

        def get(col: str):
            try:
                return row[col]
            except (IndexError, KeyError):
                return None

        return cls(
            sha256=row["sha256"],
            filename=get("filename"),
            is_supplement=bool(get("is_supplement") or 0),
            is_book=bool(get("is_book") or 0),
            size_mb=get("size_mb"),
            page_count=get("page_count"),
            total_words=get("total_words"),
            title=get("title"),
            authors=get("authors"),
            year=get("year"),
            journal=get("journal"),
            abstract=get("abstract"),
            doi=get("doi"),
            pmid=get("pmid"),
            pmcid=get("pmcid"),
            url=get("url"),
            volume=get("volume"),
            pagination=get("pagination"),
            issn=get("issn"),
            papers_id=get("papers_id"),
            metadata_source=get("metadata_source"),
            crossref_score=get("crossref_score"),
        )


@dataclass
class KnowledgeBaseAdapter:
    """Read-only handle on the KnowledgeBase metadata DB.

    Example::

        from linus.knowledge import KnowledgeBaseAdapter

        kb = KnowledgeBaseAdapter()
        hits = kb.search_papers("nitrogen limitation lipid productivity", limit=5)
        for paper in hits:
            print(paper.year, paper.title)

        paper = kb.get_paper("<sha256-hex>")
        if paper:
            print(paper.title, paper.doi)

    The adapter opens the SQLite database lazily on first query and reuses one
    read-only connection thereafter. Use :meth:`close` (or the context-manager form
    ``with KnowledgeBaseAdapter() as kb: ...``) to release the connection
    deterministically; otherwise garbage collection will close it.
    """

    db_path: Path = field(default_factory=lambda: DEFAULT_METADATA_DB)
    _conn: sqlite3.Connection | None = field(default=None, init=False, repr=False)

    # --- connection lifecycle -------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Open the SQLite connection in read-only mode (idempotent).

        Uses the ``file:...?mode=ro`` URI form via ``sqlite3.connect(..., uri=True)``;
        SQLite enforces read-only at the engine level, so even a bug attempting an
        ``INSERT`` would raise rather than mutate the upstream database.
        """
        if self._conn is not None:
            return self._conn

        if not self.db_path.exists():
            raise KnowledgeBaseUnavailableError(
                f"KnowledgeBase metadata DB not found at {self.db_path}.\n"
                "If the submodule is not initialized, run:\n"
                "    git submodule update --init modules/KnowledgeBase\n"
                "If the submodule is initialized but the DB has not been built yet, run:\n"
                "    cd modules/KnowledgeBase && python -m papers_analysis.metadata\n"
                "(see modules/KnowledgeBase/CLAUDE.md for the full pipeline.)"
            )

        # ``mode=ro`` makes the connection read-only at the SQLite engine level.
        # ``immutable=1`` could be used for additional speed on a known-static DB, but
        # we intentionally leave it off so the adapter picks up changes if Dan rebuilds
        # the metadata DB in the KB checkout without restarting Linus.
        uri = f"file:{self.db_path}?mode=ro"
        try:
            conn = sqlite3.connect(uri, uri=True)
        except sqlite3.OperationalError as exc:
            raise KnowledgeBaseUnavailableError(
                f"Failed to open KnowledgeBase metadata DB at {self.db_path}: {exc}"
            ) from exc

        conn.row_factory = sqlite3.Row
        self._conn = conn
        return conn

    def close(self) -> None:
        """Close the underlying SQLite connection if it was opened."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> KnowledgeBaseAdapter:
        # Trigger the connection eagerly so opening errors surface inside ``with``.
        self._connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self) -> None:
        """Best-effort cleanup if the caller forgot ``close()`` / ``with`` (#107 H4).

        ``__del__`` runs when CPython's refcount drops to zero, which is
        deterministic in CPython but not on PyPy and not under GC
        pressure. It is therefore a defensive fallback, not the contract.
        The class docstring still asks callers to use ``close()`` or the
        context-manager form; this hook just narrows the leak window
        when they don't.

        Wrapped in ``contextlib.suppress`` because ``__del__`` runs at
        interpreter shutdown where module references may already be torn
        down, and because the connection may have been closed or
        invalidated by other means. Never let ``__del__`` raise —
        CPython's resource-cleanup ignores it but emits a noisy warning,
        and at shutdown the exception may be ungettable anyway.
        """
        with contextlib.suppress(Exception):
            self.close()

    # --- queries --------------------------------------------------------------

    def search_papers(self, query: str, limit: int = 10) -> list[Paper]:
        """Keyword search on ``title`` and ``abstract`` columns.

        Splits the query on whitespace and ANDs each whitespace-separated token; a
        row matches iff every token appears (case-insensitively) somewhere in either
        ``title`` or ``abstract``. This is intentionally simple — the goal at v0 is
        "can Linus find a paper Dan knows about by a couple of memorable words" and
        nothing more. Semantic search via SPECTER2 embeddings is a separate item.

        Supplements (``is_supplement = 1``) are excluded; Dan rarely searches for
        supplements directly, and they typically share a title with their parent
        article which would flood results.

        Parameters
        ----------
        query:
            Free-form query string. Whitespace is treated as an implicit AND.
            Empty / whitespace-only queries return an empty list (rather than the
            whole corpus, which would be expensive and surprising).
        limit:
            Maximum number of rows to return. Must be a positive integer.

        Returns
        -------
        list[Paper]
            Matching rows ordered by ``year DESC`` then ``title`` so recent work
            surfaces first. Empty list on no matches or empty query.
        """
        if limit <= 0:
            raise ValueError(f"limit must be positive, got {limit}")

        tokens = [t for t in query.split() if t]
        if not tokens:
            return []

        conn = self._connect()

        # Build AND-of-OR-of-LIKE clauses: each token must appear in title OR abstract.
        # ``LIKE`` is case-insensitive by default in SQLite for ASCII; for the kind of
        # English/Latin-script queries Dan's corpus contains this is sufficient.
        clauses = []
        params: list[str] = []
        for token in tokens:
            clauses.append("(title LIKE ? OR abstract LIKE ?)")
            like = f"%{token}%"
            params.extend([like, like])

        where = " AND ".join(clauses)
        cols = ", ".join(_PAPER_COLUMNS)
        sql = (
            f"SELECT {cols} FROM papers "
            f"WHERE is_supplement = 0 AND ({where}) "
            "ORDER BY year DESC NULLS LAST, title "
            "LIMIT ?"
        )
        params.append(limit)

        try:
            rows = conn.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            # Older SQLite builds (pre-3.30) do not support ``NULLS LAST``. Retry
            # without it; ``year DESC`` alone is fine — NULL years just sort to the
            # head, which is a cosmetic difference, not a correctness one.
            sql_fallback = (
                f"SELECT {cols} FROM papers WHERE is_supplement = 0 AND ({where}) ORDER BY year DESC, title LIMIT ?"
            )
            rows = conn.execute(sql_fallback, params).fetchall()

        return [Paper.from_row(row) for row in rows]

    def get_paper(self, sha256: str) -> Paper | None:
        """Fetch a single paper by SHA256 hash.

        The SHA256 hash of the PDF file is the primary key in the KB's ``papers``
        table — it is the same hash the Papers app uses to join its DB rows to the
        actual PDF on disk.

        Parameters
        ----------
        sha256:
            64-char lowercase hex SHA256 hash. Case is normalized to lowercase
            before lookup, but no other validation is performed.

        Returns
        -------
        Paper | None
            The matching row, or ``None`` if no paper has that hash.
        """
        if not sha256:
            return None

        conn = self._connect()
        cols = ", ".join(_PAPER_COLUMNS)
        row = conn.execute(
            f"SELECT {cols} FROM papers WHERE sha256 = ? LIMIT 1",
            (sha256.lower(),),
        ).fetchone()

        return Paper.from_row(row) if row is not None else None

    # --- introspection --------------------------------------------------------

    def count_papers(self) -> int:
        """Return the total number of rows in the ``papers`` table.

        Useful for the demo script and for sanity-checking that the DB loaded
        correctly. Not part of the documented Phase 2c tool surface.
        """
        conn = self._connect()
        (count,) = conn.execute("SELECT COUNT(*) FROM papers").fetchone()
        return int(count)
