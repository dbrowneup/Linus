# Paper-Notes Session Summary — 2026-05-03

This document consolidates the per-batch checkpoint summaries from the 2026-05-03 / 2026-05-04
Maestro session that fanned out paper-note generation across the 39 PDFs Dan added to
[`context/papers/`](../../context/papers/) on 2026-05-02, plus 8 additional PDFs added
mid-session (2 forgotten, 6 newly acquired).

It is intentionally a recap, not a synthesis: the per-group `docs/syntheses/<group>-synthesis.md`
synthesis pass was executed within the same session and is summarized below; the wave-level
synthesis and landscape-doc weave were deferred to a future session per Dan's instruction.

---

## Pre-fan-out triage (2026-05-03)

Before any paper-note work began, the new corpus was triaged into thematic groups via four
parallel quick-skim agents (3-5 page extracts), one per ~10 papers. The triage produced 8
groups (A–H) covering all 39 papers:

| Group | Name | Papers (initial) |
|---|---|---|
| **A** | Biological Foundation Models | 8 (Evo 2, LucaOne, AlphaGenome, RiNALMo, Bacformer, ProteinReasoner, METL, REMME/REBEAN) |
| **B** | Generative Biology | 6 (mCSM-metal, GenNA, generative phages, DISCO, DeepSeMS, Trias) |
| **C** | Function Annotation, Reasoning & Discovery | 6 (Horizyn-1, DIAMOND DeepClust, ProtHGT, BioReason, BioReason-Pro, PertFormer single-cell) |
| **D** | Agentic Systems | 7 (Kosmos, Boiko/Gomes, BioGuider, Sketch2Simulation, TradingAgents, Agents survey, Practical Eval Guide) |
| **E** | LLMs in Science (meta) | 3 (Knuth claude-cycles, Binz PNAS Perspective, +dual-use threading) |
| **F** | Safety, Alignment & Privacy | 3 (Beaglehole steering, Values in the Wild, deanonymization, +dual-use biotech) |
| **G** | Infrastructure / Foundational Methods | 4 (Attention 2017, Flow Matching, PAN world model, Google environmental) |
| **H** | Humans & Teams | 2 (Güllich top performers, Harvey team learning) |

Wave plan agreed with Dan:

- **Wave 1**: Groups D + A + G (19 papers) — agentic + foundation + infra first
- **Wave 2**: Groups F + H + E (8 papers) — safety, humans, philosophy
- **Wave 3**: Groups C + B (12 papers) — function annotation + generative biology

**Decisions recorded before fan-out:**

1. **Paper-note format** — model on existing notes (`2502.16721v1.md`, `2208.07262v1.md`).
   Sections: TL;DR / The problem (in plain language) / What they propose / Key results /
   What's reusable in Linus / What's NOT applicable / Connections / Open questions for Dan.
2. **Length target** — calibrated to median (~1,597) and average (~1,748) of existing 31
   notes. Initial target ~1,400 words; soft ceiling 1,800; hard cap 2,500. (Workers
   consistently landed near the cap throughout — see "Process notes" below.)
3. **Read depth** — full PDF, not abstract-only. Worth the tokens for downstream synthesis
   precision.
4. **Smallest-first ordering** — across all of Wave 1 by file size, not within-group, for
   maximum bang-for-buck on opening batches.
5. **Workers attempt Linus-relevance sections** — given enough context about Linus, even
   shallow first drafts beat blank placeholders.
6. **Permissions allowlist** — added `Bash(pdftotext *)`, `Bash(pdfinfo *)`, `Bash(pdftoppm *)`
   to `.claude/settings.json` mid-Wave-1 after Dan flagged repeated permission prompts.
   `python3`/`sqlite3`/`curl`/`pip install`/`mkdir`/`rm`/`touch` deliberately NOT allowlisted
   (mutating or arbitrary-code-exec).

---

## Wave 1 — Groups D + A + G (19 papers, 4 batches)

### Batch 1 — 5 smallest Wave-1 papers (parallel)

**Workers:** BioGuider (D), Practical Eval Guide (D), Attention Is All You Need (G),
Google AI environmental impact (G), ProteinReasoner (A).

**Checkpoint notes from session:**

