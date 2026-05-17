# Fresh Total Landscape — reconstruction from syntheses

_Composed 2026-05-16 from the 27 synthesis documents without consulting any of
the existing landscape or top-questions files. This is the cross-corpus rollup
asking: what is the project actually built around, and where are the major
load-bearing threads, crossings, and gaps?_

## What this document is

The 27 syntheses make a project that is bigger than any single one of them.
This document is the attempt to write down what they say collectively, sorted
by how settled each claim is. Three axes organize the picture:

- **Maturity** — what is empirically validated, what is in-flight, what is
  speculative.
- **Pillar** — what is substrate (inference, memory, KB, safety), what is
  behavior (agents, skills, evaluation), what is domain (biology, finance),
  what is commercial-surface.
- **Phase** — which roadmap phase the claim becomes load-bearing.

The document leans on maturity as the primary organizing axis because Dan asked
for it. Pillar and phase show up as cross-cuts inside each maturity tier.

---

## Part I — what is settled (the validated substrate)

These threads have crossed enough internal evidence that they read as the
load-bearing assumptions of the project. They show up in multiple syntheses,
have ADR backing in many cases, and at least one downstream commitment has
been made on top of them. They are not "done" — Linus has not shipped most of
them yet — but the question "should we do this at all?" has been answered.

### 1. Apple Silicon as the deployment substrate, no CUDA in the hot path

Every synthesis that touches inference, training, or kernels operates under
this constraint. The Maestro session prompt names it. Five distinct evidence
sources reinforce it. The infrastructure-foundations synthesis treats the
modern Llama recipe (RoPE + RMSNorm + SwiGLU + GQA) as a settled baseline
modern Transformer architecture for any local Worker. The native-low-bit
synthesis chronicles the two-year arc from BitNet existence-proof to Bonsai
Ternary 8B as a downloadable MLX-native artifact; the trajectory from
"research" to "deployable" is the strongest single piece of evidence that the
Apple Silicon path is viable for capable local LLMs. The g1-apple-silicon
cluster commits to pmetal as the most likely production substrate for both
inference and training, with mlx-flash as the >RAM-streaming path and the
flash-MoE methodology as a reference rather than vendored code. The
biological-foundation-models synthesis surveys eight bio FMs and finds five of
them are M1-Max-tractable today, one needs MLX conversion, one needs a spike,
and only Evo 2 (40B) is genuinely out of range. The
function-annotation-discovery synthesis confirms that Group A FMs become Group
C tools without further plumbing for most cases.

The convention that earns the most repeated mention across syntheses is **trust
the OS page cache**: a hand-engineered 9.8 GB Metal LRU expert cache wrapping
mmap'd weight shards hurt throughput by 38%; deleting it restored performance.
The lesson is named in five places. It is now an engineering convention rather
than a curiosity, and it generalizes to any data-streaming or weight-streaming
workload Linus undertakes.

The hardware constraint also forecloses certain paths cleanly. **Docker
inference is forbidden** because macOS VMs do not pass through Metal or ANE;
Docker is fine only for stateful services that need no ML compute. This rule
shows up in the security synthesis (the WeKnora anti-pattern), the
safety-alignment-privacy synthesis (the anamnesis disqualifier), and several
cluster syntheses.

### 2. The Maestro/Worker discipline, instrumented for attribution

The architectural commitment — hosted Claude plus Dan as Maestro, local 7B-32B
models as Workers — is the most cross-cited pattern in the corpus. The
llms-in-science synthesis frames it in philosophical terms (a hybrid of Schulz
collaborator-frame + Marelli accountability + Botvinick-Gershman roadmap-agency
+ soft Bender skepticism about hosted-frontier-as-load-bearing). The
humans-teams-performance synthesis grounds it empirically at three timescales
of high performance (the slow integrative controller over fast parallel
executors is a recurring solution to bandwidth-limited high performance across
nine orders of magnitude). The skills-and-practices synthesis operationalizes
it: spec quality at the Maestro level matters more than implementation speed
at the Worker level; the bottleneck has shifted from intelligence to clarity.

The discipline carries three operational implications that are now committed:

**Spec-first delegation.** Worker invocations carry explicit task specs with
goal, constraints, validation criteria, and an uncertainty protocol. The
agentic-systems synthesis canonicalizes the typed AgentReport as the return
format. The g11 agent-frameworks cluster recommends pydantic-ai as the
orchestration primitive that gives type-safety and provider-abstraction at the
agent level. The g7 harnesses cluster identifies workgraph's JSONL append-only
DAG as the most-liftable session-store substrate.

**Audit-log-as-product, not feature.** The safety-alignment-privacy synthesis
treats per-Worker output provenance as architectural rather than procedural:
which model produced which output, with what tools, against what context, with
what citations claimed. The Marelli reading reinforces this: attribution is
the substrate that makes scientific use of LLM output defensible. The audit log
extends Identity-layer discipline (in the Agent/Identity/Venue vocabulary that
shows up in entrepreneurship and skills clusters) to every Worker invocation.

