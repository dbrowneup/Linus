"""Linus tool registry package — Phase 2a, Item 6.

This package owns the in-memory tool registry that the FastAPI orchestration
backend consults when it routes OpenAI-format tool calls to Python functions.

Design summary
--------------
- :class:`ToolRegistry` is a tiny dict-of-callables keyed by fully-qualified
  tool name (e.g. ``"linus.knowledge.search_papers"``). It records, for each
  tool, the callable, a JSON-Schema-shaped parameter definition derived from
  the function's type hints, and a short human description pulled from the
  docstring summary line.
- The :func:`tool` decorator registers a function on a registry (the
  module-level ``default_registry`` by default) and attaches the JSON-Schema
  metadata. Type hints drive the schema: ``str``, ``int``, ``float``,
  ``bool``, ``list[...]``, and ``dict[str, ...]`` are recognized; anything
  exotic falls back to ``{"type": "string"}`` so the model still gets *some*
  spec.
- The KB-backed tools (``linus.knowledge.search_papers`` and
  ``linus.knowledge.get_paper``) are registered eagerly when the
  ``linus.tools.kb_tools`` submodule is imported (which the registry's
  module-level import below triggers). Importing this package therefore
  guarantees the default registry is populated.

This is intentionally NOT MCP — Phase 3's MCP adoption (DEC-0018 + DEC-0045)
builds on top of this registry rather than replacing it. The OpenAI
tool-calling JSON format is the wire protocol the server already speaks;
keeping the in-process registry stable means MCP can later expose it as a
server without disturbing the callers.

See ``docs/specs/2026-05-12-linus-implementation-plan.md`` Item 6 for the
authoring scope and ``docs/specs/2026-05-12-linus-implementation-plan.md``
Item 5 for the upstream KB adapter scope this glues against.
"""

from linus.tools.registry import (
    ToolRegistry,
    ToolSpec,
    default_registry,
    tool,
)

# Eagerly populate the default registry with the KB-backed tools. The import
# has the side effect of running the @tool decorators in ``kb_tools.py``; we
# expose the module reference under a private name so ``from linus.tools
# import default_registry`` users get a populated registry without any
# explicit second import.
from linus.tools import kb_tools as _kb_tools  # noqa: F401
from linus.tools import arxiv_ingest as _arxiv_ingest  # noqa: F401

# Phase 2c — paper-qa integration. Importing the module triggers the four
# ``@tool``-decorated registrations (``paperqa.search``,
# ``paperqa.gather_evidence``, ``paperqa.answer``, ``paperqa.reset``). The
# module is intentionally side-effect-light at import time: paper-qa itself
# is imported lazily inside the tool callables so the hermetic test suite
# does not require the dependency to be installed.
from linus.knowledge import paperqa as _paperqa_tools  # noqa: F401

__all__ = [
    "ToolRegistry",
    "ToolSpec",
    "default_registry",
    "tool",
]
