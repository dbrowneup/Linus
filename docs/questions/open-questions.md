# Open Questions for Dan

All questions aggregated from `docs/repo-notes/` and `docs/paper-notes/`. Each section names the source note and carries
the questions unchanged. Work through these in one pass or use them as a reading agenda alongside the individual notes.

For a smaller, prioritized subset focused on the most consequential decisions, see [top-questions.md](top-questions.md).

---

## Resolution Log (2026-05-03)

All questions in this archive that surfaced into [top-questions.md](top-questions.md) Tier 0 / 1 / 2 / 3 have been
**resolved** as of 2026-05-03 in a Maestro/Dan planning session. Per-question resolution one-liners with full
traceability live in [top-questions.md](top-questions.md) under its Resolution Log. Detailed implementation of the
resulting changes is captured in [../specs/planning-update-spec.md](../specs/planning-update-spec.md), which is the
actionable spec executed by Workers in subsequent sessions.

Questions in this archive that did **not** propagate to top-questions.md remain unresolved here and may surface in
future planning sessions; they are deliberately not on the current critical path.

---

# Part 1 — From `docs/repo-notes/`

## pmetal

1. **Scope of Phase 1b.** The roadmap calls for a 5-concurrent throughput test; is that the right concurrency target, or
   would single-request tok/s + memory-footprint be enough to make the adopt/defer call?

2. **Feature-flag strategy.** Default pmetal build includes ANE + MLX + serve + Trainer
   - data + distill — about 15 active features on the critical path. Do we build the full default for Phase 1b and let
     compile times hurt, or strip to `--features serve` for the first pass and layer training in when Phase 6
     approaches?

3. **pmetal-mcp as Linus's tool registry path.** pmetal already ships 45 tools via MCP. Is that a serious candidate for
   the Phase 2a tool registry (Linus wraps pmetal-mcp + adds KnowledgeBase tools), or should Linus own tool definitions
   entirely and pmetal-mcp is study material?

4. **Dependency risk.** pmetal is one developer's project. It's impressive and signed, but single-maintainer risk is
   real. If adopted deeply, what's the fallback plan — pin a commit and accept no updates, or maintain readiness to
   migrate to mlx-lm + Ollama if pmetal goes stale?

5. **Manifold-Constrained Hyper-Connections (`pmetal-mhc`).** This maps directly onto the JPmHC paper (`2602.18308`) in
   the context folder. Are you interested in running mhc as a Phase 6 training experiment, or does it stay a curiosity?

---

## mlx-flash

1. **mlx-flash vs. flash-moe philosophically.** Same problem, different tradeoff: mlx-flash is framework-integrated +
   zero quality loss + predictive scheduling; flash-moe is bespoke + aggressively quantized + manual pipeline. Which
   style should Linus prefer when forced to choose?

2. **The native-precision claim on M1 Max.** Nemotron-30B on a 16 GB Air at bit-perfect parity is the README headline;
   the unstated question is _tok/s_. Worth a small benchmark to see what native-precision streaming costs on your
   hardware before committing to it as a serving path.

3. **Streaming + 1-bit as a composite path.** Running a 1.58-bit 30B (hypothetical Ternary-Bonsai-30B) with mlx-flash
   streaming is combinatorially more memory-efficient than either alone. Is this a Phase 6d experiment target, or does
   it wait until PrismML trains a large ternary Bonsai?

4. **Hybrid KV cache as a Linus feature.** The 128-token FP16 + older-8-bit disk-offloaded KV cache pattern is useful
   even without weight streaming. Should it be part of Phase 2a's minimum feature set, or deferred until a concrete
   long-context use case surfaces?

---

## flash-moe

1. **The 32 GB flash-moe analogue.** flash-moe ran ~400B on 48 GB. On the M1 Max 32 GB with a slower SSD, the
   comfortable ceiling is probably a ~100–150B MoE or a 30–50B dense-1-bit model. Want me to sketch a concrete Phase 6d
   target ("get MODEL X running at N tok/s on Dan's hardware") once Phase 1b closes?

2. **"Trust the OS" as a Linus design principle.** The flash-moe finding that every custom cache lost to the OS page
   cache is a strong generalizable principle. Explicitly promote it to a Linus engineering convention in CLAUDE.md, or
   keep it implicit?

3. **Autoresearch + flash-moe methodology fusion.** Phase 7c's overnight iteration loop is essentially the flash-moe
   experiment log run as a supervised AI loop against a tok/s target. Is this the first concrete use case for the Phase
   3b parallel-agent infrastructure, or does it stay a later-phase thing?

4. **Objective-C / Metal-direct as an escape hatch.** If Linus ever needs flash-moe-level control — say, to beat pmetal
   on a specific workload — we'd be writing Obj-C and Metal by hand. That's a skill Dan doesn't currently have. Is
   acquiring it a Phase 7+ bet, or ruled out in favor of "whatever pmetal supports"?

---

## ANE

1. **Does the ANE existence proof change Phase 1b?** The pmetal evaluation plan currently treats ANE serving as a
   nice-to-have. Given pmetal ships with an ANE pipeline and this repo shows training is viable, should "ANE prefill +
   GPU decode" become an explicit benchmark configuration alongside plain Ollama vs. pmetal-GPU?

2. **Read-or-defer on the Maderix substack series.** The three articles are arguably the best documentation of the ANE
   that exists. Worth reading now, or defer to whenever an ANE decision is actually forced?

3. **Private-API risk appetite for Linus.** pmetal uses some of the same `_ANEClient` surface. That's a fine bet for a
   personal project but means macOS updates can break things. Happy to document that risk in DECISIONS.md when Phase 2's
   inference backend is chosen, or would you prefer a policy of "ANE-only if officially supported API exists"?

4. **Reverse-engineering as a Linus practice.** This repo demonstrates the value of treating Apple's private APIs as
   fair game for research. Is that a stance you want Linus to inherit, or keep Linus strictly on public APIs (CoreML,
   MLX, Metal) and let pmetal carry any private-API risk?

---

## Bonsai-demo

1. **Bonsai-8B and Ternary-Bonsai-8B in the Phase 1c baseline sweep?** This is the cheapest test of the 1-bit
   quality-cost frontier on your hardware. Happy to write a smoke-test spec for it.

2. **PrismML's `llama-server` as the interim OpenAI-compatible endpoint for the Phase 1e Maestro/Worker loop?** It ships
   today and routes to the Metal backend, buying time before `pmetal serve` is evaluated. The alternative is staying on
   Ollama and accepting that Ollama does not yet have `Q1_0` Metal kernels.

3. **Native-1-bit vs. distilled-to-1-bit (BitDistill) as Linus's fine-tuning path.** Bonsai trained from scratch with
   1-bit / ternary weights. BitDistill takes an FP16 model and distills down. Different risks. Do you want to run both
   experiments in parallel at Phase 6, or pick a lane?

4. **PrismML's llama.cpp and MLX forks as upstream-tracking dependencies.** They've committed to upstreaming; do we
   track their forks as study references and adopt the upstreamed kernels once merged, or pin a specific fork commit as
   a Linus dependency?

---

## BitNet

1. **How aggressively do we want to chase 1.58-bit on Apple Silicon as a first-class path?** Bitnet.cpp's ~7 tok/s at
   100B on M2 Ultra implies a ~40–50B ternary model could be feasible on the M1 Max. Is that compelling enough to put an
   "MLX/Metal ternary runtime" experiment earlier in the roadmap (Phase 2–3 experimental branch) rather than waiting for
   Phase 6+?

