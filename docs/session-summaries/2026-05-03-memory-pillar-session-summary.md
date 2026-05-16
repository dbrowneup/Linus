# Memory-Pillar Session Summary — 2026-05-03

This document consolidates the work of the same-day follow-up Maestro/Dan planning session that
ran after the original 2026-05-03 multi-question planning session (whose Tier 0/1/2/3 resolutions
landed as DEC-0012 through DEC-0027 in
[`planning-update-spec.md`](../specs/planning-update-spec.md)). The follow-up session is the work
that turned Erik Garrison's _Memory makes computation universal, remember?_ thesis into a
Phase 2 architectural commitment for Linus.

It is intentionally a recap, not a synthesis: the synthesis itself lives at
[`docs/syntheses/memory-synthesis.md`](../syntheses/memory-synthesis.md), the per-question
resolutions live in [`top-questions.md`](../questions/top-questions.md), the architectural
contract lives in [`docs/specs/memory-architecture.md`](../specs/memory-architecture.md), and the
16 ratifying ADRs live in [`docs/adr/`](../adr/) at DEC-0028 through DEC-0043.

---

## Session shape (in execution order)

The session followed a single arc — read a piece of context, fan out work over it, synthesise,
roll up — but layered three concerns: research integration (paper notes + synthesis), planning
resolution (17 prioritised questions), and artifact production (16 ADRs + 1 architecture spec +
landscape and questions roll-up). The arc:

