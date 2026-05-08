---
title: "How should the advancement of large language models affect the practice of science?"
source: PNAS Perspective, 2025, Vol. 122 No. 5, e2401227121 (DOI: 10.1073/pnas.2401227121)
authors: Marcel Binz, Stephan Alaniz, Adina Roskies, Balazs Aczel, Carl T. Bergstrom, Colin Allen, Daniel Schad, Dirk Wulff, Jevin D. West, Qiong Zhang, Richard M. Shiffrin, Samuel J. Gershman, Vencislav Popov, Emily M. Bender, Marco Marelli, Matthew M. Botvinick, Zeynep Akata, Eric Schulz
affiliation: Max Planck Institute for Biological Cybernetics; Helmholtz Munich; multiple
date: 2025-01
pdf: ../../context/papers/binz-et-al-2025-how-should-the-advancement-of-large-language-models-affect-the-practice-of-science.pdf
tags: [llms-in-science, philosophy-of-science, attribution, accountability, transparency, open-source-llms, human-agency, group-e-meta]
---

# How should the advancement of large language models affect the practice of science?

## TL;DR

A PNAS Perspective in which the editors invite **four research groups** to debate the role LLMs should play in science,
then have each group **respond to the others** in print. The four positions: **Schulz et al.** — LLMs should be treated
as knowledgeable research assistants, and existing scientific norms suffice; **Bender et al.** — LLMs are word-form
models, not meaning models, and bespoke lightweight tools will outperform them for most scientific tasks; **Marelli et
al.** — what we need are **principles** (transparency, accountability, fairness) plus explicit attribution of LLM
contributions, including extending the CRediT taxonomy; **Botvinick & Gershman** — even if AI matches human capability,
two aspects of science should be reserved for humans: the **normative** choice of what to study and the **epistemic**
goal of human understanding. Three of the four converge on "researcher remains accountable" but disagree sharply on
whether LLMs are best framed as collaborator, tool, or hazard. For Linus, the paper is a concise inventory of the
philosophical commitments Dan is implicitly making by building a private orchestration layer at all.

## The problem (in plain language)

LLMs are flooding into scientific workflows — drafting papers, summarizing literature, writing code, suggesting
experiments, even reviewing manuscripts — but the academic community has no shared framework for thinking about what
role they should play. The vibe oscillates between Terence Tao's "AI co-author by 2026" and Bender et al.'s "stochastic
parrots that fabricate citations," and journal policies (PNAS, Nature, Science, ICML, ACL) have been written reactively
rather than from principle. The PNAS editors decided the productive move was not to publish a single consensus statement
but to **stage an explicit debate** between four groups that would otherwise talk past each other.

The substantive question is whether LLMs require a **new** category in scientific practice or whether existing norms
(authorship, plagiarism, citation, reproducibility, peer review) already cover them. Schulz et al. say no new norms are
needed — LLMs are like research assistants and we already know how to manage research assistants. Bender et al. say no
new norms are needed either, but for the opposite reason: LLMs are tools, and most bad uses are already prohibited.
Marelli et al. say existing norms need elaboration into explicit principles plus new attribution conventions. Botvinick
and Gershman shift the question to: even if LLMs become technically capable of doing all of science, which parts should
we **refuse** to delegate, and on what grounds?

For someone building a private LLM orchestration system, each position implies a different design. Surfacing them is the
point of this note.

## What they propose

The paper does not propose a single position. It proposes a **structure for the debate**: four perspectives plus four
responses, with the editorial framing deliberately light.

**Schulz et al.** propose treating LLMs as research-assistant-like collaborators and leaning hard on **open-source
models** as the way to recover reproducibility — they cite an experience where their own results stopped reproducing
mid-revision because a proprietary provider silently updated the model. Recommendations: keep existing norms; rely on
locally-runnable open models; collaborate with developers to fix shortcomings.

**Bender et al.** propose treating LLMs as one of several tools and usually not the right one. Their core claim is that
LLMs model **word-form distributions**, not meaning, and the future of machine-aided science is "an ensemble of bespoke
and often lightweight models that have been designed explicitly to solve the specific tasks at hand." They argue current
LLM hype is actively diverting funding and attention from these targeted approaches, and explicitly reject the
research-assistant frame: tools produce errors, people learn from mistakes — research assistants belong in the second
category.

**Marelli et al.** propose a **principles-based** approach: transparency (acknowledge LLM use, ideally release prompts
and responses; favor models that disclose architecture and training data); accountability (researcher remains
responsible regardless of source); fairness (LLMs reflect WEIRD populations and risk reinforcing existing inequities).
They suggest extending the **CRediT taxonomy** to encode the nature of AI contribution, even though AI cannot itself be
a co-author. They reject the collaborator frame (LLMs lack metacognition, values, introspection) but agree LLMs should
be used.

