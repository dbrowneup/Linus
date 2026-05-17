"""Content-hashing helpers for the Linus episodic store and audit log.

Per the memory architecture spec (`docs/specs/memory-architecture.md`) and DEC-0029,
every record written to the episodic store carries a content hash that serves three
purposes simultaneously:

1. **Addressability** — records can be looked up by hash without scanning by row id.
2. **Disambiguation** — two records with the same hash are the same record.
3. **Integrity** — the SHA chain (record hash + parent-pointer) is the cryptographic
   spine that lets the audit log validate the episodic store after the fact.

## Algorithm choice (v0)

DEC-0029 names **SHA-256** as the v0 hash. The Item 4 spec calls out Keccak-256 as a
preference if "readily available"; Keccak-256 is **not** in the linus conda env (no
``pycryptodome``, no ``eth-hash``, no ``pysha3``), and adding a crypto dep purely for
the v0 substrate scaffolding would violate The Algorithm — Keccak's collision-resistance
profile is not load-bearing for this use case, and SHA-256 is the explicit DEC-0029
commitment. SHA-256 is provided by Python's stdlib ``hashlib`` and ships native on every
platform Linus runs on.

If Keccak-256 graduates from "preferred" to "required" (e.g., for interop with an
external content-addressable store that uses Keccak), the upgrade path is:

1. Add ``pycryptodome`` to ``environment.yml``.
2. Switch :func:`content_hash` to dispatch on ``algorithm=`` keyword argument.
3. Migrate existing records (one-time pass: re-hash payloads, update content_hash columns,
   leave the SHA-256 column as a legacy index).

This module deliberately keeps the public surface algorithm-agnostic (the return value
is a hex digest string with an algorithm prefix) so callers don't need to change.

## Canonical JSON serialization

For dict/list payloads, the hash must be deterministic across processes, platforms, and
Python versions. JSON serialization is canonicalized via :func:`canonical_json` per the
following rules:

- ``sort_keys=True`` — dict key ordering is deterministic.
- ``separators=(",", ":")`` — no extraneous whitespace.
- ``ensure_ascii=False`` — Unicode passes through untransformed, encoded UTF-8 below.
- ``allow_nan=False`` — ``NaN``/``Infinity`` are not valid JSON; raise rather than
  produce an unparseable record.
- The final bytes are UTF-8 encoded.

Hash inputs that are already :class:`bytes` are hashed as-is. Inputs that are :class:`str`
are UTF-8 encoded. Everything else routes through :func:`canonical_json`.

The returned digest is prefixed with the algorithm name (``"sha256:<hex>"``) so callers
and future migrations can tell different hash generations apart at a glance.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

__all__ = [
    "ALGORITHM",
    "canonical_json",
    "content_hash",
    "verify_hash",
]

#: The hash algorithm name embedded in every digest returned by :func:`content_hash`.
#: Kept as a module constant so audit-log readers can detect algorithm-version drift.
ALGORITHM = "sha256"


def canonical_json(payload: Any) -> bytes:
    """Serialize ``payload`` to canonical JSON bytes for hashing.

    See module docstring for the canonicalization rules. The output is the exact byte
    sequence that gets fed into the hash function for any non-bytes, non-str input.

    Args:
        payload: Any JSON-serializable Python value.

    Returns:
        UTF-8 encoded canonical-JSON bytes.

    Raises:
        ValueError: If ``payload`` contains ``NaN`` or ``Infinity``.
        TypeError: If ``payload`` contains non-JSON-serializable types.
    """
    text = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return text.encode("utf-8")


def content_hash(payload: Any) -> str:
    """Compute the canonical content hash of ``payload``.

    The return value is a string of the form ``"{algorithm}:{hex_digest}"`` — for
    example ``"sha256:abc123..."``. The algorithm prefix is part of the durable value;
    callers should not strip it.

    Args:
        payload: Bytes, str, or any JSON-serializable Python value. Bytes are hashed
            as-is; strings are UTF-8 encoded; everything else is serialized through
            :func:`canonical_json` first.

    Returns:
        Algorithm-prefixed hex digest (``"sha256:<64 hex chars>"`` for SHA-256).
    """
    if isinstance(payload, bytes):
        data = payload
    elif isinstance(payload, str):
        data = payload.encode("utf-8")
    else:
        data = canonical_json(payload)

    digest = hashlib.sha256(data).hexdigest()
    return f"{ALGORITHM}:{digest}"


def verify_hash(payload: Any, expected: str) -> bool:
    """Return whether ``payload`` re-hashes to ``expected``.

    Used by the audit log's after-the-fact integrity check: given a record from the
    episodic store and its claimed hash, verify they still agree.

    Args:
        payload: The same shape that was originally hashed.
        expected: An algorithm-prefixed hex digest (the output of a prior
            :func:`content_hash` call).

    Returns:
        ``True`` iff the recomputed hash matches ``expected`` byte-for-byte.
    """
    return content_hash(payload) == expected
