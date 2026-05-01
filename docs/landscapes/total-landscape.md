# Total Landscape

A single integrated view of where Linus stands across both the cloned repos
([repo-landscape.md](repo-landscape.md)) and the paper corpus
([paper-landscape.md](paper-landscape.md)). The two component landscapes describe
their own halves well; this document does what neither can do alone — it
crosses code and theory, points out where they reinforce each other, where they
are in tension, and where the gaps between them are the work Linus actually has
to do.

It is intentionally a complement to [top-questions.md](top-questions.md): the
question file is the working agenda, and this file is the map. Read this once
before working through Tier 1; refer back as decisions land.

---

## How code and theory line up

The cloned repos and the paper corpus are not independent collections — they
are two sides of one technical bet. Each major paper thread has corresponding
code in `repos/`, and each repo has at least one paper that explains *why* the
code is the right shape. This is the structural picture:

| Theme | Theoretical anchor (`paper-notes/`) | Code anchor (`repo-notes/`) | Linus role |
|-------|--------------------------------------|------------------------------|------------|
| **1-bit / ternary inference** | BitNet line: 2310.11453 → 2402.17764 → 2411.04965 → 2504.18415 → 2504.12285 (the released 2B4T) → 2510.13998 (BitDistill) | `BitNet`, `Bonsai-demo`, `pmetal` (kernels) | Phase 1c benchmark sweep; Phase 6 fine-tuning lane |
| **>RAM streaming** | LLM in a Flash (2312.11514) → Flash-MoE (flash_moe.md) | `mlx-flash`, `flash-moe` | Phase 5+ inference path for fine-tuned/large models |
| **Training stability at depth** | JPmHC (2602.18308) — Cayley-constrained Hyper-Connections | (no code yet — gap) | Phase 6 architecture choice; possible Phase 8 synthesis |
| **Methodology / experiment loops** | Karpathy autoresearch tweets via `program.md`; Flash-MoE's 90-experiment log | `autoresearch`, `autoresearch-mlx` | Phase 6d / 7c overnight optimization template |
| **Pretraining data** | FineWeb / FineWeb-Edu (2406.17557) | (no code anchor — would be `datatrove`) | Phase 6 continued-pretraining corpus; Phase 4 versioned-dataset pattern |
| **KnowledgeBase substrate** | Hogan KG survey (2003.02320); Stankevičius embeddings (2408.08073); Curse of Dimensionality (2401.00422) | `modules/KnowledgeBase/` (submodule) | Phase 2a / Phase 3 KB design and retrieval |
| **Hypercube projections (orthogonal layer)** | Horiike-Fujishiro Phys. Rev. E | (none) | Curiosity / biology overlap; not phase-blocking |
| **Harnesses and orchestration** | (no paper anchor — practitioner thread) | `cline`, `claw-code-local`, `claw-code`, `openclaw` | Phase 1e/2/5 front-ends |
| **Data sovereignty (component catalog)** | (none — pragmatic) | `project-nomad` | Phase 4 reference catalog only |
| **KB ingestion — keyphrase extraction** | RaKUn 2.0 (2208.07262) Phase 2 baseline; KGRank (s41019-017-0055-z) Phase 3 enriched path | `modules/KnowledgeBase/` | Phase 2 ingestion pipeline; Phase 3 ontology-grounded indexing |
| **Benchmarking & inference evaluation** | Speed and LLMs (2502.16721) — task-completion time as primary metric; tok/s is misleading | `benchmarks/dan_tasks/` (design target) | Phase 1 benchmark design; Worker selection methodology |
| **Cognitive throughput / human-AI interface** | Zheng-Meister Neuron 2025 (PIIS0896627324008080) + Sauerbrei-Pruszynski rebuttal (nihms-2096004) | (no code anchor — design heuristic) | Phase 2 interface design; Maestro/Worker analogy grounding |
| **Security posture** | (no paper — practitioner synthesis in docs/security-synthesis.md) | `environment.yml`, `.claude/settings.json`, SAFETY.md | Phase 0 immediate (dep cleanup); Phase 2 (endpoint security); Phase 3 (prompt injection) |
| **Skills, practices & entrepreneurial** | (no paper — practitioner threads in docs/skills-and-practices-synthesis.md) | `repos/cline`, emerging: Task Master AI, claude-squad | Phase 1 (closed loop); commercial surface Phase 1+ |

Four observations fall out of this table:

**The BitNet thread is the most internally-coherent one.** Six papers and
three repos line up tightly enough that the right action — pull
`bitnet-b1.58-2B-4T-gguf`, build bitnet.cpp on M1 Max, benchmark — is
*overdetermined*, recurring across the BitNet b1.58 2B4T note, the bitnet.cpp
note, the BitNet Distillation note, and the cross-cutting paper-landscape
questions. This is Tier 1 #1 in [top-questions.md](top-questions.md) for
that reason.

