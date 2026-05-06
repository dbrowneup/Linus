# Citation Traceability Audit — Humans, Teams & Performance Synthesis

**Audited:** 2026-05-05
**Synthesis:** docs/syntheses/humans-teams-performance-synthesis.md
**Total substantive claims identified:** 28
**OK:** 26 · **MISSING:** 2 · **WEAK:** 0 · **BROKEN:** 0 · **ORPHAN:** 0

## Summary

This synthesis demonstrates excellent citation discipline overall. The two primary papers (Güllich et al., Science 2025
and Harvey et al., ASQ 2023) are cited directly via valid markdown links to existing paper-note files; the supporting
cognitive-throughput pair (Zheng-Meister and Sauerbrei-Pruszynski) are similarly well-linked. Cross-references to
syntheses and internal Linus artifacts are valid. Two substantive numerical claims (Güllich's effect sizes and the
"nine orders of magnitude" span across timescales) lack inline clarification but are recoverable from the cited papers.
No broken links or orphan references.

## Findings

### MISSING citations

**Claim (line 31): "Pooled effect sizes for multidisciplinary-breadth and gradual-progress (Cohen's d ≈ 0.39–0.58)"**
- Location: "The papers at a glance," Güllich summary
- Status: Substantive quantitative claim; linked paper exists (`science.adt7790.md`) but no inline footnote or pointer to
  the specific section where this figure appears
- Severity: Low (reader can locate in cited paper, but synthesis does not directly signal the source of the number)
- Recommendation: Add a note like "(Güllich et al., Fig. 2)" or cite the exact table/section in the paper-note

**Claim (line 82-83): "The three timescales differ by roughly nine orders of magnitude"**
- Location: "The Maestro/Worker analogy at three timescales" section
- Status: Specific quantitative claim about scale separation; implicitly derived from the three literatures but no explicit
  calculation or reference to a source that provides this estimate
- Severity: Low (order-of-magnitude estimate, not a precise measurement; derivable from cited papers but not explicitly
  grounded)
- Recommendation: Either cite a section in the Güllich or Harvey papers that justifies the magnitude gap, or briefly
  note in parentheses how the estimate was derived (e.g., "milliseconds → weeks → decades")

### WEAK citations

None identified. All provided links are functional and citations follow valid markdown format.

### BROKEN links

None identified. All markdown links to paper-notes, syntheses, and internal documents point to files that exist on disk.

### ORPHAN citations

None identified. All citations in the synthesis appear in the text they are meant to support.

### OK citations (sample, not exhaustive)

- **Lines 12–13**: Zheng-Meister and Sauerbrei-Pruszynski linked to
  `/Users/dbrowne/Desktop/Programming/GitHub/Linus/docs/paper-notes/PIIS0896627324008080.md` and
  `/Users/dbrowne/Desktop/Programming/GitHub/Linus/docs/paper-notes/nihms-2096004.md` — valid, both files exist
- **Lines 17–19**: Güllich and Harvey primary papers linked to `science.adt7790.md` and
  `harvey-et-al-2023-the-dynamics-of-team-learning-harmony-and-rhythm-in-teamwork-arrangements-for-innovation.md` —
  valid, both files exist
- **Line 125**: Link to `skills-and-practices-synthesis.md` — valid, file exists
- **Line 206**: Link to `../specs/memory-architecture.md` — valid, file exists
- **Lines 212–213**: Links to `synthesis-landscape.md` and `total-landscape.md` — valid, both files exist
- **Line 168**: Self-reference to `skills-and-practices-synthesis.md` for the update action — valid, file exists
- **Section general**: All Güllich findings (elite overlap, peak inversion, predictor flip, effect sizes) are cited to
  the primary paper or emerge naturally from Harvey's structure
- **Lines 59–64**: Cognitive-throughput trio reasoning chains coherently through the Zheng-Meister (10 bit/s conscious
  channel) and Sauerbrei-Pruszynski (pushback on details) claims without orphaning either author

## Remediation recommendations (priority order)

1. **Low priority**: Add inline parenthetical citations for the two quantitative claims (Cohen's d effect sizes, nine
   orders of magnitude). These are minor annotations that would aid readers in directly locating the evidence without
   changing the narrative flow.

2. **No structural changes needed**: All four foundational papers have valid links, all internal document links resolve
   correctly, and no broken references exist. The synthesis is publication-ready from a traceability standpoint.

3. **Future maintenance**: When the skills-and-practices-synthesis is updated per the recommendation at line 169, refresh
   the backlink in this document if the filename changes.
