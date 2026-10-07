# Pre-Dispatch Budget Check

Projects the token cost of each step before dispatching, accumulates a run total,
and pauses for developer approval if the cumulative projected cost would exceed the
configured threshold. This prevents surprise cost on god-node refactors that route
several steps to Opus.

## When It Fires

Before every sub-agent dispatch in the five-step pipeline, after dynamic routing
has determined the model alias but before the agent starts.

## Cost Projection Formula

```
projected_tokens = complexity_edge_count * 2 + 800
step_cost_usd    = projected_tokens / 1000 * cost_per_1k[model_alias]
```

Where:
- `complexity_edge_count` — edge count from the complexity query (Step 2 of
  `dynamic-routing.md`). If the query was skipped (cache hit), use the cached
  `complexity_edge_count` from the step record. If graph is absent (static routing),
  use a default of 100 edges.
- `800` — base overhead per step (prompt, return format, context)
- `cost_per_1k` — read from `model-registry.json` `cost_per_1k_tokens_usd`

The formula intentionally overestimates (better to pause early than overshoot silently).
Calibrate `800` up or down based on `actual_cost_usd` vs `projected_cost_usd` after
a few real runs.

## Threshold Configuration

Default: `$0.50` per pipeline run.

Override: set `budget_threshold_usd` in `.claude/memory.json`:
```json
"budget_threshold_usd": 1.00
```

If the field is absent, use `0.50`. If the graph is absent (no `complexity_edge_count`
available), run the check anyway using the 100-edge default from the projection
formula above, and mark the presented figures as coarse — a noisy projection the
developer can see beats a silent, unbudgeted dispatch they can't.

## Cumulative Tracking

The orchestrator maintains a running total for the active run:

```
cumulative_actual = sum(actual_cost_usd for completed steps)
cumulative_projected = sum(projected_cost_usd for remaining steps)
total_projected = cumulative_actual + cumulative_projected
```

Check fires when `total_projected > budget_threshold_usd`.

## Pause Protocol

When the check fires, stop before dispatching the current step and present:

```
Budget check: projected run cost $0.63 exceeds threshold $0.50

  Completed:  2 steps  |  $0.18 actual
  Remaining:  3 steps  |  $0.45 projected
  Breakdown:
    Step 2 (tdd)         → Sonnet   ~$0.012
    Step 3 (code_review) → Opus     ~$0.026   ← this step
    Step 4 (commit)      → Sonnet   ~$0.008

Options:
  1. Continue at current model tiers
  2. Downgrade remaining steps to "standard" (Sonnet)   → ~$0.038 total
  3. Abort run (checkpoint saved — resume with lower threshold)
```

Wait for developer response before dispatching. If developer chooses option 2,
set `model_used` to `standard` for all remaining steps and recompute the projected
cost before continuing.

## Step Record Fields

Record two cost fields on every step-record node:

```json
"projected_cost_usd": 0.012,
"actual_cost_usd": 0.009
```

`projected_cost_usd` is written at dispatch time (before the agent runs).
`actual_cost_usd` is written at checkpoint-commit time (after the agent returns),
computed as:

```
actual_cost_usd = token_cost / 1000 * cost_per_1k[model_alias]
```

The gap between projected and actual, aggregated over runs, is how you calibrate
the projection formula.

## Measurement

The `--budget` flag in `measure-routing-cost.py` prints a per-step actual vs
projected table after a run completes:

```
Step  Name          Model     Projected   Actual    Delta
0     research      Haiku      $0.002     $0.001   -50%
1     plan          Sonnet     $0.008     $0.011   +37%
2     tdd           Opus       $0.042     $0.031   -26%
...
Total                          $0.063     $0.051   -19%
```

Use this to decide whether to adjust the `800`-token base constant or the
threshold itself.
