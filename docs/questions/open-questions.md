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

---

# Part 4 — From the 2026-05-04 fan-out (10 group PRs)

This part collects all "Questions for Dan" surfaced by the 2026-05-04 repo-note fan-out (PRs #1–#10). 65 new repo notes
plus 2 late adds (claude-prism, semanticworkbench) plus 10 cross-cutting per-group syntheses, totalling ~375 questions.
Each group's section nests its repo notes (`### <repo>`) and the synthesis cross-cutting block
(`### g<N>-<slug> synthesis (cross-cutting)`).

These questions are NOT yet prioritized — that's a separate Maestro/Dan planning session that promotes selected items
into [top-questions.md](top-questions.md) tiers. Many synthesis-level questions are reframings of repo-note questions;
both are preserved here so the dedupe pass can be done deliberately rather than by Worker fiat.

---

## Group 1 — Apple Silicon Inference & Training

### autoresearch-mlx

1. **Smoke run timing.** Run the verbatim 5-minute loop now alongside Phase 1b's pmetal evaluation so we have a
   hardware-local baseline on this M1 Max before Phase 6d needs it, or wait until 6d formally opens?

2. **Payload swap for Phase 6d.** Is the first real Linus autoloop a LoRA sweep with held-out PPL on Dan's corpus, or go
   straight to a Dan-task-suite scorer despite the higher per-experiment cost?

3. **Autonomy tier for "NEVER STOP".** `program.md` assumes an agent running unsupervised overnight on its own branch,
   committing freely. SAFETY.md doesn't authorize that today. Is overnight-autonomous-on-an-agent-branch the right first
   graduation step in Phase 7?

4. **`program.md` → SKILL.md.** Promote it to the Anthropic `SKILL.md` convention as the template for Linus's first real
   skill, or keep `program.md` flavor for now?

5. **Muon variant.** The README hints the working (non-public) port used Muon to reach `1.294526` on M4 Max. Worth
   porting Muon into our fork as the first agent-driven experiment, or stay AdamW-only?

### g1-apple-silicon synthesis (cross-cutting)

1. **Should the "trust the OS page cache" finding be promoted to a named Linus engineering convention in CLAUDE.md?** It
   currently appears in the flash-moe note as a finding and in this synthesis as a recommendation. Elevating it to
   CLAUDE.md's Known Library Quirks would make it visible to every future Worker operating on inference-adjacent code.
   The cost is one paragraph in a file that already carries this kind of operational wisdom.

2. **Does the ANE prefill + GPU decode configuration belong in Phase 1b's explicit benchmark matrix?** The ANE repo
   confirms it is real on M4 and pmetal ships the implementation. Dan's M1 Max is the hardware the benchmark must run
   on. Treating it as an explicit configuration changes Phase 1b planning; deferring it leaves a measurement gap that
   Phase 2a will fill in retrospectively instead of prospectively.

3. **What is the right per-experiment budget for Phase 6d's autoloop on M1 Max?** Karpathy uses 5 minutes on H100. The
   autoresearch-mlx README shows 6–7 minutes per experiment on Apple Silicon for pretraining; a LoRA sweep on a 7B model
   with a held-out Dan-task-suite eval will be substantially longer. Picking the budget before Phase 6d opens determines
   how many experiments an overnight run can complete and what metric is feasible. The tradeoff is: shorter budget with
   a fast proxy metric (PPL on Dan's corpus) gives more experiments; longer budget with Dan-task-suite scoring gives
   higher-signal experiments. Both are defensible; the choice should be explicit.

4. **Should the autoresearch-mlx smoke run happen now (Phase 1c co-scheduled) or wait for Phase 6d?** Running it now is
   cheap (one evening, `uv sync && uv run`) and produces a hardware-local baseline and a concrete feel for the 6–7
   minute/experiment cycle on this chip before Phase 6d planning needs those numbers. Waiting avoids spending time on
   infrastructure that isn't Phase 1's critical path. The case for doing it now is that it takes less time to run the
   experiment than to estimate it.

5. **Is pmetal-mcp a serious Phase 2a tool registry candidate, or is it study material?** The 45-tool MCP server that
   ships with pmetal is a complete tool registry if Linus adds KnowledgeBase integration on top. The alternative is
   Linus building its own registry from scratch and studying pmetal-mcp as a reference. The Algorithm says delete before
   building; the case for using pmetal-mcp as the foundation is strong if the Phase 1b verdict is favorable. This
   decision should appear explicitly in Phase 2a planning documents rather than default to one answer or the other.

---

## Group 2 — LLM Wiki Engine Implementations

# Group 2 Questions for Dan — Complete Extract

### link

1. **Substrate choice for KnowledgeBase write layer.** Link bets on plain markdown in a directory, no DB. KnowledgeBase
   today uses SQLite for metadata and a vector store for embeddings. Should Phase 2's wiki-style synthesis layer sit on
   top of KnowledgeBase's existing storage, or should it adopt Link's directory-of-markdown substrate (with KB
   continuing to handle papers and embeddings)?
2. **Confidence tags vs. claim-typing.** The security synthesis argues for typed claims with content-hashed identifiers;
   Link uses inline `[confidence: high/medium/low]` strings in prose. Are those compatible — confidence as a field on a
   typed claim — or does adopting claim-typing mean abandoning Link's prose-friendly tagging?
3. **MCP as the KnowledgeBase tool surface.** Link ships `link-mcp` as the agent-facing API. Phase 3 was scoped as
   "deeper KB integration" without committing to a protocol. Should Linus's KB tools be MCP-native from the start so
   that any harness (Cline, Claude Code, openclaw, claw-code) gets KB access for free?
4. **Wiki maintenance as a Worker job.** The Link model is "agent ingests, agent compiles, agent maintains." On Linus
   that's a Worker loop running on Qwen2.5-Coder or a future fine-tuned Linus. Is wiki maintenance a good first
   long-running Worker task to design around in Phase 3, or does it belong later?
5. **Sibling sweep verdict.** Of the eleven Group-2 engines, only the rest of the sweep will tell us whether Link's
   stdlib-only / markdown-only minimalism is the right baseline or whether a sibling with embeddings + BM25 + graph
   re-ranking is closer to what Phase 3 needs. Hold the integration decision until the full Group 2 read is in?

### llmwiki

1. **Karpathy-wiki vs. KnowledgeBase RAG.** llmwiki's whole bet is "agent-maintained markdown wiki beats RAG-on-raw-PDFs
   for compounding research knowledge." KnowledgeBase today is a RAG/graph system. Is the Phase 2 KB v1 model a RAG-only
   baseline, an llmwiki-style compiled-wiki layer, or both side by side with the wiki citing back into the RAG?
2. **MCP surface size.** llmwiki gives Claude five tools (`guide`, `search`, `read`, `write`, `delete`) and that appears
   to be enough for a maintained wiki. pmetal-mcp ships 45. Is the Phase 3 target for Linus closer to five-per-domain or
   to a flat 30-50 catalog?
3. **Workspace cardinality.** llmwiki enforces one workspace per MCP server entry. For Linus, do you want one KB MCP
   endpoint covering all of `context/`, or one per subcorpus (papers, notes, threads, books) so that scope is explicit
   to the agent?
4. **Claim-typing interop.** The security synthesis recommends content-hashing and typed claims for KB entries.
   llmwiki's `documents` table has a free-form `tags JSON` column and no claim type. Should a Linus port add a
   `claim_type` column and SHA-256 of canonicalized content from day one, or is that a Phase 3 concern?
5. **Differentiator confidence.** I read llmwiki's code but only the group framing for the other ten siblings. Before
   committing to "Study" rather than something stronger, would you want the same depth of read on `wikiloom`,
   `TheKnowledge`, and `OmegaWiki` first to confirm llmwiki really is the cleanest reference and not just the first one
   read?

### llmbase

1. **Operations-registry adoption.** The `Operation(name, handler, params, writes, category)` + `dispatch()` pattern is
   a near-drop-in answer to Phase 2a's "one tool, three surfaces (CLI / OpenAI-compat HTTP / MCP)" problem. Adopt it as
   the Linus tool-registry shape, or design a different abstraction that better fits the Maestro/Worker delegation
   model?
2. **Two-layer recall vs Qdrant.** llmbase makes a defensible no-vector-DB argument at personal scale (TF-IDF over
   compiled concepts + verbatim raw fallback). The KnowledgeBase submodule already commits to Qdrant. Is Phase 3 hybrid
   retrieval `Qdrant + BM25/TF-IDF + compiled concept layer`, or stay vector-first and treat llmbase's two-layer pattern
   as a curiosity?
3. **Compiled concept layer over papers.** llmbase's central bet is that a LLM-maintained markdown wiki over your corpus
   is more useful than raw chunks. For Dan's papers/notes/threads — do you want a compiled concept layer on top of the
   existing KnowledgeBase chunks, or is the chunk-and-retrieve baseline sufficient for Phase 2?
4. **Sibling differentiation.** `llmbase` and `llmwiki` (the namesake sibling) share an author namespace and framing. Is
   there value in studying both, or should one be designated canonical and the other ignored?
5. **Autonomous worker model.** llmbase's worker thread (CBETA every 6h, compile every 1h, health every 24h) is the
   simplest "always-on KB" pattern in the group. Is an always-on background ingest/compile/heal loop in scope for Linus,
   or does ingestion stay user-initiated through Phase 4?

### llmwiki-cli

1. **Tool-surface minimalism for KB.** llmwiki-cli's full agent surface is ~14 commands, two of which (`read`, `write`)
   do most of the work. Is that the right ceiling for the Phase 2 KnowledgeBase tool registry, or do you expect Linus
   tools to be richer (chunked retrieval, citation, structured-query) from day one?
2. **Full-rewrite vs patch semantics.** The "always rewrite the full page from JSON" contract trades efficiency for
   agent reliability. For KnowledgeBase paper summaries this is probably fine; for synthesis notes that grow over time
   it gets expensive. Want Linus's KB write tool to follow this contract or support an append/patch variant?
3. **Personal wiki as a separate pillar.** Is there a Dan-personal-notes wiki use case that should be served by
   `llmwiki-cli` as a third-party tool alongside KnowledgeBase, or does everything funnel through the KnowledgeBase
   pillar?
4. **Karpathy-pattern convergence.** With eleven implementations of the same idea in `repos/`, do you want a single
   Maestro-authored synthesis ADR that picks one shape (this CLI, llmwiki's full stack, swarmvault's monorepo, a
   workflow-pattern from Group 3) as the Linus reference, or stay agnostic until Phase 2a forces a choice?
5. **d3-force graph viz.** The interactive graph is the most user-visible artifact in this repo. Worth extracting as a
   standalone KnowledgeBase visualization in Phase 2, or noise relative to Streamlit + future openclaw front-ends?

### wikidesk

1. **Multi-agent share vs single-process orchestration.** wikidesk solves "N agents on N machines, one wiki." Linus
   Phase 2 today is "N harnesses, one machine, one orchestration backend." Is the multi-machine case (e.g., M1 Max + Mac
   Studio, or laptop + desktop) something to plan KB access around now, or YAGNI until Phase 8?
2. **Research-as-tool granularity.** wikidesk's `research` tool dispatches a full agent run that may take 30 minutes.
   Linus's tool registry has so far been imagined as fast, deterministic functions. Do you want to admit long-running,
   queued, pollable tools as a first-class category in the Phase 2a registry, or keep that pattern outside the registry
   and behind a separate "agent fan-out" surface?
3. **Wiki format vs KnowledgeBase schema.** wikidesk assumes `[[wikilink]]`-style markdown. Your KnowledgeBase has its
   own schema (papers, notes, a knowledge graph). Is there interest in maintaining a parallel `wiki/`
   human-and-agent-readable view of the KB, or does the existing query/RAG surface stay the only access path?
4. **Sandboxing the worker on macOS.** wikidesk explicitly punts to Docker/bubblewrap. If Linus ever runs an autonomous
   research-agent loop on the M1 Max, what's the macOS-native sandbox plan (Seatbelt profiles? app-sandbox? confined
   launchd jobs?), and is that a Phase 7 concern or do we want a sketch in SAFETY.md sooner?
5. **MCP as the KB surface.** wikidesk speaks both MCP and REST for the same operations. Is "Linus exposes its tools
   over MCP" a settled direction (consistent with the Cline/openclaw/pmetal-mcp ecosystem), or still open?

### wikiloom

1. **Chunk-id convention.** Are you ready to commit the Phase 2 KB schema to `sha256(source_hash + chunk_index)[:N]`
   truncated chunk ids, or do you want full-length hashes everywhere for zero-collision peace of mind? WikiLoom uses 12
   hex chars (48 bits); the KB might have orders of magnitude more chunks long-term.
2. **Write-back protection model.** Does the KB need an auto-region marker (durable, survives re-synthesis) plus a
   commit-prefix flag (soft, cleared by next auto-action), or is one of the two layers enough for our use case? The
   marker is more invasive on page bodies; the prefix is invisible but easier to lose.
3. **Linker confidence tiers.** WikiLoom's 95 / 85 / 70 cutoffs come from PKM heuristics. For a research KB linking
   scientific entities, the prior is different. Do we want to start from these defaults and tune, or design our own
   scoring scale from scratch?
4. **Cross-sibling check.** I claimed the deterministic-linking + structural-provenance combo is sharpest in WikiLoom
   across the eleven. That claim should be re-verified against `TheKnowledge` and `wikimind` notes when those are
   written — flag this as a follow-up so the differentiation list stays honest.
5. **Git-as-substrate scope.** Is the Linus orchestration log itself a candidate for the same "auto-commit with
   classifying prefix" pattern, separate from the KB? It's a clean audit trail, but it does mean every Linus session
   that touches state writes commits.

### wikimind

1. **Wiki-as-product vs RAG-as-product.** Karpathy's pattern is "LLM compiles consumed sources into a persistent wiki."
   KnowledgeBase today is RAG-as-product. Is there appetite for a wiki-compilation layer on top of KnowledgeBase in
   Phase 3, or does the corpus stay query-only with provenance via citation rather than via compiled articles?
2. **YouTube transcripts.** Is YouTube-as-source actually a Linus use case (lectures, conference talks, podcast
   interviews on biochem topics)? If yes, wikimind's `youtube-transcript-api` adapter is a 1-day lift; if not, drop it
   from the shortlist.
3. **docling-serve sidecar.** KnowledgeBase currently uses pypdf (with the `sys.maxsize` quirk in CLAUDE.md). Is
   upgrading PDF extraction to docling-serve worth a Docker dependency, or stay native with pymupdf/pypdf?
4. **Provider router placement.** wikimind's `llm_router.py` is per-app; Linus's orchestration layer will need the same
   logic at a higher level (one router, many tools and harnesses). Should Linus copy this shape or wait until Phase 2a's
   tool-registry design forces the decision?
5. **Sibling differentiation visibility.** I called out wikimind's YouTube + multi-source ingest + Fly deploy story as
   differentiators against the other ten LLM-Wiki repos, but only on README evidence — the other ten notes don't exist
   yet. Should the curation pass produce a comparison matrix at the end of the group, or trust the per-repo notes to
   converge?

### OmegaWiki

1. **Skill standard adoption.** OmegaWiki uses the Anthropic Skills format (`SKILL.md` + on-demand `references/`)
   verbatim. Should Phase 7 commit to this as Linus's skill standard so skills written for Linus are also loadable by
   hosted Claude Code, or do we want a Linus-native format that local workers handle better?
2. **Claim / experiment / idea entities in KnowledgeBase v1.** OmegaWiki's wiki schema treats `claims`, `experiments`,
   `ideas`, and `failure_reason` as first-class. Should Phase 2 KB adopt that vocabulary now (cheap while the schema is
   still soft) or stay paper-centric until a real research workflow forces the question?
3. **Adversarial-review MCP pattern.** The `mcp-servers/llm-review/` model — a second LLM as an MCP-exposed reviewer for
   novelty / refinement / draft critique — is the cleanest "two-model adversarial loop" template in the cluster. Worth
   building an analogous Linus MCP that exposes a worker model to Claude Code as a reviewer? Phase 3 fits.
4. **Differentiator confidence.** The "24 skills, full lifecycle" claim is real (counted: 24 skill directories under
   `.claude/skills/`, plus `shared-references/`). Sibling-by-sibling I haven't yet confirmed whether `wikiloom` or
   `TheKnowledge` reach into experiment design or paper drafting; if any of them do, OmegaWiki's "most ambitious"
   framing softens. Want me to flag that as a follow-up audit before drawing Phase 7 conclusions?
5. **Hosted-Claude dependency as a benchmark control.** Because OmegaWiki only works under Claude Code, it is also a
   natural Maestro-side benchmark target — "what does the lifecycle look like with frontier models, against which
   Linus's local-worker version is measured." Worth designating as a Phase 1b / Phase 7 reference baseline?

### swarmvault

1. **Context packs as the Maestro/Worker artifact.** SwarmVault's
   `context build "<goal>" --target <path> --budget <tokens>` is essentially the spec format
   `docs/maestro-worker-protocol.md` is reaching for, but with citations and provenance baked in. Should Phase 2's spec
   format be Linus-native or a thin wrapper over a swarmvault-style bounded-context-pack tool?
2. **Task ledger vs. git history.** SwarmVault's `task start|update|finish` writes a parallel ledger under
   `state/memory/tasks/` and folds it into the knowledge graph. Linus already has git for atomic commits and branches
   for agent work (BRANCHING.md). Is a separate task ledger redundant, complementary (commits are artifacts, ledger is
   intent), or actively confusing?
3. **i18n in the cohort.** SwarmVault is the only sibling shipping Chinese and Japanese READMEs. That suggests the
   author is courting an international user base that the English-only siblings (`llmwiki`, `llmwiki-cli`, `wikidesk`)
   are not. Useful signal for "which of the eleven engines has real users," or noise?
4. **Contradiction detection as a KB feature.** SwarmVault tags every edge as `extracted` / `inferred` / `ambiguous` and
   runs `lint --conflicts`. The security synthesis recommends typed claims + content hashing for KB entries — is the
   swarmvault edge-typing taxonomy the right vocabulary to adopt for Linus, or is it too coarse for scientific claims?
5. **Differentiator confidence.** I depth-read swarmvault and only spot-checked `llmwiki-cli`'s `package.json` for the
   comparison. Before committing the Study verdict, would you want me to do the same depth on `wikiloom`, `wikimind`,
   and `TheKnowledge` to confirm context-packs + task-ledger really are unique to swarmvault and not also present in a
   leaner sibling?

### synthadoc

1. **AGPL boundary.** Synthadoc's engine is AGPL-3.0 with Apache-2.0 only on the `BaseSkill` and `LLMProvider` extension
   classes. Are you comfortable with "read and reimplement the patterns" being the only path, or is there a world where
   Linus tolerates an AGPL submodule for a self-hosted, never-distributed engine?
2. **Multi-wiki vs. single-KB cardinality.** Synthadoc's whole UX assumes one wiki = one domain on its own port; the
   same question came up against `llmwiki`. Do you want Linus's KB to be one endpoint over all of `context/`, or one per
   subcorpus (papers / notes / threads / books) so the agent's scope is explicit?
3. **Cost-guard relevance.** Synthadoc's `cost_guard.py` exists because its target users hit paid APIs. Linus's
   philosophy is local-first with no paid APIs in the steady state. Is there still a reason to port a soft-warn /
   hard-gate layer (for guarding ANE/GPU minutes, token-budget per task, or future hosted-model spillover), or is this
   inspector-only?
4. **Skill hot-load model.** Synthadoc's `BaseSkill` + folder-scan + `entry_points` approach is more dynamic than
   `llmbase`'s `register()` decorator. For Phase 7, do you want Linus skills to be hot-loadable from a directory without
   a server restart, or is restart-on-skill-change acceptable and simpler?
5. **Decomposition as a Phase 3 default.** Synthadoc decomposes both queries and web searches into parallel sub-tasks
   with a graceful fallback. Should Phase 3's agent fan-out adopt this as the default execution shape (decompose →
   parallel workers → merge), or is that overkill for the worker-orchestra Linus is initially aiming at?