2. **BitNet Distillation as a fine-tuning path.** Would you accept a 1.58-bit distilled Qwen2.5 variant as the Phase 6
   deliverable if it beats a FP16-LoRA'd counterpart on Dan task suite, given it sacrifices some smoothness in exchange
   for much larger effective capacity?

3. **Ternary base models vs. converted models.** Native ternary training (BitNet b1.58 2B4T) vs. post-hoc distillation
   (BitDistill) vs. post-hoc quantization (run FP16 Qwen at 2-bit via bitnet.cpp-style kernels) — three different
   philosophies. Any strong prior?

4. **Hardware bet.** The BitNet papers repeatedly call for "new hardware designed for 1-bit LLMs." The ANE is closer to
   that than Metal is. Is investing in ANE kernel development (via pmetal or directly) worth Linus dev time in Phase
   2–3, or does it stay a Phase 7+ project?

---

## cline

1. **Harness plurality.** You'll plausibly run Claude Code (Maestro), Cline (VS Code worker tasks), claw-code-local
   (terminal tasks), and openclaw (chat/voice) — all pointing at Linus. That's four front-ends. Is that the intended
   end-state, or is there a desire to converge on fewer once one proves out?

2. **MCP as the extensibility substrate.** Cline, openclaw, and pmetal all speak MCP. Adopting MCP as the
   tool-registration surface inside Linus is a plausible Phase 3 move — it means tools registered once are visible in
   all harnesses without custom glue. Architecturally cleaner, but carries MCP's complexity. Want to revisit this
   decision explicitly in Phase 3?

3. **Variant prompts for small / 1-bit models.** Cline's `xs` variant exists because tiny models need substantially
   different prompts. When Linus's Phase 6 produces a fine-tuned 1-bit model, it will likely need its own variant too.
   Plan for this in Phase 7 skills design, or defer?

4. **Browser use.** Cline's browser tool relies on Anthropic's Computer Use — a frontier-model capability. Local models
   plausibly can't drive it reliably. Is browser-based agentic work a Linus use case, or does it stay Maestro-only?

---

## claw-code

1. **Is "Linus has its own CLI harness" a Phase 5 goal, or OK to stay on Claude Code + claw-code-local forever?**
   ROADMAP 5c mentions a ~500-line custom terminal agent as a fallback. The fork handles the local-model case today, so
   this may be a dead requirement.

2. **ACP/Zed as a Linus surface.** claw-code's ACP ambitions overlap with any future Linus-in-Zed idea. Not a
   2026-current path, but worth flagging if you care about the Zed ecosystem.

3. **Rust as a Linus language.** claw-code, claw-code-local, and pmetal are all Rust. If Linus stays Python-first for
   orchestration but has Rust-based components (pmetal bindings, future CLI), is that fine, or do you want a stated "one
   orchestration language" policy?

4. **Read `PHILOSOPHY.md` now or defer?** It's short; likely contains framing worth lifting into Linus's own docs if
   relevant. I can pull excerpts into VISION.md if useful.

---

## claw-code-local

1. **Phase 5c deferred-or-done?** claw-code-local essentially already solves the "Linus terminal surface" requirement.
   The roadmap's 5c fallback ("a small custom terminal agent (~500 lines of Python)") may be dead on arrival. Happy to
   mark Phase 5c as "adopt claw-code-local" in the roadmap if you agree.

2. **Skill parity.** The fork exposes Claude Code's `/skills` command, which means Anthropic-shaped `SKILL.md` files
   work inside it. That aligns with Linus's Phase 7 skills direction. Want a Phase 1e smoke-test that runs a trivial
   Linus-defined skill through claw-code-local against Ollama?

3. **Upstream drift.** claw-code-local is a thin fork. If upstream adds meaningful features (ACP/Zed mode, MCP
   refinement), should Linus maintain its own mini-patches on top, or wait for the fork to rebase? Informs the
   dependency-tracking pattern we adopt.

4. **Behavioral parity with local models.** The fork ships the patches but doesn't validate _which_ local models produce
   usable tool calls inside claw-code's templates. This is the kind of empirical question the Dan task suite is built
   for. Want the Phase 1d suite extended with a "tool-use-through-claw-code" axis?

---

## openclaw

1. **Which openclaw surfaces actually matter?** Full channel sprawl isn't the goal. A reasonable minimum is macOS menu
   bar + voice wake + Canvas + WebChat; iOS node if you want phone access. Am I reading your priorities right, or do you
   want any specific messenger channel wired up?

2. **Voice wake as a Phase 5 feature.** openclaw supports macOS/iOS voice wake and Android continuous voice. Is voice a
   Phase 5 requirement, or defer to Phase 8 native app? Voice changes the usability story substantially.

3. **Canvas as a KnowledgeBase surface.** openclaw's Canvas is an agent-driven visual workspace. Plausible Phase 5
   experiment: have Linus render paper clusters, cluster labels, or knowledge-graph subgraphs in Canvas. Is that the
   kind of interaction you want, or is text/Streamlit sufficient?

4. **Skill symlink strategy.** Keeping Linus skills in `src/linus/skills/` and symlinking into openclaw's workspace is
   one option; copying is another; putting skills only in openclaw and having Linus read from openclaw's workspace is a
   third. Preference?

5. **Private-API / local-model first-class support.** openclaw's model config assumes a subscription. Confirming it
   works cleanly against an OpenAI-compat local endpoint with no rate-limit drama is a Phase 5 smoke-test worth
   budgeting for.

---

## autoresearch

1. **First real use of autoresearch methodology.** Phase 6d or Phase 1b's pmetal evaluation? The pmetal LoRA trial is a
   natural first loop: Maestro (me, or you + me) writes the `program.md`, Worker iterates overnight, we wake up to a
   benchmark table. Low risk, exercises the whole Maestro/Worker protocol on real work.

2. **Metric for Linus's loops.** Karpathy uses val_bpb for its architecture-fairness. Linus's analogue is Dan task suite
   score, which is higher-variance and slower-per-evaluation. Are we willing to lengthen the per-experiment budget (30
   min+) to get the higher-signal metric, or keep short loops on proxy metrics?

3. **`program.md` as SKILL.md.** autoresearch's `program.md` is essentially a lightweight skill. Promoting it to the
   Anthropic `SKILL.md` convention makes it portable between Claude Code and Linus. Worth doing in Phase 7, or
   premature?

4. **Read the Karpathy tweets linked in the README.** Short. Likely contain framing worth surfacing in VISION.md if you
   want Linus to inherit some of the "research org as code" posture explicitly.

---

## project-nomad

1. **Phase 4 scope ambition.** Roadmap Phase 4 is deliberately bounded to Kiwix + PMTiles + Qdrant + dataset version
   tracking. NOMAD hints at more (Kolibri for education content, FlatNotes for notes, CyberChef for data tooling). Do
   any of those belong in Linus Phase 4, or is notes-taking/data-tooling a non-goal for a personal research assistant?

2. **Kiwix ZIM selection.** The practical question that NOMAD resolves by asking the user: which Wikipedia subset? Full
   English is ~100 GB; Simple English is ~1 GB; there are topical ZIMs (medical, Wikipedia-for-schools). Any preference
   for genomics / biochem / chemistry-focused ZIMs if they exist?

3. **PMTiles regions.** Offline maps are only useful for specific places. Oregon + PNW makes sense given context. Any
   other regions (fieldwork sites, travel) matter?

4. **Qdrant-in-Docker vs. native vector store.** NOMAD uses Qdrant because it's a general-purpose offering; Linus's
   KnowledgeBase currently uses numpy-based similarity search. Are we promising Qdrant in Phase 4 only if benchmarks
   force it, or do you want it regardless for a smoother long-term path?

