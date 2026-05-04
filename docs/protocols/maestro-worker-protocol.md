# Maestro/Worker Protocol

This document describes the end-to-end workflow for delegating tasks from Maestro (Dan, operating via hosted Claude /
Claude Code) to Workers (local models like Qwen2.5-Coder via Ollama, or future autonomous Linus agents).

The protocol ensures safe, auditable, traceable work and keeps Dan in the review loop while enabling parallel task
execution.

## Summary

1. **Spec** (Maestro): write a concise spec in `experiments/` or `docs/specs/`
2. **Delegate** (Maestro): invoke Worker with the spec
3. **Implement** (Worker): create a branch, implement, push to remote, open PR
4. **Review** (Maestro): review PR on GitHub, approve or request changes
5. **Merge** (Maestro): merge via GitHub, branch auto-deleted
6. **Close** (optional): update spec doc if lessons learned

---

## Phase 1: Spec Writing (Maestro)

### Location

Write specs in one of these locations:

- **Task-scoped**: `experiments/<task-id>.md` for one-off delegations
- **Domain-scoped**: `docs/specs/<domain>/<spec-name>.md` for specs that may be reused or become standing practices
  (e.g., `docs/specs/inference/ollama-benchmark.md`)

### Format

A spec is a Markdown file with these sections:

```markdown
# Spec: <Title>

Task ID: <task-id> (unique short ID, e.g., "kb-sync-v1", "infer-eval-pmetal")

## Goal

One paragraph: what we're trying to learn or build, why it matters.

## Inputs

- Data sources or config files (paths relative to repo root)
- External resources (URLs, credentials needed, API keys)
- Constraints (time limit, resource limit, sample size to use)

## Outputs

- Files to generate (paths)
- Format (JSON, CSV, markdown, etc.)
- Measurement / benchmark target
- Any logs or diagnostics to capture

## Success Criteria

Bullet list. Be specific. Examples:

- "Inference completes in < 5 seconds per example"
- "All 100 test cases pass with no errors"
- "Embeddings match expected SPECTER2 dimensionality (768)"
- "No memory spike above 8 GB during evaluation"

## Smoke Test

Before running on the full scope, validate on a sample. Examples:

- "Test on 10-paper subset of KnowledgeBase first"
- "Run on first 100 examples before the full 10k-example suite"
- "Validate output schema on single model before sweeping all models"

This is the minimal experiment that takes < 5 minutes and proves the approach.

## Implementation Notes

Optional. Call out any gotchas, environment setup, or known library quirks. See CLAUDE.md.

## Related

Links to related docs, issues, or prior specs.
```

### Example Spec

```markdown
# Spec: KB Sync Tool

Task ID: kb-sync-v1

## Goal

Implement a background job that automatically syncs the KnowledgeBase embeddings every 6 hours. This enables Linus to
stay up-to-date as new papers are added to the knowledge base without manual intervention.

## Inputs

- KnowledgeBase corpus: `modules/KnowledgeBase/`
- Metadata DB: `modules/KnowledgeBase/metadata.db` (read-only)
- Existing embeddings: `~/.linus/kb_embeddings.db`

## Outputs

- Python module: `src/linus/knowledge/sync.py` with a `SyncJob` class
- Test file: `tests/test_kb_sync.py`
- Log file at runtime: `~/.linus/kb_sync.log` (append-only, rotated daily)

## Success Criteria

- Sync completes without errors on a 100-paper test corpus in < 30 seconds
- All embeddings have correct shape: (768,) for SPECTER2
- No duplicate embeddings in the database
- Graceful handling of: missing papers, network timeout, corrupted embeddings
- Log shows clear start/end timestamps and record counts

## Smoke Test

1. Insert the sync job manually (don't schedule yet)
2. Run on 10-paper subset
3. Verify output embeddings count and format
4. Check that a re-run updates existing embeddings in-place (no duplication)

## Implementation Notes

- Use `apscheduler` for the background scheduler (already in environment.yml)
- Embeddings are stored in SQLite; batch inserts in chunks of 100 to avoid timeout
- If a sync fails mid-run, the next sync should resume from where it left off (idempotent)

## Related

- ROADMAP.md Phase 2a (KnowledgeBase integration)
- KnowledgeBase SPECTER2 docs at `modules/KnowledgeBase/docs/embeddings.md`
```