**JPmHC and FineWeb are theory without code anchors.** Both are valuable, but
adopting either in Linus means writing or pulling new code (a Cayley
parametrization layer for MLX; a `datatrove`-style ingestion pipeline). They
are Phase 6+ candidates by virtue of where the code gap lives.

**The keyphrase extraction papers (RaKUn 2.0, KGRank) close a gap in the KB
ingestion pipeline.** Previously there was no paper anchor for *how* documents
get indexed when they enter the KnowledgeBase. RaKUn 2.0 provides the Phase 2
baseline (fast, unsupervised, CPU-only); KGRank provides the Phase 3 upgrade
path (ontology-grounded, semantic). Together they give the KB ingestion stack
a complete theory-to-implementation path.

**Security is now an explicit cross-cutting concern.** The `docs/security-synthesis.md`
analysis identified that `langchain`, `langgraph`, and `haystack-ai` are installed for
future use but represent unnecessary supply chain surface today. The first concrete action
before Phase 1 begins is removing these packages and adding hash-pinned lock files. The
Maestro/Worker architecture is an asset for prompt injection defense (Workers should
not take safety-relevant actions on their own authority regardless of what their context
window says), but that defense needs to be made explicit in the orchestration design.

---

## The three crossings worth naming

The cross-cutting bets are the places where a code thread, a theory thread,
and Linus's hardware constraints meet. Each crossing is one of the central
decisions Linus will resolve over the next several phases.

### Crossing 1 — The BitNet → Apple Silicon → ANE bridge

The BitNet papers argue, in increasingly specific terms across six releases,
that "design hardware for ternary models" is a real efficiency frontier. The
ANE repo proves the missing software half exists: backprop *and* inference can
run on Apple's Neural Engine via reverse-engineered private APIs. pmetal
hardens the same engineering patterns into a maintained Rust platform. And
bitnet.cpp publishes Apple M2 Ultra throughput numbers (2.15× → 4.91× over
FP16) on plain CPU SIMD without using the GPU or ANE at all.

The bridge to be built — and the question that recurs across notes — is which
of three rungs Linus actually needs to climb:

1. **CPU + bitnet.cpp** is operational today, ships from the same GitHub repo
   as the BitNet model code, and is the simplest path to "1.58-bit Worker
   running on Linus." It leaves the GPU and ANE on the table.
2. **GPU + pmetal kernels** is the next rung; pmetal's `pmetal-metal` crate
   has the fused low-bit kernels in production. Phase 1b's evaluation tells
   us whether this rung is climbable today.
3. **ANE + pmetal/Maderix patterns** is the third rung. The existence proof
   exists; pmetal ships an ANE pipeline; the question is whether Linus
   benchmarks "ANE prefill + GPU decode" as an explicit configuration in
   Phase 1b or defers to Phase 7+.

The decision shape is "how many rungs does Phase 2 climb?" not "which one is
right" — they're complementary, with each rung adding capability at the cost
of additional dependency surface (pmetal) or private-API risk (ANE).

### Crossing 2 — The streaming axis: dense (mlx-flash) vs. sparse (flash-moe) vs. composite (1-bit + streamed)

LLM in a Flash is the conceptual foundation for "MacBook ratios are flash-big
DRAM-small, design for that." mlx-flash operationalizes this for dense MLX
models with predictive scheduling and bit-perfect parity. Flash-MoE extends
it to MoE's extreme 2% activation sparsity with custom Metal/Obj-C, hitting
397B at 5.74 tok/s on 48 GB.

The axis Linus has to position itself on:

- **Pure dense + streaming** (mlx-flash): integrates immediately, no kernel
  work, native precision preserved. Right for fine-tuned 7B-class models that
  exceed RAM at native precision.
- **MoE + streaming** (flash-moe methodology applied to a smaller MoE):
  flash-moe's code is too bespoke to vendor, but the methodology applied to
  Mixtral-8×7B or DeepSeek-V2-Lite is the M1 Max analog of the 397B demo.
- **Composite: 1-bit + streamed** (Bonsai-Ternary-30B + mlx-flash): a
  combinatorial efficiency bet that needs a 1-bit checkpoint > 8B, which
  doesn't yet exist on Apple Silicon. Phase 6d candidate; possibly Phase 8.

The cleanest near-term call is "use mlx-flash if a fine-tuned model exceeds
RAM, otherwise stay in-RAM." The Phase 6d composite path is the more
ambitious target — it sits behind the answer to Tier 1 #3 (the Phase 6
fine-tuning path).

### Crossing 3 — The KnowledgeBase as a graph + vector layered substrate

