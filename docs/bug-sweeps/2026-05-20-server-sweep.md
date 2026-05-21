# Server.py + HTTP routes — bug sweep 2026-05-20

**Scope:** `src/linus/server.py` + tests covering it
(`test_server_coverage.py`, `test_anthropic_compat.py`, `test_streaming.py`,
`test_sessions.py`, `test_tool_invoke.py`, `test_healthz.py`, and
`tests/test_server.py`).
**Total findings:** 12 (critical: 1, high: 2, medium: 6, low: 3)
**Surveyor:** bug-sweep subagent (read-only; no fixes proposed)

The server-side surface is well-tested for the happy-path schema contract
and individual error branches, but the suite is uniformly single-threaded.
The most concerning class of bugs are race conditions and durability gaps
that only surface under concurrent load or client-disconnect — neither of
which the 591-test suite simulates.

## Critical findings

### C-1: SQLite session-store has a TOCTOU race on `idx` assignment under concurrent requests

- **Location:** `src/linus/memory/sessions.py:211-280` (called from
  `server.py:1240`, `server.py:1091`)
- **Category:** race condition
- **Description:** `SessionStore.append_message` and `append_messages` both
  compute `next_idx = SELECT COALESCE(MAX(idx), -1) + 1 ... WHERE session_id = ?`
  inside a `with conn:` block (SQLite's default `BEGIN DEFERRED`). Two
  concurrent requests against the same `session_id` can both read the same
  `MAX(idx)` value and then both try to INSERT with the same
  `(session_id, idx)` primary key. The class docstring explicitly admits
  "The instance is not threadsafe; create one per request handler thread if
  needed," yet `get_default_store()` returns a **process-wide singleton**
  shared across every FastAPI request handler. FastAPI runs sync route
  handlers in a threadpool, so two concurrent `/v1/chat/completions` calls
  carrying the same `session_id` hit this collision.
- **Why it's a bug:** Under realistic concurrent UI use (two browser tabs
  with the same session, or a retry after slow Ollama response), one
  request raises `sqlite3.IntegrityError: UNIQUE constraint failed:
  session_messages.session_id, session_messages.idx`. In the streaming
  path that's silently swallowed by the broad `except` at
  `server.py:1092` and the user-visible stream just stops emitting events
  with no error indication. In the non-streaming path it bubbles up as
  HTTP 500 and the assistant turn is lost — but the model already
  generated tokens (cost paid, no record kept). The user-visible
  manifestation is "the assistant's reply just disappeared" with no
  diagnostic.
- **Code excerpt:**
  ```python
  # sessions.py:225-234
  with conn:
      cursor = conn.execute(
          "SELECT COALESCE(MAX(idx), -1) + 1 AS next_idx FROM session_messages WHERE session_id = ?",
          (session_id,),
      )
      next_idx = cursor.fetchone()["next_idx"]
      conn.execute(
          "INSERT INTO session_messages(session_id, idx, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
          (session_id, next_idx, role, content, created_at),
      )
  ```
