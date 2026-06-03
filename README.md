# Linus

_A personal AI orchestration backend for Apple Silicon. Private, local, modular — Claude-equivalent capabilities for
scientific and software work, fully under your control. Named after Linus Pauling and Linus Torvalds._

**Status:** v0.5.0 — the local orchestration substrate, tagged 2026-06-02 (first revealed at the Agora hackathon, 2026-05-25). Debuting alongside
[KnowledgeBase](https://github.com/dbrowneup/KnowledgeBase) (the data substrate) and
[Archimedes](https://github.com/hackagora/archimedes-arcadia) (q-fin strategy engine — Linus specialized to one
domain, made externally verifiable, and shipped on-chain).

> _Logo placeholder: a carbon atom — sp³ orbitals, the substrate of biochemistry. Asset to land before reveal._

## TL;DR

OpenAI- and Anthropic-compatible HTTP backend that runs on a MacBook, exposes domain-specific tools backed by a
personal knowledge base, coordinates local models in parallel, enforces sandbox policy regardless of front-end, and is
designed to evolve toward fine-tuned models trained on its owner's data. Not a hosted-Claude replacement — Linus is the
**Worker** that executes under hosted Claude + you (the **Maestro**), and serves you directly when private or offline
operation is needed. The orchestration layer is what accrues value across every harness, every paper read, every
synthesis written.

## Run it locally

```bash
git clone --recurse-submodules git@github.com:dbrowneup/Linus.git && cd Linus
conda env create -f environment.yml && conda activate linus && pip install -e .
brew install ollama && brew services start ollama && ollama pull qwen3:8b
linus-serve                                     # backend on http://localhost:8000
streamlit run src/linus/app/main.py             # optional KB-consuming UI
```

Designed for Apple Silicon (M1/M2/M3 with Metal acceleration). Reference machine: 32 GB M1 Max. Full env notes, Ollama
performance env vars, and known library quirks live in [CLAUDE.md](CLAUDE.md).

## What's shipped (v0.5.0)

The local orchestration **substrate**: OpenAI + Anthropic chat-completions endpoints (streaming + tool calls,
multi-iteration tool loop) · server-side session persistence (SQLite WAL) · fastmcp-based MCP tool registry (DEC-0045)
· **KnowledgeBase** read-only adapter feeding Streamlit pages (paper graph, cluster explorer, KG render, search) · a
**grounding/rigor gate** (DEC-0059), loud `/healthz` degradation (DEC-0060), and per-tool **network policy** (DEC-0061)
· five-layer **memory pillar** (DEC-0028; intra-step latent → within-session scratchpad → cross-session episodic →
investigation memory → KnowledgeBase semantic) · path-validating **sandbox** enforcing the SAFETY.md Tier 0/1 contract
· hermetic test suite, 704 tests in ~6s. **paper-qa** ships as an optional "few named papers" deep-dive tool — the
corpus-scale, citation-grounded RAG marquee is the **v0.6.0** deliverable, a Linus-native full-text-chunk substrate
(see the [evaluation](docs/specs/2026-06-02-paperqa-evaluation-and-linus-native-rag.md)). Component-by-component
breakdown in [ARCHITECTURE.md](ARCHITECTURE.md); per-phase status in [ROADMAP.md](ROADMAP.md).

## Documentation map

| If you want to…                          | Read                                                |
| ---------------------------------------- | --------------------------------------------------- |
| Architecture deep-dive                   | [ARCHITECTURE.md](ARCHITECTURE.md)                  |
| Vision and philosophy                    | [VISION.md](VISION.md)                              |
| Phased roadmap (v0 → v8)                 | [ROADMAP.md](ROADMAP.md)                            |
| Decisions log + per-file ADRs            | [DECISIONS.md](DECISIONS.md), [`docs/adr/`](docs/adr/) |
| Safety policy + autonomy tiers           | [SAFETY.md](SAFETY.md)                              |
| Branch + PR workflow                     | [BRANCHING.md](BRANCHING.md)                        |
| Glossary                                 | [GLOSSARY.md](GLOSSARY.md)                          |
| Project context for a Claude Code session | [CLAUDE.md](CLAUDE.md)                              |

## Project layout

```
Linus/
├── src/linus/              # The product (FastAPI backend, KB integration, memory, sandbox, tools, Streamlit UI, tests)
├── modules/KnowledgeBase/  # Paper-analysis pipeline (tracked submodule)
├── repos/                  # Reference clones (gitignored, read-only study material)
├── docs/                   # ADRs, specs, syntheses, paper-notes, repo-notes, session summaries
├── benchmarks/             # Dan-tasks v0 + dated result JSON
├── experiments/            # Throwaway scripts, ablations
└── environment.yml · pyproject.toml
```

## License

MIT, per [LICENSE](LICENSE). The bundled [`modules/KnowledgeBase/`](modules/KnowledgeBase) submodule is itself MIT but
pulls in [PyMuPDF](https://github.com/pymupdf/PyMuPDF) (AGPL-3.0-or-later); if you redistribute Linus _with_ KB, AGPL
governs the combined distribution. Linus core alone is MIT-only. See
[KB's LICENSE](modules/KnowledgeBase/LICENSE) for the AGPL-inheritance details.

## Acknowledgements

Named after **Linus Pauling** (1901–1994; scientist, humanitarian, two-time unshared Nobel laureate) and **Linus
Torvalds** (1969–; engineer, open-source advocate; creator of Linux and Git) — both Oregonians. Symbol: a carbon atom
(sp³ orbitals, the foundation of biochemistry; a nice hook for what happens when carbon-based life meets silicon-based
intelligence). Extended rationale in [VISION.md](VISION.md). Per-repo credit for everything in [`repos/`](repos/) lives
in [`docs/repo-notes/`](docs/repo-notes/). Thanks to Anthropic for Claude, Apple's MLX team for making Apple Silicon a
real ML platform, and the authors of every paper and project that informs this work.