The Hogan KG survey is the spine — every KB design decision (data model,
schema, identity, context, query, deductive layer, inductive layer) maps to
a section of the paper. The Stankevičius embeddings paper is the vector
layer over the spine; Curse of Dimensionality is the geometric reason why
naïve high-dim embeddings fail. Together these three papers are roughly the
Hamiltonian for [modules/KnowledgeBase/](../modules/KnowledgeBase/).

The cross-cutting design question — "RDF or property graph?" — is Tier 1 #4
because every subsequent KB decision (schema-first vs. emergent, RDFS vs.
OWL 2 RL, SPARQL vs. Cypher, embedding aggregation strategy, distance metric
for retrieval) flows from it. The companion vector-layer decisions
(idf+quantile-u recipe, PCA dimension reduction, distance-discrimination
health metric) are Tier 2 and depend less critically on the graph data
model choice.

The connection to the rest of Linus is via Phase 6 fine-tuning: any
Linus-specialized model trained on KB content inherits whatever the KB has
recorded, and KB embeddings are how Workers retrieve context at run time. KB
quality compounds across phases.

### Crossing 4 — Security posture vs. development velocity

This crossing is new and does not have a paper anchor — it emerged from the
`docs/security-synthesis.md` synthesis of the litellm supply chain incident (Karpathy
tweet, May 2026), the Linus dependency audit, and SAFETY.md. The framing:

SAFETY.md is well-designed for operational autonomy control — the tiered permission
model, blocklist of credential paths, and audit log are solid. But it addresses a
completely different threat class than supply chain attacks or prompt injection. A
litellm-style attack bypasses all of SAFETY.md because it runs inside the package,
before any tool call is made.

The crossing Linus has to navigate is between two legitimate pressures: the need for rapid
iteration (adding packages as needed, low-friction env management) and the need for supply
chain integrity (hash-pinned lock files, minimal dependency surface, audit gates). These
are genuinely in tension for a solo developer in rapid Phase 1 iteration.

Three rungs of the security posture, in increasing rigor:

1. **Immediate (Phase 0):** Remove pre-emptive ML framework packages (`langchain`,
   `langgraph`, `haystack-ai`). Add a `requirements-locked.txt` with hash verification
   (`pip-compile --generate-hashes`). Document the dependency philosophy in CLAUDE.md.
   Cost: one session. Benefit: eliminates the largest supply chain exposure for no
   current functionality.

2. **Phase 2 (build into MVP):** Structure the OpenAI-compatible endpoint as localhost-only
   with explicit authentication design at Phase 2. Treat KnowledgeBase content as a
   prompt injection surface and add a trust-tier for Retrieved content vs. system prompts.
   Workers should not be able to take safety-relevant actions on their own authority
   regardless of what their context window says.

3. **Phase 3+ (ongoing):** Quarterly `pip-audit` runs. Prompt injection test suite for
   KB-backed retrieval. Credential rotation protocol if an incident is detected.

---

## The three layers Linus actually has to build

Independent of theme, three distinct engineering layers fall out of the
combined landscape. Each has its own decision shape and its own dependency
structure.

### Layer A — The orchestration layer (Linus proper)

The product, in [src/linus/](../src/linus/). OpenAI-compatible endpoint,
session store, audit log, tool registry, agent spawner, sandbox. Speaks to
inference backends below it (pmetal-serve / Ollama / bitnet.cpp / mlx-flash)
and to harnesses above it (cline / claw-code-local / openclaw / Claude Code).

Most of the harness questions resolve here as "all four front-ends point at
the same Linus endpoint, converge to fewer if one wins empirically." Most of
the inference-backend questions resolve here as "Phase 1b ADR picks one
primary backend and one fallback."

This layer is mostly Linus's own code — the cloned repos and papers inform
its design but don't compose into it directly.

### Layer B — The inference / training layer

Worker models and the kernels that run them. pmetal is the top candidate by
breadth (serving + training + ANE + 12 PO methods + 45-tool MCP). bitnet.cpp
is a CPU-only serving fallback. mlx-flash is the >RAM dense path. Bonsai's
llama-server is an interim 1-bit serving path while pmetal is being
evaluated. The autoresearch loop is the methodology that drives optimization
of this layer.

The single most decisive moment is Phase 1b's pmetal evaluation. It
collapses ~6 open questions into one ADR and either commits Linus to a
single Rust platform that does most of the heavy lifting, or commits Linus
to a more federated stack of smaller pieces.

### Layer C — The KnowledgeBase / data layer

[modules/KnowledgeBase/](../modules/KnowledgeBase/) (submodule), plus the
data-sovereignty components from Phase 4 (Kiwix, ProtoMaps, Qdrant or
numpy-similarity, dataset versioning). The Hogan KG survey + Stankevičius
embeddings + Curse of Dimensionality form the theoretical substrate; FineWeb
and FineWeb-Edu are the curated-corpus references. project-nomad is a
component catalog — proof the offline pattern works, not code to vendor.

