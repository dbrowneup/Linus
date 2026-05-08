# dlt (`dlt-hub/dlt`)

## 1. Purpose and scope

dlt is a mature, production-grade open-source Python library that automates the "extract, normalize, load" (ETL) cycle —
extracting data from REST APIs, SQL databases, cloud storage, and 5000+ verified sources, inferring schemas, handling
nested/messy data, and loading into any destination (DuckDB, Snowflake, BigQuery, etc.). It is designed to be embedded
in user code (Airflow DAGs, Lambda functions, notebooks, scripts), not run as a service. For Linus, dlt addresses the
"reliable, observable data pipeline backbone" problem: loading research corpora, monitoring corpus health, and feeding
KnowledgeBase ingestion. Governance and LLM-native workflows are first-class.

## 2. Architecture summary

dlt is a library with a **pipeline** abstraction: `dlt.pipeline(name, destination)` returns a state-bearing object that
wraps sources, handles incremental loading, schema evolution, and data contracts. Sources are decorated Python functions
(generators or REST-based factories) that yield records or nested data. The library infers schemas from data, normalizes
nested structures into flat tables, and loads via pluggable destinations. Notable features: schema contracts (enforce or
log on breach), incremental loading with state tracking, async/await support, rich CLI for inspection and schema
management. Code is typed (mypy, ruff linting), tested with 100s of test suites, and uses `uv` for fast dependency
resolution.

## 3. What's reusable in Linus

dlt is a direct fit as Linus's ETL backbone for **KnowledgeBase feeding** and **corpus analytics**. Use cases: (1)
periodically fetch Dan's GitHub repos' README/code files and load into DuckDB for RAG context, (2) ingest structured
research datasets (genomics, chemistry databases) with schema contracts to catch corruptions early, (3) load
user-activity logs from Linus into a queryable store for audit + analytics. The incremental-loading pattern
(checkpoint-based state tracking) is valuable for corpus updates without re-processing. The contract system (Pydantic
models defining required fields and types) directly parallels the validation layer Linus will need. No framework
lock-in; pure Python, runs anywhere Python 3.9+ runs.

## 4. What's inspiration only

dlt's **verified sources** library (5000+ pre-built connectors) is impressive but mostly orthogonal to Linus — Dan's
data sources are domain-specific (GitHub, personal papers, local DBs). The Workspace/Hub collaboration features are
SaaS-specific; skip them. The airflow/serverless examples are useful reference for deployment patterns but not directly
applicable until Linus phase 4+.

## 5. What's incompatible or out of scope

dlt is tuned for "load data into a data warehouse" workflows, not for real-time streaming or sub-millisecond latency.
For Phase 2a Linus, that's fine — KB updates are batch/hourly, not live. The library is heavy (many optional
dependencies for all 5000 sources); Linus should `pip install dlt[duckdb]` (minimal) and only add extras (sql_database,
http, parquet) as needed. dlt's "multiply don't add" philosophy means it does a lot; time investment in understanding
pipelines, schema contracts, and state tracking upfront pays off.

## 6. Recommendation: **Study (Phase 2a), Integrate (Phase 2b)**

Use dlt as the Phase 2a research spike: (1) prototype a simple pipeline that loads 10 papers from a local directory into
a DuckDB table, (2) verify schema contracts catch format mismatches, (3) measure init cost and runtime on M1 Max. If
promising, integrate into Phase 2b's KB ingestion as the authoritative ETL layer. The library is stable, well-maintained
(by dlt-hub, with 1000s of production users), and fits Linus's "no paid APIs, local-first" ethos.

## 7. Questions for Dan

1. **DuckDB as Linus's transactional store.** dlt works with many destinations; is DuckDB the plan for Phase 2a's
   metadata + corpus indexing, or is a different store (SQLite, Postgres) preferred?

   _Partially resolved (DEC-0029, see [answered-questions.md](../questions/answered-questions.md)): SQLite is the chosen
   substrate for episodic and session stores; DuckDB not adopted; corpus analytics store TBD at Phase 2b._

2. **Schema contracts rigor.** Should Linus enforce contracts strictly (fail on mismatch) or log warnings? Depends on
   corpus quality assumptions.
3. **Incremental loading strategy.** For KnowledgeBase updates, should Linus re-ingest everything monthly or use dlt's
   state tracking to only process new/changed papers?
4. **Verified sources vs. custom.** Is there any dlt verified source (e.g., GitHub API loader, academic paper database
   connector) that could jumpstart a corpus loader, or build custom from the start?
