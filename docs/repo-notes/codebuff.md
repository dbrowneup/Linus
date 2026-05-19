# codebuff (`CodebuffAI/codebuff`)

_Refreshed 2026-05-18 against upstream HEAD 26e593b42; 195 commits / 267 files reviewed._

## 1. Purpose and scope

Codebuff is an open-source, multi-agent CLI coding assistant written in TypeScript on Bun, distributed as the paid
`codebuff` npm package (CLI now at v1.0, SDK at v0.10) and as `freebuff` — a free, ad-supported sibling built from the
same monorepo via a `FREEBUFF_MODE=true` compile-time flag (freebuff at v0.0.93 with country-restricted "limited mode"
labelling, #670/#682). Where Cline and claw-code wrap a single LLM in a tool loop, Codebuff decomposes a coding request
across a small orchestra of specialized agents — File Picker, Code Searcher, Planner, Editor, Reviewer, Basher,
Researcher, Thinker, Context-Pruner, plus newer Librarian and General-Agent additions — each with its own model, prompt,
tool allow-list, and output contract. Per the README it scores 61% vs Claude Code's 53% on a 175-task internal eval
suite that reimplements real git commits across multiple open-source repos. For Linus this is the most directly relevant
repo in the harness group: it is a working, shipped instantiation of the exact Maestro/Worker decomposition the project
is committing to, with a published SDK so the orchestration layer can be embedded rather than reverse-engineered.

## 2. Architecture summary

A Bun workspace monorepo: `cli/` (OpenTUI + React terminal UI), `sdk/` (`@codebuff/sdk` — the embeddable client), `web/`
(Next.js app + API routes serving as the backend), `packages/agent-runtime/` (server-side agent loop and tool handling),
`agents/` (the shipped agent fleet, with `librarian/` and `general-agent/` added since the prior note),
`agents-graveyard/` (retired agents kept for history — context-discoverer, decomposing-thinker, deep-code-reviewer,
brainstormer, …, useful negative reference for what the team tried and dropped), `common/` (shared types, tool schemas,
Zod validators), `evals/` (the git-commit eval harness), `freebuff/` (the free build with mode toggles,
subscription/credits surface, and ad-disable commands stripped at compile time), and `python-app/` (a placeholder
pointing users to the npm install — there is no live Python implementation). The orchestrator is `agents/base2/base2.ts`
— internally named "Buffy the Orchestrator" — which exposes a `createBase2(mode)` factory producing variants for default
/ free / lite / max / fast. Buffy declares a `spawnableAgents` array (file-picker (now removed from default base2,
#421a0a5ce), code-searcher, researcher-web, researcher-docs, basher, thinker, opus-agent, gpt-5-agent, editor,
code-reviewer, browser-use, context-pruner, …) and a `handleSteps` generator that yields tool calls — `spawn_agents` to
fan out, `spawn_agent_inline` for the always-running context-pruner. Sub-agents are themselves `SecretAgentDefinition`s
with model + prompt + toolNames + spawnableAgents; for example `file-picker` runs Gemini 2.5 Flash Lite, spawns a single
`file-lister`, dedupes paths, and pipes them into a `read_files` call. Models are addressed via OpenRouter slugs
(`anthropic/claude-opus-4.7`, `moonshotai/kimi-k2.6`, `deepseek/deepseek-v4-pro`,
`google/gemini-3.1-flash-lite-preview`, `minimax/m2.7`), so any model on OpenRouter is selectable per-agent. Lite mode
(paid Codebuff) defaults to Kimi explicitly to avoid data-retention surfaces; free mode (freebuff) defaults to MiniMax
M2.7 with Kimi and DeepSeek as separate free agent variants. The communication contract between agents is structurally
just typed messages over the spawn boundary — each agent's `outputMode` (`last_message`) plus `set_output` tool defines
what gets returned to the parent. The eval methodology, in `evals/`, has a Prompting Agent guide a coding agent through
up to 5 turns to reimplement a target git commit, then three Gemini 2.5 Pro judges score completion / efficiency /
code-quality / overall on 0–10 and the median is taken; reference eval files in-tree are `eval-codebuff.json`,
`eval-manifold.json`, `eval-saleor.json`. The docs surface added `docs/patterns/handle-steps-generators.md` since the
prior note, formalizing the generator pattern.

## 3. What's reusable in Linus

The most reusable artifact is the **agent-definition contract itself** — a TypeScript object with `id`, `model`,
`displayName`, `spawnerPrompt`, `inputSchema` (Zod-shaped), `toolNames`, `spawnableAgents`, `systemPrompt`,
`instructionsPrompt`, `stepPrompt`, `handleSteps` generator, `outputMode`. This is concrete prior art for what Linus's
own Worker registry should look like, and it generalizes across model families because each agent picks its model. The
`handleSteps` generator pattern — yielding tool calls and receiving `STEP` resumption tokens — is a clean formalism for
deterministic orchestration glue around stochastic LLM steps; cleaner than Cline's monolithic loop. The new
`docs/patterns/handle-steps-generators.md` is now an explicit canonicalization of this pattern worth reading directly
when Linus's Phase 3 spawner design comes due. The `@codebuff/sdk` is callable from any Node/Bun process with
`client.run({ agent, prompt, agentDefinitions, customToolDefinitions, handleEvent })`, which means the Linus
orchestration backend could in principle delegate a whole sub-tree of work to Codebuff and stream events back. The
`evals/` harness — git-commit reimplementation with a Prompting-Agent driver and triple-Gemini-judge median — is
directly adoptable as a Linus benchmark beyond `dan_tasks`, once API budget allows. The `context-pruner` sub-agent that
runs inline every turn is a worked example of "a specialized worker dedicated to context hygiene," which Linus's Phase 3
will want. The `agents-graveyard/` is itself reusable as negative evidence: a candid record of which agent
decompositions the team tried and abandoned (context-discoverer, decomposing-thinker, deep-code-reviewer,
knowledge-keeper, …) saves Linus from re-running the same experiments.

## 4. What's inspiration only

Compared to **claude-squad** (separate user-facing instances) and **cline / claw-code / claw-code-local** (single agent
in a tight loop), Codebuff is the only one in the group that decomposes _internally_ — orchestrator plus typed sub-agent
fleet. That is the differentiator; it is also exactly Linus's intended structure. So the right reading is: do not adopt
Codebuff as Linus's harness, but treat its agent fleet as a **reference design** for the worker catalog Linus will build
(Maestro = hosted Claude in this chat or Claude Code; Workers = Linus-spawned local models with roles analogous to
file-picker, editor, reviewer, researcher). The OpenRouter-everywhere model-routing posture is the opposite of Linus's
"no paid APIs required for operation" rule — useful as a counter-example, not a template. Buffy's prompt scaffolding
(the EXPLORE_PROMPT, the per-mode `instructionsPrompt`/`stepPrompt`, the example-driven `# Response examples` section)
is good prompt-engineering prior art for Linus's eventual orchestrator prompt; copy the structure, not the strings.

## 5. What's incompatible or out of scope

The product economics — paid Codebuff with credits, free Freebuff that the README and `freebuff/README.md` together make
clear is **not** truly free in the local-first sense: it is a thin client that connects to Codebuff's cloud backend,
ships ads in the CLI, and routes prompts through cloud-hosted models (DeepSeek V4 Pro by default, with the
`freebuff/README.md` itself flagging "its API collects data for training," plus Kimi K2.6, MiniMax M2.7, DeepSeek V4
Flash, and GPT-5.4 via the user's ChatGPT subscription). The "limited mode" labelling (#670, #682, #697) makes clear
that Freebuff is geographically gated and rate-limited, with country-specific access. "Free" means no credit card, not
no network and not no telemetry. For a private local assistant this is disqualifying. The web/Next.js + Postgres +
BigQuery + billing infrastructure under `packages/` is a SaaS business backend, not Linus's concern. The Bun runtime
requirement is a soft incompatibility — not a blocker, but Linus is Python + Rust today. Tight coupling to OpenRouter
(and the assumption that any model can be hot-swapped at a URL) is incompatible with a local-Ollama-first design.

## 6. Recommendation: **Study**

Read `agents/base2/base2.ts`, `agents/file-explorer/file-picker.ts`, `agents/editor/editor.ts`,
`agents/reviewer/code-reviewer.ts`, `agents/context-pruner.ts`, and the newer `agents/librarian/` and
`agents/general-agent/` carefully when designing Linus's Phase 3 Worker catalog and orchestrator. Borrow the
agent-definition shape, the `handleSteps` generator pattern (and `docs/patterns/handle-steps-generators.md` for the
formal articulation), the inline context-pruner idea, and the "specialist per role with its own model" principle. Use
`agents-graveyard/` as a curated list of decompositions to NOT try first. Adopt the `evals/` git-commit reimplementation
methodology as a Linus benchmark in Phase 1c or Phase 2b once API budget allows it. Do **not** vendor or run Codebuff or
Freebuff as part of Linus — the cloud-and-ads economics defeat the project's purpose.

## 7. Questions for Dan

1. **Eval claim scrutiny.** The "61% vs 53%" headline rests on Codebuff's own harness — `evals/runners/claude.ts` runs
   Claude Code via Anthropic's API with bypass-permissions, prompted by a Codebuff-authored Prompting Agent, judged by
   three Gemini 2.5 Pro instances. Each of those is a knob that could tilt the result. Worth replicating before citing?
   If so, that's a Phase 1b-ish exercise that needs OpenRouter and Anthropic API budget.
2. **Inline context-pruner pattern.** Buffy spawns `context-pruner` _every step_ via `spawn_agent_inline`. That is one
   way to keep long sessions tractable; it costs a model call per turn. Worth evaluating against the alternatives
   (LLMLingua, summarization checkpoints, SCoT/Letta-style memory) for Linus's Phase 3?
3. **OpenRouter as model bus.** Codebuff routes every agent through OpenRouter slugs; this is how it offers per-agent
   model selection so cheaply. Linus's stance is local-first, but Phase 1's Maestro/Worker loop already uses Anthropic
   for Maestro. Is OpenRouter a candidate for the "non-Maestro paid models" tier (i.e. cheap planners), or stays out?
4. **Differentiator vs claude-squad.** claude-squad runs N independent Claude Code instances side-by-side; Codebuff
   decomposes one request internally. These are orthogonal patterns and Linus might want both — many Workers each
   internally decomposed. Worth making this distinction explicit in ARCHITECTURE.md when the Worker catalog is drafted?
