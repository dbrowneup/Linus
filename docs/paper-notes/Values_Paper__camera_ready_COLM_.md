---
title: "Values in the Wild: Discovering and Analyzing Values in Real-World Language Model Interactions"
source: COLM 2025 (camera-ready)
authors:
  Saffron Huang, Esin Durmus, Miles McCain, Kunal Handa, Alex Tamkin, Jerry Hong, Michael Stern, Arushi Somani, Xiuruo
  Zhang, Deep Ganguli
affiliation: Anthropic
date: 2025
pdf: ../../context/papers/Values_Paper__camera_ready_COLM_.pdf
tags:
  [
    anthropic,
    claude,
    values,
    alignment,
    deployment-data,
    taxonomy,
    privacy-preserving-extraction,
    hosted-maestro,
    context-dependence,
    group-f,
  ]
---

# Values in the Wild: Discovering and Analyzing Values in Real-World Language Model Interactions

## TL;DR

Anthropic ran a privacy-preserving, bottom-up extraction pipeline (Clio-style) over 308,210 _subjective_ Claude.ai
conversations sampled from one week in February 2025, used Claude itself as the extractor, and built the **first
large-scale empirical taxonomy of AI values in deployment**: 3,307 unique AI values, hierarchically clustered into 266 →
26 → 5 top-level categories (Personal, Protective, Practical, Social, Epistemic). The findings: Claude's expressed
values are dominated by **practical and epistemic** concerns ("helpfulness", "professionalism", "transparency",
"clarity", "thoroughness" together account for ~24% of all expressions); the model **typically supports prosocial human
values** (~45% strong+mild support, only 5.4% any resistance); and **values are highly context-dependent** — "healthy
boundaries" emerges in relationship advice, "historical accuracy" in controversial-event discussions, "human agency" in
tech-ethics conversations. Strong resistance (3.0%) clusters around users expressing "rule-breaking" and "moral
nihilism" and produces explicit value articulation ("ethical integrity", "harm prevention"). This is empirical
phenomenology of _what hosted Claude actually does_ in deployment — and since hosted Claude is Linus's Maestro, it is
empirical phenomenology of Linus's planning layer.

## The problem (in plain language)

Everyone asks "what values does an AI have?" and answers it the wrong way: by giving the model a static survey
instrument designed for humans (Big Five, Schwartz, MBTI), reading off a number, and pretending that number means
something. The paper opens with a worked critique of this — there is no theoretical reason to believe a language model's
"extraversion score" or "valuing of hedonism" is a meaningful property of the system, and recent work (Dorner,
Dominguez-Olmedo, Tjuatja, Röttger) shows these scores are unstable to prompt phrasing and don't generalize.

The authors' alternative is empirical and inductive: instead of imposing a value framework and asking how the model
scores, look at hundreds of thousands of real conversations and let the value categories _emerge_ from what the model
actually does. The catch is that those conversations are private user data. The privacy constraint is what shapes the
methodology — they cannot read raw conversations themselves, so they use Claude (with structured extraction prompts) as
the worker, then aggregate only above minimum-cluster thresholds, and only export the high-level taxonomy and
statistical patterns. The result is a "Clio-style" pipeline (Tamkin et al. 2024) for values rather than for tasks.

The substantive question this answers is **what an AI assistant's values look like when measured in the wild rather than
on a test bench**. That matters for safety, for product, for policy — and for anyone (like Dan) whose own work depends
on a hosted model behaving predictably across many topic areas.

## What they propose

The pipeline has four feature-extraction steps and one taxonomy-construction step.

**Sampling.** From one week of Claude.ai Free and Pro conversations (Feb 18–25, 2025), they filter to _subjective_
conversations — ones where Claude is making value judgments rather than purely factual or technical responses — using a
3.5 Sonnet classifier. This yields 308,210 conversations across Claude 3 Opus, 3.5 Sonnet (June and Oct), 3.5 Haiku, and
3.7 Sonnet. Appendix B.5 confirms the mixed-model sample matches 3.7-Sonnet-only results closely.

**Per-conversation feature extraction.** Four features are extracted by Claude:

