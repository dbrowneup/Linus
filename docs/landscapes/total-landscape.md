# Total Landscape

## What This Document Is

Four inputs feed into Linus's working picture: twelve cloned repos
([repo-landscape.md](repo-landscape.md)), fifteen papers
([paper-landscape.md](paper-landscape.md)), three practitioner syntheses
([synthesis-landscape.md](synthesis-landscape.md)), and this document.
The first three describe their own domains well; this document crosses all of them —
pointing out where code, theory, and practice reinforce each other, where they are in
tension, and where the gaps between them are the work Linus actually has to do.

It is intentionally a complement to [top-questions.md](top-questions.md): the question
file is the working agenda, this file is the map. Read this once before working through
Tier 1; refer back as decisions land.

---

## How code, theory, and practice align

The repos, papers, and practitioner syntheses are not independent collections — they are
three views of one technical bet. Most major themes now have anchors in all three; where a
theme has only one or two anchors, the gap is work Linus has to do:

| Theme | Theory (`paper-notes/`) | Code (`repos/`) | Practice (`synthesis-landscape.md`) | Linus role |
|-------|------------------------|-----------------|-------------------------------------|------------|
| **1-bit / ternary inference** | BitNet line: 2310.11453 → 2402.17764 → 2411.04965 → 2504.18415 → 2504.12285 (the released 2B4T) → 2502.11880 (bitnet.cpp) → 2510.13998 (BitDistill) | `BitNet`, `Bonsai-demo`, `pmetal` (kernels) | — | Phase 1c benchmark sweep; Phase 6 fine-tuning lane |
| **>RAM streaming** | LLM in a Flash (2312.11514) → Flash-MoE (flash_moe.md) | `mlx-flash`, `flash-moe` | — | Phase 5+ inference path for fine-tuned/large models |
| **Training stability at depth** | JPmHC (2602.18308) — Cayley-constrained Hyper-Connections | (no code yet — gap) | — | Phase 6 architecture choice; possible Phase 8 synthesis |
| **Methodology / experiment loops** | Karpathy autoresearch tweets via `program.md`; Flash-MoE 90-experiment log | `autoresearch`, `autoresearch-mlx` | Skills synthesis: keep-or-revert as an explicit named practice; 42% discard rate as a sign search is working | Phase 6d overnight optimization template |
| **Pretraining data** | FineWeb / FineWeb-Edu (2406.17557) | (no code anchor — would be `datatrove`) | — | Phase 6 continued-pretraining corpus; Phase 4 versioned-dataset pattern |
| **KnowledgeBase substrate** | Hogan KG survey (2003.02320); Stankevičius embeddings (2408.08073); Curse of Dimensionality (2401.00422) | `modules/KnowledgeBase/` (submodule) | LLM wiki synthesis: compile-don't-retrieve; schema is the product; hot-cache pattern (~500 words, 2.7× context savings); retrieval scaling wall at 100–200 nodes | Phase 2a / Phase 3 KB design and retrieval |
| **KB ingestion — keyphrase extraction** | RaKUn 2.0 (2208.07262) Phase 2 baseline; KGRank (s41019-017-0055-z) Phase 3 enriched path | `modules/KnowledgeBase/` | LLM wiki synthesis: claim typing (`[!source]` / `[!analysis]` / `[!unverified]` / `[!gap]`), content hashing for staleness, write-back rule, quality gate at ingest | Phase 2 ingestion pipeline; Phase 3 ontology-grounded indexing |
| **Benchmarking & inference evaluation** | Speed and LLMs (2502.16721) — task-completion time as primary metric; tok/s is misleading | `benchmarks/dan_tasks/` (design target) | Skills synthesis: task-completion time as the Worker selection axis; Worker spec uncertainty protocols to prevent misleading autonomous runs | Phase 1 benchmark design; Worker selection methodology |
| **Cognitive throughput / output interface** | Zheng-Meister Neuron 2025 (PIIS0896627324008080) + Sauerbrei-Pruszynski rebuttal (nihms-2096004) | (no code anchor — design heuristic) | Skills synthesis: parallel Worker fan-out gains zero throughput for Dan unless the Maestro interface compresses outputs to the essential bits first; default to high-density concise outputs | Phase 2 interface design; Maestro/Worker analogy grounding |
| **Harnesses and orchestration** | (no paper — practitioner thread) | `cline`, `claw-code-local`, `claw-code`, `openclaw` | Skills synthesis: Task Master AI + claude-squad as Phase 2 off-the-shelf candidates; evaluate before building custom router; The Algorithm says delete before building | Phase 1e/2/5 front-ends |
| **Data sovereignty (component catalog)** | (none — pragmatic) | `project-nomad` | — | Phase 4 reference catalog only |
| **Security posture** | (none — practitioner synthesis) | `environment.yml`, `.claude/settings.json`, `SAFETY.md` | Security synthesis: pip-audit + hash lock file + remove future-phase deps; trust-tier tagging for KB content; incident response protocol before Phase 2 | Phase 0 immediate (dep cleanup); Phase 2 (endpoint + prompt injection); Phase 3+ (audit cadence) |
| **Skills, practices & entrepreneurial** | (none — practitioner threads) | `repos/cline`; emerging: Task Master AI, claude-squad | Skills synthesis: 10 collaboration practices; 13 skills; 7 entrepreneurial opportunities filtered for Dan's PhD-biochemist/genomics profile; domain expertise is the moat | Phase 1 (closed loop); commercial surface Phase 1+ |
| **Hypercube projections (orthogonal layer)** | Horiike-Fujishiro Phys. Rev. E | (none) | — | Curiosity / biology overlap; not phase-blocking |

