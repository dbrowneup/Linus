# MiroFish-Offline (`nikmcfly/MiroFish-Offline`)

## 1. Purpose and scope

MiroFish-Offline is a **fully local fork** of the Chinese-market simulation product `666ghj/MiroFish` — a multi-agent
swarm-intelligence engine that takes an arbitrary input document (press release, policy draft, financial report,
narrative fragment) and simulates the public reaction to it on social platforms. The fork (`nikmcfly/MiroFish-Offline`,
17 MB cloned, AGPL-3.0) replaces the original's three cloud dependencies — Zep Cloud for the knowledge graph and
episodic memory, DashScope for LLM inference, Zep's hosted embeddings — with a self-hostable trio: **Neo4j Community
Edition 5.18** as the graph substrate, **Ollama** (Qwen2.5 / Llama3 / nomic-embed-text) for both LLM and embedding
inference, and a hand-written `NERExtractor` that does entity-and-relation extraction via local-LLM JSON-mode prompting.
The fork also re-translates the entire frontend (1,000+ strings across 20 React/TypeScript files) from Chinese to
English. The Canteen-blog landscape note frames this as the local-first variant of the MiroFish multi-agent debate
family ("Local-first plus multi-agent is exactly the Linus design space; if the architecture is sound this is direct
prior art") and assigned a tentative verdict of "Investigate, then Study or Watch"
([`canteen_blog_landscape_2026-05.md`](../../context/notes/canteen_blog_landscape_2026-05.md)). After the source survey,
the verdict lands at **Watch** for reasons developed in §6.

The product workflow is five stages, each implemented in the backend Flask app
(`backend/app/api/{graph,simulation,report}.py`, ~3,700 LoC across the three blueprints):

1. **Graph build.** Upload a document; the `NERExtractor` (`backend/app/storage/ner_extractor.py`, 242 LoC) extracts
   entities and relations using ontology-guided JSON-mode LLM calls, the `EmbeddingService` produces 768-dim Ollama
   `nomic-embed-text` embeddings per fact-sentence and per entity, and the `Neo4jStorage` layer
   (`backend/app/storage/neo4j_storage.py`, 657 LoC) writes them to Neo4j with both vector and BM25 fulltext indexes.
2. **Environment setup.** The `OasisProfileGenerator` (`backend/app/services/oasis_profile_generator.py`, 1,140 LoC)
   converts knowledge-graph entities into per-agent persona profiles in two flavors (Reddit-style with `karma` and
   Twitter-style with `friend_count`/`follower_count`/`statuses_count`), each with a free-text `bio`, a multi-paragraph
   `persona`, optional MBTI/profession/age/country/interested-topics, and a back-pointer `source_entity_uuid` linking
   the agent to the graph entity it was generated from. The `SimulationConfigGenerator`
   (`backend/app/services/simulation_config_generator.py`, 987 LoC) then generates per-agent activity configurations
   (posts/hour, comments/hour, sentiment bias, stance, influence weight, active hours) using a step-by-step LLM pipeline
   (time config → event config → agent batches → platform config) that mirrors the BlitzScaling shape of "decompose the
   long generation into smaller verifiable steps."
3. **Simulation.** The `SimulationRunner` (`backend/app/services/simulation_runner.py`, 1,766 LoC) hands off to the
   **OASIS** simulator (`camel-oasis==0.2.5` from the CAMEL-AI team — the actual social-platform simulator engine).
   Agents run on simulated Twitter and/or Reddit platforms in hour-by-hour rounds, executing actions (`CREATE_POST`,
   `LIKE_POST`, comment, follow, etc.) recorded as `AgentAction` records with per-round summaries. The
   `simulation_ipc.py` layer (393 LoC) is the cross-process command/response shim — OASIS runs as a subprocess for crash
   isolation.
4. **Report.** The `ReportAgent` (`backend/app/services/report_agent.py`, 2,579 LoC — the largest service module)
   analyzes the post-simulation environment using a ReACT pattern: it plans an outline, then generates each section via
   multi-round thinking + reflection, calling four tool families on the way (`SearchService` for graph queries,
   `InsightForge` for opinion-cluster summaries, `Panorama` for trend/sentiment timelines, agent-interview tools that
   pose questions to focus-group agents). Per-step actions are logged to `agent_log.jsonl` for downstream replay.
5. **Interaction.** The user can chat with any simulated agent post-hoc; the agent retains its persona, its memory of
   what it posted, and the graph context that informed its behavior.

The relevance to Linus is **architectural-pattern reference**, not code. The product is a research/business tool with a
narrow intended use case (social-dynamics simulation around business or policy artifacts); it is not a coding agent, a
scientific reasoning agent, or a Linus-shaped orchestration substrate. The local-first stack (Ollama + Neo4j Community +
nomic-embed-text + hybrid vector/BM25 search) is interesting as a worked example of a Linus-adjacent topology — Phase 2
KnowledgeBase + Layer C/E memory could absorb several specific patterns — but the AGPL-3.0 license forecloses any code
incorporation into Linus proper. The verdict is **Watch** with the AGPL caveat made explicit, plus a Phase 7+ revisit
candidate when Dan's biotech-policy commercial surface becomes scoped (per the
[entrepreneurship synthesis](../syntheses/entrepreneurship-synthesis.md) framing in the Canteen note).

