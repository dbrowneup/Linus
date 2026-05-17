# Multi-PR consolidation arc — session summary

**Window:** 2026-05-10 through 2026-05-16 (multi-day session arc) **Author:** Maestro (Dan + Claude Code)
**Companion doc:** [`2026-05-16-wave2-fanout-session-summary.md`](2026-05-16-wave2-fanout-session-summary.md) — that doc
covers the 2026-05-16 Wave 2 parallel-fanout phase in detail; this doc gives the bigger picture across the full
multi-day arc.

## Pre-execution context

Coming off PR #28 + #29 (the 2026-05-09 context fold-in arc), the corpus had matured to 114 paper-notes / 109
repo-notes / 26 syntheses, but residual gaps and Dan's growing list of new material made it clear another cleanup
pass was needed before transitioning from planning mode into build mode. The 2026-05-12 implementation plan
(`docs/specs/2026-05-12-linus-implementation-plan.md`) had been authored as the bridge: "the gap between
'well-specified' and 'shipping' is the entire current risk — planning more doesn't reduce it, coding does."

This session arc closes that planning chapter and ships the first concrete Phase 2a code substrate. It also surfaces
the load-bearing operational lesson of the project so far: shared-checkout parallel agents collide catastrophically;
worktree isolation is mandatory.

---

## Step 1 — PR 30 cleanup (2026-05-10)

Multi-tier batch closing residual gaps from PR #28/#29 and landing the Bin A + Bin B repo additions deferred from the
Canteen blog landscape note.

- **Tier 1 — 4 paper-note promotions:** Trading-R1 (`2509.11420v1`), Geometry-Preserving NA (`2602.03082v1`), Lipman
  Flow Matching (`2210.02747`, REFERENCE-category), Letta/MemGPT (`Letta-2310.08560`, paired-repo hybrid filename).
  The Letta MemGPT PDF was downloaded fresh from arxiv (Packer et al., UC Berkeley, v2 Feb 2024). Trading-R1 is the
  second canonical typed-structured-prediction example alongside BioReason-Pro.
- **Tier 2 — 2 orphan pic embeds:** Git_Branching_Model.pdf linked from BRANCHING.md §Phase 3 Migration; the claw-code
  Architect/Executor/Reviewer orchestration diagram (`HE2psIVbcAA6VLz.jpg`) embedded in g7-harnesses synthesis.
  Pre-flight audit found 7 of 9 originally-flagged pics were already correctly embedded — earlier sweep agent's grep
  missed URL-encoded paths (`%20`).
- **Tier 3 + 4 — 8 repo clones + repo-notes:** Bin A (`Letta`, `rig`, `autogen`, `langgraph`, `x402`); Bin B (`goose`,
  `debate-or-vote`, `MiroFish-Offline`). All cloned `--depth=1`. Per-repo notes authored against the standard
  7-section convention.
- **Tier 5 — core-doc staleness pass:** Single Worker pass across 7 files (CLAUDE.md, DECISIONS.md, ROADMAP.md,
  VISION.md, ARCHITECTURE.md, GLOSSARY.md, BRANCHING.md). Counts refreshed to 118 paper-notes / 117 repo-notes / 27
  syntheses (15 thematic + 12 cluster, g1–g12).
- **Tier 6 — INDEX backfill:** 4 paper-note entries + 8 repo-note entries.
- **Tier 7 — curation log:** 2026-05-10 entry covering the PR 30 batch.
- **Tier 10 — landscape + top-questions accuracy audit:** Maestro single pass with all 27 syntheses loaded. Fixed
  Dan's flagged maestro-protocol path mismatch (`docs/maestro-protocol.md` → `docs/protocols/maestro-protocol.md`,
  moved from §"What's missing" to §"Closed during the resolution arc"). 3 new R4 top-questions promoted (R4-01
  Anthropic-compat HTTP / DEC-0005 amendment; R4-02 AGPL-fork posture; R4-03 `@x402/mcp` graduation).

