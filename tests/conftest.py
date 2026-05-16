"""Pytest conftest — ensure the worktree's ``src/`` is importable.

The repo's ``linus`` package is normally installed in editable mode via
``pip install -e .`` against the main checkout. When tests are run from a
worktree, the editable install still points at the main checkout's
``src/linus``, which is missing the in-flight code under test here. This
conftest inserts the worktree's own ``src`` at the front of ``sys.path``
so test runs always see the local code first.

The shim is harmless when run from the main checkout (the ``src`` path is
already first on ``sys.path`` in editable installs); it only changes
behavior in worktree runs. Once the editable install is regenerated against
a given worktree, this conftest is a no-op for that checkout.
"""

from __future__ import annotations

import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[1]
_src = _repo_root / "src"
if _src.exists():
    src_str = str(_src)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)
