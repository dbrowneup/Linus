# QiMeng Category Promotion + LLM-Hardware-Design Synthesis Seed

**Date:** 2026-05-08 **Status:** seed; execution deferred until additional QiMeng material lands.
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

## What remains to be done (deferred until Dan's additional material lands)

1. **Stage Dan's additional QiMeng repos and papers.** ~4 repos + ~8 papers planned. As they land, place them in
   `docs/repo-notes/` and `docs/paper-notes/` with full canonical structure per CLAUDE.md §Doc-type conventions, and
   update [`docs/paper-notes/INDEX.md`](../paper-notes/INDEX.md) and
   [`docs/repo-notes/INDEX.md`](../repo-notes/INDEX.md) to assign them to the new category.
2. **Author the new repo-cluster synthesis** as `docs/syntheses/repo-clusters/g12-llm-hardware-design.md` (or
   numbered as appropriate when it lands). Anchor the cluster around the QiMeng family. Treat Sketch2Simulation as
   a cross-thread reference exemplar from the agentic-systems / process-engineering side of the same dream rather
   than as a cluster member, since its repo is in g8 (sci-agents) and its paper is in B4.
3. **Author the new thematic synthesis** as `docs/syntheses/llm-hardware-design-synthesis.md`. Frame it around
   the **idea → reality** spine (per Dan's stated intent above): LLMs producing artifacts that downstream actors
   accept and realize. QiMeng = hardware/kernels; Sketch2Simulation = process/flowsheets; future Linus skills =
   schematics, designs, build instructions for Dan's tangible-things workflow. Cite as cross-thread exemplars where
   appropriate without re-binning them.
4. **Add the new bin to the next notes-consistency fan-out spec.** When a follow-up sweep runs, add B14 with the
   QiMeng family as its primary content, plus 0549 and 2306.12456v2 as adjacent papers. Re-bin
   `2511.20099v4.md` and `2511.20100v1.md` from B9 (where the previous fan-out mis-binned them) into B14.
5. **Author ADRs as needed.** When the new synthesis converges on architectural commitments (e.g., MTMC pipeline as a
   Linus-internal pattern, idea→reality as a Phase 7 skill class), capture them under `docs/adr/` with new DEC-NNNN
   slots.
6. **Update existing notes' Connections.** Once the new syntheses exist, sweep the QiMeng papers + repo +
   Sketch2Simulation paper + repo to add Connections-section pointers to the new syntheses. Currently those notes
   reference each other and the old infra-foundations footnote; refresh the link targets.

## Out of scope today

- Writing the new synthesis text. Dan's additional ~12 items must land first or the synthesis will need substantial
  rewriting.
- Re-running the notes-consistency fan-out on B14 alone.
- Creating any new ADRs preemptively.

## Status

- 2026-05-08: seed authored. QiMeng prose removed from existing syntheses; landscape index updated;
  `2511.20100v1.md` reframed.
- _Pending: Dan's additional QiMeng repos and papers land._
- _Pending: synthesis authoring + ADRs + notes-consistency fan-out re-run on the new bin._
