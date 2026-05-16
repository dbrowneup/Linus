# Awesome-AI-Agent-Papers Gap Triage

**Status:** active **Date:** 2026-05-16 **Branch:** `agent/wave2-awesome-papers-triage` (base SHA `9b91b66`). **Owner:**
Maestro (Dan + Claude Code).

**Origin:** Wave-2 fan-out spec — pair with
[`docs/repo-notes/awesome-ai-agent-papers.md`](../repo-notes/awesome-ai-agent-papers.md). This spec is the operational
artefact that converts VoltAgent's curated 370-paper 2026 arxiv list into a prioritized fold-in plan for Linus's
`docs/paper-notes/` corpus.

**Related:**

- [`docs/repo-notes/awesome-ai-agent-papers.md`](../repo-notes/awesome-ai-agent-papers.md) — companion repo-note that
  frames the repo as a Watch-verdict ingestion source.
- [`docs/paper-notes/INDEX.md`](../paper-notes/INDEX.md) — the existing 118-paper-note catalogue used as the
  cross-reference base (70 with arxiv-style stems).
- [`docs/curation-log.md`](../curation-log.md) — destination for the corresponding fold-in batch entry when the
  follow-up HIGH-priority ingestion PR lands.

---

## 1. Method

The source repository ships a single curated `README.md` (~500 lines) with five `<details>`-block topical sections. Each
row in each section follows the pattern `**[Title](pdf-url)** - description | <a href=...arxiv-id...>`. This is
trivially regex-parseable into `(arxiv_id, section, title, description)` tuples. The parse script (regex two-step: split
on `<details ... id="..."` to assign section, then
`re.findall(r'\*\*\[(.+?)\]\([^)]+\)\*\*\s*-\s*(.+?)\s*\|\s*<a href="[^"]*?(\d{4}\.\d{4,5})')` per section) is ~30 lines
of Python and can live in `experiments/awesome-papers-parse.py` if/when promoted (Question 3 in the repo-note).

The Linus side is `docs/paper-notes/`. Of the 118 files in that directory (excluding INDEX.md), 70 have arxiv-style
stems that match `(?:[A-Za-z-]+-)?(\d{4}\.\d{4,5})(?:v\d+)?` — i.e., either plain arxiv IDs (`2412.17794v1.md`) or the
hybrid paired-repo variant (`Kimi-K2-2507.20534.md`). The remaining 48 paper-notes are non-arxiv (bioRxiv,
Nature/Science DOIs, NIH PMC IDs, hand-named whitepapers) and are by construction outside the awesome-list's
arxiv-only scope.

The cross-reference is set-intersection on arxiv ID (version-stripped). Topic categorization is the awesome-list's own
(Multi-Agent, Memory & RAG, Eval & Observability, Agent Tooling, AI Agent Security). Prioritization is a
keyword-weighted score over title + description against ~60 Linus-relevance keywords (memory, episodic, MCP, model
context protocol, orchestration, latency-aware, persistent memory, scratchpad, COCONUT, continuous latent, BitNet,
low-bit, mmap, weight streaming, prompt injection, supply chain, sandbox, capability-based, paper-qa, etc.); the
top-scoring papers are then manually filtered for non-redundant Linus-thread fit.

---

## 2. Coverage stats

| Metric                                             | Count |
| -------------------------------------------------- | ----- |
| Unique arxiv IDs in awesome-ai-agent-papers README | 370   |
| Linus paper-notes total                            | 118   |
| Linus paper-notes with arxiv-style stems           | 70    |
| Overlap (already in Linus corpus)                  | **0** |
| Gap (awesome-list IDs absent from Linus corpus)    | 370   |

**Section distribution of the 370 gap papers:**

| Section              | Count |
| -------------------- | ----- |
| Agent Tooling        | 95    |
| AI Agent Security    | 83    |
| Eval & Observability | 80    |
| Memory & RAG         | 57    |
| Multi-Agent          | 55    |

**Date distribution (arxiv year-month prefix):**

