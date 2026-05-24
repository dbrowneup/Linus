"""paper-qa Phase 2c integration — :mod:`linus.knowledge.paperqa`.

Wraps FutureHouse's `paper-qa <https://github.com/Future-House/paper-qa>`_
(Apache 2.0) as the citation-grounded paper-corpus question-answering surface
for Linus. Exposes four Linus-registered tools that mirror paper-qa's four
core orchestration primitives:

- ``paperqa.search`` — index PDFs in a paper directory and surface matching
  text chunks (analogue of paper-qa's :class:`PaperSearch`).
- ``paperqa.gather_evidence`` — re-rank passages with the configured Worker
  LLM via paper-qa's :meth:`Docs.aget_evidence` (analogue of
  :class:`GatherEvidence`).
- ``paperqa.answer`` — synthesize a citation-grounded answer via
  :meth:`Docs.aquery` (analogue of :class:`GenerateAnswer`).
- ``paperqa.reset`` — clear the in-process session state (analogue of
  :class:`Reset`).

All LLM I/O routes through paper-qa's LiteLLM adapter pointed at local
Ollama (``http://localhost:11434``); no hosted API key is required. The
default model is ``qwen3:8b`` — empirically validated as the Phase 1e/2c
Worker on the 32 GB M1 Max per CLAUDE.md. The spec's :ref:`Worker floor`
note recommends Qwen3-14B for production paper-qa synthesis; on this
hardware, ``qwen3:8b`` is the available Worker. Override via the
``LINUS_PAPERQA_MODEL`` environment variable when a 14B fits the box.

Citation grounding
------------------

paper-qa returns a :class:`paperqa.PQASession` with a ``contexts`` list of
:class:`paperqa.Context` objects, each linking to a :class:`paperqa.Text`
chunk and its source :class:`paperqa.Doc`. The
:func:`citation_to_provenance` helper flattens those into Linus's KB
provenance shape (DEC-0023): ``{"paper_id", "page", "excerpt", "score"}``.

Lazy singleton lifecycle
------------------------

The module-level :data:`_singleton` is created on first tool call so that
``import linus.knowledge.paperqa`` (run at registry-import time) does not
attempt to talk to Ollama or read the paper directory. Tests can clear the
singleton with :func:`reset_singleton`.

Graceful degradation
--------------------

paper-qa itself is an optional Linus dependency in practice — the hermetic
test suite must run without it installed. Import is therefore deferred until
the first call into a tool method. Missing paper-qa surfaces as
:class:`PaperQAUnavailableError`, which the registry translates into a
structured ``role=tool`` error message.

See ``docs/specs/kb/paper-qa-substrate-integration.md`` for the design
contract and ``docs/specs/2026-05-19-kb-hackathon-prep.md`` §LX-1 for the
hackathon-prep framing this module ships against.
"""

from __future__ import annotations

import contextlib
import logging
import os
from pathlib import Path
from typing import Any

from linus.tools.registry import tool

logger = logging.getLogger(__name__)

# ── public exception types ────────────────────────────────────────────────


class PaperQAUnavailableError(RuntimeError):
    """Raised when paper-qa is required but not importable.

    paper-qa is an optional dependency. When a tool is called and paper-qa
    is not installed in the active interpreter, this is raised with the
    remediation hint ``pip install 'paper-qa>=5.0'``.
    """


class PaperQAConfigError(RuntimeError):
    """Raised when the configured paper directory is missing or invalid.

    Distinct from :class:`PaperQAUnavailableError` because the remediation
    is different — the user needs to create or point at a paper directory,
    not install a package.
    """


# ── configuration ─────────────────────────────────────────────────────────

#: Default Ollama HTTP base URL. paper-qa's LiteLLM adapter routes here
#: when the model name is prefixed ``ollama/``. Overridable via the
#: ``OLLAMA_HOST`` environment variable for hosts running Ollama on a
#: non-default port.
DEFAULT_OLLAMA_HOST: str = "http://localhost:11434"

#: Default Worker model. ``qwen3:8b`` is the empirically validated Phase
#: 1e/2c Worker on the project's 32 GB M1 Max (CLAUDE.md). Override via
#: ``LINUS_PAPERQA_MODEL``. The spec recommends Qwen3-14B; we ship the
#: smaller default on this hardware.
DEFAULT_MODEL: str = "qwen3:8b"

