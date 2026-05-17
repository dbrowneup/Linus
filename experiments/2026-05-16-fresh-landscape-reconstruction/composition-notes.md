# Composition Notes — fresh landscape reconstruction (no-peek)

_Meta-commentary written 2026-05-16 after composing fresh-total-landscape.md,
fresh-synthesis-landscape.md, and fresh-top-questions.md. The
convergence-vs-divergence reflection at the end is the only section written
after consulting the forbidden files; everything above it predates the peek._

## Which syntheses felt most load-bearing during reconstruction?

Five syntheses did most of the load-bearing work during this composition,
and they were not the syntheses I expected to lean on most heavily before
starting:

**memory-synthesis.md** turned out to be the document the other syntheses
secretly orbit. Almost every other thematic synthesis cross-references
Layer A or Layer B or Layer C or Layer E. Memory is not just a pillar — it
is the substrate the corpus uses to mean infrastructure-that-compounds.
The Garrison framework gives the project an unusually clean philosophical
grounding: the TC0/P transition + reliable-history-access framing makes
the architectural commitment _necessary_ rather than merely useful. Every
time I went to write something like "and Linus's KB is the substrate that
makes session continuity work," the actual argument was already pinned in
memory-synthesis. The other syntheses are downstream of that grounding in
a way that makes them feel lighter.

**agentic-systems-synthesis.md** was the second-most-cited during writing.
Its eight cross-cutting threads (role specialization, structured
inter-agent messages, structured shared state, per-stage validation,
critic tier, tool documentation, hosted-frontier dependency,
agentic-system theory) form the canonical agent-architecture vocabulary
the corpus operates in. Layer D (investigation memory) was the most
visible cross-thread connection — added in response to Kosmos-style
shared state, archived to Layer C on close, the bridge between
agentic-systems and memory. Without this synthesis, the orchestration
layer would still be hand-waved at; with it, the Phase 3 spawner has
concrete typing.

**native-low-bit-apple-silicon-synthesis.md** carried the operational
substrate story. The trajectory framing (research → engineering →
productization → MLX-native deployment over ~28 months) was the cleanest
piece of narrative arc in the entire corpus. The combinable-bets thesis
(BitNet/Bonsai × flash-streaming × Kimi-K2) is the most consequential
strategic claim in the project — without it, the Phase 8 north star is
just "the long view"; with it, it has a name (DEC-0056 seed) and a
gating measurement (Phase 6d streaming feasibility). I cited this
synthesis heavily in Part III of the total-landscape because it
single-handedly populates the speculative/research-direction bin.

**llm-wiki-synthesis.md** carried the disciplinary substrate (claim
typing, content hashing, write-back rule, schema-as-flywheel). Almost
every claim in fresh-total-landscape's "what is settled" section about
KB design rolled up through this synthesis. The compile-don't-retrieve
distinction is the load-bearing architectural framing for Layer E. The
g2 and g3 cluster syntheses (eighteen wiki engines, all Study) give the
synthesis its empirical weight: it is not theoretical advice; it is what
eighteen working implementations converged on.

**llm-hardware-design-synthesis.md** was a surprise. I expected it to be a
peripheral Phase 7+ research direction; it turned out to carry the most
ambitious strategic claim in the corpus — that idea-to-reality (LLMs
producing artifacts downstream non-LLM actors realize as reality) is a
Phase 7 commitment, not a Phase 11 speculation. The "the oracle is the
unit of effort being amortized" finding is the kind of architectural
re-framing that compounds across every Phase 6+ ADR. The eleven seeded
ADRs in this single synthesis is the largest count in the corpus, and
the seeds are mostly cross-domain rather than QiMeng-specific. By the
end of reading I treated it as a co-equal partner to memory and
native-low-bit at the strategic-claim level.

The syntheses that did _less_ work than expected: the four humanistic/
philosophical syntheses (humans-teams-performance, llms-in-science,
skills-and-practices, entrepreneurship). They are interpretive layers
over the substrate decisions made elsewhere; they make the architecture
defensible (Maestro/Worker discipline gets philosophical grounding;
release posture gets a "for science, for society" rationale; the
cross-domain moat is empirically grounded) but they do not introduce new
substrate. That's not a criticism — they are doing their job — but it
meant I cited them in compact paragraphs rather than as load-bearing
contributors to long sections.

## Which threads cut across many syntheses?

