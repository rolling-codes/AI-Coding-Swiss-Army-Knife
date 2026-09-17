---
name: test-strategy
description: >
  Use this to generate a test plan and the tests themselves — unit,
  integration, edge cases, and regression tests — when asked "write tests for
  this", "what edge cases am I missing", "add a regression test", "test
  coverage for this change", or right after a bug fix before it's considered
  done; NOT for enforcing test-first ordering during active development
  (dev-workflow's TDD step), NOT for fixing the bug itself (dev-workflow),
  and NOT for review verdicts on a diff (code-review).
allowed-tools: [Read, Grep, Glob, Bash]
model: sonnet
---

# Test Strategy Skill

Produces tests that would actually catch the next regression, not tests that
just exercise the happy path for coverage numbers. Model: `standard`; use `fast`
first to enumerate cases before writing any test code.

## Quick examples

**In:** "write tests for this new auth module"
**Out:** unit tests per function, edge cases (null user, expired token, concurrent session), regression test scaffold for the current bug

**In:** "what am I missing in my test coverage?"
**Out:** gap analysis — untested code paths listed with file:line, missing edge cases, suggested test scaffolding for each

## Iron Law

A regression test counts only after it has failed against the pre-fix code —
because a test that has never failed proves nothing about its ability to catch
the bug; the fail-then-pass inversion is the entire evidence.

## Red Flags — Rationalizations to Refuse

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| "Enumerating cases in prose first is overhead — I can see the cases in the code." | Reading cases off the implementation mirrors the implementation. The spec-first enumeration exists to surface what the code *doesn't* handle. | Run Step 2 in plain language before any test code. |
| "The regression test passes post-fix; verifying it against the old code means a checkout — not worth it." | An un-failed regression test is unproven. This is the Iron Law, and there is no cheaper substitute for the evidence. | `git stash` / checkout the pre-fix ref, watch the test fail, restore, watch it pass. |
| "More tests looks better — I'll pad boundary variants to boost the count." | Padded duplicates dilute signal and slow CI without adding coverage of meaningful cases. | Coverage of the enumerated cases is the metric, not test count. Report gaps instead. |

---

## Step 1: Identify What's Under Test

- **New code** — a function, class, or endpoint being added
- **Bug fix** — something that broke; the fix needs a test that fails without it
- **Existing code, untested** — retrofitting coverage

For a bug fix specifically: reproduce the bug first (see dev-workflow's Debugging
reference if installed), confirm the fix, *then* write the regression test against
the pre-fix behavior — a regression test that was written after the fix without
ever failing against the old code isn't proven to catch anything.

---

## Step 2: Enumerate Cases (before writing test code)

Use `fast`. List cases in plain language first — writing test code before this
step produces tests that mirror the implementation instead of the specification.

**Unit level:**
- Happy path — the documented normal case
- Boundary values — empty, zero, max, min, off-by-one
- Invalid input — wrong type, null/undefined, malformed
- State-dependent behavior — same input, different prior state

**Integration level:**
- Two+ real components interacting (not mocked) through their actual interface
- Failure propagation — what happens when a downstream call fails
- Ordering/concurrency — race conditions, out-of-order events, retries

**Edge cases specific to this codebase:**
- Re-read the bug/feature description for words like "never", "always", "only if" —
  each is a boundary to test
- When a graph is available (per dev-workflow's `references/graph-tools.md`),
  query it for callers of the unit under test before enumerating integration
  cases — callers are the integration surface, and the query beats browsing
- Check for existing similar code in the repo and see what it tests (or fails to)

**Regression:**
- One test per fixed bug, named so the bug is identifiable from the test name
  (e.g. `test_config_update_no_race_on_concurrent_write`, not `test_bug_142`)

---

## Step 3: Write the Tests

- Match the repo's existing test framework and conventions — don't introduce a
  new one without asking
- One assertion concept per test; a test with five unrelated assertions hides
  which one actually failed
- Name tests by behavior, not by method: `rejects_negative_quantity`, not `test3`
- For the regression test from Step 1: run it against the pre-fix code first to
  confirm it actually fails, then confirm it passes post-fix

```bash
# Verify the regression test actually catches the bug:
git stash                              # stash the fix (or: git checkout <pre-fix-ref>)
npx jest path/to/regression.test.ts   # must FAIL here — proves the test detects the bug
git stash pop                          # restore the fix
npx jest path/to/regression.test.ts   # must PASS here — proves the fix works
```

A regression test that has never failed is unproven. If no pre-fix state is
available (e.g. fix was already committed), check out the commit before the fix:
`git checkout <pre-fix-sha> -- <files>`, run the test, then restore.

```bash
npx jest --findRelatedTests src/auth.ts   # or the repo's equivalent
```

---

## Step 4: Report Gaps

If some enumerated case from Step 2 isn't practical to test (needs infra not
present, flaky by nature, etc.), say so explicitly rather than silently dropping
it:

```
## Test Coverage: [scope]

**Added:** [N] unit, [N] integration, [N] regression
**Not covered, and why:** [case] — [reason: needs staging env / flaky by nature / etc.]
**Confidence this catches the original bug:** [High/Medium/Low] — [why]
```

---

## Rules

- Never mark a regression test as done without confirming it fails on the old code
- Don't pad a test count with trivial duplicate cases
- Flag gaps instead of hiding them
- If writing tests for someone else's PR, prefer suggesting the missing cases
  over silently adding tests they didn't ask for — check with the user first
