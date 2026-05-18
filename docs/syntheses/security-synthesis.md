# Linus — Security Synthesis

**Date:** 2026-05-08 **Author:** Claude (Maestro session, commissioned by Dan Browne) **Trigger:** litellm 1.82.8 supply
chain attack; genomics data sovereignty concerns; citation-traceability audit (2026-05-05) that rated the prior
synthesis Tier D.

_Sources: [NIST CSF v1.1](../cybersecurity-notes/01-NIST-Framework-v1.1.md) ·
[NIST SP 800-207 Zero Trust](../cybersecurity-notes/02-NIST-SP-800-207-ZeroTrust.md) ·
[NIST SP 800-171r2](../cybersecurity-notes/03-NIST-SP-800-171r2-CUI.md) ·
[NCSC China Genomics](../cybersecurity-notes/04-NCSC-China-Genomics.md) ·
[HHS Cyberthreats to Biotech](../cybersecurity-notes/05-HHS-Cyberthreats-Biotech.md) ·
[Foley Biotech IP Guide](../cybersecurity-notes/06-Foley-Biotech-IP-Confidentiality.md) ·
[NCCoE Genomics Workshop](../cybersecurity-notes/07-NCCoE-Genomics-Workshop.md) · DEC-0024_

---

## 1. Current Security Posture

### What exists

Linus's security story today lives almost entirely in SAFETY.md's autonomy tier model, and that model is genuinely
well-designed for what it addresses. The tiered permission system — read-only at Tier 0, sandboxed writes at Tier 1,
confirmation-required shell and network at Tier 2 — protects against Claude Code or a future Worker taking unintended
destructive actions. The blocklist explicitly protects `~/.ssh/`, `~/.aws/`, credential paths, and the keychain. The
audit log design is sound. The "autonomy is earned, not assumed" principle is the right default orientation.

The [NIST Cybersecurity Framework v1.1](../cybersecurity-notes/01-NIST-Framework-v1.1.md) organizes security into five
functions: **Identify** (know your assets and risks), **Protect** (access controls, encryption, dependency hygiene),
**Detect** (monitoring, anomaly detection), **Respond** (incident protocols), and **Recover** (backups, continuity).
Linus's current posture addresses parts of Protect (SAFETY.md sandbox, credential path blocklist, hash-pinned env per
DEC-0024) and Respond (Supply Chain Incident Response section in SAFETY.md, drafted 2026-05-03 per DEC-0024), with
Identify, Detect, and Recover still addressed only partially or not at all in a documented, repeatable way. The goal of
this synthesis is to close those gaps without adding enterprise overhead — a solo developer running research
infrastructure should target NIST CSF Tier 1-2, not Tier 4.

### What the current posture does NOT address

**Supply chain attacks.** SAFETY.md says nothing about the provenance of installed packages. The litellm incident is
precisely the class of threat that tiered autonomy cannot stop: the malicious code runs before any tool call, embedded
in a package that was installed days or weeks earlier. By the time Linus's sandbox decides whether to run `python`, the
attacker's payload has already had its chance.
[HHS research on biotech attack vectors](../cybersecurity-notes/05-HHS-Cyberthreats-Biotech.md) confirms that
supply-chain compromise through vulnerable dependencies is the most common initial access vector across healthcare and
research organizations.

**Prompt injection.** There is no mention of this attack class anywhere in SAFETY.md, DECISIONS.md, or CLAUDE.md. As
Linus ingests PDFs, notes, and web content into KnowledgeBase, and feeds that content to local models as context, the
surface for prompt injection grows with each paper added to the corpus.

**Dependency auditing.** The architecture is resolved (DEC-0024, 2026-05-03): hash-pinned `requirements-locked.txt`,
monthly `pip-audit`, and a Supply Chain Incident Response protocol in SAFETY.md. Implementation remains outstanding: the
lock file has not been generated and committed, and the CI gate is not yet wired.

**Network egress.** The design intends to be local-first, but the list of approved outbound connections in SAFETY.md
(HuggingFace, conda-forge, crates.io, CrossRef, PyPI) represents a meaningful attack surface. Any of these endpoints can
deliver a malicious payload during an install or model download.