- **Suggested approach:** Either (a) wrap the SELECT+INSERT in an
  `IMMEDIATE` transaction (`conn.execute("BEGIN IMMEDIATE")`) so a write
  lock is acquired before reading `MAX(idx)`, or (b) drop the `idx`
  column entirely and use `rowid` + `created_at`-secondary ordering, or
  (c) hold a Python `threading.Lock` keyed per-session-id around the
  upsert (cheap, simpler than fighting SQLite's isolation levels).
- **Test that should catch this:** A concurrency test in
  `test_sessions.py` that spins up N=8 threads each calling
  `append_message(sid, ...)` with the same `sid` and asserts no
  `IntegrityError` and the resulting `get_messages` returns exactly N
  entries with idx 0..N-1. The current suite is entirely single-threaded
  so this class of bug is invisible.

## High findings

### H-1: Streaming session writes silently lost when client disconnects mid-stream

- **Location:** `src/linus/server.py:1044-1093` (`_stream_with_session_append`)
- **Category:** error handling gap / resource leak
- **Description:** `_stream_with_session_append` is a generator. The
  post-stream session append happens after the `for event in
  _stream_chat_completion(...):` loop completes (line 1083-1093). When
  the HTTP client disconnects mid-stream, Starlette/uvicorn cancels the
  generator. The trailing append code never executes, so the user's
  visible turn (which they already saw partially streamed in their UI) is
  not persisted. On the next page load with the same `session_id`, the
  history is missing both the user message and the assistant's partial
  reply.
- **Why it's a bug:** This is a real failure mode — Streamlit's HTTP
  reconnects, browser navigations, mobile network blips all trigger
  client disconnect. The user sees an assistant response on screen but
  it's gone after refresh. Worse, the user message itself is also lost
  (line 1086-1087 only appends `new_messages` AFTER the stream completes),
  so the next request looks like a fresh conversation that just hap-
  pens to be using a "known" `session_id`.
- **Code excerpt:**
  ```python
  # server.py:1083-1093
  try:
      new_turns: list[tuple[str, str]] = []
      for m in new_messages:
          if m.role in ("user", "system") and m.content:
              new_turns.append((m.role, m.content))
      if accumulated:
          new_turns.append(("assistant", accumulated))
      if new_turns:
          store.append_messages(session_id, new_turns)
  except Exception:  # noqa: BLE001 — session-store failure must not truncate the stream
      pass
  ```
- **Suggested approach:** Persist the user turn BEFORE starting the
  Ollama stream so it's durable regardless of disconnect. Then use a
  `try/finally` (or contextmanager wrapping the generator) to flush the
  accumulated assistant content on cancellation. FastAPI/Starlette
  exposes `request.is_disconnected()` for explicit checks. Alternatively
  use Starlette's `BackgroundTask` to persist the final state. The
  current shape "persist after stream completes" is the worst of both
  worlds — durable only when nothing goes wrong.
- **Test that should catch this:** A test using `httpx.AsyncClient`
  with `aclose()` mid-stream that asserts `get_messages(sid)` returns
  the user turn (and at least the partial assistant content if any
  was accumulated) after the client drops.

### H-2: Tool-call assistant turns and tool-result messages are not persisted to session history

- **Location:** `src/linus/server.py:1232-1240` (non-streaming session append)
  and `src/linus/server.py:1086-1093` (streaming session append)
- **Category:** logic error / schema mismatch
- **Description:** When the chat loop emits tool calls (the model
  requests a tool, server executes it, appends a `role=tool` message,
  loops back), the transcript inside `_run_chat_loop` accumulates
  assistant tool-call turns + role=tool result turns. But the session
  append at line 1232-1240 only persists `req.messages` (the original
  client-sent user/system turns) and `final_message.content` (the
  terminal text-only assistant turn). The intermediate tool-call cycle
  is silently dropped.
- **Why it's a bug:** Per-session statefulness is the whole point of
  the session store — the model should see prior tool context on
  subsequent turns. With the current shape, the next request rehydrates
  the transcript as `[user1, assistant1_final_text, user2]` instead of
  the true `[user1, assistant1_with_tool_calls, tool_result1,
  assistant1_final_text, user2]`. Multi-turn conversations where the
  model used tools in turn 1 lose all tool grounding in turn 2 — the
  model can re-call the same tool with the same args and there's no
  cached state to short-circuit it. This contradicts the docstring's
  promise that "the model context survives page refreshes."
- **Code excerpt:**
  ```python
  # server.py:1232-1240
  if store is not None and req.session_id:
      new_turns: list[tuple[str, str]] = []
      for m in req.messages:
          if m.role in ("user", "system") and m.content:
              new_turns.append((m.role, m.content))
      if final_message.content:
          new_turns.append(("assistant", final_message.content))
      if new_turns:
          store.append_messages(req.session_id, new_turns)
  ```
- **Suggested approach:** Persist the full mutated `transcript` slice
  beyond `len(history)` (i.e., everything appended during this request:
  user message, any assistant tool-call turns, any role=tool messages,
  and the final assistant text). The session store schema already
  accepts `role` ∈ {user, assistant, system, tool}, so the data fits
  the existing tables. Need to also store tool-call structured payloads
  somewhere — either serialize them into the assistant message's
  `content` field as a marker block, or extend the schema with optional
  `tool_calls` / `tool_call_id` columns.
- **Test that should catch this:** A test using a session_id with a
  tool-using assistant turn that asserts the resulting `get_messages`
  returns the role=tool entry between the user and final assistant
  turns; combined with a second-turn smoke that asserts Ollama receives
  the role=tool message in the transcript on the next request.

## Medium findings

### M-1: Streaming tool-iteration cap drops the would-be `tool_calls` to the client entirely

- **Location:** `src/linus/server.py:1008-1019`
- **Category:** schema mismatch / streaming-specific
- **Description:** When the streaming path hits `_MAX_TOOL_ITERATIONS`,
  it emits a terminal chunk with `finish_reason="tool_calls"` and an
  **empty delta** — no `delta.tool_calls` info, no content telling the
  client what tools the model wanted to call. The docstring acknowledges
  "tool-call content is not emitted as visible deltas to the client" by
  design for the resolved-internally path, but the max-iteration cap
  produces zero diagnostic information for a client trying to recover.
- **Why it's a bug:** OpenAI's streaming contract for `finish_reason
  ="tool_calls"` requires `delta.tool_calls` chunks with the structured
  tool-call request. A harness that hits the iteration cap has no way
  to see what the model was looping on. Worse: a well-behaved OpenAI
  client may try to fulfill the tool call externally (the normal
  contract assumes server delegates tool execution to the client) and
  has nothing to dispatch to.
- **Code excerpt:**
  ```python
  # server.py:1008-1019
  if iteration >= _MAX_TOOL_ITERATIONS:
      yield _sse_format(
          _streaming_chunk(
              completion_id,
              created,
              resolved_model,
              delta={},
              finish_reason="tool_calls",
          )
      )
      yield "data: [DONE]\n\n"
      return
  ```
- **Suggested approach:** Either (a) emit the final-iteration tool_calls
  as a `delta.tool_calls` chunk before the terminator, or (b) change
  `finish_reason` to a custom value like `"tool_loop_exhausted"` with an
  explanatory error event so the client knows the server gave up rather
  than that the client should fulfill the tool calls.
- **Test that should catch this:** Extend
  `test_streaming.py::test_stream_chat_completion_max_iterations_emits_tool_calls`
  to additionally assert that either `delta.tool_calls` is present on
  the terminator chunk, or that an error event names the tools.

### M-2: `/healthz` makes two redundant calls to `_list_local_models` (and thus two Ollama RPCs)

- **Location:** `src/linus/server.py:1154-1161` + `server.py:438`
- **Category:** performance pitfall
- **Description:** `healthz()` calls `_list_local_models()` directly at
  line 1155, then calls `_compute_degradations()` which calls
  `_list_local_models()` again at line 438. Each call hits the local
  Ollama daemon over HTTP.
- **Why it's a bug:** `/healthz` is a liveness probe — Streamlit and
  any external probe hit it on every page load. Two RPCs per probe
  (instead of one) doubles the load on Ollama and adds latency. The
  Streamlit landing in particular polls /healthz periodically.
- **Code excerpt:**
  ```python
  # server.py:1154-1161
  try:
      models = _list_local_models()
      ollama_reachable = True
  except HTTPException:
      models = []
      ollama_reachable = False

  effective_state, degradations = _compute_degradations()
  ```
- **Suggested approach:** Refactor `_compute_degradations()` to accept
  the already-fetched `models` list as an arg, or memoize
  `_list_local_models` with a short TTL (5s) since Ollama's installed
  model set rarely changes between probes.
- **Test that should catch this:** A test that monkeypatches
  `_list_local_models` with a call-counting mock and asserts the count
  is exactly 1 after a single `GET /healthz`.

### M-3: `AnthropicMessageRequest.max_tokens` not validated for positive value; `LINUS_MAX_TOOL_ITERATIONS` env var crashes server on non-int

- **Location:** `src/linus/server.py:75, 284, 1312-1313`
- **Category:** input validation gap
- **Description:** Two related validation gaps:
  - `AnthropicMessageRequest.max_tokens: int` accepts 0 or negative
    values without validation. Anthropic's spec requires `max_tokens
    >= 1`. The server translates whatever value (including -1, 0) to
    Ollama's `num_predict`, which for `num_predict=-1` means "no
    limit" — silently subverting the client's intent.
  - `_MAX_TOOL_ITERATIONS = int(os.environ.get("LINUS_MAX_TOOL_ITERATIONS",
    "6"))` at import time. If the env var is set to a non-integer
    string (e.g., "six", or accidentally "6.0"), `int()` raises
    `ValueError` and the server fails to start with a confusing
    traceback. A negative value (e.g., "-1") silently disables the
    tool loop entirely.
- **Why it's a bug:** First case: clients pass `max_tokens=0` as a
  cheap "just give me the stop_reason" probe and get a full
  unconstrained generation back. Second case: misconfiguration in
  `~/.zshrc` (typo on a numeric env var) breaks the server with no
  hint.
- **Code excerpt:**
  ```python
  # server.py:75
  _MAX_TOOL_ITERATIONS = int(os.environ.get("LINUS_MAX_TOOL_ITERATIONS", "6"))

  # server.py:284
  max_tokens: int
  ```
- **Suggested approach:** Use `Field(..., gt=0)` on `max_tokens` and
  wrap the env-var parse in a try/except that logs and falls back to
  the default. Same hardening applies to `LINUS_PORT`.
- **Test that should catch this:** A pydantic-validation test for
  `max_tokens=0`, `max_tokens=-1` on `/v1/messages` asserting 422; and
  an import-time test that sets `LINUS_MAX_TOOL_ITERATIONS=junk` and
  imports `linus.server` asserting either the default kicks in or a
  clear startup error message.

### M-4: `AnthropicInputMessage.role` is unvalidated `str`, allows arbitrary roles into the transcript

- **Location:** `src/linus/server.py:260-272`
- **Category:** input validation gap / schema mismatch
- **Description:** Anthropic's Messages API requires `role ∈ {"user",
  "assistant"}`. The pydantic model declares `role: str` with no
  enumeration. A client passing `role: "tool"` or `role: "system"` or
  `role: "foo"` slips through validation. `_anthropic_input_to_transcript`
  then folds it into the transcript with that role string verbatim.
  Combined with the explicit `role=system` block-out check at line
  1316, only the literal string `"system"` is filtered; everything else
  is forwarded to Ollama, which may or may not error depending on the
  model.
- **Why it's a bug:** Two scenarios — (a) a client experimenting with
  the Anthropic SDK passes a custom role and gets a 502 from Ollama
  with an opaque message instead of a clean 422 from validation; (b)
  the role string might confuse Ollama into running with an
  unexpected role hierarchy. Also a contract violation that breaks the
  promise to "speak the Anthropic Messages API shape."
- **Code excerpt:**
  ```python
  # server.py:260-272
  class AnthropicInputMessage(BaseModel):
      role: str
      content: str | list[AnthropicTextBlock | dict[str, Any]]
  ```
- **Suggested approach:** Replace `role: str` with `role:
  Literal["user", "assistant"]` and let pydantic emit the 422.
- **Test that should catch this:** `test_anthropic_compat.py` test
  posting `role="tool"` and asserting 422 with a structured detail.

### M-5: Empty model string passes validation, silently fixed up via `_resolve_model` preference walk

- **Location:** `src/linus/server.py:144, 577-601`
- **Category:** input validation gap
- **Description:** `ChatCompletionRequest.model: str` accepts the empty
  string. `_resolve_model("")` then checks `if "" in available` (always
  False) and falls through to the preference walk, returning the first
  available preference. The client asked for nothing and got something
  silently. Same for `AnthropicMessageRequest.model`.
- **Why it's a bug:** Cline / openclaw / a curl smoke test that
  accidentally omits the model name in JSON serialization (e.g.,
  serializing `None` to `""`) gets a "successful" response from a
  model the client never named. This is exactly the "fail loud, not
  silently swap" behavior the docstring at line 22-25 says is the
  design intent — but the empty-string case bypasses it.
- **Code excerpt:**
  ```python
  # server.py:577-601
  def _resolve_model(requested: str) -> str:
      available = _list_local_models()
      if requested in available:
          return requested
      for candidate in _MODEL_PREFERENCES:
          if candidate in available:
              return candidate
      raise HTTPException(...)
  ```
- **Suggested approach:** `Field(..., min_length=1)` on the `model`
  field of both request models, or an explicit `if not requested:
  raise HTTPException(400, ...)` early in `_resolve_model`.
- **Test that should catch this:** `test_chat_completions_empty_model_400`
  posting `{"model": "", "messages": [{"role": "user", ...}]}` and
  asserting 400 (or 422).

### M-6: `_resolve_model` 503 response semantics conflicts with /healthz reachable=True

- **Location:** `src/linus/server.py:567-601` + `1167-1169`
- **Category:** error handling gap
- **Description:** When Ollama is reachable but no preferred model is
  pulled, `_resolve_model` raises HTTP 503 ("Service Unavailable"). But
  `/healthz` independently classifies that exact state as `effective_state
  ="down"` AND reports `ollama_reachable=True`. A monitoring system
  pulling `/healthz` sees a "reachable" service that, when actually
  called, returns 503. 503 typically means "the upstream is down" — but
  here Ollama IS up, the model is missing.
- **Why it's a bug:** Status-code semantics matter for retries and
  alerts. Some HTTP clients (and load balancers) treat 503 as
  "transient, retry me" — which makes things worse here, because no
  amount of retrying will pull the missing model. A more accurate
  status would be 409 Conflict or 422 Unprocessable (the request is
  well-formed but the named model isn't pullable from this server's
  perspective).
- **Code excerpt:**
  ```python
  # server.py:591-601
  raise HTTPException(
      status_code=503,
      detail={
          "error": (
              f"Requested model {requested!r} is not pulled and no preferred fallback "
              f"({list(_MODEL_PREFERENCES)}) is locally available."
          ),
          ...
      },
  )
  ```
- **Suggested approach:** Change to HTTP 422 with a clear "missing model"
  error code, reserving 503 for the actual Ollama-unreachable case at
  line 335-338. Document the distinction in the route docstring.
- **Test that should catch this:** Update
  `test_resolve_model_raises_503_when_no_preference_available` to assert
  422 instead, with a structured `code: "model_not_pulled"` payload.

## Low findings

### L-1: `/v1/tools/{tool_name}/invoke` has no authentication and can be exposed if `LINUS_HOST=0.0.0.0`

- **Location:** `src/linus/server.py:1342-1421` + `1483`
- **Category:** security concern
- **Description:** The direct tool invocation endpoint is unauthenticated
  and allows arbitrary callers to invoke any registered tool. Currently
  `LINUS_HOST` defaults to `127.0.0.1` so this is bound to localhost —
  safe in single-user mode. But if an operator sets `LINUS_HOST=0.0.0.0`
  to expose the server on the LAN or via tunnel (common for Tailscale-
  bridged dev workflows), anyone on the network can invoke `paperqa.*`
  tools that may write files under `~/.linus/papers/`, read papers,
  consume API quota, etc.
- **Why it's a bug:** Defense in depth — the server has no mention of
  this constraint in its docstring, README, or startup logs. A future
  operator binding to 0.0.0.0 won't realize they've exposed the tool
  surface.
- **Code excerpt:**
  ```python
  # server.py:1483
  host = os.environ.get("LINUS_HOST", "127.0.0.1")
  ```
- **Suggested approach:** Either (a) add an optional `LINUS_API_KEY` env
  var that, if set, gates `/v1/tools/{tool_name}/invoke` and
  `/v1/chat/completions` via a simple bearer-token check, or (b) at a
  minimum emit a `WARNING` log at startup when `LINUS_HOST != 127.0.0.1`
  noting that all routes are unauthenticated.
- **Test that should catch this:** A test that imports the app under
  `LINUS_HOST=0.0.0.0` and asserts a startup warning is logged (or a
  configurable auth gate returns 401 when bypassed).

### L-2: `uuid.uuid4().hex[:24]` truncation reduces id collision space unnecessarily

- **Location:** `src/linus/server.py:94, 672, 1328`
- **Category:** edge case
- **Description:** Tool-call ids and Anthropic message ids are truncated
  to 24 hex chars (96 bits) instead of 32 (128 bits). 96 bits of
  randomness is still safe for any realistic id population (collision
  probability ~10^-18 at 10^9 ids), but the truncation has no apparent
  benefit and the full 32-char form is more consistent with OpenAI's
  own `call_*` format.
- **Why it's a bug:** Minor; cosmetic. The OpenAI format is e.g.
  `call_abc123def456...` typically 24-29 chars after the prefix; the
  Anthropic format is `msg_abc...` typically 24-char body. So the
  truncation actually matches Anthropic's wire shape — but not OpenAI's
  full-uuid form (which uses longer ids). Probably intentional to match
  Anthropic; flagging for review.
- **Code excerpt:**
  ```python
  # server.py:94
  id: str = Field(default_factory=lambda: f"call_{uuid.uuid4().hex[:24]}")
  ```
- **Suggested approach:** No change required if the [:24] matches the
  intended Anthropic shape; document the choice in a comment.
- **Test that should catch this:** Not needed.

### L-3: `_compute_degradations` swallows `_kb_artifact_paths()` failure too broadly

- **Location:** `src/linus/server.py:540-547`
- **Category:** error handling gap
- **Description:** The bare `except Exception` at line 542 swallows ALL
  exceptions including `MemoryError`, `KeyboardInterrupt`-derived (no,
  that's BaseException), and unrelated bugs in `_kb_artifact_paths`.
  The comment says "Defensive: linus.app.config import or env-var-
  resolution failure must not crash /healthz" — but masking ALL
  exception classes also masks future bugs the author of
  `_kb_artifact_paths` introduces.
- **Why it's a bug:** Future maintainability — if someone breaks
  `_kb_artifact_paths()` to raise `RuntimeError`, /healthz reports
  "live" silently instead of surfacing the issue.
- **Code excerpt:**
  ```python
  # server.py:540-547
  try:
      artifacts = _kb_artifact_paths()
  except Exception:
      artifacts = []
  ```
- **Suggested approach:** Narrow to `(ImportError, OSError, KeyError,
  ValueError)` per the comment's stated concerns, and log the
  exception at WARN level before continuing.
- **Test that should catch this:** Not a regression-testable concern
  per se; addressed by code review.

## Patterns / themes

Three concerning themes repeat across the findings:

**Single-thread test bias.** The 591-test suite is uniformly
single-threaded; concurrent execution is never exercised. C-1 (SQLite
race) and H-1 (streaming disconnect) both surface only under
concurrency. As Linus moves toward serving multiple Streamlit pages or
parallel agent fan-outs, this gap will produce production bugs invisible
in CI.

**Best-effort session persistence has weak durability guarantees.**
Both session-append paths (streaming H-1 and tool-call H-2) silently
drop data on the slightly-off-happy-path. The pattern of "best-effort"
storage backed by a broad `except: pass` makes failures invisible —
healthcheck and tests pass while real conversations lose context.
Surfacing storage failures as 5xx with a structured error would let
the UI surface a "history may be inconsistent" notice rather than the
current "everything looks fine, history just isn't there" failure mode.

**Pydantic models trust client input too liberally on string fields.**
`model: str`, `role: str` (Anthropic), `max_tokens: int` (Anthropic)
all admit values that break downstream invariants. The contract Linus
exports is meant to match OpenAI/Anthropic shapes; both upstream APIs
validate these fields with Literal/positive-int constraints. Closing
this gap is low-effort (Field constraints, Literal types) and surfaces
errors loudly at the contract boundary.

## What I checked but found clean

- **`_extract_tool_calls`** (line 640-676) — dict/object shape handling,
  empty-name skip, missing-function-attr skip all defensible.
- **`_format_tool_result`** (line 679-692) — None/str/JSON/fallback
  chain is complete; test coverage in `test_server_coverage.py`
  exhaustive.
- **`_message_to_ollama`** (line 700-731) — empty-content handling per
  role, tool_calls serialization, name + tool_call_id passthrough all
  correct.
- **`_anthropic_input_to_transcript`** (line 831-859) — string-content
  branch, list-of-blocks branch, dict-block branch (reachable via
  `model_construct`), non-text-block-drop all behave as documented.
- **`_ollama_finish_to_anthropic_stop_reason`** (line 862-868) — three
  explicit mappings + defensive default.
- **`_sse_format`** (line 871-878) — correct OpenAI SSE wire format.
- **`_streaming_chunk`** (line 881-909) — correct chunk envelope.
- **`/v1/sessions` POST** (line 1424-1446) — `req or
  CreateSessionRequest()` correctly handles None body; honors
  client-supplied id; surfaces created_at.
- **`/v1/sessions/{id}/messages` GET** (line 1449-1471) — 404 on
  unknown, ordered-by-idx return, correct dataclass-to-pydantic
  conversion.
- **`invoke_tool` async-handling** (line 1392-1399) —
  `inspect.iscoroutinefunction` for async, `asyncio.to_thread` for
  sync, both paths exercised in tests.
- **`invoke_tool` error mapping** (line 1400-1417) — HTTPException
  re-raise, TypeError → 422, broad Exception → 500 with structured
  detail and no stack-trace leak. Documented contract honored.
- **`_compute_degradations` happy/degraded/down classification** —
  comprehensively tested in `test_healthz.py`.
- **`/v1/messages` streaming-not-implemented 501** — clean
  structured-error response.
- **`main()` entry-point env-var honoring** — correct host/port/reload
  forwarding to uvicorn; tests cover defaults + overrides.
