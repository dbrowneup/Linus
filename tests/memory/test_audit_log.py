"""Unit tests for :mod:`linus.memory.audit_log`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from linus.memory.audit_log import AuditLog, DispatchEvent, MemoryWriteEvent


@pytest.fixture()
def audit(tmp_path: Path) -> AuditLog:
    """Fresh audit log on a tmp path; never touches ``~/.linus/``."""
    return AuditLog(path=tmp_path / "audit.jsonl")


class TestAuditLogAppendJsonl:
    """Spec test: ``test_audit_log_append_jsonl``."""

    def test_appends_dispatch_event(self, audit: AuditLog) -> None:
        event = DispatchEvent(
            session_id="s",
            turn_id=1,
            worker_id="qwen3:8b",
            cot_budget="linear",
            memory_mode="session_stateful",
            context_used_tokens=1024,
            context_capped=False,
            per_layer_breakdown={"task_spec": 1024},
            output_hashes=["sha256:abc"],
        )
        line = audit.append_dispatch(event)
        assert line["event_type"] == "dispatch"
        assert line["timestamp"] is not None

        events = audit.read_events()
        assert len(events) == 1
        assert events[0]["worker_id"] == "qwen3:8b"
        assert events[0]["cot_budget"] == "linear"
        assert events[0]["memory_mode"] == "session_stateful"
        assert events[0]["context_used_tokens"] == 1024
        assert events[0]["output_hashes"] == ["sha256:abc"]

    def test_appends_memory_write_event(self, audit: AuditLog) -> None:
        event = MemoryWriteEvent(
            session_id="s",
            turn_id=1,
            segment="answer",
            content_hash="sha256:deadbeef",
        )
        audit.append_memory_write(event)
        events = audit.read_events()
        assert len(events) == 1
        assert events[0]["event_type"] == "memory_write"
        assert events[0]["content_hash"] == "sha256:deadbeef"

    def test_append_order_preserved(self, audit: AuditLog) -> None:
        """Order of events read back matches the order they were appended."""
        for turn in range(1, 6):
            audit.append_memory_write(
                MemoryWriteEvent(
                    session_id="s",
                    turn_id=turn,
                    segment="answer",
                    content_hash=f"sha256:turn-{turn}",
                )
            )
        events = audit.read_events()
        assert [e["turn_id"] for e in events] == [1, 2, 3, 4, 5]

    def test_file_is_valid_jsonl(self, audit: AuditLog) -> None:
        """Every non-empty line in the file is a parseable JSON object."""
        audit.append_dispatch(
            DispatchEvent(
                session_id="s",
                turn_id=1,
                worker_id="w",
                cot_budget="logarithmic",
                memory_mode="stateless",
                context_used_tokens=128,
                context_capped=False,
            )
        )
        audit.append_memory_write(
            MemoryWriteEvent(
                session_id="s",
                turn_id=1,
                segment="scratchpad",
                content_hash="sha256:x",
            )
        )
        # Read the raw file: every line must parse.
        with open(audit.path, encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                parsed = json.loads(raw)
                assert "event_type" in parsed
                assert "timestamp" in parsed

    def test_appends_survive_multiple_audit_instances(self, tmp_path: Path) -> None:
        """A second :class:`AuditLog` against the same path sees prior events.

        Models the realistic case where the dispatcher process restarts.
        """
        path = tmp_path / "audit.jsonl"
        a1 = AuditLog(path=path)
        a1.append_memory_write(MemoryWriteEvent(session_id="s", turn_id=1, segment="answer", content_hash="sha256:a"))
        a2 = AuditLog(path=path)
        a2.append_memory_write(MemoryWriteEvent(session_id="s", turn_id=2, segment="answer", content_hash="sha256:b"))
        events = a2.read_events()
        assert [e["turn_id"] for e in events] == [1, 2]

    def test_invalid_cot_budget_rejected(self) -> None:
        with pytest.raises(ValueError, match="cot_budget"):
            DispatchEvent(
                session_id="s",
                turn_id=1,
                worker_id="w",
                cot_budget="quadratic",  # not a valid regime per DEC-0031
                memory_mode="stateless",
                context_used_tokens=1,
                context_capped=False,
            )

    def test_invalid_memory_mode_rejected(self) -> None:
        with pytest.raises(ValueError, match="memory_mode"):
            DispatchEvent(
                session_id="s",
                turn_id=1,
                worker_id="w",
                cot_budget="linear",
                memory_mode="omniscient",  # not a valid mode per DEC-0031
                context_used_tokens=1,
                context_capped=False,
            )

    def test_invalid_overflow_action_rejected(self) -> None:
        with pytest.raises(ValueError, match="context_overflow_action"):
            DispatchEvent(
                session_id="s",
                turn_id=1,
                worker_id="w",
                cot_budget="linear",
                memory_mode="stateless",
                context_used_tokens=1,
                context_capped=True,
                context_overflow_action="invent",
            )

    def test_cap_override_recorded(self, audit: AuditLog) -> None:
        """Per DEC-0032 the bypass mechanism is intentionally noisy in the audit log."""
        event = DispatchEvent(
            session_id="s",
            turn_id=1,
            worker_id="w",
            cot_budget="linear",
            memory_mode="stateless",
            context_used_tokens=128_000,
            context_capped=False,
            context_cap_override=128_000,
            tags=["bypass:single_shot_whole_paper"],
        )
        audit.append_dispatch(event)
        events = audit.read_events()
        assert events[0]["context_cap_override"] == 128_000
        assert "bypass:single_shot_whole_paper" in events[0]["tags"]

    def test_iter_events_lazy(self, audit: AuditLog) -> None:
        """``iter_events`` returns a generator, not a list."""
        import types

        audit.append_memory_write(MemoryWriteEvent(session_id="s", turn_id=1, segment=None, content_hash="x"))
        gen = audit.iter_events()
        assert isinstance(gen, types.GeneratorType)
        assert next(gen)["content_hash"] == "x"
