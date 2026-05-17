# Cybersecurity Reference Notes for Linus

This directory contains structured synthesis of cybersecurity reference materials to support a rewrite of `docs/syntheses/security-synthesis.md`. Each note extracts key concepts, frameworks, and directly applicable guidance for Linus as a private, local AI assistant handling sensitive genomics data and proprietary bioinformatics pipelines.

## Sources and Key Themes

### 1. NIST Cybersecurity Framework v1.1
**File:** `01-NIST-Framework-v1.1.md`

Risk management foundation; five core functions (Identify, Protect, Detect, Respond, Recover) organized as continuous cycles. Maturity tiers (1-4) and outcomes-based profiles. Directly applicable: organizational asset inventory, critical data flows, vendor risk assessment. Linus can target Tier 1-2 maturity without enterprise overhead.

**Key theme:** Scalable risk framework agnostic to organization size.

### 2. NIST SP 800-207: Zero Trust Architecture
**File:** `02-NIST-SP-800-207-ZeroTrust.md`

Paradigm shift from perimeter defense to per-transaction authentication and authorization. Policy Decision Points (PDP) centralize logic; Policy Enforcement Points (PEP) distribute enforcement. Micro-segmentation limits lateral movement. Directly applicable: model API request validation, session re-authentication, continuous monitoring of tool access.

**Key theme:** Trust is never implicit; every access attempt requires proof.

### 3. NIST SP 800-171 Rev.2: Protecting Controlled Unclassified Information
**File:** `03-NIST-SP-800-171r2-CUI.md`

Fourteen security requirement families covering Access Control, Audit, Configuration Management, Identification & Authentication, Incident Response, Physical Protection, etc. Tailored from federal standards for nonfederal organizations. Directly applicable: need-to-know access controls, comprehensive audit logging, integrity verification of model weights, endpoint encryption.

**Key theme:** Moderate confidentiality baseline achievable without federal contractor complexity.

### 4. NCSC Fact Sheet: China's Collection of Genomic and Healthcare Data
**File:** `04-NCSC-China-Genomics.md`

Nation-state data sovereignty threat specific to genomics. China prioritizes genetic/healthcare data acquisition via legal partnerships (low-cost biotech collaborations) and illegal cyber theft. DNA as permanent PII; loss exposes individuals to surveillance and enables targeting relatives. Directly applicable: local-first data residency justification, vendor/partner evaluation, metadata leakage awareness.

**Key theme:** Genomic data has unique national security implications; private infrastructure mitigates foreign intelligence access.

### 5. HHS/HPH Cyberthreats to Biotechnology
**File:** `05-HHS-Cyberthreats-Biotech.md`

Attack vectors common to healthcare and research infrastructure: phishing (themed on current events), RDP exploitation, watering-hole attacks, vulnerable supply-chain software, insider threats, remote work risks. Double-extortion ransomware targets exfiltrate sensitive data before encryption. Directly applicable: supply chain validation, malware scanning of transferred sequencer output, offline backup strategy, USB device hygiene.

**Key theme:** Healthcare and biotech sectors face high-velocity, high-impact ransomware campaigns.

### 6. Foley Guidebook: Cybersecurity in Pharma, Biotech, and Medical Devices
**File:** `06-Foley-Biotech-IP-Confidentiality.md`

Intellectual property protection framework for trade secrets (formulas, clinical trial data, manufacturing processes). Emphasizes that reasonable secrecy measures are required to maintain trade secret status. Covers DTSA, UTSA, FDA device cybersecurity, breach cost dynamics ($300-400 per capita in healthcare/biotech). Directly applicable: trade secret documentation of proprietary pipelines, reasonable safeguards checklist, incident response procedures, third-party confidentiality agreements.

**Key theme:** Loss of secrecy = loss of legal IP protection; reasonable measures are not optional.

### 7. NIST NCCoE Virtual Workshop: Cybersecurity of Genomic Data
**File:** `07-NCCoE-Genomics-Workshop.md`

Genomics-specific threat landscape and supply chain risks. Includes practical guidance on genomic data classification, bioinformatics tool provenance, and regulatory intersections (HIPAA, FDA, NIH data sharing). DEFINE-ASSEMBLE-BUILD collaborative approach. Directly applicable: reference genome and variant database classification, tool integrity verification, audit trails for anomaly detection, secure data sharing with collaborators.

**Key theme:** Genomic data is both uniquely valuable and uniquely re-identifiable; supply chain integrity is critical.

### 8. NIST SP 800-160 Vol. 1: Systems Security Engineering
**File:** `08-NIST-SP-800-160v1.md`

