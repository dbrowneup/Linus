"""Tests for :mod:`linus.memory.episodic` — Layer C of the memory architecture.

The episodic store is the cross-session memory pillar (DEC-0028, DEC-0029):
SQLite + content hashes + git, single-file DB at ``~/.linus/episodic.db`` by
default. This module previously had no test file. The hermetic suite below
exercises:

- :func:`default_db_path` env-override + bare default
- ``EpisodicRecord`` dataclass defaults
- :class:`EpisodicStore` construction (parent-dir creation, idempotent migrate)
- :meth:`EpisodicStore.write_record` for text / bytes / JSON payloads
  (content-hash population, rowid assignment, timestamp auto-fill, forged-hash
  overwrite, uniqueness-constraint enforcement)
- :meth:`EpisodicStore.read_records` query surface — exact-match, IN, ``limit``,
  ``order``, unsupported key rejection, invalid-order rejection, empty-IN
  short-circuit
- ``_encode_content`` / ``_decode_content`` round-trips including the
  ``ValueError`` branch for unknown content_type
- Cross-instance persistence (write in one store, read in another)
- WAL-mode + foreign_keys pragmas survive across connections

Every test uses ``tmp_path`` for an isolated DB file. No Ollama, no network,
no module-level state.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from linus.memory.episodic import (
    DEFAULT_DB_PATH,
    SCHEMA_VERSION,
    EpisodicRecord,
    EpisodicStore,
    _decode_content,
    _encode_content,
    _row_to_record,
    _utcnow,
    default_db_path,
)

# ── Module-level helpers ───────────────────────────────────────────────────


def test_default_db_path_returns_home_default_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """When ``LINUS_HOME`` is unset, :func:`default_db_path` returns the documented
    ``~/.linus/episodic.db`` default."""
    monkeypatch.delenv("LINUS_HOME", raising=False)
    assert default_db_path() == DEFAULT_DB_PATH


def test_default_db_path_honors_linus_home_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``LINUS_HOME`` redirects the default DB under that root so tests / production
    relocations don't need to monkeypatch ``Path.home``."""
    monkeypatch.setenv("LINUS_HOME", str(tmp_path))
    assert default_db_path() == tmp_path / "episodic.db"


def test_default_db_path_empty_env_falls_through_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty-string ``LINUS_HOME`` is falsy under the walrus check; the function
    falls through to the documented default rather than producing a bare
    ``./episodic.db``."""
    monkeypatch.setenv("LINUS_HOME", "")
    assert default_db_path() == DEFAULT_DB_PATH


def test_utcnow_returns_iso_8601_with_utc_offset() -> None:
    """The timestamps stored alongside records are sortable lexicographically and
    carry an explicit UTC offset so cross-platform reads can't get confused."""
    ts = _utcnow()
    assert isinstance(ts, str)
    # ISO-8601 with UTC offset; e.g. ``2026-05-19T17:23:45.123456+00:00``.
    assert "T" in ts
    assert ts.endswith("+00:00")


def test_schema_version_constant_is_positive_int() -> None:
    """SCHEMA_VERSION must be a real version number, not a placeholder."""
    assert isinstance(SCHEMA_VERSION, int)
    assert SCHEMA_VERSION >= 1


# ── _encode_content / _decode_content round-trips ──────────────────────────


def test_encode_content_text_passes_string_through() -> None:
    """``str`` content is stored verbatim with ``content_type='text'``."""
    stored, ct = _encode_content("hello world")
    assert stored == "hello world"
    assert ct == "text"


def test_encode_content_bytes_uses_hex_encoding() -> None:
    """``bytes`` content is hex-encoded so the SQLite TEXT column round-trips."""
    stored, ct = _encode_content(b"\xde\xad\xbe\xef")
    assert stored == "deadbeef"
    assert ct == "bytes"


def test_encode_content_json_canonicalizes_dict() -> None:
    """Anything that isn't ``str``/``bytes`` rides the JSON path with sorted keys
    so the encoded form is deterministic across processes."""
    stored, ct = _encode_content({"b": 1, "a": 2})
    assert ct == "json"
    # ``sort_keys=True`` means ``a`` precedes ``b``.
    assert stored == '{"a": 2, "b": 1}'


def test_encode_content_json_for_lists() -> None:
    stored, ct = _encode_content([1, 2, 3])
    assert ct == "json"
    assert stored == "[1, 2, 3]"


