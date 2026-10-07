#!/bin/sh
# PreToolUse hook on the Bash tool. Guards against destructive git operations
# that are hard to reverse. Exit 2 blocks the tool call and feeds stderr back
# to Claude; exit 0 lets it run.
#
# Guards applied:
#   git push --force / -f  — can silently overwrite remote history
#   git reset --hard        — discards all uncommitted work with no undo
#
# Override: set DEV_WORKFLOW_ALLOW_DESTRUCTIVE=1 in environment to bypass.

set -u

[ "${DEV_WORKFLOW_ALLOW_DESTRUCTIVE:-0}" = "1" ] && exit 0

INPUT=$(cat 2>/dev/null || true)

# git push --force or -f
if printf '%s' "$INPUT" | grep -Eq 'git[[:space:]]+(push)[[:space:]].*(-f\b|--force)'; then
  echo "Blocked by dev-workflow-pack: 'git push --force' can overwrite remote history and is hard to reverse. If this is intentional (e.g. cleaning up a personal branch after a rebase), set DEV_WORKFLOW_ALLOW_DESTRUCTIVE=1 and retry." >&2
  exit 2
fi

# git reset --hard
if printf '%s' "$INPUT" | grep -Eq 'git[[:space:]]+reset[[:space:]]+--hard'; then
  echo "Blocked by dev-workflow-pack: 'git reset --hard' discards all uncommitted changes permanently. If this is intentional, set DEV_WORKFLOW_ALLOW_DESTRUCTIVE=1 and retry." >&2
  exit 2
fi

exit 0
