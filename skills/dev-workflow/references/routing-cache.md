# Routing Cache

Reuses prior routing decisions for entity sets seen in recent runs rather than
re-running the expansion + complexity query every time. Pays off immediately on
iterative TDD sessions where the same modules are touched repeatedly.

## Cache Lookup (Step 0 of dynamic-routing.md)

Before Step 1 (entity expansion), check whether a consistent prior routing decision
exists for the current entity set:

```python
import json, datetime
from pathlib import Path

def check_routing_cache(G, entities_touched: list[str], recent_run_ids: list[str]) -> str | None:
    """Return the cached threshold_model if a consistent decision exists, else None."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
    candidates: list[str] = []

    for node_id, data in G.nodes(data=True):
        if data.get("file_type") != "rationale" or data.get("_origin") != "orchestrator":
            continue
        if data.get("run_id") not in recent_run_ids:
            continue
        # Check recency
        ts = data.get("timestamp")
        if ts:
            try:
                if datetime.datetime.fromisoformat(ts.rstrip("Z")).replace(
                    tzinfo=datetime.timezone.utc
                ) < cutoff:
                    continue
            except ValueError:
                continue
        # Check entity overlap
        authored = {
            n for n in G.neighbors(node_id)
            if G.edges[node_id, n].get("relation") == "authored"
        }
        if authored & set(entities_touched):  # any overlap
            t = data.get("threshold_model")
            if t:
                candidates.append(t)

    if len(candidates) >= 3 and len(set(candidates)) == 1:
        return candidates[0]  # unanimous decision across ≥ 3 steps → cache hit
    return None
```

`recent_run_ids` comes from `.claude/memory.json` `recent_run_ids` field — maintain
a sliding window of the 10 most recent run IDs there, appended at pipeline end.

## Hit Condition

All three conditions must hold:
- **≥ 3 step records** with entity overlap exist across recent runs
- **All candidates agree** on `threshold_model` (unanimous, not majority)
- **No candidate is older than 7 days** (stale decisions don't carry forward)

If any condition fails → cache miss → fall through to normal Step 1 expansion.

## Cache Miss Triggers

Do not use the cache when:
- `graph_node_count` in the most recent run differs by >5% from the current graph
  node count (graph drift detected — the prior decision was made on a different
  graph topology)
- Entity set is entirely new (no overlap with any prior step's authored nodes)
- Pipeline is running with `--force-reroute` flag

Graph-drift check:
```python
G_now = G.number_of_nodes()
last_snapshot = max(
    (d.get("graph_node_count", 0) for _, d in G.nodes(data=True)
     if d.get("run_id") in recent_run_ids),
    default=0
)
if last_snapshot and abs(G_now - last_snapshot) / max(G_now, last_snapshot) > 0.05:
    return None  # graph changed significantly — don't trust cached decision
```

## Step Record Fields

When a cache hit occurs, write to the step record:
```json
"routing_decision_source": "cache",
"cache_hit": true,
"threshold_model": "<the cached decision>",
"complexity_edge_count": null,
"expanded_entity_count": null,
"expansion_capped": null
```

`complexity_edge_count` is null on a cache hit because the query was not run. This
is intentional and expected — `measure-routing-cost.py` handles nulls in this field.

## Invalidation

The cache is not a stored data structure — it is derived on-the-fly from step records
already in the graph. Invalidation happens naturally:

- If the graph grows significantly (>5% drift), the check above returns a miss
- If routing decisions become non-unanimous over recent runs (e.g., a refactor
  changed the subgraph's density), the ≥ 3 + unanimous condition fails → miss
- Entries older than 7 days are excluded by the recency filter

No explicit cache-clear operation is needed.

## Observability

`measure-routing-cost.py` reports cache-hit rate in its summary output:

```
Routing sources (Run B): cache=3  query=1  cap=1  static=0
```

High cache-hit rates are normal for TDD iteration cycles. If the cache-hit rate is
zero across many runs, check that `recent_run_ids` is being populated in memory.

## Calibration

The 7-day window and 5% drift tolerance are starting guesses, not measured values.
Whether they fit depends on two workflow properties: how fast the graph grows per
week, and how often the same entity clusters get revisited within the window.

**Protocol:** run pipelines normally for two weeks, then:

```
python tools/measure-routing-cost.py --cache-report --days 14
```

The report shows the aggregate cache-hit rate over all cache-eligible steps
(static-routed steps excluded), plus a count of drift events — steps that ran
after the graph grew past the drift tolerance.

**Bands:**

| Hit rate | Verdict | Action |
|---|---|---|
| < 20% | Cache rarely fires | Retune (see below) |
| 20–60% | Acceptable | Keep observing |
| > 60% | Well-tuned | Leave it |

The verdict is held until at least 6 runs are in the window — a hit rate over 3
runs is noise.

**Which knob to turn on a low hit rate** — the drift-event count in the report
tells you which failure mode dominates:

- **Drift events dominate** → the codebase grows faster than 5%/week and the drift
  check is invalidating decisions that were still sound. Raise the tolerance
  (5% → 8–10%) in § Cache Miss Triggers above.
- **Few drift events** → the misses come from the revisit pattern: the same entity
  clusters aren't being touched within 7 days. Lengthen the window (7 → 14 days)
  in § Cache Lookup and § Hit Condition — or accept that this workflow doesn't
  revisit clusters often enough for the cache to pay off.
- **Misses from non-unanimous decisions** → routing genuinely varies for these
  clusters (the subgraph's density is changing between runs). The cache is
  correctly declining to fire; leave it alone.

Both constants live in this file's prose — the lookup is executed by the
orchestrator from this reference, not from a config file. When retuning, update
the numbers in § Cache Lookup (the `timedelta(days=7)`) and § Cache Miss Triggers
(the `0.05`), and keep `DRIFT_TOLERANCE` in `measure-routing-cost.py` in sync.

**Cadence:** `--cache-report` is a calibration instrument, not a routine health
check — expect to run it roughly twice a quarter, or when the workflow's character
changes (new repo, major refactor). To validate a retune after changing the
constants, use the two-run comparison mode (`measure-routing-cost.py <run_a>
<run_b>`) on a pre-change and post-change run — that's the ongoing diagnostic;
this report is only the knob-turning tool.
