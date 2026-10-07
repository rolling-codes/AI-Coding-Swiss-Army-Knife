# Dynamic Cost Routing

Before dispatching a sub-agent, query the Graphify knowledge graph to measure the
structural complexity of the task's scope, then pick the model tier from
`model-registry.json` accordingly. Denser subgraphs require more reasoning — the
graph makes that measurable before any tokens are spent on the task itself.

## Prerequisite

`graphify-out/graph.json` must exist. When absent, fall back to the static
`task_map` in `model-registry.json` without change.

## Query Protocol

### 0. Check routing cache

Before any expansion or query, check whether a prior run already made a consistent
routing decision for this entity set. See `references/routing-cache.md` for the full
lookup algorithm.

**Cache hit:** `routing_decision_source: "cache"`, `cache_hit: true`. Skip Steps 1–3
and use the cached `threshold_model` directly in Step 4. Set `complexity_edge_count`,
`expanded_entity_count`, and `expansion_capped` to null.

**Cache miss:** fall through to Step 1 as normal.

### 1. Identify the task's entity scope

From the planning step, collect:
- File paths being modified
- Named symbols (function names, class names, module names)
- The task description (used as fallback when no entity names are available)

### 1.5. Expand entity list by 1 hop

Raw `entities_touched` only names nodes the sub-agent directly modified. If any
of those nodes are god nodes (high-fanout), the bare list underestimates actual
impact — the complexity query would see only the named node, not its callers.

Expand before querying:

```python
import networkx as nx, json
from pathlib import Path

G = nx.node_link_graph(json.loads(Path("graphify-out/graph.json").read_text()), edges="links")
expanded = set(entities_touched)
for entity_id in list(entities_touched):
    expanded.update(G.neighbors(entity_id))
# Use expanded as the entity scope for step 2
```

This adds one in-process NetworkX call (microseconds). The expanded set reflects
structural impact radius, not just modification sites.

**When to skip expansion:** if the entity list is already large (>20 nodes),
expansion can cause false positives. Cap at 20 entities post-expansion.

**Critical: always run the complexity query, even when the cap fires.** The cap
overrides the final model decision, but the query's edge count is still needed
to distinguish a necessary override (cap fired, query would also have said `deep`)
from an unnecessary one (cap fired, query would have said `fast`). Skipping the
query when capped makes the step record non-comparable across threshold recalibrations.

Always record five fields on the step-record node:
- `expanded_entity_count`: size of the expanded set (before capping)
- `expansion_capped`: `true` if expanded count hit or exceeded 20
- `complexity_edge_count`: edge count returned by `query_graph()` — always written, even when capped
- `threshold_model`: what the edge-count thresholds alone would have decided (`"fast"`, `"standard"`, `"deep"`)
- `routing_decision_source`: `"cache"` if Step 0 returned a hit; `"cap"` if the cap overrode the threshold decision; `"query"` for a normal edge-count decision; `"static"` if graph was absent; `"health_upgrade"` if the agent health check applied a tier upgrade on top

When `expansion_capped: true`, set `model_used` to `"deep"` (cap decision) and set
`routing_decision_source: "cap"`. The `threshold_model` field records the counterfactual.

Also record `graph_node_count: G.number_of_nodes()` on every step record. This snapshots
the graph size at execution time so `measure-routing-cost.py` can flag comparisons where
the graph grew significantly between runs — edge counts computed against different graph
sizes are not directly comparable.

### 2. Query subgraph complexity

```bash
# Via Graphify MCP (preferred)
query_graph("{entity_names or task description} dependencies", budget=500)

# Via CLI
graphify query "{entity_names}" --budget 500
```

Pass the **expanded** entity names from step 1.5 as the query subject. The query
returns a subgraph — the set of nodes and edges reachable within the budget from
nodes matching the entity names.

### 3. Count returned edges

`E = number of edges in the returned subgraph`

### 4. Map to model tier

Look up thresholds from `model-registry.json` `complexity_routing`:

| Edge count | Alias | Default model |
|---|---|---|
| E < `low_threshold` (50) | `low` → `fast` | Haiku |
| `low_threshold` ≤ E < `high_threshold` (200) | `mid` → `standard` | Sonnet |
| E ≥ `high_threshold` (200) | `high` → `deep` | Opus |

Resolve alias → API string via `model-registry.json` `aliases` as normal.

### 5. Override rules

Complexity routing upgrades but does not downgrade static routing:

- If `task_map` says `deep` and complexity says `fast` → use `deep`
- If `task_map` says `fast` and complexity says `deep` → use `deep`
- Complexity is a floor-raiser, not a ceiling-setter

Security reviews (`security_review`) and architecture tasks (`architecture`) are
pinned to `deep` in `task_map` — complexity routing is a no-op for them.

### 5.5. Agent health adjustment

After resolving the final model alias (including cap and task_map overrides), check
`.claude/agent-health.json`. If the agent being dispatched is flagged
(`mean_accuracy < 0.75` with ≥ 3 observations), apply a one-tier upgrade:

| Current alias | After adjustment |
|---|---|
| `fast` | `standard` |
| `standard` | `deep` |
| `deep` | `deep` (no change) |

Record `routing_decision_source: "health_upgrade"` and `health_flagged_agent: true`
on the step record. See `references/agent-health.md` for the flagging criteria and
how to update `.claude/agent-health.json`.

## Examples

### Leaf change → Haiku

Task: "Fix the typo in `utils/format.ts` `formatDate` function"

Query: `query_graph("formatDate dependencies", budget=500)`

Returns: 3 nodes, 2 edges (the function, its module, and one caller)

`E = 2 < 50` → `fast` → Haiku

### Cross-cutting refactor → Opus

Task: "Rename `ServerConfigStore` to `ConfigRegistry` across the codebase"

Query: `query_graph("ServerConfigStore dependencies", budget=500)`

Returns: 47 nodes, 312 edges (it's a god node; EasyCord has 10,488 edges from it)

`E = 312 ≥ 200` → `deep` → Opus

### Feature addition → Sonnet

Task: "Add rate limiting to the `/api/sessions` endpoint"

Query: `query_graph("sessions endpoint middleware dependencies", budget=500)`

Returns: 18 nodes, 87 edges

`E = 87`, `50 ≤ 87 < 200` → `standard` → Sonnet

## Caching

Store the complexity result on the step-record node (see `checkpoint.md`) so
recovery runs don't re-query for the same step:

```json
"complexity_edge_count": 87,
"model_used": "claude-sonnet-4-6"
```

## Fallback Chain

1. `graphify-out/graph.json` exists → use complexity routing
2. Graph absent → use static `task_map` lookup
3. Neither applies (unknown task type) → default to `standard`

Never block on routing. If the query fails or times out, use `standard` and log
the failure in `.claude/runs/{run_id}.json`.
