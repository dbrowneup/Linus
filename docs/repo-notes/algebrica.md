# algebrica (`antoniolupetti/algebrica`)

## 1. Purpose and scope

Algebrica (antoniolupetti/algebrica; Markdown + LaTeX + SVG + semantic JSON; CC BY-NC 4.0; single-author project by
Antonio Lupetti) is **a free, ad-free, university-level mathematics knowledge base** that publishes its source content
on GitHub in a progressively-released, editable, reusable format. The repository hosts the source files for entries
published on `algebrica.org`: original entries in Markdown + LaTeX, fully editable SVG illustrations (vector structures
and text both modifiable through source code), a **semantic JSON layer containing definitions, properties, lemmas,
theorems, and other formal mathematical structures** associated with the entries, and Markdown-based flowcharts
describing the main logical and procedural steps behind common mathematical processes.

The project's structural pattern is unusual and pedagogically interesting: each entry is built from scratch from
university textbooks, lecture notes, and reference works in mathematics, with deliberate editorial reorganization to
**reduce without distorting** — finding what can be made more direct without losing precision. Where sources differ in
notation or emphasis, they are compared and reconciled, then reorganized into a single coherent flow. The editorial
process is iterative; pages may be revisited as adjacent entries develop. Some pages include GPTZero confidence scores
("92% human") as a transparency signal — the author is honest that these scores are unstable and partially indicative.

The repository structure organizes content by mathematical topic:

```
algebrica/
├── algebraic-structures/
├── complex-numbers/
├── equations/
├── integrals/
├── limits/
├── linear-systems/
├── polynomials/
├── powers-radicals-logarithms/
├── sets-and-numbers/
├── trigonometry/
├── vectors-and-matrices/
├── LICENSE.md (CC BY-NC 4.0)
└── README.md
```

Each topic directory contains the Markdown entries, SVG illustrations, and (per the README's plan) the semantic JSON
layer. An example page is referenced: `integrals/definite-integrals.md`.

## 2. Architecture summary

**Content model:**

- **Markdown + LaTeX entries** — original source files for the entries on `algebrica.org`, progressively released.
- **Fully editable SVG illustrations** — vector structures + text elements both modifiable through source. Designed
  for educational reuse and adaptation under CC BY-NC 4.0.
- **Semantic JSON layer** (planned) — definitions, properties, lemmas, theorems, and other formal mathematical
  structures associated with the entries. Designed to be portable, reusable, openly accessible.
- **Markdown-based flowcharts** — describing main logical and procedural steps behind common mathematical processes
  and problem-solving methods.

**Editorial process:**

- Iterative. Pages may be revisited as adjacent entries develop.
- Sources compared and reconciled when notation differs; reorganized into single coherent flow.
- Reduce without distorting: university sources are often dense; part of the work is finding what can be made more
  direct without losing precision.
- Author is non-native English speaker; uses Grammarly Pro for proofreading; some pages include GPTZero confidence
  scores (acknowledged as unstable / partially indicative).

**License:** CC BY-NC 4.0 — content can be reused for non-commercial purposes with attribution.

**Distribution:** GitHub (source) + algebrica.org (published web pages).

## 3. What's reusable in Linus

**The "semantic JSON layer for formal mathematical structures" is a clean reference for Linus's KB design.** This is
the most interesting structural feature of Algebrica from a Linus perspective. The Linus KnowledgeBase (per
[`docs/specs/kb/`](../specs/kb/)) commits to dual-graph substrates per DEC-0015 and to model-prediction edges as a
first-class edge class per DEC-0048. A semantic JSON layer for **mathematical** content — definitions, properties,
lemmas, theorems, with formal structure — is the **same pattern applied to a different domain**. For Linus's Phase 7+
biology knowledge graph (per [`g9-bio.md`](../syntheses/repo-clusters/g9-bio.md)), the same pattern is portable:
biological definitions, properties, hypotheses, observations, with formal structure expressed in a semantic JSON layer
sitting alongside the Markdown content.

**Editable SVG illustrations as a multi-modal content primitive.** The "fully editable SVG illustrations (vector
structures and text elements both modifiable through source)" pattern is **portable for any Linus KB content that
includes diagrams**. For biology pathway diagrams, network topology illustrations, mechanism schematics — the editable
SVG primitive lets the user modify diagrams through source code rather than through a graphical editor. The Linus KB
spec should consider adopting editable SVG as the diagram primitive for KB content.

**Markdown-based flowcharts.** Algebrica uses Markdown flowcharts to describe logical and procedural steps. The
LLM-readable nature of Markdown flowcharts (versus, e.g., binary or proprietary flowchart formats) makes them
**directly queryable by Linus Workers**. For Linus's Phase 7+ biology Workers that reason about experimental protocols
or computational pipelines, Markdown flowcharts are a portable representation.

**Editorial discipline: "reduce without distorting."** The principle — find what can be made more direct without
losing precision — is the same as CLAUDE.md's writing-style discipline ("Prose over bullet-heavy dumps for anything a
human will read"). The Algebrica editorial process is a worked example. For Linus's documentation discipline,
Algebrica's approach is suggestive: when KB entries are written for human readers, reduction-without-distortion is
the editorial target.

**Iterative-revision discipline.** Algebrica's iterative process — pages revisited as adjacent entries develop —
matches the Linus curation protocol (DEC-0025, quarterly review with archive/removal pathway). The principle that
content evolves with the broader knowledge graph is a portable convention.

