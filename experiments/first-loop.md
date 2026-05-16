# Spec: First Recorded Maestro/Worker Loop — Sandboxed FS Wrapper

Task ID: first-loop-v1

## Goal

This is the first recorded Maestro/Worker loop on the Linus books (Phase 1e of the 2026-05-12 implementation plan).
The work product is a real, useful artifact: a Python class that wraps `linus.fs.read` and `linus.fs.write` with
sandbox path-prefix validation per SAFETY.md. The dual purpose is (a) ship the first sandbox helper that Phase 2a
will depend on, and (b) shake out the Maestro/Worker protocol's hand-off rules under realistic conditions.

Maestro is hosted Claude (this session). Worker is `qwen2.5-coder:7b` served via Ollama at `localhost:11434`
(`qwen3:8b` is not pulled locally; `qwen2.5-coder:7b` is the closest equivalent and is purpose-built for
code generation).

## Inputs

- SAFETY.md path-prefix rules (Tier 1 write allowlist): `src/`, `benchmarks/`, `experiments/`, `docs/` relative
  to the Linus repo root.
- This spec, passed to the Worker verbatim as the prompt.

No external data, no network calls beyond the local Ollama endpoint, no shell access from the Worker's generated
code.

## Outputs

- `src/linus/sandbox/fs.py` — a single Python file containing:
  - A `SandboxFS` class (or equivalent) wrapping `read` and `write` operations.
  - Path-prefix validation against the Tier 1 allowlist for write paths.
  - Read is allowed anywhere under the repo root (Tier 0 default).
  - Three pytest unit tests, either inline in the same file (under an `if __name__ == "__main__":` block is
    NOT acceptable — they must be importable by pytest) or in a sibling `test_*.py` module that the Worker
    generates as part of its output. The Worker's prompt asks for tests in the same file using a module-level
    `def test_*` functions style so a single file output suffices.

Intermediate artifacts retained for the audit trail:

- `experiments/first_loop_output.txt` — raw stdout from the Worker (full unredacted response).
- `experiments/first-loop-review.md` — Maestro's review notes after the run.

## Constraints

- Single file output at `src/linus/sandbox/fs.py`.
- Type hints on every function/method signature.
- Docstrings on the class and every public method.
- Exactly 3 unit tests, written as module-level `def test_<name>():` functions in the same file so pytest can
  discover them via `pytest src/linus/sandbox/fs.py`.
- No network calls.
- No `os.system` / `subprocess` / shell escapes.
- Standard library only (no third-party imports beyond `pytest` for the tests, if needed for fixtures).
- Path validation raises `PermissionError` (or a clearly named custom exception) on disallowed writes; do not
  return a sentinel value.
- The repo root is resolved at construction time; do not hardcode `/Users/dbrowne/...`.

## Success Criteria

1. `python -c "import ast; ast.parse(open('src/linus/sandbox/fs.py').read())"` succeeds — the file is
   well-formed Python.
2. `pytest src/linus/sandbox/fs.py -v` exits 0 with 3 tests passing.
3. Smoke check: instantiating `SandboxFS(repo_root="/tmp/whatever")` and calling `.read("/etc/passwd")` either
   raises (if read is also gated to a prefix) or returns content; calling `.write("/etc/passwd", "data")`
   raises `PermissionError`.
4. The class has type hints and docstrings on all public methods.
5. Tests cover: (a) writing to an allowed prefix succeeds, (b) writing to a disallowed prefix raises, and
   (c) reading round-trips the written content.

## Smoke Test Boundary

Trivial input, known expected output:

- Construct `SandboxFS(repo_root=tmp_path)` where `tmp_path` is a pytest tmp dir.
- `write("src/x.txt", "hello")` should succeed and create the file.
- `write("../../etc/passwd", "evil")` should raise `PermissionError`.
- `read("src/x.txt")` should return `"hello"`.

If any of those three steps fail, the smoke gate is failed and the verdict is REJECT/REVISE.

## Implementation Notes (for the Worker)

The Worker is a code-generation model. Keep the prompt focused on output, not on background. The driver script
inlines this spec into a system+user prompt and constrains the model to emit a single Python file inside a
triple-backtick fence so the driver can extract it deterministically.

The Worker is NOT expected to run tests itself. The Maestro review pass runs `pytest` after extraction.

## Related

- SAFETY.md — Tier 1 write allowlist, sandbox-enforcement contract.
- `docs/protocols/maestro-worker-protocol.md` — the protocol this loop is exercising.
- `docs/specs/2026-05-12-linus-implementation-plan.md` — Item 3.
