# Sketch2Simulation (`OptiMaL-PSE-Lab/Sketch2Simulation`)

## 1. Purpose and scope

Sketch2Simulation converts hand-drawn or scanned process flow diagrams (PFDs) into executable Aspen HYSYS Python scripts
through a nine-stage multi-agent pipeline. Each agent (Descriptor, Validator, Extractor, Basis, Instantiation,
Configuration, Fixer) calls an LLM to progressively refine and transform the image into structured process
specifications, then synthesizes final code for chemical process simulation. This is directly relevant to Linus as a
showcase of vision-to-code agentic decomposition with error recovery loops.

## 2. Architecture summary

The pipeline uses LangGraph to orchestrate agents: image → textual description → intermediate structured representation
→ normalized stream/coupling specs → HYSYS property packages → unit operations → stream connections → merged executable
script. Agent models include Gemini 3 Flash (vision tasks), Qwen 3 VL / Qwen 2.5 Coder (Ollama-compatible), and optional
Qwen 3 Coder 30B for complex configuration. Custom normalizers resolve multi-input merges and stream couplings; a
merge/executor stage handles script assembly and runtime errors with retry logic. Uses RAG (components list, mixture
recipes) via Chroma. Some instruction files are proprietary and not included; the regex-based extraction from
`hysys_template_base.py` markers is fragile.

## 3. What's reusable in Linus

The multi-stage agent orchestration pattern with progressive refinement is directly applicable to Linus Phase 3+
(Knowledge & Parallel Agents). The vision-to-code pathway (image → description → extraction → structured transformation)
is a reusable template for Dan's future domain-specific pipelines (bioinformatics workflow sketches, research pipeline
diagrams). The error-recovery loop (execute, detect failure, route to fixer agent, retry) is worth studying as a general
agentic pattern. The ability to switch between cloud (Gemini) and local models (Ollama) for different tasks is
practical.

## 4. What's inspiration only

The tight coupling to HYSYS (Windows-only COM interface) and chemical process domain is not portable to Linus's
bioinformatics-first focus. The prompt-engineering scaffolding around template markers is brittle and domain-specific.
However, the idea of a "fixer agent" that learns from execution failures is a solid pattern Linus can adapt for
code-generation tasks at Phase 6+.

## 5. What's incompatible or out of scope

Requires a licensed Aspen HYSYS installation with COM access enabled; Windows/Linux only, not macOS. The pipeline is
research-stage and depends on proprietary instruction files not distributed. Vision models are either cloud (Gemini) or
local (Ollama), but deep integration with HYSYS itself is not something Linus needs. The RAG layer (Chroma + fixed
component lists) is adequate but not a pattern Dan would want in KnowledgeBase v1.

## 6. Recommendation: **Study (Phase 3+)**

Not for direct adoption, but the agent orchestration and error-recovery patterns are instructive. If Dan ever builds a
vision-to-code pipeline (e.g., sketch-based bioinformatics workflow generation), this codebase is a useful reference.
The Sketch2Simulation paper (LLMs for design automation) fits Linus's research interest in agentic systems.

## 7. Questions for Dan

1. **Vision-to-code in Linus's domain.** Would a sketch-based bioinformatics workflow generator (genes → proteins →
   pathways as sketches) be a Phase 3/4 Linus feature, or out of scope?
2. **Local vision models.** Qwen VL 8B runs locally via Ollama. Is local vision-capability on the M1 Max a Linus stretch
   goal (Phase 6+), or deferred?
3. **Instruction file brittleness.** The regex-based template marker extraction is fragile. If Linus builds similar
   code-generation pipelines, should it invest in AST-based extraction or structured code IR from the start?
