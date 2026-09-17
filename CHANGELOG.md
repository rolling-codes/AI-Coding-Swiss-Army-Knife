# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning: [SemVer](https://semver.org/).

## [Unreleased]

## [2.4.0] - 2026-09-17

### Added
- `skills/dev-workflow/references/pr-standards.md`: canonical PR and code quality standards — size limits, required sections, hygiene checklist, code quality table with concrete pass/fail criteria, and severity mapping used consistently across skills.
- `skills/dev-workflow/references/backlog.md`: opt-in task board convention; dev-workflow reads `.claude/backlog.md` at session start, shows board summary (todo/doing/done), resumes in-progress tasks, and marks items done after Commit.
- `skills/dev-workflow/references/recipes.md`: opt-in project command registry; dev-workflow consults `.claude/recipes.md` at session start and after any unfamiliar "run/build/update/deploy" request, researches the right command from the project's own files when missing, and saves it before executing.
- `## Quick examples` blocks in all 13 skill bodies: two concrete in/out pairs per skill showing what each actually returns, placed before the Iron Law for fast orientation.
- `tools/routing-scenarios.md`: A14–A16 (recipe lookup, missing recipe research, persist discovered command) and C28–C29 (invented command when no project evidence, second invocation uses persisted recipe); total scenario count 49.

### Changed
- `skills/pr-description/SKILL.md`: Step 0 size check fires on diffs > 600 lines (split recommendation before description); Standard PR template updated to five required sections (Context/Why, What Changed, Risk & Rollback, How to Test, Reviewer Focus); PR hygiene checklist appended to every output; new Red Flag covers skipping the size check.
- `skills/code-review/SKILL.md`: §A Hygiene pass expanded to a full Code Quality Checklist (7 criteria with concrete pass/fail); explicit severity mapping (Critical/Important/Minor) added; verdict rules tied to severity thresholds.
- `agents/code-reviewer.md`: Code Quality Bar applied to "Code quality" check; severity definitions made explicit; quality findings use `criterion | file:line | why | fix` format.
- `tools/routing-scenarios.md`: C26 (size check fires on 900-line diff), C27 (missing Context/Why flagged as Important by code-review).
- `skills/dev-workflow/SKILL.md`: Session Start now checks `.claude/backlog.md` and `.claude/recipes.md`; Task Router gains two rows (backlog pick, recipe lookup).

## [2.3.0] - 2026-09-17

### Fixed

- All 12 SKILL.md files now declare `model:` and `allowed-tools:` in frontmatter,
  satisfying the CLAUDE.md constraint added in the previous session. Previously only
  `ai-hygiene` had both fields; the remaining twelve inherited session defaults silently.
- `tools/validate-pack.sh` gained checks 13 and 14: `model:` presence and `allowed-tools:`
  presence in every SKILL.md. A skill missing either field now fails the static check.
- `skills/dev-workflow/references/skill-routing.md` §5 now includes an explicit
  `docs-audit ↔ architecture-review` pair. The previous §5 claim "every unlisted pair has
  non-overlapping triggers" was false for "review before v-next" requests, which legitimately
  trigger both.
- `skills/scope-creep/SKILL.md` Step 4 now requires visible output for every mid-build
  addition, including Refinements (previously, the Refinement path could be silently
  absorbed). A new rule explicitly states that trigger keywords are sufficient but not
  necessary — any mid-build addition that changes the original goal triggers the skill
  regardless of phrasing.
- `skills/release-prep/SKILL.md` Step 5 Iron Law escape closed: user confirmation of
  known failures does not change the checklist verdict from ❌ to ✅, and an absent test
  suite is never a silent pass — it is documented as ❌ with a note.
- `skills/test-strategy/SKILL.md` Step 3 now includes the `git stash` / `checkout`
  commands for the fail→pass regression test verification, fulfilling the Iron Law at the
  workflow level rather than only in the Red Flags.
- `skills/commit-message/SKILL.md` boundary description now names the downstream skills
  explicitly: `(pr-description / changelog)` instead of the previous generic phrasing.
  A new Red Flag covers the diff+memory supplement bypass: reading the diff but
  supplementing the message with session knowledge violates the Iron Law as surely as
  skipping the diff entirely.
- `skills/context-compression/SKILL.md` YAML frontmatter line-break artifact fixed:
  `architecture-\n  review` rendered as `architecture- review` in folded block scalars.
  The `Dropped:` output template is now a bullet list, preventing multiple drops from
  being bundled into one vague `[category]` entry.
- `skills/architecture-review/SKILL.md` Step 3 now includes a three-level severity rubric
  for 🔴🟡🟢 findings, defining when each level applies.
- `skills/dev-workflow/references/sub-agents.md` now documents model alias selection for
  sub-agents: resolve via `model-registry.json`; default to `standard` for analysis agents.

