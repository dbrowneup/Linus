"""Linus memory pillar — Phase 2h scaffolding.

See [`docs/specs/memory-architecture.md`](../../../docs/specs/memory-architecture.md) for
the full spec; the v0 substrate decisions are in DEC-0028 through DEC-0043.

Phase 2h.1-2 deliverables shipped in this package:

- :mod:`linus.memory.hashing` — SHA-256 content-hash helpers with canonical JSON rules.
- :mod:`linus.memory.episodic` — SQLite-backed episodic store (Layer C, with Layer B
  absorbed) per DEC-0029.
- :mod:`linus.memory.audit_log` — append-only JSONL audit log per
  DEC-0030 / DEC-0031 / DEC-0032.

The dispatch-layer prefix loader (Phase 2h.5) and Worker registry tags (Phase 2h.7) are
not in this package yet — they're blocked on the DEC-0033 CoT-gap fingerprint output.
"""

from linus.memory.audit_log import AuditLog, DispatchEvent, MemoryWriteEvent
from linus.memory.episodic import EpisodicRecord, EpisodicStore
from linus.memory.hashing import content_hash, verify_hash

__all__ = [
    "AuditLog",
    "DispatchEvent",
    "EpisodicRecord",
    "EpisodicStore",
    "MemoryWriteEvent",
    "content_hash",
    "verify_hash",
]
