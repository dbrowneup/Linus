"""Tests for :mod:`linus.sandbox.fs` — the Tier 0 / Tier 1 sandbox boundary.

``SandboxFS`` is the security pillar that enforces the SAFETY.md sandbox
contract: read anywhere under repo root, write only under the Tier 1
allowlist (``src/``, ``benchmarks/``, ``experiments/``, ``docs/``), and
reject path-traversal escapes via resolve-and-prefix check (not string
matching). Before this file the module had zero tests; given the security
posture, every branch deserves explicit coverage.

The suite is fully hermetic — every test gets an isolated ``tmp_path`` for
its sandbox root. No network, no Ollama, no external dependencies.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from linus.sandbox import WRITE_ALLOWLIST, SandboxFS

# ── Construction + root property ───────────────────────────────────────────


def test_init_resolves_repo_root_to_absolute_path(tmp_path: Path) -> None:
    """__init__ must resolve repo_root to an absolute Path so subsequent
    operations are CWD-independent (the bug class that defeated first-loop
    Worker pass 2)."""
    sandbox = SandboxFS(tmp_path)
    assert sandbox.root.is_absolute()
    assert sandbox.root == tmp_path.resolve()


def test_init_accepts_str_path(tmp_path: Path) -> None:
    """repo_root may be a str or Path (typed as str | Path)."""
    sandbox = SandboxFS(str(tmp_path))
    assert sandbox.root == tmp_path.resolve()


def test_root_property_returns_resolved_path(tmp_path: Path) -> None:
    """The ``root`` property exposes the resolved sandbox boundary."""
    sandbox = SandboxFS(tmp_path)
    assert isinstance(sandbox.root, Path)
    assert sandbox.root == tmp_path.resolve()


# ── read happy path + rejection cases ──────────────────────────────────────


def test_read_returns_utf8_content(tmp_path: Path) -> None:
    """read() returns UTF-8 text from a file under repo_root."""
    sandbox = SandboxFS(tmp_path)
    target = tmp_path / "hello.txt"
    target.write_text("héllo wörld", encoding="utf-8")
    assert sandbox.read("hello.txt") == "héllo wörld"


def test_read_supports_nested_paths(tmp_path: Path) -> None:
    """read() handles nested relative paths under repo_root."""
    sandbox = SandboxFS(tmp_path)
    nested = tmp_path / "a" / "b" / "c.txt"
    nested.parent.mkdir(parents=True)
    nested.write_text("nested", encoding="utf-8")
    assert sandbox.read("a/b/c.txt") == "nested"


def test_read_rejects_absolute_path(tmp_path: Path) -> None:
    """Absolute input paths are rejected outright (no resolve attempted)."""
    sandbox = SandboxFS(tmp_path)
    with pytest.raises(PermissionError, match="absolute paths not allowed"):
        sandbox.read("/etc/passwd")


def test_read_rejects_dotdot_escape(tmp_path: Path) -> None:
    """``..`` segments that resolve outside repo_root must raise."""
    sandbox = SandboxFS(tmp_path)
    with pytest.raises(PermissionError, match="path escapes repo root"):
        sandbox.read("../etc/passwd")


def test_read_rejects_deep_dotdot_escape(tmp_path: Path) -> None:
    """Multi-level ``..`` chains are rejected — the resolve normalization
    catches the escape regardless of nesting depth."""
    sandbox = SandboxFS(tmp_path)
    with pytest.raises(PermissionError, match="path escapes repo root"):
        sandbox.read("a/b/../../../etc/passwd")


def test_read_rejects_symlink_escape(tmp_path: Path) -> None:
    """A symlink inside repo_root that targets outside must be rejected:
    resolve() follows the symlink, and the resulting path falls outside
    repo_root so the prefix check trips."""
    # Build an outside dir + file
    outside = tmp_path.parent / "sandbox-fs-outside-dir"
    outside.mkdir(exist_ok=True)
    secret = outside / "secret.txt"
    secret.write_text("classified", encoding="utf-8")

    # Create the sandbox in a subdirectory so we can place a symlink inside it
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    link = repo_root / "evil_link"
    try:
        os.symlink(secret, link)
    except OSError:
        pytest.skip("symlinks not supported on this platform")

    sandbox = SandboxFS(repo_root)
    try:
        with pytest.raises(PermissionError, match="path escapes repo root"):
            sandbox.read("evil_link")
    finally:
        # Cleanup the outside dir we created
        secret.unlink(missing_ok=True)
        outside.rmdir()


def test_read_missing_file_raises_filenotfound(tmp_path: Path) -> None:
    """A non-existent path INSIDE repo_root reaches read_text and surfaces
    FileNotFoundError (not PermissionError) — the sandbox check passes but
    the OS call fails. This distinguishes "policy" vs "I/O" failures."""
    sandbox = SandboxFS(tmp_path)
    with pytest.raises(FileNotFoundError):
        sandbox.read("does-not-exist.txt")


# ── write happy path + rejection cases ─────────────────────────────────────


def test_write_succeeds_under_src_allowlist(tmp_path: Path) -> None:
    """write() succeeds for a path under ``src/`` (allowlisted)."""
    sandbox = SandboxFS(tmp_path)
    (tmp_path / "src").mkdir()
    sandbox.write("src/foo.txt", "hello")
    assert (tmp_path / "src" / "foo.txt").read_text(encoding="utf-8") == "hello"


@pytest.mark.parametrize("allowlist_dir", ["src", "benchmarks", "experiments", "docs"])
def test_write_succeeds_under_each_allowlist_dir(tmp_path: Path, allowlist_dir: str) -> None:
    """Every directory in WRITE_ALLOWLIST must accept writes."""
    sandbox = SandboxFS(tmp_path)
    sandbox.write(f"{allowlist_dir}/probe.txt", "ok")
    assert (tmp_path / allowlist_dir / "probe.txt").read_text(encoding="utf-8") == "ok"


def test_write_creates_nested_parent_directories(tmp_path: Path) -> None:
    """Writing to ``src/new/nested/file.txt`` creates the parent chain."""
    sandbox = SandboxFS(tmp_path)
    sandbox.write("src/new/nested/file.txt", "deep")
    target = tmp_path / "src" / "new" / "nested" / "file.txt"
    assert target.read_text(encoding="utf-8") == "deep"
    assert target.parent.is_dir()


def test_write_writes_utf8(tmp_path: Path) -> None:
    """write() round-trips non-ASCII UTF-8 content."""
    sandbox = SandboxFS(tmp_path)
    sandbox.write("docs/uni.txt", "λ — π — 漢字")
    assert (tmp_path / "docs" / "uni.txt").read_text(encoding="utf-8") == "λ — π — 漢字"


def test_write_rejects_absolute_path(tmp_path: Path) -> None:
    """Absolute paths are rejected by the same gate as read()."""
    sandbox = SandboxFS(tmp_path)
    with pytest.raises(PermissionError, match="absolute paths not allowed"):
        sandbox.write("/tmp/escape.txt", "nope")


def test_write_rejects_dotdot_escape(tmp_path: Path) -> None:
    """``..`` escapes are caught before the allowlist check."""
    sandbox = SandboxFS(tmp_path)
    with pytest.raises(PermissionError, match="path escapes repo root"):
        sandbox.write("../escape.txt", "nope")


def test_write_rejects_path_outside_allowlist(tmp_path: Path) -> None:
    """A path INSIDE repo_root but OUTSIDE the Tier 1 allowlist
    (e.g., ``modules/foo.txt``) must raise — this is the core Tier 1
    contract that distinguishes read scope from write scope."""
    sandbox = SandboxFS(tmp_path)
    with pytest.raises(PermissionError, match="outside Tier 1 allowlist"):
        sandbox.write("modules/foo.txt", "nope")


def test_write_rejects_random_top_level_dir(tmp_path: Path) -> None:
    """Any non-allowlist top-level directory is rejected, not just the
    known submodule paths."""
    sandbox = SandboxFS(tmp_path)
    with pytest.raises(PermissionError, match="outside Tier 1 allowlist"):
        sandbox.write("some-random-dir/x.txt", "nope")


def test_write_rejects_repo_root_file(tmp_path: Path) -> None:
    """A file directly at repo_root (not under any allowlist subdir) is
    rejected — only ALLOWLIST subdirs accept writes."""
    sandbox = SandboxFS(tmp_path)
    with pytest.raises(PermissionError, match="outside Tier 1 allowlist"):
        sandbox.write("README.md", "nope")


# ── WRITE_ALLOWLIST regression guard ───────────────────────────────────────


def test_write_allowlist_constant_is_exact() -> None:
    """Regression guard: the Tier 1 allowlist must be exactly these four
    directories, in this order. Any accidental edit (adding ``modules`` or
    dropping ``benchmarks``) should fail this test loudly. SAFETY.md is the
    source of truth — coordinate any change there first."""
    assert WRITE_ALLOWLIST == ("src", "benchmarks", "experiments", "docs")


# ── Symlink TOCTOU + escape hardening (#105 H-1 + M-1) ─────────────────────
#
# The four tests below pin the 2026-05-21 fix for the SandboxFS.write TOCTOU
# + dangling-symlink escape. Policy summary: write refuses ANY symlink on
# the target path — at the final component or any ancestor — regardless of
# where the symlink ultimately resolves. "Narrower is safer" for v0.5.0;
# a future tier may relax to "symlinks allowed if their target is also
# under the allowlist," but not yet.


def test_write_refuses_when_target_is_symlink_to_outside(tmp_path: Path) -> None:
    """A symlink at the write target whose link-target is OUTSIDE repo_root
    must be refused. The pre-fix bug: ``resolve(strict=False)`` returned the
    outside path which then failed prefix-check (safe), BUT a dangling
    variant (link target does not yet exist) returned the lexical inside
    path which passed prefix-check and let ``write_text`` follow the link
    at I/O time, creating the file outside the sandbox."""
    repo_root = tmp_path / "repo"
    (repo_root / "src").mkdir(parents=True)

    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    outside_target = outside_dir / "stolen.txt"
    # Note: outside_target does NOT exist yet — this is the dangling case
    # that triggered M-1 (resolve(strict=False) accepts the lexical path).

    link = repo_root / "src" / "escape"
    try:
        os.symlink(outside_target, link)
    except OSError:
        pytest.skip("symlinks not supported on this platform")

    sandbox = SandboxFS(repo_root)
    with pytest.raises(PermissionError):
        sandbox.write("src/escape", "leaked")

    # Defense in depth: confirm no file was created outside.
    assert not outside_target.exists(), "write must not have followed the symlink"


def test_write_refuses_when_parent_component_is_symlink(tmp_path: Path) -> None:
    """A symlink at an INTERMEDIATE parent of the write target must be
    refused. This is the H-1 case: ``_resolve_under_root`` may return a
    lexically-clean path under root, but the parent is a symlink to outside
    and ``mkdir(parents=True)``/``write_text`` would extend the host tree."""
    repo_root = tmp_path / "repo"
    (repo_root / "src").mkdir(parents=True)

    outside_dir = tmp_path / "outside_dir"
    outside_dir.mkdir()
    # outside_dir is empty — when write tries to mkdir + write under the
    # symlink, it would create files inside outside_dir if not refused.

    sneaky_link = repo_root / "src" / "sneaky"
    try:
        os.symlink(outside_dir, sneaky_link)
    except OSError:
        pytest.skip("symlinks not supported on this platform")

    sandbox = SandboxFS(repo_root)
    with pytest.raises(PermissionError):
        sandbox.write("src/sneaky/file.txt", "leaked")

    # Defense in depth: nothing must have been written under outside_dir.
    assert list(outside_dir.iterdir()) == [], "write must not have followed the parent symlink"


def test_write_refuses_when_target_is_symlink_to_inside_allowed_dir(tmp_path: Path) -> None:
    """Even a "legitimate" symlink whose target is INSIDE an allowed
    directory is refused on write. Policy for v0.5.0 is "no symlinks on
    write," period — narrower is safer until we have a tier that explicitly
    relaxes this. The test pins that policy so a future relaxation has to
    be an explicit, documented decision."""
    repo_root = tmp_path / "repo"
    real_dir = repo_root / "src" / "real-dir"
    real_dir.mkdir(parents=True)

    inner_link = repo_root / "src" / "inner"
    try:
        os.symlink(real_dir, inner_link)
    except OSError:
        pytest.skip("symlinks not supported on this platform")

    sandbox = SandboxFS(repo_root)
    with pytest.raises(PermissionError):
        sandbox.write("src/inner/file.txt", "data")

    # Nothing was written through the link.
    assert not (real_dir / "file.txt").exists()


def test_write_creates_real_directory_chain(tmp_path: Path) -> None:
    """Positive control: write to a deeply-nested path under an allowlist
    directory creates ALL intermediate dirs as REAL directories (not
    symlinks) and all under repo_root. Confirms the hardened ``_safe_mkdir``
    happy path."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    sandbox = SandboxFS(repo_root)
    sandbox.write("src/new/nested/deep/file.txt", "ok")

    expected_chain = [
        repo_root / "src",
        repo_root / "src" / "new",
        repo_root / "src" / "new" / "nested",
        repo_root / "src" / "new" / "nested" / "deep",
    ]
    for d in expected_chain:
        assert d.is_dir(), f"{d!r} must exist as a directory"
        assert not d.is_symlink(), f"{d!r} must be a real directory, not a symlink"
        assert d.is_relative_to(repo_root.resolve()), f"{d!r} must be under repo_root"

    target = repo_root / "src" / "new" / "nested" / "deep" / "file.txt"
    assert target.read_text(encoding="utf-8") == "ok"
    assert not target.is_symlink()


# ── NUL byte rejection (#105 L-1, bundled with H-1 + M-1 fix) ──────────────


def test_resolve_rejects_nul_byte_with_permissionerror(tmp_path: Path) -> None:
    """A NUL byte in the input path must raise ``PermissionError`` (not the
    bare ``ValueError`` that Python's OS layer raises on the embedded null).
    Clients matching on the documented exception class need a consistent
    signal — see the bug sweep L-1 finding."""
    sandbox = SandboxFS(tmp_path)
    with pytest.raises(PermissionError, match="NUL byte"):
        sandbox.write("src/foo\x00bar.txt", "nope")
    with pytest.raises(PermissionError, match="NUL byte"):
        sandbox.read("foo\x00bar.txt")
