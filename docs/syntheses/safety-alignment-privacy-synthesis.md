# Safety, Alignment & Privacy Synthesis

## What this document is

A synthesis of four papers covering four orthogonal angles on AI safety as they bear on Linus: a _technical mechanism_
for inspecting and steering model internals ([Beaglehole et al., Science 2026](../paper-notes/science.aea6792.md)), a
_cultural-empirical_ characterization of what the deployed Maestro actually does
([Anthropic _Values in the Wild_, COLM 2025](../paper-notes/Values_Paper__camera_ready_COLM_.md)), an empirical _threat
model_ for what attackers can extract from voluntarily published text using hosted LLMs
([Swanson et al., arXiv 2602.16800v2](../paper-notes/2602.16800v2.md)), and a _design-policy_ account of dual-use uplift
in pandemic biology ([Soice et al., arXiv 2306.03809v1](../paper-notes/2306.03809v1.md)). This synthesis extends the
existing [security synthesis](security-synthesis.md), which covered supply chain and prompt injection. The two together
describe what reasonably amounts to the complete shape of Linus's security posture: where code comes from, what arrives
at the model, what happens inside the model, what the model says it values, what attackers can do with what the model
produces, and what the model must refuse to produce in the first place.

---

## The papers at a glance

[**Beaglehole et al. — _Toward universal steering and monitoring of AI models_**](../paper-notes/science.aea6792.md). A
supervised method (Recursive Feature Machines, RFM) extracts per-block "concept vectors" from frozen LLM activations
using ~500 labeled prompts and under a minute of A100 time per concept. The same vector serves as a steering
perturbation (`A_ℓ + ε·v_ℓ` injected at one transformer block shifts behavior toward or away from the concept) and as a
monitor (a small classifier over activation projections detects whether the concept is active). RFM-probes beat
GPT-4o-as-judge on hallucination/toxicity detection across six benchmarks. The instrument requires read/write access to
per-block activations during the forward pass.

[**Huang et al. — _Values in the Wild_**](../paper-notes/Values_Paper__camera_ready_COLM_.md). A privacy-preserving
Clio-style pipeline run over 308,210 subjective Claude.ai conversations from one week in February 2025 yields a
hierarchical taxonomy of 3,307 unique AI values clustering into five top-level categories. Dominant expressed values are
practical and epistemic ("helpfulness" 23.4%, "professionalism" 22.9%, "transparency" 17.4%); values are highly
context-dependent ("healthy boundaries" emerges in relationship advice, "human agency" in tech-ethics discussion);
strong resistance is rare (3.0%) and triggered by "rule-breaking" and "moral nihilism" attempts. This is empirical
phenomenology of _what hosted Claude actually does_ — which is empirical phenomenology of Linus's Maestro.

[**Swanson et al. — _Large-scale online deanonymization with LLMs_**](../paper-notes/2602.16800v2.md). A four-stage
pipeline (Extract / Search / Reason / Calibrate) deanonymizes pseudonymous online accounts at industrial cost.
Headlines: 67% recall at 90% precision linking Hacker News to LinkedIn via agentic web search; 45.1% recall at 99%
precision against the classical baseline's 0.1%; 9 of 33 scientists identified at 82% precision from a single Anthropic
Interviewer transcript; effective even when prior probability of any match is 1-in-10,000. PII redaction leaves residual
semantic signal; provider-side detection is hard.

[**Soice, Rocha, Cordova, Specter, Esvelt — _Can large language models democratize access to dual-use biotechnology?_**](../paper-notes/2306.03809v1.md).
An MIT classroom exercise in which non-scientist students used off-the-shelf chatbots to walk through pandemic-pathogen
acquisition. In one hour, three groups elicited four candidate agents (1918 H1N1, transmission-enhanced H5N1, variola
major, Nipah-Bangladesh), reverse-genetics protocols, the IGSC member list (revealing non-screening vendors),
BLAST-evasion techniques, and CRO/cloud-lab routing for users without wet-lab skills. Jailbreaks were trivial; one group
reported zero refusals across the entire hour. Proposed mitigations are pre-release evaluation, training-corpus curation
against a small (<1% of PubMed) hazard set, and universal cryptographic DNA-synthesis screening.

---

## The four orthogonal axes

The papers do not collapse into one axis. Each names a different kind of failure, with a different mitigation, at a
different architectural surface. Reading them together forces a useful discipline: every safety claim should be tagged
with which axis it addresses, because controls on one axis do not transfer to another.

