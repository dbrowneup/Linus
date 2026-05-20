"""Build the tiny fixture KG GraphML used by :mod:`test_entity_kb`.

Run this once (or whenever the fixture needs regenerating):

    python -m linus.tests.fixtures.kb.build_fixture

It writes ``kg_graph.graphml`` next to this script. The fixture
mirrors the KB Phase 6 node-attribute conventions
(:mod:`papers_analysis.knowledge_graph`):

- Paper nodes — keyed by a (fake) sha; ``node_type="Paper"``.
- Entity nodes — keyed by ``"ent::<lower-cased text>"``;
  ``node_type="Entity"``; ``text`` carries the original surface form;
  ``label`` carries the SciSpacy NER category.

Five papers + ten entities + a hand-picked edge set let the
test suite exercise: known-hit lookups, known-miss lookups,
case-folding, paper-vs-entity disambiguation, and ref_count math
(BRCA1 is mentioned by three papers, EGFR by two, ASTAXANTHIN by one
— giving us a meaningful distribution to assert against).
"""

from __future__ import annotations

from pathlib import Path

import networkx as nx


def build_fixture_graph() -> nx.MultiDiGraph:
    """Construct the in-memory fixture graph (5 papers, 10 entities)."""
    g: nx.MultiDiGraph = nx.MultiDiGraph()

    # Papers — fake sha-ish ids; attrs match KB's writer.
    papers = [
        ("paper:p1", {"title": "BRCA1 in breast cancer", "year": "2020"}),
        ("paper:p2", {"title": "EGFR signaling pathways", "year": "2021"}),
        ("paper:p3", {"title": "BRCA1/2 in ovarian cancer", "year": "2022"}),
        ("paper:p4", {"title": "Botryococcus braunii lipid biology", "year": "2023"}),
        ("paper:p5", {"title": "BRCA1 and DNA repair mechanisms", "year": "2024"}),
    ]
    for pid, attrs in papers:
        g.add_node(pid, node_type="Paper", **attrs)

    # Entities — mix of high- and low-ref-count, mixed case to test fold.
    entities = [
        ("ent::brca1", "BRCA1", "GENE_OR_GENE_PRODUCT"),
        ("ent::egfr", "EGFR", "GENE_OR_GENE_PRODUCT"),
        ("ent::tp53", "TP53", "GENE_OR_GENE_PRODUCT"),
        ("ent::astaxanthin", "astaxanthin", "CHEMICAL"),
        ("ent::botryococcus braunii", "Botryococcus braunii", "ORGANISM"),
        ("ent::squalene", "squalene", "CHEMICAL"),
        ("ent::dna repair", "DNA repair", "BIOLOGICAL_PROCESS"),
        ("ent::cancer", "cancer", "DISEASE"),
        ("ent::ovarian cancer", "ovarian cancer", "DISEASE"),
        ("ent::lipid", "lipid", "CHEMICAL"),
    ]
    for nid, text, ner_label in entities:
        # ``label`` mirrors KB's NER label; ``text`` is the surface form.
        g.add_node(nid, node_type="Entity", text=text, label=ner_label)

    # Mentions edges (Paper → Entity) — gives us a meaningful ref_count
    # distribution: BRCA1 has 3 mentions (p1, p3, p5); EGFR has 2 (p2, p3
    # for the cross-cancer signaling section we'll pretend exists); TP53 has 1.
    mentions = [
        # p1 — BRCA1 in breast cancer
        ("paper:p1", "ent::brca1"),
        ("paper:p1", "ent::cancer"),
        # p2 — EGFR signaling
        ("paper:p2", "ent::egfr"),
        ("paper:p2", "ent::cancer"),
        # p3 — BRCA1/2 in ovarian cancer (also touches EGFR)
        ("paper:p3", "ent::brca1"),
        ("paper:p3", "ent::ovarian cancer"),
        ("paper:p3", "ent::egfr"),
        # p4 — Botryococcus braunii (Dan's PhD thesis topic)
        ("paper:p4", "ent::botryococcus braunii"),
        ("paper:p4", "ent::astaxanthin"),
        ("paper:p4", "ent::squalene"),
        ("paper:p4", "ent::lipid"),
        # p5 — BRCA1 and DNA repair (BRCA1 third mention)
        ("paper:p5", "ent::brca1"),
        ("paper:p5", "ent::dna repair"),
        ("paper:p5", "ent::tp53"),
    ]
    for paper_id, ent_id in mentions:
        g.add_edge(paper_id, ent_id, edge_type="mentions", ner_label="GENE")

    # A couple of REBEL edges (Entity → Entity) — these must NOT count
    # toward ref_count (only paper-typed predecessors should). Their
    # presence in the fixture is what proves the disambiguation works.
    g.add_edge("ent::brca1", "ent::dna repair", edge_type="rebel", relation="participates_in")
    g.add_edge("ent::egfr", "ent::cancer", edge_type="rebel", relation="associated_with")

    return g


def main() -> None:
    """Write the fixture GraphML next to this script."""
    here = Path(__file__).resolve().parent
    out = here / "kg_graph.graphml"
    g = build_fixture_graph()
    nx.write_graphml(g, out)
    print(f"wrote fixture: {out} ({g.number_of_nodes()} nodes, {g.number_of_edges()} edges)")


if __name__ == "__main__":
    main()
