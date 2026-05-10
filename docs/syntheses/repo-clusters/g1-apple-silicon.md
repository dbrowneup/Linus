# Group 1 Synthesis — Apple Silicon Inference & Training

**Date:** 2026-05-08 **Author:** Claude Sonnet 4.6 (Worker, commissioned by Dan Browne) **Trigger:** G1 fan-out
synthesis pass; autoresearch-mlx repo note added as the new Group 1 entry.

---

## What this document is

Group 1 spans eight repos that collectively constitute Linus's Apple Silicon inference and training substrate. Seven of
them — pmetal, mlx-flash, flash-moe, BitNet, Bonsai-demo, ANE, and autoresearch — already shaped the total landscape
through the Phase 1 recon pass. autoresearch-mlx is the marginal addition in this fan-out: a clean MLX port of
Karpathy's autoresearch loop that converts the upstream methodology from "inspiration only, requires NVIDIA GPU" to
"runnable on M1 Max today." The synthesis treats autoresearch-mlx as the completing piece of a picture that was already
mostly drawn. The QiMeng-cpu-v1 repo, formerly grouped here as a methodological reference, has been promoted out of
g1-apple-silicon into its own forthcoming LLM-hardware-design category (see
[`docs/specs/qimeng-category-promotion.md`](../../specs/qimeng-category-promotion.md)) along with the other QiMeng
papers and repos Dan is staging.

This document is not a re-review of each repo. The per-file notes cover that ground. What this document does is name
what the eight repos are collectively pointing at, identify the engineering patterns worth lifting, map how the cluster
connects to the rest of the Linus corpus, and extract the phase-tagged implications that follow from treating these
eight repos as a unit rather than as eight independent decisions.

The total-landscape Crossings most relevant here are Crossing 1 (the BitNet → Apple Silicon → ANE bridge), Crossing 2
(the streaming axis: dense versus sparse versus composite), and Crossing 5 (memory as load-bearing pillar — which has an
inference-backend dimension the cluster sharpens). All three have landed resolutions, and this synthesis is partly an
audit of how well the G1 cluster supports those resolutions.

---

## The unifying thesis

These eight repos are eight different bets on the same underlying question: what does it take to run frontier-class AI
on a single MacBook Pro M1 Max under the 32 GB unified-memory constraint, with no CUDA, no cloud, and no framework
abstraction that sacrifices metal-level control when it matters? The repos disagree on almost everything except the
premise. pmetal bets on a maintained Rust platform. flash-moe bets on bespoke Objective-C with no framework at all.
mlx-flash bets on framework integration with a smart scheduler on top. BitNet and Bonsai-demo bet on weight formats that
make the memory ceiling move. ANE bets on a hardware block Apple does not officially expose. autoresearch and
autoresearch-mlx bet on methodology — the claim that the right search process matters more than any particular
architectural choice.

The thesis that emerges from holding the eight together is this: Apple Silicon is not a constrained-device deployment
target but a research-grade inference and training platform, and the constraint is not hardware capability but software
sophistication. The M1 Max has 24 GPU cores, 16 ANE cores, 400 GB/s memory bandwidth, and fast NVMe with unified
addressing. What it lacks is a mature software ecosystem that uses those components well together. The G1 repos are,
collectively, the partial ecosystem that exists.

For Linus this means the inference and training layer is not a purchasing decision or a one-time configuration step. It
is an ongoing engineering domain where decisions compound, where the right methodology is as important as the right
libraries, and where the gap between "what the hardware can do" and "what the software currently enables" is the space
Linus occupies.

---

## Key findings

**pmetal is the load-bearing center of the cluster.** It is the only repo that covers both the inference path (Phase 2a
OpenAI-compatible serving) and the training path (Phase 6 LoRA, preference optimization, distillation), and it ships
production ANE integration using the same engineering patterns documented in the ANE repo. The repo has expanded
substantially since the initial recon pass: `pmetal-models` now covers 18+ architectures including Qwen3 MoE, Llama 4
Scout/Maverick, DeepSeek V3, NemotronH, and Jamba; hardware auto-detection has been extended to M5's NAX accelerator;
training methods include GRPO and DAPO alongside the original DPO suite. The cluster's other repos either feed into
pmetal as context (ANE, BitNet, flash-moe as methodology reference) or extend it for specific use cases (mlx-flash for

> RAM dense models, Bonsai for 1-bit endpoint coverage during Phase 1b evaluation). The Phase 1b pmetal verdict is the
> single decision that collapses the most open questions.