Engineering-grounded reference framing security as an emergent system property. Provides the three-context framework (problem / solution / trustworthiness) and a taxonomy of 32 design principles (least privilege, secure defaults, minimized sharing, reduced complexity, reference monitor concept, defense-in-depth, isolation, accountability and traceability, secure failure and recovery, predicate permission). Directly applicable: Phase 2+ orchestration router designed against the reference monitor's three properties (tamper-proof, always invoked, small and analyzable); tool-registry entries instantiate least privilege + secure defaults; SAFETY.md additions name the principle they invoke; ARCHITECTURE.md security section organized by the three contexts.

**Key theme:** Security is engineered into the system, not bolted on; emergent-property thinking + principle-named controls beat ad-hoc additions.

### 9. Tom's Hardware: Cursor + Claude Deletes PocketOS Production Database
**File:** `09-tomshardware-cursor-claude-incident.md`

Primary-source incident report (Mark Tyson, 2026-04-27): Cursor running Claude Opus 4.6 deleted PocketOS's production database and all volume-level backups in a single Railway API call, in 9 seconds. Failure modes: autonomy without proportionate controls, blanket-scope CLI credentials across environments, backups colocated with primary, no second-pair-of-eyes on irreversible operations, platform actively marketing AI-coding-agent use without commensurate safety defaults. Directly applicable: empirical justification for the SAFETY.md `confirm-before-destructive` default, per-environment / per-resource token scoping in the Phase 2 tool registry, backup independence as a hard architectural rule, audit-log provenance for every destructive tool call.

**Key theme:** Real-world failure mode that demonstrates exactly the threat model the Linus sandbox layer and autonomy-tier graduation are designed to prevent.

### Supporting resources (index-only artifacts)

Two non-PDF artifacts in `context/cybersecurity/` accompany the NIST Cybersecurity Framework v1.1 (note 01) and are retained as reference material without standalone notes:

- **`2018-04-16_framework_v1.1_core1.xlsx`** — the NIST CSF v1.1 framework core in machine-readable form: Functions × Categories × Subcategories with informative references (NIST SP 800-53, ISO 27001, COBIT). Useful for any future mapping exercise that ties Linus controls to specific subcategory IDs (e.g., `PR.AC-1` for access control); the .md note 01 summarizes the framework, the .xlsx is the lookup table.
- **`cybersecurity_framework_v1-1_presentation.pptx`** — NIST's official briefing deck for v1.1, useful as a quick visual summary of the framework structure and v1.0-to-v1.1 deltas (CSRM expansion, privacy integration) for orienting a future reader without re-reading the full CSWP PDF.

Neither artifact warrants a standalone note; they are pointers from note 01.

## Cross-Cutting Themes for Linus Security Synthesis

1. **Data Sovereignty & Local-First Infrastructure**: Linus's private MacBook deployment mitigates nation-state data acquisition and cloud-service data-broker risks. Genomics and proprietary bioinformatics models are highest value.

2. **Zero Trust Principles Applied Locally**: Even local access should be authenticated per session. Model API calls, reference database queries, and output exports should all require re-authorization based on request context and observable device state.

3. **Supply Chain & Dependency Risk**: Model weights, bioinformatics tools, and reference genomes must be validated for integrity and traced to trusted sources. Malicious or compromised dependencies are the most plausible attack vector for a single-user research system.

4. **Trade Secret & IP Protection**: Proprietary pipelines and trained models stay local. Reasonable secrecy measures (encryption, access control, audit logging) are required to maintain trade secret status; loss of secrecy voids legal protection.

5. **Incident Response Readiness**: Offline backup strategy, audit log preservation, and procedures for detecting/containing data exfiltration or ransomware are essential. Genomic data has higher breach cost and reputational impact than typical software engineering.

6. **Regulatory Awareness Without Over-Compliance**: HIPAA applies only if Dan handles regulated PHI; FDA guidance applies if building diagnostic tools. Linus as research infrastructure avoids many healthcare-specific mandates but should be aware of them if future commercial or clinical deployments occur.

## Recommendations for Security Synthesis v2

1. Ground each threat model and control in actual Linus operational context (e.g., "Threat: Malicious model weight binary on PyPI → Control: Verify PyPI package signatures, pin versions, run isolated evaluation before deployment").

2. Define three risk tiers: **Research-Grade** (current Linus), **Enterprise-Grade** (if handling multiple users or collaborators), and **Medical-Compliance** (if clinical diagnostics).

3. Emphasize local-first privacy wins over perimeter security; differentiate from cloud-native architectures.

4. Map each NIST Framework function and NIST SP 800-171 requirement family to concrete Linus implementation (or explicitly mark as out-of-scope).

5. Include supply chain validation procedures (checksum verification, source authentication, minimal dependency footprint).

6. Provide incident response playbook skeleton (detection, containment, recovery, post-mortem).
