# ldp (`Future-House/ldp`)

## 1. Purpose and scope

LDP — "Language Decision Processes" — is FutureHouse's framework for building and **training** language agents under an
explicit POMDP formalism: actions and observations are natural-language messages, the agent emits
`(action, new_state, value_estimate)` from `get_asv()`, and the resulting trajectories feed reinforcement-learning-style
optimizers. It is the policy/learning half of the FutureHouse stack; `aviary` (`fhaviary` on PyPI) is the environment
half. Apache 2.0, pure Python (>=3.11), packaged as `ldp` on PyPI with optional extras for `nn` (PyTorch +
transformers + Dask-distributed), `scg` (the stochastic compute graph), `monitor` (wandb), `server` (FastAPI), and
`visualization` (graphviz/pydot). The Aviary paper (arXiv:2412.21154) is the conceptual anchor. For Linus this group of
repos is mission-aligned: scientific agents under a private orchestrator, trainable on Dan-specific tasks.

## 2. Architecture summary

Five layers under `src/ldp/`. **`agent/`** defines the abstract `Agent[TAgentState]` (generic over state type) with two
methods: `init_state(tools)` and `get_asv(state, obs) -> (action, state, value)`. Concrete agents include `SimpleAgent`
(one LLM call), `ReActAgent` (Yao et al. Thought/Action/Observation loop), `MemoryAgent` (retrieves prior trajectories
from a memory store and prepends them), `TreeofThoughtsAgent` (tree search over LLM-proposed reasoning steps), and
`InteractiveAgent` (human-in-the-loop). Agents auto-register in `_AGENT_REGISTRY` via `__init_subclass__` and instances
auto-discover their internal `Op`s through reflection over `__dict__` — analogous to
`torch.nn.Module.named_parameters()`. **`graph/`** is the Stochastic Compute Graph (SCG): every LLM call, prompt
formatting step, memory lookup, and post-processing fxn is an `Op` whose inputs and outputs are tracked in an async
`compute_graph()` context, enabling serialization, gradient computation (Schulman et al. 2015 SCG), and replay. Modules
in `graph/modules/` (`llm_call`, `react`, `reflect`, `thought`) compose Ops into reusable agent substructures.
**`alg/`** holds the runtime: `rollout.py` (asynchronous environment-agent loops producing `Trajectory` objects of
`Transition`s), `tree_search.py`, `beam_search.py`, `callbacks.py`, and the `optimizer/` subpackage.
**`alg/optimizer/`** defines the `Optimizer` ABC (`aggregate_trajectory` then `update`), with concrete implementations
`APEOpt` (Automatic Prompt Engineering, paired by default with `ReActAgent`), `MemoryOpt` and `PositiveMemoryOpt`
(paired with `MemoryAgent` — append successful trajectories into the memory store), `ChainedOptimizer`, and a
`default_optimizer_factory` that auto-selects per agent class. **`nn/`** is the PyTorch-backed "train your own policy"
path: `nn/agent/simple_local_agent.py` runs a local HF model as the agent LLM, `nn/handlers/` provides Dask-distributed
transformer handling and chunked generation, and `nn/graph/llm_call_op.py` is the differentiable LLM-call Op for
fine-tuning the underlying weights from trajectory rewards. The `packages/lmi/` workspace member is `fhlmi` — a unified
LiteLLM-style provider abstraction (OpenAI, Anthropic, Ollama, etc.) that all `LLMCallOp`s use.

## 3. What's reusable in Linus

The **agent abstraction itself** — `Agent.get_asv()` returning `(action, state, value)` plus a tool list passed at
`init_state` time — is a clean interface for Phase 3's multi-agent fan-out, much cleaner than ad-hoc "an agent is
whatever has a `run()` method." Linus's orchestration layer could adopt the `(state, obs) -> (action, state, value)`
shape as its Worker contract, with `value` defaulted to `0.0` for non-RL workers. `MemoryAgent` plus `MemoryOpt` is
**directly Phase 3 material**: it is a working implementation of "retrieve relevant past trajectories, format them into
the prompt, append successful new ones to the store" — the same pattern Linus needs for KnowledgeBase-grounded agents
that learn from session history. The `Trajectory`/`Transition` data structures and the rollout loop in `alg/rollout.py`
are reusable as Linus's session-recording schema. The `nn/` subpackage is **the link to Phase 6 fine-tuning**: it shows
how to take recorded trajectories, score them, and run a PyTorch update on a local model — though the existing path
assumes CUDA + Dask, so the actual Apple-Silicon training would happen via pmetal or mlx-lm-ft, with LDP supplying only
the trajectory-collection and reward-shaping scaffolding.

