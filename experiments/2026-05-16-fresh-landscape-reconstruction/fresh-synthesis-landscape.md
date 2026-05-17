# Fresh Synthesis Landscape — reconstruction from syntheses

_Composed 2026-05-16 from the 27 synthesis documents without consulting any
existing landscape or top-questions files. This is the per-synthesis rollup
asking: what are the 27 syntheses individually, how do they overlap, and
where should the bins be drawn?_

## What this document is

The corpus has 15 thematic syntheses and 12 cluster (repo-group) syntheses,
27 in total. The cluster syntheses pair with thematic syntheses but not 1:1
— some thematic syntheses have a primary cluster anchor; some cluster
syntheses get cited by multiple thematic syntheses; one thematic synthesis
(humans-teams-performance) has no cluster anchor at all. The total-landscape
is the cross-corpus rollup; this document is the per-doc rollup that
explains how the 27 fit together.

Five organizing axes are useful:

- **Substrate syntheses** — the load-bearing infrastructure threads.
- **Behavioral syntheses** — how agents work, what their interaction
  patterns are.
- **Domain syntheses** — biology, biotech, generative biology, function
  prediction, etc.
- **Measurement and meta** — benchmarks, evaluation, philosophy.
- **Commercial-surface** — entrepreneurship.

The taxonomy is approximate. Several syntheses cross axes; the most
load-bearing ones (memory, agentic-systems) are deliberately substrate-and-
behavioral hybrids.

---

## Bin 1 — Substrate syntheses (the infrastructure load-bearing layer)

### memory-synthesis.md (thematic)

The largest single synthesis by line count and arguably the most consequential.
Built on Erik Garrison's January 2025 essay plus eleven supporting paper notes
spanning complexity theory, empirical prompting, and architectural
alternatives. The canonical statement of why memory is a Phase 2 load-bearing
pillar rather than a deferred concern.

Headline claim: **single-pass transformers live in TC0; the escape into
P-class expressivity requires reliable history access and recursive state
maintenance**. The five-layer pillar (A: intra-step latent, B: within-session
scratchpad, C: cross-session episodic, D: investigation memory, E:
semantic/knowledge) is the architectural decomposition. Three discipline
rules ride alongside: scratchpad as durable artifact, context as managed
budget (16K Phase 2 default), memory mode dispatch-time-explicit.

The synthesis defines a primary cluster anchor in **g4-memory** (the
agent-persistent-memory cluster) which provides openaugi's two-table SQLite
schema as the closest Phase 2 implementation match. It is heavily
cross-referenced from agentic-systems (Layer D investigation memory was
added in response to Kosmos-style task-scoped shared state), llm-wiki
(Layer E disciplines: claim-typing, content hashing, write-back rule),
g7-harnesses (workgraph JSONL as session-store), llms-in-science (Knuth's
plan.md trajectory as durable scratchpad), safety-alignment-privacy (Layer A
as activation-observability surface), and native-low-bit (substrate
experiments live at Layer A).

### infra-foundations-synthesis.md (thematic)

The reference-anchor synthesis. Holds the Transformer paper, the Flow Matching
textbook, PAN as world-model reference, Google's environmental-impact paper,
WHAM, plus the modern-Transformer-recipe substitutions (RoPE, RMSNorm,
SwiGLU, GQA), four LLM architecture surveys, four practitioner architecture
guides, the DreamZero + EgoScale world-action-models extension, and the
Kimi-K2 backfill on MLA + MoE topology + MuonClip optimizer + token-efficiency
framing.

