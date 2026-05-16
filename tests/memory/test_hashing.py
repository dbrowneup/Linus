"""Unit tests for :mod:`linus.memory.hashing`."""

from __future__ import annotations

import pytest

from linus.memory.hashing import ALGORITHM, canonical_json, content_hash, verify_hash


class TestHashingDeterministic:
    """Spec test: ``test_hashing_deterministic``."""

    def test_same_string_same_hash(self) -> None:
        """Hashing the same string twice yields the same digest."""
        assert content_hash("hello") == content_hash("hello")

    def test_same_dict_same_hash_across_key_orders(self) -> None:
        """Dict key order does not affect the hash — canonical JSON sorts keys."""
        a = {"alpha": 1, "beta": 2, "gamma": 3}
        b = {"gamma": 3, "alpha": 1, "beta": 2}
        assert content_hash(a) == content_hash(b)

    def test_nested_dict_deterministic(self) -> None:
        """Nested dicts canonicalize at every level."""
        a = {"outer": {"x": 1, "y": [3, 2, 1]}, "extra": "value"}
        b = {"extra": "value", "outer": {"y": [3, 2, 1], "x": 1}}
        assert content_hash(a) == content_hash(b)

    def test_different_payload_different_hash(self) -> None:
        """Different content produces different hashes."""
        assert content_hash("hello") != content_hash("hello world")
        assert content_hash({"a": 1}) != content_hash({"a": 2})

    def test_hash_has_algorithm_prefix(self) -> None:
        """Hash output is prefixed with the algorithm name."""
        h = content_hash("anything")
        assert h.startswith(f"{ALGORITHM}:")
        # SHA-256 hex digest is 64 chars; total = "sha256:" (7) + 64 = 71.
        assert len(h) == len(ALGORITHM) + 1 + 64

    def test_bytes_input_hashed_directly(self) -> None:
        """Bytes go in as-is; identical bytes produce identical hashes."""
        b = b"\x00\x01\x02"
        assert content_hash(b) == content_hash(b)
        # And bytes differ from the str of their repr.
        assert content_hash(b) != content_hash(str(b))

    def test_str_and_bytes_equivalent_when_utf8_encodes(self) -> None:
        """A str and its UTF-8 bytes hash to the same value."""
        s = "héllo, world"
        assert content_hash(s) == content_hash(s.encode("utf-8"))

    def test_nan_rejected(self) -> None:
        """``NaN`` is not valid canonical JSON; the call raises."""
        with pytest.raises(ValueError):
            content_hash({"x": float("nan")})

    def test_canonical_json_separators(self) -> None:
        """No extraneous whitespace between separators."""
        out = canonical_json({"a": 1, "b": [2, 3]})
        assert b" " not in out

    def test_verify_hash_roundtrip(self) -> None:
        """``verify_hash`` accepts the value just produced and rejects tampering."""
        payload = {"session_id": "s", "turn_id": 1, "content": "hi"}
        h = content_hash(payload)
        assert verify_hash(payload, h)
        payload["content"] = "tampered"
        assert not verify_hash(payload, h)
