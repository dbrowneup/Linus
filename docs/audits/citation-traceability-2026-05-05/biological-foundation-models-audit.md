# Citation Traceability Audit — Biological Foundation Models Synthesis

**Audited:** 2026-05-05
**Synthesis:** docs/syntheses/biological-foundation-models-synthesis.md
**Total substantive claims identified:** 67
**OK:** 56 · **MISSING:** 9 · **WEAK:** 2 · **BROKEN:** 0 · **ORPHAN:** 0

## Summary

The biological foundation models synthesis demonstrates strong citation discipline overall, with 84% of substantive claims properly traced to supporting paper-notes. Nine claims lack explicit citations but are defensible as either architectural framing, comparative meta-analysis across papers, or Linus-specific design reasoning. Two weak citations point to thematically related syntheses without the specificity the claims deserve. No broken or orphan links; all referenced files exist.

**Priority remediation:** Add paper-note links to the quantitative performance comparisons in sections "Cross-cutting threads" and "Implications for Linus skills," and tighten the citations for the two simulator-pretraining generalizations to explicitly tie them to METL's paper-note.

## Findings

### MISSING citations
- **L55:** "few-shot DNA-protein matching result (LucaOne 0.84 vs DNABert2+ESM2 0.73)" — cited implicitly via the LucaOne paper-note link at L27, but the specific metric (0.84 vs 0.73) should be directly attributed to the paper-note section. Verifiable in s42256-025-01044-4.md Key Results. Priority: **medium** — the link is present but the exact numbers deserve explicit section-level anchoring.

- **L71:** "RiNALMo beats SpliceBERT (pretrained exclusively on pre-mRNA) on splicing despite seeing no mRNA at all" — cited to memory-synthesis implicitly; should cite s41467-025-60872-5.md Key Results (multi-species splice-site). Priority: **high** — this is a signature RiNALMo result that appears in the paper-note but not explicitly tagged here.

- **L72:** "AlphaGenome beats Evo 2 on the regulatory variant subdomain where Evo 2's own paper acknowledges trailing ChromBPNet" — AlphaGenome is cited (L29), but the Evo 2 paper's acknowledgment of ChromBPNet shortfall is not. Verifiable in s41586-026-10176-5.md. Priority: **medium** — comparative claim across two papers that could be more explicit about the Evo 2 source.

- **L86–93:** Releases and licensing posture (Evo 2, LucaOne, RiNALMo, Bacformer, METL, REMME/REBEAN, AlphaGenome, ProteinReasoner) — each is cited to a paper-note, but the detailed release claims (e.g., "OpenGenome2" for Evo 2, "CC-BY-4.0" for LucaOne, "Apache 2.0" for Bacformer) could have inline paper-note citations within each item rather than relying on the earlier bracket reference. Verifiable in all eight paper-notes. Priority: **low** — the citations are present; this is a documentation style preference.

- **L123:** "RiNALMo's diversity-clustered batching (cluster 36 M sequences at 70% identity into 17 M clusters, sample one per cluster per minibatch)" — cited to paper-note s41467-025-60872-5.md implicitly via section heading, but the specific numbers (36M → 17M, 70% identity) deserve a direct paper-note anchor. Verifiable in s41467-025-60872-5.md section "What they propose." Priority: **medium** — quantitative claim that should be explicitly traced.

- **L163:** "the GFP design experiment (fine-tune on 64 wet-lab variants, synthesise 20, get 16 functional)" — cited implicitly via METL paper-note at L40, but should be explicitly anchored. Verifiable in s41592-025-02776-2.md Key Results. Priority: **medium** — signature experimental outcome deserving explicit citation.

- **L165:** "'29 simulated points ≈ 1 experimental point' trade-off heuristic" — cited implicitly via METL at L40, but the specific trade-off heuristic is claimed as METL evidence and should be explicitly anchored. Verifiable in s41592-025-02776-2.md. Priority: **medium** — quantitative heuristic needing direct trace.

- **L194:** "AlphaGenome ISM outputs identify the specific motif a variant creates or disrupts and link to JASPAR matrix IDs" — cited implicitly to AlphaGenome paper-note at L29, but the specific claim about ISM output and JASPAR linking deserves an explicit section reference. Verifiable in s41586-025-10014-0.md. Priority: **low** — thematic connection is clear; specificity improvement optional.

- **L196:** "released 1.3 M-MAG annotation cache for 32 traits" — cited implicitly to Bacformer at L34, but the specific number of MAGs and traits should be explicitly referenced. Verifiable in 2025.07.20.665723v2.md Key Results. Priority: **low** — supporting detail; main claim is cited.

### WEAK citations
- **L143–144:** "This is the same lesson the [memory synthesis](memory-synthesis.md) articulated for text LLMs from a different angle: long context is useful but not a substitute for an architectural memory layer when you are memory-bound." — The memory-synthesis is cited, but the synthesis does not directly articulate a text-LLM equivalent of this architectural principle. The claim is inferred from the memory synthesis's framing, not explicitly stated there. Verifiable by reading memory-synthesis.md. Priority: **low** — contextual cross-reference; not a factual claim requiring hard evidence, but the paraphrase is looser than typical.

