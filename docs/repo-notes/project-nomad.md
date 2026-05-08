# project-nomad (`Crosstalk-Solutions/project-nomad`)

## 1. Purpose and scope

Project N.O.M.A.D. (Node for Offline Media, Archives, and Data) is a self-contained, offline-first **knowledge and
education server** packaged as a Docker-Compose orchestration of pre-built components: Kiwix for offline Wikipedia and
ebook ZIMs, Kolibri for Khan Academy courseware, ProtoMaps for offline regional maps, CyberChef for data-munging,
FlatNotes for local notes, and Ollama + Qdrant for a local AI assistant with RAG over uploaded documents — all wrapped
in a management UI ("Command Center") at `localhost:8080`. Tagline: "Knowledge That Never Goes Offline." For Linus this
is **inspiration only** — a bill of materials showing which third-party components a data-sovereignty layer can be built
from, not code to adopt.

## 2. Architecture summary

NOMAD is a distribution, not a framework. Its real contribution is the _curated list_: Kiwix (ZIMs for Wikipedia,
medical references, survival guides, ebooks), Kolibri (Khan Academy), ProtoMaps (offline PMTiles), CyberChef (offline
data tooling), FlatNotes (local Markdown notes), Ollama + Qdrant (AI + vector DB). These run as Docker containers
orchestrated from a Debian host (Ubuntu recommended), with the Command Center UI handling installation, updates, and
configuration. Recommended hardware for the AI features is NVIDIA RTX 3060 or better; it explicitly does _not_ target
Apple Silicon. No authentication by default — it's assumed to run inside a trusted home network. No built-in telemetry.
A community leaderboard at `benchmark.projectnomad.us` ranks hardware builds.

## 3. What's reusable in Linus

The component list. Phase 4 of Linus's roadmap (Data Sovereignty Layer) adopts four of the same pieces as first-class
components: **Kiwix** for offline Wikipedia and reference ZIMs, **Kolibri** for structured Khan Academy courseware,
**ProtoMaps** for OSM tiles, and **data package version tracking** — plus optionally **Qdrant** and **CyberChef**
(explicitly called out as Docker-acceptable stateless services). NOMAD is proof these components compose reasonably and
that the operational pattern ("dockerized stateless services, native inference") works.

Linus's Phase 4 should treat NOMAD as a recipe to consult, not code to vendor: install Kiwix natively on macOS (its
native binary works fine and avoids the Docker-on-macOS Metal/ANE trap), install Kolibri natively (also has a macOS app;
avoids Docker), PMTiles as a static file served by any local web server, Qdrant in Docker if KnowledgeBase's numpy path
hits its limit.

Kiwix and Kolibri are complementary, not duplicates. Kiwix serves reference lookups (Wikipedia articles, ebook ZIMs);
Kolibri serves structured pedagogy (Khan Academy's learning tree, with worked examples and exercises). A query like
"explain the Needleman-Wunsch algorithm" is better served by Kolibri's curriculum tree than by a Kiwix article.

## 4. What's inspiration only

The _posture_ — sovereignty as a first-class concern, privacy by default, no telemetry, works in a Faraday cage — is
aligned with Linus's stance and is now articulated explicitly in VISION.md. The `~/.linus/data_packages.json` +
update-check tool pattern in Phase 4 of the roadmap is effectively the same idea as NOMAD's Command Center, simplified
for a single-user CLI-first context.

FlatNotes (NOMAD's local Markdown notes component) has no role in Linus's stack. Obsidian is a materially better fit:
local-first, mature plugin ecosystem, already part of Dan's workflow, and well- suited to integration with a Linus tool
that reads the vault.

## 5. What's incompatible or out of scope

Almost everything about how NOMAD ships. It's Debian/Ubuntu-first, Docker-orchestrated, NVIDIA-GPU-recommended for the
AI features, and designed for a local network with multiple users sharing one box. Linus is macOS-first,
Apple-Silicon-only, single-user, and has a hard constraint against Docker for inference workloads because
Docker-on-macOS runs in a VM and does not pass through Metal or ANE. The management UI ("Command Center") is a browser
app that assumes a shared host; Linus's UI is per-user via Streamlit/openclaw. NOMAD's AI assistant is a thin wrapper
around Ollama + Qdrant + document upload — Linus's is orchestration + KnowledgeBase + multi-agent + skills, which is a
much deeper stack.

## 6. Recommendation: **Ignore (as a product); borrow components individually**

Do not install NOMAD. Do not vendor its Command Center. Do read its component list when Phase 4 starts, to confirm the
canonical choices (Kiwix for offline knowledge, ProtoMaps for maps, Qdrant if a vector DB is needed) and to pick up any
useful curation decisions (which ZIMs to install, which PMTiles region files to default to). NOMAD's value to Linus is
as a _reference catalog_ and a _validation_ that the offline-knowledge pattern works when the components are picked
carefully. Nothing beyond that.

## 7. Questions for Dan

1. **Phase 4 scope ambition.** Roadmap Phase 4 now includes Kolibri as a named integration target alongside Kiwix and
   PMTiles. CyberChef is noted as a Docker-acceptable stateless service if data-munging tooling is wanted. FlatNotes is
   replaced by Obsidian vault integration. The open question: is CyberChef worth adding as a Phase 4 tool, or is it out
   of scope for a research assistant?
2. **Kiwix ZIM selection.** The practical question that NOMAD resolves by asking the user: which Wikipedia subset? Full
   English is ~100 GB; Simple English is ~1 GB; there are topical ZIMs (medical, Wikipedia-for-schools). Any preference
   for genomics / biochem / chemistry-focused ZIMs if they exist?
3. **PMTiles regions.** Offline maps are only useful for specific places. Oregon + PNW makes sense given context. Any
   other regions (fieldwork sites, travel) matter?
4. **Qdrant-in-Docker vs. native vector store.** NOMAD uses Qdrant because it's a general-purpose offering; Linus's
   KnowledgeBase currently uses numpy-based similarity search. Are we promising Qdrant in Phase 4 only if benchmarks
   force it, or do you want it regardless for a smoother long-term path? _Partially resolved (S60, see
   [answered-questions.md](../questions/answered-questions.md)): Docker is acceptable for stateful services that don't
   need GPU/ANE (Qdrant is explicitly named); Qdrant-in-Docker is a valid Phase 4 option if numpy-based search
   benchmarks force it._
5. **Explicit sovereignty statement in VISION.md.** NOMAD's phrasing ("Knowledge That Never Goes Offline," zero
   telemetry, no authentication by default because the network boundary is the trust boundary) is crisper than Linus
   currently articulates. Worth lifting into VISION.md? _Partially resolved (E1, see
   [answered-questions.md](../questions/answered-questions.md)): VISION.md now has an explicit open-source-by-default /
   sovereignty "Release posture" section; the offline/zero-telemetry framing is addressed there._
