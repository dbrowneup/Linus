# Top-Questions Resolution Session Summary — 2026-05-03

This document recaps the 2026-05-03 Maestro/Dan planning session that walked
[`docs/questions/top-questions.md`](../questions/top-questions.md) end-to-end and
converted every Tier 0, Tier 1, Tier 2, and Tier 3 item into committed decisions,
landscape-doc updates, DECISIONS.md entries, and an actionable Worker spec.

It is intentionally a recap, not a synthesis: the resulting
[`docs/specs/planning-update-spec.md`](../specs/planning-update-spec.md) is the
implementation artifact; this summary is the run log.

---

## Pre-session setup

Before walking the questions, two scope clarifications were agreed:

1. **Update cadence** — running notes buffer between questions; batched landscape /
   DEC / spec updates at the end. Cleaner commits, single coherent rewrite of the
   spec at close.
2. **Tier 0 items** — treated as confirm-and-queue, not action-now. Both Tier 0
   actions (deps cleanup + lock file; SAFETY.md incident response) were queued
   into the planning-update-spec for execution by Workers in subsequent sessions.
3. **Numbering quirks** — top-questions.md has duplicate numbers (Tier 1 #6 and
   Tier 2 #6 both exist; Tier 3 restarts at #14). Walked strictly in document
   order; referred by tier+title rather than number.
4. **Project status update** — Phase 0 closed and Phase 1 in-progress status
   landed up front as a small ROADMAP.md edit before the question walk began.
   We're roughly halfway through Phase 1; 1a largely complete; 1b's pmetal
   evaluation is in progress with strongly positive initial impressions.
5. **DECISIONS.md graduation threshold** — currently 11 entries; expected ~5-8
   new DECs from this session would bring the count near the file's own ~20-entry
   ADR-graduation threshold. Agreed to keep appending this session and graduate
   to per-file ADRs in a follow-up session. Final count after this session: 27.

---

## The walk — 28 questions resolved across four tiers

### Tier 0 — Immediate actions (2 items)

Both confirmed and queued into the spec for Worker execution.

- **0/0 — Remove pre-emptive ML framework deps.** Remove langchain / langgraph /
  haystack-ai from `environment.yml`. Add hash-pinned `requirements-locked.txt`
  via `pip-compile --generate-hashes`. Document dep philosophy in CLAUDE.md.
  streamlit and lm-eval stay (closer-term Phase 1c/2 use).
- **0/1 — Incident response protocol in SAFETY.md.** Draft "Supply Chain Incident
  Response" section: trigger / containment / credential rotation / attestation.

### Tier 1 — Decisions blocking Phase 1 / Phase 2 (6 items)

The decisions with the longest downstream consequences.

- **1/1 — BitNet 2B4T spike.** Adopt as first concrete Phase 1c experiment using
  task-completion-time methodology in `benchmarks/dan_tasks/`. Threads with
  Tier 3 #19 and 1-bit viability question.
- **1/2 — Inference backend (pmetal lead).** Build flags `--features
  serve,mlx,trainer` for 1b; defer `ane,distill,data` to their phases.
  Concurrency target single-request tok/s + RSS for verdict; 5-concurrent is
  Phase 2a concern. Pin a commit; document Ollama+mlx-lm-ft fallback in ADR
  0001; revisit quarterly.
- **1/3 — Phase 6 fine-tuning lane.** Defer the lane decision (native-1-bit /
  BitDistill / FP16-LoRA) until Phase 1c BitNet data lands. Phase 6a commits to
  FP16-LoRA on genomics/biochem regardless. Decision gate at Phase 6a/6b
  boundary.
- **1/4 — KB data model.** **Dual approach** — both RDF (rdflib + optional
  Oxigraph) and property graph (networkx; Kuzu evaluated later) in parallel.
  Inspection of the KnowledgeBase submodule confirmed `rdflib` and `networkx`
  already declared as deps, with `graph.py` and `knowledge_graph.py` already as
  separate modules — the dual-substrate posture was already implicit. Linus's
  adapter exposes both as separate tool families. **Surfaced new [KB-spec]
  split convention** for spec-parts that primarily impact KnowledgeBase
  (delivered to KB repo via `docs/specs/kb/` sub-document).
- **1/5 — Harness plurality.** Maintain through Phase 5 with explicit role
  designations: Claude Code = hosted Maestro; cline = VS Code Worker;
  claw-code-local = terminal local-model; openclaw = chat/voice/canvas/mobile.
  No per-harness gold-plating. Pre-answers Tier 2 #6 (Dan signaled MCP
  adoption).