| Prefix | Papers | Window                                           |
| ------ | ------ | ------------------------------------------------ |
| 2504   | 1      | April 2025 (one outlier predating "2026 onward") |
| 2601   | 299    | January 2026                                     |
| 2602   | 65     | February 2026                                    |
| 2603   | 1      | March 2026                                       |
| 2604   | 4      | April 2026 (most recent)                         |

The 0-overlap finding is **expected, not anomalous**. Linus's 70 arxiv paper-notes cluster in 2023–2025 (BitNet, Llama
3, MemGPT, Coconut, ARC Prize 2024) with a small 2026 set that is predominantly bioRxiv-numbered (2026.02.XX,
2026.04.XX) plus a couple of older arxiv papers (2602.\* manifold-ML and DeepSeek-vintage). The awesome-list's filter
("2026 onward, arxiv, AI-agent-themed") slices a corpus segment Linus's existing arxiv ingestion has not yet swept. The
gap-triage's job is therefore not redundancy-pruning but **freshness ingestion**.

---

## 3. Top high-priority gap candidates (15+ ranked)

The HIGH/MEDIUM/LOW tiers below reflect Linus-relevance: HIGH means a Linus synthesis or open question is currently
active and the paper is a direct input; MEDIUM means relevant when an adjacent thread reactivates; LOW means
tracked-for-completeness with no immediate fold-in pull.

### HIGH priority — fold soon (10 papers)

1. **2601.21714** — _E-mem: Multi-agent based Episodic Context Reconstruction for LLM Agent Memory_ (memory--rag).
   Episodic-memory framework where assistant agents maintain uncompressed contexts and a master agent orchestrates
   global planning, **replacing destructive memory compression with context reconstruction**. Directly load-bearing for
   Layer C (cross-session episodic) and the no-silent-truncation discipline in
   [`docs/specs/memory-architecture.md`](memory-architecture.md) (DEC-0030, DEC-0032). The "context reconstruction"
   framing is exactly the substrate the Linus episodic schema (DEC-0039 hybrid leaf+summary) should be benchmarked
   against.

2. **2601.13671** — _The Orchestration of Multi-Agent Systems: Architectures, Protocols, and Enterprise Adoption_
   (multi-agent). Formalizes orchestrated MAS integrating **MCP + Agent2Agent protocol** for peer coordination,
   delegation, policy enforcement. Directly maps to DEC-0018 (MCP as tool-extensibility substrate), DEC-0050
   (role-first-class type), DEC-0051 (AgentReport contract), and the Phase 2a session-store/dispatch design. May provide
   the protocol-level vocabulary Linus's spawner spec ([`docs/specs/phase3-spawner.md`](phase3-spawner.md)) currently
   lacks.

3. **2601.11595** — _Enhancing Model Context Protocol (MCP) with Context-Aware Server Collaboration_ (agent-tooling).
   Proposes Context-Aware MCP with a **Shared Context Store** for MCP servers to coordinate autonomously. Directly
   relevant to DEC-0018 + DEC-0045 (fastmcp default), and to the in-context-cap policy (DEC-0032) — Shared Context Store
   is a candidate Layer B/C bridge.

4. **2601.01241** — _MCP-SandboxScan: WASM-based Secure Execution and Runtime Analysis for MCP Tools_ (security).
   Lightweight framework that **safely executes untrusted MCP tools inside a WASM sandbox** and produces auditable
   reports. Directly applicable to SAFETY.md sandbox policy and the long-running open question of whether Linus's tool
   registry needs a capability-based isolation layer (DEC-0046 external-API field, DEC-0024 supply-chain posture).

5. **2601.17549** — _Breaking the Protocol: Security Analysis of the Model Context Protocol Specification_ (security).
   **First security analysis of the MCP specification**, identifies three protocol-level vulnerabilities and proposes
   backward-compatible extensions. Pair-read with DEC-0018; should drive an ADR seed on Linus's MCP server hardening
   posture before Phase 2a tool registry lands.

6. **2602.06052** — _Rethinking Memory Mechanisms of Foundation Agents in the Second Half: A Survey_ (memory--rag).
   Surveys foundation agent memory organized by substrate (internal/external), cognitive mechanism (episodic, semantic,
   working, procedural), subject (agent- vs user-centric). **Directly maps to Linus's 5-layer memory architecture**
   (Layer A–E in DEC-0028+). The taxonomy is a sanity-check on Linus's own decomposition; gaps either way are mineable.

