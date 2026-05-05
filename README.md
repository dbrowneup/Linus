# Linus

A personal AI orchestration backend for Apple Silicon.

Named after Linus Pauling and Linus Torvalds. Runs locally. Respects your data. Gets better at your work over time.

## What this is

Linus is an OpenAI-compatible AI backend that runs on a MacBook Pro, exposes domain-specific tools backed by a personal
knowledge base, coordinates multiple local models in parallel, enforces sandbox policy regardless of front-end, and is
designed to evolve toward fine-tuned models trained on its owner's own data.

It's not a replacement for hosted frontier models — hosted Claude plus owner remains the primary Maestro for complex
reasoning and architecture. Linus is the orchestra that Claude plus owner conducts, and the assistant that serves its
owner directly when private or offline operation is needed.

This is a personal project, not a product. There is no company, no users to serve, no deadline. The code, decisions, and
documentation exist to make the author's own work easier and to be a pleasure to build.

## Status

**Phase 1 — Recon and Baselines** (in progress). Phase 0 closed. Repo synthesis notes largely complete; pmetal
evaluation underway (built from source, smoke tests pass). See [ROADMAP.md](ROADMAP.md) for the phased plan.

## Principles

Applied in every design decision:

1. **Question every requirement.** From _The Algorithm_ by Jon McNeill.
2. **Delete every possible step.** Err aggressive.
3. **Simplify.** Only after deletion.
4. **Accelerate cycle time.** Speed is information.
5. **Automate.** Last, not first.

Plus:

- **Maestro/Worker discipline.** Hosted Claude plus owner plans and directs; local models execute.
- **Evidence beats intuition.** Set a metric, set a goal, devise tests, iterate.
- **Parallel by default.** Multi-file and multi-subtask work fans out.

See [VISION.md](VISION.md) for the full framing.

## Architecture at a glance

```
  FRONT-ENDS (interchangeable)
    VS Code · LM Studio · openclaw · native Linus app (future)
        │
        │  OpenAI-compatible HTTP
        ▼
  LINUS ORCHESTRATION LAYER  ← the product
    router · tool registry · agent spawner · sandbox · audit
        │
    ┌───┼───┐
    ▼   ▼   ▼
  INFERENCE   KNOWLEDGE   TRAINING
  Ollama      KnowledgeBase pmetal
  pmetal srv  (submodule)   mlx-lm ft
  mlx-lm
  mlx-flash
```

See [ARCHITECTURE.md](ARCHITECTURE.md).

## Repo layout

```
Linus/
├── CLAUDE.md              # Primary context for Claude Code sessions
├── VISION.md              # Project vision, philosophy, namesake rationale
├── ARCHITECTURE.md        # Layered design and component boundaries
├── ROADMAP.md             # Phased plan with target durations
├── SAFETY.md              # Sandbox policy and autonomy tiers
├── DECISIONS.md           # ADR pointer + index (per-file ADRs in docs/adr/)
├── GLOSSARY.md            # Terms and component names
├── README.md              # This file
├── environment.yml        # Conda environment spec
├── pyproject.toml         # Python package config
├── src/linus/             # Linus orchestration backend (the product)
├── modules/KnowledgeBase/ # Dan's knowledge repo (submodule)
├── repos/                 # Reference clones (gitignored)
├── context/               # Personal context for Maestro (gitignored)
├── benchmarks/            # Evaluation harnesses and results
├── experiments/           # Throwaway scripts and ablations
└── docs/                  # Long-form synthesis
```

## Quick start

```bash
# 1. Clone with submodules
git clone --recurse-submodules git@github.com:dbrowneup/Linus.git
cd Linus

# 2. Set up the conda env
conda env create -f environment.yml
conda activate linus

# 3. Editable install
pip install -e .

# 4. Verify
python -c "import linus; print(linus.__version__)"

# 5. Start Ollama and pull the worker model
brew services start ollama
ollama pull qwen2.5-coder:7b
ollama pull mistral:7b-instruct

# 6. (Phase 2+) Launch the Linus backend
# python -m linus.server  # not yet implemented

# 7. (Phase 2+) Launch the chat UI
# streamlit run src/linus/app/main.py  # not yet implemented
```

## For Claude Code sessions

Start every session by reading [CLAUDE.md](CLAUDE.md). It contains the behavioral contract, coding conventions, sandbox
policy, and session protocol.

Key habits:

- Plan before editing for anything non-trivial
- Smoke-test on a sample before full runs
- Checkpoint summaries every 3–4 file edits
- Atomic commits with descriptive messages
- Append Known Library Quirks the session they're resolved
- Apply The Algorithm check before adding components

## Namesake

The project is named after two Linuses, both Oregonians:

**Linus Pauling** (1901–1994) — Two-time Nobel laureate (Chemistry 1954, Peace 1963). Self-taught basement-lab hacker
who became the founder of molecular biology, author of _The Nature of the Chemical Bond_, and organizer of the petition
that led to the 1963 nuclear test ban treaty.

**Linus Torvalds** (1969–) — Creator of Linux and Git. Principled engineer whose work underpins most of the world's
software infrastructure.

Logo: a carbon atom. Pauling's early work was on carbon's tetravalent sp³ hybridization; carbon is the foundation of
biochemistry — the field of the project's owner, a PhD biochemist now working in genomics and metagenomics — and the
silicon/carbon interface is a nice conceptual hook for what Linus does.

See [VISION.md](VISION.md) for the extended rationale.

## License

TBD. Default intent: permissive open source for the Linus code itself, with acknowledgment that Linus depends on
submodules (KnowledgeBase) and reference repos under their own licenses.

## Acknowledgments

- Anthropic for Claude, a key part of the Maestro that makes this project possible
- Apple's MLX team for making Apple Silicon a real ML platform
- Every repo in `repos/` and their authors — see `docs/repo-notes/` (Phase 1+) for per-repo credit
- Linus Pauling and Linus Torvalds, for the legacies this project tries, in its small way, to honor