def test_encode_content_json_rejects_nan() -> None:
    """The hashing canonicalization disallows ``NaN``; the storage encoder follows
    the same rule (``allow_nan=False``) so DB round-trips cannot produce
    unparseable JSON."""
    with pytest.raises(ValueError):
        _encode_content({"bad": float("nan")})


def test_decode_content_text_returns_string_verbatim() -> None:
    assert _decode_content("plain", "text") == "plain"


def test_decode_content_bytes_decodes_hex() -> None:
    assert _decode_content("deadbeef", "bytes") == b"\xde\xad\xbe\xef"


def test_decode_content_json_parses_text() -> None:
    assert _decode_content('{"a": 1}', "json") == {"a": 1}


def test_decode_content_rejects_unknown_type() -> None:
    """An unrecognized ``content_type`` is a corruption signal; the function must
    raise rather than silently return the raw stored text."""
    with pytest.raises(ValueError, match="Unknown content_type"):
        _decode_content("anything", "yaml")


# ── EpisodicRecord dataclass ───────────────────────────────────────────────


def test_episodic_record_minimal_init_fills_defaults() -> None:
    """Required positional args + sensible defaults for everything else."""
    r = EpisodicRecord(session_id="s1", turn_id=1, role="user", content="hi")
    assert r.session_id == "s1"
    assert r.turn_id == 1
    assert r.role == "user"
    assert r.content == "hi"
    assert r.parent_turn_id is None
    assert r.timestamp is None
    assert r.segment is None
    assert r.trust_level == "worker"
    assert r.tags == []
    assert r.content_hash is None
    assert r.content_type is None
    assert r.rowid is None


def test_episodic_record_tags_are_per_instance() -> None:
    """``field(default_factory=list)`` — not a shared list across instances."""
    r1 = EpisodicRecord(session_id="s1", turn_id=1, role="user", content="a")
    r2 = EpisodicRecord(session_id="s2", turn_id=1, role="user", content="b")
    r1.tags.append("mutated")
    assert r2.tags == []


# ── EpisodicStore construction + migrate ───────────────────────────────────


def test_store_creates_parent_directory(tmp_path: Path) -> None:
    """If the parent directory of the DB doesn't yet exist, the store creates it
    on first construction (production setup: first-run ``~/.linus/`` creation)."""
    db_path = tmp_path / "deep" / "nested" / "episodic.db"
    assert not db_path.parent.exists()
    store = EpisodicStore(db_path=db_path)
    assert db_path.parent.exists()
    assert db_path.exists()
    assert isinstance(store, EpisodicStore)


def test_store_accepts_str_path(tmp_path: Path) -> None:
    """``db_path`` accepts str or Path (typed as ``Path | str | None``)."""
    db_path = tmp_path / "episodic.db"
    store = EpisodicStore(db_path=str(db_path))
    assert store.db_path == Path(str(db_path))
    assert db_path.exists()


def test_store_none_path_uses_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Constructing with ``db_path=None`` routes through :func:`default_db_path`,
    which respects ``LINUS_HOME`` — so tests can fully redirect production
    behavior into ``tmp_path``."""
    monkeypatch.setenv("LINUS_HOME", str(tmp_path))
    store = EpisodicStore()
    assert store.db_path == tmp_path / "episodic.db"
    assert (tmp_path / "episodic.db").exists()


def test_store_migrate_is_idempotent(tmp_path: Path) -> None:
    """Calling :meth:`migrate` repeatedly must not churn data or raise. The
    schema_version table tracks already-applied migrations."""
    db_path = tmp_path / "episodic.db"
    store = EpisodicStore(db_path=db_path)
    v1 = store.migrate()
    v2 = store.migrate()
    v3 = store.migrate()
    assert v1 == v2 == v3 == SCHEMA_VERSION
    # Exactly one row in schema_version — repeated migrates don't insert duplicates
    # when the schema is already current (current >= SCHEMA_VERSION short-circuits
    # the INSERT).
    with sqlite3.connect(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0]
    assert count == 1


def test_store_migrate_creates_schema_version_table(tmp_path: Path) -> None:
    """After construction, ``schema_version`` should hold the current version."""
    db_path = tmp_path / "episodic.db"
    EpisodicStore(db_path=db_path)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    assert row[0] == SCHEMA_VERSION


def test_store_migrate_creates_episodic_records_table(tmp_path: Path) -> None:
    """The DDL creates the ``episodic_records`` table with the expected columns."""
    db_path = tmp_path / "episodic.db"
    EpisodicStore(db_path=db_path)
    with sqlite3.connect(db_path) as conn:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(episodic_records)").fetchall()}
    expected = {
        "rowid",
        "session_id",
        "turn_id",
        "parent_turn_id",
        "timestamp",
        "role",
        "segment",
        "content_hash",
        "content",
        "content_type",
        "trust_level",
        "tags",
    }
    assert expected.issubset(cols)


def test_store_migrate_creates_indexes(tmp_path: Path) -> None:
    """The DDL declares five indexes: session, hash, timestamp, role, segment.
    Confirm they're present so future query planning can rely on them."""
    db_path = tmp_path / "episodic.db"
    EpisodicStore(db_path=db_path)
    with sqlite3.connect(db_path) as conn:
        idxs = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_episodic_%'"
            ).fetchall()
        }
    assert idxs == {
        "idx_episodic_session",
        "idx_episodic_hash",
        "idx_episodic_timestamp",
        "idx_episodic_role",
        "idx_episodic_segment",
    }


