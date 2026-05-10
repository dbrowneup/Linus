# ClawBio (`ClawBio/ClawBio`)

## 1. Purpose and scope

ClawBio is a **bioinformatics-native AI agent skill library** built on OpenClaw — 63 first-party skills (with the
README headlining the curated subset and the `skills/` directory containing a few additional community-contributed
entries) covering pharmacogenomics, GWAS lookup, polygenic risk scoring, ancestry PCA, fine-mapping, scRNA-seq,
clinical-variant reporting, methylation clocks, proteomics, metagenomics, and a Galaxy-tools bridge that exposes
8,000+ external bioinformatics tools through a single skill. v0.5.0 (April 2026) added a benchmark and validation
infrastructure (AD ground-truth gene set, mock API server for offline CI, swappable fine-mapping backends, 168/182
benchmark tests passing across 10 audited skills). Each skill is a self-contained directory with a `SKILL.md`
specification, Python implementation, demo data, tests, and a reproducibility bundle (`commands.sh`, `environment.yml`,
SHA-256 checksums) that ships with every analysis output. Distributed as a Python CLI/library, a Telegram/Discord bot
("RoboTerri") via OpenClaw gateway, and a Claude Code plugin (`/plugin marketplace add ClawBio/ClawBio`). MIT licensed,
CC0 demo data (the "Corpasome" — a 30x WGS reference genome from Manuel Corpas), DOI-versioned releases on Zenodo. For
Linus this is the **closest existing precedent for what a Phase 7 inaugural bio-skills bundle should look like in
working form**, sitting alongside `bioSkills` (~438 skills, broader and shallower) as the two canonical bio-skill
libraries in the cloned-repo collection. It is the fifth member of the g9-bio cluster after Bacformer, BioReason,
bioSkills, and deepsems.

## 2. Architecture summary

Python 3.10+ monorepo, no `pip install` package yet — clone-and-run from `requirements.txt`. The single entry point
`clawbio.py` (~1100 lines) holds a `SKILLS` registry dict that maps each skill to its script path, demo arguments,
description, and a per-skill `allowed_extra_flags` allowlist (security control INT-001 — extra flags are filtered
against the per-skill allowlist before subprocess invocation, blocking flag injection through the agent layer).
`run_skill()` invokes each skill as a subprocess with `--input`, `--output`, and `--demo` always supported by
convention; `list_skills()` and `upload_profile()` round out the importable API. Per-skill folder shape: `SKILL.md`
(YAML frontmatter with `openclaw` schema — `name`, `description`, `version`, `trigger_keywords`, install
metadata — plus a markdown body with Trigger / Scope / Workflow / Example Output / Gotchas / Safety / Agent Boundary /
Chaining Partners / Maintenance sections), a Python implementation file, optional `api.py` for in-process import, a
`tests/` directory (red/green TDD is mandatory), and an `examples/` or `demo_*.txt` demo dataset. Skills produce a
`<output>/report.md` plus `figures/`, `tables/`, and `reproducibility/` subdirectories with the bundle. A
`bio-orchestrator` skill routes free-text queries to the right downstream skill based on file type and keywords. The
Galaxy Bridge skill (`skills/galaxy-bridge/`) wraps `BioBlend` to expose the full usegalaxy.org tool catalog. Tests
register via `pytest.ini` (1,756 tests at v0.5.0). Catalog generation is automated:
`scripts/generate_catalog.py` reads each `SKILL.md` frontmatter and produces `skills/catalog.json` (a 1,995-line
machine-readable index used by agents for skill discovery). The `templates/SKILL-TEMPLATE.md` defines a 17-check
conformance checklist enforced by `scripts/lint_skills.py`.

## 3. What's reusable in Linus

**The 63-skill library shape is the closest precedent for the Phase 7 inaugural bio-skills bundle.** ROADMAP currently
positions `bioSkills` (~438 skills) as the placeholder Phase 7 payload; ClawBio is a useful contrast — narrower domain
focus (human consumer/clinical genomics rather than the full computational-biology spectrum), substantially deeper
per-skill engineering (every skill has tests, demo data, a reproducibility bundle, and a benchmark scorer where
ground truth exists), and shipped behind a working Python CLI with a security-filtered subprocess invocation layer.
The two are complementary, not redundant: `bioSkills` is breadth-first and harness-installable; ClawBio is
depth-first and runtime-bundled. Plausible Phase 7 strategy is to take the ClawBio engineering shape (per-skill
tests + reproducibility bundle + catalog generator + conformance linter) and fill it with bioSkills-equivalent
breadth tuned to Dan's metagenomics + B. braunii work.

