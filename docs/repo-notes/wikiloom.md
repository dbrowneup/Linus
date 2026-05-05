# wikiloom (`do-y-lee/wikiloom`)

## 1. Purpose and scope

WikiLoom is a Python CLI (`pip install wikiloom`, MIT, alpha at v0.1.7) that turns ingested PDFs / Markdown / URLs into
a persistent, human-readable Markdown wiki under git. It's one of eleven implementations in this collection of Andrej
Karpathy's "LLM wiki" pattern. What sets it apart is a strong opinion on **the wiki as a git working tree**: every
state-mutating CLI command auto-commits with a classifying subject prefix (`ingest:`, `lint:`, `merge:`, `deprecate:`,
`dormant:`, `human-edit:`), so the project's history is the audit log and `git push` is the backup strategy. It is most
directly relevant to Linus's Phase 2 KnowledgeBase work, where the security/LLM-wiki synthesis notes already call out
content-hashing of source chunks and a "write-back as a first-class operation" rule.

## 2. Architecture summary

A single Python package (`wikiloom/`, ~25 modules) wrapping a sequential pipeline: extractors (`pymupdf`, `python-docx`,
`python-pptx`, `trafilatura` for URLs) → chunker → synthesis (LLM via `litellm`, provider-agnostic across Anthropic,
OpenAI, Gemini, Ollama) → linker → backlink graph → index regeneration → git commit. The LLM is fenced to one role: read
a chunk, emit JSON validated against `.wikiloom/output_formats/ ingest_response.json`. Everything downstream of the LLM
call is deterministic. The linker (`wikiloom/linker.py`, ~940 lines) uses spaCy NER + an alias map to score candidate
wikilinks on a 0–100 scale; ≥95 auto-inserts into the body, ≥85 auto-inserts and flags in `backlinks.json`, ≥70 defers
to `pending.json` for human review, below 70 is discarded. Provenance is enforced by `chunk_store.py`: every chunk gets
a stable `chunk_id = sha256(source_hash + chunk_index)[:12]`, and every page's `sources` frontmatter array carries the
`chunk_ids` it derives from, so any claim is one CLI hop (`wikiloom source <chunk_id>`) from the exact text the LLM saw.
Human edits are protected twice — by a `human-edit:` commit prefix that auto-tools respect, and by a durable
`<!-- wikiloom:auto -->` marker in the page body that survives even `wikiloom ingest --force`. State that lives outside
git: a SQLite cache (`_registry/wiki.db`, WAL mode) holding the chunks table, page registry, and per-page embedding
matrix used for process-cached `(M, D)` matmul-based semantic search; embeddings default to local `fastembed` (~66 MB,
BGE-small). A pre-flight token-cost estimator refuses ingest runs that would exceed `monthly_budget_usd`.

## 3. What's reusable in Linus

The chunk-id construction is directly adoptable for the Phase 2 KB schema. Linus's synthesis notes already settled on
content-hashing source chunks; WikiLoom's `sha256(source_hash + chunk_index)[:12]` truncation, with the noted
collision-risk math (negligible below ~10M chunks per source), is a clean reference implementation that interoperates
with re-ingest because the same source produces the same ids. The tiered-confidence linker output —
auto/flagged/pending/discarded with an externalized `pending.json` queue — is a better mechanical model for KB-side
entity resolution than a single-threshold cutoff, and it generalizes cleanly to whatever entity types Linus's KB ends up
with. The two-layer human-edit protection (commit-prefix soft + auto-region marker hard) addresses the write-back rule
from the synthesis notes more carefully than most siblings: among the eleven, this is the one that most clearly
distinguishes "the LLM wrote this" from "Dan wrote this" in a way that survives re-synthesis. The provider-agnostic
`litellm` routing means Linus can wire WikiLoom (or a wikiloom-shaped library) to its own OpenAI-compatible endpoint in
Phase 2a with no fork.

