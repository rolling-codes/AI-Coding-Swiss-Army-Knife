#!/bin/sh
# Static validation for the dev-workflow-pack plugin. Run before every release
# (release-prep should call this). Catches the class of bug that's easy to
# introduce by hand: a skill added without a routing-table entry, a config
# file that doesn't parse, a hook script with broken syntax.
#
# This is a static check only — it does not exercise skill triggering or
# hook firing inside an actual Claude Code session. Passing this script means
# "the files are internally consistent," not "this has been run end to end."

set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
FAILFILE=$(mktemp)
trap 'rm -f "$FAILFILE"' EXIT

fail() { echo "FAIL: $1" >&2; echo x >> "$FAILFILE"; }
ok()   { echo "ok:   $1"; }

# 1. Every skills/<dir>/SKILL.md exists and its frontmatter name: matches the dir name.
for dir in "$ROOT"/skills/*/; do
  name=$(basename "$dir")
  skill_file="$dir/SKILL.md"
  if [ ! -f "$skill_file" ]; then
    fail "skills/$name has no SKILL.md"
    continue
  fi
  fm_name=$(awk -F': *' '/^name:/{print $2; exit}' "$skill_file" | tr -d '\r')
  if [ "$fm_name" != "$name" ]; then
    fail "skills/$name/SKILL.md frontmatter name '$fm_name' does not match directory name"
  else
    ok "skills/$name frontmatter matches directory"
  fi
done

# 2. Every skill except dev-workflow itself must be mentioned in dev-workflow's
#    SKILL.md (the routing table). Catches "added a skill, forgot to route to it."
ROUTER="$ROOT/skills/dev-workflow/SKILL.md"
if [ -f "$ROUTER" ]; then
  for dir in "$ROOT"/skills/*/; do
    name=$(basename "$dir")
    [ "$name" = "dev-workflow" ] && continue
    if ! grep -q "$name" "$ROUTER"; then
      fail "skill '$name' is not referenced anywhere in dev-workflow/SKILL.md — routing table is missing an entry"
    else
      ok "skill '$name' is referenced in the router"
    fi
  done
else
  fail "dev-workflow/SKILL.md not found — cannot check routing table coverage"
fi

# 3. All JSON files parse.
JSON_TOOL="python3"
command -v "$JSON_TOOL" >/dev/null 2>&1 || JSON_TOOL=""
find "$ROOT" -name "*.json" -not -path "*/node_modules/*" | while read -r f; do
  if [ -n "$JSON_TOOL" ]; then
    if ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" >/dev/null 2>&1; then
      echo "FAIL: $f is not valid JSON" >&2
      echo x >> "$FAILFILE"
    fi
  elif command -v jq >/dev/null 2>&1; then
    jq -e . "$f" >/dev/null 2>&1 || { echo "FAIL: $f is not valid JSON" >&2; echo x >> "$FAILFILE"; }
  fi
done

# 4. All shell scripts parse (sh -n).
find "$ROOT" -name "*.sh" | while read -r f; do
  if ! sh -n "$f" 2>/dev/null; then
    echo "FAIL: $f has a shell syntax error" >&2
    echo x >> "$FAILFILE"
  fi
done

# 5. hooks.json references scripts that actually exist.
HOOKS_JSON="$ROOT/hooks/hooks.json"
if [ -f "$HOOKS_JSON" ]; then
  grep -o 'hooks/scripts/[a-zA-Z0-9_.-]*\.sh' "$HOOKS_JSON" | sort -u | while read -r rel; do
    if [ ! -f "$ROOT/$rel" ]; then
      echo "FAIL: hooks.json references $rel which does not exist" >&2
      echo x >> "$FAILFILE"
    fi
  done
fi

# 6. Reverse routing: every skill a router table row points at (→ **name**)
#    must be a real skill directory. Catches a routing arrow left pointing at a
#    renamed or deleted skill — the inverse of check 2.
if [ -f "$ROUTER" ]; then
  grep '→' "$ROUTER" | grep -oE '\*\*[a-z0-9][a-z0-9-]*\*\*' | sed 's/\*//g' | sort -u | while read -r ref; do
    if [ ! -d "$ROOT/skills/$ref" ]; then
      echo "FAIL: dev-workflow routing table points at skill '$ref' but skills/$ref/ does not exist" >&2
      echo x >> "$FAILFILE"
    fi
  done
fi

