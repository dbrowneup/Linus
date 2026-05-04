---
title: "Claude's Cycles"
source: Stanford CS preprint, https://cs.stanford.edu/~knuth/papers/claude-cycles.pdf
authors: Donald E. Knuth
affiliation: Stanford Computer Science Department
date: 2026-04-14
pdf: ../../context/papers/claude-cycles.pdf
tags:
  [
    llm-in-science,
    mathematical-reasoning,
    case-study,
    frontier-model,
    chain-of-thought,
    maestro-worker,
    hosted-claude,
    group-e,
  ]
---

# Claude's Cycles

## TL;DR

This is not a research paper. It is a five-page first-person account by Donald Knuth — yes, that Knuth — of how **Claude
Opus 4.6** solved an open combinatorial problem he had posed in a forthcoming volume of _The Art of Computer
Programming_. The problem: decompose the arcs of a particular digraph on m^3 vertices into three directed Hamiltonian
cycles, for all m > 2. Knuth had it for m = 3; his collaborator Filip Stappers had empirical solutions through m = 16;
nobody had a general construction. Stappers handed the problem to Claude with a single piece of process discipline
("after EVERY exploreXX.py run, IMMEDIATELY update plan.md"), and roughly one hour and 31 explorations later, Claude
produced a working construction for all odd m, expressed as a tiny C program. Knuth then wrote a hand proof. A Lean
formalization (Kim Morrison) followed within days; the even-m case was subsequently cracked by other people working with
GPT-5.4 Pro and Claude 4.6 Sonnet. Knuth ends: "We are living in very interesting times indeed." For Linus, this paper
is a **calibration data point on the Maestro ceiling** — what hosted frontier models can do that local Workers cannot,
told by an unimpeachable witness.

## The problem (in plain language)

Take m^3 vertices, label them ijk for 0 <= i, j, k < m. From each vertex draw three outgoing arcs: one bumps i, one
bumps j, one bumps k (each modulo m). That gives you a 3-regular directed graph. The question: can you partition all
3\*m^3 arcs into exactly three directed Hamiltonian cycles, each of length m^3? Think of it as three colorings of the
arcs such that each color class forms a single cycle that visits every vertex exactly once. Knuth had a
hand-construction for m = 3. Filip Stappers had numerically found solutions for m up through 16, which made it morally
certain that solutions exist in general — but a general construction (a formula or algorithm parameterized by m) had not
been found. The case m = 2 is genuinely impossible (proven in 1982).

This is a real open problem in combinatorics. Not a competition puzzle, not a known benchmark. It is the kind of
question that occupies a working mathematician for "several weeks" of background thought.

## What they propose

There is no methodology to propose — the paper is a narrative. But the structure of Claude's exploration, as Knuth
reconstructs it from the plan.md log, is itself the substantive content:

1. **Reformulation.** Claude immediately recasts the problem: "Need sigma: Z_m^3 -> S_3, assigning a permutation of {0,
   1, 2} at each vertex; cycle c at vertex v goes in direction sigma(v)[c]." This is the right mathematical handle.
2. **Try the easy thing first.** Test whether sigma can be cyclic and a function of a linear or quadratic form on (i, j,
   k). It can't.
3. **Brute force as a baseline.** Depth-first search over sigma assignments for m = 3. Search space ~6^27, too slow
   without pruning.
4. **Symbolic structure.** Recognize the graph as a Cayley digraph on Z_m^2 (in the 2D reduction), and discover what
   Claude calls a "serpentine pattern" — which Knuth notes is the classical modular m-ary Gray code from page 299 of
   TAOCP volume 4A.
5. **Iterate.** Twenty-plus more explorations: hyperplane analyses, fiber decompositions (the quotient map (i,j,k) ->
   i+j+k mod m), simulated annealing at scale, near-misses where 3(m-1) of m^3 vertices have conflicts, dead-end
   approaches proven impossible, and the conclusion at exploration 25: "SA can find solutions but cannot give a general
   construction. Need pure math."
6. **Pivot back to math.** Exploration 30 looks at a single SA solution from exploration 20 and notices a structural
   fact: at fiber 0 the choice depends only on j; at fibers 1 and 2 only on i. That observation collapses to the
   construction, expressed in exploration 31 as a Python program that decomposes correctly for m = 3, 5, 7, 9, 11.

The construction itself, in Knuth's C-form translation, is small enough to quote:

```c
if (s == 0)         d = (j == m-1 ? "012" : "210");
else if (s == m-1)  d = (i == 0   ? "210" : "120");
else                d = (i == m-1 ? "201" : "102");
```