**PR #30** — 27 files, +5975 / -598, 20 atomic commits. **Merged.**

**Cross-cutting findings worth flagging from Bin A/B review:**

1. **AutoGen is in maintenance mode.** Microsoft has redirected new development to Microsoft Agent Framework (MAF).
   AutoGen remains as frozen reference.
2. **Anthropic-compat 3-way convergence signal.** Letta + Kimi-K2 + Goose all ship Anthropic-compatible HTTP
   endpoints alongside OpenAI-compat — strong signal that DEC-0005 (OpenAI-only) earns a Phase 2a revisit. (This
   later seeded DEC-0056.)
3. **`@x402/mcp` is shipped**, not roadmap-only as the Canteen note suggested.
4. **rig has Ollama + MCP first-class** (corrects Canteen "no Ollama / no MCP" framing).
5. **MiroFish-Offline is AGPL-3.0** — license blocks code incorporation into Linus. (This later seeded DEC-0057.)
6. **debate-or-vote nuance:** round-0 vote often matches round-R debate in their NeurIPS results — sharpens the
   O(N) vs O(N²) coordination finding for Phase 3 spawner design.

---

## Step 2 — PR 31 filename discipline (2026-05-13/16)

Tier 8 of the original PR 30 spec, executed as its own PR. Tier 9 (Git LFS for `context/`) deferred separately after
the audit found `context/` is **844 MB**, not the ~50 MB the original spec estimated (papers alone are 775 MB,
cybersecurity adds 52 MB). GitHub Free's 1 GB LFS / 1 GB monthly bandwidth quota meant one full clone with LFS
would burn ~84% of monthly bandwidth — warranted a separate decision cycle on adoption posture.

- **DEC-0055 ADR** authored at `docs/adr/0055-filename-discipline-no-spaces.md` capturing rename rules (spaces →
  hyphens, apostrophes stripped, parens → hyphens, Unicode `→` → `to`, `:` → `-`, etc.), capitalization policy
  (preserve proper-noun caps), and scope boundary (not vendored `repos/`, not external URLs).
- **23 context/ renames** (gitignored, no diff). Including 3 newly-discovered files Dan had added since the
  original PR 30 audit: AI-Ready Biodata, Biomanufacturing MIT Brief, Biotechnology/RAND.
- **1 tracked `git mv`** — Horiike paper-note renamed; ` copy` suffix stripped; frontmatter `pdf:` field updated.
- **16 markdown files** updated; 34 total replacements across docs/. Handles bare-space, `%20`-encoded, and
  `%E2%80%99`-encoded (curly apostrophe) variants via a Python rename + reference-update script.

**PR #31** — 3 atomic commits, 18 files, +143 / -34. **Open.**

---

## Step 3 — Inventory of uncovered context/ materials (2026-05-13)

A Python inventory script cross-referenced `context/papers/` against `docs/paper-notes/INDEX.md`, `repos/` against
`docs/repo-notes/`, and so on. Initial findings overstated some categories — specifically the cybersecurity gap
(the script didn't look in `docs/cybersecurity-notes/` where coverage actually lives, so 7 of 14 cybersecurity files
showed as uncovered when they were already noted). Corrected reading:

- **2 truly uncovered papers** (`2512.24695v1`, `s41540-026-00683-6`)
- **11 new repos** Dan had added since PR 30
- **3 genuinely uncovered cybersecurity items** (NIST.SP.800-160v1, tomshardware Cursor/Claude incident,
  framework_v1.1 xlsx)
- **3 new biomed/policy notes** worth folding (AI-Ready Biodata, MIT Biomanufacturing, RAND Warfighter)

This inventory drove the scope of subsequent Wave 2 batches.

---

## Step 4 — Wave 2 fanout (shared checkout, 2026-05-16) — 7 agents

