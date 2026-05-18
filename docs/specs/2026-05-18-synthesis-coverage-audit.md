# Synthesis coverage audit (2026-05-18)

## Executive summary

Catalyzed by Dan's observation that [`docs/repo-notes/prologue.md`](../repo-notes/prologue.md) — a memory-architecture
reference repo (compression-ladder + visibility-boundaries + FPEF gate discipline) — has never been folded into
[`memory-synthesis.md`](../syntheses/memory-synthesis.md) or
[`repo-clusters/g4-memory.md`](../syntheses/repo-clusters/g4-memory.md), this audit asked the same question of every
other note in the corpus.

- **Notes audited:** 256 total (129 repo-notes, 127 paper-notes).
- **Completely unreferenced (no link, no backtick mention, no path mention in any synthesis):** 20 (11 repo-notes,
  9 paper-notes).
- **Bare-mention-only (no explicit link/backtick form, but discussed by name in at least one synthesis):** 41
  (39 repo-notes, 2 paper-notes). Spot-checks show these are real substantive references — bare mention is the dominant
  style of citation in syntheses, not a gap class.
- **CONFIRMED GAPs (substantive note + identifiable synthesis home + zero presence in that home):** 14 (10 repo-notes,
  4 paper-notes).
- **EXPECTED ABSENCE (INDEX records the note as Uncovered, or the assignment column is blank with a Watch/Ignore
  verdict):** 6 (1 repo-note, 5 paper-notes — primarily KB-foundation papers per the paper INDEX preface; plus
  `project-nomad` which is intentionally uncovered per the repo INDEX preface).

The prologue case validates the method: prologue.md is correctly identified as a CONFIRMED GAP with
`memory-synthesis.md` + `g4-memory.md` as the recommended targets, exactly matching Dan's observation.

## Methodology

The audit is a directed-grep problem run from a single Python script (operating on the worktree at base SHA
`d410c83`):

1. **Enumerate notes.** All `*.md` files under `docs/repo-notes/` and `docs/paper-notes/`, excluding `INDEX.md`.
2. **Enumerate synthesis files.** All `*.md` under `docs/syntheses/` and `docs/syntheses/repo-clusters/` (27 files:
   15 thematic + 12 cluster).
3. **For each note, search every synthesis for any reference to its basename.** Three classifications:
   - **Well-referenced** — explicit markdown link, backtick-quoted stem, or path-component mention
     (`repo-notes/foo.md`, `\`foo\``, `[foo]`, `(foo)`). The "explicit" forms are how the doc-type conventions in
     CLAUDE.md (paper-note + repo-note "Connections" sections) prescribe linking.
   - **Bare-mention-only** — case-insensitive word-boundary match of the stem (`finch`, `prologue`) but no explicit
     link/backtick form. Spot-checks confirm these are usually substantive references; bare mention is the prevailing
     prose style in syntheses.
   - **Completely unreferenced** — zero matches across all 27 syntheses.
