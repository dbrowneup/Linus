"""Grounding gate for stakeable Worker outputs (:mod:`linus.knowledge.rigor`).

Hard admission gate complementing :doc:`DEC-0019 </adr/0019-kb-ingest-quality-surface>`'s
soft scorecard. Where DEC-0019 scores raw material at the **INPUT** surface
(KB ingest — and intentionally does not gate it, because Dan is the
primary filter), this module gates synthesized claims at the **OUTPUT**
surface (before they reach the user or land in a manuscript draft).

The two surfaces are complementary: DEC-0019 trusts what Dan already
curated; ``rigor.py`` does not trust what a Worker just synthesized.
Workers can fabricate citations, hallucinate entity names, and disagree
with themselves across runs; the OUTPUT gate catches each of these before
the claim is staked publicly.

Three baseline checks (v0.5.0)
------------------------------

1. **Citation grounding** — every cited ``paper_id`` resolves in the KB
   metadata DB, and the cited ``page`` (when provided) is within that
   paper's ``page_count``. Unresolved paper ids and out-of-range pages
   are ``error``-severity failures; they fail the gate.

2. **Entity grounding** — every named biological entity (gene, protein,
   ontology term) resolves in a reference store (NCBI Gene, UniProt, GO
   ontology). v0.5.0 ships a stub :class:`BuiltinEntityLookup` seeded
   with a handful of well-known entities (BRCA1, TP53, EGFR, …) so the
   end-to-end shape is exercisable without network or external lookups.
   Unknown entities are ``warning``-severity (NOT error) — the stub
   backend explicitly says "flag, don't block." Real backends ship
   post-reveal.

3. **Confidence calibration** — if multiple Worker runs of the same
   query produced divergent answers (recorded in the audit log per
   :doc:`DEC-0030 </adr/0030-scratchpad-first-class-artifact>` and
   :doc:`DEC-0031 </adr/0031-router-primitives-cot-budget-memory-mode>`),
   reduce calibrated confidence proportionally and surface a
   ``confidence_divergence`` warning. Empty / single-run prior history
   produces no warning and a ``calibration=None`` field.

Extension points (POST-REVEAL, NOT v0.5.0 scope)
------------------------------------------------

The 2026-05-19 Archimedes cross-pollination conversation surfaced two
additional surfaces where the same gate shape applies. The module is
structured so each is an additive plug-in, not a refactor:

- ``check_temporal_grounding(claim, asof_date)`` — look-ahead audit for
  scientific time-series outputs (longitudinal biological measurements,
  sequencing campaigns, growth-rate curves). Verifies that every cited
  source predates the claim's ``asof_date`` so the synthesis is causally
  honest. Same :class:`RigorResult` return shape; same orchestrator
  composition.

- ``check_quantitative_overfitting(strategy_claim)`` — Archimedes-style
  Deflated Sharpe Ratio (DSR), Combinatorially-Symmetric Cross-Validation
  (CSCV), and walk-forward out-of-sample (OOS) checks for any
  entrepreneurial-surface output that quantifies a strategy (yield model,
  pricing curve, market sizing). Same return shape.

Each extension is a separate pure function
``check_<thing>(claim, ...) -> RigorResult`` that composes with the
baseline via :func:`check_all`. Adding one is the size of a new function +
a new test — not a refactor of the orchestrator. The orchestrator surface
``check_grounding`` deliberately keeps the v0.5.0 baseline signature
stable; richer compositions go through :func:`check_all`.

Contract surfaces
-----------------

The module consumes existing Linus shapes and changes none of them:

- :class:`ClaimDict` follows the citation + claim-categories interface from
  :doc:`DEC-0023 </adr/0023-output-interface-citations-llm-wiki>` and the
  ``citation_to_provenance`` shape from :mod:`linus.knowledge.paperqa`:
  ``{"paper_id", "page", "excerpt", "score"}`` per citation, with the
  S25-style "BioReason-Pro" enrichment fields (``rationale``,
  ``confidence``, ``evidence``, ``entities``) on the wrapping claim.

- :class:`PaperLookup` and :class:`EntityLookup` are :class:`Protocol`
  classes — anything with the right method shape satisfies them. The real
  paper backend in production is a thin adapter around
  :class:`linus.knowledge.adapter.KnowledgeBaseAdapter`; the real entity
  backend is a Phase 7 deliverable. Tests inject mocks or the builtin
  stub.

See DEC-0059 (the grounding gate ADR) for the design decision and
``docs/specs/`` for the broader v0.5.0 hackathon-prep framing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

# ── Types ──────────────────────────────────────────────────────────────────

#: Shape of a Worker-output claim, mirroring
#: :func:`linus.knowledge.paperqa.citation_to_provenance` for ``citations``
#: entries (``{"paper_id", "page", "excerpt", "score"}``) and the S25
#: BioReason-Pro convention for the wrapping fields (``rationale``,
#: ``confidence``, ``evidence``, ``entities``). Modeled as a plain ``dict``
#: rather than a TypedDict so backwards-compatible field additions don't
#: ripple through every callsite.
ClaimDict = dict[str, Any]


FailureKind = Literal[
    "unresolved_citation",  # paper_id not in KB metadata DB
    "page_out_of_range",  # cited page > paper's page count
    "unresolved_entity",  # named entity not in reference store
    "confidence_divergence",  # multiple Worker runs disagree
    "missing_evidence",  # claim has no evidence/citations
    "backend_unavailable",  # paper / entity / audit backend not configured
]


Severity = Literal["warning", "error"]


@dataclass
class RigorFailure:
    """A single failed check on a claim.

    ``kind`` enumerates the documented failure modes (one of
    :data:`FailureKind`); ``detail`` is a human-readable message safe to
    surface in chat UI or PR-review comments; ``severity`` decides
    whether the failure fails the gate (``error``) or only annotates it
    (``warning``). ``target`` identifies the specific offending item
    (paper id, entity name, etc.) so the caller can quote it back to the
    Worker for a single-shot retry.
    """

    kind: FailureKind
    detail: str
    severity: Severity
    target: str | None = None


@dataclass
class RigorResult:
    """Aggregated outcome of running one or more rigor checks against a claim.

    ``passed`` is the gate verdict — True iff ``error_count == 0``.
    Warnings propagate as info; they never fail the gate. The
    ``confidence_calibration`` field is populated when the divergence
    check has enough prior runs to estimate calibrated confidence (0.0
    fully diverged through 1.0 fully consistent); otherwise ``None``.
    ``extras`` is a per-check telemetry bag — tests inspect it; production
    callers may log it.
    """

    passed: bool
    failures: list[RigorFailure] = field(default_factory=list)
    confidence_calibration: float | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def error_count(self) -> int:
        """Number of failures with ``severity == 'error'`` (gate-failing)."""
        return sum(1 for f in self.failures if f.severity == "error")

    @property
    def warning_count(self) -> int:
        """Number of failures with ``severity == 'warning'`` (informational)."""
        return sum(1 for f in self.failures if f.severity == "warning")


# ── Lookup protocols (so checks accept real or stub backends) ──────────────


class PaperLookup(Protocol):
    """Minimal contract any paper backend must satisfy.

    The production adapter is a thin wrapper around
    :class:`linus.knowledge.adapter.KnowledgeBaseAdapter` that maps
    ``paper_id`` → SHA256 ``sha256`` and exposes ``page_count``. Tests
    inject mocks satisfying the same surface.
    """

    def get_paper(self, paper_id: str) -> Any | None:
        """Return a paper-like object or ``None`` if absent."""

    def get_page_count(self, paper_id: str) -> int | None:
        """Return the paper's page count, or ``None`` if unknown."""


