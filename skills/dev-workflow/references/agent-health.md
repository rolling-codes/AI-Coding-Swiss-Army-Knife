# Sub-Agent Health Scoring

Tracks per-agent accuracy of `entities_touched` self-reports by comparing claimed
entity count against how many nodes actually received `authored` edges after the
orchestrator commits the step. Accuracy data feeds a routing adjustment: flagged
agents get one tier higher for verification.

## How Accuracy is Measured

After the orchestrator writes `authored_by` edges for a step, compute:

```
entity_accuracy = authored_entity_count / claimed_entity_count
```

Where:
- `claimed_entity_count` — length of the `entities_touched` list the sub-agent returned
- `authored_entity_count` — number of graph nodes that received `authored` edges from
  this step's step-record node

Values:
- `> 1.0` — agent understated fanout (more nodes were written than claimed)
- `= 1.0` — perfect accuracy
- `< 1.0` — agent over-reported fanout (fewer nodes were written than claimed)
- `null` — step had no `entities_touched` (skip; don't count against accuracy)

Over-reporting is the dominant failure mode — an agent that claims 10 entities but
only produces 7 authored edges inflates the expansion scope for the complexity query.

## Step Record Fields

Write these three fields on every step record that has a non-empty `entities_touched`:

```json
"claimed_entity_count": 10,
"authored_entity_count": 7,
"entity_accuracy": 0.70
```

If `claimed_entity_count` is 0, write `"entity_accuracy": null` and do not include
this step in accuracy aggregation.

## Aggregating into agent-health.json

At pipeline end (after step 4 / commit checkpoint), the orchestrator reads all step
records for the completed run, groups by agent type (inferred from `step_name`), and
updates `.claude/agent-health.json`:

```json
{
  "last_updated": "ISO-8601",
  "agents": {
    "code-reviewer": {
      "runs": 8,
      "mean_accuracy": 0.71,
      "recent_accuracies": [0.68, 0.72, 0.71, 0.73, 0.70],
      "flagged": true
    },
    "security-reviewer": {
      "runs": 3,
      "mean_accuracy": 0.94,
      "recent_accuracies": [0.93, 0.95, 0.94],
      "flagged": false
    }
  }
}
```

Fields:
- `runs` — total pipeline runs this agent has appeared in
- `mean_accuracy` — rolling mean of all observed `entity_accuracy` values
- `recent_accuracies` — last 5 values (for trend detection in `agent-health-report.py`)
- `flagged` — true if `mean_accuracy < 0.75`

The file is written by the orchestrator only, not by sub-agents.

## Routing Adjustment

Before querying complexity (Step 1 of `dynamic-routing.md`), check
`.claude/agent-health.json`. If the task is being dispatched to a flagged agent:

```
final_model = next_tier(complexity_model)
```

Where `next_tier` promotes:
- `fast` → `standard`
- `standard` → `deep`
- `deep` → `deep` (no further upgrade)

This is a one-tier upgrade, applied once, on top of the complexity routing result.
It stacks with the cap override (cap already pins to `deep`; this adjustment only
matters for non-cap steps).

Record the adjustment in the step:
```json
"routing_decision_source": "health_upgrade",
"health_flagged_agent": true
```

## Flagging Threshold

Flag when `mean_accuracy < 0.75`, calculated over all observed runs (minimum 3
observations before flagging). The threshold is conservative — a new agent with 1
run at 0.60 accuracy is not flagged until 3 observations confirm the pattern.

## Calibration

Run `tools/agent-health-report.py` to see per-agent accuracy over time:

```
Agent Health Report — .claude/agent-health.json
──────────────────────────────────────────────────────
Agent              Runs  Mean   Trend    Flagged
──────────────────────────────────────────────────────
code-reviewer         8  0.71   ↓ -0.03  YES
security-reviewer     3  0.94   → +0.01  no
tdd-guide             5  0.88   ↑ +0.04  no
──────────────────────────────────────────────────────
1 agent flagged. Flagged agents receive +1 routing tier at dispatch.
```

Trend is computed as the slope over the `recent_accuracies` window. A decreasing
trend on an already-flagged agent is worth investigating — the agent may have
changed behavior, or the pipeline's entity-resolution logic may be over-reporting
graph writes.