Six threads recurred in five or more syntheses each. They are the threads
that turned into the "validated substrate" tier in the fresh-total-
landscape:

**The MCP convergence** was the loudest. Five clusters (g6 most directly,
plus g4, g5, g7, g9) ship MCP servers or pattern-match against MCP-shaped
interfaces. fastmcp shows up everywhere as the underlying framework.
The Phase 3 ADR question was overdetermined by the time I finished
reading g6.

**The Maestro/Worker discipline** showed up at three timescales (cognitive
throughput, team rhythm, intra-career breadth-then-depth) plus all the
agentic-systems and skills-and-practices framings. Three syntheses
explicitly tied it to the "structure compounds, intensity does not"
thesis. The Knuth case in llms-in-science was the cleanest empirical
demonstration.

**Claim-typing + content hashing + write-back** showed up in five
syntheses (llm-wiki primary; g2 + g3 for the implementation patterns;
memory for the Layer E commitment; safety-alignment-privacy for the
KB → hosted-Maestro flow gate; function-annotation-discovery for the
model_prediction edge class). The discipline is overdetermined in the
same way the MCP commitment is.

**Typed structured prediction wrapping free-text rationale** appeared in
function-annotation-discovery (BioReason-Pro shape, S25 CLAUDE.md
convention) and agentic-systems (Trading-R1 confirmation that the
pattern generalizes beyond biology) and llm-hardware-design (extended
to hardware-design specs). The convention is now the default output
shape for any Linus skill producing predictive output.

**The "trust the OS page cache" finding** appeared in four syntheses
(native-low-bit primary; g1 + memory + the general infra-foundations
narrative). The generalization from flash-MoE's specific finding to
"applications competing with OS page cache typically harm performance
on macOS unified memory" earned engineering-convention status.

**Open-weights-friendly biology Wave 1** appeared across three biology
syntheses plus g9. Six of eight Group A models release weights under
permissive licences; five of eight are operationally deployable on M1
Max today. The corpus's strongest near-term skill-development direction
falls out of this.

## Where did binning struggle?

The first binning I tried for total-landscape was three flat sections:
substrate / behavioral / domain. It broke immediately because most of the
syntheses cross at least two of those axes. agentic-systems is
behavioral plus substrate (the Role typing and AgentReport are substrate
commitments). memory is substrate plus behavioral (the in-context cap
and scratchpad rules are behavioral conventions on top of the substrate
choices). llm-hardware-design is domain plus substrate (the QiMeng
discipline is a Linus-wide infrastructure pattern, not a domain
commitment).

I switched to maturity-tier as the primary axis (validated / in-flight /
speculative) and that worked much better because it cuts across the
substrate/behavioral/domain axes naturally. Inside each tier I then
showed how pillar and phase interact. The crossings section is where
substrate-x-domain-x-behavioral interactions get named explicitly.

