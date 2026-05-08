# K-Dense BYOK (`K-Dense-AI/k-dense-byok`)

## 1. Purpose and scope

K-Dense BYOK (Bring Your Own Keys) is an open-source local-first agentic research assistant called Kady that runs on
macOS/Linux with user-supplied API keys (OpenRouter, Exa, Modal). It orchestrates a Claude Opus (or Gemini 3.1 Pro)
"maestro" model with a Gemini CLI "expert" subprocess for tool-heavy tasks, manages 170+ scientific skills (genomics,
drug discovery, materials science), and surfaces 326 workflow templates. Direct relevance to Linus: BYOK is a reference
design for the "local orchestration + remote inference" architecture Linus itself aims to be, with strong patterns for
multi-tab sandboxing, cost tracking, and skill routing.

## 2. Architecture summary

Three local services (Python agent, Node.js web UI, optional remote compute): the agent dispatches between orchestrator
(Claude Opus via OpenRouter) and expert (Gemini CLI subprocess with tool calling). MCP servers inject custom tools.
Project isolation with shared sandboxes means file I/O in one tab is immediately visible in others. Cost tracking
backfills from OpenRouter's `/api/v1/generation` API. Skills are JSON-encoded with summaries; Kady selects and passes
them to the expert via tool calling. 326 workflow templates cover 22 scientific disciplines. Uses Exa or Parallel for
neural web search; Modal for optional cloud GPU compute. Built atop Google's ADK (Agent Development Kit) and LiteLLM for
multi-model routing.

## 3. What's reusable in Linus

The orchestrator/expert split mirrors Linus's Maestro/Worker discipline and is worth adopting. The skill routing and
selection logic (list_skill_summaries, passing summaries to model) is directly applicable to Linus Phase 2's tool
registry. The multi-tab architecture with shared sandboxes is a pattern Dan should consider for Linus's session-store
design. Cost tracking (especially the OpenRouter backfill logic) is production-ready and solves the real problem of
streaming responses not including cost until after they complete. The workflow template library is a good model for
Linus Phase 4's KnowledgeBase integration.

## 4. What's inspiration only

The reliance on OpenRouter (a commercial multi-model proxy) is outside Linus's sovereignty mandate — but the routing and
model-selection UI pattern is instructive. The Exa neural search is clever for scientific research but optional. The ADK
and Gemini CLI expertise are Google-specific; Linus will use Claude or local workers instead. However, the idea of a
configurable "expert" dispatch layer (switchable between Claude Code, Gemini CLI, or future in-house agents) is worth
adopting at Phase 2/3.

## 5. What's incompatible or out of scope

Requires API keys for external services (OpenRouter for models, Exa for search, Modal for compute). No offline-only mode
without significant rework. The UI is React-based (web-first); Linus is backend-first with interchangeable front-ends.
K-Dense BYOK is production software for researchers; Linus is a personal infrastructure project — different scale and
user expectations.

## 6. Recommendation: **Study (Phase 2+)**

Not for adoption as-is, but essential reading for Linus Phase 2's orchestration backend design. The skill routing,
multi-tab sandboxing, and orchestrator/expert dispatch patterns are directly applicable. If Dan wants to compare Linus
against a production research assistant, K-Dense BYOK is the most relevant open-source reference.

## 7. Questions for Dan

1. **Skill registry at Phase 2.** K-Dense's 170+ skills model is overkill for initial Linus, but the JSON format +
   summaries are reusable. Should Linus Phase 2 ship with a minimal skill set (e.g., 10–20 bioinformatics tools) or
   defer to Phase 3?
2. **OpenRouter vs. local.** K-Dense uses OpenRouter to avoid paying for multiple model subscriptions. Linus runs
   everything locally + hosted Claude. Should Linus ever expose an optional "use OpenRouter for additional model
   variety" mode, or stay offline-first?
3. **Multi-tab sandboxing.** K-Dense's shared sandbox across tabs is elegant for researchers running parallel analyses.
   Is this a Linus Phase 2 feature, or deferred until multi-agent parallelism (Phase 3)?
4. **Expert dispatch configurability.** K-Dense lets users toggle orchestrator vs. expert models from a dropdown. Linus
   Phase 2 should support similar configurability (switch between Ollama workers, future pmetal, etc.). Worth
   prototyping early?