class EntityLookup(Protocol):
    """Minimal contract any entity backend must satisfy.

    Real backends will wrap NCBI Gene, UniProt, GO, ChEBI, etc.; v0.5.0
    ships :class:`BuiltinEntityLookup` only.
    """

    def lookup_entity(self, name: str, kind: str | None = None) -> dict[str, Any] | None:
        """Return a dict describing the entity, or ``None`` if not found.

        ``kind`` is an optional hint (``"gene"``, ``"protein"``, ``"go"``,
        …) the backend may use to disambiguate; backends are free to
        ignore it.
        """


# ── Built-in stub entity backend ───────────────────────────────────────────

#: Seed list of well-known entities so tests and demos can exercise the
#: end-to-end shape without external lookups. Real backends ship
#: post-reveal per the module docstring. Kinds follow the conventional
#: NCBI / UniProt / GO categories; gene symbols are uppercased so
#: case-insensitive lookups normalize correctly.
_BUILTIN_ENTITIES: dict[str, dict[str, Any]] = {
    "BRCA1": {"kind": "gene", "source": "stub:builtin"},
    "BRCA2": {"kind": "gene", "source": "stub:builtin"},
    "TP53": {"kind": "gene", "source": "stub:builtin"},
    "EGFR": {"kind": "gene", "source": "stub:builtin"},
    "KRAS": {"kind": "gene", "source": "stub:builtin"},
    "MYC": {"kind": "gene", "source": "stub:builtin"},
    "INSULIN": {"kind": "protein", "source": "stub:builtin"},
    "ALBUMIN": {"kind": "protein", "source": "stub:builtin"},
    # Botryococcus braunii oil-pathway anchors — Dan's domain.
    "SQS": {"kind": "gene", "source": "stub:builtin"},
    "HMGR": {"kind": "gene", "source": "stub:builtin"},
}


