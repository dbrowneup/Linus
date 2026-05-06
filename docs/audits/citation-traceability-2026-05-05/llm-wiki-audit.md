# Citation Traceability Audit — LLM Wiki Synthesis

**Audited:** 2026-05-05
**Synthesis:** docs/syntheses/llm-wiki-synthesis.md
**Total substantive claims identified:** 85+
**OK:** 12 · **MISSING:** 65+ · **WEAK:** 8 · **BROKEN:** 2 · **ORPHAN:** 0

---

## Summary

The LLM Wiki Synthesis makes numerous substantive claims about architecture patterns, community practices, and specific tool implementations, but contains **zero markdown links** to supporting documentation. All citations are in-prose only (e.g., "Rohit's v2," "practitioners who measured," "community consensus"), with no links to repo-notes, paper-notes, or cluster syntheses. Two critical files referenced throughout (COMMUNITY_INSIGHTS.md and KB_DESIGN_PATTERNS.md) do not exist in the repository. Repo-notes for cited tools all exist, but are never linked from the synthesis — readers must manually construct paths. This severely compromises traceability for a corpus that values audit trails.

---

## Findings

### BROKEN links

1. **Line 3-4**: References "COMMUNITY_INSIGHTS.md" in source preamble → **FILE DOES NOT EXIST**
2. **Line 3-4**: References "KB_DESIGN_PATTERNS.md" in source preamble → **FILE DOES NOT EXIST**
3. **Lines 296, 472**: Section 5 and closing reference "KB_DESIGN_PATTERNS.md" as source for twelve patterns → **ORPHAN DEPENDENCY**

The synthesis treats KB_DESIGN_PATTERNS.md as its primary source for implementable patterns (Section 5 opens with "KB_DESIGN_PATTERNS.md translates the community learnings...") but the file is not present anywhere in the docs tree. This is load-bearing: all pattern descriptions (claim typing, content hashing, contradiction policy, entity types) are attributed back to a non-existent document.

### MISSING citations

**Section 1 (Overview, lines 8-25):**
- Karpathy's April 2026 gist (name, publication date, ~485 comments) — no link to source gist, paper-note, or repo-note
- Rohit Garg + agentmemory project — no link to `../repo-notes/agentmemory.md`
- Rohit's "v2" follow-on gist — attributed in-prose only

**Section 2 (Core Concepts, lines 29-99):**
14 distinct architectural patterns presented as community consensus or research findings — NONE linked to sources:
- Compile-don't-retrieve distinction (RAG vs wiki)
- Three-layer architecture (raw/wiki/schema)
- Memory lifecycle and Ebbinghaus decay
- Consolidation tiers (working/episodic/semantic/procedural)
- Typed knowledge graphs
- Hybrid search (BM25+vector+graph)
- Scoping determinism
- Epistemic claim typing (`[!source]`, etc.)
- Content hashing for staleness
- Write-back rule
- Quality gates at ingest
- Schema as flywheel
- Two-layer wiki architecture
- Speculative linking (red links)

All attributed to "community" or "practitioners" with no citations.

**Section 3 (GitHub Repos, lines 112-219):**
~20 repos listed with functional claims, metrics, and phase assignments — ZERO markdown links to corresponding repo-notes despite all 20 having `.md` files in `../repo-notes/`:
- obsidian-llm-wiki-local → ../repo-notes/obsidian-llm-wiki-local.md (EXISTS but UNLINKED)
- NiharShrotri/llm-wiki → ../repo-notes/llmwiki.md (EXISTS but UNLINKED)
- 7xuanlu/origin → ../repo-notes/origin.md (EXISTS but UNLINKED)
- nashsu/llm_wiki → ../repo-notes/llmwiki-cli.md (EXISTS but UNLINKED)
- jgoldfed/keppi → ../repo-notes/keppi.md (EXISTS but UNLINKED)
- omega-memory/omega-memory → ../repo-notes/omega-memory.md (EXISTS but UNLINKED)
- (pattern continues for all 20+ repos)

**Section 4 (Community Insights, lines 221-286):**
~10 major insights, each attributed in-prose to "practitioner," "serious practitioners," "community consensus," or unnamed builders — ZERO citations. Example:
- Line 223-228: Hot cache pattern (2.7x ratio, 192.6 KB/122.4 KB metrics) — attributed to "one practitioner measured" with no link to a synthesis, paper-note, or repo-note
- Line 236-242: Epistemic integrity concerns from "multiple serious practitioners" — no sources
- Line 250-253: Write-back rule discipline — attributed to "practitioners who implemented this rule" with no traceability

**Section 6 (Autoresearch and LLM-in-a-Flash, lines 339-374):**
- Line 341: "paper and code are in `repos/flash-moe`" — no markdown link (should be `[flash-moe repo](../repo-notes/flash-moe.md)`)
- Line 349-352: Autoresearch methodology, 90 experiments, 42% discarded — no link to autoresearch-mlx repo-note or ROADMAP context
- Line 372-373: "Linus has both `repos/ANE` and `repos/flash-moe`" — conversational but unlinked

