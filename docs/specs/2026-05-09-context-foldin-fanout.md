# Context Fold-in Fan-out Spec — 2026-05-09

**Status:** active **Branch:** `agent/context-foldin-fanout` (base SHA `577ebb74ceacb218768c5d15f071270a8d7e1f79`).
**Owner:** Maestro (Dan + Claude Code).

**Origin:** Companion to the 2026-05-09 context fold-in inventory pass. Routes the authoring of ~13 paper-notes
and ~7 repo-notes identified in that inventory, plus the synthesis-level fold-ins and the new
LLM-hardware-design synthesis. The QiMeng-specific tasks are owned upstream by
[`docs/specs/qimeng-category-promotion.md`](qimeng-category-promotion.md); this spec routes their execution.

**Related conventions:**

- CLAUDE.md §Doc-type conventions (paper-note + repo-note required structure; **paired-repo variant** for Kimi-K2).
- CLAUDE.md §Worktree fan-out discipline + §Agent fan-out: probe permissions first.
- CLAUDE.md §PR summary discipline + §Branch discipline.
- CLAUDE.md §Measure, don't just estimate.

---

## Tasks at a glance

| Tier | Family                                                                | Count | Output                                       | Gating                  |
| ---- | --------------------------------------------------------------------- | ----- | -------------------------------------------- | ----------------------- |
| 1    | Paper-notes (10 QiMeng + ProtiCelli + TranscriptFormer + Kimi-K2)     | 13    | `docs/paper-notes/<stem>.md` × 13            | none — start here       |
| 2    | Repo-notes (3 QiMeng + ProtiCelli + transcriptformer + jan + Kimi-K2) | 7     | `docs/repo-notes/<repo>.md` × 7              | none — parallel w/ T1   |
| 2b   | Repo-notes (claude-code-guide, cs249r_book)                           | 2     | `docs/repo-notes/<repo>.md` × 2              | none — parallel         |
| 3    | INDEX.md updates                                                      | 2     | INDEX entry per new paper-note + repo-note   | gated on T1+T2          |
| 4    | Synthesis fold-ins                                                    | 8 PRs | edit existing thematic syntheses             | gated on T1+T2 complete |
| 5    | LLM-hardware-design synthesis authoring                               | 2     | `g12-llm-hardware-design.md` + thematic file | gated on T1+T2 QiMeng   |
| 6    | B14 notes-consistency re-bin                                          | 1     | spec sweep + paper-note Connections refresh  | gated on T5             |

Total work: ~22 author-tasks + ~8 synthesis edits + ~2 synthesis authorings + 1 sweep = **~33 sub-tasks**.

---

## Tier 1 — Paper-notes (13)

Each task: read the source PDF; author canonical paper-note (YAML frontmatter `title` / `source` / `authors` /
`affiliation` / `date` / `pdf` / `tags`; H1 = paper title; eight H2 sections in fixed order — TL;DR · The problem
(in plain language) · What they propose · Key results · What's reusable in Linus · What's NOT applicable / hype
filter · Connections · Open questions for Dan); commit on `agent/context-foldin-fanout`.

### QiMeng family (10 paper-notes; INDEX placeholder `_Pending llm-hardware-design_`)

All ten share the **idea → reality** spine per `qimeng-category-promotion.md` §"Dan's stated framing". "What's
reusable in Linus" should explicitly map each contribution to (a) what artifact the LLM produces, (b) which
downstream actor accepts it, (c) what must be true for Linus to replicate the discipline locally on Apple Silicon.