def test_store_connection_sets_pragmas(tmp_path: Path) -> None:
    """The ``_connection`` context manager opens connections with
    ``foreign_keys=ON`` and ``journal_mode=WAL`` so concurrent readers don't
    block the single writer."""
    db_path = tmp_path / "episodic.db"
    store = EpisodicStore(db_path=db_path)
    with store._connection() as conn:
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        journal = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert fk == 1
    assert journal.lower() == "wal"


def test_store_construction_on_existing_db_does_not_error(tmp_path: Path) -> None:
    """Second construction against an already-initialized DB must be a no-op
    that returns a working store (idempotent migrate is the whole point)."""
    db_path = tmp_path / "episodic.db"
    EpisodicStore(db_path=db_path)
    # Re-open — the migration should detect the schema is current and skip.
    s2 = EpisodicStore(db_path=db_path)
    assert isinstance(s2, EpisodicStore)


# ── EpisodicStore.write_record ─────────────────────────────────────────────


@pytest.fixture
def store(tmp_path: Path) -> EpisodicStore:
    """Hermetic store backed by a per-test ``tmp_path`` DB."""
    return EpisodicStore(db_path=tmp_path / "episodic.db")


def test_write_record_returns_sha256_prefixed_hash(store: EpisodicStore) -> None:
    record = EpisodicRecord(session_id="s1", turn_id=1, role="user", content="hello")
    hash_value = store.write_record(record)
    assert hash_value.startswith("sha256:")
    assert len(hash_value) == len("sha256:") + 64  # 64 hex chars for SHA-256


def test_write_record_populates_fields_in_place(store: EpisodicStore) -> None:
    """Per docstring contract: write_record mutates the record with rowid,
    content_hash, content_type, and timestamp filled."""
    record = EpisodicRecord(session_id="s1", turn_id=1, role="user", content="hello")
    assert record.rowid is None
    assert record.content_hash is None
    assert record.content_type is None
    assert record.timestamp is None
    store.write_record(record)
    assert record.rowid is not None
    assert record.rowid >= 1
    assert record.content_hash is not None
    assert record.content_hash.startswith("sha256:")
    assert record.content_type == "text"
    assert record.timestamp is not None
    assert record.timestamp.endswith("+00:00")


def test_write_record_honors_supplied_timestamp(store: EpisodicStore) -> None:
    """If caller pre-populates ``timestamp``, write_record uses it verbatim
    rather than overwriting with ``_utcnow``."""
    record = EpisodicRecord(
        session_id="s1",
        turn_id=1,
        role="user",
        content="hi",
        timestamp="2024-01-01T00:00:00+00:00",
    )
    store.write_record(record)
    assert record.timestamp == "2024-01-01T00:00:00+00:00"


def test_write_record_overwrites_forged_hash(store: EpisodicStore) -> None:
    """Caller-supplied content_hash is recomputed and overwritten so forged
    hashes never land in the store. This is a security property."""
    record = EpisodicRecord(
        session_id="s1",
        turn_id=1,
        role="user",
        content="real content",
        content_hash="sha256:forged",
    )
    returned = store.write_record(record)
    assert record.content_hash == returned
    assert record.content_hash != "sha256:forged"


