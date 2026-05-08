# gptme (`gptme/gptme`)

## 1. Purpose and scope

gptme is a terminal-first AI agent CLI that runs anywhere (local laptop, SSH, tmux, headless servers, CI/CD) with
built-in tools (shell, Python, file patching, browser, vision, computer use), extensible via plugins/skills/lessons, and
capable of autonomous long-running operation via the agent-template pattern. It's been in active development since
Spring 2023 and is provider-agnostic (Anthropic, OpenAI, local via llama.cpp, OpenRouter, etc.). The philosophy is
"minimal core, extend as needed" — gptme is the closest reference implementation in the repo collection to how Linus
might expose a Worker as a composable CLI/REST agent. For Linus, gptme demonstrates tool composition, plugin
architecture, autonomous run loops, and human-in-the-loop approval workflows that inform both the local harness and
future cross-agent communication.

## 2. Architecture summary

gptme is a layered Python CLI (Python 3.10+, ~8k lines core) with a plugin system: (1) **core chat loop** — user prompt
→ LLM call + tool selection → execute tools → feedback loop; (2) **tools** (shell, python, read, save, patch/morph,
browser, vision, screenshot, gh, tmux, subagent, rag, computer use) — each tool is a stateless function returning
structured output that loops back to the LLM; (3) **plugins** — extensible Python packages that register custom tools,
hooks (pre/post tool call), and commands; (4) **skills** — lightweight YAML bundles of instructions + examples
auto-injected when mentioned; (5) **lessons** — contextual guidance auto-activated on keywords/patterns; (6) **agents**
— persistent autonomous agents via gptme-agent-template, with workspace (git-tracked brain), task queue, meta-learning
via lessons. The server API exposes `/chat` (REST + SSE streaming), and the ACP (Agent Client Protocol) makes gptme
droppable into Zed/JetBrains as a coding agent.

## 3. What's reusable in Linus

The tool registration pattern (each tool is a Python function with type hints + docstring descriptions) is directly
applicable to Linus — mirror gptme's @tool_sync / @tool_async decorators for KnowledgeBase queries, genomics pipelines,
etc. The plugin system (discovering + loading .py modules from ~/.config/gptme/plugins/) is liftable for Linus skills
(domain-specific instruction bundles for bioinformatics tasks). The lessons system (pattern-matching contextual
guidance) is useful for Linus to capture "when analyzing metagenomics, use these practices" knowledge. The autonomous
agent template (workspace with git-tracked journal, task queue, run loop) is a reference for long-running Linus workers.
The hook system (pre/post tool execution) enables guardrails (Dan's sandbox policy) at runtime.

## 4. What's inspiration only

The computer-use tool (full desktop screenshots + GUI interaction) is powerful but not applicable to Linus (headless on
MacBook). The browser tool (Playwright-based web automation) is useful for web-based bioinformatics databases but not
core to Linus Phase 2a. The lessons system in gptme is mature (4+ releases of refinement); Linus can skip straight to
the best practices (keyword-based injection) without replicating the entire adaptive meta-learning loop.

## 5. What's incompatible or out of scope

gptme's tool set is optimized for coding (shell, file patching, GitHub interaction) and general automation (browser,
computer use). Linus will need domain-specific tools (KnowledgeBase RAG, WDL pipeline execution, bioinformatics
command-line tools) that gptme doesn't provide. gptme is provider-agnostic but assumes remote LLMs (Anthropic, OpenAI);
integrating local MLX models requires a custom Model adapter (doable but not in gptme's current design). The ACP
protocol (Editor integration) is out of scope for Linus Phase 2a (focus is backend orchestration, not editor polish).

## 6. Recommendation: **Study (Phase 2a, 7)**

gptme's architecture (tool registry, plugin system, lessons, autonomous agents) is essential reading for Linus Phase 2a
specification. Concrete learnings: (1) how to structure the tool decorator so it works with both CLI and API harnesses,
(2) how to organize long-running agent state (workspace, task queue, git tracking), (3) how plugins integrate safely
(load-time binding vs. runtime hooks). A Phase 7 experiment (Skills & Autonomy Graduation): take gptme's lessons system
and adapt it for Linus domain knowledge (e.g., "if agent mentions PacBio HiFi, inject these best practices"). Once
adapted, test a Linus agent on a real bioinformatics task with and without domain lessons, measuring task success rate
and token efficiency.

## 7. Questions for Dan

1. **gptme's tool model for Linus.** gptme tools are stateless functions returning structured output. Linus needs
   stateful tools (KnowledgeBase session, temporary files). Should Linus extend the tool abstraction to carry context,
   or remain stateless and pass context via RunContext (pydantic-ai style)?
2. **Autonomous agent workspace design.** gptme-agent-template uses git-tracked workspace (journal, tasks, lessons).
   Should Linus adopt this for long-running agents, or is it over-engineered for Dan's personal workflows?
3. **Plugin safety for domain tools.** gptme's plugin system requires file-system discovery + dynamic import. For Linus
   domain skills (bioinformatics, chemistry), should plugins be vetted/sandboxed, or is Dan's implicit trust sufficient
   for Phase 2a?