5. **Explicit sovereignty statement in VISION.md.** NOMAD's phrasing ("Knowledge That Never Goes Offline," zero
   telemetry, no authentication by default because the network boundary is the trust boundary) is crisper than Linus
   currently articulates. Worth lifting into VISION.md?

---

# Part 2 — From `docs/paper-notes/`

## BitNet (original, 2310.11453v1)

1. Are you interested in the _training-side_ contribution here (STE, latent weights, large LR) for a hypothetical
   Linus-specific fine-tune, or only in the _inference-side_ artifact (a binarized matrix you can run cheaply)? That's a
   Phase 6 vs. Phase 2 split.

2. The paper's energy advantage relies on the matmul being almost-pure-addition. On the M1 Max specifically, do we have
   a ternary/binary matmul kernel for Metal/MLX, or is everyone still using `mlx.matmul` with FP16 weights? (This is a
   `repos/pmetal/` question.)

3. Worth a synthesis note tying BitNet → ANE → flash-moe into one inference story for Linus? I think so, but you should
   call it.

---

## BitNet b1.58 (2402.17764v1)

1. Is there a community-released 1.58-bit checkpoint at 3B+ in MLX format yet, or is Bonsai-demo (which is the original
   1-bit, not 1.58) the best we have on Apple Silicon today?

2. For Phase 6, do you imagine fine-tuning _on top of_ a pre-trained BitNet (cheap, possible on M1 Max), or LoRA-on-FP16
   then converting to BitNet (more standard, but throws away the BitNet training advantage)?

3. The paper's "design new hardware for 1-bit LLMs" pitch maps neatly onto Apple's ANE strategy. Worth a longer
   synthesis note connecting BitNet → ANE → pmetal → flash-moe as one coherent inference story?

---

## BitNet a4.8 (2411.04965v1)

1. Is the squared-ReLU GLU + sparsity trick worth pulling out as a standalone technique we apply to FP16 Workers,
   independent of BitNet? Could be a quick Phase 1 inference win.

2. The 3-bit KV cache result is the most striking number here. Same answer to BitNet v2's 4-bit KV — do you want to
   prioritize KV-cache compression as a near-term Linus inference experiment?

3. This paper is mostly subsumed by BitNet v2. Should the v2 note simply replace this, or is it useful to keep both for
   the historical record? My vote: keep both, mark this one clearly as superseded.

---

## BitNet v2 (2504.18415v2)

1. Is 4-bit KV cache more interesting to you than 4-bit weights _right now_? My read: long-context queries against the
   KnowledgeBase are a near-term Linus pain point, and a 4-bit KV cache trick may help even with FP16 weights.

2. Would you want a `paper-notes/synthesis-bitnet-on-apple-silicon.md` that pulls the four BitNet papers + Bonsai-demo +
   pmetal into one "what's the single best inference path on M1 Max in 2026" writeup? The four BitNet papers
   individually summarize fine; the _practical answer_ probably needs synthesis.

3. The "trained at low precision is fundamentally different from quantized after the fact" claim is the throughline of
   the BitNet line. Do you trust it enough to commit Linus to a BitNet-derived Worker model in Phase 6, or do you want
   to keep the FP16-LoRA option open as a fallback?

---

## BitNet b1.58 2B4T (2504.12285v2)

1. **Highest-leverage concrete action**: should I scope a Phase 1 spec for "Pull `bitnet-b1.58-2B-4T-gguf`, build
   bitnet.cpp on M1 Max, benchmark against ollama-served Qwen2.5-1.5B and Llama-3.2-1B on a few representative Dan tasks
   (Python refactor, paper-summarization, quick Q&A)"? My read: this is the single most informative Phase 1 experiment;
   ~half a day of work.

2. The HumanEval+ underperformance suggests **a code-specialized BitNet would be more useful for Linus than a
   general-purpose one**. Does the Phase 6 fine-tuning plan include a domain-specialization step on Dan's specific
   Python/Rust corpus?

3. The DPO recipe documented here is the closest thing to a "how to align a Linus- specific BitNet" recipe in the public
   literature. Worth deciding now whether Phase 6 fine-tuning includes a DPO step or stops at SFT.

---

## bitnet.cpp (2502.11880v1)

1. **Direct test path**: Want me to scope a Phase 1 benchmark that builds bitnet.cpp on the M1 Max, runs the official
   BitNet b1.58 3B checkpoint, and measures `tokens/s` against the FP16 LLaMA baseline? This is small, concrete, gives
   us actual M1 numbers, and would directly validate or kill BitNet as a Worker model. Probably 1–2 hours of work.

2. The CPU-only restriction means none of bitnet.cpp's gains touch the GPU or ANE. Is the synthesis "BitNet → ANE →
   pmetal" still the long-term Linus story, or does the CPU-only result here suggest the simpler path is "use M1 Max
   CPU + bitnet.cpp" and skip the ANE detour?

3. Bitnet.cpp ships from the same GitHub repo as the BitNet model code. Do you want me to verify the `repos/BitNet/`
   clone has the bitnet.cpp tree, or is that a "Phase 1 to-do" item?

---

## BitNet Distillation (2510.13998v1)

1. Does Microsoft's BitNet repo actually include BitDistill training code, or just inference? (The paper says yes; want
   me to check the repo and report back?)

2. If we adopted this as the Linus Phase 6 plan: which downstream task would be the first BitDistill target?
   Classification of incoming papers into KB topics is the natural Phase 0/1 candidate; KnowledgeBase summarization is
   the more ambitious Phase 3 candidate.

3. The paper trains on AMD MI300X; we run on M1 Max. Worth a benchmark spike to measure whether 10B tokens of continued
   pre-training is hours/days/weeks on our hardware before committing to BitDistill as the Phase 6 path?

---

## LLM in a Flash (2312.11514v3)

1. The paper's predictor training requires picking an architecture that has clean activation sparsity (ReLU). The BitNet
   2B4T model uses **squared-ReLU GLU** which _is_ sparse — does that mean the predictor approach is naturally
   compatible with our chosen Worker architecture? My best guess: yes, but worth checking the `repos/mlx-flash/` impl to
   see what models they support.

2. Sliding-window k=5 has a ~10–15% per-token incremental load. On M1 Max flash that's ~150 ms per layer-forward at 7B.
   Worth a back-of-envelope: what model size + window-k combination crosses the latency threshold of "feels
   interactive"?

3. This and `flash_moe.pdf` are the two papers most directly tied to existing Linus repos. Do you want a _single
   synthesis note_ that combines them with the `repos/mlx-flash/` and `repos/flash-moe/` repo notes, since they're
   really one inference story?

---

## Flash-MoE (flash_moe.md)

1. **Highest-impact concrete next step**: do you want me to scope a Phase 1 spike that runs the _existing_
   `repos/flash-moe/` code on the M1 Max with a smaller MoE checkpoint (Mixtral-8×7B or DeepSeek-V2-Lite) to validate
   the technique works on our hardware? This would directly test "can Linus host 80B-class MoE models" — a Phase 6/7
   question made concrete in Phase 1.

2. The paper is Claude-as-primary-author. That's an existence proof for the Maestro/ Worker model that Linus is built
   around. Worth a `docs/maestro-worker-flash-moe-case-study.md` companion writeup analyzing the collaboration dynamics?
   Or is that too meta?

3. Combining BitNet experts with Flash-MoE streaming would push the memory/quality frontier further. Realistic Phase 8
   direction, or premature?

---

## JPmHC (2602.18308v2)

