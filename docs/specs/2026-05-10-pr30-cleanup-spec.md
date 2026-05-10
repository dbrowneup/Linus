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

| Tier | Family                                                          | Count   | Output                                        | Gating                                         |
| ---- | --------------------------------------------------------------- | ------- | --------------------------------------------- | ---------------------------------------------- |
| 1    | Promote inline-cited papers to paper-notes                      | 3       | `docs/paper-notes/<stem>.md` × 3              | none                                           |
| 2    | Investigate + embed orphan pics                                 | 4       | inline embeds + cross-refs                    | gated on figuring out what happened with #1.5 |
| 3    | Bin A — Tier 1 repo clones + notes                              | 5       | clone + `docs/repo-notes/<repo>.md` × 5       | needs Dan authorization for clones             |
| 4    | Bin B — Tier 2 repo clones + notes                              | 3       | clone + `docs/repo-notes/<repo>.md` × 3       | needs Dan authorization for clones             |
| 5    | Core-doc staleness — single Worker pass                         | 9 files | edits across CLAUDE/README/VISION/etc.        | gated on Tier 1–4 so counts are stable         |
| 6    | INDEX backfill for new paper-notes + repo-notes                 | 2 files | INDEX entries added                           | gated on Tier 1+3+4                            |
| 7    | Curation-log entries for Tier 3+4 clones                        | 1 file  | `docs/curation-log.md` updated                | gated on Tier 3+4                              |
| 8    | (Decision) Bulk-rename files with spaces — ADR candidate        | TBD     | new ADR + (maybe) rename pass                 | Dan decision needed — see §"Open decisions"    |
| 9    | (Decision) Git LFS for `context/` — ADR candidate               | TBD     | new ADR + (maybe) `.gitattributes` + migration| Dan decision needed — see §"Open decisions"    |

Total: ~24 sub-tasks, of which 8 are blocked on Dan authorization and 2 are decision items that may not execute
in PR 30 at all.

---

## Tier 1 — Promote inline-cited papers to paper-notes (3 tasks)

These three papers were intentionally deferred to inline citation during the original fold-in (per Dan's feedback
on options A/B/C/D), but the corpus is mature enough now that promoting them to full paper-notes closes a
"surprised-we-missed-this" gap and gives them durable cross-reference handles.

| Task | PDF                                                   | Target paper-note                       | Synthesis home(s)                          |
| ---- | ----------------------------------------------------- | --------------------------------------- | ------------------------------------------ |
| 1.1  | `context/papers/2509.11420v1.pdf`                     | `docs/paper-notes/2509.11420v1.md`      | agentic-systems (extends TradingAgents)    |
| 1.2  | `context/papers/2602.03082v1.pdf`                     | `docs/paper-notes/2602.03082v1.md`      | infra-foundations (manifold-ML thread)     |
| 1.3  | `context/papers/Flow Matching for Generative Modeling.pdf` | `docs/paper-notes/2210.02747.md`*  | infra-foundations (flow-matching origin)   |

\*Per the paper's arxiv ID. Filename has spaces; per Tier 8 (below), this could become an argument for the
bulk-rename decision. Provisional plan: copy/rename PDF to `2210.02747.pdf` to match arxiv convention if Dan
authorizes a one-off rename, otherwise keep the spaces and use URL-encoded `pdf:` field.

**Why these were missed:** all three were folded inline during PR #29 per the fold-in plan (option D / option (a)
in Dan's feedback). The synthesis prose cites them; no per-paper-note was authored. The "surprise" is that the
synthesis-fold completion implied paper-note authorship to reviewers. **Resolution:** author the three notes,
update INDEX, and update the inline citations in the affected syntheses to link the new paper-notes.

**Dispatch pattern:** 3 parallel agents (one per paper). Same prompt template as PR #28 fan-out, paired-paper-note
versions if applicable.

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

**Blocked on Dan authorization for clones.** Per CLAUDE.md §Tool Use Policy "Any network operation requires
confirmation"; `git clone` is a network operation. The clones are explicitly recommended in
`canteen_blog_landscape_2026-05.md` §Bin A, so this is pre-approved at the planning level — but the actual `git
clone` invocations need an explicit go-ahead.

