# PR 30 cleanup spec — coverage + staleness + Bin A/B repos

**Status:** active **Date:** 2026-05-10 **Branch:** `agent/pr30-cleanup` (base SHA `af3eddbd4ecece86eeae648aac7822569900e7ba`).
**Owner:** Maestro (Dan + Claude Code).

**Origin:** Companion to the 2026-05-09 / 2026-05-10 context fold-in arc (PR #28 + #29). Closes the residual gaps
identified by the coverage-sweep and core-doc-staleness-sweep agents (this session, 2026-05-10) and executes the
Bin A + Bin B repo additions deferred from the Canteen blog landscape note.

**Related:**

- [`2026-05-09-context-foldin-fanout.md`](2026-05-09-context-foldin-fanout.md) — the fan-out spec PR #28/#29
  descended from. This spec closes its residual scope.
- [`qimeng-category-promotion.md`](qimeng-category-promotion.md) — upstream owner of the QiMeng / idea→reality
  thread, now substantially executed.
- [`../../context/notes/canteen_blog_landscape_2026-05.md`](../../context/notes/canteen_blog_landscape_2026-05.md)
  — practitioner-claim corpus + Bin A/B/C tiered repo candidates. Bin C (synthesis addenda) executed 2026-05-10;
  Bin A + B deferred to this spec.

---

## Tasks at a glance

| Tier | Family                                                                  | Count   | Output                                        | Gating                                                              |
| ---- | ----------------------------------------------------------------------- | ------- | --------------------------------------------- | ------------------------------------------------------------------- |
| 1    | Promote inline-cited papers + Letta-paired paper to paper-notes         | 4       | `docs/paper-notes/<stem>.md` × 4              | task 1.4 needs arxiv PDF download (Dan-authorized 2026-05-10)        |
| 2    | Investigate + embed orphan pics                                         | 4       | inline embeds + cross-refs                    | gated on figuring out what happened with Bonsai pics                |
| 3    | Bin A — Tier 1 repo clones + notes                                      | 5       | clone + `docs/repo-notes/<repo>.md` × 5       | **authorized 2026-05-10**; URLs pinned below                        |
| 4    | Bin B — Tier 2 repo clones + notes                                      | 3       | clone + `docs/repo-notes/<repo>.md` × 3       | **authorized 2026-05-10**; URLs pinned below                        |
| 5    | Core-doc staleness — single Worker pass                                 | 9 files | edits across CLAUDE/README/VISION/etc.        | gated on Tier 1–4 so counts are stable                              |
| 6    | INDEX backfill for new paper-notes + repo-notes                         | 2 files | INDEX entries added                           | gated on Tier 1+3+4                                                  |
| 7    | Curation-log entries for Tier 3+4 clones                                | 1 file  | `docs/curation-log.md` updated                | gated on Tier 3+4                                                    |
| 10   | Landscape + top-questions accuracy audit (load all syntheses at once)   | 3 files | refresh `total-landscape.md` / `synthesis-landscape.md` / `top-questions.md` | gated on all prior tiers                          |

PR 30 total: ~28 sub-tasks (4 paper-notes + 4 pic embeds + 8 repo-note tasks + 9 core-doc files + 2 INDEX +
1 curation-log + 3 landscape/top-questions = 31 distinct file outputs).

**Deferred to PR 31** (separate branch + separate ADRs):

| Tier | Family                                          | Status                                       |
| ---- | ----------------------------------------------- | -------------------------------------------- |
| 8    | Bulk-rename files with spaces — ADR candidate   | **approved 2026-05-10**; PR 31 scope         |
| 9    | Git LFS for `context/` — ADR candidate          | **approved 2026-05-10**; PR 31 scope         |

---

## Tier 1 — Promote inline-cited papers + Letta-paired paper to paper-notes (4 tasks)

The first three papers were intentionally deferred to inline citation during the original fold-in (per Dan's
feedback on options A/B/C/D), but the corpus is mature enough now that promoting them to full paper-notes closes
a "surprised-we-missed-this" gap and gives them durable cross-reference handles. Task 1.4 was added 2026-05-10
when Dan authorized the Letta clone (Tier 3.1) — Letta descends architecturally from MemGPT, so the pair gets
the hybrid-filename treatment.

| Task | PDF                                                   | Target paper-note                       | Synthesis home(s)                          |
| ---- | ----------------------------------------------------- | --------------------------------------- | ------------------------------------------ |
| 1.1  | `context/papers/2509.11420v1.pdf`                     | `docs/paper-notes/2509.11420v1.md`      | agentic-systems (extends TradingAgents)    |
| 1.2  | `context/papers/2602.03082v1.pdf`                     | `docs/paper-notes/2602.03082v1.md`      | infra-foundations (manifold-ML thread)     |
| 1.3  | `context/papers/Flow Matching for Generative Modeling.pdf` | `docs/paper-notes/2210.02747.md`*  | infra-foundations (flow-matching origin)   |
| 1.4  | `context/papers/2310.08560.pdf` (download from arxiv) | `docs/paper-notes/Letta-2310.08560.md`  | memory-synthesis + agentic-systems         |

\*Per the paper's arxiv ID. Filename has spaces; per Tier 8 (PR 31), the bulk-rename pass will normalize this.
Provisional plan: keep the spaces during PR 30 and use URL-encoded `pdf:` field; PR 31 rename pass will fix it.

**Task 1.4 specifics — Letta / MemGPT paper:**

- Source: https://arxiv.org/abs/2310.08560 (Packer et al., 2023, *MemGPT: Towards LLMs as Operating Systems*).
- PDF URL: https://arxiv.org/pdf/2310.08560.pdf
- Save to: `context/papers/2310.08560.pdf`
- Paper-note path: `docs/paper-notes/Letta-2310.08560.md` (paired-repo hybrid filename per CLAUDE.md
  §Paper-note paired-repo variant convention).
- Frontmatter `pdf:` field: `../../context/papers/2310.08560.pdf`.
- Pairs with `docs/repo-notes/Letta.md` (Tier 3.1).
- Synthesis homes: primary in `memory-synthesis.md` (memory-tier architecture comparison); secondary in
  `agentic-systems-synthesis.md` (agent-OS analogy).

**Why 1.1–1.3 were missed:** all three were folded inline during PR #29 per the fold-in plan (option D / option
(a) in Dan's feedback). The synthesis prose cites them; no per-paper-note was authored. The "surprise" is that
the synthesis-fold completion implied paper-note authorship to reviewers. **Resolution:** author the three notes,
update INDEX, and update the inline citations in the affected syntheses to link the new paper-notes.

**Dispatch pattern:** 4 sequential agents (one per paper) per CLAUDE.md §Worktree fan-out discipline. Same prompt
template as PR #28 fan-out. Tasks 1.1–1.3 can run in any order; task 1.4 should be ordered after the PDF
download confirms the paper is available locally — and before Tier 3.1 so the paired repo-note can cross-link.

---

## Tier 2 — Investigate + embed orphan pics (4 tasks)

| Pic                                  | Status                                       | Action                                                                  |
| ------------------------------------ | -------------------------------------------- | ----------------------------------------------------------------------- |
| `Bonsai Energy Use.png`              | Embed reportedly attempted in Tier 4.4       | Verify + re-embed in `native-low-bit-apple-silicon-synthesis.md`         |
| `Bonsai Performance vs Size.png`     | Same                                         | Same                                                                     |
| `Git_Branching_Model.pdf`            | Orphan; user previously said `BRANCHING.md`  | Embed link in `BRANCHING.md`                                            |
| `HE2psIVbcAA6VLz.jpg` (claw-code)    | Orphan; was flagged for g7-harnesses earlier | Embed in `docs/syntheses/repo-clusters/g7-harnesses.md`                  |

**The Software Factory.png:** intentionally deferred per Dan's earlier note ("haven't created more content around
it; future fold"). Skip in PR 30.

**Why the Bonsai pics were missed:** the Tier 4.4 agent reported embedding "Intelligence Density, Benchmark
Performance, Performance vs Size, Energy Use" but the orphan check found `Bonsai Energy Use.png` and
`Bonsai Performance vs Size.png` not actually referenced. **Investigation step before fixing:** grep the synthesis
for the actual filenames vs nearby titles. If the agent embedded different filenames (e.g., the PrismML pair which
share similar titles), there's a naming mismatch to resolve. Otherwise re-embed.

**Why the others were missed:** `Git_Branching_Model.pdf` was deferred to "BRANCHING.md is the best place" but
never executed. `HE2psIVbcAA6VLz.jpg` was flagged but its embed in g7-harnesses was deferred when the cluster
fold-ins were done in Tier 4.

**Dispatch pattern:** 1 Maestro pass (4 small edits across 3 files) — too small for Worker dispatch.

---

## Tier 3 — Bin A: 5 Tier-1 repos (clone + repo-notes)

**Authorized 2026-05-10.** URLs pinned below — do not derive URLs from any other source. Clone via
`git clone --depth=1 <url> repos/<dest-name>` per CLAUDE.md §Repo Layout (read-only reference clones).

| Task | Repo (owner)                          | Canonical URL                                          | Clone destination          | Target repo-note                       | Probable verdict | Note                                                                          |
| ---- | ------------------------------------- | ------------------------------------------------------ | -------------------------- | -------------------------------------- | ---------------- | ----------------------------------------------------------------------------- |
| 3.1  | `letta-ai/letta`                      | https://github.com/letta-ai/letta                      | `repos/Letta`              | `docs/repo-notes/Letta.md`             | Study            | **Strongest single recommendation.** Memory-pillar comparison set completer. Pairs with paper-note 1.4 (MemGPT). |
| 3.2  | `0xplaygrounds/rig`                   | https://github.com/0xplaygrounds/rig                   | `repos/rig`                | `docs/repo-notes/rig.md`               | Study            | Rust-side agent + tool-calling pattern; 7.2k★, MIT, no Ollama / no MCP.       |
| 3.3  | `microsoft/autogen`                   | https://github.com/microsoft/autogen                   | `repos/autogen`            | `docs/repo-notes/autogen.md`           | Study            | Surprisingly absent; group-chat-pattern reference for g11 / agentic-systems.  |
| 3.4  | `langchain-ai/langgraph`              | https://github.com/langchain-ai/langgraph              | `repos/langgraph`          | `docs/repo-notes/langgraph.md`         | Study            | Architectural alternative to workgraph-JSONL DAG; canonical reference.        |
| 3.5  | `coinbase/x402`                       | https://github.com/coinbase/x402                       | `repos/x402`               | `docs/repo-notes/x402.md`              | Watch            | HTTP-402 payment protocol; `@x402/mcp` on roadmap as TODO; intersects DEC-0018 / DEC-0045 / future agent-monetization ADR seed. |

**Repo-note discipline:** standard 7-section, cluster-cell `[g4-memory](...)` for Letta; `[g11-agent-frameworks](...)`
for rig + autogen + langgraph; `—` (no cluster) for x402 since it's not an agent framework — possibly create a
new "agent-monetization" cluster footnote later if more lands.

**Dispatch pattern:** Sequential agent dispatch after Maestro completes the 5 clones. File-level partitioning —
each agent writes its own repo-note path, no overlap.

---

## Tier 4 — Bin B: 3 Tier-2 repos (clone + repo-notes)

**Authorized 2026-05-10.** URLs pinned below — do not derive URLs from any other source. Clone via
`git clone --depth=1 <url> repos/<dest-name>`.

| Task | Repo (owner)                            | Canonical URL                                                | Clone destination               | Target repo-note                            | Probable verdict          |
| ---- | --------------------------------------- | ------------------------------------------------------------ | ------------------------------- | ------------------------------------------- | ------------------------- |
| 4.1  | `block/goose`                           | https://github.com/block/goose                               | `repos/goose`                   | `docs/repo-notes/goose.md`                  | Study                     |
| 4.2  | `deeplearning-wisc/debate-or-vote`      | https://github.com/deeplearning-wisc/debate-or-vote          | `repos/debate-or-vote`          | `docs/repo-notes/debate-or-vote.md`         | Study + spike             |
| 4.3  | `nikmcfly/MiroFish-Offline`             | https://github.com/nikmcfly/MiroFish-Offline                 | `repos/MiroFish-Offline`        | `docs/repo-notes/MiroFish-Offline.md`       | Investigate, then Study or Watch |

**Dispatch pattern:** Sequential agent dispatch after Maestro completes the 3 clones.

---

## Tier 5 — Core-doc staleness pass (9 files, single Worker)

Per the staleness-sweep agent's recommendation, **one-shot Worker pass** with a tight spec, **NOT worktree
fan-out** — the files are interdependent (CLAUDE.md repo-layout tree references ADR slugs that DECISIONS.md must
also row; ROADMAP counts must match VISION counts must match CLAUDE counts). Serial editing prevents
cherry-pick reconciliation churn.

**Files + targeted edits** (priority-ordered, gated on Tiers 1+3+4 completion so the new counts are stable):

### CLAUDE.md (HIGH priority)

- L153–154 counts: `~99 per-repo write-ups` → **109 + 8 (Bin A+B) = 117** if Tiers 3+4 execute, else 109; same for paper-note count.
- L270–271: `# 14 thematic + 11 cluster` → `# 15 thematic + 12 cluster`.
- §Repo Layout tree: ADR list missing DEC-0055/0056 (Kimi-K2 fold seeds) + 4 new seeds (reproducibility-bundle, SKILL.md-conformance-linter, agent-monetization-via-x402-mcp, Agent/Identity/Venue layered decomposition).
- Spec list (L257–269): missing `2026-05-09-context-foldin-fanout.md`, `notes-consistency-fanout.md`, `synthesis-refinement-spec.md`, `2026-05-10-pr30-cleanup-spec.md` (this file), and others.
- Repo-clusters list (L271–282): missing `g12-llm-hardware-design.md`.
- Thematic syntheses list (L283–296): missing `llm-hardware-design-synthesis.md`.
- Session-summaries list (L249–256): missing `2026-05-08-notes-consistency-sweep` and `2026-05-08-synthesis-refinement` (and possibly newer).

### DECISIONS.md (HIGH priority)

- Index table ends at DEC-0054. Add rows for DEC-0055, DEC-0056. Add a "Seeded but not yet authored" sub-section
  or placeholder rows for the 4 new seeds (reproducibility-bundle, SKILL.md-conformance-linter,
  agent-monetization-via-x402-mcp, Agent/Identity/Venue layered decomposition).

### ROADMAP.md (MEDIUM-HIGH)

- Status snapshot date: `2026-05-07` → **2026-05-10**.
- Counts: `~99 repo notes` → 109 (or 117 with Bin A+B).
- Second-wave repos list: omits Kimi-K2, DreamZero, EgoScale, ClawBio, dreamzero, transcriptformer, ProtiCelli, plus QiMeng family (CodeV, MuPa, SALV, cpu-v1).
- L446–448: Kimi-K2 listed as "later-phase" but now Phase 6/8 candidate via DEC-0055/0056 seeds.

### VISION.md (MEDIUM)

- L160–161 counts: `12 to ~99` → 12 → 109 (or 117); `25 syntheses (14 thematic + 11 cluster, g1–g11)` → 27 (15 + 12, g1–g12).
- "What Linus is becoming concrete" framing should include `llm-hardware-design` thread + Kimi-K2 / weight-streaming + Canteen translation-as-moat angle.

### ARCHITECTURE.md (MEDIUM)

- L101–148 orchestration-layer description should reflect "Venue layer" framing from Canteen Agent/Identity/Venue.
- Reference weight-streaming target spec promotion + Kimi-K2 integration where relevant.

### GLOSSARY.md (MEDIUM)

- Add vocabulary: idea→reality spine, MTMC, planner/coder/verifier discipline, Agent/Identity/Venue layered decomposition, reproducibility bundle, SKILL.md conformance linter, weight-streaming, x402-mcp, Venue layer, translation-as-moat.
- External projects list: add Kimi-K2, DreamZero, EgoScale, ClawBio, Canteen, Agora, qimeng.

### BRANCHING.md (MEDIUM)

- Cross-link CLAUDE.md §Worktree fan-out discipline (L561–597). Update branch-type list if needed.

### README.md (LOW)

- Audience-facing snapshot; minor refresh of phase markers.

### SAFETY.md (LOW)

- No identified drift.

**Dispatch pattern:** Single Worker with line-range edits enumerated per file. Maestro reviews, commits one PR
covering all 9 files, atomic commit per file (or one bundled commit titled
`[docs] Core-doc staleness refresh after PR #28/#29 batch`).

---

## Tier 6 — INDEX backfill for new paper-notes + repo-notes

After Tiers 1+3+4 complete, add INDEX entries for:

- 3 new paper-notes (Trading-R1, Geometry-Preserving NA, Flow Matching origin).
- 8 new repo-notes (Letta, rig, AutoGen, LangGraph, x402, Goose, debate-or-vote, MiroFish-Offline) — gated on
  Tier 3+4 authorization.

**Dispatch pattern:** Maestro mechanical edits, single commit.

---

## Tier 7 — Curation-log entries

After Tier 3+4 clones land, add a 2026-05-10 entry to `docs/curation-log.md` enumerating the 8 Bin A+B clones
with one-line rationale per repo (citing the Canteen blog landscape note as the source review).

**Dispatch pattern:** Maestro single edit.

---

## Tier 10 — Landscape + top-questions accuracy audit

**Added 2026-05-10** at Dan's request. Final accuracy pass before PR 30 closes. Performed by Maestro because
it requires holding all syntheses in working memory simultaneously to spot inconsistencies — not a Worker task.

**Inputs (all loaded simultaneously):**

- All 14 thematic syntheses in `docs/syntheses/*.md` (excluding `repo-clusters/`).
- All 12 cluster syntheses in `docs/syntheses/repo-clusters/g1`–`g12`.
- `docs/landscapes/total-landscape.md` (cross-corpus rollup).
- `docs/landscapes/synthesis-landscape.md` (synthesis-doc rollup).
- `docs/questions/top-questions.md` (current working set).
- `docs/questions/answered-questions.md` (resolution archive — read for cross-check, not edited).

**Out of scope (per Dan 2026-05-10):** `docs/landscapes/paper-landscape.md` and `repo-landscape.md` are
deprecated stubs and stay as-is.

**Audit checks:**

| Check | Inputs | Failure mode to catch                                                                |
| ----- | ------ | ------------------------------------------------------------------------------------ |
| 10.1  | synthesis-landscape vs syntheses dir         | Every synthesis has a row + correct title + cluster cell + "How the syntheses overlap" entry; no orphan rows |
| 10.2  | total-landscape counts                       | Paper count, repo count, synthesis count all reflect post-PR-30 state (after Tier 1+3+4 land) |
| 10.3  | total-landscape representation               | New clusters (g12) and new fold-ins (Letta, x402, autogen, langgraph, rig, goose, debate-or-vote, MiroFish-Offline, Letta MemGPT paper, 3 promoted papers) are represented |
| 10.4  | top-questions vs syntheses                   | No question listed as "open" that a synthesis since closed (cross-reference DECs); no resolved question still showing as top-question |
| 10.5  | top-questions vs answered-questions          | Promotions to answered-questions.md are reflected — top-questions shows the right working set |
| 10.6  | synthesis-landscape §"What's missing"        | **Specifically** — `docs/maestro-protocol.md` is listed as missing at line ~385 but the doc has since been authored at `docs/protocols/maestro-protocol.md` (~18KB, last modified 2026-05-07). Resolve the path mismatch (the landscape was written before the protocol moved into `docs/protocols/`) and move the entry from §"What's missing" to §"Closed during the resolution arc". Apply the same pattern to any other items in §"What's missing" that have been silently delivered. (Dan flag, 2026-05-10) |
| 10.7  | tight coupling across the three docs         | total-landscape ↔ synthesis-landscape ↔ top-questions should reference each other consistently (no claim in one that contradicts another); trim stale info aggressively per Dan's "sharp, focused, and current" direction |

**Resolution actions:** fix drift inline as discovered. Each fix gets a brief inline rationale comment so future
audits can reproduce the reasoning. Single Maestro commit at the end titled
`[docs] Landscape + top-questions accuracy refresh after PR 30 fold-ins`.

**Why this matters:** the corpus has ~26 syntheses now and the landscapes drift quickly when fold-ins land
without explicit rollup updates. Treating "load everything at once and audit" as a recurring discipline (vs
trusting individual fold-ins to update the rollups correctly) was the gap PR #28/#29 surfaced.

**Dispatch pattern:** single Maestro session with all inputs loaded at once. Estimated 1–2 hours.

---

## Open decisions — RESOLVED 2026-05-10

All four decisions have been confirmed by Dan:

| Decision                                            | Resolution        |
| --------------------------------------------------- | ----------------- |
| Tier 3+4 clone authorization                        | **Approved**. URLs pinned in Tier 3 + Tier 4 sections above.  |
| Tier 8 — bulk-rename files with spaces              | **Approved**, deferred to PR 31. ADR + execution there.       |
| Tier 9 — Git LFS for `context/` (+ `.gitignore` update) | **Approved**, deferred to PR 31. ADR + execution there. |
| PR 30 scope — split decision                        | **PR 30 = content + Tier 10**; **PR 31 = Tier 8 (rename) + Tier 9 (LFS)**. |

---

## Dispatch pattern

**Sequential agent dispatch with file-level partitioning** per CLAUDE.md §Worktree fan-out discipline. Mostly
Maestro-led for the small-scope tiers (Tier 2, 6, 7, 10); Worker fan-out for the larger tiers (Tier 1 = 4
sequential agents; Tier 3 = 5 sequential agents after clones; Tier 4 = 3 sequential agents after clones;
Tier 5 = single Worker with tight line-range spec). No worktrees — files are interdependent (especially
Tier 5 and Tier 10).

**Canary first** for Tier 3+4 — clone + repo-note pipeline hasn't been exercised this session in this exact
shape. Use Tier 3.1 (Letta, the strongest single recommendation, with paired paper-note 1.4) as the canary.

---

## PR plan

**PR 30 (this branch: `agent/pr30-cleanup`)** — Tiers 1 + 2 + 3 + 4 + 5 + 6 + 7 + 10. Single PR; ~30+
commits. Open after Tier 10 audit closes.

**PR 31 (separate branch, after PR 30 merges)** — Tier 8 (bulk-rename) + Tier 9 (Git LFS). Each gets its own
ADR. Branch name TBD when PR 31 is opened. Both are policy decisions with broad blast radius — independent
review windows protect against rename or LFS introducing edge-case breakage that's hard to isolate inside a
content-heavy PR.

---

## Estimated wall time

| Tier | Estimate                                                                                                |
| ---- | ------------------------------------------------------------------------------------------------------- |
| 1    | 1–2 hours (4 agents — 3 already-cited papers + 1 paired Letta MemGPT note)                              |
| 2    | 30 min (Maestro inline)                                                                                 |
| 3    | 2–3 hours (5 agents after clones)                                                                       |
| 4    | 1–2 hours (3 agents after clones)                                                                       |
| 5    | 1–2 hours (single Worker; 9 files, mostly count + list updates)                                         |
| 6    | 30 min (Maestro mechanical)                                                                             |
| 7    | 15 min (Maestro single edit)                                                                            |
| 10   | 1–2 hours (Maestro audit, all syntheses loaded at once)                                                 |
| —    | **Total: ~7–13 hours**                                                                                  |

Per the measure-don't-estimate convention, log actual vs estimate at the close of each tier.

---

## Status

- 2026-05-10: spec authored on `agent/pr30-cleanup` (base SHA `af3eddb`).
- 2026-05-10: open decisions resolved (Tier 3+4 authorized; Tier 8+9 approved, deferred to PR 31; landscape audit
  added as Tier 10; Letta MemGPT paper added as Task 1.4).
- _Active: execution beginning with Tier 1 paper-note authoring._
