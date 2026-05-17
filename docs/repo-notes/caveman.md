# caveman (`JuliusBrussee/caveman`)

## 1. Purpose and scope

caveman is a Claude Code skill plus a cross-harness install matrix (Codex, Gemini CLI, Cursor, Windsurf, Cline,
Copilot, opencode, OpenClaw, plus ~30 other agents reached via the `npx skills` upstream) that constrains agent output
to "caveman talk" — short, telegraphic, filler-free responses that preserve technical content. The headline empirical
claim is **~65–75% output-token reduction at 100% technical accuracy**, validated by a three-arm eval harness in
`evals/` that compares the skill against a vanilla `Answer concisely.` system prompt (not against the verbose default —
the delta is honest, in the maintainer's words) and by a token-counted benchmark suite in `benchmarks/` that calls the
real Claude API on ten representative prompts. The MIT-licensed repo (Julius Brussee, single maintainer) ships six
intensity levels (`lite` / `full` / `ultra` / `wenyan-lite` / `wenyan-full` / `wenyan-ultra`), seven slash commands
(`/caveman`, `/caveman-commit`, `/caveman-review`, `/caveman-help`, `/caveman-stats`, `/caveman-compress`, plus the
`cavecrew-*` subagent set), an MCP middleware wrapper (`caveman-shrink`) that compresses external MCP tool
descriptions, and a `caveman-compress` sub-skill that rewrites memory files (e.g. a long `CLAUDE.md`) into caveman-speak
to cut input-token costs at session start. For Linus, this is a **skill, not a framework or substrate** — it is the
clearest worked example in the cloned corpus of "output-token-budget compression as a first-class agent skill," and the
pattern is directly applicable to the DEC-0032 in-context-window-cap policy that Linus has already committed to. The
right relationship is Study the pattern, Adapt the compression discipline into the Phase 2a Worker output budget
contract, and ignore the install machinery — Linus's Worker invocations are not multi-harness consumer installs.

## 2. Architecture summary

The repo is a single-maintainer Node-based distribution package with a TypeScript-free, JavaScript-on-Node-≥18 install
path. The architectural story has four parts: skills (the LLM-facing prompts), the unified installer (a single
`bin/install.js` with a `PROVIDERS` array driving per-agent dispatch), the Claude Code hook system (three hooks plus a
shared module), and the cross-harness distribution shape (a `npx skills add` upstream call for everything that does not
have native hooks). All four parts are documented in detail in the repo's `CLAUDE.md`; the summary here picks out the
load-bearing pieces.

The **skills** under `skills/<name>/{SKILL.md, README.md}` are the source of truth. Each skill is a YAML-frontmatter
Markdown file the agent loads as a prompt; the README is human-facing and the SKILL.md is LLM-facing. The seven skills
are independent but compose: `caveman` is the always-on output-compression rule; `caveman-commit` enforces Conventional
Commits with ≤50-char subjects; `caveman-review` produces one-line PR comments in `L<line>: <severity> <problem>. <fix>.`
format; `caveman-help` is a one-shot reference card; `caveman-stats` reads Claude Code session logs and computes
lifetime token savings; `caveman-compress` rewrites memory files (CLAUDE.md, project notes) into caveman style while
preserving code blocks, URLs, file paths, and shell commands byte-for-byte; `cavecrew` is a small set of subagent
spawners (`cavecrew-investigator`, `cavecrew-builder`, `cavecrew-reviewer`) that delegate to Haiku-shaped subagents
running their own caveman rule and producing terse outputs of the form `path:line — symbol — note`.

The **intensity levels** are defined inside `skills/caveman/SKILL.md`: `lite` drops filler only; `full` (the default)
applies fragment-style prose; `ultra` is telegraphic; `wenyan` variants apply classical Chinese for additional
compression. A small but load-bearing **auto-clarity rule** is baked into the SKILL.md: caveman temporarily drops to
normal prose for security warnings, irreversible-action confirmations, multi-step sequences where fragment ambiguity
risks misread, or when the user is confused or repeating a question. This is the discipline that prevents compression
from corrupting correctness — the same property Dan's DEC-0032 cap-bypass-audit-log rule encodes for Linus.

The **unified installer** at `bin/install.js` is the single source of truth for how the skill reaches each agent. A
single `PROVIDERS` array carries entries with `id`, `label`, `mech` (`plugin` / `hook` / `rule-file` / `npx-skills`),
`detect` (a clause spec like `command:foo||dir:$HOME/x`), and optional `profile` (the upstream vercel-labs/skills slug)
plus a `soft: true` flag for config-dir-only probes. The two shims at the repo root (`install.sh` and `install.ps1`)
each contain ~30 lines that delegate to `bin/install.js` via either local-clone `node` or `npx -y github:JuliusBrussee/caveman`.
Settings.json reads go through `bin/lib/settings.js`'s JSONC-tolerant reader (some agents ship commented settings
files); writes go through a `validateHookFields()` defensive check before any merge, because Claude Code's Zod schema
silently discards the entire settings.json on validation failure if a single malformed hook entry slips in.