The KB v1 design has its own internal sequencing: data-model decision first
(RDF vs. property graph), then identity/context/schema, then ingestion, then
the embedding pipeline, then retrieval and the inductive layer. Each step
maps to a Hogan section.

---

## Where the gaps are

Three places where neither a repo nor a paper currently delivers what Linus
will eventually need:

**A unified BitNet × MoE × Streaming codebase.** The BitNet papers, Flash-MoE,
and JPmHC together gesture at "ternary-stable-streamed-MoE" — but no codebase
combines all three. This is the natural Phase 8 research direction, and the
right way to *enter* it is by committing to a fine-tuned BitNet Worker first
(Phase 6, Tier 1 #3) and a flash-streaming benchmark second (Phase 6d, Tier
2 #11). The synthesis is downstream of those.

**An MLX Cayley parametrization layer.** JPmHC validated the orthogonal-group
constraint on a 7M TRM at 8× B200, but no MLX implementation exists yet.
Adopting JPmHC's stability story for any Linus fine-tune would mean writing
this layer first. Phase 6 architecture decision; not phase-blocking.

**An ANE serving binary that's both production-quality and officially supported.**
pmetal uses private APIs (the same `_ANEClient` surface as the Maderix repo).
That's a fine bet for personal use but a real macOS-update risk. There is
currently no public-API ANE serving path that performs comparably. The
choice is "accept the risk and benefit from pmetal-ANE" or "stay GPU-only
and revisit if/when CoreML's posture changes."

**A clear answer on Phase 2 custom orchestration vs. off-the-shelf tools.** The
skills/practices synthesis flagged that Task Master AI (PRD → tasks → sequential
Claude execution) and claude-squad (parallel terminal agents) together might satisfy
Phase 2 requirements without Linus building a custom router. The Algorithm says delete
before building. This gap is not a code gap — it is a decision gap that should close
before Phase 2 engineering begins.

**A commercial surface and entrepreneurial plan.** Linus's capabilities — domain expertise
+ local AI orchestration + private KnowledgeBase — map onto several monetizable services
(scientific literature intelligence, biotech analysis, research infrastructure consulting).
Currently there is no planning document for the commercial layer. The open question
(top-questions.md Tier 1 #14) is whether to start generating revenue now using hosted
Claude + domain expertise while Linus builds, or defer until Phase 2+ infrastructure is ready.

---

## How the four work products fit together

[repo-landscape.md](repo-landscape.md) — describes the 12 cloned repos,
grouped into four layers, with phase-by-phase entry points and key tensions.
Code-side reference.

[paper-landscape.md](paper-landscape.md) — describes the 15 papers,
grouped by theme, with reading orders by Linus phase and cross-cutting
research-direction questions. Theory-side reference.

[total-landscape.md](total-landscape.md) (this file) — crosses the two,
identifies where code and theory line up, names the three crossings worth
deciding on, and surfaces the gaps where neither side currently delivers.

[top-questions.md](top-questions.md) — the working agenda. Three tiers of
prioritized questions, with explicit pointers back to source notes.

[open-questions.md](open-questions.md) — the complete archive of every
"open question for Dan" extracted from any per-repo, per-paper, or synthesis note. The
reservoir from which `top-questions.md` was distilled.

**New synthesis documents** produced alongside the second batch of paper notes (May 2026):

[docs/llm-wiki-synthesis.md](../llm-wiki-synthesis.md) — Synthesis of Karpathy's LLM Wiki Gist,
community-contributed repos and insights (COMMUNITY_INSIGHTS.md, KB_DESIGN_PATTERNS.md), Rohit's
v2 gist, and the autoresearch/Apple Flash thread. Covers 14 core KB design concepts, 20 relevant
repos (8 suggested for `repos/`), community-validated implementation patterns, and 9 open questions.

[docs/skills-and-practices-synthesis.md](../skills-and-practices-synthesis.md) — Synthesis of the
Claude skills and best-practices threads (17 skills, Top 50 repos, 17 best practices, Stop Staring
at Files, Cline description). Covers Maestro/Worker collaboration practices, 13 skills for Linus,
12 new repo candidates, 7 entrepreneurial opportunities, and 5 open questions.

[docs/security-synthesis.md](../security-synthesis.md) — Security posture analysis triggered by
the litellm supply chain incident. Covers current dependency surface, supply chain mitigations,
prompt injection threat model, endpoint security, and 5 open questions requiring Dan's
values-level input.

The intended workflow is to walk `top-questions.md` Tier 0 (immediate actions) first, then Tier 1
in conversation, with `total-landscape.md` open as the map. Update both this file and the relevant
decisions / planning documents (ROADMAP, DECISIONS, CLAUDE.md, the per-note "Open questions for
Dan" sections) as each answer lands.