- **1/6 — KB ingest quality gate.** YAML-policy framework adopted as a
  **quality surface, not a hard gate** — Dan is the primary filter (everything
  on his machine has passed his download decision). Domain-agnostic baseline
  signals; preprints flagged not rejected; no hard reject lane in Phase 2.
  FineWeb-style calibration deferred to Phase 3 as a learning exercise.
  **[KB-spec]** item.

### Tier 2 — Decisions shaping Phase 2–6 architecture (11 items)

- **2/6 — MCP as extensibility substrate.** Adopt. Phase 2 tool registry built
  MCP-shape from the start (no Phase 3 refactor). Linus exposes a Linus-native
  MCP server AND consumes external MCP servers. **pmetal's 45-tool MCP server
  is the first external integration target.** Evaluate `fastmcp`. Updates
  DEC-0005.
- **2/7 — KB embedding pipeline ablation.** Run unified Phase 2 ablation
  (SPECTER2 raw / +Stankevičius post-processing / BGE-base / +post-processing
  / random+post-processing) × {full-dim, PCA-256/384/512}. Distance-
  discrimination `|D_max − D_min| / D_min` adopted as continuous KB health
  metric. Resolves Tier 2 #7, Curse-of-Dim Q1+Q2, and a paper-landscape
  cross-cutting question in one experiment. **[KB-spec]**.
- **2/8 — KV-cache compression.** Defer as Phase 2 explicit feature. Apply
  The Algorithm. Enable only if free config flag in pmetal/bitnet.cpp/mlx-flash.
  Revisit Phase 6+.
- **2/9 — ANE in Phase 1b.** Defer to Phase 2 as conditional follow-up
  benchmark, gated on favorable pmetal Phase 1b verdict. Phase 1b/1c primary
  backends: Ollama-CPU/GPU, pmetal-GPU, bitnet.cpp-CPU.
- **2/10 — mlx-flash vs. flash-moe.** Commit Phase 5+ to mlx-flash as the
  >RAM dense path. flash-moe stays methodology-only reference (experiment-log
  discipline + "trust the OS page cache" lesson).
- **2/11 — Streaming + 1-bit composite.** Phase 6d formal target = mlx-flash
  streams any fine-tuned model exceeding RAM. Phase 6d *stretch* target =
  opportunistic ternary >8B integration if PrismML/community releases. Phase 8
  BitNet × Flash-MoE × JPmHC stays long-horizon.
- **2/12 — flash-moe target on M1 Max.** Commit to the practice. Once Phase 1b
  closes, draft `docs/specs/phase6d-streaming-target.md` with concrete model +
  tok/s target.
- **2/13 — Custom orchestration scope.** Keep DEC-0002 (custom orchestration
  layer). Algorithm-check primitives via **new Phase 1f deliverable**: evaluate
  Task Master AI + claude-squad vs. custom Linus prototype vs.
  pmetal-MCP-as-orchestrator on a real Phase 2 task spec. Adopt PRD→tasks
  pattern as a **skill**, not a re-implementation. Linus custom layer scope
  clarified: sandbox + KB + MCP registry + audit; no task-decomposition
  primitives.
- **2/14 — Monetize now vs. build first.** Skip the binary. **New Phase 2
  deliverable: `docs/entrepreneurial-surface.md`** — a planning artifact (not
  a business plan). Don't actively pursue clients but don't rule out either.
- **2/15 — Phase 5c.** Mark formally as "adopt claw-code-local." Remove the
  500-line custom Python agent fallback from ROADMAP. Phase 5c work scope:
  configure + integrate.
