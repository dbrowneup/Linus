# Linus — Claude Code Context

## Project Purpose

Build a private, local, modular AI assistant named **Linus** that runs on Apple Silicon, provides Claude-equivalent
capabilities for Dan's scientific and software work, and stays fully under Dan's control. Named after Linus Pauling
(scientist, humanitarian, Oregonian) and Linus Torvalds (engineer, open-source advocate, Oregonian). Logo: a carbon
atom. Linus is a force that harnesses human knowledge for good in the world.

## Owner Background

- Daniel R. Browne (GitHub: dbrowneup, email: dbrowne.up@gmail.com).
- **Current role**: Senior Scientist in industrial biotech — maintains enterprise LLM infrastructure +
  leads metagenomics bioinformatics software. Prior: long-read sequencing industry (Product Owner
  Bioinformatics + Field Applications Scientist).
- **Education**: PhD Biochemistry, Texas A&M (2018, + Entrepreneurship cert). Thesis on _Botryococcus braunii_
  metabolism. BS Environmental Science + Chemistry minor, U. Portland (2011).
- **Domain specialty**: genomics + computational biology — long-read sequencing (PacBio HiFi), genome/transcriptome
  assembly, metagenomics, gene cloning/expression, protein purification. _B. braunii_ genome assembly + downstream
  lipid/terpene metabolism is the deepest publication-record thread (11 pubs, 15 presentations).
- **Stack he operates in**: Python (13yrs scientific computing), Linux, Bash, Git, GitHub Actions, SQL, WDL,
  Docker, AWS, Azure; Agile/Jira; pipeline validation + automated testing. Self-taught CS, trial-and-error debug
  fluency.
- **Entrepreneurship**: founded Botryonyx LLC (2018–2019, algae wastewater + carbon capture, $42K seed, Rice BP
  + SEC Pitch semi-finalist, 2nd at Aggie Pitch $12K); Sci Advisor CaribAlgae Curaçao (2018–2022). The
  speed/evidence instinct in this repo's Algorithm/blitzscaling framings is lived experience.
- **Currently learning**: Rust, nodejs/npm, agentic systems, LLM inference/fine-tuning. Calibrate accordingly —
  deep biology/Python/Linux, newer to systems-language idioms + modern JS tooling.
- **Hardware**: MacBook Pro 2021, Apple M1 Max, 32 GB unified memory (10 CPU / 24 GPU / 16 ANE cores). 400 GB
  internal SSD; 1 TB external flash, ~600 GB free.

## North Star

A personal AI orchestration backend that:

- Runs on Dan's MacBook Pro (and future Mac hardware), no paid APIs required for operation; local-primary with an
  opt-in network framework (DEC-0061) — some tools may use the internet when available, none depend on it,
  hermetic tests stay network-free, and every external call is captured in the audit log
- Exposes an OpenAI-compatible endpoint so any harness (VS Code, openclaw, LM Studio, a future native app) can use it
- Provides domain-specific tools backed by Dan's knowledge base (papers, notes, corpora)
- Supports multi-agent parallel task execution
- Enforces sandbox policy regardless of front-end
- Evolves toward hosting fine-tuned, Dan-specific models

Linus is NOT intended to replace hosted Claude. Hosted Claude plus Dan remains the Maestro for complex reasoning and
architecture. Linus is the Worker orchestra that executes under Claude's and Dan's direction and serves Dan directly
when private/offline operation is needed. Eventually, as Linus gets better, it can become part of the Maestro team too,
directing instantiated Workers.

## Guiding Principles

### The Algorithm (Elon Musk via Jon McNeill)

Applied to every design decision, in order:

1. **Question every requirement.** Who needs this? Why? Can it be deleted?
2. **Delete every possible step.** Err aggressive. If it comes back, re-add it.
3. **Simplify and optimize.** Only after steps have been deleted.
4. **Accelerate cycle time.** Short loops produce more information than long plans.
5. **Automate.** Last, not first. Automating a bad step industrializes the badness.

**The Algorithm check**: Before adding any component to Linus, ask "can we delete this requirement instead?" Before
reaching for a new library, ask "does something we already have serve this purpose?"

### Blitzscaling mindset (Hoffman & Yeh)

Speed is information. Short cycle times on real tasks produce better decisions than long planning on hypothetical ones.
Ship rough, learn, iterate.

### Maestro/Worker discipline

- **Maestro** = Dan + hosted Claude (this chat, Claude Code, Claude.ai). Architecture, planning, spec writing, hard
  debugging, taste-level decisions.
- **Worker** = local models. Current practical Worker on 32 GB M1 Max is `qwen3:8b` (FP16) — empirically validated
  2026-05-18 against `qwen3.6:27b` which swap-thrashed at the 600s timeout on all Dan tasks. **`qwen3.6:27b` (and other
  27B-class models) are dropped from all further testing as of 2026-06-02** — they exhaust unified memory and lock the
  machine; larger, more capable models await a memory-streaming serving path (e.g. pmetal) that doesn't blow the 32 GB
  ceiling. Bulk implementation, test generation, refactors, pipeline execution.
- Maestro attention is the scarce resource. Push any well-specified task to Workers.

### Evidence beats intuition

Plateau points get resolved by measurement, not argument. Flash-moe pattern: set a metric, set a goal, devise tests, and
iterate until the goal is hit. Keep-or-revert by git. 42% of experiments being discarded is a sign the search is
working.

## Hardware Constraints

- **No CUDA.** Everything runs on Apple Silicon (Metal, ANE, unified memory).
- **Metal/MPS for GPU compute.** MLX is the primary ML framework.
- **ANE is accessible** via pmetal and Core ML; underutilized by most frameworks.
- **32 GB unified memory** is a hard constraint for fine-tuning. LoRA/QLoRA on 7–14B models is tractable. Full
  fine-tuning of 8B+ is at the edge. Streaming-based training (optimizer state on SSD) is open research; deferred.
- **Docker inference is forbidden** — the macOS VM does not pass through Metal or ANE. ML inference and training must
  run natively. Docker is fine for any service that does not need GPU/ANE: databases (PostgreSQL, Neo4j), vector stores
  (Qdrant), knowledge servers (Kiwix, wiki), web services, etc.

## Environment

- **Package/env manager**: `mambaforge` (conda-forge) + `conda`. Base env has Python 3.12.
- **Linus env**: `conda activate linus` (set up via `environment.yml` at repo root)
- **Homebrew-installed ML tools**: `mlx`, `mlx-c`, `ollama`. Do NOT reinstall via conda — the brew versions are
  optimized for Apple Silicon.
