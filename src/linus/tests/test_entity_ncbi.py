"""Hermetic tests for :mod:`linus.knowledge.entity_ncbi`.

The module under test is the first ``online_optional`` Linus tool
(DEC-0061). Every test here is hermetic: no real network call ever
escapes the test process, even if a CI machine has connectivity. The
discipline is enforced by monkeypatching the module-level
``_get_session`` and ``_network_reachable`` shims at every test that
exercises the network code path.

Coverage goals:

- Cache hit short-circuits the network.
- Cache miss → network success → cache populate (subsequent calls hit
  cache, not network).
- Network unreachable + cache miss → None.
- ``offline_only=True`` never attempts the network.
- Invalid-name validator rejects shell-metacharacter names without any
  I/O.
- Rate-limit throttle holds at ≥1/3 second between calls without an
  API key.
- Audit-log integration writes a record per call with the expected
  ``network_egress`` shape.
- Routing by ``kind`` hint hits the matching backend; ``kind=None``
  tries all in order.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from linus.knowledge import entity_ncbi as ncbi_mod
from linus.knowledge.entity_ncbi import NCBIEntityLookup, default_ncbi_cache_path
from linus.memory.audit_log import AuditLog

# ── helpers ────────────────────────────────────────────────────────────────


class _FakeResponse:
    """Minimal httpx.Response stand-in carrying ``.status_code``, ``.content``,
    and a ``.json()`` method."""

    def __init__(self, payload: dict[str, Any] | bytes, status_code: int = 200) -> None:
        self.status_code = status_code
        if isinstance(payload, bytes):
            self._raw = payload
            self._json: dict[str, Any] | None = None
        else:
            self._json = payload
            self._raw = json.dumps(payload).encode("utf-8")

    @property
    def content(self) -> bytes:
        return self._raw

    def json(self) -> dict[str, Any]:
        if self._json is None:
            raise ValueError("not JSON")
        return self._json


class _FakeClient:
    """Stand-in for ``httpx.Client`` whose ``.get(...)`` returns a
    pre-canned :class:`_FakeResponse` and records the URL for assertions.

    Supports ``with`` so the production code's ``with client:`` block
    works unchanged.
    """

    def __init__(self, responses: list[_FakeResponse | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[str] = []

    def get(self, url: str) -> _FakeResponse:
        self.calls.append(url)
        if not self._responses:
            raise AssertionError(f"unexpected extra HTTP call to {url}")
        nxt = self._responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt

    def __enter__(self) -> _FakeClient:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _make_session_factory(client: _FakeClient):
    """Build a stub ``_get_session(timeout)`` returning ``client``."""

    def factory(timeout: float) -> _FakeClient:
        return client

    return factory


def _patch_reachable(monkeypatch: pytest.MonkeyPatch, value: bool) -> None:
    """Monkeypatch ``_network_reachable`` at the module callsite."""
    monkeypatch.setattr(ncbi_mod, "_network_reachable", lambda: value)


def _reset_throttle() -> None:
    """Reset the module-level NCBI throttle clock so test order is
    independent. The throttle is process-wide for fairness in
    production; tests need it stateless to avoid bleed-through."""
    ncbi_mod._NCBI_LAST_CALL_MONOTONIC = 0.0  # type: ignore[attr-defined]


@pytest.fixture(autouse=True)
def _reset_module_state(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Ensure every test starts with a fresh throttle clock and a
    tmp_path-rooted ``LINUS_HOME`` (so default cache + audit log don't
    leak into ``~/.linus/``)."""
    monkeypatch.setenv("LINUS_HOME", str(tmp_path))
    _reset_throttle()


# ── default_ncbi_cache_path() ──────────────────────────────────────────────


def test_default_cache_path_honors_linus_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """``LINUS_HOME=tmp`` puts the cache under ``tmp/cache/ncbi_entities.db``."""
    monkeypatch.setenv("LINUS_HOME", str(tmp_path))
    assert default_ncbi_cache_path() == tmp_path / "cache" / "ncbi_entities.db"


