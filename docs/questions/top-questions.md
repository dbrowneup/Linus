# Top Questions

A consolidated, prioritized subset of the open questions in
[open-questions.md](open-questions.md). Organized into three tiers by how much
each answer changes the next concrete action — not by how interesting they are.

The full per-source list is preserved in `open-questions.md` as a reference; this
document is the working agenda. Questions that recurred across multiple notes
have been merged. Questions that were really invitations to do small writeups
("worth a synthesis note?") have been collapsed into a single tier-3 entry on
documentation cadence.

---

## NEW: Memory Pillar (added 2026-05-03)

A new round of questions surfaced by the [memory synthesis](../syntheses/memory-synthesis.md)
and the eleven Garrison-thread paper notes. The full set lives in
[open-questions.md](open-questions.md) under "Memory pillar — Garrison thread" and
"Memory Synthesis"; the items below are the ones that *change next concrete action* and
deserve a slot in the next planning session. None are resolved.

**Tier 1 (memory-pillar) — block Phase 2 architecture decisions**

- **M1. Lift memory architecture from Phase 3+ to a Phase 2 first-class deliverable.** Write
  `docs/specs/memory-architecture.md` walking through four layers (intra-step latent /
  within-session scratchpad / cross-session episodic / semantic-knowledge), the four
  sub-requirement obligations from Garrison's framework (addressability, disambiguation,
  temporal order, integrity), and the substrate choice per layer, *before* the orchestration
  layer's session and dispatch primitives are written. The synthesis argues this is the
  load-bearing Phase 2 commitment; the complexity-theoretic results
  ([2305.15408](../paper-notes/2305.15408v5.md), [2310.07923](../paper-notes/2310.07923v5.md))
  supply the formal pressure. *(Source: memory synthesis Q6; spans most papers in the
  Garrison thread.)*

- **M2. Substrate choice for cross-session episodic memory (Layer C).** Conservative
  v0 (SQLite + content hashes + git as persistence substrate) vs. ambitious
  parametric-via-LoRA-consolidation (Akyürek-style TTT applied to session transcripts) vs.
  hybrid where knowledge graduates from text into LoRA after sufficient repeated access?
  The Phase 2 spec should not commit to (3) but should not preclude it either.
  *(Source: memory synthesis Q1; [TTT 2411.07279 Q1](../paper-notes/2411.07279v2.md);
  [TTT Q3](../paper-notes/2411.07279v2.md).)*

- **M3. Scratchpad as a first-class durable artifact (forbid the o1 anti-pattern).**
  Phase 2 session store treats reasoning tokens as durable, addressable artifacts on
  equal footing with final answers and tool outputs (addressed by `(session_id, turn_id)`,
  hashed for integrity). The Worker protocol spec explicitly forbids any integration that
  silently truncates reasoning between turns. The complexity-theoretic results say this is
  not optional. *(Source: [Merrill & Sabharwal 2310.07923 Q1](../paper-notes/2310.07923v5.md);
  [Feng et al. 2305.15408 Q1](../paper-notes/2305.15408v5.md);
  [Sparks 2303.12712 Q1](../paper-notes/2303.12712v5.md);
  [Kojima 2205.11916 Q1](../paper-notes/2205.11916v4.md).)*

- **M4. Two new router primitives: per-call CoT budget and per-call memory mode.** CoT
  budget (logarithmic / linear / polynomial per Merrill & Sabharwal regimes) is set per
  task class. Memory mode (stateless / session-stateful / project-stateful) determines
  which prefix is loaded from which memory layer before dispatch. Both are router
  *primitives* — adding them later is harder than building them in.
  *(Source: memory synthesis Q5; [Feng et al. 2305.15408 Q2](../paper-notes/2305.15408v5.md);
  [Merrill & Sabharwal 2310.07923 Q2](../paper-notes/2310.07923v5.md).)*

- **M5. In-context window cap policy.** Even when the underlying Worker supports 128K
  context (Llama 3.1 8B does), Linus deliberately caps in-context usage at 8–16K and
  routes beyond that through the episodic store. Setting the policy up front prevents
  the lazy "just stuff everything in context" pattern that gives away the architectural
  advantage of having a real episodic store.
  *(Source: [Llama 3 2407.21783 Q2](../paper-notes/2407.21783v3.md); memory synthesis
  hype filter.)*

**Tier 2 (memory-pillar) — shape Phase 2–6 architecture**

- **M6. Per-Worker CoT-gap fingerprint as a registry property.** Run a 50-item
  MultiArith-style smoke test on every Ollama-pulled model, store
  `accuracy_with_CoT - accuracy_without_CoT` in the model registry. The router uses the
  delta to decide whether to inject a CoT trigger and how much budget to allocate. Cheap
  to run, expensive to omit. *(Source: [Kojima 2205.11916 Q3](../paper-notes/2205.11916v4.md).)*

- **M7. Worker-size vs CoT-length empirical comparison.** Phase 1 benchmark: a 7B Worker
  with generous CoT budget vs. a 14B Worker with terse output on Dan's task suite. Theory
  predicts small-with-CoT wins on inherently sequential tasks; this is a falsifiable claim
  worth testing before committing to Worker-selection heuristics.
  *(Source: [Feng et al. 2305.15408 Q3](../paper-notes/2305.15408v5.md);
  [Kojima 2205.11916 Q5](../paper-notes/2205.11916v4.md).)*

