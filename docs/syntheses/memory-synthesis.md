# Memory Synthesis: The Pillar of Linus Intelligence

## What this document is

A synthesis of Erik Garrison's January 2025 essay "Memory makes computation universal, remember?" together with eleven
of the arXiv references it cites (now summarised one-pager-per-paper in [`paper-notes/`](../paper-notes/)), read
end-to-end through one question: _what is the memory architecture Linus needs to commit to in order to become a useful
local-first general assistant?_

The Garrison nucleus lives at
[`context/notes/garrison_memory_makes_computation_universal.md`](../../context/notes/garrison_memory_makes_computation_universal.md).
The eleven supporting notes are listed in the [Inputs](#inputs) section at the bottom. The synthesis is aimed at the
same audience as the existing [security](security-synthesis.md), [LLM Wiki](llm-wiki-synthesis.md), and
[skills](skills-and-practices-synthesis.md) syntheses — it is the input to a forthcoming round of edits to the landscape
documents, the questions documents, and the planning artifacts in `docs/specs/`.

The headline claim of this synthesis is that memory is not a feature roadmap item to be deferred until concrete use
cases surface. It is the load-bearing architectural pillar that _all the other pillars rest on_, and the eleven papers
reviewed here, from three different research traditions (complexity theory, post-Transformer architectures, and
frontier-model empirics), converge on that conclusion from independent angles. Phase 2 (Linus MVP) should not begin
without a memory architecture spec.

---

## Historical anchor: the memex, 1945

The argument is older than the corpus. In July 1945 Vannevar Bush, then director of the Office of Scientific Research
and Development, published [_As We May Think_](../../context/notes/As-We-May-Think.txt) in the _Atlantic Monthly_;
the September 10, 1945 _Life_ reprint
([Bush, "As We May Think", Life Magazine Sept 10 1945](../../context/pics/Bush-As-We-May-Think-Life-Magazine-9-10-1945.pdf))
carried the iconic illustrations — the desk-sized memex with its slanting translucent screens, the head-mounted walnut
camera, the trail-following levers — that fixed the device in the technical imagination. Bush's diagnosis of the
post-war scientific predicament reads as if it were written for the Garrison/Mughal thread eighty years later: a
"growing mountain of research," investigators "staggered by the findings and conclusions of thousands of other workers —
conclusions which [they] cannot find time to grasp, much less to remember," and methods of consultation that "are the
same as [were] used in the days of square-rigged ships." The bottleneck is not generation of new knowledge but reliable
access to the inherited record.

Bush's proposed substrate — the memex, "a device in which an individual stores all his books, records, and
communications, and which is mechanized so that it may be consulted with exceeding speed and flexibility... an enlarged
intimate supplement to his memory" — implements both Garrison universality criteria in 1945 typewriter-and-microfilm
terms. **Recursive state maintenance** is the desk's "transparent platen" and direct entry mechanism: the user inserts
longhand notes, photographs, and memoranda; "the depression of a lever causes it to be photographed onto the next blank
space in a section of the memex film." The state is durably read, augmented, and written back. **Reliable history
access** is the trail mechanism: any two items can be permanently joined by code, trails are named and indexed, "and his
trails do not fade." Years later, "a touch brings up the code book. Tapping a few keys projects the head of the trail."
Items are addressable, distinguishable, temporally ordered, and durable — the four sub-requirements Garrison's framework
spells out, exactly the obligations the Layer-A-through-E decomposition below is designed to satisfy.

The Bush vision sharpens what is and is not new in the corpus. The architectural claim that an intelligent worker
(scientist, lawyer, physician, chemist) cannot operate at the limit of their capability without an externalised,
addressable, associatively-linked memory substrate is older than the digital computer. What the eleven papers add is the
_formal proof_ that the diagnosis applies to transformer-class systems specifically (Garrison/Merrill & Sabharwal/Feng
et al.) and the _empirical evidence_ that current frontier models are operating without the substrate and visibly
degrading because of it (Kojima/Bubeck/Mughal). Linus is not inventing the memex. It is — eighty years on, with the
cheap-complex-devices-of-great-reliability that Bush could only forecast — building the version that runs on Apple
Silicon for one Oregonian biochemist's scientific record.

---

## The unifying thesis

Garrison's two-line argument, distilled from the [arXiv proof paper (2412.17794)](../paper-notes/2412.17794v1.md):
universality requires only **(1) recursive state maintenance** (the system can read state, apply an update, and durably
keep the new state) and **(2) reliable history access** (it can reference any prior state, distinguish states
unambiguously, maintain temporal order, and guarantee integrity). Theorem 1 of that paper proves any system meeting both
simulates a Universal Turing Machine with at most logarithmic overhead.

Each of the eleven supporting papers turns out to be a different camera angle on the same statement. The
complexity-theory papers ([2310.07923](../paper-notes/2310.07923v5.md), [2305.15408](../paper-notes/2305.15408v5.md))
prove the formal impossibility result for single-pass transformers (TC0 ceiling) and the constructive escape via
chain-of-thought recursion (UTM-class reachable). The empirical prompting paper
([2205.11916](../paper-notes/2205.11916v4.md)) shows that the gap is not abstract: a single trigger phrase delivers a
17.7%→78.7% absolute jump on multi-step arithmetic. The capability survey ([2303.12712](../paper-notes/2303.12712v5.md))
shows what the architecture _can_ do and where it predictably fails, with Section 8 reading as a catalogue of
memory-deficit failure modes. The architectural alternatives ([2412.06769](../paper-notes/2412.06769v3.md),
[2410.01201](../paper-notes/2410.01201v3.md), [2411.07279](../paper-notes/2411.07279v2.md)) each present a different
substrate that satisfies the recursive-state-maintenance requirement — latent continuous reasoning, parallel-trainable
minimal recurrence, test-time parametric updates. The wall-of-attention case study
([2102.05095](../paper-notes/2102.05095v4.md)) shows the quadratic ceiling in a non-text domain. The scaling-laws paper
([2203.15556](../paper-notes/2203.15556v1.md)) and the Llama 3 herd paper ([2407.21783](../paper-notes/2407.21783v3.md))
demonstrate that even the optimally-scaled and best-engineered frontier models still bolt chain-of-thought, retrieval,
or 128K context windows onto the same wall — they push it back, they do not remove it. The ARC-AGI 2024 retrospective
([2412.04604](../paper-notes/2412.04604v2.md)) shows the most expensive empirical proof of the same claim: the only
approaches that crossed the human-baseline line in 2024 (test-time training, deep-learning-guided program synthesis, and
o3's compute-rich parallel search) are all _external memory mechanisms grafted onto amnesiac base models_.

The eleven papers do not agree on a recipe. They agree on a diagnosis. **Capability is bottlenecked by memory
architecture, not by parameter count, training data, or attention engineering tricks.** That is the sentence the rest of
this synthesis unpacks.

A practitioner-side anchor on the same finding lands from the opposite direction. Ayesha Mughal's March 2026 piece
[_Why Claude Gets Dumber the Longer Your Session Runs_](../../context/notes/Why-Claude-Gets-Dumber-the-Longer-Your-Session-Run.txt)
documents the operational degradation visible inside a single hosted-Claude session — the same architectural deficit,
observed at the keyboard rather than proved on paper. Her mechanism is two-part: "lost in the middle" attention
degradation (instructions buried under hours of tool output get weighted a fraction of what they were when fresh) and a
real-vs-nominal token budget (a 200K nominal window in which performance starts measurably degrading around 147K, with
system prompts, tool schemas, and MCP servers already consuming 30K–50K before the user types). Where Garrison argues
from complexity theory why amnesiac architectures cannot escape TC0, Mughal documents how the same gap shows up as
drift, contradiction, and forgotten decisions inside a session that nominally has plenty of room left. The two
perspectives reinforce each other; the rest of this synthesis treats them as one finding seen from two angles.

---

## The three camera angles

### Angle 1: complexity theory — the formal ceiling and the formal escape

Two papers in the corpus carry the formal load. The earlier Merrill & Sabharwal "parallelism tradeoff" line (TACL 2023;
not in the corpus, but cited by both notes here) proved that a standard log-precision decoder-only transformer producing
its answer in a single forward pass lives inside the circuit class **TC0**. That class is informally "what fast,
massively parallel pattern matching can do in a fixed number of layers." It cannot count past a circuit-encoded
threshold, simulate an arbitrary finite-state machine on long inputs, decide directed graph connectivity, or recognise
balanced parentheses at unbounded depth. No amount of training data, parameter count, or RLHF moves a single-pass
transformer outside this class. The wall is in the model class, not in the size.

[Merrill & Sabharwal 2024 (2310.07923)](../paper-notes/2310.07923v5.md) extends that result by characterising what
scratchpad steps add. With logarithmic intermediate decoding steps the upper bound rises only to L (deterministic
logspace). With _linear_ steps the model recognises all regular languages and provably exits TC0. With _polynomial_
steps, a decoder-only transformer with strict causal attention and projected pre-norm recognises exactly P. The
construction is constructive: a "layer-norm hash" lets the transformer use its own previously generated tokens as an
addressable, content-distinguishable, temporally ordered store — in other words, the intermediate tokens _are_ the
maintained state, and strict causal attention _is_ the reliable history access.

[Feng, Zhang et al. 2023 (2305.15408)](../paper-notes/2305.15408v5.md) is the constructive twin from the opposite
direction. They prove that constant-size autoregressive transformers can solve arithmetic, linear equation solving, and
a broad class of dynamic programming problems via chain-of-thought derivation, while bounded-depth transformers of
polynomial size cannot solve any of them by direct prediction. The mechanism they isolate — _chain-of-thought raises
effective depth proportional to generation length_ — gives the formal reason why the empirical
"let's-think-step-by-step" trick works. Each emitted token is another L layers of computation applied to the
now-extended input. A constant-depth network running for n CoT steps commands O(n) effective depth.

Together these two papers make a sharp formal claim that maps directly onto Garrison's two requirements: intermediate
tokens implement recursive state maintenance, strict causal attention implements reliable history access, and the lift
from TC0 to P (or beyond, given enough steps) is exactly what universality looks like inside a transformer. **For Linus
this is the theoretical floor.** A Worker that produces its answer in one pass is, by theorem, a TC0 device; any task
requiring honest sequential reasoning has to be carried by intermediate tokens that the model can later attend over.
Truncating those tokens between turns — the o1 failure mode — collapses the Worker back toward TC0 on whatever residual
remains.

### Angle 2: empirical phenomena — the gap is real and visible at scale

[Kojima et al. 2022 (2205.11916)](../paper-notes/2205.11916v4.md) is the empirical anchor. A single trigger sentence
appended to a reasoning prompt — **"Let's think step by step"** — turns a frozen pretrained LLM into a competent
multi-step reasoner. On MultiArith, accuracy jumps from 17.7% to 78.7%. On GSM8K, from 10.4% to 40.7%. On Coin Flip,
from 12.8% to 91.4%. Three additional findings are critical for Linus design.

First, the gap is **emergent at scale**. Below roughly 60B parameters in the GPT-3 family, the trigger does essentially
nothing; above it, the gap opens dramatically. This is not a property of the trigger; it is a property of which models
have enough latent reasoning capacity to use the externalised state. For a Linus router dispatching to local
1B/3B/7B/14B Workers, this implies CoT-injection should be size-conditional — burning tokens on "let's think step by
step" with a 1B Worker is pure overhead, while suppressing it on a 7B+ Worker is leaving expressivity on the table.

Second, the gap is **task-class-conditional**. CoT helps on arithmetic, symbolic, and logical tasks; it is flat or
negative on commonsense reasoning where the bottleneck is world knowledge rather than chain length. Adopting
CoT-by-default for all Worker calls would slow latency, inflate token counts, and not help retrieval-shaped tasks. The
router needs a task-class signal, not a blanket policy.

Third, the gap is **trigger-sensitive**. Of 16 trigger variants tested in Kojima's Table 4, the spread within
"instructive" templates was 45.7%–78.7% on the same task. Treating any one trigger as magic without per-Worker
re-validation is cargo-culting that the paper itself warns against.

[Bubeck et al. 2023 (2303.12712)](../paper-notes/2303.12712v5.md) — the Sparks paper — extends the same picture
qualitatively. Sections 1–7 document remarkable transferred capability: the TikZ unicorn drawn from text alone, the
LeetCode 10/10 score, the bar-exam pass, the book-eggs- laptop-bottle-nail stacking puzzle. All evidence that exposure
to enough human writing internalises structured cognitive patterns — _state transition functions_ — that the model can
then evoke as latent skills. Section 8 is the symmetric existence proof: the same model fails on four-term integer
arithmetic (collapsing to 0% as digit counts grow), Tower-of-Hanoi with two disks, and any constraint-satisfaction task
requiring lookahead — exactly the failures Garrison's framework predicts from missing recursive state and reliable
history access. Most of those failures **recover dramatically when external scratchpad space is provided**. The
capability is latent; the architecture cannot evoke it without help.

The Sparks/Garrison/Kojima triangle is the mainspring of this synthesis. **Cognitive patterns transfer; memory does
not.** The orchestration layer exists to externalise what the model cannot internalise.

### Angle 3: substrate alternatives — what does memory done right look like?

If single-pass transformers are stuck in TC0 and chain-of-thought is the expensive escape (each extra step costs a full
forward pass through the network), what is the cheap escape? Three of the eleven papers each name a different candidate
substrate.

**Latent continuous reasoning.** [Hao et al. 2024 (2412.06769)](../paper-notes/2412.06769v3.md) — Coconut — feeds the
model's last hidden state back as the next input embedding instead of decoding to a discrete token. The recurrence
carries a real-valued vector rather than a sampled word, satisfying recursive state maintenance without the lossy detour
through token space. A single continuous thought can also hold a _superposition_ of candidate next steps because there
is no sampling step forcing a commitment, yielding an implicit breadth-first search across multiple latent positions.
Coconut is the cleanest published instance of "the carry between recurrence steps is a real-valued vector," and on
planning-heavy DAG-shaped reasoning (their ProsQA dataset), it outperforms language-space CoT while emitting fewer
tokens.

**Parallel-trainable minimal recurrence.** [Feng et al. 2024 (2410.01201)](../paper-notes/2410.01201v3.md) — "Were RNNs
all we needed?" — shows that stripping LSTM and GRU of every gate dependency on the previous hidden state and every
`tanh` range restriction yields **minLSTM** and **minGRU**, both parallelizable via prefix-sum (parallel scan), with
13–38% of the parameter count of their classical counterparts. The resulting architectures match Mamba and Transformers
on selective copy, RL benchmarks, and Shakespeare-scale language modelling, with 175–1361× faster training per step at
sequence lengths 512–4096. This paper is the most direct architectural pointer in the corpus to the path-forward section
of Garrison's blog: minimal-state recurrence reorganised for parallel training is what universality looks like at low
cost.

**Test-time parametric updates.** [Akyürek et al. 2024 (2411.07279)](../paper-notes/2411.07279v2.md) shows that fitting
a per-task LoRA adapter on a synthetic dataset built from the few-shot demonstrations of a single test task lifts an 8B
Llama from 5% to 29% on ARC (1B model) and from 45% to 53% (8B model), with ensembling reaching **61.9% — average human
performance**. Test-time training (TTT) writes the few-shot examples directly into a small set of adapter weights rather
than re-deriving them each forward pass. Garrison reads this as _another_ brute-force memory mechanism, structurally
adjacent to o3's parallel search but spending the compute on parameter updates instead. For Linus this is the most
plausible candidate for **episodic memory consolidation**: a session transcript becomes a transient LoRA adapter, stored
as a per-project memory module, loaded back when the project resumes.

These three substrates are not mutually exclusive. The interesting architectural question is not "which one wins" — they
answer different questions — but "which combination is the right substrate for which layer of Linus's memory pillar."

---

## The wall, in case the formal argument was not enough

Two papers make the cost of the no-memory path concrete and quantitative.

![The quadratic wall: attention cost vs. sequence length](../../context/pics/quadratic-wall.png)

[Bertasius, Wang & Torresani 2021 (2102.05095)](../paper-notes/2102.05095v4.md) is the wall-of-attention case study from
a non-text domain. TimeSformer's joint space-time attention literally runs out of memory on an A100 at 448-pixel crops
or 32-frame clips. The paper's contribution — _divided space-time attention_ — drops per-block cost from `(NF+1)`
comparisons per patch to `(N+F+2)` and pushes the wall back by a constant factor. It does not remove the wall; it simply
postpones the OOM. The pattern is exactly what Garrison flags for text transformers: factorisation tricks (sliding
window, sparse, axial, divided) are constant-factor escapes from quadratic attention while the structural fix — separate
state, recurrence with rolling hidden state, external addressable memory — remains the long-term answer.
**TimeSformer-L's "long-range" video at 96 frames is one minute forty seconds of footage.** That is not "long-horizon
memory" in any meaningful sense; it is episodic prediction with a slightly larger window.

[Llama 3 herd (2407.21783)](../paper-notes/2407.21783v3.md) is the high-water mark of the alternative bet — vanilla
dense Transformer + massive data + extended context window. The 405B was trained on ~15.6T tokens at ~3.8×10²⁵ FLOPs,
the 128K context window was bolted on via a continued-pre-training stage, and the 98.1 score on multi-needle-in-a-
haystack at 128K shows the simulation works. **But the simulation is the brute-force-memory-via-attention path
Garrison's framework critiques.** A gigawatt-class lab burning a 405B-parameter, 15.6T-token, multi-thousand- GPU run
still tops out at the regime Garrison flags as the architectural ceiling. The Llama 3 design is what scale can do when
memory is not treated as a separate component; it is a useful calibration point for what that approach costs and where
it stops.

[Hoffmann et al. 2022 (2203.15556)](../paper-notes/2203.15556v1.md) — the Chinchilla paper — sets the optimum _inside_
the parameter-and-data regime: across 400+ training runs, the compute-optimal scaling law says that for every doubling
of compute, double both the model and the data (N*opt ∝ C^0.5, D_opt ∝ C^0.5), with the verification model Chinchilla
(70B at 1.4T tokens) beating Gopher (280B at 300B tokens) at the same compute budget. The corollary the field
internalised: most pre-2022 large LMs were significantly undertrained. Read against Garrison's framing, this is what
\_optimal* looks like inside the bounded regime — and even Chinchilla still has to bolt chain-of-thought and retrieval
onto inference to do anything genuinely sequential. **Chinchilla is the right answer to "how should I spend a fixed
pretraining budget"; it is not an answer to "how do I escape the architectural ceiling."**

[ARC Prize 2024 (2412.04604)](../paper-notes/2412.04604v2.md) provides the most expensive empirical evidence for the
same conclusion. The state of the art on the private evaluation set jumped from 33% (2023) to 55.5% (MindsAI, end
of 2024) — a step change after five years of stagnation — driven by **test-time training and deep-learning-guided
program synthesis**, not by raw model scale. The ARChitects' open-source winner hit 53.5% with a NeMo-Minitron-8B +
heavy augmentation + stability-based selection. On the compute-rich Pub track, o3 reached 82.8% on 400 public tasks at
~$6,677 (~33M tokens) in high-efficiency mode and 91.5% at ~$1.15M (~9.5B tokens) at 172× more compute. **The 172×
compute premium for the last ~9 points is the price of buying memory reliability through parallel search.** Garrison
reads this as the negative existence proof for the framework: o3 nearly solved ARC-AGI, but at a cost that scales
linearly in compute because the underlying mechanism — search a forest of partial reasoning traces, retain only the
consistent ones — is doing what robust memory mechanisms do for free.

The wall is real, the cost of pretending it isn't is enormous, and the escape hatch (architectural memory) is what the
eleven-paper corpus collectively points to.

---

## What this means for Linus, in concrete architectural terms

The Garrison framework decomposes "memory" into two formal requirements (recursive state maintenance, reliable history
access) and four sub-requirements on the second (reference any previous state, distinguish unambiguously, maintain
temporal order, guarantee integrity). Mapped onto a Linus assistant, this lands as five practical layers (A–E), each
with a preferred substrate the corpus already names. The fifth layer — investigation memory (Layer D) — was added
2026-05-06 via DEC-0052, which inserted a task-scoped multi-agent shared-context layer between cross-session episodic
(Layer C) and semantic knowledge (formerly Layer D, now Layer E).

### Layer A — Intra-step latent state (within a single Worker forward pass)

This is the layer the Coconut paper opens up: the continuous reasoning carry inside a single inference call. Today, in
practice, this layer is whatever the underlying transformer's hidden state happens to be — opaque, discarded between
turns, never named. Linus does not need to adopt Coconut as an inference paradigm to benefit from naming this layer in
the architecture. **Naming it is the first move.** Without a name, the "continuous state being thrown away every time we
re-tokenize" is invisible to design.

For Phase 2, the practical commitment is small: when the orchestration layer dispatches to a Worker, document what
continuous state, if any, is preserved between consecutive Worker invocations on the same task. Default answer: none,
because the Worker emits tokens and the next call re-reads the transcript. That is fine, as long as it is _known_. Phase
6+ is where substrate experiments (Coconut-style latent recurrence, minGRU-style recurrent encoders, hybrid
transformer/SSM Workers) become tractable.

### Layer B — Within-session scratchpad memory (within one task, across model turns)

This is the layer the complexity-theory and CoT papers all live in. It is the memory mechanism that lifts a single
Worker call out of TC0 and into something universality-class. The architecture must commit to **scratchpad as a
first-class durable artifact**, not as ephemeral output.

The four sub-requirements from Garrison's framework map cleanly onto a session-store schema:

- _Addressability_: every reasoning trace, tool output, and intermediate artifact gets a turn id and a content hash.
  Replay is possible from any turn forward.
- _Disambiguation_: distinct turns produce distinct addresses even for near-duplicate content (content hash + turn id).
- _Temporal order_: monotonic timestamps + parent-pointer relationships between turns. Append-only.
- _Integrity_: hash chain, or git as the substrate, so corruption or loss is detectable.

The Kojima paper's two-stage pipeline (reasoning extraction → answer extraction) is the design pattern: store the
reasoning trace as one addressable record, the final answer as another, with explicit links between them. The Coconut
paper adds a refinement: where possible, retain _considered alternatives_, not only the realised chain — branch points
should be first-class entries.

What this rules out: any inference path that silently truncates reasoning prefixes between turns, summarises rather than
retains, or relies on the chat template's default truncation behaviour. The o1-forgets failure mode is not a quirk to
work around; it is a design failure that collapses expressivity.

Mughal supplies the operational evidence for the same point from the hosted-Claude side. Her measurements (citing SFEIR
Institute) put a marathon four-hour session at roughly 40–60% of fresh-session quality by hour three, while a
disciplined sprint-and-compact loop holds 80–85% across the same window. The difference is not the model and not the
task; it is whether scratchpad accumulation is being managed as a durable artifact with explicit preservation, or being
allowed to silt up the attention budget until correct instructions sink into the lossy middle. The architectural
commitments above — scratchpad as durable artifact, two-segment record per turn, explicit prohibition of the o1
truncation pattern — are exactly what makes the Linus-side equivalent of those mitigations possible. Without the
substrate, no compaction discipline can recover state that was never durably recorded.

### Layer C — Cross-session episodic memory (across sessions, days, projects)

This is the layer Linus's current architecture treats as deferred. The Garrison reading argues it should not be.
Cross-session episodic memory is the _outer scratchpad_ that does for the assistant-as-a-whole what within-session
scratchpad does for a single Worker call: lifts it out of TC0 by giving it durable history to attend over. Without it,
every session is an independent TC0 episode no matter how clever the inside-session scratchpad design is.

Three substrate candidates emerge from the corpus:

1. **Append-only structured store + content addressing.** The most conservative option — SQLite or a similar embedded
   store, with content hashes and metadata. Cheap, debuggable, easily satisfies all four sub-requirements.
2. **Git as episodic substrate.** Git is already an append-only, content-addressed, temporally ordered store with
   integrity guarantees. For sessions tied to repository work this is nearly free — Workers commit reasoning traces and
   tool outputs to a session branch as they work, and the episodic memory is the git history.
3. **TTT-style parametric consolidation.** From the Akyürek paper. At session end (or at quiet moments), fit a small
   LoRA adapter on the session's tuples. The session is consolidated into weights, not just into a transcript. The
   adapter becomes a per-project or per-domain memory module loaded back when the project resumes. This is the most
   ambitious option — it directly converts memory into the same substrate the model already uses — but also the most
   experimental, and per-task LoRA training is non-trivial on M1 Max.

These are not mutually exclusive. A reasonable Phase 2 starting position is (1) + (2) — durable structured records plus
git as the persistence layer — with (3) deferred to a Phase 3 or Phase 6 spike once the explicit store is operational
and the value of consolidation can be measured against it.

The CRISPR design hint from Garrison's blog is concrete here: recent context should be cheaper to access and more
aggressively consulted than ancient context, with mechanism for old context to remain reliably retrievable when needed.
That is a design pattern for retrieval ordering over the episodic store, not a separate substrate.

![CRISPR-as-memory analogy: ordered, append-only, recency-weighted retrieval](../../context/pics/crispr-memory.png)

Mughal's session-handoff file (`.claude/session-handoff.md` — written at session end with modified files, decisions and
their reasoning, current state, and the exact next step; read at session start) is the hosted-Claude analogue of what
the Linus episodic store provides natively. It is a volatile addressable artifact at the session boundary, captured
because nothing else in the hosted environment plays that role. The Linus equivalent is not a single overwritten
markdown file; it is an entry in the addressable episodic substrate, with the same payload (decisions, state, next step)
but stored as a first-class record alongside the session's reasoning traces and tool outputs. The hosted-Claude pattern
is a workaround for a missing layer; the Linus design treats that layer as infrastructure.

### Layer D — Investigation memory (task-scoped, multi-agent, single-investigation lifetime)

This layer was added 2026-05-06 (DEC-0052) when the agentic-systems synthesis surfaced a gap in the original four-layer
model: task-scoped shared context maintained across agents within one investigation — distinct from per-session
scratchpad (Layer B), archived episodic history (Layer C), and durable knowledge (Layer E). Three systems in the corpus
occupy this gap: Kosmos's world model (shared state across a full research investigation), Sketch2Simulation's
intermediate representation (passed between pipeline stages), and HKUST QuantAgent's context buffer (strategy +
reasoning log shared between planner and executor within one trading cycle). See the
[agentic-systems synthesis](agentic-systems-synthesis.md) for the corpus examples that motivated this layer.

