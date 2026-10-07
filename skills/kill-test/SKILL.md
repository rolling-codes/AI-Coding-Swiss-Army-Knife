---
name: kill-test
description: >
  Use when the user needs a pre-build go/no-go gate before implementing
  something — "should I build this", "is this worth implementing", "kill test
  this idea", "go/no-go on this feature", "should I write this from scratch or
  is there already something"; NOT for reviewing finished code (code-review),
  NOT for release validation (release-prep), and NOT for scope changes
  mid-build (scope-creep).
allowed-tools: [Read, Grep]
model: haiku
---

# Kill Test

Five questions before writing any code. The goal is catching bad builds before
they start, not blocking good ones. A fast GO is a good outcome.

## Quick examples

**In:** "should I build a custom rate limiter for this API?"
**Out:** GO — nothing in the codebase covers it, stdlib has no built-in, the
scope is clear, no conflicts with existing patterns

**In:** "let's build our own auth system"
**Out:** NO-GO — existing auth library covers 95% of needs, custom auth is a
common source of vulnerabilities, scope is undefined; use the library instead

## Iron Law

Answer all five questions before declaring GO or NO-GO — because a convincing
case for building sometimes collapses on question 3 or 4, and the questions are
faster to run than the build.

---

## The Five Questions

Run in order. A NO-GO on any question ends the check.

### Q1: Does it already exist here?

```bash
# Grep for related function names, class names, or utility patterns
grep -rn --include="*.{js,ts,py,go,rb,java,rs}" -i "<keyword>" . 2>/dev/null | grep -v ".git/"
```

**NO-GO if:** a working implementation already exists in the codebase. Point to
where it lives and stop — "already exists, call the existing one instead."

**GO if:** nothing close found, or what exists is clearly different in scope.

---

### Q2: Does stdlib or an already-installed dependency cover it?

Check `package.json`, `go.mod`, `Cargo.toml`, `requirements.txt`, or equivalent
for anything relevant. Check stdlib docs mentally for language built-ins.

**NO-GO if:** an already-installed dependency solves it (even partially — prefer
wrapping over reimplementing). Or if stdlib covers it in one or two calls.

**GO if:** nothing installed covers it and stdlib is insufficient.

---

### Q3: Is the scope clear enough to build?

The request must answer: what does it accept as input? What does it return or
do? What are the failure modes? If any of these are undefined, scope is unclear.

**NO-GO if:** the scope has ambiguous requirements — "smart retry logic",
"better caching", "handle edge cases" without concrete definition. Ask the user
to sharpen the spec first.

**GO if:** inputs, outputs, and failure modes are stated or inferable from context.

---

### Q4: Does this conflict with existing patterns?

Read the adjacent code. Does this introduce a new pattern where one already
exists (second caching layer, second HTTP client, second config format)?

**NO-GO if:** it duplicates or competes with an established pattern in the repo.
The fix is to extend or replace the existing one, not add another.

**GO if:** no conflict, or the new pattern is justified by a clear gap in the
existing one.

---

### Q5: Will this be maintained?

Is there a clear owner? Is the domain stable enough that custom code won't
require constant updates (e.g., parsing a third-party API that changes
frequently)?

**WARN if:** no clear owner, or the domain is inherently volatile. Flag it and
let the user decide — don't block on it.

**GO if:** ownership is clear and the domain is reasonably stable.

---

## Output Format

```
Kill test: <what was proposed>

Q1 — Already exists? [YES → NO-GO | NO → pass]
Q2 — Stdlib / installed dep covers it? [YES → NO-GO | NO → pass]
Q3 — Scope clear? [NO → NO-GO | YES → pass]
Q4 — Conflicts with existing patterns? [YES → NO-GO | NO → pass]
Q5 — Will it be maintained? [WARN: <reason> | YES → pass]

Verdict: GO / NO-GO / GO WITH WARNING

[One line: what to do next]
```

### Verdicts

**GO** — All five questions pass. Proceed to **dev-workflow**.

**NO-GO** — State which question failed and the specific reason. Suggest the
alternative (existing file, existing dep, sharpen the spec, extend existing
pattern).

**GO WITH WARNING** — Questions 1-4 pass; Q5 raised a concern. State the
warning and proceed — the user has been informed.

---

## Rules

- Never block a GO with vague concerns — only fail on a concrete answer to one of the five questions
- A NO-GO is not a refusal to build — it's a pointer to a better path
- If the user says "just build it anyway", return a one-line acknowledgement and hand off to **dev-workflow**
- The whole check should take less than 30 seconds of reading

---

## Next Step

- **GO:** use **dev-workflow** to start the build pipeline
- **NO-GO (already exists):** point to the existing file/function
- **NO-GO (dep covers it):** name the dep and the relevant API
- **NO-GO (unclear scope):** ask the one clarifying question that unlocks the build
