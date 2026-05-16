# DEC-0055 — Filename discipline: no spaces or special characters in tracked paths

**Status:** Accepted **Date:** 2026-05-16 **Authors:** Dan Browne (Maestro), Claude Code

## Context

Files with spaces or non-ASCII special characters in their filenames require URL-encoding when referenced from markdown
links (`%20` for space, `%27` for ASCII apostrophe, `%E2%80%99` for curly apostrophe, `%28`/`%29` for parens, etc.).
Several past fold-ins hit silent link rot from URL-encoding mistakes — the Anthropic Responsible Scaling Policy PDF
broke twice because its filename contains a curly apostrophe (`'`) rather than a straight one (`'`), and the encoding
was non-obvious until a clicker found the dead link.

Audit on 2026-05-16 enumerated **22 files with spaces or special characters** across the repo:

- 6 in `context/notes/`
- 2 in `context/papers/`
- 4 in `context/pics/`
- 9 in `context/threads/`
- 1 tracked file in `docs/paper-notes/` (`Horiike-...-Physical Review E copy.md` — also has a stale ` copy` suffix
  artifact from an earlier `cp -p`)

All of `context/` is gitignored at present, so 21 of 22 affected files do not live in git history. The one tracked
file (the Horiike paper-note) is renamed via `git mv` rather than `mv`.

PR 31 will also queue Tier 9 — adopting Git LFS for `context/` — which makes filename discipline more load-bearing:
once LFS tracks a file, future renames become "delete + add" against LFS history and consume bandwidth quota. The
clean filenames must land BEFORE LFS adoption, not after.

## Decision

Adopt a single project-wide convention:

**Tracked paths and locally-mirrored primary sources use ASCII-safe filenames. No spaces, no curly punctuation, no
characters requiring URL-encoding in markdown links.**

### Rename rules

Applied recursively to all current files with spaces under `context/` and `docs/`:

1. **Spaces → hyphens** (`-`). Collapse runs of multiple spaces to a single hyphen.
2. **Apostrophes (both ASCII `'` and curly `'`) → stripped.** `Anthropic's` becomes `Anthropic`. Plural-`s` forms
   are preserved by keeping the `s` (`Anthropics`); possessive-`s` forms drop the apostrophe and keep the `s`.
3. **Parentheses → hyphens.** `(version 3.0)` becomes `-v3.0`. Strip the surrounding spaces too, so the result is
   single-dash-joined.
4. **Commas and question marks → stripped** (not replaced).
5. **Unicode arrows (`→`) → `to`.** Surround with hyphens to preserve word boundaries.
6. **Ampersands (`&`) → `and`.** Surround with hyphens.
7. **Colons (`:`) → hyphens (`-`).** Some filesystems (older macOS HFS+, some FAT variants) disallow them
   outright. Replacing with hyphens preserves separator semantics (e.g., `$312:Day` becomes `312-Day` rather
   than `312Day`).
8. **Dollar signs (`$`) → stripped** for the same path-safety reason.
9. **Trailing ` copy` suffix** (artifact of `cp` operations) → stripped.
10. **Collapse runs of `-`** to a single `-` after all substitutions.

### Capitalization policy

**Preserve proper-noun capitalization in the source; lowercase descriptive terms only when the source already does so.**

The repo's existing convention is mixed-case for proper nouns (`Letta.md`, `Kimi-K2.md`, `AutoGen.md`) and ASCII-safe
for filenames generally. The rename should keep `Anthropic`, `Bonsai`, `Bush`, `Claude`, `Horiike`, `Karpathy`, `Rohit`
in their original case. Descriptive terms (`generative`, `modeling`, `responsible`, `scaling`) follow source
capitalization.

### Code paths and external citations

This rule does not apply to:

- Filenames inside vendored `repos/` (read-only reference clones, not under Linus's curation).
- Generated artifacts (build outputs, conda env caches, etc.).
- Filenames in external systems (GitHub URLs, arxiv IDs, DOIs) — those follow upstream conventions.

## Consequences

**Positive:**

- Every markdown link to a primary source resolves without URL-encoding.
- `grep` for a filename works against bare strings (no need to also search `%20`-encoded variants).
- Future LFS adoption (Tier 9, deferred) starts from clean filenames.
- Removes a recurring foot-gun (the Anthropic RSP curly-apostrophe broke twice prior to this rule).

**Negative:**

- One-time touch across ~30 markdown files to update references.
- Loses a small amount of source-fidelity in filename — the file is now `Anthropic-Responsible-Scaling-Policy-v3.0.pdf`
  rather than literally what Anthropic shipped. Not load-bearing; the document's own title page carries the canonical
  citation.
- Cherry-picks of older commits that touch the renamed files may produce trivial conflicts. Mitigation: PR 31 is
  small enough to be cherry-picked atomically rather than fragment-by-fragment.

**Out of scope for this ADR:**

- Adopting Git LFS for `context/` (Tier 9 of the PR 30 cleanup spec) — separate ADR DEC-0056 if/when that lands.
- Bulk-renaming files under `repos/` — those are vendored.

## Implementation

PR 31 (`agent/pr31-rename-files`):

1. This ADR (DEC-0055).
2. Mechanical rename script applies the rules above to the 22 enumerated files.
3. Reference update across markdown files in `docs/` that link to the spaced filenames.
4. Verification grep confirms no remaining spaces or URL-encoded characters in `context/` link targets.

Atomic commits per phase (ADR, context/ renames, docs/ paper-note rename, reference updates).

## Related

- PR 30 cleanup spec at [`docs/specs/2026-05-10-pr30-cleanup-spec.md`](../specs/2026-05-10-pr30-cleanup-spec.md) — Tier 8 origin.
- Future ADR for Git LFS adoption (deferred; not yet authored).
