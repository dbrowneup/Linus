"""Tests for :mod:`linus.knowledge.rigor` — the OUTPUT-surface grounding gate.

This is the hermetic test surface for the Q1 grounding gate (DEC-0059). It
covers each baseline check independently, the :func:`check_grounding`
orchestrator that merges them, the :func:`check_all` generalized
composition for post-reveal extensions, and edge cases around
backend-unavailable + missing-evidence semantics.

The suite is fully hermetic — pure in-process Python, no Ollama, no KB,
no network. The :class:`MockPaperLookup` fixture stands in for a real
:class:`linus.knowledge.adapter.KnowledgeBaseAdapter`; the stub entity
backend :class:`linus.knowledge.rigor.BuiltinEntityLookup` is exercised
end-to-end without modification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from linus.knowledge.rigor import (
    BuiltinEntityLookup,
    RigorFailure,
    RigorResult,
    check_all,
    check_citations,
    check_confidence,
    check_entities,
    check_grounding,
    result_to_dict,
)

# ── Fixtures ───────────────────────────────────────────────────────────────


@dataclass
class _FakePaper:
    """Minimal paper record exposed by :class:`MockPaperLookup`."""

    paper_id: str
    page_count: int


class MockPaperLookup:
    """In-memory :class:`PaperLookup` stand-in for hermetic tests.

    Constructed with a dict ``{paper_id: page_count}``; :meth:`get_paper`
    returns a :class:`_FakePaper` or None, and :meth:`get_page_count`
    returns the configured page count (or ``None`` if not configured).
    """

    def __init__(self, papers: dict[str, int | None]) -> None:
        self.papers = papers

    def get_paper(self, paper_id: str) -> Any | None:
        if paper_id not in self.papers:
            return None
        return _FakePaper(paper_id=paper_id, page_count=self.papers[paper_id] or 0)

    def get_page_count(self, paper_id: str) -> int | None:
        return self.papers.get(paper_id)


@pytest.fixture
def papers_backend() -> MockPaperLookup:
    """Three known papers with varying page counts; one with unknown count."""
    return MockPaperLookup(
        {
            "sha_a": 12,
            "sha_b": 30,
            "sha_c": 5,
            "sha_unknown_pages": None,
        }
    )


@pytest.fixture
def entities_backend() -> BuiltinEntityLookup:
    """The default builtin stub backend used in production v0.5.0."""
    return BuiltinEntityLookup()


# ── check_citations: baseline behaviors ────────────────────────────────────


def test_check_citations_all_resolve_passes(papers_backend: MockPaperLookup) -> None:
    """Happy path: every cited paper_id resolves; no page failures."""
    claim = {
        "citations": [
            {"paper_id": "sha_a", "page": 4, "excerpt": "...", "score": 0.9},
            {"paper_id": "sha_b", "page": 1, "excerpt": "...", "score": 0.8},
        ],
    }
    result = check_citations(claim, papers_backend)
    assert result.passed is True
    assert result.failures == []
    assert result.extras["citations_checked"] == 2


def test_check_citations_unresolved_paper_is_error(papers_backend: MockPaperLookup) -> None:
    """A paper_id not in the backend → ``unresolved_citation`` error."""
    claim = {
        "citations": [
            {"paper_id": "sha_fake", "page": 1, "excerpt": "..."},
        ],
    }
    result = check_citations(claim, papers_backend)
    assert result.passed is False
    assert result.error_count == 1
    assert result.failures[0].kind == "unresolved_citation"
    assert result.failures[0].severity == "error"
    assert result.failures[0].target == "sha_fake"


def test_check_citations_page_out_of_range_is_error(papers_backend: MockPaperLookup) -> None:
    """A page beyond the paper's page count → ``page_out_of_range`` error."""
    claim = {
        "citations": [
            {"paper_id": "sha_a", "page": 99, "excerpt": "..."},
        ],
    }
    result = check_citations(claim, papers_backend)
    assert result.passed is False
    assert result.error_count == 1
    assert result.failures[0].kind == "page_out_of_range"
    assert result.failures[0].severity == "error"
    assert "12 page" in result.failures[0].detail