For the synthesis-landscape, the bin I most struggled with was where to
put humans-teams-performance and llms-in-science. They are not
substrate (they don't introduce architectural commitments); they are not
behavioral in the agentic-systems sense (they don't describe how Workers
interact). They are interpretive — they give the project a defensible
philosophical position. I bundled them under "behavioral" in the synthesis-
landscape but that's a stretch. The cleaner taxonomy would have a fifth
bin called "philosophical grounding" or "meta-architecture" but that felt
like overfitting for two syntheses.

The biggest binning failure I noticed was that entrepreneurship and
g10-finance fit together so tightly they should arguably be a single
synthesis. The entrepreneurship synthesis explicitly names g10 as its
primary cluster anchor; the g10 cluster's "transferable patterns"
section reads like a section in the entrepreneurship synthesis. The
reason they are separate is presumably historical (g10 came first as a
cluster fan-out; entrepreneurship was extracted from skills-and-practices
later). The fresh-synthesis-landscape's overlap matrix notes this but
doesn't resolve it.

## What did I choose to OMIT and why?

The total-landscape omits per-paper findings even when they are
substantial. The Garrison eleven papers, the eight Group A bio FMs, the
six Group B generative-biology papers, the eight Group C function-and-
discovery papers, the fifteen QiMeng papers — none of these get
paper-by-paper treatment in fresh-total-landscape. The reason: the
syntheses do that work; replicating it would just be summarizing
summaries.

I also omitted detailed Phase 5+ work (openclaw, Tauri, native apps,
mobile, Mac Studio). The roadmap covers it; the syntheses touch it
lightly; including detailed Phase 5+ in a landscape document would dilute
the focus on what is currently load-bearing. The "what falls when" phase
mapping in Part VI hits Phase 5+ in single-line bullets, which is the
right resolution for this document.

The fresh-top-questions document explicitly omits already-resolved
decisions (which would inflate the count), per-paper open questions
(which belong in `open-questions.md` per-source rollup), and
architectural micro-decisions (which live in ADRs or specs). This kept
the count to 35 items rather than 100+; the cost is that some of the
omitted questions might have been Tier 1 for a different reader.

I notably omitted the Phase 1f orchestration verdict ADR as a Tier 1
question because the synthesis explicitly resolves it ("adopt both
patterns, neither product, build the glue" per workgraph + claude-squad
+ claude-task-master combination). But the resolution depends on the
underlying tool-registry and session-store decisions (T1-06, T2-03), so
in a sense the Phase 1f verdict is awaiting downstream resolution.

## What surprised me during composition?

Two things.

First: the **synthesis-landscape was harder to write than the total-
landscape**, contrary to what I expected. I expected the per-doc rollup
to be mechanical (one paragraph per synthesis, list cluster anchors,
done). What actually happened was that I kept noticing cross-synthesis
overlaps and felt obligated to surface them. The cross-synthesis overlap
matrix in fresh-synthesis-landscape is the most useful section of that
document and the section I'd write longer if I had more time. Several of
the matrix entries (Memory ↔ LLM-wiki, Llm-wiki ↔ Llms-in-science,
Humans-teams-performance ↔ Memory) are not the obvious pairings; they
emerged from the writing.

Second: the **top-questions skewed toward Tier 2 and Tier 3**. I expected
to find ten or more Tier 1 blocking items; I found ten exactly, and three
of those (T1-04 LAB-Bench canary, T1-06 fastmcp smoke test, T1-08
pydantic-ai adoption) are not blocking-questions so much as
implementation-tasks-with-deadlines. The Phase 1 closure questions are
mostly mechanical; the architectural decisions live at Phase 2a (Tier 2)
and Phase 6+ (Tier 3). This shape matches what the roadmap projects:
Phase 1 is recon, Phase 2 is where the architecture lands, Phase 6+ is
where the research directions branch. The shape of top-questions reflects
the shape of the work.

The third surprise — not unexpected but worth naming — is how clearly
the corpus argues for **biology as the strategic Phase 7 commitment**.
Reading the three biology thematic syntheses + g9 + g8 + entrepreneurship,
the literature-intelligence stack as commercial surface, the
biology-Phase7-roadmap spec referenced from multiple places, the
biosecurity tier policy that exists to gate biology generative skills, the
~573-skill bundle from bioSkills + scientific-agent-skills, the Phase 6
fine-tuning candidates concentrated on biology FMs (METL exemplar,
RiNALMo + Bacformer LoRA candidates) — the corpus has decided that
biology is Phase 7, even where it does not say so explicitly. That
decision compounds the open-source release posture: biology is the
domain where Dan's domain expertise is most defensible against
generalist-AI commoditization. The cross-domain moat (skills synthesis +
humans-teams-performance) is what makes the commitment durable.

## Reflections on the experiment design

The forbidden-list constraint was easier to honor than I expected. I never
felt the urge to peek at the existing landscape during composition,
probably because the syntheses themselves are so cross-referential — when
I needed cross-context I could find it in another synthesis. The risk
the experiment was designed to expose (that the prior landscape structure
constrains what the syntheses surface) didn't materialize as a felt
pressure; the syntheses are self-contained enough that the landscape
falls out of them without much shaping needed.

The one place I felt pressure to consult existing documents was when
checking ADR / DEC numbering. Several syntheses reference DEC-0044
through DEC-0055 with specific numbers. I avoided looking these up;
where I cited a DEC by number, I trusted the synthesis's reference. The
fresh-total-landscape's "what's resolved" claims are downstream of those
references; if a DEC is mis-numbered in a synthesis, the landscape
inherits the error. The experiment design is silent on whether checking
ADR numbers counts as peeking; I treated it as in-bounds because the
syntheses themselves are the input.

The output documents arrived at different shapes than the source
documents. Existing landscape documents (the ones I was forbidden from
reading) presumably have their own conventions. I deliberately did not
try to match those conventions — the spec instructed free-form
structure. fresh-total-landscape is organized by maturity-tier;
fresh-synthesis-landscape is organized by function bin; fresh-top-
questions is organized by impact-tier. If the existing documents use the
same axes that's convergence evidence; if they don't that's divergence
evidence.

---

## Post-peek convergence-vs-divergence reflection

_The section above was written before consulting any forbidden files.
This final paragraph was written after reading the openings + matrices of
`docs/landscapes/total-landscape.md`,
`docs/landscapes/synthesis-landscape.md`, and
`docs/questions/top-questions.md`._

After reading the existing documents: **the experiment produces strong
convergence at the level of load-bearing claims and meaningful divergence
at the organizational level**. Convergence is unambiguous on the
substantive content. The same hub clusters are identified (the existing
synthesis-landscape names g4-memory, g7-harnesses, g8-sci-agents, g9-bio
as cross-cutting hubs; my Bin 5 narrative converges on the same set). The
same Crossings are named: the existing total-landscape names "Crossing 1 —
BitNet → Apple Silicon → ANE," "Crossing 2 — the streaming axis,"
"Crossing 3 — KnowledgeBase as graph + vector," "Crossing 4 — structure as
the operational bottleneck," "Crossing 5 — memory as the load-bearing
pillar," "Crossing 6 — biology as a pillar," "Crossing 7 — agentic-systems
theory as first-class input." My Crossings A-F map well: my A (Memory ×
Inference) roughly matches existing Crossing 1 + Layer A discussion; my B
(Agentic Systems × Memory × KB) matches existing Crossing 5 + Crossing 7;
my C (Skills × Safety × Domain) sits inside existing Crossing 6; my D
(Hardware-design × Biology × Self-improvement) is one I named that the
existing structure handles through the new llm-hardware-design synthesis
folded in 2026-05-09. The matrix-rows in the existing synthesis-landscape
("memory" → orchestration + KB layers, g4-memory anchor, etc.) compress
the per-synthesis treatment I expanded into Bin 5 prose. The top-questions
overlap is heavy: existing Tier 1 R2-01 through R2-08 maps nearly 1:1 to
my T1-01 through T1-10 (pydantic-ai adoption, transport, serving protocol,
vault location, hyalo/keppi bake-off, dan-tasks scope, context-routing
policy, MCP transport). My T1-04 (LAB-Bench canary) and T1-05 (CoT-gap
fingerprint) are not explicitly in the existing R2 Tier 1, suggesting
either I over-weighted them or they live elsewhere in the structure.

