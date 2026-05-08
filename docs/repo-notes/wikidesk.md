# wikidesk (`ilya-epifanov/wikidesk`)

## 1. Purpose and scope

wikidesk is a Rust **companion server** for Karpathy's LLM-wiki pattern. Its central conceit is that it is _not_ a wiki
engine: it does not own the content model, the prompts, the topic structure, or the agent that does the writing. It only
requires that the target repo contain a `wiki/` subdirectory of markdown. Agents read that directory directly as their
knowledge base; on top of that, wikidesk exposes an MCP server with two tools — `research` (submit a question, get a
`task_id`) and `get_result` (poll until a research agent finishes updating the wiki and returns an answer with
`[[wikilinks]]` rewritten to file paths). The intended consumer is multiple coding agents — Claude Code, Codex,
OpenCode, Cline, etc. — sharing one wiki across machines via a client-server sync protocol. For Linus this is the first
repo in the LLM-wiki sibling group that treats the wiki as a _service_ instead of a workflow, which makes it the most
architecturally interesting one for the Phase 2 KnowledgeBase pillar.

## 2. Architecture summary

A small, focused Rust workspace of three crates: `wikidesk-server` (axum HTTP + rmcp MCP server, the queue, the runner
abstraction, wikilink rewriting), `wikidesk` (a thin CLI client that does `research` and `sync` against the server over
HTTP), and `wikidesk-shared` (request/response types and a `snapshot_dir` helper for the file-set diff sync). The server
exposes both `/mcp` (streamable HTTP MCP transport) and `/api/research` + `/api/sync` REST endpoints, so an agent can
use either MCP or plain HTTP. Concurrency is bounded by a 2-permit semaphore (`MAX_CONCURRENT_RESEARCH`) and a 128-slot
mpsc queue. The research worker is a swappable `Runner` trait with three implementations under `server/src/runner/`:
`generic` (spawn agent_command, capture stdout), `stream-json` (parse Claude Code's `--output-format=stream-json` for
live progress), and `acp` (Agent Client Protocol via `claude-agent-acp`, with bypass-permissions configured through
`<wiki_repo>/.claude/settings.json`). Sync is a diff-on-snapshot model: client posts its current file set, server
returns upserts and deletes, client applies them with path-traversal validation. The whole thing is ~2.4k lines of Rust.

## 3. What's reusable in Linus

The runner trait + sync protocol is the directly liftable idea. Linus's Phase 2 KnowledgeBase needs an agent-facing
surface, and wikidesk's `Runner` abstraction (one trait, three implementations, swap by config) is a clean template for
"spawn a research agent against my corpus, capture its output." More importantly, the **multi-agent-share** angle is the
genuine differentiator inside this sibling group: wikidesk explicitly assumes N agents on N machines pointing at one
server, with `wikidesk sync` wired into harness lifecycle hooks (Claude Code PreToolUse/Stop, Cline custom modes, etc.)
so the local mirror stays current. Compared with `link` and `llmwiki` (both single-agent, single-repo workflows that the
user runs locally), wikidesk is the only one that has thought about deployment topology at all. That maps onto Linus's
eventual reality where Claude Code, claw-code-local, Cline, and openclaw all want to consult the same KnowledgeBase
concurrently.

The dispatchable `research` MCP tool is the second differentiator worth naming. Several siblings expose the wiki as
read-only context; wikidesk lets a calling agent _delegate_ a research subtask to a sandboxed worker that mutates the
wiki and returns an answer. That is the Maestro/Worker pattern in miniature, implemented at the MCP-tool granularity,
and it is a useful prior art for Phase 3's agent fan-out story. The `instructions` and `research_tool_description`
config knobs (which inject domain-specific guidance into the MCP advertisement) are a small but smart pattern Linus's
tool registry could copy directly.

## 4. What's inspiration only

The agent_command spawn model assumes the worker is itself a frontier-grade coding agent (Claude Code or equivalent)
running with `--dangerously-skip-permissions` inside a Docker/bubblewrap sandbox. That is the inverse of Linus's
posture, where the local Worker is a small Ollama/pmetal model and the sandboxing tier is set by Linus itself per
SAFETY.md. The wikilink-rewriting (`rewrite.rs`) and `[[page]]`-based content model are LLM-wiki-format specific; if
Linus's KnowledgeBase keeps its existing schema rather than adopting LLM-wiki, this code does not port.

## 5. What's incompatible or out of scope

ACP runner depends on `claude-agent-acp`, which is Anthropic-account-bound — fine for Maestro, not usable for the
fully-local worker tier. The full-permissions security model demands real OS sandboxing, and Docker on macOS does not
pass through Metal/ANE; if Linus ever runs the research-agent loop with a local model, the sandbox layer has to be
macOS-native (Seatbelt, app sandbox, or bubblewrap-equivalent), which wikidesk does not solve. The client-server sync is
whole-file diff with no merge logic, so true concurrent edits to the same page across two agents will lose data —
acceptable for a wiki that one research agent at a time mutates, not acceptable as a general KB write path.
Single-maintainer Rust project at `0.1.2`, MIT/Apache.

## 6. Recommendation: **Study**

Don't vendor or take a build dependency. Do read `server/src/runner/mod.rs`, `queue.rs`, and the sync protocol in
`shared/src/lib.rs` + `client/src/main.rs` before designing the Phase 2 KnowledgeBase agent interface — they are a
~2.4k-line concrete example of "MCP server fronting a corpus that multiple agents share," which is exactly the shape
Linus wants. The runner trait and the lifecycle-hook sync pattern are the two ideas worth porting in spirit. Revisit if
Phase 3 fan-out needs a precedent for queued, bounded-concurrency research subtasks.

## 7. Questions for Dan

1. **Multi-agent share vs single-process orchestration.** wikidesk solves "N agents on N machines, one wiki." Linus
   Phase 2 today is "N harnesses, one machine, one orchestration backend." Is the multi-machine case (e.g., M1 Max
   - Mac Studio, or laptop + desktop) something to plan KB access around now, or YAGNI until Phase 8?
2. **Research-as-tool granularity.** wikidesk's `research` tool dispatches a full agent run that may take 30 minutes.
   Linus's tool registry has so far been imagined as fast, deterministic functions. Do you want to admit long-running,
   queued, pollable tools as a first-class category in the Phase 2a registry, or keep that pattern outside the registry
   and behind a separate "agent fan-out" surface?
3. **Wiki format vs KnowledgeBase schema.** wikidesk assumes `[[wikilink]]`-style markdown. Your KnowledgeBase has its
   own schema (papers, notes, a knowledge graph). Is there interest in maintaining a parallel `wiki/`
   human-and-agent-readable view of the KB, or does the existing query/RAG surface stay the only access path?
4. **Sandboxing the worker on macOS.** wikidesk explicitly punts to Docker/bubblewrap. If Linus ever runs an autonomous
   research-agent loop on the M1 Max, what's the macOS-native sandbox plan (Seatbelt profiles? app-sandbox? confined
   launchd jobs?), and is that a Phase 7 concern or do we want a sketch in SAFETY.md sooner?