def test_check_citations_page_below_one_is_error(papers_backend: MockPaperLookup) -> None:
    """A page < 1 (e.g. 0, -3) → ``page_out_of_range`` error."""
    claim = {"citations": [{"paper_id": "sha_a", "page": 0}]}
    result = check_citations(claim, papers_backend)
    assert result.passed is False
    assert result.failures[0].kind == "page_out_of_range"


def test_check_citations_no_page_skips_page_check(papers_backend: MockPaperLookup) -> None:
    """Missing/None page on a citation isn't a failure (page is optional)."""
    claim = {"citations": [{"paper_id": "sha_a", "page": None}]}
    result = check_citations(claim, papers_backend)
    assert result.passed is True
    assert result.failures == []


def test_check_citations_unknown_page_count_skips_page_check(
    papers_backend: MockPaperLookup,
) -> None:
    """When the backend doesn't know the page count, the page check is skipped
    rather than punishing the Worker for upstream metadata gaps."""
    claim = {"citations": [{"paper_id": "sha_unknown_pages", "page": 999}]}
    result = check_citations(claim, papers_backend)
    assert result.passed is True
    assert result.failures == []


def test_check_citations_non_integer_page_warns(papers_backend: MockPaperLookup) -> None:
    """A page that can't be parsed as int is a warning, not an error."""
    claim = {"citations": [{"paper_id": "sha_a", "page": "page seven"}]}
    result = check_citations(claim, papers_backend)
    # Warning, not error → passes the gate.
    assert result.passed is True
    assert result.warning_count == 1
    assert result.failures[0].kind == "page_out_of_range"
    assert result.failures[0].severity == "warning"


def test_check_citations_missing_paper_id_field_warns(
    papers_backend: MockPaperLookup,
) -> None:
    """A citation dict with no paper_id is a warning, not an error."""
    claim = {"citations": [{"page": 3, "excerpt": "..."}]}
    result = check_citations(claim, papers_backend)
    assert result.passed is True
    assert result.warning_count == 1
    assert result.failures[0].kind == "missing_evidence"


def test_check_citations_evidence_alias_recognized(papers_backend: MockPaperLookup) -> None:
    """Citations carried under ``evidence`` (the S25 BioReason-Pro alias)
    are recognized identically to ``citations``."""
    claim = {
        "evidence": [
            {"paper_id": "sha_a", "page": 1},
        ],
    }
    result = check_citations(claim, papers_backend)
    assert result.passed is True
    assert result.extras["citations_checked"] == 1


def test_check_citations_no_citations_warns_missing_evidence(
    papers_backend: MockPaperLookup,
) -> None:
    """A claim with no citations is a ``missing_evidence`` warning,
    not an error — observational claims sometimes legitimately don't cite."""
    claim = {"rationale": "Some bare assertion."}
    result = check_citations(claim, papers_backend)
    assert result.passed is True
    assert result.warning_count == 1
    assert result.failures[0].kind == "missing_evidence"


def test_check_citations_backend_unavailable_warns(papers_backend) -> None:
    """``papers=None`` → single ``backend_unavailable`` warning, passes."""
    claim = {"citations": [{"paper_id": "sha_a", "page": 1}]}
    result = check_citations(claim, None)
    assert result.passed is True
    assert result.warning_count == 1
    assert result.failures[0].kind == "backend_unavailable"
    assert result.failures[0].target == "papers"


# ── check_entities ─────────────────────────────────────────────────────────


def test_check_entities_known_entity_passes(entities_backend: BuiltinEntityLookup) -> None:
    """Entities in the builtin seed table resolve and produce no failures."""
    claim = {"entities": [{"name": "BRCA1", "kind": "gene"}]}
    result = check_entities(claim, entities_backend)
    assert result.passed is True
    assert result.failures == []
    assert result.extras["entities_checked"] == 1


