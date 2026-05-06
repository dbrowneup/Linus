# Foley Guidebook: Cybersecurity in Pharma, Biotech, and Medical Devices Industries

**Source:** Foley & Lardner LLP  
**Date:** Published guidance (no date)  
**File:** ../../context/cybersecurity/17mc3955cybersecuritywp.pdf  
**Relevance to Linus:** Practical framework for protecting intellectual property and confidential research data; guidance on trade secret law, regulatory compliance, and incident response applicable to personal bioinformatics and genomics research.

## Key concepts / frameworks

- **IP asset categories**: Pharmaceutical formulas, biotech patents, clinical trial data, medical device designs, manufacturing processes, genomic reference databases.
- **Trade secret protection**: Reasonable secrecy measures required; loss of secrecy = loss of legal protection. Harder to satisfy than patent filing.
- **Legislative landscape**: DTSA (Defend Trade Secrets Act), state UTSA, FDA device cybersecurity guidance, HIPAA Privacy Rule, Defend Trade Secrets Act.
- **Data breach cost dynamics**: Varies by industry; healthcare/biotech among highest ($402-$301 per capita). Costs driven by incident response, notification, regulatory fines, reputational harm.
- **Mitigation factors**: Incident response team, employee training, cyber insurance, data loss prevention (DLP), and secure software development reduce breach cost.

## Directly applicable to Linus

- **Trade secret definition**: Proprietary bioinformatics pipelines, custom genome assembly parameters, fine-tuned variant-calling models qualify as trade secrets if reasonable secrecy measures apply (local storage, encryption, access controls).
- **Reasonable safeguards checklist**: Linus should enforce (1) encrypted disk storage, (2) access control to model weights and reference genomes, (3) employee/collaborator confidentiality agreements (if sharing Linus output), (4) incident response procedures.
- **Reverse engineering risk**: Custom-trained models or adapted GATK workflows can be reverse-engineered from outputs. Keep implementation details (hyperparameters, training data, architecture modifications) confidential.
- **Third-party handling**: If Dan collaborates with external researchers or sends analysis to colleagues, use secure transfer mechanisms (encrypted email, secure file-share) and require NDAs.
- **Incident response plan**: Document procedures for data exfiltration detection (unauthorized export attempts), containment (isolate Linus system), and notification (if personal/patient data involved).

## Not applicable

- FDA premarket device approval processes and post-market surveillance.
- HIPAA Breach Notification Rule (applies only if Dan handles regulated PHI).
- Multi-company IP litigation and damages calculation.
- Licensed drug development and patent prosecution.