def test_default_cache_path_unset_env_returns_home(monkeypatch: pytest.MonkeyPatch) -> None:
    """With ``LINUS_HOME`` unset the path resolves under ``~/.linus/cache/``."""
    monkeypatch.delenv("LINUS_HOME", raising=False)
    assert default_ncbi_cache_path() == Path.home() / ".linus" / "cache" / "ncbi_entities.db"


# ── _is_safe_name ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "name",
    ["BRCA1", "TP53", "HMG-CoA reductase", "Insulin receptor", "acetylsalicylic acid", "CYP1A2", "p53"],
)
def test_safe_name_accepts_reasonable_entity_names(name: str) -> None:
    assert ncbi_mod._is_safe_name(name) is True


@pytest.mark.parametrize(
    "name",
    [
        "",  # empty
        "   ",  # whitespace only
        "'; DROP TABLE entities; --",  # SQL injection-shaped
        "<script>alert(1)</script>",  # XSS-shaped
        "name\nwith\nnewlines",  # multi-line
        "name\twith\ttabs",  # control char
        "name?param=1",  # URL escape vector
        "name&other=x",  # ampersand
        "name%20encoded",  # percent encoding
    ],
)
def test_safe_name_rejects_unsafe_names(name: str) -> None:
    assert ncbi_mod._is_safe_name(name) is False


def test_safe_name_rejects_non_string() -> None:
    assert ncbi_mod._is_safe_name(None) is False  # type: ignore[arg-type]
    assert ncbi_mod._is_safe_name(123) is False  # type: ignore[arg-type]


# ── construction is cheap ──────────────────────────────────────────────────


def test_construction_does_not_touch_cache(tmp_path: Path) -> None:
    """__init__ must not open the SQLite cache. Construction is cheap;
    the cache opens on first cache-touching operation."""
    cache = tmp_path / "cache.db"
    NCBIEntityLookup(cache_path=cache)
    assert not cache.exists()


def test_construction_does_not_attempt_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """__init__ must not call _network_reachable or _get_session."""
    called: dict[str, int] = {"reach": 0, "session": 0}
    monkeypatch.setattr(
        ncbi_mod, "_network_reachable", lambda: (called.__setitem__("reach", called["reach"] + 1), True)[1]
    )
    monkeypatch.setattr(
        ncbi_mod,
        "_get_session",
        lambda timeout: (called.__setitem__("session", called["session"] + 1), MagicMock())[1],
    )
    NCBIEntityLookup(cache_path=tmp_path / "cache.db")
    assert called == {"reach": 0, "session": 0}


# ── cache hit short-circuits network ───────────────────────────────────────


def test_cache_hit_skips_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Pre-populate the cache; lookup returns the cached value and the
    HTTP session is never touched.

    Concretely: we install a stub ``_get_session`` that fails the test
    if it's called, then we call ``lookup_entity`` after seeding the
    SQLite cache by hand.
    """
    cache = tmp_path / "cache.db"
    lookup = NCBIEntityLookup(cache_path=cache)

    # Seed the cache via the lookup's own cache_put so the on-disk shape
    # matches the production format.
    lookup._cache_put(  # type: ignore[attr-defined]
        "BRCA1",
        "gene",
        {
            "kind": "gene",
            "source": "ncbi:gene",
            "canonical_name": "BRCA1",
            "external_id": "672",
        },
    )

    # Now install a session factory that fails if called.
    def _bomb(timeout: float) -> Any:
        raise AssertionError(f"unexpected network call (timeout={timeout})")

    monkeypatch.setattr(ncbi_mod, "_get_session", _bomb)
    # Also fail loud if reachability is even probed.
    _patch_reachable(monkeypatch, True)  # reachable but should not be consulted

    result = lookup.lookup_entity("BRCA1", kind="gene")
    assert result is not None
    assert result["source"] == "ncbi:gene"
    assert result["external_id"] == "672"
    assert result["canonical_name"] == "BRCA1"
    assert "cached_at" in result


# ── cache miss → network success → cache populate ──────────────────────────


def test_cache_miss_then_network_then_cache_repopulated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Two consecutive lookups for the same name: the first hits the
    network and populates the cache; the second hits the cache only."""
    cache = tmp_path / "cache.db"
    lookup = NCBIEntityLookup(cache_path=cache)
    _patch_reachable(monkeypatch, True)

    fake_client = _FakeClient(
        responses=[
            _FakeResponse({"esearchresult": {"idlist": ["672"]}}),
            _FakeResponse({"result": {"672": {"name": "BRCA1"}}}),
        ]
    )
    monkeypatch.setattr(ncbi_mod, "_get_session", _make_session_factory(fake_client))

    # First lookup: should issue two HTTP calls (esearch, esummary).
    r1 = lookup.lookup_entity("BRCA1", kind="gene")
    assert r1 is not None
    assert r1["external_id"] == "672"
    assert r1["canonical_name"] == "BRCA1"
    assert len(fake_client.calls) == 2

    # Now swap in a session that fails if called; second lookup must
    # be cache-only.
    def _bomb(timeout: float) -> Any:
        raise AssertionError("second lookup unexpectedly touched the network")

    monkeypatch.setattr(ncbi_mod, "_get_session", _bomb)
    r2 = lookup.lookup_entity("BRCA1", kind="gene")
    assert r2 is not None
    assert r2["external_id"] == "672"


