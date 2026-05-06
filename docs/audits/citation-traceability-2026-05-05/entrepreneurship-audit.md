# Citation Traceability Audit — Entrepreneurship Synthesis

**Audited:** 2026-05-05
**Synthesis:** docs/syntheses/entrepreneurship-synthesis.md
**Total substantive claims identified:** 34
**OK:** 31 · **MISSING:** 0 · **WEAK:** 2 · **BROKEN:** 0 · **ORPHAN:** 0 · **DAN-NOTE:** 1 · **CLAUDE-MD:** 0

## Summary

Citation traceability in entrepreneurship-synthesis.md is strong. The synthesis effectively pulls from g10-finance,
g8-sci-agents, g9-bio, and supporting thematic syntheses with working links and verified underlying sources. Two claims
(dexter's compaction prompt preservation detail and OpenBB's per-session tool-activation scope) are accurately described
but lack direct quotes or line-number citations to repo-notes, making them WEAK rather than OK — they are verifiable via
the repo-notes files but require a reader to flip to another document to confirm. The whiteboard sketch is properly
flagged as DAN-NOTE and requires no external citation. All cluster verdicts (g10: 0× Integrate / 4× Study / 1× Ignore),
bioSkills count (~438), and specific component references (paper-qa tool names, Bacformer token count limits) are
traceable. No broken links, no orphan citations, no missing sources where substantive claims required them.

## Findings

### WEAK citations

1. **Line 133–139 (dexter compaction pattern).** Claim: "`src/agent/compact.ts` + `src/agent/microcompact.ts`:
   lightweight per-turn microcompact pass plus full LLM-summarization pass triggered at auto-compact threshold; the
   compaction prompt explicitly preserves all numerical data, forbids tool calls during compaction, and carries a
   structured summary of what was dropped."
   - **Status:** WEAK. The dexter repo-note (`docs/repo-notes/dexter.md`) confirms these file names and the pattern
     (lines 19–20, 35–37), but the synthesis does not cite line numbers or quote specific code regions. The claim is
     verifiable but requires reader cross-reference to dexter.md Section 3.

2. **Line 141–147 (OpenBB dynamic tool activation).** Claim: "OpenBB's `openbb-mcp` exposes ~35 data-provider
   integrations under one schema (~181 Pydantic models) but activates only the tools an agent has discovered it needs in
   the current session. For a literature-intelligence offering...the dynamic-activation pattern keeps the tool-budget
   cost bounded for small local Workers."
   - **Status:** WEAK. The OpenBB repo-note (`docs/repo-notes/OpenBB.md`) confirms the ~35 integrations (line 7) and
     ~181 standard models (line 26), and describes the dynamic per-session activation (lines 36–39). The synthesis
     claims this pattern addresses tool-budget cost in a literature-intelligence context, which is reasonable
     extrapolation but not explicitly stated in the repo-note. The link is strong but would benefit from a parenthetical
     reference to OpenBB.md Section 2 or Section 3.

### DAN-NOTE / CLAUDE-MD (no citation needed; verify framing)

