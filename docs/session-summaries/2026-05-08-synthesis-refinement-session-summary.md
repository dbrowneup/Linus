# Synthesis Refinement Session Summary (2026-05-08)

## Pre-execution context

Coming out of the recent paper-note and repo-note cleanup arc (notes-consistency sweep, 2026-05-07), the 25 syntheses in
`docs/syntheses/` had drifted slightly stale relative to (a) the cleaned-up underlying notes and (b) the DEC-0044
through DEC-0054 ADRs that landed 2026-05-06. Dan also flagged a meta-pattern: manual question lifecycle management is
becoming the bottleneck (~70 candidate questions across 25 syntheses, dedup against the existing R2 working set, decide
promotion tier per round).

The decision was to fan out Sonnet 4.6 sub-agents — one per synthesis, 25 total — to refine each in place within an
explicit edit budget, surface candidate questions for an R3 promotion, and let Maestro consolidate afterward. PR #27 is
the result.

## Step 1 — Plan and spec

Wrote `docs/specs/synthesis-refinement-spec.md` codifying:

- Per-agent task contract: read target synthesis, cited notes, both landscape docs, top-/answered-questions, then apply
  targeted refinements (weave-in / trim / sharpen / propose cross-links).
- Edit budget: ≤30% per section, escalate larger changes to Maestro.
- Cross-reference rule: propose-only; agents do not edit anything outside their target file.
- Canary phase: 2 agents on representative syntheses (memory + g4-memory) before the full 23-agent fan-out.
- Output: per-agent Markdown report with diff summary, refinements per section, stale content flagged, candidate R3
  questions, proposed cross-references, escalations, edit-budget status.

Spec committed on branch `agent/synthesis-refinement` as `b51e0f7`.

## Step 2 — Canary fan-out

Two canary agents dispatched in parallel: memory-synthesis.md and repo-clusters/g4-memory.md (tightly-coupled pair).
Both returned high-quality reports:

- Edit budgets respected (~5–28% per section, no silent overruns).
- DEC-0052 Layer D rename propagated correctly across both syntheses.
- Cross-references between the two coherent (each correctly identified the other as needing updates).
- R3 candidates concrete and non-duplicate of R2-NN (verified against `top-questions.md`).
- Escalations appropriately raised (~3–4 per agent) rather than silently exceeded.

One typo fixed inline ("synthesis surface a gap" → "synthesis surfaced a gap"). Spec count corrected (13 thematic
remaining + 10 cluster = 23, not 12+10). Otherwise canary passed full-fan-out criteria.

## Step 3 — Full fan-out

23 Sonnet 4.6 agents dispatched in parallel — file-level partitioning on the shared `agent/synthesis-refinement` branch
(no worktrees needed since each agent edits a non-overlapping file). Total wall time ~6–8 minutes for the parallel
batch. All 23 returned with valid reports following the spec structure.

Aggregate stats: +1330 / −1014 lines across 25 syntheses + spec. Most of the churn is prettier line-rewrapping on
touched files; the actual semantic deltas are smaller.

## Step 4 — Maestro consolidation

Single thorough pass per Dan's selection. Three consolidation streams:

**Approved escalations (~10 small fixes applied):**

- g4-memory: 3-paragraph Layer numbering note added to "What this document is" (DEC-0052 explanatory).
- memory: agentic-systems cross-link added in Layer D section.
- agentic-systems: Thread 1 closing sharpened from recommendation to DEC-0050 decided language; QuantAgent
  min/max-pipeline pointer added to "What this document is" framing.
- g6-mcp-tools: trigger line updated for 11-repo scope.
- g8-sci-agents: intro stale sentence updated to DEC-0044 resolved.
- infra-foundations: world-model closing updated to S35 resolution.
- g3-wiki-patterns: Phase 2 quality gate sentence updated to DEC-0019 framing.
- g9-bio: memory cross-reference updated to five-layer/Layer D.
- generative-biology: Phase 7 skills section pointed at biology-phase7-roadmap spec.
- g7-harnesses: origin H3 expanded with v0.2.1 benchmark numbers (96% fewer tokens, Recall@5 88.0%, LoCoMo10 67.3%),
  macOS Tahoe 26.x compile/Metal-init caveat, and `Arc<dyn EventEmitter>` capability-boundary pattern.

