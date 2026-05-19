"""Streamlit page modules. Streamlit auto-discovers ``*.py`` files in this
directory and renders them in the sidebar sorted by filename. Per the
MVP build spec (``docs/specs/2026-05-19-mvp-build.md``), the planned
pages and their numeric prefixes are:

- ``1_chat.py`` — chat UI (task B.1)
- ``2_corpus_stats.py`` — KB-generated PNGs (task B.2)
- ``3_cluster_explorer.py`` — broad → mid → fine drill-down (task B.3)
- ``4_paper_graph.py`` — Sigma.js + 3d-force-graph iframe (task B.4)
- ``5_knowledge_graph.py`` — REBEL/NER graph viewer (task B.5)
- ``6_search.py`` — keyword + semantic search (task B.6)

This shell (task B.0) ships only the package skeleton; pages land
incrementally as B.1–B.6 merge.
"""
