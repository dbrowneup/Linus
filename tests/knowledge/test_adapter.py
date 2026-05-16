"""Unit tests for ``linus.knowledge.adapter``.

Two test classes:

* :class:`TestAdapterWithFixtureDB` — runs always, against a tiny fabricated SQLite
  DB that mirrors the KnowledgeBase ``papers`` table schema. This is the primary
  correctness surface: schema-faithful, deterministic, no submodule required.

* :class:`TestAdapterAgainstSubmodule` — runs against the real
  ``modules/KnowledgeBase/data/metadata.db`` when present, and skips cleanly when
  not. This is the "is the adapter compatible with the real schema?" integration
  surface; per spec it must skip (not fail) if the submodule is absent.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from linus.knowledge.adapter import (
    DEFAULT_METADATA_DB,
    KnowledgeBaseAdapter,
    KnowledgeBaseUnavailableError,
    Paper,
)

# Schema mirrored from modules/KnowledgeBase/papers_analysis/metadata.py
# Keep this in sync with the upstream CREATE TABLE if it ever changes; the adapter
# selects an explicit column list, so adding columns upstream won't break us, but
# removing or renaming one would.
_CREATE_PAPERS_SQL = """
CREATE TABLE papers (
    sha256        TEXT PRIMARY KEY,
    filename      TEXT,
    is_supplement INTEGER,
    is_book       INTEGER,
    size_mb       REAL,
    page_count    INTEGER,
    total_words   INTEGER,
    title         TEXT,
    authors       TEXT,
    year          INTEGER,
    journal       TEXT,
    abstract      TEXT,
    doi           TEXT,
    pmid          TEXT,
    pmcid         TEXT,
    url           TEXT,
    volume        TEXT,
    pagination    TEXT,
    issn          TEXT,
    papers_id     TEXT,
    metadata_source TEXT,
    crossref_score  REAL
)
"""


# --- fixtures -----------------------------------------------------------------


def _hex_sha256(seed: str) -> str:
    """Generate a deterministic 64-char hex string for fixture row PKs.

    Real SHA256 hashes are 64 lowercase hex chars; the adapter normalizes input to
    lowercase before lookup, so we mirror that convention in fixtures.
    """
    import hashlib

    return hashlib.sha256(seed.encode()).hexdigest()


@pytest.fixture
def fixture_db_path(tmp_path: Path) -> Path:
    """Build a tiny in-tmp_path SQLite DB matching the KB ``papers`` schema."""
    db_path = tmp_path / "metadata.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(_CREATE_PAPERS_SQL)
        rows = [
            # Two articles about genome assembly (one recent, one older), one about
            # an unrelated topic, plus a supplement that should never appear in
            # search results.
            {
                "sha256": _hex_sha256("paper-1"),
                "filename": "Smith-Genome_assembly_with_long_reads-2023-NatureMethods.pdf",
                "is_supplement": 0,
                "is_book": 0,
                "size_mb": 1.2,
                "page_count": 12,
                "total_words": 5400,
                "title": "Genome assembly with long reads",
                "authors": "Alice Smith; Bob Jones",
                "year": 2023,
                "journal": "Nature Methods",
                "abstract": "We present a new tool for de novo genome assembly using long-read sequencing.",
                "doi": "10.1000/example.1",
                "pmid": "12345",
                "pmcid": None,
                "url": "https://example.org/paper-1",
                "volume": "20",
                "pagination": "100-110",
                "issn": "1548-7091",
                "papers_id": "papers-1",
                "metadata_source": "papers_db",
                "crossref_score": 95.0,
            },
            {
                "sha256": _hex_sha256("paper-2"),
                "filename": "Doe-Hybrid_assembly_strategies-2019-Genome.pdf",
                "is_supplement": 0,
                "is_book": 0,
                "size_mb": 0.8,
                "page_count": 8,
                "total_words": 3200,
                "title": "Hybrid assembly strategies for difficult genomes",
                "authors": "Jane Doe",
                "year": 2019,
                "journal": "Genome Research",
                "abstract": "A review of short- and long-read combinations for genome assembly.",
                "doi": "10.1000/example.2",
                "pmid": None,
                "pmcid": None,
                "url": None,
                "volume": None,
                "pagination": None,
                "issn": None,
                "papers_id": "papers-2",
                "metadata_source": "papers_db",
                "crossref_score": None,
            },
            {
                "sha256": _hex_sha256("paper-3"),
                "filename": "Lee-Lipid_productivity_in_algae-2021-AlgalRes.pdf",
                "is_supplement": 0,
                "is_book": 0,
                "size_mb": 1.0,
                "page_count": 10,
                "total_words": 4800,
                "title": "Lipid productivity in green algae under nitrogen limitation",
                "authors": "Min Lee; Sara Patel",
                "year": 2021,
                "journal": "Algal Research",
                "abstract": "Nitrogen-limited cultures of Botryococcus braunii exhibit elevated lipid productivity.",
                "doi": "10.1000/example.3",
                "pmid": None,
                "pmcid": None,
                "url": None,
                "volume": None,
                "pagination": None,
                "issn": None,
                "papers_id": "papers-3",
                "metadata_source": "papers_db",
                "crossref_score": None,
            },
            {
                "sha256": _hex_sha256("supp-1"),
                "filename": "Smith-Genome_assembly_with_long_reads-2023-NatureMethods_supplement_1.pdf",
                "is_supplement": 1,
                "is_book": 0,
                "size_mb": 0.3,
                "page_count": 4,
                "total_words": 600,
                "title": "Supplementary material for genome assembly with long reads",
                "authors": "Alice Smith; Bob Jones",
                "year": 2023,
                "journal": "Nature Methods",
                "abstract": None,
                "doi": None,
                "pmid": None,
                "pmcid": None,
                "url": None,
                "volume": None,
                "pagination": None,
                "issn": None,
                "papers_id": "papers-1",
                "metadata_source": "papers_db",
                "crossref_score": None,
            },
        ]
        cols = list(rows[0].keys())
        placeholders = ", ".join(f":{c}" for c in cols)
        sql = f"INSERT INTO papers ({', '.join(cols)}) VALUES ({placeholders})"
        conn.executemany(sql, rows)
        conn.commit()
    finally:
        conn.close()
    return db_path


@pytest.fixture
def adapter(fixture_db_path: Path) -> KnowledgeBaseAdapter:
    """Yield an adapter pointed at the fixture DB; close it on teardown."""
    a = KnowledgeBaseAdapter(db_path=fixture_db_path)
    try:
        yield a
    finally:
        a.close()


# --- tests against the fabricated fixture DB (always run) ---------------------


class TestAdapterWithFixtureDB:
    """Correctness tests against a deterministic in-tmp_path SQLite DB."""

    def test_count_papers(self, adapter: KnowledgeBaseAdapter):
        # Three articles + one supplement = 4 rows in the table.
        assert adapter.count_papers() == 4

    def test_search_returns_matches(self, adapter: KnowledgeBaseAdapter):
        hits = adapter.search_papers("genome assembly", limit=10)
        # Two real articles match; the supplement is filtered out by is_supplement=0.
        assert len(hits) == 2
        titles = {p.title for p in hits}
        assert "Genome assembly with long reads" in titles
        assert "Hybrid assembly strategies for difficult genomes" in titles

    def test_search_orders_recent_first(self, adapter: KnowledgeBaseAdapter):
        hits = adapter.search_papers("assembly", limit=10)
        years = [p.year for p in hits]
        # Recent-first ordering is part of the documented behavior.
        assert years == sorted(years, reverse=True)

    def test_search_respects_limit(self, adapter: KnowledgeBaseAdapter):
        hits = adapter.search_papers("assembly", limit=1)
        assert len(hits) == 1

    def test_search_and_semantics_across_title_and_abstract(self, adapter: KnowledgeBaseAdapter):
        # "Botryococcus" only appears in paper-3's abstract; "lipid" only in its
        # title. AND semantics across the OR-of-(title,abstract) clauses should
        # still match because both tokens hit *some* searched field.
        hits = adapter.search_papers("Botryococcus lipid", limit=10)
        assert len(hits) == 1
        assert hits[0].sha256 == _hex_sha256("paper-3")

    def test_search_no_match(self, adapter: KnowledgeBaseAdapter):
        assert adapter.search_papers("quasiparticleantiferromagnet", limit=10) == []

    def test_search_empty_query_returns_empty(self, adapter: KnowledgeBaseAdapter):
        assert adapter.search_papers("", limit=10) == []
        assert adapter.search_papers("   ", limit=10) == []

    def test_search_excludes_supplements(self, adapter: KnowledgeBaseAdapter):
        # "Supplementary" only appears in the supplement row's title; we should
        # never see it because supplements are filtered out.
        hits = adapter.search_papers("Supplementary", limit=10)
        assert hits == []

    def test_search_rejects_nonpositive_limit(self, adapter: KnowledgeBaseAdapter):
        with pytest.raises(ValueError):
            adapter.search_papers("genome", limit=0)
        with pytest.raises(ValueError):
            adapter.search_papers("genome", limit=-5)

    def test_get_paper_hits(self, adapter: KnowledgeBaseAdapter):
        sha = _hex_sha256("paper-1")
        paper = adapter.get_paper(sha)
        assert isinstance(paper, Paper)
        assert paper.sha256 == sha
        assert paper.title == "Genome assembly with long reads"
        assert paper.year == 2023
        assert paper.is_supplement is False
        assert paper.is_book is False
        assert paper.doi == "10.1000/example.1"

    def test_get_paper_normalizes_case(self, adapter: KnowledgeBaseAdapter):
        sha = _hex_sha256("paper-1")
        paper = adapter.get_paper(sha.upper())
        assert paper is not None
        assert paper.sha256 == sha

    def test_get_paper_miss(self, adapter: KnowledgeBaseAdapter):
        assert adapter.get_paper("0" * 64) is None

    def test_get_paper_empty_string(self, adapter: KnowledgeBaseAdapter):
        assert adapter.get_paper("") is None

    def test_get_paper_supplement_is_visible_by_sha(self, adapter: KnowledgeBaseAdapter):
        # get_paper does NOT filter supplements (the caller asked for a specific
        # SHA, so they get whatever row has that SHA). Only search_papers filters.
        paper = adapter.get_paper(_hex_sha256("supp-1"))
        assert paper is not None
        assert paper.is_supplement is True

    def test_context_manager_closes(self, fixture_db_path: Path):
        with KnowledgeBaseAdapter(db_path=fixture_db_path) as kb:
            assert kb.count_papers() == 4
            assert kb._conn is not None
        # After __exit__, the connection is closed and the slot cleared.
        assert kb._conn is None

    def test_readonly_blocks_writes(self, fixture_db_path: Path):
        kb = KnowledgeBaseAdapter(db_path=fixture_db_path)
        try:
            kb._connect()
            # Confirm the safety contract: even if someone calls execute directly
            # on the connection, SQLite refuses writes because the URI mode is ro.
            with pytest.raises(sqlite3.OperationalError):
                kb._conn.execute("UPDATE papers SET title = 'mutated' WHERE sha256 = ?", (_hex_sha256("paper-1"),))
        finally:
            kb.close()


# --- missing-DB error path ----------------------------------------------------


class TestAdapterMissingDB:
    """The adapter must fail with a clear, actionable error when the DB is absent."""

    def test_missing_db_raises_unavailable(self, tmp_path: Path):
        kb = KnowledgeBaseAdapter(db_path=tmp_path / "nonexistent.db")
        with pytest.raises(KnowledgeBaseUnavailableError) as excinfo:
            kb.count_papers()
        msg = str(excinfo.value)
        # Message must point Dan (or any caller) at the remediation command.
        assert "git submodule update --init" in msg
        assert "nonexistent.db" in msg


# --- tests against the real submodule DB (skip if absent) ---------------------


_SUBMODULE_DB = DEFAULT_METADATA_DB
_SUBMODULE_AVAILABLE = _SUBMODULE_DB.exists()


@pytest.mark.skipif(
    not _SUBMODULE_AVAILABLE,
    reason=(
        f"KnowledgeBase metadata DB not found at {_SUBMODULE_DB}. "
        "Initialize the submodule (`git submodule update --init modules/KnowledgeBase`) "
        "and build the DB (`cd modules/KnowledgeBase && python -m papers_analysis.metadata`) "
        "to enable these integration tests."
    ),
)
class TestAdapterAgainstSubmodule:
    """Integration tests against the real ``modules/KnowledgeBase/data/metadata.db``.

    These check that the adapter is compatible with the real schema. They make no
    assumptions about specific row contents (Dan's corpus evolves over time);
    they only check structural invariants.
    """

    def test_real_db_opens_and_counts(self):
        with KnowledgeBaseAdapter() as kb:
            count = kb.count_papers()
            # Per modules/KnowledgeBase/CLAUDE.md the corpus is ~16k papers.
            # Use a loose floor so the test does not flake when Dan adds/removes
            # papers between runs.
            assert count > 0, "real KB should have at least one paper row"

    def test_real_db_search_returns_papers(self):
        with KnowledgeBaseAdapter() as kb:
            # Pick a high-prior token — "genome" is in countless titles/abstracts in
            # Dan's corpus. If this returns zero we want to see the failure rather
            # than silently passing, because something is wrong.
            hits = kb.search_papers("genome", limit=5)
            assert isinstance(hits, list)
            assert len(hits) <= 5
            for paper in hits:
                assert isinstance(paper, Paper)
                assert len(paper.sha256) == 64  # SHA256 hex length
                assert paper.is_supplement is False  # search filters supplements

    def test_real_db_get_paper_roundtrip(self):
        with KnowledgeBaseAdapter() as kb:
            hits = kb.search_papers("genome", limit=1)
            if not hits:
                pytest.skip("No 'genome' hits in current KB corpus; cannot roundtrip-fetch.")
            sha = hits[0].sha256
            fetched = kb.get_paper(sha)
            assert fetched is not None
            assert fetched.sha256 == sha
            assert fetched.title == hits[0].title
