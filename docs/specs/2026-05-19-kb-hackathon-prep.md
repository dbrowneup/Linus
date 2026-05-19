# 2026-05-19 — KB hackathon prep (v0.5.0 reveal arc)

**Author:** Maestro (Claude Opus 4.7) — Dan reviewing.
**Status:** draft (proposed).
**Target ship date:** 2026-05-25 (Agora hackathon coordinated reveal).

---

## Context

Per the [Agora hackathon memory](../../.claude/projects/-Users-dbrowne-Desktop-Programming-GitHub-Linus/memory/hackathon_2026_05_25_agora.md), 2026-05-25 is a
coordinated public reveal of three projects:

1. **Archimedes** — public release (Dan-owned narrative).
2. **Linus** — first public visibility (this repo).
3. **KnowledgeBase** — first public visibility (submodule at `modules/KnowledgeBase/`, upstream `dbrowneup/KnowledgeBase`).

This spec covers KB-side work + Linus-side KB integration to land before reveal. pmetal-side work is
descoped from this spec — it's blocked on the missing Metal Toolchain (`xcodebuild -downloadComponent
MetalToolchain`) and tracked separately.

Dan strategic decisions captured 2026-05-19:

- **License stance: Keep PyMuPDF (AGPL), document AGPL loudly in KB README.** No migration to pypdf. Reasoning:
  KB had concrete reasons to migrate FROM pypdf TO PyMuPDF (extraction-quality regression on pypdf); reversing
  that for license aesthetics is the wrong tradeoff. Loud AGPL documentation is the honest path.
- **paper-qa Phase 2c integration: in v0.5.0.** Adds citation-grounded paper-corpus Q&A as a marquee KB
  capability at the reveal. Aggressive but doable in 6 days alongside everything else.

## Work items

Naming convention: `KB-<N>` for KB-submodule work, `LX-<N>` for Linus-side work, `SUB-<N>` for the submodule
pin bump.

### KB-1 — Public README polish + AGPL documentation (KB submodule)

**Target:** `modules/KnowledgeBase/README.md`. Branch on `master` against `dbrowneup/KnowledgeBase`.

Deliverable: rewrite README's top 80 lines to be reveal-ready. New shape:

- One-paragraph TL;DR ("What is this?") that someone landing on the GitHub cold can read.
- Demo image or animated GIF (placeholder OK for first PR; Dan can swap real asset later).
- Architecture overview — 3-4 sentences on what the pipeline does + what artifacts it produces.
- Hardware requirements (existing content, condensed).
- Setup (existing content, condensed).
- **New: License section** prominently documenting PyMuPDF (AGPL) inheritance. Must include: (a) what AGPL
  means for downstream users; (b) link to PyMuPDF's license text; (c) a "License compatibility" note that
  states KB is itself MIT but bundles AGPL deps, so the effective distribution license is AGPL-3.0-or-later.
- Pipeline phases summary (existing content, cleaned up).
- Streamlit app section (preserved).

Out of scope: code changes, dependency changes, CI changes.

### KB-2 — Smoke-test confirmation (no-code)

**Target:** confirm the KB pipeline still runs end-to-end against the configured corpus. No code change;
output is a short note in `modules/KnowledgeBase/docs/2026-05-19-smoke-confirmation.md` (new file) recording:
last-known-good extraction count, clustering output existence, knowledge-graph artifact existence, Streamlit
app launching cleanly.

Dan-owned: he runs the pipeline against his real corpus and provides the numbers. Maestro can do everything
else if Dan provides one-line "I ran X, got Y" status.

### LX-1 — paper-qa Phase 2c integration (Linus side)

**Spec reference:** `docs/specs/kb/paper-qa-substrate-integration.md` (already exists, 105 lines).

**Target:** `src/linus/knowledge/paperqa.py` (new module). Branch on `main` against `dbrowneup/Linus`.

Deliverable (per the existing spec):

- New module `src/linus/knowledge/paperqa.py` that wraps paper-qa's `PaperSearch`, `GatherEvidence`,
  `GenerateAnswer`, `Complete/Reset` tools as Linus-registered tools via `linus.tools.registry`.
- LiteLLM adapter configured to hit Ollama at `http://localhost:11434` (no hosted API).
- Tool registration: each of the 4 paper-qa tools becomes a Linus tool with name `paperqa.search`,
  `paperqa.gather_evidence`, `paperqa.answer`, `paperqa.reset`.
