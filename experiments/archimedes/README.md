# Archimedes

> **Peer-reviewed AI portfolios, settled on Arc.**
>
> *The lever is academic research. The fulcrum is autonomous AI. The world is your portfolio.*

[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg)](LICENSE)
[![Hackathon: Agora](https://img.shields.io/badge/hackathon-Agora%20Agents-violet.svg)](https://luma.com/7i50p2r9)
[![Settled on: Arc](https://img.shields.io/badge/settled%20on-Arc-2A4DD1.svg)](https://www.arc.network/)

## What is Archimedes?

Archimedes is an autonomous portfolio agent that turns peer-reviewed quant finance research
into investable, backtested strategies. Users connect a wallet, pick a risk profile, and the
agent constructs a personalized portfolio of RWA tokens and yield instruments on Arc —
settled in USDC. Every decision the agent makes is hashed and anchored on-chain, so
reputation is **verifiable history, not predicted performance**.

Built for the [**Agora Agents Hackathon**](https://luma.com/7i50p2r9) — Canteen × Circle ×
Arc, May 11–25, 2026.

**Status:** MVP in development. See [`docs/`](docs/) for design + planning artifacts.

## Why Archimedes?

Today's portfolio products force a tradeoff:

| Category                      | Examples                                  | What's missing                                            |
| ----------------------------- | ----------------------------------------- | --------------------------------------------------------- |
| TradFi robo-advisors          | Wealthfront, Betterment                   | Rule-based, opaque, no on-chain settlement                |
| DeFi yield aggregators        | Yearn, Yield Seeker                       | Chase current yields, no academic rigor, stablecoin-only  |
| AI-flavored crypto agents     | Virtuals, SingularityDAO, Theoriq         | Token-mediated speculation; reasoning is opaque           |

**Nobody is grounding portfolio decisions in peer-reviewed quant research, with verifiable
on-chain reasoning, settled in pure USDC.** That's the gap.

## Quick Links

| Topic                                          | Document                                                                   |
| ---------------------------------------------- | -------------------------------------------------------------------------- |
| 🧭 Project context for Claude Code sessions     | [`CLAUDE.md`](CLAUDE.md)                                                   |
| 🏗️ System architecture (Chuan)                  | [`docs/design.md`](docs/design.md)                                         |
| 🎯 MVP scope decisions                          | [`docs/mvp-scope-memo.md`](docs/mvp-scope-memo.md)                         |
| 🚫 Anti-features                                | [`docs/anti-features.md`](docs/anti-features.md)                           |
| 🧱 Architectural principles                     | [`docs/architectural-principles.md`](docs/architectural-principles.md)     |
| 📜 Strategy passport spec                       | [`docs/specs/strategy-passport-spec.md`](docs/specs/strategy-passport-spec.md) |
| ⚖️ Backtrader vs vectorbt decision              | [`docs/specs/backtrader-vs-vectorbt-decision-memo.md`](docs/specs/backtrader-vs-vectorbt-decision-memo.md) |
| 🎓 Q-fin paper corpus seed                      | [`docs/qfin-paper-corpus-seed.md`](docs/qfin-paper-corpus-seed.md)         |
| 🏛️ Pitch deck + demo script                     | [`docs/demo-script-pitch-deck-outline.md`](docs/demo-script-pitch-deck-outline.md) |
| 🎨 Claude Design prompts                        | [`docs/claude-design-prompts.md`](docs/claude-design-prompts.md)           |
| 🔭 RFB alignment                                | [`docs/rfb-alignment.md`](docs/rfb-alignment.md)                           |
| 🏟️ Competitive landscape                        | [`docs/competitor-landscape.md`](docs/competitor-landscape.md)             |

## Repository Structure

```
archimedes/
├── CLAUDE.md                        # Project context for Claude Code sessions
├── README.md                        # This file
├── LICENSE                          # Unlicense (public domain dedication)
├── environment.yml                  # Conda env spec for the Python backend
├── docs/                            # Design + planning + specs
│   ├── design.md                    # Full architecture (Chuan)
│   ├── architectural-principles.md
│   ├── competitor-landscape.md
│   ├── mvp-scope-memo.md
│   ├── rfb-alignment.md
│   ├── anti-features.md
│   ├── qfin-paper-corpus-seed.md
│   ├── demo-script-pitch-deck-outline.md
│   ├── claude-design-prompts.md
│   └── specs/
│       ├── strategy-passport-spec.md
│       └── backtrader-vs-vectorbt-decision-memo.md
├── backend/                         # FastAPI + strategy engine (TBD)
├── frontend/                        # Next.js (TBD)
├── contracts/                       # Solidity contracts for Arc (TBD)
└── tests/                           # Test suite (TBD)
```

## Tech Stack

| Layer             | Technology                                                                                |
| ----------------- | ----------------------------------------------------------------------------------------- |
| Backend           | Python 3.12, FastAPI, Uvicorn, SQLAlchemy                                                 |
| Frontend          | Next.js + TailwindCSS                                                                     |
| Database          | PostgreSQL 16 + Redis                                                                     |
| LLM               | Claude API ([anthropic](https://github.com/anthropics/anthropic-sdk-python))              |
| Backtesting       | [backtrader](https://github.com/mementum/backtrader) (v1 decision — see specs)            |
| Smart contracts   | Solidity targeting Arc (EVM-compatible) + [Foundry](https://book.getfoundry.sh/)          |
| On-chain          | [Circle SDK](https://www.circle.com/) + [web3.py](https://github.com/ethereum/web3.py)    |
| Hackathon CLI     | [arc-canteen](https://github.com/the-canteen-dev/ARC-cli) (traction tracking)             |
| Deployment        | Docker + Fly.io / Railway                                                                 |

Full architecture in [`docs/design.md`](docs/design.md).

---

## Setup

Works on **macOS, Linux, and Windows**. Below is a single setup path that everyone on the
team follows.

### Prerequisites

| Tool                                                                             | Purpose                                            |
| -------------------------------------------------------------------------------- | -------------------------------------------------- |
| [Git](https://git-scm.com/)                                                       | Source control                                     |
| [mambaforge / miniconda](https://github.com/conda-forge/miniforge)                | Python environments                                |
| [Node.js 20+](https://nodejs.org/) (via [nvm](https://github.com/nvm-sh/nvm))     | Frontend toolchain                                 |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/)                 | Local PostgreSQL + Redis                           |
| [Foundry](https://book.getfoundry.sh/getting-started/installation)                | Smart contract compilation + testing               |

### 1. Clone the repository

```bash
git clone git@github.com:hackagora/archimedes-arcadia.git archimedes
cd archimedes
```

### 2. Create the Python environment

The repo ships an [`environment.yml`](environment.yml) that defines all Python deps
(FastAPI, SQLAlchemy, backtrader, pandas, anthropic, web3, etc.).

```bash
conda env create -f environment.yml
conda activate archimedes
```

If you prefer mamba (faster):

```bash
mamba env create -f environment.yml
mamba activate archimedes
```

Verify:

```bash
python --version    # → Python 3.12.x
uv --version        # → uv 0.x
which pytest        # → /.../envs/archimedes/bin/pytest
```

### 3. Install the arc-canteen CLI (every team member, individually)

[arc-canteen](https://github.com/the-canteen-dev/ARC-cli) is Canteen's hackathon
traction-reporting tool. Each team member installs it personally — your traction updates
attach to your individual profile and count toward judging metrics.

```bash
uv tool install git+https://github.com/the-canteen-dev/ARC-cli
arc-canteen login        # GitHub device flow
arc-canteen --help       # explore commands
```

After login, the CLI writes credentials to `~/.arc-canteen/env` containing an RPC URL with
an embedded server token. **The token is a secret.** See
[Security notes](#security-notes) before pasting it anywhere.

To get the RPC available in every new shell:

```bash
echo '[ -f ~/.arc-canteen/env ] && . ~/.arc-canteen/env' >> ~/.bashrc
# Or for zsh:
echo '[ -f ~/.arc-canteen/env ] && . ~/.arc-canteen/env' >> ~/.zshrc
```

Then `$RPC` is set automatically in new shells.

### 4. Frontend setup

```bash
cd frontend
npm install     # or pnpm install
npm run dev     # → http://localhost:3000
```

(The `frontend/` directory will land as Daniel's PR.)

### 5. Database (Docker Compose)

```bash
docker compose up -d postgres redis
```

(The `docker-compose.yml` will land alongside the backend skeleton.)

### 6. Smart contracts (Foundry)

```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

Verify against Arc testnet using your arc-canteen RPC:

```bash
source ~/.arc-canteen/env       # ensures $RPC is set
cast block-number --rpc-url $RPC
cast chain-id --rpc-url $RPC
```

---

## Platform-specific notes

### macOS (Dan, Chuan)

mambaforge + everything else works natively. No special setup. If on Apple Silicon, the
osx-arm64 conda channels are well-supported; psycopg2-binary, web3.py, and backtrader all
have arm64 wheels.

### Linux (Daniel, Önder)

Native experience. Identical to macOS for our purposes. Standard apt/dnf installs for
docker + node if not already present.

### Windows (Marten)

**Two options. We recommend WSL2.**

**Option A — WSL2 (recommended):** Get a Linux experience inside Windows. Foundry, conda,
Docker, and everything else "just works."

```powershell
# In PowerShell as Administrator
wsl --install
# Restart, open Ubuntu, then follow the Linux instructions above
```

WSL2 docs: [microsoft.com/wsl](https://learn.microsoft.com/en-us/windows/wsl/install).

**Option B — Native Windows:** Conda works on Windows; some pain points:

- **Foundry on native Windows** is unsupported officially. Use Git Bash + the standalone
  binaries from foundry's releases, or use WSL2 just for foundry.
- **psycopg2-binary** wheels exist for Windows but occasionally need a Visual Studio
  Build Tools install. If `pip install psycopg2-binary` fails, install the
  [Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) and retry.
- **Docker Desktop on Windows** uses WSL2 under the hood anyway, so you already need WSL2
  even on Option B.

Practical take: **Marten, set up WSL2.** It removes every Windows-specific pain point and
matches Dan + Daniel + Önder's Linux/macOS workflow exactly.

---

## Development workflow

See [`CLAUDE.md`](CLAUDE.md) for full conventions. Headline points:

- **Branch model:** `feat/<name>` for features; `<discord-handle>/<name>` for personal
  staging. PRs to `develop`; promote to `main` once stable.
- **One approving review** for non-contract changes; two for contract changes.
- **Commit style:** imperative mood with optional scope tags (`[strategy]`, `[backend]`,
  `[contracts]`, etc.).
- **Daily sync:** 13:00 UTC = 8am Chicago / 10am São Paulo / 14:00 London / 15:00 Bremen /
  16:00 Ankara.

### Running tests

```bash
pytest                       # backend tests
cd frontend && npm test      # frontend tests
forge test                   # contract tests (once contracts/ lands)
```

### Lint + format

```bash
ruff format src/             # auto-format
ruff check src/ --fix        # auto-fix lint
```

---

## Security notes

A short list of hygiene items worth surfacing explicitly.

### arc-canteen credentials are secrets

The `arc-canteen login` flow writes credentials to `~/.arc-canteen/env`. The file is
permissioned `0600` (owner read/write only) by the CLI — verify yours is too with
`ls -la ~/.arc-canteen/env`.

The file contains your **personal RPC endpoint URL** with an **embedded server token**
(format: `swrm_<64-hex>`). **Treat the token like an API key:**

- 🚫 Do NOT commit `~/.arc-canteen/env` (not in this repo and not in any dotfiles repo).
- 🚫 Do NOT paste the full RPC URL into Discord channels, screenshots, pitch decks, GitHub
  issues, or AI chats. Use `$RPC` in commands so the literal token doesn't appear in
  shell history.
- 🚫 Do NOT share with teammates — each team member has their own.
- ✅ If you suspect leakage, run `arc-canteen rotate-rpc-key` to mint a fresh token and
  invalidate the old one. Cheap; takes seconds.

### Wallet hygiene

- Use a **dedicated dev wallet** for all hackathon testing — never connect a wallet that
  holds real assets.
- Private keys go in `.env` files (gitignored). Never commit secrets.
- The platform's signer key (for the rebalance contract calls) lives in environment
  variables, not in the repo.

### Dependency hygiene

- The Python deps in `environment.yml` are loosely-pinned for v1. We'll tighten when we
  move to a `pyproject.toml`-driven workflow.
- The `arc-canteen` CLI installs from the official
  [the-canteen-dev/ARC-cli](https://github.com/the-canteen-dev/ARC-cli) repo. Verify the
  URL when running `uv tool install` — typosquatting is a real attack pattern.
- All transitive deps of the arc-canteen CLI are standard CLI-tooling packages (typer,
  click, httpx, rich, pyyaml). The `annotated-doc` dep is from
  [fastapi/annotated-doc](https://github.com/fastapi/annotated-doc) — legitimate.

### GitHub OAuth scopes

When you ran `arc-canteen login`, the GitHub device flow authorized the Canteen app on
your account. Verify the granted scopes at
[github.com/settings/applications](https://github.com/settings/applications). For a
hackathon-traction tool, expected scopes are minimal (`read:user`, `user:email`). If
`repo` or `admin:*` scopes were granted, revoke and re-authenticate.

---

## Roadmap

Two-week hackathon roadmap in [`docs/design.md` § 8](docs/design.md). Post-hackathon
direction in [`docs/demo-script-pitch-deck-outline.md`](docs/demo-script-pitch-deck-outline.md)
slide 8.

## Team

5 builders across 5 timezones, with deep coverage on every load-bearing skill — see the
team table in [`CLAUDE.md`](CLAUDE.md).

## Contributing

Fork, branch, PR to `develop`. See [`CLAUDE.md`](CLAUDE.md) for engineering conventions.

## License

[Unlicense](LICENSE) — full public-domain dedication. Use, modify, distribute freely. No
warranty.

---

> *In classical Athens, the agora was the heart of the city — the original
> information-processing machine. AI agents are the new citizens.*
>
> — [Agora Agents Hackathon](https://luma.com/7i50p2r9)
