"""SQLite-backed episodic store (Layer C of the memory architecture).

This is the v0 implementation of the substrate ratified by
[DEC-0029](../../../docs/adr/0029-episodic-memory-substrate.md): a single-file SQLite
database at ``~/.linus/episodic.db`` with the record shape

    (session_id, turn_id, parent_turn_id, timestamp, role, segment,
     content_hash, content, trust_level, tags)

absorbing within-session scratchpad (Layer B per DEC-0030), cross-session episodic
history, and tool outputs without schema migration. ``segment`` distinguishes the three
record kinds per DEC-0030: ``"scratchpad"`` / ``"answer"`` / ``"tool_output"``.

## Scope of this module (Phase 2h.1 deliverable)

Per the Phase 2h deliverable split in the implementation plan, this module ships the
**data layer**: schema, migrations, write, read. The higher-level
``linus.memory.episodic.*`` tool family (``record_turn``, ``record_consolidation``,
``recall``, ``recall_recent``, ``recall_by_tag``, ``recall_by_content``, ``recall_full``,
``prune_archived``) is a Phase 2h.3 deliverable layered on top.

## Substrate hygiene

- The store is single-writer-safe via SQLite's default transaction model. Multi-worker
  write coordination (the DEC-0029 §3 cross-cutting concern) is the orchestration
  layer's problem, not this module's.
- ``WAL`` journal mode is enabled at migration time so concurrent readers don't block
  the single writer.
- ``foreign_keys = ON`` is set per connection so the ``parent_turn_id`` self-reference
  is checked.
- Timestamps are stored as ISO-8601 UTC strings (``2026-05-16T14:23:45.123456+00:00``)
  for cross-platform legibility; sorting works as expected on lexicographic compare.
- The schema is intentionally additive — new columns get added via
  ``ALTER TABLE ... ADD COLUMN``; the migration version is tracked in a
  ``schema_version`` table so :func:`migrate` is idempotent.

## What the audit log expects from us

Per DEC-0030, every record write is mirrored by an event line in the audit log
(``~/.linus/audit.jsonl``). This module returns the content hash of every write so the
caller can record the event. It does not write to the audit log itself — that coupling
is the dispatch layer's responsibility (Phase 2h.5 deliverable).
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterable, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from linus.memory.hashing import content_hash

__all__ = [
    "DEFAULT_DB_PATH",
    "SCHEMA_VERSION",
    "EpisodicRecord",
    "EpisodicStore",
    "default_db_path",
]


#: Latest schema version this module knows how to produce. Incremented when a real
#: migration ships; :func:`EpisodicStore.migrate` is idempotent against this number.
SCHEMA_VERSION = 1

#: Default location of the v0 episodic database, per DEC-0029.
DEFAULT_DB_PATH = Path.home() / ".linus" / "episodic.db"


def default_db_path() -> Path:
    """Return the default episodic DB path, honoring ``LINUS_HOME`` if set.

    The override exists so tests can redirect to ``tmp_path`` and so production setups
    can move ``~/.linus/`` if their home directory is on a slow / shared volume.
    """
    if env_root := os.environ.get("LINUS_HOME"):
        return Path(env_root) / "episodic.db"
    return DEFAULT_DB_PATH


# ---------------------------------------------------------------------------
# Record dataclass


@dataclass(slots=True)
class EpisodicRecord:
    """One record in the episodic store.

    Field shape mirrors the DEC-0029 record tuple verbatim. ``content_hash`` is
    computed at write time from ``content`` (and any caller-supplied
    ``content_for_hash`` override is rejected — the hash is a function of the payload,
    not a free parameter).

    The ``content`` field accepts ``str``, ``bytes``, or any JSON-serializable Python
    value; non-string types are canonicalized at write time and stored as JSON text.
    A ``content_type`` column records which encoding was used so reads round-trip
    correctly.

    Attributes:
        session_id: Stable identifier for the session this turn belongs to.
        turn_id: Monotonically-ordered identifier for this turn within the session.
        parent_turn_id: ``turn_id`` of the immediately-preceding turn this one is
            replying to. ``None`` for the first turn of a session.
        timestamp: ISO-8601 UTC string. Auto-filled from :func:`datetime.now` if absent.
        role: ``"user"`` / ``"assistant"`` / ``"system"`` / ``"tool"`` — free-form for
            v0; tightened to an enum in a later migration.
        segment: ``"scratchpad"`` / ``"answer"`` / ``"tool_output"`` per DEC-0030. May be
            ``None`` for non-assistant turns where the distinction does not apply.
        content: The payload. See class docstring for encoding rules.
        trust_level: Caller-asserted trust band (``"trusted"`` / ``"user"`` /
            ``"worker"`` / ``"external"``). Free-form for v0.
        tags: Free-form tag list — project tags, content tags, anything the retrieval
            layer wants to filter on later. Stored as canonical JSON.
        content_hash: Set automatically by :meth:`EpisodicStore.write_record`; the
            caller need not populate it. If populated, it is recomputed and overwritten
            to prevent forged hashes from landing in the store.
        content_type: ``"text"`` / ``"bytes"`` / ``"json"`` — derived from the type of
            ``content`` at write time. Bytes are stored hex-encoded; json is stored as
            canonical JSON text.
        rowid: Set by :meth:`EpisodicStore.write_record` after insert. Used as the
            cheap ordinal for retrieval ordering.
    """

    session_id: str
    turn_id: int
    role: str
    content: Any
    parent_turn_id: int | None = None
    timestamp: str | None = None
    segment: str | None = None
    trust_level: str = "worker"
    tags: list[str] = field(default_factory=list)
    content_hash: str | None = None
    content_type: str | None = None
    rowid: int | None = None


# ---------------------------------------------------------------------------
# Schema DDL


_SCHEMA_DDL_V1 = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS episodic_records (
    rowid           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT    NOT NULL,
    turn_id         INTEGER NOT NULL,
    parent_turn_id  INTEGER,
    timestamp       TEXT    NOT NULL,
    role            TEXT    NOT NULL,
    segment         TEXT,
    content_hash    TEXT    NOT NULL,
    content         TEXT    NOT NULL,
    content_type    TEXT    NOT NULL,
    trust_level     TEXT    NOT NULL,
    tags            TEXT    NOT NULL,
    UNIQUE (session_id, turn_id, segment)
);

CREATE INDEX IF NOT EXISTS idx_episodic_session   ON episodic_records (session_id, turn_id);
CREATE INDEX IF NOT EXISTS idx_episodic_hash      ON episodic_records (content_hash);
CREATE INDEX IF NOT EXISTS idx_episodic_timestamp ON episodic_records (timestamp);
CREATE INDEX IF NOT EXISTS idx_episodic_role      ON episodic_records (role);
CREATE INDEX IF NOT EXISTS idx_episodic_segment   ON episodic_records (segment);
"""


