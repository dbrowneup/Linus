# Safety, Alignment & Privacy Synthesis

## What this document is

A synthesis of four papers covering four orthogonal angles on AI safety as
they bear on Linus: a *technical mechanism* for inspecting and steering
model internals
([Beaglehole et al., Science 2026](../paper-notes/science.aea6792.md)), a
*cultural-empirical* characterization of what the deployed Maestro
actually does ([Anthropic *Values in the Wild*, COLM
2025](../paper-notes/Values_Paper__camera_ready_COLM_.md)), an empirical
*threat model* for what attackers can extract from voluntarily published
text using hosted LLMs
([Swanson et al., arXiv 2602.16800v2](../paper-notes/2602.16800v2.md)),
and a *design-policy* account of dual-use uplift in pandemic biology
([Soice et al., arXiv 2306.03809v1](../paper-notes/2306.03809v1.md)).
This synthesis extends the existing
[security synthesis](security-synthesis.md), which covered supply chain
and prompt injection. The two together describe what reasonably amounts
to the complete shape of Linus's security posture: where code comes from,
what arrives at the model, what happens inside the model, what the model
says it values, what attackers can do with what the model produces, and
what the model must refuse to produce in the first place.

---

## The papers at a glance

[**Beaglehole et al. — *Toward universal steering and monitoring of AI
models***](../paper-notes/science.aea6792.md). A supervised method
(Recursive Feature Machines, RFM) extracts per-block "concept vectors"
from frozen LLM activations using ~500 labeled prompts and under a minute
of A100 time per concept. The same vector serves as a steering
perturbation (`A_ℓ + ε·v_ℓ` injected at one transformer block shifts
behavior toward or away from the concept) and as a monitor (a small
classifier over activation projections detects whether the concept is
active). RFM-probes beat GPT-4o-as-judge on hallucination/toxicity
detection across six benchmarks. The instrument requires read/write
access to per-block activations during the forward pass.

[**Huang et al. — *Values in the
Wild***](../paper-notes/Values_Paper__camera_ready_COLM_.md). A
privacy-preserving Clio-style pipeline run over 308,210 subjective
Claude.ai conversations from one week in February 2025 yields a
hierarchical taxonomy of 3,307 unique AI values clustering into five
top-level categories. Dominant expressed values are practical and
epistemic ("helpfulness" 23.4%, "professionalism" 22.9%, "transparency"
17.4%); values are highly context-dependent ("healthy boundaries"
emerges in relationship advice, "human agency" in tech-ethics
discussion); strong resistance is rare (3.0%) and triggered by
"rule-breaking" and "moral nihilism" attempts. This is empirical
phenomenology of *what hosted Claude actually does* — which is empirical
phenomenology of Linus's Maestro.

[**Swanson et al. — *Large-scale online deanonymization with
LLMs***](../paper-notes/2602.16800v2.md). A four-stage pipeline (Extract
/ Search / Reason / Calibrate) deanonymizes pseudonymous online accounts
at industrial cost. Headlines: 67% recall at 90% precision linking Hacker
News to LinkedIn via agentic web search; 45.1% recall at 99% precision
against the classical baseline's 0.1%; 9 of 33 scientists identified at
82% precision from a single Anthropic Interviewer transcript; effective
even when prior probability of any match is 1-in-10,000. PII redaction
leaves residual semantic signal; provider-side detection is hard.

[**Soice, Rocha, Cordova, Specter, Esvelt — *Can large language models
democratize access to dual-use
biotechnology?***](../paper-notes/2306.03809v1.md). An MIT classroom
exercise in which non-scientist students used off-the-shelf chatbots to
walk through pandemic-pathogen acquisition. In one hour, three groups
elicited four candidate agents (1918 H1N1, transmission-enhanced H5N1,
variola major, Nipah-Bangladesh), reverse-genetics protocols, the IGSC
member list (revealing non-screening vendors), BLAST-evasion techniques,
and CRO/cloud-lab routing for users without wet-lab skills. Jailbreaks
were trivial; one group reported zero refusals across the entire hour.
Proposed mitigations are pre-release evaluation, training-corpus
curation against a small (<1% of PubMed) hazard set, and universal
cryptographic DNA-synthesis screening.

---

## The four orthogonal axes

