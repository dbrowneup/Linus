## DEC-0060 — Loud degradation: `/healthz` reports `effective_state` + `degradations[]`

**Date:** 2026-05-19 **Status:** accepted

**Context.** The pre-2026-05-19 `/healthz` endpoint reported a binary `ollama_reachable` flag plus the
locally-pulled model list and registered tool names. That surface covers **live vs. down** but is silent on
**live vs. degraded** — the operationally costly middle state where the server is reachable but cannot fulfill
its primary contracts because a prerequisite (a preferred model, a papers directory, a KB artifact bundle) is
missing. The 2026-05-19 Archimedes cross-pollination conversation flagged this: Archimedes wired its pipeline
into a request path with a `/health` endpoint reporting live-vs-degraded(canned) explicitly, making silent
failure impossible. Linus had analogous failure modes — worker-model fall-through from `qwen3:8b` to
`qwen2.5-coder:7b`, paper-qa tools registered but the papers directory absent, KB Streamlit pages dead because
`hierarchy.json` etc. are missing — and they were invisible until a tool call errored at invocation time.

**Decision.** Extend `/healthz` with two additive fields, never breaking pre-existing keys:

- **`effective_state ∈ {"live", "degraded", "down"}`** — a coarse one-word verdict. `live` = no failures.
  `degraded` = warning-severity failures only. `down` = any error-severity failure or Ollama unreachable.

- **`degradations[]`** — a list of structured records, each
  `{component, expected, actual, severity, remediation}`. The `remediation` field is a one-line **actionable**
  command or env-var set ("Run: `ollama pull qwen3:8b`", "Set `LINUS_PAPERQA_DIR` to a directory containing
  PDFs") — not vague guidance.

v0.5.0 ships four detection modes, all implemented in `_compute_degradations()` in `src/linus/server.py`:

1. **`worker_model`** — cross-references `_MODEL_PREFERENCES` against `_list_local_models()`. First-preference
   missing → `warning`. NO preference available → `error`.
2. **`papers_dir`** — resolves `LINUS_PAPERQA_DIR` / `LINUS_PAPERS_DIR` / `~/.linus/papers/` per
   `src/linus/knowledge/paperqa.py`. Missing or contains zero PDFs → `error`. Paper-qa tools will fail at
   invocation; surfacing here avoids the round-trip.
3. **`kb_outputs`** — checks the artifact bundle (`hierarchy.json`, `labels_broad.json`, metadata DB,
   embeddings) that `src/linus/app/main.py` already surfaces. Each missing artifact → `warning` (Streamlit
   pages handle gracefully; the user can still use chat / paper-qa).
4. **`ollama_models_empty`** — Ollama reachable but zero models pulled → `error`.

The Streamlit landing page renders the degradations as a five-column table (Component / Expected / Actual /
Severity / Remediation) below the existing Reachable/Unreachable status block, so operationally significant
problems surface to the user the moment the page loads.

**Backwards compatibility.** All five pre-existing `/healthz` keys (`status`, `ollama_reachable`, `models`,
`default_model_preference`, `tools`) retain their identical semantics. Clients that ignore the new fields see
no change. The decision is purely additive.

**Severity convention.** `error` means "a primary contract is broken" — e.g., the chat endpoint will 503
because no model resolves, or paper-qa tools will throw at invocation. `warning` means "fallback path engaged,
the server still serves" — the next-preference model is loaded, or a Streamlit page that needs an artifact
will render an inline-fallback message. The user-facing UI surfaces both, but the `effective_state` rolls
warnings into `degraded` and errors into `down`, preserving a single coarse signal for callers that just want
a binary go/no-go.

**Why now.** Q3 of the Archimedes cross-pollination eval, scoped into v0.5.0 because (a) it extends an
endpoint that's already on the demo path for the 2026-05-25 Agora hackathon reveal, (b) the Streamlit landing
display is the polish-visible payoff, and (c) every failure mode it surfaces is a real Linus failure mode
today, not a hypothetical.

**Consequence.** Operationally costly silent failures are no longer silent. The Streamlit landing's
"Reachable" indicator stops swallowing partial outages. The `effective_state` field gives downstream callers a
canonical degradation signal to wire alerting / fallback logic against. The pattern is extensible — adding a
new detection mode is one entry in `_compute_degradations()` plus a hermetic test stubbing the relevant
source; no protocol change. Future endpoints exposing their own `effective_state` follow this shape.

**References.**

- Source: `src/linus/server.py` (`_compute_degradations`, `/healthz`); `src/linus/app/main.py` (degradations
  table).
- Tests: `src/linus/tests/test_healthz.py` (22 hermetic tests covering each detection mode + composition +
  backwards-compat + actionable remediation).
- 2026-05-19 Archimedes cross-pollination conversation (Q3) — proposal, eval, scoping into v0.5.0.
- [DEC-0059](0059-grounding-gate-output-surface.md) — sibling Archimedes cross-pollination outcome (Q1).
