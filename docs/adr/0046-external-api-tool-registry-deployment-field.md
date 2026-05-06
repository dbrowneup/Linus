## DEC-0046 — external_api_tool: deployment field in registry schema; Phase 7 execution path

**Date:** 2026-05-06 **Status:** accepted

**Context.** Phase 7 biology skills will need to call external APIs (mCSM-metal, AlphaGenome API, Evo 2 hosted
endpoint). The generative-biology synthesis recommends treating external tools as first-class Workers with uniform
orchestration patterns. Algorithm check: the "external tools can be registered" requirement cannot be deleted — Phase 7
genuinely needs it. The "implement now" portion can be deleted. What the Algorithm leaves: one `deployment` field in the
tool registry data model. Without this field, the registry silently assumes all tools are local, creating a schema
migration and design-debt paydown in Phase 7. Closes **S4**.

**Decision.** Add a `deployment` field to the tool registry data model, typed as one of `"local" | "mcp" |
"external_api"`. Phase 2a activates `"local"` and `"mcp"` variants; `"external_api"` is a named stub with no execution
path. No execution code for `external_api` is written until Phase 7 needs it. The registry schema records this field
from Phase 2a to prevent the "registry assumes all tools are local" assumption hardening into structural debt. Phase 7
implementation: add the `external_api` execution path (HTTP request + auth header + response parsing) when the first
Phase 7 biology skill needs it.

**Consequence.** The tool registry is forward-compatible without Phase 7 implementation work today. A single enum field
in a Pydantic model or dataclass is the total Phase 2a cost. Phase 7 activation is a new method on the executor, not a
schema migration.