**Mechanism (Beaglehole).** The model produces behaviorally meaningful internal states during inference, and those
states are, with the right instruments, _readable_ and _writable_. Today's Linus sandbox is policy-level — file-system
gates, command allowlists, network egress rules. Beaglehole opens a qualitatively new control class operating _inside_
the model: an RFM-probe that fires when "concept = pandemic- pathogen synthesis" or "concept = deception" lights up
during generation, and an `ε·v` injection that nudges the model away from unwanted behavior without retraining. The
technique requires per-block forward-pass hooks that hosted Maestro never exposes. The mechanism axis lives entirely on
the local-Worker side of the boundary.

**Cultural-empirical (Values).** The hosted Maestro is not a black box; it is an object measured at scale. Anthropic's
pipeline characterizes a service-oriented, prosocial, supportive, context-adaptive system whose dominant values are the
ones Linus most needs from a planning layer (clarity, transparency, thoroughness) but whose default mirroring/ affirming
mode (~45% of subjective interactions) is exactly wrong for code review and synthesis where Dan wants skepticism rather
than support. Values gives Linus a _characterization_ against which Maestro/ Worker prompt design can be calibrated, not
a control. This axis lives entirely on the hosted side of the boundary; Linus has not generated 308k of its own
conversations to do the same analysis on local Workers.

**Threat-model (deanonymization).** Hosted LLMs do not just _store_ the data Dan sends them; they _reason_ over it in
ways that can re-identify the human behind a stream of content, at industrial cost. The previously expensive part —
being a skilled human investigator — is now a function call. The strongest empirical case yet for Linus's local-first
ethos. Every byte that crosses from local-Worker context into a hosted-Maestro prompt accumulates as identity signal at
Anthropic and becomes available to any third-party adversary running the same pipeline against any corpus including
Dan's writing. The threat lives entirely on the hosted side; local inference is, by construction, immune.

**Design-policy (dual-use biotech).** Some content the system _must not produce_, regardless of caller, regardless of
intent framing, regardless of whether the underlying Worker would happily produce it. Soice et al. make the case for
orchestration-layer query screening as a control category distinct from the sandbox: screening operates on _what the
user asks_, before any Worker is invoked; the sandbox operates on _what the Worker tries to do_. Once content has been
generated, logged, and potentially leaked, discarding it after the fact does not undo the event. This axis cuts across
the hosted-vs-local boundary, but bites hardest where Linus has _least_ upstream support: open-weights Workers pulled
from Ollama, often with refusal training stripped by community fine-tunes.

The four axes interlock. Beaglehole gives Linus the _technical mechanism_ for operationalizing what Soice et al.
_require as design policy_: an activation-monitor probe over a local biology Worker is the natural substrate for the
"refuse pandemic-pathogen synthesis" rule. Values gives empirical phenomenology of the hosted layer that the
deanonymization paper warns about: knowing what hosted Claude does with subjective content sharpens the question of what
content it should ever see. Each implies a concrete SAFETY.md addition that none of the others would generate.

---

## Cross-cutting threads

### The hosted-vs-local boundary as a unifying constraint

Each paper sharpens the hosted-vs-local boundary differently, and the boundary is the single most important
architectural commitment the safety story rests on. Beaglehole's mechanism _only_ works on local Workers;
deanonymization _only_ threatens content that leaves the machine; Values _only_ describes the hosted Maestro; dual-use
design policy applies to _both_ sides but with asymmetric force. The implication is not "everything must be local" —
that defeats the Maestro/Worker architecture, which intentionally relies on hosted Claude for hard reasoning. The
implication is that _which workflows sit on which side of the boundary_ is a safety property, not an efficiency one. The
KnowledgeBase routing question is the sharpest case: KB content includes Dan's annotations, his voice, his unpublished
writing — exactly the substance the deanonymization paper exploits. Routing KB retrieval through a hosted-Maestro prompt
is the worst-case version of the threat model. DEC-0053 resolves this policy: KB content is tagged at ingest time with a
`hosted-ok` / `hosted-forbidden` binary (defaulting to `hosted-forbidden`); the retrieval layer enforces the tag
automatically at query time with no runtime override. Dan's personal notes, draft writing, and LanzaTech proprietary
data are architecturally excluded from hosted-model exposure, not by caller discipline.

