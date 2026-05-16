# vellum-assistant (`vellum-ai/vellum-assistant`)

## 1. Purpose and scope

Vellum Assistant (vellum-ai/vellum-assistant; TypeScript + Bun; MIT; commercial-backed by Vellum, the LLM-ops product
company) is **"a personal AI assistant that evolves with you"** — a privacy-conscious local-or-managed AI assistant
that learns user preferences, builds a per-user identity, proactively reaches out when something matters, and runs in a
fail-closed security envelope. The repo is unusually well-developed for a 2025-2026 personal-assistant project: a
substantial monorepo (`apps/`, `packages/`, `clients/`, `cli/`, `assistant/`, `benchmarking/`, `evals/`, `gateway/`,
`credential-executor/`, `skills/`), Bun-based TypeScript stack, with both a managed-cloud deployment mode (Vellum Cloud)
and a local-only mode where everything runs on the user's machine. Embeddings run locally by default.

The four-pillar marketing framing is precise:

- **Memory** — "Learns what matters and forgets what doesn't." Structured memory items (identity, preferences,
  projects, events) extracted with source attribution and deduplication. Hybrid retrieval (dense + sparse) ranks results
  semantically and lexically. Staleness windows per memory type. Per-user and per-channel isolation. Embeddings local
  by default.
- **Identity** — "Becomes its own." Behavior lives in `SOUL.md`; during onboarding the assistant observes how the user
  communicates and writes its own personality files. Per-user journal captures reflections on past interactions.
  `NOW.md` is an ephemeral scratchpad for current focus and active threads.
- **Proactivity** — "Reaches out when something matters, without being asked." Every hour the assistant re-reads its
  notes, notices what's unfinished or due soon, and sends a message if needed. Notifications route to the right channel,
  won't interrupt active conversations.
- **Security** — "Fail-closed by design." Actor identity resolved once (guardian, trusted, or unknown) and enforced
  everywhere. Untrusted actors cannot read/write memory, trigger tools, or escalate. Credentials live in a separate
  process and never reach the model. Every tool runs in a sandbox.

The infrastructure framing names additional pillars: a **Trust Engine** (fail-closed actor identity), **Skills**
(manifest-driven plugins with `SKILL.md` + `TOOLS.json`), an **Evals** + **Benchmarking** suite, a **Gateway**
(presumably the OpenAI-compat HTTP surface), a **Credential Executor** (separate-process credential isolation), an
**Experimental** lane, and the **CLI** + **Apps** front-ends.

## 2. Architecture summary

**Monorepo layout (from the file listing):**

```
vellum-assistant/
├── apps/                  # End-user app surfaces (desktop, CLI, web?)
├── packages/              # Shared libraries
├── clients/               # Per-platform clients
├── cli/                   # Command-line interface
├── assistant/             # Core assistant runtime
├── benchmarking/          # Benchmark harness
├── evals/                 # Evaluation suite
├── experimental/          # Experimental lane
├── gateway/               # OpenAI-compat HTTP gateway
├── credential-executor/   # Credential-isolation subprocess
├── skills/                # Plugin / skill manifests
├── meta/                  # Meta-config
├── docs/                  # Documentation
├── scripts/               # Build / setup scripts
├── ARCHITECTURE.md        # Top-level architecture doc
├── AGENTS.md              # Agent design doc
├── CONSTITUTION.md        # Identity / behavior constitution
├── GLOSSARY.md            # Terminology
├── SECURITY.md            # Security model
├── CODE_OF_CONDUCT.md     # Project policy
├── CONTRIBUTING.md        # Project policy
├── README.md              # User-facing README
├── bunfig.toml            # Bun configuration
├── socket.yml             # Socket networking config
├── setup.sh               # Setup script
└── test-preload.ts        # Test preloading
```

**Stack:** Bun (TypeScript runtime + package manager + test runner), TypeScript strict mode, monorepo via Bun
workspaces. The presence of `socket.yml` suggests structured network configuration; the `credential-executor/`
subdirectory suggests separate-process credential isolation; the `gateway/` is presumably an OpenAI-compat HTTP layer.

**Memory model:** Structured items (identity / preferences / projects / events) with source attribution and
deduplication. Hybrid dense + sparse retrieval. Staleness windows per type. Per-user and per-channel isolation.
Embeddings local by default.

**Identity model:** `SOUL.md` for behavior, per-user journal for reflections, `NOW.md` for ephemeral focus. The model
authors its own personality files during onboarding.

**Proactivity model:** Hourly re-read of notes plus structured noticing of unfinished/due-soon items, with
context-aware notification routing.

