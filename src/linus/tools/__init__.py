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

from typing import Any

# Phase 2c — paper-qa integration. Importing the module triggers the four
# ``@tool``-decorated registrations (``paperqa.search``,
# ``paperqa.gather_evidence``, ``paperqa.answer``, ``paperqa.reset``). The
# module is intentionally side-effect-light at import time: paper-qa itself
# is imported lazily inside the tool callables so the hermetic test suite
# does not require the dependency to be installed.
from linus.knowledge import paperqa as _paperqa_tools  # noqa: F401
from linus.tools import arxiv_ingest as _arxiv_ingest  # noqa: F401

# Eagerly populate the default registry with the KB-backed tools. The import
# has the side effect of running the @tool decorators in ``kb_tools.py``; we
# expose the module reference under a private name so ``from linus.tools
# import default_registry`` users get a populated registry without any
# explicit second import.
from linus.tools import kb_tools as _kb_tools  # noqa: F401
from linus.tools.registry import (
    ToolRegistry,
    ToolSpec,
    default_registry,
    tool,
)


# Phase 2c — rigor gate (DEC-0059). Registers the ``rigor.check`` tool that
# wraps :func:`linus.knowledge.rigor.check_grounding`. The tool is callable
# via the existing ``POST /v1/tools/rigor.check/invoke`` route and accepts
# a ``claim`` dict argument; sane KB-backed defaults wire it to the
# production paper + entity backends when ``use_kb_paper_lookup`` and
# ``use_entity_lookup`` are left True. The registration lives here (rather
# than inside :mod:`linus.knowledge.rigor`) so the rigor module itself
# stays free of registry-side-effect imports — keeps the gate's contract
# surface clean of orchestrator coupling.
@tool(
    name="rigor.check",
    description=(
        "Run the grounding gate on a Worker output claim. Resolves citations "
        "against the KnowledgeBase metadata DB and entities against the "
        "best-available reference store (KB-derived if importable, builtin "
        "stub otherwise). Returns the serialized RigorResult shape."
    ),
)
def rigor_check(
    claim: dict[str, Any],
    use_kb_paper_lookup: bool = True,
    use_entity_lookup: bool = True,
) -> dict[str, Any]:
    """Invoke :func:`linus.knowledge.rigor.check_grounding` with sane defaults.

    The ``claim`` argument follows the :data:`~linus.knowledge.rigor.ClaimDict`
    shape: ``rationale``, ``citations`` (provenance dicts), ``entities``,
    optional ``confidence``. The two flags toggle backend resolution —
    ``use_kb_paper_lookup=False`` skips citation grounding (the gate
    surfaces a ``backend_unavailable`` warning); ``use_entity_lookup=False``
    likewise for entity grounding. Returns the JSON-shaped
    :func:`~linus.knowledge.rigor.result_to_dict` payload.
    """
    from linus.knowledge.paperqa import _resolve_entity_backend, _resolve_paper_backend
    from linus.knowledge.rigor import check_grounding, result_to_dict

    papers = _resolve_paper_backend() if use_kb_paper_lookup else None
    entities = _resolve_entity_backend() if use_entity_lookup else None

    result = check_grounding(claim, papers=papers, entities=entities)
    return result_to_dict(result)


__all__ = [
    "ToolRegistry",
    "ToolSpec",
    "default_registry",
    "tool",
]
