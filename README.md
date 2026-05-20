# Linus

_A personal AI orchestration backend for Apple Silicon. Private, local, modular — Claude-equivalent capabilities for
scientific and software work, fully under your control. Named after Linus Pauling and Linus Torvalds._

**Status:** v0.5.0 public reveal — 2026-05-25 (Agora hackathon). **Linked projects:** debuting alongside
[KnowledgeBase](https://github.com/dbrowneup/KnowledgeBase) (paper corpus + RAG + KG pipeline; the data substrate) and
Archimedes (q-fin strategy engine; the entrepreneurial sibling — link TBD).

> _Logo placeholder: a carbon atom — sp³ orbitals, the substrate of biochemistry. Asset to land before reveal._

> **Reveal context (May 2026).** Linus is the orchestration + memory substrate behind
> [Archimedes](https://github.com/hackagora/archimedes-arcadia), a research-grounded
> quantitative-finance strategy agent revealing alongside it for the Agora Agents
> Hackathon. The two repos share a lineage: Linus is the personal research-intelligence
> stack; Archimedes is what that stack looks like specialized to one domain, made
> externally verifiable, and shipped on-chain. Linus itself remains the personal
> substrate described below — the deliberate stance, not an accident of stage.

## What this is

Linus is an OpenAI- and Anthropic-compatible AI backend that runs on a MacBook Pro, exposes domain-specific tools backed
by a personal knowledge base, coordinates local models in parallel, enforces sandbox policy regardless of front-end, and
is designed to evolve toward fine-tuned models trained on its owner's own data. It is not a replacement for hosted
frontier models — hosted Claude plus the user remains the **Maestro** for complex reasoning and architecture, while
Linus is the **Worker** orchestra that executes under that direction and serves its owner directly when private or
offline operation is needed. The author, a working scientist, built Linus to make his own research and software work
better; the orchestration layer is what accrues value across every harness, every paper read, every synthesis written.

## Architecture in one paragraph

Any OpenAI- or Anthropic-compatible client (VS Code, Claude Code, LM Studio, openclaw, future native apps) talks HTTP to
the Linus orchestration backend — a FastAPI server housing the router, an MCP-style tool registry (fastmcp substrate),
the sandbox, the five-layer memory pillar, the session store, and an append-only audit log. From there, requests fan
out across three subsystems: **Inference** (Ollama and `mlx-lm` today; `pmetal serve` and `mlx-flash` for
larger-than-RAM models on the roadmap), **Knowledge** (the [KnowledgeBase](modules/KnowledgeBase) submodule's metadata
DB, SPECTER2 embeddings, similarity graph, and knowledge graph, exposed through a read-only adapter), and **Training**
(pmetal LoRA/QLoRA and `mlx-lm` fine-tuning, Phase 6+). The split is deliberate: harnesses come and go, but the
orchestration backend is where Dan-specific intelligence accrues. See [ARCHITECTURE.md](ARCHITECTURE.md) for the full
diagram and component-by-component breakdown.

## What's shipped (v0.5.0)

- **OpenAI-compatible** chat completions endpoint (`/v1/chat/completions`) with streaming, tool calls, and a
  multi-iteration tool loop.
- **Anthropic-compatible** messages endpoint (`/v1/messages`) — same backend, two API shapes (DEC-0056).
- **Sessions** — server-side conversation persistence (SQLite WAL), session-id passthrough, history-on-resume.
- **Tool registry** — MCP-style decorators on the fastmcp substrate (DEC-0045); grounding-gate-ready outputs via
  `rigor.py` (Phase 2c).
- **paper-qa Phase 2c integration** — citation-grounded paper-corpus Q&A, routed through Linus tools, backed by local
  Ollama (no hosted API).
- **KnowledgeBase integration** — read-only adapter for KB's clustered corpus and knowledge graph; Streamlit pages for
  paper graph, cluster explorer, KG render, and paper-qa.
- **Memory pillars** — five-layer architecture (DEC-0028): intra-step latent, within-session scratchpad, cross-session
  episodic (SQLite + content hashes + git), investigation memory, and semantic knowledge (KnowledgeBase).
- **Sandbox** — path-validating `SandboxFS` enforcing the SAFETY.md Tier 0/1 contract on every filesystem and shell
  call.
- **Hermetic test suite** — 341 tests, ~6s, runs without any external service.

## Hardware and setup

Designed for Apple Silicon (M1/M2/M3, Metal acceleration). The reference machine is a 32 GB M1 Max. The setup story is
short:

```bash
# 1. Clone with the KnowledgeBase submodule
git clone --recurse-submodules git@github.com:dbrowneup/Linus.git
cd Linus

# 2. Conda environment (Python 3.12)
conda env create -f environment.yml
conda activate linus

# 3. Editable install
pip install -e .

# 4. Ollama (Homebrew — the conda build is CPU-only)
brew install ollama
brew services start ollama
ollama pull qwen3:8b        # current Worker model; see CLAUDE.md "Maestro/Worker discipline"

# 5. Launch the Linus backend
linus-serve                  # entry point per pyproject.toml; or: uvicorn linus.server:app --reload

# 6. (Optional) Streamlit UI for KB pages
streamlit run src/linus/app/main.py
```

Full environment notes, optional Ollama performance env vars, and known library quirks live in [CLAUDE.md](CLAUDE.md).

## License

This project is released under the MIT License (declared in [`pyproject.toml`](pyproject.toml); a standalone `LICENSE`
file is planned for the reveal). Notable third-party integrations:

- The **KnowledgeBase** submodule is itself MIT but bundles [PyMuPDF](https://github.com/pymupdf/PyMuPDF) (AGPL-3.0-or-
  later) — see [KB's README](modules/KnowledgeBase/README.md#license) for the AGPL-inheritance details. If you
  redistribute Linus _with_ KB, AGPL terms govern that combined distribution; Linus core alone (without KB) is MIT-only.

## Project layout (high-level)

```
Linus/
├── src/linus/              # The product (orchestration backend, knowledge integration,
│                           #              memory, sandbox, tools, Streamlit UI, tests)
├── modules/KnowledgeBase/  # Paper-analysis pipeline (tracked submodule)
├── repos/                  # Reference clones (gitignored, read-only study material)
├── docs/                   # ADRs, specs, syntheses, paper-notes, repo-notes, session summaries
├── benchmarks/             # Dan-tasks v0 + dated result JSON
├── experiments/            # Throwaway scripts, ablations
├── environment.yml         # Conda env spec
└── pyproject.toml          # Python package config + entry points
```

Top-level docs (CLAUDE.md, VISION.md, ARCHITECTURE.md, ROADMAP.md, SAFETY.md, DECISIONS.md, GLOSSARY.md, BRANCHING.md)
sit at the repo root. CLAUDE.md is the operational contract for sessions in this repo and carries the per-document
conventions used across `docs/`.

## Where to go next

- Architecture deep-dive: [ARCHITECTURE.md](ARCHITECTURE.md)
- Vision and philosophy: [VISION.md](VISION.md)
- Phased plan: [ROADMAP.md](ROADMAP.md)
- Decisions log: [DECISIONS.md](DECISIONS.md) (per-file ADRs under [`docs/adr/`](docs/adr/))
- Safety policy and autonomy tiers: [SAFETY.md](SAFETY.md)
- Branch and PR workflow: [BRANCHING.md](BRANCHING.md)
- Glossary: [GLOSSARY.md](GLOSSARY.md)

## Acknowledgements

Named after **Linus Pauling** (1901–1994; scientist, humanitarian, two-time unshared Nobel laureate) and **Linus
Torvalds** (1969–; engineer, open-source advocate; creator of Linux and Git) — both Oregonians; Linus is what their
force-multiplier looks like in software. The symbol is a carbon atom: sp³ orbitals, the foundation of biochemistry, and
a nice conceptual hook for what happens when carbon-based life meets silicon-based intelligence. See
[VISION.md](VISION.md) for the extended rationale.

Thanks also to Anthropic for Claude (a key part of the Maestro that makes this project possible), Apple's MLX team for
making Apple Silicon a real ML platform, and the authors of every repo in `repos/` whose ideas inform this work — see
[`docs/repo-notes/`](docs/repo-notes/) for per-repo credit.
