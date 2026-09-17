# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A 13-skill Claude Code plugin pack (`dev-workflow-pack`). The authoritative plugin metadata is in `.claude-plugin/plugin.json`. There is no build step, no package.json, no compiled output — the "code" is Markdown skill files, POSIX shell scripts, and JSON config.

## Validation

The only automated check is the static consistency validator:

```sh
sh tools/validate-pack.sh
```

Run this before any release tag and after any change to a skill directory name, the routing table in `skills/dev-workflow/SKILL.md`, README.md, `hooks/hooks.json`, or `agents/*.md`. It exits 0 on pass. The 14 checks it runs:

1. SKILL.md `name:` matches directory name
2. All 12 siblings referenced in dev-workflow's routing table
3. All JSON files parse
4. All shell scripts pass `sh -n`
5. `hooks.json` only references scripts that exist
6. Every routing-table arrow (`→ **name**`) points at a real skill directory
7. Every skill is documented in README.md
8. Every SKILL.md has a `description:` field
9. Every `agents/*.md` frontmatter `name:` matches its filename
10. (informational) Hook scripts that ship but aren't registered in `hooks.json`
11. Every skill directory is mentioned in `skill-routing.md` (CTB table)
12. `model-registry.json` declares all three alias keys (`fast`, `standard`, `deep`)
13. Every SKILL.md has a `model:` field
14. Every SKILL.md has an `allowed-tools:` field

It does **not** test skill triggering or hook firing. Behavioral smoke testing requires a live Claude Code session — use `tools/routing-scenarios.md` as the manual test spec (44 scenarios across §A representative, §B ambiguous, and §C adversarial).

## Architecture

```
skills/
  dev-workflow/          ← orchestrator; routes to all 12 siblings
    SKILL.md             ← main router + 5-step pipeline (Research→Plan→TDD→Review→Commit)
    model-registry.json  ← ONLY place model strings live; resolve via alias at call time
    references/          ← lazy-loaded per task (never preload speculatively)
      skill-routing.md   ← pairwise disambiguation, handoff contract, conflict precedence
      memory.md          ← memory read/write protocol
      context-management.md, coding-tasks.md, github-operations.md, …
  <skill-name>/
    SKILL.md             ← frontmatter: name, description, allowed-tools, model
                           body: Iron Law, Red Flags, Capability/Trigger/Boundary, workflow
hooks/
  hooks.json             ← only PreToolUse (branch protection) is registered
  scripts/
    protect-branches.sh  ← active; reads hooks/config/branch-policy.json
    load-memory.sh       ← ships, not registered (opt-in — see UPGRADE-SLOTS.md)
    save-memory.sh       ← ships, not registered (opt-in — see UPGRADE-SLOTS.md)
  config/
    branch-policy.json   ← protected branch patterns
agents/
  code-reviewer.md       ← independent reviewer subagent; receives only task briefing, no session history
tools/
  validate-pack.sh       ← static consistency checker (14 checks)
  routing-scenarios.md   ← manual smoke-test spec (§A representative, §B ambiguous, §C adversarial)
```

## Key constraints when editing

**Skill structure.** Each `SKILL.md` must have a YAML frontmatter block with `name:` (must match the directory name), `description:`, `allowed-tools:`, and `model:`. The `name:` / directory match is enforced by check 1 in `validate-pack.sh`.

**Routing integrity.** If you add, rename, or remove a skill directory:
1. Update the routing table in `skills/dev-workflow/SKILL.md`.
2. Update `skills/dev-workflow/references/skill-routing.md` (§3 ownership table, §5 pairwise pairs).
3. Add/update the skill row in `README.md`.
4. Add/update a scenario in `tools/routing-scenarios.md` (§A representative, §B if it introduces an ambiguous boundary).
5. Run `sh tools/validate-pack.sh` and confirm exit 0.

**Memory hooks are intentionally disabled.** `hooks.json` registers only branch protection. `load-memory.sh` and `save-memory.sh` ship but are not registered — this is intentional. Do not silently re-enable them. If enabling them, follow the instructions in `UPGRADE-SLOTS.md` and update documentation in `README.md`, `skills/dev-workflow/references/memory.md`, `.claude-plugin/plugin.json`, and `.claude-plugin/marketplace.json` in the same commit.

**Router arrows must resolve.** Check 6 in the validator confirms every `→ **skill-name**` in the routing table points at a real `skills/<skill-name>/` directory. A renamed skill without a router update fails validation.

**Model strings.** Never hardcode a model name anywhere in the pack. All model references resolve through `skills/dev-workflow/model-registry.json` via alias (`fast` → Haiku-class, `standard` → Sonnet-class, `deep` → Opus/Fable-class). When a new model ships, update only the registry.

**Planned upgrades.** `UPGRADE-SLOTS.md` documents two intentionally-empty slots: `strategic-compact` (a replacement for context-compression, sourced from the ECC repo) and `claude-mem` (a companion session-memory plugin, not a drop-in file). Do not add a `strategic-compact` skill without following the slot instructions — it requires retiring or explicitly co-existing with `context-compression` and rewiring the router.

**Changelog.** Maintain an `[Unreleased]` section in `CHANGELOG.md` for in-progress changes. Use Keep a Changelog format with conventional types (Fixed, Added, Changed, Removed). Promote to a version section when tagging a release.

## Release checklist

1. `sh tools/validate-pack.sh` — exit 0
2. `[Unreleased]` section in `CHANGELOG.md` is populated and dated
3. Version bumped consistently in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`
4. Manual smoke-test against `tools/routing-scenarios.md` in a live session