**Single-author transparency conventions.** The author's transparency about using Grammarly Pro and GPTZero scores is
unusual for educational content. The pattern — making the author's process visible — is suggestive for Linus's
documentation discipline. The Linus session-summaries already encode this kind of transparency (estimated vs. actual
wall time per CLAUDE.md's "Measure, don't just estimate" convention).

## 4. What's inspiration only

**Single-author content project, not a code project.** Algebrica is content (Markdown + LaTeX + SVG), not software.
Linus's interest is in the **content-organization patterns** (semantic JSON layer, editable SVG, Markdown flowcharts),
not in the specific mathematics content. Vendoring would be inappropriate; integration is at the pattern level.

**CC BY-NC 4.0 license — non-commercial reuse only.** The license restricts commercial use. For Linus's eventual
commercial positioning (per the entrepreneurship synthesis), this is a constraint. Linus can use Algebrica's content
patterns under CC BY-NC 4.0 for non-commercial purposes, but vendoring content into a commercial Linus deployment is
restricted. The patterns are portable; the content is licensed.

**Mathematics-specific content.** Algebrica's content scope is mathematics (algebraic structures, complex numbers,
equations, integrals, limits, linear systems, polynomials, powers/radicals/logarithms, sets/numbers, trigonometry,
vectors/matrices). Linus's content scope is broader — biology, computer science, agentic systems, infrastructure,
safety. The Algebrica content is **not directly relevant** to Linus's KB; the structural patterns are.

**Italian-author, non-native-English-speaker.** The author's English-language proofreading discipline (Grammarly Pro,
GPTZero) is suggestive but Linus's documentation is by a native English speaker. The transparency convention is
portable; the specific tool choices are not.

## 5. What's incompatible or out of scope

**No software; purely content.** Linus is a software project. Algebrica is a content project. The patterns are
portable; integration is at the structural level only.

**Web-published as `algebrica.org`.** The published web side is a separate deployment, not part of the GitHub
repository. For Linus's eventual KB front-end (Phase 5+), the algebrica.org publishing model is potentially relevant —
GitHub source + web-published pages — but Linus's local-first commitment may argue for a local-only KB rather than
publishing pages to a web surface.

**Semantic JSON layer is planned but not yet released.** The README describes the semantic JSON layer as part of the
progressive release. The current state of the JSON layer is unclear from the README. For Linus's pattern adoption,
this is fine — Linus's own semantic-layer design (per DEC-0015 dual-graph substrates, DEC-0048 model-prediction edges)
doesn't need to wait for Algebrica's JSON layer to mature.

**SVG illustrations are not auto-generated.** Algebrica's SVGs are hand-edited. For Linus's Phase 7+ biology KB,
auto-generation of diagrams from underlying data (e.g., pathway diagrams from KEGG XML, network topology illustrations
from interaction data) is more relevant than hand-edited SVGs. The Algebrica pattern (editable SVG) is portable; the
manual-editing workflow is not.

## 6. Recommendation: **Study**

Algebrica is a **content-organization pattern reference** for the Linus KB. The semantic JSON layer alongside Markdown
content + editable SVG illustrations + Markdown-based flowcharts is a coherent, well-thought-out content model that the
Linus KB can adapt to its broader scope (biology, computer science, agentic systems, etc.). The Study recommendation
says: when the Linus KB spec is revisited (per DEC-0015 dual-graph substrates), Algebrica's content model is the
reference for the **per-entry content surface** — what does a single KB entry look like, what files compose it, how
is the semantic layer separated from the prose layer.

The closest Linus-internal pattern: the existing `docs/specs/kb/` (per DEC-0044 paper-qa substrate integration, DEC-0048
model-prediction edges) describes the substrate but not the per-entry content surface. Algebrica fills the per-entry
content-surface gap with a clean worked example.

The CC BY-NC 4.0 license restricts commercial use of the content but not of the structural patterns. Linus should
adopt the patterns; if Linus's eventual commercial positioning includes a KB content surface, the content itself must
either be Linus-authored or licensed for commercial use. Algebrica's content is not vendorable.

## 7. Questions for Dan

1. **Adopt the "semantic JSON layer + Markdown content + editable SVG" per-entry content model in the Linus KB spec.**
   This is a small but meaningful spec decision. Worth surfacing in the KB spec or in a future DEC?

2. **Editable SVG as the diagram primitive for Phase 7+ biology KB.** For pathway diagrams, network topology
   illustrations, mechanism schematics, editable SVG is a portable primitive. Worth committing to in the Phase 7
   biology roadmap?

3. **Markdown-based flowcharts for Worker-queryable protocols.** For Phase 7+ biology Workers reasoning about
   experimental protocols, Markdown flowcharts are LLM-queryable. Worth a Phase 7 spec inclusion?

4. **CC BY-NC 4.0 vs. CC BY 4.0 for Linus-authored KB content.** Linus's eventual commercial positioning suggests
   CC BY 4.0 (allows commercial use with attribution) over CC BY-NC 4.0. Worth a deliberate licensing decision for
   Linus-authored KB content?

5. **Iterative-revision discipline for KB entries.** Algebrica's iterative pattern — entries revisited as adjacent
   entries develop — is suggestive but the operational mechanics differ from Linus's quarterly curation protocol
   (DEC-0025). Worth a curation-protocol update to include "entries-revisit-when-related-entries-update" as a trigger?

6. **GPTZero-style transparency conventions.** The pattern of including LLM-generation-detector scores on
   Linus-authored content is novel but the author's caveats (unstable, partially indicative) are well-founded. Probably
   not worth adopting for Linus, but worth flagging as a curation-protocol consideration.
