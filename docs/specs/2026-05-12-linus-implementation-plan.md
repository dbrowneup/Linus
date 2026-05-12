# Linus Implementation Plan — Get to Code

> **Date:** 2026-05-12
> **Purpose:** Move Linus from planning mode into build mode. After ~2.5 weeks of synthesis,
> ADRs, and spec writing, the next-highest-leverage move is shipping code against the specs
> we have. This plan identifies the unblocked work, sequences it for usage-efficient
> delegation, and gives concrete prompts for executing each step in a fresh Claude Code
> session.
> **Scope:** remaining Phase 1 items + tractable Phase 2 items. Nothing beyond Phase 2.

## Where we actually are (honest snapshot, 2026-05-12)

**Done well:**

- 117 repo notes, 118 paper notes, 27 syntheses, 54 ADRs, multiple decision sweeps.
- Phase 1a (repo synthesis notes) complete.
- Phase 1b (pmetal evaluation) in progress — built from source, smoke tests pass, LoRA +
  serve + comparative benchmark still to run.
- Rich, well-organized planning corpus.

**Not done:**

- **`src/linus/` contains essentially no code.** Just `__about__.py` and `__init__.py`.
  The whole codebase is yet to be written.
- Phase 1c memory-pillar spikes — not started.
- Phase 1d Dan task suite — not started (`benchmarks/dan_tasks/` exists but unpopulated).
- Phase 1e first Maestro/Worker loop — not recorded.
- Phase 1f minGRU MLX port spike — not started.
- All of Phase 2.

**The reframe:** the gap between "well-specified" and "shipping" is the entire current
risk. Planning more doesn't reduce it. Coding does.

## Sequencing strategy

Three principles:

1. **Unblocked first.** Some Phase 1 and Phase 2 items depend on spikes (1b verdict, 1c CoT-gap
   fingerprint) that themselves take a session each to run. Other items have NO spike
   dependencies and can start immediately. Do the unblocked items first; the spike-blocked
   items become unblocked as the spikes finish, in parallel.

2. **Checkpoint per session.** Each work item below is sized for a single Claude Code session
   of roughly 30–60 minutes of active engagement. Each ends at a natural commit point. This
   bounds usage burn — you spend at most one session's worth of tokens before deciding whether
   to continue.

3. **Smoke-test gate everywhere.** Per CLAUDE.md convention, no pipeline runs at full scale
   without a 10–50 item smoke test passing. Each work item includes a smoke-test boundary as
   part of its "done" definition.

## The unblocked work items

These can start in any order; the dependencies between them are noted where they exist.

### Item 1 — Phase 2a bootstrap: minimal FastAPI orchestration backend

**Why first.** The OpenAI-compatible endpoint (DEC-0005) is the most architecturally
load-bearing single artifact in Phase 2. Once it exists and speaks `/v1/chat/completions`
against Ollama, every other Phase 2 item plugs into it.

**Scope.**

- Create `src/linus/server.py` with FastAPI app exposing `POST /v1/chat/completions`.
- Implement only the request/response shape; no streaming yet (add in a separate session).
- Route the request to Ollama at `localhost:11434` using the existing `ollama` Python client
  (already in the linus conda env).
- Hardcode the model for v0: `qwen3:8b` or whatever is locally available.
- No tool registry, no router, no sandbox in this session — those are separate items.
- Add `pyproject.toml` entry points so `linus serve` (or similar) launches the app.

**Success criteria.**

- `uvicorn linus.server:app --port 8000` starts cleanly.
- `curl -X POST localhost:8000/v1/chat/completions -d '{...}'` returns a valid completion.
- One smoke test in `tests/test_server.py` that asserts the basic happy path.

**Estimated session length:** 45–60 min.

**Delegable prompt** (paste into a fresh Claude Code session in the Linus repo root):

