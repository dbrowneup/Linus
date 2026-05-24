"""Tests for the ``linus.papers.ingest_arxiv`` tool.

All HTTP calls are mocked; tests run hermetically without network or
local Ollama. The PDF write path uses a real temp directory so the
sha256 + cache-layout invariants are exercised end-to-end.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from linus.tools.arxiv_ingest import ingest_arxiv, normalize_arxiv_id

# ── ID normalization ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2407.12345", "2407.12345"),
        ("2407.12345v2", "2407.12345"),
        ("2407.12345v10", "2407.12345"),
        ("https://arxiv.org/abs/2407.12345", "2407.12345"),
        ("https://arxiv.org/abs/2407.12345v3", "2407.12345"),
        ("https://arxiv.org/pdf/2407.12345.pdf", "2407.12345"),
        ("http://arxiv.org/pdf/2407.12345v2.pdf", "2407.12345"),
        ("  2407.12345  ", "2407.12345"),
        ("2310.99999", "2310.99999"),  # 5-digit suffix
    ],
)
def test_normalize_arxiv_id_accepts_valid_forms(raw: str, expected: str) -> None:
    assert normalize_arxiv_id(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "not-an-arxiv-id",
        "",
        "2407",
        "abc.def",
        "https://example.com/random",
        "2407.123",  # too few digits
    ],
)
def test_normalize_arxiv_id_rejects_invalid_forms(raw: str) -> None:
    assert normalize_arxiv_id(raw) is None


# ── Tool integration tests ────────────────────────────────────────────────


_FAKE_ATOM_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2407.12345v1</id>
    <title>Test Paper on Time-Series Momentum</title>
    <summary>This paper studies time-series momentum in q-fin contexts.</summary>
    <published>2024-07-16T12:34:56Z</published>
    <author><name>Alice Researcher</name></author>
    <author><name>Bob Coauthor</name></author>
    <arxiv:primary_category term="q-fin.PM" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
</feed>
"""

_FAKE_PDF_BYTES = b"%PDF-1.4\nminimal fake pdf body for sha256 testing\n%%EOF"


def _patch_http_ok(mock_urlopen: MagicMock) -> None:
    """Configure ``urlopen`` to return the atom XML then the PDF bytes in sequence."""
    atom_resp = MagicMock()
    atom_resp.read.return_value = _FAKE_ATOM_XML
    atom_resp.__enter__ = lambda self: self
    atom_resp.__exit__ = lambda *args: None

    pdf_resp = MagicMock()
    pdf_resp.read.return_value = _FAKE_PDF_BYTES
    pdf_resp.__enter__ = lambda self: self
    pdf_resp.__exit__ = lambda *args: None

    mock_urlopen.side_effect = [atom_resp, pdf_resp]


def test_invalid_arxiv_id_returns_error_dict(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LINUS_PAPERS_DIR", str(tmp_path))
    result = ingest_arxiv("not-an-arxiv-id")
    assert result == {"error": "invalid_arxiv_id", "arxiv_id": "not-an-arxiv-id"}


def test_happy_path_populates_passport(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LINUS_PAPERS_DIR", str(tmp_path))

    with patch("linus.tools.arxiv_ingest.urllib.request.urlopen") as mock_urlopen:
        _patch_http_ok(mock_urlopen)
        result = ingest_arxiv("2407.12345")

    assert "error" not in result
    assert result["arxiv_id"] == "2407.12345"
    assert result["title"] == "Test Paper on Time-Series Momentum"
    assert result["authors"] == ["Alice Researcher", "Bob Coauthor"]
    assert "time-series momentum" in (result["abstract"] or "").lower()
    assert result["year"] == 2024
    assert result["category"] == "q-fin.PM"
    assert len(result["sha256"]) == 64  # hex digest
    # PDF + passport land on disk in the configured papers dir.
    assert Path(result["pdf_path"]).exists()
    assert Path(result["passport_path"]).exists()
    # Embedding optional; expect None unless sentence-transformers is installed.
    # (Don't assert which — accept either path.)
    assert "embedding_path" in result


def test_idempotency_skips_redownload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Second invocation should not call urlopen — the cached passport returns directly."""
    monkeypatch.setenv("LINUS_PAPERS_DIR", str(tmp_path))

    with patch("linus.tools.arxiv_ingest.urllib.request.urlopen") as mock_urlopen:
        _patch_http_ok(mock_urlopen)
        first = ingest_arxiv("2407.12345")

    assert "error" not in first

    with patch("linus.tools.arxiv_ingest.urllib.request.urlopen") as mock_urlopen2:
        # Don't configure a side_effect — if the code calls urlopen, it raises.
        second = ingest_arxiv("2407.12345")

    assert second["arxiv_id"] == "2407.12345"
    assert mock_urlopen2.call_count == 0


def test_url_form_normalizes_before_ingest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LINUS_PAPERS_DIR", str(tmp_path))

    with patch("linus.tools.arxiv_ingest.urllib.request.urlopen") as mock_urlopen:
        _patch_http_ok(mock_urlopen)
        result = ingest_arxiv("https://arxiv.org/abs/2407.12345v2")

    assert result["arxiv_id"] == "2407.12345"


def test_arxiv_api_failure_surfaces_error_not_raised(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LINUS_PAPERS_DIR", str(tmp_path))

    import urllib.error

    with patch("linus.tools.arxiv_ingest.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.URLError("network down")
        result = ingest_arxiv("2407.12345")

    assert result["error"] == "arxiv_api_failed"
    assert "network down" in result["detail"]
    assert result["arxiv_id"] == "2407.12345"


def test_pdf_download_failure_surfaces_error_not_raised(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LINUS_PAPERS_DIR", str(tmp_path))

    import urllib.error

    atom_resp = MagicMock()
    atom_resp.read.return_value = _FAKE_ATOM_XML
    atom_resp.__enter__ = lambda self: self
    atom_resp.__exit__ = lambda *args: None

    def side_effect(req_or_url, **kwargs):
        # First call: atom api ok. Second call: PDF 404.
        if isinstance(req_or_url, str):
            return atom_resp
        raise urllib.error.HTTPError(req_or_url.full_url, 404, "Not Found", {}, None)

    with patch("linus.tools.arxiv_ingest.urllib.request.urlopen", side_effect=side_effect):
        result = ingest_arxiv("2407.12345")

    assert result["error"] == "pdf_download_failed"
    assert result["status_code"] == 404


def test_pypdf_unavailable_yields_warning_not_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When pypdf isn't importable, the tool still returns a successful passport with a warning."""
    monkeypatch.setenv("LINUS_PAPERS_DIR", str(tmp_path))

    # Patch the helper directly so we test the integration behavior.
    with (
        patch("linus.tools.arxiv_ingest.urllib.request.urlopen") as mock_urlopen,
        patch(
            "linus.tools.arxiv_ingest._try_extract_text",
            return_value=(None, "pypdf_unavailable"),
        ),
    ):
        _patch_http_ok(mock_urlopen)
        result = ingest_arxiv("2407.12345")

    assert "error" not in result
    assert "warning" in result
    assert "pypdf_unavailable" in result["warning"]


def test_tool_registered_on_default_registry() -> None:
    """The @tool decorator should register the tool under its canonical name."""
    from linus.tools import default_registry

    assert "linus.papers.ingest_arxiv" in default_registry.names()
    spec = default_registry.get("linus.papers.ingest_arxiv")
    assert spec is not None
