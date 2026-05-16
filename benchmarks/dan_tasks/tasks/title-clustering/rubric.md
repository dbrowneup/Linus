# Rubric — Title clustering

## Task

Cluster 50 paper titles into 5 named topical groups. Every title assigned to exactly one cluster. Output as Markdown
with `## Cluster N: <name>` headings followed by bulleted title lists.

## What counts as success (full credit)

1. **Exactly 5 clusters.** Not 4, not 6, not 7.
2. **Coverage = 50.** Every input title appears in some cluster, with no duplicates across clusters.
3. **Format compliance.** Output uses `## Cluster N: <name>` headings followed by bulleted lists. Cluster names
   are 3-7 words, descriptive (not "Cluster A" or "Group 1").
4. **Coherent groupings.** Titles within a cluster share a recognizable topical signal — at least 4 of 5 clusters
   should be defensibly named on a quick human read. Examples of strong clusters lurking in this 50:
   - Bio foundation models / protein language models / function prediction (~10 titles)
   - Transformer architecture primitives (RoFormer, RMSNorm, GQA, GLU, FineWeb, Llama 3, ...) (~10 titles)
   - Low-bit / efficient inference (BitNet variants, LLM-in-a-Flash, the 1.58-bit era) (~5 titles)
   - Reasoning + chain-of-thought + memory (Zero-Shot Reasoners, COCONUT, ARC Prize, TTT, Memory Makes
     Computation Universal, MemGPT-adjacent) (~7 titles)
   - LLM-driven hardware/code generation (QiMeng-GEMM, CodeV, AutoOS, Automated CPU Design, ...) (~5 titles)
   - Multi-agent / trading systems (TradingAgents, QuantAgent, ...) (~2-3 titles)
   - Misc/uncovered (Curse of Dimensionality, Knowledge Graphs, video Space-Time Attention) (~3-5 titles)

   The grader does NOT enforce a specific clustering — any defensible 5-way partition that covers all titles is
   valid. Mixing the bio-FM titles with general transformer architecture is the canonical failure mode.

## Partial credit

- 5 clusters but coverage off (45/50 titles assigned, or one title appears twice) → **partial**.
- 4 or 6 clusters but otherwise coherent → **partial**.
- Cluster names are present but generic ("Group A", "Topic 1") → **partial**.
- 5 clusters with coverage 50 but ONE cluster is incoherent (e.g., mixes bio FMs with hardware/code-gen) → **partial**.

## Failure

- Fewer than 4 or more than 7 clusters.
- Coverage below 40/50 titles.
- All titles in one cluster.
- Output is prose paragraphs without identifiable cluster structure.
- Refusal or empty output.
- Hallucinated titles (titles the model invented that were not in the input list).

## Notes for the grader

The grader extracts each `## Cluster ...` heading and the bullets beneath it. Title matching tolerates minor
whitespace/punctuation variation but flags substantive rewrites. Coverage = unique-titles-assigned / 50.
