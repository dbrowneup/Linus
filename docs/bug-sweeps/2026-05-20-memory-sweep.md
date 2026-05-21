# Memory + agents bug sweep — 2026-05-20

Read-only audit of the persistence + concurrency layer landed under
`src/linus/memory/` (episodic store, audit log, session store, hashing) and
`src/linus/agents/spawner.py` (asyncio.gather fan-out). Triage by Maestro;
this report does NOT fix anything.

## Scope

Files reviewed in full:

- `src/linus/memory/episodic.py` (Layer C, SQLite WAL + content hashes)
- `src/linus/memory/audit_log.py` (append-only JSONL audit)
- `src/linus/memory/sessions.py` (within-session SQLite store)
- `src/linus/memory/hashing.py` (content hash helpers)
- `src/linus/agents/spawner.py` (asyncio.gather agent fan-out)

Test files cross-referenced: `test_episodic.py`, `test_audit_log.py`,
`test_sessions.py`, `test_spawner.py`.

Hermetic suite at sweep time: **591 passed in 2.69s**.

---

## Critical findings

### C1. `sessions.py` `append_message` has a read-then-write race on `idx`

**File:** `src/linus/memory/sessions.py` lines 211–241
(`append_message`) and 243–280 (`append_messages`).

The pattern is:

```python
with conn:
    cursor = conn.execute(
        "SELECT COALESCE(MAX(idx), -1) + 1 AS next_idx FROM session_messages WHERE session_id = ?",
        (session_id,),
    )
    next_idx = cursor.fetchone()["next_idx"]
    conn.execute(
        "INSERT INTO session_messages(...) VALUES (?, ?, ?, ?, ?)",
        (session_id, next_idx, role, content, created_at),
    )
```

`sqlite3` connections default to `isolation_level="DEFERRED"`, which only
acquires a write lock when the first write statement executes. The SELECT
runs without a lock, so two concurrent callers (different threads, or
different processes against the same DB) can both compute the same
`next_idx`, then one INSERT will fail with
`sqlite3.IntegrityError: UNIQUE constraint failed:
session_messages.session_id, session_messages.idx`.

The class docstring on `SessionStore` says "The instance is not threadsafe;
create one per request handler thread if needed." But two facts make this
load-bearing rather than just a comment:

1. `sqlite3.connect(..., check_same_thread=False)` is set on line 126, which
   disables SQLite's thread-safety check but does NOT make the connection
   thread-safe — it just lets you call it from multiple threads without
   raising.
2. `get_default_store()` (lines 357–362) returns a **process-wide singleton**.
   FastAPI under Starlette can dispatch endpoint handlers across multiple
   threads (the `TestClient` runs in the test thread; real deployments under
   `uvicorn --workers 1` with `asyncio.to_thread` for sync handlers can fan
   out). Any concurrent chat append on the same session_id can collide.

Mitigation when triaging: switch to `BEGIN IMMEDIATE` to acquire the write
lock upfront, or use `INSERT INTO session_messages SELECT ?, COALESCE(MAX(idx), -1) + 1, ?, ?, ? FROM session_messages WHERE session_id = ?`
as a single atomic statement.

**Severity:** critical (data-loss adjacent — concurrent chat appends silently
drop or 500).

### C2. `get_default_store()` singleton has a check-then-init race

**File:** `src/linus/memory/sessions.py` lines 354–362.

```python
_default_store: SessionStore | None = None

def get_default_store() -> SessionStore:
    global _default_store
    if _default_store is None:
        _default_store = SessionStore()
    return _default_store
```

Standard check-then-init with no lock. Two threads both reading `None`,
both constructing a `SessionStore`, both writing `_default_store` — last
writer wins, the loser's connection is leaked (never closed; no `__del__`
on `SessionStore`). The leaked connection holds a file descriptor and a
SQLite memory arena until process exit.

In production with `uvicorn`'s default worker pool, this is reachable on
cold start under concurrent first requests.

**Severity:** critical (resource leak + duplicated underlying state; both
stores observe the same DB so data isn't corrupted, but the bookkeeping is
wrong and FDs leak).

---

## High findings

### H1. `spawner.py` propagates exceptions outside the broad-except blocks

**File:** `src/linus/agents/spawner.py` lines 114–166 (`_run_sync`).

The module docstring promises:

