## DEC-0061 — Network-policy framework: per-tool egress declaration + audit-log capture + `/healthz` reachability reporting

**Date:** 2026-05-20 **Status:** accepted

**Context.** The pre-2026-05-20 framing of Linus was uncompromisingly local-only: every component runs on Dan's
hardware, no telemetry leaves the box, no API key is required for any path, and the network boundary is the trust
boundary. That stance carried VISION.md, CLAUDE.md, and the public README. It is still the right default — Linus's
private-by-default character is non-negotiable — but it is too narrow for a class of tools that are demonstrably useful
when the network is available and demonstrably degrade-cleanly when it is not. The canonical example surfaced
2026-05-20: `entity_ncbi.py` (the production NCBI Gene / UniProt backend behind DEC-0059's entity grounding) wants a
real NCBI lookup when the operator has connectivity, but must fall through to the existing builtin stub when offline so
hermetic tests stay network-free and offline sessions still produce stakeable output.

The 2026-05-20 reframe: **local-primary, but some tools may use the internet when available; nothing depends on it.**
Core inference (Ollama) stays local. The KB corpus stays local. Hermetic tests stay network-free. No paid APIs are
required for any path Linus walks. What changes is that a small set of opt-in tools — entity backends, paper-metadata
lookups, and a handful of future biology tools — may consult the internet when reachable, declare that they do so at
registration time, and have every external call captured in the audit log. The Marelli accountability discipline
(DEC-0030 / DEC-0031, the audit log) extends to external calls in exactly the way it already covers Worker dispatch
and memory writes: the audit log is the durable record of what happened, and "what happened" now includes egress.

**Decision.** Add a three-pillar framework codifying network access as a first-class concern. Each pillar is additive,
backwards-compatible, and lands in this PR; the entity_ncbi.py work (next PR) is the first instance that uses it.

**Pillar 1 — per-tool `network_policy` declaration at registration.** Every registered tool carries a
`network_policy` attribute drawn from a closed three-value vocabulary: `offline` | `online_optional` | `online_required`.
The default is `offline`; existing tools land with the default unchanged so the migration is invisible. The vocabulary:

- **`offline`** — the tool never touches the network. KB reads, in-process computation, Ollama-routed inference, the
  whole existing tool catalog. The default for new tools unless explicitly elevated.
- **`online_optional`** — the tool prefers the network when available but degrades cleanly when it isn't. Concretely:
  the tool MUST have a local fallback (a cache, an alternative offline backend, or a graceful `None` / `unresolved`
  return). The first instance is `entity_ncbi.py`: real NCBI lookup when reachable, builtin stub when not. Hermetic
  tests exercise the offline branch; integration tests exercise both.
- **`online_required`** — the tool refuses to execute when offline. Reserved for tools where the offline result would be
  materially misleading (a "current weather" tool's cached value from last week is worse than refusing). No
  `online_required` tool ships in this PR; the slot exists so the framework is complete from day one rather than
  needing a later amendment.

The policy is declared at registration time, alongside the function signature and JSON-Schema parameters. The
`@tool(...)` decorator and `ToolRegistry.register(...)` both accept a `network_policy` kwarg with type
`Literal["offline", "online_optional", "online_required"]`; invalid values raise `ValueError` at registration so
typos cannot ship silently. The registered `ToolSpec` exposes the value as a read-only field, available to the server,
the audit-log writer, and any UI that wants to surface network posture per tool.

**Pillar 2 — audit-log `network_egress[]` capture.** The append-only JSONL audit log (per DEC-0030 / DEC-0031) gains
an optional `network_egress` list field on the dispatch event schema. Each entry has shape
`{url_host, query_hash, response_size, latency_ms, timestamp_ns}`. The field is **optional and backwards-compatible**:
records without it parse exactly as before; readers built before this PR continue to work. The recorded fields are
deliberately minimum-disclosure — host (not full URL), query hash (not query text), response size (not response body) —
so the audit log captures the fact of the call without retaining the content. Tools writing this field do so at the
point of call; the registry doesn't try to intercept arbitrary HTTP traffic, which would be both impossible (a tool can
use any HTTP client it wants) and the wrong layer (Marelli accountability is about the tool declaring what it did, not
about a sandbox reverse-engineering the call from below).

The first concrete writer ships with `entity_ncbi.py` in the follow-up PR. The framework here defines the field shape
and the read/write contract so the entity-backend work is purely a consumer.

**Pillar 3 — `/healthz` reachability reporting.** The `/healthz` endpoint (extended in DEC-0060) gains two new
detection paths in `_compute_degradations()`:

1. **`network_unreachable_for_online_required`** — if any registered tool has `network_policy="online_required"` AND
   the quick external reachability check fails → `error` severity. The tool cannot execute; the server is `down`.
2. **`network_optional_degraded`** — if any tool has `network_policy="online_optional"` AND the reachability check
   fails → `warning` severity. The tool still works in its cached / fallback mode; the server is `degraded`.

The reachability check is a small, mockable, fast operation: `socket.gethostbyname("1.1.1.1")` (or equivalent)
wrapped in try/except with a sub-second timeout. The function is module-level and monkeypatchable so hermetic tests
substitute it without any real network call ever happening from the test suite. The test discipline below makes this
contractual, not merely encouraged.

When no `online_*` tool is registered, neither detection path fires — a fully-offline registry sees no spurious
warnings even if the host is genuinely offline. This is the load-bearing property: the framework adds zero noise to
Dan's existing offline-only setup, and only speaks up when an `online_*` tool is actually present and the network it
wants is missing.

**Threat model — what can leak via online tools.** Each `network_policy != "offline"` tool is a potential exfiltration
surface, however small. The framework's three-part response: (a) the policy must be declared at registration, which
makes the tool author and the reviewer explicitly aware that this tool can leak; (b) the registration declaration is
visible at design time, so a code reviewer can see "this tool talks to the internet" without running the program;
(c) the audit log captures every call at runtime, so post-facto verification of what left the box is mechanically
possible. Three layers — author declares, reviewer checks, audit records — covering design-time review through to
runtime accountability.

In §"Tool Use Policy" of CLAUDE.md, tools with `network_policy != "offline"` are flagged for **explicit data-leaving
review at design time** by Maestro (Dan + hosted Claude). A tool with this elevated policy must justify: what hostnames
it contacts, what fields of the call carry user / KB / corpus data, what the host's privacy posture is, and what
happens to the data after the response returns. The review lives in the tool's PR description and the answering ADR if
one is filed. This is not bureaucracy — it is the same discipline that already gates `repos/` additions and any `pip
install` outside a `uv venv`. Network egress is the same kind of trust decision.

**Test discipline — hermetic mocks, integration suite for real HTTP.** The hermetic suite (`pytest src/linus/tests/`)
remains network-free as an architectural constant. Every test that exercises the framework either:

- uses an `offline` tool (no mocking needed; no network code path), or
- uses an `online_*` tool whose network call is monkeypatched at the call-site (the tool exports a module-level
  `_check_network_reachable()` or equivalent shim; tests substitute it), or
- exercises `/healthz` with the reachability check stubbed via the same monkeypatch path.

Real HTTP exercises live in the integration suite (`tests/`) alongside the existing Ollama integration tests, gated
behind the same `requires_network` marker convention. The hermetic / integration split is preserved verbatim — this PR
does not loosen it.

**What stays unchanged.** Core inference (Ollama) stays local. The KB corpus stays local. The chat-completions and
Anthropic-Messages endpoints involve zero external HTTP. Hermetic tests stay network-free. No paid APIs are required
for any operational path. The README's tagline ("Knowledge that never goes offline") remains accurate: the knowledge
itself never goes offline, and the assistant never *requires* the network — some tools may opt-in to using it.

**First instance.** `entity_ncbi.py` lands in the next PR as the first `online_optional` tool. It wraps the existing
builtin `BuiltinEntityLookup` stub from DEC-0059 with an opt-in NCBI Gene / UniProt resolution path: when the network
is reachable, the real backend resolves; when not, the stub answer is returned with a `backend=builtin_stub` marker so
the rigor gate's downstream consumers see the fallback explicitly. This PR ships the framework; that PR ships the
first consumer. The split is deliberate — landing the framework alone forces the design to stand on its own merits,
not to be retrofitted around a single concrete user.

**Consequence.** Linus retains its local-first character and gains the option to opt-in network capabilities under
accountability discipline. The framework is the substrate the entity_ncbi.py work (next PR) builds on, and the
substrate any future online-tool work uses — paper-metadata lookups for `arxiv_ingest`, KEGG / Reactome backends for
biology skills, web-fetch tools for the entrepreneurial surface, all of them follow the same pattern. The audit log
becomes mechanically auditable for egress, satisfying the Marelli accountability discipline (DEC-0030 / DEC-0031) at
the network boundary as it already does at the dispatch and memory-write boundaries. `/healthz` becomes the canonical
single endpoint where "can Linus do its primary job?" is answered, with network posture now part of the answer when
any `online_*` tool is registered.

**References.**

- [DEC-0024](0024-disposable-uv-envs-for-experimental-packages.md) — Disposable uv envs for experimental packages
  (the new HTTP-client libs the first online tools may need go through uv-env evaluation first).
- [DEC-0030](0030-scratchpad-first-class-artifact.md) — Scratchpad as first-class artifact (the audit log).
- [DEC-0031](0031-router-primitives-cot-budget-memory-mode.md) — Router primitives recorded in the audit log
  (the dispatch-event carrier `network_egress` extends).
- [DEC-0059](0059-grounding-gate-output-surface.md) — Grounding gate at the OUTPUT surface (the rigor-gate context
  that the entity-backend follow-up sits inside; `entity_ncbi.py` is the load-bearing first user of this framework).
- [DEC-0060](0060-loud-degradation-healthz-extension.md) — Loud degradation `/healthz` extension (the precedent for
  `_compute_degradations()` additions; the network-reachability paths follow the same pattern).
- Source: `src/linus/tools/registry.py` (ToolSpec.network_policy, register kwarg);
  `src/linus/memory/audit_log.py` (DispatchEvent.network_egress); `src/linus/server.py` (`_check_network_reachable`,
  `_compute_degradations` network branches).
- Tests: `src/linus/tests/test_registry.py`, `src/linus/tests/test_audit_log.py`, `src/linus/tests/test_healthz.py`
  (hermetic; the network-reachability shim is module-level monkeypatchable).
