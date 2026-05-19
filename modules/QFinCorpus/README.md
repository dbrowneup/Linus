# QFinCorpus — Linus's quant-finance paper corpus

A dedicated KnowledgeBase instance scoped to quantitative-finance arXiv
papers. Lives separate from Dan's personal biochem/AI corpus so the
Cluster Explorer renders a coherent finance-flavored topic landscape
for Archimedes work.

This is **not** a fork of `modules/KnowledgeBase/`. It's a thin
companion: a small set of papers + scripts that drive the existing KB
pipeline (and Linus's `papers.ingest_arxiv` MCP tool) against a
separate data root.

## Layout

```
modules/QFinCorpus/
├── README.md          # this file
├── .gitignore         # ignores papers/ and data/ (large + local)
├── papers/            # PDFs land here from the seeding script (gitignored)
└── data/              # KB pipeline outputs land here (gitignored)
```

## Workflow

### 1. Curate the seed list

Edit [`scripts/qfin_arxiv_seed.txt`](../../scripts/qfin_arxiv_seed.txt) — one
arXiv ID per line, `#` starts a comment. The shipped starter set covers
a handful of canonical quant-finance papers. Expand as you find more
that warrant inclusion (this is the editorial work that gates corpus
quality).

### 2. Run the seeder

```bash
conda activate linus
python scripts/seed_qfin_corpus.py
```

This calls Linus's `papers.ingest_arxiv` tool on each id in the seed
list. Output lands in `modules/QFinCorpus/papers/`:

- `<arxiv_id>.pdf` — raw PDF
- `<arxiv_id>.json` — paper passport (title, authors, abstract, year, sha256)

Idempotent — re-running skips already-cached papers.

### 3. Run the KB pipeline against this corpus

Two paths depending on how invasive a change you want to make to KB:

**Option A — env-var override of KB's library + cache paths.** If KB's
CLIs accept `--library-dir` and `--cache-dir` flags (verify by reading
its `extract.py`), invoke them with this corpus's paths:

```bash
cd modules/KnowledgeBase
python -m papers_analysis.extract \
    --library-dir ../QFinCorpus/papers \
    --cache-dir ../QFinCorpus/data/cache
# ...and so on for metadata / vectorize / cluster / graph
```

**Option B — clone KB into a sibling dir and point its constants at this
corpus.** Heavier but always works regardless of CLI surface. Track as a
follow-up if Option A isn't viable.

### 4. Browse it in Linus

```bash
export LINUS_KB_OUTPUTS_DIR=modules/QFinCorpus/data/outputs
streamlit run src/linus/app/main.py
```

The Cluster Explorer, Corpus Stats, Paper Graph, Knowledge Graph, and
Search pages all read from `LINUS_KB_OUTPUTS_DIR` (B.0 contract) and
will now render the q-fin corpus instead of Dan's personal one.

## Why separate from `modules/KnowledgeBase/`

The KnowledgeBase submodule is Dan's corpus-of-record (~19k biochem +
AI papers). Mixing q-fin papers into it would (a) dilute the broad
topic clusters away from the finance theme Archimedes needs to see,
and (b) couple two unrelated editorial roadmaps. Keeping QFinCorpus as
its own data root preserves both stances.

The Linus UI is agnostic to which corpus it's pointed at — change
`LINUS_KB_OUTPUTS_DIR` and the same pages re-render with the new data.