The practical commitment for Linus: when a multi-agent fan-out spawns (Phase 3+), a shared investigation context is
created, all participating agents can read and write to it, and the context is archived to Layer C when the
investigation closes. Per DEC-0052, the substrate is a SQLite table in `~/.linus/investigations.db`, partitioned by
`investigation_id`, with a GC policy that archives investigations idle for 30 days. An `investigation_stateful`
memory-mode primitive is deferred to Phase 3; Layer D is not exposed in the Phase 2 router.

### Layer E — Semantic / knowledge memory (durable, shared, factual)

This is the layer KnowledgeBase already serves (renamed from Layer D to Layer E 2026-05-06 per DEC-0052). The Garrison
framing argues it is part of memory infrastructure, not a separate "RAG feature" — which has a concrete implication for
the orchestration layer: the same API shape should serve all five memory layers, with substrate variation hidden behind
it. A Worker should not care whether a piece of context came from its own scratchpad (Layer B), a prior session (Layer
C), an active investigation (Layer D), or the KnowledgeBase (Layer E) — all satisfy the same reliable-history-access
contract. Different layers have different decay rates and different authority levels, but the _shape_ of the read API is
uniform.

This is also where the [LLM Wiki synthesis](llm-wiki-synthesis.md)'s discipline (claim typing, content hashing,
write-back rule, contradiction policy) is most load-bearing. Layer E is where claims live longest and where ungrounded
synthesis does the most damage. Memory and knowledge-quality controls are the same controls.

