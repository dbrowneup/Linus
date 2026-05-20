# Linus + KnowledgeBase Reveal Demo Script — 2026-05-25 Agora Hackathon

**Status:** draft. Dry-run iteratively before 2026-05-25.
**Audience:** Agora hackathon attendees seeing Linus (+ KB + Archimedes) for the first time.
**Time target:** 5 minutes for the core path; 10 minutes with the deeper walkthrough.

---

## Pre-demo checklist (run morning of)

Do not start the demo without confirming each:

- [ ] `ollama list` shows at least `qwen3:8b` pulled and the Ollama service running (`brew services list | grep ollama`).
- [ ] `python -c "import linus"` from `(linus)` env succeeds with no errors.
- [ ] `linus-serve` starts cleanly; landing page renders without errors.
- [ ] `curl http://localhost:8000/healthz | jq` returns `effective_state: "live"` and `degradations: []`. If
  degraded, address the listed degradation BEFORE the demo. (`paper-qa` papers_dir is the likely culprit —
  set `LINUS_PAPERQA_DIR` to a directory containing at least 3 papers from `context/papers/`.)
- [ ] `streamlit run src/linus/app/main.py` opens to the landing page with all KB artifacts shown ✅.
- [ ] Three pre-warmed paper-qa queries from §"Demo path" below run end-to-end without errors. Don't trust
  cold-start latency.
