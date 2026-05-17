---
title: "The Bitter Lesson"
source: incompleteideas.net/IncIdeas/BitterLesson.html
authors: Rich Sutton
affiliation: University of Alberta / DeepMind (at time of writing)
date: 2019-03-13
pdf: ../../context/notes/bitter_lesson.pdf
tags:
  [
    foundational,
    classic,
    sutton,
    bitter-lesson,
    compute-vs-knowledge,
    search-and-learning,
    scaling,
    methods-philosophy,
    historical-anchor,
    group-foundational,
  ]
---

# The Bitter Lesson

## TL;DR

Rich Sutton's 2019 two-page essay is the **canonical formulation of the compute-versus-knowledge tension in AI research** — short enough to read in five minutes, deep enough to organize seven decades of AI history. The argument is precise: over 70 years of AI research, general methods that leverage computation have been ultimately the most effective, by a large margin. Moore's-law-driven exponential growth in available compute means that **leveraging human knowledge of the domain helps in the short term but plateaus or inhibits progress in the long term**, because human-knowledge-engineered methods are typically less amenable to scaling with compute. Sutton walks through four illustrative cases — computer chess (Deep Blue 1997), computer Go (AlphaGo 2017), speech recognition (HMMs and then deep learning displacing phoneme-based approaches), computer vision (convnets displacing SIFT/edges/generalized-cylinders) — and notes that the pattern is the same: researchers invest in human-knowledge-engineered methods, those methods plateau, and then a more general method based on **search** and **learning** at scale wins, often to the dismay of the human-knowledge-engineered camp. The two scalable primitives are **search** (Deep Blue's minimax depth, AlphaGo's MCTS) and **learning** (self-play in AlphaZero, statistical methods in NLP, deep learning broadly). The "bitter" framing: the lesson is bitter because the eventual success is over a favored, human-centric approach. The closing argument is the more substantive one: the actual contents of minds are tremendously, irredeemably complex, and we should stop trying to find simple ways to think about space, objects, multiple agents, or symmetries; we should instead build **meta-methods that can find and capture arbitrary complexity**. We want AI agents that can discover like we can, not which contain what we have discovered. For Linus, this essay is the **single most-cited foundational substrate** for the compute-and-data-scaling discipline that organizes everything downstream — the Algorithm (Musk via McNeill, in CLAUDE.md), Blitzscaling, the Maestro/Worker discipline (push well-specified tasks to scalable Workers rather than to maestro attention), the engineering convention "trust the OS page cache" (DEC-0027, where measurement-driven scaling beat the human-knowledge-engineered LRU cache), the flash-moe study, and the broader Phase 6 fine-tuning lane all instantiate variants of the bitter-lesson discipline. It belongs at the **REFERENCE-category tier** of the corpus, cross-cited from agentic-systems-synthesis.md and infra-foundations-synthesis.md and Linus's own VISION/ARCHITECTURE write-ups.

## The problem (in plain language)

Sutton's essay is short enough to summarize at full fidelity. The problem he names: AI researchers, in seeking incremental improvements over a 1-3 year research-project timescale, gravitate toward methods that **leverage human knowledge of the domain** because human-knowledge methods tend to improve quickly in the short term. The cost is structural: human-knowledge methods complicate the architecture in ways that make them less amenable to scaling with the (exponentially growing) compute budget. Over a longer timescale — 5-20 years — the compute budget for an AI agent grows by orders of magnitude (Moore's law and its generalization to dollar-cost per unit of computation). Methods that scale arbitrarily with compute eventually overtake the human-knowledge methods, often dramatically.

The bitter framing is psychological: the eventual success of a general method is **bitter** for the human-knowledge community because the success is "over a favored, human-centric approach." Researchers want methods based on human input to win; when they don't, the disappointment is real, and the lesson is often "incompletely digested" because of the favored-approach bias.

The four illustrative cases:

**Computer chess (1997).** Deep Blue beat Kasparov with massive deep search plus specialized hardware. Computer-chess researchers who had pursued human-knowledge-based methods (chess-position evaluation functions encoding human chess theory) dismissed it as "brute force" and "not how people play chess." But the search-based approach was vastly more effective.

**Computer Go (~2017).** Initial effort directed toward human-knowledge encoding (joseki, ko fight handling, etc.). Search applied effectively at scale, plus learning by self-play to learn a value function (as in many other games), produced AlphaGo and AlphaZero. The same pattern as chess, delayed by 20 years for harder branching factor reasons.

