# Synthesis Open-Questions Cleanup Spec

**Date:** 2026-05-07 **Status:** in execution as of this commit **Owner:** Maestro (Dan + Claude Code)

**Related:** [`docs/questions/answered-questions.md`](../questions/answered-questions.md);
[`docs/questions/top-questions.md`](../questions/top-questions.md); ADRs DEC-0001 through DEC-0054.

---

## Goal

Reduce stale-question noise across the 25 synthesis documents (14 thematic in `docs/syntheses/` + 11 cluster in
`docs/syntheses/repo-clusters/`) by replacing every question that has been resolved during the 2026-05-03 →
2026-05-07 planning arc with a one-line "resolved" stub pointing at the resolving ADR or `answered-questions.md`
anchor. Questions that remain open are left as-is.

Most syntheses' open-questions sections were written before DEC-0044 through DEC-0054 landed and before the Sweep
S1–S60 + Entrepreneurship E1–E12 backlog was cleared. As a result, many of those question texts are now stale: they
ask about decisions that were made one or more sessions ago. The current document set has the right answers
elsewhere; the sweep brings the syntheses into alignment.

---

## Resolution policy (Dan's choice 2026-05-07: option B)

For each question identified as resolved, replace the question text with a one-line stub of the form:

```
- _Resolved (DEC-NNNN, see [answered-questions.md#anchor](../questions/answered-questions.md#anchor)): <one-line summary>._
```

Where:

- `DEC-NNNN` is the ADR (or list of ADRs) that resolved the question.
- The link is to the answered-questions.md anchor for the question's S-id, M-id, or E-id.
- `<one-line summary>` is the resolution in 5–15 words.

If a question was resolved without an ADR (e.g., a Tier 0 dependency cleanup or a planning-update-spec deliverable),
omit the DEC reference and use:

```
- _Resolved (see [answered-questions.md#anchor](../questions/answered-questions.md#anchor)): <one-line summary>._
```

Questions that remain open are left untouched.

Option (A) "delete outright" was not chosen because preserving the visible per-synthesis question history makes each
synthesis self-contained as an audit document — a reader can see what was asked at synthesis time, what got resolved,
and how to find the resolution without round-tripping through `answered-questions.md`.

---

## Scope and execution mode

**Scope.** All 25 syntheses. Twelve carry an explicit `## Open questions` section (the 11 cluster syntheses plus
`entrepreneurship-synthesis.md`); the remaining thematic syntheses carry questions inline within their analysis
sections and are reviewed for the same resolution-stub treatment where applicable.

**Execution mode.** Maestro direct (Dan's choice 2026-05-07), single PR, sequential walk through the syntheses. The
prior session's Worker fan-out attempt was blocked at the bash step for six of eight agents; the canary-probe
discipline (CLAUDE.md "Agent fan-out: probe permissions first") would catch this, but the cleanup is mechanical
enough that direct Maestro execution is the lower-overhead path here. ~2 hours of Maestro time at typical pace.

**Output.** A single PR `agent/synthesis-cleanup-sweep` containing the cleanup deltas across the 25 syntheses. Each
synthesis edit is small (a handful of lines per section). The PR diff per file should be readable as
question-text-replaced-by-resolution-stub plus minimal surrounding wording adjustments.

---

## Execution rules

For each synthesis:

1. **Read the open-questions section** (and any inline-question paragraphs noted in the structure).
2. **Cross-reference each question** against:
   - The DEC-NNNN ADR list (1–54).
   - `docs/questions/answered-questions.md` (the resolution archive).
   - `docs/specs/planning-update-spec.md` Audit summary (DONE list).
3. **For each resolved question**: replace the question text with the resolution stub per the policy above.
4. **For each still-open question**: leave it.
5. **For each question whose status is uncertain** (e.g., it sounds resolved but the resolution isn't crisply
   documented): leave it open and surface the ambiguity in this spec's "Surfaced ambiguities" section below.
6. **No new content** is added beyond the resolution stubs. No restructuring. No renaming sections. No prose rewrites
   beyond the exact swap.
7. **Anchor format**: when linking to an `answered-questions.md` anchor, use the auto-generated GitHub markdown
   anchor convention (lowercase, hyphens for spaces, special characters dropped). Verify the anchor exists by
   searching the file before committing if unsure.

---

## Surfaced ambiguities

The cleanup ran 2026-05-07 across the 12 cluster + thematic syntheses with explicit "Open questions" sections. Twelve
questions across six syntheses had clear ADR or planning-doc resolutions and were converted to one-line stubs.
Several other questions are visibly resolved at a coarse level but the implementation specifics remain open; these
were left intact rather than partially-stubbed:

- **g4-memory** open questions (5) are all implementation-level choices about substrate adoption (openaugi schema
  verbatim vs. extended; sqlite-vec vs. Qdrant for v0; trust-level binary vs. weighted). DEC-0029 governs the
  substrate at the architectural level but does not pin these choices. Left open.
- **g6-mcp-tools** "Stdio or streamable-http from Phase 2 launch?" sits inside the resolved DEC-0045 fastmcp
  adoption but the transport choice is an implementation detail. Left open as guidance for Phase 2a.
- **g7-harnesses** "Open Responses versus Chat Completions?" — Phase 2a serving-protocol choice; Phase 2 ships
  OpenAI-compatible (DEC-0005) but the Open Responses spec is a separate decision. Left open.
- **g7-harnesses** "Origin as memory sidecar?" — memory-architecture.md is now the spec; whether `origin-server`
  is a Phase 2b candidate sidecar is implementation evaluation, not yet captured. Left open.
- **g8-sci-agents** "Biology RLVR verifier candidates" — Phase 6 scope question requiring Dan's domain judgment.
  Left open.
- **g11-agent-frameworks** all 5 open questions are Phase 2a implementation choices (pydantic-ai dependency,
  Worker review gates, Dan task suite grader design, OTel storage, context-routing policy). Left open.
- **entrepreneurship E3, E4, E5, E7, E8, E9, E10** are mix of strategic/empirical/process items that haven't been
  decisionally closed. Left open.

The unresolved items are correctly characterized as open in their syntheses; the cleanup specifically targeted
items that were resolved-but-not-yet-marked-resolved.

---

## Verification

Before the PR is opened:

- `grep -rn "S\d\+\|M\d\+\|E\d\+" docs/syntheses/` to confirm every numeric question marker has been either replaced
  with a resolution stub or left intact (no orphans).
- `git log main..HEAD --stat` shows only synthesis files plus this spec file plus
  `docs/session-summaries/synthesis-cleanup-session-summary-2026-05-07.md` if added.
- `git log HEAD..main --stat` is empty.
- L1/L2 discipline (CLAUDE.md state-verification + cherry-pick-to-preserve) applied.

---

## Status (filled at execution time)

- 2026-05-07: spec written.
- 2026-05-07: cleanup executed (see PR for the per-synthesis diff and the Surfaced ambiguities section above).
