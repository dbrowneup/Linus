# Rubric — Paper Summarization

## Task

Given the extracted text of `context/papers/2310.08560.pdf` (MemGPT: Towards LLMs as Operating Systems), produce
exactly three numbered key findings as a Markdown numbered list.

## What counts as success (full credit)

All three of the following must hold:

1. **Format compliance.** Output is a numbered list with three items, no preamble or trailing prose. Items
   start with `1.`, `2.`, `3.` (or close equivalents like `1)`).
2. **Faithfulness.** Each finding is grounded in the paper — no claims the paper doesn't make. A claim is grounded
   if it appears in the abstract, introduction, results, or discussion of MemGPT.
3. **Substance.** Each finding is a concrete claim, not a generic platitude. Concrete = names a mechanism (e.g.,
   "hierarchical virtual memory with paging between main and external context"), a result (e.g., "beats fixed-
   context baselines on document QA"), or a capability (e.g., "supports unbounded conversation history via
   recall-managed swapping").

## Partial credit

- 2/3 findings concrete and grounded, one filler or unsupported → **partial**.
- Right substance but malformed (prose paragraph, four items, missing numbers) → **partial**.
- Grounded but vague (e.g., "MemGPT improves LLM performance") → **partial**.

## Failure

- Hallucinated findings (claims the paper does not make).
- Refusal, error, or empty output.
- Off-task output (e.g., summary of a different paper, generic LLM advice).
- Format catastrophically broken to the point that a reader can't identify three claims.

## Reference findings (for the grader; not shown to the Worker)

The MemGPT paper's load-bearing claims, any of which qualify as a grounded finding:

- **Hierarchical memory tiers** — MemGPT manages a main context (in-window) plus external context (out-of-window)
  using OS-paging-inspired primitives, letting fixed-context LLMs handle effectively unbounded input.
- **Self-directed memory management via function calls** — the LLM itself issues paging/recall operations through a
  tool interface, rather than relying on external retrieval orchestration.
- **Document analysis and multi-session chat benchmarks** — MemGPT outperforms fixed-context baselines on long-
  document QA and multi-session conversational consistency tasks where context exceeds the window.
- **Interrupt + heartbeat scheduling** — the system uses event-driven control (user-message and system-event
  interrupts, optional heartbeat events) to drive memory management proactively rather than reactively.

A response that surfaces two or three of these (or paraphrases) is full-credit grounded.