#: Default embedding model. mxbai-embed-large is Ollama's recommended
#: long-context embedding model; runs locally with no API key.
DEFAULT_EMBEDDING_MODEL: str = "ollama/mxbai-embed-large"


def _papers_dir() -> Path:
    """Return the configured paper directory, auto-creating it if missing.

    Resolution order (delegated to :func:`linus.app.config.paperqa_dir_path`):

    1. ``LINUS_PAPERQA_DIR`` environment variable, if set.
    2. ``LINUS_PAPERS_DIR`` environment variable, if set (shared with
       :mod:`linus.tools.arxiv_ingest`).
    3. Default ``~/.linus/papers/``.

    The directory is **auto-created** with a README on first access via
    :func:`linus.app.config.resolve_paperqa_dir` — this is the durable
    fix for the 2026-05-22 reveal-prep bug 4 (fresh machines used to
    surface ``PaperQAConfigError`` because ``~/.linus/papers`` did not
    exist). A non-directory at the resolved path still surfaces as
    :class:`PaperQAConfigError` from :meth:`LinusPaperQA._ensure_loaded`.

    The resolver is best-effort: on filesystem failures (permission
    denied, read-only filesystem) the path is returned unchanged and
    :meth:`LinusPaperQA._ensure_loaded` will raise
    :class:`PaperQAConfigError` per the existing contract.
    """
    # Local import to keep this module importable in test environments
    # that don't ship the full app surface.
    from linus.app.config import resolve_paperqa_dir

    return resolve_paperqa_dir()


def _ollama_host() -> str:
    """Return the Ollama HTTP base URL (overridable via ``OLLAMA_HOST``)."""
    return os.environ.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)


def _model_name() -> str:
    """Return the Ollama model name (overridable via ``LINUS_PAPERQA_MODEL``)."""
    return os.environ.get("LINUS_PAPERQA_MODEL", DEFAULT_MODEL)


def _embedding_model_name() -> str:
    """Return the Ollama embedding model name (overridable via ``LINUS_PAPERQA_EMBEDDING``)."""
    return os.environ.get("LINUS_PAPERQA_EMBEDDING", DEFAULT_EMBEDDING_MODEL)


def build_ollama_llm_config(model: str | None = None, host: str | None = None) -> dict[str, Any]:
    """Build paper-qa's LiteLLM Router config dict pointed at local Ollama.

    The shape matches paper-qa's README §"Models hosted with ollama" example.
    Returned value is suitable for both the ``llm_config`` and
    ``summary_llm_config`` fields of :class:`paperqa.Settings`.

    Parameters
    ----------
    model:
        Ollama model name (without the ``ollama/`` prefix). Defaults to
        :data:`DEFAULT_MODEL` / ``LINUS_PAPERQA_MODEL``.
    host:
        Ollama HTTP base URL. Defaults to :data:`DEFAULT_OLLAMA_HOST` /
        ``OLLAMA_HOST``.
    """
    resolved_model = f"ollama/{model or _model_name()}"
    resolved_host = host or _ollama_host()
    return {
        "model_list": [
            {
                "model_name": resolved_model,
                "litellm_params": {
                    "model": resolved_model,
                    "api_base": resolved_host,
                },
            }
        ]
    }


# ── citation → provenance mapping ─────────────────────────────────────────


