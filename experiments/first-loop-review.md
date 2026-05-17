# First Maestro/Worker Loop — Review Notes

**Date:** 2026-05-16
**Branch:** `experiment/first-maestro-worker-loop`
**Base SHA:** 9b91b66
**Maestro:** hosted Claude (Opus 4.7, Claude Code session)
**Worker:** `qwen2.5-coder:7b` via Ollama at `localhost:11434`
**Spec:** [`experiments/first-loop.md`](first-loop.md)
**Driver:** [`experiments/first_loop_driver.py`](first_loop_driver.py)
**Raw outputs:** `experiments/first_loop_output_pass1.txt`, `experiments/first_loop_output_pass2.txt`

## Verdict

**REJECT** — the Worker produced parseable Python on both passes but failed the
correctness gates on both. The generated file is NOT being added to `src/linus/sandbox/fs.py`;
the experiment artifacts (spec, driver, raw outputs, this review) are preserved as the
Phase-1 data point.

A `src/linus/sandbox/fs.py` written by Maestro (or a sharper Worker pass with a tighter
spec) remains TODO for Phase 2a. This experiment generated the data needed to write that
better spec.

## Pass 1 — what the Worker produced

`qwen2.5-coder:7b` returned 2070 characters in 34.8 seconds, cleanly wrapped in a single
` ```python ` fenced block. The extractor pulled it cleanly. AST-parse: OK.

Structure:

- A `SandboxFS` class with `__init__(repo_root)`, `_validate_path`, `read`, `write`.
- A custom `class PermissionError(Exception)` shadowing the builtin.
- A hardcoded `allowlist = ["src/", "benchmarks/", "experiments/", "docs/"]`.
- Three module-level `def test_*` functions.

`pytest src/linus/sandbox/fs.py` result: **2 passed, 1 failed.**

- `test_read_success` — PASSED.
- `test_write_allowed_prefix` — FAILED with `FileNotFoundError: /tmp/src/x.txt` because
  the Worker did not `mkdir` the parent dir and the test did not pre-create it.
- `test_write_disallowed_prefix` — PASSED.

Smoke gate on `/etc/passwd`:

- `read('/etc/passwd')` returned 9344 chars of `/etc/passwd` content. NOT GATED. The
  Worker used `os.path.join(self.repo_root, path)` which silently discards `repo_root`
  when `path` is absolute. This is a real security defect.
- `write('/etc/passwd', 'data')` raised `PermissionError`. Correctly gated (by accident
  of the string-prefix check on the allowlist).

Pass-1 verdict: REVISE. Code AST-parses but fails its own test, contains a path-traversal
escape (`startswith` check is fooled by `src/../../etc/passwd`), and leaks reads.

## Pass 2 — what the Worker produced after the revision feedback

The spec was updated with a Revision 1 feedback section enumerating the five defects.
The Worker returned 2111 characters in 18.2 seconds (faster — possibly because the model
seeded from its previous response in the prompt cache).

Pass-2 changes:

- Switched from `os.path` to `pathlib.Path`.
- Added `is_relative_to` check.
- Removed the explicit `allowlist` and replaced it with a "must be under `repo_root`" check.
- Added `parent.mkdir(parents=True, exist_ok=True)` before writing.
- Tightened type hints (`data: str`, `read() -> str`).
- Did NOT remove the shadowed `PermissionError` builtin.

`pytest src/linus/sandbox/fs.py` result: **1 passed, 2 failed.** Worse than pass 1.

- `test_write_allowed_prefix` — FAILED with `PermissionError: Access denied to src/x.txt`.
- `test_write_disallowed_prefix` — PASSED.
- `test_read_round_trip` — FAILED (depends on `test_write_allowed_prefix` succeeding).

The pass-2 bug: `self.repo_root / Path(path).resolve()` is a no-op when `path` is
relative-but-`resolve()` is called on it — `Path("src/x.txt").resolve()` resolves
against the process's current working directory (the worktree path), not against
`repo_root`. The resulting absolute path is then "joined" with `repo_root` using `/`,
which in pathlib discards the left side when the right is absolute. So
`resolved_path.is_relative_to(self.repo_root)` checks whether `<cwd>/src/x.txt` is
under `/tmp`, which it isn't, and the validator rejects the legitimate test write.

Smoke gate on `/etc/passwd`:

- `read('/etc/passwd')` raised `PermissionError`. CORRECT.
- `write('/etc/passwd', 'data')` raised `PermissionError`. CORRECT.

So pass 2 fixed the security leak but broke the happy path. Pass 1 had the happy path
mostly right but had the security leak. Neither is shippable code.

## What worked

- The Maestro/Worker protocol mechanics: spec written, driver invokes Ollama, raw output
  saved, code extracted from a fenced block deterministically. The protocol surface itself
  performed cleanly. No fence-extraction edge cases, no orphan prose, no model refusing the
  task.
- Wall-time per pass is small (35s and 18s). The iteration loop is cheap.
- Both passes produced well-formed Python that AST-parses, has type hints on every
  function, has docstrings on the class and public methods, and emits exactly three
  module-level pytest test functions. The structural constraints in the spec were honored
  in both passes.
- The Worker took the Revision 1 feedback seriously and changed real things — switched
  libraries, added `mkdir`, tightened types. It did NOT just rephrase the same code.

## What didn't work

- **The Worker can write code-shaped Python but does not yet pass its own tests on this
  kind of task.** Pass 1: 2/3 pass. Pass 2: 1/3 pass. Neither pass cleared the spec's
  success criteria #2 (`pytest src/linus/sandbox/fs.py -v` exits 0).
- **Sandbox correctness is hard for a 7B model.** The exact bug class (absolute-path
  silently bypasses `os.path.join`-based joining; `pathlib.Path.resolve()` on a relative
  path resolves to CWD) is the kind of subtle Python footgun that experienced humans
  routinely miss. Asking a 7B coder model to nail it in one shot, even with explicit
  feedback, is asking too much. This is a useful calibration data point.
- **The Worker dropped the allowlist constraint between passes.** The spec said writes
  are gated to `src/`, `benchmarks/`, `experiments/`, `docs/`. Pass 1 had the allowlist
  (via string prefix). Pass 2 replaced it with "anywhere under repo_root." The Worker
  did not surface this as a question or note; it just changed the behavior.
- **Shadowed `PermissionError`.** The Worker was told explicitly to use the builtin and
  did not. Minor, but indicates the feedback was partially absorbed.
- **No tests against pre-existing files / read paths.** Both passes wrote tests that only
  exercised the most direct cases. There were no tests for: read on a path outside
  `repo_root`, write on an absolute path, write on a path-traversal escape (`src/../../...`).
  The Maestro smoke gate caught these via separate ad-hoc invocation.

## Calibration takeaways for the spec next time

When writing the next iteration spec for sandbox helpers, do these:

1. **Provide a starter test scaffold in the spec** that the Worker fills in. Reduce the
   surface where the Worker can invent broken tests. The Maestro writes the assertions;
   the Worker implements the helpers.
2. **Use `pytest.tmp_path` fixtures** instead of `/tmp` hardcoded paths. The hardcoded
   `/tmp/src/x.txt` is brittle and pollutes the host. A `tmp_path` fixture would have
   forced the Worker to handle parent-dir creation correctly.
3. **Test the path-traversal case explicitly.** The spec should require a fourth test
   that exercises `src/../../etc/passwd` so the Worker can't pass with `startswith`.
4. **Show, don't tell, on the resolve-and-check pattern.** Include the four-line code
   sketch in the spec so the Worker doesn't have to derive it. `pathlib.Path` semantics
   around relative `resolve()` is unintuitive enough that a 7B model isn't going to
   reinvent it correctly.
5. **Consider that the right Worker for security-critical code may not be a 7B coder.**
   Per the Maestro/Worker protocol's Botvinick & Gershman principle: there is a class
   of decisions (which problems to pursue, what constitutes success) that stays with
   the human. Sandbox correctness may belong on the Maestro side of that line for now —
   delegate the boilerplate, not the security primitive itself.

## Maestro-side bugs in this loop

The Maestro pass was not without its own defects:

1. The spec's "read is allowed anywhere under the repo root" line is ambiguous about
   absolute paths. The Worker's pass-1 read leak is partly traceable to spec ambiguity.
2. The Maestro did not write the smoke-test invocations as a script the Worker could
   run; it was a manual one-liner. Putting it in the spec as a `make smoke` or
   `python -m experiments.first_loop_smoke` would have given the Worker a verifiable
   gate to self-check against.
3. The Maestro did not enforce the `pytest src/linus/sandbox/fs.py -v` gate at the
   spec level — the spec said tests must pass but did not require the Worker to run them.
   Future Worker drivers should run the tests in-line and re-attempt on failure.

## Outputs preserved in this commit

- `experiments/first-loop.md` — the spec (with the Revision 1 feedback appended)
- `experiments/first_loop_driver.py` — the driver
- `experiments/first_loop_output_pass1.txt` — raw Worker output, pass 1
- `experiments/first_loop_output_pass2.txt` — raw Worker output, pass 2
- `experiments/first_loop_output.txt` — copy of pass-2 output (live driver output file)
- `experiments/first-loop-review.md` — this file

NOT preserved: `src/linus/sandbox/fs.py`. The generated code is in the raw output
files for the audit trail but does not enter the package. A future task — write the
sandbox FS helper correctly, either as a tighter Maestro/Worker loop or as a direct
Maestro implementation — is queued for the Phase 2a sandbox slice.

## Wall time

- Start: 2026-05-16T15:00:59-0500
- End (review write): ~2026-05-16T15:08
- Total: ~7 minutes of wall time for the full loop including two Worker passes,
  manual review, and write-up. Estimate was 45 minutes; actual is ~7 minutes. The
  variance is on the cheap side because (a) the Worker passes were small (~30 sec
  each), (b) the spec was short, (c) the Maestro review used direct pytest gates
  rather than discursive analysis. This is the first data point for the
  "measure, don't estimate" cadence; the 45-minute estimate was anchored on
  human-style careful review, but Claude-Code-as-Maestro is faster at the
  mechanical parts.

## What this experiment is good for

This is a Phase-1 calibration. The take-home:

- **The protocol mechanics work.** Spec → driver → Worker → review → verdict loop
  ran cleanly end-to-end. The Maestro/Worker discipline is operationally viable on
  this hardware with this model.
- **The Worker's code-correctness on security-critical primitives is not yet Phase-2
  ready.** Use Workers for boilerplate, scaffolding, and well-fenced refactors;
  hand-write or hand-review-line-by-line security-critical code.
- **The spec is the lever.** A sharper spec with a starter test scaffold and a
  pattern sketch would likely have produced acceptable code in pass 1.

Decision: do NOT block Phase 2a on a "fix the sandbox helper" loop. The Maestro can
hand-write `src/linus/sandbox/fs.py` in 5 minutes when the actual Phase 2a server
work calls for it. The lesson from this experiment is the calibration data, not the
artifact.
