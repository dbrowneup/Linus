"""Append-only JSONL audit log for Worker dispatches and memory writes.

Per the audit-log contract in
[`docs/specs/memory-architecture.md`](../../../docs/specs/memory-architecture.md) and
DEC-0030 / DEC-0031 / DEC-0032, every Worker dispatch and every scratchpad / answer /
tool_output write produces one line in ``~/.linus/audit.jsonl``. The log is the
cryptographic spine that lets the episodic store be verified after the fact — if the
SQLite DB is corrupted or rebuilt, the audit log's content-hash chain proves what was
durably committed.

## Why JSONL and not a database

Three reasons:

1. **Append-only is the property we want.** A flat JSONL file is unambiguously
   append-only at the OS level; databases can be rewritten in place. Audit data must
   be tamper-evident in the simplest possible way.
2. **Independent of the episodic substrate.** If SQLite corrupts, the audit log is
   still readable with ``cat``. If we tried to put the audit log inside the same DB
   we'd lose the integrity backstop in exactly the situation where we need it.
3. **Cheap to ship to a remote append-only log later.** The line shape is stable; a
   future "tee to S3 / OpenZL / append-only WORM target" wrapper is a one-file change.

## Line shape

Each line is a single JSON object terminated by ``\\n``. Two event kinds are recorded
at v0; both share an envelope of ``timestamp`` (ISO-8601 UTC), ``event_type``, and an
event-specific payload.

### ``event_type = "dispatch"``

Per DEC-0031, every Worker dispatch records:

    {
      "timestamp": "...",
      "event_type": "dispatch",
      "session_id": "...",
      "turn_id": 17,
      "worker_id": "qwen3:8b",
      "cot_budget": "linear",
      "memory_mode": "session_stateful",
      "context_used_tokens": 8421,
      "context_capped": false,
      "context_overflow_action": null,
      "per_layer_breakdown": {"task_spec": 1024, "kb_context": 2048, "session": 5349},
      "context_cap_override": null,
      "input_hashes": ["sha256:..."],
      "output_hashes": ["sha256:..."],
      "tags": ["project:linus", "skill:default"],
      "network_egress": [
        {"url_host": "eutils.ncbi.nlm.nih.gov", "query_hash": "sha256:...",
         "response_size": 4096, "latency_ms": 142.3, "timestamp_ns": 1716240000000000000}
      ]
    }

Per DEC-0061, ``network_egress`` is the optional capture-list of external
HTTP calls a tool made during this dispatch. Backwards-compatible: pre-DEC-0061
records simply omit the field. Each entry is minimum-disclosure — host, query
hash, response size, latency, and a wall-clock nanosecond timestamp — never the
full URL or response body.

### ``event_type = "memory_write"``

Per DEC-0030, every episodic record write records:

    {
      "timestamp": "...",
      "event_type": "memory_write",
      "session_id": "...",
      "turn_id": 17,
      "segment": "scratchpad",
      "content_hash": "sha256:...",
      "parent_hash": "sha256:..." | null
    }

The two-event shape lets the dispatch event reference the memory_write events that
produced its outputs (via ``output_hashes``) without duplicating the content itself.

## Scope of this module (Phase 2h.2 deliverable)

- Append a dispatch event.
- Append a memory-write event.
- Read events back (line-by-line, parsed).
- Atomic append: each write is one ``write()`` call followed by ``flush()`` and
  ``fsync()`` so partial lines cannot survive a crash.

Out of scope: rotation, compaction, integrity-verification sweeps. Those are Phase 3+
operational concerns.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

__all__ = [
    "DEFAULT_AUDIT_PATH",
    "AuditLog",
    "DispatchEvent",
    "MemoryWriteEvent",
    "default_audit_path",
]


#: Default location of the v0 audit log, per the memory-architecture spec.
DEFAULT_AUDIT_PATH = Path.home() / ".linus" / "audit.jsonl"


def default_audit_path() -> Path:
    """Return the default audit-log path, honoring ``LINUS_HOME`` if set."""
    if env_root := os.environ.get("LINUS_HOME"):
        return Path(env_root) / "audit.jsonl"
    return DEFAULT_AUDIT_PATH


def _utcnow() -> str:
    """Return the current UTC timestamp as a sortable ISO-8601 string."""
    return datetime.now(tz=UTC).isoformat()


# ---------------------------------------------------------------------------
# Event dataclasses


@dataclass(slots=True)
class DispatchEvent:
    """The per-dispatch audit-log line, per DEC-0031 contract.

    See module docstring for field semantics. All non-default fields are required;
    ``timestamp`` is auto-filled to "now" if absent.

    ``network_egress`` (per DEC-0061) is the optional capture-list of external
    HTTP calls a Worker tool made during this dispatch. Each entry has shape
    ``{url_host, query_hash, response_size, latency_ms, timestamp_ns}`` and is
    minimum-disclosure: host (not full URL), query hash (not query text),
    response size (not body). The field is optional and backwards-compatible
    — records without it parse exactly as before; readers built before
    DEC-0061 continue to work because ``asdict`` emits ``"network_egress":
    []`` only when the writer set one.

    Default factory produces a fresh empty list per-instance so the captured
    egress for one dispatch does not bleed into another (the canonical
    "mutable default" footgun applied to audit-log records).
    """

    session_id: str
    turn_id: int
    worker_id: str
    cot_budget: str
    memory_mode: str
    context_used_tokens: int
    context_capped: bool
    context_overflow_action: str | None = None
    per_layer_breakdown: dict[str, int] = field(default_factory=dict)
    context_cap_override: int | None = None
    input_hashes: list[str] = field(default_factory=list)
    output_hashes: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    network_egress: list[dict[str, Any]] = field(default_factory=list)
    timestamp: str | None = None
    event_type: str = "dispatch"

    def __post_init__(self) -> None:
        # Validate router-primitive values cheaply. The router refuses impossible
        # combinations per DEC-0031; the audit log refuses to record nonsense regimes
        # so a corrupted call site cannot pollute the integrity record.
        allowed_budgets = {"logarithmic", "linear", "polynomial"}
        if self.cot_budget not in allowed_budgets:
            raise ValueError(f"cot_budget must be one of {sorted(allowed_budgets)}, got {self.cot_budget!r}")
        allowed_modes = {"stateless", "session_stateful", "project_stateful"}
        if self.memory_mode not in allowed_modes:
            raise ValueError(f"memory_mode must be one of {sorted(allowed_modes)}, got {self.memory_mode!r}")
        allowed_overflow = {None, "drop", "summarize", "retrieve"}
        if self.context_overflow_action not in allowed_overflow:
            raise ValueError(
                "context_overflow_action must be one of "
                f"{{None, 'drop', 'summarize', 'retrieve'}}, "
                f"got {self.context_overflow_action!r}"
            )


@dataclass(slots=True)
class MemoryWriteEvent:
    """The per-record-write audit-log line, per DEC-0030 contract."""

    session_id: str
    turn_id: int
    segment: str | None
    content_hash: str
    parent_hash: str | None = None
    timestamp: str | None = None
    event_type: str = "memory_write"


# ---------------------------------------------------------------------------
# Writer


class AuditLog:
    """Append-only JSONL audit-log writer.

    The audit file is created on first call (along with its parent directory).
    Subsequent appends use ``"a"`` mode, ``utf-8`` encoding, and follow each write
    with ``flush() + fsync()`` so partial lines cannot survive a crash.

    Args:
        path: Override for the log location. Defaults to :func:`default_audit_path`.

    Thread-safety: not currently guaranteed. Phase 3+ multi-Worker dispatches will
    need a lock or a single-writer dispatch thread; v0 is single-writer.
    """

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else default_audit_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Touch the file so subsequent ``read_events`` calls succeed even before any
        # writes have happened.
        self.path.touch(exist_ok=True)

    # -- writes ---------------------------------------------------------------

    def append_dispatch(self, event: DispatchEvent) -> dict[str, Any]:
        """Append a dispatch event. Returns the written line as a dict.

        ``event.timestamp`` is auto-filled if absent. The returned dict is the exact
        shape that was serialized — useful for tests and for log consumers that want
        to observe what was just persisted without re-reading the file.
        """
        if event.timestamp is None:
            event.timestamp = _utcnow()
        line = asdict(event)
        self._append_json(line)
        return line

    def append_memory_write(self, event: MemoryWriteEvent) -> dict[str, Any]:
        """Append a memory-write event. Returns the written line as a dict."""
        if event.timestamp is None:
            event.timestamp = _utcnow()
        line = asdict(event)
        self._append_json(line)
        return line

    def _append_json(self, payload: dict[str, Any]) -> None:
        """Serialize ``payload`` to one canonical JSON line and durably append it."""
        # Canonical JSON (sort keys, no whitespace) keeps lines diffable and stable.
        serialized = json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(serialized + "\n")
            fh.flush()
            os.fsync(fh.fileno())

    # -- reads ----------------------------------------------------------------

    def read_events(self) -> list[dict[str, Any]]:
        """Return every event line as a list of dicts, in append order.

        Suitable for tests and for small-volume operational inspection. For the
        large-volume case, prefer :meth:`iter_events` (lazy generator).
        """
        return list(self.iter_events())

    def iter_events(self) -> Iterator[dict[str, Any]]:
        """Yield every event line, in append order."""
        if not self.path.exists():
            return
        with open(self.path, encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                yield json.loads(raw)
