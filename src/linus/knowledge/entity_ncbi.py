"""Online-optional entity lookup against NCBI Gene, UniProt, and ChEBI.

This module is the first concrete user of the DEC-0061 network-policy
framework: the first Linus tool with ``network_policy="online_optional"``.
It complements :class:`linus.knowledge.entity_kb.KBEntityLookup` (which
resolves entities against Dan's actual KG snapshot) and
:class:`linus.knowledge.rigor.BuiltinEntityLookup` (the hand-seeded stub)
by adding a canonical-reference-DB resolution path that the rigor gate's
:class:`~linus.knowledge.entity_kb.ChainedEntityLookup` consults between
the KB and the builtin.

Backends contacted
------------------

- **NCBI E-utilities** (``eutils.ncbi.nlm.nih.gov``) — gene symbols. Free,
  no API key required; with an NCBI API key the per-host rate-limit lifts
  from 3 to 10 requests/second. The throttle is enforced client-side per
  instance so the module is a good citizen even when called in a tight
  loop.
- **UniProt** (``rest.uniprot.org``) — protein names. Public, key-less.
- **ChEBI** (``www.ebi.ac.uk``) — chemicals. Public, key-less REST endpoint.

Privacy posture
---------------

Per DEC-0061, this tool is an exfiltration surface. The discipline:

1. **Only entity NAMES go over the wire.** No claim content, no paper
   ids from Dan's corpus, no rationale text, no context beyond the
   entity name being resolved. ``lookup_entity(name, kind)`` is the
   only producer of external HTTP calls and it sends ``name`` only.
2. **Names are validated before they leave the box.** A name containing
   anything other than ``[A-Za-z0-9 ._-]`` is rejected upfront —
   ``return None`` with no network call. This guards against the
   trivial "exfiltrate by encoding into the entity name" path and
   keeps the request-URL surface mechanical.
3. **Every call is audited.** A successful network call appends one
   ``DispatchEvent`` to the audit log with a single ``network_egress``
   entry shape per DEC-0061 (host, query-hash, response size, latency,
   nanosecond timestamp). The audit-log path is overridable via
   ``LINUS_HOME`` (the same env var the rest of Linus respects) so
   hermetic tests can isolate.

Offline fallback
----------------

When the network is unreachable AND the local SQLite cache misses, the
lookup returns ``None`` — the caller's chain falls through to the next
backend (the builtin stub). When ``offline_only=True`` the module never
attempts the network even if it would succeed; cache misses produce
``None`` immediately. Both paths preserve the "private-by-default"
character of the local-first stance while honoring the opt-in network
path for users who want richer resolution.

Cache shape
-----------

A single SQLite table at ``~/.linus/cache/ncbi_entities.db``::

    entities(
        name TEXT,
        kind TEXT,
        source TEXT,
        canonical_name TEXT,
        external_id TEXT,
        payload JSON,
        cached_at INTEGER,
        PRIMARY KEY (name, kind)
    )

WAL mode is enabled for crash-safety and to match the rest of Linus's
SQLite stores (``sessions.db``, ``episodic.db``). The cache is keyed by
``(name, kind)`` so a same-name lookup with a different ``kind`` hint
can resolve against a different reference DB.

See also
--------

- :doc:`DEC-0061 </adr/0061-network-policy-framework.md>` — the framework
  this module is the first instance of.
- :doc:`DEC-0059 </adr/0059-grounding-gate-output-surface.md>` — the
  rigor gate this module's lookup feeds.
- :mod:`linus.knowledge.entity_kb` — the KB-derived sibling backend that
  this module slots alongside in the chain.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import socket
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

__all__ = [
    "NCBIEntityLookup",
    "default_ncbi_cache_path",
]


# ── Constants ──────────────────────────────────────────────────────────────

#: Default cache location. ``~/.linus/cache/ncbi_entities.db`` mirrors the
#: ``~/.linus/`` convention used by ``audit.jsonl``, ``sessions.db``, and
#: ``episodic.db``. Overridable via ``LINUS_HOME``.
DEFAULT_CACHE_REL = Path("cache") / "ncbi_entities.db"

#: Endpoints. Kept at module scope so a test can monkeypatch them if a
#: hostname changes upstream; in practice they're stable.
_NCBI_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_NCBI_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
_UNIPROT_SEARCH_URL = "https://rest.uniprot.org/uniprotkb/search"
_CHEBI_SEARCH_URL = "https://www.ebi.ac.uk/ols4/api/search"  # OLS4 ChEBI search; key-less, stable JSON

#: Validate names BEFORE sending them upstream. The regex covers
#: gene-symbol shapes (``BRCA1``, ``HMG-CoA reductase``, ``CYP1A2``),
#: protein name shapes (``Insulin receptor``), and chemical name shapes
#: (``acetylsalicylic acid``, ``2,3-dimethylbenzene``). Anything with
#: shell metacharacters, angle brackets, semicolons, or other injection
#: vectors fails the validator and never leaves the box.
_NAME_VALIDATOR = re.compile(r"^[A-Za-z0-9 ._\-,()/+]+$")

#: Rate-limit floors per the NCBI E-utilities policy. Without an API key
#: NCBI allows 3 req/sec; with one, 10/sec. We use the most-restrictive
#: applicable value as the floor between consecutive network calls.
_NCBI_RATE_LIMIT_NO_KEY_SECONDS = 1.0 / 3.0  # 3 req/sec → 333 ms
_NCBI_RATE_LIMIT_WITH_KEY_SECONDS = 1.0 / 10.0  # 10 req/sec → 100 ms

#: Probe target for the reachability check — the well-known 1.1.1.1 DNS
#: endpoint, matched to ``server._check_network_reachable`` for
#: consistency. ``socket.create_connection`` with a short timeout is the
#: only stdlib-clean way to bound a DNS probe (a bare ``gethostbyname``
#: blocks for the OS resolver's timeout regardless of any Python-level
#: argument).
_REACHABILITY_PROBE_HOST = "1.1.1.1"
_REACHABILITY_TIMEOUT_S = 1.0


# ── Helpers ────────────────────────────────────────────────────────────────


def default_ncbi_cache_path() -> Path:
    """Resolve the default cache path, honoring ``LINUS_HOME`` if set.

    Mirrors :func:`linus.memory.audit_log.default_audit_path` so the
    hermetic-test escape hatch (``LINUS_HOME=tmp_path``) puts every
    Linus on-disk artifact under a single isolated root.
    """
    if env_root := os.environ.get("LINUS_HOME"):
        return Path(env_root) / DEFAULT_CACHE_REL
    return Path.home() / ".linus" / DEFAULT_CACHE_REL


def _is_safe_name(name: str) -> bool:
    """Return True iff ``name`` matches the safe-character allowlist.

    The regex is the privacy gate — anything that doesn't match never
    becomes an HTTP request URL. See module docstring "Privacy posture"
    item 2 for the rationale.
    """
    if not name or not isinstance(name, str):
        return False
    # A bare space-only string would match the regex but carries no
    # information; explicitly reject.
    if not name.strip():
        return False
    return bool(_NAME_VALIDATOR.fullmatch(name))


def _network_reachable() -> bool:
    """Quick reachability probe; monkeypatchable for hermetic tests.

    The probe target and timeout match
    :func:`linus.server._check_network_reachable` so /healthz and this
    module agree on what "reachable" means. The function returns
    ``False`` on any socket-layer failure (DNS, timeout, firewall block);
    no diagnostic surface is exposed because /healthz's reachability
    classification is the only consumer that cares about the reason.
    """
    try:
        with socket.create_connection(
            (_REACHABILITY_PROBE_HOST, 53),
            timeout=_REACHABILITY_TIMEOUT_S,
        ):
            return True
    except OSError:
        return False


def _get_session(timeout: float) -> httpx.Client:
    """Return a fresh ``httpx.Client`` with the given timeout.

    Module-level shim so tests can monkeypatch the HTTP layer at one
    call-site:

    ::

        monkeypatch.setattr(
            "linus.knowledge.entity_ncbi._get_session",
            lambda timeout: fake_client,
        )

    A new client per call keeps the hermetic-test surface simple — no
    shared global state to reset between tests. The cost in a real
    deployment is one TCP connect per lookup, which is dominated by the
    intra-call rate-limit throttle anyway (≥100 ms between successive
    NCBI calls).
    """
    return httpx.Client(timeout=timeout)


def _query_hash(*parts: str) -> str:
    """Return the short content hash used in the ``network_egress`` entry.

    Per DEC-0061 the audit log records ``query_hash``, not the query
    text — so the host knows a lookup happened but not what was looked
    up. Joining the parts with ``\\x00`` (a character that cannot appear
    in a valid URL or entity name) keeps multi-arg hashes unambiguous.
    """
    joined = "\x00".join(parts).encode("utf-8")
    return hashlib.sha256(joined).hexdigest()[:16]


# ── Module-level lock for cross-instance throttling fairness ───────────────

# A single per-process lock guards the inter-call delay calculation. The
# throttle is per-host in spirit (NCBI's rate limit applies to a host's
# IP, not to a Python process), so a process that spawns N
# NCBIEntityLookup instances would otherwise exceed the rate limit by a
# factor of N. The class-level last-call-monotonic timestamp is shared
# under this lock to enforce a single per-process budget.
_NCBI_THROTTLE_LOCK = threading.Lock()
_NCBI_LAST_CALL_MONOTONIC: float = 0.0


def _throttle_for_ncbi(min_interval_s: float) -> None:
    """Sleep just long enough to honor the per-process NCBI rate limit.

    The throttle is global (class-level) rather than per-instance because
    NCBI's rate limit is per requesting host, not per Python object. Two
    NCBIEntityLookup instances in the same process must cooperate.
    """
    global _NCBI_LAST_CALL_MONOTONIC
    with _NCBI_THROTTLE_LOCK:
        now = time.monotonic()
        elapsed = now - _NCBI_LAST_CALL_MONOTONIC
        if elapsed < min_interval_s:
            time.sleep(min_interval_s - elapsed)
        _NCBI_LAST_CALL_MONOTONIC = time.monotonic()


# ── NCBIEntityLookup ───────────────────────────────────────────────────────


class NCBIEntityLookup:
    """Online entity lookup against NCBI Gene, UniProt, and ChEBI.

    ``network_policy``: ``online_optional`` per DEC-0061. The lookup
    prefers the network when available, caches results in a local
    SQLite cache, and degrades cleanly to a ``None`` return when both
    cache and network miss.

    Routing
    -------

    Given ``lookup_entity(name, kind=None)``:

    1. **Cache check.** Look up ``(name, kind)`` in the SQLite cache.
       Cache hit returns immediately; no network.
    2. **Reachability check.** If ``offline_only=True`` or
       :func:`_network_reachable` returns False, return ``None``.
    3. **Network resolution.** Route by ``kind`` hint:
       * ``"gene"`` → NCBI E-utilities
       * ``"protein"`` → UniProt
       * ``"chemical"`` → ChEBI (via the EBI OLS4 API)
       * ``None`` → try NCBI → UniProt → ChEBI in order; first non-None
         result wins.
    4. **Cache populate.** Successful resolutions are written to the
       cache so the next call short-circuits step 2 onward.
    5. **Audit log.** A successful network call appends one
       :class:`~linus.memory.audit_log.DispatchEvent` with one
       ``network_egress`` entry per DEC-0061.

    Parameters
    ----------

    cache_path
        Override the SQLite cache location. Defaults to
        ``~/.linus/cache/ncbi_entities.db``.
    network_timeout
        Per-request timeout in seconds. Defaults to 5.0.
    api_key
        Optional NCBI API key — bumps the NCBI rate limit from 3 to 10
        requests/second. Passed as the ``api_key`` query param on
        E-utilities calls only; UniProt and ChEBI don't accept it.
    offline_only
        If True, never attempt network calls even when reachable. Cache
        hits still resolve; cache misses return ``None``. Useful for
        deterministic test mode and for users who want the cache as a
        "remember what we resolved before" surface without the egress.
    audit_log
        Optional :class:`~linus.memory.audit_log.AuditLog` to write
        network_egress records to. ``None`` (default) silently skips
        audit-log writes — appropriate for unit tests; production
        registrations pass a real :class:`AuditLog`.
    """

    def __init__(
        self,
        cache_path: Path | None = None,
        network_timeout: float = 5.0,
        api_key: str | None = None,
        offline_only: bool = False,
        audit_log: Any | None = None,
    ) -> None:
        self._cache_path: Path = cache_path if cache_path is not None else default_ncbi_cache_path()
        self._network_timeout: float = float(network_timeout)
        self._api_key: str | None = api_key
        self._offline_only: bool = bool(offline_only)
        self._audit_log: Any | None = audit_log
        # Lazily opened on first cache touch so construction stays cheap
        # (and so a misconfigured cache_path doesn't fail at import time).
        self._conn: sqlite3.Connection | None = None
        self._conn_lock = threading.Lock()

    # ── cache ─────────────────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        """Open the SQLite cache lazily; idempotent across calls.

        Matches the pattern in :class:`linus.memory.sessions.SessionStore`:
        WAL mode, ``check_same_thread=False`` for the FastAPI worker
        threadpool, idempotent ``CREATE TABLE IF NOT EXISTS``. The
        connection is held on the instance and closed in :meth:`close`.
        """
        if self._conn is not None:
            return self._conn
        with self._conn_lock:
            if self._conn is not None:
                return self._conn
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self._cache_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS entities (
                    name TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    source TEXT NOT NULL,
                    canonical_name TEXT,
                    external_id TEXT,
                    payload TEXT,
                    cached_at INTEGER NOT NULL,
                    PRIMARY KEY (name, kind)
                )
                """
            )
            conn.commit()
            self._conn = conn
            return conn

    def close(self) -> None:
        """Close the cache connection. Idempotent."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> NCBIEntityLookup:
        self._connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    @staticmethod
    def _cache_key_kind(kind: str | None) -> str:
        """Normalize the cache-key ``kind`` — the PK can't store NULL.

        ``None`` becomes the literal ``"__any__"`` so a kind-agnostic
        lookup has a stable cache slot. Callers pass ``kind`` or
        ``None``; the on-disk PK is always a real string.
        """
        return kind if kind else "__any__"

    def _cache_get(self, name: str, kind: str | None) -> dict[str, Any] | None:
        """Look up the cache for ``(name, kind)``; return None on miss."""
        conn = self._connect()
        row = conn.execute(
            "SELECT source, canonical_name, external_id, payload, cached_at FROM entities WHERE name = ? AND kind = ?",
            (name, self._cache_key_kind(kind)),
        ).fetchone()
        if row is None:
            return None
        payload = json.loads(row["payload"]) if row["payload"] else {}
        # Merge stored core fields and the JSON payload into a single
        # response dict matching the contract documented in
        # :meth:`lookup_entity`.
        return {
            "kind": kind if kind else payload.get("kind", "entity"),
            "source": row["source"],
            "canonical_name": row["canonical_name"],
            "external_id": row["external_id"],
            "cached_at": int(row["cached_at"]),
            **{k: v for k, v in payload.items() if k not in {"kind", "source", "canonical_name", "external_id"}},
        }

    def _cache_put(self, name: str, kind: str | None, value: dict[str, Any]) -> None:
        """Upsert a resolved entity into the cache."""
        conn = self._connect()
        cached_at = time.time_ns()
        payload = {k: v for k, v in value.items() if k not in {"cached_at"}}
        with conn:
            conn.execute(
                """
                INSERT INTO entities (name, kind, source, canonical_name, external_id, payload, cached_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name, kind) DO UPDATE SET
                    source = excluded.source,
                    canonical_name = excluded.canonical_name,
                    external_id = excluded.external_id,
                    payload = excluded.payload,
                    cached_at = excluded.cached_at
                """,
                (
                    name,
                    self._cache_key_kind(kind),
                    str(value.get("source", "")),
                    value.get("canonical_name"),
                    value.get("external_id"),
                    json.dumps(payload, sort_keys=True),
                    cached_at,
                ),
            )

    # ── HTTP backends ─────────────────────────────────────────────────────

    def _ncbi_gene_lookup(self, name: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        """Resolve a gene symbol against NCBI E-utilities.

        Returns ``(result_or_None, egress_records)`` so the caller can
        merge egress records into a single dispatch event. Two HTTP
        calls happen per lookup (esearch → esummary); each gets its own
        egress entry per DEC-0061's "fact of the call" granularity.
        """
        egress: list[dict[str, Any]] = []
        _throttle_for_ncbi(self._ncbi_min_interval())
        # Step 1: esearch.fcgi to resolve symbol → gene_id.
        params: dict[str, str] = {
            "db": "gene",
            "term": f"{name}[Symbol]",
            "retmode": "json",
            "retmax": "1",
        }
        if self._api_key:
            params["api_key"] = self._api_key
        esearch_url = _NCBI_ESEARCH_URL + "?" + urlencode(params)
        t0 = time.monotonic()
        with _get_session(self._network_timeout) as client:
            resp = client.get(esearch_url)
        latency_ms = (time.monotonic() - t0) * 1000.0
        egress.append(
            {
                "url_host": "eutils.ncbi.nlm.nih.gov",
                "query_hash": _query_hash("ncbi:esearch", name),
                "response_size": len(resp.content),
                "latency_ms": latency_ms,
                "timestamp_ns": time.time_ns(),
            }
        )
        if resp.status_code != 200:
            return None, egress
        try:
            data = resp.json()
        except (json.JSONDecodeError, ValueError):
            return None, egress
        ids = ((data.get("esearchresult") or {}).get("idlist")) or []
        if not ids:
            return None, egress
        gene_id = str(ids[0])

        # Step 2: esummary.fcgi for the canonical symbol + description.
        _throttle_for_ncbi(self._ncbi_min_interval())
        summary_params: dict[str, str] = {
            "db": "gene",
            "id": gene_id,
            "retmode": "json",
        }
        if self._api_key:
            summary_params["api_key"] = self._api_key
        esummary_url = _NCBI_ESUMMARY_URL + "?" + urlencode(summary_params)
        t1 = time.monotonic()
        with _get_session(self._network_timeout) as client:
            sresp = client.get(esummary_url)
        latency2_ms = (time.monotonic() - t1) * 1000.0
        egress.append(
            {
                "url_host": "eutils.ncbi.nlm.nih.gov",
                "query_hash": _query_hash("ncbi:esummary", gene_id),
                "response_size": len(sresp.content),
                "latency_ms": latency2_ms,
                "timestamp_ns": time.time_ns(),
            }
        )
        canonical_name = name
        if sresp.status_code == 200:
            try:
                sdata = sresp.json()
            except (json.JSONDecodeError, ValueError):
                sdata = {}
            entry = (sdata.get("result") or {}).get(gene_id) or {}
            canonical_name = str(entry.get("name") or entry.get("nomenclaturesymbol") or name)
        return (
            {
                "kind": "gene",
                "source": "ncbi:gene",
                "canonical_name": canonical_name,
                "external_id": gene_id,
            },
            egress,
        )

    def _uniprot_lookup(self, name: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        """Resolve a protein name against UniProt."""
        egress: list[dict[str, Any]] = []
        params: dict[str, str] = {
            "query": name,
            "format": "json",
            "fields": "accession,protein_name",
            "size": "1",
        }
        url = _UNIPROT_SEARCH_URL + "?" + urlencode(params)
        t0 = time.monotonic()
        with _get_session(self._network_timeout) as client:
            resp = client.get(url)
        latency_ms = (time.monotonic() - t0) * 1000.0
        egress.append(
            {
                "url_host": "rest.uniprot.org",
                "query_hash": _query_hash("uniprot:search", name),
                "response_size": len(resp.content),
                "latency_ms": latency_ms,
                "timestamp_ns": time.time_ns(),
            }
        )
        if resp.status_code != 200:
            return None, egress
        try:
            data = resp.json()
        except (json.JSONDecodeError, ValueError):
            return None, egress
        results = data.get("results") or []
        if not results:
            return None, egress
        first = results[0]
        accession = str(first.get("primaryAccession") or "")
        # ``proteinDescription.recommendedName.fullName.value`` is the
        # UniProt canonical name; we degrade to ``name`` if any layer is
        # absent to keep the contract single-shape.
        prot_desc = (first.get("proteinDescription") or {}).get("recommendedName") or {}
        full_name = ((prot_desc.get("fullName") or {}).get("value")) or name
        if not accession:
            return None, egress
        return (
            {
                "kind": "protein",
                "source": "uniprot",
                "canonical_name": str(full_name),
                "external_id": accession,
            },
            egress,
        )

    def _chebi_lookup(self, name: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        """Resolve a chemical name against ChEBI (via the EBI OLS4 search API).

        OLS4 (https://www.ebi.ac.uk/ols4/api/search) is the EBI's
        unified ontology lookup API; it covers ChEBI and returns a
        stable JSON shape we can parse without a dedicated ChEBI client.
        """
        egress: list[dict[str, Any]] = []
        params: dict[str, str] = {
            "q": name,
            "ontology": "chebi",
            "rows": "1",
            "format": "json",
        }
        url = _CHEBI_SEARCH_URL + "?" + urlencode(params)
        t0 = time.monotonic()
        with _get_session(self._network_timeout) as client:
            resp = client.get(url)
        latency_ms = (time.monotonic() - t0) * 1000.0
        egress.append(
            {
                "url_host": "www.ebi.ac.uk",
                "query_hash": _query_hash("chebi:search", name),
                "response_size": len(resp.content),
                "latency_ms": latency_ms,
                "timestamp_ns": time.time_ns(),
            }
        )
        if resp.status_code != 200:
            return None, egress
        try:
            data = resp.json()
        except (json.JSONDecodeError, ValueError):
            return None, egress
        docs = ((data.get("response") or {}).get("docs")) or []
        if not docs:
            return None, egress
        first = docs[0]
        external_id = str(first.get("obo_id") or first.get("short_form") or "")
        canonical_name = str(first.get("label") or name)
        if not external_id:
            return None, egress
        return (
            {
                "kind": "chemical",
                "source": "chebi",
                "canonical_name": canonical_name,
                "external_id": external_id,
            },
            egress,
        )

    def _ncbi_min_interval(self) -> float:
        """Per-call NCBI rate-limit floor in seconds (depends on API key)."""
        return _NCBI_RATE_LIMIT_WITH_KEY_SECONDS if self._api_key else _NCBI_RATE_LIMIT_NO_KEY_SECONDS

    # ── audit log ─────────────────────────────────────────────────────────

    def _audit(self, egress: list[dict[str, Any]]) -> None:
        """Best-effort append of an ``entity_ncbi.lookup`` dispatch event.

        Failures to write the audit log are logged at DEBUG and swallowed
        — a transient audit-log issue should not crash a lookup. Per
        DEC-0061 the dispatch shape is single-call: one DispatchEvent
        per ``lookup_entity`` invocation that issued network traffic,
        with the per-source egress entries gathered into one list.
        """
        if not self._audit_log or not egress:
            return
        # Importing inside the method keeps the module-import surface
        # decoupled from audit_log's own import side-effects (mkdir on
        # ``~/.linus``). The audit_log module is small; the import cost
        # is negligible.
        try:
            from linus.memory.audit_log import DispatchEvent

            event = DispatchEvent(
                session_id="entity_ncbi",
                turn_id=0,
                worker_id="entity_ncbi.lookup",
                cot_budget="linear",
                memory_mode="stateless",
                context_used_tokens=0,
                context_capped=False,
                tags=["tool:entity_ncbi.lookup"],
                network_egress=list(egress),
            )
            self._audit_log.append_dispatch(event)
        except Exception as exc:
            logger.debug("audit append failed: %s", exc)

    # ── EntityLookup protocol ────────────────────────────────────────────

    def lookup_entity(self, name: str, kind: str | None = None) -> dict[str, Any] | None:
        """Resolve ``name`` against the cache, then the network if reachable.

        Returns a dict with shape::

            {
                "kind": "gene" | "protein" | "chemical" | str,
                "source": "ncbi:gene" | "uniprot" | "chebi" | str,
                "canonical_name": str,
                "external_id": str,
                "cached_at": int,  # unix ns
            }

        or ``None`` when neither cache nor network produce a hit.

        The cache is checked first; on miss, ``offline_only`` short-
        circuits to ``None`` without a network call. Otherwise, the
        reachability check decides whether to attempt resolution. If a
        ``kind`` hint is supplied, only the matching backend is tried;
        a ``None`` ``kind`` tries NCBI → UniProt → ChEBI in order.

        See module docstring for the privacy posture: this is the only
        producer of external HTTP calls in the module, and the name
        validation gate runs before any URL is built.
        """
        # Privacy gate (DEC-0061): reject invalid names before any I/O.
        if not _is_safe_name(name):
            return None

        # 1. Cache check.
        cached = self._cache_get(name, kind)
        if cached is not None:
            return cached

        # 2. Reachability / offline_only short-circuit.
        if self._offline_only:
            return None
        if not _network_reachable():
            return None

        # 3. Route by kind hint.
        attempts: list[str]
        if kind == "gene":
            attempts = ["gene"]
        elif kind == "protein":
            attempts = ["protein"]
        elif kind == "chemical":
            attempts = ["chemical"]
        else:
            attempts = ["gene", "protein", "chemical"]

        # 4. Try each backend in order; first non-None wins. Egress
        # accumulates across attempts so the audit-log record reflects
        # every call that was made, even if the first non-None result
        # came from the third backend.
        all_egress: list[dict[str, Any]] = []
        result: dict[str, Any] | None = None
        try:
            for source in attempts:
                if source == "gene":
                    candidate, egress = self._ncbi_gene_lookup(name)
                elif source == "protein":
                    candidate, egress = self._uniprot_lookup(name)
                else:
                    candidate, egress = self._chebi_lookup(name)
                all_egress.extend(egress)
                if candidate is not None:
                    result = candidate
                    break
        except (httpx.HTTPError, OSError) as exc:
            # Any network-layer failure: log at debug, return None per
            # the online_optional contract.
            logger.debug("network call failed for %r: %s", name, exc)
            self._audit(all_egress)
            return None

        # 5. Audit + cache populate (only on success).
        self._audit(all_egress)
        if result is None:
            return None

        # ``cached_at`` is set during cache_put; produce the same shape
        # the cache_get path would return for consistency.
        self._cache_put(name, kind, result)
        cached_back = self._cache_get(name, kind)
        return cached_back if cached_back is not None else {**result, "cached_at": time.time_ns()}
