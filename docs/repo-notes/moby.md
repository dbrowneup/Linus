# moby (`moby/moby`)

## 1. Purpose and scope

Moby (`moby/moby`; Go; Apache-2.0; the upstream of Docker Engine) is the open-source "Lego set" of container-system
toolkit components originally extracted from Docker in 2017. The root module `github.com/moby/moby/v2` produces
binaries — chiefly `dockerd` — and is explicitly **not** intended to be imported as a Go library; the public consumable
surface is two independently-versioned Go modules under the same repo: `github.com/moby/moby/client` (the Engine API
client) and `github.com/moby/moby/api` (shared API types). Starting with Docker v29 (November 2025), the old
`github.com/docker/docker` module is deprecated, and downstream consumers are expected to migrate import paths to the
`moby/moby` namespace.

The project bills itself as **modular, batteries-included-but-swappable, usable-security-by-default, developer-focused**
(README). The ROADMAP makes its current direction explicit: continued **decoupling** of the daemon, pushing duplicated
container-lifecycle work down into `containerd`, swapping the legacy "v0" builder for **BuildKit**, supporting
**rootless mode**, and migrating the legacy `integration-cli` test suite into the simpler `integration` API-test suite.
gRPC is named in the ROADMAP as the "natural communication layer between decoupled components."

Moby is the substrate Docker Engine, Mirantis Container Runtime, and various downstream container engines are built
from. It is **not** for end users seeking a commercially-supported product, and it explicitly disclaims being a
support/feature-request venue for Docker products.

## 2. Architecture summary

**Top-level layout.** Major subsystems live in `daemon/` (172 files at top level; the largest single subtree),
`client/` (Engine API Go client), `api/` (Swagger-defined API types plus generator), `cmd/dockerd/` (the daemon entry
point) and `cmd/docker-proxy/`, `pkg/` (utility libraries not specific to Moby internals), `internal/` (internal-only
helpers), `contrib/` (init scripts, package recipes, OS integration), `hack/` (build/test scripts), and `vendor/`
(vendored dependencies).

**Daemon as the central object.** The `Daemon` object lives in `daemon/daemon.go` and is named in the ROADMAP as the
top refactor target — "should be split into smaller, more manageable, and more testable components." Around it sit
specialized subdirectories: `daemon/builder/` (build orchestration including BuildKit + legacy dockerfile),
`daemon/cluster/` (Swarm-mode cluster management with `executor`, `controllers`, `provider`, `convert`),
`daemon/container/` (container lifecycle, exec, monitor, state, mounts, rwlayer, store),
`daemon/containerd/` (containerd-backed image and snapshot management — pull, push, prune, commit, history, tag, save,
load, leases, store), and `daemon/cluster/internal/` plus per-feature files for `apparmor`, `seccomp`, `exec`,
`checkpoint`, `cdi`, `commit`, `attach`, `auth`, `configs`, `cluster`.

**Two-layer runtime delegation.** The daemon no longer directly manages low-level container lifecycle; it talks to
`containerd` (vendored at `github.com/containerd/containerd/v2 v2.2.3` per `go.mod`), which in turn invokes OCI
runtimes — typically `runc` — via the OCI runtime spec (`github.com/opencontainers/runtime-spec v1.3.0`). Moby retains
opinion on **networking**, **volumes**, **image build orchestration**, **swarm cluster mode**, and the **HTTP/gRPC
API surface** that clients consume.

**API surface.** The `api/` module ships a Swagger spec (`swagger.yaml`) plus generated types, regenerated via the
`swagger-gen.yaml` config. The `client/` module is a hand-written Go HTTP client over that API — file naming mirrors
the API resource taxonomy (`container_*.go`, `image_*.go`, `network_*.go`, `volume_*.go`, `service_*.go`,
`checkpoint_*.go`, `secret_*.go`, etc.). Every resource has paired `*_test.go` and `*_example_test.go` files. The HTTP
client is the public Go SDK for the Engine API.

**Authorization plugin substrate.** `pkg/authorization/` defines a small plugin-based authz middleware (`api.go`,
`middleware.go`, `plugin.go`) that gates daemon requests against external authz plugins via HTTP. This is the
production-proven pattern for daemon-side policy enforcement at the request boundary.

**Sandbox/isolation primitives.** Linux-only files in `daemon/` handle the kernel-level sandboxing surface that Linus
does not need but is worth knowing exists: `apparmor_linux.go` / `apparmor_default.go` (AppArmor profile generation
and loading), `seccomp_linux.go` (seccomp BPF filter loading), and per-platform `container_operations_unix.go` /
`container_operations_windows.go` (namespace + cgroup setup at container start). These are tightly coupled to the
Linux kernel namespaces/cgroups model and to OCI runtime spec.