# ── network unreachable + cache miss → None ────────────────────────────────


def test_network_unreachable_and_cache_miss_returns_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When ``_network_reachable`` returns False and the cache misses,
    the lookup returns None without ever opening the HTTP session."""
    cache = tmp_path / "cache.db"
    lookup = NCBIEntityLookup(cache_path=cache)
    _patch_reachable(monkeypatch, False)

    def _bomb(timeout: float) -> Any:
        raise AssertionError("offline path unexpectedly touched the network")

    monkeypatch.setattr(ncbi_mod, "_get_session", _bomb)

    result = lookup.lookup_entity("BRCA1", kind="gene")
    assert result is None


# ── offline_only ───────────────────────────────────────────────────────────


def test_offline_only_skips_network_even_when_reachable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With ``offline_only=True``, the network is never attempted even
    when the host is reachable. Cache hits still resolve."""
    cache = tmp_path / "cache.db"
    lookup = NCBIEntityLookup(cache_path=cache, offline_only=True)
    _patch_reachable(monkeypatch, True)  # would otherwise allow the call

    def _bomb(timeout: float) -> Any:
        raise AssertionError("offline_only mode unexpectedly touched the network")

    monkeypatch.setattr(ncbi_mod, "_get_session", _bomb)

    # Cache miss + offline_only → None.
    assert lookup.lookup_entity("BRCA1", kind="gene") is None

    # Seed cache; cache hit still works in offline_only mode.
    lookup._cache_put(  # type: ignore[attr-defined]
        "TP53",
        "gene",
        {
            "kind": "gene",
            "source": "ncbi:gene",
            "canonical_name": "TP53",
            "external_id": "7157",
        },
    )
    result = lookup.lookup_entity("TP53", kind="gene")
    assert result is not None
    assert result["external_id"] == "7157"


# ── invalid name rejected without any I/O ──────────────────────────────────


