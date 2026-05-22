# 2026-05-22 — Doc consistency audit (syntheses + landscapes) for v0.5.0 reveal

**Scope:** 15 thematic syntheses + 12 cluster syntheses (g1–g12) + 4 landscape docs, audited against current
`src/linus/` reality and DECISIONS.md through DEC-0061. Selection bias: high-signal items only; reveal is in two days.

**Headline finding.** Most syntheses were written before the 2026-05-19 MVP wave that landed
`/v1/messages`, `paperqa.py`, `rigor.py`, the Streamlit landing UI, `/healthz` degradations, the
tool `registry.py`, and DEC-0059/0060/0061. The biggest single class of staleness is "Anthropic-compat is the next
deliverable" and "paper-qa is the next step" — both shipped. Three brand-new ADRs (grounding gate, loud degradation,
network policy) are invisible to the synthesis corpus. One landscape link is broken. Style is uniform; the doc-type
conventions hold.

---

## 1. Stale claims

| File:line | Excerpt | Suggested fix | Severity |
|---|---|---|---|
| `docs/syntheses/agentic-systems-synthesis.md:410` | "The Anthropic-compat surface per DEC-0056 is the immediate next deliverable" | "The Anthropic-compat surface per DEC-0056 shipped 2026-05-19; `/v1/messages` is live in `src/linus/server.py` alongside `/v1/chat/completions`." | block-reveal |
| `docs/landscapes/total-landscape.md:393–394` | "Phase 2a FastAPI bootstrap (PR #32) lands the OpenAI side; the Anthropic side is the next Phase 2a deliverable." | Mark CLOSED with the shipping PR; both sides live. | block-reveal |
| `docs/landscapes/total-landscape.md:410–411` | "The Anthropic-compat surface (DEC-0056) is the immediate follow-on." | Same as above — flip to CLOSED. | block-reveal |
| `docs/landscapes/total-landscape.md:419–420` | "First DEC-0044 paper-qa integration is the next step." | paper-qa is integrated as `src/linus/knowledge/paperqa.py` exposing four Linus tools (`paperqa.search/gather_evidence/answer/reset`); flip to CLOSED with shipping PR. | block-reveal |
| `docs/landscapes/total-landscape.md:424` | "The Layer C substrate per DEC-0029 is implemented; Worker-dispatch integration is the next step." | Verify against current `src/linus/memory/sessions.py` + `episodic.py`; sessions are now wired into the chat-completions surface. | nice-to-fix |
| `docs/syntheses/repo-clusters/g8-sci-agents.md:130–136` | "**paper-qa adoption pathway.** The adoption decision is resolved: DEC-0044 ... If acceptable, expose as a Linus tool in Phase 2c." | Replace "If acceptable, expose as a Linus tool in Phase 2c" with "Now shipped as `src/linus/knowledge/paperqa.py` exposing four Linus tools." | block-reveal |
| `docs/syntheses/repo-clusters/g8-sci-agents.md:278–283` | "**Phase 2 — Linus MVP.** ... `fhaviary` ships transitively with paper-qa; `ldp` is explicitly NOT pulled in ..." | Add a sentence: "Landed: see `src/linus/knowledge/paperqa.py`." | nice-to-fix |
| `docs/syntheses/repo-clusters/g8-sci-agents.md:313` | "_Resolved (DEC-0044, `docs/specs/kb/paper-qa-substrate-integration.md`): paper-qa adopted as the Phase 2c ..._" | Append "shipped 2026-05-21 as `linus.knowledge.paperqa`." | nice-to-fix |
| `docs/syntheses/security-synthesis.md:282` | "Model extraction via the OpenAI-compatible endpoint. Once Linus exposes an HTTP endpoint (Phase 2+), anyone who can..." | Strike "Once Linus exposes" — the endpoint is live. Rephrase to present tense; the risk surface is real now. | nice-to-fix |
| `docs/syntheses/security-synthesis.md:472, 514` | "When the OpenAI-compatible endpoint is exposed..." | Present tense; auth model is the open question, not exposure. | nice-to-fix |
| `docs/syntheses/security-synthesis.md:91, 134, 337, 478` | "Remove Phase 3+ dependencies from environment.yml ... streamlit ... convenience chat UI for Phase 2" | Streamlit is now the Linus landing UI (`src/linus/app/main.py`) — keep it, don't recommend removal. Rephrase 478 as a description of what shipped rather than a "worth asking" hypothetical. | nice-to-fix |
| `docs/syntheses/entrepreneurship-synthesis.md:291` | "satellite consumes Linus services through the future OpenAI-compatible endpoint (DEC-0005) once Phase 2 ships" | Strike "future" / "once Phase 2 ships" — Phase 2a shipped. | nice-to-fix |
| `docs/syntheses/repo-clusters/g6-mcp-tools.md:44` | "DEC-0044: paper-qa as Phase 2c KB retrieval-and-synthesis engine, the first..." | OK as-is, but adding "(now shipped as `linus.knowledge.paperqa`)" would unify with §1 fix above. | nice-to-fix |
| `docs/syntheses/repo-clusters/g8-sci-agents.md:197–200, 282` | "aviary's `Tool.from_function` as the Linus tool registry standard. ... Adopt aviary's `Tool.from_function` pattern for the Linus tool registry in Phase 2a — it is..." | Add a parenthetical: "Landed: `src/linus/tools/registry.py` provides `@tool` decorator + `ToolRegistry`." | nice-to-fix |
| `docs/syntheses/repo-clusters/g2-wiki-engines.md:131, 248` | "...is exactly the problem Linus's Phase 2a tool registry faces" / "...tool registry Linus needs in Phase 2a" | Phase 2a tool registry shipped; rephrase in past tense or add "(now shipped — see `src/linus/tools/registry.py`)". | nice-to-fix |
| `docs/landscapes/total-landscape.md:359` | "PreCompact-hook-style 'capture critical state before lossy compression' pattern. Phase 2 deliverable. **OPEN.**" | Verify against `src/linus/memory/sessions.py` — may still be open; if so leave, if not flip. | aspirational |
| `docs/syntheses/agentic-systems-synthesis.md:326, 408` | "The tool registry should ship..." / "`src/linus/server.py` now ships an OpenAI-compatible FastAPI bootstrap..." | Update to reflect both endpoints + the shipped tool registry. | nice-to-fix |