```
Read CLAUDE.md, then read ROADMAP.md sections "Phase 2 — Linus MVP" through "2d".
Read VISION.md briefly to understand the orchestration-layer-as-product framing.
Read DECISIONS.md entry DEC-0005 for the OpenAI-compatible-protocol commitment.

Task: bootstrap the minimal FastAPI orchestration backend at `src/linus/server.py`,
exposing POST /v1/chat/completions that routes to local Ollama at port 11434. Do NOT
implement: streaming, tool registry, sandbox, router intelligence, session store. Those
are separate items.

Scope:
1. Create `src/linus/server.py` with the FastAPI app + the single endpoint.
2. Use the `ollama` Python package (already installed in the linus conda env).
3. Hardcode model to `qwen3:8b` for v0; load from env in a follow-up.
4. Write one pytest smoke test in `tests/test_server.py` covering the happy path.
5. Update `pyproject.toml` to ensure the package and test deps are declared.

Success criteria:
- `conda activate linus && uvicorn linus.server:app --port 8000` starts cleanly.
- `curl -X POST localhost:8000/v1/chat/completions -H 'Content-Type: application/json' -d '{"model":"qwen3:8b","messages":[{"role":"user","content":"Hello"}]}'` returns a valid ChatCompletion-shaped JSON response.
- `pytest tests/test_server.py` passes.

When you reach the success criteria, stop. Commit with message
`[orch] Bootstrap Phase 2a OpenAI-compatible orchestration backend (DEC-0005)`.
Don't open a PR yet — Dan will review the commit locally first.
```

**Checkpoint after this:** Dan reviews the commit. If the basic shape is right, proceed to
Item 2. If not, iterate with Claude Code on this same item. Either way, the next session is
a fresh one.

---

### Item 2 — Phase 1d: minimal Dan task suite (3 tasks)

**Why early.** Every future evaluation pivots on the Dan task suite. Without it, we can't
measure whether the Worker is doing useful work. Three real tasks is enough to start;
expand to 10 later.

**Scope.**

- Create `benchmarks/dan_tasks/` directory structure: `tasks/`, `runners/`, `rubrics/`.
- Author three tasks pulled from real work. Suggested starters from ROADMAP:
  1. "Summarize this paper and extract 3 key findings" — input a real PDF from
     `context/papers/`.
  2. "Write a Python script that reads a FASTA file and computes GC content."
  3. "Given 50 paper titles, cluster them into 5 topics and name each."
- Each task has: `input.{txt,py,fasta}`, `expected_output_schema.json`, `rubric.md`.
- A minimal `runner.py` that calls Ollama against the task input and saves output to
  `benchmarks/results/dan_tasks_baseline_2026-05-12.json`.

**Success criteria.**

- Three tasks defined with schemas + rubrics.
- Runner executes against `qwen3:8b` and records output.
- Output JSON has the right shape (one entry per task with input, output, model, timestamp).

**Estimated session length:** 60–90 min (writing rubrics takes longer than it sounds).

**Delegable prompt:**

```
Read CLAUDE.md and ROADMAP.md section "1d — Private 'Dan task' suite".

Task: build the minimum viable Dan task suite at `benchmarks/dan_tasks/` with three
tasks. The suite becomes the primary evaluation measure for every future Phase 2+
delivery.

Tasks to author (start with these three; we'll expand later):
1. Paper summarization: given a PDF from `context/papers/` (use any one; pick one with
   a clear abstract), extract 3 key findings as a numbered list.
2. FASTA GC content: write a Python script that reads a FASTA file and computes GC
   content per sequence and overall.
3. Title clustering: cluster 50 paper titles into 5 topics and name each topic.

Structure:
- `benchmarks/dan_tasks/tasks/<slug>/input.{ext}` — the input artifact
- `benchmarks/dan_tasks/tasks/<slug>/expected_output_schema.json` — JSON schema for the
  expected output shape
- `benchmarks/dan_tasks/tasks/<slug>/rubric.md` — what counts as success, what's
  partial, what's failure
- `benchmarks/dan_tasks/runners/run_all.py` — Python script that calls Ollama, runs
  each task, saves results
- `benchmarks/results/dan_tasks_baseline_2026-05-12.json` — output file with one entry
  per task

For the paper input (task 1), pick a real PDF from `context/papers/` and use pypdf to
extract text. Per Known Library Quirks in CLAUDE.md, set
`sys.setrecursionlimit(sys.maxsize)` workaround.

Don't implement scoring/grading in this session — just collect outputs.

Success criteria:
- Three tasks fully specified.
- Running `python benchmarks/dan_tasks/runners/run_all.py` produces the results JSON
  with three entries.
- One task at least is "obviously working" when Dan reads the output.

Commit with `[bench] Add minimal Dan task suite (Phase 1d v0)`. Stop.
```

