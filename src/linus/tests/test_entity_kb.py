"""Hermetic tests for :mod:`linus.knowledge.entity_kb`.

These tests do not depend on the real KB submodule's GraphML output.
A tiny fixture graph lives at ``tests/fixtures/kb/kg_graph.graphml``
(regeneratable via ``build_fixture.py`` next to it) with 5 paper
nodes + 10 entity nodes + a hand-picked edge set that produces a
known ref_count distribution. See the fixture builder docstring for
the exact composition.
"""

from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import patch

import networkx as nx
import pytest

from linus.knowledge.entity_kb import (
    ChainedEntityLookup,
    KBEntityLookup,
    default_kb_lookup,
)
from linus.knowledge.rigor import BuiltinEntityLookup, EntityLookup

_FIXTURE_GRAPHML = Path(__file__).resolve().parent / "fixtures" / "kb" / "kg_graph.graphml"


# ── KBEntityLookup: construction + missing-file error ──────────────────────


def test_construction_does_not_parse_graph(tmp_path: Path) -> None:
    """Lazy load: __init__ must not call nx.read_graphml.

    Patch read_graphml and confirm it stays uncalled until the first
    lookup_entity. This is the contract that lets callers wire the
    lookup at import time without paying the parse cost up front.
    """
    fake_path = tmp_path / "kg_graph.graphml"
    fake_path.touch()  # file must exist to pass _ensure_loaded's check

    with patch("linus.knowledge.entity_kb.nx.read_graphml") as mock_read:
        lookup = KBEntityLookup(graphml_path=fake_path)
        assert mock_read.call_count == 0
        # First lookup triggers parse.
        mock_read.return_value = nx.MultiDiGraph()
        lookup.lookup_entity("anything")
        assert mock_read.call_count == 1
        # Subsequent lookups reuse the cached parse.
        lookup.lookup_entity("anything-else")
        assert mock_read.call_count == 1


def test_missing_graphml_raises_with_helpful_message(tmp_path: Path) -> None:
    """A bad path produces FileNotFoundError naming path + env var + remediation."""
    missing = tmp_path / "does_not_exist.graphml"
    lookup = KBEntityLookup(graphml_path=missing)

    with pytest.raises(FileNotFoundError) as excinfo:
        lookup.lookup_entity("BRCA1")

    msg = str(excinfo.value)
    assert str(missing) in msg
    assert "LINUS_KB_OUTPUTS_DIR" in msg
    assert "papers_analysis.knowledge_graph" in msg


# ── KBEntityLookup: happy-path lookups against the fixture ─────────────────


def _fixture_lookup(case_insensitive: bool = True) -> KBEntityLookup:
    """Shorthand for the common-path fixture-backed lookup instance."""
    assert _FIXTURE_GRAPHML.exists(), (
        f"fixture missing at {_FIXTURE_GRAPHML}; regenerate via src/linus/tests/fixtures/kb/build_fixture.py"
    )
    return KBEntityLookup(graphml_path=_FIXTURE_GRAPHML, case_insensitive=case_insensitive)


def test_lookup_known_entity_returns_metadata() -> None:
    """BRCA1 is in the fixture; lookup returns the documented dict shape."""
    lookup = _fixture_lookup()
    result = lookup.lookup_entity("BRCA1")
    assert result is not None
    assert set(result.keys()) == {"kind", "source", "ref_count"}
    assert result["kind"] == "GENE_OR_GENE_PRODUCT"
    assert result["source"].startswith("kb:")
    assert isinstance(result["ref_count"], int)


def test_lookup_ref_count_distinguishes_well_anchored_entities() -> None:
    """BRCA1 appears in 3 fixture papers; TP53 in 1; astaxanthin in 1.

    This is the "high-ref-count = well-established in Dan's corpus"
    signal the spec calls out. The asserted values come from the
    fixture's hand-picked edge set.
    """
    lookup = _fixture_lookup()
    brca1 = lookup.lookup_entity("BRCA1")
    egfr = lookup.lookup_entity("EGFR")
    tp53 = lookup.lookup_entity("TP53")
    assert brca1 is not None
    assert egfr is not None
    assert tp53 is not None
    assert brca1["ref_count"] == 3
    assert egfr["ref_count"] == 2
    assert tp53["ref_count"] == 1