1. **Is JPmHC interesting on its own merits, or as part of a larger BitNet+MoE+JPmHC story?** The most exciting
   Linus-aligned synthesis is "stability via Cayley + ternary weights via BitNet + expert streaming via Flash-MoE," none
   of which exists yet as a unified codebase. Worth flagging as a Phase 8 research direction in
   `docs/open-questions.md`?

2. **Phase 1 reproducibility spike**: would it be worth a 1–2 day exercise to try reproducing the JPmHC TRM result in
   MLX on M1 Max? It's ambitious — the paper used 8× B200 GPUs — but the model is tiny enough that the wallclock might
   be tolerable, and it would directly exercise our MLX training path.

3. The TRM-on-ARC-AGI methodology is very similar to what `repos/autoresearch/` and `repos/autoresearch-mlx/` are about
   — agentic research loops. Worth a synthesis note connecting JPmHC as a target architecture for those loops to _learn
   to design improvements upon_?

---

## FineWeb (2406.17557v2)

1. **Phase 6 path question**: if we adopt the BitDistill plan (10B tokens of continued pretraining + downstream
   fine-tune), should the 10B-token corpus be a slice of FineWeb-Edu, a slice of Dan's domain papers, or a mix? The
   Microsoft team used FALCON; FineWeb-Edu is the closest open analogue.

2. **KnowledgeBase ingestion**: would you want me to write a small `kb-quality-filter.md` spec applying FineWeb's
   "compare known-good vs known-bad statistics" methodology to your paper-ingest pipeline? The filtering math is
   paper-agnostic and may help with junk pages from web-scraped reference material.

3. **English-only assumption**: are any of your scientific reference materials in non-English languages (German for
   older biochemistry, French for some EnvSci sources)? If so, FineWeb is the wrong corpus and we should look at
   multilingual alternatives (CC-100, mC4).

---

## Knowledge Graphs survey (2003.02320v6)

1. **Choice of graph data model for KnowledgeBase**: RDF (Semantic Web stack, full ecosystem) or property graph (richer
   attributes, more performant for some workloads)? §2 lays out the tradeoffs. My read: RDF wins for a KB whose primary
   purpose is knowledge integration and SPARQL queryability; property graph wins if you imagine KB primarily as a graph
   database for analytics. Worth deciding _now_ before the schema design hardens, because converting later is painful.

2. **Schema-first vs schema-emergent**: Build a top-down ontology (using ontology-design patterns from §6.5) before
   ingesting content? Or ingest first, then mine the emergent schema (§3.1.3) and formalize? My recommendation:
   schema-first for the _spine_ (papers, authors, concepts, citations) using existing standards (BIBO, SKOS, FOAF),
   schema-emergent for the long tail.

3. **Entailment regime**: RDFS-only (sub-class, sub-property, domain, range) or OWL 2 RL (richer, but heavier)? §4.3
   makes the case; my read is RDFS-only is plenty for KB v1, with OWL 2 RL revisited if/when Phase 3 reasoning needs
   justify it.

4. **Worth a `docs/specs/kb-architecture.md`** that walks through this paper section by section and records the design
   choice + rationale for each? It would make the KB design decisions auditable and would pay back across the project
   lifetime.

---

## Sentence Embeddings (2408.08073v2)

1. **Concrete Phase 2 KB action**: do you want me to scope a `experiments/kb-embedding-ablation.md` spec that takes a
   sample of papers from your `context/papers/` folder, runs them through (a) raw last-layer-mean, (b) first+last +
   idf + quantile-u, (c) BERT+Avg., (d) a modern encoder like BGE-base — and measures cluster quality and retrieval
   relevance against a small set of hand-labeled "should-be-similar" pairs you provide? This would directly validate
   which embedding recipe to bake into the KB ingestion pipeline.

2. **Methodology generalization**: would it be worth a `docs/experimental-protocol.md` companion to ROADMAP.md,
   distilling this paper's ablation methodology + FineWeb's curation methodology into a Linus-house style guide for how
   benchmarks should be structured? My hunch: yes, and it would pay back across every Linus experiment going forward.

3. **Embedding-model selection**: BERT-base is the paper's test bed. What does Linus actually use today? My read of
   `CLAUDE.md` and the repos suggests Ollama-served models for generation, but I don't see a designated _embedding_
   model. Is that a Phase 2 decision still pending, and would you like a recommendation note pulling together the
   post-2024 embedding-model landscape (E5, BGE, Stella, Voyage, GIST) measured against the recipe in this paper?

---

## Curse of Dimensionality (2401.00422v3)

1. **Concrete next step**: should we add a "distance discrimination" health metric to the KB observability dashboard? It
   would be a simple periodic computation: sample 1,000 random points from the KB embedding store, compute pairwise
   distances, report `|D_max − D_min| / D_min`. If this ratio drops below some threshold (e.g., 0.3), retrieval quality
   has degraded into the concentration regime and we should investigate (re-train embeddings, dimension-reduce, etc.).
   I'd estimate ~30 lines of Python.

2. **PCA-reduce KB embeddings before indexing?** Theorem 4 strongly suggests there's a lower-dim representation that
   loses no signal, and the Stankevičius paper shows that post-processing helps. Worth a Phase 2 experiment: take
   BGE-base 768-dim embeddings, PCA-reduce to 256-dim, measure retrieval quality vs baseline. My prior: PCA-reduced
   embeddings will retrieve _as well or better_ than full-dim, with 3× less storage.

3. **Norm choice for retrieval**: Should the KB retrieval system use cosine (the default) or Minkowski with k < 2 (more
   robust to concentration)? This is more speculative and probably needs empirical validation on a Linus-relevant
   retrieval task before committing.

---

## Horiike Hypercube Projections

1. **Why is this paper in your `context/papers/` folder?** Is it for the geometry methodology (visualization tool), the
   biology applications (Ising-as-Boltzmann ↔ gene regulation), or because of the surface-level "hypercube" word overlap
   with JPmHC? Knowing your motivation would refocus the note.

2. **BitNet weight visualization**: would you find it useful if I drafted a small experiment spec —
   `experiments/bitnet-weight-hypercube.md` — that takes a small BitNet checkpoint, extracts the sign-pattern of one
   layer's weights, treats each input row as a hypercube vertex, and applies the PCA projection from this paper? It's
   curiosity-driven, not Phase 6 critical, but might give surprising structural insight into what 1-bit LLMs encode.

3. **Methodological methodology**: the paper's framing of "we want reproducible AND interpretable visualizations of
   high-dim binary data" maps onto a question we'll have downstream when Linus produces visualizations of agent state,
   KB structure, etc. Worth elevating as a Linus design principle (reproducibility + interpretability over fancy
   stochastic methods)?

---

## Speed and LLMs: Benchmarking Methodology (2502.16721v1)

1. **Benchmark design decision:** Should `benchmarks/dan_tasks/` be structured from the start around a three-task schema
   (minimal, fixed-length, open-ended) with wall-clock completion time as the primary metric, rather than being
   organized by topic or capability? Getting the measurement axis right now costs nothing and prevents the tok/s trap
   later.

2. **Worker selection experiment:** Would you like a smoke-test spec (50 items, three task types, wall-clock time
   measured) comparing whichever models you currently have pulled in Ollama as a Phase 1 deliverable? The paper's
   methodology is simple enough that a Worker could write the script from a spec.

3. **Router implications:** If Linus eventually dispatches different task types to different Workers (fast-terse vs.
   slow-expansive), does the orchestration layer need to classify tasks before dispatching, or is the distinction
   between "short-answer" and "open-ended" tasks something the caller always knows at dispatch time? The architecture
   answer changes how complex the router needs to be.