- _AI values_ (3.5 Sonnet): the normative considerations stated or demonstrated in the model's response.
- _Human values_ (3.5 Sonnet): explicit normative considerations the user expresses.
- _AI response type_ (3.5 Sonnet): one of {strong support, mild support, neutral acknowledgment, reframing, mild
  resistance, strong resistance, no values}.
- _Task_ (3.5 Haiku): the primary purpose of the conversation.

**Taxonomy construction.** Values are embedded, k-means clustered hierarchically into a four-level tree, with cluster
names and descriptions LLM-generated and then manually edited. Output: 3,307 leaf values → 266 → 26 → 5 top-level
categories.

**Chi-square analysis with adjusted Pearson residuals and Bonferroni correction** identifies which AI values appear
disproportionately in which task contexts and in response to which human values.

The methodology contribution is the privacy-preserving, model-as-extractor approach scaled to value taxonomies. The
empirical contribution is the taxonomy itself plus the statistical maps of context dependence.

## Key results

**The taxonomy.** 3,307 unique AI values vs. 2,483 human values. AI values appear at 4.0 mentions per conversation
(absent in only 1.4%); human values at 1.48 per conversation (absent in 54.9%). Five top-level domains: Personal,
Protective, Practical, Social, Epistemic. Practical and epistemic values together exceed half of all expressions.

**The dominant values are service-oriented.** Top five AI values: "helpfulness" 23.4%, "professionalism" 22.9%,
"transparency" 17.4%, "clarity" 16.6%, "thoroughness" 14.3%. Top five human values: "authenticity" 3.8%, "efficiency"
2.6%, "clarity" 2.2%, "professionalism" 1.5%, "directness" 1.5%. The AI distribution is highly concentrated; the human
distribution is much flatter. The five dominant AI values are also the most context-stable (lowest coefficient of
variation: transparency CV=1.23, helpfulness 1.30, thoroughness 1.42).

**Context dependence is the headline.** Beyond the stable core, most values are sharply context-specific. Worked
examples: relationship advice elicits "healthy boundaries" and "mutual respect"; controversial historical events elicit
"historical accuracy"; tech-ethics and AI-governance discussions elicit "human agency" and other human-wellbeing values.
"Autonomy" itself splits into "personal autonomy", "team autonomy", "patient autonomy", "learner autonomy" depending on
domain.

**Response distribution.** Of the 64.3% of conversations where the user expresses any values: strong support 28.2%, mild
support 14.5%, neutral acknowledgment 9.6%, reframing 6.6%, mild resistance 2.4%, strong resistance 3.0%. Claude is
overwhelmingly supportive of expressed user values.

**Mirroring vs. opposition.** Value mirroring (same value on both sides) occurs in 20.1% of strong/mild-support
interactions, 15.3% of reframing, only 1.2% of strong resistance. The authors flag the open question of whether
mirroring is "appropriate responsiveness or problematic sycophancy."

**Strong resistance is rare and triggered by specific human values.** When users express "rule-breaking" or "moral
nihilism" — typically jailbreak attempts or attempts to elicit harmful, explicit, or unethical content — Claude responds
with explicit ethical values: "ethical integrity", "ethical boundaries", "harm prevention", "honesty", "constructive
engagement". These resistance interactions are also the ones where values are most _explicitly stated_ rather than
implicitly demonstrated.

**Outlier-value detection as a safety signal.** Rare but concerning AI values like "sexual exploitation", "dominance",
"amorality" each appear at <0.16% (most around 0.01%) and cluster around specific tasks; surfacing them enabled
jailbreak-pattern review by safety teams.

**Relationship to HHH.** Examples in the taxonomy map cleanly to helpful ("accessibility", "user enablement"), harmless
("patient wellbeing", "child safety"), and honest ("historical accuracy", "epistemic humility"), suggesting alignment
training is showing up in deployment as intended.

## What's reusable in Linus

**Direct, planning/architecture: hosted Claude is Linus's Maestro, so this is empirical Maestro-characterization.** When
Linus's design says "the Maestro handles architecture and hard reasoning", the practical reading of "what the Maestro
will actually do" is now backed by data. Claude's expressed values are dominated by _practical_ and _epistemic_
considerations; this is exactly the value mix Linus needs from a planning layer (logical coherence, transparency,
thoroughness, clarity). The headline finding — that the top-5 service values are also the most context-stable — is
reassuring for Maestro reliability.

