# Planning Update — Draft (2026-05-01)

A preliminary synthesis of what has changed, what new decisions have been raised, and what
the current plans look like in light of new papers and community research (May 2026 batch).
This document is explicitly a draft — it should be revisited and revised once the open
questions in [top-questions.md](../docs/top-questions.md) have been worked through.

The goal here is not to resolve the questions but to surface their practical consequences:
where existing plan assumptions hold up, where they are stressed by new information, and what
new components belong on the roadmap regardless of how the open questions resolve.

---

## What was added (the five new papers and three synthesis documents)

**AI/ML papers with direct plan implications:**

[2502.16721v1](paper-notes/2502.16721v1.md) — *Speed and LLMs: Not All Is About Tokens per
Second* (Conde et al., UPM, 2025). Demonstrates that tok/s rankings frequently invert
task-completion time rankings across five ~7B models. The planning implication is simple
and immediate: the current plan to use Ollama's tok/s leaderboard for Worker model selection
is wrong as a methodology. `benchmarks/dan_tasks/` needs to be designed around task-completion
time from Phase 1.

[2208.07262v1](paper-notes/2208.07262v1.md) — *RaKUn 2.0* (Škrlj et al., Jožef Stefan
Institute, 2022). A CPU-only, pure-Python keyphrase extractor that processes 14M biomedical
documents in ~40 seconds on hardware comparable to the M1 Max, with statistically
indistinguishable F1 vs. slower alternatives. This closes a gap in the KB ingestion plan:
previously there was no specified method for extracting keyphrases from papers during ingestion.
RaKUn 2.0 is the Phase 2 answer.

[s41019-017-0055-z](paper-notes/s41019-017-0055-z.md) — *KGRank* (Shi et al., CUHK, 2017).
Knowledge-graph-enriched keyphrase extraction using DBpedia entity linking and personalized
PageRank. The Phase 3 upgrade path for ontology-grounded KB node labels — replacing DBpedia
with GO, MeSH, or ChEBI for Dan's biomedical corpus.

**Dan's research domain papers:**

[PIIS0896627324008080](paper-notes/PIIS0896627324008080.md) — *The Unbearable Slowness of
Being* (Zheng & Meister, Caltech, Neuron 2025). Human cognition is capped at ~10 bits/s
regardless of modality; the sensory-to-behavior sifting ratio is Si = 10⁸. This has a direct
architectural implication: parallel Worker fan-out produces zero throughput gain for Dan unless
the Maestro interface sifts outputs to the essential bits before presenting them. The paper
provides a quantitative grounding for the Maestro/Worker split.

[nihms-2096004](paper-notes/nihms-2096004.md) — *The Brain Works at More than 10 bits/s*
(Sauerbrei & Pruszynski, Nat Neurosci 2025). A direct rebuttal: 10 bits/s is a lower bound on
whole-brain throughput, not an upper bound. Unconscious sensorimotor processing (half of all
brain neurons, in the cerebellum) operates far above this. For Linus: Workers handle the
high-bandwidth parallel substrate; Dan+Claude handle the narrow conscious synthesis channel.
The two papers form a productive debate for Dan to engage as a domain expert.

**Synthesis documents (from community threads and security analysis):**

[docs/llm-wiki-synthesis.md](llm-wiki-synthesis.md) — Karpathy LLM Wiki + community insights
+ KB design patterns. 14 core KB design concepts, 20 local-first repos, 8 suggested `repos/`
additions, 9 open questions. The write-back rule and quality-gate-at-ingest pattern are the
highest-ROI immediate disciplines.

[docs/skills-and-practices-synthesis.md](skills-and-practices-synthesis.md) — Claude skills,
collaboration practices, Cline integration, entrepreneurial opportunities. Key findings:
task decomposition and architectural clarity are the scarce Maestro inputs; the Cline →
Ollama → Qwen2.5-Coder 32B path provides a Worker IDE harness immediately.

[docs/security-synthesis.md](security-synthesis.md) — Security posture analysis. Key finding:
`langchain`, `langgraph`, and `haystack-ai` are installed in the linus env for future use but
represent a large unnecessary supply chain surface today.

---

## What has changed in the plans

### 1. A new Tier 0 exists before Phase 1

Security hygiene that should happen now, before Phase 1 recon begins:

- Remove `langchain`, `langgraph`, and `haystack-ai` from `environment.yml`. These packages
  add large transitive dependency trees for zero current functionality. The orchestration logic
  they would eventually provide is Linus's core product.
- Add `requirements-locked.txt` with hash verification (`pip-compile --generate-hashes`).
  This is the technical control that would have stopped a litellm-style attack.
- Document Linus's dependency philosophy in CLAUDE.md: before adding a package, apply The
  Algorithm; prefer small, mature, general-purpose dependencies; treat orchestration logic as
  in-house.

This does not require any architectural decisions and can be done in a single session.

### 2. The benchmarking methodology needs to change from Phase 1

The current plan implicitly relies on Ollama's tok/s leaderboard for Worker model selection.
The Speed and LLMs paper proves this methodology is wrong. Phase 1's benchmark design should
be restructured around task-completion time (wall-clock, three task types: minimal output,
fixed-length, open-ended) rather than tok/s. This does not add scope — it changes the
measurement axis of work that was already planned.

### 3. The KB ingestion pipeline now has a theory-to-implementation path

