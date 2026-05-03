# Linus — Decisions Log (ADR)

An append-only log of significant architectural, product, and process decisions. Each
entry has an id, date, context, decision, and consequence. Inspired by the ADR pattern
(see https://adr.github.io/). When this file exceeds ~20 entries, graduate to per-file
ADRs in `docs/adr/NNNN-title.md`.

## Format

```
## DEC-NNNN — <short title>

**Date:** YYYY-MM-DD
**Status:** proposed | accepted | deprecated | superseded by DEC-MMMM

**Context.** Why is this decision being made? What's the forcing function?

**Decision.** What are we doing? Be specific.

**Consequence.** What does this enable? What does it foreclose? What's the reversal cost?
```

---

## DEC-0001 — Project name and namesake

**Date:** 2026-04-22
**Status:** accepted

**Context.** The project needed a name that reflects its character — local, open,
principled, cross-domain, long-horizon — and that would sit well as a daily companion.

**Decision.** The project is named **Linus** after both Linus Pauling (biochemist,
humanitarian, Oregonian, basement-lab hacker turned two-time Nobel laureate) and Linus
Torvalds (engineer, open-source advocate, Oregonian). The logo will be a carbon atom,
reflecting Pauling's foundational work on carbon chemistry, the role of carbon in
biochemistry (Dan's field), and the hardware/wetware bridge at the heart of the project.

**Consequence.** The name carries real weight — Pauling and Torvalds embody principles
(independence, craft, long horizons, open access) that shape Linus's design. The
project is personal; the name will not be genericized for broader use.

---

## DEC-0002 — Orchestration backend as the core product

**Date:** 2026-04-22
**Status:** accepted

**Context.** Several candidate architectures presented themselves: fork a harness
(Cline, claw-code, openclaw) and extend it; use harnesses directly with some glue; or
build a harness-agnostic orchestration backend that multiple front-ends point at.

**Decision.** Linus is a **harness-agnostic orchestration backend** exposing an
OpenAI-compatible endpoint. Front-ends (Cline, openclaw, VS Code chat, future native
app) are interchangeable UIs; the backend accrues Linus-specific value (tools, skills,
sandbox policy, RAG, eventually fine-tuned models).

**Consequence.** Requires building a Python backend at `src/linus/` — more work than
forking a harness. But Linus's work accrues centrally and survives harness swaps.
Swapping from Cline to openclaw to a native app doesn't require rebuilding
KnowledgeBase integration, sandbox policy, or fine-tuned models.

---

## DEC-0003 — KnowledgeBase stays separate, integrated via submodule

**Date:** 2026-04-22
**Status:** accepted

**Context.** Dan's papers_analysis project (now KnowledgeBase) overlaps heavily with
Linus's knowledge layer. Options were: (a) fully subsume KnowledgeBase into Linus, (b)
keep it separate and consume as a submodule, (c) keep it separate and consume as a
published package.

**Decision.** KnowledgeBase is tracked as a **git submodule at `modules/KnowledgeBase/`**.
Linus imports it via an adapter at `src/linus/knowledge/`. KnowledgeBase continues as an
independent project; Linus pins a SHA and updates it deliberately.

**Consequence.** KnowledgeBase can be developed and released independently. Linus
doesn't fork it. Updating the submodule is an explicit commit. Changes to
KnowledgeBase functionality happen in the KB repo, with its own review, not via Linus
edits.

---

## DEC-0004 — Package/env management via mambaforge conda

**Date:** 2026-04-22
**Status:** accepted

**Context.** Dan's existing environment uses mambaforge (conda-forge) + conda. KB also
uses conda. Options were: keep conda, switch to uv+venv, or use both.

**Decision.** Linus uses a **conda environment named `linus`**, managed via
mambaforge. Rust and uv are installed inside the conda env for tool flexibility
(pmetal build, autoresearch-mlx, etc.). Node/npm can also be installed into the env if
needed. The brew-installed `mlx`, `mlx-c`, and `ollama` are NOT reinstalled via conda —
the brew versions have native Apple Silicon optimization.

**Consequence.** Consistent with KnowledgeBase's conventions, so patterns transfer
cleanly. Environment is reproducible via `environment.yml`. Does NOT preclude
experimenting with uv-managed venvs for specific subprojects later.

---

## DEC-0005 — Maestro/Worker protocol starts OpenAI-compatible, may migrate to MCP

**Date:** 2026-04-22
**Status:** accepted

**Context.** Communication protocol between Maestro (hosted Claude) and Workers (local
models). Options: MCP, OpenAI-compatible HTTP, or a direct SDK approach.

**Decision.** Start with **OpenAI-compatible HTTP** as the protocol for Maestro/Worker
and front-end/backend. It's what Ollama, pmetal, and LM Studio all speak; it's what
Cline and openclaw already support; it's what KnowledgeBase's Haystack integration
already uses. **Revisit MCP for adoption in Phase 3** once tool-use patterns settle and
the benefit of MCP's structured context model becomes clearer.

**Consequence.** Low initial friction. Clear migration path. MCP-specific features
(cross-server context sharing, structured resources) are deferred but not precluded.

---

## DEC-0006 — pmetal evaluated as primary serving + training backend in Phase 1

**Date:** 2026-04-22
**Status:** proposed — decision gate in Phase 1

**Context.** pmetal is a comprehensive Apple Silicon ML platform (Rust, native Metal
kernels, ANE pipeline, LoRA training, distillation, OpenAI-compatible serving). It
potentially collapses "serving layer" and "training backbone" into one component.
Alternative: use Ollama for serving, mlx-lm for training.

**Decision.** **Evaluate pmetal seriously in Phase 1** (deliverable 1b) with comparative
benchmarks against Ollama on matched models. Gate decision in
`docs/adr/0001-inference-backend.md` determines whether pmetal is adopted as primary
serving backend, training backbone, both, or neither.

**Consequence.** Commits Phase 1 time to a real evaluation instead of hand-waving.
Outcome may be "adopt pmetal fully" (big architectural win) or "Ollama for serving, mlx-
lm for training" (safer) or a hybrid. The evaluation itself is valuable regardless.

---

## DEC-0007 — Claude Code remains the terminal Maestro; claw-code is reference-only

**Date:** 2026-04-22
**Status:** accepted (amended 2026-04-23 to note claw-code-local fork)

**Context.** Dan wanted a terminal-based agent harness usable with local models.
claw-code is an open-source Rust harness with similar interface but requires an
Anthropic API key and does not natively support Ollama.

**Decision.** **Claude Code (hosted) is the terminal Maestro** for the foreseeable
future. claw-code is kept as a reference clone in `repos/claw-code/` — study its
architecture and philosophy, but do not adopt it as a runtime component. A local-model
terminal agent is a Phase 5+ deliverable, built as either a thin wrapper on Linus's
backend (~500 LOC) or by adopting Cline's CLI mode if it fits.

**Consequence.** Avoids the sunk cost of patching claw-code to support local models.
Keeps near-term focus on Linus's orchestration layer. Terminal-local-agent need gets
addressed when it becomes concrete.

**Amendment 2026-04-23 — claw-code-local fork.** A community fork
([github.com/codetwentyfive/claw-code-local](https://github.com/codetwentyfive/claw-code-local))
already adds an Ollama backend to claw-code, which is exactly the gap that made upstream
claw-code reference-only. It's now cloned at `repos/claw-code-local/`. Treat upstream
**claw-code as inspiration** (architecture and philosophy) and **claw-code-local as a
practical lead** for the Phase 5+ terminal-local-agent deliverable — possibly directly
adoptable, possibly a starting point we extend. pmetal integration would still be net-new
work on top of either. The decision above does not change yet: Claude Code remains the
terminal Maestro and we are not adopting a local CLI harness as a runtime component
today. Re-evaluate when Phase 5 work begins.

---

## DEC-0008 — openclaw as front-end in Phase 5; native Linus app in Phase 8+

**Date:** 2026-04-22
**Status:** accepted

**Context.** openclaw is a polished multi-channel front-end (macOS app, voice wake,
Canvas, iOS/Android nodes) but with a large monorepo (32k+ commits) and its own
opinionated agent architecture that overlaps with Linus's orchestration layer.

**Decision.** In **Phase 5, use openclaw unmodified as a front-end**, configured to
point at Linus's OpenAI-compatible endpoint as its model provider. Accept the
duplication between openclaw's internals and Linus's; we're using it as a UI, not as a
framework to extend. In **Phase 8+, build a native Linus app** (SwiftUI or Tauri) with
fewer features but fully branded and fully under Dan's control.

**Consequence.** Short-term: chat, voice, Canvas, mobile nodes in Phase 5 without
building them. Medium-term: divergence between openclaw's features and Linus's when
their architectures conflict. Long-term: a purpose-built Linus app replaces openclaw
for Dan's primary workflows while openclaw may persist for niche capabilities.

---

## DEC-0009 — LM Studio used for model discovery, not primary runtime

**Date:** 2026-04-22
**Status:** accepted

**Context.** Dan has LM Studio installed with local models. LM Studio provides model
discovery/download UI, casual chat, and a local OpenAI-compatible server.

**Decision.** **LM Studio is a model discovery and exploration tool**, not the primary
Linus runtime. Ollama (and pmetal, if Phase 1 adopts it) serves Linus's production
path because they are scriptable and integrate into pipelines. LM Studio is used
ad-hoc for exploring new models and casual chats with models not yet wired into
Linus.

**Consequence.** Two model stores coexist (LM Studio's and Ollama's) with some
duplication. This is acceptable given their different roles. No need to unify them.

---

## DEC-0010 — Engineering conventions inherited from KnowledgeBase insights report

**Date:** 2026-04-22
**Status:** accepted

**Context.** The Claude Insights Report on KnowledgeBase surfaced actionable patterns:
smoke-test gates, Known Library Quirks section, checkpoint discipline, hooks for
lint-on-edit, parallel Task agents, custom skills. All address real failure modes.

**Decision.** **Adopt all six patterns as first-class conventions in Linus:**

- Smoke-test gates: no full-corpus runs without a sample-pass first
- Known Library Quirks section in CLAUDE.md, updated same-session when quirks are
  resolved
- Checkpoint summaries every 3–4 multi-file edits
- `.claude/settings.json` with PostToolUse hooks: `ruff format --line-length 120`,
  `ruff check --select I --fix`, `ruff check` on Python file edits
- Parallel agent fan-out as the default for work that decomposes naturally
- Custom skills at `src/linus/skills/<name>/SKILL.md` following the Anthropic
  SKILL.md convention, beginning in Phase 7

Additionally: **The Algorithm check** as a first-class convention — before adding any
component, ask "can we delete this requirement instead?" before reaching for a library,
ask "does something we already have serve this purpose?"

**Consequence.** Stronger defaults, fewer late-surfacing failures, lower Maestro token
spend, natural alignment with The Algorithm's "delete before adding" principle.

---

## DEC-0011 — Lightweight branching now (Phase 0–2), graduated gitflow at Phase 3+

**Date:** 2026-04-24
**Status:** accepted

**Context.** Linus needs a git branching model that enables safe, auditable, parallel
agentic development. The classical Driessen gitflow model (`master`, `develop`,
`feature/*`, `release/*`, `hotfix/*`) is powerful for managing versioned releases, but
Linus is pre-v1.0 with no production releases or explicit versioning yet. Adopting the
full model now would add ceremony without immediate value.

**Decision.** Use a lightweight branching model through Phase 2:
- `main` is the single long-lived integration branch (always code-reviewed)
- Feature branches (`feature/*`), agent branches (`agent/<task-id>/<slug>`), and fix
  branches (`fix/*`) branch from and PR back to `main`
- Experiments (`experiment/*`, `spike/*`) are ephemeral and not merged
- All changes to `main` require PR review by Dan before merge
- No `develop`, `release/*`, or `hotfix/*` branches yet

At Phase 3 (when Linus has versioned releases and needs release-branch discipline),
graduate to full Driessen gitflow: introduce `develop` as the integration point,
branch features from `develop`, create `release/*` and `hotfix/*` for release
management, and tag releases on `main`.

**Consequence.** Lower overhead now (no unused ceremony), while preserving a clear
migration path to gitflow when releases matter. The spec-driven Maestro/Worker protocol
naturally works with this model: Workers always branch and open PRs, Maestro reviews and
merges. The lightweight model keeps parallel task execution simple without a separate
integration branch. The branching model is fully documented in BRANCHING.md, the
Maestro/Worker protocol in docs/maestro-worker-protocol.md, and branch safety rules
integrated into SAFETY.md and CLAUDE.md's tool use policy.

---

*New decisions append below this line with monotonically increasing DEC-NNNN ids.*

---

## DEC-0012 — pmetal is the primary Phase 1b inference backend candidate

**Date:** 2026-05-03
**Status:** accepted (gate verdict pending Phase 1b LoRA + serve + comparative benchmark)

**Context.** Phase 1b pmetal evaluation in progress. Build from source successful;
smoke tests pass; initial impressions strongly positive. The evaluation must still
complete: LoRA trial, serve trial, comparative benchmark vs. Ollama, and the verdict
ADR. Sub-decisions about build flags, concurrency target, and dependency risk needed
answers regardless of the verdict.

**Decision.** pmetal is the lead candidate for Phase 2a serving and Phase 6 training
backbone. For Phase 1b: build with `--features serve,mlx,trainer` (defer
`ane,distill,data` to their phases). Concurrency target for the verdict is
single-request tok/s + RSS; 5-concurrent is a Phase 2a concern. Dependency risk
mitigation: pin a commit, document the Ollama+mlx-lm-ft fallback in
`docs/adr/0001-inference-backend.md`, and revisit quarterly.

**Consequence.** Phase 1b scope is well-defined and execution-ready. Resolves the
benchmark plurality question and the build-flags question; the LoRA + serve +
benchmark trio remain as the executable verdict. The fallback path is fully
public-API and well-understood.

---

## DEC-0013 — BitNet 2B4T spike adopted as the first concrete Phase 1c experiment

**Date:** 2026-05-03
**Status:** accepted

**Context.** Multiple paper notes (BitNet 2B4T, bitnet.cpp, BitNet Distillation) plus
the cross-cutting paper-landscape question identified a single-experiment spike that
simultaneously answers the BitNet quality-cost question, the bitnet.cpp Apple-Silicon
throughput question, and the 1-bit Worker viability question. Phase 1c needed a first
concrete experiment.

**Decision.** Pull `bitnet-b1.58-2B-4T-gguf`, build bitnet.cpp on M1 Max, benchmark
against Ollama-served Qwen2.5 and Llama-3.2 in `benchmarks/dan_tasks/` using
task-completion-time methodology (three-task schema: minimal / fixed-length /
open-ended). Spike output also seeds the Phase 1c benchmark sweep design.

**Consequence.** A single ~half-day-of-work experiment threads three Tier 1 / Tier 3
questions together. Result informs the Phase 6 fine-tuning lane decision.

---

## DEC-0014 — Phase 6 fine-tuning lane decision deferred; Phase 6a commits to FP16-LoRA on genomics regardless

**Date:** 2026-05-03
**Status:** accepted

**Context.** Phase 6 has three candidate lanes: native-1-bit (Bonsai/2B4T), BitDistill
(FP16 → 1.58-bit), and FP16-LoRA fallback. Each requires different infrastructure
investment. Picking the lane shapes Phase 6 entirely, but the right lane depends on
Phase 1c BitNet benchmark results and the genomics-vs-coding fine-tune target question.

**Decision.** Defer the lane decision until Phase 1c BitNet benchmark data lands and the
genomics-vs-coding target is settled. **Phase 6a commits to FP16-LoRA on a
genomics/biochem corpus regardless** — safe foundational work and an
always-available baseline. Explicit decision gate at the Phase 6a/6b boundary.

**Consequence.** Phase 6a is unblocked. Lane decision is informed rather than
speculative. FP16-LoRA never blocks Phase 6 deliverables.

---

## DEC-0015 — KnowledgeBase data model: dual approach (RDF + property graph)

**Date:** 2026-05-03
**Status:** accepted

**Context.** KnowledgeBase needed a graph data model commitment before Phase 2's KB
schema hardens. RDF (Semantic Web stack: rdflib, SPARQL, SHACL, ontology alignment via
GO/MeSH/ChEBI per the KGRank Phase 3 path) and property graph (richer edge attributes,
simpler mental model, performant traversal) both have legitimate fit. Inspection of
the KnowledgeBase submodule shows both `rdflib` and `networkx` already declared as
dependencies, with `graph.py` and `knowledge_graph.py` as separate modules — the
dual-substrate posture is already implicit.

**Decision.** Adopt **both substrates in parallel.** Linus's adapter
(`src/linus/knowledge/`) exposes them as separate tool families
(`linus.knowledge.sparql.*` for RDF; `linus.knowledge.graph.*` for property).
Embedded stores: rdflib (with optional Oxigraph backend if SPARQL performance
demands) for RDF; networkx for property; Kuzu evaluated later if scaling demands.
Claim typing, content hashing, and the write-back rule are baked into Phase 2 KB
schema regardless of substrate.

**Consequence.** Both Semantic Web and property-graph use cases are first-class.
KB submodule can continue developing both in parallel. Workers and Maestro see
both as queryable resources. Workload is larger than committing to one but is
distributed across the dual-developer model (Linus + KnowledgeBase repos in
partnership).

---

## DEC-0016 — [KB-spec] split convention for KB-impacting specs

**Date:** 2026-05-03
**Status:** accepted

**Context.** During the planning session of 2026-05-03, multiple Tier 1, Tier 2, and
Tier 3 questions surfaced that primarily impact KnowledgeBase rather than Linus
(KB data model, ingest quality gate, embedding ablation, keyphrase pipeline,
parallel-worker write coordination, KB architecture spec). KnowledgeBase is a
separate repo (per DEC-0003); cross-repo planning needs a clean handoff convention.

**Decision.** Spec-parts that primarily impact KnowledgeBase are tagged **[KB-spec]**
and split into a sub-document under `docs/specs/kb/` for delivery in the KnowledgeBase
repo (executed by Claude, or eventually by Linus, in partnership with Dan). Linus's
planning-update-spec carries the cross-cutting parts; [KB-spec] parts are the parallel
sub-document.

**Consequence.** Cross-repo work has a clear handoff. KB repo work doesn't pollute
Linus's planning artifacts and vice versa. Maestro can route specs to the right
working tree.

---

## DEC-0017 — Harness plurality maintained through Phase 5 with explicit role designations

**Date:** 2026-05-03
**Status:** accepted

**Context.** Linus has four candidate front-ends (Claude Code, cline, claw-code-local,
openclaw). The "converge to one" answer is empirical and depends on Dan's actual
usage; the *intent* shapes Phase 5 budget and per-harness investment.

**Decision.** Maintain plurality through Phase 5. Explicit role designations:
Claude Code = hosted Maestro (no convergence pressure; different layer); cline =
primary VS Code Worker harness; claw-code-local = primary terminal local-model
Worker harness; openclaw = Phase 5 chat/voice/canvas/mobile UI. **No per-harness
gold-plating** beyond "configure to point at Linus's endpoint and make it work." If
one proves dominant by Phase 6, naturally let it absorb the others' use cases.

**Consequence.** Each harness gets minimum-viable integration; Linus's endpoint
(OpenAI-compatible, MCP-shape tool registry) is the surface they all consume.
Convergence is observable, not engineered.

---

## DEC-0018 — Adopt MCP as the extensibility substrate

**Date:** 2026-05-03
**Status:** accepted (supersedes "revisit MCP for adoption in Phase 3" portion of DEC-0005)

**Context.** cline, openclaw, and pmetal all speak MCP. DEC-0005 deferred MCP
adoption to a Phase 3 revisit. Two new factors changed the calculation: (a) pmetal
ships a 45-tool MCP server already, (b) the harness-plurality role designations
(DEC-0017) make MCP-as-tool-registry economically dominant — register tools once,
they show up in all harnesses without per-harness glue.

**Decision.** Adopt MCP as Linus's tool-registration substrate. Phase 2 tool registry
is built MCP-shape from the start (so Phase 3 is exposure, not refactor). Linus
exposes a Linus-native MCP server AND consumes external MCP servers via a client
adapter. **pmetal's 45-tool MCP server is the first external integration target.**
Evaluate `fastmcp` (`jlowin/fastmcp`) for the server-side construction.

**Consequence.** OpenAI-compatible HTTP remains the chat-completions surface
(per DEC-0005). MCP is layered on top for tool registration and external tool
consumption. Phase 2 tool registry implementation choice (custom, fastmcp, or other)
is its own sub-decision.

---

## DEC-0019 — KB ingest quality gate as a quality surface, not a hard gate

**Date:** 2026-05-03
**Status:** accepted

**Context.** The LLM wiki synthesis recommends an auditable YAML editorial policy at
KB ingest. The naïve framing was hard accept/reject filtering — but Dan is the primary
filter (everything already on his machine has passed his download decision). Hard
gating risks losing signal already vetted by him.

**Decision.** Adopt the YAML-policy framework as a **quality surface**, not a hard
gate. Phase 2 ships YAML-policy + scoring engine + per-paper quality scorecard
surfaced in chat UI / RAG context (the model sees the score and signals when
retrieving). Domain-agnostic baseline signals: peer-review status, preprint flag,
data/code availability, retraction status, RaKUn keyphrase coverage, citation/age
signals. **No hard reject lane in Phase 2**; preprints flagged (`preprint: true`),
not auto-rejected. FineWeb-style known-good/known-bad statistical calibration is
Phase 3 learning exercise. **[KB-spec]** item.

**Consequence.** No content lost to over-eager gating. Quality information flows to
retrieval and to Maestro for review-time judgment. Phase 3 calibration teaches the
methodology rigorously without blocking Phase 2 ingest.

---

## DEC-0020 — Linus orchestration scope: sandbox + KB + MCP registry + audit; not task-decomposition primitives

**Date:** 2026-05-03
**Status:** accepted (refines DEC-0002)

**Context.** The skills synthesis correctly Algorithm-checks the custom orchestration
question (Tier 2 #13). Reaffirming DEC-0002's harness-agnostic backend commitment is
sound — but the scope of "what Linus's orchestration layer actually implements" needs
explicit narrowing to avoid re-implementing primitives that off-the-shelf tools
(Task Master AI, claude-squad, autoresearch) already do well.

**Decision.** Linus's custom orchestration layer scope = sandbox enforcement + KB
integration + MCP-shape tool registry + audit log. It does **NOT** re-implement
task decomposition primitives. Task Master AI's PRD→tasks pattern, claude-squad's
parallel-terminal pattern, and autoresearch's keep-or-revert loop are adopted as
**skills** inside Linus's skill registry, not re-built from scratch. Validated via
**new Phase 1f deliverable**: comparative evaluation of Task Master AI + claude-squad
vs. custom Linus prototype vs. pmetal-MCP-as-orchestrator on a real Phase 2 task spec
(e.g., "ingest 5 papers from `context/papers/` through KB pipeline, produce summaries,
surface in chat UI").

**Consequence.** Custom layer earns its keep on Linus-specific concerns; ecosystem
tools handle the generic. Phase 1f delivers empirical evidence rather than
assumption. DEC-0002 holds; this DEC adds bounding scope.

---

## DEC-0021 — Phase 5c formally adopts claw-code-local; 500-line custom Python agent fallback removed

**Date:** 2026-05-03
**Status:** accepted (amends DEC-0007 and ROADMAP Phase 5c)

**Context.** ROADMAP Phase 5c hedged with a "small custom terminal agent (~500 lines
of Python)" as a fallback. claw-code-local already adds an Ollama backend to claw-code
and is currently cloned at `repos/claw-code-local/`. Tier 1 #5 role designations
explicitly assigned claw-code-local as the primary terminal local-model Worker
harness. The fallback is speculative engineering.

**Decision.** Phase 5c formally = "adopt claw-code-local." The custom Python agent
fallback is removed from the roadmap. Phase 5c work scope: configure + integrate.
If claw-code-local proves insufficient at Phase 5, that triggers a fresh decision
at the time, not pre-emptive engineering now.

**Consequence.** Phase 5c is bounded and inexpensive. The Algorithm applied: delete
the speculative requirement.

---

## DEC-0022 — Parallel Worker KB write coordination: serialized writes + write-time contradiction surfacing

**Date:** 2026-05-03
**Status:** accepted

**Context.** The write-back rule (every Worker task ends with KB update proposals) is
unambiguous for a single Worker. Phase 3 multi-agent fan-out introduces concurrent
proposals on the same KB pages. Last-write-wins silently loses concurrent updates;
fully-automated reconciliation is premature complexity.

**Decision.** **Serialized writes through a coordinator + write-time contradiction
surfacing.** Workers don't write directly; they emit JSON-shaped diff proposals.
A single coordinator process applies proposals in order. Conflicts on the same
entity/page/triple flag for human (Dan/Maestro) review before merge. Git-branch-per-
ingest is the persistence layer underneath: each Worker's proposals land on
`agent/<task-id>/<slug>` branches, the writer process resolves merges on `develop`
(per DEC-0011 gitflow graduation at Phase 3). Contradiction detection at write
time, not read time. **[KB-spec]** item: spec target
`docs/specs/kb/parallel-worker-write-coordination.md`.

**Consequence.** Concurrent fan-out has well-defined semantics. No silent data loss.
Conflicts are surfaced for human judgment, not auto-resolved.

---

## DEC-0023 — Output interface: balanced bullets+prose, citations first-class, opt-in verbose; Linus reframed as personal LLM Wiki at scale

**Date:** 2026-05-03
**Status:** accepted

**Context.** The cognitive throughput papers (Zheng-Meister + Sauerbrei-Pruszynski)
quantify human conscious review at ~10 bits/s. Parallel Worker fan-out generates
zero throughput gain unless Maestro outputs are compressed before review. But
auditability matters — citations and traceability must be first-class for a
scientific KB. And bullet dumps without prose are themselves cognitively impoverished.

**Decision.** Adopt the 10-bits/s framing as a Phase 2 chat-UI design principle.
Synthesized Maestro outputs use **balanced bullets + prose** — bullets for
enumerable items, prose for reasoning, context, narrative. **Citations and
traceability are first-class, not optional**: every synthesized claim links back
to source Worker outputs, KB entities, or paper-notes. Worker outputs preserved
for Maestro inspection (drill-down UI affordance). **Opt-in `/verbose`** for
unsynthesized full-Worker output viewing. Multi-Worker fan-out outputs always
pass through a Maestro-side synthesis step before reaching Dan, with citation
links preserved. **Linus reframed as a personal LLM Wiki at scale** — citations,
traceability, and write-back discipline are core to the vision, not optional.

**Consequence.** UI design constraint baked into Phase 2 scope. Worker outputs are
artifacts; synthesized summaries are the review interface; both coexist. VISION.md
gets a paragraph on the LLM Wiki framing tying to Maestro/Worker discipline.

---

## DEC-0024 — Security posture: hash-pinned linus env + uv-via-conda for disposable experimental envs + pip-audit response protocol

**Date:** 2026-05-03
**Status:** accepted

**Context.** The litellm supply chain incident demonstrated that supply chain attacks
on Python packages are real, subtle, and time-sensitive. The current linus env had
pre-emptive ML framework deps (langchain, langgraph, haystack-ai) that increased the
attack surface for zero current functionality. No hash-pinned lock file existed. No
documented response protocol for a CVE-flagged installed package.

**Decision.** **Layered architecture.** (1) The linus conda env is the production
substrate, with `requirements-locked.txt` generated via
`pip-compile --generate-hashes` (full hash pinning) and a monthly `pip-audit`
cadence + quarterly review for "do we need any deferred packages now?" (2) **uv is
installed via conda inside the linus env** as the disposable-env tool of choice;
**untrusted experimental packages always run in disposable uv envs**, never in the
linus conda env. (3) `pip-audit` CVE response: HIGH/CRITICAL = immediate triage →
patched-version availability check → if available, env rebuild + lock-file
regeneration; if not, evaluate removal vs. documented mitigation. Response protocol
written into SAFETY.md "Supply Chain Incident Response" section. Pre-emptive
framework deps removed; dep philosophy documented in CLAUDE.md.

**Consequence.** Supply chain attack surface bounded. Experimental work continues at
full speed inside disposable envs. Quarterly review prevents lock-file rot.
Incident response is documented before incident.

---

## DEC-0025 — Curation protocol for `repos/`, `context/`, `docs/`

**Date:** 2026-05-03
**Status:** accepted

**Context.** Linus accumulates content rapidly: cloned repos, papers, notes,
synthesis docs. Without a curation protocol, `repos/` and `context/` and `docs/`
grow into junk drawers; without a removal protocol, removed content's existence
becomes opaque to future planning sessions. Healthy knowledge management requires
both growth and pruning, with memory of what was pruned and when.

**Decision.** Adopt a lightweight curation protocol covering: (a) when/why content
is added (with rationale captured in synthesis or repo notes); (b) cadence of
review (quarterly); (c) explicit archive/removal pathway; (d) **memory of what
was removed and when** via `docs/curation-log.md`. The Algorithm is applied at
each curation-review checkpoint. Protocol documented in `docs/curation-protocol.md`
and indexed in CLAUDE.md Engineering Conventions.

**Consequence.** Content can grow boldly because pruning is principled. Removed
content remains discoverable for reflection. Quarterly cadence makes the protocol
sustainable.

---

## DEC-0026 — Planning write-back cadence: Maestro/Dan + Claude planning sessions refine core files at session close

**Date:** 2026-05-03
**Status:** accepted

**Context.** The LLM Wiki synthesis's write-back rule ("every substantive task
produces two outputs: the deliverable and KB updates") was framed for Worker tasks.
Practitioner experience during the planning session of 2026-05-03 surfaced that
this discipline applies equally to Maestro/Dan + Claude planning sessions — without
explicit write-back, planning insights evaporate into chat history.

**Decision.** Adopt **planning write-back cadence** as a CLAUDE.md Engineering
Convention. At the close of every multi-question planning session, allocate time
for core-file write-back: refining CLAUDE.md, VISION.md, ROADMAP.md, ARCHITECTURE.md,
SAFETY.md, DECISIONS.md, and the relevant landscape/spec docs. The
planning-update-spec.md is the natural artifact for this routing.

**Consequence.** Planning insights compound into the knowledge base rather than
evaporating. Session boundaries become natural write-back checkpoints. Future
planning sessions inherit a refined substrate.

---

## DEC-0027 — Linus practice/stance batch (page cache, public APIs, multi-language, sovereignty, reproducibility, Obj-C)

**Date:** 2026-05-03
**Status:** accepted

**Context.** Several stance-level questions surfaced together (Tier 3 #16): trust
the OS page cache as a convention; Apple private-API risk appetite; Rust as a
co-language policy; explicit sovereignty statement; reproducibility + interpretability
principle; Obj-C/Metal-direct work as a future skill bet. These shape Linus's
posture across phases without being phase-blocking.

**Decision.** (1) **Trust the OS page cache** adopted as CLAUDE.md Engineering
Convention (anchored by the flash-moe paper's empirical finding). (2) **Public APIs
only for Linus's own code** (CoreML/MLX/Metal). pmetal uses supported APIs (not
private); the ANE reverse-engineering repo stays methodology reference only, not
vendored. Linus does not reverse-engineer Apple's private APIs. (3) **Multi-language
stance**: Python is core orchestration language; comfortable with Rust components
(pmetal, claw-code/claw-code-local), JavaScript/TypeScript components (some
node/npm familiarity), and bash for stringing CLI tools. No "one orchestration
language" policy. (4) **Light sovereignty refinement** in VISION.md borrowing
NOMAD's framing ("the network boundary is the trust boundary"); not over-elaborated.
(5) **Reproducibility + interpretability over fancy stochastic methods** adopted as
a VISION.md design principle (anchored by the Horiike PCA-projection paper). (6)
**Obj-C/Metal-direct as Phase 7/8+ skill bet** — not ruled out, deferred. Decision
revisited only if/when concrete demand surfaces.

**Consequence.** Linus's posture is documented and stable. CLAUDE.md and VISION.md
gain explicit conventions where prior implicit ones existed. Future planning sessions
can reference these stances without re-deriving them.
