# memex (`cumberland-laboratories/memex`)

## 1. Purpose and scope

Memex is a "governed markdown knowledge structure that LLMs maintain and update across sessions" — a persistence layer
that lives entirely as a directory of plain markdown files in a git repo and is operated by whatever agentic CLI the
human launches at the repo root (Claude Code, Codex CLI, Gemini CLI). The package is not a server, library, or daemon;
it is a _constitution_ (`constitution-core.md` + a project-layer `constitution.md`), a _machinery directory_ (`.memex/`
with seven Python/shell scripts and six procedure docs), and a _knowledge-graph layout_ (`memex/` with `identity.md`,
`mission.md`, `inbox.md`, `active-threads/`, `threads/`, `artifacts/`, `reference-notes/`, `patterns/`). The Vannevar
Bush namesake is honored literally: the architecture is a small-world network of cross-referenced threads ("trails"),
not a hierarchical index, and navigation is by following annotated links from any entry node. For Linus this is the
strongest entry in the eight-repo memory survey on the question "what does the _human-facing surface_ of cross-session
memory look like before any retrieval substrate is involved" — directly relevant to the Layer C / Layer D conversation
in the memory-architecture spec, and to the "claim-typing" rule from the security/llm-wiki synthesis.

## 2. Architecture summary

The project's defining choice is that **agents enforce the rules by reading them, not by an SDK enforcing the agents**.
There is no ORM, no schema validator, no API surface. Governance lives at three layers, and the layering is the
contribution. (1) The constitution: `constitution-core.md` (~120 lines, portable) + `constitution.md` (~46 lines,
project-specific) define roles (`pi`, `agent`, `enforcer`, `crawler` — see `.memex/roles.yaml`), the three thread tiers
(`active-threads/` always loaded ≤ 8 files / ≤ 400 lines budget, `threads/` on-demand 5–20 lines, `artifacts/`
write-once deep storage), the thread schema (`## Summary` + `## Detail` + `## Connections` + optional
`## Open Questions` + `## Next Up`, with YAML frontmatter `last-touched`, `category`, `hits`, `tags`), the lifecycle
rules (60-line split threshold, demotion-not-deletion, capture-bias-without-asking-permission), and the operating-mode
signals (`*c` content-level vs `*m` meta-level, defaulting from `identity.md` `operating-mode:` frontmatter). (2) The
lint script `.memex/scripts/memex-lint.sh` (205 lines, pure bash, read-only) mechanically verifies the constitution:
budget totals, thread sizes, frontmatter presence, valid category vocabulary, broken cross-references, orphan threads,
active-thread count. (3) The enforcer is a _different vendor's model_ (Codex auditing Claude's writes, per the README's
adversarial-review framing) running with read-only access via `enforcer-audit.md` and dropping a dated report into
`docs/reports/`. The Python CLI `.memex/scripts/memex.py` (1.9k lines, git-style verbs: `status`, `search`, `read`,
`hit`, `connect`, `spawn`, `health`, `crawl`) is the agent's preferred orientation path — one
`status --full --role agent --format json` call returns graph health, inbox, due rhythms, and active-thread summaries in
place of ~14 raw file reads. `graph_health.py` (780 lines, NetworkX + matplotlib) scores the thread graph across
navigability, resilience, connectivity, efficiency, and legibility, and is explicit that 100/100 is wrong by design
("forced connections worse than honest gaps"). `spawn.py` clones the portable skeleton into a fresh project.
Dependencies are exactly four: `networkx`, `matplotlib`, `anthropic`, `python-dotenv`.

## 3. What's reusable in Linus

The constitution-as-prompt + lint-as-verifier pattern is directly transferable to Linus's Layer D shared memory
substrate (DEC-0029, DEC-0034). Where `agentmemory` and `engram` ship a Python API, and where `anamnesis` ships a
PostgreSQL+pgvector server, memex ships a _contract_ — and the contract is what Linus's memory architecture spec already
commits to (markdown-backed, git-versioned, content-hashed, schema-validated externally). The thread schema (Summary as
the documentation-extractable surface, Connections as annotated edges, Next Up as forward intent) is a better-developed
answer to the same question DEC-0033's `tags` and `parent_turn_id` columns are answering at a lower level. The
cross-vendor enforcer pattern — Codex audits Claude's writes, never the same model that wrote — maps directly onto the
security/llm-wiki synthesis's claim-typing rule and onto the Maestro/Worker discipline in CLAUDE.md (Maestro plans,
Worker implements, neither audits itself). The 400-line always-loaded budget is the same context hygiene argument that
motivates DEC-0036's KV-cache continuity requirement, but expressed at the file-organization layer where Linus does not
yet have a position. **Sibling differentiator vs `openaugi`** (the other markdown knowledge structure): `openaugi` is a
viewer/parser of an existing Obsidian vault (consumes graphs the human curates), whereas memex is a _write-side
discipline_ with mechanical compliance checks — the human writes nothing; the agent maintains the graph as a side effect
of conversation, and the lint script tells you when it stopped following the rules. **Sibling differentiator vs
`remember`** (the other entity-typed memory): `remember` types memories as entities with an SDK enforcing the typing,
while memex types threads by `category:` frontmatter with a shell script enforcing it — same goal, opposite philosophy
on where the rules live. Memex's bet is that constitution-as-prompt scales further because it is portable across vendors
(proven: same files run on Claude, Codex, Gemini), where SDK-enforced typing locks you into whichever client implements
the SDK.

