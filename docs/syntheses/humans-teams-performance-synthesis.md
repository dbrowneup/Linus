# Humans, Teams & Performance Synthesis

## What this document is

A synthesis of two non-AI papers — Güllich, Barth, Hambrick & Macnamara's December 2025 _Science_ review of how the
highest levels of human performance are actually acquired, and Harvey, Cromwell, Johnson & Edmondson's 2023
_Administrative Science Quarterly_ paper on how innovation teams should structure their learning activities across
episodes. Despite saying nothing about language models, both inform Linus's design through the Maestro/Worker metaphor
and through Dan's own mid-career polymath profile. Group H is the smallest reading group in the corpus by paper count,
but the two papers braid together unusually tightly: at very different timescales they make the same anti-monotonic
argument against "more practice equals better performance," and that argument, read alongside the cognitive-throughput
pair already in the corpus ([Zheng-Meister](../paper-notes/PIIS0896627324008080.md);
[Sauerbrei-Pruszynski](../paper-notes/nihms-2096004.md)), gives the Maestro/Worker shape a rare three-scale coherence.
The headline practical claim is that **structure of practice dominates intensity of practice across every timescale
Linus operates on**, and that this should be reflected in at least one new VISION.md principle, one Worker-spec field,
one session-rhythm discipline, and one revision to the existing skills synthesis. Paper notes at
[`science.adt7790.md`](../paper-notes/science.adt7790.md) (Güllich) and
[`harvey-et-al-2023-...`](../paper-notes/harvey-et-al-2023-the-dynamics-of-team-learning-harmony-and-rhythm-in-teamwork-arrangements-for-innovation.md)
(Harvey).

## The papers at a glance

