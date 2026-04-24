# Linus — Safety & Autonomy

## Principles

- **Default deny for destructive operations.** Most actions are reversible; the ones that
  aren't need explicit confirmation.
- **Every action is auditable.** Append-only audit log at `~/.linus/audit.jsonl`.
- **Autonomy is earned, not assumed.** Higher autonomy tiers unlock when the audit log
  shows sustained safe operation, not because someone feels ready.
- **Sandbox policy is cross-cutting.** Enforced at the Linus orchestration layer, not at
  individual harnesses — this guarantees consistent behavior regardless of front-end.
- **Hardware safety matters.** Inference on Apple Silicon stresses the GPU and ANE.
  Thermal and power limits are real; Linus should respect them.

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

Linus can write to specific directories, run allowlisted commands, and commit (but not
push) to git.

- ✅ All Tier 0
- ✅ `linus.fs.write` under `src/`, `benchmarks/`, `experiments/`, `docs/`
- ✅ `linus.shell.run_sandboxed` with allowlisted commands (see below)
- ✅ Git read-only: `git status`, `git log`, `git diff`, `git branch`, `git show`
- ✅ Git local mutating: `git add`, `git commit`
- ❌ Git remote: `git push`, `git pull`, `git fetch`
- ❌ Writes to repo root files (`*.md`, `.gitignore`, `.gitmodules`, `environment.yml`,
  `pyproject.toml`) — require confirmation
