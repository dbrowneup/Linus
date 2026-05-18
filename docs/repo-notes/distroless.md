# distroless (`GoogleContainerTools/distroless`)

## 1. Purpose and scope

Distroless (GoogleContainerTools/distroless; Bazel/Starlark; Apache-2.0) builds minimal container base images that
contain only an application and its strict runtime dependencies — no package manager, no shell, no busybox, no anything
else you would expect to find in a standard Linux distribution. The published image family covers a `static` rung
(2 MiB; ca-certificates + `/etc/passwd` + `/tmp` + tzdata; targets statically-compiled Go/Rust), a `base-nossl` rung
(adds glibc), a `base` rung (adds libssl), a `cc` rung (adds C++ runtime), and language-specific rungs for
`python3-debian13` (Python 3.13), `nodejs{22,24,26}-debian13`, and `java{17,21,25}-debian13`. Each rung is published in
`latest`, `nonroot`, `debug`, and `debug-nonroot` variants across amd64, arm64, arm, s390x, ppc64le, and (for several
rungs) riscv64. The smallest image (`static-debian13`) is ~2 MiB versus ~5 MiB for alpine and ~124 MiB for stock
debian.

The build system is Bazel + `rules_oci` + `rules_distroless`, with a small set of `.bzl` config files per language
(`base/config.bzl`, `python3/config.bzl`, etc.) enumerating per-distro package lists, supported architectures, and
runtime flavors. Debian 13 (trixie) is the current base; the project tracks upstream Debian security updates via a
GitHub Action that auto-files PRs against `private/repos/deb`. All published images are cosign-signed with ephemeral
keyless certificates and verifiable via the Google OIDC issuer. Major downstream users named in the README include
Kubernetes (since v1.15), Knative, Tekton, Teleport, and SpecterOps's BloodHound.

## 2. Architecture summary

**Layered base-image hierarchy.** Each language rung inherits from a lower rung — `python3` and `cc` inherit `base`'s
glibc + libssl; `nodejs` inherits from `cc`; `base` itself inherits from `static`. Adding a language is a thin
declarative layer on top of the same minimal substrate, which keeps the supply-chain audit surface small and uniform.

**Bazel-driven reproducibility.** The top-level `BUILD` file is essentially a comprehension matrix over
`{static, base, cc, java, nodejs, python3} × {distros} × {architectures} × {(latest, nonroot, debug, debug-nonroot)}`,
generating O(hundreds) of `oci_image_index` targets. The build is hermetic: package versions are pinned in
`private/repos/deb` and consumed by `rules_distroless`'s `apt.install` extension; busybox archives for the debug
variants are pulled via a `busybox.archive()` module extension that pins per-architecture sources.

**Two debug paths, by design.** Distroless images ship without a shell as the default security posture; the `:debug`
tags add a busybox shell for triage, and the `debug-nonroot` variants further drop privileges. The README is explicit
that `:debug` is a developer-loop convenience, not the production posture.

**Signed by default, keyless.** Every published image is cosign-signed with an ephemeral GCP-OIDC certificate, and the
verification recipe is in the top-level README. The project's `cosign.pub` and the `gcr.io/distroless` registry are the
trust anchors; users are expected to verify before pulling into production builds.

**Supply-chain cadence.** The SECURITY.md commits to a 48-hour-after-fix-availability response window for Debian
security-tracker CVEs; SUPPORT_POLICY.md commits to tracking Debian's standard support timeline (Debian 12 EOL Sept
2026; Debian 13 through Debian 14 release + 1 year for static/base/cc rungs). Language rungs (java/node/python) have
shorter support windows tied to upstream runtime LTS cycles.

## 3. What's reusable in Linus

**Base images for Phase 4+ containerized services.** Per CLAUDE.md, Docker for **services** (PostgreSQL, Neo4j, Qdrant,
Kiwix, Wikipedia mirrors, future web services) is permitted; Docker for **inference** is forbidden because the macOS
VM does not pass through Metal/ANE. When Linus reaches Phase 4 (Data Sovereignty — Kiwix, ProtoMaps/OSM, versioned
datasets per ROADMAP.md) and Phase 2a service-stack work (KnowledgeBase Postgres, fastmcp tool servers per DEC-0045),
distroless is the natural base-image default. The `python3-debian13` rung covers fastmcp tool servers; the
`nodejs26-debian13` rung covers any future openclaw-adjacent services; the `static-debian13` rung covers anything
written in Go or Rust (e.g., future Linus tooling).

