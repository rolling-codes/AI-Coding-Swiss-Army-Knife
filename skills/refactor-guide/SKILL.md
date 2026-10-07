---
name: refactor-guide
description: >
  Use when a refactor spans multiple files or involves a framework migration
  — "help me migrate from X to Y", "break up this monolith", "refactor this
  module safely", "extract this into a service"; NOT for small local refactors
  during active coding (dev-workflow), NOT for reviewing a finished diff
  (code-review), and NOT for a pre-build go/no-go on a new feature
  (kill-test).
allowed-tools: [Read, Grep, Bash]
model: sonnet
---

# Refactor Guide

Plan and checkpoint a structural refactor or migration safely — so a large
change is executed in incremental, reversible steps instead of as one
unmergeable diff that breaks everything until it doesn't.

## Quick examples

**In:** "help me migrate this Express app from callbacks to async/await"
**Out:** scope (structural), blast radius (N call sites), incremental plan with
checkpoints, rollback point at each step, Checkpoint 1 as the immediate next action

**In:** "extract the billing logic out of UserService into its own module"
**Out:** symbol map of billing references, dependency graph of imports, step-by-step
extraction plan with interface-first approach and test coverage gate before starting

## Iron Law

Map the blast radius before writing the plan — because a refactor plan built
without knowing how many call sites and dependencies exist will miss steps,
underestimate scope, and produce a diff that can't be safely reviewed.

## Red Flags — Rationalizations to Refuse

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| "The refactor is straightforward — I'll skip the blast-radius step." | "Straightforward" is an assumption about what's connected. A grep of the affected symbol takes 30 seconds; missing a caller takes days to debug. | Always grep every import, usage, and type reference first. |
| "I'll do the whole refactor in one pass for consistency." | Large monolithic refactors are unreviewed, unrollbackable, and fail in unexpected places. | Produce a checkpoint plan; implement one checkpoint at a time through dev-workflow. |
| "Tests will catch any regressions." | Tests catch what they cover. A blast-radius miss means affected callers have no tests to run. | Map blast radius explicitly; add test coverage to uncovered paths before changing them. |

---

## Step 1: Classify Scope

**Q1: How many files are affected?**
- 1–3 files, single clear responsibility → **local refactor** → hand off to **dev-workflow** directly. This skill is not needed.
- 4+ files, or any cross-module boundary → continue.

**Q2: What type of change is this?**

| Type | Description | Example |
|------|-------------|---------|
| **Structural** | Moving, extracting, or merging modules within the same language/framework | Extract service, split class, consolidate utils |
| **Migration** | Switching frameworks, major version upgrades, or language migrations | Express→Fastify, Python 2→3, class→hooks |
| **Dependency swap** | Replacing one library with another at the same interface boundary | Moment.js→date-fns, Axios→fetch |

---

## Step 2: Pre-Flight

Before mapping blast radius, verify the refactor is justified:

1. **Already exists?** Grep for the target pattern — if the new structure already exists somewhere, extend it rather than recreating.
2. **Dependency covers it?** Check `package.json` / `go.mod` / `requirements.txt` — does an already-installed dep provide what you'd extract?
3. **Scope clear?** Can you state what goes in, what comes out, and what the interface looks like? If not, stop and ask for clarification before proceeding.

If any pre-flight check fails, return a scoped question instead of a plan.

---

## Step 3: Map the Blast Radius

For each symbol, module, or interface being moved or changed:

```bash
# All imports/requires of the affected module (adjust pattern to language)
grep -rn --include="*.{js,ts,py,go,rb,java,rs}" \
  -iE "(import|require|from|use)\s+.*AffectedModule" \
  . 2>/dev/null | grep -v ".git/"

# Direct usages — function calls, class instantiations
grep -rn --include="*.{js,ts,py,go,rb,java,rs}" \
  -E "AffectedSymbol(\(|\.)" \
  . 2>/dev/null | grep -v ".git/"

# Type references (typed languages)
grep -rn --include="*.{ts,go,java,rs}" \
  -E ":\s*AffectedType|AffectedType>" \
  . 2>/dev/null | grep -v ".git/"
```

Produce a blast-radius table:

| File | Usage type | Notes |
|------|-----------|-------|
| user/handler | imports + calls | primary consumer |
| tests/user-spec | test setup | needs updating |
| billing/invoice | type reference only | interface change propagates |

---

## Step 4: Produce the Checkpoint Plan

Break the refactor into checkpoints. Each checkpoint must:
- Pass existing tests before the next begins
- Be committable independently (build + tests green)
- Have a named rollback point

```
Refactor: <what's changing>
Type: structural / migration / dependency-swap
Blast radius: N files, M call sites, K type references

Checkpoint 1: <name>
  What: <concrete change — one module or one interface>
  Tests to pass: <specific test files or patterns>
  Rollback: revert this commit

Checkpoint 2: <name>
  What: ...
  Depends on: Checkpoint 1
  Tests to pass: ...
  Rollback: revert checkpoint 2 (checkpoint 1 state is stable)

...

Final checkpoint: Remove old interface / delete legacy path
  Gate: all N callers confirmed migrated; tests passing
```

Write the plan using the ledger handoff convention documented in dev-workflow; include checkpoint count, files affected, and call site count in the summary.

---

## Step 5: Surface Test Coverage Gaps

A checkpoint plan is only executable if the affected paths have test coverage.

1. Check what tests already cover the affected symbols
2. Note any callers with no tests — they are refactor risks
3. If gaps exist, recommend adding tests via **test-strategy** before starting the refactor

Uncovered callers are not a reason to cancel the refactor — they are a prerequisite task.

---

## Rules

- Never produce a single-pass plan — checkpoint-based only
- Each checkpoint is an independent commit, not a comment in one large PR
- If blast radius is larger than expected, say so and ask whether to proceed before continuing
- If existing tests are absent or sparse, say so before the plan — the risk is the user's to accept

---

## Next Step

- **Implement Checkpoint 1:** use **dev-workflow** with the checkpoint description as requirements
- **Test coverage gaps found:** use **test-strategy** first, then return here to start
- **Code quality issues in the area being refactored:** use **code-review** before starting to avoid carrying bugs forward
- **This turned out to be a local change:** use **dev-workflow** directly
