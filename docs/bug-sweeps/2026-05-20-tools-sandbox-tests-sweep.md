# Bug sweep — `src/linus/tools/` + `src/linus/sandbox/` + `tests/` (2026-05-20)

## Summary

Read-only sweep of the tool registry, sandbox filesystem boundary, paper ingestion tool, and their accompanying
hermetic + integration tests. Base SHA `e1a07af`. Hermetic suite: **591 passing (2.95 s)** — no regressions to land on
top of. Findings: **0 critical**, **1 high**, **3 medium**, **5 low**, **2 informational**. The single highest-priority
issue is a documented-but-unenforced parent-symlink TOCTOU window in `SandboxFS.write`; arbitrary-write potential exists
under contrived but plausible setups. No clear arbitrary-file-write or sandbox-bypass on the canonical hardening path
was found.

## Findings

### High

#### H-1 — `SandboxFS.write` parent-symlink TOCTOU + parent-dir creation race (sandbox, security)

**File:** `src/linus/sandbox/fs.py` lines 56–69, 71–85.

`_resolve_under_root()` does `(self._root / path).resolve()` once at the top of `write()`, then **before** the
`write_text` call, `write()` invokes `target.parent.mkdir(parents=True, exist_ok=True)` and `target.write_text(...)`.
Between the resolve check and the write, the parent directory (or the target file itself if it pre-exists as a symlink)
can be replaced with a symlink pointing outside the repo root. Specifically:

1. **Target as symlink to outside.** If `src/foo.txt` already exists as a symlink whose target is `/etc/passwd`,
   `_resolve_under_root("src/foo.txt")` resolves the symlink and returns `/etc/passwd`, which fails the
   `is_relative_to(self._root)` check — that's safe. But: if `src/foo.txt` is a symlink to **a non-existent** path
   outside the root, `resolve()` on systems where the strict default is False (Python 3.6+) returns the joined absolute
   path without following the unresolvable link, so the check **may pass** and `write_text` then follows the symlink at
   write time. Verified by inspection of `pathlib.PurePath.resolve(strict=False)` semantics: non-existent components
   normalize lexically.

2. **Parent symlink TOCTOU.** An attacker (or a misbehaving co-tenant tool) who can create files under `src/` (the
   sandbox boundary permits that) can race: between `_resolve_under_root` returning a clean path under root and the
   subsequent `mkdir(parents=True)` + `write_text`, replace `src/` with a symlink to `/tmp/evil` or rename an inner
   directory. Linus is single-process and this is a contrived attack today, but the same code is the boundary that
   will protect against multi-worker tool fan-out in Phase 3, where the race window matters.

3. **`mkdir(parents=True)` will silently create intermediate directories** under whatever the parent resolves to at
   call time, not at check time. A symlinked intermediate would cause the mkdir to extend onto a host-tree location
   without re-validating the resolved tree.

**Recommendation:** open the file with `os.open(target, O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW)` (POSIX) and re-validate the
realpath of the opened FD via `os.fstat`/`/proc/self/fd` (Linux) or `F_GETPATH` (macOS). At minimum, call
`resolve(strict=False)` then re-call `resolve(strict=True)` after `mkdir` and compare equality before writing. Also
reject target paths whose `lstat` is a symlink even when the resolved target lands inside the root.

**Severity rationale:** flagged **high**, not critical, because (a) Linus is single-process today, (b) the attacker
must already have write access under an allowlist subdirectory, and (c) no test demonstrates a real bypass. But the
class of bug is exactly the one SAFETY.md says the resolve-and-prefix check exists to prevent, so it deserves prompt
attention before Phase 3 spawns multi-process Workers.

---

### Medium

#### M-1 — `_resolve_under_root` accepts unresolvable paths without strict mode (sandbox, security)

**File:** `src/linus/sandbox/fs.py` lines 71–85.

