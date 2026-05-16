"""Minimal Worker driver for the first Maestro/Worker loop.

Reads the spec at ``experiments/first-loop.md`` (relative to repo root), submits it to
the local Ollama server, saves the raw response to ``experiments/first_loop_output.txt``,
extracts the Python code from any markdown code fence in the response, and writes the
extracted code to ``src/linus/sandbox/fs.py``.

This is the Worker half of the first recorded Maestro/Worker loop
(``docs/specs/2026-05-12-linus-implementation-plan.md`` Item 3). The Maestro half is
this Claude Code session: writes the spec, invokes this driver, reviews the output.

Usage::

    python experiments/first_loop_driver.py

Environment::

    Requires Ollama serving at localhost:11434 with the model ``qwen2.5-coder:7b``
    pulled. ``qwen3:8b`` was the originally specified model but is not pulled locally;
    coder-7b is the closest available substitute and is purpose-built for code gen.
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

try:
    import ollama
except ImportError:  # pragma: no cover - defensive guard
    print("ERROR: the 'ollama' Python package is not installed in this env.", file=sys.stderr)
    raise


MODEL = "qwen2.5-coder:7b"
REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = REPO_ROOT / "experiments" / "first-loop.md"
RAW_OUTPUT_PATH = REPO_ROOT / "experiments" / "first_loop_output.txt"
TARGET_PATH = REPO_ROOT / "src" / "linus" / "sandbox" / "fs.py"


SYSTEM_PROMPT = (
    "You are a precise Python code-generation Worker operating under the Linus "
    "Maestro/Worker protocol. You receive a Markdown spec from the Maestro. Your job "
    "is to emit exactly one Python file that satisfies the spec, wrapped in a single "
    "```python ... ``` fenced code block. Do not add prose before or after the block. "
    "Do not split the output across multiple code blocks. The file MUST be importable "
    "as-is and MUST contain three module-level pytest test functions named "
    "test_<something> so pytest can discover them."
)


USER_PROMPT_TEMPLATE = (
    "Below is the Markdown spec. Generate the single Python file requested in the "
    "Outputs section. Emit ONLY a single ```python ... ``` fenced code block — no "
    "prose, no explanation, no second block.\n\n"
    "----- BEGIN SPEC -----\n{spec}\n----- END SPEC -----\n"
)


CODE_FENCE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL)


def read_spec() -> str:
    """Read the spec markdown file from disk and return its contents."""
    return SPEC_PATH.read_text(encoding="utf-8")


def call_worker(spec_text: str) -> str:
    """Call the Worker model via Ollama and return the assistant's full text response."""
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(spec=spec_text)},
        ],
        options={"temperature": 0.1, "num_predict": 4096},
    )
    return response["message"]["content"]


def extract_python(raw: str) -> str:
    """Extract the first Python code block from the raw response.

    If no fenced block is found, returns the raw response stripped of leading/trailing
    whitespace. The Maestro review step will catch malformed output.
    """
    match = CODE_FENCE_RE.search(raw)
    if match:
        return match.group(1).rstrip() + "\n"
    return raw.strip() + "\n"


def main() -> int:
    if not SPEC_PATH.exists():
        print(f"ERROR: spec not found at {SPEC_PATH}", file=sys.stderr)
        return 1

    print(f"[driver] Reading spec from {SPEC_PATH}")
    spec_text = read_spec()

    print(f"[driver] Calling Worker model: {MODEL}")
    t0 = time.time()
    raw_output = call_worker(spec_text)
    elapsed = time.time() - t0
    print(f"[driver] Worker returned {len(raw_output)} chars in {elapsed:.1f}s")

    print(f"[driver] Saving raw output to {RAW_OUTPUT_PATH}")
    RAW_OUTPUT_PATH.write_text(raw_output, encoding="utf-8")

    print("[driver] Extracting Python code from response")
    python_code = extract_python(raw_output)

    print(f"[driver] Writing extracted code to {TARGET_PATH}")
    TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
    TARGET_PATH.write_text(python_code, encoding="utf-8")

    print(f"[driver] Done. Wrote {len(python_code)} chars to {TARGET_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
