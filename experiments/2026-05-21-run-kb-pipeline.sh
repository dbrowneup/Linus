#!/usr/bin/env bash
# KB pipeline runner — execute all KnowledgeBase phases in sequence
# against Dan's paper corpus. Documented operational artifact, not a
# library. Runs ONLY from within KB's `papers` conda env (the `linus`
# env lacks PyMuPDF + several other KB-side deps as of 2026-05-21).
#
# Usage:
#   conda activate papers
#   bash experiments/2026-05-21-run-kb-pipeline.sh [--from PHASE] [--skip-summarize]
#
# Or, per-phase manual:
#   conda activate papers
#   cd modules/KnowledgeBase
#   python -m papers_analysis.extract
#   python -m papers_analysis.metadata
#   ... etc.
#
# Defaults assume Dan's setup:
#   - Corpus at /Users/dbrowne/Documents/Papers Library/ (19,262 PDFs)
#   - Papers app SQLite at ~/Library/Application Support/Papers/<UUID>.db
#   - Outputs land in modules/KnowledgeBase/data/
#
# Override via KB env vars per docs/specs/2026-05-21-kb-hardcoded-paths-fix.md
# (currently a proposal; KB still uses module-level constants until that spec
# ships in v0.6.0).
#
# Estimated wall times on M1 Max (rough, from KB README + Dan's prior runs):
#   - extract:         ~4.5 min full corpus (71 files/sec via PyMuPDF)
#   - metadata:        ~2 min
#   - vectorize:       ~10-30 min depending on SPECTER2 GPU/CPU split
#   - cluster:         ~5-15 min (HDBSCAN + BERTopic)
#   - graph:           ~3-10 min
#   - knowledge_graph: ~30-60 min (REBEL + SciSpacy on full corpus)
#   - summarize:       ~30-90 min if not skipped (per-cluster LLM via Ollama)
#
# Total: ~1.5-3 hours for full pipeline. Phase 7 (knowledge_graph) is usually
# the longest. Skip summarize for a faster turnaround when iterating on
# downstream consumers.

set -euo pipefail

# Resolve repo root from script location so this runs from anywhere.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
KB_DIR="$REPO_ROOT/modules/KnowledgeBase"

# Defaults
FROM_PHASE=""
SKIP_SUMMARIZE=false

# Arg parsing
while [[ $# -gt 0 ]]; do
    case "$1" in
        --from)
            FROM_PHASE="$2"
            shift 2
            ;;
        --skip-summarize)
            SKIP_SUMMARIZE=true
            shift
            ;;
        -h|--help)
            sed -n '2,40p' "$0"
            exit 0
            ;;
        *)
            echo "Unknown arg: $1" >&2
            exit 2
            ;;
    esac
done

# Sanity checks
if ! command -v python >/dev/null 2>&1; then
    echo "ERROR: 'python' not on PATH. Did you 'conda activate papers'?" >&2
    exit 1
fi
if ! python -c "import pymupdf" 2>/dev/null; then
    echo "ERROR: pymupdf not importable. Activate the 'papers' env first:" >&2
    echo "       conda activate papers" >&2
    exit 1
fi
if [[ ! -d "$KB_DIR" ]]; then
    echo "ERROR: KnowledgeBase submodule not at $KB_DIR" >&2
    echo "       (Did you 'git submodule update --init'?)" >&2
    exit 1
fi

cd "$KB_DIR"

# Phase definitions: name → module
phases=(
    "extract:papers_analysis.extract"
    "metadata:papers_analysis.metadata"
    "vectorize:papers_analysis.vectorize"
    "cluster:papers_analysis.cluster"
    "graph:papers_analysis.graph"
    "knowledge_graph:papers_analysis.knowledge_graph"
)
# summarize is optional and slowest
if [[ "$SKIP_SUMMARIZE" == false ]]; then
    phases+=("summarize:papers_analysis.summarize")
fi

# Resume support: skip phases until we hit FROM_PHASE
skip_until_found=false
if [[ -n "$FROM_PHASE" ]]; then
    skip_until_found=true
fi

START_TS_OVERALL=$(date +%s)
for phase_def in "${phases[@]}"; do
    phase_name="${phase_def%%:*}"
    phase_module="${phase_def##*:}"

    if [[ "$skip_until_found" == true ]]; then
        if [[ "$phase_name" == "$FROM_PHASE" ]]; then
            skip_until_found=false
        else
            echo "==> Skipping $phase_name (resuming from $FROM_PHASE)"
            continue
        fi
    fi

    echo ""
    echo "==> Phase: $phase_name ($(date '+%Y-%m-%d %H:%M:%S'))"
    START_TS=$(date +%s)
    python -m "$phase_module"
    END_TS=$(date +%s)
    ELAPSED=$((END_TS - START_TS))
    echo "==> Phase $phase_name complete in ${ELAPSED}s"
done

END_TS_OVERALL=$(date +%s)
ELAPSED_OVERALL=$((END_TS_OVERALL - START_TS_OVERALL))
echo ""
echo "==> All phases complete in ${ELAPSED_OVERALL}s total"
echo "==> Outputs at: $KB_DIR/data/"
echo ""
echo "Next steps:"
echo "  1. Verify outputs:"
echo "     ls $KB_DIR/data/outputs/"
echo "  2. Point Linus at them (default LINUS_KB_OUTPUTS_DIR should already work)."
echo "  3. Restart Linus server + reload Streamlit pages to see populated KB views."
