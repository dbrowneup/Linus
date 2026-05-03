# Synthesis Landscape: Operational Intelligence for Linus

## What This Document Is

Three synthesis documents sit in `docs/syntheses/`, each distilling a different body of
practitioner knowledge: security posture (supply chain and prompt injection), the LLM wiki
pattern (compiled knowledge bases and session architecture), and skills and practices
(collaboration patterns, entrepreneurial opportunities, and tooling). Read the individual
syntheses for depth; read this document for the cross-cutting picture — what they agree on,
where they're in tension, and what Linus should do about it.

---

## The Unifying Thesis

All three syntheses, from completely different starting points, converge on the same
underlying claim: the bottleneck has shifted from capability to structure.

The skills synthesis calls it "architectural clarity": agents can execute at speed, but only
a human who has already decomposed the task correctly, encoded the standards in files, and
specified the uncertainty protocol gets useful output. The LLM wiki synthesis calls it "the
schema is the product": without a CLAUDE.md-equivalent governing entity types, contradiction
policy, and epistemic standards, an LLM wiki is just a junk drawer that grows faster. The
security synthesis calls it "design decisions baked into the orchestration layer": tiered
trust, input provenance tagging, and dependency minimization are properties that cannot be
retrofitted — they must be encoded from the beginning, the same way a KB schema must be
designed before the first ingest, not after the first thousand notes.

They are describing the same leverage point from three angles. For Linus, this means the
most important work in Phase 1 is not running benchmarks or standing up services — it is
getting the schemas, specs, and standards right, because those compound over every subsequent
phase. Every correction filed back into CLAUDE.md is worth more than ten implementation
shortcuts.

---

## The KnowledgeBase as the Compounding Core

The LLM wiki synthesis is the most directly applicable body of knowledge Linus has accumulated,
because the KnowledgeBase submodule is already building on the graph-plus-vector substrate
that the community independently arrived at as the right architecture. What the synthesis adds
is hard-won operational wisdom about what causes KB systems to rot and what keeps them
healthy.

Three patterns deserve immediate encoding in the KnowledgeBase schema:

**Claim typing.** Every factual claim should carry an explicit epistemic tag: `[!source]` for
direct citations, `[!analysis]` for model-derived inference with reasoning shown, `[!unverified]`
for unchecked claims, `[!gap]` for known missing knowledge. The security synthesis reinforces
this from a different direction: prompt injection via KB content is most dangerous when models
cannot distinguish grounded claims from synthesized ones. Epistemic tagging is both a
knowledge-quality mechanism and a security control.

**Content hashing for staleness.** Every compiled KB entry should record the SHA-256 hash of
its source files at compile time. Stale entries — those whose source hashes have changed —
are flagged automatically without LLM involvement. This is also the security synthesis's
recommended defense against ingest-idempotency failures: a compromised or modified source
file gets caught at the content-hash check rather than silently reinforcing its now-corrupted
claims.

**The write-back rule.** Every substantive task produces two outputs: the deliverable and
KB updates. Without this discipline, knowledge evaporates into chat history. The skills
synthesis encodes the same principle as "externalize everything to version-controlled files."
Together they imply a norm: every Worker task invocation should end with KB update proposals,
not just a primary result.

The LLM wiki synthesis also answers the open question of when KnowledgeBase outgrows the
index-file approach: at roughly 100–200 pages, a single index overflows the context window.
Planning the hybrid retrieval upgrade — BM25 plus vector plus graph traversal, fused via
reciprocal rank fusion — as a Phase 3 deliverable is significantly cheaper than migrating
after the index file becomes the bottleneck. The current node count of KnowledgeBase should
be tracked against this threshold, and the Phase 3 retrieval work should be sized accordingly.

The hot-cache pattern deserves special attention because it applies beyond KnowledgeBase to
the Linus orchestration layer itself. A `session/hot.md` file of roughly 500 words — current
task, recent decisions, active blockers, what must not be reverted — costs less than 0.25%
of a 200K context window and eliminates 2–3K tokens of re-explanation per session. The
existing CLAUDE.md session startup protocol is the right mechanism to formalize this: a
standard hot-cache file structure that Workers load at session start, maintained by the
orchestration layer as a first-class artifact rather than reconstructed from conversation
history each time.