**The reproducibility bundle (`commands.sh` + `environment.yml` + SHA-256 checksums) is a directly liftable Linus
convention candidate.** Every ClawBio analysis emits this bundle as part of the standard output, not as an
afterthought. The argument for adoption is straightforward: any Linus skill that produces a publishable artefact
should ship the bundle so a reviewer can reproduce the result in one command without contacting Dan. This generalizes
beyond biology — RNA-seq DE plots, paper synthesis figures, anything Linus generates that might end up in a paper or
a slide. Worth raising as ADR seed `_Seed: DEC-NNNN reproducibility-bundle-output-convention_` for Phase 7
finalization. Companion to DEC-0023 (output interface citations + LLM Wiki) and DEC-0027 (public APIs + measurement
discipline).

**The Galaxy tools wrapper is a substantial integration surface.** `galaxy-bridge` exposes 8,000+ external
bioinformatics tools through a single Python skill via BioBlend. This is exactly the kind of `external_api_tool`
deployment surface DEC-0046 describes — a Linus tool that fans out to a third-party server, with the tool registry
tagging it as external-API-deployed and the audit log capturing every invocation. Whether Linus extracts ClawBio's
specific implementation or re-implements over BioBlend directly is a follow-up question; the pattern itself is
load-bearing. Cross-platform chaining examples in the README (Galaxy VEP → ClawBio PharmGx; Galaxy Kraken2 → ClawBio
metagenomics) are a working precedent for the model-prediction-edge data flow described in DEC-0048.

**The specialist-skill-as-Worker model is a worked example of the BFM synthesis's central framing.** The
biological-foundation-models synthesis frames specialists (DeepSeMS, Bacformer, AlphaFold, ESM) as Workers a generalist
LLM dispatches to. ClawBio implements exactly this at the skill-class layer rather than the model-class layer: each of
the 63 skills is a deterministic, versioned specialist invoked by the orchestrator (`bio-orchestrator/`) based on
file-type and keyword routing. The "one skill, one task, no improvisation" discipline (enforced by the SKILL-TEMPLATE
"## Scope" section) is the operational form of the synthesis's specialist-as-Worker stance. Worth surfacing in the BFM
synthesis if not already there.

**The Claude Code plugin marketplace shape is a Phase 5+ distribution channel.** ClawBio installs into Claude Code as
`/plugin marketplace add ClawBio/ClawBio` followed by `/plugin install clawbio`, after which all skills are
agent-routable commands. This is the same skill-distribution pattern Linus would use to ship its own skills to any
Claude Code user (Dan first; later, a wider audience if the skills surface goes commercial). The
skills-and-practices synthesis already flags Claude Code as the Maestro harness (DEC-0007); the plugin marketplace is
the paired distribution channel for skill bundles that should be visible to Claude Code without bundling them into
Linus's core. Worth surfacing as a Phase 5/7 distribution-channel option in the skills-and-practices synthesis.

**The Corpasome reference genome is the kind of demo dataset Linus might curate for its bio benchmark suite.** A
real, fully-open, CC0-licensed 30x WGS human genome (Manuel Corpas, doi:10.5281/zenodo.19297389) gives every skill a
realistic demo input that doesn't require synthetic data. Linus's bio benchmark suite (Phase 1+ work) needs an
analogous reference dataset for Dan's domain — likely a published _B. braunii_ assembly or one of Dan's LanzaTech
metagenomes, depending on what's CC-shareable.

**The SKILL.md conformance linter and 17-check checklist are a directly portable engineering pattern.**
`scripts/lint_skills.py` enforces YAML frontmatter completeness, required sections, ≥3 trigger keywords, ≥3 gotchas, a
safety disclaimer reference, the agent-boundary clause, demo data presence, test directory presence, and a
500-line ceiling on SKILL.md size. Linus's own SKILL.md template (whichever lineage it descends from — Anthropic's,
ClawBio's, bioSkills's, or a synthesis) should ship with an equivalent linter from day one. ADR seed candidate:
`_Seed: DEC-NNNN skill-md-conformance-linter_`.

## 4. What's inspiration only

The **RoboTerri Telegram/Discord conversational interface** is impressive engineering but out of Linus's scope — Dan
does not need a messaging-channel agent; Linus's surface is Claude Code, openclaw (Phase 5+), and a future native app
(Phase 8). The conversational-LLM-as-orchestrator-only pattern (LLM stays at the meta level, biological data
processing is local) is sound architectural advice and matches Linus's local-first stance, but the specific
Telegram/Discord adapters add nothing.

The **Genomebook synthetic-genetics sandbox** (compile fictional character "souls" to diploid genomes, score
compatibility, breed offspring) is a delightful demo of skill composition (Soul2DNA → GenomeMatch → Recombinator) but
not science Linus needs to do. It is a strong illustration of how a skill DAG can compose into a multi-step pipeline,
worth referencing when Linus designs its own skill-chaining contract, but not directly applicable.

