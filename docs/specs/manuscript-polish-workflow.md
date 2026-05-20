# Manuscript Polish Workflow — using Linus to finish unfinished drafts

**Status:** proposed, 2026-05-19. Strategic spec; no code change yet.
**Owner:** Dan Browne. Maestro reviews + executes Worker tasks within the workflow.

---

## Motivation

Dan has manuscript drafts from his PhD work — mostly _Botryococcus braunii_ genome assembly and downstream
lipid/terpene metabolism — that have been sitting unpublished for ~9 years. His PI never gave the editorial help
needed to bring them across the finish line. Two structural problems compounded the delay:

1. **Citation curation.** Updating a 2017-era literature review to current state-of-the-field is a multi-week
   effort that requires reading hundreds of papers — exactly the kind of work that bottlenecks scientists.
2. **Self-review.** Any single author overestimates their own draft's clarity. The traditional remedy (a
   committed PI / co-author / colleague) requires someone with both subject-matter depth AND time.

Linus, in v0.5.0+, has the substrate to solve both: KnowledgeBase indexes Dan's 19,247-PDF corpus, paper-qa
synthesizes citation-grounded answers, and rigor.py refuses to ship fabricated citations or hallucinated
entities. The workflow below operationalizes that substrate.

---

## Workflow shape

The workflow is **iterative**, not single-shot. Each iteration improves one focused aspect of the draft;
the human is the keeper of voice and argument; Linus is the citation engine, fact-checker, and
suggestion-generator. **Dan never publishes anything Linus drafted unreviewed** — see §"Discipline rules."

### Phase 0 — Manuscript ingestion (one-shot per draft)

1. Convert the .docx / LaTeX manuscript to plain text (`pandoc -o draft.md`).
2. Drop the .md into `context/manuscripts/<slug>/draft.md` (gitignored — personal content).
3. Run `python -m linus.tools.arxiv_ingest --input context/manuscripts/<slug>/draft.md` adapted to handle a
   local-manuscript ingest (small follow-on tool: `manuscript_ingest.py` — open scope; not yet built).
4. The ingestion tool extracts: the references-cited list, the named entities (genes, proteins, organisms,
   methods), the figure-captions, the abstract, the topic-claim sentences.
5. Output: a structured `manuscript.json` with sections, claims, citations, entities — ready for the
   downstream tools to consume.

### Phase 1 — Citation freshness audit

For each cited reference in `manuscript.json`:

1. **Resolve the citation** — find the paper in KB (by DOI, title, or fuzzy match). If not found, flag as
   "cited but not in KB; consider adding to corpus."
2. **Find the modern descendants** — for each cited paper, run `paperqa.search` with the cited paper's title +
   abstract as query, restricted to papers published since the original citation date. Surface the top 5 hits.
3. **Maestro decision** — for each old citation, decide: (a) keep as-is (historical primacy), (b) supplement
   with a 2020+ citation (state-of-field update), (c) replace (the original was superseded).

Output: a citation-refresh document at `context/manuscripts/<slug>/citation-refresh.md` listing every original
citation, the decision, the new citation(s) if any, the rationale.

### Phase 2 — Claim grounding (the rigor gate's primary job)

For each topic-claim sentence in the manuscript (extracted in Phase 0):

1. Form the claim as a `ClaimDict` (per `src/linus/knowledge/rigor.py` shape) — `{rationale, evidence,
   entities, confidence}`. `evidence` is the citation list supporting that sentence.
2. Run `linus.knowledge.rigor.check_grounding(claim, papers=..., entities=...)`:
   - Citation grounding catches references that don't actually exist in KB (e.g., a citation that was a
     dangling typo in the original draft, or a fake reference inserted by a 7B Worker during regeneration).
   - Entity grounding flags every gene/protein/organism named in the sentence; warns on unrecognized entities.
   - Confidence calibration is N/A in this phase (no Worker re-runs yet) — defer to Phase 4.
3. Maestro reviews each `RigorResult.failures` entry and decides: (a) the claim is fine, (b) the citation
   needs replacing, (c) the entity name is malformed/wrong/needs updating to current nomenclature.

Output: a `claim-audit.md` per section, listing every claim → grounding verdict → action.

### Phase 3 — Section-level rewriting

For each section flagged in Phase 2 as needing rewrite:

1. Dispatch a Worker (local Ollama qwen3:8b, or higher-capacity hosted Claude via Maestro) with:
   - The original section text.
   - The list of citation updates from Phase 1.
   - The list of claim corrections from Phase 2.
   - The instruction: "Rewrite this section preserving Dan's voice, updating citations as specified, fixing
     the flagged claims, and adding no new claims that aren't already supported by the cited references."