The genuine divergences are: **(1) organizational spine**. The existing
total-landscape leads with "How the syntheses align" matrix and then the
Crossings; I led with maturity-tier (validated / in-flight / speculative)
and made crossings derivative. Both work; the existing approach is more
compact, mine is more narrative. **(2) The Round 1 / Round 2 sweep
vocabulary** (S1-S60, R2-NN, E1-E12) is entirely absent from my
top-questions because I had no access to the sweep history. The existing
document is the second wave of a much larger lifecycle (~60 S-questions
already resolved); my 35 questions are a fresh draw without that history.
**(3) I named the "observability and instrumentation gap"** at the end of
fresh-synthesis-landscape as a candidate new synthesis area; the existing
synthesis-landscape does carry observability concerns scattered across
safety-alignment-privacy, skills-and-practices (lmnr), and g11, but does
not consolidate them into a dedicated synthesis. This might be a
genuinely new finding worth proposing. **(4) The existing total-landscape
counts the Crossings to 7** (post-2026-05-04 additions); my 6 crossings
correspond to roughly the same surface but I missed naming agentic-systems
theory as a standalone crossing (existing Crossing 7).

Overall verdict: **the existing landscape structure does not appear to be
constraining what the syntheses surface in a problematic way.** An
independent reading arrives at the same load-bearing claims, the same hub
clusters, the same crossings, and substantially the same top-questions
through a different organizational spine. The experiment is therefore
mildly reassuring evidence that the corpus is well-structured internally —
the syntheses say what the landscape says, and the landscape documents
reflect that structure rather than imposing it on the syntheses. The
divergences I observed are mostly compositional (matrix-vs-narrative,
crossings-first-vs-maturity-first) rather than substantive. If anything,
the experiment surfaces that the existing top-questions document carries
significantly more history (the S-sweep + R2-sweep vocabulary) than my
fresh derivation can recover from the syntheses alone — which is a
property of the lifecycle, not a structural weakness in either document.