- Documentation now matches the actual hook wiring. The SessionStart / PreCompact
  memory hooks ship **disabled** — only branch protection is registered in
  `hooks.json` — so the README, `plugin.json`, `marketplace.json`, and
  dev-workflow's `references/memory.md` no longer describe them as active. They
  are documented as opt-in, with instructions to enable them in `/hooks`.
- README skills table now lists all thirteen skills (`ai-hygiene` was missing).
- release-prep no longer hardcodes a project-specific `easycord/` path in its
  Python version-drift grep.
- `skills/ai-hygiene/SKILL.md` script invocations in Mode 1 (Prevent) and Mode 2
  (Code Audit) now use `${CLAUDE_PLUGIN_ROOT}/skills/ai-hygiene/scripts/` paths.
  Previously, bare `scripts/` paths resolved against the user's project working
  directory and silently failed on every project where the scripts didn't exist.

### Added

- `CLAUDE.md` — repository guidance for Claude Code instances working on the pack
  itself: validation command and what it proves, architecture map, constraints for
  safe skill edits (routing integrity, intentionally-disabled memory hooks,
  router-arrow resolution), and release checklist.
- `skills/dev-workflow/references/skill-routing.md` — centralized skill-selection
  decision process, per-skill Capability/Trigger/Boundary table, pairwise
  disambiguation for every overlapping pair, conflict-precedence rules, and a
  cross-skill handoff contract. The router points here for ambiguous routing
  instead of duplicating the rules across thirteen files.
- `tools/routing-scenarios.md` — representative, ambiguous, and adversarial
  routing scenarios to smoke-test skill selection in a live session.
- `tools/routing-scenarios.md` §A now includes representative cases for bug-triage
  (A12) and scope-creep (A13), which previously appeared only in §B/§C; §C adds
  adversarial case C9 for docs-audit/context-compression confusion.
- `skills/dev-workflow/references/skill-routing.md` §5 now includes an explicit
  `docs-audit ↔ release-prep` pair. The previous §5 claim "every unlisted pair has
  non-overlapping triggers" was false for pre-release requests that can trigger both.

### Changed

- `tools/validate-pack.sh` gained five checks: reverse routing (a router arrow
  must point at a real skill), README skill-table coverage, `description:`
  presence in every SKILL.md, agent frontmatter/filename match, and an
  informational notice for hook scripts that ship unregistered.
- `tools/validate-pack.sh` gained two more checks: check 11 verifies every skill
  directory name appears in `skill-routing.md` (catching CTB-table drift independent
  of the SKILL.md routing table), and check 12 verifies `model-registry.json`
  declares all three required alias keys (`fast`, `standard`, `deep`).

## [2.2.0] - 2026-09-15

### Added

- `ai-hygiene` skill: keeps AI fingerprints out of your work across its whole
  lifecycle. It prevents them while you write new code (reuse-first, simplest thing
  that works, a complexity/size budget, and verified dependencies, backed by checker
  scripts you can run), and detects or removes them in existing code and prose, with a
  watermark reference for the technical case. One mode-routed skill covering prevention,
  code and prose auditing, humanizing, and watermark questions.

### Removed

- `lean-code` skill: its preventive code pillars are now Mode 1 of `ai-hygiene`, so the
  standalone skill was retired. If you routed work to `lean-code`, route it to
  `ai-hygiene` instead.

### Changed

- dev-workflow's routing table and the README now point at `ai-hygiene`, with a new note
  distinguishing it (AI stylistic fingerprints: over-engineering, duplication, AI prose
  tells, watermarks) from `code-review` (correctness bugs in a diff).

## [2.1.0] - 2026-07-15

### Added

- `references/graph-tools.md` — canonical graph availability check (graphify →
  codegraph MCP → declared no-graph grep fallback) with a question-to-tool map.
  Every graph-first instruction in the pack now resolves through this one file.

### Fixed

- architecture-review measures fan-out and blast radius from the graph before
  opening any file (new Step 1.5) instead of hand-counting them (RBA-F04).
- code-reviewer agent checks for a graph before reading beyond the diff and
  bounds surrounding-context reads; code-review §B's briefing spec now passes
  the `KNOWLEDGE_GRAPH` line that `sub-agents.md` declares mandatory (RBA-F02/F03).
- bug-triage scores the blast-radius severity axis from graph edge counts,
  test-strategy queries callers of the unit under test, and the debugging
  reference traces call chains via the graph — each with the previous manual
  approach as the declared fallback (RBA-F05/F06/F07).

## Earlier releases

v2.0.0 and the 2.0.1 metadata bump predate this changelog; see the
[release tags](https://github.com/rolling-codes/dev-workflow-pack/tags).