Five observations fall out of this table:

**The BitNet thread is the most internally-coherent one.** Six papers and three repos line up
tightly enough that the right Phase 1 action — pull `bitnet-b1.58-2B-4T-gguf`, build
bitnet.cpp on M1 Max, benchmark — is *overdetermined*, recurring across the 2B4T note, the
bitnet.cpp note, the BitDistill note, and [top-questions.md](top-questions.md) Tier 1 #1.

**JPmHC and FineWeb are theory without code anchors.** Both are Phase 6+ candidates by virtue
of where the code gap lives — adopting either means writing new code (a Cayley parametrization
layer for MLX; a `datatrove`-style ingestion pipeline).

**The keyphrase extraction papers close a gap in the KB ingestion pipeline.** Previously
there was no paper anchor for *how* documents get indexed when they enter the KnowledgeBase.
RaKUn 2.0 provides the Phase 2 baseline (fast, unsupervised, CPU-only); KGRank provides the
Phase 3 upgrade path (ontology-grounded, semantic). Together they give the KB ingestion stack
a complete theory-to-implementation path.

**The practitioner syntheses fill the operational gap that repos and papers leave open.** The
security, LLM wiki, and skills syntheses now provide the "how to operate" layer — KB schema
discipline, Worker spec uncertainty protocols, dependency philosophy, session architecture.
Most strikingly, the security and skills syntheses independently arrive at the same
recommendation to remove langchain/langgraph: one for supply chain risk, the other because
the orchestration logic is Linus's core competency and shouldn't be outsourced.

**Security is now a first-class cross-cutting concern with a full practitioner anchor.** The
security synthesis identified that SAFETY.md is well-designed for operational autonomy control
but addresses a completely different threat class than supply chain attacks or prompt injection.
These gaps need to close before Phase 2 expands the network-egress surface.

---

## The four crossings worth naming

The cross-cutting bets are places where a code thread, a theory thread, and now a practitioner
thread meet. Each crossing is one of the central decisions Linus will resolve over the next
several phases.

### Crossing 1 — The BitNet → Apple Silicon → ANE bridge

The BitNet papers argue, in increasingly specific terms across six releases, that "design
hardware for ternary models" is a real efficiency frontier. The ANE repo proves the missing
software half exists: backprop *and* inference can run on Apple's Neural Engine via
reverse-engineered private APIs. pmetal hardens the same engineering patterns into a maintained
Rust platform. And bitnet.cpp publishes Apple M2 Ultra throughput numbers (2.15× → 4.91× over
FP16) on plain CPU SIMD without using the GPU or ANE at all.

The bridge to be built — and the question that recurs across notes — is which of three rungs
Linus actually needs to climb:

1. **CPU + bitnet.cpp** is operational today, ships from the same GitHub repo as the BitNet
   model code, and is the simplest path to "1.58-bit Worker running on Linus." It leaves the
   GPU and ANE on the table.
2. **GPU + pmetal kernels** is the next rung; pmetal's `pmetal-metal` crate has fused low-bit
   kernels in production. Phase 1b's evaluation tells us whether this rung is climbable today.