The **Claude Code hook system** in `src/hooks/` is three JavaScript files plus a shared module plus a CommonJS pin. The
shared module `caveman-config.js` exports a `safeWriteFlag(flagPath, content)` helper that refuses to follow symlinks,
opens with `O_NOFOLLOW` where supported, writes atomically via temp-and-rename, and creates the flag file with mode
`0600` — a small but real defense against a local-attacker symlink-clobber attack on the predictable
`$CLAUDE_CONFIG_DIR/.caveman-active` path. The three hooks are: `caveman-activate.js` (SessionStart hook — writes the
active mode to the flag file, emits the full caveman ruleset to stdout which Claude Code injects as system context, and
checks for a configured statusline); `caveman-mode-tracker.js` (UserPromptSubmit hook — parses slash-command activation
like `/caveman ultra`, natural-language activation like "talk like caveman", and natural-language deactivation like
"normal mode" / "stop caveman", and emits a small `hookSpecificOutput` per-turn reinforcement to keep caveman style
stable across long sessions where other plugins inject competing instructions); and `caveman-statusline.sh` (a
statusline-renderer that reads the flag file and a `.caveman-statusline-suffix` file containing the lifetime savings
counter, both symlink-validated and whitelist-validated to prevent arbitrary-byte injection into the statusline).

The **evaluation harness** under `evals/` is a three-arm eval (`__baseline__` no-system-prompt, `__terse__` plain
`Answer concisely.`, and `<skill>` the full SKILL.md), all run through `claude -p --system-prompt` and saved to
`evals/snapshots/results.json`. The `measure.py` step computes deltas offline using tiktoken (approximation of Claude's
tokenizer; ratios are meaningful, absolute counts approximate). The discipline rule baked in: **honest delta = skill
vs. terse**, not skill vs. baseline, because comparing against the verbose default would conflate the skill with
generic conciseness. The `benchmarks/` directory ships a separate harness that calls the real Claude API with
`ANTHROPIC_API_KEY` and produces the canonical 10-prompt benchmark table embedded in the README (average 65% output
reduction, range 22–87%). Both sets of numbers — eval-harness ratios and benchmark-suite absolute counts — are
committed to git so CI can read them without API calls; only regenerate when SKILL.md changes.

The **MCP middleware** at `src/mcp-servers/caveman-shrink/` is a separately-npm-published package
(`caveman-shrink`) that wraps any MCP server and rewrites its tool descriptions in caveman style before passing them to
the agent — i.e., it compresses the input-token side of MCP tool registration the same way the main skill compresses
the output side. The `caveman-compress` sub-skill addresses the other input-token target: long memory files like
`CLAUDE.md` itself, which prepend to every session start. Both pieces extend the "compress everywhere the agent is
spending tokens" thesis from output-only to the full token budget.

## 3. What's reusable in Linus