**Inter-synthesis cross-references applied:**

- biological-foundation-models gained reciprocal BioReason-Pro cross-link to function-annotation-discovery.
- agentic-systems gained the QuantAgent min/max-pipeline cross-link to g10-finance.
- (Others surveyed but deferred; the high-priority ones above are the ones that change navigability now.)

**Landscape doc refresh:**

- Both landscape docs gained a 2026-05-08 refresh-pass note in the header.
- synthesis-landscape.md: ~13 row updates absorbing post-2026-05-05 ADR resolutions (humans-teams-performance /
  llms-in-science / generative-biology / biological-foundation-models / safety-alignment-privacy / agentic-systems /
  entrepreneurship in the thematic table; g6-mcp-tools / g8-sci-agents / g10-finance / g11-agent-frameworks in the
  cluster table).

## Step 5 — R3 sweep promotion

Harvested candidate questions from all 25 sub-agent reports. ~70 candidates total, deduped to ~50 unique, curated to 27
promoted items per Dan's selected size:

- Tier 1: 8 items (block Phase 1/2a — supply-chain execution, agentmemory hook taxonomy, skill format spec, Phase 1c
  reconciliation, AlphaGenome spike, DEC-0047 amendment, worktree fan-out decision, benchmarking ADR).
- Tier 2: 19 items (architectural shape across Phase 2–7).
- Tier 3 reservoir: 11 lower-priority items.

Promoted items appended to `top-questions.md` as the R3-NN section, mirroring the R2 pattern. One prettier-induced
formatting bug detected and fixed (R2-03's `+` mid-sentence got line-wrapped to a new line and prettier interpreted it
as a list marker, rewriting `+` → `-` and escaping the surrounding italic markers; substituted `;` to remove the
ambiguity).

## Step 6 — Question-lifecycle stub

Wrote `docs/specs/question-lifecycle.md` as a placeholder capturing Dan's meta-observation that manual question
lifecycle management is becoming the bottleneck. The shape sketched: typed-claim records on the episodic substrate
(Layer C), Worker write-back as the surfacing mechanism, periodic Maestro promotion. Not designed; not scheduled. A
handle for after Phase 2 episodic memory ships.

## Step 7 — Commit, push, PR

Three logical commits on the existing `agent/synthesis-refinement` branch:

1. `9f55f32` — synthesis refinements (25 files + spec).
2. `d348cb0` — landscape refresh (2 files).
3. `42cb443` — R3 promotions + question-lifecycle stub (2 files).

Pushed to origin; PR #27 opened against main with the standard PR summary template.

## Lessons learned (write-back candidates)

### Sonnet 4.6 is sufficient for synthesis refinement work — saved meaningful Opus budget

_Destination: CLAUDE.md "Maestro budget discipline" or a new "Worker model selection by task class" entry._

The canary verified that Sonnet quality is fully adequate for "absorb new content into existing prose under an edit
budget" work. R3 candidate-question generation was concrete and actionable, on par with what Opus would produce for this
task class. The cost differential is meaningful at scale (25 agents × full doc reads × full reports). Rule of thumb:
tasks that synthesize+integrate within an existing document framework are Sonnet territory; tasks that require novel
architectural reasoning or cross-cutting design judgment remain Opus territory.

### Prettier mid-prose `+` → `-` corruption recurrence

_Destination: CLAUDE.md "Known Library Quirks" — the existing entry on mdlint should be sharpened to also mention
prettier under specific wrapping conditions._

