# claw-code-local (`codetwentyfive/claw-code-local`)

> Compare with [claw-code.md](./claw-code.md). This is the practical lead; upstream is inspiration only.

## 1. Purpose and scope

claw-code-local is a small, focused fork of `ultraworkers/claw-code-parity` (the clean-room Claude Code
reimplementation) that does the one thing upstream refuses to do: **let the `claw` CLI talk to local models via Ollama,
LM Studio, or any OpenAI-compatible endpoint**. The fork is two original patches on top of the upstream port: (a) wiring
the existing `ProviderClient` abstraction into the CLI so the provider is auto-detected from the model name and env vars
instead of being hardcoded to Anthropic, and (b) a streaming-markdown render fix that preserves block spacing. With
those two patches you get the full Claude-Code-style experience — interactive REPL, session persistence, 130+ slash
commands, tool use, `/commit` / `/diff` / `/pr` / `/review` / `/mcp` / `/agents` / `/skills` — driving a model that runs
on your machine, with zero API spend.

## 2. Architecture summary

Same Rust workspace as upstream claw-code-parity, with the two patches applied. The CLI auto-detects provider from model
name and environment variables: `OPENAI_API_KEY=ollama` + `OPENAI_BASE_URL=http://localhost:11434/v1` for Ollama, the
equivalent for LM Studio on port 1234, native OpenAI/ xAI/Anthropic if those keys are present. Sessions auto-save and
are resumable with `claw --resume latest`. The README is minimal — maintenance is light — but the thing works and the
patch story is small enough to audit.

## 3. What's reusable in Linus

This is the single most direct candidate for Phase 5c's terminal agent surface. "Set `OPENAI_BASE_URL` to Linus's
endpoint, `OPENAI_API_KEY` to something non-empty, run `claw --model qwen3:14b`" is the shortest path to a polished
Claude-Code-equivalent CLI against Linus. That gets Linus a terminal front-end for free in Phase 2/5 without writing a
line of Rust. The fork also validates, concretely, the Linus thesis that "harness is separable from orchestration": by
swapping out just the provider routing, the same harness works against any backend.

## 4. What's inspiration only

The maintainer has clearly done the minimum to make local models work and stopped there, which is a healthy
minimum-viable posture worth emulating in Linus's own "ship rough" phases. The upstream-sync discipline
(`git fetch upstream && git merge upstream/main`) is a reasonable pattern for any Linus-internal fork of an external
project.

## 5. What's incompatible or out of scope

Small project, light maintenance, no test matrix against many models. Model-specific prompt / tool-use quirks that
Claude Code handles for Anthropic models won't necessarily work with local models — for instance, tool-call reliability
with Qwen3:14b through the Anthropic- shaped chat templates is empirically patchy, and this fork does nothing to solve
that. It solves the API-key problem, not the behavioral-parity problem. Any Linus-side use will need a Phase 1c/2
evaluation of "what slash commands and tool calls actually work reliably against your chosen worker model?"

## 6. Recommendation: **Integrate (as Phase 2/5 harness)**

Adopt as-is in Phase 5c. Concretely: after Phase 2a stands up the Linus `/v1/chat/completions` endpoint, wire
claw-code-local as a candidate terminal front-end with the env vars pointed at Linus instead of Ollama directly. In the
interim (Phase 1–2), claw-code-local is the cleanest local CLI for driving Ollama-served workers through a
Claude-Code-style REPL. Pin a specific commit and plan to revisit if the upstream claw-code parity story changes.

## 7. Questions for Dan

1. **Skill parity.** The fork exposes Claude Code's `/skills` command, which means Anthropic-shaped `SKILL.md` files
   work inside it. That aligns with Linus's Phase 7 skills direction. Want a Phase 1e smoke-test that runs a trivial
   Linus-defined skill through claw-code-local against Ollama?
2. **Upstream drift.** claw-code-local is a thin fork. If upstream adds meaningful features (ACP/Zed mode, MCP
   refinement), should Linus maintain its own mini-patches on top, or wait for the fork to rebase? Informs the
   dependency-tracking pattern we adopt.
3. **Behavioral parity with local models.** The fork ships the patches but doesn't validate _which_ local models produce
   usable tool calls inside claw-code's templates. This is the kind of empirical question the Dan task suite is built
   for. Want the Phase 1d suite extended with a "tool-use-through-claw-code" axis?