- ❌ Writes to `modules/KnowledgeBase/` (it's a submodule)
- ❌ Writes to `repos/*` (reference clones)
- ❌ Network operations (pip install, ollama pull, curl, wget)

Used for: day-to-day Linus development under Maestro direction.

### Tier 2 — Broader shell + network with confirmation

Linus can run any shell command and any network operation, but each specific command
requires confirmation before execution (not every command of a type — specifically this
command).

- ✅ All Tier 1
- ⚠️ Any shell command not in Tier 1 allowlist — show command, wait for `y` from Dan
- ⚠️ `pip install`, `ollama pull`, `brew install`, `curl`, `wget` — show command and
  destination, wait for `y`
- ⚠️ Writes to repo root files (`.gitignore`, `pyproject.toml`, etc.) — show diff, wait
  for `y`

Unlock criteria: audit log shows ≥100 successful Tier 1 operations with zero policy
violations over at least 2 weeks of active use.

### Tier 3 — Extended auto-execute

Select Tier 2 ops get promoted to auto-execute on a per-command-pattern basis based on
observed usage. Dan approves specific patterns, not blanket tiers.

Unlock criteria: Tier 2 sustained for a month, with explicit request from Dan to
promote a specific command pattern.

### Tier 4+ — Autonomous overnight runs (aspirational)

Reserved for well-scoped autoresearch-style loops with:
- Clear metric
- Clear stopping criterion
- Git worktree isolation
- Automatic revert on failure
- Bounded resource use (time, tokens, disk, GPU)

Unlocked per-experiment, not globally. Each autonomous run is its own proposal with
explicit scope.

## Shell command allowlist (Tier 1)

Auto-execute without confirmation:

- `python`, `python3` (with arguments; within the linus conda env)
- `pytest`, `ruff`, `black`, `mypy`
- `git status`, `git log`, `git diff`, `git branch`, `git show`, `git add`, `git commit`
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
- `git push`, `git reset --hard`, `git rebase` (any form), `git clean -fd`,
  `git submodule deinit`

## Forbidden operations (never, no tier unlock, no confirmation override)

- Editing `modules/KnowledgeBase/` contents directly — changes happen in the
  KnowledgeBase repo
- Editing `repos/*/` contents — they're reference clones
- Writing to `~/.ssh/`, credentials paths, keychain, or secrets stores
- Deleting or modifying `~/.linus/audit.jsonl` — append-only
- Disabling sandbox enforcement
- Bypassing the orchestration layer to call models directly in ways that skip audit
  (this means: harness→model calls for display only is fine; harness→model calls that
  produce filesystem or shell effects must go through Linus)

## Sandbox enforcement

Every Linus tool that touches filesystem or shell follows this contract:

1. Validate arguments against the tier's allowlist and blocklist
2. If forbidden: return `{status: "denied", reason: <policy_rule>}` without attempting
3. If requires confirmation at current tier: return `{status: "needs_confirmation",
   command: <preview>}` to the front-end, wait for user to approve
4. If allowed: write audit log entry BEFORE executing, execute, write completion entry
5. Return `{status: "ok" | "error", details: <...>}`; never raise uncaught exceptions
   to the model

## Audit log format

Append-only JSONL at `~/.linus/audit.jsonl`. One event per line.

```json
{
  "ts": "2026-04-22T21:45:45.123-05:00",
  "session_id": "uuid",
  "event": "tool_call",
  "tool": "linus.fs.write",
  "args": {"path": "src/linus/router.py", "bytes": 1243},
  "tier": 1,
  "decision": "allowed",
  "rule": "tier1.write.src",
  "result": "ok",
  "duration_ms": 12
}
```

Events: `tool_call`, `tool_result`, `policy_decision`, `session_start`, `session_end`,
`model_call`, `cost_record` (when applicable).

Dan reviews the audit log:
- Weekly in early phases
- Monthly once stable
- Ad-hoc before any autonomy tier graduation

## Hardware safety

- **Thermal headroom.** Long training runs push the M1 Max. `powermetrics` or Activity
  Monitor thermal pane should be monitored on multi-hour runs. Linus should emit a
  periodic heartbeat with current temperature if accessible.
- **Disk space.** Model downloads, embeddings, and training checkpoints consume
  hundreds of GB quickly. Linus tools that write large files must check free space
  first and emit a warning if < 50GB free.
- **Memory pressure.** Unified memory is shared across CPU/GPU/ANE. Approaching the
  limit causes system slowdown. Inference tools should report memory high-water mark
  and fail gracefully before swap thrashing.
- **Battery.** When on battery, high-load operations (fine-tuning, big inference) should
  warn. Plugging in is recommended for anything beyond quick inference.

## Safety around KnowledgeBase

- KnowledgeBase is a submodule; Linus never writes to it directly.
- Changes to KnowledgeBase happen in the KnowledgeBase repo, with its own review.
- Linus imports KnowledgeBase's read-only interfaces. If KnowledgeBase needs a new
  capability, it's implemented in KnowledgeBase first, then surfaced in Linus.
- Version pinning via `git submodule`: Linus commits the KnowledgeBase SHA. Updating the
  submodule is an explicit commit.

## Network safety

- No outbound connections except:
  - HuggingFace Hub (model downloads, explicit approval each time)
  - Ollama's localhost endpoint
  - pmetal's localhost endpoint (when adopted)
  - Anthropic API (only from hosted-Claude harnesses — not from Linus backend)
  - CrossRef REST (for KnowledgeBase metadata enrichment, consistent with KB's policy)
  - Wikipedia/Kiwix mirrors (Phase 4, user-approved)
  - PyPI / conda-forge / crates.io (only for explicit package installs with
    confirmation)

Anything else is a confirmation event.

## Claude Code specific

When hosted Claude operates in this repo via Claude Code, it follows the same tiered
autonomy as Linus itself. Additionally:

- Long multi-file sessions emit checkpoint summaries every 3–4 edits
- Smoke tests before any full-corpus run
- Atomic commits with descriptive messages
- No `git push` without explicit Dan approval
- No commits that rewrite history
- PostToolUse hook runs `ruff format --line-length 120` and `ruff check --select I --fix`
  and `ruff check` on edited Python files

## Escalation

If Linus (via Claude Code or a Worker) encounters a situation outside the policy:

1. STOP
2. Describe the situation to Dan
3. Propose options with pros/cons
4. Wait for explicit direction
5. Log the incident in `docs/incidents/YYYY-MM-DD-<short-name>.md` for future
   pattern-learning

Never silently work around a safety rule. Never assume "probably fine."

## Review cadence

- Weekly in Phase 1 and 2: audit log spot-check
- Monthly in Phase 3+: full audit log review
- At every autonomy tier graduation: formal review with explicit Dan approval
- After any incident: immediate review and policy update

This document is living. Incidents update it. Tier graduations update it. The intent —
safe, auditable, reversible — is permanent.
