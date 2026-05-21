## knowledge/\* — bug sweep 2026-05-20

**Scope:** `src/linus/knowledge/{paperqa,rigor,entity_kb,adapter,retriever}.py` + tests
**Total findings:** 14 (critical: 0, high: 4, medium: 6, low: 4)
**Surveyor:** bug-sweep subagent (read-only; no fixes proposed)
**Base SHA:** `9a6a276` (origin/main; the dispatch prompt cited `e1a07af` which has been superseded)
**Test baseline:** 591 passing.

This sweep covered the corpus + RAG + grounding layer (`adapter.py`, `retriever.py`,
`paperqa.py`, `rigor.py`, `entity_kb.py`) and the matching hermetic tests. Findings
emphasize the rigor-gate auto-wiring path (DEC-0059 contract) and the fail-open
discipline that paper-qa's `answer()` requires.

## Critical findings

None. Despite a careful trace through the rigor auto-gate and the entity-KB lazy
load there is no path I can identify that leaks a fabricated citation through the
gate, mutates the KB DB, or loses data. The contracts hold; the bugs surfaced are
correctness drift and operational pitfalls, not data-integrity violations.

## High findings

### H1 — `KBEntityLookup._ensure_loaded` is not thread-safe; two concurrent first-call lookups can double-parse the GraphML and produce divergent in-memory indices

**File:** `src/linus/knowledge/entity_kb.py:185-245`
**Category:** Race condition
**Severity:** high

```python
def _ensure_loaded(self) -> None:
    if self._index is not None:
        return
    if not self._graphml_path.exists():
        raise FileNotFoundError(...)
    g = nx.read_graphml(self._graphml_path)
    ...
    self._graph = g
    self._index = index
    self._source_tag = source_tag
```

