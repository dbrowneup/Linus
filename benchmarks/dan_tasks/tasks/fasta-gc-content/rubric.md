# Rubric — FASTA GC content

## Task

Generate a self-contained Python 3 script that reads a FASTA file from `argv[1]` and prints per-sequence GC content
plus an overall GC content. Standard library only. Detailed spec in `input.json`.

## What counts as success (full credit)

1. **Runs without error** when invoked as `python <script> benchmarks/dan_tasks/tasks/fasta-gc-content/sample.fasta`.
2. **Prints six lines** (5 per-sequence + 1 overall) in TSV form: `<id>\t<gc>`.
3. **Numerical correctness** within ±0.5 percentage points of the expected GC values for each sequence.
4. **Standard library only** — no `Bio`, `Biopython`, `pandas`, `numpy`, etc. (`sys` is fine.)
5. **Handles the empty/Ns-only sequence** (`seq5_empty_after_filter`) without crashing or `ZeroDivisionError`. Output
   `0.00` (or equivalent) for that line.

## Expected values (for grader)

`sample.fasta` contains five sequences. Expected GC% (N excluded from both numerator and denominator):

| seq id                 | A   | C   | G   | T   | N   | GC%   |
| ---------------------- | --- | --- | --- | --- | --- | ----- |
| seq1                   | 25  | 25  | 25  | 25  | 0   | 50.00 |
| seq2                   | 80  | 1   | 1   | 18  | 0   | 2.00  |
| seq3                   | 1   | 49  | 49  | 1   | 0   | 98.00 |
| seq4                   | 24  | 24  | 24  | 16  | 12  | 54.17 |
| seq5_empty_after_filter | 0   | 0   | 0   | 0   | 50  | 0.00  |

Overall (sum of A=130, C=99, G=99, T=60, N=62): GC% = (99+99)/(130+99+99+60) = 198 / 388 = 51.03.

The grader cross-checks the script's output against the table above (±0.5 pp tolerance per row). Exact rounding to 2dp
is preferred but not required for partial credit.

## Partial credit

- Script runs but rounds differently / off-by-one on a sequence → **partial**.
- Script handles 4 of 5 sequences correctly (likely fails on `seq5` due to division-by-zero) → **partial**.
- Script imports Biopython despite the instruction → **partial** (still credit for working logic, demerit for non-
  compliance with the spec).

## Failure

- Script does not run (syntax error, missing file handling, etc.).
- Returns prose instead of code.
- Crashes on `seq5_empty_after_filter` with `ZeroDivisionError`.
- Produces wrong GC values across the board (suggests misunderstood algorithm).
