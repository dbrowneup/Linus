# Citation Traceability Audit — LLMs in Science Synthesis

**Audited:** 2026-05-05
**Synthesis:** docs/syntheses/llms-in-science-synthesis.md
**Total substantive claims identified:** 37
**OK:** 32 · **MISSING:** 2 · **WEAK:** 2 · **BROKEN:** 1 · **ORPHAN:** 0

---

## Summary

The synthesis is broadly well-cited, with 86% of substantive claims traced to specific, existing sources. The 2026-05-05
g8-sci-agents section performs adequately on paper-note links but lacks a direct reference to the g8-sci-agents cluster
synthesis itself — claims about paper-qa, bioSkills, and scientific-agent-skills are attributable but require the reader
to infer the source from context. Two quantitative claims in the Knuth section (1 hour, 31 explorations) appear
uncited. One reference (Group F) is a categorical orphan; the dual-use biotech paper is cited by link, but "Group F"
is never defined.

---

## Findings

### MISSING citations

1. **Line 34: "~1 hour and 31 explorations"** — Quantitative claims from the Knuth case. Source is implied to be the
   paper-note `claude-cycles.md`, but the specific numbers are not cited inline or verified against the source. The
   synthesis asserts these numbers as fact without a trace. **Severity: Medium** (the paper-note exists; this is a
   convenience citation issue, not a broken link).

2. **Line 232: "multi-step research loops with citation-grounded intermediate outputs"** — The g8 cluster synthesis
   argues this empirically, but the synthesis states the claim without explicitly pointing to g8-sci-agents.md. The
   reader must infer the source from context ("the g8 cluster argues empirically"). **Severity: Low** (source is
   identifiable in surrounding context, but implicit rather than explicit).

### WEAK citations

1. **Line 11–12: "dual-use biotech paper" categorized as "Group F"** — The paper is cited by link
   (`../paper-notes/2306.03809v1.md`), but "Group F" is never defined or referenced elsewhere in the synthesis. The
   grouping system appears to be assumed knowledge, and no pointer to the grouping taxonomy (likely in the
   paper-landscape or repo-landscape) is provided. **Severity: Medium** (the paper exists and is accessible, but the
   categorical framing is orphaned).

2. **Lines 242–246: g2, g3, g9 secondary edges** — The synthesis references g2-wiki-engines, g3-wiki-patterns, and
   g9-bioinformatics as "secondary edges" supporting specific threads (epistemic-standards, reproducibility-floor,
   domain-instantiation). The claims are sound and the repos exist, but no explicit link to the cluster syntheses is
   provided. The reader must infer that "g9-bioinformatics" refers to
   `docs/syntheses/repo-clusters/g9-bio.md`. **Severity: Low** (the cluster syntheses exist and the claims are
   traceable, but the convention for cluster references is not made explicit in the synthesis itself).

### BROKEN links

1. **Line 243: `obsidian-llm-wiki-local, llm-research-wiki LINT`** — Mentioned as specific projects supporting the
   epistemic-standards thread, but appear uncited. Repo-notes may exist (`obsidian-llm-wiki-local.md` confirmed
   present), but no direct link is provided. **Severity: Low** (the repos exist; this is a formatting/convention issue
   rather than missing source material).

### ORPHAN citations

1. **"Group F" (line 11)** — Categorical reference with no definition or pointer to a grouping taxonomy. The
   dual-use biotech paper is correctly cited by link, but the categorical framing has no home. Likely refers to a
   classification in the paper-landscape.md or a fan-out group that should be named explicitly.

---

## Analysis of g8-sci-agents Section (new 2026-05-05)

The new section (lines 220–246) integrates g8-sci-agents material into the framework. **Citation coverage:** 

- **Direct paper-note links:** None (the section names repos, not cites papers).
- **Repo-note references:** paper-qa, bioSkills, scientific-agent-skills (all exist; no links provided).
- **Cluster synthesis references:** g8-sci-agents mentioned by name (line 222) but **not linked**. g2, g3, g9 mentioned
  (lines 242–245) also **not linked**. This is the primary gap.
- **Quantitative claims:** LAB-Bench canary string (line 240) — attributable to g8-sci-agents.md but not cited. The
  573-skill catalog (line 236–237) — properly traced to "integrate-trio" without a number source, acceptable.

**Assessment:** The section is conceptually sound and internally consistent with the broader synthesis, but it follows
an implicit convention (cluster syntheses are named, not linked; cluster repo-notes are mentioned, not linked) that
creates mild traceability friction. The g8-sci-agents relationship is foundational to the entire section; an explicit
link at line 222 would resolve this.

---

## Remediation recommendations (priority order)

1. **Add explicit link to g8-sci-agents cluster synthesis at line 222.** Change "The 2026-05-05 landscape remapping made
   **g8-sci-agents** the primary cluster anchor for this synthesis" to "...made **[g8-sci-agents](../syntheses/repo-clusters/g8-sci-agents.md)** the primary..." This clarifies the reference and allows readers to drill into the full cluster context.

2. **Inline the Knuth quantitative claims (line 34) with a paper-note citation.** Change "~1 hour and 31 explorations
   later" to "~1 hour and 31 explorations later (per [claude-cycles.md](../paper-notes/claude-cycles.md))" or verify
   the numbers against the source and confirm they are direct quotes. If from the paper-note, add a reference.

3. **Define or link "Group F" at first mention (line 11).** Either: (a) explain the grouping taxonomy inline (e.g.,
   "sits in [Group F](../paper-landscape.md#group-f) of the paper landscape..."), or (b) remove the categorical
   reference and rely solely on the paper-note link. Option (a) is preferable if the landscape uses this taxonomy.

4. **Add explicit links to secondary cluster syntheses (lines 242–245).** Change "g3-wiki-patterns" to
   "[g3-wiki-patterns](../syntheses/repo-clusters/g3-wiki-patterns.md)" and similarly for g2 and g9. Low-friction
   clarification that supports navigation.

5. **Verify the LAB-Bench canary string (line 240) against g8-sci-agents.md.** Confirm it is an exact quote from the
   cluster synthesis (it appears to be), then consider an inline parenthetical reference for precision.

---

## Spot-check: sample of OK citations

- Line 7: Binz et al. paper-note link ✓
- Line 8: Knuth Claude's Cycles paper-note link ✓
- Line 85: ADR 0028–0043 range (memory-pillar ADRs) ✓ (references are in text, verifiable in `/docs/adr/`)
- Line 250: memory-synthesis.md link ✓
- Line 254: security-synthesis.md link ✓
- Line 255: skills-and-practices-synthesis.md link ✓
- Line 258: synthesis-landscape.md link ✓

All cited files exist and are accessible via the relative paths provided.

---

## Notes

- The synthesis uses implicit conventions for cluster-synthesis and repo-note references that work within the Linus
  knowledge base but would benefit from explicit linking for robustness. This is not a traceability failure, but a
  convention clarification opportunity.
- No false citations detected (claims are not attributed to wrong sources).
- The paper-notes cited are all present and correctly referenced by relative path.
- ADR references (DEC-0028–DEC-0043) are text-only, not links; they are verifiable and correct.