**Maestro budget discipline.** Hosted Claude tokens are expensive attention,
not expensive tokens. The convention shows up in CLAUDE.md (implicit) and in
multiple syntheses (explicit, e.g., the agentic-systems synthesis's "Maestro
ceiling" framing from Knuth's _Claude's Cycles_). The implication: arrive at
hosted Claude with context gathered and questions sharpened; push well-specified
implementation to local Workers; reserve Maestro tokens for taste, direction,
and plateau-point insight.

### 3. Memory as a load-bearing architectural pillar, not deferred

The memory synthesis (the largest single thematic synthesis by line count) is
the canonical statement. The Garrison framework decomposes memory into two
formal requirements — recursive state maintenance and reliable history access
— and proves that a transformer satisfying both simulates a Universal Turing
Machine with logarithmic overhead. Eleven supporting papers reinforce the
diagnosis from three independent angles (complexity theory, empirical
prompting, architectural alternatives), and the practitioner-side companion
(Mughal on hosted-Claude session degradation) closes the loop.

The architectural answer is a layered memory stack:

- **Layer A** — intra-step latent state (the hidden state opaquely flowing
  through a single Worker forward pass).
- **Layer B** — within-session scratchpad (the durable addressable artifact of
  one task's intermediate reasoning, including alternatives considered).
- **Layer C** — cross-session episodic memory (SQLite + content hashes + git;
  the substrate that lifts the assistant-as-a-whole out of TC0).
- **Layer D** — investigation memory (task-scoped multi-agent shared context,
  Kosmos-style world model, archived to Layer C on close).
- **Layer E** — semantic / knowledge memory (the KnowledgeBase; durable factual
  content with claim-typing, content hashing, and contradiction policy).

The agentic-systems synthesis adds Layer D as the fifth layer (originally a
four-layer pillar) and renames the original semantic layer to Layer E. The g4
memory cluster surveys nine repos and identifies openaugi's two-table SQLite
schema as the closest match to the v0 episodic store. The llm-wiki synthesis
ties Layer E to claim-typing discipline (`[!source]` / `[!analysis]` /
`[!unverified]` / `[!gap]`) and the write-back rule (every task produces both
a deliverable and KB updates).

Three orthogonal rules apply across all layers:

- **Scratchpad is durable** — reasoning tokens are first-class addressable
  artifacts. The o1 anti-pattern (silent truncation of reasoning between turns)
  is forbidden in the Worker protocol.
- **Context is a resource to manage, not a capacity to fill** — the in-context
  cap is intentionally low (16K Phase 2 default); overflow routes through the
  episodic store; explicit bypass is audit-logged.
- **Memory mode is dispatch-time-explicit** — every Worker call carries a
  declared mode (`stateless` / `session_stateful` / `project_stateful` /
  eventually `investigation_stateful`) and a CoT budget; both recorded.

### 4. KnowledgeBase as the semantic memory layer, dual-substrate

The KnowledgeBase (Linus submodule) is committed as the Layer E substrate, with
a dual representation: RDF (rdflib) for entity-and-claim semantics; property
graph (networkx, eventual Oxigraph) for traversal and analytics. The
llm-wiki synthesis names the design discipline: claim-typing, content-hash
provenance, contradiction policy, write-back rule, schema-as-flywheel. The g2
wiki-engines cluster surveys eleven implementations and finds none of them
shaped right for Linus's purposes (all are vault-engines, not memory-pillar
components), but extracts wikiloom's chunk-id derivation, llmbase's operations
registry, TheKnowledge's citation enforcement, and OmegaWiki's SKILL.md
discipline as patterns worth lifting. The g3 wiki-patterns cluster reinforces
the schema-first message and surfaces obsidian-llm-wiki-local's
structured_output.py as immediate Phase 1 lift material. The g5 graph-tools
cluster identifies hyalo as the only Integrate verdict in that group — a Rust
binary that handles schema-validated authoring and transactional link
rewriting — with keppi as the complementary graph-aware retrieval primitive.

Beyond design discipline, two engineering commitments fall out:

- **paper-qa as the retrieval-and-synthesis engine.** The g8 sci-agents cluster
  earns paper-qa the first paper-corpus Integrate verdict in the entire run,
  resolving the "build vs adopt" question for the Phase 2c retrieval layer
  from "build" to "adopt + extend." KnowledgeBase remains corpus-of-record;
  paper-qa sits above the RDF + property-graph substrate.
- **model_prediction as a first-class edge class.** The biological-foundation-
  models synthesis names this load-bearing for any FM-derived KB content (the
  240K-protein BioReason-Pro atlas alone forces it). Each prediction carries
  producing-model + version + confidence + content-hash + validation-tier; the
  same schema serves Group A (FM predictions), Group B (designed artifacts),
  Group C (function annotations), and any future model-derived KB content.

### 5. MCP as the tool-extensibility substrate, fastmcp as the framework

Five independent repos across multiple clusters ship MCP servers (pmetal-mcp,
openclaw's gateway, py3plex-mcp, agentmemory's 51 tools, keppi's 19 tools,
codebase-memory-mcp's 14 tools, ontomics, codesight, fastmcp underneath them
all). The g6 MCP cluster is the highest-density Integrate cluster in the
entire fan-out. The conclusion is overdetermined: MCP is Linus's tool
substrate; fastmcp is the framework; in-house Linus servers are built _on_
fastmcp, not parallel to it. The transport question (stdio vs streamable-http)
is the live operational decision; everything else is settled.

The substrate carries through to four practical decisions:

- The Phase 2a tool registry is a FastMCP server.
- External MCP servers (pmetal-mcp, future paper-qa MCP, ClawBio plugins) are
  composed via `FastMCP.as_proxy()` with Linus middleware applied.
- Tool definitions carry a `deployment` field (`local` / `mcp` /
  `external_api`) that the registry dispatches on. External-API tools get
  HTTP + auth + polling + caching + offline-fallback as the canonical
  execution path.
- The tool registry surfaces are filtered per Worker Role, so the spawner can
  expose tool subsets without re-registering tools.

### 6. Safety-and-privacy as a multi-axis posture, not a single tier framework

The current SAFETY.md tier model addresses OS / filesystem / shell autonomy.
The safety-alignment-privacy synthesis extends it across four orthogonal axes
that none of the others reach:

- **Mechanism** — activation steering and monitoring as first-class
  observability primitives (the Beaglehole RFM-probe is the technique). An
  ActivationHooks stub is in place; the Phase 2 feasibility spike is the
  decision gate.
- **Cultural-empirical** — the hosted Maestro is an empirically-characterized
  object. Linus relies on its epistemic values (transparency, thoroughness)
  and actively counters its prosocial defaults (mirroring, over-hedging,
  default warmth in technical contexts). The dependency is now explicit in
  maestro-protocol.md.
- **Threat-model** — deanonymization of pseudonymous accounts via hosted LLMs
  is real and industrial; every byte crossing the local-to-remote boundary
  accumulates as identity signal. KB content default is `hosted-forbidden`;
  upgrade to `hosted-ok` is an explicit ingest-time decision, audit-logged.
- **Design-policy** — three-tier biosecurity gate (Tier A: residue, Tier B:
  gene, Tier C: whole-genome) on biology generative skills. Caller-invariant
  refusal at the orchestration layer, regardless of intent framing.

The security synthesis adds the supply-chain axis: every dependency is a trust
relationship; hash-pinned requirements, monthly pip-audit, and uv-disposable
envs for experimental packages constitute the operational posture. The
litellm incident is the canonical motivating event.

### 7. Open-source-by-default as a release posture, deferred-commercial as the
arrow ordering

The entrepreneurship synthesis sharpens what the namesakes (Pauling, Torvalds)
implied: if Linus succeeds, the default is open-source release under a "for
science, for society" rationale. The whiteboard pipeline puts business ideas
at the _end_ of the arrow, downstream of "Linus works" and "Linus is
fine-tunable on Dan's corpus." Productization is the last step, not the first.

The corollary is architectural: prefer license-compatible deps, design for
contributor-friendly module boundaries, use public benchmarks rather than
private moats. The g10 finance cluster's AGPL question for OpenBB and the g7
harnesses cluster's license-topology read of origin (AGPL frontend, Apache
backend) both inherit from this posture.