class BuiltinEntityLookup:
    """In-process stub :class:`EntityLookup` backed by a fixed entity table.

    The semantics are intentionally narrow: known entities resolve;
    unknown entities return ``None``. Per the module-level decision (see
    DEC-0059), the resulting :class:`RigorFailure` for an unknown entity
    is ``warning``-severity, not ``error`` — the stub backend explicitly
    says "flag, don't block" so a Worker output isn't blocked from being
    staked just because we haven't wired up NCBI Gene yet.

    Names are compared case-insensitively; the seed table is uppercased,
    so callers can pass mixed-case symbols.
    """

    def __init__(self, entities: dict[str, dict[str, Any]] | None = None) -> None:
        """Construct with the default seed table (or an override for tests)."""
        # Normalize keys to uppercase so lookups are case-insensitive.
        source = entities if entities is not None else _BUILTIN_ENTITIES
        self._entities: dict[str, dict[str, Any]] = {k.upper(): v for k, v in source.items()}

    def lookup_entity(self, name: str, kind: str | None = None) -> dict[str, Any] | None:
        """Return the seed entry for ``name`` (case-insensitive) or ``None``."""
        if not name:
            return None
        return self._entities.get(name.upper())


# ── Helpers ────────────────────────────────────────────────────────────────


def _extract_citations(claim: ClaimDict) -> list[dict[str, Any]]:
    """Pull the list of citation dicts off a claim.

    Accepts the two documented carrier shapes:

    - ``claim["citations"]`` — list of provenance dicts (the
      :func:`linus.knowledge.paperqa.citation_to_provenance` shape).
    - ``claim["evidence"]`` — same shape under a different key, per the
      S25 BioReason-Pro convention.

    Returns an empty list when neither key is present or the value is
    not a list-like. The caller decides whether an empty list is a
    failure (the citation check decides yes, with ``missing_evidence``).
    """
    citations = claim.get("citations")
    if isinstance(citations, list):
        return [c for c in citations if isinstance(c, dict)]

    evidence = claim.get("evidence")
    if isinstance(evidence, list):
        return [c for c in evidence if isinstance(c, dict)]

    return []


def _extract_entities(claim: ClaimDict) -> list[dict[str, Any] | str]:
    """Pull the list of entities off a claim.

    Accepts ``claim["entities"]`` as either a list of dicts
    (``{"name": ..., "kind": ...}``) or a list of bare strings. Returns
    empty list when absent.
    """
    entities = claim.get("entities")
    if isinstance(entities, list):
        # Normalize: accept bare strings or dicts; reject anything else.
        return [e for e in entities if isinstance(e, (dict, str))]
    return []


def _entity_name_and_kind(entity: dict[str, Any] | str) -> tuple[str, str | None]:
    """Normalize an entity carrier to ``(name, kind)``.

    Bare-string entities have no kind hint.
    """
    if isinstance(entity, str):
        return entity, None
    name = entity.get("name") or entity.get("symbol") or entity.get("id") or ""
    kind = entity.get("kind") or entity.get("type")
    return str(name), str(kind) if kind else None


def _rationale_token_set(claim: ClaimDict) -> frozenset[str]:
    """Coarse token bag for a claim's rationale, for edit-distance comparison.

    A whitespace-split, lowercase token set is enough resolution for
    "did two Worker runs say substantively different things?" — we're
    looking at Jaccard divergence between rationale word bags, not
    semantic equivalence.
    """
    rationale = claim.get("rationale") or claim.get("answer") or ""
    if not isinstance(rationale, str):
        return frozenset()
    return frozenset(rationale.lower().split())


def _cited_paper_set(claim: ClaimDict) -> frozenset[str]:
    """The set of paper ids a claim cites (for divergence comparison)."""
    return frozenset(c.get("paper_id") for c in _extract_citations(claim) if c.get("paper_id"))


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    """Jaccard similarity of two sets; 1.0 if both empty (by convention)."""
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


