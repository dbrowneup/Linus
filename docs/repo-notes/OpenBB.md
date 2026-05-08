# OpenBB (`OpenBB-finance/OpenBB`)

## 1. Purpose and scope

OpenBB — formally the Open Data Platform (ODP) — is the open-source "connect once, consume everywhere" data abstraction
layer for finance. It is a Python library, a CLI (`openbb-cli`), a FastAPI REST server (`openbb-api` on port 6900), and
an MCP server (`openbb-mcp`), all sitting on top of ~35 provider integrations that span equities, options, derivatives,
crypto, currency, ETFs, commodities, fixed income, indices, news, macro/economy, regulators, and SEC filings. The
distinguishing fact is that OpenBB itself is **not an agent** — it is the data-and-tools substrate that the other Group
10 agents (dexter, QuantAgent, TradingAgents) would call. Within Linus this is squarely a Phase 7 "domain skill"
candidate: a worker-attached toolset that gives Dan financial data access without writing thirty provider clients.

## 2. Architecture summary

The codebase is a Poetry monorepo at `openbb_platform/` split into `core/` (the abstraction kernel), `providers/` (one
package per data source: `yfinance`, `fmp`, `intrinio`, `tiingo`, `sec`, `fred`, `federal_reserve`, `ecb`, `oecd`,
`imf`, `bls`, `cboe`, `nasdaq`, `tradier`, `alpha_vantage`, `benzinga`, `tradingeconomics`, `cftc`, `finra`, `finviz`,
`tmx`, `eia`, `wsj`, `seeking_alpha`, `congress_gov`, `government_us`, `deribit`, `econdb`, `multpl`, `stockgrid`,
`biztoc`, `famafrench`, `federal_reserve`, `nasdaq`, `yfinance`…), `extensions/` (the verb surface: `equity`, `crypto`,
`currency`, `derivatives`, `economy`, `etf`, `fixedincome`, `index`, `news`, `commodity`, `regulators`, plus computed
extensions `quantitative`, `econometrics`, `technical`, and the `mcp_server`/`platform_api` mounts), and
`obbject_extensions/` (post-processing on the returned `OBBject`).

The provider abstraction is small and clean. Each endpoint defines a `QueryParams` model (typed input), a `Data` model
(typed output, the "standard model" — there are ~181 of these in `core/openbb_core/provider/standard_models/`), and a
per-provider `Fetcher[Q, R]` implementing `transform_query → (a)extract_data → transform_data`. Standard models are the
normalization layer: e.g., `EquityHistoricalData` looks the same whether it came from yfinance or fmp or intrinio, and
the `RegistryMap` wires provider implementations to the public Pythonic surface
(`obb.equity.price.historical("AAPL", provider="yfinance")`). Credentials are passed in per call from the user's local
credential store rather than being captured by OpenBB; most non-trivial providers require their own API key (FMP,
Intrinio, Tiingo, Alpha Vantage, Benzinga, Polygon-style services). The free defaults that work without keys are
essentially `yfinance`, `sec`, `federal_reserve`, `fred` (with a free FRED key), `ecb`, `oecd`, `imf`, `bls`,
`congress_gov`, `government_us`.

