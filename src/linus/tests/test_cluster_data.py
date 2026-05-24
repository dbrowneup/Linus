"""Tests for :mod:`linus.app.cluster_data`.

Hermetic: builds tiny JSON / npy fixtures in a tmp dir to exercise the
loader against each accepted schema variant.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from linus.app.cluster_data import load_cluster_data


def _write(path: Path, content) -> None:
    path.write_text(json.dumps(content))


def _seed_minimal(tmp: Path) -> None:
    """Write a 6-paper, 2-broad / 2-mid / 4-fine toy corpus.

    Paper layout (sha → fine cluster):
        p1, p2 → fine 100
        p3     → fine 101  (both fine 100 and 101 are under mid 10, broad 1)
        p4, p5 → fine 200  (under mid 20)
        p6     → fine 201  (under mid 21, broad 2)
    """
    _write(tmp / "labels_fine.json", {"p1": 100, "p2": 100, "p3": 101, "p4": 200, "p5": 200, "p6": 201})
    _write(tmp / "labels_mid.json", {"p1": 10, "p2": 10, "p3": 10, "p4": 20, "p5": 20, "p6": 21})
    _write(tmp / "labels_broad.json", {"p1": 1, "p2": 1, "p3": 1, "p4": 1, "p5": 1, "p6": 2})
    _write(tmp / "topics_fine.json", {"100": "fine-A", "101": "fine-B", "200": "fine-C", "201": "fine-D"})
    _write(tmp / "topics_mid.json", {"10": "mid-X", "20": "mid-Y", "21": "mid-Z"})
    _write(tmp / "topics_broad.json", {"1": "broad-alpha", "2": "broad-beta"})


def test_load_returns_none_when_no_labels_files(tmp_path: Path) -> None:
    assert load_cluster_data(tmp_path) is None


def test_load_basic_corpus(tmp_path: Path) -> None:
    _seed_minimal(tmp_path)
    data = load_cluster_data(tmp_path)
    assert data is not None
    assert len(data.broad.paper_to_cluster) == 6
    assert len(data.broad.cluster_to_label) == 2
    assert data.broad.cluster_to_label["1"] == "broad-alpha"
    assert data.broad.cluster_to_label["2"] == "broad-beta"


def test_cluster_to_papers_inversion(tmp_path: Path) -> None:
    _seed_minimal(tmp_path)
    data = load_cluster_data(tmp_path)
    assert data is not None
    assert sorted(data.fine.cluster_to_papers["100"]) == ["p1", "p2"]
    assert data.fine.cluster_to_papers["101"] == ["p3"]
    assert sorted(data.mid.cluster_to_papers["10"]) == ["p1", "p2", "p3"]


def test_hierarchy_majority_vote_fallback(tmp_path: Path) -> None:
    """No hierarchy.json → fine_to_mid + mid_to_broad derived via majority vote."""
    _seed_minimal(tmp_path)
    data = load_cluster_data(tmp_path)
    assert data is not None
    # All p1..p3 are in fine 100/101 under mid 10.
    assert data.fine_to_mid["100"] == "10"
    assert data.fine_to_mid["101"] == "10"
    assert data.fine_to_mid["200"] == "20"
    assert data.fine_to_mid["201"] == "21"
    assert data.mid_to_broad["10"] == "1"
    assert data.mid_to_broad["20"] == "1"
    assert data.mid_to_broad["21"] == "2"


def test_hierarchy_explicit_fine_to_mid_form(tmp_path: Path) -> None:
    """hierarchy.json with explicit child→parent maps takes precedence over derivation."""
    _seed_minimal(tmp_path)
    _write(
        tmp_path / "hierarchy.json",
        {
            "fine_to_mid": {"100": "10", "101": "10", "200": "20", "201": "21"},
            "mid_to_broad": {"10": "1", "20": "1", "21": "2"},
        },
    )
    data = load_cluster_data(tmp_path)
    assert data is not None
    assert data.fine_to_mid["100"] == "10"
    assert data.mid_to_broad["21"] == "2"


def test_hierarchy_nested_form(tmp_path: Path) -> None:
    """hierarchy.json with nested broad→{mid→[fines]} shape is supported."""
    _seed_minimal(tmp_path)
    _write(
        tmp_path / "hierarchy.json",
        {
            "hierarchy": {
                "1": {"10": ["100", "101"], "20": ["200"]},
                "2": {"21": ["201"]},
            }
        },
    )
    data = load_cluster_data(tmp_path)
    assert data is not None
    assert data.fine_to_mid["100"] == "10"
    assert data.fine_to_mid["201"] == "21"
    assert data.mid_to_broad["10"] == "1"
    assert data.mid_to_broad["21"] == "2"


def test_children_of(tmp_path: Path) -> None:
    _seed_minimal(tmp_path)
    data = load_cluster_data(tmp_path)
    assert data is not None
    assert sorted(data.children_of("1", "broad")) == ["10", "20"]
    assert data.children_of("2", "broad") == ["21"]
    assert sorted(data.children_of("10", "mid")) == ["100", "101"]
    assert data.children_of("100", "fine") == []


def test_papers_under_aggregates_descendants(tmp_path: Path) -> None:
    _seed_minimal(tmp_path)
    data = load_cluster_data(tmp_path)
    assert data is not None
    # Fine level — direct papers
    assert sorted(data.papers_under("100", "fine")) == ["p1", "p2"]
    # Mid level — union over child fine clusters
    assert sorted(data.papers_under("10", "mid")) == ["p1", "p2", "p3"]
    # Broad level — union over all descendant fine clusters
    assert sorted(data.papers_under("1", "broad")) == ["p1", "p2", "p3", "p4", "p5"]
    assert data.papers_under("2", "broad") == ["p6"]


def test_load_umap_aligned(tmp_path: Path) -> None:
    _seed_minimal(tmp_path)
    coords = np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2], [3, 3, 3], [4, 4, 4], [5, 5, 5]], dtype=float)
    np.save(tmp_path / "umap_3d.npy", coords)
    _write(tmp_path / "umap_sha256s.json", ["p1", "p2", "p3", "p4", "p5", "p6"])
    data = load_cluster_data(tmp_path)
    assert data is not None
    assert data.umap_3d is not None
    assert data.umap_3d.shape == (6, 3)
    assert data.umap_sha256s == ["p1", "p2", "p3", "p4", "p5", "p6"]


def test_load_umap_misaligned_drops_shas(tmp_path: Path) -> None:
    """Length mismatch between coords and sha list = render-without-click-back."""
    _seed_minimal(tmp_path)
    coords = np.zeros((6, 3))
    np.save(tmp_path / "umap_3d.npy", coords)
    _write(tmp_path / "umap_sha256s.json", ["p1", "p2"])  # too short
    data = load_cluster_data(tmp_path)
    assert data is not None
    assert data.umap_3d is not None
    assert data.umap_sha256s == []


def test_labels_parallel_arrays_form(tmp_path: Path) -> None:
    """Old/alternate labels schema: parallel arrays."""
    _write(tmp_path / "labels_fine.json", {"sha256s": ["a", "b"], "labels": [7, 7]})
    _write(tmp_path / "labels_mid.json", {"a": 1, "b": 1})
    _write(tmp_path / "labels_broad.json", {"a": 0, "b": 0})
    _write(tmp_path / "topics_fine.json", {"7": "fine-G"})
    _write(tmp_path / "topics_mid.json", {"1": "mid-G"})
    _write(tmp_path / "topics_broad.json", {"0": "broad-G"})
    data = load_cluster_data(tmp_path)
    assert data is not None
    assert data.fine.paper_to_cluster == {"a": "7", "b": "7"}
