# AgentPrometheus (`chuan-gyld/AgentPrometheus`)

## 1. Purpose and scope

Agent Prometheus (chuan-gyld/AgentPrometheus; Python + Docker; license unspecified in the README, requires
investigation; status: active development) is an open-source AI workspace runtime built around one architectural rule:
**"The system executes. The AI consults."** The runtime handles all deterministic operational work — evidence
collection, file filtering, diagnostics, task state, logs, approvals, patch safety — and the LLM receives a compact
evidence packet and returns structured advice or small proposed changes. The design intent is to make AI assistance
usable with **fast, cheaper, or less intelligent models** because the hardest operational work is done by code before
the model is asked to reason.

The repo's READMEs (a `README.md` and a substantial set of accompanying capability docs — `SYSTEM_ARCHITECTURE.md`,
`USAGE_GUIDE.md`, `AGENT_ABILITIES.md`, `HONEST_ABILITIES.md`, `API_ORCHESTRATION.md`, `CONSULTANT_MODE.md`,
`HARDWARE_SPECS.md`, `INSTALL.md`, `REMOTE_CONTROL.md`, `SPEC_TEMPLATE.md`, `PROMETHEUS_LOG.md`) describe a vision of
combining the proven ideas from major open-source agent systems — AutoGPT continuous workflows, OpenHands developer
workspace control, CrewAI roles/tasks/crews, GPT Engineer spec-to-code planning, and a "Prometheus-style" evidence-packet /
safety-gate / patch-review core — without surrendering blind autonomous control to the model.

The repo's READMEs claim a verified working implementation of: Redis-backed task polling (`prometheus_tasks` queue);
workspace scanning with ignore rules; evidence packet generation; multi-language file diagnostics (Python via safe
`compile()` without `.pyc` writes); path protection (no edits outside workspace, no edits to `.git`/`node_modules`/`venv`/
`__pycache__`/`hive_mind_db`); OpenAI-compatible model calls via LiteLLM; Redis-backed logs and notifications;
kill-switch handling; Docker manager image installation from pinned `requirements.txt`; an upstream watcher GitHub Action
that opens a PR when AutoGPT/OpenHands/CrewAI/GPT Engineer designs change.

## 2. Architecture summary

```
User / Telegram / Dashboard
        |
        v
Redis task queue (prometheus_tasks)
        |
        v
Prometheus runtime
        |
        +--> scans workspace
        +--> filters unsafe/noisy paths
        +--> builds a repo map
        +--> selects relevant evidence
        +--> runs deterministic diagnostics
        +--> sends compact evidence to model through LiteLLM/OpenAI-compatible API
        +--> receives strict JSON plan / findings / patches
        +--> requests approval or applies patches only when explicitly enabled
        |
        v
Redis logs, notifications, reports, patch results
```