4. **Verbosity as a fine-tuning target:** Is calibrating output verbosity (terse for structured tasks, expansive for
   synthesis) a Phase 6 fine-tuning objective worth adding to the roadmap explicitly? This paper makes a strong case
   that verbosity is a first-class model behavior, not a side effect.

5. **Apple Silicon specifics:** The paper's A100 results are a motivation, not a number. Is there a community resource
   (MLX Discord, Hugging Face discussions) where M1/M2/M3 task-completion benchmarks are being collected, or is this a
   gap Linus could fill with a small public benchmark release?

---

## RaKUn 2.0 — Keyphrase Extraction (2208.07262v1)

1. **Should RaKUn 2.0 be the keyphrase extraction layer for the KnowledgeBase ingestion pipeline in Phase 2**, or does
   the KnowledgeBase already have a keyphrase extraction step? If so, what method does it use, and should we benchmark
   RaKUn 2.0 against it on a sample of Dan's paper corpus?

2. **What is the right merge threshold τ for biomedical/genomics papers?** The default of τ=1 favors multi-word phrases.
   Worth a smoke test on 20–50 papers from `context/papers/` at τ ∈ {0.5, 1.0, 1.5} with manual evaluation of top-5
   keyphrases?

3. **How does RaKUn 2.0's output compare to author-supplied keywords already embedded in paper PDFs?** A concrete
   benchmark: extract keyphrases from papers that have author keywords, compute overlap, and see whether RaKUn 2.0 adds
   novel signal or merely recovers existing metadata.

4. **Is there a parallelism opportunity in the KB ingestion pipeline?** At 40 seconds for 14M documents, throughput is
   not currently a bottleneck — but should the ingestion loop be structured for parallel batching from the start so the
   architecture doesn't need refactoring later?

5. **Should RaKUn 2.0 keyphrases feed directly into Qdrant as document metadata tags, or into the knowledge graph as
   node labels, or both?** Keyphrases-as-tags enables fast filter-based retrieval; keyphrases-as-graph-nodes enables
   multi-hop reasoning. The implementation sequence matters for Phase 2 and 3 design.

---

## KGRank — KG-Enriched Keyphrase Extraction (s41019-017-0055-z)

1. **Which controlled vocabulary — GO, MeSH, ChEBI, UniProt keywords — would serve as the most practical KGRank-style
   knowledge graph for Dan's biochemistry/genomics domain**, and how would h-hop path extraction behave on GO's DAG
   structure versus DBpedia's general graph?

2. **Does the noun-only heuristic hold for scientific text?** The paper excludes adjectives citing low annotator
   agreement, but in scientific writing adjectives frequently carry domain meaning ("oxidative stress," "transcriptional
   regulation"). Does excluding adjectives discard too much signal in Dan's corpus?

3. **Would section-level entity-linking disambiguation outperform whole-document matching for long scientific papers?**
   Matching DBpedia/ontology abstracts against the methods section independently could better capture domain-specific
   term meanings.

4. **For Linus's RAG use case, keyphrases should maximize retrieval recall for queries Dan is likely to ask**, not just
   topic coverage. Is there a way to incorporate Dan's past query patterns as a supervision signal for the PPR jump
   probabilities?

5. **Would spaCy's `en_core_sci_lg` (scispaCy) be sufficient for accurate entity boundary detection in genomics
   papers**, or would a domain-specific fine-tune be needed as a drop-in CoreNLP replacement?

---

## The Unbearable Slowness of Being — Cognitive Throughput (PIIS0896627324008080)

1. **Does the authors' estimate of ~270 bits/s per cone photoreceptor hold under the biophysics of phototransduction?**
   Is the sifting happening primarily in the retina (already 10× compression to optic nerve) or between the optic nerve
   and behavior (the remaining 10⁷)?

2. **Could the KnowledgeBase be curated to assemble the evidence for or against the hypercolumn model of prefrontal
   cortex?** Which naturalistic behavioral neuroscience experiments could distinguish it from the low-dimensional
   manifold model?

3. **The paper implies that a well-curated KnowledgeBase containing Dan's papers, notes, and corpora could represent a
   meaningful fraction of the ~5 GB a person acquires in a lifetime.** Does this change how you think about the scope
   and completeness goals for the KnowledgeBase?

4. **Linus-as-cognitive-augmentation should focus on reducing the cost of accessing structured information** (faster
   retrieval, better summarization) rather than increasing raw data transfer rates — the bottleneck is the 10 bits/s
   channel, not the model latency. Does that framing match your intuition about where friction actually is in your
   scientific workflow?

5. **Could your own scientific workflow (interpreting pipeline outputs, cross-referencing databases, designing
   experiments) be instrumented as a naturalistic behavioral neuroscience experiment** — logging decision sequences and
   computing empirical information throughput?

---

## The Brain Works at More than 10 bits/s — Rebuttal (nihms-2096004)

1. **Does the 10 bits/s conscious channel bottleneck hold for scientists doing complex data interpretation?** When Dan
   scans a Manhattan plot or a genome browser track, is the rate of "discoveries per second" also ~10 bits/s, or does
   pattern recognition in domain experts operate differently?

2. **Is there a genomics analog to the sensorimotor sifting number** — say, the ratio of raw reads processed by
   alignment algorithms to the biological conclusions extracted (~10⁸?) — and would that ratio be meaningful to track as
   a design metric for the KnowledgeBase pipeline?

3. **Do you see an analogous "sifting number" in your own research workflows that Linus could be specifically designed
   to reduce** — compressing the gap between data ingestion and interpretable insight?

4. **Should the Maestro/Worker architecture be explicitly framed in terms of the 10 bits/s conscious channel** — Workers
   handle high-bandwidth sensorimotor-equivalent tasks; Dan+Claude handle the narrow conscious synthesis channel? Would
   that framing change how you draw the autonomy boundary?

5. **If Linus eventually develops a voice or gesture interface, should interaction design explicitly optimize for the 10
   bits/s bottleneck** — front-loading inference so Dan's conscious output channel is never blocked waiting for compute?

---

## Memory pillar — Garrison thread (added 2026-05)

Eleven papers cited by Erik Garrison's
[Memory makes computation universal, remember?](../../context/notes/garrison_memory_makes_computation_universal.md) plus
the proof paper itself. The cross-thread synthesis is at
[docs/syntheses/memory-synthesis.md](../syntheses/memory-synthesis.md). Per-paper open questions follow; the
memory-pillar items most likely to surface to top-questions.md are flagged inline.

### Zero-Shot Reasoners — "Let's think step by step" (2205.11916v4)

1. **Reasoning traces as first-class memory objects.** Should Linus's session store treat the reasoning trace `z` (Stage
   1 of Zero-shot-CoT) as a separately addressable artifact alongside the final answer, or as one concatenated record?
   The Garrison framework argues for separation; separation costs schema complexity. Worth resolving before the Phase 2
   schema is set. **[memory-pillar candidate]**

2. **Router policy for trigger injection.** Inject "let's think step by step" automatically based on a task-class
   classifier (arithmetic / symbolic / logical → yes; commonsense / retrieval / short-answer → no), or always defer to
   the caller? Blanket policy is wrong; classifier is one more component to maintain. Where does the complexity belong?
   **[memory-pillar candidate]**

3. **Trigger-gap as a Worker fingerprint.** Run a small smoke test (50 items, MultiArith-style) on every Ollama-pulled
   model, measure `accuracy_with_CoT - accuracy_without_CoT` as a per-model property in the model registry. Cheap to
   run, expensive to omit. **[memory-pillar candidate, immediate]**