---

## Maestro/Worker Operational Discipline

The skills synthesis distills 400+ practitioner sessions into ten practices, and the most
important five map directly onto Linus's Maestro/Worker architecture.

Task specs must answer three questions before a Worker receives them: what does "done" look
like, what are the constraints, and what should the Worker do when uncertain? The last
question is the one most often skipped, and its absence is responsible for the failure mode
of long autonomous runs that confidently produce wrong output. Linus's Worker specs in
`docs/specs/` should include an explicit uncertainty protocol — "flag rather than guess" is
not enough; the protocol needs to name the specific actions the Worker should take when it
encounters missing inputs, ambiguous classifications, or tool failures.

Context scope is a design constraint, not a preference. Larger context windows produce
noisier output; Workers should receive the minimum context required for their specific
subtask, not the full KnowledgeBase, not all project files. This is a design constraint for
Phase 2's agent spawner, and it reinforces the LLM wiki's principle that scoping should be
deterministic — handled by the graph and index layer — rather than asking the LLM to filter
in-context. The agent spawner that builds context packages for Workers should call the KB's
graph traversal layer to scope the context bundle, then hand the pre-filtered package to the
model.

The skills synthesis's most striking empirical claim — parallel subagents reduced a
40-minute research task to 10 minutes — is not primarily about speed. It is about the
quality of task decomposition: the speed gain is only realized when subtasks are genuinely
independent, which requires the Maestro to have decomposed correctly before spawning. This
is the correct framing for Linus's Phase 3 parallel agent work: the investment is in spec
quality and task decomposition discipline, not in the spawning machinery itself.

Batching related work into single sessions addresses a different inefficiency: startup cost.
Every Worker session incurs context initialization overhead. The Phase 2 task scheduler
should group related work items and pass them as a batch to a single Worker session rather
than spawning separate sessions per subtask.

---

## Security and Dependency Posture

The security synthesis was triggered by the litellm supply chain attack and the observation
that Linus's security posture consists of thoughtful operational safety controls and
essentially no supply chain or input-integrity controls. Three gaps are highest priority.

The dependency surface is larger than it needs to be. `langchain`, `langgraph`, `streamlit`,
and `lm-eval` are installed in `environment.yml` for future phases that have not yet begun.
Applying The Algorithm — delete every possible step before optimizing — means removing them
now and re-adding them when their phase actually begins. Each package not installed is a
package that cannot be compromised. The security synthesis and the skills synthesis
independently arrive at this conclusion: the former because of supply chain risk, the latter
because the orchestration logic those packages provide is exactly what Linus is building as
its core competency. If Linus is going to build an orchestration layer, the state machine
that langchain/langgraph would otherwise provide is not extra work — it is the work.

The skills synthesis reinforces this with a concrete alternative: Task Master AI
(`eyaltoledano/claude-task-master`) implements the PRD-to-structured-tasks-to-execution
pattern without the multi-hundred-dependency tree of LangChain, and claude-squad provides
parallel terminal agents without it either. The right Phase 2 question is whether Linus
needs a custom orchestration layer at all, or whether Task Master AI plus Cline covers the
use case — with the explicit application of The Algorithm before committing to a custom
build.

The absence of lock files with hash pinning is the single highest-leverage gap to close.
Hash-pinned pip requirements mean a compromised PyPI package with a new hash fails the
install instead of silently deploying. `pip-audit` is a one-command baseline audit of the
currently installed environment. Together these take one afternoon and represent the largest
security surface reduction available without changing the architecture.

Prompt injection via KB content is the threat that grows non-linearly with every paper added
to KnowledgeBase. The defense is not complex: trust-level tagging on every item entering a
model's context window (with `source: knowledge_base` treated as low-trust), and structural
delivery of tool results as typed fields rather than interpolated prompt strings. The LLM
wiki synthesis's claim-typing and content-hashing patterns are the epistemic-integrity
version of the same controls. Designing these into the context assembly pipeline in Phase 2
is an order of magnitude cheaper than retrofitting them in Phase 3 after the agent fan-out
multiplies the attack surface.