### TheKnowledge

1. **NotebookLM-shaped slot in Linus.** TheKnowledge treats NotebookLM as "the heavy-synthesis service behind the
   gateway." Linus has a directly analogous slot: a heavy-synthesis worker that's not the chat-loop model. Should that
   slot in Phase 3 be a larger MLX model running locally, hosted Claude under explicit user invocation, or both behind a
   `synthesis-backend` ADR?
2. **Citation-as-hard-invariant.** TheKnowledge's validator rejects any claim lacking `[[sources/<id>]]`. Worth porting
   as a Phase 2 KB invariant on Linus-authored synthesis pages, or kept as a lint warning so Workers can produce
   exploratory drafts cheaply?
3. **Converter scope for Phase 2.** TheKnowledge ships 13 source-type converters. Dan's `context/` today is mostly PDFs
   and notes — is the right Phase 2 scope just `pdf` + `note` + `web`, with audiobook/voice/image deferred to Phase 4
   data sovereignty, or does the breadth matter from day one?
4. **Gateway pattern vs. KnowledgeBase APIs.** KnowledgeBase already exposes Python APIs. Should Linus's KB tools call
   KnowledgeBase directly, or wrap KnowledgeBase behind a TheKnowledge-style gateway so MCP, validator, and audit log
   are uniform across all writers?
5. **Differentiator confidence.** I read TheKnowledge's code in depth and only the group framing for nine of the ten
   siblings (plus `llmwiki` from the prior note). The "NotebookLM behind a gateway" angle reads as genuinely unique in
   the cohort, but it's worth confirming once `OmegaWiki`, `wikiloom`, `wikimind`, and the others have notes — none of
   them sound like they share that bet, but I haven't verified.

### g2-wiki-engines synthesis (cross-cutting)

1. **Claim typing as a hard invariant or a lint warning?** TheKnowledge's validator hard-rejects writes missing a
   citation link. Wikiloom's human-edit protection is enforced by convention plus commit prefix. The security synthesis
   argues claim typing is the difference between a KB that earns trust over time and one that silently corrodes it. The
   question is whether Phase 2 should adopt TheKnowledge's strict enforcement — which means Workers producing
   exploratory drafts need an explicit `--draft` flag — or start with lint warnings and tighten later. Earlier is
   cheaper; retrofitting after thousands of pages are indexed is not.
2. **Single KB endpoint or one per subcorpus?** Six siblings enforce "one workspace = one MCP server instance" (llmwiki
   is explicit about this; synthadoc runs separate processes on separate ports per wiki root). Linus's `context/` spans
   papers, notes, threads, and books. A single KB endpoint means one MCP entry for everything; separate endpoints mean
   explicit agent scope but four entries in `.claude/settings.json`. This decision shapes the Phase 2 tool surface
   before the first line of KB code is written.
3. **Operations registry adoption.** Llmbase's `Operation` dataclass is a near-drop-in for the "one definition, three
   surfaces" tool registry Linus needs in Phase 2a. The alternative is a Linus-native abstraction designed from scratch
   to better fit the Maestro/Worker delegation model (e.g., an Operation carries an autonomy tier from SAFETY.md, not
   just a writes flag). Which direction: lift llmbase's proven contract, or design around Linus's specific constraints?
4. **Wiki-compilation layer or RAG-only?** Every sibling builds a compiled wiki over the raw corpus and argues it is
   more useful than RAG-on-raw-PDFs for compounding research knowledge. KnowledgeBase today is RAG-as-product. Is there
   appetite for an LLM-maintained markdown wiki layer on top of KnowledgeBase in Phase 3, or does the corpus stay
   query-only with provenance via content-hashed citations? The community's unanimous answer is "compile" but the
   community has not tried it on academic biochemistry/genomics papers with table-heavy data sections.
5. **G3 cross-check on provenance depth.** The wikiloom + TheKnowledge combination gives the best chunk-level provenance
   story in this group, but no single repo has implemented chunk-level hashing plus claim-type typing plus citation
   enforcement simultaneously. Once the G3 synthesis lands, check whether any G3 repo has achieved all three. If so,
   that repo displaces wikiloom/TheKnowledge as the primary provenance reference.

---

## Group 3 — LLM Wiki Agent-Driven Build Patterns

### agentic-wiki-builder

1. **Provenance model.** Is `git blame` provenance enough for KnowledgeBase, or does Phase 2 need explicit
   paper-id-to-claim back-references because PDFs get rewritten and reflowed across ingest runs?
2. **Branch-per-session as protocol.** The README's session pattern is essentially `agent/<uuid>/wiki-update`. Want to
   enshrine "every Worker-driven KB edit happens on its own branch and merges with `--no-ff`" in
   `docs/maestro-worker-protocol.md` as a hard rule, or keep it as one option among several?
3. **DuckDB+NetworkX as KB graph layer.** Is this the kind of prototype you want for Phase 2 link analysis, or are you
   already committed to a heavier graph store (DuckPGQ, Memgraph, Neo4j)?
4. **OpenCode in the harness picture.** Cline, claw-code-local, openclaw, Claude Code — and now, in principle, OpenCode.
   Is OpenCode worth its own evaluation slot, or has the harness shortlist already closed?
5. **Differentiator confidence.** I'm calling branch-per-session and the DuckDB linker the differentiators vs the other
   six LLM-Wiki siblings, but I haven't read those repos yet. Worth flagging whether any sibling already does the same
   so the comparison holds up.

### AgenticResearchWiki

1. **Page templates for `docs/`.** Want to lift the `Overview.md` template + `{{...}}` placeholder convention into
   Linus's `docs/` page-template kit, or keep `docs/` informal and reserve this only for per-project workspaces under
   `context/`?
2. **Install the two Skills.** `import-notes` and `project-doc-update` are user-level installable today
   (`cp -r skills/* ~/.claude/skills/`). Worth doing as a Phase 1 quality-of-life experiment on `context/notes/`, or
   defer until Memory Architecture lands?
3. **Differentiator check vs. siblings.** I distinguished AgenticResearchWiki from `llm-research-wiki` (research-of-LLMs
   vs. research-via-LLMs) and `agentic-wiki-builder` (agent-maintained vs. agent-constructed) on README evidence alone.
   Once the other two notes land, want me to revisit and tighten the contrast?
4. **Write-back loop and Memory Architecture.** The auto-write-back of task records into module Overviews is the closest
   published analogue to the journal -> index -> synthesis split the Memory Architecture spec is reaching for. Should
   the spec cite this repo as a worked example, or is the parallel coincidental?
5. **Per-experiment wikis.** Tencent's framing is one wiki per project. Linus has many concurrent experiments under
   `experiments/`. Does each experiment get a mini-wiki, or does this convention only kick in for multi-month efforts
   (Phase 6 fine-tuning, Phase 4 data-sovereignty datasets)?

### llm-research-wiki

1. **Page-type translation.** The six humanities page-types map to biochemistry roughly as paper / pathway-or-protein /
   author / contested-mechanism / synthesis / project. Is that the right mapping, or do you want a separate page-type
   for **method/protocol** (which Paulo treats as a lighter sibling of concept, but in wet-lab work is arguably the
   central artifact)?
2. **Cascade vs. embeddings.** The cluster→synthesis→`related:` cascade is an embedding-free way to keep query cost
   bounded. KnowledgeBase already has a Qdrant vector store. Run both in parallel with the cascade as the navigation
   surface and embeddings as fallback for unknown terms, or pick one?
3. **LINT autonomy.** Paulo's schema says "never auto-fix." For a 1000+ paper corpus, mechanical fixes
   (arXiv-vs-published dedup, author-name normalization, DOI canonicalization) are the bulk of the work. Want a
   `--apply` mode behind a confirmation, or strictly report-only like the original?
4. **Domain-context block.** Paulo's `CLAUDE.md` ends with a named list of his thinkers, concepts, and debates that the
   agent uses for cross-referencing. Do you want to author the equivalent for your research areas now, or have Linus
   extract it from the first 20–30 ingested papers and propose it back?
5. **Differentiator confidence.** I can distinguish llm-research-wiki from AgenticResearchWiki and atomic-knowledge on
   workflow framing (reading vs. training-ops vs. platform-neutral protocol). Is that distinction the one you'd draw, or
   do you read the three siblings differently after seeing them in practice?

### llm-wikidata

1. **Entity resolution as a Phase 2 KB tool.** Worth carving out a `linus.kb.entity_resolver` module that wraps the
   recall-then-resolve pattern (vector top-k + LLM pick-or-create with conservative/granular emission), independent of
   whatever store DEC-0026/27 land on? It's small enough to write from scratch in an afternoon.
2. **Distance threshold tuning.** This repo uses L2 ≤ 1.2 against `all-MiniLM-L6-v2` on Chinese tech-blog text. For
   Dan's biomedical corpus that threshold and embedder are both wrong. Is there appetite for a Phase 1/2 micro-bench
   that picks an embedder + threshold against a labelled set of "should-merge / should-not-merge" entity pairs from the
   paper corpus?
3. **Conservative/granular split vs single canonical entity.** The dual-emission idea trades one entity for up to two;
   in an RDF setting you'd model the granular as a sub-class or `skos:narrower` of the conservative. Is that the
   intended downstream shape, or do you want a single canonical entity per keyword with the granular treated as a
   label/alias?
4. **Differentiator confidence.** The README sells this as a knowledge-graph project, but the actual KG is a one-line
   dict and the visualisation is bipartite. The genuine differentiator vs the markdown-wiki siblings is the ChromaDB
   entity-recall step, full stop. Agreed, or do you see another piece worth lifting?

### atomic-knowledge

1. **Procedure as a first-class page type.** Atomic Knowledge promotes `procedure` to peer status with `concept` and
   `insight`. For your wet-lab/SOP corpus this seems obviously right, but it adds a page type that llm-research-wiki and
   AgenticResearchWiki do not have. Do you want the Phase 2 KB v1 schema to include `procedure` from day one, or start
   with concept/entity/insight and add procedure once it has corpus to back it?
2. **Retrieval-hint frontmatter (`search_anchors`, `key_entities`).** These are an embedding-free way to bias a small
   worker's read set. Worth standardizing across Linus KB pages as required frontmatter, or leave them optional like the
   upstream protocol does?
3. **Differentiator strength vs llm-research-wiki.** I'm calling "platform-neutral protocol stance" plus
   "procedures-as-first-class" plus "the MCP-wrapped `get_context` runtime" as the three differentiators vs the other
   six LLM-Wiki siblings. With the protocol-first framing being the loudest. Does that match what you noticed reading
   them, or is there a fourth angle (the candidate-lifecycle state machine? the `evals/` acceptance scripts?) that
   landed harder for you?
4. **Single-writer assumption.** The protocol presumes one agent maintaining one KB at a time. Phase 3 wants parallel
   workers. Is the right pattern per-worker scratch KBs that get merged into a canonical KB by Maestro, or one shared KB
   with file-level locking — and either way, is that a problem worth solving in Phase 2 or deferring to Phase 3?
5. **Autonomy-tier alignment.** AGENT.md says "ask before deletes, archives, bulk cleanup, large restructures."
   SAFETY.md is going to want a more graduated tier model. Do we want to write the mapping (Atomic Knowledge's prompt
   rules → Linus's autonomy tiers) as an explicit ADR, or treat the AK defaults as Tier-0 and graduate from there in
   Phase 7?

### beever-atlas

1. **Wiki-first-RAG for KnowledgeBase v2.** Beever's thesis is that retrieval should hit a continuously-distilled
   per-source wiki, not raw chunks. KnowledgeBase v1 is chunk-based RAG. Is "distil each paper into a structured wiki
   page at ingest, then retrieve against that" an explicit Phase 3 design move, or out of scope?
2. **Dual semantic + graph memory.** Beever runs Weaviate + Neo4j with a smart router that picks per question. The
   current Linus plan is Qdrant-only. Is a graph store (Neo4j, Memgraph, or even a SQLite-on-disk triple table) on the
   roadmap for relational queries over the paper corpus?
3. **Google ADK as an orchestration framework.** Beever's pipeline is expressed as ADK `SequentialAgent` /
   `ParallelAgent` rather than ad-hoc Python. Is ADK on the table for Linus's orchestration layer, or do we want to own
   the agent-graph abstraction ourselves to keep the dependency surface small?
4. **MCP tool surface.** Beever ships 16 tools through `fastmcp`. Is the Phase 2/3 plan for Linus's MCP surface
   similarly scoped (discovery, retrieval, graph traversal, long-running ops), or narrower for v1?
5. **Adapter abstraction for non-paper sources.** Beever's `BaseAdapter` + `NormalizedMessage` cleanly separates "where
   the bytes come from" from "what the pipeline does with them." Even ignoring chat, Dan has papers, threads, notes, and
   pics. Is there value in defining a similar `BaseSource` abstraction in KnowledgeBase before more source types
   accumulate, or is that premature?

### obsidian-llm-wiki-local

1. **Lift `structured_output.py` directly?** It is MIT, ~300 lines, no exotic dependencies, and solves a problem Linus
   will hit in Phase 1 the day a Qwen2.5 Worker is asked for JSON. Vendor it under `src/linus/inference/structured.py`
   with attribution, or rewrite from scratch?
2. **Compared to its Group 2/3 siblings (`AgenticResearchWiki` is hosted-API-first; `agentic-wiki-builder`,
   `llm-research-wiki`, `llm-wikidata`, `atomic-knowledge`, `beever-atlas` are mostly hosted-first too), this is the
   only one that treats Ollama as the default and OpenAI-compat as the fallback.** Does that local-first commitment plus
   the reject-and-explain loop make `obsidian-llm-wiki-local` the canonical Group-3 reference for Linus, with the others
   as contrast cases?
3. **Reject-and-explain as a Linus Skill primitive.** Imagine a Phase 7 Linus Skill where any Worker output can be
   rejected with a free-text critique that gets injected into the next invocation, capped at 5 attempts. Is that worth
   spec'ing now while the pattern is fresh, or premature?
4. **Obsidian as a Linus front-end, ever?** The `wiki/` output is plain markdown with `[[wikilinks]]` and YAML
   frontmatter — Obsidian-readable for free. If KnowledgeBase eventually exports synthesis pages in this shape, Dan gets
   graph view and backlinks at zero cost. Phase 4 candidate, or out of scope?
5. **The vault layout vs. the KnowledgeBase submodule.** `obsidian-llm-wiki-local`'s discipline (immutable `raw/`, all
   generated state under a single hidden directory, atomic writes, hand-edit detection) is the right pattern. Is
   KnowledgeBase already shaped this way, or worth a Phase 2 audit before deeper integration?

### g3-wiki-patterns synthesis (cross-cutting)

1. **Procedure type in Phase 2 KB schema.** The six-page-type schema from llm-research-wiki is the clearest starting
   point for KB v1, but the `procedure` type from atomic-knowledge may or may not belong in Phase 2 alongside the others
   — does Dan's paper corpus already have enough protocol-centric content (wet-lab methods sections, bioinformatics
   pipeline descriptions) to justify a `procedure` type from day one, or does that wait until the SOP-generation use
   case in Phase 2 actually produces procedure pages?
2. **LINT autonomy level.** The LINT workflow's "never auto-fix" default is right for humanistic scholarship; for a
   biochemistry corpus, DOI canonicalization and arXiv-vs-published deduplication are mechanical operations that should
   not require a human decision for every instance. What is the right autonomy level for the `linus kb lint --apply`
   mode — confirmation per fix, confirmation per fix-type, or auto-apply with a dry-run diff shown afterward?
3. **Vendoring vs. rewriting `structured_output.py`.** The `structured_output.py` lift from obsidian-llm-wiki-local is
   the clearest Phase 1 action item and the one with the most immediate payoff. The question is whether to vendor it
   directly (MIT-licensed, ~300 lines, attribution in the file header) or rewrite from scratch with the same three-tier
   logic. Vendoring is faster and keeps the test coverage; rewriting removes the Obsidian-vault framing from the
   variable names and removes any future surprise from upstream changes. Which does Dan prefer as the default practice
   for short MIT-licensed utilities?

---

## Group 4 — Agent Persistent Memory

# Group 4 Memory — Questions for Dan (Extract)

### agentmemory

1. **Hook taxonomy adoption.** The 13-hook lifecycle catalog (SessionStart through TaskCompleted) maps cleanly onto
   Garrison's four sub-requirements. Want a follow-up doc that ports this to a Linus-native list as part of the Phase 2
   episodic-memory spec, or keep that scoped to DEC-0029 work?
2. **MCP surface scope.** agentmemory exposes 51 memory tools; mem0 exposes ~5; Letta exposes ~12. Where on that
   spectrum should Linus's Layer-C MCP surface land in Phase 3 — minimal-and-composable, or comprehensive-and-curated?
3. **Lease / signal / checkpoint primitives.** These are real answers to Phase 3 parallel-Worker write coordination.
   Worth promoting from "implementation detail" to a named DEC alongside DEC-0029, or premature to formalize before the
   v0 substrate ships?
