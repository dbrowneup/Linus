"""Linus — personal AI orchestration backend for Apple Silicon.

The product is the orchestration layer: a harness-agnostic backend that exposes an
OpenAI-compatible endpoint, provides Linus-native tools (knowledge search, sandboxed
shell, parallel agents), enforces sandbox policy, and maintains durable state.

Front-ends (VS Code, openclaw, LM Studio, future native Linus app) are interchangeable
UIs that talk to this backend.

See CLAUDE.md and ARCHITECTURE.md at the repo root.
"""

from linus.__about__ import __version__

__all__ = ["__version__"]