# ── Baseline checks ────────────────────────────────────────────────────────


def check_citations(claim: ClaimDict, papers: PaperLookup | None) -> RigorResult:
    """Validate every cited ``paper_id`` resolves and every cited page is in range.

    Failure surface:

    - No ``papers`` backend → single ``backend_unavailable`` *warning*
      and ``passed=True``. The hermetic test path uses this; production
      callers should always supply a real :class:`PaperLookup`.
    - No citations on the claim → single ``missing_evidence`` *warning*
      and ``passed=True``. Some claims are observation-style and don't
      cite; the caller decides whether to treat that as a deal-breaker.
    - ``paper_id`` not found in backend → ``unresolved_citation`` *error*.
    - ``page`` provided but exceeds ``get_page_count(paper_id)`` →
      ``page_out_of_range`` *error*. A ``None`` or unknown page count
      simply skips the page check (no failure).
    """
    failures: list[RigorFailure] = []

    if papers is None:
        failures.append(
            RigorFailure(
                kind="backend_unavailable",
                detail="PaperLookup backend not configured; citation grounding skipped.",
                severity="warning",
                target="papers",
            )
        )
        return RigorResult(passed=True, failures=failures, extras={"citations_checked": 0})

    citations = _extract_citations(claim)
    if not citations:
        failures.append(
            RigorFailure(
                kind="missing_evidence",
                detail="Claim has no citations or evidence; cannot ground.",
                severity="warning",
                target=None,
            )
        )
        return RigorResult(passed=True, failures=failures, extras={"citations_checked": 0})

    checked = 0
    for citation in citations:
        paper_id = citation.get("paper_id")
        if not paper_id:
            # Provenance with no paper_id is a malformed citation but not
            # itself a grounding failure — surface it as a warning so the
            # caller can see it, and skip the resolution attempt.
            failures.append(
                RigorFailure(
                    kind="missing_evidence",
                    detail="Citation entry has no paper_id field.",
                    severity="warning",
                    target=None,
                )
            )
            continue

        checked += 1
        paper_obj = papers.get_paper(str(paper_id))
        if paper_obj is None:
            failures.append(
                RigorFailure(
                    kind="unresolved_citation",
                    detail=f"paper_id {paper_id!r} not found in KB metadata.",
                    severity="error",
                    target=str(paper_id),
                )
            )
            continue

        page = citation.get("page")
        if page is None:
            continue
        try:
            page_int = int(page)
        except (TypeError, ValueError):
            # A non-integer page is suspicious but not catastrophic; warn.
            failures.append(
                RigorFailure(
                    kind="page_out_of_range",
                    detail=f"page {page!r} on paper {paper_id!r} is not an integer.",
                    severity="warning",
                    target=str(paper_id),
                )
            )
            continue

        page_count = papers.get_page_count(str(paper_id))
        if page_count is None:
            # Unknown page count → can't validate, but don't punish the
            # Worker for upstream metadata gaps.
            continue

        if page_int < 1 or page_int > page_count:
            failures.append(
                RigorFailure(
                    kind="page_out_of_range",
                    detail=(f"page {page_int} cited on paper {paper_id!r} but the paper has {page_count} page(s)."),
                    severity="error",
                    target=str(paper_id),
                )
            )

    passed = not any(f.severity == "error" for f in failures)
    return RigorResult(
        passed=passed,
        failures=failures,
        extras={"citations_checked": checked},
    )


