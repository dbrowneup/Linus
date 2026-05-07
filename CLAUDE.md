# Linus — Claude Code Context

## Project Purpose

Build a private, local, modular AI assistant named **Linus** that runs on Apple Silicon, provides Claude-equivalent
capabilities for Dan's scientific and software work, and stays fully under Dan's control. Named after Linus Pauling
(scientist, humanitarian, Oregonian) and Linus Torvalds (engineer, open-source advocate, Oregonian). Logo: a carbon
atom. Linus is a force that harnesses human knowledge for good in the world.

## Owner Background

- Daniel R. Browne, 37 (GitHub: dbrowneup, email: dbrowne.up@gmail.com)
- **Current role**: Senior Scientist at LanzaTech (Skokie, IL), since Apr 2026. Maintains enterprise LLM infrastructure
  for company-wide AI tools and leads development/validation of bioinformatics software for metagenomics analyses.
  Promoted from Computational Biologist (Jun 2023–Mar 2026) at the same company, where he led metagenomics SW dev,
  analyzed genomic/metagenomic datasets for commercial process insights, and trained colleagues on bioinformatics
  workflows.
- **Prior industry**: PacBio (Chicago, 2019–2023) — Product Owner for Bioinformatics & Sequencing Platforms (Jul 2021–
  Jan 2023), translating user needs into product requirements across R&D/Sales/Support; before that Field Applications
  Scientist for Bioinformatics, supporting 35+ customer accounts on complex long-read pipelines and identifying edge
  cases.
- **Education**: PhD Biochemistry, Texas A&M (2018), with a Graduate Certificate in Entrepreneurship; BS Environmental
  Science with Chemistry minor, University of Portland (2011). Doctoral thesis on systems analysis of metabolism and
  physiology in the oil-producing green alga _Botryococcus braunii_ (Showa, race B).
- **Domain specialty**: genomics and computational biology — long-read sequencing (PacBio HiFi), genome/transcriptome
  assembly, comparative genomics, metagenomics, gene cloning/expression/editing, protein purification and enzyme
  assays. _B. braunii_ genome assembly and downstream lipid/terpene metabolism analyses are the deepest part of his
  publication record (11 publications, 15 presentations).
- **Production stack he already operates in**: Python, Linux, Bash, Git, GitHub, GitHub Actions, SQL, WDL, Docker, AWS,
  Azure; Agile/Jira; pipeline validation and automated testing.
- **Entrepreneurship background**: founded Botryonyx LLC (2018–2019), an algae-based wastewater-treatment + carbon-
  capture venture; raised $42K in seed funding, tested a prototype, competed at Rice Business Plan and was an SEC
  Pitch semi-finalist for Texas A&M; 2nd place at the Aggie Pitch Competition ($12K). Scientific Advisor at CaribAlgae
  in Curaçao (2018–2022). The speed-and-evidence instinct in this repo's Algorithm/blitzscaling framings is lived
  experience, not borrowed mindset.
- **13 years of Python in scientific computing**; self-taught CS, comfortable with trial-and-error debugging.
- **Currently learning**: Rust, nodejs/npm, agentic systems, LLM inference/fine-tuning. Calibrate explanations
  accordingly — deep biology/Python/Linux fluency, newer to systems-language idioms and modern JS tooling.
- **Hardware**: MacBook Pro 2021, Apple M1 Max, 32 GB unified memory, 10 CPU / 24 GPU / 16 ANE cores.
- **Storage**: 400 GB available internal SSD; 1 TB external flash SSD with ~600 GB available, attached as needed.
- **Location**: Hawthorn Woods, Illinois (greater Chicago area).

## North Star

A personal AI orchestration backend that:

- Runs on Dan's MacBook Pro (and future Mac hardware), no paid APIs required for operation
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
- **Worker** = local models (Qwen3 — best available for 32 GB M1 Max hardware; future fine-tuned Linus). Bulk implementation, test generation,
  refactors, pipeline execution.
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
- **uv** is installed inside the linus conda env via conda. uv is the **disposable-env tool of choice** for
  experimental packages: untrusted or experimental Python packages always run in a fresh `uv venv`, never installed
  into the linus conda env. The linus conda env is the production substrate (hash-pinned); uv envs are scratch space
  discarded after the experiment (DEC-0024).
- **node/npm** installable inside conda env if openclaw or other JS-based components are used.
- **poppler** is available via a Homebrew install to read PDF files in the context folder.