After PR 31 was teed up and the inventory was scoped, Maestro fired a 7-agent parallel fanout intended to maximize
session utilization. All agents operated on the SAME primary working tree on different branches.

**Outcomes:**

| Agent | Track | Outcome |
| ----- | ----- | -------- |
| A1 — Phase 2a FastAPI server (Item 1) | Code | **Landed clean** — PR #32 in ~5 min |
| A2 — Phase 2h memory v0 (Item 4) | Code | **Landed clean** — PR #35, but took ~70 min mostly fighting collisions |
| A3 — Phase 2c KB read-only adapter (Item 5) | Code | **Landed clean via cherry-pick recovery** — PR #34 on `agent/phase2c-kb-adapter-final` |
| A4 — Phase 1d Dan task suite (Item 2) | Code | **Landed clean** — PR #33 |
| B1 — Wave 2 corpus fold-in | Docs | Still in flight at session close |
| B2 — Cybersecurity gap close | Docs | **DIED** with cross-collision; commits ended up on 3 wrong branches |
| C1 — R4 ADRs batch (DEC-0056/57/58) | Docs | **Landed clean via cherry-pick recovery** — PR #36 on `agent/r4-adrs-take2` |

**The shared-checkout failure mode (load-bearing finding):** Multiple parallel Maestro-dispatched agents in the SAME
primary worktree COLLIDE on the shared `.git/HEAD` pointer. Symptoms observed:

- Branch switches reverting between an agent's bash calls
- Commits landing on sibling agents' branches instead of the agent's own
- Multiple recovery branches per agent (`-v2`, `-clean`, `-take2`, `-final` suffixes proliferating)
- One agent's untracked files getting accidentally staged into another agent's commits

3 of 7 agents recovered via the CLAUDE.md §"Cherry-pick to preserve, never reset to delete" discipline. 1 died
outright. 3 landed clean (A1 first, A4 with mid-stream cherry-pick recovery, no collision noticed; the rest had to
fight).

---

## Step 5 — Real Worker baseline data captured (PR #33 + #38)

Two PRs produced concrete Phase-1 data points on `qwen2.5-coder:7b` (Ollama, M1 Max; `qwen3:8b` not pulled locally
in this environment).

**PR #33 baseline run** (3 tasks, 55.75s total wall):

- Paper summarization: full-credit output on the MemGPT paper
- FASTA GC content: partial — generated script includes `N` in denominator (rubric says exclude)
- Title clustering: **only 36/50 titles assigned** (~28% silent drop)

**PR #38 first Maestro/Worker loop** (verdict: REJECT):

- Pass 1: Worker generated `SandboxFS` class. AST clean. 2/3 tests passed. Critical security failure:
  `os.path.join(repo_root, abs_path)` discards `repo_root` for absolute paths — Worker's `read('/etc/passwd')`
  leaked 9344 chars of `/etc/passwd`.
- Pass 2 (after Maestro feedback): Switched to `pathlib.Path` and `is_relative_to` — security tightened (both
  `/etc/passwd` smoke checks correctly raised) but dropped the allowlist and over-rejected the happy path because
  `Path.resolve()` resolves against CWD not repo_root. 1/3 tests passed.
- **Verdict: REJECT.** `src/linus/sandbox/fs.py` NOT added to the package. The calibration finding is the
  deliverable.

**Aggregate Phase 1 calibration:** `qwen2.5-coder:7b` is reliable for boilerplate, scaffolding, well-fenced
refactors. **NOT yet trustworthy for security-critical code or instructions with subtle constraints.** Phase 2
dispatch design needs explicit constraint enumeration in every Worker call, not "just make it good." Security
primitives stay Maestro-side, or require starter test scaffolds + pattern sketches in the spec.

---

## Step 6 — Wave 2 fanout (worktree-isolated, 2026-05-16) — 9 agents

After identifying the shared-checkout failure mode, Maestro switched to `isolation: "worktree"` for all subsequent
dispatches. Every agent got its own physical checkout under `.claude/worktrees/agent-<id>/`.