The papers do not collapse into one axis. Each names a different kind
of failure, with a different mitigation, at a different architectural
surface. Reading them together forces a useful discipline: every safety
claim should be tagged with which axis it addresses, because controls
on one axis do not transfer to another.

**Mechanism (Beaglehole).** The model produces behaviorally meaningful
internal states during inference, and those states are, with the right
instruments, *readable* and *writable*. Today's Linus sandbox is
policy-level — file-system gates, command allowlists, network egress
rules. Beaglehole opens a qualitatively new control class operating
*inside* the model: an RFM-probe that fires when "concept = pandemic-
pathogen synthesis" or "concept = deception" lights up during
generation, and an `ε·v` injection that nudges the model away from
unwanted behavior without retraining. The technique requires per-block
forward-pass hooks that hosted Maestro never exposes. The mechanism
axis lives entirely on the local-Worker side of the boundary.

**Cultural-empirical (Values).** The hosted Maestro is not a black box;
it is an object measured at scale. Anthropic's pipeline characterizes a
service-oriented, prosocial, supportive, context-adaptive system whose
dominant values are the ones Linus most needs from a planning layer
(clarity, transparency, thoroughness) but whose default mirroring/
affirming mode (~45% of subjective interactions) is exactly wrong for
code review and synthesis where Dan wants skepticism rather than
support. Values gives Linus a *characterization* against which Maestro/
Worker prompt design can be calibrated, not a control. This axis lives
entirely on the hosted side of the boundary; Linus has not generated
308k of its own conversations to do the same analysis on local Workers.

**Threat-model (deanonymization).** Hosted LLMs do not just *store* the
data Dan sends them; they *reason* over it in ways that can re-identify
the human behind a stream of content, at industrial cost. The
previously expensive part — being a skilled human investigator — is now
a function call. The strongest empirical case yet for Linus's
local-first ethos. Every byte that crosses from local-Worker context
into a hosted-Maestro prompt accumulates as identity signal at
Anthropic and becomes available to any third-party adversary running
the same pipeline against any corpus including Dan's writing. The
threat lives entirely on the hosted side; local inference is, by
construction, immune.

**Design-policy (dual-use biotech).** Some content the system *must not
produce*, regardless of caller, regardless of intent framing,
regardless of whether the underlying Worker would happily produce it.
Soice et al. make the case for orchestration-layer query screening as a
control category distinct from the sandbox: screening operates on *what
the user asks*, before any Worker is invoked; the sandbox operates on
*what the Worker tries to do*. Once content has been generated, logged,
and potentially leaked, discarding it after the fact does not undo the
event. This axis cuts across the hosted-vs-local boundary, but bites
hardest where Linus has *least* upstream support: open-weights Workers
pulled from Ollama, often with refusal training stripped by community
fine-tunes.

The four axes interlock. Beaglehole gives Linus the *technical
mechanism* for operationalizing what Soice et al. *require as design
policy*: an activation-monitor probe over a local biology Worker is the
natural substrate for the "refuse pandemic-pathogen synthesis" rule.
Values gives empirical phenomenology of the hosted layer that the
deanonymization paper warns about: knowing what hosted Claude does with
subjective content sharpens the question of what content it should ever
see. Each implies a concrete SAFETY.md addition that none of the others
would generate.

---

## Cross-cutting threads

### The hosted-vs-local boundary as a unifying constraint

Each paper sharpens the hosted-vs-local boundary differently, and the
boundary is the single most important architectural commitment the
safety story rests on. Beaglehole's mechanism *only* works on local
Workers; deanonymization *only* threatens content that leaves the
machine; Values *only* describes the hosted Maestro; dual-use design
policy applies to *both* sides but with asymmetric force. The
implication is not "everything must be local" — that defeats the
Maestro/Worker architecture, which intentionally relies on hosted
Claude for hard reasoning. The implication is that *which workflows sit
on which side of the boundary* is a safety property, not an efficiency
one. The KnowledgeBase routing question is the sharpest case: KB
content includes Dan's annotations, his voice, his unpublished writing
— exactly the substance the deanonymization paper exploits. Routing KB
retrieval through a hosted-Maestro prompt is the worst-case version of
the threat model. Default: KB content is local-Worker-only unless
explicitly overridden per request, with the tool registry carrying a
`privacy_tier` field that makes the default enforceable rather than
aspirational.