4. **Episodic memory schema for multi-step tasks.** Full reasoning trace per step, summary, or hybrid (full trace at the
   leaf, summary at the parent)?

5. **Do modern instruction-tuned 7B Workers still need the trigger?** Kojima's 60-point gap was on a 2022 base model;
   Qwen2.5-Coder, Llama-3, and Mistral are RLHF'd on CoT-style data. The operational question may have flipped to "when
   do we _suppress_ unnecessary reasoning to save tokens?"

6. **Trigger sensitivity and the fine-tuning roadmap.** For a fine-tuned Linus model, trigger-invariant (any reasonable
   instruction unlocks step-by-step) or standardize on one canonical trigger?

### Coconut — Continuous Latent Reasoning (2412.06769v3)

1. **Memory boundary in the Worker protocol.** Garrison's framework distinguishes session, episodic, and knowledge
   memory. Coconut highlights a fourth — _intra-step latent state_ inside a single Worker invocation. Does the
   Maestro-Worker protocol need to name this layer explicitly? **[memory-pillar candidate]**

2. **Retain considered alternatives.** If continuous thoughts can superpose multiple candidate next steps, should the
   episodic store make branch points (what was considered, what was chosen, what got pruned) first-class entries? Phase
   2 architecture question. **[memory-pillar candidate]**

3. **Coconut on Apple Silicon.** Is the Meta reference implementation MLX-portable, or does it depend on CUDA-specific
   kernels? A small spike would tell us whether Coconut-style training is on the table for Phase 6 fine-tuning.

4. **Interpretability vs. expressivity.** Linus's bias is toward inspectable artifacts; Coconut deliberately moves
   reasoning into a space humans cannot read. Right stance: "language by default, latent only when task type warrants" —
   and who decides?

5. **Benchmark on ProsQA-style planning.** Worth adding a planning-flavored benchmark to `benchmarks/dan_tasks/` so
   future Worker-model evaluations can detect whether a model is doing real BFS-style search?

### Were RNNs All We Needed? — minLSTM/minGRU (2410.01201v3)

1. **Memory-pillar substrate question.** Is minGRU (or a minGRU-flavored recurrence) the right candidate for Linus's
   session-memory encoder — the thing that compresses a long Worker turn history into a fixed-size rolling state without
   paying quadratic cost? **[memory-pillar candidate]**

2. **MLX port and Apple-Silicon benchmark.** Worth a Phase 1 spike to port the few-line minGRU/minLSTM PyTorch reference
   to MLX, run the Shakespeare experiment on M1 Max, and publish the result?

3. **Substrate for a future Linus-trained model.** Train a small (100M–500M parameter) minGRU/xLSTM/Mamba-style model
   from scratch on Dan's domain corpus in Phase 6, or stay with LoRA-on-Qwen as the safer bet?

4. **minGRU + BitNet cross-product.** Phase 6 (or earlier) experiment: minGRU with BitLinear gates as the most extreme
   hardware-friendly substrate (recurrent + 1-bit + Apple-Silicon-friendly)? **[Phase 8 research direction]**

5. **Minimum useful sequence length for Linus's recurrent components.** The paper stops at 4096 tokens; the case for
   recurrence over attention is strongest at 16k–64k. Worth a Phase 1 benchmark at those lengths to validate the
   extrapolation?

### TimeSformer — Space-Time Attention (2102.05095v4)

1. **Memory framing for the Linus architecture.** Add a "memory-architecture survey" deliverable that explicitly
   inventories factorization tricks (divided attention, sliding window, sparse, axial) alongside structural alternatives
   (Mamba, RWKV, retentive networks)? **[memory-pillar candidate]**

2. **Quadratic-wall budget for Linus's session memory.** At what conversation length on M1 Max with 32 GB unified memory
   does a Qwen-7B / Mistral-7B Worker hit a comparable wall, measured in turns / tokens / tool-output payload size?
   **[memory-pillar candidate, diagnostic]**

3. **Factorization vs. external memory as the first move.** When Linus exceeds a Worker's context window, factorization
   trick (sliding window, KV-cache compression) or external-memory trick (retrieval, summarization, episodic store)?
   Garrison says the second; engineering instinct often reaches for the first.

4. **Video as a future Linus modality.** Out of scope today; if microscope time-series, recorded meetings, screencast
   analysis, lab video become in-scope, this paper is the known-good baseline.

5. **Pretraining-cost asymmetry on Apple Silicon.** TimeSformer drops 13 points without ImageNet-21K pretraining. Should
   Linus ever attempt domain-specific pretraining or stay strictly in the LoRA / fine-tune regime?

### ARC Prize 2024 (2412.04604v2)

1. **ARC-AGI as an episodic-memory diagnostic.** Take a small Linus Worker, run it against 50–100 ARC-AGI public-eval
   tasks twice — once without episodic memory, once with — and measure the delta. The experiment that turns the memory
   claim into a number. **[memory-pillar candidate, Phase 2/3]**

2. **Memory architecture's lower bound.** o3 at $1.15M for 91.5% is the upper bound on what bad memory architecture
   costs. What is the lower bound — how much of o3's gain over the 55.5% open-source SOTA is recoverable by a small
   model with clean episodic memory and TTT?

3. **TTT as a Linus primitive.** Phase 6 fine-tuning roadmap: treat TTT as a first-class capability (Worker can request
   "spawn a fine-tuned variant of yourself for this task"), or keep training-time and inference-time concerns separate?

4. **ARC-AGI-2 timing.** Wait for ARC-AGI-2 (cleaner, fewer brute-force-solvable items), or is ARC-AGI-1 good enough for
   diagnostic use?

5. **Compute-as-memory accounting.** Track "memory budget" as a first-class architectural quantity in ARCHITECTURE.md or
   its own ADR — o3 as the upper bound, human-with-pen-and- paper as the lower bound? **[memory-pillar candidate]**

### Test-Time Training (2411.07279v2)

1. **TTT as episodic memory consolidation.** Should Linus's episodic memory layer be designed around periodic LoRA
   consolidation of session transcripts? Convert memory into the same substrate the model already uses. Worth a Phase 3
   spike, or premature? **[memory-pillar candidate]**

2. **Apple Silicon viability smoke test.** Phase 1 reproduction: 10 ARC tasks, Llama-3.2-1B, mlx-lm LoRA, leave-one-out
   synthetic data — purely to measure per-task compute cost on M1 Max. **[memory-pillar candidate]**

3. **TTT vs. KnowledgeBase as memory substrates.** TTT-on-session-tuples for the episodic layer while KnowledgeBase
   keeps serving the semantic layer? Or are they two ends of a continuum where the right answer is "KB entries that have
   been read/used recently get consolidated into a rolling LoRA adapter"?

4. **Skill-specific adapters.** In Phase 7, each Linus skill ships with canonical examples and uses TTT to fit a
   transient adapter on invocation, with adapter caching?

5. **Compute-vs-memory budget.** Linus's scarce M1 Max compute on TTT, or invest the same effort in a more durable
   explicit episodic-memory store? **[central architectural tradeoff]**

### Llama 3 Herd (2407.21783v3)

1. **Worker bake-off scope.** Add Llama 3.1 8B Instruct (Q4_K_M / Q5_K_M via Ollama) to the Phase 1 bake-off alongside
   Qwen2.5-Coder-7B and Mistral-7B, with the Speed paper's three-task protocol as the measurement schema?

2. **Long context vs. episodic store.** Llama 3 bets "buy memory by extending context to 128K." Phase 2 design:
   deliberately _cap_ in-context window usage at 8–16K and route beyond that through a real episodic store, even if the
   underlying Worker supports 128K? **[memory-pillar candidate, central design choice]**

