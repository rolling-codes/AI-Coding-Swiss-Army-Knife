#!/usr/bin/env sh
# eval-routing.sh — run bsc.py eval across all skills that have routing test files
# and produce a routing accuracy report.
#
# Usage:
#   sh tools/eval-routing.sh              # dry-run structural check (no Claude calls)
#   sh tools/eval-routing.sh --live       # live eval (calls Claude — costs API tokens)
#
# Env vars:
#   BSC_SCRIPT  path to bsc.py  (default: C:/Users/Tom/Music/skill-creator/bsc.py)
#   BSC_PYTHON  python binary   (default: python)

set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)

BSC_PYTHON=${BSC_PYTHON:-python}
BSC_SCRIPT=${BSC_SCRIPT:-C:/Users/Tom/Music/skill-creator/bsc.py}
LIVE_FLAG=""
[ "${1:-}" = "--live" ] && LIVE_FLAG="--live"

# Verify bsc.py is reachable
if ! "$BSC_PYTHON" "$BSC_SCRIPT" --help >/dev/null 2>&1; then
  echo "ERROR: bsc.py not found at $BSC_SCRIPT"
  echo "  Set BSC_SCRIPT env var to the correct path, e.g.:"
  echo "  BSC_SCRIPT=/path/to/skill-creator/bsc.py sh tools/eval-routing.sh"
  exit 1
fi

PASS=0; FAIL=0; SKIP=0

for skill_dir in "$ROOT"/skills/*/; do
  skill=$(basename "$skill_dir")
  trigger_file="$skill_dir/tests/routing_trigger.yaml"
  boundary_file="$skill_dir/tests/routing_boundary.yaml"

  # Only run skills that have at least one routing test file
  if [ ! -f "$trigger_file" ] && [ ! -f "$boundary_file" ]; then
    SKIP=$((SKIP + 1))
    continue
  fi

  result=$("$BSC_PYTHON" "$BSC_SCRIPT" eval "$skill_dir" $LIVE_FLAG 2>&1)
  status=$?

  if [ $status -eq 0 ] && echo "$result" | grep -qi "PASSED\|all.*pass\|0 fail"; then
    PASS=$((PASS + 1))
    echo "PASS  $skill"
  else
    FAIL=$((FAIL + 1))
    echo "FAIL  $skill"
    # Show first failure line for quick diagnosis
    echo "$result" | grep -i "fail\|error" | head -3 | sed 's/^/      /'
  fi
done

echo ""
echo "Routing eval: $PASS pass / $FAIL fail / $SKIP skills have no routing tests"

if [ -n "$LIVE_FLAG" ]; then
  echo "(live mode — each FAIL represents a scenario where Claude routed incorrectly)"
else
  echo "(dry-run mode — pass means structural check only; use --live for real Claude eval)"
fi

[ "$FAIL" -eq 0 ]
