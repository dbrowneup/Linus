"""KB-derived entity lookup for the rigor gate.

Loads entity vertices from KnowledgeBase's REBEL+SciSpacy KG output
(``kg_graph.graphml``) and exposes them as an :class:`EntityLookup`
implementation per the protocol in :mod:`linus.knowledge.rigor`.

Entities are "grounded" iff they appear as vertices in Dan's actual
reading corpus — not in a hand-enumerated table, not in an external
reference DB. Real entities, derived from real papers, validated
against synthesis output.

This module is the v0.5.0 replacement for the hand-seeded
:class:`linus.knowledge.rigor.BuiltinEntityLookup` stub. Dan's strategic
call on 2026-05-19 pulled it forward from v0.6.0: with KB Phase 6
already shipping REBEL+SciSpacy KG outputs, the "entities and concepts
emerge naturally from the text" promise becomes load-bearing in the
rigor gate as soon as we point it at the real graph. The stub doesn't
go away — :class:`ChainedEntityLookup` composes the KB backend with the
builtin so well-known anchors (BRCA1, TP53, …) still resolve even if
they happen not to appear in Dan's corpus snapshot.

Design notes
------------

- **Lazy load.** Construction is cheap (store path + flags); the
  expensive ``networkx.read_graphml`` call runs on first
  :meth:`KBEntityLookup.lookup_entity`. The parsed graph and the
  derived name → metadata index are cached in memory for the
  process's lifetime.

- **Trust the OS page cache.** The KG file is mmap'd by NetworkX's
  parser; we do not layer additional caching over the file itself
  (DEC-0027 / "Trust the OS page cache" convention). Only the post-
  parse Python dict index is held in memory.

- **Node disambiguation.** The KB writes entity nodes with
  ``node_type="Entity"`` and paper nodes with ``node_type="Paper"``
  (see ``modules/KnowledgeBase/papers_analysis/knowledge_graph.py``).
  :mod:`linus.app.kg_render` accepts either ``node_type`` or ``type``
  for forward-compat with hand-built test fixtures; we match the same
  fallback so a fixture written either way is recognized.

- **Entity surface form.** KB stores the original casing in the
  ``text`` attribute and the lower-cased version inside the node id
  (``ent::<lowered>``). We index by the case-folded ``text`` (when
  ``case_insensitive=True``, the default and recommended setting) so
  callers can pass any casing and still hit.

- **ref_count = number of distinct paper neighbors.** A SciSpacy
  ``mentions`` edge runs Paper → Entity; the entity's in-edges from
  paper-typed predecessors count the distinct papers it appears in.
  This is the "well-established in Dan's corpus" signal called out in
  the spec. A ref_count of 1 is a single-paper entity (low
  confidence); high ref_count is a corpus-wide anchor.

See also
--------

- ``docs/specs/2026-05-19-v0.5.0-implementation-plan.md`` for the
  v0.5.0 scope decision pulling this in.
- :mod:`linus.knowledge.rigor` for the consumer Protocol and the
  builtin stub that this composes with.
- :mod:`linus.app.kg_render` for the canonical pattern of loading
  the same GraphML file (used by the Streamlit KG page).
"""

from __future__ import annotations

import hashlib
import logging
import threading
from pathlib import Path
from typing import Any

import networkx as nx

from linus.app.config import KB_OUTPUTS_DIR
from linus.knowledge.rigor import BuiltinEntityLookup, EntityLookup

logger = logging.getLogger(__name__)

__all__ = [
    "ChainedEntityLookup",
    "KBEntityLookup",
    "default_kb_lookup",
]


def _default_graphml_path() -> Path:
    """Default location of the KB knowledge-graph GraphML output."""
    return KB_OUTPUTS_DIR / "knowledge_graph" / "kg_graph.graphml"


def _node_type(data: dict[str, Any]) -> str:
    """Return the lower-cased node type from either canonical attribute.

    The KB writer (``papers_analysis.knowledge_graph._build_graph``)
    uses ``node_type``; the kg_render test fixtures use ``type``. We
    accept both so a fixture written in either style is recognized.
    """
    return str(data.get("node_type") or data.get("type") or "").lower()


def _entity_surface(node_id: str, data: dict[str, Any]) -> str:
    """Pull the human-readable surface form for an entity node.

    KB stores the original-casing text under the ``text`` attribute.
    Some fixtures use ``label`` or ``name`` for the same purpose; fall
    back through those, then the node id itself (minus the ``ent::``
    prefix the KB uses for entity ids).
    """
    text = data.get("text") or data.get("label") or data.get("name")
    if text:
        return str(text)
    if isinstance(node_id, str) and node_id.startswith("ent::"):
        return node_id[5:]
    return str(node_id)


def _entity_kind(data: dict[str, Any]) -> str:
    """Best-effort NER category for an entity node.

    KB writes the SciSpacy NER label under ``label``; the kg_render
    fixture uses ``entity_type``. ``"entity"`` is the fallback so the
    returned ``kind`` is always a non-empty string the caller can log.
    """
    return str(data.get("label") or data.get("entity_type") or "entity")


