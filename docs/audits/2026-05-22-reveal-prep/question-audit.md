# 2026-05-22 — Open-questions audit (pre-v0.5.0)

Delta audit of every numbered item in `docs/questions/top-questions.md` against shipped reality as of
`main@d75ab68` + the 2026-05-21 fix-and-polish arc. Goal: sync top-questions / answered-questions /
open-questions for the v0.5.0 public reveal on 2026-05-25.

## Audit table

| ID | Status | Resolution pointer | Suggested action |
|---|---|---|---|
| R2-01 | STILL OPEN | Tracked as **D1** in `docs/specs/2026-05-17-linus-implementation-plan-v2.md`. No ADR yet; bespoke wrapper is what shipped in `src/linus/server.py` + `src/linus/agents/spawner.py`. | leave-open; refresh-framing — note "interim resolution: bespoke wrapper shipped; ADR pending on whether to migrate" |
| R2-02 | STILL OPEN | No spawner code path beyond stub `src/linus/agents/spawner.py`; Phase 3 concern. | leave-open |
| R2-03 | PARTIALLY RESOLVED | Already annotated INFORMED 2026-05-18 via qwen3:8b + qwen3.6:27b baselines; tracked as **C2** in `docs/specs/2026-05-18-dan-manual-tasks.md`; awaiting DEC-0064 + new task definitions. | leave-open; annotation current |
| R2-04 | STILL OPEN | Tracked as **D2** (context-routing policy ADR) in implementation-plan-v2; not landed. Adjacent: in-context cap (DEC-0032) and 16K floor are operational but per-call routing policy is not yet codified. | leave-open |
| R2-05 | RESOLVED | Already annotated. Chat Completions shipped (`src/linus/server.py` PR #32); Open Responses deferred. SSE streaming added subsequently. | leave-as-resolved-annotation; no change |
| R2-06 | STILL OPEN | No in-house MCP server ships in v0.5.0; tool registry is direct-Python (`src/linus/tools/registry.py`). Decision not yet forced. | leave-open |
| R2-07 | STILL OPEN | Phase 3 KB tooling; deferred per implementation-plan-v2 line 428. | leave-open |
| R2-08 | STILL OPEN | Same defer as R2-07. | leave-open |
| R2-09 | STILL OPEN (de facto) | `src/linus/memory/episodic.py` shipped a single `(session_id, turn_id, parent_turn_id, segment, content_hash, content, trust_level, tags)` schema per DEC-0029 — NOT a `(blocks, links)` schema. The R2-09 question framing was about lifting openaugi's shape; that lift didn't happen and the question is moot in the framing as stated. | refresh-framing or drop — note "the Linus episodic schema went a different direction (DEC-0029); openaugi-style `(blocks, links)` lift is no longer pending" |
| R2-10 | STILL OPEN | Memory v0 shipped without vector search at all (`episodic.py` is SQL-only). Sqlite-vec vs Qdrant decision still future. | leave-open |
| R2-11 | STILL OPEN | DEC-0029 schema uses `trust_level` as int (binary in practice); Anamnesis weight model not adopted. | leave-open |
| R2-12 | STILL OPEN | Phase 1f spawner + planner ADR not landed. `agents/spawner.py` is stub-level. | leave-open |
| R2-13 | STILL OPEN | Despite the `2026-05-18-repo-pull-status.md` audit re-flagging R2-13 against TradingAgents 39-commit refresh, no ARCHITECTURE.md / ADR has codified `deep_think_llm` / `quick_think_llm` as a named Linus convention. Repo-note (`docs/repo-notes/TradingAgents.md`) still carries the recommendation. | leave-open; refresh-framing — note "refresh-flagged 2026-05-18; codification still pending" |
| R2-14 | STILL OPEN | Phase 6 RLVR oracles not surveyed. | leave-open |
| R2-15 | STILL OPEN | No Phase 7 sandbox decision; Moby/distroless paper-notes are reference only (per 2026-05-18 audit). | leave-open |
| R2-16 | STILL OPEN | Bio-Task Bench Intermediate plateau read not done. | leave-open |
| R2-17 | STILL OPEN | Phase 7 question; no work yet. | leave-open |
| R2-18 | STILL OPEN | Phase 7 question; S24 already chose BioReason-Pro as first skill but R2-18 framing of pole-comparison is broader and still open. | leave-open |
| R2-19 | STILL OPEN | Benchmark methodology call; no FutureHouse-philosophy adoption ADR. | leave-open |
| R2-20 | STILL OPEN | Phase 7 sequencing; settled as S31 default order but R2-20's "which gets resourced FIRST" remains. | leave-open |
| R2-21 | STILL OPEN | Energy column not implemented in `benchmarks/results/` JSONL yet. | leave-open |
| R2-22 | STILL OPEN | Despite DEC-0022 resolving the policy and `src/linus/memory/episodic.py` documenting single-writer hygiene + the multi-worker problem as deferred (lines 27-35 of episodic.py docstring), the implementation pattern (lease / branch-per-Worker) is unresolved. PR #108 H3 follow-up tracked in code. | leave-open; refresh-framing — note "DEC-0022 set policy; implementation pattern still open, tracked at episodic.py:27-35 + PR #108 follow-up" |
| R2-23 | STILL OPEN | KB substrate-level architecture; KnowledgeBase submodule choice (mutable wiki + atomic notes co-exist informally). | leave-open |
| R2-24 | STILL OPEN | `docs/EPISTEMIC-STANDARDS.md` does not exist. Still deferred per S22 + planning-update-spec.md:878. | leave-open |
| R2-25 | STILL OPEN | OpenBB-style dynamic activation not implemented; tool registry exposes all tools statically. | leave-open |
| R2-26 | PARTIALLY RESOLVED | E1 codified in VISION.md (2026-05-06). No formal architecture audit; KB AGPL surfaced 2026-05-19 (KB README + DEC-0057). Audit not formalized as a sweep. | leave-open; refresh-framing — note "AGPL surface called out via KB README + DEC-0057; broader architecture audit not done" |
| R2-27 | STILL OPEN | Phase 8b north star; long-horizon. | leave-open |
| R2-28..R2-70 (Tier 3) | STILL OPEN | Tier 3 reservoir; no activity intended. | leave-open |
| R3-01 | PARTIALLY RESOLVED | Already annotated; lockfile half still queued in v2 plan (F-tier follow-up; lines 336-355). | leave-open; annotation current |
| R3-02 | STILL OPEN | Tracked as **D3** in implementation-plan-v2 (lines 232-248). Not landed. | leave-open |
| R3-03 | STILL OPEN | SKILL.md committed (E6/S30); no Linus-native skill format spec authored. | leave-open |
| R3-04 | PARTIALLY RESOLVED | Already annotated INFORMED 2026-05-18 (27B failure datapoint). Reconciliation work not yet landed in `phase1c-spike.md`. | leave-open; annotation current |
| R3-05 | STILL OPEN | AlphaGenome spike not run. | leave-open |
| R3-06 | RESOLVED | Already annotated (false-premise; DEC-0047 already lists DeepSeMS under Tier B). | leave-as-resolved-annotation |
| R3-07 | PARTIALLY RESOLVED | Already annotated; dispatch-policy half resolved via CLAUDE.md "Worktree fan-out discipline" + further reinforced 2026-05-21 by "editable-installs + worktrees" lesson (session summary §Lessons learned). Orchestration-code-shape half still open. | leave-open; consider extending annotation with the 2026-05-21 PYTHONPATH lesson reference |
| R3-08 | STILL OPEN | Tracked as **N7** in implementation-plan-v2 (lines 172-189). ADR not landed. | leave-open |
| R3-09 | STILL OPEN | Layer A governance unaddressed; not blocking v0.5.0. | leave-open |
| R3-10 | STILL OPEN | No Worker conformance test in `src/linus/tests/`. | leave-open |
| R3-11 | STILL OPEN | DEC-0029 went schema-flat (no per-type weights table). Question becomes "do we add the typed taxonomy later?" — leave-open with that framing. | leave-open; refresh-framing — note "DEC-0029 shipped schema-flat; typed-taxonomy retrofit is now the question, not the up-front design call" |
| R3-12 | PARTIALLY RESOLVED | Already annotated; registry-side provenance still open. | leave-open; annotation current |
| R3-13 | STILL OPEN | No Phase 3 KB retrieval pipeline shipped; paperqa is the v0.5.0 KB retrieval, which does not use keppi-style `build_context_pack`. R3-13 framing intact. | leave-open |
| R3-14 | STILL OPEN | Skills library not started. | leave-open |
| R3-15 | STILL OPEN | Phase 6 question. | leave-open |
| R3-16 | STILL OPEN | Phase 7 protein-skill bake-off. | leave-open |
| R3-17 | STILL OPEN | No `hazard_curation_status` field on `ToolSpec` (verified by reading `src/linus/tools/registry.py`); `network_policy` was added (DEC-0061) but biosecurity-tier registry property still pending. | leave-open |
| R3-18 | STILL OPEN | Procedural memory layer placement undecided. | leave-open |
| R3-19 | STILL OPEN | `critic_eligible` budget policy ADR not authored. | leave-open |
| R3-20 | STILL OPEN | Stylometric-leakage SAFETY.md section not authored; DEC-0061 covered network-policy audit-log fields, but the stylometric tiering is a different scope. | leave-open; refresh-framing — note "DEC-0061 covered network-egress audit fields; stylometric/identity-leakage SAFETY.md section is separate and unblocked" |
| R3-21 | STILL OPEN | `value_frame` field still aspirational. | leave-open |
| R3-22 | PARTIALLY RESOLVED | Already annotated INFORMED 2026-05-18; Bonsai run not executed. | leave-open; annotation current |
| R3-23 | PARTIALLY RESOLVED | LX-1 (`src/linus/knowledge/paperqa.py` PR #89) shipped paper-qa as the v0.5.0 KB retrieval engine, treating the lift as "use paper-qa's pipeline" rather than layering wikiloom / TheKnowledge / llmbase patterns on top. The decision is now de facto: lifts go AROUND paper-qa, not ON TOP of it. | leave-open; refresh-framing — note "paper-qa is the v0.5.0 retrieval engine (PR #89); G2 lifts are now post-reveal additions on top of, or parallel to, the running paper-qa pipeline, not pre-conditions for it" |
| R3-24 | STILL OPEN | dlt destination not chosen. | leave-open |
| R3-25 | STILL OPEN | Already noted as unchanged in 2026-05-18 audit. | leave-open |
| R3-26 | STILL OPEN | Phase 6 pre-spike. | leave-open |
| R3-27 | PARTIALLY RESOLVED | DEC-0030 + DEC-0031 + DEC-0061 + `src/linus/memory/audit_log.py` together establish the audit log as the central Marelli surface: per-output records of model + memory_mode + cot_budget + (now) network_egress. `docs/specs/audit-log-spec.md` as a standalone doc has not been authored, but most of its operational substance is now ADR-codified. | leave-open; refresh-framing — note "audit log substantially specified via DEC-0030/0031/0061 + `audit_log.py`; standalone spec doc still outstanding but lower-priority than originally framed" |
| R3-28..R3-38 (Tier 3) | STILL OPEN | Tier 3 reservoir; no activity intended. | leave-open |
| R4-01 | RESOLVED | DEC-0056. Verified — ADR exists; Anthropic-Messages endpoint not yet shipped in `server.py` (DEC-0056 commits the Phase 2a posture; actual endpoint implementation is a v0.6.0 follow-up). Resolution claim is sound. | leave-as-resolved |
| R4-02 | RESOLVED | DEC-0057. Verified. Confirmed shipped 2026-05-19 via KB README treatment + AGPL doc in KB submodule. | leave-as-resolved |
| R4-03 | RESOLVED | DEC-0058. Verified. Watch→Spike→Integrate pathway codified. | leave-as-resolved |

## New questions surfaced

Items that emerged from 2026-05-19 → 2026-05-21 arc and from the Archimedes cross-pollination that
are not captured in any of the three question files. Suggested numbering uses an `R5-NN` prefix to
preserve the audit trail and avoid colliding with R4 (which is closed).

- **R5-01. Env-architecture layered (Option C) — when does v0.6.0 ship.** `docs/specs/2026-05-21-env-architecture-layered.md` is committed but the actual env-layering work (separating the `papers` env from `linus` env, or unifying via a shared meta-env) has no implementation owner or target. Blocks the Streamlit-pages-fully-alive story end-to-end.
- **R5-02. KB hardcoded-paths fix — v0.6.0 ownership.** `docs/specs/2026-05-21-kb-hardcoded-paths-fix.md` documents the path-constant inventory but the refactor (proposed `papers_analysis/paths.py`) has no PR. For v0.5.0 reveal Dan is the only person who can run the pipeline; this is the load-bearing barrier to broader use.
- **R5-03. Demo-script ownership for 2026-05-25.** `docs/demo-script-2026-05-25.md` is draft. The 2026-05-21 session summary lists "Demo dry-run" as outstanding-for-next-session item #3. No owner, no dry-run wall-time estimate, no go/no-go gate definition. Three days to reveal.
- **R5-04. Editable-installs + worktrees collision discipline.** Session summary §Lessons learned flagged this; not yet propagated to CLAUDE.md "Worktree fan-out discipline." Every fix agent in the 2026-05-21 arc hit it. Cheap CLAUDE.md addition; high recurrence risk if unwritten.
- **R5-05. Entity-grounding severity promotion gate.** DEC-0059 amendment commits to "may be promoted to error when canonical reference DBs (NCBI + UniProt + GO) ship." `entity_ncbi.py` shipped 2026-05-21 (PR #113). The promotion gate is now actionable but the criteria — what % of test corpus must resolve, what fallback behavior on offline — is not codified.
- **R5-06. Q2 signed-audit-slice (anchor.py) post-reveal scope.** Seeded under "Seeded ADRs" in DECISIONS.md (line 102, 2026-05-19). Not in any question file. Should be a tracked open question if Marelli attribution on Dan's manuscripts is genuinely v0.6.0+ scope.
- **R5-07. Bug-sweep medium-severity backlog disposition.** ~20 medium-severity findings across the 4 bug-sweep reports (`docs/bug-sweeps/`) deferred to v0.5.1. No triage spec yet; risks indefinite deferral the way R3-20 has drifted.
- **R5-08. pytest integration suite gating discipline.** PR #84 codified hermetic-pytest-before-merge but the integration-suite (`tests/`) gating — required when touching `server.py / agents/ / knowledge/ / memory/ / sandbox/` per CLAUDE.md — is not visibly enforced by any tool; relies on Maestro discipline. Worth a `.github/CODEOWNERS`-adjacent automation pass post-reveal.

## answered-questions.md cleanup

Concrete polish items for the resolved archive before reveal.

- **R2-05 (line 112-120, n6-janitorial section).** The "future SSE addition" reference is now stale — streaming SSE shipped 2026-05-21 (PR #116 H-1 reference; the streaming code path is in `server.py`). Update to: "SSE streaming subsequently shipped in PR #99 + PR #116; Open Responses event-catalog adoption remains the deferred capability."

- **R3-07 (line 140-147, n6-janitorial section).** The annotation references a single Phase 3 spawner spec (`docs/specs/phase3-spawner.md`). That spec exists. Add reference to the 2026-05-21 PYTHONPATH/editable-install lesson once it lands in CLAUDE.md (per R5-04 above).

- **R3-12 (line 150-156, n6-janitorial section).** Reference to "v2 plan follow-up" should be cross-linked to `docs/specs/2026-05-17-linus-implementation-plan-v2.md` §"Follow-ups from N6" (lines 336-385); the current text says "queued as a v2 plan follow-up" without a clickable pointer.

- **R4-01 (line 168-181).** DEC-0056 commitment landed but the Anthropic-Messages endpoint code did NOT ship in v0.5.0 — `server.py` exposes only OpenAI Chat Completions endpoints (verified via `grep -n "messages\|anthropic" src/linus/server.py`). Resolution claim is true at the ADR level; recommend adding a one-line caveat: "Endpoint implementation deferred to v0.6.0; ADR sets the Phase 2a commitment."

- **Sweep Tier 1 — S1 (line 555-558).** "Minimum Worker floor: Qwen2.5-14B-Instruct" should be updated to reflect S12 resolution which moved the floor to Qwen3 (current text in answered-questions.md at line 421 says "Qwen3 replaces Qwen2.5 throughout all benchmarks"). Cross-doc drift; one is wrong.

- **Sweep Tier 1 — S7 (line 597+, truncated in my read).** Verify the 27B failure (2026-05-18 qwen3.6 datapoint) doesn't contradict the original "FP16 baseline" framing; the empirical anchor capped FP16 at 14B not at "FP16 generic." Worth a footnote.

- **Table of contents (lines 17-34).** Missing entries for `n6-janitorial-resolved-2026-05-16` (which is the topmost section after `session-2026-05-18-resolutions`). Anchors are right but the TOC line is absent — add `[N6 janitorial (resolved 2026-05-16)](#n6-janitorial-resolved-2026-05-16)`.

- **No broken links found** across the entries I sampled (DEC pointers, paper-note links, session-summary links all resolve). The `2026-05-18-dan-manual-tasks.md` reference at line 55 + 67 + 78 exists at `docs/specs/2026-05-18-dan-manual-tasks.md`.

## Summary of recommended actions

- **Two RESOLVED items confirmed clean** (R4-02, R4-03); R4-01 needs a one-line caveat about endpoint implementation deferral.
- **Five existing partial-resolution annotations remain current** (R2-03, R3-01, R3-04, R3-07, R3-12, R3-22) — no edits required to top-questions, but R3-07 can be extended with the 2026-05-21 editable-installs lesson.
- **Six items need refresh-framing** without moving to resolved: R2-09, R2-13, R2-22, R2-26, R3-11, R3-20, R3-23, R3-27 — each has shipped reality that changes the question's framing without closing it.
- **Eight new questions (R5-01..R5-08)** should be promoted from latent state. R5-01..R5-04 are reveal-critical (next 3 days); R5-05..R5-08 are post-reveal but tracked.
- **answered-questions.md** needs ~6 small polish edits — none structural, all factual-drift cleanup.
