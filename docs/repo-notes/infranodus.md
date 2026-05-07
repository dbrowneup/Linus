# infranodus (`noduslabs/infranodus`)

## 1. Purpose and scope

InfraNodus is a text-to-network web app from Nodus Labs (Dmitry Paranyushkin) that turns plain text into a co-occurrence
graph — every word a node, every co-occurrence within a sliding context window an edge — and then runs network-science
algorithms (modularity-based community detection via Graphology's Louvain, betweenness centrality via JSNetworksX, LDA
topic modelling via the `lda` library) to surface "discourse structure": main topics, most influential terms, structural
gaps between communities. The signature framing is **cognitive variability** — measuring whether a body of text is
biased, focused, diversified, or dispersed, and treating structural gaps in the graph as candidate sites for new ideas.
The paper of record is Paranyushkin's WWW'19 piece "InfraNodus — Generating Insight Using Text Network Analysis." The
clone in `repos/infranodus` is the original open-source v2.0.0 web app from ~2019 (Express + EJS + Sigma.js + Neo4j
3.x); the active product line has since moved into a hosted SaaS at infranodus.com plus a separate `infranodus-skills` /
MCP-server ecosystem.

## 2. Architecture summary

A monolithic Node.js Express app. Routing is in `app.js` (a flat list of ~80 `app.get`/`app.post` registrations) with
handlers in `routes/` (`api.js`, `api2.js`, `entries.js`, plus per-importer files for Evernote, Twitter, Google, RSS,
YouTube). The graph engine lives in `lib/`: `lib/entry.js` (~1000 lines, the core text-to-Cypher pipeline) wraps
tokenisation (`wink-tokenizer`), morphological lemmatisation per language (`phpmorphy-locutus` for English, Russian,
German; `nlp-js-tools-french` for French), language detection, hashtag extraction (`flowdock-text`), and statement
validation (`lib/middleware/validate.js`); `lib/db/neo4j.js` (~600 lines) emits Cypher against a Neo4j 3.3.9–3.5
instance via the legacy `node-neo4j` driver. The data model is opinionated and unusual: five node labels (`:Concept`,
`:Statement`, `:Context`, `:User`, `:Narrative`) and five edge types (`:TO` between concepts, `:AT` concept-to-context,
`:OF` concept-to-statement, `:IN` statement-to-context, `:BY` to user, `:INTO`/`:THRU` for narratives). Every user input
is a "statement" — a hyperedge over the concepts it co-mentions — rather than a binary edge, which is the part of the
model the README is proudest of. The browser does the heavy graph maths client-side: Sigma.js for rendering,
Graphology + `graphology-louvain-functions` for modularity, JSNetworksX for betweenness, Cytoscape.js for additional
metrics. A `gapscan` flag in the Cypher (`lib/entry.js` line 506) marks edges added by structural-gap inference vs
direct co-occurrence. JSON/GEXF export and a REST API (`/api/user/nodes`, `/api/user/statements`,
`/api/:user/lda/:type`) expose the graph for downstream consumption. **Licence: AGPL-3.0** — viral on network use, which
matters for any vendor decision in Linus.

## 3. What's reusable in Linus

The directly reusable pieces are conceptual rather than code-level. The **co-occurrence-window + Louvain + betweenness +
structural-gap-detection** pipeline is exactly the "second view" Linus's KnowledgeBase needs on top of the
RDF-and-property-graph spine from DEC-0026/27 — a way to look at a corpus of papers/notes and ask "what concepts
co-occur, what communities of ideas are in here, where are the bridges, where are the gaps?" — and the algorithms are
all standard enough that a Python re-implementation against `networkx` or `graph-tool` (or the existing Python port,
`DiscourseDiversity` on GitLab) would land in a single Phase 2 or Phase 3 sprint. The five-label cognitive data model
(`Concept`/`Statement`/`Context`/`User`/`Narrative` with `Statement` as a hyperedge) is genuinely novel prior art for
Phase 3 hybrid retrieval — it captures provenance ("who said this where") in the graph topology itself rather than as
side-car metadata, which solves a problem Linus will hit when episodic memory (Layer A in the memory architecture) and
semantic memory (Layer D, KnowledgeBase) need to share a substrate. Compared to the sibling `infranodus-skills` repo,
which is purely Claude-skill prompts that _call_ the hosted InfraNodus MCP server, this codebase is the only place where
the actual graph-construction algorithm is open-source and inspectable; if Linus wants the InfraNodus method without
paying Nodus Labs or sending data off-machine, this clone is the source of truth.