**Checkpoint after this:** Dan reads the three outputs and assesses whether Qwen3:8b is
producing useful work on his task surface. This is the first concrete "is the Worker model
actually good enough?" data point.

---

### Item 3 — Phase 1e: first Maestro/Worker loop, recorded

**Why early.** This is the first Maestro/Worker discipline run on the books. The protocol
document already exists (`docs/protocols/maestro-worker-protocol.md`); this is the practice
session.

**Scope.**

- Spec written by Maestro (you, in a Claude Code session) at `experiments/first-loop.md`.
- Worker (Qwen3 via Ollama, called from a minimal driver script) executes the spec.
- Smoke test gate before any full execution.
- Atomic commit recording the full loop: spec, output, review notes.

**Suggested task for the loop** (small and verifiable):

"Generate a Python class that wraps `linus.fs.read` and `linus.fs.write` with sandbox
path-prefix validation per SAFETY.md. Include type hints, docstrings, and 3 unit tests.
Output a single file at `src/linus/sandbox/fs.py`."

This produces real code that lives in the codebase (the sandbox helpers from Phase 2a),
exercises the Worker's code-gen ability, and tests whether the protocol's hand-off rules
work.

**Estimated session length:** 45 min.

**Delegable prompt:** Use the Maestro/Worker protocol at
`docs/protocols/maestro-worker-protocol.md` directly — this session IS the Maestro pass.
Write the spec, invoke Ollama from Bash with the spec as input, review the output, commit
or iterate.

---

### Item 4 — Phase 2h.1-2: SQLite episodic schema + audit log writer

**Why.** Two of the seven memory pillar v0 deliverables (DEC-0029, DEC-0030) have no spike
dependency — they're pure data-layer work that can start immediately and unblocks the
later dispatch/cot_budget items.

**Scope.**

- `~/.linus/` directory creation on first run.
- SQLite schema at `~/.linus/episodic.db` per DEC-0029 record shape (see
  `docs/specs/memory-architecture.md`).
- Migration script (single migration for v0 → v1).
- Hash-computation helpers (content-hash for episodic records).
- Audit log writer at `~/.linus/audit.jsonl` (append-only, JSONL, one line per dispatched
  Worker call per DEC-0030/0031/0032 contract).
- Both as separable Python modules under `src/linus/memory/`.
- Unit tests for: schema migration up, hash determinism, audit log write/read round-trip.

**Estimated session length:** 60–90 min.

**Delegable prompt:**