> Per-task exceptions are caught and surfaced as :attr:`AgentResult.error`;
> they are *not* raised. The spawner always returns a complete result list.

But `_run_sync` only wraps two call sites in `try/except`:
`_resolve_model(...)` (lines 120–129) and `ollama.chat(...)`
(lines 140–149). The message-extraction code below (lines 151–158) runs
unprotected:

```python
content = ""
message = response.get("message") if isinstance(response, dict) else None
if isinstance(message, dict):
    content = message.get("content", "") or ""
elif message is not None and hasattr(message, "content"):
    content = getattr(message, "content", "") or ""
```

A weird ollama response shape (e.g. `message` is a list, or a typed object
whose `.content` property raises on access) bubbles `AttributeError` /
`TypeError` out of the thread, through `asyncio.to_thread`, into
`asyncio.gather`. Because `gather` is called WITHOUT
`return_exceptions=True` (line 111), the first such exception cancels the
batch and the partial results are lost — directly contradicting the
"always returns a complete result list" guarantee.

Two fixes possible (Maestro pick):
1. Wrap the message-extraction in the same outer try/except so any
   `Exception` becomes an `AgentResult.error`.
2. Pass `return_exceptions=True` to `gather` and convert any escaped
   exception into a synthesized `AgentResult` at the call site.

