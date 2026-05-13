# Archimedes — Claude Code Context

> **Status:** Draft proposal, written 2026-05-12 (Day 2). Intent: drop at the root of the
> `archimedes` repo and read at the start of every Claude Code session. Several sections
> (license confirmation, demo wow-moment, weekly milestones) reference Chuan's
> [`docs/design.md`](docs/design.md) — read both together; this file is project context,
> design.md is the architecture spec.

## Project

**Archimedes** — a fund-of-funds portfolio agent that turns published quant finance research
into investable, backtested strategies, then constructs personalized portfolios of RWA tokens
and yield instruments on Arc with USDC settlement.

> *"Give me a lever long enough and I shall move the world."* The lever here is academic
> research; the fulcrum is autonomous AI; the world is your portfolio.

Built for the [**Agora Agents Hackathon**](https://luma.com/7i50p2r9) — Canteen × Circle × Arc,
May 11–25, 2026.

- Repository: [`github.com/hackagora/archimedes-arcadia`](https://github.com/hackagora/archimedes-arcadia)
- Discord: **Archimedes Arcadia** server
- Primary branch: `main`; active design work on `design`; integration on `develop`
- License: [Unlicense](https://unlicense.org) — full public-domain dedication

## North Star

A user with idle USDC who wants thoughtful portfolio management — but is tired of black-box
robo-advisors, opaque AI funds, and "trust me bro" influencer copy-trading — connects a
wallet, picks a risk profile, and gets a portfolio constructed from strategies that come
with a **paper-grounded reasoning trace anchored on-chain**. Every position the agent takes,
every rebalance it executes, every regime shift it responds to, is hashed and verifiable.

The Agora narrative frames this:

> *Where AI agents make markets. The agora was where Athens did its thinking out loud.
> Markets are still doing the same job today; they are the social technology by which a
> civilization aggregates knowledge and decides what things are worth. AI agents are the new
> citizens.*

Archimedes is one such citizen — but one whose reasoning trail is open to inspection, whose
claimed alpha is bound to academic research rather than vibes, and whose settlement happens
at sub-second finality on Arc with USDC. The mathematician's name is fitting: he was the
original empiricist working from first principles. We work from peer-reviewed first
principles.

## Team (5 members; ~20-year age span; coverage on every load-bearing skill)

Roughly balanced bios. Ages are author estimates pending team confirmation. Discord handles
in parentheses; the human handles are what shows up in the channel.

| Name                       | Age (est.) | Discord            | Location  | TZ (May)| Role                                                                                                                |
| -------------------------- | ---------- | ------------------ | --------- | --------| ------------------------------------------------------------------------------------------------------------------- |
| **Dan Browne**             | 37         | dbrowneup          | Chicago   | UTC-5   | Strategy engine (Q-fin paper corpus, strategy library curation), pitch architecture. Senior Scientist @ LanzaTech, PhD biochemistry. Day job — evenings/weekends. |
| **Marten Windler**         | ~31        | Marten             | Bremen    | UTC+2   | Off-chain → on-chain integration via Arc CLI; pairs with Chuan. Systems Engineering @ U. Bremen, ML-uncertainty B.Sc. thesis. ROS + Python/C++/Rust. Coordinator lean. |
| **Daniel Reis dos Santos** | early 20s  | The go guy / Daniel [vibe] | Brazil    | UTC-3   | Frontend ownership (Next.js + TailwindCSS). Backend engineer day-side. Go / Java / TypeScript, distributed systems, AWS, Terraform. Healthcare-ERP day role.  |
| **Chuan Bai**              | ~early 40s | moonshot           | London    | UTC+1   | Architecture + on-chain (smart contracts on Arc, Circle SDK integration). CTO @ [Gyld Finance](https://www.gyld.fi/); built CoinShares' next-gen trading platform; RWA tokenization expertise. PhD HPC. |
| **Önder Akkaya**           | ~21        | Önder              | Ankara    | UTC+3   | Portfolio math (Kelly Criterion / +EV, backtest evaluation, risk pricing). Statistics @ Hacettepe; [ASA Statistical Insight World Champion](https://www.linkedin.com/in/onder-akkaya/); President of [TİD-Genç](https://www.tid.org.tr/); trainee actuary. |

Two team members (Dan, Daniel R) have demanding day roles and commit evenings/weekends.
Chuan runs a real startup but treats the hackathon as serious focus. Marten and Önder are
students with flexible time.

**Daily sync window:** 13:00 UTC = 8am Chicago / 10am São Paulo / 14:00 London / 15:00
Bremen / 16:00 Ankara. Works across the whole team without anyone in unsocial hours.

**Schedule/flow owner:** Marten (showing coordinator instincts since Day 1). Standups in
`#standups` in Discord.

### Non-team contacts

- **Anuhya** (Discord: `moonshot` in the Canteen server, *NOT* the Chuan-moonshot in
  Archimedes Arcadia) is a **Canteen admin** running the hackathon. She is a stakeholder /
  judge-adjacent, not a teammate.

### Role allocation by load-bearing component

| Component                                          | Owner            | Backup                |
| -------------------------------------------------- | ---------------- | --------------------- |
| Strategy engine + Q-fin paper corpus curation       | Dan              | Önder                 |
| Backtesting / strategy-passport math + risk pricing | Önder            | Dan                   |
| Backend (FastAPI, strategy DB, portfolio agent)     | (open — TBD)     | Marten                |
| Frontend (Next.js, portfolio dashboard, traces)     | Daniel           | Dan                   |
| Smart contracts (Arc, Circle SDK)                   | Chuan            | Marten                |
| Off-chain ↔ on-chain orchestration                  | Marten           | Chuan                 |
| Architecture + design decisions                     | Chuan (lead)     | full team             |
| Pitch deck + demo script + judging strategy         | Dan              | Marten                |

Backend ownership is the one un-filled slot since Shimon left. The team should decide by
end of Day 3 whether to spread it across the four engineers or hire externally.

## Setup

Read [`README.md`](README.md) for the full setup walkthrough — Python conda env via
[`environment.yml`](environment.yml), Node.js frontend, Foundry for contracts, the
[arc-canteen CLI](https://github.com/the-canteen-dev/ARC-cli) for traction tracking.
Platform-specific notes for macOS / Linux / Windows (WSL2 recommended for Marten).

## Tech Stack

Refer to [`docs/design.md` § 6](docs/design.md) for the full table. Headline choices:

- **Backend:** Python 3.12 / FastAPI / Uvicorn
- **Frontend:** Next.js + TailwindCSS (Daniel's call as frontend owner)
- **DB:** PostgreSQL + Redis (Postgres for strategies + backtests; Redis for live regime
  state)
- **LLM:** Claude API for strategy extraction, reasoning trace generation, user-facing
  explanations
- **Backtesting:** Open question — vectorbt (Chuan's design.md proposal) vs.
  [backtrader](https://github.com/mementum/backtrader) (Dan's suggestion). See
  [`docs/specs/backtrader-vs-vectorbt-decision-memo.md`](docs/specs/backtrader-vs-vectorbt-decision-memo.md)
  for the framing.
- **Smart contracts:** Solidity targeting Arc (EVM-compatible)
- **On-chain integration:** Circle SDK — Wallets, USYC, Gateway, CCTP, Paymaster, App Kit
- **Deployment:** Docker + Fly.io / Railway

## Scope — the headline commitments

Refer to [`docs/mvp-scope-memo.md`](docs/mvp-scope-memo.md) for the full argument. Locked
decisions:

- **Primary RFB:** [RFB 04 — Adaptive Portfolio Manager](https://luma.com/7i50p2r9).
  Adjacent: RFB 02 (Kelly/+EV math primitive); RFB 06 (strategy leaderboard).
- **Both on-chain stories:** vault contracts for RWA-token allocation **and** reasoning-
  trace registry for verifiable provenance. Ambitious; achievable with five committed
  people.
- **Curated v1 strategy library:** ship 5–10 hand-curated quant strategies; arxiv ingest
  pipeline runs as a demo feature on 2–3 papers to show the concept.
- **Demo vertical:** portfolio construction + autonomous rebalancing on Arc, NOT trading-
  agent-as-product. Per [`docs/architectural-principles.md`](docs/architectural-principles.md),
  the wedge is verifiable history + paper-grounded provenance, not predicted performance.
- **Out of scope:** see [`docs/anti-features.md`](docs/anti-features.md).

## Engineering conventions

### Branch model (5-person hackathon team, async-first)

- `main` is protected. Every change goes through a PR.
- `develop` is the integration branch — merge feature branches here first; promote to
  `main` once stable.
- Feature branches: `feat/<short-name>`, e.g. `feat/strategy-passport`,
  `feat/regime-detection`.
- Per-owner branches: `<discord-handle>/<short-name>`, e.g. `moonshot/contracts-v0`,
  `marten/arc-cli-spike`. Personal staging.
- Smart-contract branches: `contract/<short-name>` — these get **two reviews** (Chuan +
  one generalist) before merge.
- **No force-push to `main` or `develop`. Ever.** Force-push to your own branch before
  opening a PR is fine.

### PR reviews

For a 5-person hackathon team operating async across 5 timezones, **one approving review**
is enough for non-contract changes. Contract changes get two. Reviewers should respond
within ~12 hours during the hackathon so the contributor isn't blocked overnight.

### Commit style

Imperative mood ("Add strategy passport schema" not "Added strategy passport schema").
Scope tags optional but encouraged: `[strategy]`, `[backtest]`, `[contracts]`, `[frontend]`,
`[infra]`, `[docs]`. Atomic commits — one logical change per commit; don't bundle.

### Smoke-test before deploy

Don't push to shared infrastructure without smoke-testing locally first. If the deploy is a
smart-contract change, run it against an Arc testnet first. The cost of a broken demo
environment is high; the cost of a 5-minute smoke test is low.

### Don't connect important wallets

Standard hackathon hygiene: use a fresh dev wallet for testing, never one with real assets.
Don't paste private keys anywhere in this repo. Use `.env.example` as a template;
`.env` is gitignored.

### Maestro/Worker discipline (lite)

Hosted Claude (Claude Code, claude.ai) is great at architecture, planning, and hard
debugging. Local code completion (Copilot, Cursor) is great at bulk implementation. A few
rules:

- **Use Claude for architecture decisions.** When the choice is between two real options,
  ask Claude for the tradeoff, then make the call as a team. Don't ask Claude to make the
  call.
- **Use Claude to draft specs, then implement against them.** A 1-page spec catches more
  bugs than the implementation does.
- **For PRs and bug fixes, prefer local tooling.** Save Claude budget for the next
  architecture call.
- **Spec drift is real.** If implementation diverges from the spec, update the spec or
  revert the code. Specs are living docs.
- **Multiple team members are using Claude.** Chuan (20× Max), Dan (5× Max), and others
  are running concurrent Claude sessions. **Source-of-truth artifacts in `docs/` are how
  we keep parallel sessions aligned** — every session reads from the same docs.

## When to ask before acting (Claude Code session in this repo)

- Pushing to shared infrastructure
- Adding new top-level dependencies (state which package, why, and the license)
- Touching `docker-compose*.yml`, deployment configs, or CI/CD wiring without team alignment
- Any smart contract change (needs Chuan's review)
- Editing `.env.example` (signals an env contract change for everyone)
- Editing [`environment.yml`](environment.yml) (every team member rebuilds their env on a change)
- Anything that touches the strategy-passport / reasoning-trace data flow once it lands
- Anything that touches the on-chain vault contract once it lands
- Anything that touches `~/.arc-canteen/` files (those are individual team-member credentials —
  see [`README.md` "Security notes"](README.md#security-notes))

## When NOT to ask

- Inside your own feature branch, editing your own files
- Writing tests
- Adding docstrings, type hints, or formatting fixes
- Updating `docs/` to keep specs in sync with shipped code
- Running `pytest`, `ruff`, `prettier --write`, `docker compose up --build` locally

## Architectural primitives we want to get right

These three architectural commitments are load-bearing for the pitch's defensibility. Detail
in the linked specs; principle here.

### 1. The strategy passport

Every strategy in the library carries a verifiable record: which paper claims back it, what
methodology the LLM extracted, what backtest results validated it, what reasoning trace the
agent left when selecting it for a portfolio. Detail in
[`docs/specs/strategy-passport-spec.md`](docs/specs/strategy-passport-spec.md) — builds on
Chuan's `ReasoningTrace` shape in [`docs/design.md` § 4.4](docs/design.md).

### 2. On-chain provenance anchoring

Reasoning traces, strategy registrations, and rebalance decisions all get hashed and
anchored on Arc via a `ReasoningTraceRegistry` contract (Chuan's design). The hash is the
integrity primitive; off-chain storage holds the full trace; anyone can verify a trace
matches the on-chain anchor.

### 3. Non-custodial vault architecture

User funds NEVER pass through platform custody. The pattern: user deposits USDC to an
Arc-native `ArchimedesVault` contract; the agent has rebalance authority but not withdraw-
to-platform authority. See Chuan's smart contract architecture in
[`docs/design.md` § 5.2](docs/design.md).

## Known risks

Refer to [`docs/design.md` § 10](docs/design.md) for the technical risk matrix. Adding
team / coordination risks:

- **Backend ownership unfilled.** Shimon left; backend doesn't have a single owner. Decide
  by end of Day 3.
- **Chuan as smart-contract bus factor 1.** Mitigated by keeping contracts small + pair-
  review. See [`docs/architectural-principles.md`](docs/architectural-principles.md) for the
  general pattern.
- **5-person team across 5 timezones with 3 day-job constraints.** Mitigated by Marten as
  schedule owner + daily sync + async-first defaults.
- **Multiple parallel Claude sessions risk artifact drift.** Mitigated by treating `docs/`
  as single source of truth.
- **Q-fin paper corpus needs Dan's curation.** Dan is evenings/weekends only; needs to
  block weekend time to seed the corpus per
  [`docs/qfin-paper-corpus-seed.md`](docs/qfin-paper-corpus-seed.md).

## What this file deliberately does not cover

- The full architecture — see [`docs/design.md`](docs/design.md) (Chuan)
- Pitch deck content — see [`docs/demo-script-pitch-deck-outline.md`](docs/demo-script-pitch-deck-outline.md)
- Competitive landscape — see [`docs/competitor-landscape.md`](docs/competitor-landscape.md)
- Post-hackathon roadmap — out of scope for now

---

_When the team disagrees with anything in this file, the right move is to discuss in
Discord, agree, and update the file — don't let it silently drift. Date your changes if
they substantively change a decision._
