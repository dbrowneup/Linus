"""Dan task suite runner — Phase 1d v0.

Discovers the three tasks under benchmarks/dan_tasks/tasks/, calls the local Ollama server with each task's prompt,
and writes a baseline results JSON to benchmarks/results/dan_tasks_baseline_<ISO date>.json.

Design notes:
- No scoring/grading in v0. Just collect outputs verbatim.
- FAIL LOUD if Ollama is unreachable or the model is not pulled. Do not silently fall back.
- The paper-summarization task uses pypdf to extract text from a real PDF in context/papers/. Per CLAUDE.md Known
  Library Quirks, pypdf's decompression limit is disabled via sys.setrecursionlimit(sys.maxsize). The decompression
  limit lives at pypdf level; we also set the recursion limit defensively because some pypdf paths recurse on deeply
  nested PDF object trees.

Usage:
    python benchmarks/dan_tasks/runners/run_all.py
    OLLAMA_MODEL=qwen3:14b python benchmarks/dan_tasks/runners/run_all.py
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
TASKS_DIR = REPO_ROOT / "benchmarks" / "dan_tasks" / "tasks"
RESULTS_DIR = REPO_ROOT / "benchmarks" / "results"

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
OLLAMA_TIMEOUT_S = int(os.environ.get("OLLAMA_TIMEOUT_S", "600"))


# ---------------------------------------------------------------------------
# FAIL LOUD helpers
# ---------------------------------------------------------------------------


class RunnerError(RuntimeError):
    """Raised when an unrecoverable runner precondition fails. Caller prints + exits non-zero."""


def _die(msg: str) -> None:
    print(f"\n[FAIL] {msg}\n", file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------------------
# Ollama I/O
# ---------------------------------------------------------------------------


def ollama_list_models() -> list[str]:
    """Return the names of pulled models. FAIL LOUD if the server is unreachable."""
    url = f"{OLLAMA_HOST}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            payload = json.loads(resp.read())
    except urllib.error.URLError as exc:
        raise RunnerError(
            f"Cannot reach Ollama at {OLLAMA_HOST}. Is it running?\n"
            f"  Start it with: brew services start ollama\n"
            f"  Underlying error: {exc}"
        ) from exc
    return [m.get("name", "") for m in payload.get("models", [])]


def ollama_generate(model: str, prompt: str) -> dict:
    """Single-shot generate via Ollama's /api/generate. Returns the parsed JSON response.

    Uses stream=False so we get one JSON object back. Embeds the prompt verbatim — task input prompts are designed to
    be standalone (no system prompt, no chat history).
    """
    url = f"{OLLAMA_HOST}/api/generate"
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
    ).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT_S) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RunnerError(
            f"Ollama HTTP {exc.code} for model {model!r}. Body: {body[:500]}\n"
            f"  If the body mentions 'model not found', pull it: ollama pull {model}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RunnerError(f"Ollama request failed: {exc}") from exc


# ---------------------------------------------------------------------------
# PDF extraction (task 1 helper)
# ---------------------------------------------------------------------------


def extract_pdf_text(pdf_path: pathlib.Path, char_limit: int) -> str:
    """Extract text from a PDF.

    Preferred path: pypdf (per the original task spec). Per CLAUDE.md Known Library Quirks, pypdf's decompression
    limit is disabled via sys.maxsize, NOT 0 or 2**63. We also raise the Python recursion limit defensively because
    some pypdf code paths recurse on nested PDF objects.

    Fallback path: `pdftotext` from poppler (CLAUDE.md documents poppler as available for PDF reading in the
    context folder). This keeps the runner functional even when no Python PDF library is installed in the linus
    env, and FAILS LOUD only if neither approach is available.
    """
    if not pdf_path.exists():
        raise RunnerError(f"Input PDF not found: {pdf_path}")

    # 1. Try pypdf (preferred).
    try:
        import pypdf  # type: ignore[import-not-found]

        # Quirk workaround — set BEFORE opening the reader.
        sys.setrecursionlimit(sys.maxsize)
        reader = pypdf.PdfReader(str(pdf_path))
        pages_text: list[str] = []
        total = 0
        for page in reader.pages:
            try:
                t = page.extract_text() or ""
            except Exception as exc:
                t = f"\n[pypdf extraction error on page: {exc}]\n"
            pages_text.append(t)
            total += len(t)
            if total >= char_limit:
                break
        full = "\n\n".join(pages_text)
        return full[:char_limit]
    except ImportError:
        pass  # fall through to pdftotext

    # 2. Fall back to poppler's pdftotext binary.
    import shutil
    import subprocess

    pdftotext = shutil.which("pdftotext")
    if pdftotext is None:
        raise RunnerError(
            "Neither pypdf (Python) nor pdftotext (poppler) is available.\n"
            "  Install pypdf in the linus env: conda run -n linus pip install pypdf\n"
            "  Or install poppler: brew install poppler"
        )
    proc = subprocess.run(
        [pdftotext, "-layout", "-q", str(pdf_path), "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RunnerError(f"pdftotext failed (rc={proc.returncode}) on {pdf_path}: {proc.stderr.strip()[:500]}")
    return proc.stdout[:char_limit]


# ---------------------------------------------------------------------------
# Per-task drivers
# ---------------------------------------------------------------------------


def run_paper_summarization(task_dir: pathlib.Path, model: str) -> dict:
    spec = json.loads((task_dir / "input.json").read_text())
    pdf_path = REPO_ROOT / spec["pdf_path"]
    extracted = extract_pdf_text(pdf_path, char_limit=12000)

    prompt = f"{spec['prompt']}\n\n--- BEGIN PAPER TEXT ---\n{extracted}\n--- END PAPER TEXT ---"
    raw = ollama_generate(model, prompt)
    response_text = raw.get("response", "")

    # Best-effort parse of a numbered list.
    parsed: list[str] = []
    for line in response_text.splitlines():
        m = re.match(r"^\s*(\d+)[\.\)]\s+(.+\S)\s*$", line)
        if m:
            parsed.append(m.group(2))

    return {
        "raw_output": response_text,
        "parsed_findings": parsed,
        "expected_finding_count": 3,
        "_meta": {
            "pdf_path": spec["pdf_path"],
            "pdf_chars_sent": len(extracted),
            "ollama_eval_count": raw.get("eval_count"),
            "ollama_total_duration_ns": raw.get("total_duration"),
        },
    }


def run_fasta_gc_content(task_dir: pathlib.Path, model: str) -> dict:
    spec = json.loads((task_dir / "input.json").read_text())
    prompt = spec["prompt"]
    raw = ollama_generate(model, prompt)
    response_text = raw.get("response", "")

    # Best-effort extraction of Python — strip a single ```python ... ``` fence if present.
    extracted = response_text.strip()
    fence = re.match(r"^```(?:python|py)?\s*\n(.*)\n```\s*$", extracted, re.DOTALL)
    if fence:
        extracted = fence.group(1)

    return {
        "raw_output": response_text,
        "extracted_python": extracted,
        "execution_attempted": False,
        "execution_result": None,
        "expected_per_sequence_lines": 5,
        "_meta": {
            "ollama_eval_count": raw.get("eval_count"),
            "ollama_total_duration_ns": raw.get("total_duration"),
        },
    }


def run_title_clustering(task_dir: pathlib.Path, model: str) -> dict:
    spec = json.loads((task_dir / "input.json").read_text())
    titles_block = "\n".join(f"- {t}" for t in spec["titles"])
    prompt = f"{spec['prompt']}\n\nTitles:\n{titles_block}"
    raw = ollama_generate(model, prompt)
    response_text = raw.get("response", "")

    # Best-effort parse of "## Cluster N: name" + bullets.
    parsed_clusters: list[dict] = []
    current: dict | None = None
    n_assigned = 0
    for line in response_text.splitlines():
        h = re.match(r"^##+\s*Cluster\s*\d+\s*[:\-]\s*(.+\S)\s*$", line, re.IGNORECASE)
        if h:
            if current:
                parsed_clusters.append(current)
            current = {"name": h.group(1).strip(), "titles": []}
            continue
        b = re.match(r"^\s*[-*+]\s+(.+\S)\s*$", line)
        if b and current is not None:
            current["titles"].append(b.group(1).strip())
            n_assigned += 1
    if current:
        parsed_clusters.append(current)

    parse_failed = len(parsed_clusters) == 0
    return {
        "raw_output": response_text,
        "parsed_clusters": parsed_clusters,
        "coverage": {
            "parse_failed": parse_failed,
            "n_clusters_parsed": len(parsed_clusters),
            "n_titles_assigned": n_assigned,
            "n_titles_input": 50,
        },
        "_meta": {
            "ollama_eval_count": raw.get("eval_count"),
            "ollama_total_duration_ns": raw.get("total_duration"),
        },
    }


TASK_DISPATCH = {
    "paper-summarization": run_paper_summarization,
    "fasta-gc-content": run_fasta_gc_content,
    "title-clustering": run_title_clustering,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Dan task suite against an Ollama-served worker model.")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Ollama model tag (default: {DEFAULT_MODEL}; also overridable via OLLAMA_MODEL env var).",
    )
    parser.add_argument(
        "--date-stamp",
        default=None,
        help="Override the date stamp in the output filename (default: today UTC).",
    )
    args = parser.parse_args()
    model = args.model

    # 1. Preflight: server reachable + model pulled.
    try:
        models = ollama_list_models()
    except RunnerError as exc:
        _die(str(exc))
        return 2  # unreachable; for type-checker

    if model not in models:
        # Tolerate Ollama's tag suffix variance (e.g., user has "qwen3:8b" but stored as "qwen3:8b-instruct").
        prefix = model.split(":")[0]
        matches = [m for m in models if m == model or m.startswith(prefix + ":")]
        if not matches:
            _die(
                f"Model {model!r} is not pulled.\n"
                f"  Pulled models: {models or '(none)'}\n"
                f"  Pull it with: ollama pull {model}"
            )

    # 2. Discover tasks.
    task_slugs = sorted(p.name for p in TASKS_DIR.iterdir() if p.is_dir())
    missing = [s for s in task_slugs if s not in TASK_DISPATCH]
    if missing:
        _die(f"Task directories without a dispatcher: {missing}. Update TASK_DISPATCH in this script.")

    print(f"[runner] Ollama OK at {OLLAMA_HOST}; model={model}")
    print(f"[runner] Tasks discovered: {task_slugs}")

    # 3. Run each task.
    started_at = _dt.datetime.now(_dt.UTC)
    entries: list[dict] = []
    for slug in task_slugs:
        task_dir = TASKS_DIR / slug
        print(f"\n[runner] === {slug} ===", flush=True)
        t0 = time.time()
        try:
            output = TASK_DISPATCH[slug](task_dir, model)
            status = "ok"
            err = None
        except RunnerError as exc:
            print(f"[runner] {slug} FAILED: {exc}", file=sys.stderr)
            output = None
            status = "error"
            err = str(exc)
        except Exception as exc:
            print(f"[runner] {slug} EXCEPTION: {exc!r}", file=sys.stderr)
            output = None
            status = "exception"
            err = repr(exc)
        elapsed_s = time.time() - t0
        print(f"[runner] {slug} {status} in {elapsed_s:.1f}s")
        entries.append(
            {
                "task": slug,
                "status": status,
                "error": err,
                "elapsed_s": round(elapsed_s, 2),
                "output": output,
            }
        )

    finished_at = _dt.datetime.now(_dt.UTC)

    # 4. Write results.
    date_stamp = args.date_stamp or started_at.strftime("%Y-%m-%d")
    out_path = RESULTS_DIR / f"dan_tasks_baseline_{date_stamp}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "v0",
        "suite": "dan_tasks",
        "model": model,
        "ollama_host": OLLAMA_HOST,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "wall_time_s": round((finished_at - started_at).total_seconds(), 2),
        "results": entries,
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"\n[runner] Wrote {out_path}")

    # Exit non-zero if any task failed, so CI can pick it up later.
    n_err = sum(1 for e in entries if e["status"] != "ok")
    if n_err:
        print(f"[runner] {n_err}/{len(entries)} tasks did not complete cleanly.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
