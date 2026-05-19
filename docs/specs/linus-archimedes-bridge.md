# Linus ↔ Archimedes Bridge Spec

> **Date:** 2026-05-19. **Status:** v1, post-MVP-build.
> **Audience:** Archimedes teammates (Marten, Daniel R., Chuan, Önder)
> wiring Linus into Archimedes without involving Dan or Maestro day-to-day.

Linus's Phase 2a MVP exposes three primitives Archimedes can lift directly:

1. **Anthropic-compatible HTTP endpoint** (`POST /v1/messages`) — drop-in
   target for any `anthropic.Anthropic(base_url=...)` client.
2. **`papers.ingest_arxiv` MCP tool** — turn an arXiv ID into a paper
   passport (PDF + metadata + embedding) cached locally.
3. **QFinCorpus** — a dedicated quant-finance KnowledgeBase instance
   browseable via the Linus Streamlit UI, growable via the seeder
   script.

Plus two server primitives the Archimedes Claude session flagged as
Tier 1 / Tier 2 to lift wholesale:

4. **RAG gateway contract** (`linus.knowledge.KnowledgeRetriever`) — the
   research-grounded retrieval interface; copy the typed shape verbatim
   even when the implementation differs.
5. **Agent spawner contract** (`linus.agents.spawn_agents`) — N parallel
   scoped Worker calls merged into ordered results; the strategy-fusion
   engine.

This doc is the integration contract for each. Code references point at
the current Linus tree under `src/linus/`. **Linus is not hosted** — it
runs on Dan's MacBook at `http://localhost:8000`. Archimedes integration
is "Dan starts Linus, Archimedes hits localhost" — see § "Out of scope"
for what's deliberately not provided.

---

## 1. Anthropic-compatible endpoint

Linus speaks the Anthropic Messages API at `POST /v1/messages`,
implementing DEC-0056. The official `anthropic` Python SDK works against
it without code changes — only the `base_url` differs.

### Minimal client example

```python
import anthropic

client = anthropic.Anthropic(
    base_url="http://localhost:8000",
    api_key="not-used",  # Linus doesn't enforce auth in v1
)

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",   # ignored — Linus resolves locally
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello Linus"},
    ],
)
print(response.content[0].text)
```

The `model` field is honored if the named Ollama model is locally pulled;
otherwise Linus falls back through `qwen3:8b` → `qwen2.5:14b` →
`qwen2.5-coder:7b`. If none are available, HTTP 503 surfaces the available
model list — fail loud, never silent swap.

### Streaming