**Botvinick & Gershman** propose what they call the **subjective limit**: AI should be excluded from two roles
regardless of capability — choosing what problems to study (normative) and being the entity that understands the answer
(epistemic). Their argument is not "AI cannot do these things" but "we should not let it, even if it can." Schulz et al.
respond that this is too restrictive — if an AI proves itself good at picking fruitful problems, why refuse the help?
Botvinick and Gershman counter that elevating AI to true collaborator status would entail granting personhood, a
sociological commitment far beyond science.

## Key results

This is a Perspective, so "results" means points of agreement and disagreement that fall out of the debate.

**Where the four agree.** All four converge on: (1) the researcher remains ultimately accountable for any output that
enters the scientific record; (2) science is fundamentally a social process whose integrity depends on norms beyond
technical capability; (3) the rapid pace of LLM development means rules written today will be obsolete soon, so the
focus should be durable principles rather than specific prohibitions; (4) transparency about LLM use matters, even where
the groups differ on enforcement.

**Where they sharply disagree.** Schulz vs. Bender on the **collaborator vs. tool** framing is the deepest split,
because it determines whether LLM "mistakes" are intelligible or merely affordance-failures. Marelli and
Botvinick/Gershman both side with Bender on this; the Schulz collaborator frame is a minority of one out of four.

**Schulz vs. Botvinick/Gershman on autonomy** is the **roadmap-delegation question** in its purest form. Schulz: if an
LLM is good at choosing topics, let it. Botvinick/Gershman: no, because the choice of what to study is constitutive of
the scientific community.

**Bender's universal-tool claim** is the most empirically contestable position in the paper: that bespoke specialized
models will outperform LLMs for most scientific tasks. Schulz pushes back that LLMs are widely adopted _because_ they
are universal, and the cost of building and learning bespoke tools usually exceeds the specialization gain.

**Marelli's CRediT extension** is the most actionable artifact in the paper — the one suggestion that translates
directly into a procedural change a journal or project could adopt tomorrow.

**Galactica is the recurring negative example.** Meta's science-specific LLM, taken offline after three days for
fabricating papers and authors, is cited by both the introduction and Bender et al. as the canonical failure mode.

## What's reusable in Linus

**The four perspectives map directly onto Linus design choices, and Linus implicitly takes a position on each.** This is
the most useful thing in the paper for the project, and worth making explicit in project documentation rather than
leaving implicit.

**Schulz et al. (collaborator-like, open-source).** Linus operationalizes the open-source half of Schulz — the project
exists because Dan agrees that proprietary providers cannot be relied on for reproducible scientific work. The
Maestro/Worker framing in CLAUDE.md is also a softer version of Schulz's "collaborator" language. One important
deviation: hosted Claude is allowed in the Maestro role despite being proprietary, because Dan's _own_ judgment is the
final accountability layer (which is the Marelli position, not the Schulz position).

