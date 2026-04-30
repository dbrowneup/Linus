# Open Questions for Dan

All questions aggregated from `docs/repo-notes/`. Each section names the source repo
and carries the questions unchanged. Work through these in one pass or use them as
a reading agenda alongside the individual notes.

---

## pmetal

1. **Scope of Phase 1b.** The roadmap calls for a 5-concurrent throughput test; is that
   the right concurrency target, or would single-request tok/s + memory-footprint be
   enough to make the adopt/defer call?

2. **Feature-flag strategy.** Default pmetal build includes ANE + MLX + serve + Trainer
   + data + distill — about 15 active features on the critical path. Do we build the full
   default for Phase 1b and let compile times hurt, or strip to `--features serve` for
   the first pass and layer training in when Phase 6 approaches?

3. **pmetal-mcp as Linus's tool registry path.** pmetal already ships 45 tools via MCP.
   Is that a serious candidate for the Phase 2a tool registry (Linus wraps pmetal-mcp +
   adds KnowledgeBase tools), or should Linus own tool definitions entirely and
   pmetal-mcp is study material?

4. **Dependency risk.** pmetal is one developer's project. It's impressive and signed,
   but single-maintainer risk is real. If adopted deeply, what's the fallback plan —
   pin a commit and accept no updates, or maintain readiness to migrate to mlx-lm + Ollama
   if pmetal goes stale?

5. **Manifold-Constrained Hyper-Connections (`pmetal-mhc`).** This maps directly onto
   the JPmHC paper (`2602.18308`) in the context folder. Are you interested in running
   mhc as a Phase 6 training experiment, or does it stay a curiosity?

---

## mlx-flash

1. **mlx-flash vs. flash-moe philosophically.** Same problem, different tradeoff:
   mlx-flash is framework-integrated + zero quality loss + predictive scheduling;
   flash-moe is bespoke + aggressively quantized + manual pipeline. Which style should
   Linus prefer when forced to choose?

2. **The native-precision claim on M1 Max.** Nemotron-30B on a 16 GB Air at bit-perfect
   parity is the README headline; the unstated question is *tok/s*. Worth a small
   benchmark to see what native-precision streaming costs on your hardware before
   committing to it as a serving path.

3. **Streaming + 1-bit as a composite path.** Running a 1.58-bit 30B (hypothetical
   Ternary-Bonsai-30B) with mlx-flash streaming is combinatorially more memory-efficient
   than either alone. Is this a Phase 6d experiment target, or does it wait until PrismML
   trains a large ternary Bonsai?

4. **Hybrid KV cache as a Linus feature.** The 128-token FP16 + older-8-bit
   disk-offloaded KV cache pattern is useful even without weight streaming. Should it be
   part of Phase 2a's minimum feature set, or deferred until a concrete long-context use
   case surfaces?

---

## flash-moe