def test_write_record_bytes_content_round_trips(store: EpisodicStore) -> None:
    """Bytes content is stored hex-encoded and decodes back to the original
    bytes on read."""
    record = EpisodicRecord(session_id="s1", turn_id=1, role="tool", content=b"\x00\x01\xff")
    store.write_record(record)
    assert record.content_type == "bytes"
    [out] = store.read_records({"session_id": "s1"})
    assert out.content == b"\x00\x01\xff"


def test_write_record_json_content_round_trips(store: EpisodicStore) -> None:
    """Dict content is stored canonical-JSON and decodes back to the same dict."""
    payload = {"key": "value", "nested": {"a": 1, "b": [2, 3]}}
    record = EpisodicRecord(session_id="s1", turn_id=1, role="user", content=payload)
    store.write_record(record)
    assert record.content_type == "json"
    [out] = store.read_records({"session_id": "s1"})
    assert out.content == payload


def test_write_record_list_content_round_trips(store: EpisodicStore) -> None:
    """List content rides the JSON path too."""
    record = EpisodicRecord(session_id="s1", turn_id=1, role="user", content=[1, "two", {"three": 3}])
    store.write_record(record)
    [out] = store.read_records({"session_id": "s1"})
    assert out.content == [1, "two", {"three": 3}]


def test_write_record_assigns_increasing_rowids(store: EpisodicStore) -> None:
    """rowid is the auto-increment ordinal — strictly increasing across writes."""
    rowids = []
    for i in range(5):
        r = EpisodicRecord(session_id="s1", turn_id=i, role="user", content=f"msg-{i}")
        store.write_record(r)
        rowids.append(r.rowid)
    assert rowids == sorted(rowids)
    assert len(set(rowids)) == 5


def test_write_record_uniqueness_constraint(store: EpisodicStore) -> None:
    """The schema enforces UNIQUE(session_id, turn_id, segment). A second insert
    with the same tuple raises sqlite3.IntegrityError per the docstring."""
    r1 = EpisodicRecord(session_id="s1", turn_id=1, role="user", content="a", segment="answer")
    store.write_record(r1)
    r2 = EpisodicRecord(session_id="s1", turn_id=1, role="user", content="b", segment="answer")
    with pytest.raises(sqlite3.IntegrityError):
        store.write_record(r2)


def test_write_record_same_turn_different_segment_allowed(store: EpisodicStore) -> None:
    """Different segments under the same (session_id, turn_id) are distinct rows
    — the assistant may emit both a scratchpad and an answer for a single turn."""
    r1 = EpisodicRecord(session_id="s1", turn_id=1, role="assistant", content="thinking...", segment="scratchpad")
    r2 = EpisodicRecord(session_id="s1", turn_id=1, role="assistant", content="answer.", segment="answer")
    store.write_record(r1)
    store.write_record(r2)
    out = store.read_records({"session_id": "s1"})
    assert len(out) == 2
    assert {o.segment for o in out} == {"scratchpad", "answer"}


def test_write_record_persists_tags_as_json(store: EpisodicStore) -> None:
    """``tags`` is stored as canonical JSON and decoded back to a list on read."""
    record = EpisodicRecord(session_id="s1", turn_id=1, role="user", content="hi", tags=["alpha", "beta"])
    store.write_record(record)
    [out] = store.read_records({"session_id": "s1"})
    assert out.tags == ["alpha", "beta"]


def test_write_record_persists_parent_turn_id(store: EpisodicStore) -> None:
    """``parent_turn_id`` is a nullable self-reference; non-null values must
    round-trip."""
    r1 = EpisodicRecord(session_id="s1", turn_id=1, role="user", content="q")
    r2 = EpisodicRecord(session_id="s1", turn_id=2, role="assistant", content="a", parent_turn_id=1)
    store.write_record(r1)
    store.write_record(r2)
    rows = store.read_records({"session_id": "s1"})
    parents = {row.turn_id: row.parent_turn_id for row in rows}
    assert parents == {1: None, 2: 1}


# ── EpisodicStore.read_records query surface ──────────────────────────────


def test_read_records_returns_empty_for_empty_store(store: EpisodicStore) -> None:
    assert store.read_records() == []
    assert store.read_records({}) == []
    assert store.read_records({"session_id": "nope"}) == []


