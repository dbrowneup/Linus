# semanticworkbench (`microsoft/semanticworkbench`)

## 1. Purpose and scope

Semantic Workbench is Microsoft's "prototype intelligent assistants quickly" platform — a three-tier monorepo that
splits cleanly into a Python backend (`workbench-service/`, FastAPI + SQLModel + Alembic), a React/TypeScript frontend
(`workbench-app/`, Vite + Fluent UI v9 + Redux Toolkit + MSAL/Entra auth), and an open-ended set of Assistant Services
(any framework, any language) that integrate by speaking a documented HTTP protocol. By design it is the most
structurally ambitious orchestration platform in G7: a full UI plus persistent service plus multi-assistant
conversations plus framework-agnostic plug-in model, where the leaner siblings (claude-squad's tmux CLI, workgraph's
graph runtime, codebuff's single-app multi-agent) each pick one slice. License is MIT, Microsoft-owned, actively
maintained as of April 2026 (last commit on `main` two weeks before this note). For Linus this is reference material for
the Phase 1f Algorithm-check on DEC-0002 ("does Linus need its own orchestration layer?") and a possible influence on
the Phase 2 MVP service shape, with explicit caveats around Azure coupling and the React-vs-Streamlit-vs-openclaw
frontend story.

## 2. Architecture summary

The workbench-service is a FastAPI app (`fastapi[standard]~=0.115`, `sqlmodel`, `aiosqlite` for dev / `asyncpg` for
Postgres, `sse-starlette` for streaming, `python-jose` for JWT, Alembic for migrations) organized as a thin
`semantic_workbench_service/service.py` over per-resource controllers (`controller/conversation.py`,
`controller/assistant.py`, `controller/participant.py`, `controller/file.py`, `controller/conversation_share.py`,
`controller/export_import.py`). The protocol's central abstraction is the **Assistant Service** — a separate HTTP
process the workbench discovers, registers (`assistant_service_registration.py`), and calls into via a typed client pool
(`assistant_service_client_pool.py`). "Framework-agnostic" therefore means: the workbench service does not import or run
your assistant code; it stores conversation state and forwards events to whatever HTTP endpoint your assistant exposes,
and your assistant calls back into the workbench to post messages, files, and status. A Python SDK
(`libraries/python/semantic-workbench-assistant`) wraps this so a Python assistant only writes decorated handlers
(`@assistant.events.conversation.message.chat.on_created`) and gets a working FastAPI app via `assistant.fastapi_app()`;
.NET assistants and bespoke services are first-class, demonstrated by `examples/dotnet/` and `assistants/`. Multiple
assistants can sit in the same conversation (multi-participant, parallel — not a sequential graph). Auth is JWT with
MSAL/Entra by default; an optional Microsoft Aspire orchestrator (`aspire-orchestrator/`, .NET) wraps the whole stack
for container deployment. Storage default is SQLite at `~/workbench-service/.data`, swappable to Postgres.

## 3. What's reusable in Linus

Almost nothing as code, a fair amount as design. The protocol shape — workbench owns conversations, assistants are
external HTTP services discovered via a registration call, events and messages flow over a typed model
(`semantic-workbench-api-model`) — is the cleanest articulation in G7 of "one host, many heterogenous workers" and is
exactly the seam Linus's Phase 2 orchestration layer needs to commit to. If Linus's tool registry and agent spawner
treat each Worker (Qwen-coder, Mistral, future Linus fine-tune, MCP servers) as an HTTP-registered service rather than
an in-process call, openclaw and Cline can plug in alongside model backends with the same plumbing. The SDK pattern
(`AssistantApp` + decorator event handlers + Pydantic-typed config that auto-renders UI) is also worth lifting for the
Phase 7 skills surface — declaring tool config once and getting both validation and form rendering is a real win.

Compared to siblings: claude-squad solves a different problem (parallel terminal sessions with git-worktree isolation,
no UI, no persistence, no protocol) — semanticworkbench is the inverse, all protocol and persistence and UI, no
isolation story. workgraph is closer in spirit (declarative multi-agent topology) but graph-shaped where this is
participant-shaped — Linus likely wants both axes. openclaw is the nearest analogue: also a local-first gateway with its
own UI, also OpenAI-compatible, but openclaw is built around the chat-app UX whereas semanticworkbench is built around
the assistant-development workflow. The two are not redundant; openclaw is what a user opens, semanticworkbench is what
a developer of new assistants opens.

## 4. What's inspiration only

The React/Fluent-UI frontend is a non-starter for Linus. The repo's UX commitments are Streamlit for Phase 2 and
openclaw later; adopting Fluent UI v9 plus MSAL plus Redux Toolkit plus RTK Query would invert Linus's frontend ambition
for no clear gain on a single-user local box. The .NET Aspire orchestrator likewise belongs to Microsoft's
container/cloud worldview and not to Linus's "native on M1 Max" worldview. The conversation-canvas, message-debug-panel,
and Mermaid/ABC content renderers are nice ideas to remember when designing Linus's eventual native UI, not artifacts to
import. The multi-assistant participant model is conceptually clean but for now Linus's Worker-orchestra idiom is
fan-out-and-collect, which is a thinner abstraction.

## 5. What's incompatible or out of scope

The default identity stack is MSAL/Entra (`@azure/msal-browser`, `@azure/msal-react`, `python-jose` JWT verification
configured against AAD) — the recent commit `ab0f905 Verify jwt signatures` lands in that path. There is also a hard
Azure dependency in `workbench-service/pyproject.toml` (`azure-cognitiveservices-speech`, `azure-identity`,
`azure-keyvault-secrets`, `azure-core[aio]`) for speech and secret-management features. None of this is fatal — the
LICENSE is MIT, the JWT/auth layer can be swapped, the speech feature is optional — but it means a "just adopt the
service" path in Phase 2 implies either ripping out Azure code or running it in a degraded mode. The Postgres-or-SQLite
choice is fine; the assumption that you have a Microsoft tenant to authenticate against is not. The frontend is also
designed for the Codespaces / Docker dev-container flow; running natively on M1 Max would require recreating the launch
config that VS Code's `.code-workspace` provides. None of the workbench's serving paths help with on-device inference;
this is purely the orchestration plane, and remains LLM-provider-agnostic only inasmuch as the _assistant_ picks its
provider (most examples reach for `openai-client` or `anthropic-client`). No paid-API requirement at the workbench
layer, but the example assistants assume one.

## 6. Recommendation: **Study**

The protocol design — assistant-as-external-HTTP-service with typed registration, typed events, and a typed Python SDK
that hides the wire format — is the strongest single artifact in G7 for the Phase 1f decision on DEC-0002. Read
`libraries/python/semantic-workbench-api-model` and `workbench-service/semantic_workbench_service/controller/` as a
reference protocol when designing Linus's orchestration API in Phase 2a; consider whether Linus's Worker registration
should look structurally similar (HTTP discovery + typed event bus) rather than reinventing it. Do not vendor the
service, do not adopt the frontend, do not depend on Azure. Revisit only if Phase 5 interface work surfaces a gap that
the assistant-development workflow (vs the chat workflow openclaw covers) clearly fills.

## 7. Questions for Dan

1. **Assistant-as-HTTP-service or assistant-as-in-process?** Semanticworkbench commits hard to the first; pmetal's
   `pmetal-mcp` and Linus's current assumed shape lean toward in-process tool calls plus an OpenAI-compatible serving
   endpoint. Is the right Phase 2a model a hybrid — Workers run in-process, but the orchestrator exposes an HTTP
   registration surface so external services (a future Linus fine-tune on a Mac Studio, or a Worker on the Vision Pro)
   can register the same way?
2. **Multi-participant conversations vs fan-out-and-collect.** The workbench treats N assistants in one conversation as
   peers that the user @-mentions; Linus today implies a Maestro-orchestrated fan-out. Is the multi-participant peer
   model interesting for any specific workflow (paper review, debate-style synthesis), or is fan-out enough through
   Phase 3?
3. **Frontend posture.** This repo is the strongest argument I've seen that an assistant-development UI is a separate
   artifact from a chat UI. Streamlit for Phase 2 and openclaw for Phase 5 cover the chat side; do you want a Phase 5+
   assistant-dev surface (skill authoring, prompt iteration, conversation replay), or is that always Claude Code +
   files-on-disk?
4. **Pydantic config that auto-renders UI.** Worth lifting for Phase 7 skill definitions — declare once, get both
   validation and a form. Adopt that pattern in the Linus tool registry, or stay closer to MCP's tool-schema convention?
