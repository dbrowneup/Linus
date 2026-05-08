# dspy (`stanfordnlp/dspy`)

## 1. Purpose and scope

DSPy (Declarative Self-improving Python) is Stanford's framework for programming LMs rather than prompting them. It
provides a compositional approach to building modular AI systems where you write Python code describing task flow and
use DSPy's compiler to optimize prompts and weights end-to-end via training algorithms. It solves the brittle-prompt
problem by treating LM calls as learnable modules with input/output signatures that can be jointly optimized with few
shots and in-context demonstrations. For Linus, DSPy represents a paradigm for prompt + weight optimization that could
inform Dan's fine-tuning pipeline and provide a structured alternative to ad-hoc prompt engineering.

## 2. Architecture summary

DSPy is organized around four layers: (1) Signatures — input/output type contracts for LM calls (declarative specs
describing what the LM is supposed to do), (2) Primitives — ChainOfThought, Retrieve, MultiChain, etc. (composable
modules that use signatures and coordinate tool calls), (3) Teleprompters — optimizers like BootstrapFewShot,
BayesianSignatureOptimizer, and MIPRO (automatically synthesize in-context demos and refine prompts by executing the
system on a train set and measuring outputs against metrics), and (4) Clients — LM providers (OpenAI, Anthropic, local
via llama.cpp, embeddings, retrievers). The system is built on a constraint-propagation compiler: signatures declare
what data flows through the system, teleprompters observe trace outputs and back-optimize prompts/weights, and modules
compose into larger programs without manual prompt tuning.

## 3. What's reusable in Linus

DSPy Signatures are a clean way to specify tool contracts for Linus agents — instead of manually writing docstrings, use
Signature to declare input fields and their descriptions, output fields, and optional constraints (e.g., "output must be
a list of gene names"). The Retrieve module with ColBERTv2 or other retrievers pairs directly with KnowledgeBase RAG.
The evaluation + metrics composition (defining task-specific evals as Python functions and measuring aggregate
performance) is a pattern Linus can borrow for Dan's task suite. The adapter system (ChatAdapter, XMLAdapter, etc.) for
normalizing different LM response formats is reusable if Linus needs to support multiple local model families.

## 4. What's inspiration only

Teleprompters (the optimizers) are powerful for scaling LM application development but require a substantial labeled
train set — Dan's task suite is large enough to benefit but not large enough to be the primary use case yet. MIPRO and
BayesianSignatureOptimizer are theoretically sound but empirically complex to tune; BootstrapFewShot is the
lowest-friction starting point and has the most production mileage. The DSPy compiler itself is inspirational for
understanding prompt-as-learned-parameter rather than prompt-as-hardcoded-string, but Linus's orchestration doesn't need
to re-implement the constraint-propagation system.

## 5. What's incompatible or out of scope

DSPy is a pipeline optimization framework, not an inference engine. It doesn't touch model serving, weight streaming,
fine-tuning, or local deployment — those are entirely orthogonal. DSPy works with any LM that exposes a generate API, so
integrating with MLX, Ollama, or fine-tuned Linus models is straightforward (just provide a client). The main limitation
is that DSPy assumes stateless LM calls; it's not designed for long-running agents with persistent state or real-time
tool execution loops, though DSPy Primitives compose into larger control structures.

## 6. Recommendation: **Study (Phase 1, 6)**

DSPy is not a drop-in dependency for Phase 2a (the orchestration layer is already specified) but is essential reading
for Phase 6 (fine-tuning). Understanding how signatures and teleprompters work informs Linus's own prompt/weight
optimization strategy. A concrete Phase 6 experiment: take a subset of Dan's task suite, define DSPy Signatures for the
core operations (e.g., "retrieve papers on topic X then summarize Y"), run BootstrapFewShot to generate in-context
demonstrations, then use those demos to train a LoRA'd Qwen2.5. Measure whether DSPy-optimized prompts improve accuracy
over hand-crafted prompts on the full Dan task suite.

## 7. Questions for Dan

1. **DSPy vs. direct fine-tuning.** DSPy optimizes prompts (in-context demos + few-shot examples) while fine-tuning
   optimizes weights. When should Linus prefer one over the other? A hypothesis: DSPy for rapid iteration on large
   models (too expensive to fine-tune), fine-tuning for Linus's own small models (7B–14B).
2. **Integration with KnowledgeBase.** DSPy Retrieve works with in-memory indexes (ColBERTv2, dense passage retrieval);
   KnowledgeBase is a graph + sparse index. Should Linus build a DSPy Retriever adapter for KnowledgeBase, or keep the
   two separate?
3. **Composition with pydantic-ai Agents.** A pydantic-ai Agent + DSPy Signatures is natural (Agent.run calls
   dspy.ChainOfThought) but untested. Is this a target architecture for Phase 6, or do they compete?