| Task | PDF                                          | Target paper-note                  | Paper title (short)                 | Paired repo / pairing note    |
| ---- | -------------------------------------------- | ---------------------------------- | ----------------------------------- | ----------------------------- |
| 1.1  | `context/papers/13337-ZhouQ.pdf`             | `docs/paper-notes/13337-ZhouQ.md`  | QiMeng-GEMM                         | none (kernel paper)           |
| 1.2  | `context/papers/2407.10424v5.pdf`            | `docs/paper-notes/2407.10424v5.md` | CodeV — Verilog gen via multi-level | `repos/CodeV` (Task 2.1)      |
| 1.3  | `context/papers/2505.06302v1.pdf`            | `docs/paper-notes/2505.06302v1.md` | QiMeng-TensorOp                     | none                          |
| 1.4  | `context/papers/2505.24183v5.pdf`            | `docs/paper-notes/2505.24183v5.md` | QiMeng-CodeV-R1 (RLVR for Verilog)  | `repos/CodeV` (Task 2.1)      |
| 1.5  | `context/papers/2506.11153v2.pdf`            | `docs/paper-notes/2506.11153v2.md` | QiMeng-MuPa (sequential→parallel)   | `repos/QiMeng-MuPa` (Task 2.2)|
| 1.6  | `context/papers/2506.12355v1.pdf`            | `docs/paper-notes/2506.12355v1.md` | QiMeng-Attention (FlashAttention)   | none                          |
| 1.7  | `context/papers/2510.19296v4.pdf`            | `docs/paper-notes/2510.19296v4.md` | QiMeng-SALV (signal-aware Verilog)  | `repos/QiMeng-SALV` (Task 2.3)|
| 1.8  | `context/papers/3696443.3708931.pdf`         | `docs/paper-notes/3696443.3708931.md` | VEGA (compiler back-end gen)     | none                          |
| 1.9  | `context/papers/9546_AutoOS_Make_Your_OS_More_.pdf` | `docs/paper-notes/9546_AutoOS_Make_Your_OS_More_.md` | AutoOS (kernel config) | none                |
| 1.10 | `context/papers/osdi25-dong.pdf`             | `docs/paper-notes/osdi25-dong.md`  | QiMeng-Xpiler (transcompilation)    | none                          |

**Pairing note:** Tasks 1.2 and 1.4 share `repos/CodeV` and 1.4 directly extends 1.2 with RLVR. Author both via a
**single agent** that reads both PDFs and the repo before committing two notes; each note's Connections section
links the other and the shared repo-note (Task 2.1). Other pairs (1.5↔2.2, 1.7↔2.3) can be authored by separate
agents but must cross-reference.

### Generative cellular biology FM pair (2 paper-notes)

Both bound for `biological-foundation-models-synthesis.md` (primary). ProtiCelli also folds into
`generative-biology-synthesis.md` (secondary). Each paired with its repo-note via single-agent dispatch.

| Task | PDF                                                  | Target paper-note                            | Title (short)                          | Paired repo                          |
| ---- | ---------------------------------------------------- | -------------------------------------------- | -------------------------------------- | ------------------------------------ |
| 1.11 | `context/papers/2026.03.31.715748v1.full.pdf`        | `docs/paper-notes/2026.03.31.715748v1.md`    | ProtiCelli — proteome-wide imaging FM | `repos/ProtiCelli` (Task 2.4)        |
| 1.12 | `context/papers/science.aec8514.pdf`                 | `docs/paper-notes/science.aec8514.md`        | TranscriptFormer — generative cell atlas across 1.5B yrs | `repos/transcriptformer` (Task 2.5) |

### Kimi-K2 tech-report-as-paper-note (1, special handling)

| Task | PDF                                  | Target paper-note                         | Title (short)         | Paired repo                  |
| ---- | ------------------------------------ | ----------------------------------------- | --------------------- | ---------------------------- |
| 1.13 | `repos/Kimi-K2/tech_report.pdf`     | `docs/paper-notes/Kimi-K2-2507.20534.md`  | Kimi K2: Open Agentic Intelligence | `repos/Kimi-K2` (Task 2.6) |

**Special instructions for Task 1.13:**

1. **Filename is hybrid** per CLAUDE.md §Doc-type conventions paired-repo variant: `Kimi-K2-2507.20534.md`, NOT
   `2507.20534.md`. The PDF stem differs from the conventional arxiv-id stem precisely because the tech report
   ships in the paired repo.
2. **`pdf:` frontmatter field** points to `../../repos/Kimi-K2/tech_report.pdf` (relative path into `repos/`,
   not into `context/papers/`).
3. **Read the full tech report**, not just the README. The 5.1 MB PDF is ~30–50 pages and contains the durable
   architectural / training claims (MuonClip optimizer, 1T-total / 32B-active MoE topology, 384 experts × 8
   active + 1 shared, MLA attention, 15.5T training tokens with "zero training instability"). This is paper-note
   depth, not repo-note summary.
4. **Multi-synthesis fold** in Connections section: native-low-bit-apple-silicon (primary, weight-streaming +
   1-bit Linus-flavored variant candidate); infra-foundations (architecture details + MuonClip); agentic-systems
   (SOTA Tau2 / AceBench tool-use scores); skills-and-practices (Anthropic-compatible API as Linus front-end
   pattern).
