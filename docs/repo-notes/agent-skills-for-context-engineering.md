# Agent Skills for Context Engineering (`muratcankoylan/Agent-Skills-for-Context-Engineering`)

## 1. Purpose and scope

This is a curriculum of 14 platform-agnostic agent skills teaching context engineering: the discipline of curating what enters an LLM's context window to maximize signal within fixed attention budget. Skills cover context fundamentals (lost-in-middle, degradation patterns, compression), architecture (multi-agent patterns, memory systems, tool design), and operations (context optimization, evaluation, LLM-as-judge). Unlike Superpowers (which shapes workflow), these skills teach domain knowledge — what context quality means, why bigger windows hurt, and how to detect when an agent is failing due to context scarcity. For Linus, this is high-leverage intellectual capital: Dan's Phase 2a orchestration backend will route task context, manage session history, and decide what to brief each Worker; these skills provide the theory behind that routing.

## 2. Architecture summary

14 skills, each a ~300–400 line markdown file with YAML frontmatter (name, description, trigger keywords), main content (conceptual framing + gotchas), and optional reference docs and Python pseudocode examples. Progressive disclosure: agents load skill index at startup and activate full content when task language matches triggers (e.g., "compress context" → activates compression skill). Skills are platform-agnostic (Claude Code, Cursor, GitHub Copilot, Open Plugins standard). Four example projects demonstrate skill composition: digital-brain-skill (personal operating system), llm-as-judge-skills (TypeScript evaluation library), book-sft-pipeline (LoRA fine-tuning on author style), x-to-book-system (multi-agent synthesis). Emphasis on evidence and measurable outcomes — skills direct readers toward evaluation frameworks rather than opinionated mandates.

## 3. What's reusable in Linus

The context-degradation skill is directly applicable to Phase 2a: teaches lost-in-middle phenomena, attention U-curves, and practical mitigation (summarization, windowing, reranking). Linus can use this to decide when to summarize long session history vs. keeping it verbatim. The memory-systems skill covers short-term (session state), long-term (persistent knowledge graph), and graph-based designs — Linus's KnowledgeBase submodule is a long-term memory system; this skill provides the framing for how Workers query it. The tool-design skill (minimize complexity, reduce tokens, compose orthogonally) applies to MCP tool definition in Phase 2a. The evaluation skill teaches how to measure agent success empirically; Dan's benchmarks directory should reference these patterns. The hosted-agents skill covers sandboxed execution and multi-client interfaces — potentially useful if Linus eventually exposes Workers to multiple frontends.

## 4. What's inspiration only

The BDI mental states skill (Beliefs-Desires-Intentions formalism) is theoretically sound but overkill for Linus Phase 1-2; useful as a reference if Dan ever wants to build formal agent introspection. The latent-briefing skill (KV-cache compaction handoff between agents) requires controllable worker runtime (e.g., Ollama with lorapack) — ahead of Phase 3's immediate priorities. The advanced-evaluation skill (LLM-as-judge, bias mitigation) is high-value for future benchmarking but requires substantial infrastructure (multiple Judge instances, rubric management); Phase 1 smoke tests are simpler.

## 5. What's incompatible or out of scope

These are conceptual skills, not implementations — they teach principles without shipping code. The digital-brain example uses append-only JSONL (agent-friendly but manual) rather than a structured graph store. The book-sft-pipeline example assumes tinker (LoRA service); Linus uses mlx-lm or pmetal locally, so the pipeline needs porting. The skills are deliberately vendor-neutral; applying them to Linus requires concrete translation to MLX/Ollama architecture.

## 6. Recommendation: **Study (Phase 1→2 bridge)**

Read context-degradation, memory-systems, and tool-design fully in Phase 1 closing (as theoretical input to ARCHITECTURE.md). Reference evaluation and advanced-evaluation when planning Phase 1 benchmarks. Do not implement BDI or latent-briefing yet; defer to Phase 3. Extract the trigger-keyword pattern from the repo (how skills detect activation) as a reference for Linus's own skill system.

## 7. Questions for Dan

- **Context windowing strategy.** The lost-in-middle / U-curve phenomenon is real; should Linus adopt summarization for long sessions (simpler) or multi-turn reranking (smarter)? What's Dan's tolerance for losing detail in old conversation?
  _Partially resolved (DEC-0032, see [answered-questions.md](../questions/answered-questions.md)): Phase 2 default is
  16K in-context cap with overflow routed through the episodic store via summarization-or-retrieval; reranking deferred._
- **Memory-graph design pattern.** Should Linus's KnowledgeBase expose a flat list of documents, or teach Workers to query the graph structure (functions, classes, call chains)? How much graph literacy should Workers be expected to have?
- **Tool complexity budget.** How many MCP tools should Linus expose to Workers before diminishing returns kick in? The tool-design skill suggests orthogonality; is there a "one tool per job" rule Linus should follow?
- **Evaluation coverage.** Dan's benchmarks (Phase 1 task suite) should probably measure context-efficiency (tokens used, tool calls made) alongside accuracy. Should Phase 1 close with eval framework that tracks these, or is accuracy-only acceptable for now?