**autoresearch-mlx makes the research loop executable, not just aspirational.** The upstream autoresearch repo required
an NVIDIA GPU, making it study material with a mental note to adapt later. autoresearch-mlx closes that gap: the
identical keep-or-revert loop, with `program.md` as the skill sheet and branch-per-run as the branch discipline, runs
today on M1 Max via a single `uv sync && uv run`. More importantly, it surfaces a hardware-conditional finding that
matters for Linus's Phase 6 planning: the winner optimizer and architecture on M4 Max is different from what wins on M4
Mac Mini. Transferring training recipes from someone else's results table is not safe. The autoloop has to run on Dan's
actual machine.

**The "trust the OS page cache" principle is a first-class Linus engineering convention, not a flash-moe curiosity.**
The flash-moe experiment that deleted a hand-engineered 9.8 GB Metal LRU expert cache and got a 38% throughput
improvement is the most generalizable finding in the cluster. Any SSD-streaming path, any caching layer, any inference
optimization that builds application-level state that competes with the OS buffer cache will repeat this failure. The
convention belongs in CLAUDE.md's Known Library Quirks section as an explicit anti-pattern: do not build
application-level caches for data that the OS page cache already manages. The MPC-Lite scheduler in mlx-flash succeeds
precisely because it works with the kernel's pacing, not against it.

**Bonsai-demo resolves the 1-bit interim-endpoint question.** The Phase 1b evaluation of pmetal takes time, and the
question of how to put a 1-bit model behind an OpenAI-compatible HTTP endpoint before pmetal-serve is validated has a
clean answer: PrismML's `llama-server` from their llama.cpp fork, which ships with the Bonsai setup script and routes to
the Metal backend. This is a zero-new-code path to a local 1-bit endpoint during Phase 1c benchmark sweeps.

**The ANE is a first-class capability Linus should treat as real, not deferred.** The ANE repo demonstrates training on
an M4's Neural Engine via reverse-engineered private APIs; pmetal hardens those same patterns into a maintained
codebase. The implication for Phase 1b is that "ANE prefill + GPU decode" should be a named benchmark configuration
alongside plain Ollama versus pmetal-GPU, not a deferred Phase 7+ curiosity. The software capability exists; the
question is throughput numbers on M1 Max specifically.

**The cluster has a notable gap: no production-quality combined path for 1-bit plus flash streaming.** BitNet and Bonsai
cover in-RAM 1-bit inference. mlx-flash covers >RAM dense streaming at native precision. No repo combines them. A
Ternary-Bonsai checkpoint large enough to exceed RAM does not yet exist on Apple Silicon. This is the Phase 6d stretch
target (per the Crossing 2 resolution), but it is not available today and should not be planned around for any Phase 1
or Phase 2 deliverable.

**Inference framework convergence corroborates DEC-0036 and signals an MLX-backend trajectory worth tracking (Canteen
Theme C).** An external practitioner survey of the major LLM inference servers — Ollama, SGLang, TensorRT, Triton,
vLLM, and llama.cpp — reports a shared optimization trajectory across the field. As Canteen summarizes it: _"The
KV-cache trajectory is consistent across frameworks: PagedAttention was the breakthrough, RadixAttention added prefix
sharing, HiCache adds hierarchical storage with CPU offloading."_ and _"Quantization is moving from INT4 (common for
local) through FP8 (TensorRT, SGLang, vLLM) to MXFP formats as the next generation." — Canteen, Inference Serving
Landscape, 2026-01-03_
([Canteen, _Inference Serving Landscape_, 2026-01-03](../../../context/notes/canteen_blog_landscape_2026-05.md)). The
first observation is direct corroboration of DEC-0036 (KV-cache continuity as an architectural constraint): every
serious serving framework now treats the KV cache as load-bearing and is iterating on its memory layout rather than
treating it as an implementation detail. Specifically, HiCache's hierarchical KV with CPU offload is the same
conceptual pattern — active state in fast memory, overflow to slow memory, prefetch the working set — that the Phase
6d weight-streaming target generalizes from KV state to model weights. The pattern is identical; the storage tier and
the substrate are different. The second observation, on quantization formats, is forward-looking: INT4 dominates the
local-inference tier today (BitNet/Bonsai 1-bit notwithstanding), FP8 is becoming the default for hosted serving, and
MXFP is the next step. Linus's commitment to native-low-bit (1-bit ternary) inference on Apple Silicon does not
change, but the cluster should track FP8/MXFP support in MLX and pmetal as those formats mature. The Canteen survey
also notes that **MLX backends are appearing as development branches across major frameworks** (vLLM, SGLang, and
adjacent projects). This is a relevant tracking signal for DEC-0049 (pmetal vs PrismML fork decision deferred to Phase
1b): if MLX backends in the major frameworks mature into production-grade Apple Silicon support, that path may
eventually obsolete pmetal as the primary inference candidate. The question is not active for Phase 1b, but it should
be revisited at every Phase 1 close — the relative maturity gap between pmetal and MLX-backed mainline frameworks is
the metric that determines whether DEC-0049 stays settled or reopens.