> All 5 paper-notes returned successfully. Word counts trended high — averaged ~2,100,
> well above the 1,400 target. The pattern: Linus-framing context was dense enough that
> "What's reusable in Linus" + "Connections" + "Open questions" sections expanded to fill
> the space. Quality looks high; not the 1,400 I targeted.
>
> Per-Worker token cost ~50K each; ~264K total Worker tokens for the batch.
>
> One prompt tweak for next batch: tighten the length cap.

| File | Words |
|---|---|
| 2026.02.09.704801v1.md (BioGuider) | ~1,800 |
| 2506.13023v1.md (LLM eval guide) | ~2,000 |
| NIPS-2017-attention-is-all-you-need-Paper.md | ~2,070 |
| 2508.15734v1.md (Google AI environmental) | ~2,200 |
| 2025.07.21.665832v2.md (ProteinReasoner) | ~2,476 |

### Batch 2 — next 5 smallest (parallel)

**Workers:** Sketch2Simulation (D), TradingAgents (D), REMME/REBEAN (A), Fundamentals of
LLM Agents (D), Boiko/Gomes auto-chemistry (D).

**Checkpoint notes from session:**

> Length tightening didn't fully take — Workers still landing near the ceiling. Pattern:
> Linus-framing context is dense enough that the "Reusable" + "Connections" sections
> always expand. Forcing shorter risks losing concrete connection-making. Keeping the cap
> as-is for the rest of Wave 1.
>
> Boiko/Gomes note tied directly to SAFETY.md autonomy tiers and the Wave-2 dual-use
> biotech paper — first cross-wave forward reference of the run.

| File | Words |
|---|---|
| 2603.24629v1.md (Sketch2Simulation) | ~2,100 |
| 2412.20138v7.md (TradingAgents) | ~2,150 |
| gkaf836.md (REMME/REBEAN) | ~2,393 |
| 2510.09244v1.md (LLM Agents survey) | ~1,935 |
| 2304.05332v1.md (Boiko/Gomes auto-chemistry) | ~1,671 |

### Batch 3+4 — final 9 papers (fired together as 2 simultaneous batches)

After Dan's session reset to 0% usage, Batches 3 and 4 fired simultaneously (10 agents in
parallel — exception to the 5-at-a-time pattern, justified by fresh usage budget).

**Workers (10):** METL, RiNALMo, Kosmos, Flow Matching textbook, LucaOne, Bacformer, PAN
world model, Evo 2, AlphaGenome — Wave 1 closing batch.

**Checkpoint notes from session:**

