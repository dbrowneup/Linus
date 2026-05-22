# docs/syntheses/

Theme-level digests built by reading across the repo-notes and paper-notes corpus at once. Where individual notes
capture what one source says, syntheses capture what the corpus says about a topic — what positions converge, where
they diverge, which design moves are well-supported across multiple sources, and where the open questions live.

## Two tiers

**15 thematic syntheses** (flat files at this directory's root) — each owns one topic that crosses many sources:

- `agentic-systems-synthesis.md` — agent loops, planners, harnesses, dispatch
- `biological-foundation-models-synthesis.md` — DNA / protein / cell foundation models
- `entrepreneurship-synthesis.md` — commercial surface + startup posture for Linus-derived products
- `function-annotation-discovery-synthesis.md` — protein-function prediction and annotation
- `generative-biology-synthesis.md` — generative design (proteins, BGCs, etc.)
- `humans-teams-performance-synthesis.md` — humans + teams + performance literature
- `infra-foundations-synthesis.md` — benchmarks, methodology, evaluation philosophy
- `llm-hardware-design-synthesis.md` — LLM workloads and the hardware they run on
- `llm-wiki-synthesis.md` — knowledge-base + wiki patterns for LLM consumption
- `llms-in-science-synthesis.md` — Marelli-style methodology for LLMs in scientific work
- `memory-synthesis.md` — the five-layer memory pillar (DEC-0028) and its sources
- `native-low-bit-apple-silicon-synthesis.md` — sub-4-bit inference on Apple Silicon
- `safety-alignment-privacy-synthesis.md` — values, mirroring, value-frame, leakage
- `security-synthesis.md` — security surface of Linus + reveal threats
- `skills-and-practices-synthesis.md` — skill formats, fan-out patterns, autonomy posture

**12 cluster syntheses** under [`repo-clusters/`](repo-clusters/) (`g1–g12`) — each owns one repo-cluster produced during
the 2026-05-04 fan-out: `g1-apple-silicon`, `g2-wiki-engines`, `g3-wiki-patterns`, `g4-memory`, `g5-graph-tools`,
`g6-mcp-tools`, `g7-harnesses`, `g8-sci-agents`, `g9-bio`, `g10-finance`, `g11-agent-frameworks`, `g12-llm-hardware-design`.

## Convention

Per CLAUDE.md doc-type conventions, every synthesis ends with `## References` listing the repo-notes and paper-notes it
cites. New syntheses are typically born from a fan-out (a sub-agent per source cluster) and consolidated by Maestro;
the [`../landscapes/`](../landscapes/) docs roll these up across themes.

## Where to start

[`../landscapes/total-landscape.md`](../landscapes/total-landscape.md) is the integrated view across all 27 syntheses
and is the right entry point if you want one document. For a single topic, jump into the relevant `*-synthesis.md`
file above.
