# bioSkills (`GPTomics/bioSkills`)

## 1. Purpose and scope

bioSkills is a curated collection of **438 Anthropic-format Skills across 63 bioinformatics categories**, packaged so an
AI coding agent (Claude Code, Codex CLI, Gemini CLI, OpenClaw) can be primed with domain-correct code patterns, tool
choices, and idiomatic API usage before attempting a real bio task. Coverage runs the full computational-biology
spectrum — sequence I/O, alignment, variant calling, scRNA-seq, spatial transcriptomics, Hi-C, ATAC-seq, methylation,
proteomics, metabolomics, CRISPR screens, population genetics, GWAS causal inference, structural biology (ESMFold,
Chai-1), liquid biopsy, immunoinformatics, even ecological eDNA — plus 41 end-to-end workflow templates and a
clinical-biostatistics group for CDISC-style trial work. Of every repo in the collection this is the one most directly
fitted to Dan's biochemistry/genomics specialization, and the most plausible Phase 7 skills payload Linus could ship on
day one. MIT licensed.

## 2. Content overview

Each skill is a directory holding `SKILL.md` (YAML frontmatter: `name`, `description` with mandatory "Use when…" clause,
`tool_type`, `primary_tool`), a `usage-guide.md`, and an `examples/` folder. The frontmatter is exactly the Anthropic
Agent Skills standard — the Codex and Gemini installers transparently rewrite to the SDK convention
(`examples/`→`scripts/`, `usage-guide.md`→`references/`); the OpenClaw installer keeps the original layout and can
optionally inject dependency metadata. Every code block carries a `## Version Compatibility` header pinning reference
versions (e.g., BioPython 1.83+, scanpy 1.10+) and instructs the agent to introspect on `ImportError`/`AttributeError`
rather than retry blindly. Code is paired Python and R where both ecosystems matter (`single-cell/clustering` shows
Scanpy + Seurat side by side with a `Method Comparison` table). Skills cross-link via a `Related Skills` footer that
forms an implicit DAG. Heavy work shells out to system CLI (samtools, bcftools, BLAST+, minimap2, bedtools, MACS3,
IQ-TREE2, PLINK, FlashPCA2, ADMIXTURE…), so the skills assume a properly provisioned conda/Bioconda environment, not
in-process Python only. No skill calls a paid SaaS — NCBI/UniProt/STRINGdb/myvariant queries hit free public REST APIs,
and ML structure prediction defers to local ESMFold/Chai-1.

The Bio-Task Bench evaluation (`resources/bioskills_eval_20260328.pdf`) covers 33 tests across 10 domains (ChIP-seq,
spatial transcriptomics, proteomics, metabolomics, popgen, long-read, assembly, methylation, CRISPR screens, multi-omics
integration), split 17 Basic / 16 Intermediate. Headline numbers: Claude Code Sonnet 4.6 baseline 0.975 → 0.983 with
bioSkills (+0.008); Codex GPT 5.4-Mini baseline 0.935 → 0.984 with bioSkills (+0.049). Both Basic scores hit 0.999 with
skills loaded; Intermediate barely budges (0.964→0.966 / 0.966→0.967). The PDF says the test corpus has **426 skills**
while the README header now claims 438 — the repo grew between eval and last commit.

## 3. What's reusable in Linus

For Phase 7 ("Skills & Autonomy Graduation") this is essentially a drop-in payload for Dan's domain. The four installer
shell scripts already handle global vs project-scoped install, category subsetting
(`--categories "single-cell,variant-calling"`), update, validate, and uninstall — Linus's tool-registry layer can wrap
or directly call the OpenClaw installer (which preserves the SKILL.md format Linus would itself want to consume) without
rewriting any skill content. Three immediate Phase 1+ wins: (a) load `single-cell`, `differential-expression`,
`variant-calling`, `pathway-analysis`, and `clinical-databases` against Dan's KnowledgeBase corpus to test the
literature-intelligence entrepreneurial surface mentioned in the skills synthesis; (b) point Claude Code at bioSkills
now (independent of Linus's own dev) for everyday bench analysis — a free tools upgrade today; (c) treat bioSkills as
the gold-standard SKILL.md template when Linus authors its own skills (the version-compatibility block +
introspect-on-failure pattern is genuinely good engineering and worth copying for non-bio Linus skills too).

**Differentiation vs sibling Skills repos.** OmegaWiki (24 skills) and infranodus-skills (15) target broad
knowledge-graph and content workflows; openrouter-skills (8) is API-routing meta; AgenticResearchWiki (2) is
methodology. None of them sit in Dan's day job. The closest cousin is `scientific-agent-skills` from G8 (general
lab-science agent patterns) — but bioSkills is roughly an order of magnitude larger, **measurably evaluated** on a
published benchmark (Bio-Task Bench), and concretely tied to specific tool versions and pipelines Dan already uses.
Across the whole collection bioSkills is the only Skills repo that ships a third-party benchmark report. That alone
makes it the strongest Integrate candidate in G9 and arguably across all five Skills-format repos.

