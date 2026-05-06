# Citation Traceability Audit — Generative Biology Synthesis

**Audited:** 2026-05-05  
**Synthesis:** docs/syntheses/generative-biology-synthesis.md  
**Total substantive claims identified:** 47  
**OK:** 38 · **MISSING:** 3 · **WEAK:** 4 · **BROKEN:** 0 · **ORPHAN:** 2

## Summary

The synthesis demonstrates strong citation discipline overall: 81% of substantive claims trace cleanly to valid paper notes, cluster syntheses, or cross-referenced syntheses. Three claims lack any citation and need urgent anchoring; four citations are weak (cited indirectly through another synthesis rather than directly to paper notes). No broken links detected. The "Inputs" section at the end correctly lists all six Group B papers, but the body text would benefit from frontloading paper-note links in the opening section where each paper is introduced.

## Findings

### MISSING citations

- **L41:** "de novo carbene-transfer enzymes that exceed evolved P450 variants in TTN" — This is a quantitative verdict on DISCO's validation strength. Cited implicitly through the DISCO paper note reference but no direct link at the claim site. Priority: **high**. Fix: Add inline link `[exceeding P450 variants](../paper-notes/2604.05181v1.md)` or similar.

- **L101:** "16 of 302 designs produced viable phages, several outcompeting ΦX174 itself" — The quantitative result (16/302) is the headline validation outcome for generative phages and sits at the core of dual-use policy. Should have explicit paper-note citation inline, not just contextual. Priority: **high**. Fix: Add `[16 viable phages from 302 candidates (King et al., 2025)](../paper-notes/2025.09.12.675911v1.md)`.

- **L184:** "dCT-H11 produced ~35 improved variants under one round of random mutagenesis" — Specific experimental detail from DISCO's error-prone PCR section. No citation given. Priority: **med**. Fix: Link to DISCO paper note.

### WEAK citations

- **L9, "memory synthesis":** Referenced as `[memory](memory-synthesis.md)` — This is a relative link without the full `../syntheses/` path. While it resolves in context (Markdown parser handles relative paths from the same directory tree), it's inconsistent with other cross-synthesis references that use explicit `../syntheses/synthesis-name.md` format. The **biological-foundation-models** reference on L16 uses explicit relative path; inconsistency creates maintenance risk. Priority: **low**. Fix: Standardize to `../syntheses/memory-synthesis.md`.

- **L16:** "[Group A](biological-foundation-models-synthesis.md)" — Another relative-link-without-path reference. Same issue as above. Priority: **low**.

- **L198–209:** "Feynman-Kac corrector framework from DISCO" — Referenced as "from DISCO" in prose but no inline link to the paper note. The claim is substantive (architectural pattern worth synthesis-level analysis) but relies on reader context from earlier L39 DISCO introduction rather than a direct citation. Priority: **med**. Fix: Add inline link when the FKC concept is first introduced in this section.

- **L267–268:** "the same shape the [skills synthesis](skills-and-practices-synthesis.md) named for Dan's research workflow" — Cites to skills synthesis but does not specify which section or what the named pattern is called. Reader must navigate the target synthesis to understand what "shape" is being referenced. Priority: **low**. Fix: Include the pattern name explicitly in the prose (e.g., "[skills synthesis](../syntheses/skills-and-practices-synthesis.md) named this the 'generate→score→filter workflow'").

### BROKEN links

None detected. All paper-note filenames, synthesis names, and ADR references are valid and resolvable.

### ORPHAN citations

- **L20, "2306.03809v1"** — Referenced directly as `[2306.03809v1](../paper-notes/2306.03809v1.md)` with inline link. This is the dual-use paper. Citation is _present_ but not embedded in supporting prose at L20 — the reader gets the link but no context for what the paper is or why it matters at this point. The paper is properly anchored later (L228, L357, L483) but the opening L20 reference jumps ahead of narrative setup. Not a data error, but a UX friction point. Priority: **low**. Fix: Consider adding brief apposition at L20: "the dual-use synthesis (`[2306.03809v1](../paper-notes/2306.03809v1.md)`)".

