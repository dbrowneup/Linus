# Semantic Workbench (`microsoft/semanticworkbench`)

## 1. Purpose and scope

Semantic Workbench is Microsoft Research's rapid-prototyping platform for multi-agent systems: a React/TypeScript web
UI + Python FastAPI backend that orchestrates conversations with multiple assistants, each exposing a RESTful API.
Assistants can be built with any LLM framework, language (Python, C#, Node), or custom logic, and the workbench handles
orchestration, message routing, debugging (message inspection + artifact rendering), and configuration. For Linus, it's
a reference for enterprise-scale multi-agent orchestration patterns, but the primary value is studying how to design an
agent-orchestration layer that is agnostic of the underlying LLM or assistant implementation.

## 2. Architecture summary

Workbench is a three-tier system: the React frontend (conversation UI, configuration panel, message inspection, Mermaid
graph rendering) communicates via WebSocket and HTTP to a Python FastAPI backend (conversation store, assistant
registry, message dispatch), which in turn calls out to assistant services via RESTful API (each assistant is a separate
service process, allowing independent development and scaling). The backend is stateless; the database stores
conversations, messages, and assistant metadata. Assistant services implement a protocol (provide a `POST /run` endpoint
that consumes a prompt/context and returns a response). The platform supports artifacts (Mermaid diagrams, ABC music
notation) rendered directly in the UI. Examples span Python echo-bot, Python chatbot, and .NET chatbot with content
moderation.

## 3. What's reusable in Linus

The agent-agnostic orchestration pattern is the most valuable takeaway: Linus tools don't care what model is behind an
agent (Ollama, OpenAI, local MLX, etc.) — they just call a standard endpoint and get back a structured response. The
message-dispatch architecture (pub/sub routing of events across agents) is directly liftable to Linus Phase 2a if
workgraph's JSONL + handler dispatch gets ported to Python. The artifact rendering (supporting multiple output
formats: Mermaid, plaintext, code) is a precedent for Linus tools emitting structured outputs beyond plain text.

## 4. What's inspiration only

The enterprise DevOps focus (Codespaces, GitHub Actions, Docker Compose for local dev, multi-language support) is
valuable for teams but excess friction for a single-developer Linus. The OAuth-based configuration management and
multi-tenant isolation are not applicable to Linus (which is single-user, single-machine). The Mermaid/artifact
rendering infrastructure is nice-to-have but not load-bearing for Phase 1–2.

## 5. What's incompatible or out of scope

Semantic Workbench is purpose-built for interactive multi-agent choreography (human-in-the-loop); Linus is largely
offline execution of pre-specified task DAGs. The frontend is React + TypeScript; Linus is Python-native for Phase 2
(may add a JS harness in Phase 5+ but not as the canonical backend). The Docker-heavy DevOps model (Codespaces,
containers) conflicts with Linus's local-Apple-Silicon focus. Scale assumptions are different: Workbench targets
enterprise teams; Linus targets one scientist with 32 GB RAM.

## 6. Recommendation: **Study (Phase 2a orchestration reference)**

Before finalizing Linus's Phase 2a orchestration layer, read Semantic Workbench's assistant protocol and message
dispatcher to understand how multi-agent systems can remain LLM-agnostic. The core ideas (agent as a service endpoint,
event pub/sub routing, structured artifact outputs) are directly applicable. Don't adopt the codebase; instead, port
the pattern to Python + workgraph JSONL.

## 7. Questions for Dan

- **Single agent vs. multi-agent workflows.** Semantic Workbench excels at human-in-the-loop multi-agent orchestration.
  Should Linus Phase 2a assume all tasks are multi-agent from day one, or single-agent with parallel-agent support
  deferred to Phase 3?
- **Artifact routing and rendering.** Semantic Workbench supports Mermaid, plaintext, code. Should Linus tools emit
  structured artifacts (e.g., code diffs, plots, tables) with type hints, or assume Claude-compatible plaintext output?
- **Agent discovery and registration.** How should Linus discover available tools/agents at startup? Static config file
  (toml/yaml), runtime registry, or plugin-dir scan like Huginn?

---

_Repo-note written 2026-05-05._
