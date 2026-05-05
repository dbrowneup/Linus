# Planning-Update Session Summary — 2026-05-05

This document recaps the 2026-05-05 Maestro session that processed a fresh batch of papers, threads,
and notes from `context/`, produced new synthesis documents, and propagated the implications
into the existing planning landscape (`paper-landscape.md`, `total-landscape.md`,
`open-questions.md`, `top-questions.md`) plus a new preliminary
[`planning-update-draft.md`](../planning-update-draft.md).

It is intentionally a recap, not a synthesis: the planning-update draft is itself the synthesis
artefact; this document records the run shape, the parallel-agent structure, the late-stage
wrong-path fix, and the outstanding follow-ups.

---

## Pre-fan-out scoping

Dan's brief framed the session as a multi-part batch operation against `context/`:

1. Summarize the 5 new PDFs in `context/papers/` that lacked notes in `docs/paper-notes/`
2. Read and synthesize all 9 files in `context/threads/` (Karpathy LLM Wiki Gist, Karpathy
   Wiki Repos, Rohit v2 Gist, 17 Skills → $312/Day, Top 50 Claude Skills & Repos, 17 Best
   Practices for Claude Cowork, Cline description, Stop Staring at Files, Autoresearching
   Apple's LLM in a Flash)
3. Incorporate `context/notes/COMMUNITY_INSIGHTS.md` and `context/notes/KB_DESIGN_PATTERNS.md`
4. Update the four landscape/agenda docs (`open-questions.md`, `top-questions.md`,
   `total-landscape.md`, `paper-landscape.md`)
5. Produce three new synthesis documents (LLM wiki, skills/practices, security)
6. Produce a preliminary planning-update document ahead of any roadmap revision
7. Address the security concerns triggered by the litellm supply chain incident (Karpathy
   tweet) — supply chain mitigations and prompt-injection defenses
8. Carry the entrepreneurial framing through the synthesis (Dan's stated dream of leveraging
   AI for recurring passive income; PhD biochemistry/genomics + algae biotech founder
   background)

**Decisions recorded before fan-out:**

1. **Paper-note format** — match the existing template (`2502.16721v1.md`,
   `2208.07262v1.md`): TL;DR / Problem / What they propose / Key results / Reusable in
   Linus / NOT applicable / Connections / Open questions for Dan.
2. **Parallelism** — fan out via Agent subagents rather than one-shot reads. Dan asked for
   `/batch`, which wasn't available; substituted background Agent calls (8 agents fired).
3. **Two-tree write** — paper-notes were intended for both the main repo and the worktree.
   This decision is the source of the Section "Wrong-path error and recovery" issue below.
4. **Synthesis scope** — three new synthesis documents in `docs/`: LLM wiki + community
   insights, skills/practices/entrepreneurial, security posture.

---

## The 5 new paper-notes (parallel, 5 agents)

Identified by diffing `context/papers/` listing against existing `docs/paper-notes/`. Two
clean pairs surfaced from filenames alone — two cognitive-throughput neuroscience papers
forming a debate, and two keyphrase extraction papers forming a Phase 2 → Phase 3 KB
ingestion path.

**Checkpoint notes from session:**

> All 5 paper-notes returned successfully, written to both main repo `docs/paper-notes/`
> and worktree `docs/paper-notes/`. The two-pair structure of the corpus (rather than
> 5 unrelated papers) made the Linus-relevance threading much tighter than expected.
>
> Standout findings:
> - **Speed and LLMs (2502.16721)** is methodologically the most consequential of the
>   five for Phase 1 — task-completion-time rankings *invert* tok/s rankings across 5 ~7B
>   models, which means the planned Worker selection methodology built on Ollama's tok/s
>   leaderboard is wrong from the start. The three-task schema (minimal output / fixed-
>   length / open-ended) is a ready-made template for `benchmarks/dan_tasks/`.
> - **RaKUn 2.0 (2208.07262)** closes a previously-open gap in the KB ingestion pipeline:
>   no specified keyphrase extraction method existed before. CPU-only, pure Python, 2 OOM
>   faster than YAKE/MultiPartiteRank, validated on 14M biomedical docs in ~40s on M1-Max-
>   comparable hardware. Phase 2 baseline.
> - **KGRank (s41019-017-0055-z)** is the Phase 3 upgrade path — replace DBpedia with GO,
>   MeSH, or ChEBI for Dan's biomedical corpus.
> - **Zheng & Meister (PIIS0896627324008080)** — ~10 bits/s human conscious throughput
>   regardless of modality; Si=10⁸ sifting number. Direct architectural implication: parallel
>   Worker fan-out generates zero throughput gain unless Maestro interface compresses
>   outputs to ~10 bits/s before presenting them.
> - **Sauerbrei & Pruszynski (nihms-2096004)** — direct rebuttal: 10 bits/s is a *lower*
>   bound on whole-brain throughput, not upper bound. Cerebellum (half of all brain neurons)
>   operates unconsciously at far higher rates. Sharpens the Maestro/Worker analogy:
>   Workers handle the high-bandwidth substrate; Dan+Claude handle the narrow conscious
>   synthesis channel.

| File | Group |
|---|---|
| `2502.16721v1.md` (Speed and LLMs) | Benchmarking & inference evaluation |
| `2208.07262v1.md` (RaKUn 2.0) | KB ingestion — keyphrase extraction (Phase 2 baseline) |
| `s41019-017-0055-z.md` (KGRank) | KB ingestion — keyphrase extraction (Phase 3 enriched) |
| `PIIS0896627324008080.md` (Zheng & Meister) | Cognitive throughput / human-AI interface |
| `nihms-2096004.md` (Sauerbrei & Pruszynski) | Cognitive throughput / human-AI interface |

---

## The 3 new synthesis documents (parallel, 3 agents)

Three synthesis agents fired in parallel against the 9 thread files + 2 community-notes
files in `context/`. Each produced a full document in main-repo `docs/`.

**Checkpoint notes from session:**

> 3 synthesis Workers fired in parallel; all 3 returned successfully. Each pulled from a
> distinct slice of `context/threads/` + `context/notes/`. Total Worker tokens were higher
> than per-paper-note averages because each synthesis read multiple inputs and produced a
> longer document. No retries needed.
>
> Standout findings:
>
> **LLM Wiki synthesis (`llm-wiki-synthesis.md`)** — 14 core KB design concepts surfaced;
> 20 community repos catalogued; 8 suggested for `repos/` (omega-memory, keppi,
> rohitg00/agentmemory, openaugi, qmd, the-knowledge, multi-agent-wiki, agentic-research-
> wiki). Two highest-ROI immediate disciplines: the **write-back rule** (mutate KB on
> insight, not just retrieve) and **quality-gate-at-ingest** (block low-quality content
> at the door, don't try to rank around it later). 9 open questions including the one most
> consequential for Phase 3: how to coordinate parallel-Worker writes to the same KB pages
> (git-branch-per-ingestion vs. mesh sync vs. last-write-wins).
>
> **Skills & Practices synthesis (`skills-and-practices-synthesis.md`)** — 12 new repo
> candidates beyond what's in `repos/` (top: fastmcp, Task Master AI, claude-squad,
> rendergit). 7 entrepreneurial opportunities pinned to current Linus capabilities; the
> most immediate is **scientific literature intelligence retainer** (~$1k–$3k/month/client)
> using hosted Claude + domain expertise *today*, while Linus builds in the background.
> Raises a sharp Algorithm-question for Phase 2: does Linus need a custom orchestration
> layer, or do Task Master AI + claude-squad cover it? *Delete before building.*
>
> **Security synthesis (`security-synthesis.md`)** — One immediately actionable finding:
> `langchain`, `langgraph`, and `haystack-ai` are installed in `environment.yml` for "future
> Phase 3+ evaluation" but serve no current function — large transitive trees, fast
> release cadence, and the orchestration logic they would eventually provide is exactly
> Linus's core product. Removing them costs nothing. Adds a **Tier 0** to top-questions.md
> for concrete pre-Phase-1 actions. Also articulates the threat-class distinction between
> SAFETY.md (operational autonomy) and supply chain / prompt injection (which bypass
> SAFETY.md entirely because they run inside the package or inside the model context window
> before any tool call). 5 open questions requiring Dan's values-level input.

| File | Words |
|---|---|
| `docs/llm-wiki-synthesis.md` | ~5,000 |
| `docs/skills-and-practices-synthesis.md` | ~4,300 |
| `docs/security-synthesis.md` | ~3,500 |

---

## Planning-update draft (single agent)

After all 5 paper-notes and 3 syntheses were complete, a single agent produced the
[`docs/planning-update-draft.md`](../planning-update-draft.md) document — a preliminary
synthesis of what changed in the plans, surfacing practical consequences without
pre-resolving the open questions.

**Checkpoint notes from session:**

> Single agent; ~250 lines; clean first pass. Seven changes to plans surfaced and pinned
> to specific phases:
>
> 1. **Tier 0 security hygiene before Phase 1** — remove the three pre-emptive ML
>    framework packages, add `requirements-locked.txt` with hash verification, document
>    the dependency philosophy in CLAUDE.md.
> 2. **Phase 1 benchmark methodology change** — restructure `benchmarks/dan_tasks/`
>    around task-completion time (three-task schema), not tok/s.
> 3. **KB ingestion pipeline gets a theory-to-implementation path** — RaKUn 2.0 in
>    Phase 2, KGRank-style enrichment in Phase 3.
> 4. **Phase 2 output interface gets a quantitative design constraint** — high-information-
>    density concise outputs by default, verbose opt-in, grounded in the ~10 bits/s
>    cognitive throughput literature.
> 5. **Phase 2 orchestration scope question** — investigate Task Master AI + claude-squad
>    as a potential alternative to a custom Phase 2 orchestration layer (The Algorithm:
>    delete before building).
> 6. **Community repos prioritized list** — 8 from LLM wiki synthesis + 3 from skills
>    synthesis worth cloning to `repos/` as study material; additive, low-risk.
> 7. **Cline → Ollama → Qwen2.5-Coder 32B** is now a concrete Phase 1 Worker IDE harness
>    path that requires no new infrastructure.
>
> The document explicitly defers final roadmap revision until Dan answers the Tier 0
> action and the new Tier 1 questions (#13 orchestration scope, #14 monetize-now).

---

## Wrong-path error and recovery

After all agents completed and the four landscape/agenda doc updates were made, Dan
opened `docs/total-landscape.md` in his IDE and noticed the document still showed the
*old* content. The four updates had been made to the **worktree copies**
(`.claude/worktrees/infallible-satoshi-4fa61a/docs/`) instead of the main repo
(`/Users/dbrowne/Desktop/Programming/GitHub/Linus/docs/`).

Dan's message: *"I think there was a mistake with the total-landscape.md document. Perhaps
the wrong file was modified? I may have pointed at the wrong file accidentally.
@docs/total-landscape.md is the correct file to modify. I can see I made the same mistake
with @docs/paper-landscape.md, unfortunately, plus @docs/open-questions.md and
@docs/top-questions.md. Could you please fix that real quick?"*

**Recovery:**

1. Read all four updated worktree docs to extract the new content.
2. Read the current main-repo versions (Edit/Write requires having Read first).
3. Wrote the updated content to all four main-repo paths in parallel.

Net result: the four files in main-repo `docs/` now carry the same updates as the
worktree copies. The worktree copies are unchanged (and harmless). This was process
error, not content error — the synthesis work itself was correct.

**Process note for future fan-outs:** when Dan asks for updates to existing docs,
default to the **main repo path**, not the worktree path, unless explicitly told
otherwise. Worktree paths look identical to main-repo paths in tool output but the
files do not auto-merge back.

---

## The four landscape/agenda doc updates

After the wrong-path recovery, the four documents now reflect the new material:

**[`docs/paper-landscape.md`](../paper-landscape.md)** — added 3 new thematic sections
(Benchmarking, KB-ingestion-keyphrase-extraction, Cognitive-throughput); updated Phase 2
and Phase 3 reading orders; added cross-cutting questions 8–10.

**[`docs/total-landscape.md`](../total-landscape.md)** — added 5 rows to the theme table;
"Two observations" → "Four observations" (added keyphrase-extraction observation +
security observation); added Crossing 4 (security posture vs. development velocity);
added 2 new gaps (orchestration decision, commercial surface); updated work-products
section pointing to the three new synthesis docs.

**[`docs/open-questions.md`](../open-questions.md)** — added 5 new paper question sets
(Speed/LLMs, RaKUn 2.0, KGRank, Unbearable Slowness, Brain >10 bits/s) plus a new
**Part 3** with synthesis-doc questions (LLM wiki ×8, skills/practices ×5, security ×5).

**[`docs/top-questions.md`](../top-questions.md)** — new **Tier 0** for the immediate
dep-cleanup action; new Tier 1 items #13 (Task Master AI vs. custom orchestration) and
#14 (monetize now vs. build first); new Tier 3 items #19–23 (benchmark architecture,
keyphrase strategy, security decisions, 10 bits/s interface, community repos); updated
"How to use this document" section.

---

## Cumulative run totals

| Metric | Value |
|---|---|
| New paper-notes | 5 (written to both main repo and worktree) |
| New synthesis documents | 3 (LLM wiki, skills/practices, security) |
| New planning documents | 1 (planning-update-draft.md) |
| Existing landscape/agenda docs updated | 4 (paper-landscape, total-landscape, open-questions, top-questions) |
| Parallel agents fired | 9 (5 paper-notes + 3 syntheses + 1 planning draft) |
| Wrong-path errors recovered | 4 (landscape/agenda docs initially written to worktree) |

### Integrate-class verdicts surfaced for planning revision

1. **RaKUn 2.0** — Phase 2 KB ingestion baseline. `pip install rakun2`; CPU-only;
   validated on biomedical corpora at M1-Max-comparable scale.
2. **Three-task benchmark schema** (Speed and LLMs) — Phase 1 `benchmarks/dan_tasks/`
   structure. Task-completion time as primary metric, not tok/s.
3. **Cline → Ollama → Qwen2.5-Coder 32B** — Phase 1 working Worker IDE harness with no
   new infrastructure required.
4. **Tier 0 dep cleanup** — remove `langchain`, `langgraph`, `haystack-ai` from
   `environment.yml`; add `pip-compile --generate-hashes` lock file. Pre-Phase-1.

### Tier 3 / future references

- **KGRank** — Phase 3 ontology-grounded keyphrase enrichment (substitute GO/MeSH/ChEBI
  for DBpedia)
- **8 community repos** flagged for `repos/` (omega-memory, keppi, rohitg00/agentmemory,
  openaugi, qmd, the-knowledge, multi-agent-wiki, agentic-research-wiki)
- **3 additional repos** from skills synthesis (fastmcp, Task Master AI, claude-squad)
- **Output interface design constraint**: high-information-density concise output as the
  Phase 2 default, grounded in ~10 bits/s human review throughput

---

## Outstanding questions for next session

These are the items surfaced during the run that need Dan's direction or further investigation
before the planning-update-draft can be promoted to a roadmap revision:

### Process

1. **Default to main-repo paths, not worktree paths.** Process note for any future
   multi-doc update fan-out — when updating an existing doc that lives in main-repo
   `docs/`, write to the main-repo path, not the worktree mirror, unless explicitly
   instructed otherwise.

2. **Two-tree paper-notes strategy.** The 5 new paper-notes were written to both main
   repo and worktree. This was correct for paper-notes (they're additive), but the
   landscape/agenda docs are *single-source-of-truth* and should only be updated in main.
   Worth codifying the rule explicitly: paper-notes → both; landscape/agenda → main only.

### Tier 0 (no decision needed — execution only)

3. **Remove `langchain`, `langgraph`, `haystack-ai` from `environment.yml`** and add
   `requirements-locked.txt` via `pip-compile --generate-hashes`. Document dependency
   philosophy in CLAUDE.md. One session of work; no architectural decision.

### Tier 1 decisions surfaced or sharpened by this run

4. **Phase 6 fine-tuning target (genomics-specialized vs. coding-specialized)** should be
   made by Phase 3, not deferred to Phase 6. The decision changes which entrepreneurial
   opportunities become viable post-fine-tune. *(top-questions.md Tier 1 #3, sharpened
   by skills synthesis Q4.)*

5. **Phase 2 orchestration scope: Task Master AI + claude-squad vs. custom layer.**
   Investigate as Phase 1b parallel evaluation alongside the pmetal evaluation.
   *(new top-questions.md Tier 1 #13.)*

6. **Monetize now vs. build first.** Should Dan start a scientific-literature-intelligence
   retainer engagement *now* using hosted Claude + domain expertise, or defer until
   Phase 2+ Linus infrastructure is ready? Real client feedback is more valuable than
   speculative roadmap planning. *(new top-questions.md Tier 1 #14.)*

### Decisions for downstream propagation

7. **`benchmarks/dan_tasks/` design** should be restructured around the three-task schema
   from the Speed/LLMs paper before Phase 1 Worker-selection work begins. Cheap to do
   right now; expensive to retrofit later.

8. **RaKUn 2.0 smoke test** on 20–50 papers from `context/papers/` at τ ∈ {0.5, 1.0, 1.5}
   — validates the merge threshold for Dan's biomedical/genomics domain before Phase 2
   ingestion pipeline work begins.

9. **Phase 2 output interface design**: high-information-density concise outputs as the
   default, with verbose mode opt-in, grounded in the ~10 bits/s cognitive throughput
   literature. Should land as a concrete design constraint in the Phase 2 spec.

10. **8+3 community repos for `repos/`** — additive, low-risk, no operational cost. Could
    be a single-session clone-and-document task between sessions.

### Cross-cutting findings

11. **The Maestro/Worker architecture is now grounded in two distinct pieces of theory** —
    the Maestro budget discipline (which was The Algorithm + practitioner experience) plus
    the cognitive-throughput literature (Zheng/Meister + Sauerbrei/Pruszynski). The
    architecture survives the test of being articulable from independent grounds.

12. **The entrepreneurial framing is now planning-level, not background.** Dan's stated
    goal of "leverage AI to build recurring passive income" is reflected in
    `docs/skills-and-practices-synthesis.md` (7 opportunities), in `total-landscape.md`'s
    new gap entry, and in `top-questions.md` Tier 1 #14. Worth surfacing as a `docs/
    entrepreneurial-surface.md` deliverable in a near-term session.

13. **Security posture is now a cross-cutting concern, not a deferrable item.** The
    litellm incident provides a concrete event-anchor; the SAFETY.md / supply-chain /
    prompt-injection threat-class distinction is now articulated; Tier 0 actions are
    pinned. Worth a follow-up session to execute the Tier 0 cleanup.

---

## Suggested next steps (per the agreed plan)

The plan was: **paper-notes → syntheses → planning-update-draft → landscape/agenda
propagation**. All four steps are complete. The natural next steps:

1. **Execute Tier 0** — remove the three packages from `environment.yml`, rebuild env,
   add lock file, document philosophy in CLAUDE.md. ~1 session.

2. **Walk Tier 1 in conversation** — focused conversation on the five Tier 1 items, with
   `total-landscape.md` open as the map. Each Tier 1 answer typically resolves 2–3
   downstream questions.

3. **Promote planning-update-draft to a roadmap revision** — once Tier 0 and Tier 1 are
   resolved, revise `ROADMAP.md` and add per-decision ADRs in `docs/adr/` (or
   `DECISIONS.md` per the project's ADR convention).

4. **Optional: clone the 11 community repos** into `repos/` as a single-session additive
   task before Phase 2 design begins.

5. **Optional: write `docs/entrepreneurial-surface.md`** — pull the 7 opportunities from
   the skills synthesis into a concrete deliverable, including the immediate "what would
   one client engagement look like" framing.
