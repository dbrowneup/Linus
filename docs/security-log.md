# Linus Security Log

Routine and incident security findings per SAFETY.md "Supply Chain Incident Response" and DEC-0024. Entries are
append-only and chronological. CRITICAL / HIGH findings trigger the containment + rotation + attestation procedure;
MEDIUM findings queue for the next quarterly curation review; LOW / informational findings remain documented unless
they age out without remediation.

---

## 2026-05-16 — N6 janitorial: first `pip-audit` drill + Ollama blob integrity check

Closes R3-01 (supply-chain architecture executed) and R3-12 (model weight integrity) from `top-questions.md`. Logged as
a single entry because both are routine, non-incident audits run as part of the N6 janitorial pass.

### `pip-audit` against the linus conda env

Ran `pip-audit` (v2.10.0, installed into the linus env for this drill) against the current `linus` environment. **21
vulnerabilities found across 11 packages.** Severity ranking is not surfaced by `pip-audit`; classification below is
based on (a) whether the package is in Linus's orchestration runtime path, (b) whether a fix version is published, and
(c) the nature of the CVE.

**Orchestration-runtime-path packages (triage priority HIGH for Phase 2a):**

| Package | Installed | CVE / GHSA | Fix |
| --- | --- | --- | --- |
| `langchain-core` | 1.3.1 | CVE-2026-44843 | 0.3.85, 1.3.3 |
| `langsmith` | 0.7.35 | CVE-2026-45134 | 0.8.0 |
| `urllib3` | 2.6.3 | CVE-2026-44431, CVE-2026-44432 | 2.7.0 |
| `python-multipart` | 0.0.26 | CVE-2026-42561 | 0.0.27 |
| `gitpython` | 3.1.47 | CVE-2026-44244, GHSA-mv93-w799-cj2w | 3.1.49, 3.1.50 |
| `pip` | 26.0.1 | CVE-2026-3219, CVE-2026-6357 | 26.1 (one CVE has no fix) |

**Dev / notebook-stack packages (triage priority MEDIUM — not in Linus orchestration runtime, but loaded in
KnowledgeBase ingest sessions):**

| Package | Installed | CVE | Fix |
| --- | --- | --- | --- |
| `jupyter-server` | 2.17.0 | CVE-2025-61669, CVE-2026-40110, CVE-2026-35397, CVE-2026-40934 | 2.18.0 |
| `jupyterlab` | 4.5.6 | CVE-2026-42266, CVE-2026-42557 | 4.5.7 |
| `notebook` | 7.5.5 | CVE-2026-40171 | 7.5.6 |
| `mistune` | 3.2.0 | CVE-2026-33079, CVE-2026-44708, CVE-2026-44896, CVE-2026-44897 | 3.2.1 (two CVEs have no fix) |

**No-fix-available (triage priority LOW — documented mitigation):**

| Package | Installed | CVE | Note |
| --- | --- | --- | --- |
| `sqlitedict` | 2.1.0 | CVE-2024-35515 | No fix published. Package is not used in Linus orchestration runtime; transitive via KnowledgeBase tooling. Not exposed to untrusted input. |

**Action items queued for the next implementation arc (recorded as N6 items in
`docs/specs/2026-05-17-linus-implementation-plan-v2.md`):**

1. Generate `requirements-locked.txt` via `pip-compile` + hash-pinning per DEC-0024. The pip-audit drill is the first
   half of R3-01; the lockfile is the second half and remains outstanding.
2. After lockfile generation, run `conda env update` with the upgrade targets above for the orchestration-runtime-path
   set. Verify Linus tests still pass after upgrade.
3. Re-run `pip-audit` against the rebuilt env to confirm the orchestration-runtime-path findings are cleared.

No CRITICAL findings; no containment + rotation + attestation procedure invoked.

### Ollama blob integrity (R3-12)

Verified SHA-256 of every blob in `~/.ollama/models/blobs/` against its content-addressed filename. 10 of 10 blobs pass
— on-disk content matches the SHA-256 hash that names the file:

```
OK    sha256-1064e17101bdd2460dd5c4e03e4f5cc1b38a4dee66084dc91faba294ccb64a92
OK    sha256-1e65450c30670713aa47fe23e8b9662bdf4065e81cc8e3cbfaa98924fcc0d320
OK    sha256-1ff5b64b61b9a63146475a24f70d3ca2fd6fdeec44247987163479968896fc0b
OK    sha256-43070e2d4e532684de521b885f385d0841030efa2b1a20bafb76133a5e1379c1
OK    sha256-60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463
OK    sha256-66b9ea09bd5b7099cbb4fc820f31b575c0366fa439b08245566692c6784e281e
OK    sha256-832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e
OK    sha256-d9bb33f2786931fea42f50936a2424818aa2f14500638af2f01861eb2c8fb446
OK    sha256-ed11eda7790d05b49395598a42b155812b17e263214292f7b87d15e14003d337
OK    sha256-f5074b1221da0f5a2910d33b642efa5b9eb58cfdddca1c79e16d7ad28aa2b31f
```

Coverage: `mistral:7b-instruct` + `qwen2.5-coder:7b` — every blob referenced by the local manifests.

**Caveat — what this verifies and what it does not.** This drill confirms _local-storage_ integrity: the on-disk
content matches its own content-addressed filename, so no in-place modification has occurred since Ollama wrote the
files. It does NOT verify provenance: it does not confirm that these SHA-256 hashes match what `registry.ollama.ai`
published at download time. A full provenance check would require an HTTP fetch of the manifest from
`registry.ollama.ai` and comparison against the local blob digests — a network operation that requires confirmation per
SAFETY.md Tier 1. Queued for the next implementation arc as a follow-up.

No issues; no incident.

---

_This file is append-only. Add new entries at the bottom with a date header and a short rationale for the entry. Each
entry must include: scope (routine vs incident), findings, action items (with status), and any caveats on the methods
used._
