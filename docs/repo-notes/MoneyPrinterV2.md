# MoneyPrinterV2 (`FujiwaraChoki/MoneyPrinterV2`)

## 1. Purpose and scope

MoneyPrinterV2 (FujiwaraChoki/MoneyPrinterV2; Python 3.12; AGPL-3.0; YouTube-tutorial-backed project with active
community via Discord) is a CLI application that **automates four online workflows for content/marketing automation**:
(1) Twitter/X Bot for tweet generation and posting; (2) YouTube Shorts Automator for full pipeline video generation
(LLM script → TTS → images via Nano Banana 2 / Gemini image API → MoviePy composite → Selenium upload); (3) Affiliate
Marketing via Amazon scraping + LLM pitch generation + Twitter share; (4) Local Business Outreach via Google Maps
scraping (Go binary required) + email extraction + SMTP cold outreach. The repo is a complete rewrite of the original
MoneyPrinter project, focused on modular architecture and wider feature scope.

The codebase is a CLI-only tool — no web UI, no REST API, no test suite, no CI, no linting config — with a single
entry point (`src/main.py`) plus a headless cron runner (`src/cron.py`) for scheduled execution. State is JSON-file-
based in a `.mp/` directory at the project root. Browser automation uses pre-authenticated Firefox profiles (never
handles login). LLM is Ollama-backed (Python SDK, not LiteLLM). Image generation uses Gemini's Nano Banana 2. TTS uses
KittenTTS or AssemblyAI for STT. CRON scheduling uses Python's `schedule` library (in-process, not OS cron) which spawns
subprocesses via `subprocess.run`.

The framing is candidly oriented toward monetization-by-automation: the README declares the project's intent ("An
Application that automates the process of making money online"), and includes a disclaimer that the project is "for
educational purposes only."

## 2. Architecture summary

**Entry points:**

- `src/main.py` — interactive menu loop (primary). Must be run from project root (adds `src/` to `sys.path`).
- `src/cron.py` — headless runner invoked by the scheduler as subprocess: `python src/cron.py <platform> <account_uuid>`.

**Provider pattern (configured in `config.json`):**

| Category | Options | Notes |
| -------- | ------- | ----- |
| LLM | Ollama (Python SDK) | Single provider; if `ollama_model` empty, user picks at startup |
| Image gen | Nano Banana 2 (Gemini image API) | Single provider |
| STT | `local_whisper` or `third_party_assemblyai` | Two options |

**Key modules:**

- `src/llm_provider.py` — unified `generate_text(prompt)` using Ollama Python SDK.
- `src/config.py` — 30+ getter functions, each re-reads `config.json` on every call (no caching).
- `src/cache.py` — JSON file persistence in `.mp/` (accounts, videos, posts, products).
- `src/constants.py` — menu strings, Selenium selectors for YouTube Studio / X.com / Amazon.
- `src/classes/YouTube.py` — most complex class; full pipeline: topic → script → metadata → image prompts → images → TTS → subtitles → MoviePy combine → Selenium upload.
- `src/classes/Twitter.py` — Selenium automation against x.com.
- `src/classes/AFM.py` — Amazon scraping + LLM pitch generation.
- `src/classes/Outreach.py` — Google Maps scraper (Go binary) + email sending via yagmail.
- `src/classes/Tts.py` — KittenTTS wrapper.

**Persistence model:** JSON files in `.mp/` (e.g., `youtube.json`, `twitter.json`, `afm.json`). Temporary WAV / PNG /
SRT / MP4 files cleaned per run by `rem_temp_files()`. No database.

**Browser automation:** Selenium with pre-authenticated Firefox profiles (path stored per-account in cache JSON and as
default in `config.json`).

**Dependencies:** ImageMagick (for MoviePy subtitle rendering), Firefox profile (pre-logged-in to target platforms),
Ollama, Nano Banana 2 API access, optionally Go (for Outreach Google Maps scraper).

## 3. What's reusable in Linus

