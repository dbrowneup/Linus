"""Linus Streamlit corpus-stats page — task B.2 of the MVP build.

Renders the KnowledgeBase pipeline's Phase 1 (corpus statistics)
artifacts: pre-computed PNGs from ``data/outputs/`` plus a header row
of headline metrics read from the corpus JSON files.

This page is pure read — no server interaction. The KB pipeline
(``modules/KnowledgeBase/papers_analysis/stats.py``) produces these
files; this page just surfaces them in the Linus UI so the same data
that drives the Cluster Explorer can be browsed without leaving the
app.

Path resolution: all artifact paths resolve relative to
:data:`linus.app.config.KB_OUTPUTS_DIR` (env var
``LINUS_KB_OUTPUTS_DIR``, default ``modules/KnowledgeBase/data/outputs/``).
Re-pointing the env var lets the same page render Dan's personal
corpus during dev and the q-fin corpus instance once it's seeded.

Missing artifacts render as warning rows rather than crashing — KB's
pipeline is independently resumable and a partial run is a legitimate
state to surface.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import streamlit as st

from linus.app.config import KB_OUTPUTS_DIR

st.set_page_config(page_title="Corpus Stats — Linus", page_icon="🜨", layout="wide")
st.title("📚 Corpus Stats")
st.caption(f"Phase 1 KnowledgeBase outputs from `{KB_OUTPUTS_DIR}`.")


# ── headline metrics ──────────────────────────────────────────────────────


def _load_paper_count() -> int | None:
    """Count rows in ``per_paper_stats.csv`` (one row per paper)."""
    path = KB_OUTPUTS_DIR / "per_paper_stats.csv"
    if not path.exists():
        return None
    try:
        with path.open() as f:
            reader = csv.reader(f)
            next(reader, None)  # header
            return sum(1 for _ in reader)
    except OSError:
        return None


def _load_vocab_size() -> int | None:
    """Vocabulary size = number of unique words in ``corpus_word_counts.json``."""
    path = KB_OUTPUTS_DIR / "corpus_word_counts.json"
    if not path.exists():
        return None
    try:
        with path.open() as f:
            data = json.load(f)
        if isinstance(data, dict):
            return len(data)
        return None
    except (OSError, json.JSONDecodeError):
        return None


def _load_total_words() -> int | None:
    """Total word occurrences = sum over ``corpus_word_counts.json`` values."""
    path = KB_OUTPUTS_DIR / "corpus_word_counts.json"
    if not path.exists():
        return None
    try:
        with path.open() as f:
            data = json.load(f)
        if isinstance(data, dict):
            return sum(int(v) for v in data.values() if isinstance(v, (int, float)))
        return None
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def _fmt(n: int | None) -> str:
    return f"{n:,}" if n is not None else "—"


paper_count = _load_paper_count()
vocab_size = _load_vocab_size()
total_words = _load_total_words()

col1, col2, col3 = st.columns(3)
col1.metric("Papers", _fmt(paper_count))
col2.metric("Vocabulary size", _fmt(vocab_size))
col3.metric("Total word occurrences", _fmt(total_words))


# ── visualizations ────────────────────────────────────────────────────────


PANELS: list[tuple[str, str, str]] = [
    # (filename, header, caption)
    (
        "corpus_overview.png",
        "Corpus overview",
        "Headline summary plot: paper/word distributions across the corpus.",
    ),
    (
        "zipf_filtered.png",
        "Zipf's law (DF-filtered)",
        "Log-log rank-frequency plot after document-frequency filtering "
        "(min_df=2, max_df≤66% of docs). The slope is the Zipf exponent.",
    ),
    (
        "zipf_raw.png",
        "Zipf's law (raw vocabulary)",
        "Same plot computed on the unfiltered vocabulary — useful for sanity-checking "
        "tail behavior before stop-word-like filtering.",
    ),
    (
        "page_distribution.png",
        "Pages per document",
        "Histogram of page counts. Articles vs. supplements vs. books typically separate "
        "cleanly here (>80 pages = book by KB convention).",
    ),
    (
        "words_per_document.png",
        "Words per document",
        "Histogram of total words per paper. Drives the LLM context-budget rule of thumb.",
    ),
    (
        "tokens_per_document.png",
        "Tokens per document (Mistral-7B)",
        "Per-paper Mistral-7B SentencePiece token counts with 4k / 8k / 32k / 128k context "
        "reference lines.",
    ),
    (
        "words_per_page.png",
        "Words per page",
        "Density check — useful for identifying scanned/OCR'd PDFs with low text density.",
    ),
    (
        "vocab_richness.png",
        "Vocabulary richness (type/token ratio)",
        "Per-paper unique-word count over total word count. Higher = more diverse vocabulary.",
    ),
    (
        "word_distributions.png",
        "Word-count distributions",
        "Joint distribution view across paper types (articles / supplements / books).",
    ),
    (
        "top_words_combined.png",
        "Top words (combined)",
        "Most frequent words across the corpus, post-filtering.",
    ),
]


def _render_panel(filename: str, header: str, caption: str) -> None:
    path: Path = KB_OUTPUTS_DIR / filename
    st.subheader(header)
    if path.exists():
        st.image(str(path), caption=caption, use_container_width=True)
    else:
        st.warning(f"Not found: `{path}`. Run KB Phase 1: `python -m papers_analysis.stats`.")
    st.divider()


present_count = sum(1 for fn, _, _ in PANELS if (KB_OUTPUTS_DIR / fn).exists())
if present_count == 0:
    st.info(
        "No corpus-stats artifacts found at the configured outputs directory. "
        "Run the KB Phase 1 pipeline to produce them:\n\n"
        "```\n"
        "cd modules/KnowledgeBase\n"
        "python -m papers_analysis.extract\n"
        "python -m papers_analysis.stats\n"
        "```\n\n"
        "Or set `LINUS_KB_OUTPUTS_DIR` to point at an already-populated outputs directory."
    )
else:
    for filename, header, caption in PANELS:
        _render_panel(filename, header, caption)
