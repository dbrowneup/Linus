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

### `landscapes/` — Integrated maps

Higher-altitude documents that integrate the per-item notes and the per-theme syntheses into a single picture.

- [total-landscape.md](landscapes/total-landscape.md) — master integration map crossing syntheses against architecture, roadmap, and open questions.
- [synthesis-landscape.md](landscapes/synthesis-landscape.md) — cross-synthesis structural map showing overlaps, tensions, and hub clusters across the 24 synthesis docs.
- [paper-landscape.md](landscapes/paper-landscape.md) and [repo-landscape.md](landscapes/repo-landscape.md) — deprecated stubs retained for link integrity, now pointing to index docs and synthesis-first landscapes.

### `paper-notes/` — Per-paper study notes

One page per paper under `context/papers/`. Same shape as repo-notes: what it argues, what is load-bearing for Linus,
what to skip. File names mirror the source identifiers (arXiv ids, bioRxiv DOIs, ScienceDirect PIIs). Currently ~80
notes spanning LLM foundations, agents, biological foundation models, evaluation, alignment, and the
humans/teams/performance literature.

### `protocols/` — Operating protocols

- [maestro-worker-protocol.md](protocols/maestro-worker-protocol.md) — the full version of the Maestro (Dan + hosted Claude) ↔ Worker (local models)
  delegation contract summarized in the repo-root [CLAUDE.md](../CLAUDE.md).

### `questions/` — Question logs

- [top-questions.md](questions/top-questions.md) — the prioritized working set of unresolved questions, tiered by how much each answer changes the next concrete action.
- [open-questions.md](questions/open-questions.md) — the full unresolved backlog, organized as a verbose per-source archive.
- [answered-questions.md](questions/answered-questions.md) — the archive of resolved planning questions, with linked ADR/spec pointers and session-log context.

### `repo-notes/` — Per-repo study notes

One page per cloned reference repo under `repos/`. Each note summarizes what the repo is, what is liftable into Linus,
what to ignore, and any quirks worth remembering. Used as raw material for the syntheses. Currently ~80 notes covering
Apple-Silicon inference work, agentic harnesses, MCP servers, memory systems, scientific agents, biology models, and
related ecosystems.

### `session-summaries` – Key session recaps

- [2026-05-03-memory-pillar-session-summary.md](session-summaries/2026-05-03-memory-pillar-session-summary.md) — Recaps the follow-up planning session that translated the Garrison memory thesis into Linus architecture via an 11-paper fan-out, a dedicated memory synthesis, 17 resolved memory-pillar questions, and ratifying ADR/spec outputs.
- [2026-05-03-paper-notes-session-summary.md](session-summaries/2026-05-03-paper-notes-session-summary.md) — Recaps the multi-wave paper-note fan-out across the expanded corpus, including pre-triage decisions, per-batch execution checkpoints, and same-session group syntheses with wave-level roll-up deferred.
- [2026-05-03-top-questions-resolution-session-summary.md](session-summaries/2026-05-03-top-questions-resolution-session-summary.md) — Recaps the end-to-end top-questions resolution session where Tier 0-3 items were converted into committed decisions, roadmap/spec deltas, and a concrete Worker-executable planning artifact.
- [2026-05-04-fan-out-session-summary.md](session-summaries/2026-05-04-fan-out-session-summary.md) — Recaps the Section 7 G1-G10 repo-note fan-out run, including shared pre-fan-out infrastructure commits, per-group outcomes, and the highest-impact implementation patterns surfaced for Linus.
- [2026-05-05-landscape-rollup-session-summary.md](session-summaries/2026-05-05-landscape-rollup-session-summary.md) — Recaps the post-fan-out landscape reorganization session that swept open questions, built flat index docs, rewrote the two canonical landscape files, deprecated legacy landscape docs, and appended the resulting execution plan in planning-update-spec Section 11.
- [2026-05-05-planning-update-session-summary.md](session-summaries/2026-05-05-planning-update-session-summary.md) — Recaps the context-ingestion session that produced five new paper notes, three new thematic syntheses, a preliminary planning-update draft, and a late-stage path-recovery fix that reapplied landscape updates to main-repo docs.

### `specs/` — Implementable specs and session artifacts

Working specs handed off to the next implementation step (e.g. [planning-update-spec.md](specs/planning-update-spec.md), [memory-architecture.md](specs/memory-architecture.md)) and
session summaries from large fan-out events (e.g. [2026-05-04-fan-out-session-summary.md](session-summaries/2026-05-04-fan-out-session-summary.md)). Living documents — updated
when execution surfaces gaps.

### `syntheses/` — Cross-cutting roll-ups by theme

Theme-level digests built by reading across many repo-notes and paper-notes at once. The flat files here are
topic-oriented (agentic systems, biological foundation models, function annotation, generative biology, infra
foundations, LLM wikis, LLMs in science, memory, native low-bit Apple Silicon, safety/alignment/privacy, security,
skills/practices, humans-and-teams). The nested [`repo-clusters/`](syntheses/repo-clusters/) directory holds the G1–G10
group syntheses produced during the 2026-05-04 fan-out — each `gN-<slug>.md` covers one cluster of related repos
(Apple-Silicon, wiki engines, wiki patterns, memory, graph tools, MCP tools, harnesses, scientific agents, biology,
finance).