**The `subprocess.run` cron-spawning pattern is a Phase 3 spawner reference.** MoneyPrinterV2's cron runner spawns
subprocesses via `subprocess.run(["python", "src/cron.py", platform, account_id])`. For Linus's Phase 3 multi-agent
spawner (DEC-0050), this is a usable v0 spawning primitive — out-of-process Worker invocation with command-line argument
passing. The pattern is simple, well-understood, and works on macOS (which `workgraph`'s `tree-kill` does not, per
CLAUDE.md "workgraph's tree-kill is Linux `/proc`-only; macOS port needs a `psutil`-based equivalent"). The Phase 3
spawner spec should consider `subprocess.run` as a v0 fallback when workgraph-style coordination is over-engineered.

**Per-platform provider abstraction.** MoneyPrinterV2's provider pattern (LLM = Ollama, Image = Nano Banana 2, STT =
local_whisper or AssemblyAI) is a clean string-based dispatch for swappable providers. For Linus's Phase 1c
worker-selection spike, the same pattern is portable: each worker has a `provider` string in the registry, and dispatch
routes to the right implementation. The Linus implementation is more complex (memory_mode, cot_budget, deployment field
per DEC-0046), but the underlying string-based provider dispatch is the same shape.

**Pre-authenticated browser profiles as a credential pattern.** MoneyPrinterV2's Selenium uses pre-authenticated
Firefox profiles, **never handling login**. This is a usable credential primitive: credentials live in the browser
profile, not in code or config. For Linus's Phase 7+ biology Workers that need authenticated web access (e.g., to
private databases), the pre-authenticated browser profile pattern is portable as a credential-isolation primitive.

**`config.json` re-read on every call pattern.** MoneyPrinterV2's `config.py` re-reads `config.json` on every getter
call (no caching). This is an explicit choice — runtime config changes take effect without restart. For Linus's
Phase 2a backend, the same pattern is usable for config that should be live-reloadable (e.g., the in-context cap policy
per DEC-0032). The cost is minor — JSON parsing on every config-getter call is negligible — and the benefit is live
config updates.

**`rem_temp_files()` discipline.** MoneyPrinterV2 cleans temporary files (`.wav`, `.png`, `.srt`, `.mp4`) on every run.
For Linus's Phase 7+ biology Workers that generate intermediate files (e.g., simulation outputs, intermediate sequence
files), the same discipline is portable as a per-Worker-invocation cleanup step.

**Local-Ollama-first LLM client.** MoneyPrinterV2 uses Ollama directly via its Python SDK, not LiteLLM. This is the
**same choice as Linus** (per CLAUDE.md, the brew-managed Ollama is the Phase 1c worker server). Two independent
codebases converging on Ollama-direct (versus LiteLLM-wrapped Ollama) is a small signal that the direct integration is
the right pattern. The Linus Phase 2a backend should follow.

## 4. What's inspiration only

**AGPL-3.0 license.** AGPL-3.0 is **strongly copyleft** — any service deployed from AGPL-3.0 code must release source.
Linus's commitment to open development is compatible with AGPL-3.0 at the source level, but vendoring AGPL-3.0 code
into Linus would force Linus's entire orchestration layer to be AGPL-3.0-licensed. This is a meaningful design
constraint. Linus should not vendor MoneyPrinterV2 code; the patterns are portable as design vocabulary only.

**The "make money online" framing is operationally distinct from Linus's scientific work.** MoneyPrinterV2 targets
short-form-content automation and affiliate marketing. Linus targets private scientific computing. The framings don't
converge; the patterns (provider abstraction, cron spawning) are portable but the specific automation flows
(YouTube Shorts, Twitter, Amazon affiliate, Google Maps outreach) are not.

**Selenium with pre-authenticated browser profiles is a brittle pattern.** Pre-authenticated browser profiles work
until the target platform changes its UI or its anti-bot measures. The Selenium-against-YouTube-Studio / X.com / Amazon
patterns are notoriously fragile. Linus should not adopt Selenium-based web automation as a first-class primitive;
better alternatives (official APIs, headless browsers like Playwright with explicit auth flows) exist.

