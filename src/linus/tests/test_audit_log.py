"""Tests for :mod:`linus.memory.audit_log` — the append-only JSONL audit log.

The audit log is the observability + accountability surface for every Worker
dispatch and every episodic memory write (DEC-0030 / DEC-0031 / DEC-0032).
Under-testing it leaves the integrity-spine of the memory pillar fragile;
this suite brings the module to >=90% coverage with hermetic-only tests.

Every test uses ``tmp_path`` for an isolated audit-log location. No network,
no Ollama, no real ``~/.linus/`` touch. The ``LINUS_HOME`` path-resolution
test patches ``os.environ`` via ``monkeypatch`` for full hermeticity.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from linus.memory.audit_log import (
    DEFAULT_AUDIT_PATH,
    AuditLog,
    DispatchEvent,
    MemoryWriteEvent,
    default_audit_path,
)


# ── module-level constants + default_audit_path() ──────────────────────────


def test_default_audit_path_constant_points_under_dot_linus() -> None:
    """The DEFAULT_AUDIT_PATH constant must resolve to ``~/.linus/audit.jsonl``
    so the on-disk artifact landing-zone is stable across releases."""
    assert DEFAULT_AUDIT_PATH == Path.home() / ".linus" / "audit.jsonl"
    assert DEFAULT_AUDIT_PATH.name == "audit.jsonl"


def test_default_audit_path_unset_env_returns_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """With ``LINUS_HOME`` unset, default_audit_path() returns the module
    DEFAULT_AUDIT_PATH constant."""
    monkeypatch.delenv("LINUS_HOME", raising=False)
    assert default_audit_path() == DEFAULT_AUDIT_PATH


def test_default_audit_path_honors_linus_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """When ``LINUS_HOME`` is set, default_audit_path() places audit.jsonl
    under that root — the hermetic-test escape hatch the spec contracts on."""
    monkeypatch.setenv("LINUS_HOME", str(tmp_path))
    assert default_audit_path() == tmp_path / "audit.jsonl"


def test_default_audit_path_empty_linus_home_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty ``LINUS_HOME`` string is falsy under walrus-assign, so the
    function falls back to DEFAULT_AUDIT_PATH rather than treating it as a
    valid root."""
    monkeypatch.setenv("LINUS_HOME", "")
    assert default_audit_path() == DEFAULT_AUDIT_PATH


# ── DispatchEvent validation (__post_init__) ───────────────────────────────


def _valid_dispatch_kwargs(**overrides: object) -> dict[str, object]:
    """Minimal valid kwargs for a DispatchEvent; overrides plug in per-test values."""
    base: dict[str, object] = dict(
        session_id="sid-1",
        turn_id=1,
        worker_id="qwen3:8b",
        cot_budget="linear",
        memory_mode="session_stateful",
        context_used_tokens=8421,
        context_capped=False,
    )
    base.update(overrides)
    return base


@pytest.mark.parametrize("budget", ["logarithmic", "linear", "polynomial"])
def test_dispatch_event_accepts_each_allowed_cot_budget(budget: str) -> None:
    """All three DEC-0031 cot_budget regimes construct cleanly."""
    event = DispatchEvent(**_valid_dispatch_kwargs(cot_budget=budget))
    assert event.cot_budget == budget


def test_dispatch_event_rejects_bogus_cot_budget() -> None:
    """A cot_budget outside the DEC-0031 vocabulary must raise ValueError —
    the audit log refuses to record nonsense regimes so corrupted call sites
    cannot pollute the integrity record."""
    with pytest.raises(ValueError, match="cot_budget must be one of"):
        DispatchEvent(**_valid_dispatch_kwargs(cot_budget="exponential"))


@pytest.mark.parametrize("mode", ["stateless", "session_stateful", "project_stateful"])
def test_dispatch_event_accepts_each_allowed_memory_mode(mode: str) -> None:
    """All three DEC-0031 memory_mode regimes construct cleanly."""
    event = DispatchEvent(**_valid_dispatch_kwargs(memory_mode=mode))
    assert event.memory_mode == mode


def test_dispatch_event_rejects_bogus_memory_mode() -> None:
    """A memory_mode outside the DEC-0031 vocabulary must raise ValueError."""
    with pytest.raises(ValueError, match="memory_mode must be one of"):
        DispatchEvent(**_valid_dispatch_kwargs(memory_mode="amnesiac"))