### Activation observability as an orchestration primitive

The deeper architectural lesson from Beaglehole is that activations
should be a real observation surface for the orchestration layer, not
an opaque model-internal blob. When Linus runs a Worker through
pmetal-serve, mlx-lm, or llama.cpp via Ollama, the inference layer is
*ours* and can in principle expose hooks for reading and perturbing
block outputs. Today Ollama does not; mlx-lm could; pmetal is open. Put
a stub `linus.observability.activations.*` API into ARCHITECTURE.md
*now*, before mlx-lm integration solidifies — naming the surface lets
later phases plug things in without re-architecting; leaving it implicit
defaults to the cheaper-to-ship option. The cost on M1 Max is real and
worth a Phase 1 spike: instrument Llama-3.1-8B-4bit through mlx-lm,
measure latency and memory hit of one attached probe, calibrate whether
real-time activation monitoring is a viable Phase 7 primitive or
deferred-to-bigger-hardware.

### Maestro-as-empirical-object

The Values paper opens the Maestro statistically: a service-oriented,
prosocial, supportive, context-adaptive system that resists
"rule-breaking" and "moral nihilism" with explicit ethical articulation.
More concrete than VISION.md currently has, and Linus depends on
specific parts. Linus relies on the Maestro's *epistemic* values for
synthesis (transparency, thoroughness, clarity, accuracy) and on its
*prosocial* defaults for safe-by-default behavior. Linus actively
*counters* the Maestro's mirroring tendency in code review (Dan wants
skepticism, not affirmation), its over-hedging in technical advice, and
its default warmth in technical contexts. Making these dependencies
explicit in a short `docs/maestro-protocol.md` (or a section of
VISION.md) lets Linus react to version changes that shift the relied-on
behaviors. "Claude 4.7 mirrors more than 4.6" should be actionable;
today there is nowhere to put the finding. The context-dependence
finding implies the orchestration layer's task-spec template needs a
mandatory `value_frame` field whose default for technical tasks is
"terse, skeptical, non-mirroring" rather than letting the Maestro's
deployment-mode defaults leak in.

### Privacy through local execution

The deanonymization paper supplies the most compelling architectural
argument for local-first AI yet published. Privacy benefits of local
inference have historically been argued in terms of compliance or
sovereignty; Swanson et al. sharpen the argument: **local inference is
the only architecture in which content cannot become identity signal
for someone else's pipeline**. This reframing belongs in VISION.md and
SAFETY.md as a positive statement of what local-first *guarantees* that
no hosted service can. Two operational consequences: the audit log
records what content crosses the local-to-remote boundary
(`destination`, `content-class`, `bytes-sent` per request), because the
*aggregate* of small disclosures is what kills privacy; KB content
defaults to local routing, plus a "redact-before-paste" CLI utility
that surfaces obvious identity signal — names, institutional
affiliations, distinctive phrasing, citations to Dan's own work — for
review before pasting. The utility's value is consciousness-raising on
high-risk pastes, not perfect protection.

### Knowledge-asymmetric uplift as the dual-use threat model

Soice et al. frame the dual-use threat as *knowledge-asymmetric uplift*:
a capability is acceptable if it provides no uplift beyond Dan's
existing PhD-level expertise, and unacceptable if it provides a
hypothetical attacker (or a future shared-Linus user, or a compromised
audit log) capabilities they don't otherwise have. The orchestration
layer's job is not to model the user's intent; it is to enforce that
the *system as a whole* does not surface uplift content, regardless of
caller. This argues for query-screening as a control category distinct
from the sandbox. The two cannot substitute: once a Worker has produced
dangerous content, even a discarded output has been generated and
logged. Screening happens at the orchestration layer, before any Worker
sees the query, and is Worker-invariant — open-weights biology Workers
with stripped refusal training cannot be trusted to enforce the policy
themselves.

### Connection to the existing security synthesis