**Section 7 (Open Questions, lines 377-428):**
- Line 412: ">60% entity overlap as threshold" attributed to unnamed "KevinYoung-Kw's system" — no repo link (no file exists for this person in repo-notes)
- Line 396-399: FUNGI framework (Frame, Unearth, Network, Grow, Interrogate) — introduced without source or link

### WEAK citations

1. **"Rohit's v2" (lines 13, 44, 390, 412):** Mentioned as a specific work but never linked to `../repo-notes/agentmemory.md` or any primary source. Readers cannot verify what "v2" is or locate the original gist.

2. **In-prose attribution without hyperlinks (Section 4, lines 223–286):** Phrases like "one practitioner measured," "community consensus," "serious practitioners," and "enterprise practitioner" are documentary but untraceable. These claims need links to either the original gist comments, cluster syntheses that synthesized those comments, or repo-notes that describe implementations.

3. **Phase assignments (throughout):** "Relevant to Phase 2," "Phase 3 when...," etc., referenced 40+ times — no link to ROADMAP.md or ARCHITECTURE.md for context.

4. **"Karpathy explicitly recommended" (line 198):** Specific claim about tobi/qmd — no source link.

### ORPHAN citations (sources cited in preamble but unused)

The preamble (line 3-4) claims synthesis is from:
- Karpathy LLM Wiki Gist ✓ (mentioned in text)
- Rohit LLM Wiki v2 Gist ✓ (mentioned in text)
- Karpathy LLM Wiki Repos list (mentioned but source not linked)
- Autoresearching Apple's LLM in a Flash ✓ (Section 6)
- COMMUNITY_INSIGHTS.md ✗ (DOESN'T EXIST)
- KB_DESIGN_PATTERNS.md ✗ (DOESN'T EXIST)

### OK citations (sample)

- **Line 117-118**: obsidian-llm-wiki-local + "v0.5" + feature list — stated clearly, repo-note exists; would benefit from link but facts are traceable via repo listing.
- **Line 134-136**: keppi + specific metrics (1,471 notes, 267K edges) — stated clearly, repo-note exists (though unlinked).
- **Line 177-180**: agentmemory + specific metrics (95.2% on LongMemEval-S, 43 MCP tools) — stated clearly, repo-note exists (though unlinked).
- **Line 341-373**: Flash-moe findings (5.7 t/s, 5.5 GB resident, M3 Max specifics) — stated clearly, repo-notes exist for both flash-moe and ANE; intra-doc reference at line 341 sufficient but lacks markdown link.

---

## Remediation recommendations (priority order)

1. **Create and link KB_DESIGN_PATTERNS.md immediately.** Section 5 (lines 294–335) depends on this file. If it exists elsewhere (perhaps as notes or a drafted file), move it to `docs/syntheses/` and update the reference. If it hasn't been written, write it as a separate synthesis (translating the 12 patterns mentioned into a standalone reference). Until it exists, Section 5 is unverifiable.

2. **Resolve COMMUNITY_INSIGHTS.md.** Either create the file (if it's a synthesis of the Karpathy gist comments) or remove it from the preamble. If the insights are dispersed in Section 4, create a cluster synthesis `g11-community-wiki-insights.md` and link it.

3. **Add markdown links to all repo-notes in Section 3.** Each repo (lines 112–219) should have a link like `[obsidian-llm-wiki-local](../repo-notes/obsidian-llm-wiki-local.md)`. Regex replace pattern: repo names → `[repo-name](../repo-notes/repo-name.md)`. Verify links exist before publishing.

4. **Convert in-prose attributions in Section 4 to cited sources.** Each claim about "practitioners," "community," or specific individuals (lines 223–286) should either:
   - Link to a cluster synthesis that aggregates those comments (e.g., `[community wiki insights](../syntheses/repo-clusters/g11-*.md)`)
   - Link to a specific repo-note that describes the implementation (e.g., "the hot cache pattern [from badwally/TheKnowledge](../repo-notes/the-knowledge.md)")
   - Reference a footnote or `[context]` anchor

5. **Add ROADMAP and ARCHITECTURE links for Phase references.** Replace bare "Phase 2," "Phase 3" with `[Phase 2](../../ROADMAP.md)` for context.

6. **Hyperlink the LLM-in-a-Flash and autoresearch references in Section 6.** Line 341 should be: "The paper and code are in [`repos/flash-moe`](../repo-notes/flash-moe.md)." Line 349-352 should link to [`repos/autoresearch-mlx`](../repo-notes/autoresearch-mlx.md).

7. **Source the FUNGI framework (line 276).** If it's from a paper or specific source, add a citation. If it's a synthesis from the community comments, attribute accordingly or move to a supporting synthesis file.

---

## Impact

The synthesis contains high-value architectural guidance and is well-reasoned, but **without citation links, it functions as an opinion piece rather than a grounded reference.** For a knowledge base that treats traceability as a first-class principle, this is a critical gap. The missing KB_DESIGN_PATTERNS.md file in particular blocks the entire "Patterns" section (Section 5) — readers cannot verify the twelve patterns or know their original source within the community discussions.

Estimated effort: 2–3 hours to add markdown links throughout, 4–6 hours to create/locate KB_DESIGN_PATTERNS.md and COMMUNITY_INSIGHTS.md if they must be synthesized from scratch.