where `s = (i+j+k) % m` and `d[c]` selects which coordinate to bump for cycle c. That's it. Roughly twelve characters of
policy table plus the fiber-index dispatch.

## Key results

- **A general construction for odd m.** Filip Stappers verified the program for all odd m between 3 and 101; Knuth then
  proved the first cycle Hamiltonian by hand and indicates analogous proofs for cycles 2 and 3 (sketched in the
  appendix). Kim Morrison formalized the proof in Lean within days. So the result is bona fide mathematics, not just
  empirical agreement.
- **The construction is one of many.** Knuth's after-the-fact analysis: there are 11502 Hamiltonian cycles for m = 3, of
  which 996 generalize to all odd m via the "Claude-like" template. Three-cycle decompositions built from generalizable
  cycles number 760. Claude found one of them. Knuth examined several others and found none "actually nicer."
- **Even m followed soon after.** A postscript records that other people, working with GPT-5.4 Pro, Claude 4.6 Sonnet,
  and OR-Tools' CP-SAT solver, produced constructions and proofs for even m as well. One result is a 14-page paper by
  GPT-5.4 Pro that Ho Boon Suan submitted essentially unedited.
- **Process notes from Stappers.** The session was not smooth. Claude needed restarts after random errors, lost prior
  search results, and required repeated reminders to keep documenting in plan.md. Claude eventually got stuck on the
  even case and "was not even able to write and run explore programs correctly anymore, very weird." So this is not a
  story of frictionless brilliance; it is a story of a competent but flaky collaborator under careful human stewardship.

## What's reusable in Linus

**Maestro budget framing (immediate).** This is a clean, externally validated example of the kind of work that justifies
hosted-Claude tokens. A Maestro session that solves an open combinatorial problem in an hour is not extravagant; it is
exactly the role allocation Linus' architecture already presumes. Use this paper as a touchstone when triaging tasks: if
a task is "DFS over a small space, then SA, then human-style mathematical pivot," it belongs with Maestro, not a 7B
Worker.

**Process pattern: forced documentation.** The single instruction Stappers gave Claude — "after EVERY exploreXX.py run,
IMMEDIATELY update plan.md before doing anything else" — turned an unstructured exploration into a recoverable,
summarizable trajectory. This is directly portable into Linus' Maestro/Worker protocol. For long-horizon Worker tasks,
mandate a per-iteration log update as a hard step, not a soft suggestion. The KnowledgeBase repo's existing convention
of writing to a status doc each session is the right idea; Claude-cycles is independent confirmation that it scales to
non-trivial agentic loops.

**Memory pillar evidence.** The 31-exploration log is an empirical case study of polynomial-step chain-of-thought in
action — exactly the regime that the CoT complexity-theory papers ([2305.15408v5](2305.15408v5.md),
[2310.07923v5](2310.07923v5.md)) argue is required for problems beyond TC^0, and that Kojima
([2205.11916v4](2205.11916v4.md)) anchored empirically on smaller tasks. Knuth's piece is a single high-quality data
point at the upper end of that spectrum: a frontier model traversing a deep search with mid-trajectory pivots that
recombine prior results. For the memory architecture spec, this is concrete evidence that the
**persistent-log-of-exploration** is itself the unit of progress, not the final answer alone. Linus' memory layer should
treat exploration trajectories as first-class artifacts.

**Benchmark candidate.** A natural Linus deliverable: take a smaller combinatorial problem in the same family
(Hamiltonian decomposition on a small Cayley digraph, or a fixed-m instance), specify it in the Knuth/Stappers protocol
form, and use it as a Maestro-class evaluation in `benchmarks/dan_tasks/`. Run it against hosted Claude (calibration),
then against the strongest local Worker (gap measurement). The gap is the per-token Maestro premium; the trajectory
length is the memory-architecture stress test.

## What's NOT applicable

**Not a recipe for Workers.** Nothing in this paper transfers to local 7B–14B inference. Claude Opus 4.6 is the frontier
model of its release window; the closest Linus Workers (Qwen2.5-Coder-7B, Mistral-7B, future LoRA-tuned 8B) will not
solve open combinatorics on first attempt regardless of prompting. Treat this paper as a description of the Maestro
ceiling, not as a target to clone.

**Not a methodology paper.** No metrics, no ablations, no controlled comparison. One problem, one model, one
collaborator, one hour. Generalization claims would be inappropriate.