5. **Phase mapping in "What's reusable in Linus"** must surface: Phase 6 LoRA base candidate (alongside or
   replacing Qwen3 — open question DEC-0055 seed); Phase 6d weight-streaming target (1T-total ÷ 8 active expert
   shards × FP8 footprint vs. 32 GB unified memory + 600 GB external SSD); Phase 8 research direction for a 1-bit
   / ternary Linus-flavored Kimi-K2 (DEC-0056 seed combining flash-MoE + Bonsai/BitNet quantization). Tag both
   ADR seeds inline with `_Seed: DEC-NNNN_`.
6. **MuonClip is itself a watch-item.** Even if Kimi-K2 doesn't become the base, MuonClip's "zero training
   instability at 1T × 15.5T tokens" is a Phase 6 fine-tuning convention candidate independent of the model
   choice. Surface as its own open question.
7. **Open questions** should include at minimum: (a) feasibility of weight-streaming Kimi-K2 on M1 Max + 600 GB
   external SSD; (b) latency floor for first-token / per-token under that streaming pattern; (c) does
   FP8 → int4/ternary preserve agentic benchmark performance; (d) is MuonClip reproducible on Apple Silicon /
   does it generalize to dense models; (e) Kimi-K2 vs Qwen3 evidence threshold for Phase 6 base swap.

---

## Tier 2 — Repo-notes (7)