---

## Entrepreneurial Leverage

The skills synthesis maps seven opportunities against Dan's specific profile — PhD biochemistry,
genomics depth, 13 years of scientific Python, failed biotech startup operational experience —
rather than treating him as a generic AI prompt-seller. Two of these deserve particular attention
because they are available immediately and generate real feedback about what clients actually
pay for.

Scientific literature intelligence for biotech teams (Opportunity 1) requires only Phase 1's
recon infrastructure and hosted Claude. Dan can do this manually now; the KnowledgeBase
makes it scale. Three to five clients at $1,000–$3,000/month each generates $3,000–$15,000
in recurring revenue while Linus builds in the background, and the client feedback produces
higher-quality signal about what intelligence products are actually useful than any amount of
roadmap speculation. The moat is Dan's ability to evaluate output quality scientifically — a
generalist prompt-seller cannot do what he can.

Automated bioinformatics pipeline documentation (Opportunity 2) can be prototyped in Phase 1
with Claude Code, before Linus's backend exists. The skill synthesis's SOP-generation pattern
applied to Snakemake, Nextflow, or Python pipeline code has a natural market among academic
labs who generate technical debt faster than they can document it and lack the bandwidth to
do it themselves.

The general principle the entrepreneurial section reinforces is that Dan's domain expertise is
itself a moat, independent of any architectural skill. The "Stop Staring at the Files" thread
argues that architectural clarity is the scarce input as agents improve, but for Dan the
higher-leverage scarce input is scientific interpretation — the ability to evaluate the output
of a genomics literature sweep in a way that a non-scientist cannot fake. Linus's design
should reflect this: the Maestro/Worker boundary should be drawn so that Workers handle
well-specified scientific data tasks, while Dan's judgment applies to hypothesis generation,
experimental design, and output interpretation. That is a different boundary than "Workers
code, Dan reviews code."

---

## Phase-Tagged Priorities

Consolidating actionable items across all three syntheses by phase:

**Immediately (before Phase 1 ends)**

Run `pip-audit` against the current linus env and fix any HIGH or CRITICAL findings. Remove
`langchain`, `langgraph`, `streamlit`, and `lm-eval` from `environment.yml`. Generate a
hash-pinned pip lock file with `pip-compile --generate-hashes`. Configure Cline against
Ollama with `OPENAI_BASE_URL=http://localhost:11434/v1` and validate the Maestro/Worker loop
with one well-specified coding task. Clone `omega-memory/omega-memory`, `jgoldfed/keppi`,
`rohitg00/agentmemory`, `bitsofchris/openaugi`, `tobi/qmd`, and `HawHello/AgenticResearchWiki`
as Phase 2–3 retrieval and memory reference material. Evaluate claude-squad and Task Master AI
as Phase 1 stopgaps and Phase 2 architecture inputs before committing to a custom orchestration
layer. Formalize a `session/hot.md` hot-cache convention in the CLAUDE.md session startup
protocol.

**Phase 2 — Linus MVP**

Design input trust tagging into the context assembly pipeline from day one: every item in a
Worker context window carries a `trust_level` field. Implement the write-back rule as a
structural requirement of Worker task specs: every task returns a deliverable plus KB update
proposals. Add `bandit` and `pip-audit` to the CI gate alongside ruff and mypy. Add a
static API key gate to the Linus endpoint bound to `127.0.0.1`. Implement the KnowledgeBase
schema with claim typing and content hashing as Phase 2 deliverables, not Phase 3. Evaluate
fastmcp (`jlowin/fastmcp`) for MCP server construction before Phase 3's MCP adoption
decision. Instrument the KB index file size and establish the hybrid retrieval upgrade
trigger threshold.

**Phase 3 — Knowledge and Parallel Agents**

