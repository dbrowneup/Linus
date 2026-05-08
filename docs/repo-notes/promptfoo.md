# promptfoo (`promptfoo/promptfoo`)

## 1. Purpose and scope

Promptfoo is a production-grade open-source CLI and Node.js library for evaluating and red-teaming LLM applications.
Supports comparing models side-by-side (OpenAI, Claude, Ollama, Bedrock, etc.), running automated test suites,
generating security vulnerability reports, and integrating into CI/CD pipelines. Now part of OpenAI (remains MIT
licensed and open source). For Linus, this is the **benchmarking + validation layer**: smoke-test Dan's tasks before
rolling out new prompts, model switches, or tool changes; detect regressions; measure task-specific accuracy and
latency.

## 2. Architecture summary

Promptfoo is a TypeScript/Node codebase (Vite build, React 19 frontend, SQLite backend via Drizzle ORM). Users define
evaluations in YAML: test cases (inputs), expected outputs/assertions, and model configurations. The CLI runs evals
(outputs to JSON), compares results, and serves a web viewer (React dashboard on localhost:3000). Providers are
pluggable adapters for each LLM API (OpenAI, Anthropic, local Ollama, custom). Assertions include equality checks,
semantic similarity (via embeddings), custom LLM grading, and security scanners (red-teaming plugins: prompt injection,
jailbreak, toxicity, etc.). Test results include token counts, latency, costs, and detailed traces. Pre-commit hook
(Biome linter + Prettier) enforces formatting.

## 3. What's reusable in Linus

Promptfoo is the direct fit for **Linus's Dan Task Suite** (the benchmarks/ folder). Build a promptfooconfig.yaml that
tests Linus prompts and models against the 50-100 task cases Dan cares about (e.g., genomics Q&A, code-generation,
summarization). Reuse Promptfoo's Ollama provider to test against local workers (Qwen2.5-Coder, Mistral-7B, future
fine-tuned Linus). The JSON output (success/score/error per test) feeds automated regression detection and Phase 1
baseline measurements. Red-teaming plugins (prompt injection, refusal jailbreaks) are valuable for safety validation of
Linus tools. Custom graders (via `gradeScriptFence`, hand-scored fixtures) allow Dan-specific metrics (e.g., "did this
code compile?", "did this analysis follow best practice?").

## 4. What's inspiration only

Promptfoo's web UI is polished but optional for Linus Phase 1 — the JSON output is enough for bulk analysis. The
Bedrock/Azure/commercial-API support is useful reference but not urgent for local Linus. Code-scanning GitHub Actions
integration is inspirational for CI/CD safety gates (Phase 3+). The team's 10M+ user case studies (linked in docs) are
valuable evidence that the tool scales to production scenarios.

## 5. What's incompatible or out of scope

Promptfoo is not a training framework; it measures, not improves. For Phase 6 fine-tuning, Linus needs pmetal or mlx-lm,
not promptfoo. Node.js/npm dependency adds a second language runtime; Linus's Python-first stack means promptfoo runs
alongside the core (not inside). The tool has a learning curve; Dan's task suite will need careful definition and
maintenance. Costs scale with eval size (10 configs × 50 tests × 5 model variations = 2500 API calls if using remote
models); local Ollama avoids costs but has latency tradeoff.

## 6. Recommendation: **Integrate (Phase 1 close)**

Promptfoo is ready to use now as a standalone tool for Phase 1 baseline measurement and Phase 2a regression detection.
No waiting required. Set up a smoke test: (1) define 10 representative cases from Dan's task suite in YAML, (2) test
against Ollama (Qwen2.5 or Mistral running locally), (3) export JSON results, (4) measure mean latency and task
accuracy. Use this baseline for all future model/prompt changes. As Linus scales to multi-agent (Phase 3), use
red-teaming to scan for prompt injection in tool descriptions.

## 7. Questions for Dan

1. **Dan Task Suite scope.** Start with 20-50 representative cases or go for the full 100-item suite now? Smaller suite
   iterates faster; larger suite catches more regressions but has slower iteration.
2. **Custom graders vs. built-in assertions.** For genomics/chemistry Q&A, does Linus need custom Python graders (e.g.,
   compare extracted gene names to a reference set), or do semantic similarity + equality checks suffice?
3. **Multi-model comparison.** Phase 1 baseline: single model (Ollama Qwen2.5-Coder) or compare Qwen vs. Mistral vs.
   local Claude? (Latter is heavier but more informative.)
4. **Red-teaming scope.** Which attack vectors matter most for Linus Phase 1? (e.g., prompt injection in KB queries,
   jailbreak attempts on tool descriptions, data exfiltration via search?