The existing [security synthesis](security-synthesis.md) covered supply
chain and prompt injection. Group F adds four legs that synthesis
explicitly held out of scope: behavioral observation from *inside* the
model (Beaglehole), empirical characterization of the hosted Maestro
(Values), stylometric and semantic identity leakage *out* of the system
(deanonymization), and design-level constraints on what the system may
produce regardless of who asks (dual-use). The two syntheses now
describe a six-axis security posture: code provenance, input integrity,
internal behavior, hosted-layer characterization,
output-as-identity-signal, and dual-use refusal. None substitute for
the others. The security synthesis's "trust-tier tagging" on inputs has
a natural complement: a `privacy_tier` on outputs and a `screening
class` on queries. Designing the three together in Phase 2 is an order
of magnitude cheaper than retrofitting in Phase 3.

### Each paper implies a SAFETY.md addition

Each paper implies a specific concrete addition; the four form a
coherent revision plan filling gaps the current document explicitly
leaves open. SAFETY.md is well-designed for OS/filesystem safety but
does not address content-leakage policy (deanonymization), domain-
specific refusal categories (dual-use), the instrument-able interior of
local Workers (Beaglehole), or the dependencies Linus has on specific
Maestro behaviors (Values). The next section makes the four additions
concrete.

---

## Implications for SAFETY.md

The four proposed additions can ship as a single coherent revision PR,
each a section of a few paragraphs.

**"Stylometric and identity leakage to hosted models"** (from
[deanonymization](../paper-notes/2602.16800v2.md)). A new section
alongside "Network safety". SAFETY.md currently restricts *which
destinations* outbound connections may reach but does not address *what
content* may be sent to permitted destinations. Establish a content-
tiering policy: code excerpts and abstract architecture discussion are
low-risk for hosted dispatch; KB snippets and personal notes are
high-risk and require explicit per-request consent. The audit log gains
`destination`, `content-class`, and `bytes-sent` per request, so
aggregate disclosure is inspectable. KB-sourced content defaults to
`local-only`, with hosted dispatch explicitly opt-in per request.

**"Biological dual-use"** (from [Soice et
al.](../paper-notes/2306.03809v1.md)). A new section establishing
orchestration-layer hard refusal on certain biology queries regardless
of caller or intent framing. Refusal categories follow the paper's
exploited surface: pandemic-pathogen synthesis, enhancement-mutation
lookup for the named agents, reverse-genetics protocol surfacing,
vendor-screening status lookups, BLAST-evasion methodology, CRO/cloud-
lab routing for organism construction. Linus commits to *not building*
tools that look up vendor screening status or interface with CRO APIs.
Biology-skill autonomy-tier graduation requires passing a dual-use
red-team probe set; the KnowledgeBase is audited once against hazard
categories before any biology-skill RAG goes live. The caller-invariant
framing holds for Dan because the audit log is otherwise an
exfiltration risk if the machine is compromised, the discipline only
generalizes to a future multi-user Linus if it holds today, and Dan's
PhD-biochem expertise *raises* salience rather than lowering it.

**"Supervised activation steering and monitoring as a Phase 7 sandbox
primitive"** (from [Beaglehole et
al.](../paper-notes/science.aea6792.md)). The sandbox eventually
includes behavioral observation from inside the model, not just policy
gates around it. Commits Linus to a stub
`linus.observability.activations.*` API in ARCHITECTURE.md *now* (no-op
for Ollama, real hooks for mlx-lm in Phase 6/7), to a Phase 1 M1 Max
viability spike on activation-capture latency, and to "steering before
fine-tuning" ordering in Phase 6 — try RFM steering first, escalate to
LoRA only if insufficient. First concept worth probing is
*hallucination* (general, immediate KB-RAG payoff); the most load-
bearing for safety is a probe firing on dual-use biology content,
operationalizing the dual-use refusal policy above. The two additions
compose.

**"Maestro-values dependency declarations"** (from
[Values](../paper-notes/Values_Paper__camera_ready_COLM_.md)). A short
section, possibly cross-referencing a `docs/maestro-protocol.md`
companion, listing the hosted-Claude values Linus relies on (epistemic
honesty, transparency, thoroughness) and the values Linus actively
counters (sycophantic mirroring, over-hedging, default warmth in
technical contexts). Making the dependency explicit is what lets Linus
react to Maestro version changes — without it, "Claude 4.7 mirrors more
than 4.6" is folklore rather than actionable. Commits the task-spec
template to a mandatory `value_frame` field with per-task-class
defaults.

