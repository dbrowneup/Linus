"""Demo script for the Phase 2h.1-2 memory scaffolding.

Run with ``python -m linus.memory.demo``. Writes one episodic record, reads it back,
and appends one audit-log line — exercising both modules end to end against the real
``~/.linus/`` directory (or a tmp dir if ``LINUS_HOME`` is set).

This is the smoke-test gate per CLAUDE.md convention: if the demo runs clean, the
unit tests are checking what real users will hit.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from linus.memory.audit_log import AuditLog, DispatchEvent, MemoryWriteEvent
from linus.memory.episodic import EpisodicRecord, EpisodicStore


def main() -> None:
    """Run the smoke demo."""
    print("=" * 72)
    print("Linus memory v0 demo (Phase 2h.1-2)")
    print("=" * 72)

    store = EpisodicStore()
    print(f"\nEpisodic store opened at: {store.db_path}")

    session_id = f"demo-{datetime.now(tz=UTC).strftime('%Y%m%dT%H%M%S')}"
    record = EpisodicRecord(
        session_id=session_id,
        turn_id=1,
        role="user",
        segment="answer",
        content="Hello, Linus. This is the Phase 2h.1-2 smoke demo.",
        trust_level="user",
        tags=["demo", "phase2h"],
    )
    h = store.write_record(record)
    print(f"  wrote record turn_id=1 → content_hash={h}")

    records = store.read_records({"session_id": session_id})
    assert len(records) == 1, f"expected 1 record, got {len(records)}"
    print(f"  read back {len(records)} record")
    print(f"    content: {records[0].content!r}")

    audit = AuditLog()
    print(f"\nAudit log opened at: {audit.path}")

    audit.append_memory_write(
        MemoryWriteEvent(
            session_id=session_id,
            turn_id=1,
            segment="answer",
            content_hash=h,
        )
    )
    print("  appended memory_write event")

    audit.append_dispatch(
        DispatchEvent(
            session_id=session_id,
            turn_id=1,
            worker_id="demo:none",
            cot_budget="logarithmic",
            memory_mode="stateless",
            context_used_tokens=42,
            context_capped=False,
            per_layer_breakdown={"task_spec": 42},
            output_hashes=[h],
            tags=["demo", "phase2h"],
        )
    )
    print("  appended dispatch event")

    last_two = audit.read_events()[-2:]
    print("\nLast two audit events:")
    for line in last_two:
        print("  " + json.dumps(line, sort_keys=True))

    print("\nDemo complete.")


if __name__ == "__main__":
    main()