**Security model:** Trust Engine resolves actor identity to guardian / trusted / unknown; enforces fail-closed at every
boundary. Credentials live in a separate process (`credential-executor/`). Tools run in sandboxes.

**Skills model:** Manifest-driven plugins with `SKILL.md` (prompt section) + `TOOLS.json` (tool schema). Skills can be
bundled, installed from a catalog, or added from the workspace.

## 3. What's reusable in Linus

**The four-pillar memory/identity/proactivity/security framing is a coherent personal-assistant vocabulary.** Linus's
documentation currently uses memory-layer vocabulary (Layer A-E per DEC-0028) but has no explicit "identity" or
"proactivity" framing. The Vellum vocabulary is portable as a higher-level user-facing description. The Phase 5+
interface-refinement work (per ROADMAP.md) should consider adopting this framing for user-facing documentation.

**The `SOUL.md` + `NOW.md` + per-user-journal pattern is a Layer B/C realization.** `SOUL.md` (durable behavior) =
Linus's Layer C semantic-knowledge slice; `NOW.md` (ephemeral focus) = Linus's Layer B within-session scratchpad; the
per-user journal = Linus's Layer C episodic store. The naming convention is more user-facing than Linus's Layer A-E
vocabulary; for a Phase 5+ user-facing surface, the Vellum naming is more accessible.

**The trust engine pattern — actor identity resolved once, enforced everywhere.** This is the **structural realization
of Linus's SAFETY.md autonomy-tier model**. The Trust Engine pattern with three actor classes (guardian/trusted/
unknown) is a concrete implementation of the autonomy-tier graduation per SAFETY.md. For the Phase 5+
interface-refinement work, the Trust Engine pattern is portable as a Linus identity layer.

**The credential-executor separate-process pattern.** Running credentials in a separate process that never reaches the
model is a strong security primitive. For Linus's Phase 7+ biology Workers that need API keys (e.g., for BLAST queries,
PubMed access, AlphaFold-Multimer calls), the credential-executor pattern is a portable security architecture. The
DEC-0024 supply-chain-posture commitment can extend to this.

**Manifest-driven skills (`SKILL.md` + `TOOLS.json`).** This is the **closest precedent** in the cloned-repo collection
for the Linus tool registry per DEC-0046. The pattern — a Markdown file specifying the skill's prompt section + a JSON
file specifying the tool schema — is directly portable. Linus's tool registry should adopt this two-file pattern for
each registered skill.

**Hybrid dense + sparse retrieval.** The Vellum memory model uses hybrid dense + sparse retrieval for memory items.
This is the same RRF-over-BM25-and-vector pattern that agentmemory canonicalizes (per
[`agentmemory.md`](agentmemory.md)). Two independent 2025-2026 personal-assistant codebases converging on the same
retrieval pattern is a strong signal. The Linus Layer C consolidation per DEC-0029 should adopt this as the v0
retrieval shape.

**Proactivity as a Phase 5+ extension.** The hourly-re-read-and-notice pattern is a useful framing for a Phase 5+
notification surface. The Linus dispatch layer per DEC-0031 currently doesn't include a proactivity primitive; for
Phase 5+ interface refinement, a hourly-re-read-and-notice Worker is a portable pattern.

**`AGENTS.md` + `CONSTITUTION.md` + `GLOSSARY.md` as top-level documentation conventions.** Vellum's top-level
documentation (`ARCHITECTURE.md`, `AGENTS.md`, `CONSTITUTION.md`, `GLOSSARY.md`, `SECURITY.md`) maps cleanly onto
Linus's top-level convention (CLAUDE.md, VISION.md, ARCHITECTURE.md, ROADMAP.md, SAFETY.md, GLOSSARY.md). The naming
parallel is striking — independent convergence on the same documentation structure.

## 4. What's inspiration only

**TypeScript + Bun stack is incompatible with Linus's Python orchestration core.** Linus commits to Python as the core
orchestration language (DEC-0027 multi-language stance allows TS/JS components where they fit). The Vellum-Assistant
codebase is too large (12+ subdirectories) and too TS-native to vendor; the patterns are portable, the implementation
is not.

**Commercial-backed development pace.** Vellum (the company) backs the repo. The development pace is fast (substantial
monorepo with onboarding, journal, NOW.md mechanics). Linus's single-developer pace cannot match the
commercial-development-team pace; trying to keep up with Vellum's feature additions is the wrong calibration.

**Vellum Cloud as a managed mode.** Vellum's managed-cloud mode is incompatible with Linus's local-first commitment
(per DEC-0023 output-interface citations, the "stays fully under Dan's control" north star). The local-only mode of
Vellum is the relevant comparison; the managed mode is out of scope.

