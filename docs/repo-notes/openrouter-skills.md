# openrouter-skills (`OpenRouterTeam/skills`)

## 1. Purpose and scope

A first-party collection of Anthropic-Skills-format Skills published by the OpenRouter team for building applications
and agents on top of OpenRouter's unified API to ~600 hosted models. The repo bundles eight skills under `skills/` plus
one out-of-band `open-responses/` skill that documents the Open Responses protocol spec itself rather than OpenRouter
specifically. Skills are advertised as installable into Claude Code, Cursor, OpenCode, OpenAI Codex, Pi, Gemini CLI,
Windsurf, and any other Agent-Skills-compatible harness — typically via `gh skill install OpenRouterTeam/skills` or a
plugin marketplace command. Every script in the repo requires `OPENROUTER_API_KEY`, which puts the entire bundle in
direct tension with Linus's "no paid APIs required for operation" north star (see CLAUDE.md). OpenRouter is pay-per-use,
not subscription, so it's a softer tension than Anthropic-direct usage, but it still means none of these skills could
run in a fully offline Linus deployment.

## 2. Content overview

The eight shipped skills divide cleanly into three groups. **Scaffolding skills** generate full TypeScript/Bun project
trees: `create-agent-tui` builds a terminal UI agent ("create-react-app for terminal agents") with 14 built-in tools,
configurable input styles, ASCII banners, loaders, and session persistence; `create-headless-agent` builds a headless
variant for CLIs, HTTP servers, queue workers, and MCP servers with 12 built-in tools, output-schema validation, and
webhook notifications. Both target `@openrouter/agent` as the inner loop. **SDK/API reference skills** wrap the
OpenRouter HTTP and TypeScript surface: `openrouter-typescript-sdk` documents the `callModel` pattern across 600+
models; `openrouter-agent-migration` handles `@openrouter/sdk` -> `@openrouter/agent` package migration;
`openrouter- models` provides querying, pricing comparison, context-length lookup, provider performance, and fuzzy
model-name resolution via shipped `scripts/`. **Capability skills** front specific OpenRouter-hosted features:
`openrouter-images` (text-to-image and image edit), `openrouter-video` (mentioned in tree but not in README; appears to
mirror openrouter-images for video models), and `openrouter-oauth` (a framework-agnostic Sign-In-With-OpenRouter PKCE
module with copy-pasteable auth code and a sign-in button — no SDK dependency, plain `fetch`). The standalone
`open-responses/` skill documents the Open Responses spec (POST `/v1/responses`, polymorphic items, response/item state
machines, SSE event catalog, agentic loop with `previous_response_id`, four extension mechanisms) — provider-agnostic,
not OpenRouter- specific, and arguably the most reusable artifact in the entire repo for Linus regardless of whether
OpenRouter is ever adopted.

## 3. What's reusable in Linus

Compared to the other Skills-format repos in the collection — `OmegaWiki` (24 general-purpose skills),
`infranodus- skills` (15 skills wrapping the InfraNodus knowledge-graph product), and `AgenticResearchWiki` (2
research-loop skills) — `openrouter-skills` is the only one tightly coupled to a paid SaaS API surface. Its scaffolders
generate Bun + Node TypeScript projects against `@openrouter/agent`; that codegen would have to be retargeted to a local
OpenAI-compatible endpoint (Ollama today, Linus tomorrow) before it could serve a "no paid API" Linus user. The
genuinely reusable piece is the `open-responses/` SKILL.md and its references — Open Responses is the protocol Linus's
Phase 2a backend is implicitly aiming at when ARCHITECTURE.md says "OpenAI-compatible endpoint." Adopting the spec
verbatim, with the state- machine diagrams and the streaming event catalog reproduced here, would give Linus a real
interoperability story instead of an ad-hoc OpenAI-shape. The `openrouter-models` skill's pricing/context/performance
lookup logic is also worth study for a future Linus model-routing layer (Phase 5+): even if Linus only routes between
local Ollama models and pmetal-served models, the data-shape and ranking logic have prior art here.

## 4. What's inspiration only

