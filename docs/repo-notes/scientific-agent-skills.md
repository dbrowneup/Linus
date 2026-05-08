# scientific-agent-skills (`K-Dense-AI/scientific-agent-skills`)

## 1. Purpose and scope

scientific-agent-skills is K-Dense's curated catalog of **135 Anthropic-format Agent Skills** spanning the full
scientific stack — bioinformatics, cheminformatics, proteomics, clinical research, medical imaging, materials science,
astronomy, quantum computing, geospatial/remote sensing, lab automation, scientific writing — plus a unified
`database-lookup` skill that fronts 78 public REST APIs (PubChem, ChEMBL, UniProt, COSMIC, ClinicalTrials.gov, NASA,
USGS, NIST, FRED, USPTO, SEC EDGAR, and dozens more). MIT-licensed at the repo level; each individual skill carries its
own `license` field in frontmatter (BSD/MIT/Apache typical for the Python wrappers, occasional GPL on a handful). The
repo was previously called "Claude Scientific Skills" and was renamed in 2026 to signal compliance with the open
[agentskills.io](https://agentskills.io/) standard, so the same SKILL.md tree now installs cleanly into Claude Code,
Cursor, Codex, Gemini CLI, and any other harness honoring the spec. For Linus this is the **broad-science sibling to
`bioSkills`** and the most direct external corpus for Phase 7 ("Skills & Autonomy Graduation"): hundreds of
already-written, already-scanned scientific skills targeting exactly the file format Linus's tool registry should speak.

## 2. Content overview

The repo is a flat directory `scientific-skills/` with 136 subdirectories (one is `bioskills-installer`-style machinery;
the headline 135 are SKILL.md-bearing). Each skill directory follows the Anthropic spec: a top-level `SKILL.md` with
YAML frontmatter (`name`, `description`, `license`, `metadata.skill-author`), prose "When to Use" and "Quick Start"
sections, code examples, and an optional `references/` folder with deep-dive markdown the agent loads on demand. Sampled
skills look uniformly clean: `scanpy/SKILL.md` is a tight scRNA-seq pipeline doc, `astropy/SKILL.md` covers
WCS/units/cosmology, `database-lookup/SKILL.md` is a 78-database router with a per-domain selection table. Domain
coverage by sub-count from the README: bioinformatics & genomics 21+, cheminformatics & drug discovery 10+, ML/AI 16+,
scientific communication 20+, data analysis & viz 16+, research methodology 12+, clinical 8+, materials/ physics/quantum
7, with smaller pockets in proteomics (matchms, pyOpenMS), neuroscience (Neuropixels), medical imaging (pydicom,
histolab, PathML), lab automation (PyLabRobot, Opentrons, Benchling), and one regulatory skill (ISO 13485). Notable
named skills outside the bio core: `pennylane`, `qiskit`, `cirq`, `qutip` (quantum), `pymatgen` (materials), `fluidsim`
(CFD), `geomaster` + `geopandas` (geospatial/remote sensing), `timesfm-forecasting` (Google's zero-shot foundation
model), `hugging-science` (curated catalog of HF scientific datasets/models across 17 domains), `modal` (cloud GPU
offload), and `optimize-for-gpu` (CuPy/cuDF/cuML/Warp). Install paths: `npx skills add` (cross-platform standard),
`gh skill install` (GitHub CLI v2.90+), or manual copy into the harness's skills directory. The companion **K-Dense BYOK
desktop app** is positioned as a free open-source AI co-scientist that consumes this skill set — but the skill repo
itself stands alone; the BYOK app is **not a runtime dependency** for using the skills inside Claude Code or any other
compliant harness. Security: every skill is scanned with Cisco AI Defense's Skill Scanner and the results are posted to
`SECURITY.md`; the repo authors flag that community contributions are reviewed but not exhaustively audited.

## 3. What's reusable in Linus

The whole catalog is reusable, with the same caveat that applies to `bioSkills`: Linus's Phase 7 needs to choose a tool
registry / skill format, and Anthropic's Agent Skills standard is the strongest candidate because (a) it's what Claude
Code already speaks, (b) it's becoming a multi-vendor standard, and (c) shipping skills can be vendored or symlinked
without writing code. For Dan specifically the high-value picks slot directly into the genomics/biochem workflow:
`scanpy`, `anndata`, `scvi-tools`, `scvelo`, `pydeseq2`, `pysam`, `tiledbvcf`, `gget`, `biopython`, `bioservices`,
`rdkit`, `datamol`, `deepchem`, `diffdock`, `molecular-dynamics`, `esm`, `database-lookup` (78 DBs in one wrapper),
`paper-lookup`, `bgpt-paper-search`, `pyzotero`, `citation-management`, and the writing/figure suite
(`scientific- writing`, `scientific-visualization`, `scientific-slides`, `markdown-mermaid-writing`). The KnowledgeBase
submodule already covers paper ingestion; `paper-lookup` and `bgpt-paper-search` complement that with live
PubMed/PMC/bioRxiv/ arXiv/OpenAlex/Crossref/Semantic Scholar/CORE/Unpaywall queries — exactly the gap Linus's tool layer
needs to fill.

**Comparison to bioSkills (G9, Integrate-recommended):** bioSkills (`pdarleyjr/bioSkills`) is a flat collection of ~438
narrowly-scoped bioinformatics skill directories — `alignment`, `atac-seq`, `chip-seq`, `clip-seq`, `causal- genomics`,
`differential-expression`, `comparative-genomics`, `ecological-genomics`, `epidemiological-genomics`, etc. The skill
granularity is _workflow-per-directory_ (one folder per analysis type, each with its own installer machinery).
scientific-agent-skills is _tool/database-per-directory_ with broader scope (78 DBs in one skill, one folder per Python
package or platform integration). They are **complementary, not redundant**: bioSkills is the "how do I run an ATAC-seq
analysis end-to-end" layer; scientific-agent-skills is the "how do I call RDKit / query ChEMBL / parse FITS / write a
poster" layer. A defensible Phase 7 plan is to install both with namespacing and let overlap resolve through skill
descriptions. The single hard duplicate to watch is the bio-database surface: bioSkills likely wraps the same
NCBI/Ensembl/UniProt endpoints that scientific-agent-skills wraps under `database-lookup` — pick one or accept the
redundancy.

**Comparison to OmegaWiki (24 skills):** OmegaWiki is general-purpose knowledge management; it does not overlap with
scientific-agent-skills functionally. Different problem space.

## 4. What's inspiration only

The **K-Dense BYOK desktop app** and the **K-Dense Web** SaaS upsell are not paths Linus follows — Linus is the
desktop-app equivalent for Dan, and the whole point is to keep inference local rather than paying for cloud GPUs and
shareable reports. Likewise, the README's repeated promotion of K-Dense Web as the "no-setup" version is marketing for a
hosted product that Linus is the alternative to. The `modal` skill (cloud GPU offload) is interesting as escape- hatch
infrastructure but conflicts with Linus's local-first stance and should not be installed by default. Some skills are
essentially documentation around proprietary platforms (`benchling-integration`, `dnanexus-integration`,
`latchbio-integration`, `omero-integration`, `adaptyv`, `ginkgo-cloud-lab`, `protocolsio-integration`,
`labarchive-integration`) — useful only if Dan actually uses those platforms; otherwise they're dead weight worth
pruning at install time per the README's own "do not install everything at once" advice.

## 5. What's incompatible or out of scope

The `optimize-for-gpu` skill is CUDA-centric (CuPy, Numba CUDA, cuDF, cuML, cuGraph, RAFT) and assumes an NVIDIA stack —
directly counter to Linus's no-CUDA constraint. It can stay installed for completeness but should be flagged as unusable
on M1 Max; an MLX/Metal-equivalent skill would need to be written separately. Some skills require Python 3.11+ (README
states 3.12+ recommended), which matches the `linus` conda env. `uv` is the assumed package manager for skill
dependencies — already installed in the linus env, so no friction. License heterogeneity at the per-skill level means
any "ship Linus with these skills bundled" plan needs an automated license-aggregation pass before redistribution (the
per-skill `license` frontmatter field is the right input).

## 6. Recommendation: **Integrate**

This is the broader-than-bio counterpart to `bioSkills` and should land in Linus the same way: as the seed catalog for
the Phase 7 skill registry. Concrete plan: in Phase 7a, vendor or symlink `scientific-skills/` under
`src/linus/skills/external/scientific-agent-skills/` (or use `gh skill install` against Linus's skills directory once
that exists), prune the cloud-platform integrations and `optimize-for-gpu` Dan won't use, document the bioSkills-vs-
scientific-agent-skills overlap policy in an ADR, and run a smoke-test by asking a worker model to execute one of the
README's example pipelines (single-cell scanpy → PyDESeq2 → STRING → KEGG) end-to-end against KnowledgeBase. If the
worker can chain three or four skills successfully, Phase 7 has its starting corpus and Linus's tool registry inherits
hundreds of pre-documented entry points without writing any of them from scratch.

## 7. Questions for Dan

1. **bioSkills vs. scientific-agent-skills overlap policy.** Both will install — bioSkills covers ~438 workflow skills,
   scientific-agent-skills covers 135 tool/database skills, and their bio-database surfaces overlap. Do we install both
   with namespacing (`bio/atac-seq`, `sci/scanpy`) and let agent skill-selection resolve, or do we curate a merged
   whitelist and drop duplicates manually before Phase 7 ships? _Partially resolved (see
   [answered-questions.md](../questions/answered-questions.md)): both adopted as Phase 7 inaugural bundle (~573 total);
   overlap policy and namespacing TBD in Phase 7a ADR (S30)._
2. **Cloud-platform skills.** Benchling, DNAnexus, LatchBio, OMERO, Modal, Adaptyv, Ginkgo Cloud Lab, Protocols.io,
   LabArchives — none of these match Dan's current workflow. Prune them at vendor time, or keep them installed in case
   future Dan needs them and let agent skill-selection ignore them?
3. **K-Dense BYOK desktop app.** It's a free open-source AI co-scientist that consumes these same skills with a chat UI
   bolted on. Worth a one-hour smoke-test as a reference implementation for what a "skills + chat" front-end looks like
   before Phase 5 (openclaw)? Or treat as competitive intel only?
4. **Security scanning.** scientific-agent-skills runs Cisco AI Defense's Skill Scanner weekly. Should Linus run the
   same scanner on every installed skill (vendored or otherwise) as part of CI, or trust the upstream scan results
   recorded in SECURITY.md?