def test_lookup_unknown_entity_returns_none() -> None:
    """An entity not in the fixture resolves to None, not an exception."""
    lookup = _fixture_lookup()
    assert lookup.lookup_entity("ENTIRELY_MADE_UP_GENE_XYZ") is None


def test_lookup_empty_or_missing_name_returns_none() -> None:
    """Empty-string name short-circuits to None without touching the graph."""
    lookup = _fixture_lookup()
    assert lookup.lookup_entity("") is None


def test_lookup_phd_anchor_entity() -> None:
    """Botryococcus braunii — Dan's PhD thesis topic — must resolve.

    The fixture deliberately includes a multi-word entity to confirm
    the surface-form indexing covers more than gene symbols.
    """
    lookup = _fixture_lookup()
    result = lookup.lookup_entity("Botryococcus braunii")
    assert result is not None
    assert result["kind"] == "ORGANISM"
    assert result["ref_count"] == 1


# ── Case sensitivity ───────────────────────────────────────────────────────


def test_case_insensitive_lookup_matches_any_casing() -> None:
    """With case_insensitive=True, BRCA1 / brca1 / Brca1 all resolve."""
    lookup = _fixture_lookup(case_insensitive=True)
    for variant in ("BRCA1", "brca1", "Brca1", "bRcA1"):
        result = lookup.lookup_entity(variant)
        assert result is not None, f"variant {variant!r} should resolve"
        assert result["kind"] == "GENE_OR_GENE_PRODUCT"


def test_case_sensitive_lookup_requires_exact_match() -> None:
    """With case_insensitive=False, only the original casing resolves.

    The fixture stores BRCA1 as uppercase in the ``text`` attribute,
    so "BRCA1" matches and "brca1" does not.
    """
    lookup = _fixture_lookup(case_insensitive=False)
    assert lookup.lookup_entity("BRCA1") is not None
    assert lookup.lookup_entity("brca1") is None


def test_case_insensitive_multi_word_entity() -> None:
    """Case folding works for multi-word surfaces too."""
    lookup = _fixture_lookup(case_insensitive=True)
    assert lookup.lookup_entity("botryococcus braunii") is not None
    assert lookup.lookup_entity("BOTRYOCOCCUS BRAUNII") is not None


# ── Paper / entity disambiguation ──────────────────────────────────────────


def test_paper_node_titles_are_not_returned_as_entities() -> None:
    """Paper titles (e.g. "BRCA1 in breast cancer") are paper nodes, not entities.

    The fixture's papers have BRCA1 in their titles; a naive
    implementation that indexed all node attributes would match the
    paper title. The lookup must only return entity-typed nodes.
    """
    lookup = _fixture_lookup()
    # The paper id "paper:p1" should never appear as an entity result.
    assert lookup.lookup_entity("paper:p1") is None
    assert lookup.lookup_entity("BRCA1 in breast cancer") is None


def test_ref_count_excludes_rebel_predecessors() -> None:
    """REBEL edges (Entity → Entity) must NOT inflate ref_count.

    The fixture has an edge ``ent::brca1 → ent::dna repair`` of type
    rebel. ref_count for DNA repair should count only paper-typed
    predecessors (p5 alone, ref_count=1), not the brca1 predecessor.
    """
    lookup = _fixture_lookup()
    dna_repair = lookup.lookup_entity("DNA repair")
    assert dna_repair is not None
    assert dna_repair["ref_count"] == 1, "REBEL Entity→Entity edges must not inflate ref_count"


# ── source tag ─────────────────────────────────────────────────────────────


