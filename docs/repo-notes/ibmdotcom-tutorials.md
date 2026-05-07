# ibmdotcom-tutorials (`IBM/ibmdotcom-tutorials`)

## 1. Purpose and scope

IBM's "60+ tutorials" repository, maintained by the IBM.com Technical Content Team as marketing-adjacent educational
material for the watsonx.ai platform and the Granite model family. Sixteen top-level categories span RAG, single-agent
orchestration (LangChain/LangGraph), multi-agent systems (CrewAI, BeeAI, AutoGen, MetaGPT, ChatDev), prompt engineering,
multimodal AI, tool calling, guardrails, time series, NLP foundations, MCP, observability (AgentOps, Langfuse),
full-stack demo apps, LoRA fine-tuning, Docling (IBM's document parser), and IBM Bob (their coding-assistant product).
The repo is structurally unlike anything else in this group — paper-qa, aviary, ldp, robin, ether0, BixBench, LAB-Bench,
finch, and scientific-agent-skills are all research stacks or benchmarks; this is a tutorial collection. Most notebooks
require IBM watsonx.ai cloud credentials, putting the bulk of the content directly at odds with Linus's "no paid APIs
required for operation" north star.

## 2. Content overview

The 16 directories partition by learning intent rather than by codebase coherence — each tutorial is a self-contained
notebook or small project with its own setup. The signal-bearing categories for Linus are narrow:
`03-multi-agent-systems/` contains BeeAI A2A and ACP walkthroughs (`a2a_tutorial/`, `acp_tutorial/`,
`bee-ai-multi-agent-contract-management/`) which are essentially the only IBM-unique content — BeeAI is IBM's own agent
framework and the Agent2Agent / Agent Communication Protocol are IBM-led specifications. `15-docling/` covers IBM's
open-source PDF/document parser, the most practically useful piece of IBM tooling for KnowledgeBase-style work.
`07-guardrails-and-safety/` includes Granite Guardian (an IBM safety classifier) and `ai-agent-security/` (auth, RBAC,
data-protection patterns for agents). `11-model-context-protocol/` and `16-ibm-bob/mcp-server-integration-ibm-bob/` are
MCP primers; useful only if MCP becomes Linus's tool-registration substrate in Phase 3. Categories 01, 02, 04, 06,
08–10, 12–14 are conventional LangChain/LangGraph/CrewAI tutorials wrapped around watsonx endpoints — content available
in better form upstream.

## 3. What's reusable in Linus

Three narrow slivers, in descending order of practical value. First, the Docling tutorials (`15-docling/`) — Docling is
an Apache-2.0 IBM project for parsing PDFs, scans, slides, and Office docs into structured Markdown/JSON, and unlike
most of this repo it runs locally without watsonx. If KnowledgeBase's paper-ingestion pipeline ever needs a stronger PDF
parser than pypdf, Docling is the obvious next step and these notebooks are the fastest on-ramp. Second, the BeeAI A2A
and ACP tutorials in `03-multi-agent-systems/` are the only place to learn IBM's agent-communication protocols at the
tutorial level; if Linus's Phase 3 multi-agent fan-out ever needs a wire protocol beyond ad-hoc JSON, A2A is one of the
candidates and these notebooks are reference material. Third, `12-observability-and-monitoring/` shows Langfuse wiring
patterns that translate to any LLM stack, not just watsonx — Langfuse is local-deployable and Linus's audit-log
requirements (CLAUDE.md, SAFETY.md) overlap with what Langfuse offers.

## 4. What's inspiration only

Compared to its siblings in this group, ibmdotcom-tutorials is the structural odd one out — paper-qa, aviary, ldp,
robin, ether0, finch, and scientific-agent-skills are FutureHouse research stacks intended to be _consumed as code_;
BixBench and LAB-Bench are evaluation harnesses intended to be _run against_ a system. ibmdotcom-tutorials is neither.
It's a marketing surface for watsonx that Linus has no use for as a runtime dependency, and even the conceptual material
(RAG patterns, agent orchestration, prompt engineering) is covered more deeply by sources Dan already has — Karpathy's
autoresearch, the Cline prompt-variants codebase, or any of the FutureHouse repos. The full-stack demo apps in
`13-full-stack-applications/` (AI Stylist, TTRPG AI, Silly Story Time) are pedagogically cute but not reference-grade.

## 5. What's incompatible or out of scope

The bulk of the repo is incompatible with Linus's commitments. Tier 0 #0 of the environment-cleanup decisions removed
LangChain and LangGraph from `environment.yml`; tutorials in categories 01, 02, and large parts of 03–07 are built on
exactly that stack and would have to be rewritten to be runnable here. Most notebooks require an IBM watsonx.ai account
and cloud credentials, violating the "no paid APIs required" north star. CrewAI, AutoGen, MetaGPT, and ChatDev are all
heavyweight Python frameworks Linus has no commitment to; BeeAI is Apache-2.0 but is one more agent framework on a pile
that Linus is deliberately not joining. The IBM Bob category (`16-ibm-bob/`) is documentation for IBM's proprietary
coding assistant — directly competitive with the Maestro/Worker setup Linus is built around, and not something Linus
would adopt.

## 6. Recommendation: **Ignore**

Treat the whole repo as ignore-by-default. Do not vendor anything; do not import any notebook into Linus; do not let the
LangChain/LangGraph patterns leak into the Linus codebase given the explicit removal of those libraries. The three
narrow exceptions (Docling, BeeAI A2A/ACP, Langfuse wiring) can be revisited as standalone references if and when those
specific needs arise — Docling most plausibly for KnowledgeBase Phase 2, A2A only if Phase 3 multi-agent needs a
protocol decision, Langfuse only if Phase 2 audit logging needs a heavier solution than a SQLite event table. None of
those revisits requires keeping the clone; the repo can be deleted from `repos/` without loss.

## 7. Questions for Dan

- **Docling for KnowledgeBase ingestion.** Your current pipeline uses pypdf with the decompression-limit workaround.
  Docling handles scans, tables, and slide decks that pypdf mangles. Worth a Phase 2 spike to compare on a sample of
  your harder papers — chemistry-figure-heavy, table-heavy, or scanned legacy PDFs — or is pypdf good enough for the
  corpus you actually have?
- **A2A vs ad-hoc.** When Phase 3 multi-agent fan-out lands, do you want a named wire protocol (A2A, ACP, MCP, or
  similar) for Worker-to-Worker communication, or is in-process Python plus a shared session store enough for the scales
  Linus operates at?

  _Partially resolved (DEC-0051, see [answered-questions.md](../questions/answered-questions.md)): AgentReport typed
  inter-agent message format adopted for Phase 3+; A2A/ACP specifically not adopted._

- **Langfuse vs homegrown audit log.** SAFETY.md implies an audit log without specifying its shape. Is a Langfuse-style
  trace store the right target for Phase 2, or does a SQLite event table satisfy the auditability goal at lower
  complexity?

  _Partially resolved (DEC-0029, see [answered-questions.md](../questions/answered-questions.md)): Episodic memory
  substrate is SQLite + content hashes + git; audit log shape follows the same substrate. Langfuse not adopted._

- **Anti-pattern enforcement.** The LangChain/LangGraph removal was decided once. Is it worth a one-line lint check or a
  pre-commit hook that flags `import langchain` / `from langgraph` to keep that decision from drifting back in via
  copied tutorial code?
- **Granite as a worker model.** IBM's Granite 3.x models are Apache-2.0 and available via Ollama. Do they merit a
  benchmark slot in the Phase 1c worker-model bake-off alongside Qwen2.5-Coder and Mistral-7B, or is the 3B/8B Granite
  family not competitive enough on your task suite to spend the eval cycles?

  _Resolved (S7, S12, see [answered-questions.md](../questions/answered-questions.md)): Phase 1c four-way bake-off
  fixed at Bonsai 8B 1-bit, PrismML ternary 8B, BitNet 2B4T, and FP16 baseline; Qwen3 is the Worker floor. Granite not
  in the Phase 1c slate._