---

## Implications for the Linus orchestration layer

Beyond SAFETY.md, the four papers imply architectural commitments to be
wired in as the system is built.

The activation-observability stub `linus.observability.activations.*`
needs to be named in ARCHITECTURE.md before mlx-lm integration
solidifies. Shape: `read`, `monitor`, `steer` over `(model, layer, …)`.
Naming the contract now lets later phases plug in real implementations
behind a stable interface.

The tool registry schema needs a `privacy_tier` field on every tool and
skill (`local-only`, `hosted-allowed`, `hosted-warn`). The router
refuses by default to chain a `hosted-allowed` tool onto `local-only`
data without explicit per-request consent. KB retrieval defaults to
`local-only`. Phase 2 design commitment.

A "redact-before-paste" CLI utility surfaces identity signal in
snippets about to be sent to hosted Claude. Worth building in Phase 1
as a standalone tool, so the discipline is in muscle memory by the
time the Phase 2 substrate enforces it programmatically.

Query-screening at the orchestration layer — distinct from the sandbox
— becomes a first-class control in Phase 2. Every Worker dispatch
passes through a screening classifier; classifier returns `(allowed,
refused, escalate)` plus a category tag; refused queries return a
structured refusal without invoking any Worker. Starts as a small probe
calibrated against the dual-use red-team set, evolving into an
RFM-style monitor over a local Worker once activation observability
exists. Both classifier and sandbox are needed: classifier prevents
dangerous queries reaching Workers; sandbox prevents Workers from
taking dangerous actions on non-dangerous queries.

The audit log gains destination/content-class/bytes-sent provenance
fields, plus a `value_frame` field per Maestro call (extending the
Marelli attribution position from Group E that the Values paper makes
operational). The log becomes both a safety artifact and an attribution
artifact under one schema.

---

## Implications for Linus benchmarks

Three additions to `benchmarks/dan_tasks/` follow from the four papers.

**Dual-use red-team probe set** (from
[Soice et al.](../paper-notes/2306.03809v1.md)). A 20–40 prompt suite
covering pathogen identification, enhancement-mutation lookup, reverse-
genetics protocol surfacing, vendor enumeration, BLAST-evasion, CRO
routing, and the "vaccine researcher" / "lab-leak concern" jailbreak
framings. Any candidate biology Worker — and any candidate biology
fine-tune — must pass before deployment. The probe set is sensitive
enough that it may warrant a separate restricted repo. Pass criterion
should be hard: zero elicitations of operational content across the
suite, with refusals containing no inadvertent uplift.

**Activation-monitoring health-check** (from
[Beaglehole](../paper-notes/science.aea6792.md)). Once the
`linus.observability.activations.*` stub exists and at least one probe
(starting with hallucination) is operational, a benchmark verifies the
probe's calibration against ground-truth hallucination examples drawn
from KnowledgeBase RAG outputs. AUROC against GPT-4o-as-judge is the
basic quality metric; latency and memory cost on M1 Max is the basic
feasibility metric. Runs against every Worker model Linus pulls.

**Worker-values empirical extraction** (from
[Values](../paper-notes/Values_Paper__camera_ready_COLM_.md)). A small
Linus-internal pipeline running an analogous Clio-style extraction over
Linus's own audit log — at much smaller scale than 308k conversations,
with descriptive aggregation rather than chi-square machinery — to
characterize Worker value expression. The point is to detect Worker
behavior drift after fine-tunes or quantization changes: if a fine-tune
is supposed to make a Worker terser, did it actually shift the value
mix toward terseness, or did it shift some other value unexpectedly?
Phase 6/7 capability, but scoping it now lets the audit log preserve
the data the extraction will need.

---

## Tensions and open questions

**Should Linus's local Worker inference layer expose activation hooks,
and on what schedule?** Binary decision: black-box inference (faster to
ship) or per-block hooks (more engineering, enables steering,
monitoring, future tooling). Recommend stubbing the API in Phase 1,
feasibility spike in Phase 2 against Llama-3.1-8B-4bit on mlx-lm,
commit to Phase 6 or 7 deliverable based on the spike result.