def test_read_records_no_query_returns_all(store: EpisodicStore) -> None:
    """``query=None`` (the default) returns the whole table."""
    for i in range(3):
        store.write_record(EpisodicRecord(session_id="s1", turn_id=i, role="user", content=f"m{i}"))
    out = store.read_records()
    assert len(out) == 3


def test_read_records_filter_by_session_id(store: EpisodicStore) -> None:
    for sid in ("a", "b", "a"):
        store.write_record(EpisodicRecord(session_id=sid, turn_id=0, role="user", content=f"{sid}-msg"))
    # turn_ids collide but session_ids differ; segment=None lets the unique
    # constraint accept duplicates (NULL ≠ NULL in SQLite uniqueness).
    out_a = store.read_records({"session_id": "a"})
    out_b = store.read_records({"session_id": "b"})
    assert all(r.session_id == "a" for r in out_a)
    assert all(r.session_id == "b" for r in out_b)


def test_read_records_filter_by_role(store: EpisodicStore) -> None:
    store.write_record(EpisodicRecord(session_id="s1", turn_id=1, role="user", content="q"))
    store.write_record(EpisodicRecord(session_id="s1", turn_id=2, role="assistant", content="a"))
    store.write_record(EpisodicRecord(session_id="s1", turn_id=3, role="tool", content="t"))
    [out] = store.read_records({"role": "assistant"})
    assert out.role == "assistant"
    assert out.content == "a"


def test_read_records_filter_by_segment(store: EpisodicStore) -> None:
    store.write_record(EpisodicRecord(session_id="s1", turn_id=1, role="assistant", content="x", segment="scratchpad"))
    store.write_record(EpisodicRecord(session_id="s1", turn_id=2, role="assistant", content="y", segment="answer"))
    [out] = store.read_records({"segment": "scratchpad"})
    assert out.segment == "scratchpad"


def test_read_records_filter_by_content_hash(store: EpisodicStore) -> None:
    r = EpisodicRecord(session_id="s1", turn_id=1, role="user", content="unique-payload")
    store.write_record(r)
    [out] = store.read_records({"content_hash": r.content_hash})
    assert out.content == "unique-payload"


def test_read_records_filter_by_trust_level(store: EpisodicStore) -> None:
    store.write_record(
        EpisodicRecord(session_id="s1", turn_id=1, role="user", content="trusted", trust_level="trusted")
    )
    store.write_record(
        EpisodicRecord(session_id="s1", turn_id=2, role="user", content="external", trust_level="external")
    )
    [out] = store.read_records({"trust_level": "trusted"})
    assert out.content == "trusted"


def test_read_records_filter_by_parent_turn_id(store: EpisodicStore) -> None:
    store.write_record(EpisodicRecord(session_id="s1", turn_id=1, role="user", content="q"))
    store.write_record(EpisodicRecord(session_id="s1", turn_id=2, role="assistant", content="a", parent_turn_id=1))
    [out] = store.read_records({"parent_turn_id": 1})
    assert out.turn_id == 2


def test_read_records_filter_by_turn_id(store: EpisodicStore) -> None:
    for i in range(3):
        store.write_record(EpisodicRecord(session_id="s1", turn_id=i, role="user", content=f"m{i}"))
    [out] = store.read_records({"turn_id": 1})
    assert out.turn_id == 1


def test_read_records_in_filter_list(store: EpisodicStore) -> None:
    """List value triggers the ``IN`` branch."""
    for i in range(5):
        store.write_record(EpisodicRecord(session_id="s1", turn_id=i, role="user", content=f"m{i}"))
    out = store.read_records({"turn_id": [0, 2, 4]})
    assert sorted(o.turn_id for o in out) == [0, 2, 4]


def test_read_records_in_filter_tuple(store: EpisodicStore) -> None:
    """Tuple value also triggers the ``IN`` branch (isinstance check covers
    both list and tuple)."""
    store.write_record(EpisodicRecord(session_id="a", turn_id=0, role="user", content="x"))
    store.write_record(EpisodicRecord(session_id="b", turn_id=0, role="user", content="y"))
    store.write_record(EpisodicRecord(session_id="c", turn_id=0, role="user", content="z"))
    out = store.read_records({"session_id": ("a", "c")})
    assert sorted(o.session_id for o in out) == ["a", "c"]