The check `if self._index is not None: return` is followed by the parse and the
assignment without any lock. The rigor gate runs inside the FastAPI server which
already serves concurrent requests, and the `default_kb_lookup()` factory returns
a `ChainedEntityLookup` instance that is intended to be process-wide (see
`paperqa.py:_resolve_entity_backend` and the `rigor.check` tool — both call
`default_kb_lookup()` per-invocation, but a future caller that caches the chain
across requests will hit the race). Two concurrent first calls both pass the
`is None` check, both invoke `nx.read_graphml` (an expensive op against a
potentially-large file mmap'd by NetworkX), and the second writer wins the index
assignment. Each call also recomputes `_short_sha` on the GraphML file (separate
file open + full read). The window is large enough — `read_graphml` parses XML —
that two threads racing is realistic. The damage is duplicated work and a brief
window where one observer sees the partially-built index from `self._graph = g`
before the matching `self._index = index` is set (the docstring claims
"`assert self._index is not None` after _ensure_loaded", which is true at
sequence-end but only by luck if interleaving lands wrong).

A `threading.Lock` (or `threading.RLock` so `lookup_entity` can recursively
acquire when called from a tool dispatcher already holding it) gated around the
parse + assignment is the standard fix. The fix is one import + a lock acquire;
no change to the public surface.

**Test that should catch:** start two threads that both call `lookup_entity` on
a fresh `KBEntityLookup` instance pointed at the fixture, with `read_graphml`
monkey-patched to a stub that sleeps briefly + counts calls; assert exactly one
call.

### H2 — `_AdapterPaperLookup.get_page_count` calls `adapter.get_paper` a second time on every citation, doubling SQLite round-trips

**File:** `src/linus/knowledge/paperqa.py:561-580`
**Category:** Performance pitfall
**Severity:** high (becomes critical for any answer with >20 citations)

```python
def get_paper(self, paper_id: str) -> Any | None:
    return self._adapter.get_paper(paper_id)

def get_page_count(self, paper_id: str) -> int | None:
    paper = self._adapter.get_paper(paper_id)   # second hit
    if paper is None:
        return None
    page_count = getattr(paper, "page_count", None)
    ...
```

The rigor gate's `check_citations` (`rigor.py:380-441`) calls `papers.get_paper`
first and `papers.get_page_count` second on every citation. Both calls in the
adapter wrapper hit `adapter.get_paper(paper_id)`, which executes a parameterized
SELECT against SQLite each time. For an answer with N citations this is 2N
SELECTs where N would suffice. The adapter does not cache — `get_paper`
constructs a fresh `Paper` dataclass per call. For paper-qa answers with
`max_sources=10` this is +10 SQLite round-trips; for the demo with high source
counts it scales linearly. SQLite is fast but not free, and the second lookup
is a load-bearing path for every answer the system produces.

Two reasonable fixes: (a) cache the last lookup inside `_AdapterPaperLookup`
(simplest — `get_page_count` reads from the cached row if `paper_id` matches the
last `get_paper` call); (b) refactor `PaperLookup` so `get_paper` returns a
record carrying its own `page_count` and `get_page_count` reads from it. Option
(b) is cleaner but changes the Protocol surface; (a) is a 4-line change inside
the wrapper.

**Test that should catch:** wrap the `_FakeKBAdapter` in `test_paperqa.py` with
a call-counter; run `check_grounding` with a 5-citation claim; assert
`get_paper` was called exactly 5 times (not 10).

### H3 — `_resolve_entity_backend` swallows `FileNotFoundError` and silently falls back to the builtin stub even when the KB output dir is misconfigured

**File:** `src/linus/knowledge/paperqa.py:592-615`
**Category:** Error handling gap
**Severity:** high

```python
def _resolve_entity_backend() -> Any | None:
    try:
        from linus.knowledge.entity_kb import default_kb_lookup
        return default_kb_lookup()
    except (ImportError, FileNotFoundError, AttributeError):
        try:
            from linus.knowledge.rigor import BuiltinEntityLookup
            return BuiltinEntityLookup()
        except Exception:
            return None
```

`default_kb_lookup()` is cheap — it just constructs a `ChainedEntityLookup`
without reading any file (see `entity_kb.py:300-310`). So `FileNotFoundError`
will NOT fire here; the file check is inside `KBEntityLookup._ensure_loaded`
which runs at first lookup, not at construction. The `FileNotFoundError`
clause is dead.

This matters because the actual `FileNotFoundError` from a missing GraphML
fires inside `KBEntityLookup.lookup_entity` — at gate-evaluation time — and
that exception is NOT caught by `_resolve_entity_backend`'s try block. It
DOES land inside `_run_rigor_gate`'s broad `except Exception` (paperqa.py:671),
which causes the whole rigor field to come back as `None` for any answer where
even one entity lookup hits the missing file. The user gets `rigor=None`
(silently fail-open) instead of the documented behavior of a builtin-fallback
result with `source: "stub:builtin"` on every entity.

Note also that the chain is `KBEntityLookup → BuiltinEntityLookup`: if the
primary raises (not returns None), the fallback inside `ChainedEntityLookup`
is never reached because `ChainedEntityLookup.lookup_entity` does not catch
exceptions:

```python
def lookup_entity(self, name: str, kind: str | None = None) -> dict[str, Any] | None:
    for backend in self._backends:
        result = backend.lookup_entity(name, kind=kind)   # may raise
        if result is not None:
            return result
    return None
```

Two bugs interact: (1) the misplaced `FileNotFoundError` clause in
`_resolve_entity_backend` (it catches at construction-time but the error is
raised at lookup-time), and (2) `ChainedEntityLookup` does not handle raises
from a primary backend, so the documented "well-known anchors still resolve
even if KB is missing" promise fails open instead of falling through.

Fix sketch: have `ChainedEntityLookup.lookup_entity` catch `FileNotFoundError`
(and only that) per-backend, continuing to the next backend on the catch. The
fallback chain then degrades gracefully when the KG file is missing without
needing the resolver to pre-check.

**Test that should catch:** point `KBEntityLookup` at a non-existent path,
compose with `BuiltinEntityLookup` in a chain, call `lookup_entity("BRCA1")`,
assert it returns the builtin's stub dict (not raises).

### H4 — `KnowledgeBaseAdapter._connect` keeps the SQLite connection open across the dataclass's lifetime with no `__del__` / weakref finalizer

**File:** `src/linus/knowledge/adapter.py:151-219`
**Category:** Resource leak
**Severity:** high

```python
@dataclass
class KnowledgeBaseAdapter:
    db_path: Path = field(default_factory=lambda: DEFAULT_METADATA_DB)
    _conn: sqlite3.Connection | None = field(default=None, init=False, repr=False)

    def _connect(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn
        ...
        conn = sqlite3.connect(uri, uri=True)
        ...
        self._conn = conn
        return conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
```

The class docstring says "Use :meth:`close` (or the context-manager form
``with KnowledgeBaseAdapter() as kb: ...``) to release the connection
deterministically; otherwise garbage collection will close it." This is
unsafe in practice on the rigor gate path: `paperqa.py:_resolve_paper_backend`
constructs a fresh `KnowledgeBaseAdapter()` per `_run_rigor_gate` invocation
(once per `paperqa.answer`), wraps it in `_AdapterPaperLookup`, and never
closes it. Each call leaks a SQLite file handle until CPython's refcount
drops to zero. With paper-qa answers running serially this works because
each adapter goes out of scope at function return — but the `_AdapterPaperLookup`
holds a reference to the adapter as `self._adapter`, and the
`_AdapterPaperLookup` is the return value flowing into `check_grounding`'s
`papers=` parameter, where it remains live for the gate evaluation. The
adapter falls out of scope at the end of `_run_rigor_gate`; the connection
is closed by `sqlite3.Connection.__del__` only when CPython gets around to
it, which on PyPy or under GC pressure may be delayed.