## 3. What's reusable in Linus

The honest answer is **little in code**, **some in architectural reference**. Linus runs on macOS / Apple Silicon
without Docker for ML inference (CLAUDE.md is unambiguous: "Docker inference is forbidden — the macOS VM does not pass
through Metal or ANE"). Moby is Go, Linux-first, kernel-namespace-coupled; Linus is Python-orchestration on macOS
unified memory. Direct code lift is not on the table. But Moby is the **canonical reference implementation** for two
patterns Linus needs to think hard about in later phases.

**Daemon-as-server architectural reference for the Linus orchestration backend.** Moby's daemon-plus-HTTP-client split
(daemon binary `dockerd` exposing a versioned REST API consumed by an explicitly-decoupled Go client module) is the
clearest open-source example of the shape Linus is building toward in Phase 2a — an orchestration backend that exposes
an OpenAI-compatible HTTP endpoint to interchangeable front-ends (VS Code, openclaw, LM Studio, future native). The
**versioned API + separate client module + Swagger-generated types** pattern is worth lifting as a target shape for
Linus's OpenAI-compat surface, including the discipline of treating the client module as having its own semver and
release cadence independent of the daemon binary. DEC-0005 (OpenAI-compat) is the Linus-side commitment; Moby is the
reference for how to operationalize "the daemon is the product, the client SDK is its public face."

**Authorization-plugin middleware as Phase 7 sandboxing reference.** `pkg/authorization/` (small, focused: ~10 files,
plugin discovery + request/response middleware + HTTP plugin protocol) is a directly-readable production-proven
pattern for a daemon that wants to gate operations against external policy plugins. For Linus's Phase 7 widening
sandbox graduation and the R2-15 Worker-sandboxing question, the Moby authz-plugin shape is **the** open-source
precedent worth studying: HTTP-plugin protocol, request-time and response-time hooks, opt-in registration, plugin
isolation. Linus would not vendor this code (Go vs Python; HTTP-plugin protocol is OS-specific), but the **shape** —
authz as middleware around a daemon, plugins as out-of-process HTTP services, request- and response-side hooks — maps
cleanly onto the SAFETY.md tier graduation.

**ROADMAP discipline as a planning artifact.** The Moby ROADMAP is short, links to tracking issues, names specific
refactor targets (`Daemon` object split, BuildKit integration, containerd image migration, rootless mode,
integration-cli → integration), and explicitly invites contributions in unlisted areas. The Linus ROADMAP.md is
already in this shape; the Moby document is a useful comparable to grep against during quarterly curation (DEC-0025)
when the Linus ROADMAP is reviewed for whether items still earn their keep.

**containerd / runc / OCI spec as study references for Phase 3+ Worker process isolation.** Moby's `vendor/` carries
containerd v2.2.3, containerd's `nri` (Node Resource Interface), `go-runc`, and the OCI runtime/image specs. If
Linus's Phase 3 multi-agent spawner (DEC-0050) ever needs strong per-Worker process isolation — beyond Python
subprocess + `uv venv` (DEC-0024) — `containerd` is the production-proven reference architecture for "lightweight
process runtime with image/snapshot management and a clean RPC surface." On macOS this would not run Workers in
containers (Metal/ANE forbidden); it would inform the **API shape** of a hypothetical Linus Worker-runtime daemon if
isolation needs ever escalate.

## 4. What's inspiration only

**Modular swappable-component philosophy.** "Batteries included but swappable" maps directly onto the Linus
front-ends-are-interchangeable, KnowledgeBase-is-a-submodule, fastmcp-is-the-tool-substrate posture. Moby is the
mature instance of the philosophy. Linus inherits the principle, not the code.

**Swagger-first API definition.** Moby defines the Engine API in `swagger.yaml` and generates types from it. For
Linus's OpenAI-compat surface (DEC-0005) and any internal MCP-server APIs (DEC-0045), schema-first definition is the
right discipline; fastmcp's decorator API already provides this. Moby is the comparable rather than the source.

**Move-features-to-experimental-channel-first cadence.** The ROADMAP describes promoting new Dockerfile syntax through
`docker/dockerfile:experimental` → `docker/dockerfile:latest` → binary release. This **release-channel discipline** is
worth keeping in mind as Linus accumulates skills and Workers — graduating a Worker model from `experimental` to
`default` should require similar gating. Inspirational only; no code shared.

## 5. What's incompatible or out of scope

**Go-language codebase.** Linus's core orchestration is Python (`pyproject.toml`, `src/linus/`). Components in Rust
(pmetal, claw-code) and JS (openclaw) are accepted per DEC-0027 multi-language stance, but Go is not currently in the
mix and adding it to maintain a Moby-derived component is not a cost the project should pay. Read-only code reference
only.

**Linux-kernel-coupled.** Moby's daemon, by design, depends on Linux namespaces, cgroups (v1 and v2), seccomp BPF,
AppArmor, and the OCI runtime spec. On macOS these are simulated by Docker Desktop's Linux VM. Linus runs natively on
macOS and explicitly forbids the macOS Docker VM for ML workloads. None of the sandboxing-relevant Moby code is
directly portable.

**Docker for ML inference is forbidden in Linus (CLAUDE.md).** This is the load-bearing constraint. Moby cannot host
Linus inference Workers, cannot host pmetal, cannot host MLX. Any reading of Moby that imagines containerizing the
Linus inference path is reading the wrong constraint. The macOS VM that Docker Desktop runs is opaque to Metal and ANE
and would erase the entire Apple-Silicon performance story.

**Massive codebase, narrow lift surface.** The repo is 254 MiB cloned. The Go module surface alone is ~172 files in
`daemon/` plus comparably-sized subtrees in `client/`, `pkg/`, `api/`. Even with Go's good test culture, **selectively
extracting** a pattern (e.g., the authz middleware) is a substantial reading exercise that returns small concrete
Linus-applicable artifacts. The `pkg/authorization/` subtree is the only narrow target worth a directed read; the rest
is too entangled with daemon internals to mine economically.

**Apache-2.0 license is compatible, but vendoring is the wrong shape.** License permits incorporation; architecture
forbids it. The right relationship is **read for patterns, do not vendor**.

## 6. Recommendation: **Watch**

Moby is the canonical container-engine reference but it sits behind two hard constraints that block direct
contribution to Linus: Linux-kernel coupling and the Docker-for-ML-inference prohibition. The codebase is too large to
mine opportunistically; the language (Go) does not align with the Linus core. The right posture is **Watch with a
single directed read on `pkg/authorization/`** when Phase 7 Worker-sandboxing reaches design time (R2-15) — the authz-
middleware shape is the most directly-usable architectural reference and is small enough to absorb in a focused
session. Until then, Moby earns no further Linus attention. This is a **Watch**, not a **Study**: there is no
near-term action item, only a flagged reference subtree for a future phase.

The contrast with the **Study** verdict on lighter-weight harnesses (swarms, workgraph) is instructive — those have
patterns Linus can lift in Phase 2-3. Moby's patterns are Phase 7+ at earliest and likely deferred indefinitely if
`uv venv` + subprocess isolation prove sufficient for the Worker model.

## 7. Questions for Dan

1. **Phase 7 Worker-sandboxing reference target.** When the R2-15 Worker-sandboxing decision lands at Phase 7 design
   time, is `pkg/authorization/` worth a directed 1-2 hour reading session as the open-source authz-middleware
   reference, or is the planned Python `uv venv` + subprocess approach (DEC-0024 extended) already sufficient and Moby
   stays purely observational?

2. **Versioned-client-module separation for the Linus OpenAI-compat surface.** Moby's `client/` is an independently
   versioned Go module separate from the daemon binary, with its own semver and release cadence. For Linus's Phase 2a
   orchestration backend, should the OpenAI-compat client (the part front-ends import) be similarly factored into a
   separately-versioned `src/linus/client/` package with independent semver, anticipating that VS Code / openclaw /
   future native UIs will pin different versions?

3. **Swagger-or-equivalent API spec for the Linus orchestration HTTP surface.** Moby maintains the Engine API in
   `swagger.yaml` and generates types from it. fastmcp gives Linus this for MCP servers via decorators, but the
   OpenAI-compat HTTP surface (DEC-0005) does not yet have a single source of truth. Worth adopting an
   OpenAPI/Swagger spec at the Phase 2a boundary, or is OpenAI's published spec the canonical source we mirror?

4. **`containerd` as a future Worker-runtime reference, conditional on the macOS-Metal constraint relaxing.** If a
   future Linus phase ever runs on Mac Studio + Linux GPU node, `containerd` becomes a real candidate for Worker
   isolation. Is that a Phase 8 ("Beyond MacBook") consideration worth pinning now in the roadmap, or is it premature
   given the M1 Max single-host scope through Phase 7?
