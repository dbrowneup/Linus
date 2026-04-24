# Linus — Claude Code Context

## Project Purpose

Build a private, local, modular AI assistant named **Linus** that runs on Apple Silicon,
provides Claude-equivalent capabilities for Dan's scientific and software work, and stays
fully under Dan's control. Named after Linus Pauling (scientist, humanitarian, Oregonian)
and Linus Torvalds (engineer, open-source advocate, Oregonian). Logo: a carbon atom.

## Owner Background

- Dan Browne, 37
- PhD Biochemistry (2018), specialization in genomics and computational biology
- BS Environmental Science
- 13 years of Python in scientific computing
- Self-taught CS, comfortable with trial-and-error debugging
- Learning: Rust, nodejs/npm, agentic systems, LLM inference/fine-tuning
- Hardware: MacBook Pro 2021, Apple M1 Max, 32 GB unified memory, 10 CPU / 24 GPU / 16 ANE cores
- GitHub: dbrowneup

## North Star

A personal AI orchestration backend that:

- Runs on Dan's MacBook Pro (and future Mac hardware), no paid APIs required for operation
- Exposes an OpenAI-compatible endpoint so any harness (VS Code, openclaw, LM Studio, a future native app) can use it
- Provides domain-specific tools backed by Dan's knowledge base (papers, notes, corpora)
- Supports multi-agent parallel task execution
- Enforces sandbox policy regardless of front-end
- Evolves toward hosting fine-tuned, Dan-specific models

Linus is NOT intended to replace hosted Claude. Hosted Claude plus Dan remains the Maestro for
complex reasoning and architecture. Linus is the Worker orchestra that executes under Claude's
and Dan's direction and serves Dan directly when private/offline operation is needed. Eventually, 
as Linus gets better, it can become part of the Maestro team too, directing instantiated Workers.

## Guiding Principles

### The Algorithm (Elon Musk via Jon McNeill)

Applied to every design decision, in order:

1. **Question every requirement.** Who needs this? Why? Can it be deleted?
2. **Delete every possible step.** Err aggressive. If it comes back, re-add it.
3. **Simplify and optimize.** Only after steps have been deleted.
4. **Accelerate cycle time.** Short loops produce more information than long plans.
5. **Automate.** Last, not first. Automating a bad step industrializes the badness.

**The Algorithm check**: Before adding any component to Linus, ask "can we delete this
requirement instead?" Before reaching for a new library, ask "does something we already
have serve this purpose?"

### Blitzscaling mindset (Hoffman & Yeh)

Speed is information. Short cycle times on real tasks produce better decisions than long
planning on hypothetical ones. Ship rough, learn, iterate.

### Maestro/Worker discipline

- **Maestro** = Dan + hosted Claude (this chat, Claude Code, Claude.ai). Architecture, planning,
  spec writing, hard debugging, taste-level decisions.
- **Worker** = local models (Qwen2.5-Coder, Mistral-7B, future fine-tuned Linus). Bulk
  implementation, test generation, refactors, pipeline execution.
- Maestro attention is the scarce resource. Push any well-specified task to Workers.

### Evidence beats intuition

Plateau points get resolved by measurement, not argument. Flash-moe pattern: set a metric, set
a goal, devise tests, and iterate until the goal is hit. Keep-or-revert by git. 42% of experiments being
discarded is a sign the search is working.

## Hardware Constraints

- **No CUDA.** Everything runs on Apple Silicon (Metal, ANE, unified memory).
- **Metal/MPS for GPU compute.** MLX is the primary ML framework.
- **ANE is accessible** via pmetal and Core ML; underutilized by most frameworks.
- **32 GB unified memory** is a hard constraint for fine-tuning. LoRA/QLoRA on 7–14B models is
  tractable. Full fine-tuning of 8B+ is at the edge. Streaming-based training (optimizer state
  on SSD) is open research; deferred.
- **Docker runs in a VM on macOS** and does NOT pass through Metal/ANE. Use Docker for
  stateless services only (Qdrant, Kiwix, CyberChef). Inference stays native.

## Environment

- **Package/env manager**: `mambaforge` (conda-forge) + `conda`. Base env has Python 3.12.
- **Linus env**: `conda activate linus` (set up via `environment.yml` at repo root)
- **Homebrew-installed ML tools**: `mlx`, `mlx-c`, `ollama`. Do NOT reinstall via conda — the
  brew versions are optimized for Apple Silicon.
- **Ollama** is the first worker-model server; runs on port 11434 via `brew services`.
- **Rust** is installed inside the linus conda env via `conda install rust` (needed for pmetal).
- **uv** is installed inside the linus conda env for fast Python package operations when
  needed (e.g., autoresearch-mlx).
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
├── DECISIONS.md           # ADR log — every significant decision with rationale
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
│   ├── dan_tasks/         # Private benchmark suite
│   └── results/           # Dated JSON result files
├── experiments/           # Throwaway scripts, ablations, quick tests
└── docs/                  # Long-form writing, synthesis notes
    ├── adr/               # Future per-file ADRs (once DECISIONS.md exceeds ~20)
    ├── repo-notes/        # One-pager per cloned repo
    └── maestro-worker-protocol.md
```

## Phased Plan

See [ROADMAP.md](ROADMAP.md) for full detail. Current phase markers:

- **Phase 0 — Foundation** *(closing)*: scaffolding, docs, env
- **Phase 1 — Recon & Baselines** *(next)*: synthesis notes, benchmarks, pmetal eval, first loop
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
    router · tool registry · agent spawner · sandbox · session store · audit log
            │
    ┌───────┼───────┐
    ▼       ▼       ▼
  INFERENCE  KNOWLEDGE  TRAINING
  Ollama     KnowledgeBase  pmetal / mlx-lm
  pmetal serve (submodule)
  mlx-lm
  mlx-flash (larger-than-RAM)
```