def test_check_entities_case_insensitive_lookup(entities_backend: BuiltinEntityLookup) -> None:
    """Builtin lookups are case-insensitive so 'brca1' resolves the same as 'BRCA1'."""
    claim = {"entities": [{"name": "brca1"}]}
    result = check_entities(claim, entities_backend)
    assert result.passed is True
    assert result.failures == []


def test_check_entities_unknown_entity_warns_not_errors(
    entities_backend: BuiltinEntityLookup,
) -> None:
    """An unknown entity is a *warning*, not an error — the stub backend's
    explicit "flag, don't block" semantics from DEC-0059."""
    claim = {"entities": [{"name": "FAKEGENE42"}]}
    result = check_entities(claim, entities_backend)
    assert result.passed is True  # warnings don't fail the gate
    assert result.warning_count == 1
    assert result.error_count == 0
    assert result.failures[0].kind == "unresolved_entity"
    assert result.failures[0].severity == "warning"
    assert result.failures[0].target == "FAKEGENE42"


def test_check_entities_bare_string_entity(entities_backend: BuiltinEntityLookup) -> None:
    """Entities listed as bare strings (no dict wrapper) are accepted."""
    claim = {"entities": ["TP53"]}
    result = check_entities(claim, entities_backend)
    assert result.passed is True
    assert result.failures == []


def test_check_entities_entity_with_no_name_warns(
    entities_backend: BuiltinEntityLookup,
) -> None:
    """An entity dict missing both name and symbol → unresolved_entity warning."""
    claim = {"entities": [{"kind": "gene"}]}
    result = check_entities(claim, entities_backend)
    assert result.passed is True
    assert result.warning_count == 1


def test_check_entities_no_entities_listed_is_clean(
    entities_backend: BuiltinEntityLookup,
) -> None:
    """A claim without entities is fine — methodological claims often have none."""
    claim = {"rationale": "Method statement only."}
    result = check_entities(claim, entities_backend)
    assert result.passed is True
    assert result.failures == []
    assert result.extras["entities_checked"] == 0


def test_check_entities_backend_unavailable_warns() -> None:
    """``entities=None`` → single ``backend_unavailable`` warning, passes."""
    claim = {"entities": ["BRCA1"]}
    result = check_entities(claim, None)
    assert result.passed is True
    assert result.warning_count == 1
    assert result.failures[0].kind == "backend_unavailable"
    assert result.failures[0].target == "entities"


def test_check_entities_symbol_field_also_works(
    entities_backend: BuiltinEntityLookup,
) -> None:
    """An entity dict using ``symbol`` instead of ``name`` resolves the same."""
    claim = {"entities": [{"symbol": "EGFR"}]}
    result = check_entities(claim, entities_backend)
    assert result.passed is True
    assert result.failures == []


def test_check_entities_id_field_also_works(entities_backend: BuiltinEntityLookup) -> None:
    """An entity dict using ``id`` as a final fallback resolves the same."""
    claim = {"entities": [{"id": "MYC"}]}
    result = check_entities(claim, entities_backend)
    assert result.passed is True


# ── BuiltinEntityLookup direct ─────────────────────────────────────────────


def test_builtin_entity_lookup_known_returns_dict() -> None:
    """Direct lookup of a known entity returns its seed dict."""
    backend = BuiltinEntityLookup()
    result = backend.lookup_entity("BRCA1")
    assert result is not None
    assert result["kind"] == "gene"
    assert result["source"] == "stub:builtin"


def test_builtin_entity_lookup_unknown_returns_none() -> None:
    """Direct lookup of an unknown entity returns ``None``."""
    backend = BuiltinEntityLookup()
    assert backend.lookup_entity("NONEXISTENT") is None