`(self._root / path).resolve()` calls `Path.resolve(strict=False)` (the default). For a path that doesn't yet exist on
disk, `resolve` performs lexical normalization only and does **not** follow the implicit chain through symlinked
intermediates — but pre-existing symlinked intermediates **are** followed. A pre-write target path like
`src/new/output.txt` where `src/new` is a symlink to `/tmp/evil` resolves to `/tmp/evil/output.txt` and the
`is_relative_to(self._root)` check rejects it (good). But if `src/new` is a symlink **whose target does not yet exist**,
`resolve(strict=False)` returns the lexical join (the resolver doesn't follow into a non-existent name), the path
passes the prefix check, and the subsequent `mkdir(parents=True)` / `write_text` follows the symlink at I/O time —
landing outside the root.

This is a closely related variant of H-1 above; it deserves its own line because the fix is different (force
`strict=True` on the prefix-check, accept the FileNotFoundError as a clean "must exist" gate, OR walk the path
component-by-component with `lstat` and forbid any symlink-typed intermediate).

**Recommendation:** for `write()`, walk `target.parents` from root downward and reject if any component is a symlink
(`lstat().st_mode & stat.S_IFLNK`). For `read()`, since the file must exist, use `resolve(strict=True)`.

#### M-2 — Tool registry uses `func.__module__.split(".")[0]` for default name — fragile under reorganization (tools, low/medium)

**File:** `src/linus/tools/registry.py` lines 268–273.

`f"{module}.{short}"` produces, for a function whose `__module__` is `"src.linus.tools.kb_tools"` (e.g. when pytest
collection uses the src-layout), the name `"src.search_papers"` — losing the `linus.tools.kb_tools.` qualifier. The
test suite passes because every kb_tool and rigor tool registration uses an explicit `name=` kwarg, but **any future
`@tool` use without an explicit name** is at risk of producing a top-level-package name that depends on the import
layout. For a worktree run where `sys.path` happens to be inserted at `/.../src` vs `/.../`, the same function gets a
different default name — non-determinism the dispatcher then can't reconcile.

`test_register_derives_name_from_module_and_qualname` actually documents this fragility (its assertion is the
hand-wavy `spec.name.endswith(".fn")` rather than a literal match).

**Recommendation:** drop the `split(".")[0]` and use the **full** module path. Tools that want a short name should pass
`name=` explicitly. The wire-protocol stability argument cuts the other way: a derived name should be stable, not
truncated to one segment.

#### M-3 — `_try_extract_text` does not configure pypdf's decompression limit (arxiv_ingest, performance / DoS)

**File:** `src/linus/tools/arxiv_ingest.py` lines 213–229.

CLAUDE.md Known Library Quirks records: "**pypdf decompression limit**: disable with `sys.maxsize`, NOT `0` or
`2**63`. Inherited from KnowledgeBase." The arxiv_ingest tool calls `PdfReader(str(pdf_path))` and iterates
`reader.pages` without ever setting `pypdf.constants` or `reader.strict` or the decompression-bomb cap. For an arXiv
PDF carrying an embedded zip bomb (rare but exists in the wild — academic adversarial-ML papers occasionally embed
recursive PDF objects), the extraction can spin / OOM.

This is also a swallowed exception class — the `Exception` catch on line 228 returns the warning string, so the worst
case is a captured error, but for **resource exhaustion** that catch fires after the damage. The Worker process can
end up with hundreds of MB of decompressed buffer in memory.

**Recommendation:** at module import time set the documented value (`pypdf.PdfReader` exposes
`strict=False`, and pypdf 3.x has a module-level `pypdf.PdfReader.decompression_bomb_limit` configurable). Inherit
KnowledgeBase's setting (`sys.maxsize`) explicitly, even if that means **disabling** the bomb check; the comment
should match the project-wide quirk note. Confirming the quirk's intent is recommended — "disable with sys.maxsize"
in CLAUDE.md reads as "set to sys.maxsize to disable," which is the opposite of the usual safety stance.

#### M-4 — `_download_pdf` reads entire PDF into memory before write (arxiv_ingest, resource)

**File:** `src/linus/tools/arxiv_ingest.py` lines 196–201.

`out.write(response.read())` slurps the entire HTTP response into memory before writing. For arXiv papers up to 100MB
(supplementary material), the Worker process briefly doubles its memory. The KnowledgeBase uses chunked writes for the
same reason; this tool drifted.

Also: the `urlopen` context manager is correctly used, BUT the `out.open("wb")` is in the **same `with`** clause —
`with urllib.request.urlopen(...) as response, dest.open("wb") as out:`. If the HTTP response raises during read but
before `out.close()`, Python will still close `out` (good) but leave a partial PDF on disk. Subsequent calls then see
`pdf_path.exists()` as truthy on line 308 and skip re-download — the partial PDF is reused indefinitely. There's no
size or sha verification gate.

**Recommendation:** stream in 64 KiB chunks (mirroring `_sha256_of`'s pattern), write to a `*.tmp` sibling, then
`os.replace` to the final path. Either rename-on-success or unlink-on-error. Use `shutil.copyfileobj(response, out,
length=1<<16)`.

---

### Low

#### L-1 — `_resolve_under_root` rejects NUL byte after Python OS layer raises (sandbox, edge case)

**File:** `src/linus/sandbox/fs.py` lines 80–85.

`Path("foo\x00bar").is_absolute()` returns False; `(self._root / "foo\x00bar").resolve()` raises `ValueError`
("embedded null byte"). The exception propagates as a bare `ValueError`, not a `PermissionError` — clients matching
on the documented `"PermissionError"` exception class will mistakenly treat the input as transient. Minor: probably
fine, but the docstring says "Raises ``PermissionError`` if ``path`` is absolute or resolves outside ``repo_root``" —
NUL bytes fall in neither bucket explicitly.

**Recommendation:** pre-validate `"\x00" not in path` and raise `PermissionError` with a clear message.

#### L-2 — Tool registry's `default` value is JSON-Schema-serialized unconditionally — non-JSON defaults break the schema (registry, edge case)

**File:** `src/linus/tools/registry.py` lines 193–196.

`schema["default"] = param.default` writes the literal Python default into the schema dict. If the default is a
non-JSON-serializable object (e.g. an enum member, a sentinel `object()`, a `Path`), the OpenAI-format envelope cannot
be JSON-encoded when `openai_specs()` is forwarded to Ollama. The current codebase only uses primitive defaults so
this never trips, but it's a footgun for the next `@tool` author.

**Recommendation:** wrap in a `json.dumps`-roundtrip during schema build; fall back to dropping the `default` key with
a warning if it doesn't serialize.

#### L-3 — `_try_specter2_embed` re-imports `SentenceTransformer` and `numpy` on every call (arxiv_ingest, performance)

**File:** `src/linus/tools/arxiv_ingest.py` lines 235–264.

Each invocation re-imports `sentence_transformers`, re-instantiates `SentenceTransformer("allenai/specter2_base")` (a
~440MB model load), and re-loads numpy. For a batch ingest, every paper pays the full model-load cost. The
KnowledgeBase pattern is a module-level singleton; this drift should be flagged.

**Recommendation:** cache the model at module scope using the same lazy-singleton pattern as `_get_adapter` in
`kb_tools.py`.

#### L-4 — Bare-`@tool` decorator races with `callable()` check on classes (registry, edge case)

**File:** `src/linus/tools/registry.py` lines 425–428.

`if func is not None and callable(func): return _decorate(func)` checks `callable(func)` — but classes are callable.
If someone writes `@tool` above a class definition, the decorator silently registers the class as a tool. There's no
`inspect.isfunction()` guard. This is unlikely to happen in practice, but the error message at dispatch time will
read like a confusing TypeError rather than a registration-time refusal.

**Recommendation:** add `inspect.isfunction(func) or inspect.ismethod(func)` check.

#### L-5 — `tests/test_paperqa_integration.py` swallows env-related failures as skips (tests, hygiene)

**File:** `tests/test_paperqa_integration.py` lines 32–80.

Three fixtures (`papers_dir`, `paperqa_available`, `ollama_reachable`) all `pytest.skip` on missing env. The module-
level `pytestmark = pytest.mark.integration` filters this from the hermetic run, so when a developer runs `pytest tests/`
WITHOUT setting the env vars, they see "skipped" — green output, zero coverage. The skip messages are clear, but the
canonical contract per CLAUDE.md is that integration tests fail loudly when prerequisites are missing in an
integration context. Mitigation could be a `--integration-strict` mode that converts skips to failures.

This is a deliberate design choice (see `test_server.py` for the alternative — explicit `assert ollama_reachable` to
fail loud). Both patterns exist in the suite. Recommendation: align them or document the divergence in the test
module's docstring.

---

### Informational

#### I-1 — Test `test_register_derives_name_from_module_and_qualname` documents but does not pin the truncation behavior

The test asserts `spec.name.endswith(".fn")` rather than a literal match — see M-2. Tightening the test to a literal
expectation would surface the import-layout sensitivity.

#### I-2 — `default_registry` is module-state-shared; `test_tool_decorator_bare_form_registers_to_default_registry` rescues with snapshot/restore (registry, hygiene)

The test uses a snapshot/restore pattern around the module-level `default_registry._tools` dict. Two concerns: (a) it
mutates the private `_tools` attribute directly; if the registry grows internal indexes (e.g. a name-to-schema cache),
they will go stale. (b) running multiple tests that mutate the default in parallel (Phase 3 multi-worker) would
collide. Not a real bug today, but the `clear()` method exists and would be cleaner; the snapshot/restore could move
into an autouse fixture.

---

## Remediation recommendations (priority order)

1. **H-1 + M-1** (sandbox): harden `SandboxFS.write` against parent-symlink and TOCTOU. Walk parents with `lstat`,
   reject any symlinked intermediate, use `O_NOFOLLOW` on the final write. Add unit tests:
   - parent of target is symlink to outside
   - target itself is symlink to outside (existing + dangling)
   - intermediate directory replaced with symlink between resolve and write
   - NUL byte in path
2. **M-3** (arxiv_ingest): document the pypdf decompression-limit posture in this module. Match KB inherited setting
   explicitly so the quirk note is honored.
3. **M-4** (arxiv_ingest): chunk the PDF download via `shutil.copyfileobj`; write through `.tmp` + `os.replace`.
4. **M-2** (registry): use full module path in the default tool name. Tighten the corresponding test to a literal match.
5. **L-1 through L-5**: small drift-fixes; bundle into a single follow-up PR.

## Confidence assessment

**High** on the registry / dispatch findings (M-2, L-2, L-4): the code is short, all paths were read end-to-end, and
the tests pin the documented behavior.

**Medium-high** on the sandbox findings (H-1, M-1, L-1): the symlink-TOCTOU class is well-understood and the
`SandboxFS.write` flow is short enough to reason about; I did not run a live exploit so the "may pass through
non-existent symlink" claim is reasoned, not measured. A Worker fix agent should write a focused exploit test before
landing the hardening to confirm the precise behavior.

**Medium** on the arxiv_ingest findings (M-3, M-4, L-3): library version of pypdf was not inspected; the
decompression-limit constant API may have shifted between pypdf 3.x and 4.x. The fix agent should pin the version in
use and consult the pypdf changelog.

**N/A** on async/concurrency: the registry is documented single-process Phase 2a; `/v1/tools/{name}/invoke` correctly
detects coroutine functions via `inspect.iscoroutinefunction` and routes sync tools through `asyncio.to_thread`. No
async/sync mismatch was found.

**N/A** on duplicate registration: the registry raises `ValueError` on duplicate-without-replace and the tests pin
both branches. No bug.

---

_Sweep performed read-only against base SHA `e1a07af`. Hermetic suite at base: 591 passed in 2.95 s. No production
code was modified by this sweep._