**Not unaided AI.** Stappers wrote the prompt, enforced documentation discipline, restarted sessions, recovered from
errors, and validated the final program against m = 3 to 101 with his own code. The paper is honest about this; any
"Claude solved Knuth's problem" headline would understate the human role. The right framing is **a competent
mathematician using Claude as a research tool that genuinely contributed novel structural insight** — closer to a
Wolfram Alpha session that pivots than to autonomous discovery.

**Not the only path.** Knuth notes 760 valid generalizable decompositions; Claude found one. The "Exocija" alternative
(sent later, found jointly via GPT 5.4 and Claude 4.6 Sonnet) uses only s and j and the identity permutation almost
everywhere. So the result was discoverable by other contemporaneous models with different prompting. The case study is
illustrative, not a unique-capability demonstration.

## Connections

**Group E triangulation.** Within Group E (LLMs in Science), this paper is the _optimistic data point_: a rigorous
mathematician taking AI-produced mathematics seriously enough to write it up and call for revision of his prior
opinions. The Binz PNAS Perspective is the structured debate framing the question methodologically; the LLMs/dual-use
biotech paper is the cautionary counterweight on what the same capabilities enable in the wrong hands. Knuth's piece
anchors the upper-right quadrant: high-skill human + frontier model + open problem + verifiable result. Linus' position
on "what role should LLMs play in science" should be calibrated against all three, not any one.

**Bracketing Kosmos.** [Kosmos (2511.02824v2)](2511.02824v2.md) is a 12-hour multi-agent autonomous-scientist system;
Knuth's case is a one-hour single-conversation human-in-the-loop session. Together they bracket the design space for
**LLM-driven discovery**: at one end, multi-agent persistent infrastructure with explicit hypothesis management; at the
other, a single chat thread with one disciplined process rule (update plan.md). Both produced novel correct results in
their respective domains. Linus' orchestration layer should support both modes — sustained multi-agent for autonomous
runs, light single-thread with mandated logging for Maestro sessions — and the design should not assume one is strictly
superior.

**Memory pillar: trajectory as artifact.** The plan.md document Stappers enforced is exactly the artifact the Memory
Architecture spec needs to model. Not transcripts (too noisy), not summaries (too lossy), but **structured per-iteration
progress notes maintained by the agent itself**. This connects to the CoT papers above and to the Memory Synthesis
document. A concrete proposal: Linus' Worker harness should write a `plan.md`-style log per task by default, and Maestro
reviews should consume the log, not the raw transcript.

**Reading-list nucleus.** This paper plus references [4]–[12] (Stappers' even-case program, Morrison's Lean
formalization, Aquino-Michaels' multi-agent paper, GPT-5.4 Pro's auto-generated 14-page proof) are a small reading-list
nucleus on **how working mathematicians actually integrate LLMs into research practice**. Worth tracking as a reference
set.

## Open questions for Dan

1. **Reading list?** Should there be a "famous mathematicians and scientists using Claude" reference shelf in
   `docs/repo-notes/` (Knuth, Tao's blog posts, the residue paper [10] above, and similar)? It is a small corpus that
   calibrates expectations and provides discussion fodder; not load-bearing for any single phase, but useful when
   arguing about Maestro/Worker boundaries with future collaborators.
2. **Maestro-class benchmark?** Should a small open combinatorial problem (smaller than Knuth's, but in the same family
   — Hamiltonian decomposition on a fixed digraph, or a Cayley-graph cycle problem) live in `benchmarks/dan_tasks/` as a
   _Maestro-class_ eval, explicitly distinguished from Worker-class evals? This would formalize the role distinction in
   the benchmark suite itself rather than only in protocol docs.
3. **Worker-tractable analog?** Is there a sub-problem here a 7B Worker could plausibly handle — e.g., DFS the m = 3
   case, generate the Cayley-graph reformulation given a hint, write the verification harness? Decomposing a
   Maestro-class problem into Worker-tractable sub-tasks is itself an exercise; Knuth's exploration log is unusually
   well-suited as a source because the steps are already labeled.
4. **plan.md as protocol mandate?** The forced-documentation pattern Stappers used — "update before doing anything else,
   no exceptions" — should that become a default in the Maestro/Worker protocol document, with a settings.json hook that
   enforces it for long-running Worker sessions? The cost is near zero; the upside is recoverability when Workers fail
   mid-task (which they will).
5. **Trajectory store in the memory pillar?** Should the memory architecture have an explicit "exploration trajectory"
   object type, separate from chat history and KnowledgeBase entries, designed to hold plan.md-style logs as queryable
   artifacts? This would let future Maestro sessions reuse prior exploration structure ("we tried fiber decomposition
   for problem X, here's where it stalled") instead of restarting cold.
