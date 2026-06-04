# v0.6.0 native-RAG evaluation questions (Dan's domain)

**Status:** drafted by Maestro 2026-06-02; **pending Dan's final approval/edits.** Captured durably here so they
survive session compaction — they were drafted in chat during the v0.5.0 session and were nearly lost.

**Purpose:** the question set for the **v0.6.0 RAG-vs-no-RAG ablation** — the Phase-2→3 "RAG beats the bare-Worker
baseline" gate that backs the North-Star claim (local models can be private _and_ powerful). See
[DEC-0062](../../docs/adr/0062-native-rag-supersedes-paperqa-corpus-engine.md) and R5-09 in
[`docs/questions/top-questions.md`](../../docs/questions/top-questions.md).

## The questions

Literature-synthesis questions squarely in Dan's wheelhouse — _Botryococcus braunii_ biochemistry, microalgal lipid
metabolism, long-read genome assembly, and metagenomic binning — domains where grounding in the corpus should
measurably beat a bare local model.

1. What hydrocarbons does _Botryococcus braunii_ produce, and how do they differ across the A/B/L races?
2. Which gene families are implicated in squalene and botryococcene biosynthesis in _B. braunii_?
3. How does nitrogen limitation affect lipid/hydrocarbon productivity in green microalgae?
4. What are the main computational challenges in assembling long-read (PacBio HiFi) genomes?
5. What methods are used to bin and taxonomically classify contigs in metagenomic assemblies?

## Grounding coverage (confirmed 2026-06-02 via library search — checked, not assumed)

Dan's existing corpus covers all five:

- **Q1 / Q2** — Okada (squalene synthase), Thapa (race-L SSL enzyme), and the _B. braunii_ genome / terpene-metabolism
  thread.
- **Q3** — green-microalgae nitrogen-limitation / lipid-productivity literature.
- **Q4** — Lang (PacBio HiFi vs. Nanopore assembly).
- **Q5** — Mallawaarachchi (metagenomic contig binning).

## Paper sourcing — READ IN PLACE, NEVER DUPLICATED

Source PDFs live in **Dan's existing library** (`~/Documents/Papers Library/`, ~19,262 PDFs) and the tracked
`context/papers/` set. The RAG engine **reads them in place and persists only derived artifacts** — text chunks,
embeddings, and provenance (`{paper_id, page, char-span, score}`) — in its index. **It does not copy, move, or
duplicate Dan's PDFs anywhere.** Any design that would duplicate the corpus is explicitly out of scope (Dan's standing
requirement, 2026-06-03).

## Ablation conditions

Per the v0.6.0 RAG plan (DEC-0062):

1. **Bare baseline** — qwen3:8b, no retrieval.
2. **Linus-native RAG** — persistent full-text-chunk retrieval + grounded-citation synthesis.
3. **Hosted-Claude reference** — upper-bound anchor.

**Grader:** chosen at build time (R2-03) — exact-match / keyword for factual answers (gene names, race labels,
tool names are right or wrong, not "similar") versus a rubric for the synthesis-style answers.

## Provenance

Drafted in the 2026-06-02 v0.5.0 session (transcript line 564); recovered and persisted 2026-06-03 after Dan flagged
they were at risk of being lost across a compaction. The original A2 RAG measurement was deferred from v0.5.0 to v0.6.0
when paper-qa was demoted ([DEC-0062](../../docs/adr/0062-native-rag-supersedes-paperqa-corpus-engine.md)), so these
questions were never run — they are the ready input for the v0.6.0 ablation.