- **Ollama** is the first worker-model server; runs on port 11434 via `brew services`.
- **Rust** is installed inside the linus conda env via `conda install rust` (needed for pmetal).
- **uv** is installed inside the linus conda env via conda. uv is the **disposable-env tool of choice** for experimental
  packages: untrusted or experimental Python packages always run in a fresh `uv venv`, never installed into the linus
  conda env. The linus conda env is the production substrate (hash-pinned); uv envs are scratch space discarded after
  the experiment (DEC-0024).
- **node/npm** installable inside conda env if openclaw or other JS-based components are used.
- **poppler** is available via a Homebrew install to read PDF files in the context folder.

## Repo Layout

```
Linus/
├── CLAUDE.md · VISION.md · ARCHITECTURE.md · ROADMAP.md · SAFETY.md · DECISIONS.md · GLOSSARY.md · README.md
├── BRANCHING.md · environment.yml · pyproject.toml · .gitignore · .gitmodules
├── src/linus/                    # Linus source — the product (Python package)
├── modules/KnowledgeBase/        # Tracked submodule — Dan's paper corpus + RAG + KG
├── repos/                        # 138 reference clones (gitignored, read-only study material)
├── context/                      # Dan's personal context (gitignored: papers/, books/, threads/, notes/, pics/)
├── benchmarks/                   # dan_tasks/ + results/ (dated JSON)
├── experiments/                  # Throwaway scripts, ablations, quick tests
└── docs/
    ├── README.md                 # Tour of the docs tree
    ├── curation-log.md           # DEC-0025 archive/removal record
    ├── security-log.md           # Routine pip-audit + incident log per SAFETY.md
    ├── repo-notes/               # Per-repo write-ups + INDEX.md (doc-type convention below)
    ├── paper-notes/              # Per-paper write-ups + INDEX.md
    ├── adr/                      # Per-file ADRs NNNN-<slug>.md matching DEC-NNNN; README.md = index
    ├── audits/                   # Dated audit batches (citation-traceability, repo-pull, etc.)
    ├── cybersecurity-notes/      # Government/standards primers (genomics/biotech focus)
    ├── landscapes/               # Cross-corpus rollups (total-, synthesis- active; paper-/repo- deprecated)
    ├── protocols/                # maestro-, maestro-worker-, curation-protocol.md
    ├── questions/                # top- → open- → answered-questions.md (lifecycle in docs/specs/question-lifecycle.md)
    ├── session-summaries/        # Date-prefixed Maestro session recaps
    ├── specs/                    # Living implementation specs (memory-architecture.md, phase1c-spike.md, etc.)
    │   └── kb/                   # KB-specific specs
    └── syntheses/                # 15 thematic + 12 cluster (g1–g12) syntheses
        └── repo-clusters/        # g1-apple-silicon … g12-llm-hardware-design
```

Per-file ADR index lives at `docs/adr/README.md`; full DEC list at `DECISIONS.md`. Per-document conventions for
repo-notes / paper-notes / audits / session-summaries live in §Doc-type conventions below.

## Phased Plan

See [ROADMAP.md](ROADMAP.md) for full detail; v2 implementation plan at
`docs/specs/2026-05-17-linus-implementation-plan-v2.md`.

- **Phase 0 — Foundation** _(closed)_: scaffolding, docs, env
- **Phase 1 — Recon & Baselines** _(mostly done)_: synthesis notes ✅, Dan task suite v0 ✅, first
  Maestro/Worker loop ✅; pmetal v0.5.0 verdict (1b) and memory-pillar spike (1c) + minGRU MLX port (1f) still
  open as Dan-driven items
- **Phase 2 — Linus MVP** _(in flight)_: FastAPI orchestration backend ✅, KB read-only adapter ✅, tool registry
  + KB tools ✅, memory v0 + sandbox ✅; remaining: streaming SSE, Anthropic `/v1/messages` (DEC-0056), session
  store, Streamlit chat UI, semantic search, citation synthesis
- **Phase 3 — Knowledge & Parallel Agents**: deeper KB integration, agent fan-out (workspace.py per R3-07)
- **Phase 4 — Data Sovereignty**: Kiwix, ProtoMaps/OSM, versioned datasets
- **Phase 5 — Interface Refinement**: openclaw as front-end, VS Code polish, claw-code-local (Phase 5c)
- **Phase 6 — Fine-Tuning**: LoRA on domain corpus, flash-streaming inference, DSPy track
- **Phase 7 — Skills & Autonomy Graduation**: domain tools (biology Phase 7 roadmap), widening sandbox
- **Phase 8 — Beyond MacBook**: mobile, Mac Studio, native app, Vision Pro; minGRU+BitNet research direction

## Architecture Summary (see ARCHITECTURE.md for detail)

```
  FRONT-ENDS (interchangeable)
    VS Code (Claude Code, Ollama chat) · LM Studio · openclaw · native (future)
            │
            │  OpenAI-compatible HTTP
            ▼
  LINUS ORCHESTRATION LAYER  ← the product
    router · MCP tool registry · agent spawner · sandbox · session store · audit log
            │
    ┌───────┼───────┐
    ▼       ▼       ▼
  INFERENCE  KNOWLEDGE  TRAINING
  Ollama     KnowledgeBase  pmetal / mlx-lm
  pmetal serve (submodule)
  mlx-lm
  mlx-flash (larger-than-RAM)
```

Harness ≠ Orchestration. Harnesses (Cline, claw-code, Claude Code) are coding workflows tied to a UX surface. The
orchestration layer is the product backend: Linus-specific tools, persistent state, cross-harness policy. Front-ends
come and go; the orchestration layer accrues value. See GLOSSARY.md.

## Engineering Conventions

### Smoke-test gates

No pipeline change runs on a full dataset without a 10–50-item sample passing first. Late-stage failures on long runs
are the most expensive bug class. Smoke tests are cheap.

### Known Library Quirks

A section maintained at the bottom of this file. When a tricky constant, config value, or library gotcha is resolved, it
goes here immediately — same session, not "later." Claude Code: if you resolve one, append it.

### Checkpoint discipline

Multi-file edits produce a checkpoint summary every 3–4 file edits: files changed, what each change does, remaining
TODOs. Makes long sessions resumable if interrupted.

### Hooks

`.claude/settings.json` runs a `PostToolUse` hook on `Edit|Write` that extension-guards each step. Python files:
`ruff format --line-length 120` → `ruff check --select I --fix` (import sort) → `ruff check` (lint). Markdown files:
`prettier --write` using `.prettierrc.json`'s `*.md` override (`printWidth: 120`, `proseWrap: always`) so prose is
actively re-wrapped to 120 columns. `.prettierignore` keeps `repos/`, `modules/`, `context/`, and lockfiles out of
prettier's reach. The actual hook JSON lives in `.claude/settings.json`.

