## DEC-0009 — LM Studio used for model discovery, not primary runtime

**Date:** 2026-04-22
**Status:** accepted

**Context.** Dan has LM Studio installed with local models. LM Studio provides model
discovery/download UI, casual chat, and a local OpenAI-compatible server.

**Decision.** **LM Studio is a model discovery and exploration tool**, not the primary
Linus runtime. Ollama (and pmetal, if Phase 1 adopts it) serves Linus's production
path because they are scriptable and integrate into pipelines. LM Studio is used
ad-hoc for exploring new models and casual chats with models not yet wired into
Linus.

**Consequence.** Two model stores coexist (LM Studio's and Ollama's) with some
duplication. This is acceptable given their different roles. No need to unify them.