**Phase 2a — output-token-budget compression as a Worker contract field (DEC-0032).** This is the load-bearing
connection. DEC-0032 commits Linus to a default 16K in-context window cap per Worker call, with overflow routed through
the episodic store and explicit cap-bypass audit-logged. The cap is about **input** tokens; caveman's contribution is
the symmetric **output**-side discipline: a Worker registered with a `concise` / `terse` / `default` output-budget tag
can be invoked with a "caveman-style" system-prompt rider whose empirical effect (per the
[March 2026 brevity-constraints paper](https://arxiv.org/abs/2604.00025) cited in the caveman README) is sometimes
**+26 accuracy points on certain benchmarks** when the model is forced to be brief. The Phase 2a Worker spec should
absorb an explicit `output_style` field (`verbose` / `default` / `terse` / `caveman`) alongside the existing
`memory_mode` and `cot_budget` (DEC-0031), with the dispatcher injecting the corresponding system-prompt rider and the
audit log recording the choice. The `terse` default for code-review-style Workers (the Linus equivalent of
`/caveman-review` — single-line `L<line>: <severity> <problem>. <fix>.` comments) is the lowest-risk first commitment.

**Phase 2a — auto-clarity rule as a load-bearing carve-out (DEC-0032 + SAFETY.md).** caveman's auto-clarity rule
(temporarily drop to normal prose for security warnings, irreversible-action confirmations, multi-step sequences with
ambiguity risk, and user-confused / question-repeated states) is the discipline that prevents compression from
corrupting correctness. The Linus equivalent is the **explicit cap-bypass-audit-log** rule from DEC-0032: the bypass
exists, it is invoked under specific conditions, and the invocation is logged. The caveman list of trigger conditions
is directly portable as the v0 trigger-condition set for the Linus equivalent of "Worker drops the terse output rider
because doing so would corrupt correctness." This should land as a one-paragraph addition to the Phase 2a Worker spec
when `output_style` is added; the trigger conditions become a small enum the Worker can return alongside its output to
explain why it bypassed the configured style.

**Phase 2a — `memory_file_compress` as a Phase 2a startup-budget optimization (DEC-0032 + DEC-0030).** caveman-compress
rewrites long memory files (CLAUDE.md, project notes) into caveman style at install time, cutting **~46% input-token
cost on every subsequent session start** while preserving code blocks, URLs, file paths, and shell commands. Linus's
CLAUDE.md is already substantial (the file itself approaches 700 lines of dense prose); it is loaded into every Maestro
session and every Worker invocation that needs the project context. A Phase 2a startup-budget optimization could apply
the caveman-compress transformation to a derived `CLAUDE.compact.md` file that Linus's dispatcher selects when the
calling Worker's `output_style` is `terse` or `caveman`, while the prose-first canonical `CLAUDE.md` remains the human
reference. Cost: a one-shot Maestro pass to produce the compact variant, plus a regeneration rule when the canonical
file changes meaningfully. Upside: a measurable per-invocation input-token reduction across the entire Linus operating
surface. The caveman-compress preservation rules (headings, code blocks, URLs, paths, commands all byte-identical) are
also the right baseline for what a Linus-side compressor must preserve.

**Phase 3 — `caveman-shrink`-style MCP middleware as a Phase 3 in-house MCP-tool-description compressor (DEC-0018,
DEC-0045).** Letta exposes ~12 MCP tools per its repo-note; agentmemory exposes 51; the in-house Linus MCP surface
(per DEC-0045 fastmcp default; per the Letta repo-note's Open Question 2 the right pole is the ~12-tool middle ground)
will land somewhere comparable. Tool descriptions are input tokens injected at every invocation. caveman-shrink is the
worked example of an MCP middleware that compresses tool descriptions transparently; a fastmcp-built equivalent for
Linus's own in-house MCP servers is a Phase 3 candidate optimization. Cost is one middleware crate; upside is a
sustained per-invocation input-token reduction proportional to the size of the registered tool surface.

**Phase 5+ — output-style as a per-harness compatibility surface for openclaw / claw-code-local / Cline.** Once Linus's
`/v1/chat/completions` endpoint is up (Phase 2a per DEC-0005), the `output_style` field becomes a Linus-specific
extension that openclaw, claw-code-local, and Cline can pass through to influence Worker behavior. caveman's evidence
that the same skill installs cleanly across 30+ harnesses is a confirming signal that "output style is a per-call knob,
not a per-harness commitment" is the right protocol shape. The Linus dispatch struct already encodes per-call knobs
(`memory_mode`, `cot_budget` per DEC-0031); `output_style` joins them at Phase 2a.

**Methodology — three-arm eval discipline (skill vs. terse vs. baseline) for Phase 1c benchmark suite.** The caveman
eval harness's discipline rule — measure the skill against a plain "answer concisely" baseline, not against the verbose
default, to prevent conflating the skill with generic terseness — is directly applicable to Linus's Phase 1c+ Worker
benchmarks (DEC-0034 worker-size vs. CoT-length comparison; DEC-0035 ARC-AGI as memory diagnostic). When a Linus Worker
prompt or skill is benchmarked, the comparison arm matters: a `caveman`-styled Worker should be measured against a
plain-`terse`-styled Worker, not against an unmodified verbose Worker. The three-arm pattern is also a useful
discipline for measuring future Worker output-style variants against each other (e.g., `caveman-style-A` vs.
`caveman-style-B` vs. `terse-baseline`).

**Empirical anchor — the brevity-improves-accuracy paper (March 2026, arXiv 2604.00025).** The caveman README cites
this paper, which finds that constraining large models to brief responses **improved accuracy by 26 points on certain
benchmarks**. This is a candidate Phase 1 paper to add to `context/papers/` for the Linus corpus, alongside the
Lost-in-the-Middle and Toolformer adds flagged in the Letta-MemGPT paper-note's Open Question 7. If brevity is
correlated with correctness for the specific Worker tasks Dan cares about (code review, structured QA, gene-name list
extraction), then `output_style: caveman` is not just a cost optimization — it is a quality optimization too. The Phase
1c spike should measure both effects.

## 4. What's inspiration only

The **30+-agent install matrix** is caveman's primary distribution surface but is not directly applicable to Linus.
Linus does not need to detect Cursor / Windsurf / Cline / Copilot / Junie / Trae / Warp / Tabnine / Mistral / Qwen /
Devin / Droid / ForgeCode / Bob / Crush / iFlow / OpenHands / Qoder / Rovo Dev / Replit / Antigravity on the user's
machine; Linus is single-user and the Maestro/Worker boundary is already drawn around a small set of harnesses (Claude
Code, openclaw, claw-code-local, Cline) per CLAUDE.md and the [g7-harnesses synthesis](../syntheses/repo-clusters/g7-harnesses.md).
The unified-installer `PROVIDERS` array is a useful design reference for what a Linus-side per-harness install matrix
would look like if Linus ever ships its own first-party skills package; it is not content to lift in Phase 2/3.

The **PowerShell shim** and the **Windows-quoting bug history** (cited in the repo's CLAUDE.md as the reason for the
`bin/install.js` unification) are Windows-specific. Linus is macOS-targeted; the Windows-portability discipline does
not carry over.

The **statusline badge** mechanism (`[CAVEMAN] ⛏ 12.4k`) is a Claude-Code-statusline UX touch. Linus has no equivalent
statusline surface — openclaw is the planned Phase 5 front-end and exposes its own status UI. Useful as a design
reference for what a Linus-side per-session badge might look like in Phase 5+, but not content to lift now.

The **`cavecrew-*` subagent pattern** is a Haiku-shaped delegation model where the parent agent dispatches to a small
read-only or surgically-scoped child. Linus's Phase 3 spawner (DEC-0050, DEC-0051) is the proper home for the
parent-child delegation pattern; per the [goose repo-note](goose.md) §3 and the [Letta repo-note](Letta.md) §3, goose's
subagent execution shape and Letta's manager-taxonomy vocabulary are the design references the Phase 3 spawner spec
should crib from first. cavecrew's contribution is the **terseness discipline applied to subagent outputs**
(`path:line — symbol — note`) — a useful style guide for what a Linus `Role:investigator` should emit, but the
underlying machinery is already covered by the goose / Letta references.

The **OpenClaw integration** (the marker-fenced `<!-- caveman-begin --> ... <!-- caveman-end -->` block appended to
`~/.openclaw/workspace/SOUL.md` plus the workspace-skill frontmatter merge in `bin/lib/openclaw.js`) is interesting as
a worked example of how a per-session ruleset can be auto-injected into every turn via a workspace-level config file,
but Linus's Phase 5 openclaw integration will run through the orchestration-layer HTTP boundary, not through SOUL.md
injection. The `Respond terse like smart caveman` sentinel idempotency-key pattern is the only directly portable piece
— Linus's session-startup injection (Phase 2a session-store, per the workgraph JSONL convention in CLAUDE.md) should
similarly use a sentinel string for idempotent re-application.

The **`/caveman-stats` command** that reads Claude Code session logs to compute lifetime token savings is an interesting
UX artifact but not relevant to Linus's audit log (which is JSONL at `~/.linus/audit.jsonl` per ARCHITECTURE.md, not
Claude Code's session log shape).

## 5. What's incompatible or out of scope

**The unified-installer dependency on Node ≥18 and `npx skills` is a soft incompatibility with the Linus stack.** Linus
is Python-first (DEC-0027 multi-language stance); a Node-based installer would be acceptable as a build-time dependency
under the multi-language convention, but the upstream `vercel-labs/skills` registry that caveman's `npx skills add`
path depends on is an external service whose health and stability Linus would inherit. Direct vendoring of caveman's
installer is therefore the wrong shape; the Linus equivalent should be a Python-side rewrite that calls into the
relevant per-harness install paths directly (or, more likely at Linus's scale, no installer at all — Linus is single-
user and skills can be hand-installed once into each harness Dan uses).

**The 30+-agent install matrix scope is broader than the Linus orchestration layer should own (DEC-0017 harness
plurality, DEC-0020 orchestration scope is bounded).** Linus's orchestration backend is intentionally bounded: it
provides a `/v1/chat/completions` endpoint, an MCP host, a Worker spawner, a sandbox, a session store, and an audit
log. Cross-harness skill distribution is a separate concern that belongs upstream of Linus (in the harness or in a
third-party tool like caveman or `vercel-labs/skills`), not inside Linus.

**The skill is, fundamentally, a system-prompt rider.** Caveman's mechanism of action is to inject a system prompt that
tells the underlying LLM to respond in caveman style. There is no model fine-tuning, no decoder-side intervention, no
runtime token-budget enforcement — just a prompt that the model is asked to follow. This means the skill's quality is
bottlenecked by the underlying model's instruction-following reliability, which echoes the function-calling-reliability
constraint surfaced in the [MemGPT paper-note](../paper-notes/Letta-2310.08560.md) §"What's NOT applicable / hype
filter." For Linus's planned local Workers (Qwen3, future fine-tuned bases) on Dan's M1 Max 32 GB hardware, the Phase
1c worker-selection spike ([`phase1c-spike.md`](../specs/phase1c-spike.md)) should measure each Worker's
instruction-following reliability for output-style riders specifically, alongside the function-calling-reliability
property already named for the registry. A Worker that ignores or only partially follows a `caveman` rider would not
gain the token savings the pattern promises.

**The "caveman voice" is product brand, not Linus brand.** The repo's CLAUDE.md is explicit that the deliberately
broken-grammar voice ("Brain still big." / "Cost go down forever." / "One rock. That it.") is intentional brand
positioning. Linus has its own writing conventions (CLAUDE.md §Writing style for docs: "Prose over bullet-heavy dumps
for anything a human will read"; "Markdown files in this repo communicate reasoning, not just facts"). When the caveman
pattern is adapted into Linus, the **mechanism** (system-prompt rider that constrains output to fragments + the
auto-clarity carve-out) ports cleanly; the **voice** does not. Linus's `output_style: terse` should produce
grammatically-correct short prose, not caveman-grammar fragments. The `caveman` value of the field would be a separate
opt-in for users who want the actual caveman voice.

**MCP middleware as upstream of the registered server adds a moving part.** caveman-shrink wraps an MCP server in
transit, rewriting tool descriptions before they reach the agent. For Linus's in-house MCP servers, the cleaner shape
is to write terse tool descriptions in the first place inside the server source, not to add a middleware layer. The
middleware shape is genuinely useful only when wrapping **external** MCP servers whose descriptions Linus cannot edit;
for the Phase 3 in-house surface (per DEC-0045 fastmcp default), the right pattern is "write terse descriptions in the
server definition" and the middleware approach is over-engineered. Note caveman-shrink for the external-MCP-server
wrapping case; do not adopt it as the in-house-MCP-server convention.

**caveman's eval-harness tokenizer is OpenAI tiktoken, not Claude's actual tokenizer.** The repo's CLAUDE.md is honest
about this: "tiktoken — OpenAI BPE — approximates Claude tokenizer, ratios meaningful, absolute numbers approximate."
For Linus's Phase 1c+ benchmark suite, the same caveat applies — measurements made with tiktoken against Claude or
Qwen3 are directionally informative but not authoritative. The benchmark suite should record which tokenizer was used
and treat tiktoken-counted ratios as the primary comparison axis, not absolute token counts.

## 6. Recommendation: **Study + Adapt**

Read `skills/caveman/SKILL.md` and `skills/caveman-compress/SKILL.md` end-to-end as the source-of-truth statement of the
caveman style and the file-compression contract; read `src/hooks/caveman-mode-tracker.js` for the per-turn-reinforcement
pattern and the symlink-safe flag-write discipline in `caveman-config.js`'s `safeWriteFlag()`; read the README's
benchmarks table and the `evals/` three-arm harness for the empirical-measurement discipline. The Linus-applicable
contribution is the **pattern**, not the implementation: caveman is a worked example of "output-token-budget
compression as a first-class agent skill" with measurable cost savings (~65% output reduction) and a documented
correctness carve-out (auto-clarity rule). Adapt the pattern into Phase 2a as an `output_style` field on the Worker
spec (`verbose` / `default` / `terse` / `caveman`), with the dispatcher injecting the appropriate system-prompt rider,
the audit log recording the choice (per DEC-0031 audit-log discipline), and the auto-clarity-style bypass logged when
the Worker drops the configured style for correctness reasons.

The two specific adaptions worth committing to:

1. **`output_style` as a per-call Worker dispatch field**, alongside `memory_mode` and `cot_budget` (DEC-0031). The
   v0 vocabulary is `verbose` / `default` / `terse`. The `caveman` value is reserved for a Phase 5+ opt-in once the
   instruction-following-reliability measurement from Phase 1c lands. Worth a DEC alongside DEC-0031 or as a Phase 2a
   spawner-spec extension.

2. **Memory-file compaction for CLAUDE.md and other long startup files.** Apply a caveman-compress-style transformation
   (preserve code blocks, URLs, paths, commands; rewrite prose into fragments) to produce a `CLAUDE.compact.md`
   variant. The compact variant is the input for `output_style: terse` or `caveman` Worker invocations; the canonical
   `CLAUDE.md` remains the human reference. Regeneration is a Maestro task triggered when the canonical file's
   semantic content changes (not on every commit). Cost: one Maestro pass per material update. Upside: measurable
   input-token savings on every Worker invocation that uses the compact variant.

Do **not** vendor caveman. Do **not** adopt the unified installer or the 30+-agent install matrix. The cross-harness
distribution surface is upstream of Linus and outside the orchestration layer's scope (DEC-0020). The Node.js dependency
chain (Node ≥18, `npx skills`, `vercel-labs/skills` upstream registry) is heavier than the Linus skills surface needs
at Phase 2–3. Linus is single-user; per-harness install is a one-time hand operation, not a recurring distribution
concern.

Cluster cell: skills-and-practices. caveman is a skill, not a framework — it does not belong to any `g`-cluster
synthesis. Primary thematic home:
[skills-and-practices](../syntheses/skills-and-practices-synthesis.md). The pattern surfaces alongside the existing
encode-standards-in-files / verify-loop / agent-personas / context-routing threads as a new "output-budget compression
as a first-class skill" thread. Secondary thematic anchor:
[memory-synthesis](../syntheses/memory-synthesis.md) at the DEC-0032 in-context-window-cap-policy point — caveman
provides the output-side complement to the input-side cap, and the auto-clarity rule is the design pattern for
the explicit cap-bypass discipline.

## 7. Connections

The primary fold is into [`../syntheses/skills-and-practices-synthesis.md`](../syntheses/skills-and-practices-synthesis.md).
caveman extends the existing skill-discipline thread (Anthropic-internal Claude Code playbook, claude-code-guide,
Agent-Skills-for-Context-Engineering, superpowers) with a new sub-thread: **output-token-budget compression as a
first-class skill** with measurable cost savings and a documented correctness carve-out. The synthesis should fold the
pattern in alongside the existing verify-loop and context-routing threads, naming the `output_style` Worker dispatch
field as the Phase 2a operationalization candidate.

The secondary fold is into [`../syntheses/memory-synthesis.md`](../syntheses/memory-synthesis.md). DEC-0032 commits
Linus to a 16K input-token cap per Worker call with explicit cap-bypass audit logging; caveman is the closest worked
example of the output-side complement (a default-terse output rider with an auto-clarity bypass rule). The synthesis
should fold caveman in as the output-side reference for the same compression-with-explicit-bypass-discipline thread,
and the Phase 2a Worker spec should grow an `output_style` field alongside `memory_mode` and `cot_budget` (DEC-0031).

The tertiary cross-references:

- [`Letta.md`](Letta.md) §3 Open Question 2 names "what's the right pole on the minimal-to-comprehensive spectrum?" for
  Linus's Phase 3 MCP tool surface; caveman-shrink's MCP-middleware-as-description-compressor is the design reference
  for **input-token** efficiency on the chosen surface (independent of which pole is chosen), and the answer to "how
  many tools" couples to the answer to "how terse should each tool's description be."
- [`goose.md`](goose.md) §3 Open Question 4 names Anthropic-compatible HTTP / ACP as a Phase 5+ Linus capability
  candidate; caveman's 30+-harness install matrix is a confirming signal that "the protocol surface is plural" extends
  beyond Anthropic-vs-OpenAI to skill-distribution-surface plurality, but the Linus-side answer is to stay narrow at
  Phase 2 (DEC-0020 orchestration scope is bounded) and broaden at Phase 5+ when openclaw lands.
- The [`How-Anthropic-teams-use-Claude-Code_v2.pdf`](../../context/notes/How-Anthropic-teams-use-Claude-Code_v2.pdf)
  Anthropic-internal playbook treats the verify-loop as the primary mechanism for extending autonomous runtime;
  caveman's auto-clarity rule is a complementary correctness-preservation mechanism for the **output style** dimension
  the verify-loop does not address. Together they form the Phase 2a Worker spec's "compress aggressively, bypass under
  documented conditions" discipline.

Phase mapping: Phase 2a (`output_style` Worker dispatch field, `CLAUDE.compact.md` startup-budget optimization,
auto-clarity bypass discipline); Phase 3 (in-house MCP-server-description terseness convention, optional MCP-middleware
shape for external servers); Phase 5+ (per-harness `output_style` passthrough for openclaw / claw-code-local / Cline);
Phase 1c+ (three-arm eval discipline for output-style measurement). caveman surfaces as a **pattern to adapt**, not a
substrate to vendor — the implementation is Node-based and cross-harness-distribution-focused, neither of which fits
the Linus orchestration layer's Python-first, single-user, bounded-scope posture.

## 8. Open questions for Dan

1. **`output_style` as a Phase 2a Worker dispatch field.** Should the Phase 2a Worker spec absorb an `output_style`
   field (`verbose` / `default` / `terse`) alongside `memory_mode` and `cot_budget` (DEC-0031), with the dispatcher
   injecting the appropriate system-prompt rider and the audit log recording the choice? Tentative answer: yes — the
   pattern is well-established (the March 2026 brevity-constraints paper finds +26 accuracy points on certain
   benchmarks under brevity constraints), the cost is small (one extra field in the dispatch struct + one extra
   row in the audit log), and the downstream payoff is both cost (token savings) and quality (if the brevity-accuracy
   correlation holds on Dan's task suite). Worth a DEC alongside DEC-0031, or fold into a Phase 2a Worker-spec extension
   ADR.

2. **`caveman` as a reserved Phase 5+ `output_style` value vs. a v0 Phase 2a value.** Should the v0 `output_style`
   vocabulary include `caveman` from the start, or reserve it for Phase 5+ once the Phase 1c worker-selection spike
   measures instruction-following reliability for output-style riders specifically? Tentative answer: reserve. The
   `caveman` value depends on the Worker reliably following a multi-rule prompt rider (the SKILL.md is detailed); the
   safer v0 vocabulary is `verbose` / `default` / `terse`, with `caveman` added once Phase 1c data confirms a candidate
   Worker can follow the more-elaborate rule set without degradation.

3. **`CLAUDE.compact.md` as a Phase 2a startup-budget optimization.** Should Linus produce a caveman-compress-style
   `CLAUDE.compact.md` variant for use when the calling Worker's `output_style` is `terse`, with the canonical
   `CLAUDE.md` remaining the human reference and the compact variant regenerated when the canonical file changes
   meaningfully? Tentative answer: yes for Phase 2a — the input-token savings compound across every Worker invocation,
   and the regeneration cadence is manageable (a Maestro pass when the canonical file's semantic content changes, not
   on every commit). The discipline rule from caveman-compress (preserve headings / code blocks / URLs / paths /
   commands byte-identical) should be the Linus convention too.

4. **Auto-clarity bypass discipline as a Phase 2a Worker-spec extension.** caveman's auto-clarity rule (drop to normal
   prose for security warnings, irreversible actions, multi-step sequences with ambiguity risk, user-confused states)
   is the design pattern for "compress aggressively, bypass under documented conditions." Linus's DEC-0032 already
   commits to an explicit cap-bypass audit-log discipline for the **input**-side cap; should the symmetric **output**-
   side discipline (Worker drops the configured `output_style` rider under documented conditions) land in the Phase 2a
   Worker spec? Tentative answer: yes — the bypass trigger conditions become a small enum the Worker can return
   alongside its output, and the dispatcher logs the trigger in the audit log alongside the original `output_style`
   choice.

5. **The brevity-improves-accuracy paper (arXiv 2604.00025) as a Phase 1 corpus addition.** caveman cites this March
   2026 paper, which finds brevity constraints improve accuracy by 26 points on certain benchmarks. The paper is
   currently not in `context/papers/`. Should it be added as a Phase 1 corpus candidate (alongside the Lost-in-the-
   Middle and Toolformer adds flagged in the [Letta-MemGPT paper-note](../paper-notes/Letta-2310.08560.md) §Open
   Question 7)? Tentative answer: yes — the paper is directly load-bearing for the `output_style` ADR question above,
   and the result (brevity-improves-accuracy) is the strongest empirical anchor for the Phase 1c+ measurement plan.

6. **`caveman-shrink`-style MCP middleware as a Phase 3 in-house optimization.** caveman-shrink wraps an MCP server in
   transit, compressing tool descriptions before they reach the agent. For Linus's in-house Phase 3 MCP servers (per
   DEC-0045 fastmcp default), the cleaner shape is "write terse descriptions in the server source" rather than adding a
   middleware layer. But for the **external** MCP servers Linus may eventually consume (Phase 5+, per DEC-0046
   external-API tool-registry deployment field), the middleware shape is the right tool. Should the Phase 3 MCP host
   spec name caveman-shrink as a design reference for the external-server wrapping case, while the in-house servers
   commit to terse-descriptions-in-source? Tentative answer: yes; document the asymmetry in the Phase 3 MCP host spec.

7. **The three-arm eval-harness discipline for Phase 1c benchmarks.** caveman's eval harness measures skill-vs-terse
   (not skill-vs-baseline) as the honest delta, to avoid conflating the skill with generic conciseness. Should Linus's
   Phase 1c benchmark suite adopt the three-arm discipline (baseline / terse-prompt / styled-prompt) as the canonical
   measurement shape for any output-style or skill-prompt variant? Tentative answer: yes — the discipline is cheap
   (one extra arm per measurement) and the honesty payoff is substantial (no false positives from conflating skill with
   genericness). Worth committing to in the Phase 1c spike spec.

8. **Single-maintainer dependency posture.** caveman is a single-maintainer Node package (Julius Brussee) distributed
   primarily via curl-piped install scripts and `npx -y github:JuliusBrussee/caveman`. The supply-chain posture is
   weaker than DEC-0024 commits Linus to (hash-pinned `linus` conda env; experimental Python packages in disposable
   `uv` venvs). Even adopting caveman as a personal Claude Code skill on Dan's machine routes through a curl-piped
   install path; the pattern itself is fine to adopt, but the **artifact** should be cloned-and-inspected rather than
   curl-installed. Tentative answer: study the source in `repos/caveman/`, lift the patterns into Linus's own
   `output_style` and `CLAUDE.compact.md` machinery, and do not install caveman directly into Dan's Claude Code
   environment without a security review pass first.
