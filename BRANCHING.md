# Linus — Git Branching Model

This document specifies how branches are created, used, and merged in the Linus repository to enable safe, auditable,
parallel development with agentic Workers and human Maestro review.

## Overview

Linus uses a **lightweight branching model now** (through Phase 2) that scales to full **Driessen gitflow** in Phase 3+,
when we have versioned releases and need the ceremony of `develop`, `release/*`, and `hotfix/*` branches.

**Current model (Phase 0–2):**

- `main` is the single long-lived integration branch, always deployable, always code-reviewed
- Feature work happens on short-lived feature branches
- Workers create agent branches for delegated tasks, always via PR
- No `develop` branch yet (we have no production release to separate from)
- No `release/*` or `hotfix/*` branches (premature until Phase 3)

**Future model (Phase 3+):**

Adopt full gitflow with:

- `main` for production releases (tagged)
- `develop` for integration of next-release features
- `feature/*` branching from `develop`
- `release/*` for release candidates
- `hotfix/*` for urgent production fixes (branch from `main`, merge to both `main` and `develop`)

This document focuses on the current model. A migration path will be documented as a new ADR in `docs/adr/` (and indexed
in DECISIONS.md) when Phase 3 begins.

---

## Branch Types

### `main`

**Purpose:** Integration, CI/CD, code review hub. The branch Dan points at when sharing Linus with peers.

**Policy:**

- Always buildable and passing tests
- Only accepts merges via pull request (never direct commits for non-trivial work)
- Reviewed by Dan before merge
- Protected on GitHub: require PR, require review, require status checks

**Lifetime:** Permanent

**Who creates:** GitHub admin only (Dan)

---

### `feature/<name>`

**Purpose:** New features or non-critical enhancements.

**Naming:** `feature/kb-sync`, `feature/ollama-backend`, `feature/dark-mode-ui`

**Policy:**

- Branch from: `main`
- Merge back to: `main` via PR
- Reviewed by: Dan
- Lifetime: short (1–7 days typically)

**Examples:**

```
git switch main
git pull origin main
git switch -c feature/kb-sync
# implement
git push -u origin feature/kb-sync
gh pr create --title "Add KnowledgeBase sync tool" --body "..."
```

---

### `agent/<task-id>/<slug>`

**Purpose:** Worker-spawned branches for delegated specs. The `task-id` is the identifier from the spec; `slug` is a
short kebab-case description.

**Naming:** `agent/1k8j-kb-indexing/add-specter-embeddings`, `agent/2m4n-inference/pmetal-evaluation`

**Policy:**

- Branch from: `main`
- Merge back to: `main` via PR
- Reviewed by: Dan (creator is a Worker, not a human)
- Lifetime: short to medium (1–14 days)
- Created by: Worker, not human
- Commits authored by: Worker (e.g., `Co-Authored-By: Ollama-Qwen3`)

**Worker workflow:**

1. Maestro writes a spec in `experiments/<task-id>.md` or `docs/specs/<task-id>.md`
2. Spec includes: goal, inputs, outputs, success criteria, smoke test
3. Worker is invoked with the spec
4. Worker creates branch: `agent/<task-id>/<slug>`
5. Worker implements, commits, and pushes to remote
6. Worker opens PR: `gh pr create --title "Spec: <task-id>" --body "..." --draft` (optional draft while still
   developing)