---

## Part II — what is in-flight (the engineering threads)

These threads have committed direction but live measurement remaining. They
are where the Phase 1 and Phase 2 effort concentrates.

### 8. Phase 1c benchmark sweep as the Worker-selection instrument

The infrastructure-foundations synthesis treats `benchmarks/dan_tasks/` as the
load-bearing measurement substrate. Five papers converge on the methodology
("measure the operational thing, not the surrogate"): the speed-and-tok/s
paper, the Practical Guide for Evaluating LLMs, LAB-Bench, BixBench, WHAM.
The convention adopted across syntheses:

- **Open-answer is the headline; MCQ is calibration only.** The Cloning
  Scenario collapse in LAB-Bench is the canonical demonstration.
- **Coverage/accuracy/precision triple, not a single accuracy number.**
  Refusal is a first-class choice.
- **80/20 public/private split with canary string.** LAB-Bench's canary
  string must land in the KB ingestion blocklist before any RAG or fine-tune
  work runs — a Phase 2 obligation.
- **Wh-per-prompt as a tracked axis.** The Google environmental-impact
  methodology gives the recipe; M1 Max powermetrics give the data.

The Phase 1c sweep, per the native-low-bit synthesis, is a four-way comparison
of native-low-bit checkpoints (BitNet 2B4T, Bonsai Ternary 8B, Bonsai 1-bit 8B,
Bonsai Ternary 4B) plus the FP16 Qwen3-coder baselines. The g1 cluster adds
ANE-prefill + GPU-decode as an explicit configuration. The pmetal verdict ADR
collapses several downstream questions.

### 9. Workgraph JSONL + git-worktree-per-Worker as the orchestration shape

