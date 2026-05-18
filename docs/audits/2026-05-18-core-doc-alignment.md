# Core-Doc Alignment Audit — 2026-05-18

## Summary

Audited the nine root-level core docs (CLAUDE.md, VISION.md, ARCHITECTURE.md, ROADMAP.md, SAFETY.md, DECISIONS.md,
GLOSSARY.md, BRANCHING.md, README.md) against current state: ADR layer through DEC-0058, the 27-synthesis corpus, the
2026-05-17 implementation plan v2, the 2026-05-18 Dan-manual-tasks doc, and the live `src/linus/` codebase (server +
sandbox + memory + knowledge + tools, plus a `tests/` tree). Excluded from scope: CLAUDE.md content overlapping with
in-flight PRs #57/#58/#59/#60. Headline counts: **11 Tier 1 findings** (high-impact, recommend executing this session),
**14 Tier 2 findings** (worth doing but lower urgency), **9 Tier 3 findings** (reservoir / nice-to-have). The single
biggest cluster of staleness is in **ROADMAP.md** and **README.md** — both still describe Phase 2 as forward work when
Phase 2a is largely landed (PR #32/#33/#34/#35/#40/#50/#51), and ROADMAP's Phase 1 status snapshot is dated 2026-05-10
and predates eight subsequent landings. The second-biggest cluster is **missing cross-references to DEC-0055–DEC-0058**
in DECISIONS.md (DEC-0055 absent entirely), docs/adr/README.md, ARCHITECTURE.md, and VISION.md.

---

## Findings

### Tier 1 — High-impact, recommend executing in this session

#### T1-1. DECISIONS.md is missing DEC-0055 entirely

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/DECISIONS.md`
**Location:** Index table, between DEC-0054 row (line 77) and DEC-0056 row (line 78).
**Before:** Table jumps from DEC-0054 to DEC-0056. DEC-0055 (filename discipline: no spaces) — accepted 2026-05-16 per
PR #31 — has its own ADR file at `docs/adr/0055-filename-discipline-no-spaces.md` but no row in the canonical index.
**After:** Insert a row:
`| [DEC-0055](docs/adr/0055-filename-discipline-no-spaces.md) | Filename discipline: no spaces or special characters in tracked paths | accepted |`
**Why it matters:** DECISIONS.md is the canonical lookup index; the per-file ADR README explicitly defers the
"full canonical index" responsibility back to DECISIONS.md (line 88 of `docs/adr/README.md`). Skipping DEC-0055
breaks that contract and means a `grep -c DEC-0055` against the repo undercounts the ADR by one.

#### T1-2. docs/adr/README.md index also skips DEC-0055

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/docs/adr/README.md`
**Location:** Index table, between DEC-0054 row (line 83) and DEC-0056 row (line 84).
**Before:** Same gap — DEC-0055 absent.
**After:** Insert
`| [DEC-0055](0055-filename-discipline-no-spaces.md) | Filename discipline: no spaces or special characters in tracked paths | accepted |`
**Why it matters:** Same as T1-1, but at the per-ADR-folder level. The footnote at line 88 ("DEC-0044 through DEC-0054
also exist; see DECISIONS.md for the full canonical index") is itself stale — DEC-0044–DEC-0054 ARE in this table; what's
missing is DEC-0055 alone. Fix the row and delete/update the footnote.

#### T1-3. README.md "Quick start" claims `python -m linus.server` is "not yet implemented"

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/README.md`
**Location:** Lines 111–115.
**Before:**
```
# 6. (Phase 2+) Launch the Linus backend
# python -m linus.server  # not yet implemented

# 7. (Phase 2+) Launch the chat UI
# streamlit run src/linus/app/main.py  # not yet implemented
```
**After:** The backend IS implemented and runnable today (`src/linus/server.py`, PR #32 + Item 6 in PR #40):
```
# 6. Launch the Linus backend (Phase 2a; v0 — OpenAI-compatible chat completions)
linus-serve   # or: uvicorn linus.server:app --reload

# 7. (Phase 2b — not yet implemented) Launch the chat UI
# streamlit run src/linus/app/main.py  # planned in v2 item N8
```
**Why it matters:** First-time-reader experience. README's status block already says "Phase 1 (in progress)" but the
quick start contradicts the actual repo state. Anyone landing on the README today and trying `python -m linus.server`
will succeed — the comment is just wrong.

#### T1-4. README.md status block is stale (predates Phase 2a landings)

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/README.md`
**Location:** Lines 23–25.
**Before:**
> **Phase 1 — Recon and Baselines** (in progress). Phase 0 closed. Repo synthesis notes largely complete; pmetal
> evaluation underway (built from source, smoke tests pass). See [ROADMAP.md](ROADMAP.md) for the phased plan.

**After:**
> **Phase 1 — Recon and Baselines** (in progress) + **Phase 2 — Linus MVP** (Phase 2a substantially landed). Phase 0
> closed. Repo synthesis notes complete (117 repo-notes + 118 paper-notes + 27 syntheses). Phase 2a: FastAPI
> orchestration backend, OpenAI-compatible `/v1/chat/completions`, KB read-only adapter, memory v0 (SQLite episodic
> store + content hashing + JSONL audit log), tool registry, and SandboxFS all shipped (PRs #32–#51). Phase 1b pmetal
> verdict ADR still pending (Dan-driven, see `docs/specs/2026-05-18-dan-manual-tasks.md` task A1). See [ROADMAP.md](ROADMAP.md).

**Why it matters:** The README is the GitHub front page. Saying "Phase 1 in progress" when Phase 2a is mostly built
understates the project by ~5 weeks of compounded work and misrepresents the current shape.

#### T1-5. ROADMAP.md Phase 1 status snapshot dated 2026-05-10 is missing eight landings

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/ROADMAP.md`
**Location:** Lines 33–45, the **Status snapshot (2026-05-10):** block under Phase 1.
**Before:** Lists "1a — Repo synthesis notes: complete" and "1b — pmetal deep evaluation: in progress." Says "1c, 1d,
1e, 1f: not yet started."
**After:** Update to **Status snapshot (2026-05-18)** and reflect:
- **1d Dan task suite** — v0 shipped (3 tasks: fasta-gc-content, paper-summarization, title-clustering) with two
  baselines (qwen2.5-coder:7b on 2026-05-16, qwen3:8b on 2026-05-18). qwen3.6:27b run failed (swap-thrash; documented).
  PR #33.
- **1e First Maestro/Worker loop** — recorded; verdict REJECT; calibration data preserved (PR #38; see
  `experiments/first-loop-review.md`).
- Note new constraint: qwen3.6:27b is empirically non-viable on 32 GB M1 Max with current Ollama config; qwen3:8b
  remains the practical Worker ceiling (informs DEC-0033 / DEC-0034 fingerprint calibration).
- Add status for v0 ADR seeds: DEC-0055 / DEC-0056 / DEC-0057 / DEC-0058 landed via PR #31 and PR #36.

**Why it matters:** ROADMAP is the project's working plan; an 8-day-stale snapshot drives planning calls that don't
match reality. T1-5 + T1-4 + T1-6 are the same class of fix — pull Phase 1/2 status forward.

#### T1-6. ROADMAP.md Phase 2 description treats 2a as forward work

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/ROADMAP.md`
**Location:** Lines 143–246 (full Phase 2 section, particularly the **2a — Orchestration backend (first
implementation)** subsection at line 150).
**Before:** Treats 2a, 2c (KB adapter), 2d (first real use, smoke-tested), and 2h (memory pillar v0) all as future work.
Lists deliverables as bullet items without status markers.
**After:** Add a Phase 2 **Status snapshot (2026-05-18):** block at the top, mirroring Phase 1's snapshot pattern:
- **2a Orchestration backend:** shipped (FastAPI server, OpenAI-compatible endpoint, tool-call routing, model
  preference fallback). PR #32 + PR #40. Outstanding: streaming SSE (v2 N2), Anthropic `/v1/messages` (v2 N3, DEC-0056),
  env-loaded config (v2 N4), session store (v2 N5). See `docs/specs/2026-05-17-linus-implementation-plan-v2.md`.
- **2c KnowledgeBase adapter v0:** shipped read-only adapter at `src/linus/knowledge/adapter.py` (PR #34). Outstanding:
  SPECTER2 semantic search (v2 N10), dual substrate (deferred to v3), citation synthesis (v2 N9).
- **2h Memory pillar v0:** shipped Layer C substrate (SQLite + content hashes + audit log) at `src/linus/memory/` with
  35 unit tests (PR #35). Outstanding: dispatch-layer prefix loader + router primitive plumbing + Worker registry
  (the 2h.5/6/7 split deferred behind D3 hook-taxonomy ADR).
- **Sandbox:** SandboxFS shipped at `src/linus/sandbox/fs.py` (PR #50) — hand-written after Item 3 first-loop calibration
  showed Workers couldn't pass security gates.
- **2e citations, 2f dual substrate, 2g knowledge-mining-surface, 2i ARC-AGI diagnostic, 2j Worker non-conformance:**
  not yet shipped; tracked in v2 plan.

**Why it matters:** ROADMAP is the contract for what's done vs. pending. Right now a reader can't tell from
ROADMAP alone whether Phase 2a is built or aspirational.

#### T1-7. ARCHITECTURE.md "Linus orchestration layer" section says "built iteratively starting in Phase 2" — Phase 2 has started

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/ARCHITECTURE.md`
**Location:** Lines 105–107.
**Before:**
> ### The Linus orchestration layer (src/linus/)
>
> This is the product. A Python package, built iteratively starting in Phase 2.

**After:**
> ### The Linus orchestration layer (src/linus/)
>
> This is the product. A Python package; Phase 2a is largely landed as of 2026-05-18.
> Current modules: `linus.server` (FastAPI app, OpenAI-compatible `/v1/chat/completions` with tool-call routing),
> `linus.tools` (in-memory tool registry + KB tool wrappers), `linus.knowledge` (read-only KB adapter), `linus.memory`
> (SQLite episodic store + audit log + content hashing), `linus.sandbox` (path-validating filesystem wrapper).
> Outstanding Phase 2a items: streaming SSE, Anthropic Messages endpoint per DEC-0056, env-loaded config,
> session store — see `docs/specs/2026-05-17-linus-implementation-plan-v2.md`.

**Why it matters:** Anyone reading ARCHITECTURE.md right now thinks the orchestration layer is vapor; it isn't.
Same fix-shape as T1-6 (pull state forward), one layer up.

#### T1-8. ARCHITECTURE.md never mentions DEC-0056 (dual OpenAI + Anthropic surface)

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/ARCHITECTURE.md`
**Location:** "Interface contracts" section (lines 269–276) and the Phase 2 implementation phasing list (lines 301–317).
**Before:** "Interface contracts" describes only `POST /v1/chat/completions` with the OpenAI ChatCompletions schema.
"Implementation phasing" lists Phase 2 deliverables but doesn't mention the dual-protocol commitment.
**After:**
- In "Interface contracts", add a second subsection (or amend the first) noting that DEC-0056 amends DEC-0005 to also
  expose `POST /v1/messages` with the Anthropic Messages schema from Phase 2a. The Anthropic surface translates onto
  the same Ollama routing + tool registry + audit log; it is not a parallel pipeline.
- In "Implementation phasing", add Anthropic `/v1/messages` to the Phase 2 router deliverable line.
**Why it matters:** DEC-0056 is one of the most consequential post-2026-05-03 ADRs (it changes the protocol surface
of the product); ARCHITECTURE.md is the natural place for it to land. Letta, Kimi-K2, and Goose all confirmed Anthropic-
compat is the production-stack norm; the omission is load-bearing.

#### T1-9. CLAUDE.md repo-layout box still names ADRs DEC-0001–DEC-0054 explicitly; needs DEC-0055–DEC-0058 + drop seed mentions

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/CLAUDE.md`
**Location:** The ADR list under `docs/adr/` in the "Repo Layout" block — the line-by-line file enumeration runs from
DEC-0001 through DEC-0054.
**Before:** Layout enumerates 54 ADR files explicitly (lines 130-183 in the current file). DEC-0055 / DEC-0056 / DEC-0057
/ DEC-0058 are missing from the enumeration even though they exist as files in the repo.
**After:** Either add four lines for DEC-0055–DEC-0058, or replace the long enumeration with a one-line "see
docs/adr/README.md for the index" pointer (the enumeration is brittle by design — every new ADR drifts it).
**Why it matters:** CLAUDE.md is read first every session; if it enumerates ADR files it must enumerate all of them.
Note: this finding does NOT overlap with PR #59 (worktree paragraphs) or PR #60 (CLAUDE.md compression) — both
of those operate on different sections. Verify before applying.

#### T1-10. SAFETY.md references `docs/incidents/` which does not exist

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/SAFETY.md`
**Location:** Lines 254 (Supply Chain Incident Response) and 321 (Escalation).
**Before:** References `docs/incidents/<YYYY-MM-DD>-<short-name>.md` as the canonical incident-record path.
**After:** Two options. (a) Create an empty `docs/incidents/` directory with a stub README (Tier 2 work, not blocker).
(b) Move incident-record path to `docs/security-log.md` (which already exists and serves a closely-related routine
auditing function). Recommendation: keep the path reference as-is — `docs/incidents/` is correct for incident records
(distinct from routine `pip-audit` log entries in `docs/security-log.md`) — but add a one-liner in SAFETY.md noting
the directory will be created at first-incident time, and link to `docs/security-log.md` for non-incident routine
findings.
**Why it matters:** SAFETY.md is supposed to be operational; pointing at a non-existent directory in the incident-
response procedure means the procedure can't be followed verbatim under stress. Either fix the path or pre-create
the directory.

#### T1-11. CLAUDE.md status line says PR #60 reduced CLAUDE.md to 677 lines — verify against post-PR-60 state

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/CLAUDE.md` (post-PR-60)
**Location:** N/A — applies after PR #60 merges.
**Before:** N/A.
**After:** After PR #60 lands, re-run T1-9 against the compressed CLAUDE.md. If PR #60's compression already drops the
ADR enumeration in favor of the pointer, T1-9 is moot. If not, T1-9 still applies and should be folded into a
follow-up edit.
**Why it matters:** Order-of-operations. T1-9 specifically calls out checking against PR #60's scope to avoid
overlap; flagging as a Tier 1 follow-up so it doesn't get lost.

---

### Tier 2 — Worth doing but lower urgency

#### T2-1. VISION.md never mentions DEC-0056 (Anthropic-compat protocol) or DEC-0057 (AGPL fork posture)

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/VISION.md`
**Location:** Anywhere — VISION.md doesn't reference recent ADRs explicitly, but the "Release posture" section
(lines 86–94) and the post-2026-05-04 "concrete" section (lines 156–192) both touch territory the new ADRs occupy.
**Before:** Release posture discusses open-source defaults without naming DEC-0057. The orchestration-shape discussion
nowhere mentions the Anthropic-compat decision.
**After:** Either (a) add a one-line link from "Release posture" to DEC-0057 (AGPL posture), and one-line in the
"concrete" section about Anthropic-compat per DEC-0056 emerging as a production-stack norm, or (b) leave VISION.md
high-level and let DECISIONS.md / ARCHITECTURE.md carry the ADR pointers. Recommendation: option (b) — VISION.md
should not become an ADR digest. But cross-reference at least DEC-0057 in Release posture since that's directly
about the open-source-default rationale.
**Why it matters:** VISION.md is the canonical "what is Linus" doc; if a major decision (protocol shape, license
stance) propagates without being acknowledged at the vision layer, the story gets thin. Lower urgency than the
Tier 1 staleness because VISION.md is read less often.

#### T2-2. ROADMAP.md Phase 3 branching graduation references "a new ADR in docs/adr/" — write it now or remove the forward reference

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/ROADMAP.md`
**Location:** Lines 258–265 (Phase 3 branching model graduation), also BRANCHING.md lines 28–30, 426–428.
**Before:** Three separate places promise "a new ADR documenting the gitflow graduation." No such ADR exists yet
(would be DEC-0059 at next-free).
**After:** Either author a short stub ADR `docs/adr/0059-phase3-gitflow-graduation.md` recording the intent +
trigger condition + migration steps (DEC-0011 amendment, effectively), OR drop the promise and convert it to
"will be documented inline at graduation time." Recommendation: defer — write the ADR when Phase 3 actually starts.
**Why it matters:** Promises in core docs that never materialize compound into doc debt; either deliver or rescind.

#### T2-3. ROADMAP.md Phase 2 explicit non-goal "Memory beyond session history" contradicts DEC-0028

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/ROADMAP.md`
**Location:** Lines 235–243, "Explicit non-goals for Phase 2."
**Before:** Lists "Memory beyond session history" as a Phase 2 non-goal.
**After:** Delete this line. Memory is now an explicit Phase 2 deliverable (Phase 2h, DEC-0028, plus Layer C substrate
already shipped per PR #35). The line is a left-over from the pre-2026-05-03 memory-pillar promotion.
**Why it matters:** Internal contradiction between ROADMAP Phase 2 (2h block lists memory as deliverable) and the
non-goals list (says memory is out of scope). The lower-line non-goals block won the older battle and was never updated.

#### T2-4. ROADMAP.md Phase 1d Worker model list doesn't reflect 2026-05-18 calibration

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/ROADMAP.md`
**Location:** Lines 105–117 (Phase 1d Dan task suite section).
**Before:** Describes "Ollama+Qwen3 (best available for hardware)" without committing to a specific model.
**After:** Add a parenthetical: "(empirical finding 2026-05-18: qwen3:8b is the practical Worker ceiling on 32 GB
M1 Max; qwen3.6:27b swap-thrashed at the 600s timeout on all three current tasks — documented in
`docs/specs/2026-05-18-dan-manual-tasks.md` task E3 and `docs/session-summaries/2026-05-18-...` once Dan files it)."
**Why it matters:** Empirical data point that future planning must respect (informs DEC-0033 / DEC-0034 spike).

#### T2-5. README.md license section says "TBD" — recently surfaced as Dan task C4 (open ADR DEC-0065 seed)

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/README.md`
**Location:** Lines 149–152 (License section).
**Before:** "TBD. Default intent: permissive open source..."
**After:** Either leave as-is (it accurately reflects the unresolved-decision state) or refine to:
"TBD — see `docs/specs/2026-05-18-dan-manual-tasks.md` task C4 for the resolution path (new ADR DEC-0065 seed).
Default intent: permissive open source." Recommendation: add the breadcrumb so a curious reader knows where the
decision lives.
**Why it matters:** Low — the TBD is honest. The breadcrumb is courtesy.

#### T2-6. GLOSSARY.md "Worker" entry says "currently Qwen3" without the 2026-05-18 calibration

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/GLOSSARY.md`
**Location:** Line 13 (Worker definition).
**Before:** "A local model (currently Qwen3 — best available for 32 GB M1 Max hardware, served via Ollama)."
**After:** "A local model (current practical Worker: `qwen3:8b` (FP16) on 32 GB M1 Max, served via Ollama;
`qwen3.6:27b` swap-thrashed on 2026-05-18 calibration and is non-viable as currently configured)."
**Why it matters:** CLAUDE.md (line 72) already carries this calibration; GLOSSARY.md should match.

#### T2-7. GLOSSARY.md "DEC-NNNN-reproducibility-bundle" + "DEC-NNNN-skill-md-conformance-linter" + "x402-mcp" entries reference seeded-but-not-authored ADRs

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/GLOSSARY.md`
**Location:** Lines 153–158 (reproducibility-bundle), 156–158 (SKILL.md conformance linter), 163–164 (x402-mcp).
**Before:** GLOSSARY entries point at "Seeded ADR DEC-NNNN-..." labels for three pending ADRs.
**After:** Cross-check against DEC-0058 (x402-mcp graduation pathway) which IS authored — the x402-mcp seed has
been promoted. The other two (reproducibility-bundle, SKILL.md conformance linter) are still seeds per DECISIONS.md
"Seeded ADRs" section (lines 85–97). Update the x402-mcp entry to point at DEC-0058 directly; leave the other two
as-is.
**Why it matters:** Tracks ADR seeds to their resolution; otherwise GLOSSARY drifts.

#### T2-8. SAFETY.md autonomy tier description doesn't reflect MCP / fastmcp tool-substrate decision (DEC-0018, DEC-0045)

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/SAFETY.md`
**Location:** Lines 19–80 (autonomy tiers); particularly the Tier 1 sandboxed writes section.
**Before:** Tier 1 lists `linus.fs.write`, `linus.shell.run_sandboxed`, etc. — Linus-namespaced tools without
explicit MCP framing.
**After:** Add a one-line note up-top: "Linus tools (Linus-namespaced; surfaced via the Linus-native MCP server per
DEC-0018 + DEC-0045) carry tier policy at the registry level; external MCP server tools are subject to the same
allowlist/blocklist when wired in."
**Why it matters:** SAFETY.md is read by every Worker that issues tool calls; the MCP framing changes the boundary
of where policy applies. Lower urgency because the current text isn't *wrong*, just incomplete.

#### T2-9. SAFETY.md Section "KnowledgeBase → hosted-Maestro flow policy" duplicates DEC-0053 content without cross-referencing the ADR

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/SAFETY.md`
**Location:** Lines 287–298.
**Before:** Restates the hosted-ok / hosted-forbidden policy without naming DEC-0053 explicitly until the parenthetical.
**After:** Tighten — the policy IS DEC-0053; lead with the ADR reference, then summarize.
**Why it matters:** Minor; the content is correct, the framing could be cleaner.

#### T2-10. ARCHITECTURE.md "Open architectural questions" lists items that have moved to resolved (DEC-0028–DEC-0043) but doesn't reflect Phase 2h shipped state

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/ARCHITECTURE.md`
**Location:** Lines 324–335.
**Before:** Lists "Long-term memory design: resolved (DEC-0028–0043). Layer D and beyond in Phase 3." Doesn't reflect
that Layer C substrate is now shipped.
**After:** Add "Phase 2h Layer C substrate (SQLite + content hashing + audit log) shipped via PR #35 (2026-05-16)."
or move the entry out of "Open architectural questions" entirely.
**Why it matters:** This section is supposed to be a live snapshot of unresolved architectural questions; if a question
is closed AND shipped, it doesn't belong on the open list.

#### T2-11. ARCHITECTURE.md Phase-2 implementation phasing list says "trust-tier tagging on all context items" under sandbox

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/ARCHITECTURE.md`
**Location:** Lines 301–317 (Phase 2 implementation phasing).
**Before:** "Sandbox: policy enforced, allowlist/blocklist live, trust-tier tagging on all context items."
**After:** Verify: the SandboxFS shipped in PR #50 enforces read/write boundary but does NOT do trust-tier tagging.
Trust-tier tagging is referenced in DEC-0053 (hosted-ok / hosted-forbidden) for KB content; the sandbox doesn't
tag arbitrary context items. Either rewrite this line to match what's shipped, or add a "(Phase 2h+ deliverable —
ships with the KB adapter's hosted-ok tagging)" qualifier.
**Why it matters:** The line conflates two different tagging surfaces (KB content trust-tier per DEC-0053 vs. sandbox
output trust-tier which doesn't exist yet).

#### T2-12. BRANCHING.md examples reference `experiments/<task-id>.md` for Worker specs — but most current specs live in `docs/specs/`

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/BRANCHING.md`
**Location:** Lines 96–101 ("Worker workflow" step 1), 299–308 (Scenario 2 example).
**Before:** "Maestro writes a spec in `experiments/<task-id>.md` or `docs/specs/<task-id>.md`"; later example uses
`experiments/kb-sync.md`.
**After:** The lived practice as of 2026-05-18 is to author specs in `docs/specs/<date>-<slug>.md` — `experiments/`
holds throwaway artifacts. Update the BRANCHING.md examples to reflect that specs live in `docs/specs/`. Keep
"throwaway in experiments/" for spike-style work.
**Why it matters:** New Workers reading BRANCHING.md will follow the example; the example writes to a location
inconsistent with current practice. The maestro-worker-protocol.md spec also points at `docs/specs/`.

#### T2-13. README.md acknowledgments line says "see docs/repo-notes/ (Phase 1+)" — Phase 1 is in progress, the notes exist

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/README.md`
**Location:** Line 158.
**Before:** "Every repo in `repos/` and their authors — see `docs/repo-notes/` (Phase 1+) for per-repo credit"
**After:** Drop "(Phase 1+)" — the 117 repo-notes exist today.
**Why it matters:** Tiny nit; same staleness class as T1-4 / T1-5.

#### T2-14. GLOSSARY.md "Linus" entry's example fine-tuned model name doesn't match recent practice

**File:** `/Users/dbrowne/Desktop/Programming/GitHub/Linus/GLOSSARY.md`
**Location:** Line 8.
**Before:** 'eventual fine-tuned model (e.g., "Linus-Qwen-7B-v1" as a LoRA-adapted Qwen base)'
**After:** Consider updating to reflect current ceiling: 'e.g., "Linus-Qwen3-8B-v1"' — small change for accuracy.
**Why it matters:** Cosmetic; flags the model-name space for future agents.

---

### Tier 3 — Reservoir / nice-to-have

#### T3-1. CLAUDE.md "Known Library Quirks" — accumulating worth a thematic pass

The Known Library Quirks section has grown to ~10 entries. A future pass could re-group by category (Ollama, prettier,
mdlint, page cache, env, GitHub PR mechanics) for grep-ability. Low priority.

#### T3-2. ARCHITECTURE.md component diagram in ASCII art is showing its age

The ASCII diagram on lines 56–85 hasn't been updated since Phase 0; the components match the spec but the cosmetic
boxes could be tightened. Cosmetic.

#### T3-3. VISION.md "Maestro/Worker discipline" mentions five-tier orchestra metaphor

The "Composer + Conductor / Section leaders / Musicians" metaphor is rich but reading it cold (without context) is
overdetermined. Consider tightening — but this is taste, not staleness.

#### T3-4. README.md does not mention Anthropic-compat HTTP

Once DEC-0056's `/v1/messages` endpoint lands (v2 N3), the README quick-start should mention it. Defer until N3 ships.

#### T3-5. GLOSSARY.md "External projects referenced" list could split into "active reference" vs "archived" subgroups

With 22+ entries, a two-tier split would aid grep. Low priority.

#### T3-6. SAFETY.md "Hardware safety" section is unchanged since Phase 0

Thermal / disk / battery guidance is fine but generic. As Linus actually runs training workloads (Phase 6), this
section should be revisited with empirical limits.

#### T3-7. BRANCHING.md has no mention of worktree discipline

The BRANCHING.md doc and CLAUDE.md's "Worktree fan-out discipline" sit in different files. Once PR #59 lands and
CLAUDE.md's worktree paragraphs stabilize, consider extracting a `docs/protocols/worktree-protocol.md` and cross-
referencing from BRANCHING.md.

#### T3-8. ROADMAP.md Phase 6 model candidates list is slightly stale

The line "Later-phase model candidates for fusion/flash-inference experiments: Kimi K2, DeepSeek V3, Llama 4 Scout"
is OK but as of 2026-05-18 there are 27 syntheses worth of additional fine-tuning candidates. Defer until Phase 5
planning starts.

#### T3-9. DECISIONS.md "Seeded ADRs" list (lines 85–97) lists 4 seeds; some have been promoted

Cross-check: DEC-0058 (x402-mcp graduation pathway) is the promoted form of seed #3 "agent-monetization-via-x402-mcp."
Remove from the seed list; the others (reproducibility-bundle, skill-md-conformance-linter, agent-identity-venue) are
still genuinely unauthored.

---

## Remediation recommendations (priority order)

1. **T1-1 / T1-2** — Add DEC-0055 row to DECISIONS.md and docs/adr/README.md. Cheapest, blocks nothing else; ~2-minute
   edit per file.
2. **T1-3 / T1-4 / T2-13** — Update README.md status block + quick-start. Visible to GitHub front page; ~5-minute edit.
3. **T1-5 / T1-6** — Refresh ROADMAP.md Phase 1 + Phase 2 status snapshots. Single coordinated edit; ~15 minutes.
4. **T1-7 / T1-8 / T2-10 / T2-11** — Refresh ARCHITECTURE.md to reflect shipped Phase 2a state + DEC-0056 dual protocol.
   Single coordinated edit; ~20 minutes.
5. **T2-3** — Drop "Memory beyond session history" from ROADMAP.md Phase 2 non-goals. Same edit pass as T1-6.
6. **T1-9 / T1-11** — Reconcile CLAUDE.md ADR enumeration with PR #60's final state. Verify after PR #60 merges.
7. **T1-10** — SAFETY.md `docs/incidents/` reference: add a one-line clarifier (no directory pre-creation needed).
8. **T2-1 / T2-7 / T3-9** — VISION.md DEC-0057 breadcrumb + GLOSSARY x402-mcp → DEC-0058 + DECISIONS seeds cleanup.
   Bundle as a small follow-up commit; ~10 minutes.
9. **T2-6 / T2-12 / T2-14** — GLOSSARY Worker calibration + BRANCHING.md spec-location examples + Linus-Qwen3-8B name.
   Small cosmetic batch.
10. **T2-2** — Resolve Phase 3 gitflow ADR forward reference (defer to Phase 3 start).
11. **Tier 3 items** — Reservoir; revisit at next quarterly curation review (2026-08-01).

## Confidence assessment

**High-confidence findings** (text/state mismatch, mechanical fixes): T1-1, T1-2, T1-3, T1-4, T1-5, T1-6, T1-7, T2-3,
T2-13, T3-9. These are pure factual errors or staleness — the corrective edits are mechanical and require minimal
judgment.

**Medium-confidence findings** (require Maestro/Dan judgment on framing): T1-8, T1-9, T1-10, T1-11, T2-1, T2-2, T2-4,
T2-7, T2-8, T2-9, T2-10, T2-11, T2-12. These are real misalignments but the right fix depends on how much the core doc
should embed the new ADR / how much should stay at high level. Recommend Maestro pick the framing per doc.

**Lower-confidence / taste calls**: All Tier 3 items, plus T2-5 (license breadcrumb), T2-6 (Worker calibration in
GLOSSARY — could argue this belongs only in CLAUDE.md), T2-14 (Linus-Qwen3-8B example). Reasonable people could disagree
on whether to apply these now or wait.

**Specifically NOT audited** (per scope guard): the CLAUDE.md content overlapping with PRs #57, #58, #59, #60. T1-9 and
T1-11 are written to compose cleanly with PR #60's compression; verify after merge.

**Methodology limitation**: spot-checked the synthesis layer (memory-synthesis, agentic-systems-synthesis,
infra-foundations-synthesis indices via the total-landscape rollup) but did not read every synthesis cover-to-cover.
Findings drawn from the rollup may miss niche claims; the rollup itself is dated 2026-05-16 and Tier 1 + Tier 2 items
above all anchor on independently-verified state (ADR files, git log, src/linus/ filesystem).
