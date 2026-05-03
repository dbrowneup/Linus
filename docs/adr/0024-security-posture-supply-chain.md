## DEC-0024 — Security posture: hash-pinned linus env + uv-via-conda for disposable experimental envs + pip-audit response protocol

**Date:** 2026-05-03
**Status:** accepted

**Context.** The litellm supply chain incident demonstrated that supply chain attacks
on Python packages are real, subtle, and time-sensitive. The current linus env had
pre-emptive ML framework deps (langchain, langgraph, haystack-ai) that increased the
attack surface for zero current functionality. No hash-pinned lock file existed. No
documented response protocol for a CVE-flagged installed package.

**Decision.** **Layered architecture.** (1) The linus conda env is the production
substrate, with `requirements-locked.txt` generated via
`pip-compile --generate-hashes` (full hash pinning) and a monthly `pip-audit`
cadence + quarterly review for "do we need any deferred packages now?" (2) **uv is
installed via conda inside the linus env** as the disposable-env tool of choice;
**untrusted experimental packages always run in disposable uv envs**, never in the
linus conda env. (3) `pip-audit` CVE response: HIGH/CRITICAL = immediate triage →
patched-version availability check → if available, env rebuild + lock-file
regeneration; if not, evaluate removal vs. documented mitigation. Response protocol
written into SAFETY.md "Supply Chain Incident Response" section. Pre-emptive
framework deps removed; dep philosophy documented in CLAUDE.md.

**Consequence.** Supply chain attack surface bounded. Experimental work continues at
full speed inside disposable envs. Quarterly review prevents lock-file rot.
Incident response is documented before incident.