def test_read_records_empty_in_list_short_circuits_to_empty(store: EpisodicStore) -> None:
    """An empty ``IN`` list would otherwise produce invalid SQL — the
    implementation short-circuits to ``[]`` without touching the DB."""
    store.write_record(EpisodicRecord(session_id="s1", turn_id=0, role="user", content="x"))
    assert store.read_records({"session_id": []}) == []
    assert store.read_records({"turn_id": ()}) == []


def test_read_records_in_list_chunks_past_sqlite_limit(store: EpisodicStore) -> None:
    """An IN-list of 2000 values must NOT raise ``sqlite3.OperationalError:
    too many SQL variables``. The implementation chunks the IN-list under
    SQLite's ``SQLITE_LIMIT_VARIABLE_NUMBER`` (default 999 on older libsqlite)
    and unions the results in Python.

    Regression cover for PR #108 H2: the pre-fix ``read_records`` built a
    single ``IN (?, ?, ..., ?)`` placeholder list of length N; passing N > 999
    raised ``OperationalError`` on default libsqlite builds.
    """
    # Write 50 real records under known turn_ids 0..49 inside one session.
    for i in range(50):
        store.write_record(EpisodicRecord(session_id="s1", turn_id=i, role="user", content=f"m{i}"))

    # Build an IN-list of 2000 candidate turn_ids: 50 that exist (0..49) plus
    # 1950 dummies (1000..2949) that don't. The query should return exactly
    # 50 rows. 2000 > 999, so the pre-fix code would have raised
    # ``sqlite3.OperationalError: too many SQL variables`` on a libsqlite
    # build with the default limit.
    huge_filter = list(range(50)) + list(range(1000, 2950))
    assert len(huge_filter) == 2000

    # Must not raise.
    out = store.read_records({"session_id": "s1", "turn_id": huge_filter})
    assert len(out) == 50
    assert sorted(o.turn_id for o in out) == list(range(50))

    # Sanity check at the small-batch scale: the chunked path must produce
    # identical results to the naive single-query path. We compare against a
    # small IN-list (well under any limit) so the equivalence is unambiguous.
    small_filter = [0, 10, 20, 30, 40]
    small_out = store.read_records({"session_id": "s1", "turn_id": small_filter})
    assert sorted(o.turn_id for o in small_out) == small_filter


def test_read_records_in_list_chunks_preserve_order_and_limit(store: EpisodicStore) -> None:
    """Chunked IN-list queries must still honor ``order=desc`` and ``limit``
    so the externally-visible result is identical to a single-statement form.
    """
    for i in range(100):
        store.write_record(EpisodicRecord(session_id="s1", turn_id=i, role="user", content=f"m{i}"))

    # IN-list that forces chunking (> 499, the configured chunk size).
    huge_filter = list(range(100)) + list(range(1000, 1500))
    assert len(huge_filter) == 600

    out_desc = store.read_records({"session_id": "s1", "turn_id": huge_filter, "order": "desc", "limit": 5})
    # Limit applied after merge; desc order over the merged set → highest 5 turn_ids.
    assert [r.turn_id for r in out_desc] == [99, 98, 97, 96, 95]


def test_read_records_limit_caps_result_count(store: EpisodicStore) -> None:
    for i in range(10):
        store.write_record(EpisodicRecord(session_id="s1", turn_id=i, role="user", content=f"m{i}"))
    out = store.read_records({"limit": 3})
    assert len(out) == 3


def test_read_records_limit_with_filter(store: EpisodicStore) -> None:
    """``limit`` combines with WHERE clauses."""
    for i in range(5):
        store.write_record(EpisodicRecord(session_id="s1", turn_id=i, role="user", content=f"m{i}"))
    for i in range(5):
        store.write_record(EpisodicRecord(session_id="s2", turn_id=i, role="user", content=f"o{i}"))
    out = store.read_records({"session_id": "s1", "limit": 2})
    assert len(out) == 2
    assert all(r.session_id == "s1" for r in out)


def test_read_records_limit_none_returns_all(store: EpisodicStore) -> None:
    """``limit=None`` is the documented "no limit" sentinel."""
    for i in range(4):
        store.write_record(EpisodicRecord(session_id="s1", turn_id=i, role="user", content=f"m{i}"))
    out = store.read_records({"limit": None})
    assert len(out) == 4