Each task: read the repo's README (and tech report if it has one), study the source tree's top-level structure;
author canonical repo-note per CLAUDE.md (no frontmatter; H1 = `# <repo> (\`<owner/repo>\`)`; seven numbered H2
sections in fixed order — Purpose and scope · Architecture summary · What's reusable in Linus · What's
inspiration only · What's incompatible or out of scope · Recommendation: **<verdict>** · Questions for Dan).

Verdict vocabulary: **Integrate**, **Study**, **Adapt**, **Watch**, **Ignore**.

### QiMeng repos (3; INDEX placeholder `_Pending llm-hardware-design_`)

| Task | Repo                  | Target repo-note                     | Paired paper(s)                | Probable verdict |
| ---- | --------------------- | ------------------------------------ | ------------------------------ | ---------------- |
| 2.1  | `repos/CodeV`         | `docs/repo-notes/CodeV.md`           | 2407.10424v5 + 2505.24183v5    | Study            |
| 2.2  | `repos/QiMeng-MuPa`   | `docs/repo-notes/QiMeng-MuPa.md`     | 2506.11153v2                   | Study            |
| 2.3  | `repos/QiMeng-SALV`   | `docs/repo-notes/QiMeng-SALV.md`     | 2510.19296v4                   | Study            |

### Bio FM repos (2)

| Task | Repo                       | Target repo-note                       | Paired paper       | Probable verdict |
| ---- | -------------------------- | -------------------------------------- | ------------------ | ---------------- |
| 2.4  | `repos/ProtiCelli`         | `docs/repo-notes/ProtiCelli.md`        | 2026.03.31.715748v1 | Study            |
| 2.5  | `repos/transcriptformer`   | `docs/repo-notes/transcriptformer.md`  | science.aec8514    | Study            |

### Kimi-K2 (1, paired with Task 1.13)

| Task | Repo            | Target repo-note                | Paired paper-note          | Probable verdict        |
| ---- | --------------- | ------------------------------- | -------------------------- | ----------------------- |
| 2.6  | `repos/Kimi-K2` | `docs/repo-notes/Kimi-K2.md`    | Kimi-K2-2507.20534         | Study (high upside)     |

**Special instructions for Task 2.6:** the repo-note covers **artifacts only** — deployment surface (vLLM /
SGLang / KTransformers / TensorRT-LLM), block-fp8 weights distribution on HuggingFace, Modified MIT license,
Anthropic-compatible API quirk (`real_temperature = request_temperature * 0.6`). All architectural / training
claims live in the paired paper-note (Task 1.13). The "What's reusable" section should explicitly defer
architecture commentary to the paper-note via the Connections section.

### Local-LLM front-end (1)

| Task | Repo         | Target repo-note                  | Cluster        | Probable verdict           |
| ---- | ------------ | --------------------------------- | -------------- | -------------------------- |
| 2.7  | `repos/jan`  | `docs/repo-notes/jan.md`          | g7-harnesses   | Watch                      |

---

## Tier 2b — Ecosystem repos (2; can run parallel with Tier 2)

| Task | Repo                       | Target repo-note                          | Cluster                  | Probable verdict |
| ---- | -------------------------- | ----------------------------------------- | ------------------------ | ---------------- |
| 2b.1 | `repos/claude-code-guide`  | `docs/repo-notes/claude-code-guide.md`    | g11-agent-frameworks     | Study            |
| 2b.2 | `repos/cs249r_book`        | `docs/repo-notes/cs249r_book.md`          | — (educational reference) | Study           |

`repos/awesome-ml` is **not** authored as a repo-note per Dan's decision; the 2026-05-09 curation-log entry
records it as an indexed-resource-only.

---

## Tier 3 — INDEX.md updates (gated on Tier 1 + 2 + 2b)

Add 13 new paper-note entries to `docs/paper-notes/INDEX.md` and 7 new repo-note entries to
`docs/repo-notes/INDEX.md`, alphabetically inserted (case-insensitive). Synthesis-cell convention:

- QiMeng family entries: `_Pending llm-hardware-design_` until Tier 5 lands.
- ProtiCelli: `[biological-foundation-models](../syntheses/biological-foundation-models-synthesis.md), [generative-biology](../syntheses/generative-biology-synthesis.md)`.
- TranscriptFormer: `[biological-foundation-models](...)`.
- Kimi-K2 tech-report paper-note: `[native-low-bit-apple-silicon](...), [infra-foundations](...), [agentic-systems](...), [skills-and-practices](...)`.
- jan repo-note: cluster `[g7-harnesses](...)`, thematic blank.
- Kimi-K2 repo-note: cluster `—` (pre-fan-out core style is wrong here; use cluster `—` and put thematic
  syntheses in the thematic cell same as the paper-note).
- claude-code-guide: cluster `[g11-agent-frameworks](...)`, thematic `[skills-and-practices](...)`.
- cs249r_book: cluster `—`, thematic `[infra-foundations](...)`.

---

## Tier 4 — Synthesis fold-ins (8 PRs, gated on Tier 1+2+2b+3)

One PR per affected synthesis. Each PR adds one paragraph (or 2–3 if structurally warranted) to integrate the
new notes; updates Connections sections; bumps the date stamp / refresh note in the synthesis preamble.

| PR  | Synthesis                                                          | Folds in                                                                                                            |
| --- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| 4.1 | `biological-foundation-models-synthesis.md`                        | ProtiCelli + TranscriptFormer (specialists-as-Workers framing extended to imaging FM and cross-species transcriptomic FM) |
| 4.2 | `generative-biology-synthesis.md`                                  | ProtiCelli (generative imaging substrate)                                                                            |
| 4.3 | `infra-foundations-synthesis.md`                                   | Kimi-K2 (architecture + MuonClip); Flow Matching original paper (foundational ref under existing flow-matching block); Geometry-Preserving NNs (manifold ML, JPmHC sibling) |
| 4.4 | `native-low-bit-apple-silicon-synthesis.md`                        | Kimi-K2 (primary fold — Phase 6/8 weight-streaming target + Linus-flavored 1-bit candidate); Bonsai 1-bit announcement |
| 4.5 | `memory-synthesis.md`                                              | Bush "As We May Think" historical anchor for Garrison/Mughal lineage                                                |
| 4.6 | `safety-alignment-privacy-synthesis.md`                            | Anthropic RSP v3.0 + Claude's Constitution (policy-stance benchmarks)                                               |
| 4.7 | `skills-and-practices-synthesis.md`                                | How-Anthropic-teams-use-Claude-Code; claude-code-guide repo                                                         |
| 4.8 | `agentic-systems-synthesis.md`                                     | Trading-R1 (extends TradingAgents thread); Kimi-K2 SOTA tool-use benchmarks (cross-link from native-low-bit fold)  |

Each fold-in PR should also embed any inline figures from `context/pics/` that illustrate the topic (per the
fold-in plan): Bonsai/PrismML figures and Flash-MoE scatter into PR 4.4; oai-o1-context-window /
quadratic-wall / crispr-memory into PR 4.5 + the Bush PDF.

---

## Tier 5 — LLM-hardware-design synthesis authoring (gated on Tier 1+2 QiMeng completion)

Per [`qimeng-category-promotion.md`](qimeng-category-promotion.md) §"What remains to be done" tasks 4–5:

- **Task 5.1:** Author `docs/syntheses/repo-clusters/g12-llm-hardware-design.md` covering 4 QiMeng repos
  (CodeV, MuPa, SALV, cpu-v1) with Sketch2Simulation as cross-thread reference exemplar.
- **Task 5.2:** Author `docs/syntheses/llm-hardware-design-synthesis.md` framed around the **idea → reality**
  spine.
- **Task 5.3:** Update synthesis-cell in INDEX entries from `_Pending llm-hardware-design_` to
  `[llm-hardware-design](...)` for all 15 QiMeng paper-notes (5 already-in-corpus + 10 from Tier 1) and the
  4 repo-notes (cpu-v1, CodeV, MuPa, SALV).
- **Task 5.4:** Refresh `docs/landscapes/synthesis-landscape.md` to add the 15th thematic synthesis + the 12th
  cluster, update hub matrix, refresh date stamp.

---

## Tier 6 — B14 notes-consistency re-bin (gated on Tier 5)

Per `qimeng-category-promotion.md` §"What remains to be done" task 6: re-bin the QiMeng paper-notes from B9
(where the 2026-05-04 fan-out mis-binned them) into a new B14 in the next notes-consistency sweep spec.
Refresh Connections sections in the affected notes (paper + repo) to point at the new syntheses.

---

## Dispatch pattern

**Pattern:** Sequential agent dispatch with file-level partitioning, per CLAUDE.md §Worktree fan-out discipline
("When not to use worktrees"). Each agent writes non-overlapping files on this shared branch
(`agent/context-foldin-fanout`); Maestro reviews and commits each agent's output. **No worktrees.**

**Canary first.** Per CLAUDE.md §Agent fan-out: probe permissions first. The first dispatched agent should be a
simple paper-note authoring task (e.g., Task 1.1 — QiMeng-GEMM) that exercises Read on a PDF, Write on a new
paper-note path, and exits cleanly. If the canary completes, fan-out proceeds.

**Pair-aware dispatch.** Pairs (1.2+1.4 sharing repos/CodeV; 1.11+2.4 ProtiCelli; 1.12+2.5 TranscriptFormer;
1.13+2.6 Kimi-K2) should be assigned to a single agent that authors both notes in one pass, with cross-references
present in both. This is more efficient than splitting and avoids inter-agent coordination on the cross-reference.

**Commit cadence.** Maestro commits after each agent's output (not after each note within an agent's output —
i.e., a paired-pair agent commits both notes together). Atomic commit per resolved task.

