# Notes Consistency Fan-Out Spec

**Date:** 2026-05-08 **Status:** spec authored; canary pending. **Owner:** Maestro (Dan + Claude Code).

**Related:** [`CLAUDE.md`](../../CLAUDE.md) §Doc-type conventions; §Measure, don't just estimate; §Agent fan-out:
probe permissions first. [`docs/paper-notes/INDEX.md`](../paper-notes/INDEX.md).
[`docs/repo-notes/INDEX.md`](../repo-notes/INDEX.md).

---

## Goal

Bring all 195 per-source notes — 98 in [`docs/paper-notes/`](../paper-notes/) and 97 in
[`docs/repo-notes/`](../repo-notes/) — into uniform structure, terminology, and Linus-current framing per the
"Doc-type conventions" section in [`CLAUDE.md`](../../CLAUDE.md). The notes are good; they need alignment and
freshening against the current decision and spec corpus (DEC-0001..0054, current `docs/specs/`, current phase
scoping), not rewriting.

## Scope

In scope:

- All `*.md` files in `docs/paper-notes/` excluding `INDEX.md` and `README.md` (98 files).
- All `*.md` files in `docs/repo-notes/` excluding `INDEX.md` and `README.md` (97 files).
- For each note: structural alignment, link/anchor fixes, phase/DEC mapping in "What's reusable in Linus",
  open-questions sequential renumbering where Policy A deletions left gaps.

Out of scope (do not touch):

- `docs/syntheses/`, `docs/audits/`, `docs/landscapes/`, `docs/questions/`, `docs/specs/` (other than this file),
  `docs/protocols/`, `docs/cybersecurity-notes/`, `docs/session-summaries/`, `docs/curation-log.md`.
- The submodule at [`modules/KnowledgeBase/`](../../modules/KnowledgeBase/).
- The reference clones under [`repos/`](../../repos/) (read-only for verification, never edited).
- Core docs (CLAUDE.md, VISION.md, ARCHITECTURE.md, ROADMAP.md, SAFETY.md, DECISIONS.md, GLOSSARY.md, README.md).

## Bin assignments

13 topic-coherent bins. Every file appears in exactly one bin. Stems below are filename without `.md` suffix and
without path; agent prompt resolves them to full paths.