def check_entities(claim: ClaimDict, entities: EntityLookup | None) -> RigorResult:
    """Validate every named entity on the claim resolves in the reference store.

    Per the stub-backend decision (DEC-0059): unresolved entities are
    ``warning``-severity, not ``error``. v0.5.0 cannot reliably block on
    an entity miss when the production entity backend is still a stub —
    a missed lookup is more likely "we haven't wired up that source yet"
    than "the Worker fabricated the entity." Real backends ship
    post-reveal and may re-promote this to ``error``.

    Failure surface:

    - No ``entities`` backend → single ``backend_unavailable`` warning,
      ``passed=True``.
    - No entities listed on the claim → empty result, ``passed=True``,
      no warnings. Many claims are entity-free (e.g., methodological
      statements).
    - Entity not in backend → ``unresolved_entity`` *warning*.
    """
    failures: list[RigorFailure] = []

    if entities is None:
        failures.append(
            RigorFailure(
                kind="backend_unavailable",
                detail="EntityLookup backend not configured; entity grounding skipped.",
                severity="warning",
                target="entities",
            )
        )
        return RigorResult(passed=True, failures=failures, extras={"entities_checked": 0})

    claim_entities = _extract_entities(claim)
    if not claim_entities:
        return RigorResult(passed=True, failures=[], extras={"entities_checked": 0})

    checked = 0
    for entity in claim_entities:
        name, kind = _entity_name_and_kind(entity)
        if not name:
            failures.append(
                RigorFailure(
                    kind="unresolved_entity",
                    detail="Entity entry has no name/symbol/id field.",
                    severity="warning",
                    target=None,
                )
            )
            continue

        checked += 1
        resolved = entities.lookup_entity(name, kind=kind)
        if resolved is None:
            failures.append(
                RigorFailure(
                    kind="unresolved_entity",
                    detail=(
                        f"entity {name!r}"
                        + (f" (kind={kind})" if kind else "")
                        + " not found in reference store (stub backend; warn-not-block)."
                    ),
                    severity="warning",
                    target=name,
                )
            )

    # Entity check never returns error-severity from the stub backend, so
    # `passed` is always True here. Kept as a property of the failures so
    # future real backends can flip this without changing the orchestrator.
    passed = not any(f.severity == "error" for f in failures)
    return RigorResult(
        passed=passed,
        failures=failures,
        extras={"entities_checked": checked},
    )


# Minimum Jaccard similarity below which two Worker runs are considered
# "divergent" for the purposes of confidence calibration. Empirical
# tuning is post-reveal — this is a defensible default that catches
# substantively different rationales without flagging cosmetic edits.
_DIVERGENCE_THRESHOLD: float = 0.5


def check_confidence(
    claim: ClaimDict,
    prior_runs: list[ClaimDict] | None = None,
) -> RigorResult:
    """Compare ``claim`` against prior Worker runs of the same query.

    Per :doc:`DEC-0031 </adr/0031-router-primitives-cot-budget-memory-mode>`,
    the audit log captures every Worker call's full payload; the caller
    supplies the relevant prior-runs list (already filtered to the same
    query / session). This check is therefore stateless — it does no
    audit-log lookup itself.

    Two divergence signals are combined into a single Jaccard average:

    1. **Rationale token bags** — coarse Jaccard over whitespace-split
       lowercase tokens of the ``rationale`` (or ``answer``) field.
    2. **Cited paper sets** — Jaccard over the set of ``paper_id`` values
       in the claim's citations.

    If the average similarity across all (claim, prior) pairs falls
    below :data:`_DIVERGENCE_THRESHOLD`, the result is a
    ``confidence_divergence`` *warning* (never an error — divergence is
    information, not necessarily wrong) and the calibrated confidence is
    scaled down by the similarity.

    Failure surface:

    - ``prior_runs`` is ``None`` or empty → no warning,
      ``confidence_calibration=None`` (insufficient data to calibrate).
    - One prior run → no warning if it agrees; warning if it disagrees.
    - Multiple priors → warning iff average similarity is below threshold.
    """
    failures: list[RigorFailure] = []

    if not prior_runs:
        return RigorResult(
            passed=True,
            failures=[],
            confidence_calibration=None,
            extras={"prior_runs": 0},
        )

    base_tokens = _rationale_token_set(claim)
    base_papers = _cited_paper_set(claim)

    sims: list[float] = []
    for prior in prior_runs:
        prior_tokens = _rationale_token_set(prior)
        prior_papers = _cited_paper_set(prior)
        # Average the two signals — equal-weight composite.
        sim = (_jaccard(base_tokens, prior_tokens) + _jaccard(base_papers, prior_papers)) / 2.0
        sims.append(sim)

    avg_sim = sum(sims) / len(sims)

    declared = claim.get("confidence")
    declared_f: float | None
    try:
        declared_f = float(declared) if declared is not None else None
    except (TypeError, ValueError):
        declared_f = None

    if avg_sim < _DIVERGENCE_THRESHOLD:
        failures.append(
            RigorFailure(
                kind="confidence_divergence",
                detail=(
                    f"Worker runs of the same query disagree "
                    f"(avg Jaccard similarity {avg_sim:.2f} across "
                    f"{len(prior_runs)} prior run(s), below threshold "
                    f"{_DIVERGENCE_THRESHOLD})."
                ),
                severity="warning",
                target=None,
            )
        )

    # Calibration scales declared confidence by similarity; with no
    # declared confidence we surface the raw similarity instead.
    raw = declared_f * avg_sim if declared_f is not None else avg_sim
    calibration = max(0.0, min(1.0, raw))

    return RigorResult(
        passed=True,
        failures=failures,
        confidence_calibration=calibration,
        extras={"prior_runs": len(prior_runs), "avg_similarity": avg_sim},
    )