The g7 harnesses cluster identifies workgraph's `.workgraph/graph.jsonl`
append-only DAG plus `handler_for_model.rs` dispatch as the most-liftable
orchestration runtime in the entire collection. claude-squad's
git-worktree-per-Worker isolation primitive composes with it: each task node
in the graph maps to a worktree, with the JSONL as the session store and the
worktree as the working directory. The four-component design (JSONL DAG,
handler-for-model dispatch, heartbeat-plus-PID supervisor, validation
convention) ports to Python in 200-500 lines per component; the Rust crate
does not get vendored.

The worktree convention has known failure modes that have been encoded as
discipline rules: base-SHA pinning before fan-out; branch preservation after
worktree removal (do not `git branch -D` immediately); Edit-tool path
resolution quirks that argue for `Bash(cd <worktree-path> && ...)` from
inside agents; sequential agent dispatch with file-level partitioning as the
simpler default when isolation is not load-bearing.

### 10. Agent spawner with Role as first-class type

The agentic-systems synthesis canonicalizes Role as a typed object:
`{role_id, capability_set, memory_access_tier, critic_eligible}`, serializable
to YAML, enforced at dispatch. The g7 cluster's codebuff agent-definition
contract extends it with `system_prompt`, `tool_names`, `spawnable_agents`,
`output_mode`, `handle_steps`. The g11 cluster's pydantic-ai Agent provides
the runtime substrate.

Three to seven named roles per non-trivial workflow is the practical sweet
spot. Kosmos at two roles (data-analysis + literature-search) bounds it from
below; TradingAgents at seven roles bounds it from above; WikiAutoGen's
four-viewpoint critic block is the corresponding template for the review
side. The Stony Brook QuantAgent's four-specialists + integrator with
majority-with-confirmation is the cheapest default.

Per-stage validation hooks are exposed by the spawner: pre_dispatch,
post_synthesis, post_execution. The execute → detect → fix pattern from
Sketch2Simulation is the required default for any Worker producing an
executable artifact. The Practical Guide's component-level evaluation
argument lands here: orchestration-layer components need their own metrics.

### 11. Output-side citation discipline + reproducibility-bundle convention

The output interface for any Linus skill that produces an artifact a human
will consume converges on two patterns across syntheses:

- **Typed structured prediction wrapping free-text rationale.** The
  BioReason-Pro shape is the reference: structured result with confidence and
  evidence, plus a `rationale` field for human review. The
  function-annotation-discovery synthesis canonicalizes this for biology
  skills; the agentic-systems synthesis (via Trading-R1) confirms it
  generalizes to non-biology domains.
- **Reproducibility bundle alongside the report.** ClawBio's
  `commands.sh` + `environment.yml` + `checksums.sha256` pattern is the worked
  example. The g9 bio cluster names it explicitly; the function-annotation-
  discovery synthesis seconds it. Any skill whose output might end up in a
  paper or a downstream pipeline should ship the bundle by default.

Citation discipline rides alongside: every claim carries provenance, every
artifact carries `validation_tier`, every model-derived KB entry carries the
`model_prediction` edge.

### 12. Phase 2 chat surface + KB integration with synthesis layer

The roadmap MVP commits to a Streamlit chat UI grounded in KnowledgeBase, with
Maestro-side synthesis compressing multi-Worker outputs into balanced
bullets + prose with citation drill-down. Default in-context cap 16K; explicit
bypass logged. The cognitive-throughput pair (Zheng-Meister, Sauerbrei-
Pruszynski) frames why the synthesis layer matters: parallel Worker fan-out
generates throughput gain only when synthesized into review-ready outputs
before reaching Dan's conscious channel.

---

## Part III — what is speculative (research directions and candidate spikes)

These threads have plausible upside but live measurement gates before they
become commitments. They are explicitly Phase 6+ in most cases.

### 13. The combinable-bets: Kimi-K2 × flash-streaming × BitNet/Bonsai

The native-low-bit synthesis names this as the most consequential strategic
move surfaced by the corpus. Three sub-threads compose:

- **BitNet/Bonsai built the 1-bit substrate** (existence proof through
  deployable artifact).