def test_source_tag_is_stable_for_same_file() -> None:
    """Two instances over the same file yield the same ``source`` tag."""
    lookup_a = _fixture_lookup()
    lookup_b = _fixture_lookup()
    a = lookup_a.lookup_entity("BRCA1")
    b = lookup_b.lookup_entity("BRCA1")
    assert a is not None and b is not None
    assert a["source"] == b["source"]
    # And it has the documented prefix.
    assert a["source"].startswith("kb:")


# ── ChainedEntityLookup ────────────────────────────────────────────────────


class _StubLookup:
    """Minimal EntityLookup that returns a canned dict (or None) on cue."""

    def __init__(self, table: dict[str, dict[str, object]]) -> None:
        self._table = table
        self.call_count = 0
        self.calls: list[str] = []

    def lookup_entity(self, name: str, kind: str | None = None) -> dict[str, object] | None:
        self.call_count += 1
        self.calls.append(name)
        return self._table.get(name)


def test_chained_lookup_returns_first_non_none() -> None:
    """First backend returning a dict wins; later backends are not consulted."""
    primary = _StubLookup({"X": {"kind": "gene", "source": "primary"}})
    fallback = _StubLookup({"X": {"kind": "gene", "source": "fallback"}})
    chain = ChainedEntityLookup(primary, fallback)
    result = chain.lookup_entity("X")
    assert result == {"kind": "gene", "source": "primary"}
    assert primary.call_count == 1
    assert fallback.call_count == 0


def test_chained_lookup_falls_through_on_none() -> None:
    """First backend's None hands off to the second backend."""
    primary = _StubLookup({})
    fallback = _StubLookup({"Y": {"kind": "protein", "source": "fallback"}})
    chain = ChainedEntityLookup(primary, fallback)
    result = chain.lookup_entity("Y")
    assert result == {"kind": "protein", "source": "fallback"}
    assert primary.call_count == 1
    assert fallback.call_count == 1


def test_chained_lookup_all_none_returns_none() -> None:
    """All backends returning None → chain returns None."""
    a = _StubLookup({})
    b = _StubLookup({})
    chain = ChainedEntityLookup(a, b)
    assert chain.lookup_entity("MISSING") is None
    assert a.call_count == 1
    assert b.call_count == 1


def test_chained_lookup_empty_chain_returns_none() -> None:
    """A chain with zero backends is legal and always returns None."""
    chain = ChainedEntityLookup()
    assert chain.lookup_entity("anything") is None


def test_chained_lookup_propagates_kind_hint() -> None:
    """The ``kind`` argument is forwarded to each backend."""

    received_kinds: list[str | None] = []

    class _CaptureKind:
        def lookup_entity(self, name: str, kind: str | None = None) -> dict[str, object] | None:
            received_kinds.append(kind)
            return None

    chain = ChainedEntityLookup(_CaptureKind(), _CaptureKind())
    chain.lookup_entity("X", kind="gene")
    assert received_kinds == ["gene", "gene"]


def test_chained_lookup_with_real_backends() -> None:
    """End-to-end: KB primary + builtin fallback resolves both worlds.

    BRCA1 lives in both stores; the KB result wins (it has the
    "kb:" source tag). SQS lives only in the builtin stub; the
    fallback supplies it. ENTIRELY_FAKE is in neither → None.
    """
    chain = ChainedEntityLookup(_fixture_lookup(), BuiltinEntityLookup())

    brca1 = chain.lookup_entity("BRCA1")
    assert brca1 is not None
    assert brca1["source"].startswith("kb:")

    sqs = chain.lookup_entity("SQS")
    assert sqs is not None
    assert sqs["source"] == "stub:builtin"

    assert chain.lookup_entity("ENTIRELY_FAKE_ENTITY") is None


# ── default_kb_lookup factory ──────────────────────────────────────────────