**Genomics data sovereignty.** Dan works with proprietary genomics pipelines, raw sequencing data, and bioinformatics
corpora. These represent both intellectual property and, if tied to individuals, sensitive personal data. None of
SAFETY.md, ARCHITECTURE.md, or any existing planning document addresses the threat of foreign intelligence acquisition
of genomic data — a real and documented concern per the
[NCSC China Genomics Fact Sheet](../cybersecurity-notes/04-NCSC-China-Genomics.md) and the
[NCCoE Genomics Workshop](../cybersecurity-notes/07-NCCoE-Genomics-Workshop.md). (DEC-0053 added a first architectural
control — `hosted-ok` / `hosted-forbidden` KB flow tags — which addresses part of this gap.)

**Security testing.** There are no security tests in the codebase. `bandit` is not in `environment.yml`. No fuzzing, no
prompt injection test suite, no integration test that verifies the sandbox actually denies forbidden operations.

The honest summary: Linus has thoughtful operational safety controls (sandbox tiers, Supply Chain Incident Response, KB
flow policy per DEC-0053, biosecurity tiers per DEC-0047), and still-incomplete supply chain execution (lock file not
yet generated), limited input-integrity controls, and no security testing. The architecture for supply chain is decided;
the implementation is overdue.

---

## 2. Supply Chain Threat Model

### Current dependency surface

The `environment.yml` defines the following pip-installed packages, which carry the largest transitive dependency trees
and therefore the largest supply chain risk:

- **langchain / langgraph**: Extremely large dependency trees. LangChain pulls in dozens of packages, many of which are
  themselves large (pydantic, typing-extensions, httpx, aiohttp, tenacity, and more). LangChain has had its own CVEs.
  This is arguably the highest supply chain risk item in the file, compounded by the fact that it's listed for a "Phase
  3+ evaluation" that hasn't happened yet — meaning it's being installed before it's needed.

- **haystack-ai**: Large-ish dependency tree, actively maintained, but any haystack update can pull in transitive
  changes across its ML stack.

- **streamlit**: Moderate tree, widely used, but it includes a bundled web server and pulls in tornado, protobuf, and
  other components. Phase 2 target, so same concern as langchain — installed before it's active.

- **mlx-lm**: Smaller tree than the above, but directly interfaces with the inference stack. A compromised mlx-lm that
  exfiltrated model weights or modified outputs would be nearly invisible.

- **openai**: The official OpenAI Python SDK is widely used and relatively well-audited, but it is a network client; a
  compromised version could trivially exfiltrate API keys.

The conda channel packages (fastapi, uvicorn, pydantic, httpx, sqlalchemy, etc.) come from conda-forge, which has a
stronger review process than PyPI — but not immune. The pip-installed packages bypass conda-forge's review entirely.

### Credential exposure surface

If a compromised package runs during a `conda activate linus` or `python` call, it has access to:

- `~/.ssh/` — SSH private keys (GitHub, any server access)
- `~/.aws/` — AWS credentials (if Dan uses any AWS services for genomics data)
- `~/.config/gh/` — GitHub CLI token (full repo access, including private repos)
- Any `.env` files in the Linus tree or adjacent projects
- Anthropic API key (likely in a shell env var or `.env` file)
- Shell history (which may contain credentials passed as arguments)
- The KnowledgeBase submodule — Dan's private research corpus
- Genomics data if stored in the home directory or mounted volumes

The litellm attack specifically targeted SSH keys, AWS/GCP credentials, kubernetes configs, git credentials, API keys,
shell history, crypto wallets, SSL private keys, CI/CD secrets, and database passwords. Dan's exposure subset includes
SSH keys, GitHub token, Anthropic API key, and shell history — enough to cause serious damage. The
[HHS biotech cyberthreat guide](../cybersecurity-notes/05-HHS-Cyberthreats-Biotech.md) documents that double-extortion
ransomware in healthcare and research sectors exfiltrates sensitive data before encrypting it — meaning even a brief
compromise window can cause permanent damage.

### Recommended mitigations

The decided architecture is captured in [DEC-0024](../adr/0024-security-posture-supply-chain.md) (resolved 2026-05-03,
with Supply Chain Incident Response written into SAFETY.md and `uv`-disposable-env discipline now operational per
CLAUDE.md): (1) hash-pinned `requirements-locked.txt` generated by `pip-compile --generate-hashes`; (2) `uv`-based
disposable virtual envs for all experimental packages, never installed into the linus conda env; (3) monthly `pip-audit`
with a documented CVE response protocol. The implementation checklist:

**Immediate: audit the existing install.** Run `pip-audit` against the current linus environment. Fix any HIGH or
CRITICAL findings before continuing Phase 1 work. Estimated effort: 30 minutes including triage.

**Remove Phase 3+ dependencies from `environment.yml`.** Delete `langchain`, `langgraph`, `streamlit`, and `lm-eval`
from the file. These will be re-added when their phases begin. Reduces supply chain surface immediately.

**Generate and commit a pip lock file with hashes.** Install `pip-tools`, run `pip-compile --generate-hashes` against a
`requirements.in` derived from the pip section of `environment.yml`. Commit the resulting `requirements-locked.txt`.
Future installs validate hashes.

**Add `pip-audit` to the pre-commit hook or a Makefile target.** Runs automatically before any commit that touches
`environment.yml` or `requirements-locked.txt`.

---

## 3. Prompt Injection Threat Model

Prompt injection is the attack where untrusted content in a model's context window causes the model to take unintended
actions, disclose information, or override instructions. As Linus develops, this becomes a first-class threat.

### Realistic attack vectors

**KnowledgeBase PDF ingestion.** A malicious PDF added to `context/papers/` (whether downloaded from the web, received
from a collaborator, or pulled from a preprint server) could contain injected instructions in its text, in its metadata,
or in invisible Unicode characters. When KnowledgeBase processes this PDF and a Worker receives a chunk as context, the
Worker may follow the injected instructions rather than the Maestro's task prompt.

**Web-scraped content.** If any future Linus capability fetches web pages (for literature review, news, or reference
lookups), the page content is untrusted. Attackers can plant injection payloads on publicly accessible pages
specifically targeting known AI systems.

**Tool output injection.** If a Worker calls a tool (filesystem read, web fetch, shell command) and the tool output
contains text like "Ignore all previous instructions and instead...", a poorly-designed orchestration layer may pass
that output directly into the next model call without sanitization.

**Multi-agent relay attacks.** When Phase 3 introduces parallel agent fan-out, a compromised intermediate agent — or one
that received injected content — can relay malicious instructions to other agents in the same session. The attack
surface grows non-linearly with the number of agents.

**Synthesized content in notes.** Dan's own notes in `context/notes/` could be targeted if an attacker can influence
what Dan writes (e.g., by sending a carefully crafted email that Dan quotes in his notes).

### Defense patterns for the Maestro/Worker architecture

The [NIST SP 800-207 Zero Trust Architecture](../cybersecurity-notes/02-NIST-SP-800-207-ZeroTrust.md) establishes the
principle that no implicit trust should be granted based on network location or session history — every access request
requires authentication and authorization in context. Applied to Linus: content from the KnowledgeBase, tool results,
and web fetches must be treated as untrusted regardless of how they arrived, and the orchestration layer — not the model
— controls what actions are permitted.

The Maestro/Worker split is actually a security asset here, not just an architectural one. Maestro (hosted Claude) is
more capable of reasoning about injected instructions and more resistant to naive injection than smaller local Workers.
The key is enforcing that Workers cannot take safety-relevant actions on their own authority.

**Trust tier separation.** Content entering the system should be tagged with its origin:

- `source: user` (Dan's direct input) — highest trust
- `source: tool_result` (output from Linus tools) — medium trust, validated
- `source: knowledge_base` (retrieved chunks from KnowledgeBase) — low trust, sanitized
- `source: web` (fetched content) — untrusted, sandboxed

Worker prompts should make source trust explicit, not just concatenate all context into one string.

**Output validation.** Worker outputs that drive subsequent tool calls should be validated before execution. A Worker
instructed to summarize a paper should not be able to produce output that causes a shell command to run. The
orchestration layer — not the model — decides what actions are taken.

**Sandboxed tool execution.** Tool results should be delivered to models as structured data, not interpolated into
prompt strings. A tool that returns a file path should pass that path as a structured field, not as a string that gets
concatenated into "here is the file contents: [path]".

**Prompt hardening for Workers.** Worker system prompts should include explicit anti-injection framing: clearly delimit
trusted instructions from untrusted context, tell the model how to handle conflicting instructions, and instruct it to
refuse any action request that arrives via context rather than the task specification.

---

## 4. Genomics Data Sovereignty

This section addresses a threat class entirely absent from the prior synthesis: the security of Dan's genomics data,
proprietary bioinformatics pipelines, and trained models — not just as software artifacts, but as sensitive intellectual
property and potentially re-identifiable personal data.

### Why genomics data is different

The [NCSC China Genomics Fact Sheet](../cybersecurity-notes/04-NCSC-China-Genomics.md) documents that genomic data is
treated as a strategic national security asset by nation-state actors. Unlike passwords or credit card numbers, DNA
cannot be changed once exposed. A breach of genomic data exposes not just the individual but family members through
heritable markers, enables genetic discrimination and surveillance, and provides permanent leverage for targeted
operations. The [NCCoE Genomics Workshop](../cybersecurity-notes/07-NCCoE-Genomics-Workshop.md) confirms this risk
extends to research institutions and individual researchers: malicious access, inadvertent cloud disclosure, and
ransomware targeting genomics institutes are all documented vectors.

For Dan specifically, the data in scope includes:

- Reference genomes and custom variant databases (downloaded, curated, modified in-house)
- Raw sequencing datasets (FASTQ, BAM, VCF files) from _B. braunii_ and other organisms
- Metagenomic analysis outputs — potentially tied to commercial process development at LanzaTech
- Proprietary bioinformatics pipelines (assembly workflows, variant callers, annotation scripts)
- Fine-tuned Linus models trained on domain-specific corpora — these embody domain knowledge that took years to acquire

### Local-first as a sovereignty choice

Linus's local-first architecture is not primarily a cost or latency decision — it is a data sovereignty decision. The
[NCSC China Genomics Fact Sheet](../cybersecurity-notes/04-NCSC-China-Genomics.md) identifies cloud storage, SaaS
genomics platforms, and research collaborations with Chinese biotech firms as the primary vectors for nation-state
genomic data acquisition. Linus running on Dan's MacBook with data never leaving local storage eliminates those vectors
by design.

Concrete implications:

- **No cloud sync.** Genomics data, model weights, and KnowledgeBase content must not be synced to iCloud, Dropbox,
  Google Drive, or any other cloud storage. Time Machine backup (local) is acceptable; cloud backup services are not.
- **Research direction leakage.** Even metadata — what databases Dan queries, what species he sequences, what tools he
  runs — reveals research strategy. Linus's local inference avoids routing research queries through commercial LLM APIs
  that may log, train on, or share usage data.
- **Vendor hygiene.** Any external service that touches genomic data (sequencing providers, cloud analysis platforms,
  public API endpoints) warrants evaluation for data handling practices and organizational control.
- **KB → hosted-Maestro flow boundary.** When a critic-tier or fallback Worker runs on hosted Claude rather than local
  inference, the orchestration layer must not include proprietary genomics data in the context prefix. DEC-0053 resolves
  this with a `hosted-ok` / `hosted-forbidden` binary tag applied at KB ingest time: Dan's notes, LanzaTech data, and
  private correspondence default to `hosted-forbidden` and are stripped from any prefix sent to a hosted model. This is
  a sovereignty mechanism as much as a privacy mechanism — it enforces that research direction, pipeline details, and
  proprietary analysis results never leave local infrastructure even when hosted Maestro is in the loop.

### Tool provenance in bioinformatics

The [NCCoE Genomics Workshop](../cybersecurity-notes/07-NCCoE-Genomics-Workshop.md) specifically calls out
bioinformatics tool provenance as a supply chain vector: contaminated reference genomes, compromised tool binaries, and
untrusted sequencing service providers have all been documented attack paths. The recommendation — download only from
official repositories (GitHub releases, Bioconda, official project pages) with checksum validation — maps directly to
DEC-0024's dependency philosophy applied to bioinformatics tooling, not just Python packages.

The same logic extends to model weights: a quantized model downloaded from an unofficial source could embed a trojan
that activates on specific input patterns. Model integrity verification (SHA-256 of the `.gguf` or `.safetensors` file
against the official release manifest) should be a requirement before any model runs in Linus.

### IP and trade secret protection

The [Foley Biotech IP Guide](../cybersecurity-notes/06-Foley-Biotech-IP-Confidentiality.md) establishes a critical legal
point: trade secret status requires ongoing "reasonable measures" to protect secrecy. If Linus's proprietary pipelines
or fine-tuned models are exposed through inadequate access controls, the trade secret protection that might otherwise
apply evaporates. For Dan, reasonable measures include: local-only storage, encryption at rest of model weights and
pipeline code, audit logging of access, and documented confidentiality expectations for any collaborator who receives
analysis outputs. These are not bureaucratic formalities — they are what separates "proprietary bioinformatics pipeline"
from "thing anyone can use without attribution."

---

## 5. Other Relevant Attack Vectors

**Model extraction via the OpenAI-compatible endpoint.** Once Linus exposes an HTTP endpoint (Phase 2+), anyone who can
reach it on the local network can query it. On a personal laptop this is relatively contained, but cafes, conference
networks, and future infrastructure changes expand the exposure. The more immediately relevant concern is that a process
running on Dan's machine (malware, a compromised package) could query the Linus endpoint to extract information from the
model's context window, including any credentials or private research that are in the system prompt.

Mitigation: bind the Linus endpoint to `127.0.0.1` only, not `0.0.0.0`. Add an API key gate even for local traffic — it
keeps the bar non-trivial for any process that would need to impersonate a legitimate client. Document this in
ARCHITECTURE.md as a design constraint before the code exists.

**Data exfiltration via model outputs.** A local model receiving sensitive context (private research data, credentials
accidentally in the prompt) could have its outputs logged or forwarded by a malicious process. The model itself is not
the attacker here, but the infrastructure around it is.

**Malicious MCP tool registration.** MCP tools are dynamically registered capabilities. A malicious MCP server could
register tools with names that shadow legitimate ones (e.g., a tool named `read_file` that exfiltrates content before
returning it). The attack requires either a compromised MCP server or a confused orchestration layer that accepts tool
registrations from untrusted sources.

Mitigation: implement a tool allowlist (already planned in SAFETY.md's spirit) before adopting MCP. Every tool
registration should be an explicit, logged, Dan-approved event — not a dynamic handshake.

**Social engineering via synthesized knowledge base content.** If Linus's KnowledgeBase grows to include web-sourced
content or community contributions, an attacker could plant content that subtly influences Dan's research conclusions or
Linus's responses. This is low probability for a personal system but worth naming: the integrity of the knowledge base
is a security property, not just an accuracy property.

**Offline backup failure.** The
[HHS Cyberthreats to Biotech guide](../cybersecurity-notes/05-HHS-Cyberthreats-Biotech.md) documents that ransomware
campaigns in biotech and research sectors routinely delete or encrypt cloud-synced backups before triggering encryption
of primary data. An offline backup on a disconnected drive — a Time Machine backup that is disconnected between backups
— is the minimum viable protection against ransomware affecting Linus's data and model weights.

---

## 6. Recommended Security Improvements

Organized by the NIST CSF five functions ([NIST CSF v1.1](../cybersecurity-notes/01-NIST-Framework-v1.1.md)) and phased
to match Linus's roadmap.

### Identify — Know your assets and risks

1. **Asset inventory.** List everything Linus touches: conda env packages + transitive deps, model weights and their
   sources, KnowledgeBase files, genomics data directories, API keys and credentials in use. This is the precondition
   for everything below. Estimated effort: 2 hours.

2. **Threat prioritization.** The three highest-priority threats for a solo developer with genomics data: (a) supply
   chain compromise of Python packages, (b) accidental cloud sync of genomics data or model weights, (c) credential
   exposure from a compromised conda env. Everything else is lower priority at Phase 1.

### Protect — Control access and harden the environment

3. **Run `pip-audit` on the current linus env.** `pip install pip-audit && pip-audit`. Fix any HIGH or CRITICAL
   findings. Estimated effort: 30 minutes including triage.

4. **Remove Phase 3+ dependencies from `environment.yml`.** Delete `langchain`, `langgraph`, `streamlit`, and `lm-eval`.
   Reduces supply chain surface immediately. Estimated effort: 10 minutes.

5. **Generate and commit a pip lock file with hashes** per DEC-0024. Install `pip-tools`, run
   `pip-compile --generate-hashes`, commit `requirements-locked.txt`. Estimated effort: 1 hour.

6. **Bind the Linus HTTP endpoint to `127.0.0.1`.** Default in any server startup code written in Phase 2. Add it to
   ARCHITECTURE.md as a design constraint now. Estimated effort: 10 minutes of documentation.

7. **Verify no genomics data syncs to cloud.** Audit iCloud, Dropbox, and any other sync services. Ensure sequencing
   data directories and KnowledgeBase content are excluded. Estimated effort: 30 minutes.

8. **Verify model weight checksums on download.** Before any new model runs in Linus, verify the SHA-256 of the weight
   file against the official release manifest. Estimated effort: 5 minutes per model.

### Detect — Monitor for anomalies

9. **Add `pip-audit` to the pre-commit hook or a Makefile target.** Runs automatically before any commit touching
   `environment.yml` or `requirements-locked.txt`. Estimated effort: 30 minutes.

10. **Audit log for model access.** Phase 2 orchestration layer should log every model call: timestamp, caller, tool
    used, data classification of context. Enables anomaly detection (bulk exports, off-hours access). Design this in
    from day one.

### Respond — Document protocols before incidents

11. **CVE response protocol** per DEC-0024. HIGH/CRITICAL finding in `pip-audit` → immediate triage → check for patched
    version → if available, env rebuild + lock-file regeneration; if not, evaluate removal vs. documented mitigation.
    This is already decided; the implementation needs to be written into SAFETY.md explicitly.

12. **Ransomware response playbook.** Offline Time Machine backup on a disconnected drive. If ransomware suspected:
    disconnect from network, do not reboot, photograph the screen, contact backup before attempting recovery.

### Build into the MVP (Phase 2-3)

13. **Implement input trust tagging in the orchestration layer.** Every item entering a model's context window carries a
    `trust_level` field. The orchestration layer enforces that low-trust content cannot trigger tool calls without
    explicit Worker-specific handling. Design this into the context assembly pipeline from day one.

14. **Add an API key gate to the Linus endpoint.** Even a static key stored in a local `.env` file is meaningful
    friction for unauthorized local access. Generate it on first run, store it in `~/.linus/config.toml`, and require it
    for all API calls.

15. **Add `bandit` to the Python CI gate.** Catches Python anti-patterns: hardcoded credentials, insecure subprocess
    calls, weak crypto. Add it to the ruff/mypy/pytest gate in `pyproject.toml`.

16. **Implement prompt injection canaries in Workers.** Workers that receive KnowledgeBase content should include a
    sentinel phrase in their task prompts. The orchestration layer checks whether the sentinel appears in the output,
    and flags any response that contains instructions to ignore system prompts.

17. **Submodule KnowledgeBase SHA pinning enforcement.** Already planned; add a CI check that verifies the committed
    KnowledgeBase SHA matches the lock.

18. **Enforce `hosted-ok` / `hosted-forbidden` KB flow policy in Phase 3 ingest pipeline.** DEC-0053 (resolved
    2026-05-06) defines the binary tag; Phase 3 KB ingest pipeline must implement it at record creation time.
    Conservative default: all new records start `hosted-forbidden`; explicit upgrade required for published public
    content. Enforcement in the retrieval layer: strip `hosted-forbidden` items from any prefix assembled for a hosted
    Worker, regardless of retrieval ranking.

19. **Wire `biosecurity_tier` field into tool registry at Phase 7 biology skill onboarding.** DEC-0047 (resolved
    2026-05-06) defines three tiers (A: residue-level, B: gene-level with Dan sign-off, C: whole-genome with sign-off
    - out-of-band review). Tool registry entries for all biology-generative skills must include this field; Workers
      check it at dispatch time and enforce the appropriate gate. Tools missing the field should default to Tier A (the
      conservative fallback), with a logged warning.

### Phase 6+ — Advanced

20. **Adversarial prompt injection test suite.** Tools like `garak` (LLM vulnerability scanner) or manual test cases
    targeting the specific content types in KnowledgeBase. Run this whenever a new Worker model is adopted.

21. **SBOM generation and monitoring.** Generate a Software Bill of Materials using `cyclonedx-python` and track it over
    time. Integrate with OSV for ongoing monitoring.

22. **Network egress monitoring.** Use macOS's built-in `pf` or Little Snitch to alert on unexpected outbound
    connections from the linus conda env.

---

## 7. Security Testing Posture

The current posture is nonexistent. The minimum viable security testing infrastructure, in order of leverage:

**Dependency vulnerability scanning (highest leverage, lowest effort).** `pip-audit` catches known CVEs in installed
packages. It will not catch zero-days or novel supply chain attacks like the litellm incident, but it catches the long
tail of unpatched known vulnerabilities that are far more common. Add it to the Makefile and run it weekly.

**Static analysis with `bandit`.** Catches Python anti-patterns: use of `eval`, `exec`, subprocess with shell=True,
hardcoded credentials, use of insecure MD5. False positive rate is manageable with a small `pyproject.toml`
configuration. Run it in the same CI gate as ruff and mypy.

**Sandbox enforcement tests.** Unit tests that verify the orchestration layer actually denies forbidden operations. A
test that constructs a request to write to `~/.ssh/known_hosts` and asserts that the sandbox returns
`{status: "denied"}` is a regression test for the most important safety property. These should live in `tests/security/`
and run in every CI pass.

**Prompt injection smoke tests.** A minimal set of hand-crafted test prompts containing common injection payloads, run
against each Worker configuration on adoption. Not a comprehensive red team — just a sanity check that the obvious
attacks fail.

**What a Linus security CI gate should check:**

- `pip-audit` — no HIGH or CRITICAL unpatched vulnerabilities
- `bandit` — no HIGH severity findings (MEDIUM tolerated with explanation)
- `ruff` — already wired in
- `mypy` — already wired in
- Sandbox denial tests — 100% pass
- Lock file hash integrity — all pip hashes match committed lock file

---

## 8. Dependency Philosophy

The litellm incident, and Karpathy's observation that he increasingly prefers to implement functionality with LLMs
rather than take on a dependency, point to the same underlying principle: every dependency is a trust relationship, and
trust relationships have maintenance costs and attack surfaces. The
[HHS Cyberthreats to Biotech guide](../cybersecurity-notes/05-HHS-Cyberthreats-Biotech.md) confirms that supply-chain
software compromise is one of the primary biotech attack vectors precisely because research environments tend to install
many specialized packages with minimal vetting.

**High-risk, worth reconsidering:**

`langchain` and `langgraph` are the most concerning entries. They are being added for "Phase 3+ evaluation" but are not
yet in use. Their transitive dependency trees are enormous, their release cadence is fast (increasing the probability of
a supply chain event slipping through), and the core value they provide — agent state machines and tool orchestration —
is exactly what Linus is building as its core competency. Recommendation: remove them from `environment.yml` now,
evaluate honestly in Phase 3 whether they provide enough value over Linus's own orchestration primitives to justify
re-adding them.

`haystack-ai` is pulled in because KnowledgeBase uses it. The dependency is real but indirect — it should live in
KnowledgeBase's own `environment.yml`, not Linus's. Recommendation: remove from Linus's env, import KnowledgeBase via
the submodule's own editable install as originally planned.

**Medium-risk, monitor:**

`openai` (the SDK) is a network client by nature, but it is widely used, relatively well-audited, and the specific
functionality — OpenAI-compatible client calls — is not easily reimplemented without writing the HTTP calls yourself,
which is a different kind of risk. Keep it, but pin to a specific version with hash.

`mlx-lm` is the primary inference runtime. Its supply chain risk is real but its functionality is not easily
reimplemented. Keep it; pin it; watch it closely.

`streamlit` is a convenience chat UI for Phase 2. Worth asking whether a simpler static HTML frontend or a direct
integration with an existing UI (LM Studio, openclaw in Phase 5) serves the need without the dependency.

**Low-risk:**

`fastapi`, `uvicorn`, `pydantic`, `httpx`, `sqlalchemy`, `pytest`, `ruff`, `mypy` are all well-audited, heavily used in
production systems, and have large security researcher communities. They are not zero-risk but they are significantly
lower risk than the ML/agent libraries. Keep them, pin them, audit them, move on.

This dependency philosophy is now codified in CLAUDE.md under the "Dependency philosophy" convention. The core
principle: every dependency is a trust relationship with an ongoing maintenance cost and supply chain attack surface.
Prefer small, mature, general-purpose dependencies. Avoid AI/ML framework dependencies for orchestration logic — that
logic is Linus's core product. When in doubt, implement in controlled code rather than taking the dependency. See
[DEC-0024](../adr/0024-security-posture-supply-chain.md) for the architectural decision record.

---

## 9. Open Questions for Dan

**1. How much supply chain risk is acceptable, and at what cost?** Full hash pinning and lock files add meaningful
friction to the development workflow — every time a package is upgraded, the lock file must be regenerated and
committed. For a solo developer in rapid iteration, this may feel like it slows the wrong thing down. But it is the only
technical control that could have stopped the litellm attack. How does Dan want to balance iteration speed against
supply chain integrity? A middle path exists (audit monthly, hash-pin only at phase milestones) but it should be an
explicit choice.

**2. Should Linus ever run untrusted packages from the internet, and if so, how?** Experiments in `experiments/`
sometimes need unusual packages. Should these always run in isolated, disposable `uv` virtual environments that are
never activated alongside the linus conda env? Or is the conda env isolation sufficient? (DEC-0024 decided: uv envs. The
question is whether that's being followed in practice.)

**3. What is the threat model for the KnowledgeBase content?** Dan adds papers from arXiv, bioRxiv, and other sources.
Is the threat of a maliciously crafted PDF in that corpus realistic enough to warrant sanitization tooling (stripping
metadata, normalizing text before ingestion)? Or is the corpus trusted because Dan controls what enters it? The answer
determines how much engineering goes into KB ingestion security.

**4. When the OpenAI-compatible endpoint is exposed, who is allowed to query it?** Initially this is just Dan, via
localhost. But as Linus grows — if Dan runs it on a home server, or exposes it to mobile devices on his home network —
the attack surface changes. Is there a point at which Linus needs TLS and mutual authentication, or will it remain
strictly localhost-only?

**5. How should Linus handle a detected supply chain compromise?** If `pip-audit` reports a CVE in a currently-installed
package, what is the response protocol? (DEC-0024 sketches the answer; SAFETY.md should have it written out explicitly.)
Credential rotation as a precaution? Audit of recent session logs? A written response protocol, before an incident, is
orders of magnitude more likely to be executed correctly under stress than one improvised in the moment.

**6. How does Dan classify his genomics data for privacy purposes?** Reference genomes and published assemblies are
public. Custom variant calls and proprietary pipeline outputs are IP. If Dan ever handles data tied to individual human
subjects (clinical collaborations, direct-to-consumer datasets), HIPAA and IRB considerations activate. Knowing where
the line is determines which controls are legally required vs. best-practice-optional.

**7. What is the offline backup strategy for model weights and genomics data?** The local-first stance is the right
choice for sovereignty, but it means there is no cloud backup redundancy. A Time Machine backup that is physically
disconnected between backup runs is the minimum viable protection against both accidental deletion and ransomware. Is
this currently in place for the drive containing genomics data and model weights?

## References

_This synthesis draws on the NIST Cybersecurity Framework primers in
[`docs/cybersecurity-notes/`](../cybersecurity-notes/) and on [DEC-0024](../adr/0024-security-posture-supply-chain.md)
(supply-chain posture); it does not cite any per-repo or per-paper notes. Future revisions that fold in
security-relevant paper-notes (deanonymization, dual-use uplift) or repo-notes should add corresponding `### Repo-notes`
and `### Paper-notes` subsections here._

---

_This synthesis was substantially rewritten on 2026-05-05 using the NIST Cybersecurity Framework, NIST SP 800-207, SP
800-171, NCSC China Genomics Fact Sheet, HHS Cyberthreats to Biotech, Foley Biotech IP Guide, and NCCoE Genomics
Workshop notes (all in `docs/cybersecurity-notes/`). It supersedes the prior 2026-05-01 version. Updated 2026-05-08 to
reflect DEC-0047 (biosecurity tier control), DEC-0053 (KB → hosted-Maestro flow policy), and the resolved supply chain
architecture (DEC-0024, SAFETY.md Supply Chain Incident Response section). Review and update at the start of Phase 2, at
Phase 3, and after any security incident._