- **2/16 — Parallel Worker KB write coordination.** Serialized writes through
  coordinator + write-time contradiction surfacing. Workers emit JSON-shaped
  diff proposals; coordinator merges in order; conflicts flag for human
  review. Git-branch-per-ingest underneath. **[KB-spec]:**
  `docs/specs/kb/parallel-worker-write-coordination.md`.

### Tier 3 — Documentation, conventions, longer-horizon scope (10 items)

- **3/19 — Benchmark architecture.** Three-task schema with wall-clock as
  primary axis. Multiple metrics recorded (tok/s, RSS, TTFT, completion time,
  quality score) — Worker selection is **holistic**. Public eval baselines
  (MBPP/HumanEval/MMLU/GPQA) run **alongside** `dan_tasks/`, not instead.
- **3/20 — RaKUn 2.0.** **Integrate-and-evaluate, not adopt outright.** RaKUn
  2.0 enters KB as additional tool alongside the existing TF-IDF + BERTopic +
  SPECTER2 + UMAP pipeline. Phase 2 evaluation produces empirical comparison;
  possibly retain both as parallel signals. **[KB-spec]**.
- **3/21 — Security posture.** (1) Hash pinning + monthly pip-audit + quarterly
  review. (2) **uv installed via conda inside linus env**; untrusted
  experimental packages always in disposable uv envs. (3) CVE response folded
  into SAFETY.md incident protocol. → DEC.
- **3/22 — Output interface (10 bits/s).** Adopt 10-bits/s framing as Phase 2
  design principle. **Balanced bullets + prose** (not bullet dumps).
  **Citations and traceability are first-class.** Worker outputs preserved
  for Maestro inspection. Opt-in `/verbose`. **Linus reframed as personal LLM
  Wiki at scale.** → DEC.
- **3/23 — Community repos.** **Clone all 12 community repos** + future
  additions. Phase 1a expanded to 1f addendum. **New curation protocol** for
  `repos/`, `context/`, `docs/` with archive log.
- **3/24 — Documentation cadence.** Two load-bearing notes: `docs/specs/
  kb-architecture.md` ([KB-spec], Phase 2 deliverable) and
  `docs/experimental-protocol.md` (Phase 1c deliverable). BitNet-on-Apple-
  Silicon synthesis deferred to post-Phase 1c. flash-moe case study deferred
  to Phase 5+.
- **3/25 — Phase 4 scope.** Full English Wikipedia (~100 GB) from start as
  foundation for personal LLM Wiki. **Kolibri as parallel benchmark surface**
  (`benchmarks/kolibri_tasks/`). Planet-wide PMTiles target with
  population-density fallback. English-only confirmed.
  CyberChef/ArchiveBox/Qdrant deferred. Owner location updated (Hawthorn
  Woods, IL).
- **3/26 — Practice/stance batch.** All six adopted with refinements: trust
  OS page cache (convention); public APIs only for Linus's own code (Dan
  corrected: pmetal uses supported APIs, not private; ANE repo is the
  private-API anchor); multi-language stance (Python core, Rust/JS/TS/bash for
  components); light VISION.md sovereignty refinement; reproducibility +
  interpretability principle; Obj-C/Metal-direct deferred (not ruled out).
- **3/27 — Methodology and tooling.** autoresearch program.md → SKILL.md in
  Phase 7. Per-experiment budget: 30+ min on Dan task suite as default. First
  autoresearch use: **Phase 1b pmetal LoRA trial.** Cline prompt-variant
  pattern: Phase 7.
- **3/28 — Smaller open items batch.** All 13 items resolved as batch
  recommendation (voice wake → Phase 5; canvas → Phase 5 stretch; skills
  symlinked from `src/linus/skills/`; browser-based agentic work →
  Maestro-only; ACP/Zed defer; BitNet weight viz curiosity defer; pmetal-mhc
  curiosity/stretch in Phase 6; code-specialized BitNet defers to Phase 6
  lane decision; DPO yes per existing ROADMAP; PrismML forks track upstream;
  4-bit weights first, KV cache deferred; JPmHC TRM spike defer; ANE
  substacks read in Phase 2 if pmetal verdict favorable; Karpathy autoresearch
  tweets read in Phase 1b).