---

## Patterns and modules worth lifting

The keep-or-revert discipline from autoresearch-mlx is the most directly applicable pattern for Phase 6d. The
implementation shape is specific: one mutable file (`lora_config.py` in the Linus version), one metric (Dan-task-suite
held-out score or PPL on Dan's corpus), a fixed per-experiment time budget scaled to M1 Max reality (30–60 minutes per
LoRA sweep rather than 5 minutes per pretraining step), keep-or-revert by `git`, and `program.md` as the Worker skill
sheet. The branch-per-run convention (`autoresearch/<tag>`) maps directly onto Linus's `agent/<task-id>/<slug>` branch
naming from BRANCHING.md. The monorepo-safety paragraph in `program.md` — "never `git add -A`" — is the paranoid-by-
default guardrail Phase 7c skills should inherit verbatim.

The TurboQuant KV cache design from pmetal is worth understanding for the Phase 2 context-management layer. Its approach
— random rotation plus Lloyd-Max quantization plus QJL residual correction, data-oblivious, 4-6× compression with
near-zero quality loss — addresses the long-context memory pressure on 32 GB that the memory synthesis identifies as
load-bearing. This is not something Linus builds; it is something pmetal provides if the Phase 1b verdict is favorable,
and a reason to weight that verdict accordingly.

The MPC-Lite predictive I/O scheduler from mlx-flash is the pattern to study for any Linus code that schedules SSD reads
during inference. It establishes a clean compute baseline (Cold Start token), predicts the bandwidth demand of layer N+1
while the GPU works on layer N, and uses a token-bucket actuator to pace reads via micro-sleeps. The design achieves
under 5% GPU degradation from streaming overhead. This is not a library Linus imports; it is the reference design for
"how do you stream weights without thrashing the GPU?" and the answer shapes every future >RAM inference decision.

The `pmetal-mcp` crate, which ships 45 MCP tools for Claude Desktop, is resolved as a Phase 2a design question: Linus
owns all in-house tool definitions via fastmcp; `pmetal-mcp` is consumed as an external server, not the registry
foundation (DEC-0018, DEC-0045, ARCHITECTURE.md C.1). The crate remains worth understanding as a reference for what a
well-scoped inference-layer MCP surface looks like, and the pmetal-mhc crate (Manifold-Constrained Hyper-Connections,
linked to the JPmHC paper `2602.18308` in the context folder) is a potential Phase 6 training experiment worth
revisiting when the LoRA pipeline matures.

The IOSurface zero-copy pipeline from the ANE repo — GPU prefill feeding the ANE decode stage with shared memory, no
copy, synchronization via GCD dispatch — is the engineering pattern that makes ANE + GPU hybrid inference fast rather
than just theoretically possible. pmetal's ANE crate uses the same pattern hardened. Linus's own inference code should
not need to touch this directly; understanding it is the context for interpreting Phase 1b benchmark numbers.

---

## Cross-references