**Concrete posture cross-reference for DEC-0024.** The supply-chain ADR (DEC-0024) hash-pins the linus conda env and
documents a pip-audit incident-response cadence. Distroless is the analogous discipline at the **container** layer:
known, signed, minimal base images with a 48-hour CVE-response commitment from upstream. When the Phase 4 service
specs land, citing distroless as the container-layer equivalent to DEC-0024's hash-pinned env is a clean
cross-reference. The Linus security posture is then "hash-pinned conda env on the host; distroless cosign-verified
base images for any containerized service."

**Methodology study: what gets stripped to make a 2 MiB production image.** The `base/config.bzl` package list is
remarkably short — for Debian 13: `libc6`, `libssl3t64`, `libzstd1`, `zlib1g`. That's the entire base userspace. For
the [`security-synthesis.md`](../syntheses/security-synthesis.md) thread on supply-chain minimization, the per-rung
package lists are a calibration point: "this is what production-grade Google considers the irreducible runtime for a
glibc-based service." Useful as a sanity check on any future "do we really need package X" debate, container or
otherwise.

**Cosign-keyless verification pattern.** The `cosign verify --certificate-oidc-issuer ... --certificate-identity ...`
recipe is reusable for any other signed artifact Linus eventually consumes (model weights from HuggingFace, KB
snapshots from a future Linus mirror, etc.). The pattern — keyless OIDC identity rather than long-lived signing keys —
is the modern shape for software-supply-chain provenance and is worth lifting as a default verification convention
whenever Linus has signed inputs.

**Multi-arch + reproducibility methodology.** Distroless publishes amd64, arm64, arm, s390x, ppc64le, and (newer
rungs) riscv64 from a single Bazel definition. Linus's primary substrate is arm64 (M1 Max), but future Linus
deployments (Mac Studio, Vision Pro, potentially cloud) cross architectures. The Bazel comprehension-over-arch pattern
is a methodology reference if Linus ever needs to publish multi-arch artifacts of its own (e.g., a Linus tool-server
image distributed to teammates).

## 4. What's inspiration only

**The Bazel build itself.** Distroless's reproducibility story rests on full Bazel + `rules_oci` + `rules_distroless`
+ `rules_python` + `rules_rust` + a half-dozen module extensions. For Linus to **consume** distroless images, none of
that machinery is needed — just `FROM gcr.io/distroless/python3-debian13` in a Dockerfile. The Bazel-based custom-image
authoring path is overkill for the small handful of containerized services Linus is likely to ship; the standard
multi-stage Dockerfile pattern (build with `python:3.13-slim-trixie`, copy artifacts into
`gcr.io/distroless/python3-debian13`) covers the use cases without adopting Bazel.

**The Debian-centric base.** Distroless tracks Debian releases, not Alpine or any musl-based distribution. For Linus,
this is fine — glibc is the right default for most workloads — but it's worth noting that distroless does not give
Linus an option for the Alpine size class (~5 MiB but musl-based). If Linus ever needs musl semantics (unlikely for
the service-stack roadmap), distroless is not the answer.

**The `debug` variant for production.** The `:debug` images add busybox; they're explicitly developer-loop
convenience. Linus production services should run the non-debug variants and triage via logs + structured audit trails
(per DEC-0030 scratchpad-first-class-artifact), not by shelling into containers. The discipline is "if you need to
shell into the container, you need better observability instead."

## 5. What's incompatible or out of scope

**The Linus orchestration backend itself is not containerized.** Per CLAUDE.md, ML inference and training run natively
on macOS to access Metal and ANE; Docker on macOS cannot pass them through. The Linus orchestration layer, Ollama,
pmetal, mlx-lm, and KnowledgeBase ingestion all run on the host conda env, not in containers. Distroless contributes
nothing to those code paths. Its applicability is bounded to the auxiliary service stack (Postgres, Neo4j, Qdrant,
Kiwix, etc.) that doesn't need GPU/ANE access.