4. **Cross-reference against the INDEX files.** [`repo-notes/INDEX.md`](../repo-notes/INDEX.md) and
   [`paper-notes/INDEX.md`](../paper-notes/INDEX.md) name the canonical synthesis home for each note. Notes flagged as
   "Uncovered" in INDEX (or in the INDEX's documented exclusion list — the pre-fan-out core and `project-nomad`) are
   EXPECTED ABSENCE; notes with an INDEX-named home but zero presence in that named synthesis are CONFIRMED GAP.

**Known limitations.** (a) Bare-mention detection on short common stems (`link`, `engram`, `remember`) could
false-positive, but spot-checks of the 39 bare-mention-only repo-notes show each maps to a sensible synthesis discussion
in the right cluster, so this is not driving the gap count. (b) A note could be referenced under an alternative name
that isn't its basename — `jan` references could appear as `janhq` or `menloresearch`; this was checked manually
during INDEX cross-reference for the CONFIRMED-GAP candidates. (c) The audit does not score reference _quality_; a note
mentioned once in passing counts the same as one with two paragraphs of analysis. The fold-in plan below makes judgment
calls on what level of depth each target merits.

## CONFIRMED GAPs

### Repo-notes

| Note                          | Verdict | INDEX-named home                                                | Rationale                                                                                                                                                                                                                                                            |
| ----------------------------- | ------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prologue.md`                 | Study   | memory                                                          | Compression-ladder (WORKING → PROJECT → OVERVIEW → CORE with confidence thresholds) and visibility-boundary (private / inspectable / shared / canonical) model are directly portable to Layer C consolidation and Layer D investigation memory (DEC-0028, DEC-0052). Catalyzing example for this audit. |
| `vellum-assistant.md`         | Study   | memory                                                          | Personal-assistant architecture with per-user identity + privacy-conscious local-or-managed model. Directly relevant to Linus's memory pillar and Phase 2 MVP user model.                                                                                                                                |
| `AgentPrometheus.md`          | Study   | agentic-systems                                                 | "The system executes. The AI consults." runtime model — deterministic operational work outside the LLM. Closely parallel to Linus orchestration discipline; missing from the agentic-systems thematic discussion.                                                                                       |
| `swarms.md`                   | Study   | agentic-systems                                                 | Enterprise-grade multi-agent architecture catalog (sequential / concurrent / hierarchical / debate / council / mixture-of-agents / planner-worker / heavy-swarm). Direct vocabulary reference for Phase 3 agent-spawner shape (DEC-0050).                                                                |
| `awesome-ai-agent-papers.md`  | Watch   | g11-agent-frameworks (cluster); no thematic                     | Active VoltAgent-curated 370-paper reading list across multi-agent / memory-RAG / eval-observability / agent-tooling / agent-security — five buckets that mirror Linus's own threads. Should be cited as an active ingestion source in g11.                                                              |
| `cs249r_book.md`              | Study   | infra-foundations                                               | Harvard CS249R textbook + 20-module from-scratch ML framework (TinyTorch). Direct curricular reference for Linus's infra-foundations narrative and the learn-by-building stance.                                                                                                                          |
| `jan.md`                      | Watch   | g7-harnesses (cluster); no thematic                             | Local-first chat harness (janhq/jan, formerly Menlo Research) — direct adjacent reference in the harnesses cluster but missing from g7's narrative. Watch-verdict so a brief mention suffices.                                                                                                              |
| `local-whisper.md`            | Adapt   | infra-foundations, native-low-bit-apple-silicon                 | Swift menu-bar STT app powered by WhisperKit (CoreML on Apple Silicon). Adapt-verdict means this is a high-priority gap; should be folded into both the infra and native-low-bit syntheses as a worked example of fully-local Apple-Silicon speech.                                                          |
| `MoneyPrinterV2.md`           | Watch   | none (INDEX cluster + thematic both blank)                      | INDEX leaves no home; verdict is Watch. Lower-priority but the local-Ollama-direct pattern + provider-abstraction discipline could earn a sentence in agentic-systems or skills-and-practices. Tier-3.                                                                                                       |
| `algebrica.md`                | Study   | none (INDEX cluster + thematic both blank)                      | Free university-level math KB (Markdown + LaTeX + SVG + semantic JSON). No obvious thematic home — closest fits: llm-wiki-synthesis (publishing pattern) or skills-and-practices (knowledge-base authoring). INDEX gap.                                                                                       |

### Paper-notes

| Note                          | Title                                                                            | INDEX-named home(s)                                                          | Rationale                                                                                                                                                                                                                                                            |
| ----------------------------- | -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `2603.25097v1.md`             | ElephantBroker: Knowledge-Grounded Cognitive Runtime                             | memory, agentic-systems, safety-alignment-privacy                            | INDEX names THREE thematic homes, all of which currently contain zero references to either the basename or the title. Neo4j + Qdrant + Cognee cognitive runtime with eleven-dimension scoring + guard pipeline — directly relevant to memory pillar and safety surface. |
| `2510.20844v3.md`             | TrustResearcher: Multi-Agent Knowledge-Grounded Research Ideation                | llms-in-science, agentic-systems                                             | Both named homes contain zero references. Multi-agent science-ideation work; directly in scope for two thematic syntheses.                                                                                                                                                 |
| `2210.02747.md`               | Flow Matching for Generative Modeling (canonical primary source)                 | infra-foundations                                                            | infra-foundations cites the Holderrieth & Erives flow-matching textbook (2506.02070v3) extensively but never links the canonical primary-source paper. One-line addition to the existing flow-matching subsection in infra-foundations.                                  |
| `2509.11420v1.md`             | Trading-R1: Single-model RL distillation of multi-agent trading                  | agentic-systems                                                              | Mentioned by title in agentic-systems with a context-papers PDF link, but the paper-note itself (`paper-notes/2509.11420v1.md`) is not linked from the Connections-style citation. Light gap — replace bare title with explicit paper-note link.                          |

## EXPECTED ABSENCE

### Repo-notes (1)

- **`project-nomad.md`** — repo INDEX preface explicitly states "uncovered by either substrate. It lives at the
  per-repo-note + landscape level only — by design, since it is a component catalog reference rather than a code
  integration target." Verdict is _Ignore (as a product); borrow components individually._ No action required.

### Paper-notes (5)

Per the paper INDEX preface, "A small number of papers (KB-foundation papers — embeddings, keyphrase extraction,
KG-survey adjuncts, the Horiike hypercube paper) are not yet absorbed into any thematic synthesis. They show up as
**Uncovered** in the table and live only at the per-paper-note + landscape level for now."

- `2208.07262v1.md` — Retrieval-efficiency trade-off of Unsupervised Keyword Extraction (KB-foundation: keyphrase
  extraction). _Uncovered_ in INDEX.
- `2401.00422v3.md` — Curse of Dimensionality / Distance Concentration (KB-foundation: embedding-space behavior).
  _Uncovered_ in INDEX.
- `2406.17557v2.md` — FineWeb Datasets (KB-foundation: training-data quality reference). _Uncovered_ in INDEX.
- `2408.08073v2.md` — Sentence Embeddings from Pretrained Transformer Models (KB-foundation: embeddings). _Uncovered_
  in INDEX.
- `s41019-017-0055-z.md` — Keyphrase Extraction Using Knowledge Graphs (KB-foundation: keyphrase + KG adjunct).
  _Uncovered_ in INDEX.
- `Horiike-Orthogonal-projections-of-hypercubes-2025-Physical-Review-E.md` — Hypercube projections (manifold-ML thread,
  the Horiike paper explicitly named in the INDEX preface). _Uncovered_ in INDEX.
- `2602.03082v1.md` — Geometry-Preserving Neural Architectures on Manifolds with Boundary. Bare-mention only in
  infra-foundations; INDEX records this as _Uncovered_. Sibling reference to JPmHC in the manifold-ML thread.

(Total in EXPECTED ABSENCE is 6 unique papers as called out in the executive summary; `2602.03082v1` is bare-mention
only rather than strictly unreferenced, so it does not show up in the "completely unreferenced" count but is in this
list for completeness.)

## Fold-in plan

The plan is tiered by relevance × verdict × INDEX-named-home strength.

### Tier 1 — high-relevance, Adapt or Study verdict, explicitly INDEX-named target

These are gaps a reviewer would call "should obviously be there." Each is a one-session Worker task.

| #   | Source                | Target synthesis                                                                                            | Action                                                                                                                                                                                  | Est. effort |
| --- | --------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| T1  | `prologue.md`         | `memory-synthesis.md` + `repo-clusters/g4-memory.md`                                                        | Add a Prologue subsection covering the compression-ladder (with confidence thresholds) and visibility-boundary model; connect to DEC-0028 Layer C consolidation and DEC-0052 Layer D access vocabulary. | ~45 min     |
| T2  | `vellum-assistant.md` | `memory-synthesis.md`                                                                                       | Add a paragraph on the personal-assistant per-user identity model + privacy-conscious local-or-managed model; cite as a Linus Phase 2 MVP user-model reference.                          | ~30 min     |
| T3  | `local-whisper.md`    | `native-low-bit-apple-silicon-synthesis.md` + `infra-foundations-synthesis.md`                              | Add as worked example of fully-local Apple-Silicon STT (WhisperKit + CoreML); cross-link in infra-foundations as a portable component for Linus's voice surface.                          | ~45 min     |
| T4  | `2603.25097v1.md`     | `memory-synthesis.md` + `agentic-systems-synthesis.md` + `safety-alignment-privacy-synthesis.md`            | Three-target fold-in (each gets a paragraph): memory = cognitive-runtime substrate; agentic = eleven-dimension scoring rubric; safety = guard-pipeline pattern. INDEX names all three.    | ~60 min     |
| T5  | `2510.20844v3.md`     | `llms-in-science-synthesis.md` + `agentic-systems-synthesis.md`                                             | Two-target fold-in: science = multi-agent research-ideation example; agentic = multi-agent collaboration pattern with knowledge grounding. INDEX names both.                              | ~45 min     |
| T6  | `AgentPrometheus.md`  | `agentic-systems-synthesis.md`                                                                              | Add as worked example of the "system executes / AI consults" runtime model; cite as Linus-aligned orchestration discipline.                                                                | ~30 min     |
| T7  | `swarms.md`           | `agentic-systems-synthesis.md`                                                                              | Add as multi-agent-architecture catalog reference (sequential / concurrent / hierarchical / debate / council / mixture / planner-worker / heavy-swarm); cite as Phase 3 spawner vocabulary. | ~30 min     |

### Tier 2 — moderate relevance, identifiable target, Study or Watch verdict

| #   | Source                          | Target synthesis                                                | Action                                                                                                                                                                          | Est. effort |
| --- | ------------------------------- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| T8  | `cs249r_book.md`                | `infra-foundations-synthesis.md`                                | One-paragraph mention as curricular reference for the ML-systems learn-by-building stance (TinyTorch).                                                                          | ~20 min     |
| T9  | `awesome-ai-agent-papers.md`    | `repo-clusters/g11-agent-frameworks.md`                         | One-paragraph mention as an active ingestion source for the five-bucket reading-list discipline.                                                                                | ~20 min     |
| T10 | `2210.02747.md`                 | `infra-foundations-synthesis.md`                                | One-line: add an explicit paper-note link to the canonical Flow Matching primary source alongside the existing 2506.02070v3 textbook citation.                                  | ~10 min     |
| T11 | `2509.11420v1.md`               | `agentic-systems-synthesis.md`                                  | Replace the bare title mention with an explicit paper-note link (`paper-notes/2509.11420v1.md`) for Connections-style discoverability.                                          | ~10 min     |

### Tier 3 — nice-to-have, weaker INDEX signal, low-priority verdict

| #   | Source                | Target synthesis                                                                            | Action                                                                                                                                                                                                                                                                                            | Est. effort |
| --- | --------------------- | ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| T12 | `jan.md`              | `repo-clusters/g7-harnesses.md`                                                             | One-paragraph mention as an adjacent local-first chat harness (janhq); Watch-verdict so brevity is fine.                                                                                                                                                                                            | ~15 min     |
| T13 | `MoneyPrinterV2.md`   | (unassigned; candidate: `skills-and-practices-synthesis.md` or `agentic-systems-synthesis.md`) | Decide on a home, then add a one-sentence cross-reference (local-Ollama-direct + provider-abstraction patterns). May also be deferred — the Watch verdict justifies non-inclusion.                                                                                                                  | ~20 min     |
| T14 | `algebrica.md`        | (unassigned; candidates: `llm-wiki-synthesis.md` or `skills-and-practices-synthesis.md`)    | Decide on a home for the knowledge-base authoring + LaTeX + SVG publishing pattern; one-paragraph mention.                                                                                                                                                                                          | ~20 min     |

### Fan-out spec scaffold (Tier 1)

Tier-1 work fans out cleanly along synthesis-target boundaries. Suggested allocation for a parallel Worker dispatch
(7 task slots; estimate ~4 hours total wall-time with parallelism, ~6 hours serial):

```
Bin A — memory-synthesis.md + g4-memory.md   → T1 (prologue), T2 (vellum-assistant), T4-mem (ElephantBroker memory paragraph)
Bin B — agentic-systems-synthesis.md          → T4-agentic (ElephantBroker agentic paragraph), T5-agentic (TrustResearcher agentic paragraph), T6 (AgentPrometheus), T7 (swarms)
Bin C — safety-alignment-privacy-synthesis.md → T4-safety (ElephantBroker safety paragraph)
Bin D — llms-in-science-synthesis.md          → T5-science (TrustResearcher science paragraph)
Bin E — infra-foundations + native-low-bit    → T3 (local-whisper, two-synthesis fold-in)
```

Each Bin is one Worker. Bin B is the heaviest (4 fold-ins on one synthesis); the others are 1–3 paragraph-scale edits.
T4 and T5 each require cross-binning to preserve consistency, so the dispatching Maestro should brief Bins A/B/C
together on T4 phrasing and Bins B/D together on T5 phrasing to avoid divergent framings of the same paper across
syntheses.

Per CLAUDE.md worktree fan-out discipline, parallel dispatch MUST use isolated worktrees; tier-1 is large enough to
justify that overhead. Bin-level start/end timestamps in each Worker's report per the Measure-don't-just-estimate
convention.

### Tier 2 / Tier 3 — sequential fold-in by Maestro

Tier 2 and Tier 3 are small enough (10-20 min each) that batching them into a single Maestro session with file-level
partitioning is more efficient than a worktree fan-out. Recommended: one session, sequential edits, single
consolidating commit.

### Triage caveat: bare-mention-only notes are NOT in the fold-in plan

The 39 bare-mention-only repo-notes and 2 bare-mention-only paper-notes (39 + 2 = 41 total) are NOT treated as gaps;
spot-checks show they are real substantive references that simply don't use the explicit markdown-link form. A separate
follow-up could normalize the citation style across syntheses (convert bare mentions to backtick + path-link form for
Connections-style discoverability), but that is a doc-hygiene pass, not a coverage gap. Out of scope for this audit.

## References

- Catalyzing example: prologue.md — Dan's observation that this memory-architecture reference was never folded into the
  memory-synthesis or g4-memory cluster despite being directly relevant to DEC-0028 (memory pillar) and DEC-0052
  (Layer D investigation memory). Audit method validates this case correctly as a Tier-1 CONFIRMED GAP with the exact
  fold-in targets Dan identified.
- INDEX preface clauses: [`docs/repo-notes/INDEX.md`](../repo-notes/INDEX.md) (project-nomad and the pre-fan-out core
  carve-outs) and [`docs/paper-notes/INDEX.md`](../paper-notes/INDEX.md) (KB-foundation paper carve-out).
- Doc-type convention reference: CLAUDE.md "Doc-type conventions" section (paper-note Connections discipline,
  repo-note Connections discipline).