1. **Lines 82–122 (whiteboard pipeline).** The sketch is framed as "Dan's whiteboard sketch" added 2026-05-05. This is
   properly flagged as DAN-NOTE and requires no external citation. Content matches the description ("local files →
   workspace ← GitHub repos → Claude (Maestro) → paper agents → fine-tune → business ideas") and is self-contained.
   ✓ **OK (DAN-NOTE).**

2. **Lines 71–78 (Dan's profile)** — references to "PhD biochemistry with genomics depth, 13 years of Python, prior
   founder experience (Botryonyx LLC, 2018–2019; raised $42K seed)." ✓ **OK (CLAUDE.md owner-background).** Verified in
   CLAUDE.md lines 13–33.

### OK citations (sample, not exhaustive; all verified)

1. **Line 17 — g10-finance cluster link** [`repo-clusters/g10-finance.md`]. ✓ File exists, verdict statement matches
   (0× Integrate, 4× Study, 1× Ignore per g10-finance.md line 3).

2. **Lines 19–22 — three biology syntheses** ([function-annotation-discovery](function-annotation-discovery-synthesis.md),
   [biological-foundation-models](biological-foundation-models-synthesis.md),
   [generative-biology](generative-biology-synthesis.md)). ✓ All three files exist and are correctly titled.

3. **Line 64 — bioSkills (~438 skills)** — cited as source context from g9-bio. ✓ Verified in g9-bio.md line 46: "The
   438 SKILL.md files across 63 bioinformatics categories."

4. **Line 88–122 — Opportunity 7 / Local AI infrastructure consulting.** Linked to Dan's "hands-on experience building
   Linus on the Apple Silicon / no-CUDA / Ollama stack...ahead of most research IT departments" and his "current
   LanzaTech enterprise-LLM-infrastructure role as credibility" (line 273). ✓ **OK (CLAUDE.md).** Verified in CLAUDE.md
   lines 13–14.

5. **Lines 180–198 — literature-intelligence stack convergence.** Claims that paper-qa earns Integrate verdict, with
   citations to g8-sci-agents for paper-qa and scientific-agent-skills; g9-bio for bioSkills and Bacformer; and
   infra-foundations-synthesis for LAB-Bench. ✓ All verdicts traceable:
   - paper-qa: g8-sci-agents.md line 6 (Integrate × 3, paper-qa listed).
   - bioSkills: g9-bio.md line 16 (one Integrate, bioSkills).
   - Bacformer: g9-bio.md line 16 (three Study, Bacformer is Study "path to Integrate").
   - LAB-Bench: function-annotation-discovery-synthesis.md cross-cutting note confirms LAB-Bench is in infra-foundations.

6. **Lines 225–273 — seven opportunities.** Claim: "originally housed in the `skills-and-practices` synthesis,
   extracted here for completeness." ✓ Verified in skills-and-practices-synthesis.md lines 235–247: section header
   states "Extracted 2026-05-05. The seven entrepreneurial opportunities...have been promoted to a first-class
   `entrepreneurship-synthesis.md`" and lists all seven by name.

7. **Line 394–402 — cross-reference matrix.** Links to g8-sci-agents.md, g9-bio.md, g10-finance.md, g7-harnesses.md. ✓
   All files exist and are correctly titled.

### MISSING citations

None identified. All substantive claims either carry citations or are properly flagged (DAN-NOTE, CLAUDE-MD owner
background, general framings).

### BROKEN links

None identified. All markdown links to syntheses and cluster documents resolve to existing files.

### ORPHAN citations

None identified. All cited documents are used meaningfully in context.

## Remediation recommendations (priority order)

1. **(Optional improvement, low priority)** Add parenthetical line-number citations to dexter.md and OpenBB.md for
   the two WEAK claims (compaction pattern and dynamic tool activation). Example: "The compaction prompt explicitly
   preserves all numerical data ... (see [`dexter.md` Section 3](../repo-notes/dexter.md#3-whats-reusable-in-linus)
   for implementation details)." This converts WEAK → OK without requiring text changes to entrepreneurship-synthesis.md
   itself.

2. **(Structural, optional)** The opportunities' pricing anchors (lines 226–227, 232–236, etc.) are explicitly flagged
   in the open question E9 (line 360–362) as "anchors borrowed from adjacent SaaS/consulting markets, not
   Dan-validated." The framing is honest. No remediation needed, but note that commercial validation at opportunity
   selection time will update these figures.

---

## Conclusion

The entrepreneurship-synthesis is well-grounded. Citations are present where required, cluster verdicts are traceable to
source documents, quantitative claims (bioSkills ~438, OpenBB ~35 providers, paper-qa tool names) are verifiable, and
the structure cleanly separates DAN-NOTE content (whiteboard sketch) from sourced content. The two WEAK citations are
minor — both claims are accurate and traceable, but a reader would benefit from explicit line references. No blocking
issues. The synthesis is ready for use as a reference document for Phase 2+ planning.
