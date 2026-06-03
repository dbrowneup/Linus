# Cluster Explorer — KB broad/mid label-granularity mismatch (KNOWN ISSUE)

**Found:** 2026-06-02 (live Safari triage of the v0.5.0 Streamlit UI).
**Severity:** medium — degrades a demo "glance" beat (Cluster Explorer); **not** on the
v0.5.0-tag-critical path (the marquee is paper-qa). **Owner:** Dan (KnowledgeBase pipeline).

## Summary

The Cluster Explorer's **broad** (and **mid**) levels render an unusable ~999-entry topic
list and a garbled Sankey because the KB clustering outputs are internally inconsistent: the
`labels_{broad,mid}.json` files assign papers to cluster IDs at a far finer granularity than
the `topics_{broad,mid}.json` topic sets they are supposed to key into. The **fine** level is
clean and renders correctly (after the companion label-rendering fix). This is a
**KnowledgeBase pipeline data bug**, not a Linus app bug.

## Findings

Measured against `modules/KnowledgeBase/data/outputs/clusters/` on 2026-06-02:

| scale     | `topics_*.json` entries | distinct IDs in `labels_*.json` | label IDs with **no** matching topic |
| --------- | ----------------------- | ------------------------------- | ------------------------------------ |
| **broad** | 29                      | 999                             | **971**                              |
| **mid**   | 287                     | 1021                            | **735**                              |
| **fine**  | 1125                    | 1124                            | **0** ✓                              |

- `topics_*.json` values are BERTopic dicts `{"id","size","name","top_words"}` keyed by the
  reduced topic IDs (broad: −1..27).
- `labels_broad.json` maps the 10,666 papers to **999** distinct IDs (e.g. 401, 15, 12) that
  do not exist in `topics_broad.json` — i.e. it holds near-fine-resolution assignments, not
  the agglomerated broad assignment.
- `hierarchy.json`'s `mid_to_broad` is also inconsistent: it carries identity fallbacks
  (`"285": 285`, `"1123": 1123`) for mids that are not real broad clusters, so paper→broad
  **cannot be reliably re-derived** from `labels_fine.json` + `hierarchy.json` either.

Root cause (hypothesis): the broad/mid `labels_*.json` and the `mid_to_broad` half of
`hierarchy.json` were not regenerated after the hierarchical topic reduction that produced the
29 broad / 287 mid topic sets. Only the fine outputs are current.

## Remediation recommendations (priority order)

1. **KB-side (correct fix):** in the KB clustering pipeline, regenerate `labels_broad.json` /
   `labels_mid.json` so each paper carries its *reduced* broad/mid topic ID (the same ID space
   as `topics_{broad,mid}.json`), and rebuild `hierarchy.json` so `mid_to_broad` maps every
   real mid to a real broad (no identity fallbacks). Re-export and bump the KB submodule pin.
2. **Linus-side interim (optional, if KB regen is deferred):** have the Cluster Explorer
   default to the **fine** scale (which is consistent) and show an explicit "broad/mid topic
   reduction pending KB pipeline rerun" note instead of the 999-entry list. Tracked as a
   follow-up; not done here to avoid masking the real KB fix.

## Confidence assessment

High on the diagnosis (counts are exact, reproduced against the live outputs). The companion
Linus fix (`_coerce_topics` → topic `name`, this session's `fix/cluster-topic-labels`) is
independent and correct regardless: it makes the consistent fine level render real names today
and every level render names once the KB outputs are regenerated.
