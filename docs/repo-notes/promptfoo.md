# promptfoo (`promptfoo/promptfoo`)

_Refreshed 2026-05-18 against upstream HEAD e01ab392b; 128 commits / 487 files reviewed._

## 1. Purpose and scope

Promptfoo is a production-grade open-source CLI and Node.js library for evaluating and red-teaming LLM applications.
Supports comparing models side-by-side (OpenAI, Claude, Ollama, Bedrock, etc.), running automated test suites,
generating security vulnerability reports, and integrating into CI/CD pipelines. Now part of OpenAI (remains MIT
licensed and open source). For Linus, this is the **benchmarking + validation layer**: smoke-test Dan's tasks before
rolling out new prompts, model switches, or tool changes; detect regressions; measure task-specific accuracy and
latency.

## 2. Architecture summary

Promptfoo is a TypeScript/Node codebase (Vite build, React 19 frontend, SQLite backend via Drizzle ORM, current version
0.121.11 as of 2026-05-08 release; HEAD as of 2026-05-18 is e01ab392b). Users define evaluations in YAML: test cases
(inputs), expected outputs/assertions, and model configurations. The CLI runs evals (outputs to JSON, with **junit-xml
reports** now also supported per #9073), compares results, and serves a web viewer (React dashboard on localhost:3000;
server on localhost:15500). Providers are pluggable adapters for each LLM API (OpenAI, Anthropic, local Ollama, custom).
The 2026-Q2 provider catalog gained `bedrock converse mcp` support (#9134), Mistral refresh (#9018), xAI refresh
(#9033), Atlas Cloud (#8980), `gpt-5.5` model support (#8884/#8873), Claude Opus 4.7 support (#8763), and explicit
OpenAI prompt cache controls (#9093). Assertions live under `src/assertions/` and span the full grader vocabulary —
equality, semantic similarity via embeddings (`similar.ts`), LLM-graded rubrics (`llmRubric.ts`,
`modelGradedClosedQa.ts`, `geval.ts`, `factuality.ts`, `searchRubric.ts`), classifier-based moderation, RAG-specific
graders (`contextRelevance`, `contextRecall`, `contextFaithfulness`, `answerRelevance`), n-gram (`bleu`, `rouge`,
`meteor`, `gleu`, `ngrams`), tool-call F1 (`toolCallF1`), trajectory matching, trace-span graders (`traceSpanCount`,
`traceSpanDuration`, `traceErrorSpans`), guardrails, and refusal detection. Red-teaming plugins cover prompt injection,
jailbreak, toxicity, coding-agent attacks, and a new **harmbench filter-by-category** option (#8827). **Code-scan
output** now ships SARIF (`feat(code-scan): add SARIF output support` #9161 + `refine SARIF output ergonomics` #9159),
so promptfoo results can flow directly into GitHub Code Scanning. **MCP response transforms** (#8943) let MCP-targeted
evals reshape tool responses before grading. Pre-commit hook (Biome linter + Prettier) enforces formatting; per-PR
AGENTS.md guidance under each subdirectory codifies the agent conventions.

## 3. What's reusable in Linus

Promptfoo remains the direct fit for the **Linus Dan Task Suite** (the `benchmarks/` folder) — and the 2026-05-18
refresh confirms R2-03's "promptfoo as the Dan-task grader candidate" framing: the grader shape has not pivoted, and the
existing grader vocabulary covers the spectrum Linus needs. Build a `promptfooconfig.yaml` that tests Linus prompts and
models against the 50-100 task cases Dan cares about (e.g., genomics Q&A, code-generation, summarization). Reuse
Promptfoo's Ollama provider to test against local workers (Qwen3, Qwen2.5-Coder, Mistral-7B, future fine-tuned Linus).
The JSON output (success/score/error per test) feeds automated regression detection and Phase 1 baseline measurements;
the new junit-xml output (#9073) is the natural format if Linus's CI eventually surfaces eval results in standard
test-runner UIs. The **grader vocabulary worth lifting verbatim** for the Dan Task Suite, in priority order: `equals`
and `contains` for the genomics-Q&A factoid subset; `similar` (cosine over embeddings) for paraphrase-tolerant free-text
answers; `llm-rubric` and `model-graded-closed-qa` for the rubric-graded subset (the "did this analysis follow best
practice?" class); `factuality` for the citation-faithfulness subset (RAG against the KnowledgeBase per DEC-0044);
`javascript` / `python` for the executable graders (the "did this code compile?" class); and the RAG-specific quartet
(`context-relevance`, `context-recall`, `context-faithfulness`, `answer-relevance`) for any paper-qa-backed task per
DEC-0044. The recent fix `fix(assertions): invert not-llm-rubric results` (#8986) is worth knowing — the negative-rubric
form (`assertion: not-llm-rubric`) is now reliable for "this output must NOT contain X" checks. Red-teaming plugins
(prompt injection, refusal jailbreaks, coding-agent attacks) are valuable for safety validation of Linus tools, and the
new harmbench category filter (#8827) lets the Dan Task Suite scope red-teaming to a subset (e.g., only "cyber" +
"chemical" categories) rather than running the full harmbench every time.

## 4. What's inspiration only

Promptfoo's web UI is polished but optional for Linus Phase 1 — the JSON output is enough for bulk analysis. The
Bedrock/Azure/commercial-API support is useful reference but not urgent for local Linus. The **code-scan SARIF output**
shipped in #9161 plus the `code-scan-action/` GitHub-Action wrapper is inspirational for Phase 5+ Linus CI/CD safety
gates — a Linus equivalent that emits SARIF for prompt-injection / tool-misuse findings would slot into GitHub Code
Scanning identically. The team's 10M+ user case studies (linked in docs) are valuable evidence that the tool scales to
production scenarios. The **DTO-validation hardening pass** that ran through Q2 2026 (~15 commits validating provider /
eval / model-audit / redteam / media / trace route DTOs, hash-stabilizing cache keys across vertex/bedrock/anthropic/
mistral/replicate/watsonx providers) is inspirational only — it's the kind of "production hardening of public APIs"
sweep Linus will eventually want once Phase 2+ stabilizes the orchestration backend's HTTP surface.

## 5. What's incompatible or out of scope

Promptfoo is not a training framework; it measures, not improves. For Phase 6 fine-tuning, Linus needs pmetal or mlx-lm,
not promptfoo. Node.js/npm dependency adds a second language runtime; Linus's Python-first stack means promptfoo runs
alongside the core (not inside). The tool has a learning curve; Dan's task suite will need careful definition and
maintenance. Costs scale with eval size (10 configs × 50 tests × 5 model variations = 2500 API calls if using remote
models); local Ollama avoids costs but has latency tradeoff.

## 6. Recommendation: **Integrate (Phase 1 close)** _(unchanged 2026-05-18; see refresh note)_

Promptfoo is ready to use now as a standalone tool for Phase 1 baseline measurement and Phase 2a regression detection.
No waiting required. Set up a smoke test: (1) define 10 representative cases from Dan's task suite in YAML, (2) test
against Ollama (Qwen3, Qwen2.5-Coder, or Mistral running locally), (3) export JSON results, (4) measure mean latency and
task accuracy. Use this baseline for all future model/prompt changes. As Linus scales to multi-agent (Phase 3), use
red-teaming to scan for prompt injection in tool descriptions; harmbench filter-by-category (#8827) keeps the
red-teaming budget proportional. Phase 5+ CI integration: emit SARIF (#9161) so Linus eval failures surface in GitHub
Code Scanning the same way promptfoo's own code-scan-action does. The 2026-05-18 refresh did not surface any new grader
type worth a structural rebuild of the Dan Task Suite — the existing grader vocabulary (equals / contains / similar /
llm-rubric / model-graded-closed-qa / factuality / javascript / python / RAG quartet) covers Dan's needs as originally
scoped.

## 7. Questions for Dan

1. **Dan Task Suite scope.** Start with 20-50 representative cases or go for the full 100-item suite now? Smaller suite
   iterates faster; larger suite catches more regressions but has slower iteration.
2. **Custom graders vs. built-in assertions.** For genomics/chemistry Q&A, does Linus need custom Python graders (e.g.,
   compare extracted gene names to a reference set), or do semantic similarity + equality checks suffice?
3. **Multi-model comparison.** Phase 1 baseline: single model (Ollama Qwen2.5-Coder) or compare Qwen vs. Mistral vs.
   local Claude? (Latter is heavier but more informative.)
4. **Red-teaming scope.** Which attack vectors matter most for Linus Phase 1? (e.g., prompt injection in KB queries,
   jailbreak attempts on tool descriptions, data exfiltration via search?
