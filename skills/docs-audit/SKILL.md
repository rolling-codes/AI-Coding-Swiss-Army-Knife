---
name: docs-audit
description: >
  Use this to audit project documentation (README, CONTRIBUTING, API docs,
  wikis, in-repo .md files) against what the codebase actually does now, and
  prune or update what's stale, when asked "review the docs", "are the docs
  out of date", "clean up the README", "docs don't match the code anymore",
  or after a release/major refactor before tagging; NOT for session context
  (context-compression), NOT for code structure (architecture-review), and
  NOT for authoring substantial net-new documentation from scratch.
allowed-tools: [Read, Grep, Glob, Bash, Edit]
model: sonnet
---

# Docs Audit Skill

Documentation drifts because writing it is a one-time act and the code keeps
changing. This skill treats docs the same way `context-compression` treats
session memory: classify each claim as current, stale, or dead, and act on
that classification instead of leaving everything to accumulate. Model: `standard`
for a single doc, `deep` if cross-referencing docs against a large or unfamiliar
codebase.

## Quick examples

**In:** "does the README still match what the code does?"
**Out:** drift report — stale claims (file:line with suggested fix), dead links, sections missing coverage for new features

**In:** "clean up the docs before tagging"
**Out:** same; each doc file classified as current / stale / dead with specific corrections and line-number references

## Iron Law

Every concrete claim is verified against the current code before it's classified —
because fluent prose is not evidence of accuracy, and the exact failure this skill
targets is a well-written doc describing a codebase that no longer exists.

## Red Flags — Rationalizations to Refuse

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| "This README reads confidently and consistently — it's probably accurate; I'll spot-check a couple of claims." | Internal consistency is the failure mode, not evidence against it. Docs stay fluent long after the code moves. | Check each concrete claim (command, flag, path, example) by grep against the source. |
| "This section is stale, but rewriting means understanding the new behaviour — I'll add a caveat note instead." | A wrong doc with a caveat is still a wrong doc; the caveat just spreads the doubt to the accurate parts. | Update it to match reality, or delete it. Those are the only two outcomes for stale. |
| "This old section might still help someone — I'll keep it just in case." | Dead descriptions mislead more than absence: a reader following removed instructions loses more time than one finding nothing. | Age isn't the criterion; accuracy is. Dead → delete. |

---

## Step 1: Scope

- **Single doc** — one file flagged as suspect (fastest path)
- **Full pass** — every `.md` in the repo, README outward
- **Post-release** — triggered by release-prep or a version bump; check for
  version numbers, deprecated flags, changed defaults

```bash
find . -name "*.md" -not -path "*/node_modules/*" -not -path "*/.git/*"
```

Don't open every file for a single-doc scope. Bound the read.

---

## Step 2: Classify Each Claim, Not the Whole File

Read the doc section by section. For each concrete claim (a command, a flag, a
file path, a code example, an architectural statement), check it against the
current codebase — grep for it, don't assume it's still true because it reads
confidently.

| Verdict | Meaning | Action |
|---|---|---|
| **Current** | Matches the code as it exists now | Keep as-is |
| **Stale** | Was true, isn't anymore (renamed, moved, changed behavior) | Update to match reality |
| **Dead** | Describes something removed entirely | Delete, don't leave a corrected description of a thing that no longer exists |
| **Undocumented** | Code does something the docs never mention | Flag as a gap — write it if in scope, else log it |
| **Aspirational** | Describes intended-but-never-shipped behavior | Delete or clearly mark as planned, don't let it read as current |

The failure mode this step targets specifically: docs that are internally
consistent and well-written but describe a version of the code that no longer
exists. Fluent prose is not evidence of accuracy — check against the source.

---

## Step 3: Apply Aging Rules

Same principle as memory aging — a doc that only ever grows misleads more than
it helps:

- Superseded instructions (old install method still listed alongside the new
  one) → remove the old, don't append the new next to it
- Changelogs/release notes belong in `CHANGELOG.md`, not scattered across README
  history sections — if found duplicated, keep one source of truth
- Examples using deprecated APIs → rewrite to current API, don't caveat in place
- TODO/FIXME comments describing docs work older than the repo's active branch
  age → resolve or drop, don't let them fossilize
- If `.claude/architecture.json` exists (dev-workflow), cross-check structural
  claims in docs against it — mismatches mean one of the two is now wrong

---

## Step 4: Report and Act

```
## Docs Audit: [scope]

**Files reviewed:** [N]
**Current:** [N claims/sections — no output needed for these]
**Updated:** [file:section] — [what changed, old → new]
**Deleted:** [file:section] — [why: describes removed feature / superseded / duplicate]
**Gaps found:** [feature/behavior with no docs] — [logged as issue / written now, per scope]

**Not touched, and why:** [anything intentionally left, e.g. external doc site out of scope]
```

For a full pass, make the edits directly rather than just reporting — this
skill's job is pruning, not just flagging (unlike architecture-review, which
only assesses). For gaps requiring net-new substantial writing, log via
`gh issue create` rather than drafting speculative content inline.

---

## Rules

- Never keep a stale claim because rewriting it is more work than leaving it —
  a wrong doc is worse than no doc
- Don't delete a section just because it's old; delete it because it's wrong
  or duplicated — age alone isn't the criterion, accuracy is
- Verify against the actual code (grep, read the file), never against memory
  of what the code "probably still does"
- Keep the same tone/voice as the surrounding doc when updating — don't make
  edited sections stylistically stick out
- If a doc claim can't be verified (e.g. describes external infra not in this
  repo), say so explicitly rather than guessing at current/stale/dead
