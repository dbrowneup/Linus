# Citation Traceability Audit — Infrastructure Foundations Synthesis

**Audited:** 2026-05-05
**Synthesis:** `docs/syntheses/infra-foundations-synthesis.md`
**Audit method:** Full read-through with targeted verification of every substantive claim
**Total substantive claims identified:** 47
**OK:** 44 · **MISSING:** 0 · **WEAK:** 2 · **BROKEN:** 0 · **ORPHAN:** 1

## Summary

The synthesis is well-traced overall. All five primary papers are correctly linked. The new sections added on 2026-05-05 (LAB-Bench/BixBench benchmark anchors and g5-graph-tools KG/network tooling) both cite their underlying sources correctly — LAB-Bench and BixBench link to verified paper-notes, and g5-graph-tools references the cluster synthesis plus the three underlying repo-notes (hyalo, keppi, py3plex). The two weak citations are (1) a missing link from "Practical Guide for Evaluating LLMs" on first mention at line 14, and (2) references to "DISCO" and other Wave 3 papers that are named but not linked. One orphan finding: the synthesis refers to `repos/mlx-flash/` and `repos/flash-moe/` as reference implementations, but does not supply repo-notes for these in the docs/ hierarchy (though they are cloned in repos/).

## Findings

### MISSING citations
None. All substantive claims have identifiable citation targets.

### WEAK citations

1. **Line 14: "Practical Guide for Evaluating LLMs"** — Named in the opening paragraph ("adds a capability-first-measurement thread linking WHAM to the Practical Guide for Evaluating LLMs and the speed-and-tok/s paper") but not linked on first mention. The paper-note exists at `../paper-notes/2506.13023v1.md` and is properly cited later (line 199, 153). **Severity: LOW.** First mention should include a link for discoverability; later references are correct. **Remediation:** Add link on first mention at line 14.

2. **Line 84: "DISCO is the named Wave 3 example"** — DISCO and the four papers behind it (RFdiffusion, AlphaFold3, Boltz, Chroma) are named as prominent examples of Flow Matching usage but receive no links or paper-note citations. The synthesis treats them as sufficiently well-known that citation is deferred ("the named Wave 3 example"). **Severity: MEDIUM.** This is pedagogically acceptable if DISCO et al. are not yet in the Linus corpus, but the claim "DISCO is the named Wave 3 example" asserts a fact (naming DISCO as exemplary) without a citation anchor. **Status note:** These papers may be in development for future Wave 3 synthesis work; this is contextual rather than an error. **Remediation:** Either add inline parenthetical "(as noted in the generative-biology thread; paper-notes forthcoming)" or defer to function-annotation-discovery synthesis's treatment of Wave 3 papers.

### BROKEN links
None. All relative paths are correct and all targets exist.

### ORPHAN citations
1. **Lines 69–70: `repos/mlx-flash/` and `repos/flash-moe/`** — Referenced as evidence for larger-than-RAM streaming work but lack corresponding `docs/repo-notes/` entries. The repos are cloned (verified: both exist in `repos/`), but the synthesis provides no repo-note to document their contribution or methodology. **Severity: MEDIUM.** These are active reference implementations that the synthesis uses as evidence ("sits on top of the identical-stacked-block layer structure introduced here; the 'stream a layer at a time' trick only works because…"). Unlike third-party cloned repos, these appear to be Dan's/the project's own reference implementations. **Remediation:** Either (a) create `docs/repo-notes/mlx-flash.md` and `docs/repo-notes/flash-moe.md` to document the pattern and results, or (b) consolidate into an existing synthesis note (e.g., memory-synthesis.md or a future streaming-efficiency synthesis).

### OK citations (sample)

✓ All five primary papers correctly linked:
- NIPS-2017 Transformer (line 19, 57, 72, 74)
- Flow Matching 2506.02070v3 (line 20, 79)
- PAN 2511.09057v3 (line 21, 99)
- Google environmental 2508.15734v1 (line 23, 123)
- WHAM s41586-025-08600-3 (line 25, 143)

✓ Cross-synthesis links (all verified):
- memory-synthesis.md (lines 66, 108, 185, 249)
- function-annotation-discovery-synthesis.md (line 304)
- synthesis-landscape.md (line 229)
- GLOSSARY.md (line 195)

✓ Additional paper-notes (all verified to exist):
- BitNet 2310.11453v1 (lines 64, 211, 332)
- Llama 3 2407.21783v3 (line 72)
- Coconut 2412.06769v3 (line 106)
- Hogan KG survey 2003.02320v6 (line 165)
- Practical Guide 2506.13023v1 (lines 153, 199, 314)
- Speed-and-tok/s 2502.16721v1 (lines 15, 131, 200, 314)
- LLM in a Flash 2312.11514v3 (line 212)
- flash_moe.md (line 212)

✓ New 2026-05-05 sections (both well-cited):
- **LAB-Bench anchor (lines 294–315):** Links to function-annotation-discovery-synthesis.md for deeper treatment; correctly cites 2407.10362v3 (inherited from function-annot synthesis). States "Tier-1-equivalent action" and "Phase 1 baseline" with clear traceability.
- **BixBench anchor (lines 294–315):** Correctly cites 2503.00096v3. States "Phase 2 ingestion obligation" with specific canary-string requirement, anchored to g8-sci-agents cluster synthesis (line 310).
- **g5-graph-tools cluster (lines 317–328):** Links to `../syntheses/repo-clusters/g5-graph-tools.md` (verified to exist). Names hyalo, keppi, py3plex with "Integrate verdict" and "clean-reference verdict" status. Explains KB-substrate role clearly.

✓ Repo-notes for g5-graph-tools components (all verified):
- hyalo.md exists and is correctly referenced
- keppi.md exists and is correctly referenced
- py3plex.md exists and is correctly referenced

## Remediation recommendations (priority order)

1. **[QUICK FIX]** Add link to Practical Guide for Evaluating LLMs on first mention (line 14). Change `the Practical Guide for Evaluating LLMs` to `[the Practical Guide for Evaluating LLMs](../paper-notes/2506.13023v1.md)`. **Effort: 1 min.** **Impact: readability.**

2. **[MEDIUM]** Add a parenthetical note or cross-reference for Wave 3 papers (DISCO, RFdiffusion, AlphaFold3, Boltz, Chroma) at line 84. Either link to the function-annotation-discovery synthesis's Wave 3 section or add "(forthcoming in Wave 3 synthesis)" for discoverability. **Effort: 5 min.** **Impact: prevents reader confusion on where to find DISCO documentation.**

3. **[DEFERRED, PHASE 2]** Create or consolidate repo-notes for `mlx-flash` and `flash-moe`. These are load-bearing evidence for the streaming-efficiency thread. If they are Dan's own implementations, they warrant documentation. If they are reference clones to study, a 1-paragraph entry per repo suffices. **Effort: 30 min. each.** **Impact: closes the orphan finding and strengthens the streaming thread.**

## Notes for future audits

- The synthesis treats the Transformer paper and Flow Matching textbook as foundational references. Future audit should verify that downstream syntheses and paper-notes honor these as "REFERENCE" anchors without re-deriving their content.
- LAB-Bench and BixBench paper-notes were already in the corpus (2407.10362v3, 2503.00096v3); the synthesis correctly migrated the _references_ from function-annotation-discovery to infra-foundations on 2026-05-05 without duplicating content. Cross-synthesis coherence is good.
- g5-graph-tools cluster synthesis was created as a new anchor on 2026-05-05. Verify in the next audit that no other syntheses inadvertently duplicate the hyalo/keppi/py3plex coverage.