- **Flash-streaming made >32 GB MoE feasible on consumer Apple Silicon**
  (flash-MoE's 397B at 5.74 tok/s on 48 GB M3 Max as the existence proof).
- **Kimi-K2 is the candidate model that combines both for Linus** (1.04T-MoE,
  32B active, MLA, 128K context, MuonClip-trained, Modified MIT licence,
  sized to fit M1 Max + 600 GB SSD at int4 or ternary).

The two ADR seeds: Phase 6 Qwen3 → Kimi-K2 base swap (gated on agentic
benchmark deltas and streaming feasibility); Phase 8 1-bit Linus-flavored
Kimi-K2 variant (gated on the Phase 6d streaming-feasibility measurement).
The Phase 6d spike is the most consequential measurement in the entire
low-bit-Apple-Silicon arc.

### 14. Idea-to-reality as a Phase 7+ skill class

The llm-hardware-design synthesis treats the QiMeng family (15 papers, 4
repos) plus Sketch2Simulation as the methodology corpus for "LLMs producing
artifacts that downstream non-LLM actors accept and realize." The
discipline — planner / coder / verifier with downstream actor doing real work
— recurs across kernel codegen, HDL generation, CPU microarchitecture, OS
configuration, compiler back-ends, and tensor-program transcompilation.

The cluster's strategic insight: **the oracle is the unit of effort being
amortized, not the training algorithm**. CodeV-R1's testbench generator is
the dominant contribution; the RLVR loop is the consumer. SALV's
signal-extraction is the dominant contribution; the customized DPO loss is
conceptually simple. For Linus this turns the Phase 7 commitment from
"design a fine-tune lane" to "build the verification surface for the chosen
domain first."

The Phase 7+ ADR seeds catalogued in the llm-hardware-design synthesis are
substantial in number (eleven seeds named). The biggest commitment is the
idea-to-reality skill class itself; the most actionable canary is
QiMeng-SALV-on-MLX as a sub-week Apple Silicon RLVR reproduction.

### 15. Memory-substrate alternatives — Coconut, minGRU, TTT

The memory synthesis surfaces three architecturally distinct substrates for
moving beyond single-pass transformer Workers:

- **Latent continuous reasoning** (Coconut) — feed the last hidden state back
  as the next input embedding rather than decoding to a discrete token.
- **Parallel-trainable minimal recurrence** (minGRU/minLSTM) — strip the
  gates, run via prefix-sum scan, 175-1361× faster training.
- **Test-time parametric updates** (Akyürek-style TTT) — fit a per-task LoRA
  on synthetic data built from few-shot demonstrations.

Each is a Phase 6+ spike with a documented decision rule. The minGRU MLX port
spike is the smallest. The TTT viability spike is medium-sized (10 ARC tasks,
mlx-lm LoRA, under 5 min/task gate). Coconut's MLX-portability check is the
prerequisite for the substrate experiment. The Phase 8 north star — minGRU
with BitLinear gates, possibly composed with flash-streaming — is the most
extreme hardware-friendly substrate the corpus collectively points at.

### 16. Self-improving Worker via QiMeng-discipline + Dan-task oracle

The llm-hardware-design synthesis argues that the QiMeng family's RLVR
discipline transfers to any domain with an automated verifiable oracle. For
Linus the candidate oracles are: pytest-passing Python (easy oracle, broad
relevance); ruff-clean Python (easy oracle, narrow improvement);
paper-qa-faithful answers (harder oracle, high Dan relevance); bioinformatics
pipeline correctness on small synthetic inputs (high oracle-build cost, high
relevance). The bioinformatics oracle is the highest-leverage long-term
target but requires Dan to author small synthetic test inputs first — a
Phase 7 build investment.

The training compute cost is non-trivial (~2,656 A100-GPU-hours for the
CodeV-R1 RLVR loop) and forces a hybrid posture: LoRA-only RLVR on M1 Max as
the inner loop; occasional cloud A100 bursts for occasional full RL runs;
the fine-tuned LoRA adapter runs locally afterward. The compromise echoes
the Maestro budget discipline: hosted resources as expensive teacher, local
substrate as runtime consumer.

### 17. Biology Phase 7 as the highest-leverage domain commitment

The biological-foundation-models synthesis surveys eight Group A papers and
identifies five Phase 7 skill candidates (REBEAN first, then Bacformer +
RiNALMo, then AlphaGenome + Evo 2 hybrid, with LucaOne deferred). The
function-annotation-discovery synthesis adds protein function prediction
(BioReason-Pro vs ProtHGT vs Horizyn-1, benchmark-informed selection) and
DNA pathway reasoning (BioReason). The generative-biology synthesis adds
codon optimization (Trias), BGC-to-metabolite prediction (DeepSeMS), metal
mutation scoring (mCSM-metal as the first external_api_tool case), and
text-to-sequence generation (GenNA). The g9 bio cluster confirms bioSkills
as the inaugural Phase 7 skills bundle; the g8 cluster pairs it with
scientific-agent-skills (~573 total skills).

The generalist × specialist FM pairing sequence (per the biology-Phase7
roadmap that's referenced from multiple syntheses): Trias + GenNA (sequence
design); REBEAN + DeepSeMS (metagenomic discovery); Bacformer + DeepSeMS
(bacterial genome → BGC → metabolite). mCSM-metal + DISCO and AlphaGenome +
GenNA are Phase 8 pairs pending Apple-Silicon plumbing.

Three biosecurity tiers (A: residue, B: gene, C: whole-genome) gate the
generative side; the residue-level tools are agentic-executable, the
gene-level tools require per-invocation Dan sign-off, the whole-genome tools
require sign-off plus out-of-band review.

### 18. The literature-intelligence stack as Linus's first commercial surface

The entrepreneurship synthesis names this concretely: paper-qa (engine) +
bioSkills (~438 domain skills) + scientific-agent-skills (~135 broader sci
skills) + Bacformer (FM grounding) + LAB-Bench (rigorous public benchmark) +
KnowledgeBase (the indexed corpus). All components earn independent
verdicts; together they constitute a working biotech literature-intelligence
substrate that is closer to ready than the previous planning assumed.

The differentiation is genuine: Dan understands the science, so output
quality is evaluable in a way a generalist prompt-seller cannot match.
Combined with local-first auditability (sovereignty mechanism) and citation
grounding, the offering is structurally unlike most AI side-hustle content.
The whiteboard arrow ordering remains: build Linus first; commercialize only
after it is demonstrably useful.

The Canteen/Agora signal (2026-05-09 hackathon outreach) is a first
commercial-surface inbound that exercises the OpenAI-compatible-endpoint
substrate as a forcing function for Phase 2 MVP rather than a commercial
commitment. The four RFB ideas (reasoning-traces-as-product,
Hyperliquid Whale Index, slash-bonded copy-trading, translation-as-alpha)
are commercial-substrate evidence regardless of which (if any) is pursued.
The x402 protocol intersection is seeded as a future ADR.

The Agent / Identity / Venue layered decomposition (from Canteen) generalizes
beyond crypto: any future Linus surface emitting attributable agent decisions
faces the same three-layer question. The framing is useful as an internal
lens before it becomes a productized vocabulary.

---

## Part IV — the crossings (where threads cut each other)

The threads above are not independent; the most interesting structure of the
corpus lives at the intersections.

### Crossing A — Memory × Inference (Layer A meets the substrate)

The memory synthesis names Layer A (intra-step latent state) as the layer
that today is "whatever the underlying transformer's hidden state happens to
be — opaque, discarded between turns, never named." The
safety-alignment-privacy synthesis's activation-hooks stub (Beaglehole RFM
probes) is the technique that turns Layer A from a documentation entry into
an instrument. The native-low-bit synthesis's substrate experiments
(BitNet/Bonsai, minGRU MLX port, Coconut latent recurrence) are the substrate
candidates that, if successful, change what Layer A actually contains. The
crossing is the place where memory architecture, low-bit inference, and
safety/observability cohere — and where the Phase 6+ substrate experiments
are scoped.

