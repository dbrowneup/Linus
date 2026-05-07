# Linus — Safety & Autonomy

See [BRANCHING.md](BRANCHING.md) for the complete git branching model. This document focuses on autonomy tiers, tool
policies, and audit logging. Branch-specific safety rules are noted in the blocklist below and detailed in BRANCHING.md.

## Principles

- **Default deny for destructive operations.** Most actions are reversible; the ones that aren't need explicit
  confirmation.
- **Every action is auditable.** Append-only audit log at `~/.linus/audit.jsonl`.
- **Autonomy is earned, not assumed.** Higher autonomy tiers unlock when the audit log shows sustained safe operation,
  not because someone feels ready.
- **Sandbox policy is cross-cutting.** Enforced at the Linus orchestration layer, not at individual harnesses — this
  guarantees consistent behavior regardless of front-end.
- **Hardware safety matters.** Inference on Apple Silicon stresses the GPU and ANE. Thermal and power limits are real;
  Linus should respect them.

## Autonomy tiers

### Tier 0 — Read-only (initial)

Linus can read anything under the Linus tree. No writes, no shell, no network.

- ✅ `linus.fs.read` anywhere under repo root
- ✅ `linus.knowledge.*` (read-only queries)
- ❌ Any write operation
- ❌ Any shell command
- ❌ Any network operation

Used for: initial bring-up, smoke tests, pure Q&A against the knowledge base.

### Tier 1 — Sandboxed writes (starting tier for active work)

Linus can write to specific directories, run allowlisted commands, and commit (but not push) to git.

- ✅ All Tier 0
- ✅ `linus.fs.write` under `src/`, `benchmarks/`, `experiments/`, `docs/`
- ✅ `linus.shell.run_sandboxed` with allowlisted commands (see below)
- ✅ Git read-only: `git status`, `git log`, `git diff`, `git branch`, `git show`
- ✅ Git local mutating: `git add`, `git commit`
- ❌ Git remote: `git push`, `git pull`, `git fetch`
- ❌ Writes to repo root files (`*.md`, `.gitignore`, `.gitmodules`, `environment.yml`, `pyproject.toml`) — require
  confirmation
