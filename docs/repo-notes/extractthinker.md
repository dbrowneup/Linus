# ExtractThinker (`enoch3712/Open-DocLLM`)

## 1. Purpose and scope

ExtractThinker is a Python library for structured document extraction and classification using LLMs. It provides an
ORM-like API: define extraction contracts (Pydantic models), point the library at a document, and get back structured
data (invoice fields, license info, classification labels). Supports multiple document loaders (PyPDF, Tesseract OCR,
Azure Form Recognizer, AWS Textract, Google Document AI) and LLM providers (OpenAI, Anthropic, Ollama, etc.). For Linus,
this is a specialized tool for **knowledge-rich structured extraction from documents**: extracting metadata and field
values from papers, classifying document types, and feeding structured KB records.

## 2. Architecture summary

ExtractThinker's core is the `Extractor` and `Process` classes, which orchestrate: (1) document loading (via pluggable
loaders), (2) optional splitting (lazy or eager, for multi-page documents), (3) classification (matching document
sections to contract templates), and (4) extraction (calling an LLM with the Pydantic contract as schema and getting
back validated data). Contracts are Pydantic v2 models with optional descriptions. Classification uses LLM
decision-making (no training). The library supports batching (extract_batch) and async processing. Integrates with
`instructor` (for structured LLM outputs) and `litellm` (for multi-provider LLM access). Code is typed, tested (pytest),
and uses Poetry for dependency management.

## 3. What's reusable in Linus

ExtractThinker fills a gap that raw markdownify doesn't: **structured extraction + validation**. Use cases: (1) extract
metadata (title, authors, abstract, citations) from academic papers in the KB, (2) classify paper sections (methods,
results, discussion) and extract key findings per section, (3) pull data from tables and figures (via Tesseract + LLM
vision), (4) enforce data contracts via Pydantic (catch malformed or missing fields early). The ORM style (define
schema, call extract(), get back typed objects) is Linus-friendly. Batch processing is useful for monthly KB corpus
updates. Ollama integration is direct (set `API_BASE` env var).

## 4. What's inspiration only

Azure Form Recognizer and AWS Textract support are valuable reference implementations but out of scope for Linus
(cloud-free). The Medium articles (linked in README) are useful case studies of extraction patterns in real documents
(e.g., invoice/driver-license workflows). The LangChain-inspired modular design is a good pattern to follow.

## 5. What's incompatible or out of scope

ExtractThinker relies on LLM vision models (gpt-4o, claude-3.5-sonnet) for table/figure extraction; local Ollama models
vary in OCR quality. For Dan's paper corpus with complex figures and tables, a hybrid approach (Tesseract for OCR text,
LLM for semantic understanding) is needed, but not all document loaders expose this split. The library is not a pipeline
orchestrator; Linus's dlt layer should schedule and monitor extractions. Poetry (dependency manager) is redundant if
Linus stays pure-conda; either way, the library installs cleanly via pip.

## 6. Recommendation: **Study (Phase 2a), Integrate (Phase 2b)**

Use ExtractThinker as Phase 2a research: (1) define 3-5 extraction contracts for Dan's paper corpus (abstract + authors,
methods summary, key results), (2) run on 10 sample papers with local Ollama, (3) measure accuracy (spot-check extracted
fields) and cost (tokens per paper), (4) compare to markdownify-only baseline (raw Markdown vs. structured fields). If
accuracy is acceptable, integrate into KB ingestion pipeline (Phase 2b). Combined with markdownify (convert PDF →
Markdown) and dlt (orchestrate + store), this completes the "document → structured KB record" flow.

## 7. Questions for Dan

1. **OCR quality with local models.** Ollama's Llava or other multi-modal models handle figures/tables in papers less
   gracefully than gpt-4o. Should Linus accept lower extraction accuracy for local-first, or hybrid (Tesseract text +
   local OCR + remote vision as fallback)?
2. **Extraction contract design.** How many contract types (paper metadata, experiment results, chemical structures)
   should Phase 2a start with, and are they reusable across domains (genomics, chemistry, other)?
3. **Batch vs. streaming.** Should KB ingestion extract in batches (100 papers/month) or stream (new papers daily)?
   Cost/quality tradeoff.
4. **Validation layer.** Should failed extractions (missing required fields, confidence low) be quarantined,
   re-attempted with a smarter model, or logged for manual review?

   _Partially resolved (DEC-0019, see [answered-questions.md](../questions/answered-questions.md)): KB ingest quality
   gate is a quality surface, not a hard gate; failed items are logged, not silently dropped; re-attempt policy TBD._
