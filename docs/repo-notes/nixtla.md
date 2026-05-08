# nixtla (`Nixtla/nixtla`)

## 1. Purpose and scope

This repo is the **Python SDK for TimeGPT-1**, marketed as "the first foundation model for forecasting and anomaly
detection" — an encoder-decoder transformer trained from scratch (not on top of an LLM) on >100B time-series data points
spanning finance, electricity, weather, IoT, web traffic, sales, transport, demographics, healthcare, and banking. The
SDK itself is Apache-2.0; the **model weights are closed-source and the inference is a hosted paid API** at
`https://api.nixtla.io` (also deployable inside Snowflake or Azure AI Studio behind a customer's account). The pip
package — `nixtla>=0.7.0` — exposes a single class, `NixtlaClient`, that wraps `forecast`, `detect_anomalies`,
`cross_validation`, `finetune`, and a few plotting helpers. For Linus's group-10 finance/quant cluster this is the
broadest member: time-series forecasting is the substrate finance sits on, but it also hits omics-trajectory,
epidemiology, and environmental-monitoring problems Dan cares about. It is also the cluster's clearest collision with
the "no paid APIs" north star: TimeGPT itself violates it, while the surrounding **Nixtlaverse** of sister libraries
(`statsforecast`, `mlforecast`, `neuralforecast`, `hierarchicalforecast`, `utilsforecast`) is fully local and fully
open.

## 2. Architecture summary

The repo is a thin SDK plus extensive notebook documentation (`nbs/`, `timegpt-docs/`) and an `experiments/` tree of
benchmark notebooks. The actual code is one file — `nixtla/nixtla_client.py`, ~3.5k lines — that constructs HTTPX
requests with `orjson` + `zstd` payload compression, adds `tenacity` retry/backoff, validates DataFrames via
`utilsforecast`, batches series with a `ThreadPoolExecutor`, and parses responses back into `pandas`/`polars` frames
through `narwhals`. It is, structurally, an enterprise REST client: pydantic models for inputs, custom `ApiError` class,
support for exogenous variables, holiday/calendar features (`pandas_market_calendars`, `holidays`), prediction intervals
via conformal prediction, fine-tuning calls that submit data to the server and return a model id, and distributed
execution via `fugue` to run the same client over Spark/Dask/Ray clusters. Architecturally it is the opposite of
`pmetal` or `mlx-lm`: zero local compute beyond serialization, all intelligence on the other end of the wire. The `dev`
extras pull in the rest of the Nixtlaverse, but those are sister projects in their own repos — `statsforecast`
(AutoARIMA, ETS, Theta, MSTL, CES), `mlforecast` (LightGBM/XGBoost over lag features), `neuralforecast` (NHITS, NBEATSx,
TFT, PatchTST, TimesNet), `hierarchicalforecast` (reconciliation), `utilsforecast` (shared validation/preprocessing).

## 3. What's reusable in Linus

The TimeGPT SDK itself is not reusable under the no-paid-APIs rule unless Dan opts in to the free tier or self-hosts
through Snowflake — neither is core-Linus material. The reusable surface is the **Nixtlaverse outside this repo**:
`statsforecast` and `mlforecast` are pure-Python/Numba and run cleanly on Apple Silicon today, no special build, no GPU;
`neuralforecast` runs on PyTorch with MPS where available and is the most plausible Phase 7 "forecasting skill" backend
— NHITS and PatchTST are competitive with TimeGPT on many public benchmarks while staying local. `utilsforecast` is the
right shared validation layer for any time-series tool Linus exposes regardless of backend. Compared to **OpenBB**
(group sibling, finance-data layer): the two are complementary and non-overlapping — OpenBB fetches the series, the
Nixtlaverse models them, and `TradingAgents`/`QuantAgent` would consume the forecasts as features. A Phase 7 Linus skill
called `forecast(df, h, level)` could trivially call either `statsforecast.AutoARIMA`, `neuralforecast.NHITS`, or — with
an explicit user opt-in env var — `NixtlaClient`, behind a uniform interface.

## 4. What's inspiration only

The single-class `NixtlaClient` API surface is a clean reference for what a foundation-model time-series tool should
look like from the consumer side — `client.forecast(df, h=24, level=[80, 90])` is the kind of one-liner Linus tools
should aspire to. The **time-series-as-foundation-model framing** is the research-relevant pattern beyond finance: the
TimeGPT-1 paper (`arXiv:2310.03589`) and successors (Chronos, Moirai, TimesFM, Lag-Llama, Tiny Time Mixers) are
plausibly more transferable to omics trajectories and environmental data than LLMs are. None of those models live in
this repo, but the Nixtla SDK pattern — pretrained model + zero-shot inference + optional fine-tune — is the template.
Worth tracking as a Phase 6 fine-tuning candidate: TimesFM and Chronos are open-weight, run on PyTorch/MPS, and are
small enough (50M–500M) that a LoRA over Dan's domain series is tractable on 32 GB.

## 5. What's incompatible or out of scope

TimeGPT itself: closed weights, hosted paid API, telemetry of every series sent to a third party, latency for any real
interactive forecasting workload. Direct integration into Linus is out of scope by the no-paid-APIs rule and by
data-sovereignty concerns when the input series might be patient-derived or pre-publication. Snowflake and Azure
deployments don't fix this for Dan — they require enterprise infrastructure he doesn't run. The `distributed` extra
pulls in Spark/Dask/Ray; not Linus's territory on a single MacBook. The fine-tune endpoint sends training data to
Nixtla's servers — exclude for any sensitive corpus.

## 6. Recommendation: **Study**

Skip the TimeGPT SDK as a Linus dependency. Adopt the **sister Nixtlaverse libraries** (`statsforecast`, `mlforecast`,
`neuralforecast`, `utilsforecast`) into a Phase 7 forecasting skill behind a unified `forecast` / `detect_anomalies`
interface, and treat this repo as the reference design for the API shape a future open-weight foundation-model backend
(TimesFM, Chronos) would slot into. Read the `experiments/` notebooks for benchmark methodology. Do not pin `nixtla` as
a runtime dependency of any Linus core component.

## 7. Questions for Dan

1. **Forecasting as a Phase 7 skill?** Time series forecasting is a clean candidate for the first non-trivial Linus
   domain skill — well-defined I/O, easy benchmarks, useful both for finance and for omics/environmental data. Worth a
   Phase 7a entry, or does this stay informal?
2. **Open-weight foundation TS models in Phase 6.** TimesFM (Google, ~200M) and Chronos (Amazon, T5-based, 20M–700M) are
   open and run on MPS. Interesting as Phase 6 fine-tuning targets on omics-trajectory or epidemiological data — or is
   biological time-series data shaped too differently from generic series for transfer to work?
3. **Data-sovereignty rule on TimeGPT.** Worth writing an explicit ADR that hosted-model TS APIs (TimeGPT, Google Vertex
   Forecast, AWS Forecast) are forbidden for any series derived from patient samples or unpublished experiments, even if
   a user explicitly opts in?
4. **Anomaly detection for instrument data.** `detect_anomalies` is a natural fit for QC of long-running biology
   instruments (sequencer flow rates, mass-spec ion currents, qPCR baselines). Is there a real corpus of such series in
   `context/` that could become a Linus benchmark?
5. **Hierarchical reconciliation for multi-omics.** `hierarchicalforecast` enforces consistency between aggregate and
   disaggregate forecasts (parent species + sub-species, total mRNA + per-isoform). Useful pattern for omics where
   pathway-level + gene-level forecasts must reconcile, or unrelated to how you actually analyze that data?