## 4. What's inspiration only

The web app itself — Express, EJS templates, jQuery, Sigma.js, Bootstrap Tour, Vagrant box, Evernote/Twitter/Gmail
importers, Chargebee billing, PhantomJS — is dead weight for Linus. Mid-2010s Node stack, abandoned dependencies
(`phantom`, `node-neo4j`, `bcrypt-nodejs`, jQuery 1.x-era plugins), Neo4j 3.x (current is 5.x with very different Cypher
and APOC). The "useful libraries" folder under `lib/sandbox/` and the per-importer routes are vestigial. The cognitive-
variability _measure_ (the index that maps modularity + community-size distribution onto biased/focused/diversified/
dispersed) is the differentiating IP, but it is largely _interpretive_ — applied on top of standard Louvain output — and
the SaaS layers a GPT-3 "idea generation" step on top of it that is explicitly Pro-only and not in this repo.

## 5. What's incompatible or out of scope

**AGPL-3.0** is the dominant constraint. Vendoring any non-trivial portion of `lib/entry.js` or `lib/db/neo4j.js` into
Linus would force AGPL on the touching code, and AGPL's network-use clause means even a local-only Linus exposing an
HTTP endpoint that surfaces InfraNodus-derived output is arguably a covered "use over a network." Re-implementing the
algorithm from the WWW'19 paper avoids this. The hard Neo4j dependency is also out of scope — DEC-0026/27 picks a
different graph substrate (RDF + property graph in a unified store, not Neo4j Community), so the Cypher in `lib/db/`
isn't directly portable. Node.js as the runtime for an analytics module is fine in principle but adds a process boundary
Linus doesn't otherwise need; the Python port is a better starting point.

## 6. Recommendation: **Study**

Read the WWW'19 paper, read `lib/entry.js` for the text-to-graph pipeline and `lib/db/neo4j.js` for the Cypher patterns
that compute communities and gaps, and treat the data model (Concept/Statement/Context/Narrative with hyperedge
statements) as a serious candidate for Phase 3 hybrid retrieval. Do not vendor any code. When Phase 3 hybrid retrieval
needs a co-occurrence-graph view alongside the embeddings layer, re-implement the cognitive-variability metric in Python
against the existing KnowledgeBase store (or fork `DiscourseDiversity`), and treat `infranodus-skills` as the production
"how would Claude actually use this?" reference for prompt-side integration.

## 7. Questions for Dan

- **AGPL avoidance.** The cognitive-variability _idea_ is unencumbered (it's in a published paper); the _code_ is AGPL.
  Confirm the policy is "re-implement from the paper, never copy" — and that this also applies to the Python port on
  GitLab, which is MIT but derives from AGPL upstream.
- **Cognitive variability as a first-class KB metric.** Worth surfacing biased/focused/diversified/dispersed as a
  first-class quality signal on KnowledgeBase contexts in Phase 3 (e.g., "this paper cluster is dispersed — bridge it"),
  or is that a Phase 7 skills-layer concern after the substrate is solid?
- **Statement-as-hyperedge in the data model.** Linus's memory architecture has episodic events that are naturally
  hyperedges over multiple concepts. Adopt InfraNodus's `:Statement`/`:OF`/`:IN` pattern explicitly in the
  property-graph half of DEC-0027, or stick with binary edges + reified statement nodes only when needed?
- **Relationship to `infranodus-skills`.** That sibling repo assumes a hosted MCP server. If Linus re-implements the
  engine locally, do we also stand up an MCP server façade so the same skill prompts work unchanged against local data,
  or is that scope creep before Phase 3?

  _Partially resolved (DEC-0018, DEC-0045): MCP adopted as extensibility substrate and fastmcp as the in-house MCP
  framework default — a local infranodus façade would follow the same pattern when Phase 3 arrives._

- **Neo4j.** DEC-0026/27 currently does not pick Neo4j. Does anything in InfraNodus's Cypher make a strong enough case
  to revisit that, or is the substrate decision settled and Cypher is just a reading exercise?

  _Resolved (DEC-0015, see [answered-questions.md](../questions/answered-questions.md)): Dual approach (RDF + property
  graph) is the settled substrate; Neo4j not adopted._