## 2. Architecture summary

The deliverable is a Docker Compose stack (`docker-compose.yml`) running three services: a Flask backend on port 5001
(`backend/`), a Vite-bundled React/TypeScript frontend on port 3000 (`frontend/`), and supporting services Neo4j 5.18
Community on 7474/7687 and Ollama on 11434. Optional manual installation runs the Python backend (Python 3.11+, see
`backend/requirements.txt`) and the Node frontend (Node 18+, `frontend/package.json`) directly against host-installed
Neo4j and Ollama. The `compose.yaml` reserves an NVIDIA GPU for the Ollama container by default — a Linus reproduction
on Apple Silicon would have to drop the `deploy.resources.reservations.devices` block and run Ollama via Homebrew on the
host (per CLAUDE.md "Ollama via conda is CPU-only" and the standing posture that Docker on macOS does not pass through
Metal/ANE).

The **backend** (`backend/app/`) is a Flask 3.0+ application factory (`backend/app/__init__.py`) registering three
blueprints — `graph_bp`, `simulation_bp`, `report_bp` — under `/api/graph`, `/api/simulation`, `/api/report`. The
factory initializes a single `Neo4jStorage` singleton via `app.extensions['neo4j_storage']`
(dependency-injection-via-Flask- extensions, no global singletons) and registers a `SimulationRunner.register_cleanup`
atexit hook so simulation subprocesses die with the server. The CORS surface is wide-open
(`r"/api/*": {"origins": "*"}`) — production-deployed this would need tightening, but for a localhost-only dev tool it
is acceptable.

The **storage layer** (`backend/app/storage/`, 1,243 LoC across six modules) is the cleanest piece of the codebase and
the most directly relevant to Linus's Layer C/E memory pillar. The substrate decomposes into:

- **`GraphStorage`** (`graph_storage.py`, 126 LoC) — abstract-base-class interface: `add_entity`, `add_relation`,
  `search`, `delete_graph`, etc. The README explicitly notes this is the swap-out point: "swap Neo4j for any other graph
  DB by implementing one class." Useful pattern for Linus: define a `GraphStorage` ABC at Phase 2 spec time so the v0
  KnowledgeBase Neo4j implementation can be swapped for SQLite + content hashes (per DEC-0029) without re-plumbing the
  callers.
- **`Neo4jStorage`** (`neo4j_storage.py`, 657 LoC) — the concrete implementation. Manages connection lifecycle, schema
  initialization (`neo4j_schema.py`, 62 LoC creates vector and fulltext indexes on entities and facts), per-graph
  isolation (every entity / relation carries a `graph_id` property and queries filter on it — multi-tenant-by-graph),
  and the entity-and-relation insert/upsert/delete verb set.
- **`EmbeddingService`** (`embedding_service.py`, 204 LoC) — calls Ollama's `/api/embeddings` endpoint with
  `nomic-embed-text` (768-dim by default), batches when possible, and exposes a single `embed(text: str) -> list[float]`
  verb. Notable: the service raises a typed `EmbeddingError` rather than silently returning zero vectors, so callers see
  the failure rather than corrupting the index with a sea of zeros.
- **`NERExtractor`** (`ner_extractor.py`, 242 LoC) — local-LLM-driven entity-and-relation extraction. The system prompt
  is ontology-aware (the LLM is told the entity-types and relation-types it is allowed to emit), specifies normalization
  rules (canonical form, no whitespace), demands strict JSON output, and supports a `max_retries=2` retry loop on
  JSON-parse failures. Returns `{entities: [{name, type, attributes}], relations: [{source, target, type, fact}]}`.
- **`SearchService`** (`search_service.py`, 253 LoC) — **hybrid search**: 0.7 × vector similarity + 0.3 × BM25 keyword
  match, both indexed in Neo4j directly via `db.index.vector.queryNodes` and `db.index.fulltext.queryNodes` Cypher
  procedures. Searches both nodes (entities) and edges (facts) and merges scored results. The 0.7/0.3 weighting is
  hardcoded; the v0.4 ROADMAP item is to make this per-graph-configurable. This hybrid pattern is the canonical
  knowledge-graph retrieval shape and is a direct reference for the KnowledgeBase Phase 2 retrieval surface.

The **services layer** (`backend/app/services/`, 11,632 LoC across eleven modules) is where the simulation business
logic lives. The largest modules — `simulation_runner.py` (1,766 LoC), `report_agent.py` (2,579 LoC), `graph_tools.py`
(1,496 LoC), `oasis_profile_generator.py` (1,140 LoC), `simulation_config_generator.py` (987 LoC) — together account for
~75% of the backend code volume and are tightly coupled to OASIS's simulation primitives. The five stages of the
workflow map onto: `text_processor.py` + `ontology_generator.py` + `graph_builder.py` (graph build),
`oasis_profile_generator.py` + `simulation_config_generator.py` (env setup), `simulation_runner.py` +
`simulation_ipc.py` + `simulation_manager.py` (simulation), `report_agent.py` + `graph_tools.py` (report), with
`graph_memory_updater.py` and `entity_reader.py` as cross-cutting utilities.