def citation_to_provenance(context: Any) -> dict[str, Any]:
    """Map a paper-qa :class:`Context`-like object to Linus's KB provenance shape.

    The Linus provenance contract (DEC-0023) is::

        {"paper_id": str, "page": int | None, "excerpt": str, "score": float}

    paper-qa's :class:`Context` carries:

    - ``text`` — a :class:`Text` whose ``doc`` carries ``dockey`` (the
      paper id) and (when present) a chunk ``name`` like ``"<docname>
      pages 3-4"``.
    - ``context`` — the contextual summary of the chunk for the question.
    - ``score`` — relevance score (0-10, or -1 = unset).

    This helper is robust to duck-typed inputs so test fixtures can supply
    plain Mock objects with the same attribute names. The returned dict
    always carries all four keys; missing fields default to ``None``
    (paper_id / page), empty string (excerpt), or 0.0 (score).
    """
    paper_id: str | None = None
    page: int | None = None
    excerpt: str = ""
    score: float = 0.0

    text_obj = getattr(context, "text", None)
    if text_obj is not None:
        # Prefer the doc.dockey as the canonical paper id, since dockey is a
        # SHA-style content hash that aligns with the KB's paper.sha256.
        doc_obj = getattr(text_obj, "doc", None)
        if doc_obj is not None:
            dockey = getattr(doc_obj, "dockey", None)
            if dockey is not None:
                paper_id = str(dockey)
            else:
                # Fall back to docname for human-readable Doc objects.
                docname = getattr(doc_obj, "docname", None)
                if docname is not None:
                    paper_id = str(docname)

        # Best-effort page extraction from the chunk name. paper-qa's
        # chunker emits names like ``"Smith2024 pages 3-4"``; the chunk
        # ``name`` is the most reliable carrier we have.
        chunk_name = getattr(text_obj, "name", None)
        if chunk_name:
            page = _parse_first_page(chunk_name)

        # The raw text chunk is the excerpt the model actually saw.
        raw_text = getattr(text_obj, "text", None)
        if raw_text:
            excerpt = str(raw_text)

    # Prefer the context's contextual summary as the excerpt when present
    # — it's question-conditioned and tends to be more informative than
    # the raw chunk for downstream provenance display.
    summary = getattr(context, "context", None)
    if summary:
        excerpt = str(summary)

    raw_score = getattr(context, "score", None)
    if raw_score is not None:
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            score = 0.0
        # paper-qa uses -1 as 'unset'; normalize to 0.0 for downstream.
        if score < 0:
            score = 0.0

    return {
        "paper_id": paper_id,
        "page": page,
        "excerpt": excerpt,
        "score": score,
    }


