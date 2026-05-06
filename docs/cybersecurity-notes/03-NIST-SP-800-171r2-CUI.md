# NIST SP 800-171 Rev.2: Protecting Controlled Unclassified Information

**Source:** NIST Special Publication 800-171 Revision 2  
**Date:** February 2020  
**File:** ../../context/cybersecurity/NIST.SP.800-171r2.pdf  
**Relevance to Linus:** Establishes 14 security requirement families (Access Control, Awareness & Training, Audit, etc.) adaptable to protecting proprietary genomics pipelines and sensitive scientific data resident in personal research infrastructure.

## Key concepts / frameworks

- **Controlled Unclassified Information (CUI)**: Non-classified federal data requiring safeguarding; NIST SP 800-171 provides minimum protections (confidentiality focus).
- **14 Security Requirement Families**: Access Control, Awareness & Training, Audit & Accountability, Configuration Management, Identification & Authentication, Incident Response, Maintenance, Media Protection, Personnel Security, Physical Protection, Risk Assessment, Security Assessment, System & Communications Protection, System & Information Integrity.
- **Basic vs. Derived Requirements**: Tailored from FIPS 200 and SP 800-53 baseline, eliminating uniquely federal controls.
- **Moderate Confidentiality Baseline**: Starting point; can be strengthened or loosened based on data classification and organizational constraints.
- **Security Domains**: Partitioning CUI processing/storage into logical isolation boundaries to limit exposure scope.

## Directly applicable to Linus

- **Access Control (AC)**: Discretionary access controls (DAC) + need-to-know for Linus tool execution. User Dan = only authorized subject; deny all other subjects access to model weights, KnowledgeBase.
- **Identification & Authentication (IA)**: Session-based identity verification; re-authenticate on sensitive operations (export genomics data, modify config).
- **Audit & Accountability (AU)**: Full logging of model API calls, data queries, weight/checkpoint access. Detect unauthorized export attempts, anomalous inference patterns.
- **System & Information Integrity (SI)**: Integrity verification of model checkpoints and KnowledgeBase corpus via checksums; detect supply-chain tampering in downloaded weights.
- **Physical Protection (PE)**: Disk encryption (FileVault on macOS); prevent physical theft of MacBook exposing unencrypted local data.
- **Configuration Management (CM)**: Version control of security-relevant configs (access policies, model serving settings) with change audit trails.

## Not applicable

- Federal contractor compliance and CUI marking workflows.
- Organizational multi-level security policies and segregation of duties across staff.
- Continuous Diagnostics & Mitigation (CDM) federal acquisition programs.
- Authorized federal information system authorization (FedRAMP-like) processes.