**Severity:** high (batch-failure-isolation guarantee is false for a class
of inputs the tests don't exercise).

### H2. `episodic.py` IN-list query crashes past SQLite's parameter limit

**File:** `src/linus/memory/episodic.py` lines 390–398.

```python
if isinstance(value, list | tuple):
    if not value:
        return []
    placeholders = ",".join("?" * len(value))
    where_clauses.append(f"{key} IN ({placeholders})")
    params.extend(value)
```

SQLite's default `SQLITE_LIMIT_VARIABLE_NUMBER` is 999 (libsqlite < 3.32.0)
or 32766 (>= 3.32.0). Passing a list of >999 / >32766 values raises
`sqlite3.OperationalError: too many SQL variables`. The Phase 2h.3 recall
layer is documented to sit on top of this method; a recall-by-hash with
1000+ candidate hashes will explode.

Mitigation: chunk in groups of 500 and union; or document the limit and
raise a more informative error.

**Severity:** high (production-realistic recall sizes can trip this).

### H3. `episodic.py` claims "single-writer-safe" but autocommit + no
explicit transaction wrapping multi-step writes

**File:** `src/linus/memory/episodic.py` lines 247–261 (`_connection`) and
265–279 (`migrate`).

```python
conn = sqlite3.connect(self.db_path, isolation_level=None)
```

`isolation_level=None` puts sqlite3 into **autocommit mode** — every
statement commits immediately, and `with conn:` no longer wraps a
transaction (the context-manager protocol relies on the default isolation
level to begin/commit). `migrate()` then does:

```python
conn.executescript(_SCHEMA_DDL_V1)  # autocommit per statement
current = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
if current is None or current < SCHEMA_VERSION:
    conn.execute("INSERT INTO schema_version (...) VALUES (?, ?)", ...)
```

A crash between `executescript` and the INSERT leaves the tables created
but `schema_version` empty. On the next start, `current is None` → INSERT
runs (good), but if SCHEMA_VERSION ever bumps to 2 there's no DDL applied
for the v1→v2 step; the version row would be inserted as v2 without the
schema migrated. Currently fine because DDL is v1-only; latent bug for
the first real migration.

Also: the docstring at lines 23–30 says "single-writer-safe via SQLite's
default transaction model" but autocommit is NOT the default transaction
model. Each `write_record` INSERT is its own auto-committed statement, which
is atomic on its own but loses any future ability to wrap "write record +
write audit-log entry" in a cross-store transaction.

**Severity:** high (migration correctness; latent future-bug for any v2
schema).

### H4. `episodic.py` doc claims `_utcnow` collides every microsecond, but
`time.time_ns()` is NOT used here — schema/spec inconsistency

**Files:**
- `src/linus/memory/episodic.py` line 182–184 + 277: `_utcnow()` returns
  ISO-8601 microsecond-resolution string.
- `src/linus/memory/audit_log.py` line 111–113: same.
- `src/linus/memory/sessions.py` line 190, 224, 256: uses `time.time_ns()`.

DEC-0030 (per the system prompt context and the `sessions.py` docstring
at lines 36–41) chose `time.time_ns()` to "avoid same-second ordering
collisions on fast back-to-back appends." `sessions.py` honors this.
`episodic.py` and `audit_log.py` use ISO-8601 microsecond strings —
which DO have microsecond resolution, but the format is different (string
vs int) and microsecond collisions on a fast modern Apple Silicon write
loop are reachable (Python overhead per `datetime.now()` is ~200ns;
under contention or coarse clocks two events can share a microsecond).

Two concerns:
1. **Schema inconsistency:** the timestamp column type differs across
   stores (TEXT ISO-8601 in episodic; INTEGER nanoseconds in sessions).
   The audit log's JSONL is TEXT ISO-8601. Joining episodic and audit-log
   records by timestamp requires a parse on every read.
2. **DEC-0030 compliance:** if DEC-0030 mandates ns resolution
   (system-prompt verbiage suggests it), episodic + audit_log are
   non-compliant.

Mitigation: align all three stores on `time.time_ns()` (probably the
right substrate) and emit ISO-8601 only for human-display sugar at the
API boundary. Or document the inconsistency in DECISIONS.md.

**Severity:** high (spec drift; cross-store correlation is uglier than it
should be).

---

## Medium findings

### M1. `audit_log.py` `_append_json` claims partial-line crash-safety it
can't deliver

**File:** `src/linus/memory/audit_log.py` lines 73–78, 184–192, 224–237.

The docstring promises:

> Atomic append: each write is one `write()` call followed by `flush()` and
> `fsync()` so partial lines cannot survive a crash.

`write(serialized + "\n")` is ONE Python call but is not guaranteed to be
one atomic syscall — on Linux it usually is for writes under PIPE_BUF
(4096 bytes), but JSON dispatch events can easily exceed 4096 bytes
(`per_layer_breakdown` + tag lists + hash arrays). `fsync` after write
flushes whatever made it to disk; if the write was split into two syscalls
and a power loss happened between them, the file contains a partial line.

Additionally:

- The parent **directory** is never `fsync`'d. After
  `mkdir(parents=True, exist_ok=True)` + `path.touch(exist_ok=True)`, a
  crash before the first dispatch can leave the directory entry not
  durable on some filesystems. macOS HFS+/APFS is typically forgiving;
  Linux ext4 with `data=writeback` is not.
- `iter_events` will pass a partial line to `json.loads`, raising
  `json.JSONDecodeError`. Generator does not skip malformed lines
  (only blank lines). One corrupt tail line breaks reads forever.

Mitigations: write a temporary file + rename for atomicity (heavy);
truncate-to-last-newline on read; or accept the residual risk and weaken
the docstring promise to "single-statement-fsync — partial lines on a
mid-write crash are possible and the reader skips them."

**Severity:** medium (low probability, but the docstring overstates the
guarantee).

### M2. `audit_log.py` opens + closes the file on every append

**File:** `src/linus/memory/audit_log.py` lines 234–237.

```python
with open(self.path, "a", encoding="utf-8") as fh:
    fh.write(serialized + "\n")
    fh.flush()
    os.fsync(fh.fileno())
```

For high-volume Worker dispatch (the documented future Phase 3+ load), this
is N opens, N close + fsync. Persistent handle + periodic fsync would be
significantly faster. Single-writer v0 is fine; flag as the obvious place
to revisit before Phase 3 fan-out.

**Severity:** medium (performance pitfall under future load, not a
correctness bug).

### M3. `audit_log.py` `iter_events` blows up on a single malformed line

**File:** `src/linus/memory/audit_log.py` lines 249–258.

```python
def iter_events(self) -> Iterator[dict[str, Any]]:
    if not self.path.exists():
        return
    with open(self.path, encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            yield json.loads(raw)
```

`json.loads(raw)` raises `JSONDecodeError` on the first malformed line.
The generator is consumed up to that line, then explodes. A user reading
events programmatically loses ALL records after the corruption point —
the opposite of "audit log is the cryptographic spine that lets the
episodic store be verified after the fact."

Mitigation: catch `JSONDecodeError`, log + skip, continue. Tradeoff is
silent corruption hiding. Either way, deserves a triage decision.

**Severity:** medium (one bad line = total read failure).

### M4. `sessions.py` `append_messages` shares a single `created_at`
across the batch

**File:** `src/linus/memory/sessions.py` lines 256, 266, 273.

```python
created_at = time.time_ns()
...
for offset, (role, content) in enumerate(messages):
    rows.append((session_id, next_idx + offset, role, content, created_at))
```

All N messages in the batch get the same nanosecond timestamp. By design
(documented as atomic batch), but means a downstream consumer ordering
messages by `created_at` and not `idx` sees a tie. The `idx` field is the
authoritative ordering primitive (per the docstring at line 40); this is a
"correct as designed but easy to misuse" trap.

Mitigation: compute `time.time_ns() + offset` per message so timestamps
are strictly monotonic within the batch, OR document the tie explicitly.

**Severity:** medium (correctness depends on downstream consumer using
`idx` as ordering key).

### M5. `episodic.py` reuses `rowid` as both column name and SQLite
implicit alias

**File:** `src/linus/memory/episodic.py` lines 155.

```sql
rowid INTEGER PRIMARY KEY AUTOINCREMENT,
```

SQLite reserves `rowid` as the implicit primary-key alias for non-WITHOUT
ROWID tables. Declaring an explicit `rowid INTEGER PRIMARY KEY
AUTOINCREMENT` column is legal but creates ambiguity: `SELECT rowid FROM
t` returns the same value as `SELECT *` projecting the explicit column,
but downstream tooling (sqlite browsers, ORMs) may treat them differently.
The conventional pattern is `id INTEGER PRIMARY KEY` (rowid alias) or
`id INTEGER PRIMARY KEY AUTOINCREMENT` (separate sequence). Functionally
the tests pass; stylistically this is a footgun for future maintainers.

**Severity:** medium (works today; flag for future schema migration).

---

## Low findings

### L1. `hashing.py` `verify_hash` uses `==` instead of `hmac.compare_digest`

**File:** `src/linus/memory/hashing.py` line 137.

```python
return content_hash(payload) == expected
```

For content-addressability this is fine (it's not authentication). But if
the audit-log integrity-verification sweep (out-of-scope per the audit-log
docstring but mentioned as Phase 3+) ever uses this in a context where a
network-adjacent caller can submit `expected` values, timing-attack
resistance via `hmac.compare_digest` is the canonical pattern.

**Severity:** low (defense-in-depth; not load-bearing today).

### L2. `audit_log.py` and `episodic.py` capture `DEFAULT_*_PATH` at
import time

**Files:**
- `src/linus/memory/audit_log.py` line 101: `DEFAULT_AUDIT_PATH = Path.home() / ".linus" / "audit.jsonl"`
- `src/linus/memory/episodic.py` line 73: `DEFAULT_DB_PATH = Path.home() / ".linus" / "episodic.db"`
- `src/linus/memory/sessions.py` line 57: `DEFAULT_DB_PATH = Path.home() / ".linus" / "sessions.db"`

`Path.home()` evaluates once at import. If `HOME` is mutated mid-process
(some test harnesses do this), the default does NOT update — only the
env-override `LINUS_HOME` / `LINUS_SESSIONS_DB` does. The `default_*_path()`
functions short-circuit through the env-override but their fallback uses
the import-time constant.

This is consistent with the existing test contract (the tests patch
`LINUS_HOME`, not `HOME`), so it's working as designed.

**Severity:** low (working as designed but worth noting as a gotcha).

### L3. `sessions.py` `delete_session` does not surface FK cascade error

**File:** `src/linus/memory/sessions.py` lines 282–292.

The `ON DELETE CASCADE` on `session_messages.session_id` relies on
`PRAGMA foreign_keys = ON` being set per connection (line 129) — which it
is. But if a future code path opens a connection that forgets to set the
pragma (e.g., a sqlite3 CLI session), `delete_session` will succeed at
removing the session row but leave orphan `session_messages`. The
schema's `FOREIGN KEY` is enforced only when the pragma is on.

Mitigation: enforce the pragma at connection time (done); add a constraint
check on connection open in `_connect`. Not load-bearing today.

**Severity:** low (correct today; latent fragility if pragma is dropped).

### L4. `spawner.py` `max_tokens` not validated

**File:** `src/linus/agents/spawner.py` line 66, 136–137.

`AgentTask.max_tokens: int | None` — accepts any int. Negative values pass
through to ollama's `num_predict` option. Ollama's behavior on negative
values is undefined in the client; could be a silent no-op or an error.

Mitigation: validate `max_tokens > 0` in `AgentTask.__post_init__` (would
need to drop `frozen=True` or use a `__post_init__` workaround for
frozen dataclasses).

**Severity:** low (input validation gap; unlikely to be exercised).

### L5. `audit_log.py` Unicode in JSONL with `ensure_ascii=False` —
log-injection vector

**File:** `src/linus/memory/audit_log.py` lines 227–233.

`ensure_ascii=False` is by design (test covers it on line 530). But this
means any caller-controlled string field (tags, worker_id, session_id) can
embed a `\n` literal — wait, JSON serializes `\n` as `\\n` in string
context, so newline-injection is NOT possible. But Unicode
right-to-left override (U+202E) and other formatting characters DO pass
through. If audit logs are ever displayed in a terminal or HTML, a hostile
tag could rearrange display. Low practical risk; tag values today are
all internal.

**Severity:** low (display-layer concern, not storage corruption).

---

## Patterns

- **`isolation_level=None` (autocommit) is set on episodic.py's
  connection** but NOT on sessions.py. The two stores have different
  transaction models. The audit-log doesn't use SQLite. Picking one
  model and applying it consistently would shrink the surprise budget.

- **All three stores capture default paths at import time.** Consistent,
  but worth knowing.

- **Single-writer assumption is documented but not enforced.** The
  audit-log, episodic, and session stores each claim single-writer-v0
  but offer no lock, no advisory file-lock, and no detection. Phase 3+
  multi-Worker dispatch is on the roadmap; the spec doesn't yet say HOW
  the boundary will be enforced.

- **Broad `except Exception:` clauses with `# noqa: BLE001`** appear in
  `spawner.py` (lines 121, 141). These are deliberate per-comment, but
  they don't cover ALL the exception surface in `_run_sync` (see H1).
  Pattern is: catch around the risky external call, leave subsequent
  pure-Python munging unprotected. Subsequent munging is rarely as safe
  as it looks.

- **`with conn:` semantics depend on `isolation_level`.** In
  `sessions.py` it works (default DEFERRED isolation). In `episodic.py`
  with `isolation_level=None`, it's effectively a no-op for transaction
  bracketing.

## Clean

- **`hashing.py`** is solid. Canonical JSON with sort_keys, no
  whitespace, ensure_ascii=False, allow_nan=False. Algorithm prefix in
  the digest. Bytes / str / JSON branches all sensible. No dict-ordering
  determinism bugs.

- **`audit_log.py` event dataclasses' `__post_init__` validation** is
  good — DispatchEvent rejects unknown `cot_budget`, `memory_mode`,
  `context_overflow_action` values per DEC-0031 vocabulary.

- **`episodic.py` `read_records` query-key allowlist** correctly rejects
  unknown filter keys with `ValueError` rather than silently returning
  the whole table — explicitly anti-footgun.

- **`spawner.py` `asyncio.Semaphore` + `asyncio.to_thread`** is the
  correct pattern for bounded concurrency over a sync I/O library. The
  test `test_concurrency_actually_parallelizes` validates this empirically.

- **Test coverage on the in-scope modules is dense.** Edge cases like
  empty IN-lists, forged-hash overwrite, NaN rejection, blank-line
  skipping, str-vs-Path constructor inputs are all covered.

---

## Most-concerning single finding

**C1** (`sessions.py` `append_message` read-then-write race on `idx`)
is the most concerning because:

1. It's reachable today under any concurrent chat-completion load against
   the same `session_id` (the singleton `get_default_store()` makes it
   one DB across all requests).
2. It silently violates the UNIQUE constraint, surfacing as an
   `IntegrityError` 500 to the user OR a SQLITE_BUSY retry — either way
   message data is at risk.
3. The fix is a one-line SQL change (single-statement insert with
   computed idx, or `BEGIN IMMEDIATE`).

C2 (singleton race) compounds C1 because the multi-store scenario opens
multiple connections, multiplying the race surface.

## Recommended triage order

1. **C1 + C2** together: fix the session-store concurrency model
   (atomic-insert + lock around `_default_store`).
2. **H1**: tighten `_run_sync` exception handling OR add
   `return_exceptions=True` to gather + adapter.
3. **H4**: settle the timestamp-substrate decision (ns vs ISO-8601);
   update DECISIONS.md.
4. **H2 + H3** when migration / large-recall lands.
5. M and L findings as opportunistic cleanup.