### Crossing B — Agentic Systems × Memory × KB (Layer D meets the spawner)

Layer D (investigation memory) is the bridge between the agentic-systems
synthesis (Kosmos-style task-scoped shared context) and the KB layer (Layer E
permanence). Investigation memory is shared read/write across agents in one
investigation, partitioned by investigation_id, archived to Layer C on close.
The agent-spawner consumes Layer D as its multi-agent shared substrate; the
KB consumes Layer D's archived state as content. The crossing is where the
Phase 3 fan-out architecture and the Phase 3 KB enrichment converge.

### Crossing C — Skills × Safety × Domain (biosecurity tier gates the catalog)

The biology Phase 7 skill catalog (bioSkills + scientific-agent-skills + ~5
specialist FMs) is the first domain commitment large enough to force the
biosecurity-tier discipline to be load-bearing rather than aspirational. The
generative-biology synthesis (Group B's phages, DISCO, etc.) is the
sharpest case: the recipe is general, the substrate FM is open, the
dual-use surface is real. SAFETY.md's Tier A/B/C policy is committed; the
implementation requires every biology tool registry entry to carry a
`biosecurity_tier` field; Workers enforce the gate at dispatch time. The
crossing is where the catalog grows from "interesting skills" to "operational
skills with consequence."

### Crossing D — Hardware-design × Biology × Self-improvement (verifier-first
discipline)

The llm-hardware-design synthesis's "the oracle is the unit of effort being
amortized" generalizes to biology. The most plausible Phase 7 biology
verifiers (BLAST percent identity, ESMFold pLDDT, ClinVar pathogenicity,
tissue-specific eQTL direction-of-effect) are biology's analogs of QiMeng's
RDKit/iverilog oracles. The crossing argues that Phase 7 biology skill
development should start with the verifier, not the meta-prompt. It also
sharpens the Phase 6 fine-tuning posture: build the oracle first, then
RLVR-train against it. The Phase 6c spike on M1 Max measures whether
LoRA-only RLVR with adaptive DAPO is tractable in single-digit-day wall time.

### Crossing E — Open-source posture × Commercial surface × Architecture

The entrepreneurship synthesis's release-posture commitment (open-source by
default) carries architectural consequences (license-compatible deps, public
benchmarks, contributor-friendly module boundaries) that interact with the
g10-finance AGPL question (OpenBB), the g7 origin license topology (AGPL
frontend, Apache backend), and the broader question of which paid APIs
become forbidden in the critical path. The crossing is where the commercial
surface (if and when it arrives) meets the architectural constraints
(designed-in from Phase 2 to avoid retrofits in Phase 8).

### Crossing F — Maestro/Worker × Cognitive throughput × Human-team rhythm

