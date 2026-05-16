"""Demo: search the KnowledgeBase and fetch a paper by SHA256.

Run with::

    python -m linus.knowledge.demo
    python -m linus.knowledge.demo --query "genome assembly" --limit 5
    python -m linus.knowledge.demo --sha256 <hex>

The script exits with status 2 if the KnowledgeBase submodule is not initialized or
its ``metadata.db`` has not been built — same convention as ``pytest`` skip-reasoning
so wrapper scripts can distinguish "missing dependency" from "real error".
"""

from __future__ import annotations

import argparse
import sys
from textwrap import shorten

from linus.knowledge import KnowledgeBaseAdapter, KnowledgeBaseUnavailableError


def _print_paper(paper, abstract_chars: int = 240) -> None:
    print(f"  sha256:   {paper.sha256}")
    print(f"  title:    {paper.title or '<none>'}")
    print(f"  authors:  {paper.authors or '<none>'}")
    print(f"  year:     {paper.year or '<none>'}")
    print(f"  journal:  {paper.journal or '<none>'}")
    print(f"  doi:      {paper.doi or '<none>'}")
    if paper.abstract:
        print(f"  abstract: {shorten(paper.abstract, width=abstract_chars, placeholder='…')}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Linus KnowledgeBase read-only demo")
    parser.add_argument("--query", default="genome assembly", help="Keyword search query")
    parser.add_argument("--limit", type=int, default=3, help="Max search results")
    parser.add_argument("--sha256", default=None, help="Fetch a single paper by SHA256")
    args = parser.parse_args(argv)

    try:
        with KnowledgeBaseAdapter() as kb:
            total = kb.count_papers()
            print(f"KnowledgeBase loaded: {total:,} papers in {kb.db_path}")

            if args.sha256:
                paper = kb.get_paper(args.sha256)
                if paper is None:
                    print(f"\nNo paper found with sha256={args.sha256}")
                    return 1
                print("\nLookup result:")
                _print_paper(paper)
                return 0

            print(f"\nSearch: '{args.query}' (limit={args.limit})")
            hits = kb.search_papers(args.query, limit=args.limit)
            if not hits:
                print("  <no matches>")
                return 0
            for i, paper in enumerate(hits, 1):
                print(f"\n[{i}]")
                _print_paper(paper)
            return 0
    except KnowledgeBaseUnavailableError as exc:
        print(f"KnowledgeBase unavailable:\n{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