**Code components (per README's listing):**

- `prometheus_indexer.py` — workspace scanner with ignore rules.
- `prometheus_manager.py` — task orchestration / Redis queue polling.
- `prometheus_consultant.py` — the consultant runtime (LLM-facing).
- `prometheus_json.py` — strict JSON response handling.
- `prometheus_log.md` — design / change log.
- `vps_receiver.py` + `telegram_gateway.py` — remote interfaces.
- `vision_node.py` — vision capability stub.
- `memory_ledger.py` — task / state memory ledger.
- `microservices_architecture.png` + `SYSTEM_ARCHITECTURE.md` — visual + textual architecture documentation.

**Vendored upstream references:** the repo ships AutoGPT, OpenHands, crewAI, and gpt-engineer as **subdirectory clones**
(or submodules — README says "watched upstream repositories"). These are not invoked at runtime but are reference
implementations the upstream-watcher GitHub Action tracks for design changes.

**LLM client:** LiteLLM (consistent with Swarms; broader-stack convention).

**Persistence:** Redis-backed task queue + Redis-backed logs/notifications. No SQLite or file-system persistence
mentioned in the README.

**Containerization:** Docker Compose with manager image installation from pinned `requirements.txt`. CI workflow
(`.github/workflows/ci.yml`) for Python compile checks, dependency installation, Docker Compose config validation,
secret-hygiene scanning.

## 3. What's reusable in Linus

**The "system executes, AI consults" design rule is a Linus-discipline match.** The framing — deterministic code does
the hard operational work; LLM does the consulting — is precisely the **Maestro/Worker discipline applied at the
orchestration-layer level**. Linus's CLAUDE.md commits to this discipline at the Dan-versus-Worker level; AgentPrometheus
applies it at the Worker-versus-system level. For Linus's Phase 2a/2b orchestration backend, the discipline is portable:
the FastAPI server handles the deterministic work (request routing, audit logging, sandboxing, file filtering, evidence
packet construction); the Worker handles only the LLM call. The Phase 2a spec
([`docs/specs/phase2a-fastapi-server.md`](../specs/phase2a-fastapi-server.md), if it exists) should reference
AgentPrometheus's framing as the inspirational design rule.

**Evidence packet pattern.** The evidence-packet construction step — scan workspace, filter unsafe/noisy paths, build a
repo map, select relevant evidence, run deterministic diagnostics, then send a compact evidence packet to the model — is
a useful operational pattern for Linus's Phase 2/3 Worker dispatch. The Linus Worker registry per DEC-0050 should
require each Worker invocation to specify its evidence-packet construction step. The "context is a resource to manage,
not a capacity to fill" discipline (CLAUDE.md, DEC-0032) is the same insight applied at the in-context-window level;
AgentPrometheus applies it at the evidence-collection level.

**Strict JSON response handling.** The `prometheus_json.py` pattern — every consultant response must conform to a
strict JSON schema — is the typed-structured-prediction discipline (S25, BioReason-Pro convention) applied to a
software-engineering domain rather than a biology domain. The Linus Phase 7+ tool registry should adopt the same
pattern for all skill outputs (per DEC-0046).

**Path protection patterns.** The path-protection list (no edits outside workspace; no edits to `.git`,
`node_modules`, `venv`, `__pycache__`, `hive_mind_db`) is a portable set of defaults. The Linus SAFETY.md path-
protection logic could lift these directly with attribution.

**Redis-backed task queue as a Phase 2b session-store complement.** Linus commits to workgraph JSONL as the Phase 2a
session-store shape. Redis-backed task queueing is the **distributed multi-Worker complement** — for Phase 3 multi-agent
spawning where Workers run on separate processes or machines, Redis pub/sub or stream queues are the natural primitive.
AgentPrometheus's pattern is a usable v0 for the Phase 3 spawner's queue layer.

**Upstream-watcher GitHub Action for tracking reference implementations.** The upstream-watcher pattern — a CI job that
opens a PR when watched repositories change — is a portable engineering convention. Linus's repos/ directory tracks ~100
reference repos; an upstream-watcher action could surface meaningful changes to flagged repos (per the curation protocol
DEC-0025).

## 4. What's inspiration only

**License is unspecified in the visible README content.** A repo-notes entry that lacks license clarity needs license
investigation before any code lift. The Linus DEC-0024 supply-chain posture commits to license auditing for any external
code adoption.

**The vendored AutoGPT/OpenHands/crewAI/gpt-engineer subdirectories are not first-class dependencies.** They're
reference implementations the upstream-watcher tracks. Linus should treat them as **third-hand references** — read the
original upstream sources, not the AgentPrometheus copies, for any architectural insight.

**LiteLLM-only LLM client.** Same caveat as Swarms — Linus's Ollama-direct pattern conflicts with LiteLLM-wrapped
Ollama. The "system executes, AI consults" design rule is portable; the specific LLM-client choice is not.

**Redis as a hard dependency.** AgentPrometheus assumes Redis. Linus's Phase 2a backend currently doesn't require
Redis (workgraph JSONL is file-system-based). Adding Redis is a real infrastructure commitment that should be a
deliberate ADR if pursued.

**Telegram + dashboard + VPS receiver are out of scope for Linus.** AgentPrometheus markets a remote-control surface
(Telegram bot, web dashboard, VPS receiver). Linus's commitment to the orchestration-layer-as-product means the
front-end is whatever harness Dan uses (Claude Code, openclaw, etc.); Linus shouldn't ship a Telegram bot.

## 5. What's incompatible or out of scope

**The "consultant model with weak model reliability" thesis is operationally distinct from Linus's Worker model.**
AgentPrometheus targets fast/cheap/less-intelligent models with strong system-side scaffolding. Linus's Worker model
(Qwen3-30B-A3B per Phase 1c) is not "less intelligent" — it's a reasoning model used for substantive cognitive work,
backed by a substantial scratchpad and memory architecture. AgentPrometheus's "system does everything, AI just consults"
framing is too restrictive for Linus's Worker capabilities. The Linus Worker should be able to do substantive
multi-step reasoning, not just consult on system-collected evidence.

**The framing assumes the AI is the riskiest component.** AgentPrometheus's design rule treats the LLM as untrusted by
default, deferring all destructive operations to system code with explicit approval gates. Linus's discipline is more
nuanced — the Worker is **trusted-with-bounded-scope** per DEC-0030 (scratchpad is durable; memory mode is explicit;
cot_budget is bounded). The risk model differs.

**No memory architecture beyond the Redis-backed task queue.** AgentPrometheus's persistence is Redis-backed task
queues and logs. Linus's DEC-0028 memory pillar (Layers A-E) is a far richer commitment. The pattern doesn't help with
Layer B/C/D/E architecture.

**Heavy operational-discipline overhead.** The accompanying docs (`AGENT_ABILITIES.md`, `HONEST_ABILITIES.md`,
`SPEC_TEMPLATE.md`, etc.) suggest a heavy process discipline that may be over-investment for a single-developer or
small-team project. Linus's discipline (CLAUDE.md, the Algorithm) is leaner. The AgentPrometheus process is suggestive
but not directly portable.

## 6. Recommendation: **Study**

AgentPrometheus is a **design-rule reference** for Linus's Phase 2a/2b orchestration backend. The "system executes, AI
consults" design rule, the evidence-packet construction pattern, the strict-JSON response handling, the path-protection
defaults, and the upstream-watcher CI pattern are all worth lifting as design vocabulary. The implementation is too
infrastructure-heavy (Redis hard dependency, Telegram/VPS surface, vendored upstream subdirectories) to absorb directly,
and the license needs clarification before any code lift.

The framing — that strong system-side scaffolding makes weaker models usable — is a useful **calibration data point**
for Linus's Phase 1c worker-selection spike. If Linus's Worker registry includes both strong reasoning Workers
(Qwen3-30B-A3B) and lighter "consultant" Workers (smaller distilled models), the AgentPrometheus framing argues for
giving the lighter Workers more scaffolding rather than asking them to do less.

## 7. Questions for Dan

1. **License clarification.** Before any code lift from AgentPrometheus, the license needs investigation. The README
   doesn't surface a license file; the repo structure suggests there may be one (`LICENSE` typically), but a Linus
   Worker should verify before integration.

2. **"System executes, AI consults" as a Phase 2a design-rule statement.** Should the Phase 2a backend spec adopt this
   design rule as an explicit architectural commitment? It would clarify the FastAPI server's role (deterministic work,
   evidence packet construction, audit logging) versus the Worker's role (LLM call only).

3. **Evidence-packet pattern in DEC-0050 Worker dispatch.** Should each Worker invocation per the agent-spawner spec
   require an explicit evidence-packet construction step? The pattern fits naturally with the "context is a resource"
   discipline (DEC-0032) but adds spec-level overhead.

4. **Path-protection defaults — adopt directly?** The path-protection list (no edits outside workspace, no edits to
   `.git`/`node_modules`/`venv`/`__pycache__`/`hive_mind_db`) is portable. Worth lifting into SAFETY.md as the default
   path-protection set?

5. **Upstream-watcher CI for the repos/ directory.** Linus's repos/ directory has ~100 reference clones. An
   upstream-watcher action could surface meaningful changes per the curation protocol (DEC-0025). Worth a Phase 2+
   addition?

6. **Redis as Phase 3 spawner queue.** For multi-process Phase 3 Worker dispatch, Redis is a natural primitive.
   Currently no Redis dependency. Worth scoping in the Phase 3 spawner spec or deferring as an implementation detail?