| Bin | Theme | Count | File stems |
|-----|-------|-------|-----------|
| B1 | Apple Silicon / low-bit / inference | 19 | 2310.11453v1, 2312.11514v3, 2402.17764v1, 2411.04965v1, 2502.11880v1, 2504.12285v2, 2504.18415v2, 2510.13998v1, 2508.15734v1, bonsai-1-bit-8b-whitepaper, bonsai-ternary-8b-whitepaper, flash_moe, ANE, BitNet, Bonsai-demo, flash-moe, mlx-flash, pmetal, QiMeng-cpu-v1 |
| B2 | Memory / scratchpad / TTT / CoT / RNN / KV / transformer arch (papers) | 25 | NIPS-2017-attention-is-all-you-need-Paper, 1910.07467, 2002.05202, 2102.05095v4, 2104.09864, 2203.15556v1, 2205.11916v4, 2303.12712v5, 2305.13245, 2305.15408v5, 2306.12456v2, 2310.07923v5, 2311.12351, 2407.21783v3, 2410.01201v3, 2411.07279v2, 2412.04604v2, 2412.06769v3, 2412.17794v1, 2502.16721v1, 2508.09834, bandaru_transformer_design_guide_pt2_modern_architecture, jytan_2025_crystallization_of_transformer_architectures, mughal_context_window_management, raschka_2025_big_llm_architecture_comparison |
| B3 | Memory / context / persistence (repos) | 9 | agentmemory, anamnesis, codebase-memory-mcp, engram, memex, omega-memory, openaugi, prompt-vault, remember |
| B4 | Agentic systems / orchestration (papers) | 7 | 2026.02.09.704801v1, 2304.05332v1, 2503.19065v1, 2506.13023v1, 2510.09244v1, 2511.02824v2, 2603.24629v1 |
| B5 | LLM Wiki engines + patterns (g2 + g3) | 18 | AgenticResearchWiki, OmegaWiki, TheKnowledge, agentic-wiki-builder, atomic-knowledge, beever-atlas, link, llm-research-wiki, llm-wikidata, llmbase, llmwiki, llmwiki-cli, obsidian-llm-wiki-local, swarmvault, synthadoc, wikidesk, wikiloom, wikimind |
| B6 | Bio foundation models + genomics (papers) | 9 | 2025.07.20.665723v2, 2025.07.21.665832v2, 2025.09.12.675911v1, gkaf836, s41467-025-60872-5, s41586-025-10014-0, s41586-026-10176-5, s41592-025-02776-2, s42256-025-01044-4 |
| B7 | Generative biology + function annotation/discovery (papers) | 12 | 1-s2.0-S0022283626000513-main, 2024.12.19.629561v2, 2025.03.02.641084v1, 2025.04.19.649272v1, 2025.05.13.653614v2, 2026.03.19.712954v1, 2026.04.22.720063v1, 2306.03809v1, 2505.23579v2, 2604.05181v1, rocks-et-al-2026-dual-encoder-contrastive-learning-accelerates-enzyme-discovery, s41592-026-03030-z |
| B8 | Bio repos (g9) + sci-agents (g8) | 18 | 2407.10362v3, 2503.00096v3, Bacformer, BioReason, BixBench, LAB-Bench, Sketch2Simulation, aviary, bioSkills, claude-prism, deepsems, ether0, finch, ibmdotcom-tutorials, ldp, paper-qa, robin, scientific-agent-skills |
| B9 | Finance / quant (g10 + papers) | 11 | 2402.03755v1, 2412.03220, 2412.20138v7, 2509.09995v3, 2511.20099v4, 2511.20100v1, OpenBB, QuantAgent, TradingAgents, dexter, nixtla |
| B10 | MCP tools (g6) + harness repos (g7) + analogues | 27 | WeKnora, claude-squad, claude-task-master, codebuff, codesight, dlt, dspy, extractthinker, fastmcp, gptme, gravityfile, huginn, k-dense-byok, lmnr, markdownify-mcp, ontomics, openrouter-skills, origin, promptfoo, pydantic-ai, python-sdk, qmd, rendergit, semanticworkbench, vanna, vectorless, workgraph |
| B11 | Graph tools (g5) + KG papers | 8 | 2003.02320v6, OptimusKG, hyalo, infranodus, infranodus-skills, keppi, py3plex, s41019-017-0055-z |
| B12 | Skills / practices / humans-teams / cog-sci / LLMs-in-science | 14 | PIIS0896627324008080, agent-skills-for-context-engineering, autoresearch, autoresearch-mlx, binz-et-al-2025-how-should-the-advancement-of-large-language-models-affect-the-practice-of-science, claude-cycles, claw-code, claw-code-local, cline, harvey-et-al-2023-the-dynamics-of-team-learning-harmony-and-rhythm-in-teamwork-arrangements-for-innovation, nihms-2096004, openclaw, science.adt7790, superpowers |
| B13 | Safety / alignment / privacy / values + long-tail / uncovered / KB-foundation | 18 | 0549, 2208.07262v1, 2401.00422v3, 2406.17557v2, 2408.08073v2, 2410.11381, 2506.02070v3, 2506.05007v1, 2511.09057v3, 2602.16800v2, 2602.18308v2, 2604.27269v1, Horiike-Orthogonal projections of hypercubes-2025-Physical Review E copy, Values_Paper__camera_ready_COLM_, d41586-026-00974-2, project-nomad, s41586-025-08600-3, science.aea6792 |

**Total: 195 files. Sum across bins matches.**

For each bin, a stem from `docs/paper-notes/` is a paper-note; a stem from `docs/repo-notes/` is a repo-note. Bin
B1 mixes both (the BitNet thread papers + the apple-silicon repos). Bins B3, B5, B10, B11 are repo-only; B2, B4,
B6, B7, B9, B12 mix paper-notes with related repos when applicable.

## Per-agent allowed tools (allowlist)

The fan-out is structurally simple — agents read the assigned files, edit in place, and report. The allowlist
below is what each agent receives in its prompt. Anything outside the allowlist is forbidden.

- **Read** — on the agent's assigned bin files (paper-notes paths and repo-notes paths listed in the prompt).
- **Read** — on the corresponding source material:
  - For paper-notes: the PDF at `context/papers/<paper-id>.pdf` if it exists. Read renders PDFs.
  - For repo-notes: the clone at `repos/<repo-name>/` for verifying claims against actual code/README.