The fix is straightforward but matters: either give `KnowledgeBaseAdapter`
a `__del__` that closes the connection, or have `_resolve_paper_backend`
return a context-managed wrapper, or have `_run_rigor_gate` use the
`with KnowledgeBaseAdapter()` form. The cleanest is `__del__` on the
adapter — but `__del__` on dataclasses needs care (the `_conn is not None`
guard already exists in `close`).

**Test that should catch:** in `test_knowledge_adapter.py` or
`test_paperqa.py`, run 1000 paperqa answers against a fake adapter that
counts open connections; assert no growth.

## Medium findings

### M1 — `paperqa.py:_run_async` constructs and destroys a `ThreadPoolExecutor` per inside-loop call

**File:** `src/linus/knowledge/paperqa.py:501-538`
**Category:** Performance pitfall
**Severity:** medium

```python
with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
    future = pool.submit(_runner)
    return future.result()
```

Every call to a `paperqa.*` tool from inside an event loop (e.g. inside FastAPI
which runs every handler on an event loop) spins up a thread pool with one
worker, submits one task, and tears the pool down. The thread itself runs the
new event loop. This works but wastes ~0.5–1 ms of allocator + thread-creation
overhead per call. With paper-qa's `answer` already in the hundreds-of-ms
range this is in the noise, but the test surface
(`test_run_async_works_inside_running_loop`) exercises it once per test run.
A module-level singleton executor or a `loop.run_in_executor` against the
default ThreadPoolExecutor would be lighter. Not a correctness bug; flagged
for future hot-path tuning.

### M2 — `entity_kb.py` computes `_short_sha` (a full file SHA256) at every `_ensure_loaded` call — wasted work on the first call, and the file may not be the GraphML on a future writer

**File:** `src/linus/knowledge/entity_kb.py:126-138, 218`
**Category:** Performance pitfall + minor correctness
**Severity:** medium

```python
def _short_sha(path: Path, length: int = 12) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:length]
```

