# docs/session-summaries/

Date-prefixed recaps of significant Maestro sessions. Each captures pre-execution context, numbered execution steps,
lessons learned (write-back candidates for the core docs), outstanding items for next session, and suggested next
steps. The session summary is the canonical handoff artifact between sessions when compaction or session boundaries
might otherwise lose context.

## Convention

Filename: `YYYY-MM-DD-<slug>-session-summary.md`.

Section order (per CLAUDE.md):

- `## Pre-execution context`
- Numbered `## Step N — <name>` for each major execution phase
- `## Lessons learned (write-back candidates)` — H3 per destination doc (CLAUDE.md, VISION.md, ROADMAP.md, etc.)
- `## Outstanding items for next session`
- `## Suggested next steps`

A closing line records "estimated wall time vs. actual" per the §"Measure, don't just estimate" discipline.

## Why these matter

Session summaries are the most-cited inputs to subsequent planning sessions — Maestro reads the last 1-3 summaries when
opening a new session to reconstruct context that wasn't durably written to ADRs or specs. The "lessons learned" sub-
structure routes write-backs to the right destination doc so improvements compound across sessions instead of being
re-discovered.
