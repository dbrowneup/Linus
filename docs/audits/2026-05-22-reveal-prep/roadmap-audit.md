# ROADMAP.md audit — 2026-05-22 (v0.5.0 reveal-prep)

Audited against `git log` through commit `6b4fa51` (post-PR #118), DECISIONS.md through DEC-0061,
the 2026-05-21 fix-and-polish session summary, and the actual shipped source under `src/linus/`.
The current ROADMAP "Status snapshot" is dated 2026-05-19 and was last refreshed in PR #95 (`8e6bc4b`).
The reality has moved substantially since: ~30 PRs landed in the 2026-05-19 → 2026-05-21 reveal-prep arc.

---

## Phase 0 — Foundation

- **ROADMAP says:** COMPLETE. Phase 0 gate satisfied.
- **Reality:** Accurate. No drift.
- **Delta:** None.
- **Suggested update:** None.

---

## Phase 1 — Recon and Baselines

- **ROADMAP says:** in progress; status snapshot 2026-05-18. 1a/1d/1e complete; 1b/1c/1f Dan-driven open.
- **Reality:**
  - **1a** complete — ~130 repo-notes + ~127 paper-notes + 27 syntheses; no movement since.
  - **1b pmetal evaluation** still gated on Dan-side LoRA + serve trial + verdict ADR.
    Note that pmetal v0.5.0 **binaries were rebuilt** 2026-05-19 (session summary §Step 2) — the Metal
    Toolchain quirk was resolved — but the comparative benchmark + verdict ADR remain open.
  - **1c memory-pillar spike**: not run. Empirical 2026-05-18 data point (qwen3.6:27b unviable) stands.
    **DEC-0033 fingerprint, DEC-0034 four-config sweep, DEC-0037 TTT spike: all still open.**
  - **1d** complete — qwen3:8b baselines from PR #33.
  - **1e** complete — PR #38, verdict REJECT.
  - **1f minGRU MLX spike (DEC-0038):** not run.
  - **lm-eval harness (the 1c subsection labeled "lm-evaluation-harness standup"):** not started.
    No `benchmarks/results/public_baseline_*.json` file exists.
- **Delta:** Phase 1 status text accurate at item-list level but the Phase 1 → Phase 2 "gate" framing
  is now stale because Phase 2 MVP shipped without waiting on the gate. The pmetal verdict ADR is no
  longer blocking — Ollama is shipped as the default Worker engine for v0.5.0 and `LINUS_DEFAULT_MODEL`
  defaults to `qwen3:8b` (`src/linus/server.py:63`). pmetal is now a Phase 6 substrate question.
- **Suggested update:** Add a "Gate retrospective" line: "Phase 1 → 2 gate was bypassed in practice;
  Ollama+qwen3:8b shipped as the default Worker engine. pmetal verdict reclassified as a Phase 6
  substrate gate, not a Phase 2 gate. lm-eval harness still uncommissioned; deferred to a Phase 6
  prerequisite." Move 1c lm-eval bullet explicitly to "deferred."

---

## Phase 2 — Linus MVP

- **ROADMAP says:** "Phase 2 MVP shipped 2026-05-19 (PRs #66–#82, v0.4.0 release tag). The v0.5.0
  reveal-prep arc through 2026-05-25 adds paper-qa Phase 2c integration, a grounding gate,
  loud-degradation health checks, reveal-ready READMEs, and pmetal v0.5.0 binaries. Hermetic test
  suite at **413 tests** (~2.5s), zero regressions." Snapshot lists items through PR #94 and
  references DEC-0059 / DEC-0060.
- **Reality:**
  - **All v0.5.0 reveal-prep items are LANDED** as of `6b4fa51` (2026-05-21).
  - Hermetic suite count is **out of date**: ROADMAP says 413; session summary §Step 7 says
    **695 tests passing in ~7s** post-PR #116. Coverage push wave 2 (PRs #95–#99) and the bug-sweep
    fix dispatch (PRs #110–#116) added the rest.
  - **2a orchestration** — accurate. Server, tool registry, SSE streaming, Anthropic-compat,
    session store, `/healthz` extension all shipped. Newly added since ROADMAP snapshot:
    `POST /v1/tools/{name}/invoke` (PR #98, commit `14f85dd`).
  - **2b Streamlit UI** — accurate; landing + 7 pages all shipped.
  - **2c KB + paper-qa** — accurate.
  - **2e grounding gate** — accurate; ROADMAP correctly references DEC-0059 + PR #94.
    NOT in ROADMAP: the **DEC-0059 amendment landed via PR #104** (commit `e1ab5bd`) graduating
    the entity backend from stub (`BuiltinEntityLookup`) to KB-derived (`KBEntityLookup`,
    `ChainedEntityLookup` per PR #103). The gate is now auto-wired into `paperqa.answer` per PR #102.
    ROADMAP still describes the `BuiltinEntityLookup` stub as "for v0.5.0" — true at the time of
    writing, no longer accurate as the shipped reality.
  - **2h memory pillar v0** — accurate. ROADMAP correctly notes 2h.5/6/7 deferred.
  - **Sandbox** — ROADMAP says coverage 100% in PR #85; accurate, plus subsequent C-level race fix
    (PR #110) covering TOCTOU + symlink escape.
  - **Tool registry** — ROADMAP says 100% in PR #87; accurate.
  - **NOT in ROADMAP:** DEC-0061 network-policy framework (PR #109) — a major new architectural
    pillar; `entity_ncbi.lookup` as the first `online_optional` tool (PR #113); 4 bug-sweep reports
    in `docs/bug-sweeps/` (PRs #105–#108); ~10 critical/high fix PRs (PRs #110–#116).
- **Delta:** Phase 2 status snapshot is half a session out of date. The biggest missing item is
  DEC-0061 (the network-policy reframe is a non-trivial pivot from the prior uncompromisingly local-only
  stance). The grounding gate description still refers to the stub backend when the KB-derived backend
  has shipped. Test count is wrong (413 → 695).
- **Suggested update:** Replace the 2026-05-19 status snapshot with a 2026-05-21 one. Concrete edits in
  the §"ROADMAP refresh suggestions" section below.

---

## Phase 3 — Knowledge Integration and Parallel Agents

- **ROADMAP says:** future work; 3 weeks; agent spawner, parallel multi-agent fan-out, memory deepening
  (DEC-0052 Layer D, DEC-0040 faithfulness audit trigger, DEC-0031 auto-classifier). Gitflow graduation
  also gated here.
- **Reality:**
  - **3b parallel agent spawning** — `src/linus/agents/spawner.py` already exists (PR #67 commit
    `8834273`, "Minimal agent spawner: N parallel Workers, merged"). This is a Phase 3 deliverable
    landed in Phase 2. PR #115 hardened it (broad-except safety net on H1).
  - The DEC-0050 (Role as first-class type) and DEC-0051 (AgentReport typed message) ADRs were
    authored against the Phase 3 spawner; the in-tree `spawner.py` is the minimal v0 of this.
  - Gitflow graduation not started; still on lightweight model (`main` + feature branches), and the
    2026-05-19 merge-strategy refresh (PR #63) reinforced this rather than graduating.
  - 3d memory deepening — none of the items started.
- **Delta:** The agent spawner has bled forward into Phase 2 in practice. ROADMAP describes Phase 3 as
  if 3b is a future deliverable; in reality the minimal spawner is in `src/linus/agents/spawner.py`
  and exercised by the MVP suite. Phase 3 should be reframed as "agent-spawner v1 → role type → typed
  AgentReports → multi-agent investigation memory."
- **Suggested update:** Update 3b to "**Minimal agent spawner shipped as Phase 2 (PR #67, `agents/spawner.py`);
  Phase 3 adds Role typing (DEC-0050), AgentReport (DEC-0051), and multi-agent investigation memory
  (DEC-0052 Layer D)**." Acknowledge that "Phase 2 absorbed the Phase 3 spawner v0."

---

## Phase 4 — Data Sovereignty Layer

- **ROADMAP says:** Kiwix + Kolibri + ProtoMaps + Obsidian; offline knowledge sources.
- **Reality:** No work started. No `linus.kiwix.*` / `linus.kolibri.*` / `linus.maps.*` tools registered.
- **Delta:** None — accurate; nothing shipped against this phase. However, DEC-0061 (network-policy
  framework) **changes Phase 4's framing**: previously Phase 4 was "Linus must operate without network";
  the reality is now "Linus is local-primary, with opt-in network tools." Phase 4's value is
  refocused on physically-controlled-corpus expansion (full Wikipedia, Khan Academy, OSM) rather than
  network-independence-as-such — Linus is already network-independent for its core path.
- **Suggested update:** Add a one-line note up top: "Phase 4 framing updated by DEC-0061 — Linus's core
  path is already network-independent (Ollama + KB + sandbox), so Phase 4 is about expanding the
  physically-controlled corpus, not enforcing offline operation."

---

## Phase 5 — Interface Refinement

- **ROADMAP says:** openclaw front-end, VS Code polish, terminal path, carbon-atom branding.
- **Reality:**
  - Streamlit UI (PRs #74, #75–#80, #92) is the de facto v0.5.0 front-end, with 7 pages. This is a
    Phase 5 deliverable landed in Phase 2 (under the "2b chat UI" line).
  - openclaw integration not started.
  - VS Code polish: Cline/Ollama-chat path works against `/v1/chat/completions` (PR #32+) and Anthropic
    `/v1/messages` (PR #71), so the protocol surface for VS Code is unblocked, but no `docs/vscode-setup.md`
    has been written.
  - Branding: README rewrite landed (PR #91, `e147836`); no carbon-atom SVG yet.
- **Delta:** Streamlit UI has overshot the Phase 5 chat surface in practice — Linus's primary user
  surface for the reveal is `streamlit run src/linus/app/main.py`, not openclaw or VS Code. The
  ROADMAP Phase 5 framing ("openclaw as front-end") should acknowledge Streamlit as the de facto
  Phase 2/5 surface that may absorb some of Phase 5's intent (e.g., voice integration might land on
  Streamlit instead of openclaw, or branding lands there first).
- **Suggested update:** Add 5e (or amend 5a) — "**Streamlit UI is the de facto v0.5.0 front-end**
  (Phase 2b); Phase 5 decisions on openclaw vs. native vs. continued-Streamlit-expansion are now
  empirically informed by reveal feedback."

---

## Phase 6 — Fine-Tuning

- **ROADMAP says:** LoRA continued-pretraining → instruction-tuning → preference alignment → flash
  streaming → TTT consolidation → Coconut substrate.
- **Reality:** No work started. The `experiments/adapters/` directory does not exist. The pmetal-vs-mlx-lm-ft
  branching question still gated on the (deferred) Phase 1b verdict.
- **Delta:** None of the deliverables started, but the upstream gates (DEC-0033 fingerprint, DEC-0034
  four-config, DEC-0037 TTT spike, DEC-0038 minGRU spike, DEC-0042 Coconut portability) are all still
  open from Phase 1c/1f. Phase 6 cannot start without those.
- **Suggested update:** None to the Phase 6 body. Add a line at the top: "Phase 6 is blocked on Phase 1c
  + 1f Dan-driven spikes. No movement on Phase 6 deliverables expected pre-reveal."

---

## Phase 7 — Skills and Autonomy Graduation

- **ROADMAP says:** bioSkills + scientific-agent-skills bundle, FM pairings (Trias+GenNA, etc.),
  autonomy tier graduation, inference iteration.
- **Reality:** Not started. SAFETY.md autonomy tier graduation criteria still unwritten as a checklist.
- **Delta:** None to ROADMAP text. The DEC-0046 `external_api_tool: deployment` field that Phase 7 needs
  is now adjacent to DEC-0061's `network_policy` field on `ToolSpec` — the registry schema is partially
  there. Worth a forward note that DEC-0061's framework anticipates Phase 7's external API tools.
- **Suggested update:** One line: "DEC-0061 lays the `network_policy` foundation that DEC-0046 external_api
  tools will build on; Phase 7 inherits a working network-policy framework."

---

## Phase 8 — Beyond MacBook

- **ROADMAP says:** native app, hardware expansion, Linus-as-Maestro north star.
- **Reality:** Not started, framed as long-horizon. The Q2 signed-audit-slice (seeded ADR) is implicitly
  Phase 8-adjacent — Marelli attribution discipline for manuscript submissions — but ROADMAP doesn't
  reference it.
- **Delta:** Minor — the signed-audit-slice ADR seed (post-reveal Q2) anchors a future Phase 8 capability
  worth mentioning.
- **Suggested update:** Add a memory long-horizon bullet: "Signed-audit-slice (seeded ADR, post-reveal) —
  ed25519-signed exportable audit + episodic slice for Marelli attribution discipline when Linus output
  enters Dan's manuscripts."

---

## Unrecorded work (shipped but not in ROADMAP narrative)

The following PRs / DECs landed between the 2026-05-19 ROADMAP refresh (PR #95) and 2026-05-21 and are
not yet reflected:

- **DEC-0061 network-policy framework** (PR #109, commits `fa9d6e3` + `a60da05` + `c99d248` + `81fab19`):
  three-pillar policy — per-tool `network_policy` field, `network_egress[]` on audit log, `/healthz`
  reachability for `online_*` tools. Major architectural pivot from "uncompromisingly local-only" to
  "local-primary + opt-in network." Status: shipped to main; VISION.md updated (`703e145`, `ab3ba21`);
  CLAUDE.md note added.
- **`entity_ncbi.lookup` tool** (PR #113, commits `2dd014c`, `62a43fe`, `9e90fdd`): first
  `online_optional` instance, NCBI Gene + UniProt + ChEBI routing, SQLite cache, rate-limit throttling,
  audit-log egress. 46 hermetic tests (HTTP fully mocked).
- **DEC-0059 amendment** (PR #104, commit `e1ab5bd`): entity backend graduated from stub to KB-derived
  (`KBEntityLookup` + `ChainedEntityLookup`, PR #103); auto-gate wired into `paperqa.answer` (PR #102).
- **`POST /v1/tools/{name}/invoke` route** (PR #98, commit `14f85dd`): direct tool invocation route;
  Streamlit pages refactored off prior steering-prompt + marker-block hack.
- **Bug-sweep reports** (PRs #105–#108): 4 surface-only sweep reports in `docs/bug-sweeps/` covering
  knowledge/, memory/+agents/, server.py, tools/+sandbox/+tests. 53 findings catalogued.
- **Critical fix dispatch wave 1** (PRs #110–#113): SandboxFS TOCTOU + symlink escape,
  SessionStore append_message + get_default_store races, KBEntityLookup lazy-parse race,
  ChainedEntityLookup exception isolation, entity_ncbi.lookup landing.
- **High-severity fix dispatch wave 2** (PRs #114–#116): paper-qa double-roundtrip cache, episodic
  IN-list chunking, spawner._run_sync safety net, server.py streaming session persistence on disconnect,
  server.py tool-call message persistence.
- **Hermetic test count**: ROADMAP says 413; reality is **695 (post-PR #116, ~7s wall)**.
- **`pytest-before-merge` hard rule** (PR #84, commit `02e45aa`): codified in CLAUDE.md.
- **Coverage push wave 1+2** (PRs #85–#88, #96–#99): sandbox, episodic, registry, audit_log, kb_tools,
  adapter, server.py all driven to 99–100% hermetic coverage.
- **KB submodule pin bump** (PR #90, commit `2d3d67f`) for the AGPL-honest README rewrite.
- **Operational scripts shipped** (`bec3be7`): `experiments/2026-05-21-run-kb-pipeline.sh` —
  Dan-runnable KB pipeline driver. Not a code feature but is Dan's last-mile reveal blocker.
- **v0.6.0 specs seeded** (PRs #117, #118): KB hardcoded-paths fix spec, env-architecture-layered spec
  (Option C).
- **Demo + manuscript artefacts** (PR #101, `d268e63` + `92f2fac`): `docs/demo-script-2026-05-25.md` and
  `docs/specs/manuscript-polish-workflow.md`.
- **Archimedes bridge spec** (PR #82, `b4a3a2c`): `docs/specs/linus-archimedes-bridge.md` — integration
  contract with the Archimedes team for the coordinated reveal.

---

## Architectural-pillar status (current as of 2026-05-22)

| Pillar | Status | Notes |
| --- | --- | --- |
| Orchestration (FastAPI, OpenAI + Anthropic compat) | shipped, hardened | `src/linus/server.py`, 99% hermetic cov |
| Memory v0 (Layer C SQLite + audit log + sessions) | shipped, hardened | episodic/audit_log/sessions all 100% cov; race-fixed |
| Sandbox FS | shipped, hardened | TOCTOU + symlink escape fixed (PR #110); 100% cov |
| Audit log | shipped + extended for DEC-0061 `network_egress[]` | append-only JSONL; backwards-compat |
| Network policy (DEC-0061) | **NEW** — shipped | per-tool field + audit + `/healthz`; first instance `entity_ncbi.lookup` |
| KB integration (read-only adapter + retriever) | shipped, hardened | adapter 100% cov; finalizer added; per-instance page-count cache |
| paper-qa Phase 2c | shipped, auto-gated | `linus.knowledge.paperqa`; 4 registered tools; rigor gate auto-runs on `answer` |
| Grounding gate (DEC-0059) | shipped, **entity backend graduated** | KBEntityLookup + ChainedEntityLookup live (PR #103/#104) |
| Entity grounding | KB-derived live; NCBI online_optional live | DEC-0059 amendment + PR #113 |
| Streamlit UI | shipped — landing + 7 pages | reveal-blocking smoke test pending KB pipeline run |
| Loud degradation (DEC-0060) | shipped | `/healthz` `effective_state` + `degradations[]` |
| Agent spawner (DEC-0050/0051 v0) | shipped in Phase 2 | `src/linus/agents/spawner.py`; Role+AgentReport typing deferred |
| Tool registry | shipped, hardened, extended | `network_policy` kwarg added; `POST /v1/tools/{name}/invoke` |
| Signed-audit-slice (Q2 anchor) | **seeded ADR, post-reveal** | Marelli attribution discipline |

---

## ROADMAP refresh suggestions (concrete edits)

The minimum edits for the v0.5.0 reveal-ready state of ROADMAP.md:

1. **Replace the Phase 2 status snapshot date** "(2026-05-19, v0.5.0 reveal-prep arc)" with
   "(2026-05-21, v0.5.0 reveal-prep complete)". Change the opening sentence from "Phase 2 MVP
   shipped 2026-05-19 (PRs #66–#82, v0.4.0 release tag). The v0.5.0 reveal-prep arc through
   2026-05-25 adds…" to "Phase 2 MVP shipped 2026-05-19 as v0.4.0 (PRs #66–#82); the v0.5.0
   reveal-prep arc closed 2026-05-21 with PRs #83–#118. Hermetic test suite at **695 tests**
   (~7s), zero regressions."

2. **Add a new bullet to the Phase 2 status snapshot** for DEC-0061:
   "**Network policy (DEC-0061, NEW for v0.5.0):** shipped — per-tool `network_policy` field on
   `ToolSpec`, `network_egress[]` on audit log, `/healthz` reachability for `online_*` tools (PR #109).
   First instance `entity_ncbi.lookup` for NCBI Gene + UniProt + ChEBI lookup as the production
   reference backend behind DEC-0059's entity grounding (PR #113). Local-primary stance preserved;
   nothing depends on network."

3. **Amend the 2e bullet** (output rigor): replace "`BuiltinEntityLookup` stub for v0.5.0" with
   "entity backend graduated from stub to KB-derived `KBEntityLookup` + `ChainedEntityLookup` (PR
   #103, DEC-0059 amendment); rigor gate auto-runs inside `paperqa.answer` (PR #102); `entity_ncbi.lookup`
   joins the chain as an `online_optional` first option (PR #113, DEC-0061)."

4. **Add a 2k bullet** (or rename a "Deferred" item): "**Server tool-invoke route + coverage hardening:**
   `POST /v1/tools/{name}/invoke` direct-invoke route (PR #98) plus hermetic coverage push to 99–100% on
   sandbox/fs, memory/episodic, memory/audit_log, memory/sessions, tools/registry, tools/kb_tools,
   knowledge/adapter, server.py (PRs #85–#88, #96–#99). Race-condition + TOCTOU fixes shipped via the
   bug-sweep dispatch (PRs #105–#116, 4 sweeps + 7 fix PRs)."

5. **Phase 3 reframe:** in the "Phase 3 — Knowledge Integration and Parallel Agents" intro,
   add: "**Phase 2 absorbed the minimum agent-spawner v0** (`src/linus/agents/spawner.py`, PR #67);
   Phase 3 builds on top: Role as first-class type (DEC-0050), AgentReport typed messages (DEC-0051),
   Layer D investigation memory (DEC-0052), parallel-write coordination."

6. **Phase 1 retrospective:** in the Phase 1 intro, add a "Gate retrospective" paragraph:
   "Phase 1's Phase-1b gate-decision framing has been retired in practice. Linus shipped Phase 2 with
   Ollama+qwen3:8b as the default Worker engine without waiting on the pmetal verdict. pmetal v0.5.0
   binaries rebuilt 2026-05-19 (Metal Toolchain quirk resolved); the comparative benchmark + verdict
   ADR remain open as Phase 6 substrate questions, not Phase 2 blockers. lm-eval harness deferred."

7. **Phase 4 reframe (one-line):** add at top of Phase 4 section: "**Reframed by DEC-0061:** Linus's
   core path is already network-independent (Ollama + KB + sandbox). Phase 4 is now about expanding
   the physically-controlled corpus (Wikipedia, Khan Academy, OSM), not enforcing offline operation."

8. **Phase 5 acknowledgment:** add 5e: "**Streamlit UI is the de facto v0.5.0 user surface** (landing
   + 7 pages, PRs #74–#80, #92). Phase 5 decisions on openclaw vs. native vs. continued-Streamlit-
   expansion are now empirically informed by reveal feedback."

9. **DEC index sync** (in the Phase 1 status block): add DEC-0059, DEC-0060, DEC-0061 to the "ADR
   landings since 2026-05-10" line. Currently stops at DEC-0058.

10. **Phase 2 deferred-to-post-reveal list:** add v0.6.0 items already seeded:
    "**v0.6.0 seeded:** KB hardcoded-paths fix (`docs/specs/2026-05-21-kb-hardcoded-paths-fix.md`,
    PR #117), env-architecture-layered Option C (`docs/specs/2026-05-21-env-architecture-layered.md`,
    PR #118), entity_ncbi promotion to error-severity (depends on real reference backend coverage),
    v0.5.0 bug-sweep mediums (~20 across the four sweeps in `docs/bug-sweeps/`)."

11. **Phase 8 long-horizon addendum:** add to "Memory long-horizon directions":
    "**Signed-audit-slice** (seeded ADR, post-reveal Q2): ed25519-keypair-based exportable signed
    slice of audit + episodic records for Marelli attribution discipline when Linus output enters
    Dan's manuscript submissions; forward-compatible with future Merkle-root external anchoring."

The first three items are reveal-blocking; the rest can ship in the same PR but are post-reveal-ok.
