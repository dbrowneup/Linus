## DEC-0007 — Claude Code remains the terminal Maestro; claw-code is reference-only

**Date:** 2026-04-22
**Status:** accepted (amended 2026-04-23 to note claw-code-local fork; further amended by DEC-0021)

**Context.** Dan wanted a terminal-based agent harness usable with local models.
claw-code is an open-source Rust harness with similar interface but requires an
Anthropic API key and does not natively support Ollama.

**Decision.** **Claude Code (hosted) is the terminal Maestro** for the foreseeable
future. claw-code is kept as a reference clone in `repos/claw-code/` — study its
architecture and philosophy, but do not adopt it as a runtime component. A local-model
terminal agent is a Phase 5+ deliverable, built as either a thin wrapper on Linus's
backend (~500 LOC) or by adopting Cline's CLI mode if it fits.

**Consequence.** Avoids the sunk cost of patching claw-code to support local models.
Keeps near-term focus on Linus's orchestration layer. Terminal-local-agent need gets
addressed when it becomes concrete.

**Amendment 2026-04-23 — claw-code-local fork.** A community fork
([github.com/codetwentyfive/claw-code-local](https://github.com/codetwentyfive/claw-code-local))
already adds an Ollama backend to claw-code, which is exactly the gap that made upstream
claw-code reference-only. It's now cloned at `repos/claw-code-local/`. Treat upstream
**claw-code as inspiration** (architecture and philosophy) and **claw-code-local as a
practical lead** for the Phase 5+ terminal-local-agent deliverable — possibly directly
adoptable, possibly a starting point we extend. pmetal integration would still be net-new
work on top of either. The decision above does not change yet: Claude Code remains the
terminal Maestro and we are not adopting a local CLI harness as a runtime component
today. Re-evaluate when Phase 5 work begins.
