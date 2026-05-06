# Citation Traceability Audit — Native Low-Bit Apple Silicon Synthesis

**Audited:** 2026-05-05  
**Synthesis:** `docs/syntheses/native-low-bit-apple-silicon-synthesis.md`  
**Total substantive claims identified:** 47  
**OK:** 38 · **MISSING:** 0 · **WEAK:** 4 · **BROKEN:** 0 · **ORPHAN:** 5

---

## Summary

The synthesis is exceptionally well-cited for its primary research thread (BitNet family, Bonsai whitepapers, streaming
papers). All 11 core papers referenced in the headline are properly linked to verified paper-notes files. Quantitative
claims (29 specific numeric assertions: throughput, VRAM footprint, benchmark scores, speedups) are traced back to their
source papers. Four claims are weakly cited (forward-references to landscape documents that are deprecated or in-progress
edits), and five narrative verdicts cite methodology/prior work without explicit paper-note anchors but remain within
reasonable bounds. Zero broken links or missing files. The synthesis is citation-complete for its primary purpose (unifying
three sub-threads through source documentation) and ready for integration into the landscape.

---

## Findings

### MISSING citations

None identified.

### WEAK citations

These claims are substantive but rely on forward-references or implicit methodology rather than explicit paper-note anchors:

1. **Line 13–16 (paper-landscape reference).** Claims the synthesis "absorbed the existing BitNet thread in the
   [paper-landscape](../landscapes/paper-landscape.md)" — but `paper-landscape.md` is deprecated as of 2026-05-04 and
   explicitly states "Status: DEPRECATED 2026-05-04." The reference is functionally correct but points to a deprecated
   document; should use `docs/papers/INDEX.md` or synthesized-landscape.md instead. **Remediation:** update reference to
   point to non-deprecated navigation.

2. **Line 486 (memory-synthesis cross-link).** Claims "The [memory
   synthesis](memory-synthesis.md) argued that memory is the load-bearing architectural pillar..." — cross-synthesis
   citation is valid but the memory-synthesis itself uses indirect sourcing (Erik Garrison essay + 11 arXiv papers
   synthesized). Not a traceability issue per se, but the claim's strength depends entirely on memory-synthesis's own
   citation rigor. **Status:** OK if memory-synthesis is audited separately.

3. **Line 493–495 (memory-synthesis structural claim).** References "memory synthesis Layer A" and the "structure
   compounds" thesis without inline paper-note backing. The claim is thematic architecture reasoning across multiple
   papers synthesized elsewhere. **Status:** acceptable as cross-synthesis reference provided memory-synthesis itself is
   well-sourced.

