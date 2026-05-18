# Dan-Manual Tasks — What Only You Can Do

> **Date:** 2026-05-18
> **Purpose:** A focused, command-level inventory of work that Maestro (Claude Code / hosted Claude) cannot
> delegate to itself or to Workers. Each task lists the exact command(s) to run, the result format to
> capture, the file path to write to, and how the captured artifact feeds back into Linus's analysis +
> planning loop.
> **Audience:** Dan. This doc is action-oriented — open it, pick a task, do the task, file the result,
> close the loop.

## How to use this doc

Tasks are organized by category and rough priority:

- **A. Phase 1 closeouts** — block downstream Phase 2 architecture (HIGH priority).
- **B. PR reviews** — currently open PRs that need your eyes before merge.
- **C. Decisions only you can make** — judgment calls that require domain knowledge or personal
  preference Maestro can't substitute for.
- **D. Repo-update aftermath review** — 68 of 138 repos updated on 2026-05-18; some need re-evaluation.
- **E. Optional / nice-to-have** — items that improve the project but aren't blocking anything.

For each task: **Why → Command(s) → What to capture → Where it goes → How it feeds back.**

If a task takes longer than 90 minutes of focused work, stop, file what you have, and surface the
remainder as a new TODO in this doc. Better to land partial progress than burn out.

---

## A. Phase 1 closeouts (HIGH priority — block Phase 2 architecture)

### A1. pmetal v0.5.0 verdict ADR (v1 Item 7 / v2 C1)

**Why.** Phase 1b's serving-layer decision needs a verdict ADR. With v0.5.0 just released (99 commits, 418
files since clone — confirmed via the 2026-05-18 repo pull audit), the upstream is now mature enough to
make an informed call. This gates DEC-0006 / DEC-0012 / DEC-0049 closure and shapes Phase 2's worker-model
serving stack.

**Command sequence.** Estimate 2–3 hours hands-on, possibly across 2 sessions.

```sh
cd ~/Desktop/Programming/GitHub/Linus/repos/pmetal
git log --oneline ecc82067..HEAD | head -50     # see what's new
git tag --list 'v*' | tail -5                   # confirm v0.5.0 tag
cat CHANGELOG.md | head -100                    # release notes
cat README.md                                    # current architecture
ls examples/ 2>/dev/null                         # any LoRA / serve examples
cargo build --release 2>&1 | tee /tmp/pmetal-v050-build.log
# Run pmetal's own smoke test (whatever the README points at)
# Run a LoRA fine-tune trial on a small dataset (1k examples, Qwen3:8b)
# Run pmetal serve and compare throughput vs Ollama on a 100-prompt batch
```

**What to capture.** A markdown summary covering:

1. v0.5.0 release notes — what's new in 3–5 bullets.
2. Build status (clean / errors) — paste the build log tail.
3. LoRA trial: dataset size, epochs, wall time, final loss, memory peak. Compare vs the same on
   mlx-lm-ft as a baseline.
4. Serve trial: tokens/sec for a 100-prompt batch on Qwen3:8b. Compare vs Ollama on the same batch.
5. Verdict: **Integrate** (pmetal becomes Phase 2 serving layer), **Study** (keep as reference, ship
   with mlx-lm + Ollama), **Defer** (re-evaluate at Phase 6).

**Where it goes.** Two files:

- `docs/adr/0006-pmetal-phase1-evaluation.md` — UPDATE in place (do not create a new ADR number; this is
  the existing seed). Replace the "in progress" body with the verdict + evidence + decision rationale.
  Status: `accepted`. Set the date to your completion day.
- `docs/specs/phase1b-pmetal-verdict-2026-MM-DD.md` — NEW file with the raw measurements + paste of build
  log tail + plots if you make any. The ADR cites this spec for evidence.

**How it feeds back.** Closes v1 Item 7 → v2 carry-forward C1 is resolved → ROADMAP.md Phase 1b row marked
complete → unblocks Phase 6 fine-tuning lane decision.

### A2. Phase 1c memory-pillar spike

**Why.** `docs/specs/phase1c-spike.md` is the spike-spec for memory-mode viability (CoT-gap fingerprint
per DEC-0033, Worker-size × CoT-length per DEC-0034, TTT viability per DEC-0037). Outputs gate v2 items
N5 (session store), D3 (hook taxonomy), and the dispatch-wiring work (2h.5/6/7).

**Command sequence.** Estimate 3–4 hours across 2 sessions. Run after A1 lands so the serving substrate
is settled.

```sh
cd ~/Desktop/Programming/GitHub/Linus
cat docs/specs/phase1c-spike.md   # the spike-spec is the authoritative test matrix
# Resolve R3-04 first (15 min — reconcile model list between g1-apple-silicon + native-low-bit syntheses).
# Then run the actual spike per spec.
conda activate linus
python -m benchmarks.phase1c.runner --model qwen3:8b   # (if runner doesn't exist yet, write it from the spec)
python -m benchmarks.phase1c.runner --model qwen3.6:27b
python -m benchmarks.phase1c.runner --model mistral:7b-instruct
```

