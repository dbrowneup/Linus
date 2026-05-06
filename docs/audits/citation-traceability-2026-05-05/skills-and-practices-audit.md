# Citation Traceability Audit — Skills & Practices Synthesis

**Audited:** 2026-05-05  
**Synthesis:** docs/syntheses/skills-and-practices-synthesis.md  
**Total substantive claims identified:** 47  
**OK:** 38 · **MISSING:** 6 · **WEAK:** 3 · **BROKEN:** 0 · **ORPHAN:** 0

## Summary

Post-extraction state is coherent: Section 5 stub correctly points to `entrepreneurship-synthesis.md` (verified to exist);
Questions 1 and 4 relocations are properly noted. All five source threads (`context/threads/`) are confirmed present. The
synthesis is well-anchored to practitioner threads and internal Linus architecture docs (CLAUDE.md, DECISIONS.md, ROADMAP).

**Critical issue:** Section 3 (Skills Worth Incorporating) makes quantitative claims about external GitHub repos (star
counts, repo names) without any paper-note or repo-note citations to back them. These claims read as factual but have no
traceability. This is the audit's main finding.

## Findings

### MISSING citations

**Claim 1 (Section 3.3 — Superpowers skill set):** "The 'Superpowers' skill set (obra/superpowers, 96k stars) includes a
4-phase systematic debugging approach." Named repository with star count but no citation. Unknown source for star count
accuracy or which specific repos this refers to.

**Claim 2 (Section 3.5 — Market objection mining):** "From the '$312/Day' thread: collect Reddit, Twitter, and review
data..." The claim is attributed to a thread, but does not include inline reference. The thread is listed in Section 1
overview; this is acceptable if Section 1 was framed as the source list. However, the specific **methodology and
quantification** (which platforms, which extraction pattern) is stated as a claim but lacks a repo-note or link to the
actual thread content for verification.

**Claim 3 (Section 3.6 — KV-cache optimization):** "The `muratcankoylan/agent-skills-for-context-engineering` skill
(13.9k stars) covers token cost reduction and KV-cache tricks." Named external repo with star count; no internal
citation. Unknown source of the 13.9k star count.

**Claim 4 (Section 3.8 — Content repurposing):** "From the '$312/Day' thread: one long-form piece → Twitter threads,
LinkedIn posts..." Attributed to the thread, but no inline link or excerpt provided. This is a method claim that should
be verifiable in the source thread.

**Claim 5 (Section 3.9 — Vanna AI pattern):** "'vanna-ai/vanna' implements this pattern. Linus does not have this..."
Named external repo; no internal citation or verification that this is the correct repo for NL-to-SQL.

**Claim 6 (Section 3.10 — Codebase-to-knowledge-graph):** "`DeusData/codebase-memory-mcp` converts a codebase into a
persistent knowledge graph." Named external repo; no internal citation. This claim would benefit from a repo-note to
verify the feature claim.

### WEAK citations

**Claim A (Section 2, Practice 1 — "tiered manifest"):** References "The Cowork thread" and describes its fix (three-tier
manifest), but does not include a link to the actual thread file. However, Section 1 does name "17 Best Practices for
Claude Cowork" as a source; this is contextually valid but could be more explicit per-claim. The internal reference to
CLAUDE.md as modeling the pattern helps.

**Claim B (Section 3.13 — Skill Creator skill):** "Anthropic's official Skill Creator skill
(`anthropics/skills/tree/main/skills/skill-creator`) takes a workflow description and produces a `SKILL.md` in five
minutes." This is attributed to an Anthropic official resource (external), not a paper-note or repo-note. The "five
minutes" claim has no visible source.

**Claim C (Section 6 — "compact prompts" setting):** "The 'compact prompts' setting in Cline is specifically documented
to improve performance on local hardware..." Cline is in `repos/cline/` and a repo-note exists at
`docs/repo-notes/cline.md`, but that note is not explicitly linked. The synthesis should cite
`../repo-notes/cline.md` to ground this claim.

### BROKEN links

**None detected.** All internal references to `/entrepreneurship-synthesis.md`, `repos/cline/`, CLAUDE.md, and
ROADMAP.md resolve correctly in repo structure.

### ORPHAN citations

**None detected.** No citations point to missing or deleted files.

### OK citations (sample, not exhaustive)

- **Section 1, Overview:** All five source threads named correctly:
  - "17 Best Practices For Claude Cowork.txt" ✓
  - "Stop Staring at the Files.txt" ✓
  - "17 Claude Skills → $312:Day → $10K:Month.txt" ✓
  - "Top 50 Claude Skills & GitHub Repos for AI.txt" ✓
  - "Cline description.txt" ✓

- **Section 2, Practice 2:** "This is exactly the behavior CLAUDE.md is modeling..." — direct reference to internal
  project doc ✓

- **Section 4:** "Repos already in `repos/`" (autoresearch, autoresearch-mlx, cline, openclaw, claw-code,
  claw-code-local) — verifiable in repo structure ✓

- **Section 5:** Cross-reference to `entrepreneurship-synthesis.md` — file exists and is correctly positioned ✓

- **Section 6:** "Cline is already in `repos/cline/` as a reference clone." — verifiable ✓

- **Section 7, Question 1:** "Moved to [`entrepreneurship-synthesis.md`]..." — proper cross-reference with link ✓

## Remediation recommendations (priority order)

1. **HIGH: Section 3 — add repo-notes for external skill repos.** Create brief notes for `obra/superpowers`,
   `muratcankoylan/agent-skills-for-context-engineering`, `vanna-ai/vanna`, and `DeusData/codebase-memory-mcp`
   following the existing repo-notes pattern. This grounds the star counts and feature claims in verifiable documents.
   Link these notes from Section 3 as `[obra/superpowers](../repo-notes/superpowers.md)` etc.

2. **MEDIUM: Section 6 — explicit link to cline.md repo-note.** Change "The description thread clarifies..." and the
   "compact prompts" claim to cite `[../repo-notes/cline.md](../repo-notes/cline.md)` so readers can verify the
   documentation claim.

3. **MEDIUM: Section 3.2 — Anthropic official skills.** Add a comment or footnote that Anthropic official skills are
   external references (not versioned in this repo), so their exact URLs and features may drift. This is not a
   traceability problem but a maintenance note.

4. **LOW: Section 2 — optional per-practice thread citations.** If Dan prefers strict per-claim citations, add inline
   notes like "[per 17 Best Practices thread, Practice 1]" or "[Stop Staring at the Files thread]" to each practice.
   Current approach (attributing all practices to threads in the overview) is acceptable.

---

**Post-extraction verdict:** The Section 5 stub is functional and the entrepreneurship cross-reference is clear. The
larger issue is Section 3's external repo claims lack traceability. Once repo-notes are added for those external
resources, this synthesis will meet the Linus citation standard.