## Repo Layout

```
Linus/
├── CLAUDE.md              # This file — read first in every session
├── VISION.md              # The north star; project philosophy
├── ARCHITECTURE.md        # System design, layer boundaries, component diagram
├── ROADMAP.md             # Phased plan with targets
├── SAFETY.md              # Sandbox policy, autonomy tiers, forbidden ops
├── DECISIONS.md           # Pointer + index for the per-file ADRs in docs/adr/
├── GLOSSARY.md            # Terms, component names, Linus-specific vocabulary
├── README.md              # Entry point for humans
├── environment.yml        # conda env spec for `linus`
├── pyproject.toml         # Python package config for src/linus/
├── .gitignore
├── .gitmodules            # KnowledgeBase submodule pinning
├── src/                   # Linus source code — the product
│   └── linus/             # Python package
├── modules/               # Tracked live dependencies (submodules)
│   └── KnowledgeBase/     # Dan's paper corpus + RAG + knowledge graph
├── repos/                 # Reference clones (gitignored); read-only study material
│   ├── BitNet/            # Microsoft 1-bit LLM inference
│   ├── Bonsai-demo/       # PrismML 1-bit 8B MLX model
│   ├── flash-moe/         # Dan Woods Metal/Obj-C MoE streaming
│   ├── mlx-flash/         # Matt Wong MLX weight streaming
│   ├── pmetal/            # Epistates Rust ML platform for Apple Silicon
│   ├── autoresearch/      # Karpathy agentic research loop methodology
│   ├── autoresearch-mlx/  # MLX-flavored variant of Karpathy's research loop
│   ├── ANE/               # Maderix ANE reverse-engineering
│   ├── claw-code/         # ultraworkers Rust CLI agent harness (inspiration; Anthropic-only)
│   ├── claw-code-local/   # codetwentyfive fork adding Ollama backend (more practical lead)
│   ├── openclaw/          # openclaw local-first gateway (reference/future front-end)
│   ├── cline/             # VS Code agentic coding extension
│   └── project-nomad/     # Offline knowledge server (inspiration only)
├── context/               # Dan's personal context (gitignored: papers, threads, notes, pics)
│   ├── papers/
│   ├── books/
│   ├── threads/
│   ├── notes/
│   └── pics/
├── benchmarks/            # Evaluation harnesses, Dan task suite, results
│   ├── dan_tasks/         # Private benchmark suite (Dan-authored)
│   └── results/           # Dated JSON result files
├── experiments/           # Throwaway scripts, ablations, quick tests
└── docs/                  # Long-form writing, synthesis notes
    ├── adr/               # Per-file ADRs (NNNN-<slug>.md matching DEC-NNNN ids)
    ├── landscapes/        # total-landscape, synthesis-landscape (paper/repo are deprecated stubs)
    ├── paper-notes/       # ~100 per-paper write-ups + INDEX.md
    ├── papers/            # Paper-corpus index (paper-notes/INDEX.md mirror; pointer doc)
    ├── protocols/         # maestro-worker-protocol, curation-protocol
    ├── questions/         # top-questions, open-questions, answered-questions
    ├── repo-notes/        # ~99 per-repo write-ups + INDEX.md
    ├── session-summaries/ # Maestro session recaps (one per substantive session)
    ├── specs/             # Implementation specs (memory-architecture, phase*-spike, kb/, etc.)
    └── syntheses/         # 14 thematic + 11 cluster (g1–g11) synthesis docs
```

## Phased Plan

See [ROADMAP.md](ROADMAP.md) for full detail. Current phase markers:

- **Phase 0 — Foundation** _(closed)_: scaffolding, docs, env
- **Phase 1 — Recon & Baselines** _(in progress)_: synthesis notes, benchmarks, pmetal eval, first loop
- **Phase 2 — Linus MVP**: orchestration backend, chat UI, KnowledgeBase v1
- **Phase 3 — Knowledge & Parallel Agents**: deeper KB integration, agent fan-out
- **Phase 4 — Data Sovereignty**: Kiwix, ProtoMaps/OSM, versioned datasets
- **Phase 5 — Interface Refinement**: openclaw as front-end, VS Code polish
- **Phase 6 — Fine-Tuning**: LoRA on domain corpus, flash-streaming inference
- **Phase 7 — Skills & Autonomy Graduation**: domain tools, widening sandbox
- **Phase 8 — Beyond MacBook**: mobile, Mac Studio, native app, Vision Pro

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