The humans-teams-performance synthesis's three-timescale braid (Zheng-Meister
intra-second, Harvey team-episode, Güllich intra-career) is the most ambitious
cross-timescale claim in the corpus. The Maestro/Worker discipline shows up
as the recurring solution to bandwidth-limited high performance at all three
scales. The crossing is normative as much as architectural: Linus should not
crowd out Dan's cross-domain breadth time; the orchestration layer should
expose a goal_orientation field; sessions should follow a reflexive bookends
+ exploratory middle rhythm; the skills synthesis's "moat" should be
re-framed as cross-domain expertise rather than domain expertise alone.

---

## Part V — the gaps (where the corpus is thin)

These are places where the synthesis corpus surfaces a need but does not
resolve it; they are candidates for future reading or commissioned work.

### Gap 1 — RNA-specific reasoning is absent

The function-annotation-discovery synthesis flags this explicitly. RiNALMo
covers RNA representation; no Group C paper extends BioReason-style shells
over RiNALMo for ncRNA function, or builds a Pathway-GPT typed-prediction
companion over RNA-binding-protein networks. The gap is a Phase 7 candidate
direction once Group A bio FMs are operational.

### Gap 2 — Tissue / spatial-transcriptomic FMs are missing

The function-annotation-discovery and biological-foundation-models syntheses
both note this. PertFormer is cell-level; nothing operates at organoid /
tumor-microenvironment / spatial-architecture scale. Spatial transcriptomics
FMs are the obvious next entry.

### Gap 3 — Maestro-class eval suite distinct from Worker eval

The llms-in-science synthesis (Knuth case) argues categorically for a
Maestro-class tier in `benchmarks/dan_tasks/` distinct from Worker
benchmarks. A small Hamiltonian-decomposition or Cayley-graph cycle puzzle
would formalize the role distinction. The Maestro transition (Phase 8 north
star) is gated on this measurement instrument existing.

### Gap 4 — A Worker-values empirical extraction pipeline

The safety-alignment-privacy synthesis suggests a Clio-style extraction over
Linus's own audit log to characterize Worker value expression. Detects
behavior drift after fine-tunes or quantization changes. Phase 6/7
capability; scoping it now lets the audit log preserve the data the
extraction will need.

### Gap 5 — A red-teaming gate for biology Workers

The dual-use red-team probe set (20-40 prompts from the Soice et al.
exploited categories) is a Phase 1 benchmark deliverable gating any biology
Worker or fine-tune. The probe set is sensitive enough that it may warrant a
separate restricted repo.

### Gap 6 — Open-source EDA toolchain for the idea-to-reality skill class

The llm-hardware-design synthesis is explicit: the production end-to-end
pipelines (Synopsys Design Compiler, Cadence Genus, Aspen HYSYS) are closed-
source and Apple-Silicon-incompatible. Linus's realistic envelope stops at
the open-source segment (Yosys, iverilog, clang/nvcc/mlx, open-source process
simulators where they exist). This is a structural ceiling the Phase 7 ADR
should be honest about.

### Gap 7 — A non-trivial multimodal local capability

Several syntheses (QuantAgent's vision-LLM-on-rendered-chart, claude-prism's
LaTeX rendering for paper drafting, generative-biology's microscopy
generation) flag patterns that would compose well with a strong local
multimodal model. Phase 5+ when local vision capability matures (Qwen2.5-VL
or successor on M1 Max). Until then, the patterns are filed as
study-material.

---

## Part VI — phased synthesis (what falls when, in one place)

A rough phase mapping consolidating the threads above:

**Phase 1 (now closing):**

- Native-low-bit benchmark sweep (Bonsai Ternary 8B, Bonsai 1-bit 8B, BitNet
  2B4T, FP16 baselines) under unified `dan_tasks/` methodology.
- pmetal verdict ADR (inference backend selection).
- promptfoo baseline against Ollama Workers; LAB-Bench MCQ-with-refusal +
  BixBench three-tool agent harness as Phase 1 anchors.
- LAB-Bench canary string in KB ingestion blocklist (hard obligation).
- minGRU MLX port spike, TTT viability spike, CoT-gap fingerprint
  measurement.
- fastmcp smoke test confirming round-trip with Linus tools.
- Worktree fan-out discipline + canary-agent probe pattern.

**Phase 2 — Linus MVP:**

- OpenAI-compatible orchestration backend (FastAPI + router + MCP tool
  registry on streamable-http, with `deployment` field per tool).
- pydantic-ai Agent as orchestration primitive; codebuff agent-definition
  contract as the Role schema.
- Memory pillar v0: SQLite episodic store (openaugi-shaped schema), audit
  log writer, `linus.memory.episodic.*` tool family, scratchpad facade,
  dispatch-layer prefix loader with `memory_mode` + `cot_budget` primitives.
- Worker registry with `scratchpad_durability` capability tag and per-Worker
  CoT-gap overrides.
- Streamlit chat UI with KB retrieval + balanced-bullets-plus-prose
  synthesis layer + citation drill-down.
- Output synthesis convention: typed structured prediction wrapping
  free-text rationale; reproducibility bundle for any publishable artifact.
- KB integration v1 with dual substrate (RDF + property graph) and quality
  scorecard surfaced in retrieval context.