| Agent | Scope | Outcome |
| ----- | ----- | ------- |
| W1 — Stragglers v1 (caveman + symphony + swarm + SWARM paper) | Docs | Still in flight at session close |
| W2 — Tool registry scaffolding (Item 6) | Code | **Landed clean** — PR #40 in ~10 min |
| W3 — Cybersecurity redo (B2 follow-up) | Docs | **Landed clean** — PR #37 in ~30 min |
| W4 — First Maestro/Worker loop (Item 3) | Code | **Landed clean** with REJECT verdict — PR #38 in ~7 min |
| W5 — Synthesis rollup + pmetal/ANE correction | Docs | **Landed clean** — PR #41 in ~8.5 min |
| W6 — Stragglers v2 (pi + ElephantBroker + TrustResearcher) | Docs | Still in flight |
| W7 — Awesome-papers triage | Docs | Still in flight |
| W8 — Session summary (wave-2-specific) | Docs | **Landed clean** — PR #39 in ~15 min |
| W9 — Fresh landscape reconstruction (blind experiment) | Docs | Still in flight |

**Zero collisions in worktree mode.** Average wall time per worktree-isolated agent: ~13 min (vs ~40+ min for
shared-checkout agents, much of which was spent fighting collisions). The worktree-isolation hypothesis was
validated quantitatively within the same session.

---

## Step 7 — Stragglers Dan added mid-session

A practical reality of any high-throughput session: the operator's tab-cleaning gets interleaved with the agent
dispatch flow. Items captured during this session (some folded by W1/W6/W7, some pending for the next batch):

**Repos (7):**

- `caveman` (JuliusBrussee) — token-budget Claude Code skill (W1)
- `symphony` (openai) — OpenAI harness-engineering reference (W1)
- `swarm` (swarm-ai-safety) — multi-agent safety + emergent risk framework (W1, paired with paper 2604.19752)
- `pi` (earendil-works) — agent harness mono-repo (W6)
- `awesome-ai-agent-papers` (VoltAgent) — 363+ 2026 agent papers (W7 — gap analysis, not direct ingestion)
- `docling` (docling-project) — IBM document conversion library (pending)
- `PhysiGym` (Dante-Berth) — PhysiCell + Gymnasium RL on agent-based biology (pending)

**Papers (3):**

- `2604.19752v1.pdf` — SWARM (paired with `swarm` repo, W1)
- `2603.25097v1.pdf` — ElephantBroker: knowledge-grounded cognitive runtime (W6)
- `2510.20844v3.pdf` — TrustResearcher: multi-agent research ideation (W6)

---

## Step 8 — Operational discoveries worth capture

**1. Shared-checkout parallel agents are forbidden.** Use `isolation: "worktree"` or sequential dispatch with
file-level partitioning. Hard rule, going into CLAUDE.md §Worktree fan-out discipline.

**2. Cherry-pick recovery is the discipline of last resort and it works.** 3-for-3 in this session against the
collision chaos. The CLAUDE.md §"Cherry-pick to preserve, never reset to delete" section is load-bearing.

**3. Worker calibration is gold for Phase 2 design.** The 28%-input-drop on clustering and the 2-pass security
failure on sandbox code are concrete dispatch-design constraints, not just evaluation observations.

**4. Factual errors propagate.** The pmetal/ANE error (pmetal incorrectly attributed private-API usage) had spread
to 2 landscape locations. Quarterly factual-grep audit is the mitigation — captured in W8's session summary as
write-back to `docs/protocols/curation-protocol.md`.

**5. ADR numbering needs atomic reservation.** Wave 2 produced a numbering collision: `native-low-bit-apple-silicon-
synthesis.md` had "DEC-0055 seed" and "DEC-0056 seed" labels for Kimi-K2 fold seeds, but those numbers got CLAIMED
by PR #31 (filename discipline = DEC-0055) and PR #36 (Anthropic-compat = DEC-0056). The seeds need re-renumbering
or de-numbering during consolidation.

