# Linus — Decisions Log (ADR Index)

Linus's architectural, product, and process decisions live as per-file ADRs in [`docs/adr/`](docs/adr/). Each decision
is identified by a stable `DEC-NNNN` id and stored as `docs/adr/NNNN-<kebab-slug>.md`. The id and the filename stay in
lockstep — new ADRs take the next free number.

This file used to be the single ADR log. It graduated to the per-file structure once DEC-0027 was logged (the migration
happened on 2026-05-03, per DEC-0026's planning write-back cadence). The 16-ADR memory-pillar batch (DEC-0028 through
DEC-0043) was authored directly under the per-file structure. This file now serves as a brief pointer plus an
at-a-glance index. The canonical format spec, authoring procedure, and full ADR list live in
[`docs/adr/README.md`](docs/adr/README.md).

## Cross-references

- Use `DEC-NNNN` in prose throughout the repo. Link to the file (`docs/adr/NNNN-<slug>.md`) when path precision matters;
  otherwise the bare id is sufficient and stable across renames.
- Amendments to an existing ADR live inside the same file under an `**Amendment YYYY-MM-DD — <short title>.**` heading.
- A fully superseded ADR keeps its file but flips its status line to `superseded by DEC-MMMM`.

## Index

| ID                                                                 | Title                                                                                                                         | Status                                                        |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| [DEC-0001](docs/adr/0001-project-name-and-namesake.md)             | Project name and namesake                                                                                                     | accepted                                                      |
| [DEC-0002](docs/adr/0002-orchestration-backend-as-core-product.md) | Orchestration backend as the core product                                                                                     | accepted                                                      |
| [DEC-0003](docs/adr/0003-knowledgebase-submodule.md)               | KnowledgeBase stays separate, integrated via submodule                                                                        | accepted                                                      |
| [DEC-0004](docs/adr/0004-mambaforge-conda-env.md)                  | Package/env management via mambaforge conda                                                                                   | accepted                                                      |
| [DEC-0005](docs/adr/0005-openai-compatible-protocol.md)            | Maestro/Worker protocol starts OpenAI-compatible, may migrate to MCP                                                          | accepted (MCP portion superseded by DEC-0018)                 |
| [DEC-0006](docs/adr/0006-pmetal-phase1-evaluation.md)              | pmetal evaluated as primary serving + training backend in Phase 1                                                             | proposed — gate decision in Phase 1b                          |
| [DEC-0007](docs/adr/0007-claude-code-terminal-maestro.md)          | Claude Code remains the terminal Maestro; claw-code is reference-only                                                         | accepted (amended 2026-04-23)                                 |
| [DEC-0008](docs/adr/0008-openclaw-frontend-native-app.md)          | openclaw as front-end in Phase 5; native Linus app in Phase 8+                                                                | accepted                                                      |
| [DEC-0009](docs/adr/0009-lm-studio-discovery-only.md)              | LM Studio used for model discovery, not primary runtime                                                                       | accepted                                                      |
| [DEC-0010](docs/adr/0010-engineering-conventions-from-kb.md)       | Engineering conventions inherited from KnowledgeBase insights report                                                          | accepted                                                      |
| [DEC-0011](docs/adr/0011-lightweight-branching-then-gitflow.md)    | Lightweight branching now (Phase 0–2), graduated gitflow at Phase 3+                                                          | accepted                                                      |
| [DEC-0012](docs/adr/0012-pmetal-primary-inference-candidate.md)    | pmetal is the primary Phase 1b inference backend candidate                                                                    | accepted (verdict pending)                                    |
| [DEC-0013](docs/adr/0013-bitnet-2b4t-spike.md)                     | BitNet 2B4T spike adopted as the first concrete Phase 1c experiment                                                           | accepted                                                      |
| [DEC-0014](docs/adr/0014-phase6-finetuning-lane-deferred.md)       | Phase 6 fine-tuning lane decision deferred; Phase 6a commits to FP16-LoRA on genomics regardless                              | accepted                                                      |
| [DEC-0015](docs/adr/0015-kb-dual-graph-substrates.md)              | KnowledgeBase data model: dual approach (RDF + property graph)                                                                | accepted                                                      |
| [DEC-0016](docs/adr/0016-kb-spec-split-convention.md)              | [KB-spec] split convention for KB-impacting specs                                                                             | accepted                                                      |
| [DEC-0017](docs/adr/0017-harness-plurality-roles.md)               | Harness plurality maintained through Phase 5 with explicit role designations                                                  | accepted                                                      |
| [DEC-0018](docs/adr/0018-mcp-extensibility-substrate.md)           | Adopt MCP as the extensibility substrate                                                                                      | accepted (supersedes the Phase 3 revisit portion of DEC-0005) |
| [DEC-0019](docs/adr/0019-kb-ingest-quality-surface.md)             | KB ingest quality gate as a quality surface, not a hard gate                                                                  | accepted                                                      |
| [DEC-0020](docs/adr/0020-orchestration-scope-bounded.md)           | Linus orchestration scope: sandbox + KB + MCP registry + audit; not task-decomposition primitives                             | accepted (refines DEC-0002)                                   |
| [DEC-0021](docs/adr/0021-phase5c-claw-code-local.md)               | Phase 5c formally adopts claw-code-local; 500-line custom Python agent fallback removed                                       | accepted (amends DEC-0007)                                    |
| [DEC-0022](docs/adr/0022-parallel-worker-write-coordination.md)    | Parallel Worker KB write coordination: serialized writes + write-time contradiction surfacing                                 | accepted                                                      |
| [DEC-0023](docs/adr/0023-output-interface-citations-llm-wiki.md)   | Output interface: balanced bullets+prose, citations first-class, opt-in verbose; Linus reframed as personal LLM Wiki at scale | accepted                                                      |
| [DEC-0024](docs/adr/0024-security-posture-supply-chain.md)         | Security posture: hash-pinned linus env + uv-via-conda for disposable experimental envs + pip-audit response protocol         | accepted                                                      |
| [DEC-0025](docs/adr/0025-curation-protocol.md)                     | Curation protocol for `repos/`, `context/`, `docs/`                                                                           | accepted                                                      |
| [DEC-0026](docs/adr/0026-planning-write-back-cadence.md)           | Planning write-back cadence: Maestro/Dan + Claude planning sessions refine core files at session close                        | accepted                                                      |
| [DEC-0027](docs/adr/0027-linus-practice-stance-batch.md)           | Linus practice/stance batch (page cache, public APIs, multi-language, sovereignty, reproducibility, Obj-C)                    | accepted                                                      |
| [DEC-0028](docs/adr/0028-memory-architecture-phase2-pillar.md)     | Memory architecture lifted from Phase 3+ to Phase 2 first-class pillar (M1 + M12)                                             | accepted                                                      |
| [DEC-0029](docs/adr/0029-episodic-memory-substrate.md)             | Cross-session episodic memory substrate (Layer C): SQLite + content hashes + git (M2)                                         | accepted                                                      |
| [DEC-0030](docs/adr/0030-scratchpad-first-class-artifact.md)       | Scratchpad as a first-class durable artifact; o1 anti-pattern forbidden (M3)                                                  | accepted                                                      |
| [DEC-0031](docs/adr/0031-router-primitives-cot-budget-memory-mode.md) | Router primitives: per-call CoT budget and per-call memory mode (M4)                                                       | accepted                                                      |
| [DEC-0032](docs/adr/0032-in-context-window-cap-policy.md)          | In-context window cap policy: 16K Phase 2 floor; episodic store as overflow (M5)                                              | accepted                                                      |
| [DEC-0033](docs/adr/0033-cot-gap-fingerprint-registry-property.md) | Per-Worker CoT-gap fingerprint as a measured registry property (M6)                                                           | accepted                                                      |
| [DEC-0034](docs/adr/0034-worker-size-vs-cot-length-comparison.md)  | Phase 1c empirical comparison: worker-size vs. CoT-length (M7)                                                                | accepted                                                      |
| [DEC-0035](docs/adr/0035-arc-agi-as-memory-diagnostic.md)          | ARC-AGI as a memory diagnostic, not a Linus capability target (M8)                                                            | accepted                                                      |
| [DEC-0036](docs/adr/0036-kv-cache-continuity-architectural-constraint.md) | KV-cache continuity as an architectural constraint for stateful dispatch (M9)                                          | accepted                                                      |
| [DEC-0037](docs/adr/0037-ttt-apple-silicon-viability-spike.md)     | Phase 1c TTT Apple-Silicon viability spike with explicit decision rule (M10)                                                  | accepted                                                      |
| [DEC-0038](docs/adr/0038-mingru-mlx-port-spike.md)                 | Phase 1f minGRU MLX port spike with explicit decision rule (M11)                                                              | accepted                                                      |
| [DEC-0039](docs/adr/0039-episodic-schema-hybrid-leaf-summary.md)   | Episodic schema for multi-step Worker tasks: hybrid leaf + summary (M13)                                                      | accepted                                                      |
| [DEC-0040](docs/adr/0040-faithfulness-audit-deferred.md)           | Faithfulness audit of stored reasoning traces deferred to Phase 3 with trigger condition (M14)                                | accepted                                                      |
| [DEC-0041](docs/adr/0041-mingru-bitnet-phase8-research-direction.md) | minGRU + BitNet cross-product as Phase 8 long-horizon research direction (M15)                                              | accepted                                                      |
| [DEC-0042](docs/adr/0042-coconut-phase6-substrate-experiment.md)   | Coconut as Phase 6 candidate substrate experiment, conditional on Phase 1 portability check (M16)                             | accepted                                                      |
| [DEC-0043](docs/adr/0043-memory-mode-finetuning-targets-phase6.md) | Memory-mode-aware fine-tuning targets in Phase 6a (M17)                                                                       | accepted                                                      |

_New decisions: author the ADR in `docs/adr/` first (see [`docs/adr/README.md`](docs/adr/README.md) for the procedure),
then add a row above._
