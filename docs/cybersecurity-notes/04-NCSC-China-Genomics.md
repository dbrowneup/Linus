# NCSC Fact Sheet: China's Collection of Genomic and Healthcare Data

**Source:** National Counterintelligence and Security Center (NCSC)  
**Date:** February 2021  
**File:** ../../context/cybrowne/NCSC_China_Genomics_Fact_Sheet_2021revision20210203.pdf  
**Relevance to Linus:** Illustrates nation-state data sovereignty threats specific to genomics; justifies local-first, private infrastructure for sensitive bioinformatics pipelines and genetic/clinical datasets.

## Key concepts / frameworks

- **Genomic data as strategic commodity**: China prioritizes genomic/healthcare data acquisition as national-security-level resource for AI/precision medicine competitive advantage.
- **Dual legal and illegal channels**: Chinese firms leverage U.S. partnerships (low-cost sequencing, research collaborations) and cyber theft (Anthem breach, watering hole attacks).
- **Supply chain risk**: Chinese biotech firms (BGI) embedded in U.S. healthcare/research ecosystem, gaining direct access to patient genetic data and clinical trial results.
- **DNA as permanent PII**: Cannot be replaced like credit cards; loss exposes individuals to surveillance, genetic discrimination, extortion, and enables targeting of relatives.
- **Insider threat**: National Intelligence Law mandates Chinese companies share intelligence with state; no legal mechanism for U.S. firms to refuse data requests.

## Directly applicable to Linus

- **Data residency justification**: Linus runs locally on macOS to avoid cloud storage of proprietary genomics pipelines or personal bioinformatics data where foreign intelligence services operate.
- **Vendor avoidance**: Evaluate any cloud storage, sequencing service partner, or public genomics database for Chinese ownership/influence (BGI acquisition paths, government contracts).
- **Intellectual property protection**: Local model weights and fine-tuned bioinformatics models stay on Dan's hardware, not synced to Dropbox, GitHub (if private keys leak), or other SaaS.
- **Metadata leakage**: Query logs to public genomics APIs (NCBI, 1000 Genomes) reveal research direction; Linus local mode limits external surveillance of research interests.
- **Family privacy**: Genomic data in cloud systems exposes relatives to linkage attacks if Dan's data is breached; local-only storage limits exposure surface.

## Not applicable

- Nation-state counterintelligence operations and espionage tradecraft.
- U.S. federal procurement restrictions on Chinese biotech equipment/software.
- Legal remedies and civil suits against data thieves.
- Foreign policy and trade restrictions on genomics exports.