---

## How memory rewrites the rest of the Linus plan

### The router gets two new axes

Today's implicit Worker dispatch question is "which model best handles this task?" The complexity-theoretic results add
two new axes:

- **CoT budget per call.** Per the Merrill & Sabharwal regimes (logarithmic / linear / polynomial scratchpad), the
  orchestration layer should set per-call reasoning-token budgets aligned to task expressivity demand. Algorithmic tasks
  (math, dependency resolution, multi-step planning) get linear or larger budgets with full retention; lookup-style
  tasks get logarithmic budgets with truncation. A "this task gets up to N decoding steps of scratchpad" knob is cheap
  to implement and exploits the linear-steps regime where it pays off.
- **Memory mode per call.** Some tasks are _stateless_ (single-turn classification, extraction). Some are
  _session-stateful_ (a coding task carried across many tool calls). Some are _project-stateful_ (resuming a multi-week
  investigation). The router should know which mode applies and load the appropriate prefix from the appropriate memory
  layer before dispatch.

Both axes are router _primitives_, not optimisations — adding them later is harder than building them in.

Mughal's MCP-schema budget discipline maps directly onto the same two primitives. Her observation that nine MCP servers
can consume 30K–50K of context before the user types — and that the right move is to disable servers a given task does
not need rather than load everything by default — is the practitioner-side restatement of "context is a budget, not a
capacity." `cot_budget` and `memory_mode` are the Linus-side knobs that enforce that discipline at the orchestration
layer: budget context per call, do not load by default. Her empirical numbers — degradation around ~147K of a 200K
window, auto-compaction at 64–75% capacity, performance falling to 40–60% by hour three of an unmanaged session — are
exactly the kind of measurement the router's telemetry should produce per Worker for Linus, so that "this Worker
degrades past N tokens of context fill" becomes a model-registry property rather than folklore.

