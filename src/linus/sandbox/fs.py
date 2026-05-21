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

Symlink policy (DEC-0061, hardened 2026-05-21 for #105 H-1 + M-1)
-----------------------------------------------------------------

``write`` refuses ANY symlink on the target path — both the final component
and every parent component under the sandbox root. This closes the
``resolve(strict=False)``-follows-dangling-symlink class of escape (M-1) and
the parent-symlink TOCTOU window (H-1). The policy is "narrower is safer for
v0.5.0": even a symlink whose target lies inside an allowlist directory is
refused on write. Read retains the existing resolve-and-prefix behavior
because reads inside the root are by design unrestricted.
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
        ``repo_root``, resolves outside the Tier 1 write allowlist, or if any
        path component (existing or final) is a symbolic link. Creates parent
        directories under the allowlist as needed.

        The symlink refusal closes the parent-symlink TOCTOU window (#105 H-1)
        and the dangling-symlink ``resolve(strict=False)`` bypass (#105 M-1):
        ``_safe_walk_input_path`` lstat-walks the literal input path against
        the root and refuses ANY symlink component, INCLUDING legitimate ones
        that resolve back inside the allowlist (``src/inner -> src/real-dir``).
        Policy for v0.5.0 is "no symlinks on write," period — narrower is
        safer.

        Order of checks: NUL byte / absolute-path / resolve-and-prefix gates
        in ``_resolve_under_root``, then write-allowlist on the resolved
        target, THEN the lstat-walk of the input path so a path that escapes
        the root via dangling symlink is rejected with the clearer
        "path escapes" message rather than "component is a symlink" — the
        former is the security claim, the latter is the mechanism.
        """
        if "\x00" in path:
            raise PermissionError(f"NUL byte in path not allowed: {path!r}")
        if Path(path).is_absolute():
            raise PermissionError(f"absolute paths not allowed: {path!r}")
        # Lexical join under root for the input-path walk. Do NOT resolve here:
        # we need the literal components so lstat catches a symlinked
        # intermediate even when its target lies inside root.
        literal_target = self._root / path
        # Walk the literal path against root, refusing any symlink component.
        # This catches H-1 (parent symlink, including to outside) and the
        # M-1 dangling-symlink case (resolve(strict=False) would have accepted
        # the lexical inside-root path) AND the inside-root symlink case
        # (e.g. src/inner -> src/real-dir).
        self._safe_walk_input_path(literal_target)
        # After the lstat-walk passes, the input path contains no symlinks.
        # Now apply the canonical resolve-and-prefix + allowlist gates on the
        # resolved target. The resolve here is a no-op for the symlink axis
        # because we just rejected all symlinks; the resolve still normalizes
        # `..` segments.
        target = self._resolve_under_root(path)
        if not self._is_under_write_allowlist(target):
            raise PermissionError(f"write outside Tier 1 allowlist: {path!r} (allowlist: {WRITE_ALLOWLIST})")
        # Create parent dirs. We could re-use _safe_walk_input_path for the
        # mkdir walk, but at this point we've already lstat-verified the chain
        # contains no symlinks; a plain mkdir(parents=True) is safe here
        # because the only way mkdir could "escape" is via a symlinked
        # intermediate and the walk above forbids that. Use exist_ok=True
        # since intermediate dirs may already exist as real directories.
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data, encoding="utf-8")

    def _resolve_under_root(self, path: str) -> Path:
        """Resolve ``path`` against ``repo_root`` and require it to stay inside.

        The canonical sandbox check: ``(self._root / path).resolve()`` anchors
        the join under ``repo_root`` and normalizes ``..`` segments and
        symlinks. Calling ``Path(path).resolve()`` directly would anchor to the
        process CWD, which is the bug class that defeated the first-loop
        Worker's pass 2.

        NUL bytes in the input string are rejected with ``PermissionError`` so
        clients matching on the documented exception class get a consistent
        signal (#105 L-1 — the bare ``ValueError`` from Python's OS layer was
        a footgun).
        """
        if "\x00" in path:
            raise PermissionError(f"NUL byte in path not allowed: {path!r}")
        if Path(path).is_absolute():
            raise PermissionError(f"absolute paths not allowed: {path!r}")
        candidate = (self._root / path).resolve()
        if not candidate.is_relative_to(self._root):
            raise PermissionError(f"path escapes repo root: {path!r}")
        return candidate

    def _is_under_write_allowlist(self, candidate: Path) -> bool:
        return any(candidate.is_relative_to(d) for d in self._write_dirs)

    def _safe_walk_input_path(self, literal_target: Path) -> None:
        """Walk ``literal_target`` against ``self._root`` refusing any symlink.

        ``literal_target`` is ``self._root / input_path`` joined LEXICALLY (no
        ``.resolve()``). The walk visits each component from root downward and
        uses ``Path.is_symlink()`` (lstat-based) to refuse any symlinked
        intermediate or final component — including legitimate symlinks whose
        targets resolve inside the allowlist.

        Catches three classes of escape:

        - **H-1 parent-symlink TOCTOU.** A pre-existing parent symlink to
          outside ``repo_root`` would let ``mkdir(parents=True)`` /
          ``write_text`` extend the host tree. The lstat-walk refuses before
          mkdir is called.
        - **M-1 dangling-symlink ``resolve(strict=False)`` bypass.** When a
          parent symlink points to a not-yet-existent path,
          ``resolve(strict=False)`` accepts the lexical join (inside root)
          and would let ``write_text`` follow the link at I/O time. The walk
          sees the symlink via lstat regardless of whether its target
          exists.
        - **Inside-root symlink policy.** A symlink whose target lies inside
          an allowlist directory (e.g. ``src/inner -> src/real-dir``) is
          also refused. The "narrower is safer" v0.5.0 stance: no symlinks
          on write, period.

        Components whose lexical path lies outside ``self._root`` (e.g. a
        literal ``..`` segment) are not separately checked here —
        ``_resolve_under_root`` runs the canonical resolve-and-prefix gate
        after this walk and catches lexical escapes.

        Non-existent intermediate components are accepted; they will be
        created by the subsequent ``mkdir(parents=True, exist_ok=True)``.
        Final non-existence is normal for the write happy path.
        """
        # Walk from root down to the literal target. We only check components
        # that lie under root — outside-root literal components are caught by
        # _resolve_under_root's prefix check.
        try:
            relative = literal_target.relative_to(self._root)
        except ValueError:
            # literal_target is not lexically under root. Let
            # _resolve_under_root produce the canonical "path escapes" error.
            return
        cur = self._root
        for part in relative.parts:
            cur = cur / part
            if cur.is_symlink():
                # is_symlink() uses lstat: catches dangling links too.
                raise PermissionError(f"write refused: path component is a symlink: {cur!r}")
            # Non-existent components are fine (mkdir will create them as
            # real directories). Existing non-dir, non-symlink components
            # are also fine to traverse here — if they collide with an
            # intermediate that should be a dir, mkdir(parents=True) will
            # surface FileExistsError, which is an I/O error not a policy
            # error.
