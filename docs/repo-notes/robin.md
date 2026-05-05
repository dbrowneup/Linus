# robin (`Future-House/robin`)

## 1. Purpose and scope

Robin is FutureHouse's "multi-agent system for automating scientific discovery" — published in arXiv 2505.13400 — and
its actual scope is narrower than the marketing implies but more concrete than most agentic-science demos. The pipeline
takes a single input (a disease name, e.g. `"Friedreich's Ataxia"`) and produces, end-to-end, (a) a ranked list of
proposed in-vitro experimental assays for that disease with detailed hypothesis reports, (b) a ranked list of small-
molecule therapeutic candidates predicted to work in the top assay, and (c) optionally, an analysis pass over actual
flow-cytometry data the user supplies that loops experimental results back into a refined candidate list. The
"end-to-end scientific discovery" framing in the README means precisely this loop: hypothesis → assay design → candidate
proposal → wet-lab data analysis → revised candidates. It does not run wet-lab experiments and does not discover beyond
therapeutics. The `examples/` folder ships full output trajectories for ten diseases (Friedreich's ataxia, CKD,
glaucoma, IPF, NASH, PCOS, sarcopenia, age-related hearing loss, celiac, Charcot-Marie-Tooth) — useful as a concrete
answer to "what does success look like."

## 2. Architecture summary

Three top-level async functions in `robin/__init__.py` form the public API: `experimental_assay`,
`therapeutic_candidates`, and `data_analysis`, all parametrised by a single `RobinConfiguration` Pydantic model. There
is no agent-orchestration framework in the modern sense — Robin is a hand-coded async pipeline of LLM calls and Edison
platform calls strung together with `aviary.core.Message` and `lmi.LiteLLMModel` (the FutureHouse LiteLLM wrapper). Each
pipeline phase is a fixed sequence: generate literature-search queries via the local LLM → dispatch to Edison's `Crow`
agent for paper-QA literature reviews → synthesise proposals via the local LLM → dispatch detailed hypothesis reports to
`Crow` (assays) or `Falcon`/Literature (candidates) → run pairwise tournament ranking via the local LLM with
`choix.ilsr_pairwise` Bradley-Terry inference to pick a winner. Data analysis (`analyses.py`) uses a
`MultiTrajectoryRunner` (`multitrajectory_runner.py`) that ships R/Python code-execution `Step`s to Edison's Crow-high
data-analysis job, with input/output file mapping and a parallel-trajectory consensus pattern. Prompts live in a single
48 KB `prompts.py`, instantiated through a `Prompts` Pydantic model whose validator parses every template's
`{placeholder}` arguments and asserts they match a hard-coded expected set — a clever discipline that catches prompt
drift at construction time and is worth borrowing.

## 3. What's reusable in Linus

Three things travel cleanly. First, the **Bradley-Terry pairwise tournament for ranking LLM outputs**
(`choix.ilsr_ pairwise` over uniformly random pairs from `utils.uniformly_random_pairs`) is a small, self-contained,
frequency- calibrated alternative to LLM-as-judge "rate this 1-10" prompts; for any Linus skill that produces N
candidate artefacts and needs to pick a best one (refactor variants, summary versions, hypothesis ranking against
KnowledgeBase), this pattern transplants in ~50 lines and works against any local model. Second, the **prompt-template
validator** in `Prompts.validate_all_prompts` — extract `{vars}` via regex, compare to declared expectations, fail at
instantiation — is a great convention for Linus's eventual prompt registry; it would have caught half the
prompt-template bugs Dan has hit in KnowledgeBase. Third, the **disease-input → ranked-candidates pipeline shape** is a
reference implementation of a domain-specific scientific skill — a worked example of what a Linus "drug- repurposing"
skill could look like in Phase 7, mapped onto KnowledgeBase as the literature substrate instead of Crow.

Compared to its FutureHouse sibling **paper-qa**, Robin is the orchestration layer _on top of_ paper-qa-style retrieval
(via the Crow agent on Edison) — paper-qa answers "what does the literature say about X?" while Robin chains many such
questions into a hypothesis-generation-and-ranking workflow. If Linus integrates paper-qa locally against KnowledgeBase,
Robin's pipeline shape becomes the natural Phase-7 skill that sits on top.

