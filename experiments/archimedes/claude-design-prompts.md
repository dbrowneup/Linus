# Claude Design — Prompts for Archimedes

> **Audience:** Dan (using Claude Design at [claude.ai/design](https://claude.ai/design))
> **Purpose:** Concrete prompts to paste into Claude Design for slides, UI prototypes,
> and logo variants. Each prompt is self-contained so the design session has the context
> it needs without you re-explaining the project.
> **Status:** v1 prompts. Iterate based on what Claude Design produces.

## Quick notes on using Claude Design

[Claude Design](https://claude.ai/design) is a research preview by Anthropic Labs. From
the landing page, three modes are relevant for Archimedes:

- **Prototype** — wireframe or high-fidelity. Use this for the user-facing UI flow.
- **Slide deck** — directly produces pitch slides.
- **From template / Other** — for custom needs.

A few tips before diving in:

1. **Set up a design system first** if you have brand colors / fonts in mind. There's a
   "Set up design system" CTA on the landing page. Worth 5 minutes up front to maintain
   visual consistency.
2. **Generate iteratively.** Start with the smallest scope (a single slide, a single
   screen) and expand once the style is right. Claude Design is interactive; you can
   refine.
3. **For visual references:** Claude Design can fetch URLs you give it. Screenshots
   from your end are also fine — paste them in the conversation as you would in a normal
   chat. Both work. Use URLs when you want me (this Claude session) to also see the
   reference; use screenshots when it's faster.

## How to use this doc

Each prompt below is **paste-ready**. Read the "Setup notes" first to make sure you're in
the right Claude Design mode (Prototype / Slide deck / Other), then paste the prompt into
the conversation. Edit the placeholder bits in `<angle brackets>` if anything is
inaccurate.

---

## Prompt 1 — Logo set (multiple variants)

**Setup notes:** Use Claude Design's **Other** mode for graphics generation. If a "logo"
template exists, use that. Generate 3–4 variants and pick the strongest.

```
Project: Archimedes — an AI portfolio agent that grounds investment strategies in
peer-reviewed quant finance research, settled on Arc (Circle's stablecoin-native L1)
with USDC.

I need a logo for the project. Generate 4 distinct logo concepts as separate options.
Each should be:
- A standalone mark (icon) + a wordmark (the word "Archimedes")
- Suitable for both light and dark backgrounds
- Clean and professional — this is a financial product, not a consumer app
- Conveys the "rigorous empiricism + AI + on-chain finance" combination

The four concept directions:

CONCEPT A — Archimedean spiral
A stylized Archimedean spiral (the mathematical curve named after him). Clean,
geometric, modern. The spiral can suggest both: the mathematician's discovery, AND
the recursive nature of autonomous agent decision-making. Color palette: a deep blue
or violet for the spiral, with the wordmark in a clean serif (the historical
reference) or modern monospace (the on-chain reference).

CONCEPT B — The lever and fulcrum
Archimedes' famous quote: "Give me a lever long enough and a fulcrum on which to
place it, and I shall move the world." A minimal lever-and-fulcrum mark — could
abstract into a balanced scale or a Greek-letter-like glyph. Subtle but recognizable.
Color palette: gold + dark navy (the "weighty intellectual" feel).

CONCEPT C — Eureka / displacement
The bath / displacement principle — Archimedes' "Eureka!" moment. This could be a
single droplet or a wave-form mark, suggesting both the displacement principle and the
flow of capital. Color palette: blue gradient (water) + warm accent.

CONCEPT D — Mathematical glyph
A stylized mathematical symbol that suggests Archimedes (the historical figure)
without being literal. Could combine: π (he calculated it), an integral symbol, an
infinity symbol, or a stylized lowercase Greek "α" (alpha). Color palette:
monochrome with a single accent color.

For each concept, provide:
- The icon at 256×256
- The wordmark with icon (horizontal layout)
- The wordmark with icon (vertical/stacked layout)
- A favicon-sized version (32×32)

Avoid: AI-generated photorealism, busy details, cliché Greek-temple imagery, anything
that looks like it could be a generic crypto logo.
```

**What to do with the output:**

- Pick the strongest concept (or merge two).
- Confirm with the team in Discord before locking.
- Export in PNG + SVG.
- Use the chosen mark in the Discord server, the GitHub repo (README header), the pitch
  deck, and the frontend.

---

## Prompt 2 — Slide deck (full 9 slides)

**Setup notes:** Use Claude Design's **Slide deck** mode. Make sure the design system is
set (or pass colors inline). The deck structure mirrors
[`demo-script-pitch-deck-outline.md`](demo-script-pitch-deck-outline.md).

```
Project: Archimedes — pitch deck for the Agora Agents Hackathon (Canteen × Circle ×
Arc), submission deadline May 25, 2026. 3-minute pitch + live demo + Q&A.

The deck has 9 slides. Visual style: clean, professional, financial-grade. Think a
crossover between Wealthfront's marketing site and a serious crypto-native product
like Circle's own site or Arc.network. Color palette: dark mode primary
(near-black background, off-white text), with a single brand color accent — use deep
blue (#2A4DD1 or similar) or violet (#7B2CBF). Typography: a clean serif for
headlines (the academic-rigor cue), a modern sans-serif for body. No clip art, no
emojis, no busy decoration.

Use this slide-by-slide content:

SLIDE 1 — Title
Header: Archimedes
Tagline: Peer-reviewed AI portfolios, settled on Arc.
Subtitle: The original empiricist meets autonomous on-chain finance.
Attribution: Agora Agents Hackathon — Canteen × Circle × Arc, May 11–25, 2026

SLIDE 2 — The problem
Title: Today's portfolio products force a tradeoff.
Three columns:
- TradFi robo-advisors (Wealthfront, Betterment): rule-based, opaque,
  no on-chain settlement.
- DeFi yield aggregators (Yearn, Yield Seeker): chase current yields,
  no academic rigor, stablecoin-only.
- AI-flavored crypto agents (Virtuals, SingularityDAO, Theoriq):
  token-mediated speculation, reasoning opaque.
Empty fourth column with a "?" — implying Archimedes goes here.

SLIDE 3 — What we built
Title: Archimedes — Peer-reviewed AI portfolios on Arc
Four bullets with icons:
- Strategies from peer-reviewed quant papers (with paper-claim binding).
- Risk profiles: Conservative / Moderate / Aggressive / Hyper-Risky.
- Autonomous: regime detection, rebalancing, strategy rotation.
- Every decision hashed on Arc — verifiable reasoning trace.
Background: stylized version of the system architecture diagram (strategy engine
→ backtesting → portfolio agent → on-chain).

SLIDE 4 — DEMO
Full-bleed slide: just the word "DEMO" in large type, with a small "archimedes.
hackagora.com" URL underneath. This slide gets minimum 90 seconds of live demo time.

SLIDE 5 — Competitive landscape
Title: We fill the gap.
A two-column "what others do vs. what we do" layout. Reuse the content from the
competitive slide in demo-script-pitch-deck-outline.md (paste in if Claude Design
needs it).
Bottom tagline: "Rule-based, opaque, or token-mediated → AI-driven, paper-
provenanced, USDC-native"

SLIDE 6 — Why we'll score well
Title: How Archimedes maps to the judging criteria
Four columns (one per criterion):
- Agentic Sophistication (30%): regime detection, autonomous rebalancing,
  strategy rotation, on-chain reasoning traces.
- Traction (30%): pre-curated strategies, day-1 portfolios, strategy
  leaderboard, target 50+ users.
- Circle Tool Usage (20%): Wallets, USYC, CCTP, Gateway, Paymaster,
  Contracts — full stack.
- Innovation (20%): paper-grounded provenance, on-chain reasoning traces,
  academic accountability for autonomous trading.
RFB tagline at bottom: "RFB 04 primary. RFB 02 math primitive. RFB 06 adjacent."

SLIDE 7 — Why now
Title: The agent economy is real.
Three big-number callouts:
- $222M — Circle Arc presale at $3B FDV, May 11, 2026 (BlackRock among investors)
- 700K tx/month — Olas Pearl, 30% MoM growth
- $470M aGDP — Virtuals Protocol, 18K+ agents
Sub-tagline: "But nobody is building paper-grounded, verifiably auditable
portfolio agents. That's the gap."

SLIDE 8 — Roadmap
Title: What we ship next.
A horizontal timeline with four milestones:
- Now: Hackathon submission, curated v1 library, autonomous rebalancing on Arc.
- 30 days: Productize the arxiv ingest pipeline.
- 90 days: Strategy marketplace, EURC support, DAO-governed curation.
- 180 days: v2 verticals (prediction markets, perp-aware portfolios).

SLIDE 9 — Team + ask
Title: The team.
5 photos + one-line credentials:
- Dan Browne — PhD biochemistry, LanzaTech.
- Marten Windler — Systems Engineering, U. Bremen.
- Daniel Reis dos Santos — Backend engineer, distributed systems.
- Chuan Bai — CTO @ Gyld Finance; ex-CoinShares trading platform.
- Önder Akkaya — ASA Statistical Insight World Champion; trainee actuary.

Ask: "We're asking for: feedback on the strategy passport as a candidate open
standard; introductions to quant researchers who'd contribute strategies;
partnerships with RWA-token issuers."

End-of-deck tagline: "The lever is academic research. The fulcrum is autonomous AI.
The world is your portfolio."

Generate all 9 slides. Maintain visual consistency throughout — same color palette,
same typography, same density of information.
```

**What to do with the output:**

- Review each slide; iterate on the ones that don't land.
- Export to a deck format (Keynote, PowerPoint, PDF) for the actual pitch.
- Print one as a one-page handout (Slide 1 + Slide 3 + Slide 5 condensed) if Canteen
  allows handouts.

---

## Prompt 3 — High-fidelity UI prototype (onboarding + dashboard)

**Setup notes:** Use Claude Design's **Prototype** mode with **High fidelity** selected.
This is what Daniel uses as a visual reference before writing the React code.

```
Project: Archimedes — frontend prototype.

Tech stack target: Next.js + TailwindCSS. The prototype should be implementable in
that stack — don't generate UI that requires custom canvas/WebGL or anything exotic.

I need three connected screens that walk a user through the core flow:

SCREEN 1 — Landing / Risk Profile Selection
The first screen after wallet connect. Header with logo, wallet address in top-right.
Hero section: short headline ("Peer-reviewed AI portfolios, autonomous on Arc"),
subhead, primary CTA implied.
Below the hero: four cards (Conservative / Moderate / Aggressive / Hyper-Risky).
Each card shows:
- Profile name + a one-line description
- Target volatility band
- Max drawdown
- USYC floor percentage
- A small horizontal stacked bar showing approximate asset-class breakdown
- "Select this profile" button
The cards should look like the user could comfortably skim them and choose. Use
distinct accent colors per profile (Conservative = green, Moderate = blue,
Aggressive = orange, Hyper-Risky = red), but keep them tasteful — no clip art.

SCREEN 2 — Portfolio Preview
After selecting a profile, the user sees the constructed portfolio before depositing.
Layout: top section shows a donut chart of asset weights, with a legend.
Middle section: a list of selected strategies (4–6 cards horizontally scrollable),
each showing:
- Strategy name (with paper citation in small text: "Jegadeesh & Titman 1993")
- Backtest Sharpe (with paper-claimed Sharpe in parentheses for comparison)
- One-line methodology summary
- Weight in the portfolio
- "View paper" link
Bottom section: a "Deposit USDC" CTA, plus a small "Customize" link for users who
want to manually adjust strategy weights.

SCREEN 3 — Portfolio Dashboard (after deposit)
The live state. Layout:
- Top stat row: Total value (USDC), 24h change, 7d change, current regime
  classification (Risk-On / Risk-Off / Transition / Crisis).
- Performance chart: line chart of portfolio value over time, with benchmark line
  (BTC or S&P 500 for comparison).
- Current positions table: token, weight, current value, % from target, last
  rebalance.
- "Decisions" tab (this is the differentiator) — a chronological feed of agent
  decisions:
  - Each decision has: timestamp, decision type, trigger, one-sentence summary,
    "View reasoning trace" link.
  - The first item in the feed has a "Verify trace hash" button that, when clicked,
    shows a small modal with the hash recomputation result (green checkmark animation).
- Sidebar with: deposit/withdraw buttons, portfolio stats, link to the strategy
  leaderboard.

Visual style: Dark mode primary, off-white text, brand accent color (deep blue or
violet). Typography: clean and modern; small monospace where on-chain hashes /
addresses appear; serif for big headlines (the academic-rigor cue). Information
density: high but not crowded — this user is checking on a portfolio, not browsing.

Make the prototype interactive enough that I can flow from screen 1 → 2 → 3 with
the navigation working. Don't worry about real data; placeholder values are fine.
```

**What to do with the output:**

- Share with Daniel (frontend owner). He builds the actual React/Next.js implementation
  using this as a visual reference.
- Iterate on any screens that don't match the intended feel.
- Export key screens for the pitch deck (Slide 3 can use Screen 2; Slide 4's demo will
  use the real implementation).

---

## Prompt 4 — Strategy detail page (single screen, for the deck)

**Setup notes:** Single screen. Use **Prototype / High fidelity**.

```
Single screen: the Archimedes Strategy Detail page.

Context: the user clicked on a strategy in their portfolio. This screen surfaces the
strategy's "passport" — the verifiable provenance.

Layout:
- Header: Strategy name + "Paper-grounded" badge.
- Subheader: paper citation, formatted like an academic reference:
  "Jegadeesh, N., & Titman, S. (1993). Returns to buying winners and selling losers:
  Implications for stock market efficiency. Journal of Finance, 48(1), 65–91.
  [arxiv:... | doi:...]"
- Three-column metadata strip:
  - Paper-claimed Sharpe: 1.16
  - Our backtest Sharpe (10-year, 10bps costs): 0.87
  - Delta: -25%
  - All three should be hash-anchored on Arc (small "View on Arc" link)
- Methodology section: ~3 paragraphs of plain-English explanation, with key terms
  bolded.
- Backtest section: equity curve chart with our backtest, plus a comparison line
  for the paper's claimed equity curve if available.
- Validation section: list of audit checks passed:
  ✓ Walk-forward (70/30 split)
  ✓ No look-ahead bias detected
  ✓ Out-of-sample Sharpe > 0.5
  ✓ Curator validated (with curator wallet address)
- On-chain registration: tx hash + "View on Arc Explorer" link.

Visual style: same dark-mode + deep-blue accent as the rest of the prototype. This
screen should feel like a research report, not a marketing page — that's the "we're
serious about academic rigor" cue.
```

---

## Prompt 5 — Reasoning trace viewer modal

**Setup notes:** Modal / overlay component within the portfolio dashboard. Use
**Prototype / High fidelity**.

```
Component: the Reasoning Trace Viewer modal.

Context: the user clicked "View reasoning trace" on a specific agent decision in the
Decisions tab. A modal opens showing the full trace.

Layout:
- Header: Decision type + trigger + timestamp
  ("Autonomous Rebalance — Regime change to Risk-Off — 2026-05-23 14:32 UTC")
- Market context section: a compact grid showing the metrics the agent saw at
  decision time (VIX, S&P 50/200 crossover, credit spreads, BTC dominance,
  cross-asset correlation, USYC yield).
- Reasoning section: the LLM-generated explanation as plain prose. Should look
  like writing, not bullet points — this is what a thoughtful analyst would write.
- Action taken section: a "before vs. after" portfolio weights comparison, plus
  a list of trades executed with on-chain tx hashes for each.
- Tool calls section: collapsible — by default shows count ("9 tool calls"), expand
  to see each tool, input hash, output hash, latency.
- Verification footer: content hash + storage pointer + "Verify trace" button.
  When clicked, animates a recomputation of the hash and shows pass/fail with
  green checkmark or red X.

Visual style: dense but organized. The header should be sticky if the modal
scrolls. Hash strings displayed in small monospace with copy-to-clipboard buttons.
```

---

## Logo color and typography proposal (use across all prompts)

If you want consistency across the slide deck and the UI prototype, propose this
design system up front:

**Primary palette:**

- Background: `#0E1116` (near-black)
- Surface: `#1A1F2E` (slightly lighter for cards)
- Text primary: `#F3F4F6` (off-white)
- Text secondary: `#9CA3AF` (muted gray)
- Brand accent: `#2A4DD1` (deep blue) — or alternative `#7B2CBF` (violet)
- Success: `#10B981` (green, for "Verify trace" checkmarks)
- Warning: `#F59E0B` (amber, for "paper-claim delta" if > 30%)
- Error: `#EF4444` (red, for failed verifications)

**Typography:**

- Headlines: `Crimson Pro` or `Source Serif Pro` (serif — the academic cue)
- Body: `Inter` or `Geist Sans` (clean modern sans)
- Monospace (hashes, addresses): `JetBrains Mono` or `Geist Mono`

You can paste this design-system block into any Claude Design prompt to maintain
consistency.

---

## Sources for visual reference (if Claude Design supports URL fetch)

If Claude Design lets you reference live sites, these are reasonable inspirations to
cite:

- [Arc Network](https://www.arc.network/) — clean dark-mode crypto-finance aesthetic.
- [Stripe](https://stripe.com/) — gold standard for professional financial product UI.
- [Linear](https://linear.app/) — exemplary dark-mode SaaS visual language.
- [Cleantype hero pages](https://wealthfront.com/) — for the consumer-facing
  trustworthy-finance feel.
- [Etherscan](https://etherscan.io/) — for how on-chain data should be presented
  (compact, monospace, copy-friendly).
- [DefiLlama](https://defillama.com/) — for portfolio dashboards in the DeFi context.

You can paste those URLs into the design conversation and ask Claude Design to draw
inspiration from them, particularly for color palette / typography / information
density.

---

## Workflow recap

1. **Set up a design system** in Claude Design with the palette/typography above.
2. **Run Prompt 1** (logo) first — pick a logo, lock it before doing slides/UI.
3. **Run Prompt 2** (slide deck) — generate, iterate, export.
4. **Run Prompt 3, 4, 5** (UI screens) — Daniel uses these as reference for the
   actual frontend build.
5. **Iterate** — Claude Design is conversational; refine outputs based on your eye.

If you take screenshots of references along the way, drop them in the conversation —
both Claude Design and this Linus session can ingest them. URLs work too. Either is
fine; mix freely.
