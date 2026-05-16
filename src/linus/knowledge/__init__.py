"""Linus KnowledgeBase adapter package.

Read-only access to the KnowledgeBase paper corpus. The KnowledgeBase itself lives at
``modules/KnowledgeBase/`` as a git submodule and is the corpus-of-record; Linus never
mutates it. This package wraps the submodule's ``data/metadata.db`` SQLite store and
exposes a small, stable Python surface (``KnowledgeBaseAdapter.search_papers`` and
``KnowledgeBaseAdapter.get_paper``) so the Linus orchestration layer can search Dan's
paper corpus without coupling to the upstream KB internals.

Phase 2c v0 scope (this package):
    * SQLite read path against ``modules/KnowledgeBase/data/metadata.db``
    * Keyword search on title/abstract via SQL ``LIKE``
    * Single-paper lookup by SHA256 content hash

Out of scope for this v0 — deferred to later Phase 2c/2f items:
    * SPECTER2 semantic embedding search
    * Dual substrate (SPARQL/RDF + property graph) per DEC-0015
    * paper-qa integration per ``docs/specs/kb/paper-qa-substrate-integration.md``

See ``docs/specs/2026-05-12-linus-implementation-plan.md`` Item 5 for the bootstrap
scope and ROADMAP.md sections "2c" and "2f" for the broader plan.
"""

from linus.knowledge.adapter import (
    KnowledgeBaseAdapter,
    KnowledgeBaseUnavailableError,
    Paper,
)

__all__ = [
    "KnowledgeBaseAdapter",
    "KnowledgeBaseUnavailableError",
    "Paper",
]