The **simulation engine itself is OASIS** — the `camel-oasis==0.2.5` and `camel-ai==0.2.78` dependencies (pinned in
`backend/requirements.txt`) are CAMEL-AI's social-platform simulator with built-in Twitter and Reddit primitives. The
OASIS framework is what implements the per-round agent action loop (each agent reads its timeline, decides on an action
via LLM call, writes the action to the platform, the platform propagates effects to followers); MiroFish builds the
persona generator + simulation config + post-hoc analysis layers around it. This makes the actual swarm-simulation
substance largely **upstream of MiroFish-Offline**; OASIS itself is a separate Tier-3 reference repo per the Canteen
note. The fork's contribution is the _productization_ — turning OASIS from a research framework into an
upload-document-and-run-the-pipeline product.

The **frontend** (`frontend/`, Vite + React + TypeScript) is a SPA with three primary screens: graph builder + viewer,
simulation control + live status, and report viewer + agent-chat. The Chinese-to-English translation surface is captured
in `frontend/CHINESE_TEXT_INVENTORY.md` (the per-string audit log of the translation pass). The fork's README claims
1,000+ strings translated across 20 files; the inventory file is the receipt.

The **OASIS persona shape** (per `OasisAgentProfile` in `backend/app/services/oasis_profile_generator.py`) is the most
algorithmically interesting unit in the codebase. Each agent carries: a **per-platform identity** (`user_id`,
`user_name`, `name`), a **bio + persona pair** (short tagline + long descriptive paragraph), a **demographic block**
(age, gender, MBTI, country, profession, interested topics — sparse, optional), an **influence block** (`karma` for
Reddit; `friend_count` + `follower_count` + `statuses_count` for Twitter), and a **provenance pointer**
(`source_entity_uuid` + `source_entity_type` linking back to the knowledge graph entity that seeded the agent). The
config generator separately attaches an **activity configuration** (`activity_level`, `posts_per_hour`,
`comments_per_hour`, `active_hours`, `response_delay_min/max`, `sentiment_bias`,
`stance ∈ {supportive, opposing, neutral, observer}`, `influence_weight`). The **time configuration**
(`CHINA_TIMEZONE_CONFIG` in `simulation_config_generator.py`) bakes Chinese workday rhythms into the simulation defaults
— dead hours 0–5, peak evening hours 19–22 — which is a culturally-specific assumption not yet generalized to other
markets (see §5).

The **Report Agent** (`backend/app/services/report_agent.py`, 2,579 LoC, the heaviest single module) deserves call-out
for its architecture. It implements a planning-then-section-generation loop where the planner produces an outline, each
section is generated via ReACT (Reason-Act-Observe) with tool calls into the graph and into focus-group agent
interviews, and the entire pipeline emits a per-step `agent_log.jsonl` audit trail with elapsed-time records. The JSONL
audit format — one line per action with `timestamp`, `elapsed_seconds`, `action`, `stage`, `section_title`,
`section_index`, and a `details` dict — is structurally similar to the workgraph JSONL append-only DAG pattern
recommended for the Phase 2a Linus session-store (per the `g7-harnesses` synthesis). MiroFish's report-specific
elaboration (per-section indexing, stage tagging) is a useful design cue.

## 3. What's reusable in Linus

Per §6, the verdict is **Watch** and the AGPL-3.0 license blocks any direct code incorporation. The "reusable" items
below are therefore **architectural patterns to study and re-implement Linus-native**, not code lifts. Every entry below
is gated on AGPL contamination analysis — even pattern-level lifts require careful review with a copyright specialist
before code is written that "looks like" the MiroFish source. The safer posture is treating MiroFish-Offline as
inspiration and writing Linus's implementation from a clean-room reading of upstream references (Neo4j docs, the
hybrid-search literature, the OASIS API).

**Phase 2 — `GraphStorage` ABC pattern as a reference for the KnowledgeBase substrate-swap interface (DEC-0029).**
MiroFish's storage layer factors a `GraphStorage` abstract base class (~10-method surface: `add_entity`, `add_relation`,
`search_nodes`, `search_edges`, `delete_graph`, etc.) and a single concrete `Neo4jStorage` implementation. The README
explicitly markets this as a swap-out point. For Linus, the analogous Phase 2 spec move is to define a
`KnowledgeBaseStorage` ABC at the KB-substrate layer so the v0 implementation can be Neo4j-or-SQLite-or-pgvector and the
Worker-callable retrieval surface stays stable across substrate migrations. DEC-0029 commits to "SQLite + content
hashes + git as the persistence substrate underneath," and an ABC at the storage interface is exactly how that
commitment gets honored without locking the caller surface to SQLite's specific verb shape. The MiroFish pattern is
small enough (126 LoC for `graph_storage.py`) that the exercise is mostly "reading a pre-existing example of the right
shape and then writing the Linus version against it."