7. **2602.05665** — _Graph-based Agent Memory: Taxonomy, Techniques, and Applications_ (memory--rag). Surveys
   graph-based memory architectures for agents — extraction, storage, retrieval, temporal evolution. Maps to `g4-memory`
   cluster, DEC-0039 (hybrid leaf+summary), and the long-running KG/RAG question (DEC-0015 dual graph substrates).
   Should be folded into `memory-synthesis.md` and `g4-memory.md` as a survey reference.

8. **2601.07395** — _MCP-ITP: An Automated Framework for Implicit Tool Poisoning in MCP_ (security). Implicit tool
   poisoning attack where **poisoned tool remains uninvoked but its metadata manipulates the agent into using legitimate
   tools maliciously**. Pair-read with 2601.01241 and 2601.17549; collectively these three define the MCP-security
   threat model Linus needs before Phase 2a tool registry deployment.

9. **2601.05504** — _Memory Poisoning Attack and Defense on Memory Based LLM-Agents_ (security). Evaluates memory
   poisoning attacks and proposes two defenses (input/output moderation + memory sanitization with trust-aware
   retrieval). Directly relevant to the Layer C/D durability discipline and the audit-log surface DEC-0028 prescribes.

10. **2604.01658** — _CORAL: Towards Autonomous Multi-Agent Evolution for Open-Ended Discovery_ (multi-agent).
    Long-running multi-agent systems that **self-evolve via shared persistent memory, asynchronous execution, and
    heartbeat-based interventions**; 3–10× higher improvement rates than fixed evolutionary-search baselines. The
    persistent-memory + async-execution + heartbeat shape is directly relevant to Phase 3 agent fan-out (DEC-0050) and
    the worktree fan-out discipline (CLAUDE.md §Worktree fan-out discipline).

### MEDIUM priority — fold when adjacent thread is active (10 papers)

11. **2601.10560** — _Learning Latency-Aware Orchestration for Parallel Multi-Agent Systems_ (multi-agent).
    Latency-aware MAS orchestration that **optimizes critical execution path under parallel execution**. Relevant to
    Phase 2a session-store design and the workgraph-JSONL adoption signal — fold when the session-store ADR is drafted.