---

## Phase 2: Delegation (Maestro)

When the spec is ready, delegate to the Worker. The exact mechanism depends on your harness:

### Via Claude Code (invoking Cline or local orchestration)

```
I've written a spec at experiments/kb-sync-v1.md. Please implement it:

1. Create a branch named: agent/kb-sync-v1/implementation
2. Implement the spec in full
3. Test against the smoke test criteria (10-paper subset first)
4. Push to origin and open a PR with title "Spec: KB Sync Tool"
5. Reference the spec in the PR body
```

### Via Ollama + Cline (future)

```bash
# Cline will have Linus-aware tools and can read the spec directly
cline --task-spec experiments/kb-sync-v1.md --branch agent/kb-sync-v1/implementation
```

### Via future Linus backend (Phase 2+)

```bash
# Direct API call to Linus orchestration layer
curl -X POST http://localhost:8000/v1/worker/execute \
  -H "Content-Type: application/json" \
  -d '{"spec_path": "experiments/kb-sync-v1.md", "branch": "agent/kb-sync-v1/implementation"}'
```

---

## Phase 3: Implementation (Worker)

The Worker receives the spec and executes these steps:

### 3a. Create branch

```bash
git switch main
git pull origin main
git switch -c agent/kb-sync-v1/implementation
```

Branch naming follows BRANCHING.md:

- Format: `agent/<task-id>/<slug>`
- `<task-id>` matches the spec ID (e.g., "kb-sync-v1")
- `<slug>` briefly describes the implementation approach (e.g., "implementation", "with-scheduler", "v1-draft")

### 3b. Implement

Implement per the spec:

- Create/modify files under `src/`, `tests/`, `docs/` as needed
- Run smoke test (subset from spec) **before** committing
- Commit frequently with clear messages

Example commits:

```
git add src/linus/knowledge/sync.py tests/test_kb_sync.py
git commit -m "Implement KB sync job with apscheduler

- SyncJob class manages background sync every 6 hours
- Batch inserts in chunks of 100 to avoid SQLite timeout
- Idempotent: re-runs update existing embeddings in-place
- Tested on 10-paper subset: all embeddings correct shape"
```

If commits are authored by a Worker (not Dan), use:

```
git commit -m "Implement KB sync job with apscheduler

...

Co-Authored-By: Ollama-Qwen2.5-Coder <noreply@ollama.local>"
```

### 3c. Test

Before pushing, run the smoke test from the spec:

```bash
pytest tests/test_kb_sync.py::test_smoke_10_papers -v
```

If smoke test passes, continue. If not, debug and re-commit.

### 3d. Push and open PR

```bash
git push -u origin agent/kb-sync-v1/implementation

gh pr create --title "Spec: KB Sync Tool" \
  --body "$(cat <<'EOF'
## Summary

Implements background job to sync KnowledgeBase embeddings every 6 hours.

## Spec

See experiments/kb-sync-v1.md for full details.

## Testing

- Smoke test (10-paper subset) passed: all embeddings verified
- Full integration test not yet run (awaiting review)

## Checklist

- [x] Spec implemented in full
- [x] Smoke test passes
- [ ] Full test suite passes (pending review)
- [ ] Documentation updated
EOF
)"
```

Optionally use `--draft` flag to keep the PR in draft mode while polishing:

```bash
gh pr create --draft --title "Spec: KB Sync Tool" --body "..."
```

---

## Phase 4: Review (Maestro)

Maestro (Dan) receives a notification and reviews the PR on GitHub.

### What to check

1. **Spec compliance**: Does the implementation match the spec?
2. **Success criteria**: Are all criteria met? (Run smoke test locally if needed.)
3. **Code quality**: Is the code clear, maintainable, tested?
4. **Safety**: Does it respect sandbox policy? No unintended side effects?
5. **Efficiency**: Does it use resources wisely? No obvious inefficiencies?

