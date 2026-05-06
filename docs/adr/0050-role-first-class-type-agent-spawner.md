## DEC-0050 — Role as a first-class type in the Phase 3 agent spawner

**Date:** 2026-05-06 **Status:** accepted

**Context.** Five systems in the corpus use explicit Role types for multi-agent coordination (TradingAgents,
BioGuider, Sketch2Simulation, HKUST QuantAgent, WikiAutoGen). The agentic-systems synthesis distills the pattern:
systems with explicit Roles are inspectable at rest and at runtime; systems without them drift as agent count grows.
Kosmos's two-role minimalism (Planner + Executor) is the only counter-data-point and applies only to two-agent systems.
The Phase 3 spawner design — Role + typed AgentReport + validation gates + investigation memory — needs this decision
before the spawner ships. Closes **S9**.

**Decision.** Role is a first-class Python type in the Phase 3 agent spawner. Minimum schema:

```python
@dataclass
class Role:
    role_id: str                      # unique identifier, e.g. "literature_reviewer"
    capability_set: list[str]         # tool ids this role is authorized to call
    memory_access_tier: str           # "read_all" | "read_session" | "read_own"
    critic_eligible: bool             # may this role serve as a critic/reviewer for others?
```

Role is serializable (JSON or YAML for spec files; Pydantic model in the orchestration layer) so Roles can be defined
in static files, versioned in git, and inspected without running the spawner. The orchestrator assigns each Worker a
Role at instantiation and routes tasks by Role, not by arbitrary Worker identity. The capability_set field provides the
enforcement surface for sandbox policy (DEC-0024 / SAFETY.md): a Worker cannot call tools outside its Role's
capability_set regardless of what the model requests.

The four-field minimum is intentionally narrow. Fields are added as Phase 3 design firms up; the minimum is sufficient
to wire routing, memory access, and critic-tier logic.

**Consequence.** Multi-agent systems are inspectable at rest (Role specs in YAML) and at runtime (Role objects in the
session store, cross-referenceable to AgentReport records from DEC-0051). The Role schema also provides the enforcement
surface for the sandbox policy, tightening the supply-chain security posture (DEC-0024) into multi-agent workflows.
