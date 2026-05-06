# OptimusKG (`mims-harvard/OptimusKG`)

## 1. Purpose and scope

OptimusKG is a production knowledge-graph construction pipeline for biomedical science, built at Harvard Medical School's Zitnik Lab. It integrates 65 heterogeneous data sources (OpenTargets, DrugBank, BGEE, DisGeNET, CTD, Reactome, etc.) through BioCypher and the Biolink Model into a unified knowledge graph: 190k nodes across 10 entity types, 21.8M edges across 27 relation types, 67M property instances. Relevance to Linus: OptimusKG is the most mature, reproducible knowledge-graph-as-data-pipeline reference in the research ecosystem, and demonstrates the infrastructure Dan will need for Phase 4 (Data Sovereignty) and Phase 3 (Knowledge & Parallel Agents).

## 2. Architecture summary

Built on Kedro (workflow orchestration), follows medallion architecture (landing → bronze → silver → gold). Bronze extracts and standardizes raw data from external sources (each source is a separate node, outputs Parquet). Silver consolidates entities across sources into unified node tables (Gene, Drug, Disease, Protein, etc.) and builds relationship edges. Gold exports via BioCypher in multiple formats (Parquet, Neo4j JSONL). All datasets defined in YAML catalog with schema, checksum, and origin metadata. Polars for all transformations (not Pandas). Custom runners (FixedParallelRunner, DryRunner) and hooks (ChecksumHooks, QualityChecksHooks, OriginHooks) manage parallelism, validation, and auto-download. Validated independently with PaperQA3. Uses `uv` for package management, pre-commit for CI.

## 3. What's reusable in Linus

The medallion architecture (raw → standardized → consolidated → export) is the standard pattern for any knowledge pipeline. The catalog-first design (YAML definitions of all data flows) is elegant and enables reuse: catalog entries specify schema, storage location, checksums, and origin. The hook system (pre-execution, validation, error recovery) is a mature pattern Linus should adopt at Phase 3+ for KnowledgeBase v1. The Polars-based transformation layer (not Pandas) aligns with Linus's Python 3.12 stack. Custom runners for parallelism and dry-run validation are directly applicable. The reproducibility story (deterministic, infrastructure-agnostic) is worth emulating.

## 4. What's inspiration only

The BioCypher + Biolink Model ontology alignment is specialized to biomedical knowledge and not directly reusable for Linus's knowledge base (which will mix papers, notes, corpora, tools). However, the pattern of "ontology-harmonized consolidation" is useful: Linus KnowledgeBase v1 should consider how to unify schemas across heterogeneous sources (papers via PDF extraction, notes via Markdown, genomics databases via BioCypher, etc.). The PaperQA3 validation approach (agentic QA over the graph) is instructive for Phase 4's data sovereignty validation.

## 5. What's incompatible or out of scope

OptimusKG is narrowly focused on biomedical knowledge (genes, drugs, diseases, pathways, anatomy). Its heavy reliance on external data sources (OpenTargets, DrugBank, etc.) and license compatibility checking is orthogonal to Linus's personal-knowledge-base focus. The Neo4j JSONL export is useful but not mandatory; Linus may prefer in-RAM or PostgreSQL for Phase 2/3. The 65-source integration is industrial scale; Linus Phase 3 will start with 5–10 sources (papers, Dan's notes, bioinformatics tools, genomics DBs).

## 6. Recommendation: **Study (Phase 3–4)**

Not for direct adoption, but foundational reference for Linus Phase 3 (Knowledge & Parallel Agents) and Phase 4 (Data Sovereignty). The medallion architecture and catalog-first design should inform Linus KnowledgeBase v1's structure. OptimusKG's reproducibility and validation stories are worth implementing at Phase 3. The codebase is also a model of good Kedro practice: high-quality CI, clear separation of concerns, extensive documentation.

## 7. Questions for Dan

- **Medallion vs. simpler KnowledgeBase design.** OptimusKG's 4-layer medallion (landing, bronze, silver, gold) is robust for 65 sources. For Linus Phase 3 (10–15 initial sources), is a 3-layer design (raw, standardized, enriched) sufficient, or should Linus adopt the full medallion from the start?
- **Polars + Parquet as Linus data substrate.** OptimusKG uses Polars DataFrames and Parquet export. Should Linus adopt the same stack for KnowledgeBase v1, or defer to PostgreSQL/SQLite for semantic search?
- **Catalog-first design for Linus tools.** OptimusKG catalogs all datasets in YAML. Should Linus adopt a similar approach for tool registry (tools as "datasets" with schema, metadata, versioning) at Phase 2, or keep tools and knowledge separate?
- **Validation + reproducibility.** OptimusKG uses checksums, schema validation, and PaperQA3 for human-in-the-loop QA. Which of these should Linus adopt at Phase 3 for knowledge integrity?