For Dan's actual corpus (16k papers → potentially MB-scale GraphML) this is
not catastrophic but it's a full file scan that happens once per process on
first lookup. NetworkX `read_graphml` already read the same bytes via the XML
parser. The redundant scan is gratuitous; a streaming `update` interleaved
with the XML parse is impractical, but reusing the bytes via
`hashlib.file_digest(path.open('rb'), 'sha256')` (3.11+) is the modern
single-pass form. More importantly, this read happens BEFORE the parse — if
the file is corrupted mid-write (e.g., the KB regenerator is interrupted
between writing first half and second half), `_short_sha` succeeds, returns
a stable-looking hash of the partial bytes, and the subsequent
`nx.read_graphml` either raises or worse, parses a truncated graph silently
(NetworkX's GraphML parser is lenient about missing closing tags in some
cases). The `source` tag the user sees in their grounded-entity dict would
then be a hash of a corrupted KG that was silently accepted as the ground
truth.

The right shape is to do the parse first, then the hash; or skip the hash
entirely and use `Path.stat().st_mtime_ns` as a cheap cache-key proxy.

**Test that should catch:** truncate the fixture GraphML mid-XML-document
and pass to `KBEntityLookup.lookup_entity`; assert it raises a clean
parse-error rather than silently indexing partial content with a
plausible-looking source hash.

### M3 — `_extract_citations` accepts dicts with truthy-but-zero `paper_id` (e.g. `0`, `False`) and converts them to a citation with `paper_id=None`, masking malformed input

**File:** `src/linus/knowledge/rigor.py:255-277, 380-394`
**Category:** Input validation gap
**Severity:** medium

```python
def _extract_citations(claim: ClaimDict) -> list[dict[str, Any]]:
    citations = claim.get("citations")
    if isinstance(citations, list):
        return [c for c in citations if isinstance(c, dict)]
    ...
```

The extractor admits any dict (no validation on `paper_id` type), then
`check_citations` does `paper_id = citation.get("paper_id")` followed by
`if not paper_id`. `not paper_id` is True for `None`, empty string, `0`,
`False` — but only `None` and `""` are legitimately "missing." A Worker
returning a JSON int `0` as a paper_id would currently produce a
`missing_evidence` warning rather than an `unresolved_citation` error, and
the user gets a misleading severity classification. Similarly the second
read `citation.get("page")` is then passed to `int(page)` (rigor.py:413)
which accepts numeric strings, floats, and `True` (`int(True) == 1`). A
Worker returning `page: true` resolves to page 1.

The right fix is a small per-citation validator that requires `paper_id` to
be a non-empty string and `page` (if present) to be either None or an int.
Anything else is a warning with a more specific `kind` than
`missing_evidence`. The current behavior surfaces malformed Worker output
as a benign warning, defeating the gate's purpose of catching fabrication.

**Test that should catch:** call `check_citations` with
`{"citations": [{"paper_id": 0, "page": True}]}` against a populated
backend; assert at least one error-severity failure surfaces (today: one
warning, no errors, gate passes).

### M4 — `_run_rigor_gate` sets `entities: []` on the claim it constructs from a paper-qa answer, so the entity check never runs against the synthesis output

**File:** `src/linus/knowledge/paperqa.py:636-677`
**Category:** Logic gap
**Severity:** medium

```python
claim: dict[str, Any] = {
    "rationale": answer_text or "",
    "citations": citations,
    "confidence": confidence,
    "entities": [],
}
```

The auto-gate on every `paperqa.answer` payload deliberately sends an empty
`entities` list. The entity check then short-circuits to a clean pass
(rigor.py:483-484). The KB-derived `KBEntityLookup` and the `BuiltinEntityLookup`
backends never see the answer text. Per the v0.5.0 spec
(`docs/specs/2026-05-19-v0.5.0-implementation-plan.md`) and the rigor module
docstring (rigor.py:24-30), entity grounding is one of three baseline checks
the gate is supposed to perform. Currently it is silently no-op'd on the
auto-gate path.

The hard part is that paper-qa does not return entities — they would need
to be extracted from `answer_text` via a NER pass before being fed to the
gate. Doing that pass inside `_run_rigor_gate` may be out of v0.5.0 scope.
The bug-class report flags this either way: the docstring claims a gate
runs three checks; the code runs two. Either the docstring needs to call
out the deliberate skip, or a SciSpacy entity extractor needs wiring.

