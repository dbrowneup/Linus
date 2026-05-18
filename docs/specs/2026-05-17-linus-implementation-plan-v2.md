# Linus Implementation Plan v2 — Phase 2a Closeout + Forward Motion

> **Date:** 2026-05-17
> **Purpose:** Succeed the 2026-05-12 implementation plan. v1 landed six of seven items in four days
> (PRs #32–#40, #50, #51). v2 closes the Phase 2a scaffolding gaps, executes the decisions-first ADRs
> that block downstream router and memory work, and starts forward motion on Phase 2b / 2c / 2h growth.
> **Scope:** Phase 2a closeout + tractable Phase 2b/2c/2e/2h items + the three decisions-first ADRs.
> Nothing beyond Phase 2.

## Where v1 landed (status snapshot, 2026-05-17)

**Done (six of seven):**

- ✅ **v1 Item 1** — FastAPI orchestration backend (`src/linus/server.py`, PR #32).
- ✅ **v1 Item 2** — Dan task suite v0 (PR #33; baseline at `benchmarks/results/dan_tasks_baseline_2026-05-16.json`).
- ✅ **v1 Item 3** — First Maestro/Worker loop (PR #38). Verdict REJECT; calibration data preserved.
- ✅ **v1 Item 4** — Memory v0 scaffolding (`src/linus/memory/`, PR #35).
- ✅ **v1 Item 5** — Read-only KnowledgeBase adapter (`src/linus/knowledge/`, PR #34).
- ✅ **v1 Item 6** — Tool registry + server tool-call routing (`src/linus/tools/`, PR #40).
- ✅ **v2 N1** — SandboxFS hand-written per Item 3 calibration data (`src/linus/sandbox/`, PR #50).
- ✅ **v2 N6** — Janitorial: first `pip-audit` drill + Ollama integrity + question propagations (PR #51).

**Not yet done from v1 (carried forward into v2):**

- ⏳ **v1 Item 7** — Phase 1b pmetal verdict ADR. Dan-driven, not delegatable. Stays on the v2 deferred-but-tracked
  list (item C1 below) with a recommended scheduling cadence.

**Quietly broken or carried-forward debt addressed in v2 below:**

- Server hardcodes the model (Item 1 deferred env-loaded config) → **N4**.
- No streaming on `/v1/chat/completions` → **N2**.
- No Anthropic Messages endpoint despite DEC-0056 → **N3**.
- No session store → **N5**.
- R3-08 benchmarking ADR shipped after Phase 1d rather than before → **N7** (retroactive but cheap).
- Lockfile generation (R3-01 second half) not done → **F1**.
- Six orchestration-runtime-path packages have pip-audit fixes available → **F2**.
- Ollama registry-side provenance check deferred → **F3**.

## Sequencing strategy

Same three principles as v1, plus one new one:

1. **Unblocked first.** Several items have no dependencies and can start immediately. Spike-driven items
   (Item 7, AlphaGenome, Phase 1c) stay Dan-driven and rolling in parallel.
2. **Checkpoint per session.** Same one-session sizing. ~30–60 min active engagement, ending at a clean commit.
3. **Smoke-test gate everywhere.** Same as v1.
4. **Decisions-first ADRs precede the work they unblock.** D1, D2, D3 are 30–60-minute planning turns
   that land their ADRs BEFORE the dependent code items. Cheap discipline that prevents N5/N8 from being
   designed against an unstated convention.

## v2 work items

Same shape as v1: per-item Why / Scope / Success criteria / Estimated session length / Delegable prompt
(where applicable). Items are grouped by track. Within each track, dependencies are noted.

---

### Phase 2a closeout track

#### N2 — Streaming SSE on `/v1/chat/completions`

**Why.** The OpenAI Chat Completions clients (Cline, openclaw, claw-code-local, Continue, etc.) all
expect streaming by default. The current server is request/response only. Adding streaming is small,
high-leverage, and unblocks the chat-UI work (N8).

**Scope.**

- Add `stream: bool = False` handling to `ChatCompletionRequest` in `src/linus/server.py`.
- When `stream=True`, return `StreamingResponse` emitting OpenAI-formatted SSE chunks:
  `data: {"id":...,"object":"chat.completion.chunk","choices":[{"delta":{"content":"..."}}]}\n\n` plus
  the terminal `data: [DONE]\n\n`.
- Route to Ollama's `/api/chat` with `stream=True` and translate Ollama's chunk shape to OpenAI's.
- Preserve tool-call routing: streaming + tool calls is a no-op for v0; emit the tool_calls in the
  final chunk only.
- Add a smoke test that asserts the SSE chunks parse and the concatenated content equals what
  non-streaming would have returned.

**Success criteria.**

- `curl -N -X POST localhost:8000/v1/chat/completions -d '{"model":"...","messages":[...],"stream":true}'`
  emits valid SSE chunks ending in `data: [DONE]`.
- `pytest tests/test_server_streaming.py` passes.
- Non-streaming behavior unchanged.

**Estimated session length:** 60 min.

#### N3 — Anthropic `/v1/messages` endpoint per DEC-0056

**Why.** DEC-0056 commits Phase 2a to a dual OpenAI + Anthropic surface; the Anthropic Messages-compatible
endpoint has not landed. Letta, Kimi-K2, and Goose all confirm this is the production-stack norm. Adding
it is a thin translation layer on top of the existing routing.

**Scope.**

- Add `POST /v1/messages` handling Anthropic Messages request shape.
- Translate Anthropic's `messages` + `system` field placement to Ollama's chat-message form (DEC-0056
  specifically flags system-field placement, content-block shape, tool-call format, and the streaming
  event catalog as places translation logic is needed).
- Reuse the existing Ollama routing, tool registry, audit log, and sandbox machinery — no parallel
  pipeline.
- Mirror N2: support `stream: true` via Anthropic's SSE event catalog (`message_start`, `content_block_delta`,
  `message_delta`, `message_stop`).
- Document the Kimi-K2 temperature mapping caveat (`real_temperature = request_temperature × 0.6`) in a
  module docstring as a known-quirk reference; do not implement that specific mapping unless a client demands it.
- Tests: happy path, system-field placement correct, tool-call translation, streaming chunks parse.

**Success criteria.**

- `curl localhost:8000/v1/messages` returns Anthropic-shaped response.
- Both `/v1/chat/completions` and `/v1/messages` produce equivalent content from the same underlying
  message thread (modulo response envelope shape).
- `pytest tests/test_messages_endpoint.py` passes.

**Estimated session length:** 90 min.

#### N4 — Env-loaded model config + multi-model registry

**Why.** The server currently hardcodes `qwen3:8b` (then falls through to whatever is locally available).
Hardcoding the model was an explicit v1 follow-up. Once the user supplies multiple models via env config,
the router can make per-call decisions (smallest model that fits the task, etc.) — a precondition for D2
(context-routing policy) to have anything to route over.

**Scope.**

- Add a `LINUS_DEFAULT_MODEL` env var (read at import time) and a `LINUS_MODEL_REGISTRY` env var that
  parses a comma-separated list of model names available for dispatch.
- Add an optional `~/.linus/config.toml` overriding env vars; env wins over toml; request-body wins over both.
- The model-resolution chain in `_resolve_model()` becomes: request body → env default → first available
  Ollama model.
- Tests: registry parsing, env-override, request-override, fallback to first available.

**Success criteria.**

- `LINUS_DEFAULT_MODEL=mistral:7b-instruct uvicorn linus.server:app` uses mistral as the default.
- Specifying `model` in the request body still wins.
- `pytest tests/test_model_config.py` passes.

**Estimated session length:** 45 min.

#### N5 — Session store (SQLite-backed thread of messages)

**Why.** The server is stateless across calls; clients must re-send full conversation history every turn.
This wastes tokens and prevents `memory_mode = session_stateful` (DEC-0031) from being meaningful at
Phase 2a. The session store is also memory v0 deliverable #3 (scratchpad first-class per DEC-0030).
**Depends on D3 (R3-02 hook taxonomy) landing first** so the write contract is known.

**Scope.**

- New `src/linus/memory/session.py`: SQLite-backed thread store at `~/.linus/sessions.db`.
- Schema: `sessions(id, created_at, model, metadata_json)`,
  `session_messages(session_id, turn, role, content_json, ts, content_hash)`.
- Server accepts an `X-Linus-Session-Id` request header; if present, prepends the session history to the
  request `messages`; if absent, generates a fresh session id and returns it in the response header.
- Session-write hook fires after every successful completion, writing both the request and response to
  the session table (with content hashes per DEC-0029) and emitting a corresponding episodic record
  per the D3 hook taxonomy.
- Integration test against the running server proving multi-turn coherence.

**Success criteria.**

- Two sequential `curl` calls with the same `X-Linus-Session-Id` produce a coherent response on turn 2
  (the model "remembers" turn 1 context).
- `~/.linus/sessions.db` contains both messages from the exchange.
- Audit log entries reflect the session writes per DEC-0031.

**Estimated session length:** 90 min.

---

### Top-questions / ADRs track

#### N7 — R3-08 benchmarking ADR + light retrofit of Dan tasks

**Why.** Three independent papers (BixBench, LAB-Bench, tokens-per-second 2502.16721v1) converge on
"measure the operational thing, not the surrogate." R3-08 was supposed to land before Phase 1d task
authoring; Phase 1d shipped first. Authoring the ADR now plus light retrofit of the three existing tasks
prevents the deeper R2-03 grader work from being pulled in a different direction.

**Scope.**

- Write `docs/adr/0059-benchmark-convention-open-answer-headline.md` codifying: every
  `benchmarks/dan_tasks/` task ships (a) an open-answer headline question, (b) MCQ as secondary if a
  fixed answer space exists, (c) coverage / accuracy / precision tracked as separate metrics, (d)
  insufficient-info-option per FutureHouse evaluation philosophy where applicable, (e) gap between
  open-answer and MCQ reported as calibration metric.
- Light retrofit of the three current tasks: add an `open_answer_headline` field to each
  `expected_output_schema.json` and update the rubric notes accordingly. Do NOT implement scoring
  in this session (that's R2-03 work).
- Update `ROADMAP.md` Phase 1d row to reference the ADR.

**Estimated session length:** 60 min.

#### D1 — R2-01 pydantic-ai vs bespoke wrapper ADR

**Why.** Adopting `pydantic-ai` reduces Linus orchestration code by ~70% but adds an external dependency
to the core inference path. The bespoke wrapper keeps the dependency graph minimal at the cost of more
code. Every Worker dispatch refactor is shaped by this choice. Landing the ADR before N5 / D2 / D3 prevents
those items from being designed against an unstated assumption.

**Scope.**

- 30-minute apples-to-apples comparison: write a 50-line bespoke Agent wrapper and a 50-line pydantic-ai
  equivalent for the existing `chat_completions` flow. Compare LOC, dependency footprint, type-safety,
  testability, dispatch-time overhead.
- Write `docs/adr/0060-pydantic-ai-vs-bespoke-agent-wrapper.md` recording the comparison numbers and the
  decision (recommendation: bespoke wrapper for v0; pydantic-ai re-evaluated at Phase 3 when multi-agent
  fan-out work begins — but the ADR records the actual measured trade, not the recommendation).
- Update R2-01 in top-questions to resolved.

**Estimated session length:** 60 min.

#### D2 — R2-04 context-routing policy ADR

**Why.** Context quality, not model size, is the primary determinant of Worker effectiveness per
Agent-Skills-for-Context-Engineering. The Phase 2a spec needs an explicit policy or an explicit deferral.
N5 (session store) and N8 (chat UI) both depend on knowing whether session history is summarized-vs-passed
verbatim and whether KB query results are truncated-vs-full. Depends on **N4 + D1** landing first so the
policy has concrete dispatch primitives to operate over.

**Scope.**

- Write `docs/adr/0061-context-routing-policy-phase2a.md`. Recommended posture for v0: deferred empirical
  tuning, but codify the two routing decisions Phase 2a does make:
  1. Session history is passed verbatim until the token count exceeds 16K (DEC-0032 in-context cap);
     overflow routes through episodic store summarization.
  2. KB query results are passed verbatim up to a per-tool-call cap (default 4K tokens); overflow gets
     a tool-side `truncated: true` flag and a hint to re-query with narrower terms.
- Update R2-04 in top-questions to resolved.

**Estimated session length:** 45 min.

#### D3 — R3-02 agentmemory hook taxonomy ADR

**Why.** The agentmemory 13-hook taxonomy (`SessionStart`, `UserPromptSubmit`, ...,
`TaskCompleted`) is the most complete worked answer to "which lifecycle events does Layer C subscribe to"
in the corpus. DEC-0029 specifies the record shape but leaves hook-to-write mapping to the implementer.
N5 (session store) depends on this because the write contract must be known. Land the ADR before N5.

**Scope.**

- Read `repo-notes/agentmemory.md` for the 13-hook list.
- Write `docs/adr/0062-episodic-memory-lifecycle-hooks.md` porting the taxonomy into Linus terms:
  per-hook `segment` (which `EpisodicRecord.segment` enum value the hook writes), `trust_level`
  (whether the record carries `trust_level=verified` vs `trust_level=unverified`), and `role` (the
  actor — `user`, `worker`, `maestro`, `system`).
- Document the hooks Phase 2a actually wires (SessionStart, UserPromptSubmit, ToolCall, ToolResult,
  TaskCompleted) and the hooks deferred to Phase 3 (Subagent*, PreCompact, Stop, Notification).
- Update R3-02 in top-questions to resolved.

**Estimated session length:** 60 min.

---

### Phase 2 forward-motion track

#### N8 — Streamlit chat UI (Phase 2b)

**Why.** First end-to-end demo-able artifact. The orchestration backend is invisible without a UI; even a
50-line Streamlit harness lets Dan run a real conversation against Linus from a browser tab. Depends on
**N4 + N5** landing first so model selection and session continuity work.

**Scope.**

- New `src/linus/ui/chat.py` Streamlit app calling local Linus server.
- Single chat panel; session id stored in `st.session_state`; model selectable from a dropdown populated
  from the model registry (N4).
- Streaming response display via N2's SSE endpoint.
- Tools list visible in a sidebar with which tools fired during the last turn.
- No production polish; this is a working demo, not a product.

**Success criteria.**

- `streamlit run src/linus/ui/chat.py` opens a browser tab.
- A two-turn conversation produces a coherent reply on turn 2 (session-store working).
- KB search tool fires when prompted with "search the corpus for X" (tool registry working).

**Estimated session length:** 60 min.

#### N9 — Output synthesis + citation drill-down (Phase 2e)

**Why.** "Linus answers questions about your corpus with citations" is the headline Phase 2 capability for
private research-assistant use. The KB adapter (Item 5) and tool registry (Item 6) already exist; the
synthesis layer wraps them into a single tool that returns a paragraph plus inline `[paper-id]` markers
plus a drill-down list of cited papers.

**Scope.**

- New `src/linus/knowledge/synthesis.py` exposing a `synthesize_with_citations(query, k=5)` function.
- Implementation: retrieve top-k papers via `search_papers`, pass titles + abstracts + paper-ids into a
  Worker prompt that synthesizes a paragraph with `[paper-id]` markers, return both the paragraph and
  the cited-paper metadata as a structured response (typed structured prediction per the established
  convention).
- Registered as a tool via `@tool` decorator so the orchestration layer can route to it.
- Smoke test: query "metagenomics gene calling" returns a non-empty synthesis with at least one
  citation that points to a real paper in the local KB.

**Estimated session length:** 60 min.

#### N10 — KB adapter v1: SPECTER2 embedding search

**Why.** v1 Item 5 (KB adapter v0) implements keyword search only. SPECTER2 embedding search is what makes
"semantically related papers" work, and it's the natural follow-up. The KnowledgeBase submodule already
has the SPECTER2 pipeline (per Dan's spec notes); the Linus side is just a thin adapter call. Depends on
the KnowledgeBase submodule exposing the embedding index — verify availability first.

**Scope.**

- Verify `modules/KnowledgeBase/` has the SPECTER2 index built (graceful fail if not).
- Add `search_papers_semantic(query, k=10)` to the adapter using the SPECTER2 embeddings.
- Register as a tool alongside the existing keyword search.
- The router (N4 / D2) decides which to call: explicit "find similar to X" → semantic; explicit
  "find papers mentioning X" → keyword; ambiguous → semantic.

**Estimated session length:** 75 min.

#### N11 — ARC-AGI memory diagnostic (Phase 2i, DEC-0035)

**Why.** DEC-0035 commits to ARC-AGI as a diagnostic of memory-mode-driven Worker behavior. Running even
a small subset (10–20 tasks) on Qwen3:8b against the existing memory v0 gives the first concrete
data point on whether `memory_mode = session_stateful` actually improves performance vs stateless. This
is also the input data for the Phase 1c spike (memory-pillar viability).

**Scope.**

- New `benchmarks/arc_agi/` directory.
- Pull 10 ARC-AGI tasks from the public eval set (offline cache; no network during eval).
- Driver script that runs each task twice: once with `memory_mode=stateless`, once with
  `memory_mode=session_stateful`. Records outputs to a dated JSON results file.
- No grading in this session; just collection. The grading rubric is in a separate ADR (R3-08 / N7
  shape).

**Estimated session length:** 75 min.

---

### Follow-ups from N6 (security-log v2 items)

#### F1 — Generate `requirements-locked.txt` with hash pinning (R3-01 second half)

**Why.** N6 ran the first `pip-audit` drill but did NOT generate the hash-pinned lockfile that DEC-0024
commits to. Without the lockfile, the supply-chain architecture is half-built. The lockfile is the input
to the SAFETY.md attestation procedure (`pip install --require-hashes -r requirements-locked.txt`).

**Scope.**

- Run `pip-compile --generate-hashes` (or equivalent for the conda-pip mix) to produce
  `requirements-locked.txt` capturing the current linus env.
- Document the regeneration procedure in `CLAUDE.md`'s environment section.
- Wire monthly `pip-audit` as a `make audit` or `scripts/audit.sh` for repeat runs.

**Estimated session length:** 45 min.

#### F2 — Env upgrade for orchestration-runtime-path pip-audit findings

**Why.** N6 found fix versions for six orchestration-runtime-path packages (`langchain-core`, `langsmith`,
`urllib3`, `python-multipart`, `gitpython`, `pip`). Upgrading clears the runtime-path CVE backlog.
**Depends on F1** so the lockfile reflects the new versions immediately after upgrade.

**Scope.**

- `conda env update` or `pip install --upgrade` for the six packages.
- Re-run `pytest` to confirm no test regressions.
- Re-run `pip-audit` to confirm the runtime-path findings are cleared.
- Update `docs/security-log.md` with the closure entry.

**Estimated session length:** 30 min.

#### F3 — Ollama registry-side provenance check (R3-12 follow-up)

**Why.** N6 verified on-disk blob integrity but did not verify provenance (do these SHAs match what
`registry.ollama.ai` published?). Low priority because local integrity is intact and there's no sign of
tampering, but worth doing once for documentation.

**Scope.**

- Script that fetches the manifest from `registry.ollama.ai` for each locally-stored model tag and
  compares the published SHA-256s against the local blob filenames.
- Record results in `docs/security-log.md`.
- Network operation — requires confirmation per SAFETY.md Tier 1.

**Estimated session length:** 30 min.

---

### Spike-driven, Dan-time (carry-forward from v1, not delegable)

These remain on the rolling backlog. Each is a Dan-driven session (or sessions); Claude Code is the
analysis layer, not the button-pushing layer.

#### C1 — v1 Item 7: Phase 1b pmetal verdict ADR

**Why.** Gate for Phase 2's serving-layer decision. Built and smoke-tested; LoRA + serve + comparative
benchmark + verdict ADR are the remaining steps. ~3-4 hours of active hands-on work spread across 2-3
sessions. Carries forward from v1 unchanged.

#### C2 — Phase 1c spike per `docs/specs/phase1c-spike.md`

**Why.** Memory-pillar viability (CoT-gap, Worker-size×CoT-length, TTT viability) is the input data for
DEC-0033 / DEC-0034 ADR validation and shapes the Phase 2h.5/6/7 dispatch-wiring work. Real research
time. Note R3-04 (model list reconciliation between syntheses) should be resolved as a 15-minute prep
step before the spike runs.

#### C3 — Phase 1f minGRU MLX-port spike (DEC-0038)

**Why.** Phase 8 research direction (DEC-0041); spike scoped at ~1 week of focused work.

#### C4 — AlphaGenome local-deployability spike (R3-05)

**Why.** Determines whether AlphaGenome is a local Worker or external-API only (DEC-0046's
`external_api` registry field). One-day spike: clone, inspect model size, attempt one local inference on
a 1 Mb interval.

---

## Items deliberately deferred from v2

These are real and tracked, but explicitly out of v2 scope. Each is a candidate for a v3 implementation
plan:

- **2b chat UI polish.** N8 ships a working demo; productizing it is v3.
- **2f KB dual substrate (SPARQL + property graph).** N10 ships embedding search; dual substrate is v3.
- **2g knowledge-mining-surface document.** Spec doc; Phase 2 deliverable; lower urgency.
- **2h.5/6/7 dispatch wiring with cot_budget + memory_mode.** Blocked on C2 (Phase 1c spike output) and
  D3 (hook-taxonomy ADR).
- **2j Worker protocol non-conformance constraints.** Doc work; lower priority.
- **MCP transport decision (R2-06).** Stdio vs streamable-http; needs at least one concrete MCP server
  Linus is hosting to make the call against. Defer to v3.
- **R2-07 vault location for hyalo/keppi.** Phase 3 KB-tooling layer; defer.
- **R2-08 hyalo vs keppi bake-off.** Same, defer to Phase 3.
- **R3-03 SKILL.md format spec.** Phase 7 inaugural skills bundle work; defer.
- **R2-02 Worker review gates.** Phase 3 multi-agent work; defer.
- **R2-03 Dan task suite expansion + graders.** N7 lands the convention; expansion is v3 after N9 and
  N11 produce real task surface data.

The deferred list is not a graveyard — it's a queue. Schedule a v3 planning session when v2 is ~80% landed.

## Usage management and session cadence

Same discipline as v1:

1. **Stop after each item.** Don't continue into the next item without a break.
2. **Review the commit / PR.** Did the work match the spec? Is the code clean? Tests passing?
3. **Decide:** continue to the next item, or iterate on this one.
4. **Re-plan if the picture changed.** Edit this document.

Rolling estimate: v2 items N2–N11 + D1–D3 + F1–F3 are ~14 Claude Code sessions of 45–90 min each. At
the v1 cadence (8 sessions / 4 days), v2 lands in ~7–8 days of calendar time. Add buffer; reality is
messier.

**Per-session discipline (unchanged from v1):**

- Open with the prompt or the item scope.
- Don't add new asks mid-session.
- End with a commit + PR.
- Update this document's status block as items land.

## What success looks like at the end of v2

After v2 items N2–N11 + D1–D3 + F1–F3 land:

- The OpenAI Chat Completions endpoint streams SSE (N2).
- An Anthropic Messages-compatible endpoint serves the same routing (N3).
- Multi-model config + session continuity work end-to-end (N4 + N5).
- A Streamlit chat UI demos the full stack (N8).
- The KB adapter does semantic search (N10) and citation-grounded synthesis (N9).
- ARC-AGI memory diagnostic produces the first stateful-vs-stateless comparison data (N11).
- Three load-bearing ADRs land (D1: pydantic-ai; D2: context routing; D3: episodic hook taxonomy).
- Benchmark convention is codified (N7).
- Supply chain is fully wired (F1) with the runtime-path CVEs cleared (F2) and provenance documented (F3).
- v1 Item 7 (pmetal) still rolling on Dan's hands-on backlog (C1).

**This is Linus beta.** It's not pretty; the chat UI is functional rather than polished. But it is
**demo-able end-to-end with citations and memory, runs only on Apple Silicon, and unblocks Phase 3
multi-agent work** by removing the "Phase 2a is half-built" risk.

After v2 lands, the next planning conversation is "Phase 3 multi-agent fan-out — orchestration code
shape for `src/linus/orchestration/workspace.py`" — exactly where R3-07's second half is waiting.

---

_Maintainer note: this plan reflects 2026-05-17 state. Revise after each completed item; don't let it
drift. The v1 plan (`2026-05-12-linus-implementation-plan.md`) stays as the historical record of the
first arc; v2 succeeds it without overwriting._