Within the G1 cluster, the dependency graph runs: ANE → pmetal (the ANE repo is the proof; pmetal is the production
hardening of the same patterns). flash-moe → mlx-flash (same problem, different philosophy; flash-moe is the bespoke
ultra-optimized implementation, mlx-flash is the framework-integrated practical path; both cite LLM in a Flash as the
theoretical foundation). BitNet → Bonsai-demo (BitNet is the theory and Microsoft's CPU-first implementation; Bonsai is
PrismML's Apple-Silicon-native pretrained model line). autoresearch → autoresearch-mlx (autoresearch is the upstream
methodology; autoresearch-mlx is the executable Apple Silicon port).

The cluster connects to the broader Linus corpus in three directions. First, it connects directly to Crossings 1 and 2
of the total landscape: Crossing 1's three rungs (CPU bitnet.cpp → GPU pmetal kernels → ANE pmetal/ANE-repo patterns)
map one-to-one onto BitNet/Bonsai, pmetal, and ANE respectively. Crossing 2's streaming axis maps onto mlx-flash (dense
streaming), flash-moe (sparse MoE streaming), and the deferred composite (1-bit + streamed).

Second, the cluster connects to the memory synthesis (Crossing 5) through two specific threads. The inference backend
selected by Phase 1b determines what context-window handling is available — TurboQuant KV cache compression on pmetal is
directly relevant to the memory synthesis's recommendation of a 16K in-context cap with episodic-store overflow.
Additionally, the minGRU × BitNet cross-product that the memory synthesis names as a Phase 8 research direction
(recurrent + 1-bit + streamed) sits at the intersection of the G1 cluster (BitNet, Bonsai, mlx-flash) and the memory
pillar (minGRU MLX port spike, DEC-0038). These are not independent research directions.

Third, the autoresearch-mlx loop is the implementation substrate for the experimental methodology that the LLM wiki
synthesis cites in its description of the flash-moe autoresearch thread: give an agent a metric, a goal, and reference
materials, let it run overnight, discard 42% of experiments, surface the winner. The LLM wiki synthesis treated this as
inspiration; autoresearch-mlx makes it operational infrastructure.

---

## Phase-tagged implications

**Phase 1b (pmetal bake-off):** The evaluation plan is already correctly scoped in the pmetal note. One addition from
the cluster-level view: the ANE bench configuration (ANE prefill + GPU decode) should be an explicit metric alongside
plain Ollama versus pmetal-GPU. The ANE repo confirms this configuration is real on M4; the question is M1 Max numbers.
The verdict should land in a new ADR (`DEC-NNNN, slug inference-backend`) as the pmetal note specifies. Everything
downstream in this cluster is gated on that verdict.

**Phase 1c (benchmark sweep):** Four model families should run against Dan task suite: `qwen2.5-coder:7b` and
`mistral:7b-instruct` as the baselines; `bitnet-b1.58-2B-4T` and `llama3-8b-1.58` via Ollama as the 1-bit quality-cost
measurement; Bonsai-8B-mlx-1bit and Ternary-Bonsai-8B-mlx-2bit via the Bonsai setup script as the Apple-Silicon-native
1-bit path. The Bonsai Ternary 8B (released April 2026, 1.75 GB on disk) now represents the strongest available native-
low-bit Worker — its published 75.5 benchmark average (95% of FP16 Qwen3-8B) frames the baseline quality gap; Dan's task
suite will test whether that gap holds on domain-specific work. The question "how much quality does 1.58-bit actually
cost on Dan's task suite?" is answerable in a day and informs every Phase 6 fine-tuning lane decision. The
autoresearch-mlx smoke run (verbatim 5-minute loop, reproduce a few rows of `results.tsv`) should happen alongside Phase
1c to establish a hardware-local baseline before Phase 6d needs it.

**Phase 1d / Phase 1f (memory-related spikes from DEC-0033, DEC-0034, DEC-0037, DEC-0038):** The per-Worker CoT-gap
fingerprint spike (DEC-0033) and worker-size-versus-CoT-length comparison (DEC-0034) run against the same Phase 1c model
sweep, so the G1 benchmark and memory-pillar measurements should be co-scheduled. The minGRU MLX port spike (DEC-0038,
Phase 1f) is a direct output of the memory synthesis's substrate alternative analysis and connects to the G1 cluster
through the "recurrent backends as a first-class inference option" claim.