1. **Article ingestion (Garrison nucleus).** Read Erik Garrison's January 2025 essay _Memory
   makes computation universal, remember?_ (saved to `context/notes/` as the raw article text)
   plus the companion arXiv proof paper [2412.17794](../../context/papers/2412.17794v1.pdf).
   Produced a synthesised Linus-relevant note at
   [`context/notes/garrison_memory_makes_computation_universal.md`](../../context/notes/garrison_memory_makes_computation_universal.md)
   that absorbs both, fixes a fact error from an earlier draft (the Memphis plume is the TVA
   Allen Combined Cycle gas plant, not xAI's Colossus), and reframes the implications around
   Linus's memory pillar rather than around hosted-Claude usage.

2. **Confirmation step before fan-out.** Listed the 11 Garrison-cited arXiv papers Dan had
   already added to `context/papers/` (Dan provided the exact filenames so I didn't have to
   guess). Confirmed framing — all 11 read primarily through the memory lens, with the
   standard Linus-applicability sections still included — and order of operations for the
   roll-up phase.

3. **Paper-note fan-out (11 parallel sub-agents).** One Worker per paper, all parallel, each
   following the existing `docs/paper-notes/` template (TL;DR / problem / what they propose /
   key results / what's reusable in Linus / hype filter / connections / open questions for
   Dan). Each Worker explicitly instructed to foreground the memory framing and produce at
   least three open questions framed against the memory pillar where natural.

4. **Read all 11 notes inline.** Mandatory before synthesis-writing per the agreed flow. Used
   parallel Read tool calls to keep the round-trip down.

5. **Wrote `docs/syntheses/memory-synthesis.md`.** Three-camera-angle structure (complexity
   theory / empirical phenomena / substrate alternatives), wall-of-attention case studies, the
   four-layer Linus-implication argument (intra-step latent / scratchpad / episodic / semantic),
   phase-tagged priorities, hype filter, cross-cutting open questions.

6. **Updated the three landscape documents** — added a Memory & universal computation grouping
   to `paper-landscape.md`, a new "Memory as the load-bearing pillar" section in
   `synthesis-landscape.md`, a new Crossing 5 in `total-landscape.md` plus a memory pillar row
   in the cross-table.

7. **Folded all per-paper open questions** into `docs/questions/open-questions.md` under a new
   "Memory pillar — Garrison thread" section in Part 2, plus a "Memory Synthesis" section in
   Part 3 with six cross-cutting items synthesised across the eleven notes.

8. **Promoted 17 prioritised questions** to a new Memory Pillar block at the top of
   `docs/questions/top-questions.md`: M1–M5 Tier 1 (block Phase 2 architecture), M6–M12 Tier 2
   (shape Phase 2–6 architecture), M13–M17 Tier 3 (documentation, conventions, longer-horizon
   scope). All flagged unresolved at this point in the session.

9. **Per-question resolution pass (Option A — interactive Tier 1; Option B — proposed-batch
   Tier 2 and Tier 3).** Walked M1, M2, M3, M4, M5 individually with Dan, then M6–M12 as a
   single proposed batch, then M13–M17 as a final proposed batch. All 17 confirmed.

10. **Side-quest mid-pass (Mughal article).** Dan flagged a practitioner article on
    long-session context degradation (Ayesha Mughal, March 2026) as a valuable operational
    companion to the Garrison architectural argument and asked for it to be woven into the
    memory synthesis, the synthesis landscape, and the total landscape (paper landscape
    deliberately untouched since it's not a paper). I duplicated the article as a synthesised
    note before noticing Dan had already saved the raw article to `context/notes/`; deleted my
    duplicate, then ran three parallel sub-agents to weave the article through the three
    target documents. Also amended the M5 resolution to capture Dan's framing that the 16K
    in-context cap is a floor we move with confidence as Linus matures, not a permanent
    ceiling.

11. **Roll-up (16 ADRs + 1 architecture spec + landscape resolutions + planning-spec
    extension).** Wrote DEC-0028 through DEC-0043 as per-file ADRs in `docs/adr/` (the
    convention graduated from the legacy single-file `DECISIONS.md` at this session — DEC-0027
    was the last entry there); updated the ADR README index. Drafted
    `docs/specs/memory-architecture.md` as the Phase 2 implementation contract. Updated
    `top-questions.md` with the Memory Pillar Resolution Log including 2–3 sentence rationale
    paragraphs under each Tier 1 item. Marked RESOLVED status in all three landscape documents
    pointing to the ADRs and the architecture spec. Appended Section 10 "Memory Pillar
    additions" to `planning-update-spec.md` covering the Phase-by-phase change list and
    file-by-file edit plan for downstream Worker sessions to execute.

---

## Pre-fan-out triage

Dan supplied the 11 paper filenames directly rather than asking me to derive them from
Garrison's bibliography (which had reference numbering that didn't all map cleanly to
`context/papers/` filenames). The 11 papers, framed by the substrate role each plays in the
synthesis:

| Substrate role | Paper | Filename |
| --- | --- | --- |
| Empirical anchor (gap-is-real) | Kojima et al. — _Large Language Models are Zero-Shot Reasoners_ | `2205.11916v4.pdf` |
| Substrate alternative (latent recurrence) | Hao et al. — _Coconut_ | `2412.06769v3.pdf` |
| Substrate alternative (minimal recurrence) | Feng et al. — _Were RNNs all we needed?_ | `2410.01201v3.pdf` |
| Wall-of-attention case study | Bertasius et al. — _Is Space-Time Attention All You Need..._ (TimeSformer) | `2102.05095v4.pdf` |
| Brute-force-compute case study | Chollet et al. — _ARC Prize 2024 Technical Report_ | `2412.04604v2.pdf` |
| Substrate alternative (test-time training) | Akyürek et al. — _Surprising Effectiveness of TTT_ | `2411.07279v2.pdf` |
| Wall-of-attention case study | Meta — _Llama 3 Herd of Models_ | `2407.21783v3.pdf` |
| Empirical anchor (capability + failure modes) | Bubeck et al. — _Sparks of AGI_ | `2303.12712v5.pdf` |
| Wall-of-attention case study (data axis) | Hoffmann et al. — _Chinchilla_ | `2203.15556v1.pdf` |
| Formal complexity (constructive escape) | Feng, Zhang et al. — _Towards Revealing the Mystery behind CoT_ | `2305.15408v5.pdf` |
| Formal complexity (TC0 ceiling) | Merrill & Sabharwal — _Expressive Power of Transformers with CoT_ | `2310.07923v5.pdf` |

**Decisions recorded before fan-out:**

1. **Paper-note format** — match the existing `docs/paper-notes/` shape exactly. Each Worker
   was given three reference notes
   ([`2502.16721v1.md`](../paper-notes/2502.16721v1.md),
   [`2208.07262v1.md`](../paper-notes/2208.07262v1.md),
   [`2402.17764v1.md`](../paper-notes/2402.17764v1.md))
   to lock voice, length, and section structure.
2. **Memory framing primary; standard Linus-applicability sections still included.** The
   instruction to each Worker was that the Garrison memory lens is the primary read, with
   training/retrieval/inference framings as secondary if the paper supports them.
3. **At least 3 open questions for Dan per paper, framed against the memory pillar where
   natural.**
4. **Read full PDF, not abstract.** Same rationale as the prior fan-out: the synthesis pass
   downstream needs the precision.
5. **The Garrison nucleus note stays the synthesis anchor.** Each paper-note Worker was given
   the path to `garrison_memory_makes_computation_universal.md` to ground the framing.

---

## Paper-note fan-out — 11 parallel Workers

All 11 Workers fired in parallel. All returned successfully on first try. Token usage per
Worker was in the same range as the prior session's Wave 1 fan-out (~50K each); total Worker
tokens for the batch on the order of ~600K. Wall time was a few minutes.

| File | Substrate role | Notes |
| --- | --- | --- |
| `2205.11916v4.md` | Kojima — empirical CoT trigger | The "let's think step by step" anchor. Documents emergence-at-scale, task-class-conditional behavior, trigger-sensitivity. |
| `2412.06769v3.md` | Coconut — latent recurrence | Continuous-thought superposition. Cleanest published instance of "carry between steps is a real-valued vector." |
| `2410.01201v3.md` | minLSTM/minGRU | Minimal-state recurrence parallelizable via prefix-sum. The most direct architectural pointer in the corpus to Garrison's path-forward section. |
| `2102.05095v4.md` | TimeSformer | Quadratic wall in a non-text domain. Attention factorisation = constant-factor escape, not structural fix. |
| `2412.04604v2.md` | ARC Prize 2024 | The 2024 step change driven by TTT + program synthesis, not scale. o3 at $1.15M for 91.5% as the cost-of-no-memory benchmark. |
| `2411.07279v2.md` | TTT | Per-task LoRA on synthetic leave-one-out demonstrations. Candidate substrate for episodic-memory consolidation. |
| `2407.21783v3.md` | Llama 3 | The high-water mark of "buy memory by extending context to 128K." 8B variant is a credible Linus Worker candidate. |
| `2303.12712v5.md` | Sparks | Existence proof for transferred cognitive patterns (Sections 1–7) and for the architectural memory deficit (Section 8). |
| `2203.15556v1.md` | Chinchilla | Compute-optimal scaling inside the bounded regime. The architectural ceiling is not where Chinchilla looks for it. |
| `2305.15408v5.md` | Feng et al. CoT theory | Constructive proof: constant-size autoregressive transformer with CoT solves arithmetic / linear systems / DP. |
| `2310.07923v5.md` | Merrill & Sabharwal | Characterises scratchpad-step count → complexity-class regime (log → L; linear → above TC0; polynomial → exactly P). |

**Standout per-paper findings worth flagging up to Dan:**

- **Coconut (`2412.06769`)** introduced the explicit notion of _intra-step latent state_ as a
  fourth memory layer worth naming in the architecture, separate from the existing scratchpad
  / episodic / semantic-knowledge taxonomy.
- **minGRU (`2410.01201`)** is a direct candidate for a Phase 6+ session-memory encoder
  substrate — small parameter count, parallel-trainable, constant-time per token at inference.
  The minGRU + BitNet cross-product surfaces here as a Phase 8 long-horizon target.
- **TimeSformer (`2102.05095`)** is video, not text, but its joint vs. divided attention
  ablation literally OOMs on A100 at 32-frame / 448-px clips — a clean concrete demonstration
  of Garrison's quadratic wall in a non-text domain. Useful as a reference for any future
  Linus discussion about factorisation tricks vs. structural fixes.
- **ARC Prize 2024 (`2412.04604`)** is most useful as a memory-architecture diagnostic
  (vary memory while holding the model fixed, measure delta), not a Linus capability target.
  o3 at $1.15M for 91.5% landed as the upper-bound reference for the "memory budget" framing
  that became M12 / DEC-0028.
- **TTT (`2411.07279`)** opened up the substrate question that became M2 / DEC-0029 —
  conservative SQLite + git for v0 vs. parametric LoRA consolidation as a Phase 6 candidate
  vs. hybrid graduation as a Phase 8 architectural option.
- **Sparks Section 8** is the symmetric existence proof for the Garrison framework: the same
  transformer that produces the unicorn-in-TikZ also fails on multi-digit arithmetic and
  Tower of Hanoi, and recovers when external scratchpad space is provided.
- **Chinchilla** is bounding reference, not actionable. It is the right answer to "how should
  I spend a fixed pretraining budget"; it is not an answer to "how do I escape the
  architectural ceiling."
- **Feng et al. + Merrill & Sabharwal** are the formal pair that made the M3 (scratchpad as
  durable artifact) and M9 (KV-cache continuity) resolutions feel like floor commitments
  rather than preferences. The complexity-class regime mapping (log / linear / polynomial)
  became the basis for the M4 `cot_budget` primitive.

---

## Memory synthesis — single-document write

After all 11 paper-notes were complete, wrote
[`docs/syntheses/memory-synthesis.md`](../syntheses/memory-synthesis.md) inline (single
Maestro Write, not delegated). Structure:

- _What this document is._
- _The unifying thesis._ The two-line Garrison argument as the spine.
- _The three camera angles._ Complexity theory (Merrill & Sabharwal, Feng et al.); empirical
  phenomena (Kojima, Sparks); substrate alternatives (Coconut, minGRU, TTT).
- _The wall, in case the formal argument was not enough._ TimeSformer, Llama 3, Chinchilla,
  ARC Prize 2024 as cost-of-no-memory case studies.
- _What this means for Linus, in concrete architectural terms._ The four-layer decomposition
  (intra-step latent / scratchpad / episodic / semantic-knowledge) mapped onto Garrison's two
  requirements + four sub-requirements. This is the section that became the spine of the
  Phase 2 memory-architecture spec.
- _How memory rewrites the rest of the Linus plan._ Router gets two new axes; Worker
  selection gains a memory-aware dimension; inference backend selection gains a recurrence
  preference; phase resequencing; the o1 anti-pattern as a stated failure mode.
- _What stays out of scope (hype filter)._ Frontier-scale training; local-Workers-rivalling-
  hosted-Claude; substrate commitment beyond v0; transformers-are-wrong; ARC-AGI as a Linus
  target; 128K-as-substitute-for-memory.
- _Phase-tagged priorities._
- _Cross-cutting open questions._ Six items synthesised across the eleven paper-notes.
- _Inputs._ Garrison nucleus + 11 paper-notes + cross-references.

---

## Landscape and questions roll-up

After the synthesis landed, three landscape edits and two questions edits — all single-
Maestro Edit/Write calls, no Workers:

- **`docs/landscapes/paper-landscape.md`** — new "Memory & universal computation (the new
  pillar)" section grouping the 11 papers in three sub-threads (formal theory; empirical
  phenomena; substrate alternatives) plus wall-of-attention case studies and frontier
  empirics. Plus a memory-pillar reading order added to the existing reading-orders-by-Linus-
  phase section.