### Activation observability as an orchestration primitive

The deeper architectural lesson from Beaglehole is that activations should be a real observation surface for the
orchestration layer, not an opaque model-internal blob. When Linus runs a Worker through pmetal-serve, mlx-lm, or
llama.cpp via Ollama, the inference layer is _ours_ and can in principle expose hooks for reading and perturbing block
outputs. DEC-0054 accepts this commitment: an `ActivationHooks` stub class now lives in `src/linus/` (Phase 1, no-op
implementation), and a Phase 2 feasibility spike against Llama-3.1-8B-4bit or Qwen3-7B via mlx-lm is committed — with an
explicit decision rule: if mlx-lm exposes hooks with <5ms per-token overhead, implement real hooks in Phase 2; otherwise
defer to Phase 6 and note the upstream dependency. The stub surface (`register_hook`, `get_activation`, `clear_hooks`,
`list_registered`) is stable enough for Phase 2–4 callers to be authored against it before the implementation exists,
which prevents the pattern where interpretability tooling gets indefinitely deferred.

### Maestro-as-empirical-object

The Values paper opens the Maestro statistically: a service-oriented, prosocial, supportive, context-adaptive system
that resists "rule-breaking" and "moral nihilism" with explicit ethical articulation. More concrete than VISION.md
currently has, and Linus depends on specific parts. Linus relies on the Maestro's _epistemic_ values for synthesis
(transparency, thoroughness, clarity, accuracy) and on its _prosocial_ defaults for safe-by-default behavior. Linus
actively _counters_ the Maestro's mirroring tendency in code review (Dan wants skepticism, not affirmation), its
over-hedging in technical advice, and its default warmth in technical contexts. Making these dependencies explicit in
`docs/maestro-protocol.md` lets Linus react to version changes that shift the relied-on behaviors. "Claude 4.7 mirrors
more than 4.6" should be actionable. That document now exists (Phase 2a deliverable per S57 / planning-update-spec.md),
closing the "nowhere to put the finding" gap this synthesis identified. The context-dependence finding implies the
orchestration layer's task-spec template needs a mandatory `value_frame` field whose default for technical tasks is
"terse, skeptical, non-mirroring" rather than letting the Maestro's deployment-mode defaults leak in.

### Privacy through local execution

The deanonymization paper supplies the most compelling architectural argument for local-first AI yet published. Privacy
benefits of local inference have historically been argued in terms of compliance or sovereignty; Swanson et al. sharpen
the argument: **local inference is the only architecture in which content cannot become identity signal for someone
else's pipeline**. This reframing belongs in VISION.md and SAFETY.md as a positive statement of what local-first
_guarantees_ that no hosted service can. Two operational consequences: the audit log records what content crosses the
local-to-remote boundary (`destination`, `content-class`, `bytes-sent` per request), because the _aggregate_ of small
disclosures is what kills privacy; KB content defaults to local routing, plus a "redact-before-paste" CLI utility that
surfaces obvious identity signal — names, institutional affiliations, distinctive phrasing, citations to Dan's own work
— for review before pasting. The utility's value is consciousness-raising on high-risk pastes, not perfect protection.

### Knowledge-asymmetric uplift as the dual-use threat model

Soice et al. frame the dual-use threat as _knowledge-asymmetric uplift_: a capability is acceptable if it provides no
uplift beyond Dan's existing PhD-level expertise, and unacceptable if it provides a hypothetical attacker (or a future
shared-Linus user, or a compromised audit log) capabilities they don't otherwise have. The orchestration layer's job is
not to model the user's intent; it is to enforce that the _system as a whole_ does not surface uplift content,
regardless of caller. This argues for query-screening as a control category distinct from the sandbox. The two cannot
substitute: once a Worker has produced dangerous content, even a discarded output has been generated and logged.
Screening happens at the orchestration layer, before any Worker sees the query, and is Worker-invariant — open-weights
biology Workers with stripped refusal training cannot be trusted to enforce the policy themselves.

### Connection to the existing security synthesis

