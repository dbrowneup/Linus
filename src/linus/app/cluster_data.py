"""Cluster-data loading helpers for the Streamlit Cluster Explorer page.

Loads the KnowledgeBase Phase 4 outputs (broad → mid → fine
hierarchical clustering plus UMAP projections) and exposes them as
typed Python objects ready for the UI's drill-down logic.

The data substrate (from ``modules/KnowledgeBase/papers_analysis/cluster.py``):

- ``labels_{broad,mid,fine}.json`` — per-paper cluster assignments,
  sha256 → cluster_id
- ``topics_{broad,mid,fine}.json`` — per-cluster human-readable topic
  labels, cluster_id → label
- ``hierarchy.json`` — Ward dendrogram structure linking broad / mid /
  fine cluster IDs (schema varies; this module handles two common
  shapes and falls back to deriving parent relationships from the
  label files if needed)
- ``umap_3d.npy`` + ``umap_sha256s.json`` — N×3 coordinates aligned
  with the per-paper sha256 list

This module is intentionally Streamlit-agnostic so the data layer is
independently testable and reusable.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np

Scale = Literal["broad", "mid", "fine"]
SCALES: tuple[Scale, ...] = ("broad", "mid", "fine")


@dataclass(frozen=True)
class TopicScale:
    """All per-paper + per-cluster info for one of the three scales."""

    scale: Scale
    paper_to_cluster: dict[str, str]  # sha256 → cluster_id
    cluster_to_label: dict[str, str]  # cluster_id → human-readable topic label
    cluster_to_papers: dict[str, list[str]] = field(default_factory=dict)

    def papers_in_cluster(self, cluster_id: str) -> list[str]:
        return self.cluster_to_papers.get(cluster_id, [])

    def paper_counts(self) -> dict[str, int]:
        return {cid: len(papers) for cid, papers in self.cluster_to_papers.items()}


@dataclass(frozen=True)
class ClusterData:
    """Top-level container for all loaded cluster data."""

    broad: TopicScale
    mid: TopicScale
    fine: TopicScale
    fine_to_mid: dict[str, str]
    mid_to_broad: dict[str, str]
    umap_3d: np.ndarray | None  # shape (N, 3) or None if file absent
    umap_sha256s: list[str]  # parallel to rows of umap_3d

    def scale(self, name: Scale) -> TopicScale:
        return {"broad": self.broad, "mid": self.mid, "fine": self.fine}[name]

    def children_of(self, parent_cluster_id: str, parent_scale: Scale) -> list[str]:
        """Return immediate children cluster IDs under a given parent.

        Broad → mid: list of mid_ids that map back to this broad_id.
        Mid → fine: list of fine_ids that map back to this mid_id.
        Fine has no children (returns empty list).
        """
        if parent_scale == "broad":
            return sorted({mid for mid, b in self.mid_to_broad.items() if b == parent_cluster_id})
        if parent_scale == "mid":
            return sorted({fine for fine, m in self.fine_to_mid.items() if m == parent_cluster_id})
        return []

    def papers_under(self, cluster_id: str, scale: Scale) -> list[str]:
        """All papers belonging (transitively) to a cluster at given scale.

        Used to scope the right-pane render. At fine scale = direct
        papers; at mid scale = union over child fine clusters; at broad
        scale = union over all descendant fine clusters.
        """
        if scale == "fine":
            return self.fine.papers_in_cluster(cluster_id)
        if scale == "mid":
            out: list[str] = []
            for fine_id in self.children_of(cluster_id, "mid"):
                out.extend(self.fine.papers_in_cluster(fine_id))
            return out
        # broad
        out2: list[str] = []
        for mid_id in self.children_of(cluster_id, "broad"):
            for fine_id in self.children_of(mid_id, "mid"):
                out2.extend(self.fine.papers_in_cluster(fine_id))
        return out2


def _read_json(path: Path) -> object | None:
    if not path.exists():
        return None
    try:
        with path.open() as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _coerce_labels(raw: object) -> dict[str, str]:
    """Normalize the labels file into ``{sha256: cluster_id}`` with str values.

    KB has historically shipped this as either:
    1. ``{"sha256_abc...": <int_cluster_id>}``
    2. ``{"sha256_abc...": "<int_cluster_id_str>"}``
    3. parallel arrays ``{"sha256s": [...], "labels": [...]}``
    Handle each defensively; non-conforming shapes yield an empty dict.
    """
    if isinstance(raw, dict):
        if "sha256s" in raw and "labels" in raw:
            shas = raw["sha256s"]
            labs = raw["labels"]
            if isinstance(shas, list) and isinstance(labs, list) and len(shas) == len(labs):
                return {
                    str(s): str(int(label) if isinstance(label, (int, float)) else label)
                    for s, label in zip(shas, labs)
                }
            return {}
        out: dict[str, str] = {}
        for sha, cid in raw.items():
            if cid is None:
                continue
            if isinstance(cid, (int, float)):
                cid_str = str(int(cid))
            else:
                cid_str = str(cid)
            out[str(sha)] = cid_str
        return out
    return {}


def _coerce_topics(raw: object) -> dict[str, str]:
    """Normalize topics file into ``{cluster_id_str: topic_label}``."""
    if isinstance(raw, dict):
        out: dict[str, str] = {}
        for cid, label in raw.items():
            if cid is None or label is None:
                continue
            cid_str = str(int(cid)) if isinstance(cid, (int, float)) else str(cid)
            label_str = label if isinstance(label, str) else str(label)
            out[cid_str] = label_str
        return out
    return {}


def _invert_to_clusters(paper_to_cluster: dict[str, str]) -> dict[str, list[str]]:
    """Build ``{cluster_id: [sha256, ...]}`` from the paper-to-cluster map."""
    out: dict[str, list[str]] = defaultdict(list)
    for sha, cid in paper_to_cluster.items():
        out[cid].append(sha)
    return dict(out)


def _load_scale(outputs_dir: Path, scale: Scale) -> TopicScale:
    labels = _coerce_labels(_read_json(outputs_dir / f"labels_{scale}.json"))
    topics = _coerce_topics(_read_json(outputs_dir / f"topics_{scale}.json"))
    cluster_to_papers = _invert_to_clusters(labels)
    return TopicScale(
        scale=scale,
        paper_to_cluster=labels,
        cluster_to_label=topics,
        cluster_to_papers=cluster_to_papers,
    )


def _derive_parent_map_via_majority(child_scale: TopicScale, parent_scale: TopicScale) -> dict[str, str]:
    """For each cluster at child scale, find its parent at parent scale by majority vote.

    For each child cluster, look at its papers and find what parent
    cluster the majority of them belong to. The plurality parent wins.
    Used as a fallback when hierarchy.json doesn't carry the
    relationship directly.
    """
    result: dict[str, str] = {}
    for child_cid, papers in child_scale.cluster_to_papers.items():
        parent_votes: Counter[str] = Counter()
        for sha in papers:
            parent = parent_scale.paper_to_cluster.get(sha)
            if parent is not None:
                parent_votes[parent] += 1
        if parent_votes:
            result[child_cid] = parent_votes.most_common(1)[0][0]
    return result


def _load_hierarchy_maps(
    outputs_dir: Path,
    broad: TopicScale,
    mid: TopicScale,
    fine: TopicScale,
) -> tuple[dict[str, str], dict[str, str]]:
    """Return (fine_to_mid, mid_to_broad) — child-cluster-id → parent-cluster-id.

    Tries hierarchy.json keys first:
    - ``"fine_to_mid"`` + ``"mid_to_broad"`` (canonical)
    - ``"hierarchy": {"broad": {...}}`` (nested form)

    Falls back to deriving via majority-vote join on the labels_*
    files, which always works given at least two labels files exist.
    """
    raw = _read_json(outputs_dir / "hierarchy.json")
    fine_to_mid: dict[str, str] = {}
    mid_to_broad: dict[str, str] = {}

    if isinstance(raw, dict):
        if "fine_to_mid" in raw and isinstance(raw["fine_to_mid"], dict):
            fine_to_mid = {str(k): str(v) for k, v in raw["fine_to_mid"].items()}
        if "mid_to_broad" in raw and isinstance(raw["mid_to_broad"], dict):
            mid_to_broad = {str(k): str(v) for k, v in raw["mid_to_broad"].items()}

        # Nested form: {"broad_id": {"mid_id": ["fine_id", ...]}}
        if not fine_to_mid and "hierarchy" in raw and isinstance(raw["hierarchy"], dict):
            for broad_id, mids in raw["hierarchy"].items():
                if not isinstance(mids, dict):
                    continue
                for mid_id, fines in mids.items():
                    mid_to_broad[str(mid_id)] = str(broad_id)
                    if isinstance(fines, list):
                        for fine_id in fines:
                            fine_to_mid[str(fine_id)] = str(mid_id)

    if not fine_to_mid:
        fine_to_mid = _derive_parent_map_via_majority(fine, mid)
    if not mid_to_broad:
        mid_to_broad = _derive_parent_map_via_majority(mid, broad)

    return fine_to_mid, mid_to_broad


def _load_umap(outputs_dir: Path) -> tuple[np.ndarray | None, list[str]]:
    """Load UMAP-3D coordinates + the parallel sha256 list."""
    umap_path = outputs_dir / "umap_3d.npy"
    sha_path = outputs_dir / "umap_sha256s.json"

    if not umap_path.exists():
        return None, []

    try:
        coords = np.load(umap_path)
    except (OSError, ValueError):
        return None, []

    raw = _read_json(sha_path)
    if isinstance(raw, list):
        shas = [str(s) for s in raw]
    else:
        shas = []

    # If sha list length doesn't match, the alignment is broken — return without shas
    # rather than fail; the page can render the scatter without click-back-to-paper.
    if shas and coords.shape[0] != len(shas):
        shas = []
    return coords, shas


def load_cluster_data(outputs_dir: Path) -> ClusterData | None:
    """Load all cluster artifacts. Returns ``None`` if essential files are missing.

    "Essential" = at least one of the three labels files. Without any
    cluster assignments there's nothing for the drill-down to render.
    Missing hierarchy.json triggers majority-vote derivation, not a
    failure.
    """
    broad = _load_scale(outputs_dir, "broad")
    mid = _load_scale(outputs_dir, "mid")
    fine = _load_scale(outputs_dir, "fine")

    if not (broad.paper_to_cluster or mid.paper_to_cluster or fine.paper_to_cluster):
        return None

    fine_to_mid, mid_to_broad = _load_hierarchy_maps(outputs_dir, broad, mid, fine)
    umap_3d, umap_shas = _load_umap(outputs_dir)

    return ClusterData(
        broad=broad,
        mid=mid,
        fine=fine,
        fine_to_mid=fine_to_mid,
        mid_to_broad=mid_to_broad,
        umap_3d=umap_3d,
        umap_sha256s=umap_shas,
    )
