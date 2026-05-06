# NIST Cybersecurity Framework v1.1

**Source:** NIST Cybersecurity Framework (NIST CSWP)  
**Date:** April 16, 2018  
**File:** ../../context/cybersecurity/NIST.CSWP.04162018.pdf  
**Relevance to Linus:** Provides foundational risk management structure applicable to local AI inference infrastructure protecting sensitive genomics data.

## Key concepts / frameworks

- **Five Core Functions**: Identify, Protect, Detect, Respond, Recover. These form a continuous cycle, not a linear path.
- **Framework Implementation Tiers** (1-4): Maturity levels reflecting organizational cybersecurity sophistication, from Partial/Reactive (Tier 1) to Adaptive/Risk-Informed (Tier 4).
- **Framework Profiles**: Outcomes-based approach allowing organizations to align cybersecurity activities with business drivers and risk tolerance.
- **Categories and Subcategories**: Detailed outcomes tied to each function, mapped to industry standards (ISO 27001, NIST SP 800-53).
- **Cyber Supply Chain Risk Management (CSRM)**: Expanded in v1.1; applies to third-party dependencies and vendor risk.
- **Privacy integration**: Recognizes privacy and civil liberties as part of the broader cybersecurity ecosystem.

## Directly applicable to Linus

- **Identify Function**: Asset inventory and categorization for Linus components (local models, inference server, KnowledgeBase, file storage) and critical data flows.
- **Protect Function**: Access controls, encryption, network segmentation for sensitive genomics datasets and model weights. Relevant for local-first data sovereignty.
- **Detect & Respond**: Continuous monitoring of model API access, anomalous queries, unauthorized data export attempts within the safe sandbox.
- **Supply chain focus**: Vendor assessment for any cloud storage, vector database, or external services (e.g., tokenizers, optional model serving infrastructure).
- **Tier 1 baseline**: Linus can meet Tier 1 or Tier 2 practices without formal enterprise structure; emphasize repeatable processes and risk assessment over bureaucracy.

## Not applicable

- Multi-organization coordination and government contractor requirements.
- Critical infrastructure sector-specific overlays (power grids, water systems).
- Compliance mandates for federal agencies; Linus is personal research infrastructure.
- Large-scale incident response orchestration across departments.