| Task | Repo (owner)                          | Target repo-note                          | Probable verdict | Note                                                                          |
| ---- | ------------------------------------- | ----------------------------------------- | ---------------- | ----------------------------------------------------------------------------- |
| 3.1  | `letta-ai/letta`                      | `docs/repo-notes/letta.md`                | Study            | **Strongest single recommendation.** Memory-pillar comparison set completer.  |
| 3.2  | `0xplaygrounds/rig`                   | `docs/repo-notes/rig.md`                  | Study            | Rust-side agent + tool-calling pattern; 7.2k★, MIT, no Ollama / no MCP.       |
| 3.3  | `microsoft/autogen`                   | `docs/repo-notes/autogen.md`              | Study            | Surprisingly absent; group-chat-pattern reference for g11 / agentic-systems.  |
| 3.4  | `langchain-ai/langgraph`              | `docs/repo-notes/langgraph.md`            | Study            | Architectural alternative to workgraph-JSONL DAG; canonical reference.        |
| 3.5  | `coinbase/x402`                       | `docs/repo-notes/x402.md`                 | Watch            | HTTP-402 payment protocol; `@x402/mcp` on roadmap as TODO; intersects DEC-0018 / DEC-0045 / future agent-monetization ADR seed. |

**Repo-note discipline:** standard 7-section, cluster-cell `[g4-memory](...)` for letta; `[g11-agent-frameworks](...)`
for rig + autogen + langgraph; `—` (no cluster) for x402 since it's not an agent framework — possibly create a
new "agent-monetization" cluster footnote later if more lands.

**Dispatch pattern:** 5 parallel agents after clones complete. Same template as past repo-note dispatches.

---

## Tier 4 — Bin B: 3 Tier-2 repos (clone + repo-notes)

**Blocked on Dan authorization for clones (same as Tier 3).**

| Task | Repo (owner)                            | Target repo-note                            | Probable verdict          |
| ---- | --------------------------------------- | ------------------------------------------- | ------------------------- |
| 4.1  | `block/goose`                           | `docs/repo-notes/goose.md`                  | Study                     |
| 4.2  | `deeplearning-wisc/debate-or-vote`      | `docs/repo-notes/debate-or-vote.md`         | Study + spike             |
| 4.3  | `nikmcfly/MiroFish-Offline`             | `docs/repo-notes/MiroFish-Offline.md`       | Investigate, then Study or Watch |

**Dispatch pattern:** 3 parallel agents after clones.

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

## Tier 8 (decision item) — Bulk-rename files with spaces

**Status:** ADR candidate. **Not in PR 30 execution scope; surfaced for Dan's decision.**

**Problem:** Files with spaces in their names (`Anthropic's Responsible Scaling Policy (version 3.0).pdf`,
`As We May Think.txt`, `Flow Matching for Generative Modeling.pdf`, `Bonsai Energy Use.png`,
`Bonsai Performance vs Size.png`, `Bush - As We May Think (Life Magazine 9-10-1945).pdf`,
`How-Anthropic-teams-use-Claude-Code_v2.pdf`, `LLM Wiki GitHub Repos.xlsx`, `Memory makes computation universal,
remember?.txt`, plus various synthesis-cited threads with spaces in names) require URL-encoding in markdown links
(`%20` for space, `%27` for apostrophe, etc.). This is fragile — link rot is silent, broken links don't show up
until someone clicks. Several past fold-ins have hit this (URL-encoded curly apostrophe in Anthropic RSP, etc.).

**Affected files** (sweep needed; preliminary count from `find context/ docs/ -name '* *' | wc -l`): probably 15–25
files across `context/notes/`, `context/papers/`, `context/pics/`, `context/threads/`, plus a few paper-notes
(`Horiike-Orthogonal projections of hypercubes-2025-Physical Review E copy.md`).

**Options:**

- **(a) Bulk-rename pass**, replacing spaces and special characters with `-` or `_`. Update all references in
  syntheses, paper-notes, repo-notes, INDEXes, curation-log. Major touch (~50–100 file edits). One-time pain;
  durable cleanup. Affects historical link integrity in past commits — cherry-pick reconciliation costs are
  low since the renames are pure substitution.
- **(b) Half-measure**: rename only the specific files where link breakage has been observed (Anthropic RSP,
  Flow Matching, etc.). Lower scope but leaves the discipline-debt for next time.
- **(c) Don't rename**: standardize on URL-encoding everywhere; document in CLAUDE.md §Doc-type conventions.
  Lowest immediate work; perpetual fragility.

**Recommendation pending Dan's call.** Lean toward **(a) bulk-rename** with an ADR (DEC-NNNN
filename-discipline-no-spaces) committing the policy, executed via single Maestro pass after PR 30 closes the
content drift.

---

## Tier 9 (decision item) — Git LFS for `context/`

**Status:** ADR candidate. **Not in PR 30 execution scope; surfaced for Dan's decision.**

**Problem:** `context/` is currently `.gitignore`d. Primary sources (paper PDFs, notes, pics, threads) live only
on Dan's local filesystem with no git history. Future research distribution (the entrepreneurship synthesis
flagged commercial-surface implications) needs primary-source provenance.