The **drug-photo skill's vision-model loop** (Claude vision identifies a medication from a photo, then routes to the
PharmGx skill) is a clever multimodal pattern, but Linus's local-first Worker stack does not have a vision model in
the Phase 1–7 plan; this becomes interesting only if Phase 8's native app adds vision capability.

The **four-installer matrix** (Claude / Codex / Gemini / OpenClaw, each with format quirks) that bioSkills also has is
present in ClawBio's plugin shape, but Linus should standardize on one internal SKILL.md format and let the
orchestration layer adapt — the same advice from the bioSkills repo-note applies here.

## 5. What's incompatible or out of scope

ClawBio's domain is **human consumer-genomics + GWAS + clinical-genomics** — pharmacogenomics from 23andMe, polygenic
risk scores, ACMG variant classification, UK Biobank semantic search, methylation clocks. Dan's domain is **microbial
genomics + metagenomics + algal genome assembly + LanzaTech bioprocess metagenomics**. Of the 63 skills, perhaps 5–10
map directly to Dan's day-job (`claw-metagenomics`, `analyze-fasta`, `archaic-introgression`, parts of
`variant-annotation`, the Galaxy bridge); the rest are clinical / consumer-genomics outputs that don't fit Dan's
research workflow. The pharmacogenomics core (PharmGx, Drug Photo, NutriGx, ClinPGx) is the most polished part of
ClawBio and the least relevant to Linus.

The **Galaxy server dependency** is a real footprint cost — running Galaxy Bridge against `usegalaxy.org` requires
network access and a Galaxy API key, and self-hosting a Galaxy server is a substantial infrastructure commitment.
Linus's local-first stance treats Galaxy as opt-in per project, not a default dependency.

The **clinical-variant-reporter skill (ACMG/AMP)** is regulated-domain-adjacent; per DEC-0047 (biosecurity tier control
for generative biology), any skill that emits clinical-genomics outputs should be Tier B (explicit Dan sign-off per
invocation), not standard sandbox. ClawBio mitigates this with a mandatory "research and educational tool, not a
medical device" disclaimer in every report; Linus would need to enforce the same gate.

The **Apache 2.0 vs MIT licensing** of inputs (ESM++, scvi-tools, PyAging) and the heavy R/Bioconductor dependency
footprint of some skills (DESeq2 via the bioconductor-bridge skill) means a full ClawBio install is heavier than
Linus's `linus` conda env should carry. Per-project conda envs (or per-skill `uv venv`s per DEC-0024) are the right
boundary, not a single fat env.

## 6. Recommendation: **Study (with a high prior on later Adapt-as-skill-library-pattern)**

ClawBio is the closest existing precedent for what Linus's Phase 7 biology skill class should look like in working
form, but the specific skills don't map 1:1 to Dan's research needs. The recommendation is therefore **Study** of the
content with explicit **Adapt** of three patterns:

- **Reproducibility bundle as standard output** — every analysis emits `commands.sh` + `environment.yml` +
  `checksums.sha256` so a reviewer can reproduce in 30 seconds (ADR seed
  `_Seed: DEC-NNNN reproducibility-bundle-output-convention_`).
- **SKILL.md conformance linter** — port the 17-check checklist enforced via `scripts/lint_skills.py` to Linus's
  internal skill template, regardless of which skill-library upstream Linus chooses (ADR seed
  `_Seed: DEC-NNNN skill-md-conformance-linter_`).
- **Per-skill `allowed_extra_flags` allowlist + subprocess security filter (INT-001)** — the small but load-bearing
  security control in `clawbio.py` that filters extra arguments against a per-skill allowlist before
  subprocess invocation. Should be the default pattern in Linus's tool registry / agent spawner for any
  subprocess-invoked skill.

Concrete next step: in Phase 7 planning, run a side-by-side comparison of bioSkills (~438 skills, broad-but-shallow,
Anthropic-format, harness-installable) vs ClawBio (63 skills, deep-and-engineered, runtime-bundled, plugin-marketplace
distributed) and decide which lineage Linus inaugurates Phase 7 with — or, more likely, fork the engineering shape
from one and the breadth-of-content from the other. Independent of Linus, Dan can install ClawBio as a Claude Code
plugin today (`/plugin marketplace add ClawBio/ClawBio`) for any consumer-genomics analysis — there is no real cost
and the PharmGx + GWAS Lookup skills are immediately useful even outside Dan's research focus.