**Speech recognition (1970s-2010s).** DARPA 1970s competition pitted human-knowledge methods (phonemes, vocal tract models, lexicons) against statistical methods (HMMs). Statistical methods won; this propagated through NLP over decades; deep learning further reduced human-knowledge reliance.

**Computer vision (1980s-2010s).** Early methods used edges, generalized cylinders, SIFT features. Modern deep-learning convnets use only convolution and certain invariances, and perform vastly better.

The pattern claim:

1. AI researchers often try to build knowledge into their agents.
2. This always helps in the short term, and is personally satisfying to the researcher.
3. In the long run, it plateaus and even inhibits further progress.
4. Breakthrough progress eventually arrives by an opposing approach based on **scaling computation by search and learning**.

The closing point, often less-quoted but deeper: the actual contents of minds are tremendously, irredeemably complex; we should stop trying to find simple ways to think about the contents of minds (space, objects, agents, symmetries) and instead build **meta-methods that can find and capture this arbitrary complexity**. We want AI agents that can discover like we can, not which contain what we have discovered. Building in our discoveries only makes it harder to see how the discovering process can be done.

## What it proposes

The essay does not propose methods — it proposes a **methodological discipline**: when designing AI systems, prefer methods that scale with compute over methods that encode human knowledge of the domain. Search and learning are the two specific primitives that scale; everything else is human-knowledge engineering and is likely to plateau.

Implicit in the discipline: budget research effort accordingly. A 1-3 year research project on a human-knowledge-engineered method may produce a publishable result; a parallel effort on a general method that scales may not produce a publishable result on the same timeline but is more likely to produce the **long-term breakthrough**.

## Key takeaways for Linus

**Calibration 1: the Algorithm (Musk via McNeill) is the bitter lesson applied at the engineering-decision level.** CLAUDE.md's Algorithm ordering — question every requirement, delete every step, simplify, accelerate cycle time, automate last — is the bitter lesson at the engineering-discipline level. Both argue against premature investment in domain-specific complexity (don't build the cache before you measure that one is needed; don't encode the chess strategy before you've tested search at scale). They're independent restatements of the same insight at different scales. Linus's design discipline should treat the bitter lesson and the Algorithm as **mutually reinforcing**.

**Calibration 2: search and learning as the two scalable primitives organize Linus's roadmap.** Phase 1 baselines (smoke-test gates, benchmarks), Phase 2 orchestration (Worker dispatch with cot_budget + memory_mode), Phase 6 fine-tuning (LoRA on domain corpus), Phase 8 substrate experiments (Hope/CMS, minGRU+BitNet, COCONUT) all instantiate variants of **scale-with-compute** rather than **encode-human-knowledge**. The bitter lesson is the underlying organizing principle. Linus's documentation should make this explicit: VISION.md and ARCHITECTURE.md should reference the bitter lesson as the underlying methodology, not just as a passing citation.

**Calibration 3: the flash-moe study and "trust the OS page cache" (DEC-0027) are the canonical Linus instances.** The flash-moe finding — that a 9.8 GB Metal LRU cache wrapping mmap'd weight shards **hurt** throughput by 38%, and deleting the cache restored performance — is the bitter lesson realized in Linus engineering. The human-knowledge intuition was "we should cache weight shards in fast memory because that's how you scale inference"; the bitter-lesson reality was "the OS already does this optimally; your human-knowledge cache fights the OS and loses." DEC-0027's "trust the OS page cache" engineering convention is the bitter lesson at the systems-engineering scale. Linus's documentation should cite this connection explicitly.

**Calibration 4: meta-methods over methods.** Sutton's closing argument — build meta-methods that can find and capture arbitrary complexity — is the bitter lesson at the architecture-design scale. For Linus's Phase 2 orchestration layer, this argues that the **orchestration backend itself** is the scalable meta-method, while specific tools and skills are domain-specific implementations that may come and go. The orchestration layer's value is in the patterns (Worker dispatch, memory mode, cot_budget, audit log) that allow many domain-specific skills to be composed; the specific skills are the "things we have discovered" that Sutton warns against over-investing in.