---

## Meta-decisions surfaced during the walk (not in the original tier list)

Four meta-level decisions emerged from Dan's responses that weren't on the
original question list:

1. **[KB-spec] split convention** — Tier 1 #4 introduced this. Spec-parts that
   primarily impact KnowledgeBase get tagged `[KB-spec]` and split into a
   sub-document under `docs/specs/kb/` for delivery in the KnowledgeBase repo
   (executed by Claude or eventually Linus, in partnership with Dan). Codified
   as DEC-0016.
2. **Planning write-back cadence** — Tier 3 #19 surfaced this from Dan: the
   write-back rule from the LLM Wiki synthesis explicitly extends to Maestro/
   Dan + Claude planning sessions. At the close of every multi-question
   planning session, allocate time for core-file write-back. Codified as
   DEC-0026 and added to CLAUDE.md as an Engineering Convention.
3. **Curation protocol for `repos/`, `context/`, `docs/`** — Tier 3 #23
   surfaced Dan's preference for quarterly curation review with archive
   pathway and "memory of what was removed and when." Codified as DEC-0025;
   `docs/curation-protocol.md` and `docs/curation-log.md` added to spec.
4. **uv-via-conda layered architecture** — Tier 3 #21 surfaced Dan's
   architectural commitment to install uv via conda inside the linus env, with
   uv envs as disposable scratch space and the conda env as the production
   substrate. Codified as part of DEC-0024.

---

## Outputs produced (during the same session)

After the walk completed, the session produced the following artifacts in a
batched update phase:

### Resolution markers

- **`docs/questions/open-questions.md`** — Resolution Log header pointing to
  `top-questions.md` and the spec.
- **`docs/questions/top-questions.md`** — Full Resolution Log with `[Q]: <answer>`
  links per item; tier-level RESOLVED banners on all four tiers.

### Landscape doc updates (inline resolutions)

- **`docs/landscapes/paper-landscape.md`** — All 10 cross-cutting questions
  resolved inline.
- **`docs/landscapes/repo-landscape.md`** — All three "Key Tensions" resolved
  inline.
- **`docs/landscapes/synthesis-landscape.md`** — All cross-cutting open
  questions resolved inline.
- **`docs/landscapes/total-landscape.md`** — All four "crossings worth naming"
  resolved inline; four of seven gaps closed inline (custom orchestration,
  KB ingest quality gate, incident response protocol, commercial surface).

### DECISIONS.md additions

- **DEC-0012 through DEC-0027** — 16 new entries appended. Topics:
  pmetal Phase 1b candidacy with sub-decisions; BitNet 2B4T spike adoption;
  Phase 6 lane deferral; KB dual data model; [KB-spec] split convention;
  harness plurality role designations; MCP adoption; KB quality surface;
  Linus orchestration scope refinement; Phase 5c claw-code-local adoption;
  parallel-worker KB write coordination; output interface + LLM Wiki framing;
  security posture (hash pinning + uv-via-conda + CVE response); curation
  protocol; planning write-back cadence; practice/stance batch.
- DECISIONS.md is now at 27 entries; ADR graduation queued for next session.

### Planning-update-spec rewrite

- **`docs/specs/planning-update-spec.md`** — Full rewrite, supersedes the
  2026-05-01 draft. Nine sections:
  1. Status snapshot
  2. Phase-by-phase change list (Phases 1 through 8)
  3. [KB-spec] sub-document with six KB-impacting tasks
  4. DECISIONS.md additions checklist
  5. File-by-file edit plan (CLAUDE.md, VISION.md, ARCHITECTURE.md,
     ROADMAP.md, SAFETY.md)
  6. Curation protocol setup (`docs/curation-protocol.md` +
     `docs/curation-log.md`)
  7. Repos to clone + notes to write (12 community repos + curation log entry)
  8. Worker invocation guide — three patterns: Maestro Opus session, Haiku
     Worker for self-contained tasks, future Linus-orchestrated; with
     copy-paste prompt templates for each.
  9. Open questions surfaced for next iteration.