4. **iii-engine evaluation.** It's a real piece of engineering and not crazy as a Worker-orchestration runtime in its
   own right. Worth a 30-minute look before fully closing the door, or are you firm that Linus's runtime is Python
   orchestration over SQLite and iii is out of scope full stop?
5. **Headline-benchmark interpretation.** The 95.2% R@5 LongMemEval-S number is with embeddings on but LLM compression
   off (the no-op default). Should Linus replicate LongMemEval-S as part of the Phase 2 episodic-memory acceptance
   criteria, and if so against the same `all-MiniLM-L6-v2` baseline so numbers are comparable across group repos?

### anamnesis

1. **Strategic envelope columns on the DEC-0029 schema.** Anamnesis's `reasoning`, `authority`, `confidence`,
   `decay_condition`, `supersedes`, `depends_on` are mostly orthogonal to DEC-0030's two-segment record. Worth adding
   any of them to the `~/.linus/episodic.db` schema before Phase 2a starts writing migrations, or defer until use cases
   demand them?
2. **4D recall over SQLite.** The RRF-fused four-channel retrieval is implementable on sqlite-vec + FTS5 + a recency
   index + a small entity table without leaving SQLite. Is this a Phase 2 v1 target, a Phase 3 enhancement, or out of
   scope until a real retrieval-quality complaint surfaces?
3. **Authority caps for Worker-generated memories.** Linus's Worker fan-out will write mostly `inferred`-authority
   records. Anamnesis caps these at 1.0 (initial) / 4.0 (reweighted) to prevent agent noise drowning user-stated facts.
   Is that discipline the right default for Linus's episodic store, or does it need different calibration when the
   writes are mostly automated?
4. **`reflect` as a Linus primitive.** Anamnesis distinguishes `recall` (retrieval) from `reflect` (LLM-synthesised
   directives over mission + directives + top memories). DEC-0031's `memory_mode` router primitive is closer to
   `recall`. Worth adding a separate `reflect`-style operation for boot-time strategic briefing, or is the
   dispatch-layer prefix loader sufficient?
5. **Single sibling worth comparing in depth.** This group has eight implementations. Anamnesis sits at the heaviest
   substrate end; `agentmemory` is plausibly at the SQLite-native end most aligned with DEC-0029. Want me to flag this
   comparison explicitly in the `agentmemory` note when it's written, or do the eight notes plus a synthesis pass at the
   end?

### omega-memory

1. **Type taxonomy.** OMEGA has ~30 event types with weights from 0.05 (file_summary) to 3.0 (constraint, reminder).
   DEC-0029 leaves the type/weight question open. Do we want to seed Linus's episodic store with an OMEGA-style typed
   taxonomy from day one, or stay schema-flat and let types emerge from usage?
2. **sqlite-vec vs separate vector store.** OMEGA proves you can do 384-dim cosine search inside SQLite with no separate
   service. DEC-0029 doesn't pin a vector substrate. Adopt `sqlite-vec` as the v0 vector layer (matches the "one file,
   one process" aesthetic), or stand up Qdrant in Docker for the same workload?
3. **MCP timing.** OMEGA is MCP-first; Linus's ARCHITECTURE.md is OpenAI-compat-first with MCP as a Phase 3+ option (per
   cline.md and pmetal.md notes). Does OMEGA's existence — and the fact that Cursor / Claw Code / Windsurf / Cline /
   Codex all already speak MCP — pull MCP earlier in the roadmap?
4. **Hook collision risk.** OMEGA writes into `~/.claude/settings.json`, `~/.claude.json`, and `~/.claude/CLAUDE.md`.
   Linus will eventually want to write into the same files for its own session hooks. Should Linus's settings model
   reserve a namespaced block from the start to avoid collision with tools like OMEGA, or treat it as a Phase 5b
   problem?
5. **Cross-model handoff in practice.** OMEGA's "cross-model" claim reduces to "every client points its MCP config at
   the same SQLite file." That is real but modest. Is that the cross-model story Linus wants too (Linus is the one
   server, every harness points at it), or is there a more ambitious handoff — say, transcript-replay across model
   families — worth specifying for Phase 5+?

### engram

1. **Boundary call.** Engram's wiki-shaped "memory" is Layer D in Garrison's framing. Do you agree the Linus memory
   pillar should keep Layer C (episodic, DEC-0029 SQLite) and Layer D (semantic, KnowledgeBase) as fully separate
   substrates with separate write paths, and treat anything wiki-shaped as Layer D regardless of marketing?
2. **Lint as a Layer C verb.** Engram's `lint` finds contradictions, stale entries, orphans across the corpus. The
   episodic spec has consolidation (DEC-0039) but no integrity pass. Is a periodic LLM-mediated "audit your own episodic
   store for contradictions" worth a DEC slot, or premature?
3. **Write-time-synthesis vs. write-time-raw.** DEC-0029 stores raw turns + content hashes (write-time-raw). Engram does
   write-time-synthesis (LLM rewrites the corpus on every save). For the KB write side specifically — does Linus want
   ingestion to do engram-style synthesis into the KB, or stay raw-ingest with retrieval-time synthesis?
4. **Strict Pydantic on LLM tool outputs.** Engram validates every LLM response before acting. The Linus tool registry
   spec is silent on this. Should the orchestration layer make Pydantic-validated LLM outputs a default contract for any
   tool whose effect is mediated by the LLM's response?
5. **Differentiator confidence.** Within Group 4, engram is the clearest "wiki, not memory" outlier; the others
   (agentmemory, anamnesis, omega-memory, remember, prompt-vault, openaugi, memex) are presumably more episodic-shaped.
   Worth deferring final layer-C-substrate ADR refinements until the rest of the group is noted, in case one of them has
   a recall pattern that obsoletes part of DEC-0029?

### remember

1. **Persona vs trust-level scratchpad.** Remember's `Persona.md` is unbounded — every observation gets appended as an
   "evidence line" with no provenance. DEC-0030 mandates trust levels on scratchpad segments. Should Linus's Layer D
   persona inherit the same trust-level tagging, or is Persona-class data (style preferences, naming conventions) always
   trust=high by definition?
2. **Markdown vault as Layer C export.** SQLite is the source of truth for episodic memory (DEC-0029), but a read-only
   markdown-vault projection would let Dan browse memory in Obsidian and let openclaw see memory without speaking SQL.
   Worth a small export-tool spike in Phase 2b, or premature?
3. **Retroactive backfill from `~/.claude/projects/*.jsonl`.** Dan has months of Claude Code transcripts already.
   Remember's `extract.js` shows the walker works. Is backfilling Linus's Layer C from this corpus a Phase 2b
   deliverable, or a Phase 3 "knowledge & parallel agents" item?
4. **OpenClaw plugin co-existence.** If Dan installs Remember.md inside OpenClaw for personal Obsidian-vault curation,
   and Linus also writes memory through its own pathway, the two are independent stores with no sync. Is that acceptable
   separation, or does this argue for Linus owning the only memory write-path and Remember-the-tool being uninstalled
   once Phase 2a ships?
5. **Differentiation gap with `openaugi` / `memex`.** Remember's distinguishing move is the routing-rulebook ontology;
   `openaugi` and `memex` solve adjacent problems (graph extraction from vaults, capture-and-search). Are any of the
   three sibling repos worth installing in parallel for a week of personal use to test the Obsidian-vault pattern in
   practice, or is the survey enough?

### prompt-vault

1. **Group recategorisation.** prompt-vault is mis-shelved in Group 4 (cross-session persistent memory). It is a prompt
   library with one tangentially memory-adjacent piece (the Obsidian playbook). It probably belongs in a different
   group, perhaps with other "prompt patterns / agent-skill cookbooks" repos if any exist later, or it should be
   declassified out of the curated set entirely. Want to move it?
2. **Auto-ADR cron.** The `auto-document-agent.md` pattern (run `git diff main` on a branch, emit an ADR if the change
   is architectural) would pair well with this repo's own DEC-NNNN discipline. Worth a small Phase 1c experiment to bolt
   onto our existing `.claude/settings.json` hooks, or premature?
3. **Self-updating CLAUDE.md.** Would you want the weekly cron to keep CLAUDE.md honest against the repo, given how
   often we are amending it as the architecture decisions land? The risk is that an automated PR overwrites the careful
   prose style for a more mechanical bullet-style summary.
4. **Obsidian playbook relevance.** Do you maintain (or plan to maintain) an Obsidian vault for `context/notes/` or the
   paper corpus? If yes, the `vault_connectivity_agent.md` and `transcript_processing_agent.md` prompts are concretely
   useful; if no, the entire `obisidian-knowledge-graph/` subdirectory is dead weight for Linus's purposes.

### openaugi

1. **Schema lift, verbatim or extended?** OpenAugi's `(blocks, links)` schema covers DEC-0029's addressability/
   disambiguation/temporal/integrity needs cleanly. Adopt the column set verbatim and add `session_id`, `turn_id`,
   `parent_turn_id`, `segment`, `trust_level` as new columns on `blocks`, or rename to `episodes` + `episode_links` to
   make the ownership boundary obvious from schema names alone?
2. **sqlite-vec instead of Qdrant for v0.** OpenAugi runs FTS5 + sqlite-vec inside the same file as the source-of-truth
   table, which deletes a service from the architecture. Worth re-opening the v0 Qdrant decision in light of this, or is
   the Qdrant choice already locked for reasons orthogonal to substrate-count (e.g., HNSW perf, multi-tenant scoping)?
3. **OpenAugi vs memex split.** OpenAugi gives a typed graph an agent queries through tools; memex gives a governed
   markdown wiki an agent reads as files. These are complementary, not competitive — OpenAugi as Layer C substrate,
   memex as the cross-session "constitution" layer over project artifacts. Want this articulated as an ADR before Phase
   2a, or leave it implicit until both prove out?
4. **Context-block kind in the schema.** OpenAugi makes "compiled navigational metadata" a first-class block kind
   (`context_block:cluster`, hub summaries, concept pages). Linus's spec doesn't yet name an equivalent — should the
   Phase 2 schema reserve a `kind="context_block:*"` family up front, or is that premature before Phase 3 retrieval
   patterns crystallize?
5. **`get_context` as Linus's default retrieval verb.** OpenAugi collapses semantic+keyword+dedup+MMR+link-expansion
   into one tool with sensible defaults. Adopt that as the Linus Phase 3 retrieval entry point, or expose the five modes
   individually and let the Worker compose?

### memex

1. **Constitution-as-prompt vs schema-as-API.** Memex bets governance lives in markdown the agent reads each session;
   the memory-architecture spec bets governance lives in `linus.memory.*` API shape and SQLite constraints. These are
   not exclusive — Linus could ship both — but if we ship both, which is canonical when they disagree? My read is the
   API contract wins (Workers cannot opt out of column constraints) and the constitution becomes a Maestro-only prompt
   layer; confirm or push back.
2. **Cross-vendor enforcer for a local-only stack.** Memex's enforcer pattern depends on a _different vendor's_ model
   catching what the writer's model missed. Linus's local-first commitment means the enforcer would be a different
   _local_ model. Is that adversarial enough to do real work, or does the enforcer role need to escalate to hosted
   Claude (i.e., Maestro) on a periodic cadence to be trustworthy?
3. **Lint-as-CI for the memory store.** Memex runs `memex-lint.sh` manually. Linus could run the equivalent as a git
   pre-commit hook on the memory-store directory or as a Phase 2a orchestration-layer health check. Which is the right
   tier — pre-commit (prevents bad writes) or background sweep (catches drift after the fact)?
4. **Category vocabulary.** Memex enforces a six-value enum. The Linus equivalent would be the `tags` field in DEC-0033
   — but is a controlled vocabulary an asset (lint can verify it) or a liability (you discover the seventh category
   mid-Phase-3 and have to migrate)? Memex's answer is enum-with-lint; Dan's instinct?
5. **`openaugi` vs `memex` vs `remember` as the markdown/entity reference.** All three live in this group — write-side
   discipline, read-side viewer, SDK-enforced typing. Worth a comparison artifact in `docs/syntheses/` once all eight
   repo-notes are in, or is the memory-synthesis already carrying that load?

### g4-memory synthesis (cross-cutting)

1. **Schema lift: verbatim or extended?** The openaugi `(blocks, links)` schema satisfies DEC-0029's requirements with
   almost no friction. The decision is whether to adopt the column names verbatim and add Linus-specific columns, or to
   rename to `(episodes, episode_links)` to signal ownership boundary from the first migration. Both are defensible; the
   choice should be made before Phase 2a opens the first migration file.

2. **sqlite-vec vs Qdrant for v0.** Omega-memory and openaugi both prove that 384-dim cosine search inside the same
   SQLite file satisfies Phase 2 recall requirements with no separate service. DEC-0029 does not pin a vector substrate.
   The Algorithm says to delete the Qdrant service from v0 scope and add it back if sqlite-vec proves insufficient. Is
   the Qdrant choice already locked for reasons orthogonal to substrate count (HNSW performance, multi-tenant scoping),
   or is this an active deletion candidate?

3. **Does openaugi's schema get lifted verbatim?** This is the Phase 2 scoping question this cluster surfaces that the
   memory-synthesis does not address. The two-table schema is close enough to deployable that the question is not
   "design or reference?" but "lift or study?" The difference is whether the DEC-0029 migration file starts from the
   openaugi DDL or from a clean-room design informed by it. Lifting saves time and inherits battle-tested column
   choices; clean-room design preserves full alignment with Linus's naming conventions and avoids inheriting
   alpha-software debt. Given the spec's DEC-0029 column set is already specified
   (`session_id, turn_id, parent_turn_id, timestamp, role, segment, content_hash, content, trust_level, tags`), the
   clean-room path diverges from openaugi primarily at the `blocks` vs `episodes` naming level. This is worth resolving
   explicitly before Phase 2a implementation begins.

4. **Authority caps for Worker-generated memories.** Anamnesis calibrates AI-derived records at weight 1.0 (initial),
   earning up to 4.0 via reweight cycles, to prevent agent noise from drowning user-stated facts in retrieval.
   DEC-0029's `trust_level` field carries the same concept at the binary level. Should Linus's episodic retrieval apply
   an anamnesis-style continuous weight that Worker-generated records must earn, or is the binary trust-level field
   sufficient for Phase 2?

5. **Cross-vendor enforcer with local-only models.** Memex's enforcer depends on a genuinely different vendor catching
   what the writer missed. For Linus, the closest analogue is a different local model family auditing the episodic
   store. Whether that is adversarially strong enough to catch real inconsistencies is untested. Should the enforcer
   role escalate to hosted Claude (Maestro) on a periodic cadence, or is a local-model enforcer the right design even if
   it is weaker?

---

## Group 5 — Knowledge-Graph & Network-Analysis Tooling

### infranodus

