## DEC-0008 — openclaw as front-end in Phase 5; native Linus app in Phase 8+

**Date:** 2026-04-22
**Status:** accepted

**Context.** openclaw is a polished multi-channel front-end (macOS app, voice wake,
Canvas, iOS/Android nodes) but with a large monorepo (32k+ commits) and its own
opinionated agent architecture that overlaps with Linus's orchestration layer.

**Decision.** In **Phase 5, use openclaw unmodified as a front-end**, configured to
point at Linus's OpenAI-compatible endpoint as its model provider. Accept the
duplication between openclaw's internals and Linus's; we're using it as a UI, not as a
framework to extend. In **Phase 8+, build a native Linus app** (SwiftUI or Tauri) with
fewer features but fully branded and fully under Dan's control.

**Consequence.** Short-term: chat, voice, Canvas, mobile nodes in Phase 5 without
building them. Medium-term: divergence between openclaw's features and Linus's when
their architectures conflict. Long-term: a purpose-built Linus app replaces openclaw
for Dan's primary workflows while openclaw may persist for niche capabilities.
