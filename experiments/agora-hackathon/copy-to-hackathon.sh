#!/usr/bin/env bash
# copy-to-hackathon.sh
#
# Copies the Linus-staged Agora artifacts into the hackathon repo's docs/ tree
# with the right names and at the right paths. Idempotent.
#
# Usage:
#   ./copy-to-hackathon.sh               # default paths; copies files
#   DRY_RUN=1 ./copy-to-hackathon.sh     # show what would happen without doing it
#   SOURCE_DIR=... TARGET_DIR=... ./copy-to-hackathon.sh   # override paths
#
# Defaults:
#   SOURCE_DIR=$HOME/Desktop/Programming/GitHub/Linus/experiments/agora-hackathon
#   TARGET_DIR=$HOME/Desktop/Programming/GitHub/Agora/hackathon

set -euo pipefail

SOURCE_DIR="${SOURCE_DIR:-$HOME/Desktop/Programming/GitHub/Linus/experiments/agora-hackathon}"
TARGET_DIR="${TARGET_DIR:-$HOME/Desktop/Programming/GitHub/Agora/hackathon}"
DRY_RUN="${DRY_RUN:-0}"

# --- helpers ---------------------------------------------------------------

err() { echo "ERROR: $*" >&2; exit 1; }
info() { echo "  $*"; }

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
    err "Target directory does not exist: $TARGET_DIR  (clone the hackathon repo first?)"
fi

if [[ ! -d "$TARGET_DIR/.git" ]] && [[ ! -e "$TARGET_DIR/.git" ]]; then
    err "Target directory is not a git repo: $TARGET_DIR"
fi

echo "Source: $SOURCE_DIR"
echo "Target: $TARGET_DIR"
echo "Dry run: $DRY_RUN"
echo ""

# --- copy operations -------------------------------------------------------

echo "Root-level files:"
# HACKATHON-CLAUDE.md -> CLAUDE.md at repo root
copy_file "$SOURCE_DIR/HACKATHON-CLAUDE.md" "$TARGET_DIR/CLAUDE.md"

echo ""
echo "docs/ — strategic + analytical docs:"
copy_file "$SOURCE_DIR/competitor-landscape.md"            "$TARGET_DIR/docs/competitor-landscape.md"
copy_file "$SOURCE_DIR/architectural-principles.md"        "$TARGET_DIR/docs/architectural-principles.md"
copy_file "$SOURCE_DIR/custody-and-settlement.md"          "$TARGET_DIR/docs/custody-and-settlement.md"
copy_file "$SOURCE_DIR/reputation-and-vertical-selection.md" "$TARGET_DIR/docs/reputation-and-vertical-selection.md"
copy_file "$SOURCE_DIR/current-repo-red-team.md"           "$TARGET_DIR/docs/current-repo-red-team.md"
copy_file "$SOURCE_DIR/rfb-selection-memo.md"              "$TARGET_DIR/docs/rfb-selection-memo.md"
copy_file "$SOURCE_DIR/demo-script-pitch-deck-outline.md"  "$TARGET_DIR/docs/demo-script-pitch-deck-outline.md"
copy_file "$SOURCE_DIR/anti-features.md"                   "$TARGET_DIR/docs/anti-features.md"

echo ""
echo "docs/specs/ — implementation specs:"
copy_file "$SOURCE_DIR/agent-passport-spec.md"             "$TARGET_DIR/docs/specs/agent-passport-spec.md"
copy_file "$SOURCE_DIR/mcp-integration-decision-memo.md"   "$TARGET_DIR/docs/specs/mcp-integration-decision-memo.md"

echo ""
if [[ "$DRY_RUN" == "1" ]]; then
    echo "Dry run complete. No files were copied."
else
    echo "Done. $(ls -1 "$TARGET_DIR/docs" | wc -l | tr -d ' ') docs + $(ls -1 "$TARGET_DIR/docs/specs" | wc -l | tr -d ' ') specs in place."
    echo ""
    echo "Next steps (run from $TARGET_DIR):"
    echo "  git status"
    echo "  git add CLAUDE.md docs/"
    echo "  git commit -m '[docs] Add strategic and architectural docs (CLAUDE.md, competitor landscape, passport spec, etc.)'"
    echo "  git push"
fi