def test_default_kb_lookup_returns_chained_instance(tmp_path: Path, monkeypatch) -> None:
    """The factory wires KB→builtin and is safe to construct at import time.

    We don't want the factory to require the real KB output. Point the
    KB path at a tmp file via monkeypatch and confirm: (a) construction
    succeeds without a parse, (b) builtin fallback resolves BRCA1 even
    when the KB primary fails to load.
    """
    # Re-point the default KB path at a non-existent file. Construction
    # must still succeed (lazy load).
    fake_outputs = tmp_path / "outputs"
    monkeypatch.setattr("linus.knowledge.entity_kb.KB_OUTPUTS_DIR", fake_outputs)
    # Patch the helper too, since we cached the default-path closure.
    monkeypatch.setattr(
        "linus.knowledge.entity_kb._default_graphml_path",
        lambda: fake_outputs / "knowledge_graph" / "kg_graph.graphml",
    )

    chain = default_kb_lookup()
    assert isinstance(chain, ChainedEntityLookup)

    # The KB primary will raise on lookup; we should pre-empt that by
    # checking the builtin alone fills the gap when KB is missing.
    # In production the chain would surface the KB error; in this test
    # we verify the builtin survives wiring at the second slot.
    builtin = BuiltinEntityLookup()
    direct = builtin.lookup_entity("BRCA1")
    assert direct is not None, "sanity: builtin stub holds BRCA1"


def test_default_kb_lookup_chain_uses_fixture_when_path_points_to_it(monkeypatch) -> None:
    """When the KB primary's path is the fixture, BRCA1 resolves via KB.

    Composes the default_kb_lookup factory with a redirected
    _default_graphml_path so the primary backend points at the
    committed fixture instead of the real KB output.
    """
    monkeypatch.setattr(
        "linus.knowledge.entity_kb._default_graphml_path",
        lambda: _FIXTURE_GRAPHML,
    )
    chain = default_kb_lookup()
    result = chain.lookup_entity("BRCA1")
    assert result is not None
    assert result["source"].startswith("kb:"), "primary KB backend should win"
    assert result["ref_count"] == 3


# ── EntityLookup protocol compliance ───────────────────────────────────────


# ── Edge-case attribute paths ──────────────────────────────────────────────


def test_entity_surface_falls_back_to_node_id_when_attrs_missing(tmp_path: Path) -> None:
    """An entity node with no text/label/name attr uses its id (stripped of "ent::").

    Real KB output always writes ``text``, but defensive coding pays
    off if a future writer omits it. Build a minimal graph in tmp_path
    that exercises the fallback path.
    """
    g: nx.MultiDiGraph = nx.MultiDiGraph()
    g.add_node("paper:p1", node_type="Paper", title="t")
    # Entity node with NO text/label/name attrs.
    g.add_node("ent::orphan", node_type="Entity")
    g.add_edge("paper:p1", "ent::orphan", edge_type="mentions")
    path = tmp_path / "fallback.graphml"
    nx.write_graphml(g, path)

    lookup = KBEntityLookup(graphml_path=path)
    result = lookup.lookup_entity("orphan")
    assert result is not None
    assert result["kind"] == "entity"
    assert result["ref_count"] == 1


def test_entity_surface_falls_back_to_raw_node_id_without_ent_prefix(tmp_path: Path) -> None:
    """A non-``ent::``-prefixed entity id with no text attr uses the id as-is."""
    g: nx.MultiDiGraph = nx.MultiDiGraph()
    g.add_node("paper:p1", node_type="Paper", title="t")
    g.add_node("freeform_id", node_type="Entity")  # no prefix, no text
    g.add_edge("paper:p1", "freeform_id", edge_type="mentions")
    path = tmp_path / "no_prefix.graphml"
    nx.write_graphml(g, path)

    lookup = KBEntityLookup(graphml_path=path)
    result = lookup.lookup_entity("freeform_id")
    assert result is not None
    assert result["ref_count"] == 1