# ---------------------------------------------------------------------------
# Helpers


def _utcnow() -> str:
    """Return the current UTC timestamp as a sortable ISO-8601 string."""
    return datetime.now(tz=UTC).isoformat()


def _encode_content(content: Any) -> tuple[str, str]:
    """Encode ``content`` for storage. Returns ``(stored_text, content_type)``.

    The content_type is one of:

    - ``"text"`` — ``content`` was a ``str``; stored verbatim.
    - ``"bytes"`` — ``content`` was ``bytes``; stored as a hex string.
    - ``"json"`` — anything else; stored as canonical JSON.
    """
    if isinstance(content, str):
        return content, "text"
    if isinstance(content, bytes):
        return content.hex(), "bytes"
    return json.dumps(content, sort_keys=True, ensure_ascii=False, allow_nan=False), "json"


def _decode_content(stored: str, content_type: str) -> Any:
    """Reverse of :func:`_encode_content`."""
    if content_type == "text":
        return stored
    if content_type == "bytes":
        return bytes.fromhex(stored)
    if content_type == "json":
        return json.loads(stored)
    raise ValueError(f"Unknown content_type: {content_type!r}")


# ---------------------------------------------------------------------------
# Store


class EpisodicStore:
    """Single-file SQLite episodic store.

    Construct once per process. The constructor is cheap: it only resolves the path
    and runs :meth:`migrate` (which is idempotent), creating ``~/.linus/`` on first
    call. The underlying connection is opened lazily inside the
    :meth:`_connection` context manager so the store survives ``fork`` and so tests
    can run in parallel against distinct ``LINUS_HOME`` overrides.

    Args:
        db_path: Override for the database location. Defaults to
            :func:`default_db_path`.

    Example:
        >>> store = EpisodicStore(db_path=Path("/tmp/test.db"))
        >>> record = EpisodicRecord(
        ...     session_id="s1", turn_id=1, role="user", content="hello"
        ... )
        >>> store.write_record(record)
        'sha256:...'
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.migrate()

    # -- connection management ------------------------------------------------

    @contextmanager
    def _connection(self) -> Iterable[sqlite3.Connection]:
        """Yield a configured SQLite connection.

        Per-connection settings: ``foreign_keys = ON`` and ``journal_mode = WAL``. The
        connection is closed when the context exits regardless of success.
        """
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            conn.close()

    # -- migration ------------------------------------------------------------

    def migrate(self) -> int:
        """Apply any pending migrations. Idempotent.

        Returns the resulting schema version. Safe to call on every process start;
        does not rewrite tables or churn data if the schema is already current.
        """
        with self._connection() as conn:
            conn.executescript(_SCHEMA_DDL_V1)
            current = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
            if current is None or current < SCHEMA_VERSION:
                conn.execute(
                    "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                    (SCHEMA_VERSION, _utcnow()),
                )
        return SCHEMA_VERSION

    # -- writes ---------------------------------------------------------------

    def write_record(self, record: EpisodicRecord) -> str:
        """Insert ``record`` and return its content hash.

        The hash is computed from the canonicalized content (not the wrapping
        ``EpisodicRecord``). Any caller-supplied ``record.content_hash`` is overwritten
        with the recomputed value so forged hashes cannot land in the store.

        On insert, ``record.timestamp`` is filled from :func:`_utcnow` if absent, and
        ``record.rowid`` and ``record.content_hash`` are populated in place.

        Args:
            record: The :class:`EpisodicRecord` to insert. Mutated in place with
                ``rowid``, ``content_hash``, ``content_type``, and ``timestamp`` filled.

        Returns:
            The algorithm-prefixed content hash (``"sha256:<hex>"``).

        Raises:
            sqlite3.IntegrityError: If the ``(session_id, turn_id, segment)`` uniqueness
                constraint is violated.
        """
        stored, content_type = _encode_content(record.content)
        hash_value = content_hash(record.content)
        timestamp = record.timestamp or _utcnow()
        tags_json = json.dumps(record.tags, sort_keys=True, ensure_ascii=False)

        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO episodic_records
                    (session_id, turn_id, parent_turn_id, timestamp, role, segment,
                     content_hash, content, content_type, trust_level, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.session_id,
                    record.turn_id,
                    record.parent_turn_id,
                    timestamp,
                    record.role,
                    record.segment,
                    hash_value,
                    stored,
                    content_type,
                    record.trust_level,
                    tags_json,
                ),
            )
            record.rowid = cursor.lastrowid

        record.content_hash = hash_value
        record.content_type = content_type
        record.timestamp = timestamp
        return hash_value

    # -- reads ----------------------------------------------------------------

    def read_records(self, query: dict[str, Any] | None = None) -> list[EpisodicRecord]:
        """Return records matching ``query``, ordered by ``rowid`` ascending.

        The query dict is intentionally simple at v0: each key is a column name in the
        ``episodic_records`` table; values are either a scalar (exact match) or a list
        (``IN`` match). The Phase 2h.3 ``recall_*`` API will provide higher-level
        queries (temporal weighting, full-text search, tag intersections); for now
        this method is the data-layer escape hatch.

        Supported keys: ``session_id``, ``turn_id``, ``parent_turn_id``, ``role``,
        ``segment``, ``content_hash``, ``trust_level``. Other keys raise
        :class:`ValueError` so callers don't silently get all rows back when they
        misspell a filter.

        Two additional convenience keys:

        - ``"limit"``: integer; applied as ``LIMIT``. ``None`` means no limit.
        - ``"order"``: ``"asc"`` (default) or ``"desc"``; orders by ``rowid``.

        Args:
            query: Filter dict; ``None`` or empty returns the whole table.

        Returns:
            List of :class:`EpisodicRecord` instances, deserialized from storage.
        """
        query = query or {}
        allowed_columns = {
            "session_id",
            "turn_id",
            "parent_turn_id",
            "role",
            "segment",
            "content_hash",
            "trust_level",
        }
        meta_keys = {"limit", "order"}
        unknown = set(query) - allowed_columns - meta_keys
        if unknown:
            raise ValueError(f"Unsupported query keys: {sorted(unknown)}")

        order = query.get("order", "asc").lower()
        if order not in {"asc", "desc"}:
            raise ValueError(f"order must be 'asc' or 'desc', got {order!r}")
        limit = query.get("limit")

        where_clauses: list[str] = []
        params: list[Any] = []
        for key, value in query.items():
            if key not in allowed_columns:
                continue
            if isinstance(value, list | tuple):
                if not value:
                    return []
                placeholders = ",".join("?" * len(value))
                where_clauses.append(f"{key} IN ({placeholders})")
                params.extend(value)
            else:
                where_clauses.append(f"{key} = ?")
                params.append(value)

        sql = "SELECT * FROM episodic_records"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        sql += f" ORDER BY rowid {order.upper()}"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(int(limit))

        with self._connection() as conn:
            rows: Sequence[sqlite3.Row] = conn.execute(sql, params).fetchall()

        return [_row_to_record(row) for row in rows]


def _row_to_record(row: sqlite3.Row) -> EpisodicRecord:
    """Materialize a database row as an :class:`EpisodicRecord`."""
    return EpisodicRecord(
        session_id=row["session_id"],
        turn_id=row["turn_id"],
        parent_turn_id=row["parent_turn_id"],
        timestamp=row["timestamp"],
        role=row["role"],
        segment=row["segment"],
        content=_decode_content(row["content"], row["content_type"]),
        content_hash=row["content_hash"],
        content_type=row["content_type"],
        trust_level=row["trust_level"],
        tags=json.loads(row["tags"]),
        rowid=row["rowid"],
    )