**The personal-assistant framing is broader than Linus's orchestration-backend framing.** Linus is an orchestration
backend; Vellum is an end-user personal assistant. The framing differs. Vellum's identity/proactivity primitives are
Phase 5+ user-facing concerns for Linus; the Phase 1-3 orchestration work doesn't directly benefit from them.

## 5. What's incompatible or out of scope

**TypeScript-native monorepo with 12+ subdirectories.** Vendoring is impractical. Linus's discipline of keeping the
orchestration layer small argues against attempting to absorb Vellum's monorepo structure.

**Per-user / per-channel isolation requires multi-user infrastructure.** Vellum is multi-user by design; Linus is
single-user (Dan) by current scope. The per-user / per-channel isolation primitive is well-engineered but not yet
needed; Phase 8+ if Linus grows to multi-user.

**Skill catalog and skill marketplace assumption.** Vellum's "skills installed from a catalog" framing assumes a skill
catalog exists. Linus's tool registry per DEC-0046 is internal to Linus; no catalog. The catalog framing is out of
scope for Linus's current phase.

**Onboarding flow with personality-file generation.** The "during onboarding the assistant observes how you communicate
and writes its own personality files" is a Phase 5+ user-facing flow. For Linus's Phase 1-3 work where the single user
is Dan and the orchestration backend is the product, no onboarding flow is needed.

**Socket-based networking (`socket.yml`).** Vellum's networking layer is socket-configured. Linus's Phase 2a backend
is FastAPI HTTP (per DEC-0005 OpenAI-compat). The socket-based primitive is incompatible.

## 6. Recommendation: **Study**

Vellum Assistant is a **design-vocabulary cross-reference** for Phase 5+ interface refinement and the Linus tool
registry's manifest-driven skill pattern. The four-pillar framing (memory/identity/proactivity/security), the
`SOUL.md`/`NOW.md`/per-user-journal naming, the Trust Engine pattern, the credential-executor separate-process pattern,
and the manifest-driven `SKILL.md` + `TOOLS.json` skill format are all worth lifting as design vocabulary. The
implementation is too large (TypeScript monorepo, commercial-backed pace, multi-user infrastructure) to vendor.

The closest Linus design-vocabulary reference: Letta (`letta-ai/letta`, per [`Letta.md`](Letta.md)) covers the same
personal-assistant space with explicit memory blocks; Vellum covers a wider scope (identity, proactivity, trust engine,
credential isolation) but at a higher operational-investment level. Both are Study-level cross-references; neither is
vendored.

For Linus's Phase 5+ interface refinement work, the Vellum framing is the **most user-accessible** of the cloned-repo
personal-assistant references. The DEC-0046 tool-registry skill manifest pattern (`SKILL.md` + `TOOLS.json`) is the
**most directly portable** technical pattern.

## 7. Questions for Dan

1. **Adopt the `SKILL.md` + `TOOLS.json` manifest pattern for the Linus tool registry?** DEC-0046 commits to a tool
   registry with a deployment field; the manifest pattern is a concrete implementation. Worth lifting with attribution.

2. **The `SOUL.md` / `NOW.md` / per-user-journal naming for Phase 5+ user-facing memory.** Linus's Layer A-E vocabulary
   is internal-engineering. For Phase 5+ user-facing surfaces, the Vellum naming is more accessible. Worth a Phase 5+
   spec inclusion?

3. **Trust Engine pattern as SAFETY.md autonomy-tier realization.** The three-actor-class model
   (guardian/trusted/unknown) is a concrete implementation of SAFETY.md's autonomy-tier graduation. Worth a SAFETY.md
   update to reference the Trust Engine pattern as the implementation primitive?

4. **Credential-executor separate-process pattern for Phase 7+ biology Workers.** Phase 7 biology Workers will need
   API keys (BLAST, PubMed, AlphaFold). The separate-process credential isolation is a portable security architecture.
   Worth a Phase 7 spec inclusion?

5. **Hybrid dense + sparse retrieval as the Layer C v0 retrieval shape.** Two independent codebases (Vellum,
   agentmemory) converge on this pattern. Worth committing to as the DEC-0029 v0 retrieval shape?

6. **Proactivity primitive for Phase 5+.** The hourly-re-read-and-notice pattern is suggestive. For Linus's Phase 5+
   interface refinement, a proactivity Worker that re-reads investigation memory and notices what's unfinished is a
   portable pattern. Worth a Phase 5+ feature inclusion?