**What to capture.** Per-model JSON results at `benchmarks/results/phase1c_<model>_<date>.json`. Schema
should follow the spike spec exactly. Headline numbers:

- CoT-gap fingerprint: pp gap between open-answer and MCQ on a held-out test set.
- Worker-size × CoT-length: throughput / quality curve as CoT length scales.
- TTT viability: does test-time training of episodic context improve task scores measurably on M1 Max?

**Where it goes.**

- `benchmarks/results/phase1c_*.json` — raw results.
- `docs/adr/0033-cot-gap-fingerprint-registry-property.md` — refresh the body with the measured fingerprint
  values for each tested model. Mark status `accepted` once data is in.
- `docs/adr/0034-worker-size-vs-cot-length-comparison.md` — same.
- `docs/adr/0037-ttt-apple-silicon-viability-spike.md` — same.
- `docs/session-summaries/<date>-phase1c-spike-session-summary.md` — narrative of what you did, lessons
  learned, surprises.

**How it feeds back.** Unblocks v2 D3 (hook taxonomy can be parameterized by the measured CoT-gap) and the
deferred 2h.5/6/7 dispatch wiring (which depends on knowing actual cot_budget values per Worker tier).

### A3. Phase 1f minGRU MLX port spike (DEC-0038)

**Why.** Phase 8 research direction (DEC-0041 — minGRU + BitNet as substrate experiment). Spike scoped at
~1 week of focused work but you can start with a 1-day feasibility pass: clone, attempt a forward-pass on
M1 Max, document blockers. Outputs feed Phase 6 + Phase 8 planning.

**Command sequence.** 1-day feasibility pass:

```sh
# minGRU reference implementation exists; the MLX port does not
cd ~/Desktop/Programming/GitHub/Linus
# Author the MLX port skeleton at experiments/mingru-mlx/
mkdir -p experiments/mingru-mlx
# Implement minGRU forward pass in MLX (reference: arxiv 2410.01201)
# Smoke test: 256-dim hidden state, 512-token sequence, time forward + backward pass
# Memory peak via mlx.utils.peak_memory()
```

**What to capture.** A short markdown summary:

1. Did the port compile and run a forward pass?
2. Forward-pass wall time on M1 Max for a representative sequence length.
3. Memory peak.
4. Blockers (e.g., MLX missing a specific op).
5. Feasibility verdict: **Tractable** (proceed to Phase 6 substrate experiment), **Blocked** (file the
   blockers and defer), **Premature** (re-evaluate when MLX adds X).

**Where it goes.**

- `experiments/mingru-mlx/` — the port code itself.
- `docs/adr/0038-mingru-mlx-port-spike.md` — refresh body with feasibility data + verdict.
- `docs/session-summaries/<date>-mingru-mlx-spike-session-summary.md` — narrative.

**How it feeds back.** Refines DEC-0041 + DEC-0042 (Phase 6 COCONUT substrate experiment) and signals
whether Phase 8 research direction is reachable from current toolchain or needs upstream MLX work first.

### A4. AlphaGenome local-deployability spike (R3-05)

