# 2026-05-21 — Fix-and-polish session summary

**Span:** 2026-05-19 → 2026-05-21 (continuation from MVP-shipped state).
**Maestro:** Claude Opus 4.7 via Claude Code.
**Outcome:** v0.5.0 reveal-prep arc effectively complete; ~30 PRs landed across the arc;
hermetic suite grew 102 → 695 tests; pmetal v0.5.0 binaries rebuilt; KB + Linus + DEC-0061
internet-reframe + entity grounding all in main. KB pipeline run remains as the last
Dan-side blocker for the Streamlit UI to come fully alive pre-reveal.

## Pre-execution context

Session entered with main at `d75ab68` immediately post-MVP (v0.4.0 tag). Open items at
session start, per the compaction handoff in the previous arc:

- **PRs and reviews:** all 16 MVP PRs merged; #83 (first bug-fix PR) shipped.
- **Strategic frame:** v0.5.0 targeting the 2026-05-25 Agora hackathon coordinated reveal
  alongside KnowledgeBase + Archimedes.
- **Discipline pin:** pytest-before-merge codified in PR #84 as a hard rule.
- **Dan's posture:** "burn it up baby" — high-velocity execution, reserve strategic-
  review attention for landing decisions only.

## Step 1 — Pytest discipline + coverage push wave 1 (2026-05-19 morning)

- PR #84: codified pytest-before-merge as a hard discipline rule in CLAUDE.md Branch
  discipline section.
- PR #85: `sandbox/fs.py` 0% → 100% coverage (23 hermetic tests).
- PR #86: `memory/episodic.py` 35% → 100% (66 tests).
- PR #87: `tools/registry.py` 62% → 100% (54 tests).
- PR #88: `memory/audit_log.py` 53% → 100% (46 tests).

**Pattern validated:** parallel agents in isolated worktrees produce ≥95% coverage on
specified modules in 2-3 minutes wall time each. Canary-then-fanout was the load-bearing
discipline (PR #85 first, then #86-#88 in parallel).

## Step 2 — KB hackathon prep (2026-05-19 afternoon)

- KB PR #1 (dbrowneup/KnowledgeBase): reveal-ready README rewrite + prominent AGPL
  documentation (Dan: keep PyMuPDF; document AGPL loudly).
- PR #89: LX-1 paper-qa Phase 2c integration — 172-stmt `linus.knowledge.paperqa`
  module, 4 registered tools, citation-to-provenance mapping, 50 hermetic tests.
- PR #90: SUB-1 KB submodule pin bump + CLAUDE.md "Metal Toolchain" Known Library
  Quirk entry + 2026-05-19 KB hackathon prep spec.
- PR #91: Linus README rewrite for the reveal.
- PR #92: LX-2 Streamlit page 7 (paper-qa Q&A UI).
- PR #93: Q3 — `/healthz` `effective_state` + `degradations[]` extension (DEC-0060).
- PR #94: Q1 — `linus.knowledge.rigor` grounding gate (DEC-0059) + `BuiltinEntityLookup`
  stub.
- PR #95: DECISIONS.md + ROADMAP.md refresh; DEC-0060 ADR landed.

**Pmetal v0.5.0 binaries rebuilt** in this window — required `xcodebuild -runFirstLaunch`
+ `xcodebuild -downloadComponent MetalToolchain` from Dan to fix a macOS-update-induced
missing Metal Toolchain. Documented in CLAUDE.md as a Known Library Quirk.

## Step 3 — Archimedes cross-pollination + DEC-0059 amendment (2026-05-19 evening)

- Q1 reframing from "quantitative rigor" (Archimedes-style DSR/CSCV/walk-forward) to
  "grounding gate" — scientific surface first; Archimedes-style quant rigor remains as a
  post-reveal extension point documented in DEC-0059.
- PR #102: rigor wiring — paperqa.answer auto-gates every answer, `rigor.check`
  registered as Linus tool, Streamlit badge inline.
- PR #103: `entity_kb.py` KB-derived entity lookup (`KBEntityLookup` +
  `ChainedEntityLookup` composite, `default_kb_lookup` factory; entities resolved from
  Dan's actual reading corpus via REBEL+SciSpacy KG outputs).
- PR #104: DEC-0059 amendment documenting the entity backend graduation + auto-gate
  wiring shipped in PRs #102/#103.

## Step 4 — Coverage push wave 2 (2026-05-20)

- PR #96: `tools/kb_tools.py` 48% → 100% (24 tests).
- PR #97: `knowledge/adapter.py` 45% → 100% (40 tests).
- PR #98: New `POST /v1/tools/{name}/invoke` route + LX-2 paper-qa page refactor to use
  it (eliminated the prior steering-prompt + marker-block hack).
- PR #99: `server.py` 78% → 99% (59 tests).

## Step 5 — Internet reframe (2026-05-20)

Dan's strategic call: local-first remains the major theme, but tools may use the
internet when available. Full framework + first instance in v0.5.0.

- PR #105/#106/#107/#108: four parallel bug-sweep reports, surface-only (no fixes),
  publishing to `docs/bug-sweeps/`. 53 findings total across the four sweeps.
- PR #109: DEC-0061 ADR + `network_policy` attribute on tool registration +
  `network_egress` field on audit log + two new `/healthz` degradation paths.
  618 hermetic tests passing post-merge.

## Step 6 — Fix dispatch wave 1 (2026-05-21 morning)

Critical-severity findings from the bug sweep:

- PR #111: `SessionStore` C1 (`append_message` TOCTOU race on idx) + C2 (`get_default_store`
  check-then-init race). Atomic `INSERT...SELECT` + double-checked locking +
  threading.RLock. 3 new concurrent-write tests.