**Phase 2a (orchestration layer and serving backend):** If Phase 1b is favorable, pmetal-serve slots in as the
OpenAI-compatible endpoint. The pmetal-mcp tool registry question is resolved (DEC-0018, DEC-0045): Linus owns in-house
tool definitions via fastmcp; pmetal-mcp is consumed as an external server. Bonsai's `llama-server` is the fallback
1-bit endpoint during transition pending the Phase 1b verdict (DEC-0049). mlx-flash is not Phase 2a work; it enters at
Phase 5+.

**Phase 5+ (>RAM dense inference):** mlx-flash enters here as the "any fine-tuned model that exceeds RAM runs via
streaming at native precision" path. The Phase 1c native-precision throughput benchmark on M1 Max (what tok/s does
streaming cost on Dan's hardware versus the 16 GB Air demo?) should be done before Phase 5 planning rather than during
it.

**Phase 6d (flash-streaming overnight optimization):** autoresearch-mlx is the substrate. The payload swap is the only
new engineering: replace the pretraining loop with a LoRA fine-tune harness against the Phase 6 base model, replace
`val_bpb` with a Dan-task-suite proxy or held-out PPL on Dan's corpus, inherit `program.md`, the branch convention, and
the keep-or-revert discipline unchanged. The autonomy tier for "NEVER STOP" (autoresearch-mlx's `program.md` posture of
running unsupervised overnight on its own agent branch) needs a corresponding SAFETY.md graduation before Phase 6d can
run fully unattended — that graduation step should be planned in Phase 6's setup rather than discovered mid-run.

**Phase 8 (beyond MacBook):** The minGRU × BitNet × mlx-flash research direction (recurrent + 1-bit + streamed) is the
long-horizon G1 target for inference. No Phase 6 or Phase 7 work is gated on either direction, but together they
describe the direction the cluster collectively points at when its components are combined rather than considered
individually.

---

## Open questions for Dan

_Resolved (DEC-0027, [answered-questions.md](../../questions/answered-questions.md)): "Trust the OS page cache" is now
both a named Engineering Convention and a Known Library Quirk in CLAUDE.md._

**Does the ANE prefill + GPU decode configuration belong in Phase 1b's explicit benchmark matrix?** The ANE repo
confirms it is real on M4 and pmetal ships the implementation. Dan's M1 Max is the hardware the benchmark must run on.
Treating it as an explicit configuration changes Phase 1b planning; deferring it leaves a measurement gap that Phase 2a
will fill in retrospectively instead of prospectively.

**What is the right per-experiment budget for Phase 6d's autoloop on M1 Max?** Karpathy uses 5 minutes on H100. The
autoresearch-mlx README shows 6–7 minutes per experiment on Apple Silicon for pretraining; a LoRA sweep on a 7B model
with a held-out Dan-task-suite eval will be substantially longer. Picking the budget before Phase 6d opens determines
how many experiments an overnight run can complete and what metric is feasible. The tradeoff is: shorter budget with a
fast proxy metric (PPL on Dan's corpus) gives more experiments; longer budget with Dan-task-suite scoring gives higher-
signal experiments. Both are defensible; the choice should be explicit.

**Should the autoresearch-mlx smoke run happen now (Phase 1c co-scheduled) or wait for Phase 6d?** Running it now is
cheap (one evening, `uv sync && uv run`) and produces a hardware-local baseline and a concrete feel for the 6–7
minute/experiment cycle on this chip before Phase 6d planning needs those numbers. Waiting avoids spending time on
infrastructure that isn't Phase 1's critical path. The case for doing it now is that it takes less time to run the
experiment than to estimate it.

_Resolved (DEC-0018, DEC-0045, ARCHITECTURE.md C.1): Linus's tool registry is MCP-shape from Phase 2 onwards, built on
fastmcp. pmetal-mcp is the first **external** MCP server consumed via client adapter — not the registry foundation
itself. The decision is captured in ARCHITECTURE.md's Tool registry section._

---

_This synthesis is a point-in-time document. It should be revisited when Phase 1b's pmetal verdict lands (it resolves
the cluster's central open question), when Phase 6d's autoloop produces its first overnight results (it will update the
autoresearch-mlx payload and budget estimates), and if PrismML releases a Ternary-Bonsai checkpoint larger than 8B on
Apple Silicon (it opens the Crossing 2 composite streaming path earlier than Phase 6d currently assumes)._
