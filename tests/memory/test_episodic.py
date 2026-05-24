"""Unit tests for :mod:`linus.memory.episodic`."""

from __future__ import annotations

from pathlib import Path

import pytest

from linus.memory.episodic import SCHEMA_VERSION, EpisodicRecord, EpisodicStore


@pytest.fixture()
def store(tmp_path: Path) -> EpisodicStore:
    """Fresh episodic store on a tmp DB path; never touches ``~/.linus/``."""
    db_path = tmp_path / "episodic.db"
    return EpisodicStore(db_path=db_path)


class TestEpisodicSchemaMigrationIdempotent:
    """Spec test: ``test_episodic_schema_migration_idempotent``."""

    def test_migrate_creates_schema_on_fresh_db(self, tmp_path: Path) -> None:
        db_path = tmp_path / "episodic.db"
        store = EpisodicStore(db_path=db_path)
        assert db_path.exists()
        version = store.migrate()
        assert version == SCHEMA_VERSION

    def test_migrate_is_idempotent(self, store: EpisodicStore) -> None:
        """Calling migrate repeatedly does not error or corrupt state."""
        v1 = store.migrate()
        v2 = store.migrate()
        v3 = store.migrate()
        assert v1 == v2 == v3 == SCHEMA_VERSION

    def test_writes_survive_re_migration(self, tmp_path: Path) -> None:
        """Re-running migrate on a non-empty DB does not lose records."""
        db_path = tmp_path / "episodic.db"
        store = EpisodicStore(db_path=db_path)
        record = EpisodicRecord(session_id="s", turn_id=1, role="user", content="hello")
        store.write_record(record)
        store.migrate()
        store.migrate()
        rows = store.read_records()
        assert len(rows) == 1
        assert rows[0].content == "hello"

    def test_schema_version_table_recorded(self, store: EpisodicStore) -> None:
        """The schema_version row exists after migration."""
        import sqlite3

        conn = sqlite3.connect(store.db_path)
        try:
            cur = conn.execute("SELECT MAX(version) FROM schema_version")
            assert cur.fetchone()[0] == SCHEMA_VERSION
        finally:
            conn.close()