def _short_sha(path: Path, length: int = 12) -> str:
    """Short content hash of a GraphML file for the ``source`` field.

    Used in the metadata dict's ``source: "kb:<sha>"`` so callers can
    tell which KG snapshot resolved an entity. The hash is read-lazy
    (only when :meth:`KBEntityLookup.lookup_entity` first runs); we
    pay the file scan once per process.
    """
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:length]


class KBEntityLookup:
    """EntityLookup backed by KB's ``knowledge_graph/kg_graph.graphml``.

    Construction is cheap — only the path and flags are stored. The
    GraphML parse + index build run on first :meth:`lookup_entity`
    call and the parsed graph is cached on the instance thereafter.

    Parameters
    ----------
    graphml_path
        Path to the GraphML file. Defaults to
        ``KB_OUTPUTS_DIR / 'knowledge_graph' / 'kg_graph.graphml'``
        per :mod:`linus.app.config` (overridable via the
        ``LINUS_KB_OUTPUTS_DIR`` env var).
    case_insensitive
        When ``True`` (default), entity surface forms are case-folded
        at index-build time so lookups like ``"BRCA1"`` and ``"brca1"``
        both resolve. The KG stores SciSpacy's emitted surface forms
        as-is, which can be inconsistently cased; case folding is the
        right default.

    Notes
    -----
    A missing GraphML file raises :class:`FileNotFoundError` from
    :meth:`lookup_entity` (not from ``__init__``, so callers can wire
    the lookup at import time and only pay the file check on first
    use). The error message includes the resolved path, the
    controlling env var, and the KB regen command.
    """

    def __init__(
        self,
        graphml_path: Path | None = None,
        case_insensitive: bool = True,
    ) -> None:
        self._graphml_path: Path = graphml_path if graphml_path is not None else _default_graphml_path()
        self._case_insensitive: bool = case_insensitive
        # Lazily populated on first lookup.
        self._graph: nx.MultiDiGraph | None = None
        self._index: dict[str, dict[str, Any]] | None = None
        self._source_tag: str | None = None
        # H-1 (#107): serialize lazy-parse so concurrent first calls do not
        # both invoke ``nx.read_graphml`` (expensive, briefly inconsistent
        # in-memory state). Double-checked locking — the fast path stays
        # lock-free once the index is populated.
        self._load_lock: threading.Lock = threading.Lock()

    # ── lazy load helpers ──────────────────────────────────────────────────

    def _ensure_loaded(self) -> None:
        """Parse the GraphML and build the name → metadata index once.

        H-1 (#107): double-checked locking. The first check is the
        unsynchronized fast path; if the index is already populated, we
        return without touching the lock. If not, we acquire ``_load_lock``
        and re-check under the lock so a thread that lost the race to a
        peer's parse observes the populated index instead of redoing the
        work. This keeps steady-state lookups lock-free while preventing
        two concurrent first calls from both invoking ``nx.read_graphml``.
        """
        if self._index is not None:
            return

        with self._load_lock:
            if self._index is not None:  # double-checked
                return

            if not self._graphml_path.exists():
                raise FileNotFoundError(
                    f"KB knowledge-graph file not found at {self._graphml_path!s}. "
                    "This path is controlled by the LINUS_KB_OUTPUTS_DIR env var "
                    "(default: modules/KnowledgeBase/data/outputs). To regenerate "
                    "the file, run from the KnowledgeBase submodule:\n"
                    "    cd modules/KnowledgeBase\n"
                    "    python -m papers_analysis.knowledge_graph"
                )

            g = nx.read_graphml(self._graphml_path)
            # Coerce to MultiDiGraph for consistent edge iteration (matches
            # kg_render.load_kg's behavior — the KB writes a MultiDiGraph but
            # NetworkX's GraphML reader may downcast in some versions).
            if not isinstance(g, nx.MultiDiGraph):
                g = nx.MultiDiGraph(g) if g.is_directed() else nx.MultiDiGraph(g.to_directed())

            # First pass: pick out entity nodes and their surface forms.
            entity_nodes: list[tuple[str, dict[str, Any]]] = []
            for node_id, data in g.nodes(data=True):
                if _node_type(data) == "entity":
                    entity_nodes.append((str(node_id), data))

            # Second pass: compute ref_count per entity (= count of distinct
            # paper-typed predecessors, i.e. papers that mention the entity
            # via a Paper → Entity edge). MultiDiGraph may have multiple
            # parallel mentions edges between the same paper and entity;
            # we count *distinct* papers.
            source_tag = "kb:" + _short_sha(self._graphml_path)
            index: dict[str, dict[str, Any]] = {}
            for node_id, data in entity_nodes:
                surface = _entity_surface(node_id, data)
                key = surface.casefold() if self._case_insensitive else surface

                paper_neighbors: set[str] = set()
                for predecessor in g.predecessors(node_id):
                    pred_data = g.nodes[predecessor]
                    if _node_type(pred_data) == "paper":
                        paper_neighbors.add(str(predecessor))

                metadata: dict[str, Any] = {
                    "kind": _entity_kind(data),
                    "source": source_tag,
                    "ref_count": len(paper_neighbors),
                }
                # If two entity nodes collapse to the same case-folded key
                # (KB's id-construction already lowercases, so this is
                # unlikely in practice but cheap to guard against), keep the
                # one with the higher ref_count — it's the better anchor.
                existing = index.get(key)
                if existing is None or metadata["ref_count"] > existing["ref_count"]:
                    index[key] = metadata

            # Publish the parsed state in a final order: ``_index`` last so
            # the unsynchronized fast-path check above is the load-bearing
            # publication signal. Any thread that sees ``_index is not None``
            # is guaranteed to see the matching ``_graph`` / ``_source_tag``
            # because they were assigned first under the same lock.
            self._graph = g
            self._source_tag = source_tag
            self._index = index

    # ── EntityLookup protocol ──────────────────────────────────────────────

    def lookup_entity(self, name: str, kind: str | None = None) -> dict[str, Any] | None:
        """Return entity metadata if ``name`` is in the loaded KG, else ``None``.

        The returned dict has shape
        ``{"kind": str, "source": "kb:<sha-of-graphml>", "ref_count": int}``.
        ``kind`` is the SciSpacy NER label (or ``"entity"`` when the
        node didn't carry one); ``source`` identifies the KG snapshot
        the answer came from; ``ref_count`` is the number of distinct
        papers that mention this entity (high = corpus-anchored, 1 =
        single-paper appearance).

        ``kind`` is an optional hint from the caller (the
        :class:`EntityLookup` Protocol allows it); this backend
        currently ignores it — the surface-form match is the only key.
        Future backends may use it to disambiguate homographs.
        """
        if not name:
            return None
        self._ensure_loaded()
        assert self._index is not None  # set by _ensure_loaded
        key = name.casefold() if self._case_insensitive else name
        return self._index.get(key)