def _parse_first_page(chunk_name: str) -> int | None:
    """Extract the first page integer from a chunk name like ``"Smith2024 pages 3-4"``.

    Returns ``None`` if no page-range substring is present. Robust to
    variants like ``"pages 3"``, ``"page 3"``, ``"p. 3"``; falls back to
    ``None`` if nothing parses.
    """
    import re

    # Match 'page' / 'pages' / 'p.' followed by an integer.
    match = re.search(r"(?:pages?|p\.)\s*(\d+)", chunk_name, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


# ── LinusPaperQA wrapper ──────────────────────────────────────────────────


class LinusPaperQA:
    """Lazy facade over paper-qa's :class:`Docs` and :class:`Settings`.

    Constructed once per process via :func:`get_singleton`. paper-qa is
    imported lazily inside :meth:`_ensure_loaded` so import-time cost is
    not paid until a tool is actually called, and so the hermetic test
    suite can run without paper-qa installed.

    State held:

    - :attr:`docs` — paper-qa's :class:`Docs` collection (rebuilt on
      :meth:`reset`).
    - :attr:`settings` — paper-qa's :class:`Settings`, configured for
      local Ollama on construction.
    - :attr:`papers_dir` — the resolved paper directory path.
    """

    def __init__(self, papers_dir: Path | None = None) -> None:
        """Construct the facade. Does NOT import paper-qa or hit Ollama."""
        self.papers_dir: Path = papers_dir if papers_dir is not None else _papers_dir()
        self._docs: Any = None
        self._settings: Any = None
        self._loaded: bool = False

    # --- lazy paper-qa import ---------------------------------------------

    def _ensure_loaded(self) -> None:
        """Import paper-qa and instantiate :class:`Docs` + :class:`Settings`.

        Called from every public method. After the first call, this is a
        no-op (the ``_loaded`` flag short-circuits). On import failure,
        raises :class:`PaperQAUnavailableError` with an install hint; on
        missing paper directory, raises :class:`PaperQAConfigError`.
        """
        if self._loaded:
            return

        try:
            from paperqa import Docs, Settings  # type: ignore[import-not-found]
        except ImportError as exc:
            raise PaperQAUnavailableError("paper-qa is not installed. Run: pip install 'paper-qa>=5.0'") from exc

        # Missing-dir is no longer a hard error: callers acquire the
        # papers directory through :func:`_papers_dir` which delegates to
        # :func:`linus.app.config.resolve_paperqa_dir` and auto-creates
        # ``~/.linus/papers`` on first access (2026-05-22 reveal-prep
        # bug 4). Tests construct :class:`LinusPaperQA` with an explicit
        # ``papers_dir`` though, so still guard against the case where
        # the caller hands us a path that does not exist or is not a
        # directory.
        if not self.papers_dir.exists():
            raise PaperQAConfigError(
                f"paper-qa papers directory does not exist: {self.papers_dir}. "
                "Create it and add PDFs, or set LINUS_PAPERQA_DIR to an existing directory."
            )
        if not self.papers_dir.is_dir():
            raise PaperQAConfigError(
                f"paper-qa papers path exists but is not a directory: {self.papers_dir}. "
                "Set LINUS_PAPERQA_DIR to a directory (a file or symlink-to-file is rejected)."
            )

        llm_config = build_ollama_llm_config()
        model = f"ollama/{_model_name()}"
        self._settings = Settings(
            llm=model,
            llm_config=llm_config,
            summary_llm=model,
            summary_llm_config=llm_config,
            embedding=_embedding_model_name(),
        )
        # Point paper-qa's agent index at our papers directory. Older
        # paper-qa versions may surface a different settings tree; if the
        # attribute layout differs, defer to whatever the default
        # Settings provides — the spec drift is flagged in the PR description.
        with contextlib.suppress(AttributeError):
            self._settings.agent.index.paper_directory = str(self.papers_dir)

        self._docs = Docs()
        self._loaded = True

    # --- public surface ----------------------------------------------------

    async def search(self, query: str, k: int = 10) -> list[dict[str, Any]]:
        """Search the indexed paper corpus for ``query`` and return up to ``k`` chunks.

        Backed by paper-qa's :meth:`Docs.aget_evidence`, which performs
        the same embedding-based retrieval that :class:`PaperSearch` /
        :class:`GatherEvidence` use internally. Returns up to ``k``
        provenance dicts ordered by descending relevance score.

        For a freshly-initialized :class:`Docs` (no PDFs yet added), the
        :meth:`Docs.aadd` path against :attr:`papers_dir` would be the
        natural ingest step; that's a Phase 2c follow-up wired through
        ``paperqa.ingest`` (not part of LX-1). For now this surface
        assumes the corpus is already populated.
        """
        if k < 1:
            raise ValueError(f"k must be >= 1, got {k}")
        self._ensure_loaded()

        from paperqa import PQASession  # type: ignore[import-not-found]

        session = PQASession(question=query)
        # aget_evidence returns the session with .contexts populated.
        session = await self._docs.aget_evidence(query=session, settings=self._settings)
        contexts = list(session.contexts)[:k]
        return [citation_to_provenance(c) for c in contexts]

    async def gather_evidence(self, query: str, candidate_paper_ids: list[str] | None = None) -> list[dict[str, Any]]:
        """Re-rank evidence chunks for ``query`` via the configured Worker LLM.

        Calls :meth:`Docs.aget_evidence`, which retrieves matching chunks
        and re-ranks them with the summary LLM. The
        ``candidate_paper_ids`` argument is currently advisory — paper-qa
        does not expose a per-paper filter at this entry point — but it
        is preserved in the API surface for future use when paper-qa
        adds the filter (or when Linus's KB gateway routes pre-filtered
        contexts).
        """
        self._ensure_loaded()

        from paperqa import PQASession  # type: ignore[import-not-found]

        session = PQASession(question=query)
        session = await self._docs.aget_evidence(query=session, settings=self._settings)
        contexts = list(session.contexts)

        # Soft filter by candidate_paper_ids if supplied.
        if candidate_paper_ids:
            allowed = set(candidate_paper_ids)
            contexts = [c for c in contexts if _context_paper_id(c) in allowed]

        return [citation_to_provenance(c) for c in contexts]

    async def answer(self, query: str, max_sources: int = 10) -> dict[str, Any]:
        """Synthesize a citation-grounded answer to ``query``.

        Backed by :meth:`Docs.aquery`. Returns a dict with:

        - ``answer`` — the synthesized natural-language answer.
        - ``citations`` — list of provenance dicts (max ``max_sources``).
        - ``question`` — the original query echoed back.
        - ``formatted_answer`` — paper-qa's pretty-printed answer with
          inline citations.
        - ``rigor`` — the structured rigor-gate result (see
          :func:`linus.knowledge.rigor.check_grounding`). May be ``None``
          if the gate raised internally; the answer call itself never
          fails because of the gate.
        """
        if max_sources < 1:
            raise ValueError(f"max_sources must be >= 1, got {max_sources}")
        self._ensure_loaded()

        from paperqa import PQASession  # type: ignore[import-not-found]

        session = PQASession(question=query)
        session = await self._docs.aquery(query=session, settings=self._settings)

        contexts = list(session.contexts)[:max_sources]
        citations = [citation_to_provenance(c) for c in contexts]
        payload: dict[str, Any] = {
            "question": session.question,
            "answer": session.answer,
            "formatted_answer": session.formatted_answer,
            "citations": citations,
        }
        payload["rigor"] = _run_rigor_gate(
            answer_text=session.answer,
            citations=citations,
            confidence=getattr(session, "confidence", None),
        )
        return payload

    async def reset(self) -> dict[str, str]:
        """Clear the in-process :class:`Docs` collection.

        After a reset the next call to :meth:`search` / :meth:`answer`
        will see an empty index — until the corpus is re-ingested (Phase
        2c follow-up). Returns a small status dict so the tool layer can
        echo confirmation to the caller.
        """
        if not self._loaded:
            # Reset on an un-loaded facade is a no-op; surface the fact
            # honestly rather than triggering a lazy load.
            return {"status": "reset", "detail": "no-op (facade not yet loaded)"}

        self._docs.clear_docs()
        return {"status": "reset", "detail": "docs collection cleared"}


def _context_paper_id(context: Any) -> str | None:
    """Pluck the paper id from a context-like object, mirroring :func:`citation_to_provenance`."""
    text_obj = getattr(context, "text", None)
    if text_obj is None:
        return None
    doc_obj = getattr(text_obj, "doc", None)
    if doc_obj is None:
        return None
    dockey = getattr(doc_obj, "dockey", None)
    if dockey is not None:
        return str(dockey)
    docname = getattr(doc_obj, "docname", None)
    return str(docname) if docname is not None else None


# ── module-level singleton ────────────────────────────────────────────────


_singleton: LinusPaperQA | None = None


def get_singleton() -> LinusPaperQA:
    """Return the process-wide :class:`LinusPaperQA` facade, creating it lazily."""
    global _singleton
    if _singleton is None:
        _singleton = LinusPaperQA()
    return _singleton


def reset_singleton() -> None:
    """Drop the cached singleton (mainly for tests).

    The next call to :func:`get_singleton` will rebuild it. Does NOT
    invoke :meth:`LinusPaperQA.reset` on the existing instance — that's a
    different operation (clearing paper-qa's Docs vs. dropping the
    facade).
    """
    global _singleton
    _singleton = None


# ── async-bridge helper ───────────────────────────────────────────────────


def _run_async(coro: Any) -> Any:
    """Run an awaitable to completion from a synchronous caller.

    The Linus tool registry is synchronous (registry.py docstring is
    explicit on this), so each ``paperqa.*`` tool entry has to bridge
    from sync into async. We use a fresh event loop per call rather than
    :func:`asyncio.run` so the bridge tolerates a partially-running
    loop in the calling thread (e.g., inside a FastAPI test client).
    """
    import asyncio

    try:
        # Reject the dispatch if a loop is already running in this thread —
        # we'd need to run on a worker thread instead, which Phase 2c
        # doesn't yet wire up. Surfacing the error keeps the contract honest.
        running = asyncio.get_running_loop()
    except RuntimeError:
        running = None

    if running is not None:
        # Caller is already inside an event loop. Run the coroutine in a
        # dedicated worker thread with its own loop, blocking the caller
        # until done. This pattern is borrowed from paper-qa's own
        # ``run_or_ensure`` helper (paperqa.utils).
        import concurrent.futures

        def _runner() -> Any:
            new_loop = asyncio.new_event_loop()
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_runner)
            return future.result()

    return asyncio.run(coro)