Implement hybrid retrieval (BM25 plus vector plus graph traversal) as the context scoping
layer for Worker context packages — the agent spawner calls the KB's graph traversal to
pre-filter before model calls. Design a coordination mechanism for parallel Worker KB writes
before spawning the first multi-agent session; git-branch-per-ingest and mesh sync are
both partial answers. Adopt promptfoo (`promptfoo/promptfoo`) for automated Worker safety
testing alongside the sandbox enforcement tests. Add a quality gate at KB ingest — a YAML
domain editorial policy against which sources are scored before compilation, with failures
routed to `raw/FILTERED.md` with an explanation. Implement the contradiction policy in the
KnowledgeBase schema: flag at write time, require human resolution before marking canonical.

---

## Cross-Cutting Open Questions

> **All cross-cutting questions resolved 2026-05-03.** See
> [../questions/top-questions.md](../questions/top-questions.md) Resolution Log and
> [../specs/planning-update-spec.md](../specs/planning-update-spec.md). Inline
> resolutions noted below.

Several questions surface in multiple syntheses or are unresolvable without Dan's input:

**Does Linus need a custom orchestration layer, or does Task Master AI + Cline cover Phase 2?**
This is the highest-priority architectural question before Phase 2 begins. The security and
skills syntheses both point toward minimizing the custom surface; the LLM wiki synthesis
implies the KB interaction layer and session architecture are where the real custom work lies.
The Algorithm says delete before building. Run Task Master AI against a real Phase 2 task spec
and measure whether it covers the KnowledgeBase integration and sandbox policy requirements
before committing to a custom router.

**RESOLVED:** Keep DEC-0002 (custom orchestration layer) as the architectural
commitment, but Algorithm-check the orchestration *primitives* via a **new Phase 1f
deliverable**: evaluate Task Master AI + claude-squad vs. custom Linus prototype vs.
pmetal-MCP-as-orchestrator on a real Phase 2 task spec. Adopt PRD→tasks pattern as a
**skill** inside Linus, not as a re-implementation. Linus custom layer scope clarified:
sandbox enforcement + KB integration + MCP registry + audit. Does NOT re-implement
task decomposition primitives.

**What is the right KB ingest quality gate for Dan's specific scientific domains?** The community
consensus is that filtering noise at the door beats any retrieval improvement downstream, and
that the gate should be an auditable YAML policy rather than implicit human judgment. But what
are the right domain criteria for genomics, computational biology, and environmental science
papers? What field-specific quality signals (journal tier, methodology rigor, peer review status,
data availability) should the gate encode? This shapes the KnowledgeBase schema in Phase 2.

**RESOLVED:** YAML-policy framework adopted as a **quality surface, not a hard gate.**
Reframing rationale: Dan is the primary filter — content already on his machine has
passed his download decision. The gate scores items on domain-agnostic baseline
signals (peer-review status, preprint flag, data/code availability, retraction status,
RaKUn keyphrase coverage, citation/age signals) and surfaces the score in retrieval
context. **No hard reject lane in Phase 2.** Preprints flagged (`preprint: true`),
not rejected. FineWeb-style known-good/known-bad statistical calibration adopted as
**Phase 3** learning exercise. **[KB-spec]** item.

**How should Linus handle parallel Worker KB writes?** The write-back rule is straightforward
for a single agent; for Phase 3's fan-out, multiple Workers may simultaneously propose updates
to the same KB pages. Git-branch-per-ingest and last-write-wins are partial answers, but the
right coordination mechanism for Linus's specific multi-agent pattern is not obvious. This
question should be answered in the Phase 3 KB architecture spec before any parallel agent work
begins.

**RESOLVED:** Adopt **serialized writes through a coordinator + write-time
contradiction surfacing.** Workers emit JSON-shaped diff proposals; a coordinator
process merges in order; conflicts on the same entity/page/triple flag for human
(Dan/Maestro) review before merge. Git-branch-per-ingest as the persistence layer
underneath. Contradiction detection at write time, not read time. **[KB-spec]:**
`docs/specs/kb/parallel-worker-write-coordination.md`.