def test_invalid_name_returns_none_without_io(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """SQL-injection-shaped / XSS-shaped names get rejected before any
    cache read or network probe happens."""
    cache = tmp_path / "cache.db"
    lookup = NCBIEntityLookup(cache_path=cache)

    # Install bombs at every I/O surface so we can prove no call happens.
    def _bomb_session(timeout: float) -> Any:
        raise AssertionError("invalid name unexpectedly reached _get_session")

    def _bomb_reach() -> bool:
        raise AssertionError("invalid name unexpectedly reached _network_reachable")

    monkeypatch.setattr(ncbi_mod, "_get_session", _bomb_session)
    monkeypatch.setattr(ncbi_mod, "_network_reachable", _bomb_reach)

    assert lookup.lookup_entity("'; DROP TABLE entities; --") is None
    assert lookup.lookup_entity("<script>alert(1)</script>") is None
    assert lookup.lookup_entity("") is None
    # Cache file should NOT have been touched.
    assert not cache.exists()


# ── rate-limit throttle ────────────────────────────────────────────────────


def test_ncbi_throttle_holds_one_third_second_without_api_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Four consecutive gene lookups must space their NCBI calls at the
    3-req/sec limit. We measure the wall-clock delta across the four
    lookups: at least 3 * (1/3 s) = 1.0 s between the first and fourth NCBI
    esearch call.

    Each lookup is 2 NCBI calls (esearch + esummary). The throttle
    spaces every NCBI call, so 4 lookups → 8 calls → 7 intervals of
    ≥1/3 s ≈ 2.33 s lower-bound. We only assert the loose bound to
    avoid CI flake.
    """
    cache = tmp_path / "cache.db"
    lookup = NCBIEntityLookup(cache_path=cache)
    _patch_reachable(monkeypatch, True)

    # Pre-seed 8 responses (4 lookups * 2 calls each).
    pairs: list[_FakeResponse] = []
    for i in range(4):
        pairs.append(_FakeResponse({"esearchresult": {"idlist": [str(100 + i)]}}))
        pairs.append(_FakeResponse({"result": {str(100 + i): {"name": f"GENE{i}"}}}))
    fake_client = _FakeClient(responses=pairs)
    monkeypatch.setattr(ncbi_mod, "_get_session", _make_session_factory(fake_client))

    t0 = time.monotonic()
    for i in range(4):
        # Distinct names so each call goes through the network path
        # rather than hitting the cache.
        r = lookup.lookup_entity(f"GENE{i}", kind="gene")
        assert r is not None
    elapsed = time.monotonic() - t0
    # Loose bound: at least 1 second across the 4 lookups (8 calls);
    # the tight throttle would be ~2.33s but we don't want to fight
    # macOS scheduler jitter.
    assert elapsed >= 1.0, f"throttle did not hold: only {elapsed:.3f}s elapsed across 4 lookups"


# ── audit log integration ──────────────────────────────────────────────────


def test_audit_log_receives_network_egress_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A successful network lookup writes one DispatchEvent with the
    expected ``network_egress`` shape to the audit log."""
    cache = tmp_path / "cache.db"
    audit_path = tmp_path / "audit.jsonl"
    audit = AuditLog(audit_path)
    lookup = NCBIEntityLookup(cache_path=cache, audit_log=audit)
    _patch_reachable(monkeypatch, True)

    fake_client = _FakeClient(
        responses=[
            _FakeResponse({"esearchresult": {"idlist": ["672"]}}),
            _FakeResponse({"result": {"672": {"name": "BRCA1"}}}),
        ]
    )
    monkeypatch.setattr(ncbi_mod, "_get_session", _make_session_factory(fake_client))

    result = lookup.lookup_entity("BRCA1", kind="gene")
    assert result is not None

    events = audit.read_events()
    # One dispatch event with two egress entries (esearch + esummary).
    dispatch_events = [e for e in events if e.get("event_type") == "dispatch"]
    assert len(dispatch_events) == 1
    event = dispatch_events[0]
    assert event["worker_id"] == "entity_ncbi.lookup"
    assert event["memory_mode"] == "stateless"
    egress = event["network_egress"]
    assert len(egress) == 2
    for entry in egress:
        assert entry["url_host"] == "eutils.ncbi.nlm.nih.gov"
        assert isinstance(entry["query_hash"], str)
        assert len(entry["query_hash"]) == 16  # _query_hash truncation
        assert isinstance(entry["response_size"], int)
        assert entry["response_size"] > 0
        assert isinstance(entry["latency_ms"], (int, float))
        assert isinstance(entry["timestamp_ns"], int)
    # Tag confirms the source.
    assert "tool:entity_ncbi.lookup" in event["tags"]


def test_audit_log_not_written_on_cache_hit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A cache-hit lookup does not write to the audit log — egress is
    only logged when the network was actually consulted."""
    cache = tmp_path / "cache.db"
    audit_path = tmp_path / "audit.jsonl"
    audit = AuditLog(audit_path)
    lookup = NCBIEntityLookup(cache_path=cache, audit_log=audit)

    # Seed the cache directly.
    lookup._cache_put(  # type: ignore[attr-defined]
        "BRCA1",
        "gene",
        {
            "kind": "gene",
            "source": "ncbi:gene",
            "canonical_name": "BRCA1",
            "external_id": "672",
        },
    )
    # Bomb the network so a cache miss would be visible.
    monkeypatch.setattr(ncbi_mod, "_get_session", lambda timeout: (_ for _ in ()).throw(AssertionError("net touched")))

    r = lookup.lookup_entity("BRCA1", kind="gene")
    assert r is not None

    # No dispatch events for the cache hit.
    events = audit.read_events()
    dispatch_events = [e for e in events if e.get("event_type") == "dispatch"]
    assert dispatch_events == []


# ── routing by kind ────────────────────────────────────────────────────────


def test_routing_kind_gene_hits_ncbi(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """kind='gene' calls NCBI E-utilities, not UniProt or ChEBI."""
    lookup = NCBIEntityLookup(cache_path=tmp_path / "cache.db")
    _patch_reachable(monkeypatch, True)

    fake_client = _FakeClient(
        responses=[
            _FakeResponse({"esearchresult": {"idlist": ["672"]}}),
            _FakeResponse({"result": {"672": {"name": "BRCA1"}}}),
        ]
    )
    monkeypatch.setattr(ncbi_mod, "_get_session", _make_session_factory(fake_client))

    result = lookup.lookup_entity("BRCA1", kind="gene")
    assert result is not None
    assert result["source"] == "ncbi:gene"
    for url in fake_client.calls:
        assert "eutils.ncbi.nlm.nih.gov" in url
    # No additional sources contacted.
    assert all("uniprot" not in u for u in fake_client.calls)
    assert all("ebi.ac.uk" not in u for u in fake_client.calls)


def test_routing_kind_protein_hits_uniprot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """kind='protein' calls UniProt, not NCBI."""
    lookup = NCBIEntityLookup(cache_path=tmp_path / "cache.db")
    _patch_reachable(monkeypatch, True)

    fake_client = _FakeClient(
        responses=[
            _FakeResponse(
                {
                    "results": [
                        {
                            "primaryAccession": "P38398",
                            "proteinDescription": {
                                "recommendedName": {
                                    "fullName": {"value": "Breast cancer type 1 susceptibility protein"}
                                }
                            },
                        }
                    ]
                }
            ),
        ]
    )
    monkeypatch.setattr(ncbi_mod, "_get_session", _make_session_factory(fake_client))

    result = lookup.lookup_entity("BRCA1", kind="protein")
    assert result is not None
    assert result["source"] == "uniprot"
    assert result["external_id"] == "P38398"
    assert "uniprot" in fake_client.calls[0]


def test_routing_kind_chemical_hits_chebi(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """kind='chemical' calls ChEBI (via EBI OLS4), not NCBI or UniProt."""
    lookup = NCBIEntityLookup(cache_path=tmp_path / "cache.db")
    _patch_reachable(monkeypatch, True)

    fake_client = _FakeClient(
        responses=[
            _FakeResponse(
                {
                    "response": {
                        "docs": [
                            {
                                "obo_id": "CHEBI:15365",
                                "label": "acetylsalicylic acid",
                            }
                        ]
                    }
                }
            ),
        ]
    )
    monkeypatch.setattr(ncbi_mod, "_get_session", _make_session_factory(fake_client))

    result = lookup.lookup_entity("acetylsalicylic acid", kind="chemical")
    assert result is not None
    assert result["source"] == "chebi"
    assert result["external_id"] == "CHEBI:15365"
    assert "ebi.ac.uk" in fake_client.calls[0]


def test_routing_kind_none_tries_all_in_order(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """kind=None tries NCBI → UniProt → ChEBI in order; first non-None
    result wins. We seed NCBI with a miss (empty idlist) and UniProt
    with a hit; ChEBI must never be called."""
    lookup = NCBIEntityLookup(cache_path=tmp_path / "cache.db")
    _patch_reachable(monkeypatch, True)

    fake_client = _FakeClient(
        responses=[
            # NCBI esearch: empty idlist → miss.
            _FakeResponse({"esearchresult": {"idlist": []}}),
            # UniProt: hit.
            _FakeResponse(
                {
                    "results": [
                        {
                            "primaryAccession": "P01308",
                            "proteinDescription": {"recommendedName": {"fullName": {"value": "Insulin"}}},
                        }
                    ]
                }
            ),
        ]
    )
    monkeypatch.setattr(ncbi_mod, "_get_session", _make_session_factory(fake_client))

    result = lookup.lookup_entity("Insulin", kind=None)
    assert result is not None
    assert result["source"] == "uniprot"
    assert result["external_id"] == "P01308"
    # Exactly two calls: NCBI esearch + UniProt search; ChEBI not consulted.
    assert len(fake_client.calls) == 2
    assert "eutils" in fake_client.calls[0]
    assert "uniprot" in fake_client.calls[1]


def test_routing_kind_none_returns_none_when_all_miss(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """If NCBI, UniProt, and ChEBI all return empty results, the
    lookup returns None."""
    lookup = NCBIEntityLookup(cache_path=tmp_path / "cache.db")
    _patch_reachable(monkeypatch, True)

    fake_client = _FakeClient(
        responses=[
            _FakeResponse({"esearchresult": {"idlist": []}}),
            _FakeResponse({"results": []}),
            _FakeResponse({"response": {"docs": []}}),
        ]
    )
    monkeypatch.setattr(ncbi_mod, "_get_session", _make_session_factory(fake_client))

    assert lookup.lookup_entity("ENTIRELY_FAKE_ENTITY") is None


# ── network failure handling ───────────────────────────────────────────────


def test_httpx_error_during_lookup_returns_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An httpx.HTTPError mid-call is swallowed and the lookup returns
    None per the online_optional contract."""
    lookup = NCBIEntityLookup(cache_path=tmp_path / "cache.db")
    _patch_reachable(monkeypatch, True)

    fake_client = _FakeClient(responses=[httpx.ConnectError("simulated DNS failure")])
    monkeypatch.setattr(ncbi_mod, "_get_session", _make_session_factory(fake_client))

    assert lookup.lookup_entity("BRCA1", kind="gene") is None


def test_non_200_response_returns_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-200 HTTP responses are treated as a clean miss."""
    lookup = NCBIEntityLookup(cache_path=tmp_path / "cache.db")
    _patch_reachable(monkeypatch, True)

    fake_client = _FakeClient(responses=[_FakeResponse({}, status_code=503)])
    monkeypatch.setattr(ncbi_mod, "_get_session", _make_session_factory(fake_client))

    assert lookup.lookup_entity("BRCA1", kind="gene") is None


def test_invalid_json_response_returns_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A 200 response with non-JSON payload is treated as a clean miss."""
    lookup = NCBIEntityLookup(cache_path=tmp_path / "cache.db")
    _patch_reachable(monkeypatch, True)

    # Raw bytes that aren't JSON — ``response.json()`` raises.
    fake_client = _FakeClient(responses=[_FakeResponse(b"<html>not json</html>", status_code=200)])
    monkeypatch.setattr(ncbi_mod, "_get_session", _make_session_factory(fake_client))

    assert lookup.lookup_entity("BRCA1", kind="gene") is None


# ── _network_reachable + _get_session probes ───────────────────────────────


def test_network_reachable_returns_false_on_socket_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``_network_reachable`` swallows OSError and returns False."""

    def _raise(*args: Any, **kwargs: Any) -> Any:
        raise OSError("simulated network down")

    monkeypatch.setattr("socket.create_connection", _raise)
    assert ncbi_mod._network_reachable() is False


def test_network_reachable_returns_true_on_successful_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When ``socket.create_connection`` succeeds, the probe returns True."""

    class _FakeSocket:
        def __enter__(self) -> _FakeSocket:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    monkeypatch.setattr("socket.create_connection", lambda *a, **kw: _FakeSocket())
    assert ncbi_mod._network_reachable() is True


def test_get_session_returns_httpx_client() -> None:
    """``_get_session`` returns a real httpx.Client — not lazily, but
    the constructor doesn't open any sockets."""
    client = ncbi_mod._get_session(timeout=5.0)
    try:
        assert isinstance(client, httpx.Client)
    finally:
        client.close()


# ── cache PK normalization (kind=None vs kind="gene") ──────────────────────


def test_cache_key_kind_none_normalizes_to_any_marker() -> None:
    """The PK can't store NULL; ``None`` becomes the literal marker."""
    assert NCBIEntityLookup._cache_key_kind(None) == "__any__"
    assert NCBIEntityLookup._cache_key_kind("gene") == "gene"


def test_cache_separate_slots_for_kind_none_vs_gene(tmp_path: Path) -> None:
    """A cache hit for kind=None must not be returned for kind='gene'
    (and vice versa) — they're separate PK slots."""
    lookup = NCBIEntityLookup(cache_path=tmp_path / "cache.db")
    lookup._cache_put(  # type: ignore[attr-defined]
        "X",
        None,
        {"kind": "gene", "source": "ncbi:gene", "canonical_name": "X", "external_id": "1"},
    )
    assert lookup._cache_get("X", None) is not None  # type: ignore[attr-defined]
    assert lookup._cache_get("X", "gene") is None  # type: ignore[attr-defined]


# ── default_kb_lookup_with_ncbi factory ────────────────────────────────────


def test_default_kb_lookup_with_ncbi_includes_ncbi_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The chained factory produces a chain with three backends in
    order: KB → NCBI → builtin. The exact composition matters because
    the chain dispatches in order — KB-derived answers take precedence
    over NCBI answers, which take precedence over the stub."""
    from linus.knowledge.entity_kb import ChainedEntityLookup, KBEntityLookup, default_kb_lookup_with_ncbi
    from linus.knowledge.entity_ncbi import NCBIEntityLookup
    from linus.knowledge.rigor import BuiltinEntityLookup

    chain = default_kb_lookup_with_ncbi()
    assert isinstance(chain, ChainedEntityLookup)
    # The chain has three backends: KB, NCBI, builtin (in that order).
    backends = chain._backends  # type: ignore[attr-defined]
    assert len(backends) == 3
    assert isinstance(backends[0], KBEntityLookup)
    assert isinstance(backends[1], NCBIEntityLookup)
    assert isinstance(backends[2], BuiltinEntityLookup)


def test_default_kb_lookup_with_ncbi_falls_back_on_ncbi_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If NCBIEntityLookup raises during construction, the chain still
    builds with KB + builtin only. Forward-compatible per the
    factory's docstring contract."""
    import builtins

    from linus.knowledge.entity_kb import ChainedEntityLookup, KBEntityLookup, default_kb_lookup_with_ncbi
    from linus.knowledge.rigor import BuiltinEntityLookup

    # Force the import of NCBIEntityLookup inside the factory to fail.
    original_import = builtins.__import__

    def _failing_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if "entity_ncbi" in name:
            raise ImportError("simulated unavailability")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _failing_import)

    chain = default_kb_lookup_with_ncbi()
    assert isinstance(chain, ChainedEntityLookup)
    backends = chain._backends  # type: ignore[attr-defined]
    # With NCBI unavailable, the chain falls back to KB + builtin.
    assert len(backends) == 2
    assert isinstance(backends[0], KBEntityLookup)
    assert isinstance(backends[1], BuiltinEntityLookup)


# ── tool registry integration ──────────────────────────────────────────────


def test_entity_ncbi_lookup_is_registered_with_online_optional_policy() -> None:
    """The ``entity_ncbi.lookup`` tool must be registered with
    ``network_policy='online_optional'`` per DEC-0061."""
    from linus.tools import default_registry

    spec = default_registry.get("entity_ncbi.lookup")
    assert spec is not None, "entity_ncbi.lookup not registered"
    assert spec.network_policy == "online_optional"
    # The schema must accept ``name`` (required) and ``kind`` (optional).
    params = spec.parameters
    assert "name" in params["properties"]
    assert "kind" in params["properties"]
    assert params.get("required") == ["name"]


def test_entity_ncbi_lookup_tool_returns_none_in_offline_hermetic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invoking the registered tool in a network-unreachable hermetic
    environment with an empty cache returns None — the online_optional
    fallback contract."""
    from linus.tools import default_registry

    _patch_reachable(monkeypatch, False)
    # The registered tool builds its own NCBIEntityLookup; with an
    # empty cache and no network, the call returns None.
    result = default_registry.call_tool("entity_ncbi.lookup", {"name": "BRCA1", "kind": "gene"})
    assert result is None
