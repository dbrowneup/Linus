# NIST NCCoE Virtual Workshop: Cybersecurity of Genomic Data

**Source:** National Cybersecurity Center of Excellence (NCCoE) / NIST  
**Date:** January 26, 2022  
**File:** ../../context/cybersecurity/genomics-workshop-allslides.pdf  
**Relevance to Linus:** Workshop synthesizing genomics-specific security challenges, including sensitive data handling, regulatory compliance (HIPAA, FDA), and practical threat landscape for research institutions and biotech companies.

## Key concepts / frameworks

- **Human genome basics**: 6.4 billion base pairs, inherited half from each parent, highly similar between individuals but unique identifiable signature. Once revealed, cannot be changed.
- **NCCoE approach**: DEFINE scope (industry pain points), ASSEMBLE teams (multidisciplinary), BUILD practical solutions. Collaboration with public and private stakeholders.
- **Genomic data threats**: Malicious access (espionage, competitive theft), inadvertent disclosure (misconfigured cloud storage, email misfiling), ransomware against research institutes.
- **Regulatory landscape intersect**: HIPAA (if PHI), FDA guidance (medical devices using genomic analysis), state privacy laws, NIH data sharing requirements.
- **Supply chain vectors**: Contaminated reference genomes, compromised bioinformatics tools, untrusted sequencing service providers.

## Directly applicable to Linus

- **Data classification**: Treat locally stored reference genomes, custom variant databases, and training data as confidential intellectual property or PII if tied to individuals.
- **Tool provenance**: Verify integrity of bioinformatics software (GATK, SAMTOOLS, VCFTOOLS, custom Python scripts). Download from official repositories (GitHub, official releases) with checksum validation.
- **Local-first advantage**: Linus keeps genomic datasets and analysis results on local hardware, reducing exposure to cloud data-center breaches or regulatory compliance scope creep.
- **Audit trail**: Log all model access to reference databases, variant calls, and output exports. Detect anomalies (bulk downloads, unusual queries, off-hours access).
- **Collaboration security**: If sharing genomic analysis outputs with colleagues, document data handling agreements and enforce encryption in transit (HTTPS, PGP, S/MIME).

## Not applicable

- Large biobank governance and multi-institution data-sharing agreements.
- FDA approval pathways for genomic-based diagnostic tests or therapeutic claims.
- IRB (Institutional Review Board) protocols and human-subjects research compliance.
- Population-scale genomics databases and privacy-preserving query architectures.