def test_builtin_entity_lookup_empty_name_returns_none() -> None:
    """An empty-string name returns ``None`` (not a crash)."""
    backend = BuiltinEntityLookup()
    assert backend.lookup_entity("") is None


def test_builtin_entity_lookup_custom_seed_table() -> None:
    """A custom seed table overrides the default."""
    backend = BuiltinEntityLookup(entities={"FOO": {"kind": "made_up"}})
    assert backend.lookup_entity("FOO") is not None
    # Built-in defaults are no longer present.
    assert backend.lookup_entity("BRCA1") is None


# ── check_confidence ──────────────────────────────────────────────────────


def test_check_confidence_no_priors_yields_none_calibration() -> None:
    """No prior runs → no warning, no calibration estimable."""
    claim = {"rationale": "...", "confidence": 0.8}
    result = check_confidence(claim, prior_runs=None)
    assert result.passed is True
    assert result.failures == []
    assert result.confidence_calibration is None
    assert result.extras["prior_runs"] == 0


def test_check_confidence_empty_priors_yields_none_calibration() -> None:
    """Empty prior_runs list → same as None."""
    claim = {"rationale": "..."}
    result = check_confidence(claim, prior_runs=[])
    assert result.passed is True
    assert result.confidence_calibration is None


def test_check_confidence_single_agreeing_prior_no_warning() -> None:
    """One prior run with substantially overlapping rationale + citations
    yields no warning and a high calibration."""
    claim = {
        "rationale": "BRCA1 and TP53 modulate DNA repair pathways",
        "citations": [{"paper_id": "sha_a"}, {"paper_id": "sha_b"}],
        "confidence": 0.9,
    }
    prior = {
        "rationale": "BRCA1 and TP53 modulate DNA repair pathways",
        "citations": [{"paper_id": "sha_a"}, {"paper_id": "sha_b"}],
    }
    result = check_confidence(claim, prior_runs=[prior])
    assert result.passed is True
    assert result.warning_count == 0
    assert result.confidence_calibration is not None
    assert result.confidence_calibration > 0.8  # high agreement scales near declared


def test_check_confidence_two_diverging_priors_warns() -> None:
    """Two priors that disagree on both rationale + cited papers
    → ``confidence_divergence`` warning + reduced calibration."""
    claim = {
        "rationale": "yellow daffodil chemistry alpha beta gamma",
        "citations": [{"paper_id": "sha_a"}],
        "confidence": 0.9,
    }
    prior_1 = {
        "rationale": "completely unrelated zebra octopus mango",
        "citations": [{"paper_id": "sha_x"}],
    }
    prior_2 = {
        "rationale": "another wholly different lemon iceberg banana",
        "citations": [{"paper_id": "sha_y"}],
    }
    result = check_confidence(claim, prior_runs=[prior_1, prior_2])
    assert result.passed is True  # divergence is a warning, never an error
    assert result.warning_count == 1
    assert result.failures[0].kind == "confidence_divergence"
    assert result.confidence_calibration is not None
    # With ~0 similarity, calibration should be substantially reduced
    # from the declared 0.9.
    assert result.confidence_calibration < 0.3


def test_check_confidence_two_agreeing_priors_no_warning() -> None:
    """Two priors that AGREE — no warning even though there are >=2 priors."""
    claim = {
        "rationale": "alpha beta gamma delta",
        "citations": [{"paper_id": "sha_a"}, {"paper_id": "sha_b"}],
        "confidence": 0.85,
    }
    prior_1 = {
        "rationale": "alpha beta gamma delta",
        "citations": [{"paper_id": "sha_a"}, {"paper_id": "sha_b"}],
    }
    prior_2 = {
        "rationale": "alpha beta gamma delta",
        "citations": [{"paper_id": "sha_a"}, {"paper_id": "sha_b"}],
    }
    result = check_confidence(claim, prior_runs=[prior_1, prior_2])
    assert result.passed is True
    assert result.warning_count == 0