Versus the named siblings: `wikiloom`'s git-as-substrate posture is its sharpest knife. `link` and `wikidesk`, by
contrast, treat git (if at all) as an external concern; `llmwiki-cli` and `llmbase` lean on databases or vector stores
as the canonical state. The structural-provenance chain (chunk_id in frontmatter → SQLite chunks table → exact LLM
input) appears to be more rigorously enforced here than in the other Markdown-first siblings, but this needs
cross-checking against `TheKnowledge` and `wikimind` which the README claims similar territory for. The
deterministic-linking story (spaCy NER + alias map + tiered confidence) is concrete and inspectable code rather than a
README assertion, which makes it a defensible reference even where Linus chooses a different scoring rule.

## 4. What's inspiration only

The CLI itself (26 commands across project lifecycle / ingest / read / page lifecycle / maintenance / observability) is
more breadth than Linus needs in Phase 2 — Linus's KB is consumed by the orchestration layer, not driven by a human at a
shell. The dormant/deprecate/purge lifecycle is thoughtful but specific to a personal-knowledge-management use case
where pages age out; the Linus KB is closer to a research corpus where staleness is judged differently. The litellm
dependency, while convenient, is heavy and adds a layer Linus doesn't strictly need given Ollama and pmetal already
speak OpenAI-compat. The duplicate-detection + interactive-merge UX is nice but probably overkill for a backend.

## 5. What's incompatible or out of scope

WikiLoom assumes a single Markdown wiki tree with one git history per project. Linus's KnowledgeBase is a submodule with
its own repo and its own write semantics — wikiloom-as-a-library would have to be reshaped to write into a foreign repo,
or its commit machinery would have to be bypassed, defeating most of the design's point. The spaCy `en_core_web_sm`
dependency is fine but adds ~50 MB and a cold-start cost; for batch ingest it's amortized, for interactive query it's
noticeable. fastembed (`onnxruntime`-backed BGE-small) is CPU-only and won't exploit the M1 Max GPU/ANE — Linus would
want to swap in an MLX or pmetal-backed embedder if WikiLoom code is adopted. Python 3.10 floor is older than the linus
env's 3.12 but not a blocker.

## 6. Recommendation: **Study**

Treat WikiLoom as the canonical reference for "git-as-substrate Markdown KB with deterministic linking" while the Phase
2 KB schema is being designed. Specifically: (a) lift the `chunk_id` derivation into the KB design doc as the
content-hashing convention; (b) lift the tiered-confidence linker model as the prior art for entity resolution; (c) lift
the two-layer human-edit protection (commit prefix + auto-region marker) as the write-back-rule reference
implementation. Do not vendor or depend on the package — the CLI surface, dormant lifecycle, litellm dependency, and
"one wiki = one git repo" assumption don't fit Linus's submodule-based KnowledgeBase architecture. Revisit in Phase 3 or
Phase 7 if a Linus skill needs a personal-Markdown-KB front-end and wikiloom-as-an-app is a faster route than building
one.

## 7. Questions for Dan

- **Chunk-id convention.** Are you ready to commit the Phase 2 KB schema to `sha256(source_hash + chunk_index)[:N]`
  truncated chunk ids, or do you want full-length hashes everywhere for zero-collision peace of mind? WikiLoom uses 12
  hex chars (48 bits); the KB might have orders of magnitude more chunks long-term.
- **Write-back protection model.** Does the KB need an auto-region marker (durable, survives re-synthesis) plus a
  commit-prefix flag (soft, cleared by next auto-action), or is one of the two layers enough for our use case? The
  marker is more invasive on page bodies; the prefix is invisible but easier to lose.
- **Linker confidence tiers.** WikiLoom's 95 / 85 / 70 cutoffs come from PKM heuristics. For a research KB linking
  scientific entities, the prior is different. Do we want to start from these defaults and tune, or design our own
  scoring scale from scratch?
- **Cross-sibling check.** I claimed the deterministic-linking + structural-provenance combo is sharpest in WikiLoom
  across the eleven. That claim should be re-verified against `TheKnowledge` and `wikimind` notes when those are written
  — flag this as a follow-up so the differentiation list stays honest.
- **Git-as-substrate scope.** Is the Linus orchestration log itself a candidate for the same "auto-commit with
  classifying prefix" pattern, separate from the KB? It's a clean audit trail, but it does mean every Linus session that
  touches state writes commits.