`stream=true` currently returns HTTP 501 (per the PR #71 v1 scope). The
non-streaming form works today; streaming lands in a follow-up that
shares plumbing with the OpenAI streaming work in PR #72.

### What Linus drops in v1

- Tool advertisement via `/v1/messages` — use `/v1/chat/completions` (OpenAI shape) for tool routing
- Multi-block content beyond `type=text` (images, tool_use, tool_result blocks are silently dropped)
- Auth — the `api_key` field is accepted but not validated

### Failure modes

| HTTP | Cause | Body |
|---|---|---|
| 400 | empty `messages`, only-system messages | string detail |
| 422 | missing required field (Pydantic validation) | OpenAPI-style error |
| 501 | `stream=true` | `{"error": "streaming_not_implemented", "message": "..."}` |
| 503 | Ollama unreachable / no preferred model pulled | model list + install hint |
| 502 | Ollama returned an error | propagated message |

---

## 2. `papers.ingest_arxiv` tool

A Linus tool registered as `linus.papers.ingest_arxiv` on the default
tool registry. Callable two ways:

**A. Via the OpenAI tool-call surface** (`/v1/chat/completions` with
tools): the model can call it during a reasoning step.

**B. Direct Python import** (Archimedes co-resident on the same machine):

```python
from linus.tools.arxiv_ingest import ingest_arxiv

passport = ingest_arxiv("2310.02601")
# passport = {
#   "arxiv_id": "2310.02601",
#   "title": "...",
#   "authors": [...],
#   "abstract": "...",
#   "year": 2023,
#   "category": "q-fin.PM",
#   "sha256": "<64 hex>",
#   "pdf_path": "/Users/.../.linus/papers/2310.02601.pdf",
#   "passport_path": "/Users/.../.linus/papers/2310.02601.json",
#   "embedding_path": null,   // or path to .npy when SPECTER2 is installed
#   "ingested_at": <epoch>,
# }
```

### Cache layout

`~/.linus/papers/` (override via `LINUS_PAPERS_DIR` env var). Per paper:

- `<id>.pdf` — raw bytes
- `<id>.json` — passport (the dict above + `ingested_at`)
- `<id>.npy` — SPECTER2 embedding when sentence-transformers + the
  `allenai/specter2_base` model are installed; absent otherwise

Idempotent: cached passports return directly on re-invocation.

### Failure modes

All failures land as `{"error": "<code>", ...}` records — the tool never raises:

| Code | Cause |
|---|---|
| `invalid_arxiv_id` | Input doesn't match `NNNN.NNNNN` (with optional version) |
| `arxiv_api_failed` | arxiv.org/api timed out or returned 5xx |
| `arxiv_api_parse_failed` | Atom XML malformed |
| `pdf_download_failed` | arxiv.org/pdf returned non-2xx (with `status_code` field) |

Plus best-effort warnings (passport still ships):

- `pypdf_unavailable` — text extraction skipped (install pypdf)
- `specter2_unavailable` — embedding skipped (install sentence-transformers)
- `extraction_failed: <type>: <message>` — pypdf raised

---

## 3. QFinCorpus — quant-finance KnowledgeBase instance

`modules/QFinCorpus/` is a dedicated KB data root scoped to q-fin
arXiv papers, separate from Dan's personal biochem/AI corpus. Curated
by Dan via `scripts/qfin_arxiv_seed.txt` (one arxiv ID per line) and
populated via `scripts/seed_qfin_corpus.py`.

### Pointing a consumer at it

The Linus Streamlit UI (Cluster Explorer, Search, etc.) reads its KB
artifacts from `LINUS_KB_OUTPUTS_DIR` (B.0 env-var contract). To browse
QFinCorpus instead of the default:

```bash
export LINUS_KB_OUTPUTS_DIR=$PWD/modules/QFinCorpus/data/outputs
streamlit run src/linus/app/main.py
```

For programmatic consumers (Archimedes' strategy-passport pipeline,
say): point any KB-output reader at the same dir. Reading `metadata.db`
via `linus.knowledge.KnowledgeBaseAdapter`:

```python
from linus.knowledge import KnowledgeBaseAdapter
from pathlib import Path

kb = KnowledgeBaseAdapter(db_path=Path("modules/QFinCorpus/data/metadata.db"))
hits = kb.search_papers("momentum factor", limit=10)
```

### Adding papers

Edit `scripts/qfin_arxiv_seed.txt`, then re-run `seed_qfin_corpus.py`.
The seeder is idempotent. After ingest, re-run the KB pipeline to
regenerate clusters / graphs / embeddings (see `modules/QFinCorpus/README.md`).

---

## 4. RAG gateway contract (Tier 1 lift)

`linus.knowledge.KnowledgeRetriever` is the canonical contract for
research-grounded retrieval. v1 Linus ships keyword search only;
semantic and graph methods raise `NotImplementedError` with documented
install pointers. **The contract is frozen; copy it verbatim.**

```python
from linus.knowledge import (
    KnowledgeBaseAdapter,
    KnowledgeRetriever,
    RetrievalResult,
    RetrievalHit,
)

retriever = KnowledgeRetriever(KnowledgeBaseAdapter())
result: RetrievalResult = retriever.retrieve(
    "momentum factor portfolio construction",
    top_k=20,
    methods=None,  # None = use all available; explicit list to restrict
    weights=None,  # override default fusion weights per call
)

for hit in result.hits:
    print(hit.score, hit.provenance, hit.paper.title)
```

### Why the contract matters even with a thin impl

- **Provenance per hit**: `hit.method_scores` tells the consumer
  exactly which methods contributed; the reasoning trace can cite
  retrieval evidence by method.
- **Stable shape**: Archimedes can build its strategy-grounding logic
  against `RetrievalHit.paper` (a `Paper` dataclass) and `RetrievalHit.score`
  without coupling to Linus's specific impl. Swap SPECTER2 for a
  Voyage embedding in Archimedes — the consumer code doesn't change.
- **Fusion configurable**: per-call `weights={"keyword": 0.3, ...}`
  lets Archimedes tune retrieval per use case without forking.

### What Archimedes might do differently

The Linus impl is the v1 minimum. Archimedes could:

- Replace `KnowledgeBaseAdapter` with a metadata-DB shim over its own
  `paper_corpus` Postgres table
- Implement the `_semantic` method with Voyage / OpenAI embeddings
  instead of SPECTER2
- Add a fourth method (`fundamentals` — pull from a financial data API)
  by extending the `RetrievalMethod` literal

All of this is purely additive against the same surface.

---

## 5. Agent spawner contract (Tier 2 lift)

`linus.agents.spawn_agents` is a minimal async function: take N
`AgentTask` records, fire them in parallel bounded by a concurrency
limit, return the merged `AgentResult` list in input order with
per-task failure isolation.

```python
import asyncio
from linus.agents import AgentTask, AgentResult, spawn_agents

tasks = [
    AgentTask(name="momentum",       system="Generate a momentum strategy from these papers.", user="..."),
    AgentTask(name="mean-reversion", system="Generate a mean-reversion strategy.",              user="..."),
    AgentTask(name="vol-managed",    system="Generate a vol-managed strategy.",                  user="..."),
]
results = asyncio.run(spawn_agents(tasks, concurrency=4))

for r in results:
    if r.error:
        print(f"{r.task_name}: FAILED — {r.error}")
        continue
    print(f"{r.task_name}: {r.latency_ms}ms via {r.model_used}")
```

### Why this is the engine of Archimedes's novelty pitch

The four-control selection-bias gate (DSR / PBO / walk-forward OOS /
look-ahead audit) needs MANY candidate strategies to discriminate
between. Generating one candidate per LLM call is the baseline; the
spawner lets Archimedes generate N candidates in parallel from
differently-scoped prompts and feed them all into the rigor gate. **The
spawner is what makes "Archimedes Verified 🏆" a discriminating label
rather than a rubber stamp.**

### What v1 doesn't carry

- No KV-cache continuity across tasks (each task = fresh model call)
- No mid-task tool calls
- No streaming per-task output
- No dependency graphs between tasks (parallel-only, not a DAG)

All of these are the Phase 3 agent-spawner spec (DEC-0050). The v1
contract is the bare primitive Archimedes can prototype against today.

---

## How Archimedes wires it (concretely)

### Step 1: Start Linus locally

```bash
cd ~/Desktop/Programming/GitHub/Linus
conda activate linus
uvicorn linus.server:app --reload   # localhost:8000
```

### Step 2: Pick the integration points

- **Anthropic SDK paths**: change `base_url` in your client construction
- **Direct Python**: add `submodules/Linus/src` to PYTHONPATH or pip-install
  the Linus package (`pip install -e .` from the Linus root) and import
  `linus.knowledge.KnowledgeRetriever` / `linus.agents.spawn_agents` /
  `linus.tools.arxiv_ingest`
- **HTTP-only path** for non-Python services: `POST /v1/chat/completions`
  or `POST /v1/messages` from any HTTP client

### Step 3: Decide your fallback posture

Linus is single-process on Dan's MacBook. If Dan reboots or Linus
crashes, Archimedes can't reach it. Your fallback options:

- **Cache + retry**: cache last-good responses, retry with exponential
  backoff on connection error
- **Hosted fallback**: route Anthropic-compat calls to the real
  Anthropic API on Linus-down, swap back on Linus-up
- **Degrade**: certain features (paper-ingest, fancy retrieval) are
  best-effort enhancements; the strategy-passport pipeline can ship
  with Linus-disabled stubs

The "hosted fallback" pattern is the same shape as Linus's own
model-resolution fallback chain — implement it once at the Archimedes
boundary.

---

## Out of scope (deliberately)

- **No hosted endpoint.** Linus runs on Dan's MacBook only. Anything
  that wants to call it from elsewhere needs a tunnel (Tailscale,
  Cloudflare Tunnel, etc.) you set up yourself, not part of Linus.
- **No auth.** The `api_key` field is accepted but ignored. Don't
  expose Linus to the open internet without putting it behind your
  own auth layer.
- **No TLS.** HTTP only. Tunnel adds TLS termination at the edge.
- **No multi-tenant isolation.** Single user (Dan). Sessions ARE
  isolated per `session_id`, but there's no per-user ACL.
- **No fine-tuning hooks yet.** Phase 6 of the Linus ROADMAP, not the
  MVP.
- **No production SLA.** Linus is Dan's personal tool. Treat it as a
  best-effort dev dependency, not a critical-path service.
- **No bumping `submodules/Linus` in Archimedes for you.** That's
  teammate coordination. Pin to whatever SHA Linus is at when you
  start; refresh on a schedule that suits the team.

---

## Amendment to land in `archimedes/CLAUDE.md`

The current text in `archimedes/CLAUDE.md` (last revised 2026-05-14) reads:

> **[`submodules/Linus/`](submodules/Linus/)** — Dan's personal AI
> orchestration project. **Reference only; nothing to port to
> Archimedes.** The `experiments/archimedes/` and
> `experiments/agora-hackathon/` directories contain the priors that
> seeded several of our current `docs/` files.

That stance evolved during the 2026-05-18 / 2026-05-19 MVP build. The
replacement text (paste-ready for the next Archimedes Claude session
to fold in):

> **[`submodules/Linus/`](submodules/Linus/)** — Dan's personal AI
> orchestration project, now the **nucleus** Archimedes builds around
> for research-grounded retrieval, paper ingest, agent spawning, and
> Anthropic-compatible LLM gateway. See
> [`docs/specs/linus-archimedes-bridge.md`](https://github.com/dbrowneup/Linus/blob/main/docs/specs/linus-archimedes-bridge.md)
> in the Linus repo for the integration contract. Lift the contracts
> verbatim; reimplement the impls behind them as Archimedes-specific
> needs emerge. The `submodules/Linus/experiments/archimedes/` and
> `experiments/agora-hackathon/` directories remain useful as priors
> for the deck + scope decisions.

---

## Versioning

This doc is v1, 2026-05-19. Update it (don't replace) when any contract
above changes. Linus's per-file ADRs in `docs/adr/` carry the deeper
"why"; this doc is the integration-facing surface.

For any contract change Archimedes consumers should care about, bump
the version line above and add a `### Changes since v<N>` section so
teammates skimming a refreshed copy can spot what moved.