- PR #112: `KBEntityLookup` H1 (lazy-parse race; double-checked locking) +
  `ChainedEntityLookup` H3 (per-backend exception catch + skip). 4 new tests.
- PR #110: `SandboxFS.write` H1 + M1 (TOCTOU + dangling-symlink escape). Lstat-walk
  ancestor chain + symlink-on-write refuse. 5 new tests.
- PR #113: `entity_ncbi.py` — first `online_optional` tool (DEC-0061's load-bearing
  first instance). NCBI Gene + UniProt + ChEBI routing with SQLite cache,
  rate-limit throttling, name validation, audit-log egress logging. 46 new tests
  (all hermetic, HTTP fully mocked).

PR #113 required a manual rebase against #112 (one-line `import threading` conflict
in `entity_kb.py`). Post-merge: 676 hermetic tests passing.

## Step 7 — Fix dispatch wave 2 (2026-05-21 afternoon)

Remaining high-severity findings:

- PR #114: `_AdapterPaperLookup.get_page_count` H2 (double SQLite round-trip on every
  citation — fixed via per-instance cache) + `KnowledgeBaseAdapter` H4 (no `__del__`
  finalizer — added). 9 new tests.
- PR #115: `spawner.py` H1 (broad-except safety net) + `episodic.py` H2 (IN-list
  chunking past SQLite 999-param limit) + H3/H4 docstring fixes. 3 new tests.
- PR #116: `server.py` H-1 (streaming session writes lost on client disconnect — try/
  finally + idempotent partial-write) + H-2 (tool-call messages not persisted to
  session — full transcript persistence). 7 new tests.

Post-merge: **695 hermetic tests passing in 7s**.

## Step 8 — Last-mile prep (2026-05-21 evening)

- PR #117: KB hardcoded-paths fix spec for v0.6.0 — documents the path-constant
  inventory + proposed `papers_analysis/paths.py` refactor.
- This PR (in-flight): `experiments/2026-05-21-run-kb-pipeline.sh` (operational runner
  script for the `papers` env) + `docs/specs/2026-05-21-env-architecture-layered.md`
  (Option C env-layering spec for v0.6.0) + this session summary.

## Lessons learned (write-back candidates)

### CLAUDE.md

- **Editable installs + worktrees collide on import resolution.** When `pip install -e
  .` was run from the main checkout, the resulting `.pth` file points at main's `src/`
  — so `python -c "import linus.foo"` in a worktree resolves to MAIN's code, not the
  worktree's. Every fix agent in this arc hit this and recovered via
  `PYTHONPATH=<worktree>/src pytest ...`. CLAUDE.md should document this as a
  Known-Library-Quirk-adjacent worktree discipline rule.

