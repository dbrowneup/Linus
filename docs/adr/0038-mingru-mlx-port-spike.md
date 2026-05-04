## DEC-0038 — minGRU MLX port spike (memory-substrate evaluation)

**Date:** 2026-05-03 **Status:** accepted

**Context.** [Feng et al. "Were RNNs all we needed?" (2410.01201)](../paper-notes/2410.01201v3.md) shows that
minimal-state recurrent architectures (minLSTM, minGRU) parallelizable via prefix-sum can match Mamba and Transformers
on selective copy / RL / Shakespeare-scale language modelling at 13–38% of classical parameter count and 175–1361×
faster training per step at sequence lengths 512–4096 on T4. For Linus's memory pillar, minGRU is a candidate substrate
for the session-memory encoder layer (compresses long Worker turn history into a fixed-size rolling state without
quadratic cost) and a possible foundation for a future Linus-trained sequence model. The viability question is whether
MLX parallel-scan delivers comparable speedups on Apple Silicon and whether perplexity matches vanilla LSTM at the same
parameter count.

**Decision.** **Phase 1f spike** (parallelizable with DEC-0037; both small, DEC-0037 has higher priority because TTT
directly informs DEC-0029).

- Port the few-line minGRU/minLSTM PyTorch reference to MLX using MLX's scan primitives. Use the log-space parallel scan
  from Heinsen 2023 for numerical stability.
- Run the Shakespeare benchmark (character-level, ~1M tokens) on M1 Max.
- Compare against a vanilla MLX LSTM baseline at the same parameter count.

Publish result as `experiments/mingru-mlx-shakespeare/results.md` with raw benchmark output in
`benchmarks/results/mingru_mlx_<YYYY-MM-DD>.json`.

**Decision rule:** if MLX parallel-scan delivers within ~2× of the paper's T4 numbers (allowing for hardware difference)
**and** minGRU matches vanilla LSTM perplexity on the benchmark, minGRU graduates to a Phase 6 candidate substrate for
the memory-pillar session-encoder layer; otherwise filed as Phase 8 research direction (substrate experiments deferred).

Combined with DEC-0037, the outputs of these two spikes determine the Phase 6 substrate menu for memory-pillar
experiments.

**Consequence.** The session-encoder substrate question becomes informed by measurement. If minGRU graduates, Phase 6
can prototype a 100–500M minGRU session encoder against Dan's session transcripts; if it doesn't, the session-prefix
work stays in token-space (per DEC-0031's `memory_mode` loading semantics) and the substrate experimentation moves to
Phase 8. The minGRU + BitNet cross-product (DEC-0041) is also informed by this spike — it cannot become a planned
deliverable without minGRU passing this gate.