**Phase 2 — hybrid vector + BM25 search (0.7/0.3 weights) as a starting heuristic for KnowledgeBase retrieval.**
MiroFish's `SearchService` combines `db.index.vector.queryNodes` (cosine similarity over `nomic-embed-text` embeddings)
and `db.index.fulltext.queryNodes` (Lucene BM25) with a fixed 0.7 vector / 0.3 keyword weighting. This is the canonical
hybrid-search shape — neither pure-vector (which misses lexical exact matches like SKU numbers, gene names, PMIDs) nor
pure-keyword (which misses semantic equivalents). For Linus's Phase 2 KnowledgeBase retrieval, the 0.7/0.3 weighting is
a reasonable starting point; the Phase 1 measurement work in `benchmarks/dan_tasks/` should sweep the weighting on Dan's
actual task corpus (genomics + bioinformatics + LanzaTech metagenomics) before committing to a default. Note: in Dan's
domain, lexical exact-match is unusually load-bearing (gene IDs like `BRCA1`, accession numbers like `NM_007294`,
species names like `Botryococcus braunii`) — the keyword weight may need to be **higher** than 0.3 for biology corpora,
which is the kind of finding Phase 1 measurement is designed to surface.

**Phase 2 — agent-callable tool surface with structured inputs and JSON-mode-LLM output (parallels DEC-0044).** The
`graph_tools.py` module exposes a tool surface that an agent can call via the standard LLM tool-call interface:
`SearchResult`, `InsightForgeResult`, `PanoramaResult`, `InterviewResult` are all structured-output data classes
returned by tools. This is the same shape `paper-qa` (DEC-0044) takes for KB retrieval: tools return typed structured
results, the agent reasons over them. MiroFish's contribution to the design space is the **tool taxonomy decomposition**
— retrieval tools (search) vs. analysis tools (InsightForge, Panorama) vs. social tools (agent interviews). The Linus
KnowledgeBase tool surface should make a similar decomposition explicit at Phase 2 spec time.

**Phase 7+ — persona-driven multi-agent simulation as a design point for biology-skill auto-evaluation.** The
`OasisAgentProfile` shape and the `AgentActivityConfig` shape together define a worked vocabulary for parameterizing
agent diversity: `sentiment_bias`, `stance`, `influence_weight`, `posts_per_hour`, `interested_topics`. For a Phase 7+
biology-skill auto-eval pipeline (where N agents with distinct biological-domain personas independently evaluate a
hypothesis, and the spawner aggregates their typed reports — see [debate-or-vote.md](debate-or-vote.md) §3 for the
heuristic-aggregation framing), this vocabulary is a useful reference for what fields a Linus persona library should
declare. The relevant Linus-side personas are different (Senior Scientist, Pipeline Engineer, Genomics Specialist,
Reviewer, Architect — see `debate-or-vote.md` §7 Question 6 on persona-library starter material) but the **field set**
is portable: `domain_bias`, `methodology_stance`, `confidence_calibration`, `expertise_level`. The MiroFish persona is
overspecified for Linus's biology-eval task (no need for `karma` or `friend_count`); strip the social-platform-specific
fields and keep the persona vocabulary.

**Phase 7+ — hour-by-hour temporal evolution loop as a reference for time-stepped agent simulations.** The
`CHINA_TIMEZONE_CONFIG` activity-multiplier table and the round-based `RunnerStatus` state machine in
`simulation_runner.py` together define a "simulation tick" pattern: each round advances simulation time by
`minutes_per_round` (default 60 simulation-minutes per round), each agent computes its participation-probability based
on `activity_level × time_multiplier`, and the platform propagates resulting actions. For a Phase 7+ Linus pattern that
needs to model time-evolution explicitly (e.g., a metagenomic process simulation, or a multi-day biotech-policy reaction
model), the round-tick + activity-multiplier shape is a directly applicable reference. The cultural assumption embedded
in `CHINA_TIMEZONE_CONFIG` (Chinese workday rhythms) is **not** portable; the **structure** (a per-hour
activity-multiplier table) is.