The MCP server (`openbb-mcp-server`) is the AI-integration story and is the most interesting recent addition. It wraps
the FastAPI app and exposes endpoints as MCP tools, but with a **dynamic per-session activation** model: agents see a
small discovery toolset first, browse categories, and activate only the tools they need — directly addressing context-
window bloat (~hundreds of endpoints would otherwise blow any small model's tool budget). This is closer to a
tool-broker than a static MCP server.

OpenBB Platform vs OpenBB Workspace: the Platform (this repo, AGPLv3) is the open-source data layer. The Workspace
(`pro.openbb.co`, closed-source enterprise UI) is OpenBB's commercial hosted product where their own AI agents and
visualizations live. The open repo only covers the data layer plus the MCP/REST surfaces; the Workspace agents are not
here.

## 3. What's reusable in Linus

The Python SDK and the MCP server, both directly. `pip install openbb` (with selected `extras=[...]`) gives Linus a
single import surface for ~35 providers without writing or maintaining provider clients. Wrapped as a Phase 7 worker
skill ("financial-data") it would let a worker model answer "pull AAPL historicals, BLS CPI, FRED 10Y yields, and SEC
filings for X" with one tool surface. The MCP server is the cleaner integration once Phase 3 commits to MCP as Linus's
extensibility substrate — `openbb-mcp` running locally adds a financial-tool catalog that any MCP-aware harness (Cline,
openclaw, claw-code-local) sees automatically, with the per-session dynamic-activation pattern keeping token cost
bounded. The 181 standard `Data` models are also reference-grade Pydantic schemas for "what does normalized financial
data look like" — useful even if Dan eventually writes thinner adapters himself.

Compared to **nixtla** (the other library-shaped Group 10 sibling), OpenBB and nixtla are complementary, not
overlapping: OpenBB _gets you the time series_, nixtla _forecasts on it_. A natural Linus pairing is
`openbb → pandas → nixtla.statsforecast/neuralforecast → result`. Compared to the agentic siblings (**dexter**,
**QuantAgent**, **TradingAgents**), those are consumers — they all need a data layer underneath, and OpenBB is the most
production-grade option for that role. If Linus hosts any of them as worker skills later, OpenBB is the data substrate
they'd plug into.

## 4. What's inspiration only

The dynamic per-session MCP-tool activation pattern is worth borrowing for Linus's own tool registry: a small discovery
surface plus on-demand activation is the right answer to "I have 200 tools and a 7B model with a 32k context." The
standard-model + Fetcher pattern is also a good architectural template if Linus ever needs its own multi-provider
abstraction in another domain (genomics data sources, paper-corpus providers) — the typed QueryParams/Data/Fetcher trio
is small, clear, and language-agnostic. The OpenBB Workspace UI, charting extension, and the commercial Pro tier are not
Linus territory.

## 5. What's incompatible or out of scope

**License: AGPLv3.** This is the load-bearing constraint. AGPL's network-use clause means that if Linus ships an HTTP
endpoint to anyone other than Dan (Phase 8 mobile, Mac Studio peer, future shared deployments) and that endpoint exposes
OpenBB-derived functionality, the entire combined work plausibly inherits AGPL obligations. For Phase 2–7
strictly-personal use on Dan's MacBook this is fine; for any "let a friend use Linus" scenario it forces either a clean
process boundary (OpenBB runs as a separate `openbb-api` daemon, Linus calls it as an external service — the "mere
aggregation" boundary) or replacing OpenBB with permissively-licensed alternatives. Worth an ADR before Phase 8.

**API-key dependency.** Most useful providers require third-party keys (FMP, Intrinio, Tiingo, Alpha Vantage, Benzinga).
The truly free set is yfinance, SEC, FRED (with free key), federal_reserve, ECB, OECD, IMF, BLS, plus a few
US-government feeds. This sets the floor for "what works with zero accounts."

**Footprint.** `pip install "openbb[all]"` pulls in a substantial dependency tree (Poetry monorepo with separate
sub-packages per provider and extension). Linus should install only the extras Dan actually uses — for a first pass,
something like `openbb[mcp_server,quantitative,technical]` plus the always-on free providers is enough.

**Not an inference or training repo.** Zero overlap with Linus's Inference/Training pillars. This is data + tools only.

## 6. Recommendation: **Study (with intent to integrate as a Phase 7 skill)**

Don't pull OpenBB into the dependency tree yet. Stand it up in a throwaway env
(`uv pip install openbb-mcp-server openbb` in `experiments/openbb/`), point `openbb-mcp` at Cline or claw-code-local,
and run a few real tasks: "pull AAPL 5-year historicals and FRED 10Y yields, compute correlation," "summarize the latest
10-K filing for NVDA," "show me ECB policy-rate history." If the data quality and tool ergonomics hold up — and the MCP
per-session activation keeps the tool list small enough for a 7B worker — graduate to a real Phase 7 skill with a small
curated extras set. The AGPL question doesn't bite until Phase 8.

## 7. Questions for Dan

1. **AGPL stance.** Are you comfortable with AGPL-licensed components inside Linus during Phases 2–7 (personal use, no
   network exposure to others), with the explicit ADR that Phase 8 multi-user scenarios trigger a re-architecture to a
   process-boundary call or a license replacement? Or do you want a hard "permissive-only" rule from the start?
2. **Provider key budget.** The free-tier providers (yfinance, SEC, FRED, federal_reserve, ECB, OECD, IMF, BLS) cover
   macro, equity historicals, and filings. Paid providers (FMP, Intrinio, Tiingo) add fundamentals depth, real-time
   quotes, and broader coverage. Are you planning to subscribe to any, or should the Phase 7 skill be scoped to the free
   set?
3. **MCP-first or SDK-first.** Two integration paths: (a) `openbb-mcp` runs as its own local daemon and Linus tools are
   MCP-discovered; (b) Linus imports `openbb` directly and exposes hand-picked endpoints as Linus-native tools. Path (a)
   is cleaner architecturally and aligns with the openclaw / cline MCP question; path (b) gives tighter control and
   avoids running an extra process. Preference?
4. **Pairing with nixtla.** The natural workflow is OpenBB pulls the series, nixtla forecasts. Worth specing a small
   end-to-end Phase 7 demo task ("forecast next 30 days of AAPL close with confidence intervals") that exercises both as
   one combined skill?
5. **Adjacent vs core.** You've said finance is "useful adjacent capability," not core. Should this skill ride along
   with the same Phase 7 sandbox tier as scientific tools, or sit in a more restricted tier given that financial
   workflows can shade into trading-decision territory you may not want a worker model recommending on?