**Crucially missing from all syntheses + landscapes:** DEC-0059 grounding gate (rigor.py + paperqa.py auto-gate), DEC-0060
loud degradation (`/healthz` `effective_state` + `degradations[]`), DEC-0061 network-policy framework. The
`grounding gate`, `loud degradation`, and `network_policy` phrases produce zero matches in `docs/syntheses/` or
`docs/landscapes/`. These are public-reveal load-bearing claims about what Linus is. Recommend a brief paragraph in
`docs/landscapes/total-landscape.md` ("New 2026-05-19+: Quality + safety surface — DEC-0059/0060/0061") plus a
one-sentence pointer from `safety-alignment-privacy-synthesis.md` and `security-synthesis.md`.

---

## 2. Factual errors

| File:line | Excerpt | Reality check | Severity |
|---|---|---|---|
| (None of the canonical pmetal/private-API class.) | — | The 2026-05-16 wave-2 audit fix held: `g1-apple-silicon.md:91` correctly states "M4's Neural Engine via reverse-engineered private APIs — methodology reference only, not vendored. pmetal staying on opposite sides of the public/private API line." `llm-wiki-synthesis.md:365, 387` references ANE/Maderix correctly as reverse-engineering. No drift detected. | — |
| `docs/syntheses/security-synthesis.md:134, 337` | "Delete `langchain`, `langgraph`, `streamlit`, and `lm-eval` from environment.yml" | Streamlit is now the production landing UI (`src/linus/app/main.py`). The blanket "delete" recommendation is factually wrong now and would mislead a reveal-week reader who follows it. | block-reveal |
| `docs/landscapes/paper-landscape.md:6` | "its navigation function moved to [`docs/papers/INDEX.md`](../papers/INDEX.md)" | `docs/papers/` does not exist; index is at `docs/paper-notes/INDEX.md`. (See §5.) | block-reveal |

No other CLAUDE.md-contradicting claims surfaced. Apple-private-API discipline is intact across all 27 synthesis files.

---

## 3. Redundancy (high-signal only)

Three syntheses repeat the paper-qa adoption decision in roughly the same shape:

- `repo-clusters/g8-sci-agents.md` §130–140 (the canonical pathway with the 5-paper smoke test)
- `entrepreneurship-synthesis.md` §171–196 (paper-qa as literature-intelligence engine in the Phase 7 stack)
- `repo-clusters/g6-mcp-tools.md` §44 (paper-qa as the first FastMCP-shaped Integrate)

This is mostly orthogonal — each angle adds something (technical, commercial, MCP-shape). The redundancy that a public
reader would notice is the **"Phase 2c" phasing label**: now that paper-qa has shipped, three docs all gesture toward a
Phase 2c future that is the present. One pass replacing "Phase 2c" with "shipped 2026-05-21" across these three would
remove the visible redundancy. Severity: nice-to-fix.

No other doubled content rises to the "public reader would notice" threshold. The cross-synthesis cluster anchors (e.g.
`memory-synthesis.md` ↔ `repo-clusters/g4-memory.md`, `agentic-systems-synthesis.md` ↔ `repo-clusters/g11`) are
intentionally paired and labelled as such.