7. Maestro (Dan) reviews the PR in GitHub
8. Maestro approves and merges, or requests changes
9. Branch is deleted after merge (GitHub's default)

**Parallel workers on the same feature:** If multiple Workers collaborate on a single feature, create sibling branches:

- `agent/<task-id>/worker-1`
- `agent/<task-id>/worker-2`

They coordinate via intermediate branch (`agent/<task-id>/merge-point`) or merge sequentially to avoid conflicts.
Maestro coordinates the merge order.

---

### `fix/<name>`

**Purpose:** Bug fixes (not on a release branch).

**Naming:** `fix/ollama-port-conflict`, `fix/sqlite-timeout-edge-case`

**Policy:**

- Branch from: `main`
- Merge back to: `main` via PR
- Reviewed by: Dan
- Lifetime: short (1–3 days typically)
- Urgency: higher priority than feature branches; aim to merge within 24h

**Examples:**

```
git switch main
git pull origin main
git switch -c fix/ollama-port-conflict
# implement & test
git push -u origin fix/ollama-port-conflict
gh pr create --title "Fix Ollama port 11434 conflict recovery" --body "..."
```

---

### `experiment/<name>` or `spike/<name>`

**Purpose:** Throwaway exploration, ablations, quick tests. Not intended to merge to `main` in the finished form.

**Naming:** `experiment/moe-router-ablation`, `spike/pmetal-eval-trial`, `experiment/flash-attention-benchmark`

**Policy:**

- Branch from: `main` (or another experiment branch)
- Merge back to: Typically no — these are ephemeral
- No PR required if it's your own personal exploration
- Can be deleted without review if > 2 weeks old with no activity
- If an experiment proves valuable and should graduate to a feature, rewrite it as `feature/<name>` with a fresh branch
  and PR

**Lifetime:** Days to weeks; cleaned up regularly

**Examples:**

```
git switch main
git switch -c experiment/moe-router-ablation
# iterate, test, benchmark
# Either: delete if unsuccessful
#   git push origin --delete experiment/moe-router-ablation
# Or: graduate to feature if successful
#   Create fresh feature/<name> branch and PR
```

---

### Personal branches (optional, for humans)

**Purpose:** Work-in-progress before formalizing as a feature or fix PR.

**Naming:** `dan/kb-prototype`, `dan/benchmark-refactor`

**Policy:**

- Branch from: `main`
- Only used by Dan
- Never merge directly; when ready, rewrite as `feature/<name>` or `fix/<name>` with a PR
- Safe to delete — these are **always** staging, never production
- Lifetime: hours to days; should be short-lived

**Examples:**

```
git switch main
git switch -c dan/kb-prototype
# rough implementation, commit as you go
git push -u origin dan/kb-prototype
# Later, when clean and tested:
git switch -c feature/kb-prototype-v1  # new branch from main
# cherry-pick / rebase clean commits from dan/kb-prototype
# Open PR for feature/kb-prototype-v1
```

---

## Merge Policy

### Merging to `main`

All changes to `main` **except minor documentation fixes and config updates** must be reviewed before merge. Use the
GitHub PR workflow:

```bash
# After pushing your branch:
gh pr create --title "Brief title" --body "$(cat <<'EOF'
## Summary
What this change does and why.

## Testing
What tests were run, or how to test manually.

## Related issues
Closes #123 (if applicable)
EOF
)"

# Dan reviews on GitHub
# After approval:
gh pr merge <pr-number> --squash
# Or merge via GitHub UI

# Clean up:
git branch -d <branch-name>
git push origin --delete <branch-name>
```

### Commit messages

**Format:** Imperative mood, present tense.

```
Add KnowledgeBase sync tool

- Implement SPECTER2 embedding sync from KB
- Add background job scheduler
- Add tests for edge cases (empty corpus, connection timeout)

Closes #42
```

**Not:**

- "Added KnowledgeBase sync tool"
- "Fixed the sync bug"
- "WIP: experimenting with KB" (use branches instead)

### Force-push policy

**Never force-push to `main`.** Force-push is forbidden by default (see SAFETY.md).

For your own feature branches (before opening a PR), force-push is OK to clean up local history:

```bash
git rebase -i origin/main
git push -f origin feature/my-feature  # only your branch, before PR is opened
```

Once a PR is open, **do not force-push.** If you need to update, add new commits (GitHub shows the diff over time). If a
rebase is truly necessary, coordinate with Dan and create a new branch instead.

---

## Examples

### Scenario 1: Dan implements a feature

```bash
# Start feature branch
git switch main && git pull origin main
git switch -c feature/dark-mode

# Implement
echo "/* dark theme */" >> src/app.css
git add src/app.css
git commit -m "Add dark theme stylesheet"
git push -u origin feature/dark-mode

# Create PR
gh pr create --title "Add dark mode UI" --body "..."

# Review yourself, then merge (or wait for peer review if needed)
gh pr merge <pr-number>
git switch main && git pull origin main
```

### Scenario 2: Worker implements a delegated spec

**Maestro (Dan) side:**

1. Write spec: `experiments/kb-sync.md`

   ```markdown
   # Spec: KB Sync Tool

   ## Goal

   Implement a background job that syncs the KnowledgeBase embeddings every 6 hours.

   ## Inputs

   - KnowledgeBase path: `modules/KnowledgeBase/`
   - Current embeddings index: `~/.linus/kb_embeddings.db`

   ## Outputs

   - Updated embeddings index
   - Log file: `~/.linus/kb_sync.log`

   ## Success criteria

   - Sync completes without errors on 100-paper subset
   - Embeddings match expected SPECTER2 dimension (768)
   - Existing embeddings are updated, not duplicated

   ## Smoke test

   - Run on 10-paper subset first
   - Verify log output and embeddings count
   ```

2. Delegate to Worker (Cline, Ollama, future Linus backend): "Implement the spec at `experiments/kb-sync.md`. Create
   branch `agent/kb-sync/v1`."

**Worker side:**

3. Create and implement:

   ```bash
   git switch main && git pull origin main
   git switch -c agent/kb-sync/v1

   # Implement per spec
   # ... write code, test on smoke-test subset ...

   git add src/linus/knowledge/sync.py src/linus/jobs/scheduler.py tests/
   git commit -m "Implement KB sync background job

   - Scheduled sync every 6 hours via apscheduler
   - SPECTER2 embeddings updated in-place to ~/.linus/kb_embeddings.db
   - Tested on 10-paper subset; all embeddings verified

   Co-Authored-By: Ollama-Qwen3"

   git push -u origin agent/kb-sync/v1
   gh pr create --title "Spec: KB sync tool" --body "Implements background KB sync."
   ```

4. Maestro (Dan) reviews PR on GitHub:
   - Check implementation against spec
   - Run smoke test locally if needed
   - Approve or request changes

5. Maestro merges:
   ```bash
   gh pr merge <pr-number>
   # Automatic cleanup of agent/kb-sync/v1 branch
   ```

### Scenario 3: Multiple workers on one feature

Feature: "Inference backend evaluation" (`agent/infer-eval/worker-*`)

- Worker 1 evaluates Ollama: `agent/infer-eval/ollama-bench`
- Worker 2 evaluates pmetal: `agent/infer-eval/pmetal-bench`

Merge order: Both workers push their branches and open PRs. Maestro reviews them independently (they shouldn't
conflict), approves both, merges them in sequence.

If there is a conflict, Maestro decides which branch merges first, then coordinates re-basing the second worker's
branch.

### Scenario 4: Quick experiment, not merged

```bash
# Explore a router ablation
git switch -c experiment/moe-router-ablation
# ... implement, test, iterate ...
git push origin experiment/moe-router-ablation

# Later: decide it's not worth pursuing
git push origin --delete experiment/moe-router-ablation
```

Or: the experiment was valuable. Graduate it:

```bash
# Start fresh feature branch from current main
git switch main && git pull origin main
git switch -c feature/moe-router-v1

# Cherry-pick clean commits from experiment
git cherry-pick <commit-1> <commit-2> ...
# Or rebase and squash
git rebase -i origin/main
git push -u origin feature/moe-router-v1

gh pr create --title "Add MoE router" --body "..."
```

---

## Phase 3 Migration

**When Phase 3 begins,** the repository will graduate to full Driessen gitflow:

- Create a `develop` branch from `main` (becomes the integration point for features)
- Feature branches branch from `develop` (not `main`)
- `release/*` branches branch from `develop` when preparing a release candidate
- `hotfix/*` branches branch from `main` (urgent production fixes)
- Tags mark releases on `main`
- Bugfixes from `release/*` and `hotfix/*` merge back into `develop`

The canonical reference for this model is Vincent Driessen's 2010 article _A successful Git branching model_ — the
original PDF (figure included) is archived locally at
[`context/pics/Git_Branching_Model.pdf`](context/pics/Git_Branching_Model.pdf) for offline lookup when the upstream URL
rots.

The decision to graduate and the migration procedure will be documented as a new ADR in `docs/adr/` (and indexed in
DECISIONS.md).

Until then, treat this document as the source of truth.

---

## Safety Rules

See SAFETY.md for the complete autonomy tier and tool use policy. Branch-specific rules:

- **Never force-push to `main`.** Forbidden always. (SAFETY.md blocklist)
- **Never delete another person's branch without asking.** If a branch is stale (> 2 weeks, no commits, no PR activity),
  Dan can clean it up.
- **Never commit directly to `main` for non-trivial work.** Always use a branch and PR. Exception: single-line doc fixes
  or config updates with obvious correctness.
- **`gh pr create` is auto-execute for Workers.** Once a spec is implemented, a Worker can open a PR without
  confirmation. (Details in tool use policy.)
- **Protected branches on GitHub.** `main` requires:
  - Pull request review (at least 1 approval, by Dan)
  - Status checks passing (CI/CD, tests)
  - Up-to-date with `main` before merge

---

## Related Reading

- [CLAUDE.md](CLAUDE.md) — session protocol, tool use policy
- [SAFETY.md](SAFETY.md) — autonomy tiers, branch-level safety, audit log
- [docs/protocols/maestro-worker-protocol.md](docs/protocols/maestro-worker-protocol.md) — end-to-end workflow for spec
  → implementation → review
- [ROADMAP.md](ROADMAP.md#phase-3--knowledge-integration-and-parallel-agents) — Phase 3 branching model migration