> Wave 1 paper-notes complete (19/19). Standout finding from Group D: Kosmos's structured
> "world model" suggests a candidate **fifth memory layer** distinct from the existing
> 4-layer pillar — "investigation memory" between scratchpad and episodic, holds shared
> structured state across multi-Worker investigations. Worth surfacing in the eventual
> Group D synthesis.
>
> Group A finding: 5 of 8 models are tractable as local M1 Max Workers; clear Phase 7 skill
> ordering emerges (REBEAN → Bacformer → RiNALMo → AlphaGenome+Evo2 hybrid).
>
> Group G finding: PAN paper triggers a "world models, three ways" disambiguation —
> PAN's visual-physical vs Kosmos's symbolic-shared vs Linus's episodic-durable. Same
> word, different objects. GLOSSARY.md flag.
>
> Flow Matching textbook (#14, 13 MB) was the largest Wave-1 PDF; treated as a reference
> map ("when would Dan reach for this") rather than tutorial transcription.

| File | Words |
|---|---|
| s41592-025-02776-2.md (METL) | 2,496 |
| s41467-025-60872-5.md (RiNALMo) | 2,223 |
| 2511.02824v2.md (Kosmos) | 2,540 |
| 2506.02070v3.md (Flow Matching textbook) | 2,051 |
| s42256-025-01044-4.md (LucaOne) | 2,200 |
| 2025.07.20.665723v2.md (Bacformer) | 2,467 |
| 2511.09057v3.md (PAN world model) | 2,161 |
| s41586-026-10176-5.md (Evo 2) | 2,441 |
| s41586-025-10014-0.md (AlphaGenome) | 2,478 |

**Wave 1 totals:** 19 paper-notes, ~42,300 words across notes, ~1.2M Worker tokens.

---

## Wave 1 group syntheses — D + A + G (3 parallel agents)

After all 19 Wave-1 paper-notes were complete, three group-summary agents fired in parallel
to produce per-group synthesis documents in `docs/syntheses/`.

**Checkpoint notes from session:**

> 3 group-synthesis Workers fired in parallel; all 3 returned successfully. Total Worker
> tokens ~440K. Each agent read the relevant paper-notes + skimmed `memory-synthesis.md`
> for style alignment.
>
> Standout cross-paper findings worth flagging up to Dan:
> - **Group D**: proposes a candidate **fifth memory layer** ("investigation memory")
>   for Kosmos-style structured shared state. Argues "Role" should be a first-class type
>   in the agent spawner.
> - **Group A**: recommends Phase 7 skill order **REBEAN → Bacformer → RiNALMo →
>   AlphaGenome+Evo2 hybrid**; flags METL as the right first Phase 6 fine-tuning exemplar.
>   Proposes new ADR for `external_api_tool` registry class to handle hosted-only models
>   like AlphaGenome.
> - **Group G**: proposes a `REFERENCE` paper-note tag for foundational anchors (Attention
>   + Flow Matching + Hogan KG); names the **three senses of "world model"** (PAN
>   visual-physical / Kosmos symbolic-shared / Linus episodic-durable) and recommends a
>   GLOSSARY.md disambiguation entry.

| File | Words |
|---|---|
| `docs/syntheses/agentic-systems-synthesis.md` (Group D) | ~3,400 |
| `docs/syntheses/biological-foundation-models-synthesis.md` (Group A) | ~4,284 |
| `docs/syntheses/infra-foundations-synthesis.md` (Group G) | ~2,819 |

---

## Wave 2 + Wave 3 paper-notes — Groups F, H, E + C, B (3 batches of 5)

Dan's instruction: complete all paper-notes and group-syntheses for Waves 2+3 before any
synthesis-of-syntheses or landscape work.

### Batch 5 — Wave 2 leadoff (5 smallest of remaining 20, parallel)

**Workers:** Knuth claude-cycles (E), dual-use biotech (F), Binz PNAS (E), LLM
deanonymization (F), top-performer development (H).

**Checkpoint notes from session:**

> 5 paper-notes returned successfully. Knuth's case is unusual in the corpus — first-person
> account by a respected mathematician of LLM mathematical reasoning. Framed as the
> "Maestro ceiling" — what hosted Claude can do that local Workers cannot.
>
> Dual-use biotech (2306.03809) tied directly to SAFETY.md and to the Boiko/Gomes auto-
> chemistry paper from Batch 2 — first sustained cross-batch dual-use thread.
>
> Deanonymization (2602.16800) sharpens the local-first ethos; argues KB-to-hosted-Maestro
> routing should be default-forbidden. Extends the existing security synthesis with a
> third leg (stylometric leakage beyond supply chain + prompt injection).

| File | Words | Group |
|---|---|---|
| claude-cycles.md (Knuth) | 2,191 | E |
| 2306.03809v1.md (dual-use biotech) | 2,499 | F |
| binz-et-al-2025-...md (PNAS Perspective) | 2,498 | E |
| 2602.16800v2.md (LLM deanonymization) | 2,488 | F |
| science.adt7790.md (Top performer development) | ~2,400 | H |

### Batch 6 — Wave 2 + Wave 3 transition (parallel)

**Workers:** Harvey team learning (H), Beaglehole steering (F), mCSM-metal (B), Horizyn-1
enzyme discovery (C), DIAMOND DeepClust (C).

**Checkpoint notes from session:**

> 5 returned successfully. Harvey team-learning paper (organizational behavior) is unusual
> in the corpus; framed via the Maestro/Worker-as-team metaphor at the team-episode
> timescale, complementing the existing cognitive-throughput pair (intra-second) and the
> Güllich paper (intra-career).
>
> Beaglehole (steering & monitoring of LLM activations) extends the existing security
> synthesis with a fourth leg — *technical mechanism* alongside supply-chain, prompt-
> injection, and stylometric-leak.
>
> Wave 3 began with mCSM-metal (Group B) and Horizyn-1 + DIAMOND DeepClust (Group C).
> mCSM-metal is webserver-only — first webserver-only paper in the run; raises tool-
> registry question of "external API wrapper" class. Horizyn-1's dual-encoder contrastive
> pattern surfaces as a candidate Linus architectural archetype.

| File | Words | Group |
|---|---|---|
| harvey-et-al-2023-...md (Team learning) | 2,416 | H |
| science.aea6792.md (Beaglehole steering) | 2,422 | F |
| 1-s2.0-S0022283626000513-main.md (mCSM-metal) | 2,216 | B |
| rocks-et-al-2026-...md (Horizyn-1) | 2,447 | C |
| s41592-026-03030-z.md (DIAMOND DeepClust) | 2,497 | C |

### Batch 7 — Wave 2 closer + Wave 3 (parallel)

**Workers:** ProtHGT (C), BioReason (C), Values in the Wild (F), GenNA (B), BioReason-Pro
(C).

**Checkpoint notes from session:**

> 5 returned successfully. ProtHGT directly bridges Group A (PLM substrate) and the
> KnowledgeBase architecture (heterogeneous KG) — argues for a "PLM + heterogeneous KG +
> graph transformer" Linus archetype.
>
> BioReason and BioReason-Pro form a tight pair (DNA-LM successor → protein-LM extension);
> both are empirical instantiations of CoT-escapes-TC0 in domain-FM contexts; worth citing
> in the existing memory synthesis.
>
> Values in the Wild (Anthropic, COLM) closes Group F as the cultural-empirical angle
> alongside Beaglehole's mechanism, deanonymization's threat-model, and dual-use biotech's
> design-policy. Four orthogonal axes on AI safety.

| File | Words | Group |
|---|---|---|
| 2025.04.19.649272v1.md (ProtHGT) | 2,490 | C |
| 2505.23579v2.md (BioReason) | 2,363 | C |
| Values_Paper__camera_ready_COLM_.md | 2,478 | F |
| 2026.04.22.720063v1.md (GenNA) | 2,373 | B |
| 2026.03.19.712954v1.md (BioReason-Pro) | 2,495 | C |

### Batch 8 — final paper-notes batch (5 largest Wave-3 Group B PDFs + last Group C)

**Workers:** DeepSeMS (B), Trias codon (B), generative phages (B), DISCO (B), PertFormer
single-cell (C).

**Checkpoint notes from session:**

> All 5 returned successfully. Closing batch — completed all 39 paper-notes from the
> original triage.
>
> Standout findings from this batch:
> - **Generative phages** is a watershed paper — first experimentally validated whole-
>   genome generative design. Direct dual-use implications connecting to SAFETY.md and to
>   the dual-use biotech paper.
> - **DISCO** is the most ambitious protein-design paper in the corpus (Frances Arnold lab,
>   joint sequence+structure diffusion validated by wet-lab carbene-transfer enzyme). Its
>   joint masked-discrete + continuous diffusion architecture is a non-trivial multimodal
>   generative design pattern.
> - **Trias** (47M BART) is the most M1-Max-friendly Group B model; high-frequency biotech
>   use case (codon optimization for mRNA design) makes it a top Phase 7 candidate.
> - **PertFormer** is the only cell-state-level paper in the corpus — a new modality
>   distinct from Group A's sequence FMs.

| File | Words | Group |
|---|---|---|
| 2025.03.02.641084v1.md (DeepSeMS) | 2,464 | B |
| 2025.05.13.653614v2.md (Trias codon) | 2,473 | B |
| 2025.09.12.675911v1.md (Generative phages) | 2,473 | B |
| 2604.05181v1.md (DISCO) | 2,427 | B |
| 2024.12.19.629561v2.md (PertFormer single-cell) | 2,470 | C |

**End of original-39 paper-notes phase.** All 39 notes complete; Worker tokens ~total 2.5M
across the run.

---

## Mid-session expansion (2026-05-04) — 8 additional papers

After all 39 original paper-notes were complete, Dan flagged 8 additional PDFs for
inclusion: 2 he had forgotten initially + 6 added during the session.

**Workers (8, parallel, self-discover prompts):** Each agent extracted title/abstract/
authors itself, wrote the note, and reported a suggested group at the end.

**Checkpoint notes from session:**

> 8 self-discover Workers fired in parallel; all 8 returned successfully. Self-discover
> approach worked well — each agent identified the paper, framed Linus-relevance, and
> reported a clean group recommendation.
>
> Identified papers and final group assignments (after Dan reviewed):
>
> - **2402.03755v1.md** — QuantAgent (HKUST/IDEA — two-loop self-improving agent w/ KB +
>   Bayesian-regret bound). 2,436 words. → **Group D**
> - **2509.09995v3.md** — QuantAgent (Stony Brook et al. — 4-agent LangGraph HFT). Same
>   name, different paper/team. 2,487 words. → **Group D**
> - **s41586-025-08600-3.md** — WHAM (Microsoft + Ninja Theory; 1.6B Nature world model
>   for Bleeding Edge multiplayer game). 1,750 words. → **Group G** (folds into world-model
>   thread)
> - **2503.19065v1.md** — WikiAutoGen (KAUST; multimodal Wikipedia-style article generation,
>   Storm/Co-Storm extension). 2,360 words. → **Group D**
> - **2503.00096v3.md** — BixBench (FutureHouse; 61-capsule bioinformatics agent benchmark
>   with Aviary 3-tool Jupyter scaffold). 2,418 words. → **Group D** (eval method;
>   reassigned from C after Dan's review)
> - **2407.10362v3.md** — LAB-Bench (FutureHouse; 2,457-question MCQ across 8 biology
>   research categories). 2,425 words. → **Group D** (eval method; reassigned from C
>   after Dan's review)
> - **bonsai-1-bit-8b-whitepaper.md** — PrismML Bonsai 1-bit 8B (Qwen3-8B 1-bit PTQ,
>   MLX-native, 1.15 GB, 131 tok/s on M4 Pro). 2,442 words. → **NEW Group I**
> - **bonsai-ternary-8b-whitepaper.md** — PrismML Bonsai Ternary 8B (Qwen3-8B ternary PTQ,
>   first openly released native-ternary 8B). 2,378 words. → **NEW Group I**
>
> **Two QuantAgent papers share a name but are different work** — flagged for the eventual
> Group D synthesis.
>
> **NEW Group I — Native Low-Bit Apple Silicon Inference** was created to absorb the two
> Bonsai whitepapers plus the existing 7-paper BitNet thread + LLM-in-a-Flash + Flash-MoE.
> The BitNet thread predated the 8-group triage; this expansion formalizes it as the most
> internally-coherent and operationally critical thread in the corpus for Phase 1c.
>
> **WHAM was the largest PDF of the entire run** at 134 MB (image-rich Nature SI). Worker
> handled it without issue using `pdftotext -l 30` first-pages limit when extraction was
> slow.

---

## Final group counts (after expansion)

| Group | Name | Paper Count |
|---|---|---|
| **A** | Biological Foundation Models | 8 |
| **B** | Generative Biology | 6 |
| **C** | Function Annotation, Reasoning & Discovery | 6 (PertFormer + 5 originals; LAB-Bench/BixBench moved to D) |
| **D** | Agentic Systems | 13 (7 originals + 4 new + LAB-Bench + BixBench) |
| **E** | LLMs in Science | 2 (claude-cycles, Binz; dual-use threading from F) |
| **F** | Safety, Alignment & Privacy | 4 (Beaglehole, Values, deanonymization, dual-use biotech) |
| **G** | Infrastructure / Foundational Methods | 5 (4 originals + WHAM) |
| **H** | Humans & Teams | 2 |
| **I** | Native Low-Bit Apple Silicon Inference | 11 (2 Bonsai + 7 BitNet + LLM-in-a-Flash + Flash-MoE) |
| **Total paper-notes after run** | | **47** |

---

## Group syntheses pass — 8 parallel agents (Wave 2+3 + 2 rewrites)

After all 47 paper-notes complete, 8 group-synthesis agents fired in parallel:

- **Group D — REWRITE** (paper set grew from 7 → 13, ~86% growth — full rewrite, not
  amendment)
- **Group G — LIGHT REWRITE** (added WHAM as fifth paper; expand "world models" thread)
- **Group A — SKIP** (no changes; existing synthesis still accurate)
- **Group B — NEW**
- **Group C — NEW** (LAB-Bench/BixBench reassigned to D mid-fan-out; Group C synthesis
  treats them anyway; relabeling deferred to landscape phase)
- **Group E — NEW**
- **Group F — NEW**
- **Group H — NEW**
- **Group I — NEW** (formalizes the BitNet thread + Bonsai whitepapers + streaming work)

**Checkpoint notes from session:**

> 8 group-synthesis Workers fired in parallel; all 8 returned successfully. Some ran over
> target word counts (B at 5,800 vs 4,000; C at 4,890 vs 4,500; I at 6,800 vs 5,500).
> Dan flagged this mid-run with "stop the minor wordsmithing to cut word counts, we're
> burning tokens unnecessarily" — but agents had already completed by the time the
> message arrived.
>
> Dan also clarified mid-run that **LAB-Bench and BixBench should belong in Group D**
> (eval methods alongside Practical Eval Guide), not Group C as my initial call placed
> them. The Group D synthesis (rewrite) treated them as members; the Group C synthesis
> also discussed them. Net result: both syntheses cover the papers; the assignment is
> metadata. Relabeling deferred to landscape phase.

| File | Words | Group |
|---|---|---|
| `docs/syntheses/agentic-systems-synthesis.md` (REWRITE) | 4,591 | D |
| `docs/syntheses/infra-foundations-synthesis.md` (REVISION) | 3,556 | G |
| `docs/syntheses/generative-biology-synthesis.md` (NEW) | ~5,800 | B |
| `docs/syntheses/function-annotation-discovery-synthesis.md` (NEW) | ~4,890 | C |
| `docs/syntheses/llms-in-science-synthesis.md` (NEW) | 2,500 | E |
| `docs/syntheses/safety-alignment-privacy-synthesis.md` (NEW) | 3,829 | F |
| `docs/syntheses/humans-teams-performance-synthesis.md` (NEW) | ~2,600 | H |
| `docs/syntheses/native-low-bit-apple-silicon-synthesis.md` (NEW) | ~6,800 | I |

**Standout findings from the synthesis pass:**

- **Group D synthesis (rewrite)** promotes "structured inter-agent communication" from a
  sub-point to its own first-class thread (8 cross-cutting threads, was 7). Adds Thread 8
  on agentic-system theory (anchored by HKUST QuantAgent's Bayesian-regret bound).
  Re-evaluates and *strengthens* the prior synthesis's three claims: Role-as-first-class-
  type, fifth "investigation memory" layer, multi-level validation as spawner primitive.
  Adds new role-tuple fields: `model_tier` and `episodic_schema`. WikiAutoGen's WikiSeek
  benchmark methodology added as a new evaluation pattern.
- **Group G synthesis (revision)** expands "world models, three ways" → **four ways**
  (PAN visual-physical, WHAM game-state video-token, Kosmos symbolic-shared, Linus
  episodic-durable). Adds new thread on **capability-first measurement** linking WHAM's
  consistency/diversity/persistency framework to the Practical Eval Guide and the
  Speed/LLMs paper. Proposes a parallel **METHOD** paper-note tag alongside the existing
  REFERENCE proposal.
- **Group B synthesis** organizes papers by *artefact scale* (single residue → codon →
  mid-scale text-conditional → single protein → BGC/molecule → whole genome). Proposes
  3-tier SAFETY.md addendum (Tier 1 low-risk; Tier 2 designer-enzyme with deny-list;
  Tier 3 whole-genome forbidden by default with per-session opt-in). Names 5 generalist+
  specialist combination recommendations (Trias+GenNA, REBEAN+DeepSeMS, Bacformer+
  DeepSeMS, mCSM-metal+DISCO, AlphaGenome+GenNA).
- **Group C synthesis** organizes papers in 4 archetypes (methods, reasoning, cross-
  modality, benchmarks). Notes the FutureHouse lineage as a continuous program: LAB-Bench
  → BixBench → Kosmos. Recommends Phase 1 LAB-Bench/BixBench baseline before Worker-
  selection skills work. Endorses both proposed archetype names ("PLM + heterogeneous KG
  + graph transformer", "dual-encoder cross-modal retrieval").
- **Group E synthesis** ("Where Linus stands" section is the most original content):
  articulates Linus's *implicit* hybrid position across the four Binz perspectives —
  "collaborator with bounded delegation, instrumented for attribution, with the scientific
  roadmap reserved for the human." Recommends VISION.md/CLAUDE.md absorb this framing.
- **Group F synthesis** maps each of 4 papers to a **distinct SAFETY.md addition**.
  Proposes `linus.observability.activations.*` API stub (Phase 7 from Beaglehole),
  `privacy_tier` field on each tool/skill (from deanonymization), redact-before-paste
  Maestro tooling, query-screening at orchestration layer (from dual-use biotech).
- **Group H synthesis** articulates the **Maestro/Worker analogy at three timescales**
  (intra-second cognitive throughput, team-episode harmony/rhythm, intra-career
  development). The metaphor survives all three scales — meaningful coherence check.
  Proposes a `goal_orientation` field on Worker specs (so Linus knows what to batch vs.
  sequence). Sharpens the existing skills-and-practices synthesis from "domain expertise
  as moat" to "*cross-domain* expertise as moat."
- **Group I synthesis (largest)** traces the research → productization trajectory:
  2023 BitNet exists in principle → 2024 b1.58 ternary + bitnet.cpp + 2B4T checkpoint →
  2025 v2 + BitDistill → 2025-26 Bonsai 1-bit/Ternary 8B as first MLX-native productized
  large-scale low-bit LLMs. **Bonsai 8B at 1.15 GB makes mlx-flash unnecessary at the
  8B class** — Phase 6d stretch target met ahead of schedule. Surfaces **MLX ternary
  kernel gap** as the most tractable Linus contribution opportunity in the entire corpus
  (connects to repos/pmetal). Recommends Phase 1c spike scope expansion to 4-way
  comparison: BitNet 2B4T + Bonsai Ternary 8B + Bonsai 1-bit 8B + Bonsai Ternary 4B.

---

## Cumulative run totals

| Metric | Value |
|---|---|
| Original paper-notes triage groups | 8 (A–H) |
| Original paper-notes triage papers | 39 |
| Mid-session paper additions | 8 (2 forgotten + 6 added during) |
| **Total paper-notes after run** | **47** |
| New group created mid-run | 1 (I — Native Low-Bit Apple Silicon Inference) |
| Final group count | 9 (A–I) |
| Paper-note batches fired | 8 (5 + 5 + 5 + 4 + 5 + 5 + 5 + 5 + 8 self-discover) |
| Group syntheses fired (Wave 1) | 3 (D, A, G) |
| Group syntheses fired (Wave 2+3 + rewrites) | 8 (B, C, E, F, H, I + D rewrite + G revision) |
| **Total group syntheses produced** | **9** (A from Wave 1 untouched; D and G updated) |
| Wave-level syntheses fired | 0 (deferred per Dan's instruction) |
| Landscape-doc weave fired | 0 (deferred per Dan's instruction) |

---

## Outstanding questions for next session

These are the items surfaced during the run that need Dan's direction or further investigation
before the wave-level synthesis pass can proceed cleanly:

### Categorization (cleanup)

1. **LAB-Bench + BixBench formal relabeling.** Dan clarified mid-fan-out that both belong
   in Group D (eval methods) rather than Group C as my initial call placed them. Both the
   Group D synthesis (rewrite) and the Group C synthesis treat them in detail. The
   relabeling can be folded into the eventual landscape-doc weave as metadata cleanup;
   no re-running of agents needed.

### Process

2. **Word-count drift.** Workers consistently landed near the 2,500-word hard cap rather
   than the 1,400-word target. The Linus-framing context in prompts was dense enough that
   the "Reusable" + "Connections" + "Open questions" sections always expanded. For future
   fan-out work: either accept the higher words as the natural output, or write tighter
   Linus-framing context.

3. **Dan flagged "stop minor wordsmithing"** mid-synthesis-batch when agents were running
   over target. Agents had already completed by the time the message arrived. For future
   batches: explicit "do not iterate on length post-completion" instruction in Worker
   briefs.

4. **Permissions allowlist tightening.** `Bash(pdftotext *)`, `Bash(pdfinfo *)`,
   `Bash(pdftoppm *)` added to `.claude/settings.json` mid-Wave-1. Worked. No further
   prompts after that. For future bio-PDF-heavy fan-outs, this allowlist is now baked in.

### Decisions surfaced by paper-note + synthesis findings (sample — see individual syntheses for full lists)

5. **Phase 1c BitNet spike scope expansion.** Group I synthesis recommends benchmarking
   {BitNet 2B4T, Bonsai 1-bit 1.7B/4B/8B, Bonsai Ternary 8B} together with a unified
   harness using task-completion-time methodology from `paper-notes/2502.16721v1.md`.

6. **MLX ternary kernel as a Linus contribution.** Group I synthesis surfaces this as
   well-scoped, tractable, and connects to repos/pmetal. Worth a Phase 1d or Phase 6d
   ADR.

7. **Fifth memory layer ("investigation memory")** proposed by Group D synthesis.
   Distinct from existing 4-layer memory pillar; sits between scratchpad and episodic;
   holds Kosmos-style structured shared state across multi-Worker investigations.
   Worth surfacing as a memory-architecture spec amendment.

8. **`external_api_tool` registry class** proposed by Group A synthesis to handle hosted-
   only models like AlphaGenome, plus extended in Group B synthesis to webserver-only
   tools like mCSM-metal. Worth an ADR.

9. **3-tier SAFETY.md addendum for generative biology** proposed by Group B synthesis
   (low-risk / designer-enzyme with deny-list / whole-genome forbidden by default). Tied
   to the dual-use biotech paper (Group F) and the generative phages paper (Group B).

10. **VISION.md / CLAUDE.md additions** surfaced across multiple syntheses:
    - Group E: explicitly cite Binz et al. and stake out Linus's implicit hybrid position
    - Group H: candidate principle "Linus aids multidisciplinary synthesis, not narrow
      execution"
    - Group F: Maestro-values dependencies declaration
    - Group I: Phase 6d reframing now that Bonsai meets the stretch target

11. **GLOSSARY.md disambiguation: three (now four) senses of "world model"** — surfaced
    in Wave 1 by Group G, expanded in Wave 2/3 with WHAM addition.

12. **`docs/syntheses/repo-clusters/` parallel** — note that the fan-out work documented
    in `docs/session-summaries/2026-05-04-fan-out-session-summary.md` produced 10 repo-cluster groups
    on a parallel track. The 9 paper-note groups + 10 repo-cluster groups will both feed
    the eventual landscape-doc rewrite.

---

## Suggested next steps (per the agreed plan)

The plan agreed with Dan was: **paper-notes → group syntheses → wave syntheses → landscape
weave**. Steps 1 and 2 are complete. Steps 3 and 4 are deferred:

1. **Wave-level syntheses (3 documents)** — one per wave (Wave 1 = D + A + G; Wave 2 = F +
   H + E; Wave 3 = C + B). Plus a synthesis covering Group I (which spans no single wave).
   These would each take the relevant group syntheses as input and produce a cross-group
   picture. Deferred per Dan's instruction.

2. **Landscape-doc weave** — extend `docs/landscapes/paper-landscape.md` with all 47
   paper-notes (organized by group); update `docs/landscapes/synthesis-landscape.md` with
   all 9 group syntheses; rewrite `docs/landscapes/total-landscape.md` cross-cutting
   crossings to absorb the new material. Deferred per Dan's instruction.

3. **LAB-Bench + BixBench relabeling** — fold into landscape weave as metadata cleanup
   (both syntheses already cover the papers).

4. **Open-questions sweep** — extract every "Open questions for Dan" from each paper-note
   into `open-questions.md`; promote any Tier 1 candidates into `top-questions.md`.

5. **CLAUDE.md / VISION.md write-back** — pull in the implications surfaced by the
   syntheses (per item 10 in Outstanding Questions above).