## 4. What's inspiration only

The end-to-end framing relies critically on the Edison platform: literature search (Crow), detailed hypothesis reports
(Falcon/Literature), and the entire data-analysis loop are remote API calls to a paid FutureHouse service. The
open-source code is the choreography; the substantive scientific reasoning happens behind the Edison API. Without
Edison, the README explicitly states "all the hypothesis and experiment generation code can still be run" — but
"hypothesis and experiment generation" without literature grounding is just an LLM brainstorming session formatted into
CSVs. The interesting parts (the parts that justify the arXiv paper's claims) are paywalled. The pipeline structure is
inspirational; the working Robin implementation is not directly portable to Linus without a KnowledgeBase-backed
substitute for Crow and Falcon.

## 5. What's incompatible or out of scope

Edison API dependency is the headline blocker against the no-paid-APIs north star — `edison-client>=0.11`,
`EDISON_API_KEY` required for the only interesting path, and credit-metered usage. The default LLM is OpenAI's
`o4-mini`; LiteLLM technically allows swapping in Ollama, but every prompt in `prompts.py` was written and tuned for a
frontier reasoning model and the JSON parsing of LLM output (`assays.py` lines 121-128) is fragile enough that local-
model output will need substantial work to parse reliably. The pipeline is also Jupyter-notebook-first
(`robin_demo.ipynb`, `robin_full.ipynb`) — usable as a Python module but not engineered as a library, and the
`robin_output/` directory layout is hard-coded relative to CWD throughout `assays.py` and `candidates.py`. Domain is
narrow (small-molecule therapeutics for human diseases with cell-culture assays); not directly applicable to genomics
analysis or computational biology workflows.

## 6. Recommendation: **Study**

The Edison dependency makes "use Robin in Linus" a non-starter — the substantive agents are paywalled SaaS that exist
specifically to monetise FutureHouse research. But the patterns are worth lifting. Three concrete extractions: (1) port
the `choix`-based pairwise tournament ranker into a Linus utility for Phase 3 candidate-selection use cases; (2) adopt
the `Prompts.validate_all_prompts` regex+expectations pattern when Linus grows a prompt registry in Phase 2b or 3; (3)
use Robin's pipeline as the design template for a future Linus "drug-repurposing" or "hypothesis-generation" skill in
Phase 7, with KnowledgeBase + a local paper-qa replacing Crow/Falcon. Re-evaluate if FutureHouse open-sources weights
for Crow/Falcon or if a credible local literature-QA stack (paper-qa against KnowledgeBase) reaches parity.

## 7. Questions for Dan

- **Pairwise ranker as a Linus primitive.** The `choix.ilsr_pairwise` tournament is a 50-line lift and would let any
  Linus skill that produces N alternatives pick a winner without trusting a single LLM-as-judge call. Want this in the
  Phase 2 utility belt, or wait until a skill needs it?
- **Prompt-validator convention.** Robin's "regex-parse `{placeholders}` and assert against an expected set at model
  construction" pattern would have caught half the KnowledgeBase prompt-template bugs. Worth adopting as a Linus prompt
  convention now, before there are many prompts to retrofit?
- **paper-qa + KnowledgeBase as the local Crow replacement.** Robin's Edison dependence collapses to "we need a
  literature-QA agent." If paper-qa runs locally against KnowledgeBase well enough, Robin's pipeline becomes a
  reasonable Phase 7 skill template. Worth a Phase-1 spike on paper-qa-against-KB to find out?
- **Therapeutics scope.** Robin's domain is small-molecule drug discovery for human disease via cell-culture assays —
  adjacent to but not the same as your genomics/computational-biology focus. Is a Robin-style "hypothesis pipeline"
  skill on Linus actually something you'd use, or is the value purely "study the patterns, build something different"?
- **Tournament ranking vs LLM-as-judge in benchmarks.** The Dan-tasks benchmark suite will need a way to score free-form
  outputs. Pairwise tournament + Bradley-Terry is more expensive but lower variance than rubric scoring. Worth piloting
  on one benchmark task as a methodology test?
