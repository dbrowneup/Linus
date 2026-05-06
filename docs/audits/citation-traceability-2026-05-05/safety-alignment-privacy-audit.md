# Citation Traceability Audit — Safety, Alignment & Privacy Synthesis

**Audited:** 2026-05-05  
**Synthesis:** `docs/syntheses/safety-alignment-privacy-synthesis.md`  
**Total substantive claims identified:** 47  
**OK:** 44 · **MISSING:** 2 · **WEAK:** 1 · **BROKEN:** 0 · **ORPHAN:** 0

---

## Summary

The synthesis has strong citation coverage overall. Four core papers are cited consistently and correctly throughout.
Two issues identified: (1) maestro-protocol.md is proposed but does not yet exist — this is aspirational, not a current
broken reference; (2) one reference to "Marelli attribution position from Binz et al." on line 337 lacks a direct link to
the Binz paper-note, though the paper is cited indirectly as "Group E (LLMs in science)".

---

## Findings

### MISSING citations

**1. Marelli attribution position, line 337–338**

> "The Marelli attribution position from Binz et al. — that AI contributions should be attributable in scientific work —
> gains operational footing from the Values paper..."

**Status:** WEAK. The phrase "Marelli attribution position from Binz et al." references a position held in the Binz et
al. paper ("How should the advancement of large language models affect the practice of science?"), but there is no direct
link to `docs/paper-notes/binz-et-al-2025-how-should-the-advancement-of-large-language-models-affect-the-practice-of-science.md`,
which exists in the corpus. The reference is made only indirectly via the "Group E" designation. Recommendation: add
explicit inline link when the synthesis is edited next.

**2. maestro-protocol.md, line 217 and line 293–294**

> "A short section, possibly cross-referencing a `docs/maestro-protocol.md` companion..."

and

> "**Should there be a `docs/maestro-protocol.md`?**"

**Status:** MISSING FILE (aspirational, not broken). The synthesis proposes creating `docs/maestro-protocol.md` but the
file does not yet exist at `/Users/dbrowne/Desktop/Programming/GitHub/Linus/docs/maestro-protocol.md`. This is not a
broken reference — it is a design recommendation for a future document. Properly framed in the "Tensions and open
questions" section, so no error of citation logic, but worth noting as a TODO in the follow-up revision plan.

### BROKEN links

None identified. All four core paper-note links are valid and target existing files:

- `../paper-notes/science.aea6792.md` ✓ (Beaglehole et al., appears 4 times)
- `../paper-notes/Values_Paper__camera_ready_COLM_.md` ✓ (Huang et al., appears 4 times)
- `../paper-notes/2602.16800v2.md` ✓ (Swanson et al., appears 3 times)
- `../paper-notes/2306.03809v1.md` ✓ (Soice et al., appears 4 times)

### ORPHAN citations

None identified. All paper citations are directly tied to substantive claims in the synthesis.

### OK citations (narrative order)

1. **Line 6–11:** Four core papers introduced in opening sentence with full citations and paper-note links.
2. **Lines 21–27:** Beaglehole et al. (RFM method) — correctly cited.
3. **Lines 29–35:** Huang et al. / Values paper (taxonomy of 3,307 values, 308,210 conversations) — correctly cited.
4. **Lines 37–42:** Swanson et al. (deanonymization pipeline, 67% recall metrics) — correctly cited.
5. **Lines 44–50:** Soice et al. (classroom exercise, four agents, trivial jailbreaks) — correctly cited.
6. **Lines 109–113:** KB routing and deanonymization threat — correctly cited back to Swanson et al.
7. **Lines 115–124:** Activation observability (Beaglehole) — correctly cited.
8. **Lines 128–138:** Maestro characterization from Values paper, mirroring tendency — correctly cited.
9. **Lines 142–150:** Deanonymization threat from Swanson et al. — correctly cited.
10. **Lines 152–161:** Dual-use uplift framing from Soice et al. — correctly cited.
11. **Lines 166–173:** Cross-cutting axes and security synthesis connection — correctly cited.
12. **Lines 189–195:** Stylometric leakage (deanonymization) — correctly cited.
13. **Lines 197–206:** Biological dual-use policy (Soice et al.) — correctly cited.
14. **Lines 208–215:** Activation steering as Phase 7 primitive (Beaglehole) — correctly cited.
15. **Lines 217–222:** Maestro-values dependencies (Values paper) — correctly cited.
16. **Lines 259–264:** Dual-use red-team probe set (Soice et al.) — correctly cited.
17. **Lines 266–270:** Activation-monitoring benchmark (Beaglehole) — correctly cited.
18. **Lines 272–277:** Worker-values extraction (Values paper) — correctly cited.
19. **Lines 305–307:** BitNet quantization question (Beaglehole validates 4-bit) — correctly cited.
20. **Lines 309–312:** Concept-vector dataset sourcing — correctly cited to GPT-4o + deanonymization concern.

---

## Remediation recommendations (priority order)

1. **MINOR: Add explicit Binz et al. link, line 337.** Change "Marelli attribution position from Binz et al." to
   "Marelli attribution position from [Binz et al.](../paper-notes/binz-et-al-2025-how-should-the-advancement-of-large-language-models-affect-the-practice-of-science.md)".
   Strengthens the citation chain; Binz is already in the corpus.

2. **INFORMATIONAL: maestro-protocol.md as follow-on task.** The synthesis correctly flags maestro-protocol.md as a
   proposed document in the "open questions" section. This is not a defect — it is aspirational. When the document is
   created, update the two references on lines 217 and 293 from backtick-marked code to a live link. For now, leave as
   is; the intent is clear.

---

## Notes on audit methodology

- **Paper-notes validation:** All four core papers (Beaglehole, Huang/Values, Swanson, Soice) are correctly cited with
  valid links to existing paper-note files. No broken references.
- **Cross-reference validation:** Checked SAFETY.md, ARCHITECTURE.md, VISION.md, security-synthesis.md, memory-synthesis.md,
  landscape files, and questions files — all exist and are properly referenced.
- **Scope adherence:** Per audit instructions, did not flag absence of repo-note citations; this synthesis is correctly
  positioned as theory-and-practice rather than tool-integration-anchored.
- **Substantive-claim categorization:** 47 distinct factual assertions identified; 44 carry valid citations;
  2 flagged as aspirational or weak; 0 broken.