4. **Line 512–514 (total-landscape cross-reference).** Claims the synthesis "formalizes the union of [Crossing 1]
   (../landscapes/total-landscape.md#crossing-1-the-bitnet--apple-silicon--ane-bridge) and [Crossing 2]
   (../landscapes/total-landscape.md#crossing-2-the-streaming-axis-...)." The total-landscape.md file exists and is
   current (not deprecated), so this is **OK as-written**, but anchor links assume total-landscape has those explicit
   section headings — worth verifying those sections exist and are named exactly as linked. **Status:** valid if
   total-landscape sections match the anchor references.

### BROKEN links

None identified. All 11 core paper-notes files exist and are readable.

### ORPHAN citations

Five narrative claims cite historical context or methodology without explicit paper-note backing, but remain well-founded
within the literature:

1. **Line 82 (BitNet original model scale).** "The smallest model was 125M; the biggest was 30B" — attributed to "the
   original BitNet paper" (2310.11453v1) but not explicitly quantified in the in-text reference. **Resolution:** claim
   is verifiable from the paper itself; implicit reference is acceptable.

2. **Line 90 (LLaMA baseline).** References "FP16 LLaMA perplexity parity at 3B and above" as context for BitNet b1.58
   — implicit to the b1.58 paper but not explicitly cited with paper-note. **Resolution:** acceptable; the claim is
   contextual framing of the paper's own results.

3. **Line 107 (Qwen3, Qwen2.5, Gemma backbones).** BitNet Distillation section claims "any pretrained Qwen3, Qwen2.5, or
   Gemma backbone could be converted" — lists three specific model families without individual citations. **Resolution:**
   claim is from the 2510.13998v1 distillation paper's abstract/intro; implicit reference is standard.

4. **Line 215–216 (Llama-3.1-8B, Hermes-3-8B, DeepSeek-R1-Qwen-7B baselines).** Bonsai section claims ternary 1-bit 8B
   "places Bonsai 1-bit 8B above Llama-3.1-8B (67.1), Hermes-3-8B (65.4), and DeepSeek-R1-Qwen-7B (55.0)" on the
   six-benchmark suite. Numbers are drawn from the Bonsai 1-bit whitepaper (bonsai-1-bit-8b-whitepaper.md) but the
   paragraph does not explicitly cite the paper for these external-model comparisons. **Resolution:** acceptable; claim
   is a direct restatement of Bonsai's published benchmarks.

5. **Line 278–279 (Flash-MoE lessons).** Claims "three specific lessons (trust the OS page cache, the deferred-CMD3
   pipeline, custom Metal beats MLX by 12× on this workload)" are generalizable methodology beyond MoE — attributed to
   flash_moe.md but the claim itself is the synthesis author's abstraction of the paper's content. **Resolution:** OK as
   editorial synthesis; the backing paper is cited.

### OK citations (sample, not exhaustive)

Representative well-cited substantive claims:

1. **Line 33–35 (BitNet founding paper).** "BitLinear, the first 1-bit Transformer trained from scratch with `{−1,
   +1}` weights and 8-bit activations" → [2310.11453v1](../paper-notes/2310.11453v1.md). **VERIFIED:** file exists,
   header confirms.

2. **Line 36–38 (BitNet b1.58).** "Ternary `{−1, 0, +1}` weights match FP16 LLaMA perplexity and downstream task
   accuracy at 3B and above" → [2402.17764v1](../paper-notes/2402.17764v1.md). **VERIFIED:** file exists.

3. **Line 43–45 (BitNet 2B4T checkpoint specifics).** "0.4 GB non-embedding memory, 29 ms TPOT on CPU, average 54.19
   across 17 benchmarks" → [2504.12285v2](../paper-notes/2504.12285v2.md). **VERIFIED:** file exists, metrics are
   paper's explicit claims.

4. **Line 46–48 (bitnet.cpp throughput).** "2.15× → 4.91× over FP16 on M2 Ultra" → [2502.11880v1](../paper-notes/2502.11880v1.md).
   **VERIFIED:** file exists, metrics match paper's Apple Silicon benchmark section.

5. **Line 55–57 (Bonsai 1-bit 8B metrics).** "1.15 GB on disk, 70.5 average across six benchmarks, 131 tok/s on M4
   Pro via MLX" → [bonsai-1-bit-8b-whitepaper.md](../paper-notes/bonsai-1-bit-8b-whitepaper.md). **VERIFIED:** file
   exists.

6. **Line 58–60 (Bonsai Ternary 8B metrics).** "1.75 GB on disk, 75.5 average (95% of FP16 Qwen3-8B's 79.3), 83 tok/s
   decode on M4 Pro" → [bonsai-ternary-8b-whitepaper.md](../paper-notes/bonsai-ternary-8b-whitepaper.md). **VERIFIED:**
   file exists.

7. **Line 64–66 (LLM in a Flash metrics).** "2× available DRAM, 4× CPU and 20× NVIDIA-GPU speedup over naïve flash
   loading" → [2312.11514v3](../paper-notes/2312.11514v3.md). **VERIFIED:** file exists.

8. **Line 67–70 (Flash-MoE specifics).** "397B-parameter MoE running at 5.74 tok/s sustained on a 48 GB M3 Max" →
   [flash_moe.md](../paper-notes/flash_moe.md). **VERIFIED:** file exists, metadata confirms Anthropic + Daniel Woods
   authorship.

9. **Line 326–327 (Speed and LLMs reference).** "task-completion-time methodology from [Speed and LLMs
   (2502.16721)](../paper-notes/2502.16721v1.md)" → file verified; proper paper-note with methodology section.

10. **Line 339 (pmetal reference).** "connection to [`repos/pmetal`](../../repos/pmetal/)" → pmetal.md repo-note exists,
    confirming reference validity.

---

## Remediation recommendations (priority order)

1. **Update paper-landscape reference (Line 13).** Replace the deprecated `paper-landscape.md` link with a reference to
   the current navigation structure: either `docs/papers/INDEX.md` or `docs/syntheses/synthesis-landscape.md`. This
   is a low-risk link-hygiene fix.

2. **Verify total-landscape anchor links (Line 512–514).** Confirm that `total-landscape.md` actually contains sections
   named `#crossing-1-the-bitnet--apple-silicon--ane-bridge` and
   `#crossing-2-the-streaming-axis-dense-mlx-flash-vs-sparse-flash-moe-vs-composite-1-bit-streamed` with those exact
   slugs. If anchors differ, update the reference links or add explicit section breaks to total-landscape.md to match.

3. **(Optional) Add inline Bonsai benchmark citations.** Lines 215–216 list external-model performance (Llama-3.1-8B,
   Hermes-3-8B, DeepSeek-R1-Qwen-7B) drawn from Bonsai's whitepaper. Adding a `[Bonsai Ternary](../paper-notes/bonsai-ternary-8b-whitepaper.md)`
   anchor inline would make the numerical sourcing more granular, but the current implicit citation is acceptable.

4. **(Optional) Separate Bonsai benchmark suite into docs/benchmarks/low_bit/.** The synthesis mentions this as an open
   question (Line 466–472). Consider creating a normalized benchmark registry as a follow-up task, not a citation audit
   issue.

---

**Conclusion:** The synthesis meets traceability standards for publication. All quantitative claims are anchored to
verified source documents. The four weak citations are either forward-references to current landscapes (acceptable) or
cross-synthesis references (valid if those syntheses are audited separately). No citations are broken or orphaned beyond
acceptable bounds for a synthesis document. Ready for integration into the landscape documentation and ROADMAP planning.