- **`docs/landscapes/synthesis-landscape.md`** — updated the unifying-thesis section from
  three syntheses to four; added a new "Memory as the load-bearing pillar" section walking
  the formal-result, the load-bearing-layer-current-planning-lacked, and the
  reframes-other-syntheses-questions arguments; memory items added to immediate / Phase 2 /
  Phase 3 priority lists; memory row added to the quick-reference table at the bottom.
- **`docs/landscapes/total-landscape.md`** — new memory row in the cross-cutting
  alignment table; sixth observation; new Crossing 5 ("Memory as the load-bearing pillar");
  new Layer D in the "three layers Linus has to build" section (now four); new gap entry for
  the missing episodic-memory implementation; memory synthesis added to the work-products
  list at the bottom.
- **`docs/questions/open-questions.md`** — new "Memory pillar — Garrison thread" section in
  Part 2 carrying all per-paper questions for the 11 new notes, organised by paper; new
  "Memory Synthesis" section in Part 3 with six cross-cutting items.
- **`docs/questions/top-questions.md`** — new prepended Memory Pillar block with 17
  prioritised items (M1–M17) flagged unresolved at this point in the session.

---

## Side quest mid-session — Mughal article

Dan flagged Ayesha Mughal's March 2026 article on long-session context degradation as a
valuable operational companion to the Garrison architectural argument. Concretely, Mughal
documents (a) the lost-in-the-middle attention degradation pattern in long sessions of hosted
Claude, (b) the real-vs-nominal token budget (degradation begins around ~147K of the nominal
200K window once system prompts, tool schemas, and MCP servers are loaded), and (c) the
session-handoff + targeted-compact + pre-compact-hook + 30-minute-sprint operational pattern
that retains ~80–85% of fresh-session quality across long sessions vs. ~40–60% in
unmanaged marathon sessions.