## 4. What's inspiration only

The fictional-PI populated example (`tinyagent/` + Ren persona + `memex/charters/`) is a sales surface, not a starter
kit — `spawn.py` is the actual entry point. The graph-health-score machinery (`graph_health.py`, rendered PNG,
five-dimension scoring) is intellectually interesting and ships with a well-argued "do not chase 100" doctrine, but is
plausibly over-engineering for Linus's expected scale; the lint script alone provides the enforcement value. The
`charters/` extension (project-specific ground-truth API references the agent must read before modifying code) is a
coding-agent pattern adjacent to `claw-code-local`'s tool-calling discipline rather than to memory. The wiki render
(`generate_wiki.py`) is a third audit surface that would compete with KnowledgeBase's rendering rather than complement
it.

## 5. What's incompatible or out of scope

Memex assumes the agentic harness is _the runtime_ — the README's getting-started is "launch Claude Code from the repo
root and start working." Linus's orchestration layer is a backend behind an OpenAI-compatible endpoint, so any
constitution-as-prompt approach has to be re-injected as a system prompt or tool-result on every dispatch, not as a file
the harness happens to load. The `operating-mode:` toggle and the `*c` / `*m` prefix syntax are conventions between
human and agent; Linus would need to translate them into the router primitive, probably as `memory_mode` parameters per
DEC-0031. The `category:` enum (`mathematics|cognition|systems|ventures|economics|civic`) is wrong for Dan's domain —
biology, software, hardware, papers, threads would replace it — but this is a one-line edit to `memex-lint.sh`. The
cross-vendor enforcer presumes regular access to Codex; Linus's local-first commitment means the enforcer would need to
be a _different local model_ (e.g., Mistral-7B auditing Qwen2.5-Coder writes), which is testable but unproven. The
git-only persistence (no SQLite, no vector store) is not opposed to DEC-0029 — DEC-0029 explicitly includes git as the
third layer — but memex never reaches for retrieval beyond grep, which the memory-architecture spec rejects for Layer C
scale.

## 6. Recommendation: **Study**

Memex is the most-thought-through prior art on the _human-and-agent-facing surface_ of cross-session memory in the
group. It does not ship a substrate Linus would adopt (DEC-0029 already commits to SQLite + content hashes + git, and
memex commits to git alone). What it ships is a _constitution_ and a _lint script_ — both of which Linus needs and
neither of which is currently specified beyond the memory-architecture spec's API contracts. The right move is to
extract three artifacts from memex during Phase 2 memory pillar implementation: (a) the thread schema and frontmatter
contract as the model for Linus's Layer D record format, (b) the lint-script discipline as the model for an
orchestration-layer integrity check that runs on every commit to the memory store, (c) the cross-vendor enforcer pattern
as the model for Phase 3+ multi-Worker memory audits. Do not vendor the code; do not adopt the directory layout; do read
`constitution-core.md`, `thread-lifecycle.md`, `enforcer-audit.md`, and `memex-lint.sh` before drafting the Linus
memory-store schema and CI.

## 7. Questions for Dan

- **Constitution-as-prompt vs schema-as-API.** Memex bets governance lives in markdown the agent reads each session; the
  memory-architecture spec bets governance lives in `linus.memory.*` API shape and SQLite constraints. These are not
  exclusive — Linus could ship both — but if we ship both, which is canonical when they disagree? My read is the API
  contract wins (Workers cannot opt out of column constraints) and the constitution becomes a Maestro-only prompt layer;
  confirm or push back.
- **Cross-vendor enforcer for a local-only stack.** Memex's enforcer pattern depends on a _different vendor's_ model
  catching what the writer's model missed. Linus's local-first commitment means the enforcer would be a different
  _local_ model. Is that adversarial enough to do real work, or does the enforcer role need to escalate to hosted Claude
  (i.e., Maestro) on a periodic cadence to be trustworthy?
- **Lint-as-CI for the memory store.** Memex runs `memex-lint.sh` manually. Linus could run the equivalent as a git
  pre-commit hook on the memory-store directory or as a Phase 2a orchestration-layer health check. Which is the right
  tier — pre-commit (prevents bad writes) or background sweep (catches drift after the fact)?
- **Category vocabulary.** Memex enforces a six-value enum. The Linus equivalent would be the `tags` field in DEC-0033 —
  but is a controlled vocabulary an asset (lint can verify it) or a liability (you discover the seventh category
  mid-Phase-3 and have to migrate)? Memex's answer is enum-with-lint; Dan's instinct?
- **`openaugi` vs `memex` vs `remember` as the markdown/entity reference.** All three live in this group — write-side
  discipline, read-side viewer, SDK-enforced typing. Worth a comparison artifact in `docs/syntheses/` once all eight
  repo-notes are in, or is the memory-synthesis already carrying that load?