def test_check_confidence_no_declared_uses_similarity_directly() -> None:
    """When the claim has no ``confidence`` field, the calibration is the
    raw average similarity rather than a scaled-by-declared value."""
    claim = {"rationale": "alpha beta", "citations": [{"paper_id": "sha_a"}]}
    prior = {"rationale": "alpha beta", "citations": [{"paper_id": "sha_a"}]}
    result = check_confidence(claim, prior_runs=[prior])
    assert result.confidence_calibration is not None
    # Perfect agreement → calibration close to 1.0
    assert result.confidence_calibration > 0.9


def test_check_confidence_non_numeric_declared_is_treated_as_missing() -> None:
    """A non-numeric ``confidence`` value falls back to similarity-only calibration."""
    claim = {
        "rationale": "alpha beta",
        "citations": [{"paper_id": "sha_a"}],
        "confidence": "high",
    }
    prior = {"rationale": "alpha beta", "citations": [{"paper_id": "sha_a"}]}
    result = check_confidence(claim, prior_runs=[prior])
    # Falls through to similarity-only path; shouldn't crash.
    assert result.confidence_calibration is not None


def test_check_confidence_answer_field_alias_recognized() -> None:
    """A prior using ``answer`` instead of ``rationale`` is compared the same way."""
    claim = {"rationale": "alpha beta gamma"}
    prior = {"answer": "alpha beta gamma"}
    result = check_confidence(claim, prior_runs=[prior])
    assert result.passed is True
    # High similarity since token bags match.
    assert result.warning_count == 0


# ── check_grounding orchestrator ───────────────────────────────────────────


def test_check_grounding_full_happy_path(
    papers_backend: MockPaperLookup,
    entities_backend: BuiltinEntityLookup,
) -> None:
    """All three checks pass cleanly → ``passed=True``, no failures."""
    claim = {
        "rationale": "Citation-grounded sentence about BRCA1.",
        "citations": [{"paper_id": "sha_a", "page": 3}],
        "entities": [{"name": "BRCA1", "kind": "gene"}],
        "confidence": 0.85,
    }
    result = check_grounding(claim, papers=papers_backend, entities=entities_backend)
    assert result.passed is True
    assert result.failures == []
    # Telemetry merged per-subsystem.
    assert "citations" in result.extras
    assert "entities" in result.extras
    assert "confidence" in result.extras


def test_check_grounding_citation_error_fails_gate(
    papers_backend: MockPaperLookup,
    entities_backend: BuiltinEntityLookup,
) -> None:
    """An unresolved citation (error) fails the gate even when entities pass."""
    claim = {
        "citations": [{"paper_id": "sha_fake", "page": 1}],
        "entities": [{"name": "BRCA1"}],
    }
    result = check_grounding(claim, papers=papers_backend, entities=entities_backend)
    assert result.passed is False
    assert result.error_count == 1


def test_check_grounding_entity_warning_does_not_fail_gate(
    papers_backend: MockPaperLookup,
    entities_backend: BuiltinEntityLookup,
) -> None:
    """An unresolved entity (warning) does NOT fail the gate — DEC-0059's
    stub-with-warning-not-error decision."""
    claim = {
        "citations": [{"paper_id": "sha_a", "page": 1}],
        "entities": [{"name": "TOTALLYMADEUPGENE"}],
    }
    result = check_grounding(claim, papers=papers_backend, entities=entities_backend)
    assert result.passed is True
    assert result.warning_count == 1
    assert result.error_count == 0


def test_check_grounding_no_backends_skips_with_warnings(
    papers_backend: MockPaperLookup,
) -> None:
    """All backends None → all three checks return backend warnings,
    no errors, gate passes (functional in CI environment without KB)."""
    claim = {"rationale": "..."}
    result = check_grounding(claim)
    assert result.passed is True
    assert result.error_count == 0
    # papers + entities backends both produce a backend_unavailable warning;
    # confidence with no priors produces nothing.
    backend_warnings = [f for f in result.failures if f.kind == "backend_unavailable"]
    assert len(backend_warnings) == 2


