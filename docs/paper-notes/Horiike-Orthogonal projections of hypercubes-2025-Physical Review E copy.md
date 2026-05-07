---
title: Orthogonal Projections of Hypercubes
source: Physical Review E 112, 045304 (2025); doi 10.1103/v291-9hxy
authors: Yoshiaki Horiike, Shin Fujishiro
affiliation: Nagoya University; University of Copenhagen; Kyoto University
date: 2025-10
pdf: ../../context/papers/Horiike-Orthogonal projections of hypercubes-2025-Physical Review E copy.pdf
tags: [hypercubes, pca, visualization, ising-model, energy-landscapes, gene-regulation, biology, geometry]
---

# Orthogonal Projections of Hypercubes

## TL;DR

A pure-physics/applied-math paper (Phys. Rev. E) that uses **PCA as a principled, reproducible orthogonal projection
method** for visualizing high-dimensional binary state spaces — i.e., the vertices of an N-dimensional hypercube where
each vertex is a binary string. Demonstrated on Ising spin systems (including artificial spin-ice with geometric
frustration), with the resulting 2D projections capturing energy-landscape topology and state-transition pathways. **The
biology connection** is the long footnote of cited applications: evolutionary landscapes, gene regulatory networks, gene
expression, protein folding, neural spike dynamics — i.e., Dan's territory. Less directly Linus-relevant than the
BitNet/MoE papers, but a methodological tool for visualizing high-dimensional binary structure that may apply to KB
topic distributions, agent state spaces, or BitNet weight matrices.

## The problem (in plain language)

A "hypercube" in physics-speak is just an N-dimensional generalization of a cube: each of N bits is either 0 or 1,
giving you 2^N corners (vertices), and edges connect corners that differ by exactly one bit-flip. This is the natural
state space for _any_ binary system — N spins in an Ising model, N genes that can be on or off, N neurons firing or
silent, N nucleotides each binary classified, N bits in a BitNet ternary weight (slightly different but related), etc.
Visualizing these state spaces is hard for N > 4: there are 2^N corners and N·2^(N-1) edges, all of which need to be
projected onto 2D paper.

Existing visualization methods are bad in different ways:

- **Manual orthogonal projections** require you to hand-pick a 2D viewing angle. This is impractical and unreproducible
  above 5–6 dimensions.
- **Optimization-based methods** (force-directed layouts, t-SNE, UMAP) are stochastic and non-interpretable: same data,
  different random seed, different picture.

The biology analogue: this is exactly the problem of visualizing a Waddington landscape over many genes — you have a
high-dimensional phase space and you want a 2D map that _means_ something about the dynamics, not an arbitrary squashed
picture.

## What they propose

**PCA on hypercubic vertices** as the projection method, weighted by a probability distribution `p(s)` over states. The
projection direction is the top-2 eigenvectors of the covariance matrix of the (weighted) vertex coordinates. Combined
with **biplots** (arrows showing how each original dimension contributes to the PCs), the resulting 2D plot is:

- **Reproducible**: same input → same output, no random seeds.
- **Interpretable**: each PC has explicit loadings telling you which original dimensions it captures.
- **Analytically tractable**: distributions of projected vertices and error bounds derivable in closed form for several
  distribution classes.

**Findings** about what PCA does to binary data:

1. **Heavily-weighted vertices are pushed to the periphery** of the projection (where variance is maximized). This is
   generic — it happens for any non-uniform `p(s)`.
2. **The leading PC's loading sign-pattern directly identifies which vertices are most-weighted** — read the signs off
   the PC1 loadings to get the dominant binary states.
3. **Vertices near the projection origin lose distance information**: PCA can put two states close in 2D that were
   maximally far in N-D. The paper derives error bounds quantifying this.
4. For bipolar distributions (`p` heavy on `[0...0]` and `[1...1]`), PCA recovers the **Hamming projection** — distances
   in 2D are proportional to Hamming distance from the dominant axis.
5. For energies ↔ probabilities (Boltzmann), the projection naturally captures **energy landscapes** with low-energy
   basins at the periphery and transition states near the origin.