CLAUDE.md says prettier "distinguishes from in-prose `+`" at list-marker normalization. That's true for stable
formatting, but prettier's wrap step can put a `+` at start-of-line on the next line of an italic span, at which point
the marker-position heuristic fires. The R2-03 entry in top-questions.md hit this. Mitigation: avoid `+` in prose that
prettier may wrap; prefer `;` or `,`. Rule of thumb: any time a list-item bullet contains `_(... + ...)_` italics,
replace `+` with `;` before committing.

### File-level partitioning is the right pattern for 25-way synthesis refinement

_Destination: the worktree-fan-out discipline section of CLAUDE.md already covers this; this session is empirical
confirmation that the simpler pattern works at 23-way parallelism with non-overlapping files._

23 Sonnet agents writing to 23 distinct files on a shared branch worked cleanly. No worktree overhead, no base-SHA
drift, no cherry-pick consolidation. The Edit-tool path resolution issues that motivate worktrees did not surface
because each agent's writes targeted only its assigned file. The cross-reference rule (propose-only, Maestro
consolidates) prevented races on shared files (landscape docs, top-questions.md).

### Question-lifecycle is becoming a real Linus capability, not just a workflow

_Destination: question-lifecycle.md (already captured); long-term destination is a Phase 3+ design spec._

Dan's observation during the planning conversation crystallized into a concrete artifact. The shape is now visible:
typed claim records, episodic substrate, Worker write-back as the emit mechanism, periodic Maestro promotion. The
productization angle (structured-question-management for technical teams) is plausible enough to belong in the
entrepreneurship synthesis when revisited.

## Outstanding items for next session

- **R3 Tier 1 walk** when Dan has ~2 hours available. R3-01 (supply-chain execution) and R3-04 (Phase 1c spike model
  list reconciliation) are both 30-minute items and unblock Phase 1 close.
- **Larger escalations deferred during consolidation** — the synthesis-refinement reports flagged ~6 sections that
  want >30% rewrites for full factual currency (memory's open-questions section, llm-wiki's Section 3 alignment with
  g2/g3 verdicts, function-annotation-discovery's "Implications for Linus benchmarking" trim, generative-biology's Phase
  7 skills sequencing reconciliation with biology-phase7-roadmap, infra-foundations world-model closing alternative
  framing, g11 Phase 2a skill-format expansion). Track as a follow-up Round 4 candidate or fold into the next quarterly
  curation pass.
- **Indexes hygiene** — g6 batch 2 repo-notes (markdownify-mcp, codebase-memory-mcp, vanna, ExtractThinker, rendergit)
  and 12 infra-foundations paper-notes need rows in the respective INDEX.md files. Mechanical.
- **Question-lifecycle design pass** — when Phase 2 episodic memory ships, return to `docs/specs/question-lifecycle.md`
  and turn the placeholder into a real design.

## Suggested next steps

1. Merge PR #27 once Dan reviews.
2. Walk R3 Tier 1 in a focused session (each item is 15–60 minutes; suggest batching by domain — supply-chain +
   benchmarking ADR + Phase 1c reconciliation as one infrastructure session; AlphaGenome spike + DEC-0047 amendment as a
   biology session).
3. Schedule index hygiene as a quick Worker task (mechanical INDEX.md row additions).
4. Defer larger escalations to next quarterly curation review (2026-08-01).

## Estimated wall time vs actual

- Planning conversation + spec drafting: estimated ~30 min, actual ~25 min.
- Canary fan-out + review: estimated ~30 min, actual ~25 min (2 parallel agents, ~6–8 min wall).
- Full fan-out (23 parallel agents): estimated ~30–45 min wall, actual ~10 min wall (Sonnet faster than estimated;
  parallelism worked cleanly).
- Maestro consolidation (escalations + cross-refs + landscape + R3 harvest): estimated ~60 min, actual ~75 min (R3
  curation took longer than expected; 70-candidate dedup + tier-assignment is non-trivial).
- Commit batches + PR + session summary: estimated ~15 min, actual ~10 min.
- **Total estimate: ~3.0 hours; actual: ~2.5 hours.** ~17% under estimate. Sonnet's speed advantage on the 23-agent
  parallel batch was the dominant factor.