def test_read_records_default_order_is_asc(store: EpisodicStore) -> None:
    for i in range(3):
        store.write_record(EpisodicRecord(session_id="s1", turn_id=i, role="user", content=f"m{i}"))
    out = store.read_records()
    assert [r.turn_id for r in out] == [0, 1, 2]


def test_read_records_order_desc(store: EpisodicStore) -> None:
    """``order='desc'`` flips the ORDER BY to descending rowid."""
    for i in range(3):
        store.write_record(EpisodicRecord(session_id="s1", turn_id=i, role="user", content=f"m{i}"))
    out = store.read_records({"order": "desc"})
    assert [r.turn_id for r in out] == [2, 1, 0]


def test_read_records_order_case_insensitive(store: EpisodicStore) -> None:
    """``order`` is lowercased before comparison; ``'DESC'`` works just like
    ``'desc'``."""
    for i in range(2):
        store.write_record(EpisodicRecord(session_id="s1", turn_id=i, role="user", content=f"m{i}"))
    out = store.read_records({"order": "DESC"})
    assert [r.turn_id for r in out] == [1, 0]


def test_read_records_rejects_unsupported_key(store: EpisodicStore) -> None:
    """Misspelled or unsupported filters raise ValueError rather than silently
    returning all rows — the documented "don't silently get all rows back"
    contract."""
    with pytest.raises(ValueError, match="Unsupported query keys"):
        store.read_records({"username": "alice"})


def test_read_records_rejects_invalid_order(store: EpisodicStore) -> None:
    """``order`` must be ``'asc'`` or ``'desc'`` (case-insensitive); anything
    else raises ValueError."""
    with pytest.raises(ValueError, match="order must be"):
        store.read_records({"order": "sideways"})


def test_read_records_multiple_filters_use_and(store: EpisodicStore) -> None:
    """Multiple filter keys combine with AND."""
    store.write_record(EpisodicRecord(session_id="s1", turn_id=1, role="user", content="x", segment="answer"))
    store.write_record(EpisodicRecord(session_id="s1", turn_id=2, role="user", content="y", segment="scratchpad"))
    store.write_record(EpisodicRecord(session_id="s2", turn_id=1, role="user", content="z", segment="answer"))
    out = store.read_records({"session_id": "s1", "segment": "answer"})
    assert len(out) == 1
    assert out[0].content == "x"


def test_read_records_decodes_content_per_type(store: EpisodicStore) -> None:
    """Round-trip sanity: text/bytes/json all decode back to the original
    Python value via :func:`_decode_content`."""
    store.write_record(EpisodicRecord(session_id="s1", turn_id=1, role="user", content="text-content"))
    store.write_record(EpisodicRecord(session_id="s1", turn_id=2, role="user", content=b"\xab\xcd"))
    store.write_record(EpisodicRecord(session_id="s1", turn_id=3, role="user", content={"k": "v"}))
    out = store.read_records({"session_id": "s1"})
    by_turn = {r.turn_id: r.content for r in out}
    assert by_turn == {1: "text-content", 2: b"\xab\xcd", 3: {"k": "v"}}


# ── Cross-instance persistence ─────────────────────────────────────────────


def test_records_persist_across_store_instances(tmp_path: Path) -> None:
    """Two ``EpisodicStore`` instances against the same DB file see each other's
    writes — the substrate is durable, not in-memory."""
    db_path = tmp_path / "episodic.db"
    s1 = EpisodicStore(db_path=db_path)
    s1.write_record(EpisodicRecord(session_id="s1", turn_id=1, role="user", content="durable"))
    s2 = EpisodicStore(db_path=db_path)
    out = s2.read_records({"session_id": "s1"})
    assert len(out) == 1
    assert out[0].content == "durable"


def test_records_persist_with_tags_and_metadata(tmp_path: Path) -> None:
    """Full record round-trip across instances preserves every field."""
    db_path = tmp_path / "episodic.db"
    s1 = EpisodicStore(db_path=db_path)
    r = EpisodicRecord(
        session_id="s1",
        turn_id=42,
        role="assistant",
        content={"plan": ["step1", "step2"]},
        parent_turn_id=41,
        segment="answer",
        trust_level="trusted",
        tags=["plan", "project-x"],
        timestamp="2026-05-19T12:00:00+00:00",
    )
    s1.write_record(r)
    expected_hash = r.content_hash

    s2 = EpisodicStore(db_path=db_path)
    [out] = s2.read_records({"session_id": "s1"})
    assert out.session_id == "s1"
    assert out.turn_id == 42
    assert out.role == "assistant"
    assert out.content == {"plan": ["step1", "step2"]}
    assert out.parent_turn_id == 41
    assert out.segment == "answer"
    assert out.trust_level == "trusted"
    assert sorted(out.tags) == ["plan", "project-x"]
    assert out.timestamp == "2026-05-19T12:00:00+00:00"
    assert out.content_hash == expected_hash
    assert out.content_type == "json"