# ── rigor-gate auto-wiring (DEC-0059) ─────────────────────────────────────


class _AdapterPaperLookup:
    """Thin :class:`~linus.knowledge.rigor.PaperLookup` over :class:`KnowledgeBaseAdapter`.

    Maps the rigor gate's two-method ``PaperLookup`` protocol onto the
    KB adapter's :meth:`get_paper` + :class:`Paper` row shape. Citations
    coming out of paper-qa carry the document's SHA256 (paper-qa's
    ``dockey`` is wired to the SHA-style content hash that the KB
    metadata table primary-keys on), so the resolution is a direct
    SHA-to-row lookup.

    ``get_page_count`` reads the ``page_count`` column on the matched
    row; it returns ``None`` when the column is NULL upstream (the KB
    occasionally fails to extract page count from supplementary
    materials), which the rigor gate tolerates as "can't validate the
    page" rather than as a failure.

    Per-instance lookup cache (#107 H2)
    -----------------------------------

    The rigor gate's :func:`~linus.knowledge.rigor.check_citations` calls
    :meth:`get_paper` first and :meth:`get_page_count` second on every
    citation. The naive implementation issued two SQLite ``SELECT`` round
    trips per citation; this wrapper deduplicates them by memoizing the
    first lookup in :attr:`_paper_cache`. The cache is scoped to the
    instance, which the rigor-gate auto-wiring (:func:`_run_rigor_gate`)
    constructs fresh per ``paperqa.answer`` call. There is no eviction —
    a single gate evaluation looks at O(max_sources) citations, which is
    bounded and small. Cache entries store ``None`` for resolved-missing
    paper ids so a second lookup of a missing id is also a single DB hit.
    """

    def __init__(self, adapter: Any) -> None:
        self._adapter = adapter
        # paper_id → resolved Paper (or None if upstream returned None).
        # Sentinel-free: presence in the dict means the lookup has run;
        # use ``in`` for the cache-hit test, not truthiness on the value.
        self._paper_cache: dict[str, Any | None] = {}

    def _fetch(self, paper_id: str) -> Any | None:
        """Return the cached or freshly-fetched paper for ``paper_id``.

        First call for a given id hits the underlying adapter; subsequent
        calls (within the lifetime of this :class:`_AdapterPaperLookup`
        instance) read the memoized value, including the ``None`` for
        ids the adapter resolved as missing.
        """
        if paper_id in self._paper_cache:
            return self._paper_cache[paper_id]
        paper = self._adapter.get_paper(paper_id)
        self._paper_cache[paper_id] = paper
        return paper

    def get_paper(self, paper_id: str) -> Any | None:
        return self._fetch(paper_id)

    def get_page_count(self, paper_id: str) -> int | None:
        paper = self._fetch(paper_id)
        if paper is None:
            return None
        # ``KnowledgeBaseAdapter.Paper.page_count`` is the canonical
        # field; fall back to ``pages`` for forward-compat with any
        # alternate schema that surfaces a different attribute name.
        page_count = getattr(paper, "page_count", None)
        if page_count is None:
            page_count = getattr(paper, "pages", None)
        try:
            return int(page_count) if page_count is not None else None
        except (TypeError, ValueError):
            return None