### Status edits (early in session, before the walk)

- **`README.md`** — Phase 0 closed / Phase 1 in-progress status snapshot.
- **`ROADMAP.md`** — Phase 0 collapsed to closed; Phase 1 status snapshot for
  2026-05-01 inserted; 1a/1b actual progress reflected.

### KnowledgeBase submodule check

- Inspected the KnowledgeBase submodule mid-Tier-1-#4 to verify what data
  model commitments were already in place. Confirmed `rdflib` and `networkx`
  both as deps, with `graph.py` and `knowledge_graph.py` as separate modules.
  This empirical observation drove the dual-substrate decision rather than
  forcing a single-substrate choice.

---

## Process notes from the run

1. **Notes-buffer cadence worked well.** Capturing decisions as a running
   notes buffer between questions, batching landscape/DEC/spec updates at
   the end, kept the question walk fast (one question every few minutes) and
   produced a coherent batched edit phase rather than churn-y micro-revisions.

2. **Recommendation-then-call shape worked well.** For each question, the
   pattern was: my read on the tradeoffs + my recommendation + "your call?"
   Dan agreed with most recommendations directly; pushed back or refined on
   ~5-6 (notably: Tier 1 #4 "why not both?", Tier 1 #6 "Dan is the primary
   filter," Tier 3 #19 "multiple metrics + holistic," Tier 3 #20
   "integrate-and-evaluate not adopt outright," Tier 3 #22 "balanced bullets +
   prose; citations first-class," Tier 3 #23 "clone all 12 + curation
   protocol," Tier 3 #25 "full Wikipedia + Kolibri-as-benchmark + planet
   PMTiles + Hawthorn Woods location"). The pushbacks were the most generative
   moments — they introduced the [KB-spec] split convention, the LLM-Wiki-at-
   scale reframing, the curation protocol, and the planet-wide PMTiles
   ambition.

3. **Cross-question pre-answers were efficient.** Several questions
   pre-answered each other: Tier 1 #5 (harness plurality) signaled Tier 2 #6
   (MCP adoption). Tier 1 #1 (BitNet spike) pre-set Tier 3 #19 (benchmark
   architecture). Tier 2 #10 (mlx-flash vs flash-moe) framed Tier 2 #11
   (streaming + 1-bit composite). Tier 2 #11 framed Tier 2 #12 (concrete
   target). The walk's natural ordering let earlier resolutions tee up later
   ones.