1. **AGPL avoidance.** The cognitive-variability _idea_ is unencumbered (it's in a published paper); the _code_ is AGPL.
   Confirm the policy is "re-implement from the paper, never copy" — and that this also applies to the Python port on
   GitLab, which is MIT but derives from AGPL upstream.
2. **Cognitive variability as a first-class KB metric.** Worth surfacing biased/focused/diversified/dispersed as a
   first-class quality signal on KnowledgeBase contexts in Phase 3 (e.g., "this paper cluster is dispersed — bridge
   it"), or is that a Phase 7 skills-layer concern after the substrate is solid?
3. **Statement-as-hyperedge in the data model.** Linus's memory architecture has episodic events that are naturally
   hyperedges over multiple concepts. Adopt InfraNodus's `:Statement`/`:OF`/`:IN` pattern explicitly in the
   property-graph half of DEC-0027, or stick with binary edges + reified statement nodes only when needed?
4. **Relationship to `infranodus-skills`.** That sibling repo assumes a hosted MCP server. If Linus re-implements the
   engine locally, do we also stand up an MCP server façade so the same skill prompts work unchanged against local data,
   or is that scope creep before Phase 3?
5. **Neo4j.** DEC-0026/27 currently does not pick Neo4j. Does anything in InfraNodus's Cypher make a strong enough case
   to revisit that, or is the substrate decision settled and Cypher is just a reading exercise?

### infranodus-skills

1. **Skills format as the Phase 7 contract.** Both this repo and `OmegaWiki` use the Anthropic SKILL.md format with
   frontmatter `name`/`description`/optional `allowed-tools`. Should Linus commit to that exact format for its Phase 7
   domain skills, or define a Linus-specific superset (e.g., adding hardware/budget hints, mandatory smoke-test stubs)?
2. **Cognitive-variability framework — useful or noise?** The four-state model (biased/focused/diversified/dispersed)
   maps interestingly onto Maestro/Worker review loops: a Worker stuck in BIASED could be nudged toward DIVERSIFIED by
   loading `critical-perspective`. Worth a Phase 1e experiment, or filed under "interesting but not load-bearing"?
3. **Self-hostable text-network analysis.** If we want the MCP-dependent skills to work standalone, we'd need to
   reimplement InfraNodus's modularity/centrality/gap-detection over our own KB graph (Phase 2 DEC-0026/27 surface).
   That's a meaningful build. Worth scoping into Phase 3, or accept that this repo stays study-only?
4. **OmegaWiki comparison.** I could not find an `OmegaWiki.md` repo note in `docs/repo-notes/` (only the twelve listed
   there) — was it intended to be authored separately, or is the comparison expected to live here in absentia? If the
   former, the head-to-head should probably be revisited once both notes exist.
5. **`llm-wiki` skill vs Karpathy's autoresearch.** The `llm-wiki` skill operationalizes Karpathy's LLM Wiki proposal as
   a setup workflow, which is a near-cousin of the autoresearch loop already cloned in `repos/autoresearch/`. Is there
   appetite to consolidate these into a single Linus "build a wiki from your sources" skill backed by KnowledgeBase, or
   do they stay separate study artifacts?

### py3plex

1. **Does Linus's KB actually become multilayer?** The DEC-0026/27 dual-substrate decision is RDF + property graph, not
   multilayer-property graph. If the property graph stays single-layer (one node-type universe, edges typed by
   relation), py3plex is overkill and plain networkx + a custom query helper is the right size. If layers (paper /
   concept / claim / author / source) are first-class, py3plex is the obvious substrate. Which way are you leaning
   before Phase 2 starts?
2. **DSL design ownership.** py3plex's DSL v2 is genuinely well-designed, but importing it means Linus's graph query
   surface is shaped by an upstream library's roadmap. Do we want to fork the DSL design into a Linus-native query
   builder (lighter, KB-shaped, fewer concepts), or accept the dependency to avoid rebuilding what works?
3. **Uncertainty quantification in KB retrieval.** py3plex makes confidence intervals on centrality/community a one-line
   `.uq(...)` clause. The synthesis-landscape work emphasizes epistemic standards and claim typing; UQ on graph-derived
   rankings is a natural extension. Is this a Phase 3 priority, or a Phase 4+ refinement?
4. **Formal verification adoption.** CrossHair + icontract + z3 is a serious testing posture. Adopting even just
   icontract `@require`/`@ensure` for Linus's tool registry and sandbox boundary code would be cheap and high-value.
   Want to add this as a Known Library / Engineering Convention now, or wait for a concrete pain point?
5. **MCP-as-tool-substrate, again.** py3plex ships an MCP server alongside pmetal's, openclaw's, and Cline's MCP
   support. The Phase 3 question — "is MCP the tool-registration substrate?" — keeps recurring. Three serious
   local-AI-adjacent projects in this repo collection have already answered yes. Time to make the call?

### keppi

1. **KB graph schema parity.** Keppi's edge types are vault-author-shaped (`wikilink`, `embed`, `related_to`,
   `tag_overlap`, `folder_proximity`). The KnowledgeBase corpus is paper-shaped (`cites`, `cited_by`, `co_author`,
   `shared_topic`, `shared_doi`). Should we define the Phase 2 KB edge schema explicitly before borrowing Keppi's
   weighting scheme, or pick weights empirically once the graph is built?
2. **Hybrid retrieval order.** Keppi's MCP server hard-codes `semantic_search → keyword_search → graph traversal`. For
   paper retrieval the natural order may invert (citation-graph expansion from a known paper, then semantic re-rank). Do
   we want a single canonical retrieval recipe in Phase 3, or pluggable strategies per task type?
3. **`hyalo` vs `keppi` for vault interop.** If Linus eventually mounts your personal Obsidian vault as a corpus, do we
   pick one of these two, or compose them — keppi for traversal, hyalo for authoring/synthesis?
4. **MCP-as-tool-surface revisited.** Keppi, pmetal, and Cline all ship MCP servers. Phase 3's tool-registry decision is
   becoming load-bearing; is now the time for an ADR on "MCP as Linus's tool surface vs. native registry," or does it
   stay open until we have a working KB tool to register?
5. **Context-pack as a Linus primitive.** `context_pack(topic, token_budget) → reading set` is exactly the shape of a
   Linus tool a Worker would call before starting a task. Want to spec this as a Phase 2a/3 primitive explicitly, or
   wait until a concrete Worker workflow demands it?

### hyalo

1. **Vault location.** Does Linus's note vault live at `context/notes/` (gitignored, personal), as a new top-level
   `vault/` (tracked but Dan-owned), or inside `modules/KnowledgeBase/` next to the paper corpus? Hyalo's `.hyalo.toml`
   has to point somewhere and the schema lives next to it.
2. **hyalo vs keppi bake-off.** Want a 30-minute Phase-1 spike that runs the same five operations (find by tag, bulk set
   status, rename + link rewrite, lint with schema, summary) on a sample vault under both tools and writes the verdict
   as an ADR in `docs/adr/`?
3. **Schema design.** The pmetal-style `[schema.types.iteration]` block is appealing for Linus's `experiments/` and
   `docs/adr/` directories. Adopt the iteration-file convention (`iter-NN-slug.md`,
   `planned → in-progress → completed → superseded`) for our work, or keep our looser status quo?
4. **Claude Code integration scope.** `hyalo init --claude` writes a vault-scoped rule that overrides Maestro's default
   Read/Edit behavior. Comfortable with that landing in `.claude/` for `context/notes/**`, or do you want the override
   scoped tighter?
5. **Phase 3 graph producer.** When the KB graph layer comes online, do we use hyalo's `link_graph` output as the seed
   (cheap, already computed) and add `py3plex`/`infranodus` analysis on top, or keep the graph layer hyalo-independent
   so the vault tooling stays swappable?

### g5-graph-tools synthesis (cross-cutting)

1. **Vault location.** Hyalo's `.hyalo.toml` must point at a concrete path. The three candidates — `context/notes/`
   (gitignored, personal), a new top-level `vault/` (tracked, Dan-owned), or inside `modules/KnowledgeBase/` next to the
   paper corpus — each have different implications for what gets indexed, what is gitignored, and how KnowledgeBase's
   own submodule governance interacts with hyalo's schema. The simplest starting point is `context/notes/` with a
   `.hyalo.toml` that stays gitignored alongside it.
2. **Hyalo vs. keppi bake-off.** The repo notes recommend a 30-minute Phase 1 spike (find by tag, bulk set status,
   rename + link rewrite, lint with schema, summary) run under both tools on the same sample vault. That spike would
   close the "confirm which operations keppi actually supports" question that the infra note leaves open, and produce an
   ADR verdict on how the two tools divide responsibility rather than leaving it implicit.
3. **Paper-corpus edge weights for blast radius.** Keppi's default weights (wikilink=1.0, embed=1.5, related_to=2.0)
   were tuned for a Zettelkasten. KnowledgeBase's edges are paper-shaped. What is the right relative weight for a
   citation edge vs. a co-authorship edge vs. a shared-topic edge? The answer should come from a smoke test on a known
   retrieval case (given paper A, what should context-pack return?), not from a priori intuition.
4. **AGPL re-implementation scope.** The cognitive-variability metric from infranodus is unencumbered as an idea (WWW'19
   paper); the code is AGPL. The Python port on GitLab (`DiscourseDiversity`) is MIT-licensed but derives from the same
   codebase. Confirm the policy — "re-implement from the paper, never copy, and verify MIT ports are independently clean
   before borrowing" — and document it as a DECISIONS.md entry rather than leaving it implicit in the repo note.
5. **MCP as tool-registration substrate.** Four projects in the repo collection (pmetal, Cline, keppi, py3plex) now ship
   MCP servers as their primary tool-surface. Group 5 adds enough evidence that this question should be scheduled for a
   dedicated ADR session: is MCP the tool-registration substrate for Linus's Phase 3 KB tools, or does Linus build a
   native registry? The infranodus-skills SaaS-dependency problem (MCP-dependent skills that require a paid API key) is
   also an existence proof that MCP adoption does not automatically mean local-first — the ADR should include a
   "local-only MCP policy" as a design constraint.
6. **InfraNodus self-hosting.** If Linus reaches Phase 3 with a working text-network-analysis layer over KnowledgeBase,
   the MCP-dependent skills in infranodus-skills become interesting again if that layer can expose an
   InfraNodus-compatible API. Is that worth scoping as a Phase 3 stretch goal, or does it stay filed under "interesting
   but not load-bearing until someone actually misses it"?

---

## Group 6 — MCP Servers & Code/Document Context Tools

# Group 6 — MCP Servers & Code/Document Context Tools

### Questions for Dan (Extracted)

### fastmcp

1. **Stdio vs streamable-http for Phase 2.** Local-only Maestro/Worker calls are fine over stdio, but the moment a
   second harness wants the same KB tools (Cline + Claude Code + openclaw simultaneously), HTTP becomes simpler than
   spawning N stdio children. Default to `streamable-http` on `localhost:<port>` from day one, or start stdio and
   migrate?
2. **Tool granularity.** FastMCP encourages many small typed tools. KnowledgeBase has natural verbs (semantic_search,
   hybrid_search, get_paper, walk_citations, run_cypher) — does each become its own `@mcp.tool`, or does Linus expose
   one parameterized `kb_query` and dispatch internally? The first is more legible to harnesses; the second is closer to
   how DEC-0029 frames the registry.
3. **Auth posture.** Phase 2 is single-user localhost; auth is unneeded. Phase 5b openclaw might expose Linus on the LAN
   for Dan's iPad. Plan to enable FastMCP's JWT/OAuth subsystem then, or stay localhost-only and tunnel via SSH?
4. **Proxy/composition.** If pmetal-mcp's 45 tools are useful, `FastMCP.as_proxy(pmetal_server)` lets Linus re-expose
   them under its own endpoint with Linus middleware applied. Worth pursuing in Phase 3, or keep pmetal-mcp as a
   separate endpoint Maestro picks explicitly?
5. **Dependency weight.** FastMCP pulls ~20 runtime deps including `authlib`, `opentelemetry`, `griffelib`,
   `watchfiles`. Acceptable for the Linus env, or do we want a thinner alternative (the bare `mcp` SDK) for a
   minimal-deps profile in case of shipping a packaged Linus binary later?

### ontomics

1. **MCP-as-substrate decision timing.** Cline, openclaw, pmetal, and ontomics all speak MCP. Adopting ontomics in Phase
   2a effectively forces Linus to stand up an MCP client/registry earlier than ROADMAP currently has it. Do we want to
   pull that decision forward to Phase 2a explicitly, or run ontomics out-of-band (registered per-front-end) until Phase
   3?
2. **Benchmark on a real Dan project.** The README's 20× claim is on voxelmorph and ScribblePrompt — clean ML repos.
   Should the Phase 1 benchmark suite include an "ontomics on KnowledgeBase" test (Python, mixed domain) to confirm the
   ratio holds on something messier?
3. **Behavioral clustering on bioinformatics code.** CodeRankEmbed was trained on general code; how well does it cluster
   numerical/bioinformatics function bodies (lots of array math, similar shapes, different intents)? Worth a quick
   ablation before committing.
4. **Sibling comparison gap.** This note can't yet differentiate ontomics from codesight beyond the README pitch. Do you
   want me to write the codesight note next so the head-to-head decision is made on facts rather than marketing?
5. **Domain-pack export as a Linus artifact.** ontomics's YAML `export_domain_pack` could be checked into Dan's projects
   as a portable convention spec. Is that a workflow you'd actually use, or is it a "neat feature, never opened" risk?

### codesight

1. **Per-repo vs global install.** `npx codesight` resolves the package every invocation (the README warns about Codex
   hitting a 30s timeout because of this). Globally installing inside the linus conda env is faster but means a Node
   package lives in our env. Acceptable, or do we wait until there's a second reason to take that dependency?
2. **Wiki artifacts in git.** codesight's value compounds when `.codesight/wiki/` is committed and consulted at session
   start (Karpathy-style). Are we willing to commit AI-context artifacts into the Linus repo, or treat them as
   per-session ephemera?
3. **Codesight on non-web Python.** The detectors are tuned for web frameworks (routes, ORMs, components). On a pure
   numerical/scientific Python repo with no routes and no ORM, the output may be mostly the dependency graph and env
   vars. Is that still worth the tool slot, or should we bake a science-flavored variant later?
4. **MCP tool registry shape.** codesight, ontomics, fastmcp, qmd, vectorless, WeKnora are all candidates for the Phase
   2/3 tool surface. Do we want to settle the MCP-as-registry question (raised in cline.md, openclaw, pmetal-mcp) before
   adding any of them, or pick one as a forcing function?
5. **Differentiator I could not pin down.** I can distinguish codesight from ontomics confidently, but the line between
   codesight's wiki-mode and a vectorless/WeKnora retrieval pass is fuzzy when the source is markdown rather than code.
   Worth comparing those three explicitly in a follow-up note before Phase 3 retrieval design lands.

### qmd

1. **Is RRF+rerank the right Phase 3 fusion target for KnowledgeBase?** qmd's blend of RRF, original-query ×2 weight,
   top-rank bonus, and position-aware rerank merging is more elaborate than "RRF k=60." Worth porting wholesale, or
   start with vanilla RRF and earn complexity by measurement?
2. **Phase 1f baseline scope.** Does running qmd against a Markdown slice of the corpus (notes/, threads/, maybe paper
   abstracts) and comparing top-k against KnowledgeBase's retriever count as a useful Phase 1f data point, or is the
   Markdown-only constraint too narrow to be informative?
3. **Three inference stacks on one box.** Ollama, pmetal (pending Phase 1b), and qmd's node-llama-cpp would each load
   their own Metal context. If qmd is adopted even as a study tool, do we cap it to short-lived runs, or accept a
   resident MCP daemon as a third concurrent inference process?
4. **Query-expansion fine-tune.** Tobi shipped a 1.7B Qwen3 fine-tuned for query expansion. This is a tractable Phase 6
   exercise on Dan's corpus — useful as a first LoRA target, or distract from harder scientific-domain fine-tunes?
5. **Differentiator vs siblings (vectorless, WeKnora).** I called qmd "narrowest of the three." Useful framing, or would
   Dan rather see them ranked on a different axis (Apple-Silicon-native, Markdown-fit, MCP-readiness)?

### vectorless

1. **Bake-off scope.** Should the Vectorless evaluation use a hosted model (gpt-4o-mini, Claude Haiku) for an honest
   quality ceiling, a local Ollama worker for an honest Linus-on-MacBook ceiling, or both? The two answers could be very
   different and shape whether this pattern is "worker territory" at all.
2. **Crossing 3 implications.** Vectorless's existence is an argument that a Linus KB built _purely_ on graph +
   shell-command tools, with no vectors, might be viable. Crossing 3 currently assumes vectors. Do we want to defend
   that assumption with a measurement, or is the hybrid path (vectors for recall, navigation for precision) already
   settled?
3. **Tool surface as MCP.** The shell-command vocabulary (`ls`/`cd`/`cat`/`grep`/`concepts`/`chain`) is the most
   concrete reusable artifact. Is this a Phase 2 KB-tool-registry candidate, or does it wait for Phase 3 hybrid
   retrieval design?
4. **Failure-mode tolerance.** Vectorless's "model fails, we fail" stance is the opposite of Linus's preference for
   graceful degradation in worker pipelines. If we adopt the navigation pattern, do we want to keep the strict stance or
   add KnowledgeBase-style fallbacks (BM25 backstop when the agent gives up)?
5. **engram comparison.** Is there a planned engram experiment where we can run head-to-head with Vectorless on the same
   documents and same questions, so the "compile-don't-retrieve" thesis gets a real measurement instead of a vibe?

### WeKnora

1. **Provider abstraction now or later.** WeKnora's strongest reusable idea is the unified LLM provider interface — same
   shape regardless of OpenAI vs Ollama vs Hunyuan. Does Linus want to design that abstraction in Phase 2a (when there
   are only Ollama and pmetal candidates), or wait until a third backend forces it?
2. **Per-KB indexing strategy toggle.** Should KnowledgeBase v1 commit to one retrieval mode (e.g., dense-only) for
   simplicity, or design from day one for hybrid + GraphRAG with per-corpus toggles like WeKnora does?
3. **Parser-as-sidecar.** The `docreader` Python gRPC sidecar pattern keeps the Go core clean of every PDF/OCR
   dependency. Worth considering for KnowledgeBase ingestion if the dependency surface grows, or premature for a Python
   monolith?
4. **Langfuse for agent tracing.** When Linus gets to multi-step ReAct loops in Phase 3, do you want LLM-native
   observability (Langfuse, Phoenix, Helicone) in scope, or is OpenTelemetry + structured logs sufficient?
5. **Differentiation gap.** Is there any meaningful overlap between WeKnora's Wiki Mode (auto-distill documents into
   interlinked markdown + knowledge graph) and the KnowledgeBase submodule's own roadmap, or are these solving different
   problems for different users?

### g6-mcp-tools synthesis (cross-cutting)

1. **Stdio or streamable-http from Phase 2 launch?** The fastmcp note frames this as a question; this synthesis
   recommends streamable-http on localhost from day one. The reasoning: Cline and Claude Code will want simultaneous
   access to the same KB tool surface, and spawning N stdio children for N clients is more fragile than one HTTP server.
   Is there a reason to start with stdio instead — startup latency, process isolation, dependency simplicity?
2. **Ontomics benchmarking scope.** The 20× token reduction claim is on voxelmorph and ScribblePrompt — clean ML repos.
   Dan's scientific Python (numerical pipelines, bioinformatics, no web framework routes) is a messier target. Should
   the Phase 1f benchmark suite include an ontomics run against the KnowledgeBase submodule to confirm the ratio holds?
   And should CodeRankEmbed's clustering of bioinformatics function bodies (lots of array math, similar shapes,
   different intents) get an explicit ablation before ontomics is registered as a default Worker tool?
3. **Which comes first: MCP ADR or Phase 3 design?** The total-landscape observation is that MCP adoption is now
   overdetermined, but the ADR formalizing the commitment has not been written. Should this happen at the start of Phase
   2a planning — before any tool code is written — so that the commit is explicit and the policy decisions are made once
   rather than implied by implementation choices?
4. **Vectorless bake-off model selection.** The vectorless smoke test needs an LLM in the loop. Against a hosted model
   (Claude Haiku, gpt-4o-mini) the quality ceiling is honest but expensive; against Ollama/qwen2.5-coder:14b the ceiling
   is the realistic Linus-on-MacBook constraint. The two answers could diverge significantly. Which framing is more
   useful for the Phase 3 decision: "does this pattern work in principle?" (hosted) or "does this pattern work on my
   hardware?" (local)?
5. **WeKnora's per-KB indexing toggle — relevant for KnowledgeBase v1?** WeKnora lets each knowledge base instance
   independently choose its retrieval mode (dense-only, hybrid, GraphRAG, Wiki). KnowledgeBase v1 currently has no such
   toggle. Should the Phase 2 KB design commit to one retrieval mode for simplicity, or build the toggle mechanism from
   the start? The Algorithm says delete requirements; but adding the toggle later if multiple retrieval modes coexist is
   harder than building it in.

---

## Group 7 — Agent Harnesses, Orchestration, Model Routing

# Group 7 Questions for Dan — Extracted

### claude-squad

1. **Phase 1f verdict shape.** The spec frames this as Task-Master vs claude-squad vs custom vs pmetal-MCP. After
   reading both, my read is they solve different layers (decomposition vs runtime isolation). Want the Phase 1f ADR to
   recommend using both as off-the-shelf today, with Linus's custom layer scoped to "the glue between them," or hold the
   line that Linus owns orchestration end-to-end and they remain study-only?
2. **Worktree-per-Worker as the canonical primitive.** Adopting `~/.linus/worktrees/<branch>_<nanoseconds>` matches
   BRANCHING.md cleanly but means every Worker run touches disk and consumes inodes. For short-lived stateless Workers
   (a one-shot test-generation call) this is overkill. Two-tier model — durable worktrees for `agent/<task-id>`
   branches, in-memory `git diff`-only for one-shots — or always-worktree for uniformity?
3. **tmux dependency.** Claude-squad assumes tmux. If Linus inherits this, openclaw / native-app front-ends inherit it
   too. Acceptable now (Dan uses tmux daily) or a smell to design out via `creack/pty` directly?