### Worker selection gets a memory-aware dimension

[The speed-and-tok/s paper (2502.16721)](../paper-notes/2502.16721v1.md) established that Worker selection should be
measured in task-completion-time, not tok/s. The complexity-theoretic results add a sharper test: **a 7B Worker with a
generous CoT budget and full reasoning- token retention may meaningfully outperform a 14B Worker forced to be terse on
inherently sequential tasks.** This is empirically falsifiable on M1 Max and would be a high-value Phase 1 experiment to
add to [`benchmarks/dan_tasks/`](../../benchmarks/dan_tasks/).

The Kojima emergence-at-scale finding adds another: **CoT-gap as a per-Worker fingerprint.** Run a small smoke test (50
items, MultiArith- style) on every model Linus pulls in Ollama, measure `accuracy_with_CoT - accuracy_without_CoT`,
store the delta as a per-model property. The router uses it to decide whether to inject a CoT trigger and how much
budget to allocate. Cheap to run, expensive to omit.

### Inference backend selection gets a recurrence preference

The minGRU paper's argument — recurrence carries state cheaper than attention does, by orders of magnitude at long
sequences — translates directly into a Phase 6 / Phase 7 preference. **Linus inference backends should be evaluated
partly on how cheaply they can hold and update rolling state.** Recurrent and SSM-based architectures (Mamba, S4, the
minGRU/ minLSTM line) become first-class candidates for the memory-pillar components, even if the primary Worker LLM
remains a transformer. A future Linus router that dispatches to a transformer for short-context coding tasks and to a
recurrent encoder for long-context document reasoning is a more interesting architecture than "one model for
everything."