Previously the KB ingestion plan had no specified keyphrase extraction method. Now it does:
- **Phase 2**: RaKUn 2.0 (`pip install rakun2`, CPU-only, near-linear scaling, validated on
  biomedical corpora). Provides keyphrases for KB node-candidate generation, Qdrant tags, and
  RAG context tagging.
- **Phase 3**: KGRank-style enrichment — link keyterms to domain ontologies (GO, MeSH, ChEBI)
  for semantic graph construction. Substitutes a biomedical ontology for DBpedia; scispaCy for
  CoreNLP.

These are additive to existing plans, not replacements.

### 4. The Phase 2 output interface design has a new explicit constraint

Human review throughput is empirically bounded at ~10 bits/s (approximately 120-160 words/min
of useful information extraction). The Phase 2 Linus chat/summary interface should default to
high-information-density concise outputs rather than verbose generation. Verbose mode should
be opt-in. This is a concrete design requirement derivable from the cognitive throughput papers.

### 5. New question about Phase 2 orchestration scope

The skills/practices synthesis raised a genuine question that was not on the radar before: does
Linus need a custom Phase 2 orchestration layer at all, or would Task Master AI + claude-squad
accomplish the same? The Algorithm says delete before building. This question should be
investigated in Phase 1 recon alongside the inference backend evaluation.

If Task Master AI + claude-squad can satisfy the MVP requirements (task dispatching, Worker
coordination, basic tool registry), then Phase 2 reduces to "wire KB into that infrastructure"
rather than "build an orchestration backend from scratch." This is a significant potential
simplification and deserves a concrete evaluation.

### 6. Community repos now have a prioritized candidate list

The LLM wiki synthesis identified 8 repos worth adding to `repos/` for reference:
`omega-memory`, `keppi`, `rohitg00/agentmemory`, `openaugi`, `qmd`, `the-knowledge`,
`multi-agent-wiki`, `agentic-research-wiki`. The skills synthesis identified `fastmcp`,
`Task Master AI`, and `claude-squad`.

None of these require the existing repos to be modified. Cloning them is additive, low-risk,
and provides reference material for Phase 2-3 design decisions.

### 7. The Cline Worker integration path is now concrete

Configure Cline (already in `repos/cline/`) → Ollama (already running) → Qwen2.5-Coder 32B.
Enable compact prompts setting for local hardware. This is a working Worker IDE harness that
requires no new infrastructure. Phase 1 validation task: one well-specified coding task, one
Cline/Ollama run, measure output quality. If this works, the VS Code Worker path is operational
in Phase 1 rather than Phase 5.

---

## What the roadmap looks like now (preliminary)

**Phase 0 → Phase 1 transition checklist (before Phase 1 begins):**

1. Remove pre-emptive ML framework packages, add lock file (security hygiene)
2. Validate Cline → Ollama → Qwen2.5-Coder 32B Worker path
3. Investigate Task Master AI + claude-squad as potential Phase 2 orchestration alternative
4. Design `benchmarks/dan_tasks/` with task-completion time as primary metric

**Phase 1 (Recon & Baselines) — additions/modifications:**

- Worker model selection benchmark: use task-completion time (3-task schema), not tok/s
- Add Task Master AI + claude-squad evaluation as a Phase 1b parallel to pmetal evaluation
- RaKUn 2.0 smoke test on 20-50 `context/papers/` papers (τ ∈ {0.5, 1.0, 1.5})
- Begin investigating entrepreneurial surface: what would one client engagement look like?

**Phase 2 (Linus MVP) — additions:**

- KB ingestion pipeline includes RaKUn 2.0 keyphrase extraction step
- Maestro interface defaults to concise, high-information-density outputs (~10 bits/s design)
- Dependency philosophy baked into orchestration layer design (no ML framework deps in hot path)
- Prompt injection defense designed into the KB retrieval path (trust tiers: system prompts vs.
  retrieved content)

**Phase 3 (Knowledge & Parallel Agents) — additions:**

- KB ingestion upgrade: KGRank-style ontology-grounded keyphrase enrichment
- Parallel agent write conflict resolution design (write-back rule implementation)
- `omega-memory` and `rohitg00/agentmemory` as reference implementations for KB retrieval

**Phase 6 (Fine-Tuning) — note:**

- Fine-tuning target decision (genomics-specialized vs. coding-specialized) should be made by
  Phase 3, not deferred to Phase 6. This decision changes which entrepreneurial opportunities
  become viable post-fine-tune.

---

## Open questions this document cannot resolve

This draft takes positions on what belongs in the plans regardless of how questions resolve.
But several decisions are genuinely blocked on Dan's answers:

- **Tier 1 #3** (Phase 6 fine-tuning lane) — shapes everything from Phase 3 onward
- **Tier 1 #4** (RDF vs. property graph for KB) — hardens in Phase 2
- **Tier 1 #13 / new** (Task Master AI vs. custom orchestration) — may simplify Phase 2 dramatically
- **New Tier 1 #14** (monetize now vs. build first) — shapes where Maestro time goes in Phase 1
- **Tier 0** (dep cleanup + lock file) — not a question, an action item

This document should be revised after those Tier 0 and Tier 1 questions are resolved. The
revised version should propagate decisions into ROADMAP.md, DECISIONS.md (one ADR per Tier 1
decision), and the relevant per-note "Open questions for Dan" sections as each answer lands.

---

*Draft produced 2026-05-01 from parallel synthesis of 5 new paper notes and 3 community/security
synthesis documents. Treat as preliminary until Tier 1 questions are answered.*