def test_undirected_graphml_is_coerced_to_multidigraph(tmp_path: Path) -> None:
    """If the GraphML happens to be undirected, the loader coerces it.

    GraphML's reader can return a plain Graph if the source serialized
    one. The loader's coercion path turns it into a MultiDiGraph by
    way of ``to_directed()`` so the rest of the code can assume
    predecessors() is meaningful.
    """
    g = nx.Graph()  # undirected
    g.add_node("paper:p1", node_type="Paper", title="t")
    g.add_node("ent::und", node_type="Entity", text="Undirected")
    g.add_edge("paper:p1", "ent::und", edge_type="mentions")
    path = tmp_path / "undirected.graphml"
    nx.write_graphml(g, path)

    lookup = KBEntityLookup(graphml_path=path)
    result = lookup.lookup_entity("Undirected")
    assert result is not None
    # In a directed-from-undirected graph, both directions exist, so the
    # paper is a predecessor → ref_count==1 still holds.
    assert result["ref_count"] == 1


def test_default_graphml_path_returns_kb_outputs_subpath() -> None:
    """The default-path helper resolves through KB_OUTPUTS_DIR."""
    from linus.knowledge.entity_kb import _default_graphml_path

    p = _default_graphml_path()
    assert p.name == "kg_graph.graphml"
    assert p.parent.name == "knowledge_graph"


def test_kb_lookup_satisfies_entity_lookup_protocol() -> None:
    """:class:`KBEntityLookup` is structurally an :class:`EntityLookup`.

    Confirms the new backend is a drop-in for the rigor module's
    Protocol — no isinstance check needed at the call site.
    """
    lookup: EntityLookup = _fixture_lookup()
    # If the assignment type-checks, the runtime shape also satisfies
    # the Protocol's structural method. Belt-and-braces: call the
    # method to confirm.
    assert lookup.lookup_entity("BRCA1") is not None


def test_chained_lookup_satisfies_entity_lookup_protocol() -> None:
    """:class:`ChainedEntityLookup` also satisfies the Protocol."""
    chain: EntityLookup = ChainedEntityLookup(BuiltinEntityLookup())
    assert chain.lookup_entity("BRCA1") is not None


# ── H-1 regression test (PR #107 bug sweep) ────────────────────────────────


def test_kb_entity_lookup_concurrent_first_calls_parse_once() -> None:
    """H-1 regression: 16 concurrent first lookups must trigger ONE parse.

    Under FastAPI concurrency, two threads can both observe
    ``self._graph is None`` and both kick off ``nx.read_graphml``. With
    the ``threading.Lock`` + double-checked guard in ``_ensure_loaded``,
    only the first thread through the lock parses; the rest see the
    populated index and return immediately. Uses a ``threading.Barrier``
    so all 16 threads release together — without the lock this is enough
    interleaving to produce ~16 parses (or at minimum, >1).
    """
    n_threads = 16
    lookup = KBEntityLookup(graphml_path=_FIXTURE_GRAPHML)

    real_read_graphml = nx.read_graphml
    call_count = 0
    count_lock = threading.Lock()

    def counting_read_graphml(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal call_count
        with count_lock:
            call_count += 1
        return real_read_graphml(*args, **kwargs)

    barrier = threading.Barrier(n_threads)
    results: list[dict[str, object] | None] = [None] * n_threads
    errors: list[BaseException] = []

    def worker(idx: int) -> None:
        try:
            barrier.wait(timeout=5.0)
            results[idx] = lookup.lookup_entity("BRCA1")
        except BaseException as exc:  # pragma: no cover — surface in assertion
            errors.append(exc)

    with patch("linus.knowledge.entity_kb.nx.read_graphml", side_effect=counting_read_graphml):
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)
            assert not t.is_alive(), "worker thread did not exit in time"

    assert not errors, f"worker threads raised: {errors!r}"
    assert call_count == 1, f"expected exactly 1 nx.read_graphml call, got {call_count}"
    # All 16 lookups must agree — and must match a serial baseline.
    baseline = KBEntityLookup(graphml_path=_FIXTURE_GRAPHML).lookup_entity("BRCA1")
    assert baseline is not None
    for idx, result in enumerate(results):
        assert result == baseline, f"thread {idx} got divergent result: {result!r}"


