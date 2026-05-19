# claw-code (`ultraworkers/claw-code`)

_Refreshed 2026-05-18 against upstream HEAD f8e1bb7; 339 commits / 128 files reviewed._

> Compare with [claw-code-local.md](./claw-code-local.md). The two are sibling entries: upstream vs. practical local
> fork.

## 1. Purpose and scope

claw-code is a Rust CLI agent harness — a clean-room reimplementation of Claude Code's terminal experience: interactive
REPL, session persistence, tool use (file read/write/edit, grep, glob, bash, git), slash commands, markdown rendering. As
of 2026-05-18 it has materially broadened its provider story: the upstream README and a new
`docs/local-openai-compatible-providers.md` now explicitly position Claw as a "Claude-Code-shaped workflow/runtime, not a
Claude-only product," with first-class OpenAI-compatible routing against Ollama, llama.cpp, and vLLM. The hard
ANTHROPIC_API_KEY lock-in is gone; `OPENAI_BASE_URL` + `OPENAI_API_KEY` (or a placeholder for authless local servers)
suffices for a `claw prompt` smoke test against `qwen3:latest` on `http://127.0.0.1:11434/v1`. This is the change that
matters for Phase 5c: the upstream is now usable as the canonical CLI surface against a Linus-hosted OpenAI-compatible
endpoint without forking, though claw-code-local remains the friendlier on-ramp for offline-first workflows.

## 2. Architecture summary

Rust workspace under `rust/` containing the `claw` binary across nine crates: `api`, `commands`, `compat-harness`,
`mock-anthropic-service`, `plugins`, `runtime`, `rusty-claude-cli`, `telemetry`, `tools`. The Rust port has crossed a
recognizable parity milestone — `PARITY.md` reports the 9-lane checkpoint merged on `main` (bash validation, CI sandbox
fix, file-tool edge guards, TaskRegistry, task wiring, Team+Cron registry, MCP lifecycle, LSP client, permission
enforcement), 48,599 tracked Rust LOC, 12 scripted mock-parity scenarios with 21 captured `/v1/messages` requests, and a
deterministic mock-Anthropic service for clean-environment harness runs. The OpenAI-compat path is the documented
extension surface, not just an internal abstraction: tool-call shapes and response formats are honestly flagged as
provider-dependent, and `--model "openai/..."` prefix routing wins over ambient Anthropic credentials. ACP/Zed is still
not real — `claw acp serve` remains a discoverability alias that returns status with exit code 0; the public JSON
contract is documented in `docs/g011-acp-json-rpc-status-contract.md` but the daemon is not shipped. Companion ecosystem
(clawhip + oh-my-codex + oh-my-openagent + oh-my-claudecode) is the actual operating model per `PHILOSOPHY.md`: humans
direct via Discord, claws execute autonomously through the harness.

## 3. What's reusable in Linus

The Phase 5c story is much cleaner than the prior note allowed. Upstream `claw` now points at a Linus OpenAI-compatible
endpoint with five lines of env setup (`OPENAI_BASE_URL=http://127.0.0.1:<linus-port>/v1` + a placeholder token + an
explicit `--model` argument), no fork required. That removes claw-code-local from the critical path for the basic CLI
case — though the fork still wins for offline skill installs and the more aggressive local-first polish. The 9-lane
checkpoint also delivers patterns Linus's Phase 2a backend should copy outright: the `runtime::sandbox` probe-capability
pattern (instead of binary-presence checks), the `file_ops` workspace-boundary + symlink-escape + NUL-byte binary guards,
the `TaskRegistry` in-memory lifecycle API, and the `PermissionEnforcer` cross-tool gating. The mock-Anthropic harness
(`rust/crates/mock-anthropic-service` + `mock_parity_harness.rs`) is a directly liftable shape for Linus's own
provider-contract testing — deterministic, scenario-scripted, clean-environment. The "claw doctor" first-health-check
pattern is a good model for a `linus doctor` equivalent at Phase 2a.

## 4. What's inspiration only

`PHILOSOPHY.md` is worth lifting framing from: the bottleneck-shift argument (typing speed → architectural clarity, task
decomposition, judgment, taste, conviction) overlaps directly with Linus's Maestro/Worker discipline. The clawhip + OmX +
OmO three-part decomposition (workflow layer ↔ event router ↔ multi-agent coordination) is one viable answer to the
"orchestration backend" problem, but Linus has chosen a different shape (single orchestration layer + harness plurality
per DEC-0017) and there's no need to mirror the structure. The companion UltraWorkers ecosystem (clawhip,
oh-my-claudecode, oh-my-codex, oh-my-openagent) demonstrates a small-tools toolbelt around an agent harness; useful
reference for what Linus's own toolbelt should grow once the orchestration layer exists, but not adoptable as-is.

## 5. What's incompatible or out of scope

The `cargo install claw-code` trap is still active and now explicitly warned against in the upstream README — the
crates.io `claw-code` crate is a deprecated stub that places `claw-code-deprecated.exe`; the renamed upstream binary is
`cargo install agent-code` (installs `agent`, not `agent-code`). Linus integration should always be build-from-source
against the `ultraworkers/claw-code` repo. ACP/Zed remains aspirational — do not plan around it for Phase 5c. The
clawhip-Discord-as-human-interface model from `PHILOSOPHY.md` is the upstream's operating mode but not Linus's; Linus's
human interface is the terminal (Claude Code), VS Code, and eventually openclaw, and the Discord-routing assumption in
clawhip is not transplantable. The mock-Anthropic harness is Anthropic-specific by design; an OpenAI-compat equivalent
for Linus would need to be written, not lifted.

## 6. Recommendation: **Study** _(was "Study (and defer to claw-code-local)")_

Verdict tightened from the prior "defer to claw-code-local" gloss. The upstream's documented OpenAI-compat path means
claw-code itself is now a viable Phase 5c CLI front-end against a Linus endpoint, and the 9-lane parity work has produced
several patterns (sandbox probe, file-op guards, TaskRegistry, permission enforcer, mock-parity harness) worth lifting
into Linus's Phase 2a backend. Read `USAGE.md`, `PARITY.md`, `docs/local-openai-compatible-providers.md`,
`docs/g011-acp-json-rpc-status-contract.md`, and the `runtime` crate before designing Linus's permission/sandbox layer.
Do not adopt the Rust workspace wholesale — Linus orchestration stays Python — but the Rust patterns are concrete enough
to translate. claw-code-local still wins for the offline-skills polish; both upstream and fork are now first-class
references rather than upstream-then-fork.

## 7. Questions for Dan

1. **Phase 5c CLI surface choice.** With upstream claw-code now supporting OpenAI-compat against a Linus endpoint
   directly, is the Phase 5c plan still "claw-code-local as the on-ramp" or does upstream now become the canonical
   target with claw-code-local as a fallback for offline-skill workflows? Prior note assumed the fork was the practical
   lead; the OpenAI-compat addition shifts that.
2. **Mock-parity harness shape for Linus.** claw-code's `mock-anthropic-service` + scripted scenarios pattern is directly
   transplantable to a Linus OpenAI-compat contract harness. Worth adding to the Phase 2a spec as an explicit
   deliverable, or defer to Phase 2b after the orchestration layer is real?
3. **ACP/Zed as a Linus surface.** Status unchanged from prior note — still aspirational upstream, no shipping daemon,
   tracked in claw-code's `ROADMAP.md` but not built. Worth flagging only if the Zed ecosystem becomes a priority for
   Linus front-ends.