**Phase 2 — `agent_log.jsonl` audit-record shape as a confirming signal for workgraph-JSONL adoption.** The
`ReportLogger` class in `report_agent.py` writes one JSONL line per agent step with `timestamp`, `elapsed_seconds`,
`report_id`, `action`, `stage`, `section_title`, `section_index`, and a free-form `details` dict. This is structurally
the same shape recommended in the [g7-harnesses synthesis](../syntheses/repo-clusters/g7-harnesses.md) for the Phase 2a
Linus session-store (workgraph's `.workgraph/graph.jsonl` append-only DAG). MiroFish's per-stage `stage` field
(`planning` / `generating` / `completed`) and per-section `section_title` + `section_index` are useful refinements
specific to ReACT-driven generation; the Linus equivalent for Phase 3 fan-out audit-logging should similarly carry
per-task-stage fields.

**Phase 2/7+ — local-first stack architecture as a topology reference (Ollama + Neo4j Community + nomic-embed-text +
hybrid search).** The end-to-end stack — local Ollama LLM, local Neo4j Community as graph database, local
`nomic-embed-text` for embeddings, hybrid vector+BM25 retrieval, structured tool-callable interface to the graph — is
exactly the topology Linus's KnowledgeBase + Layer E aspires to. MiroFish-Offline is **the worked example** of that
topology in the cloned-repo collection, even if the AGPL license blocks adoption. The **prior art** value is high: when
Linus designs Phase 2 KnowledgeBase v1, the MiroFish-Offline architecture is the comparison case for "what does a
production-deployed local-first knowledge-graph + retrieval + agent-tool stack actually look like?" Read the storage
layer end-to-end as design reference; do not lift code.

## 4. What's inspiration only

The **OASIS social-platform simulation engine itself** (`camel-oasis==0.2.5`) is the substrate that does the actual
swarm simulation; MiroFish-Offline is a productization wrapper. OASIS has Twitter and Reddit primitives, an action loop,
and the agent-action propagation logic. For Linus, OASIS itself is more directly relevant than MiroFish-Offline if swarm
simulation ever becomes a Phase 7+ commercial-surface deliverable — but it is also a CAMEL-AI dependency, and CAMEL-AI
is its own significant ecosystem (the Canteen note Tier-3 list mentions OASIS as reference-only). The inspiration-only
takeaway is the **separation of concerns**: MiroFish does the persona generation + simulation config + post-hoc
analysis; OASIS does the simulation tick loop. A Linus Phase 7+ analog could similarly factor the **simulation
substrate** away from the **persona / config / analysis layer**.

The **`SimulationConfigGenerator` step-by-step LLM pipeline** (time → events → agent batches → platform) is a worked
example of the Algorithm-applied-to-LLM-prompting pattern: instead of asking the model to generate one giant
configuration in one call (failure-prone, hard to validate), decompose into smaller verifiable steps with structured
outputs at each step. This is the BlitzScaling cycle-time discipline in prompt engineering. The pattern is portable to
any Linus task that currently asks the Worker for a long structured artifact — refactor into smaller per-component calls
with per-step validation. Inspiration only because the specific decomposition (time, events, agents, platform) is
MiroFish-specific; the **principle** generalizes.

The **`InsightForge` and `Panorama` analysis tools** in `graph_tools.py` (opinion-cluster summarization, sentiment-trend
timelines) are interesting design-space references for "what tools should an analysis agent have access to?" The
ReportAgent uses these alongside straight graph-search to compose its analysis. For Linus's Phase 7+ scientific-analysis
agents (e.g., a metagenomics-result analysis agent), the analogous tool set would be domain-specific (e.g., taxonomic
abundance trend, function-annotation enrichment) but the **pattern** of having both raw-retrieval tools and
pre-aggregated-analysis tools is portable.

The **agent-interview pattern in the report stage** — the ReportAgent posts questions to focus-group agents and uses
their typed responses as evidence in the report — is a creative use of the multi-agent simulation: the simulated agents
become a synthetic-population focus group whose responses inform the analysis. For a Linus Phase 7+ biology-policy
commercial surface, this maps directly: simulated stakeholder agents (regulators, industry, advocacy, scientists)
respond to a draft policy or biotech announcement, and the report aggregates their typed responses into a stakeholder-
reaction analysis. **Speculative Phase 7+** — but worth flagging as a possible commercial-surface direction once Dan's
biotech-policy advisory work scopes out (per the Canteen entrepreneurship synthesis E-IDs framing).

The **Flask-extensions-for-DI pattern** (`app.extensions['neo4j_storage']`) is a clean alternative to global singletons
for sharing service instances across blueprints. It is unsurprising for a Flask app and not load-bearing for any Linus
decision, but worth noting as a reference if Linus's eventual orchestration backend uses Flask (currently FastAPI is the
implicit default given the broader cloned-repo bias toward FastAPI; see Letta's own choice).

## 5. What's incompatible or out of scope

**The AGPL-3.0 license is the load-bearing constraint.** AGPL-3.0 is GNU's strong-copyleft license with the network-use
provision: derivative works of AGPL software, when made available over a network, must themselves be released under
AGPL-3.0 (with full source). MiroFish-Offline's LICENSE file is the canonical AGPL-3.0 text. **Linus has not committed
to an AGPL license** (the project's license posture is unsettled; CLAUDE.md's project-purpose section frames Linus as
"private, local, modular AI assistant" — there is no public license statement yet, and no ADR commits Linus to any
specific license). This means: (a) **no code can be lifted from MiroFish-Offline into Linus** without either making
Linus AGPL or carefully isolating the MiroFish-derived code into a network-detached process and analyzing the AGPL
boundary with a copyright specialist — neither of which is justified by what MiroFish-Offline offers; (b) **even
"pattern" lifts require careful clean-room separation** — reading MiroFish source and then writing "similar but not
identical" code is the gray zone where copyright analysis matters. The safe posture is to treat MiroFish-Offline as a
**Watch-only design reference** and write Linus equivalents from upstream-source clean-rooms (Neo4j docs, hybrid-search
papers, the OASIS API). This is the dominant out-of-scope reason and the load-bearing reason for the **Watch** verdict.

**The product is a research/business tool with a narrow intended use case.** MiroFish-Offline is built for "simulate
public reaction to a press release / policy / financial document." It is not a coding agent (Phase 2/3 Linus relevance:
zero), not a scientific-reasoning agent (Phase 7 Linus relevance: low), and not a Linus-shaped orchestration substrate
(Phase 2a Linus relevance: zero). It overlaps Linus's design space only at the **Phase 2 KnowledgeBase + Phase 7+
biology-policy commercial surface** (per the Canteen entrepreneurship synthesis). For Phase 1–6 deliverables — the bulk
of Linus's near-term roadmap — the product's domain is orthogonal.