# 7. Every skill is documented in README.md. Catches a skill added (or renamed)
#    without updating the user-facing skills table.
README="$ROOT/README.md"
if [ -f "$README" ]; then
  for dir in "$ROOT"/skills/*/; do
    name=$(basename "$dir")
    if ! grep -q "$name" "$README"; then
      fail "skill '$name' is not mentioned in README.md — the skills table is out of date"
    else
      ok "skill '$name' is documented in README"
    fi
  done
else
  fail "README.md not found — cannot check documentation coverage"
fi

# 8. Every SKILL.md frontmatter declares a description (the field skill routing
#    keys on). A skill with no description silently never triggers.
for dir in "$ROOT"/skills/*/; do
  name=$(basename "$dir")
  skill_file="$dir/SKILL.md"
  [ -f "$skill_file" ] || continue
  if ! grep -q '^description:' "$skill_file"; then
    fail "skills/$name/SKILL.md frontmatter has no description: field"
  fi
done

# 9. Every agents/*.md has a frontmatter name matching its filename (the same
#    contract check 1 enforces for skills — a mismatch breaks dispatch).
for af in "$ROOT"/agents/*.md; do
  [ -f "$af" ] || continue
  base=$(basename "$af" .md)
  aname=$(awk -F': *' '/^name:/{print $2; exit}' "$af" | tr -d '\r')
  if [ "$aname" != "$base" ]; then
    fail "agents/$base.md frontmatter name '$aname' does not match filename"
  else
    ok "agent '$base' frontmatter matches filename"
  fi
done

# 10. (informational, never fails) Hook scripts that ship but are not registered
#     in hooks.json. The memory hooks are intentionally unregistered — see
#     UPGRADE-SLOTS.md — so this is a heads-up, not an error.
if [ -f "$HOOKS_JSON" ]; then
  for hs in "$ROOT"/hooks/scripts/*.sh; do
    [ -f "$hs" ] || continue
    hb=$(basename "$hs")
    if ! grep -q "$hb" "$HOOKS_JSON"; then
      echo "note: hooks/scripts/$hb ships but is not registered in hooks.json (intentional for the memory hooks — see UPGRADE-SLOTS.md)"
    fi
  done
fi

# 11. Every skill directory name must appear in skill-routing.md (the CTB table and
#     pairwise pairs). A skill renamed without updating this reference fails silently
#     at routing time even though checks 2 and 7 pass — the two routing sources drift
#     independently.
ROUTING_REF="$ROOT/skills/dev-workflow/references/skill-routing.md"
if [ ! -f "$ROUTING_REF" ]; then
  fail "$ROUTING_REF not found — cannot check CTB coverage"
else
  for dir in "$ROOT"/skills/*/; do
    name=$(basename "$dir")
    [ "$name" = "dev-workflow" ] && continue
    if ! grep -q "$name" "$ROUTING_REF"; then
      fail "skill '$name' not mentioned in skills/dev-workflow/references/skill-routing.md — CTB table may be out of date"
    fi
  done
  echo "  [11] skill-routing.md covers all skill directories."
fi

# 12. model-registry.json must declare all three required alias keys. A missing key
#     means skills that reference that alias lose their model assignment with no error.
MODEL_REG="$ROOT/skills/dev-workflow/model-registry.json"
if [ ! -f "$MODEL_REG" ]; then
  fail "$MODEL_REG not found"
else
  for alias in fast standard deep; do
    if ! grep -q "\"$alias\"" "$MODEL_REG"; then
      fail "model-registry.json is missing required alias key '$alias'"
    fi
  done
  echo "  [12] model-registry.json has all required alias keys (fast, standard, deep)."
fi

# 13. Every SKILL.md frontmatter declares a model: field. A skill without a
#     model: field inherits the session default instead of the intended tier,
#     silently breaking the fast/standard/deep routing contract.
for dir in "$ROOT"/skills/*/; do
  name=$(basename "$dir")
  skill_file="$dir/SKILL.md"
  [ -f "$skill_file" ] || continue
  if ! grep -q '^model:' "$skill_file"; then
    fail "skills/$name/SKILL.md frontmatter has no model: field"
  fi
done
echo "  [13] all SKILL.md frontmatter blocks declare model:."

# 14. Every SKILL.md frontmatter declares an allowed-tools: field. A skill
#     without an allowed-tools: field has no declared tool-use guardrails.
for dir in "$ROOT"/skills/*/; do
  name=$(basename "$dir")
  skill_file="$dir/SKILL.md"
  [ -f "$skill_file" ] || continue
  if ! grep -q '^allowed-tools:' "$skill_file"; then
    fail "skills/$name/SKILL.md frontmatter has no allowed-tools: field"
  fi
done
echo "  [14] all SKILL.md frontmatter blocks declare allowed-tools:."

if [ -s "$FAILFILE" ]; then
  echo "" >&2
  echo "Validation failed. This checks internal consistency only — passing" >&2
  echo "this does not mean the pack has been exercised in a live Claude Code" >&2
  echo "session. Manual smoke-test each new/changed skill before release." >&2
  exit 1
fi

echo ""
echo "All static checks passed. Reminder: this is a consistency check, not an"
echo "end-to-end test — skill triggering and hook firing still need manual"
echo "verification in an actual Claude Code session before release."
exit 0