This sharpens the BitNet-line bet too. A _minGRU with BitLinear gates_ is the most extreme hardware-friendly substrate
the corpus collectively points at: recurrent (no quadratic attention), 1-bit (no FP16 multiplies),
Apple-Silicon-friendly (parallel scan + adder arrays). This is a Phase 6 or Phase 8 research direction worth flagging in
[`docs/landscapes/total-landscape.md`](../landscapes/total-landscape.md).

### Phase resequencing

The single biggest implication of this synthesis is that **memory should be promoted from a Phase 3+ deferred concern to
a Phase 2 first-class architectural layer.** This affects the ROADMAP directly. A reasonable restructured Phase 2
includes, alongside the existing MVP work:

- A `docs/specs/memory-architecture.md` spec walking through Layers A–E, the four sub-requirement obligations, and the
  substrate choice for each layer.
- A v0 episodic store implementation (SQLite + content hashes + git as the persistence substrate), wired into the
  Maestro/Worker protocol so that every Worker invocation reads-and-writes-back through it.
- A scratchpad-retention policy in the orchestration layer: reasoning tokens are durable artifacts by default, addressed
  by `(session_id, turn_id)`, hashed for integrity.
- A per-Worker CoT-gap measurement folded into `benchmarks/dan_tasks/`.