3. **ANE + pmetal/Maderix patterns** is the third rung. The existence proof exists; pmetal ships
   an ANE pipeline; the question is whether Linus benchmarks "ANE prefill + GPU decode" as an
   explicit configuration in Phase 1b or defers to Phase 7+.

The decision shape is "how many rungs does Phase 2 climb?" not "which one is right" — they're
complementary, each adding capability at the cost of additional dependency surface (pmetal) or
private-API risk (ANE).

### Crossing 2 — The streaming axis: dense (mlx-flash) vs. sparse (flash-moe) vs. composite (1-bit + streamed)

LLM in a Flash is the conceptual foundation for "MacBook ratios are flash-big DRAM-small,
design for that." mlx-flash operationalizes this for dense MLX models with predictive
scheduling and bit-perfect parity. Flash-MoE extends it to MoE's extreme 2% activation
sparsity with custom Metal/Obj-C, hitting 397B at 5.74 tok/s on 48 GB.

The axis Linus has to position itself on:

- **Pure dense + streaming** (mlx-flash): integrates immediately, no kernel work, native
  precision preserved. Right for fine-tuned 7B-class models that exceed RAM at native precision.
- **MoE + streaming** (flash-moe methodology applied to a smaller MoE): flash-moe's code is
  too bespoke to vendor, but the methodology applied to Mixtral-8×7B or DeepSeek-V2-Lite is
  the M1 Max analog of the 397B demo.
- **Composite: 1-bit + streamed** (Bonsai-Ternary-30B + mlx-flash): a combinatorial
  efficiency bet that needs a 1-bit checkpoint > 8B, which doesn't yet exist on Apple Silicon.
  Phase 6d candidate; possibly Phase 8.

The cleanest near-term call is "use mlx-flash if a fine-tuned model exceeds RAM, otherwise
stay in-RAM." The composite path is the more ambitious Phase 6d target — it sits behind the
answer to Tier 1 #3 (the Phase 6 fine-tuning path).

### Crossing 3 — The KnowledgeBase as graph + vector layered substrate

The Hogan KG survey is the spine — every KB design decision (data model, schema, identity,
context, query, deductive layer, inductive layer) maps to a section of the paper. The
Stankevičius embeddings paper is the vector layer over the spine; Curse of Dimensionality is
the geometric reason why naïve high-dim embeddings fail.

The practitioner layer adds operational depth that neither the paper nor the code currently
encodes: the LLM wiki synthesis establishes that the schema is the product — without typed
entities, a contradiction policy, and epistemic standards built in from the beginning, a KB is
a junk drawer that grows faster than it can be used. Three patterns must be baked into the
Phase 2 KB schema before the first paper is formally ingested: claim typing (`[!source]` /
`[!analysis]` / `[!unverified]` / `[!gap]`), content hashing for staleness detection, and the
write-back rule (every Worker task ends with KB update proposals, not just a primary result).
The security synthesis reinforces claim typing from a different direction: prompt injection via
KB content is most dangerous when models cannot distinguish grounded claims from synthesized
ones. Epistemic tagging is both a knowledge-quality mechanism and a security control.

The cross-cutting design question — "RDF or property graph?" — is Tier 1 #4 because every
subsequent KB decision flows from it. The schema discipline and claim typing are not dependent
on that choice — they should be implemented in Phase 2 regardless of which graph model is
selected.

### Crossing 4 — Structure as the operational bottleneck

This crossing did not exist in earlier versions of this document. It emerged from the
practitioner synthesis layer and has no direct paper or code anchor — it is a practitioner
finding that reframes what the code and theory layers are actually pointing at.

All three syntheses, from completely different starting points, converge on the same claim:
the bottleneck has shifted from capability to structure. The skills synthesis calls it
"architectural clarity" — agents can execute at speed, but only a human who has already
decomposed the task correctly, encoded the standards in files, and specified the uncertainty
protocol gets useful output. The LLM wiki synthesis calls it "the schema is the product."
The security synthesis calls it "design decisions baked into the orchestration layer" —
tiered trust, input provenance tagging, and dependency minimization cannot be retrofitted.

This crossing changes the reading of what Phase 1's most important work actually is. Running
benchmarks and standing up services are necessary Phase 1 deliverables, but they do not
compound across phases. The compound-interest work is encoding KB schema design, Worker spec
uncertainty protocols, CLAUDE.md session standards, and dependency philosophy correctly now,
because those decisions propagate through every subsequent phase. Every correction filed back
into CLAUDE.md is worth more than ten implementation shortcuts.