**What is the right fine-tuning target in Phase 6, and when should that decision be made?**
The skills synthesis argues this decision should be made by Phase 3, not deferred to Phase 6.
A genomics-specialized model opens the scientific intelligence opportunities; a coding-specialized
model accelerates Linus's own development; a personal-writing-style model changes the
collaboration pattern with Workers. The security synthesis adds: whichever path is chosen,
the training data provenance is a supply chain question, and the KB quality controls designed
in Phase 2 directly determine the quality of the training corpus in Phase 6. These are not
independent decisions.

**RESOLVED:** Defer the lane decision (native-1-bit vs. BitDistill vs. FP16-LoRA)
until Phase 1c BitNet benchmark data lands. **Phase 6a commits to FP16-LoRA on
genomics/biochem corpus regardless** — safe foundational work and an always-available
baseline. Explicit decision gate at the Phase 6a/6b boundary informed by Phase 1c
results and the genomics-vs-coding fine-tune target question. Code-specialized BitNet
becomes a candidate Phase 6 deliverable iff Phase 1c BitNet 2B4T spike validates the
1-bit quality path AND code performance is the surfaced gap.

**Should Dan start generating revenue from AI-assisted services now, before Linus is complete?**
The skills synthesis argues yes, on the grounds that real client feedback about what intelligence
products are actually useful is more valuable than speculative roadmap planning. Starting one
client engagement at the scientific literature intelligence level generates that feedback while
Linus builds, without requiring any Linus infrastructure to exist. The counterargument is focus
cost — client work consumes Maestro time, which is the scarce resource. This is a values-level
question about how Dan wants to allocate the next six months, not a technical one.

**RESOLVED:** Skip the binary. **New Phase 2 deliverable:
`docs/entrepreneurial-surface.md`** — a planning document articulating the opportunity
surface (who would buy what, at what price, with what infrastructure). Until that
document lands and a deliberate decision is made, don't actively pursue clients but
don't rule it out. Re-evaluate when Linus is closer to operational.

**What is the response protocol when `pip-audit` reports a CVE in the installed environment?**
The litellm incident was discovered accidentally via a RAM crash. A more subtle attack would not
announce itself. Having a written incident response protocol — immediate env rebuild, session
log audit, credential rotation scope — before an incident makes it far more likely to be
executed correctly under stress. The security synthesis lists this as an open question; it should
be answered and committed to SAFETY.md before Phase 2's network-egress surface expands.

**RESOLVED:** Tier 0 #1 — draft "Supply Chain Incident Response" section in
SAFETY.md covering trigger / containment / credential rotation / attestation, plus
explicit `pip-audit` CVE response protocol (severity triage → patched-version check
→ env rebuild + lock-file regeneration; if no patch, evaluate removal vs. documented
mitigation). **Layered architecture:** linus conda env (production, hash-pinned via
`requirements-locked.txt`, monthly `pip-audit` cadence) + uv disposable envs
(experimental packages always isolated). uv installed via conda inside linus env.

---

## Quick Reference

| Synthesis | Core Claim | Highest-Leverage Action | Phase |
|-----------|------------|------------------------|-------|
| Security | Linus has operational safety but no supply chain or input-integrity controls | pip-audit + hash lock file + remove future-phase deps | Now |
| LLM Wiki | Compile-don't-retrieve; the schema is the product; write-back is the discipline | Claim typing + content hashing in KB schema | Phase 2 |
| Skills & Practices | Bottleneck is clarity, not execution; encode standards in files | Hot cache convention + Worker spec uncertainty protocol | Now / Phase 2 |
| All three | Every dependency is a trust relationship; orchestration logic is Linus's core | Delete langchain/langgraph; evaluate Task Master AI before building custom router | Phase 2 design |

---

*This document should be revisited when Phase 2 begins (to validate the Task Master AI vs. custom
orchestration decision), when Phase 3 parallel agents are designed (to address the KB write
coordination question), and whenever any of the three source syntheses is significantly updated.*