@pytest.mark.parametrize("overflow", [None, "drop", "summarize", "retrieve"])
def test_dispatch_event_accepts_each_allowed_overflow_action(overflow: str | None) -> None:
    """The four allowed context_overflow_action values construct cleanly."""
    event = DispatchEvent(**_valid_dispatch_kwargs(context_overflow_action=overflow))
    assert event.context_overflow_action == overflow


def test_dispatch_event_rejects_bogus_overflow_action() -> None:
    """An unrecognized context_overflow_action must raise ValueError."""
    with pytest.raises(ValueError, match="context_overflow_action must be one of"):
        DispatchEvent(**_valid_dispatch_kwargs(context_overflow_action="truncate"))


def test_dispatch_event_default_fields_populated() -> None:
    """Default factories produce empty mutable defaults — verify no shared
    state across instances and the documented event_type default."""
    e1 = DispatchEvent(**_valid_dispatch_kwargs())
    e2 = DispatchEvent(**_valid_dispatch_kwargs())
    assert e1.per_layer_breakdown == {}
    assert e1.input_hashes == []
    assert e1.output_hashes == []
    assert e1.tags == []
    assert e1.event_type == "dispatch"
    assert e1.context_overflow_action is None
    assert e1.context_cap_override is None
    assert e1.timestamp is None
    # Mutate one and confirm the other is unaffected (no shared mutable default).
    e1.tags.append("project:linus")
    assert e2.tags == []


# ── MemoryWriteEvent construction ──────────────────────────────────────────


def test_memory_write_event_minimal_construction() -> None:
    """MemoryWriteEvent only requires session_id, turn_id, segment, content_hash."""
    event = MemoryWriteEvent(
        session_id="sid-1",
        turn_id=4,
        segment="scratchpad",
        content_hash="sha256:abc123",
    )
    assert event.parent_hash is None
    assert event.timestamp is None
    assert event.event_type == "memory_write"


def test_memory_write_event_accepts_segment_none() -> None:
    """Per the type hint ``segment: str | None``, an unsegmented write
    (no scratchpad/answer/tool_output category) is allowed."""
    event = MemoryWriteEvent(
        session_id="sid-1",
        turn_id=4,
        segment=None,
        content_hash="sha256:abc123",
    )
    assert event.segment is None


# ── AuditLog construction + path handling ──────────────────────────────────


def test_auditlog_init_creates_parent_dir(tmp_path: Path) -> None:
    """__init__ creates the audit file's parent directory if it doesn't
    exist (the canonical first-run case)."""
    target = tmp_path / "nested" / "deep" / "audit.jsonl"
    log = AuditLog(target)
    assert log.path == target
    assert target.parent.is_dir()
    assert target.exists()


def test_auditlog_init_touches_empty_file(tmp_path: Path) -> None:
    """__init__ touches the audit file so subsequent read_events calls
    succeed even before any writes happen."""
    target = tmp_path / "audit.jsonl"
    log = AuditLog(target)
    assert target.exists()
    assert target.read_text(encoding="utf-8") == ""
    # Reading the empty file yields no events without error.
    assert log.read_events() == []


def test_auditlog_init_accepts_str_path(tmp_path: Path) -> None:
    """The constructor accepts a str path as well as a Path."""
    target = tmp_path / "audit.jsonl"
    log = AuditLog(str(target))
    assert isinstance(log.path, Path)
    assert log.path == target


def test_auditlog_init_default_path_honors_linus_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """With ``path=None``, the constructor falls back to default_audit_path()
    which honors LINUS_HOME — the hermetic escape hatch."""
    monkeypatch.setenv("LINUS_HOME", str(tmp_path))
    log = AuditLog()
    assert log.path == tmp_path / "audit.jsonl"
    assert log.path.exists()


def test_auditlog_init_preserves_existing_file_contents(tmp_path: Path) -> None:
    """``touch(exist_ok=True)`` must not clobber a pre-existing audit file —
    the log is append-only across process restarts."""
    target = tmp_path / "audit.jsonl"
    target.write_text('{"event_type":"dispatch","session_id":"prior"}\n', encoding="utf-8")
    AuditLog(target)
    assert "prior" in target.read_text(encoding="utf-8")


# ── append_dispatch happy path + auto-timestamp ────────────────────────────


