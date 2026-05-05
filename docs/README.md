# docs/

Long-form writing for Linus: decision records, study notes on the cloned-repo and paper corpus, syntheses that roll
those notes up by theme, landscapes that integrate everything, open-question logs, planning specs, and the
Maestro/Worker protocol. Source code lives under `src/`; this tree is where reasoning is captured.

The intended reading order for a newcomer is roughly: top-level [CLAUDE.md](../CLAUDE.md) and [VISION.md](../VISION.md)
first, then [landscapes/total-landscape.md](landscapes/total-landscape.md) for the integrated picture, then dive into
whichever subtree matches the current task.

## Top-level files

- [curation-protocol.md](protocols/curation-protocol.md) — policy for adding, pruning, and archiving material in `repos/`,
  `context/`, and `docs/`. Adopted in DEC-0025.
- [curation-log.md](curation-log.md) — running memory of what was added, removed, or archived under that protocol, with
  dates and rationale.

## Subdirectories

### `adr/` — Architecture Decision Records

One markdown file per decision, numbered `NNNN-<slug>.md` and matching the `DEC-NNNN` ids indexed in the repo-root
[DECISIONS.md](../DECISIONS.md). Each ADR captures context, the decision, and consequences for a single architectural
choice (project name, orchestration backend as the product, KnowledgeBase as a submodule, OpenAI-compatible protocol,
pmetal evaluation, branching model, MCP as the extensibility substrate, and so on). Currently 44 entries.

### `repo-notes/` — Per-repo study notes

One page per cloned reference repo under `repos/`. Each note summarizes what the repo is, what is liftable into Linus,
what to ignore, and any quirks worth remembering. Used as raw material for the syntheses. Currently ~80 notes covering
Apple-Silicon inference work, agentic harnesses, MCP servers, memory systems, scientific agents, biology models, and
related ecosystems.

### `paper-notes/` — Per-paper study notes

One page per paper under `context/papers/`. Same shape as repo-notes: what it argues, what is load-bearing for Linus,
what to skip. File names mirror the source identifiers (arXiv ids, bioRxiv DOIs, ScienceDirect PIIs). Currently ~80
notes spanning LLM foundations, agents, biological foundation models, evaluation, alignment, and the
humans/teams/performance literature.

### `syntheses/` — Cross-cutting roll-ups by theme

Theme-level digests built by reading across many repo-notes and paper-notes at once. The flat files here are
topic-oriented (agentic systems, biological foundation models, function annotation, generative biology, infra
foundations, LLM wikis, LLMs in science, memory, native low-bit Apple Silicon, safety/alignment/privacy, security,
skills/practices, humans-and-teams). The nested [`repo-clusters/`](syntheses/repo-clusters/) directory holds the G1–G10
group syntheses produced during the 2026-05-04 fan-out — each `gN-<slug>.md` covers one cluster of related repos
(Apple-Silicon, wiki engines, wiki patterns, memory, graph tools, MCP tools, harnesses, scientific agents, biology,
finance).

### `landscapes/` — Integrated maps

Higher-altitude documents that integrate the per-item notes and the per-theme syntheses into a single picture.

- `total-landscape.md` — master integration map across all four input streams (repos, papers, decisions, questions).
- `repo-landscape.md`, `paper-landscape.md`, `synthesis-landscape.md` — single-stream views feeding into the total.

### `questions/` — Open-question log

- `open-questions.md` — the full backlog of unresolved questions.
- `top-questions.md` — the prioritized subset, tiered by how much each answer changes the next concrete action, with a
  resolution log appended as questions are closed.

### `specs/` — Implementable specs and session artifacts

Working specs handed off to the next implementation step (e.g. `planning-update-spec.md`, `memory-architecture.md`) and
session summaries from large fan-out events (e.g. `fan-out-session-summary-2026-05-04.md`). Living documents — updated
when execution surfaces gaps.

### `protocols/` — Operating protocols

- `maestro-worker-protocol.md` — the full version of the Maestro (Dan + hosted Claude) ↔ Worker (local models)
  delegation contract summarized in the repo-root [CLAUDE.md](../CLAUDE.md).