**Format check.** PostToolUse hooks (`prettier --write`) fire on Edit/Write. If a sub-agent's environment doesn't
propagate hooks, Maestro runs `prettier --write` manually before committing per CLAUDE.md §Sub-agent hook bypass
flow.

---

## Estimated wall time

Per CLAUDE.md §Measure, don't just estimate, log start/end timestamps per tier and variance vs. estimate.

| Tier | Task                              | Estimate          |
| ---- | --------------------------------- | ----------------- |
| 1    | 13 paper-notes                    | 4–6 hours         |
| 2    | 7 repo-notes                      | 2–3 hours         |
| 2b   | 2 ecosystem repo-notes            | 30–60 min         |
| 3    | INDEX backfill                    | 30 min (mechanical) |
| 4    | 8 synthesis fold-in PRs           | 3–5 hours         |
| 5    | New synthesis authoring           | 4–6 hours         |
| 6    | B14 sweep                         | 1–2 hours         |
| —    | **Total**                         | **15–24 hours**   |

Likely a multi-session arc. Realistic anchor (per the flash-moe / measure-don't-estimate convention applied to
prior fan-outs): expect ~50% overrun on the optimistic end → plan for ~22–35 hours.

---

## PR plan

Per CLAUDE.md §PR summary discipline, the eventual PR(s) opening from this branch follow the uniform template.
Anticipated PR shape: **one PR per tier** (or per coherent slice within a tier), **not** one mega-PR. Suggested
PR boundaries:

- **PR-A:** Tier 1 + Tier 2 + Tier 2b + Tier 3 (paper-notes + repo-notes + INDEX).
- **PR-B:** Tier 4 (8 synthesis fold-ins; could be one PR or 8 small PRs — Dan's call at review time).
- **PR-C:** Tier 5 (new synthesis authoring + landscape refresh).
- **PR-D:** Tier 6 (B14 sweep).

If the branch grows too large for one batch review, split into PR-A first and rebase the rest on origin/main
after PR-A merges, per CLAUDE.md §State verification across context boundaries.

---

## Status

- 2026-05-09 17:38: spec authored on `agent/context-foldin-fanout` (base SHA `577ebb74ceacb218768c5d15f071270a8d7e1f79`).
- _Pending: canary dispatch (Task 1.1)._
- _Pending: full fan-out._
