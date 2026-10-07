# Dev Workflow Pack

Twenty development-workflow skills where each skill knows exactly when to fire
and — just as importantly — when to stay silent. Built through the
[skill-creator](https://github.com/rolling-codes/-the-better-skill-creator-skill-)
six-gate pipeline with machine-executable routing tests, hook-enforced branch
and destructive-command protection, and context discipline baked into every step.
One Claude Code plugin.

The central design problem this solves: skills are instructions Claude can
rationalize around. This pack treats that as an engineering problem, not a
prompting problem. Every skill carries an explicit Capability + Trigger +
Boundary description so it fires when it should and stays silent when a sibling
owns the task. Every routing decision has a machine-testable form — the 29
routing scenarios in `tools/routing-scenarios.md` compile to per-skill YAML
test suites and run against real Claude sessions via `tools/eval-routing.sh`.
And every skip or shortcut a model might attempt is named in each skill's Red
Flags table with the correct behavior alongside it.

## What the hooks do

Skills are instructions Claude can forget. Hooks are guarantees that fire every time.

- **PreToolUse** (Bash) — **active by default.** Two guards: (1) blocks `git commit` and `git push` while on `main`, `master`, `develop`, `release/*`, or `hotfix/*`, and tells Claude to create a feature branch; (2) blocks `git push --force` and `git reset --hard` with a descriptive error — set `DEV_WORKFLOW_ALLOW_DESTRUCTIVE=1` to bypass when intentional. Both use plain text matching; disable per repo in `/hooks` if they get in the way.
- **SessionStart** + **PreCompact** (memory hooks) — **ship, but are not registered by default.** `load-memory.sh` (SessionStart) would inject a short memory digest — branch, dirty-file count, the one-paragraph summary from `.claude/memory.json`, and a pointer to the full files; `save-memory.sh` (PreCompact) would snapshot branch, uncommitted-file count, and the last five commits to `.claude/memory-auto.json`. They are left out of `hooks.json` because session persistence is handled either by the memory skill writing `.claude/memory.json` directly (dev-workflow / context-compression) or by an external tool such as [claude-mem](https://github.com/thedotmack/claude-mem). To turn the digest automation on, register them in `/hooks` (SessionStart → `load-memory.sh`, PreCompact → `save-memory.sh`) — but don't run them alongside claude-mem, or two systems fight over the same session. See `UPGRADE-SLOTS.md`.

All three scripts are plain POSIX sh, depend only on `git`, never block (always exit 0), and stay silent outside a git repo. On Windows they run under Git Bash, which ships with Git for Windows.

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
| ai-hygiene | Prevent/detect/remove AI fingerprints in code and prose; watermarks |
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
| security-audit | Vulnerability scanning: deps (osv-scanner), SAST (semgrep), secrets |
| dependency-check | Outdated, deprecated, and license-problematic package detection |
| observability-audit | Logging, tracing, and error-handling coverage gaps |
| kill-test | Pre-build go/no-go gate: 5-question check before implementing |
| performance-audit | Performance bottleneck mapping, hot-path analysis, profiler recommendation |
| infra-review | Dockerfile, Kubernetes, Terraform, and CI/CD IaC review |
| refactor-guide | Blast-radius mapping and checkpoint planning for structural refactors |

context-compression, docs-audit, and architecture-review sound similar —
they audit three different targets (session memory, doc files, source
structure respectively). See the disambiguation table in
`skills/dev-workflow/SKILL.md` if it's unclear which applies.

## Validating the pack itself

Two complementary checks cover different layers of correctness:

**Static consistency** — `tools/validate-pack.sh` (15 checks). Catches a skill
added without a routing-table entry, a router arrow pointing at a renamed skill,
a SKILL.md missing `description:` / `model:` / `allowed-tools:`, an agent whose
frontmatter name doesn't match its filename, malformed JSON, broken hook script
syntax, a hooks.json pointing at a missing script, and a Primary skill in
routing-scenarios.md with no generated routing test file. Run before every release:

```bash
sh tools/validate-pack.sh
```

**Routing accuracy** — `tools/eval-routing.sh` (requires
[skill-creator](https://github.com/rolling-codes/-the-better-skill-creator-skill-)
and a Claude API key). Converts `tools/routing-scenarios.md` into per-skill YAML
test files via `tools/gen-routing-tests.py` (run once, or after scenario changes),
then invokes `bsc.py eval` on each skill that has routing tests and prints a pass/fail
routing accuracy table. Skills without routing test files are skipped; exit code is
non-zero if any skill fails.

```bash
# Generate test files from routing-scenarios.md (once, or after scenario edits)
python tools/gen-routing-tests.py

# Structural check — no Claude calls, fast
sh tools/eval-routing.sh

# Live routing eval — calls real Claude sessions (costs API tokens)
sh tools/eval-routing.sh --live
```

`validate-pack.sh` proves the files are internally consistent. `eval-routing.sh --live`
proves the router sends each class of task to the right skill. Both are needed; neither
substitutes for the other.

## Memory files

- `.claude/memory.json` — narrative state (conventions, decisions, open work, session summary). Written by the dev-workflow and context-compression skills. Keep it under ~60 lines; if you enable the SessionStart memory hook it emits only a digest, not the whole file.
- `.claude/memory-auto.json` — mechanical snapshot. Written by the PreCompact memory hook *when that hook is enabled* (off by default); never hand-edit.

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
