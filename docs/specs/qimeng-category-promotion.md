# QiMeng Category Promotion + LLM-Hardware-Design Synthesis Seed

**Date:** 2026-05-08 (seeded), 2026-05-09 (additional material landed). **Status:** active; ten new
QiMeng-family papers and three repos have landed. Next gate: paper-note + repo-note authoring (Worker fan-out),
followed by the cluster + thematic syntheses.
**Owner:** Maestro (Dan + Claude Code).

**Related:** [`docs/specs/notes-consistency-fanout.md`](notes-consistency-fanout.md) (the fan-out that surfaced the
mis-binning of `2511.20099v4` and `2511.20100v1` and prompted this promotion).
[`CLAUDE.md`](../../CLAUDE.md) §Doc-type conventions.

---

## Why this exists

The QiMeng family of papers/repos describes _LLMs that design real hardware_ — kernels, processor variants, accelerator
microarchitectures — with the planner/coder discipline made explicit. It is the closest the Linus corpus comes to a
self-improving substrate: LLMs that could, in principle, design the hardware Linus runs on. Three QiMeng items are
already in the corpus:

- [`docs/paper-notes/2511.20099v4.md`](../paper-notes/2511.20099v4.md) — QiMeng-CRUX (Verilog code-gen).
- [`docs/paper-notes/2511.20100v1.md`](../paper-notes/2511.20100v1.md) — QiMeng-Kernel (GPU kernel macro/micro).
- [`docs/repo-notes/QiMeng-cpu-v1.md`](../repo-notes/QiMeng-cpu-v1.md) — Behavioral synthesis of a RISC-V CPU.

Two adjacent papers also belong to the LLM-hardware-design lens: [`0549.md`](../paper-notes/0549.md) (Cheng et al.'s
superscalar processor design via LLMs) and [`2306.12456v2.md`](../paper-notes/2306.12456v2.md) (CPU design via AI).

In the notes-consistency fan-out the QiMeng papers were classified into B9 (Finance/quant) by alphabetical-ID adjacency
to QuantAgent / TradingAgents — clearly mis-binned. The B1 (Apple Silicon) cluster also absorbed QiMeng-cpu-v1 as a
methodological footnote, which inflated the cluster's headcount to 9 and introduced a thematic discontinuity. Dan plans
to add ~4 more repos and ~8 more papers to the QiMeng / LLM-hardware-design thread; that volume warrants its own
category rather than continued footnoting in tangential clusters.

## Dan's stated framing (verbatim, this session)

> [QiMeng] also relate[s] more to Sketch2Simulation than anything else. That paper and repo is also focused on using
> LLMs to design real physical things. That's the idea I love and want to capture. The ability for Linus to design
> physical things in a practical, highly useful way. I'd love to be able to have Linus produce schematics and designs
> for me, which could be accepted by a manufacturer or engineer or builder or some such, resulting in a real physical
> thing being built. Idea to reality. That's the dream. Having these skills informed by the corpus of knowledge I've
> accumulated should amplify my ability to design and build tangible things, with help from Linus.

The thematic spine is **idea → reality**: LLMs producing artifacts (kernels, hardware, process flowsheets, schematics,
build instructions) that a downstream non-LLM actor (compiler, fab, manufacturer, contractor, builder) can accept and
realize as a physical or computational artifact. QiMeng is the hardware exemplar; Sketch2Simulation is the
process-engineering exemplar; the generative-biology corpus is arguably the biology exemplar. The new category should
foreground this design-and-build lens rather than the narrower hardware-design framing.

## What's been done so far (this session)

- **Removed QiMeng prose from existing syntheses.** Three syntheses had treated QiMeng as a methodological appendix:
  - [`docs/syntheses/repo-clusters/g1-apple-silicon.md`](../syntheses/repo-clusters/g1-apple-silicon.md) — multiple
    QiMeng-cpu-v1 paragraphs removed; cluster headcount restored from 9 to 8 repos; breadcrumb pointing here added.
  - [`docs/syntheses/infra-foundations-synthesis.md`](../syntheses/infra-foundations-synthesis.md) — "Hardware AI
    research footnote" replaced with breadcrumb pointing here.
  - [`docs/syntheses/native-low-bit-apple-silicon-synthesis.md`](../syntheses/native-low-bit-apple-silicon-synthesis.md)
    — single QiMeng-cpu-v1 paragraph removed.