def test_check_grounding_aggregates_warnings(
    papers_backend: MockPaperLookup,
    entities_backend: BuiltinEntityLookup,
) -> None:
    """Warnings from multiple checks aggregate into a single failures list."""
    claim = {
        "rationale": "alpha",
        "citations": [{"paper_id": "sha_a", "page": 1}],
        "entities": [{"name": "UNKNOWN_GENE"}],
    }
    prior_disagree = {
        "rationale": "completely different content",
        "citations": [{"paper_id": "sha_b"}],
    }
    prior_disagree_2 = {
        "rationale": "yet another disagreement",
        "citations": [{"paper_id": "sha_c"}],
    }
    result = check_grounding(
        claim,
        papers=papers_backend,
        entities=entities_backend,
        prior_runs=[prior_disagree, prior_disagree_2],
    )
    assert result.passed is True
    # 1 warning from entities (unresolved) + 1 from confidence (divergence)
    # = at least 2 warnings, zero errors.
    assert result.warning_count >= 2
    assert result.error_count == 0


def test_check_grounding_confidence_calibration_propagates(
    papers_backend: MockPaperLookup,
    entities_backend: BuiltinEntityLookup,
) -> None:
    """The merged result carries the calibration from ``check_confidence``."""
    claim = {
        "rationale": "alpha beta",
        "citations": [{"paper_id": "sha_a", "page": 1}],
        "confidence": 0.8,
    }
    prior = {"rationale": "alpha beta", "citations": [{"paper_id": "sha_a"}]}
    result = check_grounding(
        claim,
        papers=papers_backend,
        entities=entities_backend,
        prior_runs=[prior],
    )
    assert result.confidence_calibration is not None


# ── check_all (generalized composition for post-reveal extensions) ─────────


def test_check_all_empty_list_passes() -> None:
    """No checks supplied → trivially passes with empty result."""
    result = check_all({}, checks=None)
    assert result.passed is True
    assert result.failures == []


def test_check_all_combines_results_in_order() -> None:
    """Multiple pre-bound checks combine their failures and telemetry."""

    def check_a() -> RigorResult:
        return RigorResult(
            passed=True,
            failures=[RigorFailure(kind="missing_evidence", detail="a", severity="warning")],
            extras={"name": "a"},
        )

    def check_b() -> RigorResult:
        return RigorResult(
            passed=False,
            failures=[RigorFailure(kind="unresolved_citation", detail="b", severity="error")],
            extras={"name": "b"},
        )

    result = check_all({}, checks=[check_a, check_b])
    assert result.passed is False  # one error → gate fails
    assert result.error_count == 1
    assert result.warning_count == 1
    assert result.extras["0"]["name"] == "a"
    assert result.extras["1"]["name"] == "b"


def test_check_all_takes_calibration_from_last_provider() -> None:
    """When multiple checks supply calibration, the last non-None wins."""

    def check_a() -> RigorResult:
        return RigorResult(passed=True, confidence_calibration=0.5)

    def check_b() -> RigorResult:
        return RigorResult(passed=True, confidence_calibration=0.9)

    result = check_all({}, checks=[check_a, check_b])
    assert result.confidence_calibration == 0.9


def test_check_all_skips_none_calibration() -> None:
    """A check returning ``confidence_calibration=None`` doesn't overwrite a
    prior non-None value (the calibration-from-last-provider rule)."""

    def with_calib() -> RigorResult:
        return RigorResult(passed=True, confidence_calibration=0.7)

    def no_calib() -> RigorResult:
        return RigorResult(passed=True, confidence_calibration=None)

    result = check_all({}, checks=[with_calib, no_calib])
    assert result.confidence_calibration == 0.7


# ── RigorResult / RigorFailure dataclass behavior ─────────────────────────