2. Worker emits the rewritten section as a structured claim (per S25 BioReason-Pro shape).
3. Re-run rigor.py on the rewrite. If `passed=False`, dispatch one re-roll with the failure list as
   correction prompt. Two strikes = escalate to Maestro for manual handling.
4. Multiple Worker runs of the same section feed into Phase 4.

### Phase 4 — Cross-run confidence calibration

For each rewritten section, the audit log (per DEC-0030/0031) now holds multiple Worker outputs.

1. Run `rigor.check_confidence(claim, prior_runs=audit_log_for_section)` to compute Jaccard divergence
   across the runs.
2. Low divergence (>0.7 Jaccard) — sections where the Workers consistently produced similar rewrites — are
   high-confidence; surface those first.
3. High divergence (<0.5 Jaccard) — sections where Workers disagreed substantively — get flagged for
   Maestro / Dan to review the variants and pick.

This is the v0.5.0 confidence-calibration plumbing put to a real load-bearing use.

### Phase 5 — Dan-only review pass

Once Phases 1-4 have run the manuscript through Linus's machine pass:

1. Dan opens the rewritten draft alongside the original.
2. Dan reads end-to-end, comparing voice (does it still sound like him?) and argument (is the thesis intact?).
3. Dan accepts / rejects / re-instructs section-by-section.
4. Linus does not write the cover letter, the response-to-reviewers, or anything that involves Dan's
   identity or relationship with the editor. Those are human-only.

Output: a manuscript ready for journal submission.

### Phase 6 — Post-submission iteration

When reviewers respond:

1. Re-run citation freshness audit (any new state-of-field papers since submission?).
2. For each reviewer concern, run `paperqa.answer` against the relevant query — does the literature support
   the reviewer's claim or Dan's? Use the cited evidence in the response-to-reviewers, written by Dan.

---

## Discipline rules

These are non-negotiable, per CLAUDE.md §"Evidence beats intuition" and DEC-0059's grounding gate:

1. **Linus drafts nothing Dan publishes unreviewed.** Every section that Linus rewrites passes Dan's eyes
   before submission. No automation of the final pass.
2. **The rigor gate is hard.** A `RigorResult(passed=False)` blocks the section from advancing to Phase 5
   until the failure list is resolved or explicitly overridden by Maestro with a justification in the audit
   log.
3. **No Worker output enters the manuscript without provenance.** Every rewrite carries the `paper_id`,
   `evidence`, and `rationale` fields it was generated with. This is the Marelli attribution discipline
   (see DEC-0059 §References and the Q2 signed-audit-slice seed in DECISIONS.md).
4. **No fake citations, ever.** Citation grounding is `error`-severity; the gate refuses anything ungrounded.
   If a Worker insists on citing a paper that doesn't exist, dispatch a different Worker — don't lower the
   gate.
5. **Author voice is Dan's.** Maestro/Workers can suggest phrasing; Dan can accept or write his own. Voice
   is non-negotiable.

---

## Tooling gaps (work needed to make this fully functional)

The substrate exists. The workflow above is operable today **with manual stitching**. To make it
production-grade for shipping multiple manuscripts efficiently, these would help:

1. **`linus.tools.manuscript_ingest`** — extract sections / claims / entities / citations from a `.docx` or
   plain-text manuscript draft. Sized ~1 small PR. Reuses the arxiv_ingest pattern.
2. **`linus.knowledge.entity_kb`** — KB-derived entity lookup (replaces the v0.5.0 stub
   `BuiltinEntityLookup`). Pulls the entity vertices from KB's REBEL+SciSpacy KG outputs. Sized ~1
   medium PR. See the post-reveal direction discussed 2026-05-19.
3. **`linus.tools.citation_freshness`** — given a citation, find modern descendants via paper-qa over the
   KB corpus restricted by date range. Sized ~1 small PR.
4. **Streamlit page `8_manuscript_polish.py`** — UI to drive the iterative workflow (upload draft → ingest →
   see audit results → run Phase 3 dispatch → review variants → export). Sized ~1 medium PR.

None of these are v0.5.0 scope. They're the v0.6.0+ work that turns this spec into a turnkey workflow.

---

## Success criterion

A manuscript draft that has been sitting unpublished for nine years moves through the workflow above and
arrives at a submission-ready state in a small number of Dan-hours (target: a long weekend, not a month).
The Marelli attribution discipline holds — every claim in the final submission traces back through the
audit log to its supporting evidence in Dan's corpus.

If the workflow succeeds, the next manuscript is faster. If five manuscripts ship, Linus has paid for itself
in scientific output.
