## DEC-0015 — KnowledgeBase data model: dual approach (RDF + property graph)

**Date:** 2026-05-03 **Status:** accepted

**Context.** KnowledgeBase needed a graph data model commitment before Phase 2's KB schema hardens. RDF (Semantic Web
stack: rdflib, SPARQL, SHACL, ontology alignment via GO/MeSH/ChEBI per the KGRank Phase 3 path) and property graph
(richer edge attributes, simpler mental model, performant traversal) both have legitimate fit. Inspection of the
KnowledgeBase submodule shows both `rdflib` and `networkx` already declared as dependencies, with `graph.py` and
`knowledge_graph.py` as separate modules — the dual-substrate posture is already implicit.

**Decision.** Adopt **both substrates in parallel.** Linus's adapter (`src/linus/knowledge/`) exposes them as separate
tool families (`linus.knowledge.sparql.*` for RDF; `linus.knowledge.graph.*` for property). Embedded stores: rdflib
(with optional Oxigraph backend if SPARQL performance demands) for RDF; networkx for property; Kuzu evaluated later if
scaling demands. Claim typing, content hashing, and the write-back rule are baked into Phase 2 KB schema regardless of
substrate.

**Consequence.** Both Semantic Web and property-graph use cases are first-class. KB submodule can continue developing
both in parallel. Workers and Maestro see both as queryable resources. Workload is larger than committing to one but is
distributed across the dual-developer model (Linus + KnowledgeBase repos in partnership).