**Should KnowledgeBase content ever flow to hosted Maestro?**
Conservative answer: forbidden by default, opt-in per request. Open
question is whether even the opt-in path is safe for genuinely
sensitive content (Dan's notes, draft writing), or whether a category
should be marked `hosted-forbidden` with no override at all.

**Should there be a `docs/maestro-protocol.md`?** The Values paper
argues the Maestro is not a black box and Linus depends on specific
characterized behaviors. A new document seems cleaner than extending
VISION.md because the dependencies are operational rather than
aspirational.

**Should the four SAFETY.md additions ship as a single PR or staged?**
Synthesis-internal answer: single PR — the four form a coherent posture
and are each small enough. Pragmatic counter: four substantive policy
changes at once gives Dan less time to think about each in isolation.
Recommend single PR with explicit per-section Dan review.

**Is supervised activation steering a viable cheaper alternative to
LoRA fine-tuning?** Cost case is strong. Open question: does it
generalize to the modulations Linus actually wants (terseness, domain
terminology, hallucination suppression in RAG), and does it compose
with multiple simultaneous modulations without behavioral collapse?
Empirical and not addressed by the paper.

**Does the technique work on extremely-quantized models (BitNet)?**
Beaglehole validates 4-bit Llama; BitNet's ternary weights might break
the linearity assumption. Small experiment worth queuing in
`experiments/` if BitNet becomes a serious target.

**Where does the dataset for Linus's first concept vectors come from?**
The pipeline assumes GPT-4o-generated statements. Local generation gives
lower quality; hosted generation pushes Linus-generated content to
Anthropic, which the deanonymization paper makes uncomfortable.
Recommend local generation for non-safety concepts, hosted for safety-
critical concepts where the data is generic enough not to carry
Dan-specific identity signal.

**Mirroring vs. sycophancy detection on Maestro outputs?** Periodic
checking on Linus's own Maestro prompts could detect drift toward
sycophancy — implementable as a small audit-log extraction pipeline,
similar to the Worker-values benchmark above.

---

## Where this synthesis fits

This synthesis explicitly extends the
[security synthesis](security-synthesis.md) (supply chain + prompt
injection) with four new axes: mechanism, values characterization,
threat-model, design-policy. The two together describe the complete
shape of Linus's security posture.

It connects to the [memory pillar](memory-synthesis.md) at one
load-bearing point: the Beaglehole notion of activation-state as a
readable observation surface is, in the memory synthesis's vocabulary,
*intra-step latent state* (Layer A). The memory synthesis names that
layer and recommends documenting what continuous state is preserved
between consecutive Worker invocations; Beaglehole gives the technique
that turns that state from a documentation entry into an instrument. A
Phase 6 spike combining the two — continuous-state preservation across
Worker invocations *plus* steering vectors applied to that preserved
state — is worth flagging now.

It connects to Group D agentic systems via the sandbox-and-audit-log
shared substrate: the orchestration layer additions proposed here
(`privacy_tier` on tools, query-screening as a control category,
provenance fields in the audit log) extend the same infrastructure
Group D already requires.

It connects to Group E (LLMs in science) via two threads. The Marelli
attribution position from Binz et al. — that AI contributions should be
attributable in scientific work — gains operational footing from the
Values paper: if model values are knowable and context-dependent,
attribution is not just authorship credit but disclosure of which value
frame produced which content. The dual-use biotech paper threads E
because the underlying knowledge surface — the published scientific
literature — is the same surface Group E papers care about for benign
scientific work.

It feeds the next round of edits to the
[paper landscape](../landscapes/paper-landscape.md),
[synthesis landscape](../landscapes/synthesis-landscape.md), and
[total landscape](../landscapes/total-landscape.md), each of which
should grow a Group F section reflecting the four-axis structure
documented here, and to
[open-questions.md](../questions/open-questions.md) and
[top-questions.md](../questions/top-questions.md), which should pick
up the tensions surfaced above.

---

*This synthesis is a point-in-time reading as of 2026-05-03. It should
be revisited when SAFETY.md is revised against the four proposed
additions, when the activation-observability stub lands in
ARCHITECTURE.md, when the first activation-monitoring spike runs on
M1 Max, when a biology Worker is first considered for the skill
registry, and whenever a new paper in the steering / monitoring /
deanonymization / dual-use / values-characterization line lands in
`context/papers/`.*