- Citation grounding: paper-qa's citation objects mapped to KB's provenance model per the spec's
  Claim-typing layer section.
- Hermetic tests at `src/linus/tests/test_paperqa.py` covering: tool registration; argument validation;
  citation→provenance mapping; error paths (paper-qa unavailable, no papers indexed). Mocks for LiteLLM
  to avoid Ollama dependency in hermetic suite.
- Integration test at `tests/test_paperqa_integration.py` requiring Ollama + at least one indexed paper;
  validates end-to-end query → answer with citations.
- Dependency added to `pyproject.toml`: `paper-qa>=5.0` (or whatever the current published version is).

Open question for Dan during build: paper-qa pins its own model preferences. We override via LiteLLM to point
at qwen3:8b. If quality is poor on qwen3, we surface this as a separate issue post-build — do NOT block the
PR on it.

### LX-2 — Streamlit page (optional, post-paper-qa PR)

If LX-1 ships in good shape, add `src/linus/app/pages/7_paper_qa.py` exposing a question box → answer +
citation list UI. Wires through to the `paperqa.*` tools via the Linus server endpoint. Hermetic-untestable
(Streamlit UI); manual smoke test only.

**Decision: include if budget permits, defer if any LX-1 friction arises.**

### SUB-1 — Linus submodule pin bump

**Target:** `modules/KnowledgeBase` pointer in `.gitmodules`-anchored submodule. Branch on `main`.

After KB-1 merges into KB master, bump the Linus submodule pin to the merged commit. Small dedicated PR
(only the submodule pointer + a one-line commit message). Verification: `git submodule update --remote
--merge` clean, hermetic suite still passes (it doesn't depend on submodule state, but verify).

## Ship sequence

1. **Now (2026-05-19, this session)**: dispatch KB-1 + LX-1 in parallel as agents in isolated worktrees.
   KB-1's worktree branches against `dbrowneup/KnowledgeBase` master; LX-1's against `dbrowneup/Linus` main.
2. **2026-05-19/20**: review + merge KB-1 → KB master. Open SUB-1 PR on Linus, merge.
3. **2026-05-20/21**: review + merge LX-1 → Linus main. Optional: dispatch LX-2 agent for the Streamlit
   page if budget remains.
4. **2026-05-21/22**: Dan runs KB-2 smoke test against his real corpus, reports numbers, agent writes the
   smoke-confirmation note.
5. **2026-05-23/24**: final polish pass, dry-run the reveal narrative end-to-end (Linus landing → demo →
   KB pages → paper-qa query → cited answer). Last-mile bug fixes.
6. **2026-05-25**: hackathon. Splash.

## Out of scope (post-reveal)

- pmetal v0.5.0 binary rebuild (blocked on Metal Toolchain install).
- KB pipeline performance optimizations.
- Streamlit page redesigns beyond LX-2.
- New visualizations.
- Migration to pypdf or any other PDF backend.
- Anything that doesn't trace to "this makes the reveal stronger" per the hackathon memory.

## Success criteria

A reviewer landing on `github.com/dbrowneup/Linus`, `github.com/dbrowneup/KnowledgeBase`, and Archimedes's repo
cold on 2026-05-25 can:

- Read each README and understand what the project is in under 60 seconds.
- See the three projects' relationship to each other clearly.
- Find no embarrassing half-finished features in the default branch.
- Run a hermetic test suite (`pytest src/linus/tests/`) on Linus and see it pass.
- Issue a paper-qa query via the Linus server and get a citation-grounded answer (this is the marquee).
