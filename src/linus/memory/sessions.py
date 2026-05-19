"""Per-conversation session store (task A.3 of the MVP build).

A small SQLite-backed store that gives the FastAPI server's chat
endpoints **multi-turn statefulness** without the client having to
resend conversation history. Clients pass a ``session_id`` on each
request; the server prepends the stored history before calling the
model and appends the new user/assistant pair after the response
completes.

This is intentionally **separate** from the episodic memory store
(:mod:`linus.memory.episodic`, ``~/.linus/episodic.db``) because the
two have different roles:

- :class:`SessionStore` (this module, ``~/.linus/sessions.db``) is
  about chat-UI session history — what the user said, what the
  assistant said, in order, per conversation. Read on every chat
  request; appended on every chat completion.
- :class:`linus.memory.episodic.EpisodicStore` is about reasoning
  traces, scratchpads, and tool outputs per DEC-0029 / DEC-0030 —
  the longer-term durable substrate.

A future hop unifies them once the access patterns settle, per the
memory-architecture spec; for v1 keeping them separate keeps the
session-store contract tight and lets each evolve independently.

Schema
------

Two tables, kept narrow on purpose:

- ``sessions(id TEXT PRIMARY KEY, created_at INTEGER, model TEXT,
   system_prompt TEXT)``
- ``session_messages(session_id TEXT, idx INTEGER, role TEXT,
   content TEXT, created_at INTEGER,
   PRIMARY KEY(session_id, idx))``

``created_at`` is integer nanoseconds since the epoch
(``time.time_ns()``); nanosecond precision avoids same-second ordering
collisions on fast back-to-back appends. Sort within a session is by
``idx``, not timestamp. ``model`` and ``system_prompt`` on the
sessions row are nullable; they're set at session-create time as a
convenience for clients that want to surface them in the UI.
"""

from __future__ import annotations

import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


DEFAULT_DB_PATH = Path.home() / ".linus" / "sessions.db"


def _resolve_db_path(db_path: Path | str | None = None) -> Path:
    """Resolve the SQLite DB path from arg → env → default, expanding ``~``."""
    if db_path is not None:
        return Path(db_path).expanduser()
    env = os.environ.get("LINUS_SESSIONS_DB")
    if env:
        return Path(env).expanduser()
    return DEFAULT_DB_PATH


@dataclass(frozen=True)
class Session:
    """One conversation session — the index row, not the messages.

    ``model`` and ``system_prompt`` are caller-supplied at create time
    for client convenience; the server doesn't enforce that subsequent
    requests against this session use the same model.
    """

    id: str
    created_at: int
    model: str | None = None
    system_prompt: str | None = None


@dataclass(frozen=True)
class StoredMessage:
    """One message in a session's history.

    ``idx`` is the per-session sequence number (zero-based, dense).
    ``role`` is ``"user"`` / ``"assistant"`` / ``"system"`` /
    ``"tool"`` — the same vocabulary the server's request body uses.
    """

    session_id: str
    idx: int
    role: str
    content: str
    created_at: int