- [ ] `repos/pmetal/target/release/pmetal --version` returns `pmetal 0.5.0`.
- [ ] Network is on (paper-qa over local Ollama doesn't need it, but the landing GitHub link does).

If anything in this checklist fails, **fix it before the demo, don't apologize during**.

---

## Demo path — the 5-minute happy path

### Opening (30 sec)

> "Linus is a private, local AI orchestration backend for Apple Silicon. It runs on my MacBook Pro — no
> cloud, no paid API. The point is to give scientists like me Claude-equivalent capabilities under our own
> control, plus domain-specific tools backed by our own knowledge corpora."

Show: `github.com/dbrowneup/Linus` README in the browser. The "What this is" + "What's shipped (v0.5.0)"
sections do the heavy narrative lifting.

### Beat 1 — Honest health (45 sec)

Open `http://localhost:8000/healthz` in browser. Show the JSON:
- `effective_state: "live"` — green.
- `degradations: []` — empty.

> "The server reports honestly when it's degraded, not just when it's down. If my preferred model isn't pulled, or my paper-qa directory is missing PDFs, the
> `/healthz` endpoint says so — with an actionable `remediation` field telling you exactly the command to
> fix it. Silent failures are a category of bug we've designed out."

Optional flourish: open a second terminal, `mv ~/.linus/papers/ ~/.linus/papers.bak/`, refresh /healthz —
show the degradation appearing. Then restore. (Only do this if you trust the restore step.)

### Beat 2 — KnowledgeBase pages (90 sec)

Open Streamlit landing. Click through pages quickly:
- Page 1 Chat — "Linus speaks OpenAI- and Anthropic-compatible APIs. Any harness — Claude Code, openclaw,
  LM Studio — plugs in."
- Page 3 Cluster Explorer — "The KnowledgeBase submodule has clustered my 19,000-PDF corpus. Drill down:
  Broad → Mid → Fine."
- Page 4 Paper Graph — "Paper similarity in 2D and 3D, Sigma.js and force-directed."
- Page 5 Knowledge Graph — "REBEL + SciSpacy entity-relation triplets across the corpus. A real KG over
  what I've actually read."

Each one is a glance, not a deep dive — the point is breadth at this stage.

### Beat 3 — The marquee: paper-qa with citations (2 min)

Open Streamlit Page 7 (Paper QA).

Question to ask: **"What does the literature say about Botryococcus braunii oil productivity under
nitrogen limitation?"**

(Pre-warmed; ~10-15 sec wall time for the model. If the model is slow, narrate while waiting:
"Local Ollama; M1 Max; no API; the model is qwen3:8b running on Metal.")

When the answer renders:
- Read 1-2 sentences of the answer aloud.
- Expand the "Citations" panel. Point at the citation list — paper_id + page + excerpt + score per entry.
- > "This is the marquee feature. Citation-grounded synthesis, 100% local. Every claim in the answer
>    traces back to a paper actually in my corpus."

Optional second query: **"What gene families are involved in B. braunii squalene biosynthesis?"** — shorter,
more entity-rich.

### Beat 4 — The rigor gate (60 sec)

Open a terminal. Run:

```python
python -c "
from linus.knowledge.rigor import check_grounding, BuiltinEntityLookup
from linus.knowledge.adapter import KnowledgeBaseAdapter
import json
claim = json.loads(open('demo_claim.json').read())
papers = KnowledgeBaseAdapter()  # real KB
entities = BuiltinEntityLookup()  # v0.5.0 stub
result = check_grounding(claim, papers=papers, entities=entities)
print(json.dumps({
    'passed': result.passed,
    'failures': [{'kind': f.kind, 'severity': f.severity, 'detail': f.detail} for f in result.failures],
    'confidence_calibration': result.confidence_calibration,
}, indent=2))
"
```

(Have `demo_claim.json` prepared with a valid claim + one deliberately fabricated paper_id so the gate
shows a real `unresolved_citation` error.)

> "Workers can fabricate. Linus refuses fabrication at the orchestration boundary. This is what catches a
> hallucinated citation before it lands in a manuscript draft."

Note for narration: the entity backend in v0.5.0 is a stub; the v0.6.0 backend pulls from KB's own
REBEL+SciSpacy outputs so entities are validated against the corpus, not enumerated by hand. **Be honest
about this**: it's a known gap with a clear roadmap.

### Closing (30 sec)

> "Linus is 413+ hermetic tests, ~2.5 seconds. Released today. The companion KnowledgeBase ships at the
> same time. The third project, Archimedes, releases publicly today as well — a coordinated trio.
> They're not separate things; they're the same idea expressed in three surfaces — orchestration,
> knowledge, and q-fin strategy. Linus is what a scientist's private AI looks like when it stays under
> their control."

Point at the three GitHub URLs:
- `github.com/dbrowneup/Linus`
- `github.com/dbrowneup/KnowledgeBase`
- `github.com/dbrowneup/Archimedes` (TBD URL — confirm before demo)

---

## Demo path — the 10-minute version (additions)

If audience is engaged + time allows:

### Beat 5 — Multi-front-end (60 sec)

Open VS Code with Claude Code extension. Show `claude` slash command pointing at
`http://localhost:8000/v1/chat/completions` instead of Anthropic's. Same prompts work.

> "Any OpenAI- or Anthropic-compatible client plugs in. Linus is the orchestration backend; the front-end
> is interchangeable. VS Code, openclaw, LM Studio, a future native app — all the same Linus."

### Beat 6 — pmetal (45 sec)

Terminal:
```
~/Desktop/Programming/GitHub/Linus/repos/pmetal/target/release/pmetal --help
```

> "This is pmetal — LLM fine-tuning optimized for Apple Silicon. Linus's training-stack sibling. Today's
> Workers come from Ollama; tomorrow's come from pmetal-fine-tuned-on-my-corpus. The reveal here is the
> v0.5.0 binary just landed alongside Linus."

### Beat 7 — Architecture flyover (90 sec)

Open `ARCHITECTURE.md` in browser, show the diagram. Walk through:
- Front-ends (any client) → HTTP →
- Linus orchestration layer (FastAPI server, MCP tool registry, sandbox, memory pillar, audit log) →
- Inference / Knowledge / Training (Ollama, KB submodule, pmetal/mlx-lm).

> "The orchestration layer is the product. Harnesses come and go; the orchestration layer accrues value."

---

## Known-fragile moments (don't trigger these on stage)

- **paper-qa first-call latency** — first query of a session can take 30+ seconds while paper-qa builds its
  embedding index. **Pre-warm before the demo** with the same queries you'll demo.
- **Streamlit page rerun on slider change** — moving the `max_sources` slider re-fires the page. Don't touch
  it mid-demo.
- **The `download` subcommand on pmetal** — actually pulls from HuggingFace. Don't run during demo; show
  `--help` only.
- **The Streamlit chat page** — if Ollama is mid-update or briefly unresponsive, the chat panel shows an
  error. Have a fallback to skip the chat-page beat.

---

## Post-demo hooks

If audience asks "what's next":

- **v0.5.1 (week of 2026-06)** — `entity_kb.py` lookup against KB's KG (replaces stub backend).
- **v0.6.0** — manuscript-polish workflow at `docs/specs/manuscript-polish-workflow.md` operationalized.
- **v0.7.0+** — agent spawner, parallel multi-Worker fan-out, fine-tuning via pmetal on the local corpus.

If audience asks "why local-only":

- "Privacy. Cost. Latency. Control. None of those are negotiable for the work I want to do."

If audience asks "is this Claude":

- "Claude is the Maestro I drive Linus with. Linus is the Worker substrate I drive locally. They're
  complementary — the Maestro/Worker discipline is in CLAUDE.md and VISION.md."

If audience asks "can I use it":

- "It's MIT-licensed today, with the KnowledgeBase submodule pulling in AGPL via PyMuPDF. So yes — fork
  it, run it, but understand the AGPL implications if you redistribute. README has the details."
