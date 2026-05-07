# huginn (`huginn/huginn`)

## 1. Purpose and scope

Huginn is a self-hosted, event-driven automation platform — a private, Ruby-on-Rails IFTTT/Zapier alternative that
runs on your own server. Users compose DAGs of interconnected "Agents" that read the web, watch for events, and trigger
actions: scrape websites, track weather/Twitter trends, send email digests, integrate Slack/Twilio/JIRA, run Bash
commands, and chain Amazon Mechanical Turk workflows. For Linus, Huginn is a reference implementation of orchestration
patterns and trigger/action architecture, relevant for understanding how a local tool-composition backend might chain
user-defined workflows.

## 2. Architecture summary

Huginn is a conventional Rails monolith backed by MySQL/PostgreSQL. The core abstraction is the **Agent**: a stateful
object that consumes and emits `Event` objects as JSON payloads, propagated along a directed graph in a scheduler loop.
Each agent subclass (WeatherAgent, TwitterAgent, EmailAgent, etc.) implements `receive_events` and `create_events`. The
UI is server-rendered Rails; the database stores agent configs, events, and execution state. Agents can be packaged as
external gems (the `huginn_agent` gem provides the framework for third-party extensions). Testing uses rspec + Capybara
for acceptance specs in a headless browser. Deployment targets Docker, Heroku, OpenShift, or manual server installation.

## 3. What's reusable in Linus

The agent/event pattern is directly applicable: Linus orchestration can model tool chains as a DAG of agents that
emit/consume structured events. The gem-extensibility model is worth studying — allowing third-party tools to be
installed without forking core code is a design principle Linus will need as it grows beyond a single developer's
machine. Huginn's agent-to-agent wiring (via "receivers" and "sources") is a clean precedent for declaring dependencies
between Linus components. The multi-agent acceptance test suite (Capybara + headless browser) demonstrates how to test
complex, stateful workflows end-to-end — useful when Linus has multi-step tasks.

## 4. What's inspiration only

Huginn is purpose-built for end-user workflow automation with a rich built-in agent library. Linus is engineer-facing
and domain-specific to Dan's research/coding work. The Rails architectural decisions (monolith, server-rendered UI,
asset pipeline) don't fit Linus's headless+API-first design. Huginn's event scheduling loop and database-backed state
are production patterns, but Linus Phase 2 will likely use simpler in-memory DAG dispatch (workgraph's JSONL append-only
log is a lighter alternative).

## 5. What's incompatible or out of scope

Huginn is Ruby; Linus is Python. Neither language choice is portable to the other without a rewrite. Huginn's reliance
on a full database (MySQL/PostgreSQL) is heavier than Linus Phase 2a needs; see CLAUDE.md's recommendation for workgraph
JSONL session store. The user-facing workflow builder UI is out of scope for Linus (which assumes Dan codes his own
task specs in Python or YAML).

## 6. Recommendation: **Study (before Phase 2a orchestration design)**

Before finalizing Linus's session-store shape and agent dispatch mechanism, read Huginn's agent-wiring code and event
loop. The DAG pattern is sound; the gem-extensibility model is a good north star. Then document the differences in
CLAUDE.md (Python-specific version of the Huginn-style pattern).

## 7. Questions for Dan

- **Multi-agent workflows as first-class.** Huginn treats agent DAGs as first-class objects with a UI for composition.
  Should Linus Phase 2a assume multi-step task specs from the start, or is single-agent-per-task adequate until Phase 3
  demands parallelism? _Resolved (DEC-0050, DEC-0051, see [answered-questions.md](../questions/answered-questions.md)): Role as first-class type and typed AgentReport are Phase 3 spawner primitives; Phase 2a uses single-agent dispatch; multi-step fan-out deferred to Phase 3._
- **Event schema design.** Huginn's events are bare JSON; type safety is implicit. When Linus chains multiple workers,
  should event types be schema-defined (Pydantic models, Protocol Buffers) or duck-typed? _Resolved (DEC-0051, see [answered-questions.md](../questions/answered-questions.md)): Typed AgentReport with required fields (task_id, role_id, status, result, rationale, evidence, timestamp) is the inter-agent message format; Pydantic-typed, appended to workgraph JSONL._
- **Persistent state for long-running workflows.** Huginn uses the database; Linus Phase 2a uses a JSONL DAG log. How
  many intermediate states should Linus log per workflow to enable debugging and resume-after-crash? _Partially resolved (see [answered-questions.md](../questions/answered-questions.md)): Workgraph JSONL append-only DAG is the committed Phase 2a session-store shape; leaf + summary hybrid schema per DEC-0039; exact per-workflow log granularity not yet specified._

---

_Repo-note written 2026-05-05._