**Test that should catch:** call `paperqa.answer` end-to-end (with the fake
adapter); assert the rigor payload's `extras["entities"]["entities_checked"]`
is > 0 when the answer text contains a well-known gene symbol like BRCA1.
Today it is always 0.

### M5 — `KnowledgeRetriever._fuse` divides nothing — it just sums weighted scores — so a paper that only ranks in one method gets `weight * score` while a paper ranking in two gets the sum; the score is the wrong "fused" interpretation

**File:** `src/linus/knowledge/retriever.py:249-267`
**Category:** Logic / contract drift
**Severity:** medium

```python
for sha in all_shas:
    total = 0.0
    for method, scores in per_method.items():
        method_score = scores.get(sha, 0.0)
        weight = weights.get(method, 0.0)
        total += weight * method_score
    fused[sha] = total
```

With default weights `keyword=0.3, semantic=0.7, graph=0.0` and (e.g.) `paper_a`
scoring `1.0` in keyword and `1.0` in semantic, the fused score is `1.0`.
A `paper_b` scoring only in keyword at `1.0` gets `0.3`. So far so good — that
matches "weighted sum." But the docstring of `_keyword` says scores are
"rank-based: 1.0 for the top hit, linearly decaying to 1/N for the N-th." If
`_semantic` returns cosine similarities in `[0, 1]` (as the spec implies)
then the two methods are scored on different scales: keyword's `1.0` means
"best rank" while semantic's `1.0` means "perfect cosine match." Adding them
weighted with no per-method normalization conflates two scales. A paper that
ranks middling on both methods gets a lower fused score than a paper that
ranks #1 in only one of them, even though "evidence from both methods"
should be weighted as a stronger signal. The keyword scoring also leaks the
result-set size N into the score: with `top_k=5` the #5 paper scores `0.2`;
with `top_k=10` the #5 paper scores `0.5`. The same paper ranks differently
depending on `top_k`.

