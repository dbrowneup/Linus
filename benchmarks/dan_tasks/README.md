# Dan task suite — Phase 1d v0

Private benchmark suite for Linus. Three tasks pulled from real work; the primary evaluation measure for every future
Phase 2+ delivery (per ROADMAP.md section "1d — Private 'Dan task' suite").

## Layout

```
dan_tasks/
  README.md
  tasks/
    paper-summarization/
      input.json                    # task spec (PDF path + prompt)
      expected_output_schema.json   # JSON schema for the expected output
      rubric.md                     # success / partial / failure rules
    fasta-gc-content/
      input.json
      sample.fasta                  # 5-sequence test FASTA with known GC values
      expected_output_schema.json
      rubric.md
    title-clustering/
      input.json                    # 50 real titles from docs/paper-notes/INDEX.md
      expected_output_schema.json
      rubric.md
  runners/
    run_all.py                      # calls Ollama, runs each task, writes results JSON
```

Results land at `benchmarks/results/dan_tasks_baseline_<ISO date>.json`.

## Tasks (v0)

1. **paper-summarization** — extract 3 key findings from MemGPT (arxiv 2310.08560). pypdf-extracted text, first 12000
   chars sent to the model, three-item numbered Markdown list expected.
2. **fasta-gc-content** — generate a self-contained Python script that computes per-sequence and overall GC content
   on a FASTA file. Stdlib only. Rubric grades against numerical expected values in `sample.fasta`.
3. **title-clustering** — cluster 50 paper titles (drawn live from `docs/paper-notes/INDEX.md`) into 5 named topics.
   Output as Markdown `## Cluster N: <name>` sections with bulleted title lists.

## Running

```bash
conda activate linus
# Ensure Ollama is running with the worker model pulled:
brew services start ollama
ollama pull qwen3:8b

python benchmarks/dan_tasks/runners/run_all.py
# Or with a different model:
OLLAMA_MODEL=qwen3:14b python benchmarks/dan_tasks/runners/run_all.py
```

The runner FAILS LOUD if Ollama is unreachable or the model is not pulled — no silent fallbacks. Output JSON is written
to `benchmarks/results/dan_tasks_baseline_<ISO date>.json` with one entry per task plus wall-time metadata.

## Scope of v0

This is collection-only. No automated scoring/grading — that's a follow-up. Dan reads the raw outputs and assesses
whether Qwen3:8b is producing useful work on his task surface. That's the first concrete "is the Worker model
actually good enough?" data point.

Future versions will:

- Add 2-5 more tasks (matplotlib log-scale fix, bioinformatics traceback diagnosis, ...) per ROADMAP 1d.
- Add an automated scoring pass that executes the FASTA script, parses the cluster list against the rubric, and
  grades the paper findings against the reference list.
- Run the suite against multiple worker models (Ollama variants, pmetal if adopted, hosted Claude as reference)
  for side-by-side comparison.

## Conventions

- One task = one directory under `tasks/`. Slug matches the dispatcher key in `runners/run_all.py`.
- Every task has `input.json`, `expected_output_schema.json`, and `rubric.md`. Additional input artifacts (PDFs,
  FASTA, code snippets) live next to those.
- Results never overwrite — date-stamped filenames keep the historical record. Wall-time and ollama eval counts are
  preserved per task for trend analysis.