12. **2602.01848** — _ROMA: Recursive Open Meta-Agent Framework for Long-Horizon Multi-Agent Systems_ (multi-agent).
    Subtask-tree parallel execution to handle **long-horizon workflows without exceeding context windows**. Pair-read
    with E-mem (#1) and StackPlanner (#19) when Phase 3 agent-spawner spec is reactivated.

13. **2601.07190** — _Active Context Compression: Autonomous Memory Management in LLM Agents_ (memory--rag).
    Agent-centric architecture inspired by Physarum polycephalum where the agent **autonomously decides when to
    consolidate and prune**. Adjacent to DEC-0032 (in-context cap policy) and the no-silent-truncation rule;
    biologically-inspired framing makes for an interesting comparison with Linus's hybrid leaf+summary schema.

14. **2601.18642** — _FadeMem: Biologically-Inspired Forgetting for Efficient Agent Memory_ (memory--rag). **Adaptive
    exponential decay, LLM-guided conflict resolution, dual-layer hierarchy**. Relevant to memory-layer eviction policy
    — currently underspecified in DEC-0028+. Fold when memory-architecture spec moves from contract to implementation.

15. **2601.05111** — _Agent-as-a-Judge_ (eval). Evolution from LLM-as-Judge to Agent-as-Judge with **planning,
    tool-augmented verification, multi-agent collaboration, persistent memory**. Adjacent to DEC-0040 (CoT faithfulness
    audit deferred) and the agentic-systems synthesis's evaluation-substrate question.

16. **2601.19935** — _Mem2ActBench: A Benchmark for Evaluating Long-Term Memory Utilization in Task-Oriented Autonomous
    Agents_ (eval). Benchmarks whether agents **proactively use long-term memory to execute actions**, not just retrieve
    facts. Direct evaluation tool for Layer C/D in [`docs/specs/memory-architecture.md`](memory-architecture.md); ingest
    when the memory implementation needs an external benchmark.

17. **2601.17548** — _Prompt Injection Attacks on Agentic Coding Assistants: A Systematic Analysis_ (security). Surveys
    78 studies with a **three-dimensional taxonomy across delivery vectors, modalities, propagation**. Background
    reading for `safety-alignment-privacy-synthesis.md`; fold when the SAFETY.md autonomy-tier graduation review is next
    on deck.

18. **2601.10923** — _Hidden-in-Plain-Text: A Benchmark for Social-Web Indirect Prompt Injection in RAG_ (security).
    End-to-end **benchmark and harness for web-facing RAG under indirect prompt injection**. Relevant if Linus ever
    exposes a web-ingesting tool surface — currently not on the Phase 1–4 roadmap but Phase 5+ adjacent.

19. **2601.05890** — _StackPlanner: A Centralized Hierarchical Multi-Agent System with Task-Experience Memory
    Management_ (multi-agent). Hierarchical MAS with **active task-level memory control and RL-driven experience
    reuse**. Adjacent to Layer D (investigation memory, DEC-0052) and Phase 3 spawner; pair-read with ROMA (#12).

20. **2601.08012** — _Towards Verifiably Safe Tool Use for LLM Agents_ (security). **System-Theoretic Process Analysis**
    to derive formal safety specifications enforced through a capability-enhanced MCP framework. Adjacent to DEC-0024
    (security posture) and the SAFETY.md tier-graduation discipline; the capability-enhanced MCP angle pairs with #4 and
    #5.

### LOW priority — watch only (sample of 4)

21. **2601.06606** — _CEDAR: Context Engineering for Agentic Data Science_ (agent-tooling). Context-engineering
    techniques including **separate plan and code agents, smart history rendering**. Domain-overlapping with Dan's
    LanzaTech computational-biology work but the cross-application generalization to Linus's Phase 2a is indirect.
    Watch.

22. **2601.07004** — _MemTrust: A Zero-Trust Architecture for Unified AI Memory System_ (security). **TEE protection
    across five functional layers**. Interesting concept but TEE-based hardware-trust is operationally out of scope for
    Linus's MacBook-resident substrate (no Secure Enclave-resident memory store on Apple Silicon that Linus would
    actually use). Watch as architectural reference only.

23. **2601.10955** — _Beyond Max Tokens: Stealthy Resource Amplification via Tool Calling Chains in LLM Agents_
    (security). **658x cost amplification via MCP-compatible tool server modifications**. Vivid threat model; relevance
    is gated on Linus ever exposing a paid tool surface (DEC-0046 external-API field — currently dormant). Watch.

24. **2602.06495** — _Subgraph Reconstruction Attacks on Graph RAG Deployments with Practical Defenses_ (security).
    Graph-RAG-specific attack class. Relevant if/when Linus's KnowledgeBase exposes a Graph RAG surface to external
    queries; current KB scope is internal-only, so this is Phase 5+ adjacent.

The full sortable scored list (40+ candidates) lives in the Python-script output and is regeneratable; the deliverable
here is the top-20 with categorization. Beyond #24, scores fall steeply (≤6) and Linus-relevance is mostly
"topic-adjacent, no active thread."

---

## 4. Topic-distribution summary

Of the top 20 ranked HIGH+MEDIUM gap candidates, the synthesis-bin destination distribution is:

| Synthesis bin                                                                            | Count | Notes                                                                                                                              |
| ---------------------------------------------------------------------------------------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------- |
| [memory-synthesis](../syntheses/memory-synthesis.md)                                     | 7     | E-mem, Active Context Compression, FadeMem, two surveys, Mem2ActBench, Memory Poisoning                                            |
| [agentic-systems-synthesis](../syntheses/agentic-systems-synthesis.md)                   | 5     | MAS Orchestration, CORAL, ROMA, StackPlanner, Latency-Aware                                                                        |
| [safety-alignment-privacy-synthesis](../syntheses/safety-alignment-privacy-synthesis.md) | 6     | Six security papers (MCP-SandboxScan, MCP-ITP, Breaking-Protocol, Memory Poisoning, Prompt Injection Coding, Hidden-in-Plain-Text) |
| MCP-specific (cross-cuts agentic-systems + safety)                                       | 4     | Context-Aware MCP, Sandbox, ITP, Breaking-Protocol                                                                                 |
| [skills-and-practices-synthesis](../syntheses/skills-and-practices-synthesis.md)         | 2     | Agent-as-a-Judge, Verifiably Safe Tool Use                                                                                         |

The dominant synthesis-bin destinations are **memory** (Layer C/D implementation drivers + surveys), **agentic-systems**
(orchestration protocols + long-horizon multi-agent patterns), and **safety-alignment-privacy** (MCP-specific threat
models). This is consistent with where Linus's open ADR seeds cluster: DEC-0028+ (memory layers), DEC-0050/0051
(spawner + AgentReport), DEC-0018/0045 (MCP substrate).

**Synthesis-pass focus implication.** The next synthesis fold-in pass should prioritize **memory-synthesis** and
**safety-alignment-privacy-synthesis** — the candidates flagged here are the most directly mineable for synthesis
refinement and would close visible coverage gaps (the existing memory-synthesis is anchored on 2023–2025 work; six 2026
candidates would refresh the front edge).

A note on what's **not** in the high-priority set: the awesome list's Agent Tooling section (95 papers, the largest)
contributes only #3 (Context-Aware MCP) and #21 (CEDAR) to the top 20. The reason is taxonomic — most Agent-Tooling
papers are taxonomy/survey/framework descriptions whose abstracts read as "yet another agent framework with X
distinctive feature." Without a Linus-thread to absorb them, they score low. The same is true for many Eval &
Observability entries: most are benchmark introductions for narrow tasks (game balancing, hospital admin, recommender
systems) that do not crosscut Linus's substrate.

---

## 5. Recommended action

**Bulk-ingest the 10 HIGH-priority gap papers in a follow-up Wave-3 PR.** Each ingestion follows the standard paper-note
process: download PDF to `context/papers/`, author `docs/paper-notes/<arxiv-id>v<N>.md` per CLAUDE.md §Doc-type
conventions (paper-note variant), fold into the relevant thematic synthesis, update INDEX, log batch in
`curation-log.md`. Estimated effort: ~6 hours for 10 papers (canonical paper-note process is ~30 min/paper at Worker
speed once the PDF is in hand).

**Track the 10 MEDIUM-priority candidates here for on-demand pull.** When the adjacent thread reactivates — e.g., the
Phase 3 spawner spec moves from stub to implementation, or the memory-architecture spec moves from contract to code —
pull the relevant MEDIUM papers at that point. No bulk ingest needed; the spec is the durable tracker.

**Defer the LOW-priority and unscored ~350 papers.** They remain accessible via the awesome-list itself. The next
quarterly curation review (next: 2026-08-01) re-runs the cross-reference; any LOW-priority candidates that have become
HIGH because a Linus thread shifted are surfaced then. The awesome-list will also have grown by ~13 weeks of weekly
updates by then, so the next sweep covers both the deferred-LOW set and the new arrivals.

**Operational housekeeping for the Wave-3 PR:**

- Commit the parse script to `experiments/awesome-papers-parse.py` (per repo-note Question 3) — useful for the
  2026-08-01 re-sweep and any interim ad-hoc pulls.
- Append a curation-log entry under 2026-05-XX (date of Wave-3 PR) with the 10 paper-note additions, citing this spec.
- Bonus: update `docs/syntheses/memory-synthesis.md` and `docs/syntheses/safety-alignment-privacy-synthesis.md` to cite
  the new 2026-vintage papers inline; this is the natural "synthesis-pass focus" implication from §4.

---

## 6. Time accounting

- **Estimated wall time:** 90 minutes (per the Wave-2 fan-out brief).
- **Actual wall time:** to be measured at PR close; recorded here for the "measure, don't just estimate" convention.
- **Variance notes:** to be appended at consolidation.