The fix is a per-method normalization (z-score or rank-normalize against the
method's full distribution) before the weighted sum, or — simpler — switch to
RRF (Reciprocal Rank Fusion: `score(p) = Σ 1/(k + rank_in_method)`), which
the IR literature has solved cleanly. Until semantic and graph are wired this
doesn't bite, but the contract that downstream Archimedes-style consumers
lift verbatim (per the module docstring) carries this asymmetry forward.

**Test that should catch:** plug a fake `_semantic` returning `{"sha_x": 0.05}`
plus the existing keyword backend; verify that a paper appearing in both
ranks above a paper appearing only at keyword rank 1, instead of the current
behavior where the keyword-rank-1 paper wins due to scale mismatch.

### M6 — `entity_kb.py` indexes only `nodes(data=True)` — case-folding collision policy keeps the higher-`ref_count` entry, but the choice is order-dependent if ref_counts tie

**File:** `src/linus/knowledge/entity_kb.py:240-245`
**Category:** Edge case / nondeterminism
**Severity:** medium

```python
existing = index.get(key)
if existing is None or metadata["ref_count"] > existing["ref_count"]:
    index[key] = metadata
```

If two entity nodes case-fold to the same key with equal `ref_count`, the
first inserted wins. Node iteration order in NetworkX MultiDiGraph is
insertion order (CPython 3.7+ dict semantics), but the GraphML reader's
parse order is dependent on the XML element order in the file. The file is
written by the KB submodule; if the writer is ever changed to a parallel
walker or a different traversal, the same case-folded entity would resolve
to a different metadata dict. The user-facing impact is small (the `kind`
field could differ between two near-identical entities) but it's
non-deterministic if equal-`ref_count` collisions exist. Lowest fix is
adding a tiebreak (e.g., prefer alphabetic-first node id) so the choice is
deterministic across runs and KB writers.

## Low findings

### L1 — `paperqa.py` constants assume `mxbai-embed-large` is pulled into the local Ollama; no preflight or remediation pointer

**File:** `src/linus/knowledge/paperqa.py:103-106`
**Category:** Operational
**Severity:** low

`DEFAULT_EMBEDDING_MODEL = "ollama/mxbai-embed-large"` is hardcoded as the
default; if the user's `brew install ollama` setup hasn't pulled this model,
the first paper-qa call fails deep inside LiteLLM's HTTP path with a 404 from
Ollama. No preflight or remediation hint is emitted by Linus. A `subprocess
ollama list | grep mxbai-embed-large` preflight on first `_ensure_loaded`
with a clear `PaperQAConfigError("run: ollama pull mxbai-embed-large")` would
be a friendlier failure surface. Not a bug per se but a known footgun for
new users.

### L2 — `adapter.py:_PAPER_COLUMNS` is duplicated as `_FULL_COLUMNS` in `test_knowledge_adapter.py`; a column add/drop requires two coordinated edits

**File:** `src/linus/knowledge/adapter.py:43-66` + `src/linus/tests/test_knowledge_adapter.py:35-58`
**Category:** Maintenance
**Severity:** low

The test file deliberately duplicates the column tuple "so a schema drift in
either place produces a loud test failure" (its own comment). Fine intent,
but the duplication is not enforced — the assertion that the two tuples are
equal is missing. If the production tuple gains a column and the test tuple
doesn't (or vice versa), the wider suite still passes; only the specific
`from_row` happy-path test reveals the mismatch. A one-line assertion at
the top of the test module (`assert _FULL_COLUMNS == _PAPER_COLUMNS`) would
make this enforceable.

### L3 — `Paper.from_row` uses `bool(get("is_supplement") or 0)` which evaluates to False for stored `None`, but also for stored `0` — correct here, just brittle

**File:** `src/linus/knowledge/adapter.py:125-148`
**Category:** Style / future trap
**Severity:** low

```python
is_supplement=bool(get("is_supplement") or 0),
```

The `or 0` defends against `None` from a NULL upstream value, and the `bool(...)`
coerces `0`/`1` ints. Correct today. But if the upstream column ever stores a
string `"true"` / `"false"` (some SQLite-via-ORM stacks do this), `bool("false")`
is `True`. Not worth fixing speculatively; flag for awareness.

### L4 — `rigor.py:_jaccard` returns `1.0` for "both sets empty" by convention, which makes a fully-empty rationale claim look like a perfect match to anything

**File:** `src/linus/knowledge/rigor.py:325-332, 576-621`
**Category:** Edge case
**Severity:** low

```python
def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)
```

A claim with no rationale (`rationale=""`) yields `_rationale_token_set` =
empty frozenset. Compared against any prior also with empty rationale, the
similarity is 1.0 — perfect "agreement." Compared against a prior with
content, similarity is 0/N = 0. The asymmetry is intentional (the docstring
says "1.0 if both empty (by convention)") but the corner case is that a
worker producing empty output looks like a perfectly confident agreement
with another worker producing empty output, which is the wrong calibration
signal. Empty-rationale claims arguably should NOT participate in the
confidence-divergence calculation at all (or should be penalized rather
than treated as agreement). Low priority because empty rationales are
themselves caught upstream — but the rigor gate's input shape allows them.

## Patterns / themes

1. **Fail-open semantics are load-bearing but lightly tested.** The auto-gate
   path in `paperqa.py:_run_rigor_gate` wraps every gate evaluation in a
   broad `except Exception` returning `None`, with one test
   (`test_answer_rigor_failopens_to_none_when_gate_raises`) exercising it.
   The H3 finding (the chained-lookup raises path) shows that the catch
   currently swallows raises that the chain was supposed to fall through.
   The fail-open is correct as a last resort; the bug is that the failure
   modes which SHOULD fall through to graceful degradation instead silently
   set `rigor=None` and the user gets no signal.

2. **Lazy-load discipline is consistent but unsynchronized.** Both
   `LinusPaperQA._ensure_loaded` (paperqa.py:303) and
   `KBEntityLookup._ensure_loaded` (entity_kb.py:185) check-then-set with no
   lock. H1 documents the entity case; the paperqa case is less acute
   because the singleton itself is already created lazily in `get_singleton`,
   but the same `_loaded` flag race exists if two threads call any tool
   method on a fresh facade simultaneously.

3. **The `_AdapterPaperLookup` shim duplicates work the adapter already
   does.** H2 (page_count second lookup) is the worst case; M4 (entities
   dropped on the auto-gate path) shows the shim doesn't pull the rich
   data it could. The shim is the bridge between two contracts; reshaping
   the `PaperLookup` Protocol to return a record carrying its own page
   count would resolve both at the cost of an ADR.

4. **Test fixtures use realistic shapes for paper-qa but not for the
   adapter.** `test_paperqa.py`'s `_FakeKBAdapter` returns objects with
   only `page_count` — no other attribute — so the H2 double-lookup is
   not visible in tests. A more faithful fake (returning the full `Paper`
   dataclass shape) would expose the bug at test time.

5. **Schema-evolution traps in adapter ↔ test column tuples.** L2 is the
   visible instance; the same shape appears in test fixtures across the
   suite. The pattern to encode is "production tuple is the source of
   truth, test imports it" rather than "test duplicates and we hope for
   matching edits."

## What I checked but found clean

- **`KnowledgeBaseAdapter` read-only invariant.** The `mode=ro` URI is
  honored by SQLite at the engine level; tests
  (`test_connect_uses_readonly_uri`, `test_adapter_cannot_mutate_via_search_path`)
  exercise both `INSERT` and `UPDATE` rejection. The H4 leak doesn't
  compromise the read-only property.

- **`citation_to_provenance` field extraction against real paper-qa
  shapes.** Cross-checked against `repos/paper-qa/src/paperqa/types.py`
  (`Doc.dockey`, `Doc.docname`, `Text.name`, `Text.text`, `Text.doc`,
  `Context.text`, `Context.context`, `Context.score`); the duck-typed
  getattr walks match the real class layout. The `score=-1` "unset"
  sentinel is correctly normalized to 0.0.

- **`PQASession.confidence` field.** Confirmed it does NOT exist on
  paper-qa's `PQASession`; `getattr(session, "confidence", None)` is the
  right guard. The rigor gate's `confidence` parameter is therefore always
  `None` on the auto-gate path today — which is correct behavior but
  worth a docstring note (low — not flagged separately).

- **`Docs.clear_docs` semantics.** Confirmed against
  `repos/paper-qa/src/paperqa/docs.py:78`; `LinusPaperQA.reset` correctly
  delegates and reports the no-op path when the facade is unloaded.

- **`_run_async` event-loop bridge for the FastAPI test client case.**
  The implementation correctly detects a running loop via
  `asyncio.get_running_loop()` and routes to a worker-thread loop;
  `test_run_async_works_inside_running_loop` exercises the branch.

- **`check_grounding` and `check_all` orchestrator merging.** The error
  aggregation (`passed = not any(f.severity == "error" for f in
  merged_failures)`) is correct; the calibration-from-last-non-None
  rule in `check_all` is correct. Both have direct unit coverage.

- **`result_to_dict` round-trip across every `RigorFailure` kind.**
  Every documented `FailureKind` is exercised somewhere in
  `test_rigor.py`; the serializer doesn't drop any field of the dataclass.

- **`KnowledgeRetriever.retrieve` explicit-method `NotImplementedError`.**
  The contract that explicit `methods=["semantic"]` raises with the
  install pointer is honored; auto-selection silently skips. Both
  branches have coverage.

- **Path traversal in `KBEntityLookup`.** The `graphml_path` parameter
  is taken as `Path` and passed directly to `nx.read_graphml`. No
  user-controllable path traversal vector — the path is set either via
  the env var `LINUS_KB_OUTPUTS_DIR` (operator-controlled) or the
  default constant. Both are trusted inputs in this threat model.

- **`KnowledgeBaseUnavailableError` firing semantics.** It correctly
  fires in `_connect` for missing files and for `OperationalError`
  during open; tests cover both.
