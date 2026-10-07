# Checkpoint Protocol

Implements Graphify-backed run state so pipelines survive interruption. The
orchestrator (main session) is the sole graph writer. Sub-agents return results;
the orchestrator commits them.

## When to Use

- Any full five-step pipeline run (Research → Plan → TDD → Code Review → Commit)
- Any delegated multi-step task spanning more than one sub-agent dispatch
- Skip for one-liner / abbreviated pipeline runs where a single step completes inline

## Prerequisite

`graphify-out/graph.json` must exist for the project. If it doesn't, fall back to
`.claude/runs/{run_id}.json` as a sidecar-only checkpoint (no graph writes).

## Run ID Format

```
{repo_slug}_{unix_ms}
```

Example: `easycord_1720612345678`

- `repo_slug`: repo name from `.claude/memory.json` `"repo"` field, slug-safe
  (lowercase, replace `/` and spaces with `_`)
- `unix_ms`: millisecond timestamp at pipeline start

Store the run_id in memory for the session:
```json
"active_run_id": "easycord_1720612345678"
```

**Collision detection:** Before writing step 0, check whether the generated run_id
already exists in the graph (two concurrent sessions can produce the same
`{repo_slug}_{unix_ms}` if they start within the same millisecond). If it does,
append a random 4-hex-char suffix:

```python
import random, string
G = nx.node_link_graph(json.loads(Path("graphify-out/graph.json").read_text()), edges="links")
existing_runs = {d["run_id"] for _, d in G.nodes(data=True) if d.get("run_id")}
if run_id in existing_runs:
    run_id = f"{run_id}_{''.join(random.choices(string.hexdigits[:16], k=4))}"
```

## Commit Phase (after each step completes)

After a step's sub-agents return results and the orchestrator aggregates:

### 1. Collect touched entities

From sub-agent `entities_touched` lists. These are Graphify node IDs or file paths;
paths get mapped to their node IDs via `get_node(label)`.

### 2. Write step-record node

Node uses `file_type: "rationale"` and `_origin: "orchestrator"` to distinguish
from code/doc nodes. Additional fields beyond the 8-field core are stored as extra
NetworkX node properties — Graphify does not restrict them.

```json
{
  "id": "run_{run_id}_step_{N}",
  "label": "{step_name}",
  "file_type": "rationale",
  "_origin": "orchestrator",
  "source_file": ".claude/runs/{run_id}.json",
  "source_location": null,
  "norm_label": "{step_name}",
  "run_id": "{run_id}",
  "step_index": 0,
  "step_name": "research | plan | tdd | code_review | commit",
  "step_hash": "sha256({input_summary}+{step_name})",
  "model_used": "claude-sonnet-4-6",
  "token_cost": 0,
  "exit_status": "success",
  "timestamp": "ISO-8601",
  "expanded_entity_count": 8,
  "expansion_capped": false,
  "complexity_edge_count": 43,
  "threshold_model": "fast | standard | deep",
  "routing_decision_source": "cache | cap | query | static | health_upgrade",
  "graph_node_count": 4837,
  "cache_hit": false,
  "claimed_entity_count": 10,
  "authored_entity_count": 7,
  "entity_accuracy": 0.70,
  "projected_cost_usd": 0.012,
  "actual_cost_usd": 0.009
}
```

### 3. Write authored_by edges

One edge per touched entity, pointing from the step record to the entity:

```json
{
  "source": "run_{run_id}_step_{N}",
  "target": "{entity_node_id}",
  "relation": "authored",
  "confidence": "EXTRACTED",
  "confidence_score": 1.0,
  "context": "run_id:{run_id}"
}
```

### 4. Acquire file lock and merge into graph

Graphify has no transaction support. A second concurrent session writing at the same
time will corrupt `graph.json`. Acquire a lock before calling `build_merge()`.

**With portalocker (preferred — cross-platform):**
```python
import portalocker
from pathlib import Path
lock_path = Path("graphify-out/.graphify.lock")
with portalocker.Lock(str(lock_path), timeout=10):
    build_merge(new_extractions, Path("graphify-out/graph.json"), ...)
# Lock released on context exit; timeout=10s raises LockException if held too long
```

**Fallback (portalocker unavailable):**
```python
import os, time
from pathlib import Path
lock_path = Path("graphify-out/.graphify.lock")
# Check for stale lock (>60s old → assume dead process)
if lock_path.exists() and time.time() - lock_path.stat().st_mtime > 60:
    lock_path.unlink()
if lock_path.exists():
    raise RuntimeError("graph.json is locked by another process")
lock_path.write_text(str(os.getpid()))
try:
    build_merge(new_extractions, Path("graphify-out/graph.json"), ...)
finally:
    lock_path.unlink(missing_ok=True)
```

Install portalocker if available: `pip install portalocker`

Use `graphify.build.build_merge()` or the Graphify MCP server. Always
orchestrator-initiated — never from inside a sub-agent.

```bash
# Via MCP (preferred when server is running)
python -m graphify.serve graphify-out/graph.json
# Then call query tools normally; use a direct build_merge() call for writes

# Via Python API
python -c "
from graphify.build import build_merge
from pathlib import Path
build_merge(new_extractions, Path('graphify-out/graph.json'), prune_sources=[], root=Path('.'), directed=False)
"
```

### 5. Sidecar fallback

Always also append to `.claude/runs/{run_id}.json` — this survives if the graph
write fails:

```json
{
  "run_id": "easycord_1720612345678",
  "steps": [
    {
      "step_index": 0,
      "step_name": "research",
      "exit_status": "success",
      "timestamp": "ISO-8601",
      "entities_touched": ["node_id_1", "node_id_2"]
    }
  ]
}
```

## Recovery Phase (on session resume)

Triggered when `active_run_id` is present in `.claude/memory.json`.

### 1. Query for incomplete steps

```
query_graph("incomplete steps run_id:{run_id}", budget=500)
```

Filter returned nodes:
```
file_type == "rationale"
AND _origin == "orchestrator"
AND run_id == "{active_run_id}"
AND exit_status != "success"
```

Sort by `step_index` ascending.

### 2. Determine resume point

- No incomplete steps → run finished; clear `active_run_id` from memory
- Incomplete steps found → resume from the lowest `step_index`

### 3. Reconstruct prior step context

For the step immediately before the resume point, fetch its output entities:

```
get_neighbors("run_{run_id}_step_{N-1}")
# Returns all nodes connected by "authored" edges
```

Pass those node IDs to the resuming step as its available inputs.

### 4. Proceed

Run the incomplete step with its reconstructed inputs. Continue forward through
remaining steps. On each completion, commit to graph as normal.

## Sidecar Fallback (no graph.json)

If `graphify-out/graph.json` does not exist, write only to `.claude/runs/{run_id}.json`.
Recovery reads the sidecar directly:

```json
// Find last completed step
last_success = max(step["step_index"] for step in sidecar["steps"] if step["exit_status"] == "success")
resume_from = last_success + 1
```

No entity reconstruction is possible without the graph; provide a summary of the
prior step's result from memory instead.

## Housekeeping

Clear `active_run_id` from memory when:
- All five steps reach `exit_status: "success"`
- User explicitly cancels the run

Do not delete run sidecar files — they serve as a lightweight audit trail.