4. **AutoYes meets SAFETY.md.** Claude-squad's `-y` is "press Enter on every prompt." Linus's autonomy graduation
   expects `-y` to mean "press Enter on prompts that match the current tier's allowlist, deny otherwise." Should the
   Phase 1f ADR explicitly call out that any adopted runner must hand off prompt-arbitration to Linus's policy engine?
5. **Screen-scraping vs structured I/O.** Claude-squad detects "agent waiting" by reading the tmux pane. Local Workers
   speaking OpenAI-compat give Linus structured turn boundaries for free. Do we want the orchestration layer to support
   both modalities (spawned-CLI + API-Worker), or commit to API-Worker as the only Linus-native pattern and treat
   CLI-spawning as a third-party concern?

### claude-task-master

1. **Phase 1f framing.** The brief treats claude-squad and claude-task-master as competing candidates, but they target
   different stages (decompose vs. parallel-execute). Is the Phase 1f deliverable better written as "adopt both
   patterns, neither product," or do you want a single winner declared?
2. **Three model roles, or more?** Taskmaster pins three: main / research / fallback. Linus's worker layer plausibly
   needs at least four — main (Qwen2.5-Coder), research (an external API or Perplexity for facts), fallback, and a
   cheap/fast triage model (Mistral-7B or Bonsai). Codify three roles or design for N from the start?
3. **Task-state location.** Taskmaster centralizes everything in `.taskmaster/`. Should Linus's PRD-to-tasks skill
   output to `experiments/<task-id>/`, to a SQLite-backed session store (per ARCHITECTURE.md), or to git-tracked JSON
   next to the spec — and which of those plays best with the agent-branch workflow in BRANCHING.md?
4. **MCP tool count discipline.** Taskmaster's `core` tier is 7 tools at ~5k tokens; their default of 36 already costs
   ~21k tokens. For Linus's eventual MCP surface, do we adopt a hard cap (say, 10 tools per worker session) and force
   composition, or accept higher token cost in exchange for breadth?
5. **Differentiator gap.** I could not identify a meaningful technical differentiator that argues for Taskmaster _over_
   reimplementing the pattern in Linus — every reusable idea (schema, three roles, complexity-then-expand) is small
   enough to lift in a day. Is there a Taskmaster feature you specifically want that I should re-evaluate before closing
   the ADR?

### codebuff

1. **Eval claim scrutiny.** The "61% vs 53%" headline rests on Codebuff's own harness — `evals/runners/claude.ts` runs
   Claude Code via Anthropic's API with bypass-permissions, prompted by a Codebuff-authored Prompting Agent, judged by
   three Gemini 2.5 Pro instances. Each of those is a knob that could tilt the result. Worth replicating before citing?
   If so, that's a Phase 1b-ish exercise that needs OpenRouter and Anthropic API budget.
2. **Agent-definition shape.** Codebuff's `SecretAgentDefinition` (model, prompt, toolNames, spawnableAgents,
   handleSteps generator, outputMode) is a concrete TypeScript schema. Linus has not committed to a worker-definition
   schema yet. Adopt this shape directly (in Python/Pydantic), translate to a YAML-first format, or design fresh?
3. **Inline context-pruner pattern.** Buffy spawns `context-pruner` _every step_ via `spawn_agent_inline`. That is one
   way to keep long sessions tractable; it costs a model call per turn. Worth evaluating against the alternatives
   (LLMLingua, summarization checkpoints, SCoT/Letta-style memory) for Linus's Phase 3?
4. **OpenRouter as model bus.** Codebuff routes every agent through OpenRouter slugs; this is how it offers per-agent
   model selection so cheaply. Linus's stance is local-first, but Phase 1's Maestro/Worker loop already uses Anthropic
   for Maestro. Is OpenRouter a candidate for the "non-Maestro paid models" tier (i.e. cheap planners), or stays out?
5. **Differentiator vs claude-squad.** claude-squad runs N independent Claude Code instances side-by-side; Codebuff
   decomposes one request internally. These are orthogonal patterns and Linus might want both — many Workers each
   internally decomposed. Worth making this distinction explicit in ARCHITECTURE.md when the Worker catalog is drafted?

### workgraph

1. **Graph vs. list as the orchestration substrate.** workgraph commits to a DAG with `--after` edges, cycles, and a
   `restart_on_failure` policy. claude-task-master commits to an ordered list emitted from a PRD. Which fits the kinds
   of work you actually delegate to Workers — bench sweeps and ablations (graph-shaped, dependencies real) or per-paper
   synthesis batches (list-shaped, embarrassingly parallel)?
2. **JSONL store at the orchestration layer.** ARCHITECTURE.md mentions a session store and an audit log without picking
   a format. Adopting workgraph's `.workgraph/graph.jsonl` shape (append-only, one record per event, human-readable) for
   Linus's session store would be cheap and git-friendly. Or do you want SQLite from day one for query power?
3. **Agency / auto-evaluate as Linus's verification layer.** workgraph's `## Validation` convention plus a haiku-pinned
   evaluator is a lightweight version of what SAFETY.md's autonomy tier graduation needs. Worth lifting the convention
   into Linus's Maestro/Worker protocol now, or keep verification human-in-the-loop until Phase 7?
4. **The macOS gap.** Tree-kill via `/proc` doesn't exist on M1. If Linus borrows the heartbeat pattern, we need a
   `kqueue`-based or `pgrep -P`-based equivalent. Worth writing as a small Phase 1f experiment, or accept that on macOS
   a stuck Worker is a `wg kill --force` command rather than an automatic recovery?
5. **Composing workgraph with claude-task-master.** A plausible Group-7 verdict is "task-master plans, workgraph
   executes" — task-master emits the DAG, workgraph runs it. Is that interesting enough to prototype in Phase 3, or
   should Linus own both halves natively in Python?

### openrouter-skills

1. **OpenRouter as a sanctioned escape hatch?** The "no paid APIs required" rule is about _required_, not _forbidden_.
   Is there a tier of Linus tasks where reaching out to OpenRouter for a model size local hardware can't host (Llama 4
   Maverick, Claude Opus 4.7 itself via the OpenRouter route) is acceptable, or is OpenRouter strictly off the table
   even as opt-in?
2. **Open Responses adoption.** Linus's Phase 2a says "OpenAI-compatible endpoint." Is the actual target the OpenAI Chat
   Completions shape (legacy, what Ollama serves), the OpenAI Responses shape (newer, stateful), or the Open Responses
   spec documented in this repo? The three are not interchangeable and the choice locks in client compatibility.
3. **Skills bundle for Linus itself.** OmegaWiki (24), infranodus-skills (15), AgenticResearchWiki (2),
   openrouter-skills (8) — there's a clear pattern of vendors shipping Skills bundles. Should Linus ship its own Skills
   bundle (`linus-skills`?) for KnowledgeBase queries, sandbox operations, and pmetal commands once Phase 7 lands, or is
   that premature given Anthropic's Skills format may evolve?
4. **Server-tools vs client-tools partition.** OpenRouter's `openrouter:web_search` etc. is executed remotely by them.
   When Linus exposes a tool registry, which surface does it expose tools through — MCP (which Cline and openclaw
   consume), Skills (which Claude Code and many editors consume), or both? They're not equivalent and double-publishing
   has maintenance cost.
5. **Differentiator confidence.** The README only lists 7 skills but the `skills/` tree contains 8 (`openrouter-video`
   is undocumented). Worth flagging upstream, or just note and move on?

### python-sdk

1. **Vocabulary lift, yes or no?** Adopting OpenRouter's `provider` field shape verbatim (with `order`,
   `allow_fallbacks`, `sort`, `only`/`ignore`) means any client already speaking OpenRouter — including Cline and
   openclaw — can drive Linus's router with no per-client config. The cost is binding Linus's wire format to
   OpenRouter's evolution. Worth it for Phase 2a, or design a Linus-native vocabulary from scratch?
2. **Sort criteria for a single-machine router.** OpenRouter's `price | throughput | latency | exacto` doesn't quite
   map. On a 32 GB M1 Max the meaningful axes are probably `latency | throughput | memory_pressure | quality_tier`. Want
   to pin the Linus sort enum now, or defer until Phase 3 when there are actually >1 local backends to choose between?
3. **Burst-to-paid-API escape hatch.** The north star says "no paid APIs required for operation," not "forbidden." Is
   there a future where Linus _optionally_ falls back to OpenRouter (or hosted Anthropic) when a local backend OOMs or
   fails — and if so, this SDK becomes a real dependency. Worth flagging in ROADMAP, or off-limits?
4. **Speakeasy for the eventual `linus-py`.** When Linus ships its own client in Phase 5+, would you rather hand-write
   the SDK (full control, more taste) or generate it from the OpenAPI spec (free updates, less work, the
   `python-sdk`/Speakeasy shape as the template)?
5. **Differentiation from `openrouter-skills`.** Do you see Linus ever adopting the Agent-Skills standard for its own
   local-routing skill pack — i.e. publishing `linus-skills` for Claude Code, Cursor, etc. — or is that overkill given
   Linus is a backend, not an agent skill?

### origin

1. **Memory layer ownership.** The Memory Architecture spec is fresh. Is the intent for Linus to _own_ the memory store
   (KnowledgeBase + bespoke schema) or to _consume_ one (Origin daemon as sidecar)? This decision flips Origin from
   "study material" to "architectural dependency."
2. **MCP as the integration substrate.** Origin's primary surface is MCP; pmetal's `pmetal-mcp` exposes 45 tools the
   same way; cline and openclaw both speak MCP. Three of the four most relevant repos in the collection have converged
   on MCP. Want to make MCP-as-tool-substrate an explicit Phase 3 ADR rather than letting it accrete?
3. **AGPL hygiene.** Origin is the second AGPL repo encountered (after a few others in earlier groups). Do we want a
   written rule in SAFETY.md or DECISIONS.md that AGPL code is allowed as an out-of-process dependency but never
   vendored, with the Apache-2.0 boundary types as the integration surface?
4. **Eval-harness pattern.** Origin's three-variant benchmark structure (base / reranked / expanded) on LongMemEval and
   LoCoMo is the most disciplined RAG eval in the collection. Worth porting the shape to `benchmarks/dan_tasks/` for
   KnowledgeBase RAG, or premature?
5. **macOS Tahoe stability.** Origin documents real Tahoe 26.x pain (`ggml_metal_init` failures, C++17 release-build
   fix, CoreGraphics quirks). Is your dev MacBook on Tahoe yet, and if so, has Linus's own llama.cpp/MLX path hit the
   same Metal init failure mode?

### gravityfile

1. **Does the KnowledgeBase indexer need a fast parallel walker?** If KB ingestion is currently slow because of
   single-threaded directory traversal, the jwalk pattern in `gravityfile-scan/src/scanner.rs` is worth lifting. If KB
   walks are already fast enough or bound by PDF parsing and embedding, this is a non-issue and gravityfile becomes pure
   ignore.
2. **Native TUI for Linus — yes or no?** ROADMAP Phase 5 points at openclaw as the front-end and Phase 8 at a native
   app. Is there an in-between phase where a Ratatui TUI for "talk to local Linus from any terminal without a browser"
   would be valuable? If yes, gravityfile-tui and pmetal's TUI become joint references. If no, this question closes the
   file.
3. **Multi-runtime plugin embedding (Lua + Rhai + WASM) — relevant to Phase 7 skills?** gravityfile embeds three
   scripting runtimes in one binary. For Linus's skills/tools system, is in-process scripting on the table, or is the
   plan strictly subprocess + MCP?
4. **Outlier honesty check.** The brief flagged this as Group 7's outlier and I confirm it: the only meaningful
   Linus-side angle is the scanner, and even that is a 200-line copy-paste candidate, not an integration. Should outlier
   repos like this get full notes in future curation passes, or a one-liner in the log?

### semanticworkbench

1. **Assistant-as-HTTP-service or assistant-as-in-process?** Semanticworkbench commits hard to the first; pmetal's
   `pmetal-mcp` and Linus's current assumed shape lean toward in-process tool calls plus an OpenAI-compatible serving
   endpoint. Is the right Phase 2a model a hybrid — Workers run in-process, but the orchestrator exposes an HTTP
   registration surface so external services (a future Linus fine-tune on a Mac Studio, or a Worker on the Vision Pro)
   can register the same way?
2. **Multi-participant conversations vs fan-out-and-collect.** The workbench treats N assistants in one conversation as
   peers that the user @-mentions; Linus today implies a Maestro-orchestrated fan-out. Is the multi-participant peer
   model interesting for any specific workflow (paper review, debate-style synthesis), or is fan-out enough through
   Phase 3?
3. **Frontend posture.** This repo is the strongest argument I've seen that an assistant-development UI is a separate
   artifact from a chat UI. Streamlit for Phase 2 and openclaw for Phase 5 cover the chat side; do you want a Phase 5+
   assistant-dev surface (skill authoring, prompt iteration, conversation replay), or is that always Claude Code +
   files-on-disk?
4. **Pydantic config that auto-renders UI.** Worth lifting for Phase 7 skill definitions — declare once, get both
   validation and a form. Adopt that pattern in the Linus tool registry, or stay closer to MCP's tool-schema convention?
5. **DEC-0002 reaffirmation.** After reading this, does the "framework-agnostic protocol over HTTP" shape change your
   conviction on owning the orchestration layer, or does it reinforce it (because the protocol surface is what's worth
   owning, not the service implementation)?

### g7-harnesses synthesis (cross-cutting)

1. **Phase 1f framing.** The evaluation brief treats claude-squad and claude-task-master as finalists for the same slot.
   After reading both notes, the verdict is that they are not competitors — they are planner and runner. Does the ADR
   capture "adopt both patterns, neither product," or should it declare one pattern as primary and treat the other as
   supplementary?
2. **Session store format.** ARCHITECTURE.md calls for a session store and audit log without specifying a format. The
   workgraph JSONL shape is the right weight for a personal system; SQLite is the right weight if Phase 2 query patterns
   demand it. Which wins — human-readable append-only JSONL, SQLite with Alembic migrations, or JSONL now with a SQLite
   migration gate at Phase 3 when query complexity arrives?
3. **Open Responses versus Chat Completions.** The serving protocol choice locks in client compatibility. Ollama serves
   the legacy Chat Completions shape; the Open Responses spec adds stateful response threading and the SSE event
   catalog. Cline and openclaw speak both; claw-code-local speaks OpenAI-compat generically. What is the Phase 2a
   target, and is it worth a short spike against the open-responses spec document before committing?
4. **Origin as memory sidecar.** The memory-architecture spec is fresh at commit `d77e026`. Does Dan want to evaluate
   `origin-server` as a Phase 2b candidate sidecar before the spec hardens, or does the spec get written first and
   origin gets evaluated against the resulting requirements? The order matters because if origin is the candidate, the
   spec should be written in a way that makes the evaluation legible.
5. **MCP as explicit Phase 3 ADR.** Three repos (origin, cline, semanticworkbench) and the existing pmetal-mcp note all
   converge on MCP as the tool substrate. DEC-0005 deferred this evaluation. G7 supplies enough data to close it. Should
   the Phase 1f ADR include a sub-decision on MCP, or does it get its own ADR at Phase 3 kickoff?

---

## Group 8 — Scientific Reasoning Agents (FutureHouse stack + adjacents)

# Group 8 Questions for Dan — Scientific Reasoning Agents

### paper-qa

1. **KnowledgeBase vs paper-qa division of labor.** KnowledgeBase already does PDF ingest, metadata, and a knowledge
   graph. Should paper-qa replace KnowledgeBase's retrieval/synthesis (KB stays corpus-of-record), or run alongside it
   as a second engine, or is the right move to fork paper-qa and graft KnowledgeBase's KG into the `GatherEvidence`
   re-ranker?
2. **Local-LLM floor.** Paper-qa explicitly warns 7B is too weak. Does the Phase 2c plan target Qwen2.5-14B as the
   default worker, accept the quality hit on 7B, or wait for a Phase 6 fine-tune that's specifically tuned for the
   RCS/tool-selection prompts?
3. **Citation accuracy as a metric.** The "superhuman" claim is largely about citation precision/recall vs human experts
   on LitQA2. Is that worth replicating as a Linus benchmark in `benchmarks/dan_tasks/` against your own biochem PDFs,
   or is "Dan's subjective satisfaction on real questions" the better signal?
4. **Multimodal enrichment cost.** `parsing.multimodal=True` adds an LLM call per figure/table at index time. For your
   ~thousand-paper corpus that's a substantial one-time hit. Run it (and pay the time/tokens once for permanently better
   figure retrieval), defer to a later phase, or run it selectively on starred papers?
5. **FutureHouse stack commitment.** Adopting paper-qa pulls in `fhlmi` and `fhaviary` as runtime deps and makes `ldp`
   an obvious Phase 6 candidate. Comfortable making FutureHouse a strategic upstream for Linus's scientific reasoning
   layer, or do you want a paper-qa-only integration with an exit ramp?

### aviary

1. **Benchmark substrate.** Should `benchmarks/dan_tasks/` be implemented as aviary `Environment`s from day one (so
   Phase 6 RL is a config flip, not a rewrite), or kept as a lighter custom-eval-runner format and ported only if/when
   RL becomes real?
2. **LDP vs pmetal-trainer for RL.** Both can drive aviary environments in principle, but LDP is Python-native and
   assumes LiteLLM-style endpoints, while pmetal owns the model weights and offers GRPO/DAPO directly. Is the Phase 6
   plan "aviary envs + LDP rollouts + pmetal as the served model," or "aviary envs + a pmetal-native rollout shim"?
   They're different glue problems.
3. **LAB-Bench as a Maestro/Worker delta target.** LAB-Bench is published, with hosted-frontier scores presumably
   available. Worth running a local Qwen-Coder-32B vs. hosted-Claude head-to-head on LitQA2 / FigQA to size the gap
   before committing to fine-tuning?
4. **Notebook environment as Linus's notebook tool.** The `aviary.notebook` package is a working Docker-sandboxed
   Jupyter executor. Adopt it as Linus's first sandboxed-code-execution skill in Phase 7, or roll a simpler
   `nbclient`-based local executor and accept lower isolation?
5. **Tool definition surface.** `Tool.from_function` (signature + docstring → schema) is much cleaner than the
   Cline-style "variant prompts per model family" approach. Standardize on it for Linus's tool registry, or treat it as
   one of several adapters into a Linus-native `Tool` type?

### ldp

1. **Adopt the `(action, state, value)` contract for Linus Workers?** The shape is clean and gives us value-estimate
   optionality for free. Cost is a small departure from the bare OpenAI chat-completions shape that Cline and openclaw
   send today. Worth standardizing in Phase 2a, or leave it as Phase 3 work?