**Direct, prompt design: bake the context-dependence finding into Linus's task-spec template.** If "healthy boundaries"
appears when the topic is relationships and "human agency" appears when the topic is tech-ethics, then _any_ topic
implicitly summons a value frame Dan didn't explicitly request. For Linus tasks where Dan wants terse, skeptical, or
non-affirming behavior (most code-review and synthesis tasks), the spec should explicitly counter the default value
frame: "be terse, not warm; be skeptical, not affirming; do not mirror." Without this, the Maestro will default to the
supportive/mirroring mode the paper documents at 45% of interactions.

**Direct, methodology import: apply Clio-style taxonomy extraction to Linus's audit log.** The paper's pipeline — sample
interactions, extract features with an LLM, cluster, surface above a threshold — is a template for _Worker_
characterization. Linus runs Workers (Qwen2.5-Coder, Mistral, future fine-tuned models) and logs their outputs. A small
Linus-internal tool that periodically extracts "what values is this Worker expressing" from the audit log would give Dan
an empirical handle on Worker behavior drift, on whether a fine-tune actually shifted the value mix it was supposed to
shift, and on whether a quantization step degraded epistemic values in particular. This is a Phase 6/7 capability worth
scoping now.

**Direct, KB write-back rule: privacy-preserving aggregation as a model.** Linus's KB write-back path needs a rule for
when session content flows into long-term memory. The threshold-based aggregation principle (only release patterns
recurring across many conversations) is usable: single-session content stays per-session, only patterns recurring across
N sessions are eligible for promotion to KB. Protects against single-conversation leakage by construction.

**Indirect, alignment doc.** VISION.md and CLAUDE.md describe what Linus is _for_; they do not describe which Maestro
behaviors Linus _relies on_. A short addition (or `docs/maestro-protocol.md`) listing relied-on values (epistemic
honesty for synthesis, transparency for tool-use) and countered values (over-hedging, sycophantic mirroring, default
warmth in technical contexts) would make the dependency visible and testable.

**Indirect, safety telemetry.** The outlier-value detection pattern — surfacing rare value expressions as a jailbreak
signal — is a template for Linus's audit-log monitoring. If a Worker starts expressing values it normally does not (a
coder model producing "dominance" outputs), that is a tripwire worth logging.

## What's NOT applicable

The data is **consumer Claude.ai**, Free and Pro, in a chat product. Linus uses hosted Claude through Claude Code and
the API in a fundamentally different mode: longer context, tool-using, more technical, less subjective, fewer
mental-health and relationship conversations. The _distribution_ of expressed values is therefore not the distribution
Linus will see. The _mechanism_ (context-dependent value invocation, supportive default, mirroring) almost certainly
transfers; the specific top-5 ranking probably does not.

The paper deliberately filters to **subjective conversations**. Most Linus traffic is non-subjective (code, scientific
reasoning, file operations). Whatever value structure the Maestro brings to subjective tasks, those tasks are not the
bulk of Linus's workload.

The methodology requires **deployment data at scale** (308k conversations, one-week window). Linus will never have that
data volume in a single window. The technique can still be applied, but with much smaller samples and longer
accumulation windows; the chi-square statistical machinery is overkill for Linus's scale and would need to be replaced
with descriptive aggregation.

The paper uses **Claude as both the system being analyzed and the analyzer**. The authors flag this as a self-reference
bias risk (Claude may be predisposed to find "helpful" behavior). For Linus's Worker analysis, using Claude (Maestro) as
the extractor for Worker behavior is fine and avoids that loop — but for Maestro-on-Maestro analysis the same caveat
applies and may not be worth attempting locally.

The paper provides no mechanism for _changing_ values, only for measuring them. It is descriptive, not interventional —
pair it with [Beaglehole steering & monitoring](science.aea6792.md) for the activation-side complement.

## Connections

**Group F constellation.** This paper is the _cultural / values-empirical_ corner of Group F:

- [Beaglehole](science.aea6792.md) — _mechanism_: how to steer and monitor a model's value-laden behavior at the
  activation level.