def test_append_dispatch_returns_serialized_dict(tmp_path: Path) -> None:
    """append_dispatch returns the exact dict shape that was serialized,
    useful for tests + log consumers."""
    log = AuditLog(tmp_path / "audit.jsonl")
    event = DispatchEvent(**_valid_dispatch_kwargs())
    written = log.append_dispatch(event)
    assert written["event_type"] == "dispatch"
    assert written["session_id"] == "sid-1"
    assert written["worker_id"] == "qwen3:8b"
    assert written["cot_budget"] == "linear"
    assert written["memory_mode"] == "session_stateful"
    assert written["context_used_tokens"] == 8421
    assert written["context_capped"] is False


def test_append_dispatch_auto_fills_timestamp(tmp_path: Path) -> None:
    """When event.timestamp is None at append time, it is auto-filled with
    a sortable ISO-8601 UTC string."""
    log = AuditLog(tmp_path / "audit.jsonl")
    event = DispatchEvent(**_valid_dispatch_kwargs())
    assert event.timestamp is None
    written = log.append_dispatch(event)
    assert isinstance(written["timestamp"], str)
    # ISO-8601 UTC: YYYY-MM-DDTHH:MM:SS(.ffffff)+00:00
    assert re.match(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?\+00:00$",
        written["timestamp"],
    )
    # And the event itself is mutated in place (the spec says auto-fill).
    assert event.timestamp == written["timestamp"]


def test_append_dispatch_honors_provided_timestamp(tmp_path: Path) -> None:
    """A caller-supplied timestamp is not overwritten."""
    log = AuditLog(tmp_path / "audit.jsonl")
    pinned = "2026-05-19T12:34:56+00:00"
    event = DispatchEvent(**_valid_dispatch_kwargs(timestamp=pinned))
    written = log.append_dispatch(event)
    assert written["timestamp"] == pinned


def test_append_dispatch_persists_one_line_per_call(tmp_path: Path) -> None:
    """Each append writes exactly one ``\\n``-terminated JSON line; partial
    lines cannot survive flush+fsync."""
    target = tmp_path / "audit.jsonl"
    log = AuditLog(target)
    log.append_dispatch(DispatchEvent(**_valid_dispatch_kwargs(session_id="s1")))
    log.append_dispatch(DispatchEvent(**_valid_dispatch_kwargs(session_id="s2", turn_id=2)))
    raw = target.read_text(encoding="utf-8")
    lines = raw.splitlines()
    assert len(lines) == 2
    assert raw.endswith("\n")
    parsed = [json.loads(line) for line in lines]
    assert parsed[0]["session_id"] == "s1"
    assert parsed[1]["session_id"] == "s2"


def test_append_dispatch_writes_canonical_json(tmp_path: Path) -> None:
    """JSON is serialized with sort_keys + no whitespace separator so lines
    are diffable and stable across runs."""
    target = tmp_path / "audit.jsonl"
    log = AuditLog(target)
    log.append_dispatch(DispatchEvent(**_valid_dispatch_kwargs()))
    raw_line = target.read_text(encoding="utf-8").strip()
    # No whitespace around ``:`` or ``,``.
    assert ": " not in raw_line
    assert ", " not in raw_line
    # Keys are sorted: event_type < session_id alphabetically.
    obj = json.loads(raw_line)
    serialized_again = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    assert raw_line == serialized_again


def test_append_dispatch_records_per_layer_breakdown_and_tags(tmp_path: Path) -> None:
    """The full DEC-0031 payload (per_layer_breakdown, input_hashes,
    output_hashes, tags, context_cap_override) round-trips intact."""
    target = tmp_path / "audit.jsonl"
    log = AuditLog(target)
    event = DispatchEvent(
        **_valid_dispatch_kwargs(
            context_used_tokens=12000,
            context_capped=True,
            context_overflow_action="summarize",
            per_layer_breakdown={"task_spec": 1024, "kb_context": 2048, "session": 8928},
            context_cap_override=16384,
            input_hashes=["sha256:in1", "sha256:in2"],
            output_hashes=["sha256:out1"],
            tags=["project:linus", "skill:default"],
        )
    )
    written = log.append_dispatch(event)
    assert written["per_layer_breakdown"] == {"task_spec": 1024, "kb_context": 2048, "session": 8928}
    assert written["context_capped"] is True
    assert written["context_overflow_action"] == "summarize"
    assert written["context_cap_override"] == 16384
    assert written["input_hashes"] == ["sha256:in1", "sha256:in2"]
    assert written["output_hashes"] == ["sha256:out1"]
    assert written["tags"] == ["project:linus", "skill:default"]
    # Round-trip through the file.
    on_disk = json.loads(target.read_text(encoding="utf-8").strip())
    assert on_disk == written


# ── append_memory_write happy path + auto-timestamp ────────────────────────


