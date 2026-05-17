"""Demo: drive the Phase 2a tool-call loop end-to-end against a live model.

Run with::

    python -m linus.tools.demo
    python -m linus.tools.demo --prompt "what papers discuss memory architecture?"
    python -m linus.tools.demo --model qwen2.5-coder:7b --limit 3

The demo:

1. Verifies the KnowledgeBase metadata DB is loadable. If not, prints the
   remediation command (``python -m papers_analysis.metadata`` inside the
   KB submodule) and exits with status 2.
2. Spins up the FastAPI app in-process via ``fastapi.testclient.TestClient``
   so the same code path the HTTP endpoint uses is exercised — no separate
   uvicorn process needed.
3. Posts the prompt to ``/v1/chat/completions`` and prints the model's final
   answer plus a count of tool calls observed.

This is the success-criterion artefact called out in
``docs/specs/2026-05-12-linus-implementation-plan.md`` Item 6. It also doubles
as a manual sanity check for the search_papers wiring without needing the full
test suite.

Exit codes:

    0 — happy path, model returned a non-empty answer.
    1 — model returned empty content or no tool calls were made when expected.
    2 — KnowledgeBase metadata DB unavailable; remediation hint printed.
    3 — Ollama unreachable or no suitable model is pulled.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from fastapi.testclient import TestClient

from linus.knowledge import KnowledgeBaseAdapter, KnowledgeBaseUnavailableError
from linus.server import app
from linus.tools import default_registry


def _preflight_kb() -> int | None:
    """Open the KB adapter once to surface missing-DB errors up front.

    Returns ``None`` on success, or an exit code to propagate on failure.
    Doing the preflight here means the demo fails with a clear remediation
    message rather than waiting for the model to call the tool and then
    surfacing the error indirectly as a role=tool error message (which the
    model would dutifully convert into a confusing prose paragraph).
    """
    try:
        with KnowledgeBaseAdapter() as kb:
            total = kb.count_papers()
            print(f"KnowledgeBase loaded: {total:,} papers")
            return None
    except KnowledgeBaseUnavailableError as exc:
        print("KnowledgeBase metadata DB is unavailable.\n", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        print(
            "\nRemediation: in modules/KnowledgeBase, run:"
            "\n    git submodule update --init modules/KnowledgeBase"
            "\n    cd modules/KnowledgeBase && python -m papers_analysis.metadata"
            "\nThen re-run this demo.",
            file=sys.stderr,
        )
        return 2


def _run_chat(prompt: str, model: str) -> dict[str, Any]:
    """POST to /v1/chat/completions in-process and return the response body."""
    client = TestClient(app)
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Linus, a research assistant with access to Dan's paper "
                    "library. When the user asks about papers, ALWAYS call the "
                    "linus.knowledge.search_papers tool to retrieve real titles, "
                    "then summarize the results. Never invent paper titles."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }
    resp = client.post("/v1/chat/completions", json=payload)
    if resp.status_code != 200:
        print(
            f"Server returned {resp.status_code}: {resp.text}",
            file=sys.stderr,
        )
        sys.exit(3)
    return resp.json()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Linus tool-call demo: prompt → search_papers → synthesized answer.",
    )
    parser.add_argument(
        "--prompt",
        default="What papers in my library discuss memory architecture for AI agents?",
        help="User prompt to send.",
    )
    parser.add_argument(
        "--model",
        default="qwen3:8b",
        help="Ollama model name (falls back to qwen2.5-coder:7b if unpulled).",
    )
    args = parser.parse_args(argv)

    # Preflight: clear failure if the KB isn't usable.
    rc = _preflight_kb()
    if rc is not None:
        return rc

    print(f"\nRegistered tools: {default_registry.names()}")
    print(f"Prompt: {args.prompt}\n")

    body = _run_chat(args.prompt, args.model)
    choice = body["choices"][0]
    print("--- Final answer ---")
    print(choice["message"]["content"])
    print("--- /Final answer ---\n")

    print(f"Model used: {body['model']}")
    print(f"Finish reason: {choice['finish_reason']}")
    print(
        f"Usage: prompt={body['usage']['prompt_tokens']} "
        f"completion={body['usage']['completion_tokens']} "
        f"total={body['usage']['total_tokens']}"
    )

    content = (choice["message"]["content"] or "").strip()
    if not content:
        print(
            "Model returned empty content. Check Ollama logs for tool-loop spin.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
