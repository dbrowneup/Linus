# Phase 0 Close-Out — Setup Steps

Commands to run, in order, to get from the current state to Phase 0 complete. Each step
is safe to inspect before running. Pause between steps if anything looks wrong.

## 1. Place the generated artifacts

Move the generated files from your Downloads folder (or wherever Claude delivered them)
into the Linus repo root. The files are:

- `CLAUDE.md` (replace existing empty file)
- `VISION.md` (replace)
- `ARCHITECTURE.md` (replace)
- `ROADMAP.md` (replace)
- `SAFETY.md` (replace)
- `DECISIONS.md` (replace)
- `GLOSSARY.md` (replace)
- `README.md` (replace)
- `environment.yml` (new)
- `pyproject.toml` (new)
- `.gitignore` (replace current)

And two files that go into `src/linus/`:

- `src/linus/__init__.py` (new)
- `src/linus/__about__.py` (new)

And one file into `.claude/`:

- `.claude/settings.json` (new — requires creating the `.claude/` directory)

```bash
cd ~/Desktop/Programming/GitHub/Linus

# Create the src/linus package directory
mkdir -p src/linus

# Create the .claude directory for Claude Code settings
mkdir -p .claude

# Now move the artifact files into place. Adjust source path as needed:
# (assuming artifacts are in ~/Downloads/linus_artifacts/)
ARTIFACTS=~/Downloads/linus_artifacts

cp "$ARTIFACTS/CLAUDE.md" .
cp "$ARTIFACTS/VISION.md" .
cp "$ARTIFACTS/ARCHITECTURE.md" .
cp "$ARTIFACTS/ROADMAP.md" .
cp "$ARTIFACTS/SAFETY.md" .
cp "$ARTIFACTS/DECISIONS.md" .
cp "$ARTIFACTS/GLOSSARY.md" .
cp "$ARTIFACTS/README.md" .
cp "$ARTIFACTS/environment.yml" .
cp "$ARTIFACTS/pyproject.toml" .
cp "$ARTIFACTS/.gitignore" .

cp "$ARTIFACTS/__init__.py" src/linus/__init__.py
cp "$ARTIFACTS/__about__.py" src/linus/__about__.py

cp "$ARTIFACTS/settings.json" .claude/settings.json
```

## 2. Sanity check

```bash
# Confirm everything is in place
ls -la
ls src/linus
ls .claude
tree -L 2 -a . | head -40

# Review the key files
cat CLAUDE.md | head -80
cat DECISIONS.md | head -40
```

## 3. Create the conda environment

```bash
# Create the env from spec. This takes 2-5 minutes.
conda env create -f environment.yml

# Activate it
conda activate linus

# Editable install of the linus package
pip install -e .

# Smoke test
python -c "import linus; print(linus.__version__)"
# Expected output: 0.0.1.dev0
```

## 4. Move context files into place

Context files (papers, threads, notes, pics) are gitignored but filesystem-visible to
Claude Code. Move whatever you want in scope:

```bash
# Example — adjust to your actual files
# cp ~/Downloads/1bit-llm-paper.pdf context/papers/
# cp ~/Downloads/"The Era of 1-bit LLMs".pdf context/papers/
# cp -r ~/some-notes/ context/notes/
```

## 5. First commits

```bash
# Stage the doc set
git add CLAUDE.md VISION.md ARCHITECTURE.md ROADMAP.md SAFETY.md DECISIONS.md GLOSSARY.md README.md

git commit -m "Add initial governance doc set (CLAUDE, VISION, ARCHITECTURE, ROADMAP, SAFETY, DECISIONS, GLOSSARY, README)"

# Stage the Python package scaffolding
git add src/linus/__init__.py src/linus/__about__.py pyproject.toml

git commit -m "Scaffold linus Python package with pyproject.toml"

# Stage the environment spec
git add environment.yml

git commit -m "Add conda environment.yml for linus env"

# Stage the updated gitignore
git add .gitignore

git commit -m "Update .gitignore for Linus layout (context/, linus runtime data, build artifacts)"

# Stage the Claude Code settings
git add .claude/settings.json

git commit -m "Add .claude/settings.json with ruff PostToolUse hooks"

# Push
git push origin main
```

## 6. Verify Phase 0 gate

```bash
# Environment works
conda activate linus
python -c "import linus; print(linus.__version__)"
# -> 0.0.1.dev0

# Ollama works
brew services list | grep ollama
ollama list
# Should show mistral:7b-instruct and qwen2.5-coder:7b

# Repo structure correct
tree -L 2 -a -I '.git|repos|modules|context' .
```

If all of the above pass, Phase 0 is closed. You're ready for Phase 1.

## 7. Open the first Claude Code session in Linus

From the Linus repo root in a terminal:

```bash
claude
```

First prompt to give it:

```
Read CLAUDE.md, VISION.md, ARCHITECTURE.md, and ROADMAP.md. Then review the repos
cloned into repos/ — look at the README of each. Produce a one-page synthesis note per
repo in docs/repo-notes/, following this format for each:

1. Purpose and scope (2-3 sentences)
2. Architecture summary (for code) or content overview (for non-code)
3. What's reusable in Linus
4. What's inspiration only
5. What's incompatible or out of scope
6. Recommendation: integrate / study / ignore

Repos to cover: BitNet, Bonsai-demo, ANE, flash-moe, mlx-flash, pmetal, claw-code,
claw-code-local, autoresearch, openclaw, cline, project-nomad.

This is deliverable 1a from Phase 1. Smoke-test by writing one note first (pick BitNet),
show it to me for review, then proceed with the rest in parallel Task agents.
```

That starts Phase 1 deliverable 1a and gets the Maestro/Worker loop rolling.