Harness ≠ Orchestration. Harnesses (Cline, claw-code, Claude Code) are coding workflows
tied to a UX surface. The orchestration layer is the product backend: Linus-specific tools,
persistent state, cross-harness policy. Front-ends come and go; the orchestration layer
accrues value. See GLOSSARY.md.

## Engineering Conventions

### Smoke-test gates

No pipeline change runs on a full dataset without a 10–50-item sample passing first.
Late-stage failures on long runs are the most expensive bug class. Smoke tests are cheap.

### Known Library Quirks

A section maintained at the bottom of this file. When a tricky constant, config value, or
library gotcha is resolved, it goes here immediately — same session, not "later." Claude
Code: if you resolve one, append it.

### Checkpoint discipline

Multi-file edits produce a checkpoint summary every 3–4 file edits: files changed, what each
change does, remaining TODOs. Makes long sessions resumable if interrupted.

### Hooks

`.claude/settings.json` runs a `PostToolUse` hook on `Edit|Write`:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [
        {"type": "command", "command": "ruff format --line-length 120 $CLAUDE_FILE_PATH 2>&1 || true"},
        {"type": "command", "command": "ruff check --select I --fix $CLAUDE_FILE_PATH 2>&1 || true"},
        {"type": "command", "command": "ruff check $CLAUDE_FILE_PATH 2>&1 || true"}
      ]
    }]
  }
}
```

### Commit discipline

Atomic commits per resolved issue. Descriptive messages in imperative mood
("Add Linus tool registry" not "Added tool registry"). Scope tags welcome
(`[orch]`, `[kb]`, `[infer]`, `[docs]`).

### Parallel by default

Multi-file audit, multi-repo synthesis, multi-paper analysis, benchmark sweeps — all fan
out to parallel Task agents or multiple Worker processes. Sequential is the exception, not
the default.

### Maestro budget discipline

When interacting with hosted Claude (via Claude Code or this chat): arrive with context
gathered, questions sharpened, and the task well-specified. Don't use Maestro tokens to
read files Claude can't cache; pull excerpts and paste. Don't use Maestro tokens for
well-specified implementation; hand the spec to a Worker.

### Writing style for docs

Prose over bullet-heavy dumps for anything a human will read. Markdown files in this repo
communicate reasoning, not just facts. Lists where they clarify; paragraphs where they
reason. Claude Code: when generating docs, follow this style.

## Session Startup Protocol

When Claude Code opens a session in this repo:

1. Read CLAUDE.md (this file) fully.
2. Read VISION.md if the task touches project direction.
3. Read ROADMAP.md if the task relates to phased work.
4. Read ARCHITECTURE.md if the task involves components or interfaces.
5. Check DECISIONS.md for any decision relevant to the task.
6. For any non-trivial change: propose a plan before editing. Use the `[Plan]` → `[Act]`
   workflow pattern.
7. After 3–4 file edits, post a checkpoint summary.
8. Before long runs: smoke-test on a sample.
9. On session end or significant pauses: commit with a clean message.

## Maestro/Worker Protocol (summary, full version in docs/)

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
- Run `pytest`, `ruff`, `python` (in linus env), `git add`, `git commit`
- Read-only git: `git status`, `git log`, `git diff`, `git branch`
- `ls`, `cat`, `grep`, `tree`, `wc`, `head`, `tail`

### Require confirmation (show command, wait for OK)

- Any `git push`, `git rebase`, `git reset --hard`
- File writes outside `src/ benchmarks/ experiments/ docs/` (including repo root edits)
- Shell commands touching `~/` outside the Linus tree
- Any network operation (curl, wget, pip install, brew install, ollama pull)
- Running a model against full KnowledgeBase corpus (must smoke-test first)

### Forbidden (do not propose)

- `rm -rf` on anything under `~/`
- Edits to `modules/KnowledgeBase/` (it's a submodule — work happens in the KnowledgeBase repo)
- Edits to `repos/*` (reference-only clones)
- Writing to `~/.ssh`, `~/.aws`, or any credentials path
- `sudo` anything
- Modifying `.gitignore` or `.gitmodules` without explicit request

See SAFETY.md for autonomy tier graduation and the full policy.

## Known Library Quirks

*(This section grows over time. Append entries as issues are resolved.)*

**Ollama via conda is CPU-only.** Use the Homebrew install (`brew install ollama` +
`brew services start ollama`). The conda build lacks Metal acceleration. Inherited from
KnowledgeBase.

**Ollama port conflict recovery.** If a stale `ollama serve` from a conda shell holds
port 11434, `brew services` fails with `fork/exec`. Fix:
`pkill -f 'ollama serve' && brew services restart ollama`. Inherited from KnowledgeBase.

**Optional Ollama speed env vars**: `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`.
Set before `brew services start`.

**pypdf decompression limit**: disable with `sys.maxsize`, NOT `0` or `2**63`.
Inherited from KnowledgeBase.

**SQLite large writes**: batch commits in chunks of 100–500 rows. Single transactions
on 10k+ rows fail. Inherited from KnowledgeBase.

---

*This file is the contract between Dan and Claude (Maestro), and any Worker operating in the
Linus repo. Update it when conventions change. Don't silently drift.*