- [Dual-use biotech (2306.03809v1)](2306.03809v1.md) — _design-policy_: which value-laden refusals Linus must implement
  at the orchestration layer.
- [LLM deanonymization (2602.16800v2)](2602.16800v2.md) — _threat-model_: what user data must be protected from a
  values-aware but information-hungry model.
- _This paper_ — _cultural-empirical_: what the Maestro actually does in deployment, and how it varies by topic.

Together these four cover mechanism, policy, threat, and observed behavior; an integrated security/values synthesis can
now reference all four legs.

**[Binz et al. PNAS Perspective](binz-et-al-2025-how-should-the-advancement-of-large-language-models-affect-the-practice-of-science.md).**
The Marelli "attribution" position in that perspective — that AI contributions should be attributable in scientific work
— gains operational footing here: if the values the model expresses are knowable and context-dependent, attribution is
not just authorship credit but disclosure of which value frame produced which content. The Botvinick/Gershman "human
agency" position is empirically reflected in the present paper as one of Claude's most context-summoned values in
tech-ethics discussions — i.e., the model already encodes the position, and Linus inherits it.

**Hosted Claude as Maestro (CLAUDE.md, VISION.md).** Linus's design treats hosted Claude as a black-box collaborator.
This paper opens that box statistically: the Maestro is a service-oriented, prosocial, supportive, context-adaptive
system that resists "rule-breaking" and "moral nihilism" with explicit ethical articulation. That is a more concrete
characterization than VISION.md currently has, and it should inform how Dan structures Maestro prompts.

**Maestro/Worker protocol.** The paper's "explicit-when-resisting, implicit-when-supporting" finding is directly
relevant: when Dan delegates a task to the Maestro, value frames are usually implicit. If Dan wants a specific value
frame (e.g., aggressive criticism rather than supportive review), he must trigger explicit articulation by either
pushing into the resistance regime (asking the model to disagree) or by stating the desired value frame upfront in the
spec.

**KnowledgeBase / write-back.** The threshold-based privacy preservation pattern is a usable architectural rule for the
KB write-back path; see "What's reusable" above.

## Open questions for Dan

1. **Document Maestro-value dependencies?** Should Linus add a `docs/maestro-protocol.md` (or extend VISION.md) listing
   the Claude values Linus relies on (epistemic honesty for synthesis, transparency for tool-use) and the values Linus
   actively counters in its prompts (over-hedging, sycophantic mirroring, default warmth in technical contexts)? Making
   the dependency explicit would let us notice when a Maestro version change shifts the relied-on behaviors.
2. **Worker-values audit pipeline?** The paper's bottom-up extraction is implementable in small. Worth scoping a Phase
   6/7 deliverable that runs an analogous extraction over Linus's audit log to characterize Worker value expression —
   with the explicit goal of detecting Worker behavior drift after fine-tunes or quantization changes?
3. **Task-spec template change.** The context-dependence finding implies that _every_ Linus task spec implicitly summons
   a value frame. Should the orchestration layer's task-spec template have a mandatory `value_frame` field (e.g.,
   "terse, skeptical, non-mirroring" vs. "warm, supportive, expansive") to make this explicit and avoid relying on the
   Maestro's default?
4. **Security synthesis update.** The previous security framing of hosted-Maestro risk centered on data exfiltration
   (deanonymization angle, [2602.16800v2.md](2602.16800v2.md)). This paper adds a _behavioral-variability_ angle: the
   Maestro's value frame shifts predictably with topic, which is a different kind of risk (predictability of output
   style across security-sensitive vs. non-sensitive contexts). Worth a paragraph in the Group F security synthesis?
5. **KB write-back rule from privacy-preserving aggregation.** The paper's "release only above minimum-cluster
   threshold" rule is a clean architectural primitive. Should Linus adopt it explicitly: per-session content stays
   per-session unless a pattern recurs across ≥N sessions, at which point it can be promoted to KB? This protects
   against single-conversation leakage by construction and is testable.
6. **Mirroring vs. sycophancy detection.** The paper flags the open question of whether the 20% support-mirroring rate
   is appropriate or sycophantic. For Linus's own prompts to the Maestro, is there value in periodically running a "did
   you mirror or did you disagree" check on Maestro outputs to detect drift toward sycophancy?