**6. Edit-tool absolute-path resolution to primary checkout** was empirically confirmed twice (W4 + W8). Inside a
worktree, the Edit tool resolves absolute paths to the registered primary worktree, not the agent's worktree. Use
`Bash(cd <worktree> && ...)` for file writes inside worktrees.

**7. PR `baseRefOid` caching artifact.** PR #40 cherry-picked from PR #32 + #34 since neither had merged yet —
GitHub will show all predecessor commits in #40's diff until #32 and #34 merge first. The recommended landing order
addresses this.

**8. Session usage budget protocol.** Captured separately (see Lessons learned below). Rough anchors: ~2-2.5% burn
per agent dispatch, ~0.7% per Maestro turn. Target ceiling 92%, hard ceiling 95%. Dan reports usage at planning
checkpoints since Maestro can't see it directly.

---

## PR ledger (state at session close)

| PR | Branch | Scope | Status |
| --- | --- | --- | --- |
| #30 | `agent/pr30-cleanup` | Cleanup + paper/repo-notes + landscape audit | **Merged** |
| #31 | `agent/pr31-rename-files` | DEC-0055 filename discipline | Open |
| #32 | `feature/phase2a-fastapi-server` | A1 — FastAPI server (DEC-0005) | Open |
| #33 | `feature/phase1d-dan-tasks` | A4 — Dan task suite v0 + baseline JSON | Open |
| #34 | `agent/phase2c-kb-adapter-final` | A3 — KB read-only adapter (cherry-pick rebuild) | Open |
| #35 | `feature/phase2h-memory-v0` | A2 — Memory v0 (SQLite + audit + hashing) | Open |
| #36 | `agent/r4-adrs-take2` | C1 — DEC-0056/57/58 (cherry-pick rebuild) | Open |
| #37 | `agent/wave2-cyber-redo` | W3 — Cybersecurity gap close (B2 redo) | Open |
| #38 | `experiment/first-maestro-worker-loop` | W4 — Maestro/Worker loop (REJECT verdict) | Open |
| #39 | `agent/wave2-session-summary` | W8 — Wave-2 session summary | Open |
| #40 | `feature/phase2a-tool-registry` | W2 — Tool registry (depends on #32 + #34) | Open |
| #41 | `agent/wave2-synthesis-rollup` | W5 — pmetal/ANE fix + Wave 2 rollup | Open |
| TBD | `agent/wave2-foldin-corpus` | B1 — corpus fold-in batch | In flight |
| TBD | `agent/wave2-stragglers` | W1 — caveman + symphony + swarm pair | In flight |
| TBD | `agent/wave2-stragglers-v2` | W6 — pi + ElephantBroker + TrustResearcher | In flight |
| TBD | `agent/wave2-awesome-papers-triage` | W7 — awesome-ai-agent-papers gap analysis | In flight |
| TBD | `experiment/fresh-landscape-reconstruction` | W9 — blind landscape reconstruction | In flight |

