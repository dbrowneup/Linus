# Agent Market — Claude Code Context

> **Status:** Draft proposal, written 2026-05-11 (Day 1). The intent is that this file becomes the
> `CLAUDE.md` at the root of the hackathon repo and is read at the start of every Claude Code
> session in this repo. Several sections (license, real-MCP commitment, demo vertical, 6th team
> member) are explicitly flagged as **pending team decision** — anyone updating those should
> remove the flag and date the change.

## Project

**Agent Market** — a marketplace where users hire specialized AI agents per operation and developers
earn through USDC payments on Arc.

Built for the **Arc / Circle AI Agents Hackathon**, May 11–25, 2026.

- Repository: `git@github.com:ShimonNavon/hackathon.git`
- Deploy target: `hackathon.navontech.dev` (Google Cloud VM at `136.113.230.93`, Cloudflare proxy +
  Let's Encrypt SSL)
- Primary branch: `main`

## North Star

A user with a job they want done browses a catalog of agents, picks one, hires it for a single
operation, watches the agent complete the work using a transparent set of tools, and pays in USDC on
Arc. The developer who built the agent earns a payout. The platform takes a cut and surfaces a
verifiable record of what the agent did, so reputation is based on **what happened**, not on what
the agent claims about itself.

The platform's defensible value is the **agent passport** — a verifiable history of each agent's
prior jobs, the tools it used, and the reasoning trace behind its outputs — not the agents
themselves. Quality risk is transferred to developers, who are rewarded when their agents perform
and earn nothing when they don't.

## Tech Stack

| Layer            | Technology                                            |
| ---------------- | ----------------------------------------------------- |
| Frontend         | React 18, Vite, static build served by Nginx          |
| Backend          | FastAPI, Python 3.12, Uvicorn                         |
| Database         | PostgreSQL 16                                         |
| ORM              | SQLAlchemy                                            |
| Containerization | Docker Compose (dev + prod compose files)             |
| Reverse Proxy    | Host Nginx                                            |
| SSL              | Let's Encrypt with Cloudflare proxy                   |
| CI/CD            | Jenkins (already wired)                               |
| Payments         | USDC on Arc, **initially mocked**, real settlement W2 |
| Agent Tools      | **MCP — protocol vs. "MCP-style" pending decision**   |

## Team (6 members; timezone spread; age range ~early-20s to early-40s)

Roughly balanced bios. Ages are author estimates pending team confirmation; the ~20-year span is
itself a feature — early-career energy meets multi-decade quant-finance and product depth.

| Name                       | Age (est.) | Location  | TZ (May DST) | Role / strengths                                                                                            |
| -------------------------- | ---------- | --------- | ------------ | ----------------------------------------------------------------------------------------------------------- |
| **Shimon Navon**           | late 20s   | Tel Aviv  | UTC+3        | Backend + DBA, project originator. Shipped the live infra Day 1. PostgreSQL, Django REST, Docker, CI/CD, cloud (GCP/Azure/AWS). |
| **Marten Windler**         | ~31        | Bremen    | UTC+2        | Systems Engineering at U. Bremen, finishing B.Sc. on ML uncertainty quantification. ROS, Python/C++/Rust. Coordinator instincts. |
| **Daniel Reis dos Santos** | early 20s  | Brazil    | UTC-3        | Backend engineer. Go / Java / TypeScript, distributed systems, Kafka, AWS, Terraform. Healthcare-ERP day role. |
| **Dan Browne**             | 37         | Chicago   | UTC-5        | Senior Scientist at LanzaTech, PhD biochemistry. Python / bioinformatics / agentic systems. Evenings + weekends only. |
| **Chuan Bai**              | ~early 40s | London    | UTC+1        | CTO @ [Gyld Finance](https://www.gyld.fi/) (institutional staking). Built CoinShares' next-gen digital-asset trading platform. RWA tokenization expertise. PhD HPC. Owns smart contracts + Arc. |
| **Önder Akkaya**           | ~21        | Ankara    | UTC+3        | Statistics @ Hacettepe; [ASA Statistical Insight World Champion](https://www.linkedin.com/in/onder-akkaya/); President of [TİD-Genç](https://www.tid.org.tr/) (Young Statisticians). Owns the math engine (stochastic processes, Kelly Criterion). |

Three team members (Dan, Daniel R, Chuan) have demanding day roles and commit
evenings/weekends or partial days; Önder and Marten are students with flexible time; Shimon
is currently self-employed with the most flexibility.

**Proposed daily sync window:** 13:00 UTC = 8am Chicago / 10am São Paulo / 14:00 London /
15:00 Bremen / 16:00 Ankara + Tel Aviv. Works for the full team without anyone in unsocial
hours.

**Proposed schedule/flow owner:** Marten (showing coordinator instincts in early threads). Open to
discussion; the role is "runs daily standup, tracks blockers, owns demo-prep narrative."

**Role allocation (working draft, refine as the team aligns):**

- **Shimon** — backend + infra ownership; the marketplace runtime and job pipeline.
- **Marten** — schedule/flow owner; demo-agent build with Dan; ML/uncertainty patterns where
  they apply to reputation modeling.
- **Daniel R** — backend support; MCP server implementations; reliability and observability.
- **Dan** — architecture, agent passport spec, pitch-deck strategy, demo-script narrative;
  domain credibility for scientific-intelligence vertical extension story in the deck.
- **Chuan** — smart contracts (escrow + passport anchor) on Arc; on-chain integration;
  Q&A primary for custody, settlement, and Arc questions; RWA-contextual framing in the
  pitch.
- **Önder** — agent decision-making math (stochastic processes, Kelly Criterion for any
  +EV/risk-modeled agents); statistical rigor for the reputation/passport metrics; native
  Turkish gives him an angle on the Canteen RFB iv translation-as-alpha vertical if we
  pursue it.

## Scope — what we are and aren't building

### In scope for the 2-week hackathon demo

- Marketplace UI with **2–3 curated demo agents** (not third-party onboarding)
- End-to-end flow: user browses → user hires → backend creates job → agent runs → result saved →
  USDC settles on Arc → developer earns payout
- Agent passport with public profile, price per operation, and **verifiable action history** (the
  passport spec is delivered separately as `docs/agent-passport-spec.md` when ready)
- MCP-based tool layer wired into at least one demo agent (assuming real-MCP commitment)
- Mock USDC in week 1, **real Arc settlement live by demo day**

### Explicitly out of scope

- Third-party developer onboarding (curated only for v1)
- Full slashing / predictive-performance reputation mechanic. **v1 reputation = verifiable history,
  not predictive performance.** Hyperliquid leaderboard rank doesn't persist out-of-sample; we don't
  pretend ours will.
- Self-hosting story for developers (we host for v1)
- Multi-vertical breadth — **pick one vertical, polish it**
- Platform custody of user funds — **never. Use on-chain escrow per job.**
- Public launch / external user acquisition. The deliverable is a demo, not a product.

### Demo vertical — pending team decision

The Agora hackathon is heavily crypto-finance-oriented and the three demo agents in the current
README (News Trader, Whale Watcher, Risk Checker) are all finance-focused. The recommendation under
review is to **avoid pure-trading as the lead demo** for three reasons: (1) regulatory exposure, (2)
custody complexity scales nonlinearly, (3) reputation-credibility on small samples is the hardest
case. Alternative verticals worth considering: on-chain research, whale-watching alerts,
news-to-prediction-market translation (Canteen's own RFB suggestion iv), signal verification.
Trading can remain the v2 story in the pitch deck without being the demo build.

**Decision pending — to be aligned by end of Day 2.**

## Engineering conventions

### Branch model (lighter than a long-running project)

- `main` is protected. Every change goes through a PR; no direct push to `main`.
- Feature branches: `feature/<short-name>` (e.g. `feature/agent-passport`, `feature/job-runner`).
- Fix branches: `fix/<short-name>`.
- Smart-contract branches: `contract/<short-name>` — these get **two reviews** (Chuan + one
  generalist) because contract bugs are expensive.
- Experiment branches: `experiment/<short-name>` — throwaway, no review required, deleted after
  merging-or-discarding.
- Personal staging branches: `<name>/<short-name>` (e.g. `dan/passport-schema-spike`).
- **No force-push to `main`. Ever.** Force-push to your own branch before opening a PR is fine.

### PR reviews

For a 6-person hackathon team operating async across 4 timezones, **one approving review** is
enough for non-contract changes. Contract changes get two. Reviewers should respond within ~12 hours
during the hackathon so the contributor isn't blocked overnight.

### Commit style

Imperative mood ("Add agent passport schema" not "Added agent passport schema"). Scope tags optional
but encouraged: `[backend]`, `[frontend]`, `[contracts]`, `[infra]`, `[docs]`. Atomic commits — one
logical change per commit, no bundling unrelated work.

### Smoke-test before deploy

The deploy target is shared infrastructure. Don't push to `hackathon.navontech.dev` without smoke
testing locally first (`docker compose up --build` and the documented MVP flow works). If the
deploy is for a smart-contract change, run the contract against an Arc testnet first.

### Don't connect important wallets

Standard hackathon hygiene: use a fresh dev wallet for testing, never your real one. Don't paste
private keys anywhere in this repo. Don't paste API keys; use `.env.example` as the template and
keep `.env` gitignored.

### License — pending decision

Currently "Private hackathon project. License to be decided." This needs to be locked **before
the team grows further or before any external contributor lands a PR.** Recommendation: MIT or
Apache-2.0 for permissive ecosystem-friendly choice, consistent with the hackathon's open-builder
ethos. Decision should happen in the first week.

## Architectural primitives we want to get right

These are the small number of architectural choices where being thoughtful early pays off
disproportionately at demo time. Specs for each will land in `docs/` as they're written.

### The agent passport

The single biggest defensibility argument we have. Each completed job should produce a record that
includes:

- The job's `id`, `agent_id`, `user_id`, `timestamp`
- The reasoning trace the agent produced (or a content hash anchored to off-chain storage)
- The tool calls invoked, with their inputs and outputs
- The result delivered to the user
- (Optionally, in v2) the user's rating and any dispute flag

The point is that the passport is built from **what happened**, not from what the agent claims.
Future buyers can audit prior jobs before hiring. Reputation gaming via self-reporting is foreclosed
by design.

Implementation should add at minimum two tables beyond the current `Agent` / `Job` / `ToolCall` /
`Payment` set: a `ReasoningTrace` table (job_id, content_hash, storage_pointer, created_at) and a
`ToolCallProvenance` table (job_id, tool_call_id, tool_name, input_hash, output_hash). The
content-hashing primitive lets the trace live in cheaper off-chain storage while keeping verifiability.

The spec for this lands in `docs/agent-passport-spec.md` (pending).

### MCP — protocol vs. "MCP-style" — decision pending

The README currently says "MCP-style tool adapters." We need to commit one way or the other:

- **Real MCP** via Anthropic's protocol (Python: `fastmcp` is the de facto framework). Wins us
  verifiability of the agent's tool surface, ecosystem compatibility, and a cleaner pitch story.
- **"MCP-style" homegrown adapters.** Easier short-term; throws away the verifiability and
  ecosystem wins.

Recommendation: **commit to real MCP**, scope the integration to one demo agent + 2-3 tools (market
data, news, wallet lookup). The decision memo lands in `docs/mcp-decision.md` (pending).

### Custody and settlement

User funds must NEVER pass through platform custody. The pattern: user prepays an Arc-native escrow
contract scoped to a specific job; the contract releases USDC to the developer's address upon job
completion and to a platform fee address simultaneously. If the job fails or is disputed (v2), the
escrow returns funds to the user.

For the demo, the minimum smart-contract surface is:

- One escrow contract that accepts USDC deposits per `job_id`
- A settlement function callable by the platform's signer after job completion
- A platform fee parameter (e.g., 5%)

Chuan owns this end-to-end. We don't add features (slashing, time-locks, dispute resolution) to the
contract during week 1 — those are v2.

## Maestro/Worker discipline (lightweight version)

Hosted Claude is great at architecture, planning, and hard debugging. Local code completion
(Copilot, Cursor, etc.) is great at bulk implementation. A few rules to make this work without
overhead:

- **Use Claude for the architecture decisions.** When the choice is between two real options
  (real-MCP vs. MCP-style; one schema vs. another), ask Claude for the tradeoff and then make the
  call as a team. Don't ask Claude to make the call.
- **Use Claude to draft specs, then implement against them.** A 1-page spec catches more bugs than
  the implementation does. The spec lives in `docs/`.
- **For PRs and bug fixes, prefer local tooling.** Save Claude budget for the next architecture call.
- **Spec drift is real.** If the implementation diverges from the spec, update the spec or revert
  the code. Specs are living docs.

## When to ask before acting (Claude Code session)

- Pushing to `hackathon.navontech.dev` (shared infra)
- Adding new top-level dependencies (state which package, why, and the license)
- Touching `docker-compose*.yml`, `Jenkinsfile`, or Nginx config without team alignment
- Any smart contract change (needs Chuan's review)
- Editing `.env.example` (signals an env contract change for everyone)
- Anything that touches the `agent_passport` / `reasoning_trace` data flow once it lands

## When NOT to ask

- Inside your own feature branch, editing your own files
- Writing tests
- Adding docstrings, type hints, or formatting fixes
- Updating `docs/` to keep specs in sync with shipped code
- Running `pytest`, `ruff`, `prettier --write`, `docker compose up --build` locally

## Known risks and what we've decided about them

- **Reputation gaming.** Mitigated by passport-as-verifiable-history. We're explicit that v1
  reputation = "what happened," not "predictive performance."
- **Custody.** Mitigated by on-chain escrow per job. Platform never holds user funds.
- **Cold start.** Acknowledged for v1; demo agents are curated, not crowdsourced. v2 problem.
- **Skill gap on Solidity.** Mitigated by Chuan; bus factor of 1 on contracts is the residual risk.
  Mitigation: keep the contract small enough that any team member can read it.
- **Coordination across timezones.** Mitigated by a single daily sync (13:00 UTC) and async-first
  defaults outside that window. Marten is proposed schedule owner.
- **"MCP-style" hedging.** Decision pending; default toward real MCP per recommendation above.
- **Mature competitive landscape.** As of Day 2 research, the category is more crowded than the
  Day-1 hypothesis assumed. Direct comps include
  [Swarms](https://swarms.world/) (shipped marketplace + payments), Circle Agent Stack (launched
  May 11, 2026 — the same week as this hackathon), [Olas Pearl](https://olas.network/) with
  [x402](https://www.x402.org/) integration, and [Theoriq](https://www.theoriq.ai/) for
  verifiable agent attestations in DeFi. See `competitor-landscape.md` for the full read. **Pitch
  positioning must acknowledge these — "no competition" is factually wrong.**

## What this file deliberately does not cover

- Pitch deck content (lives in a separate doc once we write it)
- Competitor positioning (see `docs/competitor-landscape.md`)
- Demo script and judging Q&A prep (Week 2)
- Post-hackathon roadmap (out of scope — this is a hackathon repo)

---

_When the team disagrees with anything in this file, the right move is to discuss in Discord,
agree, and update the file — don't let the file silently drift from team consensus. Date your
changes if they substantively change a decision._