class TestEpisodicWriteReadRoundtrip:
    """Spec test: ``test_episodic_write_read_roundtrip``."""

    def test_string_content_roundtrip(self, store: EpisodicStore) -> None:
        record = EpisodicRecord(
            session_id="sess-A",
            turn_id=1,
            role="user",
            content="hello, Linus",
            tags=["demo"],
        )
        h = store.write_record(record)
        assert h.startswith("sha256:")
        assert record.content_hash == h
        assert record.rowid is not None
        assert record.timestamp is not None

        rows = store.read_records({"session_id": "sess-A"})
        assert len(rows) == 1
        out = rows[0]
        assert out.session_id == "sess-A"
        assert out.turn_id == 1
        assert out.role == "user"
        assert out.content == "hello, Linus"
        assert out.tags == ["demo"]
        assert out.content_hash == h
        assert out.content_type == "text"
        assert out.rowid == record.rowid

    def test_bytes_content_roundtrip(self, store: EpisodicStore) -> None:
        payload = b"\x00\x01\xff"
        record = EpisodicRecord(session_id="s", turn_id=1, role="tool", content=payload, segment="tool_output")
        store.write_record(record)
        rows = store.read_records({"session_id": "s"})
        assert rows[0].content == payload
        assert rows[0].content_type == "bytes"

    def test_json_content_roundtrip(self, store: EpisodicStore) -> None:
        payload = {"x": 1, "y": [2, 3, {"nested": True}]}
        record = EpisodicRecord(session_id="s", turn_id=1, role="assistant", content=payload, segment="answer")
        store.write_record(record)
        rows = store.read_records({"session_id": "s"})
        assert rows[0].content == payload
        assert rows[0].content_type == "json"

    def test_multiple_segments_per_turn(self, store: EpisodicStore) -> None:
        """One turn can produce scratchpad + answer + tool_output per DEC-0030."""
        for segment, content in [
            ("scratchpad", "let me think..."),
            ("answer", "the answer is 42"),
            ("tool_output", {"tool": "calculator", "result": 42}),
        ]:
            store.write_record(
                EpisodicRecord(
                    session_id="multi",
                    turn_id=1,
                    role="assistant",
                    segment=segment,
                    content=content,
                )
            )
        rows = store.read_records({"session_id": "multi"})
        assert len(rows) == 3
        assert {r.segment for r in rows} == {"scratchpad", "answer", "tool_output"}

    def test_uniqueness_constraint(self, store: EpisodicStore) -> None:
        """Same ``(session_id, turn_id, segment)`` cannot be inserted twice."""
        import sqlite3

        record = EpisodicRecord(session_id="dup", turn_id=1, role="user", segment="answer", content="x")
        store.write_record(record)
        with pytest.raises(sqlite3.IntegrityError):
            store.write_record(
                EpisodicRecord(
                    session_id="dup",
                    turn_id=1,
                    role="user",
                    segment="answer",
                    content="x",
                )
            )

    def test_parent_turn_id_recorded(self, store: EpisodicStore) -> None:
        """Parent-pointer chain survives a roundtrip."""
        store.write_record(EpisodicRecord(session_id="s", turn_id=1, role="user", content="first"))
        store.write_record(
            EpisodicRecord(
                session_id="s",
                turn_id=2,
                parent_turn_id=1,
                role="assistant",
                content="second",
            )
        )
        rows = store.read_records({"session_id": "s"})
        assert rows[0].parent_turn_id is None
        assert rows[1].parent_turn_id == 1

    def test_query_filters_supported_columns(self, store: EpisodicStore) -> None:
        for turn in range(1, 4):
            store.write_record(
                EpisodicRecord(
                    session_id="s",
                    turn_id=turn,
                    role="user" if turn == 1 else "assistant",
                    segment="scratchpad" if turn == 2 else "answer",
                    content=f"turn-{turn}",
                )
            )
        scratchpad = store.read_records({"segment": "scratchpad"})
        assert {r.turn_id for r in scratchpad} == {2}
        assistant = store.read_records({"role": "assistant"})
        assert {r.turn_id for r in assistant} == {2, 3}

    def test_query_unknown_key_raises(self, store: EpisodicStore) -> None:
        with pytest.raises(ValueError, match="Unsupported query keys"):
            store.read_records({"not_a_column": "value"})

    def test_query_limit_and_order(self, store: EpisodicStore) -> None:
        for turn in range(1, 6):
            store.write_record(EpisodicRecord(session_id="s", turn_id=turn, role="user", content=f"t{turn}"))
        first_two = store.read_records({"limit": 2})
        assert [r.turn_id for r in first_two] == [1, 2]
        last_two = store.read_records({"limit": 2, "order": "desc"})
        assert [r.turn_id for r in last_two] == [5, 4]

    def test_query_in_list(self, store: EpisodicStore) -> None:
        for turn in range(1, 4):
            store.write_record(EpisodicRecord(session_id=f"s{turn}", turn_id=1, role="user", content="x"))
        rows = store.read_records({"session_id": ["s1", "s3"]})
        assert {r.session_id for r in rows} == {"s1", "s3"}

    def test_content_hash_deterministic_across_writes(self, store: EpisodicStore) -> None:
        """Two records with identical content hash to the same value."""
        store.write_record(EpisodicRecord(session_id="s", turn_id=1, role="user", content="same payload"))
        # Same content in a different session must produce the same hash.
        store.write_record(EpisodicRecord(session_id="s2", turn_id=1, role="user", content="same payload"))
        hashes = {r.content_hash for r in store.read_records()}
        assert len(hashes) == 1