- **L200–205:** "KnowledgeBase should expose a typed `model_prediction` edge class... When the model is updated, the content-hash mechanism flags the KG edges that need revalidation. Without this discipline, model-derived KG content becomes indistinguishable from curated content within months." — Cites the [LLM wiki synthesis](llm-wiki-synthesis.md) for the "claim-typing pattern," but the specific architecture recommendation (content-hash flagging on update, the revalidation discipline) is not explicitly stated in the llm-wiki-synthesis. This is a design inference from Group A evidence, not a direct citation of llm-wiki-synthesis's claims. The underlying principle is sound but should be attributed to "inferred from [llm-wiki-synthesis]" or tied directly to a specific Group A paper's reasoning. Priority: **medium** — architectural recommendation that should either cite a specific paper-note or explicitly state it as a synthesis recommendation.

### BROKEN links
None. All paper-note, repo-note, and synthesis cross-references verified to exist.

### ORPHAN citations
None. All citations point to supporting material that is genuinely relevant to the claims they accompany.

### OK citations (sample, not exhaustive)
- **L25–44:** The eight paper-at-a-glance descriptions (Evo 2, LucaOne, AlphaGenome, RiNALMo, Bacformer, ProteinReasoner, METL, REMME/REBEAN) all cite their respective paper-notes with working markdown links. ✓

- **L50–51:** Generalist vs specialist axis introduced; claims about model postures are immediately supported by paper-note references. ✓

- **L70–77:** Comparative verdicts on strategy viability cite evidence directly to paper-notes: LucaOne discussion (L70), RiNALMo vs SpliceBERT (L71), AlphaGenome vs Evo 2 (L72), Bacformer essentiality (L73). ✓

- **L112–114:** Modern Transformer recipe convergence (RoPE, SwiGLU, FlashAttention-2) cited to paper-notes for RiNALMo, LucaOne, ProteinReasoner, Bacformer. ✓

- **L129:** Evo 2 1M-token context and AlphaGenome 1 Mb window claims; both cited to paper-notes L25 and L29. ✓

- **L148–152:** RiNALMo ArchiveII results and Evo 2 BRCA1 AUROC 0.95 both explicitly cited to respective paper-notes. ✓

- **L171–187:** M1 Max viability section systematically cites parameter counts and inference profiles to paper-notes for each model. ✓

- **L211–240:** Skill recommendations (REBEAN, Bacformer, RiNALMo, AlphaGenome + Evo 2 hybrid) all cite evidence to paper-notes and reference SAFETY.md for policy constraints. ✓

- **L244–266:** Phase 6 fine-tuning recommendations cite specific paper-notes (METL at L245–249, REMME/REBEAN at L251–255, RiNALMo and LucaOne at L257–258). ✓

- **L272–288:** Phase 4 data-sovereignty recommendations cite OpenGenome2, AlphaGenome evaluation datasets, Bacformer MAG cache, and RiNALMo evaluation sets all to paper-notes. ✓

## Remediation recommendations (priority order)

1. **Add explicit paper-note anchors to quantitative comparative claims.** L55 (LucaOne 0.84 vs 0.73), L71 (RiNALMo splicing), L123 (RiNALMo clustering 36M→17M), L163 (GFP 64 variants → 20 designed), L165 (29:1 trade-off). These are signature results that deserve section-level references, not just paragraph-level paper-note links. Use inline format: `[[s41586-026-10176-5.md#key-results]]` or similar anchor.

2. **Clarify the KnowledgeBase `model_prediction` edge design (L200–205).** This is a synthesis recommendation, not a direct citation of prior work. Either explicitly state "recommended from Group A implications" or tie it more directly to ProteinReasoner's three-modality framing and Bacformer's phenotype-attribution design. Currently feels slightly orphaned from its supporting evidence.

3. **Strengthen the memory-synthesis cross-reference (L143–144).** Verify the claim about "long context useful but not a substitute for architectural memory" appears explicitly in memory-synthesis.md, or rephrase as "analogously, for text LLMs, long context trades off against architectural memory under unified-memory constraints" and remove the synthesis citation.

4. **Add inline brief citations to release details (L86–93).** Optional but improves traceability. Currently "Five releases are unambiguously open and locally deployable: Evo 2 (weights, code, OpenGenome2, SAE checkpoints), ..." has excellent detail but no inline paper-note cues for a reader who wants to verify each release posture. Consider: "Evo 2 ([ref](../paper-notes/s41586-026-10176-5.md#key-results), weights/code/OpenGenome2/SAEs), ..." — lightweight and keeps the paragraph readable.

5. **Watch ProteinReasoner checkpoint release (L328–329).** Already called out as a low-priority watch; no action required, but consider a reminder comment in DECISIONS.md or top-questions.md to revisit this synthesis when BioMap releases checkpoints.

## Citation style observations

**Strengths:**
- Paper-note links are consistently formatted and all verified to exist.
- Comparative claims across multiple models cite the relevant paper-notes in close proximity.
- Quantitative numbers (parameter counts, context windows, accuracy metrics) are almost always traceable to paper-notes.
- Linus-specific design recommendations (Phase 6, Phase 7 skill order) are explicitly distinguished from paper evidence.

**Gaps:**
- Some comparative verdicts (e.g., "RiNALMo beats X on Y") cite the RiNALMo paper-note but could strengthen by explicitly calling out the subsection (Key Results, Ablations, etc.).
- Cross-synthesis references (memory-synthesis, llm-wiki-synthesis, skills-and-practices-synthesis) are thematic rather than evidence-based; no harm, but worth distinguishing from hard citations in a second pass.