Phase 6 and Phase 8 stay as the homes for the more ambitious substrate experiments (Coconut-style latent recurrence in a
Linus-trained model; TTT-style episodic consolidation; minGRU/minLSTM/SSM Workers), with their viability informed by
Phase 1c and Phase 2 measurements rather than guessed up front.

### Context-window management is an operational concern, not just an architectural one

The eleven-paper corpus and the Garrison nucleus give Linus the _substrate_: layered memory, an episodic store,
recursive state with reliable history access. Mughal's piece supplies the complementary _operational pattern_ that runs
on top of that substrate. The two are not in tension. The architectural pillar makes the disciplined operation possible;
the disciplined operation realises the value the architecture was built for. Treating either as sufficient on its own is
a category error.

Concretely, Linus needs orchestration-layer analogues of the four hosted-Claude commands and the PreCompact hook
pattern. A diagnostic command parallel to `/context` that reports per-call context fill at dispatch time, broken down by
layer (scratchpad, episodic, investigation, semantic, system); a full-reset operation parallel to `/clear` for moves to
unrelated tasks; a summarising compression operation parallel to `/compact` that takes explicit preservation
instructions about what must survive; a surgical rollback operation parallel to `/rewind` that returns to a named
checkpoint without losing the work before it; and a PreCompact-style hook that captures critical state to the durable
substrate before any lossy compression event fires. The reactive-versus- active framing Mughal closes on — context as a
resource to manage rather than a bucket that fills — is the Maestro/Worker stance Linus should adopt by default.

These are not separate from the M-series resolutions; they are the orchestration-layer surface that exposes the M-series
substrate to the Maestro/Worker protocol. The architectural commitment in M3 (scratchpad as durable artifact,
two-segment record) makes the PreCompact pattern trivial to implement, because the critical state is already being
written durably at every turn — the hook becomes a notification rather than a rescue. The architectural commitment in M2
(episodic store as addressable substrate) makes the session-handoff pattern trivial, because handoff content is just
another addressable record at a session boundary. The architectural commitment in M4 (router primitives `cot_budget` and
`memory_mode`) is what makes per-call diagnostic visibility possible at all, because per-call budgets are what get
reported. Without the substrate the operations have nothing to act on; without the operations the substrate is unused
capacity.

### The o1 anti-pattern is now a stated failure mode to avoid

OpenAI's documentation that o1 "discards reasoning tokens from its context after each response" is, in the formal
language of the corpus, a direct violation of reliable-history-access requirement (2). Linus's Worker protocol should
explicitly _forbid_ this pattern: any Worker integration that silently drops reasoning between turns is a non-starter
for the session memory layer, regardless of how impressive its single-shot benchmarks look. This belongs in the Worker
protocol spec, not as a preference but as a hard constraint.

![OpenAI o1 context window: reasoning tokens discarded between turns](../../context/pics/oai-o1-context-window.png)

The figure above (per DEC-0032's 16K in-context cap policy) shows the structural problem: reasoning tokens that are not
durably retained between turns force the next turn to re-derive what was already established, collapsing the worker back
toward TC0 on whatever residual remains. The Linus episodic substrate is the architectural answer to that silent
truncation.

---

## What stays out of scope (hype filter)

Several adjacent attractive claims are _not_ what this synthesis supports.

**This is not an argument that Linus should attempt frontier-scale training.** Chinchilla and Llama 3 are bounding
references for what the brute-force scaling axis can do; Linus's hardware constraint (32 GB unified memory, single M1
Max) takes that path off the table. The synthesis says the brute-force-via-attention path is the wrong axis; it does not
say Linus should compete on the right axis against gigawatt clusters.

**This is not an argument that local 7B/8B models will rival hosted Claude on Maestro tasks.** The Sparks paper makes
clear that frontier capability ceilings are real. The argument is that Worker capability is _memory-bottlenecked_, and
that fixing the memory pillar narrows the gap on operational tasks where the limiting factor was scratchpad / episodic
retention, not raw reasoning ceiling. Maestro/Worker discipline still applies; Linus is not trying to be the Maestro.

**This is not an argument that Linus should adopt Coconut, TTT, or minGRU as the Phase 2 substrate.** These are
candidate substrates worth prototyping; the corpus does not yet have a clear winner among them, and the right Phase 2
commitment is a _memory architecture spec_ that is substrate-agnostic at the API level. Substrate choice is empirical
and deferred to Phase 6+ when measurements exist.

**This is not an argument against transformers.** Transformers with adequate scratchpad retention are universality-class
per the formal results. The argument is that _single-pass transformers without external memory_ are TC0, which is the
architectural pattern Linus must avoid, not that transformers themselves are the wrong substrate.

**ARC-AGI is not a Linus target.** The benchmark is most useful as a _diagnostic frame_ for memory experiments — vary
the memory while holding the model fixed, measure the delta — not as a leaderboard target. Frontier-compute approaches
(o3 at $1.15M for 91.5%) are not Linus territory; Kaggle-track approaches (8B + TTT + augmentation) are research
projects, not weekend spikes.

**Llama 3's 128K context window is not a substitute for episodic memory.** The 98.1 multi-needle score is impressive; it
is also a quadratic-cost simulation of memory inside attention. Linus should deliberately _cap_ in-context window usage
low (8–16K) and route everything beyond that through the episodic store, even when the underlying Worker technically
supports 128K. Setting that policy up front prevents the lazy "just stuff it all in context" pattern.

