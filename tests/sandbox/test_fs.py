"""Tests for src/linus/sandbox/fs.py — sandbox path-validation contract.

These tests intentionally cover the failure modes that defeated both Worker
passes in the 2026-05-16 first-loop experiment: absolute-path bypass,
``Path.resolve()``-anchored-to-CWD on relative paths, and ``startswith``
prefix-check defeated by ``..`` traversal.
"""

from pathlib import Path

import pytest

from linus.sandbox.fs import WRITE_ALLOWLIST, SandboxFS


@pytest.fixture
def sandbox(tmp_path: Path) -> SandboxFS:
    """SandboxFS rooted at a pytest ``tmp_path`` with allowlist dirs created."""
    for name in WRITE_ALLOWLIST:
        (tmp_path / name).mkdir()
    return SandboxFS(repo_root=tmp_path)


def test_write_then_read_roundtrip(sandbox: SandboxFS) -> None:
    sandbox.write("src/hello.txt", "hi there")
    assert sandbox.read("src/hello.txt") == "hi there"


def test_write_creates_parent_dirs(sandbox: SandboxFS) -> None:
    sandbox.write("docs/nested/deeply/note.md", "x")
    assert sandbox.read("docs/nested/deeply/note.md") == "x"


def test_write_outside_allowlist_raises(sandbox: SandboxFS) -> None:
    with pytest.raises(PermissionError, match="Tier 1 allowlist"):
        sandbox.write("modules/KnowledgeBase/forbidden.md", "x")


def test_write_absolute_path_raises(sandbox: SandboxFS) -> None:
    with pytest.raises(PermissionError, match="absolute paths"):
        sandbox.write("/etc/passwd", "x")


def test_write_traversal_escape_raises(sandbox: SandboxFS) -> None:
    with pytest.raises(PermissionError, match="escapes repo root"):
        sandbox.write("src/../../etc/passwd", "x")


def test_read_absolute_path_raises(sandbox: SandboxFS) -> None:
    with pytest.raises(PermissionError, match="absolute paths"):
        sandbox.read("/etc/passwd")


def test_read_traversal_escape_raises(sandbox: SandboxFS) -> None:
    with pytest.raises(PermissionError, match="escapes repo root"):
        sandbox.read("src/../../etc/passwd")


def test_read_anywhere_under_repo_root(sandbox: SandboxFS) -> None:
    """Read works for any subdir under repo_root, not just the write allowlist."""
    (sandbox.root / "modules").mkdir()
    (sandbox.root / "modules" / "x.txt").write_text("readable", encoding="utf-8")
    assert sandbox.read("modules/x.txt") == "readable"


def test_root_property_is_absolute_and_resolved(tmp_path: Path) -> None:
    fs = SandboxFS(repo_root=tmp_path)
    assert fs.root == tmp_path.resolve()
    assert fs.root.is_absolute()


def test_sandbox_uses_repo_root_not_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: pass-2 Worker bug was Path.resolve() anchoring to CWD."""
    other = tmp_path / "elsewhere"
    other.mkdir()
    (other / "src").mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "src").mkdir()
    monkeypatch.chdir(other)  # CWD is NOT under repo_root
    fs = SandboxFS(repo_root=repo_root)
    fs.write("src/x.txt", "hello")
    assert (repo_root / "src" / "x.txt").read_text() == "hello"
    assert not (other / "src" / "x.txt").exists()
