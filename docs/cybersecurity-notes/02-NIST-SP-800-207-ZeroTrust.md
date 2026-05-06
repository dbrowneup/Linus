# NIST SP 800-207: Zero Trust Architecture

**Source:** NIST Special Publication 800-207  
**Date:** August 2020  
**File:** ../../context/cybersecurity/NIST.SP.800-207.pdf  
**Relevance to Linus:** Zero trust principles directly apply to local AI orchestration: assume no implicit trust for local models, authenticate all tool requests, enforce least-privilege access to genomics data and model weights.

## Key concepts / frameworks

- **Zero Trust Tenets**: All resources (data, services, compute) are considered resources requiring authentication/authorization on per-session basis. No implicit trust from device location.
- **Policy Decision Point (PDP) and Policy Enforcement Point (PEP)**: Centralized authorization logic with distributed enforcement at each access attempt.
- **Dynamic Policy**: Access decisions include observable state (device characteristics, behavior, environment attributes) and client identity, not just static role.
- **Micro-segmentation**: Network and logical isolation so lateral movement is constrained after initial breach.
- **Continuous monitoring and validation**: Trust is re-evaluated on every transaction, not once per session.
- **Device agent and gateway models**: Variations of ZTA deployment (agent-based, enclave-based, resource portal-based).

## Directly applicable to Linus

- **Local model access pattern**: Every tool invocation to local inference server should validate requester identity (Dan's session), request authenticity, and data classification before passing to model.
- **Implicit trust zone elimination**: MacBook OS permissions alone are insufficient. Linus should not grant broad access to KnowledgeBase after one successful authentication.
- **Per-transaction policy**: Access to sensitive genomics pipelines, model weights, or private papers should re-check authorization on each request, with observable attributes (time, device state).
- **Prevent lateral movement**: Sandbox policy should restrict compromised models or malicious plugins from freely accessing all local resources.
- **Audit and evidence**: Every access decision logged with context (PDP decision rationale, PEP enforcement point, result).

## Not applicable

- Enterprise-wide ZTA migration strategies with 10,000+ devices.
- Cloud multi-tenant isolation and cross-organizational access.
- Federal zero trust conformance assessment frameworks.
- Hardware token and SmartCard requirements.