**Why.** Determines whether AlphaGenome is a local Worker (substrate FM in `src/linus/skills/`) or
external-API-only (DEC-0046's `external_api` registry field). Direct entrepreneurial implications per
biological-foundation-models synthesis.

**Command sequence.** 1-day spike:

```sh
cd ~/Desktop/Programming/GitHub/Linus/repos
# AlphaGenome may already be cloned; if not:
git clone <repo-url-from-google-deepmind> AlphaGenome   # check the existing repo-note for the canonical URL
cd AlphaGenome
cat README.md
ls -lh weights/ 2>/dev/null || ls -lh checkpoints/ 2>/dev/null   # inspect model size
du -sh .                                                          # total disk footprint
# Attempt one local inference on a 1 Mb interval per the synthesis spec
# Capture wall time, memory peak, output size
```

**What to capture.** A short markdown:

1. Model size on disk (GB).
2. Inference wall time on a 1 Mb interval (one canonical test case from the README or synthesis).
3. Memory peak on M1 Max.
4. License (commercial-use restrictions per DEC-0046 framing).
5. Verdict: **Local Worker** (tractable), **External-API** (DEC-0046 path), **Defer** (Phase 7+).

**Where it goes.**

- `docs/repo-notes/AlphaGenome.md` — UPDATE existing note with the spike data in Section 3 / 6.
- `docs/session-summaries/<date>-alphagenome-spike-session-summary.md` — narrative.
- If the verdict changes from the synthesis's current framing, mark R3-05 resolved in
  `docs/questions/top-questions.md` and add an entry to `docs/questions/answered-questions.md`.

**How it feeds back.** Closes R3-05 → shapes Phase 7 biology-skill registry priorities.

---

## B. PR reviews (the queue waiting on you right now)

As of 2026-05-18 there are five open PRs that Maestro authored and pushed but cannot merge without your
review.

| PR | Title | Scope |
| --- | --- | --- |
| **#53** | Wave-2 stragglers — moby + distroless repo-notes + protein-design paper-note | 3 new corpus additions; one consolidated PR. |
| **#54** | Synthesis coverage audit (prologue trigger) | The audit doc identifying 14 CONFIRMED GAPs across the synthesis layer. |
| **#55** | Add References sections to all 27 syntheses | Bibliography appended to every synthesis. |
| (this) | Dan-manual-tasks doc + repo-pull status audit | The doc you're reading + the 138-repo pull rollup. |
| (qwen3.6:27b pending) | Dan tasks rerun comparison data | Once the qwen3.6:27b run finishes. |

**Command sequence.**

```sh
cd ~/Desktop/Programming/GitHub/Linus
gh pr list --state open
gh pr view 53        # read the summary
gh pr diff 53        # inspect changes (or use the GitHub web UI)
# repeat for 54, 55, and the others
gh pr merge 53 --squash --delete-branch   # when satisfied
```

**What to capture.** Nothing extra needed beyond the merge action itself. If you have inline review
comments, leave them in the PR's GitHub UI.

**Where it goes.** Merging closes the PR and lands the changes on `main`. The GitHub PR is the durable
record.

**How it feeds back.** Merged PRs become the substrate for future Maestro sessions to build on.
Unmerged PRs delay downstream work.

---

## C. Decisions only you can make

These are judgment calls that need your domain knowledge, personal preference, or strategic taste. Maestro
can lay out trade-offs but cannot pick.

### C1. R2-02 — Worker review gates (Phase 2a)

**Why.** Should Workers self-review against a rubric (Superpowers model) before marking a task complete,
OR should Dan-review be the gate? Two-stage self-review is more scalable for Phase 3 multi-agent
workflows but adds prompt complexity per task. Dan-review is simpler now but doesn't scale.

**What to capture.** A short paragraph in the ADR explaining your call.

**Where it goes.** Write `docs/adr/0063-worker-review-gates.md` (you author this, not Maestro — it's a
preference call). Update R2-02 to resolved in top-questions, add to answered-questions.

**How it feeds back.** Sets the Phase 2a Worker dispatch shape.

### C2. R2-03 — Dan task suite scope + grader strategy

**Why.** v1 Phase 1d shipped with 3 tasks. Expanding to ~20 tasks (fast iteration) vs ~100 (more
regression coverage) is your call. Grader strategy for genomics Q&A (where "gene name X" is right or
wrong, not "similar") is also your call.

**What to capture.** A short decision doc plus the new task definitions.

**Where it goes.**

- `docs/adr/0064-dan-task-suite-scope.md` — author the decision.
- `benchmarks/dan_tasks/tasks/<new-slug>/...` — author the new tasks.
- N7 (the R3-08 benchmarking ADR) lands the convention; this is the per-task data.

**How it feeds back.** Closes R2-03 → makes downstream evaluation work tractable.

### C3. Phase 2 demo target — what counts as "Linus alpha demo-able to yourself"?

**Why.** v2 Item N8 ships a Streamlit chat UI. What scenarios does it need to handle for you to consider
Phase 2 "done enough" to demo to a teammate or peer? E.g., "answer 5 questions about my corpus with
citations and remember what I asked yesterday." This is a strategic-taste call.

**What to capture.** A short scenarios doc with 3–5 demo scripts.

**Where it goes.** `docs/specs/phase2-demo-scenarios.md`.

**How it feeds back.** Gives N8 (chat UI), N9 (citation synthesis), N10 (semantic search), and N11
(ARC-AGI memory diagnostic) a concrete acceptance target.

### C4. R2-45 / project-license stance for Linus itself

**Why.** DEC-0057 governs AGPL **reference** repos. The Linus-project license (MIT? Apache-2.0?
AGPL-3.0? proprietary?) is a separate question that interacts with the entrepreneurship roadmap and the
"open-source-by-default" commitment (DEC-0027 area).

**What to capture.** A decision rationale paragraph.

**Where it goes.** New ADR `docs/adr/0065-project-license-stance.md`. Update top-level `LICENSE` file when
you decide.

**How it feeds back.** Closes the carry-forward open in DEC-0057's text. Frees DEC-0057's "Forbidden tier"
escape hatch.

---

## D. Repo-update aftermath review

68 of 138 repos pulled new commits on 2026-05-18 (full status:
[`docs/audits/2026-05-18-repo-pull-status.md`](../audits/2026-05-18-repo-pull-status.md)). 11 of those have
large enough deltas (>50 commits or >200 files) that the existing repo-note may now misrepresent current
state.

The high-impact tier — pmetal (covered by A1), TheKnowledge, WeKnora, claw-code, link, beever-atlas,
wikimind, codebuff, origin, goose, promptfoo — needs you to either (a) re-read the upstream and refresh
the note yourself, or (b) authorize Maestro to spawn a refresh fan-out (one agent per repo).

**Recommendation.** Authorize a refresh fan-out (option b) — Maestro can handle it as the next
implementation arc. Your decision is "yes, do the refresh fan-out now / batch it into v3 / skip."

**What to capture.** A one-line authorization in your next session ("refresh the 11 high-impact
repo-notes per docs/audits/2026-05-18-repo-pull-status.md") or a note here saying you're deferring.

**Where it goes.** Next session's spec OR this doc as a "deferred to v3" comment.

**How it feeds back.** Determines whether the synthesis-references PR #55 will need a re-run after the
note refreshes, vs whether refs stay accurate-as-of-2026-05-18.

---

## E. Optional / nice-to-have

### E1. Run a `make audit` cron equivalent

Per DEC-0024, `pip-audit` should run monthly. The first drill ran 2026-05-16 (N6). Set up a recurring
reminder or `launchd`-based cron to re-run monthly. Output goes to `docs/security-log.md`.

```sh
# Manually for now:
conda activate linus && pip-audit | tee /tmp/pip-audit-$(date +%Y-%m-%d).log
```

### E2. KnowledgeBase submodule update

The submodule pointer was last touched in commit `e858b8f` (2026-05-16). If the KnowledgeBase repo has new
commits worth pulling, update the submodule pointer:

```sh
cd ~/Desktop/Programming/GitHub/Linus
git submodule update --remote modules/KnowledgeBase
cd modules/KnowledgeBase && git log --oneline -5    # check what's new
cd ../.. && git add modules/KnowledgeBase
git commit -m "[update] Bump KnowledgeBase submodule pointer"
```

### E3. Dan task suite — comparison + analysis

The qwen3:8b baseline ran successfully on 2026-05-18 (results in
`benchmarks/results/dan_tasks_baseline_2026-05-18-qwen3-8b.json`). Eyeball it alongside the existing
qwen2.5-coder:7b baseline (`dan_tasks_baseline_2026-05-16.json`) to see whether qwen3:8b is meaningfully
better on (a) the FASTA GC-content code task, (b) the paper summarization, (c) the title clustering. If
so, the Phase 1d v0 Worker-model choice should upgrade from `qwen2.5-coder:7b` to `qwen3:8b` (matching v1
Item 2's original spec which used `qwen3:8b` before the model was pulled).

**The qwen3.6:27b run FAILED on all three tasks** — every task timed out at the 600s `OLLAMA_TIMEOUT_S`
default. Results file (with the TimeoutError entries) is preserved at
`benchmarks/results/dan_tasks_baseline_2026-05-18-qwen3.6-27b.json` for the audit trail. The 17 GB model
on the 32 GB M1 Max is almost certainly swap-thrashing under inference load. This is a useful Phase 1c
data point: a 27B Worker is NOT viable as currently configured on this hardware. Possible mitigations to
try: (a) raise `OLLAMA_TIMEOUT_S=1800` to confirm whether it's pure slowness vs swap-death; (b) close
other memory-hungry processes (browsers, Claude Code itself) and retry; (c) keep qwen3:8b as the practical
ceiling for the Worker tier on this hardware. Recommend documenting the failure mode in
`docs/session-summaries/2026-05-18-qwen3-dan-tasks-comparison.md` even if you don't run further trials.

**Where it goes.** A short paragraph in a session summary at
`docs/session-summaries/2026-05-18-qwen3-dan-tasks-comparison.md`.

---

## How to feed everything back

The general loop:

1. **Pick a task** from this doc.
2. **Run the commands**, capturing output to `/tmp/...log` files (your call on naming).
3. **Write the artifact** to the path specified in the task's "Where it goes" section.
4. **Open a PR** for the changes: `git switch -c dan/<short-name> && git add ... && git commit && git push -u origin dan/<short-name> && gh pr create`.
5. **In your next Claude Code session, mention the PR or the file path** so Maestro picks up the new
   state and can plan downstream work against it.

If a task surfaces something unexpected — a blocker, a new question, a major upstream change — file it
HERE as a new line in the relevant section. Don't let it drift into "remembered, not written."

---

_This doc is appended-to, not rewritten. As tasks complete, mark them in-place with a brief outcome
line; as new manual tasks surface, add them in the right category._