**Solution:** Track `context/` (or selectively, `context/papers/` + `context/notes/` + `context/pics/`) via Git
LFS. PDFs / images stored remotely on the LFS server; pointers in git history; clones can opt-in to fetch via
`git lfs pull`.

**Implications:**

- **Storage:** GitHub Free includes 1 GB LFS storage + 1 GB/month bandwidth. `context/` is currently ~50 MB
  estimated; well within free tier.
- **Distribution:** with LFS, anyone cloning the repo can pull primary sources. Important for reproducibility,
  for the entrepreneurship-synthesis commercial-surface story, and for future Worker fan-outs that need primary
  source access.
- **Clone size:** non-LFS clones stay small (LFS files are pointer files, ~1 KB each). LFS pull is opt-in.
- **Setup:** add `.gitattributes` declaring LFS patterns; `git lfs migrate import --include=…` for historical
  files (if any are already tracked); update `.gitignore` to remove `context/`.
- **Caveats:** GitHub LFS has bandwidth limits; if Linus eventually distributes broadly, may need to upgrade or
  move to a dedicated LFS server.

**Recommendation pending Dan's call.** Lean toward **adopt LFS for `context/`** with an ADR (DEC-NNNN
context-tracked-via-git-lfs) committing the policy, executed in a separate PR before any commercial-surface
distribution.

---

## Open decisions Dan needs to make

1. **Tier 3+4 clone authorization** — go/no-go on Bin A (5 repos) and Bin B (3 repos).
2. **Tier 8 decision** — bulk-rename files with spaces? (a / b / c above)
3. **Tier 9 decision** — adopt Git LFS for `context/`?
4. **PR 30 scope** — execute only Tier 1+2+5+6+7 (no clones, no rename, no LFS), or bundle some/all of the above?

If Dan returns "go on all four," recommended PR 30 scope:

- Tier 1 (3 paper-notes)
- Tier 2 (4 pic embeds)
- Tier 3 (5 Bin A repos + repo-notes)
- Tier 4 (3 Bin B repos + repo-notes)
- Tier 5 (9 core-doc updates)
- Tier 6 (INDEX backfill)
- Tier 7 (curation-log)

Defer Tier 8 (rename) and Tier 9 (LFS) to **PR 31** as separate ADRs + execution because both are policy decisions
with broad blast radius.

If Dan returns "do the safe stuff in PR 30, defer the rest" — recommended PR 30 scope: Tier 1+2+5+6+7 only.
Tier 3+4+8+9 deferred to PR 31+.

---

## Dispatch pattern

**Sequential agent dispatch with file-level partitioning** per CLAUDE.md §Worktree fan-out discipline. Mostly
Maestro-led for the small-scope tiers (Tier 2, 6, 7); Worker fan-out for the larger tiers (Tier 1 = 3 agents
in parallel; Tier 3 = 5 agents in parallel; Tier 4 = 3 agents in parallel; Tier 5 = single Worker with tight
line-range spec). No worktrees — files are interdependent (especially Tier 5).

**Canary first** for Tier 3+4 if those execute — clone + repo-note pipeline hasn't been exercised this session
in this exact shape.

---

## PR plan

**PR 30** — Tier 1 + 2 + (3+4 if authorized) + 5 + 6 + 7. Single PR if scope is manageable (~30 commits).
Branch: `agent/pr30-cleanup`.

**PR 31** (if Tier 8/9 advance) — Bulk-rename + LFS migration. Each gets its own ADR. Should land separately
from PR 30 because both are policy decisions worth their own review windows.

---

## Estimated wall time

| Tier | Estimate                                                                                                |
| ---- | ------------------------------------------------------------------------------------------------------- |
| 1    | 1–2 hours (3 agents, paper-notes for already-cited papers — fast)                                       |
| 2    | 30 min (Maestro inline)                                                                                 |
| 3    | 2–3 hours (5 agents after clones)                                                                       |
| 4    | 1–2 hours (3 agents after clones)                                                                       |
| 5    | 1–2 hours (single Worker; 9 files, mostly count + list updates)                                         |
| 6    | 30 min (Maestro mechanical)                                                                             |
| 7    | 15 min (Maestro single edit)                                                                            |
| —    | **Total:** ~6–11 hours if all tiers execute; ~3–5 hours if Bin A+B deferred.                            |

Per the measure-don't-estimate convention, log actual vs estimate at the close of each tier.

---

## Status

- 2026-05-10: spec authored on `agent/pr30-cleanup` (base SHA `af3eddb`).
- _Pending: Dan's decision on Tier 3+4 clone authorization, Tier 8 rename, Tier 9 LFS._
- _Pending: execution after Dan returns from PR #29 review and answers the open decisions._