**Aiming for ever-larger Worker context windows is a long-term goal, not a substitute for the memory pillar.** The
Garrison formal argument gives one reason: a window large enough to hold history is still single-pass attention over
that history, which is the regime the corpus shows is TC0-bounded. Mughal's lost-in-the-middle finding gives the
operational companion: even _inside_ a window the model nominally has, attention on content buried in the middle
degrades to a fraction of what it was when fresh, so a 200K window is in practice a ~100K–120K working budget that silts
up further with every tool call. The 16K cap M5 sets for Phase 2 is a floor that can move with confidence as Linus
matures and as Worker context-handling improves — not a ceiling. What stays regardless of how far the cap rises is the
rest of the M-series commitment: the episodic store as the path for anything beyond the window, the overflow contract
for what spills, and the explicit-bypass mechanism for the rare case where stuffing context is the right answer. Larger
windows are useful; they do not change the architecture they sit inside.

---

## Phase-tagged priorities

Consolidated across the corpus, the actionable items by phase:

**Immediately (before Phase 1 ends)**

Add a per-Worker CoT-gap measurement (50 items, MultiArith-style) to the Phase 1 benchmark protocol so that every
Ollama-pulled model carries the metric in the model registry. Cost: hours of work; permanent value.

Adopt the Kojima two-stage pattern (reasoning extraction → answer extraction with explicit separation) as the default
Worker invocation template. Reasoning trace is a separately addressable artifact; final answer is a separately
addressable artifact; the link between them is explicit. Implementing this now costs nothing; retrofitting later is
expensive because every downstream consumer of Worker output will assume the concatenated form.

Forbid the o1 anti-pattern in the Worker protocol spec. Any Worker integration that silently truncates reasoning between
turns is non-conformant.

**Phase 2 — Linus MVP**

The biggest move: lift the memory architecture from Phase 3+ to Phase 2 as a first-class deliverable. Concretely:

- `docs/specs/memory-architecture.md` (new) walks through Layers A–E, the four sub-requirement obligations, the
  substrate choice per layer, and the read/write API the orchestration layer exposes.
- v0 episodic store implementation: SQLite + content hashes + git as persistence substrate. Wired into the
  Maestro/Worker protocol so that every Worker invocation reads relevant episodic context on entry and writes the
  resulting (reasoning trace, answer, tool outputs) tuple on exit. CRISPR-style temporal ordering (recent ranked higher,
  ancient retrievable on demand). **Scaffolding landed 2026-05-16 via PR #35 (Phase 2h.1-2):** `src/linus/memory/` ships
  the SQLite episodic store with idempotent schema migration, a JSONL audit-log writer with lazy `iter_events`, SHA-256
  content-hashing (Keccak deferred via the `_resolve_algorithm` hook), and a `DispatchEvent` type that validates the
  `memory_mode` ∈ {`stateless`, `session_stateful`, `project_stateful`} and `cot_budget` ∈ {`logarithmic`, `linear`,
  `polynomial`} router primitives at construction per DEC-0031, plus records cap-override audit-noise per DEC-0032. 35
  unit tests pass. The next step is wiring this v0 substrate into Worker dispatch so episodic context-read on entry and
  tuple-write on exit become the default Worker behavior, not an opt-in.
- Scratchpad retention as a default in the orchestration layer; addressed by `(session_id, turn_id)`, hashed for
  integrity.
- Router gains two new primitives: per-call CoT budget, per-call memory mode (stateless / session-stateful /
  project-stateful).
- A "memory-aware Worker selection" benchmark in [`benchmarks/dan_tasks/`](../../benchmarks/dan_tasks/) that compares a
  small Worker with generous CoT budget against a larger Worker with terse output on inherently sequential tasks (the
  falsifiable claim from the complexity-theory results).
- In-context window cap policy: deliberately limit Worker context windows to 8–16K and route beyond that through the
  episodic store. Prevents the long-context-as-memory-substitute anti-pattern.
- A first-class diagnostic command in the orchestration surface (the Linus analogue of
  [`/context`](../../context/notes/Why-Claude-Gets-Dumber-the-Longer-Your-Session-Run.txt)) that reports
  per-call context fill at dispatch time, broken down by layer (scratchpad, episodic, investigation, semantic, system).
  Visibility is the precondition for active management; without it, every "context is full" decision is folklore.
- A session-handoff record written to the episodic store at session end and read at session start. The Linus-native
  analogue of Mughal's `.claude/session-handoff.md`, but addressable via the M2 substrate rather than a single volatile
  file — which means handoff content is versioned alongside the session it summarises, and a project that spans many
  sessions accumulates a navigable handoff history rather than overwriting it each time.

**Phase 3 — Knowledge & Parallel Agents**

The episodic store gets parallel-write coordination (already a Tier 2 question; the answer is more urgent now because
parallel Workers amplifying memory contention will surface faster than expected).

A diagnostic ARC-AGI experiment: take 50–100 public-eval tasks, run a small Linus Worker against them twice — once
without episodic memory, once with it. Measure the delta. This is the cleanest way to turn the memory thesis into a
number.

The semantic-memory layer (KnowledgeBase) gains the uniform read API shape, so Workers cannot tell whether context came
from scratchpad, episodic, or knowledge memory.

**Phase 6 — Fine-Tuning**

Memory-substrate experiments become viable. Three candidates ranked by risk:

1. _FP16-LoRA on Dan's domain corpus_ — the safe baseline regardless of memory work. Already committed in the existing
   planning.
2. _TTT spike (Akyürek-style)_ — fit a per-task LoRA on a small ARC or domain-specific task using mlx-lm + Llama-3.2-1B.
   Measures whether episodic-memory-as-LoRA-consolidation is viable on M1 Max. Low cost, high information.
3. _minGRU MLX port + Shakespeare baseline_ — port the few-line PyTorch reference to MLX, run on M1 Max, publish the
   result. Establishes whether parallel-scan recurrence is a real local training option.

**Phase 8 — Beyond MacBook**

The most ambitious cross-product the corpus collectively points at: _minGRU with BitLinear gates_, possibly combined
with mlx-flash streaming for larger-than-RAM weights. Recurrent + 1-bit + streamed is the most hardware-friendly
substrate for Apple Silicon's adder-array ANE and the unified-memory budget. Pure research direction; no Phase 6/7 work
gated on it.

---

## Cross-cutting open questions surfaced by this synthesis