`mdlint` is **deliberately not in the hook chain** — 0.3.15's `check` subcommand silently auto-fixes some rules (notably
MD004) even without `--fix`, corrupting prose with characters that look like list markers (a `+` in "ANE + MLX + serve"
gets rewritten to `-`). Run `mdlint check <file>` manually + inspect the diff if you want lint feedback.

### Commit discipline

Atomic commits per resolved issue. Descriptive messages in imperative mood ("Add Linus tool registry" not "Added tool
registry"). Scope tags welcome (`[orch]`, `[kb]`, `[infer]`, `[docs]`).

### Parallel by default

Multi-file audit, multi-repo synthesis, multi-paper analysis, benchmark sweeps — all fan out to parallel Task agents or
multiple Worker processes. Sequential is the exception, not the default.

### MCP as tool substrate

In-house Linus MCP servers build on **fastmcp** (DEC-0045) — decorator API + middleware pipeline, not parallel to it.
Open policy details: which tools, what permissions, transport (R2-06 stdio vs streamable-http). See
`docs/syntheses/repo-clusters/g6-mcp-tools.md` for the cluster-level verdict.

### Workgraph JSONL session-store shape (Phase 2a recommendation)

Workgraph's `.workgraph/graph.jsonl` append-only DAG + `handler_for_model.rs` dispatch is the most directly liftable
orchestration runtime in the cloned-repo collection (G7 synthesis). Recommended as Phase 2a session-store + audit-log
format before any other format is committed to. Port the JSONL shape + dispatch pattern to Python; do not vendor the
Rust crate. Caveat: workgraph's tree-kill is Linux `/proc`-only; macOS port needs `psutil`.

### Maestro budget discipline

When interacting with hosted Claude (via Claude Code or this chat): arrive with context gathered, questions sharpened,
and the task well-specified. Don't use Maestro tokens to read files Claude can't cache; pull excerpts and paste. Don't
use Maestro tokens for well-specified implementation; hand the spec to a Worker.

### Trust the OS page cache

The flash-moe empirical finding — that a 9.8 GB Metal LRU cache wrapping mmap'd weight shards hurt throughput by 38%,
and deleting it restored performance — is a Linus engineering convention (DEC-0027). Before designing custom caching for
any data-streaming or weight-streaming workload, default to trusting macOS's unified page cache. Only build custom
caching when measurement demonstrates the OS cache underperforms.

### Public APIs only

Linus's own code stays on supported public Apple APIs (CoreML, MLX, Metal). No reverse-engineering of Apple's private
APIs (DEC-0027). pmetal uses supported APIs; the ANE reverse-engineering repo in `repos/ANE/` is methodology reference
only, not vendored. If pmetal goes dormant, the fallback (Ollama + mlx-lm-ft) is fully public-API.

### Multi-language stance

Python is the core orchestration language. Components in Rust (pmetal, claw-code, claw-code-local),
JavaScript/TypeScript (openclaw, some npm tooling), and Bash (stringing CLI tools) are acceptable when they fit the task
(DEC-0027). No single-orchestration-language policy. Choose the language that fits the component.

### Curation cadence

`repos/`, `context/`, and `docs/` grow rapidly with reference material. Apply the curation protocol at
`docs/protocols/curation-protocol.md` (DEC-0025): quarterly review with an explicit archive or removal pathway; removed
content recorded in `docs/curation-log.md` with rationale and timestamp. Apply The Algorithm at each review: question
every requirement; delete what no longer earns its keep. Next scheduled review: 2026-08-01.

**Factual-grep audit clause** (added 2026-05-16 from the pmetal/ANE finding). At each quarterly curation review,
grep landscape + synthesis + ADR docs for any claim about Apple private APIs, unsupported APIs, reverse-engineering,
or license-incompatibility. Cross-check every match against the source of truth (CLAUDE.md for project-level claims,
the cited repo's actual license for license claims, the referenced ADR for design claims). Factual errors propagate
silently as docs are folded into syntheses — the 2026-05-16 wave-2 audit found "pmetal uses private APIs" had
propagated to two landscape locations when CLAUDE.md is unambiguous that pmetal uses supported public APIs and only
`repos/ANE/` uses reverse-engineering. Only a directed grep catches this class of drift.

### Planning write-back cadence

Every multi-question Maestro/Dan planning session closes with explicit time allocated for core-file write-back:
CLAUDE.md, VISION.md, ROADMAP.md, ARCHITECTURE.md, SAFETY.md, DECISIONS.md, and relevant landscape and spec docs
(DEC-0026). The natural artifact is a `docs/specs/planning-update-spec.md` (rewritten per session) that routes edits to
the right files and then deploys Workers to execute them.

### Memory pillar discipline

Memory is a load-bearing architectural pillar (DEC-0028). Five layers: intra-step latent (Layer A), within-session
scratchpad (Layer B), cross-session episodic (Layer C, SQLite + content hashes + git), investigation memory (Layer D,
task-scoped multi-agent), and semantic knowledge (Layer E, KnowledgeBase). Implementation contract:
[`docs/specs/memory-architecture.md`](docs/specs/memory-architecture.md).

Three discipline rules apply across all Worker work:

- **Scratchpad is durable.** Reasoning tokens are first-class addressable artifacts (DEC-0030); silently truncating
  reasoning between turns is forbidden.
- **Context is a resource to manage, not a capacity to fill.** Phase 2 default in-context cap: 16K tokens per Worker
  call (DEC-0032); overflow routes through the episodic store; explicit cap-bypass is audit-logged.
- **Memory mode is dispatch-time-explicit.** Every Worker call carries a `memory_mode` (`stateless` / `session_stateful`
  / `project_stateful`) and a `cot_budget` (`logarithmic` / `linear` / `polynomial`) per DEC-0031. Both recorded in the
  audit log.

### Typed structured prediction for biology skills (resolved 2026-05-06, S25)

For any biology skill or domain skill producing a predictive output, use typed structured prediction wrapping free-text
rationale — the BioReason-Pro shape. The structured result is machine-queryable; the `rationale` field preserves
explanation for human review. Example:
`{gene: "BRCA1", predicted_function: "DNA repair", confidence: 0.87, evidence: ["pmid:12345"], rationale: "..."}`. This
generalizes beyond biology to any task where auditability matters.

### Sub-agent hook bypass flow

When a Worker writes a file, the `PostToolUse` hook triggers on the Worker's Edit/Write calls. If the Worker is running
in a context where hooks can't execute (e.g., sub-agent invocation without hook propagation), the canonical flow is:
Worker writes → Maestro formats (runs prettier/ruff manually if needed) → Maestro commits. Never skip formatting
silently; the commit should always reflect hook-clean output.

### Internal-error recovery protocol

When a Worker task produces a missing or empty result and the session log shows an internal error, check the filesystem
state before re-issuing the task. Workers may have partially written output even if the session terminated abnormally.
Check the target files and branch state first; re-running a completed task wastes tokens and may overwrite good work.

**API-error mid-work recovery for in-worktree agents.** When an agent dispatched with `isolation: "worktree"` returns an
API error (529 Overloaded, 503, network) after writing files but before committing, the files persist in the agent's
worktree at `.claude/worktrees/agent-<id>/`. The agent's branch pointer is still at the base SHA; the work-in-progress
is in the worktree's working tree, unstaged. Maestro can land the work directly without re-dispatching:
`git -C .claude/worktrees/agent-<id> status` to inspect, then `git -C ... add ...`, `git -C ... commit -m "..."`,
`git -C ... push -u origin <branch>` to publish. The pattern was validated 2026-05-18 when 3 of 4 refresh-fanout agents
hit API 529 after completing all 9 file edits — every file recovered cleanly via Maestro-side commit + push. Re-dispatch
would have burnt fresh tokens to redo work already done, and worse, re-rolled the model's outputs (a 7B Worker doesn't
deterministically reproduce a 200-line refresh).

### State verification across context boundaries

When state was established in a prior context — different session, compaction summary, or Maestro's own earlier claims
in the same session — verify before building on it. Canonical failure mode (PR #12, 2026-05-06): a compaction summary
stated "committed and pushed on branch X," the continuation acted on it, the commit was actually on branch Y; an empty
PR almost lost work to the reflog. Two applications:

- **Branch state before "ready to merge" claims.** Run `git log <branch>..main --stat` and `git log main..<branch>
  --stat` before any end-of-session report. If the diffs don't match expectation, the claim is false.
- **Compaction-summary humility.** Treat synthesized summaries as hypothesis, not ground truth. Verify "X was committed
  / pushed / merged / written" claims against the actual artefact.

### Cherry-pick to preserve, never reset to delete

Before any `git reset --hard` past a commit, run `git branch --contains <sha>` to confirm it exists elsewhere. If not,
reset leaves the commit reachable only via reflog (~90 days, durable for zero). Safe pattern: cherry-pick first to a
known-good branch, then reset. Canonical failure mode: Task A redo (2026-05-06) where a cleanup reset destroyed the
only copy of a cherry-pickable commit; reflog rescue worked but the discipline rule is cheaper.

Cherry-pick recovery is also the load-bearing discipline when shared-checkout parallel agents collide (validated 3-for-3
in 2026-05-16 wave-2 fanout). When an agent reports "my commits landed on the wrong branch": identify the agent's
commits by scope tag (`[orch]`, `[memory]`, `[kb]`, `[bench]`, `[docs]`, `[adr]`), `git checkout -b <rescue-branch>
origin/main`, `git cherry-pick <sha>...`, push, open PR. Never `git reset --hard` the contaminated branch; let it
linger as audit trail until the rescue PR merges.

### PR summary discipline

PR descriptions are the durable record of what a change does and why. They should follow a uniform template so a
reviewer can scan a batch of related PRs without recalibrating per-author style. The template:

```markdown
## Summary

<1–2 sentence executive summary: what the PR changes and why>

## Changes

- **<spec-item-id>** — <terse 1-line description>. <DEC refs where relevant>
- ...
- **Bonus fix** — <description> (only when applicable)

## Spec

See [`docs/specs/<spec-name>.md`](docs/specs/<spec-name>.md) — Task <X>.

[## Background — only when reviewer needs context, e.g. a redo or a non-obvious dependency]
```

Apply this for every Worker-delivered or Maestro-delivered PR that descends from a planning-update spec or any
multi-task spec doc. Per-PR ad-hoc structures (Test plan checklists, prose blocks, bold-per-file headers) are
specifically out of scope; pick this template even if it feels less expressive for a particular task. Consistency across
the batch beats expressivity within one PR.

### Agent fan-out: probe permissions first

When fanning out N parallel agents that need bash access for `git` / `gh` / `pytest` / similar operations, probe with a
single canary agent before the full fan-out. Run a one-step task that exercises the same tool surface (e.g., "create a
branch, write a file, commit, push, open a PR") and confirm the agent completes. If the canary is blocked at a step, the
full fan-out will be blocked too — and Maestro will end up doing the work serially anyway, having paid the fan-out tax
for no parallelism gain. The canary costs a minute; debugging six stuck agents costs much more.

### Worktree fan-out discipline

Worktrees enable genuine parallel agent work but carry non-obvious failure modes. Apply these rules for any
`isolation: "worktree"` agent dispatch or manual `git worktree add` fan-out.

**HARD RULE: parallel Maestro-dispatched agents MUST run in isolated worktrees.** When dispatching N>1 agents
concurrently, every agent gets its own physical checkout (`isolation: "worktree"` on the Agent tool, or manual
`git worktree add`). Shared-checkout parallel agents collide on `.git/HEAD`: branch switches revert mid-command, commits
land on sibling branches, recovery requires cherry-pick. Validated 2026-05-16: 7 shared-checkout agents → 1 outright
failure + 2 cherry-pick recoveries + branch-proliferation artifacts; subsequent 9 in isolated worktrees → zero
collisions. The §"When not to use worktrees" exception below applies only to SEQUENTIAL dispatch.

**Default to the main checkout.** Worktrees are the exception. Strategic analysis, artifact production, single-file
refactors, corpus reads, spec writing — none need worktree isolation and most are actively harmed by it
(path-resolution surprises, invisible-filesystem artifacts, cleanup overhead). Create a worktree only for parallel
agent fan-out, in-progress PR work that must coexist with mainline edits, or atomically-throwaway experiments. If a
session opens in a worktree and doesn't need one, dismantle and continue in main — staying in a wrong-shaped worktree
compounds cost across the session.

**Branch preservation.** `git worktree remove` deletes the directory but leaves the branch pointer. Preserve it. Do NOT
immediately `git branch -D` agent branches after worktree removal — retain them at least until the consolidated PR is
open (audit trail; re-cherry-pickable if conflict resolution was wrong). Delete after commits confirmed on the merged
target branch. Fast-track exception: if cherry-picks were clean (no conflict resolution involved), delete on
consolidation-push rather than waiting for PR merge — the commits are byte-identical with the consolidation branch's.

**Base-SHA pinning.** All parallel worktrees in one fan-out must branch from the same commit. Record base SHA
(`git rev-parse HEAD`) before dispatching; include it verbatim in each agent's prompt. If Maestro commits to base
between agent dispatches, later agents see a different base and consolidation cherry-picks produce false conflicts or
silently miss commits. Verify with `git log <agent-branch>..<base-branch>` before cherry-pick consolidation.

**Edit-tool path resolution.** Inside a worktree, Edit/Write with absolute paths sometimes resolve to the primary
checkout rather than the worktree — the resolver anchors to the registered primary. Agents inside worktrees should use
`git -C <worktree-path>` for git operations and prefer `Bash(cd <worktree-path> && <cmd>)` over direct Edit calls. When
an agent reports "file already has this content" or edits appear in the wrong checkout, the root cause is almost always
absolute-path resolution. Recovery: capture `git diff` in main, `git checkout --` to restore main, `git apply` inside
the worktree.

**Editable installs (`pip install -e .`) collide with worktrees on import resolution.** When `pip install -e .` is run
from the main checkout, the resulting `.pth` / `__editable__` finder points Python at the **main** checkout's `src/`, so
`python -c "import linus.foo"` and `pytest` inside a worktree silently resolve to MAIN's code, not the worktree's. Every
fix agent in the 2026-05-21 arc hit this. Recovery: run the worktree's Python with `PYTHONPATH=<worktree>/src pytest ...`
(or `cd <worktree> && PYTHONPATH=$PWD/src ...`) so the worktree's source wins. Suspect it whenever a worktree agent's
test run passes or fails in a way that doesn't match the edits it just made (R5-04).

**Handoff artifacts written into a worktree are invisible to humans in the main checkout.** Write handoff files (specs,
briefs, drafts in `experiments/`) using the main-checkout absolute path
(`/Users/dbrowne/Desktop/Programming/GitHub/Linus/experiments/...`) — not the worktree-relative path. Worktrees get
removed; the human looking at `~/Linus/experiments/...` sees nothing. If the artifact must live in the worktree for
in-flight reasons, copy it out before dismantling.

**When not to use worktrees.** For fan-outs where agents write non-overlapping files on a shared branch (N notes, N
analyses) AND the dispatch is SEQUENTIAL (not parallel), file-level partitioning is simpler than worktree isolation —
Maestro commits each agent's output without the worktree overhead (base-SHA drift, path-resolution quirks, manual
cleanup, cherry-pick conflicts). For PARALLEL dispatch, the hard rule above wins regardless.

**Worktrees can't see gitignored content; agents needing to read it must use absolute paths to the main checkout.**
`git worktree add` creates a working directory containing TRACKED files only. Gitignored content — notably `repos/`
(138 cloned reference repositories), `context/`, `~/.linus/` artifacts — is NOT carried into the new worktree's
filesystem space. Agents that need to read gitignored content (e.g., refreshing a repo-note against current upstream,
running benchmark fixtures from `context/papers/`) must use the absolute path of the main checkout:
`/Users/dbrowne/Desktop/Programming/GitHub/Linus/repos/<name>/`. The absolute path resolves to the actual filesystem
location regardless of which worktree the agent is in. This is reads-only safe — writes via absolute path hit the
Edit-tool path-resolution quirk documented above, which agents must recover via the standard capture-diff / restore-main
/ git-apply pattern. When dispatching agents that need both read-from-gitignored-source and write-to-tracked-target,
state this explicitly in the prompt: "Use absolute paths to read FROM `repos/...`; writes to `docs/...` should land in
your worktree but may hit the path-resolution quirk — use the recovery pattern."

**`git -C <path>` over `cd <path>` when operating across multiple worktrees.** Multi-worktree operations from Maestro
(committing + pushing in each of N worktrees in sequence) are vulnerable to CWD confusion: a `cd` from a prior Bash call
leaves Maestro's CWD in a worktree that may not be the one Maestro intends for the next operation. The 2026-05-18
recovery flow hit this — a `git add` for "batch 3 files" was issued with CWD pointing at batch 2's worktree, and the
command silently no-op'd because those files weren't where CWD was. Use `git -C <worktree-path> <subcommand>` for every
git operation that crosses worktree boundaries. This makes each operation explicit about its target and immune to the
silent-wrong-worktree class of bug. Reserve `cd` for cases where multiple sequential commands genuinely share a working
directory inside the same Bash invocation chained by `&&`.

**Worktree cleanup sequence.** After all agent commits are cherry-picked and confirmed:

1. `git worktree unlock <path>` — release any stale process lock
2. `git worktree remove --force <path>` — removes directory; branch pointer persists
3. Verify: `git branch | grep agent/` — branches should still appear
4. Delete branches only after the consolidated PR is merged: `git branch -D agent/<name>`

**Source-branch cleanup timing — default conservative, fast-track when cherry-picks are clean.** Step 4 above defaults
to "delete only after the consolidated PR is merged" because keeping source agent branches alive lets you re-cherry-pick
if you discover a conflict-resolution error. That conservative rule is correct when cherry-picks involved real merge
conflicts and you might need to re-resolve. When cherry-picks were CLEAN (no conflict markers, byte-identical diffs
against the consolidation branch), the source branches carry no information the consolidation branch doesn't already
hold — they can be deleted as soon as the consolidation branch is pushed and the PR is opened. The 2026-05-18 refresh
fanout used this fast-track: 4 source branches were deleted while PR #57 was still open, with no recovery risk because
every cherry-pick had landed conflict-free. The end-of-session sweep then becomes:

1. Identify source branches whose commits exist on either `main` (merged PRs) or an open consolidation PR (clean
   cherry-picks).
2. Local delete: `git branch -D <name>` for each.
3. Remote delete: `git push origin --delete <name>` for each.
4. `git remote prune origin` to clear stale remote-tracking refs.
5. Dismantle all worktrees per the sequence above.

Mass-deletion safety check before step 2: confirm each source branch's commits are represented on the consolidation
branch via `git log <consolidation-branch> --grep "<scope-tag>"` or by reading the PR description's named source SHAs.
If a source branch had merge-conflict cherry-picks, keep it until the consolidation PR merges (the conservative rule).

**End-of-session dismantling, not just post-PR.** The sequence above is canonically written for the
after-cherry-picks-and-PR-merge case, but the same sequence applies whenever a worktree's purpose is complete —
including a session ending without commits, a piece of work being abandoned, or the work being completed in a different
way than the worktree was created for. Lingering worktrees accumulate, get rediscovered weeks later in confusing
states, and contribute to path-resolution surprises in future sessions. If a worktree exists at end-of-session and the
next session won't immediately need it, dismantle. Worktrees are cheap to recreate; lingering ones are not cheap to
debug. For branches with zero unique commits (e.g., a session that produced artifacts but no commits to the worktree's
branch), the branch-preservation rule above does not apply — delete the empty branch as part of dismantling.

### Writing style for docs

Prose over bullet-heavy dumps for anything a human will read. Markdown files in this repo communicate reasoning, not
just facts. Lists where they clarify; paragraphs where they reason. Claude Code: when generating docs, follow this
style.

### Doc-type conventions

Per-document-type shapes. Fan-out agents must match them exactly — fixed section order matters because cross-doc grep
relies on it. Don't reorder without surfacing the change as a convention update. Also add a `## References`
bibliography to the end of each synthesis (per PR #55 convention) listing the repo-notes and paper-notes it cites.

**Paper-note** — `docs/paper-notes/<paper-id>.md`. YAML frontmatter: `title`, `source`, `authors`, `affiliation`,
`date`, `pdf`, `tags`. H1 = paper title. Eight H2 sections in fixed order: `## TL;DR` · `## The problem (in plain
language)` · `## What they propose` · `## Key results` · `## What's reusable in Linus` (maps each point to a phase
1..8, references DEC/spec where applicable) · `## What's NOT applicable / hype filter` · `## Connections` (relative
markdown links) · `## Open questions for Dan` (numbered sequentially, no gaps).

**Paper-note paired-repo variant.** When the source PDF lives in a paired repo (model release shipping its own tech
report alongside weights/code), use hybrid filename `<RepoName>-<arxiv-id>.md` and point `pdf:` at the repo path
(`../../repos/Kimi-K2/tech_report.pdf`). Canonical: `paper-notes/Kimi-K2-2507.20534.md` ↔ `repo-notes/Kimi-K2.md`.

**Repo-note** — `docs/repo-notes/<repo-name>.md`. No frontmatter. H1 = `` # <repo-name> (`<owner/repo>`) ``. Seven
numbered H2 sections: `## 1. Purpose and scope` · `## 2. Architecture summary` · `## 3. What's reusable in Linus` ·
`## 4. What's inspiration only` · `## 5. What's incompatible or out of scope` · `## 6. Recommendation: **<verdict>**`
· `## 7. Questions for Dan`. Verdict vocabulary: **Integrate**, **Study**, **Adapt**, **Watch**, **Ignore** (single
primary verdict + optional modifier). Section 7 numbered sequentially. Same Reusable / Connections / Open-questions
discipline as paper-notes.

**Refreshed-note dated line.** When refreshing a repo-note against current upstream, add immediately after H1:
`_Refreshed YYYY-MM-DD against upstream HEAD <short-sha>; <N commits / M files> reviewed._` (per 2026-05-18 refresh
convention).

**Partial-resolved citation.** Items use `_Partially resolved (DEC-NNNN, see [answered-questions.md](...)): nuance._`
where DEC-NNNN is the resolving ADR. S-NN / E-NN / M-NN IDs from the planning-update arc are also accepted; agents
should not normalize them to DEC-NNNN unless the mapping is verifiable from `docs/adr/`.

**Audit** — `docs/audits/<batch-name>/<source>-audit.md`. H1 = subject. Sections: `## Summary` · `## Findings` (H3
sub-categories by severity/class) · `## Remediation recommendations (priority order)` · `## Confidence assessment`.

**Session summary** — `docs/session-summaries/<YYYY-MM-DD>-<slug>-session-summary.md`. Sections in order: `##
Pre-execution context` · numbered `## Step N — <name>` · `## Lessons learned (write-back candidates)` (H3 per
destination doc) · `## Outstanding items for next session` · `## Suggested next steps`. Date prefix + lessons-learned
sub-structure required; record "estimated wall time vs actual" in the closing section per §Measure, don't just
estimate.

### Measure, don't just estimate

Every multi-step task and fan-out logs start time, end time, and a variance note when actual diverges from estimate by
>~20%. Per-session summaries record "estimated wall time vs actual" in closing; per-fan-out reports record bin-level
timestamps and Maestro records delta vs estimate in the spec's status line at consolidation. Use the accumulated
record to anchor future estimates — if "spec → canary → parallel fan-out → consolidate → PR" consistently overruns
2-hour estimates by 50%, the next plan starts from a 3-hour empirical anchor. Flash-moe pattern (DEC-0027) applied to
workflow estimates: measurement beats intuition.

### ADR numbering atomic reservation

The next-free DEC-NNNN number is reserved by writing the file. On collision (two agents authoring the same number),
first-to-commit wins; the late agent picks the next free. "Seed" labels in synthesis prose (`DEC-NNNN seed: ...`) are
placeholders, NOT reservations — reconcile at consolidation. The 2026-05-16 wave-2 fanout surfaced this:
`native-low-bit-apple-silicon-synthesis.md` had DEC-0055/0056 seed placeholders but those numbers were claimed by
landed ADRs (DEC-0055 filename discipline, DEC-0056 Anthropic-compat amendment); seeds need re-renumbering at next
consolidation. Treat any prose-level ADR-number reservation as soft.

### Session usage budgeting

Maestro cannot see Claude Code usage % directly; Dan reports it at planning checkpoints. Target ceiling **92%**
(soft); hard ceiling **95%** (beyond which incurs Extra usage costs). Calibration anchors from 2026-05-16
wave-2 fanout: **~2-2.5% burn per agent dispatch**, **~0.5-0.8% per Maestro turn** (crude — agents vary widely
in run length; refine anchors after every 2-3 sessions).

Planning formula at any session checkpoint:

```
remaining_budget_pct = ceiling_pct - current_usage_pct
agent_slots ≈ remaining_budget_pct / 2.5
maestro_turn_slots ≈ remaining_budget_pct / 0.7
```

Pick the mix that fits the work shape. Defer the lowest-priority items if the dispatch would exceed the ceiling.
When in doubt, undersize the batch and have agents land before the ceiling rather than risk overflow.

### Branch discipline

All changes to `main` require a pull request reviewed by Dan before merge. Branches are the unit of parallel work. See
[BRANCHING.md](BRANCHING.md) for the complete model:

- **Feature branches** (`feature/<name>`): new features, reviewed PR to `main`
- **Agent branches** (`agent/<task-id>/<slug>`): Worker-delegated tasks, always opened as PR by the Worker, reviewed by
  Dan before merge
- **Fix branches** (`fix/<name>`): bug fixes, reviewed PR to `main`
- **Experiment/spike branches** (`experiment/<name>`, `spike/<name>`): throwaway exploration, no review required, often
  deleted without merging
- **Personal branches** (`dan/<name>`): Dan's staging branches before formalizing as a PR

Push to origin and use `gh pr create` to open PRs. Maestro (Dan) reviews and merges via GitHub. Never force-push to
`main`; force-push to your own branch is OK before opening a PR. See BRANCHING.md for detailed workflows and examples.

**Pytest before merge — hard rule.** No PR opens against `main` without a clean local pytest run, and no PR description
claims green without a `Verification:` line recording what was run. Two suites:

- **Hermetic** — `pytest src/linus/tests/` (~2s, no external deps). Runs on **every** PR, doc-only included. Doc-only
  PRs still risk breaking imports referenced from docstrings or accidentally moving a code-block path; the cost of
  running it is negligible.
- **Integration** — `pytest tests/` (~12s, requires `brew services start ollama` + a pulled qwen3-class model). Runs
  whenever the PR touches `src/linus/server.py`, `src/linus/agents/`, `src/linus/knowledge/`, `src/linus/memory/`, or
  `src/linus/sandbox/`. These are the modules whose contracts cross the Ollama boundary; hermetic alone can't catch
  regressions in the model-call shape.

The rule exists because the 2026-05-19 MVP build merged 15 PRs without running pytest between them and
`test_chat_completions_happy_path` regressed silently when a too-tight `max_tokens=16` collided with qwen3:8b's default
thinking mode (fixed in PR #83). A pytest run between merges would have caught it inside one of the contributing PRs
instead of after the fact.

If a test fails, fix it BEFORE opening the PR — do not open the PR + push fixes inside it just because the branch is
ready otherwise. The PR description's `Verification:` line must reflect what is true at PR-open time, e.g.
`Verification: hermetic 102 passed (~2s), integration 4 passed (~12s)`.

**Merge strategy: default is `--merge` (preserve graph), squash only on explicit justification.** Use
`gh pr merge <N> --merge --delete-branch` or the "Create a merge commit" button in the GitHub UI. Merge commits preserve
branch divergence + re-convergence in `git log --graph`, keep per-commit authorship and SHAs intact, and make
`git bisect` and selective revert practical. Squash merges collapse the branch into a single linear commit, obscuring
this structure — they're the right tool only when a PR contains noisy fix-up commits that don't tell a coherent story
(e.g., "fix typo", "rebase", "address review feedback") and a clean single-commit summary is more readable than the
constituent commits. When squash is the right call, state the reason in the PR description; otherwise default to merge.
Repo-level enforcement: disable "Allow squash merging" in GitHub repo settings (Settings → General → Pull Requests) so
the merge button cannot fall back to squash without re-enabling first.

## Session Startup Protocol

When Claude Code opens a session in this repo:

1. Read CLAUDE.md (this file) fully.
2. Read VISION.md if the task touches project direction.
3. Read ROADMAP.md if the task relates to phased work.
4. Read ARCHITECTURE.md if the task involves components or interfaces.
5. Check DECISIONS.md (and the per-file ADRs in `docs/adr/`) for any decision relevant to the task.
6. For any non-trivial change: propose a plan before editing. Use the `[Plan]` → `[Act]` workflow pattern.
7. After 3–4 file edits, post a checkpoint summary.
8. Before long runs: smoke-test on a sample.
9. On session end or significant pauses: commit with a clean message.

## Maestro/Worker Protocol (summary, full version in docs/protocols/)

For a task you (Claude Code, playing Maestro) could delegate to a local Worker:

1. Write a concise spec in `experiments/<task>.md` or `docs/specs/<task>.md`
2. Spec contains: goal, inputs, outputs, constraints, success criteria, smoke test
3. Invoke Worker with the spec (via Ollama API, Cline, or future Linus backend)
4. Worker implements. Claude Code reviews the result.
5. If the spec needed clarification, update the spec. Specs are living docs.

## Tool Use Policy

**Network egress requires design-time review (DEC-0061).** Any tool registered with
`network_policy != "offline"` (i.e. `online_optional` or `online_required`) constitutes a potential
exfiltration surface, however narrow. Before such a tool merges to `main`, Maestro (Dan + hosted Claude)
reviews: what hostnames it contacts, which fields of the call carry user / KB / corpus data, the host's
privacy posture, and what happens to the data after the response returns. The review lives in the tool's
PR description and the answering ADR if one is filed. This is the same discipline that gates `repos/`
additions and any `pip install` outside a `uv venv` — network egress is the same kind of trust decision.

### Allowlist (auto-execute OK)

- Read any file under the Linus tree
- Write/edit files under `src/`, `benchmarks/`, `experiments/`, `docs/`
- Run `pytest`, `ruff`, `prettier --write|--check` (Linus tree only), `mdlint check` (Linus tree only — but see Known
  Library Quirks; mdlint mutates), `python` (in linus env), `git add`, `git commit`
- Read-only git: `git status`, `git log`, `git diff`, `git branch`, `git show`, `git worktree list`, `git for-each-ref`,
  `git reflog`, `git rev-parse`, `git cherry-pick` (within Linus tree, agent branches only)
- Branch creation and pushing: `git switch -c <branch>`, `git push -u origin <branch>`
- Pull request creation and interaction: `gh pr create`, `gh pr view`, `gh pr list`, `gh pr comment`, `gh pr merge`
  (with Dan approval for merge)
- `ls`, `cat`, `grep`, `tree`, `wc`, `head`, `tail`, `find`, `awk`, `sed` (read-only `-n`), `sort`, `uniq`, `xargs`
- **Compound shell statements** that wrap allowlisted commands: `for X in ...; do <allowlisted-cmd>; done`,
  `while read X; do <allowlisted-cmd>; done`, pipelines among allowlisted commands (`grep | sort | uniq`,
  `git worktree list | awk | while ...`), and `python3 <<'EOF' ... EOF` heredocs that run scripts containing only
  allowlisted operations. The compound is allowlisted iff every command and side-effect inside it is allowlisted.
- **Worktree management**: `git worktree unlock`, `git worktree remove --force` (within `.claude/worktrees/` only),
  `git branch -D worktree-agent-*` (only branches matching that pattern).

### Require confirmation (show command, wait for OK)

- `git push` to `main` (always forbidden; use PR + Dan review instead)
- `git rebase`, `git reset --hard` (rewrites history; ask first)
- `git push --force` anywhere (forbidden; see BRANCHING.md)
- File writes outside `src/ benchmarks/ experiments/ docs/` (including repo root edits)
- Shell commands touching `~/` outside the Linus tree
- Any network operation (curl, wget, pip install, brew install, ollama pull)
- Running a model against full KnowledgeBase corpus (must smoke-test first)

### Forbidden (do not propose)

- `rm -rf` on anything under `~/` or `/` (avoid key system files for maximal safety)
  - Temporary files as part of our workflows may be safely created and destroyed in `/tmp`
  - Files may be deleted within the git-tracked Linus directory as part of our work
    - When removing git-tracked files, use `git rm`, otherwise use `rm`
  - At this point, seek user permission before deleting any files (more autonomy may be granted in future)
- Edits to `modules/KnowledgeBase/` (it's a submodule — work happens in the KnowledgeBase repo)
- Edits to `repos/*` (reference-only clones)
- Writing to `~/.ssh`, `~/.aws`, or any credentials path
- `sudo` anything
- Modifying `.gitignore` or `.gitmodules` without explicit request

See SAFETY.md for autonomy tier graduation and the full policy.

## Known Library Quirks

_(This section grows over time. Append entries as issues are resolved.)_

**Ollama via conda is CPU-only.** Use the Homebrew install (`brew install ollama` + `brew services start ollama`). The
conda build lacks Metal acceleration. Inherited from KnowledgeBase.

**Ollama port conflict recovery.** If a stale `ollama serve` from a conda shell holds port 11434, `brew services` fails
with `fork/exec`. Fix: `pkill -f 'ollama serve' && brew services restart ollama`. Inherited from KnowledgeBase.

**Optional Ollama speed env vars**: `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`. Set before
`brew services start`.

**pypdf decompression limit**: disable with `sys.maxsize`, NOT `0` or `2**63`. Inherited from KnowledgeBase.

**SQLite large writes**: batch commits in chunks of 100–500 rows. Single transactions on 10k+ rows fail. Inherited from
KnowledgeBase.

**`mdlint check` 0.3.15 silently auto-fixes some rules.** Despite the `--fix` flag being documented as opt-in,
`mdlint check` applies "safe" fixes unconditionally — notably MD004 (list marker style). On prose containing characters
that look like list markers (e.g. a `+` in the middle of "ANE + MLX + serve") this corrupts the meaning by rewriting `+`
to `-`. Consequence: mdlint is **not** in the `PostToolUse` hook chain (only `prettier --write` is). Run
`mdlint check <file>` manually with confirmation when you want lint feedback, and inspect the diff before keeping it.

**Trust the OS page cache for memory-mapped file workloads.** From the flash-moe study (G1 synthesis,
`docs/syntheses/repo-clusters/g1-apple-silicon.md`): a hand-engineered 9.8 GB Metal LRU cache wrapping mmap'd weight
shards _hurt_ throughput by 38%; deleting the cache and trusting the macOS unified-buffer cache produced the speedup.
The principle generalizes — application-level caches that compete with the OS buffer cache typically harm performance on
macOS unified memory. Profile before adding any caching layer over `mmap`'d files; default position is "let the OS
handle it."

**`prettier` markdown config: `printWidth: 120`, `proseWrap: always`.** Set in `.prettierrc.json` via an `*.md` override
to match the Python ruff convention (also 120). With `proseWrap: always`, prettier actively re-wraps prose to fit the
column budget — paragraphs become long lines wrapped at 120, not the older 60–65-character convention. The full corpus
was bulk-reformatted in a single commit (see git log for `[format] prettier --write`); subsequent edits should not
produce noisy reformatting diffs. Prettier also normalizes heading style, list marker style at true list positions
(distinguishes from in-prose `+`), trailing whitespace, and final newlines.

**Disposable uv envs for experimental packages.** Untrusted or experimental Python packages always go in a fresh
`uv venv`, never `pip install` into the linus conda env (DEC-0024). The linus env is the production substrate,
hash-pinned and audited. Create with `uv venv .venv && source .venv/bin/activate`; discard after the experiment.

**GitHub PR `baseRefOid` caching artefact.** When a PR is opened from a branch that's based on a local main ahead of
origin/main, GitHub captures `baseRefOid` at the older origin/main commit. Even after origin/main advances, GitHub does
not auto-refresh `baseRefOid`, so the PR's diff display shows the stale-base diff (extra commits, extra files, all
appearing as "changes in this PR"). The merge itself is correct — only the head branch's unique commits land — but the
review UI is misleading. Workarounds: (a) push local main to origin/main before opening task PRs so the captured
`baseRefOid` is current; (b) verify true diffs with `git diff origin/main..origin/<branch>` not via `gh pr diff`; (c)
manually update the base in GitHub UI after origin/main advances. The cleanest fix is (a) — keep origin/main current
before fanning out task branches.

**Empty PRs from branches even with main may auto-fast-forward on merge.** A PR opened from a branch that has zero
unique commits beyond its base (i.e., `git log base..head` is empty) will still merge if Dan clicks "merge." The merge
behaves as a fast-forward of `origin/<base>` to wherever the head pointed at PR creation, which can advance
`origin/main` by N commits even though the PR itself has no diff content. Side effect: a PR can serve as an ancillary
push vehicle for prior local-main commits. This is not a bug but it can confuse reviewers. PR #12 (2026-05-06) was the
canonical instance — see the planning-update-execution session summary for the full incident.

**Xcode Metal Toolchain is a load-bearing dep for Metal-shader builds; macOS updates silently break it.** Rust/C++
projects that compile Metal shaders (notably `repos/pmetal/` building `pmetal-bridge` via MLX) require Xcode's Metal
Toolchain component. macOS updates can silently invalidate this component, causing `cargo build` to fail deep in the
build script with `error: cannot execute tool 'metal' due to missing Metal Toolchain; use: xcodebuild
-downloadComponent MetalToolchain`. Recovery (interactive, requires user; cannot be automated by Maestro):

```
xcodebuild -runFirstLaunch          # if xcodebuild itself reports a plug-in load failure
xcodebuild -downloadComponent MetalToolchain
```

First hit + recovered 2026-05-19 during the pmetal v0.5.0 rebuild for the Agora hackathon. The fix is environmental,
not code — do not attempt build-script workarounds. After each macOS update, plan for the possibility that the next
pmetal build will need this sequence rerun.

---

_This file is the contract between Dan and Claude (Maestro), and any Worker operating in the Linus repo. Update it when
conventions change. Don't silently drift._