---

## 4. Style drift (visible-to-reader only)

- **References discipline holds.** All 15 thematic + 12 cluster syntheses end with `## References` (per PR #55
  convention). Nothing to fix.
- **H2 ordering is consistent** for repo-cluster docs (Cluster summary / Headline findings / Patterns and modules
  worth lifting / etc.). No visible drift.
- **One paper-note doc-type quirk worth noting (not in this audit's scope but cross-cuts):** the paired-repo-variant
  filename convention (e.g. `Letta-2310.08560.md`, `Kimi-K2-2507.20534.md`) is correctly applied at the link layer in
  syntheses. No fix needed.
- **No frontmatter issues observed** on the 27 audited files (they don't carry frontmatter — paper-notes do; this
  matches CLAUDE.md's convention).

---

## 5. Broken cross-links

| Link target (relative) | Found in | Status | Suggested fix |
|---|---|---|---|
| `../papers/INDEX.md` | `docs/landscapes/paper-landscape.md:6` | **Missing** — `docs/papers/` directory does not exist. Index lives at `docs/paper-notes/INDEX.md`. | Rewrite to `../paper-notes/INDEX.md`. |

Spot-checked the rest of the relative-link surface (146 unique relative `*.md` targets across syntheses + landscapes;
see `/tmp/all_links.txt` working set). All paper-note, repo-note, ADR, and cross-synthesis links resolve. Subdirectory
specs (`../specs/2026-05-09-context-foldin-fanout.md`, `../specs/biology-phase7-roadmap.md`,
`../specs/memory-architecture.md`, `../specs/qimeng-category-promotion.md`) and protocol links
(`../protocols/maestro-protocol.md`) all exist on disk. The only confirmed break is the one above.

(Note: did not exhaustively crawl every `[..]( )` form; sampled across all 27 syntheses + 4 landscape docs by directory
prefix. If a fuller pass is wanted, a `markdown-link-check` run would catch any in-prose links missed by the regex
sample.)

---

## 6. Triage for reveal (ranked, <60 min total)

**Must-fix before reveal (block-reveal — ~25 min total):**

1. Fix broken `../papers/INDEX.md` link in `docs/landscapes/paper-landscape.md:6` → `../paper-notes/INDEX.md`. (1 min)
2. Update `agentic-systems-synthesis.md:410` from "immediate next deliverable" to "shipped". (2 min)
3. Update `total-landscape.md:393–394, 410–411, 419–420` to flip Anthropic-compat and paper-qa from "next step" to
   CLOSED with PR refs. (5 min)
4. Update `repo-clusters/g8-sci-agents.md:130–140, 278–283, 313` paper-qa adoption from "If acceptable, expose..." to
   "Now shipped as `linus.knowledge.paperqa`." (10 min)
5. Soften `security-synthesis.md:91, 134, 337, 478` Streamlit removal recommendation — Streamlit is the production
   landing UI. Replace with a description of the shipped surface + the still-open auth question. (5 min)
6. Add a 2–3 sentence "Quality + safety surface" paragraph to `total-landscape.md` Wave-2-stragglers block citing
   DEC-0059 (grounding gate), DEC-0060 (loud `/healthz`), DEC-0061 (network policy). The reveal narrative needs these
   to be visible somewhere a reader will encounter them. (5 min)

**Should-fix if time (nice-to-fix — additional ~25 min):**

7. Tool-registry "Phase 2a" present-tense fixes in `repo-clusters/g8-sci-agents.md:197–200, 282` and
   `repo-clusters/g2-wiki-engines.md:131, 248` and `agentic-systems-synthesis.md:326`.
8. Strike "future" / "once Phase 2 ships" in `entrepreneurship-synthesis.md:291`.
9. Update Layer C / Worker-dispatch integration status in `total-landscape.md:424` if integration is now done.

**Defer (aspirational):**

10. A full "new ADR cross-pollination" pass — adding DEC-0059/0060/0061 references throughout
    `safety-alignment-privacy-synthesis.md`, `security-synthesis.md`, and the relevant question-resolution lines
    everywhere — is a multi-hour rewrite. The minimum-viable fix is item 6 above; the comprehensive fold-in is
    post-reveal work.
11. PreCompact-hook deliverable status verification in `total-landscape.md:359`. Low public-visibility surface.
12. A `markdown-link-check` sweep for any links missed by the regex sample.

**Net assessment.** The corpus is structurally healthy — conventions hold, no factual drift on the Apple-private-API
class, References discipline uniform. The visible-to-reader risk is concentrated in ~6 stale "Phase 2 will" / "next
deliverable" phrasings and one broken link, all in landscape + agentic-systems + g8-sci-agents + security. A focused
30-minute pass clears the block-reveal items; the rest can wait.
