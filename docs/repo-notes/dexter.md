# dexter (`virattt/dexter`)

## 1. Purpose and scope

Dexter is an autonomous financial-research agent shaped explicitly after Claude Code, but specialized for equity
research: take a complex question ("is NVDA fairly valued at today's price"), decompose it into research steps, pull
live market and fundamentals data, write filings into a scratchpad, validate, and iterate until a confident answer is
produced. It is a single-binary TypeScript/Bun CLI built on LangChain abstractions, with an Ink-rendered terminal UI, a
SQLite-backed persistent-memory layer, a `SKILL.md` extensibility system that mirrors Anthropic's Skills convention, and
a WhatsApp gateway built on `@whiskeysockets/baileys` so Dan could literally text questions to it. For Linus this is a
Group-10 adjacent-domain repo: financial intelligence is a Phase 7+ Worker skill Dan has explicitly said he wants, and
the agent- loop architecture happens to be one of the cleanest small-codebase examples of the Claude-Code pattern in the
collection.

## 2. Architecture summary

The agent loop lives in `src/agent/agent.ts` (~680 lines): a single growing message array, streaming LLM calls,
concurrent read-only tools dispatched by `src/agent/tool-executor.ts`, and a two-tier context management strategy —
`microcompact.ts` runs every turn to trim minor noise, while `compact.ts` triggers a full LLM-summarization pass when
token usage crosses an auto-compact threshold (the prompt explicitly preserves "all numerical data" and forbids tool
calls during compaction). This is direct prior art for context engineering on long agent runs and is the single most
transferable piece of the repo. A `scratchpad.ts` module (also referenced in `.dexter/scratchpad/*.jsonl`) is the
durable record of every tool call and result. Tools are registered in `src/tools/registry.ts` with both rich and compact
descriptions, conditionally enabled by env var: finance (`get_financials`, `get_market_data`, `read_filings`,
`stock_screener` — all backed by financialdatasets .ai), web (Exa preferred, Perplexity, then Tavily), filesystem
(read/write/edit), browser (Playwright), cron, heartbeat, memory (`memory_get`/`search`/`update` over SQLite +
embeddings in `src/memory/`), and a `skill` tool that invokes `SKILL.md` workflows (a DCF valuation skill ships
in-tree). LLM provider is multi-vendor through LangChain — OpenAI, Anthropic, Google, xAI, OpenRouter, Moonshot,
DeepSeek, Ollama — with a `/model` slash command to swap at runtime; default is `gpt-5.4`. The WhatsApp gateway
(`src/gateway/`) is a separate process: `bun run gateway:login` pairs the device via QR, then `bun run gateway` watches
your "message myself" chat and routes inbound messages through the agent loop.

## 3. What's reusable in Linus

The agent loop and the compaction strategy are the prize. `src/agent/compact.ts` plus `src/agent/microcompact.ts` are a
working, opinionated implementation of the "preserve numbers, summarize prose" pattern that Dan flagged in the recent
memory-architecture synthesis notes — the system prompt for compaction in particular is worth lifting more or less
verbatim as a starting template for Linus's own context manager. The `SKILL.md`-driven skill registry
(`src/skills/ registry.ts`) is the closest in-tree example of how a Phase 7 Linus skill catalog can look: YAML
frontmatter, markdown body, exposed to the LLM via system-prompt metadata, invoked through a single `skill` tool. The
provider-detection logic in `src/providers.ts` (prefix-based dispatch — `claude-` → Anthropic, etc.) is a useful sketch
of how Linus's router can present a unified model surface without a per-provider matrix.

Compared to the QuantAgent and TradingAgents siblings, Dexter is distinct in being a **single-agent Claude-Code-style
research loop**, not a multi-agent committee. QuantAgent and TradingAgents both lean on multi-role debate (analyst,
trader, risk officer); Dexter explicitly does not, betting that one capable agent with a good scratchpad and a real
compaction strategy beats role-played consensus for research questions. That positioning is worth borrowing directly:
for Linus's first agentic skill, the right baseline is one Dexter-shaped Worker, not a TradingAgents-shaped committee.

## 4. What's inspiration only

The financial domain itself — the finance tools are tightly coupled to financialdatasets.ai, a paid third-party API ($),
and to SEC EDGAR scraping conventions. If Linus wants real financial intelligence in Phase 7, the right move is to study
Dexter's tool _shapes_ (what does a useful `get_financials` argument set look like, how should results be summarized for
the LLM, what concurrency guarantees) and re-implement against whatever data sources Dan actually intends to fund.
Inheriting an API-key dependency is the wrong default. The WhatsApp gateway is a fun demo and a real proof-point for
"agent-as-chat-buddy", but Linus's interface story is openclaw + VS Code + native app, not Baileys; treat it as evidence
that the orchestration layer should be transport-agnostic, not as a component to vendor.

## 5. What's incompatible or out of scope

TypeScript/Bun is a different runtime from the Linus Python+Rust core. Vendoring code is impractical; reading code for
patterns is fine. LangChain is a heavy dependency that Linus has so far avoided — the compaction patterns are
extractable without it but the model-abstraction layer assumes it. The default-on LangSmith tracing and the
`playwright install chromium` postinstall step are both unwanted in a private local stack. The agent's identity is
loaded at startup from `SOUL.md` (a charming Buffett-and-Munger-quoting persona document) — cute, and a reminder that
Linus will eventually want its own equivalent, but the specific text is not Linus's voice.

## 6. Recommendation: **Study**

Read `src/agent/agent.ts`, `src/agent/compact.ts`, `src/agent/scratchpad.ts`, and `src/skills/registry.ts` carefully
when designing Linus's Phase 2/3 agent loop and Phase 7 skill catalog. Steal the compaction prompt template and the
SKILL.md-as-first-class-citizen pattern. Do not vendor any code; do not adopt LangChain on dexter's account; do not pay
for financialdatasets.ai unless Phase 7 financial-intelligence is being actively built. Revisit if and when Dan
prioritizes a financial-research Worker skill — at that point Dexter becomes the reference architecture for what to
re-implement in-house.

## 7. Questions for Dan

- **Financial-intelligence priority.** The total-landscape doc lists financial knowledge as a desired Linus skill. Is
  that a near-term Phase 7 target (build a Linus equivalent of Dexter against free data sources) or a "nice eventually"
  marker that can sit until later phases?
- **Single-agent vs multi-agent default.** Dexter explicitly bets on one capable agent; TradingAgents and QuantAgent bet
  on committees. Linus's Phase 3 ("Knowledge & Parallel Agents") implies fan-out is desirable. Do we treat Dexter's
  single-agent-loop shape as the per-Worker default and reserve multi-agent for orchestration above it, or design for
  committee-style debate within a single Worker too?
- **WhatsApp / phone interface.** Out of scope for Linus's current roadmap, but the Baileys gateway is a working pattern
  for "Linus you can text from a hike." Worth a Phase 8 placeholder, or actively not-wanted on privacy grounds?