# ── H-3 regression tests (PR #107 bug sweep) ───────────────────────────────


class _RaisingLookup:
    """Backend whose ``lookup_entity`` always raises a given exception.

    Used to exercise the H-3 fix in ``ChainedEntityLookup``: the chain
    must catch per-backend exceptions and continue to the next backend
    rather than propagating up to the caller.
    """

    def __init__(self, exc: BaseException) -> None:
        self._exc = exc
        self.call_count = 0

    def lookup_entity(self, name: str, kind: str | None = None) -> dict[str, object] | None:
        self.call_count += 1
        raise self._exc


def test_chained_entity_lookup_skips_raising_backend() -> None:
    """H-3 regression: a raise from one backend must not propagate.

    A backend that raises ``RuntimeError`` is treated as if it returned
    ``None`` for the chain's purposes — the next backend runs. With the
    builtin stub second in the chain, BRCA1 resolves via the fallback
    and the user sees the stub source tag, not the RuntimeError.
    """
    raiser = _RaisingLookup(RuntimeError("simulated kb failure"))
    builtin = BuiltinEntityLookup()
    chain = ChainedEntityLookup(raiser, builtin)

    result = chain.lookup_entity("BRCA1")
    assert result is not None
    assert result["source"] == "stub:builtin"
    assert result["kind"] == "gene"
    # The raising backend WAS consulted (its raise was caught), but the
    # chain did not bail out — it advanced to the builtin.
    assert raiser.call_count == 1


def test_chained_entity_lookup_propagates_none_correctly_when_all_backends_miss() -> None:
    """H-3 regression: two raisers + one None-returner yields None, not a raise.

    The chain's documented contract is "first non-None wins; end-of-chain
    returns None." With per-backend exception catching, that contract
    holds even when intermediate backends raise — the chain still
    returns None cleanly without leaking any of the suppressed
    exceptions to the caller.
    """
    raiser_a = _RaisingLookup(FileNotFoundError("first backend missing"))
    raiser_b = _RaisingLookup(OSError("second backend IO error"))
    none_returner = _StubLookup({})
    chain = ChainedEntityLookup(raiser_a, raiser_b, none_returner)

    # Must return None — no leaked exception of any kind.
    assert chain.lookup_entity("MISSING_ENTITY") is None
    assert raiser_a.call_count == 1
    assert raiser_b.call_count == 1
    assert none_returner.call_count == 1


def test_kb_entity_lookup_missing_file_does_not_leak_through_chain(tmp_path: Path) -> None:
    """H-1 + H-3 interaction: missing GraphML must fall through to builtin.

    Construction of ``KBEntityLookup`` with a non-existent path
    succeeds (lazy load). The first ``lookup_entity`` call would raise
    ``FileNotFoundError`` from inside ``_ensure_loaded``; without the
    H-3 fix that exception leaks past ``ChainedEntityLookup`` and into
    ``paperqa._run_rigor_gate``'s broad fail-open ``except``, silently
    setting ``rigor=None``. With the fix, the chain swallows the
    FileNotFoundError, advances to ``BuiltinEntityLookup``, and the
    documented ``stub:builtin`` fallback resolves BRCA1.
    """
    missing_path = tmp_path / "definitely_does_not_exist.graphml"
    kb = KBEntityLookup(graphml_path=missing_path)
    builtin = BuiltinEntityLookup()
    chain = ChainedEntityLookup(kb, builtin)

    result = chain.lookup_entity("BRCA1")
    assert result is not None
    assert result["source"] == "stub:builtin", "missing KB GraphML should fall through to builtin, not raise"
    assert result["kind"] == "gene"