**No test suite, no CI, no linting.** MoneyPrinterV2's README explicitly notes the absence of test infrastructure. This
is incompatible with Linus's engineering convention (CLAUDE.md "Smoke-test gates," DEC-0027 measurement-driven
discipline). Linus's adoption of any MoneyPrinterV2 pattern should be tested even where MoneyPrinterV2 itself isn't.

## 5. What's incompatible or out of scope

**The four automation workflows (Twitter, YouTube Shorts, Affiliate Marketing, Outreach) are out of scope.** Linus's
orchestration layer is not a content-marketing tool. These specific workflows are not relevant for adoption.

**Go binary dependency (for Outreach).** The Google Maps scraper requires the Go programming language. Linus's
Python-centric stack (with Rust for pmetal and TS/JS for openclaw, per DEC-0027) does not include Go. Adopting any
Outreach-adjacent functionality would require either re-implementing the Go scraper in Python or adding Go to the Linus
dependency stack. Neither is justified.

**Nano Banana 2 / Gemini image API is a paid external API.** Linus's local-first commitment (per DEC-0027) argues for
local image generation (e.g., MFLUX or Stable Diffusion via MLX) rather than external API calls. The Nano Banana 2
dependency is out of scope.

**KittenTTS and AssemblyAI dependencies.** Both are TTS providers; KittenTTS is bundled and AssemblyAI is external.
Linus's local-first commitment would prefer WhisperKit (per `local-whisper`, [`local-whisper.md`](local-whisper.md)) for
STT and a local TTS option (Apple's `AVSpeechSynthesizer`, or a future TTS Worker). KittenTTS and AssemblyAI are out of
scope.

**ImageMagick for MoviePy subtitle rendering.** Heavy external dependency for a feature (subtitle rendering) Linus
doesn't need. Out of scope.

## 6. Recommendation: **Watch**

MoneyPrinterV2 is the **least Linus-aligned of the 7 external repos in this triage batch**. The framing
(content-monetization automation), the license (AGPL-3.0, strongly copyleft), the specific workflows (YouTube Shorts /
Twitter / Affiliate / Outreach), and the brittle web-automation patterns (Selenium against changing platform UIs) all
argue against active adoption. The portable patterns (provider abstraction, cron spawning, config-reload-on-getter,
local-Ollama-direct, pre-authenticated browser profiles) are individually useful but small enough to lift as design
vocabulary from any reference; MoneyPrinterV2 is not the strongest reference for any of them.

Recommendation: **Watch** for whether the project's local-Ollama-direct pattern + provider-abstraction discipline
matures into broader patterns. The independent-confirmation signal — that another 2024-2026 personal-automation project
chose Ollama-direct over LiteLLM-wrapped Ollama — is the most useful Linus calibration data point. Beyond that,
MoneyPrinterV2 is a marketing-automation tool with limited relevance to Linus's scientific-computing scope.

The repo is included in the triage batch for completeness rather than for active adoption — it illustrates the **range
of agentic-automation projects** in the cloned-repo collection, which is itself a calibration data point for the
broader landscape.

## 7. Questions for Dan

1. **Confirm AGPL-3.0 incompatibility with Linus vendoring.** AGPL-3.0's network-services clause is a hard constraint
   for any code that becomes part of a network-accessible Linus deployment. Worth a brief check by Dan that this is
   correctly understood, since the MoneyPrinterV2 README does mention AGPL-3.0 but not the network-services
   implications.

2. **Watch-only status — confirm or adjust.** The Watch recommendation deprioritizes MoneyPrinterV2 relative to the
   other 6 external repos in this batch. If Dan wants more attention on a specific pattern (e.g., the provider-
   abstraction pattern), this should be surfaced explicitly.

3. **Pre-authenticated browser profile pattern for Phase 7+ Workers.** The pattern is portable for credential
   isolation. Worth a Phase 7+ spec inclusion when authenticated-web-access Workers are scoped?

4. **`subprocess.run` cron spawning as a Phase 3 spawner v0 fallback.** Worth surfacing in the Phase 3 spawner spec as
   the simpler-than-workgraph spawning primitive for cases where full DAG coordination is over-engineered?