These supplement (not replace) the per-paper open questions accumulated in
[../questions/open-questions.md](../questions/open-questions.md).

**The substrate question for Layer C.** SQLite + git as the conservative v0 is an obvious starting point. But the
Akyürek TTT result is striking enough that it warrants explicit consideration: should episodic memory be
_structured-text-and-hashes_ (debuggable, inspectable, slow to consult) or _parametric-via-LoRA-consolidation_ (fast to
consult, opaque, requires a training pass per consolidation event)? Or are these two ends of a continuum where the right
answer is "both, with knowledge graduating from text into LoRA after sufficient repeated access"? The right Phase 2 spec
should not commit to (3) but should not preclude it either.

**Faithfulness of retained reasoning.** If reasoning traces are stored as durable artifacts and surfaced to Dan, the
system implicitly endorses them. The Kojima paper's error analysis notes that traces sometimes generate unnecessary
steps after reaching the correct answer, then corrupt the answer; sometimes they just rephrase the question. Should
there be a Phase 3 component that audits CoT for self-consistency, or is that out of scope until specific failure modes
appear?

**Memory budget as a first-class accounting quantity.** o3 paid $1.15M to brute-force memory reliability through
parallel search. Linus's local hardware budget is a few tens of dollars of electricity per day. Can ARCHITECTURE.md (or
a new ADR) treat memory budget as a first-class quantity with the o3 number as the cautionary upper bound and
human-with- pen-and-paper as the lower bound? The point is to make implicit choices ("we'll just retry until it works")
legible.

**ARC-AGI as a memory diagnostic, not a target.** Should `benchmarks/dan_tasks/` include 50–100 public-eval ARC-AGI
tasks, run with and without the episodic store as a memory-architecture probe? The benchmark is not a Linus capability
target, but it is one of the few public-domain proxies for "reliable computation across many steps on a novel task."

**Scratchpad-budget policy per task class.** Should the router enforce per-call CoT budgets, and if so, on what basis
(task type, deadline, energy budget)? The Merrill & Sabharwal regimes (log / linear / polynomial) are theoretically
clean; mapping them to concrete token caps is empirical work. A simple v0 ("DP-shaped tasks get up to 4096 reasoning
tokens with full retention; lookup tasks get 256 with truncation") is cheap to implement and would generate the data to
inform a more refined policy.

---

## Inputs

The Garrison nucleus:

- [`context/notes/garrison_memory_makes_computation_universal.md`](../../context/notes/garrison_memory_makes_computation_universal.md)
  — the synthesized blog + paper note that anchored this reading.
- [`context/papers/2412.17794v1.pdf`](../../context/papers/2412.17794v1.pdf) — Garrison's proof paper (formal arXiv
  version now in corpus as ([2412.17794v1](../paper-notes/2412.17794v1.md))).

The eleven supporting paper notes (all in [`docs/paper-notes/`](../paper-notes/)):

- [2205.11916v4](../paper-notes/2205.11916v4.md) — Kojima et al., _Large Language Models are Zero-Shot Reasoners_ (the
  "let's think step by step" paper).
- [2203.15556v1](../paper-notes/2203.15556v1.md) — Hoffmann et al., _Training Compute-Optimal Large Language Models_
  (Chinchilla).
- [2102.05095v4](../paper-notes/2102.05095v4.md) — Bertasius, Wang & Torresani, _Is Space-Time Attention All You Need
  for Video Understanding?_ (TimeSformer).
- [2303.12712v5](../paper-notes/2303.12712v5.md) — Bubeck et al., _Sparks of Artificial General Intelligence: Early
  experiments with GPT-4_.
- [2305.15408v5](../paper-notes/2305.15408v5.md) — Feng, Zhang et al., _Towards Revealing the Mystery behind Chain of
  Thought: A Theoretical Perspective_.
- [2310.07923v5](../paper-notes/2310.07923v5.md) — Merrill & Sabharwal, _The Expressive Power of Transformers with Chain
  of Thought_.
- [2407.21783v3](../paper-notes/2407.21783v3.md) — Meta, _The Llama 3 Herd of Models_.
- [2410.01201v3](../paper-notes/2410.01201v3.md) — Feng et al., _Were RNNs All We Needed?_
- [2411.07279v2](../paper-notes/2411.07279v2.md) — Akyürek et al., _The Surprising Effectiveness of Test-Time Training
  for Few-Shot Learning_.
- [2412.04604v2](../paper-notes/2412.04604v2.md) — Chollet et al., _ARC Prize 2024: Technical Report_.
- [2412.06769v3](../paper-notes/2412.06769v3.md) — Hao et al., _Training Large Language Models to Reason in a Continuous
  Latent Space_ (Coconut).

Cross-references that were load-bearing without being in the eleven-paper set:

- The earlier Merrill & Sabharwal "parallelism tradeoff" paper (TACL 2023; not in `context/papers/`) supplies the strict
  TC0 result for single-pass transformers that both 2310.07923 and 2305.15408 build on.
- The structured-state-space line (S4, Mamba, Hyena, Mamba/SSM duality) is referenced by 2410.01201 as the cousin
  architecture; not separately noted here, but the same recursive-state-maintenance argument applies.
- Boyle, Komargodski & Vafa's "Memory checking requires logarithmic overhead" (STOC 2024) supplies the tight lower bound
  used by Garrison's Theorem 1.
- Ayesha Mughal,
  [_Why Claude Gets Dumber the Longer Your Session Runs (and the Exact Fix)_](../../context/notes/Why-Claude-Gets-Dumber-the-Longer-Your-Session-Run.txt)
  (Medium, March 2026) — the practitioner-side companion to the Garrison thread; documents lost-in-the-middle attention
  degradation, real-vs- nominal token budgets, and the four operational primitives (clear / compact / rewind /
  diagnostic-context) plus the PreCompact hook and session-handoff patterns that map onto the M2/M3/M4 substrate.

---

_This synthesis is the input to the next round of edits to [paper-landscape.md](../landscapes/paper-landscape.md),
[synthesis-landscape.md](../landscapes/synthesis-landscape.md), [total-landscape.md](../landscapes/total-landscape.md),
[open-questions.md](../questions/open-questions.md), and [top-questions.md](../questions/top-questions.md). It should be
revisited when the Phase 2 memory architecture spec lands, when the Phase 6 substrate experiments produce results, and
whenever a new paper in the recurrence / state-space / memory-architecture line lands in `context/papers/`._