1. **The 32 GB flash-moe analogue.** flash-moe ran ~400B on 48 GB. On the M1 Max 32 GB
   with a slower SSD, the comfortable ceiling is probably a ~100–150B MoE or a 30–50B
   dense-1-bit model. Want me to sketch a concrete Phase 6d target ("get MODEL X running
   at N tok/s on Dan's hardware") once Phase 1b closes?

2. **"Trust the OS" as a Linus design principle.** The flash-moe finding that every
   custom cache lost to the OS page cache is a strong generalizable principle. Explicitly
   promote it to a Linus engineering convention in CLAUDE.md, or keep it implicit?

3. **Autoresearch + flash-moe methodology fusion.** Phase 7c's overnight iteration loop
   is essentially the flash-moe experiment log run as a supervised AI loop against a
   tok/s target. Is this the first concrete use case for the Phase 3b parallel-agent
   infrastructure, or does it stay a later-phase thing?

4. **Objective-C / Metal-direct as an escape hatch.** If Linus ever needs
   flash-moe-level control — say, to beat pmetal on a specific workload — we'd be writing
   Obj-C and Metal by hand. That's a skill Dan doesn't currently have. Is acquiring it a
   Phase 7+ bet, or ruled out in favor of "whatever pmetal supports"?

---

## ANE

1. **Does the ANE existence proof change Phase 1b?** The pmetal evaluation plan currently
   treats ANE serving as a nice-to-have. Given pmetal ships with an ANE pipeline and this
   repo shows training is viable, should "ANE prefill + GPU decode" become an explicit
   benchmark configuration alongside plain Ollama vs. pmetal-GPU?

2. **Read-or-defer on the Maderix substack series.** The three articles are arguably the
   best documentation of the ANE that exists. Worth reading now, or defer to whenever an
   ANE decision is actually forced?

3. **Private-API risk appetite for Linus.** pmetal uses some of the same `_ANEClient`
   surface. That's a fine bet for a personal project but means macOS updates can break
   things. Happy to document that risk in DECISIONS.md when Phase 2's inference backend
   is chosen, or would you prefer a policy of "ANE-only if officially supported API
   exists"?

4. **Reverse-engineering as a Linus practice.** This repo demonstrates the value of
   treating Apple's private APIs as fair game for research. Is that a stance you want
   Linus to inherit, or keep Linus strictly on public APIs (CoreML, MLX, Metal) and let
   pmetal carry any private-API risk?

---

## Bonsai-demo

1. **Bonsai-8B and Ternary-Bonsai-8B in the Phase 1c baseline sweep?** This is the
   cheapest test of the 1-bit quality-cost frontier on your hardware. Happy to write a
   smoke-test spec for it.

2. **PrismML's `llama-server` as the interim OpenAI-compatible endpoint for the Phase 1e
   Maestro/Worker loop?** It ships today and routes to the Metal backend, buying time
   before `pmetal serve` is evaluated. The alternative is staying on Ollama and accepting
   that Ollama does not yet have `Q1_0` Metal kernels.

3. **Native-1-bit vs. distilled-to-1-bit (BitDistill) as Linus's fine-tuning path.**
   Bonsai trained from scratch with 1-bit / ternary weights. BitDistill takes an FP16
   model and distills down. Different risks. Do you want to run both experiments in
   parallel at Phase 6, or pick a lane?

4. **PrismML's llama.cpp and MLX forks as upstream-tracking dependencies.** They've
   committed to upstreaming; do we track their forks as study references and adopt the
   upstreamed kernels once merged, or pin a specific fork commit as a Linus dependency?

---

## BitNet

1. **How aggressively do we want to chase 1.58-bit on Apple Silicon as a first-class
   path?** Bitnet.cpp's ~7 tok/s at 100B on M2 Ultra implies a ~40–50B ternary model
   could be feasible on the M1 Max. Is that compelling enough to put an "MLX/Metal
   ternary runtime" experiment earlier in the roadmap (Phase 2–3 experimental branch)
   rather than waiting for Phase 6+?

2. **BitNet Distillation as a fine-tuning path.** Would you accept a 1.58-bit distilled
   Qwen2.5 variant as the Phase 6 deliverable if it beats a FP16-LoRA'd counterpart on
   Dan task suite, given it sacrifices some smoothness in exchange for much larger
   effective capacity?

3. **Ternary base models vs. converted models.** Native ternary training (BitNet b1.58
   2B4T) vs. post-hoc distillation (BitDistill) vs. post-hoc quantization (run FP16 Qwen
   at 2-bit via bitnet.cpp-style kernels) — three different philosophies. Any strong prior?

4. **Hardware bet.** The BitNet papers repeatedly call for "new hardware designed for
   1-bit LLMs." The ANE is closer to that than Metal is. Is investing in ANE kernel
   development (via pmetal or directly) worth Linus dev time in Phase 2–3, or does it
   stay a Phase 7+ project?

---

## cline

1. **Harness plurality.** You'll plausibly run Claude Code (Maestro), Cline (VS Code
   worker tasks), claw-code-local (terminal tasks), and openclaw (chat/voice) — all
   pointing at Linus. That's four front-ends. Is that the intended end-state, or is there
   a desire to converge on fewer once one proves out?

2. **MCP as the extensibility substrate.** Cline, openclaw, and pmetal all speak MCP.
   Adopting MCP as the tool-registration surface inside Linus is a plausible Phase 3 move
   — it means tools registered once are visible in all harnesses without custom glue.
   Architecturally cleaner, but carries MCP's complexity. Want to revisit this decision
   explicitly in Phase 3?

3. **Variant prompts for small / 1-bit models.** Cline's `xs` variant exists because
   tiny models need substantially different prompts. When Linus's Phase 6 produces a
   fine-tuned 1-bit model, it will likely need its own variant too. Plan for this in Phase
   7 skills design, or defer?

4. **Browser use.** Cline's browser tool relies on Anthropic's Computer Use — a
   frontier-model capability. Local models plausibly can't drive it reliably. Is
   browser-based agentic work a Linus use case, or does it stay Maestro-only?

---

## claw-code

1. **Is "Linus has its own CLI harness" a Phase 5 goal, or OK to stay on Claude Code +
   claw-code-local forever?** ROADMAP 5c mentions a ~500-line custom terminal agent as a
   fallback. The fork handles the local-model case today, so this may be a dead
   requirement.

2. **ACP/Zed as a Linus surface.** claw-code's ACP ambitions overlap with any future
   Linus-in-Zed idea. Not a 2026-current path, but worth flagging if you care about the
   Zed ecosystem.

3. **Rust as a Linus language.** claw-code, claw-code-local, and pmetal are all Rust. If
   Linus stays Python-first for orchestration but has Rust-based components (pmetal
   bindings, future CLI), is that fine, or do you want a stated "one orchestration
   language" policy?

4. **Read `PHILOSOPHY.md` now or defer?** It's short; likely contains framing worth
   lifting into Linus's own docs if relevant. I can pull excerpts into VISION.md if
   useful.

---

## claw-code-local