Cross-link to the relevant syntheses: `biological-foundation-models-synthesis.md` (specialist-skill-as-Worker
framing — DEC-0046, DEC-0048), `function-annotation-discovery-synthesis.md` (variant annotation, GWAS, clinical
databases as function-annotation-discovery instances), `skills-and-practices-synthesis.md` (Claude Code plugin
marketplace as Phase 5+ distribution channel), `entrepreneurship-synthesis.md` (DOI + Zenodo + slides as a
local-first bioinformatics commercial-surface precedent), and `repo-clusters/g9-bio.md` (primary cluster home).

## 7. Questions for Dan

1. **Which 5–10 ClawBio skills are most directly relevant to your metagenomics work?** A first pass picked
   `claw-metagenomics`, `analyze-fasta`, `archaic-introgression` (for ancient-DNA-like population work),
   `variant-annotation`, and `galaxy-bridge` as candidates. Are there others (e.g., `dnasp` for popgen, `clinpgx` if
   pharmacogenomics ever becomes adjacent, `ukb-navigator` for biobank-style queries against your own data) that
   should be in scope, or skills you'd expect to be in this list but aren't?

2. **Is the Galaxy tools wrapper feasible to extract or re-implement for Linus?** ClawBio's `galaxy-bridge` is built
   on BioBlend and exposes 8,000+ tools through a single skill. The integration is non-trivial (server URL, API key,
   workflow chaining), but the pattern (one Linus tool → many external tools) is exactly DEC-0046's
   `external_api_tool` deployment field. Should Linus extract ClawBio's `galaxy-bridge` skill and re-host it as a
   first-class Linus tool, or re-implement against BioBlend directly with Linus's tool-registry conventions?

3. **Should Linus adopt the reproducibility-bundle convention as a skill output requirement?** Every ClawBio analysis
   emits `commands.sh` + `environment.yml` + `checksums.sha256` alongside the markdown report. Adopting this for any
   Linus skill that produces a publishable artefact has a strong reproducibility argument and a small
   implementation cost. Worth promoting to a Linus convention with an ADR (seed flagged in §3 above), or kept as a
   per-skill optional output until Phase 7 lands?

4. **Is the Corpasome reference genome appropriate for Linus's bio benchmark?** ClawBio uses Manuel Corpas's CC0 30x
   WGS human genome as its standard demo input. Linus's analogous benchmark dataset for your domain would be a
   _B. braunii_ assembly (likely your own published Showa race-B work) or a LanzaTech metagenome subset, depending on
   what's CC-shareable. Would the Corpasome work as a generic-human-genome smoke-test alongside a microbial-domain
   benchmark, or does Linus want to stay strictly inside microbial/algal genomics?

5. **How does ClawBio's skill model compare to bioSkills in coverage and quality for your work?** Both are MIT-licensed
   bio-skill libraries. ClawBio: 63 skills, deeper per-skill engineering (tests + reproducibility bundle + benchmark
   scorer), narrower coverage (consumer/clinical human genomics). bioSkills: ~438 skills, broader coverage (full
   computational-biology spectrum including microbial, popgen, single-cell, structural), shallower per-skill (mostly
   SKILL.md + usage-guide + examples without tests). For Phase 7 inauguration, do you want depth-first (ClawBio
   shape, fewer skills, more polish), breadth-first (bioSkills shape, more skills, lighter), or a hybrid (port the
   ClawBio engineering shape and fill it with bioSkills-equivalent breadth tuned to your work)?

6. **The plugin-marketplace distribution channel for Linus skills.** ClawBio installs into Claude Code via
   `/plugin marketplace add ClawBio/ClawBio`. Should Linus eventually publish its own skill bundle to the Claude Code
   plugin marketplace as a Phase 5/7 distribution channel (separate from the Linus orchestration backend, which
   stays local), or keep all Linus skills bundled with the orchestration runtime and never independently
   distributable?

7. **The SKILL.md conformance linter as a Linus-wide convention.** ClawBio's `scripts/lint_skills.py` enforces a
   17-check checklist on every skill PR. The pattern generalizes beyond bio skills to any Linus skill (orchestration
   tools, KnowledgeBase queries, future fine-tune-deployment skills). Should Linus adopt a single conformance linter
   for all skills from day one (Phase 7 prep), or wait until the skill count justifies it and do an ad-hoc review
   per-skill in the meantime?

8. **The specialist-skill-as-Worker framing in working form.** The BFM synthesis frames specialists (Bacformer,
   DeepSeMS, AlphaFold) as Workers a generalist LLM dispatches to. ClawBio implements this at the skill-class layer,
   not the model-class layer — `bio-orchestrator` routes to the right deterministic skill based on file type and
   keywords, not to a different model. Is the right Phase 7 architecture for Linus a single agent spawner that
   dispatches to both kinds of Worker (deterministic skill _and_ specialist model) through a uniform interface, or
   two separate dispatch surfaces?