**Calibration 5: Maestro/Worker discipline as a bitter-lesson realization.** The CLAUDE.md Maestro/Worker protocol — push well-specified tasks to local Workers; reserve Maestro attention for taste-level decisions — is the bitter lesson applied to the human-attention budget. Maestro attention is a scarce, expensive resource (analogous to human-knowledge engineering); Worker compute is an abundant, cheap resource (analogous to search and learning at scale). The discipline of preferring Worker dispatch where possible is the bitter-lesson discipline applied to Dan's time. The Phase 3 multi-agent spawner (DEC-0050) and the parallel-by-default convention (CLAUDE.md) are the operational realization.

## What's reusable in Linus

**Foundational citation in VISION.md and CLAUDE.md.** The bitter lesson should be cited explicitly as one of the foundational methodologies for Linus, alongside the Algorithm, Blitzscaling, and the Maestro/Worker discipline. The fold-in is a single paragraph in VISION.md (or in CLAUDE.md's Guiding Principles section) that names the bitter lesson as the underlying methodology, with a citation to this paper-note.

**Agentic-systems-synthesis foundational thread.** The synthesis already covers Maestro/Worker, the Algorithm, and parallel-by-default as engineering disciplines. Adding the bitter lesson as the underlying methodological substrate strengthens the synthesis. Suggested fold: a paragraph in the synthesis's discussion of agent-design discipline citing the bitter lesson as the foundational substrate.

**Infra-foundations-synthesis foundational thread.** The synthesis covers the Apple-Silicon-specific engineering conventions (RoFormer, RMSNorm, GLU variants, flow matching). The bitter lesson is the methodological substrate for "prefer general methods over domain-specific encoded knowledge." Suggested fold: a citation in the synthesis's discussion of why specific architectural primitives have won (general convolution + invariance vs. SIFT; general attention vs. encoded language structure).

**DEC-0027 substrate citation.** DEC-0027's "trust the OS page cache" + "public APIs only" + "multi-language stance" all instantiate the bitter-lesson discipline. The DEC should cite the bitter lesson as the underlying methodological substrate.

**Phase 6 fine-tuning lane motivation.** Phase 6 commits to LoRA on Dan's domain corpus. The bitter lesson argues that this is the right phase scope — fine-tuning is the **learning** primitive applied to a specific domain corpus, rather than encoding human-knowledge rules about the domain. The Phase 6 spec should reference the bitter lesson as the underlying methodological substrate.

**Phase 8 substrate-experiments motivation.** Phase 8's substrate experiments (Hope/CMS, minGRU+BitNet, COCONUT per DEC-0041/0042 and the Behrouz et al. paper-note 2512.24695v1) are all bets on **architectural primitives that scale with compute** rather than on domain-specific human knowledge. The bitter lesson is the underlying motivation. The Phase 8 substrate-experiments spec should cite explicitly.

## What's NOT applicable / hype filter

**The bitter lesson is not a license to ignore domain knowledge.** Sutton's argument is that **encoding** human knowledge in the architecture is the failure mode, not that human knowledge is useless. Human knowledge remains valuable for: (1) framing the problem (what is the right task, what are the right inputs); (2) evaluating the output (what counts as a correct solution); (3) curating the training data (which examples are relevant). Linus's Phase 7 biology Workers benefit enormously from Dan's biology PhD-level domain knowledge — for framing the right tasks, for curating training data, for evaluating outputs. The bitter lesson argues against **building chess theory into the chess agent**, not against having a domain expert specify what counts as winning at chess.

**The bitter lesson is a long-timescale argument.** Sutton's evidence is multi-decade: chess from 1950s-1997, speech from 1970s-2010s, vision from 1980s-2010s. On shorter timescales (1-3 years), human-knowledge-engineered methods are often the right choice because the compute budget is not yet large enough for the general method to overtake. Linus's near-term roadmap (Phase 1-3) appropriately prioritizes **engineering discipline over substrate replacement** — most of Phase 1-3 is conventional Worker dispatch with Ollama + KnowledgeBase, not a substrate experiment.

**"Search and learning" are specific scalable primitives, not generic encouragement.** Sutton is precise: search (in the minimax / MCTS / planning sense) and learning (in the gradient-descent / self-play sense) are the two primitives that scale arbitrarily with compute. Other primitives (e.g., reasoning, retrieval, symbolic manipulation) may scale to some degree but have not been demonstrated to scale arbitrarily. Linus's documentation should be careful not to over-claim that "everything scales with compute" — only specific primitives have been demonstrated to.

**The essay does not address data scaling explicitly.** Modern foundation-model practice (Chinchilla scaling laws, the Hoffmann et al. 2022 finding that compute-optimal training requires both more parameters and more data in tandem) supplements Sutton's argument with the observation that **data is also a scalable input**. The bitter lesson essay predates the Chinchilla framing; both should be cited together when arguing for the scale-with-compute discipline.

**The "incomplete digestion" critique is rhetorical, not architectural.** Sutton's observation that the bitter lesson is "often incompletely digested" because of the favored-approach bias is psychological commentary, not an architectural claim. Linus's documentation should cite the substantive argument (compute beats encoded human knowledge over long timescales) rather than the psychological framing (researchers are personally invested in the favored approach).

## Connections

The primary fold is into [`../syntheses/agentic-systems-synthesis.md`](../syntheses/agentic-systems-synthesis.md). The synthesis already covers Maestro/Worker, the Algorithm, parallel-by-default, and similar engineering disciplines. The bitter lesson is the underlying methodological substrate that organizes them. Suggested fold: a one-clause citation in the synthesis's engineering-discipline section.

The secondary fold is into [`../syntheses/infra-foundations-synthesis.md`](../syntheses/infra-foundations-synthesis.md). The synthesis covers architectural primitives (RoFormer, RMSNorm, GLU variants, flow matching) that have won in the field. The bitter lesson is the underlying methodological substrate for why those general primitives have won over domain-specific encoded alternatives.

Cross-links to existing documents that share concerns:

- VISION.md / CLAUDE.md — foundational Linus methodology where the bitter lesson belongs alongside the Algorithm and Blitzscaling.
- DEC-0027 (Linus practice stance batch) — the "trust the OS page cache" + "public APIs only" + "multi-language stance" engineering conventions that instantiate the bitter lesson.
- [`flash_moe.md`](flash_moe.md) — the canonical Linus instance of the bitter lesson realized in engineering (the 9.8 GB cache that hurt throughput).
- [`raschka_2025_big_llm_architecture_comparison.md`](raschka_2025_big_llm_architecture_comparison.md) — the modern transformer-architecture survey that documents the convergence of architectural choices, broadly consistent with the bitter lesson.
- [`bandaru_transformer_design_guide_pt2_modern_architecture.md`](bandaru_transformer_design_guide_pt2_modern_architecture.md) — the transformer-design-guide companion.
- [`2203.15556v1.md`](2203.15556v1.md) — Chinchilla scaling laws, the data-scaling complement to the bitter lesson's compute-scaling argument.

Phase mapping: foundational methodology (cross-cutting); Phase 6 fine-tuning lane motivation; Phase 8 substrate-experiments motivation; engineering-discipline anchor for DEC-0027 and related conventions.

## Open questions for Dan

1. **Cite the bitter lesson explicitly in VISION.md and CLAUDE.md?** Currently CLAUDE.md cites the Algorithm and Blitzscaling but not the bitter lesson. Adding it would strengthen the methodological lineage with a five-minute foundational read.

2. **Cite as substrate in DEC-0027 and related ADRs?** DEC-0027's engineering conventions all instantiate the bitter lesson. Adding the citation would strengthen the ADR's lineage.

3. **Update the agentic-systems synthesis to cite the bitter lesson as the methodological substrate?** Currently the synthesis covers the engineering disciplines but doesn't name the underlying methodology. A single paragraph would suffice.

4. **Read the broader Sutton corpus.** The bitter lesson is the most-cited Sutton work, but Sutton's broader work (the RL textbook, the "alberta plan," the "world model" papers) is foundational for many of the substrate-experiment threads. Worth a deeper Sutton corpus pass at some point?

5. **Compare to Karpathy / Hinton / Bengio recent statements on compute-vs-knowledge.** The bitter lesson is a 2019 statement. Modern restatements (Karpathy's "software 2.0," Hinton's various 2024-2025 talks) may have updated nuances worth tracking. Worth a brief survey?

6. **The "meta-methods over methods" framing — applied to Linus's tool registry.** Sutton's closing argument suggests that Linus's tool registry should prefer **patterns** (typed-structured-prediction, paired physics-based validators, compute-to-data deployment) over **specific tools** (this CVAE, this protein language model). The registry's architecture should make pattern-level abstractions first-class. Is this already implicit in DEC-0046, or worth surfacing as a future DEC?