The practical implication for Phase 2: the engineering plan should allocate explicit time to
schema design, spec templates, and security posture — not as pre-work before "real"
implementation, but as the highest-leverage implementation work of Phase 2 itself.

---

## The three layers Linus actually has to build

Independent of theme, three distinct engineering layers fall out of the combined landscape.
Each has its own decision shape and dependency structure.

### Layer A — The orchestration layer (Linus proper)

The product, in `src/linus/`. OpenAI-compatible endpoint, session store, audit log, tool
registry, agent spawner, sandbox. Speaks to inference backends below it (pmetal-serve /
Ollama / bitnet.cpp / mlx-flash) and to harnesses above it (cline / claw-code-local /
openclaw / Claude Code).

The most consequential open question for this layer is now whether to build it at all. The
skills synthesis argues that Task Master AI implements the PRD-to-structured-tasks-to-execution
pattern without the multi-hundred-dependency tree of LangChain, and claude-squad provides
parallel terminal agents without it. The Algorithm says delete before building. The custom
orchestration layer is justified if, and only if, KnowledgeBase integration and sandbox policy
require custom primitives that off-the-shelf tools cannot provide. This should be answered by
explicit measurement — running Task Master AI against a real Phase 2 task spec — before Phase 2
engineering begins.

If a custom layer is built, the security synthesis adds two structural requirements that cannot
be retrofitted into Phase 3: input trust-tier tagging on every item in every Worker context
window, and a static API key gate binding the endpoint to `127.0.0.1`. Both are cheap to
design in from the start and expensive to add after the first multi-agent session.

### Layer B — The inference / training layer

Worker models and the kernels that run them. pmetal is the top candidate by breadth (serving +
training + ANE + 12 preference-optimization methods + 45-tool MCP). bitnet.cpp is a CPU-only
serving fallback. mlx-flash is the >RAM dense path. Bonsai's `llama-server` is an interim
1-bit serving path while pmetal is being evaluated. The autoresearch loop is the methodology
that drives optimization of this layer.

The single most decisive moment is Phase 1b's pmetal evaluation. It collapses ~6 open
questions into one ADR and either commits Linus to a single Rust platform that does most of
the heavy lifting, or commits Linus to a more federated stack of smaller pieces.

### Layer C — The KnowledgeBase / data layer

`modules/KnowledgeBase/` (submodule), plus the data-sovereignty components from Phase 4
(Kiwix, ProtoMaps, Qdrant or numpy-similarity, dataset versioning). The Hogan KG survey +
Stankevičius embeddings + Curse of Dimensionality form the theoretical substrate; FineWeb and
FineWeb-Edu are the curated-corpus references.

The practitioner syntheses expand this layer's Phase 2 scope beyond the structural data-model
decision. Claim typing and content hashing should be built into the KB schema as Phase 2
deliverables — they are both a knowledge-quality mechanism and a security control against
prompt injection. The retrieval scaling wall (a single index file overflows context at roughly
100–200 KB nodes) should be tracked from Phase 2 onwards, with the hybrid retrieval upgrade
(BM25 + vector + graph traversal, fused via reciprocal rank fusion) scoped as a Phase 3
deliverable before the wall is hit, not after. And the write-back rule — every Worker task
ends with KB update proposals, not just a primary result — should be structural in Worker
task specs from Phase 2, not a convention added later.

---

## Where the gaps are

Seven places where neither a repo, a paper, nor a practitioner synthesis currently delivers
what Linus will eventually need:

**A unified BitNet × MoE × Streaming codebase.** The BitNet papers, Flash-MoE, and JPmHC
together gesture at "ternary-stable-streamed-MoE" — but no codebase combines all three. This
is the natural Phase 8 research direction, entered by committing to a fine-tuned BitNet Worker
first (Phase 6) and a flash-streaming benchmark second (Phase 6d).

**An MLX Cayley parametrization layer.** JPmHC validated the orthogonal-group constraint on a
7M TRM at 8× B200, but no MLX implementation exists yet. Phase 6 architecture decision; not
phase-blocking.