- **Updated the synthesis landscape index.**
  [`docs/landscapes/synthesis-landscape.md`](../landscapes/synthesis-landscape.md) row for g1 reflects the headcount
  change and points here.
- **Reframed [`2511.20100v1.md`](../paper-notes/2511.20100v1.md)** with the LLM-hardware-design + Apple-Silicon
  transferability + Sketch2Simulation-as-sibling lens (the original note was a thin GPU-only framing).

## What landed 2026-05-09

Dan added ten new QiMeng-family papers and three new QiMeng repos. The papers/repos pair up as follows; the family
identifier comes from the ICT/CAS Yunji Chen / Qi Guo group's authorship overlap.

**Papers (10) — all without paper-notes yet:**

| Paper PDF | Short title | Repo pair | Notes |
| --- | --- | --- | --- |
| `13337-ZhouQ.pdf` | QiMeng-GEMM (AAAI-25) | — | LLM-generated high-perf GEMM code |
| `2407.10424v5.pdf` | CodeV (Verilog gen via multi-level summarization) | `repos/CodeV` | Direct paper↔repo pair |
| `2505.06302v1.pdf` | QiMeng-TensorOp | — | Tensor operators with hardware primitives |
| `2505.24183v5.pdf` | QiMeng-CodeV-R1 (reasoning-enhanced Verilog via RLVR) | (extends `repos/CodeV`) | RLVR follow-up to CodeV |
| `2506.11153v2.pdf` | QiMeng-MuPa (sequential→parallel CUDA) | `repos/QiMeng-MuPa` | Direct paper↔repo pair |
| `2506.12355v1.pdf` | QiMeng-Attention (SOTA FlashAttention via SOTA algorithm) | — | LLM-generated attention kernels |
| `2510.19296v4.pdf` | QiMeng-SALV (signal-aware Verilog gen) | `repos/QiMeng-SALV` | Direct paper↔repo pair |
| `3696443.3708931.pdf` | VEGA (compiler back-end gen via pre-trained transformer) | — | Adjacent — same group, compiler back-ends |
| `9546_AutoOS_Make_Your_OS_More_.pdf` | AutoOS (LLM-driven OS kernel config tuning) | — | OS-level adaptation, same group |
| `osdi25-dong.pdf` | QiMeng-Xpiler (OSDI'25, neural-symbolic transcompilation) | — | Tensor-program transcompiler |

**Repos (3) — all without repo-notes yet:**

- `repos/CodeV` — pairs with `2407.10424v5.pdf`; covers `2505.24183v5.pdf` as the CodeV-R1 RL extension.
- `repos/QiMeng-MuPa` — pairs with `2506.11153v2.pdf`.
- `repos/QiMeng-SALV` — pairs with `2510.19296v4.pdf`.

**Already-in-corpus QiMeng material (refresher):**

- Paper-notes: `0549.md` (superscalar processor design), `2306.12456v2.md` (Push the Limits CPU design),
  `2506.05007v1.md` (QiMeng: Fully Automated HW+SW Design — newly landed paper-note),
  `2511.20099v4.md` (QiMeng-CRUX), `2511.20100v1.md` (QiMeng-Kernel).
- Repo-note: `QiMeng-cpu-v1.md`.
- Cross-thread exemplar (not a QiMeng member but the same idea→reality spine): paper `2603.24629v1.md`
  (Sketch2Simulation) + repo `Sketch2Simulation` (in g8-sci-agents).

After this batch lands, the QiMeng family will comprise **15 paper-notes + 4 repo-notes** worth of material,
with five additional already-existing paper-notes (0549, 2306.12456v2, 2506.05007v1, 2511.20099v4, 2511.20100v1)
that should be re-Connected to the new synthesis when it lands.

## What remains to be done

1. **Author paper-notes for the 10 new papers** (Worker fan-out). Match canonical paper-note structure per CLAUDE.md
   §Doc-type conventions: YAML frontmatter, eight H2 sections (TL;DR through Open questions for Dan), Reusable-in-Linus
   mapped to phases (Phase 1..8) with DEC/spec refs where applicable, Connections via relative links, sequentially
   numbered open questions. Each note's "What's reusable in Linus" section should explicitly map to the **idea → reality**
   spine — what artifact does the LLM produce, what downstream actor accepts it, and what must be true for Linus to
   replicate the discipline locally. CodeV / CodeV-R1 should be authored together since they share a repo.
2. **Author repo-notes for the 3 new repos** (Worker fan-out). Match canonical repo-note structure: H1 = `# <repo>
   (\`<owner/repo>\`)`, seven numbered H2 sections, fixed-vocabulary verdict, sequentially numbered Section-7 questions.
   Each repo-note links its paired paper-note(s).
3. **Update the INDEX files** ([`docs/paper-notes/INDEX.md`](../paper-notes/INDEX.md) and
   [`docs/repo-notes/INDEX.md`](../repo-notes/INDEX.md)). For the new entries, mark them `_Pending llm-hardware-design_`
   in the synthesis column until the new synthesis is authored. Same convention for the 5 already-in-corpus QiMeng
   paper-notes whose current synthesis cell shows `_Uncovered_`.
4. **Author the new repo-cluster synthesis** as `docs/syntheses/repo-clusters/g12-llm-hardware-design.md`. Anchor it
   around the QiMeng family (4 repos), with Sketch2Simulation cited as a cross-thread reference exemplar (not a member
   — its repo is in g8). Document the within-cluster pattern: the planner/coder discipline, the multi-level
   summarization approach (CodeV), the signal-aware verification approach (SALV), the macro-thinking/micro-coding
   paradigm (Kernel), and the RLVR feedback loop (CodeV-R1).
5. **Author the new thematic synthesis** as `docs/syntheses/llm-hardware-design-synthesis.md`. Frame around the
   **idea → reality** spine: QiMeng = hardware/kernels; Sketch2Simulation = process/flowsheets; future Linus skills
   = schematics, designs, build instructions for Dan's tangible-things workflow. The thematic synthesis should
   explicitly anchor on Dan's stated framing (Section "Dan's stated framing" above) and identify which QiMeng
   patterns generalize beyond hardware.
6. **Add the new bin to the next notes-consistency fan-out spec.** When a follow-up sweep runs, add B14 with the
   full QiMeng family as primary content, plus 0549 and 2306.12456v2 as adjacent papers. Re-bin
   `2511.20099v4.md` and `2511.20100v1.md` from B9 (where the previous fan-out mis-binned them) into B14.
7. **Author ADRs as needed.** Candidates: (a) MTMC pipeline (Macro-Thinking Micro-Coding) as a Linus-internal pattern;
   (b) idea→reality as a Phase 7 skill class; (c) CodeV-R1's RLVR loop as a Worker self-improvement substrate; (d) the
   typed-structured-prediction-wrapping-rationale convention from CLAUDE.md applied to hardware design specifications.
8. **Update existing notes' Connections.** Sweep `0549.md`, `2306.12456v2.md`, `2506.05007v1.md`, `2511.20099v4.md`,
   `2511.20100v1.md`, `QiMeng-cpu-v1.md`, plus `2603.24629v1.md` and `Sketch2Simulation.md` to add Connections-section
   pointers to the new syntheses once they exist.

## Out of scope today

- Writing the new synthesis text **before paper-notes and repo-notes for the new batch are authored**. The
  fan-out should land first, then the synthesis can quote the canonical-structure note bodies.
- Re-running the notes-consistency fan-out on B14 alone.
- Creating any new ADRs preemptively. Phase 6/7 ADR seeds can be drafted but committed only after the synthesis
  reveals the durable architectural commitments.

## Status

- 2026-05-08: seed authored. QiMeng prose removed from existing syntheses; landscape index updated;
  `2511.20100v1.md` reframed.
- 2026-05-09: additional material landed (10 papers + 3 repos enumerated above). Active; next gate is paper-note +
  repo-note authoring fan-out.
- _Pending: paper-note authoring (10 notes), repo-note authoring (3 notes), INDEX updates._
- _Pending: cluster synthesis (`g12-llm-hardware-design.md`) + thematic synthesis (`llm-hardware-design-synthesis.md`)._
- _Pending: ADRs (MTMC pattern, idea→reality skill class, RLVR loop)._
- _Pending: notes-consistency fan-out re-run on the new bin (B14)._
