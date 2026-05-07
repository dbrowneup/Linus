# paper-qa Substrate Integration

**Date:** 2026-05-06 **Status:** proposed **Phase:** 2c **Related ADR:** DEC-0044

---

## Goal

Define the integration contract between paper-qa (FutureHouse, Apache 2.0) and the Linus KnowledgeBase so that Phase
2c delivers citation-grounded paper-corpus question answering without duplicating the retrieval and synthesis machinery
that paper-qa already provides. The adoption pattern is "adopt + extend," not fork or rewrite.

---

## Adoption scope

paper-qa wraps KnowledgeBase's existing paper corpus as the retrieval-and-synthesis layer. It does not replace the RDF
substrate (`linus.knowledge.sparql.*`) or the property graph substrate (`linus.knowledge.graph.*`) defined in DEC-0015;
those substrates handle ontology-aligned structured queries. paper-qa handles the unstructured question-and-answer
surface: given a natural-language question, find the relevant passages across Dan's paper collection, re-rank them with
an LLM, and produce a citation-grounded answer. The two surfaces are complementary. A query that needs SPARQL — "give
me all papers where the subject entity is annotated with GO:0006412" — routes to the graph substrate. A query that
needs synthesis across prose — "what does the literature say about _B. braunii_ lipid productivity under nitrogen
limitation?" — routes to paper-qa.

---

## Integration points

paper-qa reads PDFs from `context/papers/` and the KB paper store directly. It builds and maintains its own tantivy
full-text index and embedding store (sentence-transformer `st-multi-qa-MiniLM-L6-cos-v1`, Apple-Silicon-compatible, no
API key required) alongside the KB's existing RDF and graph stores. The two index types coexist in the same
`context/papers/` tree; there is no duplication of the underlying PDF files.

The Linus orchestration layer routes KB-synthesis queries to paper-qa via the `linus.knowledge.paperqa.*` tool family
(Phase 2c). The tool family wraps paper-qa's four core tools — `PaperSearch`, `GatherEvidence`, `GenerateAnswer`, and
`Complete`/`Reset` — as Linus-registered MCP tools. All LLM I/O goes through paper-qa's LiteLLM adapter, configured to
hit Ollama at `http://localhost:11434`, so no hosted API is required for operation.

paper-qa outputs citation-grounded answers: each answer includes the paper identifiers, page references, and passage
excerpts that support it. These citation objects map directly to the KB's provenance model (DEC-0023).

---

## Claim-typing layer

paper-qa's citation grounding maps to Linus claim types as follows:

- A passage retrieved from an indexed paper and cited in the answer is `[!source]` — a direct claim from a primary
  document with an explicit reference.
- A synthesis inference that paper-qa's `GenerateAnswer` step produces by reasoning across multiple retrieved passages,
  without a single sentence in the corpus asserting it directly, is `[!analysis]` — model-mediated inference grounded
  in sources but not verbatim from them.
- A gap acknowledged in the answer — "the literature does not address this" or "the retrieved papers do not resolve
  this question" — is `[!gap]`.

These tags are applied by the Linus integration wrapper, not by paper-qa itself. The wrapper inspects the
`GenerateAnswer` output, parses citation presence, and annotates accordingly before the answer enters the session
scratchpad or KB.

---

## LAB-Bench canary enforcement hook

Before any paper enters the paper-qa corpus (i.e., before `PaperSearch` indexes it or `GatherEvidence` embeds it), the
ingest preflight step runs a substring scan against every entry in `docs/specs/kb/canaries.yaml`. This is the same scan
described in `canary-blocklist.md`. A match blocks ingestion and logs to `raw/FILTERED.md`; the paper does not enter
the paper-qa index.

The enforcement hook applies to the paper-qa corpus independently of the broader KB ingest pipeline. Even if a file
bypasses the main KB ingest (for example, by being added directly to the paper-qa directory rather than through the
standard ingest path), the paper-qa wrapper checks the blocklist before indexing.

---

## Worker floor

The minimum Worker for paper-qa synthesis tasks is Qwen3-14B. paper-qa's documentation explicitly warns that 7B models
perform poorly on the multi-hop, nested instruction-following tasks that `GatherEvidence` and `GenerateAnswer` require.
Dispatching paper-qa queries to a smaller Worker is non-conformant and will produce degraded citation quality. The
Linus tool registry entry for `linus.knowledge.paperqa.*` must encode this floor as a capability requirement so the
router rejects dispatch to undersized Workers.

---

## Aviary dependency note

paper-qa is built on FutureHouse's aviary framework (`fhaviary`). Adopting paper-qa as the Phase 2c retrieval engine
does NOT commit Linus to FutureHouse's `ldp` policy-training framework. `ldp` is the obvious Phase 6 candidate for
fine-tuning the tool-selection policy inside paper-qa's `ToolSelector` agent, but that is a separate decision deferred
to Phase 6. Through Phase 5, paper-qa's bundled `ToolSelector` is sufficient. The aviary runtime dependency is
acceptable; the ldp training dependency is explicitly not pulled in until a fine-tuning spike validates the benefit.

---

## Phase sequencing

Phase 2c delivers the smoke-test integration: five-paper sample from `context/papers/`, embedding configured,
`pqa ask` validated against a known biochemistry question, tok/s and answer quality logged. If the smoke gate passes,
paper-qa is exposed as a Linus MCP tool and added to the Phase 1e Maestro/Worker loop as the "look it up in Dan's
papers" capability.

Phase 3 replaces KnowledgeBase's ad-hoc retrieval layer with paper-qa's tantivy index and RCS pipeline, keeping
KnowledgeBase as the corpus-of-record and paper-qa as the query engine. At that point the `linus.knowledge.paperqa.*`
and `linus.knowledge.sparql.*` tool families are unified under a single KB gateway that routes by query type.