- KB substrate paper-qa adoption (adopt + extend).
- ARC-AGI memory diagnostic (stateless vs session_stateful, 50-100 tasks).
- SAFETY.md additions: stylometric/identity-leakage tiering;
  Maestro-values dependency declarations.
- `docs/knowledge-mining-surface.md` (entrepreneurial-surface planning
  artifact).
- ActivationHooks Phase 2 feasibility spike (decision rule: <5ms/token →
  Phase 2 implementation, otherwise Phase 6 deferral).

**Phase 3 — Knowledge & Parallel Agents:**

- Agent spawner with Role-as-first-class-type, AgentReport as canonical
  inter-agent message, per-stage validation hooks.
- Parallel-Worker fan-out with branch-per-Worker coordination; investigation
  memory (Layer D) at `~/.linus/investigations.db` with `investigation_id`
  partitioning.
- Hybrid retrieval upgrade (qmd fusion math: RRF k=60 + query-expansion
  weighting + position-aware rerank blend).
- KB lint command (llm-research-wiki LINT pattern over hyalo substrate).
- Vectorless-style shell-command tools (`kb_ls`/`kb_cd`/`kb_cat`/...) as
  navigation surface complementary to vector retrieval.
- Dan task suite re-run: Linus-with-RAG vs Linus-without-RAG vs hosted
  Claude.

**Phase 4 — Data Sovereignty:**

- Kiwix native (Full English Wikipedia + topical ZIMs).
- Kolibri (Khan Academy courseware + parallel benchmark surface).
- ProtoMaps PMTiles (planet-scale OSM).
- OpenGenome2 mirror + AlphaGenome evaluation datasets + DIAMOND DeepClust
  cluster representatives + Bacformer 1.3M-MAG cache as biology mirrors.
- Obsidian vault integration (stretch).

**Phase 5 — Interface Refinement:**

- openclaw as front-end pointed at Linus endpoint.
- VS Code polish; terminal path.
- Carbon atom branding.
- Laminar observability target (deferred to x86 Linux VM or Mac Studio
  tier).
- claw-code-local landing (Rust+MCP Worker harness).
- Claude Code plugin marketplace as Phase 5+ distribution channel.

**Phase 6 — Fine-Tuning:**

- Continued pretraining LoRA on ~1M tokens KB; instruction-tuning LoRA;
  optional preference alignment.
- BitDistill spike (10B-token continued pretraining feasibility).
- Flash-streaming evaluation on Linus-branded 30B+ or Kimi-K2 at int4 /
  ternary.
- TTT-as-episodic-consolidation spike (conditional on TTT viability).
- Coconut substrate experiment (conditional on MLX portability).
- MuonClip ablation (Muon + QK-Clip vs Muon vs AdamW on LoRA).
- DSPy BootstrapFewShot → LoRA demonstrations experiment.
- Memory-mode-specific fine-tuning targets (stateless / session_stateful /
  project_stateful).

**Phase 7 — Skills & Autonomy:**

- Inaugural skills bundle: bioSkills + scientific-agent-skills (~573 total),
  with namespace ADR for overlaps.
- Generalist × specialist FM pairs: Trias + GenNA, REBEAN + DeepSeMS,
  Bacformer + DeepSeMS as Phase 7-tractable.
- mCSM-metal as first `external_api_tool` deployment.
- Idea-to-reality skill class: planner / coder / verifier discipline with
  per-domain verification surface as the dominant build cost.
- Domain skills emerging from usage: genomics-pipeline, paper-to-script,
  plot-style-consistency, cluster-label-propose.
- SAFETY.md autonomy graduation criteria.

**Phase 8 — Beyond MacBook:**

- Native Linus app (SwiftUI or Tauri); iPhone/iPad companion nodes; Mac
  Studio peer; Vision Pro experimentation.
- 1-bit / ternary Linus-flavored Kimi-K2 (DEC-0056 seed; ~130-205 GB total,
  ~44-88 MB/token streamed; comfortably inside Phase 8 territory).
- minGRU × BitNet × flash-streaming cross-product (the most extreme
  hardware-friendly substrate the corpus points at).
- Maestro transition: Linus passes Maestro-class eval suite within 10
  percentage points of hosted Claude on Dan's domain tasks.

---

## Closing observation

The most striking thing about the 27-synthesis corpus, read end-to-end, is
how consistently the same shape recurs: **structure of the work matters more
than the intensity of the work, and the structure is what compounds**.
Memory architecture compounds across sessions where flat context does not.
Tool registry composition compounds where bespoke per-tool protocols do not.
Citation discipline compounds where free-form attribution does not.
Cross-domain expertise compounds where domain depth alone does not. The
Algorithm's deletion discipline compounds where additive feature work does
not. The Maestro/Worker boundary compounds where blended human-AI workflow
does not.

That structural argument is the unifying claim of the corpus, repeated at
many scales by many syntheses. The roadmap and the architecture are the
operationalization of that argument. The landscape above is the cross-cut
that makes it visible.