**Application demonstrated**: Ising spin systems on artificial spin-ice geometries (including frustrated lattices). The
PCA projection of the full 2^N state space, when overlaid with hypercubic edges, reveals **dominant state-transition
pathways** — and the time-integrated probability flux of the actual stochastic dynamics matches those pathways.

## Key results

- PCA projections are **reproducible** by construction (just an eigendecomposition).
- For Ising systems with up to ~16 spins (2^16 = 65,536 states), the resulting 2D plots are visually informative —
  energy basins distinct, transition pathways readable.
- **Dominant pathways tend to emerge around the periphery** of the projection (mean-field analysis confirms this).
- **Asymptotic distribution of projected vertices** derived analytically for several `p(s)` classes (Gaussian, bipolar,
  sexapolar).
- **Inner-product error bound** derived: vertices near the origin have higher distance distortion than vertices at the
  periphery.

Scale: visualization technique. Applies to any binary state space; demonstrated on Ising up to N≈16. No training, no
compute beyond eigendecomposition.

## What's reusable in Linus

**Indirect (visualization tool):** If Linus ever needs to visualize a high-dimensional binary structure — for example, a
topic-membership matrix over KB papers (each paper either _is_ or _isn't_ on each of N topics), or a feature-activation
matrix from a BitNet's intermediate states — this is the principled approach. Better than t-SNE for cases where
reproducibility and interpretability matter.

**Indirect (BitNet weights as quasi-binary):** BitNet weights are ternary `{-1, 0, +1}`, not binary. But the zero state
is sparse; in any given group, you mostly have `±1`. The Horiike-Fujishiro framework could in principle be adapted to
visualize the _active_ (non-zero) sign-pattern of BitNet weights as a hypercube, which might give insight into the
structure of what a 1-bit LLM has learned. Speculative — not in the paper — but a thread worth pulling.

**Indirect (biology connection):** The cited applications are _Dan's territory_: gene regulation networks (Boolean
networks of N genes), evolutionary fitness landscapes, neural spike dynamics. Methods for visualizing these have been
ad-hoc for decades; this paper is a clean replacement. If Linus ever does work on a biology problem (KB-driven question
about a regulatory network, say), this paper gives a visualization recipe.

**Methodological lesson:** PCA-as-projection is doing something specific (preserving variance, moving high-mass vertices
outward). Knowing _what_ PCA captures and _what it distorts_ (distance near origin) is a transferable insight whenever
PCA is used in any Linus pipeline.

## What's NOT applicable

- **Not about AI/LLMs**. The paper makes no claims about neural networks; the connection to BitNet is my own
  speculation.
- **Scaling**: 2^16 vertices is the upper end of what's tractable. For BitNet's actual weight matrices (millions of
  parameters), this method doesn't directly apply — you'd have to project a much smaller derived structure.
- **Static snapshots**: the method produces one projection per probability distribution. Animated/temporal data needs
  additional work.
- **Doesn't help with continuous data**: this is binary-state-space-specific. Most ML data is real-valued; for that,
  plain PCA (without the hypercube structure) is the standard tool.

## Connections

- **The other "hypercube" paper Dan mentioned**: [JPmHC](2602.18308v2.md) — different sense of "hypercube" (parallel
  residual streams in a transformer, mixed via an `n×n` orthogonal matrix). Both papers use ideas from high-dimensional
  geometry and the geometry of orthogonal/manifold-constrained operators, but they're not the same hypercube. Worth
  flagging that the word "hypercube" means different things in different communities.
- **Biology overlap**: gene regulatory networks, evolutionary landscapes — relevant to Dan's bioinformatics background;
  might be a useful tool for KnowledgeBase work or future Linus skills targeting biology corpora.
- **Linus phase**: cross-cutting / educational. No direct phase mapping. Useful as a reference if Linus ever produces
  visualizations of binary or boolean structures.

## Open questions for Dan

1. **Why is this paper in your `context/papers/` folder?** Is it for the geometry methodology (visualization tool), the
   biology applications (Ising-as-Boltzmann ↔ gene regulation), or because of the surface-level "hypercube" word overlap
   with JPmHC? Knowing your motivation would refocus the note.