- **Read** — on `docs/adr/` for DEC ID lookups when claims need a citation.
- **Read** — on this spec doc and on auto-loaded `CLAUDE.md`.
- **Edit** / **Write** — on the assigned bin's note files only (no other paths).
- **Glob** / **Grep** — restricted to the agent's bin file paths and the allowed source-material paths above.
- **Bash** — `git add` and `git commit` only, restricted to the worktree. No other Bash. No network. No
  spawning sub-agents.

Forbidden (do not propose):

- Reading any other notes outside the assigned bin (other paper-notes / repo-notes).
- Reading `docs/syntheses/`, `docs/audits/`, `docs/landscapes/`, `docs/questions/`, `docs/protocols/`,
  `docs/session-summaries/`, `docs/cybersecurity-notes/`, `docs/curation-log.md`.
- Reading the submodule `modules/KnowledgeBase/`.
- Editing anything outside the assigned bin's note files.
- `git push`, `gh`, `git checkout`, `git merge`, `git rebase`, branch-switching, force-anything.

Cross-bin consistency is Maestro's job at consolidation, not the agent's.

## Per-note rubric

For each note in the bin, the agent verifies and minimally edits to match the canonical shape per
[`CLAUDE.md`](../../CLAUDE.md) §Doc-type conventions. Concretely:

1. **Frontmatter (paper-notes only).** Ensure YAML frontmatter contains `title`, `source`, `authors`,
   `affiliation`, `date`, `pdf`, `tags`. Add missing fields where derivable from existing prose. Don't fabricate.
2. **H1 title** matches paper title (paper-notes) or `# <repo-name> (\`<owner/repo>\`)` (repo-notes).
3. **Section headings** match the canonical order exactly. Reorder if needed; do not rename or invent.
4. **"What's reusable in Linus"** — each point maps to a phase (Phase 1..8) and references a DEC or spec where
   applicable. Stale phase claims (e.g., "Phase 3 spec for X" when X is now Phase 2) get updated. If the agent
   cannot verify a phase or DEC mapping from `docs/adr/`, leave the prose as-is and flag the note in the report.
5. **"Connections"** — relative markdown links only. Verify each link's target exists (Glob/Read on the path).
   Fix broken links if the target moved within the agent's allowed paths; flag if the target moved outside.
6. **"Open questions for Dan"** — numbered sequentially with no gaps. Renumber to close gaps left by prior
   Policy A deletions. Partial-resolved items use the canonical format
   `_Partially resolved (DEC-NNNN, see [answered-questions.md](../questions/answered-questions.md)): nuance._`.
7. **Repo-note recommendation verdict** — one of: **Integrate**, **Study**, **Adapt**, **Watch**, **Ignore**.
   If a note uses different vocabulary (e.g. "evaluate", "consider"), normalize to the closest canonical verdict.
8. **Prose style** — per CLAUDE.md §Writing style for docs: prose over bullet dumps. Don't rewrite prose for
   style alone; only adjust if a section is bullet-heavy where it should reason.
9. **No vestigial headers** (`# Group N Questions for Dan — Extract` etc.) — delete if present.

## Hard constraints

- **No invented technical claims.** If a "reusable in Linus" claim is unverifiable from the source material
  (paper PDF or repo code), flag the note for Maestro and leave the prose untouched.
- **No semantic-meaning changes** to any reusable claim. Restructure / standardize / link-fix only.
- **Stay strictly inside the assigned bin's file set** plus the permitted source material.
- **Atomic per-note commits** within the worktree branch. One commit per note touched. Commit message:
  `[notes-consistency] <note-stem>: <what changed>`.
- **Emit the standardized summary report verbatim** at the end of the agent's response.

## Standardized summary report

Every agent emits this YAML block verbatim at the end of its response. Variation in report shape is what made
prior fan-outs hard to consolidate; this template removes that surface area entirely.

