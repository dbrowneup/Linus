# local-whisper (`t2o2/local-whisper`)

## 1. Purpose and scope

LocalWhisper (t2o2/local-whisper; Swift + SPM; MIT; macOS menu-bar app) is a **fully local Apple-Silicon-optimized
speech-to-text app** for macOS. The user holds a global hotkey (default `Ctrl+Shift+Space`), speaks, releases the
hotkey, and the transcribed text is automatically typed into the focused application via the macOS Accessibility API.
Powered by [WhisperKit](https://github.com/argmaxinc/WhisperKit) (the Swift Whisper port with CoreML), the app uses
CoreML + Apple Neural Engine acceleration on Apple Silicon. **No internet required**; all processing is on-device; no
audio leaves the Mac. Models range from tiny to large-v3, selected via the menu-bar UI.

The project is a clean exemplar of Apple-Silicon-native ML application engineering: small Swift codebase, SPM-based
build (`swift build && swift run`), tight architecture with explicit actor-isolation for thread safety, dependency
injection via an `AppState` container, and four service classes (`AudioCaptureService`, `TranscriptionService`,
`TextInjectionService`, `PermissionsService`) plus a coordinator (`TranscriptionCoordinator`) that orchestrates the
hotkey → record → transcribe → inject workflow. macOS 14.0+ (Sonoma); Apple Silicon required (M1/M2/M3/M4); 8 GB RAM
minimum (16 GB+ for large models). Custom vocabulary support for technical terms, product names, proper nouns.

The repo's `CLAUDE.md` is brief and operationally precise — build commands (`swift build`, `swift run`, `swift build
-c release`, `open Package.swift`); architecture with actor isolation patterns; key files mapped to purposes;
common-task recipes (adding a setting, changing default shortcut, debugging transcription).

## 2. Architecture summary

**Core components:**

- **`AppState`** (`App/AppState.swift`) — global state container, holds all services. Uses `@MainActor` for UI-related
  code.
- **`TranscriptionCoordinator`** (`Coordinators/`) — orchestrates the workflow: hotkey → record → transcribe → inject.
- **Services (`Services/`):**
  - `AudioCaptureService` — AVAudioEngine-based 16 kHz mono recording.
  - `TranscriptionService` — WhisperKit wrapper.
  - `TextInjectionService` — AXUIElement API (Accessibility-API-based text injection) with clipboard fallback.
  - `PermissionsService` — macOS permission handling.

**Key patterns:**

- **Actor isolation:** Services use Swift actors for thread safety.
- **`@MainActor`:** UI-related code (AppState, Coordinator, Views).
- **Dependency injection:** Services configured via AppState.

**Key files:**

| File | Purpose |
|------|---------|
| `Package.swift` | SPM dependencies (WhisperKit, KeyboardShortcuts) |
| `App/AppDelegate.swift` | Menu bar setup, global shortcut registration |
| `Services/AudioCaptureService.swift` | Microphone recording in Whisper format |
| `Services/TranscriptionService.swift` | WhisperKit model loading and transcription |
| `Services/TextInjectionService.swift` | Inject text via Accessibility API |

**Dependencies:**

- **WhisperKit** (0.9.0+) — local Whisper transcription with CoreML.
- **KeyboardShortcuts** (2.0.0+) — global hotkey handling.

**Stack:** Swift / SPM, CoreML, Apple Neural Engine acceleration. Build via `swift build` (debug) or `swift build -c
release` (release). Open in Xcode via `open Package.swift`.

**Text injection model:** AXUIElement API for native apps; clipboard fallback for Electron apps (which don't expose
their text fields via AXUIElement reliably).

## 3. What's reusable in Linus

**The "100% offline, Apple-Silicon-native, ANE-accelerated" framing is exactly Linus's positioning.** This is the most
load-bearing structural match. LocalWhisper's three core commitments — fully local, Apple-Silicon-native, ANE-
accelerated — are the same three Linus commits to per CLAUDE.md ("Docker inference is forbidden — the macOS VM does not
pass through Metal or ANE. ML inference and training must run natively"). LocalWhisper is the **canonical worked
example** of a non-trivial Apple-Silicon-native ML app at small scale, and the closest existing template for
Phase 5+ Linus front-end app architecture (per DEC-0008 openclaw-frontend-native-app).

**WhisperKit as the STT primitive for Phase 5+ Linus.** WhisperKit is the **right** STT primitive for Linus's
Phase 5+ voice input. Two independent Linus-relevant choices: MFLUX for image generation, WhisperKit for speech-to-
text. Both are Apple-Silicon-native, both use CoreML, both run on the ANE. LocalWhisper is the worked example of
WhisperKit integration; for Phase 5+ Linus voice input, the same primitive should be adopted. The Phase 5 spec should
reference LocalWhisper as the integration reference.

**Actor-isolation pattern as a concurrency primitive.** Swift's actor system provides compile-time-checked thread
safety. For Linus's Phase 5+ native app (if openclaw-as-frontend graduates to native, per DEC-0021), the same actor
pattern is portable. Even if the native app ends up in TypeScript or Rust rather than Swift, the **discipline** —
explicit actor isolation for shared state, `@MainActor` for UI code — is a portable engineering convention.

**AXUIElement-with-clipboard-fallback text injection pattern.** This is a Phase 5+ Linus pattern for any "agent that
writes text into another app" use case. The AXUIElement API works for native macOS apps; clipboard fallback handles
Electron apps. For Linus Workers that need to inject output into VS Code (Electron) or terminal (native), the same
fallback discipline applies.

**KeyboardShortcuts library for global hotkeys.** For Phase 5+ Linus app integration, global hotkeys are likely (e.g.,
"Cmd+Shift+L" to invoke a Linus Worker on the current selection). KeyboardShortcuts is the standard Swift library;
LocalWhisper's integration is a reference.

**Custom vocabulary as a Worker-tuning pattern.** LocalWhisper's custom vocabulary feature (add words/names for
accurate transcription of technical terms) is the same shape as Linus's BioReason-Pro-style typed-structured-prediction
output: tell the model what classes/entities exist, get back better outputs. For Phase 7+ biology Workers,
domain-specific vocabulary lists (gene names, protein names, organism names) should be pre-loaded into the Worker's
context (or fine-tuning) similarly.

**Small Swift codebase as a Phase 5+ template.** The LocalWhisper codebase is small — ~10-15 Swift files, ~3-5k LOC.
For Phase 5+ Linus native-app development, this is the right scale (versus, e.g., openclaw's larger TypeScript codebase
or Vellum's 12-subdirectory monorepo). A Phase 5+ Linus native app for "voice-driven Worker invocation" could fit in a
similar codebase footprint.

## 4. What's inspiration only

**Swift / SPM stack is incompatible with the Linus Python core.** Linus's orchestration layer is Python; LocalWhisper
is Swift. The patterns (actor isolation, dependency injection, AXUIElement integration) are portable; the codebase is
not. A Phase 5+ Linus native app might be written in Swift (following LocalWhisper as template) or in another stack;
that's a Phase 5+ decision.

**No multi-model routing.** LocalWhisper supports model selection (tiny → large-v3) but treats each as a single STT
choice. Linus's Phase 2 router (per DEC-0031, DEC-0033, DEC-0034) is multi-model with cot_budget and memory_mode
routing. The single-purpose STT app doesn't benefit from multi-model routing; the Linus pattern is broader.

**No first-class Linus orchestration backend integration.** LocalWhisper is a standalone STT app, not a Linus client.
For Phase 5+ Linus voice input, a custom integration is required — either LocalWhisper extended with a HTTP POST to a
Linus endpoint, or a custom Linus voice-input app that reuses WhisperKit at the Worker level.

**macOS-only.** LocalWhisper targets macOS 14.0+ on Apple Silicon. Linus's broader scope per ROADMAP.md Phase 8 ("Beyond
MacBook") includes mobile, Mac Studio, native app, Vision Pro. LocalWhisper's macOS-only scope is correct for its
target; Linus's broader scope means Phase 5+ apps may target multiple platforms.

## 5. What's incompatible or out of scope

**No Linus-specific tooling.** LocalWhisper is a general-purpose STT app, not a Linus Worker. Integration requires
custom development.

**No multi-user / multi-account model.** LocalWhisper assumes a single user on a single Mac. Linus's single-user (Dan)
scope is the same; not an issue, but no multi-user primitive.

**No long-running session model.** LocalWhisper is hotkey-triggered for short utterances. Linus's Phase 2/3 sessions
are long-running (Worker dispatch, multi-agent investigations). The transient hotkey model doesn't map onto Linus's
session model.

**No audit log.** LocalWhisper transcribes locally and types into the focused app; no audit log is generated. Linus's
DEC-0030 commitment to durable scratchpad and audit logging would require an extension if LocalWhisper is integrated.

**Single Swift dependency tree.** WhisperKit + KeyboardShortcuts is the entire dependency surface. For a Phase 5+
Linus native app reusing this stack, that's fine; for a richer Linus client (with networking, MCP integration, etc.),
the dependency surface grows substantially.

## 6. Recommendation: **Adapt**

LocalWhisper is the **canonical Apple-Silicon-native Linus reference app** for Phase 5+ frontend work. The combination —
WhisperKit + KeyboardShortcuts + actor isolation + AXUIElement injection + tiny Swift codebase — is precisely the right
template for a Phase 5+ Linus voice-input or hotkey-triggered-Worker-invocation app. The Adapt recommendation says:
when Phase 5+ Linus voice input or hotkey-Worker-invocation is scoped, **start by forking LocalWhisper** and adapting
the codebase to invoke a Linus Worker (via HTTP POST to the Phase 2a backend) instead of writing transcribed text to
the focused app. The architecture pattern carries over; the specific functionality changes from "transcribe to text"
to "transcribe to Worker invocation."

The closest precedent: openclaw (per [`openclaw.md`](openclaw.md)) is the Phase 5+ TypeScript/Electron front-end target
per DEC-0008. LocalWhisper is the Phase 5+ Swift/native template for any **hotkey-triggered** integration. The two
serve different Phase 5+ use cases — openclaw for sustained authoring/coding workflows, LocalWhisper-style apps for
quick-invoke utility flows. Both are reusable; LocalWhisper is the smaller, cleaner template.

## 7. Questions for Dan

1. **WhisperKit as the Phase 5+ STT primitive — commit?** This is a small decision but worth surfacing: when voice
   input becomes a Phase 5+ feature, WhisperKit is the default choice. Worth committing to in a Phase 5+ spec?

2. **LocalWhisper as the Phase 5+ Adapt template.** When hotkey-triggered Worker invocation is scoped (Phase 5+),
   forking LocalWhisper and adapting it is the recommended path. Worth flagging in the Phase 5 spec?

3. **Custom vocabulary lists for Phase 7+ biology Workers.** Domain-specific term lists (gene names, organism names,
   protein families) loaded into Worker context could meaningfully improve typed-structured-prediction accuracy. The
   LocalWhisper custom-vocabulary pattern is suggestive. Worth a Phase 7 spec inclusion?

4. **AXUIElement integration as a Phase 5+ orchestration primitive.** Linus Workers may need to inject output into
   other apps (VS Code, terminal, Slack desktop). The AXUIElement-with-clipboard-fallback pattern is portable. Worth
   a Phase 5+ orchestration-primitive spec inclusion?

5. **Actor-isolation discipline.** For any Phase 5+ Linus native code (Swift or otherwise), the actor-isolation
   discipline (explicit thread-safety boundaries, `@MainActor` for UI) is a portable engineering convention. Worth
   surfacing in CLAUDE.md's engineering conventions section?

6. **WhisperKit + Linus voice-input integration as a Phase 5+ deliverable.** Worth a Phase 5 spec line item — "WhisperKit-
   based voice input for Linus Worker invocation, modeled on LocalWhisper" — as a scoped deliverable?