2. **MemoryAgent + MemoryOpt as Phase 3's first multi-agent template.** A KnowledgeBase-backed agent that records its
   own successful trajectories and retrieves them on future invocations is exactly the "learn-from-use" loop you've
   sketched. Is this the right first agent to build, or do you want a simpler ReAct-over-KnowledgeBase as the v1?
3. **Pair ldp with aviary, or unify behind a single Linus-native abstraction?** Both are FutureHouse, both are Apache,
   but they are two packages with two install footprints. Phase 2 could vendor the parts we need into
   `src/linus/agents/` and skip the dependency. Acceptable, or worth the dep?
4. **SCG: yes or no for Phase 6.** The SCG buys gradient flow through the agent for end-to-end training. It also buys
   ~1k lines of compute-graph machinery to maintain. Do you anticipate Phase 6 doing gradient-based agent training (in
   which case SCG earns its keep), or is Phase 6 scoped to LoRA-on-trajectories (in which case SCG is pure overhead)?
5. **fhlmi vs. direct Ollama/pmetal-serve clients.** fhlmi is yet another LiteLLM wrapper. Linus will already have
   OpenAI-compatible clients for its own backends. Worth taking on fhlmi as the shared LLM-interface layer (and
   inheriting its caching, retries, embedding API), or build a thin Linus-native client and skip it?

### robin

1. **Pairwise ranker as a Linus primitive.** The `choix.ilsr_pairwise` tournament is a 50-line lift and would let any
   Linus skill that produces N alternatives pick a winner without trusting a single LLM-as-judge call. Want this in the
   Phase 2 utility belt, or wait until a skill needs it?
2. **Prompt-validator convention.** Robin's "regex-parse `{placeholders}` and assert against an expected set at model
   construction" pattern would have caught half the KnowledgeBase prompt-template bugs. Worth adopting as a Linus prompt
   convention now, before there are many prompts to retrofit?
3. **paper-qa + KnowledgeBase as the local Crow replacement.** Robin's Edison dependence collapses to "we need a
   literature-QA agent." If paper-qa runs locally against KnowledgeBase well enough, Robin's pipeline becomes a
   reasonable Phase 7 skill template. Worth a Phase-1 spike on paper-qa-against-KB to find out?
4. **Therapeutics scope.** Robin's domain is small-molecule drug discovery for human disease via cell-culture assays —
   adjacent to but not the same as your genomics/computational-biology focus. Is a Robin-style "hypothesis pipeline"
   skill on Linus actually something you'd use, or is the value purely "study the patterns, build something different"?
5. **Tournament ranking vs LLM-as-judge in benchmarks.** The Dan-tasks benchmark suite will need a way to score
   free-form outputs. Pairwise tournament + Bradley-Terry is more expensive but lower variance than rubric scoring.
   Worth piloting on one benchmark task as a methodology test?

### ether0

1. **Biology verifier candidates.** The ether0 trick is that chemistry has cheap rule-based and simulator-based oracles
   (RDKit, MolTrans, KDESol, molbloom). Which biology subdomains do you think have analogously cheap verifiers — BLAST
   identity for sequence design, ESMFold pLDDT for protein design, tissue-eQTL direction-of-effect for variant
   reasoning? A short list would shape Phase 6 materially.
2. **Mistral-Small-24B as base.** Ether0 chose Mistral-Small-24B specifically. For a Linus bio reasoner, is 24B the
   right starting size given the 32 GB constraint, or do we deliberately go smaller (Qwen2.5-7B / Mistral-7B) to keep
   RLVR experiments cheap and trade specialist quality for cycle time?
3. **Specialist-then-generalist pattern.** The ether0 paper's RL loop runs specialists per task group, rejection-samples
   their traces, and re-SFTs into a generalist. Worth replicating verbatim for a Linus domain model, or is the
   multi-pass orchestration overhead prohibitive on M1 Max — i.e. should we collapse to single-stage RLVR?
4. **Reward-function design discipline.** Most of ether0's verifiers return strict 0/1, with `soft` Tanimoto only as a
   fallback. Do you agree with the design bet that strict binary rewards beat dense shaped rewards for RLVR, or do you
   want partial-credit shaped rewards as the default for early bio experiments where the verifier itself is noisier?
5. **Adopting `ether0.rewards` in KnowledgeBase.** Some KnowledgeBase chemistry tooling could use `valid_mol_eval` and
   `is_reasonable_molecule` as guardrails for any LLM-generated SMILES today — worth a small dependency, or keep
   KnowledgeBase free of FH-stack imports for now?

### BixBench

1. **Dataset overlap risk.** BixBench questions derive from 60 published notebooks. If Dan has read any of those source
   papers (likely, given the field), there is a contamination concern when Dan-curated tasks share provenance. Want to
   log which capsules Dan recognizes and treat them as "no-credit" items in the Linus scorecard?
2. **Open-ended vs MCQ for Dan-task-suite.** BixBench supports both modes; the open-ended setting with LLM-judge grading
   is more realistic but noisier. For the private Dan-task-suite, do we follow BixBench and offer both, or commit to one
   mode (likely open-ended with hand-graded rubric for the held-out subset)?
3. **Docker vs native kernel.** BixBench defaults to a Docker Jupyter env. On the M1 Max that loses Metal/ANE access for
   any in-notebook ML; for bio-analytics work this rarely matters (pandas/scipy/biopython), but for any benchmark task
   involving local inference inside the notebook it would. Run BixBench in `use_docker: false` mode to keep parity with
   Linus's actual deployment surface, or accept the Docker default for reproducibility?
4. **LAB-Bench in parallel.** The sibling repo LAB-Bench is the literature-reasoning counterpart to BixBench's
   notebook-execution focus. Worth standing both up in Phase 1, or prioritize BixBench as the more mission-aligned and
   treat LAB-Bench as a later add?
5. **Frontier baselines.** Should the Linus scorecard list the v1.5 paper's GPT-4o / Claude-3.5-Sonnet numbers as a
   visible ceiling on every BixBench run, or leave them out so Worker progress is judged on its own trajectory?

### LAB-Bench

1. **ProtocolQA failure-mode coverage.** The repo's protocols are realistic (PBMC isolation, QIAprep miniprep, etc.) and
   the questions inject deliberate errors for the model to catch. Spend an hour reading 20 ProtocolQA questions across
   subsets — do the injected mistakes match the kinds of mistakes you actually saw burn experiments in the lab (buffer
   swaps, centrifuge speeds, missing cofactors), or are they too cosmetic / too obvious to be a real wet-lab signal?
2. **SeqQA as a Linus smoke test.** SeqQA is closed-form and largely procedural (count restriction-enzyme fragments,
   design PCR primers, compute GC%). Many of these have deterministic right answers a small Python tool could solve
   outright. Is SeqQA more interesting as a test of (a) raw model reasoning over sequence text or (b) Linus's
   tool-routing — i.e., the right answer is "call the `restriction_digest` skill, here's the result"?
3. **LitQA2 vs paper-qa loop.** LitQA2 provides DOIs / URLs for ~80% of questions but the public scoring path is
   closed-book MCQ. Does running LitQA2 with KnowledgeBase + paper-qa retrieval (open-book) and reporting the lift over
   closed-book make sense as an early Phase 2 milestone, or do we keep closed-book to stay comparable to the arXiv
   baselines?
4. **DbQA as a Phase 7 skill driver.** The 9 DbQA subtasks each correspond to a different biological database (GTRD,
   miRNA targets, oncogenic signatures, viral PPI, etc.). Do you want Linus's Phase 7 skill set to track this list — one
   domain tool per database — or is this too narrow vs. the actual queries you run day-to-day in your own work?
5. **Canary hygiene.** The canary string is a superset of BIG-bench's. Should it go into a single
   `benchmarks/canaries.txt` file plus an ingestion-time grep block in KnowledgeBase, or does the KB submodule already
   have a contamination-filter hook we should extend?

### finch

1. **Sandbox decision for Phase 7.** Three options: (a) accept emulated x86 Docker and the slowness, (b) build an arm64
   bioinformatics image (real packaging work, many bioconda pins to revisit), (c) skip Docker and isolate via a
   per-Worker conda env + sandbox-exec. Which way should the spec lean?
2. **Notebook-as-artifact in KnowledgeBase.** Finch produces a `notebook.ipynb` per task as a first-class shareable
   artifact. Should Linus's KnowledgeBase store agent-produced notebooks alongside papers and notes — i.e., does "agent
   ran this analysis" become a retrievable, citable object?
3. **Rerun-everything cost on local hardware.** The "rerun whole notebook on every edit" invariant is elegant but
   expensive on a laptop for analyses with 10+ minute cells. Acceptable cost for the simplicity, or do we add cell-level
   cache invalidation in the Linus port?
4. **Coupling to BixBench as the eval.** Does it make sense to run BixBench against Linus's own port of the finch loop
   as the Phase 7 acceptance test, or build a Dan-specific notebook benchmark in `benchmarks/dan_tasks/` that more
   closely matches your real workflow (the genomics/RNA-seq problems you actually do)?
5. **Multi-language support.** Finch supports Python, R, and Bash via `NBLanguage`. R is a meaningful fraction of
   bioinformatics. Is keeping R kernel support in Linus a Phase 7 requirement, or is Python-only acceptable for v1?

### scientific-agent-skills

1. **Skill format lock-in.** Adopting the Anthropic Agent Skills standard for Linus's tool registry means committing to
   Claude-flavored markdown + YAML frontmatter as the source of truth. This is becoming a multi-vendor standard, but
   Linus could alternately wrap each skill in a Linus-native tool definition. Commit to Agent Skills as Linus's native
   format in Phase 7, or treat it as one of several formats the registry consumes?
2. **bioSkills vs. scientific-agent-skills overlap policy.** Both will install — bioSkills covers ~438 workflow skills,
   scientific-agent-skills covers 135 tool/database skills, and their bio-database surfaces overlap. Do we install both
   with namespacing (`bio/atac-seq`, `sci/scanpy`) and let agent skill-selection resolve, or do we curate a merged
   whitelist and drop duplicates manually before Phase 7 ships?
3. **Cloud-platform skills.** Benchling, DNAnexus, LatchBio, OMERO, Modal, Adaptyv, Ginkgo Cloud Lab, Protocols.io,
   LabArchives — none of these match Dan's current workflow. Prune them at vendor time, or keep them installed in case
   future Dan needs them and let agent skill-selection ignore them?
4. **K-Dense BYOK desktop app.** It's a free open-source AI co-scientist that consumes these same skills with a chat UI
   bolted on. Worth a one-hour smoke-test as a reference implementation for what a "skills + chat" front-end looks like
   before Phase 5 (openclaw)? Or treat as competitive intel only?
5. **Security scanning.** scientific-agent-skills runs Cisco AI Defense's Skill Scanner weekly. Should Linus run the
   same scanner on every installed skill (vendored or otherwise) as part of CI, or trust the upstream scan results
   recorded in SECURITY.md?

### ibmdotcom-tutorials

1. **Docling for KnowledgeBase ingestion.** Your current pipeline uses pypdf with the decompression-limit workaround.
   Docling handles scans, tables, and slide decks that pypdf mangles. Worth a Phase 2 spike to compare on a sample of
   your harder papers — chemistry-figure-heavy, table-heavy, or scanned legacy PDFs — or is pypdf good enough for the
   corpus you actually have?
2. **A2A vs ad-hoc.** When Phase 3 multi-agent fan-out lands, do you want a named wire protocol (A2A, ACP, MCP, or
   similar) for Worker-to-Worker communication, or is in-process Python plus a shared session store enough for the
   scales Linus operates at?
3. **Langfuse vs homegrown audit log.** SAFETY.md implies an audit log without specifying its shape. Is a Langfuse-style
   trace store the right target for Phase 2, or does a SQLite event table satisfy the auditability goal at lower
   complexity?
4. **Anti-pattern enforcement.** The LangChain/LangGraph removal was decided once. Is it worth a one-line lint check or
   a pre-commit hook that flags `import langchain` / `from langgraph` to keep that decision from drifting back in via
   copied tutorial code?
5. **Granite as a worker model.** IBM's Granite 3.x models are Apache-2.0 and available via Ollama. Do they merit a
   benchmark slot in the Phase 1c worker-model bake-off alongside Qwen2.5-Coder and Mistral-7B, or is the 3B/8B Granite
   family not competitive enough on your task suite to spend the eval cycles?

### claude-prism

1. **Paper-drafting as a Worker task.** Does the Phase 7 skills graduation include "draft a methods section from a
   notebook" or "convert a markdown draft to a journal-formatted LaTeX manuscript" as named Worker capabilities, or is
   manuscript writing always a Maestro+Dan activity? The answer changes whether claude-prism's shell is interesting at
   all.
2. **K-Dense skills corpus relationship.** Two repos in this group (claude-prism and scientific-agent-skills) install
   the same K-Dense bundle. Should Linus pick the K-Dense corpus as its canonical Phase 7 scientific-skills baseline, or
   is OmegaWiki's Anthropic-authored set or some merged superset more appropriate for a PhD biochemist's workflow?
3. **Tectonic embedding.** Embedding Tectonic costs a substantial Rust dependency tree (harfbuzz, icu, freetype,
   graphite2). For a Linus-side LaTeX capability, is "shell out to a system `tectonic` binary" enough, or is the
   embedded-engine pattern worth the build complexity?
4. **Local LLM fit.** Suppose Phase 6 produces a Linus fine-tune capable of competent LaTeX editing on a given
   manuscript. Would patching claude-prism's `claude.rs` to talk to a local OpenAI-compatible endpoint be a reasonable
   Phase 8 spike, or is the Claude-CLI-subprocess assumption baked deep enough that a fork is impractical?
5. **Differentiator confidence.** I read claude-prism as "K-Dense scientific skills wrapped in a LaTeX/PDF/Zotero
   writing GUI." If you see a sharper differentiator after using the DMG — particularly something the K-Dense
   scientific-agent-skills app doesn't already provide — please flag it; I had to stop short of running both apps
   side-by-side.

### g8-sci-agents synthesis (cross-cutting)

1. **The KnowledgeBase vs paper-qa substrate decision.** Three options are on the table: (1) paper-qa becomes the
   retrieval/synthesis engine with KnowledgeBase as the corpus-of-record and tantivy index; (2) paper-qa runs as a
   second engine alongside KnowledgeBase's existing retrieval; (3) paper-qa's patterns are lifted into KnowledgeBase
   directly without the paper-qa dependency. Which is acceptable depends on how much paper-qa's `GatherEvidence`
   re-ranking buys over what KnowledgeBase already does. The smoke-test result on 10 papers will make this concrete. Is
   there a quality bar that would cause you to build from scratch rather than adopt paper-qa wholesale?
2. **Biology RLVR verifier candidates.** ether0's chemistry recipe generalizes if the oracle side generalizes. The
   candidate verifiers above (BLAST, ESMFold pLDDT, ClinVar, eQTL direction-of-effect) are based on what's publicly
   available and computationally cheap. From your genomics/biochem experience: which biology tasks have verifiers cheap
   enough to run in a tight RL loop — meaning sub-second per call, deterministic or near-deterministic, and available
   without a remote paid API? The answer to this question shapes Phase 6's scope more than any architectural choice.
3. **The Phase 7 sandbox decision for the notebook-agent Worker.** Three options: accept emulated x86 Docker (slow for
   BLAST, IQ-TREE, SPAdes on M1 Max); build an arm64 bioinformatics image (real packaging work against bioconda pins);
   or design a Linus-native sandbox using per-Worker conda env plus sandbox-exec. Which is the right starting point
   depends partly on which bioinformatics tools you actually need in the analysis loop — if the real use cases are
   pandas/scanpy/biopython rather than BLAST and assembly tools, the native conda env path may be faster to a working
   agent than rebuilding the Docker image for arm64.
4. **ProtocolQA as a personal calibration test.** The LAB-Bench ProtocolQA subset injects deliberate errors into
   realistic wet-lab protocols (PBMC isolation, QIAprep miniprep, similar) and asks the model to catch them. Spending an
   hour reading 20 ProtocolQA questions is worth doing before setting it as a benchmark axis — both to verify that the
   injected mistakes match the kinds you actually saw burn experiments (buffer swaps, centrifuge speeds, missing
   cofactors) and to check whether a local model answering "correctly" on this benchmark actually demonstrates wet-lab
   reasoning or is pattern-matching against training data. Your ground truth here is directly useful.
5. **FutureHouse as a strategic upstream.** Adopting paper-qa as the Phase 2c substrate and ldp's agent contract for
   Phase 3 Workers effectively makes FutureHouse a strategic upstream vendor in the same way Ollama and mlx-lm are
   inference upstreams. The upside is a cohesive, evaluated, scientifically literate stack with Apache 2.0 across the
   workspace. The downside is tracking two or three additional package release cadences. Is FutureHouse a stable enough
   upstream for that role, or do you want a paper-qa-only integration with a deliberate exit ramp before taking on ldp?

---

## Group 9 — Bioinformatics & Domain-Specific Science Models

### Bacformer

1. **Which downstream task carries the most weight for you?** The eight checkpoints cover masked vs causal vs
   essential-genes-finetuned, MAG vs complete-genome. Operon ID, essential-gene prediction, and strain clustering all
   have ready tutorials — is one of these the natural first Linus skill, or is the contextualised-embedding output
   itself the primary product (i.e., upstream of your own KnowledgeBase analyses)?

2. **Bacformer vs your existing pipelines.** You have 13 years of genomics tooling. Where does a 300M protein-aware
   encoder land relative to whatever you currently use for, say, operon calling or MAG QC — replacement, ensemble
   member, or "interesting embedding signal to graft onto existing scoring"?

3. **The protein-family-token causal checkpoint.** `bacformer-causal-protein-family-modeling-complete-genomes` can
   generate plausible bacterial genomes at the family level. Is that something you want to expose as a Linus capability
   (synthetic-genome scaffolds, hypothesis generation), or strictly off-piste?

4. **Differentiation from BioReason and the DNA-LLM landscape.** I argued in section 3 that Bacformer occupies a
   distinct slot (above-ORF, prokaryote-only, encoder-only, no reasoning head). Does that framing match your read, or is
   there overlap I'm missing — e.g., do you see Bacformer embeddings being plugged into a BioReason-style reasoning loop
   as a Phase 7+ composite?

5. **Pretraining ambitions.** Phase 6 is fine-tuning on Apple Silicon. The 26M base model with a small LoRA on a bespoke
   corpus (e.g., your own genome collection) is plausibly tractable on M1 Max. Worth scoping as a Phase 6 candidate
   alongside the language-model fine-tunes, or strictly out of scope?