The synthesis's role is to be the citation everything else implicitly uses.
Its contribution is taxonomic rather than load-bearing: it names what is
foundational reference material vs methodology reference vs watch-the-field
material. The "world model, four ways" disambiguation (PAN's visual-physical
simulator vs WHAM's game-state video-token simulator vs Kosmos's symbolic-
scientific shared state vs Linus's durable factual + episodic context) is
sharp.

The "capability-first measurement" thread (WHAM + Practical Guide for
Evaluating LLMs + speed-and-tok/s) is folded in here. LAB-Bench and BixBench
were moved here from the function-annotation-discovery synthesis in
2026-05-05 because the load-bearing contribution is methodological. g5
graph-tools is the primary cluster anchor (hyalo + keppi + py3plex + dlt +
OptimusKG).

### native-low-bit-apple-silicon-synthesis.md (thematic)

The operational substrate synthesis. Four sub-threads: BitNet research line
(seven papers, Microsoft Research, 2023-2025); Bonsai productized line
(PrismML 2026); larger-than-RAM streaming (LLM in a Flash + Flash-MoE);
Kimi-K2 frontier-MoE candidate (Moonshot AI 2025-07).

Headline claim: the trajectory from "1-bit LLMs are possible in principle"
to "MLX-native Apache-licensed downloadable native-ternary 8B checkpoint" is
~28 months; the substrate is now real. Combinable-bets thesis: Bonsai built
the 1-bit substrate; flash-streaming made >32 GB MoE feasible; Kimi-K2 is
the candidate that combines both. Two ADR seeds named (Phase 6 Qwen3 →
Kimi-K2 base swap; Phase 8 1-bit Linus-flavored Kimi-K2 variant).

g1-apple-silicon is the primary cluster anchor (pmetal, mlx-flash, flash-moe,
BitNet, Bonsai-demo, ANE, autoresearch, autoresearch-mlx). The synthesis
makes the unusual move of explicitly naming MLX as the convergence point and
identifying the MLX ternary kernel gap as the most tractable Linus
contribution opportunity in the entire corpus.

### llm-wiki-synthesis.md (thematic)

Built on Karpathy's April 2026 LLM Wiki gist, Rohit v2's gist, the community
response (485 comments), and Dan Woods' autoresearch / flash-moe report.

Headline claim: **compile-don't-retrieve** as the architectural distinction.
RAG finds chunks and re-derives on every query; a compiled wiki has already
done the synthesis. The framework's load-bearing operational contributions:
the three-layer architecture (raw / wiki / schema), the memory lifecycle
(confidence decay, supersession), typed knowledge graph over flat pages,
hybrid retrieval (BM25 + vector + graph traversal), claim typing
(`[!source]` / `[!analysis]` / `[!unverified]` / `[!gap]`), content hashing
for staleness detection, write-back rule, quality gate at ingest, schema as
flywheel, two-layer architecture (central wiki + project-specific), red-link
prioritization.

g2-wiki-engines is the primary cluster anchor (eleven repos covering wiki
engine implementations — link, llmwiki, llmbase, llmwiki-cli, wikidesk,
wikiloom, wikimind, OmegaWiki, swarmvault, synthadoc, TheKnowledge). g3-wiki-
patterns is the companion cluster (seven more repos covering schema and
build patterns — agentic-wiki-builder, AgenticResearchWiki, llm-research-
wiki, llm-wikidata, atomic-knowledge, beever-atlas, obsidian-llm-wiki-local).
Both clusters net out 18 LLM Wiki repos, all Study — the wiki engines are
shaped for personal vaults, not for the memory-pillar of a Maestro/Worker
orchestration backend.

### security-synthesis.md (thematic)

Anchored on the litellm 1.82.8 supply-chain attack, genomics data sovereignty
concerns, and the NIST CSF v1.1 framework. Sources include NIST SP 800-207
(zero trust), SP 800-171r2 (CUI), NCSC China Genomics, HHS Cyberthreats to
Biotech, Foley Biotech IP Guide, NCCoE Genomics Workshop.

Headline claim: Linus's current posture (SAFETY.md tiered autonomy) is
well-designed for what it addresses but leaves five gaps: supply chain
attacks, prompt injection, dependency auditing, network egress, genomics data
sovereignty. The recommended response is a six-axis posture (code provenance,
input integrity, internal behavior, hosted-layer characterization,
output-as-identity-signal, dual-use refusal) extended by the
safety-alignment-privacy synthesis.

DEC-0024 (hash-pinned deps + monthly pip-audit + uv-disposable envs) is the
operational core. The dependency philosophy ("every dependency is a trust
relationship") is codified in CLAUDE.md.

### safety-alignment-privacy-synthesis.md (thematic)

The four-axis extension of the security synthesis: mechanism (Beaglehole RFM
activation probes), cultural-empirical (Anthropic Values in the Wild),
threat-model (Swanson et al. deanonymization), design-policy (Soice et al.
dual-use biotech). Plus the Anthropic RSP v3.0 + Claude's Constitution
benchmark thread.

Three resolved decisions: DEC-0047 biosecurity tier control (A/B/C); DEC-0053
KB → hosted-Maestro flow policy (hosted-ok / hosted-forbidden); DEC-0054
ActivationHooks stub.

The synthesis's most original contribution is the activation observability
framing: model-internal state should be a first-class observation surface
for the orchestration layer, not opaque. The Phase 2 feasibility spike
against Llama-3.1-8B-4bit or Qwen3-7B via mlx-lm has a clean decision rule
(<5ms/token overhead → real implementation; otherwise → Phase 6).

---

## Bin 2 — Behavioral syntheses (how agents work, interact, decide)

### agentic-systems-synthesis.md (thematic)

Ten paper notes spanning multi-agent architectures: Kosmos (12-hour
autonomous research agent), Boiko/Gomes (foundational chemistry agent),
BioGuider (bioinformatics documentation), Sketch2Simulation (flowsheet
multi-agent), TradingAgents, Fundamentals of LLM Agents, Practical Guide
for Evaluating LLMs, two QuantAgent papers, WikiAutoGen.

The eight cross-cutting threads form the canonical agent-architecture
vocabulary the corpus operates in:

1. Role specialization at the right granularity (3-7 roles per non-trivial
   workflow).
2. Structured inter-agent communication promoted to first-class (typed
   AgentReport).
3. Structured shared state as antidote to multi-step drift (Layer D
   investigation memory).
4. Validation as per-stage spawner primitive, not end-of-pipeline check
   (execute → detect → fix).
5. Critic tier as model-level Maestro/Worker inside a single workflow
   (writer LMs cheaper, critic LMs stronger).
6. Tool binding via per-tool documentation, not just signatures.
7. Hosted-frontier-model dependency as the elephant; Kimi-K2 narrows the
   gap.
8. Agentic-system theory (regret bounds, MDP formalism) as a first-class
   design input.

Resolved decisions include Role as first-class type (DEC-0050), AgentReport
as canonical inter-agent message (DEC-0051), per-stage validation hooks in
the spawner.

### skills-and-practices-synthesis.md (thematic)

Built on five X/Twitter practitioner threads (May 2026) — Claude Cowork best
practices, claw-code "Stop Staring at the Files," $312/Day Claude skills,
Top 50 Claude skills, Cline description — plus the Anthropic-internal
Claude Code playbook.

Headline claim: **the bottleneck has shifted from intelligence to clarity**.
Agents can execute; humans must still decide what to build, decompose it
correctly, and design the coordination system. Ten Top practices distilled:
manifest files per context, encode standards in files not prompts, define
end state + constraints + uncertainty protocol, always request a plan
before execution, scope context to minimum, batch related work, use
subagents deliberately for independent parallel subtasks, architectural
clarity > execution speed, externalize to version-controlled files, taste
and conviction as non-commoditized inputs.

The Anthropic-internal cross-check (data infrastructure, product
development, security engineering, inference, etc.) confirms the patterns:
detailed CLAUDE.md as predictor, self-sufficient verify loops, custom slash
commands, parallel Claude Code instances per repo, end-of-session
documentation rituals.

g11-agent-frameworks is the primary cluster anchor (pydantic-ai, dspy,
superpowers, gptme, huginn, Agent-Skills-for-Context-Engineering, promptfoo,
lmnr). ClawBio added 2026-05-10 as worked precedent for the
skills-as-shippable-bundle archetype (per-skill tests, reproducibility
bundle, conformance linter, Claude Code plugin marketplace distribution).

### humans-teams-performance-synthesis.md (thematic)

Two non-AI papers — Güllich on how high human performance is acquired
(34,000+ adult top performers; pooled effect sizes for multidisciplinary
breadth and gradual progress d ≈ 0.39–0.58) and Harvey et al. on innovation
team learning rhythm (102 + 61 teams; reflexive bookends + exploratory
middles).

Headline claim: structure of practice dominates intensity of practice across
every timescale; the Maestro/Worker metaphor holds at three timescales (the
~10-bit/s conscious channel above the ~10⁹ bit/s sensorimotor substrate from
Zheng-Meister; team-episode rhythm from Harvey; intra-career breadth-then-
depth from Güllich).

VISION.md update (S39 resolved): deliberate multidisciplinary time
allocation as a design practice. Worker-spec `goal_orientation` field
deferred to Phase 3 spawner spec. Session-rhythm health metric still open.
Skills synthesis "domain expertise as moat" → "cross-domain expertise as
moat" still pending.

No primary cluster anchor. The synthesis's contribution is interpretive — it
sharpens existing claims rather than introducing new substrates.

### llms-in-science-synthesis.md (thematic)

Built on the Binz et al. 2025 PNAS Perspective (four-perspectives framework:
Schulz collaborator, Marelli accountability, Botvinick & Gershman roadmap
agency, Bender capability skepticism) and Knuth's _Claude's Cycles_ (the
strongest empirical case for the Schulz frame; Knuth's hand-construction
problem solved in ~1 hour and 31 explorations with Claude Opus 4.6).

Headline claim: **Linus is itself a position-taking artifact in the Binz
debate**. By existing, Linus commits to Schulz on open-source, Bender on
limits of hosted-frontier dependence, Marelli on attribution, Botvinick &
Gershman on roadmap agency. VISION.md now explicitly cites the framework
(S36 resolved); maestro-protocol.md has a "Philosophy" section naming the
blend (S37 resolved).

Knuth as Maestro-class workload demonstration. plan.md forced-documentation
pattern as durable scratchpad reference. Translation-as-moat thread (the
Canteen analog for non-English scientific corpus work).

g8-sci-agents is the primary cluster anchor (paper-qa, aviary, ldp, robin,
ether0, BixBench, LAB-Bench, finch, scientific-agent-skills,
ibmdotcom-tutorials, claude-prism, Sketch2Simulation).

---

## Bin 3 — Domain syntheses (biology + biotech + finance)

### biological-foundation-models-synthesis.md (thematic)

Eight Group A papers + the late-2026 cell-FM extension (ProtiCelli +
TranscriptFormer) + ClawBio as specialist-skill-as-Worker precedent.

Headline claim: Group A is the first Wave 1 batch where Linus's value
proposition is unambiguously domain-specific rather than infrastructural.
Six of eight release weights under permissive licences; five of eight are
operationally deployable on M1 Max with caveats; the smallest two
(REMME/REBEAN at 1.66M, METL at 2.5-50M) are small enough for full
local pretraining.

Constellation along generalist-vs-specialist axis: LucaOne (generalist
across DNA/RNA/protein, ~1.8B); Evo 2 (generalist within DNA, 7B/40B);
RiNALMo, AlphaGenome, METL, ProteinReasoner, Bacformer, REMME/REBEAN as
specialists. Recommended layered design: LucaOne as KG anchor; specialists
invoked by domain.

Cell-level FM extension (ProtiCelli + TranscriptFormer) opens a fresh
modality axis. ClawBio as working precedent for specialists-as-Workers at
the skill-class layer (depth complement to bioSkills's breadth).

Phase 7 sequence: REBEAN first; Bacformer + RiNALMo; AlphaGenome + Evo 2
hybrid; LucaOne and METL on demand. Phase 6 candidates: METL fine-tuning
exemplar; REMME/REBEAN full pretraining target.

g9-bio cluster (Bacformer, BioReason, bioSkills, deepsems, ClawBio) is
adjacent; the biological-foundation-models synthesis covers the model class
while g9-bio covers the deployable repos.

### generative-biology-synthesis.md (thematic)

Six Group B papers + ProtiCelli as Wave 2 cell-scale generative-imaging
extension. The papers form a residue-to-genome ladder of generated
artifacts: mCSM-metal (single residue, hybrid neuro-symbolic), Trias (codon
sequence, 47M BART), GenNA (mid-scale text-conditional, 3.6B), DISCO
(single-protein joint sequence+structure, heavy AlphaFold-class), DeepSeMS
(BGC → SMILES, ~100M), generative phages (whole-genome, Evo 1/2
fine-tuned).

Cross-cutting threads include: open-weights vs webserver-only release (five
of six open; mCSM-metal motivates the `external_api_tool` registry class);
M1 Max viability per scale (three local, one external API, two
aspirational); foundation-model substrate dependencies (Group B is
downstream of Group A vertically); validation rigor (wet-lab vs in-silico);
inference-time guidance and prompting (Feynman-Kac correctors generalize);
dual-use risk gradient (phages → DISCO → mCSM-metal/Trias/DeepSeMS/GenNA);
the generate→score→filter→wet-lab archetype.

SAFETY.md three-tier biosecurity policy (DEC-0047) and external_api_tool
registry class (DEC-0046) are the resolved decisions. Phase 7 sequence:
Trias, DeepSeMS, mCSM-metal external HTTP, GenNA 0.36B variant; DISCO and
Evo 2 / generative-phage pipeline deferred as remote-Worker-tier.

### function-annotation-discovery-synthesis.md (thematic)

Eight Group C papers covering function annotation, reasoning, and discovery:
Horizyn-1 (enzyme discovery via dual-encoder contrastive), DIAMOND
DeepClust (335M protein cluster representatives), ProtHGT (heterogeneous
graph transformer over CROssBAR KG), BioReason (DNA + LLM fusion, GRPO),
BioReason-Pro (protein + LLM + GO-GPT typed prediction), PertFormer (3B
cell-state FM), LAB-Bench, BixBench.

Headline claim: Group C is the first Wave 1 batch where Linus has access to
both methods and rulers at the same time. The benchmark archetype
(LAB-Bench + BixBench, now anchored from infra-foundations) reframes the
Phase 1 question from "selection" to "benchmarking."

Three paradigms for interpretability: free-text generation (BioReason),
graph-path traversal (ProtHGT), retrieval (Horizyn-1). The recommended Linus
default is **typed structured prediction wrapping free-text rationale** (S25
CLAUDE.md convention). KG-grounded vs FM-only function prediction —
ProtHGT's CROssBAR schema is the template for KG topology.

ClawBio added 2026-05-10 as orthogonal-modality extension (human consumer/
clinical genomics scale, complementary to Group C's protein-function focus).

g9-bio is the relevant cluster; the synthesis's Phase 7 sequence is
benchmark-informed (LAB-Bench + BixBench baseline → first skills decision).

### g10-finance.md (cluster) and entrepreneurship-synthesis.md (thematic)

Five finance/quant repos: dexter, OpenBB, QuantAgent, TradingAgents, nixtla
(0 Integrate, 5 Study). Off-mission relative to Linus's scientific computing
core but supplying four operationally load-bearing transferable patterns:

- **Two-tier context compaction (dexter)** — Phase 2 design constraint.
- **Dynamic per-session MCP tool activation (OpenBB)** — Phase 2/3
  orchestration primitive.
- **Two-tier LLM split + decision-log (TradingAgents)** — analyst-tier vs
  manager-tier; self-correction loop.
- **SKILL.md extensibility convention (dexter, OpenBB)** — committed Phase 7
  standard.

Plus the nixtla ecosystem (statsforecast, mlforecast, neuralforecast,
hierarchicalforecast) as time-series tooling that ports cleanly to omics
trajectories and environmental monitoring.

The entrepreneurship synthesis is the thematic home for these patterns
plus the seven Dan-profile-relevant opportunities (scientific literature
intelligence, genomics pipeline auditing, decision frameworks for grants,
environmental data intelligence, manuscript preparation, Notion templates,
local AI infrastructure consulting), the literature-intelligence stack
(paper-qa + bioSkills + Bacformer + LAB-Bench + KnowledgeBase) as
commercial-surface candidate, and the Canteen/Agora signal as first
commercial inbound. The entrepreneurship synthesis adopts a deliberately
exploratory posture: Linus first, knowledge mining second, business ideas
at the end of the pipeline.

The whiteboard pipeline frames the arrow ordering as load-bearing. The
Agent/Identity/Venue layered decomposition (from Canteen) generalizes as
an internal lens for attributable agent output.

---

## Bin 4 — LLM-hardware-design (a category of its own)

### llm-hardware-design-synthesis.md (thematic)

Fifteen QiMeng paper-notes + four cluster repos + Sketch2Simulation as
cross-thread exemplar. The thematic spine is **idea → reality**: LLMs
producing artifacts that downstream non-LLM actors (compilers, simulators,
fabs, manufacturers, engineers, contractors) accept and realize as physical
or computational reality.

Five within-cluster patterns plus a sixth via paper-side material:
multi-level summarization data synthesis (CodeV); RLVR with rule-based
testbench (CodeV-R1); Mutual-Supervised Learning via Co-verify + Co-evolve
(QiMeng-MuPa); substructure-aware preference optimization
(QiMeng-SALV); behavioral synthesis from I/O examples (QiMeng-cpu-v1);
macro-thinking / micro-coding planner-coder split (QiMeng-Kernel paper).

Strategic claim: **the oracle is the unit of effort being amortized, not
the training algorithm**. Phase 7 idea-to-reality skill class as the
biggest commitment; QiMeng-SALV as the most actionable canary for a
Linus-internal MTMC reproduction on M1 Max. Phase 8 long-horizon target:
biotech tangible things (bioreactor designs, fermentation vessel layouts,
custom electroporation cuvette geometries, bench-scale biotech
instrumentation BOMs).

Eleven ADR seeds named in this synthesis (the most of any single
synthesis). Confronts a structural ceiling honestly: production EDA
toolchains are closed-source and Apple-Silicon-incompatible; Linus's
realistic envelope stops at the open-source segment.

g12-llm-hardware-design is the primary cluster anchor (CodeV, QiMeng-MuPa,
QiMeng-SALV, QiMeng-cpu-v1, with Sketch2Simulation as cross-thread
reference).

---

## Bin 5 — Cluster syntheses (the repo-side rollups)

Twelve cluster syntheses pair with thematic syntheses but cover repos
rather than papers. Each is summarized in a sentence-or-two below.

### g1-apple-silicon.md

Eight repos (pmetal, mlx-flash, flash-moe, BitNet, Bonsai-demo, ANE,
autoresearch, autoresearch-mlx). Argues Apple Silicon is a research-grade
inference and training platform; pmetal is the load-bearing center.
autoresearch-mlx makes the research loop executable today; "trust the OS
page cache" is a first-class engineering convention. Primary anchor for
native-low-bit synthesis.

### g2-wiki-engines.md

Eleven LLM Wiki engine implementations (link, llmwiki, llmbase, llmwiki-cli,
wikidesk, wikiloom, wikimind, OmegaWiki, swarmvault, synthadoc,
TheKnowledge). All Study because none is shape-aligned with Linus's
memory-pillar requirements. Extracts wikiloom's chunk-id derivation,
llmbase's operations registry, TheKnowledge's citation enforcement,
OmegaWiki's SKILL.md discipline, qmd's fusion math. Primary cluster anchor
for llm-wiki synthesis.

### g3-wiki-patterns.md

Seven build-pattern repos (agentic-wiki-builder, AgenticResearchWiki,
llm-research-wiki, llm-wikidata, atomic-knowledge, beever-atlas,
obsidian-llm-wiki-local). All Study. Together with g2 brings the 18-repo
count, all Study. Highest-priority Phase 1 lift: obsidian-llm-wiki-local's
structured_output.py three-tier JSON-extraction fallback.

### g4-memory.md

Nine repos (agentmemory, anamnesis, omega-memory, engram, remember,
prompt-vault, openaugi, memex, k-dense-byok). All Study except prompt-vault
(Ignore). openaugi is the closest existing match to DEC-0029 v0 substrate;
agentmemory's lease/signal/checkpoint primitives address Phase 3
parallel-write coordination; engram's lint taxonomy ports to Layer C audit.
Primary cluster anchor for memory synthesis.

### g5-graph-tools.md

Seven repos (hyalo, keppi, py3plex, infranodus, infranodus-skills,
OptimusKG, dlt). One Integrate (hyalo: Rust binary for schema-validated
authoring + transactional link rewriting), six Study. hyalo + keppi close
most of Phase 3 KB tooling gap. OptimusKG's medallion architecture and dlt
as ETL backbone are Phase 2b/Phase 3 candidates.

### g6-mcp-tools.md

Eleven repos (fastmcp, ontomics, codesight, qmd, vectorless, WeKnora,
markdownify-mcp, codebase-memory-mcp, vanna, ExtractThinker, rendergit).
Five Integrate, six Study. Highest-density Integrate cluster. Headline
finding: MCP is overdetermined as Linus's tool substrate; fastmcp is the
framework; the registry expands beyond "KB tools only" to a unified
MCP document-context platform (KB + ingestion + extraction + codebase
intelligence).

### g7-harnesses.md

Fourteen repos (cline, claw-code, claw-code-local, openclaw, claude-squad,
claude-task-master, codebuff, workgraph, openrouter-skills, python-sdk,
origin, gravityfile, semanticworkbench, plus debate-or-vote and Goose as
Canteen-thread additions). The most directly consequential cluster for
Phase 1f orchestration evaluation. Headline: workgraph's JSONL DAG +
git-worktree-per-Worker is the most-liftable orchestration shape;
claude-squad and claude-task-master are complementary not competing.

### g8-sci-agents.md

Twelve repos centered on FutureHouse stack (paper-qa, aviary, ldp, robin,
ether0, BixBench, LAB-Bench, finch, scientific-agent-skills,
ibmdotcom-tutorials, claude-prism, Sketch2Simulation). Three Integrate
(paper-qa, LAB-Bench, scientific-agent-skills), eight Study, one Ignore.
paper-qa as Phase 2c KB retrieval engine. LAB-Bench canary string as Phase
2 ingestion obligation. Primary cluster anchor for llms-in-science
synthesis.

### g9-bio.md

Five repos (Bacformer, BioReason, bioSkills, deepsems, ClawBio). One
Integrate (bioSkills as inaugural Phase 7 skills payload), four Study
(Bacformer with Phase 7 hedge; ClawBio with high prior on later Adapt).
The most directly mission-aligned cluster for Dan's PhD specialization.
Companion to biological-foundation-models, function-annotation-discovery,
and generative-biology syntheses.

### g10-finance.md

Five repos (dexter, OpenBB, QuantAgent, TradingAgents, nixtla). 0
Integrate, 5 Study. Off-mission for scientific computing core; on-mission
for transferable patterns and Phase 7 entrepreneurial-surface
consideration. Primary cluster anchor for entrepreneurship synthesis.

### g11-agent-frameworks.md

Eight repos (pydantic-ai, dspy, superpowers, gptme, huginn,
Agent-Skills-for-Context-Engineering, promptfoo, lmnr). Two Integrate
(pydantic-ai as orchestration primitive, promptfoo as evaluation harness),
six Study. Closes Phase 1 Recon loop and opens Phase 2a specification.
Primary cluster anchor for skills-and-practices synthesis.

### g12-llm-hardware-design.md

Four repos (CodeV, QiMeng-MuPa, QiMeng-SALV, QiMeng-cpu-v1) + 15 paper
notes + Sketch2Simulation as cross-thread reference. All four repos Study.
Primary cluster anchor for llm-hardware-design synthesis.

---

## Cross-synthesis overlap matrix

Several syntheses share substantial overlap. The relationships worth naming:

**Memory ↔ Agentic-systems.** Layer D (investigation memory) was added in
response to Kosmos-style task-scoped shared state in the agentic-systems
synthesis. The two syntheses jointly own the memory-architecture pillar:
memory covers within-Worker layers (A, B, C); agentic-systems covers Layer
D (shared across Workers); KB synthesis covers Layer E.

**Memory ↔ LLM-wiki.** Layer E (semantic/knowledge memory) is where the
llm-wiki synthesis's discipline (claim typing, content hashing, write-back
rule, contradiction policy) is most load-bearing. The same hash-and-cite
substrate serves both the wiki-as-compiled-knowledge function and the
memory-pillar's reliable-history-access requirement.

**Llm-wiki ↔ Llms-in-science.** Both syntheses converge on citation
discipline. Llm-wiki provides the schema-as-flywheel framing; llms-in-
science provides the philosophical grounding (Marelli accountability,
Schulz reproducibility, Botvinick & Gershman roadmap agency). The
combination is the architecture of trust for any scientific use of
LLM output.

**Biological-foundation-models ↔ Function-annotation-discovery ↔ Generative-
biology.** These three thematic syntheses cover Wave 1 of the biology
pillar. Group A (foundation models) provides the substrate; Group B
(generation) and Group C (annotation/reasoning) consume the substrate. The
biology-Phase7-roadmap spec is the operational integration document.

**Llm-hardware-design ↔ Skills-and-practices.** The Phase 7 idea-to-reality
skill class proposed by llm-hardware-design is a Linus-specific skill
instantiation. The skills-and-practices synthesis is the natural
destination for the durable skill-class commitment when the Phase 7 ADR
lands.

**Safety-alignment-privacy ↔ Security.** The two syntheses jointly own the
six-axis security posture: code provenance + input integrity (security);
internal behavior + hosted-layer characterization + output-as-identity-
signal + dual-use refusal (safety-alignment-privacy).

**Entrepreneurship ↔ Skills-and-practices.** Both syntheses cover the
commercial-surface question. Skills-and-practices originally housed the
seven opportunities; they were promoted to entrepreneurship in 2026-05-05.
The g10-finance cluster supplies transferable patterns to both. The
literature-intelligence stack is the worked example in entrepreneurship;
the broader practitioner-knowledge claims live in skills-and-practices.

**Humans-teams-performance ↔ Skills-and-practices ↔ Memory.** The
three-timescales braid (cognitive throughput + team rhythm + intra-career)
informs Maestro/Worker discipline; the skills synthesis operationalizes the
clarity-over-intelligence thesis; the memory synthesis provides the
architectural substrate that makes durable scratchpad possible. Together
they argue that structure compounds where intensity does not.

---

## Where bins might be redrawn (and where they shouldn't be)

The taxonomy above puts memory + infra + native-low-bit + llm-wiki +
security + safety-alignment-privacy into the substrate bin. An alternative
binning would split inference (native-low-bit + infra) from data substrate
(llm-wiki + memory + KB) from safety (security + safety-alignment-privacy).
That split is defensible; the reason for keeping them together is that
the memory synthesis explicitly ties Layer A to the inference substrate
(Coconut, minGRU, BitNet/Bonsai), so the architectural commitments are
braided in a way that makes the split artificial.

Agentic-systems and skills-and-practices both sit awkwardly in the
behavioral bin — agentic-systems is half infrastructure (Role typing,
AgentReport, Layer D) and half behavioral. The cleaner split would put
agentic-systems into substrate and skills-and-practices into pure
behavioral. The reason for keeping them together is that the Maestro/Worker
discipline shows up in both as the unifying behavioral principle, and the
cross-references run thick.

The biology syntheses (three thematic + g9 cluster) could collapse into a
single biology pillar synthesis. The reason for keeping them split is that
the three thematic axes (foundation models / function and discovery /
generative) have genuinely different operational commitments (e.g., the
biosecurity tier policy is sharpest in generative-biology; the
typed-structured-prediction convention is sharpest in function-annotation-
discovery; the registry stratification of substrate-vs-application is
sharpest in biological-foundation-models). Three syntheses is the right
resolution for the level of architectural commitment each requires.

The llm-hardware-design synthesis could arguably belong in the domain bin
alongside biology — both are Phase 7+ domain commitments — but I have put
it in its own bin because the strategic claim (idea-to-reality as a
Linus-specific skill class) is one level up from domain commitments and
sits at the same level as the safety posture or the orchestration shape.

Humans-teams-performance is the smallest synthesis by paper count and
cleanest in its argument. It could be folded into skills-and-practices as a
section. The reason for keeping it separate is that the three-timescales
braid is a load-bearing piece of philosophical infrastructure that earns a
durable home rather than a section in a synthesis that may grow or shrink.

---

## Closing observation

The 27 syntheses are unevenly weighted. Five syntheses (memory,
infra-foundations, native-low-bit, llm-wiki, agentic-systems) carry the
infrastructure substrate and are the largest by line count. Three syntheses
(biological-foundation-models, generative-biology, function-annotation-
discovery) carry the biology-domain commitment. Three syntheses
(skills-and-practices, llms-in-science, humans-teams-performance) carry
behavioral and philosophical content. Two syntheses (security,
safety-alignment-privacy) carry the security posture. One synthesis each
covers llm-hardware-design and entrepreneurship.

The cluster syntheses (g1-g12) pair with thematic syntheses but are not
1:1 — some thematic syntheses have multiple cluster anchors; some clusters
serve multiple thematic syntheses. The most extensively-referenced clusters
are g1-apple-silicon (cited from native-low-bit and infra-foundations and
memory and security), g6-mcp-tools (cited from agentic-systems and
infra-foundations and skills-and-practices and llm-wiki), and g9-bio
(cited from all three biology thematic syntheses and from
entrepreneurship).

The most under-represented area in the cluster syntheses is humanistic /
philosophical content — there is no cluster for the llms-in-science or
humans-teams-performance threads because those threads are paper-driven
rather than repo-driven. The reverse is also true: g4-memory and
g7-harnesses are repo-heavy clusters whose thematic anchors (memory,
skills-and-practices) cover only part of the repo-level material.

The corpus would benefit from one additional synthesis the existing
27 do not cover: a synthesis on **observability and instrumentation**
spanning Beaglehole activation probes, lmnr OTel tracing, Worker-values
extraction, and the audit-log as both Marelli-attribution and
safety-evidence substrate. Today this content is scattered across
safety-alignment-privacy, skills-and-practices, agentic-systems, and
g11. A consolidating synthesis would surface the cross-cutting
"observability is not optional" thesis that runs through all of them.
