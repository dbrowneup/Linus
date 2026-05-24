"""Seed the QFinCorpus with arXiv papers via Linus's papers.ingest_arxiv tool.

Reads ``scripts/qfin_arxiv_seed.txt``, ingests each listed paper into
``modules/QFinCorpus/papers/`` via the C.1 tool, and prints a summary.

Idempotent: papers already cached (i.e. ``<id>.json`` exists) are
skipped without re-downloading.

Usage::

    conda activate linus
    python scripts/seed_qfin_corpus.py                     # default seed list
    python scripts/seed_qfin_corpus.py path/to/other.txt   # custom list

The script sets ``LINUS_PAPERS_DIR=modules/QFinCorpus/papers`` before
importing the tool, so the cache root is scoped to this corpus regardless
of where you usually point the env var.

Exits 0 on full success, 1 if any paper failed (errors printed). Either
way the successful papers ARE cached; re-run after fixing the bad ids
to top up.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Resolve repo root from this file's location (scripts/ is at the repo root).
_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_SEED_LIST = _REPO_ROOT / "scripts" / "qfin_arxiv_seed.txt"
_DEFAULT_OUTPUT_DIR = _REPO_ROOT / "modules" / "QFinCorpus" / "papers"


def _read_seed_list(path: Path) -> list[str]:
    """Return the non-comment, non-empty lines from the seed file."""
    if not path.exists():
        raise SystemExit(f"Seed list not found: {path}")
    ids: list[str] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        ids.append(line)
    return ids


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "seed_list",
        nargs="?",
        default=str(_DEFAULT_SEED_LIST),
        help="Path to seed list (one arxiv id per line). Defaults to scripts/qfin_arxiv_seed.txt.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(_DEFAULT_OUTPUT_DIR),
        help="Where ingested PDFs + passports land. Default: modules/QFinCorpus/papers/.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Cap the number of ingests this run (useful for smoke-testing).",
    )
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    os.environ["LINUS_PAPERS_DIR"] = str(output_dir)

    # Import after setting the env var so the tool reads the right path.
    from linus.tools.arxiv_ingest import ingest_arxiv

    ids = _read_seed_list(Path(args.seed_list))
    if args.limit is not None:
        ids = ids[: args.limit]
    if not ids:
        print("Seed list is empty (only comments). Nothing to do.")
        return 0

    print(f"Seeding QFinCorpus from {len(ids)} arxiv ids → {output_dir}\n")

    ok_count = 0
    skipped_count = 0
    fail_count = 0
    for i, arxiv_id in enumerate(ids, start=1):
        prefix = f"[{i:>3}/{len(ids)}]"
        passport_path = output_dir / f"{arxiv_id}.json"
        was_cached = passport_path.exists()

        result = ingest_arxiv(arxiv_id)

        if "error" in result:
            fail_count += 1
            print(f"{prefix} ✗ {arxiv_id}: {result['error']} {result.get('detail', '')}".rstrip())
            continue

        title = (result.get("title") or "—")[:70]
        year = result.get("year") or "n.d."
        warning = result.get("warning")
        marker = "·" if was_cached else "✓"
        msg = f"{prefix} {marker} {arxiv_id}  {year}  {title}"
        if warning:
            msg += f"  ({warning})"
        print(msg)

        if was_cached:
            skipped_count += 1
        else:
            ok_count += 1

    print()
    print(f"Done. ingested={ok_count}  cached={skipped_count}  failed={fail_count}  total={len(ids)}")
    print()
    print("Next step: run the KB pipeline against this corpus.")
    print("See modules/QFinCorpus/README.md for the two-option playbook.")
    print()
    print(f"To browse: export LINUS_KB_OUTPUTS_DIR={output_dir.parent / 'data' / 'outputs'}")
    print("           streamlit run src/linus/app/main.py")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
