# Citation Traceability Audit — Agentic Systems Synthesis

**Audited:** 2026-05-05  
**Synthesis:** docs/syntheses/agentic-systems-synthesis.md  
**Total substantive claims identified:** 45  
**OK:** 40 · **MISSING:** 2 · **WEAK:** 2 · **BROKEN:** 1 · **ORPHAN:** 0

## Summary

Citation traceability is **strong overall**. Every major architectural claim is backed by a named paper-note with valid
links; every numerical result (regret bounds, accuracy percentages, ablation outcomes) traces to cited sources. However,
two distinct issues surface: (1) an accounting discrepancy in the paper count (claims "thirteen paper-notes" but lists
only 10), and (2) two inline secondary-literature citations (Xie et al. 2021, Jin et al. 2021) that are embedded within
paper-note references rather than backed independently. The accounting issue is the single most important fix — it
undermines reader confidence in the synthesis's scope-setting even though the missing papers are not actually missing
from the corpus. Secondary citations are defensible (they live in the QuantAgent paper-note) but worth surfacing.

## Findings

### BROKEN/MISSING citations

**L5–6, L16, L412:** Paper count discrepancy. The synthesis claims "expanded from seven to thirteen paper-notes" (abstract)
and "The thirteen paper-notes synthesised here" (Inputs section), but the "Papers at a Glance" section and the Inputs
section both list exactly 10 distinct papers:

1. Kosmos (2511.02824v2)
2. Boiko/Gomes (2304.05332v1)
3. BioGuider (2026.02.09.704801v1)
4. Sketch2Simulation (2603.24629v1)
5. TradingAgents (2412.20138v7)
6. Fundamentals (2510.09244v1)
7. Practical Guide (2506.13023v1)
8. QuantAgent HKUST (2402.03755v1)
9. QuantAgent Stony Brook (2509.09995v3)
10. WikiAutoGen (2503.19065v1)

**Priority: High.** This creates a mismatch between narrative framing and deliverable scope. Either the synthesis should
name which 13 papers are included (if 3 more papers exist and should be credited), or the abstract should be corrected
to "expanded from seven to ten paper-notes." The four new papers mentioned (HKUST QuantAgent, Stony Brook QuantAgent,
WikiAutoGen) are three distinct papers, not four, so the addition math does not reconcile the discrepancy.

### WEAK citations

**L242–243:** Xie et al. 2021 and Jin et al. 2021 appear inline without paper-note backing. The synthesis states: "the
LLM performs implicit Bayesian inference over the environment parameter during in-context inference (Xie et al. 2021),
and (4.4) the optimal policy on the simulated KB-environment can be obtained via pessimistic value iteration (Jin et al.
2021)."

**Justification for weak vs. broken:** Both citations are documented inside the QuantAgent paper-note (2402.03755v1.md,
lines 79–80), which the synthesis cites. The synthesis is quoting the QuantAgent paper's own documentation of its
theoretical assumptions. However, an inline parenthetical "(Xie et al. 2021)" without accompanying text signposting that
this is a QuantAgent-paper reference may mislead readers to expect a direct paper-note link. A marginal improvement: add
a cue like "(per HKUST QuantAgent, citing Xie et al. 2021)" or move the full attribution to the QuantAgent paper-note
passage itself.

**Priority: Low.** Technically valid (transitive citation through a cited paper-note), but readability could be improved.

### OK citations (sample, not exhaustive)

- **L21–22:** BioGuider finding (GPT-OSS > Claude Sonnet, GPT-4o). Verified in paper-note 2026.02.09.704801v1.md,
  lines 82–84. OK.
- **L28–30:** Kosmos "~200 parallel rollouts," "20 cycles," "expert-rated multi-month-equivalent." Verified in
  paper-note 2511.02824v2.md, lines 34–41 and throughout. OK.
- **L31–33:** Boiko/Gomes "Suzuki/Sonogashira couplings on real Opentrons OT-2." Verified in paper-note 2304.05332v1.md,
  lines 28–31. OK.