def _adapter_to_paper_lookup(adapter: Any) -> _AdapterPaperLookup:
    """Adapt a :class:`KnowledgeBaseAdapter` (or duck-typed equivalent) to ``PaperLookup``.

    Module-private. The wrapper is intentionally tiny so tests can pass
    any object with ``get_paper(paper_id)`` and it Just Works.
    """
    return _AdapterPaperLookup(adapter)


def _resolve_entity_backend() -> Any | None:
    """Return the best-available :class:`~linus.knowledge.rigor.EntityLookup` backend.

    Prefer a KB-derived backend (``linus.knowledge.entity_kb.default_kb_lookup``)
    when importable; fall back to the in-process
    :class:`~linus.knowledge.rigor.BuiltinEntityLookup` stub. On any
    import-time failure (the sibling KB-entity work hasn't landed yet,
    or the KB DB isn't built), the fallback fires and the gate still
    runs against the stub seeds. Returns ``None`` only if even the stub
    can't be constructed — that path is a programmer error in this
    module, not a runtime concern.
    """
    try:
        from linus.knowledge.entity_kb import default_kb_lookup  # type: ignore[import-not-found]

        return default_kb_lookup()
    except (ImportError, FileNotFoundError, AttributeError):
        # Forward-compatible fallback to the in-process stub.
        try:
            from linus.knowledge.rigor import BuiltinEntityLookup

            return BuiltinEntityLookup()
        except Exception:  # pragma: no cover — rigor module is always importable
            return None