1. **Phase 5c deferred-or-done?** claw-code-local essentially already solves the "Linus
   terminal surface" requirement. The roadmap's 5c fallback ("a small custom terminal
   agent (~500 lines of Python)") may be dead on arrival. Happy to mark Phase 5c as
   "adopt claw-code-local" in the roadmap if you agree.

2. **Skill parity.** The fork exposes Claude Code's `/skills` command, which means
   Anthropic-shaped `SKILL.md` files work inside it. That aligns with Linus's Phase 7
   skills direction. Want a Phase 1e smoke-test that runs a trivial Linus-defined skill
   through claw-code-local against Ollama?

3. **Upstream drift.** claw-code-local is a thin fork. If upstream adds meaningful
   features (ACP/Zed mode, MCP refinement), should Linus maintain its own mini-patches on
   top, or wait for the fork to rebase? Informs the dependency-tracking pattern we adopt.

4. **Behavioral parity with local models.** The fork ships the patches but doesn't
   validate *which* local models produce usable tool calls inside claw-code's templates.
   This is the kind of empirical question the Dan task suite is built for. Want the Phase
   1d suite extended with a "tool-use-through-claw-code" axis?

---

## openclaw

1. **Which openclaw surfaces actually matter?** Full channel sprawl isn't the goal. A
   reasonable minimum is macOS menu bar + voice wake + Canvas + WebChat; iOS node if you
   want phone access. Am I reading your priorities right, or do you want any specific
   messenger channel wired up?

2. **Voice wake as a Phase 5 feature.** openclaw supports macOS/iOS voice wake and
   Android continuous voice. Is voice a Phase 5 requirement, or defer to Phase 8 native
   app? Voice changes the usability story substantially.

3. **Canvas as a KnowledgeBase surface.** openclaw's Canvas is an agent-driven visual
   workspace. Plausible Phase 5 experiment: have Linus render paper clusters, cluster
   labels, or knowledge-graph subgraphs in Canvas. Is that the kind of interaction you
   want, or is text/Streamlit sufficient?

4. **Skill symlink strategy.** Keeping Linus skills in `src/linus/skills/` and
   symlinking into openclaw's workspace is one option; copying is another; putting skills
   only in openclaw and having Linus read from openclaw's workspace is a third.
   Preference?

5. **Private-API / local-model first-class support.** openclaw's model config assumes a
   subscription. Confirming it works cleanly against an OpenAI-compat local endpoint with
   no rate-limit drama is a Phase 5 smoke-test worth budgeting for.

---

## autoresearch

1. **First real use of autoresearch methodology.** Phase 6d or Phase 1b's pmetal
   evaluation? The pmetal LoRA trial is a natural first loop: Maestro (me, or you + me)
   writes the `program.md`, Worker iterates overnight, we wake up to a benchmark table.
   Low risk, exercises the whole Maestro/Worker protocol on real work.

2. **Metric for Linus's loops.** Karpathy uses val_bpb for its architecture-fairness.
   Linus's analogue is Dan task suite score, which is higher-variance and
   slower-per-evaluation. Are we willing to lengthen the per-experiment budget (30 min+)
   to get the higher-signal metric, or keep short loops on proxy metrics?

3. **`program.md` as SKILL.md.** autoresearch's `program.md` is essentially a
   lightweight skill. Promoting it to the Anthropic `SKILL.md` convention makes it
   portable between Claude Code and Linus. Worth doing in Phase 7, or premature?

4. **Read the Karpathy tweets linked in the README.** Short. Likely contain framing worth
   surfacing in VISION.md if you want Linus to inherit some of the "research org as code"
   posture explicitly.

---

## project-nomad

1. **Phase 4 scope ambition.** Roadmap Phase 4 is deliberately bounded to Kiwix +
   PMTiles + Qdrant + dataset version tracking. NOMAD hints at more (Kolibri for
   education content, FlatNotes for notes, CyberChef for data tooling). Do any of those
   belong in Linus Phase 4, or is notes-taking/data-tooling a non-goal for a personal
   research assistant?

2. **Kiwix ZIM selection.** The practical question that NOMAD resolves by asking the
   user: which Wikipedia subset? Full English is ~100 GB; Simple English is ~1 GB; there
   are topical ZIMs (medical, Wikipedia-for-schools). Any preference for genomics /
   biochem / chemistry-focused ZIMs if they exist?

3. **PMTiles regions.** Offline maps are only useful for specific places. Oregon + PNW
   makes sense given context. Any other regions (fieldwork sites, travel) matter?

4. **Qdrant-in-Docker vs. native vector store.** NOMAD uses Qdrant because it's a
   general-purpose offering; Linus's KnowledgeBase currently uses numpy-based similarity
   search. Are we promising Qdrant in Phase 4 only if benchmarks force it, or do you want
   it regardless for a smoother long-term path?

5. **Explicit sovereignty statement in VISION.md.** NOMAD's phrasing ("Knowledge That
   Never Goes Offline," zero telemetry, no authentication by default because the network
   boundary is the trust boundary) is crisper than Linus currently articulates. Worth
   lifting into VISION.md?