**No macOS-specific value.** Distroless images are Linux-only. On a developer's M1 Max running Docker Desktop, the
Linux VM still needs to boot, which dominates the size-advantage delta for casual local use. The 2 MiB-vs-124 MiB win
matters most in cloud or fleet deployment, less so for Dan's MacBook-Pro-as-the-whole-deployment phase. The full win
arrives later (Phase 8 — Beyond MacBook: Mac Studio, cloud, multi-host).

**Bazel is not a Linus build tool.** The Linus repo uses `pyproject.toml` + conda + uv (DEC-0024). Adopting Bazel just
to author custom distroless images would invert the cost/benefit. The cheap path — multi-stage Dockerfile with
distroless as the final stage — sidesteps Bazel entirely. If Linus ever needs Bazel for some other reason, the
distroless `MODULE.bazel` is a clean reference; until then, vendoring Bazel-build patterns is not justified.

**License (Apache-2.0) permits derivative work, but there's no derivative to make.** Linus consumes distroless via
public image references; there is no codebase to vendor and no license attribution requirement beyond what the image
itself carries. The Apache-2.0 license is mentioned for completeness, not because it gates any decision.

## 6. Recommendation: **Adapt**

Distroless is the **default container base-image family** for any Phase 2a–Phase 4+ Linus auxiliary service that
genuinely needs containerization. The recommendation is "Adapt" rather than "Study" because the path is concrete: when
the first service spec lands (likely the KnowledgeBase Postgres in Phase 2a or a Kiwix mirror in Phase 4), the
Dockerfile's final stage uses a distroless image — `gcr.io/distroless/static-debian13` for Go/Rust services,
`gcr.io/distroless/base-debian13` for glibc-linked binaries, `gcr.io/distroless/python3-debian13` for any Python tool
server, `gcr.io/distroless/nodejs26-debian13` for any Node service. The cosign-verify step belongs in the build
pipeline, and the distroless choice is referenced as the container-layer counterpart to DEC-0024's hash-pinned conda
env.

The recommendation does **not** extend to authoring custom distroless images via Bazel; the standard multi-stage
Dockerfile pattern with distroless as the final stage is sufficient. And the recommendation explicitly does not apply
to the Linus orchestration backend or any inference/training path — those run natively on macOS where Docker is
forbidden for Metal/ANE reasons. Distroless is a service-stack tool, not a core-orchestration tool.

## 7. Questions for Dan

1. **When the first containerized Linus service ships (likely KnowledgeBase Postgres in Phase 2a or a Kiwix mirror in
   Phase 4), should the spec explicitly call out `gcr.io/distroless/<rung>-debian13` as the required base image and
   `cosign verify` as a required CI step?** Putting it in the first spec sets the precedent cheaply; retro-fitting
   later is harder.

2. **Should DEC-0024 (security posture, supply chain) be amended to name distroless as the container-layer
   counterpart**, or is a new container-supply-chain ADR (DEC-NNNN) the cleaner placement? An amendment is cheaper; a
   new ADR is more discoverable if container supply-chain grows into its own concern area.

3. **For the eventual Phase 8 "Beyond MacBook" deployments (Mac Studio, cloud, possibly multi-host), do you want Linus
   to publish its own multi-arch container images** (e.g., a fastmcp tool-server image for teammates to pull), or stay
   strictly host-native? If yes, distroless's Bazel comprehension-over-arch pattern is the reference; if no, this
   question is deferrable.

4. **Cosign-keyless verification as a Linus-wide convention for signed external inputs?** Beyond container images, the
   pattern applies to model weights, KB snapshots, and any other signed artifact Linus consumes. Worth surfacing as a
   convention update in CLAUDE.md "Engineering Conventions" alongside the existing supply-chain section?

5. **Is the `:debug` variant ever an acceptable production posture for a Linus service** (e.g., during incident triage
   on a service Dan can't easily roll), or is the discipline "non-debug only; observability replaces shell access"
   absolute? The discipline framing in §4 above is a draft; the canonical answer should be in SAFETY.md or in the
   first container-service spec.