**The Chinese-market origin means cultural assumptions are baked into defaults.** The `CHINA_TIMEZONE_CONFIG` in
`simulation_config_generator.py` defaults the simulation to Chinese workday rhythms (dead hours 0–5, work hours 9–18,
peak evening hours 19–22, night decay at 23). The persona generator's `country` field defaults are not symmetric across
cultures — agents are biased toward Chinese-market personas even after the UI translation. The frontend CHINESE*TEXT*
INVENTORY captures the translation work but does not capture the cultural biases in the persona / activity templates.
For a Linus reproduction or any biotech-policy adaptation, the cultural-assumption surface would need a full audit and
re-defaulting pass. This is a non-trivial scope item, not a quick translate.

**The `NERExtractor` is a research-quality module, not a production-grade NER system.** The 242-LoC LLM-based
ontology-aware extractor with two retries on JSON-parse failure is fine for a demo and acceptable for a small-to-medium
input corpus, but is not equivalent to a production NER system in extraction quality, throughput, or recall on
domain-specific entities (e.g., gene names, protein domains, compound names). For Linus's KnowledgeBase ingest pipeline,
the NER substrate should be a domain-aware tool (per the [`paper-qa` integration spec](../specs/kb/paper-qa-substrate-
integration.md) and the broader KB pipeline) — possibly multiple specialized extractors (a chemistry NER, a biology NER,
a PMID NER) rather than one ontology-aware general LLM call. The MiroFish pattern is the floor, not the ceiling.

**OASIS social-platform simulation is not a Linus substrate.** The fact that MiroFish-Offline has Twitter and Reddit
primitives and a per-hour action loop is interesting prior art, but the actual social-platform simulation is **out of
scope for Linus orchestration**. Linus is the orchestration backend for Dan's scientific work; it is not a social-
network simulator. Even at Phase 7+ when biotech-policy commercial-surface work might use simulation, the substrate
choice would be a separate scoping decision (likely OASIS or SocioSim-like rather than building from scratch).

**The `compose.yaml` GPU reservation assumes NVIDIA / CUDA.** The Ollama service block reserves
`driver: nvidia, count: all, capabilities: [gpu]` — this is a Linux-CUDA assumption. On Apple Silicon, Docker-hosted
Ollama would need to drop the GPU reservation entirely (Docker on macOS does not expose Metal/ANE), making the container
CPU-only with predictable performance loss. The supported posture per CLAUDE.md is **host-installed Ollama via Homebrew,
not Docker-hosted Ollama**, which means a Linus-side reproduction would need to rewrite the compose stack to point the
backend at `host.docker.internal:11434` and skip the Ollama container entirely. Worth noting because the out-of-the-box
`docker compose up -d` will not work on M1/M2/M3 hardware as written.

**The 167+ LoC `RunnerStatus` enum + `AgentAction` + `RoundSummary` + IPC subprocess machinery in `simulation_runner.py`
is OASIS-specific.** This is the layer that bridges MiroFish's API surface to OASIS's tick loop; the entire shape only
makes sense if you are running OASIS. For Linus, none of this is portable. The relevant Linus pattern is the spawner /
sub-process orchestration shape from Phase 3 (DEC-0050, DEC-0052), not the OASIS-bridge shape.

**No paired paper-note exists** (and probably should not be created). The original MiroFish does not have a published
arxiv paper that I am aware of from this source survey; the Canteen note is the secondary-source framing. Unlike
[`debate-or-vote`](debate-or-vote.md) (paired with arxiv 2508.17536) or [`Letta`](Letta.md) (paired with arxiv
2310.08560), MiroFish-Offline is a product without an academic paper trail. The OASIS framework underneath does have
publications, but those are upstream of MiroFish and would belong to a separate OASIS / CAMEL-AI repo-note (not in scope
here). Recommendation: do not create a paired paper-note.

## 6. Recommendation: **Watch** (with AGPL caveat)

