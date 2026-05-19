"""Linus agent primitives.

This package houses the minimal agent-spawner contract that lets a
caller dispatch N parallel scoped Worker calls (each a single Ollama
chat completion) and merge the results.

The Archimedes project (submodule consumer of Linus) treats this
contract as the engine of its strategy-fusion / novelty differentiator:
N candidate strategy generators run in parallel, each scoped to a
different prompt / approach, and the merged result feeds the
selection-bias-corrected admission gate. Linus ships the primitive;
Archimedes adds domain logic on top.

Public surface:

- :class:`AgentTask` — one scoped Worker invocation
- :class:`AgentResult` — outcome of one task (content, latency, error)
- :func:`spawn_agents` — async dispatch function
"""

from linus.agents.spawner import AgentResult, AgentTask, spawn_agents

__all__ = [
    "AgentResult",
    "AgentTask",
    "spawn_agents",
]