- **L254–255, "the mCSM-metal note already proposed the PLM+graph+rules archetype"** — References "the mCSM-metal note" but uses indirect phrasing ("already proposed") rather than a direct link. The note does exist (`../paper-notes/1-s2.0-S0022283626000513-main.md`) and the reader can infer it, but no explicit citation is embedded. Priority: **med**. Fix: Add direct link: `[mCSM-metal paper note](../paper-notes/1-s2.0-S0022283626000513-main.md) already proposed`.

### OK citations (sample, not exhaustive)

These substantive claims are properly cited:

- **L27–29, mCSM-metal introduction:** Linked directly to paper note with clear pointer to webserver-only release. ✓
- **L31–33, Trias introduction:** 47M parameters, BART, GFP benchmark — all facts with direct paper-note link. ✓
- **L35–37, GenNA introduction:** 3.6B parameters, cross-modal BPE, English prompting — facts with direct link. ✓
- **L39–41, DISCO introduction:** Joint diffusion, context conditioning, carbene enzymes — linked. ✓
- **L43–45, DeepSeMS introduction:** ~100M, Pfam→SMILES, ocean MAGs, antibiotic candidates — linked. ✓
- **L47–49, generative phages introduction:** Evo 1/2 fine-tuning, 15K Microviridae, 16/302 viable (redundant with missing citation above but linked here). ✓
- **L70–72, Trias perplexity correlation:** ρ = -0.76 GFP fluorescence claim — correctly attributed with correlation coefficient. ✓
- **L78–80, GenNA in-silico validation:** tRNAscan-SE, wobble behavior, stratified mutation effects — linked with examples. ✓
- **L169–174, validation rigor section:** Wet-lab vs in-silico split across papers — each paper type is properly traced. ✓
- **L228–230, connection to 2306.03809v1 dual-use paper:** Properly linked and contextualized. ✓
- **L360–381, SAFETY.md implications:** Recommends SAFETY.md edits and references both generative-phage and 2306.03809v1 papers by name. ✓
- **L399–406, KnowledgeBase schema:** Designed-artefact triple described with reference to specific papers (generative phages, DISCO, DeepSeMS). ✓

## Remediation recommendations (priority order)

1. **HIGH:** Add inline paper-note link at L101 for the "16 viable phages" quantitative result. This is the linchpin of dual-use policy and should not rely on contextual inference.

2. **HIGH:** Add inline paper-note link at L41 for "exceed evolved P450 variants in TTN." This is a key validation verdict and deserves explicit traceability.

3. **MED:** Add inline paper-note link at L184 for the dCT-H11 error-prone PCR detail (specific experimental outcome).

4. **MED:** Add explicit paper-note link when Feynman-Kac correctors are first named as a reusable pattern (L206–209).

5. **MED:** Clarify the indirect reference at L254–255 by adding a direct link to the mCSM-metal note.

6. **LOW:** Standardize all cross-synthesis references to use explicit relative paths (`../syntheses/memory-synthesis.md` instead of `memory-synthesis.md`) for consistency and maintainability.

7. **LOW:** Wrap the 2306.03809v1 link at L20 with brief context (e.g., "dual-use synthesis").

---

## Notes on citation style

The synthesis follows a convention where paper introductions (L27–49) have clean paper-note links in their opening definitions, and specific architectural or quantitative claims drawn from those papers later in the document sometimes cite by name + inline description rather than re-linking. This works well when the papers are introduced early, but works poorly when a claim is made before the reader has encountered the paper. The L101 "16/302" and L41 "exceed P450" claims fall into this trap — they're central claims that should be anchored directly, not deferred to earlier prose context.

The cross-references to syntheses, landscapes, and SAFETY.md are consistently present and well-formed. No missing dependencies detected in the broader knowledge structure.
