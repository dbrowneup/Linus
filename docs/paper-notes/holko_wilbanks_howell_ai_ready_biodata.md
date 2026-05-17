---
title: "AI-Ready Biodata Is America's Next Strategic Infrastructure"
source: War on the Rocks (Cogs of War column), https://warontherocks.com/cogs-of-war/ai-ready-biodata-is-americas-next-strategic-infrastructure/
authors: Michelle Holko, John Wilbanks, Sam Howell
affiliation: Computercraft Corporation + CNAS (Holko); independent (Wilbanks; formerly Broad Institute Terra, Sage Bionetworks); CNAS Technology and National Security Program (Howell)
date: 2026-03-09
pdf: ../../context/notes/AI-Ready-Biodata-Is-Americas-Next-Strategic-Infrastructure.pdf
tags:
  [
    policy-brief,
    ai-bio-nexus,
    biodata-sovereignty,
    national-security,
    nccoe,
    nscb-2025,
    china-biotech,
    genebank,
    federated-learning,
    compute-to-data,
    biosecurity,
    entrepreneurship-context,
    group-policy,
  ]
---

# AI-Ready Biodata Is America's Next Strategic Infrastructure

## TL;DR

A March 2026 War-on-the-Rocks Cogs-of-War commentary by three deeply credentialed authors — Holko (former White House PIF, DARPA, NIH, BARDA, DHS CISA, NSCB advisor), Wilbanks (founder of Incellico, ran Sage Bionetworks, led product for Terra at the Broad Institute), and Howell (CNAS biotech/quantum policy) — arguing that the binding constraint on U.S. AI-bio leadership is not compute, talent, or capital but **biodata**: large, representative, interoperable, secure biological datasets engineered for AI training. The piece frames biodata as critical national infrastructure analogous to semiconductors or critical minerals, citing the 2025 final report of the National Security Commission on Emerging Biotechnology ("dominance in biotechnology will hinge on who controls the most complete, accurate, and secure biological datasets") and arguing the U.S. has a roughly three-year window. The China comparison is the load-bearing geopolitical argument: China National GeneBank DataBase plus integrated CAR-T / non-invasive-prenatal-testing / multi-omics ecosystems plus state-directed coordination across biotech + big data + AI under directed planning. The U.S. comparison is the load-bearing structural argument: world-class repositories (GenBank, SRA, dbGaP at NCBI) but built for archival access and scientific openness rather than AI-native optimization, with governance, interoperability, and commercialization distributed across agencies, universities, private actors. Four U.S. challenges are named (diversity, quality, interoperability, security); five policy recommendations are made (treat biodata as critical national infrastructure; build a secure national compute-to-data portal; convert NDAA pilots to binding national standards; align the Genesis Mission EO with biodata generation; sustain tens-of-billions-over-a-decade investment). For Linus, this piece is the **clearest 2026 policy framing of the biodata-sovereignty thread** that underlies Phase 7 (biology skills) and the Phase 8 hybrid-graduation pattern (where Linus moves from text-based memory to model-weight consolidation, and so where Dan's KnowledgeBase + paper corpus + experimental notebooks become the seed for fine-tuned Linus-specific biology models). The cybersecurity-notes folder (`docs/cybersecurity-notes/`) already captures the regulatory side (NIST CSF, SP 800-207 Zero Trust, SP 800-171r2 CUI, NCSC China genomics advisory, HHS cyberthreats brief, Foley biotech IP, NCCoE genomics-cyber workshop); this commentary is the **strategic-policy companion** that motivates why those regulations matter.

## The problem (in plain language)

The piece frames a tightening triangle. **AI scales with data** — generative models, language models, foundation models all show power-law scaling in capability with training data size, and biological data is the lever for biotech-specific foundation models. **Biotechnology is the next national-power axis** — NSCB 2025 explicitly identifies biotech as a critical domain of geopolitical competition, the U.S. requested ~$27B in biodefense-related FY2026 spending, and the domestic bioeconomy supports ~$830B in annual economic impact. **The U.S. biodata environment is the binding constraint** — world-class repositories exist (GenBank, Sequence Read Archive, dbGaP via NCBI; the U.S. is a global open-science leader), but the data is fragmented, not engineered for AI optimization, lacks consistent provenance and metadata standards, and is not coordinated for industrial translation.

The China comparison is the catalyst. The China National GeneBank DataBase aggregates multi-omics data under a unified national framework with cloud computing and bioinformatics tools, supported by state-directed coordination across biotech + big data + AI. BGI Group runs large-scale sequencing platforms. The non-invasive-prenatal-testing market was ~$608M in 2023 and is projected to exceed $1B by decade end, all integrated with hospital networks, clinical care, research, and industry. CAR-T cell therapy approvals and clinical biomanufacturing capacity are growing. The point isn't replication — the authors are explicit that China's centralization has weaknesses (quality-control challenges from rapid scaling, cross-border data-transfer restrictions, centralization-driven cybersecurity risk) — but recognition that **coordination, not just innovation, determines AI-bio leadership.**

The piece's structural framing of the U.S. challenges is unusually clean:

- **Diversity** (foundational genomic datasets overrepresent European ancestry — AI models underperform in diverse populations);
- **Quality** (heterogeneous collection conditions, missing metadata, batch effects degrade downstream analytical performance);
- **Interoperability** (different formats and ontologies across repositories, integration tax before AI deployment);
- **Security** (aggregated biodata creates high-value cyber/insider targets; fragmentation doesn't eliminate risk, just diffuses accountability).

Most U.S. biodata, the authors observe, was not designed for AI. ChatGPT and AlphaFold trained primarily on "found" data — readily available, not intentionally structured for model optimization. Open science has been a U.S. strength but reflects inconsistencies in collection, documentation, context. Without deliberate curation, shared standards, and AI-native architecture, models risk amplifying noise rather than extracting biological signal.

## What they propose

Five concrete recommendations form the actionable substrate of the piece:

1. **Treat biodata as critical national infrastructure.** Congress directs DOE in coordination with NIST, NIH, and domain-relevant agencies to fund AI-ready biodata commissioning: large, longitudinal datasets; standardized metadata; provenance tracking; shared security classifications; sustained maintenance. The argument: private firms invest in proprietary, short-horizon, commercially monetizable datasets, leaving gaps in longitudinal, cross-sector, and public-interest data. Public investment is "the substrate that makes private innovation scalable and transferable."

2. **Build a secure national compute-to-data portal.** A federated portal allowing vetted users to bring algorithms to sensitive datasets, using privacy-preserving machine learning, differential privacy, continuous monitoring. The framing: algorithms move; data stays in controlled environments. The authors caveat this requires sustained investment in technology infrastructure, governance, auditing, user vetting to avoid becoming new bottlenecks.

3. **Convert NDAA pilots into binding national standards.** Section 244/245 of the FY26 NDAA pilots become standards. OSTP and NIST, with DOE/NIH/mission agencies, define baseline biodata metadata, provenance, and security standards as conditions of federal funding. Compliance is enforced via procurement rules, grant and contract requirements, and data-sharing eligibility — not regulation alone.

4. **Align the Genesis Mission EO with biodata generation.** The recent Genesis executive order signals awareness of AI-accelerated science. The authors argue it risks scaling fragmentation if not paired with coordinated biodata generation; NIST plus domain agencies should spearhead federal automation for standardized, AI-ready datasets, secure measurement systems, continuous data pipelines feeding model training.

5. **Sustained investment at the scale of tens of billions over a decade.** Compared to the ~$27B FY2026 biodefense request and the ~$830B annual bioeconomy impact, this is "not extraordinary in context." The choice is between losing AI-bio leadership and engineering coordinated investment with security and access controls.

The piece also surfaces the dual-use tension explicitly: biology is inherently dual-use, the same datasets that accelerate vaccines / industrial enzymes / climate-resilient crops can lower barriers to harmful biological design if misused. Aggregated biological datasets become high-value cyber and insider targets. A national biodata strategy must pair coordination with **compute-to-data controls, auditability, red-teaming, and tiered access frameworks** — explicitly invoking the same vocabulary the Linus DEC-0047 biosecurity-tier framework adopts.

## Key takeaways for Linus

The piece is policy commentary, not a research paper, so the "key results" frame doesn't apply. The substantive yield is **three calibration points** for Linus's strategic posture:

**Calibration 1: biodata sovereignty is the underlying motivation for Phase 7+ biology skills, not just a technical convenience.** Linus's Phase 7 biology roadmap ([`biology-phase7-roadmap.md`](../specs/biology-phase7-roadmap.md)) and DEC-0047 biosecurity tiering already commit to local-first processing of biological data. This commentary supplies the **strategic framing**: the binding constraint on AI-bio leadership is data quality, integration, and security; Linus's local-first architecture is aligned with the policy direction the field is moving toward. The Phase 7 biology skills are not a bet on a niche; they're a bet on the structurally-correct stack for the next decade of AI-bio.

**Calibration 2: compute-to-data is the right architectural primitive.** Recommendation 2 (a secure national compute-to-data portal) is the same architectural pattern Linus's local-first Workers implement at small scale: algorithms move to data, data stays in controlled environments. The MemGPT / Letta / Hope precedents at the model-internal level (memory tiering with controlled access) have the same shape at the dataset level. For Linus's Phase 3 multi-agent spawner (DEC-0050) and Phase 4 data-sovereignty work, this argues for **compute-to-data as a first-class deployment pattern** — Linus Workers can be sent to datasets they don't own, with the dataset owner controlling what algorithms run.

**Calibration 3: the Linus "biodata sovereignty" thread for the entrepreneurship synthesis is not speculative.** The entrepreneurship synthesis already names a biodata-sovereignty angle (per the Tier 1-3 framing); this commentary is the strongest 2026 policy substrate for it. The argument for Linus's commercial positioning: if NSCB 2025's three-year window is accurate, and the policy direction is biodata coordination with tiered access + compute-to-data + auditability + red-teaming, then **a local-first AI assistant that operates on private domain data with full auditability** is positioned to ride the policy wave. The competitive position is structural: hosted Claude can't credibly meet the auditability + tiered-access + private-data requirements that the policy framework will impose on biotech.

## What's reusable in Linus

**Entrepreneurship-synthesis biodata-sovereignty thread.** This piece is the **primary citation** for the biodata-sovereignty angle in [`../syntheses/entrepreneurship-synthesis.md`](../syntheses/entrepreneurship-synthesis.md). It links the NSCB 2025 strategic framing to the U.S. policy stack (Genesis EO, NDAA Sections 244-245, OSTP/NIST coordination), giving the Linus entrepreneurship synthesis a defensible strategic argument: "Linus's local-first auditable architecture is aligned with the direction U.S. biodata policy is going." The fold-in is a paragraph-length addition to the Canteen / Agora signal section, with explicit citation.

**Phase 4 — data-sovereignty work justification.** Phase 4 ("Data Sovereignty") in ROADMAP.md commits to Kiwix, ProtoMaps/OSM, versioned datasets. This piece supplies the **biodata extension**: Phase 4 should also include a Linus integration of NCBI's GenBank/SRA/dbGaP, with the local-first architecture and auditable algorithm-to-data pattern that the commentary's Recommendation 2 envisions for the national compute-to-data portal. The Phase 4 spec should reference Recommendation 2 explicitly.

**DEC-0047 biosecurity-tier framework — strategic anchor.** DEC-0047's biosecurity-tier framework (Tier 1 read-only knowledge through Tier 4+ pathogenic-design gating) maps cleanly onto the commentary's "tiered access frameworks." The fold-in adds a citation to NSCB 2025 and to this commentary as the **strategic-policy substrate** for the tier framework, rather than presenting DEC-0047 as a Linus-internal invention.

**Phase 7 biology skills — calibration toward auditable typed-structured-prediction.** The commentary's emphasis on auditability + provenance + tiered access reinforces the S25 typed-structured-prediction convention. Every Phase 7 biology skill's output should be auditable — input data, model version, prediction, rationale, source citations. The Phase 7 roadmap should explicitly note this commentary as a motivation for the typed-structured-prediction discipline.

**Cybersecurity-notes folder cross-reference.** The existing [`docs/cybersecurity-notes/`](../cybersecurity-notes/) folder (NIST CSF, SP 800-207 Zero Trust, SP 800-171r2 CUI, NCSC China advisory, HHS cyberthreats, Foley IP brief, NCCoE genomics workshop, NIST SP 800-160v1) is the regulatory companion to this strategic-policy commentary. The commentary names the regulatory frameworks the cybersecurity notes summarize and adds the strategic-policy motivation for why those frameworks matter. The fold-in is a one-line cross-reference in each direction.

## What's NOT applicable / hype filter

**This is policy commentary, not a research paper or technical spec.** The piece makes strategic arguments and policy recommendations; it does not provide implementation specifications, technical benchmarks, or experimental results. Linus's adoption should treat it as **calibration for strategic posture**, not as a source of implementation patterns. The Phase 4 data-sovereignty work, the Phase 7 biology skills, and the DEC-0047 biosecurity tiering are all already specified at the implementation level; this commentary motivates them at the strategic level.

**The three-year window claim is the authors' framing, not an independent assessment.** The NSCB 2025 final report's three-year window for the U.S. to reassert biotech leadership is a strong claim that the authors cite uncritically. Linus's strategic posture should not over-index on the specific three-year timeline; the structural argument (biodata coordination is binding) holds at any reasonable timeline.

**The U.S.-vs-China framing is sharp and politicized.** The commentary is in War on the Rocks (Cogs of War column), a national-security-and-defense outlet. The framing is appropriate for the venue and the audience, but Linus's documentation should not adopt the same framing wholesale. The substantive claims (biodata is the binding constraint, coordination matters, dual-use risk is real) are independent of the China-competition framing.

**No specific implementation guidance for compute-to-data.** Recommendation 2 (secure national compute-to-data portal with privacy-preserving ML, differential privacy, continuous monitoring) is a desired property, not a recipe. Linus's Phase 4 implementation work needs separate technical specifications for: which federated learning protocol; which differential-privacy noise mechanism; which auditing log format. The NCCoE genomics-cyber workshop notes (in `docs/cybersecurity-notes/07-NCCoE-Genomics-Workshop.md`) are closer to actionable.

## Connections

The primary fold is into [`../syntheses/entrepreneurship-synthesis.md`](../syntheses/entrepreneurship-synthesis.md) under the biodata-sovereignty / Canteen-Agora-signal thread. The commentary is the 2026 strategic-policy substrate that motivates Linus's local-first auditable architecture as competitively differentiated.

The secondary fold is into [`../syntheses/biological-foundation-models-synthesis.md`](../syntheses/biological-foundation-models-synthesis.md) — the commentary's data-quality framing (diversity / quality / interoperability / security) maps directly onto the data-substrate challenges that biological-foundation-model training faces. The synthesis can cite this commentary as the policy-side companion to its technical discussion.

Cross-links to existing documents that share concerns:

- [`docs/cybersecurity-notes/04-NCSC-China-Genomics.md`](../cybersecurity-notes/04-NCSC-China-Genomics.md) — NCSC advisory on China + genomics data, the regulatory companion to this strategic commentary.
- [`docs/cybersecurity-notes/05-HHS-Cyberthreats-Biotech.md`](../cybersecurity-notes/05-HHS-Cyberthreats-Biotech.md) — HHS cyberthreats brief, the operational threat-model companion.
- [`docs/cybersecurity-notes/07-NCCoE-Genomics-Workshop.md`](../cybersecurity-notes/07-NCCoE-Genomics-Workshop.md) — NCCoE genomics-cyber workshop, the implementation-pattern companion.
- DEC-0047 biosecurity-tier-control — the Linus-internal biosecurity framework that maps onto the commentary's "tiered access frameworks" recommendation.
- [`../syntheses/safety-alignment-privacy-synthesis.md`](../syntheses/safety-alignment-privacy-synthesis.md) — the broader safety/privacy synthesis where biodata-sovereignty is a subset of the privacy thread.

Phase mapping: Phase 4 (data sovereignty — biodata integration, local-first GenBank/SRA, compute-to-data pattern); Phase 7 (biology skills — auditable typed-structured-prediction with provenance per recommendation 1's "standardized metadata; provenance tracking"); strategic posture — entrepreneurship synthesis's biodata-sovereignty thread.

## Open questions for Dan

1. **Position Linus's commercial-positioning narrative explicitly on biodata sovereignty?** The entrepreneurship synthesis names this as a Tier 1 commercial thread. This commentary is the strongest 2026 substrate for the narrative. Worth a session-summary-level write-up of "Linus and the biodata-sovereignty wave"?

2. **Phase 4 GenBank/SRA integration scope.** Phase 4 already commits to Kiwix and OSM. Should it explicitly include a biology-data layer: local-first GenBank or SRA replicas with compute-to-data semantics? The data volumes are large (SRA alone is ~50 petabytes) but a curated subset relevant to Dan's domain (Botryococcus, algae, metagenomics) is much smaller and tractable on a 1 TB external SSD.

3. **DEC-0047 biosecurity-tier framework — cite NSCB 2025 and this commentary as strategic substrate?** The current DEC-0047 framing is internally-motivated. Adding the NSCB 2025 + Holko/Wilbanks/Howell substrate gives DEC-0047 external policy alignment, which matters for any future credibility argument (e.g., government grants, biotech partner due diligence).

4. **Compute-to-data as a Phase 4 architectural primitive.** The commentary's Recommendation 2 (algorithms move; data stays controlled) is the architectural primitive that Linus's local-first Workers already implement at small scale. Should Phase 4 explicitly target "compute-to-data Worker dispatch" as a first-class deployment pattern, alongside the existing in-context Worker pattern?

5. **NSCB 2025 final report adoption in `context/notes/` or `context/papers/`.** The NSCB 2025 final report is heavily cited by this commentary. Not yet in the corpus. Should be a Phase 1 candidate add — it's the underlying primary source for both the strategic framing and the policy recommendations.

6. **Genesis Mission executive order — track or ignore?** The commentary frames the Genesis EO as a meaningful policy signal. For Linus's strategic posture, is the Genesis EO worth tracking as an evolving policy substrate (with periodic re-reads as implementation guidance lands), or treat as background context that doesn't materially affect Linus's roadmap?

7. **A "biodata-sovereignty" session summary?** This commentary plus the existing cybersecurity-notes plus DEC-0047 plus the entrepreneurship synthesis biodata thread are now substantial enough to warrant a session-summary-level write-up that consolidates the strategic posture. Worth scheduling as a 2026-05-Q3 or Q4 deliverable?