def test_append_memory_write_returns_serialized_dict(tmp_path: Path) -> None:
    """append_memory_write returns the exact dict shape that was serialized."""
    log = AuditLog(tmp_path / "audit.jsonl")
    event = MemoryWriteEvent(
        session_id="sid-1",
        turn_id=17,
        segment="scratchpad",
        content_hash="sha256:deadbeef",
        parent_hash="sha256:cafebabe",
    )
    written = log.append_memory_write(event)
    assert written["event_type"] == "memory_write"
    assert written["session_id"] == "sid-1"
    assert written["turn_id"] == 17
    assert written["segment"] == "scratchpad"
    assert written["content_hash"] == "sha256:deadbeef"
    assert written["parent_hash"] == "sha256:cafebabe"


def test_append_memory_write_auto_fills_timestamp(tmp_path: Path) -> None:
    """When event.timestamp is None at append time, it is auto-filled."""
    log = AuditLog(tmp_path / "audit.jsonl")
    event = MemoryWriteEvent(
        session_id="sid-1",
        turn_id=4,
        segment="answer",
        content_hash="sha256:abc",
    )
    assert event.timestamp is None
    written = log.append_memory_write(event)
    assert isinstance(written["timestamp"], str)
    assert event.timestamp == written["timestamp"]


def test_append_memory_write_honors_provided_timestamp(tmp_path: Path) -> None:
    """A caller-supplied timestamp on a MemoryWriteEvent is preserved."""
    log = AuditLog(tmp_path / "audit.jsonl")
    pinned = "2026-05-19T01:02:03+00:00"
    event = MemoryWriteEvent(
        session_id="sid-1",
        turn_id=4,
        segment="answer",
        content_hash="sha256:abc",
        timestamp=pinned,
    )
    written = log.append_memory_write(event)
    assert written["timestamp"] == pinned


def test_append_memory_write_accepts_null_parent_hash(tmp_path: Path) -> None:
    """A genesis write (no parent) records parent_hash=None on disk."""
    target = tmp_path / "audit.jsonl"
    log = AuditLog(target)
    log.append_memory_write(
        MemoryWriteEvent(
            session_id="sid-1",
            turn_id=0,
            segment="scratchpad",
            content_hash="sha256:genesis",
        )
    )
    on_disk = json.loads(target.read_text(encoding="utf-8").strip())
    assert on_disk["parent_hash"] is None


# ── read_events / iter_events ──────────────────────────────────────────────


def test_read_events_empty_log_returns_empty_list(tmp_path: Path) -> None:
    """A freshly initialized (touched but unwritten) audit log returns an
    empty event list — no exception."""
    log = AuditLog(tmp_path / "audit.jsonl")
    assert log.read_events() == []


def test_read_events_preserves_append_order(tmp_path: Path) -> None:
    """read_events returns dicts in the order they were appended."""
    log = AuditLog(tmp_path / "audit.jsonl")
    log.append_dispatch(DispatchEvent(**_valid_dispatch_kwargs(session_id="s1", turn_id=1)))
    log.append_memory_write(
        MemoryWriteEvent(
            session_id="s1", turn_id=1, segment="scratchpad", content_hash="sha256:1"
        )
    )
    log.append_dispatch(DispatchEvent(**_valid_dispatch_kwargs(session_id="s1", turn_id=2)))
    events = log.read_events()
    assert len(events) == 3
    assert events[0]["event_type"] == "dispatch"
    assert events[0]["turn_id"] == 1
    assert events[1]["event_type"] == "memory_write"
    assert events[2]["event_type"] == "dispatch"
    assert events[2]["turn_id"] == 2


def test_read_events_round_trips_dispatch(tmp_path: Path) -> None:
    """Write a DispatchEvent, read it back, fields match exactly."""
    log = AuditLog(tmp_path / "audit.jsonl")
    written = log.append_dispatch(DispatchEvent(**_valid_dispatch_kwargs()))
    read_back = log.read_events()
    assert len(read_back) == 1
    assert read_back[0] == written


def test_read_events_round_trips_memory_write(tmp_path: Path) -> None:
    """Write a MemoryWriteEvent, read it back, fields match exactly."""
    log = AuditLog(tmp_path / "audit.jsonl")
    written = log.append_memory_write(
        MemoryWriteEvent(
            session_id="sid-1",
            turn_id=4,
            segment="tool_output",
            content_hash="sha256:tool",
            parent_hash="sha256:parent",
        )
    )
    read_back = log.read_events()
    assert len(read_back) == 1
    assert read_back[0] == written