## 4. What's inspiration only

The four-harness installer matrix (Claude / Codex / Gemini / OpenClaw, each with its own format quirks) is more
engineering than Linus needs in its own skills layer — Linus should standardize on one internal SKILL.md format and let
the orchestration layer adapt to whichever harness is calling. Adopt the bioSkills content, study the installer, but
don't replicate four-way format-conversion machinery. The R/Bioconductor dependency footprint (DESeq2, edgeR, Seurat,
clusterProfiler, methylKit) is heavy and slow to provision; Linus shouldn't take an R dependency lightly — load the R-
flavored skills only into projects where R is already present.

## 5. What's incompatible or out of scope

The Bio-Task Bench Intermediate plateau (0.964→0.966 with skills) is a real and unflattering signal: skills give large
gains where the baseline is weak (Codex Basic +9.4 points) and trivial gains where the baseline is already near ceiling.
Most of the +0.049 overall Codex gain comes from cleaning up the Basic tier; the harder problems are not moved. Whether
the eval is saturated, whether Intermediate is actually hard enough, or whether SKILL.md context genuinely doesn't help
on multi-step pipelines is a question the report doesn't resolve. Out of scope for Linus: the clinical-trial / CDISC
SAS-import skills (irrelevant to Dan's research workflow) and the imaging-mass-cytometry / flow-cytometry groups
(interesting but no current data path). The 41 workflow templates assume Snakemake / Nextflow / Cromwell are installed
and configured — Linus should treat those as opt-in per project rather than global.

## 6. Recommendation: **Integrate**

Start using bioSkills via `./install-claude.sh --project <kb-or-research-repo>` against KnowledgeBase or a sequencing
analysis project this week — it costs nothing and upgrades current Claude Code behavior on real Dan tasks immediately.
For Linus proper: bake bioSkills into Phase 7 as the inaugural domain skills bundle (selective `--categories` install
keyed to the project type), and adopt the SKILL.md frontmatter conventions (version-compatibility block, "Use when…"
clause, primary_tool single-value rule, related-skills DAG) as the in-house Linus skill template. Re-run the Bio-Task
Bench against the chosen Phase 2a worker model (Qwen2.5-Coder, Mistral, eventual Linus fine-tune) to see whether the
+0.008 / +0.049 deltas hold for non-frontier models — if local-model Basic-tier gains track Codex's +9.4-point jump,
that is a strong argument for bundling skills with every Linus instance.

## 7. Questions for Dan

- **Bio-Task Bench Intermediate plateau.** Both agents land at 0.96–0.97 on Intermediate with or without skills. Read
  scientifically: is this an evaluator saturation problem (rubric too coarse), is Intermediate actually too easy, or
  does in-context skill priming genuinely fail to help on multi-step tasks where the bottleneck is judgment rather than
  API recall? The answer changes how aggressively Linus should bet on skills as an autonomy-graduation lever.
  _Partially resolved (see [answered-questions.md](../questions/answered-questions.md)): bioSkills adopted as Phase 7
  inaugural bundle with a pre-launch A/B measurement gate; if no measurable lift on judgment-heavy tasks, skills launch
  as opt-in rather than default-on (S30). Plateau mechanism remains an open empirical question._
- **Local-model amplification.** The biggest gain (+0.049) was on Codex 5.4-Mini, the weaker model. Hypothesis: smaller
  / local models benefit more from skill priming than Sonnet does. Worth running bioSkills against Qwen2.5-Coder-32B and
  a future Linus fine-tune on the same 33-test BTB to test this empirically before Phase 7?
  _Partially resolved (see [answered-questions.md](../questions/answered-questions.md)): S30 calls for re-running
  Bio-Task Bench against the chosen Phase 2a worker model (Qwen3) before Phase 7; local-model amplification hypothesis
  will be tested then._
- **Heavy CLI tool surface.** ~25 Bioconda CLIs (samtools, bcftools, MACS3, IQ-TREE2, PLINK, ADMIXTURE, Salmon, STAR,
  Bakta, BRAKER3, …) need to be present for the skills to actually run. Make this a single conda env Linus manages, or
  per-project, or document and let the user provision?
- **Single-cell coverage match.** The 14 single-cell skills cover scRNA-seq, scATAC, perturb-seq, lineage tracing
  (Cassiopeia), cell-cell communication (CellChat-style + MeboCost metabolite communication). Does this map onto the
  scRNA-seq workflows you actually run, or are there missing methods (e.g. specific batch-correction or trajectory tools
  you prefer) that we'd want to author additional skills for?
- **Entrepreneurial surface.** The skills synthesis flagged scientific-literature intelligence and bioinformatics
  pipeline documentation as Phase 1+ surfaces. bioSkills is essentially a working v0 of the second one. Worth reaching
  out to GPTomics (the maintainer) to compare notes, or keep this as private ammunition for the Linus-as-product story?