class ChainedEntityLookup:
    """Composite :class:`EntityLookup` that tries N backends in order.

    Chain-of-responsibility: each backend's :meth:`lookup_entity` is
    called in turn; the first non-``None`` result wins. When every
    backend returns ``None``, the chain returns ``None``.

    The intended composition (see :func:`default_kb_lookup`) is
    ``ChainedEntityLookup(KBEntityLookup(), BuiltinEntityLookup())``:
    KB-derived entities (real, from Dan's corpus) take precedence, and
    the hand-seeded stub catches well-known anchors that happen not to
    appear in the current corpus snapshot. Empty chains are legal and
    always return ``None``.
    """

    def __init__(self, *backends: EntityLookup) -> None:
        self._backends: tuple[EntityLookup, ...] = backends

    def lookup_entity(self, name: str, kind: str | None = None) -> dict[str, Any] | None:
        """Return the first non-``None`` lookup result across backends.

        H-3 (#107): per-backend exceptions are caught and treated as a
        ``None`` result for that backend, then the chain continues to the
        next backend. The chain's job is "try each entity backend in
        order until one resolves the name"; a raise from one backend
        (e.g. ``KBEntityLookup`` hitting a missing GraphML file at first
        lookup) MUST NOT short-circuit that contract. Without this catch
        a missing KG file leaks ``FileNotFoundError`` past the chain into
        ``paperqa._run_rigor_gate``'s broad fail-open ``except``, which
        silently sets ``rigor=None`` — the user loses the documented
        ``stub:builtin`` fallback that the chain was specifically
        designed to provide.

        Failures are logged at debug level so operators can correlate a
        silent-skip event with backend health, but they are NOT
        propagated. The blanket ``except Exception`` is deliberate: any
        per-backend failure (file IO, NetworkX parse error, network blip
        in a future remote backend, ...) is treated the same way as a
        clean ``None`` return, since the contract the consumer relies on
        is "the chain returns the first resolved entity or None at end
        of chain."
        """
        for backend in self._backends:
            try:
                result = backend.lookup_entity(name, kind=kind)
            except Exception as exc:  # chain must not propagate; see docstring.
                logger.debug(
                    "ChainedEntityLookup: backend %s raised %s; skipping to next",
                    type(backend).__name__,
                    type(exc).__name__,
                )
                continue
            if result is not None:
                return result
        return None


def default_kb_lookup() -> EntityLookup:
    """Return the production-default chained entity lookup.

    Composes :class:`KBEntityLookup` (primary) with
    :class:`BuiltinEntityLookup` (fallback). The KB backend is
    constructed lazily — no file parse happens until the first
    :meth:`lookup_entity` call — so this is safe to call at module
    import time. Callers wiring rigor checks should prefer this
    factory over instantiating either backend directly.
    """
    return ChainedEntityLookup(KBEntityLookup(), BuiltinEntityLookup())