- ❌ Writes to `modules/KnowledgeBase/` (it's a submodule)
- ❌ Writes to `repos/*` (reference clones)
- ❌ Network operations (pip install, ollama pull, curl, wget)

Used for: day-to-day Linus development under Maestro direction.

### Tier 2 — Broader shell + network with confirmation

Linus can run any shell command and any network operation, but each specific command requires confirmation before
execution (not every command of a type — specifically this command).

- ✅ All Tier 1
- ⚠️ Any shell command not in Tier 1 allowlist — show command, wait for `y` from Dan
- ⚠️ `pip install`, `ollama pull`, `brew install`, `curl`, `wget` — show command and destination, wait for `y`
- ⚠️ Writes to repo root files (`.gitignore`, `pyproject.toml`, etc.) — show diff, wait for `y`

Unlock criteria: audit log shows ≥100 successful Tier 1 operations with zero policy violations over at least 2 weeks of
active use.

### Tier 3 — Extended auto-execute

Select Tier 2 ops get promoted to auto-execute on a per-command-pattern basis based on observed usage. Dan approves
specific patterns, not blanket tiers.

Unlock criteria: Tier 2 sustained for a month, with explicit request from Dan to promote a specific command pattern.

### Tier 4+ — Autonomous overnight runs (aspirational)

Reserved for well-scoped autoresearch-style loops with:

- Clear metric
- Clear stopping criterion
- Git worktree isolation
- Automatic revert on failure
- Bounded resource use (time, tokens, disk, GPU)

Unlocked per-experiment, not globally. Each autonomous run is its own proposal with explicit scope.

## Shell command allowlist (Tier 1)

Auto-execute without confirmation:

- `python`, `python3` (with arguments; within the linus conda env)
- `pytest`, `ruff`, `black`, `mypy`
- `git status`, `git log`, `git diff`, `git branch`, `git show`, `git add`, `git commit`
- `git switch -c <branch>` (branch creation)
- `git push -u origin <branch>` (push to non-main branches)
- `gh pr create`, `gh pr view`, `gh pr list`, `gh pr comment` (PR interaction)
- `gh pr merge` (merge PRs; requires Dan's explicit approval in the PR)
- `ls`, `cat`, `grep`, `rg`, `tree`, `wc`, `head`, `tail`, `find` (without `-delete`)
- `echo`, `printf`, `date`
- `conda list`, `conda info`, `conda env list`
- `pip list`, `pip show` (read-only pip)
- `ollama list`, `ollama show`
- `ps`, `top` (read-only)
- `which`, `where`, `type`
- `diff`, `cmp`
- `mkdir` (only under repo root, and only for paths that don't yet exist)
- `touch` (only under repo root)
- `mv`, `cp` within the repo tree only

## Shell command blocklist (never auto-execute, require confirmation at all tiers)

These ALWAYS require confirmation, even at Tier 3+:

- `rm` — any form, any location
- `sudo` — any form
- `chmod`, `chown`, `chgrp`
- `kill`, `killall`, `pkill`
- `dd`
- `shutdown`, `reboot`, `halt`
- `launchctl` (macOS services)
- `systemctl` (Linux services)
- `crontab`
- Any command touching `~/.ssh/`, `~/.aws/`, `~/.config/gh/`, `~/Library/Keychains/`
- Any command touching `~/Library/Application Support/` (apart from Linus's own data)
- Any command with `>`/`>>` redirects outside the repo tree
- `git push` to `main` or `master`
- `git push --force` (any branch)
- `git reset --hard`, `git rebase` (any form), `git clean -fd`, `git submodule deinit`
- `git branch -d` or `git push --delete` for branches other than your own
- Merging non-main branches to `main` outside of PR review (use `gh pr merge` after Dan's approval)

## Forbidden operations (never, no tier unlock, no confirmation override)

- Editing `modules/KnowledgeBase/` contents directly — changes happen in the KnowledgeBase repo
- Editing `repos/*/` contents — they're reference clones
- Writing to `~/.ssh/`, credentials paths, keychain, or secrets stores
- Deleting or modifying `~/.linus/audit.jsonl` — append-only
- Disabling sandbox enforcement
- Bypassing the orchestration layer to call models directly in ways that skip audit (this means: harness→model calls for
  display only is fine; harness→model calls that produce filesystem or shell effects must go through Linus)

## Sandbox enforcement

Every Linus tool that touches filesystem or shell follows this contract:

1. Validate arguments against the tier's allowlist and blocklist
2. If forbidden: return `{status: "denied", reason: <policy_rule>}` without attempting
3. If requires confirmation at current tier: return `{status: "needs_confirmation", command: <preview>}` to the
   front-end, wait for user to approve
4. If allowed: write audit log entry BEFORE executing, execute, write completion entry
5. Return `{status: "ok" | "error", details: <...>}`; never raise uncaught exceptions to the model

## Audit log format

Append-only JSONL at `~/.linus/audit.jsonl`. One event per line.

```json
{
  "ts": "2026-04-22T21:45:45.123-05:00",
  "session_id": "uuid",
  "event": "tool_call",
  "tool": "linus.fs.write",
  "args": { "path": "src/linus/router.py", "bytes": 1243 },
  "tier": 1,
  "decision": "allowed",
  "rule": "tier1.write.src",
  "result": "ok",
  "duration_ms": 12
}
```

Events: `tool_call`, `tool_result`, `policy_decision`, `session_start`, `session_end`, `model_call`, `cost_record` (when
applicable).

Dan reviews the audit log:

- Weekly in early phases
- Monthly once stable
- Ad-hoc before any autonomy tier graduation

## Hardware safety

- **Thermal headroom.** Long training runs push the M1 Max. `powermetrics` or Activity Monitor thermal pane should be
  monitored on multi-hour runs. Linus should emit a periodic heartbeat with current temperature if accessible.
- **Disk space.** Model downloads, embeddings, and training checkpoints consume hundreds of GB quickly. Linus tools that
  write large files must check free space first and emit a warning if < 50GB free.
- **Memory pressure.** Unified memory is shared across CPU/GPU/ANE. Approaching the limit causes system slowdown.
  Inference tools should report memory high-water mark and fail gracefully before swap thrashing.
- **Battery.** When on battery, high-load operations (fine-tuning, big inference) should warn. Plugging in is
  recommended for anything beyond quick inference.

## Safety around KnowledgeBase

- KnowledgeBase is a submodule; Linus never writes to it directly.
- Changes to KnowledgeBase happen in the KnowledgeBase repo, with its own review.
- Linus imports KnowledgeBase's read-only interfaces. If KnowledgeBase needs a new capability, it's implemented in
  KnowledgeBase first, then surfaced in Linus.
- Version pinning via `git submodule`: Linus commits the KnowledgeBase SHA. Updating the submodule is an explicit
  commit.

## Network safety

- No outbound connections except:
  - HuggingFace Hub (model downloads, explicit approval each time)
  - Ollama's localhost endpoint
  - pmetal's localhost endpoint (when adopted)
  - Anthropic API (only from hosted-Claude harnesses — not from Linus backend)
  - CrossRef REST (for KnowledgeBase metadata enrichment, consistent with KB's policy)
  - Wikipedia/Kiwix mirrors (Phase 4, user-approved)
  - PyPI / conda-forge / crates.io (only for explicit package installs with confirmation; experimental packages always
    go in disposable `uv` envs per DEC-0024, never in the linus conda env)

Anything else is a confirmation event.

## Supply Chain Incident Response

Trigger conditions, containment, credential rotation, and attestation procedures for confirmed or suspected supply chain
compromise (DEC-0024). Drafted ahead of any incident so under-stress execution is reliable.

### Trigger conditions

- `pip-audit` reports a HIGH or CRITICAL CVE in an installed package.
- A package suddenly publishes a new release with an anomalous version-jump or unverified signing.
- An unknown subprocess, network connection, or filesystem write originates from a Worker session and cannot be traced
  to known tool calls.
- An external advisory (Snyk, GitHub security advisory, project blog) names a package currently installed.
- A package's behavior changes between sessions despite no version change in `requirements-locked.txt` (hash mismatch
  detected).

### Containment

1. **Pause all in-flight Worker sessions** (`pkill -f ollama serve` if needed; close all VS Code Cline sessions; close
   openclaw if active).
2. **Snapshot the audit log** at `~/.linus/audit.jsonl` to a safe location
   (`~/.linus/incidents/<YYYY-MM-DD>-audit.jsonl`).
3. **Identify the compromised package's access scope:** what files, paths, and network resources did Worker sessions
   touch since the package was last updated? Use the audit log.
4. **Tear down the linus conda env:** `conda env remove -n linus`. Do not reuse the existing env even after a package
   upgrade — adversarial state may persist in pip caches, byte-compiled `.pyc` files, or modified site-packages.
5. **Disable Worker autonomy temporarily:** revert to Tier 0 (read-only) until attestation completes.

### Credential rotation scope and order

Rotate in this order (not in parallel — each rotation is auditable and recoverable):

1. Anthropic API key (highest priority — all hosted Claude sessions).
2. GitHub PAT / SSH keys (if the compromised package had filesystem access to `~/.ssh/` or `~/.config/gh/`).
3. Hugging Face token (if the package may have accessed it).
4. Any other API keys ever loaded into the env (review `~/.linus/audit.jsonl` to identify).

### Attestation: verifying the rebuilt env is clean

1. Recreate the linus env from `environment.yml` + `requirements-locked.txt` with hash verification:
   `pip install --require-hashes -r requirements-locked.txt`.
2. Run `pip-audit` against the fresh env; verify zero HIGH/CRITICAL CVEs.
3. Compare installed package versions against the lock file — exact match required.
4. Run a clean smoke test (Phase 1c spike, single config) in the rebuilt env; verify behavior matches pre-incident
   baseline.
5. Document the incident in `docs/incidents/<YYYY-MM-DD>-<short-name>.md`: timeline, scope, response actions,
   lessons learned, policy updates (e.g., add a package to a permanent blocklist).
6. Resume normal autonomy tier only after all five attestation steps complete.

### `pip-audit` CVE response (non-incident, routine)

`pip-audit` runs monthly per DEC-0024. CVE response by severity:

- **CRITICAL:** treat as confirmed incident — invoke containment + rotation + attestation.
- **HIGH:** triage → patched-version check → if available, env rebuild + lock-file regeneration; if not, document
  mitigation in `docs/security-log.md`.
- **MEDIUM:** queue for next quarterly curation review.
- **LOW / informational:** note in `docs/security-log.md`; no action unless it ages out without remediation.

## Generative biology — three-tier biosecurity policy

Applies to any Linus skill or Worker task that generates or predicts biological sequences (DEC-0047). Three tiers based
on genomic scope:

**Tier A — Residue-level design (no gate).** Single-residue mutation prediction, small peptide design (<50 residues),
protein-property prediction. No special approval required. Output tagged `biosecurity_tier: A` in the audit log.

**Tier B — Gene-level design (sign-off required per invocation).** CDS/codon-level generation, gene-scale scaffold
design, multi-gene pathway reconstruction. Requires explicit per-invocation Dan sign-off before tool call executes.
Output tagged `biosecurity_tier: B`.

**Tier C — Whole-genome design (sign-off + out-of-band review).** Whole-genome scaffold generation, phage genome
assembly from scratch, chromosome-scale design. Requires explicit per-invocation Dan sign-off AND a separate
out-of-band review before execution. Tool call refuses without both approvals. Output tagged `biosecurity_tier: C`.

Tool registry entries for biology-generative tools must include a `biosecurity_tier` field. Workers invoking biology
tools check this field at dispatch time and enforce the appropriate gate.

## KnowledgeBase → hosted-Maestro flow policy

KB content reaching a hosted-Maestro context (Claude API, Claude.ai) is governed by a `hosted-ok` / `hosted-forbidden`
binary tag applied at ingest time (DEC-0053). Conservative default: new records tagged `hosted-forbidden` unless
explicitly upgraded.

- `hosted-ok`: published papers, public reference databases, public ontologies.
- `hosted-forbidden`: Dan's personal notes, draft writing, financial data, LanzaTech proprietary data, anything from
  `context/` that is not already public.

Enforcement: the retrieval layer strips `hosted-forbidden` content before any prompt sent to a hosted model. No
override at query time — only the ingest-time tag governs.

## Claude Code specific

When hosted Claude operates in this repo via Claude Code, it follows the same tiered autonomy as Linus itself.
Additionally:

- Long multi-file sessions emit checkpoint summaries every 3–4 edits
- Smoke tests before any full-corpus run
- Atomic commits with descriptive messages
- No `git push` without explicit Dan approval
- No commits that rewrite history
- PostToolUse hook runs `ruff format --line-length 120` and `ruff check --select I --fix` and `ruff check` on edited
  Python files

## Escalation

If Linus (via Claude Code or a Worker) encounters a situation outside the policy:

1. STOP
2. Describe the situation to Dan
3. Propose options with pros/cons
4. Wait for explicit direction
5. Log the incident in `docs/incidents/YYYY-MM-DD-<short-name>.md` for future pattern-learning

Never silently work around a safety rule. Never assume "probably fine."

## Review cadence

- Weekly in Phase 1 and 2: audit log spot-check
- Monthly in Phase 3+: full audit log review
- At every autonomy tier graduation: formal review with explicit Dan approval
- After any incident: immediate review and policy update

This document is living. Incidents update it. Tier graduations update it. The intent — safe, auditable, reversible — is
permanent.