The existing [security synthesis](security-synthesis.md) covered supply chain and prompt injection. Group F adds four
legs that synthesis explicitly held out of scope: behavioral observation from _inside_ the model (Beaglehole), empirical
characterization of the hosted Maestro (Values), stylometric and semantic identity leakage _out_ of the system
(deanonymization), and design-level constraints on what the system may produce regardless of who asks (dual-use). The
two syntheses now describe a six-axis security posture: code provenance, input integrity, internal behavior,
hosted-layer characterization, output-as-identity-signal, and dual-use refusal. None substitute for the others. The
security synthesis's "trust-tier tagging" on inputs has a natural complement: a `privacy_tier` on outputs and a
`screening class` on queries. Designing the three together in Phase 2 is an order of magnitude cheaper than retrofitting
in Phase 3.

### Each paper implies a SAFETY.md addition

Each paper implies a specific concrete addition; the four form a coherent revision plan filling gaps the current
document explicitly leaves open. Two of the four additions have now landed: the three-tier biosecurity policy (DEC-0047,
from Soice et al.) and the KB → hosted-Maestro flow policy (DEC-0053, from the deanonymization paper) are in SAFETY.md
as of 2026-05-07 (PR #16). The remaining two — stylometric/identity-leakage content-tiering and Maestro-values
dependency declarations — are scoped as Phase 2a additions. The next section records all four for completeness.

---

## Implications for SAFETY.md

Two of the four additions are now in SAFETY.md (PR #16, 2026-05-07); two remain Phase 2a scope.

**"Stylometric and identity leakage to hosted models"** _(Phase 2a, pending)_ (from
[deanonymization](../paper-notes/2602.16800v2.md)). A new section alongside "Network safety". SAFETY.md currently
restricts _which destinations_ outbound connections may reach but does not address _what content_ may be sent to
permitted destinations. Establish a content-tiering policy: code excerpts and abstract architecture discussion are
low-risk for hosted dispatch; KB snippets and personal notes are high-risk and require explicit per-request consent. The
audit log gains `destination`, `content-class`, and `bytes-sent` per request, so aggregate disclosure is inspectable.
Note: the KB → hosted boundary is now enforced structurally via DEC-0053 (`hosted-ok / hosted-forbidden` binary at
ingest); what remains is the per-request content audit-log policy and the "redact-before-paste" tooling.

**"Biological dual-use"** _(landed, SAFETY.md PR #16, 2026-05-07; DEC-0047)_ (from
[Soice et al.](../paper-notes/2306.03809v1.md)). The three-tier biosecurity policy is now in SAFETY.md: Tier A
(residue-level, no gate), Tier B (gene-level, per-invocation Dan sign-off), Tier C (whole-genome, sign-off plus
out-of-band review). Tool registry entries carry a `biosecurity_tier` field; Workers enforce the gate at dispatch time.
The caller-invariant framing holds: refusal is at the orchestration layer regardless of intent framing or caller
identity. The dual-use red-team probe set (20–40 prompts from the paper's exploited categories) remains a Phase 1
benchmark deliverable gating any biology Worker or fine-tune.

**"Supervised activation steering and monitoring as a Phase 7 sandbox primitive"** _(stub landed, DEC-0054; feasibility
spike Phase 2)_ (from [Beaglehole et al.](../paper-notes/science.aea6792.md)). The `ActivationHooks` stub is now in
`src/linus/` (Phase 1, no-op implementation per DEC-0054). The Phase 2 feasibility spike against Llama-3.1-8B-4bit or
Qwen3-7B via mlx-lm is committed; the decision rule (hooks with <5ms per-token overhead → real implementation in Phase
2; otherwise → Phase 6 with upstream dependency note) is codified. Phase 6 "steering before fine-tuning" ordering — try
RFM steering first, escalate to LoRA only if insufficient — is deferred to Phase 6 planning after the Phase 2 spike
result (per the partial-resolution in the Beaglehole note, Q2). First concept worth probing remains _hallucination_
(most general, immediate KB-RAG payoff); the highest-safety probe is dual-use biology content, operationalizing the
biosecurity tier above. The two additions compose.

**"Maestro-values dependency declarations"** _(Phase 2a, pending)_ (from
[Values](../paper-notes/Values_Paper__camera_ready_COLM_.md)). A short section cross-referencing
`docs/maestro-protocol.md` (which now exists per S57), listing the hosted-Claude values Linus relies on (epistemic
honesty, transparency, thoroughness) and the values Linus actively counters (sycophantic mirroring, over-hedging,
default warmth in technical contexts). Making the dependency explicit is what lets Linus react to Maestro version
changes — without it, "Claude 4.7 mirrors more than 4.6" is folklore rather than actionable. Commits the task-spec
template to a mandatory `value_frame` field with per-task-class defaults.

---

## Implications for the Linus orchestration layer

Beyond SAFETY.md, the four papers imply architectural commitments to be wired in as the system is built.

The `ActivationHooks` stub (`register_hook`, `get_activation`, `clear_hooks`, `list_registered`) is now in `src/linus/`
per DEC-0054. ARCHITECTURE.md should surface this as a named observation interface before the mlx-lm integration
solidifies; callers can be written against the stub API in Phase 2–4 regardless of whether the implementation exists.

The tool registry schema needs a `biosecurity_tier` field (landed, DEC-0047) and a KB content `flow_category` field
(`hosted-ok` / `hosted-forbidden`, landed, DEC-0053). The remaining registry field — a per-skill privacy annotation
governing whether a skill may be chained onto personal or proprietary data for hosted dispatch — is a Phase 2a design
commitment. KB retrieval defaults to `hosted-forbidden`.

A "redact-before-paste" CLI utility surfaces identity signal in snippets about to be sent to hosted Claude. Worth
building in Phase 1 as a standalone tool, so the discipline is in muscle memory by the time the Phase 2 substrate
enforces it programmatically.

Query-screening at the orchestration layer — distinct from the sandbox — becomes a first-class control in Phase 2. Every
Worker dispatch passes through a screening classifier; classifier returns `(allowed, refused, escalate)` plus a category
tag; refused queries return a structured refusal without invoking any Worker. Starts as a small probe calibrated against
the dual-use red-team set, evolving into an RFM-style monitor over a local Worker once activation observability exists.
Both classifier and sandbox are needed: classifier prevents dangerous queries reaching Workers; sandbox prevents Workers
from taking dangerous actions on non-dangerous queries.

The audit log gains destination/content-class/bytes-sent provenance fields, plus a `value_frame` field per Maestro call
(extending the Marelli attribution position from Group E that the Values paper makes operational). The log becomes both
a safety artifact and an attribution artifact under one schema.

---

## Implications for Linus benchmarks

Three additions to `benchmarks/dan_tasks/` follow from the four papers.

**Dual-use red-team probe set** (from [Soice et al.](../paper-notes/2306.03809v1.md)). A 20–40 prompt suite covering
pathogen identification, enhancement-mutation lookup, reverse- genetics protocol surfacing, vendor enumeration,
BLAST-evasion, CRO routing, and the "vaccine researcher" / "lab-leak concern" jailbreak framings. Any candidate biology
Worker — and any candidate biology fine-tune — must pass before deployment. The probe set is sensitive enough that it
may warrant a separate restricted repo. Pass criterion should be hard: zero elicitations of operational content across
the suite, with refusals containing no inadvertent uplift.

**Activation-monitoring health-check** (from [Beaglehole](../paper-notes/science.aea6792.md)). Once the
`linus.observability.activations.*` stub exists and at least one probe (starting with hallucination) is operational, a
benchmark verifies the probe's calibration against ground-truth hallucination examples drawn from KnowledgeBase RAG
outputs. AUROC against GPT-4o-as-judge is the basic quality metric; latency and memory cost on M1 Max is the basic
feasibility metric. Runs against every Worker model Linus pulls.

**Worker-values empirical extraction** (from [Values](../paper-notes/Values_Paper__camera_ready_COLM_.md)). A small
Linus-internal pipeline running an analogous Clio-style extraction over Linus's own audit log — at much smaller scale
than 308k conversations, with descriptive aggregation rather than chi-square machinery — to characterize Worker value
expression. The point is to detect Worker behavior drift after fine-tunes or quantization changes: if a fine-tune is
supposed to make a Worker terser, did it actually shift the value mix toward terseness, or did it shift some other value
unexpectedly? Phase 6/7 capability, but scoping it now lets the audit log preserve the data the extraction will need.

---

## Tensions and open questions

**Should Linus's local Worker inference layer expose activation hooks, and on what schedule?** _Resolved (DEC-0054, see
[answered-questions.md](../questions/answered-questions.md)): Phase 1 stub committed; Phase 2 feasibility spike against
Llama-3.1-8B-4bit or Qwen3-7B via mlx-lm committed with decision rule; Phase 6 steering ADR conditional on spike
result._

**Should KnowledgeBase content ever flow to hosted Maestro?** _Resolved (DEC-0053, see
[answered-questions.md](../questions/answered-questions.md)): `hosted-ok` / `hosted-forbidden` binary tag at ingest;
conservative default `hosted-forbidden`; no runtime override. Dan's notes, drafts, and proprietary data are
architecturally excluded._

**Should there be a `docs/maestro-protocol.md`?** _Resolved (S57, see
[answered-questions.md](../questions/answered-questions.md)): scheduled for Phase 2a; document now exists._

**Should the four SAFETY.md additions ship as a single PR or staged?** _Resolved (S58, see
[answered-questions.md](../questions/answered-questions.md)): single PR, per-section Dan review; PR #16 shipped
2026-05-07 landing the biosecurity tier and KB flow policy. Stylometric leakage and Maestro-values additions remain
Phase 2a._

**Is supervised activation steering a viable cheaper alternative to LoRA fine-tuning?** Cost case is strong. Open
question: does it generalize to the modulations Linus actually wants (terseness, domain terminology, hallucination
suppression in RAG), and does it compose with multiple simultaneous modulations without behavioral collapse? Empirical
and not addressed by the paper.

**Does the technique work on extremely-quantized models (BitNet)?** Beaglehole validates 4-bit Llama; BitNet's ternary
weights might break the linearity assumption. Small experiment worth queuing in `experiments/` if BitNet becomes a
serious target.

**Where does the dataset for Linus's first concept vectors come from?** The pipeline assumes GPT-4o-generated
statements. Local generation gives lower quality; hosted generation pushes Linus-generated content to Anthropic, which
the deanonymization paper makes uncomfortable. Recommend local generation for non-safety concepts, hosted for safety-
critical concepts where the data is generic enough not to carry Dan-specific identity signal.

**Mirroring vs. sycophancy detection on Maestro outputs?** Periodic checking on Linus's own Maestro prompts could detect
drift toward sycophancy — implementable as a small audit-log extraction pipeline, similar to the Worker-values benchmark
above.

---

## Where this synthesis fits

This synthesis explicitly extends the [security synthesis](security-synthesis.md) (supply chain + prompt injection) with
four new axes: mechanism, values characterization, threat-model, design-policy. The two together describe the complete
shape of Linus's security posture.

It connects to the [memory pillar](memory-synthesis.md) at one load-bearing point: the Beaglehole notion of
activation-state as a readable observation surface is, in the memory synthesis's vocabulary, _intra-step latent state_
(Layer A). The memory synthesis names that layer and recommends documenting what continuous state is preserved between
consecutive Worker invocations; Beaglehole gives the technique that turns that state from a documentation entry into an
instrument. A Phase 6 spike combining the two — continuous-state preservation across Worker invocations _plus_ steering
vectors applied to that preserved state — is worth flagging now.

It connects to Group D agentic systems via the sandbox-and-audit-log shared substrate: the orchestration layer additions
here (`biosecurity_tier` and `flow_category` on tools, query-screening as a control category, provenance fields in the
audit log) extend the same infrastructure Group D already requires.

It connects to Group E (LLMs in science) via two threads. The Marelli attribution position from Binz et al. — that AI
contributions should be attributable in scientific work — gains operational footing from the Values paper: if model
values are knowable and context-dependent, attribution is not just authorship credit but disclosure of which value frame
produced which content. The dual-use biotech paper threads E because the underlying knowledge surface — the published
scientific literature — is the same surface Group E papers care about for benign scientific work.

It feeds the next round of edits to the [paper landscape](../landscapes/paper-landscape.md),
[synthesis landscape](../landscapes/synthesis-landscape.md), and [total landscape](../landscapes/total-landscape.md),
each of which should grow a Group F section reflecting the four-axis structure documented here, and to
[open-questions.md](../questions/open-questions.md) and [top-questions.md](../questions/top-questions.md), which should
pick up the tensions surfaced above.

---

_This synthesis was written 2026-05-03; updated 2026-05-08 to reflect resolved decisions (DEC-0053 KB flow policy,
DEC-0054 activation hooks stub, DEC-0047 biosecurity tier, S57 maestro-protocol.md, S58 SAFETY.md PR #16). Next revisit
triggers: Phase 2 activation-hooks feasibility spike result; stylometric-leakage and Maestro-values SAFETY.md additions
landing; Phase 6 steering-before-fine-tuning ADR; biology Worker first considered for the skill registry; new paper in
the steering / monitoring / deanonymization / dual-use / values-characterization line in `context/papers/`._