- **M8. ARC-AGI as a memory diagnostic (not a target).** Take 50–100 ARC-AGI public-eval
  tasks, run a small Linus Worker against them twice — once without episodic memory,
  once with — and measure the delta. Turns the memory thesis into a number; costs nothing
  in Maestro tokens. *(Source: [ARC Prize 2024 2412.04604 Q1](../paper-notes/2412.04604v2.md);
  memory synthesis Q4.)*

- **M9. KV-cache continuity as an architectural constraint.** Linus inference layer
  commits to preserving KV cache across Worker turns within a session as a hard
  requirement, given that recursion-via-feedback is what the expressivity result hinges
  on. Affects which inference servers (Ollama, mlx-lm, future pmetal) are viable Worker
  backends. *(Source: [Feng et al. 2305.15408 Q4](../paper-notes/2305.15408v5.md).)*

- **M10. Apple-Silicon viability of TTT.** Phase 1 spike: 10 ARC tasks, Llama-3.2-1B,
  mlx-lm LoRA, leave-one-out synthetic data — purely to measure per-task compute cost on
  M1 Max. Determines whether parametric episodic-memory consolidation is on the table at
  all for Phase 6+. *(Source: [TTT 2411.07279 Q2](../paper-notes/2411.07279v2.md).)*

- **M11. minGRU MLX port as a memory-substrate spike.** Port the few-line minGRU/minLSTM
  PyTorch reference to MLX, run the Shakespeare experiment on M1 Max, publish the result.
  Low-cost, high-information experiment that establishes whether parallel-scan recurrence
  is a real local training option for memory-pillar components.
  *(Source: [Were RNNs all we needed? 2410.01201 Q2](../paper-notes/2410.01201v3.md).)*

- **M12. Compute-as-memory accounting in ARCHITECTURE.md.** Treat memory budget as a
  first-class architectural quantity, with the o3 figure ($1.15M for 91.5% on ARC-AGI) as
  the cautionary upper bound and human-with-pen-and-paper as the lower bound. The point is
  to make implicit "we'll just retry until it works" choices legible.
  *(Source: [ARC Prize 2024 2412.04604 Q5](../paper-notes/2412.04604v2.md); memory
  synthesis Q3.)*

**Tier 3 (memory-pillar) — documentation, conventions, longer-horizon scope**

- **M13. Episodic memory schema for multi-step Worker tasks.** Full reasoning trace per
  step, summary, or hybrid (full at the leaf, summary at the parent)? Decides shortly after
  the v0 episodic store is built. *(Source: [Kojima 2205.11916 Q4](../paper-notes/2205.11916v4.md);
  [Coconut 2412.06769 Q2](../paper-notes/2412.06769v3.md).)*

- **M14. Faithfulness audit of stored reasoning traces.** Phase 3 component that audits
  CoT for self-consistency, or out of scope until specific failure modes appear?
  *(Source: [Feng et al. 2305.15408 Q5](../paper-notes/2305.15408v5.md); memory
  synthesis Q2.)*

- **M15. minGRU + BitNet cross-product as Phase 8 research direction.** "minGRU with
  BitLinear gates" as the most extreme hardware-friendly substrate (recurrent + 1-bit +
  Apple-Silicon-friendly). Phase 8 candidate; no Phase 6/7 work gated on it.
  *(Source: [Were RNNs all we needed? 2410.01201 Q4](../paper-notes/2410.01201v3.md);
  [BitNet line](../paper-notes/2402.17764v1.md).)*

- **M16. Coconut-style latent recurrence as a Phase 6 substrate experiment.** Is the Meta
  reference implementation MLX-portable, or is iCoT the more practical lead for Linus's
  compute budget? *(Source: [Coconut 2412.06769 Q3](../paper-notes/2412.06769v3.md).)*

- **M17. Memory mode as a Linus-trained model fine-tuning target.** Phase 6 fine-tune
  absorbs the trigger sentence so that step-by-step decomposition for system-2 queries is
  default behavior — and additionally trains the model to produce *episodic-store-friendly*
  output (typed tags on facts, deliberation vs. conclusion separation, branch-point
  surfacing per Coconut).
  *(Source: [Kojima 2205.11916 Q6](../paper-notes/2205.11916v4.md);
  [Coconut 2412.06769 Q2](../paper-notes/2412.06769v3.md).)*

The memory-pillar items above are *unresolved* as of 2026-05-03; the existing Tier 0/1/2/3
items below the line carry their previous (May 2026) resolutions. The next planning session
should walk M1–M5 first (the Tier 1 set), then sample from M6–M12 as time allows.

---

## Resolution Log (2026-05-03)

All Tier 0, 1, 2, and 3 items resolved in a Maestro/Dan planning session on 2026-05-03.
Each entry below uses `[Q]: <one-line resolution>` where `Q` links to the in-document
question. Full implementation detail is in
[../specs/planning-update-spec.md](../specs/planning-update-spec.md).

**Tier 0 — Immediate actions**

