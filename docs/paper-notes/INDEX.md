# Papers Index

Flat lookup table from each per-paper note in [`docs/paper-notes/`](../paper-notes/) to the thematic syntheses that
cover it. Use this to navigate: pick a paper, find the synthesis (or syntheses) that frame it; pick a synthesis, find
the papers it draws on.

This is a navigation aid, not analysis. The narrative argument lives in the syntheses; the per-paper write-up lives in
the paper-note. The two former landscape documents (`paper-landscape.md` and the paper sections of
`total-landscape.md`) used to host both navigation and argument; the navigation half moved here so the landscape docs
can focus on argument.

A small number of papers (KB-foundation papers — embeddings, keyphrase extraction, KG-survey adjuncts, the Horiike
hypercube paper) are not yet absorbed into any thematic synthesis. They show up as **Uncovered** in the table and live
only at the per-paper-note + landscape level for now.

## How to read the table

- **Paper note**: link to the file in `paper-notes/` (filename matches the source PDF basename).
- **Title**: from the note's YAML frontmatter; abbreviated where long.
- **Thematic syntheses**: comma-separated. Each entry links to the corresponding `docs/syntheses/<name>-synthesis.md`.
  An empty cell means "not yet absorbed into a synthesis."

---

| Paper note | Title | Thematic syntheses |
| --- | --- | --- |
| [`0549`](../paper-notes/0549.md) | Automated Superscalar Processor Design by Learning Data Dependencies | _Pending llm-hardware-design_ |
| [`1-s2.0-S0022283626000513-main`](../paper-notes/1-s2.0-S0022283626000513-main.md) | mCSM-metal: A Deep Learning Resource to Predict Effect of Mutations… | [generative-biology](../syntheses/generative-biology-synthesis.md) |
| [`13337-ZhouQ`](../paper-notes/13337-ZhouQ.md) | QiMeng-GEMM: Automatically Generating High-Performance Matrix Multi… | _Pending llm-hardware-design_ |
| [`1910.07467`](../paper-notes/1910.07467.md) | Root Mean Square Layer Normalization | [infra-foundations](../syntheses/infra-foundations-synthesis.md) |
| [`2002.05202`](../paper-notes/2002.05202.md) | GLU Variants Improve Transformer | [infra-foundations](../syntheses/infra-foundations-synthesis.md) |
| [`2003.02320v6`](../paper-notes/2003.02320v6.md) | Knowledge Graphs | [infra-foundations](../syntheses/infra-foundations-synthesis.md) |
| [`2024.12.19.629561v2`](../paper-notes/2024.12.19.629561v2.md) | Multimodal foundation model predicts zero-shot functional perturbat… | [function-annotation-discovery](../syntheses/function-annotation-discovery-synthesis.md) |
| [`2025.03.02.641084v1`](../paper-notes/2025.03.02.641084v1.md) | DeepSeMS: a large language model reveals hidden biosynthetic potent… | [generative-biology](../syntheses/generative-biology-synthesis.md) |
| [`2025.04.19.649272v1`](../paper-notes/2025.04.19.649272v1.md) | ProtHGT: Heterogeneous Graph Transformers for Automated Protein Fun… | [function-annotation-discovery](../syntheses/function-annotation-discovery-synthesis.md) |
| [`2025.05.13.653614v2`](../paper-notes/2025.05.13.653614v2.md) | A generative language model decodes contextual constraints on codon… | [generative-biology](../syntheses/generative-biology-synthesis.md) |
| [`2025.07.20.665723v2`](../paper-notes/2025.07.20.665723v2.md) | A contextualised protein language model reveals the functional synt… | [biological-foundation-models](../syntheses/biological-foundation-models-synthesis.md) |
| [`2025.07.21.665832v2`](../paper-notes/2025.07.21.665832v2.md) | ProteinReasoner: A Multi-Modal Protein Language Model with Chain-of… | [biological-foundation-models](../syntheses/biological-foundation-models-synthesis.md) |
| [`2025.09.12.675911v1`](../paper-notes/2025.09.12.675911v1.md) | Generative design of novel bacteriophages with genome language models | [biological-foundation-models](../syntheses/biological-foundation-models-synthesis.md), [generative-biology](../syntheses/generative-biology-synthesis.md) |
| [`2026.02.09.704801v1`](../paper-notes/2026.02.09.704801v1.md) | A multi-agent platform for assessment and improvement of bioinforma… | [agentic-systems](../syntheses/agentic-systems-synthesis.md) |
| [`2026.03.19.712954v1`](../paper-notes/2026.03.19.712954v1.md) | BioReason-Pro: Advancing Protein Function Prediction with Multimoda… | [function-annotation-discovery](../syntheses/function-annotation-discovery-synthesis.md) |
| [`2026.03.31.715748v1`](../paper-notes/2026.03.31.715748v1.md) | ProtiCelli: Generative ML unlocks the first proteome-wide image of … | [biological-foundation-models](../syntheses/biological-foundation-models-synthesis.md), [generative-biology](../syntheses/generative-biology-synthesis.md) |
| [`2026.04.22.720063v1`](../paper-notes/2026.04.22.720063v1.md) | GenNA: Conditional generation of nucleotide sequences guided by nat… | [generative-biology](../syntheses/generative-biology-synthesis.md) |
| [`2102.05095v4`](../paper-notes/2102.05095v4.md) | Is Space-Time Attention All You Need for Video Understanding? | [memory](../syntheses/memory-synthesis.md) |
| [`2104.09864`](../paper-notes/2104.09864.md) | RoFormer: Enhanced Transformer with Rotary Position Embedding | [infra-foundations](../syntheses/infra-foundations-synthesis.md) |
| [`2203.15556v1`](../paper-notes/2203.15556v1.md) | Training Compute-Optimal Large Language Models | [memory](../syntheses/memory-synthesis.md) |
| [`2205.11916v4`](../paper-notes/2205.11916v4.md) | Large Language Models are Zero-Shot Reasoners | [memory](../syntheses/memory-synthesis.md) |
| [`2208.07262v1`](../paper-notes/2208.07262v1.md) | Retrieval-efficiency trade-off of Unsupervised Keyword Extraction | _Uncovered_ |
| [`2303.12712v5`](../paper-notes/2303.12712v5.md) | Sparks of Artificial General Intelligence: Early experiments with G… | [memory](../syntheses/memory-synthesis.md) |
| [`2304.05332v1`](../paper-notes/2304.05332v1.md) | Emergent autonomous scientific research capabilities of large langu… | [agentic-systems](../syntheses/agentic-systems-synthesis.md) |
| [`2305.13245`](../paper-notes/2305.13245.md) | GQA: Training Generalized Multi-Query Transformer Models from Multi-… | [infra-foundations](../syntheses/infra-foundations-synthesis.md) |
| [`2305.15408v5`](../paper-notes/2305.15408v5.md) | Towards Revealing the Mystery behind Chain of Thought: A Theoretica… | [memory](../syntheses/memory-synthesis.md) |
| [`2306.03809v1`](../paper-notes/2306.03809v1.md) | Can large language models democratize access to dual-use biotechnol… | [generative-biology](../syntheses/generative-biology-synthesis.md), [llms-in-science](../syntheses/llms-in-science-synthesis.md), [safety-alignment-privacy](../syntheses/safety-alignment-privacy-synthesis.md) |
| [`2306.12456v2`](../paper-notes/2306.12456v2.md) | Pushing the Limits of Machine Design: Automated CPU Design with AI | _Pending llm-hardware-design_ |
| [`2310.07923v5`](../paper-notes/2310.07923v5.md) | The Expressive Power of Transformers with Chain of Thought | [memory](../syntheses/memory-synthesis.md) |
| [`2310.11453v1`](../paper-notes/2310.11453v1.md) | BitNet — Scaling 1-bit Transformers for Large Language Models | [infra-foundations](../syntheses/infra-foundations-synthesis.md), [native-low-bit-apple-silicon](../syntheses/native-low-bit-apple-silicon-synthesis.md) |
| [`2311.12351`](../paper-notes/2311.12351.md) | Advancing Transformer Architecture in Long-Context LLMs: A Comprehe… | [infra-foundations](../syntheses/infra-foundations-synthesis.md) |
| [`2312.11514v3`](../paper-notes/2312.11514v3.md) | LLM in a Flash — Efficient Large Language Model Inference with Li… | [infra-foundations](../syntheses/infra-foundations-synthesis.md), [native-low-bit-apple-silicon](../syntheses/native-low-bit-apple-silicon-synthesis.md) |
| [`2401.00422v3`](../paper-notes/2401.00422v3.md) | Interpreting the Curse of Dimensionality from Distance Concentratio… | _Uncovered_ |
| [`2402.03755v1`](../paper-notes/2402.03755v1.md) | QuantAgent: Seeking Holy Grail in Trading by Self-Improving Large L… | [agentic-systems](../syntheses/agentic-systems-synthesis.md) |
| [`2402.17764v1`](../paper-notes/2402.17764v1.md) | The Era of 1-bit LLMs — All Large Language Models are in 1.58 Bits | [native-low-bit-apple-silicon](../syntheses/native-low-bit-apple-silicon-synthesis.md) |
| [`2406.17557v2`](../paper-notes/2406.17557v2.md) | The FineWeb Datasets — Decanting the Web for the Finest Text Data… | _Uncovered_ |
| [`2407.10362v3`](../paper-notes/2407.10362v3.md) | LAB-Bench: Measuring Capabilities of Language Models for Biology Re… | [function-annotation-discovery](../syntheses/function-annotation-discovery-synthesis.md) |
| [`2407.10424v5`](../paper-notes/2407.10424v5.md) | CodeV: Empowering LLMs for Verilog Generation through Multi-Level S… | _Pending llm-hardware-design_ |
| [`2407.21783v3`](../paper-notes/2407.21783v3.md) | The Llama 3 Herd of Models | [infra-foundations](../syntheses/infra-foundations-synthesis.md), [memory](../syntheses/memory-synthesis.md) |
| [`2408.08073v2`](../paper-notes/2408.08073v2.md) | Extracting Sentence Embeddings from Pretrained Transformer Models | _Uncovered_ |
| [`2410.01201v3`](../paper-notes/2410.01201v3.md) | Were RNNs All We Needed? | [memory](../syntheses/memory-synthesis.md) |
| [`2410.11381`](../paper-notes/2410.11381.md) | Survey and Evaluation of Converging Architecture in LLMs Based on F… | [infra-foundations](../syntheses/infra-foundations-synthesis.md) |
| [`2411.04965v1`](../paper-notes/2411.04965v1.md) | BitNet a4.8 — 4-bit Activations for 1-bit LLMs | [native-low-bit-apple-silicon](../syntheses/native-low-bit-apple-silicon-synthesis.md) |
| [`2411.07279v2`](../paper-notes/2411.07279v2.md) | The Surprising Effectiveness of Test-Time Training for Few-Shot Lea… | [memory](../syntheses/memory-synthesis.md) |
| [`2412.03220`](../paper-notes/2412.03220.md) | Survey of different Large Language Model Architectures: Trends, Ben… | [infra-foundations](../syntheses/infra-foundations-synthesis.md) |
| [`2412.04604v2`](../paper-notes/2412.04604v2.md) | ARC Prize 2024: Technical Report | [memory](../syntheses/memory-synthesis.md) |
| [`2412.06769v3`](../paper-notes/2412.06769v3.md) | Training Large Language Models to Reason in a Continuous Latent Space | [infra-foundations](../syntheses/infra-foundations-synthesis.md), [memory](../syntheses/memory-synthesis.md) |
| [`2412.17794v1`](../paper-notes/2412.17794v1.md) | Memory Makes Computation Universal, Remember? | [memory](../syntheses/memory-synthesis.md) |
| [`2412.20138v7`](../paper-notes/2412.20138v7.md) | TradingAgents: Multi-Agents LLM Financial Trading Framework | [agentic-systems](../syntheses/agentic-systems-synthesis.md) |
| [`2502.11880v1`](../paper-notes/2502.11880v1.md) | Bitnet.cpp — Efficient Edge Inference for Ternary LLMs | [native-low-bit-apple-silicon](../syntheses/native-low-bit-apple-silicon-synthesis.md) |
| [`2502.16721v1`](../paper-notes/2502.16721v1.md) | Speed and Conversational Large Language Models (LLMs): Not All Is A… | [function-annotation-discovery](../syntheses/function-annotation-discovery-synthesis.md), [infra-foundations](../syntheses/infra-foundations-synthesis.md), [memory](../syntheses/memory-synthesis.md), [native-low-bit-apple-silicon](../syntheses/native-low-bit-apple-silicon-synthesis.md) |
| [`2503.00096v3`](../paper-notes/2503.00096v3.md) | BixBench: a Comprehensive Benchmark for LLM-based Agents in Computa… | [function-annotation-discovery](../syntheses/function-annotation-discovery-synthesis.md) |
| [`2503.19065v1`](../paper-notes/2503.19065v1.md) | WikiAutoGen: Towards Multi-Modal Wikipedia-Style Article Generation | [agentic-systems](../syntheses/agentic-systems-synthesis.md) |
| [`2504.12285v2`](../paper-notes/2504.12285v2.md) | BitNet b1.58 2B4T Technical Report | [native-low-bit-apple-silicon](../syntheses/native-low-bit-apple-silicon-synthesis.md) |
| [`2504.18415v2`](../paper-notes/2504.18415v2.md) | BitNet v2 — Native 4-bit Activations with Hadamard Transformation… | [native-low-bit-apple-silicon](../syntheses/native-low-bit-apple-silicon-synthesis.md) |
| [`2505.06302v1`](../paper-notes/2505.06302v1.md) | QiMeng-TensorOp: Automatically Generating High-Performance Tensor O… | _Pending llm-hardware-design_ |
| [`2505.23579v2`](../paper-notes/2505.23579v2.md) | BioReason: Incentivizing Multimodal Biological Reasoning within a D… | [function-annotation-discovery](../syntheses/function-annotation-discovery-synthesis.md) |
| [`2505.24183v5`](../paper-notes/2505.24183v5.md) | QiMeng-CodeV-R1: Reasoning-Enhanced Verilog Generation | _Pending llm-hardware-design_ |
| [`2506.02070v3`](../paper-notes/2506.02070v3.md) | An Introduction to Flow Matching and Diffusion Models | [infra-foundations](../syntheses/infra-foundations-synthesis.md) |
| [`2506.05007v1`](../paper-notes/2506.05007v1.md) | QiMeng: Fully Automated Hardware and Software Design for Processor … | _Pending llm-hardware-design_ |
| [`2506.11153v2`](../paper-notes/2506.11153v2.md) | QiMeng-MuPa: Mutual-Supervised Learning for Sequential-to-Parallel … | _Pending llm-hardware-design_ |
| [`2506.12355v1`](../paper-notes/2506.12355v1.md) | QiMeng-Attention: SOTA Attention Operator is generated by SOTA Atte… | _Pending llm-hardware-design_ |
| [`2506.13023v1`](../paper-notes/2506.13023v1.md) | A Practical Guide for Evaluating LLMs and LLM-Reliant Systems | [agentic-systems](../syntheses/agentic-systems-synthesis.md), [function-annotation-discovery](../syntheses/function-annotation-discovery-synthesis.md), [infra-foundations](../syntheses/infra-foundations-synthesis.md) |
| [`2508.09834`](../paper-notes/2508.09834.md) | Speed Always Wins: A Survey on Efficient Architectures for Large La… | [infra-foundations](../syntheses/infra-foundations-synthesis.md) |
| [`2508.15734v1`](../paper-notes/2508.15734v1.md) | Measuring the environmental impact of delivering AI at Google Scale | [infra-foundations](../syntheses/infra-foundations-synthesis.md) |
| [`2509.09995v3`](../paper-notes/2509.09995v3.md) | QuantAgent: Price-Driven Multi-Agent LLMs for High-Frequency Trading | [agentic-systems](../syntheses/agentic-systems-synthesis.md) |
| [`2510.09244v1`](../paper-notes/2510.09244v1.md) | Fundamentals of Building Autonomous LLM Agents | [agentic-systems](../syntheses/agentic-systems-synthesis.md) |
| [`2510.13998v1`](../paper-notes/2510.13998v1.md) | BitNet Distillation | [native-low-bit-apple-silicon](../syntheses/native-low-bit-apple-silicon-synthesis.md) |
| [`2510.19296v4`](../paper-notes/2510.19296v4.md) | QiMeng-SALV: Signal-Aware Learning for Verilog Code Generation | _Pending llm-hardware-design_ |
| [`2511.02824v2`](../paper-notes/2511.02824v2.md) | Kosmos: An AI Scientist for Autonomous Discovery | [agentic-systems](../syntheses/agentic-systems-synthesis.md), [function-annotation-discovery](../syntheses/function-annotation-discovery-synthesis.md) |
| [`2511.09057v3`](../paper-notes/2511.09057v3.md) | PAN: A World Model for General, Interactable, and Long-Horizon Worl… | [infra-foundations](../syntheses/infra-foundations-synthesis.md) |
| [`2511.20099v4`](../paper-notes/2511.20099v4.md) | QiMeng-CRUX: Narrowing the Gap Between Natural Language and Verilog… | _Pending llm-hardware-design_ |
| [`2511.20100v1`](../paper-notes/2511.20100v1.md) | QiMeng-Kernel: Macro-Thinking Micro-Coding Paradigm for LLM-Based H… | _Pending llm-hardware-design_ |
| [`2602.16800v2`](../paper-notes/2602.16800v2.md) | Large-scale online deanonymization with LLMs | [safety-alignment-privacy](../syntheses/safety-alignment-privacy-synthesis.md) |
| [`2602.18308v2`](../paper-notes/2602.18308v2.md) | JPmHC — Dynamical Isometry via Orthogonal Hyper-Connections | _Uncovered_ |
| [`2603.24629v1`](../paper-notes/2603.24629v1.md) | Sketch2Simulation: Automating Flowsheet Generation via Multi-Agent … | [agentic-systems](../syntheses/agentic-systems-synthesis.md) |
| [`2604.05181v1`](../paper-notes/2604.05181v1.md) | General Multimodal Protein Design Enables DNA-Encoding of Chemistry | [generative-biology](../syntheses/generative-biology-synthesis.md) |
| [`2604.27269v1`](../paper-notes/2604.27269v1.md) | OptimusKG: Unifying biomedical knowledge in a modern multimodal graph | [biological-foundation-models](../syntheses/biological-foundation-models-synthesis.md) |
| [`3696443.3708931`](../paper-notes/3696443.3708931.md) | VEGA: Automatically Generating Compiler Backends using a Pre-traine… | _Pending llm-hardware-design_ |
| [`9546_AutoOS_Make_Your_OS_More_`](../paper-notes/9546_AutoOS_Make_Your_OS_More_.md) | AutoOS: Make Your OS More Powerful by Exploiting Large Language Mod… | _Pending llm-hardware-design_ |
| [`bandaru_transformer_design_guide_pt2_modern_architecture`](../paper-notes/bandaru_transformer_design_guide_pt2_modern_architecture.md) | Transformer Design Guide (Part 2: Modern Architecture) | [infra-foundations](../syntheses/infra-foundations-synthesis.md) |
| [`binz-et-al-2025-how-should-the-advancement-of-large-language-models-affect-the-practice-of-science`](../paper-notes/binz-et-al-2025-how-should-the-advancement-of-large-language-models-affect-the-practice-of-science.md) | How should the advancement of large language models affect the prac… | [llms-in-science](../syntheses/llms-in-science-synthesis.md) |
| [`bonsai-1-bit-8b-whitepaper`](../paper-notes/bonsai-1-bit-8b-whitepaper.md) | 1-bit Bonsai 8B: End-to-end 1-bit language model deployment across … | [native-low-bit-apple-silicon](../syntheses/native-low-bit-apple-silicon-synthesis.md) |
| [`bonsai-ternary-8b-whitepaper`](../paper-notes/bonsai-ternary-8b-whitepaper.md) | Ternary Bonsai 8B: Ternary (1.58-bit) language models at 8B, 4B, an… | [native-low-bit-apple-silicon](../syntheses/native-low-bit-apple-silicon-synthesis.md) |
| [`claude-cycles`](../paper-notes/claude-cycles.md) | Claude's Cycles | [llms-in-science](../syntheses/llms-in-science-synthesis.md) |
| [`d41586-026-00974-2`](../paper-notes/d41586-026-00974-2.md) | Self-Driving Labs Power Up | [llms-in-science](../syntheses/llms-in-science-synthesis.md) |
| [`flash_moe`](../paper-notes/flash_moe.md) | Flash-MoE: Streaming a 397B Parameter Mixture-of-Experts Model from… | [infra-foundations](../syntheses/infra-foundations-synthesis.md), [native-low-bit-apple-silicon](../syntheses/native-low-bit-apple-silicon-synthesis.md) |
| [`gkaf836`](../paper-notes/gkaf836.md) | Deciphering enzymatic potential in metagenomic reads through DNA la… | [biological-foundation-models](../syntheses/biological-foundation-models-synthesis.md) |
| [`harvey-et-al-2023-the-dynamics-of-team-learning-harmony-and-rhythm-in-teamwork-arrangements-for-innovation`](../paper-notes/harvey-et-al-2023-the-dynamics-of-team-learning-harmony-and-rhythm-in-teamwork-arrangements-for-innovation.md) | The Dynamics of Team Learning: Harmony and Rhythm in Teamwork Arran… | [humans-teams-performance](../syntheses/humans-teams-performance-synthesis.md) |
| [`Horiike-Orthogonal projections of hypercubes-2025-Physical Review E copy`](../paper-notes/Horiike-Orthogonal projections of hypercubes-2025-Physical Review E copy.md) | Orthogonal Projections of Hypercubes | _Uncovered_ |
| [`jytan_2025_crystallization_of_transformer_architectures`](../paper-notes/jytan_2025_crystallization_of_transformer_architectures.md) | The Crystallization of Transformer Architectures (2017–2025) | [infra-foundations](../syntheses/infra-foundations-synthesis.md) |
| [`Kimi-K2-2507.20534`](../paper-notes/Kimi-K2-2507.20534.md) | Kimi K2: Open Agentic Intelligence (tech report) | [native-low-bit-apple-silicon](../syntheses/native-low-bit-apple-silicon-synthesis.md), [infra-foundations](../syntheses/infra-foundations-synthesis.md), [agentic-systems](../syntheses/agentic-systems-synthesis.md), [skills-and-practices](../syntheses/skills-and-practices-synthesis.md) |
| [`mughal_context_window_management`](../paper-notes/mughal_context_window_management.md) | Why Claude Gets Dumber the Longer Your Session Runs (and the Exact… | [infra-foundations](../syntheses/infra-foundations-synthesis.md), [memory](../syntheses/memory-synthesis.md) |
| [`nihms-2096004`](../paper-notes/nihms-2096004.md) | The brain works at more than 10 bits per second | [humans-teams-performance](../syntheses/humans-teams-performance-synthesis.md) |
| [`NIPS-2017-attention-is-all-you-need-Paper`](../paper-notes/NIPS-2017-attention-is-all-you-need-Paper.md) | Attention Is All You Need | [infra-foundations](../syntheses/infra-foundations-synthesis.md) |
| [`osdi25-dong`](../paper-notes/osdi25-dong.md) | QiMeng-Xpiler: Transcompiling Tensor Programs for Deep Learning Sys… | _Pending llm-hardware-design_ |
| [`PIIS0896627324008080`](../paper-notes/PIIS0896627324008080.md) | The unbearable slowness of being: Why do we live at 10 bits/s? | [humans-teams-performance](../syntheses/humans-teams-performance-synthesis.md) |
| [`raschka_2025_big_llm_architecture_comparison`](../paper-notes/raschka_2025_big_llm_architecture_comparison.md) | The Big LLM Architecture Comparison: From DeepSeek V3 to GLM-5 | [infra-foundations](../syntheses/infra-foundations-synthesis.md) |
| [`rocks-et-al-2026-dual-encoder-contrastive-learning-accelerates-enzyme-discovery`](../paper-notes/rocks-et-al-2026-dual-encoder-contrastive-learning-accelerates-enzyme-discovery.md) | Dual-encoder contrastive learning accelerates enzyme discovery | [function-annotation-discovery](../syntheses/function-annotation-discovery-synthesis.md) |
| [`s41019-017-0055-z`](../paper-notes/s41019-017-0055-z.md) | Keyphrase Extraction Using Knowledge Graphs | _Uncovered_ |
| [`s41467-025-60872-5`](../paper-notes/s41467-025-60872-5.md) | RiNALMo: general-purpose RNA language models can generalize well on… | [biological-foundation-models](../syntheses/biological-foundation-models-synthesis.md) |
| [`s41586-025-08600-3`](../paper-notes/s41586-025-08600-3.md) | World and Human Action Models towards gameplay ideation | [infra-foundations](../syntheses/infra-foundations-synthesis.md) |
| [`s41586-025-10014-0`](../paper-notes/s41586-025-10014-0.md) | Advancing regulatory variant effect prediction with AlphaGenome | [biological-foundation-models](../syntheses/biological-foundation-models-synthesis.md) |
| [`s41586-026-10176-5`](../paper-notes/s41586-026-10176-5.md) | Genome modelling and design across all domains of life with Evo 2 | [biological-foundation-models](../syntheses/biological-foundation-models-synthesis.md) |
| [`s41592-025-02776-2`](../paper-notes/s41592-025-02776-2.md) | Biophysics-based protein language models for protein engineering | [biological-foundation-models](../syntheses/biological-foundation-models-synthesis.md) |
| [`s41592-026-03030-z`](../paper-notes/s41592-026-03030-z.md) | Clustering the protein universe of life using DIAMOND DeepClust | [function-annotation-discovery](../syntheses/function-annotation-discovery-synthesis.md) |
| [`s42256-025-01044-4`](../paper-notes/s42256-025-01044-4.md) | Generalized biological foundation model with unified nucleic acid a… | [biological-foundation-models](../syntheses/biological-foundation-models-synthesis.md) |
| [`science.adt7790`](../paper-notes/science.adt7790.md) | Recent discoveries on the acquisition of the highest levels of huma… | [humans-teams-performance](../syntheses/humans-teams-performance-synthesis.md) |
| [`science.aea6792`](../paper-notes/science.aea6792.md) | Toward universal steering and monitoring of AI models | [safety-alignment-privacy](../syntheses/safety-alignment-privacy-synthesis.md) |
| [`science.aec8514`](../paper-notes/science.aec8514.md) | TranscriptFormer: A generative cell atlas across 1.5 billion years … | [biological-foundation-models](../syntheses/biological-foundation-models-synthesis.md) |
| [`Values_Paper__camera_ready_COLM_`](../paper-notes/Values_Paper__camera_ready_COLM_.md) | Values in the Wild: Discovering and Analyzing Values in Real-World … | [safety-alignment-privacy](../syntheses/safety-alignment-privacy-synthesis.md) |