```
Read CLAUDE.md, then docs/specs/memory-architecture.md fully, then docs/adr/0029-
episodic-memory-substrate.md, 0030-scratchpad-first-class-artifact.md, 0031-router-
primitives-cot-budget-memory-mode.md, and 0032-in-context-window-cap-policy.md.

Task: implement Phase 2h deliverables 1 + 2 — the SQLite episodic store and the
audit log writer. These two are unblocked from the spike work (DEC-0033, DEC-0034)
because they're pure data-layer scaffolding.

Scope:
1. `src/linus/memory/episodic.py` — SQLite-backed episodic store with the record
   shape from DEC-0029. Initialize `~/.linus/episodic.db` on first call. Provide:
   - `write_record(record: EpisodicRecord) -> str` (returns content hash)
   - `read_records(query: dict) -> list[EpisodicRecord]`
   - `migrate()` — idempotent schema init.
2. `src/linus/memory/audit_log.py` — append-only JSONL writer at `~/.linus/audit.jsonl`
   with the DEC-0031 contract: every Worker dispatch records memory_mode, cot_budget,
   token counts, content hashes, timestamps.
3. `src/linus/memory/hashing.py` — Keccak-256 (preferred) or SHA-256 content-hashing
   helpers, with canonical JSON serialization rules documented in docstrings.
4. Unit tests in `tests/memory/`:
   - test_episodic_schema_migration_idempotent
   - test_episodic_write_read_roundtrip
   - test_audit_log_append_jsonl
   - test_hashing_deterministic

Do NOT implement the dispatch-layer prefix loader (deliverable 5) or the worker
registry tags (deliverable 7) — those depend on DEC-0033 fingerprint output.

Success criteria:
- `pytest tests/memory/` passes.
- A demo script `python -m linus.memory.demo` writes one episodic record, reads it
  back, and appends an audit log line.

Commit with `[memory] Phase 2h.1-2: SQLite episodic store + audit log scaffolding
(DEC-0029, DEC-0030, DEC-0031)`.
```

**Checkpoint after this:** Dan reviews the schema migration + audit log shape. This is the
foundation for everything memory-related; getting it right matters.

---

### Item 5 — Phase 2c bootstrap: KnowledgeBase v1 read-only adapter

**Why.** Linus's commercial-surface thesis (per `entrepreneurship-synthesis.md`) depends on
KB integration. The read-only adapter is non-controversial scaffolding that opens the
"can Linus answer questions about Dan's corpus" milestone.

**Scope.**

- `src/linus/knowledge/__init__.py` — package init.
- `src/linus/knowledge/adapter.py` — loads `modules/KnowledgeBase/metadata.db` read-only.
- Two functions: `search_papers(query: str, limit: int = 10)` and
  `get_paper(sha256: str)`.
- For now, search is a simple keyword match against title/abstract; SPECTER2 embedding
  search is deferred to a separate item.
- Unit tests against the actual KnowledgeBase submodule.

**Estimated session length:** 60 min.

**Delegable prompt:**

```
Read CLAUDE.md, then ROADMAP.md section "2c — KnowledgeBase integration (v1)" and
"2f — KB integration v1 with dual substrate". Also read
docs/specs/kb/paper-qa-substrate-integration.md.

Task: implement the read-only KnowledgeBase adapter at `src/linus/knowledge/`. This
session covers ONLY the SQLite read path. SPECTER2 embedding search and dual-substrate
(SPARQL + property graph) are separate items.

Scope:
1. `src/linus/knowledge/adapter.py` with:
   - `KnowledgeBaseAdapter` class loading `modules/KnowledgeBase/metadata.db` read-only
   - `search_papers(query: str, limit: int = 10)` — keyword search on title/abstract
   - `get_paper(sha256: str)` — fetch single paper metadata
2. Unit tests in `tests/knowledge/` against the actual KB submodule.

Do NOT mutate KnowledgeBase state in any way — open SQLite as read-only.

If `modules/KnowledgeBase/metadata.db` does not exist yet (submodule not initialized),
fail gracefully with a clear error message pointing to `git submodule update --init`.

Success criteria:
- `pytest tests/knowledge/` passes (or skips with clear message if submodule absent).
- A demo script can search for a known paper and retrieve its metadata.

Commit with `[kb] Phase 2c: read-only KnowledgeBase adapter v0`.
```

**Checkpoint after this:** Dan tests with a real query against his corpus.

---

### Item 6 — Tool registry scaffolding (Phase 2a, second slice)

**Why.** Once the server exists (Item 1) and the KB adapter exists (Item 5), the tool
registry plugs them together. This is the first cross-module integration.

**Scope.**

- `src/linus/tools/registry.py` — simple in-memory dict-of-tools.
- Tool decorator (`@tool`) that registers a function.
- Two tools registered: `linus.knowledge.search_papers`, `linus.knowledge.get_paper`.
- Hook into `/v1/chat/completions` so the server can route tool calls.
- This is OpenAI's tool-calling JSON format, not MCP yet — MCP is a Phase 3 conversation
  per existing roadmap.