### BioReason

1. **KEGG benchmark legitimacy.** The 290-datapoint KEGG disease-pathway set is the headline result. Is that benchmark
   actually meaningful to a working biochemist — does getting 98% on it imply useful pathway reasoning, or has it been
   reduced to a multiple-choice exercise where memorization of KEGG itself dominates? Worth a 30-minute look at the
   curation notebook before adopting it as a Linus eval target.

2. **Evo2 vs NucleotideTransformer.** For Linus's Phase 1 benchmark suite, NT-500M is the M1-Max-tractable choice and
   Evo2-1B almost certainly is not. But the paper shows Evo2 wins on VEP non-SNV. Are you willing to leave the harder,
   more interesting variant-effect questions on the table to stay on a portable encoder, or is Evo2 worth the porting
   fight in Phase 6?

3. **DNA-LLM fusion vs RAG.** BioReason's pitch is that the LLM literally consumes DNA embeddings as context tokens. The
   obvious Linus alternative is a KnowledgeBase RAG over annotated genomic resources (KEGG, ClinVar, UniProt, Ensembl) +
   a generic Qwen — no fusion, no fine-tune. Do you have a prior on which path is more promising for Phase 3?

4. **GRPO for reasoning, not alignment.** The repo's `train_grpo.py` uses GRPO to elicit reasoning traces, lifting KEGG
   from 95.86% to 98.28%. That is a concrete protocol Linus could adopt in Phase 6 for a "reasoning-trained Linus"
   rather than a generic instruct fine-tune. Worth raising to a Phase 6 candidate experiment now, or premature?

5. **BioReason-Pro relevance.** The follow-up swaps DNA encoder for ESM3 protein embeddings + GO-GPT to predict protein
   function — closer to wet-lab interpretation. Should this group's "study target" be BioReason or BioReason-Pro?

### bioSkills

1. **Bio-Task Bench Intermediate plateau.** Both agents land at 0.96–0.97 on Intermediate with or without skills. Read
   scientifically: is this an evaluator saturation problem (rubric too coarse), is Intermediate actually too easy, or
   does in-context skill priming genuinely fail to help on multi-step tasks where the bottleneck is judgment rather than
   API recall? The answer changes how aggressively Linus should bet on skills as an autonomy-graduation lever.

2. **Local-model amplification.** The biggest gain (+0.049) was on Codex 5.4-Mini, the weaker model. Hypothesis: smaller
   / local models benefit more from skill priming than Sonnet does. Worth running bioSkills against Qwen2.5-Coder-32B
   and a future Linus fine-tune on the same 33-test BTB to test this empirically before Phase 7?

3. **Heavy CLI tool surface.** ~25 Bioconda CLIs (samtools, bcftools, MACS3, IQ-TREE2, PLINK, ADMIXTURE, Salmon, STAR,
   Bakta, BRAKER3, …) need to be present for the skills to actually run. Make this a single conda env Linus manages, or
   per-project, or document and let the user provision?

4. **Single-cell coverage match.** The 14 single-cell skills cover scRNA-seq, scATAC, perturb-seq, lineage tracing
   (Cassiopeia), cell-cell communication (CellChat-style + MeboCost metabolite communication). Does this map onto the
   scRNA-seq workflows you actually run, or are there missing methods (e.g. specific batch-correction or trajectory
   tools you prefer) that we'd want to author additional skills for?

5. **Entrepreneurial surface.** The skills synthesis flagged scientific-literature intelligence and bioinformatics
   pipeline documentation as Phase 1+ surfaces. bioSkills is essentially a working v0 of the second one. Worth reaching
   out to GPTomics (the maintainer) to compare notes, or keep this as private ammunition for the Linus-as-product story?

### deepsems

1. **Cryptic-BGC reality check.** The headline (41.1% structure recovery vs. 8.9% / 0.0% for PRISM 4 / antiSMASH 7) is
   large enough to be either field-changing or a benchmark-construction artifact. Worth a careful read of the paper's
   test-set design before promising a Linus tool — do you want to do that read, or have it queued for a Worker?

2. **Scope of "molecular properties" in your work.** `calculate_molecular_properties.py` covers LogP / MW / TPSA / QED /
   SAscore via RDKit — drug-likeness flavored. Your biochemistry interest is genomic/regulatory, not drug-discovery. Is
   downstream filtering on these properties useful to you, or is the SMILES alone the deliverable?

3. **MPS port effort budget.** Porting `predict.py` to `torch.device("mps")` is probably an afternoon (model is 50M
   params, no custom CUDA kernels visible). Is that worth a Phase-3 spike, or hold off until the broader KnowledgeBase +
   worker-tool plumbing is up?

4. **Pfam dependency.** Running DeepSeMS requires HMMER + Pfam-A.hmm (~1.5 GB) installed and indexed. Is bundling Pfam
   inside KnowledgeBase acceptable, or should the BGC-prediction tool assume Pfam is a separately-managed KnowledgeBase
   artifact?

5. **Sibling comparison priority.** Of {DeepSeMS, Bacformer, BioReason, bioSkills}, DeepSeMS is the most _packaged_
   (paper, weights, web server, Docker, ensemble). Should it be the G9 entry that gets promoted to a Phase 3 tool first
   as a forcing function for the whole "biology-domain Linus tool" pattern, or is one of the others a better leading
   example?

### g9-bio synthesis (cross-cutting)

1. **Bio-Task Bench Intermediate plateau.** Both agents land at 0.96–0.97 on Intermediate with or without skills loaded.
   Three explanations are consistent with the data: the rubric is too coarse to detect skill-level gains at the top end;
   the Intermediate tasks genuinely require multi-step biological judgment that in-context skill priming cannot provide;
   or skills help on the wrong axis at Intermediate difficulty (API recall instead of reasoning). Which explanation you
   find most credible changes how aggressively Linus should invest in the skills layer as an autonomy-graduation
   mechanism versus investing in the reasoning-trace training path (BioReason GRPO template). Worth a 30-minute look at
   five representative Intermediate tasks before deciding.

2. **Bacformer versus your existing operon callers.** You have 13 years of genomics pipelines. Where does a 300M
   protein-context-aware encoder land relative to whatever you currently use for operon calling, MAG QC, or strain
   clustering — replacement, ensemble member, or "interesting embedding signal to graft onto existing scoring"? The
   answer determines whether Bacformer is a Phase 7 skill that surfaces results to Dan directly or a Phase 7 capability
   that feeds upstream of Dan's own analyses.

3. **BioReason benchmark legitimacy.** The KEGG disease-pathway set covers 290 datapoints curated from KEGG relation
   annotations. Is that benchmark actually meaningful to a working biochemist — does 98% accuracy imply genuine
   multi-step pathway reasoning, or has the task been reduced to a pattern-matching exercise where memorization of KEGG
   annotation structure dominates? A 30-minute read of the curation notebook in `data/` would resolve this before
   adopting the dataset as a Linus evaluation target.

4. **deepsems cryptic-BGC reproducibility.** The 41.1% versus 8.9% headline is large enough to be either field-changing
   or a test-set construction artifact. Do you want to read the _Nat. Comp. Sci._ paper critically yourself, or route
   that review to a Worker with the paper in context and a structured rubric for checking train/test overlap?

5. **Pairing with scientific-agent-skills.** bioSkills (438) plus scientific-agent-skills from G8 (135) produces roughly
   573 skills as the Phase 7 inaugural catalogue, with bioSkills handling the bioinformatics specifics and
   scientific-agent-skills handling the broader lab-science agent patterns. Does that pairing feel right from your
   vantage point, or are there overlapping skills categories between the two repos that would create confusion for a
   Worker receiving both in context?

---

## Group 10 — Finance / Quant Agents

# Group 10 (Finance/Quant) — Questions for Dan Extract

### dexter

1. **Financial-intelligence priority.** The total-landscape doc lists financial knowledge as a desired Linus skill. Is
   that a near-term Phase 7 target (build a Linus equivalent of Dexter against free data sources) or a "nice eventually"
   marker that can sit until later phases?
2. **Compaction prompt as Phase 2 starting point.** Dexter's compact.ts prompt is a strong, tested template for
   "summarize tool results without losing numbers." Want to lift it directly into the Linus context-manager spec, or
   design from scratch and use Dexter only as a sanity check?
3. **Single-agent vs multi-agent default.** Dexter explicitly bets on one capable agent; TradingAgents and QuantAgent
   bet on committees. Linus's Phase 3 ("Knowledge & Parallel Agents") implies fan-out is desirable. Do we treat Dexter's
   single-agent-loop shape as the per-Worker default and reserve multi-agent for orchestration above it, or design for
   committee-style debate within a single Worker too?
4. **SKILL.md as the Linus skill format.** Dexter, Anthropic, and others are converging on YAML-frontmatter markdown for
   skill definitions. Adopt the same format for Linus's Phase 7 skill catalog so skills are portable, or specify a
   Linus-native format with richer typing?
5. **WhatsApp / phone interface.** Out of scope for Linus's current roadmap, but the Baileys gateway is a working
   pattern for "Linus you can text from a hike." Worth a Phase 8 placeholder, or actively not-wanted on privacy grounds?

### OpenBB

1. **AGPL stance.** Are you comfortable with AGPL-licensed components inside Linus during Phases 2–7 (personal use, no
   network exposure to others), with the explicit ADR that Phase 8 multi-user scenarios trigger a re-architecture to a
   process-boundary call or a license replacement? Or do you want a hard "permissive-only" rule from the start?
2. **Provider key budget.** The free-tier providers (yfinance, SEC, FRED, federal_reserve, ECB, OECD, IMF, BLS) cover
   macro, equity historicals, and filings. Paid providers (FMP, Intrinio, Tiingo) add fundamentals depth, real-time
   quotes, and broader coverage. Are you planning to subscribe to any, or should the Phase 7 skill be scoped to the free
   set?
3. **MCP-first or SDK-first.** Two integration paths: (a) `openbb-mcp` runs as its own local daemon and Linus tools are
   MCP-discovered; (b) Linus imports `openbb` directly and exposes hand-picked endpoints as Linus-native tools. Path (a)
   is cleaner architecturally and aligns with the openclaw / cline MCP question; path (b) gives tighter control and
   avoids running an extra process. Preference?
4. **Pairing with nixtla.** The natural workflow is OpenBB pulls the series, nixtla forecasts. Worth specing a small
   end-to-end Phase 7 demo task ("forecast next 30 days of AAPL close with confidence intervals") that exercises both as
   one combined skill?
5. **Adjacent vs core.** You've said finance is "useful adjacent capability," not core. Should this skill ride along
   with the same Phase 7 sandbox tier as scientific tools, or sit in a more restricted tier given that financial
   workflows can shade into trading-decision territory you may not want a worker model recommending on?

### QuantAgent

1. **Multi-agent decomposition pattern transferability.** The four-role linear pipeline (measurer → recognizer →
   contextualizer → decider) is generic. Worth prototyping a non-financial Linus skill on this template — say, a
   paper-triage skill (extract → classify → contextualize-against-KB → recommend) — to see whether LangGraph adds value
   versus a hand-rolled sequence in Phase 2's orchestration layer?
2. **LangGraph as orchestration substrate.** QuantAgent, TradingAgents, and several other agentic repos in the
   collection use LangGraph. ARCHITECTURE.md leaves the orchestration runtime open. Want to do a Phase 2a spike that
   evaluates LangGraph vs. a custom Linus orchestrator on one or two skills, with a written verdict ADR?
3. **Vision-LLM-on-rendered-chart pattern for science.** QuantAgent demonstrates "render → ask multimodal model" as a
   way to summarize numerical data. For genomics (coverage tracks, variant call plots, phylogeny figures) this could be
   useful with a local Qwen2.5-VL. Worth a Phase 1 experiment, or wait until local vision models are stronger?
4. **Differentiation from TradingAgents.** QuantAgent and TradingAgents are sibling repos solving overlapping problems
   with very different architectures (linear-4-agent vision pipeline vs. debate-style multi-team roster). Is the
   financial-knowledge adjacency Dan wants better served by one over the other, or do we treat both as study material
   and revisit only if a concrete Phase 7 skill needs them?
5. **Real-money safety boundary.** SAFETY.md doesn't currently address financial-execution autonomy. If Linus ever grows
   a financial skill, do we want an explicit SAFETY.md tier that forbids execution endpoints (broker APIs, wallet
   signing) regardless of harness? Worth pre-committing now, before the temptation appears.

### TradingAgents

1. **Domain transfer of the bull/bear debate.** The most interesting Linus-applicable idea here is the structured
   adversarial debate between two researchers over a shared report set. Is there a scientific-workflow analog you'd want
   Linus to run — e.g., "supports hypothesis" vs "alternative explanation" debate over a set of paper summaries from
   KnowledgeBase — and if so, should the Phase 3 spec include it explicitly or wait for Phase 7?
2. **Two-tier LLM split as a Linus convention.** TradingAgents' `deep_think_llm` / `quick_think_llm` distinction is a
   clean pattern — analysts on a cheap fast model, managers on a strong model. Should Linus formalize this as a config
   convention (and as a Maestro/Worker boundary marker) in ARCHITECTURE.md before Phase 3?
3. **Decision-log + reflection pattern.** The `~/.tradingagents/memory/trading_memory.md` mechanism — append outcome,
   compute realized result, feed prior lessons into the next run's manager prompt — is a near-drop-in template for a
   Linus "what worked / what didn't" memory. Is that interesting enough to spec independently, or does it stay coupled
   to whatever KnowledgeBase ends up being?
4. **Personal finance as a Phase 7 skill.** The README is firm that this is research-only and not investment advice.
   Setting that aside — do you ever want Linus to do private personal-finance research (analyze a 401k, model a
   refinance, evaluate a stock) such that TradingAgents' `dataflows/` adapters become useful, or is finance permanently
   out of scope for Linus?
5. **LangGraph as Linus's orchestration substrate.** TradingAgents, like several other agent frameworks, builds on
   LangGraph. Linus has not committed to an orchestration library yet. Is LangGraph in the running for Phase 2a's
   orchestration layer, or is the plan to write a thinner Linus-native graph runner and avoid that dep?

### nixtla

1. **Forecasting as a Phase 7 skill?** Time series forecasting is a clean candidate for the first non-trivial Linus
   domain skill — well-defined I/O, easy benchmarks, useful both for finance and for omics/environmental data. Worth a
   Phase 7a entry, or does this stay informal?
2. **Open-weight foundation TS models in Phase 6.** TimesFM (Google, ~200M) and Chronos (Amazon, T5-based, 20M–700M) are
   open and run on MPS. Interesting as Phase 6 fine-tuning targets on omics-trajectory or epidemiological data — or is
   biological time-series data shaped too differently from generic series for transfer to work?
3. **Data-sovereignty rule on TimeGPT.** Worth writing an explicit ADR that hosted-model TS APIs (TimeGPT, Google Vertex
   Forecast, AWS Forecast) are forbidden for any series derived from patient samples or unpublished experiments, even if
   a user explicitly opts in?
4. **Anomaly detection for instrument data.** `detect_anomalies` is a natural fit for QC of long-running biology
   instruments (sequencer flow rates, mass-spec ion currents, qPCR baselines). Is there a real corpus of such series in
   `context/` that could become a Linus benchmark?
5. **Hierarchical reconciliation for multi-omics.** `hierarchicalforecast` enforces consistency between aggregate and
   disaggregate forecasts (parent species + sub-species, total mRNA + per-isoform). Useful pattern for omics where
   pathway-level + gene-level forecasts must reconcile, or unrelated to how you actually analyze that data?

### g10-finance synthesis (cross-cutting)

1. **Financial-intelligence priority.** The total-landscape doc lists financial knowledge as desired adjacent
   capability. Is this a near-term Phase 7 target — build a Linus financial-data skill against OpenBB's free providers —
   or a "nice eventually" placeholder that can remain dormant while the scientific-computing core is built?
2. **AGPL stance before Phase 8.** OpenBB is AGPLv3. For Phases 2–7 on a personal machine with no network exposure to
   others, this is fine. For any "let a collaborator use Linus" or mobile-access scenario in Phase 8, an ADR is needed:
   process-boundary isolation or license replacement? Worth pre-committing to the decision criteria now rather than
   discovering the constraint mid-Phase-8.
3. **Nixtlaverse as a Phase 7 forecasting skill.** `statsforecast`, `mlforecast`, and `neuralforecast` install cleanly
   today. Is there a real corpus of omics-trajectory or environmental time-series data in `context/` that could anchor a
   Phase 7 benchmark and make this concrete, or does the forecasting skill remain speculative until that data exists?
4. **Two-tier LLM config as a named convention.** Should `deep_think_llm`/`quick_think_llm` be formalized in
   ARCHITECTURE.md as a named config pattern before Phase 3, or is the analyst/manager distinction best left implicit in
   per-skill configuration?
5. **Financial-execution safety boundary.** SAFETY.md does not currently address financial-execution autonomy. If Linus
   ever grows a financial skill — even research-only — worth adding an explicit tier that forbids broker API calls and
   wallet signing regardless of what a Worker requests? Pre-committing this constraint before the capability exists is
   cheaper than adding it after.

---

# Thematic syntheses — 2026-05-04 sweep

The nine thematic syntheses written during the post-fan-out integration pass each surface their own "Tensions and open
questions" section. The items below are the verbatim distillation of those sections, kept here as the per-source
archive. Promotion candidates (Tier 1 / Tier 2 / Tier 3) live in
[top-questions.md](top-questions.md) under the "Sweep promotions (added 2026-05-04)" section.

## Humans, Teams & Performance Synthesis (docs/syntheses/humans-teams-performance-synthesis.md)

1. **Promote "preserve room for Dan's multidisciplinary work" to explicit Linus design constraint?** VISION.md
   prominence vs softer location (CLAUDE.md engineering convention or ROADMAP.md phase note). Güllich evidence
   supports the constraint; the question is the right home.
2. **Worker-spec template: `goal_orientation` as hard requirement or optional annotation?** Hard requirement forces
   spec authors to think about orientation explicitly (source of most value) but adds friction to throwaway specs.
   Optional annotation captures intent but loses much of the discipline.
3. **Update skills synthesis inline now or hold for post-Phase-1 revision pass?** Change small enough that inline is
   cheap; risk is drift across syntheses if landscape doc isn't re-read immediately after.
4. **Session-rhythm metric — worth tracking, or would degrade into theatre?** Cheap to prototype on existing commit
   history; compute retrospectively before instrumenting as prospective gate.