def _resolve_paper_backend() -> Any | None:
    """Return the production :class:`PaperLookup` backend, or ``None`` on failure.

    Wraps :class:`KnowledgeBaseAdapter` via :func:`_adapter_to_paper_lookup`.
    The adapter constructor is cheap (it does not open the SQLite
    connection until first query), so building one per answer call is
    fine. Any exception during construction routes through ``None``;
    the rigor gate downgrades a missing paper backend to a single
    ``backend_unavailable`` warning rather than failing.
    """
    try:
        from linus.knowledge.adapter import KnowledgeBaseAdapter

        return _adapter_to_paper_lookup(KnowledgeBaseAdapter())
    except Exception:
        return None


def _run_rigor_gate(
    answer_text: str | None,
    citations: list[dict[str, Any]],
    confidence: float | None = None,
) -> dict[str, Any] | None:
    """Run :func:`linus.knowledge.rigor.check_grounding` on a synthesized answer.

    Best-effort by design. Constructs the :class:`ClaimDict` shape the
    gate expects (rationale + citations + entities + confidence),
    resolves both backends with graceful fallback, runs the gate, and
    returns the serialized :class:`RigorResult` dict.

    Returns ``None`` on any exception inside the gate — paper-qa's
    ``answer`` contract is that the answer call always succeeds; the
    rigor field is purely additive telemetry. A logged warning records
    the failure for post-hoc diagnosis without surfacing it to the
    caller.
    """
    try:
        from linus.knowledge.rigor import check_grounding, result_to_dict

        claim: dict[str, Any] = {
            "rationale": answer_text or "",
            "citations": citations,
            "confidence": confidence,
            "entities": [],
        }
        paper_backend = _resolve_paper_backend()
        entity_backend = _resolve_entity_backend()
        result = check_grounding(
            claim,
            papers=paper_backend,
            entities=entity_backend,
        )
        return result_to_dict(result)
    except Exception as exc:
        logger.warning(
            "rigor gate skipped for paperqa.answer (rigor=None): %s: %s",
            type(exc).__name__,
            exc,
        )
        return None


# ── Linus tool registrations ──────────────────────────────────────────────


@tool(name="paperqa.search")
def paperqa_search(query: str, k: int = 10) -> list[dict[str, Any]]:
    """Search the indexed paper corpus and return up to k matching chunks.

    Returns a list of provenance dicts of shape
    ``{"paper_id", "page", "excerpt", "score"}``, ordered by descending
    relevance. Backed by paper-qa's embedding-based retrieval over the
    configured papers directory (default ``~/.linus/papers/``).
    """
    return _run_async(get_singleton().search(query=query, k=k))


@tool(name="paperqa.gather_evidence")
def paperqa_gather_evidence(query: str, candidate_paper_ids: list[str] | None = None) -> list[dict[str, Any]]:
    """Re-rank evidence chunks for query via the configured Worker LLM.

    Optional ``candidate_paper_ids`` filter narrows the result to only
    chunks from the named papers. Returns provenance dicts in the same
    shape as ``paperqa.search``, but post-ranking is performed by the
    summary LLM rather than purely by embedding similarity.
    """
    return _run_async(get_singleton().gather_evidence(query=query, candidate_paper_ids=candidate_paper_ids))


@tool(name="paperqa.answer")
def paperqa_answer(query: str, max_sources: int = 10) -> dict[str, Any]:
    """Synthesize a citation-grounded answer to query against the paper corpus.

    Returns a dict with the synthesized ``answer`` text, the original
    ``question``, the ``formatted_answer`` (paper-qa's pretty-printed
    answer with inline citations), and a list of ``citations`` (up to
    ``max_sources`` provenance dicts).
    """
    return _run_async(get_singleton().answer(query=query, max_sources=max_sources))


@tool(name="paperqa.reset")
def paperqa_reset() -> dict[str, str]:
    """Clear paper-qa's in-process document collection and session state.

    Useful when starting a new investigation thread or when the prior
    evidence proved unsuitable for the question. Returns a status dict.
    """
    return _run_async(get_singleton().reset())
