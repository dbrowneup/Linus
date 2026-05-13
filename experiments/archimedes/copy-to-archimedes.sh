#!/usr/bin/env bash
# copy-to-archimedes.sh
#
# Copies the Linus-staged Archimedes artifacts into the archimedes repo's docs/ tree
# with the right names and at the right paths. Idempotent. Does NOT overwrite
# Chuan's existing docs/design.md.
#
# Usage:
#   ./copy-to-archimedes.sh               # default paths; copies files
#   DRY_RUN=1 ./copy-to-archimedes.sh     # show what would happen without doing it
#   SOURCE_DIR=... TARGET_DIR=... ./copy-to-archimedes.sh   # override paths
#
# Defaults:
#   SOURCE_DIR=$HOME/Desktop/Programming/GitHub/Linus/experiments/archimedes
#   TARGET_DIR=$HOME/Desktop/Programming/GitHub/Agora/archimedes

set -euo pipefail

SOURCE_DIR="${SOURCE_DIR:-$HOME/Desktop/Programming/GitHub/Linus/experiments/archimedes}"
TARGET_DIR="${TARGET_DIR:-$HOME/Desktop/Programming/GitHub/Agora/archimedes}"
DRY_RUN="${DRY_RUN:-0}"

# --- helpers ---------------------------------------------------------------

err() { echo "ERROR: $*" >&2; exit 1; }
info() { echo "  $*"; }
warn() { echo "  ⚠ $*"; }

copy_file() {
    local src="$1"
    local dst="$2"
    if [[ ! -f "$src" ]]; then
        err "Source file missing: $src"
    fi
    if [[ "$DRY_RUN" == "1" ]]; then
        info "DRY-RUN cp \"$src\" \"$dst\""
    else
        mkdir -p "$(dirname "$dst")"
        cp "$src" "$dst"
        info "$(basename "$src") -> $dst"
    fi
}

# --- validation ------------------------------------------------------------

if [[ ! -d "$SOURCE_DIR" ]]; then
    err "Source directory does not exist: $SOURCE_DIR"
fi

if [[ ! -d "$TARGET_DIR" ]]; then
    err "Target directory does not exist: $TARGET_DIR  (clone the archimedes repo first?)"
fi

if [[ ! -d "$TARGET_DIR/.git" ]] && [[ ! -e "$TARGET_DIR/.git" ]]; then
    err "Target directory is not a git repo: $TARGET_DIR"
fi

# Safety check: do NOT overwrite Chuan's design.md if it exists
if [[ -f "$TARGET_DIR/docs/design.md" ]]; then
    warn "Existing docs/design.md detected (Chuan's design doc) — will NOT be touched."
fi

echo "Source: $SOURCE_DIR"
echo "Target: $TARGET_DIR"
echo "Dry run: $DRY_RUN"
echo ""

# Branch warning
CURRENT_BRANCH=$(git -C "$TARGET_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
echo "Current branch in target: $CURRENT_BRANCH"
if [[ "$CURRENT_BRANCH" == "main" ]]; then
    warn "You are on 'main'. Consider creating a feature branch first:"
    warn "    git -C $TARGET_DIR switch -c feat/docs-onboarding"
fi
echo ""

# --- copy operations -------------------------------------------------------

echo "Root-level files:"
# CLAUDE.md at repo root (Claude Code session-startup convention)
copy_file "$SOURCE_DIR/CLAUDE.md" "$TARGET_DIR/CLAUDE.md"
# README.md — overwrites the empty stub
copy_file "$SOURCE_DIR/README.md" "$TARGET_DIR/README.md"
# environment.yml — conda env for Python backend
copy_file "$SOURCE_DIR/environment.yml" "$TARGET_DIR/environment.yml"

echo ""
echo "docs/ — strategic + analytical docs:"
copy_file "$SOURCE_DIR/architectural-principles.md"       "$TARGET_DIR/docs/architectural-principles.md"
copy_file "$SOURCE_DIR/competitor-landscape.md"           "$TARGET_DIR/docs/competitor-landscape.md"
copy_file "$SOURCE_DIR/rfb-alignment.md"                  "$TARGET_DIR/docs/rfb-alignment.md"
copy_file "$SOURCE_DIR/mvp-scope-memo.md"                 "$TARGET_DIR/docs/mvp-scope-memo.md"
copy_file "$SOURCE_DIR/anti-features.md"                  "$TARGET_DIR/docs/anti-features.md"
copy_file "$SOURCE_DIR/qfin-paper-corpus-seed.md"         "$TARGET_DIR/docs/qfin-paper-corpus-seed.md"
copy_file "$SOURCE_DIR/demo-script-pitch-deck-outline.md" "$TARGET_DIR/docs/demo-script-pitch-deck-outline.md"
copy_file "$SOURCE_DIR/claude-design-prompts.md"          "$TARGET_DIR/docs/claude-design-prompts.md"

echo ""
echo "docs/specs/ — implementation specs:"
copy_file "$SOURCE_DIR/specs/strategy-passport-spec.md"               "$TARGET_DIR/docs/specs/strategy-passport-spec.md"
copy_file "$SOURCE_DIR/specs/backtrader-vs-vectorbt-decision-memo.md" "$TARGET_DIR/docs/specs/backtrader-vs-vectorbt-decision-memo.md"

echo ""
if [[ "$DRY_RUN" == "1" ]]; then
    echo "Dry run complete. No files were copied."
else
    doc_count=$(ls -1 "$TARGET_DIR/docs" 2>/dev/null | wc -l | tr -d ' ')
    spec_count=$(ls -1 "$TARGET_DIR/docs/specs" 2>/dev/null | wc -l | tr -d ' ')
    echo "Done. $doc_count docs + $spec_count specs in place."
    echo ""
    echo "Next steps (run from $TARGET_DIR):"
    echo "  git status"
    echo ""
    echo "If you want to commit on a new branch (recommended):"
    echo "  git switch -c feat/docs-strategy-and-passport"
    echo "  git add CLAUDE.md docs/"
    echo "  git commit -m '[docs] Add CLAUDE.md, strategy passport, RFB alignment, MVP scope, anti-features, competitor landscape, Q-fin corpus seed, demo/pitch outline, Claude Design prompts'"
    echo "  git push -u origin feat/docs-strategy-and-passport"
    echo "  gh pr create --base develop --fill"
fi
