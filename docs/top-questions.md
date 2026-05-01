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

## Tier 1 — Decisions that block Phase 1 / Phase 2

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

---

## Tier 2 — Decisions that shape Phase 2–6 architecture

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

### 13. Phase 5c: deferred or done?

claw-code-local plus the Phase 2a Linus endpoint already solves the terminal
agent surface. The roadmap's 5c fallback ("a small custom terminal agent
~500 lines of Python") may be dead on arrival. Mark Phase 5c as "adopt
claw-code-local," or keep the custom-agent option open? *(claw-code-local
Q1; claw-code Q1.)*

---

## Tier 3 — Decisions that affect documentation, conventions, and longer-horizon scope

These are meaningful but don't block any concrete next action. Resolve them
in batches when there is time.

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

The plan is to walk Tier 1 first as a focused conversation, with Tier 2 as
the natural follow-up. Tier 3 is a reservoir to dip into when context
suggests one of those threads matters now (e.g., Phase 4 starts → revisit
Tier 3 #15).

Each Tier 1 answer typically resolves 2–3 downstream questions automatically,
so progress will compound. As decisions are made, mark them resolved here
and propagate the resulting changes into [total-landscape.md](total-landscape.md),
ROADMAP.md, DECISIONS.md (an ADR per Tier 1 decision is appropriate), and
the relevant per-note `Open questions for Dan` sections.