```yaml
# Notes-Consistency Fan-Out — Bin Report
bin_id: B<N>
notes_total: <int>
notes_touched: <int>
notes_unchanged: <int>
notes_flagged: <int>
start_iso: 2026-MM-DDTHH:MM:SSZ
end_iso:   2026-MM-DDTHH:MM:SSZ
elapsed_seconds: <int>

per_note:
  - path: docs/paper-notes/<id>.md           # or docs/repo-notes/<name>.md
    status: touched | unchanged | flagged
    fixes_applied:
      - frontmatter: <description or "none">
      - sections: <description or "none">
      - phase_mapping: <description or "none">
      - dec_links: <description or "none">
      - links: <description or "none">
      - prose: <description or "none">
      - open_questions_renumbering: <description or "none">
      - verdict_normalization: <description or "none">  # repo-notes only
    flag_reason: <empty if not flagged; one-sentence reason if flagged>
  # ... one entry per note in the bin

cross_bin_observations: |
  Free-text section. Things this agent noticed that aren't in scope for this bin
  but Maestro should know about (broken links pointing outside bin, stale
  references in adjacent files, etc.). Keep terse. Empty string if nothing.

estimate_vs_actual: |
  Estimated: <maestro estimate in minutes from spec>
  Actual:    <elapsed_seconds / 60 minutes>
  Variance note: <one sentence if >20% off; empty otherwise>
```

## Canary procedure (L4)

Before the parallel fan-out, one foreground (non-worktree) canary agent runs **Bin B13** as the canary. B13 is
the long-tail / safety / KB-foundation bin; it has the most heterogeneous content, so if the rubric works on B13
it will work on the topically-tighter bins. Maestro reads the canary's report and diff, refines this spec if
needed, and only then dispatches the remaining 12 bins in parallel via worktree mode.

If the canary blocks at any allowlisted-tool step (e.g., a Read on `repos/<name>/` is denied, or `git commit` in
worktree fails), Maestro fixes the permission/spec issue before the parallel fan-out — never debug 12 stuck
agents.

## Branch / PR strategy

Single base branch `agent/notes-consistency-sweep` off the current branch
(`agent/notes-cleanup-fanout`). Each parallel agent works in a worktree off this base. Maestro consolidates by
cherry-picking each worktree's per-note commits onto the base branch in deterministic bin order
(B1, B2, …, B13) at the end. **Single PR** with per-bin commit groups inside.

When PR #24 (the prior `agent/notes-cleanup-fanout` content) merges to main, this branch will rebase cleanly.

## Estimates and time tracking

Per the new "Measure, don't just estimate" CLAUDE.md convention:

- **Maestro estimate.** ~3 hours wall time total: spec ~30 min (already drafted), canary ~30 min, parallel
  fan-out ~60-90 min bounded by slowest bin (parallel max), consolidation ~30 min, PR ~15 min. Anchored
  conservatively given the 195-file scope and L4 lessons from the prior fan-out.
- **Per-bin estimate carried in agent prompt.** ~10 minutes per bin for B3/B4/B6/B7/B9/B11/B12 (≤12 files);
  ~15-20 minutes for B1/B2/B5/B8/B10/B13 (≥14 files).
- **Maestro fills the Status section below at consolidation** with measured wall time and variance note.

## Status (filled at execution)

- 2026-05-08: spec authored.
- 2026-05-08: canary on B13 — _pending_.
- 2026-05-08: parallel fan-out on B1-B12 — _pending_.
- 2026-05-08: consolidation + PR — _pending_.
- 2026-05-08: measured wall time — _pending_.

---

## Agent prompt template (reference)

Maestro composes per-bin prompts from this template, substituting `<BIN_ID>`, `<BIN_THEME>`, `<FILE_LIST>`, and
the per-bin estimate. The template is here for traceability; it's not invoked directly.

```
You are running as a fan-out Worker for the Linus notes-consistency sweep. Read this spec first:
docs/specs/notes-consistency-fanout.md (and the auto-loaded CLAUDE.md §Doc-type conventions).

Your bin: <BIN_ID> — <BIN_THEME>.
Files in your bin (filename stems; resolve to docs/paper-notes/<stem>.md or docs/repo-notes/<stem>.md based on
which directory contains it):
<FILE_LIST>

Per-bin estimate: <N> minutes.

For each file, apply the per-note rubric (spec §Per-note rubric). Honor all hard constraints (spec §Hard
constraints) and stay within the allowlisted tools (spec §Per-agent allowed tools). For each note touched,
make an atomic commit in your worktree with message
`[notes-consistency] <note-stem>: <what changed>`.

When done, emit the standardized summary report YAML block (spec §Standardized summary report) verbatim at the
end of your response. Record start_iso, end_iso, elapsed_seconds accurately.
```