3. **Multi-needle as an episodic-store benchmark.** Add a synthetic multi-needle task to `benchmarks/dan_tasks/`
   evaluated against Linus's _episodic store_ rather than against a model context, to verify the four sub-requirements?

4. **Distillation rather than fine-tuning.** Phase 6 path: hosted Llama 3.1 405B (or Claude) as a teacher to distill
   domain-specific behaviors into a local 8B or BitNet student?

5. **Open-weights longevity.** Llama 3 is Llama 3 Community License (not OSI-open). Linus principle of "fully under
   Dan's control" — treat Llama 3 as transitional, replace when a fully-open or BitNet-class equivalent appears?

### Sparks of AGI (2303.12712v5)

1. **Memory substrate decision, forced by Sparks Section 8.** Phase 2 MVP commits upfront to an explicit scratchpad
   protocol — every Worker invocation gets a writable, durable scratch region the orchestration layer manages — rather
   than relying on the chat template? **[memory-pillar candidate]**

2. **Which of Dan's domains has the most useful transferred priors?** Run a small Sparks-style qualitative probe on
   three or four cross-domain prompts against current Ollama models?

3. **Episodic memory as the o1 anti-pattern.** Persist not just final outputs but _intermediate reasoning traces_ of a
   Worker, so next session can build on the deliberation, not just the conclusion? **[memory-pillar candidate]**

4. **Evaluation philosophy.** Lean explicitly into Sparks methodology — small numbers of perturbed, open-ended tasks
   judged by Dan — alongside the quantitative tok/s and task-completion-time measurements?

### Chinchilla (2203.15556v1)

1. **Data axis for fine-tuning.** What does Linus's "1.4T tokens equivalent" look like — the realistic upper bound on
   high-quality, well-filtered tokens we can assemble from Dan's papers, threads, code, and notes, and is it large
   enough relative to a 7B LoRA target to matter?

2. **Memory vs. scaling, in concrete terms.** Linus's bet is "use a small Chinchilla-era model + strong
   episodic/semantic memory" instead of "use a bigger model with weaker memory." Architectural commitment in Phase 2;
   what is the test that would falsify it? **[memory-pillar candidate]**

3. **Inference-economics overshoot.** Llama-3-style overtrained smaller models as the default Worker substrate, since
   inference cost on M1 Max is the binding constraint?

4. **Curation as a first-class Linus activity.** KnowledgeBase ingestion pipeline versions, hashes, and quality-scores
   corpus subsets the way pretraining labs version their data mixes — "corpus version 0.3 with stricter dedup" as a
   first-class artifact?

### CoT Theory — Feng, Zhang et al. (2305.15408v5)

1. **Scratchpad as first-class memory object.** Phase 2 session store treats reasoning tokens as durable artifacts by
   default — versioned, addressable, replayable — or as ephemeral generation byproducts? Expressivity argument says the
   former; chat harnesses default to the latter. **[memory-pillar candidate, Phase 2 critical]**

2. **Reasoning-token budget per task class.** Router maps task-class to CoT-budget (DP-shaped tasks get up to 4096
   reasoning tokens with full retention; lookup tasks get 256 with truncation), or uniform budgeting until benchmarks
   force the issue? **[memory-pillar candidate]**

3. **Worker-size vs CoT-length tradeoff.** Empirical Phase 1 benchmark: a 7B Worker with generous CoT budget vs. a 14B
   Worker with terse output on Dan's task suite. Theory predicts small-with-CoT wins on inherently sequential tasks.
   **[memory-pillar candidate, falsifiable]**

4. **KV-cache continuity as architectural constraint.** Linus inference layer commits to preserving KV cache across
   Worker turns within a session as a hard requirement, or treat as later optimization? Affects which inference servers
   (Ollama, mlx-lm, future pmetal) are viable Worker backends. **[memory-pillar candidate]**

5. **Faithfulness check for retained reasoning.** Phase 3 component that audits CoT for self-consistency, or out of
   scope until specific failure modes appear?

### Expressive Power of Transformers with CoT — Merrill & Sabharwal (2310.07923v5)

1. **Scratchpad as first-class artifact.** Phase 2 session store treats model scratchpad / chain-of-thought tokens as
   durable, addressable artifacts on equal footing with final answers and tool outputs? Smallest viable schema (turn id,
   scratchpad blob, hash, timestamp) that satisfies Garrison's four sub-requirements? **[memory-pillar candidate]**

2. **Linear vs. polynomial scratchpad budget per Worker call.** Per-call scratchpad budgets in the router based on task
   type / deadline / energy budget? **[memory-pillar candidate]**

3. **Recurrence as a memory-cost optimization.** Phase 6 actively prefers state-space or hybrid architectures for the
   default Linus Worker because they implement the Garrison/Merrill-Sabharwal recursion requirement at lower per-step
   cost on a 32 GB unified-memory budget? Connects to Bonsai / pmetal / mlx-flash thread. **[memory-pillar candidate]**

4. **Cross-session episodic memory as the "outer scratchpad."** What experiment would distinguish a Linus with a thin
   episodic store from one without, in a way sensitive to the hypothesized expressivity gap rather than just to
   convenience? **[memory-pillar candidate]**

---

# Part 3 — From `docs/syntheses` documents

## LLM Wiki & Community Insights (docs/llm-wiki-synthesis.md)

1. **How should Linus implement the write-back rule across parallel Workers?** For Phase 3 multi-agent fan-out, multiple
   Workers may simultaneously propose updates to the same KB pages. What coordination mechanism prevents parallel
   workers from producing contradictory KB writes? (git branch per ingestion, mesh sync, last-write-wins?)

2. **What is the right confidence decay rate for different claim types in a scientific corpus?** The v2 gist proposes
   Ebbinghaus decay — exponential with time, reset on access or confirmation. Methods sections decay faster than
   foundational results. What are the right decay constants for Dan's domains (genomics, computational biology, ML
   inference)?

3. **Can the FUNGI processing protocol (Frame, Unearth, Network, Grow, Interrogate) be formalized as a KnowledgeBase
   ingest step?** Is it tractable to run this on every paper with a local Qwen2.5 Worker, or does the Interrogate step
   require a stronger model?

4. **Should Linus adopt immutable atomic notes (Zettelkasten) or mutable wiki pages for KnowledgeBase?** Mutable pages
   are easier to keep current but make provenance harder. Immutable notes with stable IDs make every claim traceable but
   require a separate synthesis layer. Is there a hybrid given that KnowledgeBase is already structured around entity
   pages?

5. **What is the right entity deduplication threshold for KnowledgeBase?** Some systems use >60% entity overlap as the
   threshold for updating vs. creating. The community identified concept deduplication ("attention mechanism" vs
   "self-attention") as the hardest part of graph construction. What threshold works for Dan's scientific domain?

6. **How should Linus handle the "mostly correct is broken" problem for high-stakes content?** For formal protocols and
   method descriptions in the KB, a mostly-correct summary is a broken state, not a degraded one. Should those content
   types use the wiki only as a pointer to validated source material?

7. **What does the entrepreneurial application surface look like for a private compiled KB?** The business use cases
   (internal wiki fed by domain content, competitive analysis, due diligence) suggest a Linus-derived KB-as-a-service
   could be differentiated. What would it look like for a small lab or startup?

8. **Which repos from the LLM wiki community list should be cloned into `repos/` as reference material?** Top
   candidates: `omega-memory` (hybrid FTS5+vector+cross-encoder retrieval, 95.4% accuracy at 50ms), `keppi` (graph
   traversal with blast-radius analysis on 1.4K notes), `rohitg00/agentmemory` (production memory/retrieval with 43 MCP
   tools), `openaugi` (simplest graph-backed memory with write-back). See `docs/llm-wiki-synthesis.md` Section 8 for
   full list.