def test_iter_events_is_lazy_generator(tmp_path: Path) -> None:
    """iter_events returns an iterator (generator), not a materialized list —
    suitable for the large-volume case."""
    import collections.abc

    log = AuditLog(tmp_path / "audit.jsonl")
    log.append_dispatch(DispatchEvent(**_valid_dispatch_kwargs()))
    it = log.iter_events()
    assert isinstance(it, collections.abc.Iterator)
    assert not isinstance(it, list)
    consumed = list(it)
    assert len(consumed) == 1


def test_iter_events_skips_blank_lines(tmp_path: Path) -> None:
    """Blank lines mid-file (e.g., from manual editing or a partial write
    recovered by truncation) are silently skipped by iter_events."""
    target = tmp_path / "audit.jsonl"
    log = AuditLog(target)
    log.append_dispatch(DispatchEvent(**_valid_dispatch_kwargs(session_id="s1")))
    log.append_dispatch(DispatchEvent(**_valid_dispatch_kwargs(session_id="s2", turn_id=2)))
    # Inject a blank line + a whitespace-only line between entries.
    current = target.read_text(encoding="utf-8")
    target.write_text(current + "\n   \n", encoding="utf-8")
    events = log.read_events()
    assert len(events) == 2
    assert events[0]["session_id"] == "s1"
    assert events[1]["session_id"] == "s2"


def test_iter_events_returns_empty_when_path_missing(tmp_path: Path) -> None:
    """If the audit file is deleted after construction (e.g., manual cleanup
    or test teardown), iter_events yields nothing rather than raising —
    the early-return guard in the generator."""
    target = tmp_path / "audit.jsonl"
    log = AuditLog(target)
    target.unlink()
    assert log.read_events() == []
    # Re-confirm via the iterator directly (covers the generator early-return).
    assert list(log.iter_events()) == []


def test_read_events_handles_many_appends(tmp_path: Path) -> None:
    """Sequential appends produce N lines, all readable back. Stand-in for
    concurrent-write safety (the module is single-writer v0 per docstring)."""
    log = AuditLog(tmp_path / "audit.jsonl")
    n = 50
    for i in range(n):
        log.append_dispatch(DispatchEvent(**_valid_dispatch_kwargs(session_id=f"s{i}", turn_id=i)))
    events = log.read_events()
    assert len(events) == n
    assert [e["session_id"] for e in events] == [f"s{i}" for i in range(n)]
    assert [e["turn_id"] for e in events] == list(range(n))


def test_appends_are_durable_across_logger_instances(tmp_path: Path) -> None:
    """A second AuditLog over the same path sees writes from the first —
    the file is the source of truth, not in-memory state."""
    target = tmp_path / "audit.jsonl"
    log1 = AuditLog(target)
    log1.append_dispatch(DispatchEvent(**_valid_dispatch_kwargs(session_id="first")))
    log2 = AuditLog(target)
    log2.append_dispatch(DispatchEvent(**_valid_dispatch_kwargs(session_id="second", turn_id=2)))
    events = log2.read_events()
    assert [e["session_id"] for e in events] == ["first", "second"]


# ── serialization edge cases ───────────────────────────────────────────────


def test_append_dispatch_rejects_nan_in_payload(tmp_path: Path) -> None:
    """``allow_nan=False`` in the serializer must reject non-finite floats —
    NaN cannot round-trip through strict JSON and would corrupt the log."""
    log = AuditLog(tmp_path / "audit.jsonl")
    # Stuff a NaN into per_layer_breakdown — the only float-friendly field.
    event = DispatchEvent(
        **_valid_dispatch_kwargs(per_layer_breakdown={"layer_a": float("nan")})
    )
    with pytest.raises(ValueError):
        log.append_dispatch(event)


def test_append_dispatch_preserves_unicode_in_tags(tmp_path: Path) -> None:
    """``ensure_ascii=False`` keeps non-ASCII characters as-is in the log —
    important for any internationalized session metadata."""
    target = tmp_path / "audit.jsonl"
    log = AuditLog(target)
    log.append_dispatch(
        DispatchEvent(**_valid_dispatch_kwargs(tags=["project:linus", "topic:λ-calculus"]))
    )
    raw = target.read_text(encoding="utf-8")
    assert "λ-calculus" in raw
    on_disk = json.loads(raw.strip())
    assert on_disk["tags"] == ["project:linus", "topic:λ-calculus"]