**Bender et al. (LLMs misused/overhyped, prefer bespoke tools).** Linus's plan to build "domain-specific tools backed by
Dan's knowledge base" (CLAUDE.md, North Star) is the bespoke-tools half of Bender embedded inside an LLM orchestration
layer. KnowledgeBase, the planned scientific tool registry, and the deliberate calibration language ("Hosted Claude +
Dan = Maestro" rather than "Linus replaces hosted Claude") all align with Bender's caution. The dual-use biotech paper
(`paper-notes/2306.03809v1.md`, same wave) is a sharp instantiation of Bender's misuse concern; SAFETY.md and the
autonomy tier scheme are implicit acknowledgments that this worry is well-founded.

**Marelli et al. (transparency, accountability, fairness, attribution).** This perspective maps most directly onto a
concrete Linus engineering deliverable: the **audit log**. A Marelli-compliant audit log would record, per Worker
output: which model, which prompt, which retrieved context, which tools, which time, with what citations claimed and
what citations actually retrieved. That is more than most audit logs do today and is a useful design constraint to set
early. The CRediT-extension suggestion is worth holding for when Dan eventually publishes papers using Linus.

**Botvinick & Gershman (humans retain agency over the roadmap).** This is the perspective most aligned with the existing
**Maestro budget discipline** convention. It strengthens the principle that **roadmap decisions should not be delegated
to Workers or to hosted Claude** — they are normative judgments in the Botvinick/Gershman sense. ROADMAP.md,
ARCHITECTURE.md, and the phase plan are exactly the artifacts this perspective marks as off-limits to AI generation.
They can be _drafted_ with AI help (Schulz and Marelli are both fine with this), but the choice of what Linus is _for_
must remain Dan's.

**Specific actionable suggestion.** VISION.md or CLAUDE.md should consider adding a short section naming the four
perspectives and identifying which Linus implicitly endorses. The sentence "Linus exists because Dan endorses Schulz on
open-source, Bender on bespoke domain tools, Marelli on attribution, and Botvinick/Gershman on roadmap agency" is a
stronger anchor than the current language, immediately legible to a future contributor or to hosted Claude in a future
session.

## What's NOT applicable / hype filter

The paper's audience is scientists publishing in PNAS — it discusses authorship, peer review, manuscript fabrication,
journal policy. Linus is not a publishing system; publication-bound prescriptions (CRediT updates, dedicated
AI-disclosure statements in method sections, prompts as supplementary materials) do not translate directly. They are
useful as templates for internal practices, not as deliverables.

The paper says nothing about local inference, hardware constraints, Apple Silicon, MLX, or fine-tuning. Phase 1 (Recon),
Phase 6 (Fine-Tuning), and the inference layer are unaffected; the deeper philosophical positions are mostly orthogonal
to whether you fine-tune.

The Marelli fairness argument applies most acutely to LLMs used as substitutes for human study participants or
annotators — not a Linus use case. It does not vanish (any Worker producing scientific text inherits training-data
biases) but it is downstream, not a near-term design pressure.

The paper does not directly address agentic systems, tool use, or multi-agent orchestration. It is the **framework**
layer, not the system layer — current LLM debates (AI scientists like Sakana, Kosmos; agentic research loops like
autoresearch) sit downstream of it.

## Connections

**Group E (LLMs in Science) — direct kin.** The Knuth/claude-cycles paper (`paper-notes/claude-cycles.md`, same wave) is
a near-perfect existence proof of the Schulz collaborator-frame: a working mathematician treats Claude as a colleague
who can chase down a long dependency chain to a proof. Binz et al. lets Dan place that paper inside the broader debate
as an exemplar of one position rather than a free-standing curiosity.

The dual-use biotech paper (`paper-notes/2306.03809v1.md`, same wave) is a sharp instantiation of the Bender position
about misuse and harm at scale. Together with claude-cycles it brackets the live span of the debate: Schulz at one end
(LLM as collaborator on hard math), Bender at the other (LLM as accelerant for biological misuse). Binz et al. is the
framework that organizes both into a single conversation.

The Kosmos paper on autonomous AI scientists is a direct test of the Botvinick/Gershman position. Kosmos is exactly the
"full-spectrum replacement for human scientists" prospect they call "deeply unappealing." Reading Kosmos through Binz et
al. clarifies that the technical question (can it work?) and the normative question (should we want it to?) are
separable, and that Linus is implicitly taking a Botvinick/Gershman-flavored position by being a tool for Dan rather
than an autonomous scientist.

**Engineering conventions — direct hooks.** "Maestro budget discipline" in CLAUDE.md is the operational form of the
Botvinick/Gershman roadmap-agency argument. The "evidence beats intuition" principle and the smoke-test gate align with
Marelli's accountability stance (verify before trusting). The audit log entry in the orchestration layer is exactly
where Marelli-style attribution requirements should be designed in from the start rather than retrofitted.

**Memory architecture (recent ADRs, see DECISIONS.md).** The provenance and write-back rules in the recent memory
architecture work intersect Marelli's attribution requirements directly. If the memory layer records that a synthesis
was generated by a Worker from particular sources, that _is_ the kind of transparency Marelli calls for. Worth
re-reading the Memory Architecture spec with Marelli in hand.

## Open questions for Dan

1. **Should the audit log design be re-examined against Marelli-style attribution requirements?** The CLAUDE.md "audit
   log" line item is currently a one-liner. Marelli implies a richer specification: per-output records of model, prompt,
   retrieved context, tool calls, claimed-vs-retrieved citations, timestamps — designed so the audit log alone could
   justify any output downstream. Promote this to a Phase 2 design document with Marelli's principles cited?
2. **Which of the four perspectives most resonates with you personally, and is that reflected in the documentation?**
   The implicit answer in the current docs reads as a Marelli-flavored hybrid (principles-based,
   accountability-centered) with Botvinick/Gershman commitments on roadmap agency. Accurate? If so, the docs would be
   improved by saying so out loud. If not, what is missing?
3. **Reproducibility from proprietary providers — has the Schulz horror story already happened to your work?** Schulz et
   al. report a paper revision blocked by a silent provider-side model change. If anything similar has been at risk in
   Dan's hosted-Claude work, that's the strongest possible motivation for accelerating the Phase 2 MVP and pinning
   Worker model versions in the audit log from day one.