4. **The [KB-spec] convention emerged organically.** Tier 1 #4 surfaced Dan's
   observation that much of this material more directly impacts KnowledgeBase
   than Linus. The convention was named there and applied retroactively to
   six items across the walk (Tier 1 #4, Tier 1 #6, Tier 2 #7, Tier 2 #16,
   Tier 3 #20, Tier 3 #24). Without the convention, the resulting spec would
   have entangled Linus and KnowledgeBase work; with it, KB work has a clean
   handoff document.

5. **DECISIONS.md graduation timing.** The session's 16-DEC budget brought the
   file to 27 entries, past the file's own ~20-threshold. Deliberate choice:
   keep appending rather than splitting graduation work into this session.
   ADR graduation queued for next session.

6. **Worker invocation guide added at Dan's request.** The original spec
   structure didn't include execution instructions; Dan asked for them. The
   resulting Section 8 of the spec includes three Worker invocation patterns
   (Maestro Opus full execution, Haiku narrow task, future Linus-orchestrated)
   with copy-paste prompt templates and recommended execution order. This is
   the part that makes the spec genuinely Worker-executable rather than
   Maestro-only.

7. **Date drift during the session.** Multiple system reminders flagged date
   changes during the walk (2026-05-01 → 2026-05-02 → 2026-05-03). The walk
   spanned the date boundary; outputs are dated 2026-05-03 as the close of
   the session (consistent with the DECISIONS.md entries and the spec
   timestamp).

---

## Cumulative run totals

| Metric | Value |
|---|---|
| Questions walked | 28 (Tier 0: 2; Tier 1: 6; Tier 2: 11; Tier 3: 9 individual + 13 in batch) |
| Questions resolved | 28 (all answered) |
| Meta-decisions surfaced | 4 ([KB-spec] split convention, planning write-back cadence, curation protocol, uv-via-conda) |
| New DECs added | 16 (DEC-0012 through DEC-0027) |
| DECISIONS.md final state | 27 entries; ADR graduation queued for next session |
| Files modified in batched edit phase | 9 (open-questions.md, top-questions.md, four landscape docs, DECISIONS.md, planning-update-spec.md, README.md, ROADMAP.md) |
| Spec sections | 9 |
| [KB-spec] sub-document tasks queued | 6 (KB-3.1 through KB-3.6) |
| Worker invocation patterns documented | 3 (Maestro Opus full / Haiku narrow / future Linus-orchestrated) |

---

## Outstanding questions for next session

These are items surfaced during the run that need Dan's direction or further
investigation; they are explicitly carried forward to the next iteration rather
than resolved now:

1. **Planet PMTiles disk footprint research.** What is the actual file size for
   global PMTiles coverage at the resolution Linus needs? Decide between full
   planet vs. population-density-weighted vs. fallback regional priority based
   on the answer.

2. **Additional community repos to clone.** Dan flagged "one more slug" of
   content in this iteration; the next iteration captures the specific repos
   beyond the 12 already named.

3. **DECISIONS.md → ADR graduation.** DECISIONS.md is now at 27 entries. The
   file's own threshold ("graduate to per-file ADRs in `docs/adr/NNNN-title.md`
   when this file exceeds ~20") has been crossed. Action queued.

4. **Per-domain KB quality criteria.** Tier 1 #6 was reframed as "surface, not
   gate," but per-domain criteria (genomics, computational biology,
   environmental science) for the YAML-policy framework remain unspecified. A
   future session fills these in alongside the [KB-spec] KB-3.2
   implementation.

5. **fastmcp evaluation outcome.** Phase 2 spec needs the fastmcp evaluation
   result to commit MCP server-side construction technology. Output of Phase
   1f orchestration evaluation feeds this.

6. **Cartography skill development plan.** Tier 3 #25 surfaced Dan's interest
   in cartography + geospatial-DB integration. No phase-blocking decisions, but
   worth a small planning artifact in a future iteration.

---

## Suggested next steps (per the agreed plan)

The plan agreed with Dan was: **walk top-questions → mark resolutions → update
landscape docs → add DECs → rewrite planning-update-spec → execute spec via
Workers**. Steps 1–5 are complete in this session. Step 6 remains:

1. **Open `feature/planning-spec-2026-05-03` and execute Section 5.5 (SAFETY.md
   incident response) first** — the highest-priority Tier 0 item before any
   further env work.

2. **Execute the rest of Sections 5 (CLAUDE.md, VISION.md, ARCHITECTURE.md,
   ROADMAP.md edits)** in the recommended execution order in Section 8.1 of
   the spec. Either as a single Maestro Opus session (Pattern 1) or split
   across smaller Haiku Worker sessions (Pattern 2).

3. **Section 6 + 7** — create curation protocol and log; clone the 12
   community repos; write their one-page notes (parallel-by-default).

4. **Section 3 [KB-spec] tasks** — deliver to KnowledgeBase repo as separate
   PRs. KB-3.1 through KB-3.6 are independent; the KB-3.5 parallel-worker
   write coordination is the most architecturally complex and may benefit from
   a Maestro session rather than a Haiku-only execution.

5. **DECISIONS.md → ADR graduation** — separate session; not blocked by other
   work.

6. **Planning write-back at the close of subsequent planning sessions** — per
   DEC-0026 and the new CLAUDE.md Engineering Convention. Each multi-question
   planning session ends with a refresh of the relevant core files via a
   planning-update-spec.