Güllich et al. review 19 datasets covering more than 34,000 adult international top performers — Nobel laureates, the
most renowned classical composers, Olympic medalists, the world's best chess players. Three findings replicate across
these otherwise unrelated domains. Early elite performers and adult elite performers are _largely different people_
(roughly 90% non-overlap among elite athletes and top-10 chess players, 92–99% among top childhood cognitive performers
vs. top-5% adult earners). Peak adult performance is _negatively correlated_ with early performance (senior world-top-3
chess players were on average 62 Elo points behind their later top-4-to-10 peers at age 14, despite ending up 48 points
ahead at peak). And the _predictors invert_: among youth, heavy discipline- specific practice and little
multidisciplinary practice predicts higher early performance; among adult world-class performers, the same correlations
flip sign. Pooled effect sizes for multidisciplinary-breadth and gradual-progress (Cohen's d ≈ 0.39–0.58) are
statistically indistinguishable across athletics, science, music, and chess.

Harvey et al. studied 102 innovation teams at a Fortune Global 500 telecom (seven-month contest) and 61 MBA project
teams (six-week class project). They distinguish four learning activities along a 2×2 of _internal/external_ and
_exploitation/exploration_: reflexive (internal exploitation — evaluating, refining, ADR-writing in Linus terms),
experimental (internal exploration — prototyping, spikes), vicarious (external exploitation), and contextual (external
exploration — scanning). Importing music theory's vocabulary, they argue reflexive learning is the _tonal_ activity —
the only one that sustainably repeats — and other activities should combine by short-term goal congruence: _harmonious
within an episode, dissonant across episodes_. Reflexive + vicarious within one episode helps performance; reflexive +
experimental or contextual within one episode hurts; alternating reflexive ↔ exploratory ↔ reflexive across episodes
produces a positive _rhythm_, mediated in Study 2 by _coordination quality_ — the cognitive state from reflexive
learning that lets the next episode's exploration land cleanly.

The papers share neither methodology nor field. What they share is a structural argument that the right way to think
about high performance is _non-monotonic_.

## Two scales of one finding

Both papers argue against the simplest model of practice — more reps, more output, more skill — and they do so at
strikingly different scales. Güllich operates at the _career_ timescale: across decades, early-narrow practice is
anti-correlated with adult excellence, and breadth followed by depth is the predictor of late peak performance. Harvey
operates at the _team-episode_ timescale: across weeks, conflicting-goal activities should be spread across episodes
rather than crammed into one, where they create dissonance and degrade output. At both scales, structure of practice
matters more than intensity. The youth athlete who does five sports for nine years and the innovation team that opens
reflexively, explores in the middle, and closes reflexively are doing the same thing at different timescales — managing
the shape of their work rather than maximizing throughput at any moment.

The cognitive-throughput pair makes the same claim at the third, smallest scale: Zheng-Meister document a roughly
10-bit/second conscious channel sitting above a massively parallel sensorimotor substrate; Sauerbrei-Pruszynski push
back on details but do not contest the basic shape — a slow attention-bottlenecked controller orchestrating fast
parallel pipelines. At the millisecond scale, brute-forcing more bandwidth through the conscious channel is not the
move; _structure_ — what gets routed through which pathway — is. Three independent literatures, three independent
timescales, the same anti-monotonic claim.

## The Maestro/Worker analogy at three timescales

Linus's Maestro/Worker metaphor — Dan plus hosted Claude as the slow deliberate controller, local Worker models as the
fast parallel executors — was chosen in Phase 0 because it described the way Dan and Claude were already working
together. The original justification was practical: the metaphor matched the observed pattern. What the Group H pair
adds, when read alongside the cognitive-throughput pair, is that the same shape recurs at three radically different
timescales of high human performance.

At the **intra-second scale**, Zheng-Meister and Sauerbrei-Pruszynski describe a slow ~10-bit/s conscious controller
above a massively parallel unconscious substrate — the conscious channel selects, plans, and routes, the parallel
substrate executes. At the **team-episode scale**, Harvey describes reflexive learning as the tonal home — the slow
integrative activity against which faster exploratory and vicarious activities are interpreted, with reflexive bookends
creating coordination quality and the exploratory middle doing the parallel generative work. At the **intra-career
scale**, Güllich describes early broad acquisition (parallel exploration of multiple disciplines, fast-cycling) feeding
a later integrative phase (slow, deliberate, deep cross-domain synthesis).

The three timescales differ by roughly nine orders of magnitude, and the mechanisms generating the shape are entirely
different — neural bandwidth constraints, social coordination dynamics, life-history opportunity costs. The metaphor
_should not_ survive that. The fact that it does — that "slow integrative controller above fast parallel executor"
describes a stable structural pattern across all three — is mild evidence that the Maestro/Worker metaphor is
load-bearing rather than merely convenient. It names a recurring solution to a recurring constraint: when bandwidth at
the controller is the bottleneck, the right architecture pushes parallelism to the layer below and reserves the
controller for selection, integration, and rhythm.

This does not mean Linus's Worker LLMs are equivalent to neurons or to MBA project-team members — the metaphorical leap
is real and should be flagged. What it does mean is that the architectural commitment — Maestro time is the scarce
input, push specifiable work to Workers, reserve Maestro attention for taste and direction — is consistent with how high
performance has historically been achieved across at least three independent domains when controller bandwidth is the
binding constraint. That is a coherence check the metaphor passes that it did not need to.

## Cross-cutting threads

**Validation of Dan's career arc.** The Güllich pattern — substantial multidisciplinary breadth followed by mid-career
integrative depth — is a recognizable description of Dan's actual trajectory: PhD biochemistry, BS environmental
science, 13 years of scientific Python, now adding Rust, agentic systems, LLM inference and fine-tuning, and the Linus
build itself. The paper makes this empirically the _predictor_ of long-term excellence at depth across athletics,
science, music, and chess, not a deviation from focus that needs correction. The actionable implication is more
permission than instruction: continued time spent acquiring new domains is not a distraction from biochemistry depth, it
is the documented complement to it.

**Implications for Linus's design constraints.** This translates into a soft but real constraint on Linus itself. If the
Güllich pattern is correct, Linus's value to Dan is partly conditional on Linus _not crowding out_ the cross-domain
time, bench work, and reading that the evidence says is generative for adult excellence. A Linus that becomes so
absorbing it monopolizes attention loses on the long-horizon axis even if it wins on the short-horizon productivity
axis. This is the substance behind the candidate VISION.md principle: _Linus aids multidisciplinary synthesis; it does
not amplify narrow specialization_. As a design constraint, this argues against UX choices that funnel Dan into a single
workflow, against KnowledgeBase defaults that retrieve only the most-specific match, and against roadmap items that
effectively ask Dan to become more of a Linus operator than he was before. Linus is a synthesis amplifier for someone
already doing the breadth work, not a substitute for it.

**Operational implications for Maestro/Worker scheduling.** Harvey's harmony/rhythm framework gives the orchestration
layer a more specific rule than "batch related work." Tasks sharing short-term goal — multiple refactors of the same
module, a sweep of test fill-ins, a documentation pass — _harmonize_ and can share a Worker session. Tasks pulling in
opposing directions — exploratory model selection alongside deletion-pass cleanup, speculative architecture sketching
alongside finalizing an implementation — are dissonant within an episode and should be sequenced across sessions. A
Worker spec that asks one Worker to "explore options for X _and_ finalize Y" is a decomposition error; it should split
into two specs in two sessions with a reflexive consolidation between. The small Worker-spec template change is to add a
`goal_orientation: [exploit | explore]` field for the orchestration layer to act on.

**Sharpening the skills synthesis.** The existing [skills-and-practices-synthesis](skills-and-practices-synthesis.md)
carries the claim that Dan's _domain expertise is itself a moat_. Güllich sharpens this. The 10,000-hours version of
domain depth is replicable by anyone willing to do the hours; what is rare, and what the empirical data identifies as
the predictor of world-class adult performance, is _cross-domain synthesis_. For Dan specifically the relevant stack
(biochemistry plus genomics plus scientific Python plus environmental science plus agentic systems plus operational
biotech experience) is not commonly stacked, and the synthesis derived from it is what no generalist prompt-seller can
produce. The skills synthesis should reflect this — the moat language should become _cross-domain expertise_, with
explicit reference to the Güllich grounding.

**Reconciliation with The Algorithm and Blitzscaling.** Both Group H papers sit in apparent tension with Blitzscaling's
"speed is information" and The Algorithm's "delete every step you can." The reconciliation is that the frames operate at
different units of analysis. Blitzscaling is about cycle time _within a project once started_; The Algorithm is about
deletion _within a decision_; Güllich and Harvey are about _the structure of practice across decisions and across
projects_. The structure-of- practice axis exists and matters in addition to the speed-and-deletion axis, not as a
replacement. Blitzscaling tells Dan to ship the v0 of Linus rough; Güllich tells Dan the v0 should not itself be a
vehicle for narrowing his work to one domain; Harvey tells Dan to alternate reflexive bookends with exploratory middles.
They sit at different scales and compose.

## Implications for Linus

**VISION.md design practice: deliberate multidisciplinary time allocation (adopted, S39 resolved 2026-05-06).**
VISION.md "The long view" section now carries an explicit paragraph: distributing research and tool-building effort
across biology, computer science, and infrastructure rather than deep-specializing is a design practice, not an
accident. The cross-domain fluency that Pauling exemplified is a practice Linus should keep pace with because Dan's
actual work spans domains. Downstream consequences this adoption carries: KnowledgeBase queries should favor
cross-discipline retrieval over single-subfield narrowing; Worker dispatch should surface analogies from neighboring
domains, not only the most-specific match; time-allocation defaults should reduce time on low-value execution _more_
than they expand Dan's exposure to new domains.

**Worker-spec template: `goal_orientation` field (deferred to Phase 3 spawner spec, S38 resolved 2026-05-06).** The
field — `goal_orientation: [exploit | explore]` with optional
`learning_type: [reflexive | experimental | vicarious | contextual]` — is an optional annotation rather than a hard
requirement at Phase 2. The Phase 3 spawner spec is the right home: a hard requirement at that stage forces every spec
author to state orientation explicitly, producing the disciplined decomposition Harvey's harmony/rhythm logic calls for.
At Phase 2 the annotation may be added voluntarily; the orchestration layer does not yet act on it programmatically. The
data to validate or falsify Harvey's transfer to LLM orchestration will accumulate as annotated specs build up.

**Session-rhythm health metric.** Score each session on whether it opens reflexively, contains an experimental or
exploratory beat in the middle, and closes with a reflexive bookend (checkpoint summary, ADR check, commit message).
Sessions lacking the closing bookend leave Harvey's coordination quality on the table. Testable on existing session logs
and commit history without any architecture change.

**Time-allocation guard.** An explicit lightweight commitment that Linus development does not consume the cross-domain
time Güllich identifies as generative. A Maestro-level discipline more than a codebase change — possibly an entry in
CLAUDE.md or a ROADMAP.md norm — but consequential because Linus is engrossing enough to risk it.

**Skills synthesis update.** Revise [skills-and-practices-synthesis.md](skills-and-practices-synthesis.md) to reframe
"domain expertise as moat" as "cross-domain expertise as moat," citing Güllich as empirical grounding. Touch the
entrepreneurial section in particular: Dan's differentiation rests not on biochemistry alone, not on Python alone, not
on AI infrastructure alone, but on the rare stacking of all three.

## Tensions and open questions

Three questions remain open; two have been resolved.

_Resolved: multidisciplinary preservation in VISION.md (S39, 2026-05-06)._ The "The long view" paragraph in VISION.md
now codifies deliberate multidisciplinary time allocation as a design practice. The question of which document was the
right home — VISION.md, CLAUDE.md, or ROADMAP.md — resolved in favor of VISION.md, with the principle phrased as design
practice rather than constraint.

_Resolved: `goal_orientation` as hard requirement vs. optional annotation (S38, 2026-05-06)._ Decision: optional
annotation deferred to the Phase 3 spawner spec. Spec authors may add the tag voluntarily at Phase 2; it becomes a named
field requirement when the spawner design lands.

First open question: whether the skills synthesis should be updated to replace "domain expertise as moat" with
"cross-domain expertise as moat," citing Güllich as empirical grounding. This change is small, the evidence is specific,
and the framing matters — the 10,000-hours version of narrow domain depth is replicable; the cross-domain stack is not.
Still pending as of 2026-05-08.

Second open question: whether a session-rhythm metric is worth tracking, or whether it would degrade into theatre —
sessions structured to score well on the metric rather than to do work well. The metric is cheap to prototype on
existing commit history; computing it retrospectively before instrumenting it as a prospective gate is the right move.
Still no prototype; still open.

Third question, for Dan rather than Linus: whether the Güllich finding actually changes current time allocation. The
current shape — Linus development, biochemistry work, Rust, agentic systems — already looks like the multidisciplinary
mix the paper identifies as generative. The implication may not be "change the shape" but "_protect_ the shape": be
explicit about the budget so that Linus, which is engrossing, does not silently consume it.

## Where this synthesis fits

This document sits next to four others in [`docs/syntheses/`](.) — security, LLM wiki, skills and practices, and the
memory pillar — and is the smallest by paper count and direct architectural impact. Its primary contribution is
interpretive. It sharpens the [skills-and-practices-synthesis.md](skills-and-practices-synthesis.md) moat claim from
"domain expertise" to "cross-domain expertise." It provides external grounding for the within-session vs. across-session
distinction that [`docs/specs/memory-architecture.md`](../specs/memory-architecture.md) formalizes as session memory vs.
episodic memory layers — Harvey's within-episode harmony vs. across-episode rhythm is the human-team analogue. And it
grounded the VISION.md design practice — deliberate multidisciplinary time allocation across biology, CS, and
infrastructure — which was adopted in VISION.md "The long view" (S39, 2026-05-06), propagating into KnowledgeBase
retrieval defaults, Worker dispatch preferences, and time-allocation norms.

The Maestro/Worker-at-three-timescales argument is the most original contribution and the one most worth carrying
forward into [`synthesis-landscape.md`](../landscapes/synthesis-landscape.md) and
[`total-landscape.md`](../landscapes/total-landscape.md). The metaphor was chosen for practical reasons in Phase 0; what
Group H and the cognitive-throughput pair together demonstrate is that the same shape — slow integrative controller
above fast parallel executor — is the recurring solution to bandwidth-limited high performance across at least three
independent domains and nine orders of magnitude. That is not proof the metaphor is correct for LLM orchestration; it is
evidence Linus's commitment to it is consistent with how high performance has historically been achieved when controller
bandwidth is the binding constraint, which is exactly the constraint Linus is built around.

Revisit when the skills synthesis is updated to the cross-domain framing (still pending as of 2026-05-08), when the
Phase 3 spawner spec lands and the `goal_orientation` field becomes a named requirement, and whenever a new paper in the
human-development or team-learning literature lands in `context/papers/`.

---

## References

### Paper-notes

- [`harvey-et-al-2023-the-dynamics-of-team-learning-harmony-and-rhythm-in-teamwork-arrangements-for-innovation`](../paper-notes/harvey-et-al-2023-the-dynamics-of-team-learning-harmony-and-rhythm-in-teamwork-arrangements-for-innovation.md)
  — Harvey, Cromwell, Johnson & Edmondson's 2023 _Administrative Science Quarterly_ paper introducing the 2×2 of
  reflexive / experimental / vicarious / contextual learning activities with the harmony-within-episode and
  rhythm-across-episodes prescription; the team-episode-timescale anchor of the synthesis.
- [`nihms-2096004`](../paper-notes/nihms-2096004.md) — Sauerbrei-Pruszynski commentary _The brain works at more than 10
  bits per second_ pushing back on details of the Zheng-Meister bandwidth estimate without contesting the slow-
  controller-over-parallel-substrate shape; second half of the millisecond-scale cognitive-throughput pair.
- [`PIIS0896627324008080`](../paper-notes/PIIS0896627324008080.md) — Zheng-Meister _The unbearable slowness of being:
  Why do we live at 10 bits/s?_ documenting the ~10 bit/s conscious channel above a massively parallel sensorimotor
  substrate; the millisecond-scale anchor for the Maestro/Worker three-timescale argument.
- [`science.adt7790`](../paper-notes/science.adt7790.md) — Güllich, Barth, Hambrick & Macnamara's December 2025
  _Science_ review of ~34,000 adult international top performers showing early-narrow practice is anti-correlated with
  adult excellence; the career-timescale anchor of the synthesis.