**Estimated session length:** 60 min.

**Delegable prompt:** [structurally similar to the above; build against the Items 1, 5
foundations]

---

### Item 7 — Phase 1b completion: pmetal verdict ADR

**Why.** This is the gate for Phase 2's serving-layer decision. The infrastructure is
already there (pmetal builds; smoke tests pass). The remaining work is the LoRA trial,
serve trial, and comparative benchmark — then writing the verdict ADR.

**Note this is partially BLOCKED** by pmetal-specific spikes that have to run sequentially.
It's still doable now, but estimate the entire item at ~3-4 hours of active work spread
across 2-3 sessions.

**Don't delegate to a fresh Claude Code session blindly** — this needs hands-on benchmark
running. Dan stays in the loop. Use Claude Code as the analysis layer, not the
button-pushing layer.

---

## Items deliberately deferred

These can wait:

- **1c memory-pillar spikes (CoT-gap, Worker-size×CoT-length, TTT viability).** Real
  research, real time. Do after the Phase 2a + 2h scaffolding lands.
- **1f minGRU MLX port spike.** Same reason.
- **2h.5/6/7 dispatch wiring with cot_budget + memory_mode.** Blocked on the CoT-gap
  fingerprint output from 1c.
- **2b chat UI (Streamlit).** Needed for Phase 2 demo but lower-leverage than the backend.
  Land last.
- **2e output synthesis + citation drill-down.** Phase 2 deliverable but not on the
  critical path.
- **2f KB dual substrate.** Phase 2 deliverable; do after the read-only adapter is
  working.
- **2g knowledge-mining-surface document.** Spec doc; Phase 2 deliverable; lower urgency.
- **2i ARC-AGI memory diagnostic.** Phase 2 deliverable; do after memory pillar v0.
- **2j Worker protocol non-conformance constraints.** Doc work; lower priority.

Don't let "lower priority" mean "never." Schedule a session for each in a rolling Phase 2
plan.

## Usage management: how to control burn

Each item above is sized for one Claude Code session. After each session:

1. **Stop.** Don't continue into the next item without a break.
2. **Review the commit.** Did Claude do what was asked? Is the code clean? Test pass?
3. **Decide:** continue to the next item, or iterate on this one.
4. **Re-plan if the picture changed.** If a session surfaced a blocker, edit this
   document.

A rolling estimate: items 1–6 above are ~6-8 Claude Code sessions of 45-90 min each. If
you spend 1 session/day evenings + 2 sessions over a weekend, you ship the unblocked
critical-path in roughly 5–6 days of calendar time. Add buffer; reality is messier than
this estimate.

For each session, the discipline:

- **Open with the prompt.** Drop the prompt above (or your variant) at the start.
- **Don't add new asks mid-session.** If a new requirement surfaces, write it down and
  schedule a separate session.
- **End with a commit.** Even if it's `[wip]`-tagged, the session ends at a clean
  checkpoint.

## What success looks like at the end of this plan

After items 1–7 land:

- `src/linus/` has a working FastAPI orchestration backend.
- The OpenAI-compatible endpoint serves Ollama-backed completions.
- The KnowledgeBase adapter loads and serves searches.
- Two real tools are registered and callable.
- The SQLite episodic store and audit log are functional.
- Three Dan tasks have baseline outputs recorded.
- One Maestro/Worker loop is documented and committed.
- The pmetal verdict ADR is written.

**This is Linus alpha.** It's not pretty; the chat UI is missing; the memory architecture
is half-built. But it is **runnable, demo-able to yourself, and unblocks every Phase 2
remainder** by removing the "we have no code" risk.

After this, the next planning conversation is "do we open up to the team yet, and what
does Phase 2 finish look like?" — which is exactly where you wanted to be by May 16.

---

_Maintainer note: this plan reflects 2026-05-12 state. Revise after each completed item;
don't let it drift._