class SessionStore:
    """Read/write handle for chat-session history.

    Connection lifecycle: opened lazily on first operation, kept alive
    on the instance, and closed by :meth:`close` (or the
    context-manager form). The instance is not threadsafe; create one
    per request handler thread if needed. For Phase 2a single-process
    use that's not a constraint.

    Schema migration is idempotent — :meth:`_ensure_schema` runs on
    every connect and ``CREATE TABLE IF NOT EXISTS`` does the right
    thing on a populated DB.
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = _resolve_db_path(db_path)
        self._conn: sqlite3.Connection | None = None

    # ── connection lifecycle ────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        self._conn = conn
        self._ensure_schema()
        return conn

    def _ensure_schema(self) -> None:
        assert self._conn is not None
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at INTEGER NOT NULL,
                    model TEXT,
                    system_prompt TEXT
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_messages (
                    session_id TEXT NOT NULL,
                    idx INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    PRIMARY KEY(session_id, idx),
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
                """
            )

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "SessionStore":
        self._connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    # ── writes ──────────────────────────────────────────────────────

    def create_session(
        self,
        model: str | None = None,
        system_prompt: str | None = None,
        session_id: str | None = None,
    ) -> Session:
        """Create a new session and return its record.

        ``session_id`` may be supplied to honor a client-provided id
        (e.g. a UUID generated in the browser); otherwise a fresh
        UUID4 is minted. ``model`` and ``system_prompt`` are stored
        verbatim and surfaced via :meth:`get_session`.
        """
        conn = self._connect()
        sid = session_id or str(uuid.uuid4())
        created_at = time.time_ns()
        with conn:
            conn.execute(
                "INSERT INTO sessions(id, created_at, model, system_prompt) VALUES (?, ?, ?, ?)",
                (sid, created_at, model, system_prompt),
            )
        return Session(id=sid, created_at=created_at, model=model, system_prompt=system_prompt)

    def ensure_session(self, session_id: str, model: str | None = None) -> Session:
        """Return the session if it exists; create it (with the given id) otherwise.

        Convenience for the chat endpoint: a client may pass a
        ``session_id`` for the first turn without having explicitly
        called :meth:`create_session` first. The endpoint can call
        ``ensure_session`` to upsert atomically.
        """
        existing = self.get_session(session_id)
        if existing is not None:
            return existing
        return self.create_session(model=model, session_id=session_id)

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> StoredMessage:
        """Append a single message to a session's history.

        Returns the stored record (with its assigned ``idx``). The
        session must already exist; callers can use
        :meth:`ensure_session` if they're not sure.
        """
        conn = self._connect()
        created_at = time.time_ns()
        with conn:
            cursor = conn.execute(
                "SELECT COALESCE(MAX(idx), -1) + 1 AS next_idx FROM session_messages WHERE session_id = ?",
                (session_id,),
            )
            next_idx = cursor.fetchone()["next_idx"]
            conn.execute(
                "INSERT INTO session_messages(session_id, idx, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, next_idx, role, content, created_at),
            )
        return StoredMessage(
            session_id=session_id,
            idx=next_idx,
            role=role,
            content=content,
            created_at=created_at,
        )

    def append_messages(
        self,
        session_id: str,
        messages: list[tuple[str, str]],
    ) -> list[StoredMessage]:
        """Append a batch of ``(role, content)`` tuples atomically.

        All messages land in one transaction; either the whole batch
        commits or none of it does. Indexes are assigned dense + monotonic.
        """
        if not messages:
            return []
        conn = self._connect()
        created_at = time.time_ns()
        out: list[StoredMessage] = []
        with conn:
            cursor = conn.execute(
                "SELECT COALESCE(MAX(idx), -1) + 1 AS next_idx FROM session_messages WHERE session_id = ?",
                (session_id,),
            )
            next_idx = cursor.fetchone()["next_idx"]
            rows = []
            for offset, (role, content) in enumerate(messages):
                rows.append((session_id, next_idx + offset, role, content, created_at))
                out.append(
                    StoredMessage(
                        session_id=session_id,
                        idx=next_idx + offset,
                        role=role,
                        content=content,
                        created_at=created_at,
                    )
                )
            conn.executemany(
                "INSERT INTO session_messages(session_id, idx, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
                rows,
            )
        return out

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages.

        Returns True if the session existed (and was deleted), False
        otherwise. Useful for test cleanup and for a future
        ``DELETE /v1/sessions/{id}`` endpoint.
        """
        conn = self._connect()
        with conn:
            cursor = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return cursor.rowcount > 0

    # ── reads ───────────────────────────────────────────────────────

    def get_session(self, session_id: str) -> Session | None:
        conn = self._connect()
        row = conn.execute(
            "SELECT id, created_at, model, system_prompt FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        return Session(
            id=row["id"],
            created_at=row["created_at"],
            model=row["model"],
            system_prompt=row["system_prompt"],
        )

    def get_messages(self, session_id: str) -> list[StoredMessage]:
        """Return all messages for a session, ordered by idx ascending."""
        conn = self._connect()
        rows = conn.execute(
            "SELECT session_id, idx, role, content, created_at FROM session_messages "
            "WHERE session_id = ? ORDER BY idx ASC",
            (session_id,),
        ).fetchall()
        return [
            StoredMessage(
                session_id=row["session_id"],
                idx=row["idx"],
                role=row["role"],
                content=row["content"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def list_sessions(self, limit: int = 50) -> list[Session]:
        """Return up to ``limit`` sessions, most recent first."""
        conn = self._connect()
        rows = conn.execute(
            "SELECT id, created_at, model, system_prompt FROM sessions "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            Session(
                id=row["id"],
                created_at=row["created_at"],
                model=row["model"],
                system_prompt=row["system_prompt"],
            )
            for row in rows
        ]


# Process-wide default store. Lazily initialized on first access so
# tests that monkeypatch DEFAULT_DB_PATH (or the LINUS_SESSIONS_DB env
# var) before the first call get the patched path. The server endpoint
# layer uses _get_default_store() to share one store across requests.

_default_store: SessionStore | None = None


def get_default_store() -> SessionStore:
    """Return the process-wide :class:`SessionStore` singleton."""
    global _default_store
    if _default_store is None:
        _default_store = SessionStore()
    return _default_store


def reset_default_store() -> None:
    """Drop the cached singleton so the next call rebuilds it.

    Tests should call this after monkeypatching ``LINUS_SESSIONS_DB``
    to make the next :func:`get_default_store` honor the patched env.
    """
    global _default_store
    if _default_store is not None:
        _default_store.close()
        _default_store = None


@contextmanager
def in_memory_store() -> Iterator[SessionStore]:
    """Context manager yielding an in-memory SessionStore for tests."""
    store = SessionStore(db_path=":memory:")
    try:
        yield store
    finally:
        store.close()
