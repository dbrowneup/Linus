# Archimedes orient — 2026-05-22

> Audit-only orientation for Linus's reveal-time README cross-reference work. Sources:
> `experiments/archimedes/README.md` (the canonical project README), `experiments/archimedes/CLAUDE.md`
> (project context), `docs/specs/linus-archimedes-bridge.md` (the integration contract), and existing
> Linus root README/ROADMAP/DECISIONS mentions. The live `repos/archimedes/` tree was sandbox-blocked,
> so this orient draws on the in-tree priors + the v1 bridge spec.

## What Archimedes is

Archimedes is an autonomous portfolio agent that turns peer-reviewed quantitative-finance research into
investable, backtested strategies. A user connects a wallet, picks a risk profile, and the agent
constructs a personalized portfolio of real-world-asset (RWA) tokens and yield instruments on the Arc
network, settled in USDC. The novel claim is verifiability: every decision the agent makes — which
strategy it selects, what evidence backs the selection, every rebalance it executes — is hashed and
anchored on-chain via a `ReasoningTraceRegistry` contract, so reputation becomes verifiable history
rather than predicted performance. The pitch deliberately positions against three nearby categories:
TradFi robo-advisors (opaque, off-chain), DeFi yield aggregators (no academic rigor), and AI-flavored
crypto agents (token-mediated speculation with no auditable reasoning).

Architecturally, Archimedes is a Python 3.12 / FastAPI backend, a Next.js + TailwindCSS frontend, a
PostgreSQL + Redis store, Solidity contracts on Arc, and the Circle SDK for on-chain integration. The
three load-bearing primitives are (1) the **strategy passport** — every strategy carries a record
binding it to a source paper, an extracted methodology, backtest results, and a reasoning trace; (2)
**on-chain provenance anchoring** via hashes anchored on Arc; and (3) **non-custodial vault
architecture** so user funds never pass through platform custody.

Archimedes was built for the Agora Agents Hackathon (Canteen × Circle × Arc, May 11–25, 2026). It is
the work of a five-person team across five timezones: Dan Browne (Chicago, strategy engine + pitch),
Marten Windler (Bremen, off-chain ↔ on-chain), Daniel Reis dos Santos (Brazil, frontend), Chuan Bai
(London, architecture + smart contracts; CTO at Gyld Finance), and Önder Akkaya (Ankara, portfolio
math). License is the Unlicense (full public-domain dedication).

## Strategy engine role

The **strategy engine** is the subsystem responsible for the paper-to-strategy pipeline: ingesting
q-fin papers (curated v1 library of 5–10 strategies, with an arXiv-ingest pipeline demoed on 2–3
papers), extracting strategy methodology, generating backtested candidate strategies, and producing
the **strategy passport** that ties each strategy to its source paper, methodology, backtest results,
and reasoning trace. It is the upstream of every Archimedes-verified claim — without it, the
portfolio agent has nothing rigorous to allocate against.

Dan owns the strategy engine (Önder backs it on portfolio-math / risk-pricing). It sits at the front
of the data flow: paper corpus → strategy library → portfolio agent → vault contract. Per the bridge
spec, this is where Linus contributes most directly: Archimedes lifts Linus's `papers.ingest_arxiv`
tool, the `KnowledgeRetriever` RAG-gateway contract, and the `spawn_agents` parallel-agent primitive
as the substrate that makes "Archimedes Verified" a discriminating label rather than a rubber stamp.

## Public release posture

Already public: the GitHub org `hackagora` with the canonical repo at
`github.com/hackagora/archimedes-arcadia`. The Agora Hackathon page itself
(`luma.com/7i50p2r9`) is public; Archimedes appears there as a participating project. Settlement
chain is Arc (`arc.network`).

Newly revealed at the 2026-05-25 hackathon: the working MVP — strategy engine, portfolio agent,
on-chain reasoning-trace registry on Arc, and the demo of paper → strategy → portfolio → settlement.
This is also when Linus and KnowledgeBase make their coordinated public reveal. The Linus root
README already references Archimedes by canonical name + URL (`hackagora/archimedes-arcadia`); the
"link TBD" line in §Status is stale — the repo URL is known.

Canonical naming convention: project name "Archimedes"; repo name `archimedes-arcadia`; team Discord
server "Archimedes Arcadia".

## Cross-project messaging suggestions

Three concrete sentences usable in Linus's root README:

1. "Archimedes (`hackagora/archimedes-arcadia`) is the entrepreneurial sibling project debuting
   alongside Linus at the Agora hackathon — a peer-reviewed-research-grounded portfolio agent on
   Arc, settled in USDC. Linus's research-intelligence stack (paper ingest, RAG gateway, parallel
   agent spawner) is what powers Archimedes's strategy engine; the integration contract lives in
   [`docs/specs/linus-archimedes-bridge.md`](docs/specs/linus-archimedes-bridge.md)."

2. "Where Linus is the general personal research substrate, Archimedes is what that substrate looks
   like specialized to one domain (quantitative finance), made externally verifiable
   (on-chain reasoning traces), and shipped as a product."

3. The existing reveal-context blockquote in README.md §Status is already on-message; only the
   "link TBD" parenthetical needs replacing with the canonical URL.

## What I couldn't determine

- The live `repos/archimedes/` working tree was sandbox-blocked from this agent; the orient draws on
  `experiments/archimedes/` priors (last updated 2026-05-12 to 2026-05-14) plus the 2026-05-19
  bridge spec. Items that may have shifted since: backend ownership (open as of 2026-05-12), the
  vectorbt-vs-backtrader v1 backtesting call, and whether the arxiv-ingest pipeline is demo-only or
  load-bearing in the final pitch.
- Whether Archimedes has a public-facing landing page beyond the GitHub repo + the Agora luma page.
- Whether the team wants Linus's README to name Chuan / Önder / Marten / Daniel R. as collaborators
  or to keep the cross-reference repo-level only.
- Whether "Archimedes Verified" is a final brand mark or a working-title.
