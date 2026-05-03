# Linus — Architecture Decision Records

This directory holds per-file ADRs (Architecture Decision Records). Each significant
architectural, product, or process decision lives in its own file, named
`NNNN-<kebab-slug>.md`, where `NNNN` matches the decision id `DEC-NNNN` used in
cross-references throughout the repo. The id and the filename stay in lockstep.

This structure replaces the single-file `DECISIONS.md` log used through DEC-0027.
`DECISIONS.md` at the repo root is now a brief pointer + index.

The pattern is inspired by Michael Nygard's ADR convention; see
[adr.github.io](https://adr.github.io/) for background.

## Format

```markdown
## DEC-NNNN — <short title>

**Date:** YYYY-MM-DD
**Status:** proposed | accepted | deprecated | superseded by DEC-MMMM

**Context.** Why is this decision being made? What's the forcing function?

**Decision.** What are we doing? Be specific.

**Consequence.** What does this enable? What does it foreclose? What's the reversal cost?
```

Amendments to an existing ADR are appended inside the same file under an
`**Amendment YYYY-MM-DD — <short title>.**` heading, preserving the original
text. If a decision is fully superseded, mark its status `superseded by DEC-MMMM`
and link to the new ADR.

## Authoring a new ADR

1. Pick the next free `DEC-NNNN` id (one greater than the highest existing).
2. Create `docs/adr/NNNN-<kebab-slug>.md` using the template above.
3. Add a one-line entry to the index below and to the table in
   [`../../DECISIONS.md`](../../DECISIONS.md).
4. Reference the decision in prose as `DEC-NNNN`; link to the file when path
   precision matters.

## Index

| ID | Title | Status |
|----|-------|--------|
| [DEC-0001](0001-project-name-and-namesake.md) | Project name and namesake | accepted |
| [DEC-0002](0002-orchestration-backend-as-core-product.md) | Orchestration backend as the core product | accepted |
| [DEC-0003](0003-knowledgebase-submodule.md) | KnowledgeBase stays separate, integrated via submodule | accepted |
| [DEC-0004](0004-mambaforge-conda-env.md) | Package/env management via mambaforge conda | accepted |
| [DEC-0005](0005-openai-compatible-protocol.md) | Maestro/Worker protocol starts OpenAI-compatible, may migrate to MCP | accepted (MCP portion superseded by DEC-0018) |
| [DEC-0006](0006-pmetal-phase1-evaluation.md) | pmetal evaluated as primary serving + training backend in Phase 1 | proposed — gate decision in Phase 1b |
| [DEC-0007](0007-claude-code-terminal-maestro.md) | Claude Code remains the terminal Maestro; claw-code is reference-only | accepted (amended 2026-04-23) |
| [DEC-0008](0008-openclaw-frontend-native-app.md) | openclaw as front-end in Phase 5; native Linus app in Phase 8+ | accepted |
| [DEC-0009](0009-lm-studio-discovery-only.md) | LM Studio used for model discovery, not primary runtime | accepted |
| [DEC-0010](0010-engineering-conventions-from-kb.md) | Engineering conventions inherited from KnowledgeBase insights report | accepted |
| [DEC-0011](0011-lightweight-branching-then-gitflow.md) | Lightweight branching now (Phase 0–2), graduated gitflow at Phase 3+ | accepted |
| [DEC-0012](0012-pmetal-primary-inference-candidate.md) | pmetal is the primary Phase 1b inference backend candidate | accepted (verdict pending) |
| [DEC-0013](0013-bitnet-2b4t-spike.md) | BitNet 2B4T spike adopted as the first concrete Phase 1c experiment | accepted |
| [DEC-0014](0014-phase6-finetuning-lane-deferred.md) | Phase 6 fine-tuning lane decision deferred; Phase 6a commits to FP16-LoRA on genomics regardless | accepted |
| [DEC-0015](0015-kb-dual-graph-substrates.md) | KnowledgeBase data model: dual approach (RDF + property graph) | accepted |
| [DEC-0016](0016-kb-spec-split-convention.md) | [KB-spec] split convention for KB-impacting specs | accepted |
| [DEC-0017](0017-harness-plurality-roles.md) | Harness plurality maintained through Phase 5 with explicit role designations | accepted |
| [DEC-0018](0018-mcp-extensibility-substrate.md) | Adopt MCP as the extensibility substrate | accepted (supersedes the Phase 3 revisit portion of DEC-0005) |
| [DEC-0019](0019-kb-ingest-quality-surface.md) | KB ingest quality gate as a quality surface, not a hard gate | accepted |
| [DEC-0020](0020-orchestration-scope-bounded.md) | Linus orchestration scope: sandbox + KB + MCP registry + audit; not task-decomposition primitives | accepted (refines DEC-0002) |
| [DEC-0021](0021-phase5c-claw-code-local.md) | Phase 5c formally adopts claw-code-local; 500-line custom Python agent fallback removed | accepted (amends DEC-0007) |
| [DEC-0022](0022-parallel-worker-write-coordination.md) | Parallel Worker KB write coordination: serialized writes + write-time contradiction surfacing | accepted |
| [DEC-0023](0023-output-interface-citations-llm-wiki.md) | Output interface: balanced bullets+prose, citations first-class, opt-in verbose; Linus reframed as personal LLM Wiki at scale | accepted |
| [DEC-0024](0024-security-posture-supply-chain.md) | Security posture: hash-pinned linus env + uv-via-conda for disposable experimental envs + pip-audit response protocol | accepted |
| [DEC-0025](0025-curation-protocol.md) | Curation protocol for `repos/`, `context/`, `docs/` | accepted |
| [DEC-0026](0026-planning-write-back-cadence.md) | Planning write-back cadence: Maestro/Dan + Claude planning sessions refine core files at session close | accepted |
| [DEC-0027](0027-linus-practice-stance-batch.md) | Linus practice/stance batch (page cache, public APIs, multi-language, sovereignty, reproducibility, Obj-C) | accepted |

*New ADRs append to this index with monotonically increasing `DEC-NNNN` ids.*