# ── _row_to_record direct cover ────────────────────────────────────────────


def test_row_to_record_materializes_full_record(tmp_path: Path) -> None:
    """Cover :func:`_row_to_record` directly. Reading via the public surface
    already exercises it, but a direct test pins the row-to-dataclass contract
    independently of the query DSL."""
    db_path = tmp_path / "episodic.db"
    store = EpisodicStore(db_path=db_path)
    store.write_record(
        EpisodicRecord(
            session_id="s1",
            turn_id=1,
            role="user",
            content="payload",
            tags=["t1"],
        )
    )
    with store._connection() as conn:
        row = conn.execute("SELECT * FROM episodic_records LIMIT 1").fetchone()
    record = _row_to_record(row)
    assert record.session_id == "s1"
    assert record.turn_id == 1
    assert record.role == "user"
    assert record.content == "payload"
    assert record.tags == ["t1"]
    assert record.content_hash is not None
    assert record.content_type == "text"
    assert record.rowid is not None


# ── Content-hash determinism sanity ────────────────────────────────────────


def test_same_content_produces_same_hash_across_writes(store: EpisodicStore) -> None:
    """The hash is a function of the content, not the wrapping record. Two
    records with the same payload (different session_id / turn_id) produce the
    same hash — confirming addressability."""
    r1 = EpisodicRecord(session_id="s1", turn_id=1, role="user", content="dedupe-me")
    r2 = EpisodicRecord(session_id="s2", turn_id=99, role="user", content="dedupe-me")
    h1 = store.write_record(r1)
    h2 = store.write_record(r2)
    assert h1 == h2


def test_different_content_produces_different_hash(store: EpisodicStore) -> None:
    r1 = EpisodicRecord(session_id="s1", turn_id=1, role="user", content="a")
    r2 = EpisodicRecord(session_id="s2", turn_id=2, role="user", content="b")
    assert store.write_record(r1) != store.write_record(r2)


def test_hash_lookup_finds_duplicate_content(store: EpisodicStore) -> None:
    """Hash filtering surfaces all records sharing a payload — the substrate
    primitive the Phase 2h.3 dedup layer will sit on top of."""
    same = "the-same-payload"
    for i in range(3):
        store.write_record(EpisodicRecord(session_id=f"s{i}", turn_id=0, role="user", content=same))
    one = store.write_record(EpisodicRecord(session_id="other", turn_id=0, role="user", content="different"))
    [r] = store.read_records({"content_hash": one})
    assert r.content == "different"
    hash_of_same = EpisodicRecord(session_id="x", turn_id=0, role="user", content=same)
    # Compute the canonical hash without inserting (write_record mutates in
    # place, but a fresh record carrying the same content gives us the value).
    from linus.memory.hashing import content_hash

    matched = store.read_records({"content_hash": content_hash(same)})
    assert len(matched) == 3
    assert all(r.content == same for r in matched)
    # Sanity: the unused fresh record is the same shape, unaltered.
    assert hash_of_same.content == same


# ── Tags JSON canonicalization ─────────────────────────────────────────────


def test_tags_stored_as_canonical_json(tmp_path: Path) -> None:
    """``tags`` is written via ``json.dumps(..., sort_keys=True)``. Read the raw
    column to confirm the JSON form is canonical and round-trips through
    :func:`json.loads`."""
    db_path = tmp_path / "episodic.db"
    store = EpisodicStore(db_path=db_path)
    store.write_record(EpisodicRecord(session_id="s1", turn_id=1, role="user", content="x", tags=["z", "a", "m"]))
    with sqlite3.connect(db_path) as conn:
        raw = conn.execute("SELECT tags FROM episodic_records").fetchone()[0]
    assert isinstance(raw, str)
    assert json.loads(raw) == ["z", "a", "m"]