Process notes from this side quest:

- **I duplicated the article unnecessarily.** Started by saving a synthesised note as
  `mughal_context_window_management.md` in `context/notes/` before noticing Dan had already
  saved the raw article as `Why-Claude-Gets-Dumber-the-Longer-Your-Session-Run.txt` in the
  same folder. Deleted my duplicate immediately when Dan flagged it, then proceeded with the
  three sub-agent integrations against the raw article only.
- **Three parallel sub-agents handled the integration into `memory-synthesis.md`,
  `synthesis-landscape.md`, and `total-landscape.md`.** Per Dan's instruction the paper
  landscape was deliberately untouched (the article is not a paper). All three agents
  returned successfully with wove-it-in-not-bolted-on diffs.
- **The M5 in-context cap resolution was amended** to capture Dan's framing that the 16K cap
  is a floor we move with confidence as Linus matures and as Worker context windows themselves
  grow, not a permanent ceiling. The episodic store, overflow contract, and explicit-bypass
  mechanism stay regardless because attention degrades inside the window even when the window
  is large (Mughal's lost-in-the-middle finding) and because the formal-complexity argument
  for separate state-bearing infrastructure (Garrison's Theorem 1) is substrate-independent.

The Mughal article ended up as the practitioner-side anchor for the Garrison-thread
architectural argument — Garrison says memory architecture is the load-bearing primitive
(theory + complexity); Mughal says context management is the operational pattern that
exposes the substrate (practice). Both got woven into the synthesis as one finding seen from
two angles.

---

## Resolution pass — M1 through M17

The session walked the 17 prioritised items in three sub-passes:

- **Tier 1 (M1–M5) — interactive (Option A).** One question at a time. Maestro proposed a
  resolution with rationale; Dan confirmed or steered. All five confirmed without revision
  except the M5 amendment described above.
- **Tier 2 (M6–M12) — proposed batch (Option B).** All seven resolutions proposed in a single
  message. Dan confirmed the whole batch.
- **Tier 3 (M13–M17) — proposed batch (Option B).** All five resolutions proposed in a single
  message. Dan confirmed the whole batch.

The 17 resolutions, summarised one-line each (full text in
[Memory Pillar Resolution Log in top-questions.md](../questions/top-questions.md), full
context in the per-question ADRs):

| Item | Resolution | ADR |
| --- | --- | --- |
| M1 | Memory architecture lifted from Phase 3+ to Phase 2 first-class architectural pillar; new spec drafted as part of this roll-up | DEC-0028 (also absorbs M12) |
| M2 | Phase 2 v0 episodic substrate is SQLite + content hashes + git as persistence; TTT spike conditional on M10; hybrid as Phase 8 architectural option | DEC-0029 |
| M3 | Scratchpad as first-class durable artifact (`scratchpad`/`answer`/`tool_output` two-segment record per turn); o1 anti-pattern forbidden; `scratchpad_durability` capability tag | DEC-0030 |
| M4 | Two new router primitives: `cot_budget` (`logarithmic` / `linear` / `polynomial`) and `memory_mode` (`stateless` / `session_stateful` / `project_stateful`) | DEC-0031 |
| M5 | 16K Phase 2 default in-context cap with episodic-store overflow; 16K is a floor we move with confidence, not a permanent ceiling | DEC-0032 |
| M6 | Per-Worker CoT-gap fingerprint as a measured registry property (50-item MultiArith-style smoke test in Phase 1c) | DEC-0033 |
| M7 | Phase 1c empirical comparison of `(worker_size, cot_budget)` configurations on sequential-task subset of `dan_tasks/` | DEC-0034 |
| M8 | ARC-AGI as a memory diagnostic (50–100 public-eval tasks, stateless vs. session_stateful), not a Linus capability target | DEC-0035 |
| M9 | KV-cache continuity is a hard requirement for `session_stateful`/`project_stateful` Worker backends | DEC-0036 |
| M10 | Phase 1c TTT viability spike with explicit decision rule (per-task cost <5 min wall-clock graduates TTT to Phase 6 candidate) | DEC-0037 |
| M11 | Phase 1f minGRU MLX port spike with explicit decision rule (within 2× T4 + matched perplexity graduates to Phase 6 candidate) | DEC-0038 |
| M12 | Memory budget as a first-class architectural quantity in ARCHITECTURE.md (folded into DEC-0028) | (DEC-0028) |
| M13 | Hybrid episodic memory schema for multi-step Worker tasks: full M3 record at the leaf, deterministic structural summary at the parent, both addressable | DEC-0039 |
| M14 | Faithfulness audit deferred to Phase 3 with explicit trigger condition (measurable failure mode) | DEC-0040 |
| M15 | minGRU + BitNet cross-product as Phase 8 long-horizon research direction (gated on M11 + M10) | DEC-0041 |
| M16 | Coconut as Phase 6 candidate substrate experiment, conditional on Phase 1 MLX-portability check vs. iCoT alternative | DEC-0042 |
| M17 | Two memory-related fine-tuning targets added to Phase 6a (trigger-invariant step-by-step + episodic-store-friendly output structure) | DEC-0043 |

---

## Roll-up artefacts produced

After all 17 resolutions confirmed, the roll-up phase produced (in order):

1. **16 per-file ADRs** at `docs/adr/0028-memory-architecture-phase2-pillar.md` through
   `docs/adr/0043-memory-mode-finetuning-targets-phase6.md`. Each follows the standard
   Context / Decision / Consequence shape from the existing ADRs in the directory. The legacy
   single-file `DECISIONS.md` at the repo root is now closed at DEC-0027 — these are the
   first per-file ADRs under the graduated convention.
2. **`docs/adr/README.md` index updated** with the 16 new entries, each one-line entry naming
   the M-series item it ratifies.
3. **`docs/specs/memory-architecture.md`** drafted as the Phase 2 implementation contract.
   Walks through the four layers, sub-requirement-to-mechanism mapping, router-side and
   Worker-side contracts, audit-log contract, the nine Phase 2 implementation deliverables in
   execution order, what stays open and why, and forward pointer to ARCHITECTURE.md's
   "Memory Budget Accounting" section.
4. **`docs/questions/top-questions.md` Memory Pillar Resolution Log** added with one-line
   resolutions plus 2–3 sentence rationale paragraphs under each Tier 1 item (M1–M5). Tier 2
   and Tier 3 stayed one-line per the agreed format.
5. **Three landscape documents marked RESOLVED** with pointers back to the ADRs and the
   architecture spec. Crossing 5 in `total-landscape.md`, the Memory section in
   `synthesis-landscape.md`, the new memory-pillar section in `paper-landscape.md` all carry
   RESOLVED notes; the underlying paper-notes and synthesis remain as standing reference.
6. **`docs/specs/planning-update-spec.md` Section 10 — Memory Pillar additions** appended,
   covering Phase 1c spikes (CoT-gap fingerprint, worker-size-vs-CoT-length, TTT viability),
   Phase 1f minGRU spike, Phase 2 first-class deliverables (memory pillar v0 implementation,
   ARC-AGI memory diagnostic, Worker protocol non-conformance constraints), Phase 3
   extensions (faithfulness audit trigger, auto-classifier for `cot_budget`/`memory_mode`,
   parallel-write coordination of episodic-store writes), Phase 6 extensions (memory-mode-
   aware fine-tuning targets, TTT-as-episodic-consolidation spike, Coconut substrate
   experiment), Phase 8 additions (minGRU + BitNet cross-product, hybrid Layer C graduation,
   Layer A active management). Plus file-by-file edit plan extending the existing CLAUDE.md /
   ARCHITECTURE.md / ROADMAP.md edits with memory-pillar additions, the new
   `docs/protocols/maestro-worker-protocol.md` Worker-protocol-non-conformance file, and the
   `~/.linus/` runtime directory layout. Plus a Worker invocation guide for executing the
   additions, an ADR checklist, and five new open questions surfaced during this session.

---

## Cumulative session totals

| Metric | Value |
| --- | --- |
| Garrison-thread paper-notes produced | 11 |
| Synthesised research notes produced | 1 (`memory-synthesis.md`) |
| Landscape documents updated | 3 (paper, synthesis, total) |
| Question documents updated | 2 (open-questions, top-questions) |
| ADRs produced (per-file) | 16 (DEC-0028 through DEC-0043) |
| Architecture specs produced | 1 (`memory-architecture.md`) |
| Planning-spec sections appended | 1 (Section 10 — Memory Pillar additions) |
| Side-quest articles integrated | 1 (Mughal `Why Claude Gets Dumber...`) |
| Sub-agent fan-outs fired | 2 (11-paper paper-note batch + 3-doc Mughal integration) |
| Resolution-pass questions resolved | 17 (M1–M17), all confirmed |

---

## Outstanding questions for next session

These are the items surfaced during the run that need Dan's direction or further investigation
before the next Phase-2-impacting planning session can proceed cleanly. Five items, all queued
in Section 10.5 of `planning-update-spec.md`:

1. **Per-domain CoT-gap variance.** The DEC-0033 fingerprint runs MultiArith-style problems.
   Does Dan's task distribution (genomics, bioinformatics, scientific Python) produce a
   meaningfully different CoT-gap profile per Worker? A small Phase 1c+ extension to the
   fingerprint with domain-specific probes would tell us.
2. **In-context cap empirical revision schedule.** DEC-0032 sets 16K as a floor that moves
   with confidence as measurements accumulate. What is the trigger condition for moving the
   cap up — periodic review (quarterly?), a measured fraction of Worker calls hitting the
   cap, or a Worker-class transition (when fine-tuned BitNet 3B lands)?
3. **Episodic-store retention pruning policy.** DEC-0030 keeps everything in v0; "retain
   unless explicitly archived" is the default. What is the actual long-tail behavior — when
   does the database start being unwieldy, and what does the first pruning policy look like?
4. **Hybrid summary function quality.** DEC-0039's deterministic structural summary is a v0
   choice; a learned summarizer is Phase 6+. What is the trigger condition for moving from
   deterministic to learned?
5. **Per-domain memory-mode defaults.** DEC-0031's v0 heuristic is session-continuity-based.
   Are there domain-specific defaults worth encoding (e.g., genomics literature review →
   `project_stateful` by default; quick Q&A → `stateless`)?

---

## Suggested next steps

The natural follow-on work, in approximate order of leverage:

1. **Worker sessions executing Section 10 of `planning-update-spec.md`** — propagate the
   memory-pillar additions into CLAUDE.md (the new "Memory pillar discipline" Engineering
   Convention), ARCHITECTURE.md (the new "Memory pillar" section + "Memory Budget Accounting"
   sub-section), ROADMAP.md (Phase 1c / 1f / 2 / 3 / 6 / 8 additions), and the new
   `docs/protocols/maestro-worker-protocol.md` Worker-protocol-non-conformance file. Largely
   single-Worker per file, mechanical, low risk.
2. **Phase 1c spike kickoff** — three new spike deliverables land on the Phase 1c critical
   path: per-Worker CoT-gap fingerprint (DEC-0033), worker-size-vs-CoT-length comparison
   (DEC-0034), TTT Apple-Silicon viability spike (DEC-0037). All three sequenced after the
   existing BitNet 2B4T spike (DEC-0013) so Worker registry and benchmark-methodology
   plumbing exists when they fire.
3. **Phase 1f minGRU MLX port spike** (DEC-0038) — parallelizable with the Phase 1c spikes,
   small enough to be a single Worker-spec deliverable.
4. **Phase 2 memory pillar v0 implementation** — the seven Phase 2a deliverables in the
   memory-architecture spec (SQLite schema, audit log, `linus.memory.episodic.*` and
   `linus.memory.scratchpad.*` tool families, dispatch-layer prefix loader, router primitive
   plumbing, Worker registry CoT-gap-fingerprint integration). Sequenced before the Phase 2a
   orchestration backend implementation per DEC-0028.
5. **ARC-AGI memory diagnostic** (DEC-0035) — Phase 2/3 deliverable; runs against the v0
   episodic store once it exists. The cleanest way to turn the memory thesis into a number.
