## DEC-0051 — AgentReport: typed inter-agent message format

**Date:** 2026-05-06 **Status:** accepted

**Context.** Five systems in the corpus use typed structured outputs for inter-agent messages (TradingAgents, both
QuantAgents, WikiAutoGen, BioGuider, Sketch2Simulation). Kosmos uses shared state objects. The agentic-systems synthesis
distills the failure mode: free-text inter-agent messages drift as agent count and task complexity grow; typed messages
with a named rationale field are both human-readable and machine-queryable. Companion to DEC-0050 (Role). Closes **S10**.

**Decision.** Typed `AgentReport` is the canonical inter-agent message format for Phase 3+. Minimum schema:

```python
@dataclass
class AgentReport:
    task_id: str                      # links to the spawning task in the session store
    role_id: str                      # sending agent's Role (from DEC-0050)
    status: Literal["complete", "partial", "blocked", "error"]
    result: Any | None                # structured; type defined per task class; None for blocked/error
    rationale: str                    # free text — the ONLY free-text field
    evidence: list[str]               # citation keys / KB references / tool output ids
    timestamp: str                    # ISO-8601
```

Free text is confined to `rationale`. The `result` field is typed per task class (defined in task-class spec files, not
in the orchestrator). Workers always return an `AgentReport`; the orchestrator inspects `status` before deciding next
action (continue, retry, escalate to critic, or surface to Dan). `AgentReport` records are appended to the workgraph
JSONL session store (DEC-0026 shape) so the full inter-agent conversation is auditable after the fact.

`status: "partial"` is explicitly named to handle the common case where a Worker has useful intermediate output but
cannot complete — partial results are returned rather than swallowed, so the orchestrator can decide whether to chain
another Worker or surface to Dan.

**Consequence.** Inter-agent messages are inspectable, loggable, and diffable across runs. The `rationale` field
preserves explanation for human review without contaminating the structured result. The `evidence` list makes
KnowledgeBase and citation grounding mandatory in the message contract rather than optional in the implementation.