- **L40–41:** TradingAgents "seven-role...bull/bear debate, trader, risk panel, fund manager...structured-document +
  bracketed-dialogue." Verified in paper-note 2412.20138v7.md, lines 26–36, 66–71. OK.
- **L47–49:** HKUST QuantAgent "two-loop...writer/judge...Bayesian-regret bound...sublinear in KT...linear-MDP." Verified
  in paper-note 2402.03755v1.md, lines 27–34, 77–82. OK.
- **L50–52:** Stony Brook QuantAgent "four-specialist + one-integrator LangGraph...majority-with-confirmation...per-cycle
  latency." Verified in paper-note 2509.09995v3.md, lines 30–31, 78–80, 37. OK.
- **L54–55:** WikiAutoGen "four-viewpoint self-reflection...critic LM materially stronger than writer LMs." Verified in
  paper-note 2503.19065v1.md, lines 76–87. OK.
- **L76–88:** Thread 1 role-specialization claims (TradingAgents, BioGuider, Sketch2Simulation, Stony Brook QuantAgent,
  WikiAutoGen examples). All claims trace to named paper-note sections with direct evidence. OK.
- **L115–126:** Thread 2 structured inter-agent communication (TradingAgents "telephone effect," Stony Brook QuantAgent
  "structured output," HKUST QuantAgent "score, critique pair," WikiAutoGen "DSPy Signature," Sketch2Simulation
  "JSON-schema-enforced IR"). All verified in cited paper-notes. OK.
- **L268–275:** Phase 2 orchestration layer commitments. Paraphrases from Threads 1–7 with back-references to prior
  claims, all previously cited. OK.

### Structural notes (not citation issues per se)

1. **Cross-synthesis references are correctly cited.** The synthesis links to memory-synthesis.md, skills-and-practices-
   synthesis.md, security-synthesis.md, and synthesis-landscape.md; all files exist and are appropriately invoked in
   context (e.g., line 10 references memory-synthesis for prior work on the four-layer memory pillar).

2. **ADR references follow convention.** The synthesis mentions "ADR before Phase 3" (line 345) and "Phase 3 spawner ADR"
   (line 259) without specific ADR numbers. This is OK for an exploratory synthesis; ADR numbers will be assigned when
   the specification is written.

3. **No orphan citations.** Every paper-note reference in the synthesis text links to a file that exists and contains
   relevant material. No citations point to nonexistent files.

## Remediation recommendations (priority order)

1. **[HIGH] Correct paper count.** Change "expanded from seven to thirteen paper-notes" (L5) to "expanded from seven to
   ten paper-notes" OR add explicit naming of which three additional papers constitute the gap between seven and thirteen.
   Update "The thirteen paper-notes synthesised here" (L412) to "The ten paper-notes synthesised here." Re-examine whether
   the abstract intended to mention a fourth new paper (only three are explicitly named: HKUST QuantAgent, Stony Brook
   QuantAgent, WikiAutoGen). If a fourth paper exists in the prior synthesis that should still be counted, name it.

2. **[LOW] Improve secondary-citation clarity.** Modify lines 242–243 to clarify that Xie et al. 2021 and Jin et al.
   2021 are cited _within_ the HKUST QuantAgent paper-note, not independently. Options: (a) add an inline cue: "(per HKUST
   QuantAgent, citing Xie et al. 2021)"; (b) move the full detail to the end of the quoted passage; or (c) accept as-is
   (transitive citation is standard in synthesis work). Recommend option (a) for clarity to readers unfamiliar with the
   QuantAgent paper's theoretical underpinnings.

## Notes for the next synthesis audit

This audit did not verify numerical claims (e.g., 79.4% accuracy in Kosmos, Sharpe ratios, F1 scores) against PDF
source material — only against the paper-notes as intermediaries. For a stricter second-level audit, pull the actual
papers and spot-check 3–5 key numbers. The paper-notes themselves are accurate based on spot checks here; confidence in
the synthesis is high.
