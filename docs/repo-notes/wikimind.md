# wikimind (`manavgup/wikimind`)

## 1. Purpose and scope

WikiMind is a "personal knowledge OS" built around the inversion that distinguishes it from a notes app: the user never
writes; they only feed sources, and an LLM compiles them into a structured, persistent wiki with full source
attribution. It is one of eleven sibling implementations of Andrej Karpathy's "LLM Wiki" pattern in the `repos/`
collection, and it sits at the heaviest, most production-shaped end of that group: a FastAPI gateway on port 7842 backed
by SQLite or Postgres, an ARQ + Redis job queue for async compilation, multi-provider LLM routing (Anthropic, OpenAI,
Google, OpenAI-compatible gateways, Ollama), a React + Vite + TanStack Query frontend, an Electron desktop shell, a
Manifest-V3 Chrome/Firefox clipper extension, OAuth2 multi-user mode, and a full Fly.io deploy pipeline with
staging-then-prod promotion. For Linus, this is squarely a Phase 2 KnowledgeBase-pillar study: it overlaps with what
`modules/KnowledgeBase` already does on Dan's corpus, but with a much wider ingest surface and a wiki-as-output model
rather than a RAG-as-output model.

## 2. Architecture summary

The Python backend lives under `src/wikimind/` and decomposes cleanly: `ingest/` houses one adapter per source type
(`adapters/url.py` using trafilatura, `adapters/pdf.py` delegating to a `docling-serve` sidecar with pymupdf fallback,
`adapters/text.py`, `adapters/youtube.py` using youtube-transcript-api), with `ingest/service.py` routing URLs by
sniffing for `youtube.com`/`youtu.be`, `.pdf` suffixes, or HTML; `engine/` holds the LLM compilation pipeline
(`compiler.py`, `concept_compiler.py`, `qa_agent.py`, `llm_router.py`, `wikilink_resolver.py`, `backlink_enforcer.py`,
`frontmatter_validator.py`, `title_normalizer.py`, plus a `linter/` subpackage), with provider adapters in
`engine/providers/` mirroring the five supported backends; `services/` wraps the engine for the route layer; `jobs/`
runs the ARQ background compiler so HTTP requests stay snappy; `models.py` defines SQLModel tables and Pydantic schemas;
`api/routes/` are deliberately thin. Alembic handles migrations for the Postgres path. The CI under `.github/workflows/`
is unusually thorough — fifteen workflows including separate `deploy.yml`, `e2e.yml`, `nightly.yml`, `codeql.yml`,
`dependency-review.yml`, `extension-publish.yml`, and a doc-sync job that fails the build if `README.md`,
`docs/openapi.yaml`, or the ADR index drift from source.

## 3. What's reusable in Linus

The ingest layer is the most directly liftable piece. `ingest/adapters/youtube.py` plus the routing logic in
`ingest/service.py` give Linus a clean path to absorb YouTube transcripts into the KnowledgeBase pillar — among the
eleven sibling LLM-Wiki implementations, multi-source ingest with a YouTube path is wikimind's most clearly staked claim
(siblings like `link`, `llmwiki`, `llmbase`, and `wikidesk` lean text/URL/PDF, and `synthadoc` and `TheKnowledge` lean
document-centric without YouTube-as-first-class). The `docling-serve` sidecar pattern for PDFs is also worth borrowing:
it keeps a heavy parsing dependency out of the Linus process and matches the "Docker-for-stateless-services" rule in
CLAUDE.md. The provider abstraction in `engine/llm_router.py` + `engine/providers/` — particularly the
auto-enable-by-detected-key behavior and the OpenAI-compatible configurable provider — is a compact reference for how
Linus's orchestration layer can present one routing surface over Ollama plus future pmetal-serve plus, optionally,
hosted APIs. The frontmatter validator, wikilink resolver, and backlink enforcer in `engine/` form a small, vendorable
wiki-integrity toolkit that KnowledgeBase doesn't have.

## 4. What's inspiration only

The deployment story (Fly.io with staging promotion gated on smoke tests, Gunicorn auto-tuned to CPU cores, Docker
Compose with Postgres + Redis + ARQ worker + docling-serve sidecar, OAuth2, JWT-encrypted BYOK key storage in keyring)
is exactly what a hosted multi-tenant SaaS needs and exactly the opposite of what Linus needs. Linus runs on Dan's
MacBook for Dan, period; Phase 2 uses SQLite, no Redis, no Postgres, no Fly. The React + Electron + browser-extension
trifecta is also not Linus's UX surface — Streamlit and eventually openclaw cover the front-end. The interesting
takeaway is methodological: wikimind shows what a serious one-person open- source project's quality bar looks like (ruff
with ~30 rule families, mypy + basedpyright + pylint + pydocstyle

- bandit + vulture + deptry + interrogate, 80% coverage floor, doc-sync rule engine), worth borrowing piecemeal without
  adopting wholesale.

## 5. What's incompatible or out of scope

The wiki-as-product premise is orthogonal to Linus's KnowledgeBase pillar, which is a RAG layer over Dan's papers and
notes — exactly the design wikimind's README explicitly rejects ("**Not** a RAG tool — the wiki is the product, not a
retrieval layer"). Adopting wikimind's compilation model would mean rewriting KnowledgeBase's purpose, not extending it.
The Postgres + Redis + ARQ stack is overbuilt for single-user local use; the SQLite + in-process job path exists in the
codebase but is the secondary mode. Authentication, OAuth2, BYOK encryption, and Fly secrets management are dead weight
on a localhost daemon. The browser extension and Electron shell duplicate front-end surfaces Linus has already chosen
against.

## 6. Recommendation: **Study**

Clone-as-reference is the right disposition. Lift specific patterns into Linus when Phase 2 needs them — the YouTube
ingest adapter, the docling-serve sidecar contract, the provider-router auto-enable logic, the wikilink and backlink
validators — without inheriting the wiki-as-product framing or the multi-tenant deployment surface. Revisit when the
LLM-Wiki sibling group is fully surveyed; if a different sibling has a cleaner ingest layer or a better provider
abstraction, prefer that one. Do not vendor wikimind whole; do not run its server.

## 7. Questions for Dan

1. **Wiki-as-product vs RAG-as-product.** Karpathy's pattern is "LLM compiles consumed sources into a persistent wiki."
   KnowledgeBase today is RAG-as-product. Is there appetite for a wiki-compilation layer on top of KnowledgeBase in
   Phase 3, or does the corpus stay query-only with provenance via citation rather than via compiled articles?
2. **YouTube transcripts.** Is YouTube-as-source actually a Linus use case (lectures, conference talks, podcast
   interviews on biochem topics)? If yes, wikimind's `youtube-transcript-api` adapter is a 1-day lift; if not, drop it
   from the shortlist.
3. **docling-serve sidecar.** KnowledgeBase currently uses pypdf (with the `sys.maxsize` quirk in CLAUDE.md). Is
   upgrading PDF extraction to docling-serve worth a Docker dependency, or stay native with pymupdf/pypdf?
4. **Provider router placement.** wikimind's `llm_router.py` is per-app; Linus's orchestration layer will need the same
   logic at a higher level (one router, many tools and harnesses). Should Linus copy this shape or wait until Phase 2a's
   tool-registry design forces the decision?
5. **Sibling differentiation visibility.** I called out wikimind's YouTube + multi-source ingest + Fly deploy story as
   differentiators against the other ten LLM-Wiki repos, but only on README evidence — the other ten notes don't exist
   yet. Should the curation pass produce a comparison matrix at the end of the group, or trust the per-repo notes to
   converge?