**An ANE serving binary that is both production-quality and officially supported.** pmetal uses
private APIs. There is currently no public-API ANE serving path that performs comparably. The
choice is "accept the risk and benefit from pmetal-ANE" or "stay GPU-only and revisit if
CoreML's posture changes."

**A clear answer on Phase 2 custom orchestration vs. off-the-shelf tools.** The skills and
security syntheses both point toward minimizing the custom surface; the LLM wiki synthesis
implies the KB interaction layer is where the real custom work lies. The Algorithm says delete
before building. This gap is not a code gap — it is a decision gap that must close before
Phase 2 engineering begins. Run Task Master AI against a real Phase 2 task spec and measure
whether it covers KnowledgeBase integration and sandbox policy requirements.

**A KB ingest quality gate for Dan's specific scientific domains.** The LLM wiki synthesis
establishes that filtering noise at the door beats any retrieval improvement downstream, and
the gate should be an auditable YAML domain editorial policy. But the right criteria for Dan's
domains (genomics, computational biology, environmental science) have not been specified.
What field-specific signals — journal tier, methodology rigor, peer review status, data
availability — should the gate encode? This shapes the Phase 2 KB schema.

**A written incident response protocol.** The litellm supply chain incident was discovered
accidentally via a RAM crash; a more subtle attack would not announce itself. The security
synthesis identifies this as an open question that should be answered and committed to SAFETY.md
before Phase 2's network-egress surface expands. This is not a code gap — it closes in one
session.

**A commercial surface and entrepreneurial plan.** Linus's capabilities — domain expertise +
local AI orchestration + private KnowledgeBase — map onto several monetizable services. The
skills synthesis argues that scientific literature intelligence for biotech teams is buildable
today with Phase 1 infrastructure and hosted Claude, generating $3,000–$15,000/month in
recurring revenue while Linus builds, and producing higher-quality signal about what clients
pay for than any amount of roadmap speculation. Currently there is no planning document for
the commercial layer, and the trade-off (client revenue now vs. infrastructure focus) is an
unresolved values-level question.

---

## How the six work products fit together

[repo-landscape.md](repo-landscape.md) — describes the 12 cloned repos, grouped into four
layers, with phase-by-phase entry points and key tensions. Code-side reference.

[paper-landscape.md](paper-landscape.md) — describes the 15 papers, grouped by theme, with
reading orders by Linus phase and cross-cutting research-direction questions. Theory-side
reference.

[synthesis-landscape.md](synthesis-landscape.md) — describes the three practitioner syntheses
(security posture, LLM wiki pattern, skills and practices), with the cross-cutting picture of
what they agree on, where they are in tension, and phase-tagged priorities.
Practitioner-knowledge reference.

[total-landscape.md](total-landscape.md) (this file) — crosses all three, identifies where
code, theory, and practice align, names the four crossings worth deciding on, and surfaces
the gaps where no current input delivers what Linus will need.

[top-questions.md](top-questions.md) — the working agenda. Three tiers of prioritized
questions, with explicit pointers back to source notes and synthesis documents.

[open-questions.md](open-questions.md) — the complete archive of every "open question for Dan"
extracted from any per-repo, per-paper, or synthesis note. The reservoir from which
`top-questions.md` was distilled.

**Synthesis documents** in `docs/syntheses/`:

[docs/syntheses/security-synthesis.md](../syntheses/security-synthesis.md) — security posture
analysis triggered by the litellm supply chain incident. Covers dependency surface, supply
chain mitigations, prompt injection threat model, endpoint security, and 5 open questions.

[docs/syntheses/llm-wiki-synthesis.md](../syntheses/llm-wiki-synthesis.md) — synthesis of the
Karpathy LLM wiki gist, community-contributed repos and insights, Rohit's v2 gist, and the
autoresearch/Apple Flash thread. Covers 14 KB design concepts, 20 relevant repos, and 9 open
questions.

[docs/syntheses/skills-and-practices-synthesis.md](../syntheses/skills-and-practices-synthesis.md)
— synthesis of the Claude skills and best-practices threads. Covers 10 collaboration practices,
13 skills, 13 repo candidates, 7 entrepreneurial opportunities, and 5 open questions.

The intended workflow is to walk `top-questions.md` Tier 0 (immediate actions) first, then
Tier 1 in conversation, with `total-landscape.md` open as the map. Update both this file and
the relevant planning documents (ROADMAP.md, DECISIONS.md, CLAUDE.md, the per-note open
questions) as each answer lands.