# ── Orchestrator ───────────────────────────────────────────────────────────


def check_grounding(
    claim: ClaimDict,
    papers: PaperLookup | None = None,
    entities: EntityLookup | None = None,
    prior_runs: list[ClaimDict] | None = None,
) -> RigorResult:
    """Run the three baseline rigor checks and merge into one :class:`RigorResult`.

    ``passed`` on the merged result is True iff no constituent check
    raised an ``error``-severity failure. Warnings (including
    ``backend_unavailable`` for skipped checks) propagate; they do not
    fail the gate. ``confidence_calibration`` is carried over from
    :func:`check_confidence`; ``extras`` is merged per-check under
    keys ``"citations"``, ``"entities"``, ``"confidence"`` so the caller
    can inspect each subsystem's telemetry independently.

    This is the function to register as a Linus tool / call from a
    server's response-validation step. Richer post-reveal compositions
    (e.g., adding the time-series or quant-overfitting checks) go
    through :func:`check_all`, which keeps this signature stable.
    """
    citation_result = check_citations(claim, papers)
    entity_result = check_entities(claim, entities)
    confidence_result = check_confidence(claim, prior_runs)

    merged_failures: list[RigorFailure] = []
    merged_failures.extend(citation_result.failures)
    merged_failures.extend(entity_result.failures)
    merged_failures.extend(confidence_result.failures)

    extras = {
        "citations": citation_result.extras,
        "entities": entity_result.extras,
        "confidence": confidence_result.extras,
    }

    passed = not any(f.severity == "error" for f in merged_failures)
    return RigorResult(
        passed=passed,
        failures=merged_failures,
        confidence_calibration=confidence_result.confidence_calibration,
        extras=extras,
    )


def check_all(
    claim: ClaimDict,
    checks: list[Any] | None = None,
) -> RigorResult:
    """Generalized composition: run an arbitrary list of pre-bound checks.

    Each entry in ``checks`` must be a zero-argument callable returning a
    :class:`RigorResult` (bind backends / asof_dates / prior_runs at
    callsite via :func:`functools.partial`). This is the extension
    surface for future post-reveal checks
    (:func:`check_temporal_grounding`,
    :func:`check_quantitative_overfitting`, etc.) so the baseline
    orchestrator :func:`check_grounding` stays stable.

    ``passed`` on the merged result is True iff no constituent failure
    is ``error`` severity. ``confidence_calibration`` is taken from the
    last result that supplied a non-``None`` value (most callers will
    bind exactly one check that estimates calibration). ``extras`` is
    keyed by an integer index so callers can correlate constituent
    telemetry with the order they passed.
    """
    if not checks:
        return RigorResult(passed=True, failures=[], extras={})

    merged_failures: list[RigorFailure] = []
    calibration: float | None = None
    extras: dict[str, Any] = {}

    for idx, check in enumerate(checks):
        result = check()
        merged_failures.extend(result.failures)
        if result.confidence_calibration is not None:
            calibration = result.confidence_calibration
        extras[str(idx)] = result.extras

    passed = not any(f.severity == "error" for f in merged_failures)
    return RigorResult(
        passed=passed,
        failures=merged_failures,
        confidence_calibration=calibration,
        extras=extras,
    )


# ── Serialization helper ───────────────────────────────────────────────────


def result_to_dict(result: RigorResult) -> dict[str, Any]:
    """Serialize a :class:`RigorResult` to a plain JSON-compatible dict.

    Useful for the tool-registry surface: the Linus tool dispatcher
    expects JSON-shaped returns; dataclasses cross the wire as their
    field dict. Failures serialize as a list of dicts preserving every
    field of :class:`RigorFailure`.
    """
    return {
        "passed": result.passed,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "confidence_calibration": result.confidence_calibration,
        "failures": [
            {
                "kind": f.kind,
                "detail": f.detail,
                "severity": f.severity,
                "target": f.target,
            }
            for f in result.failures
        ],
        "extras": result.extras,
    }


__all__ = [
    "BuiltinEntityLookup",
    "ClaimDict",
    "EntityLookup",
    "FailureKind",
    "PaperLookup",
    "RigorFailure",
    "RigorResult",
    "Severity",
    "check_all",
    "check_citations",
    "check_confidence",
    "check_entities",
    "check_grounding",
    "result_to_dict",
]