Watch the project for two reasons. First, **AGPL-3.0 license blocks any direct code incorporation into Linus** — the
strong-copyleft network-use provision means Linus would have to commit to AGPL itself, which is a project-defining
license decision that has not been made and should not be triggered by adopting one upstream component. Second, **the
product's domain is orthogonal to Linus's Phase 1–6 deliverables**. The narrow use case (multi-agent simulation of
public reaction to documents) overlaps Linus only at the speculative Phase 7+ commercial-surface boundary (where Dan's
biotech-policy advisory work might intersect), and even there, the MiroFish-specific cultural assumptions and OASIS
substrate dependency limit reusability.

The Watch posture has a specific revisit trigger: **when Linus's Phase 7+ biotech-policy commercial surface scopes out
explicitly** (per the [entrepreneurship synthesis](../syntheses/entrepreneurship-synthesis.md) framing and the Canteen
note's Tier-2 positioning), MiroFish-Offline becomes the closest existing prior art for the architectural shape that
work would take. At that point the right move is **commission a clean-room re-implementation** — read the MiroFish-
Offline source carefully for design ideas, write the Linus version against upstream sources (Neo4j docs, OASIS API,
hybrid-search literature), and document the design lineage explicitly. The AGPL boundary remains the load-bearing
constraint regardless: even at Phase 7+ revisit time, Linus's license posture will need to be settled before any code
that is "informed by" MiroFish-Offline can be written, and a copyright specialist consult is the right gate.

The **architectural patterns listed in §3** (storage ABC, hybrid-search weighting, persona vocabulary, hour-tick
simulation loop, JSONL audit shape) are the durable takeaway and can be lifted as design references at any phase without
AGPL contamination — they are sufficiently common in the broader literature that Linus equivalents written from upstream
sources are clean. Specifically, the Phase 2 KnowledgeBase substrate spec should reference MiroFish- Offline as one
prior-art comparison case for the Neo4j-Community-as-graph-substrate path (alongside Letta's pgvector path and the
upcoming KB v1 spec's SQLite + content hashes path per DEC-0029).

**Cluster cell:** [`g11-agent-frameworks`](../syntheses/repo-clusters/g11-agent-frameworks.md) is the closest fit — the
load-bearing pattern is persona-driven multi-agent simulation, which sits in the general-purpose-agent-framework design
space rather than g4 (memory), g6 (MCP tools), g7 (harnesses), or g8 (scientific reasoning agents). The fit is awkward
because g11 is dominated by general-purpose frameworks (CrewAI, AutoGen, LangGraph) rather than domain-specific
products, but persona-driven simulation as a multi-agent pattern is closer to "agent framework" than to any other
cluster. A secondary connection to [`g8-sci-agents`](../syntheses/repo-clusters/g8-sci-agents.md) is worth flagging if
the Phase 7+ biotech-policy commercial surface ever instantiates — at that point MiroFish-Offline's architecture would
inform a domain-specific scientific-policy-simulation agent, which is closer to g8.

Do **not** clone the non-Offline variants (`666ghj/MiroFish`, `666ghj/BettaFish`, `aaronjmars/MiroShark`) per the
Canteen note's Tier-2 framing ("reference-only unless one shows a notable architectural difference"). The Offline
variant captures the MiroFish family's relevant patterns; the upstream Chinese-market variants add cloud dependencies
and Chinese-language UI without architectural deltas worth a separate repo-note.

## 7. Questions for Dan

1. **Linus license posture — when does this get settled?** MiroFish-Offline's AGPL-3.0 license raises the question that
   has been deferred across the project: what license will Linus itself use? The cloned-repo collection contains AGPL
   projects (MiroFish-Offline), permissive projects (Letta Apache-2.0, debate-or-vote MIT, goose Apache-2.0), and
   varying-license MCP servers. Linus's eventual license choice has cascading implications for which upstream patterns
   can be lifted versus only inspired-by. Tentative answer: defer the formal license decision until Phase 5+ (when
   public release becomes scoped), but adopt a **working "Linus is permissively licensed in spirit" posture now** — no
   AGPL code lifts, no AGPL pattern lifts that survive a clean-room test, and an explicit ADR at Phase 5+ that commits
   to the final license (likely Apache-2.0 or MIT, per the broader Maestro-tooling ecosystem). Worth a Phase 5+
   spawner-spec or a separate license-posture ADR.

2. **Phase 7+ biotech-policy commercial surface — does this graduate from speculative to scoped?** The Canteen
   entrepreneurship synthesis (E-IDs framing in `canteen_blog_landscape_2026-05.md`) flags simulation-of-public-reaction
   as a possible Phase 7+ commercial direction adjacent to Dan's biotech-policy advisory work. The MiroFish-Offline
   architecture is the closest existing prior art for that direction. Tentative answer: leave it speculative until Phase
   6 lands and Phase 7 planning begins; at that point, revisit MiroFish-Offline as a primary architectural reference and
   either commission a clean-room reproduction or scope a wider survey of synthetic-population simulation tools (OASIS,
   Concordia from DeepMind, Generative Agents, etc.). The decision to even build a biotech-policy simulation product is
   itself a Maestro-level scoping question that depends on Dan's bandwidth and on whether LanzaTech or external advisory
   work surfaces a concrete commercial pull.

3. **Should Linus track a non-AGPL persona-based simulation reference instead of MiroFish-Offline?** If the
   architectural patterns in §3 are the durable takeaway and the AGPL constraint blocks code lifts, the question is
   whether to add a secondary reference repo-note for a permissively-licensed alternative. Candidates worth surveying:
   Concordia (DeepMind, Apache-2.0 — generative agent simulation), Generative-Agents-style reproductions (multiple,
   varying licenses), OASIS itself (CAMEL-AI, license to be checked). Tentative answer: yes, when Phase 7+ biotech-
   policy work scopes out per Q2; until then, MiroFish-Offline's repo-note serves as the architectural-reference
   placeholder and the AGPL caveat is sufficient gating. Re-survey at Phase 6 close.

4. **The hybrid 0.7 vector / 0.3 BM25 weighting — does Linus's domain need a higher keyword weight?** Per §3, biology
   and bioinformatics domains have unusually load-bearing lexical exact-matches (gene IDs, accession numbers, species
   names, PMIDs, compound IDs) where pure-vector retrieval underperforms on exact-token recall. MiroFish's 0.7/0.3
   default is calibrated for general-purpose Chinese-news-style entities. Tentative answer: include weighting sweep as a
   `benchmarks/dan_tasks/` axis at Phase 1c or Phase 2, with weights {0.5/0.5, 0.6/0.4, 0.7/0.3, 0.8/0.2} compared on
   Dan's actual genomics/metagenomics retrieval tasks. The empirical answer will inform the KnowledgeBase v1 default;
   the principle (hybrid is right; weighting is task-dependent) is the lift.

5. **`GraphStorage` ABC pattern at the KnowledgeBase substrate boundary — adopt at Phase 2 spec time, or defer?**
   MiroFish's `GraphStorage` ABC is a clean pattern for substrate portability, but adding an ABC at v0 is the kind of
   premature-abstraction trap The Algorithm warns against ("delete every step; add it back if it returns"). Tentative
   answer: defer the ABC until Phase 2 KnowledgeBase v1 is shipped against a concrete substrate (likely SQLite + content
   hashes per DEC-0029); add the ABC at v2 when the second substrate (pgvector for production, or Neo4j for richer graph
   queries) is being built. This matches the YAGNI principle and avoids the ABC-without-clear-second-impl smell. Worth
   resolution in the Phase 2 KnowledgeBase v1 spec.

6. **The persona vocabulary lift for Phase 7+ biology-skill auto-eval — design-ahead now, or wait for Phase 7 scoping?**
   §3 flags the OasisAgentProfile + AgentActivityConfig vocabulary (`sentiment_bias`, `stance`, `influence_weight`,
   `interested_topics`) as a starting point for a Linus persona-library at Phase 7+. The question is whether to design
   the Linus persona schema now (as part of the Phase 3 spawner spec, since DEC-0050 makes Role first-class) or wait
   until Phase 7+ when the biology-skill auto-eval surface concretizes. Tentative answer: defer until Phase 7+ — the
   Phase 3 spawner's Role-as-first-class commitment (DEC-0050) is sufficient v0 vocabulary, and adding a richer persona
   schema now is exactly the over-specification that DEC-0030 / DEC-0031 / DEC-0032 explicitly guard against. The
   MiroFish vocabulary is bookmarked design reference for the Phase 7+ revisit.

7. **OASIS as a separate repo-note — is the upstream simulation engine worth its own slot in the corpus?** OASIS
   (`camel-ai/oasis`) is the actual simulation substrate underneath MiroFish; its license posture and architectural
   shape are upstream-of-relevant. The Canteen note has it on the Tier-3 reference-only list. Tentative answer: defer
   until Phase 7+ scoping per Q2 — at that point, if biotech-policy simulation graduates to a real Linus product
   surface, OASIS becomes the primary repo-note candidate (with MiroFish-Offline reframed as "the productization layer
   on top of OASIS"). Until then, OASIS remains a one-line mention in the relevant synthesis.

8. **Should the §3 architectural-pattern lifts be gated through a project license-compatibility ADR before any are acted
   on?** The list in §3 (`GraphStorage` ABC, hybrid 0.7/0.3 weighting, persona vocabulary, hour-tick simulation, JSONL
   audit shape) are framed as "patterns that can be re-implemented Linus-native from upstream sources" — but the line
   between "pattern" and "code" is thin in practice, and a single careless agent-coding session could produce
   MiroFish-derivative code without a clean-room separation. Tentative answer: yes — write a short license-compatibility
   ADR (or extend DEC-0024's supply-chain posture) that specifies the clean-room procedure for AGPL-adjacent prior art
   before any §3 lift is commissioned. The procedure should require a pre-write upstream-source check, an explicit note
   in the resulting code that the design was informed by clean-room reading of upstream Neo4j / OASIS / hybrid- search
   literature (not by reading MiroFish-Offline source directly during the implementation session), and a
   license-compatibility review at PR time. The cost is a paragraph in DEC-0024; the upside is durable license
   discipline as the cloned-repo collection grows and license heterogeneity increases.