Compared to its FutureHouse siblings, ldp's distinctive contribution is the **policy abstraction plus the SCG plus the
trajectory-driven optimizer interface** — `aviary` provides environments and the `Tool`/`Message`/`ToolRequestMessage`
types (ldp imports them and does not redefine), `paper-qa` is a domain agent that _uses_ ldp's agents, and
`BixBench`/`LAB-Bench` are evaluation harnesses expressed _as_ aviary environments. ldp is the only piece in the stack
with first-class training support and the only one that frames agent execution as a learnable POMDP.

## 4. What's inspiration only

The SCG itself is elegant but heavy — every LLM call, prompt-format, and post-processing step becomes a node,
dependencies tracked through async context, and the whole graph serialized for replay. Linus's MVP almost certainly does
not need this; conventional logging of inputs/outputs per tool call gets us 90% of the value. Adopt the SCG only if
Phase 6 actually performs gradient-based agent training, not just supervised fine-tuning on collected trajectories. The
`TreeofThoughtsAgent` and `BeamSearch` runners are interesting prior art for inference-time search but are research
artifacts more than production patterns. The Dask-distributed `nn/handlers/` machinery assumes multi-GPU CUDA clusters
and does not map onto a single M1 Max.

## 5. What's incompatible or out of scope

The `nn` extra **pulls `dask-cuda`, `torch>=2.9`, and a multi-GB transformers stack**, all CUDA-flavored — installable
on macOS but not actually usable for training without translation to MPS/MLX. The pin `torch>=2.9,==2.11.0` is exact and
aggressive; coexistence with Linus's other PyTorch consumers needs care. The default LLM Ops in `lmi` route through
LiteLLM and assume an OpenAI-compatible endpoint — fine for Ollama and pmetal-serve, but the prompt templates in
`agent/react_agent.py` and `graph/modules/react.py` are tuned for GPT-4-class models, mirroring the Cline
`xs`-vs-`generic` split: small local Workers will need their own variants. The optimizer set is narrow (APE, MemoryOpt,
PositiveMemoryOpt) — there is no PPO/DPO/GRPO here; for those, look to pmetal's trainer crates and pair them with ldp
for trajectory collection.

## 6. Recommendation: **Study**

ldp is the right _abstraction_ to inform Linus's agent contract and Phase 3 multi-agent design, but it is not the right
_runtime_ to embed wholesale. Pull the `Agent.get_asv()` interface, the `Trajectory`/`Transition` schema, and the
MemoryOpt pattern into Linus's own module. Defer the SCG and the `nn/` training stack until Phase 6 has a concrete
fine-tuning plan; if at that point we want RL on collected trajectories rather than supervised LoRA, revisit ldp as a
dependency. Keep the clone for Phase 3 design discussions and as a reference for the Aviary-paper formalism.

## 7. Questions for Dan

- **Adopt the `(action, state, value)` contract for Linus Workers?** The shape is clean and gives us value-estimate
  optionality for free. Cost is a small departure from the bare OpenAI chat-completions shape that Cline and openclaw
  send today. Worth standardizing in Phase 2a, or leave it as Phase 3 work?
- **MemoryAgent + MemoryOpt as Phase 3's first multi-agent template.** A KnowledgeBase-backed agent that records its own
  successful trajectories and retrieves them on future invocations is exactly the "learn-from-use" loop you've sketched.
  Is this the right first agent to build, or do you want a simpler ReAct-over-KnowledgeBase as the v1?
- **Pair ldp with aviary, or unify behind a single Linus-native abstraction?** Both are FutureHouse, both are Apache,
  but they are two packages with two install footprints. Phase 2 could vendor the parts we need into `src/linus/agents/`
  and skip the dependency. Acceptable, or worth the dep? _Partially resolved (DEC-0044, see
  [answered-questions.md](../questions/answered-questions.md)): paper-qa adopted as Phase 2c engine without requiring
  ldp or aviary; revisit ldp/aviary only if Phase 6 fine-tunes a domain-specific tool-selection policy._
- **SCG: yes or no for Phase 6.** The SCG buys gradient flow through the agent for end-to-end training. It also buys ~1k
  lines of compute-graph machinery to maintain. Do you anticipate Phase 6 doing gradient-based agent training (in which
  case SCG earns its keep), or is Phase 6 scoped to LoRA-on-trajectories (in which case SCG is pure overhead)?
- **fhlmi vs. direct Ollama/pmetal-serve clients.** fhlmi is yet another LiteLLM wrapper. Linus will already have
  OpenAI-compatible clients for its own backends. Worth taking on fhlmi as the shared LLM-interface layer (and
  inheriting its caching, retries, embedding API), or build a thin Linus-native client and skip it?
