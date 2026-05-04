# openclaw (`openclaw/openclaw`)

## 1. Purpose and scope

openclaw is a polished, feature-rich **personal AI assistant platform** — a local-first Node.js Gateway that speaks to
20+ messaging channels (WhatsApp, Telegram, Slack, Discord, Signal, iMessage, Matrix…), runs voice wake and continuous
voice on macOS/iOS/Android, renders a live Canvas the agent can control, supports a plugin/skill ecosystem via
`SKILL.md` files, and provides a macOS menu bar app plus iOS/Android companion nodes. It was "built for Molty, a space
lobster AI assistant." Sponsored by OpenAI, GitHub, NVIDIA, Vercel, and others. For Linus, openclaw is the intended
Phase 5 _front-end_ — not a framework to extend, but a polished UI pointed at Linus's OpenAI- compatible endpoint.

## 2. Architecture summary

Node 22+/24 TypeScript monorepo (pnpm, with Bun as an alternative), structured around a local "Gateway" control plane at
port 18789. Core engine in `src/` plus `ui/` and `packages/`; bundled plugins in `extensions/` (per-channel
integrations: Telegram, WhatsApp, Slack, etc.). Architectural boundaries are enforced: core is extension- agnostic, and
plugins cross into core only via the public `openclaw/plugin-sdk/*` seams. Multi-agent routing maps inbound channels to
isolated agents with their own workspaces and sessions; tools run on the host for the `main` session and in Docker/SSH/
OpenShell sandboxes for non-main sessions. macOS/iOS/Android companion apps are optional and pair over the Gateway
WebSocket. Configuration lives in `~/.openclaw/openclaw.json` and `~/.openclaw/workspace/`. ClawHub (`clawhub.ai`) is a
skills registry. OAuth subscriptions to OpenAI and similar are supported; the README specifically recommends "a current
flagship model from the provider you trust," which will mean Linus's OpenAI-compatible endpoint once Phase 5 arrives.

## 3. What's reusable in Linus

openclaw as a drop-in Phase 5 UI is the plan already. Voice wake (macOS/iOS), continuous voice (Android), live Canvas,
menu bar control, iOS/Android companion nodes — Linus gets all of this for free by pointing openclaw's model config at
Linus's endpoint. The `SKILL.md` convention is the same one Anthropic established and that Linus's Phase 7 adopts; any
skill written for one works in the other. The "Gateway at port 18789 + companion apps over WebSocket" pattern is a
useful reference for any Phase 8 native-Linus-app architecture, even if Linus doesn't actually reuse openclaw's code.

## 4. What's inspiration only

The _breadth_ of channel integrations (20+) is a reminder that Linus intentionally scopes much smaller — Linus does not
aim to be a WhatsApp/Slack/Discord assistant. The sponsor/community model (OpenAI, Vercel, Discord, regular release
cadence) is what openclaw is; Linus is a personal project with no such ambitions. The architectural discipline visible
in `AGENTS.md` (extension-agnostic core, public plugin SDK, contracts over internals) is a sound engineering pattern
Linus can borrow when its own plugin story starts to matter in Phase 7.

## 5. What's incompatible or out of scope

Scope, mostly. Linus does not need WhatsApp, Telegram, Slack, Signal, iMessage, IRC, Matrix, Feishu, LINE, Mattermost,
or Nostr — none of them serve Dan's genomics/biochem workflow. Running the full openclaw Gateway means carrying those
channels whether used or not. openclaw's model is subscription-friendly (OAuth to OpenAI/Anthropic); Linus's is
local-model-first. There may be small friction getting openclaw to treat a local Linus endpoint as "first-class" in
preference to the configured flagship models. And openclaw is a large active project — version pinning will matter to
avoid breakage from upstream churn (README's own advice: "pin a known-good openclaw version; track upstream for
security-relevant updates").

## 6. Recommendation: **Integrate (as Phase 5 front-end, pinned)**

Do not build on openclaw or vendor any of its code. Do install it in Phase 5, point it at Linus's `/v1/chat/completions`
endpoint as the configured model provider, and use it as the polished UI for chat/voice/Canvas. Pin a specific version
and upgrade manually. Keep Linus's skills under `src/linus/skills/*/SKILL.md` and symlink or mount them into openclaw's
`~/.openclaw/workspace/skills/` so the same skills surface in both. Stay out of openclaw's channel configuration beyond
"macOS + WebChat" unless Dan actually wants Telegram/Slack/etc.

## 7. Questions for Dan

- **Which openclaw surfaces actually matter?** Full channel sprawl isn't the goal. A reasonable minimum is macOS menu
  bar + voice wake + Canvas + WebChat; iOS node if you want phone access. Am I reading your priorities right, or do you
  want any specific messenger channel wired up?
- **Voice wake as a Phase 5 feature.** openclaw supports macOS/iOS voice wake and Android continuous voice. Is voice a
  Phase 5 requirement, or defer to Phase 8 native app? Voice changes the usability story substantially.
- **Canvas as a KnowledgeBase surface.** openclaw's Canvas is agent-driven visual workspace. Plausible Phase 5
  experiment: have Linus render paper clusters, cluster labels, or knowledge-graph subgraphs in Canvas. Is that the kind
  of interaction you want, or is text/Streamlit sufficient?
- **Skill symlink strategy.** Keeping Linus skills in `src/linus/ skills/` and symlinking into openclaw's workspace is
  one option; copying is another; putting skills only in openclaw and having Linus read from openclaw's workspace is a
  third. Preference?
- **Private-API / local-model first-class support.** openclaw's model config assumes a subscription. Confirming it works
  cleanly against an OpenAI-compat local endpoint with no rate-limit drama is a Phase 5 smoke-test worth budgeting for.
