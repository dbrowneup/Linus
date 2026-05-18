"""Sandboxed filesystem helpers for Linus per SAFETY.md.

``SandboxFS`` enforces the Tier 0 / Tier 1 contract: read is permitted anywhere
under the resolved repo root; write is permitted only under the Tier 1
allowlist subdirectories (``src/``, ``benchmarks/``, ``experiments/``,
``docs/``). Path-traversal escapes are rejected by resolve-and-prefix check,
not string matching. Absolute input paths are rejected outright.

The repo root is resolved once at construction and stored as an absolute
Path. Subsequent operations join input paths under this stored root rather
than the current working directory, so SandboxFS is safe to use from a
Worker process whose CWD is unspecified.

This module is the canonical hand-written implementation; the 2026-05-16
first-loop experiment generated useful calibration data but the Worker
implementations did not pass the security gates. See
``experiments/first-loop-review.md``.
"""

from __future__ import annotations

from pathlib import Path

WRITE_ALLOWLIST: tuple[str, ...] = ("src", "benchmarks", "experiments", "docs")


class SandboxFS:
    """Path-validating wrapper around read and write under a fixed repo root.

    Reads are permitted anywhere under the resolved ``repo_root``. Writes are
    permitted only under one of the ``WRITE_ALLOWLIST`` subdirectories of
    ``repo_root``. Both read and write reject absolute input paths and paths
    that resolve outside the repo root after symlink and ``..`` normalization.
    """

    def __init__(self, repo_root: str | Path) -> None:
        """Resolve and store ``repo_root`` as the sandbox boundary."""
        self._root: Path = Path(repo_root).resolve()
        self._write_dirs: tuple[Path, ...] = tuple(self._root / name for name in WRITE_ALLOWLIST)

    @property
    def root(self) -> Path:
        """The resolved absolute path of the sandbox root."""
        return self._root

    def read(self, path: str) -> str:
        """Read a UTF-8 text file at ``path`` interpreted relative to repo root.

        Raises ``PermissionError`` if ``path`` is absolute or resolves outside
        ``repo_root``. Raises ``FileNotFoundError`` if the resolved path does
        not exist.
        """
        target = self._resolve_under_root(path)
        return target.read_text(encoding="utf-8")

    def write(self, path: str, data: str) -> None:
        """Write ``data`` as UTF-8 to ``path`` interpreted relative to repo root.

        Raises ``PermissionError`` if ``path`` is absolute, resolves outside
        ``repo_root``, or resolves outside the Tier 1 write allowlist. Creates
        parent directories under the allowlist as needed.
        """
        target = self._resolve_under_root(path)
        if not self._is_under_write_allowlist(target):
            raise PermissionError(
                f"write outside Tier 1 allowlist: {path!r} (allowlist: {WRITE_ALLOWLIST})"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data, encoding="utf-8")

    def _resolve_under_root(self, path: str) -> Path:
        """Resolve ``path`` against ``repo_root`` and require it to stay inside.

        The canonical sandbox check: ``(self._root / path).resolve()`` anchors
        the join under ``repo_root`` and normalizes ``..`` segments and
        symlinks. Calling ``Path(path).resolve()`` directly would anchor to the
        process CWD, which is the bug class that defeated the first-loop
        Worker's pass 2.
        """
        if Path(path).is_absolute():
            raise PermissionError(f"absolute paths not allowed: {path!r}")
        candidate = (self._root / path).resolve()
        if not candidate.is_relative_to(self._root):
            raise PermissionError(f"path escapes repo root: {path!r}")
        return candidate

    def _is_under_write_allowlist(self, candidate: Path) -> bool:
        return any(candidate.is_relative_to(d) for d in self._write_dirs)
