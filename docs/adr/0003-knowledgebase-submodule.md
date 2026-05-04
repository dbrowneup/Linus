## DEC-0003 — KnowledgeBase stays separate, integrated via submodule

**Date:** 2026-04-22 **Status:** accepted

**Context.** Dan's papers_analysis project (now KnowledgeBase) overlaps heavily with Linus's knowledge layer. Options
were: (a) fully subsume KnowledgeBase into Linus, (b) keep it separate and consume as a submodule, (c) keep it separate
and consume as a published package.

**Decision.** KnowledgeBase is tracked as a **git submodule at `modules/KnowledgeBase/`**. Linus imports it via an
adapter at `src/linus/knowledge/`. KnowledgeBase continues as an independent project; Linus pins a SHA and updates it
deliberately.

**Consequence.** KnowledgeBase can be developed and released independently. Linus doesn't fork it. Updating the
submodule is an explicit commit. Changes to KnowledgeBase functionality happen in the KB repo, with its own review, not
via Linus edits.