The two scaffolders (`create-agent-tui`, `create-headless-agent`) are the most concretely interesting parts after Open
Responses, but their value to Linus is structural rather than functional. Sibling `claw-code-local` already gives Dan a
working Ollama-backed Rust agent harness, and `cline` gives a VS Code one — Linus does not need a third TypeScript
scaffolder. What's instructive is the _checklist UX_ (multi-select feature picker covering entry points, server tools,
client tools, persistence, schema validation, webhooks) and the explicit separation of "OpenRouter server tools"
(executed remotely with zero client code, e.g. `openrouter:web_search`, `openrouter:web_fetch`, `openrouter:datetime`,
`openrouter:image_generation`) from "user-defined client tools." Linus's eventual Phase 7 skills/tools layer faces the
same partition between server-side tools (Linus executes locally with its own sandbox) and harness-side tools (Cline,
claw-code, openclaw execute on the developer's machine), and the OpenRouter framing — type strings, default-on/default-
off matrix — is a clean precedent. Differentiator vs `OmegaWiki` and `infranodus-skills`: those are libraries of
_single-purpose action_ skills (one skill = one capability invocation), whereas openrouter-skills' two scaffolders are
_meta-skills_ that emit entire project trees. That is closer in spirit to Cline's "MCP server generator" than to a
typical Skills bundle.

## 5. What's incompatible or out of scope

The hard incompatibility is the API key. `OPENROUTER_API_KEY` gates every skill that touches a model — meaning
`create-agent-tui`, `create-headless-agent`, `openrouter-typescript-sdk`, `openrouter-agent-migration`,
`openrouter-models`, `openrouter-images`, `openrouter-video`, and `openrouter-oauth` are all unusable in a fully
offline/local Linus deployment. Only the protocol-spec skill (`open-responses/`) is provider-agnostic. Beyond the
licensing/billing surface, the codegen targets are TypeScript + Bun, which is fine for clients sitting outside Linus but
a poor fit for the Python orchestration layer in `src/linus/`; nothing in this repo reduces Phase 2a Python work. The
OpenRouter "server tools" model (web search, web fetch, datetime executed in OpenRouter's cloud) is also the exact
opposite of what Linus wants — Linus's value proposition is that those tools run on Dan's M1 Max, against his
KnowledgeBase corpus, under the SAFETY.md sandbox. If Linus offered web search at all, it would be local-Kiwix-backed,
not remote.

## 6. Recommendation: **Study**

Adopt nothing wholesale; harvest two specific things. First, treat `open-responses/SKILL.md` as the de facto reference
for Linus's Phase 2a serving spec and either link to it from ARCHITECTURE.md or fork the relevant prose into a Linus-
owned doc. Second, study the `create-headless-agent` and `create-agent-tui` checklists as a UX template for any future
"linus init agent" command. Do not install OpenRouter-key-requiring skills into Dan's Claude Code — they would advertise
themselves on triggers like "build an agent" and burn Maestro tokens routing toward a paid path Dan has explicitly
deprioritized. If OpenRouter ever becomes an explicitly-sanctioned escape hatch for "Worker model that local hardware
can't run" (e.g. Llama 4 Maverick at full quality), revisit and install `openrouter-models` +
`openrouter-typescript- sdk` then.

## 7. Questions for Dan

- **OpenRouter as a sanctioned escape hatch?** The "no paid APIs required" rule is about _required_, not _forbidden_. Is
  there a tier of Linus tasks where reaching out to OpenRouter for a model size local hardware can't host (Llama 4
  Maverick, Claude Opus 4.7 itself via the OpenRouter route) is acceptable, or is OpenRouter strictly off the table even
  as opt-in?
- **Open Responses adoption.** Linus's Phase 2a says "OpenAI-compatible endpoint." Is the actual target the OpenAI Chat
  Completions shape (legacy, what Ollama serves), the OpenAI Responses shape (newer, stateful), or the Open Responses
  spec documented in this repo? The three are not interchangeable and the choice locks in client compatibility.
- **Differentiator confidence.** The README only lists 7 skills but the `skills/` tree contains 8 (`openrouter-video` is
  undocumented). Worth flagging upstream, or just note and move on?