- **Worktree-agent `git pr merge --delete-branch` requires worktrees dismantled
  first.** Already known; reinforced this arc.

- **Cherry-pick recovery from a contaminated main is the universal pattern.** At least
  two agents this arc accidentally committed to main (Edit-tool path-resolution
  quirk); both recovered via the documented cherry-pick-to-rescue-branch + reset-main
  pattern.

### ROADMAP.md

- Phase 2 (Linus MVP) is now effectively complete; v0.5.0 is the reveal release.
- New seeded items for v0.6.0: KB hardcoded-paths fix (DEC-NNNN spec), env-architecture-
  layered (DEC-NNNN spec), entity_ncbi promotion to error-severity (depends on real
  reference backend coverage), v0.5.0 bug-sweep mediums.

### DECISIONS.md

- DEC-0059 (grounding gate), DEC-0060 (loud degradation), DEC-0061 (network policy
  framework) all landed this arc.
- Q2 signed-audit-slice (anchor.py) remains seeded for post-reveal.

## Estimated wall time vs actual

The original 2026-05-19 hackathon-prep spec estimated ~6 days of human-time work for
the reveal arc (KB-1 + LX-1 + LX-2 + SUB-1 + dry-run). Actual:

| Item | Estimated | Actual |
|---|---|---|
| KB-1 README + AGPL | ~half-day | ~10 min (single agent, no Dan intervention) |
| LX-1 paper-qa integration | ~2 days | ~25 min (single agent) |
| LX-2 Streamlit page | ~half-day | ~40 min (single agent + #98 refactor) |
| SUB-1 + housekeeping | ~half-day | ~5 min (Maestro-direct) |
| Plus: Q1 + Q3 + entity_kb + entity_ncbi + bug-sweep + fixes | NOT estimated | ~6 hours wall time |
| **Total arc** | ~6 days | **~12 hours wall time across 3 calendar days** |

**Key insight:** I (Maestro) systematically overestimate implementation time. Parallel
agent dispatch with worktree isolation reduces real wall time by ~5-10x on
well-specified tasks. Future planning should use empirical anchors:

- Single bug-sweep agent (read-only report): 5-7 min wall time, ~2.5% Anthropic budget.
- Single fix agent (code + tests + PR): 8-12 min wall time, ~3-4% budget.
- Single feature agent (new module + tests + PR): 15-25 min wall time, ~5-7% budget.
- Maestro-direct doc PR (spec, ADR amendment): 2-5 min, ~1% budget.

Reference this when sizing future arcs.

## Outstanding items for next session

1. **KB pipeline run** — Dan executes the new `experiments/2026-05-21-run-kb-pipeline.sh`
   script in his `papers` conda env. Expected wall: 1.5-3 hours full pipeline; the
   Streamlit pages 2-6 come fully alive once outputs land.
2. **Streamlit UI smoke test** — Dan exercises the marquee demo path in-browser after
   KB outputs exist. Surface any new bugs.
3. **Demo dry-run** — walk through `docs/demo-script-2026-05-25.md` end-to-end on the
   real system once Streamlit is fully working.
4. **v0.5.0 line-drawing** — declare reveal-ready after Streamlit verifies. Remaining
   bug-sweep mediums (~20 across the four sweeps) can defer to v0.5.1.
5. **Open PRs**: this PR (#TBD — pipeline runner + env spec + summary). Possibly #100
   if not yet merged.

## Suggested next steps

In likely order of impact:

1. **Compact this conversation** — substantial context used; a session summary now
   keeps the load-bearing artifacts accessible after compaction without dragging
   intermediate tool-result noise into the new context window.
2. **Pipeline run** (Dan-owned, ~1.5-3 hours wall, mostly background).
3. **Streamlit smoke test** (Dan-owned, ~15-30 minutes).
4. **Declare v0.5.0 ready** if smoke test passes.
5. **Tag v0.5.0** + push to remote.
6. **Final asset polish** (logo placeholder → real image; Archimedes link → real URL).

## Memory write-back

This session deserves at least one new cross-session memory entry capturing the
empirical wall-time anchors (under "feedback" type — guidance for future Maestro
about how to size estimates). The hackathon plan memory and v0.4.0 state memory
remain accurate; v0.5.0 will need an analog when it ships.