`.claude/settings.json` runs a `PostToolUse` hook on `Edit|Write`. Each sub-command guards on the file extension so
unrelated edits skip cleanly. Python edits are formatted by `ruff format` at line length 120, import-sorted by
`ruff check --select I --fix`, then linted by `ruff check`. Markdown edits are formatted by `prettier --write`; the
prettier config at `.prettierrc.json` overrides `printWidth: 120` and `proseWrap: always` for `*.md` files, so markdown
prose is actively re-wrapped to 120 columns (matching the Python convention) rather than preserving original line
breaks. `.prettierignore` keeps `repos/`, `modules/`, `context/`, and lockfiles out of prettier's reach as
defense-in-depth.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "if [[ \"$CLAUDE_FILE_PATH\" == *.py ]]; then ruff format --line-length 120 \"$CLAUDE_FILE_PATH\" 2>&1 || true; fi"
          },
          {
            "type": "command",
            "command": "if [[ \"$CLAUDE_FILE_PATH\" == *.py ]]; then ruff check --select I --fix \"$CLAUDE_FILE_PATH\" 2>&1 || true; fi"
          },
          {
            "type": "command",
            "command": "if [[ \"$CLAUDE_FILE_PATH\" == *.py ]]; then ruff check \"$CLAUDE_FILE_PATH\" 2>&1 || true; fi"
          },
          {
            "type": "command",
            "command": "if [[ \"$CLAUDE_FILE_PATH\" == *.md ]]; then prettier --write \"$CLAUDE_FILE_PATH\" 2>&1 || true; fi"
          }
        ]
      }
    ]
  }
}
```

`mdlint` (the Markdown linter — pip-installed alongside prettier in the linus env) is **deliberately not in the hook
chain.** mdlint 0.3.15's `check` subcommand silently auto-fixes some rules (notably MD004 list marker style) even
without `--fix`, which can corrupt prose containing characters that look like list markers — e.g. `+` in the middle of a
sentence about feature flags gets rewritten to `-`. Run mdlint manually with confirmation when you want lint feedback;
do not put it in the auto-format chain. See Known Library Quirks below.

### Commit discipline

Atomic commits per resolved issue. Descriptive messages in imperative mood ("Add Linus tool registry" not "Added tool
registry"). Scope tags welcome (`[orch]`, `[kb]`, `[infer]`, `[docs]`).

### Parallel by default

Multi-file audit, multi-repo synthesis, multi-paper analysis, benchmark sweeps — all fan out to parallel Task agents or
multiple Worker processes. Sequential is the exception, not the default.

### MCP as tool substrate (resolved 2026-05-04)

After the Section 7 fan-out, MCP-as-Linus-tool-substrate is no longer an open question — only the policy details (which
tools, what permissions, which transport) remain. Six independent repos in the cloned collection ship MCP servers
(pmetal-mcp, openclaw, py3plex*mcp, agentmemory's 51-tool MCP, keppi, plus fastmcp as the underlying framework). The G6
synthesis (`docs/syntheses/repo-clusters/g6-mcp-tools.md`) canonicalizes the verdict: in-house Linus MCP servers build
\_on* fastmcp's decorator API + middleware pipeline, not parallel to it. The MCP adoption ADR should be written at Phase
2a planning time rather than deferred to Phase 3.

### Workgraph JSONL as the Phase 2a session-store shape (recommended)

The G7 synthesis (`docs/syntheses/repo-clusters/g7-harnesses.md`) identifies workgraph's `.workgraph/graph.jsonl`
append-only DAG plus `handler_for_model.rs` dispatch as the most directly liftable orchestration runtime in the entire
cloned-repo collection — recommended as the Phase 2a session-store and audit-log format before any other format is
committed to. The Rust crate doesn't need to be vendored; the JSONL shape and dispatch pattern can be ported to Python.
Caveat: workgraph's tree-kill is Linux `/proc`-only; macOS port needs a `psutil`-based equivalent.

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
- **Memory mode is dispatch-time-explicit.** Every Worker call carries a `memory_mode`
  (`stateless` / `session_stateful` / `project_stateful`) and a `cot_budget` (`logarithmic` / `linear` / `polynomial`)
  per DEC-0031. Both recorded in the audit log.

### Typed structured prediction for biology skills (resolved 2026-05-06, S25)

For any biology skill or domain skill producing a predictive output, use typed structured prediction wrapping free-text
rationale — the BioReason-Pro shape. The structured result is machine-queryable; the `rationale` field preserves
explanation for human review. Example: `{gene: "BRCA1", predicted_function: "DNA repair", confidence: 0.87, evidence:
["pmid:12345"], rationale: "..."}`. This generalizes beyond biology to any task where auditability matters.

### Sub-agent hook bypass flow

When a Worker writes a file, the `PostToolUse` hook triggers on the Worker's Edit/Write calls. If the Worker is running
in a context where hooks can't execute (e.g., sub-agent invocation without hook propagation), the canonical flow is:
Worker writes → Maestro formats (runs prettier/ruff manually if needed) → Maestro commits. Never skip formatting
silently; the commit should always reflect hook-clean output.

### Internal-error recovery protocol

When a Worker task produces a missing or empty result and the session log shows an internal error, check the filesystem
state before re-issuing the task. Workers may have partially written output even if the session terminated abnormally.
Check the target files and branch state first; re-running a completed task wastes tokens and may overwrite good work.

### State verification across context boundaries

When state was established in a prior context — a different session, a context-window compaction summary, or even
Maestro's own claims from earlier in the same session — verify the state before building further work on it. The
canonical failure mode (PR #12, 2026-05-06): a compaction summary stated "committed and pushed on branch X." The
post-compaction continuation acted on this without verification; the commit was actually on branch Y. An empty PR was
opened and merged before anyone checked, and the actual content nearly went into the reflog-only state.

The rule has two specific applications worth calling out:

- **Branch state verification before "ready to merge" claims.** Before any end-of-session report that a PR is ready or
  that a branch contains a commit, run `git log <branch>..main --stat` and `git log main..<branch> --stat`. If those
  two commands don't show the expected diff, the claim is false.
- **Compaction-summary humility.** Treat any synthesized session summary as a hypothesis about prior state, not a
  ground truth. Verify any "X was committed / pushed / merged / written" claim against the actual artefact before
  proceeding.

### Cherry-pick to preserve, never reset to delete

Before any `git reset --hard` past a commit, run `git branch --contains <sha>` to confirm the commit exists elsewhere.
If it does not, the reset will leave the commit reachable only via reflog (recoverable for ~90 days, durable for
zero). The safe pattern is cherry-pick first to a known-good branch, then reset; never the reverse. Canonical failure
mode: the Task A redo (2026-05-06), where a "cleanup" reset destroyed the only copy of the cherry-pickable commit. The
reflog rescue worked but the discipline rule is cheaper.

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
specifically out of scope; pick this template even if it feels less expressive for a particular task. Consistency
across the batch beats expressivity within one PR.

### Agent fan-out: probe permissions first

When fanning out N parallel agents that need bash access for `git` / `gh` / `pytest` / similar operations, probe with
a single canary agent before the full fan-out. Run a one-step task that exercises the same tool surface (e.g., "create
a branch, write a file, commit, push, open a PR") and confirm the agent completes. If the canary is blocked at a step,
the full fan-out will be blocked too — and Maestro will end up doing the work serially anyway, having paid the
fan-out tax for no parallelism gain. The canary costs a minute; debugging six stuck agents costs much more.

### Writing style for docs

Prose over bullet-heavy dumps for anything a human will read. Markdown files in this repo communicate reasoning, not
just facts. Lists where they clarify; paragraphs where they reason. Claude Code: when generating docs, follow this
style.

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

### Allowlist (auto-execute OK)

- Read any file under the Linus tree
- Write/edit files under `src/`, `benchmarks/`, `experiments/`, `docs/`
- Run `pytest`, `ruff`, `prettier --write|--check` (Linus tree only), `mdlint check` (Linus tree only — but see Known
  Library Quirks; mdlint mutates), `python` (in linus env), `git add`, `git commit`
- Read-only git: `git status`, `git log`, `git diff`, `git branch`, `git show`
- Branch creation and pushing: `git switch -c <branch>`, `git push -u origin <branch>`
- Pull request creation and interaction: `gh pr create`, `gh pr view`, `gh pr list`, `gh pr comment`, `gh pr merge`
  (with Dan approval for merge)
- `ls`, `cat`, `grep`, `tree`, `wc`, `head`, `tail`

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

---

_This file is the contract between Dan and Claude (Maestro), and any Worker operating in the Linus repo. Update it when
conventions change. Don't silently drift._
