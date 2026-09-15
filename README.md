# Dev Workflow Pack

Thirteen development-workflow skills rebuilt through the
[skill-creator](https://github.com/rolling-codes/-the-better-skill-creator-skill-)
six-gate pipeline, plus hook-enforced session memory and branch protection. One
Claude Code plugin.

**v2.0.0:** each skill now carries an explicit Capability + Trigger + Boundary
description (so skills fire when they should and stay silent when a sibling owns
the task), an Iron Law stating its one non-negotiable rule as "X because Y"
reasoning, and a Red Flags table of agent-introspected rationalizations paired
with the correct behavior. Pairwise description overlap was checked across all
thirteen before release.

## What the hooks do

Skills are instructions Claude can forget. Hooks are guarantees that fire every time.

- **SessionStart** (startup, resume, and after compaction): injects a short digest into context — branch, dirty-file count, the one-paragraph session summary from `.claude/memory.json`, and a pointer to the full files. Claude reads the full files only when the digest is not enough, so the recurring per-session cost is a few lines, not the whole memory.
- **PreCompact** (manual `/compact` and auto-compaction): snapshots branch, uncommitted-file count, and the last five commits to `.claude/memory-auto.json`, so the post-compaction SessionStart reload has fresh state to hand back.
- **PreToolUse** (Bash): blocks `git commit` and `git push` while on `main`, `master`, `develop`, `release/*`, or `hotfix/*`, and tells Claude to create a feature branch. Matching is a plain text scan, so a command that merely mentions "git commit" inside a string can false positive; disable per repo in `/hooks` if it gets in the way.

Both scripts are plain POSIX sh, depend only on `git`, never block (always exit 0), and stay silent outside a git repo. On Windows they run under Git Bash, which ships with Git for Windows.

## Install

From a marketplace that lists this plugin:

```
/plugin marketplace add <owner>/<repo>
/plugin install dev-workflow-pack
```

Or from a local checkout:

```
claude plugin install /path/to/dev-workflow-pack
```

Restart Claude Code (or run `/reload-plugins`) after installing — hooks register at session start.

## Agent included

**code-reviewer** — an independent reviewer with its own context window. The code-review skill dispatches it with a description, requirements, and a commit range; it returns only findings (Strengths, Critical/Important/Minor issues, verdict). Because it runs outside the main conversation, a large-diff review costs the main context a briefing and a findings list instead of the whole diff.

## Skills included

| Skill | Job |
|---|---|
| dev-workflow | Orchestrator: routing, model selection, GitHub ops, memory |
| commit-message | Conventional Commits from staged changes |
| pr-description | PR description from branch diff and history |
| changelog | Keep a Changelog entries from git history |
| release-prep | Version drift, changelog, tests, go/no-go checklist |
| code-review | Self-review checklist or delegated reviewer subagent |
| bug-triage | Deduplicate and severity-rank findings |
| scope-creep | Flags mid-build scope expansion automatically |
| architecture-review | Coupling, cohesion, layering, dependency direction |
| test-strategy | Unit/integration/edge-case/regression test generation |
| context-compression | Session context budget: summarize, keep/drop, age memory |
| docs-audit | Docs vs. code drift: current/stale/dead/gap classification |

context-compression, docs-audit, and architecture-review sound similar —
they audit three different targets (session memory, doc files, source
structure respectively). See the disambiguation table in
`skills/dev-workflow/SKILL.md` if it's unclear which applies.

## Validating the pack itself

`tools/validate-pack.sh` is a static consistency check for this repo — it
catches a skill added without a routing-table entry, malformed JSON config,
broken hook script syntax, or a hooks.json pointing at a script that doesn't
exist. Run it before tagging a release of the pack:

```bash
sh tools/validate-pack.sh
```

This is a static check only. It does not trigger skills or fire hooks inside
an actual Claude Code session — passing it means the files are internally
consistent, not that the pack has been exercised end to end. Smoke-test any
new or changed skill in a real session before shipping.

## Memory files

- `.claude/memory.json` — narrative state (conventions, decisions, open work, session summary). Written by the dev-workflow skill. Keep it under 60 lines; the load hook truncates beyond that.
- `.claude/memory-auto.json` — mechanical snapshot. Owned by the PreCompact hook; never hand-edit.

Commit both for team-shared memory, or add `.claude/memory*.json` to `.gitignore` to keep memory local.

## Integrations

- **ECC (context management + pipeline rules).** dev-workflow's Environment
  Verification checks that the ECC rules exist at `~/.claude/rules/ecc/common/`
  (development-workflow, git-workflow, testing, code-review, performance). The
  pack's Context Rule and `references/context-management.md` operationalize
  ECC's Context Window Management; ECC wins on conflict. Missing rules stop the
  full pipeline — the TDD, review, and budget requirements are defined there.
- **Graphify (knowledge base, optional).** Durable knowledge — decisions with
  rationale, architecture changes, lessons — flows to the knowledge graph via
  the graphify skill (`/graphify`) at session end and during context
  compression. Without graphify, `.claude/memory.json` is the only persistence
  layer; the skills note the skipped handoff instead of blocking or silently
  dropping items. See `skills/dev-workflow/references/memory.md` § Knowledge
  Base Layer.

## Review before you trust

Hooks execute shell commands with your user permissions. Read `hooks/scripts/` before installing — they are short on purpose.
