# HHS/HPH Cyberthreats to Biotechnology

**Source:** Department of Health and Human Services / Health Public Health  
**Date:** March 2021  
**File:** ../../context/cybersecurity/hph-cyberthreats-to-biotechnology.pdf  
**Relevance to Linus:** Maps attack vectors (phishing, ransomware, IoT device compromise) relevant to local bioinformatics pipelines and distributed genomics analysis infrastructure.

## Key concepts / frameworks

- **Healthcare attack surface**: Connected medical devices (sequencers, analyzers), hospital networks, research lab infrastructure increasingly targeted for ransomware and data theft.
- **Common attack vectors**: Phishing (themed on COVID-19, payroll systems), RDP exploitation, watering-hole attacks, vulnerable supply-chain software (e.g., unsigned genomics pipeline tools).
- **Ransomware operators**: Double-extortion tactics: encrypt data and exfiltrate sensitive records (patient info, research data) before demanding payment.
- **Insider threat**: Disgruntled researchers, shared lab accounts, lack of proper access controls enable theft or sabotage of proprietary pipelines.
- **Remote work risks**: Unmanaged personal devices, home networks, and cloud file-sync tools increase lateral movement and data exfiltration risk.

## Directly applicable to Linus

- **Supply chain validation**: Any bioinformatics tool installed locally (WDL runners, GATK, custom scripts) should be from trusted sources with integrity verification. Avoid unsigned binary downloads from untrusted mirrors.
- **Phishing resilience**: Linus runs locally without email integration; reduces attack surface for credential harvesting targeting research accounts, but Dan must practice credential hygiene across accounts.
- **Ransomware isolation**: Local inference and data processing on macOS is harder to encrypt en masse than cloud workloads; single-point-of-failure is still disk encryption key.
- **Removable media policy**: Sequencer output transferred to Linus MacBook should be scanned for malware; USB drives from collaborative labs are potential infection vectors.
- **Backup strategy**: Offline backup of critical reference genomes and trained model weights (e.g., on external SSD stored separately) mitigates ransomware total-loss scenario.

## Not applicable

- Hospital incident response and patient notification protocols.
- FDA medical device regulations and cyber-physical system safety.
- Multi-facility enterprise ransomware response coordination.
- Regulatory breach notification timelines (HIPAA, state law).