5. **(Personal, not Linus.)** Whether the Güllich finding actually changes current time allocation. Implication may
   be "protect the shape, don't change it" — be explicit about the budget so Linus, which is engrossing, does not
   silently consume it.

## Generative Biology Synthesis (docs/syntheses/generative-biology-synthesis.md)

1. **"Generate → score → filter → wet-lab validate" as a named Linus generative-biology archetype now, or wait for a
   second in-corpus instance beyond DISCO and generative phages?** Recommendation: write the archetype paired with
   Evo 2 paper-note as canonical worked example.
2. **Evo 2 + generative-phages pairing as a focused mini-synthesis?** Wave 3 deliverable. Pairing forces sharp answer
   to the local-vs-remote-Evo-2 question, the SAFETY.md tier-3 policy, and the external-Worker-tier infrastructure
   question.
3. **Pattern for wrapping webserver-only tools (mCSM-metal, AlphaGenome API, hosted Evo 2)?** `external_api_tool`
   registry class plus an ADR. Deeper question: registry treats external tools as first-class Workers or degraded
   path. Synthesis-level argument is _first-class_.
4. **SAFETY.md tier-control for generative whole-genome design before Phase 7 starts?** Yes — write three-tier policy
   as Phase 1 deliverable.
5. **Generalist Group A FMs × specialist Group B generators — which combinations to implement first?** Recommended
   pairs: Trias+GenNA; REBEAN+DeepSeMS; Bacformer+DeepSeMS; mCSM-metal+DISCO (Phase 8); AlphaGenome+GenNA (Phase 8).
6. **DeepSeMS Pfam-domain input modernised with LucaOne or ProteinReasoner before being exposed as a Linus skill?**
   Phase 6 spike worth recommending in either case.
7. **FKC steering as a generic Linus inference-time pattern?** Mathematically principled where best-of-N is heuristic;
   pattern applies wherever a per-trajectory reward is available. Record on second instance.

## Infrastructure Foundations Synthesis (docs/syntheses/infra-foundations-synthesis.md)

1. **"World model as orchestration primitive" — useful design concept or term too overloaded?** PAN, WHAM, Kosmos,
   memory pillar all use the phrase to mean different things. Phase 3 design might be cleaner picking
   `task_state`/`shared_context`/`belief_state` for orchestration-layer surface, reserving "world model" for citation.
2. **Wh per task as first-class column in `benchmarks/dan_tasks/` vs separate energy ledger?** Per-prompt measurement
   (benchmark column) gives per-model comparability; `~/.linus/energy.jsonl` ledger gives per-project honesty.
   Different artifacts; sequencing matters for Phase 1 vs Phase 5.
3. **When does Linus need diffusion-model internals vs treating them as black boxes?** Working rule: black-box for
   any consumed model (image generators, AlphaFold3 outputs); internals only when reading a paper deeply enough to
   evaluate methodology. Worth committing to the rule explicitly.
4. **"Modern Transformer reference" paper to bridge 2017 → 2025?** RoPE, RMSNorm, SwiGLU, GQA, pre-norm conventions
   are spread across many papers without a clean survey companion. Short reference paper or Karpathy-style writeup
   would lower cost of every quantization/fine-tuning/KV-cache conversation.
5. **Local actually greener than hosted when boundary is drawn comprehensively?** Honest answer is "measure both" —
   commit to one focused local-vs-hosted comparison experiment now, or defer to Phase 5.
6. **WHAM consistency/diversity/persistency triple lifted wholesale or derived from Dan-specific workflow
   introspection first?** WHAM playbook says _derive, then evaluate_; vocabulary may serve as starting template.

## Native Low-Bit Apple Silicon Synthesis (docs/syntheses/native-low-bit-apple-silicon-synthesis.md)

1. **Phase 1c benchmark Bonsai 8B and BitNet 2B4T together under unified Worker-selection methodology?** Four-way
   comparison with one unified harness, scoring on joint cost/quality/latency Pareto position. Methodology authority
   in `docs/specs/phase1c-spike.md` (proposed) vs `docs/experimental-protocol.md` (existing) — second is more
   durable.
2. **MLX ternary kernel gap as a Linus contribution?** Single best-scoped contribution opportunity in the corpus.
   Phase 1d (immediately, while spike measurement is fresh) vs Phase 6d (deferred until streaming-or-not scoping).
3. **Bonsai 1-bit vs ternary as the right Worker default?** At 8B, ternary's 95% quality recovery vs binary's 89% is
   substantial; 0.6 GB extra footprint is small relative to 32 GB. Binary as opt-in for footprint-critical paths.
4. **pmetal low-bit Rust kernels evaluated as alternative to MLX-native Bonsai serving?** Long-term: pin to PrismML
   fork (real maintenance liability), contribute upstream MLX scale-only quant support, or wait for pmetal to
   subsume both. Deserves own ADR before inference layer hardens.
5. **Phase 6 BitDistill on small fine-tuned Worker more tractable than waiting for or reverse-engineering Bonsai
   PTQ?** Cost dominated by ~10B tokens of continued pretraining; on M1 Max could be hours/days/weeks. Spike timing:
   Phase 6a vs 6b vs deferred until PrismML's posture clarifies.
6. **"Native Low-Bit Apple Silicon" worth dedicated benchmark suite distinct from `benchmarks/dan_tasks/`?** Bonsai
   uses six-benchmark suite (MMLU-Redux, MuSR, GSM8K, HumanEval+, IFEval, BFCLv3); mirroring in `benchmarks/low_bit/`
   would let Linus reproduce published numbers and track the low-bit landscape over time.
7. **Is mlx-flash deprecated for Phase 6d's _original_ purpose?** Bonsai's compactness makes 8B class fit trivially.
   Honest answer: not deprecated, _narrowed in scope_. Phase 6d formal target should be rewritten — fine-tuned
   models that genuinely exceed RAM remain the proper streaming targets.

## LLMs in Science Synthesis (docs/syntheses/llms-in-science-synthesis.md)

1. **VISION.md cite Binz et al. and stake out Linus's positions explicitly?** One-paragraph addition naming four
   perspectives and Linus's hybrid converts implicit bets into reviewable design philosophy. Sub-question: whether
   to acknowledge tension points (the "Linus joins the Maestro team" line is in slight tension with strict
   Botvinick/Gershman reading).
2. **`docs/maestro-worker-protocol.md` Philosophy section naming Schulz/Marelli/Botvinick-Gershman blend?**
   Editorial work, but makes the connection between Binz-level commitments and Worker-level mechanics legible.
3. **`docs/EPISTEMIC-STANDARDS.md` analogous to LLM-wiki claim-typing?** Marelli calls for clear quality criteria
   defined before using LLMs. Short doc defining claim categories Linus distinguishes (verified-against-source,
   model-asserted-uncited, gap-flagged, contradiction-flagged) operationalizes Marelli explicitly and generalizes
   the LLM-wiki KB categories.
4. **(Personal.)** For Dan: which of the four perspectives most resonates, and is that reflected in current docs?
   Implicit answer reads as Marelli-flavored hybrid with Botvinick/Gershman on roadmap agency and Schulz on
   open-source. If accurate, say so; if not, the gap is worth surfacing.
5. **Maestro-class evaluation tier in `benchmarks/dan_tasks/` distinct from Worker benchmarks?** Knuth case is the
   cleanest argument that Maestro and Worker workloads are categorically different. Small Maestro-class eval
   (Hamiltonian-decomposition or Cayley-graph cycle puzzle) would formalize the role distinction.

## Function Annotation, Reasoning & Discovery Synthesis (docs/syntheses/function-annotation-discovery-synthesis.md)

1. **ProtHGT vs Horizyn-1 vs BioReason-Pro for first protein-function skill — picking criteria?** Pick on benchmark
   against Dan-authored protein-function eval; deeper question is which axis matters (latency, narrative quality,
   GO-Fmax, low-similarity robustness, ease of local deployment, agreement with experimental controls).
   BioReason-Pro's four-tier evaluation is a credible scaled-down picking template.
2. **LAB-Bench MCQ + BixBench agent harness as Phase 1 baseline for Worker selection?** Adopt now, supplement with
   Dan-authored capsules over Phase 1–3, reserve right to weight categories differently than source papers.
3. **FutureHouse evaluation philosophy worth adopting wholesale?** Insufficient-info option, open-answer-vs-MCQ
   contrast, 80/20 public/private split, LLM-judge for open-answer grading, pure-recall calibration baseline. Yes,
   with caveat: LLM-judge dependency on hosted Claude is not aligned with local-first posture; Phase 4 should target
   local judge or accept hybrid where hosted is benchmarking-only. Deserves explicit ADR.
4. **BioReason-Pro encoder swap to LucaOne or ProteinReasoner?** Frozen-encoder design makes swap mechanically cheap.
   Phase 6/7 spike: rerun the harness with each substituted, report deltas. Pending ProteinReasoner checkpoint
   release.
5. **"PLM + heterogeneous KG + graph transformer" as named Linus archetype?** ≥3 corpus papers (ProtHGT, DeepHGAT,
   PSPGO) are variants. Name after second independent replication outside this corpus, with ProtHGT as lead worked
   example.
6. **"Dual-encoder cross-modal retrieval" as named Linus archetype?** Pattern well-established externally (CLIP,
   CLAP, VideoCLIP, CodeBERT, ProtST); Horizyn-1 is first scientific-discovery instantiation. Name now with
   Horizyn-1 as lead worked example — external priors strong enough that pattern is not speculative.
7. **Default mode for function prediction?** Linus needs all three (KG-grounded, FM-with-typed-companion, pure FM),
   but default for new skills should be what orchestration layer audits most cleanly. Recommended: typed structured
   prediction wrapping free-text rationale (BioReason-Pro shape).

## Agentic Systems Synthesis (docs/syntheses/agentic-systems-synthesis.md)

1. **Role as first-class type in Phase 3 agent spawner?** ADR before Phase 3. Five+ corpus papers argue yes; Kosmos
   minimalism is the only counter-data-point; expanded set tilts strongly toward yes.
2. **Fifth memory layer for "investigation memory"?** Kosmos world model, Sketch2Simulation IR, HKUST QuantAgent
   context buffer all occupy a layer the four-layer pillar lacks (task-scoped, multi-agent, single-investigation
   lifetime). Resolve before Phase 3.
3. **"Validation gate" primitive in spawner, or sandbox layer's job?** Sketch2Simulation argues per-stage hooks make
   failures localizable; HKUST QuantAgent two-loop judge/reviewer and WikiAutoGen four-viewpoint critic block
   strengthen the case.
4. **"12-hour autonomous Linus run on Dan-supplied dataset" as Phase 7 north-star?** Concrete, falsifiable, inherits
   Kosmos's evaluation. Honest concern: gated on hosted-model-class capability local Workers may not reach on M1
   Max.
5. **Linus's policy on hosted-model fallback?** Critic-tier thread reframes: not "do we ever call hosted Claude?"
   but "which Roles are tagged as critic-tier and what is the budget policy?"
6. **Adversarial debate as Worker primitive?** Each round costs 2N+1 model calls; TradingAgents has no ablation
   isolating debate; Stony Brook QuantAgent is partial counter (works without debate, majority-with-confirmation as
   integrator). Empirical question for `benchmarks/dan_tasks/`.
7. **Typed inter-agent message format?** TradingAgents, both QuantAgents, WikiAutoGen, BioGuider, Sketch2Simulation
   all use typed structured outputs; only Kosmos hides schema in shared state object. Default to typed `AgentReport`
   with free text confined to named rationale field. ADR before spawner ships.
8. **Agentic-system theory as first-class architectural input alongside memory-pillar theory?** HKUST QuantAgent
   regret bound is the first formal result. Design intuition (KB coverage growth as dominant lever on suboptimality)
   worth promoting to design constraint. Brief "applicable theory" section in Phase 3 spawner ADR.

## Safety, Alignment & Privacy Synthesis (docs/syntheses/safety-alignment-privacy-synthesis.md)

1. **Linus local Worker inference layer expose activation hooks, on what schedule?** Black-box (faster to ship) vs
   per-block hooks (more engineering, enables steering/monitoring/future tooling). Stub API in Phase 1, feasibility
   spike in Phase 2 against Llama-3.1-8B-4bit on mlx-lm, commit to Phase 6 or 7 deliverable based on spike result.
2. **KnowledgeBase content ever flow to hosted Maestro?** Conservative: forbidden by default, opt-in per request.
   Open: whether even opt-in path is safe for genuinely sensitive content (Dan's notes, draft writing), or whether a
   category should be marked `hosted-forbidden` with no override.
3. **`docs/maestro-protocol.md`?** Values paper argues Maestro is not a black box and Linus depends on specific
   characterized behaviors. Cleaner than extending VISION.md because dependencies are operational rather than
   aspirational.
4. **Four SAFETY.md additions: single PR or staged?** Synthesis-internal: single PR (four form coherent posture).
   Pragmatic counter: four substantive policy changes at once gives less time to think about each. Single PR with
   explicit per-section Dan review.
5. **Supervised activation steering as cheaper alternative to LoRA fine-tuning?** Cost case strong. Open: does it
   generalize to modulations Linus actually wants (terseness, domain terminology, hallucination suppression in RAG),
   and does it compose without behavioral collapse?
6. **Activation steering on extremely-quantized models (BitNet)?** Beaglehole validates 4-bit Llama; BitNet ternary
   weights might break linearity assumption. Small experiment in `experiments/` if BitNet becomes serious target.
7. **First concept-vector dataset source?** Pipeline assumes GPT-4o-generated statements. Local generation gives
   lower quality; hosted generation pushes Linus-generated content to Anthropic, which deanonymization paper makes
   uncomfortable. Local for non-safety concepts, hosted for safety-critical concepts where data is generic enough
   not to carry Dan-specific identity signal.
8. **Mirroring vs sycophancy detection on Maestro outputs?** Periodic checking on Linus's own Maestro prompts could
   detect drift toward sycophancy — implementable as small audit-log extraction pipeline.

## Biological Foundation Models Synthesis (docs/syntheses/biological-foundation-models-synthesis.md)

1. **Generalist vs specialist Worker strategy — right Phase 7 default?** Recommended split (LucaOne as KG anchor,
   specialists as task workers) is a hedge; whether also right answer is empirical. Sub-question: benchmark LucaOne
   against RiNALMo on Dan-relevant RNA task and against AlphaGenome on variant scoring task before committing
   registry architecture.
2. **Evo 2 vs AlphaGenome for variant prediction — both, or pick one?** Hybrid depends on both being operationally
   available locally; Evo 2 faces real plumbing risk (StripedHyena 2 quantization tooling). Sub-question: hybrid
   worth the operational cost, or right Phase 7 commitment is "AlphaGenome variant scoring + Evo 2 generative DNA
   skill" with no internal routing?
3. **Tool registry `external_api_tool` class for non-locally-deployable models?** AlphaGenome hybrid release
   motivating case; Evo 2 40B second. Explicit auth, rate-limiting, cost accounting, graceful offline fallback,
   trust-tier tagging — recommend ADR.
4. **METL simulation-pretrained pattern worth applying to other Linus domains now or wait for second instance?**
   Recommend waiting; this synthesis is the placeholder. Risk of premature naming is generalizing from single case.
5. **Focused "Evo 2 + Wave 3 generative phage" mini-synthesis?** Pairing would land at "what does a private
   generative-biology workflow look like in Linus" and force sharp answer to local-vs-remote-Evo-2 question.
   Recommend yes, 1500–2000 words, scheduled as Wave 3 prep.
6. **Faithfulness of model-derived KG content.** First Wave 1 batch where volume of model-derived KG content is
   large enough to make claim-typing load-bearing. Sub-question: KnowledgeBase schema needs `model_prediction` edge
   class with explicit producing-model + version + confidence + content-hash provenance before Group A skills start
   writing back? Recommend yes.
7. **ProteinReasoner checkpoint release** — low-priority watch on BioMap GitHub and `airkingbd` HuggingFace org.
8. **AlphaGenome non-commercial license — does it constrain Linus's long-term posture?** If Linus is offered as a
   service, API path is closed and only legal path is released weights run locally. Hybrid release means workable
   iff local-deployability spike lands cleanly.

---

# Fan-out outstanding items — 2026-05-04

The Section 7 fan-out summary closed with 13 outstanding items. They're recapped here for archival completeness; the
ones promoted to top-questions.md are noted inline.

## Categorization

1. **prompt-vault placement** — miscategorized prompt cookbook; drop from G4 synthesis or create a tiny
   "miscellaneous prompt libraries" group at the end. → S41.

## Process / substrate

2. **Ollama-vs-non-Ollama Worker mix for the synthesis pass** — heavier per-document and lower-parallelism than the
   fan-out reads + writes. Worth deciding model strategy before kicking it off. → S42.
3. **Sub-agent hook bypass.** Sub-agent Write tool calls did NOT trigger the prettier hook — the pattern is "Worker
   writes, Maestro formats, Maestro commits." → S43.
4. **Internal-error edge case on result messages.** Two batches (G6, G8) had Worker result messages dropped due to
   internal error; Workers had completed and written files. Protocol: check filesystem state first when results are
   missing. → S44.

## Decisions surfaced by the integrate verdicts

5. **Phase 2 KB substrate decision: paper-qa as default integration target?** → S1 (Tier 1).
6. **LAB-Bench canary string blocklist** as Phase 2 ingestion obligation. → S2 (Tier 1).
7. **Phase 7 skills bundle: bioSkills + scientific-agent-skills as inaugural pair.** → S30.
8. **hyalo + keppi as Phase 3 KB tooling layer.** → S26.
9. **Maestro codebase navigation: ontomics vs codesight vs both.** → S27.
10. **fastmcp as MCP framework default.** Should land as explicit DEC-NNNN ADR before Phase 2 MCP-server work begins.
    → S3 (Tier 1).

## Cross-cutting findings

11. **Entrepreneurial-surface "biotech literature intelligence" stack now concrete:** bioSkills + paper-qa +
    Bacformer + LAB-Bench + KnowledgeBase. Fills `docs/entrepreneurial-surface.md` deliverable from
    planning-update-spec.
12. **MCP as tool substrate is now overdetermined.** Six repos in the run ship MCP servers (pmetal, openclaw,
    py3plex_mcp, agentmemory, keppi, plus fastmcp as framework). Phase 3 MCP adoption is no longer an open question
    — only policy details remain. Resolved via CLAUDE.md update.
13. **"No stateful Docker on macOS" rule well-validated by counter-examples.** anamnesis (Postgres+pgvector), WeKnora
    (6–10 container stack), finch (x86_64 miniconda) all trip on it. Worth referencing in eventual Phase 8 "what we
    don't build" section. → S60.