### Feedback paths

**Approve and merge:**

```bash
gh pr merge <pr-number> --squash
# or via GitHub UI
```

Branch is auto-deleted. The Worker's work is incorporated into `main`.

**Request changes:**

Comment on the PR via GitHub UI:

```
// On the PR:
"The sync should handle a network timeout gracefully. Currently it
fails the whole job. Can we add retry logic with exponential backoff?"
```

The Worker receives the feedback and updates the PR with new commits.

**Close and ask for rewrite:**

If the approach is fundamentally wrong or needs a major rethink:

```
// Close the PR and create an issue or new spec:
"This approach is on the right track, but the scheduler
integration is too tightly coupled. Let's revise the spec
at experiments/kb-sync-v2.md to separate concerns.
I'll assign this to you as a new task."
```

---

## Phase 5: Merge (Maestro)

Once approved, Maestro merges via GitHub:

```bash
gh pr merge <pr-number>
# --squash: combine all worker commits into one (default, recommended for worker PRs)
# --rebase: replay commits one by one (useful for multi-person reviews)
# --auto: merge automatically when status checks pass (optional)
```

The branch is auto-deleted by GitHub. The implementation is now in `main`.

---

## Phase 6: Close and Learn (Maestro)

Optional: if the spec proved inaccurate or lessons were learned, update it:

```markdown
# Spec: KB Sync Tool (CLOSED)

Task ID: kb-sync-v1

[... original spec ...]

## Lessons Learned / Retro

- Initial estimate was 30 seconds per full sync; actual is 8 seconds. Faster than expected due to index caching.
- Network timeout handling proved critical. Future specs should always include a "failure modes" section.
- SQLite batch size of 100 was good; we could try 200 for faster bulk writes on next iteration.

## Status

✅ CLOSED. Implemented and merged as of commit abc123.
```

This helps future Workers avoid repeating the same investigation work.

---

## Multi-Worker Coordination

When multiple Workers collaborate on the same task:

### Case 1: Sequential subtasks

Task A must complete before task B begins.

```markdown
# Spec: Benchmark suite, part 1/2: infrastructure

Task ID: bench-infra-v1

[... spec ...]
```

Worker 1 completes and merges. Then:

```markdown
# Spec: Benchmark suite, part 2/2: inference runs

Task ID: bench-runs-v1

[... spec, referencing completed part 1 ...]
```

Worker 2 starts, depending on Worker 1's output.

### Case 2: Parallel subtasks

Multiple Workers work on independent parts of the same feature.

```
agent/infer-eval-v1/ollama-bench  [Worker 1]
agent/infer-eval-v1/pmetal-bench  [Worker 2]
```

Both push and open PRs independently. Maestro reviews both, approves both, merges them sequentially (if no conflicts) or
coordinates conflict resolution.

### Case 3: Merge coordination

If two workers' branches have merge conflicts (unlikely if they touch different files):

Maestro decides merge order. The second Worker rebases onto the first's merged code:

```bash
# On Worker 2's branch, after Worker 1's merge:
git rebase origin/main
# resolve conflicts
git push -f origin agent/infer-eval-v1/pmetal-bench
```

---

## Spec as a Living Document

Specs are not archived after completion. They become templates for similar future work.

If the same category of task appears again:

1. Copy the closed spec: `cp experiments/kb-sync-v1.md experiments/kb-sync-v2.md`
2. Update it: incorporate lessons learned, adjust success criteria based on new requirements
3. Increment the version number
4. Delegate to a Worker

Over time, frequently-used specs become standing specifications in `docs/specs/` and may be executed multiple times with
minor tweaks.

---

## Related Reading

- [BRANCHING.md](../BRANCHING.md) — branch naming and merge policy
- [CLAUDE.md](../CLAUDE.md) — session protocol and tool use policy
- [SAFETY.md](../SAFETY.md) — autonomy tiers and audit logging
- [ROADMAP.md](../ROADMAP.md#phase-1--recon--baselines) — Phase 1 spec for the first Maestro/Worker loop