**Recommended landing order:** Foundationals first (#31, #32, #34, #35, #36); dependents next (#40 after #32 + #34
merge); docs/analysis as ready (#33, #37, #38, #39, #41).

---

## Lessons learned (write-back candidates)

### Lesson 1: Worktree isolation is mandatory for parallel agent dispatch

**Destination:** `CLAUDE.md` §Worktree fan-out discipline — add hard rule and reference W8's draft language.

**Content:** "When dispatching N>1 parallel agents from Maestro, ALL parallel agents MUST run in isolated worktrees
(`isolation: "worktree"` parameter on the Agent tool, or manual `git worktree add` for each agent). Shared-checkout
parallel agents collide on the single `.git/HEAD` pointer; branch switches revert mid-command; commits land on
wrong branches. The CLAUDE.md §"When not to use worktrees" exception for non-overlapping file work applies only to
SEQUENTIAL dispatch, not parallel."

### Lesson 2: Cherry-pick recovery works under hostile conditions

**Destination:** Reinforce existing CLAUDE.md §"Cherry-pick to preserve, never reset to delete" with Wave 2 worked
example (A3 → `-final`, C1 → `-take2`, B1 → recovered mid-stream).

### Lesson 3: ADR numbering needs atomic reservation

**Destination:** `CLAUDE.md` §Decision discipline (new sub-section or extension of existing).

**Content:** "When authoring an ADR, the agent reserves the next-free DEC-NNNN number atomically by writing the file
before any other agent can claim it. On collision (two agents both attempt to author the same DEC-NNNN), the agent
that wrote-then-committed first wins; the late agent picks the next-free number. 'Seed' labels in synthesis prose
(DEC-NNNN seed: ...) are placeholders, NOT reservations — they get reconciled at consolidation when the actual ADRs
land."

### Lesson 4: Phase 1 Worker calibration is a Phase 2 dispatch-design constraint

**Destination:** `docs/specs/2026-05-12-linus-implementation-plan.md` (follow-up note) AND `docs/specs/phase3-
spawner.md` (Phase 3 spawner spec input).

**Content:** "qwen2.5-coder:7b at Phase 1 calibration: ~28% silent input drop on clustering tasks; full failure on
security-critical code despite 2 revision passes. Phase 2 dispatch contract MUST specify constraints explicitly
(starter test scaffolds, pattern sketches, full type signatures) rather than relying on Worker inference. Security
primitives stay Maestro-side or move to higher-tier Workers in Phase 6+."

### Lesson 5: Quarterly factual-grep audit

**Destination:** `docs/protocols/curation-protocol.md` AND CLAUDE.md §Curation cadence.

**Content:** "At each quarterly curation review, grep landscape + synthesis + ADR docs for any claim about Apple
private APIs / unsupported APIs / reverse-engineering / license-incompatibility. Cross-check every match against
the source of truth (CLAUDE.md for project-level claims, the cited repo's actual license for license claims, the
referenced ADR for design claims). Factual errors that propagate are silent — only a directed audit catches them.
Triggered by the 2026-05-16 pmetal/ANE finding."

### Lesson 6: Session usage budget protocol

**Destination:** New `CLAUDE.md` §Session usage budgeting.

**Content:** "Maestro cannot see session usage % directly; Dan reports it at planning checkpoints. Target ceiling
92%, hard ceiling 95% (beyond which incurs extra-usage costs). Rough calibration anchors from 2026-05-16: ~2-2.5%
burn per agent dispatch, ~0.7% per Maestro turn. Refine anchors after every 2-3 sessions. When planning a batch,
compute: `remaining_budget = ceiling - current_usage`; `agent_slots ≈ remaining_budget / 2.5`. Defer the
lowest-priority items if the dispatch would exceed the ceiling."

### Lesson 7: Edit-tool path resolution inside worktrees

**Destination:** CLAUDE.md §Worktree fan-out discipline (extension of existing warning).

**Content:** Empirical confirmation from W4 + W8 in this session: Edit tool absolute paths resolve to the primary
worktree, not the agent's worktree. Mitigation: `Bash(cd <worktree-path> && cat > file <<EOF ... EOF)` for file
writes inside worktrees, or write to `./relative/path` after `cd`.

### Lesson 8: Mid-stream straggler discipline

**Destination:** `CLAUDE.md` §Engineering Conventions (new sub-section).

**Content:** "During a high-throughput session, operators (Dan) often clean up open tabs and add new material
mid-session. The pattern: 'X more repos added,' 'one more paper.' Maestro should: (a) identify the new material
quickly (1-2 bash calls), (b) acknowledge with placement intent (which synthesis/cluster), (c) batch them rather
than re-spawning per-item agents, (d) defer fold-in to a clean post-consolidation pass unless time/usage permits a
worktree-isolated straggler agent."

---

## Outstanding items for next session

1. **In-flight agents to land:** B1 (corpus fold-in), W1 (stragglers v1), W6 (stragglers v2), W7 (awesome-papers
   triage), W9 (blind landscape reconstruction). Notifications will arrive as each completes.
2. **Post-consolidation cleanup:** delete dead collision-artifact branches (`agent/wave2-r4-adrs`, `-v2`, `-clean`,
   `agent/r4-adrs-final`, plus `worktree-agent-*` auto-branches). Remote deletion of contaminated
   `origin/agent/r4-adrs-final` requires Dan's explicit approval.
3. **CLAUDE.md write-back PR:** capture lessons 1-8 above; use W8's draft language as the seed.
4. **DEC numbering reconciliation:** re-renumber or de-number the "DEC-0055 seed" / "DEC-0056 seed" labels in
   `native-low-bit-apple-silicon-synthesis.md` (those numbers are now claimed by landed ADRs).
5. **W9 reaction:** when the blind reconstruction lands, the `composition-notes.md` convergence/divergence verdict
   needs Dan-and-Maestro review before deciding whether the existing landscape structure needs reshaping.
6. **Straggler batch 3:** fold in `docling` + `PhysiGym` repos (the two Dan added at the very end of this session,
   after W6 was already in flight).
7. **W7 follow-up:** when the awesome-papers triage lands, the recommended HIGH-priority gap papers are the
   ingestion queue for the next corpus pass.

---

## Suggested next steps

1. **Wait for in-flight agents** to land notifications. Don't fire new work until current batch drains.
2. **Triage each PR** for diff cleanliness against `main`. Use the recommended landing order. Reconcile any
   contaminated diffs via cherry-pick (proven discipline this session).
3. **Merge in foundational order** — PR #31, #32, #34, #35, #36 first (foundationals); then #40 (tool registry
   diff clarifies after #32 + #34 land); then docs/analysis PRs.
4. **Author the CLAUDE.md write-back PR** as a single focused commit batch.
5. **Transition to Phase 2 build mode** — Items 1, 2, 4, 5, 6 from the 2026-05-12 implementation plan have all
   landed (or are in flight) via this session. Item 3 (Maestro/Worker loop) landed with REJECT verdict — the
   calibration is the deliverable. Item 7 (pmetal verdict ADR) is the next gate; explicitly needs Dan in the loop
   for hands-on benchmarking.

---

## Measure-don't-estimate close

**Estimated wall time vs actual** (best-effort across the multi-day arc):

- Phase A (PR 30): estimated ~5-6 hours; actual ~7-8 hours including Tier 10 audit + Dan reviews + multi-day spread.
  **Variance: ~30% over.** Most of the over-run was Tier 10 (landscape audit ran longer than the 1-2 hour estimate
  because the corpus had grown faster than the rollup).
- Phase B (PR 31): estimated ~3 hours; actual ~2 hours. **Variance: ~33% under.** The rename script approach was
  more mechanical than expected; Python's `pathlib.rename` handled Unicode cleanly.
- Phase D (Wave 2 shared-checkout): no formal estimate; ~40 min session time, of which an estimated 60% was spent
  on collision recovery work that wouldn't exist with worktree isolation.
- Phase E (Wave 2 worktree-isolated): no formal estimate; agents averaged ~13 min each; aggregate wall ~2 hours
  with high parallelism.
- Total session-arc duration: 6 days calendar (2026-05-10 → 2026-05-16); ~12-15 hours of active Maestro engagement
  across multiple session windows.

**Take-away for future estimates:** The 2026-05-12 implementation plan's "5-6 days calendar time" estimate for
items 1-7 was approximately correct — Items 1, 2, 4, 5, 6 all shipped (or are in flight) within that window. Item
3's REJECT verdict was a Phase-1 calibration finding, not a planning failure.