def test_rigor_result_error_and_warning_counts() -> None:
    """The error_count / warning_count properties tally severities correctly."""
    failures = [
        RigorFailure(kind="unresolved_citation", detail="", severity="error"),
        RigorFailure(kind="unresolved_entity", detail="", severity="warning"),
        RigorFailure(kind="unresolved_entity", detail="", severity="warning"),
    ]
    result = RigorResult(passed=False, failures=failures)
    assert result.error_count == 1
    assert result.warning_count == 2


def test_rigor_result_default_factory_lists_are_independent() -> None:
    """Default ``field(default_factory=...)`` ensures separate instances do
    not share the same list/dict object."""
    a = RigorResult(passed=True)
    b = RigorResult(passed=True)
    a.failures.append(RigorFailure(kind="missing_evidence", detail="", severity="warning"))
    assert b.failures == []
    a.extras["x"] = 1
    assert b.extras == {}


# ── result_to_dict serialization ───────────────────────────────────────────


def test_result_to_dict_round_trip() -> None:
    """Serialization preserves every field of the result + each failure."""
    result = RigorResult(
        passed=False,
        failures=[
            RigorFailure(
                kind="unresolved_citation",
                detail="missing sha",
                severity="error",
                target="sha_x",
            ),
        ],
        confidence_calibration=0.42,
        extras={"foo": "bar"},
    )
    serialized = result_to_dict(result)
    assert serialized["passed"] is False
    assert serialized["error_count"] == 1
    assert serialized["warning_count"] == 0
    assert serialized["confidence_calibration"] == 0.42
    assert serialized["extras"] == {"foo": "bar"}
    assert serialized["failures"][0] == {
        "kind": "unresolved_citation",
        "detail": "missing sha",
        "severity": "error",
        "target": "sha_x",
    }


def test_result_to_dict_empty_result() -> None:
    """An empty (no-failure) result serializes to a sensible JSON shape."""
    result = RigorResult(passed=True)
    serialized = result_to_dict(result)
    assert serialized["passed"] is True
    assert serialized["failures"] == []
    assert serialized["confidence_calibration"] is None


# ── Edge cases ─────────────────────────────────────────────────────────────


def test_empty_claim_dict_does_not_crash(
    papers_backend: MockPaperLookup,
    entities_backend: BuiltinEntityLookup,
) -> None:
    """A completely empty claim dict produces sane warnings, no crash."""
    result = check_grounding(
        {},
        papers=papers_backend,
        entities=entities_backend,
    )
    # Citations: missing_evidence warning; entities: no entries (clean);
    # confidence: no priors (clean). Net: 1 warning, 0 errors.
    assert result.passed is True
    assert result.warning_count >= 1
    missing = [f for f in result.failures if f.kind == "missing_evidence"]
    assert len(missing) >= 1


def test_claim_with_citations_but_no_evidence_field_works(
    papers_backend: MockPaperLookup,
) -> None:
    """The ``citations`` key alone is enough — no ``evidence`` field needed."""
    claim = {"citations": [{"paper_id": "sha_a", "page": 1}]}
    result = check_citations(claim, papers_backend)
    assert result.passed is True
    assert result.failures == []


def test_claim_with_evidence_string_not_list_is_treated_as_missing(
    papers_backend: MockPaperLookup,
) -> None:
    """If ``evidence`` is a string (not a list), citations are treated as
    absent — guards against malformed Worker output."""
    claim = {"evidence": "see paper X"}
    result = check_citations(claim, papers_backend)
    assert result.passed is True
    assert result.warning_count == 1
    assert result.failures[0].kind == "missing_evidence"


def test_entities_as_non_list_is_ignored(entities_backend: BuiltinEntityLookup) -> None:
    """If ``entities`` is a string (malformed), the check treats it as
    no-entities — no crash, no failure."""
    claim = {"entities": "BRCA1"}
    result = check_entities(claim, entities_backend)
    assert result.passed is True
    assert result.failures == []
    assert result.extras["entities_checked"] == 0
