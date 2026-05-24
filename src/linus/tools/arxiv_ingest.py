"""arXiv paper ingest tool — ``linus.papers.ingest_arxiv``.

Given an arXiv identifier (bare, URL, or versioned form), downloads the
PDF, fetches metadata via the arXiv Atom API, optionally extracts text
via pypdf, optionally computes a SPECTER2 embedding, and persists a
paper passport JSON in a configurable cache directory.

Returns a flat dict suitable for serialization back to a calling model
(the OpenAI tool-call surface) or to an MCP client. Never raises;
failures land as ``{"error": "<code>", ...}`` records so a downstream
strategy-fusion agent can surface or retry cleanly.

PDF backend
-----------

pypdf (BSD-3) is the canonical PDF text extraction backend in Linus,
not PyMuPDF. The KnowledgeBase submodule uses PyMuPDF for its 4.4×
speed advantage, but PyMuPDF is AGPL-licensed and Linus's license
posture (see DEC-0057) is to avoid AGPL dependencies absent a
project-level license commitment. A future reevaluation could swap
the backend; until then this module sticks to pypdf.

Cache layout
------------

Default root is ``~/.linus/papers/`` (overridable via the
``LINUS_PAPERS_DIR`` environment variable). For each ingested paper:

- ``<id>.pdf`` — raw PDF bytes
- ``<id>.json`` — paper passport (this tool's response payload + extras)
- ``<id>.npy`` — SPECTER2 embedding when sentence-transformers + the
  ``allenai/specter2_base`` model are available; absent otherwise

Idempotency: if ``<id>.json`` already exists, the cached passport is
returned without re-downloading or re-extracting. Force re-ingest by
deleting the JSON file.

Graceful degradation
--------------------

Four external dependencies are handled cleanly:

1. **arXiv API** — required. Failure → ``{"error": "arxiv_api_failed"}``.
2. **PDF download** — required. Failure → ``{"error": "pdf_download_failed"}``.
3. **pypdf text extraction** — optional. Missing import or extraction
   error → ``"warning": "pypdf_unavailable"`` / ``"extraction_failed"``;
   the passport still ships with metadata + sha256.
4. **SPECTER2 embedding** — optional. Missing model →
   ``"warning": "specter2_unavailable"``; the passport still ships.

This lets the tool deliver value (paper metadata + cached PDF) even on
a minimal environment, while documenting the install path for richer
downstream consumers like the Archimedes Tier-1 retrieval engine.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from linus.tools.registry import tool

# ── arXiv ID normalization ────────────────────────────────────────────────

# Bare modern arXiv id: 4 digits . 4-5 digits, optional vN. Pre-2007 ids
# are domain/section/yyyymmnnn but Archimedes-side q-fin papers post-date
# the 2007 changeover so we only need the modern shape here.
_ARXIV_ID_RE = re.compile(r"^(\d{4}\.\d{4,5})(v\d+)?$")
_ARXIV_API_URL = "http://export.arxiv.org/api/query?id_list={id}"
_ARXIV_PDF_URL = "https://arxiv.org/pdf/{id}.pdf"
_ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def normalize_arxiv_id(raw: str) -> str | None:
    """Strip URL prefix, drop version suffix, validate canonical form.

    Returns the canonical bare id (e.g. ``"2407.12345"``) or ``None`` if
    the input is unparseable.
    """
    if not raw:
        return None
    candidate = raw.strip()

    # URL form: extract the last path segment.
    if candidate.startswith(("http://", "https://")):
        parsed = urllib.parse.urlparse(candidate)
        # Path looks like ``/abs/2407.12345v2`` or ``/pdf/2407.12345v2`` or ``.../2407.12345.pdf``
        last = parsed.path.rstrip("/").split("/")[-1]
        if last.endswith(".pdf"):
            last = last[: -len(".pdf")]
        candidate = last

    match = _ARXIV_ID_RE.match(candidate)
    if not match:
        return None
    return match.group(1)


# ── cache layout ──────────────────────────────────────────────────────────


def _papers_dir() -> Path:
    raw = os.environ.get("LINUS_PAPERS_DIR")
    if raw:
        root = Path(raw).expanduser()
    else:
        root = Path.home() / ".linus" / "papers"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _passport_path(arxiv_id: str) -> Path:
    return _papers_dir() / f"{arxiv_id}.json"


def _pdf_path(arxiv_id: str) -> Path:
    return _papers_dir() / f"{arxiv_id}.pdf"


def _embedding_path(arxiv_id: str) -> Path:
    return _papers_dir() / f"{arxiv_id}.npy"


# ── arXiv metadata fetch ──────────────────────────────────────────────────


def _fetch_arxiv_metadata(arxiv_id: str, timeout: float = 10.0) -> dict[str, Any]:
    """Query the arXiv Atom API and parse out the canonical metadata fields.

    Returns a dict with ``title``, ``authors``, ``abstract``, ``year``,
    ``category``. Raises any urllib or XML parse error to the caller —
    :func:`ingest_arxiv` translates those to error-dict responses.
    """
    url = _ARXIV_API_URL.format(id=arxiv_id)
    with urllib.request.urlopen(url, timeout=timeout) as response:
        body = response.read()
    return _parse_atom_entry(body)


def _parse_atom_entry(body: bytes) -> dict[str, Any]:
    """Parse the single-entry arXiv Atom response into a dict."""
    root = ET.fromstring(body)
    entry = root.find("atom:entry", _ATOM_NS)
    if entry is None:
        return {
            "title": None,
            "authors": [],
            "abstract": None,
            "year": None,
            "category": None,
        }

    title_el = entry.find("atom:title", _ATOM_NS)
    summary_el = entry.find("atom:summary", _ATOM_NS)
    published_el = entry.find("atom:published", _ATOM_NS)
    primary_cat_el = entry.find("arxiv:primary_category", _ATOM_NS)

    authors: list[str] = []
    for author_el in entry.findall("atom:author", _ATOM_NS):
        name_el = author_el.find("atom:name", _ATOM_NS)
        if name_el is not None and name_el.text:
            authors.append(name_el.text.strip())

    year: int | None = None
    if published_el is not None and published_el.text:
        # ``2024-07-16T12:34:56Z`` — take leading 4 chars.
        try:
            year = int(published_el.text[:4])
        except ValueError:
            year = None

    return {
        "title": (title_el.text.strip() if title_el is not None and title_el.text else None),
        "authors": authors,
        "abstract": (summary_el.text.strip() if summary_el is not None and summary_el.text else None),
        "year": year,
        "category": (primary_cat_el.get("term") if primary_cat_el is not None else None),
    }


# ── PDF download + extraction ─────────────────────────────────────────────


def _download_pdf(arxiv_id: str, dest: Path, timeout: float = 30.0) -> None:
    """Download the arXiv PDF to ``dest``. Raises urllib errors on failure."""
    url = _ARXIV_PDF_URL.format(id=arxiv_id)
    req = urllib.request.Request(url, headers={"User-Agent": "linus-arxiv-ingest/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as response, dest.open("wb") as out:
        out.write(response.read())


def _sha256_of(path: Path) -> str:
    """Return the SHA256 hex digest of ``path``'s contents (chunked)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _try_extract_text(pdf_path: Path) -> tuple[str | None, str | None]:
    """Return ``(text, warning)``. Either text is set or warning explains why not.

    pypdf is the canonical backend per project license posture (see
    DEC-0057). PyMuPDF would be faster but is AGPL — not used here.
    """
    try:
        from pypdf import PdfReader  # type: ignore[import-not-found]
    except ImportError:
        return None, "pypdf_unavailable"

    try:
        reader = PdfReader(str(pdf_path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages), None
    except Exception as exc:
        return None, f"extraction_failed: {type(exc).__name__}: {exc}"


# ── SPECTER2 embedding (interface only in v1) ────────────────────────────


def _try_specter2_embed(title: str | None, abstract: str | None) -> tuple[bytes | None, str | None]:
    """Attempt SPECTER2 embed of ``title + [SEP] + abstract``.

    Returns ``(npy_bytes, warning)``. v1 ships the interface; if
    sentence-transformers + the SPECTER2 model aren't installed,
    returns ``(None, "specter2_unavailable")``. The Archimedes-side
    consumer can implement this later without changing the tool's
    public surface.
    """
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
    except ImportError:
        return None, "specter2_unavailable"

    if not title and not abstract:
        return None, "no_text_to_embed"

    try:
        import io

        import numpy as np  # type: ignore[import-not-found]

        model = SentenceTransformer("allenai/specter2_base")
        text = f"{title or ''} [SEP] {abstract or ''}".strip()
        embedding = model.encode([text], convert_to_numpy=True)
        buf = io.BytesIO()
        np.save(buf, embedding[0])
        return buf.getvalue(), None
    except Exception as exc:
        return None, f"specter2_failed: {type(exc).__name__}: {exc}"


# ── public entry point ────────────────────────────────────────────────────


@tool(name="linus.papers.ingest_arxiv")
def ingest_arxiv(arxiv_id: str) -> dict[str, Any]:
    """Download, extract, and embed an arXiv paper; return its passport.

    Idempotent: re-running on a cached id returns the existing passport
    without re-downloading. Never raises — failures land as
    ``{"error": ...}`` records.

    The returned dict on success carries: ``arxiv_id``, ``title``,
    ``authors``, ``abstract``, ``year``, ``category``, ``sha256``,
    ``pdf_path``, ``passport_path``, ``embedding_path`` (may be
    ``None``), and an optional ``warning`` describing any best-effort
    step that didn't complete (e.g. ``"pymupdf_unavailable"``).
    """
    normalized = normalize_arxiv_id(arxiv_id)
    if normalized is None:
        return {"error": "invalid_arxiv_id", "arxiv_id": arxiv_id}

    passport = _passport_path(normalized)
    if passport.exists():
        try:
            return json.loads(passport.read_text())
        except (json.JSONDecodeError, OSError):
            # Stale or corrupted cache — fall through to a fresh ingest.
            pass

    # Step 1: metadata
    try:
        metadata = _fetch_arxiv_metadata(normalized)
    except urllib.error.URLError as exc:
        return {"error": "arxiv_api_failed", "detail": str(exc), "arxiv_id": normalized}
    except ET.ParseError as exc:
        return {"error": "arxiv_api_parse_failed", "detail": str(exc), "arxiv_id": normalized}
    except Exception as exc:
        return {"error": "arxiv_api_failed", "detail": f"{type(exc).__name__}: {exc}", "arxiv_id": normalized}

    # Step 2: PDF download
    pdf_path = _pdf_path(normalized)
    if not pdf_path.exists():
        try:
            _download_pdf(normalized, pdf_path)
        except urllib.error.HTTPError as exc:
            return {"error": "pdf_download_failed", "status_code": exc.code, "arxiv_id": normalized}
        except urllib.error.URLError as exc:
            return {"error": "pdf_download_failed", "detail": str(exc), "arxiv_id": normalized}

    sha256 = _sha256_of(pdf_path)

    # Step 3: optional text extraction (best-effort)
    _full_text, extraction_warning = _try_extract_text(pdf_path)

    # Step 4: optional embedding (best-effort)
    embedding_bytes, embedding_warning = _try_specter2_embed(metadata.get("title"), metadata.get("abstract"))
    embedding_path: str | None = None
    if embedding_bytes is not None:
        emb_path = _embedding_path(normalized)
        emb_path.write_bytes(embedding_bytes)
        embedding_path = str(emb_path)

    # Collect warnings (only the most informative; SPECTER2 unavailable shouldn't drown extraction failures).
    warnings = [w for w in (extraction_warning, embedding_warning) if w is not None]

    result: dict[str, Any] = {
        "arxiv_id": normalized,
        "title": metadata.get("title"),
        "authors": metadata.get("authors", []),
        "abstract": metadata.get("abstract"),
        "year": metadata.get("year"),
        "category": metadata.get("category"),
        "sha256": sha256,
        "pdf_path": str(pdf_path),
        "passport_path": str(passport),
        "embedding_path": embedding_path,
        "ingested_at": int(time.time()),
    }
    if warnings:
        result["warning"] = "; ".join(warnings)

    passport.write_text(json.dumps(result, indent=2))
    return result