- [Q](#0-remove-pre-emptive-ml-framework-dependencies-from-environmentyml): Confirmed; remove langchain/langgraph/haystack-ai from environment.yml; add hash-pinned `requirements-locked.txt` via `pip-compile --generate-hashes`; document dep philosophy in CLAUDE.md. streamlit and lm-eval stay (closer-term Phase 1c/2). → spec task.
- [Q](#1-write-and-commit-an-incident-response-protocol-to-safetymd): Confirmed; draft "Supply Chain Incident Response" section in SAFETY.md covering trigger / containment / credential rotation / attestation. → spec task.

**Tier 1 — Decisions blocking Phase 1 / Phase 2**

- [Q](#1-is-the-first-concrete-phase-1-spike-bitnet-2b4t--bitnetcpp-on-m1-max-benchmark-vs-ollama-qwen25llama-32): Adopt as the first concrete Phase 1c experiment using task-completion-time methodology in `benchmarks/dan_tasks/`. Threads with Tier 3 #19 and 1-bit viability question. → DEC.
- [Q](#2-inference-backend-pmetal-vs-ollamamlx-lm-ft-decided-by-phase-1b-evaluation): pmetal is the lead pending Phase 1b verdict. Build flags: `--features serve,mlx,trainer` for 1b; defer `ane,distill,data`. Concurrency: single-request tok/s + RSS for verdict; 5-concurrent is Phase 2a concern. Dependency risk: pin commit, document Ollama+mlx-lm-ft fallback in ADR 0001, revisit quarterly. → DEC.
- [Q](#3-phase-6-fine-tuning-path-native-1-bit-bonsai2b4t-vs-bitdistill-fp16--158-bit-vs-fp16-lora-fallback): Defer the lane decision until Phase 1c BitNet data lands. Phase 6a commits to FP16-LoRA on genomics/biochem corpus regardless. Decision gate at Phase 6a/6b boundary. → DEC.
- [Q](#4-knowledgebase-data-model-rdf-vs-property-graph): **Dual approach** — both RDF (rdflib + optional Oxigraph) and property graph (networkx; Kuzu evaluated later). KB already started both with rdflib + networkx as deps. Linus exposes both via separate tool families. Introduces **[KB-spec] split convention** for spec-parts that primarily impact KnowledgeBase. → DEC × 2.
- [Q](#5-harness-plurality-converge-to-one-front-end-or-run-all-four-indefinitely): Maintain plurality through Phase 5 with explicit role designations. Claude Code = hosted Maestro; cline = VS Code Worker; claw-code-local = terminal local-model; openclaw = chat/voice/canvas/mobile. No per-harness gold-plating. Pre-answers Tier 2 #6: adopt MCP. → DEC.
- [Q](#6-kb-ingest-quality-gate-what-are-the-right-domain-criteria-for-dans-scientific-fields): YAML-policy framework adopted as a **quality surface, not a hard gate** (Dan is the primary filter). Domain-agnostic baseline signals; preprints flagged not rejected; no hard reject lane in Phase 2. FineWeb-style calibration deferred to Phase 3 as a learning exercise. **[KB-spec]** item. → DEC.

**Tier 2 — Decisions shaping Phase 2–6 architecture**

- [Q](#6-mcp-as-the-extensibility-substrate): Adopt MCP. Phase 2 tool registry built MCP-shape from the start. pmetal's 45-tool MCP server is first external integration target. Evaluate `fastmcp`. Updates DEC-0005. → DEC.
- [Q](#7-kb-embedding-pipeline-idf--firstlast--quantile-u-recipe-vs-modern-encoder-bgee5-baseline): Run a unified Phase 2 ablation (SPECTER2 raw / +Stankevičius post-processing / BGE-base / +post-processing / random+post-processing) × {full-dim, PCA-256/384/512}. Distance-discrimination `|D_max − D_min| / D_min` adopted as continuous KB health metric. Resolves Curse-of-Dim Q1+Q2 in one experiment. **[KB-spec]**.
- [Q](#8-kv-cache-compression-as-a-near-term-linus-feature): Defer as explicit Phase 2 feature. Apply The Algorithm. Enable only if free config flag in pmetal/bitnet.cpp/mlx-flash. Revisit Phase 6+.
- [Q](#9-ane-in-phase-1b-or-defer-entirely): Defer to Phase 2 as conditional follow-up benchmark, gated on favorable pmetal Phase 1b verdict. Phase 1b/1c primary backends: Ollama-CPU/GPU, pmetal-GPU, bitnet.cpp-CPU.
- [Q](#10-mlx-flash-vs-flash-moe-philosophy-when-forced-to-choose): Commit Phase 5+ to mlx-flash as the >RAM dense path. flash-moe stays methodology-only reference. → DEC.
- [Q](#11-streaming--1-bit-composite-path): Phase 6d formal target = mlx-flash streams any fine-tuned model exceeding RAM. Phase 6d stretch target = opportunistic ternary >8B integration if PrismML/community releases. Phase 8 BitNet × Flash-MoE × JPmHC stays long-horizon.
- [Q](#12-the-flash-moe-target-on-m1-max-32-gb): Commit to the practice. Once Phase 1b closes, draft `docs/specs/phase6d-streaming-target.md` with concrete model + tok/s target.
- [Q](#13-does-linus-need-a-custom-orchestration-layer-or-will-task-master-ai--cline-cover-phase-2): Keep DEC-0002 (custom orchestration). Algorithm-check primitives via **new Phase 1f deliverable**: evaluate Task Master AI + claude-squad vs. custom prototype vs. pmetal-MCP-as-orchestrator on a real Phase 2 task spec. Adopt PRD→tasks pattern as a skill, not a re-implementation. → DEC refining DEC-0002.
- [Q](#14-should-dan-start-monetizing-ai-capabilities-now-before-linus-infrastructure-is-ready): Skip the binary. New Phase 2 deliverable: `docs/entrepreneurial-surface.md`. Don't actively pursue clients yet; don't rule out either. Re-evaluate when Linus closer to operational.
- [Q](#15-phase-5c-deferred-or-done): Mark Phase 5c as "adopt claw-code-local" formally. Remove 500-line custom Python agent fallback from ROADMAP. → DEC amending DEC-0007.
- [Q](#16-parallel-worker-kb-write-coordination): Serialized writes through coordinator + write-time contradiction surfacing. Workers emit JSON-shaped diff proposals; coordinator merges; conflicts flag for human review. Git-branch-per-ingest underneath. **[KB-spec]**: `docs/specs/kb/parallel-worker-write-coordination.md`.

**Tier 3 — Documentation, conventions, longer-horizon scope**

- [Q](#19-benchmark-architecture-toks-vs-task-completion-time): `benchmarks/dan_tasks/` structured around three-task schema with wall-clock as **primary** axis. Multiple metrics recorded (tok/s, RSS, TTFT, completion time, quality score) — Worker selection holistic. Public eval baselines run alongside.
- [Q](#20-kb-ingestion-keyphrase-strategy-rakun-20-as-the-phase-2-baseline): **Integrate-and-evaluate, not adopt outright.** RaKUn 2.0 enters KB as additional tool alongside existing TF-IDF + BERTopic + SPECTER2 + UMAP pipeline. Phase 2 evaluation produces empirical comparison; possibly retain both as parallel signals. **[KB-spec]**.
- [Q](#21-security-posture-decisions-lock-files-dependency-philosophy-incident-protocol): (1) Full hash pinning + monthly pip-audit + quarterly review. (2) **Untrusted experimental packages always in disposable `uv` envs**; uv installed via conda inside linus env. (3) CVE response folded into SAFETY.md incident protocol. → DEC.
- [Q](#22-output-interface-design-optimize-for-the-10-bitss-human-review-channel): Adopt 10-bits/s framing as Phase 2 design principle. **Balanced bullets + prose** (not bullet dumps). **Citations and traceability are first-class.** Worker outputs preserved for Maestro inspection. Opt-in `/verbose`. **Linus reframed as personal LLM Wiki at scale.** → DEC.
- [Q](#23-which-community-repos-to-clone-into-repos-as-phase-2-3-references): **Clone all 12 community repos** + future additions. Phase 1a expanded (or 1f addendum) to include their notes. **New curation protocol** for repos/, context/, docs/ with archive log. → DEC.
- [Q](#14-documentation-cadence-and-synthesis-docs): Two load-bearing notes adopted: `docs/specs/kb-architecture.md` ([KB-spec], Phase 2) and `docs/experimental-protocol.md` (Phase 1c). BitNet-on-Apple-Silicon synthesis deferred to post-Phase 1c results. flash-moe case study deferred to Phase 5+.
- [Q](#15-phase-4-scope-ambition-how-much-beyond-kiwix--pmtiles--qdrant): Full English Wikipedia (~100 GB) from start as foundation for personal LLM Wiki. **Kolibri as parallel benchmark surface** (`benchmarks/kolibri_tasks/`). Planet-wide PMTiles target with population-density fallback. English-only confirmed. CyberChef/ArchiveBox/Qdrant deferred. Owner location updated (Hawthorn Woods, IL).
- [Q](#16-linus-practice-and-stance-questions): All six stances adopted with refinements: trust OS page cache (convention); public APIs only for Linus's own code (pmetal uses supported APIs, ANE is the private-API anchor); multi-language stance (Python core, Rust/JS/TS/bash for components); light VISION.md sovereignty refinement; reproducibility + interpretability principle; Obj-C/Metal-direct deferred (not ruled out). → DEC.
- [Q](#17-methodology-and-tooling): autoresearch program.md → SKILL.md in Phase 7. Per-experiment budget: 30+ min on Dan task suite as default. First autoresearch use: **Phase 1b pmetal LoRA trial.** Cline prompt-variant pattern: Phase 7.
- [Q](#18-smaller-open-items): All 13 batch items resolved. See spec for one-liner per item.

**New meta-decisions surfaced during the session (not in the original tier list):**

- [KB-spec] split convention for KB-impacting specs (`docs/specs/kb/`).
- **Planning write-back cadence** — write-back rule (LLM Wiki synthesis) extends to Maestro/Dan + Claude planning sessions; refine core files at the close of every multi-question planning session.
- **Curation protocol for `repos/`, `context/`, `docs/`** — quarterly review, archive pathway, curation log for what's removed and when.
- **uv-via-conda layered architecture** — linus conda env (production) + uv disposable envs (experimental) as a hard rule.

---

## Tier 0 — Immediate actions (Phase 0 / security hygiene, do not wait)

> **TIER 0 — ALL RESOLVED (2026-05-03).** See [Resolution Log](#resolution-log-2026-05-03)
> for one-line resolutions and [planning-update-spec.md](../specs/planning-update-spec.md)
> for execution detail.

These are not architectural questions — they are concrete, reversible actions with negligible
downside that should happen before Phase 1 starts. They don't require answers; they require
execution.

### 0. Remove pre-emptive ML framework dependencies from environment.yml

`langchain`, `langgraph`, and `haystack-ai` are currently installed in the linus conda
environment for "Phase 3+ evaluation" but serve no current function. Their transitive
dependency trees are enormous, their release cadence is fast, and the core value they provide
(agent state machines, tool orchestration, document pipelines) is exactly what Linus is building
as its core competency. `langchain` alone was a litellm-style supply chain attack target in 2024.
Removing them costs nothing; re-adding them at Phase 3 takes one line.

Additionally, `haystack-ai` is a KnowledgeBase-layer dependency and should live in
KnowledgeBase's own environment, not Linus's.

**Action**: Remove `langchain`, `langgraph`, and `haystack-ai` from `environment.yml`. Rebuild
the env. Add a lock file (`pip-compile --generate-hashes`) to pin all dependencies with hash
verification. Document the dependency philosophy in CLAUDE.md.

**Source**: `docs/security-synthesis.md` dependency surface analysis.

---

### 1. Write and commit an incident response protocol to SAFETY.md

The litellm supply chain incident was discovered accidentally via a RAM crash. A more subtle
attack would not announce itself. Having a written protocol before an incident occurs makes it
far more likely to be executed correctly under stress.

The protocol should cover: (1) trigger — what constitutes a confirmed or suspected supply
chain compromise; (2) containment — env teardown, session log audit, what the compromised
package had access to; (3) credential rotation scope — which credentials need rotating and in
what order; (4) attestation — how to verify the rebuilt env is clean before resuming work.

**Action**: Draft and commit a "Supply Chain Incident Response" section to SAFETY.md before
Phase 2 expands the network-egress surface. One session of work; no architecture decision
required.

**Source**: `docs/syntheses/security-synthesis.md` Q5; `docs/landscapes/synthesis-landscape.md`
cross-cutting open questions; `docs/questions/open-questions.md` Part 3 / Security Q5.

---

## Tier 1 — Decisions that block Phase 1 / Phase 2

> **TIER 1 — ALL RESOLVED (2026-05-03).** See [Resolution Log](#resolution-log-2026-05-03)
> and [planning-update-spec.md](../specs/planning-update-spec.md).

These determine what gets built first, and several other questions resolve
automatically once they are answered.

### 1. Is the first concrete Phase 1 spike "BitNet 2B4T + bitnet.cpp on M1 Max, benchmark vs. Ollama Qwen2.5/Llama-3.2"?

**Why it leads.** This single experiment answers the BitNet quality-cost
question, the bitnet.cpp-on-Apple-Silicon throughput question, and the
"is a 1-bit Worker viable today" question simultaneously. Estimated 1–2
hours of work; the Phase 1c benchmark sweep can be built around it.

**Source notes:** BitNet 2B4T, bitnet.cpp, BitNet Distillation, Bonsai-demo,
and the cross-cutting paper-landscape questions.

### 2. Inference backend: pmetal vs. Ollama+mlx-lm-ft, decided by Phase 1b evaluation

**Why it leads.** pmetal subsumes ANE work, supplies the Phase 6 training
backbone, supplies a 45-tool MCP server, and stands up the OpenAI-compatible
endpoint. If it passes, ~6 other open questions resolve automatically. If it
fails, the fallback (Ollama + mlx-lm-ft + Bonsai's llama-server) is well-
understood.

**Sub-decisions inside this:**
- Build `--features serve` only for Phase 1b, or the full default with all 15
  features enabled?
- Concurrency target: 5-concurrent throughput, or single-request tok/s +
  RSS sufficient?
- Single-maintainer dependency risk: pin a commit and accept staleness, or
  commit to a migration plan if pmetal goes dormant?

**Source notes:** pmetal (Q1, Q2, Q4), repo-landscape "Inference: The Pivotal
Decision."

### 3. Phase 6 fine-tuning path: native-1-bit (Bonsai/2B4T) vs. BitDistill (FP16 → 1.58-bit) vs. FP16-LoRA fallback

**Why it leads.** Three different philosophies, three different infrastructure
investments. BitDistill needs ~10B tokens of continued pre-training; native
1-bit needs an MLX-native ternary training path; FP16-LoRA is the safe fallback
already covered by pmetal-trainer or mlx-lm-ft. Picking the lane shapes Phase 6
entirely.

**Source notes:** Bonsai-demo (Q3), BitNet b1.58 (Q2), BitNet v2 (Q3),
BitNet Distillation (Q2 and Q3), 2B4T (Q2), repo-landscape "Key Tensions."

### 4. KnowledgeBase data model: RDF vs. property graph

**Why it leads.** Hardens early in Phase 2; "convert later" is painful.
Determines whether KB plugs into the Semantic Web stack (rdflib, SPARQL,
SHACL) or into a graph database (Neo4j, Cypher). Shapes every subsequent
KB design choice (schema, identity, context, querying, deductive layer).

**Source notes:** Knowledge Graphs survey (Q1), and an implicit prerequisite
for any of the embedding/retrieval Phase 2 questions.

### 5. Harness plurality: converge to one front-end, or run all four indefinitely?

**Why it leads.** Determines how much engineering goes into per-harness
polish, MCP integration, and skill symlink strategy. The current set (Claude
Code as Maestro + cline + claw-code-local + openclaw) is four; the "one wins"
answer is empirical, but the *intent* shapes Phase 5 budget.

**Source notes:** cline (Q1), claw-code (Q1), claw-code-local (Q1), openclaw
(Q1), repo-landscape "Harnesses."

### 6. KB ingest quality gate: what are the right domain criteria for Dan's scientific fields?

**Why it leads.** The LLM wiki synthesis establishes that filtering noise at the door beats
any retrieval improvement downstream, and the gate should be an auditable YAML domain editorial
policy. But the right criteria for Dan's specific domains (genomics, computational biology,
environmental science) have not been specified. This decision shapes the Phase 2 KB schema
before the first paper is formally ingested — getting it wrong means the KB accumulates
low-quality content that corrupts retrieval and, eventually, the Phase 6 fine-tuning corpus.

**Sub-decisions inside this:**
- What field-specific signals should the gate encode? Candidates: journal tier, methodology
  rigor, peer review status, data availability, reproducibility markers.
- Binary (accept/reject) or scored (score + threshold + manual review lane)?
- Where do preprints (arXiv, bioRxiv) land? Dan's domains move fast; blanket rejection loses
  signal, but blanket acceptance opens the noise floor.
- Should FineWeb's "compare known-good vs. known-bad statistics" methodology be adapted as a
  template for this gate?

**Source notes**: `docs/syntheses/llm-wiki-synthesis.md` quality gate section;
`docs/landscapes/synthesis-landscape.md` cross-cutting open questions; FineWeb (Q2);
`docs/questions/open-questions.md` Part 2 / FineWeb Q2; Part 3 / LLM Wiki Q5.

---

## Tier 2 — Decisions that shape Phase 2–6 architecture

> **TIER 2 — ALL RESOLVED (2026-05-03).** See [Resolution Log](#resolution-log-2026-05-03)
> and [planning-update-spec.md](../specs/planning-update-spec.md).

These don't block Phase 1, but the answers steer the next several phases.

### 6. MCP as the extensibility substrate?

cline, openclaw, and pmetal all speak MCP. Adopting it as Linus's tool-
registration surface in Phase 3 means tools surface in all harnesses without
glue. The cost is MCP's protocol complexity. Decide explicitly at the start
of Phase 3 rather than inheriting by accident. *(cline Q2; pmetal Q3.)*

### 7. KB embedding pipeline: idf + first+last + quantile-u recipe vs. modern encoder (BGE/E5) baseline?

The Stankevičius paper claims a >10-point STS improvement from aggregation +
post-processing tricks alone, on BERT-base. Worth a small `experiments/
kb-embedding-ablation.md` ablation against modern encoders to confirm before
the recipe hardens into the KB pipeline. Pairs with the PCA-reduction question
(Curse of Dimensionality Q2) and the distance-discrimination health metric
(Curse of Dimensionality Q1) — small-effort, large-payoff implementations.
*(Sentence Embeddings Q1+Q3; Curse of Dimensionality Q1+Q2.)*

### 8. KV-cache compression as a near-term Linus feature?

Two papers (BitNet a4.8, BitNet v2) report 3-bit / 4-bit KV cache with
near-zero accuracy loss. mlx-flash also provides a hybrid FP16-recent +
8-bit-older offloaded KV pattern. Long-context KB queries are a near-term
Linus pain point that compresses KV is the cheapest path to fix. Phase 2a
minimum feature set, or defer until a concrete long-context use case
surfaces? *(BitNet v2 Q1; BitNet a4.8 Q2; mlx-flash Q4.)*

### 9. ANE in Phase 1b, or defer entirely?

The ANE existence proof + pmetal's ANE crate together suggest "ANE prefill +
GPU decode" should be an explicit benchmark configuration alongside Ollama
vs. pmetal-GPU. The counter-argument is bitnet.cpp's CPU-only path being
already fast enough that ANE may be a detour. Decide whether ANE earns Phase
1–2 attention or stays Phase 7+. *(ANE Q1+Q3; BitNet Q4; bitnet.cpp Q2.)*

### 10. mlx-flash vs. flash-moe philosophy when forced to choose

Same problem (>RAM inference), opposite tradeoff. mlx-flash is framework-
integrated + zero quality loss; flash-moe is bespoke + aggressively quantized
+ manual Metal/Obj-C. Linus likely never integrates flash-moe code (Obj-C
skill ramp), so the practical question is whether to commit to mlx-flash as
the Linus >RAM path in Phase 5+. *(mlx-flash Q1; flash-moe Q1+Q4;
LLM-in-a-Flash Q3.)*

### 11. Streaming + 1-bit composite path

Bonsai-Ternary-30B + mlx-flash is combinatorially more memory-efficient
than either alone. Phase 6d experiment target, or wait for PrismML to train
a large ternary Bonsai? Closely related: "BitNet × Flash-MoE × JPmHC" as a
Phase 8 synthesis target. *(mlx-flash Q3; Flash-MoE Q3; JPmHC Q1; cross-
cutting paper-landscape Q3.)*

### 12. The flash-moe target on M1 Max 32 GB

flash-moe ran 397B on 48 GB M3 Max. The comfortable M1 Max ceiling is
probably ~100–150B MoE or 30–50B dense-1-bit. Want a concrete Phase 6d
target ("get model X running at N tok/s on Dan's hardware") sketched once
Phase 1b closes? *(flash-moe Q1; Flash-MoE paper Q1.)*

### 13. Does Linus need a custom orchestration layer, or will Task Master AI + Cline cover Phase 2?

Task Master AI (PRD → structured tasks → sequential Claude execution) and claude-squad (parallel
terminal agents) together might satisfy Phase 2's orchestration requirements without Linus building
a custom router. The Algorithm says delete before building. The counter-argument is that
KnowledgeBase integration, sandbox policy, and Apple Silicon optimization require enough
custom orchestration primitives that the custom layer is the work, not overhead. This question
should be answered by explicit comparison, not assumption.

**Source**: `docs/skills-and-practices-synthesis.md` Q2; cross-cutting entrepreneurial material.

### 14. Should Dan start monetizing AI capabilities now, before Linus infrastructure is ready?

Scientific literature intelligence as a retainer service — Dan's PhD + genomics domain expertise +
hosted Claude — is buildable today with no Linus infrastructure, and could generate $1,000–$3,000/
month per client. Starting even one engagement would generate real feedback about what clients pay
for, which is more valuable than further planning. The tradeoff: time taken from Linus
infrastructure work. The counter-argument: Linus's value is to enable this kind of work at scale,
so building the infrastructure first makes each engagement cheaper. Which path yields better
information faster?

**Source**: `docs/skills-and-practices-synthesis.md` Q1; entrepreneurial opportunity analysis.

### 15. Phase 5c: deferred or done?

claw-code-local plus the Phase 2a Linus endpoint already solves the terminal
agent surface. The roadmap's 5c fallback ("a small custom terminal agent
~500 lines of Python") may be dead on arrival. Mark Phase 5c as "adopt
claw-code-local," or keep the custom-agent option open? *(claw-code-local
Q1; claw-code Q1.)*

### 16. Parallel Worker KB write coordination

**Why it belongs in Tier 2.** The write-back rule — every Worker task ends with KB update
proposals — is straightforward for a single Worker. For Phase 3's multi-agent fan-out,
multiple Workers may simultaneously propose updates to the same KB pages. Git-branch-per-ingest
and last-write-wins are partial answers, but neither handles the general case: git branches
require a merge strategy; last-write-wins silently discards concurrent updates.

The right coordination mechanism should be designed into the Phase 3 KB architecture spec
*before* the first multi-agent session is spawned. The cost of designing it in Phase 2 is low;
retrofitting it after the first conflicting write is high.

**Sub-decisions**: serialized KB writes even during parallel fan-out (simplest, no
coordination needed) vs. merge-on-human-review vs. automated reconciliation; whether
contradiction detection runs at write time or read time.

*(LLM wiki synthesis Q1; `docs/questions/open-questions.md` Part 3 / LLM Wiki Q1;
`docs/landscapes/synthesis-landscape.md` cross-cutting open questions.)*

---

## Tier 3 — Decisions that affect documentation, conventions, and longer-horizon scope

> **TIER 3 — ALL RESOLVED (2026-05-03).** See [Resolution Log](#resolution-log-2026-05-03)
> and [planning-update-spec.md](../specs/planning-update-spec.md).

These are meaningful but don't block any concrete next action. Resolve them
in batches when there is time.

### 19. Benchmark architecture: tok/s vs. task-completion time

The [Speed and LLMs paper](paper-notes/2502.16721v1.md) shows that task-completion rankings
frequently invert tok/s rankings — the canonical Worker selection metric is systematically
misleading. `benchmarks/dan_tasks/` should be structured around a three-task schema (minimal
output, fixed-length, open-ended) with wall-clock completion time as the primary axis from
Phase 1. This is not a hard decision — it is a design choice that is cheap to get right now
and expensive to retrofit later. *(2502.16721v1 Q1; Q2.)*

### 20. KB ingestion keyphrase strategy: RaKUn 2.0 as the Phase 2 baseline?

RaKUn 2.0 is CPU-only, pure Python, 2 orders of magnitude faster than alternatives with
statistically indistinguishable F1, and demonstrated on biomedical corpora the size of
Dan's domain. It is the natural Phase 2 keyphrase extraction baseline. The question is
whether to adopt it immediately or benchmark it against author-supplied paper keywords
first. KGRank is the Phase 3 upgrade path for ontology-enriched KB node labels.
*(2208.07262v1 Q1-3; s41019-017-0055-z Q1.)*

### 21. Security posture decisions: lock files, dependency philosophy, incident protocol

Three concrete decisions that don't require architecture work but require Dan's values-level input:
(1) How much supply chain friction is acceptable — full hash pinning, monthly audit, or phase-
milestone pinning? (2) Should untrusted experimental packages always run in disposable `uv` envs?
(3) What is the response protocol if `pip-audit` finds a CVE in the installed env? Having written
answers to all three now, before an incident, is the right time to do it.
*(security-synthesis.md Q1, Q2, Q5.)*

### 22. Output interface design: optimize for the 10 bits/s human review channel?

Parallel Worker fan-out generates zero throughput gain for Dan unless the Maestro interface
compresses outputs to the essential bits before presenting them. The [Zheng-Meister paper](paper-notes/PIIS0896627324008080.md) gives this a quantitative foundation: the bottleneck is ~10 bits/s
human review, not model latency. The design implication for Phase 2 is that Linus's chat/summary
interface should default to high-information-density concise outputs, with verbose modes opt-in.
*(PIIS0896627324008080 Q4; nihms-2096004 Q4.)*

### 23. Which community repos to clone into repos/ as Phase 2-3 references?

The LLM wiki synthesis identified 8 high-value repos not already in `repos/` — all local-first,
Apple Silicon compatible, no CUDA required. Top candidates: `omega-memory` (hybrid
FTS5+vector+cross-encoder, 95.4% at 50ms), `keppi` (graph traversal on real 1.4K-note KG),
`rohitg00/agentmemory` (43 MCP tools, BM25+vector+KG), `openaugi` (simplest graph-backed memory
with write-back). The skills synthesis also flagged `fastmcp`, `Task Master AI`, and `claude-squad`.
Cloning all ~12 adds study material without operational risk. *(llm-wiki-synthesis.md S8;
skills-and-practices-synthesis.md S4.)*

### 14. Documentation cadence and synthesis docs

Several questions ask "worth a synthesis note?" The candidates:
- `docs/specs/kb-architecture.md` — KB design rationale section by section
  against the Hogan KG survey
- `docs/experimental-protocol.md` — Linus-house style guide for benchmarks
  (lifting Stankevičius + FineWeb methodology)
- `synthesis-bitnet-on-apple-silicon.md` — pull the four BitNet papers +
  Bonsai + pmetal into one "actual inference path" writeup
- `docs/maestro-worker-flash-moe-case-study.md` — analyze the flash-moe
  collaboration dynamics as a Maestro/Worker existence proof

Decide which (if any) earn the writing time, and at what phase.

### 15. Phase 4 scope ambition: how much beyond Kiwix + PMTiles + Qdrant?

Kolibri (education), FlatNotes (notes), CyberChef (data tooling), specific
Wikipedia ZIM subsets, PMTiles regions (Oregon/PNW + fieldwork sites?),
Qdrant-in-Docker vs. native vector store, English-only assumption for
FineWeb-Edu vs. multilingual support. *(project-nomad all questions; FineWeb
Q3.)*

### 16. Linus practice and stance questions

- "Trust the OS page cache" as an explicit CLAUDE.md engineering convention?
- Reverse-engineering Apple's private APIs as a Linus practice, or strictly
  public APIs (CoreML/MLX/Metal)?
- Rust as a co-language: stated "one orchestration language" policy or
  comfortable with Rust components alongside Python?
- Sovereignty statement (NOMAD's phrasing) lifted into VISION.md?
- Reproducibility + interpretability over fancy stochastic methods as a
  stated design principle?
- Obj-C/Metal-direct as a Phase 7+ skill bet or ruled out?

### 17. Methodology and tooling

- autoresearch's `program.md` promoted to `SKILL.md`?
- Per-experiment budget: short loops on proxy metrics, or 30+ minutes on
  Dan task suite?
- First real use of autoresearch methodology — Phase 1b pmetal LoRA trial
  or Phase 6d fine-tuning sweep?
- cline's prompt-variant pattern (`xs`/`hermes`/`glm`) for Linus's per-
  worker-class tool-use templates — Phase 7 plan or defer?

### 18. Smaller open items

- Voice wake as a Phase 5 requirement or Phase 8?
- Canvas as a KnowledgeBase visualization surface?
- Skill symlink strategy (Linus → openclaw, copy / symlink / openclaw-
  primary)?
- Browser-based agentic work — Linus use case or Maestro-only?
- ACP/Zed as a future surface?
- BitNet weight visualization via the Horiike PCA-projection method —
  curiosity experiment or skip?
- pmetal-mhc as a Phase 6 training experiment vs. curiosity?
- BitNet 2B4T HumanEval+ underperformance: code-specialized BitNet as a
  Phase 6 deliverable?
- DPO step in Phase 6 fine-tuning, or stop at SFT?
- PrismML's llama.cpp/MLX forks as upstream-tracking dependencies?
- 4-bit KV cache vs. 4-bit weights, which first?
- JPmHC TRM reproducibility spike on M1 Max — worth 1–2 days?
- Read-or-defer on the Maderix ANE substack series and the Karpathy
  autoresearch tweets?

---

## How to use this document

**Tier 0** items are concrete immediate actions — no discussion needed, just execute. Two
currently: (0) remove pre-emptive ML dependencies and add a hash-pinned lock file; (1) write
and commit an incident response protocol to SAFETY.md. Both should be done before Phase 1 starts.

Walk Tier 1 as a focused conversation, with Tier 2 as the natural follow-up. Tier 3 is a
reservoir to dip into when context suggests one of those threads matters now (e.g., Phase 4
starts → revisit Tier 3 #15).

Each Tier 1 answer typically resolves 2–3 downstream questions automatically, so progress will
compound. As decisions are made, mark them resolved here and propagate the resulting changes
into [total-landscape.md](total-landscape.md), ROADMAP.md, DECISIONS.md (an ADR per Tier 1
decision is appropriate), and the relevant per-note `Open questions for Dan` sections.

[total-landscape.md](total-landscape.md) is the map — it now integrates repos, papers, and
all three practitioner syntheses into a single cross-cutting view. [open-questions.md](open-questions.md)
is the full archive; it now includes a Part 3 sourced from the synthesis documents. Questions in
`top-questions.md` are a prioritized distillation of that archive.