---

## Skills, Practices & Entrepreneurial Opportunities (docs/skills-and-practices-synthesis.md)

1. **What is Linus's first monetizable capability, and when?** Should Dan start generating revenue from AI-assisted
   services now (scientific literature intelligence retainer, ~$1,000–$3,000/month/client) using hosted Claude + domain
   expertise, while Linus builds in the background? Or does investment focus remain entirely on infrastructure? Real
   client feedback is more valuable than speculative roadmap planning.

2. **Does Linus need a custom orchestration layer, or will Task Master AI + Cline cover Phase 2?** The Algorithm says
   delete before building. Do Dan's requirements for KnowledgeBase integration, sandbox policy enforcement, and Apple
   Silicon optimization justify a custom orchestration layer, or does combining existing tools get to a working system
   faster?

3. **What is Linus's smallest-possible closed Maestro/Worker loop that Dan could run this week?** A Worker receiving a
   spec, executing it, and returning a verifiable result — even trivially. Getting that loop working is more valuable
   than any further planning.

4. **What is the right fine-tuning target in Phase 6, and does it change the entrepreneurial calculus?** A
   genomics-specialized model opens the scientific intelligence opportunities; a coding-specialized model accelerates
   Linus's own development. This decision should probably be made by Phase 3, not deferred to Phase 6.

5. **Is Dan's domain expertise (biochemistry, genomics, environmental science) the scarce input at Maestro time, rather
   than task decomposition skill?** This shapes how the Maestro/Worker boundary is drawn — domain expertise applied to
   problems Workers cannot touch may be higher-leverage than decomposing tasks for Workers to execute.

---

## Memory Synthesis (docs/syntheses/memory-synthesis.md)

Cross-cutting questions surfaced by the [memory synthesis](../syntheses/memory-synthesis.md) that supplement the
per-paper questions in the Memory pillar section above. These are the items that synthesize across multiple papers in
the Garrison thread.

1. **The substrate question for cross-session episodic memory (Layer C).** SQLite + git as the conservative v0 is an
   obvious starting point. The Akyürek TTT result is striking enough to warrant explicit consideration:
   structured-text-and-hashes (debuggable, inspectable, slow to consult) or parametric-via-LoRA-consolidation (fast,
   opaque, training pass per consolidation event)? Or two ends of a continuum where knowledge graduates from text into
   LoRA after sufficient repeated access? Phase 2 spec should not commit to (3) but should not preclude it either.
   **[memory-pillar candidate]**

2. **Faithfulness of retained reasoning.** Stored reasoning traces surfaced to Dan are implicitly endorsed, but Kojima's
   error analysis notes traces sometimes generate unnecessary steps after reaching the correct answer or just rephrase
   the question. Phase 3 component that audits CoT for self-consistency, or out of scope until specific failure modes
   appear?

3. **Memory budget as a first-class accounting quantity.** o3 paid $1.15M to brute-force memory reliability through
   parallel search. Linus's local hardware budget is a few tens of dollars of electricity per day. ARCHITECTURE.md (or a
   new ADR) treats memory budget as a first-class quantity with the o3 number as cautionary upper bound and
   human-with-pen-and-paper as the lower bound? **[memory-pillar candidate]**

4. **ARC-AGI as a memory diagnostic, not a target.** `benchmarks/dan_tasks/` includes 50–100 public-eval ARC-AGI tasks,
   run with and without the episodic store as a memory-architecture probe? Not a Linus capability target; one of the few
   public-domain proxies for "reliable computation across many steps on a novel task."

5. **Scratchpad-budget policy per task class.** Router enforces per-call CoT budgets based on task class, with a v0
   mapping (DP-shaped tasks → 4096 tokens with full retention; lookup tasks → 256 with truncation)? Cheap to implement;
   would generate data to inform a more refined policy. **[memory-pillar candidate]**

6. **Memory architecture spec as a Phase 2 deliverable.** Commit to writing `docs/specs/memory-architecture.md` walking
   through Layers A–D, the four sub-requirement obligations, and the substrate choice per layer — _before_ the
   orchestration layer's session and dispatch primitives are written? The synthesis says yes; the formal
   complexity-theoretic results give the architectural pressure. **[memory-pillar Tier 1 candidate]**

---

## Security Posture (docs/security-synthesis.md)

1. **How much supply chain risk is acceptable, and at what cost?** Full hash pinning and lock files add friction to the
   development workflow. How does Dan want to balance iteration speed against supply chain integrity? A middle path
   (audit monthly, hash-pin at phase milestones) should be an explicit choice.

2. **Should Linus ever run untrusted packages from the internet, and if so, how?** Should experimental packages always
   run in isolated, disposable `uv` virtual environments that are never activated alongside the linus conda env, or is
   conda env isolation sufficient?

3. **What is the threat model for the KnowledgeBase content?** Dan adds papers from arXiv, bioRxiv, and other sources.
   Is the threat of a maliciously crafted PDF realistic enough to warrant PDF sanitization tooling? Or is the corpus
   trusted because Dan controls what enters it?

4. **When the OpenAI-compatible endpoint is exposed, who is allowed to query it?** Is there a point at which Linus needs
   TLS and mutual authentication (e.g., if run on a home server or accessed from mobile), or will it remain strictly
   localhost-only?

5. **How should Linus handle a detected supply chain compromise?** If `pip-audit` reports a CVE in an installed package,
   what is the response protocol? Immediate env rebuild? Credential rotation as a precaution? The litellm incident was
   discovered by accident via a RAM crash; a more subtle attack would not announce itself.

---

## Cross-cutting (from `docs/paper-landscape.md`)

These reappeared across multiple paper notes and are reproduced here so they are not lost amid the per-paper questions:

1. Is the _single most useful Phase 1 spike_ "build bitnet.cpp on M1 Max, pull `bitnet-b1.58-2B-4T-gguf`, benchmark vs
   Ollama-served Qwen and Llama"? Mentioned in 2B4T, bitnet.cpp, and BitNet Distillation notes.

2. Should Linus commit to a BitNet-derived Worker for Phase 6, or keep the FP16-LoRA option open? Mentioned in BitNet
   b1.58 and BitNet Distillation notes.

3. Is a BitNet × Flash-MoE × JPmHC synthesis a real Phase 8 research direction, or premature speculation? Mentioned in
   JPmHC and Flash-MoE notes.

4. Should there be a `synthesis-bitnet-on-apple-silicon.md` companion note that pulls the four-or-five most relevant
   papers into one "what's the actual inference path" writeup? Mentioned in BitNet v2 and 2B4T notes.

5. Should the KB v1 embedding pipeline use the recipe from Stankevičius & Lukoševičius (idf weighting + first+last
   layers + quantile-u normalization), and should that paper's ablation methodology be lifted into a
   `docs/experimental-protocol.md` Linus-house style guide for benchmark design? Mentioned in the embeddings note.

6. Should there be a `docs/specs/kb-architecture.md` that walks through the Hogan et al. KG survey section by section
   and records the design choice + rationale for each KB layer (data model, schema, identity, context, query language,
   deductive layer, inductive layer)? Mentioned in the KG-survey note.

7. Should KB embeddings be PCA-reduced before indexing, and should the KB observability dashboard track distance
   discrimination `|D_max − D_min| / D_min` as a health metric? Mentioned in the Curse of Dimensionality note. Both are
   small-effort, large-payoff implementations.
